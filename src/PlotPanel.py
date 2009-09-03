from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import matplotlib.cm
import wx
import numpy as np


#
#
# THIS MODULE IS NOT WORKING
#
#

class PlotPanel(wx.Panel):
    def __init__( self, parent, **kwargs ):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.parent = parent
        self.im = None
        self.figure = Figure( None, None )
        self.canvas = FigureCanvasWxAgg( self, -1, self.figure )
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        
    def SetMap(self, map):
        self.map = matplotlib.cm.get_cmap(map)
        if self.im is not None:
            self.im.set_cmap(self.map)
            self.Refresh()

    
    def OnPaint(self, evt):
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        
#        if self.im is None:
#            a = np.arange(200.)
#            a = np.vstack([a for x in range(20)])
#            self.im = self.subplot.imshow(a, cmap=self.map, aspect='equal', extent=(0,self.Size[0],self.Size[1],0))
#            self.subplot.axis('tight')
#            self.subplot.axis('off')
#            self.subplot.yaxis.set_visible(False)
#            self.figure.subplots_adjust(0.,0.,1.,1.)
#            self.canvas.SetSize(self.Size)
#            self.figure.set_size_inches(6.,0.5)
        
        self.canvas.draw()
    
    def OnSize(self, evt):
        self.canvas.SetSize(self.Size)
        self.figure.set_size_inches(float(self.Size[0]) / self.figure.get_dpi(),
                                    float(self.Size[1]) / self.figure.get_dpi())
        evt.Skip()
        
        
        
    
            
if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    frame = wx.Frame( None, wx.ID_ANY, 'WxPython and Matplotlib')#, size=(300,300) )
    panel = PlotPanel(frame, size=(600,14))
    frame.Show()
    
    app.MainLoop()