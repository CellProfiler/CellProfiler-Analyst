#!/usr/bin/env python

import sys
#import csv
import logging
from optparse import OptionParser
import numpy as np
import cpa
from .cache import Cache, RobustLinearNormalization
from .profiles import Profiles

def _compute_group_mean((cache_dir, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=RobustLinearNormalization)
        normalizeddata_mean = np.mean(normalizeddata, axis = 0)
        return normalizeddata_mean
    except: # catch *all* exceptions
        from traceback import print_exc
        import sys
        print_exc(None, sys.stderr)

def profile_mean(cache_dir, group_name, filter=None, ipython_profile=None):
    cpa.properties.LoadFile(properties_file)
    cache = Cache(cache_dir)

    group, colnames_group = cpa.db.group_map(group_name, reverse=True, filter=filter)
    variables = RobustLinearNormalization(cache).colnames

    keys = group.keys()
    parameters = [(cache_dir, group[g]) for g in keys]

    return Profiles.compute(keys, variables, _compute_group_mean, parameters,
                            ipython_profile, group_name=group_name)

    # def save_as_csv_file(self, output_file):
    #     csv_file = csv.writer(output_file)
    #     csv_file.writerow(list(self.colnames_group) + list(self.colnames))
    #     for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
    #         csv_file.writerow(list(gp) + list(datamean))
    
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] PROPERTIES-FILE CACHE-DIR GROUP")
    parser.add_option('--ipython-profile', dest='ipython_profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group = args

    cpa.properties.LoadFile(properties_file)

    profiles = profile_mean(cache_dir, group, filter=options.filter, 
                            ipython_profile=options.ipython_profile)
    profiles.save(options.output_filename)
