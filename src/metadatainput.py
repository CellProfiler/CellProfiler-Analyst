import wx

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
        print 'init overview panel'
        wx.Panel.__init__(self, parent, id, **kwargs)
        self.sw = wx.ScrolledWindow(self)
        #Create text controls
        title_t = wx.TextCtrl(self.sw, -1)
        title_t.SetToolTipString('Type the title of the project')
        aim_t   = wx.TextCtrl(self.sw, -1)
        aim_t.SetToolTipString('Detail the aim of the project')
        kword_t = wx.TextCtrl(self.sw, -1)
        kword_t.SetToolTipString('Keywords tags the project')
        exno_t = wx.TextCtrl(self.sw, -1)
        exno_t.SetToolTipString('Experiment number under this project')
        pub_t = wx.TextCtrl(self.sw, -1)
        pub_t.SetToolTipString('Pubmed publications')
        inst_t = wx.TextCtrl(self.sw, -1)
        inst_t.SetToolTipString('Institution name')
        dept_t = wx.TextCtrl(self.sw, -1)
        dept_t.SetToolTipString('Department name')
        addr_t = wx.TextCtrl(self.sw, -1)
        addr_t.SetToolTipString('Address of the department')
        sts_t = wx.TextCtrl(self.sw, -1)
        sts_t.SetToolTipString('Complete or under going project')
        
        self.settings = {'title' : title_t,
                         'aim' : aim_t,
                         }
                
        # Add labels and text controls to the sizer
        fgs = wx.FlexGridSizer(rows=9, cols=2, hgap=5, vgap=5)
        fgs.Add(wx.StaticText(self.sw, -1, 'Project title'), 0)
        fgs.Add(title_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Project aim'), 0)
        fgs.Add(aim_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Keywords'), 0)
        fgs.Add(kword_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Experiment Number'), 0)
        fgs.Add(exno_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Associated publications'), 0)
        fgs.Add(pub_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Institution'), 0)
        fgs.Add(inst_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Department'), 0)
        fgs.Add(dept_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Address'), 0)
        fgs.Add(addr_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Status'), 0)
        fgs.Add(sts_t, 0, wx.EXPAND)

        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        #self.button.Bind(wx.EVT_BUTTON, self.OnClear, self.button)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)
        
        
class MicroscopePanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        print 'init microscope panel'
        wx.Panel.__init__(self, parent, id, **kwargs)
        self.sw = wx.ScrolledWindow(self)
        
        #Create text control           
        mfg_t = wx.TextCtrl(self.sw, -1)
        mfg_t.SetToolTipString('Manufacturer name')
        mdl_t = wx.TextCtrl(self.sw, -1)
        mdl_t.SetToolTipString('Model number of the microscope')
        typ_t = wx.TextCtrl(self.sw, -1)
        typ_t.SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
        lgs_t = wx.TextCtrl(self.sw, -1)
        lgs_t.SetToolTipString('Light Source')
        dtc_t = wx.TextCtrl(self.sw, -1)
        dtc_t.SetToolTipString('Detector')
        lna_t = wx.TextCtrl(self.sw, -1)
        lna_t.SetToolTipString('Lens Aperture')
        lnc_t = wx.TextCtrl(self.sw, -1)
        lnc_t.SetToolTipString('Lens Correction')
        ilt_t = wx.TextCtrl(self.sw, -1)
        ilt_t.SetToolTipString('Illumination Type')
        mde_t = wx.TextCtrl(self.sw, -1)
        mde_t.SetToolTipString('Mode')
        imm_t = wx.TextCtrl(self.sw, -1)
        imm_t.SetToolTipString('Immersion')
        cor_t = wx.TextCtrl(self.sw, -1)
        cor_t.SetToolTipString('Correction')
        nmm_t = wx.TextCtrl(self.sw, -1)
        nmm_t.SetToolTipString('Nominal Magnification')
        cam_t = wx.TextCtrl(self.sw, -1)
        cam_t.SetToolTipString('Calibrated Magnification')
        wrd_t = wx.TextCtrl(self.sw, -1)
        wrd_t.SetToolTipString('Working distance')
        flt_t = wx.TextCtrl(self.sw, -1)
        flt_t.SetToolTipString('Filter used in the microscope')
        sft_t = wx.TextCtrl(self.sw, -1)
        sft_t.SetToolTipString('Name and version of the software used')


        # Add the labels and text controls to the panel
        fgs = wx.FlexGridSizer(rows=16, cols=2, hgap=5, vgap=5)
        fgs.Add(wx.StaticText(self.sw, -1, 'Manufacturer'), 0)
        fgs.Add(mfg_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Model'), 0)
        fgs.Add(mdl_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Type'), 0)
        fgs.Add(typ_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Light Source'), 0)
        fgs.Add(lgs_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Detector'), 0)
        fgs.Add(dtc_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Lens Aperture'), 0)
        fgs.Add(lna_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Lens Correction'), 0)
        fgs.Add(lnc_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Illumination Type'), 0)
        fgs.Add(ilt_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Mode'), 0)
        fgs.Add(mde_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Immersion'), 0)
        fgs.Add(imm_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Correction'), 0)
        fgs.Add(cor_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Nominal Magnification'), 0)
        fgs.Add(nmm_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Calibrated Magnification'), 0)
        fgs.Add(cam_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Working Distance'), 0)
        fgs.Add(wrd_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Filter Used'), 0)
        fgs.Add(flt_t, 0, wx.EXPAND)
        fgs.Add(wx.StaticText(self.sw, -1, 'Software'), 0)
        fgs.Add(sft_t, 0, wx.EXPAND)
        
        self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)
        # Use standard button IDs
        okay = wx.Button(self, wx.ID_OK)
        #self.button.Bind(wx.EVT_BUTTON, self.OnClear, self.button)
        okay.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL)
        btns = wx.StdDialogButtonSizer()
        btns.AddButton(okay)
        btns.AddButton(cancel)
        btns.Realize()
        self.Sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)


class TemplatePanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        print 'init microscope panel'
        wx.Panel.__init__(self, parent, id, **kwargs)
        self.sw = wx.ScrolledWindow(self)
        
        fgs = wx.FlexGridSizer(rows=16, cols=2, hgap=5, vgap=5)
        
        # Add settings line 
        ctrl = wx.TextCtrl(self.sw, -1)
        ctrl.SetToolTipString('tooltip')
        fgs.Add(wx.StaticText(self.sw, -1, 'label'), 0)
        fgs.Add(ctrl, 0, wx.EXPAND)
        # Add settings line 
        ctrl = wx.TextCtrl(self.sw, -1)
        ctrl.SetToolTipString('tooltip')
        fgs.Add(wx.StaticText(self.sw, -1, 'label'), 0)
        fgs.Add(ctrl, 0, wx.EXPAND)
        
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
        
        
class ExperimentSettingsWindow(wx.SplitterWindow):
    def __init__(self, parent, id=-1, **kwargs):
        wx.SplitterWindow.__init__(self, parent, id, **kwargs)
        
        self.tree = wx.TreeCtrl(self, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS)
        root = self.tree.AddRoot('Experiment Name')
        
        ovr = self.tree.AppendItem(root, 'Overview')
        ins = self.tree.AppendItem(root, 'Instrument Settings')
        exv = self.tree.AppendItem(root, 'Experimental Vessel')
        stc = self.tree.AppendItem(root, 'Stock Culture')
        cld = self.tree.AppendItem(root, 'Cell Loading')
        ptb = self.tree.AppendItem(root, 'Perturbation')
        stn = self.tree.AppendItem(root, 'Staining')
        adp = self.tree.AppendItem(root, 'Additional Processes')
        dta = self.tree.AppendItem(root, 'Data Acquisition')

        self.tree.AppendItem(ins, 'Microscope')
        self.tree.AppendItem(ins, 'Flowcytometer')

        self.tree.AppendItem(exv, 'Plate')
        self.tree.AppendItem(exv, 'Flask')

        self.tree.AppendItem(ptb, 'Biological')
        self.tree.AppendItem(ptb, 'Chemical')
        self.tree.AppendItem(ptb, 'Physical')

        self.tree.AppendItem(adp, 'Spin')
        self.tree.AppendItem(adp, 'Wash')
        self.tree.AppendItem(adp, 'Dry')
        self.tree.AppendItem(adp, 'Harvest')
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
        #self.display.SetLabel(self.tree.GetItemText(item))
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
        elif self.tree.GetItemText(item) == 'Chemical':
            pass
            #self.nb = wx.Notebook(self)
            #for page in ('Drug 1', 'Drug 2', 'Drug 3'):
                #panel = wx.Panel(self.nb)
                #self.nb.AddPage(panel,page)
        
        self.settings_container.Layout()
        

if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title='Lineageprofiler')
    p = ExperimentSettingsWindow(frame)
    frame.Show()
    app.MainLoop()
