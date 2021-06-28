

import numpy as np
import sys
import logging

sys.path.insert(1, '/home/vagrant/cpa-multiclass/CellProfiler-Analyst/cpa');
sys.path.insert(1, '/home/vagrant/cpa-multiclass/CellProfiler-Analyst/')

import threading
import cpa.sqltools
from .dbconnect import DBConnect, UniqueObjectClause, UniqueImageClause, image_key_columns, object_key_columns, GetWhereClauseForImages, GetWhereClauseForObjects, object_key_defs
from .properties import Properties
from .datamodel import DataModel
from sklearn.ensemble import AdaBoostClassifier
import pandas as pd

db = DBConnect()
p = Properties()
dm = DataModel()

temp_stump_table = "_stump"
temp_score_table = "_scores"
temp_class_table = "_class"
filter_table_prefix = '_filter_'


def create_perobject_class_table(classifier, classNames, updater):
    '''
    classifier: generalclassifier object
    classNames: list/array of class names
    RETURNS: Saves table with columns Table Number, Image Number, Object Number, class number, class name to a pre defined
    table in the database (the class number is the predicted class)
    '''
    updater(0, "Preparing to score")
    if p.class_table is None:
        raise ValueError('"class_table" in properties file is not set.')

    index_cols = UniqueObjectClause()
    class_cols = UniqueObjectClause() + ', class_number, class'
    class_col_defs = f"{object_key_defs()}, class VARCHAR ({max(map(len, classNames))}), class_number INT"

    # Drop must be explicitly asked for Classifier.ScoreAll
    print('Drop table...')
    db.execute('DROP TABLE IF EXISTS %s'%(p.class_table))
    print('Create table...')
    db.execute('CREATE TABLE %s (%s)'%(p.class_table, class_col_defs))
    print('Create index...')
    db.execute('CREATE INDEX idx_%s ON %s (%s)'%(p.class_table, p.class_table, index_cols))

    print('Getting data...')
    chunk_size = 10000
    cap = dm.get_total_object_count()
    updater(0, "Classifying objects...")

    for start in range(0, cap, chunk_size):
        updater(int(start / cap * 100))

        print(f"Classifying object... {start}")
        data = db.execute(f'SELECT {UniqueObjectClause(p.object_table)}, {",".join(db.GetColnamesForClassifier())} '
                          f'FROM {p.object_table} LIMIT {start}, {chunk_size}')

        print('Getting predictions...')
        cell_data, object_keys = processData(data)
        predicted_classes = classifier.Predict(cell_data)

        try:
            print('Preparing data table...')
            # We need to pass a connection object to Pandas so it can do all the work for us.
            connID = threading.currentThread().getName()
            if connID not in db.connections:
                db.connect()
            conn = db.connections[connID]
            class_data = pd.DataFrame(data=object_keys, columns=object_key_columns())
            class_data["class"] = [classNames[i - 1] for i in predicted_classes]
            class_data["class_number"] = predicted_classes
            print('Writing to database...')
            class_data.to_sql(p.class_table, conn, if_exists="append", index=False)
        except:
            # This is the old writing method, may still be necessary if a weird db connection type is used.
            print("Faster database writing method failed, retrying with slow method...")
            print('Drop table...')
            db.execute('DROP TABLE IF EXISTS %s'%(p.class_table))
            print('Create table...')
            db.execute('CREATE TABLE %s (%s)'%(p.class_table, class_col_defs))
            print('Create index...')
            db.execute('CREATE INDEX idx_%s ON %s (%s)'%(p.class_table, p.class_table, index_cols))

            if len(object_keys.shape) > 2:
                expr = 'CASE '+ ''.join(["WHEN %s=%d AND %s=%d AND %s=%d THEN '%s'"%(p.table_id,
                    object_keys[ii][0], p.image_id, object_keys[ii][1], p.object_id, object_keys[ii][2], predicted_classes[ii] )
                    for ii in range(0, len(predicted_classes))])+ " END"
                expr2 = 'CASE '+ ''.join(["WHEN %s=%d AND %s=%d AND %s=%d THEN '%s'"%(p.table_id,
                    object_keys[ii][0], p.image_id, object_keys[ii][1], p.object_id, object_keys[ii][2],
                    classNames[predicted_classes[ii] - 1]) for ii in range(0, len(predicted_classes))])+ " END"
            elif len(object_keys.shape) == 2:
                expr = 'CASE '+ ''.join(["WHEN %s=%d AND %s=%d THEN '%s'"%(p.image_id,
                    object_keys[ii][0], p.object_id, object_keys[ii][1], predicted_classes[ii] )
                    for ii in range(0, len(predicted_classes))])+ " END"
                expr2 = 'CASE '+ ''.join(["WHEN %s=%d AND %s=%d THEN '%s'"%(p.image_id,
                    object_keys[ii][0], p.object_id, object_keys[ii][1], classNames[predicted_classes[ii] - 1])
                    for ii in range(0, len(predicted_classes))])+ " END"
            else:
                raise Exception(f'object keys have length {len(object_keys.shape)} but should have length >= 2')
            print('Writing to database...')
            db.execute('INSERT INTO %s (%s) SELECT %s, %s, %s FROM %s'%(p.class_table, class_cols, index_cols, expr, expr2, p.object_table),
                silent=True)
    db.Commit()



