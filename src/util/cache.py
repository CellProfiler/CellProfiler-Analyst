'''
Cache of per-well block of per-cell feature data.
'''

import sys
import os
import logging
import numpy as np
import cpa

logger = logging.getLogger(__name__)

def _filename(cache_dir, plate_name, well_name):
    return os.path.join(cache_dir, plate_name, well_name + '.npy')

def load(cache_dir, plate_name, well_name):
    return np.load(_filename(cache_dir, plate_name, well_name))

def get_colnames(cache_dir):
    return open(os.path.join(cache_dir, 'colnames.txt'), 'rU').readlines()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    program_name = os.path.basename(sys.argv[0])
    if len(sys.argv) != 3:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR' % program_name
        sys.exit(os.EX_USAGE)
    properties_file, cache_dir = sys.argv[1:]

    cpa.properties.LoadFile(properties_file)

    if os.path.exists(cache_dir):
        logger.error('Cache directory exists already')
        sys.exit(os.EX_DATAERR)
    os.mkdir(cache_dir)

    cols = cpa.db.GetColnamesForClassifier()
    with open(os.path.join(cache_dir, 'colnames.txt'), 'w') as f:
        for col in cols:
            print >>f, col

    wells = cpa.db.execute('select distinct %s, %s from %s'%
                           (cpa.properties.plate_id, 
                            cpa.properties.well_id, 
                            cpa.properties.image_table))

    for i, plate, well in enumerate(wells):
        logger.info('Well %d of %d' % (i + 1, len(wells)))
        plate_dir = os.path.join(cache_dir, plate)
        if not os.path.exist(plate_dir):
            os.mkdir(plate_dir)
        features = cpa.db.execute("""select %s from %s join %s using (%s, %s) 
                                     where %s = %%s and %s = %%s""" % (
                ','.join(cols), cpa.properties.object_table, 
                cpa.properties.image_table, cpa.properties.table_id, 
                cpa.properties.image_id, cpa.properties.plate_id,
                cpa.properties.well_id), (plate, well))
        np.save(_filename(cache_dir, plate, well), features)

    # Test the other functions in the module
    assert cols == get_colnames(cache_dir)
    data = load(cache_dir, wells[0][0], wells[0][1])
    assert data.shape[1] == len(cols)
