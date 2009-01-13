import wx
from ImageTileSizer import ImageTileSizer

class Test(wx.ScrolledWindow):
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent)

        sizer = ImageTileSizer()

        for i in range(50):
            wxc=wx.TextCtrl(self,-1,style=0)
            sizer.Add(wxc)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Layout()
        self.Fit()

        self.unit=20
        width,height = self.GetSizeTuple()

        self.SetScrollbars(self.unit, self.unit, width/self.unit, height/self.unit)
        if (width>400): width=400
        if (height>400): height=400
        self.SetSize((width,height))
        self.Center()
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
    def OnSize(self, evt):
        w, h = evt.GetSize()
        self.SetVirtualSize(self.GetSizer().CalcMin())
        #self.GetSizer().SetSize( evt.GetSize() )


myapp=wx.PySimpleApp()
frame = wx.Frame(None)
x = Test(frame)
frame.Show(1)
myapp.MainLoop()

#import wx
#
#class MyScrolledWindow(wx.Frame):
#   def __init__(self, parent, id, title):
#       wx.Frame.__init__(self, parent, id, title, size=(400, 400))
#
#       sw = wx.ScrolledWindow(self)
#       bmp = wx.Image('/Users/afraser/Pictures/Photo 142-pola01.jpg',wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
#       wx.StaticBitmap(sw, -1, bmp)
#       w,h = bmp.GetSize()
#       sw.SetScrollbars(1,1,w,h)
#
#class MyApp(wx.App):
#   def OnInit(self):
#       frame = MyScrolledWindow(None, -1, 'Aliens')
#       frame.Show(True)
#       frame.Centre()
#       return True
#
#
#app = MyApp(0)
#app.MainLoop()
