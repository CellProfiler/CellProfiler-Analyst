from DBConnect import DBConnect
from DataGrid import DataGrid
from DataModel import DataModel
from ImageControlPanel import ImageControlPanel
from Properties import Properties
from ScoreDialog import ScoreDialog
import SortBin
from TileCollection import EVT_TILE_UPDATED
from TrainingSet import TrainingSet
from cStringIO import StringIO
import DirichletIntegrate
import FastGentleBoostingMulticlass
import ImageTools
import MulticlassSQL
import PolyaFit
import numpy
import os
import wx


class ClassifierGUI(wx.Frame):

    """GUI Interface and functionality for the Classifier."""

    def __init__(self, parent):
        
        if p.IsEmpty():
            print 'Classifier requires a properties file. Exiting.'
            exit()

        if DataModel.getInstance().IsEmpty():
            print "DataModel is empty. Classifier requires a populated DataModel to function. Exiting."
            exit()

        wx.Frame.__init__(self, parent, id=-1, title='Classifier 2.0 - %s'%(p.filename), size=(800,600))
                
        self.worker = None
        self.weaklearners = None
        self.trainingSet = None
        self.classBins = []
        self.binsCreated = 0
        self.chMap = p.image_channel_colors[:]
        self.toggleChMap = p.image_channel_colors[:] # used to store previous color mappings when toggling colors on/off with ctrl+1,2,3...
        self.brightness = 1.0
        self.scale = 1.0
        self.defaultTSFileName = None
        self.lastScoringFilter = None
        
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateFileMenu()
        self.CreateChannelMenus()
        
        # Image Controls Menu
        displayMenu = wx.Menu()
        imageControlsMenuItem = wx.MenuItem(parentMenu=displayMenu,
                                            id=wx.NewId(), text='Image Controls', 
                                            help='Launches a control panel for adjusting image brightness, size, etc.')
        displayMenu.AppendItem(imageControlsMenuItem)
        self.GetMenuBar().Append(displayMenu, 'Display')
        # Help Menu
        helpMenu = wx.Menu()
        helpMenuItem = wx.MenuItem(parentMenu=helpMenu,
                                   id=wx.NewId(), text='Readme',
                                   help='Displays the readme file.')
        helpMenu.AppendItem(helpMenuItem)
        self.GetMenuBar().Append(helpMenu, 'Help')

        self.CreateStatusBar()
        
        # Create the Fetch panel
        self.fetchSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Fetch '+p.object_name[1]),wx.HORIZONTAL)
        self.nObjectsTxt = wx.TextCtrl(self, id=wx.NewId(), value='20', size=(30,-1))
        self.obClassChoice = wx.Choice(self, id=wx.NewId(), choices=['random'])
        self.obClassChoice.SetSelection(0)
        filters = p.filters_ordered
        groups = p.groups_ordered
        self.filterChoice = wx.Choice(self, id=wx.NewId(), choices=['experiment', 'image']+filters+groups)
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
        self.fetchFromGroupSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetchSizer.AddSizer(self.fetchFromGroupSizer)
        self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
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
        self.topSortSizer = wx.StaticBoxSizer(wx.StaticBox(self.topSortPanel, 
                                                           label='unclassified '+p.object_name[1]))
        self.topSortPanel.SetSizer(self.topSortSizer)
        self.unclassifiedBin = SortBin.SortBin(parent=self.topSortPanel, 
                                               classifier=self,
                                               label='unclassified', 
                                               parentSizer=self.topSortSizer)
        self.topSortSizer.Add(self.unclassifiedBin, proportion=1, flag=wx.EXPAND)
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
        
        self.Centre()
        self.MapChannels(p.image_channel_colors[:])
        self.BindMouseOverHelpText()

        # do event binding
        self.Bind(wx.EVT_MENU, self.OnShowImageControls, imageControlsMenuItem)
        self.Bind(wx.EVT_MENU, self.OnShowReadme, helpMenuItem)
        self.Bind(wx.EVT_CHOICE, self.OnSelectFilter, self.filterChoice)
        self.Bind(wx.EVT_MENU, self.OnLoadTrainingSet, self.loadTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveTrainingSet, self.saveTSMenuItem)
        self.Bind(wx.EVT_BUTTON, self.OnFetch, self.fetchBtn)
        self.Bind(wx.EVT_BUTTON, self.OnAddSortClass, self.addSortClassBtn)
        self.Bind(wx.EVT_BUTTON, self.OnFindRules, self.findRulesBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreAll, self.scoreAllBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreImage, self.scoreImageBtn)
        self.nObjectsTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.nRulesTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnDragSash)
        self.Bind(wx.EVT_MENU, self.OnClose, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
#        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)  # TODO: why doesn't this work!?
        self.Bind(wx.EVT_CHAR, self.OnKey)     # Doesn't work for windows
        EVT_TILE_UPDATED(self, self.OnTileUpdated)
        self.Bind(SortBin.EVT_QUANTITY_CHANGED, self.OnQuantityChanged)
        
        # If there's a default training set. Ask to load it.
        if p.training_set and os.access(p.training_set, os.R_OK):
            # file existence is checked in Properties module
            dlg = wx.MessageDialog(self, 'Would you like to load the training set defined in your properties file?\n\n%s\n\nTo prevent this message from appearing. Remove the training_set field from your properties file.'%(p.training_set),
                                   'Load Default Training Set?', wx.YES_NO|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.LoadTrainingSet(p.training_set)


    def BindMouseOverHelpText(self):
        self.nObjectsTxt.SetToolTip(wx.ToolTip('The number of %s to fetch.'%(p.object_name[1])))
        self.obClassChoice.SetToolTip(wx.ToolTip('The phenotype of the %s.'%(p.object_name[1])))
        self.obClassChoice.GetToolTip().SetDelay(3000)
        self.filterChoice.SetToolTip(wx.ToolTip('Image filters allow you to find %s from a subset of your images. (See groups and filters in the properties file)'%(p.object_name[1])))
        self.filterChoice.GetToolTip().SetDelay(3000)
        self.fetchBtn.SetToolTip(wx.ToolTip('Fetches images of %s to be sorted.'%(p.object_name[1])))
        self.rulesTxt.SetToolTip(wx.ToolTip('Rules are displayed in this text box.'))
        self.nRulesTxt.SetToolTip(wx.ToolTip('The maximum number of rules classifier should use to define your phenotypes.'))
        self.findRulesBtn.SetToolTip(wx.ToolTip('Tell Classifier to find a rule set that fits your phenotypes as you have sorted them.'))
        self.scoreAllBtn.SetToolTip(wx.ToolTip('Compute %s counts and per-group enrichments across your experiment. (This may take a while)'%(p.object_name[0])))
        self.scoreImageBtn.SetToolTip(wx.ToolTip('Highlight %s of a particular phenotype in an image.'%(p.object_name[1])))
        self.addSortClassBtn.SetToolTip(wx.ToolTip('Add another bin to sort your %s into.'%(p.object_name[1])))
        self.unclassifiedBin.SetToolTip(wx.ToolTip('%s in this bin should be sorted into the bins below.'%(p.object_name[1].capitalize())))

    
    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        keycode = evt.GetKeyCode()
        chIdx = keycode-49
        if evt.ControlDown() or evt.CmdDown():
            # load training set
            if keycode == ord('o'):
                self.OnLoadTrainingSet(evt)
            # save training set
            elif keycode == ord('s'):
                self.OnSaveTrainingSet(evt)
            # ctrl+N toggles channel #N on/off
            elif len(self.chMap) > chIdx >= 0:
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
        self.loadTSMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='Load training set', help='Loads objects and classes specified in a training set file.')
        self.saveTSMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='Save training set', help='Save your training set to file so you can reload these classified cells again.')
        self.exitMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.wx.NewId(), text='Exit', help='Exit classifier')
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
            # Separators screw up selection
            #channel_menu.InsertSeparator(3)
            #channel_menu.InsertSeparator(8)
            self.GetMenuBar().Append(channel_menu, channel)
            chIndex+=1

        
    def AddSortClass(self, label):
        ''' Create a new SortBin in a new StaticBoxSizer with the given label.
        This sizer is then added to the bottomSortSizer. '''
        sizer = wx.StaticBoxSizer(wx.StaticBox(self.bottomSortPanel, label=label), wx.VERTICAL)
        # NOTE: bin must be created after sizer or drop events will occur on the sizer
        bin = SortBin.SortBin(parent=self.bottomSortPanel, label=label, 
                              classifier=self, parentSizer=sizer)
        sizer.Add(bin, proportion=1, flag=wx.EXPAND)
        self.bottomSortSizer.Add(sizer, proportion=1, flag=wx.EXPAND)
        self.classBins.append(bin)
        self.bottomSortPanel.Layout()
        self.binsCreated += 1
        
    
    def RemoveSortClass(self, label):
        for bin in self.classBins:
            if bin.label == label:
                self.classBins.remove(bin)
                # Remove the label from the class dropdown menu
                self.obClassChoice.SetItems([item for item in self.obClassChoice.GetItems() if item!=bin.label])
                self.obClassChoice.Select(0)
                # Remove the bin
                self.bottomSortSizer.Remove(bin.parentSizer)
                bin.Destroy()
                self.bottomSortPanel.Layout()
                break
        self.weaklearners = None
        self.rulesTxt.SetValue('')
        for bin in self.classBins:
            bin.trained = False
        self.UpdateClassChoices()
        
        
    def RemoveAllSortClasses(self):
        # Note: can't use "for bin in self.classBins:"
        for label in [bin.label for bin in self.classBins]:
            self.RemoveSortClass(label)
            
    
    def RenameClass(self, label):
        dlg = wx.TextEntryDialog(self, 'New class name:','Rename class')
        dlg.SetValue(label)
        if dlg.ShowModal() == wx.ID_OK:
            newLabel = dlg.GetValue()
            if newLabel != label and newLabel in [bin.label for bin in self.classBins]:
                errdlg = wx.MessageDialog(self, 'There is already a class with that name.', "Can't Name Class", wx.OK|wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    self.RenameClass(label)
                    return
            if ' ' in newLabel:
                errdlg = wx.MessageDialog(self, 'Labels can not contain spaces', "Can't Name Class", wx.OK|wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    self.RenameClass(label)
                    return
            for bin in self.classBins:
                if bin.label == label:
                    bin.label = newLabel
                    bin.UpdateQuantity()
                    break
            dlg.Destroy()
        
        updatedList = self.obClassChoice.GetItems()
        sel = self.obClassChoice.GetSelection()
        for i in xrange(len(updatedList)):
            if updatedList[i] == label:
                updatedList[i] = newLabel
        self.obClassChoice.SetItems(updatedList)
        self.obClassChoice.SetSelection(sel)
    

    def all_sort_bins(self):
        return [self.unclassifiedBin] + self.classBins
                
    
    def UpdateClassChoices(self):
        if not self.weaklearners:
            self.obClassChoice.SetItems(['random'])
            self.obClassChoice.SetSelection(0)
            return
        sel = self.obClassChoice.GetSelection()
        selectableClasses = ['random']+[bin.label for bin in self.classBins if bin.trained]
        self.obClassChoice.SetItems(selectableClasses)
        if len(selectableClasses) < sel:
            sel=0
        self.obClassChoice.SetSelection(sel)
        
    def OnQuantityChanged(self, event):
        """The number of tiles in one of the SortBins has changed.  Go
        through them all.  Disable the button for finding rules if any
        SortBin is empty."""
        self.findRulesBtn.Disable()
        for bin in self.classBins:
            if not bin.empty:
                self.findRulesBtn.Enable()
    
    def OnFetch(self, evt):
        # Parse out the GUI input values        
        nObjects    = int(self.nObjectsTxt.Value)
        obClass     = self.obClassChoice.Selection
        obClassName = self.obClassChoice.GetStringSelection()
        filter      = self.filterChoice.GetStringSelection()
        
        statusMsg = 'fetching %d %s %s'%(nObjects, obClassName, p.object_name[1])
        
        # Get object keys
        # unclassified:
        if obClass == 0:
            if filter == 'experiment':
                obKeys = dm.GetRandomObjects(nObjects)
                statusMsg += ' from whole experiment'
            elif filter == 'image':
                imKey = self.GetGroupKeyFromGroupSizer()
                obKeys = dm.GetRandomObjects(nObjects, [imKey])
                statusMsg += ' from image %s'%(imKey,)
            elif filter in p.filters_ordered:
                filteredImKeys = db.GetFilteredImages(filter)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in filter "%s"'%(filter))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys)
                statusMsg += ' from filter "%s"'%(filter)
            elif filter in p.groups_ordered:
                # if the filter name is a group then it's actually a group
                groupName = filter
                groupKey = self.GetGroupKeyFromGroupSizer()
                filteredImKeys = dm.GetImagesInGroup(groupName, groupKey)
                colNames = dm.GetGroupColumnNames(groupName)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in group %s: %s'%(groupName, 
                                        ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)])))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys)
                if not obKeys:
                    self.PostMessage('The images in this group are empty. Group %s: %s'%(groupName, 
                                        ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)])))
                    return
                statusMsg += ' from group %s: %s'%(groupName,
                                        ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)]))
                    
        # classified
        else:
            hits = 0
            obKeys = []
            # Get images within any selected filter or group
            if filter != 'experiment':
                if filter == 'image':
                    imKey = self.GetGroupKeyFromGroupSizer()
                    filteredImKeys = [imKey]
                elif filter in p.filters_ordered:
                    filteredImKeys = db.GetFilteredImages(filter)
                    if filteredImKeys == []:
                        self.PostMessage('No images were found in filter "%s"'%(filter))
                        return
                elif filter in p.groups_ordered:
                    groupKey = self.GetGroupKeyFromGroupSizer()
                    colNames = dm.GetGroupColumnNames(filter)
                    filteredImKeys = dm.GetImagesInGroup(filter, groupKey)
                    if filteredImKeys == []:
                        self.PostMessage('No images were found in group %s: %s'%(filter,
                                            ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)])))
                        return
                    
            attempts = 0
            while len(obKeys) < nObjects:
                if filter == 'experiment':
                    obKeysToTry = dm.GetRandomObjects(100)
                    loopMsg = ' from whole experiment'
                elif filter == 'image':
                    # All objects are tried in first pass
                    if attempts>0: break
                    imKey = self.GetGroupKeyFromGroupSizer()
                    obKeysToTry = dm.GetObjectsFromImage(imKey)
                    loopMsg = ' from image %s'%(imKey,)
                else:
                    obKeysToTry = dm.GetRandomObjects(100, filteredImKeys)
                    if filter in p.filters_ordered:
                        loopMsg = ' from filter %s'%(filter)
                    elif filter in p.groups_ordered:
                        loopMsg = ' from group %s: %s'%(filter,
                                            ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)]))
                obKeys += MulticlassSQL.FilterObjectsFromClassN(obClass, self.weaklearners, obKeysToTry)
                attempts += len(obKeysToTry)
                if attempts%10000.0==0:
                    dlg = wx.MessageDialog(self, 'Found %d %s after %d attempts. Continue searching?'
                                           %(len(obKeys), p.object_name[1], attempts), 
                                           'Continue searching?', wx.YES_NO|wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    if response == wx.ID_NO:
                        break
            statusMsg += loopMsg
            
        self.PostMessage(statusMsg)
        self.unclassifiedBin.AddObjects(obKeys[:nObjects], self.chMap, pos='last')
        
    

    def OnTileUpdated(self, evt):
        self.unclassifiedBin.UpdateTile(evt.data)
        for bin in self.classBins:
            bin.UpdateTile(evt.data)
        
        
    def OnLoadTrainingSet(self, evt):
        ''' Present user with file select dialog, then load selected training set. '''
        dlg = wx.FileDialog(self, "Select a the file containing your classifier training set.",
                            defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadTrainingSet(filename)
        
    def LoadTrainingSet(self, filename):
        ''' Loads the selected file, parses out object keys, and fetches the tiles. '''        
        self.PostMessage('Loading training set from: '+filename)
        # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        os.chdir(os.path.split(filename)[0])
        self.defaultTSFileName = os.path.split(filename)[1]
        
        self.trainingSet = TrainingSet(p, filename)
        
        self.RemoveAllSortClasses()
        for label in self.trainingSet.labels:
            self.AddSortClass(label)
            
        keysPerBin = {}
        for (label, key) in self.trainingSet.entries:
            if label in keysPerBin.keys():
                keysPerBin[label] += [key]
            else:
                keysPerBin[label] = [key]
        for bin in self.classBins:
            if bin.label in keysPerBin.keys():
                bin.AddObjects(keysPerBin[bin.label], self.chMap, priority=2)
                
        self.PostMessage('Training set loaded.')
        
    
    def OnSaveTrainingSet(self, evt):
        self.SaveTrainingSet()
        
    def SaveTrainingSet(self):
        if not self.defaultTSFileName:
            self.defaultTSFileName = 'MyTrainingSet.txt'
        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(), 
                                   defaultFile=self.defaultTSFileName, wildcard='txt', 
                                   style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)#wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal()==wx.ID_OK:
            filename = saveDialog.GetPath()
            self.defaultTSFileName = os.path.split(filename)[1]
            self.SaveTrainingSetAs(filename)

    
    def SaveTrainingSetAs(self, filename):
        classDict = {}
        self.trainingSet = TrainingSet(p)
        self.trainingSet.Create([bin.label for bin in self.classBins], [bin.GetObjectKeys() for bin in self.classBins])
        self.trainingSet.Save(filename)
        
    
    def OnAddSortClass(self, evt):
        label = 'class_'+str(self.binsCreated)
        self.AddSortClass(label)
        self.RenameClass(label)
        
        
    def OnMapChannels(self, evt):
        ''' Responds to selection from the color mapping menus. '''
        # TODO: For some reason, typing Command+Q on an ImageViewer
        #    triggers wx.EVT_MENU here, which throws an exception
        try:
            (chIdx,color) = self.chMapById[evt.GetId()]
        except Exception:
            return
        self.chMap[chIdx] = color
        if color.lower() != 'none':
            self.toggleChMap[chIdx] = color
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
        self.trainingSet.Create(labels = [bin.label for bin in self.classBins],
                                keyLists = [bin.GetObjectKeys() for bin in self.classBins])
        output = StringIO()
        self.PostMessage('Training classifier with '+str(nRules)+' rules...')
        self.weaklearners = FastGentleBoostingMulticlass.train(self.trainingSet.colnames,
                                                               nRules, self.trainingSet.label_matrix, 
                                                               self.trainingSet.values, output)
        print self.weaklearners
        self.SetStatusText('')
        self.rulesTxt.Value = output.getvalue()
        self.scoreAllBtn.Enable()
        self.scoreImageBtn.Enable()

        for bin in self.classBins:
            if not bin.empty:
                bin.trained = True
            else:
                bin.trained = False
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
    
        # 2) Find the hits for each phenotype
        try:
            obKeys = dm.GetObjectsFromImage(imKey)
        except:
            self.SetStatusText('No such image: %s'%(imKey,))
            return
        classHits = {}
        if obKeys:
            for clNum, bin in enumerate(self.classBins):
                classHits[bin.label] = MulticlassSQL.FilterObjectsFromClassN(clNum+1, self.weaklearners, [imKey])
                self.PostMessage('%s of %s %s classified as %s in image %s'%(len(classHits[bin.label]), len(obKeys), p.object_name[1], bin.label, imKey))
        
        # 3) Get object coordinates in image and display
        classCoords = {}
        for className, obKeys in classHits.items():
            coords = []
            for obKey in obKeys:
                coords += [db.GetObjectCoords(obKey)]
            classCoords[className] = coords
        imViewer = ImageTools.ShowImage(imKey, list(self.chMap), self,
                                        brightness=self.brightness, scale=self.scale)
        imViewer.SetClasses(classCoords)
        
        
        
    def OnScoreAll(self, evt):
        '''
        Handler for ScoreAll button.  Calculates object counts for each class
        and enrichment values, then builds a table and displays it in a DataGrid.
        '''
        groupChoices   =  ['Image'] + p.groups_ordered
        filterChoices  =  [None] + p.filters_ordered
        nClasses       =  len(self.classBins)
        two_classes    =  nClasses == 2

        
        dlg = ScoreDialog(self, groupChoices, filterChoices)
        if dlg.ShowModal() == wx.ID_OK:            
            group = dlg.group
            filter = dlg.filter
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        from time import time
        t1 = time()
        
        # If hit counts havn't been calculated since last training or if the
        # user is filtering the data differently then classify all objects
        # into phenotype classes and count phenotype-hits per-image.
        if not self.keysAndCounts or filter!=self.lastScoringFilter:
            self.lastScoringFilter = filter

            dlg = wx.ProgressDialog('Calculating %s counts for each class...'%(p.object_name[0]), '0% complete', 100, self, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME)
            def update(frac):
                dlg.Update(int(frac * 100), '%d%% Complete'%(frac * 100))
            try:
                self.keysAndCounts = MulticlassSQL.PerImageCounts(self.weaklearners, filter=filter, cb=update)
            finally:
                dlg.Destroy()

            # Make sure PerImageCounts returned something
            if not self.keysAndCounts:
                errdlg = wx.MessageDialog(self, 'No images are in filter "%s". Please check the filter definition in your properties file.'%(filter), "Empty Filter", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                errdlg.Destroy()
                return
                
        t2 = time()
        print 'time to calculate hits: %.3fs'%(t2-t1)
        
        # Sum hits-per-group if not grouping by image
        if group != groupChoices[0]:
            self.PostMessage('Grouping %s counts by %s...' % (p.object_name[0], group))
            imData = {}
            for row in self.keysAndCounts:
                key = tuple(row[:-nClasses])
                imData[key] = numpy.array([float(v) for v in row[-nClasses:]])
            groupedKeysAndCounts = numpy.array([list(k)+vals.tolist() for k, vals in dm.SumToGroup(imData, group).items()], dtype=object)
        else:
            groupedKeysAndCounts = numpy.array(self.keysAndCounts, dtype=object)
        
        t3 = time()
        print 'time to group per-image counts: %.3fs'%(t3-t2)
                
        # Calculate alpha
        self.PostMessage('Fitting beta binomial distribution to data...')
        counts = groupedKeysAndCounts[:,-nClasses:]
        alpha, converged = PolyaFit.fit_betabinom_minka_alternating(counts)
        print '   alpha =', alpha, '   converged =', converged
        print '   alpha/Sum(alpha) = ', [a/sum(alpha) for a in alpha]
        
        t4 = time()
        print 'time to fit beta binomial: %.3fs'%(t4-t3)
                    
        # Construct matrix of table data
        self.PostMessage('Computing enrichment scores for each group...')
        tableData = []
        fraction = 0.0
        dlg = wx.ProgressDialog('Computing enrichment scores for each group...', '0% complete', len(groupedKeysAndCounts), self, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME)
        for i, row in enumerate(groupedKeysAndCounts):
            # Update the status text after every 2% is done.
            if float(i)/len(groupedKeysAndCounts)-fraction > 0.02:
                fraction = float(i)/len(groupedKeysAndCounts)
                dlg.Update(i, '%d%% Complete'%(fraction*100))
            
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
        dlg.Destroy()
        tableData = numpy.array(tableData, dtype=object)
        
        t5 = time()
        print 'time to compute enrichment scores: %.3fs'%(t5-t4)
        
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
                labels += ['Counts\n'+self.classBins[i].label]
            else:
                labels += ['Area Sums\n'+self.classBins[i].label]
        for i in xrange(nClasses):
            labels += ['p(Enriched)\n'+self.classBins[i].label]
        if two_classes:
            labels += ['Enriched Score\n'+self.classBins[0].label]
        else:
            for i in xrange(nClasses):
                labels += ['Enriched Score\n'+self.classBins[i].label]

        title = "Enrichments grouped by %s"%(group,)
        if filter:
            title += " filtered by %s"%(filter,)
        grid = DataGrid(tableData, labels, grouping=group,
                        groupIDIndices=groupIDIndices,
                        chMap=self.chMap[:], parent=self,
                        selectableColumns=set(range(len(groupIDIndices),len(labels))),
                        title=title)
        grid.Show()
        
        self.SetStatusText('')      
        
    
    def WriteEnrichmentsToTempTable(self):
        '''
        Write per-image enrichments to a temporary table for access in other parts of the app.
        '''
        tableName = 'enrichments'
        cols = [p.image_id, p.well_id, p.plate_id] + [labels[i] for i in self.selectableColumns]
        colDefs = ['%s %s'%(c, t) for c in cols]
        
        'DROP TABLE IF EXISTS %s'%(tableName)
        'CREATE TEMPORARY TABLE %s (%s)'%(tableName, colDefs)
        'INSERT INTO %s (%s) '%(tableName, cols, row)
  
                
            
    def OnSelectFilter(self, evt):
        ''' Handler for fetch filter selection. '''
        filter = self.filterChoice.GetStringSelection()
        # Select from a specific image
        if filter == 'experiment' or filter in p.filters_ordered:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
        elif filter == 'image' or filter in p.groups_ordered:
            self.SetupFetchFromGroupSizer(filter)
            self.fetchSizer.Show(self.fetchFromGroupSizer, True)
        self.Layout()
        
    
    def SetupFetchFromGroupSizer(self, group):
        '''
        This sizer displays text fields for inputting each element of a
        particular group's key. A group with 2 columns: Gene, and Well,
        would be represented by two text boxes.
        '''
        if group=='image':
            fieldNames = ['image']
            if p.table_id: fieldNames = ['table', 'image']
            fieldTypes = [int, int]
            validKeys = dm.GetAllImageKeys()
        elif group=='well':
            fieldNames = ['plate', 'well']
            fieldTypes = [str, str]
            validKeys = dm.GetAllImageKeys()
        else:            
            fieldNames = dm.GetGroupColumnNames(group)
            fieldTypes = dm.GetGroupColumnTypes(group)
            validKeys = dm.GetGroupKeysInGroup(group)
            
        self.groupInputs = []
        self.groupFieldValidators = []
        self.fetchFromGroupSizer.Clear(True)
        for i, field in enumerate(fieldNames):
            label = wx.StaticText(self, wx.NewId(), field+':')
            validCols = list(set([col[i] for col in validKeys]))
            validCols.sort()
            validCols = [str(col) for col in validCols]
            if fieldTypes[i]==int or fieldTypes[i]==long or fieldTypes[i]==float:
                if group=='image':
                    fieldInp = wx.ComboBox(self, -1, value=validCols[0], size=(80,-1),
                                           choices=validCols)
                else:
                    fieldInp = wx.ComboBox(self, -1, value=validCols[0], size=(80,-1),
                                           choices=['**ANY**']+validCols)
                    validCols = ['**ANY**']+validCols
                # Create and bind to a text Validator
                def ValidateGroupField(evt, validCols=validCols):
                    ctrl = evt.GetEventObject().GetChildren()[0]
                    if ctrl.GetValue() in validCols:
                        ctrl.SetForegroundColour('#000001')
                    else:
                        ctrl.SetForegroundColour('#FF0000')
                self.groupFieldValidators += [ValidateGroupField]
                fieldInp.Bind(wx.EVT_TEXT, self.groupFieldValidators[-1])
            else:
                fieldInp = wx.ComboBox(self, -1, value=validCols[0], size=(80,-1),
                                       choices=['**ANY**']+validCols, style=wx.CB_READONLY)
            self.groupInputs += [fieldInp]
            self.fetchFromGroupSizer.Add(label)
            self.fetchFromGroupSizer.Add(fieldInp)
            self.fetchFromGroupSizer.AddSpacer((10,20))
    
    
    def ValidateIntegerField(self, evt):
        ''' Validates an integer-only TextCtrl '''
        txtCtrl = evt.GetEventObject()
        # NOTE: textCtrl.SetBackgroundColor doesn't appear to work (probably works on win)
        #   foreground color only works when not setting to black.  LAAAAMMMEE!
        try:
            int(txtCtrl.GetValue())
            txtCtrl.SetForegroundColour('#000001')
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')
            
    
    def GetGroupKeyFromGroupSizer(self):
        ''' Returns the text in the group text inputs as a group key. '''
        groupKey = []
        for input in self.groupInputs:
            groupKey += [input.GetValue()]
            # Try to convert the type to long or float if possible
            # TODO: Cludgy: we should match the key type in the DataModel
            try: groupKey[-1] = float(groupKey[-1])
            except: pass
            try: groupKey[-1] = long(groupKey[-1])
            except: pass
        return tuple(groupKey)
    
    
    def OnShowImageControls(self, evt):
        ''' Shows the image adjustment control panel in a new frame. '''
        self.imageControlFrame = wx.Frame(self)
        ImageControlPanel(self.imageControlFrame, self, brightness=self.brightness, scale=self.scale)
        self.imageControlFrame.Show(True)
        
    
    def OnShowReadme(self, evt):
        ''' Shows a scrollable message dialog with the readme. '''
        from wx.lib.dialogs import ScrolledMessageDialog
        f = open(os.getcwd().rpartition('/')[0]+'/README.txt')
        text = f.read()
        dlg = ScrolledMessageDialog(self, text, 'Readme', size=(900,600))
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
        
        
    def PostMessage(self, message):
        ''' Updates the status bar text and prints to stdout. '''
        self.SetStatusText(message)
        print message
        

    def OnClose(self, evt):
        ''' Prompt to save training set before closing. '''
        if self.trainingSet and self.trainingSet.saved == False:
            dlg = wx.MessageDialog(self, 'Do you want to save your training set before quitting?', 'Training Set Not Saved', wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.SaveTrainingSet()
            elif response == wx.ID_CANCEL:
                return
        self.Destroy()
        
    
    def Destroy(self):
        ''' Kill off all threads before combusting. '''
        super(ClassifierGUI, self).Destroy()
        import threading
        for thread in threading.enumerate():
            if thread != threading.currentThread():
                print 'aborting thread', thread.getName()
                try:
                    thread.abort()
                except:
                    pass
        
                
        
def show_exception_as_dialog(type, value, tb):
    """Exception handler that show a dialog."""
    import traceback
    traceback.print_exc()
    lines = ['An error occurred in the program:\n']
    lines += traceback.format_exception_only(type, value)
    lines += ['\nTraceback (most recent call last):\n']
    lines += traceback.format_tb(tb)
    wx.MessageBox("".join(lines), 'Error')
    raise value



def LoadProperties():
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])      # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
        dm.PopulateModel()
    else:
        print 'Classifier requires a properties file.  Exiting.'
        exit()



# ----------------- Run -------------------

if __name__ == "__main__":
    import sys
    
    global defaultDir
    defaultDir = os.getcwd()
    
    # Handles args to MacOS "Apps"
    if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
        del sys.argv[1]

    # Initialize the app early because the fancy exception handler
    # depends on it in order to show a dialog.
    app = wx.PySimpleApp()
    
    # Install our own pretty exception handler unless one has already
    # been installed (e.g., a debugger)
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = show_exception_as_dialog

    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
        dm.PopulateModel()
    else:
        LoadProperties()
        
    classifier = ClassifierGUI(None)
    classifier.Show(True)
    app.MainLoop()
