# Encoding: utf-8

import matplotlib

from cpa.guiutils import create_status_bar

matplotlib.use('WXAgg')

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from . import tableviewer
from .datamodel import DataModel
from .imagecontrolpanel import ImageControlPanel
from .properties import Properties
from .scoredialog import ScoreDialog
from . import tilecollection
from .trainingset import TrainingSet
from io import StringIO
from time import time
from . import icons
from . import dbconnect
from . import dirichletintegrate
from . import imagetools
from . import polyafit
from . import sortbin
import logging
import numpy as np
import os
import sys
import wx
import re
import random
import cpa.helpmenu

from . import fastgentleboostingmulticlass
from .fastgentleboosting import FastGentleBoosting

from .generalclassifier import GeneralClassifier

from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import roc_curve, auc


# number of cells to classify before prompting the user for whether to continue
MAX_ATTEMPTS = 10000

ID_CLASSIFIER = wx.NewIdRef()
CREATE_NEW_FILTER = '*create new filter*'

class Classifier(wx.Frame):
    """
    GUI Interface and functionality for the Classifier.
    """

    def __init__(self, properties=None, parent=None, id=ID_CLASSIFIER, **kwargs):

        if properties is not None:
            global p
            p = properties
            global db
            db = dbconnect.DBConnect()

        wx.Frame.__init__(self, parent, id=id, title='CPA/Classifier - %s' % \
                                                     (os.path.basename(p._filename)), size=(900, 600), **kwargs)
        if parent is None and not sys.platform.startswith('win'):
            from wx.adv import TaskBarIcon
            self.tbicon = TaskBarIcon()
            self.tbicon.SetIcon(icons.get_cpa_icon(), 'CPA/Classifier')
        else:
            self.SetIcon(icons.get_cpa_icon())
        self.SetName('Classifier')

        db.register_gui_parent(self)

        global dm
        dm = DataModel()

        if not p.is_initialized():
            logging.critical('Classifier requires a properties file. Exiting.')
            raise Exception('Classifier requires a properties file. Exiting.')

        self.pmb = None
        self.worker = None
        self.trainingSet = None
        self.training_set_ready = False
        self.classBins = []
        self.binsCreated = 0
        self.kFolds = 5
        self.chMap = p.image_channel_colors[:]
        self.toggleChMap = p.image_channel_colors[
                           :]  # used to store previous color mappings when toggling colors on/off with ctrl+1,2,3...
        self.brightness = 1.0
        self.required_fields = []
        self.with_replacement = False
        self.reject_duplicates = False

        # if not p.classification_type == 'image':
        self.image_tile_size = p.image_tile_size
        self.scale = 1.0
        # else:
        #     if p.field_defined('image_width') and p.field_defined('image_height'):
        #         self.image_tile_size = min([p.image_width, p.image_height])
        #     else:
        #         cols = [x for x in db.GetColumnNames(p.image_table)]
        #         list_of_cols = [str(x) for x in cols]
        #         image_width, image_height = db.GetImageWidthHeight(list_of_cols)
        #         self.image_tile_size = min([image_width, image_height])
        #     self.scale = 100.0/float(self.image_tile_size)

        self.required_fields = ['object_table', 'object_id', 'cell_x_loc', 'cell_y_loc']        
        
        for field in self.required_fields:
            if not p.field_defined(field):
                errdlg = wx.MessageDialog(self, 'Properties field "%s" is required for Classifier.'% (field),
                                       'Error', wx.OK| wx.ICON_ERROR)
                errdlg.ShowModal()
                errdlg.Destroy()
                logging.error('Properties field "%s" is required for Classifier.'% (field))
                self.Destroy()
                return 

        self.contrast = 'Linear'
        self.defaultTSFileName = None
        self.defaultModelFileName = None
        self.lastScoringFilter = None

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateMenus()

        self.status_bar = create_status_bar(self, force=True)
        #### Create GUI elements
        # Top level - three split windows
        self.splitter = wx.SplitterWindow(self, style=wx.NO_BORDER | wx.SP_3DSASH | wx.SP_LIVE_UPDATE)

        self.fetch_and_rules_panel = wx.Panel(self.splitter)
        self.bins_splitter = wx.SplitterWindow(self.splitter, style=wx.NO_BORDER | wx.SP_3DSASH | wx.SP_LIVE_UPDATE)

        # fetch & rules
        self.fetch_panel = wx.Panel(self.fetch_and_rules_panel)
        self.rules_text = wx.TextCtrl(self.fetch_and_rules_panel, -1, size=(-1, -1),
                                      style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.rules_text.SetMinSize((-1, 40))
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
        self.obClassChoice = wx.Choice(self.fetch_panel, id=-1, choices=['random', 'sequential'])
        self.filterChoice = wx.Choice(self.fetch_panel, id=-1,
                                      choices=['experiment', 'image'] + p._filters_ordered + p.gates_ordered +
                                              p._groups_ordered + [CREATE_NEW_FILTER])
        self.fetchFromGroupSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetchBtn = wx.Button(self.fetch_panel, -1, 'Fetch!')

        # find rules interface/set neurons interface
        self.nRulesTxt = wx.TextCtrl(self.find_rules_panel, -1, value='5', size=(30, -1))
        self.nNeuronsTxt = wx.TextCtrl(self.find_rules_panel, -1, value='12,12', size=(50, -1))
        algorithmChoices = ['RandomForest Classifier',
                            'AdaBoost Classifier',
                            'SVC',
                            'GradientBoosting Classifier',
                            'LogisticRegression',
                            'LDA',
                            'KNeighbors Classifier',
                            'Fast Gentle Boosting',
                            'Neural Network']

        self.classifierChoice = wx.Choice(self.find_rules_panel, id=-1, choices=algorithmChoices) # Classifier Choice
        self.classifierChoice.SetSelection(0) # Windows GUI otherwise doesn't select
        self.trainClassifierBtn = wx.Button(self.find_rules_panel, -1, 'Train')
        self.scoreAllBtn = wx.Button(self.find_rules_panel, -1, 'Score All')
        self.scoreImageBtn = wx.Button(self.find_rules_panel, -1, 'Score Image')

        # add sorting class
        self.addSortClassBtn = wx.Button(self.status_bar, -1, "Add new class", style=wx.BU_EXACTFIT)

        #### Create Sizers
        self.fetchSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.find_rules_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetch_and_rules_sizer = wx.BoxSizer(wx.VERTICAL)
        self.classified_bins_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #### Add elements to sizers and splitters
        # fetch panel
        self.fetchSizer.AddStretchSpacer()
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'Fetch'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(5)
        self.fetchSizer.Add(self.nObjectsTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(5)
        self.fetchSizer.Add(self.obClassChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(5)
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, p.object_name[1]), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(5)
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'from'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(5)
        self.fetchSizer.Add(self.filterChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(10)
        self.fetchSizer.Add(self.fetchFromGroupSizer, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer(5)
        self.fetchSizer.Add(self.fetchBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddStretchSpacer()
        self.fetch_panel.SetSizerAndFit(self.fetchSizer)

        # Train classifier panel
        self.find_rules_sizer.AddStretchSpacer()
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(wx.StaticText(self.find_rules_panel, -1, 'Use'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.Add(self.classifierChoice, flag=wx.ALIGN_CENTER_VERTICAL) #Classifier Choice
        self.find_rules_sizer.Add((5, 20))
        self.find_rules_sizer.AddSpacer(5)
        self.panelTxt = wx.StaticText(self.find_rules_panel, -1, 'display')
        self.find_rules_sizer.Add(self.panelTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.AddSpacer(5)
        self.panelTxt2 = wx.StaticText(self.find_rules_panel, -1, '')
        self.find_rules_sizer.Add(self.nRulesTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.Add(self.nNeuronsTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.nNeuronsTxt.Hide()
        self.find_rules_sizer.AddSpacer(5)
        self.find_rules_sizer.Add(self.panelTxt2, flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.AddSpacer(5)
        # Cross Validation Button
        self.find_rules_sizer.AddSpacer(5)
        self.find_rules_sizer.Add(self.trainClassifierBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.AddSpacer(5)
        self.evaluationBtn = wx.Button(self.find_rules_panel, -1, 'Evaluate')
        self.evaluationBtn.Disable()
        self.find_rules_sizer.AddSpacer(5)
        self.find_rules_sizer.Add(self.evaluationBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        # Plot nice graphics Button
        self.find_rules_sizer.AddSpacer(5)
        self.find_rules_sizer.Add(self.scoreAllBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.AddSpacer(5)
        self.find_rules_sizer.Add(self.scoreImageBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.find_rules_sizer.AddStretchSpacer()
        self.find_rules_panel.SetSizerAndFit(self.find_rules_sizer)

        # fetch and rules panel
        self.fetch_and_rules_sizer.Add((5, 5))
        self.fetch_and_rules_sizer.Add(self.fetch_panel, flag=wx.EXPAND)
        self.fetch_and_rules_sizer.Add((5, 5))
        self.fetch_and_rules_sizer.Add(self.find_rules_panel, flag=wx.EXPAND)
        self.fetch_and_rules_sizer.Add((5, 5))
        self.fetch_and_rules_sizer.Add(self.rules_text, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)      
        self.fetch_and_rules_sizer.Add((5, 5))
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
        self.bins_splitter.UpdateSize()

        # Set initial state
        self.obClassChoice.SetSelection(0)
        self.filterChoice.SetSelection(0)
        self.trainClassifierBtn.Disable()
        self.scoreAllBtn.Disable()
        self.scoreImageBtn.Disable()
        self.fetchSizer.Hide(self.fetchFromGroupSizer)

        #######################
        #### Model Section ####
        #######################

        # Define Classifiers
        RandomForestClassifier = GeneralClassifier("ensemble.RandomForestClassifier(n_estimators=100)", self)
        AdaBoostClassifier = GeneralClassifier("ensemble.AdaBoostClassifier()", self)
        SVC = GeneralClassifier("svm.SVC(probability=True)", self, scaler=True)
        
        GradientBoostingClassifier = GeneralClassifier("ensemble.GradientBoostingClassifier()", self)
        LogisticRegression = GeneralClassifier("linear_model.LogisticRegression()", self)
        LDA = GeneralClassifier("discriminant_analysis.LinearDiscriminantAnalysis()", self)
        KNeighborsClassifier = GeneralClassifier("neighbors.KNeighborsClassifier()", self, scaler=True)
        FastGentleBoostingClassifier = FastGentleBoosting(self)
        NeuralNetworkClassifier = GeneralClassifier("neural_network.MLPClassifier(hidden_layer_sizes=(12,12), solver='lbfgs', max_iter=500)", self, scaler=True)

        # JK - Start Add
        # Define the Random Forest classification algorithm to be default and set the default
        self.algorithm = RandomForestClassifier
        self.panelTxt.SetLabel(str(self.algorithm.panelTxt()))
        self.panelTxt2.SetLabel(str(self.algorithm.panelTxt2()))

        self.algorithms = {
            'RandomForestClassifier': RandomForestClassifier,
            'AdaBoostClassifier': AdaBoostClassifier,
            'SVC' : SVC,
            'GradientBoostingClassifier': GradientBoostingClassifier,
            'LogisticRegression': LogisticRegression,
            'LDA': LDA,
            'KNeighborsClassifier': KNeighborsClassifier,
            'FastGentleBoosting' : FastGentleBoostingClassifier,
            'NeuralNetwork' : NeuralNetworkClassifier
        }

        #####################
        #### GUI Section ####
        #####################

        # add the default classes
        #for class in range(1, num_classes+1):
        if p.class_names:
            bins = p.class_names.split(',')
            for bin in bins:
                bin = bin.strip()
                self.AddSortClass(bin)
        else:
            self.AddSortClass('positive')
            self.AddSortClass('negative')

        self.Layout()

        self.Center()
        self.MapChannels(p.image_channel_colors[:])
        self.BindMouseOverHelpText()

        # Watch the filter and gates list for updates
        p._filters.addobserver(self.UpdateFilterChoices)
        p.gates.addobserver(self.UpdateFilterChoices)

        # do event binding
        self.Bind(wx.EVT_CHOICE, self.OnSelectFilter, self.filterChoice)
        self.Bind(wx.EVT_CHOICE, self.OnClassifierChoice, self.classifierChoice)
        self.Bind(wx.EVT_BUTTON, self.OnFetch, self.fetchBtn)
        self.Bind(wx.EVT_BUTTON, self.OnAddSortClass, self.addSortClassBtn)
        self.Bind(wx.EVT_BUTTON, self.OnEvaluation, self.evaluationBtn)
        self.Bind(wx.EVT_BUTTON, self.OnTrainClassifier, self.trainClassifierBtn)
        self.Bind(wx.EVT_BUTTON, self.ScoreAll, self.scoreAllBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreImage, self.scoreImageBtn)

        self.nObjectsTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.nRulesTxt.Bind(wx.EVT_TEXT, self.ValidateNumberOfRules)
        self.nNeuronsTxt.Bind(wx.EVT_TEXT, self.ValidateNumberOfNeurons)
        self.nObjectsTxt.Bind(wx.EVT_TEXT_ENTER, self.OnFetch)

        self.status_bar.Bind(wx.EVT_SIZE, self.status_bar_onsize)
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
                name, file_extension = os.path.splitext(p.training_set)
                if '.txt' == file_extension: 
                    self.LoadTrainingSet(p.training_set)
                elif '.csv' == file_extension:
                    self.LoadTrainingSetCSV(p.training_set)
                else:
                    logging.error("Couldn't load the file! Make sure it is .txt or .csv")
                #self.LoadTrainingSet(p.training_set)

        # Apr 2021 - It's not clear why refreshing the training set on a timer is necessary. Disabling it.
        # self.AutoSave() # Autosave try out

    def status_bar_onsize(self, event):
        # draw the "add sort class..." button in the status bar
        button = self.addSortClassBtn
        width, height = self.status_bar.GetClientSize()
        # diagonal lines drawn on mac, so move let by height.
        button.SetPosition((width - button.GetSize()[0] - 1 - height, button.GetPosition()[1]))

    # When choosing the classifier in the rules panel
    def OnClassifierChoice(self, event):
        itemId = self.classifierChoice.GetSelection()
        self.classifierMenu.Check(itemId + 1, True)
        selectedItem = re.sub('[\W_]+', '', self.classifierMenu.FindItemById(itemId + 1).GetItemLabel())
        self.SelectAlgorithm(selectedItem)

    def OnSelectAlgorithm(self, event):
        if not isinstance(event.EventObject, wx.Menu):
            # Fix bug: The first bind we make likes to grab any event without a specific target.
            event.Skip()
            return
        selectedItem = re.sub('[\W_]+', '', self.classifierMenu.FindItemById(event.GetId()).GetItemLabel())
        self.SelectAlgorithm(selectedItem)

    # JK - Start Add
    # Parameter: selected Item is name of the selected Algorithm
    def SelectAlgorithm(self, selectedItem):
        try:
            self.algorithm = self.algorithms[selectedItem]
            logging.info("Classifier " + selectedItem + " successfully loaded")
            self.panelTxt.SetLabel(str(self.algorithm.panelTxt())) # Set new label to # box
            self.panelTxt2.SetLabel(str(self.algorithm.panelTxt2())) # Set new label to # box

            itemId = self.classifier2ItemId[selectedItem] # translate name to select
            self.classifierChoice.SetSelection(itemId - 1) # Set the rules panel selection

        except:
            # Fall back to default algorithm
            logging.error('Could not load specified algorithm, falling back to RandomForestClassifier.')
            self.algorithm = self.algorithms['RandomForestClassifier']

        if self.algorithm == self.algorithms['NeuralNetwork']:
            self.nRulesTxt.Hide()
            self.nNeuronsTxt.Show()
        else:
            self.nRulesTxt.Show()
            self.nNeuronsTxt.Hide()
        self.scalerMenuItem.Check(self.algorithm.scaler is not None)
        # Update the GUI complexity text and classifier description
        # self.panelTxt2.SetLabel(self.algorithm.get_params())
        self.panelTxt2.Parent.Layout()
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
        if keycode == wx.WXK_LEFT:
            if not self.unclassifiedBin.tiles:
                return
            for idx, tile in enumerate(self.unclassifiedBin.tiles):
                if tile.selected:
                    if idx == 0:
                        return
                    if not evt.ShiftDown():
                        self.unclassifiedBin.DeselectAll()
                    self.unclassifiedBin.tiles[idx - 1].Select()
                    return
            self.unclassifiedBin.tiles[-1].Select()
            return
        elif keycode == wx.WXK_RIGHT:
            if not self.unclassifiedBin.tiles:
                return
            for idx, tile in enumerate(self.unclassifiedBin.tiles[::-1]):
                if tile.selected:
                    if idx == 0:
                        return
                    if not evt.ShiftDown():
                        self.unclassifiedBin.DeselectAll()
                    self.unclassifiedBin.tiles[-idx].Select()
                    return
            self.unclassifiedBin.tiles[0].Select()
            return
        elif keycode == ord('F'):
            self.OnFetch(evt)
            return
        # convert from keycode to a channel index to match number keypress to channel
        # some keyboards match the number 1 to 325; others match 1 to 49
        # this conditional accounts for those differences
        # alternatively wx.GetUnicodeKey() will match 1 to 49 consistently, but may not respect numlock
        if keycode >= 325:
            chIdx = keycode - 325
        else:
            chIdx = keycode - 49
        if evt.ControlDown() or evt.CmdDown():
            # ctrl+N toggles channel #N on/off
            if len(self.chMap) > chIdx >= 0:
                self.ToggleChannel(chIdx)
            else:
                evt.Skip()
        elif 0 <= chIdx <= 9:
            bin = chIdx
            if bin < len(self.classBins):
                self.classBins[bin].AddObjects(self.unclassifiedBin.SelectedKeys(), srcID=self.unclassifiedBin.GetId(),
                                               deselect=True)
                if self.unclassifiedBin.tiles:
                    self.unclassifiedBin.tiles[0].Select()
            return
        else:
            evt.Skip()

    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            for (idx, color, item, menu) in list(self.chMapById.values()):
                if idx == chIdx and color.lower() == self.toggleChMap[chIdx].lower():
                    item.Check()
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            for (idx, color, item, menu) in list(self.chMapById.values()):
                if idx == chIdx and color.lower() == 'none':
                    item.Check()
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)

    def CreateMenus(self):
        ''' Create file menu and menu items '''
        self.fileMenu = wx.Menu()
        self.loadTSMenuItem = self.fileMenu.Append(-1, item='Load Training Set\tCtrl+O',
                                                   helpString='Loads objects and classes specified in a training set file.')
        self.saveTSMenuItem = self.fileMenu.Append(-1, item='Save Training Set\tCtrl+S',
                                                   helpString='Save your training set to file so you can reload these classified cells again.')
        self.fileMenu.AppendSeparator()
        # JEN - Start Add
        self.loadModelMenuItem = self.fileMenu.Append(-1, item='Load Classifier Model', helpString='Loads a classifier model specified in a text file')
        self.saveModelMenuItem = self.fileMenu.Append(-1, item='Save Classifier Model', helpString='Save your classifier model to file so you can use it again on this or other experiments.')
        self.fileMenu.AppendSeparator()
        # JEN - End Add
        self.exitMenuItem = self.fileMenu.Append(id=wx.ID_EXIT, item='Exit\tCtrl+Q', helpString='Exit classifier')
        self.GetMenuBar().Append(self.fileMenu, 'File')

        # View Menu
        viewMenu = wx.Menu()
        imageControlsMenuItem = viewMenu.Append(-1, item='Image Controls\tCtrl+Shift+I',
                                                helpString='Launches a control panel for adjusting image brightness, size, etc.')
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
            'FastGentleBoosting' : 8,
            'NeuralNetwork' : 9
        }

        rfMenuItem = self.classifierMenu.AppendRadioItem(1, item='RandomForest Classifier', help='Uses RandomForest to classify')
        adaMenuItem = self.classifierMenu.AppendRadioItem(2, item='AdaBoost Classifier', help='Uses AdaBoost to classify.')
        svcMenuItem = self.classifierMenu.AppendRadioItem(3, item='SVC', help='Uses Support Vector Machines to classify.')
        gbMenuItem = self.classifierMenu.AppendRadioItem(4, item='GradientBoosting Classifier', help='Uses GradientBoosting to classify')
        lgMenuItem = self.classifierMenu.AppendRadioItem(5, item='LogisticRegression', help='Uses LogisticRegression to classify.')
        ldaMenuItem = self.classifierMenu.AppendRadioItem(6, item='LDA', help='Uses LDA to classify.')
        knnMenuItem = self.classifierMenu.AppendRadioItem(7, item='KNeighbors Classifier', help='Uses the kNN algorithm to classify.')
        fgbMenuItem = self.classifierMenu.AppendRadioItem(8, item='Fast Gentle Boosting', help='Uses the Fast Gentle Boosting algorithm to find classifier rules.')
        mlpMenuItem = self.classifierMenu.AppendRadioItem(9, item='Neural Network', help='Uses the multi-layer perceptron neural network to classify.')

        self.GetMenuBar().Append(self.classifierMenu, 'Classifier')

        # Evaluation menu
        self.evalMenu = wx.Menu()

        # Plotting options
        confusionMenuItem = self.evalMenu.AppendRadioItem(-1, item='Confusion Matrix', help='Visualizes the Normalized Confusion Matrix')
        reportMenuItem = self.evalMenu.AppendRadioItem(-1, item='Classification Report', help='Visualization of Accuracy, Recall and F1 Scores')
        #paramsEditMenuItem = self.evalMenu.AppendRadioItem(2, text=u'ROC Curve', help='Plots a One vs all ROC Curve and calculates the area under the curve')
        #featureSelectMenuItem = self.evalMenu.AppendRadioItem(3, text=u'Precision Recall Curve', help='Plots a One vs all Precision Recall Curve')
        #learningMenuItem = self.evalMenu.AppendRadioItem(4, text=u'Learning Curve', help='Plots a One vs all Learning Curve')
        kfoldMenuItem = self.evalMenu.Append(-1, item='Set cross validation folds', helpString='Adjust how many cross validation folds are used in evaluation')

        self.GetMenuBar().Append(self.evalMenu, 'Evaluation')


        # Advanced menu
        advancedMenu = wx.Menu()
        rulesEditMenuItem = advancedMenu.Append(-1, item='Edit Rules...', helpString='Lets you edit the rules')
        paramsEditMenuItem = advancedMenu.Append(-1, item='Edit Parameters...', helpString='Lets you edit the hyperparameters')
        featureSelectMenuItem = advancedMenu.Append(-1, item='Check Features', helpString='Check the variance of your Training Data')
        saveMenuItem = advancedMenu.Append(-1, item='Save Thumbnails as PNG', helpString='Save TrainingSet thumbnails as PNG')
        self.scalerMenuItem = advancedMenu.AppendCheckItem(-1, item='Use Scaler',
                                                             help='Perform scaling normalization on training data')
        self.scalerMenuItem.Check(False)
        sampleReplacementItem = advancedMenu.AppendCheckItem(-1, item='Sample with replacement',
                                           help='Allow duplicates when fetching objects')
        sampleReplacementItem.Check(False)
        rejectDuplicatesItem = advancedMenu.AppendCheckItem(-1, item='Prevent duplicate objects',
                                                             help="Don't fetch objects which are already classified")
        rejectDuplicatesItem.Check(False)
        self.GetMenuBar().Append(advancedMenu, 'Advanced')

        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self, manual_url="5_classifier.html"), 'Help')


        # Bind events to different menu items
        self.Bind(wx.EVT_MENU, self.OnLoadTrainingSet, self.loadTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveTrainingSet, self.saveTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnLoadModel, self.loadModelMenuItem) # JEN - Added
        self.Bind(wx.EVT_MENU, self.SaveModel, self.saveModelMenuItem) # JEN - Added
        self.Bind(wx.EVT_MENU, self.OnShowImageControls, imageControlsMenuItem)
        self.Bind(wx.EVT_MENU, self.OnChangeEvaluationFolds, kfoldMenuItem)
        self.Bind(wx.EVT_MENU, self.OnParamsEdit, paramsEditMenuItem)
        self.Bind(wx.EVT_MENU, self.OnRulesEdit, rulesEditMenuItem)
        self.Bind(wx.EVT_MENU, self.OnFeatureSelect, featureSelectMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveThumbnails ,saveMenuItem)
        self.Bind(wx.EVT_MENU, self.OnToggleScaling, self.scalerMenuItem)
        self.Bind(wx.EVT_MENU, self.OnToggleReplacement, sampleReplacementItem)
        self.Bind(wx.EVT_MENU, self.OnToggleRejectDuplicates, rejectDuplicatesItem)

        # Bind events for algorithms
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, rfMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, adaMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, svcMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, gbMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, lgMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, ldaMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, knnMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, fgbMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAlgorithm, mlpMenuItem)


    def CreateChannelMenus(self):
        ''' Create color-selection menus for each channel. '''

        # Clean up existing channel menus
        try:
            menus = set([items[2].Menu for items in list(self.chMapById.values())])
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
        zippedChNamesChMap = list(zip(channel_names, self.chMap))

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
        for ids in list(self.chMapById.keys()):
            (chIndex, color, item, channel_menu) = self.chMapById[ids]
            if (color.lower() == 'none'):
                item.Check()
        for ids in list(self.imMapById.keys()):
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
        if evt.GetId() in self.imMapById:

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
        self.training_set_ready = False
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
        self.training_set_ready = False
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
        self.algorithm.UpdateBins([])
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
        self.training_set_ready = False
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
            for i in range(len(updatedList)):
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
            self.obClassChoice.SetItems(['random', 'sequential'])
            self.obClassChoice.SetSelection(0)
            self.scoreAllBtn.Disable()
            self.scoreImageBtn.Disable()
            return
        sel = self.obClassChoice.GetSelection()
        selectableClasses = ['random', 'sequential']

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
        self.training_set_ready = False
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

    # Save object thumbnails of training set
    def OnSaveThumbnails(self, evt):

        saveDialog = wx.DirDialog(self, "Choose input directory", 
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal() == wx.ID_OK:
            directory = saveDialog.GetPath()

            for bin in self.classBins:
                label = bin.label

                if not os.path.exists(directory + '/training_set'):
                    os.makedirs(directory + '/training_set')

                if not os.path.exists(directory + '/training_set' +  '/' + str(label)):
                    os.makedirs(directory + '/training_set' +  '/' + str(label))

                for tile in bin.tiles:
                    imagetools.SaveBitmap(tile.bitmap, directory + '/training_set/' + str(label) + '/' + str(tile.obKey) + '.png')

    def OnToggleScaling(self, evt):
        self.algorithm.toggle_scaler(evt.IsChecked())
        self.UpdateClassChoices()

    def OnToggleReplacement(self, evt):
        if evt.IsChecked():
            self.with_replacement = True
        else:
            self.with_replacement = False

    def OnToggleRejectDuplicates(self, evt):
        if evt.IsChecked():
            self.reject_duplicates = True
        else:
            self.reject_duplicates = False

    def OnFetch(self, evt):
        # Parse out the GUI input values
        nObjects = int(self.nObjectsTxt.Value)
        obClass = self.obClassChoice.Selection
        obClassName = self.obClassChoice.GetStringSelection()
        fltr_sel = self.filterChoice.GetStringSelection()

        statusMsg = 'Fetching %d %s %s' % (nObjects, obClassName, p.object_name[1])

        # Get object keys
        obKeys = []
        # unclassified random:
        if obClass == 0:
            if fltr_sel == 'experiment':
                obKeys = dm.GetRandomObjects(nObjects, with_replacement=self.with_replacement)
                statusMsg += ' from whole experiment'
            elif fltr_sel == 'image':
                imKey = self.GetGroupKeyFromGroupSizer()
                obKeys = dm.GetRandomObjects(nObjects, [imKey], with_replacement=self.with_replacement)
                statusMsg += ' from image %s' % (imKey,)
            elif fltr_sel in p.gates_ordered:
                obKeys = db.GetGatedObjects(fltr_sel, nObjects, random=True)
                if obKeys == []:
                    self.PostMessage('No objects were found in gate "%s"' % (fltr_sel))
                    return
                if self.with_replacement and len(obKeys) < nObjects:
                    obs = random.choices(obKeys, k=nObjects)
                statusMsg += ' from gate "%s"' % (fltr_sel)
            elif fltr_sel in p._filters_ordered:
                filteredImKeys = db.GetFilteredImages(fltr_sel)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in filter "%s"' % (fltr_sel))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys, with_replacement=self.with_replacement)
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
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys, with_replacement=self.with_replacement)
                if not obKeys:
                    self.PostMessage('No cells were found in this group. Group %s: %s' % (groupName,
                                                                                          ', '.join(
                                                                                              ['%s=%s' % (n, v) for n, v
                                                                                               in zip(colNames,
                                                                                                      groupKey)])))
                    return
                statusMsg += ' from group %s: %s' % (groupName,
                                                     ', '.join(['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))
        # unclassified sequential
        elif obClass == 1:
            if fltr_sel == 'experiment':
                obKeys = dm.GetAllObjects(N=nObjects)
                statusMsg += ' from whole experiment'
            elif fltr_sel == 'image':
                imKey = self.GetGroupKeyFromGroupSizer()
                obKeys = dm.GetAllObjects(imkeys=[imKey], N=nObjects)
                statusMsg += ' from image %s' % (imKey,)

            elif fltr_sel in p.gates_ordered:
                obKeys = db.GetGatedObjects(fltr_sel, nObjects, random=False)
                if obKeys == []:
                    self.PostMessage('No objects were found in gate "%s"' % (fltr_sel))
                    return
                statusMsg += ' from gate "%s"' % (fltr_sel)
            elif fltr_sel in p._filters_ordered:
                obKeys = dm.GetAllObjects(filter_name=fltr_sel, N=nObjects)
                if obKeys == []:
                    self.PostMessage('No objects were found in filter "%s"' % (fltr_sel))
                    return
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
                obKeys = dm.GetAllObjects(imkeys=filteredImKeys, N=nObjects)
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
                elif fltr_sel in p.gates_ordered:
                    # We gate on objects, no need to filter imKeys
                    pass
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
            time_start = time()
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
                        obKeysToTry = dm.GetRandomObjects(100, with_replacement=self.with_replacement)
                    loopMsg = ' from whole experiment'
                elif fltr_sel == 'image':
                    # All objects are tried in first pass
                    if attempts > 0:
                        break
                    imKey = self.GetGroupKeyFromGroupSizer()
                    obKeysToTry = [imKey]
                    loopMsg = ' from image %s' % (imKey,)
                elif fltr_sel in p.gates_ordered:
                    obKeysToTry = db.GetGatedObjects(fltr_sel, 100, random=True)
                    if obKeysToTry == []:
                        self.PostMessage('No objects were found in gate "%s"' % (fltr_sel))
                        return
                    loopMsg = ' from gate %s' % (fltr_sel)
                else:
                    obKeysToTry = dm.GetRandomObjects(100, filteredImKeys, with_replacement=self.with_replacement)
                    obKeysToTry.sort()
                    if fltr_sel in p._filters_ordered:
                        loopMsg = ' from filter %s' % (fltr_sel)
                    elif fltr_sel in p._groups_ordered:
                        loopMsg = ' from group %s: %s' % (fltr_sel,
                                                          ', '.join(
                                                              ['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))

                self.PostMessage(f'Classifying {len(obKeysToTry)} {p.object_name[1]}.')

                if obClassName == 'uncertain':
                    obKeys += self.algorithm.FilterObjectsFromClassN(obClass - 1, obKeysToTry, uncertain=True)
                else:
                    obKeys += self.algorithm.FilterObjectsFromClassN(obClass - 1, obKeysToTry)


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
                elif time() - time_start > 30:
                    dlg = wx.MessageDialog(self, 'Found %d %s after %d seconds. Continue searching?'
                                           % (len(obKeys), p.object_name[1], time() - time_start),
                                           'Continue searching?', wx.YES_NO | wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    dlg.Destroy()
                    if response == wx.ID_NO:
                        break
                    time_start = time()

            statusMsg += loopMsg

        if self.reject_duplicates:
            used_keys = set(self.unclassifiedBin.GetObjectKeys())
            for bin in self.classBins:
                used_keys.update(bin.GetObjectKeys())
            obKeys = list(set(obKeys) - used_keys)
            if len(obKeys) == 0:
                self.PostMessage("All fetched objects had already been used.")
                return

        self.unclassifiedBin.AddObjects(obKeys[:nObjects], self.chMap, pos='last',
                                        display_whole_image=p.classification_type == 'image')
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
                            defaultDir=os.getcwd(), style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadModel(filename)

    # Get the name of the loaded model file
    def GetModelData(self, filename):
        import joblib
        try: 
            return joblib.load(filename)
        except:
            logging.error("Couldn't check model!")

    def LoadModel(self, filename):
        '''
        Loads the selected file and parses the classifier model.
        '''
        self.training_set_ready = False
        self.PostMessage('Loading classifier model from: %s' % filename)
        # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        #os.chdir(os.path.split(filename)[0])
        self.defaultModelFileName = os.path.split(filename)[1]
        # self.RemoveAllSortClasses(False) # Don't remove sorted classes

        try:
            # Get the name of the loaded file
            model, bin_labels, load_name, features = self.GetModelData(filename)

            for bin in self.classBins:
                if len(bin.GetObjectKeys()) > 0:
                    dlg = wx.MessageDialog(self, 'Loading a model will clear existing training objects. Continue?',
                                           'Load model?', wx.YES_NO | wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    dlg.Destroy()
                    if response == wx.ID_NO:
                        return
                break

            if self.algorithm.name != load_name:
                logging.info("Detected different setted classifier: " + self.algorithm.name + ", switching to " + load_name)
            if load_name in self.algorithms:
                self.algorithm = self.algorithms[load_name]
                itemId = self.classifier2ItemId[load_name]
                # Checks the MenuItem
                self.classifierMenu.Check(itemId, True)
                self.classifierChoice.SetSelection(itemId - 1) # Set the rules panel selection
                self.algorithm.LoadModel(filename)
                self.scalerMenuItem.Check(self.algorithm.scaler is not None)
                self.RemoveAllSortClasses()
                for label in bin_labels:
                    self.AddSortClass(label)
                # for label in self.algorithm.bin_labels:
                for bin in self.classBins:
                    bin.trained = True
                self.scoreAllBtn.Enable()
                self.scoreImageBtn.Enable()
                self.algorithm.trained = True
                self.PostMessage('Classifier model successfully loaded')

                # Some User Information about the loaded Algorithm
                self.PostMessage('Loaded trained classifier: ' + self.algorithm.name + ' on classes:')
                for label in self.algorithm.bin_labels:
                    self.PostMessage(label)
                self.PostMessage('CAUTION: Classifier needs to be trained on the current data set!')
            else:
                logging.error("Algorithm: %s doesn't exist", load_name)

        except:
            self.scoreAllBtn.Disable()
            self.scoreImageBtn.Disable()

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
            self.algorithm._set_features(self.trainingSet.colnames)
            self.algorithm.SaveModel(filename, bin_labels)
            self.PostMessage('Classifier model succesfully saved.')

    def OnLoadTrainingSet(self, evt):
        '''
        Present user with file select dialog, then load selected training set.
        '''
        dlg = wx.FileDialog(self, "Select the file containing your classifier training set.",
                            defaultDir=os.getcwd(),
                            wildcard='CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt',
                            style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            name, file_extension = os.path.splitext(filename)
            if '.txt' == file_extension: 
                self.LoadTrainingSet(filename)
            elif '.csv' == file_extension:
                self.LoadTrainingSetCSV(filename)
            else:
                logging.error("Couldn't load the file! Make sure it is .txt or .csv")

    # def OnLoadFullTrainingSet(self, evt):
    #     '''
    #     Present user with file select dialog, then load selected training set.
    #     '''
    #     dlg = wx.FileDialog(self, "Select the file containing your classifier training set.",
    #                         defaultDir=os.getcwd(),
    #                         wildcard='Text files(*.csv)|*.csv|All files(*.*)|*.*',
    #                         style=wx.OPEN | wx.FD_CHANGE_DIR)
    #     if dlg.ShowModal() == wx.ID_OK:
    #         filename = dlg.GetPath()
    #         self.LoadTrainingSetCSV(filename)

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

            num_objs = 0
            for bin in self.classBins:
                if bin.label in keysPerBin:
                    bin.AddObjects(keysPerBin[bin.label], self.chMap, priority=2,
                                   display_whole_image=p.classification_type == 'image')
                    num_objs += len(keysPerBin[bin.label])

            self.PostMessage('Training set loaded (%d %s).'%(num_objs,p.object_name[1]))
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
            self.Refresh()
            num_objs = 0
            for bin in self.classBins:
                if bin.label in keysPerBin:
                    bin.AddObjects(keysPerBin[bin.label], self.chMap, priority=2,
                                   display_whole_image=p.classification_type == 'image')
                    num_objs += len(keysPerBin[bin.label])
                    bin.Refresh()
            self.PostMessage('Training set loaded (%d %s).'%(num_objs,p.object_name[1]))
            self.GetNumberOfClasses() # Logs number of classes


    def OnSaveTrainingSet(self, evt):
        self.SaveTrainingSet()

    def SaveTrainingSet(self):
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

    def SaveTrainingSetAsCSV(self, filename):
        classDict = {}
        trainingSet = self.trainingSet # Create Save Copy
        try:
            self.trainingSet = TrainingSet(p)
            self.trainingSet.Create([bin.label for bin in self.classBins], [bin.GetObjectKeys() for bin in self.classBins])
            self.training_set_ready = True
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

    # Nice plotting which depends on which plot one choses
    def OnEvaluation(self, evt):
        items = self.evalMenu.GetMenuItems()
        selectedText = ""
        for item in items:
            if item.IsChecked():
                selectedText = item.GetItemLabel()

        # if selectedText == "ROC Curve":
        #     self.PlotROC()
        # elif selectedText == "Learning Curve":
        #     self.PlotLearningCurveWrapper()
        # elif selectedText == "Precision Recall Curve":
        #     self.PlotPrecisionRecall()
        if selectedText == "Confusion Matrix":
            folds = min(self.kFolds, min([len(bin.GetObjectKeys()) for bin in self.classBins]))
            logging.info(f"Evaluating with {folds} cross-validation folds")
            self.algorithm.ConfusionMatrix(folds)
        else:
            self.algorithm.CheckProgress()

    # def PlotLearningCurveWrapper(self):
    #     from sklearn import cross_validation
    #     model = self.algorithm
    #     clf = model.classifier
    #     X_train = self.trainingSet.values
    #     y_train = self.trainingSet.label_array

    #     # Training Set is currently sorted. I will shuffle it
    #     y_trans = y_train.reshape(y_train.shape[0],1)
    #     df_values = pd.DataFrame(X_train, columns=self.trainingSet.colnames)
    #     df_class = pd.DataFrame(y_trans, columns=["Class"])
    #     df = pd.concat([df_class, df_values],axis=1)
    #     df = df.reindex(np.random.permutation(df.index))
    #     X_train = df[self.trainingSet.colnames].values
    #     y_train = df["Class"].values

    #     #cv = cross_validation.StratifiedKFold(y_train, n_folds=3, shuffle=False)
    #     plot_title = 'Learning Curves ({})'.format(model.name)
    #     self.PlotLearningCurve(clf, plot_title, X_train, y_train, cv=5)

    from .utils import delay
    # Add AutoSave by DD
    @delay(360.0) # every 5 min
    def AutoSave(self):
        #logging.info("Autosaving ...")
        try:
            self.AutoSaveTrainingSet() # Saves only labels
            self.AutoSave()
        except:
            #logging.error("Autosaving failed.")
            pass

    # Same as Update Training Set, just without box
    def AutoSaveTrainingSet(self):
        # pause tile loading
        with tilecollection.load_lock():
            try:
                def cb(frac):
                    self.PostMessage(f'{int(frac*100)}% saved')

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
        if self.training_set_ready:
            return True
        # pause tile loading
        self.PostMessage('Waiting for image loader to finish current job.')
        with tilecollection.load_lock():
            try:
                def cb(frac):
                    cont, skip = dlg.Update(int(frac * 100.), 'Saving training set: %d%% complete' % (frac * 100.))
                    if not cont:  # cancel was pressed
                        dlg.Destroy()
                        raise StopCalculating()
                self.PostMessage('Saving training set.')
                dlg = wx.ProgressDialog('Fetching cell data for training set...', '0% Complete', 100, self,
                                        wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME |
                                        wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE)
                self.trainingSet = TrainingSet(p)
                try:
                    self.trainingSet.Create(labels=[bin.label for bin in self.classBins],
                                        keyLists=[bin.GetObjectKeys() for bin in self.classBins],
                                        callback=cb)
                    self.PostMessage('Training set saved.')
                    self.training_set_ready = True
                except Exception as e:
                    self.PostMessage('Error: Training set could not be saved.')
                    print("Error generating training set: ", e)
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

    def TrainClassifier(self):
        try:
            nRules = int(self.nRulesTxt.GetValue())
        except:
            logging.error('Unable to parse number of rules')
            return
        if self.algorithm == self.algorithms['NeuralNetwork']:
            nNeurons = self.nNeuronsTxt.GetValue()
            splitneurons = nNeurons.split(',')
            if nNeurons == "":
                # No layers is fine
                pass
            elif all([level.isdigit() for level in splitneurons]) and all([int(level) > 0 for level in splitneurons]):
                # All layers must have at least 1 neuron
                pass
            else:
                logging.error("Unable to parse neuron parameters")
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

                # JK - Start Modification
                # Train the desired algorithm
                # Legacy Code
                if self.algorithm.name == "FastGentleBoosting":
                    dlg = wx.ProgressDialog('Training classifier...', '0% Complete', 100, self,
                                            wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME |
                                            wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE)
                    self.algorithm.Train(
                        self.trainingSet.colnames, nRules, self.trainingSet.label_matrix,
                        self.trainingSet.values, output, callback=cb
                    )
                else:
                    dlg = wx.ProgressDialog('Training classifier...', 'Training in progress', 100, self,
                                            wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE)
                    dlg.Pulse()
                    # Convert labels
                    self.algorithm.Train(self.trainingSet.label_array, self.trainingSet.values, output)
                    self.nRules = nRules # Hack 

                # JK - End Modification

                self.PostMessage('Classifier trained in %.2fs.' % (time() - t1))
                dlg.Destroy()

                self.rules_text.SetValue(self.algorithm.ShowModel())
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
        # self.UpdateTrainingSet()
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

        self.ClassifyImage(imKey)

    def ClassifyImage(self, imKey):
        # Score the Image
        classHits = self.ScoreImage(imKey)
        # Get object coordinates in image and display
        classCoords = {}
        trainingCoords = {}
        training_obKeys = self.trainingSet.get_object_keys()
        for className, obKeys in classHits.items():
            training_keys = [key for key in obKeys if key in training_obKeys]
            if training_keys:
                trainingCoords['training ' + className] = db.GetObjectsCoords(training_keys)
            else:
                trainingCoords['training ' + className] = []
            object_keys = [key for key in obKeys if key not in training_obKeys]
            if object_keys:
                classCoords[className] = db.GetObjectsCoords(object_keys)
            else:
                classCoords[className] = []
        classCoords.update(trainingCoords)
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

        # record the column indices for the keys
        # CONSTRUCT ARRAY OF TABLE DATA
        classCounts = []
        tableData = []
        for className, obKeys in list(classHits.items()):
            classCounts.append(len(classCoords[className]))
        tableData += imKey
        tableData += [sum(classCounts)]
        tableData += classCounts

        labels = list(dbconnect.image_key_columns())
        key_col_indices = [i for i in range(len(labels))]
        labels = self.getLabels(labels, nClasses)
        trainingCountsRow = np.zeros(len(self.trainingSet.labels), dtype=int).tolist()
        training_table = pd.DataFrame(self.trainingSet.get_object_keys(), columns=["ImageNumber", "ObjectNumber"])
        training_table["Class"] = self.trainingSet.get_class_per_object()
        subset = training_table[training_table["ImageNumber"] == imKey[0]]
        for idx, lab in enumerate(self.trainingSet.labels):
            trainingCountsRow[idx] += len(subset[subset["Class"] == lab])
        tableRow = [sum(trainingCountsRow)]
        tableRow.extend(trainingCountsRow)
        tableData.extend(tableRow)
        grid.table_from_array(np.array([tableData]), labels, 'Image', key_col_indices)
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
        # self.UpdateTrainingSet()
        groupChoices = ['Image'] + p._groups_ordered
        filterChoices = [None] + p._filters_ordered
        nClasses = len(self.classBins)
        two_classes = nClasses == 2
        nKeyCols = len(dbconnect.image_key_columns())

        # GET GROUPING METHOD AND FILTER FROM USER
        enrichments = True
        if p.classification_type == 'image':
            enrichments = False

        dlg = ScoreDialog(self, groupChoices, filterChoices, enrichments)
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

            if not p.class_table:
                dlg = wx.MessageDialog(self,
                                       'No class table name was specified in the .properties file. Would you like to '
                                       'save per-object class data? If yes, a table called "object_class" will be made',
                                       'Do you want to save per-object class data?',
                                       wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                response = dlg.ShowModal()
                if response == wx.ID_YES:
                    p.class_table = "object_class"

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
                                    wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT
                                    | wx.PD_AUTO_HIDE)

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

            if p.class_table and overwrite_class_table:
                dlg = wx.ProgressDialog('Calculating per-object scores...', 'Generating..',
                                        100,
                                        self,
                                        )

                self.PostMessage('Saving %s classes to database...' % (p.object_name[0]))
                self.algorithm.CreatePerObjectClassTable([bin.label for bin in self.classBins], dlg.Update)
                self.PostMessage('%s classes saved to table "%s"' % (p.object_name[0].capitalize(), p.class_table))
                dlg.Destroy()

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
                                             in list(dm.SumToGroup(imData, group).items())], dtype=object)
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
        training_table = pd.DataFrame(self.trainingSet.get_object_keys(), columns=["ImageNumber", "ObjectNumber"])
        training_table["Class"] = self.trainingSet.get_class_per_object()
        labels = self.trainingSet.labels

        for i, row in enumerate(groupedKeysAndCounts):
            # Start this row with the group key:
            imageNumber = list(row[:nKeyCols])
            tableRow = imageNumber
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
                    if two_classes:
                        tableRow += ['NaN'] * 3
                    else:
                        tableRow += ['NaN'] * 2 * len(countsRow)
            #training set counts
            trainingCountsRow = np.zeros(len(labels), dtype=int).tolist()
            subset = training_table[training_table["ImageNumber"] == tableRow[0]]
            for idx, lab in enumerate(labels):
                trainingCountsRow[idx] += len(subset[subset["Class"] == lab])
            tableRow += [sum(trainingCountsRow)]
            tableRow += trainingCountsRow
            tableData.append(tableRow)
        tableData = np.array(tableData, dtype=object)

        if wants_enrichments:
            t5 = time()
            self.PostMessage('time to compute enrichment scores: %.3fs' % (t5 - t4))

        # CREATE COLUMN LABELS LIST
        # if grouping isn't per-image, then get the group key column names.
        if group != groupChoices[0]:
            labels = dm.GetGroupColumnNames(group)
            labels += ['Images']
        else:
            labels = list(dbconnect.image_key_columns())
            if p.plate_id and p.well_id:
                labels += [p.plate_id]#labels += ['Plate ID']
                labels += [p.well_id]
        labels = self.getLabels(labels, nClasses, wants_enrichments=wants_enrichments)
        key_col_indices = list(range(nKeyCols))
        try:
            title = "Hit table (grouped by %s)" % (group,)
            if filter:
                title += " filtered by %s" % (filter,)
            title += ' (%s)' % (os.path.split(p._filename)[1])
            grid = tableviewer.TableViewer(self, title=title)
            grid.table_from_array(tableData, labels, group, key_col_indices)
            grid.Show()
        except Exception as e:
            wx.MessageDialog(self, 'Unable to calculate enrichment scores.', 'Error', style=wx.OK).ShowModal()
            print("Enrichment calculation failed: ", e)

        self.SetStatusText('')

    def getLabels(self, firstLabel, nClasses, wants_enrichments=False):
        labels = firstLabel
        # record the column indices for the keys

        labels += ['Total\n %s Count' % (p.object_name[0].capitalize())]
        for i in range(nClasses):
            labels += ['%s\n %s Count' % (self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        if p.area_scoring_column is not None:
            labels += ['Total\n %s Area' % (p.object_name[0].capitalize())]
            for i in range(nClasses):
                labels += ['%s\n %s Area' % (self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        if wants_enrichments:
            for i in range(nClasses):
                labels += ['p(Enriched)\n' + self.classBins[i].label]
            if nClasses==2:
                labels += ['Enriched Score\n' + self.classBins[0].label]
            else:
                for i in range(nClasses):
                    labels += ['Enriched Score\n' + self.classBins[i].label]
        #Training cell count
        labels += ['Training Total\n %s Count' % (p.object_name[0].capitalize())]
        for i in range(nClasses):
            labels += ['Training %s\n %s Count' % (self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        return labels

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
        from wx.grid import EVT_GRID_CMD_LABEL_LEFT_CLICK
        grid.grid.Unbind(EVT_GRID_CMD_LABEL_LEFT_CLICK)

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
        if filter == 'experiment' or filter in p._filters_ordered or filter in p.gates_ordered:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
        elif filter == 'image' or filter in p._groups_ordered:
            self.SetupFetchFromGroupSizer(filter)
            self.fetchSizer.Show(self.fetchFromGroupSizer, True)
        elif filter == CREATE_NEW_FILTER:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
            from .columnfilter import ColumnFilterDialog
            tables = []
            for t in [p.image_table, p.object_table, p.class_table]:
                if isinstance(t, str):
                    tables.append(t)
            cff = ColumnFilterDialog(self, tables=tables, size=(600,150))
            if cff.ShowModal() == wx.OK:
                fltr = cff.get_filter()
                fname = cff.get_filter_name()
                p._filters[fname] = fltr
                self.filterChoice.SetStringSelection(fname)
            else:
                self.filterChoice.Select(0)
            cff.Destroy()
        self.fetch_panel.Layout()
        self.fetch_panel.Refresh() 

    def UpdateFilterChoices(self, evt):
        selected_string = self.filterChoice.GetStringSelection()
        self.filterChoice.SetItems(['experiment', 'image'] + p._filters_ordered + p.gates_ordered +
                                              p._groups_ordered + [CREATE_NEW_FILTER])
        if selected_string in self.filterChoice.Items:
            self.filterChoice.SetStringSelection(selected_string)
        else:
            self.filterChoice.Select(0)
        self.filterChoice.Layout()

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
            if group == 'image' or fieldTypes[i] == int:
                fieldInp = wx.TextCtrl(self.fetch_panel, -1, value=validVals[0], size=(80, -1))
                fieldInp.SetSelection(-1,-1) # Fix #203, textCtrl has different API since wx3
            else:
                fieldInp = wx.Choice(self.fetch_panel, -1, size=(80, -1),
                                       choices=['__ANY__'] + validVals)
                fieldInp.SetSelection(0)

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
            self.fetchFromGroupSizer.Add(10, 20, 0)

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

    def ValidateNumberOfNeurons(self, evt=None):
        if self.algorithm == self.algorithms['NeuralNetwork']:
            nNeurons = self.nNeuronsTxt.GetValue()
            if nNeurons == "":
                self.algorithms['NeuralNetwork']  = GeneralClassifier(f"neural_network.MLPClassifier(hidden_layer_sizes=(), solver='lbfgs', max_iter=500)", self, scaler=self.algorithm.scaler is not None)
                self.algorithm = self.algorithms['NeuralNetwork']
                return True
            splitneurons = nNeurons.split(',')
            if all([level.isdigit() for level in splitneurons]) and all([int(level) > 0 for level in splitneurons]):
                self.nNeuronsTxt.SetForegroundColour('#000001')
                # Refresh the classifier
                self.algorithms['NeuralNetwork']  = GeneralClassifier(f"neural_network.MLPClassifier(hidden_layer_sizes=({nNeurons}), solver='lbfgs', max_iter=500)", self, scaler=self.algorithm.scaler is not None)
                self.algorithm = self.algorithms['NeuralNetwork']
                return True
            else:
                self.nNeuronsTxt.SetForegroundColour('#0000FF')
                return False
        else:
            return True

    def GetGroupKeyFromGroupSizer(self, group=None):
        ''' Returns the text in the group text inputs as a group key. '''
        if group is not None:
            fieldTypes = dm.GetGroupColumnTypes(group)
        else:
            fieldTypes = [int for input in self.groupInputs]
        groupKey = []
        for input, ftype in zip(self.groupInputs, fieldTypes):
            if isinstance(input, wx.TextCtrl):
                val = input.GetValue()
            else:
                val = input.GetStringSelection()
            # if the value is blank, don't bother typing it, it is a wildcard
            if val != '__ANY__':
                val = ftype(val)
            groupKey += [val]
        return tuple(groupKey)

    def OnShowImageControls(self, evt):
        ''' Shows the image adjustment control panel in a new frame. '''
        self.imageControlFrame = wx.Frame(self, size=(470, 155))
        ImageControlPanel(self.imageControlFrame, self, brightness=self.brightness, scale=self.scale,
                          contrast=self.contrast)
        self.imageControlFrame.Show(True)

    def OnChangeEvaluationFolds(self, evt):
        ''' Shows the evaluation k-fold adjustment control. '''
        dlg = wx.NumberEntryDialog(
            self,
            'Number of cross validation folds:',
            'Enter folds',
            "Evaluate Classifier",
            self.kFolds,
            1,
            1000
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.kFolds = int(dlg.GetValue())
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

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
                except ValueError as e:
                    wx.MessageDialog(self, 'Unable to parse your edited rules:\n\n' + str(e), 'Parse error',
                                     style=wx.OK).ShowModal()
                    self.OnRulesEdit(evt)
                    return
                self.keysAndCounts = None
                self.rules_text.SetValue(self.algorithm.ShowModel())
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

                except ValueError as e:
                    wx.MessageDialog(self, 'Unable to parse your edited hyperparameters:\n\n' + str(e), 'Parse error',
                                     style=wx.OK).ShowModal()
                    self.OnParamsEdit(evt)
                    return
                self.keysAndCounts = None
                self.rules_text.SetValue(self.algorithm.ShowModel())
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
        return self.algorithm.IsTrained()

    def Destroy(self):
        p._filters.removeobserver(self.UpdateFilterChoices)
        p.gates.removeobserver(self.UpdateFilterChoices)
        ''' Kill off all threads before combusting. '''
        super(Classifier, self).Destroy()
        import threading
        t = tilecollection.TileCollection()
        if self in t.loader.notify_window:
            t.loader.notify_window.remove(self)
        # If no other windows are attached to the loader we shut it down and delete the tilecollection.
        if len(t.loader.notify_window) == 0:
            for thread in threading.enumerate():
                if thread != threading.currentThread() and thread.getName().lower().startswith('tileloader'):
                    logging.debug('Aborting thread %s' % thread.getName())
                    try:
                        thread.abort()
                    except:
                        pass
            tilecollection.TileCollection.forget()

    # Get number of labels/classes we have in our training set
    def GetNumberOfClasses(self):
        number_of_classes = len(self.trainingSet.labels)
        # logging.info("We have " + str(number_of_classes) + " Classes")
        return number_of_classes

    # Buggy?
    def PlotPrecisionRecall(self):
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

    def PlotProbs(self,values, key="object"):
        labels = self.trainingSet.labels
        fig = plt.figure()
        fig.canvas.set_window_title(f"{fig.canvas.get_window_title()} - {key}")
        ax = fig.add_subplot(111)

        tmp_df = pd.DataFrame(labels,columns=["Class"])
        df = pd.DataFrame(values,columns=["Probs"])
        df = pd.concat([df,tmp_df],axis=1)
        df = df.sort_values("Probs",ascending=False)
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
        from sklearn.model_selection import learning_curve

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
    from .errors import show_exception_as_dialog

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

    p = Properties()
    db = dbconnect.DBConnect()
    dm = DataModel()

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
        print("Caught exception while killing VM")
