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

def translate(weaklearners):
    '''
    Translate weak leaners into a classifier() expression
    (or something more complicated in the future).
    '''
    num_features = len(weaklearners)
    nClasses = len(weaklearners[0][2])

    has_classifier_function = False
    if p.db_type.lower() == 'sqlite':
        has_classifier_function = True
    elif p.db_type.lower() == 'mysql':
        db.Execute("SELECT * from mysql.func where name='classifier'")
        has_classifier_function = len(db.GetResultsAsList()) > 0
    
    if has_classifier_function:
        num_stumps = len(weaklearners)
        featurenames = "1," + ",".join([wl[0] for wl in weaklearners])
        thresholds = "0,"+",".join([str(wl[1]) for wl in weaklearners])
        base = [sum([wl[3][k] for wl in weaklearners]) for k in range(nClasses)]
        weights = ",".join([",".join([str(base[k])] + [str(wl[2][k]-wl[3][k]) for wl in weaklearners]) for k in range(nClasses)])
        return "(classifier(%d, %s, %s, %s)+1)"%(num_stumps + 1, featurenames, thresholds, weights)
    else:
        # we should create a stored function here, perhaps
        raise RuntimeError("No classifier() function available in database.")


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

    class_query = translate(weaklearners)

    if filterKeys != []:
        isImKey = len(filterKeys[0]) == (2 if p.table_id else 1)
        if isImKey:
            whereclause = "AND " + GetWhereClauseForImages(filterKeys)
        else:
            whereclause = "AND " + GetWhereClauseForObjects(filterKeys)
    else:
        whereclause = ""

    db.Execute('SELECT '+UniqueObjectClause()+' FROM %s WHERE %s=%d %s'%(p.object_table, class_query, clNum, whereclause))
    return db.GetResultsAsList()


def object_scores(weaklearners, filter=None, filterKeys=[]):
    stump_stmnts, score_stmnts, find_max_query, _, _ = \
                  translate(weaklearners, filter=filter, filterKeys=filterKeys)
    db.Execute('DROP TABLE IF EXISTS _stump')
    db.Execute('DROP TABLE IF EXISTS _scores')
    [db.Execute(stump_query) for stump_query in stump_stmnts] 
    [db.Execute(score_query) for score_query in score_stmnts]
    col_names = db.GetColumnNames('_scores')
    col_types = db.GetColumnTypes('_scores')
    type_mapping = { long: 'i4', float: 'f8' }
    dtype = numpy.dtype([(name, type_mapping[type])
                         for name, type in zip(col_names, col_types)])
    db.Execute('SELECT * from _scores')
    return numpy.array(map(tuple, db.GetResultsAsList()), dtype)
    
    
# TODO: FIX ME!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def CreatePerObjectClassTable(classnames):
    ''' Saves object keys and classes to a text file '''
    nClasses = len(classnames)
    if p.table_id:
        key_col_defs = p.table_id+" INT, "+p.image_id+" INT, "+p.object_id+" INT, "
        index_cols = "%s, %s, %s"%(p.table_id, p.image_id, p.object_id)
    else:
        key_col_defs = p.image_id+" INT, "+p.object_id+" INT, "
        index_cols = "%s, %s"%(p.image_id, p.object_id)
        
    class_cols = index_cols+', class'
    class_col_defs = key_col_defs+'class VARCHAR (100)'
    
    # Drop must be explicitly asked for Classifier.ScoreAll
    #db.Execute('DROP TABLE IF EXISTS `%s`'%(p.class_table))
    db.Execute('CREATE TABLE `%s` (%s)'%(p.class_table, class_col_defs))
    db.Execute('CREATE INDEX `idx_%s` ON `%s` (%s)'%(p.class_table, p.class_table, index_cols))
        
    for i in xrange(nClasses):
        select = 'SELECT %s, "%s" FROM %s WHERE class%d = 1'%(index_cols, classnames[i], temp_class_table, i+1)
        db.Execute('INSERT INTO `%s` (%s) %s'%(p.class_table, class_cols, select))
        
    
