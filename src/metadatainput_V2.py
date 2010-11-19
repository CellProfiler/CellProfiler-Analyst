#!/usr/bin/env python

import wx
import  wx.calendar
import wx.lib.agw.flatnotebook as fnb
import wx.lib.mixins.listctrl  as  listmix
from experimentsettings import ExperimentSettings

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
	
        #self.tree.AppendItem(exv, 'Plate')
        #self.tree.AppendItem(exv, 'Flask')

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
        #hvr = self.tree.AppendItem(adp, 'Harvest')
        #self.tree.AppendItem(hvr, 'Skew')
        self.tree.Expand(root)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

        self.settings_container = wx.Panel(self)#MicroscopePanel(self)
        self.settings_container.SetSizer(wx.BoxSizer())
        self.settings_panel = wx.Panel(self)

        self.SetMinimumPaneSize(20)
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
	if meta.get_field(exnumTAG) is None:
	    self.settings_controls[exnumTAG].SetSelection(0)
	else:
	    self.settings_controls[exnumTAG].SetStringSelection(meta.get_field(exnumTAG))
	
	self.settings_controls[exnumTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
	self.settings_controls[exnumTAG].SetToolTipString('Experiment Number....')
	fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Number'), 0)
	fgs.Add(self.settings_controls[exnumTAG], 0, wx.EXPAND)
	# Experiment Date
	#exdateTAG = 'Overview|Project|ExptDate'
	#self.settings_controls[exdateTAG] = wx.DatePickerCtrl(self.sw, style = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.DP_ALLOWNONE )
	#self.settings_controls[exdateTAG].SetToolTipString('Start date of the experiment')
	#fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Start Date'), 0)
	#fgs.Add(self.settings_controls[exdateTAG], 0, wx.EXPAND)
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
	self.settings_controls[statusTAG] = wx.Choice(self.sw, -1,  choices=['Complete', 'Ongoing', 'Pending', 'Discarded'])
	if meta.get_field(statusTAG) is None:
	    self.settings_controls[statusTAG].SetSelection(0)
	else:
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

    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'

	
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
	self.first_type_page_counter = 0
	self.second_type_page_counter = 0
	
	self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)
	
	
	mic_list = meta.get_field_instances('Instrument|Microscope')
	for mic_id in mic_list:
	    panel = MicroscopePanel(self.notebook, int(mic_id))
	    self.notebook.AddPage(panel, 'Microscope: %s'%(mic_id), True)
	flow_list = meta.get_field_instances('Instrument|FlowCytometer')
	for flow_id in flow_list:
	    panel = FlowCytometerPanel(self.notebook, int(flow_id))
	    self.notebook.AddPage(panel, 'Flow Cytometer: %s'%(flow_id), True)
	
	#instrument_list = meta.get_field('Instrument|List', [])
	
	#for inst_id in instrument_list:
	    ##inst_id is of the form: 'instrument_type#'
	    ##   where instrument_type is either 'Microscope' or 'FlowCytometer'
	    #print inst_id
	    #if inst_id.lower().startswith('microscope'):
		#panel = MicroscopePanel(self.notebook, int(inst_id[10:]))
		#self.notebook.AddPage(panel, inst_id, True)
	    #elif inst_id.lower().startswith('flowcytometer'):
		#panel = FlowCytometerPanel(self.notebook, int(inst_id[13:]))
		#self.notebook.AddPage(panel, inst_id, True)
	    #else:
		#raise Exception('Unrecognizable instrument id tag (%s) in '
		                #'Instrument|List.'%(inst_id))
        addFirstTypePageBtn = wx.Button(self, label="Add Microscope")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onAddMicroscopePage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Microscope")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelMicroscopePage)
	
	addSecondTypePageBtn = wx.Button(self, label="Add Flowcytometer")
	addSecondTypePageBtn.SetBackgroundColour("#33FF33")
        addSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onAddFlowcytometerPage)
	rmvSecondTypePageBtn = wx.Button(self, label="Delete Flowcyotometer")
	rmvSecondTypePageBtn.SetBackgroundColour("#FF3300")
        rmvSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFlowcytometerPage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(addSecondTypePageBtn , 0, wx.ALL, 5)
	btnSizer.Add(rmvSecondTypePageBtn , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()
	
    def onAddMicroscopePage(self, event):
	self.first_type_page_counter += 1
        caption = "Microscope No. " + str(self.first_type_page_counter)
	panel = MicroscopePanel(self.notebook, self.first_type_page_counter)
        self.notebook.AddPage(panel, caption, True)

    def onDelMicroscopePage(self, event):
	if self.first_type_page_counter > 0:
	    panel = self.notebook.GetPage(self.notebook.GetSelection())
	    id = panel.first_type_page_counter
	    meta = ExperimentSettings.getInstance()
	    fields = meta.get_field_tags('Instrument|Microscope', instance=str(id))
	    for field in fields:
		meta.remove_field(field)
	    self.notebook.DeletePage(self.notebook.GetSelection())
		
    def onAddFlowcytometerPage(self, event):
	self.second_type_page_counter += 1
        caption = "Flowcyotmeter No. " + str(self.second_type_page_counter)
	panel = FlowCytometerPanel(self.notebook, self.second_type_page_counter)
        self.notebook.AddPage(panel, caption, True)

    def onDelFlowcytometerPage(self, event):
	if self.second_type_page_counter >= 1:
	    self.second_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection())   
	    panel = self.notebook.GetPage(self.notebook.GetSelection())
	    id = panel.first_type_page_counter
	    meta = ExperimentSettings.getInstance()
	    fields = meta.get_field_tags('Instrument|FlowCytometer', instance=str(id))
	    for field in fields:
		meta.remove_field(field)
		
	    
	        #---- Savings the users defined parameters----------#


	
class MicroscopePanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
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
	micromfgTAG = 'Instrument|Microscope|Manufacter|'+str(self.first_type_page_counter)
	self.settings_controls[micromfgTAG] = wx.Choice(self.sw, -1,  choices=['Zeiss','Olympus','Nikon', 'MDS', 'GE'])
	if meta.get_field(micromfgTAG) is not None:
	    self.settings_controls[micromfgTAG].SetStringSelection(meta.get_field(micromfgTAG))
	self.settings_controls[micromfgTAG].SetToolTipString('Manufacturer name')
	fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
	fgs.Add(self.settings_controls[micromfgTAG], 0, wx.EXPAND)
	#--Model--#
	micromdlTAG = 'Instrument|Microscope|Model|'+str(self.first_type_page_counter)
	self.settings_controls[micromdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(micromdlTAG, default=''))
	self.settings_controls[micromdlTAG].SetToolTipString('Model number of the microscope')
	fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
	fgs.Add(self.settings_controls[micromdlTAG], 0, wx.EXPAND)
	#--Microscope type--#
        microtypTAG = 'Instrument|Microscope|Type|'+str(self.first_type_page_counter)
	self.settings_controls[microtypTAG] = wx.Choice(self.sw, -1,  choices=['Upright', 'Inverted', 'Confocal'])
	if meta.get_field(microtypTAG) is None:
	    self.settings_controls[microtypTAG].SetSelection(0)
	else:
	    self.settings_controls[microtypTAG].SetStringSelection(meta.get_field(microtypTAG))
	self.settings_controls[microtypTAG].SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
	fgs.Add(wx.StaticText(self.sw, -1, 'Microscope Type'), 0)
	fgs.Add(self.settings_controls[microtypTAG], 0, wx.EXPAND)
	#--Light source--#
	microlgtTAG = 'Instrument|Microscope|LightSource|'+str(self.first_type_page_counter)
	self.settings_controls[microlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Filament', 'Arc', 'LightEmitingDiode'])
	if meta.get_field(microlgtTAG) is None:
	    self.settings_controls[microlgtTAG].SetSelection(0)
	else:
	    self.settings_controls[microlgtTAG].SetStringSelection(meta.get_field(microlgtTAG))
	self.settings_controls[microlgtTAG].SetToolTipString('e.g. Laser, Filament, Arc, Light Emiting Diode')
	fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
	fgs.Add(self.settings_controls[microlgtTAG], 0, wx.EXPAND)
        #--Detector--#
	microdctTAG = 'Instrument|Microscope|Detector|'+str(self.first_type_page_counter)
	self.settings_controls[microdctTAG] = wx.Choice(self.sw, -1,  choices=['CCD', 'Intensified-CCD', 'Analog-Video', 'Spectroscopy', 'Life-time-imaging', 'Correlation-Spectroscopy', 'FTIR', 'EM-CCD', 'APD', 'CMOS'])
	if meta.get_field(microdctTAG) is None:
	    self.settings_controls[microdctTAG].SetSelection(0)
	else:
	    self.settings_controls[microdctTAG].SetStringSelection(meta.get_field(microlgtTAG))
	self.settings_controls[microdctTAG].SetToolTipString('Type of dectector used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Dectector'), 0)
	fgs.Add(self.settings_controls[microdctTAG], 0, wx.EXPAND)
        #--Lense Aperture--#
	microlnsappTAG = 'Instrument|Microscope|LensApprture|'+str(self.first_type_page_counter)
	self.settings_controls[microlnsappTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(microlnsappTAG, default=''))
	self.settings_controls[microlnsappTAG].SetToolTipString('A floating value of lens numerical aperture')
	fgs.Add(wx.StaticText(self.sw, -1, 'Lense Apparture'), 0)
	fgs.Add(self.settings_controls[microlnsappTAG], 0, wx.EXPAND)
        # Lense Correction
	microlnscorrTAG = 'Instrument|Microscope|LensCorr|'+str(self.first_type_page_counter)
	self.settings_controls[microlnscorrTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if meta.get_field(microlnscorrTAG) is None:
	    self.settings_controls[microlnscorrTAG].SetSelection(0)
	else:
	    self.settings_controls[microlnscorrTAG].SetStringSelection(meta.get_field(microlnscorrTAG))
	self.settings_controls[microlnscorrTAG].SetToolTipString('Yes/No')
	fgs.Add(wx.StaticText(self.sw, -1, 'Lense Correction'), 0)
	fgs.Add(self.settings_controls[microlnscorrTAG], 0, wx.EXPAND)
	#--Illumination Type--#
        microIllTAG = 'Instrument|Microscope|IllumType|'+str(self.first_type_page_counter)
	self.settings_controls[microIllTAG] = wx.Choice(self.sw, -1,  choices=['Transmitted','Epifluorescence','Oblique','NonLinear'])
	if meta.get_field(microIllTAG) is None:
	    self.settings_controls[microIllTAG].SetSelection(0)
	else:
	    self.settings_controls[microIllTAG].SetStringSelection(meta.get_field(microIllTAG))
	self.settings_controls[microIllTAG].SetToolTipString('Type of illumunation used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Illumination Type'), 0)
	fgs.Add(self.settings_controls[microIllTAG], 0, wx.EXPAND)
	#--Mode--#
        microModTAG = 'Instrument|Microscope|Mode|'+str(self.first_type_page_counter)
	self.settings_controls[microModTAG] = wx.Choice(self.sw, -1,  choices=['WideField','LaserScanningMicroscopy', 'LaserScanningConfocal', 'SpinningDiskConfocal', 'SlitScanConfocal', 'MultiPhotonMicroscopy', 'StructuredIllumination','SingleMoleculeImaging', 'TotalInternalReflection', 'FluorescenceLifetime', 'SpectralImaging', 'FluorescenceCorrelationSpectroscopy', 'NearFieldScanningOpticalMicroscopy', 'SecondHarmonicGenerationImaging', 'Timelapse', 'Other'])
	if meta.get_field(microModTAG) is None:
	    self.settings_controls[microModTAG].SetSelection(0)
	else:
	    self.settings_controls[microModTAG].SetStringSelection(meta.get_field(microModTAG))
	self.settings_controls[microModTAG].SetToolTipString('Mode of the microscope')
	fgs.Add(wx.StaticText(self.sw, -1, 'Mode'), 0)
	fgs.Add(self.settings_controls[microModTAG], 0, wx.EXPAND)
        #--Immersion--#
        microImmTAG = 'Instrument|Microscope|Immersion|'+str(self.first_type_page_counter)
	self.settings_controls[microImmTAG] = wx.Choice(self.sw, -1,  choices=['Oil', 'Water', 'WaterDipping', 'Air', 'Multi', 'Glycerol', 'Other', 'Unkonwn'])
	if meta.get_field(microImmTAG) is None:
	    self.settings_controls[microImmTAG].SetSelection(0)
	else:
	    self.settings_controls[microImmTAG].SetStringSelection(meta.get_field(microImmTAG))
	self.settings_controls[microImmTAG].SetToolTipString('Immersion medium used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
	fgs.Add(self.settings_controls[microImmTAG], 0, wx.EXPAND)
        #--Correction--#
        microCorrTAG = 'Instrument|Microscope|Correction|'+str(self.first_type_page_counter)
	self.settings_controls[microCorrTAG] = wx.Choice(self.sw, -1,  choices=['UV', 'PlanApo', 'PlanFluor', 'SuperFluor', 'VioletCorrected', 'Unknown'])
	if meta.get_field(microCorrTAG) is None:
	    self.settings_controls[microCorrTAG].SetSelection(0)
	else:
	    self.settings_controls[microCorrTAG].SetStringSelection(meta.get_field(microCorrTAG))
	self.settings_controls[microCorrTAG].SetToolTipString('Lense correction used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
	fgs.Add(self.settings_controls[microCorrTAG], 0, wx.EXPAND)
        #--Nominal Magnification--#
        microNmgTAG = 'Instrument|Microscope|NominalMagnification|'+str(self.first_type_page_counter)
	self.settings_controls[microNmgTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microNmgTAG, default=''))
	self.settings_controls[microNmgTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
	fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
	fgs.Add(self.settings_controls[microNmgTAG], 0, wx.EXPAND)
        # Calibrated Magnification
        microCalTAG = 'Instrument|Microscope|CalibratedMagnification|'+str(self.first_type_page_counter)
	self.settings_controls[microCalTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCalTAG, default=''))
	self.settings_controls[microCalTAG].SetToolTipString('The magnification of the lens as measured by a calibration process- i.e. 59.987 for a 60X lens')
	fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
	fgs.Add(self.settings_controls[microCalTAG], 0, wx.EXPAND)
        #--Working distance--#
        microWrkTAG = 'Instrument|Microscope|WorkDistance|'+str(self.first_type_page_counter)
	self.settings_controls[microWrkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microWrkTAG, default=''))
	self.settings_controls[microWrkTAG].SetToolTipString('The working distance of the lens expressed as a floating point (real) number. Units are um')
	fgs.Add(wx.StaticText(self.sw, -1, 'Working Distance (uM)'), 0)
	fgs.Add(self.settings_controls[microWrkTAG], 0, wx.EXPAND)
        #--Filter used--#
        microFltTAG = 'Instrument|Microscope|Filter|'+str(self.first_type_page_counter)
	self.settings_controls[microFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if meta.get_field(microFltTAG) is None:
	    self.settings_controls[microFltTAG].SetSelection(0)
	else:
	    self.settings_controls[microFltTAG].SetStringSelection(meta.get_field(microFltTAG))
	self.settings_controls[microFltTAG].SetToolTipString('Whether filter was used or not')
	fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
	fgs.Add(self.settings_controls[microFltTAG], 0, wx.EXPAND)
        #--Software--#
        microSoftTAG = 'Instrument|Microscope|Software|'+str(self.first_type_page_counter)
	self.settings_controls[microSoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microSoftTAG, default=''))
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
        microTempTAG = 'Instrument|Microscope|Temp|'+str(self.first_type_page_counter)
	self.settings_controls[microTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microTempTAG, default=''))
	self.settings_controls[microTempTAG].SetToolTipString('Temperature of the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
	fgs.Add(self.settings_controls[microTempTAG], 0, wx.EXPAND)
	#--Carbondioxide--#
        microCarbonTAG = 'Instrument|Microscope|C02|'+str(self.first_type_page_counter)
	self.settings_controls[microCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microCarbonTAG, default=''))
	self.settings_controls[microCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
	fgs.Add(self.settings_controls[microCarbonTAG], 0, wx.EXPAND)
	#--Humidity--#
        microHumTAG = 'Instrument|Microscope|Humidity|'+str(self.first_type_page_counter)
	self.settings_controls[microHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microHumTAG, default=''))
	self.settings_controls[microHumTAG].SetToolTipString('Humidity at the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
	fgs.Add(self.settings_controls[microHumTAG], 0, wx.EXPAND)
	#--Pressure--#
        microPressTAG = 'Instrument|Microscope|Pressure|'+str(self.first_type_page_counter)
	self.settings_controls[microPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(microPressTAG, default=''))
	self.settings_controls[microPressTAG].SetToolTipString('Pressure at the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
	fgs.Add(self.settings_controls[microPressTAG], 0, wx.EXPAND)
	
	
        #--Create the Adding button--#
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	addBut = wx.Button(self.sw, -1, label="Record Microscope %s settings" % self.first_type_page_counter)
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'


class FlowCytometerPanel(wx.Panel):
    def __init__(self, parent, second_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.second_type_page_counter = second_page_counter
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
	flowmfgTAG = 'Instrument|Flowcytometer|Manufacter|'+str(self.second_type_page_counter)
	self.settings_controls[flowmfgTAG] = wx.Choice(self.sw, -1,  choices=['Beckman','BD-Biosciences'])
	if meta.get_field(flowmfgTAG) is None:
	    self.settings_controls[flowmfgTAG].SetSelection(0)
	else:
	    self.settings_controls[flowmfgTAG].SetStringSelection(meta.get_field(flowmfgTAG))
	self.settings_controls[flowmfgTAG].SetToolTipString('Manufacturer name')
	fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
	fgs.Add(self.settings_controls[flowmfgTAG], 0, wx.EXPAND)
	#--Model--#
	flowmdlTAG = 'Instrument|Flowcytometer|Model|'+str(self.second_type_page_counter)
	self.settings_controls[flowmdlTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(flowmdlTAG, default=''))
	self.settings_controls[flowmdlTAG].SetToolTipString('Model number of the Flowcytometer')
	fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
	fgs.Add(self.settings_controls[flowmdlTAG], 0, wx.EXPAND)
	#--Flowcytometer type--#
        flowtypTAG = 'Instrument|Flowcytometer|Type|'+str(self.second_type_page_counter)
	self.settings_controls[flowtypTAG] = wx.Choice(self.sw, -1,  choices=['Stream-in-air', 'cuvette'])
	if meta.get_field(flowtypTAG) is None:
	    self.settings_controls[flowtypTAG].SetSelection(0)
	else:
	    self.settings_controls[flowtypTAG].SetStringSelection(meta.get_field(flowtypTAG))
	self.settings_controls[flowtypTAG].SetToolTipString('Type of flowcytometer')
	fgs.Add(wx.StaticText(self.sw, -1, 'Flowcytometer Type'), 0)
	fgs.Add(self.settings_controls[flowtypTAG], 0, wx.EXPAND)
	#--Light source--#
	flowlgtTAG = 'Instrument|Flowcytometer|LightSource|'+str(self.second_type_page_counter)
	self.settings_controls[flowlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Beam'])
	if meta.get_field(flowlgtTAG) is None:
	    self.settings_controls[flowlgtTAG].SetSelection(0)
	else:
	    self.settings_controls[flowlgtTAG].SetStringSelection(meta.get_field(flowlgtTAG))
	self.settings_controls[flowlgtTAG].SetToolTipString('Light source of the flowcytometer')
	fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
	fgs.Add(self.settings_controls[flowlgtTAG], 0, wx.EXPAND)
        #--Detector--#
	flowdctTAG = 'Instrument|Flowcytometer|Detector|'+str(self.second_type_page_counter)
	self.settings_controls[flowdctTAG] = wx.Choice(self.sw, -1,  choices=['PhotoMultiplierTube', 'FluorescentDetectors'])
	if meta.get_field(flowdctTAG) is None:
	    self.settings_controls[flowdctTAG].SetSelection(0)
	else:
	    self.settings_controls[flowdctTAG].SetStringSelection(meta.get_field(flowlgtTAG))
	self.settings_controls[flowdctTAG].SetToolTipString('Type of dectector used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Dectector'), 0)
	fgs.Add(self.settings_controls[flowdctTAG], 0, wx.EXPAND)
	#--Filter used--#
        flowFltTAG = 'Instrument|Flowcytometer|Filter|'+str(self.second_type_page_counter)
	self.settings_controls[flowFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if meta.get_field(flowFltTAG) is None:
	    self.settings_controls[flowFltTAG].SetSelection(0)
	else:
	    self.settings_controls[flowFltTAG].SetStringSelection(meta.get_field(flowFltTAG))
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
        flowTempTAG = 'Instrument|Flowcytometer|Temp|'+str(self.second_type_page_counter)
	self.settings_controls[flowTempTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowTempTAG, default=''))
	self.settings_controls[flowTempTAG].SetToolTipString('Temperature of the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'Temperature (C)'), 0)
	fgs.Add(self.settings_controls[flowTempTAG], 0, wx.EXPAND)
	#--Carbondioxide--#
        flowCarbonTAG = 'Instrument|Flowcytometer|C02|'+str(self.second_type_page_counter)
	self.settings_controls[flowCarbonTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowCarbonTAG, default=''))
	self.settings_controls[flowCarbonTAG].SetToolTipString('Carbondioxide percentage at the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'CO2 %'), 0)
	fgs.Add(self.settings_controls[flowCarbonTAG], 0, wx.EXPAND)
	#--Humidity--#
        flowHumTAG = 'Instrument|Flowcytometer|Humidity|'+str(self.second_type_page_counter)
	self.settings_controls[flowHumTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowHumTAG, default=''))
	self.settings_controls[flowHumTAG].SetToolTipString('Humidity at the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'Humidity'), 0)
	fgs.Add(self.settings_controls[flowHumTAG], 0, wx.EXPAND)
	#--Pressure--#
        flowPressTAG = 'Instrument|Flowcytometer|Pressure|'+str(self.second_type_page_counter)
	self.settings_controls[flowPressTAG] = wx.TextCtrl(self.sw, value=meta.get_field(flowPressTAG, default=''))
	self.settings_controls[flowPressTAG].SetToolTipString('Pressure at the incubator')
	fgs.Add(wx.StaticText(self.sw, -1, 'Pressure'), 0)
	fgs.Add(self.settings_controls[flowPressTAG], 0, wx.EXPAND)
	
	
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Flowcytometer %s settings" % self.second_type_page_counter)
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'
        
########################################################################        
################## EXPERIMENT VESSEL SETTING PANEL  ####################
########################################################################	    
class ExpVessSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        
        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id)
        
        # create some widgets
	self.first_type_page_counter = 0
	self.second_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)
        
        addFirstTypePageBtn = wx.Button(self, label="Add Plate")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Plate")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)
	
	addSecondTypePageBtn = wx.Button(self, label="Add Flask")
	addSecondTypePageBtn.SetBackgroundColour("#33FF33")
        addSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onSecondTypeAddPage)
	rmvSecondTypePageBtn = wx.Button(self, label="Delete Flask")
	rmvSecondTypePageBtn.SetBackgroundColour("#FF3300")
        rmvSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelSecondTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(addSecondTypePageBtn , 0, wx.ALL, 5)
	btnSizer.Add(rmvSecondTypePageBtn , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Plate No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return PlateWellPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 
	
    def onSecondTypeAddPage(self, event):
	self.second_type_page_counter += 1
        caption = "Flask No. " + str(self.second_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createSecondTypePage(caption), caption, True)
        self.Thaw()
    def createSecondTypePage(self, caption):
	return FlaskPanel(self.notebook, self.second_type_page_counter)
    def onDelSecondTypePage(self, event):
	if self.second_type_page_counter >= 1:
	    self.second_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection())   

class PlateWellPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter

        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=6, cols=2, hgap=5, vgap=5) 

        #----------- Plate Labels and Text Controler-------        
	##--Plate Number--#
	#expPltnumTAG = 'ExptVessel|Plate|Number'
	#self.settings_controls[expPltnumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
	#if meta.get_field(expPltnumTAG) is None:
	    #self.settings_controls[expPltnumTAG].SetSelection(0)
	#else:
	    #self.settings_controls[expPltnumTAG].SetStringSelection(meta.get_field(expPltnumTAG))
	#self.settings_controls[expPltnumTAG].SetToolTipString('Number of Plate used')
	#fgs.Add(wx.StaticText(self.sw, -1, 'Total number of Plate used'), 0)
	#fgs.Add(self.settings_controls[expPltnumTAG], 0, wx.EXPAND)
	
	#--Design--#
	expPltdesTAG = 'ExptVessel|Plate|Design'
	self.settings_controls[expPltdesTAG] = wx.Choice(self.sw, -1,  choices=['6-Well-(2x3)', '96-Well-(8x12)', '384-Well-(16x24)', '1536-Well-(32x48)', '5600-Well-(40x140)'])
	if meta.get_field(expPltdesTAG) is None:
	    self.settings_controls[expPltdesTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltdesTAG].SetStringSelection(meta.get_field(expPltdesTAG))
	self.settings_controls[expPltdesTAG].SetToolTipString('Design of Plate')
	fgs.Add(wx.StaticText(self.sw, -1, 'Plate Design'), 0)
	fgs.Add(self.settings_controls[expPltdesTAG], 0, wx.EXPAND)
        
	#--Well Shape--#
	expPltshpTAG = 'ExptVessel|Plate|Shape'
	self.settings_controls[expPltshpTAG] = wx.Choice(self.sw, -1,  choices=['Square','Round','Oval'])
	if meta.get_field(expPltshpTAG) is None:
	    self.settings_controls[expPltshpTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltshpTAG].SetStringSelection(meta.get_field(expPltshpTAG))
	self.settings_controls[expPltshpTAG].SetToolTipString('Shape of wells in the plate used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Well Shape'), 0)
	fgs.Add(self.settings_controls[expPltshpTAG], 0, wx.EXPAND)
	
	#--Well Size--#
	expPltsizTAG = 'ExptVessel|Plate|Size'
	self.settings_controls[expPltsizTAG] = wx.TextCtrl(self.sw, value=meta.get_field(expPltsizTAG, default=''))
	self.settings_controls[expPltsizTAG].SetToolTipString('Size of the wells  used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Size of Well (mm)'), 0)
	fgs.Add(self.settings_controls[expPltsizTAG], 0, wx.EXPAND)
	
	#--Plate Material--#
	expPltmatTAG = 'ExptVessel|Plate|Material'
	self.settings_controls[expPltmatTAG] = wx.Choice(self.sw, -1,  choices=['Plastic','Glass'])
	if meta.get_field(expPltmatTAG) is None:
	    self.settings_controls[expPltmatTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltmatTAG].SetStringSelection(meta.get_field(expPltmatTAG))
	self.settings_controls[expPltmatTAG].SetToolTipString('Material of the plate')
	fgs.Add(wx.StaticText(self.sw, -1, 'Plate Material'), 0)
	fgs.Add(self.settings_controls[expPltmatTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Plate Settings")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'

##---------- Flask Panel----------------##
class FlaskPanel(wx.Panel):
    def __init__(self, parent, second_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.second_type_page_counter = second_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5) 

        #----------- Plate Labels and Text Controler-------        
	##--Flask Number--#
	#expFlknumTAG = 'ExptVessel|Flask|Number'
	#self.settings_controls[expFlknumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
	#if meta.get_field(expFlknumTAG) is None:
	    #self.settings_controls[expFlknumTAG].SetSelection(0)
	#else:
	    #self.settings_controls[expFlknumTAG].SetStringSelection(meta.get_field(expFlknumTAG))
	#self.settings_controls[expFlknumTAG].SetToolTipString('Number of Flasks used')
	#fgs.Add(wx.StaticText(self.sw, -1, 'Total number of Flask used'), 0)
	#fgs.Add(self.settings_controls[expFlknumTAG], 0, wx.EXPAND)
        #--Flask Size--#
	expFlksizTAG = 'ExptVessel|Flask|Size'
	self.settings_controls[expFlksizTAG] = wx.TextCtrl(self.sw, value=meta.get_field(expFlksizTAG, default=''))
	self.settings_controls[expFlksizTAG].SetToolTipString('Size of the Flask used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Size of Flask (mm)'), 0)
	fgs.Add(self.settings_controls[expFlksizTAG], 0, wx.EXPAND)
        #--Flask Material--#
	expFlkmatTAG = 'ExptVessel|Flask|Material'
	self.settings_controls[expFlkmatTAG] = wx.Choice(self.sw, -1,  choices=['Plastic','Glass'])
	if meta.get_field(expFlkmatTAG) is None:
	    self.settings_controls[expFlkmatTAG].SetSelection(0)
	else:
	    self.settings_controls[expFlkmatTAG].SetStringSelection(meta.get_field(expFlkmatTAG))
	self.settings_controls[expFlkmatTAG].SetToolTipString('Material of the Flask')
	fgs.Add(wx.StaticText(self.sw, -1, 'Flask Material'), 0)
	fgs.Add(self.settings_controls[expFlkmatTAG], 0, wx.EXPAND)
        
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Flask Settings")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'        
        
        
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
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)
        
        addFirstTypePageBtn = wx.Button(self, label="Add Stock Culture")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Stock Culture")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Stock Culture No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return StockCulturePanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

	    
class StockCulturePanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5) 



        #----------- Labels and Text Controler-------        
	# Cell Line Name
        cellLineTAG = 'StockCulture|Sample|CellLine'
	self.settings_controls[cellLineTAG] = wx.TextCtrl(self.sw, value=meta.get_field(cellLineTAG, default=''))
	self.settings_controls[cellLineTAG].SetToolTipString('Cell Line selection')
	fgs.Add(wx.StaticText(self.sw, -1, 'Cell Line'), 0)
	fgs.Add(self.settings_controls[cellLineTAG], 0, wx.EXPAND)        
        
        # Taxonomic ID
	taxIdTAG = 'StockCulture|Sample|TaxID'
	self.settings_controls[taxIdTAG] = wx.Choice(self.sw, -1,  choices=['HomoSapiens(9606)', 'MusMusculus(10090)', 'RattusNorvegicus(10116)'])
	if meta.get_field(taxIdTAG) is None:
	    self.settings_controls[taxIdTAG].SetSelection(0)
	else:
	    self.settings_controls[taxIdTAG].SetStringSelection(meta.get_field(taxIdTAG))
	self.settings_controls[taxIdTAG].SetToolTipString('Taxonomic ID of the species')
	fgs.Add(wx.StaticText(self.sw, -1, 'Organism'), 0)
	fgs.Add(self.settings_controls[taxIdTAG], 0, wx.EXPAND)
	
	# Gender
	gendTAG = 'StockCulture|Sample|Gender'
	self.settings_controls[gendTAG] = wx.Choice(self.sw, -1,  choices=['Male', 'Female', 'Neutral'])
	if meta.get_field(gendTAG) is None:
	    self.settings_controls[gendTAG].SetSelection(0)
	else:
	    self.settings_controls[gendTAG].SetStringSelection(meta.get_field(gendTAG))
	self.settings_controls[gendTAG].SetToolTipString('Gender of the organism')
	fgs.Add(wx.StaticText(self.sw, -1, 'Gender'), 0)
	fgs.Add(self.settings_controls[gendTAG], 0, wx.EXPAND)        
	
	# Age
        ageTAG ='StockCulture|Sample|Age'
        self.settings_controls[ageTAG] = wx.TextCtrl(self.sw, value=meta.get_field(ageTAG, default=''))
	self.settings_controls[ageTAG].SetToolTipString('Age of the organism in days when the cells were collected. .')
	fgs.Add(wx.StaticText(self.sw, -1, 'Age of organism (days)'), 0)
	fgs.Add(self.settings_controls[ageTAG], 0, wx.EXPAND)
	
	# Organ
	organTAG = 'StockCulture|Sample|Organ'
	self.settings_controls[organTAG] = wx.TextCtrl(self.sw, value=meta.get_field(organTAG, default=''))
	self.settings_controls[organTAG].SetToolTipString('Organ name from where the cell were collected. eg. Heart, Lung, Bone etc')
	fgs.Add(wx.StaticText(self.sw, -1, 'Organ'), 0)
	fgs.Add(self.settings_controls[organTAG], 0, wx.EXPAND)
	
	# Tissue
	tissueTAG = 'StockCulture|Sample|Tissue'
	self.settings_controls[tissueTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tissueTAG, default=''))
	self.settings_controls[tissueTAG].SetToolTipString('Tissue from which the cells were collected')
	fgs.Add(wx.StaticText(self.sw, -1, 'Tissue'), 0)
	fgs.Add(self.settings_controls[tissueTAG], 0, wx.EXPAND)
	
	# Pheotype
	phtypTAG = 'StockCulture|Sample|Phenotype'
	self.settings_controls[phtypTAG] = wx.TextCtrl(self.sw, value=meta.get_field(phtypTAG, default=''))
	self.settings_controls[phtypTAG].SetToolTipString('Phenotypic examples Colour Height OR any other value descriptor')
	fgs.Add(wx.StaticText(self.sw, -1, 'Phenotype'), 0)
	fgs.Add(self.settings_controls[phtypTAG], 0, wx.EXPAND)
	
	# Genotype
	gentypTAG = 'StockCulture|Sample|Genotype'
	self.settings_controls[gentypTAG] = wx.TextCtrl(self.sw, value=meta.get_field(gentypTAG, default=''))
	self.settings_controls[gentypTAG].SetToolTipString('Wild type or mutant etc. (single word)')
	fgs.Add(wx.StaticText(self.sw, -1, 'Genotype'), 0)
	fgs.Add(self.settings_controls[gentypTAG], 0, wx.EXPAND)
	
	# Strain
	strainTAG = 'StockCulture|Sample|Strain'
	self.settings_controls[strainTAG] = wx.TextCtrl(self.sw, value=meta.get_field(strainTAG, default=''))
	self.settings_controls[strainTAG].SetToolTipString('Starin of that cell line eGFP, Wild type etc')
	fgs.Add(wx.StaticText(self.sw, -1, 'Strain'), 0)
	fgs.Add(self.settings_controls[strainTAG], 0, wx.EXPAND)
	
	#  Passage Number
	passTAG = 'StockCulture|Sample|PassageNumber'
	self.settings_controls[passTAG] = wx.TextCtrl(self.sw, value=meta.get_field(passTAG, default=''))
	self.settings_controls[passTAG].SetToolTipString('Numeric value of the passage of the cells under investigation')
	fgs.Add(wx.StaticText(self.sw, -1, 'Passage Number'), 0)
	fgs.Add(self.settings_controls[passTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Stock Culture")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)

        
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 

########################################################################        
################## CELL TRANSFER SETTING PANEL #########################
########################################################################
class CellTransferSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id)

        # create some widgets
	self.first_type_page_counter = 0
	self.second_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add Cell Loading Sequence")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Cell Loading Sequence")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)
	
	addSecondTypePageBtn = wx.Button(self, label="Add Cell Harvesting Sequence")
	addSecondTypePageBtn.SetBackgroundColour("#33FF33")
        addSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onSecondTypeAddPage)
	rmvSecondTypePageBtn = wx.Button(self, label="Delete Cell Harvesting Sequence")
	rmvSecondTypePageBtn.SetBackgroundColour("#FF3300")
        rmvSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelSecondTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(addSecondTypePageBtn , 0, wx.ALL, 5)
	btnSizer.Add(rmvSecondTypePageBtn , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Cell Loading Sequence No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return CellLoadPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 
	
    def onSecondTypeAddPage(self, event):
	self.second_type_page_counter += 1
        caption = "Cell Harvesting Sequence No. " + str(self.second_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createSecondTypePage(caption), caption, True)
        self.Thaw()
    def createSecondTypePage(self, caption):
	return CellHarvestPanel(self.notebook, self.second_type_page_counter)
    def onDelSecondTypePage(self, event):
	if self.second_type_page_counter >= 1:
	    self.second_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 


class CellLoadPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5) 
	
	# Seeding Density
	seedTAG = 'CellTransfer|Load|SeedingDensity'
	self.settings_controls[seedTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seedTAG, default=''))
	self.settings_controls[seedTAG].SetToolTipString('Number of cells seeded in each well or flask')
	fgs.Add(wx.StaticText(self.sw, -1, 'Seeding Density'), 0)
	fgs.Add(self.settings_controls[seedTAG], 0, wx.EXPAND)
		
	# Medium Used
	medmTAG = 'CellTransfer|Load|MediumUsed'
	self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
	if meta.get_field(medmTAG) is None:
	    self.settings_controls[medmTAG].SetSelection(0)
	else:
	    self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
	self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
	fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0)
	fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND) 
	
	#  Medium Addatives
	medaddTAG = 'CellTransfer|Load|MediumAddatives'
	self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
	self.settings_controls[medaddTAG].SetToolTipString('Any medium addatives used with concentration, Glutamine')
	fgs.Add(wx.StaticText(self.sw, -1, 'Medium Addatives'), 0)
	fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)
	
	# Trypsinization
	trypsTAG = 'CellTransfer|Load|Trypsinizatiton'
	self.settings_controls[trypsTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if meta.get_field(trypsTAG) is None:
	    self.settings_controls[trypsTAG].SetSelection(0)
	else:
	    self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
	self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
	fgs.Add(wx.StaticText(self.sw, -1, 'Trypsinization'), 0)
	fgs.Add(self.settings_controls[trypsTAG], 0, wx.EXPAND)  
       
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Loading Variables")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 
      
        
class CellHarvestPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	# Seeding Density
	seedTAG = 'CellTransfer|Harvest|HarvestingDensity'
	self.settings_controls[seedTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seedTAG, default=''))
	self.settings_controls[seedTAG].SetToolTipString('Number of cells harvested from each well or flask')
	fgs.Add(wx.StaticText(self.sw, -1, 'Harvesting Density'), 0)
	fgs.Add(self.settings_controls[seedTAG], 0, wx.EXPAND)
		
	# Medium Used
	medmTAG = 'CellTransfer|Harvest|MediumUsed'
	self.settings_controls[medmTAG] = wx.Choice(self.sw, -1,  choices=['Typical', 'Atypical'])
	if meta.get_field(medmTAG) is None:
	    self.settings_controls[medmTAG].SetSelection(0)
	else:
	    self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
	self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
	fgs.Add(wx.StaticText(self.sw, -1, 'Medium Used'), 0)
	fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND) 
	
	#  Medium Addatives
	medaddTAG = 'CellTransfer|Harvest|MediumAddatives'
	self.settings_controls[medaddTAG] = wx.TextCtrl(self.sw, value=meta.get_field(medaddTAG, default=''))
	self.settings_controls[medaddTAG].SetToolTipString('Any medium addatives used with concentration, Glutamine')
	fgs.Add(wx.StaticText(self.sw, -1, 'Medium Addatives'), 0)
	fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)
	
	# Trypsinization
	trypsTAG = 'CellTransfer|Harvest|Trypsinizatiton'
	self.settings_controls[trypsTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if meta.get_field(trypsTAG) is None:
	    self.settings_controls[trypsTAG].SetSelection(0)
	else:
	    self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
	self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
	fgs.Add(wx.StaticText(self.sw, -1, 'Trypsinization'), 0)
	fgs.Add(self.settings_controls[trypsTAG], 0, wx.EXPAND)  
       
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Harvesting variable")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()

	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 

	    
########################################################################        
################## PERTURBATION SETTING PANEL ###########################
########################################################################	    
class PerturbationSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):

        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
	
        wx.Panel.__init__(self, parent, id)

        # create some widgets
	self.first_type_page_counter = 0
	self.second_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add Chemical Agent")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Chemical Agent")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)
	
	addSecondTypePageBtn = wx.Button(self, label="Add Biological Agent")
	addSecondTypePageBtn.SetBackgroundColour("#33FF33")
        addSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onSecondTypeAddPage)
	rmvSecondTypePageBtn = wx.Button(self, label="Delete Biological Agent")
	rmvSecondTypePageBtn.SetBackgroundColour("#FF3300")
        rmvSecondTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelSecondTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(addSecondTypePageBtn , 0, wx.ALL, 5)
	btnSizer.Add(rmvSecondTypePageBtn , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Chemical Agent No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return ChemicalAgentPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 
	
    def onSecondTypeAddPage(self, event):
	self.second_type_page_counter += 1
        caption = "Biological Agent No. " + str(self.second_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createSecondTypePage(caption), caption, True)
        self.Thaw()
    def createSecondTypePage(self, caption):
	return BiologicalAgentPanel(self.notebook, self.second_type_page_counter)
    def onDelSecondTypePage(self, event):
	if self.second_type_page_counter >= 1:
	    self.second_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 
	    
class ChemicalAgentPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)
	
	#  Chem Agent Name
	chemnamTAG = 'Perturbation|Chem|ChemName'
	self.settings_controls[chemnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(chemnamTAG, default=''))
	self.settings_controls[chemnamTAG].SetToolTipString('Name of the Chemical agent used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Chemical Agent Name'), 0)
	fgs.Add(self.settings_controls[chemnamTAG], 0, wx.EXPAND)
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	#  Chem Concentration and Unit
	concTAG = 'Perturbation|Chem|Conc'
	self.settings_controls[concTAG] = wx.TextCtrl(self.sw, -1)
	self.settings_controls[concTAG].SetToolTipString('Concetration of the Chemical agent used')
	unitTAG = 'Perturbation|Chem|Unit'
	self.settings_controls[unitTAG] = wx.Choice(self.sw, -1,  choices=['uM', 'nM', 'mM', 'mg/L'])
	if meta.get_field(unitTAG) is None:
	    self.settings_controls[unitTAG].SetSelection(0)
	else:
	    self.settings_controls[unitTAG].SetStringSelection(meta.get_field(unitTAG))
	    
	
	fgs.Add(wx.StaticText(self.sw, -1, 'Concentration'), 0)
	fgs.Add(self.settings_controls[concTAG], 0, wx.EXPAND)
	fgs.Add(self.settings_controls[unitTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Chemical Agent")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 
	

class BiologicalAgentPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=3, hgap=5, vgap=5)
	
	#  RNAi Sequence
	seqnamTAG = 'Perturbation|Bio|SeqName'
	self.settings_controls[seqnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seqnamTAG, default=''))
	self.settings_controls[seqnamTAG].SetToolTipString('Sequence of the RNAi')
	fgs.Add(wx.StaticText(self.sw, -1, 'RNAi Sequence'), 0)
	fgs.Add(self.settings_controls[seqnamTAG], 0, wx.EXPAND)
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	#  Sequence accession number
	seqacssTAG = 'Perturbation|Bio|AccessNumber'
	self.settings_controls[seqacssTAG] = wx.TextCtrl(self.sw, value=meta.get_field(seqacssTAG, default=''))
	self.settings_controls[seqacssTAG].SetToolTipString('Sequence Accession Number')
	fgs.Add(wx.StaticText(self.sw, -1, 'Sequence Accession Number'), 0)
	fgs.Add(self.settings_controls[seqacssTAG], 0, wx.EXPAND)
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	#  Target GeneAccessNumber
	tgtgenTAG = 'Perturbation|Bio|TargetGeneAccessNum'
	self.settings_controls[tgtgenTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tgtgenTAG, default=''))
	self.settings_controls[tgtgenTAG].SetToolTipString('Target GeneAccessNumber')
	fgs.Add(wx.StaticText(self.sw, -1, 'Target GeneAccess Number'), 0)
	fgs.Add(self.settings_controls[tgtgenTAG], 0, wx.EXPAND)
	fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Biological Agent")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 

        
