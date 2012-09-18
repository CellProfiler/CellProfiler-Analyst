"""
Determine a number of factors using the Kaiser rule.
See http://yatani.jp/HCIstats/FA
"""

from optparse import OptionParser
import numpy as np
from cpa.util import replace_atomically
from .profiles import Profiles

def parse_arguments():
    parser = OptionParser("usage: %prog INPUT-FILENAME")
    parser.add_option('-o', dest='output_filename', help='file to store the output in')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Incorrect number of arguments')
    return options, args

if __name__ == '__main__':
    options, (input_filename,) = parse_arguments()
    profiles = Profiles.load(input_filename)
    c = np.corrcoef(profiles.data.T)
    w, v = np.linalg.eig(c)
    nfactors = (w >= 1).sum()

    if options.output_filename:
        with replace_atomically(options.output_filename) as f:
            print >>f, nfactors
    else:
        print nfactors


