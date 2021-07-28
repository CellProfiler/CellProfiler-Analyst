
import re
from . import dbconnect
import logging
from . import multiclasssql_legacy as multiclasssql # Legacy code for scoring cells
import numpy as np
import matplotlib.pyplot as plt
from sys import stdin, stdout, argv, exit
from time import time


class FastGentleBoosting(object):
    def __init__(self, classifier = None):
        logging.info('Initialized New Classifier: FastGentleBoosting')
        self.name = self.name()
        self.model = None
        self.classBins = []
        self.classifier = classifier
        self.scaler = None
        self.features = []

    # Set features
    def _set_features(self, features):
        self.features = features

    def name(self):
        return self.__class__.__name__

    def CheckProgress(self):
        import wx
        ''' Called when the Cross Validation Button is pressed. '''
        # get wells if available, otherwise use imagenumbers
        try:
            nRules = int(self.classifier.nRulesTxt.GetValue())
        except:
            logging.error('Unable to parse number of rules')
            return

        if not self.classifier.UpdateTrainingSet():
            self.PostMessage('Cross-validation canceled.')
            return

        
        db = dbconnect.DBConnect()
        groups = [db.get_platewell_for_object(key) for key in self.classifier.trainingSet.get_object_keys()]

        t1 = time()
        dlg = wx.ProgressDialog('Computing cross validation accuracy...', '0% Complete', 100, self.classifier, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)        
        base = 0.0
        scale = 1.0

        class StopXValidation(Exception):
            pass

        def progress_callback(amount):
            pct = min(int(100 * (amount * scale + base)), 100)
            cont, skip = dlg.Update(pct, '%d%% Complete'%(pct))
            self.classifier.PostMessage('Computing cross validation accuracy... %s%% Complete'%(pct))
            if not cont:
                raise StopXValidation

        # each round of xvalidation takes about (numfolds * (1 - (1 / num_folds))) time
        step_time_1 = (2.0 * (1.0 - 1.0 / 2.0))
        step_time_2 = (20.0 * (1.0 - 1.0 / 20.0))
        scale = step_time_1 / (10 * step_time_1 + step_time_2)

        xvalid_50 = []

        try:
            n_iter = 1
            for i in range(10):
                xval = self.XValidate(
                    self.classifier.trainingSet.colnames, nRules, self.classifier.trainingSet.label_matrix,
                    self.classifier.trainingSet.values, 2, groups, progress_callback)
                if xval is not None:
                    xvalid_50 += xval
                    n_iter += 1

                # each round makes one "scale" size step in progress
                base += scale
            xvalid_50 = sum(xvalid_50) / float(n_iter)

            # only one more step
            scale = 1.0 - base
            xvalid_95 = self.XValidate(
                self.classifier.trainingSet.colnames, nRules, self.classifier.trainingSet.label_matrix,
                self.classifier.trainingSet.values, 20, groups, progress_callback)

            dlg.Destroy()
            figure = plt.figure()
            plt.clf()
            plt.plot()
            plt.plot(list(range(1, nRules + 1)), 1.0 - xvalid_50 / float(len(groups)), 'r', label='50% cross-validation accuracy')
            plt.plot(list(range(1, nRules + 1)), 1.0 - xvalid_95[0] / float(len(groups)), 'b', label='95% cross-validation accuracy')
            chance_level = 1.0 / len(self.classifier.trainingSet.labels)
            plt.plot([1, nRules + 1], [chance_level, chance_level], 'k--', label='accuracy of random classifier')
            plt.legend(loc='lower right')
            plt.xlabel('Rule #')
            plt.ylabel('Accuracy')
            plt.xlim(1, max(nRules,2))
            plt.ylim(-0.05, 1.05)
            plt.title('Cross-validation accuracy')
            plt.show()
            self.classifier.PostMessage('Cross-validation complete in %.1fs.'%(time()-t1))
        except StopXValidation:
            dlg.Destroy()

    def ClearModel(self):
        self.classBins = []
        self.model = None

    # Adjust text for the classifier rules panel
    def panelTxt(self):
        return 'with'

    def panelTxt2(self):
        return 'max rules'

    def CreatePerObjectClassTable(self, labels, updater=None):
        multiclasssql.create_perobject_class_table(labels, self.model)

    def FilterObjectsFromClassN(self, obClass, obKeysToTry):
        return multiclasssql.FilterObjectsFromClassN(obClass, self.model, obKeysToTry)

    def IsTrained(self):
        return self.model is not None

    def toggle_scaler(self, status):
        logging.info("Scaling is not supported by FastGentleBoosting, will have no effect")

    def LoadModel(self, model_filename):
        
        import joblib
        try:
            self.model, self.bin_labels, self.name = joblib.load(model_filename)
        except:
            self.model = None
            self.bin_labels = None
            logging.error('Loading trained model failed')
            raise TypeError

    def ParseModel(self, string):
        self.model = []
        string = string.replace('\r\n', '\n')
        for line in string.split('\n'):
            if line.strip() == '':
                continue
            m = re.match('^IF \((\w+) > (-{0,1}\d+\.\d+), \[(-{0,1}\d+\.\d+(?:, -{0,1}\d+\.\d+)*)\], \[(-{0,1}\d+\.\d+(?:, -{0,1}\d+\.\d+)*)\]\)',
                         line, flags=re.IGNORECASE)
            if m is None:
                raise ValueError
            colname, thresh, a, b = m.groups()
            thresh = float(thresh)
            a = list(map(float, a.split(',')))
            b = list(map(float, b.split(',')))
            if len(a) != len(b):
                raise ValueError('Alpha and beta must have the same cardinality in "IF (column > threshold, alpha, beta)"')
            self.model.append((colname, thresh, a, b, None))
        n_classes = len(self.model[0][2])
        for wl in self.model:
            if len(wl[2]) != n_classes:
                raise ValueError('Number of classes must remain the same between rules.')
        return self.model

    def PerImageCounts(self, filter_name=None, cb=None):
        return multiclasssql.PerImageCounts(self.model, filter_name=filter_name, cb=cb)

    def SaveModel(self, model_filename, bin_labels):

        # For loading scikit learn library
        import joblib
        joblib.dump((self.model, bin_labels, self.name), model_filename, compress=1)

    def ShowModel(self):
        '''
        Transforms the weak learners of the algorithm into a human readable
        representation
        '''
        if self.model is not None and self.model is not []:
            return '\n'.join("IF (%s > %s, %s, %s)" %(colname, repr(thresh),
                             "[" + ", ".join([repr(v) for v in a]) + "]",
                             "[" + ", ".join([repr(v) for v in b]) + "]")
                        for colname, thresh, a, b, e_m in self.model)
        else:
            return ''

    def Train(self, colnames, num_learners, label_matrix, values, fout=None, do_prof=False, test_values=None, callback=None):
        '''
        label_matrix is an n by k numpy array containing values of either +1 or -1
        values is the n by j numpy array of cell measurements
        n = #example cells, k = #classes, j = #measurements
        Return a list of learners.  Each learner is a tuple (column, thresh, a,
        b, average_margin), where column is an integer index into colnames
        '''
        if 0 in values.shape:
            # Nothing to train
            return None
        assert label_matrix.shape[0] == values.shape[0] # Number of training examples.
        computed_labels = np.zeros(label_matrix.shape, np.float32)
        num_examples, num_classes = label_matrix.shape
        do_tests = (test_values is not None)
        if do_tests:
            num_tests = test_values.shape[0]
            computed_test_labels = np.zeros((num_tests, num_classes), np.float32)
            test_labels_by_iteration = []
        # Set weights, normalize by number of examples
        weights = np.ones(label_matrix.shape, np.float32)
        margin_correct = np.zeros((num_examples, num_classes-1), np.float32)
        margin_incorrect = np.zeros((num_examples, num_classes-1), np.float32)
        for idx in range(num_classes):
            classmask = (label_matrix[:, idx] == 1).reshape((num_examples, 1))
            num_examples_class = sum(classmask)
            weights[np.tile(classmask, (1, num_classes))] /= num_examples_class
        balancing = weights.copy()

        def GetOneWeakLearner(ctl=None, tlbi=None):
            best_error = float(np.Infinity)
            for feature_idx in range(values.shape[1]):
                thresh, err, a, b = self.TrainWeakLearner(label_matrix, weights, values[:, feature_idx])
                if err < best_error:
                    best_error = err
                    bestvals = (err, feature_idx, thresh, a, b)
            err, column, thresh, a, b = bestvals
            # recompute weights
            delta = np.reshape(values[:, column] > thresh, (num_examples, 1))
            feature_thresh_mask = np.tile(delta, (1, num_classes))
            adjustment = feature_thresh_mask * np.tile(a, (num_examples, 1)) + (1 - feature_thresh_mask) * np.tile(b, (num_examples, 1))
            recomputed_labels = computed_labels + adjustment
            reweights = balancing * np.exp(- recomputed_labels * label_matrix)
            reweights = reweights / sum(reweights)

            # if we have test values, update their computed labels
            if ctl is not None:
                test_delta = np.reshape(test_values[:, column] > thresh, (num_tests, 1))
                test_feature_thresh_mask = np.tile(test_delta, (1, num_classes))
                test_adjustment = test_feature_thresh_mask * np.tile(a, (num_tests, 1)) + (1 - test_feature_thresh_mask) * np.tile(b, (num_tests, 1))
                ctl += test_adjustment
                tlbi += [ctl.argmax(axis=1)]

            return (err, colnames[int(column)], thresh, a, b, reweights, recomputed_labels, adjustment)

        self.model = []
        for weak_count in range(num_learners):
            if do_tests:
                err, colname, thresh, a, b, reweight, recomputed_labels, adjustment = GetOneWeakLearner(ctl=computed_test_labels, tlbi=test_labels_by_iteration)
            else:
                err, colname, thresh, a, b, reweight, recomputed_labels, adjustment = GetOneWeakLearner()

            # compute margins
            step_correct_class = adjustment[label_matrix > 0].reshape((num_examples, 1))
            step_relative = step_correct_class - (adjustment[label_matrix < 0].reshape((num_examples, num_classes - 1)))
            mask = (step_relative > 0)
            margin_correct += step_relative * mask
            margin_incorrect += (- step_relative) * (~ mask)
            expected_worst_margin = sum(balancing[:,0] * (margin_correct / (margin_correct + margin_incorrect)).min(axis=1)) / sum(balancing[:,0])

            computed_labels = recomputed_labels
            self.model += [(colname, thresh, a, b, expected_worst_margin)]

            if callback is not None:
                callback(weak_count / float(num_learners))

            if fout:
                colname, thresh, a, b, e_m = self.model[-1]
                fout.write("IF (%s > %s, %s, %s)\n" %
                           (colname, repr(thresh),
                            "[" + ", ".join([repr(v) for v in a]) + "]",
                            "[" + ", ".join([repr(v) for v in b]) + "]"))
            if err == 0.0:
                break
            weights = reweight
        if do_tests:
            return test_labels_by_iteration

    def TrainWeakLearner(self, labels, weights, values):
        ''' For a multiclass training set, with C classes and N examples,
        finds the optimal weak learner in O(M * N logN) time.
        Optimality is defined by Eq. 7 of Torralba et al., 'Sharing visual
        features...', 2007, IEEE PAMI.

        We differ from Torralba et al. in two ways:
        - we do not share a's and b's between classes
        - we always solve for the complete set of examples, regardless of label

        Labels should be 1 and -1, only.
        label_matrix and weights are NxC.
        values is N
        '''

        global order, s_values, s_labels, s_weights, s_weights_times_labels, num_a, den_a, a, b, sless0, sgrtr0, w_below_neg, w_below_pos, w_above_neg, w_above_pos, J

        # Sort labels and weights by values (AKA possible thresholds).  By
        # default, argsort is not stable, so the results will vary
        # slightly with the number of workers.  Add kind="mergesort" to
        # get a stable sort, which avoids this.
        order = np.argsort(values)
        s_values = values[order]
        s_labels = labels[order, :]
        s_weights = weights[order, :]

        # useful subfunction
        num_examples = labels.shape[0]
        def tilesum(a):
            return np.tile(np.sum(a, axis=0), (num_examples, 1))

        # Equations 9 and 10 of Torralba et al.
        s_weights_times_labels = s_weights * s_labels
        num_a = (tilesum(s_weights_times_labels) - np.cumsum(s_weights_times_labels, axis=0))
        den_a = (tilesum(s_weights) - np.cumsum(s_weights, axis=0))
        den_a[den_a <= 0.0] = 1.0 # avoid div by zero
        a = num_a / den_a
        b = np.cumsum(s_weights_times_labels, axis=0) / np.cumsum(s_weights, axis=0)

        # We need, at each index, the total weights below and above,
        # separated by positive and negative label.  Below includes the
        # current index
        sless0 = (s_labels < 0)
        sgrtr0 = (s_labels > 0)
        w_below_neg = np.cumsum(s_weights * sless0, axis=0)
        w_below_pos = np.cumsum(s_weights * sgrtr0, axis=0)
        w_above_neg = tilesum(s_weights * sless0) - w_below_neg
        w_above_pos = tilesum(s_weights * sgrtr0) - w_below_pos

        # Now evaluate the error at each threshold.
        # (see Equation 7, and note that we're assuming -1 and +1 for entries in the label matrix.
        J = w_below_neg * ((-1 - b)**2) + w_below_pos * ((1 - b)**2) + w_above_neg * ((-1 - a)**2) + w_above_pos * ((1 - a)**2)
        J = J.sum(axis=1)

        # Find index of least error
        idx = np.argmin(J)

        # make sure we're at the top of this thresh
        while (idx+1 < len(s_values)) and (s_values[idx] == s_values[idx + 1]):
            idx += 1

        # return the threshold at that index
        return s_values[idx], J[idx], a[idx, :].copy(), b[idx, :].copy()

    def UpdateBins(self, classBins):
        self.classBins = classBins

    def Usage(self, name):
        print(("usage %s:" % (name)))
        print(("%s num_learners              - read from stdin, write to stdout" % (name)))
        print(("%s num_learners file         - read from file, write to stdout" % (name)))
        print(("%s num_learners file1 file2  - read from file1, write to file2" % (name)))
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
        exit(1)

    def XValidate(self, colnames, num_learners, label_matrix, values, folds, group_labels, progress_callback, confusion=False):
        # if everything's in the same group, ignore the labels
        if all([g == group_labels[0] for g in group_labels]):
            group_labels = list(range(len(group_labels)))

        # randomize the order of labels
        unique_labels = list(set(group_labels))
        np.random.shuffle(unique_labels)

        fold_min_size = len(group_labels) / float(folds)
        num_misclassifications = np.zeros(num_learners, int)

        np_holdout_results = np.array([])
        np_holdout_labels = np.array([])

        # break into folds, randomly, but with all identical group_labels together
        for f in range(folds):
            current_holdout = [False] * len(group_labels)
            while unique_labels and (sum(current_holdout) < fold_min_size):
                to_add = unique_labels.pop()
                current_holdout = [(a or b) for a, b in zip(current_holdout, [g == to_add for g in group_labels])]

            if sum(current_holdout) == 0:
                logging.error("no holdout")
                break

            holdout_idx = np.nonzero(current_holdout)[0]
            current_holdin = ~ np.array(current_holdout)
            holdin_idx = np.nonzero(current_holdin)[0]
            holdin_labels = label_matrix[holdin_idx, :]
            holdin_values = values[holdin_idx, :]
            holdout_values = values[holdout_idx, :]
            holdout_results = self.Train(colnames, num_learners, holdin_labels, holdin_values, test_values=holdout_values)
            if holdout_results is None:
                return None
            # pad the end of the holdout set with the last element
            if len(holdout_results) < num_learners:
                holdout_results += [holdout_results[-1]] * (num_learners - len(holdout_results))
            holdout_labels = label_matrix[holdout_idx, :].argmax(axis=1)

            if confusion:
                np_holdout_results = np.concatenate((np_holdout_results,np.array(holdout_results).flatten()))
                np_holdout_labels = np.concatenate((np_holdout_labels,np.tile(holdout_labels,(num_learners,1)).flatten()))
                
            num_misclassifications += [sum(hr != holdout_labels) for hr in holdout_results]
            if progress_callback:
                progress_callback(f / float(folds))

        if confusion:
            return np_holdout_results, np_holdout_labels
        else:
            return [num_misclassifications]

    def XValidatePredict(self, colnames, num_learners, label_matrix, values, folds, group_labels, progress_callback):
        # if everything's in the same group, ignore the labels
        if all([g == group_labels[0] for g in group_labels]):
            group_labels = list(range(len(group_labels)))

        # randomize the order of labels
        unique_labels = list(set(group_labels))
        np.random.shuffle(unique_labels)

        fold_min_size = len(group_labels) / float(folds)
        num_misclassifications = np.zeros(num_learners, int)

        # break into folds, randomly, but with all identical group_labels together
        for f in range(folds):
            current_holdout = [False] * len(group_labels)
            while unique_labels and (sum(current_holdout) < fold_min_size):
                to_add = unique_labels.pop()
                current_holdout = [(a or b) for a, b in zip(current_holdout, [g == to_add for g in group_labels])]

            if sum(current_holdout) == 0:
                logging.error("no holdout")
                break

            holdout_idx = np.nonzero(current_holdout)[0]
            current_holdin = ~ np.array(current_holdout)
            holdin_idx = np.nonzero(current_holdin)[0]
            holdin_labels = label_matrix[holdin_idx, :]
            holdin_values = values[holdin_idx, :]
            holdout_values = values[holdout_idx, :]
            holdout_results = self.Train(colnames, num_learners, holdin_labels, holdin_values, test_values=holdout_values)
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

    # Confusion Matrix
    def plot_confusion_matrix(self, conf_arr, title='Confusion matrix', cmap=plt.cm.Blues):
        import seaborn as sns

        sns.set_style("whitegrid", {'axes.grid' : False})

        #plt.imshow(cm, interpolation='nearest', cmap=cmap)
        norm_conf = []
        for i in conf_arr:
            a = 0
            tmp_arr = []
            a = sum(i, 0)
            for j in i:
                tmp_arr.append(float(j)/float(a))
            norm_conf.append(tmp_arr)

        fig = plt.figure()
        fig.canvas.set_window_title(f"{fig.canvas.get_window_title()} - {self.name}")
        plt.clf()
        ax = fig.add_subplot(111)
        ax.set_aspect(1)
        res = ax.imshow(np.array(norm_conf), cmap=cmap, 
                        interpolation='nearest')

        width = len(conf_arr)
        height = len(conf_arr[0])

        for x in range(width):
            for y in range(height):
                if conf_arr[x][y] != 0:
                    ax.annotate("%.2f" % conf_arr[x][y], xy=(y, x), 
                                horizontalalignment='center',
                                verticalalignment='center')
        plt.title(title)
        plt.colorbar(res)
        tick_marks = np.arange(len(self.classifier.trainingSet.labels))
        plt.xticks(tick_marks, self.classifier.trainingSet.labels, rotation=45)
        plt.yticks(tick_marks, self.classifier.trainingSet.labels)
        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')

    def ConfusionMatrix(self, folds):

        from sklearn.metrics import confusion_matrix
        import wx
        # get wells if available, otherwise use imagenumbers
        try:
            nRules = int(self.classifier.nRulesTxt.GetValue())
        except:
            logging.error('Unable to parse number of rules')
            return

        if not self.classifier.UpdateTrainingSet():
            self.PostMessage('Cross-validation canceled.')
            return

        
        db = dbconnect.DBConnect()
        groups = [db.get_platewell_for_object(key) for key in self.classifier.trainingSet.get_object_keys()]

        #t1 = time()
        #dlg = wx.ProgressDialog('Computing cross validation accuracy...', '0% Complete', 100, self.classifier, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)        
        #base = 0.0
        #scale = 1.0

        if(folds):
            folds = folds
        else:
            folds = 5
        
        class StopXValidation(Exception):
            pass

        # def progress_callback(amount):
        #     pct = min(int(100 * (amount * scale + base)), 100)
        #     cont, skip = dlg.Update(pct, '%d%% Complete'%(pct))
        #     self.classifier.PostMessage('Computing cross validation accuracy... %s%% Complete'%(pct))
        #     if not cont:
        #         raise StopXValidation

        y_pred, y_test = self.XValidate(self.classifier.trainingSet.colnames, nRules, self.classifier.trainingSet.label_matrix,
                    self.classifier.trainingSet.values, folds, groups, None, confusion=True)

        cm = confusion_matrix(y_test, y_pred)
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        np.set_printoptions(precision=2)
        self.plot_confusion_matrix(cm_normalized, title='Normalized confusion matrix')
        
        plt.show()

