'''
Cache of per-well block of per-cell feature data.

Example usage as a script:

$ py -m cpa.util.cache CDP2.properties /imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache
'''

import sys
import os
import logging
from optparse import OptionParser
import numpy as np
import cpa

logger = logging.getLogger(__name__)

def _filename(cache_dir, plate_name, well_name):
    return os.path.join(cache_dir, unicode(plate_name), well_name + '.npy')

def load(cache_dir, plate_name, well_name):
    """Load the raw features of all the cells in a particular well and
    return them as a ncells x nfeatures numpy array."""
    return np.load(_filename(cache_dir, plate_name, well_name))

def get_colnames(cache_dir):
    return [line.rstrip() 
            for line in open(os.path.join(cache_dir, 'colnames.txt'), 'rU').readlines()]

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = OptionParser("usage: %prog [-f] PROPERTIES-FILE CACHE-DIR")
    parser.add_option('-f', dest='overwrite', action='store_true')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir = args

    cpa.properties.LoadFile(properties_file)

    if os.path.exists(cache_dir):
        if options.overwrite:
            for root, dirs, files in os.walk(cache_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        else:
            logger.error('Cache directory exists already')
    else:
        os.mkdir(cache_dir)

    cols = cpa.db.GetColnamesForClassifier()
    with open(os.path.join(cache_dir, 'colnames.txt'), 'w') as f:
        for col in cols:
            print >>f, col

    wells = cpa.db.execute('select distinct %s, %s from %s'%
                           (cpa.properties.plate_id, 
                            cpa.properties.well_id, 
                            cpa.properties.image_table))

    for i, (plate, well) in enumerate(wells):
        logger.info('Well %d of %d' % (i + 1, len(wells)))
        filename = _filename(cache_dir, plate, well)
        plate_dir = os.path.dirname(filename)
        if not os.path.exists(plate_dir):
            os.mkdir(plate_dir)
        if cpa.properties.table_id:
            using_clause = 'using (%s, %s)' % (cpa.properties.table_id,
                                               cpa.properties.image_id)
        else:
            using_clause = 'using (%s)' % cpa.properties.image_id
        features = cpa.db.execute("""select %s from %s join %s %s 
                                     where %s = %%s and %s = %%s""" % (
                ','.join(cols), cpa.properties.object_table, 
                cpa.properties.image_table, using_clause, 
                cpa.properties.plate_id, cpa.properties.well_id), 
                                  (plate, well))
        np.save(filename, features)

    # Test the other functions in the module
    assert cols == get_colnames(cache_dir)
    data = load(cache_dir, wells[0][0], wells[0][1])
    assert data.shape[1] == len(cols)
