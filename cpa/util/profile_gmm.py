#!/usr/bin/env python

import logging
import sys
import os
from optparse import OptionParser
import numpy as np
from scipy import linalg
from sklearn.mixture import GMM

import cpa
from cpa.util.cache import Cache, RobustLinearNormalization
from .profiles import Profiles
from .profile_factoranalysis_mean import subsample
            
def _compute_mixture_probabilities((cache_dir, images, gmm, meanvector, loadings)):
    import numpy as np        
    from cpa.util import cache
    cache = Cache(cache_dir)
    normalizeddata, normalized_colnames = cache.load(images, normalization=RobustLinearNormalization)
    mean_centered = normalizeddata - meanvector
    projected = np.dot(mean_centered, loadings)
    mixture_probabilities = gmm.predict_proba(projected)
    return mixture_probabilities.mean(0)
    
def profile_gmm(cache_dir, group_name, ncomponents=50, filter=None, 
                ipython_profile=None):
    cache = Cache(cache_dir)
    group, colnames_group = cpa.db.group_map(group_name, reverse=True, filter=filter)

    keys = group.keys()
    subsamples = subsample(cache_dir, [group[g] for g in keys], ipython_profile)

    subsampled = np.vstack(subsamples)
    meanvector = np.mean(subsampled, 0)
    mean_centered = subsampled - meanvector

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
    gmm = GMM(ncomponents, cvtype='full')
    gmm.fit(scores[:, :npc], n_iter=100000, thresh=1e-7)

    parameters = [(cache_dir, group[g], gmm, meanvector, loadings[:, :npc])
                  for g in keys]
    variables = ['Component %d' % i for i in range(ncomponents)]
    return Profiles.compute(keys, variables, _compute_mixture_probabilities, 
                            parameters, ipython_profile, group_name=group_name)

    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [--ipython-profile FILENAME] [-o FILENAME] [-f FILTER-NAME] [--ncomponents INTEGER] PROPERTIES-FILE CACHE-DIR GROUP")
    parser.add_option('--ipython-profile', dest='ipython_profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    parser.add_option('--components', dest='ncomponents', type='int', default=5, help='number of mixture components')
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group_name = args
    cpa.properties.LoadFile(properties_file)

    profiles = profile_gmm(cache_dir, group_name, ncomponents=options.ncomponents, 
                           filter=options.filter,
                           ipython_profile=options.ipython_profile)
    if options.csv:
        profiles.save_csv(options.output_filename)
    else:
        profiles.save(options.output_filename)
