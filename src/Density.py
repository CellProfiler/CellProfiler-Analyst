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
    A panel with controls for selecting the source data for a densityplot 
    '''
    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        # the panel to draw charts on
        self.figpanel = figpanel
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.table_choice = wx.Choice(self, -1, choices=db.GetTableNames())
        self.table_choice.Select(0)
        self.x_choice = wx.Choice(self, -1)
        self.y_choice = wx.Choice(self, -1)
        self.gridsize_input = wx.TextCtrl(self, -1, '100')
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
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "grid size:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.gridsize_input)
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
        fieldnames = self.get_numeric_columns_from_table(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)
        self.y_choice.Clear()
        self.y_choice.AppendItems(fieldnames)
        self.y_choice.SetSelection(0)

    def get_numeric_columns_from_table(self, table):
        ''' Fetches names of numeric columns for the given table. '''
        measurements = db.GetColumnNames(table)
        types = db.GetColumnTypes(table)
        return [m for m,t in zip(measurements, types) if t in [float, int, long]]
        
    def on_update_pressed(self, evt):        
        points = self.loadpoints(self.table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 self.y_choice.GetStringSelection())
        gridsize = int(self.gridsize_input.GetValue())
        self.plotpoints(points, gridsize)
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xpoints, ypoints):
        #loads points from the database
        n_points = 10000000
        points = db.execute('SELECT %s, %s FROM %s LIMIT %s'%(xpoints, ypoints, tablename, n_points)) 
        return [points]
    
    def plotpoints(self, points, gridsize):
        self.figpanel.setpointslists(points)
        self.figpanel.setgridsize(gridsize)
        self.figpanel.draw()
        
    def _onsize(self, evt):
        self.figpanel._SetSize()
        evt.Skip()
        

class DensityPanel(PlotPanel):
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.point_lists = []
        self.gridsize = 100
        self.cb = None
        
        # initiate plotter
        PlotPanel.__init__(self, parent, **kwargs)
        self.SetColor((255, 255, 255))
    
    def setpointslists(self, points):
        self.point_lists = points
    
    def getpointslists(self):
        return self.point_lists
    
    def setgridsize(self, gridsize):
        self.gridsize = gridsize
    
    def draw(self):
        #Draw data.
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)

        self.subplot.clear()

        for i, pt_list in enumerate(self.point_lists):
            plot_pts = np.array(pt_list)
            hb = self.subplot.hexbin(plot_pts[:, 0], plot_pts[:, 1], 
                                     gridsize=self.gridsize)#,
#                                     xscale='log', yscale='log')
            if self.cb:
                self.cb.update_bruteforce(hb)
            else:
                self.cb = self.figure.colorbar(hb)
        self.canvas.draw()
        

class Density(wx.Frame):
    '''
    A very basic density plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600)):
        wx.Frame.__init__(self, parent, -1, size=size, title='density plot')
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.exitMenuItem = self.fileMenu.Append(ID_EXIT, text='Exit\tCtrl+Q',
                                                 help='Close Density Plot')
        self.fileMenu.AppendItem(self.exitMenuItem)
        self.GetMenuBar().Append(self.fileMenu, 'File')
        wx.EVT_MENU(self, ID_EXIT, lambda evt:self.Close())
        
        figpanel = DensityPanel(self)
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
        print 'Densityplot requires a properties file.  Exiting.'
        exit()

            
if __name__ == "__main__":
    app = wx.PySimpleApp()
        
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        LoadProperties()

    density = Density(None)
    density.Show()
    
    app.MainLoop()