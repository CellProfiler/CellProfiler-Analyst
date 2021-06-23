
from . import dbconnect
import logging
from . import multiclasssql
import numpy as np
import matplotlib.pyplot as plt
from sys import stdin, stdout, argv, exit
from time import time
from sklearn import ensemble, naive_bayes, svm, discriminant_analysis, tree, multiclass, linear_model, neighbors, neural_network
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn import metrics
import pickle, json
import joblib
import seaborn as sns
from sklearn.model_selection import LeaveOneOut, KFold, cross_val_predict, cross_val_score
from sklearn.preprocessing import StandardScaler
import sys

##########
# MatPlotLib currently has a bug on Windows which crashes wx if you close an interactive plot window.
# This should be fixed in MPL 3.4, but for now we'll monkey patch in the fix.
# See MPL PR #19596 for more details. - dstirling Mar 2021
import wx
import matplotlib.backends.backend_wx
from matplotlib._pylab_helpers import Gcf

def mp_onClose(self, event):
    self.canvas.close_event()
    self.canvas.stop_event_loop()
    self.figmgr.frame = None
    Gcf.destroy(self.figmgr)
    event.Skip()

def mp_Destroy(self, *args, **kwargs):
    try:
        self.canvas.mpl_disconnect(self.toolbar._id_drag)
    except AttributeError:
        pass
    if self and not self.IsBeingDeleted():
        wx.Frame.Destroy(self, *args, **kwargs)
    return True

def mp_mandestroy(self, *args):
    frame = self.frame
    if frame:
        wx.CallAfter(frame.Close)

matplotlib.backends.backend_wx.FigureFrameWx._onClose = mp_onClose
matplotlib.backends.backend_wx.FigureFrameWx.Destroy = mp_Destroy
matplotlib.backends.backend_wx.FigureManagerWx.destroy = mp_mandestroy
##########

class GeneralClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, classifier = "discriminant_analysis.LinearDiscriminantAnalysis()", env=None, scaler=False):
        self.classBins = []
        self.classifier = eval(classifier)
        if scaler:
            self.scaler = StandardScaler()
        else:
            self.scaler = None
        self.trained = False
        self.env = env # Env is Classifier in Legacy Code -- maybe renaming ?
        self.name = self.name()
        self.features = []

        logging.info('Initialized New Classifier: ' + self.name)

    # Set features
    def _set_features(self, features):
        self.features = features

    # Return name
    def name(self):
        return self.classifier.__class__.__name__

    def CheckProgress(self):
        #import wx
        ''' Called when the Cross Validation Button is pressed. '''
        # get wells if available, otherwise use imagenumbers

        db = dbconnect.DBConnect()
        groups = [db.get_platewell_for_object(key) for key in self.env.trainingSet.get_object_keys()]

        if not self.env.UpdateTrainingSet():
            self.PostMessage('Cross-validation canceled.')
            return

        #t1 = time()
        #dlg = wx.ProgressDialog('Nothing', '0% Complete', 100, self.classifier, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
        labels = self.env.trainingSet.label_array
        values = self.env.trainingSet.values
        classificationReport = self.ClassificationReport(labels, self.XValidatePredict(labels, values, folds=5, stratified=True))
        logging.info("Classification Report")
        logging.info(classificationReport)
        self.plot_classification_report(classificationReport)

    def toggle_scaler(self, enabled):
        if enabled:
            if self.scaler is None:
                # ClearModel will create a scaler for us, no need to do this twice
                self.scaler = True
        else:
            self.scaler = None
        self.ClearModel()

    def ClassificationReport(self, true_labels, predicted_labels, confusion_matrix=False):

        return metrics.classification_report(true_labels, predicted_labels)

    def ClearModel(self):
        self.classBins = []
        if self.scaler is not None:
            self.scaler = StandardScaler()
        self.trained = False

    # Adjust text for the classifier rules panel
    def panelTxt(self):
        if self.scaler is not None:
            return "with"
        return 'display'
        
    def panelTxt2(self):
        if self.name == "MLPClassifier":
            return "neurons per layer"
        return 'top features'

    def CreatePerObjectClassTable(self, classNames, updater):
        multiclasssql.create_perobject_class_table(self, classNames, updater)

    def FilterObjectsFromClassN(self, obClass, obKeysToTry, uncertain=False):
        return multiclasssql.FilterObjectsFromClassN(obClass, self, obKeysToTry, uncertain)

    def IsTrained(self):
        return self.trained

    def LoadModel(self, model_filename):

        try:
            self.classifier, self.bin_labels, self.name, self.features = joblib.load(model_filename)
            self.scaler = self.classifier.scaler
            print("Loaded", self.classifier, self.scaler, "models")
        except:
            self.classifier = None
            self.scaler = None
            self.bin_labels = None
            logging.error('Model not correctly loaded')
            raise TypeError


    def LOOCV(self, labels, values, details=False):
        '''
        Performs leave one out cross validation.
        Takes a subset of the input data label_array and values to do the cross validation.
        RETURNS: array of length folds of cross validation scores,
        detailedResults is an array of length # of samples containing the predicted classes
        '''
        num_samples = values.shape[0]
        scores = np.zeros(num_samples)
        detailedResults = np.zeros(num_samples)
        # get training and testing set, train on training set, score on test set
        for train, test in LeaveOneOut(num_samples):
            values_test = values[test]
            label_test = labels[test]
            self.Train(labels[train], values[train], fout=None)
            scores[test] = self.classifier.score(values_test, label_test)
            if details:
                detailedResults[test] = self.Predict(values_test)
        if details:
            return scores, detailedResults
        return scores

    def PerImageCounts(self, number_of_classes, filter_name=None, cb=None):
        return multiclasssql.PerImageCounts(self, number_of_classes, filter_name, cb)

    def Predict(self, test_values, fout=None):
        '''RETURNS: np array of predicted classes of input data test_values '''
        if self.scaler is not None:
            test_values = self.scaler.transform(test_values)
        predictions = self.classifier.predict(test_values)
        if fout:
            print(predictions)
        return np.array(predictions)

    # Return probabilities
    def PredictProba(self, test_values):
        try:
            if "predict_proba" in dir(self.classifier):
                if self.scaler is not None:
                    test_values = self.scaler.transform(test_values)
                return self.classifier.predict_proba(test_values)
        except:
            logging.info("Selected algorithm doesn't provide probabilities")
           
    def SaveModel(self, model_filename, bin_labels):
        # Attach any scaler to the model object
        self.classifier.scaler = self.scaler
        joblib.dump((self.classifier, bin_labels, self.name, self.features), model_filename, compress=1)

    def ShowModel(self):#SKLEARN TODO
        '''
        Returns a string describing the most important features of the trained classifier
        '''
        if self.trained:
            try:
                colnames = self.env.trainingSet.colnames
                importances = self.classifier.feature_importances_
                indices = np.argsort(importances)[::-1]
                return "\n".join([str(colnames[indices[f]]) for f in range(self.env.nRules)])
            except:
                return ''
        else:
            return ''

    def Train(self, labels, values, fout=None):
        '''Trains classifier using values and label_array '''
        if self.scaler is not None:
            # Reset the scaler for training
            self.scaler = StandardScaler()
            values = self.scaler.fit_transform(values)
        self.classifier.fit(values, labels)
        self.trained = True

        if fout:
            print((self.classifier))

    def UpdateBins(self, classBins):
        self.classBins = classBins

    def Usage(self):
        print("usage :")
        print(" classifier              - read from stdin, write to stdout")
        print(" classifier file         - read from file, write to stdout")
        print(" classifier file1 file2  - read from file1, write to file2")
        print("")
        print("Input files should be tab delimited.")
        print("Example:")
        print("ClassLabel   Value1_name Value2_name Value3_name")
        print("2    0.1 0.3 1.5")
        print("1    0.5 -0.3    0.5")
        print("3    0.1 1.0 0.5")
        print("")
        print("Class labels should be integers > 0.")
        exit(1)

    def XValidate(self, labels, values, folds, stratified=True, scoring=None):
        '''
        Performs K fold cross validation based on input folds.
        Takes a subset of the input data label_array and values to do the cross validation.
        RETURNS: array of length folds of cross validation scores
        '''

        num_samples = values.shape[0]
        if stratified:
            CV = folds
        else:
            CV = KFold(num_samples, folds)
        #scores = cross_validation.cross_val_score(self.classifier, scoring=scoring, X=values, y=labels, cv=CV, n_jobs=-1, verbose=1)
        scores = cross_val_score(self.classifier, X=values, y=labels, cv=folds, n_jobs=1)

        return np.array(scores)

    def XValidateBalancedClasses(self, labels, values, folds):
        '''
        :param labels: class of each sample
        :param values: feature values for each sample
        :param folds: number of folds
        :return: score for each fold
        '''
        n_samples = values.shape[0]
        unique_labels, indices = np.unique(labels, return_inverse=True)
        label_counts = np.bincount(indices) #count of each class
        min_labels = np.min(label_counts) #possibly make this flexible
        n_classes = len(unique_labels)
        cumSumLabelIndices = np.append(np.array(0), np.cumsum(label_counts))

        #make new data set
        #randomly choose min_labels samples from each class (the rest are thrown away)
        chosenIndices = [np.random.choice(list(range(cumSumLabelIndices[i],cumSumLabelIndices[i+1])), min_labels, replace=False) for i in range(n_classes)]

        labels_s = np.zeros(min_labels*n_classes)
        values_s = np.zeros((min_labels*n_classes, values.shape[1]))
        for c in reversed(list(range(n_classes))):
            labels_s[min_labels*c:min_labels*(c+1)] = labels[chosenIndices[c]]
            values_s[min_labels*c:min_labels*(c+1)] = values[chosenIndices[c]]

        #do k fold cross validation on this newly balanced data
        return self.XValidate(labels_s, values_s, folds, stratified=True)

    def XValidatePredict(self, labels, values, folds, stratified=True):
        '''
        :param labels: class of each sample
        :param values: feature values for each sample
        :param folds: number of folds
        :param stratified: boolean whether to use stratified K fold
        :return: cross-validated estimates for each input data point
        '''
        num_samples = values.shape[0]
        if stratified:
            CV = folds
        else:
            CV = KFold(num_samples, folds)
        if self.scaler is not None:
            values = self.scaler.transform(values)
        predictions = cross_val_predict(self.classifier, X=values, y=labels, cv=CV, n_jobs=1)
        return np.array(predictions)

    # Classification Report Start

    def show_values(self, pc, fmt="%.2f", **kw):
        '''
        Heatmap with text in each cell with matplotlib's pyplot
        Source: http://stackoverflow.com/a/25074150/395857 
        By HYRY
        '''
        
        pc.update_scalarmappable()
        ax = pc.axes
        for p, color, value in zip(pc.get_paths(), pc.get_facecolors(), pc.get_array()):
            x, y = p.vertices[:-2, :].mean(0)
            if np.all(color[:3] > 0.5):
                color = (0.0, 0.0, 0.0)
            else:
                color = (1.0, 1.0, 1.0)
            ax.text(x, y, fmt % value, ha="center", va="center", color=color, **kw)

    def cm2inch(self, *tupl):
        '''
        Specify figure size in centimeter in matplotlib
        Source: http://stackoverflow.com/a/22787457/395857
        By gns-ank
        '''
        inch = 2.54
        if type(tupl[0]) == tuple:
            return tuple(i/inch for i in tupl[0])
        else:
            return tuple(i/inch for i in tupl)


    def heatmap(self, AUC, title, xlabel, ylabel, xticklabels, yticklabels, figure_width=40, figure_height=20, correct_orientation=False, cmap='RdBu'):
        '''
        Inspired by:
        - http://stackoverflow.com/a/16124677/395857 
        - http://stackoverflow.com/a/25074150/395857
        '''

        # Plot it out
        fig, ax = plt.subplots()    
        #c = ax.pcolor(AUC, edgecolors='k', linestyle= 'dashed', linewidths=0.2, cmap='RdBu', vmin=0.0, vmax=1.0)
        c = ax.pcolor(AUC, edgecolors='k', linestyle= 'dashed', linewidths=0.2, cmap=cmap)

        # put the major ticks at the middle of each cell
        ax.set_yticks(np.arange(AUC.shape[0]) + 0.5, minor=False)
        ax.set_xticks(np.arange(AUC.shape[1]) + 0.5, minor=False)

        # set tick labels
        #ax.set_xticklabels(np.arange(1,AUC.shape[1]+1), minor=False)
        ax.set_xticklabels(xticklabels, minor=False)
        ax.set_yticklabels(yticklabels, minor=False)

        # set title and x/y labels
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)      

        # Remove last blank column
        plt.xlim( (0, AUC.shape[1]) )

        # Turn off all the ticks
        ax = plt.gca()    
        for t in ax.xaxis.get_major_ticks():
            t.tick1On = False
            t.tick2On = False
        for t in ax.yaxis.get_major_ticks():
            t.tick1On = False
            t.tick2On = False

        # Add color bar
        plt.colorbar(c)

        # Add text in each cell 
        self.show_values(c)

        # Proper orientation (origin at the top left instead of bottom left)
        if correct_orientation:
            ax.invert_yaxis()
            ax.xaxis.tick_top()       

        # resize 
        fig = plt.gcf()
        # Disabling this - not sure why we make the figure so huge, it sizes itself just fine. Mar 2021
        # fig.set_size_inches(self.cm2inch(figure_width, figure_height))
        plt.show()

    def plot_classification_report(self, classification_report, title='Classification report ', cmap='RdBu'):
        '''
        Plot scikit-learn classification report.
        Extension based on http://stackoverflow.com/a/31689645/395857 
        '''
        lines = classification_report.split('\n')

        classes = []
        plotMat = []
        support = []
        class_names = []
        for line in lines[2:-4]:
            t = line.strip().split()
            if len(t) < 2: continue
            classes.append(t[0])
            v = [float(x) for x in t[1:-1]]
            support.append(int(t[-1]))
            class_names.append(t[0])
            print(v)
            plotMat.append(v)

        print(('plotMat: {0}'.format(plotMat)))
        print(('support: {0}'.format(support)))

        xlabel = 'Metrics'
        ylabel = 'Classes'
        xticklabels = ['Precision', 'Recall', 'F1-score']
        yticklabels = ['{0} ({1})'.format(self.env.trainingSet.labels[idx], sup) for idx, sup  in enumerate(support)]
        figure_width = 25
        figure_height = len(class_names) + 7
        correct_orientation = False
        self.heatmap(np.array(plotMat), title, xlabel, ylabel, xticklabels, yticklabels, figure_width, figure_height, correct_orientation, cmap=cmap)

    # Classification Report End

    # Confusion Matrix (improved version with total numbers)
    def plot_confusion_matrix(self, conf_arr, title='Confusion matrix', cmap=plt.cm.Blues):
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
        tick_marks = np.arange(len(self.env.trainingSet.labels))
        plt.xticks(tick_marks, self.env.trainingSet.labels, rotation=45)
        plt.yticks(tick_marks, self.env.trainingSet.labels)
        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')

    def ConfusionMatrix(self, folds):
        from sklearn.metrics import confusion_matrix
        # Compute confusion matrix

        y_pred = self.XValidatePredict(self.env.trainingSet.label_array, self.env.trainingSet.values, folds, stratified=True)
        y_test = self.env.trainingSet.label_array

        cm = confusion_matrix(y_test, y_pred)

        nObjects = cm.sum()
        misRate = float(nObjects - np.diag(cm).sum()) * 100 / nObjects

        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        np.set_printoptions(precision=2)
        logging.info('Confusion matrix (Classification Accuracy: %3.2f%%)' % (100 - misRate))
        logging.info(cm)
        #plt.figure()
        self.plot_confusion_matrix(cm_normalized, title='Confusion matrix (Classification Accuracy: %3.2f%%)' % (100 - misRate))

        # Normalize the confusion matrix by row (i.e by the number of samples
        # in each class)
        logging.info('Normalized confusion matrix')
        logging.info(cm_normalized)
        #plt.figure()
        #self.plot_confusion_matrix(cm_normalized, title='Normalized confusion matrix')

        plt.show()

    # Get sklearn params dic
    def get_params(self):
        return self.classifier.get_params()

    # Set sklearn params 
    def set_params(self, params):
        self.classifier.set_params(**params)


if __name__ == '__main__':

    classifier = GeneralClassifier(eval(argv[1]))
    if len(argv) == 2:
        fin = stdin
        fout = stdout
    elif len(argv) == 3:
        fin = open(argv[2])
        fout = stdout
    elif len(argv) == 4:
        fin = open(argv[2])
        fout = open(argv[3], 'w')
    elif len(argv) > 4:
        classifier.Usage()

    import csv
    reader = csv.reader(fin, delimiter='    ')
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

    #scores = classifier.XValidate(labels, values, folds=20, stratified=True)
    #scores = classifier.XValidateBalancedClasses(labels, values, folds=5)
    scorePerClass = classifier.ScorePerClass(labels, classifier.XValidatePredict(labels,values,folds=20, stratified=True))
