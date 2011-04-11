import wx
import  wx.lib.intctrl
import wx.lib.agw.floatspin as FS
import normalize as norm
import dbconnect
import properties

p = properties.Properties.getInstance()

GROUP_CHOICES = ['experiment', 'plate', 'quad', 'neighbors', 'constant']
AGG_CHOICES = ['mean', 'median', 'mode']

class NormalizationStepPanel(wx.Panel):
    def __init__(self, parent, id=-1, allow_delete=True, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        
        self.window_group = wx.Choice(self, -1, choices=GROUP_CHOICES)
        self.window_group.Select(0)
        self.agg_type = wx.Choice(self, -1, choices=AGG_CHOICES)
        self.agg_type.Select(0)
        self.constant_float = FS.FloatSpin(self, -1, increment=1, value=1.0)
        self.constant_float.Hide()
        self.window_type = wx.RadioBox(self, -1, 'Window type', choices=['linear', 'linear (meander)', 'square'])
        self.window_type.Disable()
        self.window_size = wx.lib.intctrl.IntCtrl(self, value=3, min=1, max=100)
        self.window_size.Disable()
        self.window_size.SetForegroundColour(wx.LIGHT_GREY)
                
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Divide values by:'))
        sz.AddSpacer((5,-1))
        sz.Add(self.window_group)
        sz.AddSpacer((5,-1))
        sz.Add(self.agg_type)
        sz.Add(self.constant_float)
        if allow_delete:
            self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))
            sz.AddStretchSpacer()
            sz.Add(self.x_btn)
            self.x_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        self.Sizer.Add(sz, 1, wx.EXPAND)
        
        self.Sizer.Add(self.window_type, 0, wx.LEFT, 30)
        self.Sizer.AddSpacer((-1,15))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Window size:'), 0)
        sz.AddSpacer((5,-1))
        sz.Add(self.window_size, 0)
        self.Sizer.Add(sz, 1, wx.EXPAND|wx.LEFT, 30)
        
        self.window_group.Bind(wx.EVT_CHOICE, self.on_window_group_selected)
        self.Fit()

    def on_window_group_selected(self, evt):
        selected_string = self.window_group.GetStringSelection()
        self.window_type.Disable()
        self.window_size.Disable()
        self.window_size.SetForegroundColour(wx.LIGHT_GREY)
        self.agg_type.Show()
        self.constant_float.Hide()
        if selected_string == 'neighbors':
            self.window_type.Enable()
            self.window_size.Enable()
            self.window_size.SetForegroundColour(wx.BLACK)
        elif selected_string == 'constant':
            self.agg_type.Hide()
            self.constant_float.Show()
        self.Refresh()
        self.Layout()
        
    def on_remove(self, evt):
        self.GrandParent.remove_norm_step(self)
        
    def get_configuration_dict(self):
        '''returns a dictionary of configuration settings to be used by 
        normalize.do_normalization_step.
        IMPORTANT: these key names must match the parameter names of
            do_normalization_step
        '''
        return {norm.P_GROUPING : self.window_group.GetStringSelection(), 
                norm.P_AGG_TYPE : self.agg_type.GetStringSelection(), 
                norm.P_CONSTANT : self.constant_float.GetValue() if self.window_group.GetStringSelection()=='constant' else None, 
                norm.P_WIN_TYPE : self.window_type.GetStringSelection() if self.window_group.GetStringSelection()=='neighbors' else None, 
                norm.P_WIN_SIZE : self.window_size.Value if self.window_group.GetStringSelection()=='neighbors' else None
                }

