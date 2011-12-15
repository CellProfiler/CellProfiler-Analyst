#!/usr/bin/env python

import io
import sys
import os
import csv
import logging
from optparse import OptionParser
import numpy as np
import time
import itertools
import cpa
from cpa.util.cache import Cache, RobustLinearNormalization
from profiles import Profiles
from .parallel import ParallelProcessor, Uniprocessing

logger = logging.getLogger(__name__)

def _compute_ksstatistic((cache_dir, images, control_images)):
    import numpy as np 
    import sys
    from cpa.util.cache import Cache, RobustLinearNormalization
    from cpa.util.ks_2samp import ks_2samp

    cache = Cache(cache_dir)
    normalizeddata, variables = cache.load(images, normalization=RobustLinearNormalization)
    control_data, control_colnames = cache.load(control_images, normalization=RobustLinearNormalization)
    assert len(control_data) >= len(normalizeddata)
    assert variables == control_colnames
    #downsampled = control_data[np.random.randint(0, len(control_data), len(normalizeddata)), :]
    m = len(variables)
    profile = np.empty(m)
    for j in range(m):
        profile[j] = ks_2samp(control_data[:, j], normalizeddata[:, j],
			      signed=True)[0]
    return profile
        
def images_by_plate(filter, plate_group=None):
    if plate_group is None:
        return {None: cpa.db.execute(cpa.db.filter_sql(filter))}
    else:
        plate_group_r, plate_colnames = cpa.db.group_map(plate_group, reverse=True, filter=filter)
	return plate_group_r

def profile_ksstatistic(cache_dir, group_name, control_filter, plate_group,
                        filter=None, parallel=Uniprocessing()):
    cache = Cache(cache_dir)
    group, colnames_group = cpa.db.group_map(group_name, reverse=True, 
                                             filter=filter)
    variables = RobustLinearNormalization(cache).colnames
    control_images_by_plate = images_by_plate(control_filter, plate_group)
    plate_by_image = dict((row[:-2], tuple(row[-2:-1]))
                          for row in cpa.db.GetPlatesAndWellsPerImage())

    def control_images(treated_images):
        if plate_group is None:
            return control_images_by_plate[None]
        else:
            return [r for image in treated_images
                    for r in control_images_by_plate[plate_by_image[image]]]

    keys = group.keys()
    parameters = [(cache_dir, group[k], control_images(group[k]))
                  for k in keys]

    return Profiles.compute(keys, variables, _compute_ksstatistic, 
                            parameters, parallel=parallel, 
                            group_name=group_name)
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR GROUP CONTROL-FILTER")
    ParallelProcessor.add_options(parser)
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-p', dest='plate_group', help='CPA group defining plates')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group, control_filter = args

    cpa.properties.LoadFile(properties_file)
    profiles = profile_ksstatistic(cache_dir, group, control_filter, 
				   options.plate_group,
                                   filter=options.filter, parallel=parallel)
    profiles.save(options.output_filename)
