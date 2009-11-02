from numpy import *
import sys
from FastGentleBoostingWorkerMulticlass import train_weak_learner


def train(colnames, num_learners, label_matrix, values, fout=None, do_prof=False):
    '''
    label_matrix is an n by k numpy array containing values of either +1 or -1
    values is the n by j numpy array of cell measurements
    n = #example cells, k = #classes, j = #measurements
    Return a list of learners.  Each learner is a tuple (column, thresh, a, b, average_margin),
    where column is an integer index into colnames
    '''
    assert label_matrix.shape[0] == values.shape[0] # Number of training examples.
    computed_labels = zeros(label_matrix.shape, float32)
    num_examples, num_classes = label_matrix.shape
    # Set weights, normalize by number of examples
    weights = ones(label_matrix.shape, float32)
    margin_correct = zeros((num_examples, num_classes-1), float32)
    margin_incorrect = zeros((num_examples, num_classes-1), float32)
    for idx in range(num_classes):
        classmask = (label_matrix[:, idx] == 1).reshape((num_examples, 1))
        num_examples_class = sum(classmask)
        weights[tile(classmask, (1, num_classes))] /= num_examples_class
    balancing = weights.copy()
    
    def get_one_weak_learner():
        
        best_error = float(Infinity)
        for feature_idx in range(values.shape[1]):
            thresh, err, a, b = train_weak_learner(label_matrix, weights, values[:, feature_idx])
            if err < best_error:
                best_error = err
                bestvals = (err, feature_idx, thresh, a, b)
        err, column, thresh, a, b = bestvals
        # recompute weights
        delta = reshape(values[:, column] > thresh, (num_examples, 1))
        feature_thresh_mask = tile(delta, (1, num_classes))
        adjustment = feature_thresh_mask * tile(a, (num_examples, 1)) + (1 - feature_thresh_mask) * tile(b, (num_examples, 1))
        recomputed_labels = computed_labels + adjustment
        reweights = balancing * exp(- recomputed_labels * label_matrix)
        reweights = reweights / sum(reweights)
        return (err, colnames[int(column)], thresh, a, b, reweights, recomputed_labels, adjustment)

    weak_learners = []
    for weak_count in range(num_learners):
        err, colname, thresh, a, b, reweight, recomputed_labels, adjustment = get_one_weak_learner()
        step_correct_class = adjustment[label_matrix > 0].reshape((num_examples, 1))
        step_relative = step_correct_class - (adjustment[label_matrix < 0].reshape((num_examples, num_classes - 1)))
        mask = (step_relative > 0)
        margin_correct += step_relative * mask
        margin_incorrect += (- step_relative) * (~ mask)
        expected_worst_margin = sum(balancing[:,0] * (margin_correct / (margin_correct + margin_incorrect)).min(axis=1)) / sum(balancing[:,0])

        computed_labels = recomputed_labels
        weak_learners += [(colname, thresh, a, b, expected_worst_margin)]
        if fout:
            colname, thresh, a, b, e_m = weak_learners[-1]
            fout.write("IF (%s > %s, %s, %s)\n" %
                       (colname, repr(thresh), "[" + ", ".join([repr(v) for v in a]) + "]", "[" + ", ".join([repr(v) for v in b]) + "]"))
        if err == 0.0:
            break
        weights = reweight

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
