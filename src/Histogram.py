from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, image_key_columns
from MulticlassSQL import filter_table_prefix
from PlateMapPanel import *
from PlotPanel import *
from Properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import ImageTools
import numpy as np
import os
import sys
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
    A panel with controls for selecting the source data for a histogramplot 
    '''
    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        # the panel to draw charts on
        self.figpanel = figpanel
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        tables = db.GetTableNames()
        self.table_choice = ComboBox(self, -1, choices=tables, style=wx.CB_READONLY)
        self.table_choice.Select(tables.index(p.image_table))
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.bins_input = wx.TextCtrl(self, -1, '100')
        self.filter_choice = ComboBox(self, -1, choices=[NO_FILTER]+p._filters_ordered, style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_column_fields()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "table:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.table_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.x_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "bins:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.bins_input)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_COMBOBOX(self.table_choice, -1, self.on_table_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.on_update_pressed)   
        self.Bind(wx.EVT_SIZE, self._onsize)
        
        self.SetSizer(sizer)
        self.Show(1)

    def on_table_selected(self, evt):
        self.update_column_fields()
        
    def update_column_fields(self):
        tablename = self.table_choice.GetStringSelection()
        fieldnames = self.get_numeric_columns_from_table(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)

    def get_numeric_columns_from_table(self, table):
        ''' Fetches names of numeric columns for the given table. '''
        measurements = db.GetColumnNames(table)
        types = db.GetColumnTypes(table)
        return [m for m,t in zip(measurements, types) if t in [float, int, long]]
        
    def on_update_pressed(self, evt):    
        filter = self.filter_choice.GetStringSelection()
        points = self.loadpoints(self.table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 filter)    
        bins = int(self.bins_input.GetValue())
        self.figpanel.set_x_label(self.x_choice.GetStringSelection())
        self.figpanel.setpoints(points, bins)
        self.figpanel.draw()
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xpoints, filter=NO_FILTER):
        fields = '%s.%s'%(tablename, xpoints)
        tables = tablename
        where_clause = ''
        if filter != NO_FILTER:
            # If a filter is applied we must compute a WHERE clause and add the 
            # filter table to the FROM clause
            tables += ', `%s`'%(filter_table_prefix+filter) 
            filter_clause = ' AND '.join(['%s.%s=`%s`.%s'%(tablename, id, filter_table_prefix+filter, id) 
                                          for id in db.GetLinkingColumnsForTable(tablename)])
            where_clause = 'WHERE %s'%(filter_clause)
        return [db.execute('SELECT %s FROM %s %s'%(fields, tables, where_clause))]
    
    def _onsize(self, evt):
        self.figpanel._SetSize()
        evt.Skip()
        

class HistogramPanel(PlotPanel):
    def __init__(self, parent, points, bins=100, **kwargs):
        self.parent = parent
        self.setpoints(points, bins)
        self.x_label = ''
        
        # initiate plotter
        PlotPanel.__init__(self, parent, **kwargs)
        self.SetColor((255, 255, 255))
    
    def setpoints(self, points, bins):
        self.points = np.array(points)
        self.bins = bins
    
    def set_x_label(self, label):
        self.x_label = label
        
    def getpointslists(self):
        return self.points
    
    def draw(self):
        #Draw data.
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
        self.subplot.hist(self.points, self.bins, 
                          facecolor=[0.93,0.27,0.58], 
                          edgecolor='none',
                          alpha=0.75)
        self.subplot.set_xlabel(self.x_label)
        self.canvas.draw()
        

class Histogram(wx.Frame):
    '''
    A very basic histogram plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600)):
        wx.Frame.__init__(self, parent, -1, size=size, title='Histogram plot')
        
        points = [1,2,2,3,3,3,4,4,4,4,5,5,5,5,5]
        figpanel = HistogramPanel(self, points)
        configpanel = DataSourcePanel(self, figpanel)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
        sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        



def LoadProperties():
    import os
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])  # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        print 'Histogramplot requires a properties file.  Exiting.'
        sys.exit()

            
if __name__ == "__main__":
    app = wx.PySimpleApp()
        
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        LoadProperties()

    import MulticlassSQL
    MulticlassSQL.CreateFilterTables()
    
    histogram = Histogram(None)
    histogram.Show()
    
    app.MainLoop()
