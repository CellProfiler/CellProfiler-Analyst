import wx
from Properties import Properties
import numpy as np
from matplotlib.pyplot import cm

p = Properties.getInstance()

contrast_modes = ['None', 'Auto', 'Log']

class ImageControlPanel(wx.Panel):
    def __init__(self, parent, listeners, brightness=1.0, scale=1.0, 
                 contrast=None, classCoords=None):
        '''
        This panel provides widgets
        listeners : list of objects to broadcast to.
        listeners must implement SetScale, SetBrightness, and SetContrastMode
        '''
        wx.Panel.__init__(self, parent, wx.NewId())
        if type(listeners) == list:
            self.listeners = listeners
        else:
            self.listeners = [listeners]
        
        self.scale_slider      = wx.Slider(parent, -1, scale*100, 1, 300, (10, 10), (100, 40), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.brightness_slider = wx.Slider(parent, -1, brightness*100, 1, 300, (10, 10), (100, 40), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.reset_btn         = wx.Button(parent, wx.NewId(), 'Reset')
        
        self.scale_percent      = wx.StaticText(parent, wx.NewId(), str(self.scale_slider.GetValue())+'%')
        self.brightness_percent = wx.StaticText(parent, wx.NewId(), str(self.brightness_slider.GetValue())+'%')
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        brightness_sizer = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.Add(wx.StaticText(parent, wx.NewId(), 'Brightness:'))
        brightness_sizer.Add(wx.StaticBitmap(self.GetParent(), -1, wx.BitmapFromImage(wx.Image('/Users/afraser/Desktop/brightness.png'))), proportion=0)
        brightness_sizer.AddSpacer((5,-1))
        brightness_sizer.Add(self.brightness_slider, proportion=1, flag=wx.ALL|wx.EXPAND)
        brightness_sizer.AddSpacer((5,-1))
        brightness_sizer.Add(self.brightness_percent)
        scale_sizer = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.Add(wx.StaticText(parent, wx.NewId(), 'Scale:'))
        scale_sizer.Add(wx.StaticBitmap(self.GetParent(), -1, wx.BitmapFromImage(wx.Image('/Users/afraser/Desktop/zoom.png'))), proportion=0)
        scale_sizer.AddSpacer((5,-1))
        scale_sizer.Add(self.scale_slider, proportion=1, flag=wx.ALL|wx.EXPAND)
        scale_sizer.AddSpacer((5,-1))
        scale_sizer.Add(self.scale_percent)
        sizer2.Add(brightness_sizer)
        sizer2.Add(scale_sizer)
        sizer2.Add(self.reset_btn)
        
        self.sizer3 = wx.BoxSizer(wx.VERTICAL)
        self.AddContrastControls(contrast)
        if classCoords is not None:
            self.SetClasses(classCoords)

        sizer.Add(sizer2, flag=wx.EXPAND)
        sizer.AddSpacer((10,-1))
        sizer.Add(self.sizer3, flag=wx.EXPAND)
        parent.SetSizer(sizer)
        
        self.scale_slider.Bind(wx.EVT_SLIDER, self.OnScaleSlider)
        self.brightness_slider.Bind(wx.EVT_SLIDER, self.OnBrightnessSlider)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.OnReset)


    def AddContrastControls(self, mode):
        radiobox = wx.RadioBox(self.GetParent(), -1, 'Contrast Adjust:', choices=contrast_modes)
        try:
            radiobox.SetSelection(contrast_modes.index(mode))
        except:
            radiobox.SetSelection(0)
        self.sizer3.Add(radiobox, flag=wx.EXPAND)
        self.sizer3.AddSpacer((-1,10))
        radiobox.Bind(wx.EVT_RADIOBOX, self.OnSetContrastMode)
        


    def SetClassPoints(self, classCoords):
        vals = np.arange(float(len(classCoords))) / len(classCoords)
        if len(vals) > 0:
            vals += (1.0 - vals[-1]) / 2
            colors = [np.array(cm.jet(val))*255 for val in vals]
            
        self.sizer3.Add(wx.StaticText(self.GetParent(), -1, 'Phenotypes:'))
        for (name, keys), color in zip(classCoords.items(), colors):
            checkBox = wx.CheckBox(self.GetParent(), wx.NewId(), name)
            checkBox.SetForegroundColour(color)   # Doesn't work on Mac. Works on Windows.
            checkBox.SetValue(True)
            self.sizer3.Add(checkBox, flag=wx.EXPAND)
            checkBox.Bind(wx.EVT_CHECKBOX, self.OnTogglePhenotype)


    def OnBrightnessSlider(self, evt):
        pos = self.brightness_slider.GetValue()/100.0
        for listener in self.listeners:
            listener.SetBrightness(pos)
        self.brightness_percent.SetLabel(str(self.brightness_slider.GetValue())+'%')


    def OnScaleSlider(self, evt):
        pos = self.scale_slider.GetValue()/100.0      
        for listener in self.listeners:
            listener.SetScale(pos)
        self.scale_percent.SetLabel(str(self.scale_slider.GetValue())+'%')

        
    def OnReset(self, evt):
        for listener in self.listeners:
            listener.SetScale(1.0)
            listener.SetBrightness(1.0)
        self.scale_slider.SetValue(100)
        self.brightness_slider.SetValue(100)
        self.brightness_percent.SetLabel('100%')
        self.scale_percent.SetLabel('100%')
        self.Layout()

            
    def ConnectTolistener(self, listener):
        self.listeners += [listener]
        
                
    def OnTogglePhenotype(self, evt):
        className = evt.EventObject.Label
        for listener in self.listeners:
            listener.ToggleClass(className, evt.Checked())
            
    
    def OnSetContrastMode(self, evt):
        for listener in self.listeners:
            listener.SetContrastMode(contrast_modes[evt.GetEventObject().GetSelection()])
        
