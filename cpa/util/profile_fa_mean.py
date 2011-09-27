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

class waiter(Thread):
    def init(self, file_dir, file_item_total):
        self.file_dir = file_dir
        self.file_item_total = file_item_total
    
    def run(self):
        self.running = True
        startTime = time.time()
        group_item_current = 1.0
        while(group_item_current < self.file_item_total and self.running):
            filenum = len(os.listdir(self.file_dir))
            if (filenum > 0): 
                group_item_current = float(filenum)
            remaining = self.file_item_total - group_item_current
            ratio = group_item_current/self.file_item_total
            percent = (ratio * 100)
            now = time.time()
            elapsedTime = (now - startTime)
            estTotalTime = elapsedTime / ratio
            estRemainingTime = estTotalTime - elapsedTime;
            timeleft = time.strftime("%H:%M:%S", time.gmtime(estRemainingTime))
            print '(%d) %d%% Est remaining time: %s' % (remaining,percent,timeleft)
            time.sleep(1)
       

            
def _compute_group_subsample((cache_dir, gp_subsample_file, images)):
    try:
        import numpy as np
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=cache.RobustLinearNormalization)
        np.random.shuffle(normalizeddata)
        normalizeddata_sample = [x for i, x in enumerate(normalizeddata) if i % 100 == 0]
        np.save(gp_subsample_file, normalizeddata_sample)
        return normalizeddata_sample
    except: # catch *all* exceptions
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: (%s) %s" % (gp_mean_file,e)
      
def _compute_group_projection_and_mean((cache_dir, gp_fa_mean_file, images, fa_node, meanvector, standarddev)):
    try:
        import numpy as np        
        from cpa.util import cache
        cash = cache.Cache(cache_dir)
        normalizeddata, normalized_colnames = cash.load(images, normalization=cache.RobustLinearNormalization)
        normalizeddata = (normalizeddata - meanvector) / standarddev
        normalizeddata_projected = fa_node.execute(normalizeddata)
        normalizeddata_projected_mean = np.mean(normalizeddata_projected, axis = 0)
        np.save(gp_fa_mean_file, normalizeddata_projected_mean)
        return normalizeddata_mean
    except: # catch *all* exceptions
        e = sys.exc_info()[1]
        print >>sys.stderr, "Error: (%s) %s" % (gp_fa_mean_file,e)
        

