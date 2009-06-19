import wx
import pylab
import numpy as np

slider_width = 30
s_off = slider_width/2

class ColorBarPanel(wx.Panel):
    '''
    A HORIZONTAL color bar and value axis drawn on a panel.
    '''
    def __init__(self, parent, map, extents=[0.,1.], ticks=5, labelformat='%.3f',
                 **kwargs):
        '''
        map -- a colormap name from pyla~b.cm
        extents -- min and max values to display on the bar
        ticks -- # of ticks to display values for on the bar
                 1 or 0 will draw no ticks
        labelformat -- a valid format string for the values displayed
                       on the value axis 
        '''
        wx.Panel.__init__(self, parent, **kwargs)
        self.ticks = ticks
        self.labelformat = labelformat
        self.low_slider = wx.Button(self, -1, '[', pos=(0,-1), size=(slider_width,-1))
        self.high_slider = wx.Button(self, -1, ']', pos=(self.Size[0],-1), size=(slider_width,-1))
        self.ClearNotifyWindows()
        self.SetMap(map)
        self.interval = list(extents)
        self.extents = extents
        self.clipmode = 'rescale'
        
        self.low_slider.SetToolTipString('')
        self.low_slider.GetToolTip().Enable(True)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.low_slider.Bind(wx.EVT_LEFT_DOWN, self.OnClipSliderLeftDown)
        self.low_slider.Bind(wx.EVT_MOTION, self.OnClipSliderMotion)
        self.high_slider.Bind(wx.EVT_LEFT_DOWN, self.OnClipSliderLeftDown)
        self.high_slider.Bind(wx.EVT_MOTION, self.OnClipSliderMotion)
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
    def OnLeftDown(self, evt):
        # Get the slider closest to the click point.
        if abs(self.low_slider.GetPositionTuple()[0] - evt.X) < abs(self.high_slider.GetPositionTuple()[0] - evt.X):
            self.cur_slider = self.low_slider
        else:
            self.cur_slider = self.high_slider
        self.cur_slider.SetPosition((evt.X - s_off, -1))
        self.xo = 0
        self.UpdateInterval()
    
    def OnClipSliderLeftDown(self, evt):
        self.cur_slider = evt.EventObject
        self.xo = evt.X

    def OnMotion(self, evt):
        if not evt.Dragging() or not evt.LeftIsDown():
            return
        self.cur_slider.SetPosition((evt.X - s_off, -1))
        self.UpdateInterval()

    def OnClipSliderMotion(self, evt):
        slider = evt.EventObject
        if not evt.Dragging() or not evt.LeftIsDown():
            return
        slider.SetPosition((slider.GetPositionTuple()[0] + evt.X - self.xo - s_off, -1))
        self.xo = 0
        self.UpdateInterval()
            
    def ClearNotifyWindows(self):
        self.notify_windows = []
    
    def AddNotifyWindow(self, win):
        self.notify_windows += [win]
        
    def ResetInterval(self):
        ''' Sets clip interval to the extents of the colorbar. '''
        self.interval = list(self.extents)
        self.low_slider.SetPosition((0-s_off,-1))
        self.high_slider.SetPosition((self.Size[0]-s_off,-1))
        for win in self.notify_windows:
            win.SetClipInterval(self.GetInterval(), self.clipmode)
        self.Refresh()
        
    def UpdateInterval(self):
        ''' Calculates the interval values w.r.t. the current extents
        and clipping slider positions. '''
        range = self.extents[1]-self.extents[0]
        if range>0 and self.Size[0]>0:
            self.interval[0] = self.extents[0] + ((self.low_slider.GetPositionTuple()[0] + s_off) / float(self.Size[0]) * range)
            self.interval[1] = self.extents[0] + ((self.high_slider.GetPositionTuple()[0] + s_off) / float(self.Size[0]) * range)
        else:
            self.interval = list(self.extents)
        self.low_slider.SetToolTipString(str(self.interval[0]))
        self.high_slider.SetToolTipString(str(self.interval[1]))
        for win in self.notify_windows:
            win.SetClipInterval(self.GetInterval(), self.clipmode)
        self.Refresh()
        
    def GetInterval(self):
        ''' Returns the interval clipped on the value axis. '''
        return self.interval
        
    def SetMap(self, map):
        ''' Sets the colormap that is displayed.
        map should be the string name of a colormap from pylab.cm'''
        self.cm = pylab.cm.get_cmap(map)
        self.Refresh()
        
    def SetExtents(self, extents):
        ''' Sets the value axis min and max. Accepts a 2-tuple.'''
        self.extents = extents
        self.UpdateInterval()
        
    def SetTicks(self, ticks):
        ''' Sets the number of tick marks displayed by the ColorBarPanel.
        1 or 0 will draw no ticks'''
        self.ticks = ticks
        self.Refresh()
    
    def SetLabelFormat(self, format):
        ''' Sets the value formatting of the value axis
        format should be in the form "%0.3f" '''
        self.labelformat = format
        self.Refresh()
        
    def OnToggleClipMode(self, evt):
        if self.clipmode == 'clip':
            self.clipmode = 'rescale'
        else:
            self.clipmode = 'clip'
        for win in self.notify_windows:
            win.SetClipInterval(self.GetInterval(), self.clipmode)
        self.Refresh()
        
    def OnRightDown(self, evt):
        popupMenu = wx.Menu()
        popupMenu.SetTitle('Colorbar')
        reset = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Reset sliders'))
        self.Bind(wx.EVT_MENU, lambda(evt):self.ResetInterval(), reset)
        if self.clipmode == 'clip':
            bracket_mode = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Value bracketing: RESCALE'))
        else:
            bracket_mode = popupMenu.AppendItem(wx.MenuItem(popupMenu, -1, 'Value bracketing: CLIP'))
        self.Bind(wx.EVT_MENU, self.OnToggleClipMode, bracket_mode)
        self.PopupMenu(popupMenu, (evt.X, evt.Y))
        
    def OnResize(self, evt):
        range = self.extents[1] - self.extents[0]
        self.low_slider.SetPosition((self.Size[0] * (self.interval[0] - self.extents[0]) / range - s_off, -1))
        self.high_slider.SetPosition((self.Size[0] * (self.interval[1] - self.extents[0]) / range - s_off, -1))
            
    def OnPaint(self, evt):
        w,h = self.Size
        if 0 in self.Size:
            return
        low_slider_pos = self.low_slider.GetPositionTuple()[0] + s_off
        high_slider_pos = self.high_slider.GetPositionTuple()[0] + s_off
        
        # create array of values to be used for the color bar
        if self.clipmode=='rescale':
            a1 = np.zeros(low_slider_pos)
            a2 = np.arange(abs(high_slider_pos-low_slider_pos), dtype=float) / (high_slider_pos-low_slider_pos)
            a3 = np.ones(w-high_slider_pos)
            a = np.hstack([a1,a2,a3])
        elif self.clipmode=='clip':
            a = (np.arange(w, dtype=float) / w)
            a[:low_slider_pos] = 0.
            a[high_slider_pos:] = 1.
        
        # draw the color bar
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        for x, v in enumerate(a):
            color = np.array(self.cm(v)) * 255
            dc.SetPen(wx.Pen(color))
            dc.DrawLine(x,0,x,h-14)
        
        # draw value axis
        if self.ticks <= 1:
            return
        font = dc.GetFont()
        font.SetPixelSize((6,12))
        dc.SetFont(font)
        for t in xrange(self.ticks):
            xpos = t * w/(self.ticks-1.)
            val = t * (self.extents[1]-self.extents[0]) / (self.ticks-1)  + self.extents[0]
            dc.DrawLine(xpos,6,xpos,h-14)
            textpos = xpos - xpos/w * dc.GetFullTextExtent(self.labelformat%(val), font)[0]
            dc.DrawText(self.labelformat%(val), textpos, h-13)
            
        dc.EndDrawing()        
