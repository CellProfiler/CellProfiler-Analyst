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
from optparse import OptionParser
import time
import itertools
import progressbar
import numpy as np
from datetime import timedelta
from threading import Thread

import cpa
from cpa.util import cache

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

class IMapUnorderedIterator(object):
    def __init__(self, client, msg_ids):
        self.client = client
        self.msg_ids = msg_ids
        self.returned = set()
        self.queue = []
        
    def __len__(self):
        return len(self.msg_ids)

    def __iter__(self):
        return self

    def next(self):
        if len(self.returned) == len(self.msg_ids):
            raise StopIteration
        if len(self.queue) == 0:
            while True:
                msg_ids = list(set(self.msg_ids)
                               .intersection(self.client.history)
                               .difference(self.returned))
                results = self.client.result_status(msg_ids, status_only=False)
                if results['completed']:
                    for msg_id in results['completed']:
                        self.returned.add(msg_id)
                        self.queue.append(results[msg_id])
                    break
                else:
                    time.sleep(1e-3)
                    self.client.spin()
        return self.queue.pop()
            

def ParallelFunction_imap_unordered(self, func, iterable, chunksize=1):
    if chunksize != 1:
        raise NotImplementedError
    ar = self.map(func, iterable)
    return IMapUnorderedIterator(self.client, ar.msg_ids)

class ProfileMean(object):
    
    def __init__(self, properties_file, cache_dir, group, filter=None, profile=None):
        cpa.properties.LoadFile(properties_file)
        self.cache_dir = cache_dir
        self.cash = cache.Cache(cache_dir)
        
        self.mapping_group_images, self.colnames_group = cpa.db.group_map(group, reverse=True, filter=filter)
        self.colnames = cache.RobustLinearNormalization(self.cash).colnames
        
        parameters = [(self.cache_dir, self.mapping_group_images[gp])
                      for gp in self.mapping_group_images.keys()]
        njobs = len(parameters)
        print njobs, 'jobs'

        if profile:
            from IPython.parallel import Client, LoadBalancedView
            client = Client(profile='lsf')
            LoadBalancedView.imap_unordered = ParallelFunction_imap_unordered
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
        results = list(progress(lview.imap_unordered(_compute_group_mean, 
                                                     parameters)))

        for i, (p, r) in enumerate(zip(parameters, results)):
            if r is None:
                print >>sys.stderr, '#### There was an error, recomputing locally: %s' % parameters[i][1]
                results[i] = _compute_group_mean(p)

        self.results = results
        
    def save_as_text(self, text_file):
        grps = '\t'.join('' for g in self.colnames_group)
        cols = '\t'.join("%s"%c for c in self.colnames)
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

    parser = OptionParser("usage: %prog [--profile PROFILE-NAME] [-o OUTPUT-FILENAME] [-f FILTER] PROPERTIES-FILE CACHE-DIR GROUP")
    parser.add_option('--profile', dest='profile', help='iPython.parallel profile')
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    parser.add_option('-f', dest='filter', help='only profile images matching this CPAnalyst filter')
    options, args = parser.parse_args()

    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, cache_dir, group = args

    profileMean = ProfileMean(properties_file, cache_dir, group, 
                              filter=options.filter, profile=options.profile)
    if options.output_filename:
        with open(options.output_filename, "w") as f:
            profileMean.save_as_text(f)
    else:
        profileMean.save_as_text(sys.stdout)
