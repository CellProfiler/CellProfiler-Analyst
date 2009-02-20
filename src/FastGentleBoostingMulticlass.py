from numpy import *
import subprocess, os, sys


def train(colnames, num_learners, label_matrix, values, fout=None, do_prof=False):
    '''
    label_matrix is an n by k numpy array containing values of either +1 or -1
    values is the n by j numpy array of cell measurements
    n = #example cells, k = #classes, j = #measurements
    Return a list of learners.  Each learner is a tuple (column, thresh, a, b),
    where column is an integer index into colnames
    '''
    assert label_matrix.shape[0] == values.shape[0] # Number of training examples.
    computed_labels = zeros(label_matrix.shape, float32)
    num_examples, num_classes = label_matrix.shape
    # Set weights, normalize by number of examples
    weights = ones(label_matrix.shape, float32)
    for idx in range(num_classes):
        classmask = (label_matrix[:, idx] == 1).reshape((num_examples, 1))
        num_examples_class = sum(classmask)
        weights[tile(classmask, (1, num_classes))] /= num_examples_class
    
    nworkers = int(os.getenv("NWORKERS") or 2)
    workers = range(nworkers)
    ncols = shape(values)[1]
    basecols = zeros((nworkers,))
    for i in range(nworkers):
        worker_path = os.path.join(sys.path[0], __import__('FastGentleBoostingWorkerMulticlass', globals()).__file__)
        
        if worker_path[-3:] == 'pyc':
            worker_path = worker_path[:-1]
        if os.name == 'nt':   # Windows
            worker_path = "python \""+worker_path+"\""
        else:
            worker_path = [sys.executable, worker_path]

        if (i == 0) and do_prof:
            workers[i] = subprocess.Popen([worker_path,"doprof"],
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE)
        else:
            workers[i] = subprocess.Popen(worker_path,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE)
        if os.name == 'nt':   # Windows
            import msvcrt
            msvcrt.setmode(workers[i].stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(workers[i].stdout.fileno(), os.O_BINARY)  
        slice_start = int(floor(i * ncols / float(nworkers)))
        slice_end = int(floor((i+1) * ncols / float(nworkers)))
        basecols[i] = slice_start
        array([shape(values)[0], slice_end - slice_start], int32).tofile(workers[i].stdin)
        array([label_matrix.shape[1]], int32).tofile(workers[i].stdin)
        values[:, slice_start:slice_end].astype(float32).tofile(workers[i].stdin)
        label_matrix.astype(int32).tofile(workers[i].stdin)

    def get_one_weak_learner():
        best = float(Infinity)
        for i in range(nworkers):
            workers[i].stdin.write("not done yet\n")
            weights.astype(float32).tofile(workers[i].stdin)
            workers[i].stdin.flush()
        for i in range(nworkers):
            err, column, thresh = fromfile(workers[i].stdout, float32, 3)
            a = fromfile(workers[i].stdout, float32, num_classes)
            b = fromfile(workers[i].stdout, float32, num_classes)
            column = int(column) + basecols[i]
            if err < best:
                best = err
                bestvals = (err, column, thresh, a, b)
        err, column, thresh, a, b = bestvals
        # recompute weights
        delta = reshape(values[:, column] > thresh, (num_examples, 1))
        feature_thresh_mask = tile(delta, (1, num_classes))
        recomputed_labels = computed_labels + feature_thresh_mask * tile(a, (num_examples, 1)) + (1 - feature_thresh_mask) * tile(b, (num_examples, 1))
        reweights = exp(- recomputed_labels * label_matrix)
        reweights = reweights / sum(reweights)


        return (err, int(column), thresh, a, b, reweights, recomputed_labels)

    def shutdown():
        for i in range(0, nworkers):
            workers[i].stdin.write("done\n")
            workers[i].stdin.close()
        

    weak_learners = []
    for weak_count in range(num_learners):
        err, column, thresh, a, b, reweight, recomputed_labels = get_one_weak_learner()
        computed_labels = recomputed_labels
        weak_learners += [(column, thresh, a, b)]
        if fout:
            column, thresh, a, b = weak_learners[-1]
            fout.write("IF (%s > %s, %s, %s)\n" %
                       (colnames[column], repr(thresh), "[" + ", ".join([repr(v) for v in a]) + "]", "[" + ", ".join([repr(v) for v in b]) + "]"))
            fout.flush()
        if err == 0.0:
            break
        weights = reweight

    shutdown()
    return weak_learners


def usage(name):
    print "usage %s:"%(name)
    print "%s num_learners              - read from stdin, write to stdout"%(name)
    print "%s num_learners file         - read from file, write to stdout"%(name)
    print "%s num_learners file1 file2  - read from file1, write to file2"%(name)
    print ""
    print "Input files should be tab delimited."
    print "Example:"
    print "ClassLabel	Value1_name	Value2_name	Value3_name"
    print "2	0.1	0.3	1.5"
    print "1	0.5	-0.3	0.5"
    print "3	0.1	1.0	0.5"
    print ""
    print "Labels should be positive integers."
    print "Note that if one learner is sufficient, only one will be written."
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        fin = sys.stdin
        fout = sys.stdout
    elif len(sys.argv) == 3:
        fin = open(sys.argv[2])
        fout = sys.stdout
    elif len(sys.argv) == 4:
        fin = open(sys.argv[2])
        fout = open(sys.argv[3], 'w')
    else:
        usage(sys.argv[0])

    num_learners = int(sys.argv[1])
    assert num_learners > 0

    colnames = fin.readline().rstrip().split(' ')[1:]
    labels = []
    values = []
    rawdata = loadtxt(fin)
    labels = rawdata[:, 0].astype(int32)
    values = rawdata[:, 1:].astype(float32)

    # convert labels to a matrix with +1/-1 values only (+1 in the column matching the label, 1-indexed)
    num_classes = max(labels)
    label_matrix = -ones((len(labels), num_classes), int32)
    for i, j in zip(range(len(labels)), array(labels)-1):
        label_matrix[i, j] = 1

    wl = train(colnames, num_learners, label_matrix, values, fout)
    from MulticlassSQL import translate
    translate(wl, colnames, 'CPA_per_object', 'TEMP')
    sys.exit(0)
