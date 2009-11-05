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

NO_FILTER = 'No filter'

ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LINEAR_SCALE = 'linear'

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
        self.table_choice.Select(0)
        self.x_choice = wx.Choice(self, -1)
        self.y_choice = wx.Choice(self, -1)
#        self.x_scale_choice = wx.Choice(self, -1, choices=[LINEAR_SCALE, LOG_SCALE])
#        self.y_scale_choice = wx.Choice(self, -1, choices=[LINEAR_SCALE, LOG_SCALE])
#        self.filter_choice = wx.Choice(self, -1, choices=[NO_FILTER]+p._filters_ordered)
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
#        sz.AddSpacer((5,-1))
#        sz.Add(wx.StaticText(self, -1, "x-scale:"))
#        sz.AddSpacer((5,-1))
#        sz.Add(self.x_scale_choice)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "y-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.y_choice)
#        sz.AddSpacer((5,-1))
#        sz.Add(wx.StaticText(self, -1, "y-scale:"))
#        sz.AddSpacer((5,-1))
#        sz.Add(self.y_scale_choice)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sz = wx.BoxSizer(wx.HORIZONTAL)
#        sz.Add(wx.StaticText(self, -1, "filter:"))
#        sz.AddSpacer((5,-1))
#        sz.Add(self.filter_choice)
#        sizer.Add(sz)
#        sizer.AddSpacer((-1,5))
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_CHOICE(self.table_choice, -1, self.on_table_selected)
#        wx.EVT_CHOICE(self.x_scale_choice, -1, self.on_x_scale_selected)
#        wx.EVT_CHOICE(self.y_scale_choice, -1, self.on_y_scale_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.on_update_pressed)   
        self.Bind(wx.EVT_SIZE, self._onsize)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        sizer.Fit(self)
        self.Show(1)
        
    def on_x_scale_selected(self, evt):
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())        
        
    def on_y_scale_selected(self, evt):
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())

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
#        self.filter = self.filter_choice.GetStringSelection()
        points = self.loadpoints(self.table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 self.y_choice.GetStringSelection())
#                                 self.filter)
        # plot the points
        self.figpanel.setpointslists(points)
        self.figpanel.draw()
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xpoints, ypoints, filter=NO_FILTER):
        #loads points from the database
        q = 'SELECT %s, %s FROM %s'%(xpoints, ypoints, tablename)
#        if filter!=NO_FILTER:
#            wc_start = p._filters[filter].upper().find(' WHERE ')
#            q += p._filters[filter][wc_start:]
        points = db.execute(q) 
        return [points]
    
        
    def _onsize(self, evt):
        self.figpanel._SetSize()
        evt.Skip()
        

class ScatterPanel(PlotPanel):
    def __init__(self, parent, point_lists, clr_list, **kwargs):
        self.parent = parent
        self.point_lists = point_lists
        self.clr_list = clr_list
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE

        # initiate plotter
        PlotPanel.__init__(self, parent, **kwargs)
        self.SetColor((255, 255, 255))
    
    def setpointslists(self, points):
        self.point_lists = points
    
    def getpointslists(self):
        return self.point_lists
    
    def set_x_scale(self, scale):
        self.x_scale = scale
    
    def set_y_scale(self, scale):
        self.y_scale = scale
    
    def draw(self):
        #Draw data.
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
        for i, pt_list in enumerate(self.point_lists):
            plot_pts = np.array(pt_list)
            clr = [float(c) / 255. for c in self.clr_list[i]]
            self.subplot.scatter(plot_pts[:, 0], plot_pts[:, 1], color=clr, 
                                 edgecolor='none', alpha=0.75)
#            if self.x_scale == self.y_scale == LOG_SCALE:
#                self.subplot.loglog()
#            elif self.x_scale == LOG_SCALE:
#                self.subplot.semilogx()
#            elif self.y_scale == LOG_SCALE:
#                self.subplot.semilogy()
#            xmin = np.nanmin(plot_pts[:,0])
#            xmax = np.nanmax(plot_pts[:,0])
#            ymin = np.nanmin(plot_pts[:,1])
#            ymax = np.nanmax(plot_pts[:,1])
#            xpad = (xmax-xmin)/20.
#            ypad = (ymax-ymin)/20.
#            self.subplot.axis([xmin, xmax, ymin, ymax])
        self.canvas.draw()
        

class Scatter(wx.Frame):
    '''
    A very basic scatter plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600)):
        wx.Frame.__init__(self, parent, -1, size=size, title='Scatter plot')
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.exitMenuItem = self.fileMenu.Append(ID_EXIT, text='Exit\tCtrl+Q',
                                                 help='Close Scatter Plot')
        self.fileMenu.AppendItem(self.exitMenuItem)
        self.GetMenuBar().Append(self.fileMenu, 'File')
        wx.EVT_MENU(self, ID_EXIT, lambda evt:self.Close())
        
        points = [[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]]
        clrs = [[238, 70, 148]]
        
        figpanel = ScatterPanel(self, points, clrs)
#        figpanel = cpfig.CPFigurePanel(self, -1)
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
    
    logging.basicConfig(level=logging.DEBUG,)
        
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
#    figpanel = ScatterPanel(frame, points, clrs)
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

