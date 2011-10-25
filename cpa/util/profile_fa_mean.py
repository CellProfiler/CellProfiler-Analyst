#!/usr/bin/env python

"""
$ profile_fa_mean.py properties_file cache_dir output_file group [filter]

Writes a tab-delimited file containing the profiles. Example:

	f1	f2
Well1   0.123	4.567
Well2	8.901	2.345

		f1	f2
Comp1   Conc1   0.123	4.567
Comp1	Conc2   8.901	2.345

"""

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
from cpa.util import cache

from IPython.parallel import Client

            
def _compute_group_subsample((cache_dir, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=cache.RobustLinearNormalization)
        np.random.shuffle(normalizeddata)
        normalizeddata_sample = [x for i, x in enumerate(normalizeddata) if i % 100 == 0]
        return normalizeddata_sample
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,)
        return None
      
def _compute_group_projection_and_mean((cache_dir, images, fa_node, mean, stdev)):
    try:
        import numpy as np        
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=cache.RobustLinearNormalization)
        normalizeddata = (normalizeddata - mean) / stdev
        normalizeddata_projected = fa_node.execute(normalizeddata)
        normalizeddata_projected_mean = np.mean(normalizeddata_projected, axis = 0)
        return normalizeddata_projected_mean
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,)
        return None
        

class ProfileFAMean(object):
    
    def __init__(self, properties_file, cache_dir, group, filter=None, 
                 factors=50, profile=None):
        startTime = time.time()

        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cash = cache.Cache(cache_dir)
        self.factors = factors        
        self.profile = profile
            
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = cache.RobustLinearNormalization(self.cash).colnames
        
        self.subsamples = self._compute_subsamples()
        self.results = self._compute_fa_mean_profile()
        
        now = time.time()
        print "Elapsed time: %s" % time.strftime("%H:%M:%S", time.gmtime(now-startTime))
        
  
    def _compute_subsamples(self):

        print "subsampling..."

        parameters = [(self.cache_dir, self.mapping_group_images[gp])
                      for gp in self.mapping_group_images.keys()]
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
                                                    str(len(parameters)), ' ',
                                                    progressbar.ETA()],
                                           maxval=len(parameters))
        results = list(progress(lview.imap(_compute_group_subsample, parameters)))

        subsample = []
        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[i][1]
                results[i] = _compute_group_subsample(p) # just to see throw the exception
                print >>sys.stderr, '#### Exiting'
                sys.exit(os.EX_USAGE)
            subsample.extend(r)

        print "the subsampling set contains %d items" % len(subsample)
        return subsample
    
    def _compute_fa_mean_profile(self):        

        print "computing Factor Analysis"
  
##        import pdb
##        pdb.set_trace()
        mean = np.mean(self.subsamples, axis = 0)   
        subsampled_data = self.subsamples - mean
        stdev = np.std(subsampled_data, axis = 0)
        subsampled_data = subsampled_data/stdev
        
        fa_node = nodes.FANode(input_dim=None, output_dim=self.factors, dtype=None, max_cycles=30)
        fa_node.train(subsampled_data)
        fa_node.stop_training()
                
        self.factors = min(self.factors, subsampled_data.shape[1])

        print "projecting groups (%s) ..." % len(self.mapping_group_images)

        parameters = [(self.cache_dir, self.mapping_group_images[gp], fa_node, mean, stdev)
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
        results = list(progress(lview.imap(_compute_group_projection_and_mean, parameters)))

        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[i][1]
                results[i] = _compute_group_projection_and_mean(p)

        return results
        
    def save_as_text(self, text_file):
        #grps = '\t'.join('' for g in self.colnames_group)
        #cols = '\t'.join("%s"%c for c in self.colnames)
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%s"%v for v in datamean)
            text_file.write('%s\t%s\n' % (groupItem, values))
        text_file.close()
    
    def save_as_csv_file(self, output_file):
        csv_file = csv.writer(output_file)
        csv_file.writerow(list(self.colnames_group) + map(lambda x: 'F%03d'%x, range(self.factors)))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            csv_file.writerow(list(gp) + list(datamean))
    
    
    
if __name__ == '__main__':
 
    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] [--factors NFACTORS] PROPERTIES-FILE CACHE-DIR GROUP")
    parser.add_option('--profile', dest='profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    parser.add_option('--factors', dest='nfactors', type='int', default=5, help='number of factors')
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group = args

    profiles = ProfileFAMean(properties_file, cache_dir, group, filter=options.filter, 
                  factors=options.nfactors, profile=options.profile)
    if options.output_filename:
        with open(options.output_filename, "w") as f:
            profiles.save_as_text(f)
    else:
        profiles.save_as_text(sys.stdout)
