#!/usr/bin/env python

from __future__ import print_function
import logging
from optparse import OptionParser
import progressbar
import numpy as np
import mdp.nodes as nodes
import cpa.util
from .cache import Cache
from .preprocessing import Preprocessor, VariableSelector

logger = logging.getLogger(__name__)
            
def standardize(a):
    mean = np.mean(a, axis=0)   
    centered = a - mean
    stdev = np.std(centered, axis=0)
    return centered / stdev


class FactorAnalysisPreprocessor(Preprocessor):
    def __init__(self, training_data, input_variables, nfactors):
        assert training_data.shape[1] == len(input_variables)
        self.input_variables = input_variables
        self.nfactors = nfactors
        self.variables = ['Factor %d' % (i + 1) for i in range(self.nfactors)]
        self.selected_variables = range(len(self.variables))
        self._train(training_data)

    def _train(self, training_data, tol=1e-05):
        # select independent columns
        # http://stackoverflow.com/a/13313828/1094109
        _, R = np.linalg.qr(training_data)
        self.selected_variables = np.where(np.abs(R.diagonal()) > tol)[0]
            
        nvariables = len(self.selected_variables)
        if self.nfactors > nvariables:
            raise ValueError('Cannot find more factors than the number of '
                             'variables ({0})'.format(nvariables))

        self.fa_node = nodes.FANode(input_dim=None, output_dim=self.nfactors, 
                                    dtype=None, max_cycles=30)
        self.fa_node.train(training_data[:, self.selected_variables])
        self.fa_node.stop_training()

    def __call__(self, data):
        return self.fa_node.execute(data[:, self.selected_variables])

    @property
    def nvariables(self):
        return self.fa_node.E_y_mtx.shape[0]

    def get_variable_selector(self):
        loadings = self.fa_node.E_y_mtx
        variable_indices = set(np.argmax(loadings, axis=0))
        variable_indices_mapped = [self.selected_variables[i] for i in variable_indices]
        mask = np.array([i in variable_indices_mapped
                         for i in xrange(len(self.input_variables))])
        return VariableSelector(mask, self.input_variables)

def kaiser(data):
    c = np.corrcoef(data.T)
    w, v = np.linalg.eig(c)
    return (w >= 1).sum()

def _main(args=None):
    # Import the module under its full name so the class can be found
    # when unpickling.
    import cpa.profiling.factor_analysis

    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] SUBSAMPLE-FILE NFACTORS OUTPUT-FILE")
    parser.add_option('--variable-selection-only', dest='variable_selection_only',
                      help='use factor analysis only to select variables to keep (those most heavily loaded on at least on factor)',
                      action='store_true')
    options, args = parser.parse_args(args)
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    subsample_file = args[0]
    nfactors = int(args[1])
    output_file = args[2]

    subsample = cpa.util.unpickle1(subsample_file)
    print(kaiser(subsample.data))
    preprocessor = cpa.profiling.factor_analysis.FactorAnalysisPreprocessor(
        standardize(subsample.data), subsample.variables, nfactors)
    if options.variable_selection_only:
        preprocessor = preprocessor.get_variable_selector()
    cpa.util.pickle(output_file, preprocessor)

if __name__ == '__main__':
    _main()
