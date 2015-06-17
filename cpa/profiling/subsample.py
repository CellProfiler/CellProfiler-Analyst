#!/usr/bin/env python

def _compute_group_subsample((cache_dir, normalization_name, image_key, 
                              indices)):
    import numpy as np
    from .cache import Cache, normalizations
    cache = Cache(cache_dir)
    normalizeddata, normalized_colnames, _ = cache.load([image_key], 
                                                        normalization=normalizations[normalization_name],
                                                        removeRowsWithNaN=False)
    return normalizeddata[indices], np.hstack((np.array([image_key]*indices.shape[0]), _[indices][:,np.newaxis]))

import cPickle as pickle
import operator
import random
import logging
from optparse import OptionParser
import numpy as np
import cpa
from cpa.util import replace_atomically
from .cache import Cache
from .normalization import RobustLinearNormalization, normalizations
from .parallel import ParallelProcessor, Uniprocessing

def _break_indices(indices, image_keys, count_cells):
    """Break the overall list of random indices into per-image indices."""
    sorted_indices = np.sort(indices)
    a = 0
    start = end = 0
    for image_key in image_keys:
        c = count_cells([image_key])
        while end < len(sorted_indices) and sorted_indices[end] < a + c:
            end += 1
        yield sorted_indices[start:end] - a
        start = end
        a += c

def _make_parameters(cache_dir, normalization_name, image_keys, 
                     per_image_indices):
    parameters = [(cache_dir, normalization_name, image_key, indices)
            for image_key, indices in zip(image_keys, per_image_indices)]
    return [(a,b,c,d) for (a,b,c,d) in parameters if d.shape[0]>1] # remove images with one or no indices

def _combine_subsample(generator):
    return np.vstack([a for a in generator])

def make_count_cells_function(cache):
    """
    Return a function that computes the total number of cells
    across a list of image keys.

    """
    c = cache.get_cell_counts()
    return lambda image_keys: reduce(operator.add, (c.get(tuple(map(int, k)), 0) 
                                                    for k in image_keys))

def organize_image_keys_per_group(image_keys, group):
    group_mapping, colnames = cpa.db.group_map(group)
    per_group = {}
    for image_key in image_keys:
        g = group_mapping[image_key]
        per_group.setdefault(g, []).append(image_key)
    return per_group


class Subsample(object):
    def __init__(self, cache_dir, sample_size, filter=None, group=None,
                 normalization=RobustLinearNormalization,
                 parallel=Uniprocessing(), show_progress=True, verbose=True):
        self.cache_dir = cache_dir
        self.normalization_name = normalization.__name__
        cache = Cache(self.cache_dir)
        self.variables = normalization(cache).colnames
        self.data, self.objkeys = self._compute(sample_size, filter, group, 
                                                parallel, show_progress, 
                                                verbose)

    def _compute(self, sample_size, filter, group, parallel, show_progress, 
                 verbose):
        cache = Cache(self.cache_dir)
        if filter is None:
            image_keys = cpa.db.GetAllImageKeys()
        else:
            image_keys = cpa.db.GetFilteredImages(filter)
        count_cells = make_count_cells_function(cache)
        ncells = count_cells(image_keys)
        if sample_size is None:
            sample_size = int(round(0.001 * ncells))
        if verbose:
            print 'Subsampling {0} of {1} cells'.format(sample_size, ncells)
        if group is None:
            return self._compute1([(sample_size, image_keys)], count_cells,
                                  parallel, show_progress)
        else:
            per_group = organize_image_keys_per_group(image_keys, group)
            ngroups = len(per_group)
            # Subsample an equal number of cell from each group.
            sample_sizes_and_keys = []
            nchosen = 0
            for i, (g, keys) in enumerate(per_group.items()):
                needed = int(round((i + 1.0) * sample_size / ngroups - nchosen))
                ncells_this_group = count_cells(keys)
                needed = min(needed, ncells_this_group)
                nchosen += needed
                sample_sizes_and_keys.append((needed, keys))
            return self._compute1(sample_sizes_and_keys, count_cells,
                                  parallel, show_progress)

    def _compute1(self, sample_sizes_and_keys, count_cells, parallel, show_progress):
        parameters = []
        for sample_size, image_keys in sample_sizes_and_keys:
            ncells = count_cells(image_keys)
            indices = np.array(random.sample(xrange(ncells), sample_size))
            per_image_indices = _break_indices(indices, image_keys, count_cells)
            parameters.extend(_make_parameters(self.cache_dir, self.normalization_name, 
                                               image_keys, per_image_indices))

        njobs = len(parameters)
        generator = parallel.view('subsample').imap(_compute_group_subsample, parameters)
        if show_progress:
            import progressbar
            progress = progressbar.ProgressBar(widgets=['Subsampling:',
                                                        progressbar.Percentage(), ' ',
                                                        progressbar.Bar(), ' ', 
                                                        progressbar.Counter(), '/', 
                                                        str(njobs), ' ',
                                                        progressbar.ETA()],
                                               maxval=njobs)
        else:
            progress = lambda x: x
        results = list(progress(generator))
        data = _combine_subsample([a for (a,b) in results])
        objkey = _combine_subsample([b for (a,b) in results])
        return data, objkey

def _parse_arguments():
    global options, parallel
    global properties_file, cache_dir, output_filename, sample_size
    parser = OptionParser("usage: %prog [options] PROPERTIES-FILE CACHE-DIR OUTPUT-FILENAME [SAMPLE-SIZE]")
    ParallelProcessor.add_options(parser)
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('-g', dest='group', help='sample evenly across groups')
    parser.add_option('-p', dest='progress', action='store_true', help='show progress bar')
    parser.add_option('-v', dest='verbose', action='store_true', help='print additional information')
    parser.add_option('--normalization', help='normalization method (default: RobustLinearNormalization)',
                      default='RobustLinearNormalization')
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)
    if len(args) < 3 or len(args) > 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, output_filename = args[:3]
    if len(args) == 4:
        sample_size = int(args[3])
    else:
        sample_size = None

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _parse_arguments()
    cpa.properties.LoadFile(properties_file)
    normalization = normalizations[options.normalization]
    # Import the module under its full name so the class can be found
    # when unpickling.
    import cpa.profiling.subsample
    subsample = cpa.profiling.subsample.Subsample(
        cache_dir, sample_size, filter=options.filter, group=options.group,
        parallel=parallel, show_progress=options.progress, 
        verbose=options.verbose, normalization=normalization)
    with replace_atomically(output_filename) as f:
        pickle.dump(subsample, f)
