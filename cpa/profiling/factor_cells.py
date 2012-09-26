import sys
import re
import logging
from optparse import OptionParser
import numpy as np
from scipy.spatial.distance import cdist
import pylab
import cpa
from .profiles import add_common_options
from .preprocessing import NullPreprocessor
from .cache import Cache, normalizations

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR PREPROCESSOR [NSTEPS]")
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    add_common_options(parser)
    options, args = parser.parse_args()

    if len(args) not in [3, 4]:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, preprocess_file = args[:3]
    nsteps = int(args[3]) if len(args) == 4 else 20

    normalization = normalizations[options.normalization]
    if preprocess_file is None:
        preprocessor = NullPreprocessor(normalization.colnames)
    else:
        preprocessor = cpa.util.unpickle1(preprocess_file)
    cpa.properties.LoadFile(properties_file)
    cache = Cache(cache_dir)

    if options.filter:
        image_keys = cpa.db.GetFilteredImages(options.filter)
    else:
        image_keys = cpa.db.GetAllImageKeys()

    nfactors = len(preprocessor.variables)
    min_distances = np.ones(nfactors * nsteps) * np.inf
    nearest_neighbors = [None] * nfactors * nsteps
    min_profile = np.ones(nfactors) * np.inf
    max_profile = np.ones(nfactors) * -np.inf

    njobs = len(image_keys)

    def make_progress():
        show_progress = True
        if show_progress:
            import progressbar
            return progressbar.ProgressBar(widgets=[progressbar.Percentage(), ' ',
                                                        progressbar.Bar(), ' ', 
                                                        progressbar.Counter(), '/', 
                                                        str(njobs), ' ',
                                                        progressbar.ETA()],
                                               maxval=njobs)
        else:
            return lambda x: x

    # Get the range of each variable

    for image_key in make_progress()(image_keys):
        data, colnames, object_keys = cache.load([image_key], normalization=normalization)
        if len(data) == 0:
            continue
        data = preprocessor(data)
        min_profile = np.minimum(min_profile, np.min(data, 0))
        max_profile = np.maximum(max_profile, np.max(data, 0))

    print >>sys.stderr, 'RANGES:'
    for i in range(nfactors):
        print >>sys.stderr, i + 1, min_profile[i], max_profile[i]
    print >>sys.stderr

    values = np.vstack([np.linspace(min_profile[i], max_profile[i], nsteps)
                        for i in range(nfactors)])

    # Pick cells

    for image_key in make_progress()(image_keys):
        data, colnames, object_keys = cache.load([image_key], normalization=normalization)
        if len(data) == 0:
            continue
        data = preprocessor(data)
        distances = np.zeros((len(data), nfactors * nsteps))
        for i in range(len(data)):
            for factor in range(nfactors):
                for step in range(nsteps):
                    distance = np.abs(data[i, factor] - values[factor, step])
                    distances[i, factor * nsteps + step] = distance
        assert distances.shape[1] == nfactors * nsteps
        cell_indices, target_indices = np.nonzero(distances < min_distances)
        for i, j in zip(cell_indices, target_indices):
            min_distances[j] = distances[i, j]
            nearest_neighbors[j] = image_key + (object_keys[i],)

    print 'label', ' '.join([re.sub(' ', '_', v) for v in preprocessor.variables])
    for i, label in enumerate(preprocessor.variables):
        for j in range(nsteps):
            print re.sub(' ', '_', label), ' '.join(map(str, nearest_neighbors[i * nsteps + j]))
