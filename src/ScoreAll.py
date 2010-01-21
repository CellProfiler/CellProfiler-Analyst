#!/usr/bin/env python
from DBConnect import *
from DataGrid import DataGrid
from DataModel import DataModel
from Properties import Properties
from StringIO import StringIO, StringIO
from TrainingSet import TrainingSet
from time import time
import DirichletIntegrate
import FastGentleBoostingMulticlass
import MulticlassSQL
import PolyaFit
import logging
import numpy as np
import os
import sys
import wx

USAGE = '''
ABOUT:
This script will train a classifier for a given properties file and training set and output a table of counts.

USAGE:
python ScoreAll.py <propertiesfile> <trainingset>
'''


def score(props, ts, nRules, filter=None, group='Image'):
    '''
    Trains a Classifier on a training set and scores the experiment
    returns the loaded training set and a DataGrid of scores 
        
    props -- properties file
    ts -- training set
    nRules -- number of rules 
    filter -- name of a filter to use from the properties file
    group -- name of a group to use from the properties file 
    '''
    
    if group == None:
        group = 'Image'

    print ''
    print 'properties:  ', props
    print 'training set:', ts
    print '# rules:     ', nRules
    print 'filter:      ', filter
    print 'grouping by: ', group
    print ''
        
    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()

    logging.info('Loading properties file...')
    p.LoadFile(props)
    
    logging.info('Loading training set...')
    trainingSet = TrainingSet(p)
    trainingSet.Load(ts)
    
    nClasses = len(trainingSet.labels)
    nKeyCols = len(image_key_columns())
    
    
    assert 200 > nRules > 0, '# of rules must be between 1 and 200.  Value was %s'%(nRules,)
    assert filter in p._filters.keys()+[None], 'Filter %s not found in properties file.  Valid filters are: %s'%(filter, p._filters.keys(),)
    assert group in p._groups.keys()+['Image'], 'Group %s not found in properties file.  Valid groups are: %s'%(group, p._groups.keys(),)
    
    logging.info('Creating tables for filters...')
    MulticlassSQL.CreateFilterTables()
    
    output = StringIO()
    logging.info('Training classifier with %s rules...'%nRules)
    t0 = time()
    weaklearners = FastGentleBoostingMulticlass.train(trainingSet.colnames,
                                                      nRules, trainingSet.label_matrix, 
                                                      trainingSet.values, output)
    logging.info('Training done in %f seconds'%(time()-t0))
    
    logging.info('Computing per-image class counts...')
    t0 = time()
    def update(frac): 
        logging.info('%d%% '%(frac*100.,))
    keysAndCounts = MulticlassSQL.PerImageCounts(weaklearners, filter=(filter or None), cb=update)
    keysAndCounts.sort()
    logging.info('Counts found in %f seconds'%(time()-t0))
        
    if not keysAndCounts:
        logging.error('No images are in filter "%s". Please check the filter definition in your properties file.'%(filter))
        raise Exception('No images are in filter "%s". Please check the filter definition in your properties file.'%(filter))
        
    # AGGREGATE PER_IMAGE COUNTS TO GROUPS IF NOT GROUPING BY IMAGE
    if group != 'Image':
        logging.info('Grouping %s counts by %s...' % (p.object_name[0], group))
        t0 = time()
        imData = {}
        for row in keysAndCounts:
            key = tuple(row[:nKeyCols])
            imData[key] = np.array([float(v) for v in row[nKeyCols:]])
        
        groupedKeysAndCounts = np.array([list(k)+vals.tolist() for k, vals in dm.SumToGroup(imData, group).items()], dtype=object)
        nKeyCols = len(dm.GetGroupColumnNames(group))
        logging.info('Grouping done in %f seconds'%(time()-t0))
    else:
        groupedKeysAndCounts = np.array(keysAndCounts, dtype=object)
    
    # FIT THE BETA BINOMIAL
    logging.info('Fitting beta binomial distribution to data...')
    counts = groupedKeysAndCounts[:,-nClasses:]
    alpha, converged = PolyaFit.fit_betabinom_minka_alternating(counts)
    logging.info('   alpha = %s   converged = %s'%(alpha, converged))
    logging.info('   alpha/Sum(alpha) = %s'%([a/sum(alpha) for a in alpha]))
                
    # CONSTRUCT ARRAY OF TABLE DATA
    logging.info('Computing enrichment scores for each group...')
    t0 = time()
    tableData = []
    for i, row in enumerate(groupedKeysAndCounts):
        # Start this row with the group key: 
        tableRow = list(row[:nKeyCols])
        
        if group != 'Image':
            tableRow += [len(dm.GetImagesInGroup(group, tuple(row[:nKeyCols])))]
        # Append the counts:
        countsRow = [int(v) for v in row[nKeyCols:nKeyCols+nClasses]]
        tableRow += [sum(countsRow)]
        tableRow += countsRow
        if p.area_scoring_column is not None:
            # Append the areas
            countsRow = [int(v) for v in row[-nClasses:]]
            tableRow += [sum(countsRow)]
            tableRow += countsRow
            
        # Append the scores:
        #   compute enrichment probabilities of each class for this image OR group
        scores = np.array( DirichletIntegrate.score(alpha, np.array(countsRow)) )
        #   clamp to [0,1] to 
        scores[scores>1.] = 1.
        scores[scores<0.] = 0.
        tableRow += scores.tolist()
        # Append the logit scores:
        #   Special case: only calculate logit of "positives" for 2-classes
        if nClasses==2:
            tableRow += [np.log10(scores[0])-(np.log10(1-scores[0]))]   # compute logit of each probability
        else:
            tableRow += [np.log10(score)-(np.log10(1-score)) for score in scores]   # compute logit of each probability
        tableData.append(tableRow)
    tableData = np.array(tableData, dtype=object)
    logging.info('Enrichments computed in %f seconds'%(time()-t0))
    
    # CREATE COLUMN LABELS LIST
    # if grouping isn't per-image, then get the group key column names.
    if group != 'Image':
        labels = dm.GetGroupColumnNames(group)
    else:
        labels = list(image_key_columns())

    # record the column indices for the keys
    key_col_indices = [i for i in range(len(labels))]
    
    if group != 'Image':
        labels += ['# Images']
    labels += ['Total %s Count'%(p.object_name[0].capitalize())]
    for i in xrange(nClasses):
        labels += ['%s %s Count'%(trainingSet.labels[i].capitalize(), p.object_name[0].capitalize())]
    if p.area_scoring_column is not None:
        labels += ['Total %s Area'%(p.object_name[0].capitalize())]
        for i in xrange(nClasses):
            labels += ['%s %s Area'%(trainingSet.labels[i].capitalize(), p.object_name[0].capitalize())]
    for i in xrange(nClasses):
        labels += ['p(Enriched)\n'+trainingSet.labels[i]]
    if nClasses==2:
        labels += ['Enriched Score\n'+trainingSet.labels[0]]
    else:
        for i in xrange(nClasses):
            labels += ['Enriched Score\n'+trainingSet.labels[i]]

    title = "Enrichments grouped by %s"%(group,)
    if filter:
        title += " filtered by %s"%(filter,)
    title += ' (%s)'%(os.path.split(p._filename)[1])
    
    return (
            trainingSet,
            DataGrid(tableData, labels, grouping=group, key_col_indices=key_col_indices, title=title)
            )



#
# run
#
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) < 3:
        print USAGE
        sys.exit()

    props  = sys.argv[1]
    ts     = sys.argv[2]
    
    app = wx.PySimpleApp()
    
    nRules = int(raw_input('# of rules: '))
    
    filter = raw_input('Filter name (return for none): ')
    if filter == '':
        filter = None
    
    group  = raw_input('Group name (return for none): ')
    if group=='':
        group = 'Image'
    
    grid = score(props, ts, nRules, filter, group)[1]
    grid.Show()
    
    app.MainLoop()
    

