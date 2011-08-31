import sys
from cpa.util import cache
import cpa

    # read precomputed percentiles from disk
    # normalize the data
    # returns numpy array of the normalized data

def normalize(data, colnames, cache_dir, plate):
    percentiles_filename = os.path.join(cache_dir, plate, 'percentiles.npy')
    percentiles = np.load(percentiles_filename)
    assert data.shape[1] == percentiles.shape[1]
    return (data - percentiles[0]) / (percentiles[1] - percentiles[0])

    """
    >>> unnormalized = cache.load(cache_dir, plate, well)
    >>> colnames = cache.get_colnames(cache_dir)
    >>> normalized = normalize(unnormalized, colnames, plate)
    """

if __name__ == '__main__':
    properties, predicate, cache_dir = sys.argv[1:4]
    percentiles_dir = os.path.join(cache_dir, 'percentiles')
    plates = cpa.db.execute("select distinct %s from %s" % (cpa.properties.plate_id, cpa.properties.image_table))
    for plate in plates:
        features = []
        plate_dir = os.path.join(cache_dir, plate)
        percentiles_filename = os.path.join(plate_dir, 'percentiles.npy')
        for well in cpa.db.execute("select distinct %s from %s where %s" % (cpa.properties.well_id, cpa.properties.image_table, predicate)):
            features.append(cache.load(cache_dir, plate, well))
        if len(features) == 0:
            print 'No DMSO features for', plate
            continue
        features = np.vstack(features)
        print plate, len(features)
        m = features.shape[1]
        percentiles = np.ones((2, m)) * np.nan
        for j in xrange(m):
            percentiles[0, j] = scoreatpercentile(features[:, j], 1)
            percentiles[1, j] = scoreatpercentile(features[:, j], 99)
        np.save(percentiles_filename, percentiles)
        
