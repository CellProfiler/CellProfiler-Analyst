'''
Classifier.py
Authors: afraser
'''

import wx
import wx.grid
import numpy
from cStringIO import StringIO

from DataModel import DataModel
from DBConnect import DBConnect
from Properties import Properties

from CellBoard import CellBoard
from ImageTile import ImageTile
from DragObject import DragObject
from DropTarget import DropTarget
from LoadTilesWorker import *

from TrainingSet import TrainingSet
import FastGentleBoostingMulticlass
import MulticlassSQL
import PolyaFit
import DirichletIntegrate

from DataGrid import DataGrid

p = Properties.getInstance()
db = DBConnect.getInstance()



class SortClass(object):
    def __init__(self, label, board, sizer, trained=False):
        self.label = label
        self.board = board
        self.sizer = sizer
        self.trained = trained



class ClassifierGUI(wx.Frame):
    ''' =========================================================================
    GUI Interface and functionality for the Classifier
    ============================================================================= '''
    def __init__(self, parent):
        
        wx.Frame.__init__(self, parent, id=-1, title="pyClassifier", size=(800,600))
        
        if p.IsEmpty():
            self.LoadProperties()
            
        if DataModel.getInstance().IsEmpty():
            print "ERROR: <ClassifierGUI.__init__>: DataModel is empty. Classifier requires a populated DataModel to function."
            self.Close()
        
        self.worker = None
        self.weaklearners = None
        self.trainingSet = None
        self.classes = []
        self.binsCreated = 0
        self.chMap = p.image_channel_colors[:]
        self.toggleChMap = p.image_channel_colors[:] # this is used to store previous color mappings when toggling colors on/off with ctrl+1,2,3...
        
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateFileMenu()
        self.CreateChannelMenus()
        self.CreateStatusBar()
        
        # Create the Fetch panel
        self.fetchSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Fetch '+p.object_name[1]),wx.HORIZONTAL)
        self.nObjectsTxt = wx.TextCtrl(self, id=wx.NewId(), value='20', size=(30,-1))
        self.obClassChoice = wx.Choice(self, id=wx.NewId(), choices=['random'])
        self.obClassChoice.SetSelection(0)
        filters = []
        if 'filters' in p.__dict__:
            filters = p.filters
        self.filterChoice = wx.Choice(self, id=wx.NewId(), choices=['experiment']+filters)
        self.filterChoice.SetSelection(0)
        self.fetchBtn = wx.Button(self, wx.NewId(), 'Fetch!')
        self.fetchSizer.AddStretchSpacer()
        self.fetchSizer.Add(wx.StaticText(self, wx.NewId(), 'Fetch'))
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.nObjectsTxt)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.obClassChoice)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(wx.StaticText(self, wx.NewId(), p.object_name[1]))
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(wx.StaticText(self, wx.NewId(), 'from'))
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.filterChoice)
        self.fetchSizer.AddSpacer((10,20))
        self.fetchSizer.Add(self.fetchBtn)
        self.fetchSizer.AddStretchSpacer()
        
        # Create the Train panel
        self.trainSizer = wx.StaticBoxSizer(wx.StaticBox(self, label="Train Classifier"),wx.VERTICAL)
        self.rulesTxt = wx.TextCtrl(self, wx.NewId(), size=(-1,60), style=wx.TE_MULTILINE)
        self.rulesTxt.SetEditable(False)
        self.trainSizer.Add(self.rulesTxt, proportion=0, flag=wx.EXPAND)
        self.trainSizer.AddSpacer((-1,5))
        self.trainSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.nRulesTxt = wx.TextCtrl(self, wx.NewId(), value='5', size=(30,-1))
        self.findRulesBtn = wx.Button(self, wx.NewId(), 'Find Rules')
        self.findRulesBtn.Disable()
        self.scoreAllBtn = wx.Button(self, wx.NewId(), 'Score All')
        self.scoreAllBtn.Disable()
        self.addSortClassBtn = wx.Button(self, wx.NewId(), "+", size=(30,30))
        self.trainSizer2.AddStretchSpacer()
        self.trainSizer2.Add(wx.StaticText(self, wx.NewId(), 'Max number of rules:'))
        self.trainSizer2.Add((5,20))
        self.trainSizer2.Add(self.nRulesTxt)
        self.trainSizer2.Add((5,20))
        self.trainSizer2.Add(self.findRulesBtn)
        self.trainSizer2.Add((5,20))
        self.trainSizer2.Add(self.scoreAllBtn)
        self.trainSizer2.Add((5,20))
        self.trainSizer2.Add(self.addSortClassBtn)
        self.trainSizer.Add(self.trainSizer2, proportion=1, flag=wx.EXPAND)
        
        # Create the sorting panel (splitter window)
        self.splitter = wx.SplitterWindow(self)
        self.splitter.SetMinimumPaneSize(30)
        self.splitter.SetSashGravity(0.5)
        # top half
        self.topSortPanel = wx.Panel(self.splitter)
        self.topSortSizer = wx.StaticBoxSizer(wx.StaticBox(self.topSortPanel, label='unclassified '+p.object_name[1]))
        self.topSortPanel.SetSizer(self.topSortSizer)
        self.unclassifiedBoard = CellBoard(parent=self.topSortPanel, classifier=self)
        self.topSortSizer.Add( self.unclassifiedBoard, proportion=1, flag=wx.EXPAND )
        # bottom half
        self.bottomSortPanel = wx.Panel(self.splitter)
        self.bottomSortSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomSortPanel.SetSizer(self.bottomSortSizer)
        # add the default classes
        self.AddSortClass('positive')
        self.AddSortClass('negative')
        
        self.splitter.SplitHorizontally(self.topSortPanel, self.bottomSortPanel)
        
        self.outerSizer = wx.BoxSizer(wx.VERTICAL)
        self.outerSizer.Add(self.fetchSizer, proportion=0, flag=wx.EXPAND)
        self.outerSizer.Add(self.trainSizer, proportion=0, flag=wx.EXPAND)
        self.outerSizer.Add(self.splitter, proportion=1, flag=wx.EXPAND)
        self.SetSizer(self.outerSizer)
        
        
        self.MapChannels(p.image_channel_colors[:])

        # do event binding
