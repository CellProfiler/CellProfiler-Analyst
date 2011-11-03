#!/usr/bin/env python

"""
Plot distances between profiles.

"""

from optparse import OptionParser
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import pylab
from .profiles import Profiles

def plot_distances(profiles):
    fig = plt.figure()
    fig.set_size_inches(800 / 72, 800 / 72)
    ax = fig.add_axes([0.4, 0.1, 0.5, 0.8])
    dist = cdist(profiles.data, profiles.data, 'cosine')
    axes_image = ax.imshow(dist, cmap=pylab.cm.RdBu_r, interpolation='nearest')
    yfirst_labels = [' '.join(map(str, k)) for k in profiles.keys()]
    ax.set_yticks([i for i, l in enumerate(yfirst_labels) if l != ''])
    ax.set_yticklabels([l for l in yfirst_labels if l != ''])
    for tick in ax.yaxis.iter_ticks():
        tick[0].label1.set_fontsize(8)
    xfirst_labels = yfirst_labels
    ax.set_xticks([i for i, l in enumerate(xfirst_labels) if l != ''])
    ax.set_xticklabels(['' for l in xfirst_labels if l != ''])
    plt.axis('image')
    

def parse_arguments():
    parser = OptionParser("usage: %prog PROPERTIES-FILE INPUT-FILENAME GROUP")
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    return options, args

if __name__ == '__main__':
    options, (properties_file, input_filename, group_name) = parse_arguments()
    cpa.properties.LoadFile(properties_file)
    profiles = Profiles.load(input_filename)
    # TODO: Get group from profiles.group_name, use group_name to
    # obtain a sort order, and make labels.
    plot_distances(profiles)
    pylab.show()
