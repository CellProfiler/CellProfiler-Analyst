#!/usr/bin/env python

from optparse import OptionParser
import numpy as np
import cpa
from scipy.spatial.distance import cdist, cosine
from .profiles import Profiles

def regroup(profiles, group_name):
    input_group_r, input_colnames = cpa.db.group_map(profiles.group_name, 
                                                     reverse=True)
    input_group_r = dict((tuple(map(str, k)), v) 
                         for k, v in input_group_r.items())

    group, colnames = cpa.db.group_map(group_name)
    #group = dict((v, tuple(map(str, k))) 
    #             for v, k in group.items())
    d = {}
    for key in profiles.keys():
        images = input_group_r[key]
        groups = [group[image] for image in images if image in group]
        if len(groups) == 0:
            # No group defined for this image.
            continue
        if groups.count(groups[0]) != len(groups):
            print >>sys.stderr, 'Error: Input group %r contains images in %d output groups' % (key, len(set(groups)))
            sys.exit(1)
        d[key] = groups[0]
    return d

def vote(predictions):
    votes = {}
    for i, prediction in enumerate(predictions):
        votes.setdefault(prediction, []).append(i)
    winner = sorted((len(indices), indices[0]) for k, indices in votes.items())[-1][1]
    return predictions[winner]

def crossvalidate(profiles, true_group_name, holdout_group_name=None):
    profiles.assert_not_isnan()

    true_labels = regroup(profiles, true_group_name)

    if holdout_group_name:
       holdouts = regroup(profiles, holdout_group_name)
    else:
       holdouts = None

    confusion = {}
    dist = cdist(profiles.data, profiles.data, 'cosine')
    keys = profiles.keys()
    for i, key in enumerate(keys):
       if key not in true_labels:
           continue
       true = true_labels[key]
       if holdouts:
          ho = tuple(holdouts[key])
          held_out = np.array([tuple(holdouts[k]) == ho for k in keys], dtype=bool)
          dist[i, held_out] = -1.
       else:
          dist[i, i] = -1.
       indices = np.argsort(dist[i, :])
       predictions = []
       for j in indices:
           if dist[i, j] == -1.:
               continue # Held out.
           if keys[j] not in true_labels:
               continue
           predictions.append(true_labels[keys[j]])
           if len(predictions) == 1:
               predicted = vote(predictions)
               confusion[true, predicted] = confusion.get((true, predicted), 0) + 1
               break
    return confusion


class NNClassifier(object):
    def __init__(self, features, labels):
        assert isinstance(labels, list)
        assert len(labels) == features.shape[0]
        self.features = features
        self.labels = labels

    def classify(self, feature):
        distances = np.array([cosine(f, feature) for f in self.features])
        return self.labels[np.argmin(distances)]


def crossvalidate(profiles, true_group_name, holdout_group_name=None, 
                  sva=False, train=NNClassifier):
    profiles.assert_not_isnan()
    keys = profiles.keys()
    true_labels = regroup(profiles, true_group_name)
    labels = list(set(true_labels.values()))

    if holdout_group_name:
        holdouts = regroup(profiles, holdout_group_name)
    else:
        holdouts = dict((k, k) for k in keys)

    confusion = {}
    for ho in set(holdouts.values()):
        test_set_mask = np.array([tuple(holdouts[k]) == ho for k in keys], 
                                 dtype=bool)
        training_features = profiles.data[~test_set_mask, :]
        test_features = profiles.data[test_set_mask, :]
        training_labels = [labels.index(true_labels[tuple(k)]) 
                           for k, m in zip(keys, ~test_set_mask) if m]
        if sva:
            import pyRserve
            conn = pyRserve.connect()
            conn.r.traininglabels = np.array(training_labels, dtype='i4')
            conn.r.trainData = training_features.ravel().reshape(training_features.shape, order='F').T
            conn.r.testData = test_features.ravel().reshape(test_features.shape, order='F').T
            #import pdb; pdb.set_trace()
            #assert conn.r('trainData[1,2]') == training_features[1, 0]
            #assert conn.r('testData[1,2]') == test_features[1, 0]
            conn.r('library(sva)')
            conn.r('trainData <- as.matrix(trainData)')
            conn.r('testData <- as.matrix(testData)')
            conn.r('trainpheno <- data.frame(label=traininglabels)')
            #conn.r('write.table(trainData, "/tmp/trainData.txt")')
            #conn.r('write.table(testData, "/tmp/testData.txt")')
            #conn.r('write.table(trainpheno, "/tmp/trainpheno.txt")')
            conn.r('trainMod <- model.matrix(~as.factor(label), trainpheno)')
            nsv = conn.r('num.sv(trainData, trainMod)')
            print nsv, 'surrogate variables'
            conn.r('trainMod0 <- model.matrix(~1, trainpheno)')
            conn.r('trainSv <- sva(trainData, trainMod, trainMod0, B=1)')
            conn.r('fsvaobj <- fsva(trainData, trainMod, trainSv, testData)')
            filtered_train = getattr(conn.r, 'fsvaobj$db').T
            filtered_test = getattr(conn.r, 'fsvaobj$new').T
        else:
            filtered_train = training_features
            filtered_test = test_features

        model = train(filtered_train, training_labels)
        for k, f, m in zip(keys, profiles.data, test_set_mask):
            if not m:
                continue
            true = true_labels[k]
            predicted = labels[model.classify(f)]
            confusion[true, predicted] = confusion.get((true, predicted), 0) + 1
    return confusion

def confusion_matrix(confusion, dtype=int):
   labels = set()
   for a, b in confusion.keys():
      labels.add(a)
      labels.add(b)
   labels = sorted(labels)
   cm = np.zeros((len(labels), len(labels)), dtype=dtype)
   for (a, b), count in confusion.items():
      cm[labels.index(a), labels.index(b)] = count
   return cm

def confusion_reduce(operation, confusions):
   d = confusions[0].copy()
   for c in confusions[1:]:
      for k, v in c:
         d[k] = operation(d[k], v)
   return d

def print_confusion_matrix(confusion):
   cm = confusion_matrix(confusion)
   print cm
   print 'Overall: %d / %d = %.0f %%' % (np.diag(cm).sum(), cm.sum(),
                                         100.0 * np.diag(cm).sum() / cm.sum())

def print_confusion(confusion):
    for (a, b), v in confusion.items():
        print '\t'.join([' '.join(a), ' '.join(b), str(v)])

if __name__ == '__main__':
    parser = OptionParser("usage: %prog [-c] [-h HOLDOUT-GROUP] PROPERTIES-FILE PROFILES-FILENAME TRUE-GROUP")
    parser.add_option('-c', dest='csv', help='input and output as CSV', action='store_true')
    parser.add_option('-s', dest='sva', help='surrogate variable analysis', action='store_true')
    parser.add_option('-H', dest='holdout_group', help='hold out all that map to the same holdout group', action='store')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Incorrect number of arguments')
    properties_file, profiles_filename, true_group_name = args
    cpa.properties.LoadFile(properties_file)

    if options.csv:
       profiles = Profiles.load_csv(profiles_filename)
    else:
       profiles = Profiles.load(profiles_filename)

    confusion = crossvalidate(profiles, true_group_name,
                              options.holdout_group, sva=options.sva)
    print_confusion(confusion)
