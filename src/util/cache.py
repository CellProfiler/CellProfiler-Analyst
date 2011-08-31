'''
Cache of per-well block of per-cell feature data.
'''

import sys
import numpy as np

def load(cache_dir, plate_name, well_name):
    # return numpy array

def get_colnames(cache_dir):
    # reads colnames.txt and returns a list of strings

if __name__ == '__main__':
    properties, cache_dir = sys.argv[1:]
    # create directory, load raw features from the database, write
    # them to npy files, write list of columns to colnames.txt
