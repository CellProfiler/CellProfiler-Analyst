# Encoding: utf-8
from __future__ import with_statement

import matplotlib
matplotlib.use('WXAgg')

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

import tableviewer
from datamodel import DataModel
from imagecontrolpanel import ImageControlPanel
from properties import Properties
from scoredialog import ScoreDialog
import tilecollection
from trainingset import TrainingSet
from cStringIO import StringIO
from time import time
import icons
import dbconnect
import dirichletintegrate
import imagetools
import polyafit
import sortbin
import logging
import numpy as np
import os
import wx
import re
import cpa.helpmenu
from dimensredux import PlotMain

import fastgentleboostingmulticlass
from fastgentleboosting import FastGentleBoosting

#from supportvectormachines import SupportVectorMachines
from generalclassifier import GeneralClassifier

# number of cells to classify before prompting the user for whether to continue
MAX_ATTEMPTS = 10000

ID_CLASSIFIER = wx.NewId()
CREATE_NEW_FILTER = '*create new filter*'

required_fields = ['object_table', 'object_id', 'cell_x_loc', 'cell_y_loc']

class Classifier(wx.Frame):
    """
    GUI Interface and functionality for the Classifier.
    """

    def __init__(self, properties=None, parent=None, id=ID_CLASSIFIER, **kwargs):

        if properties is not None:
            global p
            p = properties
            global db
            db = dbconnect.DBConnect.getInstance()

        wx.Frame.__init__(self, parent, id=id, title='CPA/Classifier - %s' % \
                                                     (os.path.basename(p._filename)), size=(800, 600), **kwargs)
        if parent is None and not sys.platform.startswith('win'):
            self.tbicon = wx.TaskBarIcon()
            self.tbicon.SetIcon(icons.get_cpa_icon(), 'CPA/Classifier')
        else:
            self.SetIcon(icons.get_cpa_icon())
        self.SetName('Classifier')

        db.register_gui_parent(self)
        for field in required_fields:
            if not p.field_defined(field):
                raise Exception('Properties field "%s" is required for Classifier.' % (field))
                self.Destroy()
                return

        global dm
        dm = DataModel.getInstance()

        if not p.is_initialized():
            logging.critical('Classifier requires a properties file. Exiting.')
            raise Exception('Classifier requires a properties file. Exiting.')

        self.pmb = None
        self.worker = None
        self.trainingSet = None
        self.classBins = []
        self.binsCreated = 0
        self.chMap = p.image_channel_colors[:]
        self.toggleChMap = p.image_channel_colors[
                           :]  # used to store previous color mappings when toggling colors on/off with ctrl+1,2,3...
        self.brightness = 1.0
        self.scale = 1.0
        self.contrast = 'Linear'
        self.defaultTSFileName = None
        self.defaultModelFileName = None
        self.lastScoringFilter = None

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateMenus()

        self.CreateStatusBar()

        #### Create GUI elements
        # Top level - three split windows
        self.splitter = wx.SplitterWindow(self, style=wx.NO_BORDER | wx.SP_3DSASH)
        self.fetch_and_rules_panel = wx.Panel(self.splitter)
        self.bins_splitter = wx.SplitterWindow(self.splitter, style=wx.NO_BORDER | wx.SP_3DSASH)

        # fetch & rules
        self.fetch_panel = wx.Panel(self.fetch_and_rules_panel)
        self.rules_text = wx.TextCtrl(self.fetch_and_rules_panel, -1, size=(-1, -1),
                                      style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.rules_text.SetMinSize((-1, 50))
        self.find_rules_panel = wx.Panel(self.fetch_and_rules_panel)

        # sorting bins
        self.unclassified_panel = wx.Panel(self.bins_splitter)
        self.unclassified_box = wx.StaticBox(self.unclassified_panel, label='unclassified ' + p.object_name[1])
        self.unclassified_sizer = wx.StaticBoxSizer(self.unclassified_box, wx.VERTICAL)
        self.unclassifiedBin = sortbin.SortBin(parent=self.unclassified_panel,
                                               classifier=self,
                                               label='unclassified',
                                               parentSizer=self.unclassified_sizer)
        self.unclassified_sizer.Add(self.unclassifiedBin, proportion=1, flag=wx.EXPAND)
        self.unclassified_panel.SetSizer(self.unclassified_sizer)
        self.classified_bins_panel = wx.Panel(self.bins_splitter)

        # fetch objects interface
        self.nObjectsTxt = wx.TextCtrl(self.fetch_panel, id=-1, value='20', size=(30, -1), style=wx.TE_PROCESS_ENTER)
        self.obClassChoice = wx.Choice(self.fetch_panel, id=-1, choices=['random'])
        self.filterChoice = wx.Choice(self.fetch_panel, id=-1,
                                      choices=['experiment', 'image'] + p._filters_ordered + p._groups_ordered + [
                                          CREATE_NEW_FILTER])
        self.fetchFromGroupSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetchBtn = wx.Button(self.fetch_panel, -1, 'Fetch!')

        # find rules interface
        self.nRulesTxt = wx.TextCtrl(self.find_rules_panel, -1, value='5', size=(30, -1))
        self.trainClassifierBtn = wx.Button(self.find_rules_panel, -1, 'Train Classifier')
        self.scoreAllBtn = wx.Button(self.find_rules_panel, -1, 'Score All')
        self.scoreImageBtn = wx.Button(self.find_rules_panel, -1, 'Score Image')

        # JEN - Start Add
        self.openDimensReduxBtn = wx.Button(self.find_rules_panel, -1, 'Dimension Reduction')
        # JEN - End Add

        # add sorting class
        self.addSortClassBtn = wx.Button(self.GetStatusBar(), -1, "Add new class", style=wx.BU_EXACTFIT)

        #### Create Sizers
        self.fetchSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.find_rules_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetch_and_rules_sizer = wx.BoxSizer(wx.VERTICAL)
        self.classified_bins_sizer = wx.BoxSizer(wx.HORIZONTAL)


        #### Add elements to sizers and splitters
        # fetch panel
        self.fetchSizer.AddStretchSpacer()
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'Fetch'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5, 20))
        self.fetchSizer.Add(self.nObjectsTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5, 20))
        self.fetchSizer.Add(self.obClassChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5, 20))
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, p.object_name[1]), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5, 20))
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'from'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5, 20))
        self.fetchSizer.Add(self.filterChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((10, 20))
        self.fetchSizer.Add(self.fetchFromGroupSizer, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5, 20))
        self.fetchSizer.Add(self.fetchBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddStretchSpacer()
        self.fetch_panel.SetSizerAndFit(self.fetchSizer)

        # Train classifier panel
        self.find_rules_sizer.AddStretchSpacer()
        self.find_rules_sizer.Add((5, 20))
        self.complexityTxt = wx.StaticText(self.find_rules_panel, -1, '')
        self.find_rules_sizer.Add(self.complexityTxt)
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(self.nRulesTxt)
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(self.trainClassifierBtn)
        # Cross Validation Button
        self.evaluationBtn = wx.Button(self.find_rules_panel, -1, 'Plot Evaluation')
        self.evaluationBtn.Disable()
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(self.evaluationBtn)
        self.Bind(wx.EVT_BUTTON, self.OnEvaluation, self.evaluationBtn)
        # Plot nice graphics Button
        self.find_rules_sizer.Add((5, 20))


        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(self.scoreAllBtn)
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(self.scoreImageBtn)
        self.find_rules_sizer.Add((5, 20))
        # JEN - Start Add
        self.find_rules_sizer.Add(self.openDimensReduxBtn)
        self.find_rules_sizer.Add((5, 20))
        # JEN - End Add
        self.find_rules_panel.SetSizerAndFit(self.find_rules_sizer)

        # fetch and rules panel
        self.fetch_and_rules_sizer.Add((5, 5))
        self.fetch_and_rules_sizer.Add(self.fetch_panel, flag=wx.EXPAND)
        self.fetch_and_rules_sizer.Add((5, 5))
        self.fetch_and_rules_sizer.Add(self.rules_text, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        self.fetch_and_rules_sizer.Add((5, 5))
        self.fetch_and_rules_sizer.Add(self.find_rules_panel, flag=wx.EXPAND)
        self.fetch_and_rules_panel.SetSizerAndFit(self.fetch_and_rules_sizer)

        # classified bins panel
        self.classified_bins_panel.SetSizer(self.classified_bins_sizer)

        # splitter windows
        self.splitter.SplitHorizontally(self.fetch_and_rules_panel, self.bins_splitter,
                                        self.fetch_and_rules_panel.GetMinSize()[1])
        self.bins_splitter.SplitHorizontally(self.unclassified_panel, self.classified_bins_panel)

        self.splitter.SetSashGravity(0.0)
        self.bins_splitter.SetSashGravity(0.5)

        self.splitter.SetMinimumPaneSize(max(50, self.fetch_and_rules_panel.GetMinHeight()))
        self.bins_splitter.SetMinimumPaneSize(50)
        self.SetMinSize((self.fetch_and_rules_panel.GetMinWidth(), 4 * 50 + self.fetch_and_rules_panel.GetMinHeight()))

        # Set initial state
        self.obClassChoice.SetSelection(0)
        self.filterChoice.SetSelection(0)
        self.trainClassifierBtn.Disable()
        self.scoreAllBtn.Disable()
        self.scoreImageBtn.Disable()
        # JEN - Start Add
        self.openDimensReduxBtn.Disable()
        # JEN - End Add
        self.fetchSizer.Hide(self.fetchFromGroupSizer)

        #######################
        #### Model Section ####
        #######################

        # Define Classifiers
        RandomForestClassifier = GeneralClassifier("ensemble.RandomForestClassifier()", self)
        AdaBoostClassifier = GeneralClassifier("ensemble.AdaBoostClassifier()", self)
        SVC = GeneralClassifier("svm.SVC(probability=True)", self) # Need to turn on probs
        
        GradientBoostingClassifier = GeneralClassifier("ensemble.GradientBoostingClassifier()", self)
        LogisticRegression = GeneralClassifier("linear_model.LogisticRegression()", self)
        LDA = GeneralClassifier("lda.LDA()", self)
        KNeighborsClassifier = GeneralClassifier("neighbors.KNeighborsClassifier()", self)
        FastGentleBoostingClassifier = FastGentleBoosting(self)

        # JK - Start Add
        # Define the Random Forest classification algorithm to be default and set the default
        self.algorithm = RandomForestClassifier
        self.complexityTxt.SetLabel(str(self.algorithm.ComplexityTxt()))

        self.algorithms = {
            'RandomForestClassifier': RandomForestClassifier,
            'AdaBoostClassifier': AdaBoostClassifier,
            'SVC' : SVC,
            'GradientBoostingClassifier': GradientBoostingClassifier,
            'LogisticRegression': LogisticRegression,
            'LDA': LDA,
            'KNeighborsClassifier': KNeighborsClassifier,
            'FastGentleBoosting' : FastGentleBoostingClassifier
        }

        #####################
        #### GUI Section ####
        #####################

        # add the default classes
        #for class in range(1, num_classes+1):
        self.AddSortClass('positive')
        self.AddSortClass('negative')

        self.Layout()

        self.Center()
        self.MapChannels(p.image_channel_colors[:])
        self.BindMouseOverHelpText()

        # do event binding
        self.Bind(wx.EVT_CHOICE, self.OnSelectFilter, self.filterChoice)
        self.Bind(wx.EVT_BUTTON, self.OnFetch, self.fetchBtn)
        self.Bind(wx.EVT_BUTTON, self.OnAddSortClass, self.addSortClassBtn)
        self.Bind(wx.EVT_BUTTON, self.OnTrainClassifier, self.trainClassifierBtn)
        self.Bind(wx.EVT_BUTTON, self.ScoreAll, self.scoreAllBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreImage, self.scoreImageBtn)
        #self.Bind(wx.EVT_BUTTON, self.OnInspect, self.inspectBtn)
        # JEN - Start Add
        self.Bind(wx.EVT_BUTTON, self.OpenDimensRedux, self.openDimensReduxBtn)
        # JEN - End Add
        self.nObjectsTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.nRulesTxt.Bind(wx.EVT_TEXT, self.ValidateNumberOfRules)
        self.nObjectsTxt.Bind(wx.EVT_TEXT_ENTER, self.OnFetch)

        self.GetStatusBar().Bind(wx.EVT_SIZE, self.status_bar_onsize)
        wx.CallAfter(self.status_bar_onsize, None)

        self.Bind(wx.EVT_MENU, self.OnClose, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHAR, self.OnKey)  # Doesn't work for windows
        tilecollection.EVT_TILE_UPDATED(self, self.OnTileUpdated)
        self.Bind(sortbin.EVT_QUANTITY_CHANGED, self.QuantityChanged)

        # If there's a default training set. Ask to load it.
        if p.training_set and os.access(p.training_set, os.R_OK):
            # file existence is checked in Properties module
            dlg = wx.MessageDialog(self,
                                   'Would you like to load the training set defined in your properties file?\n\n%s\n\nTo prevent this message from appearing. Remove the training_set field from your properties file.' % (
                                   p.training_set),
                                   'Load Default Training Set?', wx.YES_NO | wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.LoadTrainingSet(p.training_set)

        self.AutoSave() # Autosave try out


 

    # JEN - Start Add
    def OpenDimensRedux(self, event):
        self.pca_main = PlotMain(self, properties=p)
        self.pca_main.Show(True)

    # JEN - End Add

    def status_bar_onsize(self, event):
        # draw the "add sort class..." button in the status bar
        button = self.addSortClassBtn
        width, height = self.GetStatusBar().GetClientSize()
        # diagonal lines drawn on mac, so move let by height.
        button.SetPosition((width - button.GetSize()[0] - 1 - height, button.GetPosition()[1]))

    # JK - Start Add
    def AlgorithmSelect(self, event):
        selectedItem = re.sub('[\W_]+', '', self.classifierMenu.FindItemById(event.GetId()).GetText())
        try:
            self.algorithm = self.algorithms[selectedItem]
            logging.info("Classifier " + selectedItem + " successfully loaded")
            self.complexityTxt.SetLabel(str(self.algorithm.ComplexityTxt())) # Set new label to # box
        except:
            # Fall back to default algorithm
            logging.error('Could not load specified algorithm, falling back to RandomForestClassifier.')
            self.algorithm = self.algorithms['RandomForestClassifier']

        # Update the GUI complexity text and classifier description
        # self.complexityTxt.SetLabel(self.algorithm.get_params())
        self.complexityTxt.Parent.Layout()
        self.rules_text.Value = ''

        # Make sure the classifier is cleared before running a new training session
        self.algorithm.ClearModel()

        # Update the classBins in the model
        self.algorithm.UpdateBins(self.classBins)
        for bin in self.classBins:
            bin.trained = False
        self.UpdateClassChoices()

        # Disable scoring buttons
        self.scoreAllBtn.Disable()
        self.scoreImageBtn.Disable()
        self.openDimensReduxBtn.Disable()

    # JK - End Add

    def BindMouseOverHelpText(self):
        self.nObjectsTxt.SetToolTip(wx.ToolTip('The number of %s to fetch.' % (p.object_name[1])))
        self.obClassChoice.SetToolTip(wx.ToolTip('The phenotype of the %s.' % (p.object_name[1])))
        self.obClassChoice.GetToolTip().SetDelay(3000)
        self.filterChoice.SetToolTip(wx.ToolTip(
            'Filters fetched %s to be from a subset of your images. (See groups and filters in the properties file)' % (
            p.object_name[1])))
        self.filterChoice.GetToolTip().SetDelay(3000)
        self.fetchBtn.SetToolTip(wx.ToolTip('Fetches images of %s to be sorted.' % (p.object_name[1])))
        self.rules_text.SetToolTip(wx.ToolTip('Rules are displayed in this text box.'))
        self.nRulesTxt.SetToolTip(
            wx.ToolTip('The number of top features to show or fast gentle boosting learners.'))
        self.trainClassifierBtn.SetToolTip(wx.ToolTip(
            'Tell Classifier to train itself for classification of your phenotypes as you have sorted them.'))
        self.scoreAllBtn.SetToolTip(wx.ToolTip(
            'Compute %s counts and per-group enrichments across your experiment. (This may take a while)' % (
            p.object_name[0])))
        self.scoreImageBtn.SetToolTip(
            wx.ToolTip('Highlight %s of a particular phenotype in an image.' % (p.object_name[1])))
        self.addSortClassBtn.SetToolTip(wx.ToolTip('Add another bin to sort your %s into.' % (p.object_name[1])))
        self.unclassifiedBin.SetToolTip(
            wx.ToolTip('%s in this bin should be sorted into the bins below.' % (p.object_name[1].capitalize())))

    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        keycode = evt.GetKeyCode()
        chIdx = keycode - 49
        if evt.ControlDown() or evt.CmdDown():
            # ctrl+N toggles channel #N on/off
            if len(self.chMap) > chIdx >= 0:
                self.ToggleChannel(chIdx)
            else:
                evt.Skip()
        else:
            evt.Skip()

    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            for (idx, color, item, menu) in self.chMapById.values():
                if idx == chIdx and color.lower() == self.toggleChMap[chIdx].lower():
                    item.Check()
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            for (idx, color, item, menu) in self.chMapById.values():
                if idx == chIdx and color.lower() == 'none':
                    item.Check()
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)

    def CreateMenus(self):
        ''' Create file menu and menu items '''
        self.fileMenu = wx.Menu()
        self.loadTSMenuItem = self.fileMenu.Append(-1, text='Load training set\tCtrl+O',
                                                   help='Loads objects and classes specified in a training set file.')
        self.saveTSMenuItem = self.fileMenu.Append(-1, text='Save training set\tCtrl+S',
                                                   help='Save your training set to file so you can reload these classified cells again.')
        self.loadFullTSMenuItem = self.fileMenu.Append(-1, text='Load training set (CSV)',
                                                   help='Loads objects and classes specified in a training set file.')
        self.saveFullTSMenuItem = self.fileMenu.Append(-1, text='Save training set (CSV)',
                                                   help='Save your training data as CSV')
        self.fileMenu.AppendSeparator()
        # JEN - Start Add
        self.loadModelMenuItem = self.fileMenu.Append(-1, text='Load classifier model\tCtrl+Shift+O', help='Loads a classifier model specified in a text file')
        self.saveModelMenuItem = self.fileMenu.Append(-1, text='Save classifier model\tCtrl+Shift+S', help='Save your classifier model to file so you can use it again on this or other experiments.')
        self.fileMenu.AppendSeparator()
        # JEN - End Add
        self.exitMenuItem = self.fileMenu.Append(id=wx.ID_EXIT, text='Exit\tCtrl+Q', help='Exit classifier')
        self.GetMenuBar().Append(self.fileMenu, 'File')

        # View Menu
        viewMenu = wx.Menu()
        imageControlsMenuItem = viewMenu.Append(-1, text='Image Controls\tCtrl+Shift+I',
                                                help='Launches a control panel for adjusting image brightness, size, etc.')
        self.GetMenuBar().Append(viewMenu, 'View')

        # Rules menu
        # rulesMenu = wx.Menu()
        # rulesEditMenuItem = rulesMenu.Append(-1, text=u'Edit…', help='Lets you edit the rules')
        # self.GetMenuBar().Append(rulesMenu, 'Rules')

        # Channel Menus
        self.CreateChannelMenus()

        # Classifier Type chooser
        self.classifierMenu = wx.Menu();

        # helps translating the checked item for loadModel
        self.classifier2ItemId = {
            'RandomForestClassifier' : 1,
            'AdaBoostClassifier' : 2,
            'SVC' : 3,
            'GradientBoostingClassifier': 4,
            'LogisticRegression': 5,
            'LDA': 6,
            'KNeighborsClassifier': 7,
            'FastGentleBoosting' : 8
        }

        rfMenuItem = self.classifierMenu.AppendRadioItem(1, text='RandomForest Classifier', help='Uses RandomForest to classify')
        adaMenuItem = self.classifierMenu.AppendRadioItem(2, text='AdaBoost Classifier', help='Uses AdaBoost to classify.')
        svcMenuItem = self.classifierMenu.AppendRadioItem(3, text='SVC', help='Uses Support Vector Machines to classify.')
        gbMenuItem = self.classifierMenu.AppendRadioItem(4, text='GradientBoosting Classifier', help='Uses GradientBoosting to classify')
        lgMenuItem = self.classifierMenu.AppendRadioItem(5, text='LogisticRegression', help='Uses LogisticRegression to classify.')
        ldaMenuItem = self.classifierMenu.AppendRadioItem(6, text='LDA', help='Uses LDA to classify.')
        knnMenuItem = self.classifierMenu.AppendRadioItem(7, text='KNeighbors Classifier', help='Uses the kNN algorithm to classify.')
        fgbMenuItem = self.classifierMenu.AppendRadioItem(8, text='Fast Gentle Boosting', help='Uses the Fast Gentle Boosting algorithm to find classifier rules.')

        self.GetMenuBar().Append(self.classifierMenu, 'Classifier')

        # Evaluation menu
        self.evalMenu = wx.Menu()

        # Plotting options
        reportMenuItem = self.evalMenu.AppendRadioItem(-1, text=u'Classification Report', help='Visualization of Accuracy, Recall and F1 Scores')
        confusionMenuItem = self.evalMenu.AppendRadioItem(-1, text=u'Confusion Matrix', help='Visualizes the Confusion Matrix')
        #paramsEditMenuItem = self.evalMenu.AppendRadioItem(2, text=u'ROC Curve', help='Plots a One vs all ROC Curve and calculates the area under the curve')
        #featureSelectMenuItem = self.evalMenu.AppendRadioItem(3, text=u'Precision Recall Curve', help='Plots a One vs all Precision Recall Curve')
        #learningMenuItem = self.evalMenu.AppendRadioItem(4, text=u'Learning Curve', help='Plots a One vs all Learning Curve')

        self.GetMenuBar().Append(self.evalMenu, 'Evaluation')


        # Advanced menu
        advancedMenu = wx.Menu()
        rulesEditMenuItem = advancedMenu.Append(-1, text=u'Edit Rules', help='Lets you edit the rules')
        paramsEditMenuItem = advancedMenu.Append(-1, text=u'Edit Parameters', help='Lets you edit the hyperparameters')
        featureSelectMenuItem = advancedMenu.Append(-1, text=u'Check Features', help='Check the variance of your Training Data')
        self.GetMenuBar().Append(advancedMenu, 'Advanced')

        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self), 'Help')


        # Bind events to different menu items
        self.Bind(wx.EVT_MENU, self.OnLoadTrainingSet, self.loadTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnLoadFullTrainingSet, self.loadFullTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveTrainingSet, self.saveTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveFullTrainingSet, self.saveFullTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnLoadModel, self.loadModelMenuItem) # JEN - Added
        self.Bind(wx.EVT_MENU, self.SaveModel, self.saveModelMenuItem) # JEN - Added
        self.Bind(wx.EVT_MENU, self.OnShowImageControls, imageControlsMenuItem)
        self.Bind(wx.EVT_MENU, self.OnParamsEdit, paramsEditMenuItem) 
        self.Bind(wx.EVT_MENU, self.OnRulesEdit, rulesEditMenuItem)
        self.Bind(wx.EVT_MENU, self.OnFeatureSelect, featureSelectMenuItem)


        # Bind events for algorithms
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, rfMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, adaMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, svcMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, gbMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, lgMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, ldaMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, knnMenuItem)
        self.Bind(wx.EVT_MENU, self.AlgorithmSelect, fgbMenuItem)


    def CreateChannelMenus(self):
        ''' Create color-selection menus for each channel. '''

        # Clean up existing channel menus
        try:
            menus = set([items[2].Menu for items in self.chMapById.values()])
            for menu in menus:
                for i, mbmenu in enumerate(self.MenuBar.Menus):
                    if mbmenu[0] == menu:
                        self.MenuBar.Remove(i)
            for menu in menus:
                menu.Destroy()
            if 'imagesMenu' in self.__dict__:
                self.MenuBar.Remove(self.MenuBar.FindMenu('Images'))
                self.imagesMenu.Destroy()
        except:
            pass

        # Initialize variables
        self.imagesMenu = wx.Menu()
        chIndex = 0
        self.chMapById = {}
        self.imMapById = {}
        channel_names = []
        startIndex = 0
        channelIds = []

        for i, chans in enumerate(p.channels_per_image):
            chans = int(chans)
            # Construct channel names, for RGB images, append a # to the end of
            # each channel.
            name = p.image_names[i]
            if chans == 1:
                channel_names += [name]
            elif chans == 3:  # RGB
                channel_names += ['%s [%s]' % (name, x) for x in 'RGB']
            elif chans == 4:  # RGBA
                channel_names += ['%s [%s]' % (name, x) for x in 'RGBA']
            else:
                channel_names += ['%s [%s]' % (name, x + 1) for x in range(chans)]

        # Zip channel names with channel map
        zippedChNamesChMap = zip(channel_names, self.chMap)

        # Loop over all the image names in the properties file
        for i, chans in enumerate(p.image_names):
            channelIds = []
            # Loop over all the channels
            for j in range(0, int(p.channels_per_image[i])):
                (channel, setColor) = zippedChNamesChMap[chIndex]
                channel_menu = wx.Menu()
                for color in ['Red', 'Green', 'Blue', 'Cyan', 'Magenta', 'Yellow', 'Gray', 'None']:
                    id = wx.NewId()
                    # Create a radio item that maps an id and a color.
                    item = channel_menu.AppendRadioItem(id, color)
                    # Add a new chmapbyId object
                    self.chMapById[id] = (chIndex, color, item, channel_menu)
                    # If lowercase color matches what it was originally set to...
                    if color.lower() == setColor.lower():
                        # Check off the item
                        item.Check()
                    # Bind
                    self.Bind(wx.EVT_MENU, self.OnMapChannels, item)
                    # Add appropriate Ids to imMapById
                    if ((int(p.channels_per_image[i]) == 1 and color == 'Gray') or
                            (int(p.channels_per_image[i]) > 1 and j == 0 and color == 'Red') or
                            (int(p.channels_per_image[i]) > 1 and j == 2 and color == 'Blue') or
                            (int(p.channels_per_image[i]) > 1 and j == 1 and color == 'Green')):
                        channelIds = channelIds + [id]
                # Add new menu item
                self.GetMenuBar().Append(channel_menu, channel)
                chIndex += 1
            # New id for the image as a whole
            id = wx.NewId()
            item = self.imagesMenu.AppendRadioItem(id, p.image_names[i])
            # Effectively this code creates a data structure that stores relevant info with ID as a key
            self.imMapById[id] = (int(p.channels_per_image[i]), item, startIndex, channelIds)
            # Binds the event menu to OnFetchImage (below) and item
            self.Bind(wx.EVT_MENU, self.OnFetchImage, item)
            startIndex += int(p.channels_per_image[i])
        # Add the "none" image and check it off.
        id = wx.NewId()
        item = self.imagesMenu.AppendRadioItem(id, 'None')
        self.Bind(wx.EVT_MENU, self.OnFetchImage, item)
        item.Check()  # Add new "Images" menu bar item
        self.GetMenuBar().Append(self.imagesMenu, 'Images')

    #######################################
    # OnFetchImage
    #
    # Allows user to display one image at a time.  If image is single channel,
    # displays the image as gray.  If image is multichannel, displays image as
    # RGB.
    # @param self, evt
    #######################################
    def OnFetchImage(self, evt=None):

        # Set every channel to black and set all the toggle options to 'none'
        for ids in self.chMapById.keys():
            (chIndex, color, item, channel_menu) = self.chMapById[ids]
            if (color.lower() == 'none'):
                item.Check()
        for ids in self.imMapById.keys():
            (cpi, itm, si, channelIds) = self.imMapById[ids]
            if cpi == 3:
                self.chMap[si] = 'none'
                self.chMap[si + 1] = 'none'
                self.chMap[si + 2] = 'none'
                self.toggleChMap[si] = 'none'
                self.toggleChMap[si + 1] = 'none'
                self.toggleChMap[si + 2] = 'none'
            else:
                self.chMap[si] = 'none'
                self.toggleChMap[si] = 'none'

        # Determine what image was selected based on the event.  Set channel to appropriate color(s)
        if evt.GetId() in self.imMapById.keys():

            (chanPerIm, item, startIndex, channelIds) = self.imMapById[evt.GetId()]

            if chanPerIm == 1:
                # Set channel map and toggleChMap values.
                self.chMap[startIndex] = 'gray'
                self.toggleChMap[startIndex] = 'gray'

                # Toggle the option for the independent channel menu
                (chIndex, color, item, channel_menu) = self.chMapById[channelIds[0]]
                item.Check()
            else:
                RGB = ['red', 'green', 'blue'] + ['none'] * chanPerIm
                for i in range(chanPerIm):
                    # Set chMap and toggleChMap values
                    self.chMap[startIndex + i] = RGB[i]
                    self.toggleChMap[startIndex + i] = RGB[i]
                    # Toggle the option in the independent channel menus
                    (chIndex, color, item, channel_menu) = self.chMapById[channelIds[i]]
                    item.Check()

        self.MapChannels(self.chMap)
        #######################################
        # /OnFetchImage
        #######################################

    def AddSortClass(self, label):
        ''' Create a new SortBin in a new StaticBoxSizer with the given label.
        This sizer is then added to the classified_bins_sizer. '''
        bin = sortbin.SortBin(parent=self.classified_bins_panel, label=label,
                              classifier=self)

        box = wx.StaticBox(self.classified_bins_panel, label=label)
        # NOTE: bin must be created after sizer or drop events will occur on the sizer
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        bin.parentSizer = sizer

        sizer.Add(bin, proportion=1, flag=wx.EXPAND)
        self.classified_bins_sizer.Add(sizer, proportion=1, flag=wx.EXPAND)
        self.classBins.append(bin)
        self.algorithm.UpdateBins(self.classBins)
        self.classified_bins_panel.Layout()
        self.binsCreated += 1
        self.QuantityChanged()
        # IMPORTANT: required for drag and drop to work on Linux
        # see: http://trac.wxwidgets.org/ticket/2763
        box.Lower()

    def RemoveSortClass(self, label, clearModel=True):
        for bin in self.classBins:
            if bin.label == label:
                self.classBins.remove(bin)
                # Remove the label from the class dropdown menu
                self.obClassChoice.SetItems([item for item in self.obClassChoice.GetItems() if item != bin.label])
                self.obClassChoice.Select(0)
                # Remove the bin
                self.classified_bins_sizer.Remove(bin.parentSizer)
                wx.CallAfter(bin.Destroy)
                self.classified_bins_panel.Layout()
                break
        self.algorithm.UpdateBins([]);
        if clearModel:
            self.algorithm.ClearModel()
        self.rules_text.SetValue('')
        for bin in self.classBins:
            bin.trained = False
        self.UpdateClassChoices()
        self.QuantityChanged()

    def RemoveAllSortClasses(self, clearModel=True):
        # Note: can't use "for bin in self.classBins:"
        for label in [bin.label for bin in self.classBins]:
            self.RemoveSortClass(label, clearModel)

    def RenameClass(self, label):
        dlg = wx.TextEntryDialog(self, 'New class name:', 'Rename class')
        dlg.SetValue(label)
        if dlg.ShowModal() == wx.ID_OK:
            newLabel = dlg.GetValue()
            if newLabel != label and newLabel in [bin.label for bin in self.classBins]:
                errdlg = wx.MessageDialog(self, 'There is already a class with that name.', "Can't Name Class",
                                          wx.OK | wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    return self.RenameClass(label)
            if ' ' in newLabel:
                errdlg = wx.MessageDialog(self, 'Labels can not contain spaces', "Can't Name Class",
                                          wx.OK | wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    return self.RenameClass(label)
            for bin in self.classBins:
                if bin.label == label:
                    bin.label = newLabel
                    bin.UpdateQuantity()
                    break
            self.algorithm.UpdateBins(self.classBins)
            dlg.Destroy()
            updatedList = self.obClassChoice.GetItems()
            sel = self.obClassChoice.GetSelection()
            for i in xrange(len(updatedList)):
                if updatedList[i] == label:
                    updatedList[i] = newLabel
            self.obClassChoice.SetItems(updatedList)
            self.obClassChoice.SetSelection(sel)
            return wx.ID_OK
        return wx.ID_CANCEL

    def all_sort_bins(self):
        return [self.unclassifiedBin] + self.classBins

    def UpdateClassChoices(self):
        if not self.IsTrained():
            self.obClassChoice.SetItems(['random'])
            self.obClassChoice.SetSelection(0)
            self.scoreAllBtn.Disable()
            self.scoreImageBtn.Disable()
            self.openDimensReduxBtn.Disable()
            return
        sel = self.obClassChoice.GetSelection()
        selectableClasses = ['random'] 

        selectableClasses += [bin.label for bin in self.classBins if bin.trained]

        # DD: Add new option to select uncertain images
        if self.algorithm.IsTrained() and self.algorithm.name != "FastGentleBoosting":
            selectableClasses += ['uncertain']
        
        self.obClassChoice.SetItems(selectableClasses)
        if len(selectableClasses) < sel:
            sel = 0
        self.obClassChoice.SetSelection(sel)

    def QuantityChanged(self, evt=None):
        '''
        When the number of tiles in one of the SortBins has changed.
        Disable the buttons for training and checking accuracy if any bin is
        empty
        '''
        self.trainClassifierBtn.Enable()
        if hasattr(self, 'evaluationBtn'):
            self.evaluationBtn.Enable()
        if len(self.classBins) <= 1:
            self.trainClassifierBtn.Disable()
            if hasattr(self, 'evaluationBtn'):
                self.evaluationBtn.Disable()
        for bin in self.classBins:
            if bin.empty:
                self.trainClassifierBtn.Disable()
                if hasattr(self, 'evaluationBtn'):
                    self.evaluationBtn.Disable()

    def OnFetch(self, evt):
        # Parse out the GUI input values
        nObjects = int(self.nObjectsTxt.Value)
        obClass = self.obClassChoice.Selection
        obClassName = self.obClassChoice.GetStringSelection()
        fltr_sel = self.filterChoice.GetStringSelection()

        statusMsg = 'Fetched %d %s %s' % (nObjects, obClassName, p.object_name[1])

        # Get object keys
        obKeys = []
        # unclassified:
        if obClass == 0:
            if fltr_sel == 'experiment':
                obKeys = dm.GetRandomObjects(nObjects)
                statusMsg += ' from whole experiment'
            elif fltr_sel == 'image':
                imKey = self.GetGroupKeyFromGroupSizer()
                obKeys = dm.GetRandomObjects(nObjects, [imKey])
                statusMsg += ' from image %s' % (imKey,)
            elif fltr_sel in p._filters_ordered:
                filteredImKeys = db.GetFilteredImages(fltr_sel)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in filter "%s"' % (fltr_sel))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys)
                statusMsg += ' from filter "%s"' % (fltr_sel)
            elif fltr_sel in p._groups_ordered:
                # if the filter name is a group then it's actually a group
                groupName = fltr_sel
                groupKey = self.GetGroupKeyFromGroupSizer(groupName)
                filteredImKeys = dm.GetImagesInGroupWithWildcards(groupName, groupKey)
                colNames = dm.GetGroupColumnNames(groupName)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in group %s: %s' % (groupName,
                                                                               ', '.join(['%s=%s' % (n, v) for n, v in
                                                                                          zip(colNames, groupKey)])))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys)
                if not obKeys:
                    self.PostMessage('No cells were found in this group. Group %s: %s' % (groupName,
                                                                                          ', '.join(
                                                                                              ['%s=%s' % (n, v) for n, v
                                                                                               in zip(colNames,
                                                                                                      groupKey)])))
                    return
                statusMsg += ' from group %s: %s' % (groupName,
                                                     ', '.join(['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))

        # classified
        else:
            hits = 0
            # Get images within any selected filter or group
            if fltr_sel != 'experiment':
                if fltr_sel == 'image':
                    imKey = self.GetGroupKeyFromGroupSizer()
                    filteredImKeys = [imKey]
                elif fltr_sel in p._filters_ordered:
                    filteredImKeys = db.GetFilteredImages(fltr_sel)
                    if filteredImKeys == []:
                        self.PostMessage('No images were found in filter "%s"' % (fltr_sel))
                        return
                elif fltr_sel in p._groups_ordered:
                    group_name = fltr_sel
                    groupKey = self.GetGroupKeyFromGroupSizer(group_name)
                    colNames = dm.GetGroupColumnNames(group_name)
                    filteredImKeys = dm.GetImagesInGroupWithWildcards(group_name, groupKey)
                    if filteredImKeys == []:
                        self.PostMessage('No images were found in group %s: %s' % (group_name,
                                                                                   ', '.join(
                                                                                       ['%s=%s' % (n, v) for n, v in
                                                                                        zip(colNames, groupKey)])))
                        return

            total_attempts = attempts = 0
            # Now check which objects fall within the classification
            while len(obKeys) < nObjects:
                self.PostMessage('Gathering random %s.' % (p.object_name[1]))
                if fltr_sel == 'experiment':
                    if 0 and p.db_sqlite_file:
                        # This is incredibly slow in SQLite
                        # obKeysToTry = dm.GetRandomObjects(100)
                        # HACK: tack this query onto the where clause so we try
                        #       100 randomly distributed obkeys to try.
                        obKeysToTry = 'ABS(RANDOM()) %% %s < 100' % (dm.get_total_object_count())
                    else:
                        obKeysToTry = dm.GetRandomObjects(100)
                    loopMsg = ' from whole experiment'
                elif fltr_sel == 'image':
                    # All objects are tried in first pass
                    if attempts > 0:
                        break
                    imKey = self.GetGroupKeyFromGroupSizer()
                    obKeysToTry = [imKey]
                    loopMsg = ' from image %s' % (imKey,)
                else:
                    obKeysToTry = dm.GetRandomObjects(100, filteredImKeys)
                    obKeysToTry.sort()
                    if fltr_sel in p._filters_ordered:
                        loopMsg = ' from filter %s' % (fltr_sel)
                    elif fltr_sel in p._groups_ordered:
                        loopMsg = ' from group %s: %s' % (fltr_sel,
                                                          ', '.join(
                                                              ['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))

                self.PostMessage('Classifying %s.' % (p.object_name[1]))

                if obClassName == 'uncertain':
                    obKeys += self.algorithm.FilterObjectsFromClassN(obClass, obKeysToTry, uncertain=True)
                else:
                    obKeys += self.algorithm.FilterObjectsFromClassN(obClass, obKeysToTry)


                attempts += len(obKeysToTry)
                total_attempts += len(obKeysToTry)
                if attempts >= MAX_ATTEMPTS:
                    dlg = wx.MessageDialog(self, 'Found %d %s after %d attempts. Continue searching?'
                                           % (len(obKeys), p.object_name[1], total_attempts),
                                           'Continue searching?', wx.YES_NO | wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    dlg.Destroy()
                    if response == wx.ID_NO:
                        break
                    attempts = 0
            statusMsg += loopMsg

        self.unclassifiedBin.AddObjects(obKeys[:nObjects], self.chMap, pos='last')
        self.PostMessage(statusMsg)

    def OnTileUpdated(self, evt):
        '''
        When the tile loader returns the tile image update the tile.
        '''
        self.unclassifiedBin.UpdateTile(evt.data)
        for bin in self.classBins:
            bin.UpdateTile(evt.data)

    # JEN - Start Add
    def OnLoadModel(self, evt):
        '''
        Present user with file select dialog, then load selected classifier model.
        '''
        dlg = wx.FileDialog(self, "Select the file containing your classifier model.",
                            defaultDir=os.getcwd(), style=wx.OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadModel(filename)

    def LoadModel(self, filename):
        '''
        Loads the selected file and parses the classifier model.
        '''
        self.PostMessage('Loading classifier model from: %s' % filename)
        # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        os.chdir(os.path.split(filename)[0])
        self.defaultModelFileName = os.path.split(filename)[1]
        # self.RemoveAllSortClasses(False) # Don't remove sorted classes
        if True:

            # Save old name for checking
            tmp_name = self.algorithm.name

            # Now algorithm.name is different! Don't move it before tmp_name
            self.algorithm.LoadModel(filename)
            # Save to select for later
            select = self.algorithm.name

            if self.algorithm.name != tmp_name:
                logging.info("Detected different setted classifier: " + tmp_name + ", switching to " + self.algorithm.name)
                # Restore the name
                self.algorithm.name = tmp_name
                self.algorithm = self.algorithms[select]
                # Load again
                self.algorithm.LoadModel(filename)

            itemId = self.classifier2ItemId[select]
            # Checks the MenuItem
            self.classifierMenu.Check(itemId, True)

            # for label in self.algorithm.bin_labels:
            #     self.AddSortClass(label)
            for bin in self.classBins:
                 bin.trained = True
            self.scoreAllBtn.Enable()
            self.scoreImageBtn.Enable()
            self.PostMessage('Classifier model succesfully loaded')

            # Some User Information about the loaded Algorithm
            self.PostMessage('Loaded trained classifier: ' + self.algorithm.name + ' on classes:')
            for label in self.algorithm.bin_labels:
                self.PostMessage(label)
            self.PostMessage('CAUTION: Classifier needs to be trained on the current data set!')

        try:
            pass
        except:
            self.scoreAllBtn.Disable()
            self.scoreImageBtn.Disable()
            self.openDimensReduxBtn.Disable()

            logging.error('Error loading classifier model')
            self.PostMessage('Error loading classifier model')
        finally:
            self.UpdateClassChoices()
            self.keysAndCounts = None



    def SaveModel(self, evt=None):
        if not self.defaultModelFileName:
            self.defaultModelFileName = 'my_model.model'
        if not self.algorithm.classifier:
            logging.error('No classifier model has been created. Please create one before saving')
            return

        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(),
                                   defaultFile=self.defaultModelFileName,
                                   wildcard='Model files (*.model)|*.model|All files(*.*)|*.*',
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal() == wx.ID_OK:
            filename = saveDialog.GetPath()
            self.defaultModelFileName = os.path.split(filename)[1]
            bin_labels = [bin.label for bin in self.classBins]
            self.algorithm.SaveModel(filename, bin_labels)
            self.PostMessage('Classifier model succesfully saved.')

    # JEN - End Add

    def OnLoadTrainingSet(self, evt):
        '''
        Present user with file select dialog, then load selected training set.
        '''
        dlg = wx.FileDialog(self, "Select the file containing your classifier training set.",
                            defaultDir=os.getcwd(),
                            wildcard='Text files(*.txt)|*.txt|All files(*.*)|*.*',
                            style=wx.OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadTrainingSet(filename)

    def OnLoadFullTrainingSet(self, evt):
        '''
        Present user with file select dialog, then load selected training set.
        '''
        dlg = wx.FileDialog(self, "Select the file containing your classifier training set.",
                            defaultDir=os.getcwd(),
                            wildcard='Text files(*.csv)|*.csv|All files(*.*)|*.*',
                            style=wx.OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadTrainingSetCSV(filename)

    def LoadTrainingSet(self, filename):
        '''
        Loads the selected file, parses out object keys, and fetches the tiles.
        '''
        # pause tile loading
        with tilecollection.load_lock():
            self.PostMessage('Loading training set from: %s' % filename)
            # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
            self.defaultTSFileName = os.path.basename(filename)

            self.trainingSet = TrainingSet(p, filename, labels_only=False)

            self.RemoveAllSortClasses()
            for label in self.trainingSet.labels:
                self.AddSortClass(label)

            keysPerBin = {}
            for (label, key) in self.trainingSet.entries:
                keysPerBin[label] = keysPerBin.get(label, []) + [key]

            for bin in self.classBins:
                if bin.label in keysPerBin.keys():
                    bin.AddObjects(keysPerBin[bin.label], self.chMap, priority=2)

            self.PostMessage('Training set loaded.')
            self.GetNumberOfClasses() # Logs number of classes

    def LoadTrainingSetCSV(self, filename):
        '''
        Loads the selected file, parses out object keys, and fetches the tiles for CSV
        '''
        # pause tile loading
        with tilecollection.load_lock():
            self.PostMessage('Loading training set from: %s' % filename)
            # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
            self.defaultTSFileName = os.path.basename(filename)

            self.trainingSet = TrainingSet(p, filename, labels_only=False, csv=True)

            self.RemoveAllSortClasses()
            for label in self.trainingSet.labels:
                self.AddSortClass(label)

            keysPerBin = {}
            for (label, key) in self.trainingSet.entries:
                keysPerBin[label] = keysPerBin.get(label, []) + [key]

            for bin in self.classBins:
                if bin.label in keysPerBin.keys():
                    bin.AddObjects(keysPerBin[bin.label], self.chMap, priority=2)

            self.PostMessage('Training set loaded.')
            self.GetNumberOfClasses() # Logs number of classes


    def OnSaveTrainingSet(self, evt):
        self.SaveTrainingSet()

    def OnSaveFullTrainingSet(self, evt):
        self.SaveFullTrainingSet()

    def SaveTrainingSet(self):
        if not self.defaultTSFileName:
            self.defaultTSFileName = 'MyTrainingSet.txt'
        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(),
                                   defaultFile=self.defaultTSFileName,
                                   wildcard='Text files (*.txt)|*.txt|All files (*.*)|*.*',
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal() == wx.ID_OK:
            filename = saveDialog.GetPath()
            self.defaultTSFileName = os.path.split(filename)[1]
            self.SaveTrainingSetAs(filename)

    def SaveFullTrainingSet(self):
        if not self.defaultTSFileName:
            self.defaultTSFileName = 'MyTrainingSet.csv'
        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(),
                                   defaultFile=self.defaultTSFileName,
                                   wildcard='Text files (*.csv)|*.csv|All files (*.*)|*.*',
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal() == wx.ID_OK:
            filename = saveDialog.GetPath()
            self.defaultTSFileName = os.path.split(filename)[1]
            self.SaveTrainingSetAsCSV(filename)

    def SaveTrainingSetAs(self, filename):
        classDict = {}
        trainingSet = self.trainingSet # Create Save Copy
        try:
            self.trainingSet = TrainingSet(p)
            self.trainingSet.Create([bin.label for bin in self.classBins], [bin.GetObjectKeys() for bin in self.classBins])
        except:
            logging.info("Couldn't update TrainingSet. Using last AutoSave.")
            self.trainingSet = trainingSet # Use backup
        self.trainingSet.Save(filename)

    def SaveTrainingSetAsCSV(self, filename):
        classDict = {}
        trainingSet = self.trainingSet # Create Save Copy
        try:
            self.trainingSet = TrainingSet(p)
            self.trainingSet.Create([bin.label for bin in self.classBins], [bin.GetObjectKeys() for bin in self.classBins])
        except:
            logging.info("Couldn't update TrainingSet. Using last AutoSave.")
            self.trainingSet = trainingSet # Use backup
        self.trainingSet.SaveAsCSV(filename)

    def OnAddSortClass(self, evt):
        label = 'class_' + str(self.binsCreated)
        self.AddSortClass(label)
        if self.RenameClass(label) == wx.ID_CANCEL:
            self.RemoveSortClass(label)

    def OnMapChannels(self, evt):
        ''' Responds to selection from the color mapping menus. '''
        (chIdx, color, item, menu) = self.chMapById[evt.GetId()]
        item.Check()
        self.chMap[chIdx] = color.lower()
        if color.lower() != 'none':
            self.toggleChMap[chIdx] = color.lower()
        self.MapChannels(self.chMap)

    def MapChannels(self, chMap):
        ''' Tell all bins to apply a new channel-color mapping to their tiles. '''
        # TODO: Need to update color menu selections
        self.chMap = chMap
        for bin in self.all_sort_bins():
            bin.MapChannels(chMap)

    def ValidateImageKey(self, evt):
        ''' Checks that the image field specifies an existing image. '''
        txtCtrl = evt.GetEventObject()
        try:
            if p.table_id:
                imKey = (int(self.tableTxt.Value), int(self.imageTxt.Value))
            else:
                imKey = (int(self.imageTxt.Value),)
            if dm.GetObjectCountFromImage(imKey) > 0:
                txtCtrl.SetForegroundColour('#000001')
                self.SetStatusText('Image contains %s %s.' % (dm.GetObjectCountFromImage(imKey), p.object_name[1]))
            else:
                txtCtrl.SetForegroundColour('#888888')  # Set field to GRAY if image contains no objects
                self.SetStatusText('Image contains zero %s.' % (p.object_name[1]))
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')  # Set field to red if image doesn't exist
            self.SetStatusText('No such image.')

    # Nice plotting which depends on which plot one choses
    def OnEvaluation(self, evt):
        items = self.evalMenu.GetMenuItems()
        selectedText = ""
        for item in items:
            if item.IsChecked():
                selectedText = item.GetText()

        if selectedText == "ROC Curve":
            self.PlotROC()
        elif selectedText == "Learning Curve":
            self.PlotLearningCurveWrapper()
        elif selectedText == "Precision Recall Curve":
            self.PlotPrecisionRecall()
        elif selectedText == "Confusion Matrix":
            self.algorithm.ConfusionMatrix()
        else:
            self.algorithm.CheckProgress()

    def PlotLearningCurveWrapper(self):
        from sklearn import cross_validation
        model = self.algorithm
        clf = model.classifier
        X_train = self.trainingSet.values
        y_train = self.trainingSet.label_array

        # Training Set is currently sorted. I will shuffle it
        y_trans = y_train.reshape(y_train.shape[0],1)
        df_values = pd.DataFrame(X_train, columns=self.trainingSet.colnames)
        df_class = pd.DataFrame(y_trans, columns=["Class"])
        df = pd.concat([df_class, df_values],axis=1)
        df = df.reindex(np.random.permutation(df.index))
        X_train = df[self.trainingSet.colnames].values
        y_train = df["Class"].values

        #cv = cross_validation.StratifiedKFold(y_train, n_folds=3, shuffle=False)
        plot_title = 'Learning Curves ({})'.format(model.name)
        self.PlotLearningCurve(clf, plot_title, X_train, y_train, cv=5)

    from utils import delay
    # Add AutoSave by DD
    @delay(360.0) # every 5 min
    def AutoSave(self):
        logging.info("Autosaving ...")
        self.AutoSaveTrainingSet() # Saves only labels
        self.AutoSave()

    # Same as Update Training Set, just without box
    def AutoSaveTrainingSet(self):
        # pause tile loading
        with tilecollection.load_lock():
            try:
                def cb(frac):
                    self.PostMessage('%i % saved',frac * 100.)
                    logging.info("frac %i", frac)

                self.trainingSet = TrainingSet(p)
                try:
                    self.trainingSet.Create(labels=[bin.label for bin in self.classBins],
                                        keyLists=[bin.GetObjectKeys() for bin in self.classBins],
                                        callback=cb, labels_only=True) # Save only labels because its faster
                    self.PostMessage('Autosaving ...')
                except:
                    self.PostMessage('Error: Training set could not be saved.')
                return True
            except StopCalculating:
                self.PostMessage('User canceled saving training set.')
                return False

    def UpdateTrainingSet(self):
        # pause tile loading
        with tilecollection.load_lock():
            try:
                def cb(frac):
                    cont, skip = dlg.Update(int(frac * 100.), 'Saving training set: %d%% complete' % (frac * 100.))
                    if not cont:  # cancel was pressed
                        dlg.Destroy()
                        raise StopCalculating()

                dlg = wx.ProgressDialog('Fetching cell data for training set...', '0% Complete', 100, self,
                                        wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
                self.trainingSet = TrainingSet(p)
                try:
                    self.trainingSet.Create(labels=[bin.label for bin in self.classBins],
                                        keyLists=[bin.GetObjectKeys() for bin in self.classBins],
                                        callback=cb)
                    self.PostMessage('Training set saved.')
                except:
                    self.PostMessage('Error: Training set could not be saved.')
                dlg.Destroy()
                return True
            except StopCalculating:
                self.PostMessage('User canceled updating training set.')
                return False

    def OnTrainClassifier(self, evt):
        if not self.ValidateNumberOfRules():
            errdlg = wx.MessageDialog(self, 'Classifier will not run for the number of rules you have entered.',
                                      "Invalid Number of Rules", wx.OK | wx.ICON_EXCLAMATION)
            errdlg.ShowModal()
            errdlg.Destroy()
            return
        self.TrainClassifier()

#SKLEARN TODO
    def TrainClassifier(self):
        try:
            nRules = int(self.nRulesTxt.GetValue())
        except:
            logging.error('Unable to parse number of rules')
            return

        self.keysAndCounts = None  # Must erase current keysAndCounts so they will be recalculated from new rules

        if not self.UpdateTrainingSet():
            return

        # pause tile loading
        with tilecollection.load_lock():
            try:
                def cb(frac):
                    cont, skip = dlg.Update(int(frac * 100.), '%d%% Complete' % (frac * 100.))
                    if not cont:  # cancel was pressed
                        dlg.Destroy()
                        raise StopCalculating()

                t1 = time()
                output = StringIO()
                dlg = wx.ProgressDialog('Training classifier...', '0% Complete', 100, self,
                                        wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)

                # JK - Start Modification
                # Train the desired algorithm
                # Legacy Code
                if self.algorithm.name == "FastGentleBoosting":
                    self.algorithm.Train(
                        self.trainingSet.colnames, nRules, self.trainingSet.label_matrix,
                        self.trainingSet.values, output, cb
                    )
                else:
                    # Convert labels
                    self.algorithm.Train(self.trainingSet.label_array, self.trainingSet.values, output)
                    self.nRules = nRules # Hack 

                # JK - End Modification

                self.PostMessage('Classifier trained in %.2fs.' % (time() - t1))
                dlg.Destroy()

                self.rules_text.Value = self.algorithm.ShowModel()
                self.scoreAllBtn.Enable()
                self.scoreImageBtn.Enable()

            except StopCalculating:
                self.PostMessage('User canceled training.')
                return

        for bin in self.classBins:
            if not bin.empty:
                bin.trained = True
            else:
                bin.trained = False
        self.UpdateClassChoices()#

    def OnScoreImage(self, evt):
        # Get the image key
        # Start with the table_id if there is one
        tblNum = None
        if p.table_id:
            dlg = wx.TextEntryDialog(self, p.table_id + ':', 'Enter ' + p.table_id)
            dlg.SetValue('0')
            if dlg.ShowModal() == wx.ID_OK:
                tblNum = int(dlg.GetValue())
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
        # Then get the image_id
        dlg = wx.TextEntryDialog(self, p.image_id + ':', 'Enter ' + p.image_id)
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            imgNum = int(dlg.GetValue())
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        # Build the imKey
        if p.table_id:
            imKey = (tblNum, imgNum)
        else:
            imKey = (imgNum,)

        # Score the Image
        classHits = self.ScoreImage(imKey)
        # Get object coordinates in image and display
        classCoords = {}
        for className, obKeys in classHits.items():
            classCoords[className] = [db.GetObjectCoords(key) for key in obKeys]
        # Show the image
        imViewer = imagetools.ShowImage(imKey, list(self.chMap), self,
                                        brightness=self.brightness, scale=self.scale,
                                        contrast=self.contrast)
        imViewer.SetClasses(classCoords)

         # Show table of counts
        nClasses = len(self.classBins)
        title = "Hit table (Image key %s)" % (imKey)
        title += ' (%s)' % (os.path.split(p._filename)[1])
        grid = tableviewer.TableViewer(self, title=title)
        labels = list(dbconnect.image_key_columns())
        # record the column indices for the keys
        # CONSTRUCT ARRAY OF TABLE DATA
        classCounts = []
        tableData = []
        for className, obKeys in classHits.items():
            classCounts.append(len(classCoords[className]))
        tableData += imKey
        tableData += [sum(classCounts)]
        tableData += classCounts
        key_col_indices = [i for i in range(len(labels))]

        labels += ['Total %s Count' % (p.object_name[0].capitalize())]
        for i in xrange(nClasses):
            labels += ['%s %s Count' % (self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        tableData = np.array([tableData])
        grid.table_from_array(tableData, labels, 'Image', key_col_indices)
        grid.Show()

    def ScoreImage(self, imKey):
        '''
        Scores an image, then returns a dictionary of object keys indexed by class name
        eg: ScoreImage(imkey)['positive'] ==> [(6,32), (87,23), (412,65)]
        '''
        try:
            obKeys = dm.GetObjectsFromImage(imKey)
        except:
            self.SetStatusText('No such image: %s' % (imKey,))
            return

        classHits = {}
        if obKeys:
            for clNum, bin in enumerate(self.classBins):
                classHits[bin.label] = self.algorithm.FilterObjectsFromClassN(clNum + 1, [imKey])
                self.PostMessage('%s of %s %s classified as %s in image %s' % (
                len(classHits[bin.label]), len(obKeys), p.object_name[1], bin.label, imKey))

        return classHits

    def ScoreAll(self, evt=None):
        '''
        Calculates object counts for each class and enrichment values,
        then builds a table and displays it in a DataGrid.
        '''
        groupChoices = ['Image'] + p._groups_ordered
        filterChoices = [None] + p._filters_ordered
        nClasses = len(self.classBins)
        two_classes = nClasses == 2
        nKeyCols = len(dbconnect.image_key_columns())

        # GET GROUPING METHOD AND FILTER FROM USER
        dlg = ScoreDialog(self, groupChoices, filterChoices)
        if dlg.ShowModal() == wx.ID_OK:
            group = dlg.group
            filter = dlg.filter
            wants_enrichments = dlg.wants_enrichments
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        t1 = time()

        # FETCH PER-IMAGE COUNTS FROM DB
        if not self.keysAndCounts or filter != self.lastScoringFilter:
            # If hit counts havn't been calculated since last training or if the
            # user is filtering the data differently then classify all objects
            # into phenotype classes and count phenotype-hits per-image.
            self.lastScoringFilter = filter

            if p.class_table:
                overwrite_class_table = True
                # If p.class_table is already in the db, we need to confirm whether or not to overwrite it.
                if db.table_exists(p.class_table):
                    dlg = wx.MessageDialog(self,
                                           'The database table "%s" already exists. Overwrite '
                                           'this table with new per-object class data?' % (p.class_table),
                                           'Overwrite %s?' % (p.class_table),
                                           wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    if response == wx.ID_YES:
                        pass
                    else:
                        overwrite_class_table = False

            dlg = wx.ProgressDialog('Calculating %s counts for each class...' % (p.object_name[0]), '0% Complete', 100,
                                    self,
                                    wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)

            def update(frac):
                cont, skip = dlg.Update(int(frac * 100.), '%d%% Complete' % (frac * 100.))
                if not cont:  # cancel was pressed
                    raise StopCalculating()

            try:
                # Adapter Pattern to switch between Legacy code and SciKit Learn
                if self.algorithm.name == "FastGentleBoosting":
                    self.keysAndCounts = self.algorithm.PerImageCounts(filter_name=filter, cb=update)
                else:
                    number_of_classes = self.GetNumberOfClasses()
                    self.keysAndCounts = self.algorithm.PerImageCounts(number_of_classes, filter, update)
            except StopCalculating:
                dlg.Destroy()
                self.SetStatusText('Scoring canceled.')
                return

            dlg.Destroy()

            # Make sure PerImageCounts returned something
            if not self.keysAndCounts:
                errdlg = wx.MessageDialog(self,
                                          'No images are in filter "%s". Please check the filter definition in your properties file.' % (
                                          filter), "Empty Filter", wx.OK | wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                errdlg.Destroy()
                return
#SKLEARN TODO
            if p.class_table and overwrite_class_table:
                self.PostMessage('Saving %s classes to database...' % (p.object_name[0]))
                self.algorithm.CreatePerObjectClassTable([bin.label for bin in self.classBins])
                self.PostMessage('%s classes saved to table "%s"' % (p.object_name[0].capitalize(), p.class_table))

        t2 = time()
        self.PostMessage('time to calculate hits: %.3fs' % (t2 - t1))

        # AGGREGATE PER_IMAGE COUNTS TO GROUPS IF NOT GROUPING BY IMAGE
        if group != groupChoices[0]:
            self.PostMessage('Grouping %s counts by %s...' % (p.object_name[0], group))
            imData = {}
            for row in self.keysAndCounts:
                key = tuple(row[:nKeyCols])
                imData[key] = np.array([float(v) for v in row[nKeyCols:]])
            groupedKeysAndCounts = np.array([list(k) + vals.tolist() for k, vals
                                             in dm.SumToGroup(imData, group).items()], dtype=object)
            nKeyCols = len(dm.GetGroupColumnNames(group))
        else:
            groupedKeysAndCounts = np.array(self.keysAndCounts, dtype=object)
            if p.plate_id and p.well_id:
                pw = db.GetPlatesAndWellsPerImage()
                platesAndWells = {}
                for row in pw:
                    platesAndWells[tuple(row[:nKeyCols])] = list(row[nKeyCols:])

        t3 = time()
        self.PostMessage('time to group per-image counts: %.3fs' % (t3 - t2))

        # FIT THE BETA BINOMIAL
        if wants_enrichments:
            self.PostMessage('Fitting beta binomial distribution to data...')
            counts = groupedKeysAndCounts[:, -nClasses:]
            alpha, converged = polyafit.fit_betabinom_minka_alternating(counts)
            logging.info('   alpha = %s   converged = %s' % (alpha, converged))
            logging.info('   alpha/Sum(alpha) = %s' % ([a / sum(alpha) for a in alpha]))
            t4 = time()
            logging.info('time to fit beta binomial: %.3fs' % (t4 - t3))
            self.PostMessage('Computing enrichment scores for each group...')

        # CONSTRUCT ARRAY OF TABLE DATA
        tableData = []
        fraction = 0.0
        for i, row in enumerate(groupedKeysAndCounts):
            # Start this row with the group key:
            tableRow = list(row[:nKeyCols])
            if group != 'Image':
                # Append the # of images in this group
                tableRow += [len(dm.GetImagesInGroup(group, tuple(row[:nKeyCols]), filter))]
            else:
                # Append the plate and well ids
                if p.plate_id and p.well_id:
                    tableRow += platesAndWells[tuple(row[:nKeyCols])]
            # Append the counts:
            countsRow = [int(v) for v in row[nKeyCols:nKeyCols + nClasses]]
            tableRow += [sum(countsRow)]
            tableRow += countsRow
            if p.area_scoring_column is not None:
                # Append the areas
                countsRow = [int(v) for v in row[-nClasses:]]
                tableRow += [sum(countsRow)]
                tableRow += countsRow

            if wants_enrichments:
                # Only calculate enrichment scores if the beta binomial distribution has been fitted properly
                if not np.isnan(alpha).any():
                    # Append the scores:
                    #   compute enrichment probabilities of each class for this image OR group
                    scores = np.array(dirichletintegrate.score(alpha, np.array(countsRow)))
                    #   clamp to [0,1] to
                    scores[scores > 1.] = 1.
                    scores[scores < 0.] = 0.
                    tableRow += scores.tolist()
                    # Append the logit scores:
                    # Special case: only calculate logit of "positives" for 2-classes
                    if two_classes:
                        tableRow += [
                            np.log10(scores[0]) - (np.log10(1 - scores[0]))]  # compute logit of each probability
                    else:
                        tableRow += [np.log10(score) - (np.log10(1 - score)) for score in
                                     scores]  # compute logit of each probability
                else:
                    tableRow += ['NaN'] * 2 * len(countsRow)
            tableData.append(tableRow)
        tableData = np.array(tableData, dtype=object)

        if wants_enrichments:
            t5 = time()
            self.PostMessage('time to compute enrichment scores: %.3fs' % (t5 - t4))

        # CREATE COLUMN LABELS LIST
        # if grouping isn't per-image, then get the group key column names.
        if group != groupChoices[0]:
            labels = dm.GetGroupColumnNames(group)
        else:
            labels = list(dbconnect.image_key_columns())
        # record the column indices for the keys
        key_col_indices = [i for i in range(len(labels))]
        if group != 'Image':
            labels += ['Images']
        else:
            if p.plate_id and p.well_id:
                #                labels += [p.plate_id]
                labels += ['Plate ID']
                labels += [p.well_id]
        labels += ['Total %s Count' % (p.object_name[0].capitalize())]
        for i in xrange(nClasses):
            labels += ['%s %s Count' % (self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        if p.area_scoring_column is not None:
            labels += ['Total %s Area' % (p.object_name[0].capitalize())]
            for i in xrange(nClasses):
                labels += ['%s %s Area' % (self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        if wants_enrichments:
            for i in xrange(nClasses):
                labels += ['p(Enriched)\n' + self.classBins[i].label]
            if two_classes:
                labels += ['Enriched Score\n' + self.classBins[0].label]
            else:
                for i in xrange(nClasses):
                    labels += ['Enriched Score\n' + self.classBins[i].label]

        title = "Hit table (grouped by %s)" % (group,)
        if filter:
            title += " filtered by %s" % (filter,)
        title += ' (%s)' % (os.path.split(p._filename)[1])
        grid = tableviewer.TableViewer(self, title=title)
        grid.table_from_array(tableData, labels, group, key_col_indices)
        grid.Show()

        self.openDimensReduxBtn.Enable()  # JEN - Added

        self.SetStatusText('')

    # JK - Start Add
    def ShowConfusionMatrix(self, confusionMatrix, axes):
        # Calculate the misclassification rate
        nObjects = confusionMatrix.sum()
        misRate = float(nObjects - np.diag(confusionMatrix).sum()) * 100 / nObjects

        # Build the graphical representation of the matrix
        title = 'Confusion Matrix (Classification Accuracy: %3.2f%%)' % (100 - misRate)
        grid = tableviewer.TableViewer(self, title=title)
        grid.table_from_array(confusionMatrix, axes)

        # We don't want clicks on the header to sort the table, so we remove the event listener
        grid.grid.Unbind(wx.grid.EVT_GRID_CMD_LABEL_LEFT_CLICK)

        # We also want to have the classes on the row labels
        grid.grid.Table.row_labels = axes
        grid.grid.SetRowLabelSize(grid.grid.GetRowLabelSize() + 25)

        # Show the confusion matrix
        grid.Show()

    # JK - End Add

    def OnSelectFilter(self, evt):
        ''' Handler for fetch filter selection. '''
        filter = self.filterChoice.GetStringSelection()
        # Select from a specific image
        if filter == 'experiment' or filter in p._filters_ordered:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
        elif filter == 'image' or filter in p._groups_ordered:
            self.SetupFetchFromGroupSizer(filter)
            self.fetchSizer.Show(self.fetchFromGroupSizer, True)
        elif filter == CREATE_NEW_FILTER:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
            from columnfilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(600, 150))
            if cff.ShowModal() == wx.OK:
                fltr = cff.get_filter()
                fname = cff.get_filter_name()
                p._filters[fname] = fltr
                items = self.filterChoice.GetItems()
                self.filterChoice.SetItems(items[:-1] + [fname] + items[-1:])
                self.filterChoice.Select(len(items) - 1)
            else:
                self.filterChoice.Select(0)
            cff.Destroy()
        self.fetch_panel.Layout()
        self.fetch_panel.Refresh()

    def SetupFetchFromGroupSizer(self, group):
        '''
        This sizer displays input fields for inputting each element of a
        particular group's key. A group with 2 columns: Gene, and Well,
        would be represented by two combo boxes.
        '''
        if group == 'image':
            fieldNames = ['table', 'image'] if p.table_id else ['image']
            fieldTypes = [int, int]
            validKeys = dm.GetAllImageKeys()
        else:
            fieldNames = dm.GetGroupColumnNames(group)
            fieldTypes = dm.GetGroupColumnTypes(group)
            validKeys = dm.GetGroupKeysInGroup(group)

        self.groupInputs = []
        self.groupFieldValidators = []
        self.fetchFromGroupSizer.Clear(True)
        for i, field in enumerate(fieldNames):
            label = wx.StaticText(self.fetch_panel, wx.NewId(), field + ':')
            # Values to be sorted BEFORE being converted to str
            validVals = list(set([col[i] for col in validKeys]))
            validVals.sort()
            validVals = [str(col) for col in validVals]
            if group == 'image' or fieldTypes[i] == int or fieldTypes[i] == long:
                fieldInp = wx.TextCtrl(self.fetch_panel, -1, value=validVals[0], size=(80, -1))
            else:
                fieldInp = wx.ComboBox(self.fetch_panel, -1, value=validVals[0], size=(80, -1),
                                       choices=['__ANY__'] + validVals)
            validVals = ['__ANY__'] + validVals
            # Create and bind to a text Validator
            def ValidateGroupField(evt, validVals=validVals):
                ctrl = evt.GetEventObject()
                if ctrl.GetValue() in validVals:
                    ctrl.SetForegroundColour('#000001')
                else:
                    ctrl.SetForegroundColour('#FF0000')

            self.groupFieldValidators += [ValidateGroupField]
            fieldInp.Bind(wx.EVT_TEXT, self.groupFieldValidators[-1])
            self.groupInputs += [fieldInp]
            self.fetchFromGroupSizer.Add(label)
            self.fetchFromGroupSizer.Add(fieldInp)
            self.fetchFromGroupSizer.AddSpacer((10, 20))

    def ValidateIntegerField(self, evt):
        ''' Validates an integer-only TextCtrl '''
        txtCtrl = evt.GetEventObject()
        # NOTE: textCtrl.SetBackgroundColor doesn't work on Mac
        #   and foreground color only works when not setting to black.
        try:
            int(txtCtrl.GetValue())
            txtCtrl.SetForegroundColour('#000001')
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')

    def ValidateNumberOfRules(self, evt=None):
        # NOTE: textCtrl.SetBackgroundColor doesn't work on Mac
        #   and foreground color only works when not setting to black.
        try:
            nRules = int(self.nRulesTxt.GetValue())
            if p.db_type == 'sqlite':
                nClasses = len(self.classBins)
                maxRules = 99
                if nRules > maxRules:
                    self.nRulesTxt.SetToolTip(wx.ToolTip(str(maxRules)))
                    self.nRulesTxt.SetForegroundColour('#FF0000')
                    logging.warn(
                        'No more than 99 rules can be used with SQLite. To avoid this limitation, use MySQL.' % (
                        nClasses, maxRules))
                    return False
            self.nRulesTxt.SetForegroundColour('#000001')
            return True
        except(Exception):
            self.nRulesTxt.SetForegroundColour('#FF0000')
            return False

    def GetGroupKeyFromGroupSizer(self, group=None):
        ''' Returns the text in the group text inputs as a group key. '''
        if group is not None:
            fieldTypes = dm.GetGroupColumnTypes(group)
        else:
            fieldTypes = [int for input in self.groupInputs]
        groupKey = []
        for input, ftype in zip(self.groupInputs, fieldTypes):
            # GetValue returns unicode from ComboBox, but we need a string
            val = str(input.GetValue())
            # if the value is blank, don't bother typing it, it is a wildcard
            if val != '__ANY__':
                val = ftype(val)
            groupKey += [val]
        return tuple(groupKey)

    def OnShowImageControls(self, evt):
        ''' Shows the image adjustment control panel in a new frame. '''
        self.imageControlFrame = wx.Frame(self)
        ImageControlPanel(self.imageControlFrame, self, brightness=self.brightness, scale=self.scale,
                          contrast=self.contrast)
        self.imageControlFrame.Show(True)

#SKLEARN TODO
    def OnRulesEdit(self, evt):
        '''Lets the user edit the rules.'''
        if self.algorithm.name == "FastGentleBoosting":
            dlg = wx.TextEntryDialog(self, 'Rules:', 'Edit rules',
                                     style=wx.TE_MULTILINE | wx.OK | wx.CANCEL)
            dlg.SetValue(self.rules_text.Value)
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    modelRules = self.algorithm.ParseModel(dlg.GetValue())
                    if len(modelRules[0][2]) != len(self.classBins):
                        wx.MessageDialog(self, 'The rules you entered specify %s '
                                               'classes but %s bins exist in classifier. Please adjust'
                                               ' your rules or the number of bins so that they agree.' %
                                         (len(modelRules[0][2]), len(self.classBins)),
                                         'Rules Error', style=wx.OK).ShowModal()
                        self.OnRulesEdit(evt)
                        return
                except ValueError, e:
                    wx.MessageDialog(self, 'Unable to parse your edited rules:\n\n' + str(e), 'Parse error',
                                     style=wx.OK).ShowModal()
                    self.OnRulesEdit(evt)
                    return
                self.keysAndCounts = None
                self.rules_text.Value = self.algorithm.ShowModel()
                self.scoreAllBtn.Enable(True if self.algorithm.IsTrained() else False)
                self.scoreImageBtn.Enable(True if self.algorithm.IsTrained() else False)
                for bin in self.classBins:
                    bin.trained = True
                self.UpdateClassChoices()
        else:
            dlg = wx.MessageDialog(self,'Selected algorithm does not provide this feature', 'Unavailable', style=wx.OK)
            response = dlg.ShowModal()

    def OnParamsEdit(self, evt):
        '''Lets the user edit the hyperparameters.'''
        if self.algorithm.name != "FastGentleBoosting":
            dlg = wx.TextEntryDialog(self, 'Hyperparameters:', 'Edit hyperparameters',
                                     style=wx.TE_MULTILINE | wx.OK | wx.CANCEL)
            dlg.SetSize((500,500))
            #import json
            #dlg.SetValue(json.dumps(self.algorithm.get_params(), sort_keys=True,indent=4, separators=(',', ': ')))

            params = self.algorithm.get_params()
            types = {}
            # Transform to list
            string = ""
            for key in params:
                string +=  key +  " : " + str(params[key]) + "\n"
                types[key] = type(params[key]) # remember the types of each key

            dlg.SetValue(string)
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    s = dlg.GetValue() 
                    s = s.split("\n")[:-1] # Get rid of the last element
                    for el in s:
                        el = el.split(" : ")
                        if types[el[0]] == type(""):
                            el = "{\'" + el[0] + "\':" + "\'" + el[1] + "\'" + "}" # add some ''
                        else:
                            el = "{\'" + el[0] + "\':" + el[1] + "}" # add '' for strings

                        logging.info("Setting params to: " + el)
                        self.algorithm.set_params(eval(el)) # now evaluate

                except ValueError, e:
                    wx.MessageDialog(self, 'Unable to parse your edited hyperparameters:\n\n' + str(e), 'Parse error',
                                     style=wx.OK).ShowModal()
                    self.OnParamsEdit(evt)
                    return
                self.keysAndCounts = None
                self.rules_text.Value = self.algorithm.ShowModel()
                self.scoreAllBtn.Enable(True if self.algorithm.IsTrained() else False)
                self.scoreImageBtn.Enable(True if self.algorithm.IsTrained() else False)
                for bin in self.classBins:
                    bin.trained = True
                self.UpdateClassChoices()
        else:
            dlg = wx.MessageDialog(self,'Selected algorithm does not provide this feature', 'Unavailable', style=wx.OK)
            response = dlg.ShowModal()

    '''
    Performs Variance Thresholding on the Test Data
    '''
    def OnFeatureSelect(self, evt):
        from sklearn import feature_selection

        if self.trainingSet:


            selector = feature_selection.VarianceThreshold()
            selector.fit(self.trainingSet.values)

            colnames = self.trainingSet.colnames
            variances = selector.variances_
            indices = np.argsort(variances)
            variances = np.sort(variances)
            result = ""
            for i,var in enumerate(variances):
                result += colnames[indices[i]] + " , " + str(var) + "\n"
            
            
            dlg = wx.TextEntryDialog(self, 'Lowest Feature Variance:', 'Features ordered by lowest variance',
                                     style=wx.TE_MULTILINE | wx.OK )
            dlg.SetSize((500,500))
            dlg.SetValue(result)
            dlg.ShowModal()

        else:
            dlg = wx.MessageDialog(self,'Please load your training data first', 'No data available', style=wx.OK)
            dlg.ShowModal()


    def SetBrightness(self, brightness):
        ''' Updates the global image brightness across all tiles. '''
        self.brightness = brightness
        [t.SetBrightness(brightness) for bin in self.all_sort_bins() for t in bin.tiles]

    def SetScale(self, scale):
        ''' Updates the global image scaling across all tiles. '''
        self.scale = scale
        [t.SetScale(scale) for bin in self.all_sort_bins() for t in bin.tiles]
        [bin.UpdateSizer() for bin in self.all_sort_bins()]

    def SetContrastMode(self, mode):
        self.contrast = mode
        [t.SetContrastMode(mode) for bin in self.all_sort_bins() for t in bin.tiles]

    def PostMessage(self, message):
        ''' Updates the status bar text and logs to info. '''
        self.SetStatusText(message)
        logging.info(message)

    def OnClose(self, evt):
        ''' Prompt to save training set before closing. '''
        if self.trainingSet and self.trainingSet.saved == False:
            dlg = wx.MessageDialog(self, 'Do you want to save your training set before quitting?',
                                   'Training Set Not Saved', wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.SaveTrainingSet()
            elif response == wx.ID_CANCEL:
                try:
                    evt.Veto()
                except:
                    pass
                return
        self.Destroy()

    def IsTrained(self):
        return self.algorithm.IsTrained() is not None

    def Destroy(self):
        ''' Kill off all threads before combusting. '''
        super(Classifier, self).Destroy()
        import threading
        for thread in threading.enumerate():
            if thread != threading.currentThread() and thread.getName().lower().startswith('tileloader'):
                logging.debug('Aborting thread %s' % thread.getName())
                try:
                    thread.abort()
                except:
                    pass
        # XXX: Hack -- can't figure out what is holding onto TileCollection, but
        #      it needs to be trashed if Classifier is to be reopened since it
        #      will otherwise grab the existing instance with a dead tileLoader
        tilecollection.TileCollection._forgetClassInstanceReferenceForTesting()

    # Get number of labels/classes we have in our training set
    def GetNumberOfClasses(self):
        number_of_classes = len(self.trainingSet.labels)
        # logging.info("We have " + str(number_of_classes) + " Classes")
        return number_of_classes

    # Buggy?
    def PlotPrecisionRecall(self):
        from sklearn.metrics import precision_recall_curve
        from sklearn.metrics import average_precision_score
        from sklearn.cross_validation import train_test_split
        from sklearn.preprocessing import label_binarize
        from sklearn.multiclass import OneVsRestClassifier

        # Import some data to play with
        X = self.trainingSet.normalize()
        y = self.trainingSet.get_class_per_object()
        n_classes = self.GetNumberOfClasses()

        # Binarize the output
        y = label_binarize(y, classes=self.trainingSet.labels)

        # Split into training and test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.4)

        # Run classifier
        clf = OneVsRestClassifier(self.algorithm.classifier)
        clf.fit(X_train, y_train)
        if hasattr(self.algorithm.classifier, "predict_proba"):
            y_score = clf.predict_proba(X_test)        
        else: # use decision function
            y_score = clf.decision_function(X_test)

        # Compute Precision-Recall and plot curve
        precision = dict()
        recall = dict()
        average_precision = dict()
        for i in range(n_classes):
            precision[i], recall[i], _ = precision_recall_curve(y_test[:, i],
                                                                y_score[:, i])
            average_precision[i] = average_precision_score(y_test[:, i], y_score[:, i])

        # Compute micro-average precision curve and precision area
        precision["micro"], recall["micro"], _ = precision_recall_curve(y_test.ravel(),
            y_score.ravel())
        average_precision["micro"] = average_precision_score(y_test, y_score,
                                                             average="micro")

        # Plot Precision-Recall curve
        plt.clf()
        plt.plot(recall[0], precision[0], label='Precision-Recall curve')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.ylim([0.0, 1.05])
        plt.xlim([0.0, 1.0])
        plt.title('Precision-Recall: Average Precision={0:0.2f}'.format(average_precision[0]))
        plt.legend(loc="lower left")
        plt.show()

        # Plot Precision-Recall curve for each class
        plt.clf()
        plt.plot(recall["micro"], precision["micro"],
                 label='micro-average Precision-recall curve (area = {0:0.2f})'
                       ''.format(average_precision["micro"]))
        for i in range(n_classes):
            plt.plot(recall[i], precision[i],
                     label='Precision-recall curve of class {0} (area = {1:0.2f})'
                           ''.format(i, average_precision[i]))

        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Receiver operating characteristic of multi-class {}. 60/40 Split'.format(self.algorithm.name))
        plt.legend(loc="lower right")
        plt.show()

    # ROC Curve for multi class # TODO: Binary class ROC Curve
    def PlotROC(self):
        from matplotlib import offsetbox
        from sklearn.metrics import roc_curve, auc
        from sklearn.cross_validation import train_test_split
        from sklearn.preprocessing import label_binarize
        from sklearn.multiclass import OneVsRestClassifier

        # Import some data to play with
        X = self.trainingSet.normalize()
        y = self.trainingSet.get_class_per_object()
        n_classes = self.GetNumberOfClasses()

        # Binarize the output
        y = label_binarize(y, classes=self.trainingSet.labels)

        # shuffle and split training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.4,
                                                            random_state=0)

        # Learn to predict each class against the other
        clf = OneVsRestClassifier(self.algorithm.classifier)
        clf.fit(X_train, y_train)
        if hasattr(self.algorithm.classifier, "predict_proba"):
            y_score = clf.predict_proba(X_test)        
        else: # use decision function
            y_score = clf.decision_function(X_test)

        # Compute ROC curve and ROC area for each class
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i in range(n_classes):
            fpr[i], tpr[i], _ = roc_curve(y_test[:, i], y_score[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])

        # Compute micro-average ROC curve and ROC area
        if n_classes > 1:
            fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), y_score.ravel())
            roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

        # Plot ROC curve
        plt.figure()
        if n_classes > 1:
            plt.plot(fpr["micro"], tpr["micro"],
                     label='micro-average ROC curve (area = {0:0.2f})'
                           ''.format(roc_auc["micro"]))
        for i in range(n_classes):
            plt.plot(fpr[i], tpr[i], label='ROC curve of {0} (area = {1:0.2f})'
                                           ''.format(self.trainingSet.labels[i], roc_auc[i]))

        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic of multi-class {}. 60/40 Split'.format(self.algorithm.name))
        plt.legend(loc="lower right")
        plt.show()

    def PlotProbs(self,values):
        labels = self.trainingSet.labels
        fig = plt.figure()
        ax = fig.add_subplot(111)

        tmp_df = pd.DataFrame(labels,columns=["Class"])
        df = pd.DataFrame(values,columns=["Probs"])
        df = pd.concat([df,tmp_df],axis=1)
        df = df.sort_values("Probs",ascending=False)
        # print df
        sns.set(style="whitegrid")
        if(len(df) > 7):
            sns.barplot(x="Probs", y="Class", data=df, palette="RdBu_r",ax=ax)
        else:
            sns.barplot(y="Probs", x="Class", data=df, palette="RdBu_r",ax=ax)    
        
        plt.show()

    def PlotLearningCurve(self,estimator, plot_title, X, y, ylim=None, cv=None,
                        n_jobs=1, train_sizes=np.linspace(0.1, 1.0, 5),
                        scoring=None):
        """
        Generate a simple plot of the test and training learning curve.

        Parameters
        ----------
        estimator : object type that implements the "fit" and "predict" methods
            An object of that type which is cloned for each validation.

        title : string
            Title for the chart.

        X : array-like, shape (n_samples, n_features)
            Training vector, where n_samples is the number of samples and
            n_features is the number of features.

        y : array-like, shape (n_samples) or (n_samples, n_features), optional
            Target relative to X for classification or regression;
            null for unsupervised learning.

        ylim : tuple, shape (ymin, ymax), optional
            Defines minimum and maximum yvalues plotted.

        cv : integer, cross-validation generator, optional
            If an integer is passed, it is the number of folds (defaults to 3).
            Specific cross-validation objects can be passed, see
            sklearn.cross_validation module for the list of possible objects

        n_jobs : integer, optional
            Number of jobs to run in parallel (default 1).
        """    
        from sklearn.learning_curve import learning_curve
        
        plt.figure()
        plt.title(plot_title)
        if ylim is not None:
            plt.ylim(*ylim)
        plt.xlabel("Training examples")
        plt.ylabel("Cost = 1 - Score")
        train_sizes, train_scores, test_scores = learning_curve(estimator, X, y,
                                                                cv=cv, n_jobs=n_jobs,
                                                                train_sizes=train_sizes,
                                                                scoring=scoring)
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std = np.std(train_scores, axis=1)
        test_scores_mean = np.mean(test_scores, axis=1)
        test_scores_std = np.std(test_scores, axis=1)
        plt.grid()

        plt.fill_between(train_sizes, 1 - train_scores_mean + train_scores_std,
                         1 - train_scores_mean - train_scores_std, alpha=0.1,
                         color="b")
        plt.fill_between(train_sizes, 1 - test_scores_mean + test_scores_std,
                         1 - test_scores_mean - test_scores_std, alpha=0.1, color="r")
        plt.plot(train_sizes, 1 - train_scores_mean, 'o-', color="b",
                 label="Training score")
        plt.plot(train_sizes, 1 - test_scores_mean, 'o-', color="r",
                 label="Test score")

        plt.legend(loc="best")
        plt.show()
        

class StopCalculating(Exception):
    pass


# ----------------- Run -------------------

if __name__ == "__main__":
    import sys
    import logging
    from errors import show_exception_as_dialog

    logging.basicConfig(level=logging.DEBUG, )

    global defaultDir
    defaultDir = os.getcwd()

    # Handles args to MacOS "Apps"
    if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
        del sys.argv[1]

    # Initialize the app early because the fancy exception handler
    # depends on it in order to show a dialog.
    app = wx.App()

    # Install our own pretty exception handler unless one has already
    # been installed (e.g., a debugger)
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = show_exception_as_dialog

    p = Properties.getInstance()
    db = dbconnect.DBConnect.getInstance()
    dm = DataModel.getInstance()

    # Load a properties file if passed as the first argument
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            logging.error('Classifier requires a properties file.  Exiting.')
            wx.GetApp().Exit()

    classifier = Classifier()
    classifier.Show(True)

    # Load a training set if passed as the second argument
    if len(sys.argv) > 2:
        training_set_filename = sys.argv[2]
        classifier.LoadTrainingSet(training_set_filename)

    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import javabridge

        javabridge.kill_vm()
    except:
        import traceback

        traceback.print_exc()
        print "Caught exception while killing VM"
