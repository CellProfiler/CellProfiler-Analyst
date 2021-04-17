import wx
from .properties import Properties
import numpy as np
from matplotlib.pyplot import cm
from cpa.icons import get_icon

p = Properties()

contrast_modes = ['None', 'Linear', 'Log']

class ImageControlPanel(wx.Panel):
    def __init__(self, parent, listeners, brightness=1.0, scale=1.0, 
                 contrast=None, classCoords=None):
        '''
        This panel provides widgets
        listeners : list of objects to broadcast to.
        listeners must implement SetScale, SetBrightness, and SetContrastMode
        '''
        wx.Panel.__init__(self, parent, wx.NewId())

        self.SetBackgroundColour('white') # color for the background of panel

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
        brightness_sizer.Add(wx.StaticBitmap(self.Parent, -1, get_icon('brightness').ConvertToBitmap()), proportion=0)
        brightness_sizer.AddSpacer(5)
        brightness_sizer.Add(self.brightness_slider, proportion=1, flag=wx.ALL|wx.EXPAND)
        brightness_sizer.AddSpacer(5)
        brightness_sizer.Add(self.brightness_percent)

        scale_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scale_sizer.Add(wx.StaticBitmap(self.Parent, -1, get_icon('zoom').ConvertToBitmap()), proportion=0)
        scale_sizer.AddSpacer(5)
        scale_sizer.Add(self.scale_slider, proportion=1, flag=wx.ALL|wx.EXPAND)
        scale_sizer.AddSpacer(5)
        scale_sizer.Add(self.scale_percent)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.reset_btn)
        # Avoids circular import at the start of the module.
        from cpa.imageviewer import ImageViewerPanel
        if isinstance(self.listeners[0], ImageViewerPanel):
            self.fit_to_window_btn = wx.Button(parent, wx.NewId(), 'Fit to Window')
            button_sizer.AddSpacer(5)
            button_sizer.Add(self.fit_to_window_btn)
            self.fit_to_window_btn.Bind(wx.EVT_BUTTON, self.OnFitToWindow)

        sizer2.Add(brightness_sizer)
        sizer2.Add(scale_sizer)
        text = wx.StaticText(parent, wx.NewId(), 'Find selected objects: Ctrl+F/Cmd+F')
        sizer2.Add(text)
        sizer2.Add(button_sizer)
        sizer2.Add(0, 10, 0) # Space on the bottom
        self.sizer3 = wx.BoxSizer(wx.VERTICAL)
        self.AddContrastControls(contrast)
        self.sizer_checkboxes = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3.Add(self.sizer_checkboxes) # place holder for class check boxes
        self.sizer3.Add(0, 10, 0) # Space on the bottom

        if classCoords is not None:
            self.SetClassPoints(classCoords)

        sizer.Add(sizer2, flag=wx.EXPAND)
        sizer.AddSpacer(10)
        sizer.Add(self.sizer3, flag=wx.EXPAND)
        parent.SetSizer(sizer)
        
        self.scale_slider.Bind(wx.EVT_SLIDER, self.OnScaleSlider)
        self.brightness_slider.Bind(wx.EVT_SLIDER, self.OnBrightnessSlider)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.OnReset)
        # When a slider is moved wx produces update events extremely quickly.
        # This will freeze up CPA if there are more than a few tiles displayed.
        # To solve this, we put the tile updates on a timer. If the slider
        # changes again before the timeout then the timer resets. This means
        # tiles will only get redrawn when the slider stops moving.
        self.throttle_scale = wx.CallLater(100, self.UpdateScale)
        self.throttle_scale.Stop()
        self.throttle_brightness = wx.CallLater(100, self.UpdateBrightness)
        self.throttle_brightness.Stop()

    def AddContrastControls(self, mode):
        self.contrast = mode
        self.contrast_radiobox = wx.RadioBox(self.Parent, -1, 'Contrast Stretch:', choices=contrast_modes)
        try:
            self.contrast_radiobox.SetSelection(contrast_modes.index(mode))
        except:
            self.contrast_radiobox.SetSelection(1)
        self.sizer3.Add(self.contrast_radiobox, flag=wx.EXPAND)
        self.sizer3.Add(-1, 10, 0)
        self.contrast_radiobox.Bind(wx.EVT_RADIOBOX, self.OnSetContrastMode)
        # Disabling this for now, contrast from init should never have changed so no need to update? Mar 2021
        # self.UpdateContrastMode()

    def SetClassPoints(self, classCoords):
        self.sizer_checkboxes.Clear()
        sizer_classes = wx.BoxSizer(wx.VERTICAL)
        sizer_training = wx.BoxSizer(wx.VERTICAL)
        self.sizer_checkboxes.Add(sizer_classes)
        self.sizer_checkboxes.AddSpacer(5)
        self.sizer_checkboxes.Add(sizer_training)
        vals = np.arange(float(len(classCoords))) / len(classCoords)
        label_lookup = {}
        if len(vals) > 0:
            vals += (1.0 - vals[-1]) / 2
            colors = [np.array(cm.rainbow(val)) * 255 for val in vals]
            colors_dict = {}
            i=0
            for name in classCoords:
                colors_dict[name] = colors[i]
                i+=1
            sizer_classes.Add(wx.StaticText(self.Parent, -1, 'Classes:'))
            i=1
            sizer_add_to = sizer_classes
            for name in classCoords:
                if i == len(classCoords)/2 + 1:
                    sizer_training.Add(wx.StaticText(self.Parent, -1, 'Training:'))
                    sizer_add_to = sizer_training
                label = f"{i} - {name} ({len(classCoords[name])})"
                checkBox = wx.CheckBox(self.Parent, wx.NewId(), label)
                label_lookup[label] = name
      
                #checkBox.SetForegroundColour(color)   # Doesn't work on Mac. Works on Windows.
                checkBox.SetBackgroundColour(colors_dict[name])
                checkBox.SetValue(True)
                sizer_add_to.Add(checkBox, flag=wx.EXPAND)

                def OnTogglePhenotype(evt):
                    className = evt.EventObject.Label
                    for listener in self.listeners:
                        listener.ToggleClass(label_lookup[className], evt.IsChecked())

                checkBox.Bind(wx.EVT_CHECKBOX, OnTogglePhenotype)
                i+=1



    def OnBrightnessSlider(self, evt):
        self.brightness_percent.SetLabel(str(self.brightness_slider.GetValue())+'%')
        if self.throttle_brightness.IsRunning():
            self.throttle_brightness.Restart(100)
        else:
            self.throttle_brightness.Start(100)

    def UpdateBrightness(self):
        pos = self.brightness_slider.GetValue() / 100.0
        for listener in self.listeners:
            listener.SetBrightness(pos)

    def OnScaleSlider(self, evt):
        self.scale_percent.SetLabel(str(self.scale_slider.GetValue())+'%')
        if self.throttle_scale.IsRunning():
            self.throttle_scale.Restart(100)
        else:
            self.throttle_scale.Start(100)

    def UpdateScale(self):
        pos = self.scale_slider.GetValue() / 100.0
        for listener in self.listeners:
            listener.SetScale(pos)

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

    def OnFitToWindow(self, evt):
        scale = 1
        from cpa.imageviewer import ImageViewerPanel
        for listener in self.listeners:
            if isinstance(listener, ImageViewerPanel):
                client_h, client_w = listener.GetParent().GetSize()
                img_w, img_h = listener.images[0].shape
                scale = min(client_w / img_w, client_h / img_h)
                listener.SetScale(scale)
                break
        self.scale_slider.SetValue(scale * 100)
        self.scale_percent.SetLabel(str(self.scale_slider.GetValue())+'%')
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
