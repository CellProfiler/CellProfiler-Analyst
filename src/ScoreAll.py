#!/usr/bin/env python
import wx
import os
import MulticlassSQL
import numpy
from DBConnect import *
from Properties import Properties
from DataModel import DataModel
from StringIO import StringIO
from TrainingSet import TrainingSet
from StringIO import StringIO
import FastGentleBoostingMulticlass
from DataGrid import DataGrid
import PolyaFit
import DirichletIntegrate

USAGE = '''
ABOUT:
This script will train a classifier for a given properties file and training set and output a table of counts.

USAGE:
python ScoreAll.py <propertiesfile> <trainingset>
'''

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print USAGE
        exit()

    props  = sys.argv[1]
    ts     = sys.argv[2]
    
    app = wx.PySimpleApp()
    
    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()
    
    print 'Loading properties file...'
    p.LoadFile(props)
    dm.PopulateModel()
    
    print 'Loading training set...'
    trainingSet = TrainingSet(p)
    trainingSet.Load(ts)
    
    nClasses = len(trainingSet.labels)

    nRules = int(raw_input('# of rules: '))
    assert 200 > nRules > 0, '# of rules must be between 1 and 200.  Value was %s'%(nRules,)
    filter = raw_input('Filter name (return for none): ')
    assert filter in p._filters.keys()+[''], 'Filter %s not found in properties file.  Valid filters are: %s'%(filter, p._filters.keys(),)
    group  = raw_input('Group name (return for none): ')
    assert group in p._groups.keys()+[''], 'Group %s not found in properties file.  Valid groups are: %s'%(group, p._groups.keys(),)
    if group=='':
        group = 'Image'
    
    if p.table_id:
        nKeyCols = 2
    else:
        nKeyCols = 1
    
    print ''
    print 'properties:  ', props
    print 'training set:', ts
    print '# rules:     ', nRules
    print 'filter:      ', filter
    print 'grouping by: ', group
    print ''
    
    output = StringIO()
    print 'Training classifier with '+str(nRules)+' rules...'
    weaklearners = FastGentleBoostingMulticlass.train(trainingSet.colnames,
                                                      nRules, trainingSet.label_matrix, 
                                                      trainingSet.values, output)
    def update(frac): print '%d%% complete'%(frac*100.,)
    keysAndCounts = MulticlassSQL.PerImageCounts(weaklearners, filter=(filter or None), cb=update)
    keysAndCounts.sort()
    print 'done.'
        
    if not keysAndCounts:
        print 'No images are in filter "%s". Please check the filter definition in your properties file.'%(filter)
        exit()
    
    # AGGREGATE PER_IMAGE COUNTS TO GROUPS IF NOT GROUPING BY IMAGE
    if group != 'Image':
        print 'Grouping %s counts by %s...' % (p.object_name[0], group)
        imData = {}
        for row in keysAndCounts:
            key = tuple(row[:nKeyCols])
            imData[key] = numpy.array([float(v) for v in row[nKeyCols:]])
        groupedKeysAndCounts = numpy.array([list(k)+vals.tolist() for k, vals in dm.SumToGroup(imData, group).items()], dtype=object)
        nKeyCols = len(dm.GetGroupColumnNames(group))
    else:
        groupedKeysAndCounts = numpy.array(keysAndCounts, dtype=object)
            
    # FIT THE BETA BINOMIAL
    print 'Fitting beta binomial distribution to data...'
    counts = groupedKeysAndCounts[:,-nClasses:]
    alpha, converged = PolyaFit.fit_betabinom_minka_alternating(counts)
    print '   alpha =', alpha, '   converged =', converged
    print '   alpha/Sum(alpha) = ', [a/sum(alpha) for a in alpha]
                
    # CONSTRUCT ARRAY OF TABLE DATA
    print 'Computing enrichment scores for each group...'
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
        scores = DirichletIntegrate.score(alpha, numpy.array(countsRow))       # compute enrichment probabilities of each class for this image OR group 
        tableRow += scores
        # Append the logit scores:
        # Special case: only calculate logit of "positives" for 2-classes
        if nClasses==2:
            tableRow += [numpy.log10(scores[0])-(numpy.log10(1-scores[0]))]   # compute logit of each probability
        else:
            tableRow += [numpy.log10(score)-(numpy.log10(1-score)) for score in scores]   # compute logit of each probability
        tableData.append(tableRow)
    tableData = numpy.array(tableData, dtype=object)
    print 'done.'
    
    # CREATE COLUMN LABELS LIST
    labels = []
    # if grouping isn't per-image, then get the group key column names.
    if group != 'Image':
        labels = dm.GetGroupColumnNames(group)
    else:
        if p.table_id:
            labels += [p.table_id]
        labels += [p.image_id]
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
    
    grid = DataGrid(tableData, labels, grouping=group,
                    key_col_indices=key_col_indices, title=title)
    grid.Show()
    
        
    app.MainLoop()
    