########################################################################        
################## STAINING SETTING PANEL    ###########################
########################################################################
class StainingAgentSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        
        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id)
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add Staining Agent")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Staining Agent")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Staining Agent No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return StainPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

class StainPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	
	#  Staining Agent Name
	stainnamTAG = 'Staining|StaingAgent|SAName'
	self.settings_controls[stainnamTAG] = wx.TextCtrl(self.sw, value=meta.get_field(stainnamTAG, default=''))
	self.settings_controls[stainnamTAG].SetToolTipString('Staining Agent Name')
	fgs.Add(wx.StaticText(self.sw, -1, 'Staining Agent Name'), 0)
	fgs.Add(self.settings_controls[stainnamTAG], 0, wx.EXPAND)
	
	# Staining Protocol
	protTAG = 'Staining|StaingAgent|Protocol'
	self.settings_controls[protTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(protTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[protTAG].SetInitialSize((300, 400))

	self.settings_controls[protTAG].SetToolTipString('Cut and paste your Staining Protocol here')
	fgs.Add(wx.StaticText(self.sw, -1, 'Paste Staining Protocol'), 0)
	fgs.Add(self.settings_controls[protTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Staining Agent")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()

	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 


########################################################################        
################## SPINNING SETTING PANEL    ###########################
########################################################################
class SpinningSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):

        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent, id)
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add Spinning Protocol")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Spinning Protocol")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Spinning Protocol No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return SpinPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

class SpinPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	
	#  Staining Agent Name
	spinTAG = 'AddProcess|Spin|SpinPrtocolTag'
	self.settings_controls[spinTAG] = wx.TextCtrl(self.sw, value=meta.get_field(spinTAG, default=''))
	self.settings_controls[spinTAG].SetToolTipString('Type an unique TAG for identifying the spinning protocol')
	fgs.Add(wx.StaticText(self.sw, -1, 'Spinning Protocol Tag'), 0)
	fgs.Add(self.settings_controls[spinTAG], 0, wx.EXPAND)
	
	# Staining Protocol
	spinprotTAG = 'AddProcess|Spin|SpinProtocol'
	self.settings_controls[spinprotTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(spinprotTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[spinprotTAG].SetInitialSize((300, 400))
	self.settings_controls[spinprotTAG].SetToolTipString('Cut and paste your Spinning Protocol here')
	fgs.Add(wx.StaticText(self.sw, -1, 'Paste Spinning Protocol'), 0)
	fgs.Add(self.settings_controls[spinprotTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Spinning Protocol")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'       
        
########################################################################        
################## WASH SETTING PANEL    ###########################
########################################################################
class WashSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        
        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id)
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add Washing Protocol")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Washing Protocol")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Washing Protocol No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return WashPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

class WashPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	
	#  Wash Name
	washTAG = 'AddProcess|Wash|WashPrtocolTag'
	self.settings_controls[washTAG] = wx.TextCtrl(self.sw, value=meta.get_field(washTAG, default=''))
	self.settings_controls[washTAG].SetToolTipString('Type an unique TAG for identifying the washning protocol')
	fgs.Add(wx.StaticText(self.sw, -1, 'Spinning Protocol Tag'), 0)
	fgs.Add(self.settings_controls[washTAG], 0, wx.EXPAND)
	
	# Staining Protocol
	washprotTAG = 'AddProcess|Wash|WashProtocol'
	self.settings_controls[washprotTAG] = wx.TextCtrl(self.sw,  value=meta.get_field(washprotTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[washprotTAG].SetInitialSize((300, 400))
	self.settings_controls[washprotTAG].SetToolTipString('Cut and paste your washing Protocol here')
	fgs.Add(wx.StaticText(self.sw, -1, 'Paste Washing Protocol'), 0)
	fgs.Add(self.settings_controls[washprotTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Washing Protocol")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()

	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'         
  
	    
########################################################################        
################## TIMELAPSE SETTING PANEL    ##########################
########################################################################
class TLMSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):

        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id)
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)
        
        addFirstTypePageBtn = wx.Button(self, label="Add Timelapse Image Settings")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Timelapse Image Settings")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Timelapse Image Settings No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return TLMPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

class TLMPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	#-- Microscope selection ---#
	tlmselctTAG = 'DataAcquis|Timelapse|MicroscopeInstance'
	self.settings_controls[tlmselctTAG] = wx.Choice(self.sw, -1,  choices=['Microscope 1', 'Microscope 2', 'Microscope 3'])
	if meta.get_field(tlmselctTAG) is None:
	    self.settings_controls[tlmselctTAG].SetSelection(0)
	else:
	    self.settings_controls[tlmselctTAG].SetStringSelection(meta.get_field(tlmselctTAG))
	self.settings_controls[tlmselctTAG].SetToolTipString('Microscope used for data acquisition')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope'), 0)
	fgs.Add(self.settings_controls[tlmselctTAG], 0, wx.EXPAND)
	#-- Image Format ---#
	tlmfrmtTAG = 'DataAcquis|Timelapse|Format'
	self.settings_controls[tlmfrmtTAG] = wx.Choice(self.sw, -1,  choices=['tiff', 'jpeg', 'stk'])
	if meta.get_field(tlmfrmtTAG) is None:
	    self.settings_controls[tlmfrmtTAG].SetSelection(0)
	else:
	    self.settings_controls[tlmfrmtTAG].SetStringSelection(meta.get_field(tlmfrmtTAG))
	self.settings_controls[tlmfrmtTAG].SetToolTipString('Image Format')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Image Format'), 0)
	fgs.Add(self.settings_controls[tlmfrmtTAG], 0, wx.EXPAND)
	#-- Channel ---#
	tlmchTAG = 'DataAcquis|Timelapse|Channel'
	self.settings_controls[tlmchTAG] = wx.Choice(self.sw, -1,  choices=['Red', 'Green', 'Blue'])
	if meta.get_field(tlmchTAG) is None:
	    self.settings_controls[tlmchTAG].SetSelection(0)
	else:
	    self.settings_controls[tlmchTAG].SetStringSelection(meta.get_field(tlmchTAG))
	self.settings_controls[tlmchTAG].SetToolTipString('Channel used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
	fgs.Add(self.settings_controls[tlmchTAG], 0, wx.EXPAND)
	#  Time Interval
	tlmintTAG = 'DataAcquis|Timelapse|TimeInterval'
	self.settings_controls[tlmintTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmintTAG, default=''))
	self.settings_controls[tlmintTAG].SetToolTipString('Time interval image was acquired')
	fgs.Add(wx.StaticText(self.sw, -1, 'Time Interval (min)'), 0)
	fgs.Add(self.settings_controls[tlmintTAG], 0, wx.EXPAND)
	#  Total Frame/Pane Number
	tlmfrmTAG = 'DataAcquis|Timelapse|FrameNumber'
	self.settings_controls[tlmfrmTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmfrmTAG, default=''))
	self.settings_controls[tlmfrmTAG].SetToolTipString('Total Frame/Pane Number')
	fgs.Add(wx.StaticText(self.sw, -1, 'Total Frame/Pane Number'), 0)
	fgs.Add(self.settings_controls[tlmfrmTAG], 0, wx.EXPAND)
	#  Stacking Order
	tlmstkTAG = 'DataAcquis|Timelapse|StackProcess'
	self.settings_controls[tlmstkTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmstkTAG, default=''))
	self.settings_controls[tlmstkTAG].SetToolTipString('Stacking Order')
	fgs.Add(wx.StaticText(self.sw, -1, 'Stacking Order'), 0)
	fgs.Add(self.settings_controls[tlmstkTAG], 0, wx.EXPAND)
	#  Pixel Size
	tlmpxlTAG = 'DataAcquis|Timelapse|PixelSize'
	self.settings_controls[tlmpxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxlTAG, default=''))
	self.settings_controls[tlmpxlTAG].SetToolTipString('Pixel Size')
	fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0)
	fgs.Add(self.settings_controls[tlmpxlTAG], 0, wx.EXPAND)
	#  Pixel Conversion
	tlmpxcnvTAG = 'DataAcquis|Timelapse|PixelConvert'
	self.settings_controls[tlmpxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmpxcnvTAG, default=''))
	self.settings_controls[tlmpxcnvTAG].SetToolTipString('Pixel Conversion')
	fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0)
	fgs.Add(self.settings_controls[tlmpxcnvTAG], 0, wx.EXPAND)
	#  Software
	tlmsoftTAG = 'DataAcquis|Timelapse|Software'
	self.settings_controls[tlmsoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(tlmsoftTAG, default=''))
	self.settings_controls[tlmsoftTAG].SetToolTipString(' Software')
	fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
	fgs.Add(self.settings_controls[tlmsoftTAG], 0, wx.EXPAND)

	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Image Acquistion Settings")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'    	    
	    
