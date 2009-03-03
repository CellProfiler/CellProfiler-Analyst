import wx
from Properties import Properties

p = Properties.getInstance()


class ImageControlPanel(wx.Panel):
    def __init__(self, parent, listeners, brightness=1.0, scale=1.0):
        '''
        This panel provides widgets
        listeners : list of objects to broadcast to.
        listeners must implement SetScale, and SetBrightness
        '''
        wx.Panel.__init__(self, parent, wx.NewId())
        if type(listeners) == list:
            self.listeners = listeners
        else:
            self.listeners = [listeners]
        

        self.scale_slider      = wx.Slider(self, -1, scale*100, 1, 200, (10, 10), (100, 40), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.brightness_slider = wx.Slider(self, -1, brightness*100, 1, 200, (10, 10), (100, 40), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.reset_btn         = wx.Button(self, wx.NewId(), 'Reset')
        
        
        self.scale_percent      = wx.StaticText(self, wx.NewId(), '%'+str(self.scale_slider.GetValue()))
        self.brightness_percent = wx.StaticText(self, wx.NewId(), '%'+str(self.brightness_slider.GetValue()))
        
        self.sizer = wx.GridSizer(3,3)
        self.sizer.Add(wx.StaticText(self, wx.NewId(), 'Brightness:'))
        self.sizer.Add(self.brightness_slider, wx.ALL|wx.EXPAND)
        self.sizer.Add(self.brightness_percent)
        self.sizer.Add(wx.StaticText(self, wx.NewId(), 'Scale:'))
        self.sizer.Add(self.scale_slider, wx.ALL|wx.EXPAND)
        self.sizer.Add(self.scale_percent)
        self.sizer.Add(self.reset_btn)
        self.SetSizer(self.sizer)
        
        self.scale_slider.Bind(wx.EVT_SLIDER, self.OnScaleSlider)
        self.brightness_slider.Bind(wx.EVT_SLIDER, self.OnBrightnessSlider)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.OnReset)


    def OnBrightnessSlider(self, evt):
        pos = self.brightness_slider.GetValue()/100.0
        for listener in self.listeners:
            listener.SetBrightness(pos)
        self.brightness_percent.SetLabel('%'+str(self.brightness_slider.GetValue()))


    def OnScaleSlider(self, evt):
        pos = self.scale_slider.GetValue()/100.0      
        for listener in self.listeners:
            listener.SetScale(pos)
        self.scale_percent.SetLabel('%'+str(self.scale_slider.GetValue()))

        
    def OnReset(self, evt):
        for listener in self.listeners:
            listener.SetScale(1.0)
            listener.SetBrightness(1.0)
        self.scale_slider.SetValue(100)
        self.brightness_slider.SetValue(100)
        self.brightness_percent.SetLabel('%100')
        self.scale_percent.SetLabel('%100')
        self.Layout()

        
    def ConnectTolistener(self, listener):
        self.listeners += [listener]
        
        

class ImageViewerControlPanel(wx.Panel):
    def __init__(self, parent, listeners, classCoords, colorMap):
        '''
        This panel provides widgets
        listeners : list of objects to broadcast to.
        listeners must implement SetScale, and SetBrightness
        '''
        wx.Panel.__init__(self, parent, wx.NewId())
        if type(listeners) == list:
            self.listeners = listeners
        else:
            self.listeners = [listeners]

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        for (name, keys), color in zip(classCoords.items(), colorMap):
            checkBox = wx.CheckBox(self, wx.NewId(), name)
            checkBox.SetForegroundColour(color)   # Doesn't work on Mac. Works on Windows.
            checkBox.SetValue(True)
            self.sizer.Add(checkBox, flag=wx.EXPAND)
            checkBox.Bind(wx.EVT_CHECKBOX, self.OnCheck)
        self.SetSizer(self.sizer)
        
    def OnCheck(self, evt):
        className = evt.EventObject.Label
        checked = evt.Checked()
        for listener in self.listeners:
            listener.ToggleClass(className, checked)
        
