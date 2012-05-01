#!/usr/bin/env python

import wx
import os
import re
import sys
import operator
import  wx.calendar
import wx.lib.agw.flatnotebook as fnb
import wx.lib.mixins.listctrl as listmix
import wx.lib.filebrowsebutton
import  wx.gizmos   as  gizmos
import string, os
import wx.lib.agw.foldpanelbar as fpb
import experimentsettings as exp
import wx.html
import webbrowser
import wx.media
from functools import partial
from experimentsettings import *
from instancelist import *
from utils import *
from makechannel import ChannelBuilder
from stepbuilder import StepBuilder
from passagestepwriter import *


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
        lbl = self.tree.AppendItem(stc, 'Staining')
        self.tree.AppendItem(lbl, 'Dye')
        self.tree.AppendItem(lbl, 'Immunofluorescence')
        self.tree.AppendItem(lbl, 'Genetic')
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
	nte = self.tree.AppendItem(stc, 'Notes')
            
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
    
    def OnLeafSelect(self):
	self.tree.ExpandAll()
    
    def ShowInstance(self, tag):
	
	meta =ExperimentSettings.getInstance()
	
	self.settings_panel.Destroy()
	self.settings_container.Sizer.Clear()
	
	if get_tag_type(tag) == 'CellTransfer' and get_tag_event(tag) == 'Seed':
	    self.settings_panel = CellSeedSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'CellTransfer' and get_tag_event(tag) == 'Harvest':
	    self.settings_panel = CellHarvestSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'Perturbation' and get_tag_event(tag) == 'Chem':
	    self.settings_panel = ChemicalSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)	
	if get_tag_type(tag) == 'Perturbation' and get_tag_event(tag) == 'Bio':
            self.settings_panel = BiologicalSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'Staining' and get_tag_event(tag) == 'Dye':
	    self.settings_panel = DyeSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'Staining' and get_tag_event(tag) == 'Immuno':
	    self.settings_panel = ImmunoSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'Staining' and get_tag_event(tag) == 'Genetic':
	    self.settings_panel = GeneticSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'AddProcess' and get_tag_event(tag) == 'Spin':
	    self.settings_panel = SpinningSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)	
	if get_tag_type(tag) == 'AddProcess' and get_tag_event(tag) == 'Wash':
	    self.settings_panel = WashSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'AddProcess' and get_tag_event(tag) == 'Dry':
	    self.settings_panel = DrySettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'AddProcess' and get_tag_event(tag) == 'Medium':
	    self.settings_panel = MediumSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'AddProcess' and get_tag_event(tag) == 'Incubator':
	    self.settings_panel = IncubatorSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)	
	if get_tag_type(tag) == 'DataAcquis' and get_tag_event(tag) == 'TLM':  # may link with microscope settings??
	    self.settings_panel = TLMSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'DataAcquis' and get_tag_event(tag) == 'HCS':  # may link with microscope settings??
	    self.settings_panel = HCSSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)	
	if get_tag_type(tag) == 'DataAcquis' and get_tag_event(tag) == 'FCS':  # may link with flowcytometer settings??
	    self.settings_panel = FCSSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)
	if get_tag_type(tag) == 'Notes':  
	    self.settings_panel = NoteSettingPanel(self.settings_container)
	    self.settings_panel.notebook.SetSelection(int(get_tag_instance(tag))-1)	
	    
	self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)        
	self.settings_container.Layout()
	self.settings_panel.ClearBackground()
	self.settings_panel.Refresh()
	


                
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
            
        elif self.tree.GetItemText(item) == 'Dye':
            self.settings_panel = DyeSettingPanel(self.settings_container)        
        elif self.tree.GetItemText(item) == 'Immunofluorescence':
            self.settings_panel =  ImmunoSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Genetic':
            self.settings_panel =  GeneticSettingPanel(self.settings_container)
                    
        elif self.tree.GetItemText(item) == 'Timelapse Image':
            self.settings_panel = TLMSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Static Image':
            self.settings_panel = HCSSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Flow Cytometer Files':
            self.settings_panel = FCSSettingPanel(self.settings_container)
            
        elif self.tree.GetItemText(item) == 'Notes':
                    self.settings_panel = NoteSettingPanel(self.settings_container)
          
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
        self.settings_controls[titleTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(titleTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[titleTAG].SetInitialSize((300, 20))
        self.settings_controls[titleTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[titleTAG].SetToolTipString('Insert the title of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Title'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[titleTAG], 0, wx.EXPAND)
        # Experiment Aim
        aimTAG = 'Overview|Project|Aims'
        self.settings_controls[aimTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(aimTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[aimTAG].SetInitialSize((300, 50))
        self.settings_controls[aimTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[aimTAG].SetToolTipString('Describe here the aim of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Aim'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[aimTAG], 0, wx.EXPAND)
	# Experiment Aim
	fundTAG = 'Overview|Project|Fund'
	self.settings_controls[fundTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(fundTAG, default=''), style=wx.TE_PROCESS_ENTER)
	self.settings_controls[fundTAG].SetInitialSize((300, 20))
	self.settings_controls[fundTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[fundTAG].SetToolTipString('Project funding codes')
	fgs.Add(wx.StaticText(self.sw, -1, 'Funding Code'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[fundTAG], 0, wx.EXPAND)	
        # Keywords
        keyTAG = 'Overview|Project|Keywords'
        self.settings_controls[keyTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(keyTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[keyTAG].SetInitialSize((300, 50))
        self.settings_controls[keyTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[keyTAG].SetToolTipString('Keywords that indicates the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Keywords'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[keyTAG], 0, wx.EXPAND)
        # Experiment Number
        exnumTAG = 'Overview|Project|ExptNum'
        self.settings_controls[exnumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
        if meta.get_field(exnumTAG) is not None:
            self.settings_controls[exnumTAG].SetStringSelection(meta.get_field(exnumTAG))
        self.settings_controls[exnumTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        self.settings_controls[exnumTAG].SetToolTipString('Experiment Number....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Number'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Start Date'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[exdateTAG], 0, wx.EXPAND)
        # Publication
        exppubTAG = 'Overview|Project|Publications'
        self.settings_controls[exppubTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(exppubTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[exppubTAG].SetInitialSize((300, 50))
        self.settings_controls[exppubTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[exppubTAG].SetToolTipString('Experiment related publication list')
        fgs.Add(wx.StaticText(self.sw, -1, 'Related Publications'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[exppubTAG], 0, wx.EXPAND)
        # Experimenter Name
        expnameTAG = 'Overview|Project|Experimenter'
        self.settings_controls[expnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(expnameTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[expnameTAG].SetInitialSize((300, 20))
        self.settings_controls[expnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[expnameTAG].SetToolTipString('Name of experimenter(s)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Name of Experimenter(s)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[expnameTAG], 0, wx.EXPAND)
        # Institution Name
        instnameTAG = 'Overview|Project|Institution'
        self.settings_controls[instnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(instnameTAG, default=''))
        self.settings_controls[instnameTAG].SetInitialSize((300, 20))
        self.settings_controls[instnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[instnameTAG].SetToolTipString('Name of Institution')
        fgs.Add(wx.StaticText(self.sw, -1, 'Name of Institution'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[instnameTAG], 0, wx.EXPAND)
        # Department Name
        deptnameTAG = 'Overview|Project|Department'
        self.settings_controls[deptnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(deptnameTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[deptnameTAG].SetInitialSize((300, 20))
        self.settings_controls[deptnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[deptnameTAG].SetToolTipString('Name of the Department')
        fgs.Add(wx.StaticText(self.sw, -1, 'Department Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[deptnameTAG], 0, wx.EXPAND)
        # Address
        addressTAG = 'Overview|Project|Address'
        self.settings_controls[addressTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(addressTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[addressTAG].SetInitialSize((300, 50))
        self.settings_controls[addressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[addressTAG].SetToolTipString('Postal address and other contact details')
        fgs.Add(wx.StaticText(self.sw, -1, 'Address'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[addressTAG], 0, wx.EXPAND)
        # Status
        statusTAG = 'Overview|Project|Status'
        self.settings_controls[statusTAG] = wx.Choice(self.sw, -1, choices=['Complete', 'Ongoing', 'Pending', 'Discarded'])
        if meta.get_field(statusTAG) is not None:
            self.settings_controls[statusTAG].SetStringSelection(meta.get_field(statusTAG))
        self.settings_controls[statusTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[statusTAG].SetToolTipString('Status of the experiment, e.g. Complete, On-going, Discarded')
        fgs.Add(wx.StaticText(self.sw, -1, 'Status'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[statusTAG], 0, wx.EXPAND)

        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)


########################################################################        
######          STOCK CULTURE SETTING PANEL                       ######
########################################################################
class StockCultureSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'StockCulture|Sample'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = StockCulturePanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	#loadTabBtn = wx.Button(self, label="Load Instance")
	#loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	#btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = StockCulturePanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)


class StockCulturePanel(wx.Panel):
    def __init__(self, parent, stk_id=None):
        wx.Panel.__init__(self, parent=parent)
	
	self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
	
	self.testDict = {}
        if stk_id is None:  
            stk_list = meta.get_field_instances('StockCulture|Sample|')
            #Find the all instances of stkroscope
            if stk_list:
                stk_id =  max(map(int, stk_list))+1
            else:
                stk_id = 1
        self.stk_id = stk_id
	
	self.protocol = 'StockCulture|Sample|%s'%str(self.stk_id)
	self.tag_stump = 'StockCulture|Sample'
	self.instance = str(self.stk_id)
	self.currpassageNo = 0
	
        self.top_panel = wx.Panel(self)
	self.bot_panel = wx.ScrolledWindow(self)	
        
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
    
        #----------- Labels and Text Controler-------        
        # Cell Line Name
        cellLineTAG = 'StockCulture|Sample|CellLine|%s'%str(self.stk_id)
        self.settings_controls[cellLineTAG] = wx.TextCtrl(self.top_panel, style=wx.TE_PROCESS_ENTER, value=meta.get_field(cellLineTAG, default=''))
        self.settings_controls[cellLineTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[cellLineTAG].SetToolTipString('Cell Line selection')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Cell Line'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[cellLineTAG], 0, wx.EXPAND)               
        # ATCC reference
        acttTAG = 'StockCulture|Sample|ATCCref|%s'%str(self.stk_id)
        self.settings_controls[acttTAG] = wx.TextCtrl(self.top_panel, style=wx.TE_PROCESS_ENTER, value=meta.get_field(acttTAG, default=''))
        self.settings_controls[acttTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[acttTAG].SetToolTipString('ATCC reference')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Reference'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[acttTAG], 0, wx.EXPAND) 
        # Taxonomic ID
        taxIdTAG = 'StockCulture|Sample|Organism|%s'%str(self.stk_id)
	organism_choices =['Homo Sapiens', 'Mus Musculus', 'Rattus Norvegicus', 'Other']
	self.settings_controls[taxIdTAG]= wx.ListBox(self.top_panel, -1, wx.DefaultPosition, (120,30), organism_choices, wx.LB_SINGLE)
	if meta.get_field(taxIdTAG) is not None:
	    self.settings_controls[taxIdTAG].Append(meta.get_field(taxIdTAG))
	    self.settings_controls[taxIdTAG].SetStringSelection(meta.get_field(taxIdTAG))
	self.settings_controls[taxIdTAG].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[taxIdTAG].SetToolTipString('Taxonomic ID of the species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Organism'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[taxIdTAG], 0, wx.EXPAND)
        # Gender
        gendTAG = 'StockCulture|Sample|Gender|%s'%str(self.stk_id)
        self.settings_controls[gendTAG] = wx.Choice(self.top_panel, -1,  choices=['Male', 'Female', 'Neutral'])
        if meta.get_field(gendTAG) is not None:
            self.settings_controls[gendTAG].SetStringSelection(meta.get_field(gendTAG))
        self.settings_controls[gendTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[gendTAG].SetToolTipString('Gender of the organism')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Gender'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[gendTAG], 0, wx.EXPAND)        
        # Age
        ageTAG ='StockCulture|Sample|Age|%s'%str(self.stk_id)
        self.settings_controls[ageTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(ageTAG, default=''))
        self.settings_controls[ageTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[ageTAG].SetToolTipString('Age of the organism in days when the cells were collected. .')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Age of Organism (days)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[ageTAG], 0, wx.EXPAND)
        # Organ
        organTAG = 'StockCulture|Sample|Organ|%s'%str(self.stk_id)
        self.settings_controls[organTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(organTAG, default=''))
        self.settings_controls[organTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[organTAG].SetToolTipString('Organ name from where the cell were collected. eg. Heart, Lung, Bone etc')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Organ'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[organTAG], 0, wx.EXPAND)
        # Tissue
        tissueTAG = 'StockCulture|Sample|Tissue|%s'%str(self.stk_id)
        self.settings_controls[tissueTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(tissueTAG, default=''))
        self.settings_controls[tissueTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tissueTAG].SetToolTipString('Tissue from which the cells were collected')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Tissue'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tissueTAG], 0, wx.EXPAND)
        # Pheotype
        phtypTAG = 'StockCulture|Sample|Phenotype|%s'%str(self.stk_id)
        self.settings_controls[phtypTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(phtypTAG, default=''))
        self.settings_controls[phtypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[phtypTAG].SetToolTipString('Phenotypic examples Colour Height OR any other value descriptor')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Phenotype'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[phtypTAG], 0, wx.EXPAND)
        # Genotype
        gentypTAG = 'StockCulture|Sample|Genotype|%s'%str(self.stk_id)
        self.settings_controls[gentypTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(gentypTAG, default=''))
        self.settings_controls[gentypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[gentypTAG].SetToolTipString('Wild type or mutant etc. (single word)')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Genotype'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[gentypTAG], 0, wx.EXPAND)
        # Strain
        strainTAG = 'StockCulture|Sample|Strain|%s'%str(self.stk_id)
        self.settings_controls[strainTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(strainTAG, default=''))
        self.settings_controls[strainTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[strainTAG].SetToolTipString('Starin of that cell line eGFP, Wild type etc')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Strain'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[strainTAG], 0, wx.EXPAND)
        #  Passage Number
        passTAG = 'StockCulture|Sample|OrgPassageNo|%s'%str(self.stk_id)
        self.settings_controls[passTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(passTAG, default=''))
        self.settings_controls[passTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[passTAG].SetToolTipString('Numeric value of the passage of the cells under investigation')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Original Passage Number'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[passTAG], 0, wx.EXPAND)
        #  Cell Density
        densityTAG = 'StockCulture|Sample|Density|%s'%str(self.stk_id)
        self.settings_controls[densityTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(densityTAG, default=''))
        self.settings_controls[densityTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[densityTAG].SetToolTipString('Numeric value of the cell density at the culture flask')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Cell Density'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[densityTAG], 0, wx.EXPAND)
        # Duplicate button        
        #self.copyStockCulturePageBtn = wx.Button(self.sw, -1, label="Duplicate Settings")
        #self.copyStockCulturePageBtn.Bind(wx.EVT_BUTTON, self.onCopyStockCulturePage)
	self.recordPassageBtn = wx.Button(self.top_panel, -1, label="Record Passage steps")
	self.recordPassageBtn.Bind(wx.EVT_BUTTON, self.onRecordPassage)
        fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
        fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
        fgs.Add(self.recordPassageBtn, 0, wx.EXPAND)
        #fgs.Add(self.copyStockCulturePageBtn, 0, wx.EXPAND)

        #---------------Layout with sizers---------------
	self.fpbsizer = wx.FlexGridSizer(cols=1, vgap=5)	
	
	self.showPassages()

        self.top_panel.SetSizer(fgs)
        self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)

	
        #self.Show()   	
	
        #self.sw.SetSizer(fgs)
        #self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        #self.Sizer = wx.BoxSizer(wx.VERTICAL)
        #self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    #def onCopyStockCulturePage(self, event):
            
        #meta = ExperimentSettings.getInstance()
        ##Get the maximum microscope id from the list
        #stk_list = meta.get_field_instances('StockCulture|Sample|')
        
        #if not stk_list:
            #dial = wx.MessageDialog(None, 'No instance to duplicate', 'Error', wx.OK | wx.ICON_ERROR)
            #dial.ShowModal()  
            #return
                    
        #new_stk_id =  max(map(int, stk_list))+1
        ##Copy all data fields from the selected instances
        #meta.set_field('StockCulture|Sample|CellLine|%s'%str(new_stk_id),    meta.get_field('StockCulture|Sample|CellLine|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|ATCCref|%s'%str(new_stk_id),     meta.get_field('StockCulture|Sample|ATCCref|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Organism|%s'%str(new_stk_id),       meta.get_field('StockCulture|Sample|Organism|%s'%str(self.stk_id)), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Gender|%s'%str(new_stk_id),      meta.get_field('StockCulture|Sample|Gender|%s'%str(self.stk_id)), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Age|%s'%str(new_stk_id),         meta.get_field('StockCulture|Sample|Age|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Organ|%s'%str(new_stk_id),       meta.get_field('StockCulture|Sample|Organ|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Tissue|%s'%str(new_stk_id),       meta.get_field('StockCulture|Sample|Tissue|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Phenotype|%s'%str(new_stk_id),   meta.get_field('StockCulture|Sample|Phenotype|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Genotype|%s'%str(new_stk_id),    meta.get_field('StockCulture|Sample|Genotype|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Strain|%s'%str(new_stk_id),      meta.get_field('StockCulture|Sample|Strain|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|PassageNumber|%s'%str(new_stk_id), meta.get_field('StockCulture|Sample|PassageNumber|%s'%str(self.stk_id), default=''), notify_subscribers =False)
        #meta.set_field('StockCulture|Sample|Density|%s'%str(new_stk_id),      meta.get_field('StockCulture|Sample|Density|%s'%str(self.stk_id), default=''))
      
        #panel = StockCulturePanel(self.Parent, new_stk_id)
        #self.Parent.AddPage(panel, 'StockCulture No: %s'% new_stk_id, True)
    
    def onRecordPassage(self, event):
        meta = ExperimentSettings.getInstance()

	orgPassNum = meta.get_field(self.tag_stump+'|OrgPassageNo|%s'%self.instance, default = 0)
	
	passages = [attr for attr in meta.get_attribute_list_by_instance(self.tag_stump, self.instance)
		            if attr.startswith('Passage')]
	if passages:
	    lastpassage = sorted(passages, key = meta.stringSplitByNumbers)[-1]
	    self.currpassageNo = int(lastpassage.split('Passage')[1])+1
	else:
	    self.currpassageNo = int(orgPassNum)+1
	
	# Show the passage dialog
        dia = PassageStepBuilder(self, self.protocol, self.currpassageNo)
        if dia.ShowModal() == wx.ID_OK: 
	    meta.set_field(self.tag_stump+'|Passage%s|%s' %(self.currpassageNo, self.instance), dia.curr_protocol.items())	# set the value as a list rather than a dictionary
	    self.showPassages()
        dia.Destroy()	

    def showPassages(self):
	'''This method writes the updated passage history in a sequence fashion'''
	meta = ExperimentSettings.getInstance()
	
	passages = [attr for attr in meta.get_attribute_list_by_instance(self.tag_stump, self.instance)
		                    if attr.startswith('Passage')]
	if passages:
	    
	    self.fpbsizer.Clear(deleteWindows=True)
	    self.settings_controls[self.tag_stump+'|OrgPassageNo|%s'%self.instance].Disable()
	    
	    for passage in sorted(passages, reverse=True):
		# make a foldable panel for each passage
		admin_info = self.getAdminInfo(passage)
		passagepane = wx.CollapsiblePane(self.bot_panel, label=passage+': '+admin_info, style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
		self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, passagepane)
		self.passagePane(passagepane.GetPane(), passage)	
		self.fpbsizer.Add(passagepane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)	
    

	    # Sizers update
	    self.bot_panel.SetSizer(self.fpbsizer)
	    self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	

    def OnPaneChanged(self, evt=None):
	    self.bot_panel.Layout()
	
    def passagePane(self, pane, passage):
	''' This pane makes the microscope stand (backbone of the microscope)'''	
	
	meta = ExperimentSettings.getInstance()
	self.pane = pane
	
	passage_info = meta.get_field(self.tag_stump+'|%s|%s' %(passage, self.instance))
	curr_protocol = dict(passage_info)
	
	steps = sorted([step for step in curr_protocol.keys()
		 if not step.startswith('ADMIN')] , key = meta.stringSplitByNumbers)
	
	string = ''
	for s in steps:
	    step_info = curr_protocol.get(s)
	    string += s+': %s ' %step_info[0]
	    if len(step_info[1])> 0:
		string += 'for %s mins ' %step_info[1]
	    if len(step_info[2])> 0:
		string += 'at %s C ' %step_info[2]	  
	    if len(step_info[3])> 0:
		string += 'Tips: %s' %step_info[3]		    
	    string += '\n'
	    
	wx.StaticText(self.pane, -1, string) 
	
 
    def validate(self):
        pass
    
    def getAdminInfo(self, passage):
	meta = ExperimentSettings.getInstance()
	passage_info = meta.get_field(self.tag_stump+'|%s|%s' %(passage, self.instance))
	admin_info = dict(passage_info).get('ADMIN')
	
	return 'Operator %s Date %s Split 1:%s Cell Count %s' %(admin_info[0], admin_info[1], admin_info[2], admin_info[3])
  
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
	
########################################################################        
################## MICROSCOPE SETTING PANEL         ####################
########################################################################
class MicroscopeSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Instrument|Microscope'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = MicroscopePanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = MicroscopePanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = MicroscopePanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 
    


class MicroscopePanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY )

	self.page_counter = page_counter
	self.sw = wx.ScrolledWindow(self)
	self.protocol = 'Instrument|Microscope|%s'%str(self.page_counter)

	headfgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
	#  Protocol Name
	chnameTAG = 'Instrument|Microscope|ChannelName|'+str(self.page_counter)
	self.settings_controls[chnameTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chnameTAG, default=''))
	self.settings_controls[chnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[chnameTAG].SetInitialSize((250,20))
	self.settings_controls[chnameTAG].SetToolTipString('Type a unique name for the channel')
	self.save_btn = wx.Button(self.sw, -1, "Save Channel Settings")
	self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingChannel)
	headfgs.Add(wx.StaticText(self.sw, -1, 'Channel Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL) 
	headfgs.Add(self.settings_controls[chnameTAG], 0, wx.EXPAND)
	headfgs.Add(self.save_btn, 0, wx.EXPAND)
	
	# Progress bar
	self.gauge = wx.Gauge(self.sw, -1, 100, size=(250, 20), style=wx.GA_SMOOTH)
	headfgs.Add(wx.StaticText(self.sw, -1, 'Data filled so far'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL) 
	headfgs.Add(self.gauge, 0)
	self.progpercent = wx.StaticText(self.sw, -1, '')
	headfgs.Add(self.progpercent, 0)

	#-- COLLAPSIBLE PANES ---#
	self.strucpane= wx.CollapsiblePane(self.sw, label="Hardware", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
	self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self.strucpane)
	self.hardwarePane(self.strucpane.GetPane())
	self.strucpane.Disable()
	
        self.illumpane = wx.CollapsiblePane(self.sw, label="Optics", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self.illumpane)
        self.opticsPane(self.illumpane.GetPane())

	#---  Sizers ---#
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(headfgs, 0, wx.ALL, 25)
	sizer.Add(self.strucpane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
        sizer.Add(self.illumpane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)

        self.sw.SetSizer(sizer)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)	
	
	self.updateProgressBar()

    def OnPaneChanged(self, evt=None):
        self.sw.Layout()
    
    def hardwarePane(self, pane):
	''' This pane makes the microscope stand (backbone of the microscope)'''	
	
	meta = ExperimentSettings.getInstance()
	self.pane = pane	
	
	#--- Core Comp ---#	
	staticbox = wx.StaticBox(self.pane, -1, "Stand")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	microstandTAG = 'Instrument|Microscope|Stand|%s'%str(self.page_counter)
	microstand = meta.get_field(microstandTAG, [])
	
	stand_choices=['Wide Field','Laser Scanning Microscopy', 'Laser Scanning Confocal', 'Spinning Disk Confocal', 'Slit Scan Confocal', 'Multi Photon Microscopy', 'Structured Illumination','Single Molecule Imaging', 'Total Internal Reflection', 'Fluorescence Lifetime', 'Spectral Imaging', 'Fluorescence Correlation Spectroscopy', 'Near FieldScanning Optical Microscopy', 'Second Harmonic Generation Imaging', 'Timelapse', 'Unknown', 'Other']
	self.settings_controls[microstandTAG+'|0']= wx.ListBox(self.pane, -1, wx.DefaultPosition, (150,30), stand_choices, wx.LB_SINGLE)
	if len(microstand) > 0:
	    self.settings_controls[microstandTAG+'|0'].Append(microstand[0])
	    self.settings_controls[microstandTAG+'|0'].SetStringSelection(microstand[0])
	self.settings_controls[microstandTAG+'|0'].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[microstandTAG+'|0'].SetToolTipString('Type of microscope e.g. Inverted, Confocal...') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|0'], 0, wx.EXPAND)	
	
	make_choices=['Zeiss','Olympus','Nikon', 'MDS','GE', 'Unknown', 'Other']
	self.settings_controls[microstandTAG+'|1']= wx.ListBox(self.pane, -1, wx.DefaultPosition, (150,30), make_choices, wx.LB_SINGLE)
	if len(microstand) > 1:
	    self.settings_controls[microstandTAG+'|1'].Append(microstand[1])
	    self.settings_controls[microstandTAG+'|1'].SetStringSelection(microstand[1])
	self.settings_controls[microstandTAG+'|1'].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[microstandTAG+'|1'].SetToolTipString('Manufacturer of microscope') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|1'], 0, wx.EXPAND)		
	
	self.settings_controls[microstandTAG+'|2']= wx.TextCtrl(self.pane, value='') 
	if len(microstand) > 2:
	    self.settings_controls[microstandTAG+'|2'].SetValue(microstand[2])
	self.settings_controls[microstandTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)   
	self.settings_controls[microstandTAG+'|2'].SetToolTipString('Model of the microscope') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|2'], 0, wx.EXPAND)
		
	self.settings_controls[microstandTAG+'|3']= wx.Choice(self.pane, -1, choices=['', 'Upright', 'Inverted'])
	if len(microstand) > 3:
	    self.settings_controls[microstandTAG+'|3'].SetStringSelection(microstand[3])
	self.settings_controls[microstandTAG+'|3'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[microstandTAG+'|3'].SetToolTipString('Orientation of the microscope in relation to the sample') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Orientation'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|3'], 0, wx.EXPAND)	
	
	self.settings_controls[microstandTAG+'|4']= wx.SpinCtrl(self.pane, -1, "", (30, 50))
	self.settings_controls[microstandTAG+'|4'].SetRange(0,20)
	if len(microstand) > 4:
	    self.settings_controls[microstandTAG+'|4'].SetValue(int(microstand[4]))
	self.settings_controls[microstandTAG+'|4'].Bind(wx.EVT_SPINCTRL, self.OnSavingData)	    
	self.settings_controls[microstandTAG+'|4'].SetToolTipString('Number of lamps used in the microscope') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Number of Lamps'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|4'], 0, wx.EXPAND) 	     
	
	self.settings_controls[microstandTAG+'|5']= wx.SpinCtrl(self.pane, -1, "", (30, 50))
	self.settings_controls[microstandTAG+'|5'].SetRange(0,20)
	if len(microstand) > 5:
	    self.settings_controls[microstandTAG+'|5'].SetValue(int(microstand[5]))
	self.settings_controls[microstandTAG+'|5'].Bind(wx.EVT_SPINCTRL, self.OnSavingData)	    
	self.settings_controls[microstandTAG+'|5'].SetToolTipString('Number of detectors used in the microscope') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Number of Detectors'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|5'], 0, wx.EXPAND)    	

	standSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	standSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	#-- Condensor --#
	staticbox = wx.StaticBox(self.pane, -1, "Condensor")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	condensorTAG = 'Instrument|Microscope|Condensor|'+str(self.page_counter)
	condensor = meta.get_field(condensorTAG, [])

	self.settings_controls[condensorTAG+'|0']= wx.Choice(self.pane, -1, choices=['','White Light', 'Fluorescence'])
	if len(condensor) > 0:
	    self.settings_controls[condensorTAG+'|0'].SetStringSelection(condensor[0])
	self.settings_controls[condensorTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[condensorTAG+'|0'].SetToolTipString('Type of condensor') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[condensorTAG+'|0'], 0, wx.EXPAND)

	self.settings_controls[condensorTAG+'|1'] = wx.TextCtrl(self.pane, value='') 
	if len(condensor)> 1:
	    self.settings_controls[condensorTAG+'|1'].SetValue(condensor[1])
	self.settings_controls[condensorTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[condensorTAG+'|1'].SetToolTipString('Manufacturer of condensor source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[condensorTAG+'|1'], 0, wx.EXPAND)
	
	self.settings_controls[condensorTAG+'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(condensor)> 2:
	    self.settings_controls[condensorTAG+'|2'].SetValue(condensor[2])
	self.settings_controls[condensorTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[condensorTAG+'|2'].SetToolTipString('Model of condensor source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[condensorTAG+'|2'], 0, wx.EXPAND)

	condensSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	condensSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	

	#-- Stage --#
	staticbox = wx.StaticBox(self.pane, -1, "Stage")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	stageTAG = 'Instrument|Microscope|Stage|'+str(self.page_counter)
	stage = meta.get_field(stageTAG, [])

	self.settings_controls[stageTAG+'|0']= wx.Choice(self.pane, -1, choices=['','Manual', 'Motorized'])
	if len(stage) > 0:
	    self.settings_controls[stageTAG+'|0'].SetStringSelection(stage[0])
	self.settings_controls[stageTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[stageTAG+'|0'].SetToolTipString('Type of stage') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[stageTAG+'|0'], 0, wx.EXPAND)

	self.settings_controls[stageTAG+'|1'] = wx.TextCtrl(self.pane, value='') 
	if len(stage)> 1:
	    self.settings_controls[stageTAG+'|1'].SetValue(stage[1])
	self.settings_controls[stageTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[stageTAG+'|1'].SetToolTipString('Manufacturer of stage source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[stageTAG+'|1'], 0, wx.EXPAND)
	
	self.settings_controls[stageTAG+'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(stage)> 2:
	    self.settings_controls[stageTAG+'|2'].SetValue(stage[2])
	self.settings_controls[stageTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[stageTAG+'|2'].SetToolTipString('Model of stage source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[stageTAG+'|2'], 0, wx.EXPAND)
	
	self.settings_controls[stageTAG+'|3']= wx.Choice(self.pane, -1, choices=['Yes', 'No'])
	if len(stage) > 3:
	    self.settings_controls[stageTAG+'|3'].SetStringSelection(stage[3])
	self.settings_controls[stageTAG+'|3'].Bind(wx.EVT_CHOICE, self.onEnabling)   
	self.settings_controls[stageTAG+'|3'].SetToolTipString('Holder for the samples') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Sample Holder'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[stageTAG+'|3'], 0, wx.EXPAND)	
	
	self.settings_controls[stageTAG+'|4'] = wx.TextCtrl(self.pane, value='') 	
	if len(stage)> 4:
	    self.settings_controls[stageTAG+'|4'].SetValue(stage[4])
	self.settings_controls[stageTAG+'|4'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[stageTAG+'|4'].SetToolTipString('Sample holder code')
	self.settings_controls[stageTAG+'|4'].Disable()
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Holder Code'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[stageTAG+'|4'], 0, wx.EXPAND)	

	stageSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	stageSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	#-- Incubator --#
	staticbox = wx.StaticBox(self.pane, -1, "Incubator")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	incbatorTAG = 'Instrument|Microscope|Incubator|'+str(self.page_counter)
	incubator = meta.get_field(incbatorTAG, [])

	self.settings_controls[incbatorTAG+'|0'] = wx.TextCtrl(self.pane, value='') 
	if len(incubator)> 0:
	    self.settings_controls[incbatorTAG+'|0'].SetValue(incubator[0])
	self.settings_controls[incbatorTAG+'|0'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbatorTAG+'|0'].SetToolTipString('Manufacturer of incubator source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[incbatorTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[incbatorTAG+'|1'] = wx.TextCtrl(self.pane, value='') 	
	if len(incubator)> 1:
	    self.settings_controls[incbatorTAG+'|1'].SetValue(incubator[1])
	self.settings_controls[incbatorTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbatorTAG+'|1'].SetToolTipString('Model of incubator source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[incbatorTAG+'|1'], 0, wx.EXPAND)
	
	self.settings_controls[incbatorTAG+'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(incubator)> 2:
	    self.settings_controls[incbatorTAG+'|2'].SetValue(incubator[2])
	self.settings_controls[incbatorTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbatorTAG+'|2'].SetToolTipString('Incubation temperature')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Temperature(C)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[incbatorTAG+'|2'], 0, wx.EXPAND)
	
	self.settings_controls[incbatorTAG+'|3'] = wx.TextCtrl(self.pane, value='') 	
	if len(incubator)> 3:
	    self.settings_controls[incbatorTAG+'|3'].SetValue(incubator[3])
	self.settings_controls[incbatorTAG+'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbatorTAG+'|3'].SetToolTipString('Percentages of Carbondioxide')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'CO2%'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[incbatorTAG+'|3'], 0, wx.EXPAND)	

	self.settings_controls[incbatorTAG+'|4'] = wx.TextCtrl(self.pane, value='') 	
	if len(incubator)> 4:
	    self.settings_controls[incbatorTAG+'|4'].SetValue(incubator[4])
	self.settings_controls[incbatorTAG+'|4'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbatorTAG+'|4'].SetToolTipString('Humidity within the incubator')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Humidity'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[incbatorTAG+'|4'], 0, wx.EXPAND)	
	
	self.settings_controls[incbatorTAG+'|5'] = wx.TextCtrl(self.pane, value='') 	
	if len(incubator)> 5:
	    self.settings_controls[incbatorTAG+'|5'].SetValue(incubator[5])
	self.settings_controls[incbatorTAG+'|5'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbatorTAG+'|5'].SetToolTipString('Pressure within the incubator')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Pressure'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[incbatorTAG+'|5'], 0, wx.EXPAND)	

	incubatorSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	incubatorSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	#--- Layout ---#
	fgs = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
	fgs.Add(standSizer)
	fgs.Add(condensSizer)
	fgs.Add(stageSizer)
	fgs.Add(incubatorSizer)

	self.pane.SetSizer(fgs)

    def opticsPane(self, pane):
	''' This pane makes the Illumination pane of the microscope. Each component of the illum pane can have mulitple components
	which can again has multiple attributes'''
	
	meta = ExperimentSettings.getInstance()
	self.pane = pane
	
	self.exTsld = 300
	self.exBsld = 800	
	
	#-- Light Source --#
	staticbox = wx.StaticBox(self.pane, -1, "Light")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	lightsrcTAG = 'Instrument|Microscope|LightSource|'+str(self.page_counter)
	lightsrc = meta.get_field(lightsrcTAG, [])
	
	self.settings_controls[lightsrcTAG+'|0']=  wx.Choice(self.pane, -1,  choices=['Transmitted','Epifluorescence','Oblique','Non Linear'])
	if len(lightsrc)> 0:
	    self.settings_controls[lightsrcTAG+'|0'].SetStringSelection(lightsrc[0])
	self.settings_controls[lightsrcTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData) 
	self.settings_controls[lightsrcTAG+'|0'].SetToolTipString('Type of the light source') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|1']= wx.Choice(self.pane, -1, choices=['Laser', 'Filament', 'Arc', 'Light Emitting Diode'])
	if len(lightsrc) > 1:
	    self.settings_controls[lightsrcTAG+'|1'].SetStringSelection(lightsrc[1])
	self.settings_controls[lightsrcTAG+'|1'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[lightsrcTAG+'|1'].SetToolTipString('Type of the light source') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Source'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|1'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|2'] = wx.TextCtrl(self.pane, value='') 
	if len(lightsrc)> 2:
	    self.settings_controls[lightsrcTAG+'|2'].SetValue(lightsrc[2])
	self.settings_controls[lightsrcTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lightsrcTAG+'|2'].SetToolTipString('Manufacturer of light source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|2'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|3'] = wx.TextCtrl(self.pane, value='') 	
	if len(lightsrc)> 3:
	    self.settings_controls[lightsrcTAG+'|3'].SetValue(lightsrc[3])
	self.settings_controls[lightsrcTAG+'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lightsrcTAG+'|3'].SetToolTipString('Model of light source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|3'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|4'] = wx.TextCtrl(self.pane, value='') 	
	if len(lightsrc)> 4:
	    self.settings_controls[lightsrcTAG+'|4'].SetValue(lightsrc[4])
	self.settings_controls[lightsrcTAG+'|4'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lightsrcTAG+'|4'].SetToolTipString('Power of light source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Measured Power (User)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|4'], 0, wx.EXPAND)	
	
	self.settings_controls[lightsrcTAG+'|5'] = wx.TextCtrl(self.pane, value='') 	
	if len(lightsrc)> 5:
	    self.settings_controls[lightsrcTAG+'|5'].SetValue(lightsrc[5])
	self.settings_controls[lightsrcTAG+'|5'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lightsrcTAG+'|5'].SetToolTipString('Measured power of light source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Measured Power (Instrument)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|5'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|6']= wx.Choice(self.pane, -1, choices=['Yes', 'No'])
	if len(lightsrc) > 6:
	    self.settings_controls[lightsrcTAG+'|6'].SetStringSelection(lightsrc[6])
	self.settings_controls[lightsrcTAG+'|6'].Bind(wx.EVT_CHOICE, self.onEnabling)
	self.settings_controls[lightsrcTAG+'|6'].SetToolTipString('Shutter used') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Shutter Used'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|6'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|7']= wx.Choice(self.pane, -1, choices=['Internal', 'External'])
	if len(lightsrc) > 7:
	    self.settings_controls[lightsrcTAG+'|7'].SetStringSelection(lightsrc[7])
	self.settings_controls[lightsrcTAG+'|7'].Bind(wx.EVT_CHOICE, self.onEnabling)
	self.settings_controls[lightsrcTAG+'|7'].SetToolTipString('Shutter used') 
	self.settings_controls[lightsrcTAG+'|7'].Disable()
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Shutter Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|7'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|8'] = wx.TextCtrl(self.pane, value='') 
	if len(lightsrc)> 8:
	    self.settings_controls[lightsrcTAG+'|8'].SetValue(lightsrc[8])
	self.settings_controls[lightsrcTAG+'|8'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lightsrcTAG+'|8'].SetToolTipString('Manufacturer of light source')
	self.settings_controls[lightsrcTAG+'|8'].Disable()
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Ext Shutter Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|8'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|9'] = wx.TextCtrl(self.pane, value='') 	
	if len(lightsrc)> 9:
	    self.settings_controls[lightsrcTAG+'|9'].SetValue(lightsrc[9])
	self.settings_controls[lightsrcTAG+'|9'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lightsrcTAG+'|9'].SetToolTipString('Model of light source')
	self.settings_controls[lightsrcTAG+'|9'].Disable()
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Ext Shutter Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|9'], 0, wx.EXPAND)	
	
	lightSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	lightSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)
	
	#-- Excitation Filter --#
	staticbox = wx.StaticBox(self.pane, -1, " Excitation Filter")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	extfltTAG = 'Instrument|Microscope|ExtFilter|'+str(self.page_counter)
	extfilter = meta.get_field(extfltTAG, [])
	
	self.startNM, self.endNM = 300, 800
	if len(extfilter)> 1:
	    self.startNM = int(extfilter[0])
	    self.endNM = int(extfilter[1])

	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Wavelength\n(nm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

	self.exTsld = self.settings_controls[extfltTAG +'|0'] = wx.Slider(self.pane, -1, self.startNM, 300, 800, wx.DefaultPosition, (100, -1), wx.SL_LABELS)
	self.exBsld = self.settings_controls[extfltTAG +'|1'] = wx.Slider(self.pane, -1, self.endNM, 300, 800, wx.DefaultPosition, (100, -1), style = wx.SL_LABELS|wx.SL_TOP)
	
	self.fltrspectrum = FilterSpectrum(self.pane)

	self.pane.Bind(wx.EVT_SLIDER, self.OnSavingData)
	
	spctrmSizer = wx.BoxSizer(wx.VERTICAL)
	spctrmSizer.Add(self.settings_controls[extfltTAG +'|0'],0)
	spctrmSizer.Add(self.fltrspectrum, 0)
	spctrmSizer.Add(self.settings_controls[extfltTAG +'|1'],0)   
	
	multctrlSizer.Add(spctrmSizer, 0)
	
	self.settings_controls[extfltTAG +'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(extfilter)> 2:
	    self.settings_controls[extfltTAG +'|2'].SetValue(extfilter[2])
	self.settings_controls[extfltTAG +'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[extfltTAG +'|2'].SetToolTipString('Make of filter')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[extfltTAG +'|2'], 0, wx.EXPAND)	
	
	self.settings_controls[extfltTAG +'|3'] = wx.TextCtrl(self.pane, value='') 	
	if len(extfilter)> 3:
	    self.settings_controls[extfltTAG +'|3'].SetValue(extfilter[3])
	self.settings_controls[extfltTAG +'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[extfltTAG +'|3'].SetToolTipString('Model of filter')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[extfltTAG +'|3'], 0, wx.EXPAND)
	
	extfilterSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	extfilterSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	#-- Dichroic Mirror --#
	staticbox = wx.StaticBox(self.pane, -1, "Dichroic Mirror")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	mirrorTAG = 'Instrument|Microscope|Mirror|'+str(self.page_counter)
	mirror = meta.get_field(mirrorTAG, [])
	self.startNM, self.endNM = 300, 800
	if len(mirror)> 1:
	    self.startNM = int(mirror[0])
	    self.endNM = int(mirror[1])

	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Wavelength\n(nm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

	self.settings_controls[mirrorTAG +'|0'] = wx.Slider(self.pane, -1, self.startNM, 300, 800, wx.DefaultPosition, (100, -1), wx.SL_LABELS)
	self.settings_controls[mirrorTAG +'|1'] = wx.Slider(self.pane, -1, self.endNM, 300, 800, wx.DefaultPosition, (100, -1), style = wx.SL_LABELS|wx.SL_TOP)
	
	self.pane.fltTsld = self.settings_controls[mirrorTAG +'|0']
	self.pane.fltBsld = self.settings_controls[mirrorTAG +'|1']
	
	self.fltrspectrum = FilterSpectrum(self.pane)

	self.pane.Bind(wx.EVT_SLIDER, self.OnSavingData)
	
	spctrmSizer = wx.BoxSizer(wx.VERTICAL)
	spctrmSizer.Add(self.pane.fltTsld,0)
	spctrmSizer.Add(self.fltrspectrum, 0)
	spctrmSizer.Add(self.pane.fltBsld,0)   
	
	multctrlSizer.Add(spctrmSizer, 0)
	
	self.settings_controls[mirrorTAG+'|2']= wx.Choice(self.pane, -1, choices=['Transmitted', 'Reflected'])
	if len(lightsrc) > 2:
	    self.settings_controls[mirrorTAG+'|2'].SetStringSelection(lightsrc[2])
	self.settings_controls[mirrorTAG+'|2'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[mirrorTAG+'|2'].SetToolTipString('Mirror mode') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Mode'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[mirrorTAG+'|2'], 0, wx.EXPAND)	
	
	self.settings_controls[mirrorTAG +'|3'] = wx.TextCtrl(self.pane, value='') 	
	if len(mirror)> 3:
	    self.settings_controls[mirrorTAG +'|3'].SetValue(mirror[3])
	self.settings_controls[mirrorTAG +'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[mirrorTAG +'|3'].SetToolTipString('Make of mirror')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[mirrorTAG +'|3'], 0, wx.EXPAND)	
	
	self.settings_controls[mirrorTAG +'|4'] = wx.TextCtrl(self.pane, value='') 	
	if len(mirror)> 4:
	    self.settings_controls[mirrorTAG +'|4'].SetValue(mirror[4])
	self.settings_controls[mirrorTAG +'|4'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[mirrorTAG +'|4'].SetToolTipString('Model of mirror')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[mirrorTAG +'|4'], 0, wx.EXPAND)
	
	self.settings_controls[mirrorTAG+'|5']= wx.Choice(self.pane, -1, choices=['Yes', 'No'])
	if len(lightsrc) > 5:
	    self.settings_controls[mirrorTAG+'|5'].SetStringSelection(lightsrc[5])
	self.settings_controls[mirrorTAG+'|5'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[mirrorTAG+'|5'].SetToolTipString('Modification done') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Modification'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[mirrorTAG+'|5'], 0, wx.EXPAND)		
	
	mirrorSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	mirrorSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	
	#-- Emission Filter --#
	staticbox = wx.StaticBox(self.pane, -1, " Emission Filter")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	emsfltTAG = 'Instrument|Microscope|EmsFilter|'+str(self.page_counter)
	emsfilter = meta.get_field(emsfltTAG, [])
	self.startNM, self.endNM = 300, 800
	if len(emsfilter)> 1:
	    self.startNM = int(emsfilter[0])
	    self.endNM = int(emsfilter[1])

	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Wavelength\n(nm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

	self.settings_controls[emsfltTAG +'|0'] = wx.Slider(self.pane, -1, self.startNM, 300, 800, wx.DefaultPosition, (100, -1), wx.SL_LABELS)
	self.settings_controls[emsfltTAG +'|1'] = wx.Slider(self.pane, -1, self.endNM, 300, 800, wx.DefaultPosition, (100, -1), style = wx.SL_LABELS|wx.SL_TOP)
	
	self.pane.fltTsld = self.settings_controls[emsfltTAG +'|0']
	self.pane.fltBsld = self.settings_controls[emsfltTAG +'|1']
	
	self.fltrspectrum = FilterSpectrum(self.pane)

	self.pane.Bind(wx.EVT_SLIDER, self.OnSavingData)
	
	spctrmSizer = wx.BoxSizer(wx.VERTICAL)
	spctrmSizer.Add(self.pane.fltTsld,0)
	spctrmSizer.Add(self.fltrspectrum, 0)
	spctrmSizer.Add(self.pane.fltBsld,0)   
	
	multctrlSizer.Add(spctrmSizer, 0)
	
	self.settings_controls[emsfltTAG +'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(emsfilter)> 2:
	    self.settings_controls[emsfltTAG +'|2'].SetValue(emsfilter[2])
	self.settings_controls[emsfltTAG +'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[emsfltTAG +'|2'].SetToolTipString('Make of filter')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[emsfltTAG +'|2'], 0, wx.EXPAND)	
	
	self.settings_controls[emsfltTAG +'|3'] = wx.TextCtrl(self.pane, value='') 	
	if len(emsfilter)> 3:
	    self.settings_controls[emsfltTAG +'|3'].SetValue(emsfilter[3])
	self.settings_controls[emsfltTAG +'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[emsfltTAG +'|3'].SetToolTipString('Model of filter')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[emsfltTAG +'|3'], 0, wx.EXPAND)
	
	emsfilterSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	emsfilterSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)
	
	
	#-- Lens --#
	staticbox = wx.StaticBox(self.pane, -1, "Lens")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	lensTAG = 'Instrument|Microscope|Lens|'+str(self.page_counter)
	lens = meta.get_field(lensTAG, [])
	
	self.settings_controls[lensTAG+'|0'] = wx.TextCtrl(self.pane, value='') 
	if len(lens)> 0:
	    self.settings_controls[lensTAG+'|0'].SetValue(lens[0])
	self.settings_controls[lensTAG+'|0'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lensTAG+'|0'].SetToolTipString('Manufacturer of lens')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[lensTAG+'|1'] = wx.TextCtrl(self.pane, value='') 	
	if len(lens)> 1:
	    self.settings_controls[lensTAG+'|1'].SetValue(lens[1])
	self.settings_controls[lensTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lensTAG+'|1'].SetToolTipString('Model of lens')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|1'], 0, wx.EXPAND)
	
	self.settings_controls[lensTAG+'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(lens)> 2:
	    self.settings_controls[lensTAG+'|2'].SetValue(lens[2])
	self.settings_controls[lensTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lensTAG+'|2'].SetToolTipString('Objective Magnification')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Objective Magnification'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|2'], 0, wx.EXPAND)
	
	self.settings_controls[lensTAG+'|3'] = wx.TextCtrl(self.pane, value='') 	
	if len(lens)> 3:
	    self.settings_controls[lensTAG+'|3'].SetValue(lens[3])
	self.settings_controls[lensTAG+'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lensTAG+'|3'].SetToolTipString('nominal aperture')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Objective NA'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|3'], 0, wx.EXPAND)	
	
	self.settings_controls[lensTAG+'|4'] = wx.TextCtrl(self.pane, value='') 	
	if len(lens)> 4:
	    self.settings_controls[lensTAG+'|4'].SetValue(lens[4])
	self.settings_controls[lensTAG+'|4'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lensTAG+'|4'].SetToolTipString('Calibrated Magnification')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Calibrated Magnification'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|4'], 0, wx.EXPAND)	
	
	immersion_choices=['Oil', 'Water', 'Water Dipping', 'Air', 'Multi', 'Glycerol', 'Unknown','Other']
	self.settings_controls[lensTAG+'|5']= wx.ListBox(self.pane, -1, wx.DefaultPosition, (50,30), immersion_choices, wx.LB_SINGLE)
	if len(lens) > 5:
	    self.settings_controls[lensTAG+'|5'].Append(lens[5])
	    self.settings_controls[lensTAG+'|5'].SetStringSelection(lens[5])
	self.settings_controls[lensTAG+'|5'].Bind(wx.EVT_LISTBOX, self.OnSavingData)
	self.settings_controls[lensTAG+'|5'].SetToolTipString('Immersion') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Immersion'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|5'], 0, wx.EXPAND)
	
	self.settings_controls[lensTAG+'|6']= wx.Choice(self.pane, -1, choices=['Yes', 'No'])
	if len(lens) > 6:
	    self.settings_controls[lensTAG+'|6'].SetStringSelection(lens[6])
	self.settings_controls[lensTAG+'|6'].Bind(wx.EVT_CHOICE, self.onEnabling)
	self.settings_controls[lensTAG+'|6'].SetToolTipString('Correction Collar') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Correction Collar'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|6'], 0, wx.EXPAND)
	
	self.settings_controls[lensTAG+'|7']= wx.TextCtrl(self.pane, value='')
	if len(lens) > 7:
	    self.settings_controls[lensTAG+'|7'].SetValue(lens[7])
	self.settings_controls[lensTAG+'|7'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[lensTAG+'|7'].SetToolTipString('Correction value') 
	self.settings_controls[lensTAG+'|7'].Disable()
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Correction Value'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|7'], 0, wx.EXPAND) 	
	
	self.settings_controls[lensTAG+'|8']= wx.Choice(self.pane, -1, choices=['UV', 'PlanApo', 'PlanFluor', 'SuperFluor', 'VioletCorrected', 'Unknown'])
	if len(lens) > 8:
	    self.settings_controls[lensTAG+'|8'].SetStringSelection(lens[8])
	self.settings_controls[lensTAG+'|8'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[lensTAG+'|8'].SetToolTipString('Correction type') 
	self.settings_controls[lensTAG+'|8'].Disable()
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Correction Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lensTAG+'|8'], 0, wx.EXPAND)	
		
	lensSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	lensSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	
	#-- Detector --#
	staticbox = wx.StaticBox(self.pane, -1, "Detector")
	multctrlSizer = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

	detectorTAG = 'Instrument|Microscope|Detector|'+str(self.page_counter)
	detector = meta.get_field(detectorTAG, [])
	
	detector_choices =['CCD', 'Intensified-CCD', 'Analog-Video', 'Spectroscopy', 'Life-time-imaging', 'Correlation-Spectroscopy', 'FTIR', 'EM-CCD', 'APD', 'CMOS', 'Unknown', 'Other']
	self.settings_controls[detectorTAG+'|0']= wx.ListBox(self.pane, -1, wx.DefaultPosition, (120,30), detector_choices, wx.LB_SINGLE)
	if len(detector) > 0:
	    self.settings_controls[detectorTAG+'|0'].Append(detector[0])
	    self.settings_controls[detectorTAG+'|0'].SetStringSelection(detector[0])
	self.settings_controls[detectorTAG+'|0'].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[detectorTAG+'|0'].SetToolTipString('Type of detector') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|0'], 0, wx.EXPAND)
	multctrlSizer.Add(wx.StaticText(self.pane, -1, ''), 0)
	
	self.settings_controls[detectorTAG+'|1'] = wx.TextCtrl(self.pane, value='') 
	if len(detector)> 1:
	    self.settings_controls[detectorTAG+'|1'].SetValue(detector[1])
	self.settings_controls[detectorTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[detectorTAG+'|1'].SetToolTipString('Manufacturer of detector')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Make'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|1'], 0, wx.EXPAND)
	multctrlSizer.Add(wx.StaticText(self.pane, -1, ''), 0)
	
	self.settings_controls[detectorTAG+'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(detector)> 2:
	    self.settings_controls[detectorTAG+'|2'].SetValue(detector[2])
	self.settings_controls[detectorTAG+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[detectorTAG+'|2'].SetToolTipString('Model of light source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|2'], 0, wx.EXPAND)
	multctrlSizer.Add(wx.StaticText(self.pane, -1, ''), 0)
	
	self.settings_controls[detectorTAG+'|3']= wx.Choice(self.pane, -1, choices=['1','2','4','8','16'])
	if len(detector) > 3:
	    self.settings_controls[detectorTAG+'|3'].SetStringSelection(detector[3])
	self.settings_controls[detectorTAG+'|3'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[detectorTAG+'|3'].SetToolTipString('Binning') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Binning'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|3'], 0, wx.EXPAND)
	multctrlSizer.Add(wx.StaticText(self.pane, -1, ''), 0)
		
	self.settings_controls[detectorTAG+'|4'] = wx.TextCtrl(self.pane, value='') 	
	if len(detector)> 4:
	    self.settings_controls[detectorTAG+'|4'].SetValue(detector[4])
	self.settings_controls[detectorTAG+'|4'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[detectorTAG+'|4'].SetToolTipString('Exposure Time')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Exposure Time'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|4'], 0, wx.EXPAND)
	
	self.settings_controls[detectorTAG+'|5']= wx.Choice(self.pane, -1, choices=['microsecond','millisecond','second','minute'])
	if len(detector) > 5:
	    self.settings_controls[detectorTAG+'|5'].SetStringSelection(detector[5])
	self.settings_controls[detectorTAG+'|5'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[detectorTAG+'|5'].SetToolTipString('unit for exposure time') 
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|5'], 0, wx.EXPAND)
	
	self.settings_controls[detectorTAG+'|6'] = wx.TextCtrl(self.pane, value='') 	
	if len(detector)> 6:
	    self.settings_controls[detectorTAG+'|6'].SetValue(detector[6])
	self.settings_controls[detectorTAG+'|6'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[detectorTAG+'|6'].SetToolTipString('Gain in volts')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Gain'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|6'], 0, wx.EXPAND)
	
	self.settings_controls[detectorTAG+'|7']= wx.Choice(self.pane, -1, choices=['microvolt','millivolt','volt'])
	if len(detector) > 7:
	    self.settings_controls[detectorTAG+'|7'].SetStringSelection(detector[7])
	self.settings_controls[detectorTAG+'|7'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[detectorTAG+'|7'].SetToolTipString('unit') 
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|7'], 0, wx.EXPAND)	
	
	self.settings_controls[detectorTAG+'|8'] = wx.TextCtrl(self.pane, value='') 	
	if len(detector)> 8:
	    self.settings_controls[detectorTAG+'|8'].SetValue(detector[8])
	self.settings_controls[detectorTAG+'|8'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[detectorTAG+'|8'].SetToolTipString('Offset in volts')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Offset'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|8'], 0, wx.EXPAND)
	
	self.settings_controls[detectorTAG+'|9']= wx.Choice(self.pane, -1, choices=['microvolt','millivolt','volt'])
	if len(detector) > 9:
	    self.settings_controls[detectorTAG+'|9'].SetStringSelection(detector[9])
	self.settings_controls[detectorTAG+'|9'].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[detectorTAG+'|9'].SetToolTipString('unit') 
	multctrlSizer.Add(self.settings_controls[detectorTAG+'|9'], 0, wx.EXPAND)	
	
	
	detectorSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	detectorSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	# --- Layout and Sizers ---#
	top_fgs = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
	bot_fgs = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
	
	top_fgs.Add(lightSizer)
	top_fgs.Add(extfilterSizer)
	top_fgs.Add(mirrorSizer)
	top_fgs.Add(emsfilterSizer)
	bot_fgs.Add(lensSizer)
	bot_fgs.Add(detectorSizer)
	
	fgs = wx.FlexGridSizer(rows=2, hgap=5, vgap=5)
	fgs.Add(top_fgs)
	fgs.Add(bot_fgs)
	
	self.pane.SetSizer(fgs)


    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)   	
	self.updateProgressBar()
	
    def onEnabling(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]	

	if self.settings_controls['Instrument|Microscope|LightSource|%s|%s'%(str(self.page_counter), '6')].GetStringSelection() == 'Yes':
	    self.settings_controls['Instrument|Microscope|LightSource|%s|%s'%(str(self.page_counter), '7')].Enable()
	if self.settings_controls['Instrument|Microscope|LightSource|%s|%s'%(str(self.page_counter), '7')].GetStringSelection() == 'External':
	    self.settings_controls['Instrument|Microscope|LightSource|%s|%s'%(str(self.page_counter), '8')].Enable()
	    self.settings_controls['Instrument|Microscope|LightSource|%s|%s'%(str(self.page_counter), '9')].Enable()
	if self.settings_controls['Instrument|Microscope|Lens|%s|%s'%(str(self.page_counter), '6')].GetStringSelection() == 'Yes':
	    self.settings_controls['Instrument|Microscope|Lens|%s|%s'%(str(self.page_counter), '7')].Enable()
	    self.settings_controls['Instrument|Microscope|Lens|%s|%s'%(str(self.page_counter), '8')].Enable()
	if self.settings_controls['Instrument|Microscope|Stage|%s|%s'%(str(self.page_counter), '3')].GetStringSelection() == 'Yes':
	    self.settings_controls['Instrument|Microscope|Stage|%s|%s'%(str(self.page_counter), '4')].Enable()	
	    
	meta.saveData(ctrl, tag, self.settings_controls)   
		
	self.updateProgressBar()	
    
    def updateProgressBar(self):
	filledCount = 0
	
	for tag, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice) or isinstance(ctrl, wx.ListBox):
		if ctrl.GetStringSelection():
		    filledCount += 1	    
	    elif isinstance(ctrl, wx.Slider):
		if tag.endswith('0') and ctrl.GetValue() > 300:
		    filledCount += 1
		if tag.endswith('1') and ctrl.GetValue() < 700:
		    filledCount += 1
	    else:
		if ctrl.GetValue():
		    filledCount += 1
		    
	progress = 100*(filledCount/float(len(self.settings_controls)))
	self.gauge.SetValue(int(progress))
	self.progpercent.SetLabel(str(int(progress))+' %')
	
    def onSavingChannel(self, event):
        # also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()   
		
	if not meta.get_field('Instrument|Microscope|ChannelName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please provide a channel name', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return
				
        filename = meta.get_field('Instrument|Microscope|ChannelName|%s'%str(self.page_counter))+'.txt'
        
        dlg = wx.FileDialog(None, message='Saving Channel Settings...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol) 


class FilterSpectrum(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,  size=(100, 30), style=wx.SUNKEN_BORDER)

        self.parent = parent
	self.meta = ExperimentSettings.getInstance()
	self.startNM = 300
	self.endNM = 800

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
	
	# get the component WL of the just previous one
	nmRange =  self.meta.partition(range(self.startNM, self.endNM+1), 5)
	
        #fltTsldVal = self.parent.exTsld.GetValue()
	#fltTsldMinVal = self.parent.exTsld.GetMin()
        #fltBsldVal = self.parent.exBsld.GetValue()
	#fltBsldMaxVal = self.parent.exBsld.GetMax()
	
	#fltTsldMove = (fltTsldVal-fltTsldMinVal)*100/(fltBsldMaxVal-fltTsldMinVal)  # 100 pxl is the physical size of the spectra panel
	#fltBsldMove = (fltBsldVal-fltTsldMinVal)*100/(fltBsldMaxVal-fltTsldMinVal)
	        
        # Draw the specturm according to the spectral range
        dc.GradientFillLinear((0, 0, 20, 30), self.meta.nmToRGB(nmRange[0]), self.meta.nmToRGB(nmRange[1]), wx.EAST)
        dc.GradientFillLinear((20, 0, 20, 30), self.meta.nmToRGB(nmRange[1]), self.meta.nmToRGB(nmRange[2]), wx.EAST)
        dc.GradientFillLinear((40, 0, 20, 30), self.meta.nmToRGB(nmRange[2]), self.meta.nmToRGB(nmRange[3]), wx.EAST)
        dc.GradientFillLinear((60, 0, 20, 30), self.meta.nmToRGB(nmRange[3]), self.meta.nmToRGB(nmRange[4]), wx.EAST)
        dc.GradientFillLinear((80, 0, 20, 30), self.meta.nmToRGB(nmRange[4]), self.meta.nmToRGB(nmRange[5]), wx.EAST)
        
        # Draw the slider on the spectrum to depict the selected range within the specta
	#dc = wx.PaintDC(self)
	#dc.SetPen(wx.Pen(self.GetBackgroundColour()))
	#dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
	#dc.DrawRectangle(0, 0, fltTsldMove, 30)
	#dc.DrawRectangle(fltBsldMove, 0, 100, 30) 

       
    def OnSize(self, event):
        self.Refresh()	

########################################################################        
################## FLOW CYTOMETER SETTING PANEL         ####################
########################################################################
class FlowcytometerSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Instrument|Flowcytometer'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = FlowcytometerPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = FlowcytometerPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = FlowcytometerPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 
   

class FlowcytometerPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
	
	self.protocol = 'Instrument|Flowcytometer'
 
        self.page_counter = page_counter
	
	self.top_panel = wx.Panel(self)
	self.bot_panel = wx.ScrolledWindow(self)	
  
	self.top_fgs = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
	self.bot_fgs = wx.FlexGridSizer(cols=30, hgap=5, vgap=5)
	
	#-- Show previously encoded channels --#
	
	#----------- Microscope Labels and Text Controler-------#
	self.saveSettings = wx.Button(self.top_panel, -1, 'Save Settings')
	self.saveSettings.Bind(wx.EVT_BUTTON, self.onSavingSettings)
	self.top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	self.top_fgs.Add(self.saveSettings, 0)		
	#--Manufacture--#
	flowmfgTAG = 'Instrument|Flowcytometer|Manufacter|'+str(self.page_counter)
	self.settings_controls[flowmfgTAG] = wx.Choice(self.top_panel, -1,  choices=['Beckman','BD-Biosciences'])
	if meta.get_field(flowmfgTAG) is not None:
	    self.settings_controls[flowmfgTAG].SetStringSelection(meta.get_field(flowmfgTAG))
	self.settings_controls[flowmfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[flowmfgTAG].SetToolTipString('Manufacturer name')
	self.top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Manufacturer'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	self.top_fgs.Add(self.settings_controls[flowmfgTAG], 0, wx.EXPAND)
	#--Model--#
	flowmdlTAG = 'Instrument|Flowcytometer|Model|'+str(self.page_counter)
	self.settings_controls[flowmdlTAG] = wx.TextCtrl(self.top_panel,  value=meta.get_field(flowmdlTAG, default=''))
	self.settings_controls[flowmdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[flowmdlTAG].SetToolTipString('Model number of the Flowcytometer')
	self.top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	self.top_fgs.Add(self.settings_controls[flowmdlTAG], 0, wx.EXPAND)
	#---Add Channel--#	
	self.addCh = wx.Button(self.top_panel, 1, '+ Add Channel')
	self.addCh.Bind(wx.EVT_BUTTON, self.onAddChnnel) 
	self.top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	self.top_fgs.Add(self.addCh, 0)

	#-- Show previously encoded channels in case of loading ch settings--#	
	self.showChannels()
        
        #-- Sizers --#
	self.top_panel.SetSizer(self.top_fgs)
	self.bot_panel.SetSizer(self.bot_fgs)
        self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)	          

    def onAddChnnel(self, event):
	meta = ExperimentSettings.getInstance() 
	self.dlg = ChannelBuilder(self.bot_panel, -1, 'Channel Builder')
	
        if self.dlg.ShowModal() == wx.ID_OK:
	    lightpath = []
	    for comp in self.dlg.componentList:
		lightpath.append(self.dlg.componentList[comp])
	    chName = self.dlg.select_chName.GetStringSelection()
	    tag = 'Instrument|Flowcytometer|%s|%s' %(chName, str(self.page_counter))
	    value = lightpath
	    self.drawChannel(chName, value)
	    meta.set_field(tag, value)
    
    def showChannels(self):
	meta = ExperimentSettings.getInstance()	
			    
	#-- Show previously encoded channels --#
	chs = [tag.split('|')[2] for tag in meta.get_field_tags('Instrument|Flowcytometer', str(self.page_counter))
                           if not tag.startswith('Instrument|Flowcytometer|Manufacter') 
	                   if not tag.startswith('Instrument|Flowcytometer|Model')]
	if chs:
	    for ch in sorted(chs):
		self.drawChannel(ch, meta.get_field(('Instrument|Flowcytometer|%s|%s') %(ch, str(self.page_counter))))
	    
    
    def drawChannel(self, chName, lightpath):
	meta = ExperimentSettings.getInstance()
	# Add the channel name
	self.bot_fgs.Add(wx.StaticText(self.bot_panel, -1, chName), 0)
	
	# Add the components
	for component in lightpath:
	    compName = component[0]
	    nmRange = component[1]
	    
	    if compName.startswith('LSR'):
		staticbox = wx.StaticBox(self.bot_panel, -1, "Excitation Laser")
		laserNM = int(compName.split('LSR')[1])
		
		self.laser = wx.TextCtrl(self.bot_panel, -1, str(laserNM), style=wx.TE_READONLY)
		self.laser.SetBackgroundColour(meta.nmToRGB(laserNM))
		
		laserSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		laserSizer.Add(self.laser, 0) 	    
		self.bot_fgs.Add(laserSizer,  0)
	    
	    if compName.startswith('DMR') or compName.startswith('FLT') or compName.startswith('SLT'):
		staticbox = wx.StaticBox(self.bot_panel, -1, compName)
		
		self.startNM, self.endNM = meta.getNM(nmRange)
		self.spectralRange =  meta.partition(range(self.startNM, self.endNM+1), 5)

		self.spectrum = DrawSpectrum(self.bot_panel, self.startNM, self.endNM)
		
		mirrorSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		mirrorSizer.Add(self.spectrum, 0)
		self.bot_fgs.Add(mirrorSizer, 0)
		
	    if compName.startswith('DYE'):
		staticbox = wx.StaticBox(self.bot_panel, -1, 'DYE')
		dye = compName.split('_')[1]
		emLow, emHgh = meta.getNM(nmRange)
		dyeList = meta.setDyeList(emLow, emHgh)
		if dye not in dyeList:
		    dyeList.append(dye) 
		dyeList.append('Add Dye by double click')
		
		self.dyeListBox = wx.ListBox(self.bot_panel, -1, wx.DefaultPosition, (150, 50), dyeList, wx.LB_SINGLE)
		self.dyeListBox.SetStringSelection(dye)
		self.dyeListBox.Bind(wx.EVT_LISTBOX, partial(self.onEditDye, ch = chName, compNo = lightpath.index(component), opticalpath = lightpath))
		self.dyeListBox.Bind(wx.EVT_LISTBOX_DCLICK, partial(self.onMyDyeSelect, ch = chName, compNo = lightpath.index(component), opticalpath = lightpath))
		
		dye_sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		dye_sizer.Add(self.dyeListBox, 0)               
		self.bot_fgs.Add(dye_sizer, 0) 	    		
		
		
	    if compName.startswith('DTC'):
		staticbox = wx.StaticBox(self.bot_panel, -1, "Detector")
		volt = int(compName.split('DTC')[1])
		
		self.detector = wx.SpinCtrl(self.bot_panel, -1, "", (30, 50))
		self.detector.SetRange(1,1000)
		self.detector.SetValue(volt)
		
		self.detector.Bind(wx.EVT_SPINCTRL, partial(self.onEditDetector, ch = chName, compNo = lightpath.index(component), opticalpath = lightpath))
			 		
		detector_sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		detector_sizer.Add(self.detector, 0)
		self.bot_fgs.Add(detector_sizer, 0)
		

		#pmtSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		#pmtSizer.Add(wx.StaticText(self.bot_panel, -1, volt+' Volts'))
		#self.bot_fgs.Add(pmtSizer, 0)
		
	
	##set the delete button at the end
	self.delete_button = wx.Button(self.bot_panel, wx.ID_DELETE)
	self.delete_button.Bind(wx.EVT_BUTTON, partial(self.onDeleteCh, cn = chName))
	self.bot_fgs.Add(self.delete_button, 0, wx.EXPAND|wx.ALL, 10)
	# Fill up the gap	
	for gap in range(len(lightpath)+3, 31): #because there are 30 cols in fgs max number of componensts it can hold
	    self.bot_fgs.Add(wx.StaticText(self.bot_panel, -1, ''), 0)
		
	#-- Sizers --#
	self.top_panel.SetSizer(self.top_fgs)
	self.bot_panel.SetSizer(self.bot_fgs)
        self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)	 
	
    def onEditDye(self, event, ch, compNo, opticalpath):
	meta = ExperimentSettings.getInstance() 
	ctrl = event.GetEventObject()
		
	opticalpath[compNo][0] = 'DYE'+'_'+ctrl.GetStringSelection()
	tag = 'Instrument|Flowcytometer|%s|%s' %(ch, str(self.page_counter))
	meta.remove_field(tag)
	meta.set_field(tag, opticalpath)
    
    def onMyDyeSelect(self, event, ch, compNo, opticalpath):
	meta = ExperimentSettings.getInstance()
	ctrl = event.GetEventObject()
	
	emLow, emHgh = meta.getNM(opticalpath[compNo][1])
	dye = wx.GetTextFromUser('Enter Dye name within the emission range '+str(emLow)+' - '+str(emHgh), 'Customized Dye')
	if dye != '':
	    ctrl.Delete(ctrl.GetSelection())
	    ctrl.Append(dye)
	    ctrl.SetStringSelection(dye)
	    
	    opticalpath[compNo][0] = 'DYE'+'_'+dye
	    tag = 'Instrument|Flowcytometer|%s|%s' %(ch, str(self.page_counter))
	    meta.remove_field(tag)
	    meta.set_field(tag, opticalpath)
	    
    def onEditDetector(self, event, ch, compNo, opticalpath):
	meta = ExperimentSettings.getInstance() 
	ctrl = event.GetEventObject()

	opticalpath[compNo][0] = 'DTC%s' %str(ctrl.GetValue())
		
	tag = 'Instrument|Flowcytometer|%s|%s' %(ch, str(self.page_counter))
	meta.remove_field(tag)
	meta.set_field(tag, opticalpath)	
		    
    def onDeleteCh(self, event, cn):
	meta = ExperimentSettings.getInstance()
	meta.remove_field('Instrument|Flowcytometer|%s|%s'%(cn, self.page_counter))
	self.bot_fgs.Clear(deleteWindows=True)
	self.showChannels()
	
    def onSavingSettings(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()

	if meta.get_field('Instrument|Flowcytometer|Manufacter|%s'%str(self.page_counter)) is None:
	    dial = wx.MessageDialog(None, 'Please select a manufacturer', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return
	if meta.get_field('Instrument|Flowcytometer|Model|%s'%str(self.page_counter)) is None:
	    dial = wx.MessageDialog(None, 'Please type the model name', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return
	#TO DO check check whether there is atleast one channel optical path being filled
		
	filename = meta.get_field('Instrument|Flowcytometer|Manufacter|%s'%str(self.page_counter))+'_'+meta.get_field('Instrument|Flowcytometer|Model|%s'%str(self.page_counter)).rstrip('\n').rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Flowcytometer settings...', 
	                    defaultDir=os.getcwd(), defaultFile=filename, 
	                    wildcard='.txt', 
	                    style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	
	    f = open(file_path,'w')

	    attributes = meta.get_attribute_list_by_instance('Instrument|Flowcytometer', str(self.page_counter))
	    for attr in attributes:
		info = meta.get_field('Instrument|Flowcytometer|%s|%s' %(attr, self.page_counter))
		f.write('%s = %s\n'%(attr, repr(info)))
	    f.close()	    	
	
    def OnSavingData(self, event):
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)

#########################################################################        
###################     Draw Spectrum on panel size 100,30 pxl  #########
######################################################################### 
class DrawSpectrum(wx.Panel):
    def __init__(self, parent, startNM, endNM):
        wx.Panel.__init__(self, parent,  size=(100, 30), style=wx.SUNKEN_BORDER)

        self.parent = parent	
	
	self.startNM = startNM
	self.endNM = endNM
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event): 
	
	meta = ExperimentSettings.getInstance()  
	
	spectralRange =  meta.partition(range(self.startNM, self.endNM+1), 5)
	
	dc = wx.PaintDC(self)	
	dc.GradientFillLinear((0, 0, 30, 30), meta.nmToRGB(spectralRange[0]), meta.nmToRGB(spectralRange[1]), wx.EAST)
	dc.GradientFillLinear((30, 0, 30, 30), meta.nmToRGB(spectralRange[1]), meta.nmToRGB(spectralRange[2]), wx.EAST)
	dc.GradientFillLinear((60, 0, 30, 30), meta.nmToRGB(spectralRange[2]), meta.nmToRGB(spectralRange[3]), wx.EAST)
	dc.GradientFillLinear((90, 0, 30, 30), meta.nmToRGB(spectralRange[3]), meta.nmToRGB(spectralRange[4]), wx.EAST)
	dc.GradientFillLinear((120, 0, 30, 30), meta.nmToRGB(spectralRange[4]), meta.nmToRGB(spectralRange[5]), wx.EAST)
	dc.EndDrawing()	
	
    def OnSize(self, event):
	self.Refresh()

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
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = sorted(meta.get_field_instances('ExptVessel|Plate'))
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of plates in the stack'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.platenum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_plate_ids:
            self.platenum.Enable() 
        else:
            self.platenum.SetStringSelection(meta.get_field('ExptVessel|Plate|Number|'+str(inc_plate_ids[0])))
            self.platenum.Disable()            
        fgs.Add(self.platenum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_plate_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Plate|GroupName|%s'%str(inc_plate_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
            
        #--Design--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Design'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Coating'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.platecoat = wx.Choice(self.sw, -1, choices=['None','Collagen IV','Gelatin','Poly-L-Lysine','Poly-D-Lysine', 'Fibronectin', 'Laminin','Poly-D-Lysine + Laminin', 'Poly-L-Ornithine+Laminin'])
        if not inc_plate_ids:
            self.platecoat.Enable()
        else:
            self.platecoat.SetStringSelection(meta.get_field('ExptVessel|Plate|Coat|%s'%str(inc_plate_ids[0])))
            self.platecoat.Disable()
        fgs.Add(self.platecoat, 0, wx.EXPAND)
                    
        #--Plate Material--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Material'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.platematerial = wx.Choice(self.sw, -1, choices=['Plastic','Glass'])
        if not inc_plate_ids:
            self.platematerial.Enable()
        else:
            self.platematerial.SetStringSelection(meta.get_field('ExptVessel|Plate|Material|%s'%str(inc_plate_ids[0])))
            self.platematerial.Disable()
        fgs.Add(self.platematerial, 0, wx.EXPAND)
                
        #--Well Shape--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Well Shape'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.wellshape = wx.Choice(self.sw, -1, choices=['Square','Round','Oval'])
        if not inc_plate_ids:
            self.wellshape.Enable()
        else:
            self.wellshape.SetStringSelection(meta.get_field('ExptVessel|Plate|Shape|%s'%str(inc_plate_ids[0])))
            self.wellshape.Disable()
        fgs.Add(self.wellshape, 0, wx.EXPAND)
                
        #--Well Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Well Size (mm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
            plate_design = self.platedesign.GetClientData(self.platedesign.GetSelection())
            pid ='Plate'+str(plate_id)
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate('Plate', str(plate_id), plate_design, self.groupname.GetValue())
            else:
                PlateDesign.set_plate_format(pid, plate_design)
        
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
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = sorted(meta.get_field_instances('ExptVessel|Flask'))
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of flasks in the stack'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.flasknum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_flask_ids:
            self.flasknum.Enable() 
        else:
            self.flasknum.SetStringSelection(meta.get_field('ExptVessel|Flask|Number|'+str(inc_flask_ids[0])))
            self.flasknum.Disable()            
        fgs.Add(self.flasknum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_flask_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Flask|GroupName|%s'%str(inc_flask_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
        
        #--Fask Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Flask Size (cm2)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.flasksize = wx.Choice(self.sw, -1, choices=['12.5','25','75','150','175'])
        if not inc_flask_ids:
            self.flasksize.Enable()
        else:
            self.flasksize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Flask|Size|%s'%str(inc_flask_ids[0])))
            self.flasksize.Disable()
        fgs.Add(self.flasksize, 0, wx.EXPAND)
        
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Flask Coating'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
            id = 'Flask%s'%(flask_id)
            plate_design = (1,1)  # since flask is alwasys a sigle entity resembling to 1x1 well plate format   
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate('Flask', str(flask_id), plate_design, self.groupname.GetValue())
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
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = sorted(meta.get_field_instances('ExptVessel|Dish'))
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of dishs in the stack'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.dishnum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_dish_ids:
            self.dishnum.Enable() 
        else:
            self.dishnum.SetStringSelection(meta.get_field('ExptVessel|Dish|Number|'+str(inc_dish_ids[0])))
            self.dishnum.Disable()            
        fgs.Add(self.dishnum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_dish_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Dish|GroupName|%s'%str(inc_dish_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
        
        #--Dish Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Dish Size (mm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.dishsize = wx.Choice(self.sw, -1, choices=['35','60','100','150'])
        if not inc_dish_ids:
            self.dishsize.Enable()
        else:
            self.dishsize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Dish|Size|%s'%str(inc_dish_ids[0])))
            self.dishsize.Disable()
        fgs.Add(self.dishsize, 0, wx.EXPAND)
        
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Dish Coating'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
            plate_design = (1,1)  # since dish is alwasys a sigle entity resembling to 1x1 well plate format   
            id = 'Dish%s'%(dish_id)
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate('Dish', str(dish_id), plate_design, self.groupname.GetValue())
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
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)
         
        # Get all the previously encoded Microscope pages and re-Add them as pages
        field_ids = sorted(meta.get_field_instances('ExptVessel|Coverslip'))
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Total number of coverslips in the stack'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.coverslipnum = wx.Choice(self.sw, -1,  choices= map(str, range(1,25)))
        if not inc_coverslip_ids:
            self.coverslipnum.Enable() 
        else:
            self.coverslipnum.SetStringSelection(meta.get_field('ExptVessel|Coverslip|Number|'+str(inc_coverslip_ids[0])))
            self.coverslipnum.Disable()            
        fgs.Add(self.coverslipnum, 0, wx.EXPAND)
                
        #--- Group name---#
        fgs.Add(wx.StaticText(self.sw, -1, 'Stack Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.groupname = wx.TextCtrl(self.sw, -1, value='')
        if not inc_coverslip_ids:
            self.groupname.Enable()
        else:
            self.groupname = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Coverslip|GroupName|%s'%str(inc_coverslip_ids[0])))
            self.groupname.Disable()
        fgs.Add(self.groupname, 0, wx.EXPAND)
        
        #--Coverslip Size--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Coverslip Size (mm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.coverslipsize = wx.Choice(self.sw, -1, choices=['12','22'])
        if not inc_coverslip_ids:
            self.coverslipsize.Enable()
        else:
            self.coverslipsize = wx.TextCtrl(self.sw, -1, value=meta.get_field('ExptVessel|Coverslip|Size|%s'%str(inc_coverslip_ids[0])))
            self.coverslipsize.Disable()
        fgs.Add(self.coverslipsize, 0, wx.EXPAND)
        
        #--Coating--#
        fgs.Add(wx.StaticText(self.sw, -1, 'Coverslip Coating'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
            id = 'Coverslip%s'%(coverslip_id)
            plate_design = (1,1)  # since coverslip is alwasys a sigle entity resembling to 1x1 well plate format   
            if id not in PlateDesign.get_plate_ids():
                PlateDesign.add_plate('Coverslip', str(coverslip_id), plate_design, self.groupname.GetValue())
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
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'CellTransfer|Seed'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = CellSeedPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)      

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = CellSeedPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Stock Culture'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[celllineselcTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)

        # Seeding Density
        seedTAG = 'CellTransfer|Seed|SeedingDensity|'+str(self.page_counter)
        self.settings_controls[seedTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seedTAG, default=''))
        self.settings_controls[seedTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seedTAG].SetToolTipString('Number of cells seeded in each well or flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Seeding Density'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[seedTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        # Medium Used
        medmTAG = 'CellTransfer|Seed|MediumUsed|'+str(self.page_counter)
        self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
        if meta.get_field(medmTAG) is not None:
            self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
        self.settings_controls[medmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #  Medium Addatives
        medaddTAG = 'CellTransfer|Seed|MediumAddatives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetToolTipString('Any medium additives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Additives'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        # Trypsinization
        trypsTAG = 'CellTransfer|Seed|Trypsinizatiton|'+str(self.page_counter)
        self.settings_controls[trypsTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(trypsTAG) is not None:
            self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
        self.settings_controls[trypsTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Trypsinization'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)



########################################################################        
################## CELL HARVEST PANEL #########################
########################################################################
class CellHarvestSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'CellTransfer|Harvest'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = CellHarvestPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)       

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = CellHarvestPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)

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
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Cell Line'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[celllineselcTAG], 0, wx.EXPAND)

        # Seeding Density
        harvestTAG = 'CellTransfer|Harvest|HarvestingDensity|'+str(self.page_counter)
        self.settings_controls[harvestTAG] = wx.TextCtrl(self.sw, value=meta.get_field(harvestTAG, default=''))
        self.settings_controls[harvestTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[harvestTAG].SetToolTipString('Number of cells harvested from each well or flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Harvesting Density'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[harvestTAG], 0, wx.EXPAND)

        # Medium Used
        medmTAG = 'CellTransfer|Harvest|MediumUsed|'+str(self.page_counter)
        self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
        if meta.get_field(medmTAG) is not None:
            self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
        self.settings_controls[medmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND) 

        #  Medium Addatives
        medaddTAG = 'CellTransfer|Harvest|MediumAddatives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetToolTipString('Any medium addatives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Addatives'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)

        # Trypsinization
        trypsTAG = 'CellTransfer|Harvest|Trypsinizatiton|'+str(self.page_counter)
        self.settings_controls[trypsTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(trypsTAG) is not None:
            self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
        self.settings_controls[trypsTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Trypsinization'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[trypsTAG], 0, wx.EXPAND)  

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)



########################################################################        
################## CHEMICAL SETTING PANEL ###########################
########################################################################	    
class ChemicalSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Perturbation|Chem'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = ChemicalAgentPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = ChemicalAgentPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)

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
        fgs.Add(wx.StaticText(self.sw, -1, 'Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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

        fgs.Add(wx.StaticText(self.sw, -1, 'Concentration'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[concTAG], 0, wx.EXPAND)
        fgs.Add(self.settings_controls[unitTAG], 0, wx.EXPAND)
        
         #  Manufacturer
        chemmfgTAG = 'Perturbation|Chem|Manufacturer|'+str(self.page_counter)
        self.settings_controls[chemmfgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemmfgTAG, default=''))
        self.settings_controls[chemmfgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemmfgTAG].SetToolTipString('Name of the Chemical agent Manufacturer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[chemmfgTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Catalogue Number
        chemcatTAG = 'Perturbation|Chem|CatNum|'+str(self.page_counter)
        self.settings_controls[chemcatTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemcatTAG, default=''))
        self.settings_controls[chemcatTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemcatTAG].SetToolTipString('Name of the Chemical agent Catalogue Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Catalogue Number'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[chemcatTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
         #  Additives
        chemaddTAG = 'Perturbation|Chem|Additives|'+str(self.page_counter)
        self.settings_controls[chemaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemaddTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[chemaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemaddTAG].SetToolTipString(meta.get_field(chemaddTAG, default=''))
        fgs.Add(wx.StaticText(self.sw, -1, 'Additives'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[chemaddTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
         #  Other informaiton
        chemothTAG = 'Perturbation|Chem|Other|'+str(self.page_counter)
        self.settings_controls[chemothTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemothTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[chemothTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[chemothTAG].SetToolTipString(meta.get_field(chemothTAG, default=''))
        fgs.Add(wx.StaticText(self.sw, -1, 'Other informaiton'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[chemothTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)


        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)


########################################################################        
################## BIOLOGICAL SETTING PANEL ###########################
########################################################################	    
class BiologicalSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Perturbation|Bio'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = BiologicalAgentPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
      

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = BiologicalAgentPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)

        
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
        fgs.Add(wx.StaticText(self.sw, -1, 'RNAi Sequence'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[seqnamTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Sequence accession number
        seqacssTAG = 'Perturbation|Bio|AccessNumber|'+str(self.page_counter)
        self.settings_controls[seqacssTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seqacssTAG, default=''))
        self.settings_controls[seqacssTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seqacssTAG].SetToolTipString('Sequence Accession Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Sequence Accession Number'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[seqacssTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Target GeneAccessNumber
        tgtgenTAG = 'Perturbation|Bio|TargetGeneAccessNum|'+str(self.page_counter)
        self.settings_controls[tgtgenTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tgtgenTAG, default=''))
        self.settings_controls[tgtgenTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tgtgenTAG].SetToolTipString('Target GeneAccessNumber')
        fgs.Add(wx.StaticText(self.sw, -1, 'Target Gene Accession Number'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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

        fgs.Add(wx.StaticText(self.sw, -1, 'Concentration'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[concTAG], 0, wx.EXPAND)
        fgs.Add(self.settings_controls[unitTAG], 0, wx.EXPAND)        
        #  Additives
        bioaddTAG = 'Perturbation|Bio|Additives|'+str(self.page_counter)
        self.settings_controls[bioaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(bioaddTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[bioaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[bioaddTAG].SetToolTipString(meta.get_field(bioaddTAG, default=''))
        fgs.Add(wx.StaticText(self.sw, -1, 'Additives'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[bioaddTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
         #  Other informaiton
        bioothTAG = 'Perturbation|Bio|Other|'+str(self.page_counter)
        self.settings_controls[bioothTAG] = wx.TextCtrl(self.sw, value=meta.get_field(bioothTAG, default=''), style=wx.TE_MULTILINE)
        self.settings_controls[bioothTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[bioothTAG].SetToolTipString(meta.get_field(bioothTAG, default=''))
        fgs.Add(wx.StaticText(self.sw, -1, 'Other informaiton'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[bioothTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    def OnSavingData(self, event):
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)


########################################################################        
################## ANTIBODY SETTING PANEL    ###########################
########################################################################
class ImmunoSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Staining|Immuno'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = ImmunoPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = ImmunoPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = ImmunoPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 


class ImmunoPanel(wx.Panel):    
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
	
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter
	
	self.protocol = 'Staining|Immuno|%s'%str(self.page_counter)

        # Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	top_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

        protnameTAG = 'Staining|Immuno|ProtocolName|'+str(self.page_counter)
        self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
        self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[protnameTAG].SetInitialSize((250,20))
        self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
        self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
        self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	top_fgs.Add(self.save_btn, 0, wx.EXPAND|wx.ALL, 5)	
	
	fgs = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
	# Target Antibody 
	trgtseqTAG = 'Staining|Immuno|Target|'+str(self.page_counter)
	self.settings_controls[trgtseqTAG] = wx.TextCtrl(self.top_panel,  value=meta.get_field(trgtseqTAG, default=''))
	self.settings_controls[trgtseqTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[trgtseqTAG].SetToolTipString('Name of the target antibody')
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Target Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[trgtseqTAG], 0, wx.EXPAND)
	fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
        # Clonality 
	clonalityTAG = 'Staining|Immuno|Clonality|'+str(self.page_counter)
	self.settings_controls[clonalityTAG] = wx.Choice(self.top_panel, -1,  choices=['Monoclonal', 'Polyclonal'])
	if meta.get_field(clonalityTAG) is not None:
	    self.settings_controls[clonalityTAG].SetStringSelection(meta.get_field(clonalityTAG))
	self.settings_controls[clonalityTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
	self.settings_controls[clonalityTAG].SetToolTipString('Clonality')
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Clonality'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[clonalityTAG], 0, wx.EXPAND)
	fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
        # Primary source and associated solvent
        primaryantiTAG = 'Staining|Immuno|Primary|'+str(self.page_counter)
	primaryanti = meta.get_field(primaryantiTAG, [])
	organism_choices =['Homo Sapiens', 'Mus Musculus', 'Rattus Norvegicus', 'Other']
	self.settings_controls[primaryantiTAG+'|0']= wx.ListBox(self.top_panel, -1, wx.DefaultPosition, (120,30), organism_choices, wx.LB_SINGLE)
	if len(primaryanti) > 0:
	    self.settings_controls[primaryantiTAG+'|0'].Append(primaryanti[0])
	    self.settings_controls[primaryantiTAG+'|0'].SetStringSelection(primaryanti[0])
	self.settings_controls[primaryantiTAG+'|0'].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[primaryantiTAG+'|0'].SetToolTipString('Primary source species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Primary Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[primaryantiTAG+'|0'], 0, wx.EXPAND)	
	
	self.settings_controls[primaryantiTAG+'|1'] = wx.TextCtrl(self.top_panel, value='') 
	if len(primaryanti)> 1:
	    self.settings_controls[primaryantiTAG+'|1'].SetValue(primaryanti[1])
	    self.settings_controls[primaryantiTAG+'|1'].SetToolTipString('Solvent used\n%s' %primaryanti[1])
	self.settings_controls[primaryantiTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Solvent'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[primaryantiTAG+'|1'], 0, wx.EXPAND)	
	
	# Secondary source and associated solvent
	scndantiTAG = 'Staining|Immuno|Secondary|'+str(self.page_counter)
	scndanti = meta.get_field(scndantiTAG, [])
	organism_choices =['Homo Sapiens', 'Mus Musculus', 'Rattus Norvegicus', 'Other']
	self.settings_controls[scndantiTAG+'|0']= wx.ListBox(self.top_panel, -1, wx.DefaultPosition, (120,30), organism_choices, wx.LB_SINGLE)
	if len(scndanti) > 0:
	    self.settings_controls[scndantiTAG+'|0'].Append(scndanti[0])
	    self.settings_controls[scndantiTAG+'|0'].SetStringSelection(scndanti[0])
	self.settings_controls[scndantiTAG+'|0'].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[scndantiTAG+'|0'].SetToolTipString('Secondary source species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Secondary Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[scndantiTAG+'|0'], 0, wx.EXPAND)		

	self.settings_controls[scndantiTAG+'|1'] = wx.TextCtrl(self.top_panel, value='') 
	if len(scndanti)> 1:
	    self.settings_controls[scndantiTAG+'|1'].SetValue(scndanti[1])
	    self.settings_controls[scndantiTAG+'|1'].SetToolTipString('Solvent used\n%s' %scndanti[1])
	self.settings_controls[scndantiTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Solvent'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[scndantiTAG+'|1'], 0, wx.EXPAND)	
	
	# Tertiary source and associated solvent
	tertantiTAG = 'Staining|Immuno|Tertiary|'+str(self.page_counter)
	tertanti = meta.get_field(tertantiTAG, [])
	organism_choices =['Homo Sapiens', 'Mus Musculus', 'Rattus Norvegicus', 'Other']
	self.settings_controls[tertantiTAG+'|0']= wx.ListBox(self.top_panel, -1, wx.DefaultPosition, (120,30), organism_choices, wx.LB_SINGLE)
	if len(tertanti) > 0:
	    self.settings_controls[tertantiTAG+'|0'].Append(tertanti[0])
	    self.settings_controls[tertantiTAG+'|0'].SetStringSelection(tertanti[0])
	self.settings_controls[tertantiTAG+'|0'].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[tertantiTAG+'|0'].SetToolTipString('Tertiary source species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Tertiary Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[tertantiTAG+'|0'], 0, wx.EXPAND)	
	
	self.settings_controls[tertantiTAG+'|1'] = wx.TextCtrl(self.top_panel, value='') 
	if len(tertanti)> 1:
	    self.settings_controls[tertantiTAG+'|1'].SetValue(tertanti[1])
	    self.settings_controls[tertantiTAG+'|1'].SetToolTipString('Solvent used\n%s' %tertanti[1])
	self.settings_controls[tertantiTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Solvent'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[tertantiTAG+'|1'], 0, wx.EXPAND)		
	
	#---------------Layout with sizers---------------
	topsizer = wx.BoxSizer(wx.VERTICAL)
	topsizer.Add(top_fgs)
	topsizer.Add(fgs)
	self.top_panel.SetSizer(topsizer)
	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       


    def onSavingSuppProtocol(self, event):
        # also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('Staining|Immuno|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('Staining|Immuno|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	

	if meta.get_field('Staining|Immuno|ProtocolName|%s'%str(self.page_counter)) is None:
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
        filename = meta.get_field('Staining|Immuno|ProtocolName|%s'%str(self.page_counter))+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
    
########################################################################        
################## PRIMER SETTING PANEL    ###########################
########################################################################
class GeneticSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Staining|Genetic'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = GeneticPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = GeneticPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = GeneticPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 

class GeneticPanel(wx.Panel):
    def __init__(self, parent, page_counter):

	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
	wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

	self.page_counter = page_counter
	self.step_list = []
	
	self.protocol = 'Staining|Genetic|%s'%str(self.page_counter)
	
	# Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	top_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

	protnameTAG = 'Staining|Genetic|ProtocolName|'+str(self.page_counter)
	self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
	self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[protnameTAG].SetInitialSize((250,20))
	self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
	self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
	self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	top_fgs.Add(self.save_btn, 0, wx.ALL, 5)

	#--Target Sequence--#
	targseqTAG = 'Staining|Genetic|Target|'+str(self.page_counter)
	self.settings_controls[targseqTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(targseqTAG, default=''))
	self.settings_controls[targseqTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[targseqTAG].SetInitialSize((100, 20))
	self.settings_controls[targseqTAG].SetToolTipString(meta.get_field(targseqTAG, default=''))
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Target Sequence'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[targseqTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	#--Primer Sequence--#
	primseqTAG = 'Staining|Genetic|Primer|'+str(self.page_counter)
	self.settings_controls[primseqTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(primseqTAG, default=''))
	self.settings_controls[primseqTAG].Bind(wx.EVT_TEXT,self.OnSavingData)
	self.settings_controls[primseqTAG].SetToolTipString(meta.get_field(primseqTAG, default=''))
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Primer Sequence'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[primseqTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)	
        #--Temperature--#
        tempTAG = 'Staining|Genetic|Temp|'+str(self.page_counter)
        self.settings_controls[tempTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(tempTAG, default=''))
        self.settings_controls[tempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tempTAG].SetToolTipString('Temperature')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Temperature'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[tempTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
        #--Carbondioxide--#
        gcTAG = 'Staining|Genetic|GC|'+str(self.page_counter)
        self.settings_controls[gcTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(gcTAG, default=''))
        self.settings_controls[gcTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[gcTAG].SetToolTipString('GC Percentages')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'GC%'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[gcTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)		
    
		
        #---------------Layout with sizers---------------
	self.top_panel.SetSizer(top_fgs)
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       


    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('Staining|Genetic|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('Staining|Genetic|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('Staining|Genetic|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('Staining|Genetic|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
            
########################################################################        
################## STAINING SETTING PANEL    ###########################
########################################################################
class DyeSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Staining|Dye'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = DyePanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = DyePanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = DyePanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 
	    
	
class DyePanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
	
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter
        self.step_list = []
	
	self.protocol = 'Staining|Dye|%s'%str(self.page_counter)
	
        # Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	title_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

        protnameTAG = 'Staining|Dye|ProtocolName|'+str(self.page_counter)
        self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
        self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[protnameTAG].SetInitialSize((250,20))
        self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
        self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
        self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	title_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	title_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	title_fgs.Add(self.save_btn, 0, wx.ALL, 5)	

        #---------------Layout with sizers---------------	
	self.top_panel.SetSizer(title_fgs)
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       

    
    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('Staining|Dye|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('Staining|Dye|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('Staining|Dye|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('Staining|Dye|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
    
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)


########################################################################        
################## SPINNING SETTING PANEL    ###########################
########################################################################
class SpinningSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'AddProcess|Wash'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = SpinPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = SpinPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = SpinPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 


class SpinPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
	
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter
        self.step_list = []
	
	self.protocol = 'AddProcess|Spin|%s'%str(self.page_counter)
	
        # Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	title_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

        protnameTAG = 'AddProcess|Spin|ProtocolName|'+str(self.page_counter)
        self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
        self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[protnameTAG].SetInitialSize((250,20))
        self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
        self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
        self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	title_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	title_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	title_fgs.Add(self.save_btn, 0, wx.ALL, 5)	

        #---------------Layout with sizers---------------	
	self.top_panel.SetSizer(title_fgs)
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       

    
    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Spin|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('AddProcess|Spin|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('AddProcess|Spin|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('AddProcess|Spin|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
 

   

########################################################################        
################## WASH SETTING PANEL    ###########################
########################################################################
class WashSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'AddProcess|Wash'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = WashPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = WashPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = WashPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 


class WashPanel(wx.Panel):
    def __init__(self, parent, page_counter):

	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
	wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

	self.page_counter = page_counter
	self.step_list = []
	
	self.protocol = 'AddProcess|Wash|%s'%str(self.page_counter)
	
	# Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	title_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

	protnameTAG = 'AddProcess|Wash|ProtocolName|'+str(self.page_counter)
	self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
	self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[protnameTAG].SetInitialSize((250,20))
	self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
	self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
	self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	title_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	title_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	title_fgs.Add(self.save_btn, 0, wx.ALL, 5)	

	#---------------Layout with sizers---------------	
	self.top_panel.SetSizer(title_fgs)
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       

    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Wash|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('AddProcess|Wash|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('AddProcess|Wash|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('AddProcess|Wash|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)

        
########################################################################        
################## DRY SETTING PANEL    ###########################
########################################################################
class DrySettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'AddProcess|Dry'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = DryPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = DryPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = DryPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 

class DryPanel(wx.Panel):
    def __init__(self, parent, page_counter):

	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
	wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

	self.page_counter = page_counter
	self.step_list = []
	
	self.protocol = 'AddProcess|Dry|%s'%str(self.page_counter)
	
	# Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	title_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

	protnameTAG = 'AddProcess|Dry|ProtocolName|'+str(self.page_counter)
	self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
	self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[protnameTAG].SetInitialSize((250,20))
	self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
	self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
	self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	title_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	title_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	title_fgs.Add(self.save_btn, 0, wx.ALL, 5)	

	#---------------Layout with sizers---------------	
	self.top_panel.SetSizer(title_fgs)
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       

    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Dry|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('AddProcess|Dry|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('AddProcess|Dry|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('AddProcess|Dry|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)

            
########################################################################        
################## MEDIUM SETTING PANEL    ###########################
########################################################################
class MediumSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'AddProcess|Medium'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = MediumPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = MediumPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = MediumPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 



class MediumPanel(wx.Panel):
    def __init__(self, parent, page_counter):

	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
	wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

	self.page_counter = page_counter
	self.step_list = []
	
	self.protocol = 'AddProcess|Medium|%s'%str(self.page_counter)
	
	# Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	title_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

	protnameTAG = 'AddProcess|Medium|ProtocolName|'+str(self.page_counter)
	self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
	self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[protnameTAG].SetInitialSize((250,20))
	self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
	self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
	self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	title_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	title_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	title_fgs.Add(self.save_btn, 0, wx.ALL, 5)	
	
        # Medium Additives
        additiveField = 'AddProcess|Medium|MediumAdditives|'+str(self.page_counter)
	self.settings_controls[additiveField] = wx.TextCtrl(self.top_panel, value=meta.get_field(additiveField, default=''))
	self.settings_controls[additiveField].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[additiveField].SetInitialSize((250,30))
	self.settings_controls[additiveField].SetToolTipString(meta.get_field(additiveField, default=''))
		
	title_fgs.Add(wx.StaticText(self.top_panel, -1, 'Medium additives  '), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	title_fgs.Add(self.settings_controls[additiveField], 0, wx.EXPAND|wx.ALL, 5)
	title_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	
	self.top_panel.SetSizer(title_fgs)

        #---------------Layout with sizers---------------	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       


    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Medium|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('AddProcess|Medium|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('AddProcess|Medium|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('AddProcess|Medium|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls) 


########################################################################        
################## INCUBATOR SETTING PANEL    ###########################
########################################################################            
class IncubatorSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'AddProcess|Incubator'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = IncubatorPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	loadTabBtn = wx.Button(self, label="Load Instance")
	loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = IncubatorPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    
    def onLoadTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return 
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file and setup a new tab
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(next_tab_num))  
	    panel = IncubatorPanel(self.notebook, next_tab_num)
	    self.notebook.AddPage(panel, 'Instance No: %s'%str(next_tab_num), True) 
	
        
class IncubatorPanel(wx.Panel):
    def __init__(self, parent, page_counter):

	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
	wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

	self.page_counter = page_counter
	self.step_list = []
	
	self.protocol = 'AddProcess|Incubator|%s'%str(self.page_counter)
	
	# Top panel for static information and bottom pannel for adding steps
	self.top_panel = wx.Panel(self)	
	self.bot_panel  = StepBuilder(self, self.protocol)
	
	top_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)

	protnameTAG = 'AddProcess|Incubator|ProtocolName|'+str(self.page_counter)
	self.settings_controls[protnameTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(protnameTAG, default=''))
	self.settings_controls[protnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[protnameTAG].SetInitialSize((250,20))
	self.settings_controls[protnameTAG].SetToolTipString('Type a unique name for identifying the protocol')
	self.save_btn = wx.Button(self.top_panel, -1, "Save Protocol")
	self.save_btn.Bind(wx.EVT_BUTTON, self.onSavingSuppProtocol)
	
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Protocol Title/Name'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[protnameTAG], 0, wx.EXPAND|wx.ALL, 5) 
	top_fgs.Add(self.save_btn, 0, wx.ALL, 5)

	#--Manufacture--#
	incbmfgTAG = 'AddProcess|Incubator|Manufacter|'+str(self.page_counter)
	self.settings_controls[incbmfgTAG] = wx.TextCtrl(self.top_panel, name='Manufacter' ,  value=meta.get_field(incbmfgTAG, default=''))
	self.settings_controls[incbmfgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[incbmfgTAG].SetInitialSize((100, 20))
	self.settings_controls[incbmfgTAG].SetToolTipString('Manufacturer name')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Manufacturer'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[incbmfgTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	#--Model--#
	incbmdlTAG = 'AddProcess|Incubator|Model|'+str(self.page_counter)
	self.settings_controls[incbmdlTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(incbmdlTAG, default=''))
	self.settings_controls[incbmdlTAG].Bind(wx.EVT_TEXT,self.OnSavingData)
	self.settings_controls[incbmdlTAG].SetToolTipString('Model number of the Incubator')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[incbmdlTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)	
        #--Temperature--#
        incbTempTAG = 'AddProcess|Incubator|Temp|'+str(self.page_counter)
        self.settings_controls[incbTempTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(incbTempTAG, default=''))
        self.settings_controls[incbTempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbTempTAG].SetToolTipString('Temperature of the incubator')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Temperature'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[incbTempTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
        #--Carbondioxide--#
        incbCarbonTAG = 'AddProcess|Incubator|C02|'+str(self.page_counter)
        self.settings_controls[incbCarbonTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(incbCarbonTAG, default=''))
        self.settings_controls[incbCarbonTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'CO2%'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[incbCarbonTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)		
        #--Humidity--#
        incbHumTAG = 'AddProcess|Incubator|Humidity|'+str(self.page_counter)
        self.settings_controls[incbHumTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(incbHumTAG, default=''))
        self.settings_controls[incbHumTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbHumTAG].SetToolTipString('Humidity at the incubator')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Humidity'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[incbHumTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)		
        #--Pressure--#
        incbPressTAG = 'AddProcess|Incubator|Pressure|'+str(self.page_counter)
        self.settings_controls[incbPressTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(incbPressTAG, default=''))
        self.settings_controls[incbPressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[incbPressTAG].SetToolTipString('Pressure at the incubator')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Pressure'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[incbPressTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)	
		
        #---------------Layout with sizers---------------
	self.top_panel.SetSizer(top_fgs)
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Show()       


    def onSavingSuppProtocol(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Incubator|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	for step in steps:
	    step_info = meta.get_field('AddProcess|Incubator|%s|%s' %(step, str(self.page_counter)))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return	
    
	if not meta.get_field('AddProcess|Incubator|ProtocolName|%s'%str(self.page_counter)):
	    dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()  
	    return	
		
	filename = meta.get_field('AddProcess|Incubator|ProtocolName|%s'%str(self.page_counter)).rstrip('\n')
	filename = filename+'.txt'
		
	dlg = wx.FileDialog(None, message='Saving Supplementary protocol...', 
                            defaultDir=os.getcwd(), defaultFile=filename, 
                            wildcard='.txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
	if dlg.ShowModal() == wx.ID_OK:
	    dirname=dlg.GetDirectory()
	    self.file_path = os.path.join(dirname, filename)
	    meta.save_supp_protocol_file(self.file_path, self.protocol)
		    
     
    def OnSavingData(self, event):
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
            
########################################################################        
################## TIMELAPSE SETTING PANEL    ##########################
########################################################################
class TLMSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'DataAcquis|TLM'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = TLMPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)
	#loadTabBtn = wx.Button(self, label="Load Instance")
	#loadTabBtn.Bind(wx.EVT_BUTTON, self.onLoadTab)        

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	#btnSizer.Add(loadTabBtn , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = TLMPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)


class TLMPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
	
	#------- Heading ---#
	text = wx.StaticText(self.sw, -1, 'Timelapse Image Format')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD)
	text.SetFont(font)
	titlesizer = wx.BoxSizer(wx.VERTICAL)
	titlesizer.Add(text, 0)	
	fgs.Add(titlesizer, 0)
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #-- Microscope selection ---#
        tlmselctTAG = 'DataAcquis|TLM|MicroscopeInstance|'+str(self.page_counter)
        self.settings_controls[tlmselctTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmselctTAG, default=''))        
        showInstBut = wx.Button(self.sw, -1, 'Show Channels', (100,100))
        showInstBut.Bind (wx.EVT_BUTTON, self.OnShowDialog)
        self.settings_controls[tlmselctTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tlmselctTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)
        #-- Image Format ---#
	tlmfrmtTAG = 'DataAcquis|TLM|Format|'+str(self.page_counter)
	organism_choices =['tiff', 'jpeg', 'stk', 'Other']
	self.settings_controls[tlmfrmtTAG]= wx.ListBox(self.sw, -1, wx.DefaultPosition, (120,30), organism_choices, wx.LB_SINGLE)
	if meta.get_field(tlmfrmtTAG) is not None:
	    self.settings_controls[tlmfrmtTAG].Append(meta.get_field(tlmfrmtTAG))
	    self.settings_controls[tlmfrmtTAG].SetStringSelection(meta.get_field(tlmfrmtTAG))
	self.settings_controls[tlmfrmtTAG].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[tlmfrmtTAG].SetToolTipString('Image Format') 
	fgs.Add(wx.StaticText(self.sw, -1, 'Image Format'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[tlmfrmtTAG], 0, wx.EXPAND)	
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Time Interval
        tlmintTAG = 'DataAcquis|TLM|TimeInterval|'+str(self.page_counter)
        self.settings_controls[tlmintTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmintTAG, default=''))
        self.settings_controls[tlmintTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmintTAG].SetToolTipString('Time interval image was acquired')
        fgs.Add(wx.StaticText(self.sw, -1, 'Time Interval (min)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tlmintTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Total Frame/Pane Number
        tlmfrmTAG = 'DataAcquis|TLM|FrameNumber|'
        self.settings_controls[tlmfrmTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmfrmTAG, default=''))
        self.settings_controls[tlmfrmTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmfrmTAG].SetToolTipString('Total Frame/Pane Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Total Frame/Pane Number'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tlmfrmTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Stacking Order
        tlmstkTAG = 'DataAcquis|TLM|StackProcess|'+str(self.page_counter)
        self.settings_controls[tlmstkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmstkTAG, default=''))
        self.settings_controls[tlmstkTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmstkTAG].SetToolTipString('Stacking Order')
        fgs.Add(wx.StaticText(self.sw, -1, 'Stacking Order'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tlmstkTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Size
        tlmpxlTAG = 'DataAcquis|TLM|PixelSize|'+str(self.page_counter)
        self.settings_controls[tlmpxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxlTAG, default=''))
        self.settings_controls[tlmpxlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmpxlTAG].SetToolTipString('Pixel Size')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tlmpxlTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Conversion
        tlmpxcnvTAG = 'DataAcquis|TLM|PixelConvert|'+str(self.page_counter)
        self.settings_controls[tlmpxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxcnvTAG, default=''))
        self.settings_controls[tlmpxcnvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmpxcnvTAG].SetToolTipString('Pixel Conversion')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[tlmpxcnvTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Software
        tlmsoftTAG = 'DataAcquis|TLM|Software|'+str(self.page_counter)
        self.settings_controls[tlmsoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmsoftTAG, default=''))
        self.settings_controls[tlmsoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmsoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software Name and Version'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
                self.settings_controls[tlmselctTAG].SetValue(meta.get_field('Instrument|Microscope|ChannelName|%s'%str(instance)))
        dia.Destroy()

    def OnSavingData(self, event):
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
        
########################################################################        
################## STATIC SETTING PANEL    ##########################
########################################################################
class HCSSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'DataAcquis|HCS'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = HCSPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = HCSPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    

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
        showInstBut = wx.Button(self.sw, -1, 'Show Channels', (100,100))
        showInstBut.Bind (wx.EVT_BUTTON, self.OnShowDialog) 
        self.settings_controls[hcsselctTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcsselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[hcsselctTAG], 0, wx.EXPAND)
        fgs.Add(showInstBut, 0, wx.EXPAND)	
        #-- Image Format ---#
	hcsfrmtTAG = 'DataAcquis|HCS|Format|'+str(self.page_counter)
	organism_choices =['tiff', 'jpeg', 'stk', 'Other']
	self.settings_controls[hcsfrmtTAG]= wx.ListBox(self.sw, -1, wx.DefaultPosition, (120,30), organism_choices, wx.LB_SINGLE)
	if meta.get_field(hcsfrmtTAG) is not None:
	    self.settings_controls[hcsfrmtTAG].Append(meta.get_field(hcsfrmtTAG))
	    self.settings_controls[hcsfrmtTAG].SetStringSelection(meta.get_field(hcsfrmtTAG))
	self.settings_controls[hcsfrmtTAG].Bind(wx.EVT_LISTBOX, self.OnSavingData)   
	self.settings_controls[hcsfrmtTAG].SetToolTipString('Image Format') 
	fgs.Add(wx.StaticText(self.sw, -1, 'Image Format'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[hcsfrmtTAG], 0, wx.EXPAND)	
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Size
        hcspxlTAG = 'DataAcquis|HCS|PixelSize|'+str(self.page_counter)
        self.settings_controls[hcspxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxlTAG, default=''))
        self.settings_controls[hcspxlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcspxlTAG].SetToolTipString('Pixel Size')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[hcspxlTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Pixel Conversion
        hcspxcnvTAG = 'DataAcquis|HCS|PixelConvert|'+str(self.page_counter)
        self.settings_controls[hcspxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxcnvTAG, default=''))
        self.settings_controls[hcspxcnvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcspxcnvTAG].SetToolTipString('Pixel Conversion')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[hcspxcnvTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Software
        hcssoftTAG = 'DataAcquis|HCS|Software|'+str(self.page_counter)
        self.settings_controls[hcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcssoftTAG, default=''))
        self.settings_controls[hcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcssoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, 'Software Name and Version'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
		    self.settings_controls[hcsselctTAG].SetValue(meta.get_field('Instrument|Microscope|ChannelName|%s'%str(instance)))
	    dia.Destroy()    

    def OnSavingData(self, event):
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)
	    


########################################################################        
################## FLOW SETTING PANEL    ##########################
########################################################################
class FCSSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'DataAcquis|FCS'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = FCSPanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.is_supp_protocol_filled(self.protocol, str(int(next_tab_num)-1)) is False:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = FCSPanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)

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
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Flow Cytometer'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Select FCS file Format'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(self.settings_controls[fcsfrmtTAG], 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #  Software
        fcssoftTAG = 'DataAcquis|FCS|Software|'+str(self.page_counter)
        self.settings_controls[fcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(fcssoftTAG, default=''))
        self.settings_controls[fcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[fcssoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, 'Software Name and Version'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
        ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	meta.saveData(ctrl, tag, self.settings_controls)

########################################################################        
################## NoteSettingPanel             #########################
########################################################################
class NoteSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Notes'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, meta.onTabClosing)

	for instance_id in sorted(meta.get_field_instances(self.protocol)):
	    panel = NotePanel(self.notebook, int(instance_id))
	    self.notebook.AddPage(panel, 'Instance No: %s'%(instance_id), True)
		
	# Buttons
	createTabBtn = wx.Button(self, label="Create Instance")
	createTabBtn.Bind(wx.EVT_BUTTON, self.onCreateTab)

	# Sizers
	mainsizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	mainsizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(createTabBtn  , 0, wx.ALL, 5)
	mainsizer.Add(btnSizer)
	self.SetSizer(mainsizer)
	self.Layout()
	
    def onCreateTab(self, event):
	next_tab_num = meta.get_new_protocol_id(self.protocol)
	if meta.does_tag_exists(self.protocol, str(int(next_tab_num)-1)) is True:
	    dlg = wx.MessageDialog(None, 'Can not create instance\nPlease fill information in Instance No: %s'%str(int(next_tab_num)-1), 'Deleting..', wx.OK| wx.ICON_STOP)
	    dlg.ShowModal()
	    return  	    
	
	panel = NotePanel(self.notebook, next_tab_num)
	self.notebook.AddPage(panel, 'Instance No: %s'%next_tab_num, True)
    


class NotePanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter
        self.sw = wx.ScrolledWindow(self)
 
        self.top_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)	
	self.bot_fgs = wx.FlexGridSizer(cols=1, hgap=5, vgap=5)
	
	self.noteSelect = wx.Choice(self.sw, -1,  choices=['CriticalPoint', 'Rest', 'Hint', 'URL', 'Video'])
	self.noteSelect.SetStringSelection('')
	self.noteSelect.Bind(wx.EVT_CHOICE, self.onCreateNotepad)
	self.top_fgs.Add(wx.StaticText(self.sw, -1, 'Note type'), 0)
	self.top_fgs.Add(self.noteSelect, 0, wx.EXPAND)
	self.top_fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	
	#---------------Layout with sizers---------------
	self.mainSizer = wx.BoxSizer(wx.VERTICAL)
	self.mainSizer.Add(self.top_fgs)
	self.mainSizer.Add(self.bot_fgs)
	self.sw.SetSizer(self.mainSizer)
	self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)		
	
	if meta.get_field_tags('Notes|', str(self.page_counter)):
	    self.noteTAG = meta.get_field_tags('Notes|', str(self.page_counter))[0]
	    self.noteType = exp.get_tag_event(self.noteTAG)
	    self.noteSelect.SetStringSelection(self.noteType)
	    self.noteSelect.Disable()
	    self.createNotePad()	

	

    def onCreateNotepad(self, event):
	ctrl = event.GetEventObject()
	self.noteType = ctrl.GetStringSelection()
	self.createNotePad()
    
    def createNotePad(self):		
	if self.noteType=='CriticalPoint' or self.noteType=='Rest'or self.noteType=='Hint':
	    self.noteDescrip = wx.TextCtrl(self.sw,  value=meta.get_field('Notes|%s|Description|%s' %(self.noteType, str(self.page_counter)), default=''), style=wx.TE_MULTILINE)
	    self.noteDescrip.Bind(wx.EVT_TEXT, self.OnSavingData)
	    self.noteDescrip.SetInitialSize((250, 300))
	    self.noteSelect.SetStringSelection(self.noteType)
	    self.noteSelect.Disable()
	   
	    self.top_fgs.Add(wx.StaticText(self.sw, -1, 'Note Description'), 0)
	    self.top_fgs.Add(self.noteDescrip, 0,  wx.EXPAND)
	    self.top_fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	

	if self.noteType == 'URL':
	    self.noteDescrip = wx.TextCtrl(self.sw,  value=meta.get_field('Notes|%s|Description|%s' %(self.noteType, str(self.page_counter)), default='http://www.jove.com/'))
	    self.noteDescrip.Bind(wx.EVT_TEXT, self.OnSavingData)
	    self.noteDescrip.SetInitialSize((250, 20))
	    self.noteSelect.SetStringSelection(self.noteType)
	    self.noteSelect.Disable()
	    
	    goURLBtn = wx.Button(self.sw, -1, 'Go to URL')
	    goURLBtn.Bind(wx.EVT_BUTTON, self.goURL)
	    
	    self.top_fgs.Add(wx.StaticText(self.sw, -1, 'Paste URL'), 0)
	    self.top_fgs.Add(self.noteDescrip, 0,  wx.EXPAND)
	    self.top_fgs.Add(goURLBtn, 0, wx.EXPAND)

	if self.noteType == 'Video':
	    self.mediaTAG = 'Notes|%s|Description|%s' %(self.noteType, str(self.page_counter))
	    self.noteDescrip = wx.TextCtrl(self.sw, value=meta.get_field(self.mediaTAG, default=''))
	    self.noteDescrip.Bind(wx.EVT_TEXT, self.OnSavingData)	    
	    self.browseBtn = wx.Button(self.sw, -1, 'Load Media File')
	    self.browseBtn.Bind(wx.EVT_BUTTON, self.loadFile)
	    self.mediaplayer = MediaPlayer(self.sw)
	    
	    if meta.get_field('Notes|%s|Description|%s' %(self.noteType, str(self.page_counter))) is not None:	
		self.mediaplayer.mc.Load(meta.get_field('Notes|%s|Description|%s' %(self.noteType, str(self.page_counter))))		

	    self.top_fgs.Add(wx.StaticText(self.sw, -1, 'Media file path'), 0)
	    self.top_fgs.Add(self.noteDescrip, 0)
	    self.top_fgs.Add(self.browseBtn, 0)
	    
	    self.bot_fgs.Add(self.mediaplayer, 0)

	self.sw.SetSizer(self.mainSizer)
	self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)	
	
    def loadFile(self, event):
	dlg = wx.FileDialog(None, "Select a media file",
	                        defaultDir=os.getcwd(), wildcard='*.mp3;*.mpg;*.mid;*.wav; *.wmv;*.au;*.avi', style=wx.OPEN|wx.FD_CHANGE_DIR)
		# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)
	    self.noteDescrip.SetValue(file_path)
	    self.mediaplayer.mc.Load(file_path)
		
    def onFileLoad(self, event):
	self.path = self.fbb.GetValue()
	self.mediaplayer.mc.Load(self.path)    
    
    def goURL(self, event):
	try:
	    webbrowser.open(self.noteDescrip.GetValue())
	except:
            dial = wx.MessageDialog(None, 'Unable to launch internet browser', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return

    def OnSavingData(self, event):	
        meta = ExperimentSettings.getInstance()    
        self.noteTAG = 'Notes|%s|Description|%s' %(self.noteType, str(self.page_counter))
        meta.set_field(self.noteTAG, self.noteDescrip.GetValue())

class MediaPlayer(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,  size=(250, 300))
        self.SetBackgroundColour(self.GetBackgroundColour())

        try:
            self.mc = wx.media.MediaCtrl(self)
        except:
            dial = wx.MessageDialog(None, 'Unable to play media file', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.mc, 0, border=10)
        self.SetSizer(vsizer)
        
        self.mc.ShowPlayerControls()

    #def onPlay(self):
        #self.mc.Play()

        
if __name__ == '__main__':
    app = wx.App(False)
    
    frame = wx.Frame(None, title='ProtocolNavigator', size=(650, 650))
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