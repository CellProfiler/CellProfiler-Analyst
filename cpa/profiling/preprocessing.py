import cpa.util

class Preprocessor(object):
    pass

class NullPreprocessor(Preprocessor):
    def __init__(self, variables):
        self.variables = variables

    def __call__(self, data):
        return data