#        self.Bind(wx.EVT_MENU, self.OnLoadProperties, self.loadPropertiesMenuItem)
#        self.Bind(wx.EVT_MENU, self.OnSaveProperties, self.savePropertiesMenuItem)
        self.Bind(wx.EVT_MENU, self.OnLoadTrainingSet, self.loadTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveTrainingSet, self.saveTSMenuItem)
        self.Bind(wx.EVT_BUTTON, self.OnFetch, self.fetchBtn)
        self.Bind(wx.EVT_BUTTON, self.OnAddSortClass, self.addSortClassBtn)
        self.Bind(wx.EVT_BUTTON, self.OnFindRules, self.findRulesBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreAll, self.scoreAllBtn)
        self.nObjectsTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.nRulesTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnDragSash)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MENU, self.OnClose, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)    
        self.Bind(wx.EVT_CHAR, self.OnKey)    
        
        EVT_IMAGE_RESULT(self, self.OnImageResult)
        

    
    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        print 'classifier KEY'
        if evt.ControlDown():
            chIdx = evt.GetKeyCode()-49
            if len(self.chMap) > chIdx >= 0:   # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
            
            
    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)
                    

    def CreateFileMenu(self):
        ''' Create file menu and menu items '''
        self.fileMenu = wx.Menu()
#        self.loadPropertiesMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='Load properties', help='Clears the current session and imports settings from a new properties file.')
#        self.savePropertiesMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='Save rules', help='')
        self.loadTSMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='Load training set', help='Loads objects and classes specified in a training set file.')
        self.saveTSMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='Save training set', help='Save your training set to file so you can reload these classified cells again.')
        self.exitMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.wx.NewId(), text='Exit', help='Exit classifier')
