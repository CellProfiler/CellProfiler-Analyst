'''
From http://stackoverflow.com/questions/578200/easiest-way-to-create-a-scrollable-area-using-wxpython

Okay, so I want to display a series of windows within windows and have the whole lot scrollable. I've 
been hunting through the wxWidgets documentation and a load of examples from various sources on t'internet. 
Most of those seem to imply that a wx.ScrolledWindow should work if I just pass it a nested group of sizers(?):

The most automatic and newest way is to simply let sizers determine the scrolling area.This is now the 
default when you set an interior sizer into a wxScrolledWindow with wxWindow::SetSizer. The scrolling 
area will be set to the size requested by the sizer and the scrollbars will be assigned for each orientation 
according to the need for them and the scrolling increment set by wxScrolledWindow::SetScrollRate.

...but all the example's I've seen seem to use the older methods listed as ways to achieve scrolling. I've 
got something basic working, but as soon as you start scrolling you lose the child windows:
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

        self.Bind(wx.EVT_SIZE, self.OnSize)

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
    
    
Oops.. turns out I was creating my child windows badly:

wind = MyCustomWindow(self)
should be:

wind = MyCustomWindow(self.scrolling_window)
..which meant the child windows were waiting for the top-level 
window (the frame) to be re-drawn instead of listening to the 
scroll window. Changing that makes it all work wonderfully :)
'''
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