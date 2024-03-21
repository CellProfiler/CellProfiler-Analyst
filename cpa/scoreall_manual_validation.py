#!/usr/bin/env python

from .dbconnect import *
from .datamodel import DataModel
from .properties import Properties
from io import StringIO, StringIO
from .trainingset import TrainingSet
from time import time
from . import dirichletintegrate
from . import fastgentleboostingmulticlass
from . import multiclasssql
from . import polyafit
import logging
import numpy as np
import os
import sys
import wx
import matplotlib.pyplot as plt
from sklearn import metrics
#import util.crossvalidation as xval

USAGE = '''
ABOUT:
This script will train a classifier for a given properties file and training
set and output a confusion matrix, indicating how well the classifier learned
from the initial trainingset (trainingset_initial) applies to a fresh, non-iterated
training set (trainingset_manual).

USAGE:
python scoreall_manual_validation.py <propertiesfile> <trainingset_initial> <trainingset_manual>

trainingset_initial = training set created by the traditional CPA iterative process
trainingset_manual = training set generated as a manual ground truth to test against CPA's classification 
'''
## per_cell_scores code copied from https://svn.broadinstitute.org/imaging/2007_05_16_HCS_AstraZeneca/src/boosting.py
## because it was not in this repository -- DL

DISPLAY_CONFUSION_MATRIX = 1

def per_cell_scores(learners, test, colnames):
    assert test.shape[1] == len(colnames)
    scores = np.zeros(len(test), dtype=float)
    for colname, thresh, a, b, expected_worst_margin in learners:
        try:
            col = colnames.index(colname)
        except ValueError:
            logging.warn('Skipping %s'%colname)
            continue
        above_threshold = np.array(test)[:,col] > thresh
        scores[above_threshold] += a[0]
        scores[np.logical_not(above_threshold)] += b[0]
    return scores

