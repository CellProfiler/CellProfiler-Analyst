from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import pylab
import wx
import numpy as np


class ColorBarPanel(wx.Panel):
        def __init__( self, parent, map, **kwargs ):
            wx.Panel.__init__(self, parent, **kwargs)
                        
            self.parent = parent
            self.map = pylab.cm.get_cmap(map)
            self.im = None
            self.figure = Figure( None, None )
            self.canvas = FigureCanvasWxAgg( self, -1, self.figure )
            self.draw()
            
            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.Bind(wx.EVT_SIZE, self.OnSize)
            
        def SetMap(self, map):
            self.map = pylab.cm.get_cmap(map)
            if self.im is not None:
                self.im.set_cmap(self.map)
                self.Refresh()

        def draw(self):
            if not hasattr(self, 'subplot'):
                self.subplot = self.figure.add_subplot(111)

            if self.im is None:
                a = np.atleast_2d(np.arange(200.)).T
                self.im = self.subplot.imshow(a, cmap=self.map, aspect='auto')
                self.subplot.axis('tight')
                self.subplot.axis('off')
#                self.subplot.xaxis.set_visible(False)
                self.figure.subplots_adjust(0.,0.,1.,1.)
        
        def OnPaint(self, evt):
            self.canvas.draw()
            
        def OnSize(self, evt):
            self.canvas.SetSize(self.Size)
            self.figure.set_size_inches(float(self.Size[0]) / self.figure.get_dpi(),
                                        float(self.Size[1]) / self.figure.get_dpi())
            evt.Skip()
        
    
            
if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    frame = wx.Frame( None, wx.ID_ANY, 'WxPython and Matplotlib')#, size=(300,300) )
    panel = ColorBarPanel(frame, 'hot', size=(300,14))
    frame.Show()
    
    app.MainLoop()