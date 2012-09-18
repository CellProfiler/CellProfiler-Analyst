import sys
from optparse import OptionParser
import numpy as np
import cpa
from cpa.util import replace_atomically
from .profiles import Profiles

def get_loadings(preprocessor):
    fa_node = preprocessor.fa_node
    orderings = np.argsort(np.abs(fa_node.A), 0)[::-1]
    results = []
    for j in range(orderings.shape[1]):
        loadings = []
        for feature_index in orderings[:15, j]:
            loadings.append((np.abs(fa_node.A)[feature_index, j],
                             preprocessor.input_variables[feature_index]))
        results.append((preprocessor.variables[j], loadings))
    return results

def write_loadings_text(f, loadings):
    for i, (factor, l) in enumerate(loadings):
        if i > 0:
            print >>f
        print >>f, factor
        for weight, variable in l:
            print >>f, '%f %s' % (weight, variable)

def write_loadings_latex(f, loadings):
    for i, (factor, l) in enumerate(loadings):
        if i > 0:
            print >>f, '\\addlinespace'
        for j, (weight, variable) in enumerate(l):
            label = factor if j == 0 else ''
            print >>f, '%s & %f & %s \\\\' % (label, weight, variable)

if __name__ == '__main__':
    parser = OptionParser("usage: %prog FACTOR-MODEL")
    parser.add_option('-o', dest='output_filename', help='file to store the output in')
    parser.add_option('--latex', dest='latex', help='output in LaTeX format', action='store_true')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Incorrect number of arguments')
    factor_model_file, = args
    factor_model = cpa.util.unpickle1(factor_model_file)

    loadings = get_loadings(factor_model)

    def write_loadings(f):
        if options.latex:
            write_loadings_latex(f, loadings)
        else:
            write_loadings_text(f, loadings)
    
    if options.output_filename:
        with replace_atomically(options.output_filename) as f:
            write_loadings(f)
    else:
        write_loadings(sys.stdout)

