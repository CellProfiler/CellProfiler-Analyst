import wx
from properties import Properties
import numpy as np
from matplotlib.pyplot import cm
from StringIO import StringIO
from base64 import b64decode
p = Properties.getInstance()

contrast_modes = ['None', 'Linear', 'Log']

brightness_icon = 'iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAMAAABhEH5lAAAAGXRFWHRTb2Z\
0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAMBQTFRFOTk5LS0t////YWFhNjY2ZGRk9fX1VFRUf\
39/l5eX9vb2pqamNTU1oaGhNzc3WlpaNDQ0MzMzMDAwo6OjqampUFBQd3d3qqqq7OzssrKyenp6MTE\
x2NjY6enpXl5eXV1d7+/vPz8/7e3t29vbdnZ2MjIyQEBAsLCw1dXV8/Pz6+vrfHx8wsLCdHR0pKSkT\
k5OW1tbwMDAcHBwc3NzioqKjIyM8vLyqKiovr6+v7+/eXl5n5+fnp6emZmZmpqa////TDLFQQAAAAd\
0Uk5T////////ABpLA0YAAACySURBVHjabNCHCsMgEABQc0YTyd5kkFI6oXvv/v9nVU1NAq1w3vHwT\
hTR7zJNVaG/dMhFsSjEHmNJ+T5XB+LaahpnPDJCLjxZ7awRQS4sWdUbz0UHoKyjzNV1GwB2kaTinlL\
MxecEBiUYo3S8otj2g4mghGJcy0bLD8qQy+3RjffKUAM4n3o3VoamwfU4b2nNw0k2T57eDUWGox70m\
jJJjeCB2Nmw9zmD7c9/eZ6qPgIMAAElDf2nrDqEAAAAAElFTkSuQmCC'

