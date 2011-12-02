#!/usr/bin/env python

import sys
#import csv
import logging
from optparse import OptionParser
import numpy as np
import cpa
from .cache import Cache, RobustLinearNormalization, normalizations
from .profiles import Profiles

def _compute_group_mean((cache_dir, images, normalization_name)):
    try:
        import numpy as np
        from cpa.util.cache import Cache, normalizations
        cache = Cache(cache_dir)
        normalization = normalizations[normalization_name]
        normalizeddata, normalized_colnames = cache.load(images,
                                                    normalization=normalization)
        if len(normalizeddata) == 0:
            return np.empty(len(normalized_colnames)) * np.nan

        normalizeddata = normalizeddata[
                ~np.isnan(np.sum(normalizeddata,1)),:]

        if len(normalizeddata) == 0:
            return np.empty(len(normalized_colnames)) * np.nan

        return np.mean(normalizeddata, axis = 0)
    except: # catch *all* exceptions
        from traceback import print_exc
        import sys
        print_exc(None, sys.stderr)
        return None

def profile_mean(cache_dir, group_name, filter=None, ipython_profile=None,
                 normalization=RobustLinearNormalization):
    cache = Cache(cache_dir)

    group, colnames_group = cpa.db.group_map(group_name, reverse=True,
                                             filter=filter)
    variables = normalization(cache).colnames

    keys = group.keys()
    parameters = [(cache_dir, group[g], normalization.__name__)
                  for g in keys]

    return Profiles.compute(keys, variables, _compute_group_mean, parameters,
                            ipython_profile, group_name=group_name)

    # def save_as_csv_file(self, output_file):
    #     csv_file = csv.writer(output_file)
    #     csv_file.writerow(list(self.colnames_group) + list(self.colnames))
    #     for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
    #         csv_file.writerow(list(gp) + list(datamean))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] [--normalization NORMALIZATION] PROPERTIES-FILE CACHE-DIR GROUP")
    parser.add_option('--ipython-profile', dest='ipython_profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-c', dest='csv', help='output as CSV', action='store_true')
    parser.add_option('--normalization', help='normalization method (default: RobustLinearNormalization)',
                      default='RobustLinearNormalization')
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group = args

    cpa.properties.LoadFile(properties_file)

    profiles = profile_mean(cache_dir, group, filter=options.filter,
                            ipython_profile=options.ipython_profile,
                            normalization=normalizations[options.normalization])
    if options.csv:
        profiles.save_csv(options.output_filename)
    else:
        profiles.save(options.output_filename)
