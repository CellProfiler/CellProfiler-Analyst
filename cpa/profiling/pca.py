#!/usr/bin/env python

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


class PCAPreprocessor(Preprocessor):
    def __init__(self, training_data, input_variables, npcs):
        assert training_data.shape[1] == len(input_variables)
        self.input_variables = input_variables
        self.npcs = npcs
        self.variables = ['PC %d' % (i + 1) for i in range(self.npcs)]
        self._train(training_data)

    def _train(self, training_data):
        nvariables = training_data.shape[1]
        if self.npcs > nvariables:
            raise ValueError('Cannot find more principal components than the '
                             'number of variables ({0})'.format(nvariables))

        self.pca_node = nodes.PCANode(input_dim=None, output_dim=self.npcs, 
                                     dtype=None)
        self.pca_node.train(training_data)
        self.pca_node.stop_training()

    def __call__(self, data):
        return self.pca_node.execute(data)


def _main(args=None):
    # Import the module under its full name so the class can be found
    # when unpickling.
    import cpa.profiling.pca

    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] SUBSAMPLE-FILE NPCS OUTPUT-FILE")
    options, args = parser.parse_args(args)
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    subsample_file = args[0]
    npcs = int(args[1])
    output_file = args[2]

    subsample = cpa.util.unpickle1(subsample_file)
    preprocessor = cpa.profiling.pca.PCAPreprocessor(
        standardize(subsample.data), subsample.variables, npcs)
    cpa.util.pickle(output_file, preprocessor)

if __name__ == '__main__':
    _main()
