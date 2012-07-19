import tempfile
import numpy as np
import unittest
from mock import Mock, patch, call, sentinel
import cpa.util
from cpa.profiling import cache

def test_make_progress_bar_no_text():
    p = cache.make_progress_bar()

def test_make_progress_bar_with_text():
    p = cache.make_progress_bar('Foo')

def test_invert_dict():
    d = {'a': 1, 'b': 2, 'c': 1}
    inv = cache.invert_dict(d)
    assert inv[1] == ['a', 'c']
    assert inv[2] == ['b']
    assert len(inv.keys()) == 2


class DummyNormalizationTestCase(unittest.TestCase):
    def test_init(self):
        c = object()
        n = cache.DummyNormalization(c)
        assert n.cache == c

    def test_normalize(self):
        n = cache.DummyNormalization(None)
        assert n.normalize(1, 2) == 2

    def test_colnames(self):
        c = Mock()
        c.colnames = object()
        n = cache.DummyNormalization(c)
        assert n.colnames == c.colnames


class RobustLinearNormalizationTestCase(unittest.TestCase):
    def setUp(self):
        self.c = Mock()
        self.c.cache_dir = 'foo'
        self.n = cache.RobustLinearNormalization(self.c)

    def test_init(self):
        assert self.n.cache == self.c
        assert self.n.dir == 'foo/robust_linear'
        self.assertEqual(self.n._colmask_filename, 
                         'foo/robust_linear/colmask.npy')

    def test_percentiles_filename(self):
        self.assertEqual(self.n._percentiles_filename('myplate'),
                         'foo/robust_linear/percentiles/myplate.npy')

    def assertArrayEqual(self, a, b):
        self.assertTrue(np.array_equal(a, b))

    def test_colmask(self):
        file = tempfile.NamedTemporaryFile(suffix='.npy')
        a = np.empty((20,), dtype=bool)
        np.save(file.name, a)
        self.n._colmask_filename = file.name
        self.assertEqual(self.n._cached_colmask, None)
        self.assertArrayEqual(self.n._colmask, a)
        self.assertArrayEqual(self.n._cached_colmask, a)
        self.assertArrayEqual(self.n._colmask, a)
        file.close()

    @staticmethod
    def data_and_percentiles():
        v = np.linspace(1, 9, 101)
        data = np.vstack([v, v * 2, v * 10]).T
        percentiles = np.vstack([data[1,:], data[-2,:]])
        return data, percentiles

    def test_normalize(self):
        data, percentiles = self.data_and_percentiles()
        colmask = np.array([True, False, True])
        self.n._cached_colmask = colmask
        percentiles_file = tempfile.NamedTemporaryFile(suffix='.npy')
        np.save(percentiles_file.name, percentiles)
        self.n._percentiles_filename = lambda plate: percentiles_file.name

        plate = object()
        normalized = self.n.normalize(plate, data)

        self.assertEqual(normalized[1,0], 0)
        self.assertEqual(normalized[1,1], 0)
        self.assertEqual(normalized[-2,0], 1)
        self.assertEqual(normalized[-2,1], 1)
        self.assertEqual(normalized[50, 0], 0.5)
        self.assertEqual(normalized[50, 1], 0.5)
        percentiles_file.close()

    def test_colnames(self):
        self.c.colnames = ['foo', 'bar', 'baz']
        self.n._cached_colmask = np.array([True, False, True])
        self.assertEqual(self.n.colnames, ['foo', 'baz'])

    def test_create_cache(self):
        self.n._create_cache_percentiles = Mock()
        self.n._create_cache_colmask = Mock()
        predicate = object()
        resume = object()
        self.n._create_cache(predicate, resume)
        self.n._create_cache_percentiles.assert_called_once_with(predicate, resume)
        self.n._create_cache_colmask.assert_called_once_with(predicate)

    def test_get_controls(self):
        with patch('cpa.properties') as properties:
            properties.plate_id = 'PlateName'
            properties.image_table = 'ImageTable'
            with patch('cpa.dbconnect') as dbconnect:
                dbconnect.image_key_columns.return_value = ['TableNumber', 'ImageNumber']
                with patch('cpa.db') as db:
                    db.execute.return_value = [['p1', 1, 42],
                                               ['p2', 0, 11],
                                               ['p1', 3, 14]]
                    predicate = 'predicate'
                    controls = self.n._get_controls(predicate)
                    db.execute.assert_called_once_with("select distinct PlateName, TableNumber, ImageNumber from ImageTable where predicate")
                    self.assertEqual(controls['p1'], [(1, 42), (3, 14)])
                    self.assertEqual(controls['p2'], [(0, 11)])
                    self.assertEqual(len(controls.keys()), 2)

    def test_create_cache_colmask(self):
        percentiles_file1 = tempfile.NamedTemporaryFile(suffix='.npy')
        percentiles_file2 = tempfile.NamedTemporaryFile(suffix='.npy')
        percentiles_file3 = tempfile.NamedTemporaryFile(suffix='.npy')
        np.save(percentiles_file1.name, np.array((0, 2)))
        np.save(percentiles_file2.name, np.array([[0.1, 1.0], [0.9, 9.0]]))
        np.save(percentiles_file3.name, np.array([[0.1, 0.4], [0.5, 0.4]]))
        self.n._get_controls = lambda predicate: {'p1': [(1, 42), (3, 14)],
                                                  'p2': [(0, 11)],
                                                  'p3': [(23, 42)]}
        self.n._percentiles_filename = lambda plate: {'p1': percentiles_file1.name,
                                                      'p2': percentiles_file2.name,
                                                      'p3': percentiles_file3.name}[plate]
        colmask_file = tempfile.NamedTemporaryFile(suffix='.npy')
        self.n._colmask_filename = colmask_file.name
        self.n._create_cache_colmask('predicate')
        
        colmask = np.load(colmask_file.name)
        self.assertArrayEqual(colmask, [True, False])

        percentiles_file1.close()
        percentiles_file2.close()
        percentiles_file3.close()
        colmask_file.close()

    def test_compute_percentiles(self):
        data, percentiles = self.data_and_percentiles()
        self.assertArrayEqual(self.n._compute_percentiles(data),
                              percentiles)

    def test_create_cache_percentiles_1_nofeatures(self):
        self.c.load.return_value = (np.zeros((0,0)),)
        self.c.colnames = ['Foo', 'Bar', 'Baz']
        with tempfile.NamedTemporaryFile(suffix='.npy') as file:
            with patch('cpa.profiling.cache.logger') as logger:
                logger.warning = Mock()
                self.n._create_cache_percentiles_1('p1', [(1, 12), (0, 11)], 
                                                   file.name)
                logger.warning.assert_called_once_with('No DMSO features for plate p1')
                self.assertArrayEqual(np.load(file.name), np.zeros((0, 3)))

    def test_create_cache_percentiles_1_features(self):
        data, percentiles = self.data_and_percentiles()
        self.c.load.return_value = (data,)
        with tempfile.NamedTemporaryFile(suffix='.npy') as file:
            self.n._create_cache_percentiles_1('p1', [(1, 12), (0, 11)], 
                                               file.name)
            self.assertArrayEqual(np.load(file.name), percentiles)

    @patch('cpa.profiling.cache.make_progress_bar')
    @patch('cpa.profiling.cache._check_directory')
    def test_create_cache_percentiles(self, check_directory, make_progress_bar):
        controls = {'p1': [(1, 42), (3, 14)],
                    'p2': [(0, 11)],
                    'p3': [(23, 42)]}
        progress = Mock(return_value=controls.items())
        make_progress_bar.return_value = progress
        self.n._get_controls = Mock(return_value=controls)
        self.n._percentiles_filename = lambda p: 'foo/%s.npy' % p
        self.n._create_cache_percentiles_1 = Mock()
        self.n._create_cache_percentiles('predicate', False)
        check_directory.assert_called_once_with('foo', False)
        self.assertEqual(self.n._create_cache_percentiles_1.call_args_list,
                         [call(plate, image_keys, 'foo/%s.npy' % plate) 
                          for plate, image_keys in controls.items()])


