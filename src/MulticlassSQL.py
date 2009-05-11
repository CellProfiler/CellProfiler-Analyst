import numpy
from DBConnect import *
from Properties import Properties
from DataModel import DataModel

db = DBConnect.getInstance()
p = Properties.getInstance()
dm = DataModel.getInstance()

temp_stump_table = "_stump"
temp_score_table = "_scores"
temp_class_table = "_class"
filter_table_prefix = '_filter_'

# filter & filterKeys is kind of redundant here, yet they are implemented
# very differently.  Should we only use filterKeys?
def translate(weaklearners, filter=None, filterKeys=[]):
    '''
    Translate weak learners into MySQL queries that place the resulting 
      classification in a MySQL temporary table named "temp_class_table"
    filter: if supplied, scoring will be limited to only imKeys within this
            filter
    filterKeys: (optional) A specific list of imKeys OR obKeys (NOT BOTH)
        to classify.
        * WARNING: If this list is too long, you may exceed the size limit to
          MySQL queries. 
        * Useful when fetching N objects from a particular class. Use the
          DataModel to get batches of random objects, and sift through them
          here until N objects of the desired class have been accumulated.
        * Also useful for classifying a specific image or group of images.
    '''
    
    num_features = len(weaklearners)
    nClasses = len(weaklearners[0][2])

    if p.table_id:
        key_col_defs = p.table_id+" INT, "+p.image_id+" INT, "+p.object_id+" INT, "
        index_cols = "%s, %s, %s"%(p.table_id, p.image_id, p.object_id)
    else:
        key_col_defs = p.image_id+" INT, "+p.object_id+" INT, "
        index_cols = "%s, %s"%(p.image_id, p.object_id)
        
    select_start = UniqueObjectClause()+', '
    filter_clause = ''
    if filter is not None:
        filter_clause = ', `%s` WHERE %s.%s=`%s`.%s '%(filter_table_prefix+filter, p.object_table, p.image_id, filter_table_prefix+filter, p.image_id)
        if p.table_id:
            filter_clause += 'AND %s.%s=`%s`.%s '%(p.object_table, p.table_id, filter_table_prefix+filter, p.table_id)
    
    # Create stump table (ob x nRules) <0/1>
    stump_cols             = select_start + ", ".join(["stump%d"%(i) for i in range(num_features)])
    stump_col_defs         = key_col_defs + ", ".join(["stump%d TINYINT"%(i) for i in range(num_features)])
    stump_select_features  = ", ".join(["(%s > %f) AS stump%d"%(wl[0], wl[1], idx) for idx, wl in enumerate(weaklearners)])
    stump_select_statement = UniqueObjectClause(p.object_table)+', ' + stump_select_features + " FROM " + p.object_table + filter_clause
    stump_stmnts = ['CREATE TEMPORARY TABLE %s (%s)'%(temp_stump_table, stump_col_defs),
                    'CREATE INDEX idx_%s ON %s (%s)'%(temp_stump_table, temp_stump_table, index_cols),
                    'INSERT INTO %s (%s) SELECT %s'%(temp_stump_table, stump_cols, stump_select_statement)]
    
    if filterKeys != []:
        isImKey = lambda(k): (p.table_id and len(k)==2) or (not p.table_id and len(k)==1)
        if isImKey(filterKeys[0]):
            stump_stmnts[2] += ' WHERE '+GetWhereClauseForImages(filterKeys)
        else:
            stump_stmnts[2] += ' WHERE '+GetWhereClauseForObjects(filterKeys)

    # Create class scores table (ob x classes) <float>
    classidxs          = range(1, nClasses+1)
    score_vals_columns = ["score%d"%(i) for i in classidxs]
    score_col_defs     = key_col_defs + ", ".join(["%s FLOAT"%(s) for s in score_vals_columns]) + ", score_greatest FLOAT"
    score_cols         = select_start + ", ".join(["%s"%(s) for s in score_vals_columns]) + ", score_greatest"
    # SQLite doesn't support conditional operators, so we use math instead:
    # Example: if (A>B), C, D ==> D+(C-D)*(A>B)
    score_select_scores = ", ".join(["+".join(["%f+(%f-(%f))*(stump%d)"
                                    %(weaklearners[i][3][k-1], weaklearners[i][2][k-1],weaklearners[i][3][k-1], i) 
                                    for i in range(num_features)]) + " AS score%d"%(k)
                                    for k in classidxs])
    score_select_statement = select_start + score_select_scores + ", 0.0 FROM " + temp_stump_table
    score_stmnts = ['CREATE TEMPORARY TABLE %s (%s)'%(temp_score_table, score_col_defs),
                    'CREATE INDEX idx_%s ON %s (%s)'%(temp_score_table, temp_score_table, index_cols),
                    'INSERT INTO %s (%s) SELECT %s'%(temp_score_table, score_cols, score_select_statement )]
    
    # Create maximum column in class scores table
    greatest_expr = "GREATEST(" + ", ".join(score_vals_columns) + ")"
    find_max_query = "UPDATE %s SET score_greatest = %s"%(temp_score_table, greatest_expr)

    # Convert to class membership table (ob x classes) <T/F>
    class_cols            = select_start + ", ".join(["class%d"%(k) for k in classidxs])
    class_col_defs        = key_col_defs + ", ".join(["class%d TINYINT"%(k) for k in classidxs])
    select_class_greatest = ", ".join(["%s = score_greatest AS class%d"%(sc, k) for sc,k in zip(score_vals_columns, classidxs)])
    class_select_statement = select_start + select_class_greatest + " FROM " + temp_score_table
    class_stmnts = ['CREATE TEMPORARY TABLE %s (%s)'%(temp_class_table, class_col_defs),
                    'CREATE INDEX idx_%s ON %s (%s)'%(temp_class_table, temp_class_table, index_cols),
                    'INSERT INTO %s (%s) SELECT %s'%(temp_class_table, class_cols, class_select_statement)]

    return stump_stmnts, score_stmnts, find_max_query, class_stmnts


