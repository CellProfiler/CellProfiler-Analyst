'''
https://groups.google.com/forum/#!topic/wxpython-users/4dA11MLwKYw
'''
import wx
import  wx.lib.scrolledpanel as scrolled
image_filename = r"\\iodine\imaging_analysis\2011_01_04_NSF_RIG_TLM_tools\CellProfiler-Analyst\cpa\icons\add_stain.png"

class TestPanel(scrolled.ScrolledPanel):     
    def __init__(self, parent, lsize):
        scrolled.ScrolledPanel.__init__(self, parent, -1, size=lsize, style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)

        self.btn_add = wx.Button(self, label="Add")
        self.Bind(wx.EVT_BUTTON, self.on_add, self.btn_add)

        self.scrollPnlSizer = wx.BoxSizer(wx.VERTICAL)

        img = wx.Image(image_filename, wx.BITMAP_TYPE_ANY)
        staticBitmap = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))
        
        self.scrollPnlSizer.Add(self.btn_add)

        self.scrollPnlSizer.Add(staticBitmap, 1, wx.EXPAND | wx.ALL, 3)

        self.SetSizer(self.scrollPnlSizer)


        self.Centre()

    def on_add(self, event):
        img = wx.Image(image_filename, wx.BITMAP_TYPE_ANY)
        staticBitmap = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))

        self.scrollPnlSizer.Add(staticBitmap, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSizer(self.scrollPnlSizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()  

        self.Refresh()
        self.Layout()


class TestFrame(wx.Frame):    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent)
        self.Maximize(True)
        size = self.GetSize()
        TestPanel(self, size)

if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = TestFrame(None)
    frame.Show()
    app.MainLoop()