zoom_icon = 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAAK/INwWK6\
QAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAFGSURBVHjalFKxjoJQEFyO6yD\
RoJ0FH0CJVNYSYsEfYGkiCT2/QE1pZ8M/gJRYA60WUNBgIQWUuufD3IWI+s5JSMjbndmdzDKICO+wW\
q2wrmtgWRaGwyG4rst068wrgeVyiaIownw+h9ls1r5FUQS73Q6yLIPtdnsXIgKP32KxwP1+j69Aarq\
uk9/+BoZhoCRJYNv2W2uO40BVVfD1WCiKAlRVBRpIT5qmfQuyLOPlckEaSM90OsXeBrRUuriJ9C0MB\
gNIkoRKjuMYBEHoC0wmE/B9nyoQBAEoivI8Rk3TqDGSnqcxWpaF4/EYeJ5vY+oe0o3YTj4cDuB5HtO\
7xPV6jafTCY7HI4xGIwjDkPk9ZQKO42Cz2Tw/ZdM0sSzLNtvr9UpEmP8k8d2d/CmZgM3zHM/n8190n\
5DbDZqmaScTK5+SCX4EGADRZjaIh/KWhwAAAABJRU5ErkJggg=='


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
        
        self.contrast = contrast
        
        self.scale_slider      = wx.Slider(parent, -1, scale*100, 1, 300, (10, 10), (100, 40), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.brightness_slider = wx.Slider(parent, -1, brightness*100, 1, 300, (10, 10), (100, 40), wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.reset_btn         = wx.Button(parent, wx.NewId(), 'Reset')
        
        self.scale_percent      = wx.StaticText(parent, wx.NewId(), str(self.scale_slider.GetValue())+'%')
        self.brightness_percent = wx.StaticText(parent, wx.NewId(), str(self.brightness_slider.GetValue())+'%')
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        brightness_sizer = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.Add(wx.StaticText(parent, wx.NewId(), 'Brightness:'))
        brightness_sizer.Add(wx.StaticBitmap(self.Parent, -1, wx.BitmapFromImage(wx.ImageFromStream(StringIO(b64decode(brightness_icon))))), proportion=0)
        brightness_sizer.AddSpacer((5,-1))
        brightness_sizer.Add(self.brightness_slider, proportion=1, flag=wx.ALL|wx.EXPAND)
        brightness_sizer.AddSpacer((5,-1))
        brightness_sizer.Add(self.brightness_percent)
        scale_sizer = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.Add(wx.StaticText(parent, wx.NewId(), 'Scale:'))
        scale_sizer.Add(wx.StaticBitmap(self.Parent, -1, wx.BitmapFromImage(wx.ImageFromStream(StringIO(b64decode(zoom_icon))))), proportion=0)
        scale_sizer.AddSpacer((5,-1))
        scale_sizer.Add(self.scale_slider, proportion=1, flag=wx.ALL|wx.EXPAND)
        scale_sizer.AddSpacer((5,-1))
        scale_sizer.Add(self.scale_percent)
        sizer2.Add(brightness_sizer)
        sizer2.Add(scale_sizer)
        sizer2.Add(self.reset_btn)
        
        self.sizer3 = wx.BoxSizer(wx.VERTICAL)
        self.AddContrastControls(contrast)
        self.sizer4 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3.Add(self.sizer4) # place holder for class check boxes
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
        self.contrast = mode
        self.contrast_radiobox = wx.RadioBox(self.Parent, -1, 'Contrast Stretch:', choices=contrast_modes)
        try:
            self.contrast_radiobox.SetSelection(contrast_modes.index(mode))
        except:
            self.contrast_radiobox.SetSelection(1)
        self.sizer3.Add(self.contrast_radiobox, flag=wx.EXPAND)
        self.sizer3.AddSpacer((-1,10))
        self.contrast_radiobox.Bind(wx.EVT_RADIOBOX, self.OnSetContrastMode)
        self.UpdateContrastMode()

    def SetClassPoints(self, classCoords):
        self.sizer4.DeleteWindows()
        vals = np.arange(float(len(classCoords))) / len(classCoords)
        if len(vals) > 0:
            vals += (1.0 - vals[-1]) / 2
            colors = [np.array(cm.jet(val)) * 255 for val in vals]
            
            self.sizer4.Add(wx.StaticText(self.Parent, -1, 'Classes:'))
            i=1
            for (name, keys), color in zip(classCoords.items(), colors):
                checkBox = wx.CheckBox(self.Parent, wx.NewId(), '%d) %s'%(i,name))
                checkBox.SetForegroundColour(color)   # Doesn't work on Mac. Works on Windows.
                checkBox.SetValue(True)
                self.sizer4.Add(checkBox, flag=wx.EXPAND)
                
                def OnTogglePhenotype(evt):
                    className = evt.EventObject.Label
                    for listener in self.listeners:
                        listener.ToggleClass(className[3:], evt.Checked())
                
                checkBox.Bind(wx.EVT_CHECKBOX, OnTogglePhenotype)
                i+=1


    def OnBrightnessSlider(self, evt):
        self.UpdateBrightness()
    
    def UpdateBrightness(self):
        pos = self.brightness_slider.GetValue() / 100.0
        for listener in self.listeners:
            listener.SetBrightness(pos)
        self.brightness_percent.SetLabel(str(self.brightness_slider.GetValue())+'%')

    def OnScaleSlider(self, evt):
        self.UpdateScale()
    
    def UpdateScale(self):
        pos = self.scale_slider.GetValue() / 100.0      
        for listener in self.listeners:
            listener.SetScale(pos)
        self.scale_percent.SetLabel(str(self.scale_slider.GetValue())+'%')

    def OnSetContrastMode(self, evt):
        self.UpdateContrastMode()
        
    def UpdateContrastMode(self):
        for listener in self.listeners:
            listener.SetContrastMode(contrast_modes[self.contrast_radiobox.GetSelection()])

    def SetContrastMode(self, mode):
        if mode.lower() == 'none':
            self.contrast_radiobox.SetSelection(0)
        elif mode.lower() == 'linear':
            self.contrast_radiobox.SetSelection(1)
        elif mode.lower() == 'log':
            self.contrast_radiobox.SetSelection(2)
        
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
    
    def SetListener(self, listener):
        self.listeners = [listener]
        self.UpdateAll()
        
    def UpdateAll(self):
        self.UpdateBrightness()
        self.UpdateScale()
        self.UpdateContrastMode()
