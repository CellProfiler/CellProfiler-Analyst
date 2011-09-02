from colorbarpanel import ColorBarPanel
from dbconnect import DBConnect, UniqueImageClause, image_key_columns
from platemappanel import *
import imagetools
from properties import Properties
import numpy as np
import os
import re
import wx
from PlotPanelTS import *


p = Properties.getInstance()
# Hack the properties module so it doesn't require the object table.
#properties.optional_vars += ['object_table']
db = DBConnect.getInstance()


ID_IMPORT = 1001
ID_ADDPOINTS = 1002
ID_TABLE_SELECT = 1003
ID_REMOVEPOINTS = 1004

class DataSourcePanel(wx.Panel):
    
    def __init__(self, parent, figurepanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        #the panel to draw charts on
        self.figurepanel = figurepanel
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        

        testpanel = wx.Panel(self, style=wx.BORDER)
        sizer2 = wx.BoxSizer(wx.VERTICAL)


        import_button = wx.Button(testpanel, ID_IMPORT, "Import Properties File")
        self.importpathtext = wx.StaticText(testpanel, -1, "Please specify a properties file to import")
        self.tabledropdown = wx.Choice(testpanel, ID_TABLE_SELECT)
        
        
        wx.EVT_BUTTON(import_button, ID_IMPORT, self.loadproperties)        
        wx.EVT_CHOICE(self.tabledropdown, ID_TABLE_SELECT, self.selecttable)
        
        sizer2.Add(import_button)
        sizer2.Add(self.importpathtext)
        sizer2.Add(self.tabledropdown)        
        testpanel.SetSizer(sizer2)
        

        
        testpanel2 = wx.Panel(self, style=wx.BORDER)
        sizer3 = wx.BoxSizer(wx.VERTICAL)

        self.field1dropdown = wx.Choice(testpanel2)
        self.field2dropdown = wx.Choice(testpanel2)        
        self.addtochartbutton = wx.Button(testpanel2, ID_ADDPOINTS, "Add to Chart")

        sizer3.Add(wx.StaticText(testpanel2, -1, "Charting Selections"))
        sizer3.Add(wx.StaticText(testpanel2, -1, "x-axis:"))        
        sizer3.Add(self.field1dropdown)
        sizer3.Add(wx.StaticText(testpanel2, -1, "y-axis:"))                
        sizer3.Add(self.field2dropdown) 
        sizer3.Add(self.addtochartbutton) 
     
        wx.EVT_BUTTON(self.addtochartbutton, ID_ADDPOINTS, self.addtochart)   
    
        testpanel2.SetSizer(sizer3)
        
        
        
        
        testpanel3 = wx.Panel(self, style=wx.BORDER)
        
        self.plotfieldslistbox = wx.ListBox(testpanel3)
        self.removechartbutton = wx.Button(testpanel3, ID_REMOVEPOINTS, "Remove")
        
        
        sizer4 = wx.BoxSizer(wx.VERTICAL)
        sizer4.Add(self.plotfieldslistbox)
        sizer4.Add(self.removechartbutton)

        wx.EVT_BUTTON(self.removechartbutton, ID_REMOVEPOINTS, self.removefromchart)          
        
        testpanel3.SetSizer(sizer4)
        
        self.sizer.Add(testpanel, 1, wx.EXPAND)
        self.sizer.Add(testpanel2, 1, wx.EXPAND)
        self.sizer.Add(testpanel3, 1, wx.EXPAND)        
        
        #Layout sizers
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Show(1)


    def loadproperties(self, event):
        dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            os.chdir(os.path.split(filename)[0])      # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
            p.LoadFile(filename)
            self.importpathtext.SetLabel(filename)
            table_list = db.GetTableNames()
            self.tabledropdown.Clear()
            self.tabledropdown.AppendItems(table_list)
            
            
        else:
            print 'CellDistributionViewer requires a properties file.  Don\'t make me exit :-(.'

    def selecttable(self, event):
        tablename = event.GetString()
        #ok now fetch the list of fields from the database
        fieldnames = db.GetColumnNames(tablename)
        self.field1dropdown.Clear()
        self.field1dropdown.AppendItems(fieldnames)
        self.field1dropdown.SetSelection(0)
        self.field2dropdown.Clear()
        self.field2dropdown.AppendItems(fieldnames)
        self.field2dropdown.SetSelection(0)
        
    
    def addtochart(self, event):        
        addition = self.field1dropdown.GetStringSelection() + '  -  ' + self.field2dropdown.GetStringSelection()
        pointstuple = (self.tabledropdown.GetStringSelection(),
                       self.field1dropdown.GetStringSelection(),
                       self.field2dropdown.GetStringSelection())
        self.plotfieldslistbox.Append(addition, clientData=pointstuple)
        
        points = self.loadpoints(pointstuple[0], pointstuple[1], pointstuple[2])
        self.plotpoints(points)


    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)


    def loadpoints(self, tablename, xpoints, ypoints):
        #loads points from the database
        points = db.execute('SELECT %s, %s FROM %s LIMIT 5000'%(xpoints, ypoints, tablename)) 
        return [points]
        
    def plotpoints(self, points):
        self.figurepanel.setpointslists(points)
        self.figurepanel.draw()
        self.figurepanel.Refresh()


if __name__ == "__main__":

    theta = np.arange(0, 45 * 2 * np.pi, 0.02)

    rad0 = (0.8 * theta / (2 * np.pi) + 1)
    r0 = rad0 * (8 + np.sin(theta * 7 + rad0 / 1.8))
    x0 = r0 * np.cos(theta)
    y0 = r0 * np.sin(theta)

    rad1 = (0.8 * theta / (2 * np.pi) + 1)
    r1 = rad1 * (6 + np.sin(theta * 7 + rad1 / 1.9))
    x1 = r1 * np.cos(theta)
    y1 = r1 * np.sin(theta)

    points = [[(1, 1)],
              [(2, 2)],
              [(3, 3)],
              [(4, 4)],
              [(5, 5)]
              ]
    clrs = [[225, 200, 160], [219, 112, 147], [219, 112, 147], [219, 112, 147], [219, 112, 147]]

    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, " Demo with Notebook")
    nb = wx.Notebook(frame, -1)
    simplepanel = wx.Panel(nb, style=wx.BORDER)
    figpanel = FigurePanel(simplepanel, points, clrs)
        
    sizer = wx.BoxSizer()
    sizer.Add(figpanel, 1, wx.EXPAND)
    simplepanel.SetSizer(sizer)
    
        
    nb.AddPage(simplepanel, "Display")
    nb.AddPage(DataSourcePanel(nb, figpanel), "Data Sources") 
    
    frame.Show(1)
    app.MainLoop()

