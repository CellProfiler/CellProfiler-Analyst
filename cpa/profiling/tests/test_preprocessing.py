from unittest import TestCase
from cpa.profiling import preprocessing

class NullPreprocessorTestCase(TestCase):
    def test_init(self):
        variables = ['foo', 'bar', 'baz']
        p = preprocessing.NullPreprocessor(variables)
        assert isinstance(p, preprocessing.Preprocessor)
        assert p.variables == variables

    def test_call(self):
        data = object()
        p = preprocessing.NullPreprocessor([])
        assert p(data) == data
