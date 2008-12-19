'''
'''

import wx
import ImageTools
from Properties import Properties
from DropTarget import DropTarget

p = Properties.getInstance()



class ImagePanel(wx.Panel, DropTarget):
    def __init__(self, imgs, chMap, parent):
        self.h, self.w = imgs[0].shape
        wx.Panel.__init__(self, parent, wx.NewId(), size=(self.w,self.h))
        self.chMap       = chMap
        self.toggleChMap = chMap[:]
        self.images      = imgs                                         # image channel arrays
        self.bitmap      = ImageTools.MergeToBitmap(imgs, self.chMap)   # displayed wx.Bitmap
        
        self.brightness  = 1.0
        self.contrast    = 1.0
        self.scale       = 1.0
        self.selected = False
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        
    def OnPaint(self, evt):
        self.dc = wx.PaintDC(self)
        self.dc.Clear()
        self.dc.DrawBitmap(self.bitmap, 0, 0)
        if self.selected:
            self.dc.BeginDrawing()
            self.dc.SetPen(wx.Pen("WHITE",1))
            self.dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
            self.dc.DrawRectangle(1,1,self.bitmap.Width-1,self.bitmap.Height-1)
            self.dc.EndDrawing()
        self.SetClientSize((self.bitmap.Width, self.bitmap.Height))


    def UpdateBitmap(self):
        self.bitmap = ImageTools.MergeToBitmap(self.images,
                                               chMap = self.chMap,
                                               brightness = self.brightness,
                                               contrast = self.contrast,
                                               scale = self.scale)
        self.Refresh()
            
    
    def MapChannels(self, chMap):
        ''' Recalculates the displayed bitmap for a new channel-color map. '''
        self.chMap = chMap
        self.UpdateBitmap()
        

    def SetScale(self, scale):
        self.scale = scale
        self.UpdateBitmap()
        
        
    def SetBrightness(self, brightness):
        self.brightness = brightness
        self.UpdateBitmap()
        
    
    def SetContrast(self, contrast):
        self.contrast = contrast
        self.UpdateBitmap()


    def ReceiveDrop(self, data):
        # Pass drop data on to parent if it is a DropTarget
        if issubclass(self.GetParent().__class__, DropTarget):
            self.GetParent().ReceiveDrop(data)



