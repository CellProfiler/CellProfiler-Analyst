#!/usr/bin/env python
#
# python -m cpa.util.median_profiles -o treatment_profiles_mean.txt ~/src/az/properties/supplement.properties well_profiles_mean.txt Well CompoundConcentration

import itertools
import sys
from optparse import OptionParser
import numpy as np
import cpa

def parse_arguments():
    parser = OptionParser("usage: %prog [-o OUTPUT-FILENAME] PROPERTIES-FILE INPUT-FILENAME INPUT-GROUP OUTPUT-GROUP")
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    options, args = parser.parse_args()
    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    return options, args

# XXX: Move out into separate module
class Profiles(object):
    def __init__(self, keys, data, variables, key_size=None):
        assert isinstance(keys, list)
        assert all(isinstance(k, tuple) for k in keys)
        assert all(isinstance(v, str) for v in variables)
        self.keys = keys
        self.data = np.array(data)
        self.variables = variables
        if key_size is None:
            self.key_size = len(keys[0])
        else:
            self.key_size = key_size

    @classmethod
    def load(cls, filename):
        data = []
        keys = []
        for i, line in enumerate(open(filename).readlines()):
            line = line.rstrip()
            if i == 0:
                headers = line.split('\t')
                try:
                    headers.index('')
                except ValueError:
                    print >>sys.stderr, '%s:%d: Error: Header should be empty for the key columns' % (filename, i + 1)
                    sys.exit(1)
                key_size = len(headers) - headers[::-1].index('')
                variables = headers[key_size:]
            else:
                row = line.split('\t')
                key = tuple(row[:key_size])
                values = row[key_size:]
                if len(values) != len(variables):
                    print >>sys.stderr, '%s:%d: Error: Expected %d feature values, found %d' % (filename, i + 1, len(variables), len(values))
                    sys.exit(1)
                keys.append(key)
                data.append(map(float, values))
        return cls(keys, np.array(data), variables, key_size)

    def save(self, filename=None):
        header = ['' for i in xrange(self.key_size)] + self.variables
        if isinstance(filename, str):
            f = open(filename, 'w')
        elif filename is None:
            f = sys.stdout
        else:
            f = filename
        try:
            print >>f, '\t'.join(header)
            for key, vector in zip(self.keys, self.data):
                print >>f, '\t'.join(map(str, itertools.chain(key, vector)))
        finally:
            f.close()

    def items(self):
        return itertools.izip(input_profiles.keys, input_profiles.data)

    def isnan(self):
        return np.any(np.isnan(vector))

    def assert_not_isnan(self):
        for key, vector in self.items():
            if np.any(np.isnan(vector)):
                print >>sys.stderr, 'Error: Profile %r has a NaN value.' % key
                sys.exit(1)


if __name__ == '__main__':
    options, (properties_file, input_filename, input_group_name, output_group_name) = parse_arguments()
    cpa.properties.LoadFile(properties_file)

    input_group_r, input_colnames = cpa.db.group_map(input_group_name, reverse=True)
    output_group, output_colnames = cpa.db.group_map(output_group_name)
    input_profiles = Profiles.load(input_filename)
    input_profiles.assert_not_isnan()

    d = {}
    for key, vector in input_profiles.items():
        images = input_group_r[key]
        groups = [output_group[image] for image in images]
        if groups.count(groups[0]) != len(groups):
            print >>sys.stderr, 'Error: Input group %r contains images in %d output groups' % (key, len(set(groups)))
            sys.exit(1)
        d.setdefault(groups[0], []).append(vector)


    output_profiles = Profiles(keys, [np.median(np.vstack(d[key]), 0)
                                      for key in keys], input_profiles.variables)
    output_profiles.save(options.output_filename)
