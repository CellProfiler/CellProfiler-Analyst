import wx
import pylab
import numpy as np


class ColorBarPanel(wx.Panel):
    '''
    A HORIZONTAL color bar and value axis drawn on a panel.
    '''
    def __init__(self, parent, map, extents=(0.,1.), ticks=5, labelformat='%.3f',
                 **kwargs):
        '''
        map -- a colormap name from pylab.cm
        extents -- min and max values to display on the bar
        ticks -- # of ticks to display values for on the bar
                 1 or 0 will draw no ticks
        labelformat -- a valid format string for the values displayed
                       on the value axis 
        '''
        wx.Panel.__init__(self, parent, **kwargs)
        self.ticks = ticks
        self.labelformat = labelformat
        self.SetMap(map)
        self.SetExtents(extents)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def SetMap(self, map):
        ''' Sets the colormap that is displayed.
        map should be the string name of a colormap from pylab.cm'''
        self.cm = pylab.cm.get_cmap(map)
        self.Refresh()
        
    def SetExtents(self, extents):
        ''' Sets the value axis min and max. Accepts a 2-tuple.'''
        self.extents = extents
        self.Refresh()
        
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
            
    def OnPaint(self, evt):
        w,h = self.Size
        if 0 in self.Size:
            return
        
        # values to be used for color map
        a = np.arange(w, dtype=float) / w
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        for x in xrange(w):
            color = np.array(self.cm(a[x])) * 255
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
