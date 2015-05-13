'''
Cache of per-well block of per-cell feature data.

Example usage as a script (builds cache and precomputes normalizations):

$ python -m cpa.profiling.cache CDP2.properties /imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache "Image_Metadata_ASSAY_WELL_ROLE = 'mock'"

Example usage as module:

>>> import cpa
>>> from cpa.profiling.cache import Cache
>>> from cpa.profiling.normalization import RobustLinearNormalization
>>> cpa.properties.LoadFile('CDP2.properties')
>>> cache = Cache('/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache')
>>> cc_mapping, cc_colnames = cpa.db.group_map('CompoundConcentration', reverse=True)
>>> imKeys = cc_mapping.values()[0]
>>> unnormalized, unnormalized_colnames = cache.load(imKeys)
>>> normalized, normalized_colnames = cache.load(imKeys, normalization=RobustLinearNormalization)

'''

import sys
import os
import logging
import json
from optparse import OptionParser
import progressbar
import numpy as np
from scipy.stats.stats import scoreatpercentile
import cpa
import pandas as pd
import re
import fnmatch
import pickle
from .normalization import DummyNormalization, normalizations

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

def invert_dict(d):
    inverted = {}
    for k, v in d.items():
        inverted.setdefault(v, []).append(k)
    return inverted



