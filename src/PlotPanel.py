#!/usr/bin/env python

import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import numpy as np
import wx
from matplotlib.figure import Figure
from DBConnect import DBConnect
from Properties import Properties
#matplotlib.interactive(True)
#matplotlib.use('WXAgg')

db = DBConnect.getInstance()
p = Properties.getInstance()

class PlotPanel (wx.Panel):
    '''
    The PlotPanel has a Figure and a Canvas. OnSize events simply set a 
    flag, and the actual resizing of the figure is triggered by an Idle event.
    '''
    def __init__(self, parent, color=None, dpi=None, **kwargs):
        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.figure = Figure(None, dpi)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.color = color
        self.SetColor(color)
        self.draw()

        self._resizeflag = False

        self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_SIZE, self._onSize)

    def clear_figure(self):
        self.figure.clear()
        self.SetColor(self.color)
        self._resizeflag = True
        
    def SetColor(self, rgbtuple=None):
        '''Set figure and canvas colors to be the same.'''
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get()
        clr = [c / 255. for c in rgbtuple]
        self.figure.set_facecolor(clr)
        self.figure.set_edgecolor(clr)
        self.canvas.SetBackgroundColour(wx.Colour(*rgbtuple))

    def _onSize(self, event):
        self._resizeflag = True

    def _onIdle(self, evt):
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()

    def _SetSize(self):
        pixels = self.GetClientSize()
        if 0 in pixels:
            return
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(float(pixels[0]) / self.figure.get_dpi(),
                                     float(pixels[1]) / self.figure.get_dpi())

    def draw(self):
        # abstract, to be overridden by child classes 
        pass 





# Use CP
#    def launch_scatter(self, evt):
#        figure = cpfig.create_or_find(self, -1, 'scatter', subplots=(1,1), name='scatter')
#        table = np.random.randn(5000,2)
#        figure.panel.subplot_scatter(0, 0, table)



if __name__ == '__main__':
    p.LoadFile('/Users/afraser/Desktop/cpa_example/example.properties')
    app = wx.PySimpleApp()
    f = ScatterFrame(None)
    f.Show()
    app.MainLoop()
