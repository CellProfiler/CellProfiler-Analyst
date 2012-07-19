import cpa.util


class Preprocessor(object):
    pass


class NullPreprocessor(Preprocessor):
    def __init__(self, variables):
        self.variables = variables

    def __call__(self, data):
        return data


class VariableSelector(Preprocessor):
    def __init__(self, mask, variables):
        assert len(mask) == len(variables)
        self.mask = mask
        self.variables = [v for v, m in zip(variables, mask) if m]

    def __call__(self, data):
        return data[:, self.mask]
