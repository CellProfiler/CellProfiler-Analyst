from sys import stderr
from numpy import array

from DBConnect import DBConnect

db = DBConnect.getInstance()

class TrainingSet:
    "A class representing a set of manually labeled cells."

    def __init__(self, properties, filename='', include_group_info=False):
        self.properties = properties
        self.colnames = db.GetColnamesForClassifier()
        self.filename = filename
        if filename != '':
            self.Load(filename, include_group_info)


    def Clear(self):
        self.saved = False
        self.labels = []
        self.values = []
        self.groups = []
        self.entries = []
            
            
    def Create(self, labels, keyLists):
        '''
        labels   = ['class1', 'class2', ... ]
        keyLists = [[k1,k2,..], [k1,k2,..], ... ]
        '''
        assert len(labels)==len(keyLists), 'Class labels and keyLists must be of equal size.'
        self.Clear()
        self.labels = array(labels)
        
        for label, keyList in zip(labels,keyLists):
            for obKey in keyList:
                self.entries.append((label,obKey))
                self.values.append(db.GetCellDataForClassifier(obKey))
        
        self.values = array(self.values)


    def Load(self, filename, include_group_info=False):
        self.Clear()
        f = open(filename)
        for l in f:
            try:
                label = l.strip().split(' ')[0]
                if (label == "label"):
                    self.labels = l.strip().split(' ')[1:]
                    continue
                obKey = tuple([int(float(k)) for k in l.strip().split(' ')[1:]])
            except:
                print >>stderr, "error parsing training set %s, line >>>%s<<<"%(filename, l.strip())
                f.close()
                raise

            self.entries.append((label, obKey))
            self.values.append(db.GetCellDataForClassifier(obKey))
            if include_group_info:
                self.groups.append(db.GetCellGroup(obKey[:-1]))
            else:
                self.groups.append(obKey[:-1])

        self.labels = array(self.labels)
        self.values = array(self.values)
        
        f.close()
        
        
    def Save(self, filename):
        f = open(filename, 'w')
        try:
            f.write('label '+' '.join(self.labels)+'\n')
            for label, obKey in self.entries:
                line = label+' '+' '.join([str(int(k)) for k in obKey])+'\n'
                f.write(line)
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


if __name__ == "__main__":
    from sys import argv
    from Properties import Properties
    prop = Properties(argv[1])
    tr = TrainingSet(prop)
    tr.Load(argv[2], False)
    for i in range(len(tr.labels)):
        print tr.labels[i],
        print " ".join([str(v) for v in tr.values[i]])
        
