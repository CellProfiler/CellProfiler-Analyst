import wx

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(550, 450))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        panel1 = wx.Panel(self, -1)
        panel2 = wx.Panel(self, -1)

        self.tree = wx.TreeCtrl(panel1, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS)
        root = self.tree.AddRoot('Experiment Name')
        
        self.formpanel = panel2
	        
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
              
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, id=1)
              
        vbox.Add(self.tree, 1, wx.EXPAND)
        hbox.Add(panel1, 1, wx.EXPAND)
        hbox.Add(panel2, 1, wx.EXPAND)
        
        panel1.SetSizer(vbox)
        self.SetSizer(hbox)
        
        self.Centre()

    def OnSelChanged(self, event):
        
        item =  event.GetItem()
                
        #self.display.SetLabel(self.tree.GetItemText(item))
        if self.tree.GetItemText(item) == 'Overview':
            
            #Create labels
            title_l = wx.StaticText(self.formpanel, -1, 'Project title')
            aim_l   = wx.StaticText(self.formpanel, -1, 'Project aim')
            kword_l = wx.StaticText(self.formpanel, -1, 'Keywords')
            exno_l = wx.StaticText(self.formpanel, -1, 'Experiment Number')
            pub_l = wx.StaticText(self.formpanel, -1, 'Associated publications')
            inst_l = wx.StaticText(self.formpanel, -1, 'Institution')
            dept_l = wx.StaticText(self.formpanel, -1, 'Department')
            addr_l = wx.StaticText(self.formpanel, -1, 'Address')
            sts_l = wx.StaticText(self.formpanel, -1, 'Status')
            
            
            #Create text control           
            title_t = wx.TextCtrl(self.formpanel, -1)
            title_t.SetToolTipString('Type the title of the project')
            aim_t   = wx.TextCtrl(self.formpanel, -1)
            aim_t.SetToolTipString('Detail the aim of the project')
            kword_t = wx.TextCtrl(self.formpanel, -1)
            kword_t.SetToolTipString('Keywords tags the project')
            exno_t = wx.TextCtrl(self.formpanel, -1)
            exno_t.SetToolTipString('Experiment number under this project')
            pub_t = wx.TextCtrl(self.formpanel, -1)
            pub_t.SetToolTipString('Pubmed publications')
            inst_t = wx.TextCtrl(self.formpanel, -1)
            inst_t.SetToolTipString('Institution name')
            dept_t = wx.TextCtrl(self.formpanel, -1)
            dept_t.SetToolTipString('Department name')
            addr_t = wx.TextCtrl(self.formpanel, -1)
            addr_t.SetToolTipString('Address of the department')
            sts_t = wx.TextCtrl(self.formpanel, -1)
            sts_t.SetToolTipString('Complete or under going project')
            
            # Use standard button IDs
            okay   = wx.Button(self.formpanel, wx.ID_OK)
            #self.formpanel.button.Bind(wx.EVT_BUTTON, self.OnClear, self.formpanel.button)
            okay.SetDefault()
            cancel = wx.Button(self.formpanel, wx.ID_CANCEL)
                       
            # Add the labels and text controls to the panel
            fgs = wx.FlexGridSizer(rows=9, cols=2, hgap=5, vgap=5)
            fgs.Add(title_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(title_t, 0, wx.EXPAND)
            fgs.Add(aim_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(aim_t, 0, wx.EXPAND)
            fgs.Add(kword_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(kword_t, 0, wx.EXPAND)
            fgs.Add(exno_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(exno_t, 0, wx.EXPAND)
            fgs.Add(pub_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(pub_t, 0, wx.EXPAND)
            fgs.Add(inst_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(inst_t, 0, wx.EXPAND)
            fgs.Add(dept_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(dept_t, 0, wx.EXPAND)
            fgs.Add(addr_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(addr_t, 0, wx.EXPAND)
            fgs.Add(sts_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(sts_t, 0, wx.EXPAND)
            
            fgs.AddGrowableCol(1)
            
            # Layout with sizers
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)
    
            btns = wx.StdDialogButtonSizer()
            btns.AddButton(okay)
            btns.AddButton(cancel)
            btns.Realize()
            sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)
    
            self.formpanel.SetSizer(sizer)
            sizer.Fit(self.formpanel)
        
        if self.tree.GetItemText(item) == 'Microscope':
            
            #Create labels
            mfg_l = wx.StaticText(self.formpanel, -1, 'Manufacturer')
            mdl_l   = wx.StaticText(self.formpanel, -1, 'Model')
            typ_l = wx.StaticText(self.formpanel, -1, 'Type')
            lgs_l = wx.StaticText(self.formpanel, -1, 'Light Source')
            dtc_l = wx.StaticText(self.formpanel, -1, 'Detector')
            lna_l = wx.StaticText(self.formpanel, -1, 'Lens Aparture')
            lnc_l = wx.StaticText(self.formpanel, -1, 'Lens Correction')
            ilt_l = wx.StaticText(self.formpanel, -1, 'Illumination Type')
            mde_l = wx.StaticText(self.formpanel, -1, 'Mode')
            imm_l = wx.StaticText(self.formpanel, -1, 'Immersion')
            cor_l = wx.StaticText(self.formpanel, -1, 'Correction')
            nmm_l = wx.StaticText(self.formpanel, -1, 'Nominal Magnification')
            cam_l = wx.StaticText(self.formpanel, -1, 'Calibrated Magnification')
            wrd_l = wx.StaticText(self.formpanel, -1, 'Working Distance')
            flt_l = wx.StaticText(self.formpanel, -1, 'Filter Used')
            sft_l = wx.StaticText(self.formpanel, -1, 'Software')
            
            #Create text control           
            mfg_t = wx.TextCtrl(self.formpanel, -1)
            mfg_t.SetToolTipString('Manufacturer name')
            mdl_t = wx.TextCtrl(self.formpanel, -1)
            mdl_t.SetToolTipString('Model number of the microscope')
            typ_t = wx.TextCtrl(self.formpanel, -1)
            typ_t.SetToolTipString('Type of microscope e.g. Inverted, Confocal...')
            lgs_t = wx.TextCtrl(self.formpanel, -1)
            lgs_t.SetToolTipString('Light Source')
            dtc_t = wx.TextCtrl(self.formpanel, -1)
            dtc_t.SetToolTipString('Detector')
            lna_t = wx.TextCtrl(self.formpanel, -1)
            lna_t.SetToolTipString('Lens Aparture')
            lnc_t = wx.TextCtrl(self.formpanel, -1)
            lnc_t.SetToolTipString('Lens Correction')
            ilt_t = wx.TextCtrl(self.formpanel, -1)
            ilt_t.SetToolTipString('Illumination Type')
            mde_t = wx.TextCtrl(self.formpanel, -1)
            mde_t.SetToolTipString('Mode')
            imm_t = wx.TextCtrl(self.formpanel, -1)
            imm_t.SetToolTipString('Immersion')
            cor_t = wx.TextCtrl(self.formpanel, -1)
            cor_t.SetToolTipString('Correction')
            nmm_t = wx.TextCtrl(self.formpanel, -1)
            nmm_t.SetToolTipString('Nominal Magnification')
            cam_t = wx.TextCtrl(self.formpanel, -1)
            cam_t.SetToolTipString('Calibrated Magnification')
            wrd_t = wx.TextCtrl(self.formpanel, -1)
            wrd_t.SetToolTipString('Working distance')
            flt_t = wx.TextCtrl(self.formpanel, -1)
            flt_t.SetToolTipString('Filter used in the microscope')
            sft_t = wx.TextCtrl(self.formpanel, -1)
            sft_t.SetToolTipString('Name and version of the software used')
            
            # Use standard button IDs
            okay   = wx.Button(self.formpanel, wx.ID_OK)
            #okay.Bind(wx.EVT_BUTTON, self.OnClear,  okay)
            #okay.SetDefault()
            cancel = wx.Button(self.formpanel, wx.ID_CANCEL)
            
            
            #okya   = wx.Button(self.formpanel, wx.ID_OK)
            #self.formpanel.Bind(wx.EVT_BUTTON, self.formpanel.OnClear, self.formpanel.button)
            
            
            #cancel = wx.Button(self.formpanel, wx.ID_CANCEL)
            #okya.SetDefault()
            
            
            
            

            
            # Add the labels and text controls to the panel
            fgs = wx.FlexGridSizer(rows=16, cols=2, hgap=5, vgap=5)
            fgs.Add(mfg_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(mfg_t, 0, wx.EXPAND)
            fgs.Add(mdl_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(mdl_t, 0, wx.EXPAND)
            fgs.Add(typ_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(typ_t, 0, wx.EXPAND)
            fgs.Add(lgs_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(lgs_t, 0, wx.EXPAND)
            fgs.Add(dtc_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(dtc_t, 0, wx.EXPAND)
            fgs.Add(lna_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(lna_t, 0, wx.EXPAND)
            fgs.Add(lnc_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(lnc_t, 0, wx.EXPAND)
            fgs.Add(ilt_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(ilt_t, 0, wx.EXPAND)
            fgs.Add(mde_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(mde_t, 0, wx.EXPAND)
            fgs.Add(imm_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(imm_t, 0, wx.EXPAND)
            fgs.Add(cor_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(cor_t, 0, wx.EXPAND)
            fgs.Add(nmm_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(nmm_t, 0, wx.EXPAND)
            fgs.Add(cam_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(cam_t, 0, wx.EXPAND)
            fgs.Add(wrd_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(wrd_t, 0, wx.EXPAND)
            fgs.Add(flt_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(flt_t, 0, wx.EXPAND)
            fgs.Add(sft_l, 0, wx.ALIGN_RIGHT)
            fgs.Add(sft_t, 0, wx.EXPAND)
            
            fgs.AddGrowableCol(1)
            
            # Layout with sizers
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)
    
            btns = wx.StdDialogButtonSizer()
            btns.AddButton(okay)
            btns.AddButton(cancel)
            btns.Realize()
            sizer.Add(btns, 0, wx.EXPAND|wx.ALL, 5)
    
            self.formpanel.SetSizer(sizer)
            sizer.Fit(self.formpanel)
            
        if self.tree.GetItemText(item) == 'Chemical':
            
	    self.nb = wx.Notebook(self)
	    
            for page in ("Drug 1","Drug 2","Drug 3"):
	
		panel = wx.Panel(self.nb)
		self.nb.AddPage(panel,page)
        
        def OnClear(self, event):
            print "I am here"
             #self.Close(True)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame(None, -1, 'Lineageprofiler')
    frame.Show()
    app.MainLoop()
