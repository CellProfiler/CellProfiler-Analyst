from sys import stderr
import numpy
import cPickle
import base64
import zlib
from DBConnect import DBConnect
from Singleton import Singleton

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
            
            
    def Create(self, labels, keyLists, labels_only=False):
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
        

        # Populate the label_matrix, entries, and values
        for label, cl_label, keyList in zip(labels, self.classifier_labels, keyLists):
            self.label_matrix += ([cl_label] * len(keyList))
            self.entries += zip([label] * len(keyList), keyList)
            self.values += ([] if labels_only else [self.cache.get_object_data(k) for k in keyList])

        self.label_matrix = numpy.array(self.label_matrix)
        self.values = numpy.array(self.values)


    def Load(self, filename, labels_only=False):
        self.Clear()
        f = open(filename, 'U')
        lines = f.read()
#        lines = lines.replace('\r', '\n')    # replace CRs with LFs
        lines = lines.split('\n')
        labelDict = {}
        for l in lines:
            try:
                if l.strip()=='': continue
                if l.startswith('#'):
                    self.cache.load_from_string(l[2:])
                    continue

                label = l.strip().split(' ')[0]
                if (label == "label"): continue
                
                obKey = tuple([int(float(k)) for k in l.strip().split(' ')[1:]])
                if label not in labelDict.keys():
                    labelDict[label] = [obKey]
                else:
                    labelDict[label] += [obKey]
            except:
                print >>stderr, "error parsing training set %s, line >>>%s<<<"%(filename, l.strip())
                f.close()
                raise
            
        self.Create(labelDict.keys(), labelDict.values(), labels_only=labels_only)
        
        f.close()
        
        
    def Save(self, filename):
        # check cache freshness
        self.cache.clear_if_objects_modified()

        f = open(filename, 'w')
        try:
            from Properties import Properties
            p = Properties.getInstance()
            f.write('# Training set created while using properties: %s\n'%(p._filename))
            f.write('label '+' '.join(self.labels)+'\n')
            for label, obKey in self.entries:
                line = label+' '+' '.join([str(int(k)) for k in obKey])+'\n'
                f.write(line)
            f.write('# ' + self.cache.save_to_string([k[1] for k in self.entries]) + '\n')
        except:
            print >>stderr, "error saving training set %s" % (filename)
            f.close()
            raise
        f.close()
        print 'training set saved to',filename
        self.saved = True
            

    def Subset(self, mask):
        sub = TrainingSet(self.properties)
        sub.colnames = self.colnames
        sub.labels = self.labels[mask]
        sub.values = self.values[mask]
        sub.groups = [self.groups[i] for i in range(len(self.groups)) if mask[i]]
        return sub

class CellCache(Singleton):
    "caching frontend for holding cell data"
    
    def __init__(self):
        self.data = {}
        self.last_update = db.get_objects_modify_date()

    def load_from_string(self, str):
        'load data from a string, verifying that the table has not changed since it was created (encoded in string)'
        try:
            date, oldcache = cPickle.loads(zlib.decompress(base64.b64decode(str)))
        except:
            # silent failure
            return
        # verify the database hasn't been changed
        if db.verify_objects_modify_date_earlier(date):
            self.data.update(oldcache)

    def save_to_string(self, keys):
        'convert the cache data to a string, but only for certain keys'
        temp = {}
        for k in keys:
            if k in self.data:
                temp[k] = self.data[k]
        output = (db.get_objects_modify_date(), temp)
        return base64.b64encode(zlib.compress(cPickle.dumps(output)))

    def get_object_data(self, key):
        if key not in self.data:
            self.data[key] = db.GetCellDataForClassifier(key)
        return self.data[key]

    def clear_if_objects_modified(self):
        if not db.verify_objects_modify_date_earlier(self.last_update):
            self.data = {}
            self.last_update = db.get_objects_modify_date()
        

if __name__ == "__main__":
    from sys import argv
    from Properties import Properties
    p = Properties.getInstance()
    p.LoadFile(argv[1])
    tr = TrainingSet(p)
    tr.Load(argv[2])
    for i in range(len(tr.labels)):
        print tr.labels[i],
        print " ".join([str(v) for v in tr.values[i]])
        
