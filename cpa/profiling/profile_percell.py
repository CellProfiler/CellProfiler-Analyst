#!/usr/bin/env python

import sys
import os
import logging
from optparse import OptionParser
import numpy as np
import cpa
from .cache import Cache
from .normalization import DummyNormalization, RobustLinearNormalization, RobustStdNormalization, normalizations
from .profiles import Profiles
from .parallel import ParallelProcessor, Uniprocessing
import string

def _transform_cell_feats((cache_dir, images, normalization_name, output_filename, key, header)):
    try:
        import numpy as np
        from .cache import Cache
        from .normalization import DummyNormalization, RobustLinearNormalization, RobustStdNormalization, normalizations
        cache = Cache(cache_dir)
        normalization = normalizations[normalization_name]
        normalizeddata, normalized_colnames, cell_ids = cache.load(images,
                                                                   normalization=normalization)
        if len(normalizeddata) == 0:
            return np.empty(len(normalized_colnames)+1) * np.nan # +1 is for cell_ids

        normalizeddata = normalizeddata[
                ~np.isnan(np.sum(normalizeddata,1)),:]

        if len(normalizeddata) == 0:
            return np.empty(len(normalized_colnames)+1) * np.nan # +1 is for cell_ids

        # save the features to csv
        import csv
        key = [str(k) for k in key]
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        key_str = "".join(c for c in "-".join(key) if c in valid_chars)
        
        filename = output_filename + "-" + key_str + ".csv"
        
        with open(filename, 'w') as f: 
            w = csv.writer(f)
            w.writerow(header)
        
            for i, (cell_id,vector) in enumerate(zip(cell_ids, normalizeddata)):
                w.writerow(tuple(key) + tuple([cell_id]) + tuple(vector))
        
        return [-1]

    except: # catch *all* exceptions
        from traceback import print_exc
        import sys
        print_exc(None, sys.stderr)
        return None

def cell_feats(cache_dir, group_name, filter=None, parallel=Uniprocessing(),
                 normalization=RobustLinearNormalization, output_filename=None):
    cache = Cache(cache_dir)

    group, colnames_group = cpa.db.group_map(group_name, reverse=True,
                                             filter=filter)
    variables = normalization(cache).colnames

    header = tuple(colnames_group) + tuple(["cell_id"]) + tuple(variables)
    keys = group.keys()

    # #HACK!
    # import random
    # seed = lambda : 0.5
    # n = int(len(keys)*.20)
    # random.shuffle(keys, seed)
    # keys = keys[0:n-1] 
    # #HACK!

    parameters = [(cache_dir, group[g], normalization.__name__, output_filename, 
                   g, header)
                  for g in keys]

    if "CPA_DEBUG" in os.environ:
        DEBUG_NGROUPS = 3
        logging.warning('In debug mode. Using only a few groups (n=%d) to create profile' % DEBUG_NGROUPS)

        parameters = parameters[0:DEBUG_NGROUPS]
        keys = keys[0:DEBUG_NGROUPS]
    

    Profiles.compute(keys, variables, _transform_cell_feats, parameters,
                     parallel=parallel, group_name=group_name)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR GROUP")
    ParallelProcessor.add_options(parser)
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    parser.add_option('--normalization', help='normalization method (default: RobustLinearNormalization)',
                      default='RobustLinearNormalization')
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group = args

    cpa.properties.LoadFile(properties_file)

    cell_feats(cache_dir, group, filter=options.filter,
               parallel=parallel,
               normalization=normalizations[options.normalization],
               output_filename=options.output_filename)