if __name__ == '__main__':
    fgb = FastGentleBoosting()

    if len(argv) == 2:
        fin = stdin
        fout = stdout
    elif len(argv) == 3:
        fin = open(argv[2])
        fout = stdout
    elif len(argv) == 4:
        fin = open(argv[2])
        fout = open(argv[3], 'w')
    else:
        fgb.usage(argv[0])

    num_learners = int(argv[1])
    assert num_learners > 0

    import csv
    reader = csv.reader(fin, delimiter='	')
    header = next(reader)
    label_to_labelidx = {}
    curlabel = 1

    def getNumlabel(strlabel):
        if strlabel in label_to_labelidx:
            return label_to_labelidx[strlabel]
        global curlabel
        print(("LABEL: ", curlabel, strlabel))
        label_to_labelidx[strlabel] = curlabel
        curlabel += 1
        return label_to_labelidx[strlabel]

    colnames = header[1:]
    labels = []
    values = []
    for vals in reader:
        values.append([0 if v == 'None' else float(v) for v in vals[1:]])
        numlabel = getNumlabel(vals[0])
        labels.append(numlabel)

    labels = np.array(labels).astype(np.int32)
    values = np.array(values).astype(np.float32)

    # convert labels to a matrix with +1/-1 values only (+1 in the column matching the label, 1-indexed)
    num_classes = max(labels)
    label_matrix = -np.ones((len(labels), num_classes), np.int32)
    for i, j in zip(list(range(len(labels))), np.array(labels)-1):
        label_matrix[i, j] = 1

    wl = fgb.Train(colnames, num_learners, label_matrix, values, fout)
    for w in wl:
        print(w)
    print((label_matrix.shape, "groups"))
    print((fgb.xvalidate(colnames, num_learners, label_matrix, values, 20, list(range(1, label_matrix.shape[0]+1)), None)))

