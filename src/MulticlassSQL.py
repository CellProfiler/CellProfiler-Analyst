import numpy
from DBConnect import *
from Properties import Properties


db = DBConnect.getInstance()
p = Properties.getInstance()


def translate(weak_learners, column_names, area_column=None, filter=None):
    '''
    Translate weak learners into MySQL queries that place the resulting 
      classification in a MySQL temporary table named "temp_class_table"
    If imKeys is supplied, then the queries will only include those images.
    '''
    
    num_features = len(weak_learners)
    num_classes = len(weak_learners[0][2])

    if p.table_id:
        key_col_defs = p.table_id+" INT, "+p.image_id+" INT, "+p.object_id+" INT, "
    else:
        key_col_defs = p.image_id+" INT, "+p.object_id+" INT, "
        
    select_start = UniqueObjectClause()+', '

    # If a filter is specified, use it as a subquery; otherwise, just
    # use the object table.
    if filter is None:
        object_table_name = p.object_table
        object_table_from = p.object_table
    else:
        object_table_name = filter
        object_table_from = ("(%s) as %s JOIN %s using (%s)"%
                             (p.filters[filter], filter, p.object_table,
                              ", ".join(image_key_columns())))
    
    # Create stump table (ob x nRules) <0/1>
    temp_stump_table       = "_stump"
    stump_cols             = select_start + ", ".join(["stump%d"%(i) for i in range(num_features)])
    stump_col_defs         = key_col_defs + ", ".join(["stump%d TINYINT"%(i) for i in range(num_features)])
    stump_select_features  = ", ".join(["(%s > %f) AS stump%d"%(column_names[wl[0]], wl[1], idx) for idx, wl in enumerate(weak_learners)])
    stump_select_statement = select_start + stump_select_features + \
                             " FROM " + object_table_from
    q_stump1 = 'CREATE TEMPORARY TABLE %s (%s)'%(temp_stump_table, stump_col_defs)
    q_stump2 = 'INSERT INTO %s (%s) SELECT %s'%(temp_stump_table, stump_cols, stump_select_statement)
    
    # Create class scores table (ob x classes) <float>
    classidxs          = range(1, num_classes+1)
    temp_score_table   = "_scores"
    score_vals_columns = ["score%d"%(i) for i in classidxs]
    score_col_defs     = key_col_defs + ", ".join(["%s FLOAT"%(s) for s in score_vals_columns]) + ", score_greatest FLOAT"
    score_cols         = select_start + ", ".join(["%s"%(s) for s in score_vals_columns]) + ", score_greatest"
    # SQLite doesn't support conditional operators, so we use math instead:
    # Example: if (A>B), C, D ==> D+(C-D)*(A>B)
    score_select_scores = ", ".join(["+".join(["%f+(%f-(%f))*(stump%d)"
                                    %(weak_learners[i][3][k-1], weak_learners[i][2][k-1],weak_learners[i][3][k-1], i) 
                                    for i in range(num_features)]) + " AS score%d"%(k)
                                    for k in classidxs])
    score_select_statement = select_start + score_select_scores + ", 0.0 FROM " + temp_stump_table
    q_score1 = 'CREATE TEMPORARY TABLE %(temp_score_table)s (%(score_col_defs)s)'%(locals())
    q_score2 = 'INSERT INTO %s (%s) SELECT %s'%(temp_score_table, score_cols, score_select_statement )
    
    # Create maximum column in class scores table
    greatest_expr = "GREATEST(" + ", ".join(score_vals_columns) + ")"
    find_max_query = "UPDATE %(temp_score_table)s SET score_greatest = %(greatest_expr)s"%(locals())

    # Convert to class membership table (ob x classes) <T/F>
    temp_class_table      = "_class"
    class_cols            = select_start + ", ".join(["class%d"%(k) for k in classidxs])
    class_col_defs        = key_col_defs + ", ".join(["class%d TINYINT"%(k) for k in classidxs])
    select_class_greatest = ", ".join(["%s = score_greatest AS class%d"%(sc, k) for sc,k in zip(score_vals_columns, classidxs)])
    class_select_statement = select_start + select_class_greatest + " FROM " + temp_score_table
    q_class1 = 'CREATE TEMPORARY TABLE %s (%s)'%(temp_class_table, class_col_defs)
    q_class2 = 'INSERT INTO %s (%s) SELECT %s'%(temp_class_table, class_cols, class_select_statement)


    # Get hit counts
    count_query = 'SELECT %s, %s FROM %s GROUP BY %s' % \
                        (UniqueImageClause(), 
                         ", ".join(["SUM(class%d)"%(k) for k in classidxs]),
                         temp_class_table, UniqueImageClause())

    # handle area-based scoring if needed, replacing count query
    if area_column:
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
                         ", ".join(["SUM(%s.class%d * %s.%s)"%(temp_class_table, k, object_table_name, area_column) for k in classidxs]),
                         temp_class_table, object_table_from,
                         object_match_clauses,
                         UniqueImageClause(object_table_name))
    
    return [q_stump1, q_stump2], [q_score1, q_score2], find_max_query, [q_class1, q_class2], count_query
