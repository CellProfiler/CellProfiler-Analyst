import sys
import os
import logging
import json
from optparse import OptionParser
import progressbar
import numpy as np
from scipy.stats.stats import scoreatpercentile
from scipy.stats import norm as Gaussian
import cpa
import cpa.dbconnect
import cpa.util

logger = logging.getLogger(__name__)

def np_load(filename):
    "Work around bug in numpy that causes file handles to be left open."
    with open(filename, 'rb') as f:
        x = np.load(f)
        f.close()
    return x

def make_progress_bar(text=None):
    widgets = (['%s: ' % text] if text else []) + [progressbar.Percentage(), ' ', 
                                                   progressbar.Bar(), ' ', 
                                                   progressbar.ETA()]
    return progressbar.ProgressBar(widgets=widgets)

def _check_directory(dir, resume):
    if os.path.exists(dir):
        if not resume:
            logger.error('Directory exists already (remove or use -r): ' + dir)
            sys.exit(1)
    else:
        os.makedirs(dir)

import abc
class BaseNormalization(object):
    __metaclass__ = abc.ABCMeta
    
    _cached_colmask = None

    def __init__(self, cache, param_dir):
        self.cache = cache
        self.dir = os.path.join(cache.cache_dir, param_dir)
        self._colmask_filename = os.path.join(self.dir, 'colmask.npy')

    def _params_filename(self, plate):
        return os.path.join(self.dir, 'params', 
                            unicode(plate) + '.npy')

    @property
    def _colmask(self):
        if self._cached_colmask is None:
            self._cached_colmask = np_load(self._colmask_filename)
        return self._cached_colmask

    @abc.abstractmethod
    def normalize(self, plate, data):
        pass
        
    @property
    def colnames(self):
        """Return the names of the columns returned by normalize()"""
        return [col
                for col, keep in zip(self.cache.colnames, self._colmask) 
                if keep]

    @property
    def colnames_excluded(self):
        """Return the names of the columns excluded by normalize()"""
        return [col
                for col, keep in zip(self.cache.colnames, self._colmask) 
                if not keep]

    #
    # Methods to precompute the normalizations
    #

    def _create_cache(self, predicate, resume=False):
        self._create_cache_params(predicate, resume)
        self._create_cache_colmask(predicate)

    def _get_controls(self, predicate):
        """Return a dictionary mapping plate names to lists of control wells"""
        plates_and_images = {}
        for row in cpa.db.execute("select distinct %s, %s from %s where %s"%
                                  (cpa.properties.plate_id, 
                                   ', '.join(cpa.dbconnect.image_key_columns()),
                                   cpa.properties.image_table, predicate)):
            plate = row[0]
            imKey = tuple(row[1:])
            plates_and_images.setdefault(plate, []).append(imKey)
        return plates_and_images

    def _create_cache_colmask(self, predicate):
        colmask = None
        for plate, imKeys in self._get_controls(predicate).items():
            params = np_load(self._params_filename(plate))
            if len(params) == 0:
                continue # No DMSO wells, so no params
            nonzero = self._check_param_zero(params)
            if colmask is None:
                colmask = nonzero
            else:
                colmask &= nonzero
        np.save(self._colmask_filename, colmask)
            
    @abc.abstractmethod
    #@staticmethod
    def _compute_params(self, features):
        pass

    @abc.abstractproperty
    def _null_param(self):
        """
        Return a value that corresponds to a null value for the normalization
        parameter.
        """
        pass
        
    @abc.abstractproperty
    def _check_param_zero(self, params):
        """
        Return a boolean vector of length = len(colmask), where an element is 
        True iff the normalization for the corresponding variable can be 
        calculated. E.g. scale == 0.
        """
        pass
        
    def _create_cache_params_1(self, plate, imKeys, filename):
        features = self.cache.load(imKeys)[0]
        if len(features) == 0:
            logger.warning('No DMSO features for plate %s' % str(plate))
            params = self._null_param
        else:
            params = self._compute_params(features)
        np.save(filename, params)

    def _create_cache_params(self, predicate, resume=False):
        controls = self._get_controls(predicate)
        for i, (plate, imKeys) in enumerate(make_progress_bar('Params')(controls.items())):
            filename = self._params_filename(plate)
            if i == 0:
                _check_directory(os.path.dirname(filename), resume)
            if resume and os.path.exists(filename):
                continue
            self._create_cache_params_1(plate, imKeys, filename)
            
            
            