def test_normalizations():
    assert cache.normalizations['DummyNormalization'] == cache.DummyNormalization
    assert cache.normalizations['RobustLinearNormalization'] == cache.RobustLinearNormalization


class CacheTestCase(unittest.TestCase):
    def test_init(self):
        c = cache.Cache('foo')
        self.assertEqual(c.cache_dir, 'foo')
        self.assertEqual(c._plate_map_filename, 'foo/image_to_plate.pickle')
        self.assertEqual(c._colnames_filename, 'foo/colnames.txt')

    def test_image_filename(self):
        c = cache.Cache('foo')
        self.assertEqual(c._image_filename('plate1', (0, 42)), 
                         'foo/plate1/0-42.npz')
        self.assertEqual(c._image_filename('plate1', (42,)), 
                         'foo/plate1/42.npz')

    def test_image_filename_backward_compatible(self):
        c = cache.Cache('foo')
        self.assertEqual(c._image_filename_backward_compatible('plate1', (0, 42)), 
                         'foo/plate1/0-42.npy')
        self.assertEqual(c._image_filename_backward_compatible('plate1', (42,)), 
                         'foo/plate1/42.npy')

    def test_plate_map(self):
        c = cache.Cache('foo')
        original = dict(foo=42)
        with tempfile.NamedTemporaryFile(suffix='.pickle') as file:
            cpa.util.pickle(file.name, original)
            c._plate_map_filename = file.name
            self.assertEqual(c._cached_plate_map, None)
            first = c._plate_map
            self.assertFalse(first is original)
            self.assertEqual(first, original)
            self.assertTrue(c._cached_plate_map is first)
            self.assertTrue(c._plate_map is first)

    # TODO: test_load

    def test_colnames(self):
        with tempfile.NamedTemporaryFile(suffix='.txt') as file:
            with open(file.name, 'w') as f:
                print >>f, 'foo'
                print >>f, 'bar'
                print >>f, 'baz'
            c = cache.Cache('foo')
            c._colnames_filename = file.name
            self.assertEqual(c._cached_colnames, None)
            self.assertEqual(c.colnames, ['foo', 'bar', 'baz'])
            self.assertEqual(c._cached_colnames, ['foo', 'bar', 'baz'])
            self.assertEqual(c.colnames, ['foo', 'bar', 'baz'])

    # TODO: test_create_cache

    # TODO: test_create_cache_colnames

    @patch.object(cache.Cache, '__init__')
    @patch('cpa.util.pickle')
    @patch('cpa.db.execute')
    @patch('cpa.dbconnect.image_key_columns')
    def test_create_cache_plate_map(self, image_key_columns, execute, pickle, 
                                    init):
        image_key_columns = ('TableNumber', 'ImageNumber')
        execute.return_value = [['p1', 1, 42],
                                ['p2', 0, 11],
                                ['p1', 3, 14]]
        init.return_value = None
        c = cache.Cache('my_cache_dir')
        c._plate_map_filename = sentinel.plate_map_filename
        c._create_cache_plate_map(False)
        pickle.assert_called_once_with(sentinel.plate_map_filename,
                                       {(1, 42): 'p1',
                                        (0, 11): 'p2',
                                        (3, 14): 'p1'})

    @patch('cpa.profiling.cache.make_progress_bar')
    @patch.object(cache.Cache, '_plate_map')
    def test_create_cache_features(self, plate_map, make_progress_bar):
        cache_dir = tempfile.mkdtemp()
        c = cache.Cache(cache_dir)
        plate_map.__get__ = Mock(return_value={(0L, 42L): 'p1', (1L, 23L): 'p2'})
        make_progress_bar.return_value = lambda x: x
        c._create_cache_image = Mock()
        c._create_cache_features(False)
        calls = c._create_cache_image.call_args_list
        assert len(calls) == 2
        assert call('p1', (0L, 42L), False) in calls
        assert call('p2', (1L, 23L), False) in calls

    # TODO: test_create_image

    # TODO: test_check_directory
