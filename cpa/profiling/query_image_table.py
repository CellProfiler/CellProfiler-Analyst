'''
Query image_table that exists in cache

Example usage as a script:

$ python -m cpa.profiling.query_image_table <PLATE_DIR>  
"select Metadata_Barcode, Metadata_Well, sum(Metadata_isLowIntensity) as Metadata_isLowIntensity from _image_table group by Metadata_Barcode, Metadata_Well"

'''


import sys
import os
import logging
from optparse import OptionParser

logger = logging.getLogger(__name__)

import abc
class Query(object):
    __metaclass__ = abc.ABCMeta
    
    _cached_colmask = None

    def __init__(self, cache):
        self.cache = cache


    def query_image_table(self, query_str):
        """Query image_table"""
        plates_and_images = {}
        from pandasql import sqldf
        _image_table = self.cache.get_image_table()
        df = sqldf(query_str, locals())
        return df
        
                                
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = OptionParser("usage: %prog PLATE-DIR QUERY")
    parser.add_option('-o', dest='output_file', action='store', help='output_file')
    
    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error('Incorrect number of arguments')
        
    cache_dir = os.path.join(args[0], "profiling_params")
    query_str = args[1]

    from cpa.profiling.cache import Cache
    cache = Cache(cache_dir)
    queryer = Query(cache)

    res = queryer.query_image_table(query_str)
    
    res.to_csv(options.output_file, index=False)
        