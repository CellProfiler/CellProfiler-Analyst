#!/usr/bin/env python

def _compute_ksstatistic((cache_dir, images, control_images, preprocess_file)):
    import numpy as np 
    import sys
    from cpa.profiling.cache import Cache, RobustLinearNormalization
    from cpa.profiling.ks_2samp import ks_2samp

    cache = Cache(cache_dir)
    normalizeddata, variables, _ = cache.load(images, normalization=RobustLinearNormalization)
    control_data, control_colnames, _ = cache.load(control_images, normalization=RobustLinearNormalization)
    assert len(control_data) >= len(normalizeddata)
    assert variables == control_colnames
    if preprocess_file:
        preprocessor = cpa.util.unpickle1(preprocess_file)
        normalizeddata = preprocessor(normalizeddata)
        control_data = preprocessor(control_data)
        variables = preprocessor.variables
    #downsampled = control_data[np.random.randint(0, len(control_data), len(normalizeddata)), :]
    m = len(variables)
    profile = np.empty(m)
    for j in range(m):
        profile[j] = ks_2samp(control_data[:, j], normalizeddata[:, j],
			      signed=True)[0]
    return profile

import io
import sys
import os
import csv
import logging
from optparse import OptionParser
import numpy as np
import cpa
from .cache import Cache, RobustLinearNormalization, normalizations
from profiles import Profiles, add_common_options
from .parallel import ParallelProcessor, Uniprocessing

logger = logging.getLogger(__name__)
        
def images_by_plate(filter, plate_group=None):
    if plate_group is None:
        return {None: cpa.db.execute(cpa.db.filter_sql(filter))}
    else:
        plate_group_r, plate_colnames = cpa.db.group_map(plate_group, reverse=True, filter=filter)
	return plate_group_r

def profile_ksstatistic(cache_dir, group_name, control_filter, plate_group,
                        filter=None, parallel=Uniprocessing(),
                        normalization=RobustLinearNormalization, 
                        preprocess_file=None):
    group, colnames_group = cpa.db.group_map(group_name, reverse=True, 
                                             filter=filter)
    control_images_by_plate = images_by_plate(control_filter, plate_group)
    plate_by_image = dict((row[:-2], tuple(row[-2:-1]))
                          for row in cpa.db.GetPlatesAndWellsPerImage())

    def control_images(treated_images):
        if plate_group is None:
            return control_images_by_plate[None]
        else:
            return list(set(r for image in treated_images
                            for r in control_images_by_plate[plate_by_image[image]]))

    keys = group.keys()
    parameters = [(cache_dir, group[k], control_images(group[k]), preprocess_file)
                  for k in keys]

    if preprocess_file:
        preprocessor = cpa.util.unpickle1(preprocess_file)
        variables = preprocessor.variables
    else:
        cache = Cache(cache_dir)
        variables = normalization(cache).colnames
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
    add_common_options(parser)
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group, control_filter = args

    cpa.properties.LoadFile(properties_file)
    profiles = profile_ksstatistic(cache_dir, group, control_filter, 
				   options.plate_group,
                                   filter=options.filter, parallel=parallel,
                                   normalization=normalizations[options.normalization],
                                   preprocess_file=options.preprocess_file)
    profiles.save(options.output_filename)
