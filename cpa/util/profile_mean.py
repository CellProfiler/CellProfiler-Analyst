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
        #print gp_mean_file
        return normalizeddata_mean
    except: # catch *all* exceptions
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: (%s) %s" % (gp_mean_file,e) 
        

class ProfileMean(object):
    
    def __init__(self, properties_file, cache_dir, group, filter = None):
        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cash = cache.Cache(cache_dir)
        
        self.group_mean_dir = os.path.join(cache_dir, 'mean_profile_%s' % group)
        if filter:
            self.group_mean_dir = self.group_mean_dir + '_' + filter
        
        if not os.path.exists(self.group_mean_dir):
            os.mkdir(self.group_mean_dir)
            
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = cache.RobustLinearNormalization(self.cash).colnames
        
        self.group_mean_file = '%s.npy' % self.group_mean_dir
        
        if not os.path.exists(self.group_mean_file):
            self._compute_mean_profile()
        
    
    def _compute_mean_profile(self):
        
        parameters = []
        group_item_total = len(self.mapping_group_images)

        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp).replace('/','_')
            gp_mean_file = os.path.join(self.group_mean_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_mean_file):
                parameter = (self.cache_dir, gp_mean_file, self.mapping_group_images[gp])
                parameters.append(parameter)
                #print parameter
        
        if(len(parameters)>0):
            client = Client(profile='lsf')
            dview = client[:] #client.load_balanced_view() 
            #dview.block = True
            
            w = waiter()
            w.init(self.group_mean_dir, group_item_total)
            w.start()
            
            results = dview.map_sync(_compute_group_mean, parameters)
            
            #results = dview.map(_compute_group_mean, parameters)    
            #results = map(_compute_group_mean, parameters)
            #results = [_compute_group_mean(parameters[0])]
        
            if(results.__contains__(None)):
                index = results.index(None)
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[index][1]
                _compute_group_mean(parameters[index])
                print >>sys.stderr, '#### Exiting'
                sys.exit(os.EX_USAGE)
            
            time.sleep(5) #let a little time to write properly the last files
            
            w.running = False            
        
    def save_as_text_file(self, output_file):

        grps = '\t'.join("%s"%g for g in self.colnames_group)
        cols = '\t'.join("%s"%c for c in self.colnames)

        group_item_total = len(self.mapping_group_images)

        print "combining files..."
        startTime = time.time()
        row = 1.0

        text_file = open(output_file + '.txt', "w")
        text_file.write('%s\t%s\n' % (grps, cols))
        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp).replace('/','_')
            gp_mean_file = os.path.join(self.group_mean_dir, '%s' % gp_name)
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
    
    def save_as_csv_file(self, output_file):

        group_item_total = len(self.mapping_group_images)

        print "combining files..."
        startTime = time.time()
        row = 1.0

        csv_file = csv.writer(open(output_file + '.csv', "w"))
        csv_file.writerow(list(self.colnames_group) + list(self.colnames))

        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp).replace('/','_')
            gp_mean_file = os.path.join(self.group_mean_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_mean_file):
                print >>sys.stderr, '%s was not computed, exiting program' % gp_name
                os.remove(output_file)
                sys.exit(os.EX_USAGE)
            datamean = np.load('%s.npy' % gp_mean_file)
            csv_file.writerow(list(gp) + list(datamean))
            
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
        profileMean.save_as_text(output_file) 
        
    if len_argv == 6:
        properties_file, cache_dir, output_file, group, filter = sys.argv[1:6]
        profileMean = ProfileMean(properties_file, cache_dir, group, filter=filter)
        profileMean.save_as_text(output_file) 
     
    

