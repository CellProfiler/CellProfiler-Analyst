'''
From http://stackoverflow.com/questions/16194279/scrolledpanel-not-resizing-after-destroychildren
I got this code from a topic on Stackoverflow ScrolledPanel inside Panel not sizing. It works well for me. 
However I want to destroy all children of the scrolled_panel then recreate its new children. So I modify the code like this:

import wx
import wx.lib.scrolledpanel as scrolled

########################################################################
class MyForm(wx.Frame):

    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Tutorial", size=(200,500))

        self.n = 13
        # Add a panel so it looks the correct on all platforms
        self.panel = wx.Panel(self, wx.ID_ANY)

        # --------------------
        # Scrolled panel stuff
        self.scrolled_panel = scrolled.ScrolledPanel(self.panel, -1, 
                                 style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER, name="panel1")
        self.scrolled_panel.SetAutoLayout(1)
        self.scrolled_panel.SetupScrolling()

        words = "A Quick Brown Insane Fox Jumped Over the Fence and Ziplined to Cover".split()
        self.spSizer = wx.BoxSizer(wx.VERTICAL)
        for word in words:
            text = wx.TextCtrl(self.scrolled_panel, value=word)
            self.spSizer.Add(text)
        self.scrolled_panel.SetSizer(self.spSizer)
        # --------------------

        btn = wx.Button(self.panel, label="Add Widget")
        btn.Bind(wx.EVT_BUTTON, self.onAdd)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.AddSpacer(50)
        panelSizer.Add(self.scrolled_panel, 1, wx.EXPAND)
        panelSizer.Add(btn)
        self.panel.SetSizer(panelSizer)

    #----------------------------------------------------------------------
    def onAdd(self, event):
        """"""
        print "in onAdd"
        self.n += 1
        self.scrolled_panel.DestroyChildren()
        for i in range(self.n):
            new_text = wx.TextCtrl(self.scrolled_panel, value="New Text %s" % i)
            self.spSizer.Add(new_text)
        #new_text = wx.TextCtrl(self.scrolled_panel, value="New Text")
        #self.spSizer.Add(new_text)
        self.scrolled_panel.Layout()
        self.scrolled_panel.SetupScrolling()


# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyForm().Show()
    app.MainLoop()
Now, even when I create the children more than the panel's size can show, I don't see the scroll bar as the 
original code. Can any one help me with this? Thanks ahead!!!

I solved this problem by adding testpanel to add scrolledPanel in it. Whennever onAdd() is call, after destroying 
all of testpanel's children, everything under the testpanel even the sizer have to be re-created and re-setup.

I've tried to do like that without the testpanel, I still could scroll by using my mouse, but didn't see the scrollbar, 
I don't know why. This is my new code:
'''

import wx
import wx.lib.scrolledpanel as scrolled

########################################################################
class MyForm(wx.Frame):

    #----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Tutorial", size=(200,500))

        # Add a panel so it looks the correct on all platforms
        self.panel = wx.Panel(self, wx.ID_ANY)

        # --------------------
        # Scrolled panel stuff
        self.scrolled_panel = scrolled.ScrolledPanel(self.panel, -1, 
                                 style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER, name="panel1")
        self.scrolled_panel.SetAutoLayout(1)
        self.scrolled_panel.SetupScrolling()

        words = "A Quick Brown Insane Fox Jumped Over the Fence and Ziplined to Cover".split()
        self.spSizer = wx.BoxSizer(wx.VERTICAL)
        for word in words:
            text = wx.TextCtrl(self.scrolled_panel, value=word)
            self.spSizer.Add(text)
        self.scrolled_panel.SetSizer(self.spSizer)
        # --------------------

        btn = wx.Button(self.panel, label="Add Widget")
        btn.Bind(wx.EVT_BUTTON, self.onAdd)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.AddSpacer(50)
        panelSizer.Add(self.scrolled_panel, 1, wx.EXPAND)
        panelSizer.Add(btn)
        self.panel.SetSizer(panelSizer)

    #----------------------------------------------------------------------
    def onAdd(self, event):
        """"""
        print "in onAdd"
        new_text = wx.TextCtrl(self.scrolled_panel, value="New Text")
        self.spSizer.Add(new_text)
        self.scrolled_panel.Layout()
        self.scrolled_panel.SetupScrolling()

# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyForm().Show()
    app.MainLoop()