def PerImageCounts(weaklearners, filter=None, cb=None):
    '''
    weaklearners: Weak learners from FastGentleBoostingMulticlass.train
    filter: name of filter, or None.
    cb: callback function to update with the fraction complete
    RETURNS: A list of lists of imKeys and respective object counts for each class:
        Note that the imKeys are exploded so each row is of the form:
        [TableNumber, ImageNumber, Class1_ObjectCount, Class2_ObjectCount,...]
        where TableNumber is only present if table_id is defined in Properties. 
        If p.area_scoring_column is set, then area scores will be appended to
        the object scores.
    '''

    def objectify(field):
        return "%s.%s"%(p.object_table, field)

    def where_clauses():
        imkeys = dm.GetAllImageKeys(filter)
        imkeys.sort()
        stepsize = max(len(imkeys) / 100, 50)
        key_thresholds = imkeys[-1:1:-stepsize]
        key_thresholds.reverse()
        if p.table_id:
            # split each table independently
            def splitter():
                yield "(%s = %d) AND (%s <= %d)"%(objectify(p.table_id), key_thresholds[0][0], 
                                                  objectify(p.image_id), key_thresholds[0][1])
                for lo, hi in zip(key_thresholds[:-1], key_thresholds[1:]):
                    if lo[0] == hi[0]:
                        # block within one table
                        yield "(%s = %d) AND (%s > %d) AND (%s <= %d)"%(objectify(p.table_id), lo[0], 
                                                                        objectify(p.image_id), lo[1], 
                                                                        objectify(p.image_id), hi[1])
                    else:
                        # query spans a table boundary
                        yield "(%s = %d) AND (%s > %d)"%(objectify(p.table_id), lo[0], 
                                                         objectify(p.image_id), lo[1])
                        yield "(%s = %d) AND (%s <= %d)"%(objectify(p.table_id), hi[0], 
                                                          objectify(p.image_id), hi[1])
            return list(splitter())
        else:
            return (["(%s <= %d)"%(objectify(p.image_id), key_thresholds[0][0])] + 
                    ["(%s > %d) AND (%s <= %d)"
                     %(objectify(p.image_id), lo[0], objectify(p.image_id), hi[0])
                     for lo, hi in zip(key_thresholds[:-1], key_thresholds[1:])])
                                                            
    # I'm pretty sure this would be even faster if we were to run two
    # or more parallel threads and split the work between them.
    def do_by_steps(imkeys, class_query, tables, filter_clause, result_clauses):
        if cb:
            result =  []
            wheres = where_clauses()
            num_clauses = len(wheres)
            for idx, wc in enumerate(wheres):
                if filter_clause is '':
                    where_clause = wc
                else:
                    where_clause = '%s AND %s'%(wc, filter_clause)
                db.Execute('SELECT %s, %s as class, %s FROM %s WHERE %s GROUP BY %s, class'%
                           (imkeys, class_query, result_clauses, tables, where_clause, imkeys),
                           silent=(idx > 10))
                result += [db.GetResultsAsList()]
                cb(min(1, idx/float(num_clauses)))
            return sum(result, [])
        else:
            if filter_clause is '':
                db.Execute('SELECT %s, %s as class, %s FROM %s GROUP BY %s, class'%
                           (imkeys, class_query, result_clauses, tables, imkeys))
            else:
                db.Execute('SELECT %s, %s as class, %s FROM %s WHERE %s GROUP BY %s, class'%
                           (imkeys, class_query, result_clauses, tables, filter_clause, imkeys))
            return db.GetResultsAsList()
                                                                                  
    if p.table_id:
        imkeys = "%s, %s"%(objectify(p.table_id), objectify(p.image_id))
    else:
        imkeys = objectify(p.image_id)

    if p.area_scoring_column is None:
        result_clauses = 'COUNT(*)'
    else:
        result_clauses = 'COUNT(*), SUM(%s)'%(objectify(p.area_scoring_column))

    filter_clause = ''
    tables = p.object_table
    if filter is not None:
        tables += ', ' + filter_table_prefix+filter
        filter_clause = '%s=`%s`.%s '%(objectify(p.image_id), filter_table_prefix+filter, p.image_id)
        if p.table_id:
            filter_clause += 'AND %s=`%s`.%s '%(objectify(p.table_id), filter_table_prefix+filter, p.table_id)

    class_query = translate(weaklearners)


    results = do_by_steps(imkeys, class_query, tables, filter_clause, result_clauses)

    # convert to dictionary
    counts = {}
    if p.table_id:
        keylen = 3 # includes class
    else:
        keylen = 2 # includes class
    for r in results:
        counts[r[:keylen]] = r[keylen:]

    num_classes = len(weaklearners[0][2])
    # this is clearer than the one-line version
    def get_count(im_key, classnum):
        return counts.get(tuple(list(im_key) + [classnum]), [0])[0]

    def get_area(im_key, classnum):
        return counts.get(tuple(list(im_key) + [classnum]), [0, 0])[1]

    def get_results():
        for imkey in dm.GetImageKeysAndObjectCounts(filter):
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
    CreateFilterTables()
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
    for row in table:
        print row
#    app = wx.PySimpleApp()
#    grid = DataGrid(numpy.array(table), labels, key_col_indices=[0,1])
#    grid.Show()
#    app.MainLoop()
    
