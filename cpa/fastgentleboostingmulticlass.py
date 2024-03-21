
from numpy import *
import sys
from .fastgentleboostingworkermulticlass import train_weak_learner


def train(colnames, num_learners, label_matrix, values, fout=None, do_prof=False, test_values=None, callback=None):
    '''
    label_matrix is an n by k numpy array containing values of either +1 or -1
    values is the n by j numpy array of cell measurements
    n = #example cells, k = #classes, j = #measurements
    Return a list of learners.  Each learner is a tuple (column, thresh, a, b, average_margin),
    where column is an integer index into colnames
    '''
    if 0 in values.shape:
        # Nothing to train
        return None
    assert label_matrix.shape[0] == values.shape[0] # Number of training examples.
    computed_labels = zeros(label_matrix.shape, float32)
    num_examples, num_classes = label_matrix.shape
    do_tests = (test_values is not None)
    if do_tests:
        num_tests = test_values.shape[0]
        computed_test_labels = zeros((num_tests, num_classes), float32)
        test_labels_by_iteration = []
    # Set weights, normalize by number of examples
    weights = ones(label_matrix.shape, float32)
    margin_correct = zeros((num_examples, num_classes-1), float32)
    margin_incorrect = zeros((num_examples, num_classes-1), float32)
    for idx in range(num_classes):
        classmask = (label_matrix[:, idx] == 1).reshape((num_examples, 1))
        num_examples_class = sum(classmask)
        weights[tile(classmask, (1, num_classes))] /= num_examples_class
    balancing = weights.copy()
    
    def get_one_weak_learner(ctl=None, tlbi=None):
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

        # if we have test values, update their computed labels
        if ctl is not None:
            test_delta = reshape(test_values[:, column] > thresh, (num_tests, 1))
            test_feature_thresh_mask = tile(test_delta, (1, num_classes))
            test_adjustment = test_feature_thresh_mask * tile(a, (num_tests, 1)) + (1 - test_feature_thresh_mask) * tile(b, (num_tests, 1))
            ctl += test_adjustment
            tlbi += [ctl.argmax(axis=1)]

        return (err, colnames[int(column)], thresh, a, b, reweights, recomputed_labels, adjustment)

    weak_learners = []
    for weak_count in range(num_learners):
        if do_tests:
            err, colname, thresh, a, b, reweight, recomputed_labels, adjustment = get_one_weak_learner(ctl=computed_test_labels, tlbi=test_labels_by_iteration)
        else:
            err, colname, thresh, a, b, reweight, recomputed_labels, adjustment = get_one_weak_learner()

        # compute margins
        step_correct_class = adjustment[label_matrix > 0].reshape((num_examples, 1))
        step_relative = step_correct_class - (adjustment[label_matrix < 0].reshape((num_examples, num_classes - 1)))
        mask = (step_relative > 0)
        margin_correct += step_relative * mask
        margin_incorrect += (- step_relative) * (~ mask)
        expected_worst_margin = sum(balancing[:,0] * (margin_correct / (margin_correct + margin_incorrect)).min(axis=1)) / sum(balancing[:,0])

        computed_labels = recomputed_labels
        weak_learners += [(colname, thresh, a, b, expected_worst_margin)]

        if callback is not None:
            callback(weak_count / float(num_learners))

        if fout:
            colname, thresh, a, b, e_m = weak_learners[-1]
            fout.write("IF (%s > %s, %s, %s)\n" %
                       (colname, repr(thresh), 
                        "[" + ", ".join([repr(v) for v in a]) + "]", 
                        "[" + ", ".join([repr(v) for v in b]) + "]"))
        if err == 0.0:
            break
        weights = reweight
    if do_tests:
        return test_labels_by_iteration
    return weak_learners