########################################################################        
################## STATIC SETTING PANEL    ##########################
########################################################################
class HCSSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):
        
        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id)
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add Static Image Settings")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete Static Image Settings")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Static Image Settings No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return HCSPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

class HCSPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	#-- Microscope selection ---#
	hcsselctTAG = 'DataAcquis|Static|MicroscopeInstance'
	self.settings_controls[hcsselctTAG] = wx.Choice(self.sw, -1,  choices=['Microscope 1', 'Microscope 2', 'Microscope 3'])
	if meta.get_field(hcsselctTAG) is None:
	    self.settings_controls[hcsselctTAG].SetSelection(0)
	else:
	    self.settings_controls[hcsselctTAG].SetStringSelection(meta.get_field(hcsselctTAG))
	self.settings_controls[hcsselctTAG].SetToolTipString('Microscope used for data acquisition')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Microscope'), 0)
	fgs.Add(self.settings_controls[hcsselctTAG], 0, wx.EXPAND)
	#-- Image Format ---#
	hcsfrmtTAG = 'DataAcquis|Static|Format'
	self.settings_controls[hcsfrmtTAG] = wx.Choice(self.sw, -1,  choices=['tiff', 'jpeg', 'stk'])
	if meta.get_field(hcsfrmtTAG) is None:
	    self.settings_controls[hcsfrmtTAG].SetSelection(0)
	else:
	    self.settings_controls[hcsfrmtTAG].SetStringSelection(meta.get_field(hcsfrmtTAG))
	self.settings_controls[hcsfrmtTAG].SetToolTipString('Image Format')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Image Format'), 0)
	fgs.Add(self.settings_controls[hcsfrmtTAG], 0, wx.EXPAND)
	#-- Channel ---#
	hcschTAG = 'DataAcquis|Static|Channel'
	self.settings_controls[hcschTAG] = wx.Choice(self.sw, -1,  choices=['Red', 'Green', 'Blue'])
	if meta.get_field(hcschTAG) is None:
	    self.settings_controls[hcschTAG].SetSelection(0)
	else:
	    self.settings_controls[hcschTAG].SetStringSelection(meta.get_field(hcschTAG))
	self.settings_controls[hcschTAG].SetToolTipString('Channel used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
	fgs.Add(self.settings_controls[hcschTAG], 0, wx.EXPAND)
	#  Pixel Size
	hcspxlTAG = 'DataAcquis|Static|PixelSize'
	self.settings_controls[hcspxlTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxlTAG, default=''))
	self.settings_controls[hcspxlTAG].SetToolTipString('Pixel Size')
	fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Size'), 0)
	fgs.Add(self.settings_controls[hcspxlTAG], 0, wx.EXPAND)
	#  Pixel Conversion
	hcspxcnvTAG = 'DataAcquis|Static|PixelConvert'
	self.settings_controls[hcspxcnvTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcspxcnvTAG, default=''))
	self.settings_controls[hcspxcnvTAG].SetToolTipString('Pixel Conversion')
	fgs.Add(wx.StaticText(self.sw, -1, 'Pixel Conversion'), 0)
	fgs.Add(self.settings_controls[hcspxcnvTAG], 0, wx.EXPAND)
	#  Software
	hcssoftTAG = 'DataAcquis|Static|Software'
	self.settings_controls[hcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(hcssoftTAG, default=''))
	self.settings_controls[hcssoftTAG].SetToolTipString(' Software')
	fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
	fgs.Add(self.settings_controls[hcssoftTAG], 0, wx.EXPAND)

	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record Image Acquistion Settings")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()

	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'    		    
	    

