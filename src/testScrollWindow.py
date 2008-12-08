import wx

class MyScrolledWindow(wx.Frame):
   def __init__(self, parent, id, title):
       wx.Frame.__init__(self, parent, id, title, size=(400, 400))

       sw = wx.ScrolledWindow(self)
       bmp = wx.Image('/Users/afraser/Desktop/swinger.jpg',wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
       wx.StaticBitmap(sw, -1, bmp)
       w,h = bmp.GetSize()
       sw.SetScrollbars(1,1,w,h)

class MyApp(wx.App):
   def OnInit(self):
       frame = MyScrolledWindow(None, -1, 'Aliens')
       frame.Show(True)
       frame.Centre()
       return True


app = MyApp(0)
app.MainLoop()