def GetCountQuery(nClasses):
    classidxs = range(1, nClasses+1)
    # Get hit counts
    count_query = 'SELECT %s, %s FROM %s GROUP BY %s' % \
                    (UniqueImageClause(), 
                    ", ".join(["SUM(class%d)"%(k) for k in classidxs]),
                    temp_class_table, UniqueImageClause())
    return count_query


def CreateFilterTables():
    ''' Creates a temporary with image keys for each filter. '''
    if p.table_id:
        key_col_defs = p.table_id+" INT, "+p.image_id+" INT"
        index_cols = "%s, %s"%(p.table_id, p.image_id)
    else:
        key_col_defs = p.image_id+" INT"
        index_cols = "%s"%(p.image_id)
        
    for name, query in p._filters.items():
        db.Execute('DROP TABLE IF EXISTS `%s`'%(filter_table_prefix+name))
        db.Execute('CREATE TEMPORARY TABLE `%s` (%s)'%(filter_table_prefix+name, key_col_defs))
        db.Execute('CREATE INDEX `idx_%s` ON `%s` (%s)'%(filter_table_prefix+name, filter_table_prefix+name, index_cols))
        db.Execute('INSERT INTO `%s` (%s) %s'%(filter_table_prefix+name, index_cols, query))
        

def GetAreaSumsQuery(nClasses, filter=None):
    classidxs = range(1, nClasses+1)
    # handle area-based scoring if needed, replacing count query
    if p.area_scoring_column:
        table_match = ''
        if p.table_id:
            table_match = '%s.%s = %s.%s AND '%(p.object_table, p.table_id, temp_class_table, p.table_id)
        image_match = '%s.%s = %s.%s AND '%(p.object_table, p.image_id, temp_class_table, p.image_id)
        object_match = '%s.%s = %s.%s'%(p.object_table, p.object_id, temp_class_table, p.object_id)
        object_match_clauses = table_match + image_match + object_match
        
        return 'SELECT %s, %s FROM %s, %s WHERE %s GROUP BY %s' % \
                (UniqueImageClause(p.object_table), 
                 ", ".join(["SUM(%s.class%d * %s.%s)"%(temp_class_table, k, p.object_table, p.area_scoring_column) for k in classidxs]),
                 temp_class_table, p.object_table,
                 object_match_clauses,
                 UniqueImageClause(p.object_table))
    

