from optparse import OptionParser
import numpy as np
from scipy.spatial.distance import pdist, cdist
import pylab
from .profiles import Profiles
import cpa
from cpa.util import auc

def compute_inter_intra_distances(profiles, true_group_name):
    label_map = profiles.regroup(true_group_name)
    labels = label_map.values()
    label_indices = np.array([labels.index(label_map[k])
                              for k in profiles.keys()], dtype='i4')
    grouped_data = [profiles.data[label_indices == i]
                    for i in range(label_indices.max() + 1)]
    intra_distances = np.hstack([pdist(data, 'cosine')
                                 for data in grouped_data])
    inter_distances = np.hstack([cdist(d1, d2, 'cosine').ravel()
                                 for d1 in grouped_data
                                 for d2 in grouped_data])
    return inter_distances, intra_distances

def plot_inter_intra_distances(profiles, true_group_name):
    inter_distances, intra_distances = compute_inter_intra_distances(profiles,
                                                                     true_group_name)
    print 'AUC:', auc(inter_distances, intra_distances)
    h_intra, e_intra = np.histogram(intra_distances, 15, normed=True)
    h_inter, e_inter = np.histogram(inter_distances, 15, normed=True)
    pylab.bar(e_intra[:-1], h_intra, e_intra[1] - e_intra[0], color='r', 
              alpha=0.5, label='Intra-' + true_group_name)
    pylab.bar(e_inter[:-1], h_inter, e_inter[1] - e_inter[0], color='b', 
              alpha=0.5, label='Inter-' + true_group_name)
    pylab.legend(loc='upper right')
    pylab.xlabel('Cosine distance')
    pylab.ylabel('Normalized frequency (probability density)')
    pylab.xlim(0, None)

if __name__ == '__main__':
    parser = OptionParser("usage: %prog PROPERTIES-FILE PROFILES-FILENAME TRUE-GROUP")
    parser.add_option('-o', dest='output_filename', help='file to store the profiles in')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, profiles_filename, true_group_name = args
    cpa.properties.LoadFile(properties_file)

    profiles = Profiles.load(profiles_filename)

    plot_inter_intra_distances(profiles, true_group_name)
    if options.output_filename:
        pylab.savefig(options.output_filename)
    else:
        pylab.show()
