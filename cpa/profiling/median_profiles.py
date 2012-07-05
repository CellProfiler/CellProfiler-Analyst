#!/usr/bin/env python
#
# python -m cpa.profiling.median_profiles -o treatment_profiles_mean.txt ~/src/az/properties/supplement.properties well_profiles_mean.txt Well CompoundConcentration

import itertools
import sys
from optparse import OptionParser
import numpy as np
import cpa
from .profiles import Profiles

def parse_arguments():
    parser = OptionParser("usage: %prog [-c] [-o OUTPUT-FILENAME] PROPERTIES-FILE INPUT-FILENAME OUTPUT-GROUP")
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-c', dest='csv', help='input and output as CSV', action='store_true')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    return options, args

def aggregate_profiles(profiles, group_name, aggregator):
    profiles.assert_not_isnan()
    input_group_r, input_colnames = cpa.db.group_map(profiles.group_name, reverse=True)
    input_group_r = dict((tuple(map(str, k)), v) 
                         for k, v in input_group_r.items())
    output_group, output_colnames = cpa.db.group_map(group_name)

    d = {}
    for key, vector in profiles.items():
        images = input_group_r[key]
        groups = [output_group[image] for image in images]
        if groups.count(groups[0]) != len(groups):
            raise 'Error: Input group %r contains images in %d different output groups' % (key, len(set(groups)))
        d.setdefault(groups[0], []).append(vector)

    keys = d.keys()
    return Profiles(keys, [aggregator(np.vstack(d[key]), 0)
                           for key in keys], profiles.variables,
                    group_name=group_name)

def median_profiles(profiles, group_name):
    return aggregate_profiles(profiles, group_name, np.median)

if __name__ == '__main__':
    options, (properties_file, input_filename, group_name) = parse_arguments()
    cpa.properties.LoadFile(properties_file)

    if options.csv:
        input_profiles = Profiles.load_csv(input_filename)
    else:
        input_profiles = Profiles.load(input_filename)

    output_profiles = median_profiles(input_profiles, group_name)

    if options.csv:
        output_profiles.save_csv(options.output_filename)
    else:
        output_profiles.save(options.output_filename)