class Cache(object):
    _cached_plate_map = None
    _cached_colnames = None
    _image_key_columns = None
    _object_id = None
    _plate_id = None

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self._plate_map_filename = os.path.join(self.cache_dir, 
                                                'image_to_plate.pickle')
        self._colnames_filename = os.path.join(self.cache_dir, 'colnames.txt')
        self._counts_filename = os.path.join(self.cache_dir, 'counts.pickle')
        self._image_table_filename = os.path.join(self.cache_dir, 'image_table.pickle')
        self._object_table_filename = os.path.join(self.cache_dir, 'object_table.pickle')
        self._cache_params_filename = os.path.join(self.cache_dir, 'cache_params.pickle')
        
    def _image_filename(self, plate, imKey):
        return os.path.join(self.cache_dir, unicode(plate),
                            u'-'.join(map(unicode, imKey)) + '.npz')

    def _image_filename_backward_compatible(self, plate, imKey):
        # feature files were previously stored as npy files
        return os.path.join(self.cache_dir, unicode(plate),
                            u'-'.join(map(unicode, imKey)) + '.npy')
    @property
    def _plate_map(self):
        if self._cached_plate_map is None:
            self._cached_plate_map = cpa.util.unpickle1(self._plate_map_filename)
        return self._cached_plate_map

    def load_objects(self, object_keys, normalization=DummyNormalization, removeRowsWithNaN=True):
        objects_by_image = {}
        for object_key in object_keys:
            objects_by_image.setdefault(object_key[:-1], []).append(object_key[-1])
        results = {}
        for image_key, cell_ids in objects_by_image.items():
            stackedfeatures, colnames, stackedcellids = self.load([image_key], normalization, removeRowsWithNaN)
            stackedcellids = list(stackedcellids)
            for cell_id in cell_ids:
                index = stackedcellids.index(cell_id)
                fv = stackedfeatures[index, :]
                object_key = tuple(list(image_key) + [cell_id])
                results[object_key] = fv
        return np.array([results[object_key] for object_key in object_keys])

    def load(self, image_keys, normalization=DummyNormalization, removeRowsWithNaN=True):
        """Load the raw features of all the cells in a particular well and
        return them as a ncells x nfeatures numpy array."""
        normalizer = normalization(self)
        images_per_plate = {}
        for imKey in image_keys:
            images_per_plate.setdefault(self._plate_map[imKey], []).append(imKey)

        # check if cellids have been stored
        plate, imKeys = images_per_plate.items()[0]
        imf_old = self._image_filename_backward_compatible(plate, imKey)
        imf_new = self._image_filename(plate, imKey)
        if os.path.exists(imf_old) and os.path.exists(imf_new):
            logger.warning('Both new and old feature files found : %s and %s. Using new feature file %s.' \
                           % (imf_new, imf_old, imf_new))
            flag_bkwd = False
        else:
            flag_bkwd = os.path.exists(imf_old)
        
        _image_filename = self._image_filename_backward_compatible if flag_bkwd else \
            self._image_filename

        features = []
        cellids = []

        for plate, imKeys in images_per_plate.items():
            for imKey in imKeys:
                # Work around bug in numpy that causes file
                # handles to be left open.
                with open(_image_filename(plate, imKey), 'rb') as file:
                    raw = np.load(file)
                    if flag_bkwd:
                        _features = np.array(raw, dtype=float)
                    else:
                        _features = np.array(raw["features"], dtype=float)
                        _cellids = np.array(raw["cellids"], dtype=int)

                #import pdb
                #pdb.set_trace()

                if removeRowsWithNaN and len(_features) > 0:
                    prune_rows = np.any(np.isnan(_features),axis=1)
                    _features = _features[-prune_rows,:]
                    if not flag_bkwd:
                        if _cellids.shape != ():
                            _cellids = _cellids[-prune_rows]
                        else:
                            # This is redundant but put in here
                            # for sake of completeness
                            if prune_rows[0]:
                                _cellids = np.array([])

                if len(_features) > 0:
                    features.append(normalizer.normalize(plate, _features))
                    if not flag_bkwd:
                        cellids.append(_cellids)

            if(len(features) > 0):
                stackedfeatures = np.vstack(features)
                if not flag_bkwd:
                    stackedcellids = np.squeeze(np.hstack(cellids))
            else:
                stackedfeatures = np.array([])
                if not flag_bkwd:
                    stackedcellids = np.array([])
            
        if flag_bkwd:
            stackedcellids = None
        return stackedfeatures, normalizer.colnames, stackedcellids

    @property
    def colnames(self):
        if self._cached_colnames is None:
            self._cached_colnames = [line.rstrip() 
                                     for line in open(self._colnames_filename, 
                                                      'rU').readlines()]
        return self._cached_colnames

    @property
    def object_id(self):
        if self._object_id is None:
            _cache_params = cpa.util.unpickle1(self._cache_params_filename)
            self._object_id = _cache_params['_object_id']
        return self._object_id
        
    @property
    def plate_id(self):
        if self._plate_id is None:
            _cache_params = cpa.util.unpickle1(self._cache_params_filename)
            self._plate_id = _cache_params['_plate_id']
        return self._plate_id
        
    @property
    def image_key_columns(self):
        if self._image_key_columns is None:
            _cache_params = cpa.util.unpickle1(self._cache_params_filename)
            self._image_key_columns = _cache_params['_image_key_columns']
        return self._image_key_columns
        
    def get_cell_counts(self):
        """
        The counts include rows with NaNs, which may be removed by
        the load() method depending on the removeRowsWithNaN
        keyword.
        
        Image with zero object won't have their key stored in this dictionary.
        """
        
        assert len(self.image_key_columns) == 1, "_create_cache_image does not currently support composite image_key"
        #if not os.path.exists(self._counts_filename):
        #    self._create_cache_counts()
        df = pd.read_pickle(self._counts_filename)
        return dict((row[self.image_key_columns[0]], row['count']) for idx, row in df.iterrows())


    #
    # Methods to create the cache
    #

    def _create_cache(self, resume=False):
        self._create_cache_params(resume)
        self._create_cache_image_table(resume)
        self._create_cache_object_table(resume)
        # self._create_cache_colnames(resume)
        self._create_cache_plate_map(resume)
        self._create_cache_features(resume)
        self._create_cache_counts(resume)

    def _create_cache_params(self, resume):
        """Create cache of parameters"""
        if resume and os.path.exists(self._cache_params_filename):
            return
            
        _cache_params = dict({})
        _cache_params['_object_id'] = options.object_id
        _cache_params['_plate_id'] = options.plate_id
        _cache_params['_image_key_columns'] = options.image_key_columns.split(",")
        cpa.util.pickle(self._cache_params_filename, _cache_params)
        
            
    def _generate_imagekey_prefix(self, fname):
        return re.sub('[^0-9a-zA-Z]+', '_', os.path.dirname(os.path.relpath(fname, os.path.join(self.cache_dir, "../../"))))
        
    def get_image_table(self):
        if os.path.exists(self._image_table_filename):
            return cpa.util.unpickle1(self._image_table_filename)
        else:
            logger.error('%s does not exist.' % self._image_table_filename)
            sys.exit(1)
        
    def _create_cache_image_table(self, resume):
        """Create cache of image table"""
        if resume and os.path.exists(self._image_table_filename):
            self._image_table = cpa.util.unpickle1(self._image_table_filename)
            return
            
        image_table_csv_l = []
        for root, dirnames, filenames in os.walk(os.path.join(self.cache_dir, "../")):
          for filename in fnmatch.filter(filenames, 'image.csv'):
            image_table_csv_l.append(os.path.join(root, filename))

        image_table_l = []
        for image_table_csv in image_table_csv_l:
            df = pd.read_csv(image_table_csv, dtype={'ImageNumber': str, 'Metadata_Barcode' : str} )
            prefix = self._generate_imagekey_prefix(image_table_csv) 
            df['ImageNumber'] = prefix + "_" + df['ImageNumber'] 
            image_table_l.append(df)
            
        self._image_table = pd.concat(image_table_l)
        cpa.util.pickle(self._image_table_filename, self._image_table)

    def _create_cache_object_table(self, resume):
        """Create cache of object table"""
        if resume and os.path.exists(self._object_table_filename):
            self._object_table = cpa.util.unpickle1(self._object_table_filename)
            return

        object_table_csv_l = []
        for root, dirnames, filenames in os.walk(os.path.join(self.cache_dir, "../")):
          for filename in fnmatch.filter(filenames, 'object.csv'):
            object_table_csv_l.append(os.path.join(root, filename))

        object_table_l = []
        object_table_csv_l_ = object_table_csv_l if options.debug_limit == -1 else object_table_csv_l[0:options.debug_limit]
        for object_table_csv in object_table_csv_l_:
            with(open(object_table_csv, "r")) as f:
                a = f.readline()
                b = f.readline()
                
            header = b.strip().split(",")
            header_dtype  = dict(zip(header, [np.float32]*len(header)))
            header_dtype['ImageNumber'] = str
            header_dtype['ObjectNumber'] = np.int32

            header_new = [x+"_"+y if y not in ['ImageNumber', 'ObjectNumber'] else y for x,y in zip(a.strip().split(","), b.strip().split(",")) ]
            
            df = pd.read_csv(object_table_csv, dtype=header_dtype, header=1, names=header_new)
            
            prefix = self._generate_imagekey_prefix(object_table_csv) 
            df['ImageNumber'] = prefix + "_" + df['ImageNumber'] 
            
            object_table_l.append(df)
            
            cols = [col for col in header_new if col not in ['ImageNumber', 'ObjectNumber'] ]
            
            self._create_cache_colnames1(cols)
            
            
        self._object_table = pd.concat(object_table_l)
        cpa.util.pickle(self._object_table_filename, self._object_table)
    
    def _create_cache_colnames(self, resume):
        """Create cache of column names - modified to only throw error if file does not exist"""
        # Check if file exists by trying to open it
        try:
            with(open(self._colnames_filename, 'r')) as f:
                pass
        except Exception:
            logger.error('_colnames_filename %s not found.' % _colnames_filename)
            raise
        return
        
    def _create_cache_colnames1(self, cols):
        """Create cache of column names"""
        if os.path.exists(self._colnames_filename):
            return
        with open(self._colnames_filename, 'w') as f:
            for col in cols:
                print >>f, col        

    def _create_cache_plate_map(self, resume):
        """Create cache of map from image key to plate name"""
        if resume and os.path.exists(self._plate_map_filename):
            return
        from pandasql import sqldf
        _image_table = self._image_table
        df = sqldf('select distinct %s, %s from %s'% (self.plate_id, ', '.join(self.image_key_columns), '_image_table'), locals())
        self._cached_plate_map = dict((tuple(row[1:].tolist()), row[0]) for idx, row in df.iterrows())
        #from IPython import embed; embed()                                                                 
        cpa.util.pickle(self._plate_map_filename, self._cached_plate_map)

    def _create_cache_features(self, resume):
        nimages = len(self._plate_map)
        for plate, image_keys in make_progress_bar('Features')(invert_dict(self._plate_map).items()):
            plate_dir = os.path.dirname(self._image_filename(plate, image_keys[0]))
            if not os.path.exists(plate_dir):
                os.mkdir(plate_dir)
            for image_key in image_keys:
                self._create_cache_image(plate, image_key, resume)
                
    def _create_cache_image(self, plate, image_key, resume=False):
        filename = self._image_filename(plate, image_key)
        if resume and os.path.exists(filename):
            return
        
        assert len(image_key) == 1, "_create_cache_image does not currently support composite image_key"
        
        sel = self._object_table[self.image_key_columns[0]]==image_key[0]
        features = self._object_table[self.colnames][sel]            
        cellids  = self._object_table[self.object_id][sel]
                        
        np.savez(filename, features=np.array(features, dtype=float), cellids=np.squeeze(np.array(cellids)))

    def _create_cache_counts(self, resume):
        """
        Does not create a key for images with zero objects - this may not longer be true
        """
        if resume and os.path.exists(self._counts_filename):
            return
        
        assert len(self.image_key_columns) == 1, "_create_cache_image does not currently support composite image_key"
        
        counts = self._object_table[self.image_key_columns[0]].value_counts()
        counts = pd.DataFrame(counts, columns=['count'])
        counts['ImageNumber'] = counts.index
        
        with cpa.util.replace_atomically(self._counts_filename) as f:
            pickle.dump(counts, f)

