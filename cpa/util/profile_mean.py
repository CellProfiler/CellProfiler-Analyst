#!/usr/bin/env python

"""
$ profile_mean.py properties_file cache_dir output_file group [filter]

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

import cpa
from cpa.util import cache

from IPython.parallel import Client

def _compute_group_mean((cache_dir, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=cache.RobustLinearNormalization)
        normalizeddata_mean = np.mean(normalizeddata, axis = 0)
        return normalizeddata_mean
    except: # catch *all* exceptions
        from traceback import print_exc
        print_exc(None, sys.stderr)
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: %s" % (e,) 
        

class ProfileMean(object):
    
    def __init__(self, properties_file, cache_dir, group, filter = None):
        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cash = cache.Cache(cache_dir)
        
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = cache.RobustLinearNormalization(self.cash).colnames
        
        self.results = self._compute_mean_profile()
        
    
    def _compute_mean_profile(self):
        
        parameters = [(self.cache_dir, self.mapping_group_images[gp])
                      for gp in self.mapping_group_images.keys()]

        client = Client(profile='lsf')
        lview = client.load_balanced_view()
        print len(parameters), 'jobs'
        ar = lview.map_async(_compute_group_mean, parameters)
        while not ar.ready():
            msgset = set(ar.msg_ids)
            completed = msgset.difference(client.outstanding)
            print '%d of %d complete' % (len(completed), len(msgset))
            ar.wait(1)

        results = ar.get()
        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[index][1]
                results[i] = _compute_group_mean(p)

        self.results = results
        return results
        
    def save_as_text_file(self, output_file):
        grps = '\t'.join('' for g in self.colnames_group)
        cols = '\t'.join("%s"%c for c in self.colnames)
        text_file = open(output_file + '.txt', "w")
        text_file.write('%s\t%s\n' % (grps, cols))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%s"%v for v in datamean)
            text_file.write('%s\t%s\n' % (groupItem, values))
        text_file.close()
    
    def save_as_csv_file(self, output_file):
        csv_file = csv.writer(open(output_file + '.csv', "w"))
        csv_file.writerow(list(self.colnames_group) + list(self.colnames))
        for gp, datamean in zip(self.mapping_group_images.keys(), self.results):
            csv_file.writerow(list(gp) + list(datamean))
    
    
if __name__ == '__main__':
 
    # python profile_mean.py '/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2.properties' '/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache' '/home/unix/auguste/ImagingAuguste/CDP2/test_cc_map.txt' 'CompoundConcentration' 'compound_treated'

    program_name = os.path.basename(sys.argv[0])
    len_argv = len(sys.argv)
    
    if len_argv < 5 or len_argv > 6:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR OUTPUT_FILE GROUP [FILTER]' % program_name
        sys.exit(os.EX_USAGE)
    
    if len_argv == 5:
        properties_file, cache_dir, output_file, group = sys.argv[1:5]
        profileMean = ProfileMean(properties_file, cache_dir, group)
        profileMean.save_as_text_file(output_file) 
        
    if len_argv == 6:
        properties_file, cache_dir, output_file, group, filter = sys.argv[1:6]
        profileMean = ProfileMean(properties_file, cache_dir, group, filter=filter)
        profileMean.save_as_text_file(output_file) 
     
    

