import wx
import  wx.lib.intctrl
import wx.lib.agw.floatspin as FS

GROUP_CHOICES = ['experiment', 'plate', 'quad']
AGG_CHOICES = ['mean', 'median', 'mode']

class NormalizationStepPanel(wx.Panel):
    def __init__(self, parent, id=-1, allow_delete=True, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        
        self.window_group = wx.Choice(self, -1, choices=GROUP_CHOICES)
        self.window_group.Select(0)
        self.agg_type = wx.Choice(self, -1, choices=AGG_CHOICES)
        self.agg_type.Select(0)
        self.compute_from_neighbors_checkbox = wx.CheckBox(self, -1, 'Compute the value from spatial neighbors?')
        self.window_type = wx.RadioBox(self, -1, 'Window type', choices=['linear', 'square'])
        self.window_size = wx.lib.intctrl.IntCtrl(self, value=3, min=1, max=100)
        self.compute_from_neighbors_checkbox.Set3StateValue(True)
        self.specify_constant_check = wx.CheckBox(self, -1, 'Divide by constant value') # TODO: Specify either a single numeric value or a per-image measurement
        self.constant_float = FS.FloatSpin(self, -1, increment=1, value=1.0)
        self.constant_float.Disable()
                
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Divide values by:'))
        sz.AddSpacer((5,-1))
        sz.Add(self.window_group)
        sz.AddSpacer((5,-1))
        sz.Add(self.agg_type)
        if allow_delete:
            self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))
            sz.AddStretchSpacer()
            sz.Add(self.x_btn)
            self.x_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        self.Sizer.Add(sz, 1, wx.EXPAND)

        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, '        OR '))
        sz.AddSpacer((5,-1))
        sz.Add(self.specify_constant_check)
        sz.AddSpacer((5,-1))
        sz.Add(self.constant_float)
        self.Sizer.Add(sz, 1, wx.EXPAND)
        

        self.Sizer.Add(self.compute_from_neighbors_checkbox, 1, wx.EXPAND)
        self.Sizer.Add(self.window_type, 0, wx.LEFT, 30)
        self.Sizer.AddSpacer((-1,15))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Window size:'), 0)
        sz.AddSpacer((5,-1))
        sz.Add(self.window_size, 0)
        self.Sizer.Add(sz, 1, wx.EXPAND|wx.LEFT, 30)
        
        self.compute_from_neighbors_checkbox.Bind(wx.EVT_CHECKBOX, self.on_compute_from_neighbors_check)
        self.specify_constant_check.Bind(wx.EVT_CHECKBOX, self.on_specify_constant)
        self.Fit()

    def on_compute_from_neighbors_check(self, evt):
        self.window_type.Enable(evt.Checked())
        self.window_size.Enable(evt.Checked())
        if evt.Checked():
            self.window_size.SetForegroundColour(wx.BLACK)
        else: 
            self.window_size.SetForegroundColour(wx.LIGHT_GREY)

    def on_specify_constant(self, evt):
        self.constant_float.Enable(evt.Checked())
        self.window_group.Enable(not evt.Checked())
        self.agg_type.Enable(not evt.Checked())
        
        if evt.Checked():
            self.constant_float.GetTextCtrl().SetForegroundColour(wx.BLACK)
            self.window_group.Clear()
            self.agg_type.Clear()
        else: 
            self.constant_float.GetTextCtrl().SetForegroundColour(wx.LIGHT_GREY)
            self.window_group.SetItems(GROUP_CHOICES)
            self.window_group.Select(0)
            self.agg_type.SetItems(AGG_CHOICES)
            self.agg_type.Select(0)
            
    def on_remove(self, evt):
        self.GrandParent.remove_norm_step(self)
        
    def settings(self):
        return [self.window_group, 
                self.agg_type, 
                self.compute_from_neighbors_checkbox, 
                self.window_type, 
                self.window_size,]
    
    def get_values(self):
        return [s.GetValue() for s in self.settings()]


class NormalizationUI(wx.Frame):
    '''
    '''
    def __init__(self, parent=None, id=-1, title='Normalization Settings', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        
        self.n_steps = 1
        
        #
        # Define the controls
        #
        col_choices = wx.CheckListBox(self, -1, choices=map(str, range(100)), size=(-1, 100))
        add_norm_step_btn = wx.Button(self, -1, 'Add normalization step')
        norm_meas_checkbox = wx.CheckBox(self, -1, 'Normalized measurement')
        norm_value_checkbox = wx.CheckBox(self, -1, 'Normalization value')
        prefix_text = wx.TextCtrl(self, -1, '')
        
        ok = wx.Button(self, wx.ID_OK, 'Perform Normalization')
                
        self.norm_steps = [ ]
        self.boxes = [ ]
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.Sizer.Add(wx.StaticText(self, -1, 'Select measurements to normalize:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer((-1,5))
        self.Sizer.Add(col_choices, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        
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
        sz.Add(ok, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.ALL, 15)
        
        add_norm_step_btn.Bind(wx.EVT_BUTTON, self.on_add_norm_step)

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

    def get_normalization_parameters(self):
        '''returns a list of dictionaries whose parameters can be used as input
        to the normalize(**kwargs)
        
        eg:
        ui = NormalizationUI()
        for params in ui.get_normalization_parameters():
            values = normalize(**params)
        '''
        pass

        

if __name__ == "__main__":
    app = wx.PySimpleApp()

    f = NormalizationUI(size=(700,500))
    f.Show()
    f.Center()
    
    app.MainLoop()
