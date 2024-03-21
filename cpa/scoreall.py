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

USAGE = '''
ABOUT:
This script will train a classifier for a given properties file and training
set and output a results table. You can also use it to write directly to a
database table.

USAGE:
python scoreall.py <propertiesfile> <trainingset>
'''

def score(properties, ts, nRules, filter_name=None, group='Image',
          show_results=False, results_table=None, overwrite=False):
    '''
    Trains a Classifier on a training set and scores the experiment
    returns the table of scores as a numpy array.
        
    properties    -- Properties instance
    ts            -- TrainingSet instance
    nRules        -- number of rules to use
    filter_name   -- name of a filter to use from the properties file
    group         -- name of a group to use from the properties file
    show_results  -- whether or not to show the results in TableViewer
    results_table -- table name to save results to or None.
    '''
    
    p = properties
    db = DBConnect()
    dm = DataModel()

    if group == None:
        group = 'Image'
        
    if results_table:
        if db.table_exists(results_table) and not overwrite:
            print(('Table "%s" already exists. Delete this table before running scoreall.'%(results_table)))
            return None

    print('')
    print(('properties:    ', properties))
    print(('training set:  ', ts))
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
    assert group in list(p._groups.keys())+['Image'], 'Group %s not found in properties file.  Valid groups are: %s'%(group, ','.join(list(p._groups.keys())),)
    
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
        
        groupedKeysAndCounts = np.array([list(k)+vals.tolist() for k, vals in list(dm.SumToGroup(imData, group).items())], dtype=object)
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
        colnames = dm.GetGroupColumnNames(group)
    else:
        colnames = list(image_key_columns())

    # record the column indices for the keys
    key_col_indices = [i for i in range(len(colnames))]
    
    if group != 'Image':
        colnames += ['Number_of_Images']
    colnames += ['Total_%s_Count'%(p.object_name[0].capitalize())]
    for i in range(nClasses):
        colnames += ['%s_%s_Count'%(ts.labels[i].capitalize(), p.object_name[0].capitalize())]
    if p.area_scoring_column is not None:
        colnames += ['Total_%s_Area'%(p.object_name[0].capitalize())]
        for i in range(nClasses):
            colnames += ['%s_%s_Area'%(ts.labels[i].capitalize(), p.object_name[0].capitalize())]
    for i in range(nClasses):
        colnames += ['pEnriched_%s'%(ts.labels[i])]
    if nClasses==2:
        colnames += ['Enriched_Score_%s'%(ts.labels[0])]
    else:
        for i in range(nClasses):
            colnames += ['Enriched_Score_%s'%(ts.labels[i])]

    title = results_table or "Enrichments_per_%s"%(group,)
    if filter_name:
        title += "_filtered_by_%s"%(filter_name,)
    title += ' (%s)'%(os.path.split(p._filename)[1])
    
    if results_table:
        print(('Creating table %s'%(results_table)))
        success = db.CreateTableFromData(tableData, colnames, results_table, temporary=False)
        if not success:
            print('Failed to create results table :(')
    
    if show_results:
        from . import tableviewer
        tableview = tableviewer.TableViewer(None, title=title)
        if results_table and overwrite:
            tableview.load_db_table(results_table)
        else:
            tableview.table_from_array(tableData, colnames, group, key_col_indices)
        tableview.set_fitted_col_widths()
        tableview.Show()
    return tableData



#
# run
#
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit()

    props_file = sys.argv[1]
    ts_file    = sys.argv[2]
    
    app = wx.App()
    
    nRules = int(eval(input('# of rules: ')))
    
    filter_name = eval(input('Filter name (return for none): '))
    if filter_name == '':
        filter_name = None
    
    group = eval(input('Group name (return for none): '))
    if group=='':
        group = 'Image'
        
    results_table = eval(input('Results table name (return for none): '))

    logging.info('Loading properties file...')
    p = Properties()
    p.LoadFile(props_file)
    logging.info('Loading training set...')
    ts = TrainingSet(p)
    ts.Load(ts_file)

    score(p, ts, nRules, filter_name, group, show_results=True,
          results_table=results_table, overwrite=False)
    
    app.MainLoop()
    
    #
    # Kill the Java VM
    #
    try:
        import javabridge
        javabridge.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print("Caught exception while killing VM")