def FilterObjectsFromClassN(clNum, weaklearners, filterKeys):
    '''
    clNum: 1-based index of the class to retrieve obKeys from
    weaklearners: Weak learners from FastGentleBoostingMulticlass.train
    filterKeys: (optional) A specific list of imKeys OR obKeys (NOT BOTH)
        to classify.
        * WARNING: If this list is too long, you may exceed the size limit to
          MySQL queries. 
        * Useful when fetching N objects from a particular class. Use the
          DataModel to get batches of random objects, and sift through them
          here until N objects of the desired class have been accumulated.
        * Also useful for classifying a specific image or group of images.
    RETURNS: A list of object keys that fall in the specified class,
        if Properties.area_scoring_column is specified, area sums are also
        reported for each class
    '''
    stump_stmnts, score_stmnts, find_max_query, _ = translate(weaklearners, filterKeys=filterKeys)

    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    [db.Execute(stump_query) for stump_query in stump_stmnts] 
    [db.Execute(score_query) for score_query in score_stmnts]
    db.Execute(find_max_query)
    db.Execute('SELECT '+UniqueObjectClause()+' FROM _scores WHERE score'+str(clNum)+'=score_greatest')
    return db.GetResultsAsList()
    
    
def PerImageCounts(weaklearners, filter=None, cb=None):
    '''
    weaklearners: Weak learners from FastGentleBoostingMulticlass.train
    filter: name of filter, or None.
    cb: callback function to update with the fraction complete
    RETURNS: A list of lists of imKeys and respective object counts for each class:
        Note that the imKeys are exploded so each row is of the form:
        [TableNumber, ImageNumber, Class1_ObjectCount, Class2_ObjectCount,...]
        where TableNumber is only present if table_id is defined in Properties. 
    '''
    nClasses = len(weaklearners[0][2])
    stump_stmnts, score_stmnts, find_max_query, class_stmnts = translate(weaklearners, filter=filter)
    count_query = GetCountQuery(nClasses)
    
    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    db.Execute('DROP TABLE IF EXISTS _class')

    if cb:
        imkeys = dm.GetAllImageKeys()
        imkeys.sort()
        stepsize = max(len(imkeys) / 100, 50)
        key_thresholds  = imkeys[-1:1:-stepsize]
        key_thresholds.reverse()
        if p.table_id:
            # split each table independently
            def splitter():
                yield " WHERE (%s = %d) AND (%s <= %d)"%(p.table_id, key_thresholds[0][0], p.image_id, key_thresholds[0][1])
                for lo, hi in zip(key_thresholds[:-1], key_thresholds[1:]):
                    if lo[0] == hi[0]:
                        yield " WHERE (%s = %d) AND (%s > %d) AND (%s <= %d)"%(p.table_id, lo[0], p.image_id, lo[1], p.image_id, hi[1])
                    else:
                        yield " WHERE (%s = %d) AND (%s > %d)"%(p.table_id, lo[0], p.image_id, lo[1])
                        yield " WHERE (%s = %d) AND (%s <= %d)"%(p.table_id, hi[0], p.image_id, hi[1])
            where_clauses = list(splitter())

        else:
            where_clauses = ([" WHERE (%s <= %d)"%(p.image_id, key_thresholds[0][0])] + 
                             [" WHERE (%s > %d) AND (%s <= %d)"
                              %(p.image_id, lo[0], p.image_id, hi[0]) 
                              for lo, hi in zip(key_thresholds[:-1], key_thresholds[1:])])
        num_clauses = len(where_clauses)
        num_steps = 3 * num_clauses

    def do_by_steps(query, stepnum):
        if cb:
            for idx, wc in enumerate(where_clauses):
                db.Execute(query +  wc, silent=(idx > 0))
                cb(min(1, (idx + stepnum * num_clauses)/float(num_steps)))
        else:
            db.Execute(query)

    db.Execute(stump_stmnts[0])
    db.Execute(stump_stmnts[1])
    do_by_steps(stump_stmnts[2], 0)
    db.Execute(score_stmnts[0])
    db.Execute(score_stmnts[1])
    do_by_steps(score_stmnts[2], 1)
    db.Execute(find_max_query)
    db.Execute(class_stmnts[0])
    db.Execute(class_stmnts[1])
    do_by_steps(class_stmnts[2], 2)
    db.Execute(count_query)
    keysAndCounts = db.GetResultsAsList()
    
    if p.area_scoring_column is not None:
        area_sums_query = GetAreaSumsQuery(nClasses, filter)
        db.Execute(area_sums_query)
        keysAndAreas = db.GetResultsAsList()
        keysAndAreas.sort()
        keysAndCounts.sort()
        # append areas
        for i in xrange(len(keysAndCounts)):
            keysAndCounts[i] += keysAndAreas[i][-nClasses:]
    
    # Add in images with zero object count that the queries missed
    for imKey, obCount in dm.GetImageKeysAndObjectCounts(filter):
        if obCount == 0:
            if p.area_scoring_column is not None:
                keysAndCounts += [list(imKey) + [0 for c in range(nClasses*2)]]
            else:
                keysAndCounts += [list(imKey) + [0 for c in range(nClasses)]]

    return [list(row) for row in keysAndCounts] 


