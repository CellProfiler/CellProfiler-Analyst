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
    
    def __init__(self, properties_file, cache_dir, group, filter = None, factors = 50):
        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cash = cache.Cache(cache_dir)
        self.factors = factors        
            
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = cache.RobustLinearNormalization(self.cash).colnames
        
        self.subsamples = self._compute_subsamples()
        self.results = self._compute_fa_mean_profile()
  
    def _compute_subsamples(self):

        print "subsampling..."

        parameters = [(self.cache_dir, self.mapping_group_images[gp])
                      for gp in self.mapping_group_images.keys()]

        client = Client(profile='lsf')
        lview = client.load_balanced_view()
        print len(parameters), ' jobs'
        ar = lview.map_async(_compute_group_subsample, parameters)
        while not ar.ready():
            msgset = set(ar.msg_ids)
            completed = msgset.difference(client.outstanding)
            print '%d of %d complete' % (len(completed), len(msgset))
            ar.wait(1)

        results = ar.get()
        subsample = []
        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[index][1]
                results[i] = _compute_group_subsample(p) # just to see throw the exception
                print >>sys.stderr, '#### Exiting'
                sys.exit(os.EX_USAGE)
            subsample.extend(r)
            
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

        client = Client(profile='lsf')
        lview = client.load_balanced_view()
        print len(parameters), ' jobs'
        ar = lview.map_async(_compute_group_projection_and_mean, parameters)
        while not ar.ready():
            msgset = set(ar.msg_ids)
            completed = msgset.difference(client.outstanding)
            print '%d of %d complete' % (len(completed), len(msgset))
            ar.wait(1)

        results = ar.get()
        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[index][1]
                results[i] = _compute_group_projection_and_mean(p)

        return results

        
    def save_as_text_file(self, output_file):
        grps = '\t'.join("%s"%g for g in self.colnames_group)
        cols = '\t'.join("F%03d"%f for f in range(self.factors))
        text_file = open(output_file + '.txt', "w")
        text_file.write('%s\t%s\n' % (grps, cols))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%s"%v for v in datamean)
            text_file.write('%s\t%s\n' % (groupItem, values))
        text_file.close()
    
    def save_as_csv_file(self, output_file):
        csv_file = csv.writer(open(output_file + '.csv', "w"))
        csv_file.writerow(list(self.colnames_group) + map(lambda x: 'F%03d'%x, range(self.factors)))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            csv_file.writerow(list(gp) + list(datamean))
    
    
    
if __name__ == '__main__':
 
    # python profile_mean.py '/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2.properties' '/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache' '/home/unix/auguste/ImagingAuguste/CDP2/test_cc_map.txt' 'CompoundConcentration' 'compound_treated'

    program_name = os.path.basename(sys.argv[0])
    len_argv = len(sys.argv)
    
    if len_argv != 7:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR OUTPUT_FILE GROUP FILTER FACTORS' % program_name
        sys.exit(os.EX_USAGE)
    
    properties_file, cache_dir, output_file, group, filter, factors = sys.argv[1:6]
    profileFAMean = ProfileFAMean(properties_file, cache_dir, group, filter, factors)
    profileFAMean.save_as_text(output_file) 
     
    

