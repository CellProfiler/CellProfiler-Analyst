#require "matrix"
#require "thread"
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

# Import support vector classifier, feature selection and Pipeline from scikits.learn
try:
    from scikits.learn.svm import SVC
    from scikits.learn import feature_selection
    from scikits.learn.pipeline import Pipeline
    from scikits.learn import __version__
    if __version__ != '0.8':
        logging.warn('SupportVectorMachine classifier requires scikits.learn '
                     'version 0.8, you have version %s'%(__version__))
    scikits_loaded = True
except:
    # classifier.py checks this so developers don't have to install it if they don't want it.
    scikits_loaded = False

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
        self.percentile = 90

        # Initialize the total object storage
        self.perClassObjects = {}
        self.feat_min, self.feat_max = None, None
        self.svm_train_labels, self.svm_train_values = None, None

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
        return '# of cross-validations: '

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
                actualClass = np.int(actualClass)

                # Count all misclassifications
                for j in predicted[i]:
                    confusionMatrix[np.int(j), actualClass] += 1

        return confusionMatrix, classLabels

    def ConvertToSVMFormat(self, labels, values):
        '''
        Convert the training set data to SVM format
        Format: label feature_1:value feature_2:value feature_3:value ...
        '''
        labels = np.array([np.nonzero(target > 0) for target in labels]).squeeze()
        return labels, values

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

        if p.db_type.lower() == 'mysql':
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
        if isinstance(keys, str):
            object_data[0] = db.GetCellDataForClassifier(keys)
        elif keys != []:
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
        scaled_values = self.ScaleData(values_array)
        pred_labels = self.model.predict(scaled_values)

        # Group the object keys per class
        classObjects = {}
        for index in range(1, len(self.classBins)+1):
            classObjects[float(index)] = []
        for index, label in enumerate(pred_labels):
            classObjects[np.int(label)+1].append(sorted_keys[index])

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
        import cPickle
        fh = open(model_file_name, 'r')
        try:
            self.model, self.bin_labels, self.feat_min, self.feat_max = cPickle.load(fh)
        except:
            self.model = None
            self.bin_labels = None
            self.feat_min = None
            self.feat_max = None
            logging.error('The loaded model was not a support vector machines model')
            raise TypeError
        finally:
            fh.close()

    def ParameterGridSearch(self, callback = None, nValidation = 5):
        '''
        Grid search for the best C and gamma parameters for the RBF Kernel.
        The efficiency of the parameters is evaluated using nValidation-fold
        cross-validation of the training data.
    
        As this process is time consuming and parallelizable, a number of
        threads equal to the number of cores in the computer is used for the
        calculations
        '''
        from scikits.learn.grid_search import GridSearchCV
        from scikits.learn.metrics import precision_score
        from scikits.learn.cross_val import StratifiedKFold
        # 
        # XXX: program crashes with >1 worker when running cpa.py
        #      No crash when running from classifier.py. Why?
        #
        n_workers = 1
        #try:
            #from multiprocessing import cpu_count
            #n_workers = cpu_count()
        #except:
            #n_workers = 1

        # Define the parameter ranges for C and gamma and perform a grid search for the optimal setting
        parameters = {'C': 2**np.arange(-5,11,2, dtype=float),
                      'gamma': 2**np.arange(3,-11,-2, dtype=float)}                
        clf = GridSearchCV(SVC(kernel='rbf'), parameters, n_jobs=n_workers, score_func=precision_score)
        clf.fit(self.svm_train_values, self.svm_train_labels, 
                cv=StratifiedKFold(self.svm_train_labels, nValidation))

        # Pick the best parameters as the ones with the maximum cross-validation rate
        bestParameters = max(clf.grid_scores_, key=lambda a: a[1])
        bestC = bestParameters[0]['C']
        bestGamma = bestParameters[0]['gamma']
        logging.info('Optimal values: C=%s g=%s rate=%s'%
                     (bestC, bestGamma, bestParameters[1]))
        return bestC, bestGamma

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

    def SaveModel(self, model_file_name, bin_labels):       
        import cPickle
        fh = open(model_file_name, 'w')
        cPickle.dump((self.model, bin_labels, self.feat_min, self.feat_max), fh)
        fh.close()

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
        if self.model is not None:
            return 'Trained the following support vector machines classifier:\n%s' % self.model.named_steps['svc']
        else:
            return ''

    def Train(self, colNames, nValidation, labels, values, fout=None, callback = None):
        '''
    	Train a SVM model using optimized C and Gamma parameters and a training set.
    	'''
        # First make sure the supplied problem is in SVM format
        self.TranslateTrainingSet(labels, values)

        # Perform a grid-search to obtain the C and gamma parameters for C-SVM
        # classification
        if nValidation > 1:
            C, gamma = self.ParameterGridSearch(callback, nValidation)
        else:
            C, gamma = self.ParameterGridSearch(callback)

        # Train the model using the obtained C and gamma parameters to obtain the final classifier
        self.model = Pipeline([('anova', feature_selection.SelectPercentile(feature_selection.f_classif,
                                                                            percentile=self.percentile)),
                               ('svc', SVC(kernel='rbf', C=C, gamma=gamma, tol=0.1))])
        self.model.fit(self.svm_train_values, self.svm_train_labels)

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

        # Convert the training set into SVM format and search for optimal parameters
        # C and gamma using 5-fold cross-validation
        logging.info('Performing grid search for parameters C and gamma on entire training set...')
        self.TranslateTrainingSet(self.classifier.trainingSet.label_matrix, 
                                  self.classifier.trainingSet.values)
        C, gamma = self.ParameterGridSearch(callback=cb)
        dlg.Destroy()
        logging.info('Grid search completed. Found optimal C=%d and gamma=%f.' % (C, gamma))

        # Create the classifier and initialize misclassification storage
        classifier = Pipeline([('anova', feature_selection.SelectPercentile(feature_selection.f_classif,
                                                                            percentile=self.percentile)),
                               ('svc', SVC(kernel='rbf', C=C, gamma=gamma, eps=0.1))])
        nObjects = self.classifier.trainingSet.label_matrix.shape[0]
        subsetSize = np.ceil(nObjects / float(totalGroups))
        indices = np.arange(nObjects)
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
                classifier.fit(allValues[trainingSet], allLabels[trainingSet])

                # Predict the test set using the trained classifier
                testSet = np.hstack([subsets[i] for i in range(totalGroups) if i not in group])
                testLabels = classifier.predict(allValues[testSet])

                # Store all misclassifications
                [misclassifications[testSet[i]].append(testLabels[i]) \
                    for i in range(len(testLabels)) \
                    if testLabels[i] != allLabels[testSet][i]]

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
