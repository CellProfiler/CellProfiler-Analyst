
import numpy
import sys
import cpa.sqltools
from .dbconnect import *
from .properties import Properties
from .datamodel import DataModel

db = DBConnect()
p = Properties()
dm = DataModel()

temp_stump_table = "_stump"
temp_score_table = "_scores"
temp_class_table = "_class"
filter_table_prefix = '_filter_'

def translate(weaklearners):
    '''
    Translate weak leaners into a classifier() expression
    (or something more complicated in the future).
    '''
    num_features = len(weaklearners)
    nClasses = len(weaklearners[0][2])

    has_classifier_function = False
    if p.db_type.lower() == 'sqlite':
        thresholds = numpy.array([wl[1] for wl in weaklearners])
        a = numpy.array([wl[2] for wl in weaklearners])
        b = numpy.array([wl[3] for wl in weaklearners])
        db.setup_sqlite_classifier(thresholds, a, b)
        return "classifier(%s)"%(",".join([wl[0] for wl in weaklearners]))
    
    if p.db_type.lower() == 'mysql':
        # MySQL
        try:
            res = db.execute("SELECT * from mysql.func where name='classifier'")
            has_classifier_function = len(res) > 0
        except:
            has_classifier_function = False
        if has_classifier_function:
            num_stumps = len(weaklearners)
            featurenames = "1," + ",".join([wl[0] for wl in weaklearners])
            thresholds = "0,"+",".join([str(wl[1]) for wl in weaklearners])
            base = [sum([wl[3][k] for wl in weaklearners]) for k in range(nClasses)]
            weights = ",".join([",".join([str(base[k])] + [str(wl[2][k]-wl[3][k]) for wl in weaklearners]) for k in range(nClasses)])
            return "(classifier(%d, %s, %s, %s)+1)"%(num_stumps + 1, featurenames, thresholds, weights)
        else:
            class_scores = ['+'.join(['IF(`%s` > %f, %f, %f)'%(feature, threshold, a[i], b[i]) for (feature, threshold, a, b, ignore) in weaklearners]) for i in range(nClasses)]
            return "CASE GREATEST(%s) %s END"%(",".join(class_scores), "\n".join(["WHEN %s THEN %d"%(score, idx+1) for idx, score in enumerate(class_scores)]))
    

