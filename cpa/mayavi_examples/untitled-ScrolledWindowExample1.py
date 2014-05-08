import wx
from wx.combo import OwnerDrawnComboBox as ComboBox
from wx.lib.scrolledpanel import ScrolledPanel

class MeasurementFilter(wx.Panel):
    def __init__(self, parent, allow_delete=True):
        wx.Panel.__init__(self, parent)        
        
        self.colChoice = ComboBox(self, choices=['a','b'], style=wx.CB_READONLY)
        self.colChoice.Select(0)
        self.comparatorChoice = ComboBox(self, choices=['=','<','>'])
        self.comparatorChoice.Select(0)
        self.valueField = wx.ComboBox(self, -1, value='')
        if allow_delete:
            self.minus_button = wx.Button(self, -1, '-', size=(30,-1))
            self.minus_button.Bind(wx.EVT_BUTTON, lambda event: self.Parent.on_remove_filter(event,self))              
        self.plus_button = wx.Button(self, -1, '+', size=(30,-1))   
        self.plus_button.Bind(wx.EVT_BUTTON, lambda event: self.Parent.on_add_filter(event,self))     
        
        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(self.colChoice, 1, wx.EXPAND|wx.ALL,1)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.comparatorChoice, 1, wx.EXPAND|wx.ALL,1)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.valueField, 1, wx.EXPAND|wx.ALL,1)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.plus_button, 0, wx.EXPAND|wx.ALL,1)        
        if allow_delete:
            colSizer.AddSpacer((5,-1))
            colSizer.Add(self.minus_button, 0, wx.EXPAND)
        self.SetSizer(colSizer)
        #self.Layout()

class FilterPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent, -1)
        
        self.scrolling_window = wx.ScrolledWindow(self,-1)
        self.scrolling_window.SetScrollRate(1,1)
        self.scrolling_window.EnableScrolling(False,True)
        #self.scrolling_window.Bind(wx.EVT_SIZE, self.OnSize)        

        self.sizer_container = wx.BoxSizer( wx.VERTICAL )
        self.sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.sizer_container.Add(self.sizer,0,wx.CENTER,wx.EXPAND)
        self.child_windows = []
        filt = MeasurementFilter(self, False)
        self.sizer.Add(filt, 0, wx.CENTER|wx.ALL, 5)
        self.child_windows.append(filt)

        self.scrolling_window.SetSizer(self.sizer_container)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)  
        sizer.Add(self.scrolling_window, 1, wx.ALL, 4)
        self.SetSizer(sizer)

    def on_add_filter(self,event,selected_filter):
        self.filters += [MeasurementFilter(self, True)]
        self.scrolledwindow.Sizer.Add(self.filters[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.scrolledwindow.FitInside()
        
    def on_remove_filter(self,event,selected_filter):
        i = self.filters.index(selected_filter)
        self.Sizer.Remove(selected_filter)
        self.panels.remove(selected_filter)
        selected_filter.Destroy()
        self.scrolledwindow.FitInside()        
        
    def OnSize(self, event):
        self.scrolling_window.SetSize(self.GetClientSize())
        
class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.test_panel = FilterPanel(self)
        sizer.Add(wx.StaticText(self, -1, "Filter:"), 0, wx.CENTER|wx.ALL, 4)
        sizer.AddSpacer((4,-1))        
        sizer.Add(self.test_panel, 1, wx.CENTER|wx.ALL, 4)
        self.SetSizer(sizer)
        
if __name__=='__main__':
    app = wx.PySimpleApp()
    f = TestFrame()
    f.Show()
    app.MainLoop()    