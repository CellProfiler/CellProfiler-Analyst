import numpy as np
from numpy.testing import assert_almost_equal
from unittest import TestCase
from mock import patch, Mock, sentinel
from cpa.profiling import factor_analysis

cars = np.array([[2930, 4099], [3350, 4749], [2640, 3799],
                 [3250, 4816], [4080, 7827]])

def test_standardize():
    # Data from http://www.ats.ucla.edu/stat/sas/faq/standard.htm
    s = factor_analysis.standardize(cars)
    assert_almost_equal(s[:,0].mean(), 0)
    assert_almost_equal(s[:,1].mean(), 0)
    assert_almost_equal(s[:,0].std(), 1)
    assert_almost_equal(s[:,1].std(), 1)

class FactorAnalysisPreprocessorTestCase(TestCase):

    @patch.object(factor_analysis.FactorAnalysisPreprocessor, '_train')
    def test_init(self, train):
        d = np.random.normal(size=(500, 50))
        variables = ['f%d' % (i + 1) for i in xrange(50)]
        p = factor_analysis.FactorAnalysisPreprocessor(d, variables, 5)
        p._train.assert_called_once_with(d)

    def test_init_too_many_factors(self):
        d = np.random.normal(size=(500, 5))
        variables = ['f%d' % (i + 1) for i in xrange(5)]
        self.assertRaises(ValueError,
                          lambda: factor_analysis.FactorAnalysisPreprocessor(d, variables, 6))
    
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

    @patch.object(factor_analysis.FactorAnalysisPreprocessor, '__init__')
    def test_nvariables(self, init):
        init.return_value = None
        p = factor_analysis.FactorAnalysisPreprocessor()
        p.fa_node = Mock()
        p.fa_node.E_y_mtx = np.zeros((3, 2))
        assert p.nvariables == 3

    @patch.object(factor_analysis.FactorAnalysisPreprocessor, 'nvariables')
    @patch.object(factor_analysis.FactorAnalysisPreprocessor, '__init__')
    def test_get_variable_selector(self, init, nvariables):
        init.return_value = None
        nvariables.__get__ = Mock(return_value=4)
        p = factor_analysis.FactorAnalysisPreprocessor()
        # 4 variables, 3 factors
        p.fa_node = Mock()
        p.fa_node.E_y_mtx = np.array([[2, 1, 0],
                                      [1, 0, 0],
                                      [0, 0, 1],
                                      [0, 0, 2]])
        p.input_variables = ['f1', 'f2', 'f3', 'f4']
        sel = p.get_variable_selector()
        data = np.array([0, 1, 2, 3], dtype='i4')
        assert np.array_equal(sel(data), np.array([0, 3]))

@patch('cpa.util.pickle')
@patch('cpa.util.unpickle1')
@patch('cpa.profiling.factor_analysis.FactorAnalysisPreprocessor')
def test_main(pclass, unpickle, pickle):
    p = Mock()
    pclass.return_value = p
    subsample = Mock()
    subsample.data = cars
    unpickle.return_value = subsample
    factor_analysis._main(['foo.subsample', '5', 'foo.famodel'])
    pclass.assert_called_once()

