#!/usr/bin/env python

"""
$ profile_mean.py properties_file cache_dir output_file [group [filter]]

Writes a tab-delimited file containing the profiles. Example:

		f1	f2
GroupItem1	0.123	4.567
GroupItem2	8.901	2.345

"""
import io
import sys
import os
import numpy as np

import cpa
from cpa.util import cache
from cpa.util import percentiles


if __name__ == '__main__':
 
    #program_name = os.path.basename(sys.argv[0])
    #len_argv = len(sys.argv)
    #if len_argv < 4 or len_argv > 6:
        #print >>sys.stderr, 'Usage: %s PROPERTIES-FILE CACHE-DIR OUTPUT_FILE [GROUP [FILTER]]' % program_name
        #sys.exit(os.EX_USAGE)
    #properties_file, cache_dir, output_file = sys.argv[1:4]
    #if len_argv > 4:
        #group = sys.argv[4]
        #if len_argv == 6:
            #ffilter = sys.argv[5]

    # test
    properties_file = 'C:\\Users\\auguste\\Documents\\CDRP\\CDP2\\CDP2.properties'
    cache_dir = 'Z:\\2008_12_04_Imaging_CDRP_for_MLPCN\\CDP2\\cache'
    output_file = 'C:\\Users\\auguste\\Documents\\CDRP\\CDP2\\test.txt'
    group = 'CompoundConcentration'
    
    cpa.properties.LoadFile(properties_file)
    
    mapping_group_images, colnames_group = cpa.db.group_map(group, reverse=True)
    
    images_plates_wells = cpa.db.execute("select distinct %s, %s, %s from %s" % (cpa.properties.image_id, cpa.properties.plate_id, cpa.properties.well_id, cpa.properties.image_table))
    
    # does't unpack directly for any reason
    images = [row[0] for row in images_plates_wells]
    plates = [row[1] for row in images_plates_wells]
    wells  = [row[2] for row in images_plates_wells]
    
    colnames = cache.get_colnames(cache_dir)
    
    grps = '\t'.join("%s"%g for g in colnames_group)
    cols = '\t'.join("%s"%c for c in colnames)
    
    text_file = open(output_file, "w")
    text_file.write('%s\t%s\n' % (grps, cols))
    
    # !! we have no choice but to include the whole well as soon as an image of a well is present in the group... not so great
    # Solution: implement the cache at image level and not well level (hence drawback of increasing file access, also not really usefull in practice)
    for gp in mapping_group_images.keys():
        plate_well = []
        # ensure unicity of each well
        for image in mapping_group_images[gp]:
            i = images.index(image[0])
            value = [plates[i], wells[i]]
            if not value in plate_well:
                plate_well.append(value)
        # collect data
        rawdata = []
        for plate, well in plate_well:
            plate_dir = os.path.join(cache_dir, '%s' % plate)
            for row in cache.load(cache_dir, '%s' % plate, '%s' % well):
                rawdata.append(row)
        
        # compute the mean vector
        normalizeddata = rawdata #percentiles.normalize(rowdata, cache_dir, plate) # <= !!! Cannot normalized because percentiles aren't available
        normalizeddata_mean = np.mean(normalizeddata, axis = 0)
        
        groupItem = '\t'.join("%s"%i for i in gp)
        values = '\t'.join("%d"%v for v in normalizeddata_mean)
        text_file.write('%s\t%s\n' % (groupItem, values))
        #add a line normalizeddata_mean in the file

    text_file.close()

    
    
    
    
