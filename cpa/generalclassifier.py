import re
import dbconnect
import logging
import multiclasssql
import numpy as np
import matplotlib.pyplot as plt
from sys import stdin, stdout, argv, exit
from time import time
from sklearn import ensemble, naive_bayes, grid_search, svm, lda, qda, tree, multiclass, linear_model, neighbors
#from sklearn.externals import joblib
from sklearn import cross_validation
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn import metrics
import cPickle, json
from sklearn.externals import joblib
import seaborn as sns

class GeneralClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, classifier = "lda.LDA()", env=None):
        self.classBins = []
        self.classifier = eval(classifier)
        self.trained = False
        self.env = env # Env is Classifier in Legacy Code -- maybe renaming ?
        self.name = self.name()

        logging.info('Initialized New Classifier: ' + self.name)

    # Return name
    def name(self):
        return self.classifier.__class__.__name__

    def CheckProgress(self):
        #import wx
        ''' Called when the Cross Validation Button is pressed. '''
        # get wells if available, otherwise use imagenumbers

        db = dbconnect.DBConnect.getInstance()
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


    def ClassificationReport(self, true_labels, predicted_labels, confusion_matrix=False):

        return metrics.classification_report(true_labels, predicted_labels)

    def ClearModel(self):
        self.classBins = []
        self.trained = False

    # Adapter to SciKit Learn
    def ComplexityTxt(self):
        return '# top features'

    def CreatePerObjectClassTable(self, classNames):
        multiclasssql.create_perobject_class_table(self, classNames)

    def FilterObjectsFromClassN(self, obClass, obKeysToTry, uncertain=False):
        return multiclasssql.FilterObjectsFromClassN(obClass, self, obKeysToTry, uncertain)

    def IsTrained(self):
        return self.trained

    def LoadModel(self, model_filename):

        try:
            self.classifier, self.bin_labels, self.name = joblib.load(model_filename)
        except:
            self.classifier = None
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
        for train, test in cross_validation.LeaveOneOut(num_samples):
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
        predictions = self.classifier.predict(test_values)
        if fout:
            print predictions
        return np.array(predictions)

    # Return probabilities
    def PredictProba(self, test_values):
        try:
            if "predict_proba" in dir(self.classifier):
                return self.classifier.predict_proba(test_values)
        except:
            logging.info("Selected algorithm doesn't provide probabilities")
           
    def SaveModel(self, model_filename, bin_labels):
        joblib.dump((self.classifier, bin_labels, self.name), model_filename, compress=9)

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

        self.classifier.fit(values, labels)
        self.trained = True

        if fout:
            print self.classifier

    def UpdateBins(self, classBins):
        self.classBins = classBins

    def Usage(self):
        print "usage :"
        print " classifier              - read from stdin, write to stdout"
        print " classifier file         - read from file, write to stdout"
        print " classifier file1 file2  - read from file1, write to file2"
        print ""
        print "Input files should be tab delimited."
        print "Example:"
        print "ClassLabel   Value1_name Value2_name Value3_name"
        print "2    0.1 0.3 1.5"
        print "1    0.5 -0.3    0.5"
        print "3    0.1 1.0 0.5"
        print ""
        print "Class labels should be integers > 0."
        exit(1)

    def XValidate(self, labels, values, folds, stratified=False, scoring=None):
        '''
        Performs K fold cross validation based on input folds.
        Takes a subset of the input data label_array and values to do the cross validation.
        RETURNS: array of length folds of cross validation scores
        '''

        num_samples = values.shape[0]
        if stratified:
            CV = folds
        else:
            CV = cross_validation.KFold(num_samples, folds)
        #scores = cross_validation.cross_val_score(self.classifier, scoring=scoring, X=values, y=labels, cv=CV, n_jobs=-1, verbose=1)
        scores = cross_validation.cross_val_score(self.classifier, X=values, y=labels, cv=folds, n_jobs=1)

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
        chosenIndices = [np.random.choice(range(cumSumLabelIndices[i],cumSumLabelIndices[i+1]), min_labels, replace=False) for i in range(n_classes)]

        labels_s = np.zeros(min_labels*n_classes)
        values_s = np.zeros((min_labels*n_classes, values.shape[1]))
        for c in reversed(range(n_classes)):
            labels_s[min_labels*c:min_labels*(c+1)] = labels[chosenIndices[c]]
            values_s[min_labels*c:min_labels*(c+1)] = values[chosenIndices[c]]

        #do k fold cross validation on this newly balanced data
        return self.XValidate(labels_s, values_s, folds, stratified=True)

    def XValidatePredict(self, labels, values, folds, stratified=False):
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
            CV = cross_validation.KFold(num_samples, folds)

        predictions = cross_validation.cross_val_predict(self.classifier, X=values, y=labels, cv=CV, n_jobs=1)
        return np.array(predictions)

    # Plots the classification report for the user
    def plot_classification_report(self, cr, title='Classification report ', with_avg_total=False, cmap=plt.cm.Greys):
        sns.set_style("whitegrid", {'axes.grid' : False})

        lines = cr.split('\n')

        classes = []
        plotMat = []
        for line in lines[2 : (len(lines) - 3)]:
            #print(line)
            t = line.split()
            # print(t)
            label = self.env.trainingSet.labels[int(t[0]) - 1]
            classes.append(label)
            v = [float(x) for x in t[1: len(t) - 1]]
            plotMat.append(v)

        if with_avg_total:
            aveTotal = lines[len(lines) - 1].split()
            classes.append('avg/total')
            vAveTotal = [float(x) for x in t[1:len(aveTotal) - 1]]
            plotMat.append(vAveTotal)

        plt.imshow(plotMat, interpolation='nearest', cmap=cmap)
        plt.title(title)
        plt.colorbar()
        x_tick_marks = np.arange(3)
        y_tick_marks = np.arange(len(classes))
        plt.xticks(x_tick_marks, ['precision', 'recall', 'f1-score'], rotation=45)
        plt.yticks(y_tick_marks, classes)
        plt.tight_layout()
        plt.ylabel('Classes')
        plt.xlabel('Measures')
        plt.show()

    # Confusion Matrix
    def plot_confusion_matrix(self, cm, title='Confusion matrix', cmap=plt.cm.Blues):
        sns.set_style("whitegrid", {'axes.grid' : False})

        plt.imshow(cm, interpolation='nearest', cmap=cmap)
        plt.title(title)
        plt.colorbar()
        tick_marks = np.arange(len(self.env.trainingSet.labels))
        plt.xticks(tick_marks, self.env.trainingSet.labels, rotation=45)
        plt.yticks(tick_marks, self.env.trainingSet.labels)
        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')

    def ConfusionMatrix(self):
        from sklearn.metrics import confusion_matrix
        # Compute confusion matrix
        folds = 5 # like classification report
        y_pred = self.XValidatePredict(self.env.trainingSet.label_array, self.env.trainingSet.values, folds)
        y_test = self.env.trainingSet.label_array

        cm = confusion_matrix(y_test, y_pred)
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        np.set_printoptions(precision=2)
        logging.info('Confusion matrix, without normalization')
        logging.info(cm)
        plt.figure()
        self.plot_confusion_matrix(cm)

        # Normalize the confusion matrix by row (i.e by the number of samples
        # in each class)
        logging.info('Normalized confusion matrix')
        logging.info(cm_normalized)
        plt.figure()
        self.plot_confusion_matrix(cm_normalized, title='Normalized confusion matrix')

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
    header = reader.next()
    label_to_labelidx = {}
    curlabel = 1
 
    def getNumlabel(strlabel):
        if strlabel in label_to_labelidx:
            return label_to_labelidx[strlabel]
        global curlabel
        print "LABEL: ", curlabel, strlabel
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
