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
import numpy as np
import time
import itertools
from datetime import timedelta
from threading import Thread

import cpa
from cpa.util import cache

from IPython.parallel import Client

class waiter(Thread):
    def init(self, group_mean_dir, group_item_total):
        self.group_mean_dir = group_mean_dir
        self.group_item_total = group_item_total
    
    def run(self):
        self.running = True
        startTime = time.time()
        group_item_current = 1.0
        while(group_item_current < self.group_item_total and self.running):
            filenum = len(os.listdir(self.group_mean_dir))
            if (filenum > 0): 
                group_item_current = float(filenum)
            remaining = self.group_item_total - group_item_current
            ratio = group_item_current/self.group_item_total
            percent = (ratio * 100)
            now = time.time()
            elapsedTime = (now - startTime)
            estTotalTime = elapsedTime / ratio
            estRemainingTime = estTotalTime - elapsedTime;
            timeleft = time.strftime("%H:%M:%S", time.gmtime(estRemainingTime))
            print '(%d) %d%% Est remaining time: %s' % (remaining,percent,timeleft)
            time.sleep(1)
       


def _compute_group_mean((cache_dir, gp_mean_file, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=cache.RobustLinearNormalization)
        normalizeddata_mean = np.mean(normalizeddata, axis = 0)
        np.save(gp_mean_file, normalizeddata_mean)
        return normalizeddata_mean
    except: # catch *all* exceptions
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: (%s) %s" % (gp_mean_file,e) 
    

def _compute_group_means(properties_file, cache_dir, output_file, group, filter = None):
    cpa.properties.LoadFile(properties_file)
    cash = cache.Cache(cache_dir)
    
    client = Client(profile='lsf')
    dview = client.load_balanced_view() #client[:]
    
    group_mean_dir = os.path.join(cache_dir, 'mean_profile_%s' % group)
    if filter:
        group_mean_dir = group_mean_dir + '_' + filter
    
    if not os.path.exists(group_mean_dir):
        os.mkdir(group_mean_dir)
    
    mapping_group_images, colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
    
    colnames = cash.colnames
    
    grps = '\t'.join("%s"%g for g in colnames_group)
    cols = '\t'.join("%s"%c for c in colnames)
    
    parameters = []
    group_item_total = len(mapping_group_images)
    w = waiter()
    w.init(group_mean_dir, group_item_total)
    w.start()
    
    for gp in mapping_group_images.keys():
        gp_name = '_'.join("%s"%i for i in gp)
        gp_mean_file = os.path.join(group_mean_dir, '%s' % gp_name)
        if not os.path.exists('%s.npy' % gp_mean_file):
            parameter = (cache_dir, gp_mean_file, mapping_group_images[gp])
            parameters.append(parameter)
            
    
    if(len(parameters)>0):
        results = dview.map(_compute_group_mean, parameters)    
        #results = dview.map_sync(_compute_group_mean, parameters)
        #results = map(_compute_group_mean, parameters)
        
    w.running = False
        
    #writing text file
    text_file = open(output_file, "w")
    text_file.write('%s\t%s\n' % (grps, cols))
    
    print "writing file..."
    time.sleep(5) # #let a little time to write properly the last files
    startTime = time.time()
    row = 1.0
    for gp in mapping_group_images.keys():
        gp_name = '_'.join("%s"%i for i in gp)
        gp_mean_file = os.path.join(group_mean_dir, '%s' % gp_name)
        if not os.path.exists('%s.npy' % gp_mean_file):
            print >>sys.stderr, '%s was not computed, exiting program' % gp_name
            text_file.close()
            os.remove(output_file)
            sys.exit(os.EX_USAGE)
        datamean = np.load('%s.npy' % gp_mean_file)
        groupItem = '\t'.join("%s"%i for i in gp)
        values = '\t'.join("%s"%v for v in datamean)
        text_file.write('%s\t%s\n' % (groupItem, values))
        
        if(row % 100 == 0):
            ratio = row/group_item_total
            percent = (ratio * 100)
            now = time.time()
            elapsedTime = (now - startTime)
            estTotalTime = elapsedTime / ratio
            estRemainingTime = estTotalTime - elapsedTime;
            timeleft = time.strftime("%H:%M:%S", time.gmtime(estRemainingTime))
            print '%d%% Est remaining time: %s' % (percent,timeleft)
        row += 1
            
    text_file.close()

if __name__ == '__main__':
 
    # python profile_mean.py '/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2.properties' '/imaging/analysis/2008_12_04_Imaging_CDRP_for_MLPCN/CDP2/cache' '/home/unix/auguste/ImagingAuguste/CDP2/test_cc_map.txt' 'CompoundConcentration' 'compound_treated'

    program_name = os.path.basename(sys.argv[0])
    len_argv = len(sys.argv)
    
    if len_argv < 5 or len_argv > 6:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR OUTPUT_FILE GROUP [FILTER]' % program_name
        sys.exit(os.EX_USAGE)
    
    if len_argv == 5:
        properties_file, cache_dir, output_file, group = sys.argv[1:5]          
        _compute_group_means(properties_file, cache_dir, output_file, group)
        
    if len_argv == 6:
        properties_file, cache_dir, output_file, group, filter = sys.argv[1:6]
        _compute_group_means(properties_file, cache_dir, output_file, group, filter=filter)
     
    