class NormalizationUI(wx.Frame):
    '''
    '''
    def __init__(self, parent=None, id=-1, title='Normalization Settings', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        
        self.n_steps = 1
        
        #
        # Define the controls
        #
        db = dbconnect.DBConnect.getInstance()
        measurements = db.GetColumnNames(p.image_table)
        types = db.GetColumnTypes(p.image_table)
        numeric_columns = [m for m,t in zip(measurements, types) if t in [float, int, long]]
        self.col_choices = wx.CheckListBox(self, -1, choices=numeric_columns, size=(-1, 100))
        add_norm_step_btn = wx.Button(self, -1, 'Add normalization step')
        norm_meas_checkbox = wx.CheckBox(self, -1, 'Normalized measurement')
        norm_value_checkbox = wx.CheckBox(self, -1, 'Normalization value')
        prefix_text = wx.TextCtrl(self, -1, '')
        
        self.do_norm_btn = wx.Button(self, wx.ID_OK, 'Perform Normalization')
                
        self.norm_steps = [ ]
        self.boxes = [ ]
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.Sizer.Add(wx.StaticText(self, -1, 'Select measurements to normalize:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer((-1,5))
        self.Sizer.Add(self.col_choices, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        
        #
        # Lay out the first normalization step inside a scrolled window
        # and a static box sizer.
        #
        self.Sizer.Add(wx.StaticText(self, -1, 'Specify the normalization steps you want to perform:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.sw = wx.ScrolledWindow(self)
        sbs = wx.StaticBoxSizer(wx.StaticBox(self.sw, label=''), wx.VERTICAL)
        sbs.Add(NormalizationStepPanel(self.sw, allow_delete=False), 0, wx.EXPAND)
        self.sw.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.sw.Sizer.Add(sbs, 0, wx.EXPAND)
        (w,h) = self.sw.Sizer.GetSize()
        self.sw.SetScrollbars(20,20,w/20,h/20,0,0)
        self.Sizer.AddSpacer((-1,5))
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddStretchSpacer()
        sz.Add(add_norm_step_btn, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Output format:'), 0, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(norm_meas_checkbox, 0, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(norm_value_checkbox, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Choose a prefix for each normalized measurement:'), 0, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(prefix_text, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddStretchSpacer()
        sz.Add(self.do_norm_btn, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.ALL, 15)
        
        add_norm_step_btn.Bind(wx.EVT_BUTTON, self.on_add_norm_step)
        self.do_norm_btn.Bind(wx.EVT_BUTTON, self.on_do_normalization)

    def on_add_norm_step(self, evt):
        self.add_norm_step()
        
    def add_norm_step(self):
        sz = wx.StaticBoxSizer(wx.StaticBox(self.sw, label=''), wx.VERTICAL)
        self.norm_steps += [NormalizationStepPanel(self.sw)]
        self.boxes += [sz]
        sz.Add(self.norm_steps[-1], 0, wx.EXPAND)
        self.sw.Sizer.InsertSizer(len(self.norm_steps), sz, 0, wx.EXPAND|wx.TOP, 15)
        self.sw.FitInside()
        self.Layout()
        
    def remove_norm_step(self, panel):
        idx = self.norm_steps.index(panel)
        self.norm_steps.remove(panel)
        panel.Destroy()
        # remove the statix box that was holding the panel
        sbox = self.boxes.pop(idx)
        self.sw.Sizer.Remove(sbox)
        self.sw.FitInside()
        self.Layout()
        
    def get_selected_measurement_columns(self):
        return self.col_choices.GetCheckedStrings()

    def on_do_normalization(self, evt):
        self.do_normalization()
        
    def do_normalization(self):
        '''
        '''
        # Get the data from the db
        db = dbconnect.DBConnect.getInstance()
        meas_col_names = self.col_choices.GetCheckedStrings()
        FIRST_MEAS_INDEX = len(dbconnect.image_key_columns() + dbconnect.well_key_columns())
        WELL_KEY_INDEX = len(dbconnect.image_key_columns())
        query = "SELECT %s, %s, %s FROM %s"%(dbconnect.UniqueImageClause(), 
                                             dbconnect.UniqueWellClause(), 
                                             ', '.join(meas_col_names),
                                             p.image_table)
        input_data = np.array(db.execute(query), dtype=object)
        well_keys = input_data[:, range(WELL_KEY_INDEX, FIRST_MEAS_INDEX)]
        
        output_normed = []
        output_factors = []
        for colnum, col in enumerate(input_data[:,FIRST_MEAS_INDEX:].T):
            norm_data = col.copy()
            for step_panel in self.norm_steps:
                d = step_panel.get_configuration_dict()
                if d[norm.P_GROUPING] in (norm.G_PLATE, norm.G_QUADRANT, norm.G_WELL_NEIGHBORS):
                    # Reshape data if norm step is plate sensitive.
                    assert p.plate_id and p.well_id
                    norm_data, wks = FormatPlateMapData(np.hstack((well_keys, np.array([norm_data]).T)))
                    
                norm_data, norm_factors = norm.do_normalization_step(norm_data, **d)

                if d[norm.P_GROUPING] in (norm.G_PLATE, norm.G_QUADRANT, norm.G_WELL_NEIGHBORS):
                    norm_data.flatten()
            output_columns += [norm_data]
            output_factors += [norm_factors]

            
        
        output_table = '2008_11_05_QualityControlForScreens'            
        db.execute('DROP TABLE IF EXISTS %s'%(output_table))
        col_defs = ', '.join(['%s %s'%(col, db.GetColumnTypeString(col))
                              for col in dbconnect.image_key_columns() + dbconnect.well_key_columns()])
        col_defs += ', '.join(['%s_Norm %s'%(col, db.GetColumnTypeString(col))
                               for col in meas_col_names]) 
        db.execute('CREATE TABLE %s (%s)'%(output_table, col_defs))
        
        for i, (val, factor) in enumerate(zip(norm_data, norm_factors)):
            db.execute('INSERT INTO %s values (%s)'%(output_table, ','.join(input_data[i, :FIRST_MEAS_INDEX] + [val])))
        

if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    if p.show_load_dialog():
        f = NormalizationUI(size=(700,500))
        f.Show()
        f.Center()
    
    app.MainLoop()
