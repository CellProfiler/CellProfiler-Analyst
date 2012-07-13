import numpy as np
from numpy.testing import assert_almost_equal
from unittest import TestCase
from mock import patch, Mock, sentinel
from cpa.profiling import pca

cars = np.array([[2930, 4099], [3350, 4749], [2640, 3799],
                 [3250, 4816], [4080, 7827]])

class PCAPreprocessorTestCase(TestCase):

    @patch.object(pca.PCAPreprocessor, '_train')
    def test_init(self, train):
        d = np.random.normal(size=(500, 50))
        variables = ['f%d' % (i + 1) for i in xrange(50)]
        p = pca.PCAPreprocessor(d, variables, 5)
        p._train.assert_called_once_with(d)

    def test_init_too_many_pcs(self):
        d = np.random.normal(size=(500, 5))
        variables = ['f%d' % (i + 1) for i in xrange(5)]
        self.assertRaises(ValueError,
                          lambda: pca.PCAPreprocessor(d, variables, 6))
    
    @patch.object(pca.PCAPreprocessor, '__init__')
    def test_train(self, init):
        init.return_value = None
        p = pca.PCAPreprocessor()
        p.npcs = 5
        d = np.random.normal(size=(500, 50))
        p._train(d)
        assert p.pca_node

    @patch.object(pca.PCAPreprocessor, '__init__')
    def test_call(self, init):
        init.return_value = None
        p = pca.PCAPreprocessor()
        p.pca_node = Mock()
        rv = object()
        p.pca_node.execute.return_value = rv
        d = object()
        r = p(d)
        assert r == rv
        p.pca_node.execute.assert_called_once_with(d)

@patch('cpa.util.pickle')
@patch('cpa.util.unpickle1')
@patch('cpa.profiling.pca.PCAPreprocessor')
def test_main(pclass, unpickle, pickle):
    p = Mock()
    pclass.return_value = p
    subsample = Mock()
    subsample.data = cars
    unpickle.return_value = subsample
    pca._main(['foo.subsample', '5', 'foo.famodel'])
    pclass.assert_called_once()

