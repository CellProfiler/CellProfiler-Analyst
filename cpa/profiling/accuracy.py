"""
Compute the overall accuracy of a confusion matrix
"""

import sys
from optparse import OptionParser
import numpy as np
import cpa.util
from cpa.profiling.confusion import confusion_matrix, load_confusion

parser = OptionParser("usage: %prog [options] CONFUSION")
parser.add_option('-f', dest='float', action='store_true', help='use floating-point accuracies')
parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
options, args = parser.parse_args()
if len(args) != 1:
    parser.error('Incorrect number of arguments')
(input_filename,) = args

confusion = load_confusion(input_filename)
cm = confusion_matrix(confusion, 'if'[options.float or 0])
acc = 100.0 * np.diag(cm).sum() / cm.sum()

def write_output(f):
    print >>f, '%.0f%%' % acc

if options.output_filename:
    with cpa.util.replace_atomically(options.output_filename) as f:
        write_output(f)
else:
    write_output(sys.stdout)

