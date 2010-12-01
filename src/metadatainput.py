#!/usr/bin/env python

import wx
import  wx.calendar
import wx.lib.agw.flatnotebook as fnb
import wx.lib.mixins.listctrl  as  listmix
from experimentsettings import *
import os
import re

class ExperimentSettingsWindow(wx.SplitterWindow):
    def __init__(self, parent, id=-1, **kwargs):
        wx.SplitterWindow.__init__(self, parent, id, **kwargs)
        
        self.tree = wx.TreeCtrl(self, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS)

        root = self.tree.AddRoot('Experiment Name')

        stc = self.tree.AppendItem(root, 'STATIC')
        ovr = self.tree.AppendItem(stc, 'Overview')
        ins = self.tree.AppendItem(stc, 'Instrument Settings')
        stk = self.tree.AppendItem(stc, 'Stock Culture')
        exv = self.tree.AppendItem(stc, 'Experimental Vessel')

        stc = self.tree.AppendItem(root, 'TEMPORAL')
        cld = self.tree.AppendItem(stc, 'Cell Transfer')
        ptb = self.tree.AppendItem(stc, 'Perturbation')
        adp = self.tree.AppendItem(stc, 'Additional Processes')
        self.tree.AppendItem(adp, 'Staining')
        self.tree.AppendItem(adp, 'Spin')
        self.tree.AppendItem(adp, 'Wash')
        #self.tree.AppendItem(adp, 'Dry')
        dta = self.tree.AppendItem(stc, 'Data Acquisition')
        self.tree.AppendItem(dta, 'Timelapse Image')
        self.tree.AppendItem(dta, 'Static Image')
        self.tree.AppendItem(dta, 'FCS files')
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
        elif self.tree.GetItemText(item) == 'Instrument Settings':
            self.settings_panel = InstrumentSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Experimental Vessel':
            self.settings_panel = ExpVessSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Flask':
            self.settings_panel = FlaskPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Stock Culture':
            self.settings_panel = StockCultureSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Cell Transfer':
            self.settings_panel = CellTransferSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Perturbation':
            self.settings_panel = PerturbationSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Staining':
            self.settings_panel = StainingAgentSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Spin':
            self.settings_panel =  SpinningSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Wash':
            self.settings_panel =  WashSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Timelapse Image':
            self.settings_panel = TLMSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'Static Image':
            self.settings_panel = HCSSettingPanel(self.settings_container)
        elif self.tree.GetItemText(item) == 'FCS files':
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
################## INSTRUMENT SETTING PANEL         ####################
########################################################################
class InstrumentSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        # create some widgets
        #self.first_type_page_counter = 0
        #self.second_type_page_counter = 0

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        mic_list = meta.get_field_instances('Instrument|Microscope|')
        self.mic_next_page_num = 1
        # update the  number of existing microscope
        if mic_list:
            #print mic_list 
            self.mic_next_page_num =  int(mic_list[-1])+1
        for mic_id in mic_list:
            panel = MicroscopePanel(self.notebook, int(mic_id))
            self.notebook.AddPage(panel, 'Microscope: %s'%(mic_id), True)

        # Get all the previously encoded Flowcytometer pages and re-Add them as pages
        flow_list = meta.get_field_instances('Instrument|Flowcytometer|')
        self.flow_next_page_num = 1
        # update the  number of existing flowcytometer
        if flow_list:
            self.flow_next_page_num =  int(flow_list[-1])+1
        for flow_id in flow_list:
            panel = FlowCytometerPanel(self.notebook, int(flow_id))
            self.notebook.AddPage(panel, 'Flow Cytometer: %s'%(flow_id), True)

        addMicroscopePageBtn = wx.Button(self, label="Add Microscope")
        addMicroscopePageBtn.SetBackgroundColour("#33FF33")
        addMicroscopePageBtn.Bind(wx.EVT_BUTTON, self.onAddMicroscopePage)
        #rmvMicroscopePageBtn = wx.Button(self, label="Delete Microscope")
        #rmvMicroscopePageBtn.SetBackgroundColour("#FF3300")
        #rmvMicroscopePageBtn.Bind(wx.EVT_BUTTON, self.onDelMicroscopePage)
        #self.createRightClickMenu()
        #self.notebook.SetRightClickMenu(self._rmenu)

        addFlowcytometerPageBtn = wx.Button(self, label="Add Flowcytometer")
        addFlowcytometerPageBtn.SetBackgroundColour("#33FF33")
        addFlowcytometerPageBtn.Bind(wx.EVT_BUTTON, self.onAddFlowcytometerPage)
        #rmvFlowcytometerPageBtn = wx.Button(self, label="Delete Flowcyotometer")
        #rmvFlowcytometerPageBtn.SetBackgroundColour("#FF3300")
        #rmvFlowcytometerPageBtn.Bind(wx.EVT_BUTTON, self.onDelFlowcytometerPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addMicroscopePageBtn  , 0, wx.ALL, 5)
        #btnSizer.Add(rmvMicroscopePageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(addFlowcytometerPageBtn , 0, wx.ALL, 5)
        #btnSizer.Add(rmvFlowcytometerPageBtn , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddMicroscopePage(self, event):
        panel = MicroscopePanel(self.notebook, self.mic_next_page_num)
        self.notebook.AddPage(panel, 'Microscope: %s'%(self.mic_next_page_num), True)
        self.mic_next_page_num += 1

    #def onDelMicroscopePage(self, event):
        #if self.first_type_page_counter > 0:
            #panel = self.notebook.GetPage(self.notebook.GetSelection())
            #id = panel.first_type_page_counter
            #meta = ExperimentSettings.getInstance()
            #fields = meta.get_field_tags('Instrument|Microscope', instance=str(id))
            #for field in fields:
                #meta.remove_field(field)
            #self.notebook.DeletePage(self.notebook.GetSelection())

    #def createRightClickMenu(self):
        #self._rmenu = wx.Menu()
        #item = wx.MenuItem(self._rmenu, wx.ID_ANY,
                            #"Close Tab\tCtrl+F4",
                            #"Close Tab")
        #self.Bind(wx.EVT_MENU, self.onDelMicroscopePage, item)
        #self._rmenu.AppendItem(item)		

    def onAddFlowcytometerPage(self, event):
        panel = FlowCytometerPanel(self.notebook, self.flow_next_page_num)
        self.notebook.AddPage(panel, 'Flow Cytometer: %s'%(self.flow_next_page_num), True)
        self.flow_next_page_num += 1


    #def onDelFlowcytometerPage(self, event):
        #if self.second_type_page_counter >= 1:
            #self.second_type_page_counter -= 1
            #self.notebook.DeletePage(self.notebook.GetSelection())   
            #panel = self.notebook.GetPage(self.notebook.GetSelection())
            #id = panel.first_type_page_counter
            #meta = ExperimentSettings.getInstance()
            #fields = meta.get_field_tags('Instrument|FlowCytometer', instance=str(id))
            #for field in fields:
                #meta.remove_field(field)



class MicroscopePanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=25, cols=2, hgap=5, vgap=5)

        #----------- Microscope Labels and Text Controler-------        
        heading = 'Microscope Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #--Manufacture--#
        micromfgTAG = 'Instrument|Microscope|Manufacter|'+str(self.page_counter)
        self.settings_controls[micromfgTAG] = wx.Choice(self.sw, -1,  choices=['Zeiss','Olympus','Nikon', 'MDS', 'GE'])
        if meta.get_field(micromfgTAG) is not None:
            self.settings_controls[micromfgTAG].SetStringSelection(meta.get_field(micromfgTAG))
        self.settings_controls[micromfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)    
        self.settings_controls[micromfgTAG].SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(self.settings_controls[micromfgTAG], 0, wx.EXPAND)
        #--Model--#
        micromdlTAG = 'Instrument|Microscope|Model|'+str(self.page_counter)
        self.settings_controls[micromdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(micromdlTAG, default=''))
        self.settings_controls[micromdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[micromdlTAG].SetToolTipString('Model number of the microscope')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(self.settings_controls[micromdlTAG], 0, wx.EXPAND)
        #--Microscope type--#
        microtypTAG = 'Instrument|Microscope|Type|'+str(self.page_counter)
        self.settings_controls[microtypTAG] = wx.Choice(self.sw, -1,  choices=['Upright', 'Inverted', 'Confocal'])
        if meta.get_field(microtypTAG) is not None:
            self.settings_controls[microtypTAG].SetStringSelection(meta.get_field(microtypTAG))
        self.settings_controls[microtypTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        self.settings_controls[microtypTAG].SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Microscope Type'), 0)
        fgs.Add(self.settings_controls[microtypTAG], 0, wx.EXPAND)
        #--Light source--#
        microlgtTAG = 'Instrument|Microscope|LightSource|'+str(self.page_counter)
        self.settings_controls[microlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Filament', 'Arc', 'LightEmitingDiode'])
        if meta.get_field(microlgtTAG) is not None:
            self.settings_controls[microlgtTAG].SetStringSelection(meta.get_field(microlgtTAG))
        self.settings_controls[microlgtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData) 
        self.settings_controls[microlgtTAG].SetToolTipString('e.g. Laser, Filament, Arc, Light Emiting Diode')
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(self.settings_controls[microlgtTAG], 0, wx.EXPAND)
        #--Detector--#
        microdctTAG = 'Instrument|Microscope|Detector|'+str(self.page_counter)
        self.settings_controls[microdctTAG] = wx.Choice(self.sw, -1,  choices=['CCD', 'Intensified-CCD', 'Analog-Video', 'Spectroscopy', 'Life-time-imaging', 'Correlation-Spectroscopy', 'FTIR', 'EM-CCD', 'APD', 'CMOS'])
        if meta.get_field(microdctTAG) is not None:
            self.settings_controls[microdctTAG].SetStringSelection(meta.get_field(microdctTAG))
        self.settings_controls[microdctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microdctTAG].SetToolTipString('Type of dectector used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Dectector'), 0)
        fgs.Add(self.settings_controls[microdctTAG], 0, wx.EXPAND)
        #--Lense Aperture--#
        microlnsappTAG = 'Instrument|Microscope|LensApprture|'+str(self.page_counter)
        self.settings_controls[microlnsappTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microlnsappTAG, default=''))
        self.settings_controls[micromdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microlnsappTAG].SetToolTipString('A floating value of lens numerical aperture')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lense Apparture'), 0)
        fgs.Add(self.settings_controls[microlnsappTAG], 0, wx.EXPAND)
        # Lense Correction
        microlnscorrTAG = 'Instrument|Microscope|LensCorr|'+str(self.page_counter)
        self.settings_controls[microlnscorrTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(microlnscorrTAG) is not None:
            self.settings_controls[microlnscorrTAG].SetStringSelection(meta.get_field(microlnscorrTAG))
        self.settings_controls[microlnscorrTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microlnscorrTAG].SetToolTipString('Yes/No')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lense Correction'), 0)
        fgs.Add(self.settings_controls[microlnscorrTAG], 0, wx.EXPAND)
        #--Illumination Type--#
        microIllTAG = 'Instrument|Microscope|IllumType|'+str(self.page_counter)
        self.settings_controls[microIllTAG] = wx.Choice(self.sw, -1,  choices=['Transmitted','Epifluorescence','Oblique','NonLinear'])
        if meta.get_field(microIllTAG) is not None:
            self.settings_controls[microIllTAG].SetStringSelection(meta.get_field(microIllTAG))
        self.settings_controls[microIllTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microIllTAG].SetToolTipString('Type of illumunation used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Illumination Type'), 0)
        fgs.Add(self.settings_controls[microIllTAG], 0, wx.EXPAND)
        #--Mode--#
        microModTAG = 'Instrument|Microscope|Mode|'+str(self.page_counter)
        self.settings_controls[microModTAG] = wx.Choice(self.sw, -1,  choices=['WideField','LaserScanningMicroscopy', 'LaserScanningConfocal', 'SpinningDiskConfocal', 'SlitScanConfocal', 'MultiPhotonMicroscopy', 'StructuredIllumination','SingleMoleculeImaging', 'TotalInternalReflection', 'FluorescenceLifetime', 'SpectralImaging', 'FluorescenceCorrelationSpectroscopy', 'NearFieldScanningOpticalMicroscopy', 'SecondHarmonicGenerationImaging', 'Timelapse', 'Other'])
        if meta.get_field(microModTAG) is not None:
            self.settings_controls[microModTAG].SetStringSelection(meta.get_field(microModTAG))
        self.settings_controls[microModTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microModTAG].SetToolTipString('Mode of the microscope')
        fgs.Add(wx.StaticText(self.sw, -1, 'Mode'), 0)
        fgs.Add(self.settings_controls[microModTAG], 0, wx.EXPAND)
        #--Immersion--#
        microImmTAG = 'Instrument|Microscope|Immersion|'+str(self.page_counter)
        self.settings_controls[microImmTAG] = wx.Choice(self.sw, -1,  choices=['Oil', 'Water', 'WaterDipping', 'Air', 'Multi', 'Glycerol', 'Other', 'Unkonwn'])
        if meta.get_field(microImmTAG) is not None:
            self.settings_controls[microImmTAG].SetStringSelection(meta.get_field(microImmTAG))
        self.settings_controls[microImmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microImmTAG].SetToolTipString('Immersion medium used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
        fgs.Add(self.settings_controls[microImmTAG], 0, wx.EXPAND)
        #--Correction--#
        microCorrTAG = 'Instrument|Microscope|Correction|'+str(self.page_counter)
        self.settings_controls[microCorrTAG] = wx.Choice(self.sw, -1,  choices=['UV', 'PlanApo', 'PlanFluor', 'SuperFluor', 'VioletCorrected', 'Unknown'])
        if meta.get_field(microCorrTAG) is not None:
            self.settings_controls[microCorrTAG].SetStringSelection(meta.get_field(microCorrTAG))
        self.settings_controls[microCorrTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microCorrTAG].SetToolTipString('Lense correction used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
        fgs.Add(self.settings_controls[microCorrTAG], 0, wx.EXPAND)
        #--Nominal Magnification--#
        microNmgTAG = 'Instrument|Microscope|NominalMagnification|'+str(self.page_counter)
        self.settings_controls[microNmgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microNmgTAG, default=''))
        self.settings_controls[microNmgTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microNmgTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
        fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
        fgs.Add(self.settings_controls[microNmgTAG], 0, wx.EXPAND)
        # Calibrated Magnification
        microCalTAG = 'Instrument|Microscope|CalibratedMagnification|'+str(self.page_counter)
        self.settings_controls[microCalTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCalTAG, default=''))
        self.settings_controls[microCalTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microCalTAG].SetToolTipString('The magnification of the lens as measured by a calibration process- i.e. 59.987 for a 60X lens')
        fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
        fgs.Add(self.settings_controls[microCalTAG], 0, wx.EXPAND)
        #--Working distance--#
        microWrkTAG = 'Instrument|Microscope|WorkDistance|'+str(self.page_counter)
        self.settings_controls[microWrkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microWrkTAG, default=''))
        self.settings_controls[microWrkTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microWrkTAG].SetToolTipString('The working distance of the lens expressed as a floating point (real) number. Units are um')
        fgs.Add(wx.StaticText(self.sw, -1, 'Working Distance (uM)'), 0)
        fgs.Add(self.settings_controls[microWrkTAG], 0, wx.EXPAND)
        #--Filter used--#
        microFltTAG = 'Instrument|Microscope|Filter|'+str(self.page_counter)
        self.settings_controls[microFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(microFltTAG) is not None:
            self.settings_controls[microFltTAG].SetStringSelection(meta.get_field(microFltTAG))
        self.settings_controls[microFltTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[microFltTAG].SetToolTipString('Whether filter was used or not')
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
        fgs.Add(self.settings_controls[microFltTAG], 0, wx.EXPAND)
        #--Software--#
        microSoftTAG = 'Instrument|Microscope|Software|'+str(self.page_counter)
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
        microTempTAG = 'Instrument|Microscope|Temp|'+str(self.page_counter)
        self.settings_controls[microTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microTempTAG, default=''))
        self.settings_controls[microTempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microTempTAG].SetToolTipString('Temperature of the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
        fgs.Add(self.settings_controls[microTempTAG], 0, wx.EXPAND)
        #--Carbondioxide--#
        microCarbonTAG = 'Instrument|Microscope|C02|'+str(self.page_counter)
        self.settings_controls[microCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCarbonTAG, default=''))
        self.settings_controls[microCarbonTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
        fgs.Add(self.settings_controls[microCarbonTAG], 0, wx.EXPAND)
        #--Humidity--#
        microHumTAG = 'Instrument|Microscope|Humidity|'+str(self.page_counter)
        self.settings_controls[microHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microHumTAG, default=''))
        self.settings_controls[microHumTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microHumTAG].SetToolTipString('Humidity at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
        fgs.Add(self.settings_controls[microHumTAG], 0, wx.EXPAND)
        #--Pressure--#
        microPressTAG = 'Instrument|Microscope|Pressure|'+str(self.page_counter)
        self.settings_controls[microPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microPressTAG, default=''))
        self.settings_controls[microPressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[microPressTAG].SetToolTipString('Pressure at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
        fgs.Add(self.settings_controls[microPressTAG], 0, wx.EXPAND)


        ##--Create the Adding button--#
        #fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        #addBut = wx.Button(self.sw, -1, label="Record Microscope %s settings" % self.page_counter)
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


class FlowCytometerPanel(wx.Panel):
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
        heading = 'Flowcytometer Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)

        #--Manufacture--#
        flowmfgTAG = 'Instrument|Flowcytometer|Manufacter|'+str(self.page_counter)
        self.settings_controls[flowmfgTAG] = wx.Choice(self.sw, -1,  choices=['Beckman','BD-Biosciences'])
        if meta.get_field(flowmfgTAG) is not None:
            self.settings_controls[flowmfgTAG].SetStringSelection(meta.get_field(flowmfgTAG))
        self.settings_controls[flowmfgTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowmfgTAG].SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(self.settings_controls[flowmfgTAG], 0, wx.EXPAND)
        #--Model--#
        flowmdlTAG = 'Instrument|Flowcytometer|Model|'+str(self.page_counter)
        self.settings_controls[flowmdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(flowmdlTAG, default=''))
        self.settings_controls[flowmdlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[flowmdlTAG].SetToolTipString('Model number of the Flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(self.settings_controls[flowmdlTAG], 0, wx.EXPAND)
        #--Flowcytometer type--#
        flowtypTAG = 'Instrument|Flowcytometer|Type|'+str(self.page_counter)
        self.settings_controls[flowtypTAG] = wx.Choice(self.sw, -1,  choices=['Stream-in-air', 'cuvette'])
        if meta.get_field(flowtypTAG) is not None:
            self.settings_controls[flowtypTAG].SetStringSelection(meta.get_field(flowtypTAG))
        self.settings_controls[flowtypTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowtypTAG].SetToolTipString('Type of flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Flowcytometer Type'), 0)
        fgs.Add(self.settings_controls[flowtypTAG], 0, wx.EXPAND)
        #--Light source--#
        flowlgtTAG = 'Instrument|Flowcytometer|LightSource|'+str(self.page_counter)
        self.settings_controls[flowlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Beam'])
        if meta.get_field(flowlgtTAG) is not None:
            self.settings_controls[flowlgtTAG].SetStringSelection(meta.get_field(flowlgtTAG))
        self.settings_controls[flowlgtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowlgtTAG].SetToolTipString('Light source of the flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(self.settings_controls[flowlgtTAG], 0, wx.EXPAND)
        #--Detector--#
        flowdctTAG = 'Instrument|Flowcytometer|Detector|'+str(self.page_counter)
        self.settings_controls[flowdctTAG] = wx.Choice(self.sw, -1,  choices=['PhotoMultiplierTube', 'FluorescentDetectors'])
        if meta.get_field(flowdctTAG) is not None:
            self.settings_controls[flowdctTAG].SetStringSelection(meta.get_field(flowdctTAG))
        self.settings_controls[flowdctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowdctTAG].SetToolTipString('Type of dectector used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Dectector'), 0)
        fgs.Add(self.settings_controls[flowdctTAG], 0, wx.EXPAND)
        #--Filter used--#
        flowFltTAG = 'Instrument|Flowcytometer|Filter|'+str(self.page_counter)
        self.settings_controls[flowFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
        if meta.get_field(flowFltTAG) is not None:
            self.settings_controls[flowFltTAG].SetStringSelection(meta.get_field(flowFltTAG))
        self.settings_controls[flowdctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[flowFltTAG].SetToolTipString('Whether filter was used or not')
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
        fgs.Add(self.settings_controls[flowFltTAG], 0, wx.EXPAND)

        #-- Heading --#
        heading = 'Incubator Settings'
        text = wx.StaticText(self.sw, -1, heading)
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        text.SetFont(font)
        fgs.Add(text, 0)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
            #--Temperature--#
        flowTempTAG = 'Instrument|Flowcytometer|Temp|'+str(self.page_counter)
        self.settings_controls[flowTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowTempTAG, default=''))
        self.settings_controls[flowTempTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[flowTempTAG].SetToolTipString('Temperature of the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
        fgs.Add(self.settings_controls[flowTempTAG], 0, wx.EXPAND)
        #--Carbondioxide--#
        flowCarbonTAG = 'Instrument|Flowcytometer|C02|'+str(self.page_counter)
        self.settings_controls[flowCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowCarbonTAG, default=''))
        self.settings_controls[flowCarbonTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[flowCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
        fgs.Add(self.settings_controls[flowCarbonTAG], 0, wx.EXPAND)
        #--Humidity--#
        flowHumTAG = 'Instrument|Flowcytometer|Humidity|'+str(self.page_counter)
        self.settings_controls[flowHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowHumTAG, default=''))
        self.settings_controls[flowHumTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[flowHumTAG].SetToolTipString('Humidity at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
        fgs.Add(self.settings_controls[flowHumTAG], 0, wx.EXPAND)
        #--Pressure--#
        flowPressTAG = 'Instrument|Flowcytometer|Pressure|'+str(self.page_counter)
        self.settings_controls[flowPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowPressTAG, default=''))
        self.settings_controls[flowPressTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[flowPressTAG].SetToolTipString('Pressure at the incubator')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
        fgs.Add(self.settings_controls[flowPressTAG], 0, wx.EXPAND)



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
################## STOCK CULTURE SETTING PANEL  ########################
########################################################################
class StockCultureSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent, id)

        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8)

        self.stock_next_page_num = 1
        stock_list = meta.get_field_instances('StockCulture|Sample|')
        # update the  number of existing microscope
        if stock_list:
            print stock_list
            self.stock_next_page_num =  int(stock_list[-1])+1
        for stock_id in stock_list:
            panel = StockCulturePanel(self.notebook, int(stock_id))
            self.notebook.AddPage(panel, 'StockCulture: %s'%(stock_id), True)

        addStockCulturePageBtn = wx.Button(self, label="Add Stock Culture")
        addStockCulturePageBtn.SetBackgroundColour("#33FF33")
        addStockCulturePageBtn.Bind(wx.EVT_BUTTON, self.onAddStockCulturePage)
        #rmvStockCulturePageBtn = wx.Button(self, label="Delete Stock Culture")
        #rmvStockCulturePageBtn.SetBackgroundColour("#FF3300")
        #rmvStockCulturePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addStockCulturePageBtn  , 0, wx.ALL, 5)
        #btnSizer.Add(rmvStockCulturePageBtn  , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddStockCulturePage(self, event):
        panel = StockCulturePanel(self.notebook, self.stock_next_page_num)
        self.notebook.AddPage(panel, 'Stock Culture: %s'%(self.stock_next_page_num), True)
        self.stock_next_page_num += 1	

class StockCulturePanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5) 


        #----------- Labels and Text Controler-------        
        # Cell Line Name
        cellLineTAG = 'StockCulture|Sample|CellLine|'+str(self.page_counter)
        self.settings_controls[cellLineTAG] = wx.TextCtrl(self.sw, value=meta.get_field(cellLineTAG, default=''))
        self.settings_controls[cellLineTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[cellLineTAG].SetToolTipString('Cell Line selection')
        fgs.Add(wx.StaticText(self.sw, -1, 'Cell Line'), 0)
        fgs.Add(self.settings_controls[cellLineTAG], 0, wx.EXPAND)        

        # Taxonomic ID
        taxIdTAG = 'StockCulture|Sample|TaxID|'+str(self.page_counter)
        self.settings_controls[taxIdTAG] = wx.Choice(self.sw, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
        if meta.get_field(taxIdTAG) is not None:
            self.settings_controls[taxIdTAG].SetStringSelection(meta.get_field(taxIdTAG))
        self.settings_controls[taxIdTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[taxIdTAG].SetToolTipString('Taxonomic ID of the species')
        fgs.Add(wx.StaticText(self.sw, -1, 'Organism'), 0)
        fgs.Add(self.settings_controls[taxIdTAG], 0, wx.EXPAND)

        # Gender
        gendTAG = 'StockCulture|Sample|Gender|'+str(self.page_counter)
        self.settings_controls[gendTAG] = wx.Choice(self.sw, -1,  choices=['Male', 'Female', 'Neutral'])
        if meta.get_field(gendTAG) is not None:
            self.settings_controls[gendTAG].SetStringSelection(meta.get_field(gendTAG))
        self.settings_controls[gendTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[gendTAG].SetToolTipString('Gender of the organism')
        fgs.Add(wx.StaticText(self.sw, -1, 'Gender'), 0)
        fgs.Add(self.settings_controls[gendTAG], 0, wx.EXPAND)        

        # Age
        ageTAG ='StockCulture|Sample|Age|'+str(self.page_counter)
        self.settings_controls[ageTAG] = wx.TextCtrl(self.sw, value=meta.get_field(ageTAG, default=''))
        self.settings_controls[ageTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[ageTAG].SetToolTipString('Age of the organism in days when the cells were collected. .')
        fgs.Add(wx.StaticText(self.sw, -1, 'Age of organism (days)'), 0)
        fgs.Add(self.settings_controls[ageTAG], 0, wx.EXPAND)

        # Organ
        organTAG = 'StockCulture|Sample|Organ|'+str(self.page_counter)
        self.settings_controls[organTAG] = wx.TextCtrl(self.sw, value=meta.get_field(organTAG, default=''))
        self.settings_controls[organTAG].Bind(wx.EVT_TEXT, self.OnSavingData)	
        self.settings_controls[organTAG].SetToolTipString('Organ name from where the cell were collected. eg. Heart, Lung, Bone etc')
        fgs.Add(wx.StaticText(self.sw, -1, 'Organ'), 0)
        fgs.Add(self.settings_controls[organTAG], 0, wx.EXPAND)

        # Tissue
        tissueTAG = 'StockCulture|Sample|Tissue|'+str(self.page_counter)
        self.settings_controls[tissueTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tissueTAG, default=''))
        self.settings_controls[tissueTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tissueTAG].SetToolTipString('Tissue from which the cells were collected')
        fgs.Add(wx.StaticText(self.sw, -1, 'Tissue'), 0)
        fgs.Add(self.settings_controls[tissueTAG], 0, wx.EXPAND)

        # Pheotype
        phtypTAG = 'StockCulture|Sample|Phenotype|'+str(self.page_counter)
        self.settings_controls[phtypTAG] = wx.TextCtrl(self.sw, value=meta.get_field(phtypTAG, default=''))
        self.settings_controls[phtypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[phtypTAG].SetToolTipString('Phenotypic examples Colour Height OR any other value descriptor')
        fgs.Add(wx.StaticText(self.sw, -1, 'Phenotype'), 0)
        fgs.Add(self.settings_controls[phtypTAG], 0, wx.EXPAND)

        # Genotype
        gentypTAG = 'StockCulture|Sample|Genotype|'+str(self.page_counter)
        self.settings_controls[gentypTAG] = wx.TextCtrl(self.sw, value=meta.get_field(gentypTAG, default=''))
        self.settings_controls[gentypTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[gentypTAG].SetToolTipString('Wild type or mutant etc. (single word)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Genotype'), 0)
        fgs.Add(self.settings_controls[gentypTAG], 0, wx.EXPAND)

        # Strain
        strainTAG = 'StockCulture|Sample|Strain|'+str(self.page_counter)
        self.settings_controls[strainTAG] = wx.TextCtrl(self.sw, value=meta.get_field(strainTAG, default=''))
        self.settings_controls[strainTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[strainTAG].SetToolTipString('Starin of that cell line eGFP, Wild type etc')
        fgs.Add(wx.StaticText(self.sw, -1, 'Strain'), 0)
        fgs.Add(self.settings_controls[strainTAG], 0, wx.EXPAND)

        #  Passage Number
        passTAG = 'StockCulture|Sample|PassageNumber|'+str(self.page_counter)
        self.settings_controls[passTAG] = wx.TextCtrl(self.sw, value=meta.get_field(passTAG, default=''))
        self.settings_controls[passTAG].Bind(wx.EVT_TEXT, self.OnSavingData)    
        self.settings_controls[passTAG].SetToolTipString('Numeric value of the passage of the cells under investigation')
        fgs.Add(wx.StaticText(self.sw, -1, 'Passage Number'), 0)
        fgs.Add(self.settings_controls[passTAG], 0, wx.EXPAND)

        ##--Create the Adding button--#
        #addBut = wx.Button(self.sw, -1, label="Record Stock Culture")
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
################## EXPERIMENT VESSEL SETTING PANEL  ####################
########################################################################	    
class ExpVessSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()


        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON|fnb.FNB_VC8)
        # Get all the previously encoded Microscope pages and re-Add them as pages
        plate_list = meta.get_field_instances('ExptVessel|Plate|')
        self.plate_next_page_num = 1
        # update the  number of existing plateroscope
        if plate_list: 
            self.plate_next_page_num =  int(plate_list[-1])+1
        for plate_id in plate_list:
            panel = PlateWellPanel(self.notebook, int(plate_id))
            self.notebook.AddPage(panel, 'Plate No: %s'%(plate_id), True)

        # Get all the previously encoded Flowcytometer pages and re-Add them as pages
        flask_list = meta.get_field_instances('ExptVessel|Flask|')
        self.flask_next_page_num = 1
        # update the  number of existing flaskcytometer
        if flask_list:
            self.flask_next_page_num =  int(flask_list[-1])+1
        for flask_id in flask_list:
            panel = FlaskPanel(self.notebook, int(flask_id))
            self.notebook.AddPage(panel, 'Flask no: %s'%(flask_id), True)

        addPlatePageBtn = wx.Button(self, label="Add Plate")
        addPlatePageBtn.SetBackgroundColour("#33FF33")
        addPlatePageBtn.Bind(wx.EVT_BUTTON, self.onAddPlatePage)

        addFlaskPageBtn = wx.Button(self, label="Add Flask")
        addFlaskPageBtn.SetBackgroundColour("#33FF33")
        addFlaskPageBtn.Bind(wx.EVT_BUTTON, self.onAddFlaskPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addPlatePageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(addFlaskPageBtn , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddPlatePage(self, event):
        panel = PlateWellPanel(self.notebook, self.plate_next_page_num)
        self.notebook.AddPage(panel, 'Plate: %s'%(self.plate_next_page_num), True)
        self.plate_next_page_num += 1

    def onAddFlaskPage(self, event):
        panel = FlaskPanel(self.notebook, self.flask_next_page_num)
        self.notebook.AddPage(panel, 'Flask: %s'%(self.flask_next_page_num), True)
        self.flask_next_page_num += 1


class PlateWellPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=6, cols=2, hgap=5, vgap=5) 

        #--Design--#
        expPltdesTAG = 'ExptVessel|Plate|Design|'+str(self.page_counter)
        self.settings_controls[expPltdesTAG] = wx.Choice(self.sw, -1, choices=WELL_NAMES_ORDERED)
        for i, format in enumerate([WELL_NAMES[name] for name in WELL_NAMES_ORDERED]):
            self.settings_controls[expPltdesTAG].SetClientData(i, format)
        if meta.get_field(expPltdesTAG) is not None:
            self.settings_controls[expPltdesTAG].SetStringSelection(meta.get_field(expPltdesTAG))
        self.settings_controls[expPltdesTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[expPltdesTAG].SetToolTipString('Design of Plate')
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Design'), 0)
        fgs.Add(self.settings_controls[expPltdesTAG], 0, wx.EXPAND)

        #--Well Shape--#
        expPltshpTAG = 'ExptVessel|Plate|Shape|'+str(self.page_counter)
        self.settings_controls[expPltshpTAG] = wx.Choice(self.sw, -1,  choices=['Square','Round','Oval'])
        if meta.get_field(expPltshpTAG) is not None:
            self.settings_controls[expPltshpTAG].SetStringSelection(meta.get_field(expPltshpTAG))
        self.settings_controls[expPltshpTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[expPltshpTAG].SetToolTipString('Shape of wells in the plate used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Well Shape'), 0)
        fgs.Add(self.settings_controls[expPltshpTAG], 0, wx.EXPAND)

        #--Well Size--#
        expPltsizTAG = 'ExptVessel|Plate|Size|'+str(self.page_counter)
        self.settings_controls[expPltsizTAG] = wx.TextCtrl(self.sw, value=meta.get_field(expPltsizTAG, default=''))
        self.settings_controls[expPltsizTAG].Bind(wx.EVT_TEXT, self.OnSavingData)   	
        self.settings_controls[expPltsizTAG].SetToolTipString('Size of the wells  used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Size of Well (mm)'), 0)
        fgs.Add(self.settings_controls[expPltsizTAG], 0, wx.EXPAND)

        #--Plate Material--#
        expPltmatTAG = 'ExptVessel|Plate|Material|'+str(self.page_counter)
        self.settings_controls[expPltmatTAG] = wx.Choice(self.sw, -1,  choices=['Plastic','Glass'])
        if meta.get_field(expPltmatTAG) is not None:
            self.settings_controls[expPltmatTAG].SetStringSelection(meta.get_field(expPltmatTAG))
        self.settings_controls[expPltmatTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[expPltmatTAG].SetToolTipString('Material of the plate')
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Material'), 0)
        fgs.Add(self.settings_controls[expPltmatTAG], 0, wx.EXPAND)

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
            if ctrl.GetClientData(ctrl.GetSelection()):
                #
                # HACK: A control with ClientData attached are assumed to be
                #       the Plate Design Choice control
                #
                plate_id = 'plate%s'%(tag.rsplit('|', 1)[-1])
                plate_shape = ctrl.GetClientData(ctrl.GetSelection())
                if plate_id not in PlateDesign.get_plate_ids():
                    PlateDesign.add_plate(plate_id, plate_shape)
                else:
                    PlateDesign.set_plate_format(plate_id, plate_shape)
                meta.set_field(tag, ctrl.GetStringSelection())
            else:
                meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())


##---------- Flask Panel----------------##
class FlaskPanel(wx.Panel):
    def __init__(self, parent, page_counter):

        self.settings_controls = {}
        meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.page_counter = page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5) 

        #----------- Plate Labels and Text Controler-------        
        #--Flask Size--#
        expFlksizTAG = 'ExptVessel|Flask|Size|'+str(self.page_counter)
        self.settings_controls[expFlksizTAG] = wx.TextCtrl(self.sw, value=meta.get_field(expFlksizTAG, default=''))
        self.settings_controls[expFlksizTAG].Bind(wx.EVT_TEXT, self.OnSavingData)   
        self.settings_controls[expFlksizTAG].SetToolTipString('Size of the Flask used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Size of Flask (mm)'), 0)
        fgs.Add(self.settings_controls[expFlksizTAG], 0, wx.EXPAND)
        #--Flask Material--#
        expFlkmatTAG = 'ExptVessel|Flask|Material|'+str(self.page_counter)
        self.settings_controls[expFlkmatTAG] = wx.Choice(self.sw, -1,  choices=['Plastic','Glass'])
        if meta.get_field(expFlkmatTAG) is not None:
            self.settings_controls[expFlkmatTAG].SetStringSelection(meta.get_field(expFlkmatTAG))
        self.settings_controls[expFlkmatTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[expFlkmatTAG].SetToolTipString('Material of the Flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Flask Material'), 0)
        fgs.Add(self.settings_controls[expFlkmatTAG], 0, wx.EXPAND)

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
################## CELL TRANSFER SETTING PANEL #########################
########################################################################
class CellTransferSettingPanel(wx.Panel):
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

        # Get all the previously encoded Flowcytometer pages and re-Add them as pages
        cellharv_list = meta.get_field_instances('CellTransfer|Harvest|')
        self.cellharv_next_page_num = 1
        # update the  number of existing cellharvcytometer
        if cellharv_list:
            self.cellharv_next_page_num =  int(cellharv_list[-1])+1
        for cellharv_id in cellharv_list:
            panel = CellHarvestPanel(self.notebook, int(cellharv_id))
            self.notebook.AddPage(panel, 'Cell Harvest Specification No: %s'%(cellharv_id), True)

        addCellSeedPageBtn = wx.Button(self, label="Add Cell Seeding Specification")
        addCellSeedPageBtn.SetBackgroundColour("#33FF33")
        addCellSeedPageBtn.Bind(wx.EVT_BUTTON, self.onAddCellSeedPage)

        addCellHarvestPageBtn = wx.Button(self, label="Add Cell Harvest Specification")
        addCellHarvestPageBtn.SetBackgroundColour("#33FF33")
        addCellHarvestPageBtn.Bind(wx.EVT_BUTTON, self.onAddCellHarvestPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addCellSeedPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(addCellHarvestPageBtn , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddCellSeedPage(self, event):
        panel = CellSeedPanel(self.notebook, self.cellload_next_page_num)
        self.notebook.AddPage(panel, 'Cell Seeding Specification No: %s'%(self.cellload_next_page_num), True)
        self.cellload_next_page_num += 1

    def onAddCellHarvestPage(self, event):
        panel = CellHarvestPanel(self.notebook, self.cellharv_next_page_num)
        self.notebook.AddPage(panel, 'Cell Harvest Specification No: %s'%(self.cellharv_next_page_num), True)
        self.cellharv_next_page_num += 1



class CellSeedPanel(wx.Panel):
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
        celllineselcTAG = 'CellTransfer|Seed|CellLineInstance|'+str(self.page_counter)
        self.settings_controls[celllineselcTAG] = wx.Choice(self.sw, -1,  choices=cell_Line_choices)
        if meta.get_field(celllineselcTAG) is not None:
            self.settings_controls[celllineselcTAG].SetStringSelection(meta.get_field(celllineselcTAG))
        self.settings_controls[celllineselcTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[celllineselcTAG].SetToolTipString('Cell Line used for seeding')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Cell Line'), 0)
        fgs.Add(self.settings_controls[celllineselcTAG], 0, wx.EXPAND)

        # Seeding Density
        seedTAG = 'CellTransfer|Seed|SeedingDensity|'+str(self.page_counter)
        self.settings_controls[seedTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seedTAG, default=''))
        self.settings_controls[seedTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seedTAG].SetToolTipString('Number of cells seeded in each well or flask')
        fgs.Add(wx.StaticText(self.sw, -1, 'Seeding Density'), 0)
        fgs.Add(self.settings_controls[seedTAG], 0, wx.EXPAND)

        # Medium Used
        medmTAG = 'CellTransfer|Seed|MediumUsed|'+str(self.page_counter)
        self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
        if meta.get_field(medmTAG) is not None:
            self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
        self.settings_controls[medmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0)
        fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND) 

        #  Medium Addatives
        medaddTAG = 'CellTransfer|Seed|MediumAddatives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetToolTipString('Any medium addatives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self.sw, -1, 'Medium Addatives'), 0)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)

        # Trypsinization
        trypsTAG = 'CellTransfer|Seed|Trypsinizatiton|'+str(self.page_counter)
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
        celllineselcTAG = 'CellTransfer|Harvest|CellLineInstance|'+str(self.page_counter)
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
################## PERTURBATION SETTING PANEL ###########################
########################################################################	    
class PerturbationSettingPanel(wx.Panel):
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
        addChemAgentPageBtn = wx.Button(self, label="Add Chemical Agent")
        addChemAgentPageBtn.SetBackgroundColour("#33FF33")
        addChemAgentPageBtn.Bind(wx.EVT_BUTTON, self.onAddChemAgentPage)

        addBioAgentPageBtn = wx.Button(self, label="Add Biological Agent")
        addBioAgentPageBtn.SetBackgroundColour("#33FF33")
        addBioAgentPageBtn.Bind(wx.EVT_BUTTON, self.onAddBioAgentPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addChemAgentPageBtn  , 0, wx.ALL, 5)
        btnSizer.Add(addBioAgentPageBtn , 0, wx.ALL, 5)

        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onAddChemAgentPage(self, event):
        panel = ChemicalAgentPanel(self.notebook, self.chemical_next_page_num)
        self.notebook.AddPage(panel, 'Chemical Agent No: %s'%(self.chemical_next_page_num), True)
        self.chemical_next_page_num += 1

    def onAddBioAgentPage(self, event):
        panel = BiologicalAgentPanel(self.notebook, self.bio_next_page_num)
        self.notebook.AddPage(panel, 'Biological Agent No: %s'%(self.bio_next_page_num), True)
        self.bio_next_page_num += 1    


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
        self.settings_controls[concTAG] = wx.TextCtrl(self.sw, -1)
        self.settings_controls[concTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[concTAG].SetToolTipString('Concetration of the Chemical agent used')
        unitTAG = 'Perturbation|Chem|Unit|'+str(self.page_counter)
        self.settings_controls[unitTAG] = wx.Choice(self.sw, -1,  choices=['uM', 'nM', 'mM', 'mg/L'])
        if meta.get_field(unitTAG) is not None:
            self.settings_controls[unitTAG].SetStringSelection(meta.get_field(unitTAG))
        self.settings_controls[unitTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)

        fgs.Add(wx.StaticText(self.sw, -1, 'Concentration'), 0)
        fgs.Add(self.settings_controls[concTAG], 0, wx.EXPAND)
        fgs.Add(self.settings_controls[unitTAG], 0, wx.EXPAND)


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
        fgs.Add(wx.StaticText(self.sw, -1, 'Target GeneAccess Number'), 0)
        fgs.Add(self.settings_controls[tgtgenTAG], 0, wx.EXPAND)
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
        stain_list = meta.get_field_instances('AddProcess|Stain|')
        self.stain_next_page_num = 1
        # update the  number of existing cell loading
        if stain_list: 
            self.stain_next_page_num  =  int(stain_list[-1])+1
        for stain_id in stain_list:
            panel = StainPanel(self.notebook, int(stain_id))
            self.notebook.AddPage(panel, 'Staining Protocol No: %s'%(stain_id), True)

        # Add the buttons
        addStainingPageBtn = wx.Button(self, label="Add Staining Protocols")
        addStainingPageBtn.SetBackgroundColour("#33FF33")
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
        stainnamTAG = 'AddProcess|Stain|StainProtocolTag|'+str(self.page_counter)
        self.settings_controls[stainnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(stainnamTAG, default=''))
        self.settings_controls[stainnamTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[stainnamTAG].SetToolTipString('Staining Agent Name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Staining Agent Name'), 0)
        fgs.Add(self.settings_controls[stainnamTAG], 0, wx.EXPAND)

        # Staining Protocol
        protTAG = 'AddProcess|Stain|Protocol|'+str(self.page_counter)
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
        addSpinningPageBtn.SetBackgroundColour("#33FF33")
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
        addWashingPageBtn.SetBackgroundColour("#33FF33")
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
        addTLMPageBtn.SetBackgroundColour("#33FF33")
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
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
        
        micro_instances = meta.get_field_instances('Instrument|Microscope|Manufacter|')
        micro_choices = []
        for micro_instance in micro_instances:
            micro_choices.append(meta.get_field('Instrument|Microscope|Manufacter|'+micro_instance)+'_'+micro_instance)
 
        #-- Microscope selection ---#
        tlmselctTAG = 'DataAcquis|TLM|MicroscopeInstance|'+str(self.page_counter)
        self.settings_controls[tlmselctTAG] = wx.Choice(self.sw, -1,  choices=micro_choices)
        if meta.get_field(tlmselctTAG) is not None:
            self.settings_controls[tlmselctTAG].SetStringSelection(meta.get_field(tlmselctTAG))
        self.settings_controls[tlmselctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[tlmselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope'), 0)
        fgs.Add(self.settings_controls[tlmselctTAG], 0, wx.EXPAND)
        #-- Image Format ---#
        tlmfrmtTAG = 'DataAcquis|TLM|Format|'+str(self.page_counter)
        self.settings_controls[tlmfrmtTAG] = wx.Choice(self.sw, -1,  choices=['tiff', 'jpeg', 'stk'])
        if meta.get_field(tlmfrmtTAG) is not None:
            self.settings_controls[tlmfrmtTAG].SetStringSelection(meta.get_field(tlmfrmtTAG))
        self.settings_controls[tlmfrmtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[tlmfrmtTAG].SetToolTipString('Image Format')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Image Format'), 0)
        fgs.Add(self.settings_controls[tlmfrmtTAG], 0, wx.EXPAND)
        #-- Channel ---#
        tlmchTAG = 'DataAcquis|TLM|Channel|'+str(self.page_counter)
        self.settings_controls[tlmchTAG] = wx.Choice(self.sw, -1,  choices=['Red', 'Green', 'Blue'])
        if meta.get_field(tlmchTAG) is not None:
            self.settings_controls[tlmchTAG].SetStringSelection(meta.get_field(tlmchTAG))
        self.settings_controls[tlmchTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[tlmchTAG].SetToolTipString('Channel used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
        fgs.Add(self.settings_controls[tlmchTAG], 0, wx.EXPAND)
        #  Time Interval
        tlmintTAG = 'DataAcquis|TLM|TimeInterval|'+str(self.page_counter)
        self.settings_controls[tlmintTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmintTAG, default=''))
        self.settings_controls[tlmintTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmintTAG].SetToolTipString('Time interval image was acquired')
        fgs.Add(wx.StaticText(self.sw, -1, 'Time Interval (min)'), 0)
        fgs.Add(self.settings_controls[tlmintTAG], 0, wx.EXPAND)
        #  Total Frame/Pane Number
        tlmfrmTAG = 'DataAcquis|TLM|FrameNumber|'
        self.settings_controls[tlmfrmTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmfrmTAG, default=''))
        self.settings_controls[tlmfrmTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmfrmTAG].SetToolTipString('Total Frame/Pane Number')
        fgs.Add(wx.StaticText(self.sw, -1, 'Total Frame/Pane Number'), 0)
        fgs.Add(self.settings_controls[tlmfrmTAG], 0, wx.EXPAND)
        #  Stacking Order
        tlmstkTAG = 'DataAcquis|TLM|StackProcess|'+str(self.page_counter)
        self.settings_controls[tlmstkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmstkTAG, default=''))
        self.settings_controls[tlmstkTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmstkTAG].SetToolTipString('Stacking Order')
        fgs.Add(wx.StaticText(self.sw, -1, 'Stacking Order'), 0)
        fgs.Add(self.settings_controls[tlmstkTAG], 0, wx.EXPAND)
        #  Pixel Size
        tlmpxlTAG = 'DataAcquis|TLM|PixelSize|'+str(self.page_counter)
        self.settings_controls[tlmpxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxlTAG, default=''))
        self.settings_controls[tlmpxlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmpxlTAG].SetToolTipString('Pixel Size')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0)
        fgs.Add(self.settings_controls[tlmpxlTAG], 0, wx.EXPAND)
        #  Pixel Conversion
        tlmpxcnvTAG = 'DataAcquis|TLM|PixelConvert|'+str(self.page_counter)
        self.settings_controls[tlmpxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxcnvTAG, default=''))
        self.settings_controls[tlmpxcnvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmpxcnvTAG].SetToolTipString('Pixel Conversion')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0)
        fgs.Add(self.settings_controls[tlmpxcnvTAG], 0, wx.EXPAND)
        #  Software
        tlmsoftTAG = 'DataAcquis|TLM|Software|'+str(self.page_counter)
        self.settings_controls[tlmsoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmsoftTAG, default=''))
        self.settings_controls[tlmsoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[tlmsoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
        fgs.Add(self.settings_controls[tlmsoftTAG], 0, wx.EXPAND)

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
        addHCSPageBtn.SetBackgroundColour("#33FF33")
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
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)

        #-- Microscope selection ---#
        micro_instances = meta.get_field_instances('Instrument|Microscope|Manufacter|')
        micro_choices = []
        for micro_instance in micro_instances:
            micro_choices.append(meta.get_field('Instrument|Microscope|Manufacter|'+micro_instance)+'_'+micro_instance)
 
        tlmselctTAG = 'DataAcquis|HCS|MicroscopeInstance|'+str(self.page_counter)
        self.settings_controls[tlmselctTAG] = wx.Choice(self.sw, -1,  choices=micro_choices)
        if meta.get_field(tlmselctTAG) is not None:
            self.settings_controls[tlmselctTAG].SetStringSelection(meta.get_field(tlmselctTAG))
        self.settings_controls[tlmselctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[tlmselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope'), 0)
        fgs.Add(self.settings_controls[tlmselctTAG], 0, wx.EXPAND)
 
        #-- Image Format ---#
        hcsfrmtTAG = 'DataAcquis|HCS|Format|'+str(self.page_counter)
        self.settings_controls[hcsfrmtTAG] = wx.Choice(self.sw, -1,  choices=['tiff', 'jpeg', 'stk'])
        if meta.get_field(hcsfrmtTAG) is not None:
            self.settings_controls[hcsfrmtTAG].SetStringSelection(meta.get_field(hcsfrmtTAG))
        self.settings_controls[hcsfrmtTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[hcsfrmtTAG].SetToolTipString('Image Format')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Image Format'), 0)
        fgs.Add(self.settings_controls[hcsfrmtTAG], 0, wx.EXPAND)
        #-- Channel ---#
        hcschTAG = 'DataAcquis|HCS|Channel|'+str(self.page_counter)
        self.settings_controls[hcschTAG] = wx.Choice(self.sw, -1,  choices=['Red', 'Green', 'Blue'])
        if meta.get_field(hcschTAG) is not None:
            self.settings_controls[hcschTAG].SetStringSelection(meta.get_field(hcschTAG))
        self.settings_controls[hcschTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[hcschTAG].SetToolTipString('Channel used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
        fgs.Add(self.settings_controls[hcschTAG], 0, wx.EXPAND)
        #  Pixel Size
        hcspxlTAG = 'DataAcquis|HCS|PixelSize|'+str(self.page_counter)
        self.settings_controls[hcspxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxlTAG, default=''))
        self.settings_controls[hcspxlTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcspxlTAG].SetToolTipString('Pixel Size')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0)
        fgs.Add(self.settings_controls[hcspxlTAG], 0, wx.EXPAND)
        #  Pixel Conversion
        hcspxcnvTAG = 'DataAcquis|HCS|PixelConvert|'+str(self.page_counter)
        self.settings_controls[hcspxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxcnvTAG, default=''))
        self.settings_controls[hcspxcnvTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcspxcnvTAG].SetToolTipString('Pixel Conversion')
        fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0)
        fgs.Add(self.settings_controls[hcspxcnvTAG], 0, wx.EXPAND)
        #  Software
        hcssoftTAG = 'DataAcquis|HCS|Software|'+str(self.page_counter)
        self.settings_controls[hcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcssoftTAG, default=''))
        self.settings_controls[hcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[hcssoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
        fgs.Add(self.settings_controls[hcssoftTAG], 0, wx.EXPAND)

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
        addFlowPageBtn.SetBackgroundColour("#33FF33")
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
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)

        #-- FlowCytometer selection ---#
        flow_instances = meta.get_field_instances('Instrument|Flowcytometer|Manufacter|')
        flow_choices = []
        for flow_instance in flow_instances:
            flow_choices.append(meta.get_field('Instrument|Flowcytometer|Manufacter|'+flow_instance)+'_'+flow_instance)
 
        fcsselctTAG = 'DataAcquis|FCS|FlowcytInstance|'+str(self.page_counter)
        self.settings_controls[fcsselctTAG] = wx.Choice(self.sw, -1,  choices=flow_choices)
        if meta.get_field(fcsselctTAG) is not None:
            self.settings_controls[fcsselctTAG].SetStringSelection(meta.get_field(fcsselctTAG))
        self.settings_controls[fcsselctTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[fcsselctTAG].SetToolTipString('Microscope used for data acquisition')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope'), 0)
        fgs.Add(self.settings_controls[fcsselctTAG], 0, wx.EXPAND)
        

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
        #-- Channel ---#
        fcschTAG = 'DataAcquis|FCS|Channel|'+str(self.page_counter)
        self.settings_controls[fcschTAG] = wx.Choice(self.sw, -1,  choices=['FL8', 'FL6', 'FL2'])
        if meta.get_field(fcschTAG) is not None:
            self.settings_controls[fcschTAG].SetStringSelection(meta.get_field(fcschTAG))
        self.settings_controls[fcschTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[fcschTAG].SetToolTipString('Channel used')
        fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
        fgs.Add(self.settings_controls[fcschTAG], 0, wx.EXPAND)
        #  Software
        fcssoftTAG = 'DataAcquis|FCS|Software|'+str(self.page_counter)
        self.settings_controls[fcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(fcssoftTAG, default=''))
        self.settings_controls[fcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[fcssoftTAG].SetToolTipString(' Software')
        fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
        fgs.Add(self.settings_controls[fcssoftTAG], 0, wx.EXPAND)
        self.settings_controls[fcssoftTAG].Bind(wx.EVT_TEXT, self.OnSavingData)

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


def on_save_settings(evt):
    # for saving the experimental file, the text file may have the following nomenclature
    # Date(YYYY_MM_DD)_ExperimenterNumber_Experimenter Name_ first 20 words from the aim

    meta = ExperimentSettings.getInstance()
    
    #-- Get Experimental Date/number ---#
    exp_date = meta.get_field('Overview|Project|ExptDate')
    exp_num = meta.get_field('Overview|Project|ExptNum')
    exp_title = meta.get_field('Overview|Project|Title')
    
    day, month, year =  exp_date.split('/')
    
    dlg = wx.FileDialog(None, message='Saving Experimental metadata...', defaultDir=os.getcwd(), 
                        defaultFile=year+month+day+'_'+exp_num+'_'+exp_title, wildcard='txt', 
                        style=wx.SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        ExperimentSettings.getInstance().save_to_file(dlg.GetPath())

        
def on_load_settings(evt):
    dlg = wx.FileDialog(None, "Select the file containing your CPAnalyst workspace...",
                        defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        ExperimentSettings.getInstance().load_from_file(dlg.GetPath())

        
if __name__ == '__main__':
    app = wx.App(False)
    
    frame = wx.Frame(None, title='Lineageprofiler', size=(650, 750))
    p = ExperimentSettingsWindow(frame)
    
    frame.SetMenuBar(wx.MenuBar())
    fileMenu = wx.Menu()
    saveSettingsMenuItem = fileMenu.Append(-1, 'Save settings\tCtrl+S', help='')
    loadSettingsMenuItem = fileMenu.Append(-1, 'Load settings\tCtrl+O', help='')
    frame.Bind(wx.EVT_MENU, on_save_settings, saveSettingsMenuItem)
    frame.Bind(wx.EVT_MENU, on_load_settings, loadSettingsMenuItem) 
    frame.GetMenuBar().Append(fileMenu, 'File')


    frame.Show()
    app.MainLoop()