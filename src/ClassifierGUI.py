'''
Classifier.py
Authors: afraser
'''
import ImageTools

import os
import wx
import wx.grid
import numpy
from cStringIO import StringIO

from DataModel import DataModel
from DBConnect import DBConnect
from Properties import Properties

from SortBin import SortBin
from ImageTile import ImageTile
from ImageControlPanel import ImageControlPanel
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
    def __init__(self, label, bin, sizer, trained=False):
        self.label = label
        self.bin = bin
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
        self.brightness = 1.0
        self.scale = 1.0
        self.defaultTSFileName = None
        
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateFileMenu()
        self.CreateChannelMenus()
        self.DisplayMenu = wx.Menu()
        self.imageControlsMenuItem = wx.MenuItem(parentMenu=self.DisplayMenu, id=wx.NewId(), text='Image Controls', help='Launches a control panel for adjusting image brightness, size, etc.')
        self.DisplayMenu.AppendItem(self.imageControlsMenuItem)
        self.GetMenuBar().Append(self.DisplayMenu, 'Display')

        self.CreateStatusBar()
        
        # Create the Fetch panel
        self.fetchSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Fetch '+p.object_name[1]),wx.HORIZONTAL)
        self.nObjectsTxt = wx.TextCtrl(self, id=wx.NewId(), value='20', size=(30,-1))
        self.obClassChoice = wx.Choice(self, id=wx.NewId(), choices=['random'])
        self.obClassChoice.SetSelection(0)
        filters = []
        if p.filters:
            filters = p.filters
        self.filterChoice = wx.Choice(self, id=wx.NewId(), choices=['experiment', 'image']+filters)
        self.filterChoice.SetSelection(0)
        self.imageTxt = wx.TextCtrl(self, id=wx.NewId(), value='1', size=(30,-1))
        if p.table_id:
            self.tableStaticTxt = wx.StaticText(self, wx.NewId(), 'in table #')
            self.tableTxt = wx.TextCtrl(self, id=wx.NewId(), value='0', size=(30,-1))
            self.tableTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
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
        self.fetchFromImageSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetchFromImageSizer.Add(self.imageTxt)
        self.fetchFromImageSizer.AddSpacer((10,20))
        if p.table_id:
            self.fetchFromImageSizer.Add(self.tableStaticTxt)
            self.fetchFromImageSizer.AddSpacer((10,20))
            self.fetchFromImageSizer.Add(self.tableTxt)
            self.fetchFromImageSizer.AddSpacer((10,20))
        self.fetchSizer.AddSizer(self.fetchFromImageSizer)
        self.fetchSizer.Hide(self.fetchFromImageSizer, True)
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
        self.scoreImageBtn = wx.Button(self, wx.NewId(), 'Score Image')
        self.scoreImageBtn.Disable()
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
        self.trainSizer2.Add(self.scoreImageBtn)
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
        self.unclassifiedBin = SortBin(parent=self.topSortPanel, classifier=self, label='unclassified')
        self.topSortSizer.Add( self.unclassifiedBin, proportion=1, flag=wx.EXPAND )
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
        self.Bind(wx.EVT_MENU, self.OnShowImageControls, self.imageControlsMenuItem)
        self.Bind(wx.EVT_CHOICE, self.OnSelectFilter, self.filterChoice)
        self.Bind(wx.EVT_MENU, self.OnLoadTrainingSet, self.loadTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveTrainingSet, self.saveTSMenuItem)
        self.Bind(wx.EVT_BUTTON, self.OnFetch, self.fetchBtn)
        self.Bind(wx.EVT_BUTTON, self.OnAddSortClass, self.addSortClassBtn)
        self.Bind(wx.EVT_BUTTON, self.OnFindRules, self.findRulesBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreAll, self.scoreAllBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreImage, self.scoreImageBtn)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.CancelCapture)
        self.nObjectsTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.nRulesTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.imageTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.imageTxt.Bind(wx.EVT_TEXT, self.ValidateImageKey)
        if p.table_id:
            self.tableTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
            self.tableTxt.Bind(wx.EVT_TEXT, self.ValidateImageKey)
        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnDragSash)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MENU, self.OnClose, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)    
        self.Bind(wx.EVT_CHAR, self.OnKey)    
        
        EVT_IMAGE_RESULT(self, self.OnImageResult)
        

    
    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
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
        ''' Create a new SortBin in a new StaticBoxSizer with the given label.
        This sizer is then added to the bottomSortSizer. '''
        sizer = wx.StaticBoxSizer(wx.StaticBox(self.bottomSortPanel, label=label), wx.VERTICAL)
        bin = SortBin(parent=self.bottomSortPanel, label=label, classifier=self)             # NOTE: bin must be created after sizer or drops events will occur on the sizer
        sizer.Add(bin, proportion=1, flag=wx.EXPAND)
        self.bottomSortSizer.Add(sizer, proportion=1, flag=wx.EXPAND)
        self.classes.append( SortClass(label,bin,sizer) )
        self.bottomSortPanel.Layout()
        self.binsCreated += 1
        
    
    def RemoveSortClass(self, label):
        for cl in self.classes:
            if cl.label == label:
                # Remove the bin
                self.bottomSortSizer.Remove(cl.sizer)
                #cl.bin.Clear()
                cl.bin.Destroy()
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
                    cl.bin.label = newLabel
                    break
            dlg.Destroy()
        self.UpdateBinLabels()
        
        updatedList = self.obClassChoice.GetItems()
        sel = self.obClassChoice.GetSelection()
        for i in xrange(len(updatedList)):
            if updatedList[i] == label:
                updatedList[i] = newLabel
        self.obClassChoice.SetItems(updatedList)
        self.obClassChoice.SetSelection(sel)
        
    

    def all_sort_bins(self):
        return [self.unclassifiedBin] + [c.bin for c in self.classes]


    def OnLeftUp(self, evt):
        drag = DragObject.getInstance()
        if drag.IsEmpty():
            self.ReleaseMouse()
            return

        drop_target = None
        mouse_screen_pos = self.ClientToScreen(evt.GetPosition())
        for bin in self.all_sort_bins():
            if bin.GetScreenRect().Contains(mouse_screen_pos):
                drop_target = bin

        if drop_target and drag.source != drop_target:
            if isinstance(drop_target, DropTarget):
                drop_target.ReceiveDrop(drag)
                if not self.trainingSet:
                    self.trainingSet = TrainingSet(p)
                    self.trainingSet.Create([], [])
            self.UpdateBinLabels()

        drag.Empty()
        self.ReleaseMouse()
        #wx.SetCursor(wx.NullCursor)


    def CancelCapture(self, evt):
        DragObject.getInstance().Empty()

        
    def UpdateBinLabels(self):
        self.findRulesBtn.Disable()
        ts = False
        self.topSortSizer.GetStaticBox().SetLabel( 'unclassified '+p.object_name[1]+' ('+str(len(self.unclassifiedBin.tiles))+')' )
        for cl in self.classes:
            cl.sizer.GetStaticBox().SetLabel( cl.label+' ('+str(len(cl.bin.tiles))+')')
            if len(cl.bin.tiles) > 0:
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
            elif filter =='image':
                if p.table_id:
                    imKey = (int(self.tableTxt.Value), int(self.imageTxt.Value))
                else:
                    imKey = (int(self.imageTxt.Value),)
                obKeys = dm.GetObjectsFromImage(imKey)
                statusMsg += ' from image '+str(imKey)
            else:
                imKeysInFilter = db.GetFilteredImages(filter)
                obKeys = dm.GetRandomObjects(nObjects, imKeysInFilter)
                statusMsg += ' from filter "'+filter+'"...'
        # classified
        else:
            hits = 0
            obKeys = []
            
            if filter != 'experiment':
                if filter =='image':
                    if p.table_id:
                        imKey = (int(self.tableTxt.Value), int(self.imageTxt.Value))
                    else:
                        imKey = (int(self.imageTxt.Value),)
                    imKeysInFilter = [imKey]
                else:    
                    imKeysInFilter = db.GetFilteredImages(filter)
            
            attempts = 0
            while len(obKeys) < nObjects:
                if filter == 'experiment':
                    obKeysToTry = dm.GetRandomObjects(100)
                    loopMsg = ' in class "'+obClassName+'" from whole experiment... '
                elif filter == 'image':
                    obKeysToTry = dm.GetObjectsFromImage(imKey)
                    loopMsg = ' in class "'+obClassName+'" from image '+str(imKey)    
                else:
                    obKeysToTry = dm.GetRandomObjects(100,imKeysInFilter)
                    loopMsg = ' in class "'+obClassName+'" from filter "'+filter+'"...'
                stump_query, score_query, find_max_query, class_query, count_query = MulticlassSQL.translate(self.weaklearners, self.trainingSet.colnames)
                obKeys += MulticlassSQL.FilterObjectsFromClassN(obClass, obKeysToTry, stump_query, score_query, find_max_query)

                attempts += 100
                if attempts%10000.0==0:
                    dlg = wx.MessageDialog(self, 'Found '+str(len(obKeys))+' '+p.object_name[1]+' after '+str(attempts)+' attempts. Continue searching?',
                                           'Continue searching?', wx.YES_NO|wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    if response == wx.ID_NO:
                        break

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
            tile = ImageTile(self.unclassifiedBin, obKey=evt.data[0], images=evt.data[1], chMap=self.chMap, selected=False, scale=self.scale, brightness=self.brightness)
            self.unclassifiedBin.AddTile(tile, pos='last')
            self.topSortSizer.GetStaticBox().SetLabel( 'unclassified '+p.object_name[1]+' ('+str(len(self.unclassifiedBin.tiles))+')' )
        
        
    def OnLoadTrainingSet(self, evt):
        self.LoadTrainingSet()
        
    def LoadTrainingSet(self):
        ''' Presents the user with a file select dialog. 
        Loads the selected file, parses out object keys, and fetches the tiles. '''
        dlg = wx.FileDialog(self, "Select a the file containing your classifier training set.", defaultDir=os.getcwd(), style=wx.OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            
            self.SetStatusText('Loading training set from: '+filename)
            os.chdir(os.path.split(filename)[0])                       # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
            self.defaultTSFileName = os.path.split(filename)[1]
            
            self.trainingSet = TrainingSet(p, filename)
            
            self.RemoveAllSortClasses()
            for label in self.trainingSet.labels:
                self.AddSortClass(label)
            for (label, key) in self.trainingSet.entries:
                for cl in self.classes:
                    if cl.label == label:
                        cl.bin.AddObject(key, self.chMap[:], refresh=False)
                        break
            for cl in self.classes:
                cl.bin.Refresh()
                cl.bin.Layout()
        self.UpdateBinLabels()
        self.SetStatusText('Training set loaded.')
        
    
    def OnSaveTrainingSet(self, evt):
        self.SaveTrainingSet()
        
    def SaveTrainingSet(self):
        if not self.defaultTSFileName:
            self.defaultTSFileName = 'MyTrainingSet.txt'
        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(), defaultFile=self.defaultTSFileName, wildcard='txt', style=wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal()==wx.ID_OK:
            filename = saveDialog.GetPath()
            os.chdir(os.path.split(filename)[0])                 # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
            self.defaultTSFileName = os.path.split(filename)[1]
            self.SaveTrainingSetAs(filename)

    
    def SaveTrainingSetAs(self, filename):
        classDict = {}
        self.trainingSet = TrainingSet(p)
        self.trainingSet.Create([cl.label for cl in self.classes], [cl.bin.GetObjectKeys() for cl in self.classes])
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
        
        self.unclassifiedBin.MapChannels(chMap)
        for cl in self.classes:
            cl.bin.MapChannels(chMap)
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
                self.SetStatusText('Image contains %s %s.'%(dm.GetObjectCountFromImage(imKey),p.object_name[1]))
            else:
                txtCtrl.SetForegroundColour('#888888')   # Set field to GRAY if image contains no objects
                self.SetStatusText('Image contains zero %s.'%(p.object_name[1]))
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')       # Set field to red if image doesn't exist
            self.SetStatusText('No such image.')
          
    
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
        self.trainingSet.Create([cl.label for cl in self.classes], [cl.bin.GetObjectKeys() for cl in self.classes])
        labelMatrix = self.ComputeLabelMatrix()
        output = StringIO()
        self.SetStatusText('Training classifier with '+str(nRules)+' rules...')
        self.weaklearners = FastGentleBoostingMulticlass.train(self.trainingSet.colnames, nRules, labelMatrix, self.trainingSet.values, output)
        self.SetStatusText('')
        self.rulesTxt.Value = output.getvalue()
        self.scoreAllBtn.Enable()
        self.scoreImageBtn.Enable()

        for cl in self.classes:
            if len(cl.bin.tiles) > 0:
                cl.trained = True
            else:
                cl.trained = False
        self.UpdateClassChoices()
        
        
    def OnScoreImage(self, evt):
        # 1) Get the image key
        # Start with the table_id if there is one
        tblNum = None
        if p.table_id:
            dlg = wx.TextEntryDialog(self, p.table_id+':','Enter '+p.table_id)
            dlg.SetValue('0')
            if dlg.ShowModal() == wx.ID_OK:
                tblNum = int(dlg.GetValue())
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
        # Then get the image_id
        dlg = wx.TextEntryDialog(self, p.image_id+':','Enter '+p.image_id)
        dlg.SetValue('1')
        if dlg.ShowModal() == wx.ID_OK:
            imgNum = int(dlg.GetValue())
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        # Build the imKey
        if p.table_id:
            imKey = (tblNum,imgNum)
        else:
            imKey = (imgNum,)
           
        # 2) Get the phenotype to highlight:
        dlg = wx.SingleChoiceDialog(self, 'Select a class to highlight:', 'Choose Class', [cl.label for cl in self.classes], wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:            
            cls   = str(dlg.GetStringSelection())  # class name to print in feedback
            clNum = dlg.GetSelection() + 1         # class index to pass to the classifier
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
    
        # 3) Find the hits
        stump_query, score_query, find_max_query, class_query, count_query = MulticlassSQL.translate(self.weaklearners, self.trainingSet.colnames, [imKey])
        obKeys = dm.GetObjectsFromImage(imKey)
        hits = []
        if obKeys:
            hits = MulticlassSQL.FilterObjectsFromClassN(clNum, obKeys, stump_query, score_query, find_max_query)
        self.SetStatusText('%s of %s %s classified as %s in image %s'%(len(hits), len(obKeys), p.object_name[1], cls, imKey))
        
        # 4) Get object coordinates in image and display
        coordList = []
        for obKey in hits:
            coordList += [db.GetObjectCoords(obKey)]
        imViewer = ImageTools.ShowImage(imKey, self.chMap, self)
        imViewer.imagePanel.SelectPoints(coordList)
        
        
        
    def OnScoreAll(self, evt):
        groupChoices = ['Image']
        if p.groups is not None:
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
                
        nClasses = len(self.classes)
        
        # Check if hit counts have already been calculated (since last training)
        # If not: Classify all objects into phenotype classes and count phenotype-hits per-image
        if self.keysAndCounts == None:
            stump_query, score_query, find_max_query, class_query, count_query = MulticlassSQL.translate(self.weaklearners, self.trainingSet.colnames, p.area_scoring_column)
            self.SetStatusText('Calculating %s counts for each class...' % p.object_name[0])
            self.keysAndCounts = MulticlassSQL.HitsAndCounts(stump_query, score_query, find_max_query, class_query, count_query)

            # Add in images with zero object count
            for imKey, obCount in dm.GetImageKeysAndObjectCounts():
                if obCount == 0:
                    self.keysAndCounts += [list(imKey) + [0 for c in range(nClasses)]]
                
        t2 = time()
        print 'time to calculate hits: ',t2-t1
        
        # Sum hits-per-group if not grouping by image
        if group != groupChoices[0]:
            self.SetStatusText('Grouping %s counts by %s...' % (p.object_name[0], group))
            imData = {}
            for row in self.keysAndCounts:
                key = tuple(row[:-nClasses])
                imData[key] = numpy.array([float(v) for v in row[-nClasses:]])
            groupedKeysAndCounts = numpy.array([list(k)+vals.tolist() for k, vals in dm.SumToGroup(imData, group).items()], dtype=object)
        else:
            groupedKeysAndCounts = numpy.array(self.keysAndCounts, dtype=object)
        
        t3 = time()
        print 'time to group per-image counts:',t3-t2
        
        # TODO: validate that this works as expected
        #       display results in a table?
        zprimes = self.CalculateZPrimes(groupedKeysAndCounts.copy(), nClasses)
        
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
                self.SetStatusText('Computing enrichment scores for each group... %d%%' %(100*fraction))
            
            # Start this row with the group key: 
            tableRow = list(row[:-nClasses])
            # Append the counts:
            countsRow = [int(v) for v in row[-nClasses:]]
            tableRow += countsRow 
            # Append the scores:
            scores = DirichletIntegrate.score(alpha, numpy.array(countsRow))       # compute enrichment probabilities of each class for this image OR group 
            tableRow += scores
            # Append the logit scores:
            # Special case: only calculate logit of "positives" for 2-classes
            if two_classes:
                tableRow += [numpy.log10(scores[0])-(numpy.log10(1-scores[0]))]   # compute logit of each probability
            else:
                tableRow += [numpy.log10(score)-(numpy.log10(1-score)) for score in scores]   # compute logit of each probability
            tableData.append(tableRow)
        tableData = numpy.array(tableData, dtype=object)
        self.SetStatusText('Computing enrichment scores for each group... 100%')
        
        t5 = time()
        print 'time to compute enrichment scores:',t5-t4
                
        # Create column labels list
        labels = []
        # if grouping isn't per-image, then get the group key column names.
        if group != groupChoices[0]:
            labels = dm.GetGroupColumnNames(group)
        elif p.table_id:
            labels += [p.table_id, p.image_id]
        else:
            labels += [p.image_id]
            
        groupIDIndices = [i for i in range(len(labels))]
            
        for i in xrange(nClasses):
            if p.area_scoring_column is None:
                labels += ['Counts\n'+self.classes[i].label]
            else:
                labels += ['Area Sums\n'+self.classes[i].label]
        for i in xrange(nClasses):
            labels += ['p(Enriched)\n'+self.classes[i].label]
        if two_classes:
            labels += ['Enriched Score\n'+self.classes[0].label]
        else:
            for i in xrange(nClasses):
                labels += ['Enriched Score\n'+self.classes[i].label]
        
        grid = DataGrid(tableData, labels, grouping=group, groupIDIndices=groupIDIndices,
                        chMap=self.chMap[:], parent=self, title='Enrichments grouped by '+group)
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
            for obKey in cl.bin.GetObjectKeys():
                m.append( [(int(cls.bin==cl.bin) or -1) for cls in self.classes] )
        return numpy.array(m)
    
    
    
    def CalculateZPrimes(self, keysAndCounts, nClasses):
        '''
        Calculates Z' factor as 1-3*(Sp+Sn)/|Mp-Mn|
        This is done for each class against all other classes combined.
        keysAndCounts: A numpy.array([[key, nX, nY, nZ...], where nX, nY, nZ
                       are the object counts for classes X,Y,Z...
        nClasses: The number of classes
        Returns: A list of Z' factors for each class in the order they came in.
        '''
        firstClassIdx = len(keysAndCounts[0])-nClasses
        counts = keysAndCounts[:,firstClassIdx:].astype('float')
        result = []
        for i in range(nClasses):
            ingroup = counts[:,i]
            outgroup = numpy.hstack([counts[:,j] for j in range(nClasses) if j!=i])
            ssd = ingroup.std() + outgroup.std()
            r = abs(ingroup.mean() - outgroup.mean())
            result += [1-3*ssd/r]
            
        print "Z' factors =", result
        
        return result
        
    
    
    def LoadProperties(self):
        dlg = wx.FileDialog(self, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            p.LoadFile(filename)
            db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
            dm.PopulateModel()
        else:
            print 'Classifier requires a properties file.  Exiting.'
            exit()
            
            
            
    def OnSelectFilter(self, evt):
        # Select from a specific image
        if evt.Selection == 1:
            self.fetchSizer.Show(self.fetchFromImageSizer, True)
        else:
            self.fetchSizer.Hide(self.fetchFromImageSizer, True)
        self.Layout()
        

    def OnShowImageControls(self, evt):
        self.imageControlFrame = wx.Frame(self)
        ImageControlPanel(self.imageControlFrame, self, brightness=self.brightness, scale=self.scale)
        self.imageControlFrame.Show(True)
        
        
    def SetBrightness(self, brightness):
        self.brightness = brightness
        [t.SetBrightness(brightness) for t in self.unclassifiedBin.tiles] 
        [t.SetBrightness(brightness) for cl in self.classes for t in cl.bin.tiles]
        

    def SetScale(self, scale):
        self.scale = scale
        panels = ([t for t in self.unclassifiedBin.tiles] + 
                  [t for cl in self.classes for t in cl.bin.tiles])
        
        for p in panels:
            p.SetScale(scale)
        # Layout the bins
        self.unclassifiedBin.Layout()
        for cl in self.classes:
            cl.bin.Layout()
        

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
    
    app = wx.PySimpleApp()
    classifier = ClassifierGUI(None)
    classifier.Show(True)
    app.MainLoop()
