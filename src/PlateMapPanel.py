import wx
import numpy as np
import matplotlib.pyplot as plt

abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
alphabet = [c for c in abc] + [c+c for c in abc]

class PlateMapPanel(wx.Panel):
    '''
    A Panel that displays a plate layout with wells that are colored by their
    data (in the range [0,1]).  The panel provides mechanisms for selection,
    color mapping, setting row & column labels, and reshaping the layout.
    '''
    
    def __init__(self, parent, data, shape=None, colormap=plt.cm.jet):
        wx.Panel.__init__(self, parent)
        self.colormap = colormap
        self.SetData(data, shape)
        self.selection = set([])
        self.x_labels = ['%02d'%i for i in range(1,self.data.shape[0]+1)]
        self.y_labels = ['%2s'%c for c in alphabet[:self.data.shape[1]]]
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
       
    
    def SetData(self, data, shape=None):
        '''
        data: An iterable with values between 0 and 1. It's shape will be used
              to layout the plate unless overridden by the shape parameter
        shape: If passed, this will be used to reshape the data.
        '''
        self.data = np.array(data).astype('float')
        if shape != None:
            self.data = self.data.reshape(shape)
        assert (data<=1).all() and (data>=0).all()
        self.Refresh()
        
    
    def SetXLabels(self, labels):
        assert len(labels) >= self.data.shape[0]
        self.x_labels = ['%2s'%c for c in labels]
        self.Refresh()
        
    
    def SetYLabels(self, labels):
        assert len(labels) >= self.data.shape[1]
        self.y_labels = ['%2s'%c for c in labels]
        self.Refresh()
        
        
    def SetColorMap(self, colormap):
        ''' colormap: a matplotlib.colors.LinearSegmentedColormap instance '''
        self.colormap = colormap
        
    
    def SelectWell(self, well):
        ''' well: 2-tuple of integers indexing a well position '''
        self.selection = set([well])
        self.Refresh()
        
        
    def ToggleSelected(self, well):
        ''' well: 2-tuple of integers indexing a well position '''
        if well in self.selection:
            self.selection.remove(well)
        else:
            self.selection.add(well)
        self.Refresh()
        

    def GetWellAtCoord(self, x, y):
        ''' returns a 2 tuple of integers indexing a well position 
                    or -1 if there is no well at the given position. '''
        r = min(self.Size[0]/(self.data.shape[0]+1.)/2.,
                self.Size[1]/(self.data.shape[1]+1.)/2.) - 1.
        i = int((x-2)/(r*2+2))
        j = int((y-2)/(r*2+2))
        if 0<i<=self.data.shape[0] and 0<j<=self.data.shape[1]:
            return (i-1,j-1)
        else:
            return -1


    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        r = min(self.Size[0]/(self.data.shape[0]+1.)/2.,
                self.Size[1]/(self.data.shape[1]+1.)/2.) - 1.
        dc.SetPen(wx.Pen("BLACK",min(r/10., 1.)))
        py = 0
        i=0
        for y in range(self.data.shape[1]+1):
            px = 0
            for x in range(self.data.shape[0]+1):
                # Draw column headers
                if y==0 and x!=0:
                    dc.DrawText(self.x_labels[x-1], px+r/2, py+r/2)
                # Draw row headers
                elif y!=0 and x==0:
                    dc.DrawText(self.y_labels[y-1], px+r/2, py+r/2)
                # Draw wells
                elif y>0 and x>0:
                    if (x-1,y-1) in self.selection:
                        dc.SetPen(wx.Pen("BLACK",5))
                    else:
                        dc.SetPen(wx.Pen("BLACK",min(r/10., 1.)))
                    color = np.array(self.colormap(self.data[x-1][y-1])[:3]) * 255
                    dc.SetBrush(wx.Brush(color))
                    dc.DrawRoundedRectangle(px+1, py+1, r*2, r*2, r*0.75)
#                    dc.DrawCircle(px+r+1, py+r+1, r)
#                    dc.DrawRectangle(px+1, py+1, r*2, r*2)
                    i+=1
                px += 2*r+2
            py += 2*r+2
        dc.EndDrawing()
        return dc
    
    
    # Should be externalized
    def OnClick(self, evt):
        if evt.ShiftDown():
            self.ToggleSelected(self.GetWellAtCoord(evt.X, evt.Y))
        else:
            self.SelectWell(self.GetWellAtCoord(evt.X, evt.Y))        
   
   
   

if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    data = np.arange(384)/384.
    frame = wx.Frame(None, size=(600.,430.))
    p = PlateMapPanel(frame, data, shape=(24,16))
    frame.Show()
    
#    f = wx.Frame(None)
#    data = np.arange(96)/96.
#    p2 = PlateMapPanel(f, data, (12,8)) #96 wells
#    f.Show()
    
    app.MainLoop()
    
    
    