if __name__ == "__main__":
#    dir = "/Users/ljosa/research/modifier/piyush"
#    p.LoadFile("%s/batch1and2.properties"%(dir,))
#    import cPickle as pickle
#    f = open("%s/batch1and2.boostingclassifier"%(dir,))
#    learners = pickle.load(f)
#    f.close()
#
#    keys_and_counts = PerImageCounts(learners, filter='HRG')
#    import numpy
#    keys_and_counts = numpy.array(keys_and_counts, dtype='i4')
#    print keys_and_counts[0,:]
#    print sum(keys_and_counts[:,-2:])

    from TrainingSet import TrainingSet
    from StringIO import StringIO
    import FastGentleBoostingMulticlass
    from DataGrid import DataGrid
    import wx
    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()
    
#    props = '/Volumes/imaging_analysis/2007_10_19_Gilliland_LeukemiaScreens/Screen3_1Apr09_run3/2007_10_19_Gilliland_LeukemiaScreens_Validation_v2_AllBatches_DuplicatesFiltered_FullBarcode_testSinglePlate.properties'
#    ts = '/Volumes/imaging_analysis/2007_10_19_Gilliland_LeukemiaScreens/Screen3_1Apr09_run3/trainingvalidation3b.txt'
    props = '../Properties/nirht_area_test.properties'
    ts = '/Users/afraser/Desktop/MyTrainingSet3.txt'
    nRules = 5
    filter = 'MAPs'
#    props = '/Users/afraser/Desktop/2007_10_19_Gilliland_LeukemiaScreens_Validation_v2_AllBatches_DuplicatesFiltered_FullBarcode.properties'
#    ts = '/Users/afraser/Desktop/trainingvalidation3d.txt'
#    nRules = 50
#    filter = 'afraser_test'
    
    p.LoadFile(props)
    dm.PopulateModel()
    trainingSet = TrainingSet(p)
    trainingSet.Load(ts)
    output = StringIO()
    print 'Training classifier with '+str(nRules)+' rules...'
    weaklearners = FastGentleBoostingMulticlass.train(trainingSet.colnames,
                                                      nRules, trainingSet.label_matrix, 
                                                      trainingSet.values, output)
    table = PerImageCounts(weaklearners, filter=filter)
    table.sort()

    labels = ['table', 'image'] + list(trainingSet.labels) + list(trainingSet.labels)
    print labels
    print table[0]

    app = wx.PySimpleApp()
    grid = DataGrid(numpy.array(table), labels, key_col_indices=[0,1])
    grid.Show()

    app.MainLoop()
    