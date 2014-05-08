import wx
import  wx.lib.scrolledpanel as scrolled

class ImageDlg(wx.Dialog):
    def __init__(self, parent, title):
        wx.Dialog.__init__(self, parent=parent,title=title, size=wx.DefaultSize)
        
        self.scrollPnl = scrolled.ScrolledPanel(self, -1, size=(200, 200), style = wx.SUNKEN_BORDER)

        self.addBtn = wx.Button(self, id=wx.ID_ADD)
        self.Bind(wx.EVT_BUTTON, self.on_add, self.addBtn)

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)       

        self.scrollPnlSizer = wx.BoxSizer(wx.VERTICAL)       
        img = wx.Image("add_stain.png", wx.BITMAP_TYPE_ANY)
        staticBitmap = wx.StaticBitmap(self.scrollPnl, wx.ID_ANY, wx.BitmapFromImage(img))
        self.scrollPnlSizer.Add(staticBitmap, 1, wx.EXPAND | wx.ALL, 3)

        self.mainSizer.Add(self.addBtn)
        self.mainSizer.Add(self.scrollPnl)

        self.SetSizerAndFit(self.mainSizer)


    def on_add(self, event):
        img = wx.Image("add_stain.png", wx.BITMAP_TYPE_ANY)
        staticBitmap = wx.StaticBitmap(self.scrollPnl, wx.ID_ANY, wx.BitmapFromImage(img))
        self.scrollPnlSizer.Add(staticBitmap, 1, wx.EXPAND | wx.ALL, 3)
        self.scrollPnl.SetSizer(self.scrollPnlSizer)
        self.scrollPnl.SetAutoLayout(1)
        self.scrollPnl.SetupScrolling()  

        self.Refresh()
        self.Layout()

class TestPanel(wx.Panel):     
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)

        openDlg_btn = wx.Button(self, label="Open Dialog")
        self.Bind(wx.EVT_BUTTON, self.onBtn)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(openDlg_btn, 0, wx.ALL, 10)
        self.SetSizerAndFit(mainSizer)
        self.Centre()

    def onBtn(self, event):
        dlg = ImageDlg(self, title='Image Dialog')
        dlg.SetSize((300,300))

        dlg.CenterOnScreen()
        dlg.ShowModal()  
        dlg.Destroy()


class TestFrame(wx.Frame):    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent)
        TestPanel(self)


if __name__ == "__main__":

    app = wx.PySimpleApp()
    frame = TestFrame(None)
    frame.Show()
    app.MainLoop()