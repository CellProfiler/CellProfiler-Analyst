
from sys import stderr
import logging
import numpy
import pickle
import base64
import zlib
import wx
import collections

import pandas as pd
from .dbconnect import *
from .singleton import Singleton

db = DBConnect()

class TrainingSet:
    "A class representing a set of manually labeled cells."

    def __init__(self, properties, filename='', labels_only=False, csv=False):
        self.properties = properties
        self.colnames = db.GetColnamesForClassifier()
        self.key_labels = object_key_columns()
        self.filename = filename
        self.cache = CellCache()
        if filename != '':
            if csv:
                self.LoadCSV(filename, labels_only=labels_only)
            else:
                self.Load(filename, labels_only=labels_only)

    def normalize(self):
        import pandas as pd
        df = pd.DataFrame(self.values, columns = self.colnames)
        df_norm = (df - df.mean()) / (df.max() - df.min())
        return df.values

    # Get back an array with labels instead of numbers
    def get_class_per_object(self):
        return [self.labels[self.label_array[i] - 1] for i in range(len(self.label_array))]

    def Clear(self):
        self.saved = False
        self.labels = []                # set of possible class labels (human readable)
        self.classifier_labels = []     # set of possible class labels (for classifier)
                                        #     eg: [[+1,-1,-1], [-1,+1,-1], [-1,-1,+1]]
        self.label_matrix = []          # n x k matrix of classifier labels for each sample
        self.label_array = []           # n x 1 vector of classifier labels (indexed with 1) 
                                        #     eg: [1,1,2,3,1,2] 
        self.values = []                # array of measurements (data from db) for each sample
        self.entries = []               # list of (label, obKey) pairs
        self.coordinates = []           # list of coordinates per obKey

        # check cache freshness
        try:
            self.cache.clear_if_objects_modified()
        except:
            logging.info("Couldn't check for cache freshness. Connection to DB broken?") #let it pass to allow saving 
            
    def Create(self, labels, keyLists, labels_only=False, callback=None):
        '''
        labels:   list of class labels
                  Example: ['pos','neg','other']
        keyLists: list of lists of obKeys in the respective classes
                  Example: [[k1,k2], [k3], [k4,k5,k6]] 
        '''
        assert len(labels)==len(keyLists), 'Class labels and keyLists must be of equal size.'
        self.Clear()
        self.labels = numpy.array(labels)
        self.classifier_labels = 2 * numpy.eye(len(labels), dtype=int) - 1
        
        num_to_fetch = sum([len(k) for k in keyLists])
        num_fetched = [0] # use a list to get static scoping

        # Populate the label_matrix, entries, and values
        # NB: values that are nonnumeric or Null/None are made to be 0
        idx = 0
        for label, cl_label, keyList in zip(labels, self.classifier_labels, keyLists):
            self.label_matrix += ([cl_label] * len(keyList))

            self.entries += list(zip([label] * len(keyList), keyList))

            if labels_only and len(keyList) > 0:
                self.values += []
                self.coordinates += db.GetObjectsCoords(keyList)
            elif len(keyList) > 0:
                self.values += self.cache.get_objects_data(keyList)
                colnames = db.GetColnamesForClassifier()
                # If we just got the coordinates as part of the data table, we don't need to fetch again.
                if set([p.cell_x_loc, p.cell_y_loc]).issubset(colnames):
                    idx_x = colnames.index(p.cell_x_loc)
                    idx_y = colnames.index(p.cell_y_loc)
                    self.coordinates += [(item[idx_x], item[idx_y]) for item in self.values]
                else:
                    self.coordinates += db.GetObjectsCoords(keyList)
            idx += 1
            if callback:
                callback(idx / len(labels))
        self.label_matrix = numpy.array(self.label_matrix)
        self.values = numpy.array(self.values, np.float64)
        if len(self.label_matrix) > 0:
            self.label_array = numpy.nonzero(self.label_matrix + 1)[1] + 1 # Convert to array
        else:
            self.label_array = self.label_matrix      
            

    def Load(self, filename, labels_only=False):
        self.Clear()
        f = open(filename, 'U')
        lines = f.read()
