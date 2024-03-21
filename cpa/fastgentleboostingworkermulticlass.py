#!/usr/bin/env python
#
# Worker script called from FastGentleBoosting.py.

from sys import stdin, stdout, stderr, argv
from numpy import *

def train_weak_learner(labels, weights, values):
    ''' For a multiclass training set, with C classes and N examples,
    finds the optimal weak learner in O(M * N logN) time.
    Optimality is defined by Eq. 7 of Torralba et al., 'Sharing visual
    features...', 2007, IEEE PAMI.

    We differ from Torralba et al. in two ways:
    - we do not share a's and b's between classes
    - we always solve for the complete set of examples, regardless of label

    Labels should be 1 and -1, only.
    label_matrix and weights are NxC.
    values is Nx1
    '''
    
    global order, s_values, s_labels, s_weights, s_weights_times_labels, num_a, den_a, a, b, sless0, sgrtr0, w_below_neg, w_below_pos, w_above_neg, w_above_pos, J

    # Sort labels and weights by values (AKA possible thresholds).  By
    # default, argsort is not stable, so the results will vary
    # slightly with the number of workers.  Add kind="mergesort" to
    # get a stable sort, which avoids this.
    order = argsort(values)
    s_values = values[order]
    s_labels = labels[order, :]
    s_weights = weights[order, :]

    # useful subfunction
    num_examples = labels.shape[0]
    def tilesum(a):
        return tile(sum(a, axis=0), (num_examples, 1))

    # Equations 9 and 10 of Torralba et al.
    s_weights_times_labels = s_weights * s_labels
    num_a = (tilesum(s_weights_times_labels) - cumsum(s_weights_times_labels, axis=0))
    den_a = (tilesum(s_weights) - cumsum(s_weights, axis=0))
    den_a[den_a <= 0.0] = 1.0 # avoid div by zero
    a = num_a / den_a
    b = cumsum(s_weights_times_labels, axis=0) / cumsum(s_weights, axis=0)

    # We need, at each index, the total weights below and above,
    # separated by positive and negative label.  Below includes the
    # current index
    sless0 = (s_labels < 0)
    sgrtr0 = (s_labels > 0)
    w_below_neg = cumsum(s_weights * sless0, axis=0)
    w_below_pos = cumsum(s_weights * sgrtr0, axis=0)
    w_above_neg = tilesum(s_weights * sless0) - w_below_neg
    w_above_pos = tilesum(s_weights * sgrtr0) - w_below_pos

    # Now evaluate the error at each threshold.
    # (see Equation 7, and note that we're assuming -1 and +1 for entries in the label matrix.
    J = w_below_neg * ((-1 - b)**2) + w_below_pos * ((1 - b)**2) + w_above_neg * ((-1 - a)**2) + w_above_pos * ((1 - a)**2)
    J = J.sum(axis=1)

    # Find index of least error
    idx = argmin(J)

    # make sure we're at the top of this thresh
    while (idx+1 < len(s_values)) and (s_values[idx] == s_values[idx + 1]):
        idx += 1

    # return the threshold at that index
    return s_values[idx], J[idx], a[idx, :].copy(), b[idx, :].copy()

def train_classifier(labels, values, iterations):
    # make sure these are arrays (not matrices)
    labels = array(labels)
    values = array(values)

    num_examples = labels.shape[0]

    learners = []
    weights = ones(labels.shape)
    output = zeros(labels.shape)
    for n in range(iterations):
        best_error = float(Infinity)

        for feature_idx in range(values.shape[1]):
            val, err, a, b = train_weak_learner(labels, weights, values[:, feature_idx])
            if err < best_error:
                best_error = err
                best_idx = feature_idx
                best_val = val
                best_a = a
                best_b = b

        delta = values[:, best_idx] > best_val
        delta.shape = (len(delta), 1)
        feature_thresh_mask = tile(delta, (1, labels.shape[1]))
        output = output + feature_thresh_mask * tile(best_a, (num_examples, 1)) + (1 - feature_thresh_mask) * tile(best_b, (num_examples, 1))
        weights = exp(- output * labels)
        weights = weights / sum(weights)
        err = sum((output * labels) <= 0)
    return

def myfromfile(stream, type, sh):
    if len(sh) == 2:
        tot = sh[0] * sh[1]
    else:
        tot = sh[0]
    result = fromfile(stream, type, tot)
    result.shape = sh
    return result

def doit():
    testing = False
    n, ncols = myfromfile(stdin, int32, (2,))
    num_classes = myfromfile(stdin, int32, (1,))[0]
    values = myfromfile(stdin, float32, (n, ncols))
    label_matrix = myfromfile(stdin, int32, (n, num_classes))

    while True:
        # It would be cleaner to tell the worker we're done by just
        # closing the stream, but numpy does strange things (prints
        # error message, signals MemoryError) when myfromfile cannot
        # read as many bytes as expected.
        if stdin.readline() == "done\n":
            return
        weights = myfromfile(stdin, float32, (n, num_classes))

        best = float(Infinity)
        for column in range(ncols):
            colvals = values[:, column]
            # print >>stderr, "WORK", column, label_matrix, weights, colvals
            thresh, err, a, b = train_weak_learner(label_matrix, weights, colvals)
            if err < best:
                best = err
                bestvals = (err, column, thresh, a, b)

        err, column, thresh, a, b = bestvals
        array([err, column, thresh], float32).tofile(stdout)
        a.astype(float32).tofile(stdout)
        b.astype(float32).tofile(stdout)
        stdout.flush()



if __name__ == '__main__':
    try:
        import dl
        h = dl.open('change_malloc_zone.dylib')
        h.call('setup')
    except:
        pass
    if len(argv) != 1:
        import cProfile
        cProfile.runctx("doit()", globals(), locals(), "worker.cprof")
    else:
        try: # Use binary I/O on Windows
            import msvcrt, os
            try:
                msvcrt.setmode(stdin.fileno(), os.O_BINARY)
            except:
                stderr.write("Couldn't deal with stdin\n")
                pass
            try:
                msvcrt.setmode(stdout.fileno(), os.O_BINARY)
                stderr.write("Couldn't deal with stdout\n")
            except:
                pass
        except ImportError:
            pass
        doit()
    try:
        h.call('teardown')
    except:
        pass