#        self.fileMenu.AppendItem(self.loadPropertiesMenuItem)
#        self.fileMenu.AppendItem(self.savePropertiesMenuItem)
        self.fileMenu.AppendItem(self.loadTSMenuItem)
        self.fileMenu.AppendItem(self.saveTSMenuItem)
        self.fileMenu.AppendSeparator()
        self.fileMenu.AppendItem(self.exitMenuItem)
        self.GetMenuBar().Append(self.fileMenu, 'File')
        
        
    def CreateChannelMenus(self):
        ''' Create color-selection menus for each channel. '''
        chIndex=0
        self.chMapById = {}
        for channel, setColor in zip(p.image_channel_names, self.chMap):
            channel_menu = wx.Menu()
            for color in ['Red', 'Green', 'Blue', 'Cyan', 'Magenta', 'Yellow', 'Gray', 'None']:
                id = wx.NewId()
                self.chMapById[id] = (chIndex,color)
                if color.lower() == setColor.lower():
                    item = channel_menu.AppendRadioItem(id,color).Check()
                else:
                    item = channel_menu.AppendRadioItem(id,color)
                self.Bind(wx.EVT_MENU, self.OnMapChannels, item)
            channel_menu.InsertSeparator(3)
            channel_menu.InsertSeparator(8)
            self.GetMenuBar().Append(channel_menu, channel)
            chIndex+=1

        
    def AddSortClass(self, label):
        ''' Create a new CellBoard in a new StaticBoxSizer with the given label.
        This sizer is then added to the bottomSortSizer. '''
        sizer = wx.StaticBoxSizer(wx.StaticBox(self.bottomSortPanel, label=label), wx.VERTICAL)
        board = CellBoard(parent=self.bottomSortPanel, label=label, classifier=self)             # NOTE: board must be created after sizer or drops events will occur on the sizer
        sizer.Add(board, proportion=1, flag=wx.EXPAND)
        self.bottomSortSizer.Add(sizer, proportion=1, flag=wx.EXPAND)
        self.classes.append( SortClass(label,board,sizer) )
        self.bottomSortPanel.Layout()
        self.binsCreated += 1
        
    
    def RemoveSortClass(self, label):
        for cl in self.classes:
            if cl.label == label:
                # Remove the bin
                self.bottomSortSizer.Remove(cl.sizer)
                #cl.board.Clear()
                cl.board.Destroy()
                self.bottomSortPanel.Layout()
                # Remove the label from the class dropdown menu
                self.obClassChoice.SetItems([item for item in self.obClassChoice.GetItems() if item!=cl.label])
                self.obClassChoice.Select(0)
                # Remove the class from the list of classes
                self.classes.remove(cl)
                break
        self.weaklearners = None
        self.rulesTxt.SetValue('')
        for cl in self.classes:
            cl.trained = False
        self.UpdateClassChoices()
        
        
    def RemoveAllSortClasses(self):
        # Note: can't use "for cl in self.classes:"
        for label in [cl.label for cl in self.classes]:
            self.RemoveSortClass(label)
            
    
    def RenameClass(self, label):
        dlg = wx.TextEntryDialog(self, 'New class name:','Rename class')
        dlg.SetValue(label)
        print 'old',label
        if dlg.ShowModal() == wx.ID_OK:
            newLabel = dlg.GetValue()
            print 'new',newLabel
            if newLabel != label and newLabel in [cl.label for cl in self.classes]:
                errdlg = wx.MessageDialog(self, 'There is already a class with that name.', "Can't Name Class", wx.OK|wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    self.RenameClass(label)
                    return
            if ' ' in newLabel:
                errdlg = wx.MessageDialog(self, 'Labels can not contain spaces', "Can't Name Class", wx.OK|wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    self.RenameClass(label)
                    return
            for cl in self.classes:
                if cl.label == label:
                    cl.label = newLabel
                    cl.board.label = newLabel
                    break
            dlg.Destroy()
        self.UpdateBoardLabels()
        
        updatedList = self.obClassChoice.GetItems()
        sel = self.obClassChoice.GetSelection()
        for i in xrange(len(updatedList)):
            if updatedList[i] == label:
                updatedList[i] = newLabel
        self.obClassChoice.SetItems(updatedList)
        self.obClassChoice.SetSelection(sel)
        
    
    def OnLeftUp(self, evt):
        dropTarget = wx.FindWindowAtPointer()
        drag = DragObject.getInstance()
        if not drag.IsEmpty() and drag.source != dropTarget:
            if isinstance(dropTarget, DropTarget):
                dropTarget.ReceiveDrop(drag)
                if not self.trainingSet:
                    self.trainingSet = TrainingSet(p)
                    self.trainingSet.Create([], [])
            self.UpdateBoardLabels()
            drag.Empty()
            self.ReleaseMouse()
        #wx.SetCursor(wx.NullCursor)
        
        
    def UpdateBoardLabels(self):
        self.findRulesBtn.Disable()
        ts = False
        self.topSortSizer.GetStaticBox().SetLabel( 'unclassified '+p.object_name[1]+' ('+str(len(self.unclassifiedBoard.tiles))+')' )
        for cl in self.classes:
            cl.sizer.GetStaticBox().SetLabel( cl.label+' ('+str(len(cl.board.tiles))+')')
            if len(cl.board.tiles) > 0:
                if ts:
                    self.findRulesBtn.Enable()
                ts = True
                
    
    def UpdateClassChoices(self):
        if not self.weaklearners:
            self.obClassChoice.SetItems(['random'])
            self.obClassChoice.SetSelection(0)
            return
        sel = self.obClassChoice.GetSelection()
        selectableClasses = ['random']+[cl.label for cl in self.classes if cl.trained]
        self.obClassChoice.SetItems(selectableClasses)
        if len(selectableClasses) < sel:
            sel=0
        self.obClassChoice.SetSelection(sel)

    
    def OnFetch(self, evt):
        # If a worker already exists then stop it.
        if self.worker:
            # Note: The worker will finish loading it's last tile before it dies
            #    raises an ImageResult.  Therefore it's critical NOT to set worker=None
            #    here or it will be possible to start more than one worker at a time
            #    by clicking fetch repeatedly.
            self.worker.abort()
            self.fetchBtn.Disable()  # Disable the button until the operation finishes to prevent antsy users from restarting it.
            return
        
        # Parse out the GUI input values        
        nObjects    = int(self.nObjectsTxt.Value)
        obClass     = self.obClassChoice.Selection
        obClassName = self.obClassChoice.GetStringSelection()
        filter       = self.filterChoice.GetStringSelection()
        
        statusMsg = 'fetching '+str(nObjects)+' '+p.object_name[1]
        
        # Get object keys
        # unclassified:
        if obClass == 0:
            if filter == 'experiment':
                obKeys = dm.GetRandomObjects(nObjects)
                statusMsg += ' from whole experiment...'
            else:
                imKeysInFilter = db.GetFilteredImages(filter)
                obKeys = dm.GetRandomObjects(nObjects, imKeysInFilter)
                statusMsg += ' from filter "'+filter+'"...'
        # classified
        else:
            hits = 0
            obKeys = []
            if filter != 'experiment':
                imKeysInFilter = db.GetFilteredImages(filter)
            while len(obKeys) < nObjects:
                if filter == 'experiment':
                    obKeysToTry = dm.GetRandomObjects(100)
                    loopMsg = ' in class "'+obClassName+'" from whole experiment... '
                else:
                    obKeysToTry = dm.GetRandomObjects(100,imKeysInFilter)
                    loopMsg = ' in class "'+obClassName+'" from filter "'+filter+'"...'
                stump_query, score_query, find_max_query, class_query, count_query = MulticlassSQL.translate(self.weaklearners, self.trainingSet.colnames)
                obKeys += MulticlassSQL.FilterObjectsFromClassN(obClass, obKeysToTry, stump_query, score_query, find_max_query)
            statusMsg += loopMsg
                
        # Create a worker thread to load the tiles!
        self.worker = LoadTilesWorker(self, obKeys[:nObjects])
        
        # Toggle the fetch button text and give the user feedback
        self.fetchBtn.SetLabel('Stop')
        self.SetStatusText(statusMsg)
    
    
    def OnImageResult(self, evt):
        ''' Results from worker thread. '''
        if evt.data == None:
            self.fetchBtn.Enable()
            self.fetchBtn.SetLabel('Fetch!')
            self.SetStatusText('')
            self.worker = None
        else:
            tile = ImageTile(self.unclassifiedBoard, obKey=evt.data[0], images=evt.data[1], chMap=self.chMap, selected=False)
            self.unclassifiedBoard.AddTile(tile, pos='last')
            self.topSortSizer.GetStaticBox().SetLabel( 'unclassified '+p.object_name[1]+' ('+str(len(self.unclassifiedBoard.tiles))+')' )
        
        
    def OnLoadTrainingSet(self, evt):
        self.LoadTrainingSet()
        
    def LoadTrainingSet(self):
        ''' Presents the user with a file select dialog. 
        Loads the selected file, parses out object keys, and fetches the tiles. '''
        dlg = wx.FileDialog(self, "Select a the file containing your classifier training set.", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            
            self.SetStatusText('Loading training set from: '+filename)
            
            self.trainingSet = TrainingSet(p, filename)
            
            self.RemoveAllSortClasses()
            for label in self.trainingSet.labels:
                self.AddSortClass(label)
            for (label, key) in self.trainingSet.entries:
                for cl in self.classes:
                    if cl.label == label:
                        cl.board.AddObject(key, self.chMap[:], refresh=False)
                        break
            for cl in self.classes:
                cl.board.Refresh()
                cl.board.Layout()
        self.UpdateBoardLabels()
        self.SetStatusText('Training set loaded.')
        
    
    def OnSaveTrainingSet(self, evt):
        self.SaveTrainingSet()
        
    def SaveTrainingSet(self):
        import os
        defaultFileName = 'testTrainingSet.txt'
        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(), defaultFile=defaultFileName, wildcard='txt', style=wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal()==wx.ID_OK:
            self.SaveTrainingSetAs(saveDialog.GetPath())

    
    def SaveTrainingSetAs(self, filename):
        classDict = {}
        self.trainingSet = TrainingSet(p)
        self.trainingSet.Create([cl.label for cl in self.classes], [cl.board.GetObjectKeys() for cl in self.classes])
        self.trainingSet.Save(filename)
        
    
    def OnAddSortClass(self, evt):
        label = 'class_'+str(self.binsCreated)
        self.AddSortClass(label)
        self.RenameClass(label)
        
        
    def OnMapChannels(self, evt):
        (chIdx,color) = self.chMapById[evt.GetId()]
        self.chMap[chIdx] = color
        if color.lower() != 'none':
            self.toggleChMap[chIdx] = color
        self.MapChannels(self.chMap)

        
    def MapChannels(self, chMap):
        self.chMap = chMap
        
        # TODO: Need to update color menu selections
        
        self.unclassifiedBoard.MapChannels(chMap)
        for cl in self.classes:
            cl.board.MapChannels(chMap)
        self.Refresh()
        self.Layout()


    def ValidateIntegerField(self, evt):
        ''' Validates an integer-only TextCtrl '''
        txtCtrl = evt.GetEventObject()
        # NOTE: textCtrl.SetBackgroundColor doesn't appear to work
        #   foregroundcolor only works when not setting to black.  LAAAAMMMEEE!
        try:
            int(txtCtrl.GetValue())
            txtCtrl.SetForegroundColour('#000001')
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')
            
    
    def OnDragSash(self, evt):
        ''' Move the splitter sash as it is dragged. '''
        self.splitter.SetSashPosition(evt.SashPosition)
        
        
    def OnFindRules(self, evt):
        try:
            nRules = int(self.nRulesTxt.GetValue())
        except:
            print 'Unable to parse number of rules'
            return
        
        self.keysAndCounts = None    # Must erase current keysAndCounts so they will be recalculated from new rules
        
        self.trainingSet = TrainingSet(p)
        self.trainingSet.Create([cl.label for cl in self.classes], [cl.board.GetObjectKeys() for cl in self.classes])
        labelMatrix = self.ComputeLabelMatrix()
        output = StringIO()
        self.SetStatusText('Training classifier with '+str(nRules)+' rules...')
        self.weaklearners = FastGentleBoostingMulticlass.train(self.trainingSet.colnames, nRules, labelMatrix, self.trainingSet.values, output)
        self.SetStatusText('')
        self.rulesTxt.Value = output.getvalue()
        self.scoreAllBtn.Enable()

        for cl in self.classes:
            if len(cl.board.tiles) > 0:
                cl.trained = True
            else:
                cl.trained = False
        self.UpdateClassChoices()
        
        
    def OnScoreAll(self, evt):
        groupChoices = ['Image']
        if 'groups' in p.__dict__:
            groupChoices += p.groups
        dlg = wx.SingleChoiceDialog(self, 'Please choose a grouping method:', 'Score all', groupChoices, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:            
            group = str(dlg.GetStringSelection())
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        
        from time import time
        t1 = time()
        
        # SCORING NEEDS...
        # weaklearners, colnames, nClasses, keysAndCounts (if already calculated),
        
        nClasses = len(self.classes)
        
        #worker = CalculateScoresThread(self.weaklearners, self.trainingSet.colnames, nClasses, self.keysAndCounts, group)
        
        # Check if hit counts have already been calculated (since last training)
        # If not: Classify all objects into phenotype classes and count phenotype-hits per-image
        if self.keysAndCounts == None:
            stump_query, score_query, find_max_query, class_query, count_query = MulticlassSQL.translate(self.weaklearners, self.trainingSet.colnames)
            self.SetStatusText('Calculating %s counts for each class...' % p.object_name[0])
            self.keysAndCounts = MulticlassSQL.HitsAndCounts(stump_query, score_query, find_max_query, class_query, count_query)
        
        t2 = time()
        print 'time to calculate hits: ',t2-t1
        
        # Sum hits-per-group if not grouping by image
        if group != groupChoices[0]:
            self.SetStatusText('Grouping %s counts by %s...' % (p.object_name[0], group))
            imData = {}
            for row in self.keysAndCounts:
                key = row[:-nClasses]
                imData[key] = numpy.array([float(v) for v in row[-nClasses:]])
            groupedKeysAndCounts = numpy.array([list(k)+vals.tolist() for k, vals in dm.SumToGroup(imData, group).items()], dtype=object)
        else:
            groupedKeysAndCounts = numpy.array(self.keysAndCounts, dtype=object)
        
        
        t3 = time()
        print 'time to group per-image counts:',t3-t2
        
        
        # Calculate alpha
        self.SetStatusText('Fitting beta binomial distribution to data...')
        counts = groupedKeysAndCounts[:,-nClasses:]
        alpha, converged = PolyaFit.fit_betabinom_minka_alternating(counts)
        print '   alpha =', alpha, '   converged =', converged
        print '   alpha/Sum(alpha) = ', [a/sum(alpha) for a in alpha]
        
        t4 = time()
        print 'time to fit beta binomial:',t4-t3
        
        # Flag: positive/negative two-class experiment
        two_classes = len(self.classes) == 2 and \
                      self.classes[0].label.lower() == 'positive' and \
                      self.classes[1].label.lower() == 'negative'
            
        # Construct matrix of table data
        self.SetStatusText('Computing enrichment scores for each group...')
        tableData = []
        fraction = 0.0
        for i, row in enumerate(groupedKeysAndCounts):
            # Update the status text after every 5% is done.
            if float(i)/float(len(groupedKeysAndCounts))-fraction > 0.05:
                fraction = float(i)/float(len(groupedKeysAndCounts))
                self.SetStatusText('Computing enrichment scores for each group... %%%d' %(100*fraction))

            key = tuple(row[:-nClasses])                
            countsRow = [int(v) for v in row[-nClasses:]]
            tableRow = [key]
            tableRow += countsRow
            scores = DirichletIntegrate.score(alpha, numpy.array(countsRow))       # compute enrichment probabilities of each class for this image OR group 
            tableRow += scores
            # Special case: only calculate logit of "positives" for 2-classes
            if two_classes:
                logitscores = [numpy.log(scores[0])-(numpy.log(1-scores[0]))]   # compute logit of each probability
            else:
                logitscores = [numpy.log(score)-(numpy.log(1-score)) for score in scores]   # compute logit of each probability
            tableRow += logitscores
            tableData.append(tableRow)
        tableData = numpy.array(tableData, dtype=object)
        self.SetStatusText('Computing enrichment scores for each group... %100')
        
        t5 = time()
        print 'time to compute enrichment scores:',t5-t4
                
        # Create column labels list
        labels = ['Group Key']
        for i in xrange(nClasses):
            labels.append('Counts\n'+self.classes[i].label)
        for i in xrange(nClasses):
            labels.append('p(Enriched)\n'+self.classes[i].label)
        if two_classes:
            labels.append('Enriched Score\n'+self.classes[0].label)
        else:
            for i in xrange(nClasses):
                labels.append('Enriched Score\n'+self.classes[i].label)
        
        grid = DataGrid(tableData, labels, grouping=group, chMap=self.chMap[:], parent=self, title='Enrichments grouped by '+group)
        grid.Show()
        
        self.SetStatusText('')
        
        
    
    def ComputeLabelMatrix(self):
        '''
        label_matrix is an n by k numpy array containing values of either +1 or -1 indicating class membership
        n = #example objects, k = #classess
        '''
        m = []
        nClasses = len(self.classes)
        for cl in self.classes:
            for obKey in cl.board.GetObjectKeys():
                m.append( [(int(cls.board==cl.board) or -1) for cls in self.classes] )
        return numpy.array(m)
    
    
    
    def LoadProperties(self):
        dlg = wx.FileDialog(self, "Select a the file containing your properties.", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            
            p.LoadFile(filename)
            db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
            dm.PopulateModel()
            
            
    
    def OnClose(self, evt):
        if self.trainingSet and self.trainingSet.saved == False:
            dlg = wx.MessageDialog(self, 'Do you want to save your training set before quitting?', 'Training Set Not Saved', wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.SaveTrainingSet()
            elif response == wx.ID_CANCEL:
                return
        self.Destroy()
        
        

        
        
# ----------------- Testing -------------------

if __name__ == "__main__":
    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()
    
    import sys
    
    # Handles args to MacOS "Apps"
    if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
        del sys.argv[1]

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
        db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
        dm.PopulateModel()
#    else:
#        propsFile = '../properties/2008_07_22_HSC_Alison_Stewart_fixed.properties'
#        # propsFile = '/Users/thouis/CPAnalyst/pyCPAnalyst/CPA/properties/nirht_test.properties' 
#        print 'No properties file given. Using "'+propsFile+'"'
#        p.LoadFile(propsFile)

    
    app = wx.PySimpleApp()
    classifier = ClassifierGUI(None)
    classifier.Show(True)
    app.MainLoop()
