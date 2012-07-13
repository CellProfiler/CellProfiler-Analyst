#!/usr/bin/env python

import io
import sys
import os
import csv
import logging
import hashlib
import pickle
from optparse import OptionParser
import numpy as np
import time
import itertools
import cpa
import cpa.util
from .cache import Cache, RobustLinearNormalization, normalizations
from .profiles import Profiles, add_common_options
from .parallel import ParallelProcessor, Uniprocessing

logger = logging.getLogger(__name__)

def _compute_rfe(x, y, target_accuracy=1.0):
    from sklearn.cross_validation import KFold
    from sklearn.feature_selection import RFECV, RFE
    from sklearn.svm import LinearSVC, SVC
    from sklearn.metrics import zero_one

    cv = KFold(len(y), 5)
    clf = SVC(kernel='linear', C=1.) #LinearSVC(C=1.0)
    #clf = LinearSVC(C=1.0)
    rfecv = RFECV(clf, step=0.1, cv=cv, loss_func=zero_one)
    print 'About to call RFECV.fit on', x.shape, 'and', y.shape
    rfecv.fit(x, y)
    print 'RFECV done'
    # The percentage correct for each # of variables in the cross validation
    perccorrect_tot = [100 - ((100 * i) / y.shape[0]) 
                       for i in rfecv.cv_scores_]
    threshold = min(perccorrect_tot) + target_accuracy * (max(perccorrect_tot) - min(perccorrect_tot))
    nfeatures = np.nonzero(perccorrect_tot >= threshold)[0][0] + 1

    rfe = RFE(clf, nfeatures, step=0.1)
    rfe.fit(x, y)
    return rfe.support_

memoization_dir = None

class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.dir = memoization_dir
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
    def __call__(self, *args):
        filename = os.path.join(self.dir, hashlib.sha1(pickle.dumps(args)).hexdigest())
        try:
            value = cpa.util.unpickle(filename)[0]
            #logger.debug('Using cached value')
            return value
        except IOError:
            value = self.func(*args)
            cpa.util.pickle(filename, value)
            return value
    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)

def _compute_svmnormalvector((cache_dir, images, control_images, rfe)):
    #try:
        import numpy as np 
        import sys
        from cpa.profiling.cache import Cache, RobustLinearNormalization
        from sklearn.svm import LinearSVC
        from cpa.profiling.profile_svmnormalvector import _compute_rfe

        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames, _ = cache.load(images, normalization=RobustLinearNormalization)
        control_data, control_colnames, _ = cache.load(control_images, normalization=RobustLinearNormalization)
        assert len(control_data) >= len(normalizeddata)
        downsampled = control_data[np.random.randint(0, len(control_data), len(normalizeddata)), :]
        x = np.vstack((normalizeddata, downsampled))
        y = np.array([1] * len(normalizeddata) + [0] * len(downsampled))
        clf = LinearSVC(C=1.0)
        m = clf.fit(x, y)
        normal_vector = m.coef_[0]
        if rfe:
            normal_vector[~_compute_rfe(x, y)] = 0
        return normal_vector
    #except: # catch *all* exceptions
    #    from traceback import print_exc
    #    print_exc(None, sys.stderr)
    #    return None
        
def images_by_plate(filter):
    f = cpa.properties._filters[filter]
    d = {}
    for row in cpa.db.execute("""
        SELECT %s, %s FROM %s 
        WHERE substr(Image_Metadata_Well_DAPI from 2 for 2) IN ('02', '11')""" % (
            cpa.dbconnect.UniqueImageClause(), cpa.properties.plate_id,
            cpa.properties.image_table)):
        plate_name = row[-1]
        imkey = row[:-1]
        d.setdefault(plate_name, []).append(imkey)
    return d

def profile_svmnormalvector(cache_dir, group_name, control_filter, 
                            filter=None, rfe=False, job=None,
                            parallel=Uniprocessing(),
                            normalization=RobustLinearNormalization, 
                            preprocess_file=None):
        group, colnames_group = cpa.db.group_map(group_name, reverse=True, 
                                                 filter=filter)
        control_images_by_plate = images_by_plate(control_filter)
        plate_by_image = dict((row[:-2], row[-2])
                              for row in cpa.db.GetPlatesAndWellsPerImage())

        def control_images(treated_images):
            return [r for image in treated_images
                    for r in control_images_by_plate[plate_by_image[image]]]

        keys = group.keys()
        parameters = [(cache_dir, group[k], control_images(group[k]), rfe)
                      for k in keys]

        if preprocess_file:
            preprocessor = cpa.util.unpickle1(preprocess_file)
            variables = preprocessor.variables
        else:
            cache = Cache(cache_dir)
            variables = normalization(cache).colnames

        if job:
            i = job - 1
            memoize(_compute_svmnormalvector)
        else:
            if memoization_dir is None:
                fn = _compute_svmnormalvector
            else:
                fn = memoizer(_compute_svmnormalvector)
            return Profiles.compute(keys, variables, fn, parameters, 
                                    parallel=parallel, group_name=group_name)
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [--memoize DIRECTORY] [-J NUMBER] [-o OUTPUT-FILENAME] [-f FILTER] PROPERTIES-FILE CACHE-DIR GROUP CONTROL-FILTER")
    ParallelProcessor.add_options(parser)
    parser.add_option('--memoize', dest='memoize', default=None, help='Checkpoint individual profiles in temporary files')
    parser.add_option('-J', dest='job', help='Compute only one profile, 1 <= j <= n', default=None, type=int)
    parser.add_option('--rfe', dest='rfe', help='Recursive feature elimination', action='store_true')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    add_common_options(parser)
    options, args = parser.parse_args()
    parallel = ParallelProcessor.create_from_options(parser, options)

    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group, control_filter = args

    if options.job and not options.memoize:
        parser.error("-J can only be used with --memoize")
    memoization_dir = options.memoize

    cpa.properties.LoadFile(properties_file)
    profiles = profile_svmnormalvector(cache_dir, group, control_filter, 
                                       filter=options.filter, rfe=options.rfe, 
                                       parallel=parallel, job=options.job,
                                       normalization=normalizations[options.normalization],
                                       preprocess_file=options.preprocess_file)
    profiles.save(options.output_filename)