def FilterObjectsFromClassN(classNum, classifier, filterKeys, uncertain):
    '''
    uncertain: allows to search for uncertain (regarding the probs assigned by the classifier) cell images
    classNum: 1-based index of the class to retrieve obKeys from
    classifier: trained classifier object
    filterKeys: (optional) A list of specific imKeys OR obKeys (NOT BOTH)
        to classify.
        * WARNING: If this list is too long, you may exceed the size limit to
          MySQL queries.
        * Useful when fetching N objects from a particular class. Use the
          DataModel to get batches of random objects, and sift through them
          here until N objects of the desired class have been accumulated.
        * Also useful for classifying a specific image or group of images.
    RETURNS: A list of object keys that fall in the specified class (but not all objects?),
        if Properties.area_scoring_column is specified, area sums are also
        reported for each class
    '''

    if filterKeys != [] and filterKeys is not None:

        if isinstance(filterKeys, str):
            whereclause = filterKeys #+ " AND"
        else:
            isImKey = len(filterKeys[0]) == len(image_key_columns())
            if isImKey:
                whereclause = GetWhereClauseForImages(filterKeys) #+ " AND"
            else:
                whereclause = GetWhereClauseForObjects(filterKeys) #+ " AND"
    else:
        whereclause = ""

    if p.area_scoring_column:
        data = db.execute('SELECT %s, %s FROM %s WHERE %s'%(UniqueObjectClause(p.object_table),
        ",".join(db.GetColnamesForClassifier()),
        _objectify(p, p.area_scoring_column), p.object_table, whereclause))
        area_score = data[-1] #separate area from data
        data = data[:-1]
    else:
        data = db.execute('SELECT %s, %s FROM %s WHERE %s'%(UniqueObjectClause(p.object_table),
        ",".join(db.GetColnamesForClassifier()), p.object_table, whereclause))

    cell_data, object_keys = processData(data)#, p.check_tables=='yes')
    res = [] # list
    if uncertain:
        # Our requirement: if the two largest scores are smaller than threshold
        probabilities = classifier.PredictProba(cell_data) #
        threshold = 0.1 # TODO: This threshold should be adjustable
        sorted_p = np.sort(probabilities)[:,-2:]# sorted array
        diff = sorted_p[:,1] - sorted_p[:,0]

        indices = np.where(diff < threshold)[0] # get all indices where this is true
        res = [object_keys[i] for i in indices]
    else:
        predicted_classes = classifier.Predict(cell_data)
        res = object_keys[predicted_classes == classNum * np.ones(predicted_classes.shape)].tolist() #convert to list
    return list(map(tuple,res)) # ... and then to tuples

def processData(data):
    #takes data from query and returns arrays for feature values and object keys
    col_names = db.GetColnamesForClassifier()
    number_of_features = len(col_names)

    # Old method of generating data arrays
    # cell_data = []
    # object_keys = []
    # for row in data:
    #     cell_data.append(row[-number_of_features:])#last number_of_features columns in row
    #     object_keys.append(row[:-number_of_features])#all elements in row before last (number_of_features) elements
    # cell_data = np.array(cell_data)
    # object_keys = np.array(object_keys)
    # New method, Mar 2021
    object_keys, cell_data = np.split(np.array(data), [-number_of_features], axis=1)
    object_keys = np.array(list(map(tuple, object_keys))).astype(int)

    # if numpy array is already floats, pass; if numpy array contains strings, convert
    if not np.issubdtype(cell_data.dtype, float):
        cell_data = np.where(cell_data == np.array(None), '0', cell_data).astype(str)

        data_shape = cell_data.shape
        try:
            cell_data = np.apply_along_axis(pd.to_numeric, 1, cell_data, errors="coerce")
            # print(('data type 1 ', cell_data.dtype))
        except Exception as e:
            logging.info("Data conversion failed, trying slower method - ", e)
            try:
                cell_data = np.reshape(np.genfromtxt(cell_data.ravel(), delimiter=','), data_shape)
            except Exception as e:
                logging.info("Fallback data conversion failed, will try proceeding anyway - ", e)
            # print(('data type 2 ', cell_data.dtype))
    cell_data = np.nan_to_num(cell_data)
    logging.info('Any values that cannot be converted to float were set to 0')
    return cell_data, object_keys

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

