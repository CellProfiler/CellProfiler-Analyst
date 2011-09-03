#!/usr/bin/env python

"""
$ profile_mean.py properties_file cache_dir output_file [group [filter]]

Writes a tab-delimited file containing the profiles. Example:

		f1	f2
Plate1	A01	0.123	4.567
Plate1	A02	8.901	2.345

or:

	f1	f2
Gene1	0.123	4.567
Gene2	8.901	2.345
"""
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

            
            
    properties_file = 'C:\\Users\\auguste\\Documents\\CDRP\\CDP2\\CDP2.properties'
    cache_dir = 'Z:\\2008_12_04_Imaging_CDRP_for_MLPCN\\CDP2\\cache'
    output_file = 'C:\\Users\\auguste\\Documents\\CDRP\\CDP2\\test'
    group = 'CompoundConcentration'
    
    #colnames = cache.get_colnames(cache_dir)
    
    cpa.properties.LoadFile(properties_file)
    
    mapping_group_images, colnames_group = cpa.db.group_map(group, reverse=True)
    
    images_plates_wells = cpa.db.execute("select distinct %s, %s, %s from %s" % (cpa.properties.image_id, cpa.properties.plate_id, cpa.properties.well_id, cpa.properties.image_table))
    
    # does't unpack directly for any reason
    images = [row[0] for row in images_plates_wells]
    plates = [row[1] for row in images_plates_wells]
    wells  = [row[2] for row in images_plates_wells]
    
    # !! we have to include the whole well as soon as an image of a well is present in the group... not so great
    # This prevent the granularity to be below the well level and can lead to unexpected results in this case.
    # Solution: implement the cache at image level and not well level (hence drawback of increasing file access, also not really usefull in practice)
    
    for gp in mapping_group_images.keys()[0:3]:
            # gp = mapping_group_images.keys()[0]            
            plate_well = []
            # ensure unicity of well
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
            normalizeddata = rawdata #percentiles.normalize(rowdata, cache_dir, plate)
            normalizeddata_mean = np.mean(normalizeddata, axis = 0)
            print normalizeddata_mean[0:5]
            #add a line normalizeddata_mean in the file


    
    
    
    
