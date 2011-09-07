#!/usr/bin/env python

"""
$ profile_mean.py properties_file cache_dir group [output_file]

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
import commands
from threading import Thread
import itertools

import cpa
from cpa.util import cache
from cpa.util import percentiles



def _compute_group_means(properties_file, cache_dir, group, output_file=''):
       
    cpa.properties.LoadFile(properties_file)
    
    group_mean_dir = os.path.join(cache_dir, 'mean_profile_%s' % group)
    if not os.path.exists(group_mean_dir):
        os.mkdir(group_mean_dir)
    
    mapping_group_images, colnames_group = cpa.db.group_map(group, reverse=True)
    
    colnames = cache.get_colnames(cache_dir)
    
    grps = '\t'.join("%s"%g for g in colnames_group)
    cols = '\t'.join("%s"%c for c in colnames)
    
    combine = len(output_file) != 0
    
    if combine:
        text_file = open(output_file, "w")
        text_file.write('%s\t%s\n' % (grps, cols))
        
    # !! we have no choice but to include the whole well as soon as an image of a well is present in the group... not so great
    for gp in mapping_group_images.keys()[0:4]:
    
        predicate = (' or %s='%(cpa.properties.image_id)).join("%d"%im for im in mapping_group_images[gp])
        predicate = '%s=%s' % (cpa.properties.image_id, predicate)
        
        # has to be inside the loop because Copper for instance hasn't enough memory 
        images_plates_wells = cpa.db.execute("select distinct %s, %s, %s from %s where %s" % (cpa.properties.image_id, cpa.properties.plate_id, cpa.properties.well_id, cpa.properties.image_table, predicate))
        images = [row[0] for row in images_plates_wells]
        plates = [row[1] for row in images_plates_wells]
        wells  = [row[2] for row in images_plates_wells]
        
        # ensure unicity of each well
        plate_well = []
        for image in mapping_group_images[gp]:
            i = images.index(image[0])
            value = [plates[i], wells[i]]
            if not value in plate_well:
                plate_well.append(value)

        gp_name = '_'.join("%s"%i for i in gp)
        gp_mean_file = os.path.join(group_mean_dir, '%s' % gp_name)

        if combine:
            # combine data
            print '%s.npy' % gp_mean_file
            datamean = np.load('%s.npy' % gp_mean_file)
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%s"%v for v in datamean)
            text_file.write('%s\t%s\n' % (groupItem, values))
        else:
            # collect data with LSF 
            sub_output_file = os.path.join(group_mean_dir, '%s.txt' % gp_name)
            well_plate_args =  ' '.join("'%s'"%i for i in list(itertools.chain(*plate_well)))
            bsubcommand = "bsub -P mean_profile -o %s -q hour python ./profile_mean.py '%s' '%s' '%s' '%s' %s" % (sub_output_file, properties_file, cache_dir, group, gp_mean_file, well_plate_args)
            #print bsubcommand
            commands.getstatusoutput(bsubcommand)
        
    if combine:
        text_file.close()


def _compute_group_mean(cache_dir, gp_mean_file, plate_well):
    
    rawdata = []
    for i in range(0,len(plate_well)-1,2):
        plate = plate_well[i]
        well  = plate_well[i+1]
        plate_dir = os.path.join(cache_dir, '%s' % plate)
        for row in cache.load(cache_dir, '%s' % plate, '%s' % well):
            rawdata.append(row)
    
    # compute the mean vector
    normalizeddata = percentiles.normalize(np.array(rawdata), cache_dir, plate)
    normalizeddata_mean = np.mean(normalizeddata, axis = 0)
    np.save(gp_mean_file, normalizeddata_mean)
    
    
    
    


if __name__ == '__main__':
 
    program_name = os.path.basename(sys.argv[0])
    len_argv = len(sys.argv)

    # profile_mean.py properties_file cache_dir group [output_file]

    if len_argv < 4:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR GROUP [OUTPUT_FILE]' % program_name
        sys.exit(os.EX_USAGE)

    if len_argv == 4:
        properties_file, cache_dir, group = sys.argv[1:4]          
        _compute_group_means(properties_file, cache_dir, group)

    elif len_argv == 5:
        properties_file, cache_dir, group, output_file = sys.argv[1:5]          
        _compute_group_means(properties_file, cache_dir, group, output_file)

    elif len_argv > 5:
        properties_file, cache_dir, group, gp_mean_file = sys.argv[1:5]
        plate_well = sys.argv[5:len_argv]    
        _compute_group_mean(cache_dir, gp_mean_file, plate_well)
    


