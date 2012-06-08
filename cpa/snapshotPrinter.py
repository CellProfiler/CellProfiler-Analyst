#######################################################################
# snapshotPrinter.py
#
# Created: 12/26/2007 by mld
#
# Description: Displays screenshot image using html and then allows
#              the user to print it.
#######################################################################
 
import os
import wx
from wx.html import HtmlEasyPrinting, HtmlWindow
 
class SnapshotPrinter(wx.Frame):
 
    #----------------------------------------------------------------------
    def __init__(self, title='Snapshot Printer'):
        wx.Frame.__init__(self, None, wx.ID_ANY, title, size=(650,400))
 
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.printer = HtmlEasyPrinting(name='Printing', parentWindow=None)
 
        self.html = HtmlWindow(self.panel)
        self.html.SetRelatedFrame(self, self.GetTitle())
 
        if not os.path.exists('screenshot.htm'):
            self.createHtml()
        self.html.LoadPage('screenshot.htm')
 
        pageSetupBtn = wx.Button(self.panel, wx.ID_ANY, 'Page Setup')
        printBtn = wx.Button(self.panel, wx.ID_ANY, 'Print')
        cancelBtn = wx.Button(self.panel, wx.ID_ANY, 'Cancel')
 
        self.Bind(wx.EVT_BUTTON, self.onSetup, pageSetupBtn)
        self.Bind(wx.EVT_BUTTON, self.onPrint, printBtn)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelBtn)
 
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
 
        sizer.Add(self.html, 1, wx.GROW)
        btnSizer.Add(pageSetupBtn, 0, wx.ALL, 5)
        btnSizer.Add(printBtn, 0, wx.ALL, 5)
        btnSizer.Add(cancelBtn, 0, wx.ALL, 5)
        sizer.Add(btnSizer)
 
        self.panel.SetSizer(sizer)
        self.panel.SetAutoLayout(True)
 
    #----------------------------------------------------------------------
    def createHtml(self):
        '''
        Creates an html file in the home directory of the application
        that contains the information to display the snapshot
        '''
        print 'creating html...'
 
        #html = '<html>\n<body>\n<center><img src=myImage.png width=700 height=800></center>\n</body>\n</html>'
        f = file('screenshot.htm', 'w')
        f.write(open('C:/Protocols/CoreProtocols/20111213_1_transfer_example.txt').read()) 
        f.write('<html>\n<body>\n<center><img src=myImage.png width=350 height=600></center>\n</body>\n</html>')
        f.close()
 
    #----------------------------------------------------------------------
    def onSetup(self, event):
        self.printer.PageSetup()
 
    #----------------------------------------------------------------------
    def onPrint(self, event):
        self.sendToPrinter()
 
    #----------------------------------------------------------------------
    def sendToPrinter(self):
        """"""
        self.printer.GetPrintData().SetPaperId(wx.PAPER_LETTER)
        self.printer.PrintFile(self.html.GetOpenedPage())
 
    #----------------------------------------------------------------------
    def onCancel(self, event):
        self.Close()
 
 
class wxHTML(HtmlWindow):
    #----------------------------------------------------------------------
    def __init__(self, parent, id):
        html.HtmlWindow.__init__(self, parent, id, style=wx.NO_FULL_REPAINT_ON_RESIZE)
 
 
if __name__ == '__main__':
    app = wx.App(False)
    frame = SnapshotPrinter()
    frame.Show()
    app.MainLoop()