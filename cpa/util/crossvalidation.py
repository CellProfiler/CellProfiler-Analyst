#!/usr/bin/env python

'''
Cross validation.

'''

import sys
import csv
import numpy as np
import itertools as it
import matplotlib.pyplot as plt
import matplotlib as mpl

def _k_fold_cross_validation_iterator(cdata, K):
   """
   Generates K (training, validation) pairs from the items in X.
   """
   np.random.shuffle(cdata)
   for k in xrange(K):
      training = np.array([x for i, x in enumerate(cdata) if i % K != k])
      validation = np.array([x for i, x in enumerate(cdata) if i % K == k])
      yield training, validation


def get_confusion_matrix(classifier, cdata, K=10):
   '''   
   return classes, confusion, percent, avg
   
   compute a confusion matrix from the 'K'-fold validation of the 'classifier' on the 'cdata', cdata contains class labels in the first column
   '''
   classes = np.sort(np.unique(cdata[:,0]))
   numclasses = classes.shape[0]
   confusion = np.zeros((numclasses,numclasses), dtype=np.int)
   
   for training, test in _k_fold_cross_validation_iterator(cdata, K): 
      training_data   = training[:,1:]
      training_labels = training[:,0]
      
      test_data   = test[:,1:]
      test_labels = test[:,0]
      
      #print 'training: ', training_data.shape
      #print 'test    : ', test_data.shape
      
      classifier.train(training_labels, training_data)
      pred_labels = classifier.classify(test_data)

      for i, label_pred in enumerate(pred_labels):
         label_real = test_labels[i]
         ind_real = np.where(classes==label_real)
         ind_pred = np.where(classes==label_pred)
         confusion[ind_real, ind_pred] += 1
   
   s = np.sum(confusion,axis=1)
   percent = [100*confusion[i,i]/float(s[i]) for i in range(len(s))]
   avg = 100 * np.trace(confusion) / float(np.sum(confusion))
   
   return classes, confusion, percent, avg


def _inner_join(labels, profiles, keysize):
   for labelrow in labels:
      for profilerow in profiles:
         k1 = labelrow[1:]
         k2 = profilerow[:keysize]
         #print str(k1) + ' => ' + str(k2)
         if (all(k1==k2)):
            row = [labelrow[0]] + list(profilerow[keysize:])
            yield row

def cross_validation(labels_csvfile, profile_csvfile, classifier, K=10):
   '''
   - labels_csvfile's first column are the labels, following N columns are the key 
   - profile_csvfile N first column are considered to be the key, the remining column are the vector data values
   - First row (headers) in two files are ignored
   '''
      
   labels   = [row for row in csv.reader(open(labels_csvfile, "rb"))]
   profiles = [row for row in csv.reader(open(profile_csvfile, "rb"))]
   
   labels = np.array(labels)
   profiles = np.array(profiles)
   
   #print 'labels: ', labels.shape
   #print 'profiles:', profiles.shape
   
   # ignore header row
   labels = labels[1:,:]
   profiles = profiles[1:,:]
      
   keysize  = labels.shape[1] - 1
   cdata = np.array([row for row in _inner_join(labels, profiles, keysize)])
   
   classes, confusion, percent, avg = get_confusion_matrix(classifier, cdata, K)

   _display_as_text(classes, confusion, percent, avg, cdata.shape[0])
   _display_as_graph(classes, confusion, percent, avg)
   
def _display_as_text(classes, confusion, percent, avg, numprofiles):
   
   s = np.sum(confusion,axis=1)
   print 'Classifying %d profiles:' % numprofiles
   for i, v in enumerate(confusion):
      for u in v:
         print "%2d " % u ,
      print "(%02d)  %3d%%  %s " % (s[i],percent[i],classes[i])
   
   print 'Average: %3d%%' % avg


def _display_as_graph(classes, confusion, percent, avg):   
   # normalized figure
   
   s = np.sum(confusion,axis=1)
   norm_confusion = np.zeros((len(classes),len(classes)), dtype=np.float)
   for i, row in enumerate(confusion):
      for j, v in enumerate(row):
         norm_confusion[i,j] = v / float(s[i])
      
   fig = plt.figure()
   ax = fig.add_subplot(111)
   im = ax.imshow(norm_confusion, interpolation='nearest', cmap = mpl.cm.RdBu_r)

   ax.set_xticklabels([''])
   ax.set_yticklabels([''])
   
   # print categories
   xcoord = len(classes)
   ycoord = 0
   ticks = []
   for i in range(len(classes)):
      #ticks.append(yoffset)
      txt = "(%02d)  %3d%%  %s " % (s[i],percent[i],classes[i])
      ax.text(xcoord, ycoord, txt, transform=ax.transData, fontsize='small', verticalalignment='center', horizontalalignment='left')
      ycoord += 1
   
   plt.xticks([], [])
   plt.yticks(ticks, [])
   
   
   
   
   
   plt.draw()
   plt.show()
