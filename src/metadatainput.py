#!/usr/bin/env python

import wx
import os
import re
import sys
import operator
import  wx.calendar
import wx.lib.agw.flatnotebook as fnb
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *
from instancelist import *
from utils import *

class ExperimentSettingsWindow(wx.SplitterWindow):
    def __init__(self, parent, id=-1, **kwargs):
        wx.SplitterWindow.__init__(self, parent, id, **kwargs)
        
        self.tree = wx.TreeCtrl(self, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS)

        root = self.tree.AddRoot('Experiment')

        stc = self.tree.AppendItem(root, 'SETTINGS')
        ovr = self.tree.AppendItem(stc, 'Overview')
        stk = self.tree.AppendItem(stc, 'Stock Culture')
        ins = self.tree.AppendItem(stc, 'Instrument')
        self.tree.AppendItem(ins, 'Microscope')
        self.tree.AppendItem(ins, 'Flow Cytometer')
        exv = self.tree.AppendItem(stc, 'Experimental Vessel')
        self.tree.AppendItem(exv, 'Plate')
        self.tree.AppendItem(exv, 'Flask')
        self.tree.AppendItem(exv, 'Dish')
        self.tree.AppendItem(exv, 'Coverslip')
        #self.tree.AppendItem(exv, 'Culture Slide').Disable()
        stc = self.tree.AppendItem(root, 'ASSAY')
        cld = self.tree.AppendItem(stc, 'Cell Transfer')
        self.tree.AppendItem(cld, 'Seeding')
        self.tree.AppendItem(cld, 'Harvesting')
        ptb = self.tree.AppendItem(stc, 'Perturbation')
        self.tree.AppendItem(ptb, 'Chemical')
        self.tree.AppendItem(ptb, 'Biological')
        lbl = self.tree.AppendItem(stc, 'Labeling')
        self.tree.AppendItem(lbl, 'Stain')
        self.tree.AppendItem(lbl, 'Antibody')
        self.tree.AppendItem(lbl, 'Primer')
        adp = self.tree.AppendItem(stc, 'Additional Processes')        
        self.tree.AppendItem(adp, 'Spin')
        self.tree.AppendItem(adp, 'Wash')
        self.tree.AppendItem(adp, 'Dry')
        self.tree.AppendItem(adp, 'Add Medium')
        self.tree.AppendItem(adp, 'Incubation')
        dta = self.tree.AppendItem(stc, 'Data Acquisition')
        self.tree.AppendItem(dta, 'Timelapse Image')
        self.tree.AppendItem(dta, 'Static Image')
        self.tree.AppendItem(dta, 'Flow Cytometer Files')
        self.tree.Expand(root)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

        #self.openBenchBut = wx.Button(self, id=-1, label='Open Wrok Bench', pos=(20, 60), size=(175, 28))
        #self.openBenchBut.Bind(wx.EVT_BUTTON, self.onOpenWrokBench)

        self.settings_container = wx.Panel(self)
        self.settings_container.SetSizer(wx.BoxSizer())
        self.settings_panel = wx.Panel(self)

        self.SetMinimumPaneSize(40)
        self.SplitVertically(self.tree, self.settings_container, self.tree.MinWidth)
        self.SetSashPosition(180)
        self.Centre()
                
    def OnSelChanged(self, event):
        item =  event.GetItem()

        self.settings_panel.Destroy()
        self.settings_container.Sizer.Clear()
        if self.tree.GetItemText(item) == 'Overview':
            self.settings_panel = OverviewPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Stock Culture':
            self.settings_panel = StockCultureSettingPanel(self.settings_container)
        
        elif self.tree.GetItemText(item) == 'Microscope':
            self.settings_panel = MicroscopeSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Flow Cytometer':
            self.settings_panel = FlowcytometerSettingPanel(self.settings_container)    
        
        elif self.tree.GetItemText(item) == 'Plate':
            self.settings_panel = PlateSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Flask':
            self.settings_panel = FlaskSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Dish':
            self.settings_panel = DishSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Coverslip':
            self.settings_panel = CoverslipSettingPanel(self.settings_container)        
        elif self.tree.GetItemText(item) == 'Culture Slide':
            self.settings_panel = CultureslideSettingPanel(self.settings_container)
        
        elif self.tree.GetItemText(item) == 'Seeding':
            self.settings_panel = CellSeedSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Harvesting':
            self.settings_panel = CellHarvestSettingPanel(self.settings_container)    
            
        elif self.tree.GetItemText(item) == 'Chemical':
            self.settings_panel = ChemicalSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Biological':
            self.settings_panel = BiologicalSettingPanel(self.settings_container)
                 
        elif self.tree.GetItemText(item) == 'Spin':
            self.settings_panel =  SpinningSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Wash':
            self.settings_panel =  WashSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Dry':
            self.settings_panel =  DrySettingPanel(self.settings_container) 
        elif self.tree.GetItemText(item) == 'Add Medium':
            self.settings_panel =  MediumSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Incubation':
            self.settings_panel = IncubatorSettingPanel(self.settings_container)   
            
        elif self.tree.GetItemText(item) == 'Stain':
            self.settings_panel = StainingAgentSettingPanel(self.settings_container)        
        elif self.tree.GetItemText(item) == 'Antibody':
            self.settings_panel =  AntibodySettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Primer':
            self.settings_panel =  PrimerSettingPanel(self.settings_container)
                    
        elif self.tree.GetItemText(item) == 'Timelapse Image':
            self.settings_panel = TLMSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Static Image':
            self.settings_panel = HCSSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Flow Cytometer Files':
            self.settings_panel = FCSSettingPanel(self.settings_container)
        else:
            self.settings_panel = wx.Panel(self.settings_container)

        self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)        
        self.settings_container.Layout()
        # Annoying: not sure why, but the notebook tabs reappear on other 
        # settings panels even after the panel that owend them (and the notebook
        # itself) is destroyed. This seems to happen on Mac only.
        self.settings_panel.ClearBackground()
        self.settings_panel.Refresh()

