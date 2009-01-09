'''
ImagePanel.py
Authors: afraser
'''

import wx
import ImageTools
from Properties import Properties
from DropTarget import DropTarget

p = Properties.getInstance()



class ImagePanel(wx.Panel, DropTarget):
    def __init__(self, imgs, chMap, parent, scale=1.0, brightness=1.0):
        self.chMap       = chMap
        self.toggleChMap = chMap[:]
        self.images      = imgs                                         # image channel arrays
        self.bitmap      = ImageTools.MergeToBitmap(imgs,
                                                    chMap = chMap,
                                                    scale = scale,
                                                    brightness = brightness)   # displayed wx.Bitmap
        
        wx.Panel.__init__(self, parent, wx.NewId(), size=self.bitmap.Size)
        
        self.scale          = scale
        self.brightness     = brightness
        self.selected       = False
        self.selectedPoints = []
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)        
        
        
    def OnPaint(self, evt):
        self.SetClientSize((self.bitmap.Width, self.bitmap.Height))
        self.dc = wx.PaintDC(self)
        self.dc.Clear()
        self.dc.DrawBitmap(self.bitmap, 0, 0)
        
        for (x,y) in self.selectedPoints:
            x = x * self.scale - 2
            y = y * self.scale - 2
            w = h = 4
            
            self.dc.BeginDrawing()
            self.dc.SetPen(wx.Pen("WHITE",1))
            self.dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
            self.dc.DrawRectangle(x,y,w,h)
            self.dc.EndDrawing()
        
        if self.selected:
            self.dc.BeginDrawing()
            self.dc.SetPen(wx.Pen("WHITE",1))
            self.dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
            self.dc.DrawRectangle(1,1,self.bitmap.Width-1,self.bitmap.Height-1)
            self.dc.EndDrawing()


    def UpdateBitmap(self):
        self.bitmap = ImageTools.MergeToBitmap(self.images,
                                               chMap = self.chMap,
                                               brightness = self.brightness,
                                               scale = self.scale)
        self.Refresh()
            
    
    def MapChannels(self, chMap):
        ''' Recalculates the displayed bitmap for a new channel-color map. '''
        self.chMap = chMap
        self.UpdateBitmap()
        

    def SetScale(self, scale):
        if scale != self.scale:
            self.scale = scale
            self.UpdateBitmap()
        
        
    def SetBrightness(self, brightness):
        if brightness != self.brightness:
            self.brightness = brightness
            self.UpdateBitmap()
        

    def ReceiveDrop(self, data):
        # Pass drop data on to parent if it is a DropTarget
        if issubclass(self.GetParent().__class__, DropTarget):
            self.GetParent().ReceiveDrop(data)

    
    def SelectPoints(self, coordList):
        self.selectedPoints = coordList
        self.Refresh()
            

