#!/usr/bin/env python

import logging
from optparse import OptionParser
import progressbar
import numpy as np
import cpa.util
from .cache import Cache
from .preprocessing import Preprocessor, VariableSelector
import os
from sklearn.decomposition import PCA, MiniBatchSparsePCA
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import Imputer
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)
            
class DecompositionPreprocessor(Preprocessor):
    def __init__(self, training_data, input_variables, decomp_method='pca', n_components=2):
        assert training_data.shape[1] == len(input_variables)
        self.input_variables = input_variables
        self.n_components = n_components
        self.variables = ['V%d' % (i + 1) for i in range(self.n_components)]

        impute = Imputer()
        nzv = VarianceThreshold()
        scale = StandardScaler()

        model_l = [('impute', impute), ('nzv', nzv), ('scale', scale)]

        if decomp_method == 'pca':
            pca = PCA()
            model_l.append(('pca', pca))
            self.model = Pipeline(model_l)
            self.model.set_params(pca__whiten = False, pca__n_components = n_components)
        elif decomp_method == 'mbspca':
            mbspca = MiniBatchSparsePCA()
            model_l.append(('mbspca', mbspca))
            self.model = Pipeline(model_l)
            self.model.set_params(mbspca__n_components = n_components, mbspca__verbose = True)

        self._train(training_data)

    def _train(self, training_data):
        self.model.fit(training_data)

    def __call__(self, data):
        return self.model.transform(data)

def _main(args=None):
    # Import the module under its full name so the class can be found
    # when unpickling.
    import cpa.profiling.decomp

    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [options] SUBSAMPLE-FILE N_COMPONENTS OUTPUT-FILE")
    parser.add_option('--method', dest='method', type = 'choice', choices = ['pca', 'mbspca'], action='store', default='pca')
    options, args = parser.parse_args(args)
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    subsample_file = args[0]
    n_components = int(args[1])
    output_file = args[2]

    subsample = cpa.util.unpickle1(subsample_file)
    preprocessor = cpa.profiling.decomp.DecompositionPreprocessor(training_data = subsample.data, 
                                                                  input_variables = subsample.variables, 
                                                                  decomp_method = options.method,
                                                                  n_components = n_components)
    cpa.util.pickle(output_file, preprocessor)

if __name__ == '__main__':
    _main()
