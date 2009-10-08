from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, image_key_columns
from PlateMapPanel import *
from PlotPanel import *
from Properties import Properties
import ImageTools
import numpy as np
import os
import re
import wx


p = Properties.getInstance()
db = DBConnect.getInstance()

ID_EXIT = wx.NewId()

class DataSourcePanel(wx.Panel):
    '''
    A panel with controls for selecting the source data for a scatterplot 
    '''
    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        # the panel to draw charts on
        self.figpanel = figpanel
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.table_choice = wx.Choice(self, -1, choices=db.GetTableNames())
        self.x_choice = wx.Choice(self, -1)
        self.y_choice = wx.Choice(self, -1)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_column_fields()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "table:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.table_choice, 1, wx.EXPAND)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.x_choice)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "y-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.y_choice)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_CHOICE(self.table_choice, -1, self.on_table_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.on_update_pressed)   
        self.Bind(wx.EVT_SIZE, self._onsize)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        sizer.Fit(self)
        self.Show(1)

    def on_table_selected(self, evt):
        self.update_column_fields()
        
    def update_column_fields(self):
        tablename = self.table_choice.GetStringSelection()
        fieldnames = db.GetColumnNames(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)
        self.y_choice.Clear()
        self.y_choice.AppendItems(fieldnames)
        self.y_choice.SetSelection(0)        
        
    def on_update_pressed(self, evt):        
        points = self.loadpoints(self.table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 self.y_choice.GetStringSelection())
        self.plotpoints(points)
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xpoints, ypoints):
        #loads points from the database
        n_points = 99999999
        points = db.execute('SELECT %s, %s FROM %s LIMIT %s'%(xpoints, ypoints, tablename, n_points)) 
        return [points]
    
    def plotpoints(self, points):
        self.figpanel.setpointslists(points)
        self.figpanel.draw()
        
    def _onsize(self, evt):
        self.figpanel._SetSize()
        evt.Skip()
        


class Scatter(wx.Frame):
    '''
    A very basic scatter plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600)):
        wx.Frame.__init__(self, parent, -1, size=size, title='Scatter plot')
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.exitMenuItem = wx.MenuItem(parentMenu=self.fileMenu, 
                                        id=ID_EXIT, text='Exit\tCtrl+Q',
                                        help='Close PlateMapBrowser')
        self.fileMenu.AppendItem(self.exitMenuItem)
        self.GetMenuBar().Append(self.fileMenu, 'File')
        wx.EVT_MENU(self, ID_EXIT, lambda evt:self.Close())
        
        accelerator_table = wx.AcceleratorTable([(wx.ACCEL_CTRL,ord('Q'),ID_EXIT),])
        self.SetAcceleratorTable(accelerator_table)
        
        points = [[(1, 1)],[(2, 2)],[(3, 3)],[(4, 4)],[(5, 5)]]
        clrs = [[225, 200, 160], [219, 112, 147], [219, 112, 147], [219, 112, 147], [219, 112, 147]]
        
        figpanel = FigurePanel(self, points, clrs)
        configpanel = DataSourcePanel(self, figpanel)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
        sizer.Add(configpanel, 0)
        self.SetSizer(sizer)
        



def LoadProperties():
    import os
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])  # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        print 'Scatterplot requires a properties file.  Exiting.'
        exit()

            
if __name__ == "__main__":
    app = wx.PySimpleApp()
        
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        LoadProperties()

    scatter = Scatter(None)
    scatter.Show()
    
    app.MainLoop()

#if __name__ == "__main__":
#    points = [[(1, 1)],[(2, 2)],[(3, 3)],[(4, 4)],[(5, 5)]]
#    clrs = [[225, 200, 160], [219, 112, 147], [219, 112, 147], [219, 112, 147], [219, 112, 147]]
#
#    app = wx.PySimpleApp()
#
#    p.LoadFile('/Users/afraser/ExampleImages/cpa_example/example.properties')
#    
#    frame = wx.Frame(None, -1, "Scatter Plot")
#    figpanel = FigurePanel(frame, points, clrs)
#    configpanel = DataSourcePanel(frame, figpanel)
#    
##    sizer = wx.BoxSizer(wx.VERTICAL)
##    sizer.Add(figpanel, 1, wx.EXPAND)
##    sizer.Add(configpanel, 0)
#    
##    frame.SetSizer(sizer)
#    
#    frame.Show(1)
#    app.MainLoop()

