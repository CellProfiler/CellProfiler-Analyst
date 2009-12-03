from __future__ import with_statement

# This must come first for py2app/py2exe
import matplotlib
matplotlib.use('WXAgg')
try:
    import cellprofiler.gui.cpfigure as cpfig
except: pass
# ---

from DataGrid import DataGrid
from DataModel import DataModel
from ImageControlPanel import ImageControlPanel
from PlateMapBrowser import PlateMapBrowser
from Properties import Properties
from ScoreDialog import ScoreDialog
import TileCollection
from TrainingSet import TrainingSet
from cStringIO import StringIO
from time import time
from icons import get_cpa_icon
import DBConnect
import DirichletIntegrate
import FastGentleBoostingMulticlass
import ImageTools
import MulticlassSQL
import PolyaFit
import SortBin
import logging
import numpy as np
import os
import sys
import wx
    
ID_EXIT = wx.NewId()
ID_CLASSIFIER = wx.NewId()

class ClassifierGUI(wx.Frame):
    """
    GUI Interface and functionality for the Classifier.
    """
    def __init__(self, properties=None, parent=None, id=ID_CLASSIFIER, **kwargs):
        
        if properties is not None:
            global p
            p = properties
            global dm
            dm = DataModel.getInstance()
            if dm.IsEmpty():
                dm.PopulateModel()
            if __name__ == "__main__":
                MulticlassSQL.CreateFilterTables()
            global db
            db = DBConnect.DBConnect.getInstance()
            
        if p.IsEmpty():
            logging.critical('Classifier requires a properties file. Exiting.')
            sys.exit()

        if DataModel.getInstance().IsEmpty():
            logging.debug("DataModel is empty. Classifier requires a populated DataModel to function. Exiting.")
            sys.exit()

        wx.Frame.__init__(self, parent, id=id, title='Classifier 2.0 - %s'%(os.path.basename(p._filename)), size=(800,600), **kwargs)
        self.tbicon = wx.TaskBarIcon()
        self.tbicon.SetIcon(get_cpa_icon(), 'CellProfiler Analyst 2.0')
        self.SetName('Classifier')
        
        self.pmb = None
        self.worker = None
        self.weaklearners = None
        self.trainingSet = None
        self.classBins = []
        self.binsCreated = 0
        self.chMap = p.image_channel_colors[:]
        self.toggleChMap = p.image_channel_colors[:] # used to store previous color mappings when toggling colors on/off with ctrl+1,2,3...
        self.brightness = 1.0
        self.scale = 1.0
        self.contrast = None
        self.defaultTSFileName = None
        self.lastScoringFilter = None
        
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateMenus()
        
        self.CreateStatusBar()
        
        #### Create GUI elements
        # Top level - three split windows
        self.splitter = wx.SplitterWindow(self, style=wx.NO_BORDER|wx.SP_3DSASH)
        self.fetch_and_rules_panel = wx.Panel(self.splitter)
        self.bins_splitter = wx.SplitterWindow(self.splitter, style=wx.NO_BORDER|wx.SP_3DSASH)
        
        # fetch & rules
        self.fetch_panel = wx.Panel(self.fetch_and_rules_panel)
        self.rules_text = wx.TextCtrl(self.fetch_and_rules_panel, -1, size=(-1,-1), style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.rules_text.SetMinSize((-1, int(p.image_tile_size)))
        self.find_rules_panel = wx.Panel(self.fetch_and_rules_panel)
        
        # sorting bins
        self.unclassified_panel = wx.Panel(self.bins_splitter)
        self.unclassified_box = wx.StaticBox(self.unclassified_panel, label='unclassified '+p.object_name[1])
        self.unclassified_sizer = wx.StaticBoxSizer(self.unclassified_box, wx.VERTICAL)
        self.unclassifiedBin = SortBin.SortBin(parent=self.unclassified_panel,
                                               classifier=self,
                                               label='unclassified',
                                               parentSizer=self.unclassified_sizer)
        self.unclassified_sizer.Add(self.unclassifiedBin, proportion=1, flag=wx.EXPAND)
        self.unclassified_panel.SetSizer(self.unclassified_sizer)
        self.classified_bins_panel = wx.Panel(self.bins_splitter)

        # fetch objects interface
        self.nObjectsTxt = wx.TextCtrl(self.fetch_panel, id=-1, value='20', size=(30,-1), style=wx.TE_PROCESS_ENTER)
        self.obClassChoice = wx.Choice(self.fetch_panel, id=-1, choices=['random'])
        self.filterChoice = wx.Choice(self.fetch_panel, id=-1, 
                                      choices=['experiment', 'image']+p._filters_ordered+p._groups_ordered)#+['*create new filter*'])
        self.fetchFromGroupSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetchBtn = wx.Button(self.fetch_panel, -1, 'Fetch!')

        # find rules interface
        self.nRulesTxt = wx.TextCtrl(self.find_rules_panel, -1, value='5', size=(30,-1))
        self.findRulesBtn = wx.Button(self.find_rules_panel, -1, 'Find Rules')
        self.scoreAllBtn = wx.Button(self.find_rules_panel, -1, 'Score All')
        self.scoreImageBtn = wx.Button(self.find_rules_panel, -1, 'Score Image')

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
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.nObjectsTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.obClassChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, p.object_name[1]), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'from'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.filterChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((10,20))
        self.fetchSizer.Add(self.fetchFromGroupSizer, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddSpacer((5,20))
        self.fetchSizer.Add(self.fetchBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddStretchSpacer()
        self.fetch_panel.SetSizerAndFit(self.fetchSizer)

        # find rules panel
        self.find_rules_sizer.AddStretchSpacer()
        self.find_rules_sizer.Add((5,20))
        self.find_rules_sizer.Add(wx.StaticText(self.find_rules_panel, -1, 'Max number of rules:'))
        self.find_rules_sizer.Add((5,20))
        self.find_rules_sizer.Add(self.nRulesTxt)
        self.find_rules_sizer.Add((5,20))
        self.find_rules_sizer.Add(self.findRulesBtn)
        try:
            import cellprofiler.gui.cpfigure as cpfig
            self.checkAccuracyBtn = wx.Button(self.find_rules_panel, -1, 'Check Accuracy')
            self.checkAccuracyBtn.Disable()
            self.find_rules_sizer.Add((5,20))
            self.find_rules_sizer.Add(self.checkAccuracyBtn)
            self.Bind(wx.EVT_BUTTON, self.OnCheckAccuracy, self.checkAccuracyBtn)
        except:
            logging.debug("Could not import cpfigure, will not display Margin vs. Iteration plot.")
        self.find_rules_sizer.Add((5,20))
        self.find_rules_sizer.Add(self.scoreAllBtn)
        self.find_rules_sizer.Add((5,20))
        self.find_rules_sizer.Add(self.scoreImageBtn)
        self.find_rules_sizer.Add((5,20))
        self.find_rules_panel.SetSizerAndFit(self.find_rules_sizer)

        # fetch and rules panel
        self.fetch_and_rules_sizer.Add((5,5))
        self.fetch_and_rules_sizer.Add(self.fetch_panel, flag=wx.EXPAND)
        self.fetch_and_rules_sizer.Add((5,5))
        self.fetch_and_rules_sizer.Add(self.rules_text, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=5)
        self.fetch_and_rules_sizer.Add((5,5))
        self.fetch_and_rules_sizer.Add(self.find_rules_panel, flag=wx.EXPAND)
        self.fetch_and_rules_panel.SetSizerAndFit(self.fetch_and_rules_sizer)

        # classified bins panel
        self.classified_bins_panel.SetSizer(self.classified_bins_sizer)

        # splitter windows
        self.splitter.SplitHorizontally(self.fetch_and_rules_panel, self.bins_splitter, self.fetch_and_rules_panel.GetMinSize()[1])
        self.bins_splitter.SplitHorizontally(self.unclassified_panel, self.classified_bins_panel)

        self.splitter.SetSashGravity(0.0)
        self.bins_splitter.SetSashGravity(0.5)

        self.splitter.SetMinimumPaneSize(max(int(p.image_tile_size), self.fetch_and_rules_panel.GetMinHeight()))
        self.bins_splitter.SetMinimumPaneSize(int(p.image_tile_size))
        self.SetMinSize((self.fetch_and_rules_panel.GetMinWidth(), 4 * int(p.image_tile_size) + self.fetch_and_rules_panel.GetMinHeight()))

        # Set initial state
        self.obClassChoice.SetSelection(0)
        self.filterChoice.SetSelection(0)
        self.findRulesBtn.Disable()
        self.scoreAllBtn.Disable()
        self.scoreImageBtn.Disable()
        self.fetchSizer.Hide(self.fetchFromGroupSizer)
        # add the default classes
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
        self.Bind(wx.EVT_BUTTON, self.OnFindRules, self.findRulesBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreAll, self.scoreAllBtn)
        self.Bind(wx.EVT_BUTTON, self.OnScoreImage, self.scoreImageBtn)
        self.nObjectsTxt.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.nRulesTxt.Bind(wx.EVT_TEXT, self.ValidateNumberOfRules)
        self.nObjectsTxt.Bind(wx.EVT_TEXT_ENTER, self.OnFetch)

        self.GetStatusBar().Bind(wx.EVT_SIZE, self.status_bar_onsize)
        wx.CallAfter(self.status_bar_onsize, None)

        self.Bind(wx.EVT_MENU, self.OnClose, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHAR, self.OnKey)     # Doesn't work for windows
        TileCollection.EVT_TILE_UPDATED(self, self.OnTileUpdated)
        self.Bind(SortBin.EVT_QUANTITY_CHANGED, self.OnQuantityChanged)
        
        # If there's a default training set. Ask to load it.
        if p.training_set and os.access(p.training_set, os.R_OK):
            # file existence is checked in Properties mobdule
            dlg = wx.MessageDialog(self, 'Would you like to load the training set defined in your properties file?\n\n%s\n\nTo prevent this message from appearing. Remove the training_set field from your properties file.'%(p.training_set),
                                   'Load Default Training Set?', wx.YES_NO|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.LoadTrainingSet(p.training_set)

    def status_bar_onsize(self, event):
        # draw the "add sort class..." button in the status bar
        button = self.addSortClassBtn
        width, height = self.GetStatusBar().GetClientSize()
        # diagonal lines drawn on mac, so move let by height.
        button.SetPosition((width - button.GetSize()[0] - 1 - height , button.GetPosition()[1]))


    def BindMouseOverHelpText(self):
        self.nObjectsTxt.SetToolTip(wx.ToolTip('The number of %s to fetch.'%(p.object_name[1])))
        self.obClassChoice.SetToolTip(wx.ToolTip('The phenotype of the %s.'%(p.object_name[1])))
        self.obClassChoice.GetToolTip().SetDelay(3000)
        self.filterChoice.SetToolTip(wx.ToolTip('Filters fetched %s to be from a subset of your images. (See groups and filters in the properties file)'%(p.object_name[1])))
        self.filterChoice.GetToolTip().SetDelay(3000)
        self.fetchBtn.SetToolTip(wx.ToolTip('Fetches images of %s to be sorted.'%(p.object_name[1])))
        self.rules_text.SetToolTip(wx.ToolTip('Rules are displayed in this text box.'))
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
        self.loadTSMenuItem = self.fileMenu.Append(-1, text='Load training set\tCtrl+O', help='Loads objects and classes specified in a training set file.')
        self.saveTSMenuItem = self.fileMenu.Append(-1, text='Save training set\tCtrl+S', help='Save your training set to file so you can reload these classified cells again.')
        self.fileMenu.AppendSeparator()
        self.exitMenuItem = self.fileMenu.Append(id=ID_EXIT, text='Exit\tCtrl+Q', help='Exit classifier')
        self.GetMenuBar().Append(self.fileMenu, 'File')

        # View Menu
        viewMenu = wx.Menu()
        imageControlsMenuItem = viewMenu.Append(-1, text='Image Controls\tCtrl+Shift+I', help='Launches a control panel for adjusting image brightness, size, etc.')
        self.GetMenuBar().Append(viewMenu, 'View')

        # Channel Menus
        self.CreateChannelMenus()
        
        self.Bind(wx.EVT_MENU, self.OnLoadTrainingSet, self.loadTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveTrainingSet, self.saveTSMenuItem)
        self.Bind(wx.EVT_MENU, self.OnShowImageControls, imageControlsMenuItem)
        
        
    def CreateChannelMenus(self):
        ''' Create color-selection menus for each channel. '''
        chIndex=0
        self.chMapById = {}
        for channel, setColor in zip(p.image_channel_names, self.chMap):
            channel_menu = wx.Menu()
            for color in ['Red', 'Green', 'Blue', 'Cyan', 'Magenta', 'Yellow', 'Gray', 'None']:
                id = wx.NewId()
                item = channel_menu.AppendRadioItem(id,color)
                self.chMapById[id] = (chIndex,color,item,channel_menu)
                if color.lower() == setColor.lower():
                    item.Check()
                self.Bind(wx.EVT_MENU, self.OnMapChannels, item)
            self.GetMenuBar().Append(channel_menu, channel)
            chIndex+=1
        
        
    def AddSortClass(self, label):
        ''' Create a new SortBin in a new StaticBoxSizer with the given label.
        This sizer is then added to the classified_bins_sizer. '''
        sizer = wx.StaticBoxSizer(wx.StaticBox(self.classified_bins_panel, label=label), wx.VERTICAL)
        # NOTE: bin must be created after sizer or drop events will occur on the sizer
        bin = SortBin.SortBin(parent=self.classified_bins_panel, label=label, 
                              classifier=self, parentSizer=sizer)
        sizer.Add(bin, proportion=1, flag=wx.EXPAND)
        self.classified_bins_sizer.Add(sizer, proportion=1, flag=wx.EXPAND)
        self.classBins.append(bin)
        self.classified_bins_panel.Layout()
        self.binsCreated += 1
        
    
    def RemoveSortClass(self, label):
        for bin in self.classBins:
            if bin.label == label:
                self.classBins.remove(bin)
                # Remove the label from the class dropdown menu
                self.obClassChoice.SetItems([item for item in self.obClassChoice.GetItems() if item!=bin.label])
                self.obClassChoice.Select(0)
                # Remove the bin
                self.classified_bins_sizer.Remove(bin.parentSizer)
                bin.Destroy()
                self.classified_bins_panel.Layout()
                break
        self.weaklearners = None
        self.rules_text.SetValue('')
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
                    return self.RenameClass(label)
            if ' ' in newLabel:
                errdlg = wx.MessageDialog(self, 'Labels can not contain spaces', "Can't Name Class", wx.OK|wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    return self.RenameClass(label)
            for bin in self.classBins:
                if bin.label == label:
                    bin.label = newLabel
                    bin.UpdateQuantity()
                    break
            dlg.Destroy()
            return wx.ID_OK
        return wx.ID_CANCEL
        
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
        if not self.IsTrained():
            self.obClassChoice.SetItems(['random'])
            self.obClassChoice.SetSelection(0)
            self.scoreAllBtn.Disable()
            self.scoreImageBtn.Disable()
            if hasattr(self, 'checkAccuracyBtn'):
                self.checkAccuracyBtn.Disable()
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
            elif filter in p._filters_ordered:
                filteredImKeys = db.GetFilteredImages(filter)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in filter "%s"'%(filter))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys)
                statusMsg += ' from filter "%s"'%(filter)
            elif filter in p._groups_ordered:
                # if the filter name is a group then it's actually a group
                groupName = filter
                groupKey = self.GetGroupKeyFromGroupSizer(groupName)
                filteredImKeys = dm.GetImagesInGroupWithWildcards(groupName, groupKey)
                colNames = dm.GetGroupColumnNames(groupName)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in group %s: %s'%(groupName, 
                                        ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)])))
                    return
                obKeys = dm.GetRandomObjects(nObjects, filteredImKeys)
                if not obKeys:
                    self.PostMessage('No cells were found in this group. Group %s: %s'%(groupName, 
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
                elif filter in p._filters_ordered:
                    filteredImKeys = db.GetFilteredImages(filter)
                    if filteredImKeys == []:
                        self.PostMessage('No images were found in filter "%s"'%(filter))
                        return
                elif filter in p._groups_ordered:
                    group_name = filter
                    groupKey = self.GetGroupKeyFromGroupSizer(group_name)
                    colNames = dm.GetGroupColumnNames(group_name)
                    filteredImKeys = dm.GetImagesInGroupWithWildcards(group_name, groupKey)
                    if filteredImKeys == []:
                        self.PostMessage('No images were found in group %s: %s'%(group_name,
                                            ', '.join(['%s=%s'%(n,v) for n, v in zip(colNames,groupKey)])))
                        return
                    
            attempts = 0
            # Now check which objects fall within the classification
            while len(obKeys) < nObjects:
                if filter == 'experiment':
                    if p.db_sqlite_file:
                        obKeysToTry = 'RANDOM() < %d'%(dm.GetRandomFraction(100))
                    else:
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
                    obKeysToTry.sort()
                    if filter in p._filters_ordered:
                        loopMsg = ' from filter %s'%(filter)
                    elif filter in p._groups_ordered:
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
        
        # pause tile loading
        with TileCollection.load_lock():
            self.PostMessage('Loading training set from: %s'%filename)
            # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
            os.chdir(os.path.split(filename)[0])
            self.defaultTSFileName = os.path.split(filename)[1]

            self.trainingSet = TrainingSet(p, filename, labels_only=True)

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
        if self.RenameClass(label) == wx.ID_CANCEL:
            self.RemoveSortClass(label)
            
        
    def OnMapChannels(self, evt):
        ''' Responds to selection from the color mapping menus. '''
        (chIdx,color,item,menu) = self.chMapById[evt.GetId()]
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
                self.SetStatusText('Image contains %s %s.'%(dm.GetObjectCountFromImage(imKey),p.object_name[1]))
            else:
                txtCtrl.SetForegroundColour('#888888')   # Set field to GRAY if image contains no objects
                self.SetStatusText('Image contains zero %s.'%(p.object_name[1]))
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')       # Set field to red if image doesn't exist
            self.SetStatusText('No such image.')

    def OnCheckAccuracy(self, evt):
        ''' Called when the CheckAccuracy Button is pressed. '''
        # get wells if available, otherwise use imagenumbers
        try:
            nRules = int(self.nRulesTxt.GetValue())
        except:
            logging.error('Unable to parse number of rules')
            return

        groups = [db.get_platewell_for_object(key) for key in self.trainingSet.get_object_keys()]

        dlg = wx.ProgressDialog('Computing cross validation accuracy...', '0% Complete', 100, self, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)        
        base = 0.0
        scale = 1.0

        class StopXValidation(Exception):
            pass

        def progress_callback(amount):
            pct = min(int(100 * (amount * scale + base)), 100)
            cont, skip = dlg.Update(pct, '%d%% Complete'%(pct))
            if not cont:
                raise StopXValidation

        # each round of xvalidation takes about (numfolds * (1 - (1 / num_folds))) time
        step_time_1 = (2.0 * (1.0 - 1.0 / 2.0))
        step_time_2 = (20.0 * (1.0 - 1.0 / 20.0))
        scale = step_time_1 / (10 * step_time_1 + step_time_2)

        xvalid_50 = []

        try:
            for i in range(10):
                xvalid_50 += FastGentleBoostingMulticlass.xvalidate(self.trainingSet.colnames,
                                                                    nRules, self.trainingSet.label_matrix, 
                                                                    self.trainingSet.values, 2,
                                                                    groups, progress_callback)
                # each round makes one "scale" size step in progress
                base += scale

            xvalid_50 = sum(xvalid_50) / 10.0

            # only one more step
            scale = 1.0 - base
            xvalid_95 = FastGentleBoostingMulticlass.xvalidate(self.trainingSet.colnames,
                                                                    nRules, self.trainingSet.label_matrix, 
                                                                    self.trainingSet.values, 20,
                                                                    groups, progress_callback)

            dlg.Destroy()

            figure = cpfig.create_or_find(self, -1, 'Cross-validation accuracy', subplots=(1,1), name='Cross-validation accuracy')
            sp = figure.subplot(0,0)
            sp.clear()
            sp.hold(True)
            sp.plot(range(1, nRules + 1), 1.0 - xvalid_50 / float(len(groups)), 'r', label='50% cross-validation accuracy')
            sp.plot(range(1, nRules + 1), 1.0 - xvalid_95[0] / float(len(groups)), 'b', label='95% cross-validation accuracy')
            chance_level = 1.0 / len(self.classBins)
            sp.plot([1, nRules + 1], [chance_level, chance_level], 'k--', label='accuracy of random classifier')
            sp.legend(loc='lower right')
            sp.set_xlabel('Rule #')
            sp.set_ylabel('Accuracy')
            sp.set_ylim(-0.05, 1.05)
            figure.Refresh()
        except StopXValidation:
            dlg.Destroy()

        
    def OnFindRules(self, evt):
        if not self.ValidateNumberOfRules():
            errdlg = wx.MessageDialog(self, 'Classifier will not run for the number of rules you have entered.', "Invalid Number of Rules", wx.OK|wx.ICON_EXCLAMATION)
            errdlg.ShowModal()
            errdlg.Destroy()
            return
        self.FindRules()
        
    def FindRules(self):
        try:
            nRules = int(self.nRulesTxt.GetValue())
        except:
            logging.error('Unable to parse number of rules')
            return
        
        self.keysAndCounts = None    # Must erase current keysAndCounts so they will be recalculated from new rules
        

        # pause tile loading
        with TileCollection.load_lock():
            try:
                def cb(frac):
                    cont, skip = dlg.Update(int(frac * 100.), '%d%% Complete'%(frac * 100.))
                    if not cont: # cancel was pressed
                        dlg.Destroy()
                        raise StopCalculating()

                dlg = wx.ProgressDialog('Fetching cell data for training set...', '0% Complete', 100, self, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
                self.trainingSet = TrainingSet(p)
                self.trainingSet.Create(labels = [bin.label for bin in self.classBins],
                                        keyLists = [bin.GetObjectKeys() for bin in self.classBins],
                                        callback=cb)
                output = StringIO()
                self.PostMessage('Training classifier with %s rules...'%(nRules))
                dlg.Destroy()
                dlg = wx.ProgressDialog('Training classifier...', '0% Complete', 100, self, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
                self.weaklearners = FastGentleBoostingMulticlass.train(self.trainingSet.colnames,
                                                                       nRules, self.trainingSet.label_matrix, 
                                                                       self.trainingSet.values, output,
                                                                       callback=cb)
                dlg.Destroy()
                self.SetStatusText('')
                self.rules_text.Value = output.getvalue()
                self.scoreAllBtn.Enable()
                self.scoreImageBtn.Enable()
                if hasattr(self, 'checkAccuracyBtn'):
                    self.checkAccuracyBtn.Enable()
            except StopCalculating:
                return

        for bin in self.classBins:
            if not bin.empty:
                bin.trained = True
            else:
                bin.trained = False
        self.UpdateClassChoices()
        
        
    def OnScoreImage(self, evt):
        # Get the image key
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
        dlg.SetValue('')
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
        
        # Score the Image
        classHits = self.ScoreImage(imKey)
        # Get object coordinates in image and display
        classCoords = {}
        for className, obKeys in classHits.items():
            classCoords[className] = [db.GetObjectCoords(key) for key in obKeys]
        # Show the image
        imViewer = ImageTools.ShowImage(imKey, list(self.chMap), self,
                                        brightness=self.brightness, scale=self.scale,
                                        contrast=self.contrast)
        imViewer.SetClasses(classCoords)
    
    def ScoreImage(self, imKey):
        '''
        Scores an image, then returns a dictionary of object keys indexed by class name
        eg: ScoreImage(imkey)['positive'] ==> [(6,32), (87,23), (412,65)]
        '''
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
        
        return classHits
         
        
    def OnScoreAll(self, evt):
        self.ScoreAll()
    
    def ScoreAll(self):
        '''
        Calculates object counts for each class and enrichment values,
        then builds a table and displays it in a DataGrid.
        '''
        groupChoices   =  ['Image'] + p._groups_ordered
        filterChoices  =  [None] + p._filters_ordered
        nClasses       =  len(self.classBins)
        two_classes    =  nClasses == 2
        nKeyCols = len(DBConnect.image_key_columns())
        
        # GET GROUPING METHOD AND FILTER FROM USER
        dlg = ScoreDialog(self, groupChoices, filterChoices)
        if dlg.ShowModal() == wx.ID_OK:            
            group = dlg.group
            filter = dlg.filter
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        t1 = time()
        
        # FETCH PER-IMAGE COUNTS FROM DB
        if not self.keysAndCounts or filter!=self.lastScoringFilter:
            # If hit counts havn't been calculated since last training or if the
            # user is filtering the data differently then classify all objects
            # into phenotype classes and count phenotype-hits per-image.
            self.lastScoringFilter = filter
            
            if p.class_table:
                overwrite_class_table = True
                # If p.class_table is already in the db, we need to confirm whether or not to overwrite it.
                if db.table_exists(p.class_table):
                    dlg = wx.MessageDialog(self, 'The database table "%s" already exists. Overwrite this table with new per-object class data?'%(p.class_table),
                                   'Overwrite %s?'%(p.class_table), wx.YES_NO|wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    if response == wx.ID_YES:
                        pass
                    else:
                        overwrite_class_table = False

            dlg = wx.ProgressDialog('Calculating %s counts for each class...'%(p.object_name[0]), '0% Complete', 100, self, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
            def update(frac):
                cont, skip = dlg.Update(int(frac * 100.), '%d%% Complete'%(frac * 100.))
                if not cont: # cancel was pressed
                    raise StopCalculating()
            try:
                self.keysAndCounts = MulticlassSQL.PerImageCounts(self.weaklearners, filter=filter, cb=update)
            except StopCalculating:
                dlg.Destroy()
                self.SetStatusText('Scoring canceled.')      
                return
                
            dlg.Destroy()

            # Make sure PerImageCounts returned something
            if not self.keysAndCounts:
                errdlg = wx.MessageDialog(self, 'No images are in filter "%s". Please check the filter definition in your properties file.'%(filter), "Empty Filter", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                errdlg.Destroy()
                return
            
            if p.class_table and overwrite_class_table:
                self.PostMessage('Saving %s classes to database...'%(p.object_name[0]))
                MulticlassSQL.create_perobject_class_table(self.trainingSet.labels, self.weaklearners)
                self.PostMessage('%s classes saved to table "%s"'%(p.object_name[0].capitalize(), p.class_table))
            
        t2 = time()
        logging.info('time to calculate hits: %.3fs'%(t2-t1))
        
        # AGGREGATE PER_IMAGE COUNTS TO GROUPS IF NOT GROUPING BY IMAGE
        if group != groupChoices[0]:
            self.PostMessage('Grouping %s counts by %s...' % (p.object_name[0], group))
            imData = {}
            for row in self.keysAndCounts:
                key = tuple(row[:nKeyCols])
                imData[key] = np.array([float(v) for v in row[nKeyCols:]])
            groupedKeysAndCounts = np.array([list(k)+vals.tolist() for k, vals in dm.SumToGroup(imData, group).items()], dtype=object)
            nKeyCols = len(dm.GetGroupColumnNames(group))
        else:
            groupedKeysAndCounts = np.array(self.keysAndCounts, dtype=object)
            if p.plate_id and p.well_id:
                pw = db.GetPlatesAndWellsPerImage()
                platesAndWells = {}
                for row in pw:
                    platesAndWells[tuple(row[:nKeyCols])] = list(row[nKeyCols:])
            
        
        t3 = time()
        logging.info('time to group per-image counts: %.3fs'%(t3-t2))
                
        # FIT THE BETA BINOMIAL
        self.PostMessage('Fitting beta binomial distribution to data...')
        counts = groupedKeysAndCounts[:,-nClasses:]
        alpha, converged = PolyaFit.fit_betabinom_minka_alternating(counts)
        logging.info('   alpha = %s   converged = %s'%( alpha, converged))
        logging.info('   alpha/Sum(alpha) = %s'%([a/sum(alpha) for a in alpha]))
        
        t4 = time()
        logging.info('time to fit beta binomial: %.3fs'%(t4-t3))
        
        # CONSTRUCT ARRAY OF TABLE DATA
        self.PostMessage('Computing enrichment scores for each group...')
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
            countsRow = [int(v) for v in row[nKeyCols:nKeyCols+nClasses]]
            tableRow += [sum(countsRow)]
            tableRow += countsRow
            if p.area_scoring_column is not None:
                # Append the areas
                countsRow = [int(v) for v in row[-nClasses:]]
                tableRow += [sum(countsRow)]
                tableRow += countsRow
            # Append the scores:
            #   compute enrichment probabilities of each class for this image OR group
            scores = np.array( DirichletIntegrate.score(alpha, np.array(countsRow)) )
            #   clamp to [0,1] to 
            scores[scores>1.] = 1.
            scores[scores<0.] = 0.
            tableRow += scores.tolist()
            # Append the logit scores:
            # Special case: only calculate logit of "positives" for 2-classes
            if two_classes:
                tableRow += [np.log10(scores[0])-(np.log10(1-scores[0]))]   # compute logit of each probability
            else:
                tableRow += [np.log10(score)-(np.log10(1-score)) for score in scores]   # compute logit of each probability
            tableData.append(tableRow)
        tableData = np.array(tableData, dtype=object)
        
        t5 = time()
        logging.info('time to compute enrichment scores: %.3fs'%(t5-t4))
        
        # CREATE COLUMN LABELS LIST
        # if grouping isn't per-image, then get the group key column names.
        if group != groupChoices[0]:
            labels = dm.GetGroupColumnNames(group)
        else:
            labels = list(DBConnect.image_key_columns())
        # record the column indices for the keys
        key_col_indices = [i for i in range(len(labels))]
        if group != 'Image':
            labels += ['Images']
        else:
            if p.plate_id and p.well_id:
                labels += [p.plate_id]
                labels += [p.well_id]
        labels += ['Total %s Count'%(p.object_name[0].capitalize())]
        for i in xrange(nClasses):
            labels += ['%s %s Count'%(self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
        if p.area_scoring_column is not None:
            labels += ['Total %s Area'%(p.object_name[0].capitalize())]
            for i in xrange(nClasses):
                labels += ['%s %s Area'%(self.classBins[i].label.capitalize(), p.object_name[0].capitalize())]
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
        title += ' (%s)'%(os.path.split(p._filename)[1])
        
        grid = DataGrid(tableData, labels, grouping=group,
                        key_col_indices=key_col_indices,
                        chMap=self.chMap[:], parent=self,
                        title=title)
        grid.Show()
        
        self.SetStatusText('')
        
    
    def OnSelectFilter(self, evt):
        ''' Handler for fetch filter selection. '''
        filter = self.filterChoice.GetStringSelection()
        # Select from a specific image
        if filter == 'experiment' or filter in p._filters_ordered:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
        elif filter == 'image' or filter in p._groups_ordered:
            self.SetupFetchFromGroupSizer(filter)
            self.fetchSizer.Show(self.fetchFromGroupSizer, True)
        elif filter == '*create new filter*':
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
            from ColumnFilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(550,80))
            if cff.ShowModal()==wx.OK:
                p._filters_ordered += [str(cff.get_filter())]
                p._filters[str(cff.get_filter())] = cff.get_filter().to_sql()
                items = self.filterChoice.GetItems()
                self.filterChoice.SetItems(items[:-1]+[str(cff.get_filter())]+items[-1:])
                self.filterChoice.SetSelection(len(items)-1)
            cff.Destroy()

        self.fetch_panel.Layout()
        self.fetch_panel.Refresh()
    
    
    def SetupFetchFromGroupSizer(self, group):
        '''
        This sizer displays input fields for inputting each element of a
        particular group's key. A group with 2 columns: Gene, and Well,
        would be represented by two combo boxes.
        '''
        if group=='image':
            fieldNames = ['table', 'image'] if p.table_id else ['image']
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
            label = wx.StaticText(self.fetch_panel, wx.NewId(), field+':')
            # Values to be sorted BEFORE being converted to str
            validVals = list(set([col[i] for col in validKeys]))
            validVals.sort()
            validVals = [str(col) for col in validVals]
            if group=='image' or fieldTypes[i]==int or fieldTypes[i]==long:
                fieldInp = wx.TextCtrl(self.fetch_panel, -1, value=validVals[0], size=(80,-1))
            else:
                fieldInp = wx.ComboBox(self.fetch_panel, -1, value=validVals[0], size=(80,-1),
                                       choices=['__ANY__']+validVals)
            validVals = ['__ANY__']+validVals
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
            self.fetchFromGroupSizer.AddSpacer((10,20))
    
    
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
            nRules   = int(self.nRulesTxt.GetValue())
            if p.db_type == 'sqlite':
                nClasses = len(self.classBins)
                maxRules = int((100-1)/(2+nClasses)) - 1
                if nRules > maxRules:
                    self.nRulesTxt.SetToolTip(wx.ToolTip(str(maxRules)))
                    self.nRulesTxt.SetForegroundColour('#FF0000')
                    logging.warn('For %s classes, the max number of rules is %s. To avoid this limitation, use MySQL.'%(nClasses, maxRules))
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
            val = input.GetValue()
            # if the value is blank, don't bother typing it, it is a wildcard
            if val != '__ANY__':
                val = ftype(val)
            groupKey += [val]
        return tuple(groupKey)
    
    
    def OnShowImageControls(self, evt):
        ''' Shows the image adjustment control panel in a new frame. '''
        self.imageControlFrame = wx.Frame(self)
        ImageControlPanel(self.imageControlFrame, self, brightness=self.brightness, scale=self.scale)
        self.imageControlFrame.Show(True)

        
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
            dlg = wx.MessageDialog(self, 'Do you want to save your training set before quitting?', 'Training Set Not Saved', wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
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
        return self.weaklearners is not None
        
    
    def Destroy(self):
        ''' Kill off all threads before combusting. '''
        super(ClassifierGUI, self).Destroy()
        import threading
        for thread in threading.enumerate():
            if thread != threading.currentThread() and thread.getName().lower().startswith('tileloader'):
                logging.debug('Aborting thread %s'%thread.getName())
                try:
                    thread.abort()
                except:
                    pass
        from TileCollection import TileCollection
        # XXX: Hack -- can't figure out what is holding onto TileCollection, but
        #      it needs to be trashed if Classifier is to be reopened since it
        #      will otherwise grab the existing instance with a dead tileLoader
        TileCollection._forgetClassInstanceReferenceForTesting()
        
                
        
        

class StopCalculating(Exception):
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
    dlg = wx.FileDialog(None, "Select the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])      # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        logging.error('Classifier requires a properties file.  Exiting.')
        sys.exit()


# ----------------- Run -------------------

if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.DEBUG,)
    
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
    db = DBConnect.DBConnect.getInstance()
    dm = DataModel.getInstance()

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        LoadProperties()
        
    dm.PopulateModel()
    MulticlassSQL.CreateFilterTables()
        
    classifier = ClassifierGUI()
    classifier.Show(True)
    app.MainLoop()
