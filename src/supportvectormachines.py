#!/usr/bin/env python

# TODO:
# Multiprocessing module for Python 2.5, substitute linear_scale for lambda,
# change the c and g intervals definition, maybe use np.nan_to_num before scaling

import dbconnect
import dimensredux as dr
import logging
import numpy as np
import wx
from datamodel import DataModel
from properties import Properties
from sys import hexversion, exc_info
from threading import Thread
from traceback import print_exception

# Import all functions to interface with the libsvm library
import svmutil
#from scikits.learn.svm import BaseLibSVM


def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)


# Since the Queue module has been renamed in Python 3 import it appropriately
if(hexversion < 0x03000000):
    import Queue
else:
    import queue as Queue

class Worker(Thread):
    '''
    Worker for the execution of each calculation thread.
    '''
    def __init__(self, name, job_queue, result_queue, labels, values, nValidation):
        Thread.__init__(self)
        self.name = name
        self.job_queue = job_queue
        self.result_queue = result_queue
        self.labels, self.values = labels, values
        self.nValidation = nValidation
        self.classifierParameters = []

    def run(self):
        while True:
            (cexp,gexp) = self.job_queue.get()
            if cexp is WorkerStopToken:
                self.job_queue.put((cexp,gexp))
                break
            try:
                rate = self.run_one(2**cexp, 2**gexp, self.labels, self.values)
                if rate is None: raise "get no rate"
            except:
                print_exception(exc_info()[0], exc_info()[1], exc_info()[2])
                self.job_queue.put((cexp,gexp))
                logging.info('Worker %s quit.' % self.name)
                break
            else:
                self.result_queue.put((self.name,cexp,gexp,rate))

class WorkerStopToken:
    '''
    Notify a worker to stop.
    '''
    pass

class LocalWorker(Worker):
    '''
    Thread in the local computer.
    '''
    def run_one(self, c, g, y, x):
        options = '-t 2 -c %s -g %s -v %s -e 0.1 -q' % (c, g, self.nValidation)
        result = svmutil.svm_train(y, x, options)
        return float(result)

class StopCalculating(Exception):
    pass