class DummyNormalization(BaseNormalization):
    def __init__(self, cache, param_dir='dummy'):
        super(DummyNormalization, self).__init__(cache, param_dir)

    def normalize(self, plate, data):
        return data

    def _null_param(self):
        return np.zeros((0, len(self.cache.colnames)))
        
    def _check_param_zero(self, params):
        return False

    def _compute_params(self, features):
        return np.zeros((0, len(features)))
        
    @property
    def colnames(self):
        return self.cache.colnames
    
class StdNormalization(BaseNormalization):
    def __init__(self, cache, param_dir='std'):
        super(StdNormalization, self).__init__(cache, param_dir)

    def normalize(self, plate, data):
        params = np_load(self._params_filename(plate))
        assert data.shape[1] == params.shape[1]
        data = data[:, self._colmask]
        params = params[:, self._colmask]
        shift = params[0]
        scale = params[1]
        assert np.all(scale > 0)
        return (data - shift) / scale

    def _compute_params(self, features):
        m = features.shape[1]
        params = np.ones((2, m)) * np.nan
        for j in xrange(m):
            params[0, j] = np.mean(features[:, j])
            params[1, j] = np.std(features[:, j])
        return params                   

    def _null_param(self):
        return np.zeros((0, len(self.cache.colnames)))
        
    def _check_param_zero(self, params):
        return params[1] != 0    

class RobustStdNormalization(StdNormalization):
    def __init__(self, cache, param_dir='robust_std'):
        super(RobustStdNormalization, self).__init__(cache, param_dir)
        
    def _compute_params(self, features):
        m = features.shape[1]
        params = np.ones((2, m)) * np.nan
        c = Gaussian.ppf(3/4.)
        for j in xrange(m):
            d = np.median(features[:, j])
            params[0, j] = d
            params[1, j] = np.median(np.fabs(features[:, j] - d) / c)
        return params                   

class RobustLinearNormalization(BaseNormalization):
    def __init__(self, cache, param_dir='robust_linear', lower_q=1, upper_q=99):
        super(RobustLinearNormalization, self).__init__(cache, param_dir)
        self.lower_q = lower_q
        self.upper_q = upper_q
        
    def normalize(self, plate, data):
        percentiles = np_load(self._params_filename(plate))
        assert data.shape[1] == percentiles.shape[1]
        data = data[:, self._colmask]
        percentiles = percentiles[:, self._colmask]
        divisor = (percentiles[1] - percentiles[0])
        assert np.all(divisor > 0)
        return (data - percentiles[0]) / divisor
        
    def _compute_params(self, features):
        m = features.shape[1]
        percentiles = np.ones((2, m)) * np.nan
        for j in xrange(m):
            percentiles[0, j] = scoreatpercentile(features[:, j], self.lower_q)
            percentiles[1, j] = scoreatpercentile(features[:, j], self.upper_q)
        return percentiles

    def _null_param(self):
        return np.zeros((0, len(self.cache.colnames)))
        
    def _check_param_zero(self, params):
        return params[1] != params[0]

normalizations = dict((c.__name__, c)
                      for c in [RobustLinearNormalization,
                                RobustStdNormalization,
                                StdNormalization,
                                DummyNormalization])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = OptionParser("usage: %prog [-r] [-m method] PROPERTIES-FILE CACHE-DIR PREDICATE")
    parser.add_option('-m', '--method', dest='method', action='store', default='RobustStdNormalization', help='method')
    
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, predicate = args

    cpa.properties.LoadFile(properties_file)

    from cpa.profiling.cache import Cache
    cache = Cache(cache_dir)
    normalizer = normalizations[options.method](cache)
    normalizer._create_cache(predicate)
