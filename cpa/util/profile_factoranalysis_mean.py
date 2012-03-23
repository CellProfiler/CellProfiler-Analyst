#!/usr/bin/env python

import logging
import sys
import os
from optparse import OptionParser
import progressbar
import numpy as np
import mdp.nodes as nodes

import cpa
from cpa.util.cache import Cache, RobustLinearNormalization
from .profiles import Profiles
from .lsf import LSF

logger = logging.getLogger(__name__)
            
def _compute_group_subsample((cache_dir, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames, _ = cache.load(images, normalization=RobustLinearNormalization)
        np.random.shuffle(normalizeddata)
        normalizeddata_sample = [x for i, x in enumerate(normalizeddata) if i % 1000 == 0]
        return normalizeddata_sample
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,)
        return None

def subsample(cache_dir, image_sets, ipython_profile):
    parameters = [(cache_dir, images) for images in image_sets]

    if isinstance(ipython_profile, LSF):
        view = ipython_profile.view('subsample')
        logger.debug('Running %d jobs on LSF' % view.njobs)
        generator = view.imap(_compute_group_subsample, parameters)
    elif ipython_profile:
        from IPython.parallel import Client, LoadBalancedView
        client = Client(profile='lsf')
        lview = client.load_balanced_view()
        generator = lview.imap(_compute_group_subsample, parameters)
    elif ipython_profile == False:
        generator = (_compute_group_subsample(p) for p in parameters)
    else:
        from multiprocessing import Pool
        lview = Pool()
        generator = lview.imap(_compute_group_subsample, parameters)
    progress = progressbar.ProgressBar(widgets=['Subsampling:',
                                                progressbar.Percentage(), ' ',
                                                progressbar.Bar(), ' ', 
                                                progressbar.Counter(), '/', 
                                                str(len(parameters)), ' ',
                                                progressbar.ETA()],
                                       maxval=len(parameters))
    results = list(generator)

    subsample = []
    for i, (p, r) in enumerate(zip(parameters, results)):
        if r is None:
            print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[i][1]
            results[i] = _compute_group_subsample(p) # just to see throw the exception
        subsample.extend(r)

    print "the subsampling set contains %d items" % len(subsample)
    return subsample
      
def _compute_group_projection_and_mean((cache_dir, images, fa_node, mean, stdev)):
    try:
        import numpy as np        
        from cpa.util import cache
        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames = cache.load(images, normalization=RobustLinearNormalization)
        normalizeddata = (normalizeddata - mean) / stdev
        normalizeddata_projected = fa_node.execute(normalizeddata)
        normalizeddata_projected_mean = np.mean(normalizeddata_projected, axis = 0)
        return normalizeddata_projected_mean
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,)
        return None
        

    
def profile_factoranalysis_mean(cache_dir, group_name, nfactors=5, filter=None, 
                                ipython_profile=None, save_model=None):
    cache = Cache(cache_dir)

    group, colnames_group = cpa.db.group_map(group_name, reverse=True, filter=filter)

    keys = group.keys()
    subsamples = subsample(cache_dir, [group[g] for g in keys], ipython_profile)

    mean = np.mean(subsamples, axis=0)   
    subsampled_data = subsamples - mean
    stdev = np.std(subsampled_data, axis=0)
    subsampled_data = subsampled_data / stdev

    nfactors = min(nfactors, subsampled_data.shape[1])
    variables = ['Factor %d' % (i + 1) for i in range(nfactors)]
    fa_node = nodes.FANode(input_dim=None, output_dim=nfactors, dtype=None, max_cycles=30)
    print 'Training'
    fa_node.train(subsampled_data)
    fa_node.stop_training()

    if save_model:
        cpa.util.pickle(save_model, fa_node)
    
    parameters = [(cache_dir, group[g], fa_node, mean, stdev)
                  for g in keys]
    return Profiles.compute(keys, variables, _compute_group_projection_and_mean, 
                            parameters, ipython_profile, group_name=group_name)

    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [--ipython-profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] [--factors NFACTORS] [--save-model FILENAME] PROPERTIES-FILE CACHE-DIR GROUP")
    parser.add_option('--ipython-profile', dest='ipython_profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    parser.add_option('--factors', dest='nfactors', type='int', default=5, help='number of factors')
    parser.add_option('--save-model', dest='save_model', default=None, help='save pickled model to file')
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group_name = args
    cpa.properties.LoadFile(properties_file)

    profiles = profile_factoranalysis_mean(cache_dir, group_name, nfactors=options.nfactors, 
                                           filter=options.filter,
                                           ipython_profile=options.ipython_profile,
                                           save_model=options.save_model)
    if options.csv:
        profiles.save_csv(options.output_filename)
    else:
        profiles.save(options.output_filename)