class ProfileFAMean(object):
    
    def __init__(self, properties_file, cache_dir, group, filter = None, factors = 50):
        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cash = cache.Cache(cache_dir)
        
        self.group_fa_mean_dir = os.path.join(cache_dir, 'mean_fa_profile_%s' % group)
        if filter:
            self.group_fa_mean_dir = self.group_fa_mean_dir + '_' + filter
        if not os.path.exists(self.group_fa_mean_dir):
            os.mkdir(self.group_fa_mean_dir)

        self.group_subsample_dir = os.path.join(self.group_fa_mean_dir, 'subsample')
        if not os.path.exists(self.group_subsample_dir):
            os.mkdir(self.group_subsample_dir)
            
        self.group_mean_dir = os.path.join(self.group_fa_mean_dir, 'mean')
        if not os.path.exists(self.group_mean_dir):
            os.mkdir(self.group_mean_dir)
        
            
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = self.cash.colnames
        
        
        self.group_subsample_file = os.path.join(self.group_fa_mean_dir, 'subsample.npy')
        if not os.path.exists(self.group_subsample_file):
            self._compute_subsamples()
        
        self.group_fa_mean_file = os.path.join(self.group_fa_mean_dir, 'fa_mean_profile.npy')
        print self.group_fa_mean_file
        if not os.path.exists(self.group_fa_mean_file) and os.path.exists(self.group_subsample_file):
            self._compute_fa_mean_profile(factors)
        
    
    def _compute_subsamples(self):
        client = Client(profile='lsf')
        dview = client[:] #client.load_balanced_view() 

        parameters = []
        group_item_total = len(self.mapping_group_images)
        w = waiter()
        w.init(self.group_subsample_dir, group_item_total)
        w.start()
        
        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp)
            gp_subsample_file = os.path.join(self.group_subsample_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_subsample_file):
                parameter = (self.cache_dir, gp_subsample_file, self.mapping_group_images[gp])
                parameters.append(parameter)
                #print parameter
        
        if(len(parameters)>0):
            results = dview.map_sync(_compute_group_subsample, parameters)
            
            #results = dview.map(_compute_group_mean, parameters)    
            #results = map(_compute_group_mean, parameters)
            #_compute_group_mean(parameters[0])
         
        if(results.__contains__(None)):
            index = results.index(None)
            print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[index]
            _compute_group_mean(parameters[index])
            print >>sys.stderr, '#### Exiting'
            sys.exit(os.EX_USAGE)

        time.sleep(5) #let a little time to write properly the last files
        w.running = False

        print "combining subsample files..."
        startTime = time.time()
        row = 1.0
        data = []
        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp)
            gp_subsample_file = os.path.join(self.group_subsample_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_subsample_file):
                print >>sys.stderr, '%s was not computed, exiting program' % gp_name
                sys.exit(os.EX_USAGE)
            subsample = np.load('%s.npy' % gp_subsample_file)
            data.extend(subsample)
            
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
            
        np.save(self.group_subsample_file, data)
    
    def _compute_fa_mean_profile(self,factors):
       
        subsampled_data = np.load(self.group_subsample_file)
  
        print "computing Factor Analysis"
        meanvector = np.mean(subsampled_data, axis = 0)   
        subsampled_data = subsampled_data - meanvector
        standarddev = np.std(subsampled_data, axis = 0)
        subsampled_data = subsampled_data/standarddev
        
        factors = min(factors, subsampled_data.shape[1])
        
        fa_node = nodes.FANode(input_dim=None, output_dim=factors, dtype=None, max_cycles=20)
        fa_node.train(subsampled_data)
        fa_node.stop_training()
        
        client = Client(profile='lsf')
        dview = client[:] #client.load_balanced_view() 

        parameters = []
        group_item_total = len(self.mapping_group_images)
        print "projecting groups (%s) ..." % len(self.mapping_group_images)
        w = waiter()
        w.init(self.group_mean_dir, group_item_total)
        w.start()

        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp)
            gp_fa_mean_file = os.path.join(self.group_mean_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_fa_mean_file):
                parameter = (self.cache_dir, gp_fa_mean_file, self.mapping_group_images[gp], fa_node, meanvector, standarddev)
                parameters.append(parameter)
                #print parameter
        
        if(len(parameters)>0):
            results = dview.map_sync(_compute_group_projection_and_mean, parameters)
            
            #results = dview.map(_compute_group_projection_and_mean, parameters)    
            #results = map(_compute_group_projection_and_mean, parameters)
            #_compute_group_projection_and_mean(parameters[0])
            
        if(results.__contains__(None)):
            index = results.index(None)
            print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[index]
            _compute_group_mean(parameters[index])
            print >>sys.stderr, '#### Exiting'
            sys.exit(os.EX_USAGE)

        time.sleep(5) #let a little time to write properly the last files
        w.running = False

        print "combining group mean files..."
        startTime = time.time()
        row = 1.0
        data = []
        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp)
            gp_fa_mean_file = os.path.join(self.group_mean_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_fa_mean_file):
                print >>sys.stderr, '%s was not computed (%s), exiting program' % (gp_name,gp_fa_mean_file)
                sys.exit(os.EX_USAGE)
            datamean = np.load('%s.npy' % gp_fa_mean_file)
            labeleddatamean = ['_'.join("%s"%i for i in gp)] + list(datamean)
            data.append(labeleddatamean)
            
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
        np.save(self.group_fa_mean_file, data)

    def get_data(self):
        return np.load('%s.npy' % self.gp_fa_mean_file)
        
    def save_as_ext_file(self, output_file):

        grps = '\t'.join("%s"%g for g in self.colnames_group)
        cols = '\t'.join("%s"%c for c in self.colnames)

        #writing text file
        text_file = open(output_file, "w")
        text_file.write('%s\t%s\n' % (grps, cols))
        for gp in self.mapping_group_images.keys():
            gp_name = '_'.join("%s"%i for i in gp)
            gp_fa_mean_file = os.path.join(self.group_mean_dir, '%s' % gp_name)
            if not os.path.exists('%s.npy' % gp_fa_mean_file):
                print >>sys.stderr, '%s was not computed (%s), exiting program' % (gp_name,gp_fa_mean_file)
                text_file.close()
                os.remove(output_file)
                sys.exit(os.EX_USAGE)
            datamean = np.load('%s.npy' % gp_fa_mean_file)
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%s"%v for v in datamean)
            text_file.write('%s\t%s\n' % (groupItem, values))
                
        text_file.close()
    
    
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
     
    