########################################################################        
################## FLOW SETTING PANEL    ##########################
########################################################################
class FCSSettingPanel(wx.Panel):
    """
    Panel that holds parameter input panel and the buttons for more additional panel
    """
    def __init__(self, parent, id=-1):

        self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent, id)
        # create some widgets
	self.first_type_page_counter = 0
	
        self.notebook = fnb.FlatNotebook(self, -1, style=fnb.FNB_NO_X_BUTTON)

        addFirstTypePageBtn = wx.Button(self, label="Add FCS file Settings")
	addFirstTypePageBtn.SetBackgroundColour("#33FF33")
        addFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onFirstTypeAddPage)
	rmvFirstTypePageBtn = wx.Button(self, label="Delete FCS file Settings")
	rmvFirstTypePageBtn.SetBackgroundColour("#FF3300")
        rmvFirstTypePageBtn.Bind(wx.EVT_BUTTON, self.onDelFirtTypePage)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addFirstTypePageBtn  , 0, wx.ALL, 5)
	btnSizer.Add(rmvFirstTypePageBtn  , 0, wx.ALL, 5)
        
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

    def onFirstTypeAddPage(self, event):
	self.first_type_page_counter += 1
        caption = "Static FCS file No. " + str(self.first_type_page_counter)
        self.Freeze()
        self.notebook.AddPage(self.createFirstTypePage(caption), caption, True)
        self.Thaw()
    def createFirstTypePage(self, caption):
        return FCSPanel(self.notebook, self.first_type_page_counter)
    def onDelFirtTypePage(self, event):
	if self.first_type_page_counter >= 1:
	    self.first_type_page_counter -= 1
	    self.notebook.DeletePage(self.notebook.GetSelection()) 