def xvalidate(colnames, num_learners, label_matrix, values, folds, group_labels, progress_callback):
    # if everything's in the same group, ignore the labels
    if all([g == group_labels[0] for g in group_labels]):
        group_labels = list(range(len(group_labels)))
    
    # randomize the order of labels
    unique_labels = list(set(group_labels))
    random.shuffle(unique_labels)
    
    
    fold_min_size = len(group_labels) / float(folds)
    num_misclassifications = zeros(num_learners, int)
    
    # break into folds, randomly, but with all identical group_labels together
    for f in range(folds):
        print(("fold", f))
        current_holdout = [False] * len(group_labels)
        while unique_labels and (sum(current_holdout) < fold_min_size):
            to_add = unique_labels.pop()
            current_holdout = [(a or b) for a, b in zip(current_holdout, [g == to_add for g in group_labels])]
        
        if sum(current_holdout) == 0:
            print("no holdout")
            break

        holdout_idx = nonzero(current_holdout)[0]
        current_holdin = ~ array(current_holdout)
        holdin_idx = nonzero(current_holdin)[0]
        holdin_labels = label_matrix[holdin_idx, :]
        holdin_values = values[holdin_idx, :]
        holdout_values = values[holdout_idx, :]
        holdout_results = train(colnames, num_learners, holdin_labels, holdin_values, test_values=holdout_values)
        if holdout_results is None:
            return None
        # pad the end of the holdout set with the last element
        if len(holdout_results) < num_learners:
            holdout_results += [holdout_results[-1]] * (num_learners - len(holdout_results))
        holdout_labels = label_matrix[holdout_idx, :].argmax(axis=1)
        num_misclassifications += [sum(hr != holdout_labels) for hr in holdout_results]
        if progress_callback:
            progress_callback(f / float(folds))

    return [num_misclassifications]
        

def usage(name):
    print(("usage %s:"%(name)))
    print(("%s num_learners              - read from stdin, write to stdout"%(name)))
    print(("%s num_learners file         - read from file, write to stdout"%(name)))
    print(("%s num_learners file1 file2  - read from file1, write to file2"%(name)))
    print("")
    print("Input files should be tab delimited.")
    print("Example:")
    print("ClassLabel	Value1_name	Value2_name	Value3_name")
    print("2	0.1	0.3	1.5")
    print("1	0.5	-0.3	0.5")
    print("3	0.1	1.0	0.5")
    print("")
    print("Labels should be positive integers.")
    print("Note that if one learner is sufficient, only one will be written.")
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

    import csv
    reader = csv.reader(fin, delimiter='	')
    header = next(reader)
    label_to_labelidx = {}
    curlabel = 1
    def get_numlabel(strlabel):
        if strlabel in label_to_labelidx:
            return label_to_labelidx[strlabel]
        global curlabel
        print(("LABEL: ", curlabel, strlabel))
        label_to_labelidx[strlabel] = curlabel
        curlabel += 1
        return label_to_labelidx[strlabel]

#     l1 = header.index('MountingMedium')
#     l2 = header.index('WormStrain')
#     plate = header.index('Image_Metadata_Plate')
#     colnames = header[plate + 1:]
#     labels = []
#     values = []
#     for vals in reader:
#         strlabel = "%s-%s"%(vals[l1], vals[l2])
#         if 'NoVecta' not in strlabel:
#             continue
#         numlabel = get_numlabel(strlabel)
#         if '\\N' in vals:
#             continue
#         values.append([float(v) if v != '\\N' else 0 for v in vals[plate + 1:]])
#         labels.append(numlabel)
#         
#     labels = array(labels).astype(int32)
#     values = array(values).astype(float32)
#     
#     exclude = array([('bubble' in c) or ('dark_w' in c) for c in colnames])
#     values = values[:, nonzero(~exclude)[0]]
#     colnames = [c for c in colnames if not (('bubble' in c) or ('dark_w' in c))]
#     
#     assert len(colnames) == values.shape[1]


    colnames = header[1:]
    labels = []
    values = []
    for vals in reader:
        values.append([0 if v == 'None' else float(v) for v in vals[1:]])
        numlabel = get_numlabel(vals[0])
        labels.append(numlabel)

    labels = array(labels).astype(int32)
    values = array(values).astype(float32)
        

    # convert labels to a matrix with +1/-1 values only (+1 in the column matching the label, 1-indexed)
    num_classes = max(labels)
    label_matrix = -ones((len(labels), num_classes), int32)
    for i, j in zip(list(range(len(labels))), array(labels)-1):
        label_matrix[i, j] = 1

    wl = train(colnames, num_learners, label_matrix, values, fout)
    for w in wl:
        print(w)
    print((label_matrix.shape, "groups"))
    print((xvalidate(colnames, num_learners, label_matrix, values, 20, list(range(1, label_matrix.shape[0]+1)), None)))