def PerImageCounts(classifier, num_classes, filter_name=None, cb=None):
    '''
    classifier: trained classifier object
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
    # For each image clause, classify the cells using the model
    # then for each image key, count the number in each class (and maybe area)
    def do_by_steps(tables, filter_name, area_score=False):
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

        wheres = _where_clauses(p, dm, filter_name)
        num_clauses = len(wheres)
        counts = {}

        # iterate over where clauses to go through whole set
        for idx, where_clause in enumerate(wheres):
            if filter_clause is not None:
                where_clause += ' AND ' + filter_clause
            if area_score:
                data = db.execute('SELECT %s, %s, %s FROM %s '
                                  '%s WHERE %s'
                                  %(UniqueImageClause(p.object_table),
                                    ",".join(db.GetColnamesForClassifier()),
                                    _objectify(p, p.area_scoring_column), tables,
                                    join_clause, where_clause),
                                  silent=(idx > 10))
                area_score = data[-1] #separate area from data
                data = data[:-1]
            else:
                data = db.execute('SELECT %s, %s FROM %s '
                              '%s WHERE %s'
                              %(UniqueObjectClause(p.object_table),
                                ",".join(db.GetColnamesForClassifier()), tables,
                                join_clause, where_clause),
                              silent=(idx > 10))

            cell_data, image_keys = processData(data)
            predicted_classes = classifier.Predict(cell_data)
            for i in range(0, len(predicted_classes)):
                row_cls = tuple(np.append(image_keys[i][0], predicted_classes[i]))
                oneCount = np.array([1])
                if area_score:
                    oneCount = np.append(oneCount, area_score[i])
                if row_cls in counts:
                    counts[row_cls] += oneCount
                else:
                    counts[row_cls] = oneCount

            if cb:
                cb(min(1, (idx + 1)/num_clauses)) #progress
        return counts
    counts = do_by_steps(p.object_table, filter_name, p.area_scoring_column)
    def get_count(im_key, classnum):
        return counts.get(im_key + (classnum, ), np.array([0]))[0]

    def get_area(im_key, classnum):
        return counts.get(im_key + (classnum, ), np.array([0, 0]))[1]

    def get_results():
        for imkey in dm.GetImageKeysAndObjectCounts(filter_name):
            if p.area_scoring_column is None:
                yield list(imkey[0]) + [get_count(imkey[0], cl) for cl in range(1, num_classes+1)]
            else:
                yield list(imkey[0]) + [get_count(imkey[0], cl) for cl in range(1, num_classes+1)] + [get_area(imkey[0], cl) for cl in range(1, num_classes+1)]

    return list(get_results())


if __name__ == "__main__":
    from .trainingset import TrainingSet
    from io import StringIO
    from . import generalclassifier
    from .datatable import DataGrid
    import wx
    p = Properties()
    db = DBConnect()
    dm = DataModel()

    props = '/vagrant/az-dnaonly.properties'
    ts = '/vagrant/Anne_DNA_66.txt'
    nRules = 5
    filter = None

    classifier = AdaBoostClassifier(n_estimators=nRules)
    GC = generalclassifier.GeneralClassifier(classifier)

    p.LoadFile(props)
    trainingSet = TrainingSet(p)
    trainingSet.Load(ts)
    print((trainingSet.label_matrix.shape))
    print((trainingSet.labels))
    print((len(trainingSet.colnames)))
    print((trainingSet.values.shape))
    output = StringIO()
    print(('Training classifier with '+str(nRules)+' rules...'))

    labels = np.nonzero(trainingSet.label_matrix+1)[1] + 1 #base 1 classes
    print((len(labels)))
    GC.Train(labels,trainingSet.values)
    num_classes = trainingSet.label_matrix.shape[1]

    '''
    table = PerImageCounts(GC.classifier, num_classes, filter_name=filter)
    table.sort()
    labels = ['table', 'image'] + list(trainingSet.labels) + list(trainingSet.labels)
    for row in table:
        print row'''

    #obkey_list = FilterObjectsFromClassN(2, GC, filterKeys=None)
    #for row in obkey_list:
    #    print row
    #object_scores()
    p.class_table = 'testmulticlassql'
    create_perobject_class_table(GC, list(range(num_classes)))
    #_objectify()
