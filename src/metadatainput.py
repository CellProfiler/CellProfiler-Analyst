import wx
import  wx.calendar
import wx.lib.agw.flatnotebook as fnb
import wx.lib.mixins.listctrl  as  listmix

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


class ExperimentSettings(object):
    def __init__(self):
        #TODO: come up with a structure to hold ALL settings data
        pass
    
    def save_to_file(self, file):
        pass
    
    def load_from_file(self, file):
        pass


class OverviewPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=10, cols=2, hgap=5, vgap=5)
        
        # Project Title
        ptl = wx.TextCtrl(self.sw, -1, style=wx.TE_MULTILINE)
        ptl.SetToolTipString('The title of the project')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Title'), 0)
        fgs.Add(ptl, 0, wx.EXPAND)
        # Project Aim
        pam = wx.TextCtrl(self.sw, -1, style=wx.TE_MULTILINE)
        pam.SetToolTipString('Project Aim....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Project Aim'), 0)
        fgs.Add(pam, 0, wx.EXPAND)
        # Keywords
        kwd = wx.TextCtrl(self.sw, -1, style=wx.TE_MULTILINE)
        kwd.SetToolTipString('Keywords....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Keywords'), 0)
        fgs.Add(kwd, 0, wx.EXPAND)
        # Experiment Number
        expn = wx.TextCtrl(self.sw, -1)
        expn.SetToolTipString('Experiment Number....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Number'), 0)
        fgs.Add(expn, 0, wx.EXPAND)
        ## Experiment Date
        cald = wx.calendar.CalendarCtrl(self.sw, -1, wx.DateTime_Now(), 
                                         style=wx.calendar.CAL_SHOW_HOLIDAYS | wx.calendar.CAL_MONDAY_FIRST |
                                         wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION)
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Date'), 0)
        fgs.Add(cald, 0, wx.EXPAND)
        # Publication
        pub = wx.TextCtrl(self.sw, -1, style=wx.TE_MULTILINE)
        pub.SetToolTipString('Publication....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Publication'), 0)
        fgs.Add(pub, 0, wx.EXPAND)
        # Institution Name
        inst = wx.TextCtrl(self.sw, -1)
        inst.SetToolTipString('Institution Name....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Institution Name'), 0)
        fgs.Add(inst, 0, wx.EXPAND)
        # Department Name
        dept = wx.TextCtrl(self.sw, -1)
        dept.SetToolTipString('Department Name....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Department Name'), 0)
        fgs.Add(dept, 0, wx.EXPAND)
        # Address
        addr = wx.TextCtrl(self.sw, -1, style=wx.TE_MULTILINE)
        addr.SetToolTipString('Address Name....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Address'), 0)
        fgs.Add(addr, 0, wx.EXPAND)
        # Status
        sts = wx.TextCtrl(self.sw, -1)
        sts.SetToolTipString('Status....')
        fgs.Add(wx.StaticText(self.sw, -1, 'Status'), 0)
        fgs.Add(sts, 0, wx.EXPAND)
 

        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)
        
        
class MicroscopePanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):

        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=16, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        # Manufacture
        mfg = wx.TextCtrl(self.sw, -1)
        mfg.SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(mfg, 0, wx.EXPAND)
        # Model
        mdl = wx.TextCtrl(self.sw, -1)
        mdl.SetToolTipString('Model number of the microscope')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(mdl, 0, wx.EXPAND)
        # Microscope type
        mtyp = wx.TextCtrl(self.sw, -1)
        mtyp.SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(mtyp, 0, wx.EXPAND)
        # Light source
        mtyp = wx.TextCtrl(self.sw, -1)
        mtyp.SetToolTipString('Light source...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(mtyp, 0, wx.EXPAND)
        # Detector
        dect = wx.TextCtrl(self.sw, -1)
        dect.SetToolTipString('Detector...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Detector'), 0)
        fgs.Add(dect, 0, wx.EXPAND)
        # Lense Aperture
        lnap = wx.TextCtrl(self.sw, -1)
        lnap.SetToolTipString('Aparture of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lense Apparture'), 0)
        fgs.Add(lnap, 0, wx.EXPAND)
        # Lense Correction
        lcorr = wx.TextCtrl(self.sw, -1)
        lcorr.SetToolTipString('Correction of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lense Correction'), 0)
        fgs.Add(lcorr, 0, wx.EXPAND)
        # Illumination Type
        iltyp = wx.TextCtrl(self.sw, -1)
        iltyp.SetToolTipString('Illumuniation of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Lense Correction'), 0)
        fgs.Add(iltyp, 0, wx.EXPAND)
        # Mode
        mde = wx.TextCtrl(self.sw, -1)
        mde.SetToolTipString('Mode of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Mode'), 0)
        fgs.Add(mde, 0, wx.EXPAND)
        # Immersion
        imrs = wx.TextCtrl(self.sw, -1)
        imrs.SetToolTipString('Immersion of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
        fgs.Add(imrs, 0, wx.EXPAND)
        # Correction
        corr = wx.TextCtrl(self.sw, -1)
        corr.SetToolTipString('Correction of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
        fgs.Add(corr, 0, wx.EXPAND)
        # Nominal Magnification
        nmfg = wx.TextCtrl(self.sw, -1)
        nmfg.SetToolTipString('Nominal Magnification of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
        fgs.Add(nmfg, 0, wx.EXPAND)
        # Calibrated Magnification
        cmfg = wx.TextCtrl(self.sw, -1)
        cmfg.SetToolTipString('Calibrated Magnification of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
        fgs.Add(cmfg, 0, wx.EXPAND)
        # Working distance
        wdst = wx.TextCtrl(self.sw, -1)
        wdst.SetToolTipString('Working distance of the lense...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Working distance'), 0)
        fgs.Add(wdst, 0, wx.EXPAND)
        # Filter used
        fusd = wx.TextCtrl(self.sw, -1)
        fusd.SetToolTipString('Filter used in the microscope...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
        fgs.Add(fusd, 0, wx.EXPAND)
        # Software
        sft = wx.TextCtrl(self.sw, -1)
        sft.SetToolTipString('Name and version of the software used...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Software'), 0)
        fgs.Add(sft, 0, wx.EXPAND)
        
        
        #---------------Layout with sizers---------------
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
     
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)

class FlowCytometerPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=7, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        # Manufacture
        mfg = wx.TextCtrl(self.sw, -1)
        mfg.SetToolTipString('Manufacturer name')
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(mfg, 0, wx.EXPAND)
        # Model
        mdl = wx.TextCtrl(self.sw, -1)
        mdl.SetToolTipString('Model number of the Flowcytometer')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(mdl, 0, wx.EXPAND)
        # Flowcytometer type
        mtyp = wx.TextCtrl(self.sw, -1)
        mtyp.SetToolTipString('Type of Flow Cytometer...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(mtyp, 0, wx.EXPAND)
        # Light source
        mtyp = wx.TextCtrl(self.sw, -1)
        mtyp.SetToolTipString('Light source...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(mtyp, 0, wx.EXPAND)
        # Detector
        dect = wx.TextCtrl(self.sw, -1)
        dect.SetToolTipString('Detector...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Detector'), 0)
        fgs.Add(dect, 0, wx.EXPAND)
        # Filter used
        fusd = wx.TextCtrl(self.sw, -1)
        fusd.SetToolTipString('Filter used in the microscope...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter used'), 0)
        fgs.Add(fusd, 0, wx.EXPAND)
        # Software
        sft = wx.TextCtrl(self.sw, -1)
        sft.SetToolTipString('Name and version of the software used...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Software'), 0)
        fgs.Add(sft, 0, wx.EXPAND)
        
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)

