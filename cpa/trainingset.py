from sys import stderr
import logging
import numpy
import cPickle
import base64
import zlib
import wx
import collections

from dbconnect import *
from singleton import Singleton

db = DBConnect.getInstance()

class TrainingSet:
    "A class representing a set of manually labeled cells."

    def __init__(self, properties, filename='', labels_only=False):
        self.properties = properties
        self.colnames = db.GetColnamesForClassifier()
        self.filename = filename
        self.cache = CellCache.getInstance()
        if filename != '':
            self.Load(filename, labels_only=labels_only)


    def Clear(self):
        self.saved = False
        self.labels = []                # set of possible class labels (human readable)
        self.classifier_labels = []     # set of possible class labels (for classifier)
                                        #     eg: [[+1,-1,-1], [-1,+1,-1], [-1,-1,+1]]
        self.label_matrix = []          # array of classifier labels for each sample
        self.values = []                # array of measurements (data from db) for each sample
        self.entries = []               # list of (label, obKey) pairs

        # check cache freshness
        self.cache.clear_if_objects_modified()
            
            
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
        self.classifier_labels = 2 * numpy.eye(len(labels), dtype=numpy.int) - 1
        
        num_to_fetch = sum([len(k) for k in keyLists])
        num_fetched = [0] # use a list to get static scoping

        # Populate the label_matrix, entries, and values
        for label, cl_label, keyList in zip(labels, self.classifier_labels, keyLists):
            self.label_matrix += ([cl_label] * len(keyList))
            self.entries += zip([label] * len(keyList), keyList)

            if labels_only:
                self.values += []
            else:
                def get_data(k):
                    d = self.cache.get_object_data(k)
                    if callback is not None:
                        callback(num_fetched[0] / float(num_to_fetch))
                    num_fetched[0] = num_fetched[0] + 1
                    return d
                self.values += [get_data(k) for k in keyList]

        self.label_matrix = numpy.array(self.label_matrix)
        self.values = numpy.array(self.values, np.float64)


    def Load(self, filename, labels_only=False):
        self.Clear()
        f = open(filename, 'U')
        lines = f.read()
#        lines = lines.replace('\r', '\n')    # replace CRs with LFs
        lines = lines.split('\n')
        labelDict = collections.OrderedDict()
        for l in lines:
            try:
                if l.strip()=='': continue
                if l.startswith('#'):
                    self.cache.load_from_string(l[2:])
                    continue
                
                label = l.strip().split(' ')[0]
                if (label == "label"):
                    for labelname in l.strip().split(' ')[1:]:
                        if labelname not in labelDict.keys():
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
        self.Create(labelDict.keys(), labelDict.values(), labels_only=labels_only)
        
        f.close()
        
    def Renumber(self, label_dict):
        from properties import Properties
        obkey_length = 3 if Properties.getInstance().table_id else 2
        
        have_asked = False
        progress = None
        for label in label_dict.keys():
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
                            total = sum([len(v) for v in label_dict.values()])
                            done = 0
                            progress = wx.ProgressDialog("Remapping", "0%", maximum=total, style=wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
                        label_dict[label][idx] = db.GetObjectNear(obkey[:-1], x, y, silent=True)
                        done = done + 1
                        cont, skip = progress.Update(done, '%d%%'%((100 * done) / total))
                        if not cont:
                            label_dict.clear()
                            return
                        
        have_asked = False
        for label in label_dict.keys():
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
        self.cache.clear_if_objects_modified()

        f = open(filename, 'w')
        try:
            from properties import Properties
            p = Properties.getInstance()
            f.write('# Training set created while using properties: %s\n'%(p._filename))
            f.write('label '+' '.join(self.labels)+'\n')
            for label, obKey in self.entries:
                line = '%s %s %s\n'%(label, ' '.join([str(int(k)) for k in obKey]), ' '.join([str(int(k)) for k in db.GetObjectCoords(obKey)]))
                f.write(line)
            f.write('# ' + self.cache.save_to_string([k[1] for k in self.entries]) + '\n')
        except:
            logging.error("Error saving training set %s" % (filename))
            f.close()
            raise
        f.close()
        logging.info('Training set saved to %s'%filename)
        self.saved = True
            

    def get_object_keys(self):
        return [e[1] for e in self.entries]

class CellCache(Singleton):
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
            date, colnames, oldcache = cPickle.loads(zlib.decompress(base64.b64decode(str)))
        except:
            # silent failure
            return
        # Strings started sneaking into some caches when we started classifying entire images.
        # Detect this case and force an update to flush them.
        if len(oldcache) > 0:
            if oldcache.values()[0].dtype.kind == 'S':
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
        return base64.b64encode(zlib.compress(cPickle.dumps(output)))

    def get_object_data(self, key):
        if key not in self.data:
            self.data[key] = db.GetCellData(key)
        return self.data[key][self.col_indices]

    def clear_if_objects_modified(self):
        if not db.verify_objects_modify_date_earlier(self.last_update):
            self.data = {}
            self.last_update = db.get_objects_modify_date()
        

if __name__ == "__main__":
    from sys import argv
    from properties import Properties
    p = Properties.getInstance()
    p.LoadFile(argv[1])
    tr = TrainingSet(p)
    tr.Load(argv[2])
    for i in range(len(tr.labels)):
        print tr.labels[i],
        print " ".join([str(v) for v in tr.values[i]])
        
