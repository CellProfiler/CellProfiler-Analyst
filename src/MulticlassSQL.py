import numpy
from DBConnect import *
from Properties import Properties
from DataModel import DataModel


db = DBConnect.getInstance()
p = Properties.getInstance()
dm = DataModel.getInstance()


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
    num_classes = len(weaklearners[0][2])

    if p.table_id:
        key_col_defs = p.table_id+" INT, "+p.image_id+" INT, "+p.object_id+" INT, "
        index_cols = "%s, %s"%(p.table_id, p.image_id)
    else:
        key_col_defs = p.image_id+" INT, "+p.object_id+" INT, "
        index_cols = "%s"%(p.image_id)
        
    select_start = UniqueObjectClause()+', '

    # If a filter is specified, use it as a subquery; otherwise, just
    # use the object table.
    if filter is None:
        object_table_name = p.object_table
        object_table_from = p.object_table
    else:
        object_table_name = filter
        object_table_from = ("(%s) as %s JOIN %s using (%s)"%
                             (p._filters[filter], filter, p.object_table,
                              ", ".join(image_key_columns())))
    
    # Create stump table (ob x nRules) <0/1>
    temp_stump_table       = "_stump"
    stump_cols             = select_start + ", ".join(["stump%d"%(i) for i in range(num_features)])
    stump_col_defs         = key_col_defs + ", ".join(["stump%d TINYINT"%(i) for i in range(num_features)])
    stump_select_features  = ", ".join(["(%s > %f) AS stump%d"%(wl[0], wl[1], idx) for idx, wl in enumerate(weaklearners)])
    stump_select_statement = select_start + stump_select_features + \
                             " FROM " + object_table_from
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
    classidxs          = range(1, num_classes+1)
    temp_score_table   = "_scores"
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
    score_stmnts = ['CREATE TEMPORARY TABLE %(temp_score_table)s (%(score_col_defs)s)'%(locals()),
                    'CREATE INDEX idx_%s ON %s (%s)'%(temp_score_table, temp_score_table, index_cols),
                    'INSERT INTO %s (%s) SELECT %s'%(temp_score_table, score_cols, score_select_statement )]
    
    # Create maximum column in class scores table
    greatest_expr = "GREATEST(" + ", ".join(score_vals_columns) + ")"
    find_max_query = "UPDATE %(temp_score_table)s SET score_greatest = %(greatest_expr)s"%(locals())

    # Convert to class membership table (ob x classes) <T/F>
    temp_class_table      = "_class"
    class_cols            = select_start + ", ".join(["class%d"%(k) for k in classidxs])
    class_col_defs        = key_col_defs + ", ".join(["class%d TINYINT"%(k) for k in classidxs])
    select_class_greatest = ", ".join(["%s = score_greatest AS class%d"%(sc, k) for sc,k in zip(score_vals_columns, classidxs)])
    class_select_statement = select_start + select_class_greatest + " FROM " + temp_score_table
    class_stmnts = ['CREATE TEMPORARY TABLE %s (%s)'%(temp_class_table, class_col_defs),
                    'INSERT INTO %s (%s) SELECT %s'%(temp_class_table, class_cols, class_select_statement)]


    # Get hit counts
    count_query = 'SELECT %s, %s FROM %s GROUP BY %s' % \
                        (UniqueImageClause(), 
                         ", ".join(["SUM(class%d)"%(k) for k in classidxs]),
                         temp_class_table, UniqueImageClause())

    # handle area-based scoring if needed, replacing count query
    if p.area_scoring_column:
        table_match = ''
        if p.table_id:
            table_match = '%s.%s = %s.%s AND '%(object_table_name, p.table_id,
                                                temp_class_table, p.table_id)
        image_match = '%s.%s = %s.%s AND '%(object_table_name, p.image_id,
                                            temp_class_table, p.image_id)
        object_match = '%s.%s = %s.%s'%(object_table_name, p.object_id,
                                        temp_class_table, p.object_id)
        object_match_clauses = table_match + image_match + object_match
        count_query = 'SELECT %s, %s FROM %s, %s WHERE %s GROUP BY %s' % \
                        (UniqueImageClause(object_table_name), 
                         ", ".join(["SUM(%s.class%d * %s.%s)"%(temp_class_table, k, object_table_name, p.area_scoring_column) for k in classidxs]),
                         temp_class_table, object_table_from,
                         object_match_clauses,
                         UniqueImageClause(object_table_name))
    
    return stump_stmnts, score_stmnts, find_max_query, class_stmnts, count_query
    

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
    RETURNS: A list of object keys that fall in the specified class.
    '''
    stump_stmnts, score_stmnts, find_max_query, _, _ = translate(weaklearners, filterKeys=filterKeys)

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
    stump_stmnts, score_stmnts, find_max_query, class_stmnts, count_query = \
                 translate(weaklearners, filter=filter)
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
                cb((idx + stepnum * num_clauses)/ float(num_steps))
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
    do_by_steps(class_stmnts[1], 2)
    db.Execute(count_query)
    
    keysAndCounts = db.GetResultsAsList()
    
    nClasses = len(weaklearners[0][2])
    # Add in images with zero object count that the queries missed
    for imKey, obCount in dm.GetImageKeysAndObjectCounts(filter):
        if obCount == 0:
            keysAndCounts += [list(imKey) + [0 for c in range(nClasses)]]

    return [list(row) for row in keysAndCounts] 


if __name__ == "__main__":
    dir = "/Users/ljosa/research/modifier/piyush"
    p.LoadFile("%s/batch1and2.properties"%(dir,))
    import cPickle as pickle
    f = open("%s/batch1and2.boostingclassifier"%(dir,))
    learners = pickle.load(f)
    f.close()

    keys_and_counts = PerImageCounts(learners, filter='HRG')
    import numpy
    keys_and_counts = numpy.array(keys_and_counts, dtype='i4')
    print keys_and_counts[0,:]
    print sum(keys_and_counts[:,-2:])
