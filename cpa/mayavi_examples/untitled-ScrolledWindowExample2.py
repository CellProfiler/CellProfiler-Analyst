import wx

class MyCustomWindow(wx.Window):
    def __init__(self, parent):
        wx.Window.__init__(self, parent)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetSize((50,50))

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetPen(wx.Pen('blue', 2))
        dc.SetBrush(wx.Brush('blue'))
        (width, height)=self.GetSizeTuple()
        dc.DrawRoundedRectangle(0, 0,width, height, 8)

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1)

        #self.Bind(wx.EVT_SIZE, self.OnSize)

        self.scrolling_window = wx.ScrolledWindow( self )
        self.scrolling_window.SetScrollRate(1,1)
        self.scrolling_window.EnableScrolling(True,True)
        self.sizer_container = wx.BoxSizer( wx.VERTICAL )
        self.sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.sizer_container.Add(self.sizer,1,wx.CENTER,wx.EXPAND)
        self.child_windows = []
        for i in range(0,50):
            wind = MyCustomWindow(self.scrolling_window)
            self.sizer.Add(wind, 0, wx.CENTER|wx.ALL, 5)
            self.child_windows.append(wind)

        self.scrolling_window.SetSizer(self.sizer_container)

    def OnSize(self, event):
        self.scrolling_window.SetSize(self.GetClientSize())

if __name__=='__main__':
    app = wx.PySimpleApp()
    f = TestFrame()
    f.Show()
    app.MainLoop()