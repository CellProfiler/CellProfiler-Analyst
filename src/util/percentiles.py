import sys
from cpa.util import cache

def normalize(data, colnames, cache_dir, plate):
    """
    >>> unnormalized = cache.load(cache_dir, plate, well)
    >>> colnames = cache.get_colnames(cache_dir)
    >>> normalized = normalize(unnormalized, colnames, plate)
    """
    # read precomputed percentiles from disk
    # normalize the data
    # returns numpy array of the normalized data

if __name__ == '__main__':
    properties, predicate, cache_dir = sys.argv[1:4]
    percentiles_dir = os.path.join(cache_dir, 'percentiles')
    
    plates = ...
    for plate in plates:
        features = []
        for well in ...read DMSO wells from DB using predicate...:
            features.append(cache.load(cache_dir, plate, well))
        # compute percentiles from np.vstack(features)
        # save percentiles for this plate in a separate file

        
