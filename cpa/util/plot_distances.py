#!/usr/bin/env python

"""
Plot distances between profiles.

"""

from optparse import OptionParser
import numpy as np
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import pylab
import cpa
from .profiles import Profiles

def plot_distances(profiles, output_group_name=None):
    if output_group_name:
        input_group_r, input_colnames = cpa.db.group_map(profiles.group_name, 
                                                         reverse=True)
        input_group_r = dict((tuple(map(str, k)), v) 
                             for k, v in input_group_r.items())
        output_group, output_colnames = cpa.db.group_map(output_group_name)
        d = {}
        labels = []
        for i, k in enumerate(profiles.keys()):
            groups = [output_group[image] for image in input_group_r[k]]
            if groups.count(groups[0]) != len(groups):
                print >>sys.stderr, 'Error: Input group %r contains images in %d output groups' % (key, len(set(groups)))
                sys.exit(1)
            d.setdefault(groups[0], []).append(i)
            labels.append(groups[0])
        ordering = [i for k in sorted(d.keys()) for i in d[k]]
        labels = list(np.array(labels)[ordering])
    else:
        ordering = np.arange(len(profiles.keys))
        labels = list(np.array(profiles.keys())[ordering])
    labels = [' '.join(map(str, k)) for k in labels]
    data = profiles.data[ordering]

    for i in range(len(labels))[:0:-1]:
        if labels[i] == labels[i - 1]:
            labels[i] = ''

    fig, ax = plt.subplots()
    dist = cdist(data, data, 'cosine')
    axes_image = ax.imshow(dist, cmap=pylab.cm.RdBu, interpolation='nearest')
    fig.colorbar(axes_image, use_gridspec=True)
    ax.set_yticks([i for i, l in enumerate(labels) if l != ''])
    ax.set_yticklabels([l for l in labels if l != ''])
    for tick in ax.yaxis.iter_ticks():
        tick[0].label1.set_fontsize(8)
    ax.set_xticks([i for i, l in enumerate(labels) if l != ''])
    ax.set_xticklabels(['' for l in labels if l != ''])
    plt.axis('image')
    plt.tight_layout()
    

def parse_arguments():
    parser = OptionParser("usage: %prog PROPERTIES-FILE INPUT-FILENAME GROUP")
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    return options, args

if __name__ == '__main__':
    options, (properties_file, input_filename, group_name) = parse_arguments()
    cpa.properties.LoadFile(properties_file)
    profiles = Profiles.load(input_filename)
    plot_distances(profiles, group_name)
    if options.output_filename:
        pylab.savefig(options.output_filename)
    else:
        pylab.show()
