from sys import stderr
from numpy import array
from DBConnect import DBConnect

db = DBConnect.getInstance()

class TrainingSet:
    "A class representing a set of manually labeled cells."

    def __init__(self, properties, filename=''):
        self.properties = properties
        self.colnames = db.GetColnamesForClassifier()
        self.filename = filename
        if filename != '':
            self.Load(filename)


    def Clear(self):
        self.saved = False
        self.labels = []                # set of possible class labels (human readable)
        self.classifier_labels = []     # set of possible class labels (for classifier)
                                        #     eg: [[+1,-1,-1], [-1,+1,-1], [-1,-1,+1]]
        self.label_matrix = []          # array of classifier labels for each sample
        self.values = []                # array of measurements (data from db) for each sample
        self.entries = []               # list of (label, obKey) pairs
            
            
    def Create(self, labels, keyLists):
        '''
        labels:   list of class labels
                  Example: ['pos','neg','other']
        keyLists: list of lists of obKeys in the respective classes
                  Example: [[k1,k2], [k3], [k4,k5,k6]] 
        '''
        assert len(labels)==len(keyLists), 'Class labels and keyLists must be of equal size.'
        self.Clear()
        self.labels = array(labels)
        self.classifier_labels = []
        for i in range(len(labels)):
            self.classifier_labels += [[-1 for j in labels]]
            self.classifier_labels[-1][i] = 1
        
        # Populate the label_matrix, entries, and values
        for label, cl_label, keyList in zip(labels, self.classifier_labels, keyLists):
            for obKey in keyList:
                self.label_matrix.append(cl_label)
                self.entries.append((label,obKey))
                self.values.append(db.GetCellDataForClassifier(obKey))
        self.label_matrix = array(self.label_matrix)
        self.values = array(self.values)


    def Load(self, filename):
        self.Clear()
        f = open(filename, 'U')
        lines = f.read()
#        lines = lines.replace('\r', '\n')    # replace CRs with LFs
        lines = lines.split('\n')
        for l in lines:
            try:
                if l.strip()=='' or l.startswith('#'):
                    continue
                label = l.strip().split(' ')[0]
                if (label == "label"):
                    self.labels = l.strip().split(' ')[1:]
                    continue
                if label not in self.labels:
                    self.labels += [label]
                obKey = tuple([int(float(k)) for k in l.strip().split(' ')[1:]])
            except:
                print >>stderr, "error parsing training set %s, line >>>%s<<<"%(filename, l.strip())
                f.close()
                raise

            self.entries.append((label, obKey))
            self.values.append(db.GetCellDataForClassifier(obKey))

        self.labels = array(self.labels)
        self.values = array(self.values)
        
        f.close()
        
        
    def Save(self, filename):
        f = open(filename, 'w')
        try:
            from Properties import Properties
            p = Properties.getInstance()
            f.write('# Training set created while using properties: %s\n'%(p._filename))
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
    tr.Load(argv[2])
    for i in range(len(tr.labels)):
        print tr.labels[i],
        print " ".join([str(v) for v in tr.values[i]])
        
