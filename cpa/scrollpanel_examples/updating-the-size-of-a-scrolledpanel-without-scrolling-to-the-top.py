'''
 From http://stackoverflow.com/questions/22078836/updating-the-size-of-a-scrolledpanel-without-scrolling-to-the-top
 
 Consider the following dummy application:
 
 It contains a ScrolledPanel to which content is dynamically added when the user presses the button. The ScrolledPanel 
 seems to update its size and layout okay, but if I scroll partway down the list and press the button, the SetupScrolling 
 call causes the scroll position to jump back to the top. This will be unacceptable behavior for my application. How can 
 I do one of the following?
 
 1. Lay out the scrolled area without jumping to the top
 
 2. Call SetupScrolling only if the content area has actually changed size 
 
Thanks to this answer on a similar question, I found that I needed to call FitInside instead of SetupScrolling to get the scroll bars to update. This does not affect the scroll position.

My example code needs to be modified to change MyPanel.add_text_line to this:

    def add_text_line(self, text):
        self.sizer.Add(wx.StaticText(self, label=text))
        self.sizer.Layout()
        self.FitInside()
'''
import wx
from wx.lib.scrolledpanel import ScrolledPanel


class MyPanel(ScrolledPanel):
    def __init__(self, parent):
        ScrolledPanel.__init__(self, parent, size=(128, 64))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.SetAutoLayout(1)
        self.SetupScrolling(scroll_x=False, scroll_y=True)
        
    def add_text_line(self, text):
        self.sizer.Add(wx.StaticText(self, label=text))
        self.sizer.Layout()
        self.FitInside()        

class MainWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title='Test Window')

        self.line_number = 1

        sizer = wx.BoxSizer(wx.VERTICAL)

        button = wx.Button(self, label='Add a row')
        self.Bind(wx.EVT_BUTTON, self.add_row, button)
        sizer.Add(button)

        self.panel = MyPanel(self)
        sizer.Add(self.panel)

        self.SetSizer(sizer)

    def add_row(self, _):
        self.panel.add_text_line('Line number ' + str(self.line_number))
        self.line_number += 1


if __name__ == '__main__':
    app = wx.App(False)
    MainWindow(None).Show()
    app.MainLoop()