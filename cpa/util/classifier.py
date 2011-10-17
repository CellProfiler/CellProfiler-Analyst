#!/usr/bin/env python

'''
Classifier 

'''

import sys
import numpy as np


class Classifier(object):
   
   def train(self, labels, data):
      '''Train the classifier'''
      raise NotImplementedError( "Should have implemented this" )

   def classify(self, data):
      '''Return a vector containing predicted labels'''
      raise NotImplementedError( "Should have implemented this" )

def opposite_cosine_similarity(a, b):
      return - np.dot(a,b) / (np.sqrt(np.dot(a,a) * np.dot(b,b)))


class KNearestNeighborClassifier(Classifier):
   '''
   - the default 'metric' used is the opposite of the cosine similarirty
   - the defaut value of K is 1
   '''

   def __init__(self, K=1, distance=opposite_cosine_similarity):
      self.K = K
      self.distance = distance
   
   def train(self, labels, data):
      '''Train the classifier'''
      self.labels = np.array(labels)
      self.data = np.array(data).astype(float)

   def classify(self, data):
      '''Return a vector containing predicted labels'''
      data  = np.array(data).astype(float) 
      predicted_labels = []
      for x in data:
         predicted_labels.append(self._NN(x))
      return np.array(predicted_labels)
         

   def _NN(self, x):
      dist = []
      for i, y in enumerate(self.data):
         if(all(y == x)): # should never happen in k-fold validation
            print 'KNearestNeighborClassifier: how come this happened ??!! sum -> ', 
            print np.sum(x)
         else:
            dist.append((self.distance(x,y),self.labels[i]))

      dist.sort()
      dist = dist[0:min(self.K, len(dist))]
      keys = np.unique(np.array(dist)[:,1])      
      scores = dict(zip(keys, np.zeros(self.K,dtype=np.int)))
      
      for v in dist:
         scores[v[1]] += v[0]*v[0]

      return max(scores, key=scores.get)

