#!/usr/bin/env python

import io
import sys
import os
import csv
from optparse import OptionParser
import progressbar
import numpy as np
import time
import itertools
from datetime import timedelta
from threading import Thread
from random import shuffle
import mdp.nodes as nodes

import cpa
from cpa.util.cache import Cache, RobustLinearNormalization

from IPython.parallel import Client

            
def _compute_group_subsample((cache_dir, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames = cache.load(images, normalization=RobustLinearNormalization)
        np.random.shuffle(normalizeddata)
        normalizeddata_sample = [x for i, x in enumerate(normalizeddata) if i % 100 == 0]
        return normalizeddata_sample
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,)
        return None
      
def _compute_svmnormalvector((cache_dir, images, control_images)):
    try:
        import numpy as np 
        import sys
        from cpa.util import cache
        from sklearn.svm import LinearSVC

        cache = Cache(cache_dir)
        normalizeddata, normalized_colnames = cache.load(images, normalization=RobustLinearNormalization)
        control_data, control_colnames = cache.load(control_images, normalization=RobustLinearNormalization)
        assert len(control_data) >= len(normalizeddata)
        downsampled = control_data[np.random.randint(0, len(control_data), len(normalizeddata)), :]
        x = np.vstack((normalizeddata, downsampled))
        y = [1] * len(normalizeddata) + [0] * len(downsampled)
        clf = LinearSVC()
        m = clf.fit(x, y)
        return m.coef_[0]
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,)
        return None
        

class ProfileSVMNormalVector(object):
    
    def __init__(self, properties_file, cache_dir, group, control_filter,
                 filter=None, profile=None):
        startTime = time.time()

        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cache = Cache(cache_dir)
        self.control_filter = control_filter
        self.profile = profile
            
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = RobustLinearNormalization(self.cache).colnames
        
        self.results = self._compute_svmnormalvector_profile()
        
        now = time.time()
        print "Elapsed time: %s" % time.strftime("%H:%M:%S", time.gmtime(now-startTime))
    
    def _compute_svmnormalvector_profile(self):
        f = cpa.properties._filters[self.control_filter]
        control_images_by_plate = {}
        #for row in cpa.db.execute("SELECT %s, %s FROM %s WHERE %s" % (
        #        cpa.dbconnect.UniqueImageClause(), cpa.properties.plate_id,
        #        ','.join(f.get_tables()), str(f))):
        for row in cpa.db.execute("SELECT %s, %s FROM %s WHERE substr(Image_Metadata_Well_DAPI from 2 for 2) IN ('02', '11')" %(
                cpa.dbconnect.UniqueImageClause(), cpa.properties.plate_id,
                cpa.properties.image_table)):
            plate_name = row[-1]
            imkey = row[:-1]
            control_images_by_plate.setdefault(plate_name, []).append(imkey)

        plate_by_image = dict((row[:-2], row[-2])
                              for row in cpa.db.GetPlatesAndWellsPerImage())

        def control_images(treated_images):
            r = []
            for image in treated_images:
                r +=control_images_by_plate[plate_by_image[image]]
            return r

        parameters = [(self.cache_dir, self.mapping_group_images[gp],
                       control_images(self.mapping_group_images[gp]))
                      for gp in self.mapping_group_images.keys()]
        njobs = len(parameters)
        print njobs, ' jobs'
        if self.profile:
            from IPython.parallel import Client, LoadBalancedView
            client = Client(profile='lsf')
            lview = client.load_balanced_view()
        else:
            from multiprocessing import Pool
            lview = Pool()
        progress = progressbar.ProgressBar(widgets=[progressbar.Percentage(), ' ',
                                                    progressbar.Bar(), ' ', 
                                                    progressbar.Counter(), '/', 
                                                    str(njobs), ' ',
                                                    progressbar.ETA()],
                                           maxval=njobs)
        results = list(progress(lview.imap(_compute_svmnormalvector, parameters)))

        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[i][1]
                results[i] = _compute_svmnormalvector(p)

        return results
        
    def save_as_text(self, text_file):
        #grps = '\t'.join('' for g in self.colnames_group)
        #cols = '\t'.join("%s"%c for c in self.colnames)
        text_file.write('%s\t%s\n' % (grps, cols))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%s"%v for v in datamean)
            text_file.write('%s\t%s\n' % (groupItem, values))
    
    def save_as_csv_file(self, output_file):
        csv_file = csv.writer(output_file)
        csv_file.writerow(list(self.colnames_group) + map(lambda x: 'F%03d'%x, range(self.factors)))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            csv_file.writerow(list(gp) + list(datamean))
    
    
    
if __name__ == '__main__':
 
    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] [--factors NFACTORS] PROPERTIES-FILE CACHE-DIR GROUP CONTROL-FILTER")
    parser.add_option('--profile', dest='profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    options, args = parser.parse_args()

    if len(args) != 4:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group, control_filter = args

    profiles = ProfileSVMNormalVector(properties_file, cache_dir, group, 
                                      control_filter, filter=options.filter, 
                                      profile=options.profile)
    if options.output_filename:
        with open(options.output_filename, "w") as f:
            profiles.save_as_text(f)
    else:
        profiles.save_as_text(sys.stdout)
