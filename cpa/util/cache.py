'''
Cache of per-well block of per-cell feature data.

Example usage as a script (builds cache and precomputes normalizations):

$ py -m cpa.util.cache CDP2.properties /imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache

Example usage as module:

>>> import cpa
>>> from cpa.util import cache
>>> cpa.properties.LoadFile('Morphology.properties')
>>> c = cache.Cache('/broad/shptmp/ljosa/az_cache')
>>> cc_mapping, cc_colnames = cpa.db.group_map('CompoundConcentration', reverse=True)
>>> imKeys = mapping.values()[0]
>>> unnormalized, unnormalized_colnames = c.load(imKeys)
>>> normalized, normalized_colnames = c.load(imKeys, normalization=cache.RobustLinearNormalization)

'''

import sys
import os
import logging
from optparse import OptionParser
import numpy as np
from scipy.stats.stats import scoreatpercentile
import cpa
import cpa.dbconnect
import cpa.util

logger = logging.getLogger(__name__)

def invert_dict(d):
    inverted = {}
    for k, v in d.items():
        inverted.setdefault(v, []).append(k)
    return inverted


class DummyNormalization(object):
    def __init__(self, cache):
        self.cache = cache

    def normalize(self, plate, data):
        return data

    @property
    def colnames(self):
        """Return the names of the columns returned by normalize()"""
        return self.cache.colnames


class RobustLinearNormalization(object):
    _cached_colmask = None

    def __init__(self, cache):
        self.cache = cache
        self.dir = os.path.join(cache.cache_dir, 'robust_linear')
        self._colmask_filename = os.path.join(self.dir, 'colmask.npy')

    def _percentiles_filename(self, plate):
        return os.path.join(self.dir, 'percentiles', 
                            unicode(plate) + '.npy')

    @property
    def _colmask(self):
        if self._cached_colmask is None:
            self._cached_colmask = np.load(self._colmask_filename)
        return self._cached_colmask

    def normalize(self, plate, data):
        """
        Normalize the data according to the precomputed normalization
        for the specified plate. The normalized data may have fewer
        columns that the unnormalized data, as columns may be removed
        if normalizing them is impossible.

        """
        percentiles = np.load(self._percentiles_filename(plate))
        assert data.shape[1] == percentiles.shape[1]
        data = data[:, self._colmask]
        percentiles = percentiles[:, self._colmask]
        divisor = (percentiles[1] - percentiles[0])
        assert np.all(divisor > 0)
        return (data - percentiles[0]) / divisor

    @property
    def colnames(self):
        """Return the names of the columns returned by normalize()"""
        return [col
                for col, keep in zip(self.cache.colnames, self._colmask) 
                if keep]

    #
    # Methods to precompute the normalizations
    #

    def _create_cache(self, resume=False):
        self._create_cache_colmask()
        self._create_cache_percentiles(resume)

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
            percentiles = np.load(self._percentiles_filename(plate))
            if len(percentiles) == 0:
                continue # No DMSO wells, so no percentiles
            nonzero = percentiles[0] != percentiles[1]
            if colmask is None:
                colmask = nonzero
            else:
                colmask &= nonzero
        np.save(self._colmask_filename, colmask)

    def _create_cache_percentiles(self, resume=False):
        controls = self._get_controls(predicate)
        for i, (plate, imKeys) in enumerate(controls.items()):
            features = self.cache.load(imKeys)
            if len(features) == 0:
                logger.warning('No DMSO features for plate %s' % str(plate))
                percentiles = np.zeros((0, len(colnames)))
            else:
                m = features.shape[1]
                percentiles = np.ones((2, m)) * np.nan
                for j in xrange(m):
                    percentiles[0, j] = scoreatpercentile(features[:, j], 1)
                    percentiles[1, j] = scoreatpercentile(features[:, j], 99)
            np.save(self._percentiles_filename(plate), percentiles)
            logger.info('Plate %d of %d' % (i + 1, len(controls.keys())))


class Cache(object):
    _cached_plate_map = None
    _cached_colnames = None

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self._plate_map_filename = os.path.join(self.cache_dir, 
                                                'image_to_plate.pickle')
        self._colnames_filename = os.path.join(self.cache_dir, 'colnames.txt')

    def _image_filename(self, plate, imKey):
        return os.path.join(self.cache_dir, unicode(plate),
                            u'-'.join(map(unicode, imKey)) + '.npy')

    @property
    def _plate_map(self):
        if self._cached_plate_map is None:
            self._cached_plate_map = cpa.util.unpickle1(self._plate_map_filename)
        return self._cached_plate_map

    def load(self, image_keys, normalization=DummyNormalization):
        """Load the raw features of all the cells in a particular well and
        return them as a ncells x nfeatures numpy array."""
        normalizer = normalization(self)
        images_per_plate = {}
        for imKey in image_keys:
            images_per_plate.setdefault(self._plate_map[imKey], []).append(imKey)
        features = []
        for plate, imKeys in images_per_plate.items():
            f = np.load(self._image_filename(plate_name, well_name))
            if len(data) > 0:
                features.append(normalizer.normalize(f))
        return np.vstack(features), normalizer.colnames

    @property
    def colnames(self):
        if self._cached_colnames is None:
            self._cached_colnames = [line.rstrip() 
                                     for line in open(self._colnames_filename, 
                                                      'rU').readlines()]
        return self._cached_colnames

    #
    # Methods to create the cache
    #

    def _create_cache(self, resume=False):
        self._create_cache_colnames()
        self._create_cache_plate_map()

        nimages = len(cache._plate_map)
        i = 0
        for plate, image_keys in invert_dict(cache._plate_map).items():
            plate_dir = os.path.dirname(self._image_filename(plate, image_keys[0]))
            if not os.path.exists(plate_dir):
                os.mkdir(plate_dir)
            for image_key in image_keys:
                self._create_cache_image(plate, image_key, resume)
                i += 1
                logger.info('Image %d of %d' % (i + 1, nimages))

    def _create_cache_colnames(self):
        """Create cache of column names"""
        cols = cpa.db.GetColnamesForClassifier()
        with open(self._colnames_filename, 'w') as f:
            for col in cols:
                print >>f, col

    def _create_cache_plate_map(self):
        """Create cache of map from image key to plate name"""
        plate_map = dict((tuple(row[1:]), row[0])
                         for row in cpa.db.execute('select distinct %s, %s from %s'%
                                                   (cpa.properties.plate_id, 
                                                    ', '.join(cpa.dbconnect.image_key_columns()),
                                                    cpa.properties.image_table)))
        cpa.util.pickle(self._plate_map_filename, plate_map)

    def _create_cache_image(self, plate, image_key, resume=False):
        filename = self._image_filename(plate, image_key)
        if resume and os.exists(filename):
            return
        features = cpa.db.execute("""select %s from %s where %s""" % (
                ','.join(self.colnames), cpa.properties.object_table, 
                cpa.dbconnect.GetWhereClauseForImages([image_key])))
        np.save(filename, features)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = OptionParser("usage: %prog [-f] PROPERTIES-FILE CACHE-DIR PREDICATE")
    parser.add_option('-r', dest='resume', action='store_true')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, predicate = args

    cpa.properties.LoadFile(properties_file)

    if os.path.exists(cache_dir):
        logger.error('Cache directory exists already. Remove or use -r.')
        sys.exit(1)
    else:
        os.mkdir(cache_dir)

    cache = Cache(cache_dir)

    cache._create_cache(options.resume)
    RobustLinearNormalization(cache)._create_cache(options.resume)
