import numpy
from DBConnect import *
from Properties import Properties


db = DBConnect.getInstance()
p = Properties.getInstance()


def translate(weak_learners, column_names):
    '''translate weak learners into MySQL queries that place the resulting 
    classification in a table (name: temp_prefix_classlabels)
    '''
    
    num_features = len(weak_learners)
    num_classes = len(weak_learners[0][2])

    if 'table_id' in p.__dict__:
        columns_start = p.table_id+" INT, "+p.image_id+" INT, "+p.object_id+" INT, "
    else:
        columns_start = p.image_id+" INT, "+p.object_id+" INT, "
    
    select_start = UniqueObjectClause()+', '
    
    # Create stump table (ob x nRules) <0/1>
    temp_stump_table = "_stump"
    stump_columns = columns_start + ", ".join(["stump%d TINYINT"%(i) for i in range(num_features)])
    stump_select_features = ", ".join(["(%s > %f) AS stump%d"%(column_names[wl[0]], wl[1], idx) for wl,idx in zip(weak_learners, range(num_features))])
    stump_select_statement = select_start + stump_select_features + " FROM " + p.object_table
    stump_query = 'CREATE TEMPORARY TABLE %(temp_stump_table)s (%(stump_columns)s) SELECT %(stump_select_statement)s'%(locals())
    
    # Create class scores table (ob x classes) <float>
    classidxs = range(1, num_classes+1)
    temp_score_table = "_scores"
    score_vals_columns = ["score%d"%(i) for i in classidxs]
    score_columns = columns_start + ", ".join(["%s FLOAT"%(s) for s in score_vals_columns]) + ", score_greatest FLOAT"
    score_select_scores = ", ".join(["+".join(["IF(stump%d, %f, %f)"%(i, weak_learners[i][2][k-1], weak_learners[i][3][k-1]) for i in range(num_features)]) + " AS score%d"%(k) for k in classidxs])
    score_select_statement = select_start + score_select_scores + ", 0.0 FROM " + temp_stump_table
    score_query = 'CREATE TEMPORARY TABLE %(temp_score_table)s (%(score_columns)s) SELECT %(score_select_statement)s'%(locals())
    
    # Create maximum column in class scores table
    greatest_expr = "GREATEST(" + ", ".join(score_vals_columns) + ")"
    find_max_query = "UPDATE %(temp_score_table)s SET score_greatest = %(greatest_expr)s"%(locals())

    # Convert to class membership table (ob x classes) <T/F>
    temp_class_table = "_class"
    class_columns = columns_start + ", ".join(["class%d TINYINT"%(k) for k in classidxs])
    select_class_greatest = ", ".join(["%s = score_greatest AS class%d"%(sc, k) for sc,k in zip(score_vals_columns, classidxs)])
    class_select_statement = select_start + select_class_greatest + " FROM " + temp_score_table
    class_query = 'CREATE TEMPORARY TABLE %(temp_class_table)s (%(class_columns)s) SELECT %(class_select_statement)s'%(locals())

    # Get hit counts
    count_query = 'SELECT %s, %s FROM %s GROUP BY %s'%(UniqueImageClause(), ", ".join(["SUM(class%d)"%(k) for k in classidxs]), temp_class_table, UniqueImageClause())
    
    return stump_query, score_query, find_max_query, class_query, count_query
    

def FilterObjectsFromClassN(clNum, obKeys, stump_query, score_query, find_max_query):
    # Drop existing temporary tables
    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    stump_query += ' WHERE '+GetWhereClauseForObjects(obKeys)
    db.Execute(stump_query)
    db.Execute(score_query)
    db.Execute(find_max_query)
    db.Execute('SELECT '+UniqueObjectClause()+' FROM _scores WHERE score'+str(clNum)+'=score_greatest')
    return db.GetResultsAsList()
    
    
def HitsAndCounts(stump_query, score_query, find_max_query, class_query, count_query):
    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    db.Execute('DROP TABLE IF EXISTS _class')
    db.Execute(stump_query)
    db.Execute(score_query)
    db.Execute(find_max_query)
    db.Execute(class_query)
    db.Execute(count_query)
    return db.GetResultsAsList()
    
    