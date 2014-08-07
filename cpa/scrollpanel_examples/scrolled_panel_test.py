import wx
from wx.combo import OwnerDrawnComboBox as ComboBox
from wx.lib.scrolledpanel import ScrolledPanel

class Choice(wx.Panel):
    def __init__(self, parent, allow_delete=True):
        wx.Panel.__init__(self, parent)        
        
        self.colChoice = ComboBox(self, choices=['a','b','c'], style=wx.CB_READONLY)
        self.colChoice.Select(0)
        if allow_delete:
            self.minus_button = wx.Button(self, label='-', size=(30,-1))
            self.minus_button.Bind(wx.EVT_BUTTON, lambda event: self.Parent.on_remove_choice(event,self))              
        self.plus_button = wx.Button(self, label='+', size=(30,-1))   
        self.plus_button.Bind(wx.EVT_BUTTON, lambda event: self.Parent.on_add_choice(event,self))     
        
        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(self.colChoice, 1, wx.EXPAND|wx.ALL,1)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.plus_button, 0, wx.EXPAND|wx.ALL,1)        
        if allow_delete:
            colSizer.AddSpacer((5,-1))
            colSizer.Add(self.minus_button, 0, wx.EXPAND)
        else:
            colSizer.AddSpacer((5,-1))
            colSizer.Add(wx.StaticText(self), 0,wx.EXPAND)
        self.SetSizerAndFit(colSizer)

class ChoicePanel(ScrolledPanel):
    def __init__(self,parent):
        ScrolledPanel.__init__(self, parent, -1)

        self.panel_sizer = wx.BoxSizer( wx.VERTICAL )
        self.choices = []
        c = Choice(self, False)
        self.panel_sizer.Add(c, 0, wx.EXPAND)
        self.choices.append(c)

        self.SetSizer(self.panel_sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling(False,True)

    def on_add_choice(self,event,selected_filter):
        self.choices.append(Choice(self, True))
        self.panel_sizer.Add(self.choices[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.SetupScrolling(False,True)
        self.panel_sizer.SetMinSize(self.panel_sizer.GetMinSize())
        self.SetSizerAndFit(self.panel_sizer)        
        self.SetAutoLayout(1)
        self.Refresh()
        self.Layout()      
                       
    def on_remove_choice(self,event,selected_filter):
        i = self.choices.index(selected_filter)
        self.choices.remove(selected_filter)
        self.panel_sizer.Remove(selected_filter)
        selected_filter.Destroy()
        self.SetupScrolling(False,len(self.choices) < 3 )  
        self.Refresh()
        self.Layout()          
        
class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.test_panel = ChoicePanel(self)
        self.sizer.Add(wx.StaticText(self, -1, "Some text here:"), 0, wx.CENTER|wx.ALL, 4)
        self.sizer.AddSpacer((4,-1))        
        self.sizer.Add(self.test_panel, 1, wx.CENTER|wx.ALL, 4)
        self.SetSizer(self.sizer)
        self.Layout()
        
if __name__=='__main__':
    app = wx.PySimpleApp()
    f = TestFrame()
    f.Show()
    app.MainLoop()    