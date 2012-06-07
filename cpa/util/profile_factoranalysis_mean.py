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
from .parallel import ParallelProcessor, Uniprocessing

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

def subsample(cache_dir, image_sets, parallel):
    parameters = [(cache_dir, images) for images in image_sets]
    njobs = len(parameters)
    generator = parallel.view('profile_factor_analysis_mean.subsample').imap(_compute_group_subsample, parameters)
    try:
        import progressbar
        progress = progressbar.ProgressBar(widgets=['Subsampling:',
                                                    progressbar.Percentage(), ' ',
                                                    progressbar.Bar(), ' ', 
                                                    progressbar.Counter(), '/', 
                                                    str(njobs), ' ',
                                                    progressbar.ETA()],
                                           maxval=njobs)
        results = list(progress(generator))
    except ImportError:
        results = list(generator)

    subsample = []
    for i, (p, r) in enumerate(zip(parameters, results)):
        if r is None:
            logger.info('Retrying failed computation locally')
            r = _compute_group_subsample(p) # just to see throw the exception
        subsample.extend(r)

    print "the subsampling set contains %d items" % len(subsample)
    return subsample
      
def _compute_group_projection_and_mean((cache_dir, images, fa_node, mean, stdev)):
    try:
        import numpy as np        
        from cpa.util import cache
        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames, _ = cache.load(images, normalization=RobustLinearNormalization)
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
                                parallel=Uniprocessing(), save_model=None):
    cache = Cache(cache_dir)

    group, colnames_group = cpa.db.group_map(group_name, reverse=True, filter=filter)

    keys = group.keys()
    subsamples = subsample(cache_dir, [group[g] for g in keys], parallel)

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
                            parameters, parallel=parallel, group_name=group_name)

    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR GROUP")
    ParallelProcessor.add_options(parser)
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    parser.add_option('--factors', dest='nfactors', type='int', default=5, help='number of factors')
    parser.add_option('--save-model', dest='save_model', default=None, help='save pickled model to file')
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group_name = args
    cpa.properties.LoadFile(properties_file)

    profiles = profile_factoranalysis_mean(cache_dir, group_name, 
                                           nfactors=options.nfactors, 
                                           filter=options.filter,
                                           parallel=parallel,
                                           save_model=options.save_model)
    if options.csv:
        profiles.save_csv(options.output_filename)
    else:
        profiles.save(options.output_filename)