########################################################################        
######                 OVERVIEW PANEL                        ###########
########################################################################
class OverviewPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=12, cols=2, hgap=5, vgap=5)

        # Experiment Title
        titleTAG = 'Overview|Project|Title'
        self.settings_controls[titleTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(titleTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[titleTAG].SetInitialSize((300, 20))
        self.settings_controls[titleTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[titleTAG].SetToolTipString('Insert the title of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Title'), 0)
        fgs.Add(self.settings_controls[titleTAG], 0, wx.EXPAND)
        # Experiment Aim
        aimTAG = 'Overview|Project|Aims'
        self.settings_controls[aimTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(aimTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[aimTAG].SetInitialSize((300, 50))
        self.settings_controls[aimTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[aimTAG].SetToolTipString('Describe here the aim of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Aim'), 0)
        fgs.Add(self.settings_controls[aimTAG], 0, wx.EXPAND)
        # Keywords
        keyTAG = 'Overview|Project|Keywords'
        self.settings_controls[keyTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(keyTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[keyTAG].SetInitialSize((300, 50))
        self.settings_controls[keyTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[keyTAG].SetToolTipString('Keywords that indicates the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Keywords'), 0)
        fgs.Add(self.settings_controls[keyTAG], 0, wx.EXPAND)
        # Experiment Number
        exnumTAG = 'Overview|Project|ExptNum'
        self.settings_controls[exnumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
        if meta.get_field(exnumTAG) is not None:
            self.settings_controls[exnumTAG].SetStringSelection(meta.get_field(exnumTAG))
        self.settings_controls[exnumTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        self.settings_controls[exnumTAG].SetToolTipString('Experiment Number....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Number'), 0)
        fgs.Add(self.settings_controls[exnumTAG], 0, wx.EXPAND)
        # Experiment Date
        exdateTAG = 'Overview|Project|ExptDate'
        self.settings_controls[exdateTAG] = wx.DatePickerCtrl(self.sw, style = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY )
        if meta.get_field(exdateTAG) is not None:
            day, month, year = meta.get_field(exdateTAG).split('/')
            myDate = wx.DateTimeFromDMY(int(day), int(month)-1, int(year))
            self.settings_controls[exdateTAG].SetValue(myDate)
        self.settings_controls[exdateTAG].Bind(wx.EVT_DATE_CHANGED,self.OnSavingData)
        self.settings_controls[exdateTAG].SetToolTipString('Start date of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Start Date'), 0)
        fgs.Add(self.settings_controls[exdateTAG], 0, wx.EXPAND)
        # Publication
        exppubTAG = 'Overview|Project|Publications'
        self.settings_controls[exppubTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(exppubTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[exppubTAG].SetInitialSize((300, 50))
        self.settings_controls[exppubTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[exppubTAG].SetToolTipString('Experiment related publication list')
        fgs.Add(wx.StaticText(self.sw, -1, 'Related Publications'), 0)
        fgs.Add(self.settings_controls[exppubTAG], 0, wx.EXPAND)
        # Experimenter Name
        expnameTAG = 'Overview|Project|Experimenter'
        self.settings_controls[expnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(expnameTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[expnameTAG].SetInitialSize((300, 20))
        self.settings_controls[expnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[expnameTAG].SetToolTipString('Name of experimenter(s)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Name of Experimenter(s)'), 0)
        fgs.Add(self.settings_controls[expnameTAG], 0, wx.EXPAND)
        # Institution Name
        instnameTAG = 'Overview|Project|Institution'
        self.settings_controls[instnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(instnameTAG, default=''))
        self.settings_controls[instnameTAG].SetInitialSize((300, 20))
        self.settings_controls[instnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[instnameTAG].SetToolTipString('Name of Institution')
        fgs.Add(wx.StaticText(self.sw, -1, 'Name of Institution'), 0)
        fgs.Add(self.settings_controls[instnameTAG], 0, wx.EXPAND)
        # Department Name
        deptnameTAG = 'Overview|Project|Department'
        self.settings_controls[deptnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(deptnameTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[deptnameTAG].SetInitialSize((300, 20))
        self.settings_controls[deptnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[deptnameTAG].SetToolTipString('Name of the Department')
        fgs.Add(wx.StaticText(self.sw, -1, 'Department Name'), 0)
        fgs.Add(self.settings_controls[deptnameTAG], 0, wx.EXPAND)
        # Address
        addressTAG = 'Overview|Project|Address'
        self.settings_controls[addressTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(addressTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[addressTAG].SetInitialSize((300, 50))
        self.settings_controls[addressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[addressTAG].SetToolTipString('Postal address and other contact details')
        fgs.Add(wx.StaticText(self.sw, -1, 'Address'), 0)
        fgs.Add(self.settings_controls[addressTAG], 0, wx.EXPAND)
        # Status
        statusTAG = 'Overview|Project|Status'
        self.settings_controls[statusTAG] = wx.Choice(self.sw, -1, choices=['Complete', 'Ongoing', 'Pending', 'Discarded'])
        if meta.get_field(statusTAG) is not None:
            self.settings_controls[statusTAG].SetStringSelection(meta.get_field(statusTAG))
        self.settings_controls[statusTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[statusTAG].SetToolTipString('Status of the experiment, e.g. Complete, On-going, Discarded')
        fgs.Add(wx.StaticText(self.sw, -1, 'Status'), 0)
        fgs.Add(self.settings_controls[statusTAG], 0, wx.EXPAND)

        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        elif isinstance(ctrl, wx.DatePickerCtrl):
            date = ctrl.GetValue()
            meta.set_field(tag, '%02d/%02d/%4d'%(date.Day, date.Month+1, date.Year))
        else:
            meta.set_field(tag, ctrl.GetValue())


########################################################################        
######          STOCK CULTURE SETTING PANEL                       ######
########################################################################
class StockCultureSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_VC8)
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.onTabClosing)
        
        # Get all the previously encoded StockCulture pages and re-Add them as pages
        stk_list = meta.get_field_instances('StockCulture|Sample')
        
        for stk_id in sorted(stk_list):
            panel = StockCulturePanel(self.notebook,stk_id)
            self.notebook.AddPage(panel, 'StockCulture No: %s'% stk_id, True)     
        self.addStockCulturePageBtn = wx.Button(self, label="Add StockCulture")
        self.addStockCulturePageBtn.Bind(wx.EVT_BUTTON, self.onAddStockCulturePage)
        # at least one instance of the stkroscope exists so uers can copy from that instead of creating a new one
        if stk_list:
            self.addStockCulturePageBtn.Disable()
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addStockCulturePageBtn  , 0, wx.ALL, 5)
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
    
    def onTabClosing(self, event):
        meta = ExperimentSettings.getInstance()
        #first check whether this is the only instnace then it cant be deleted
        stk_list = meta.get_field_instances('StockCulture|Sample')
        
        if len(stk_list) == 1:
            event.Veto()
            dlg = wx.MessageDialog(self, 'Can not delete the only instance', 'Deleting..', wx.OK| wx.ICON_STOP)
            dlg.ShowModal()
            return
        
        tab_caption =  self.notebook.GetPageText(event.GetSelection())
        self.stk_id = tab_caption.split(':')[1].strip()
        
        dlg = wx.MessageDialog(self, 'Deleting Stock Culture no %s' %self.stk_id, 'Deleting..', wx.OK| wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_OK:
            #remove the instances 
            meta.remove_field('StockCulture|Sample|CellLine|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|ATCCref|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Organism|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Gender|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Age|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Organ|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Tissue|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Phenotype|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Genotype|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Strain|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|PassageNumber|%s'%str(self.stk_id), notify_subscribers =False)
            meta.remove_field('StockCulture|Sample|Density|%s'%str(self.stk_id))
  

    def onAddStockCulturePage(self, event):
        # This button is active only at the first instance
        stk_id = 1
        panel = StockCulturePanel(self.notebook,stk_id)
        self.notebook.AddPage(panel, 'StockCulture No: %s'% stk_id, True)        
        #Disable the add button
        self.addStockCulturePageBtn.Disable()
        

class StockCulturePanel(wx.Panel):
    def __init__(self, parent, stk_id=None):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
        
        if stk_id is None:  
            stk_list = meta.get_field_instances('StockCulture|Sample|')
            #Find the all instances of stkroscope
            if stk_list:
                stk_id =  max(map(int, stk_list))+1
            else:
                stk_id = 1
        self.stk_id = stk_id
        
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
    
        #----------- Labels and Text Controler-------        
        # Cell Line Name
        cellLineTAG = 'StockCulture|Sample|CellLine|%s'%str(self.stk_id)
        self.settings_controls[cellLineTAG] = wx.TextCtrl(self.sw, value=meta.get_field(cellLineTAG, default=''))
        self.settings_controls[cellLineTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[cellLineTAG].SetToolTipString('Cell Line selection')
        cellLineTXT = wx.StaticText(self.sw, -1, 'Cell Line')
        cellLineTXT.SetForegroundColour((0,0,0))
        fgs.Add(cellLineTXT, 0)
        fgs.Add(self.settings_controls[cellLineTAG], 0, wx.EXPAND)
        
        
        #meta.add_subscriber(lambda(evt): cellLineTXT.SetForegroundColour((0,0,0)), cellLineTAG)
        # ATCC reference
        acttTAG = 'StockCulture|Sample|ATCCref|%s'%str(self.stk_id)
        self.settings_controls[acttTAG] = wx.TextCtrl(self.sw, value=meta.get_field(acttTAG, default=''))
        self.settings_controls[acttTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[acttTAG].SetToolTipString('ATCC reference')
        fgs.Add(wx.StaticText(self.sw, -1, 'ATCC Reference'), 0)
        fgs.Add(self.settings_controls[acttTAG], 0, wx.EXPAND) 
        # Taxonomic ID
        taxIdTAG = 'StockCulture|Sample|Organism|%s'%str(self.stk_id)
        self.settings_controls[taxIdTAG] = wx.Choice(self.sw, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
        if meta.get_field(taxIdTAG) is not None:
            self.settings_controls[taxIdTAG].SetStringSelection(meta.get_field(taxIdTAG))
        self.settings_controls[taxIdTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[taxIdTAG].SetToolTipString('Taxonomic ID of the species')
        fgs.Add(wx.StaticText(self.sw, -1, 'Organism'), 0)
        fgs.Add(self.settings_controls[taxIdTAG], 0, wx.EXPAND)
        # Gender
        gendTAG = 'StockCulture|Sample|Gender|%s'%str(self.stk_id)
        self.settings_controls[gendTAG] = wx.Choice(self.sw, -1,  choices=['Male', 'Female', 'Neutral'])
        if meta.get_field(gendTAG) is not None:
            self.settings_controls[gendTAG].SetStringSelection(meta.get_field(gendTAG))
        self.settings_controls[gendTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[gendTAG].SetToolTipString('Gender of the organism')
        fgs.Add(wx.StaticText(self.sw, -1, 'Gender'), 0)
        fgs.Add(self.settings_controls[gendTAG], 0, wx.EXPAND)        
        # Age
        ageTAG ='StockCulture|Sample|Age|%s'%str(self.stk_id)
        self.settings_controls[ageTAG] = wx.TextCtrl(self.sw, value=meta.get_field(ageTAG, default=''))
        self.settings_controls[ageTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[ageTAG].SetToolTipString('Age of the organism in days when the cells were collected. .')
        fgs.Add(wx.StaticText(self.sw, -1, 'Age of organism (days)'), 0)
        fgs.Add(self.settings_controls[ageTAG], 0, wx.EXPAND)
        # Organ
        organTAG = 'StockCulture|Sample|Organ|%s'%str(self.stk_id)
        self.settings_controls[organTAG] = wx.TextCtrl(self.sw, value=meta.get_field(organTAG, default=''))
        self.settings_controls[organTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[organTAG].SetToolTipString('Organ name from where the cell were collected. eg. Heart, Lung, Bone etc')
        fgs.Add(wx.StaticText(self.sw, -1, 'Organ'), 0)
        fgs.Add(self.settings_controls[organTAG], 0, wx.EXPAND)
        # Tissue
        tissueTAG = 'StockCulture|Sample|Tissue|%s'%str(self.stk_id)
        self.settings_controls[tissueTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tissueTAG, default=''))
        self.settings_controls[tissueTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tissueTAG].SetToolTipString('Tissue from which the cells were collected')
        fgs.Add(wx.StaticText(self.sw, -1, 'Tissue'), 0)
        fgs.Add(self.settings_controls[tissueTAG], 0, wx.EXPAND)
        # Pheotype
        phtypTAG = 'StockCulture|Sample|Phenotype|%s'%str(self.stk_id)
        self.settings_controls[phtypTAG] = wx.TextCtrl(self.sw, value=meta.get_field(phtypTAG, default=''))
        self.settings_controls[phtypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[phtypTAG].SetToolTipString('Phenotypic examples Colour Height OR any other value descriptor')
        fgs.Add(wx.StaticText(self.sw, -1, 'Phenotype'), 0)
        fgs.Add(self.settings_controls[phtypTAG], 0, wx.EXPAND)
        # Genotype
        gentypTAG = 'StockCulture|Sample|Genotype|%s'%str(self.stk_id)
        self.settings_controls[gentypTAG] = wx.TextCtrl(self.sw, value=meta.get_field(gentypTAG, default=''))
        self.settings_controls[gentypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[gentypTAG].SetToolTipString('Wild type or mutant etc. (single word)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Genotype'), 0)
        fgs.Add(self.settings_controls[gentypTAG], 0, wx.EXPAND)
        # Strain
        strainTAG = 'StockCulture|Sample|Strain|%s'%str(self.stk_id)
        self.settings_controls[strainTAG] = wx.TextCtrl(self.sw, value=meta.get_field(strainTAG, default=''))
        self.settings_controls[strainTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[strainTAG].SetToolTipString('Starin of that cell line eGFP, Wild type etc')
        fgs.Add(wx.StaticText(self.sw, -1, 'Strain'), 0)
        fgs.Add(self.settings_controls[strainTAG], 0, wx.EXPAND)
        #  Passage Number
        passTAG = 'StockCulture|Sample|PassageNumber|%s'%str(self.stk_id)
        self.settings_controls[passTAG] = wx.TextCtrl(self.sw, value=meta.get_field(passTAG, default=''))
        self.settings_controls[passTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[passTAG].SetToolTipString('Numeric value of the passage of the cells under investigation')
        fgs.Add(wx.StaticText(self.sw, -1, 'Passage Number'), 0)
        fgs.Add(self.settings_controls[passTAG], 0, wx.EXPAND)
        #  Cell Density
        densityTAG = 'StockCulture|Sample|Density|%s'%str(self.stk_id)
        self.settings_controls[densityTAG] = wx.TextCtrl(self.sw, value=meta.get_field(densityTAG, default=''))
        self.settings_controls[densityTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[densityTAG].SetToolTipString('Numeric value of the cell density at the culture flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Cell Density'), 0)
        fgs.Add(self.settings_controls[densityTAG], 0, wx.EXPAND)
        # Duplicate button        
        self.copyStockCulturePageBtn = wx.Button(self.sw, -1, label="Duplicate Settings")
        self.copyStockCulturePageBtn.Bind(wx.EVT_BUTTON, self.onCopyStockCulturePage)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(self.copyStockCulturePageBtn, 0, wx.EXPAND)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def onCopyStockCulturePage(self, event):
            
        meta = ExperimentSettings.getInstance()
        #Get the maximum microscope id from the list
        stk_list = meta.get_field_instances('StockCulture|Sample|')
        
        if not stk_list:
            dial = wx.MessageDialog(None, 'No instance to duplicate', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
                    
        new_stk_id =  max(map(int, stk_list))+1
        #Copy all data fields from the selected instances
        meta.set_field('StockCulture|Sample|CellLine|%s'%str(new_stk_id),    meta.get_field('StockCulture|Sample|CellLine|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|ATCCref|%s'%str(new_stk_id),     meta.get_field('StockCulture|Sample|ATCCref|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Organism|%s'%str(new_stk_id),       meta.get_field('StockCulture|Sample|Organism|%s'%str(self.stk_id)), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Gender|%s'%str(new_stk_id),      meta.get_field('StockCulture|Sample|Gender|%s'%str(self.stk_id)), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Age|%s'%str(new_stk_id),         meta.get_field('StockCulture|Sample|Age|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Organ|%s'%str(new_stk_id),       meta.get_field('StockCulture|Sample|Organ|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Tissue|%s'%str(new_stk_id),       meta.get_field('StockCulture|Sample|Tissue|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Phenotype|%s'%str(new_stk_id),   meta.get_field('StockCulture|Sample|Phenotype|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Genotype|%s'%str(new_stk_id),    meta.get_field('StockCulture|Sample|Genotype|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Strain|%s'%str(new_stk_id),      meta.get_field('StockCulture|Sample|Strain|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|PassageNumber|%s'%str(new_stk_id), meta.get_field('StockCulture|Sample|PassageNumber|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        meta.set_field('StockCulture|Sample|Density|%s'%str(new_stk_id),      meta.get_field('StockCulture|Sample|Density|%s'%str(self.stk_id), default=''))
      
        panel = StockCulturePanel(self.Parent, new_stk_id)
        self.Parent.AddPage(panel, 'StockCulture No: %s'% new_stk_id, True)
    
    def validate(self):
        pass
    
    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:                
            meta.set_field(tag, ctrl.GetValue())

########################################################################        
################## MICROSCOPE SETTING PANEL         ####################
########################################################################
class MicroscopeSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style= fnb.FNB_VC8)
        
        # Get all the previously encoded Microscope pages and re-Add them as pages
        mic_list = meta.get_field_instances('Instrument|Microscope|')
        
        for mic_id in sorted(mic_list):
            panel = MicroscopePanel(self.notebook,mic_id)
            self.notebook.AddPage(panel, 'Microscope No: %s'% mic_id, True)
            
        self.addMicroscopePageBtn = wx.Button(self, label="Add Microscope")
        self.addMicroscopePageBtn.Bind(wx.EVT_BUTTON, self.onAddMicroscopePage)
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.onTabClosing)
        
        # at least one instance of the microscope exists so uers can copy from that instead of creating a new one
        if mic_list:
            self.addMicroscopePageBtn.Disable()
         
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addMicroscopePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
        
    def onTabClosing(self, event):
        meta = ExperimentSettings.getInstance()
        #first check whether this is the only instnace then it cant be deleted
        mic_list = meta.get_field_instances('Instrument|Microscope|')
        
        if len(mic_list) == 1:
            event.Veto()
            dlg = wx.MessageDialog(self, 'Can not delete the only instance', 'Deleting..', wx.OK| wx.ICON_STOP)
            dlg.ShowModal()
            return
        
        tab_caption =  self.notebook.GetPageText(event.GetSelection())
        self.mic_id = tab_caption.split(':')[1].strip()
        
        dlg = wx.MessageDialog(self, 'Deleting Microscope no %s' %self.mic_id, 'Deleting..', wx.OK | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_OK:                    
            #remove the instances 
            meta.remove_field('Instrument|Microscope|Manufacter|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Model|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Type|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|LightSource|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Detector|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|LensApprture|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|LensCorr|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|IllumType|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Mode|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Immersion|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Correction|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|NominalMagnification|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|CalibratedMagnification|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|WorkDistance|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Filter|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Software|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Temp|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|C02|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Humidity|%s'%str(self.mic_id), notify_subscribers =False)
            meta.remove_field('Instrument|Microscope|Pressure|'+str(self.mic_id))

    def onAddMicroscopePage(self, event):
        # This button is active only at the first instance
        mic_id = 1
        panel = MicroscopePanel(self.notebook,mic_id)
        self.notebook.AddPage(panel, 'Microscope No: %s'% mic_id, True)        
        #Disable the add button
        self.addMicroscopePageBtn.Disable()
        


class MicroscopePanel(wx.Panel):
    def __init__(self, parent, mic_id=None):
        '''
        mic_id -- the micrscope id subtag to use to populate this form
        '''
        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        wx.Panel.__init__(self, parent=parent)
        
        if mic_id is None:
            mic_list = meta.get_field_instances('Instrument|Microscope|')
            #Find the all instances of microscope
            if mic_list:
                mic_id =  max(map(int, mic_list))+1
            else:
                mic_id = 1            
        self.mic_id = mic_id
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        heading = 'Microscope Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        
        #--Manufacture--#
        micromfgTAG = 'Instrument|Microscope|Manufacter|'+str(self.mic_id)
        self.settings_controls[micromfgTAG] = wx.Choice(self.sw, -1,  choices=['Zeiss','Olympus','Nikon', 'MDS', 'GE'])
        if meta.get_field(micromfgTAG) is not None:
            self.settings_controls[micromfgTAG].SetStringSelection(meta.get_field(micromfgTAG))
        self.settings_controls[micromfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)    
        self.settings_controls[micromfgTAG].SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(self.settings_controls[micromfgTAG], 0, wx.EXPAND)
        #--Model--#
        micromdlTAG = 'Instrument|Microscope|Model|'+str(self.mic_id)
        self.settings_controls[micromdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(micromdlTAG, default=''))
        self.settings_controls[micromdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[micromdlTAG].SetToolTipString('Model number of the microscope')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(self.settings_controls[micromdlTAG], 0, wx.EXPAND)
        #--Microscope type--#
        microtypTAG = 'Instrument|Microscope|Type|'+str(self.mic_id)
        self.settings_controls[microtypTAG] = wx.Choice(self.sw, -1,  choices=['Upright', 'Inverted', 'Confocal'])
        if meta.get_field(microtypTAG) is not None:
            self.settings_controls[microtypTAG].SetStringSelection(meta.get_field(microtypTAG))
        self.settings_controls[microtypTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        self.settings_controls[microtypTAG].SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Microscope Type'), 0)
        fgs.Add(self.settings_controls[microtypTAG], 0, wx.EXPAND)
        #--Light source--#
        microlgtTAG = 'Instrument|Microscope|LightSource|'+str(self.mic_id)
        self.settings_controls[microlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Filament', 'Arc', 'LightEmittingDiode'])
        if meta.get_field(microlgtTAG) is not None:
            self.settings_controls[microlgtTAG].SetStringSelection(meta.get_field(microlgtTAG))
        self.settings_controls[microlgtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        self.settings_controls[microlgtTAG].SetToolTipString('e.g. Laser, Filament, Arc, Light Emitting Diode')
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(self.settings_controls[microlgtTAG], 0, wx.EXPAND)
        #--Detector--#
        microdctTAG = 'Instrument|Microscope|Detector|'+str(self.mic_id)
        self.settings_controls[microdctTAG] = wx.Choice(self.sw, -1,  choices=['CCD', 'Intensified-CCD', 'Analog-Video', 'Spectroscopy', 'Life-time-imaging', 'Correlation-Spectroscopy', 'FTIR', 'EM-CCD', 'APD', 'CMOS'])
        if meta.get_field(microdctTAG) is not None:
            self.settings_controls[microdctTAG].SetStringSelection(meta.get_field(microdctTAG))
        self.settings_controls[microdctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microdctTAG].SetToolTipString('Type of detector used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Detector'), 0)
        fgs.Add(self.settings_controls[microdctTAG], 0, wx.EXPAND)
        #--Lense Aperture--#
        microlnsappTAG = 'Instrument|Microscope|LensApprture|'+str(self.mic_id)
        self.settings_controls[microlnsappTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microlnsappTAG, default=''))
        self.settings_controls[microlnsappTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microlnsappTAG].SetToolTipString('A floating value of lens numerical aperture')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lens Aperture'), 0)
        fgs.Add(self.settings_controls[microlnsappTAG], 0, wx.EXPAND)
        # Lense Correction
        microlnscorrTAG = 'Instrument|Microscope|LensCorr|'+str(self.mic_id)
        self.settings_controls[microlnscorrTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(microlnscorrTAG) is not None:
            self.settings_controls[microlnscorrTAG].SetStringSelection(meta.get_field(microlnscorrTAG))
        self.settings_controls[microlnscorrTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microlnscorrTAG].SetToolTipString('Yes/No')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lens Correction'), 0)
        fgs.Add(self.settings_controls[microlnscorrTAG], 0, wx.EXPAND)
        #--Illumination Type--#
        microIllTAG = 'Instrument|Microscope|IllumType|'+str(self.mic_id)
        self.settings_controls[microIllTAG] = wx.Choice(self.sw, -1,  choices=['Transmitted','Epifluorescence','Oblique','NonLinear'])
        if meta.get_field(microIllTAG) is not None:
            self.settings_controls[microIllTAG].SetStringSelection(meta.get_field(microIllTAG))
        self.settings_controls[microIllTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microIllTAG].SetToolTipString('Type of illumunation used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Illumination Type'), 0)
        fgs.Add(self.settings_controls[microIllTAG], 0, wx.EXPAND)
        #--Mode--#
        microModTAG = 'Instrument|Microscope|Mode|'+str(self.mic_id)
        self.settings_controls[microModTAG] = wx.Choice(self.sw, -1,  choices=['WideField','LaserScanningMicroscopy', 'LaserScanningConfocal', 'SpinningDiskConfocal', 'SlitScanConfocal', 'MultiPhotonMicroscopy', 'StructuredIllumination','SingleMoleculeImaging', 'TotalInternalReflection', 'FluorescenceLifetime', 'SpectralImaging', 'FluorescenceCorrelationSpectroscopy', 'NearFieldScanningOpticalMicroscopy', 'SecondHarmonicGenerationImaging', 'Timelapse', 'Other'])
        if meta.get_field(microModTAG) is not None:
            self.settings_controls[microModTAG].SetStringSelection(meta.get_field(microModTAG))
        self.settings_controls[microModTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microModTAG].SetToolTipString('Mode of the microscope')
        fgs.Add(wx.StaticText(self.sw, -1, 'Mode'), 0)
        fgs.Add(self.settings_controls[microModTAG], 0, wx.EXPAND)
        #--Immersion--#
        microImmTAG = 'Instrument|Microscope|Immersion|'+str(self.mic_id)
        self.settings_controls[microImmTAG] = wx.Choice(self.sw, -1,  choices=['Oil', 'Water', 'WaterDipping', 'Air', 'Multi', 'Glycerol', 'Other', 'Unkonwn'])
        if meta.get_field(microImmTAG) is not None:
            self.settings_controls[microImmTAG].SetStringSelection(meta.get_field(microImmTAG))
        self.settings_controls[microImmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microImmTAG].SetToolTipString('Immersion medium used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
        fgs.Add(self.settings_controls[microImmTAG], 0, wx.EXPAND)
        #--Correction--#
        microCorrTAG = 'Instrument|Microscope|Correction|'+str(self.mic_id)
        self.settings_controls[microCorrTAG] = wx.Choice(self.sw, -1,  choices=['UV', 'PlanApo', 'PlanFluor', 'SuperFluor', 'VioletCorrected', 'Unknown'])
        if meta.get_field(microCorrTAG) is not None:
            self.settings_controls[microCorrTAG].SetStringSelection(meta.get_field(microCorrTAG))
        self.settings_controls[microCorrTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microCorrTAG].SetToolTipString('Lense correction used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
        fgs.Add(self.settings_controls[microCorrTAG], 0, wx.EXPAND)
        #--Nominal Magnification--#
        microNmgTAG = 'Instrument|Microscope|NominalMagnification|'+str(self.mic_id)
        self.settings_controls[microNmgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microNmgTAG, default=''))
        self.settings_controls[microNmgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microNmgTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
        fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
        fgs.Add(self.settings_controls[microNmgTAG], 0, wx.EXPAND)
        # Calibrated Magnification
        microCalTAG = 'Instrument|Microscope|CalibratedMagnification|'+str(self.mic_id)
        self.settings_controls[microCalTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCalTAG, default=''))
        self.settings_controls[microCalTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microCalTAG].SetToolTipString('The magnification of the lens as measured by a calibration process- i.e. 59.987 for a 60X lens')
        fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
        fgs.Add(self.settings_controls[microCalTAG], 0, wx.EXPAND)
        #--Working distance--#
        microWrkTAG = 'Instrument|Microscope|WorkDistance|'+str(self.mic_id)
        self.settings_controls[microWrkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microWrkTAG, default=''))
        self.settings_controls[microWrkTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microWrkTAG].SetToolTipString('The working distance of the lens expressed as a floating point (real) number. Units are um')
        fgs.Add(wx.StaticText(self.sw, -1, 'Working Distance (uM)'), 0)
        fgs.Add(self.settings_controls[microWrkTAG], 0, wx.EXPAND)
        #--Filter used--#
        microFltTAG = 'Instrument|Microscope|Filter|'+str(self.mic_id)
        self.settings_controls[microFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(microFltTAG) is not None:
            self.settings_controls[microFltTAG].SetStringSelection(meta.get_field(microFltTAG))
        self.settings_controls[microFltTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microFltTAG].SetToolTipString('Whether filter was used or not')
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
        fgs.Add(self.settings_controls[microFltTAG], 0, wx.EXPAND)
        #--Software--#
        microSoftTAG = 'Instrument|Microscope|Software|'+str(self.mic_id)
        self.settings_controls[microSoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microSoftTAG, default=''))
        self.settings_controls[microSoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microSoftTAG].SetToolTipString('Name and version of software used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Software'), 0)
        fgs.Add(self.settings_controls[microSoftTAG], 0, wx.EXPAND)
        #-- Heading --#
        heading = 'Incubator Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #--Temperature--#
        microTempTAG = 'Instrument|Microscope|Temp|'+str(self.mic_id)
        self.settings_controls[microTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microTempTAG, default=''))
        self.settings_controls[microTempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microTempTAG].SetToolTipString('Temperature of the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
        fgs.Add(self.settings_controls[microTempTAG], 0, wx.EXPAND)
        #--Carbondioxide--#
        microCarbonTAG = 'Instrument|Microscope|C02|'+str(self.mic_id)
        self.settings_controls[microCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCarbonTAG, default=''))
        self.settings_controls[microCarbonTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
        fgs.Add(self.settings_controls[microCarbonTAG], 0, wx.EXPAND)
        #--Humidity--#
        microHumTAG = 'Instrument|Microscope|Humidity|'+str(self.mic_id)
        self.settings_controls[microHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microHumTAG, default=''))
        self.settings_controls[microHumTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microHumTAG].SetToolTipString('Humidity at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
        fgs.Add(self.settings_controls[microHumTAG], 0, wx.EXPAND)
        #--Pressure--#
        microPressTAG = 'Instrument|Microscope|Pressure|'+str(self.mic_id)
        self.settings_controls[microPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microPressTAG, default=''))
        self.settings_controls[microPressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microPressTAG].SetToolTipString('Pressure at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
        fgs.Add(self.settings_controls[microPressTAG], 0, wx.EXPAND)
        #-- button --#
        self.copyMicroscopePageBtn = wx.Button(self.sw, -1, label="Duplicate Settings")
        self.copyMicroscopePageBtn.Bind(wx.EVT_BUTTON, self.onCopyMicroscopePage)
        
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)        
        fgs.Add(self.copyMicroscopePageBtn, 0, wx.EXPAND)

      
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def onCopyMicroscopePage(self, event):
      
        meta = ExperimentSettings.getInstance()
        #Get the maximum microscope id from the list
        mic_list = meta.get_field_instances('Instrument|Microscope|')
        
        if not mic_list:
            dial = wx.MessageDialog(None, 'No instance to duplicate', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
                    
        new_mic_id =  max(map(int, mic_list))+1
        #Copy all data fields from the selected microscope to traget microscope
        meta.set_field('Instrument|Microscope|Manufacter|%s'%str(new_mic_id),               meta.get_field('Instrument|Microscope|Manufacter|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Model|%s'%str(new_mic_id),                    meta.get_field('Instrument|Microscope|Model|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Type|%s'%str(new_mic_id),                     meta.get_field('Instrument|Microscope|Type|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|LightSource|%s'%str(new_mic_id),              meta.get_field('Instrument|Microscope|LightSource|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Detector|%s'%str(new_mic_id),                 meta.get_field('Instrument|Microscope|Detector|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|LensApprture|%s'%str(new_mic_id),             meta.get_field('Instrument|Microscope|LensApprture|%s'%str(self.mic_id), default=''), notify_subscribers =False)      
        meta.set_field('Instrument|Microscope|LensCorr|%s'%str(new_mic_id),                 meta.get_field('Instrument|Microscope|LensCorr|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|IllumType|%s'%str(new_mic_id),                meta.get_field('Instrument|Microscope|IllumType|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Mode|%s'%str(new_mic_id),                     meta.get_field('Instrument|Microscope|Mode|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Immersion|%s'%str(new_mic_id),                meta.get_field('Instrument|Microscope|Immersion|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Correction|%s'%str(new_mic_id),               meta.get_field('Instrument|Microscope|Correction|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|NominalMagnification|%s'%str(new_mic_id),     meta.get_field('Instrument|Microscope|NominalMagnification|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|CalibratedMagnification|%s'%str(new_mic_id),  meta.get_field('Instrument|Microscope|CalibratedMagnification|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|WorkDistance|%s'%str(new_mic_id),             meta.get_field('Instrument|Microscope|WorkDistance|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Filter|%s'%str(new_mic_id),                   meta.get_field('Instrument|Microscope|Filter|%s'%str(self.mic_id)), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Software|%s'%str(new_mic_id),                 meta.get_field('Instrument|Microscope|Software|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Temp|%s'%str(new_mic_id),                     meta.get_field('Instrument|Microscope|Temp|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|C02|%s'%str(new_mic_id),                      meta.get_field('Instrument|Microscope|C02|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Humidity|%s'%str(new_mic_id),                 meta.get_field('Instrument|Microscope|Humidity|%s'%str(self.mic_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Microscope|Pressure|%s'%str(new_mic_id),                 meta.get_field('Instrument|Microscope|Pressure|%s'%str(self.mic_id), default=''))
        
        panel = MicroscopePanel(self.Parent, new_mic_id)
        self.Parent.AddPage(panel, 'Microscope: %s'% new_mic_id)
        
        
    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()
        
        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
            

########################################################################        
################## FLOW CYTOMETER SETTING PANEL         ####################
########################################################################
class FlowcytometerSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        
        ## Get all the previously encoded Flowcytometer pages and re-Add them as pages
        flow_list = meta.get_field_instances('Instrument|Flowcytometer|')
               
        for flow_id in sorted(flow_list):
            panel = FlowcytometerPanel(self.notebook,flow_id)
            self.notebook.AddPage(panel, 'Flowcytometer No: %s'% flow_id, True)
            
        self.addFlowcytometerPageBtn = wx.Button(self, label="Add Flowcytometer")
        self.addFlowcytometerPageBtn.Bind(wx.EVT_BUTTON, self.onAddFlowcytometerPage)
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.onTabClosing)
        
        # at least one instance of the flowroscope exists so uers can copy from that instead of creating a new one
        if flow_list:
            self.addFlowcytometerPageBtn.Disable()
         
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addFlowcytometerPageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
    
    def onTabClosing(self, event):
        meta = ExperimentSettings.getInstance()
        #first check whether this is the only instnace then it cant be deleted
        flow_list = meta.get_field_instances('Instrument|Flowcytometer|')
        
        if len(flow_list) == 1:
            event.Veto()
            dlg = wx.MessageDialog(self, 'Can not delete the only instance', 'Deleting..', wx.OK| wx.ICON_STOP)
            dlg.ShowModal()
            return
        
        tab_caption =  self.notebook.GetPageText(event.GetSelection())
        self.flow_id = tab_caption.split(':')[1].strip()
        
        dlg = wx.MessageDialog(self, 'Deleting Flowcytometer no %s' %self.flow_id, 'Deleting..', wx.OK | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_OK:  
            meta.remove_field('Instrument|Flowcytometer|Manufacter|%s'%str(self.flow_id), notify_subscribers =False)
            meta.remove_field('Instrument|Flowcytometer|Model|%s'%str(self.flow_id), notify_subscribers =False)
            meta.remove_field('Instrument|Flowcytometer|Type|%s'%str(self.flow_id), notify_subscribers =False)
            meta.remove_field('Instrument|Flowcytometer|LightSource|%s'%str(self.flow_id), notify_subscribers =False)
            meta.remove_field('Instrument|Flowcytometer|Detector|%s'%str(self.flow_id), notify_subscribers =False)
            meta.remove_field('Instrument|Flowcytometer|Filter|%s'%str(self.flow_id))

        
    def onAddFlowcytometerPage(self, event):
        # This button is active only at the first instance
        flow_id = 1
        panel = FlowcytometerPanel(self.notebook,flow_id)
        self.notebook.AddPage(panel, 'Flowcytometer No: %s'% flow_id, True)        
        #Disable the add button
        self.addFlowcytometerPageBtn.Disable()
        

class FlowcytometerPanel(wx.Panel):
    def __init__(self, parent, flow_id=None):
        '''
        flow_id -- the flowrscope id subtag to use to populate this form
        '''

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
        
        if flow_id is None:
            
            flow_list = meta.get_field_instances('Instrument|Flowcytometer|')
        
            #Find the all instances of flowroscope
            if flow_list:
                flow_id =  max(map(int, flow_list))+1
            else:
                flow_id = 1
            
        self.flow_id = flow_id
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        #-- Heading --#
        heading = 'Flowcytometer Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #--Manufacture--#
        flowmfgTAG = 'Instrument|Flowcytometer|Manufacter|'+str(self.flow_id)
        self.settings_controls[flowmfgTAG] = wx.Choice(self.sw, -1,  choices=['Beckman','BD-Biosciences'])
        if meta.get_field(flowmfgTAG) is not None:
            self.settings_controls[flowmfgTAG].SetStringSelection(meta.get_field(flowmfgTAG))
        self.settings_controls[flowmfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowmfgTAG].SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(self.settings_controls[flowmfgTAG], 0, wx.EXPAND)
        #--Model--#
        flowmdlTAG = 'Instrument|Flowcytometer|Model|'+str(self.flow_id)
        self.settings_controls[flowmdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(flowmdlTAG, default=''))
        self.settings_controls[flowmdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[flowmdlTAG].SetToolTipString('Model number of the Flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(self.settings_controls[flowmdlTAG], 0, wx.EXPAND)
        #--Flowcytometer type--#
        flowtypTAG = 'Instrument|Flowcytometer|Type|'+str(self.flow_id)
        self.settings_controls[flowtypTAG] = wx.Choice(self.sw, -1,  choices=['Stream-in-air', 'cuvette'])
        if meta.get_field(flowtypTAG) is not None:
            self.settings_controls[flowtypTAG].SetStringSelection(meta.get_field(flowtypTAG))
        self.settings_controls[flowtypTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowtypTAG].SetToolTipString('Type of flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Flowcytometer Type'), 0)
        fgs.Add(self.settings_controls[flowtypTAG], 0, wx.EXPAND)
        #--Light source--#
        flowlgtTAG = 'Instrument|Flowcytometer|LightSource|'+str(self.flow_id)
        self.settings_controls[flowlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Beam'])
        if meta.get_field(flowlgtTAG) is not None:
            self.settings_controls[flowlgtTAG].SetStringSelection(meta.get_field(flowlgtTAG))
        self.settings_controls[flowlgtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowlgtTAG].SetToolTipString('Light source of the flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(self.settings_controls[flowlgtTAG], 0, wx.EXPAND)
        #--Detector--#
        flowdctTAG = 'Instrument|Flowcytometer|Detector|'+str(self.flow_id)
        self.settings_controls[flowdctTAG] = wx.Choice(self.sw, -1,  choices=['PhotoMultiplierTube', 'FluorescentDetectors'])
        if meta.get_field(flowdctTAG) is not None:
            self.settings_controls[flowdctTAG].SetStringSelection(meta.get_field(flowdctTAG))
        self.settings_controls[flowdctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowdctTAG].SetToolTipString('Type of detector used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Detector'), 0)
        fgs.Add(self.settings_controls[flowdctTAG], 0, wx.EXPAND)
        #--Filter used--#
        flowFltTAG = 'Instrument|Flowcytometer|Filter|'+str(self.flow_id)
        self.settings_controls[flowFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(flowFltTAG) is not None:
            self.settings_controls[flowFltTAG].SetStringSelection(meta.get_field(flowFltTAG))
        self.settings_controls[flowFltTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowFltTAG].SetToolTipString('Whether filter was used or not')
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
        fgs.Add(self.settings_controls[flowFltTAG], 0, wx.EXPAND)

        #-- Button --#
        
        self.copyFlowcytometerPageBtn = wx.Button(self.sw, -1, label="Duplicate Settings")
        self.copyFlowcytometerPageBtn.Bind(wx.EVT_BUTTON, self.onCopyFlowcytometerPage)
        
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(self.copyFlowcytometerPageBtn, 0, wx.EXPAND)
        

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        
    def onCopyFlowcytometerPage(self, event):
        meta = ExperimentSettings.getInstance()
        
        
        #Get the maximum flowroscope id from the list
        flow_list = meta.get_field_instances('Instrument|Flowcytometer|')
        
        if not flow_list:
            dial = wx.MessageDialog(None, 'No instance to duplicate', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        
        new_flow_id =  max(map(int, flow_list))+1
        
        #Copy all data fields from the selected flowroscope to traget flowroscope
        
        meta.set_field('Instrument|Flowcytometer|Manufacter|%s'%str(new_flow_id),    meta.get_field('Instrument|Flowcytometer|Manufacter|%s'%str(self.flow_id)), notify_subscribers =False)
        meta.set_field('Instrument|Flowcytometer|Model|%s'%str(new_flow_id),         meta.get_field('Instrument|Flowcytometer|Model|%s'%str(self.flow_id), default=''), notify_subscribers =False)
        meta.set_field('Instrument|Flowcytometer|Type|%s'%str(new_flow_id),          meta.get_field('Instrument|Flowcytometer|Type|%s'%str(self.flow_id)), notify_subscribers =False)
        meta.set_field('Instrument|Flowcytometer|LightSource|%s'%str(new_flow_id),   meta.get_field('Instrument|Flowcytometer|LightSource|%s'%str(self.flow_id)), notify_subscribers =False)
        meta.set_field('Instrument|Flowcytometer|Detector|%s'%str(new_flow_id),      meta.get_field('Instrument|Flowcytometer|Detector|%s'%str(self.flow_id)), notify_subscribers =False)
        meta.set_field('Instrument|Flowcytometer|Filter|%s'%str(new_flow_id),        meta.get_field('Instrument|Flowcytometer|Filter|%s'%str(self.flow_id)))
        
        panel = FlowcytometerPanel(self.Parent, new_flow_id)
        self.Parent.AddPage(panel, 'Flowcytometer: %s'% new_flow_id)
    


    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
 
#########################################################################        
###################     PLATE SETTING PANEL          ####################
#########################################################################	    
class PlateSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = meta.get_field_instances('ExptVessel|Plate')
        # figure out the group numbers from this list
        plategrp = []
        for id in field_ids:
            plategrp.append(meta.get_field('ExptVessel|Plate|GroupNo|%s'%(id)))
        pltgrp_list = set(plategrp)

        for pltgrp_id in sorted(pltgrp_list):
            panel = PlateConfigPanel(self.notebook,pltgrp_id)
            self.notebook.AddPage(panel, 'Stack No: %s'% pltgrp_id, True)
            
                
        self.addPlateGrpPageBtn = wx.Button(self, label="Add New Stack of Plates")
        self.addPlateGrpPageBtn.Bind(wx.EVT_BUTTON, self.onAddPlateGroupPage)
      
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addPlateGrpPageBtn  , 0, wx.ALL, 5)        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPlateGroupPage(self, event):
        # This function is called only for the first instance
        meta = ExperimentSettings.getInstance()
        # Get all the previously encoded pages 
        field_ids = meta.get_field_instances('ExptVessel|Plate')
        # figure out the group numbers from this list
        plategrp = []
        for id in field_ids:
            plategrp.append(meta.get_field('ExptVessel|Plate|GroupNo|%s'%(id)))
        pltgrp_list = set(plategrp)
        
        # find out max Group number to be assigned
        if pltgrp_list:
            pltgrp_id =  max(map(int, pltgrp_list))+1
        else:
            pltgrp_id = 1
                    
        # create the first page
        panel = PlateConfigPanel(self.notebook,pltgrp_id)
        self.notebook.AddPage(panel, 'Stack No: %s'% pltgrp_id, True)
        # disable the add button
        self.addPlateGrpPageBtn.Disable()
        
##---- Plate Configuration Panel --------#         
class PlateConfigPanel(wx.Panel):
    def __init__(self, parent, plgrp_id=None):
        
        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
        
      
        # find the Done status for this group
        # get the group number                
        self.plgrp_id = plgrp_id

        # get all the plate instances for this group 
        inc_plate_ids = []
        
        for id in meta.get_field_instances('ExptVessel|Plate'):     
            if (meta.get_field('ExptVessel|Plate|GroupNo|%s'%(id)) == self.plgrp_id):
                inc_plate_ids.append(id)
        
         # Make a scroll window
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)    
        
        #------- Heading ---#
        text = wx.StaticText(self.sw, -1, 'Plate Settings')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---- Plate number---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of plates in the stack'), 0)
        self.platenum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_plate_ids:
            self.platenum.Enable() 
        else:
            self.platenum.SetStringSelection(meta.get_field('ExptVessel|Plate|Number|'+str(inc_plate_ids[0])))
            self.platenum.Disable()            
        fgs.Add(self.platenum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_plate_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Plate|GroupName|%s'%str(inc_plate_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
            
        ##--Design--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Design'), 0)
        self.platedesign = wx.Choice(self.sw, -1, choices=WELL_NAMES_ORDERED, name='PlateDesign')
        for i, format in enumerate([WELL_NAMES[name] for name in WELL_NAMES_ORDERED]):
                self.platedesign.SetClientData(i, format)
        if not inc_plate_ids:
            self.platedesign.Enable()            
        else:
            self.platedesign.SetStringSelection(meta.get_field('ExptVessel|Plate|Design|%s'%str(inc_plate_ids[0])))
            self.platedesign.Disable()
        fgs.Add(self.platedesign, 0, wx.EXPAND)
                
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Coating'), 0)
        self.platecoat = wx.Choice(self.sw, -1, choices=['None','Collagen IV','Gelatin','Poly-L-Lysine','Poly-D-Lysine', 'Fibronectin', 'Laminin','Poly-D-Lysine + Laminin', 'Poly-L-Ornithine+Laminin'])
        if not inc_plate_ids:
            self.platecoat.Enable()
        else:
            self.platecoat.SetStringSelection(meta.get_field('ExptVessel|Plate|Coat|%s'%str(inc_plate_ids[0])))
            self.platecoat.Disable()
        fgs.Add(self.platecoat, 0, wx.EXPAND)
                    
        #--Plate Material--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Material'), 0)
        self.platematerial = wx.Choice(self.sw, -1, choices=['Plastic','Glass'])
        if not inc_plate_ids:
            self.platematerial.Enable()
        else:
            self.platematerial.SetStringSelection(meta.get_field('ExptVessel|Plate|Material|%s'%str(inc_plate_ids[0])))
            self.platematerial.Disable()
        fgs.Add(self.platematerial, 0, wx.EXPAND)
                
        #--Well Shape--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Well Shape'), 0)
        self.wellshape = wx.Choice(self.sw, -1, choices=['Square','Round','Oval'])
        if not inc_plate_ids:
            self.wellshape.Enable()
        else:
            self.wellshape.SetStringSelection(meta.get_field('ExptVessel|Plate|Shape|%s'%str(inc_plate_ids[0])))
            self.wellshape.Disable()
        fgs.Add(self.wellshape, 0, wx.EXPAND)
                
        #--Well Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Well Size (mm)'), 0)
        self.wellsize = wx.TextCtrl(self.sw, -1, value='')
        if not inc_plate_ids:
            self.wellsize.Enable()
        else:
            self.wellsize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Plate|Size|%s'%str(inc_plate_ids[0])))
            self.wellsize.Disable()
        fgs.Add(self.wellsize, 0, wx.EXPAND)

        
        ##-------------- Buttons -----------------------
        self.deletePlategroupPageBtn = wx.Button(self.sw, -1, label="Delete Stack")
        self.deletePlategroupPageBtn.Bind(wx.EVT_BUTTON, self.onDeletePlategroupPage)
        if not inc_plate_ids:
            self.deletePlategroupPageBtn.Disable()
        else:
            self.deletePlategroupPageBtn.Enable()
        
        self.createBtn = wx.Button(self.sw, -1, label="Create Stack")
        self.createBtn.Bind(wx.EVT_BUTTON, self.onCreatePlategroupPage)
        if inc_plate_ids:
            self.createBtn.Disable()
            
        fgs.Add(self.deletePlategroupPageBtn, 0, wx.EXPAND)
        fgs.Add(self.createBtn, 0, wx.EXPAND)             

        ##---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def onCreatePlategroupPage(self, event):
        
        # get all input from the fields
        meta = ExperimentSettings.getInstance()
        # get the users input for number of plates requried
        plate_count = int(self.platenum.GetStringSelection())
        ## TO DO: check whether this value being selected, if not show message!!
        
        plate_list = meta.get_field_instances('ExptVessel|Plate|')
        
        #Find the all instances of plate
        if plate_list:
            max_id =  max(map(int, plate_list))+1
        else:
            max_id = 1
        
        # save the input from the max instances         
        for plate_id in range(max_id, max_id+plate_count):
            
            id = 'plate%s'%(plate_id)
            plate_design = self.platedesign.GetClientData(self.platedesign.GetSelection())
    
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate(id, plate_design)
            else:
                PlateDesign.set_plate_format(id, plate_design)
        
            meta.set_field('ExptVessel|Plate|GroupNo|%s'%str(plate_id),    self.plgrp_id, notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|Number|%s'%str(plate_id),     self.platenum.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|GroupName|%s'%str(plate_id),  self.groupname.GetValue(), notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|Design|%s'%str(plate_id),     self.platedesign.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|Coat|%s'%str(plate_id),       self.platecoat.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|Material|%s'%str(plate_id),   self.platematerial.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|Shape|%s'%str(plate_id),      self.wellshape.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Plate|Size|%s'%str(plate_id),       self.wellsize.GetValue())

        
        # make all input fields disable
        self.platenum.Disable()
        self.groupname.Disable()
        self.platedesign.Disable()
        self.platecoat.Disable()
        self.platematerial.Disable()
        self.wellshape.Disable()
        self.wellsize.Disable()
        # make the copy and delete button active
        self.createBtn.Disable()
        #self.copyPlategroupPageBtn.Enable()
        self.deletePlategroupPageBtn.Enable()
        self.GrandParent.addPlateGrpPageBtn.Enable()
         
      
    def onDeletePlategroupPage(self, event):

        dlg = wx.MessageDialog(self, 'Do you want to delete stack '+str(self.plgrp_id)+' ?', 'Deleting..', wx.YES_NO| wx.NO_DEFAULT | wx.ICON_WARNING)
        
        if dlg.ShowModal() == wx.ID_YES:
                
            meta = ExperimentSettings.getInstance()
       
            for exs_plate_id in meta.get_field_instances('ExptVessel|Plate|GroupNo|'):
            # get the set of each parameters since all parameters are same for all instances under this group so one will be same     
                if meta.get_field('ExptVessel|Plate|GroupNo|'+str(exs_plate_id)) == self.plgrp_id:
                    #remove the instances                    
                    meta.remove_field('ExptVessel|Plate|GroupNo|%s'%str(exs_plate_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Plate|Number|%s'%str(exs_plate_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Plate|GroupName|%s'%str(exs_plate_id), notify_subscribers =False)                    
                    meta.remove_field('ExptVessel|Plate|Design|%s'%str(exs_plate_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Plate|Coat|%s'%str(exs_plate_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Plate|Material|%s'%str(exs_plate_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Plate|Shape|%s'%str(exs_plate_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Plate|Size|%s'%str(exs_plate_id))
                    
            # remove the page
            self.Parent.DeletePage(self.Parent.GetSelection())
            # TO DO: Remove plates from the Bench Panel and update the lineage panel accordingly
            

#########################################################################        
###################     FLASK SETTING PANEL          ####################
#########################################################################	    
class FlaskSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = meta.get_field_instances('ExptVessel|Flask')
        # figure out the group numbers from this list
        flaskgrp = []
        for id in field_ids:
            flaskgrp.append(meta.get_field('ExptVessel|Flask|GroupNo|%s'%(id)))
        flkgrp_list = set(flaskgrp)

        for flkgrp_id in sorted(flkgrp_list):
            panel = FlaskConfigPanel(self.notebook,flkgrp_id)
            self.notebook.AddPage(panel, 'Stack No: %s'% flkgrp_id, True)
      
        self.addFlaskGrpPageBtn = wx.Button(self, label="Add New Stack of Flask")
        self.addFlaskGrpPageBtn.Bind(wx.EVT_BUTTON, self.onAddFlaskGroupPage)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addFlaskGrpPageBtn  , 0, wx.ALL, 5)        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddFlaskGroupPage(self, event):
        # This function is called only for the first instance
        meta = ExperimentSettings.getInstance()
        # Get all the previously encoded pages 
        field_ids = meta.get_field_instances('ExptVessel|Flask')
        # figure out the group numbers from this list
        flaskgrp = []
        for id in field_ids:
            flaskgrp.append(meta.get_field('ExptVessel|Flask|GroupNo|%s'%(id)))
        flkgrp_list = set(flaskgrp)
        
        # find out max Group number to be assigned
        if flkgrp_list:
            flkgrp_id =  max(map(int, flkgrp_list))+1
        else:
            flkgrp_id = 1
                    
        # create the first page
        panel = FlaskConfigPanel(self.notebook,flkgrp_id)
        self.notebook.AddPage(panel, 'Stack No: %s'% flkgrp_id, True)
        # disable the add button
        self.addFlaskGrpPageBtn.Disable()

##---------- Flask Config Panel----------------##
class FlaskConfigPanel(wx.Panel):
    def __init__(self, parent, plgrp_id=None):
        
        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
        
        # Make a scroll window
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
        # find the Done status for this group
        # get the group number                
        self.plgrp_id = plgrp_id

        # get all the flask instances for this group 
        inc_flask_ids = []
        
        for id in meta.get_field_instances('ExptVessel|Flask'):     
            if (meta.get_field('ExptVessel|Flask|GroupNo|%s'%(id)) == self.plgrp_id):
                inc_flask_ids.append(id)
        
        #------- Heading ---#
        text = wx.StaticText(self.sw, -1, 'Flask Settings')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---- Flask number---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of flasks in the stack'), 0)
        self.flasknum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_flask_ids:
            self.flasknum.Enable() 
        else:
            self.flasknum.SetStringSelection(meta.get_field('ExptVessel|Flask|Number|'+str(inc_flask_ids[0])))
            self.flasknum.Disable()            
        fgs.Add(self.flasknum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_flask_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Flask|GroupName|%s'%str(inc_flask_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
        
        #--Fask Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Flask Size (cm2)'), 0)
        self.flasksize = wx.Choice(self.sw, -1, choices=['12.5','25','75','150','175'])
        if not inc_flask_ids:
            self.flasksize.Enable()
        else:
            self.flasksize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Flask|Size|%s'%str(inc_flask_ids[0])))
            self.flasksize.Disable()
        fgs.Add(self.flasksize, 0, wx.EXPAND)
        
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Flask Coating'), 0)
        self.flaskcoat = wx.Choice(self.sw, -1, choices=['None','Collagen IV','Gelatin','Poly-L-Lysine','Poly-D-Lysine', 'Fibronectin', 'Laminin','Poly-D-Lysine + Laminin', 'Poly-L-Ornithine+Laminin'])
        if not inc_flask_ids:
            self.flaskcoat.Enable()
        else:
            self.flaskcoat.SetStringSelection(meta.get_field('ExptVessel|Flask|Coat|%s'%str(inc_flask_ids[0])))
            self.flaskcoat.Disable()
        fgs.Add(self.flaskcoat, 0, wx.EXPAND)
        
        # DELETE button
        self.deleteFlaskgroupPageBtn = wx.Button(self.sw, -1, label="Delete Stack")
        self.deleteFlaskgroupPageBtn.Bind(wx.EVT_BUTTON, self.onDeleteFlaskgroupPage)
        if not inc_flask_ids:
            self.deleteFlaskgroupPageBtn.Disable()
        else:
            self.deleteFlaskgroupPageBtn.Enable()
        fgs.Add(self.deleteFlaskgroupPageBtn, 0, wx.EXPAND)
        
        # CREATE button
        self.createBtn = wx.Button(self.sw, -1, label="Create Stack")
        self.createBtn.Bind(wx.EVT_BUTTON, self.onCreateFlaskgroupPage)
        if inc_flask_ids:
            self.createBtn.Disable()
        fgs.Add(self.createBtn, 0, wx.EXPAND)             

        ##---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def onCreateFlaskgroupPage(self, event):
        
        # get all input from the fields
        meta = ExperimentSettings.getInstance()
        # get the users input for number of flasks requried
        flask_count = int(self.flasknum.GetStringSelection())
        ## TO DO: check whether this value being selected, if not show message!!
        
        flask_list = meta.get_field_instances('ExptVessel|Flask|')
        
        #Find the all instances of flask
        if flask_list:
            max_id =  max(map(int, flask_list))+1
        else:
            max_id = 1
        
        # save the input from the max instances         
        for flask_id in range(max_id, max_id+flask_count):
            
            id = 'flask%s'%(flask_id)
            plate_design = (1,1)  # since flask is alwasys a sigle entity resembling to 1x1 well plate format   
    
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate(id, plate_design)
            else:
                PlateDesign.set_plate_format(id, plate_design)
        
            meta.set_field('ExptVessel|Flask|GroupNo|%s'%str(flask_id),    self.plgrp_id, notify_subscribers =False)
            meta.set_field('ExptVessel|Flask|Number|%s'%str(flask_id),     self.flasknum.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Flask|GroupName|%s'%str(flask_id),  self.groupname.GetValue(), notify_subscribers =False)
            meta.set_field('ExptVessel|Flask|Size|%s'%str(flask_id),       self.flasksize.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Flask|Coat|%s'%str(flask_id),       self.flaskcoat.GetStringSelection())

        
        # make all input fields disable
        self.flasknum.Disable()
        self.groupname.Disable()
        self.flasksize.Disable()
        self.flaskcoat.Disable()

        # make the copy and delete button active
        self.createBtn.Disable()
        self.deleteFlaskgroupPageBtn.Enable()
        self.GrandParent.addFlaskGrpPageBtn.Enable()
         
      
    def onDeleteFlaskgroupPage(self, event):

        dlg = wx.MessageDialog(self, 'Do you want to delete stack '+str(self.plgrp_id)+' ?', 'Deleting..', wx.YES_NO| wx.NO_DEFAULT | wx.ICON_WARNING)
        
        if dlg.ShowModal() == wx.ID_YES:
                
            meta = ExperimentSettings.getInstance()
       
            for exs_flask_id in meta.get_field_instances('ExptVessel|Flask|GroupNo|'):
            # get the set of each parameters since all parameters are same for all instances under this group so one will be same     
                if meta.get_field('ExptVessel|Flask|GroupNo|'+str(exs_flask_id)) == self.plgrp_id:
                
                    #remove the instances                    
                    meta.remove_field('ExptVessel|Flask|GroupNo|%s'%str(exs_flask_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Flask|Number|%s'%str(exs_flask_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Flask|GroupName|%s'%str(exs_flask_id), notify_subscribers =False)                    
                    meta.remove_field('ExptVessel|Flask|Size|%s'%str(exs_flask_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Flask|Coat|%s'%str(exs_flask_id))
           
            ##remove the page
            self.Parent.DeletePage(self.Parent.GetSelection())

#########################################################################        
###################     DISH SETTING PANEL          ####################
#########################################################################	    
class DishSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        
        
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = meta.get_field_instances('ExptVessel|Dish')
        # figure out the group numbers from this list
        dishgrp = []
        for id in field_ids:
            dishgrp.append(meta.get_field('ExptVessel|Dish|GroupNo|%s'%(id)))
        flkgrp_list = set(dishgrp)

        for flkgrp_id in sorted(flkgrp_list):
            panel = DishConfigPanel(self.notebook,flkgrp_id)
            self.notebook.AddPage(panel, 'Stack No: %s'% flkgrp_id, True)
        
        self.addDishGrpPageBtn = wx.Button(self, label="Add New Stack of Dish")
        self.addDishGrpPageBtn.Bind(wx.EVT_BUTTON, self.onAddDishGroupPage)

        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addDishGrpPageBtn  , 0, wx.ALL, 5)        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddDishGroupPage(self, event):
        # This function is called only for the first instance
        meta = ExperimentSettings.getInstance()
        # Get all the previously encoded pages 
        field_ids = meta.get_field_instances('ExptVessel|Dish')
        # figure out the group numbers from this list
        dishgrp = []
        for id in field_ids:
            dishgrp.append(meta.get_field('ExptVessel|Dish|GroupNo|%s'%(id)))
        flkgrp_list = set(dishgrp)
        
        # find out max Group number to be assigned
        if flkgrp_list:
            flkgrp_id =  max(map(int, flkgrp_list))+1
        else:
            flkgrp_id = 1
                    
        # create the first page
        panel = DishConfigPanel(self.notebook,flkgrp_id)
        self.notebook.AddPage(panel, 'Stack No: %s'% flkgrp_id, True)
        # disable the add button
        self.addDishGrpPageBtn.Disable()

##---------- Dish Config Panel----------------##
class DishConfigPanel(wx.Panel):
    def __init__(self, parent, plgrp_id=None):
        
        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
        
        # Make a scroll window
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
        # find the Done status for this group
        # get the group number                
        self.plgrp_id = plgrp_id

        # get all the dish instances for this group 
        inc_dish_ids = []
        
        for id in meta.get_field_instances('ExptVessel|Dish'):     
            if (meta.get_field('ExptVessel|Dish|GroupNo|%s'%(id)) == self.plgrp_id):
                inc_dish_ids.append(id)
        
        #------- Heading ---#
        text = wx.StaticText(self.sw, -1, 'Dish Settings')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---- Dish number---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of dishs in the stack'), 0)
        self.dishnum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_dish_ids:
            self.dishnum.Enable() 
        else:
            self.dishnum.SetStringSelection(meta.get_field('ExptVessel|Dish|Number|'+str(inc_dish_ids[0])))
            self.dishnum.Disable()            
        fgs.Add(self.dishnum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_dish_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Dish|GroupName|%s'%str(inc_dish_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
        
        #--Dish Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Dish Size (mm)'), 0)
        self.dishsize = wx.Choice(self.sw, -1, choices=['35','60','100','150'])
        if not inc_dish_ids:
            self.dishsize.Enable()
        else:
            self.dishsize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Dish|Size|%s'%str(inc_dish_ids[0])))
            self.dishsize.Disable()
        fgs.Add(self.dishsize, 0, wx.EXPAND)
        
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Dish Coating'), 0)
        self.dishcoat = wx.Choice(self.sw, -1, choices=['None','Collagen IV','Gelatin','Poly-L-Lysine','Poly-D-Lysine', 'Fibronectin', 'Laminin','Poly-D-Lysine + Laminin', 'Poly-L-Ornithine+Laminin'])
        if not inc_dish_ids:
            self.dishcoat.Enable()
        else:
            self.dishcoat.SetStringSelection(meta.get_field('ExptVessel|Dish|Coat|%s'%str(inc_dish_ids[0])))
            self.dishcoat.Disable()
        fgs.Add(self.dishcoat, 0, wx.EXPAND)
        
        # DELETE button
        self.deleteDishgroupPageBtn = wx.Button(self.sw, -1, label="Delete Stack")
        self.deleteDishgroupPageBtn.Bind(wx.EVT_BUTTON, self.onDeleteDishgroupPage)
        if not inc_dish_ids:
            self.deleteDishgroupPageBtn.Disable()
        else:
            self.deleteDishgroupPageBtn.Enable()
        fgs.Add(self.deleteDishgroupPageBtn, 0, wx.EXPAND)
        
        # CREATE button
        self.createBtn = wx.Button(self.sw, -1, label="Create Stack")
        self.createBtn.Bind(wx.EVT_BUTTON, self.onCreateDishgroupPage)
        if inc_dish_ids:
            self.createBtn.Disable()
        fgs.Add(self.createBtn, 0, wx.EXPAND)             

        ##---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def onCreateDishgroupPage(self, event):
        
        # get all input from the fields
        meta = ExperimentSettings.getInstance()
        # get the users input for number of dishs requried
        dish_count = int(self.dishnum.GetStringSelection())
        ## TO DO: check whether this value being selected, if not show message!!
        
        dish_list = meta.get_field_instances('ExptVessel|Dish|')
        
        #Find the all instances of dish
        if dish_list:
            max_id =  max(map(int, dish_list))+1
        else:
            max_id = 1
        
        # save the input from the max instances         
        for dish_id in range(max_id, max_id+dish_count):
            
            id = 'dish%s'%(dish_id)
            plate_design = (1,1)  # since dish is alwasys a sigle entity resembling to 1x1 well plate format   
    
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate(id, plate_design)
            else:
                PlateDesign.set_plate_format(id, plate_design)
        
            meta.set_field('ExptVessel|Dish|GroupNo|%s'%str(dish_id),    self.plgrp_id, notify_subscribers =False)
            meta.set_field('ExptVessel|Dish|Number|%s'%str(dish_id),     self.dishnum.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Dish|GroupName|%s'%str(dish_id),  self.groupname.GetValue(), notify_subscribers =False)
            meta.set_field('ExptVessel|Dish|Size|%s'%str(dish_id),       self.dishsize.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Dish|Coat|%s'%str(dish_id),       self.dishcoat.GetStringSelection())

        
        # make all input fields disable
        self.dishnum.Disable()
        self.groupname.Disable()
        self.dishsize.Disable()
        self.dishcoat.Disable()

        # make the copy and delete button active
        self.createBtn.Disable()
        self.deleteDishgroupPageBtn.Enable()
        self.GrandParent.addDishGrpPageBtn.Enable()
         
      
    def onDeleteDishgroupPage(self, event):

        dlg = wx.MessageDialog(self, 'Do you want to delete stack '+str(self.plgrp_id)+' ?', 'Deleting..', wx.YES_NO| wx.NO_DEFAULT | wx.ICON_WARNING)
        
        if dlg.ShowModal() == wx.ID_YES:
                
            meta = ExperimentSettings.getInstance()
       
            for exs_dish_id in meta.get_field_instances('ExptVessel|Dish|GroupNo|'):
            # get the set of each parameters since all parameters are same for all instances under this group so one will be same     
                if meta.get_field('ExptVessel|Dish|GroupNo|'+str(exs_dish_id)) == self.plgrp_id:
                
                    #remove the instances                    
                    meta.remove_field('ExptVessel|Dish|GroupNo|%s'%str(exs_dish_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Dish|Number|%s'%str(exs_dish_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Dish|GroupName|%s'%str(exs_dish_id), notify_subscribers =False)                    
                    meta.remove_field('ExptVessel|Dish|Size|%s'%str(exs_dish_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Dish|Coat|%s'%str(exs_dish_id))
           
            ##remove the page
            self.Parent.DeletePage(self.Parent.GetSelection())

#########################################################################        
###################     DISH SETTING PANEL          ####################
#########################################################################	    
class CoverslipSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
        
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        
        
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = meta.get_field_instances('ExptVessel|Coverslip')
        # figure out the group numbers from this list
        coverslipgrp = []
        for id in field_ids:
            coverslipgrp.append(meta.get_field('ExptVessel|Coverslip|GroupNo|%s'%(id)))
        flkgrp_list = set(coverslipgrp)

        for flkgrp_id in sorted(flkgrp_list):
            panel = CoverslipConfigPanel(self.notebook,flkgrp_id)
            self.notebook.AddPage(panel, 'Stack No: %s'% flkgrp_id, True)
       
        self.addCoverslipGrpPageBtn = wx.Button(self, label="Add New Stack of Coverslip")
        self.addCoverslipGrpPageBtn.Bind(wx.EVT_BUTTON, self.onAddCoverslipGroupPage)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addCoverslipGrpPageBtn  , 0, wx.ALL, 5)        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddCoverslipGroupPage(self, event):
        # This function is called only for the first instance
        meta = ExperimentSettings.getInstance()
        # Get all the previously encoded pages 
        field_ids = meta.get_field_instances('ExptVessel|Coverslip')
        # figure out the group numbers from this list
        coverslipgrp = []
        for id in field_ids:
            coverslipgrp.append(meta.get_field('ExptVessel|Coverslip|GroupNo|%s'%(id)))
        flkgrp_list = set(coverslipgrp)
        
        # find out max Group number to be assigned
        if flkgrp_list:
            flkgrp_id =  max(map(int, flkgrp_list))+1
        else:
            flkgrp_id = 1
                    
        # create the first page
        panel = CoverslipConfigPanel(self.notebook,flkgrp_id)
        self.notebook.AddPage(panel, 'Stack No: %s'% flkgrp_id, True)
        # disable the add button
        self.addCoverslipGrpPageBtn.Disable()

##---------- Coverslip Config Panel----------------##
class CoverslipConfigPanel(wx.Panel):
    def __init__(self, parent, plgrp_id=None):
        
        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
        
        # Make a scroll window
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
        # find the Done status for this group
        # get the group number                
        self.plgrp_id = plgrp_id

        # get all the coverslip instances for this group 
        inc_coverslip_ids = []
        
        for id in meta.get_field_instances('ExptVessel|Coverslip'):     
            if (meta.get_field('ExptVessel|Coverslip|GroupNo|%s'%(id)) == self.plgrp_id):
                inc_coverslip_ids.append(id)
        
        #------- Heading ---#
        text = wx.StaticText(self.sw, -1, 'Coverslip Settings')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---- Coverslip number---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of coverslips in the stack'), 0)
        self.coverslipnum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_coverslip_ids:
            self.coverslipnum.Enable() 
        else:
            self.coverslipnum.SetStringSelection(meta.get_field('ExptVessel|Coverslip|Number|'+str(inc_coverslip_ids[0])))
            self.coverslipnum.Disable()            
        fgs.Add(self.coverslipnum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_coverslip_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Coverslip|GroupName|%s'%str(inc_coverslip_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
        
        #--Coverslip Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Coverslip Size (mm)'), 0)
        self.coverslipsize = wx.Choice(self.sw, -1, choices=['12','22'])
        if not inc_coverslip_ids:
            self.coverslipsize.Enable()
        else:
            self.coverslipsize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Coverslip|Size|%s'%str(inc_coverslip_ids[0])))
            self.coverslipsize.Disable()
        fgs.Add(self.coverslipsize, 0, wx.EXPAND)
        
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Coverslip Coating'), 0)
        self.coverslipcoat = wx.Choice(self.sw, -1, choices=['None','Collagen IV','Gelatin','Poly-L-Lysine','Poly-D-Lysine', 'Fibronectin', 'Laminin','Poly-D-Lysine + Laminin', 'Poly-L-Ornithine+Laminin'])
        if not inc_coverslip_ids:
            self.coverslipcoat.Enable()
        else:
            self.coverslipcoat.SetStringSelection(meta.get_field('ExptVessel|Coverslip|Coat|%s'%str(inc_coverslip_ids[0])))
            self.coverslipcoat.Disable()
        fgs.Add(self.coverslipcoat, 0, wx.EXPAND)
        
        # DELETE button
        self.deleteCoverslipgroupPageBtn = wx.Button(self.sw, -1, label="Delete Stack")
        self.deleteCoverslipgroupPageBtn.Bind(wx.EVT_BUTTON, self.onDeleteCoverslipgroupPage)
        if not inc_coverslip_ids:
            self.deleteCoverslipgroupPageBtn.Disable()
        else:
            self.deleteCoverslipgroupPageBtn.Enable()
        fgs.Add(self.deleteCoverslipgroupPageBtn, 0, wx.EXPAND)
        
        # CREATE button
        self.createBtn = wx.Button(self.sw, -1, label="Create Stack")
        self.createBtn.Bind(wx.EVT_BUTTON, self.onCreateCoverslipgroupPage)
        if inc_coverslip_ids:
            self.createBtn.Disable()
        fgs.Add(self.createBtn, 0, wx.EXPAND)             

        ##---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def onCreateCoverslipgroupPage(self, event):
        
        # get all input from the fields
        meta = ExperimentSettings.getInstance()
        # get the users input for number of coverslips requried
        coverslip_count = int(self.coverslipnum.GetStringSelection())
        ## TO DO: check whether this value being selected, if not show message!!
        
        coverslip_list = meta.get_field_instances('ExptVessel|Coverslip|')
        
        #Find the all instances of coverslip
        if coverslip_list:
            max_id =  max(map(int, coverslip_list))+1
        else:
            max_id = 1
        
        # save the input from the max instances         
        for coverslip_id in range(max_id, max_id+coverslip_count):
            
            id = 'coverslip%s'%(coverslip_id)
            plate_design = (1,1)  # since coverslip is alwasys a sigle entity resembling to 1x1 well plate format   
    
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate(id, plate_design)
            else:
                PlateDesign.set_plate_format(id, plate_design)
        
            meta.set_field('ExptVessel|Coverslip|GroupNo|%s'%str(coverslip_id),    self.plgrp_id, notify_subscribers =False)
            meta.set_field('ExptVessel|Coverslip|Number|%s'%str(coverslip_id),     self.coverslipnum.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Coverslip|GroupName|%s'%str(coverslip_id),  self.groupname.GetValue(), notify_subscribers =False)
            meta.set_field('ExptVessel|Coverslip|Size|%s'%str(coverslip_id),       self.coverslipsize.GetStringSelection(), notify_subscribers =False)
            meta.set_field('ExptVessel|Coverslip|Coat|%s'%str(coverslip_id),       self.coverslipcoat.GetStringSelection())

        
        # make all input fields disable
        self.coverslipnum.Disable()
        self.groupname.Disable()
        self.coverslipsize.Disable()
        self.coverslipcoat.Disable()

        # make the copy and delete button active
        self.createBtn.Disable()
        self.deleteCoverslipgroupPageBtn.Enable()
        self.GrandParent.addCoverslipGrpPageBtn.Enable()
         
      
    def onDeleteCoverslipgroupPage(self, event):

        dlg = wx.MessageDialog(self, 'Do you want to delete stack '+str(self.plgrp_id)+' ?', 'Deleting..', wx.YES_NO| wx.NO_DEFAULT | wx.ICON_WARNING)
        
        if dlg.ShowModal() == wx.ID_YES:
                
            meta = ExperimentSettings.getInstance()
       
            for exs_coverslip_id in meta.get_field_instances('ExptVessel|Coverslip|GroupNo|'):
            # get the set of each parameters since all parameters are same for all instances under this group so one will be same     
                if meta.get_field('ExptVessel|Coverslip|GroupNo|'+str(exs_coverslip_id)) == self.plgrp_id:
                
                    #remove the instances                    
                    meta.remove_field('ExptVessel|Coverslip|GroupNo|%s'%str(exs_coverslip_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Coverslip|Number|%s'%str(exs_coverslip_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Coverslip|GroupName|%s'%str(exs_coverslip_id), notify_subscribers =False)                    
                    meta.remove_field('ExptVessel|Coverslip|Size|%s'%str(exs_coverslip_id), notify_subscribers =False)
                    meta.remove_field('ExptVessel|Coverslip|Coat|%s'%str(exs_coverslip_id))
           
            ##remove the page
            self.Parent.DeletePage(self.Parent.GetSelection())

########################################################################        
################## CELL SEEDING PANEL #########################
########################################################################
class CellSeedSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        cellload_list = meta.get_field_instances('CellTransfer|Seed|')
        self.cellload_next_page_num = 1
        # update the  number of existing cell loading
        if cellload_list: 
            self.cellload_next_page_num  =  int(cellload_list[-1])+1
        for cellload_id in cellload_list:
            panel = CellSeedPanel(self.notebook, int(cellload_id))
            self.notebook.AddPage(panel, 'Cell Seeding Specification No: %s'%(cellload_id), True)

        addCellSeedPageBtn = wx.Button(self, label="Add Cell Seeding Specification")
        addCellSeedPageBtn.Bind(wx.EVT_BUTTON, self.onAddCellSeedPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addCellSeedPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddCellSeedPage(self, event):
        panel = CellSeedPanel(self.notebook, self.cellload_next_page_num)
        self.notebook.AddPage(panel, 'Cell Seeding Specification No: %s'%(self.cellload_next_page_num), True)
        self.cellload_next_page_num += 1


class CellSeedPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5) 
        
        #-- Cell Line selection ---#
        celllineselcTAG = 'CellTransfer|Seed|StockInstance|'+str(self.page_counter)
        self.settings_controls[celllineselcTAG] = wx.TextCtrl(self.sw, value=meta.get_field(celllineselcTAG, default=''))
        showInstBut = wx.Button(self.sw, -1, 'Show Stock Cultures', (100,100))
        showInstBut.Bind (wx.EVT_BUTTON, self.OnShowDialog) 
        self.settings_controls[celllineselcTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[celllineselcTAG].SetToolTipString('Stock culture from where cells were transferred')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Stock Culture'), 0)
        fgs.Add(self.settings_controls[celllineselcTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)

        # Seeding Density
        seedTAG = 'CellTransfer|Seed|SeedingDensity|'+str(self.page_counter)
        self.settings_controls[seedTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seedTAG, default=''))
        self.settings_controls[seedTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seedTAG].SetToolTipString('Number of cells seeded in each well or flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Seeding Density'), 0)
        fgs.Add(self.settings_controls[seedTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        # Medium Used
        medmTAG = 'CellTransfer|Seed|MediumUsed|'+str(self.page_counter)
        self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
        if meta.get_field(medmTAG) is not None:
            self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
        self.settings_controls[medmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0)
        fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #  Medium Addatives
        medaddTAG = 'CellTransfer|Seed|MediumAddatives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetToolTipString('Any medium additives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Additives'), 0)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        # Trypsinization
        trypsTAG = 'CellTransfer|Seed|Trypsinizatiton|'+str(self.page_counter)
        self.settings_controls[trypsTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(trypsTAG) is not None:
            self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
        self.settings_controls[trypsTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Trypsinization'), 0)
        fgs.Add(self.settings_controls[trypsTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        
    def OnShowDialog(self, event):     
        # link with the dynamic experiment settings
        meta = ExperimentSettings.getInstance()
        attributes = meta.get_attribute_list('StockCulture|Sample') 
        
        #check whether there is at least one attributes
        if not attributes:
            dial = wx.MessageDialog(None, 'No Instances exists!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        #show the popup table
        dia = InstanceListDialog(self, 'StockCulture|Sample', selection_mode = False)
        if dia.ShowModal() == wx.ID_OK:
            if dia.listctrl.get_selected_instances() != []:
                instance = dia.listctrl.get_selected_instances()[0]
                celllineselcTAG = 'CellTransfer|Seed|StockInstance|'+str(self.page_counter)
                self.settings_controls[celllineselcTAG].SetValue(str(instance))
        dia.Destroy()

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())



########################################################################        
################## CELL HARVEST PANEL #########################
########################################################################
class CellHarvestSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        cellload_list = meta.get_field_instances('CellTransfer|Seed|')
        self.cellload_next_page_num = 1
        # update the  number of existing cell loading
        ## Get all the previously encoded Flowcytometer pages and re-Add them as pages
        cellharv_list = meta.get_field_instances('CellTransfer|Harvest|')
        self.cellharv_next_page_num = 1
        # update the  number of existing cellharvcytometer
        if cellharv_list:
            self.cellharv_next_page_num =  int(cellharv_list[-1])+1
        for cellharv_id in cellharv_list:
            panel = CellHarvestPanel(self.notebook, int(cellharv_id))
            self.notebook.AddPage(panel, 'Cell Harvest Specification No: %s'%(cellharv_id), True)

        addCellHarvestPageBtn = wx.Button(self, label="Add Cell Harvest Specification")
        addCellHarvestPageBtn.Bind(wx.EVT_BUTTON, self.onAddCellHarvestPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addCellHarvestPageBtn , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddCellHarvestPage(self, event):
        panel = CellHarvestPanel(self.notebook, self.cellharv_next_page_num)
        self.notebook.AddPage(panel, 'Cell Harvest Specification No: %s'%(self.cellharv_next_page_num), True)
        self.cellharv_next_page_num += 1

class CellHarvestPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)

        cell_Line_instances = meta.get_field_instances('StockCulture|Sample|CellLine|')
        cell_Line_choices = []
        for cell_Line_instance in cell_Line_instances:
            cell_Line_choices.append(meta.get_field('StockCulture|Sample|CellLine|'+cell_Line_instance)+'_'+cell_Line_instance)
  
        #-- Cell Line selection ---#
        celllineselcTAG = 'CellTransfer|Harvest|StockInstance|'+str(self.page_counter)
        self.settings_controls[celllineselcTAG] = wx.Choice(self.sw, -1,  choices=cell_Line_choices)
        if meta.get_field(celllineselcTAG) is not None:
            self.settings_controls[celllineselcTAG].SetStringSelection(meta.get_field(celllineselcTAG))
        self.settings_controls[celllineselcTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[celllineselcTAG].SetToolTipString('Cell Line used for harvesting')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Cell Line'), 0)
        fgs.Add(self.settings_controls[celllineselcTAG], 0, wx.EXPAND)

        # Seeding Density
        harvestTAG = 'CellTransfer|Harvest|HarvestingDensity|'+str(self.page_counter)
        self.settings_controls[harvestTAG] = wx.TextCtrl(self.sw, value=meta.get_field(harvestTAG, default=''))
        self.settings_controls[harvestTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[harvestTAG].SetToolTipString('Number of cells harvested from each well or flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Harvesting Density'), 0)
        fgs.Add(self.settings_controls[harvestTAG], 0, wx.EXPAND)

        # Medium Used
        medmTAG = 'CellTransfer|Harvest|MediumUsed|'+str(self.page_counter)
        self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
        if meta.get_field(medmTAG) is not None:
            self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
        self.settings_controls[medmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0)
        fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND) 

        #  Medium Addatives
        medaddTAG = 'CellTransfer|Harvest|MediumAddatives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetToolTipString('Any medium addatives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Addatives'), 0)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)

        # Trypsinization
        trypsTAG = 'CellTransfer|Harvest|Trypsinizatiton|'+str(self.page_counter)
        self.settings_controls[trypsTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(trypsTAG) is not None:
            self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
        self.settings_controls[trypsTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Trypsinization'), 0)
        fgs.Add(self.settings_controls[trypsTAG], 0, wx.EXPAND)  

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())



########################################################################        
################## CHEMICAL SETTING PANEL ###########################
########################################################################	    
class ChemicalSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        chemical_list = meta.get_field_instances('Perturbation|Chem|')
        self.chemical_next_page_num = 1
        # update the  number of existing cell loading
        if chemical_list: 
            self.chemical_next_page_num  =  int(chemical_list[-1])+1
        for chemical_id in chemical_list:
            panel = ChemicalAgentPanel(self.notebook, int(chemical_id))
            self.notebook.AddPage(panel, 'Chemical Agent No: %s'%(chemical_id), True)

        # Add the buttons
        addChemAgentPageBtn = wx.Button(self, label="Add Chemical Agent")
        addChemAgentPageBtn.Bind(wx.EVT_BUTTON, self.onAddChemAgentPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addChemAgentPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddChemAgentPage(self, event):
        panel = ChemicalAgentPanel(self.notebook, self.chemical_next_page_num)
        self.notebook.AddPage(panel, 'Chemical Agent No: %s'%(self.chemical_next_page_num), True)
        self.chemical_next_page_num += 1 


class ChemicalAgentPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)

        #  Chem Agent Name
        chemnamTAG = 'Perturbation|Chem|ChemName|'+str(self.page_counter)
        self.settings_controls[chemnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemnamTAG, default=''))
        self.settings_controls[chemnamTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemnamTAG].SetToolTipString('Name of the Chemical agent used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Chemical Agent Name'), 0)
        fgs.Add(self.settings_controls[chemnamTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Chem Concentration and Unit
        concTAG = 'Perturbation|Chem|Conc|'+str(self.page_counter)
        self.settings_controls[concTAG] = wx.TextCtrl(self.sw, value=meta.get_field(concTAG, default='')) 
        self.settings_controls[concTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[concTAG].SetToolTipString('Concetration of the Chemical agent used')
        
        unitTAG = 'Perturbation|Chem|Unit|'+str(self.page_counter)
        self.settings_controls[unitTAG] = wx.Choice(self.sw, -1,  choices=['uM', 'nM', 'mM', 'mg/L', 'uL/L', '%w/v', '%v/v'])
        if meta.get_field(unitTAG) is not None:
            self.settings_controls[unitTAG].SetStringSelection(meta.get_field(unitTAG))
        self.settings_controls[unitTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)

        fgs.Add(wx.StaticText(self.sw, -1, 'Concentration'), 0)
        fgs.Add(self.settings_controls[concTAG], 0, wx.EXPAND)
        fgs.Add(self.settings_controls[unitTAG], 0, wx.EXPAND)
        
         #  Manufacturer
        chemmfgTAG = 'Perturbation|Chem|Manufacturer|'+str(self.page_counter)
        self.settings_controls[chemmfgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemmfgTAG, default=''))
        self.settings_controls[chemmfgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemmfgTAG].SetToolTipString('Name of the Chemical agent Manufacturer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Chemical Agent Manufacturer'), 0)
        fgs.Add(self.settings_controls[chemmfgTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Catalogue Number
        chemcatTAG = 'Perturbation|Chem|CatNum|'+str(self.page_counter)
        self.settings_controls[chemcatTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemcatTAG, default=''))
        self.settings_controls[chemcatTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemcatTAG].SetToolTipString('Name of the Chemical agent Catalogue Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Chemical Agent Catalogue Number'), 0)
        fgs.Add(self.settings_controls[chemcatTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
         #  Additives
        chemaddTAG = 'Perturbation|Chem|Additives|'+str(self.page_counter)
        self.settings_controls[chemaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemaddTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[chemaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemaddTAG].SetToolTipString('Name of Additives')
        fgs.Add(wx.StaticText(self.sw, -1, 'Additives'), 0)
        fgs.Add(self.settings_controls[chemaddTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
         #  Other informaiton
        chemothTAG = 'Perturbation|Chem|Other|'+str(self.page_counter)
        self.settings_controls[chemothTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemothTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[chemothTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemothTAG].SetToolTipString('Other informaiton')
        fgs.Add(wx.StaticText(self.sw, -1, 'Other informaiton'), 0)
        fgs.Add(self.settings_controls[chemothTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)


        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())


########################################################################        
################## BIOLOGICAL SETTING PANEL ###########################
########################################################################	    
class BiologicalSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
 
        # Get all the previously encoded Flowcytometer pages and re-Add them as pages
        bio_list = meta.get_field_instances('Perturbation|Bio|')
        self.bio_next_page_num = 1
        # update the  number of existing biocytometer
        if bio_list:
            self.bio_next_page_num =  int(bio_list[-1])+1
        for bio_id in bio_list:
            panel = BiologicalAgentPanel(self.notebook, int(bio_id))
            self.notebook.AddPage(panel, 'Biological Agent No: %s'%(bio_id), True)

        # Add the buttons
        addBioAgentPageBtn = wx.Button(self, label="Add Biological Agent")
        addBioAgentPageBtn.Bind(wx.EVT_BUTTON, self.onAddBioAgentPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addBioAgentPageBtn , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddBioAgentPage(self, event):
        panel = BiologicalAgentPanel(self.notebook, self.bio_next_page_num)
        self.notebook.AddPage(panel, 'Biological Agent No: %s'%(self.bio_next_page_num), True)
        self.bio_next_page_num += 1    
        
class BiologicalAgentPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)

        #  RNAi Sequence
        seqnamTAG = 'Perturbation|Bio|SeqName|'+str(self.page_counter)
        self.settings_controls[seqnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seqnamTAG, default=''))
        self.settings_controls[seqnamTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seqnamTAG].SetToolTipString('Sequence of the RNAi')
        fgs.Add(wx.StaticText(self.sw, -1, 'RNAi Sequence'), 0)
        fgs.Add(self.settings_controls[seqnamTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Sequence accession number
        seqacssTAG = 'Perturbation|Bio|AccessNumber|'+str(self.page_counter)
        self.settings_controls[seqacssTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seqacssTAG, default=''))
        self.settings_controls[seqacssTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seqacssTAG].SetToolTipString('Sequence Accession Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Sequence Accession Number'), 0)
        fgs.Add(self.settings_controls[seqacssTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Target GeneAccessNumber
        tgtgenTAG = 'Perturbation|Bio|TargetGeneAccessNum|'+str(self.page_counter)
        self.settings_controls[tgtgenTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tgtgenTAG, default=''))
        self.settings_controls[tgtgenTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tgtgenTAG].SetToolTipString('Target GeneAccessNumber')
        fgs.Add(wx.StaticText(self.sw, -1, 'Target Gene Accession Number'), 0)
        fgs.Add(self.settings_controls[tgtgenTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #  Bio Concentration and Unit
        concTAG = 'Perturbation|Bio|Conc|'+str(self.page_counter)
        self.settings_controls[concTAG] = wx.TextCtrl(self.sw, value=meta.get_field(concTAG, default='')) 
        self.settings_controls[concTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[concTAG].SetToolTipString('Concetration of the Biological agent used')
        
        unitTAG = 'Perturbation|Bio|Unit|'+str(self.page_counter)
        self.settings_controls[unitTAG] = wx.Choice(self.sw, -1,  choices=['uM', 'nM', 'mM', 'mg/L', 'uL/L', '%w/v', '%v/v'])
        if meta.get_field(unitTAG) is not None:
            self.settings_controls[unitTAG].SetStringSelection(meta.get_field(unitTAG))
        self.settings_controls[unitTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)

        fgs.Add(wx.StaticText(self.sw, -1, 'Concentration'), 0)
        fgs.Add(self.settings_controls[concTAG], 0, wx.EXPAND)
        fgs.Add(self.settings_controls[unitTAG], 0, wx.EXPAND)        
        #  Additives
        bioaddTAG = 'Perturbation|Bio|Additives|'+str(self.page_counter)
        self.settings_controls[bioaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(bioaddTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[bioaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[bioaddTAG].SetToolTipString('Name of Additives')
        fgs.Add(wx.StaticText(self.sw, -1, 'Additives'), 0)
        fgs.Add(self.settings_controls[bioaddTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
         #  Other informaiton
        bioothTAG = 'Perturbation|Bio|Other|'+str(self.page_counter)
        self.settings_controls[bioothTAG] = wx.TextCtrl(self.sw, value=meta.get_field(bioothTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[bioothTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[bioothTAG].SetToolTipString('Other informaiton')
        fgs.Add(wx.StaticText(self.sw, -1, 'Other informaiton'), 0)
        fgs.Add(self.settings_controls[bioothTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())


########################################################################        
################## ANTIBODY SETTING PANEL    ###########################
########################################################################
class AntibodySettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Antibody pages and re-Add them as pages
        antibody_list = meta.get_field_instances('Labeling|Antibody|')
        self.antibody_next_page_num = 1
        # update the  number of existing Drying protocols
        if antibody_list: 
            self.antibody_next_page_num  =  int(antibody_list[-1])+1
        for antibody_id in antibody_list:
            panel = AntibodyPanel(self.notebook, int(antibody_id))
            self.notebook.AddPage(panel, 'Antibody No: %s'%(antibody_id), True)

        # Add the buttons
        addAntibodyPageBtn = wx.Button(self, label="Add Antibody ")
        #addAntibodyPageBtn.SetBackgroundColour("#33FF33")
        addAntibodyPageBtn.Bind(wx.EVT_BUTTON, self.onAddAntibodyPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addAntibodyPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddAntibodyPage(self, event):
        panel = AntibodyPanel(self.notebook, self.antibody_next_page_num)
        self.notebook.AddPage(panel, 'Antibody No: %s'%(self.antibody_next_page_num), True)
        self.antibody_next_page_num += 1

class AntibodyPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=4, hgap=5, vgap=5)


        #  Antibodying Target
        targetTAG = 'Labeling|Antibody|Target|'+str(self.page_counter)
        self.settings_controls[targetTAG] = wx.TextCtrl(self.sw, value=meta.get_field(targetTAG, default=''))
        self.settings_controls[targetTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[targetTAG].SetToolTipString('Antibody Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Antibody Name'), 0)
        fgs.Add(self.settings_controls[targetTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        # Clonality 
        clonalityTAG = 'Labeling|Antibody|Clonality|'+str(self.page_counter)
        self.settings_controls[clonalityTAG] = wx.Choice(self.sw, -1,  choices=['Monoclonal', 'Polyclonal'])
        if meta.get_field(clonalityTAG) is not None:
            self.settings_controls[clonalityTAG].SetStringSelection(meta.get_field(clonalityTAG))
        self.settings_controls[clonalityTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        
        fgs.Add(wx.StaticText(self.sw, -1, 'Clonality'), 0)
        fgs.Add(self.settings_controls[clonalityTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        # Primary source and associated solvent
        primsrcspcTAG = 'Labeling|Antibody|Primsrcspc|'+str(self.page_counter)
        self.settings_controls[primsrcspcTAG] = wx.Choice(self.sw, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
        if meta.get_field(primsrcspcTAG) is not None:
            self.settings_controls[primsrcspcTAG].SetStringSelection(meta.get_field(primsrcspcTAG))
        self.settings_controls[primsrcspcTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        
        primsrcsolvTAG = 'Labeling|Antibody|Primsrcsolv|'+str(self.page_counter)
        self.settings_controls[primsrcsolvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(primsrcsolvTAG, default='')) 
        self.settings_controls[primsrcsolvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[primsrcsolvTAG].SetToolTipString('Primary source species')
        
        fgs.Add(wx.StaticText(self.sw, -1, 'Primary Source'), 0)
        fgs.Add(self.settings_controls[primsrcspcTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Solvent'), 0)
        fgs.Add(self.settings_controls[primsrcsolvTAG], 0, wx.EXPAND)
        
        # Secondary source and associated solvent
        secnsrcspcTAG = 'Labeling|Antibody|Secnsrcspc|'+str(self.page_counter)
        self.settings_controls[secnsrcspcTAG] = wx.Choice(self.sw, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
        if meta.get_field(secnsrcspcTAG) is not None:
            self.settings_controls[secnsrcspcTAG].SetStringSelection(meta.get_field(secnsrcspcTAG))
        self.settings_controls[secnsrcspcTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        
        secnsrcsolvTAG = 'Labeling|Antibody|Secnsrcsolv|'+str(self.page_counter)
        self.settings_controls[secnsrcsolvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(secnsrcsolvTAG, default='')) 
        self.settings_controls[secnsrcsolvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[secnsrcsolvTAG].SetToolTipString('Secondary source species')
        
        fgs.Add(wx.StaticText(self.sw, -1, 'Secondary Source'), 0)
        fgs.Add(self.settings_controls[secnsrcspcTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Solvent'), 0)
        fgs.Add(self.settings_controls[secnsrcsolvTAG], 0, wx.EXPAND)        
        
        # Tertiary source and associated solvent
        tertsrcspcTAG = 'Labeling|Antibody|Tirtsrcspc|'+str(self.page_counter)
        self.settings_controls[tertsrcspcTAG] = wx.Choice(self.sw, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
        if meta.get_field(tertsrcspcTAG) is not None:
            self.settings_controls[tertsrcspcTAG].SetStringSelection(meta.get_field(tertsrcspcTAG))
        self.settings_controls[tertsrcspcTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        
        tertsrcsolvTAG = 'Labeling|Antibody|Tirtsrcsolv|'+str(self.page_counter)
        self.settings_controls[tertsrcsolvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tertsrcsolvTAG, default='')) 
        self.settings_controls[tertsrcsolvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tertsrcsolvTAG].SetToolTipString('Tertiary source species')
        
        fgs.Add(wx.StaticText(self.sw, -1, 'Tertiary Source'), 0)
        fgs.Add(self.settings_controls[tertsrcspcTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Solvent'), 0)
        fgs.Add(self.settings_controls[tertsrcsolvTAG], 0, wx.EXPAND)  

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())            

########################################################################        
################## PRIMER SETTING PANEL    ###########################
########################################################################
class PrimerSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Primer pages and re-Add them as pages
        antibody_list = meta.get_field_instances('Labeling|Primer|')
        self.antibody_next_page_num = 1
        # update the  number of existing Drying protocols
        if antibody_list: 
            self.antibody_next_page_num  =  int(antibody_list[-1])+1
        for antibody_id in antibody_list:
            panel = PrimerPanel(self.notebook, int(antibody_id))
            self.notebook.AddPage(panel, 'Primer No: %s'%(antibody_id), True)

        # Add the buttons
        addPrimerPageBtn = wx.Button(self, label="Add Primer ")
        #addPrimerPageBtn.SetBackgroundColour("#33FF33")
        addPrimerPageBtn.Bind(wx.EVT_BUTTON, self.onAddPrimerPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPrimerPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPrimerPage(self, event):
        panel = PrimerPanel(self.notebook, self.antibody_next_page_num)
        self.notebook.AddPage(panel, 'Primer No: %s'%(self.antibody_next_page_num), True)
        self.antibody_next_page_num += 1

class PrimerPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)


        #  Primer Target
        targetTAG = 'Labeling|Primer|Target|'+str(self.page_counter)
        self.settings_controls[targetTAG] = wx.TextCtrl(self.sw, value=meta.get_field(targetTAG, default=''))
        self.settings_controls[targetTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[targetTAG].SetToolTipString('Primer Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Primer Name'), 0)
        fgs.Add(self.settings_controls[targetTAG], 0, wx.EXPAND)
        
        # Primer Sequence
        seqTAG = 'Labeling|Primer|Sequence|'+str(self.page_counter)
        self.settings_controls[seqTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seqTAG, default=''))
        self.settings_controls[seqTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seqTAG].SetToolTipString('Primer Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Primer Sequence'), 0)
        fgs.Add(self.settings_controls[seqTAG], 0, wx.EXPAND)
        
        # Melting Temp
        mtempTAG = 'Labeling|Primer|Temp|'+str(self.page_counter)
        self.settings_controls[mtempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(mtempTAG, default=''))
        self.settings_controls[mtempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[mtempTAG].SetToolTipString('Primer Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Melting Temperature'), 0)
        fgs.Add(self.settings_controls[mtempTAG], 0, wx.EXPAND)
        
        # GC%
        gcTAG = 'Labeling|Primer|GC|'+str(self.page_counter)
        self.settings_controls[gcTAG] = wx.TextCtrl(self.sw, value=meta.get_field(gcTAG, default=''))
        self.settings_controls[gcTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[gcTAG].SetToolTipString('Primer Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'GC%'), 0)
        fgs.Add(self.settings_controls[gcTAG], 0, wx.EXPAND)


        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())       
            
########################################################################        
################## STAINING SETTING PANEL    ###########################
########################################################################
class StainingAgentSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        stain_list = meta.get_field_instances('Labeling|Stain|')
        self.stain_next_page_num = 1
        # update the  number of existing cell loading
        if stain_list: 
            self.stain_next_page_num  =  int(stain_list[-1])+1
        for stain_id in stain_list:
            panel = StainPanel(self.notebook, int(stain_id))
            self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(stain_id), True)

        # Add the buttons
        addStainingPageBtn = wx.Button(self, label="Add Staining Protocols")
        #addStainingPageBtn.SetBackgroundColour("#33FF33")
        addStainingPageBtn.Bind(wx.EVT_BUTTON, self.onAddStainingPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addStainingPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddStainingPage(self, event):
        panel = StainPanel(self.notebook, self.stain_next_page_num)
        self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(self.stain_next_page_num), True)
        self.stain_next_page_num += 1

class StainPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)


        #  Staining Agent Name
        stainnamTAG = 'Labeling|Stain|StainProtocolTag|'+str(self.page_counter)
        self.settings_controls[stainnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(stainnamTAG, default=''))
        self.settings_controls[stainnamTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[stainnamTAG].SetToolTipString('Staining Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Staining Agent Name'), 0)
        fgs.Add(self.settings_controls[stainnamTAG], 0, wx.EXPAND)

        # Staining Protocol
        protTAG = 'Labeling|Stain|Protocol|'+str(self.page_counter)
        self.settings_controls[protTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(protTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[protTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[protTAG].SetInitialSize((300, 400))
        self.settings_controls[protTAG].SetToolTipString('Cut and paste your Staining Protocol here')
        fgs.Add(wx.StaticText(self.sw, -1, 'Paste Staining Protocol'), 0)
        fgs.Add(self.settings_controls[protTAG], 0, wx.EXPAND)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())



########################################################################        
################## SPINNING SETTING PANEL    ###########################
########################################################################
class SpinningSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        spin_list = meta.get_field_instances('AddProcess|Spin|')
        self.spin_next_page_num = 1
        # update the  number of existing cell loading
        if spin_list: 
            self.spin_next_page_num  =  int(spin_list[-1])+1
        for spin_id in spin_list:
            panel = SpinPanel(self.notebook, int(spin_id))
            self.notebook.AddPage(panel, 'Spinning Protocol No: %s'%(spin_id), True)

        # Add the buttons
        addSpinningPageBtn = wx.Button(self, label="Add Spinning Protocols")
        #addSpinningPageBtn.SetBackgroundColour("#33FF33")
        addSpinningPageBtn.Bind(wx.EVT_BUTTON, self.onAddSpinningPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addSpinningPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddSpinningPage(self, event):
        panel = SpinPanel(self.notebook, self.spin_next_page_num)
        self.notebook.AddPage(panel, 'Spinning Protocol No: %s'%(self.spin_next_page_num), True)
        self.spin_next_page_num += 1


class SpinPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)


        #  Spinging  Name
        spinTAG = 'AddProcess|Spin|SpinPrtocolTag|'+str(self.page_counter)
        self.settings_controls[spinTAG] = wx.TextCtrl(self.sw, value=meta.get_field(spinTAG, default=''))
        self.settings_controls[spinTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[spinTAG].SetToolTipString('Type an unique TAG for identifying the spinning protocol')
        fgs.Add(wx.StaticText(self.sw, -1, 'Spinning Protocol Tag'), 0)
        fgs.Add(self.settings_controls[spinTAG], 0, wx.EXPAND)

        # Spinging Protocol
        spinprotTAG = 'AddProcess|Spin|SpinProtocol|'+str(self.page_counter)
        self.settings_controls[spinprotTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(spinprotTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[spinprotTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[spinprotTAG].SetInitialSize((300, 400))
        self.settings_controls[spinprotTAG].SetToolTipString('Cut and paste your Spinning Protocol here')
        fgs.Add(wx.StaticText(self.sw, -1, 'Paste Spinning Protocol'), 0)
        fgs.Add(self.settings_controls[spinprotTAG], 0, wx.EXPAND)


        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
   

########################################################################        
################## WASH SETTING PANEL    ###########################
########################################################################
class WashSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        wash_list = meta.get_field_instances('AddProcess|Wash|')
        self.wash_next_page_num = 1
        # update the  number of existing cell loading
        if wash_list: 
            self.wash_next_page_num  =  int(wash_list[-1])+1
        for wash_id in wash_list:
            panel = WashPanel(self.notebook, int(wash_id))
            self.notebook.AddPage(panel, 'Washing Protocol No: %s'%(wash_id), True)
        
                # Add the buttons
        addWashingPageBtn = wx.Button(self, label="Add Washing Protocols")
        #addWashingPageBtn.SetBackgroundColour("#33FF33")
        addWashingPageBtn.Bind(wx.EVT_BUTTON, self.onAddWashingPage)    

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addWashingPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddWashingPage(self, event):
        panel = WashPanel(self.notebook, self.wash_next_page_num)
        self.notebook.AddPage(panel, 'Washing Protocol No: %s'%(self.wash_next_page_num), True)
        self.wash_next_page_num += 1


class WashPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)


        #  Wash Name
        washTAG = 'AddProcess|Wash|WashPrtocolTag|'+str(self.page_counter)
        self.settings_controls[washTAG] = wx.TextCtrl(self.sw, value=meta.get_field(washTAG, default=''))
        self.settings_controls[washTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[washTAG].SetToolTipString('Type an unique TAG for identifying the washning protocol')
        fgs.Add(wx.StaticText(self.sw, -1, 'Washing Protocol Tag'), 0)
        fgs.Add(self.settings_controls[washTAG], 0, wx.EXPAND)

        # Washing Protocol
        washprotTAG = 'AddProcess|Wash|WashProtocol|'+str(self.page_counter)
        self.settings_controls[washprotTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(washprotTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[washprotTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[washprotTAG].SetInitialSize((300, 400))
        self.settings_controls[washprotTAG].SetToolTipString('Cut and paste your Washing Protocol here')
        fgs.Add(wx.StaticText(self.sw, -1, 'Paste Washing Protocol'), 0)
        fgs.Add(self.settings_controls[washprotTAG], 0, wx.EXPAND)


        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
        
########################################################################        
################## DRY SETTING PANEL    ###########################
########################################################################
class DrySettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        dry_list = meta.get_field_instances('AddProcess|Dry|')
        self.dry_next_page_num = 1
        # update the  number of existing Drying protocols
        if dry_list: 
            self.dry_next_page_num  =  int(dry_list[-1])+1
        for dry_id in dry_list:
            panel = DryPanel(self.notebook, int(dry_id))
            self.notebook.AddPage(panel, 'Drying Protocol No: %s'%(dry_id), True)

        # Add the buttons
        addDryingPageBtn = wx.Button(self, label="Add Drying Protocols")
        #addDryingPageBtn.SetBackgroundColour("#33FF33")
        addDryingPageBtn.Bind(wx.EVT_BUTTON, self.onAddDryingPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addDryingPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddDryingPage(self, event):
        panel = DryPanel(self.notebook, self.dry_next_page_num)
        self.notebook.AddPage(panel, 'Drying Protocol No: %s'%(self.dry_next_page_num), True)
        self.dry_next_page_num += 1

class DryPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)


        #  Drying Agent Name
        drynamTAG = 'AddProcess|Dry|DryProtocolTag|'+str(self.page_counter)
        self.settings_controls[drynamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(drynamTAG, default=''))
        self.settings_controls[drynamTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[drynamTAG].SetToolTipString('Drying Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Drying Agent Name'), 0)
        fgs.Add(self.settings_controls[drynamTAG], 0, wx.EXPAND)

        # Drying Protocol
        protTAG = 'AddProcess|Dry|Protocol|'+str(self.page_counter)
        self.settings_controls[protTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(protTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[protTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[protTAG].SetInitialSize((300, 400))
        self.settings_controls[protTAG].SetToolTipString('Cut and paste your Drying Protocol here')
        fgs.Add(wx.StaticText(self.sw, -1, 'Paste Drying Protocol'), 0)
        fgs.Add(self.settings_controls[protTAG], 0, wx.EXPAND)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())

            
########################################################################        
################## MEDIUM SETTING PANEL    ###########################
########################################################################
class MediumSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        medium_list = meta.get_field_instances('AddProcess|Medium|')
        self.medium_next_page_num = 1
        # update the  number of existing Drying protocols
        if medium_list: 
            self.medium_next_page_num  =  int(medium_list[-1])+1
        for medium_id in medium_list:
            panel = MediumPanel(self.notebook, int(medium_id))
            self.notebook.AddPage(panel, 'Medium No: %s'%(medium_id), True)

        # Add the buttons
        addMediumPageBtn = wx.Button(self, label="Add Medium ")
        #addMediumPageBtn.SetBackgroundColour("#33FF33")
        addMediumPageBtn.Bind(wx.EVT_BUTTON, self.onAddMediumPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addMediumPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddMediumPage(self, event):
        panel = MediumPanel(self.notebook, self.medium_next_page_num)
        self.notebook.AddPage(panel, 'Medium No: %s'%(self.medium_next_page_num), True)
        self.medium_next_page_num += 1

class MediumPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)


        #  Mediuming Agent Name
        mediumnamTAG = 'AddProcess|Medium|MediumNameTag|'+str(self.page_counter)
        self.settings_controls[mediumnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(mediumnamTAG, default=''))
        self.settings_controls[mediumnamTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[mediumnamTAG].SetToolTipString('Medium Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Name'), 0)
        fgs.Add(self.settings_controls[mediumnamTAG], 0, wx.EXPAND)

        # Medium Additives
        medaddTAG = 'AddProcess|Medium|MediumAdditives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(medaddTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetInitialSize((300, 400))
        self.settings_controls[medaddTAG].SetToolTipString('Type other medium additives')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium additives'), 0)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())

########################################################################        
################## INCUBATOR SETTING PANEL    ###########################
########################################################################            
class IncubatorSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        incubator_list = meta.get_field_instances('AddProcess|Incubator|')
        self.incubator_next_page_num = 1
        # update the  number of existing Drying protocols
        if incubator_list: 
            self.incubator_next_page_num  =  int(incubator_list[-1])+1
        for incubator_id in incubator_list:
            panel = IncubatorPanel(self.notebook, int(incubator_id))
            self.notebook.AddPage(panel, 'Incubator No: %s'%(incubator_id), True)

        # Add the buttons
        addIncubatorPageBtn = wx.Button(self, label="Add Incubator ")
        #addIncubatorPageBtn.SetBackgroundColour("#33FF33")
        addIncubatorPageBtn.Bind(wx.EVT_BUTTON, self.onAddIncubatorPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addIncubatorPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddIncubatorPage(self, event):
        panel = IncubatorPanel(self.notebook, self.incubator_next_page_num)
        self.notebook.AddPage(panel, 'Incubator No: %s'%(self.incubator_next_page_num), True)
        self.incubator_next_page_num += 1
        
        
class IncubatorPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)

        #----------- Microscope Labels and Text Controler-------        
        #-- Heading --#
        heading = 'Incubator Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #--Manufacture--#
        incbmfgTAG = 'AddProcess|Incubator|Manufacter|'+str(self.page_counter)
        self.settings_controls[incbmfgTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(incbmfgTAG, default=''))
        self.settings_controls[incbmfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[incbmfgTAG].SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(self.settings_controls[incbmfgTAG], 0, wx.EXPAND)
        #--Model--#
        incbmdlTAG = 'AddProcess|Incubator|Model|'+str(self.page_counter)
        self.settings_controls[incbmdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(incbmdlTAG, default=''))
        self.settings_controls[incbmdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbmdlTAG].SetToolTipString('Model number of the Incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(self.settings_controls[incbmdlTAG], 0, wx.EXPAND)
        #--Temperature--#
        incbTempTAG = 'AddProcess|Incubator|Temp|'+str(self.page_counter)
        self.settings_controls[incbTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(incbTempTAG, default=''))
        self.settings_controls[incbTempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbTempTAG].SetToolTipString('Temperature of the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
        fgs.Add(self.settings_controls[incbTempTAG], 0, wx.EXPAND)
        #--Carbondioxide--#
        incbCarbonTAG = 'AddProcess|Incubator|C02|'+str(self.page_counter)
        self.settings_controls[incbCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(incbCarbonTAG, default=''))
        self.settings_controls[incbCarbonTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
        fgs.Add(self.settings_controls[incbCarbonTAG], 0, wx.EXPAND)
        #--Humidity--#
        incbHumTAG = 'AddProcess|Incubator|Humidity|'+str(self.page_counter)
        self.settings_controls[incbHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(incbHumTAG, default=''))
        self.settings_controls[incbHumTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbHumTAG].SetToolTipString('Humidity at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
        fgs.Add(self.settings_controls[incbHumTAG], 0, wx.EXPAND)
        #--Pressure--#
        incbPressTAG = 'AddProcess|Incubator|Pressure|'+str(self.page_counter)
        self.settings_controls[incbPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(incbPressTAG, default=''))
        self.settings_controls[incbPressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbPressTAG].SetToolTipString('Pressure at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
        fgs.Add(self.settings_controls[incbPressTAG], 0, wx.EXPAND)



        #--Create the Adding button--#
        #addBut = wx.Button(self.sw, -1, label="Record Flowcytometer %s settings" % self.page_counter)
        #addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
        #fgs.Add(addBut, 0, wx.ALL, 5)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
            

            
########################################################################        
################## TIMELAPSE SETTING PANEL    ##########################
########################################################################
class TLMSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        tlm_list = meta.get_field_instances('DataAcquis|TLM|')
        self.tlm_next_page_num = 1
        # update the  number of existing cell loading
        if tlm_list: 
            self.tlm_next_page_num  =  int(tlm_list[-1])+1
        for tlm_id in tlm_list:
            panel = TLMPanel(self.notebook, int(tlm_id))
            self.notebook.AddPage(panel, 'Timelapse Image Format No: %s'%(tlm_id), True)

        # Add the buttons
        addTLMPageBtn = wx.Button(self, label="Add Timelapse Image Format")
        #addTLMPageBtn.SetBackgroundColour("#33FF33")
        addTLMPageBtn.Bind(wx.EVT_BUTTON, self.onAddTLMPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addTLMPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddTLMPage(self, event):
        panel = TLMPanel(self.notebook, self.tlm_next_page_num)
        self.notebook.AddPage(panel, 'Timelapse Image Format No: %s'%(self.tlm_next_page_num), True)
        self.tlm_next_page_num += 1

class TLMPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)

        #-- Microscope selection ---#
        tlmselctTAG = 'DataAcquis|TLM|MicroscopeInstance|'+str(self.page_counter)
        self.settings_controls[tlmselctTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmselctTAG, default=''))        
        showInstBut = wx.Button(self.sw, -1, 'Show Microscope settings', (100,100))
        showInstBut.Bind (wx.EVT_BUTTON, self.OnShowDialog)
        self.settings_controls[tlmselctTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope Instance'), 0)
        fgs.Add(self.settings_controls[tlmselctTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)
        #-- Image Format ---#
        tlmfrmtTAG = 'DataAcquis|TLM|Format|'+str(self.page_counter)
        self.settings_controls[tlmfrmtTAG] = wx.Choice(self.sw, -1,  choices=['tiff', 'jpeg', 'stk'])
        if meta.get_field(tlmfrmtTAG) is not None:
            self.settings_controls[tlmfrmtTAG].SetStringSelection(meta.get_field(tlmfrmtTAG))
        self.settings_controls[tlmfrmtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[tlmfrmtTAG].SetToolTipString('Image Format')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Image Format'), 0)
        fgs.Add(self.settings_controls[tlmfrmtTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #-- Channel ---#
        tlmchTAG = 'DataAcquis|TLM|Channel|'+str(self.page_counter)
        self.settings_controls[tlmchTAG] = wx.Choice(self.sw, -1,  choices=['Red', 'Green', 'Blue'])
        if meta.get_field(tlmchTAG) is not None:
            self.settings_controls[tlmchTAG].SetStringSelection(meta.get_field(tlmchTAG))
        self.settings_controls[tlmchTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[tlmchTAG].SetToolTipString('Channel used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
        fgs.Add(self.settings_controls[tlmchTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Time Interval
        tlmintTAG = 'DataAcquis|TLM|TimeInterval|'+str(self.page_counter)
        self.settings_controls[tlmintTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmintTAG, default=''))
        self.settings_controls[tlmintTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmintTAG].SetToolTipString('Time interval image was acquired')
        fgs.Add(wx.StaticText(self.sw, -1, 'Time Interval (min)'), 0)
        fgs.Add(self.settings_controls[tlmintTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Total Frame/Pane Number
        tlmfrmTAG = 'DataAcquis|TLM|FrameNumber|'
        self.settings_controls[tlmfrmTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmfrmTAG, default=''))
        self.settings_controls[tlmfrmTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmfrmTAG].SetToolTipString('Total Frame/Pane Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Total Frame/Pane Number'), 0)
        fgs.Add(self.settings_controls[tlmfrmTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Stacking Order
        tlmstkTAG = 'DataAcquis|TLM|StackProcess|'+str(self.page_counter)
        self.settings_controls[tlmstkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmstkTAG, default=''))
        self.settings_controls[tlmstkTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmstkTAG].SetToolTipString('Stacking Order')
        fgs.Add(wx.StaticText(self.sw, -1, 'Stacking Order'), 0)
        fgs.Add(self.settings_controls[tlmstkTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Size
        tlmpxlTAG = 'DataAcquis|TLM|PixelSize|'+str(self.page_counter)
        self.settings_controls[tlmpxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxlTAG, default=''))
        self.settings_controls[tlmpxlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmpxlTAG].SetToolTipString('Pixel Size')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0)
        fgs.Add(self.settings_controls[tlmpxlTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Conversion
        tlmpxcnvTAG = 'DataAcquis|TLM|PixelConvert|'+str(self.page_counter)
        self.settings_controls[tlmpxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxcnvTAG, default=''))
        self.settings_controls[tlmpxcnvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmpxcnvTAG].SetToolTipString('Pixel Conversion')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0)
        fgs.Add(self.settings_controls[tlmpxcnvTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Software
        tlmsoftTAG = 'DataAcquis|TLM|Software|'+str(self.page_counter)
        self.settings_controls[tlmsoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmsoftTAG, default=''))
        self.settings_controls[tlmsoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmsoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
        fgs.Add(self.settings_controls[tlmsoftTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def OnShowDialog(self, event):     
        # link with the dynamic experiment settings
        meta = ExperimentSettings.getInstance()
        attributes = meta.get_attribute_list('Instrument|Microscope') 
        
        #check whether there is at least one attributes
        if not attributes:
            dial = wx.MessageDialog(None, 'No Instances exists!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        #show the popup table 
        dia = InstanceListDialog(self, 'Instrument|Microscope', selection_mode = False)
        if dia.ShowModal() == wx.ID_OK:
            if dia.listctrl.get_selected_instances() != []:
                instance = dia.listctrl.get_selected_instances()[0]
                tlmselctTAG = 'DataAcquis|TLM|MicroscopeInstance|'+str(self.page_counter)
                self.settings_controls[tlmselctTAG].SetValue(str(instance))
        dia.Destroy()

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
            
        
########################################################################        
################## STATIC SETTING PANEL    ##########################
########################################################################
class HCSSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        hcs_list = meta.get_field_instances('DataAcquis|HCS|')
        self.hcs_next_page_num = 1
        # update the  number of existing cell loading
        if hcs_list: 
            self.hcs_next_page_num  =  int(hcs_list[-1])+1
        for hcs_id in hcs_list:
            panel = HCSPanel(self.notebook, int(hcs_id))
            self.notebook.AddPage(panel, 'HCS Image Format No: %s'%(hcs_id), True)
            
        # Add the buttons
        addHCSPageBtn = wx.Button(self, label="Add HCS File Format")
        #addHCSPageBtn.SetBackgroundColour("#33FF33")
        addHCSPageBtn.Bind(wx.EVT_BUTTON, self.onAddHCSPage)    

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addHCSPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddHCSPage(self, event):
        panel = HCSPanel(self.notebook, self.hcs_next_page_num)
        self.notebook.AddPage(panel, 'HCS Image Format No: %s'%(self.hcs_next_page_num), True)
        self.hcs_next_page_num += 1


class HCSPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)
        
        #-- Microscope selection ---#
        hcsselctTAG = 'DataAcquis|HCS|MicroscopeInstance|'+str(self.page_counter)
        self.settings_controls[hcsselctTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcsselctTAG, default=''))
        showInstBut = wx.Button(self.sw, -1, 'Show Microscope settings', (100,100))
        showInstBut.Bind (wx.EVT_BUTTON, self.OnShowDialog) 
        self.settings_controls[hcsselctTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcsselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope'), 0)
        fgs.Add(self.settings_controls[hcsselctTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)
        #-- Image Format ---#
        hcsfrmtTAG = 'DataAcquis|HCS|Format|'+str(self.page_counter)
        self.settings_controls[hcsfrmtTAG] = wx.Choice(self.sw, -1,  choices=['tiff', 'jpeg', 'stk'])
        if meta.get_field(hcsfrmtTAG) is not None:
            self.settings_controls[hcsfrmtTAG].SetStringSelection(meta.get_field(hcsfrmtTAG))
        self.settings_controls[hcsfrmtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[hcsfrmtTAG].SetToolTipString('Image Format')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Image Format'), 0)
        fgs.Add(self.settings_controls[hcsfrmtTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #-- Channel ---#
        hcschTAG = 'DataAcquis|HCS|Channel|'+str(self.page_counter)
        self.settings_controls[hcschTAG] = wx.Choice(self.sw, -1,  choices=['Red', 'Green', 'Blue'])
        if meta.get_field(hcschTAG) is not None:
            self.settings_controls[hcschTAG].SetStringSelection(meta.get_field(hcschTAG))
        self.settings_controls[hcschTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[hcschTAG].SetToolTipString('Channel used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
        fgs.Add(self.settings_controls[hcschTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Size
        hcspxlTAG = 'DataAcquis|HCS|PixelSize|'+str(self.page_counter)
        self.settings_controls[hcspxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxlTAG, default=''))
        self.settings_controls[hcspxlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcspxlTAG].SetToolTipString('Pixel Size')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0)
        fgs.Add(self.settings_controls[hcspxlTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Conversion
        hcspxcnvTAG = 'DataAcquis|HCS|PixelConvert|'+str(self.page_counter)
        self.settings_controls[hcspxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxcnvTAG, default=''))
        self.settings_controls[hcspxcnvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcspxcnvTAG].SetToolTipString('Pixel Conversion')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0)
        fgs.Add(self.settings_controls[hcspxcnvTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Software
        hcssoftTAG = 'DataAcquis|HCS|Software|'+str(self.page_counter)
        self.settings_controls[hcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcssoftTAG, default=''))
        self.settings_controls[hcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcssoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
        fgs.Add(self.settings_controls[hcssoftTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    
    def OnShowDialog(self, event):     
        # link with the dynamic experiment settings
        meta = ExperimentSettings.getInstance()
        attributes = meta.get_attribute_list('Instrument|Microscope') 
        
        #check whether there is at least one attributes
        if not attributes:
            dial = wx.MessageDialog(None, 'No Instances exists!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        #show the popup table 
        dia = InstanceListDialog(self, 'Instrument|Microscope', selection_mode = False)
        if dia.ShowModal() == wx.ID_OK:
            if dia.listctrl.get_selected_instances() != []:
                instance = dia.listctrl.get_selected_instances()[0]
                hcsselctTAG = 'DataAcquis|HCS|MicroscopeInstance|'+str(self.page_counter)
                self.settings_controls[hcsselctTAG].SetValue(str(instance))
        dia.Destroy()

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
	    


########################################################################        
################## FLOW SETTING PANEL    ##########################
########################################################################
class FCSSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        flow_list = meta.get_field_instances('DataAcquis|FCS|')
        self.flow_next_page_num = 1
        # update the  number of existing cell loading
        if flow_list: 
            self.flow_next_page_num  =  int(flow_list[-1])+1
        for flow_id in flow_list:
            panel = FCSPanel(self.notebook, int(flow_id))
            self.notebook.AddPage(panel, 'FCS Format No: %s'%(flow_id), True)

        # Add the buttons
        addFlowPageBtn = wx.Button(self, label="Add FCS File Format")
        #addFlowPageBtn.SetBackgroundColour("#33FF33")
        addFlowPageBtn.Bind(wx.EVT_BUTTON, self.onAddFlowPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFlowPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddFlowPage(self, event):
        panel = FCSPanel(self.notebook, self.flow_next_page_num)
        self.notebook.AddPage(panel, 'FCS Format No: %s'%(self.flow_next_page_num), True)
        self.flow_next_page_num += 1


class FCSPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)

        #-- FlowCytometer selection ---#
        fcsselctTAG = 'DataAcquis|FCS|FlowcytInstance|'+str(self.page_counter)
        self.settings_controls[fcsselctTAG] = wx.TextCtrl(self.sw, value=meta.get_field(fcsselctTAG, default=''))
        self.settings_controls[fcsselctTAG].SetToolTipString('Flow cytometer used for data acquisition')
        showInstBut = wx.Button(self.sw, -1, 'Show Flow Cytometer settings', (100,100))
        showInstBut.Bind (wx.EVT_BUTTON, self.OnShowDialog)
        self.settings_controls[fcsselctTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Flow Cytometer'), 0)
        fgs.Add(self.settings_controls[fcsselctTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)
        #-- Image Format ---#
        fcsfrmtTAG = 'DataAcquis|FCS|Format|'+str(self.page_counter)
        self.settings_controls[fcsfrmtTAG] = wx.Choice(self.sw, -1,  choices=['fcs1.0', 'fcs2.0', 'fcs3.0'])
        self.settings_controls[fcsfrmtTAG].SetStringSelection('')
        if meta.get_field(fcsfrmtTAG) is not None:
            self.settings_controls[fcsfrmtTAG].SetStringSelection(meta.get_field(fcsfrmtTAG))
        self.settings_controls[fcsfrmtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[fcsfrmtTAG].SetToolTipString('FCS file Format')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select FCS file Format'), 0)
        fgs.Add(self.settings_controls[fcsfrmtTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #-- Channel ---#
        fcschTAG = 'DataAcquis|FCS|Channel|'+str(self.page_counter)
        self.settings_controls[fcschTAG] = wx.Choice(self.sw, -1,  choices=['FL8', 'FL6', 'FL2'])
        if meta.get_field(fcschTAG) is not None:
            self.settings_controls[fcschTAG].SetStringSelection(meta.get_field(fcschTAG))
        self.settings_controls[fcschTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[fcschTAG].SetToolTipString('Channel used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
        fgs.Add(self.settings_controls[fcschTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Software
        fcssoftTAG = 'DataAcquis|FCS|Software|'+str(self.page_counter)
        self.settings_controls[fcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(fcssoftTAG, default=''))
        self.settings_controls[fcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[fcssoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
        fgs.Add(self.settings_controls[fcssoftTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    def OnShowDialog(self, event):     
        # link with the dynamic experiment settings
        meta = ExperimentSettings.getInstance()
        attributes = meta.get_attribute_list('Instrument|Flowcytometer') 
        
        #check whether there is at least one attributes
        if not attributes:
            dial = wx.MessageDialog(None, 'No Instances exists!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        #show the popup table 
        dia = InstanceListDialog(self, 'Instrument|Flowcytometer', selection_mode = False)
        if dia.ShowModal() == wx.ID_OK:
            if dia.listctrl.get_selected_instances() != []:
                instance = dia.listctrl.get_selected_instances()[0]
                fcsselctTAG = 'DataAcquis|FCS|FlowcytInstance|'+str(self.page_counter)
                self.settings_controls[ fcsselctTAG].SetValue(str(instance))
        dia.Destroy()


    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())


        
if __name__ == '__main__':
    app = wx.App(False)
    
    frame = wx.Frame(None, title='ProtocolNavigator', size=(650, 750))
    p = ExperimentSettingsWindow(frame)
    
    frame.SetMenuBar(wx.MenuBar())
    fileMenu = wx.Menu()
    saveSettingsMenuItem = fileMenu.Append(-1, 'Save settings\tCtrl+S', help='')
    loadSettingsMenuItem = fileMenu.Append(-1, 'Load settings\tCtrl+O', help='')
    #frame.Bind(wx.EVT_MENU, on_save_settings, saveSettingsMenuItem)
    #frame.Bind(wx.EVT_MENU, on_load_settings, loadSettingsMenuItem) 
    frame.GetMenuBar().Append(fileMenu, 'File')


    frame.Show()
    app.MainLoop()