def FilterObjectsFromClassN(clNum, weaklearners, filterKeys):
    '''
    clNum: 1-based index of the class to retrieve obKeys from
    weaklearners: Weak learners from fastgentleboostingmulticlass.train
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

    class_query = translate(weaklearners)

    if filterKeys != []:
        if isinstance(filterKeys, str):
            whereclause = filterKeys + " AND"
        else:
            isImKey = len(filterKeys[0]) == len(image_key_columns())
            if isImKey:
                whereclause = GetWhereClauseForImages(filterKeys) + " AND"
            else:
                whereclause = GetWhereClauseForObjects(filterKeys) + " AND"
    else:
        whereclause = ""
    
    return db.execute('SELECT '+UniqueObjectClause()+' FROM %s WHERE %s %s=%d '%(p.object_table, whereclause, class_query, clNum))


def object_scores(weaklearners):
    stump_stmnts, score_stmnts, find_max_query, _, _ = \
                  translate(weaklearners)
    db.execute('DROP TABLE IF EXISTS _stump')
    db.execute('DROP TABLE IF EXISTS _scores')
    [db.execute(stump_query) for stump_query in stump_stmnts] 
    [db.execute(score_query) for score_query in score_stmnts]
    col_names = db.GetColumnNames('_scores')
    col_types = db.GetColumnTypes('_scores')
    type_mapping = { int: 'i4', float: 'f8' }
    dtype = numpy.dtype([(name, type_mapping[type])
                         for name, type in zip(col_names, col_types)])
    res = db.execute('SELECT * from _scores')
    return numpy.array(list(map(tuple, res)), dtype)


def create_perobject_class_table(classnames, rules):
    ''' Saves object keys and classes to a text file '''
    nClasses = len(classnames)

    if p.class_table is None:
        raise ValueError('"class_table" in properties file is not set.')

    index_cols = UniqueObjectClause()
    class_cols = UniqueObjectClause() + ', class, class_number'
    class_col_defs = object_key_defs() + ', class VARCHAR (%d)'%(max([len(c) for c in classnames])+1) + ', class_number INT'
    
    
    # Drop must be explicitly asked for Classifier.ScoreAll
    db.execute('DROP TABLE IF EXISTS %s'%(p.class_table))
    db.execute('CREATE TABLE %s (%s)'%(p.class_table, class_col_defs))
    db.execute('CREATE INDEX idx_%s ON %s (%s)'%(p.class_table, p.class_table, index_cols))
        
    case_expr = 'CASE %s'%(translate(rules)) + ''.join([" WHEN %d THEN '%s'"%(n+1, classnames[n]) for n in range(nClasses)]) + " END"
    case_expr2 = 'CASE %s'%(translate(rules)) + ''.join([" WHEN %d THEN '%s'"%(n+1, n+1) for n in range(nClasses)]) + " END"
    db.execute('INSERT INTO %s (%s) SELECT %s, %s, %s FROM %s'%(p.class_table, class_cols, index_cols, case_expr, case_expr2, p.object_table))
    db.Commit()

def _objectify(p, field):
    return "%s.%s"%(p.object_table, field)

def _where_clauses(p, dm, filter_name):
    imkeys = dm.GetAllImageKeys(filter_name)
    imkeys.sort()
    stepsize = max(len(imkeys) // 100, 50)
    key_thresholds = imkeys[-1:1:-stepsize]
    key_thresholds.reverse()
    if len(key_thresholds) == 0:
        return ['(1 = 1)']
    if p.table_id:
        # split each table independently
        def splitter():
            yield "(%s = %d) AND (%s <= %d)"%(_objectify(p, p.table_id), key_thresholds[0][0], 
                                              _objectify(p, p.image_id), key_thresholds[0][1])
            for lo, hi in zip(key_thresholds[:-1], key_thresholds[1:]):
                if lo[0] == hi[0]:
                    # block within one table
                    yield "(%s = %d) AND (%s > %d) AND (%s <= %d)"%(_objectify(p, p.table_id), lo[0], 
                                                                    _objectify(p, p.image_id), lo[1], 
                                                                    _objectify(p, p.image_id), hi[1])
                else:
                    # query spans a table boundary
                    yield "(%s >= %d) AND (%s > %d)"%(_objectify(p, p.table_id), lo[0], 
                                                     _objectify(p, p.image_id), lo[1])
                    yield "(%s <= %d) AND (%s <= %d)"%(_objectify(p, p.table_id), hi[0], 
                                                      _objectify(p, p.image_id), hi[1])
        return list(splitter())
    else:
        return (["(%s <= %d)"%(_objectify(p, p.image_id), key_thresholds[0][0])] + 
                ["(%s > %d) AND (%s <= %d)"
                 %(_objectify(p, p.image_id), lo[0], _objectify(p, p.image_id), hi[0])
                 for lo, hi in zip(key_thresholds[:-1], key_thresholds[1:])])
    
def PerImageCounts(weaklearners, filter_name=None, cb=None):
    '''
    weaklearners: Weak learners from fastgentleboostingmulticlass.train
    filter: name of filter, or None.
    cb: callback function to update with the fraction complete
    RETURNS: A list of lists of imKeys and respective object counts for each class:
        Note that the imKeys are exploded so each row is of the form:
        [TableNumber, ImageNumber, Class1_ObjectCount, Class2_ObjectCount,...]
        where TableNumber is only present if table_id is defined in Properties. 
        If p.area_scoring_column is set, then area scores will be appended to
        the object scores.
    '''

    # I'm pretty sure this would be even faster if we were to run two
    # or more parallel threads and split the work between them.
    def do_by_steps(class_query, tables, filter_name, result_clauses):
        filter_clause = '1 = 1'
        join_clause = ''
        if filter_name is not None:
            filter = p._filters[filter_name]
            if isinstance(filter, cpa.sqltools.OldFilter):
                join_table = '(%s) as filter' % str(filter)
            else:
                if p.object_table in tables:
                    join_table = None
                else:
                    join_table = p.object_table
                    filter_clause = str(filter)
            if join_table:
                join_clause = 'JOIN %s USING (%s)' % (join_table, ','.join(image_key_columns()))
        if cb:
            result =  []
            wheres = _where_clauses(p, dm, filter_name)
            num_clauses = len(wheres)
            
            for idx, where_clause in enumerate(wheres):
                if filter_clause is not None:
                    where_clause += ' AND ' + filter_clause
                result += [db.execute('SELECT %s, %s as class, %s FROM %s '
                                      '%s WHERE %s GROUP BY %s, class'
                                      %(UniqueImageClause(p.object_table), 
                                        class_query, result_clauses, tables, 
                                        join_clause, where_clause, 
                                        UniqueImageClause(p.object_table)),
                                      silent=(idx > 10))]
                cb(min(1, idx/float(num_clauses)))
            return sum(result, [])
        else:
            return db.execute('SELECT %s, %s as class, %s FROM %s %s WHERE %s GROUP BY %s, class'%
                              (imkeys, class_query, result_clauses, tables, join_clause, filter_clause, imkeys))
    
    if p.area_scoring_column is None:
        result_clauses = 'COUNT(*)'
    else:
        result_clauses = 'COUNT(*), SUM(%s)'%(_objectify(p, p.area_scoring_column))

    class_query = translate(weaklearners)
    results = do_by_steps(class_query, p.object_table, filter_name, result_clauses)

    # convert to dictionary
    counts = {}
    keylen = 1 + len(image_key_columns()) # includes class

    for r in results:
        counts[r[:keylen]] = r[keylen:]

    num_classes = len(weaklearners[0][2])
    # this is clearer than the one-line version
    def get_count(im_key, classnum):
        return counts.get(tuple(list(im_key) + [classnum]), [0])[0]

    def get_area(im_key, classnum):
        return counts.get(tuple(list(im_key) + [classnum]), [0, 0])[1]

    def get_results():
        for imkey in dm.GetImageKeysAndObjectCounts(filter_name):
            if p.area_scoring_column is None:
                yield list(imkey[0]) + [get_count(imkey[0], cl) for cl in range(1, num_classes+1)]
            else:
                yield list(imkey[0]) + [get_count(imkey[0], cl) for cl in range(1, num_classes+1)] + [get_area(imkey[0], cl) for cl in range(1, num_classes+1)]

    return list(get_results())


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

    from .trainingset import TrainingSet
    from io import StringIO
    from . import fastgentleboostingmulticlass
    from .datatable import DataGrid
    import wx
    p = Properties()
    db = DBConnect()
    dm = DataModel()
    
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
    trainingSet = TrainingSet(p)
    trainingSet.Load(ts)
    output = StringIO()
    print(('Training classifier with '+str(nRules)+' rules...'))
    weaklearners = fastgentleboostingmulticlass.train(trainingSet.colnames,
                                                      nRules, trainingSet.label_matrix, 
                                                      trainingSet.values, output)
    table = PerImageCounts(weaklearners, filter_name=filter)
    table.sort()

    labels = ['table', 'image'] + list(trainingSet.labels) + list(trainingSet.labels)
    print(labels)
    for row in table:
        print(row)
#    app = wx.App()
#    grid = DataGrid(numpy.array(table), labels, key_col_indices=[0,1])
#    grid.Show()
#    app.MainLoop()
    