#        lines = lines.replace('\r', '\n')    # replace CRs with LFs
        lines = lines.split('\n')
        labelDict = collections.OrderedDict()
        self.key_labels = object_key_columns()
        for l in lines:
            try:
                if l.strip()=='': continue
                if l.startswith('#'):
                    self.cache.load_from_string(l[2:])
                    continue
                
                label = l.strip().split(' ')[0]
                if (label == "label"):
                    for labelname in l.strip().split(' ')[1:]:
                        if labelname not in labelDict:
                            labelDict[labelname] = []
                    continue
                
                obKey = tuple([int(float(k)) for k in l.strip().split(' ')[1:len(object_key_columns())+1]])
                labelDict[label] = labelDict.get(label, []) + [obKey]

            except:
                logging.error('Error parsing training set %s, line >>>%s<<<'%(filename, l.strip()))
                f.close()
                raise
            
        # validate positions and renumber if necessary
        self.Renumber(labelDict)
        self.Create(list(labelDict.keys()), list(labelDict.values()), labels_only=labels_only)
        
        f.close()
        
    def LoadCSV(self, filename, labels_only=True):
        self.Clear()
        df = pd.read_csv(filename)
        labels = list(set(df['Class'].values)) # List of labels
        labelDict = collections.OrderedDict() # Why stuck?
        self.key_labels = object_key_columns()
        key_names = [key for key in self.key_labels]
        for label in labels:
            keys = df[key_names][df['Class'] == label].values # Get the keys
            if len(key_names) == 2:
                keys = [tuple((x[0],x[1])) for x in keys] # convert them into tuples
                labelDict[label] = keys
            else:
                assert(len(key_names) == 3)
                keys = [tuple((x[0],x[1],x[2])) for x in keys]
                labelDict[label] = keys
            
        # validate positions and renumber if necessary
        self.Renumber(labelDict)
        self.Create(list(labelDict.keys()), list(labelDict.values()), labels_only=labels_only)
        
    def Renumber(self, label_dict):
        from .properties import Properties
        obkey_length = 3 if Properties().table_id else 2
        
        have_asked = False
        progress = None
        for label in list(label_dict.keys()):
            for idx, key in enumerate(label_dict[label]):
                if len(key) > obkey_length:
                    obkey = key[:obkey_length]
                    x, y = key[obkey_length:obkey_length+2]
                    coord = db.GetObjectCoords(obkey, none_ok=True, silent=True) 
                    if coord == None or (int(coord[0]), int(coord[1])) != (x, y):
                        if not have_asked:
                            dlg = wx.MessageDialog(None, 'Cells in the training set and database have different image positions.  This could be caused by running CellProfiler with different image analysis parameters.  Should CPA attempt to remap cells in the training set to their nearest match in the database?',
                                                   'Attempt remapping of cells by position?', wx.CANCEL|wx.YES_NO|wx.ICON_QUESTION)
                            response = dlg.ShowModal()
                            have_asked = True
                            if response == wx.ID_NO:
                                return
                            elif response == wx.ID_CANCEL:
                                label_dict.clear()
                                return
                        if progress is None:
                            total = sum([len(v) for v in list(label_dict.values())])
                            done = 0
                            progress = wx.ProgressDialog("Remapping", "0%", maximum=total, style=wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
                        label_dict[label][idx] = db.GetObjectNear(obkey[:-1], x, y, silent=True)
                        done = done + 1
                        cont, skip = progress.Update(done, '%d%%'%((100 * done) / total))
                        if not cont:
                            label_dict.clear()
                            return
                        
        have_asked = False
        for label in list(label_dict.keys()):
            if None in label_dict[label]:
                if not have_asked:
                    dlg = wx.MessageDialog(None, 'Some cells from the training set could not be remapped to cells in the database, indicating that the corresponding images are empty.  Continue anyway?',
                                           'Some cells could not be remapped!', wx.YES_NO|wx.ICON_ERROR)
                    response = dlg.ShowModal()
                    have_asked = True
                    if response == wx.ID_NO:
                        label_dict.clear()
                        return
                label_dict[label] = [k for k in label_dict[label] if k is not None]
                
            

    def Save(self, filename):
        # check cache freshness
        try:
            self.cache.clear_if_objects_modified()
        except:
            logging.info("Couldn't check cache freshness, DB connection lost?")

        f = open(filename, 'w')
        try:
            from .properties import Properties
            p = Properties()
            f.write('# Training set created while using properties: %s\n'%(p._filename))
            f.write('label '+' '.join(self.labels)+'\n')
            i = 0
            for label, obKey in self.entries:
                line = '%s %s %s\n'%(label, ' '.join([str(int(k)) for k in obKey]), ' '.join([str(int(k)) for k in self.coordinates[i]]))
                f.write(line)
                i += 1 # increase counter to keep track of the coordinates positions
            try:
                f.write('# ' + self.cache.save_to_string([k[1] for k in self.entries]) + '\n')
            except:
                logging.error("No DB connection, couldn't save cached image strings")
        except:
            logging.error("Error saving training set %s" % (filename))
            f.close()
            raise
        f.close()
        logging.info('Training set saved to %s'%filename)
        self.saved = True

    def SaveAsCSV(self, filename):
        # check cache freshness
        try:
            self.cache.clear_if_objects_modified()
            df = pd.DataFrame(self.values, columns=self.colnames)
        except:
            logging.info("Couldn't check cache freshness, DB connection lost?")
            df = pd.DataFrame([]) # empty

        try:
            from .properties import Properties
            # getting feature values

            # getting object key
            tuples = self.get_object_keys()
            key_labels = self.key_labels
            # Differentiate between ids
            if len(key_labels) == 2:
                keyList = [[x[0],x[1]] for x in tuples]
                df_keys = pd.DataFrame(keyList, columns=key_labels)
            else:
                #assert(len(tuples) == 3) # It has to be 3!
                keyList = [[x[0],x[1],x[2]] for x in tuples]
                df_keys = pd.DataFrame(keyList, columns=key_labels)


            # getting label dataframe
            labels = self.labels
            label_array = self.label_array
            labels = [labels[label_array[i] - 1] for i in range(len(label_array))]
            df_class = pd.DataFrame(labels, columns=["Class"])

            # Join to get the labeled data along the columns!
            df_labeled = pd.concat([df_keys,df_class,df],axis=1)
            df_labeled.to_csv(filename, index=False)

        except:
            logging.error("Error saving training set %s" % (filename))
            raise

        logging.info('Training set saved to %s as CSV'%filename)
        self.saved = True
            

    def get_object_keys(self):
        return [e[1] for e in self.entries]

class CellCache(metaclass=Singleton):
    ''' caching front end for holding cell data '''
    def __init__(self):
        self.data        = {}
        self.colnames    = db.GetColumnNames(p.object_table)
        if db.GetColnamesForClassifier() is not None:
            self.col_indices = [self.colnames.index(v) for v in db.GetColnamesForClassifier()]
        else:
            self.col_indices = []
        self.last_update = db.get_objects_modify_date()

    def load_from_string(self, str):
        'load data from a string, verifying that the table has not changed since it was created (encoded in string)'
        try:
            date, colnames, oldcache = pickle.loads(zlib.decompress(base64.b64decode(str)))
        except:
            # silent failure
            return
        # Strings started sneaking into some caches when we started classifying entire images.
        # Detect this case and force an update to flush them.
        if len(oldcache) > 0:
            if list(oldcache.values())[0].dtype.kind == 'S':
                return
        # verify the database hasn't been changed
        if db.verify_objects_modify_date_earlier(date):
            self.data.update(oldcache)
            self.colnames = colnames

    def save_to_string(self, keys):
        'convert the cache data to a string, but only for certain keys'
        temp = {}
        for k in keys:
            if k in self.data:
                temp[k] = self.data[k]
        output = (db.get_objects_modify_date(), self.colnames, temp)
        return base64.b64encode(zlib.compress(pickle.dumps(output)))

    def get_object_data(self, key):
        if key not in self.data:
            self.data[key] = db.GetCellData(key)
        return self.data[key][self.col_indices]

    def get_objects_data(self, keys):
        # Get data for a list of object keys
        databuffer = db.GetCellsData(keys)
        out = []
        seen = set()
        for key, line in databuffer:
            if key not in keys:
                raise ValueError(f"Retrieved key {key} did not match a desired object")
            if key in self.data and key in seen:
                logging.debug("Duplicate found", self.data[key], line)
            elif key in self.data:
                numpy.testing.assert_equal(self.data[key], line)
                seen.add(key)
            self.data[key] = line
        # SQL call didn't care about duplicates, so we'll have to iterate through to ensure they're added
        for key in keys:
            if key not in self.data:
                logging.error(f"Unable to retrieve key {key}, may be missing from database")
            else:
                out.append(self.data[key][self.col_indices])
        return out

    def clear_if_objects_modified(self):
        if not db.verify_objects_modify_date_earlier(self.last_update):
            self.data = {}
            self.last_update = db.get_objects_modify_date()
        

if __name__ == "__main__":
    from sys import argv
    from .properties import Properties
    p = Properties()
    p.LoadFile(argv[1])
    tr = TrainingSet(p)
    tr.Load(argv[2])
    for i in range(len(tr.labels)):
        print(tr.labels[i], end=' ')
        print(" ".join([str(v) for v in tr.values[i]]))
        