def score_objects(properties, ts, gt, nRules, filter_name=None, group='Image',
          show_results=False, results_table=None, overwrite=False):
    '''
    Trains a Classifier on a training set and scores the experiment
    returns the table of scores as a numpy array.
        
    properties    -- Properties instance
    ts            -- TrainingSet instance
    gt            -- Ground Truth instance
    nRules        -- number of rules to use
    filter_name   -- name of a filter to use from the properties file
    group         -- name of a group to use from the properties file
    show_results  -- whether or not to show the results in TableViewer
    results_table -- table name to save results to or None.
    '''
    
    p = properties
    #db = DBConnect() ## Removed writing to db.  Results_table should be 'None' anyway
    dm = DataModel()

    #if group == None:
        #group = 'Image'

    print('')
    print(('properties:    ', properties))
    print(('initial training set:  ', ts))
    print(('ground truth training set:  ', gt))
    print(('# rules:       ', nRules))
    print(('filter:        ', filter_name))
    print(('grouping by:   ', group))
    print(('show results:  ', show_results))
    print(('results table: ', results_table))
    print(('overwrite:     ', overwrite))
    print('')
            
    nClasses = len(ts.labels)
    nKeyCols = len(image_key_columns())
    
    assert 200 > nRules > 0, '# of rules must be between 1 and 200.  Value was %s'%(nRules,)
    assert filter_name in list(p._filters.keys())+[None], 'Filter %s not found in properties file.  Valid filters are: %s'%(filter_name, ','.join(list(p._filters.keys())),)
    assert group in list(p._groups.keys())+['Image', 'None'], 'Group %s not found in properties file.  Valid groups are: %s'%(group, ','.join(list(p._groups.keys())),)
    
    output = StringIO()
    logging.info('Training classifier with %s rules...'%nRules)
    t0 = time()
    weaklearners = fastgentleboostingmulticlass.train(ts.colnames,
                                                      nRules, ts.label_matrix, 
                                                      ts.values, output)
    logging.info('Training done in %f seconds'%(time()-t0))
    
    t0 = time()
    #def update(frac): 
        #logging.info('%d%% '%(frac*100.,))

    ## Score Ground Truth using established classifier
    gt_predicted_scores = per_cell_scores(weaklearners, gt.values, gt.colnames)
    #plt.hist(gt_predicted_scores)
    #plt.show()
    gt_predicted_signs = np.sign(gt_predicted_scores)
    
    
    ## Compare Ground Truth score signs with the actual ground truth values
    numclasses = ts.labels.size
    gt_actual_signs = gt.label_matrix[:,0]
    cm_unrotated = metrics.confusion_matrix(gt_actual_signs,gt_predicted_signs)
    ## sklearn.metrics.confusion_matrix -- 2D confusion matrix is inverted from convention.
    ## https://github.com/scikit-learn/scikit-learn/issues/1664
    cm = np.rot90(np.rot90(cm_unrotated))
    fpr, sens, thresholds = metrics.roc_curve(gt_actual_signs,gt_predicted_signs)
    spec = 1-fpr
    s = np.sum(cm,axis=1)
    percent = [100*cm[i,i]/float(s[i]) for i in range(len(s))]
    avg = np.mean(percent)
    avgTotal = 100 * np.trace(cm) / float(np.sum(cm))    
    print(('accuracy = %f' % avgTotal))
    print('Confusion Matrix = ... ')
    print(cm)
    my_sens = cm[0,0] / float(cm[0,0] + cm[0,1]) #TP/(TP+FN)
    my_spec = cm[1,1] / float(cm[1,1] + cm[1,0]) #TN/(TN+FP)
    print(('My_Sensitivity = %f' % my_sens))
    print(('My_Specificity = %f' % my_spec))
    print('Sensitivity = ...')
    print(sens)
    print('Specificity = ...')
    print(spec)
    print('Done calculating')
    
    ############
    ## Confusion Matrix code from here: http://stackoverflow.com/questions/5821125/how-to-plot-confusion-matrix-with-string-axis-rather-than-integer-in-python
    conf_arr = cm
    norm_conf = []
    ## This normalizes each *row* to the color map, but I chose to normalize the whole confusion matrix to the same scale
    ##for i in conf_arr:
        ##a = 0
        ##tmp_arr = []
        ##a = sum(i, 0)
        ##for j in i:
            ##tmp_arr.append(float(j)/float(a))
        ##norm_conf.append(tmp_arr)
    norm_conf = conf_arr / float(np.max(conf_arr))
    
    if DISPLAY_CONFUSION_MATRIX:
        fig = plt.figure()
        plt.clf()
        ax = fig.add_subplot(111)
        ax.set_aspect(1)
        res = ax.imshow(np.array(norm_conf), cmap=plt.cm.jet, 
                        interpolation='nearest')
        
        width = len(conf_arr)
        height = len(conf_arr[0])
        
        for x in range(width):
            for y in range(height):
                ax.annotate(str(conf_arr[x][y]), xy=(y, x), 
                            horizontalalignment='center',
                            verticalalignment='center')
        cb = fig.colorbar(res)
        #cb.set_cmap = [0,1]
        if width == 2 and height == 2:
            plt.xticks([0,1],['FP','TN'])
            plt.yticks([0,1],['TP','FP'])
        else:
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            plt.xticks(list(range(width)), alphabet[:width])
            plt.yticks(list(range(height)), alphabet[:height])
        plt.show()
            
    print('Done')
    #plt.savefig('confusion_matrix.png', format='png')    
######
#
# run
#
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) < 4:
        print(USAGE)
        sys.exit()

    props_file = sys.argv[1]
    ts_file    = sys.argv[2]
    gt_file    = sys.argv[3] # Ground Truth    
    
    app = wx.App()
    
    ## Set to 50, only for testing! 
    #nRules = int(raw_input('# of rules: '))
    nRules = 50
    
    ## I am removing this for now, since the only objects that
    ## will be classified are the ground truth set ("gt_file")
    #filter_name = raw_input('Filter name (return for none): ')
    #if filter_name == '':
        #filter_name = None
    filter_name = None
    
    ##
    #group = raw_input('Group name (return for none): ')
    #if group=='':
        #group = 'Image'
    group = 'None'
    
    ##
    #results_table = raw_input('Results table name (return for none): ')
    results_table = ''
    
    logging.info('Loading properties file...')
    p = Properties()
    p.LoadFile(props_file)
    logging.info('Loading initial training set...')
    ts = TrainingSet(p)
    ts.Load(ts_file)
    logging.info('Loading ground truth training set...')
    gt = TrainingSet(p)
    gt.Load(gt_file)
    
    score_objects(p, ts, gt, nRules, filter_name, group, show_results=True,
          results_table=results_table, overwrite=False)
    
    app.MainLoop()