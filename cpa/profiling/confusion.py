import numpy as np

def load_confusion(filename):
    confusion = {}
    for line in open(filename).readlines():
        a, b, v = line.rstrip().split('\t')
        confusion[a, b] = float(v)
    return confusion

def confusion_matrix(confusion, dtype=int):
   labels = set()
   for a, b in confusion.keys():
      labels.add(a)
      labels.add(b)
   labels = sorted(labels)
   cm = np.zeros((len(labels), len(labels)), dtype=dtype)
   for (a, b), count in confusion.items():
      cm[labels.index(a), labels.index(b)] = count
   return cm

def confusion_reduce(operation, confusions):
   d = confusions[0].copy()
   for c in confusions[1:]:
      for k, v in c:
         d[k] = operation(d[k], v)
   return d

def write_confusion(confusion, stream):
    for (a, b), v in confusion.items():
        print >>stream, '\t'.join([' '.join(a), ' '.join(b), str(v)])
