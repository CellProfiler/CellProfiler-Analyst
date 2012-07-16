import numpy as np
from mock import Mock, patch, call
from cpa.profiling import subsample

def test_compute_group_subsample():
    cache = Mock()
    cache_module = Mock()
    cache_module.normalizations = {None: lambda x: x}
    cache_module.Cache.return_value = cache
    data = np.array([[1.1, 2.2, 3.3], [4.4, 5.5, 6.6], [7.7, 8.8, 9.0]])
    colnames = ['f1', 'f2', 'f3']
    cache.load.return_value = data, colnames, None
    indices = np.array([0, 2], dtype='i4')
    with patch.dict('sys.modules', {'cpa.profiling.cache': cache_module}):
        r = subsample._compute_group_subsample(('my_cache_dir', 
                                                None,
                                                (0, 42), indices))
    assert np.array_equal(r, np.array([[1.1, 2.2, 3.3], [7.7, 8.8, 9.0]]))

def test_break_indices():
    indices = np.array([0, 99, 40, 64, 65, 39], dtype='i4')
    image_keys = [(0L, 42L), (1L, 23L), (2L, 92L)]
    counts = {image_keys[0]: 40, image_keys[1]: 25, image_keys[2]: 35}
    per_image_indices = list(subsample._break_indices(indices, image_keys, 
                                                      counts))
    assert len(per_image_indices) == 3
    assert np.array_equal(per_image_indices[0], np.array([0, 39], dtype='i4'))
    assert np.array_equal(per_image_indices[1], np.array([0, 24], dtype='i4'))
    assert np.array_equal(per_image_indices[2], np.array([0, 34], dtype='i4'))

def test_combine_subsample():
    generator = [np.array([[1, 2, 3], [4, 5, 6]]),
                 np.array([]),
                 np.array([[7, 8, 9]])]
    r = subsample._combine_subsample(generator)
    assert np.array_equal(r, np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))

# TODO: SubsampleTestCase
# TODO: test_init
# TODO: test_compute

# TODO: test_parse_arguments

# TODO: test_main
