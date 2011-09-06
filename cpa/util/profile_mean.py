#!/usr/bin/env python

"""
$ profile_mean.py properties_file cache_dir output_file group [filter]

Writes a tab-delimited file containing the profiles. Example:

		f1	f2
GroupItem1	0.123	4.567
GroupItem2	8.901	2.345

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



def _compute_group_means(properties_file, cache_dir, group, combine=False):
    
    # test
    #properties_file = 'C:\\Users\\auguste\\Documents\\CDRP\\CDP2\\CDP2.properties'
    #cache_dir = 'Z:\\2008_12_04_Imaging_CDRP_for_MLPCN\\CDP2\\cache'
    #output_file = 'C:\\Users\\auguste\\Documents\\CDRP\\CDP2\\test.txt'
    #group = 'CompoundConcentration'
    
    cpa.properties.LoadFile(properties_file)
    
    group_mean_dir = os.path.join(cache_dir, 'mean_profile_%s' % group)
    if not os.path.exists(group_mean_dir):
        os.mkdir(group_mean_dir)
    
    mapping_group_images, colnames_group = cpa.db.group_map(group, reverse=True)
    
    images_plates_wells = cpa.db.execute("select distinct %s, %s, %s from %s" % (cpa.properties.image_id, cpa.properties.plate_id, cpa.properties.well_id, cpa.properties.image_table))
    
    # cannot unpack directly above for any reason so do it here
    images = [row[0] for row in images_plates_wells]
    plates = [row[1] for row in images_plates_wells]
    wells  = [row[2] for row in images_plates_wells]
    
    colnames = cache.get_colnames(cache_dir)
    
    grps = '\t'.join("%s"%g for g in colnames_group)
    cols = '\t'.join("%s"%c for c in colnames)
    
    if combine:
        text_file = open(output_file, "w")
        text_file.write('%s\t%s\n' % (grps, cols))
    
    # !! we have no choice but to include the whole well as soon as an image of a well is present in the group... not so great
    # Solution: implement the cache at image level and not well level (hence drawback of increasing file access, also not really usefull in practice)
    for gp in mapping_group_images.keys()[0:4]:
    
        # ensure unicity of each well
        plate_well = []
        for image in mapping_group_images[gp]:
            i = images.index(image[0])
            value = [plates[i], wells[i]]
            if not value in plate_well:
                plate_well.append(value)

        gp_name = '_'.join("%s"%i for i in gp)
        gp_mean_file = os.path.join(group_mean_dir, '%s.py' % gp_name)

        if combine:
            # combine data
            datamean = np.load(os.path.join(group_mean_dir, '%s.npy' % plate_well), normalizeddata_mean)
            groupItem = '\t'.join("%s"%i for i in gp)
            values = '\t'.join("%d"%v for v in normalizeddata_mean)
            text_file.write('%s\t%s\n' % (groupItem, values))
        else:
            # collect data with LSF 
            sub_output_file = os.path.join(group_mean_dir, '%s.txt' % gp_name)
            well_plate_args =  ' '.join("%s"%i for i in list(itertools.chain(*plate_well)))
            commands.getstatusoutput("bsub -P mean_profile -o %s -q hour python ./profile_mean.py '%s' '%s'" 
                                     % (sub_output_file,    ,well_plate_args))
            _compute_group_mean(cache_dir, plate_well)
        
        
        #add a line normalizeddata_mean in the file
    if combine:
        text_file.close()


def _compute_group_mean(cache_dir, group_mean_dir, plate_well):
    rawdata = []
    plates = plate_well[::2]
    wells = plate_well[1::2]
    for plate, well in plates, wells:
        plate_dir = os.path.join(cache_dir, '%s' % plate)
        for row in cache.load(cache_dir, '%s' % plate, '%s' % well):
            rawdata.append(row)
    
    # compute the mean vector
    normalizeddata = rawdata #percentiles.normalize(rowdata, cache_dir, plate) # <= !!! Cannot normalized because percentiles aren't available
    normalizeddata_mean = np.mean(normalizeddata, axis = 0)
    np.save(os.path.join(group_mean_dir, '%s.npy' % plate_well), normalizeddata_mean)

    
    
    


if __name__ == '__main__':
 
    program_name = os.path.basename(sys.argv[0])
    len_argv = len(sys.argv)

    if len_argv < 5:
        print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR OUTPUT_FILE GROUP [FILTER]' % program_name
        sys.exit(os.EX_USAGE)

    elif len_argv == 5 or len_argv == 6:
        properties_file, cache_dir, output_file, group = sys.argv[1:5]          
        if len_argv == 6:
            ffilter = sys.argv[5]
            print >>sys.stderr, 'FILTER option not implemented yet' % program_name
            sys.exit(os.EX_USAGE)
        _compute_group_means(properties_file, cache_dir, output_file, group)

    elif len_argv > 6:
        plate_well = sys.argv[7:len_argv]    
        _compute_group_mean(cache_dir, plate_well)
    