#def train_classifier(labels, values, iterations):
#    # make sure these are arrays (not matrices)
#    labels = array(labels)
#    values = array(values)
#
#    num_examples = labels.shape[0]
#
#    learners = []
#    weights = ones(labels.shape)
#    output = zeros(labels.shape)
#    for n in range(iterations):
#        best_error = float(Infinity)
#
#        for feature_idx in range(values.shape[1]):
#            val, err, a, b = trainWeakLearner(labels, weights, values[:, feature_idx])
#            if err < best_error:
#                best_error = err
#                best_idx = feature_idx
#                best_val = val
#                best_a = a
#                best_b = b
#
#        delta = values[:, best_idx] > best_val
#        delta.shape = (len(delta), 1)
#        feature_thresh_mask = tile(delta, (1, labels.shape[1]))
#        output = output + feature_thresh_mask * tile(best_a, (num_examples, 1)) + (1 - feature_thresh_mask) * tile(best_b, (num_examples, 1))
#        weights = exp(- output * labels)
#        weights = weights / sum(weights)
#        err = sum((output * labels) <= 0)
#    return
#
#def myfromfile(stream, type, sh):
#    if len(sh) == 2:
#        tot = sh[0] * sh[1]
#    else:
#        tot = sh[0]
#    result = fromfile(stream, type, tot)
#    result.shape = sh
#    return result
#
#def doit():
#    testing = False
#    n, ncols = myfromfile(stdin, int32, (2,))
#    num_classes = myfromfile(stdin, int32, (1,))[0]
#    values = myfromfile(stdin, float32, (n, ncols))
#    label_matrix = myfromfile(stdin, int32, (n, num_classes))
#
#    while True:
#        # It would be cleaner to tell the worker we're done by just
#        # closing the stream, but numpy does strange things (prints
#        # error message, signals MemoryError) when myfromfile cannot
#        # read as many bytes as expected.
#        if stdin.readline() == "done\n":
#            return
#        weights = myfromfile(stdin, float32, (n, num_classes))
#
#        best = float(Infinity)
#        for column in range(ncols):
#            colvals = values[:, column]
#            # print >>stderr, "WORK", column, label_matrix, weights, colvals
#            thresh, err, a, b = trainWeakLearner(label_matrix, weights, colvals)
#            if err < best:
#                best = err
#                bestvals = (err, column, thresh, a, b)
#
#        err, column, thresh, a, b = bestvals
#        array([err, column, thresh], float32).tofile(stdout)
#        a.astype(float32).tofile(stdout)
#        b.astype(float32).tofile(stdout)
#        stdout.flush()



#if __name__ == '__main__':
#    try:
#        import dl
#        h = dl.open('change_malloc_zone.dylib')
#        h.call('setup')
#    except:
#        pass
#    if len(argv) != 1:
#        import cProfile
#        cProfile.runctx("doit()", globals(), locals(), "worker.cprof")
#    else:
#        try: # Use binary I/O on Windows
#            import msvcrt, os
#            try:
#                msvcrt.setmode(stdin.fileno(), os.O_BINARY)
#            except:
#                stderr.write("Couldn't deal with stdin\n")
#                pass
#            try:
#                msvcrt.setmode(stdout.fileno(), os.O_BINARY)
#                stderr.write("Couldn't deal with stdout\n")
#            except:
#                pass
#        except ImportError:
#            pass
#        doit()
#    try:
#        h.call('teardown')
#    except:
#        pass
