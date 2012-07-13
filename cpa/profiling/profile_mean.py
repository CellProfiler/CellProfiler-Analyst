#!/usr/bin/env python

import os
import sys
#import csv
import logging
from optparse import OptionParser
import numpy as np
import cpa
from .cache import Cache, RobustLinearNormalization, normalizations
from .profiles import Profiles, add_common_options
from .parallel import ParallelProcessor, Uniprocessing

def _compute_group_mean((cache_dir, images, normalization_name, 
                         preprocess_file)):
    try:
        import numpy as np
        from cpa.profiling.cache import Cache, normalizations
        cache = Cache(cache_dir)
        normalization = normalizations[normalization_name]
        data, colnames, _ = cache.load(images, normalization=normalization)
        
        if len(data) == 0:
            return np.empty(len(colnames)) * np.nan

        data = data[~np.isnan(np.sum(data, 1)), :]

        if len(data) == 0:
            return np.empty(len(colnames)) * np.nan

        if preprocess_file:
            preprocessor = cpa.util.unpickle1(preprocess_file)
            data = preprocessor(data)

        return np.mean(data, axis = 0)
    except: # catch *all* exceptions
        from traceback import print_exc
        import sys
        print_exc(None, sys.stderr)
        return None

def profile_mean(cache_dir, group_name, filter=None, parallel=Uniprocessing(),
                 normalization=RobustLinearNormalization, preprocess_file=None,
                 show_progress=True):
    group, colnames_group = cpa.db.group_map(group_name, reverse=True,
                                             filter=filter)

    keys = group.keys()
    parameters = [(cache_dir, group[g], normalization.__name__, preprocess_file)
                  for g in keys]

    if "CPA_DEBUG" in os.environ:
        DEBUG_NGROUPS = 5
        logging.warning('In debug mode. Using only a few groups (n=%d) to create profile' % DEBUG_NGROUPS)

        parameters = parameters[0:DEBUG_NGROUPS]
        keys = keys[0:DEBUG_NGROUPS]
    
    if preprocess_file:
        preprocessor = cpa.util.unpickle1(preprocess_file)
        variables = preprocessor.variables
    else:
        cache = Cache(cache_dir)
        variables = normalization(cache).colnames
    return Profiles.compute(keys, variables, _compute_group_mean, parameters,
                            parallel=parallel, group_name=group_name,
                            show_progress=show_progress)

    # def save_as_csv_file(self, output_file):
    #     csv_file = csv.writer(output_file)
    #     csv_file.writerow(list(self.colnames_group) + list(self.colnames))
    #     for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
    #         csv_file.writerow(list(gp) + list(datamean))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR GROUP")
    ParallelProcessor.add_options(parser)
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    add_common_options(parser)
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group = args

    cpa.properties.LoadFile(properties_file)

    profiles = profile_mean(cache_dir, group, filter=options.filter,
                            parallel=parallel, 
                            normalization=normalizations[options.normalization],
                            preprocess_file=options.preprocess_file)
    if options.csv:
        profiles.save_csv(options.output_filename)
    else:
        profiles.save(options.output_filename)
