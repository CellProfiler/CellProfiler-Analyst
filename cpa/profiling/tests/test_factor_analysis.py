import numpy as np
from numpy.testing import assert_almost_equal
from unittest import TestCase
from mock import patch, Mock
from cpa.profiling import factor_analysis

def test_standardize():
    # Data from http://www.ats.ucla.edu/stat/sas/faq/standard.htm
    cars = np.array([[2930, 4099], [3350, 4749], [2640, 3799],
                     [3250, 4816], [4080, 7827]])
    s = factor_analysis.standardize(cars)
    assert_almost_equal(s[:,0].mean(), 0)
    assert_almost_equal(s[:,1].mean(), 0)
    assert_almost_equal(s[:,0].std(), 1)
    assert_almost_equal(s[:,1].std(), 1)

class FactorAnalysisPreprocessorTestCase(TestCase):

    @patch.object(factor_analysis.FactorAnalysisPreprocessor, '_train')
    def test_init(self, train):
        d = np.random.normal(size=(500, 50))
        p = factor_analysis.FactorAnalysisPreprocessor(d, 5)
        p._train.assert_called_once_with(d)

    def test_init_too_many_factors(self):
        d = np.random.normal(size=(500, 5))
        self.assertRaises(ValueError,
                          lambda: factor_analysis.FactorAnalysisPreprocessor(d, 6))
    
    @patch.object(factor_analysis.FactorAnalysisPreprocessor, '__init__')
    def test_train(self, init):
        init.return_value = None
        p = factor_analysis.FactorAnalysisPreprocessor()
        p.nfactors = 5
        d = np.random.normal(size=(500, 50))
        p._train(d)
        assert p.fa_node

    @patch.object(factor_analysis.FactorAnalysisPreprocessor, '__init__')
    def test_call(self, init):
        init.return_value = None
        p = factor_analysis.FactorAnalysisPreprocessor()
        p.fa_node = Mock()
        rv = object()
        p.fa_node.execute.return_value = rv
        d = object()
        r = p(d)
        assert r == rv
        p.fa_node.execute.assert_called_once_with(d)


