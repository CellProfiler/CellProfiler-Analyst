#!/usr/bin/env python

def _compute_mixture_probabilities((cache_dir, normalization_name, 
                                    preprocess_file, images, gmm, meanvector, 
                                    loadings)):
    import numpy as np        
    from cpa.profiling import cache
    cache = Cache(cache_dir)
    normalization = normalizations[normalization_name]
    normalizeddata, normalized_colnames, _ = cache.load(images, normalization=normalization)
    if preprocess_file:
        preprocessor = cpa.util.unpickle1(preprocess_file)
        normalizeddata = preprocessor(normalizeddata)
    mean_centered = normalizeddata - meanvector
    projected = np.dot(mean_centered, loadings)
    mixture_probabilities = gmm.predict_proba(projected)
    return mixture_probabilities.mean(0)

import logging
import sys
import os
from optparse import OptionParser
import numpy as np
from scipy import linalg
from sklearn.mixture import GMM
import cpa
from .cache import Cache, RobustLinearNormalization, normalizations
from .profiles import Profiles, add_common_options
from .parallel import ParallelProcessor, Uniprocessing
    
def profile_gmm(cache_dir, subsample_file, group_name, ncomponents=50, 
                filter=None, parallel=Uniprocessing(),
                normalization=RobustLinearNormalization, preprocess_file=None):
    cache = Cache(cache_dir)
    group, colnames_group = cpa.db.group_map(group_name, reverse=True, filter=filter)

    keys = group.keys()
    subsample = cpa.util.unpickle1(subsample_file)
    if preprocess_file:
        preprocessor = cpa.util.unpickle1(preprocess_file)
        subsample_data = preprocessor(subsample.data)
    else:
        subsample_data = subsample.data
    meanvector = np.mean(subsample_data, 0)
    mean_centered = subsample_data - meanvector

    #perform PCA
    U, s, V = linalg.svd(mean_centered, full_matrices=False)
    percvar_expl = s ** 2 / np.sum(s ** 2)
    scores = np.dot(U, np.diag(s))
    loadings = np.transpose(V)

    # Find the number of PCs required to explain x% of variance
    cutoffpercentage = 80
    percvar_cum = np.cumsum(percvar_expl)
    npc = np.nonzero(percvar_cum > float(cutoffpercentage) / 100)[0][0]
    if npc < 20: 
        npc = 20
   
    # GMM
    gmm = GMM(ncomponents, covariance_type='full', n_iter=100000, thresh=1e-7)
    gmm.fit(scores[:, :npc])

    parameters = [(cache_dir, normalization.__name__, preprocess_file,
                   group[g], gmm, meanvector, loadings[:, :npc])
                  for g in keys]
    variables = ['Component %d' % i for i in range(ncomponents)]
    return Profiles.compute(keys, variables, _compute_mixture_probabilities, 
                            parameters, parallel=parallel, group_name=group_name)

    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR SUBSAMPLE-FILE GROUP")
    ParallelProcessor.add_options(parser)
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    parser.add_option('--components', dest='ncomponents', type='int', default=5, help='number of mixture components')
    add_common_options(parser)
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, subsample_file, group_name = args
    cpa.properties.LoadFile(properties_file)

    profiles = profile_gmm(cache_dir, subsample_file, group_name, 
                           ncomponents=options.ncomponents, 
                           filter=options.filter, parallel=parallel,
                           normalization=normalizations[options.normalization],
                           preprocess_file=options.preprocess_file)
    if options.csv:
        profiles.save_csv(options.output_filename)
    else:
        profiles.save(options.output_filename)
