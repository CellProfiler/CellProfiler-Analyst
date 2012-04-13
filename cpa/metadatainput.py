#!/usr/bin/env python

import wx
import os
import re
import sys
import operator
import  wx.calendar
import wx.lib.agw.flatnotebook as fnb
import wx.lib.mixins.listctrl as listmix
import  wx.gizmos   as  gizmos
import string, os
import wx.lib.agw.foldpanelbar as fpb
import experimentsettings as exp
import wx.html
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
	
	#self.settings_panel.Destroy()
	#self.settings_container.Sizer.Clear()
	
	if get_tag_type(tag) == 'Perturbation' and get_tag_event(tag) == 'Biological':
	    #open the perturbation-->biological page in the notebook
            self.settings_panel = BiologicalAgentPanel(self.settings_container)
	    #select the appropirate tab based on the instance of the tag
	    
	
	
	print get_tag_type(tag)
	print get_tag_event(tag)
	print get_tag_instance(tag)

                
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
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Title'), 0)
        fgs.Add(self.settings_controls[titleTAG], 0, wx.EXPAND)
        # Experiment Aim
        aimTAG = 'Overview|Project|Aims'
        self.settings_controls[aimTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(aimTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[aimTAG].SetInitialSize((300, 50))
        self.settings_controls[aimTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[aimTAG].SetToolTipString('Describe here the aim of the experiment')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Aim'), 0)
        fgs.Add(self.settings_controls[aimTAG], 0, wx.EXPAND)
	# Experiment Aim
	fundTAG = 'Overview|Project|Fund'
	self.settings_controls[fundTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(fundTAG, default=''), style=wx.TE_PROCESS_ENTER)
	self.settings_controls[fundTAG].SetInitialSize((300, 20))
	self.settings_controls[fundTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[fundTAG].SetToolTipString('Project funding codes')
	fgs.Add(wx.StaticText(self.sw, -1, 'Funding Code'), 0)
	fgs.Add(self.settings_controls[fundTAG], 0, wx.EXPAND)	
        # Keywords
        keyTAG = 'Overview|Project|Keywords'
        self.settings_controls[keyTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(keyTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
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
        self.settings_controls[exppubTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(exppubTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[exppubTAG].SetInitialSize((300, 50))
        self.settings_controls[exppubTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[exppubTAG].SetToolTipString('Experiment related publication list')
        fgs.Add(wx.StaticText(self.sw, -1, 'Related Publications'), 0)
        fgs.Add(self.settings_controls[exppubTAG], 0, wx.EXPAND)
        # Experimenter Name
        expnameTAG = 'Overview|Project|Experimenter'
        self.settings_controls[expnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(expnameTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
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
        self.settings_controls[deptnameTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(deptnameTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.settings_controls[deptnameTAG].SetInitialSize((300, 20))
        self.settings_controls[deptnameTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[deptnameTAG].SetToolTipString('Name of the Department')
        fgs.Add(wx.StaticText(self.sw, -1, 'Department Name'), 0)
        fgs.Add(self.settings_controls[deptnameTAG], 0, wx.EXPAND)
        # Address
        addressTAG = 'Overview|Project|Address'
        self.settings_controls[addressTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(addressTAG, default=''), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
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
        stk_list = sorted(meta.get_field_instances('StockCulture|Sample'))
        
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
        cellLineTXT = wx.StaticText(self.top_panel, -1, 'Cell Line')
        cellLineTXT.SetForegroundColour((0,0,0))
        fgs.Add(cellLineTXT, 0)
        fgs.Add(self.settings_controls[cellLineTAG], 0, wx.EXPAND)               
        # ATCC reference
        acttTAG = 'StockCulture|Sample|ATCCref|%s'%str(self.stk_id)
        self.settings_controls[acttTAG] = wx.TextCtrl(self.top_panel, style=wx.TE_PROCESS_ENTER, value=meta.get_field(acttTAG, default=''))
        self.settings_controls[acttTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[acttTAG].SetToolTipString('ATCC reference')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Reference'), 0)
        fgs.Add(self.settings_controls[acttTAG], 0, wx.EXPAND) 
        # Taxonomic ID
        taxIdTAG = 'StockCulture|Sample|Organism|%s'%str(self.stk_id)
        self.settings_controls[taxIdTAG] = wx.Choice(self.top_panel, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
        if meta.get_field(taxIdTAG) is not None:
            self.settings_controls[taxIdTAG].SetStringSelection(meta.get_field(taxIdTAG))
        self.settings_controls[taxIdTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[taxIdTAG].SetToolTipString('Taxonomic ID of the species')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Organism'), 0)
        fgs.Add(self.settings_controls[taxIdTAG], 0, wx.EXPAND)
        # Gender
        gendTAG = 'StockCulture|Sample|Gender|%s'%str(self.stk_id)
        self.settings_controls[gendTAG] = wx.Choice(self.top_panel, -1,  choices=['Male', 'Female', 'Neutral'])
        if meta.get_field(gendTAG) is not None:
            self.settings_controls[gendTAG].SetStringSelection(meta.get_field(gendTAG))
        self.settings_controls[gendTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[gendTAG].SetToolTipString('Gender of the organism')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Gender'), 0)
        fgs.Add(self.settings_controls[gendTAG], 0, wx.EXPAND)        
        # Age
        ageTAG ='StockCulture|Sample|Age|%s'%str(self.stk_id)
        self.settings_controls[ageTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(ageTAG, default=''))
        self.settings_controls[ageTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[ageTAG].SetToolTipString('Age of the organism in days when the cells were collected. .')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Age of organism (days)'), 0)
        fgs.Add(self.settings_controls[ageTAG], 0, wx.EXPAND)
        # Organ
        organTAG = 'StockCulture|Sample|Organ|%s'%str(self.stk_id)
        self.settings_controls[organTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(organTAG, default=''))
        self.settings_controls[organTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[organTAG].SetToolTipString('Organ name from where the cell were collected. eg. Heart, Lung, Bone etc')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Organ'), 0)
        fgs.Add(self.settings_controls[organTAG], 0, wx.EXPAND)
        # Tissue
        tissueTAG = 'StockCulture|Sample|Tissue|%s'%str(self.stk_id)
        self.settings_controls[tissueTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(tissueTAG, default=''))
        self.settings_controls[tissueTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tissueTAG].SetToolTipString('Tissue from which the cells were collected')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Tissue'), 0)
        fgs.Add(self.settings_controls[tissueTAG], 0, wx.EXPAND)
        # Pheotype
        phtypTAG = 'StockCulture|Sample|Phenotype|%s'%str(self.stk_id)
        self.settings_controls[phtypTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(phtypTAG, default=''))
        self.settings_controls[phtypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[phtypTAG].SetToolTipString('Phenotypic examples Colour Height OR any other value descriptor')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Phenotype'), 0)
        fgs.Add(self.settings_controls[phtypTAG], 0, wx.EXPAND)
        # Genotype
        gentypTAG = 'StockCulture|Sample|Genotype|%s'%str(self.stk_id)
        self.settings_controls[gentypTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(gentypTAG, default=''))
        self.settings_controls[gentypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[gentypTAG].SetToolTipString('Wild type or mutant etc. (single word)')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Genotype'), 0)
        fgs.Add(self.settings_controls[gentypTAG], 0, wx.EXPAND)
        # Strain
        strainTAG = 'StockCulture|Sample|Strain|%s'%str(self.stk_id)
        self.settings_controls[strainTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(strainTAG, default=''))
        self.settings_controls[strainTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[strainTAG].SetToolTipString('Starin of that cell line eGFP, Wild type etc')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Strain'), 0)
        fgs.Add(self.settings_controls[strainTAG], 0, wx.EXPAND)
        #  Passage Number
        passTAG = 'StockCulture|Sample|OrgPassageNo|%s'%str(self.stk_id)
        self.settings_controls[passTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(passTAG, default=''))
        self.settings_controls[passTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[passTAG].SetToolTipString('Numeric value of the passage of the cells under investigation')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Original Passage Number'), 0)
        fgs.Add(self.settings_controls[passTAG], 0, wx.EXPAND)
        #  Cell Density
        densityTAG = 'StockCulture|Sample|Density|%s'%str(self.stk_id)
        self.settings_controls[densityTAG] = wx.TextCtrl(self.top_panel,  style=wx.TE_PROCESS_ENTER, value=meta.get_field(densityTAG, default=''))
        self.settings_controls[densityTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[densityTAG].SetToolTipString('Numeric value of the cell density at the culture flask')
        fgs.Add(wx.StaticText(self.top_panel, -1, 'Cell Density'), 0)
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
	
	self.protocol = 'Instrument|Microscope'

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
        for protocol_id in supp_protocol_list:
            panel = MicroscopePanel(self.notebook, int(protocol_id))
            self.notebook.AddPage(panel, 'Microscope No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Microscope Settings")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Microscope Setttings")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = MicroscopePanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Microscope No: %s'%str(self.next_page_num), True)
        self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
        meta = ExperimentSettings.getInstance()
        
        dlg = wx.FileDialog(None, "Select the file containing microscope settings...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        # read the supp protocol file
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	# set the panel accordingly    
	panel = MicroscopePanel(self.notebook, self.next_page_num)
	self.notebook.AddPage(panel, 'Microscope No: %s'%str(self.next_page_num), True)
	self.next_page_num += 1	    
    
        
    #def onTabClosing(self, event):
        #meta = ExperimentSettings.getInstance()
        ##first check whether this is the only instnace then it cant be deleted
        #mic_list = meta.get_field_instances('Instrument|Microscope|')
        
        #if len(mic_list) == 1:
            #event.Veto()
            #dlg = wx.MessageDialog(self, 'Can not delete the only instance', 'Deleting..', wx.OK| wx.ICON_STOP)
            #dlg.ShowModal()
            #return
        
        #tab_caption =  self.notebook.GetPageText(event.GetSelection())
        #self.mic_id = tab_caption.split(':')[1].strip()
        
        #dlg = wx.MessageDialog(self, 'Deleting Microscope no %s' %self.mic_id, 'Deleting..', wx.OK | wx.ICON_WARNING)
        #if dlg.ShowModal() == wx.ID_OK:                    
            ##remove the instances 
            #meta.remove_field('Instrument|Microscope|Manufacter|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Model|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Type|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|LightSource|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Detector|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|LensApprture|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|LensCorr|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|IllumType|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Mode|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Immersion|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Correction|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|NominalMagnification|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|CalibratedMagnification|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|WorkDistance|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Filter|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Software|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Temp|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|C02|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Humidity|%s'%str(self.mic_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Microscope|Pressure|'+str(self.mic_id))


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
	standpane = wx.CollapsiblePane(self.sw, label="Structure", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
	self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, standpane)
	self.standPane(standpane.GetPane())	
	
        illumpane = wx.CollapsiblePane(self.sw, label="Illumination", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, illumpane)
        self.makeIlluminationPane(illumpane.GetPane())
	
	#stagepane = wx.CollapsiblePane(self.sw, label="Stage", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
	#self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, stagepane)
	#self.MakePaneContent(stagepane.GetPane())
	
	#detectpane = wx.CollapsiblePane(self.sw, label="Detector", style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
	#self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, detectpane)
	#self.MakePaneContent(detectpane.GetPane())

	#---  Sizers ---#
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(headfgs, 0, wx.ALL, 25)
	sizer.Add(standpane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
        sizer.Add(illumpane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
	#sizer.Add(stagepane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
	#sizer.Add(detectpane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
	
        self.sw.SetSizer(sizer)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)	
	
	self.updateProgressBar()

    def OnPaneChanged(self, evt=None):
        self.sw.Layout()
    
    def standPane(self, pane):
	''' This pane makes the microscope stand (backbone of the microscope)'''	
	
	meta = ExperimentSettings.getInstance()
	self.pane = pane	
	
	#--- Core Comp ---#	
	staticbox = wx.StaticBox(self.pane, -1, "Microscope Stand")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
	
	microstandTAG = 'Instrument|Microscope|Stand|%s'%str(self.page_counter)
	microstand = meta.get_field(microstandTAG, [])
	
	self.settings_controls[microstandTAG+'|0']= wx.Choice(self.pane, -1, choices=['Wide Field','Laser Scanning Microscopy', 'Laser Scanning Confocal', 'Spinning Disk Confocal', 'Slit Scan Confocal', 'Multi Photon Microscopy', 'Structured Illumination','Single Molecule Imaging', 'Total Internal Reflection', 'Fluorescence Lifetime', 'Spectral Imaging', 'Fluorescence Correlation Spectroscopy', 'Near FieldScanning Optical Microscopy', 'Second Harmonic Generation Imaging', 'Timelapse', 'Other'])
	if len(microstand) > 0:
	    self.settings_controls[microstandTAG+'|0'].SetStringSelection(microstand[0])
	self.settings_controls[microstandTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[microstandTAG+'|0'].SetToolTipString('Type of microscope e.g. Inverted, Confocal...') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[microstandTAG+'|0'], 0, wx.EXPAND)	
	
	self.settings_controls[microstandTAG+'|1']= wx.Choice(self.pane, -1, choices=['Zeiss','Olympus','Nikon', 'MDS', 'GE'])
	if len(microstand) > 1:
	    self.settings_controls[microstandTAG+'|1'].SetStringSelection(microstand[1])
	self.settings_controls[microstandTAG+'|1'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
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
		
	#self.settings_controls[microstandTAG+'|3']= wx.Choice(self.pane, -1, choices=['', 'Upright', 'Inverted', 'Confocal'])
	#if len(microstand) > 3:
	    #self.settings_controls[microstandTAG+'|3'].SetStringSelection(microstand[3])
	#self.settings_controls[microstandTAG+'|3'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	#self.settings_controls[microstandTAG+'|3'].SetToolTipString('Orientation of the microscope in relation to the sample') 
	#multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Orientation'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	#multctrlSizer.Add(self.settings_controls[microstandTAG+'|3'], 0, wx.EXPAND)	
      
	#self.settings_controls[microstandTAG+'|4']= wx.Choice(self.pane, -1, choices=['','1','2','3','4','5','6','7','8','9','10'])
	#if len(microstand) > 4:
	    #self.settings_controls[microstandTAG+'|4'].SetStringSelection(microstand[4])
	#self.settings_controls[microstandTAG+'|4'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	#self.settings_controls[microstandTAG+'|4'].SetToolTipString('Number of lamps used in the microscope') 
	#multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Number of Lamps'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	#multctrlSizer.Add(self.settings_controls[microstandTAG+'|4'], 0, wx.EXPAND)      
	
	#self.settings_controls[microstandTAG+'|5']= wx.Choice(self.pane, -1, choices=['','1','2','3','4','5','6','7','8','9','10'])
	#if len(microstand) > 5:
	    #self.settings_controls[microstandTAG+'|5'].SetStringSelection(microstand[5])
	#self.settings_controls[microstandTAG+'|5'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	#self.settings_controls[microstandTAG+'|5'].SetToolTipString('Number of detectors used in the microscope') 
	#multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Number of Detectors'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	#multctrlSizer.Add(self.settings_controls[microstandTAG+'|5'], 0, wx.EXPAND)   	


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
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Condensor Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
	
	#--- Layout ---#
	
	fgs = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
	fgs.Add(standSizer)
	fgs.Add(condensSizer)

	self.pane.SetSizer(fgs)

    def makeIlluminationPane(self, pane):
	''' This pane makes the Illumination pane of the microscope. Each component of the illum pane can have mulitple components
	which can again has multiple attributes'''
	
	meta = ExperimentSettings.getInstance()
	self.pane = pane
	
	#-- Light Source --#
	staticbox = wx.StaticBox(self.pane, -1, "Light")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	lightsrcTAG = 'Instrument|Microscope|LightSource|'+str(self.page_counter)
	lightsrc = meta.get_field(lightsrcTAG, [])

	self.settings_controls[lightsrcTAG+'|0']= wx.Choice(self.pane, -1, choices=['Laser', 'Filament', 'Arc', 'Light Emitting Diode'])
	if len(lightsrc) > 0:
	    self.settings_controls[lightsrcTAG+'|0'].SetStringSelection(lightsrc[0])
	self.settings_controls[lightsrcTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[lightsrcTAG+'|0'].SetToolTipString('Type of the light source') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Source'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[lightsrcTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[lightsrcTAG+'|1']=  wx.Choice(self.pane, -1,  choices=['Transmitted','Epifluorescence','Oblique','Non Linear'])
	if len(lightsrc)> 1:
	    self.settings_controls[lightsrcTAG+'|1'].SetStringSelection(lightsrc[1])
	self.settings_controls[lightsrcTAG+'|1'].Bind(wx.EVT_CHOICE, self.OnSavingData) 
	self.settings_controls[lightsrcTAG+'|1'].SetToolTipString('Type of the light source') 
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Type'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
	
	lightSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	lightSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)
	
    
	
	#-- Filter --#
	self.pane.filter_bandwidth = '500/400'
	staticbox = wx.StaticBox(self.pane, -1, "Excitation Filter")
	multctrlSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)

	self.extfltTAG = 'Instrument|Microscope|ExtFilter|'+str(self.page_counter)
	extfilter = meta.get_field(self.extfltTAG, [])
	self.startNM, self.endNM = 300, 700
	if len(extfilter)> 1:
	    self.startNM = int(extfilter[0])
	    self.endNM = int(extfilter[1])

	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Spectrum\n(nm)'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

	self.settings_controls[self.extfltTAG +'|0'] = wx.Slider(self.pane, -1, self.startNM, 300, 700, wx.DefaultPosition, (100, -1), wx.SL_LABELS)
	self.settings_controls[self.extfltTAG +'|1'] = wx.Slider(self.pane, -1, self.endNM, 300, 700, wx.DefaultPosition, (100, -1), style = wx.SL_LABELS|wx.SL_TOP)
	
	self.pane.fltTsld = self.settings_controls[self.extfltTAG +'|0']
	self.pane.fltBsld = self.settings_controls[self.extfltTAG +'|1']
	
	self.fltrspectrum = FilterSpectrum(self.pane)

	self.pane.Bind(wx.EVT_SLIDER, self.OnSavingData)
	
	spctrmSizer = wx.BoxSizer(wx.VERTICAL)
	spctrmSizer.Add(self.pane.fltTsld,0)
	spctrmSizer.Add(self.fltrspectrum, 0)
	spctrmSizer.Add(self.pane.fltBsld,0)   
	
	multctrlSizer.Add(spctrmSizer, 0)
	
	self.settings_controls[self.extfltTAG +'|2'] = wx.TextCtrl(self.pane, value='') 	
	if len(extfilter)> 2:
	    self.settings_controls[self.extfltTAG +'|2'].SetValue(extfilter[2])
	self.settings_controls[self.extfltTAG +'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[self.extfltTAG +'|2'].SetToolTipString('Model of condens source')
	multctrlSizer.Add(wx.StaticText(self.pane, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	multctrlSizer.Add(self.settings_controls[self.extfltTAG +'|2'], 0, wx.EXPAND)	
	
	filterSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	filterSizer.Add(multctrlSizer, 1, wx.EXPAND|wx.ALL, 5)	
	
	# --- Layout and Sizers ---#
	fgs = wx.FlexGridSizer(rows=3, cols=3, hgap=5, vgap=5)
	fgs.Add(lightSizer)
	fgs.Add(filterSizer)
	
	self.pane.SetSizer(fgs)
	   

    def MakePaneContent(self, pane):
	pass

    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)    
	
	self.updateProgressBar()
    
    def updateProgressBar(self):
	filledCount = 0
	
	for tag, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
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
	self.endNM = 700

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
	
	# get the component WL of the just previous one
	nmRange =  self.meta.partition(range(self.startNM, self.endNM+1), 5)
	
        fltTsldVal = self.Parent.fltTsld.GetValue()
	fltTsldMinVal = self.Parent.fltTsld.GetMin()
        fltBsldVal = self.Parent.fltBsld.GetValue()
	fltBsldMaxVal = self.Parent.fltBsld.GetMax()
	
	fltTsldMove = (fltTsldVal-fltTsldMinVal)*100/(fltBsldMaxVal-fltTsldMinVal)  # 100 pxl is the physical size of the spectra panel
	fltBsldMove = (fltBsldVal-fltTsldMinVal)*100/(fltBsldMaxVal-fltTsldMinVal)
	        
        # Draw the specturm according to the spectral range
        dc.GradientFillLinear((0, 0, 20, 30), self.meta.nmToRGB(nmRange[0]), self.meta.nmToRGB(nmRange[1]), wx.EAST)
        dc.GradientFillLinear((20, 0, 20, 30), self.meta.nmToRGB(nmRange[1]), self.meta.nmToRGB(nmRange[2]), wx.EAST)
        dc.GradientFillLinear((40, 0, 20, 30), self.meta.nmToRGB(nmRange[2]), self.meta.nmToRGB(nmRange[3]), wx.EAST)
        dc.GradientFillLinear((60, 0, 20, 30), self.meta.nmToRGB(nmRange[3]), self.meta.nmToRGB(nmRange[4]), wx.EAST)
        dc.GradientFillLinear((80, 0, 20, 30), self.meta.nmToRGB(nmRange[4]), self.meta.nmToRGB(nmRange[5]), wx.EAST)
        
        # Draw the slider on the spectrum to depict the selected range within the specta
	dc = wx.PaintDC(self)
	dc.SetPen(wx.Pen(self.GetBackgroundColour()))
	dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
	dc.DrawRectangle(0, 0, fltTsldMove, 30)
	dc.DrawRectangle(fltBsldMove, 0, 100, 30) 

       
    def OnSize(self, event):
        self.Refresh()	
		
    #def __init__(self, parent, mic_id=None):
        #'''
        #mic_id -- the micrscope id subtag to use to populate this form
        #'''
        #self.settings_controls = {}
        #meta = ExperimentSettings.getInstance()
        #wx.Panel.__init__(self, parent=parent)
        
        #if mic_id is None:
            #mic_list = meta.get_field_instances('Instrument|Microscope|')
            ##Find the all instances of microscope
            #if mic_list:
                #mic_id =  max(map(int, mic_list))+1
            #else:
                #mic_id = 1            
        #self.mic_id = mic_id
        ## Attach the scrolling option with the panel
        #self.sw = wx.ScrolledWindow(self)
        ## Attach a flexi sizer for the text controler and labels
        #fgs = wx.FlexGridSizer(rows=30, cols=5, hgap=5, vgap=5)
        
        ##----------- Microscope -------        
        #heading = 'Microscope'
        #text = wx.StaticText(self.sw, -1, heading)
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #microtypTAG = 'Instrument|Microscope|Type|'+str(self.mic_id)
        #self.settings_controls[microtypTAG] = wx.Choice(self.sw, -1,  choices=['WideField','LaserScanningMicroscopy', 'LaserScanningConfocal', 'SpinningDiskConfocal', 'SlitScanConfocal', 'MultiPhotonMicroscopy', 'StructuredIllumination','SingleMoleculeImaging', 'TotalInternalReflection', 'FluorescenceLifetime', 'SpectralImaging', 'FluorescenceCorrelationSpectroscopy', 'NearFieldScanningOpticalMicroscopy', 'SecondHarmonicGenerationImaging', 'Timelapse', 'Other'])
        #if meta.get_field(microtypTAG) is not None:
            #self.settings_controls[microtypTAG].SetStringSelection(meta.get_field(microtypTAG))
        #self.settings_controls[microtypTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        #self.settings_controls[microtypTAG].SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Microscope Type'), 0)
        #fgs.Add(self.settings_controls[microtypTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
    
        #micromfgTAG = 'Instrument|Microscope|Manufacter|'+str(self.mic_id)
        #self.settings_controls[micromfgTAG] = wx.Choice(self.sw, -1,  choices=['Zeiss','Olympus','Nikon', 'MDS', 'GE'])
        #if meta.get_field(micromfgTAG) is not None:
            #self.settings_controls[micromfgTAG].SetStringSelection(meta.get_field(micromfgTAG))
        #self.settings_controls[micromfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)    
        #self.settings_controls[micromfgTAG].SetToolTipString('Modification')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        #fgs.Add(self.settings_controls[micromfgTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
      
        #micromdlTAG = 'Instrument|Microscope|Model|'+str(self.mic_id)
        #self.settings_controls[micromdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(micromdlTAG, default=''))
        #self.settings_controls[micromdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[micromdlTAG].SetToolTipString('Model number of the microscope')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        #fgs.Add(self.settings_controls[micromdlTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
     
        #microorntTAG = 'Instrument|Microscope|Orientation |'+str(self.mic_id)
        #self.settings_controls[microorntTAG] = wx.Choice(self.sw, -1,  choices=['Upright', 'Inverted', 'Confocal'])
        #if meta.get_field(microorntTAG) is not None:
            #self.settings_controls[microorntTAG].SetStringSelection(meta.get_field(microorntTAG))
        #self.settings_controls[microorntTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        #self.settings_controls[microorntTAG].SetToolTipString('Orientation of the microscope in relation to the sample')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Orientation'), 0)
        #fgs.Add(self.settings_controls[microorntTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        ##----------- Light -------        
        #text = wx.StaticText(self.sw, -1, 'Light')
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
   
        #microlgtTAG = 'Instrument|Microscope|LightSource|'+str(self.mic_id)
        #self.settings_controls[microlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Filament', 'Arc', 'LightEmittingDiode'])
        #if meta.get_field(microlgtTAG) is not None:
            #self.settings_controls[microlgtTAG].SetStringSelection(meta.get_field(microlgtTAG))
        #self.settings_controls[microlgtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        #self.settings_controls[microlgtTAG].SetToolTipString('e.g. Laser, Filament, Arc, Light Emitting Diode')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        #fgs.Add(self.settings_controls[microlgtTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
      
        #microIllTAG = 'Instrument|Microscope|IllumType|'+str(self.mic_id)
        #self.settings_controls[microIllTAG] = wx.Choice(self.sw, -1,  choices=['Transmitted','Epifluorescence','Oblique','NonLinear'])
        #if meta.get_field(microIllTAG) is not None:
            #self.settings_controls[microIllTAG].SetStringSelection(meta.get_field(microIllTAG))
        #self.settings_controls[microIllTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        #self.settings_controls[microIllTAG].SetToolTipString('Type of illumunation used')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Illumination Type'), 0)
        #fgs.Add(self.settings_controls[microIllTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        
        ##----------- Filter -------        
        #text = wx.StaticText(self.sw, -1, 'Filter')
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microfltacroTAG = 'Instrument|Microscope|FilterAcro|'+str(self.mic_id)
        #self.settings_controls[microfltacroTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microfltacroTAG, default=''))
        #self.settings_controls[microfltacroTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microfltacroTAG].SetToolTipString('Acroname of the filter e.g. DAPI, GFP')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Filter Acronym'), 0)
        #fgs.Add(self.settings_controls[microfltacroTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #font = wx.Font(11, wx.ROMAN, wx.NORMAL, wx.BOLD)
        #excitation = wx.StaticText(self.sw, -1, 'Excitation')
        #dichroic = wx.StaticText(self.sw, -1, 'Dichroic')
        #emission = wx.StaticText(self.sw, -1, 'Emission')
        #excitation.SetFont(font)
        #dichroic.SetFont(font)
        #emission.SetFont(font)
        
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(excitation, 0)
        #fgs.Add(dichroic, 0)
        #fgs.Add(emission, 0)
        
        #microExtMFGTAG = 'Instrument|Microscope|ExtMFG|'+str(self.mic_id)
        #self.settings_controls[microExtMFGTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtMFGTAG, default=''))
        #self.settings_controls[microExtMFGTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtMFGTAG].SetToolTipString('Manufacturer name of the excitation filter')
        #microDchMFGTAG = 'Instrument|Microscope|DchMFG|'+str(self.mic_id)
        #self.settings_controls[microDchMFGTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchMFGTAG, default=''))
        #self.settings_controls[microDchMFGTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchMFGTAG].SetToolTipString('Manufacturer name of the dichroic filter')
        #microEmsMFGTAG = 'Instrument|Microscope|EmsMFG|'+str(self.mic_id)
        #self.settings_controls[microEmsMFGTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsMFGTAG, default=''))
        #self.settings_controls[microEmsMFGTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsMFGTAG].SetToolTipString('Manufacturer name of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        #fgs.Add(self.settings_controls[microExtMFGTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchMFGTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsMFGTAG], 0, wx.EXPAND)
        
        #microExtMDLTAG = 'Instrument|Microscope|ExtMDL|'+str(self.mic_id)
        #self.settings_controls[microExtMDLTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtMDLTAG, default=''))
        #self.settings_controls[microExtMDLTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtMDLTAG].SetToolTipString('Model name of the excitation filter')
        #microDchMDLTAG = 'Instrument|Microscope|DchMDL|'+str(self.mic_id)
        #self.settings_controls[microDchMDLTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchMDLTAG, default=''))
        #self.settings_controls[microDchMDLTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchMDLTAG].SetToolTipString('Model name of the dichroic filter')
        #microEmsMDLTAG = 'Instrument|Microscope|EmsMDL|'+str(self.mic_id)
        #self.settings_controls[microEmsMDLTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsMDLTAG, default=''))
        #self.settings_controls[microEmsMDLTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsMDLTAG].SetToolTipString('Model name of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        #fgs.Add(self.settings_controls[microExtMDLTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchMDLTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsMDLTAG], 0, wx.EXPAND)
        
        #microExtLOTTAG = 'Instrument|Microscope|ExtLOT|'+str(self.mic_id)
        #self.settings_controls[microExtLOTTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtLOTTAG, default=''))
        #self.settings_controls[microExtLOTTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtLOTTAG].SetToolTipString('Lot Number of the excitation filter')
        #microDchLOTTAG = 'Instrument|Microscope|DchLOT|'+str(self.mic_id)
        #self.settings_controls[microDchLOTTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchLOTTAG, default=''))
        #self.settings_controls[microDchLOTTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchLOTTAG].SetToolTipString('Lot Number of the dichroic filter')
        #microEmsLOTTAG = 'Instrument|Microscope|EmsLOT|'+str(self.mic_id)
        #self.settings_controls[microEmsLOTTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsLOTTAG, default=''))
        #self.settings_controls[microEmsLOTTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsLOTTAG].SetToolTipString('Lot Number name of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, 'Lot Number'), 0)
        #fgs.Add(self.settings_controls[microExtLOTTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchLOTTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsLOTTAG], 0, wx.EXPAND)
        
        #microExtTYPTAG = 'Instrument|Microscope|ExtTYP|'+str(self.mic_id)
        #self.settings_controls[microExtTYPTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtTYPTAG, default=''))
        #self.settings_controls[microExtTYPTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtTYPTAG].SetToolTipString('WVEation filter')
        #microDchTYPTAG = 'Instrument|Microscope|DchTYP|'+str(self.mic_id)
        #self.settings_controls[microDchTYPTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchTYPTAG, default=''))
        #self.settings_controls[microDchTYPTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchTYPTAG].SetToolTipString('Type of the dichroic filter')
        #microEmsTYPTAG = 'Instrument|Microscope|EmsTYP|'+str(self.mic_id)
        #self.settings_controls[microEmsTYPTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsTYPTAG, default=''))
        #self.settings_controls[microEmsTYPTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsTYPTAG].SetToolTipString('Type of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)        
        #fgs.Add(wx.StaticText(self.sw, -1, 'Type'), 0)
        #fgs.Add(self.settings_controls[microExtTYPTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchTYPTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsTYPTAG], 0, wx.EXPAND)
        
        #microExtWVETAG = 'Instrument|Microscope|ExtWVE|'+str(self.mic_id)
        #self.settings_controls[microExtWVETAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtWVETAG, default=''))
        #self.settings_controls[microExtWVETAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtWVETAG].SetToolTipString('HMXe excitation filter')
        #microDchWVETAG = 'Instrument|Microscope|DchWVE|'+str(self.mic_id)
        #self.settings_controls[microDchWVETAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchWVETAG, default=''))
        #self.settings_controls[microDchWVETAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchWVETAG].SetToolTipString('Wave length of the dichroic filter')
        #microEmsWVETAG = 'Instrument|Microscope|EmsWVE|'+str(self.mic_id)
        #self.settings_controls[microEmsWVETAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsWVETAG, default=''))
        #self.settings_controls[microEmsWVETAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsWVETAG].SetToolTipString('Wave length of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, 'Wave Length'), 0)
        #fgs.Add(self.settings_controls[microExtWVETAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchWVETAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsWVETAG], 0, wx.EXPAND)
        
        #microExtHMXTAG = 'Instrument|Microscope|ExtHMX|'+str(self.mic_id)
        #self.settings_controls[microExtHMXTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtHMXTAG, default=''))
        #self.settings_controls[microExtHMXTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtHMXTAG].SetToolTipString('Spectral width at half max of the excitation filter')
        #microDchHMXTAG = 'Instrument|Microscope|DchHMX|'+str(self.mic_id)
        #self.settings_controls[microDchHMXTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchHMXTAG, default=''))
        #self.settings_controls[microDchHMXTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchHMXTAG].SetToolTipString('Spectral width at half max of the dichroic filter')
        #microEmsHMXTAG = 'Instrument|Microscope|EmsHMX|'+str(self.mic_id)
        #self.settings_controls[microEmsHMXTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsHMXTAG, default=''))
        #self.settings_controls[microEmsHMXTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsHMXTAG].SetToolTipString('Spectral width at half max of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, 'Spectral Width at Half Max'), 0)
        #fgs.Add(self.settings_controls[microExtHMXTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchHMXTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsHMXTAG], 0, wx.EXPAND)
        
        #microExtMDFTAG = 'Instrument|Microscope|ExtMDF|'+str(self.mic_id)
        #self.settings_controls[microExtMDFTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microExtMDFTAG, default=''))
        #self.settings_controls[microExtMDFTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microExtMDFTAG].SetToolTipString('Modification of the excitation filter')
        #microDchMDFTAG = 'Instrument|Microscope|DchMDF|'+str(self.mic_id)
        #self.settings_controls[microDchMDFTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microDchMDFTAG, default=''))
        #self.settings_controls[microDchMDFTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microDchMDFTAG].SetToolTipString('Modification of the dichroic filter')
        #microEmsMDFTAG = 'Instrument|Microscope|EmsMDF|'+str(self.mic_id)
        #self.settings_controls[microEmsMDFTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microEmsMDFTAG, default=''))
        #self.settings_controls[microEmsMDFTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microEmsMDFTAG].SetToolTipString('Modification of the emission filter')
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, 'Custom Modification'), 0)
        #fgs.Add(self.settings_controls[microExtMDFTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microDchMDFTAG], 0, wx.EXPAND)
        #fgs.Add(self.settings_controls[microEmsMDFTAG], 0, wx.EXPAND)
        
        ##----------- Lenses -------        
        #text = wx.StaticText(self.sw, -1, 'Lens')
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
                
        #LensMfgTAG = 'Instrument|Microscope|LensMFG|'+str(self.mic_id)
        #self.settings_controls[LensMfgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(LensMfgTAG, default=''))
        #self.settings_controls[LensMfgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[LensMfgTAG].SetToolTipString('Manufacturer of lense')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        #fgs.Add(self.settings_controls[LensMfgTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #LensMdlTAG = 'Instrument|Microscope|LensMDL|'+str(self.mic_id)
        #self.settings_controls[LensMdlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(LensMdlTAG, default=''))
        #self.settings_controls[LensMdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[LensMdlTAG].SetToolTipString('Model of the lens')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        #fgs.Add(self.settings_controls[LensMdlTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microOnaTAG = 'Instrument|Microscope|ObjectiveNA|'+str(self.mic_id)
        #self.settings_controls[microOnaTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microOnaTAG, default=''))
        #self.settings_controls[microOnaTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microOnaTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Objective NA'), 0)
        #fgs.Add(self.settings_controls[microOnaTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microlnsappTAG = 'Instrument|Microscope|LensApprture|'+str(self.mic_id)
        #self.settings_controls[microlnsappTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microlnsappTAG, default=''))
        #self.settings_controls[microlnsappTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microlnsappTAG].SetToolTipString('A floating value of lens numerical aperture')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Aperture'), 0)
        #fgs.Add(self.settings_controls[microlnsappTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microImmTAG = 'Instrument|Microscope|Immersion|'+str(self.mic_id)
        #self.settings_controls[microImmTAG] = wx.Choice(self.sw, -1,  choices=['Oil', 'Water', 'WaterDipping', 'Air', 'Multi', 'Glycerol', 'Other', 'Unkonwn'])
        #if meta.get_field(microImmTAG) is not None:
            #self.settings_controls[microImmTAG].SetStringSelection(meta.get_field(microImmTAG))
        #self.settings_controls[microImmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        #self.settings_controls[microImmTAG].SetToolTipString('Immersion medium used')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
        #fgs.Add(self.settings_controls[microImmTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
    
        #microCorrTAG = 'Instrument|Microscope|Correction|'+str(self.mic_id)
        #self.settings_controls[microCorrTAG] = wx.Choice(self.sw, -1,  choices=['UV', 'PlanApo', 'PlanFluor', 'SuperFluor', 'VioletCorrected', 'Unknown'])
        #if meta.get_field(microCorrTAG) is not None:
            #self.settings_controls[microCorrTAG].SetStringSelection(meta.get_field(microCorrTAG))
        #self.settings_controls[microCorrTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        #self.settings_controls[microCorrTAG].SetToolTipString('Lense correction used')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
        #fgs.Add(self.settings_controls[microCorrTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microObjTAG = 'Instrument|Microscope|ObjectiveMagnification|'+str(self.mic_id)
        #self.settings_controls[microObjTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microObjTAG, default=''))
        #self.settings_controls[microObjTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microObjTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Objective Magnification'), 0)
        #fgs.Add(self.settings_controls[microObjTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
      
        #microNmgTAG = 'Instrument|Microscope|NominalMagnification|'+str(self.mic_id)
        #self.settings_controls[microNmgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microNmgTAG, default=''))
        #self.settings_controls[microNmgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microNmgTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
        #fgs.Add(self.settings_controls[microNmgTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
 
        #microCalTAG = 'Instrument|Microscope|CalibratedMagnification|'+str(self.mic_id)
        #self.settings_controls[microCalTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCalTAG, default=''))
        #self.settings_controls[microCalTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microCalTAG].SetToolTipString('The magnification of the lens as measured by a calibration process- i.e. 59.987 for a 60X lens')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
        #fgs.Add(self.settings_controls[microCalTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
 
        #microWrkTAG = 'Instrument|Microscope|WorkDistance|'+str(self.mic_id)
        #self.settings_controls[microWrkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microWrkTAG, default=''))
        #self.settings_controls[microWrkTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microWrkTAG].SetToolTipString('The working distance of the lens expressed as a floating point (real) number. Units are um')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Working Distance (uM)'), 0)
        #fgs.Add(self.settings_controls[microWrkTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        
        ##----------- Detector -------        
        #text = wx.StaticText(self.sw, -1, 'Detector')
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microdctTAG = 'Instrument|Microscope|Detector|'+str(self.mic_id)
        #self.settings_controls[microdctTAG] = wx.Choice(self.sw, -1,  choices=['CCD', 'Intensified-CCD', 'Analog-Video', 'Spectroscopy', 'Life-time-imaging', 'Correlation-Spectroscopy', 'FTIR', 'EM-CCD', 'APD', 'CMOS'])
        #if meta.get_field(microdctTAG) is not None:
            #self.settings_controls[microdctTAG].SetStringSelection(meta.get_field(microdctTAG))
        #self.settings_controls[microdctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        #self.settings_controls[microdctTAG].SetToolTipString('Type of detector used')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Detector'), 0)
        #fgs.Add(self.settings_controls[microdctTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #dectMfgTAG = 'Instrument|Microscope|DetectorMFG|'+str(self.mic_id)
        #self.settings_controls[dectMfgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(dectMfgTAG, default=''))
        #self.settings_controls[dectMfgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[dectMfgTAG].SetToolTipString('Manufacturer of detector')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        #fgs.Add(self.settings_controls[dectMfgTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #dectMdlTAG = 'Instrument|Microscope|DetectorMDL|'+str(self.mic_id)
        #self.settings_controls[dectMdlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(dectMdlTAG, default=''))
        #self.settings_controls[dectMdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[dectMdlTAG].SetToolTipString('Model of the detector')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        #fgs.Add(self.settings_controls[dectMdlTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #dectGainTAG = 'Instrument|Microscope|DetectorGain|'+str(self.mic_id)
        #self.settings_controls[dectGainTAG] = wx.TextCtrl(self.sw, value=meta.get_field(dectGainTAG, default=''))
        #self.settings_controls[dectGainTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[dectGainTAG].SetToolTipString('Gain in the detector')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Gain'), 0)
        #fgs.Add(self.settings_controls[dectGainTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #dectOffTAG = 'Instrument|Microscope|DetectorOff|'+str(self.mic_id)
        #self.settings_controls[dectOffTAG] = wx.TextCtrl(self.sw, value=meta.get_field(dectOffTAG, default=''))
        #self.settings_controls[dectOffTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[dectOffTAG].SetToolTipString('Offset of the detector')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Offset'), 0)
        #fgs.Add(self.settings_controls[dectOffTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #dectExpTAG = 'Instrument|Microscope|DetectorEXP|'+str(self.mic_id)
        #self.settings_controls[dectExpTAG] = wx.TextCtrl(self.sw, value=meta.get_field(dectExpTAG, default=''))
        #self.settings_controls[dectExpTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[dectExpTAG].SetToolTipString('Exposure time of the detector')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Exposure Time'), 0)
        #fgs.Add(self.settings_controls[dectExpTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #dectBinTAG = 'Instrument|Microscope|DetectorBin|'+str(self.mic_id)
        #self.settings_controls[dectBinTAG] = wx.TextCtrl(self.sw, value=meta.get_field(dectBinTAG, default=''))
        #self.settings_controls[dectBinTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[dectBinTAG].SetToolTipString('Binning of the detector')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Binning'), 0)
        #fgs.Add(self.settings_controls[dectBinTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
   
        ##----------- Software -------        
        #text = wx.StaticText(self.sw, -1, 'Software')
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microSoftTAG = 'Instrument|Microscope|Software|'+str(self.mic_id)
        #self.settings_controls[microSoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microSoftTAG, default=''))
        #self.settings_controls[microSoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microSoftTAG].SetToolTipString('Name and version of software used for data acquisition')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Software Name and version'), 0)
        #fgs.Add(self.settings_controls[microSoftTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        
        ##-- Incubator --#
        #heading = 'Incubator'
        #text = wx.StaticText(self.sw, -1, heading)
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #text.SetFont(font)
        #fgs.Add(text, 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
       
        #microTempTAG = 'Instrument|Microscope|Temp|'+str(self.mic_id)
        #self.settings_controls[microTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microTempTAG, default=''))
        #self.settings_controls[microTempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microTempTAG].SetToolTipString('Temperature of the incubator')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
        #fgs.Add(self.settings_controls[microTempTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
       
        #microCarbonTAG = 'Instrument|Microscope|C02|'+str(self.mic_id)
        #self.settings_controls[microCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCarbonTAG, default=''))
        #self.settings_controls[microCarbonTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
        #fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
        #fgs.Add(self.settings_controls[microCarbonTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        #microHumTAG = 'Instrument|Microscope|Humidity|'+str(self.mic_id)
        #self.settings_controls[microHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microHumTAG, default=''))
        #self.settings_controls[microHumTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microHumTAG].SetToolTipString('Humidity at the incubator')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
        #fgs.Add(self.settings_controls[microHumTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
       
        #microPressTAG = 'Instrument|Microscope|Pressure|'+str(self.mic_id)
        #self.settings_controls[microPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microPressTAG, default=''))
        #self.settings_controls[microPressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        #self.settings_controls[microPressTAG].SetToolTipString('Pressure at the incubator')
        #fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
        #fgs.Add(self.settings_controls[microPressTAG], 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        ##-- button --#
        #self.copyMicroscopePageBtn = wx.Button(self.sw, -1, label="Duplicate Settings")
        #self.copyMicroscopePageBtn.Bind(wx.EVT_BUTTON, self.onCopyMicroscopePage)
        
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(self.copyMicroscopePageBtn, 0, wx.EXPAND)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

      
        #self.sw.SetSizer(fgs)
        #self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
        #self.Sizer = wx.BoxSizer(wx.VERTICAL)
        #self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
    
    #def onCopyMicroscopePage(self, event):
      
        #meta = ExperimentSettings.getInstance()
        ##Get the maximum microscope id from the list
        #mic_list = meta.get_field_instances('Instrument|Microscope|')
        
        #if not mic_list:
            #dial = wx.MessageDialog(None, 'No instance to duplicate', 'Error', wx.OK | wx.ICON_ERROR)
            #dial.ShowModal()  
            #return
                    
        #new_mic_id =  max(map(int, mic_list))+1
        
        #tag_list =  meta.get_field_tags('Instrument|Microscope', str(self.mic_id))
        
        #for tag in tag_list:
            #newtag = '%s|%s'%(get_tag_stump(tag), str(new_mic_id))
            #meta.set_field( newtag,  meta.get_field(tag))
            
        #panel = MicroscopePanel(self.Parent, new_mic_id)
        #self.Parent.AddPage(panel, 'Microscope: %s'% new_mic_id)
        
        
    #def OnSavingData(self, event):
        #meta = ExperimentSettings.getInstance()
        
        #ctrl = event.GetEventObject()
        #tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        #if isinstance(ctrl, wx.Choice):
            #meta.set_field(tag, ctrl.GetStringSelection())
        #else:
            #meta.set_field(tag, ctrl.GetValue())
            

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
	meta = ExperimentSettings.getInstance()
        self.settings_controls = {}
	self.protocol = 'Instrument|Flowcytometer'
       
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        
        ## Get all the previously encoded Flowcytometer pages and re-Add them as pages
        flow_list = sorted(meta.get_field_instances(self.protocol))
        
        self.next_page_num = 1
               # update the  number of existing cell loading
        if flow_list: 
            self.next_page_num  =  int(flow_list[-1])+1   
	    for flow_id in sorted(flow_list):
		panel = FlowcytometerPanel(self.notebook, flow_id)
		self.notebook.AddPage(panel, 'Flowcytometer No: %s'% flow_id, True)
            
        self.addFlowcytometerPageBtn = wx.Button(self, label="Add Flowcytometer Settings")
        self.addFlowcytometerPageBtn.Bind(wx.EVT_BUTTON, self.onAddFlowcytometerPage)
        #self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.onTabClosing)
	
        self.loadFlowcytometerPageBtn = wx.Button(self, label="Load Flowcytometer Settings")
        self.loadFlowcytometerPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSettings)        
	

        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(self.addFlowcytometerPageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(self.loadFlowcytometerPageBtn, 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
    
    #def onTabClosing(self, event):
        #meta = ExperimentSettings.getInstance()
        ##first check whether this is the only instnace then it cant be deleted
        #flow_list = meta.get_field_instances('Instrument|Flowcytometer|')
        
        #if len(flow_list) == 1:
            #event.Veto()
            #dlg = wx.MessageDialog(self, 'Can not delete the only instance', 'Deleting..', wx.OK| wx.ICON_STOP)
            #dlg.ShowModal()
            #return
        
        #tab_caption =  self.notebook.GetPageText(event.GetSelection())
        #self.flow_id = tab_caption.split(':')[1].strip()
        
        #dlg = wx.MessageDialog(self, 'Deleting Flowcytometer no %s' %self.flow_id, 'Deleting..', wx.OK | wx.ICON_WARNING)
        #if dlg.ShowModal() == wx.ID_OK:  
            #meta.remove_field('Instrument|Flowcytometer|Manufacter|%s'%str(self.flow_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Flowcytometer|Model|%s'%str(self.flow_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Flowcytometer|Type|%s'%str(self.flow_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Flowcytometer|LightSource|%s'%str(self.flow_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Flowcytometer|Detector|%s'%str(self.flow_id), notify_subscribers =False)
            #meta.remove_field('Instrument|Flowcytometer|Filter|%s'%str(self.flow_id))

        
    def onAddFlowcytometerPage(self, event):
        # This button is active only at the first instance
        panel = FlowcytometerPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Flowcytometer No: %s'% self.next_page_num, True)        
        #Disable the add button
        self.next_page_num +=1
	
    def onLoadSettings(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your instrument settings...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_flowcytometer_settings(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = FlowcytometerPanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Flowcytometer No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1	            

class FlowcytometerPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent)
	
	self.protocol = 'Instrument|Flowcytometer'
 
        self.page_counter = page_counter
  
        self.sw = wx.ScrolledWindow(self)
	self.fgs = wx.FlexGridSizer(rows=30, cols=30, hgap=5, vgap=5)
	
	#-- Show previously encoded channels --#
	self.showChannels()
        
        #-- Sizers --#
	self.sw.SetSizer(self.fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 20)
        self.Show()           

    def onAddChnnel(self, event):
	meta = ExperimentSettings.getInstance() 
	self.dlg = ChannelBuilder(self.sw, -1, 'Channel Builder')
	
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
	
	#----------- Microscope Labels and Text Controler-------        
	#--- Save Settings (TO DO)---#
	self.saveSettings = wx.Button(self.sw, -1, 'Save Settings')
	self.saveSettings.Bind(wx.EVT_BUTTON, self.onSavingSettings)
	self.fgs.Add(self.saveSettings, 0)	
	#---Add Channel--#
	self.addCh = wx.Button(self.sw, 1, '+ Add Channel')
	self.addCh.Bind(wx.EVT_BUTTON, self.onAddChnnel) 
	self.fgs.Add(self.addCh, 0)	
	for gap in range(3, 31): #because there are 30 cols in fgs max number of componensts it can hold
	    self.fgs.Add(wx.StaticText(self.sw, -1, ''), 0)	
	#--Manufacture--#
	flowmfgTAG = 'Instrument|Flowcytometer|Manufacter|'+str(self.page_counter)
	self.settings_controls[flowmfgTAG] = wx.Choice(self.sw, -1,  choices=['Beckman','BD-Biosciences'])
	if meta.get_field(flowmfgTAG) is not None:
	    self.settings_controls[flowmfgTAG].SetStringSelection(meta.get_field(flowmfgTAG))
	self.settings_controls[flowmfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[flowmfgTAG].SetToolTipString('Manufacturer name')
	self.fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	self.fgs.Add(self.settings_controls[flowmfgTAG], 0, wx.EXPAND)
	for gap in range(3, 31): 
	    self.fgs.Add(wx.StaticText(self.sw, -1, ''), 0)	
	#--Model--#
	flowmdlTAG = 'Instrument|Flowcytometer|Model|'+str(self.page_counter)
	self.settings_controls[flowmdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(flowmdlTAG, default=''))
	self.settings_controls[flowmdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[flowmdlTAG].SetToolTipString('Model number of the Flowcytometer')
	self.fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	self.fgs.Add(self.settings_controls[flowmdlTAG], 0, wx.EXPAND)
	for gap in range(3, 31): 
	    self.fgs.Add(wx.StaticText(self.sw, -1, ''), 0)	
	for gap in range(1, 31): 
	    self.fgs.Add(wx.StaticText(self.sw, -1, ''), 0)	
		
	#if status is 'Load':
	    #self.addCh.Hide()
	    #self.saveSettings.Hide()
	self.sw.SetSizer(self.fgs)
	self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 20)	
			    
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
	self.fgs.Add(wx.StaticText(self.sw, -1, chName), 0)
	
	# Add the components
	for component in lightpath:
	    compName = component[0]
	    nmRange = component[1]
	    
	    if compName.startswith('LSR'):
		staticbox = wx.StaticBox(self.sw, -1, "Excitation Laser")
		laserNM = int(compName.split('LSR')[1])
		
		self.laser = wx.TextCtrl(self.sw, -1, str(laserNM), style=wx.TE_READONLY)
		self.laser.SetBackgroundColour(meta.nmToRGB(laserNM))
		
		laserSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		laserSizer.Add(self.laser, 0) 	    
		self.fgs.Add(laserSizer,  0)
	    
	    if compName.startswith('DMR') or compName.startswith('FLT') or compName.startswith('SLT'):
		staticbox = wx.StaticBox(self.sw, -1, compName)
		
		self.startNM, self.endNM = meta.getNM(nmRange)
		self.spectralRange =  meta.partition(range(self.startNM, self.endNM+1), 5)

		self.spectrum = DrawSpectrum(self.sw, self.startNM, self.endNM)
		
		mirrorSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		mirrorSizer.Add(self.spectrum, 0)
		self.fgs.Add(mirrorSizer, 0)
		
	    if compName.startswith('DYE'):
		staticbox = wx.StaticBox(self.sw, -1, 'DYE')
		dye = compName.split('_')[1]
		emLow, emHgh = meta.getNM(nmRange)
		dyeList = meta.setDyeList(emLow, emHgh)
		if dye not in dyeList:
		    dyeList.append(dye) 
		dyeList.append('Add Dye by double click')
		
		self.dyeListBox = wx.ListBox(self.sw, -1, wx.DefaultPosition, (150, 50), dyeList, wx.LB_SINGLE)
		self.dyeListBox.SetStringSelection(dye)
		self.dyeListBox.Bind(wx.EVT_LISTBOX, partial(self.onEditDye, ch = chName, compNo = lightpath.index(component), opticalpath = lightpath))
		self.dyeListBox.Bind(wx.EVT_LISTBOX_DCLICK, partial(self.onMyDyeSelect, ch = chName, compNo = lightpath.index(component), opticalpath = lightpath))
		
		dye_sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		dye_sizer.Add(self.dyeListBox, 0)               
		self.fgs.Add(dye_sizer, 0) 	    		
		
		
	    if compName.startswith('DTC'):
		staticbox = wx.StaticBox(self.sw, -1, "Detector")
		volt = int(compName.split('DTC')[1])
		
	
		self.detector = wx.SpinCtrl(self.sw, -1, "", (30, 50))
		self.detector.SetRange(1,1000)
		self.detector.SetValue(volt)
		
		self.detector.Bind(wx.EVT_SPINCTRL, partial(self.onEditDetector, ch = chName, compNo = lightpath.index(component), opticalpath = lightpath))
			 		
		detector_sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		detector_sizer.Add(self.detector, 0)
		self.fgs.Add(detector_sizer, 0)
		

		#pmtSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
		#pmtSizer.Add(wx.StaticText(self.sw, -1, volt+' Volts'))
		#self.fgs.Add(pmtSizer, 0)
		
	
	##set the delete button at the end
	self.delete_button = wx.Button(self.sw, wx.ID_DELETE)
	self.delete_button.Bind(wx.EVT_BUTTON, partial(self.onDeleteCh, cn = chName))
	self.fgs.Add(self.delete_button, 0, wx.EXPAND|wx.ALL, 10)
	# Fill up the gap	
	for gap in range(len(lightpath)+3, 31): #because there are 30 cols in fgs max number of componensts it can hold
	    self.fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
		
	self.sw.SetSizer(self.fgs)
	self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 20)	
	
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
	self.fgs.Clear(deleteWindows=True)
	self.showChannels()
	
    def onSavingSettings(self, event):
	# also check whether the description field has been filled by users
	meta = ExperimentSettings.getInstance()
	
	# TO DO: check whehter make and model field being filled up 
	# Also check whether there is atleast one channel optical path being filled
	#steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Spin|Step', str(self.page_counter)), key = meta.stringSplitByNumbers)
	#for step in steps:
	    #step_info = meta.get_field('AddProcess|Spin|%s|%s' %(step, str(self.page_counter)))
	    #if not step_info[0]:
		#dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		#dial.ShowModal()  
		#return	
    
	#if not meta.get_field('AddProcess|Spin|ProtocolName|%s'%str(self.page_counter)):
	    #dial = wx.MessageDialog(None, 'Please type a name for the supplementary protocol', 'Error', wx.OK | wx.ICON_ERROR)
	    #dial.ShowModal()  
	    #return	
		
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
	    
	    print self.page_counter
	    
	    attributes = meta.get_attribute_list_by_instance('Instrument|Flowcytometer', str(self.page_counter))
	    print attributes
	    for attr in attributes:
		info = meta.get_field('Instrument|Flowcytometer|%s|%s' %(attr, self.page_counter))
		if isinstance(info, list):
		    f.write(attr+'='+str(info)+'\n')
		else:
		    f.write(attr+'='+info+'\n')
	    f.close()	    
		    
	 
	
	
	
	
	
    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()      

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
            ctrl.SetToolTipString(str(ctrl.GetValue()))

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
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        cellload_list = sorted(meta.get_field_instances('CellTransfer|Seed|'))
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
        cellload_list = sorted(meta.get_field_instances('CellTransfer|Seed|'))
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
        chemical_list = sorted(meta.get_field_instances('Perturbation|Chem|'))
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
        bio_list = sorted(meta.get_field_instances('Perturbation|Bio|'))
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
class ImmunoSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
	
	self.protocol = 'Staining|Immuno'

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
        for protocol_id in supp_protocol_list:
            panel = ImmunoPanel(self.notebook, int(protocol_id))
            self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Staining Protocol")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Staining Protocol")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = ImmunoPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Staining Protocol No: %s'%str(self.next_page_num), True)
        self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
        meta = ExperimentSettings.getInstance()
        
        dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        # read the supp protocol file
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	# set the panel accordingly    
	panel = ImmunoPanel(self.notebook, self.next_page_num)
	self.notebook.AddPage(panel, 'Staining Protocol No: %s'%str(self.next_page_num), True)
	self.next_page_num += 1	


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
	self.settings_controls[primaryantiTAG+'|0']= wx.Choice(self.top_panel, -1, choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
	if len(primaryanti) > 0:
	    self.settings_controls[primaryantiTAG+'|0'].SetStringSelection(primaryanti[0])
	self.settings_controls[primaryantiTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[primaryantiTAG+'|0'].SetToolTipString('Primary source species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Primary Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[primaryantiTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[primaryantiTAG+'|1'] = wx.TextCtrl(self.top_panel, value='') 
	if len(primaryanti)> 1:
	    self.settings_controls[primaryantiTAG+'|1'].SetValue(primaryanti[1])
	self.settings_controls[primaryantiTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[primaryantiTAG+'|1'].SetToolTipString('Solvent')
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Solvent'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[primaryantiTAG+'|1'], 0, wx.EXPAND)	
	
	# Secondary source and associated solvent
	scndantiTAG = 'Staining|Immuno|Secondary|'+str(self.page_counter)
	scndanti = meta.get_field(scndantiTAG, [])
	self.settings_controls[scndantiTAG+'|0']= wx.Choice(self.top_panel, -1, choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
	if len(scndanti) > 0:
	    self.settings_controls[scndantiTAG+'|0'].SetStringSelection(scndanti[0])
	self.settings_controls[scndantiTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[scndantiTAG+'|0'].SetToolTipString('Secondary source species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Secondary Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[scndantiTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[scndantiTAG+'|1'] = wx.TextCtrl(self.top_panel, value='') 
	if len(scndanti)> 1:
	    self.settings_controls[scndantiTAG+'|1'].SetValue(scndanti[1])
	self.settings_controls[scndantiTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[scndantiTAG+'|1'].SetToolTipString('Solvent')
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Solvent'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[scndantiTAG+'|1'], 0, wx.EXPAND)	
	
	# Tertiary source and associated solvent
	tertantiTAG = 'Staining|Immuno|Tertiary|'+str(self.page_counter)
	tertanti = meta.get_field(tertantiTAG, [])
	self.settings_controls[tertantiTAG+'|0']= wx.Choice(self.top_panel, -1, choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
	if len(tertanti) > 0:
	    self.settings_controls[tertantiTAG+'|0'].SetStringSelection(tertanti[0])
	self.settings_controls[tertantiTAG+'|0'].Bind(wx.EVT_CHOICE, self.OnSavingData)   
	self.settings_controls[tertantiTAG+'|0'].SetToolTipString('Tertiary source species') 
	fgs.Add(wx.StaticText(self.top_panel, -1, 'Tertiary Antibody'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	fgs.Add(self.settings_controls[tertantiTAG+'|0'], 0, wx.EXPAND)
	
	self.settings_controls[tertantiTAG+'|1'] = wx.TextCtrl(self.top_panel, value='') 
	if len(tertanti)> 1:
	    self.settings_controls[tertantiTAG+'|1'].SetValue(tertanti[1])
	self.settings_controls[tertantiTAG+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls[tertantiTAG+'|1'].SetToolTipString('Solvent')
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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	 
    
########################################################################        
################## PRIMER SETTING PANEL    ###########################
########################################################################
class GeneticSettingPanel(wx.Panel):
    """
     Panel that holds parameter input panel and the buttons for more additional panel
     """
    def __init__(self, parent, id=-1):
	"""Constructor"""
	wx.Panel.__init__(self, parent, id)

	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
	self.protocol = 'Staining|Genetic'

	self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
	# Get all the previously encoded Microscope pages and re-Add them as pages
	supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
	self.next_page_num = 1
	# update the  number of existing cell loading
	if supp_protocol_list: 
	    self.next_page_num  =  int(supp_protocol_list[-1])+1
	for protocol_id in supp_protocol_list:
	    panel = GeneticPanel(self.notebook, int(protocol_id))
	    self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(protocol_id), True)

	# Add the buttons
	addPageBtn = wx.Button(self, label="Add Staining Protocol")
	addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
	
	loadPageBtn = wx.Button(self, label="Load Staining Protocol")
	loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

	# create some sizers
	sizer = wx.BoxSizer(wx.VERTICAL)
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)

	# layout the widgets
	sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
	btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

	sizer.Add(btnSizer)
	self.SetSizer(sizer)
	self.Layout()
	self.Show()

    def onAddPage(self, event):
	panel = GeneticPanel(self.notebook, self.next_page_num)
	self.notebook.AddPage(panel, 'Staining Protocol No: %s'%str(self.next_page_num), True)
	self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	# set the panel accordingly    
	panel = GeneticPanel(self.notebook, self.next_page_num)
	self.notebook.AddPage(panel, 'Staining Protocol No: %s'%str(self.next_page_num), True)
	self.next_page_num += 1	

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
	self.settings_controls[targseqTAG].SetToolTipString('Target Sequence')
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Target Sequence'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	top_fgs.Add(self.settings_controls[targseqTAG], 0)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ''), 0)
	#--Primer Sequence--#
	primseqTAG = 'Staining|Genetic|Primer|'+str(self.page_counter)
	self.settings_controls[primseqTAG] = wx.TextCtrl(self.top_panel, value=meta.get_field(primseqTAG, default=''))
	self.settings_controls[primseqTAG].Bind(wx.EVT_TEXT,self.OnSavingData)
	self.settings_controls[primseqTAG].SetToolTipString('Primer Sequence')
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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	
            
########################################################################        
################## STAINING SETTING PANEL    ###########################
########################################################################
class DyeSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()
		
	self.protocol = 'Staining|Dye'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
	    for protocol_id in supp_protocol_list:
		panel = DyePanel(self.notebook, int(protocol_id))
		self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Staining Protocols")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Staining Protocols")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = DyePanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(self.next_page_num), True)
        self.next_page_num += 1
	
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = DyePanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Staining Protocol No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1	    
	
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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	 	 


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
		
	self.protocol = 'AddProcess|Spin'	

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
	    for protocol_id in supp_protocol_list:
		panel = SpinPanel(self.notebook, int(protocol_id))
		self.notebook.AddPage(panel, 'Spinning Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Spinning Protocols")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Spinning Protocols")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = SpinPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Spinning Protocol No: %s'%(self.next_page_num), True)
        self.next_page_num += 1
	
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = SpinPanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Spinning Protocol No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1	    


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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	 
 

   

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
	
	self.protocol = 'AddProcess|Wash'
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
	    for protocol_id in supp_protocol_list:
		panel = WashPanel(self.notebook, int(protocol_id))
		self.notebook.AddPage(panel, 'Washing Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Washing Protocol")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Washing Protocol")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = WashPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Washing Protocol No: %s'%(self.next_page_num), True)
        self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = WashPanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Washing Protocol No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1	    


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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	 
  	 
	    

        
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
	
	self.protocol = 'AddProcess|Dry'

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
	    for protocol_id in supp_protocol_list:
		panel = DryPanel(self.notebook, int(protocol_id))
		self.notebook.AddPage(panel, 'Drying Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Drying Protocol")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Drying Protocol")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = DryPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Drying Protocol No: %s'%(self.next_page_num), True)
        self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = DryPanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Drying Protocol No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1

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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	 

            
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
	self.protocol = 'AddProcess|Medium'

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
	    for protocol_id in supp_protocol_list:
		panel = MediumPanel(self.notebook, int(protocol_id))
		self.notebook.AddPage(panel, 'Medium Addition Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Medium Addition Protocol")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Medium Addition Protocol")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = MediumPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Add Medium Protocol No: %s'%(self.next_page_num), True)
        self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
                                    defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = MediumPanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Add Medium Protocol No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1


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
	self.settings_controls[additiveField].SetToolTipString('List the medium additives')
		
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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	 


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

	self.protocol = 'AddProcess|Incubator'

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        supp_protocol_list = sorted(meta.get_field_instances(self.protocol))
	
        self.next_page_num = 1
        # update the  number of existing cell loading
        if supp_protocol_list: 
            self.next_page_num  =  int(supp_protocol_list[-1])+1
	    for protocol_id in supp_protocol_list:
		panel = IncubatorPanel(self.notebook, int(protocol_id))
		self.notebook.AddPage(panel, 'Incubation Protocol No: %s'%(protocol_id), True)

        # Add the buttons
        addPageBtn = wx.Button(self, label="Add Incubation Protocol")
        addPageBtn.Bind(wx.EVT_BUTTON, self.onAddPage)
        
        loadPageBtn = wx.Button(self, label="Load Incubation Protocol")
        loadPageBtn.Bind(wx.EVT_BUTTON, self.onLoadSuppProtocol)        

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(loadPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPage(self, event):
        panel = IncubatorPanel(self.notebook, self.next_page_num)
        self.notebook.AddPage(panel, 'Incubation Protocol No: %s'%(self.next_page_num), True)
        self.next_page_num += 1
    
    def onLoadSuppProtocol(self, event):
	meta = ExperimentSettings.getInstance()
	
	dlg = wx.FileDialog(None, "Select the file containing your supplementary protocol...",
	                            defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
	# read the supp protocol file
	if dlg.ShowModal() == wx.ID_OK:
	    filename = dlg.GetFilename()
	    dirname = dlg.GetDirectory()
	    file_path = os.path.join(dirname, filename)	    
	    
	    meta.load_supp_protocol_file(file_path, self.protocol+'|%s'%str(self.next_page_num))
	
	    # set the panel accordingly    
	    panel = IncubatorPanel(self.notebook, self.next_page_num)
	    self.notebook.AddPage(panel, 'Incubation Protocol No: %s'%str(self.next_page_num), True)
	    self.next_page_num += 1
	
        
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
	meta = ExperimentSettings.getInstance()
	
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if len(tag.split('|'))>4:
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 4) == exp.get_tag_stump(tg, 4):
		    c_num = int(tg.split('|')[4])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
	    meta.set_field(exp.get_tag_stump(tag, 4), info)  # get the core tag like AddProcess|Spin|Step|<instance> = [duration, description, temp]
	else:
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(tag, ctrl.GetStringSelection())
	    else:
		user_input = ctrl.GetValue()
		user_input.rstrip('\n')
		user_input.rstrip('\t')		
		meta.set_field(tag, user_input)	
            
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
        tlm_list = sorted(meta.get_field_instances('DataAcquis|TLM|'))
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
        fgs.Add(wx.StaticText(self.sw, -1, ' Software Name and Version'), 0)
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
        hcs_list = sorted(meta.get_field_instances('DataAcquis|HCS|'))
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
        fgs.Add(wx.StaticText(self.sw, -1, ' Software Name and Version'), 0)
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
        flow_list = sorted(meta.get_field_instances('DataAcquis|FCS|'))
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

########################################################################        
################## NoteSettingPanel             #########################
########################################################################
class NoteSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        nte_list = sorted(meta.get_field_instances('Notes|'))
        self.nte_next_page_num = 1
        # update the  number of existing cell loading
        if nte_list: 
            self.nte_next_page_num  =  int(nte_list[-1])+1
        for nte_id in nte_list:
            panel = NotePanel(self.notebook, int(nte_id))
            self.notebook.AddPage(panel, 'Note No: %s'%(nte_id), True)

        # Add the buttons
        addNTEPageBtn = wx.Button(self, label="Add Note")
        addNTEPageBtn.Bind(wx.EVT_BUTTON, self.onAddNTEPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addNTEPageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddNTEPage(self, event):
        panel = NotePanel(self.notebook, self.nte_next_page_num)
        self.notebook.AddPage(panel, 'Note No: %s'%(self.nte_next_page_num), True)
        self.nte_next_page_num += 1


class NotePanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        self.fgs = wx.FlexGridSizer(rows=2, cols=2, hgap=5, vgap=5)
	
	self.noteSelect = wx.Choice(self.sw, -1,  choices=['CriticalPoint', 'Rest', 'Hint'])
	self.noteSelect.SetStringSelection('')
	self.noteSelect.Bind(wx.EVT_CHOICE, self.onCreateNotepad)
	self.fgs.Add(wx.StaticText(self.sw, -1, 'Note type'), 0)
	self.fgs.Add(self.noteSelect, 0, wx.EXPAND)	
	
	#---------------Layout with sizers---------------
	self.sw.SetSizer(self.fgs)
	self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)	
        
        ####################################################
        ## TODO:  Add capability to add video/image notes ##
        ####################################################
	if meta.get_field_tags('Notes|', str(self.page_counter)):
	    self.noteTAG = meta.get_field_tags('Notes|', str(self.page_counter))[0]
            self.noteType = self.noteTAG.split('|')[1]
            self.noteSelect.SetStringSelection(self.noteType)
            self.noteSelect.Disable()
            
            self.noteDescrip = wx.TextCtrl(self.sw,  value=meta.get_field('Notes|%s|Description|%s' %(self.noteType, str(self.page_counter))), style=wx.TE_MULTILINE)
            self.noteDescrip.Bind(wx.EVT_TEXT, self.OnSavingData)
            self.noteDescrip.SetInitialSize((250, 300))
            self.fgs.Add(wx.StaticText(self.sw, -1, 'Note Description'), 0)
            self.fgs.Add(self.noteDescrip, 0,  wx.EXPAND)
	    
	    #---------------Layout with sizers---------------
	    self.sw.SetSizer(self.fgs)
	    self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
    
	    self.Sizer = wx.BoxSizer(wx.VERTICAL)
	    self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5) 	    

    def onCreateNotepad(self, event):
	
	ctrl = event.GetEventObject()
	self.noteType = ctrl.GetStringSelection()
        self.noteSelect.Disable()
        self.noteDescrip = wx.TextCtrl(self.sw,  value='', style=wx.TE_MULTILINE)
        self.noteDescrip.Bind(wx.EVT_TEXT, self.OnSavingData)
        self.noteDescrip.SetInitialSize((250, 300))
        self.fgs.Add(wx.StaticText(self.sw, -1, 'Note Description'), 0)
        self.fgs.Add(self.noteDescrip, 0,  wx.EXPAND)

        #---------------Layout with sizers---------------
        self.sw.SetSizer(self.fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)        

    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()    
        self.noteTAG = 'Notes|%s|Description|%s' %(self.noteType, str(self.page_counter))
        meta.set_field(self.noteTAG, self.noteDescrip.GetValue())

        
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