##---------- Plate Well Panel----------------##
class PlateWellPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=5, cols=2, hgap=5, vgap=5) 
       
        plateNum = ['1','2','3','4','5','6','7','8','9','10']
        plateDsg = ["6 Well (2x3)", "96 Well (8x12)", "384 Well (16x24)", "1536 Well (32x48)", "5600 Well (40x140)" ]
      
        #----------- Plate Labels and Text Controler-------        
        # Stock Culture Relationship
        pnum = wx.Choice(self.sw, -1, choices= ['Stock Culture - U2OS', 'Stock Culture - HeLA'])
        pnum.SetToolTipString('Selecting the stock culture')
        fgs.Add(wx.StaticText(self.sw, -1, 'Related Stock Culture'), 0)
        fgs.Add(pnum, 0, wx.EXPAND)
        # Plate Number
        pnum = wx.Choice(self.sw, -1, choices= plateNum)
        pnum.SetToolTipString('Total number of plates')
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Number'), 0)
        fgs.Add(pnum, 0, wx.EXPAND)
        # Plate Design
        pdsg = wx.Choice(self.sw, -1, (85, 18), choices=plateDsg)
        pdsg.SetToolTipString('Design of the plate')
        fgs.Add(wx.StaticText(self.sw, -1, 'Plate Design'), 0)
        fgs.Add(pdsg, 0, wx.EXPAND)
        # Plate Material
        pmtr = wx.TextCtrl(self.sw, -1)
        pmtr.SetToolTipString('Material of the Plate, e.g. Plastic, Glass, etc..')
        fgs.Add(wx.StaticText(self.sw, -1, 'Material'), 0)
        fgs.Add(pmtr, 0, wx.EXPAND)
        # Plate Size
        psiz = wx.TextCtrl(self.sw, -1)
        psiz.SetToolTipString('Diameter of well in mm...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Well Diameter'), 0)
        fgs.Add(psiz, 0, wx.EXPAND)
        
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)

##---------- Flast Panel----------------##
class FlaskPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        # Attach the scrolling option with the panel
        self.sw = wx.ScrolledWindow(self)
        # Attach a flexi sizer for the text controler and labels
        fgs = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5) 
       
        flaskNum = ['1','2','3','4','5','6','7','8','9','10']
       
        #----------- Flask Labels and Text Controler-------        
        # Stock Culture Relationship
        pnum = wx.Choice(self.sw, -1, choices= ['Stock Culture - U2OS', 'Stock Culture - HeLA'])
        pnum.SetToolTipString('Selecting the stock culture')
        fgs.Add(wx.StaticText(self.sw, -1, 'Related Stock Culture'), 0)
        fgs.Add(pnum, 0, wx.EXPAND)
        
        # Flask Number
        fnum = wx.Choice(self.sw, -1, choices= flaskNum)
        fnum.SetToolTipString('Total number of Flasks')
        fgs.Add(wx.StaticText(self.sw, -1, 'Flask Number'), 0)
        fgs.Add(fnum, 0, wx.EXPAND)
        # Flask Material
        pmtr = wx.TextCtrl(self.sw, -1)
        pmtr.SetToolTipString('Flask material e.g. Platic...')
        fgs.Add(wx.StaticText(self.sw, -1, 'Material of the Flask'), 0)
        fgs.Add(pmtr, 0, wx.EXPAND)
             
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)        
    
        
        
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
    def __init__(self, parent):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
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
        self._newPageCounter = 1
       
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
        caption = "Stock Culture No. " + str(self._newPageCounter)
        self.Freeze()
        self.notebook.AddPage(self.createStainPage(caption), caption, True)
        self.Thaw()
        self._newPageCounter = self._newPageCounter + 1

    def createStainPage(self, caption):
        """
        Creates a chemical perturbing agent notebook page
        """
        return StockCulturePanel(self.notebook)
    
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
