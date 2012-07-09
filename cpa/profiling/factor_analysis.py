#!/usr/bin/env python

import logging
from optparse import OptionParser
import progressbar
import numpy as np
import mdp.nodes as nodes
import cpa.util
from .preprocessing import Preprocessor

logger = logging.getLogger(__name__)
            
def standardize(a):
    mean = np.mean(a, axis=0)   
    centered = a - mean
    stdev = np.std(centered, axis=0)
    return centered / stdev


class FactorAnalysisPreprocessor(Preprocessor):
    def __init__(self, training_data, nfactors):
        nfeatures = training_data.shape[1]
        if nfactors > nfeatures:
            raise ValueError('Cannot find more factors than the number of '
                             'features ({0})'.format(nfeatures))

        self.nfactors = nfactors
        self.variables = ['Factor %d' % (i + 1) for i in range(self.nfactors)]
        self._train(training_data)

    def _train(self, training_data):
        self.fa_node = nodes.FANode(input_dim=None, output_dim=self.nfactors, 
                                    dtype=None, max_cycles=30)
        self.fa_node.train(training_data)
        self.fa_node.stop_training()

    def __call__(self, data):
        return self.fa_node.execute(data)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] SUBSAMPLE-FILE NFACTORS OUTPUT-FILE")
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    subsample_file = args[0]
    nfactors = int(args[1])
    output_file = args[2]

    subsample = standardize(np.load(subsample_file))
    # Import the module under its full name so the class can be found
    # when unpickling.
    import cpa.profiling.factor_analysis
    preprocessor = cpa.profiling.factor_analysis.FactorAnalysisPreprocessor(
        subsample, nfactors)
    cpa.util.pickle(output_file, preprocessor)
