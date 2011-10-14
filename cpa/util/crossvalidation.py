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

def _k_fold_cross_validation_iterator(data, K=None):
   """
   Generates K (training, validation) pairs from the items in X. If K is unspecified it is set to a leave one out
   """
   if K == None:
      K = data.shape[0]

   np.random.shuffle(data)
   for k in xrange(K):
      training = np.array([x for i, x in enumerate(data) if i % K != k])
      validation = np.array([x for i, x in enumerate(data) if i % K == k])
      yield training, validation


def get_confusion_matrix(classifier, ckdata, keysize, K=None, exclude_subkey=None, include_subkey=None):
   '''   
   return classes, confusion, percent, avg, avgTotal
   
   compute a confusion matrix from the 'K'-fold validation of the 'classifier' on the 'cdata', cdata contains class labels in the first column
   '''
   #import pdb
   #pdb.set_trace()
   classes = np.sort(np.unique(ckdata[:,0]))
   numclasses = classes.shape[0]
   confusion = np.zeros((numclasses,numclasses), dtype=np.int)
   
   for training, test in _k_fold_cross_validation_iterator(ckdata, K):
      
      training_labels = training[:,0]
      training_keys = training[:,1:1+keysize]
      training_data   = training[:,1+keysize:]
      
      test_labels = test[:,0]
      test_keys = test[:,1:1+keysize]
      test_data   = test[:,1+keysize:]

      if exclude_subkey != None:
         if test_data.shape[0] > 1:
            print 'A group exclusion cannot be used for a k fold cross validation that is not a leave one out (K=%s)' % K
      
         training_exclude = training_keys[:,exclude_subkey]
         test_exclude = test_keys[0,exclude_subkey]
         if isinstance(exclude_subkey,int):
            indices = np.where([not row==test_exclude for row in training_exclude])[0]
         else:
            indices = np.where([not all(row==test_exclude) for row in training_exclude])[0]
         #import pdb
         #pdb.set_trace()
         
         if include_subkey != None:
            if test_data.shape[0] > 1:
               print 'A group inclusion cannot be used for a k fold cross validation that is not a leave one out (K=%s)' % K
         
            training_include = training_keys[:,include_subkey]
            test_include = test_keys[0,include_subkey]
            if isinstance(include_subkey,int):
               indices_include = np.where([row==test_include for row in training_include])[0]
            else:
               indices_include = np.where([all(row==test_include) for row in training_include])[0]
            #import pdb
            #pdb.set_trace()
            indices = np.union1d(indices, indices_include)
            
            
         training_data = training_data[indices]
         training_labels = training_labels[indices]

      
      classifier.train(training_labels, training_data)
      pred_labels = classifier.classify(test_data)

      for i, label_pred in enumerate(pred_labels):
         label_real = test_labels[i]
         ind_real = np.where(classes==label_real)
         ind_pred = np.where(classes==label_pred)
         confusion[ind_real, ind_pred] += 1
   
   s = np.sum(confusion,axis=1)
   percent = [100*confusion[i,i]/float(s[i]) for i in range(len(s))]
   avg = np.mean(percent)
   avgTotal = 100 * np.trace(confusion) / float(np.sum(confusion))
   
   return classes, confusion, percent, avg, avgTotal


def _inner_join(labels, profiles, keysize):
   for labelrow in labels:
      for profilerow in profiles:
         k1 = labelrow[1:]
         k2 = profilerow[:keysize]
         #print str(k1) + ' => ' + str(k2)
         if (all(k1==k2)):
            row = [labelrow[0]] + list(profilerow[:])
            yield row

def cross_validation(labels_csvfile, profile_csvfile, classifier, K=None, exclude_subkey=None, include_subkey=None, standardize=False):
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
   ckdata = np.array([row for row in _inner_join(labels, profiles, keysize)])
   
   # remove nan rows
   nan_row_indices = np.unique(np.where(ckdata == 'nan')[0])
   ckdata = np.delete(ckdata, nan_row_indices, axis=0)
   
   # standardize
   if standardize:
      ck = ckdata[:,:1+keysize]
      data = ckdata[:,1+keysize:].astype(float)
      m_data = np.mean(data, axis=0)
      s_data = np.std(data, axis=0)
      data = (data - m_data) / s_data 
      ckdata = np.hstack((ck,data))


   classes, confusion, percent, avg, avgTotal = get_confusion_matrix(classifier, ckdata, keysize, K, exclude_subkey, include_subkey)
   _display_as_text(classes, confusion, percent, avgTotal, ckdata.shape[0])
   _display_as_graph(classes, confusion, percent, avgTotal)
      
      
   ## subsampling loop
   #P = []
   #rate = []
   #for p in range(5,100,5):
      #np.random.shuffle(ckdata)
      #ckdata_sample = np.array([x for i, x in enumerate(ckdata) if i % 100/p == 0])
   
      #classes, confusion, percent, avg, avgTotal = get_confusion_matrix(classifier, ckdata_sample, keysize, K, exclude_subkey, include_subkey)
      #print '%d %d %d' % (p,avgTotal,ckdata_sample.shape[0])
      #P.append(p)
      #rate.append(avg)

      #_display_as_graph(classes, confusion, percent, avg, 'image_%s'%p)
    
   #fig = plt.figure()
   #plt.plot(P,rate)
   #plt.show()

def concentration_selection(compound1, compound2, compoundKeyIndex):
   return None
   
def _display_as_text(classes, confusion, percent, avg, numprofiles):
   
   s = np.sum(confusion,axis=1)
   print 'Classifying %d profiles:' % numprofiles
   for i, v in enumerate(confusion):
      for u in v:
         print "%2d " % u ,
      print "(%02d)  %3d%%  %s " % (s[i],percent[i],classes[i])
   
   print 'Average: %3d%%' % avg


def _display_as_graph(classes, confusion, percent, avg, filename=None):   
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
 
   #plt.draw()
   if filename != None:
      plt.savefig("%s.png"%filename, format='png')
   else:
      plt.show()