class FCSPanel(wx.Panel):
    def __init__(self, parent, first_type_page_counter):
	
	self.settings_controls = {}
	meta = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
	
	self.first_type_page_counter = first_type_page_counter
	
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5)
	
	#-- Flow  selection ---#
	fcsselctTAG = 'DataAcquis|Flow|FlowcytInstance'
	self.settings_controls[fcsselctTAG] = wx.Choice(self.sw, -1,  choices=['Flowcytometer 1', 'Flowcytometer 2', 'Flowcytometer 3'])
	if meta.get_field(fcsselctTAG) is None:
	    self.settings_controls[fcsselctTAG].SetSelection(0)
	else:
	    self.settings_controls[fcsselctTAG].SetStringSelection(meta.get_field(fcsselctTAG))
	self.settings_controls[fcsselctTAG].SetToolTipString('Flowcytometer used for data acquisition')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Flowcytometer'), 0)
	fgs.Add(self.settings_controls[fcsselctTAG], 0, wx.EXPAND)
	#-- Image Format ---#
	fcsfrmtTAG = 'DataAcquis|Flow|Format'
	self.settings_controls[fcsfrmtTAG] = wx.Choice(self.sw, -1,  choices=['fcs1.0', 'fcs2.0', 'fcs3.0'])
	if meta.get_field(fcsfrmtTAG) is None:
	    self.settings_controls[fcsfrmtTAG].SetSelection(0)
	else:
	    self.settings_controls[fcsfrmtTAG].SetStringSelection(meta.get_field(fcsfrmtTAG))
	self.settings_controls[fcsfrmtTAG].SetToolTipString('FCS file Format')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select FCS file Format'), 0)
	fgs.Add(self.settings_controls[fcsfrmtTAG], 0, wx.EXPAND)
	#-- Channel ---#
	fcschTAG = 'DataAcquis|Flow|Channel'
	self.settings_controls[fcschTAG] = wx.Choice(self.sw, -1,  choices=['FL8', 'FL6', 'FL2'])
	if meta.get_field(fcschTAG) is None:
	    self.settings_controls[fcschTAG].SetSelection(0)
	else:
	    self.settings_controls[fcschTAG].SetStringSelection(meta.get_field(fcschTAG))
	self.settings_controls[fcschTAG].SetToolTipString('Channel used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Select Channel'), 0)
	fgs.Add(self.settings_controls[fcschTAG], 0, wx.EXPAND)
	#  Software
	fcssoftTAG = 'DataAcquis|Flow|Software'
	self.settings_controls[fcssoftTAG] = wx.TextCtrl(self.sw, value=meta.get_field(fcssoftTAG, default=''))
	self.settings_controls[fcssoftTAG].SetToolTipString(' Software')
	fgs.Add(wx.StaticText(self.sw, -1, ' Software'), 0)
	fgs.Add(self.settings_controls[fcssoftTAG], 0, wx.EXPAND)

	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Record FCS Acquistion Settings")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	
	#---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	meta = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		meta.set_field(name, ctrl.GetStringSelection())
	    else:
		meta.set_field(name, ctrl.GetValue())
	    
	meta.save_to_file('test.txt')
	before = meta.global_settings.items()
    
	meta.load_from_file('test.txt')    
	after = meta.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.' 



if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title='Lineageprofiler', size=(700, 600))
    p = ExperimentSettingsWindow(frame)
    frame.Show()
    app.MainLoop()
