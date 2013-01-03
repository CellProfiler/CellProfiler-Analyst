import re
import sys
from optparse import OptionParser
import numpy as np
import cpa
from cpa.util import replace_atomically
from .profiles import Profiles

def rank_variables(profiles):
    keys = profiles.keys()
    nclasses = len(keys)
    result = {}
    for i in range(nclasses):
        this_profile = profiles.data[i]
        other_profiles = np.vstack([p for k, p in enumerate(profiles.data)
                                    if k != i])
        absdiff = np.min(np.abs(this_profile - other_profiles), 0)
        order = np.argsort(absdiff)[::-1]
        variables = []
        for feature_index in order[:15]:
            variables.append((absdiff[feature_index], profiles.variables[feature_index]))
        result[' '.join(keys[i])] = variables
    return result

def rank_variables_all_pairs(profiles):
    keys = profiles.keys()
    nclasses = len(keys)
    result = {}
    for i in range(nclasses):
        this_profile = profiles.data[i]
        for k in range(i + 1, nclasses):
            other_profile = profiles.data[k]
            absdiff = np.abs(this_profile - other_profile)
            order = np.argsort(absdiff)[::-1]
            variables = []
            for feature_index in order[:15]:
                variables.append((absdiff[feature_index], profiles.variables[feature_index]))
            result[' '.join(keys[i]) + ' / ' + ' '.join(keys[k])] = variables
    return result

def write_result_text(f, result):
    for i, class_ in enumerate(sorted(result.keys())):
        variables = result[class_]
        if i > 0:
            print >>f
        print >>f, class_
        for score, variable in variables:
            print >>f, '%f %s' % (score, variable)

def write_result_latex(f, result):
    for i, class_ in enumerate(sorted(result.keys())):
        variables = result[class_]
        if i > 0:
            print >>f, '\\addlinespace'
        for j, (score, variable) in enumerate(variables):
            label = class_ if j == 0 else ''
            print >>f, '%s & %d & %f & %s \\\\' % (
                label, j + 1, score, re.sub('_', r'\_', variable))

if __name__ == '__main__':
    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE PROFILES-FILENAME")
    parser.add_option('-a', dest='all_pairs', help='all pairs', action='store_true')
    parser.add_option('-o', dest='output_filename', help='file to store the output in')
    parser.add_option('--latex', dest='latex', help='output in LaTeX format', action='store_true')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Incorrect number of arguments')
    properties_file, profiles_filename = args
    cpa.properties.LoadFile(properties_file)

    profiles = Profiles.load(profiles_filename)

    if options.all_pairs:
        result = rank_variables_all_pairs(profiles)
    else:
        result = rank_variables(profiles)

    def write_result(f):
        if options.latex:
            write_result_latex(f, result)
        else:
            write_result_text(f, result)

    if options.output_filename:
        with replace_atomically(options.output_filename) as f:
            write_result(f)
    else:
        write_result(sys.stdout)

