'''
Main.py
Authors: afraser
'''

import wx
import os
from DBConnect import DBConnect
from DataModel import DataModel
from Properties import Properties
from ClassifierGUI import ClassifierGUI
import ImageLoaderGUI
from ImageReader import ImageReader
from ImageFrame import ImageFrame

class MainWindow(wx.Frame):
    def __init__(self, parent, id, title):
        self.db = None  # db connection
        self.dm = None  # data model
        
        style=wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER)
        wx.Frame.__init__(self, parent, id, title=title, size=(-1,-1), style=style)
        self.Center()
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour('White')
        self.CreateMenuBar()


    def CreateMenuBar(self):
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        menuFile = wx.Menu()
        menuBar.Append(menuFile, '&File')
        loadPropertiesMenuItem = menuFile.Append(-1, '&Load Properties File')
        self.Bind(wx.EVT_MENU, self.OnLoadProperties, loadPropertiesMenuItem)
        exitMenuItem = menuFile.Append(-1, 'E&xit', 'Exit the viewer')        
        self.Bind(wx.EVT_MENU, self.OnExit, exitMenuItem)

        menuTools = wx.Menu()
        menuBar.Append(menuTools, '&Tools')
        classifyMenuItem = menuTools.Append(-1, '&Classify')
        self.Bind(wx.EVT_MENU, self.OnClassify, classifyMenuItem)
        imageViewerMenuItem = menuTools.Append(-1, '&Image Viewer')
        self.Bind(wx.EVT_MENU, self.OnImageViewer, imageViewerMenuItem)
        browseImageMenuItem = menuTools.Append(-1, '&Browse for Image')
        self.Bind(wx.EVT_MENU, self.OnBrowseImage, browseImageMenuItem)        
        
    def OnLoadProperties(self, evt):
        dlg = wx.FileDialog(self, "Select a properties file", style=wx.OPEN)
        wildcard = "Properties files (.properties)|*.properties|" \
                   "All files (*.*)|*.*"
        dlg.SetWildcard(wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            p = Properties.getInstance()
            p.LoadFile(filename)
            self.db = DBConnect.getInstance()
            self.db.Connect(db_name=p.db_name, db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd)
            self.dm = DataModel.getInstance()
            self.dm.PopulateModel()
            print self.dm
        dlg.Destroy()


    def OnClassify(self, evt):
        self.classifier = ClassifierGUI(parent=self)
        self.classifier.Show()


    def OnImageViewer(self, evt):
        self.imageLoader = ImageLoaderGUI.Frame(parent=None, id=-1, title='Image Viewer')
        self.imageLoader.Show()
        
    
    def OnBrowseImage(self, event):
        filters = 'Image files (*.gif;*.png;*.jpg;*.dib;*.tif)|*.gif;*.png;*.jpg;*.dib;*.tif'
        dlg = wx.FileDialog(self, message="Open an Image...", defaultDir=os.getcwd(), 
                            defaultFile="", wildcard=filters, style=wx.OPEN)
        
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()    
            reader = ImageReader()
            reader.format = filename[-3:]
            reader.ReadImages([filename])
            imFrame = ImageFrame(image=reader.GetImages()[0], parent=self)
            imFrame.Show(True)
   
        dlg.Destroy() # we don't need the dialog any more so we ask it to clean-up


    def OnExit(self, event):
        "Close the application by Destroying the object"
        self.Destroy() 



class MainApp(wx.App):
    
    def OnInit(self):
        self.frame = MainWindow(parent=None, id=-1, title='Classifier Test')
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

if __name__ == "__main__":       
    # make an App object, set stdout to the console so we can see errors
    app = MainApp(redirect=False)
    app.MainLoop()
