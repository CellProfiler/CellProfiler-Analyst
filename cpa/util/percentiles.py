'''

Example usage as script:

$ py -m cpa.util.percentiles Morphology.properties "Image_LoadedText_Compounds = 'DMSO'" /broad/shptmp/ljosa/az_cache

Example usage as module:

>>> import cpa
>>> from cpa.util import cache
>>> from cpa.util import percentiles
>>> cpa.properties.LoadFile('Morphology.properties')
>>> cache_dir = '/broad/shptmp/ljosa/az_cache'
>>> predicate = "Image_LoadedText_Compounds = 'DMSO'"
>>> unnormalized = cache.load(cache_dir, 'Week1_22123', 'B02')
>>> normalized = percentiles.normalize(unnormalized, cache_dir, 'Week1_22123')

>>> unnormalized_colnames = cache.get_colnames(cache_dir)
>>> normalized_colnames = percentiles.get_colnames(cache_dir)

'''

import sys
import os
import numpy as np
from scipy.stats.stats import scoreatpercentile
import cpa
from cpa.util import cache

    # read precomputed percentiles from disk
    # normalize the data
    # returns numpy array of the normalized data

def _filename(cache_dir, plate):
    return os.path.join(cache_dir, 'percentiles', unicode(plate) + '.npy')

def get_control_wells(predicate):
    """
    Return a dictionary mapping plate names to lists of control
    wells.
    """
    plates_and_wells = {}
    for plate, well in cpa.db.execute("select distinct %s, %s from %s where %s"%
                                      (cpa.properties.plate_id, cpa.properties.well_id, 
                                       cpa.properties.image_table, predicate)):
        plates_and_wells.setdefault(plate, []).append(well)
    return plates_and_wells

def _calculate_nonzero_variance(cache_dir, predicate):
    """
    Return a boolean vector indicating which features have non-zero
    variance for the populations of control wells of every plate.
    """
    colmask = None
    for plate, wells in get_control_wells(predicate).items():
        percentiles = np.load(_filename(cache_dir, plate))
        if len(percentiles) == 0:
            continue # No DMSO wells, so no percentiles
        nonzero = percentiles[0] != percentiles[1]
        if colmask is None:
            colmask = nonzero
        else:
            colmask &= nonzero
    return colmask

def get_nonzero_variance(cache_dir):
    return np.load(os.path.join(cache_dir, 'nonzero_variance.npy'))

def get_colnames(cache_dir):
    colmask = get_nonzero_variance(cache_dir)
    return [col for col, include in zip(cache.get_colnames(cache_dir), colmask)
            if include]

def normalize(data, cache_dir, plate):
    """
    Normalize the 
    """
    percentiles = np.load(_filename(cache_dir, plate))
    assert data.shape[1] == percentiles.shape[1]
    nonzero_variance = get_nonzero_variance(cache_dir)
    percentiles = percentiles[:, nonzero_variance]
    data = data[:, nonzero_variance]
    divisor = (percentiles[1] - percentiles[0])
    assert np.all(divisor > 0)
    return (data - percentiles[0]) / divisor

if __name__ == '__main__':
    program_name = os.path.basename(sys.argv[0])
    if len(sys.argv) != 4:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE PREDICATE CACHE-DIR' % program_name
        sys.exit(os.EX_USAGE)
    properties_file, predicate, cache_dir = sys.argv[1:4]
    cpa.properties.LoadFile(properties_file)
    percentiles_dir = os.path.join(cache_dir, 'percentiles')
    if not os.path.exists(percentiles_dir):
        os.mkdir(percentiles_dir)

    colnames = cache.get_colnames(cache_dir)
    control_wells = get_control_wells(predicate)
    for i, (plate, wells) in enumerate(control_wells.items()):
        features = []
        for well in wells:
            data = cache.load(cache_dir, plate, well)
            if len(data) > 0:
                features.append(data)
        if len(features) == 0:
            print 'No DMSO features for plate', plate
            percentiles = np.zeros((0, len(colnames)))
        else:
            features = np.vstack(features)
            m = features.shape[1]
            percentiles = np.ones((2, m)) * np.nan
            for j in xrange(m):
                percentiles[0, j] = scoreatpercentile(features[:, j], 1)
                percentiles[1, j] = scoreatpercentile(features[:, j], 99)
        np.save(_filename(cache_dir, plate), percentiles)
        print '%d of %d' % (i + 1, len(control_wells.keys()))

    nz = _calculate_nonzero_variance(cache_dir, predicate)
    np.save(os.path.join(cache_dir, 'nonzero_variance.npy'), nz)

    # Run tests
    import doctest
    doctest.testmod()
