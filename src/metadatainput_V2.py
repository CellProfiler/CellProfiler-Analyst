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
        self.tree.AppendItem(ins, 'Microscope')
        self.tree.AppendItem(ins, 'Flowcytometer')
        stk = self.tree.AppendItem(stc, 'Stock Culture')
        exv = self.tree.AppendItem(stc, 'Experimental Vessel')
        self.tree.AppendItem(exv, 'Plate')
        self.tree.AppendItem(exv, 'Flask')
        
        stc = self.tree.AppendItem(root, 'TEMPORAL')
        cld = self.tree.AppendItem(stc, 'Cell Loading')
        ptb = self.tree.AppendItem(stc, 'Perturbation')
        stn = self.tree.AppendItem(stc, 'Staining')
        adp = self.tree.AppendItem(stc, 'Additional Processes')
        self.tree.AppendItem(adp, 'Spin')
        self.tree.AppendItem(adp, 'Wash')
        self.tree.AppendItem(adp, 'Dry')
        dta = self.tree.AppendItem(stc, 'Data Acquisition')
        self.tree.AppendItem(dta, 'Timelapse Image')
        self.tree.AppendItem(dta, 'Static Image')
        self.tree.AppendItem(dta, 'Flow FCS files')
        #hvr = self.tree.AppendItem(adp, 'Harvest')
        #self.tree.AppendItem(hvr, 'Skew')
        self.tree.Expand(root)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        
        self.settings_container = wx.Panel(self)#MicroscopePanel(self)
        self.settings_container.SetSizer(wx.BoxSizer())
        self.settings_panel = wx.Panel(self)
        
        self.SetMinimumPaneSize(20)
        self.SplitVertically(self.tree, self.settings_container, self.tree.MinWidth)
        
        self.Centre()

    def OnSelChanged(self, event):
        item =  event.GetItem()

        if self.tree.GetItemText(item) == 'Overview':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = OverviewPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)
        elif self.tree.GetItemText(item) == 'Microscope':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = MicroscopePanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)
        elif self.tree.GetItemText(item) == 'Flowcytometer':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = FlowCytometerPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)
        elif self.tree.GetItemText(item) == 'Plate':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = PlateWellPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)
        elif self.tree.GetItemText(item) == 'Flask':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = FlaskPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)    
        elif self.tree.GetItemText(item) == 'Stock Culture':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = StockCulturingPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)    
        elif self.tree.GetItemText(item) == 'Cell Loading':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = CellLoadingPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)    
        elif self.tree.GetItemText(item) == 'Perturbation':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = PerturbationPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)
        elif self.tree.GetItemText(item) == 'Staining':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = StainingPanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)    
        elif self.tree.GetItemText(item) == 'Timelapse Image':
            self.settings_panel.Destroy()
            self.settings_container.Sizer.Clear()
            self.settings_panel = TimeLapseImagePanel(self.settings_container)
            self.settings_container.Sizer.Add(self.settings_panel, 1, wx.EXPAND)    
 
        
        
        self.settings_container.Layout()

class OverviewPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        
	self.settings_controls = {}
	settings = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
	# Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=12, cols=2, hgap=5, vgap=5)
        
        # Experiment Title
	titleTAG = 'Overview|Project|Title'
	self.settings_controls[titleTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(titleTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[titleTAG].SetToolTipString('Insert the title of the experiment')
	fgs.Add(wx.StaticText(self.sw, -1, 'Project Title'), 0)
	fgs.Add(self.settings_controls[titleTAG], 0, wx.EXPAND)
	# Experiment Aim
	aimTAG = 'Overview|Project|Aims'
        self.settings_controls[aimTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(aimTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[aimTAG].SetToolTipString('Describe here the aim of the experiment')
	fgs.Add(wx.StaticText(self.sw, -1, 'Project Aim'), 0)
	fgs.Add(self.settings_controls[aimTAG], 0, wx.EXPAND)
        # Keywords
	keyTAG = 'Overview|Project|Keywords'
        self.settings_controls[keyTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(keyTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[keyTAG].SetToolTipString('Keywords that indicates the experiment')
	fgs.Add(wx.StaticText(self.sw, -1, 'Keywords'), 0)
	fgs.Add(self.settings_controls[keyTAG], 0, wx.EXPAND)
        # Experiment Number
	exnumTAG = 'Overview|Project|ExptNum'
	self.settings_controls[exnumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
	if settings.get_field(exnumTAG) is None:
	    self.settings_controls[exnumTAG].SetSelection(0)
	else:
	    self.settings_controls[exnumTAG].SetStringSelection(settings.get_field(exnumTAG))
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
	self.settings_controls[exppubTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(exppubTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[exppubTAG].SetToolTipString('Experiment related publication list')
	fgs.Add(wx.StaticText(self.sw, -1, 'Related Publications'), 0)
	fgs.Add(self.settings_controls[exppubTAG], 0, wx.EXPAND)
	# Experimenter Name
	expnameTAG = 'Overview|Project|Experimenter'
        self.settings_controls[expnameTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(expnameTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[expnameTAG].SetToolTipString('Name of experimenter(s)')
	fgs.Add(wx.StaticText(self.sw, -1, 'Name of Experimenter(s)'), 0)
	fgs.Add(self.settings_controls[expnameTAG], 0, wx.EXPAND)
	# Institution Name
        instnameTAG = 'Overview|Project|Institution'
        self.settings_controls[instnameTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(instnameTAG, default=''))
	self.settings_controls[instnameTAG].SetToolTipString('Name of Institution')
	fgs.Add(wx.StaticText(self.sw, -1, 'Name of Institution'), 0)
	fgs.Add(self.settings_controls[instnameTAG], 0, wx.EXPAND)
        # Department Name
        deptnameTAG = 'Overview|Project|Department'
        self.settings_controls[deptnameTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(deptnameTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[deptnameTAG].SetToolTipString('Name of the Department')
	fgs.Add(wx.StaticText(self.sw, -1, 'Department Name'), 0)
	fgs.Add(self.settings_controls[deptnameTAG], 0, wx.EXPAND)
        # Address
        addressTAG = 'Overview|Project|Address'
        self.settings_controls[addressTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(addressTAG, default=''), style=wx.TE_MULTILINE)
	self.settings_controls[addressTAG].SetToolTipString('Postal address and other contact details')
	fgs.Add(wx.StaticText(self.sw, -1, 'Address'), 0)
	fgs.Add(self.settings_controls[addressTAG], 0, wx.EXPAND)
        # Status
        statusTAG = 'Overview|Project|Status'
	self.settings_controls[statusTAG] = wx.Choice(self.sw, -1,  choices=['Complete', 'Ongoing', 'Pending', 'Discarded'])
	if settings.get_field(statusTAG) is None:
	    self.settings_controls[statusTAG].SetSelection(0)
	else:
	    self.settings_controls[statusTAG].SetStringSelection(settings.get_field(statusTAG))
	self.settings_controls[statusTAG].SetToolTipString('Status of the experiment, e.g. Complete, On-going, Discarded')
	fgs.Add(wx.StaticText(self.sw, -1, 'Status'), 0)
	fgs.Add(self.settings_controls[statusTAG], 0, wx.EXPAND)
		
      	#Create the button
	addBut = wx.Button(self.sw, -1, label="Add Data")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
	    
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	
        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
   
    def OnSavingData(self, event):
	settings = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		settings.set_field(name, ctrl.GetStringSelection())
	    else:
		settings.set_field(name, ctrl.GetValue())
	    
	settings.save_to_file('test.txt')
	before = settings.global_settings.items()
    
	settings.load_from_file('test.txt')    
	after = settings.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'


class MicroscopePanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
	
	self.settings_controls = {}
	settings = ExperimentSettings.getInstance()

        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=17, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        #--Manufacture--#
	micromfgTAG = 'Instrument|Microscope|Manufacter'
	self.settings_controls[micromfgTAG] = wx.Choice(self.sw, -1,  choices=['Zeiss','Olympus','Nikon', 'MDS', 'GE'])
	if settings.get_field(micromfgTAG) is None:
	    self.settings_controls[micromfgTAG].SetSelection(0)
	else:
	    self.settings_controls[micromfgTAG].SetStringSelection(settings.get_field(micromfgTAG))
	self.settings_controls[micromfgTAG].SetToolTipString('Manufacturer name')
	fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
	fgs.Add(self.settings_controls[micromfgTAG], 0, wx.EXPAND)
	#--Model--#
	micromdlTAG = 'Instrument|Microscope|Model'
	self.settings_controls[micromdlTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(micromdlTAG, default=''))
	self.settings_controls[micromdlTAG].SetToolTipString('Model number of the microscope')
	fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
	fgs.Add(self.settings_controls[micromdlTAG], 0, wx.EXPAND)
	#--Microscope type--#
        microtypTAG = 'Instrument|Microscope|Type'
	self.settings_controls[microtypTAG] = wx.Choice(self.sw, -1,  choices=['Upright', 'Inverted', 'Confocal'])
	if settings.get_field(microtypTAG) is None:
	    self.settings_controls[microtypTAG].SetSelection(0)
	else:
	    self.settings_controls[microtypTAG].SetStringSelection(settings.get_field(microtypTAG))
	self.settings_controls[microtypTAG].SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
	fgs.Add(wx.StaticText(self.sw, -1, 'Microscope Type'), 0)
	fgs.Add(self.settings_controls[microtypTAG], 0, wx.EXPAND)
	#--Light source--#
	microlgtTAG = 'Instrument|Microscope|LightSource'
	self.settings_controls[microlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Filament', 'Arc', 'LightEmitingDiode'])
	if settings.get_field(microlgtTAG) is None:
	    self.settings_controls[microlgtTAG].SetSelection(0)
	else:
	    self.settings_controls[microlgtTAG].SetStringSelection(settings.get_field(microlgtTAG))
	self.settings_controls[microlgtTAG].SetToolTipString('e.g. Laser, Filament, Arc, Light Emiting Diode')
	fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
	fgs.Add(self.settings_controls[microlgtTAG], 0, wx.EXPAND)
        #--Detector--#
	microdctTAG = 'Instrument|Microscope|Detector'
	self.settings_controls[microdctTAG] = wx.Choice(self.sw, -1,  choices=['CCD', 'Intensified-CCD', 'Analog-Video', 'Spectroscopy', 'Life-time-imaging', 'Correlation-Spectroscopy', 'FTIR', 'EM-CCD', 'APD', 'CMOS'])
	if settings.get_field(microdctTAG) is None:
	    self.settings_controls[microdctTAG].SetSelection(0)
	else:
	    self.settings_controls[microdctTAG].SetStringSelection(settings.get_field(microlgtTAG))
	self.settings_controls[microdctTAG].SetToolTipString('Type of dectector used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Dectector'), 0)
	fgs.Add(self.settings_controls[microdctTAG], 0, wx.EXPAND)
        #--Lense Aperture--#
	microlnsappTAG = 'Instrument|Microscope|LensApprture'
	self.settings_controls[microlnsappTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(microlnsappTAG, default=''))
	self.settings_controls[microlnsappTAG].SetToolTipString('A floating value of lens numerical aperture')
	fgs.Add(wx.StaticText(self.sw, -1, 'Lense Apparture'), 0)
	fgs.Add(self.settings_controls[microlnsappTAG], 0, wx.EXPAND)
        # Lense Correction
	microlnscorrTAG = 'Instrument|Microscope|LensCorr'
	self.settings_controls[microlnscorrTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if settings.get_field(microlnscorrTAG) is None:
	    self.settings_controls[microlnscorrTAG].SetSelection(0)
	else:
	    self.settings_controls[microlnscorrTAG].SetStringSelection(settings.get_field(microlnscorrTAG))
	self.settings_controls[microlnscorrTAG].SetToolTipString('Yes/No')
	fgs.Add(wx.StaticText(self.sw, -1, 'Lense Correction'), 0)
	fgs.Add(self.settings_controls[microlnscorrTAG], 0, wx.EXPAND)
	#--Illumination Type--#
        microIllTAG = 'Instrument|Microscope|IllumType'
	self.settings_controls[microIllTAG] = wx.Choice(self.sw, -1,  choices=['Transmitted','Epifluorescence','Oblique','NonLinear'])
	if settings.get_field(microIllTAG) is None:
	    self.settings_controls[microIllTAG].SetSelection(0)
	else:
	    self.settings_controls[microIllTAG].SetStringSelection(settings.get_field(microIllTAG))
	self.settings_controls[microIllTAG].SetToolTipString('Type of illumunation used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Illumination Type'), 0)
	fgs.Add(self.settings_controls[microIllTAG], 0, wx.EXPAND)
	#--Mode--#
        microModTAG = 'Instrument|Microscope|Mode'
	self.settings_controls[microModTAG] = wx.Choice(self.sw, -1,  choices=['WideField','LaserScanningMicroscopy', 'LaserScanningConfocal', 'SpinningDiskConfocal', 'SlitScanConfocal', 'MultiPhotonMicroscopy', 'StructuredIllumination','SingleMoleculeImaging', 'TotalInternalReflection', 'FluorescenceLifetime', 'SpectralImaging', 'FluorescenceCorrelationSpectroscopy', 'NearFieldScanningOpticalMicroscopy', 'SecondHarmonicGenerationImaging', 'Timelapse', 'Other'])
	if settings.get_field(microModTAG) is None:
	    self.settings_controls[microModTAG].SetSelection(0)
	else:
	    self.settings_controls[microModTAG].SetStringSelection(settings.get_field(microModTAG))
	self.settings_controls[microModTAG].SetToolTipString('Mode of the microscope')
	fgs.Add(wx.StaticText(self.sw, -1, 'Mode'), 0)
	fgs.Add(self.settings_controls[microModTAG], 0, wx.EXPAND)
        #--Immersion--#
        microImmTAG = 'Instrument|Microscope|Immersion'
	self.settings_controls[microImmTAG] = wx.Choice(self.sw, -1,  choices=['Oil', 'Water', 'WaterDipping', 'Air', 'Multi', 'Glycerol', 'Other', 'Unkonwn'])
	if settings.get_field(microImmTAG) is None:
	    self.settings_controls[microImmTAG].SetSelection(0)
	else:
	    self.settings_controls[microImmTAG].SetStringSelection(settings.get_field(microImmTAG))
	self.settings_controls[microImmTAG].SetToolTipString('Immersion medium used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
	fgs.Add(self.settings_controls[microImmTAG], 0, wx.EXPAND)
        #--Correction--#
        microCorrTAG = 'Instrument|Microscope|Correction'
	self.settings_controls[microCorrTAG] = wx.Choice(self.sw, -1,  choices=['UV', 'PlanApo', 'PlanFluor', 'SuperFluor', 'VioletCorrected', 'Unknown'])
	if settings.get_field(microCorrTAG) is None:
	    self.settings_controls[microCorrTAG].SetSelection(0)
	else:
	    self.settings_controls[microCorrTAG].SetStringSelection(settings.get_field(microCorrTAG))
	self.settings_controls[microCorrTAG].SetToolTipString('Lense correction used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
	fgs.Add(self.settings_controls[microCorrTAG], 0, wx.EXPAND)
        #--Nominal Magnification--#
        microNmgTAG = 'Instrument|Microscope|NominalMagnification'
	self.settings_controls[microNmgTAG] = wx.TextCtrl(self.sw, -1)
	self.settings_controls[microNmgTAG].SetToolTipString('The magnification of the lens as specified by the manufacturer - i.e. 60 is a 60X lens')
	fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
	fgs.Add(self.settings_controls[microNmgTAG], 0, wx.EXPAND)
        # Calibrated Magnification
        microCalTAG = 'Instrument|Microscope|CalibratedMagnification'
	self.settings_controls[microCalTAG] = wx.TextCtrl(self.sw, -1)
	self.settings_controls[microCalTAG].SetToolTipString('The magnification of the lens as measured by a calibration process- i.e. 59.987 for a 60X lens')
	fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
	fgs.Add(self.settings_controls[microCalTAG], 0, wx.EXPAND)
        #--Working distance--#
        microWrkTAG = 'Instrument|Microscope|WorkDistance'
	self.settings_controls[microWrkTAG] = wx.TextCtrl(self.sw, -1)
	self.settings_controls[microWrkTAG].SetToolTipString('The working distance of the lens expressed as a floating point (real) number. Units are um')
	fgs.Add(wx.StaticText(self.sw, -1, 'Working Distance in uM'), 0)
	fgs.Add(self.settings_controls[microWrkTAG], 0, wx.EXPAND)
        #--Filter used--#
        microFltTAG = 'Instrument|Microscope|Filter'
	self.settings_controls[microFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if settings.get_field(microFltTAG) is None:
	    self.settings_controls[microFltTAG].SetSelection(0)
	else:
	    self.settings_controls[microFltTAG].SetStringSelection(settings.get_field(microFltTAG))
	self.settings_controls[microFltTAG].SetToolTipString('Whether filter was used or not')
	fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
	fgs.Add(self.settings_controls[microFltTAG], 0, wx.EXPAND)
        #--Software--#
        microSoftTAG = 'Instrument|Microscope|Software'
	self.settings_controls[microSoftTAG] = wx.TextCtrl(self.sw, -1)
	self.settings_controls[microSoftTAG].SetToolTipString('Name and version of software used for data acquisition')
	fgs.Add(wx.StaticText(self.sw, -1, 'Software'), 0)
	fgs.Add(self.settings_controls[microSoftTAG], 0, wx.EXPAND)
	
        #--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Add Data")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	settings = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		settings.set_field(name, ctrl.GetStringSelection())
	    else:
		settings.set_field(name, ctrl.GetValue())
	    
	settings.save_to_file('test.txt')
	before = settings.global_settings.items()
    
	settings.load_from_file('test.txt')    
	after = settings.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'

class FlowCytometerPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        
	self.settings_controls = {}
	settings = ExperimentSettings.getInstance()
	
	wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=7, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        #--Manufacture--#
	flowmfgTAG = 'Instrument|Flowcytometer|Manufacter'
	self.settings_controls[flowmfgTAG] = wx.Choice(self.sw, -1,  choices=['Beckman','BD-Biosciences'])
	if settings.get_field(flowmfgTAG) is None:
	    self.settings_controls[flowmfgTAG].SetSelection(0)
	else:
	    self.settings_controls[flowmfgTAG].SetStringSelection(settings.get_field(flowmfgTAG))
	self.settings_controls[flowmfgTAG].SetToolTipString('Manufacturer name')
	fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
	fgs.Add(self.settings_controls[flowmfgTAG], 0, wx.EXPAND)
	#--Model--#
	flowmdlTAG = 'Instrument|Flowcytometer|Model'
	self.settings_controls[flowmdlTAG] = wx.TextCtrl(self.sw,  value=settings.get_field(flowmdlTAG, default=''))
	self.settings_controls[flowmdlTAG].SetToolTipString('Model number of the Flowcytometer')
	fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
	fgs.Add(self.settings_controls[flowmdlTAG], 0, wx.EXPAND)
	#--Flowcytometer type--#
        flowtypTAG = 'Instrument|Flowcytometer|Type'
	self.settings_controls[flowtypTAG] = wx.Choice(self.sw, -1,  choices=['Stream-in-air', 'cuvette'])
	if settings.get_field(flowtypTAG) is None:
	    self.settings_controls[flowtypTAG].SetSelection(0)
	else:
	    self.settings_controls[flowtypTAG].SetStringSelection(settings.get_field(flowtypTAG))
	self.settings_controls[flowtypTAG].SetToolTipString('Type of flowcytometer')
	fgs.Add(wx.StaticText(self.sw, -1, 'Flowcytometer Type'), 0)
	fgs.Add(self.settings_controls[flowtypTAG], 0, wx.EXPAND)
	#--Light source--#
	flowlgtTAG = 'Instrument|Flowcytometer|LightSource'
	self.settings_controls[flowlgtTAG] = wx.Choice(self.sw, -1,  choices=['Laser', 'Beam'])
	if settings.get_field(flowlgtTAG) is None:
	    self.settings_controls[flowlgtTAG].SetSelection(0)
	else:
	    self.settings_controls[flowlgtTAG].SetStringSelection(settings.get_field(flowlgtTAG))
	self.settings_controls[flowlgtTAG].SetToolTipString('Light source of the flowcytometer')
	fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
	fgs.Add(self.settings_controls[flowlgtTAG], 0, wx.EXPAND)
        #--Detector--#
	flowdctTAG = 'Instrument|Flowcytometer|Detector'
	self.settings_controls[flowdctTAG] = wx.Choice(self.sw, -1,  choices=['PhotoMultiplierTube', 'FluorescentDetectors'])
	if settings.get_field(flowdctTAG) is None:
	    self.settings_controls[flowdctTAG].SetSelection(0)
	else:
	    self.settings_controls[flowdctTAG].SetStringSelection(settings.get_field(flowlgtTAG))
	self.settings_controls[flowdctTAG].SetToolTipString('Type of dectector used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Dectector'), 0)
	fgs.Add(self.settings_controls[flowdctTAG], 0, wx.EXPAND)
	#--Filter used--#
        flowFltTAG = 'Instrument|Flowcytometer|Filter'
	self.settings_controls[flowFltTAG] = wx.Choice(self.sw, -1,  choices=['Yes', 'No'])
	if settings.get_field(flowFltTAG) is None:
	    self.settings_controls[flowFltTAG].SetSelection(0)
	else:
	    self.settings_controls[flowFltTAG].SetStringSelection(settings.get_field(flowFltTAG))
	self.settings_controls[flowFltTAG].SetToolTipString('Whether filter was used or not')
	fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
	fgs.Add(self.settings_controls[flowFltTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Add Data")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	settings = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		settings.set_field(name, ctrl.GetStringSelection())
	    else:
		settings.set_field(name, ctrl.GetValue())
	    
	settings.save_to_file('test.txt')
	before = settings.global_settings.items()
    
	settings.load_from_file('test.txt')    
	after = settings.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'


##---------- Plate Well Panel----------------##
class PlateWellPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        
	#initiate the dictionary with singelton 
	self.settings_controls = {}
	settings = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=6, cols=2, hgap=5, vgap=5) 

        #----------- Plate Labels and Text Controler-------        
	#--Plate Number--#
	expPltnumTAG = 'ExptVessel|Plate|Number'
	self.settings_controls[expPltnumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
	if settings.get_field(expPltnumTAG) is None:
	    self.settings_controls[expPltnumTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltnumTAG].SetStringSelection(settings.get_field(expPltnumTAG))
	self.settings_controls[expPltnumTAG].SetToolTipString('Number of Plate used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Total number of Plate used'), 0)
	fgs.Add(self.settings_controls[expPltnumTAG], 0, wx.EXPAND)
	
	#--Design--#
	expPltdesTAG = 'ExptVessel|Plate|Design'
	self.settings_controls[expPltdesTAG] = wx.Choice(self.sw, -1,  choices=['6-Well-(2x3)', '96-Well-(8x12)', '384-Well-(16x24)', '1536-Well-(32x48)', '5600-Well-(40x140)'])
	if settings.get_field(expPltdesTAG) is None:
	    self.settings_controls[expPltdesTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltdesTAG].SetStringSelection(settings.get_field(expPltdesTAG))
	self.settings_controls[expPltdesTAG].SetToolTipString('Design of Plate')
	fgs.Add(wx.StaticText(self.sw, -1, 'Plate Design'), 0)
	fgs.Add(self.settings_controls[expPltdesTAG], 0, wx.EXPAND)
        
	#--Well Shape--#
	expPltshpTAG = 'ExptVessel|Plate|Shape'
	self.settings_controls[expPltshpTAG] = wx.Choice(self.sw, -1,  choices=['Square','Round','Oval'])
	if settings.get_field(expPltshpTAG) is None:
	    self.settings_controls[expPltshpTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltshpTAG].SetStringSelection(settings.get_field(expPltshpTAG))
	self.settings_controls[expPltshpTAG].SetToolTipString('Shape of wells in the plate used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Well Shape'), 0)
	fgs.Add(self.settings_controls[expPltshpTAG], 0, wx.EXPAND)
	
	#--Well Size--#
	expPltshpTAG = 'ExptVessel|Plate|Size'
	self.settings_controls[expPltshpTAG] = wx.TextCtrl(self.sw, -1)
	self.settings_controls[expPltshpTAG].SetToolTipString('Size of the wells  used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Size of Well (mm)'), 0)
	fgs.Add(self.settings_controls[expPltshpTAG], 0, wx.EXPAND)
	
	#--Plate Material--#
	expPltmatTAG = 'ExptVessel|Plate|Material'
	self.settings_controls[expPltmatTAG] = wx.Choice(self.sw, -1,  choices=['Plastic','Glass'])
	if settings.get_field(expPltmatTAG) is None:
	    self.settings_controls[expPltmatTAG].SetSelection(0)
	else:
	    self.settings_controls[expPltmatTAG].SetStringSelection(settings.get_field(expPltmatTAG))
	self.settings_controls[expPltmatTAG].SetToolTipString('Material of the plate')
	fgs.Add(wx.StaticText(self.sw, -1, 'Plate Material'), 0)
	fgs.Add(self.settings_controls[expPltmatTAG], 0, wx.EXPAND)
	
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Add Data")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	settings = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		settings.set_field(name, ctrl.GetStringSelection())
	    else:
		settings.set_field(name, ctrl.GetValue())
	    
	settings.save_to_file('test.txt')
	before = settings.global_settings.items()
    
	settings.load_from_file('test.txt')    
	after = settings.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'

##---------- Flast Panel----------------##
class FlaskPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
	
	#initiate the dictionary with singelton 
	self.settings_controls = {}
	settings = ExperimentSettings.getInstance()
        
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5) 
       
        #----------- Plate Labels and Text Controler-------        
	#--Flask Number--#
	expFlknumTAG = 'ExptVessel|Flask|Number'
	self.settings_controls[expFlknumTAG] = wx.Choice(self.sw, -1,  choices=['1','2','3','4','5','6','7','8','9','10'])
	if settings.get_field(expFlknumTAG) is None:
	    self.settings_controls[expFlknumTAG].SetSelection(0)
	else:
	    self.settings_controls[expFlknumTAG].SetStringSelection(settings.get_field(expFlknumTAG))
	self.settings_controls[expFlknumTAG].SetToolTipString('Number of Flasks used')
	fgs.Add(wx.StaticText(self.sw, -1, 'Total number of Flask used'), 0)
	fgs.Add(self.settings_controls[expFlknumTAG], 0, wx.EXPAND)
        
        #--Flask Material--#
	expFlkmatTAG = 'ExptVessel|Flask|Material'
	self.settings_controls[expFlkmatTAG] = wx.Choice(self.sw, -1,  choices=['Plastic','Glass'])
	if settings.get_field(expFlkmatTAG) is None:
	    self.settings_controls[expFlkmatTAG].SetSelection(0)
	else:
	    self.settings_controls[expFlkmatTAG].SetStringSelection(settings.get_field(expFlkmatTAG))
	self.settings_controls[expFlkmatTAG].SetToolTipString('Material of the Flask')
	fgs.Add(wx.StaticText(self.sw, -1, 'Flask Material'), 0)
	fgs.Add(self.settings_controls[expFlkmatTAG], 0, wx.EXPAND)
        
	#--Create the Adding button--#
	addBut = wx.Button(self.sw, -1, label="Add Data")
	addBut.Bind(wx.EVT_BUTTON, self.OnSavingData)
	fgs.Add(addBut, 0, wx.ALL, 5)
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
      
    #---- Savings the users defined parameters----------#
    def OnSavingData(self, event):
	settings = ExperimentSettings.getInstance()
	
	for name, ctrl in self.settings_controls.items():
	    if isinstance(ctrl, wx.Choice):
		settings.set_field(name, ctrl.GetStringSelection())
	    else:
		settings.set_field(name, ctrl.GetValue())
	    
	settings.save_to_file('test.txt')
	before = settings.global_settings.items()
    
	settings.load_from_file('test.txt')    
	after = settings.global_settings.items()
	
	for a, b in zip(sorted(before), sorted(after)):
	    assert a == b, 'loaded data is not the same as the saved data.'        
  
    
        
        
########################################################################
################## PERTURBATION SELECTION ##############################
########################################################################
class FlatNotebookDemo(fnb.FlatNotebook):
    """
    Flatnotebook class
    """
    def __init__(self, parent):
        """Constructor"""
        fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY)

        
        
########################################################################        
################## STAININ SELECTION ##############################
########################################################################
class StockCulturePanel(wx.Panel):
    """
    This page for Chemical perturbing agent parameter input
    """
    #----------------------------------------------------------------------
    def __init__(self, parent, culture_number):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.culture_number = culture_number
	print self.culture_number
        fgs = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
	

        #----------- Labels and Text Controler-------        
        # Taxonomic ID
        txid = wx.TextCtrl(self, -1)
        txid.SetToolTipString('Taxonomic ID...')
        fgs.Add(wx.StaticText(self, -1, 'Taxonomic ID'), 0)
        fgs.Add(txid, 0, wx.EXPAND)
        # Cell Line Name
        cln = wx.TextCtrl(self, -1)
        cln.SetToolTipString('Cell Line Name...')
        fgs.Add(wx.StaticText(self, -1, 'Cell Line Name'), 0)
        fgs.Add(cln, 0, wx.EXPAND)
        # Strain
        strn = wx.TextCtrl(self, -1)
        strn.SetToolTipString('Starin of that cell line eGFP, Wild type etc.')
        fgs.Add(wx.StaticText(self, -1, 'Strain'), 0)
        fgs.Add(strn, 0, wx.EXPAND)
        # Age
        age = wx.TextCtrl(self, -1)
        age.SetToolTipString('Age of the organism in days when the cells were collected. .')
        fgs.Add(wx.StaticText(self, -1, 'Strain'), 0)
        fgs.Add(age, 0, wx.EXPAND)
        # Gender
        gnd = wx.TextCtrl(self, -1)
        gnd.SetToolTipString('Male/Female/Neutral. ')
        fgs.Add(wx.StaticText(self, -1, 'Gender'), 0)
        fgs.Add(gnd, 0, wx.EXPAND)
        # Organ
        gnd = wx.TextCtrl(self, -1)
        gnd.SetToolTipString('The organ name from where the cell were collected. eg. Heart, Lung, Bone etc')
        fgs.Add(wx.StaticText(self, -1, 'Organ'), 0)
        fgs.Add(gnd, 0, wx.EXPAND)
        # Tissue
        tss = wx.TextCtrl(self, -1)
        tss.SetToolTipString('The tissue from which the cells were collected')
        fgs.Add(wx.StaticText(self, -1, 'Tissue'), 0)
        fgs.Add(tss, 0, wx.EXPAND)
        # Pheotype
        pho = wx.TextCtrl(self, -1)
        pho.SetToolTipString('The phenotypic examples Colour Height OR any other value descriptor')
        fgs.Add(wx.StaticText(self, -1, 'Phenotype'), 0)
        fgs.Add(pho, 0, wx.EXPAND)
        # Genotype
        gen = wx.TextCtrl(self, -1)
        gen.SetToolTipString('wild type or mutant etc. (single word)')
        fgs.Add(wx.StaticText(self, -1, 'Genotype'), 0)
        fgs.Add(gen, 0, wx.EXPAND)
        # Medium Used
        mdm = wx.TextCtrl(self, -1)
        mdm.SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self, -1, 'Medium Used'), 0)
        fgs.Add(mdm, 0, wx.EXPAND)
        # Passage Number
        psnum = wx.TextCtrl(self, -1)
        psnum.SetToolTipString('The numeric value of the passage of the cells under investigation')
        fgs.Add(wx.StaticText(self, -1, 'Passage Number'), 0)
        fgs.Add(psnum, 0, wx.EXPAND)
        # Trypsinization
        tryp = wx.TextCtrl(self, -1)
        tryp.SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self, -1, 'Trypsinization'), 0)
        fgs.Add(tryp, 0, wx.EXPAND)
               
        
        # Layout with sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)

class StockCulturingPanel(wx.Panel):
    """
    Frame that holds all other widgets
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)
        
        # create some widgets
	self.number_of_stocks = 0
	
        #panel = wx.Panel(self)
        self.createRightClickMenu()
        
        self.notebook = FlatNotebookDemo(self)
        
        addStainPageBtn = wx.Button(self, label="+ New (Stock Culture)")
        addStainPageBtn.Bind(wx.EVT_BUTTON, self.onStainAddPage)
        removePageBtn = wx.Button(self, label="Remove Page")
        removePageBtn.Bind(wx.EVT_BUTTON, self.onDeletePage)
        self.notebook.SetRightClickMenu(self._rmenu)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addStainPageBtn , 0, wx.ALL, 5)
        btnSizer.Add(removePageBtn, 0, wx.ALL, 5)
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()

        self.Show()
    def createRightClickMenu(self):
        """
        Based on method from flatnotebook demo
        """
        self._rmenu = wx.Menu()
        item = wx.MenuItem(self._rmenu, wx.ID_ANY, "Close Tab\tCtrl+F4", "Close Tab")
        self.Bind(wx.EVT_MENU, self.onDeletePage, item)
        self._rmenu.AppendItem(item)

    def onStainAddPage(self, event):
        """
        This method is based on the flatnotebook demo
        It adds a new page to the notebook
        """
        caption = "Stock Culture No. " + str(self.number_of_stocks)
        self.Freeze()
        self.notebook.AddPage(self.createStainPage(caption), caption, True)
        self.Thaw()
        

    def createStainPage(self, caption):
        """
        Creates a chemical perturbing agent notebook page
        """
	self.number_of_stocks += 1
        return StockCulturePanel(self.notebook, self.number_of_stocks)
    
    def onDeletePage(self, event):
        """
        This method is based on the flatnotebook demo
 
        It removes a page from the notebook
        """
        self.notebook.DeletePage(self.notebook.GetSelection())        
        
        
        
##....>>>><<<<<<......#####        
class ChemPanel(wx.Panel):
    """
    This page for Chemical perturbing agent parameter input
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        fgs = wx.FlexGridSizer(rows=3, cols=3, hgap=5, vgap=5)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        concUnit = ['ml', 'uM', 'nM', 'ug/L']
        
        #Heading
        heading1 = wx.StaticText(self, -1, 'Chemical Agent')
        heading1.SetFont(font)
        fgs.Add(heading1, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self, -1, ''), 0, wx.EXPAND)# seting the gap for aligning the column number
        fgs.Add(wx.StaticText(self, -1, ''), 0, wx.EXPAND)
        
        # Chemical Name
        drugName = wx.TextCtrl(self, -1)
        drugName.SetToolTipString('Name of the Drug')
        fgs.Add(wx.StaticText(self, -1, 'Chemical Name'), 0)
        fgs.Add(drugName, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self, -1, ''), 0)
        
        # Concentration
        drugConc = wx.TextCtrl(self, -1)
        drugConc.SetToolTipString('Concentration of the Drug')
        fgs.Add(wx.StaticText(self, -1, 'Concentration'), 0)
        fgs.Add(drugConc, 0, wx.EXPAND)
        fgs.Add(wx.Choice(self, -1, (85, 18), choices=concUnit))     
        
           
        # Layout with sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)

class BioPanel(wx.Panel):
    """
    This page for Chemical perturbing agent parameter input
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        fgs = wx.FlexGridSizer(rows=4, cols=2, hgap=5, vgap=5)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        #Heading
        heading1 = wx.StaticText(self, -1, 'Biological Agent')
        heading1.SetFont(font)
        heading2 = wx.StaticText(self, -1, '')  # seting the gap for aligning the column number
        fgs.Add(heading1, 0, wx.EXPAND)
        fgs.Add(heading2, 0, wx.EXPAND)
                
        # Sequence
        seqName = wx.TextCtrl(self, -1)
        seqName.SetToolTipString('RNAi Sequence ......')
        fgs.Add(wx.StaticText(self, -1, 'RNAi Sequence'), 0)
        fgs.Add(seqName, 0, wx.EXPAND)
        # Accession Number
        accsNum = wx.TextCtrl(self, -1)
        accsNum.SetToolTipString('Accession Number ......')
        fgs.Add(wx.StaticText(self, -1, 'Accession Number'), 0)
        fgs.Add(accsNum, 0, wx.EXPAND)
         # Target gene accession Number
        tgaccsNum = wx.TextCtrl(self, -1)
        tgaccsNum.SetToolTipString('Target gene Accession Number ......')
        fgs.Add(wx.StaticText(self, -1, 'Target Gene Accession Number'), 0)
        fgs.Add(tgaccsNum, 0, wx.EXPAND) 

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)        

class PerturbationPanel(wx.Panel):
    """
    Frame that holds all other widgets
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)
        
        # create some widgets
        self._newPageCounter = 1
       
        #panel = wx.Panel(self)
        self.createRightClickMenu()
        
        self.notebook = FlatNotebookDemo(self)
        
        addChemPageBtn = wx.Button(self, label="+ New (Chemical)")
        addChemPageBtn.Bind(wx.EVT_BUTTON, self.onChemAddPage)
        addBioPageBtn = wx.Button(self, label="+ New (Biological)")
        addBioPageBtn.Bind(wx.EVT_BUTTON, self.onBioAddPage)
        removePageBtn = wx.Button(self, label="Remove Page")
        removePageBtn.Bind(wx.EVT_BUTTON, self.onDeletePage)
        self.notebook.SetRightClickMenu(self._rmenu)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addChemPageBtn, 0, wx.ALL, 5)
        btnSizer.Add(addBioPageBtn, 0, wx.ALL, 5)
        btnSizer.Add(removePageBtn, 0, wx.ALL, 5)
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()
        

    
    def createRightClickMenu(self):
        """
        Based on method from flatnotebook demo
        """
        self._rmenu = wx.Menu()
        item = wx.MenuItem(self._rmenu, wx.ID_ANY,
                           "Close Tab\tCtrl+F4",
                           "Close Tab")
        self.Bind(wx.EVT_MENU, self.onDeletePage, item)
        self._rmenu.AppendItem(item)

    def onChemAddPage(self, event):
        """
        This method is based on the flatnotebook demo
        It adds a new page to the notebook
        """
        caption = "Perturbing Agent No. " + str(self._newPageCounter)
        self.Freeze()
        self.notebook.AddPage(self.createChemPage(caption), caption, True)
        self.Thaw()
        self._newPageCounter = self._newPageCounter + 1

    def createChemPage(self, caption):
        """
        Creates a chemical perturbing agent notebook page
        """
        return ChemPanel(self.notebook)
    
    def onBioAddPage(self, event):
        """
        This method is based on the flatnotebook demo
        It adds a new page to the notebook
        """
        caption = "Perturbing Agent No. " + str(self._newPageCounter)
        self.Freeze()
        self.notebook.AddPage(self.createBioPage(caption), caption, True)
        self.Thaw()
        self._newPageCounter = self._newPageCounter + 1

    def createBioPage(self, caption):
        """
        Creates a chemical perturbing agent notebook page
        """
        return BioPanel(self.notebook)
    
    def onDeletePage(self, event):
        """
        This method is based on the flatnotebook demo
 
        It removes a page from the notebook
        """
        self.notebook.DeletePage(self.notebook.GetSelection())
        
########################################################################        
################## STAININ SELECTION ##############################
########################################################################
class StainPanel(wx.Panel):
    """
    This page for Chemical perturbing agent parameter input
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        fgs = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        #Heading
        heading1 = wx.StaticText(self, -1, 'Staining Agent')
        heading1.SetFont(font)
        heading2 = wx.StaticText(self, -1, '')  # seting the gap for aligning the column number
        fgs.Add(heading1, 0, wx.EXPAND)
        fgs.Add(heading2, 0, wx.EXPAND)
        
        # Chemical Name
        drugName = wx.TextCtrl(self, -1)
        drugName.SetToolTipString('Name of the Staining Agent.....')
        fgs.Add(wx.StaticText(self, -1, 'Staining Agent Name'), 0)
        fgs.Add(drugName, 0, wx.EXPAND)
        # Concentration
        drugConc = wx.TextCtrl(self, -1)
        drugConc.SetToolTipString('Concentration of the SA.......')
        fgs.Add(wx.StaticText(self, -1, 'Concentration'), 0)
        fgs.Add(drugConc, 0, wx.EXPAND)
           
        # Layout with sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)


class StainingPanel(wx.Panel):
    """
    Frame that holds all other widgets
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)
        
        # create some widgets
        self._newPageCounter = 1
       
        #panel = wx.Panel(self)
        self.createRightClickMenu()
        
        self.notebook = FlatNotebookDemo(self)
        
        addStainPageBtn = wx.Button(self, label="+ New (Staining Agent)")
        addStainPageBtn.Bind(wx.EVT_BUTTON, self.onStainAddPage)
        removePageBtn = wx.Button(self, label="Remove Page")
        removePageBtn.Bind(wx.EVT_BUTTON, self.onDeletePage)
        self.notebook.SetRightClickMenu(self._rmenu)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addStainPageBtn , 0, wx.ALL, 5)
        btnSizer.Add(removePageBtn, 0, wx.ALL, 5)
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()

        self.Show()
    def createRightClickMenu(self):
        """
        Based on method from flatnotebook demo
        """
        self._rmenu = wx.Menu()
        item = wx.MenuItem(self._rmenu, wx.ID_ANY, "Close Tab\tCtrl+F4", "Close Tab")
        self.Bind(wx.EVT_MENU, self.onDeletePage, item)
        self._rmenu.AppendItem(item)

    def onStainAddPage(self, event):
        """
        This method is based on the flatnotebook demo
        It adds a new page to the notebook
        """
        caption = "Staining Agent No. " + str(self._newPageCounter)
        self.Freeze()
        self.notebook.AddPage(self.createStainPage(caption), caption, True)
        self.Thaw()
        self._newPageCounter = self._newPageCounter + 1

    def createStainPage(self, caption):
        """
        Creates a chemical perturbing agent notebook page
        """
        return StainPanel(self.notebook)
    
    def onDeletePage(self, event):
        """
        This method is based on the flatnotebook demo
 
        It removes a page from the notebook
        """
        self.notebook.DeletePage(self.notebook.GetSelection())

        
        
        
########################################################################        
################## CELL LOADING SELECTION ##############################
########################################################################
class CellLoadPanel(wx.Panel):
    """
    This page for Chemical perturbing agent parameter input
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        fgs = wx.FlexGridSizer(rows=4, cols=2, hgap=5, vgap=5)
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        stck = ['Stock Culture - U2OS', 'Stock Culture - Hela', 'Stock Culture - Fibroblast' ]
 
        
        
        #Heading
        heading1 = wx.StaticText(self, -1, 'Cell Loading')
        heading1.SetFont(font)
        heading2 = wx.StaticText(self, -1, '')  # seting the gap for aligning the column number
        fgs.Add(heading1, 0, wx.EXPAND)
        fgs.Add(heading2, 0, wx.EXPAND)
              
        #Stock Culture
        stcl = wx.StaticText(self, -1, 'Stock Culture')
        stcl.SetToolTipString('Select the stock culture from which cells are drawn')
        fgs.Add(stcl, 0, wx.EXPAND)
        fgs.Add(wx.Choice(self, -1, (85, 18), choices=stck))  
        # Seeding Density
        drugName = wx.TextCtrl(self, -1)
        drugName.SetToolTipString('Number of cells seeded in each well or flask.....')
        fgs.Add(wx.StaticText(self, -1, 'Seeding Density'), 0)
        fgs.Add(drugName, 0, wx.EXPAND)
        # Harvesting Density
        drugConc = wx.TextCtrl(self, -1)
        drugConc.SetToolTipString('Number of cells before analysis (for Flow only) simliar to how many progenitor cells per well (Imaging) before analysis')
        fgs.Add(wx.StaticText(self, -1, 'Harvesting Density'), 0)
        fgs.Add(drugConc, 0, wx.EXPAND)
           
        # Layout with sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)

class CellLoadingPanel(wx.Panel):
    """
    Frame that holds all other widgets
    """
    def __init__(self, parent, id=-1):
        """Constructor"""
        wx.Panel.__init__(self, parent, id)
        
        # create some widgets
        self._newPageCounter = 1
       
        #panel = wx.Panel(self)
        self.createRightClickMenu()
        
        self.notebook = FlatNotebookDemo(self)
        
        addStainPageBtn = wx.Button(self, label="+ Load Cells")
        addStainPageBtn.Bind(wx.EVT_BUTTON, self.onStainAddPage)
        removePageBtn = wx.Button(self, label="Remove Page")
        removePageBtn.Bind(wx.EVT_BUTTON, self.onDeletePage)
        self.notebook.SetRightClickMenu(self._rmenu)

        # create some sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # layout the widgets
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        btnSizer.Add(addStainPageBtn , 0, wx.ALL, 5)
        btnSizer.Add(removePageBtn, 0, wx.ALL, 5)
        sizer.Add(btnSizer)
        self.SetSizer(sizer)
        self.Layout()

        self.Show()
    def createRightClickMenu(self):
        """
        Based on method from flatnotebook demo
        """
        self._rmenu = wx.Menu()
        item = wx.MenuItem(self._rmenu, wx.ID_ANY, "Close Tab\tCtrl+F4", "Close Tab")
        self.Bind(wx.EVT_MENU, self.onDeletePage, item)
        self._rmenu.AppendItem(item)

    def onStainAddPage(self, event):
        """
        This method is based on the flatnotebook demo
        It adds a new page to the notebook
        """
        caption = "Loading Sequnce No. " + str(self._newPageCounter)
        self.Freeze()
        self.notebook.AddPage(self.createStainPage(caption), caption, True)
        self.Thaw()
        self._newPageCounter = self._newPageCounter + 1

    def createStainPage(self, caption):
        """
        Creates a chemical perturbing agent notebook page
        """
        return CellLoadPanel(self.notebook)
    
    def onDeletePage(self, event):
        """
        This method is based on the flatnotebook demo
 
        It removes a page from the notebook
        """
        self.notebook.DeletePage(self.notebook.GetSelection())        

##---------- Plate Well Panel----------------##
class TimeLapseImagePanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=3, cols=3, hgap=5, vgap=5) 
       
             
        #----------- Labels and Text Controler-------        
        # Start End point
        pnum = wx.Choice(self.sw, -1, choices= ['Start Point','End Point'])
        pnum.SetSelection(0)
        pnum.SetToolTipString('Start or end point of the image sequence')
        pnum.Bind(wx.EVT_CHOICE, self.OnEndPoint, pnum)
        fgs.Add(wx.StaticText(self.sw, -1, 'Start or End point'), 0)
        fgs.Add(pnum, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, ''), 0)
        
        
        # Number of Field of View
        fvnum = wx.Choice(self.sw, -1, choices= ['1','2','3','4','5','6','7','8','9','10'])
        fvnum.SetSelection(2)
        fvnum.SetToolTipString('Total number of Field of View per well')
        fvnum.Bind(wx.EVT_CHOICE, self.OnSave, fvnum)
        fgs.Add(wx.StaticText(self.sw, -1, 'Field of View per well'), 0)
        fgs.Add(fvnum, 0, wx.EXPAND)
        
        
        
        
        
        # File Save
        image = "save.png"
        svIcon = wx.Image(image, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        buttons=[]
        ## Note - give the buttons numbers 1 to 6, generating events 301 to 306
        ## because IB_BUTTON1 is 300
        for i in range(3):
            # describe a button
          
            buttons.append(wx.BitmapButton(self.sw, id=-1, bitmap=svIcon, size = (svIcon.GetWidth()+1, svIcon.GetHeight()+1)))
            ## add that button to the sizer2 geometry
            buttons[i].Bind(wx.EVT_BUTTON, self.OnSave, buttons[i])
            hbox.Add(buttons[i],1,wx.EXPAND)
        
        
        fgs.Add(hbox)
        
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
        
        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        
        #fbut = wx.BitmapButton(self.sw, id=-1, bitmap=svIcon, size = (svIcon.GetWidth()+1, svIcon.GetHeight()+1))
        ##fbut = wx.Button(self.sw, -1, label="Save Timelapse Image")
        #fbut.Bind(wx.EVT_BUTTON, self.OnSave, fbut)
        
        #fgs.Add(wx.StaticText(self.sw, -1, 'Field of view #'), 0)
        #fgs.Add(fbut, 0, wx.EXPAND)
         
                   
        #self.sw.SetSizer(fgs)
        #self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        
        
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)
    
    def OnSave(self,event):

        # Save away the edited text
        # Open the file, do an RU sure check for an overwrite!
        dlg = wx.FileDialog(self, style=wx.SAVE)
        
        # Call the dialog as a model-dialog so we're required to choose Ok or Cancel
        if dlg.ShowModal() == wx.ID_OK:
            # User has selected something, get the path, set the window's title to the path
            filename = dlg.GetPath()
            #print filename
            #self.SetTitle(filename)
            #wx.BeginBusyCursor()            
            #wx.EndBusyCursor()
                        
        dlg.Destroy()
        
        #if dlg.ShowModal() == wx.ID_OK:
            ## Grab the content to be saved
            #itcontains = self.control.GetValue()

            ## Open the file for write, write, close
            #self.filename=dlg.GetFilename()
            #self.dirname=dlg.GetDirectory()
            #filehandle=open(os.path.join(self.dirname, self.filename),'w')
            #filehandle.write(itcontains)
            #filehandle.close()
        ## Get rid of the dialog to keep things tidy
        #dlg.Destroy()
    
    def OnEndPoint(self, event):
        chc = event.GetEventObject().GetStringSelection()
        print chc
        
        #if(chc == 'End Point'):
            #print "Ask how many field of view per well"


#####################  CALENDAR PANEL   ######################        
#class CalendarPanel(wx.Panel):
    #def __init__(self, parent, id=-1):
        #wx.Panel.__init__(self, parent,id)

        #cal = wx.calendar.CalendarCtrl(self, -1, wx.DateTime_Now(), pos = (25, 50),
                                        #style=wx.calendar.CAL_SHOW_HOLIDAYS | wx.calendar.CAL_MONDAY_FIRST |
                                        #wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION)
    
        #self.cal = cal
        #self.Bind(wx.calendar.EVT_CALENDAR, self.OnCalSelected, id=cal.GetId())
    
        ## Set up control to display a set of holidays:
        #self.Bind(wx.calendar.EVT_CALENDAR_MONTH, self.OnChangeMonth, cal)
        #self.holidays = [(1,1), (10,31), (12,25)]    # (these don't move around)
        #self.OnChangeMonth()
    
    #def OnCalSelected(self, evt):
        #print 'OnCalSelected: %s' % evt.GetDate()


    #def OnChangeMonth(self, evt=None):
        #cur_month = self.cal.GetDate().GetMonth() + 1   # convert wxDateTime 0-11 => 1-12
        #for month, day in self.holidays:
            #if month == cur_month:
                #self.cal.SetHoliday(day)
  
        #if cur_month == 8:
            #attr = wx.calendar.CalendarDateAttr(border=wx.calendar.CAL_BORDER_SQUARE, colBorder="blue")
            #self.cal.SetAttr(14, attr)
        #else:
            #self.cal.ResetAttr(14)


    #def OnCalSelChanged(self, evt):
        #cal = evt.GetEventObject()
        #print "OnCalSelChanged:\n\t%s: %s\n\t%s: %s\n\t%s: %s\n\t" % ("EventObject", cal, "Date       ", cal.GetDate(),
                                                                       #"Ticks      ", cal.GetDate().GetTicks())

                                                                       

if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title='Lineageprofiler')
    p = ExperimentSettingsWindow(frame)
    frame.Show()
    app.MainLoop()
