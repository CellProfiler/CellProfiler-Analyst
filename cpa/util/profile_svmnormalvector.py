#!/usr/bin/env python

import io
import sys
import os
import csv
import logging
from optparse import OptionParser
import numpy as np
import time
import itertools
from IPython.parallel import Client
import cpa
from cpa.util.cache import Cache, RobustLinearNormalization
from profiles import Profiles

logger = logging.getLogger(__name__)

def _compute_svmnormalvector((cache_dir, images, control_images)):
    #try:
        import numpy as np 
        import sys
        from cpa.util.cache import Cache, RobustLinearNormalization
        from sklearn.svm import LinearSVC

        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames = cache.load(images, normalization=RobustLinearNormalization)
        control_data, control_colnames = cache.load(control_images, normalization=RobustLinearNormalization)
        assert len(control_data) >= len(normalizeddata)
        downsampled = control_data[np.random.randint(0, len(control_data), len(normalizeddata)), :]
        x = np.vstack((normalizeddata, downsampled))
        y = [1] * len(normalizeddata) + [0] * len(downsampled)
        clf = LinearSVC(C=1.0)
        m = clf.fit(x, y)
        return m.coef_[0]
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
                             filter=None, ipython_profile=None):
        cache = Cache(cache_dir)
        group, colnames_group = cpa.db.group_map(group_name, reverse=True, 
                                                 filter=filter)
        variables = RobustLinearNormalization(cache).colnames
        control_images_by_plate = images_by_plate(control_filter)
        plate_by_image = dict((row[:-2], row[-2])
                              for row in cpa.db.GetPlatesAndWellsPerImage())

        def control_images(treated_images):
            return [r for image in treated_images
                    for r in control_images_by_plate[plate_by_image[image]]]

        keys = group.keys()
        parameters = [(cache_dir, group[k], control_images(group[k]))
                      for k in keys]

        return Profiles.compute(keys, variables, _compute_svmnormalvector, 
                                parameters, ipython_profile)
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
 
    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] [--factors NFACTORS] PROPERTIES-FILE CACHE-DIR GROUP CONTROL-FILTER")
    parser.add_option('--ipython-profile', dest='ipython_profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    options, args = parser.parse_args()

    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group, control_filter = args

    cpa.properties.LoadFile(properties_file)
    profiles = profile_svmnormalvector(cache_dir, group, control_filter, 
                                       filter=options.filter, 
                                       ipython_profile=options.ipython_profile)
    profiles.save(options.output_filename)
