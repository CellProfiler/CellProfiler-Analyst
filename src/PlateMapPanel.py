import wx
import numpy as np
import matplotlib.pyplot as plt

alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

class PlateMapPanel(wx.Panel):
    '''
    '''
    def __init__(self, parent, data, shape=(24,16)):
        wx.Panel.__init__(self, parent)
        self.shape = shape
        self.SetData(data)
        self.selection = set([])
        self.x_labels = ['%02d'%i for i in range(1,self.shape[0]+1)]
        self.y_labels = ['%2s'%c for c in alphabet]
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
       
    def SetData(self, data):
        '''
        data: An iterable with values between 0 and 1. It's length must also
              match the total size of the PlateMapPanel, though the shape does
              not matter.
        '''
        self.data = np.array(data).flatten().astype('float')
        assert (data<=1).all() and (data>=0).all()
        self.Refresh()
        
    def SetXLabels(self, labels):
        assert len(labels) == self.shape[0]
        self.x_labels = labels
        self.Refresh()
        
    def SetYLabels(self, labels):
        assert len(labels) == self.shape[1]
        self.y_labels = labels
        self.Refresh()
        
    def SelectWellAtCoord(self, x, y):
        well = self.GetWellAtCoord(x, y)
        self.selection = set([well])
        self.Refresh()
        
    def ToggleSelected(self, well):
        if well in self.selection:
            self.selection.remove(well)
        else:
            self.selection.add(well)
        self.Refresh()
        
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        r = min(self.Size[0]/(self.shape[0]+1.)/2.,
                self.Size[1]/(self.shape[1]+1.)/2.) - 1.
        dc.SetPen(wx.Pen("BLACK",min(r/10., 1.)))
        py = 0
        i=0
        for y in range(self.shape[1]+1):
            px = 0
            for x in range(self.shape[0]+1):
                # Draw column headers
                if y==0 and x!=0:
                    dc.DrawText(self.x_labels[x-1], px+r/2, py+r/2)
                # Draw row headers
                elif y!=0 and x==0:
                    dc.DrawText(self.y_labels[y-1], px+r/2, py+r/2)
                # Draw wells
                elif y>0 and x>0:
                    if (x,y) in self.selection:
                        dc.SetPen(wx.Pen("BLACK",5))
                    else:
                        dc.SetPen(wx.Pen("BLACK",min(r/10., 1.)))
                    color = np.array(plt.cm.jet(self.data[i])[:3])*255
                    dc.SetBrush(wx.Brush(color))
#                    dc.DrawRectangle(px+1, py+1, r*2, r*2)
                    dc.DrawRoundedRectangle(px+1, py+1, r*2, r*2, r*0.75)
#                    dc.DrawCircle(px+r+1, py+r+1, r)
                    i+=1
                px += 2*r+2
            py += 2*r+2
        dc.EndDrawing()
        return dc
    
    def OnClick(self, evt):
        if evt.ShiftDown():
            self.ToggleSelected(self.GetWellAtCoord(evt.X, evt.Y))
        else:
            self.SelectWellAtCoord(evt.X, evt.Y)
    
    def GetWellAtCoord(self, x, y):
        r = min(self.Size[0]/(self.shape[0]+1.)/2.,
                self.Size[1]/(self.shape[1]+1.)/2.) - 1.
        i = int((x-2)/(r*2+2))
        j = int((y-2)/(r*2+2))
        if 0<i<=self.shape[0] and 0<j<=self.shape[1]:
            return (i,j)
        else:
            return -1
        
   
   
   

if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    data = np.arange(384)/384.
    data = data.reshape(24,16)
    frame = wx.Frame(None, size=(600.,430.))
    p = PlateMapPanel(frame, data)
    frame.Show()
    
    f = wx.Frame(None)
    data = np.arange(96)/96.
    p2 = PlateMapPanel(f, data, (12,8)) #96 wells
    f.Show()
    
    app.MainLoop()
    
    
    