def _check_directory(dir, resume):
    if os.path.exists(dir):
        if not resume:
            logger.error('Directory exists already (remove or use -r): ' + dir)
            sys.exit(1)
    else:
        os.makedirs(dir)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = OptionParser("usage: %prog [-r] [-c colnames] PLATE-DIR ")
    parser.add_option('-r', '--resume', dest='resume', action='store_true', help='resume')
    parser.add_option('-k', '--image_key_columns', dest='image_key_columns', action='store', default='ImageNumber', help='image_key_columns',)
    parser.add_option('-p', '--plate_id', dest='plate_id', action='store', default='Metadata_Barcode', help='plate_id')
    parser.add_option('-j', '--object_id', dest='object_id', action='store', default='ObjectNumber', help='object_id')
    parser.add_option('-d', '--debug_limit', dest='debug_limit', action='store', type='int', default=-1, help='debug_limit')
    
    options, args = parser.parse_args()

    if len(args) != 1:
        parser.error('Incorrect number of arguments')
    cache_dir = os.path.join(args[0], "profiling_params")

    _check_directory(cache_dir, options.resume)

    cache = Cache(cache_dir)

    cache._create_cache(options.resume)
    # if predicate != '':
    #     for Normalization in normalizations.values():
    #         Normalization(cache)._create_cache(predicate, options.resume)
    # else:
    #     print 'Not performing normalization because not predicate was specified.'