#    return stump_query, score_query, find_max_query, class_query, count_query
    

def FilterObjectsFromClassN(clNum, weaklearners, colnames, filterKeys=[]):
    '''
    clNum: 1-based index of the class to retrieve obKeys from
    weaklearners: Weak learners from FastGentleBoostingMulticlass.train
    colnames: Column names to include in classification
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
    isImKey = lambda(k): (p.table_id and len(k)==2) or (not p.table_id and len(k)==1)    
    stump_query, score_query, find_max_query, _, _ = translate(weaklearners, colnames)
    if filterKeys:
        if isImKey(filterKeys[0]):
            stump_query[1] += ' WHERE '+GetWhereClauseForImages(filterKeys)
        else:
            stump_query[1] += ' WHERE '+GetWhereClauseForObjects(filterKeys)
    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    db.Execute(stump_query[0])
    db.Execute(stump_query[1])
    db.Execute(score_query[0])
    db.Execute(score_query[1])
    db.Execute(find_max_query)
    db.Execute('SELECT '+UniqueObjectClause()+' FROM _scores WHERE score'+str(clNum)+'=score_greatest')
    return db.GetResultsAsList()
    
    
def HitsAndCounts(weaklearners, colnames, filter=None):
    '''
    weaklearners: Weak learners from FastGentleBoostingMulticlass.train
    colnames: Column names to include in classification
    filter: name of filter, or None.
    RETURNS: A list of lists of imKeys and respective object counts for each class:
        Note that the imKeys are exploded so each row is of the form:
        [TableNumber, ImageNumber, Class1_ObjectCount, Class2_ObjectCount,...]
        where TableNumber is only present if table_id is defined in Properties. 
    '''
    stump_query, score_query, find_max_query, class_query, count_query = \
                 translate(weaklearners, colnames, filter=filter)
    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    db.Execute('DROP TABLE IF EXISTS _class')
    db.Execute(stump_query[0])
    db.Execute(stump_query[1])    
    db.Execute(score_query[0])
    db.Execute(score_query[1])
    db.Execute(find_max_query)
    db.Execute(class_query[0])
    db.Execute(class_query[1])
    db.Execute(count_query)
    return db.GetResultsAsList()    

if __name__ == "__main__":
    dir = "/Users/ljosa/research/modifier/piyush"
    p.LoadFile("%s/batch1and2.properties"%(dir,))
    import cPickle as pickle
    f = open("%s/batch1and2.boostingclassifier"%(dir,))
    colnames = pickle.load(f)
    learners = pickle.load(f)
    f.close()

    keys_and_counts = HitsAndCounts(learners, colnames, filter='HRG')
    import numpy
    keys_and_counts = numpy.array(keys_and_counts, dtype='i4')
    print keys_and_counts[0,:]
    print sum(keys_and_counts[:,-2:])
