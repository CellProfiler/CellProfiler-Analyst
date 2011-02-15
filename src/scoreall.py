#!/usr/bin/env python
from dbconnect import *
from datatable import DataGrid
from datamodel import DataModel
from properties import Properties
from StringIO import StringIO, StringIO
from trainingset import TrainingSet
from time import time
import dirichletintegrate
import fastgentleboostingmulticlass
import multiclasssql
import polyafit
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

def score(properties, ts, nRules, filter_name=None, group='Image', show_results=False):
    '''
    Trains a Classifier on a training set and scores the experiment
    returns the loaded training set and a DataGrid of scores 
        
    properties -- Properties instance
    ts         -- TrainingSet instance
    nRules     -- number of rules to use
    filter     -- name of a filter to use from the properties file
    group      -- name of a group to use from the properties file 
    '''
    
    if group == None:
        group = 'Image'

    print ''
    print 'properties:  ', properties
    print 'training set:', ts
    print '# rules:     ', nRules
    print 'filter:      ', filter_name
    print 'grouping by: ', group
    print ''
        
    p = properties
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()
    
    nClasses = len(ts.labels)
    nKeyCols = len(image_key_columns())
    
    assert 200 > nRules > 0, '# of rules must be between 1 and 200.  Value was %s'%(nRules,)
    assert filter_name in p._filters.keys()+[None], 'Filter %s not found in properties file.  Valid filters are: %s'%(filter_name, ','.join(p._filters.keys()),)
    assert group in p._groups.keys()+['Image'], 'Group %s not found in properties file.  Valid groups are: %s'%(group, ','.join(p._groups.keys()),)
    
    output = StringIO()
    logging.info('Training classifier with %s rules...'%nRules)
    t0 = time()
    weaklearners = fastgentleboostingmulticlass.train(ts.colnames,
                                                      nRules, ts.label_matrix, 
                                                      ts.values, output)
    logging.info('Training done in %f seconds'%(time()-t0))
    
    logging.info('Computing per-image class counts...')
    t0 = time()
    def update(frac): 
        logging.info('%d%% '%(frac*100.,))
    keysAndCounts = multiclasssql.PerImageCounts(weaklearners, filter_name=(filter_name or None), cb=update)
    keysAndCounts.sort()
    logging.info('Counts found in %f seconds'%(time()-t0))
        
    if not keysAndCounts:
        logging.error('No images are in filter "%s". Please check the filter definition in your properties file.'%(filter_name))
        raise Exception('No images are in filter "%s". Please check the filter definition in your properties file.'%(filter_name))
        
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
    alpha, converged = polyafit.fit_betabinom_minka_alternating(counts)
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
        scores = np.array( dirichletintegrate.score(alpha, np.array(countsRow)) )
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
        labels += ['%s %s Count'%(ts.labels[i].capitalize(), p.object_name[0].capitalize())]
    if p.area_scoring_column is not None:
        labels += ['Total %s Area'%(p.object_name[0].capitalize())]
        for i in xrange(nClasses):
            labels += ['%s %s Area'%(ts.labels[i].capitalize(), p.object_name[0].capitalize())]
    for i in xrange(nClasses):
        labels += ['p(Enriched)\n'+ts.labels[i]]
    if nClasses==2:
        labels += ['Enriched Score\n'+ts.labels[0]]
    else:
        for i in xrange(nClasses):
            labels += ['Enriched Score\n'+ts.labels[i]]

    title = "Enrichments grouped by %s"%(group,)
    if filter_name:
        title += " filtered by %s"%(filter_name,)
    title += ' (%s)'%(os.path.split(p._filename)[1])
    
    if show_results:
        import tableviewer
        grid = tableviewer.TableViewer(None, title=title)
        grid.table_from_array(tableData, labels, group, key_col_indices)
        grid.set_fitted_col_widths()
        grid.Show()
    return tableData



#
# run
#
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) < 3:
        print USAGE
        sys.exit()

    props_file = sys.argv[1]
    ts_file    = sys.argv[2]
    
    app = wx.PySimpleApp()
    
    nRules = int(raw_input('# of rules: '))
    
    filter_name = raw_input('Filter name (return for none): ')
    if filter_name == '':
        filter_name = None
    
    group  = raw_input('Group name (return for none): ')
    if group=='':
        group = 'Image'

    logging.info('Loading properties file...')
    p = Properties.getInstance()
    p.LoadFile(props_file)
    logging.info('Loading training set...')
    ts = TrainingSet(p)
    ts.Load(ts_file)

    score(p, ts, nRules, filter_name, group, show_results=True)
    
    app.MainLoop()
    