class SupportVectorMachines(object):
    '''
    Class to define a complete support vector machine classifier calculation problem. 
    '''
    def __init__(self, classifier = None):
        logging.info('Initialized New Support Vector Machines Classifier')
        self.model = None 
        self.classBins = []
        self.classifier = classifier

        # Initialize the total object storage
        self.perClassObjects = {}
        self.feat_min, self.feat_max = None, None
        self.svm_train_labels, self.svm_train_values = None, None

    def CalculateCGamma(self, callback = None, nValidation = 5):
        '''
    	Grid search of the best C and gamma parameters for the RBF Kernel.
    	The efficiency of the parameters is evaluated using nValidation-fold
        cross-validation of the training data.
    
    	As this process is time consuming and parallelizable, a number of
        threads equal to the number of cores in the computer is used for the
        calculations
    	'''
        jobs = self.CalculateJobs()
        job_queue = Queue.Queue(0)
        result_queue = Queue.Queue(0)

        jobs_flat_list = [(c,g) for line in jobs for (c,g) in line]
        map(job_queue.put, jobs_flat_list)
        job_queue._put = job_queue.queue.appendleft

        # Start local workers
        try:
            from multiprocessing import cpu_count
            nr_local_worker = cpu_count()
        except:
            nr_local_worker = 1

        for i in xrange(nr_local_worker):
            LocalWorker('local %s' % (i+1), job_queue, result_queue,
                        self.svm_train_labels, self.svm_train_values,
                        nValidation).start()

        # Initialize result containers
        done_jobs = {}
        db = []
        best_rate = -1
        best_c1, best_g1 = None, None

        for index, (c,g) in enumerate(jobs_flat_list):
            if callback is not None:
                callback(index / float(len(jobs_flat_list)))
            while (c, g) not in done_jobs:
                (worker,c1,g1,rate) = result_queue.get()
                done_jobs[(c1,g1)] = rate
                if (rate > best_rate) or (rate == best_rate and g1 == best_g1 and c1 < best_c1):
                    best_rate = rate
                    best_c1, best_g1 = c1, g1
                    best_c = 2.0**c1
                    best_g = 2.0**g1
                logging.info("[%s] C=%s g=%s rate=%s (Best values C=%s, g=%s, rate=%s)" %
                             (worker, c1, g1, rate, best_c, best_g, best_rate))
            db.append((c,g,done_jobs[(c,g)]))

        job_queue.put((WorkerStopToken, None))
        logging.info("Optimal values: C=%s g=%s rate=%s" % (best_c, best_g, best_rate))
        self.classifierParameters = (best_c, best_g, best_rate)

        return best_c, best_g

    def CalculateJobs(self):
        '''
    	Calculate the C and Gamma parameters tuples for the grid search in CalculateCGamma()
    	'''
        c_begin, c_end, c_step = -5,  11, 2
        g_begin, g_end, g_step =  3, -11, -2
        c_seq = self.PermuteSequence(list(np.arange(c_begin,c_end,c_step)))
        g_seq = self.PermuteSequence(list(np.arange(g_begin,g_end,g_step)))

        nr_c = float(len(c_seq))
        nr_g = float(len(g_seq))
        i = 0
        j = 0
        jobs = []

        while i < nr_c or j < nr_g:
            if i/nr_c < j/nr_g:
                # increase C resolution
                line = []
                for k in xrange(0,j):
                    line.append((c_seq[i],g_seq[k]))
                i = i + 1
                jobs.append(line)
            else:
                # increase g resolution
                line = []
                for k in xrange(0,i):
                    line.append((c_seq[k],g_seq[j]))
                j = j + 1
                jobs.append(line)
        return jobs

    def CheckProgress(self):
        # Calculate cross-validation data
        nPermutations = 10
        try:
            misclassifications = self.XValidate(nPermutations)
        except StopCalculating:
            return

        def confusionMatrix():
            # Open confusion matrix
            confusionMatrix, axes = self.ConfusionMatrix(
                self.svm_train_labels,
                [misclassifications[i]+[val]*(nPermutations-len(misclassifications[i]))
                 for i, val in enumerate(self.svm_train_labels)]
            )
            self.classifier.ShowConfusionMatrix(confusionMatrix, axes)

        def dimensionReduction():
            # Initialize PCA/tSNE plot
            pca_main = dr.PlotMain(self.classifier, properties = Properties.getInstance(), loadData = False)
            pca_main.set_data(self.classifier.trainingSet.values,
                              dict([(index, object) for index, object in 
                                    enumerate(self.classifier.trainingSet.get_object_keys())]),
                              np.int64(self.classifier.trainingSet.label_matrix > 0),
                              self.classifier.trainingSet.labels,
                              np.array([len(misclassifications[i])/float(nPermutations) for i in xrange(len(misclassifications))]).round(2))
            pca_main.Show(True)

        # Ask how the user wants to visualize the cross-validation results (either through
        # a confusion matrix or visually in a dimension reductionality plot)
        visualizationChoiceBox(self.classifier, -1, 'Pick cross-validation visualization', confusionMatrix, dimensionReduction)

    def ClearModel(self):
        # Clear all parameters related to the trained classifier
        self.classBins = []
        self.model = None
        self.feat_min, self.feat_max = None, None
        self.svm_train_labels, self.svm_train_values = None, None

    def ComplexityTxt(self):
        return 'Number of cross-validations: '

    def ConfusionMatrix(self, actual = None, predicted = None):
        # Retrieve the number of classes, their labels and initialize
        # the confusion matrix
        nClasses = len(self.classBins)
        confusionMatrix = np.zeros((nClasses, nClasses), np.int64)
        classLabels = [bin.label for bin in self.classBins]

        # For each of the objects used to train the classifier, check what class
        # it was predicted to have been by the classifier
        if actual is None or predicted is None:
            for actualClassNum, actualClassObjects in \
                enumerate([bin.GetObjectKeys() for bin in self.classBins]):
                for predictedLabel in [(classLabels[i], i) for i in range(nClasses)]:
                    confusionMatrix[predictedLabel[1], actualClassNum] += \
                        len([obj for obj in actualClassObjects if \
                        obj in self.perClassObjects[predictedLabel[0]]])
        else:
            # Generate the confusion matrix for a list of actual and predicted classes
            for i, actualClass in enumerate(actual):
                # Count the number of correct classifications and store them in the
                # confusion matrix
                actualClass = np.int(actualClass)-1

                # Count all misclassifications
                for j in predicted[i]:
                    confusionMatrix[np.int(j)-1, actualClass] += 1

        return confusionMatrix, classLabels

    def ConvertToSVMFormat(self, labels, values):
        '''
        Convert the training set data to SVM format
        Format: label feature_1:value feature_2:value feature_3:value ...
        '''
        prob_y = []
        prob_x = []

        for label, value_row in zip(labels, values):
            xi = {}
            for ind, val in enumerate(value_row):
                xi[int(ind)+1] = float(val)
            prob_x += [xi]
            for ind, lab in enumerate(label):
                if lab == 1: true_label = ind+1
            prob_y += [float(true_label)]
        return prob_y, prob_x

    def CreatePerObjectClassTable(self, classes):
        '''
    	Saves object keys and classes to a SQL table
    	'''
        p = Properties.getInstance()
        if p.class_table is None:
            raise ValueError('"class_table" in properties file is not set.')

        index_cols = dbconnect.UniqueObjectClause()
        class_cols = dbconnect.UniqueObjectClause() + ', class, class_number'
        class_col_defs = dbconnect.object_key_defs() + ', class VARCHAR (%d)'%(max([len(c.label) for c in self.classBins])+1) + ', class_number INT'

        # Drop must be explicitly asked for Classifier.ScoreAll
        db = dbconnect.DBConnect.getInstance()
        db.execute('DROP TABLE IF EXISTS %s'%(p.class_table))
        db.execute('CREATE TABLE %s (%s)'%(p.class_table, class_col_defs))
        db.execute('CREATE INDEX idx_%s ON %s (%s)'%(p.class_table, p.class_table, index_cols))
        for clNum, clName in enumerate(self.perClassObjects.keys()):
            for obj in self.perClassObjects[clName]:
                query = ''.join(['INSERT INTO ',p.class_table,' (',class_cols,') VALUES (',str(obj[0]),', ',str(obj[1]),', "',clName,'", ',str(clNum+1),')'])
                db.execute(query)

        query = ''.join(['ALTER TABLE ',p.class_table,' ORDER BY ',p.image_id,' ASC, ',p.object_id,' ASC'])
        db.execute(query)
        db.Commit()

    def FilterObjectsFromClassN(self, classN = None, keys = None):
        '''
    	Filter the input objects to output the keys of those in classN, 
    	using a defined SVM model classifier.
    	'''
        # Retrieve instance of the database connection
        db = dbconnect.DBConnect.getInstance()
        object_data = {}
        if keys != []:
            if len(keys) == len(dbconnect.image_key_columns()):
                # Retrieve instance of the data model and retrieve objects in the requested image
                dm = DataModel.getInstance()
                obKeys = dm.GetObjectsFromImage(keys[0])
            else:
                obKeys = keys
            for key in obKeys:
                object_data[key] = db.GetCellDataForClassifier(key)

        sorted_keys = sorted(object_data.keys())
        values_array = np.array([object_data[key] for key in sorted_keys])
        scaled_values = list(self.ScaleData(values_array))
        labels = [(1,-1)]*len(scaled_values) # Toy labels, input data is not yet labelled.
        svm_labels, svm_values = self.ConvertToSVMFormat(labels, scaled_values)
        pred_labels = svmutil.svm_predict(svm_labels, svm_values, self.model)

        # Group the object keys per class
        classObjects = {}
        for index in range(1, len(self.classBins)+1):
            classObjects[float(index)] = []
        for index, label in enumerate(pred_labels[0]):
            classObjects[label].append(sorted_keys[index])

        # Return either a summary of all classes and their corresponding objects
        # or just the objects for a specific class
        if classN is None:
            return classObjects
        else:
            return classObjects[classN]

    def IsTrained(self):
        return self.model is not None

    def LinearScale(self, value, low_lim, up_lim, feat_min, feat_max):
        return low_lim + (up_lim-low_lim)*(value-feat_min) / (feat_max-feat_min)

    def LoadModel(self, model_file_name):
        self.model = svmutil.svm_load_model(model_file_name)
        f = open(model_file_name, 'r')

        # Load bin labels, feat_max, feat_min
        for line in f:
            heading = line.split(':')
            if heading[0] == '#bins':
                self.bin_labels = [str(elem) for elem in heading[1].strip().split(',')]
            elif heading[0] == '#feat_min':
                self.feat_min = np.array([float(elem) for elem in heading[1].strip().split(',')])
            elif heading[0] == '#feat_max':
                self.feat_max = np.array([float(elem) for elem in heading[1].strip().split(',')])

        f.close()

    def PerImageCounts(self, filter_name=None, cb=None):
        # Clear the current perClassObjects storage
        for bin in self.classBins:
            self.perClassObjects[bin.label] = []

        # Retrieve a data model instance
        dm = DataModel.getInstance()

        # Retrieve image keys and initialize variables
        imageKeys = dm.GetAllImageKeys(filter_name)
        imageAmount = float(len(imageKeys))
        perImageData = []

        # Process all images
        for k_index, imKey in enumerate(imageKeys):
            try:
                # Retrieve the keys of the objects in the current image
                obKeys = dm.GetObjectsFromImage(imKey)
            except:
                raise 'No such image: %s' % (imKey,)
                return

            # Calculate the amount of hits for each of the classes in the current image
            classHits = {}
            objectCount = [imKey[0]]
            if obKeys:
                classObjects = self.FilterObjectsFromClassN(keys = [imKey])
                for clNum, bin in enumerate(self.classBins):
                    # Get the objects from the image which belong to the selected class
                    classHits[bin.label] = classObjects[float(clNum+1)]

                    # Store the total object count of this class for the current image
                    nrHits = len(classHits[bin.label])
                    objectCount.append(nrHits)

                    # Store the objects for the current class and image grouped
                    # by class if any are found for this class in the selected image
                    if nrHits > 0:
                        self.perClassObjects[bin.label] += classHits[bin.label]
            else:
                # If there are objects in the image, add zeros for all bins
                [objectCount.append(0) for bin in self.classBins]

            # Store the results for the current image and update the callback
            # function if available
            perImageData.append(objectCount)
            if cb:
                cb(min(1, k_index/imageAmount))

        return perImageData

    def PermuteSequence(self, seq):
        n = len(seq)
        if n <= 1: return seq

        mid = int(n/2)
        left = self.PermuteSequence(seq[:mid])
        right = self.PermuteSequence(seq[mid+1:])

        ret = [seq[mid]]
        while left or right:
            if left: ret.append(left.pop(0))
            if right: ret.append(right.pop(0))
        return ret

    def SaveModel(self, model_file_name, bin_labels):
        svmutil.svm_save_model(model_file_name, self.model)
        # Save feat_max, feat_min
        f = open(model_file_name, 'a')
        feat_min_str = [str(elem) for elem in self.feat_min]
        feat_max_str = [str(elem) for elem in self.feat_max]
        f.write('\n#bins:' + ','.join(bin_labels))
        f.write('\n#feat_min:' + ','.join(feat_min_str))
        f.write('\n#feat_max:' + ','.join(feat_max_str))
        f.close()

    def ScaleData(self, values, low_lim=0.0, up_lim=1.0):
        '''
    	Linearly scale the data to improve the efficiency of the classifier
    	'''
        row, col = np.shape(values)
        scaled_data = np.zeros((row, col))
        for j in xrange(col):
            scaled_data[:,j] = self.LinearScale(values[:,j], low_lim, up_lim,
                                                self.feat_min[j], self.feat_max[j])
        return scaled_data

    def ShowModel(self):
        return 'Trained a SVM Classifier using a radial basis function with ' \
               'parameters:\nC: %s\nGamma: %s\nCross-validation rate: %s' \
               % self.classifierParameters

    def Train(self, colNames, nValidation, labels, values, fout=None, callback = None):
        '''
    	Train a SVM model using optimized C and Gamma parameters and a training set.
    	'''
        # First make sure the supplied problem is in SVM format
        # TODO: Add Check for compatibility
        self.TranslateTrainingSet(labels, values)

        # Perform a grid-search to obtain the C and gamma parameters for C-SVM
        # classification
        if nValidation > 1:
            c, g = self.CalculateCGamma(callback, nValidation)
        else:
            c, g = self.CalculateCGamma(callback)

        # Retrain the model using the obtained C and gamma parameters to obtain
        # the final SVM model
        options = '-g %f -c %f -e 0.1 -t 2 -q' % (g, c)
        self.model = svmutil.svm_train(self.svm_train_labels, self.svm_train_values, options)

    def TranslateTrainingSet(self, labels, values):
        '''
    	Translate and scale CPAnalyst Classifier training set labels and values
    	to the SVM problem format.
    	'''
        adata = np.nan_to_num(np.array(values))
        self.feat_min = adata.min(axis=0)
        self.feat_max = adata.max(axis=0)
        self.feat_min[0] = 0.0
        values = self.ScaleData(adata)
        self.svm_train_labels, self.svm_train_values = self.ConvertToSVMFormat(labels, values)

    def UpdateBins(self, classBins):
        self.classBins = classBins

        # Reinitialize the objects per class storage
        self.perClassObjects = {}
        for bin in self.classBins:
            self.perClassObjects[bin.label] = []

    def XValidate(self, nPermutations):
        # Make sure all data is available in the training set
        if not self.classifier.UpdateTrainingSet():
            return

        # Initialize process dialog
        def cb(frac):
            cont, skip = dlg.Update(int(frac * 100.), '%d%% Complete'%(frac * 100.))
            if not cont: # Cancel was pressed
                dlg.Destroy()
                raise StopCalculating()

        dlg = wx.ProgressDialog('Performing grid search for optimal parameters...', '0% Complete', 100,
                                self.classifier, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | 
                                wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)

        # Define cross validation parameters
        totalGroups = 5
        trainingGroups = 4

        # Convert the trainingset into SVM format and search for optimal parameters
        # C and gamma using 5-fold cross-validation
        logging.info('Performing grid search for parameters C and gamma on entire training set...')
        self.TranslateTrainingSet(self.classifier.trainingSet.label_matrix, 
                                  self.classifier.trainingSet.values)
        C, gamma = self.CalculateCGamma(callback=cb)
        dlg.Destroy()
        logging.info('Grid search completed. Found optimal C=%d and gamma=%f.' % (C, gamma))

        # Define the options for the SVM training and initialize misclassification storage
        nObjects = self.classifier.trainingSet.label_matrix.shape[0]
        subsetSize = np.ceil(nObjects / float(totalGroups))
        indices = np.arange(nObjects)
        options = '-g %f -c %f -e 0.1 -t 2 -q' % (gamma, C)
        misclassifications = [[] for i in range(nObjects)]

        # Create group combinations and arrays of all labels and values
        dt = ','.join('i'*trainingGroups)
        trainingTotalGroups = list(np.fromiter(combinations(range(totalGroups),trainingGroups), dtype=dt, count=-1))
        #trainingTotalGroups = list(combinations(range(totalGroups), trainingGroups))
        allLabels = np.array(self.svm_train_labels)
        allValues = np.array(self.svm_train_values)

        # For all permutations of the subsets train the classifier on 4 totalGroups and
        # classify the remaining group for a number of random subsets
        logging.info('Calculating average classification accuracy %d times over a ' \
                     '%0.1f%%/%0.1f%% cross-validation process' % \
                     (nPermutations, trainingGroups/float(totalGroups)*100, \
                     (1-trainingGroups/float(totalGroups))*100))
        dlg = wx.ProgressDialog('Calculating average cross-validation accuracy...', '0% Complete', 100,
                                self.classifier, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | 
                                wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
        nTrainingTotalGroups = len(trainingTotalGroups)
        nOperations = float(nPermutations * nTrainingTotalGroups)
        for per in range(nPermutations):
            # Split the training set into subsets
            np.random.shuffle(indices)
            lastGroupStart = (totalGroups-1)*subsetSize
            subsets = np.hsplit(indices[0:lastGroupStart], (totalGroups-1))
            subsets.append(indices[lastGroupStart:],)

            for index, group in enumerate(trainingTotalGroups):
                # Retrieve indices of all objects in the training set
                trainingSet = np.hstack([subsets[i] for i in range(totalGroups) if i in group])

                # Train a classifier on the subset
                model = svmutil.svm_train(allLabels[trainingSet].tolist(),
                                          allValues[trainingSet].tolist(), options)

                # Predict the test set using the trained classifier
                testSet = np.hstack([subsets[i] for i in range(totalGroups) if i not in group])
                testLabels = svmutil.svm_predict(allLabels[testSet].tolist(),
                                                 allValues[testSet].tolist(), model)

                # Store all misclassifications
                [misclassifications[testSet[i]].append(testLabels[0][i]) \
                    for i in range(len(testLabels[0])) \
                    if testLabels[0][i] != allLabels[testSet][i]]

                # Update progress dialog
                cb((nTrainingTotalGroups * per + index) / nOperations)

        # Calculate average classification accuracy
        dlg.Destroy()
        logging.info('Average Classification Accuracy: %f%%' % \
                     ((1-len([item for sublist in misclassifications for item in sublist]) /\
                     float(nObjects * nPermutations))*100))

        return misclassifications

class visualizationChoiceBox(wx.Frame):
    def __init__(self, parent, id, title, btn1Cb = None, btn2Cb = None):
        # Initialize frame and containing panel
        wx.Frame.__init__(self, parent, id, title, size=(525, 90))
        panel = wx.Panel(self, -1)

        def button1Press(evt):
            btn1Cb()
            self.CloseDialog(evt)

        def button2Press(evt):
            btn2Cb()
            self.CloseDialog(evt)
            
        def bothPress(evt):
            btn1Cb()
            btn2Cb()
            self.CloseDialog(evt)

        # Generate the content of the dialog
        qText = wx.StaticText(panel, wx.NewId(), 'How would you like to visualize the results of the cross-validation process on the training set?', style=wx.ALIGN_CENTER)
        btn1 = wx.Button(panel, wx.NewId(), 'Confusion Matrix', (-1, -1), wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, button1Press, btn1)
        btn2 = wx.Button(panel, wx.NewId(), 'Dimension Reduction Plot', (-1, -1), wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, button2Press, btn2)
        btn3 = wx.Button(panel, wx.NewId(), 'Both', (-1, -1), wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, bothPress, btn3)
        btn4 = wx.Button(panel, wx.NewId(), 'Don\'t Visualize', (-1, -1), wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, self.CloseDialog, btn4)

        # Generate the layout of the dialog box, while inserting the content
        bbox = wx.BoxSizer(wx.HORIZONTAL)
        bbox.Add(btn1, 0, wx.ALL, 0)
        bbox.Add((-1, -1), 1)
        bbox.Add(btn2, 0, wx.ALL, 0)
        bbox.Add((-1, -1), 1)
        bbox.Add(btn3, 0, wx.ALL, 0)
        bbox.Add((-1, -1), 1)
        bbox.Add(btn4, 0, wx.ALL, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(qText, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(bbox, 0, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(vbox)

        # Show the dialog
        self.Centre()
        self.Show(True)

    def CloseDialog(self, evt):
        self.Close(True)
