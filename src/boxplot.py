from dbconnect import DBConnect, UniqueImageClause, image_key_columns
from multiclasssql import filter_table_prefix
from properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import imagetools
import logging
import numpy as np
import os
import sys
import re
import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

from cpatool import CPATool

p = Properties.getInstance()
db = DBConnect.getInstance()

NO_FILTER = 'No filter'
CREATE_NEW_FILTER = '*create new filter*'
ID_EXIT = wx.NewId()
SELECT_MULTIPLE = '<MULTIPLE SELECTED>'

class DataSourcePanel(wx.Panel):
    '''
    A panel with controls for selecting the source data for a boxplot 
    '''
    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        # the panel to draw charts on
        self.figpanel = figpanel
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.x_columns = [] # column names to plot if selecting multiple columns

        tables = [p.image_table, p.object_table] #db.GetTableNames()
        self.table_choice = ComboBox(self, -1, choices=tables, style=wx.CB_READONLY)
        if p.image_table in tables:
            self.table_choice.Select(tables.index(p.image_table))
        else:
            logging.error('Could not find your image table "%s" among the database tables found: %s'%(p.image_table, tables))
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.x_multiple = wx.Button(self, -1, 'select multiple', size=(150,-1))
        
        self.filter_choice = ComboBox(self, -1, choices=[NO_FILTER]+p._filters_ordered+[CREATE_NEW_FILTER], style=wx.CB_READONLY)
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
        sz.Add(self.x_multiple, 0, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_BUTTON(self.x_multiple, -1, self.on_select_multiple)
        wx.EVT_COMBOBOX(self.table_choice, -1, self.on_table_selected)
        wx.EVT_COMBOBOX(self.filter_choice, -1, self.on_filter_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.update_figpanel)   
        
        self.SetSizer(sizer)
        self.Show(1)

    def on_select_multiple(self, evt):
        tablename = self.table_choice.GetStringSelection()
        column_names = self.get_numeric_columns_from_table(tablename)
        dlg = wx.MultiChoiceDialog(self, 
                                   'Select the columns you would like to plot',
                                   'Select Columns', column_names)
        dlg.SetSelections([column_names.index(v) for v in self.x_columns])
        if (dlg.ShowModal() == wx.ID_OK):
            self.x_choice.SetValue(SELECT_MULTIPLE)
            self.x_columns = [column_names[i] for i in dlg.GetSelections()]
            print self.x_columns
        
    def on_table_selected(self, evt):
        self.update_column_fields()
    
    def on_filter_selected(self, evt):
        filter = self.filter_choice.GetStringSelection()
        if filter == CREATE_NEW_FILTER:
            from ColumnFilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(600,150))
            if cff.ShowModal()==wx.OK:
                fltr = str(cff.get_filter())
                fname = str(cff.get_filter_name())
                p._filters_ordered += [fname]
                p._filters[fname] = fltr
                items = self.filter_choice.GetItems()
                self.filter_choice.SetItems(items[:-1]+[fname]+items[-1:])
                self.filter_choice.SetSelection(len(items)-1)
                from multiclasssql import CreateFilterTable
                logging.info('Creating filter table...')
                CreateFilterTable(fname)
                logging.info('Done creating filter.')
            cff.Destroy()
            
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
        
    def update_figpanel(self, evt=None):    
        filter = self.filter_choice.GetStringSelection()
        if self.x_choice.Value == SELECT_MULTIPLE:
            cols = self.x_columns
        else:
            cols = [self.x_choice.GetStringSelection()]
        points = []
        for col in cols:
            pts = self.loadpoints(self.table_choice.GetStringSelection(),
                                  col, filter)
            pts = np.array(pts[0]).T[0]
            points += [pts]
            
        if self.x_choice.Value == SELECT_MULTIPLE:
            self.figpanel.set_x_labels(self.x_columns)
        else:
            self.figpanel.set_x_labels([self.x_choice.GetStringSelection()])
        self.figpanel.setpoints(points)
        self.figpanel.draw()
        
    def loadpoints(self, tablename, xpoints, filter=NO_FILTER):
        ''' Returns a list of rows containing:
        (TableNumber), ImageNumber, X measurement
        '''
        fields = '%s.%s'%(tablename, xpoints)
        tables = tablename
        where_clause = ''
        if filter != NO_FILTER:
            # If a filter is applied we must compute a WHERE clause and add the 
            # filter table to the FROM clause
            tables += ', %s'%(filter_table_prefix+filter) 
            filter_clause = ' AND '.join(['%s.%s=%s.%s'%(tablename, id, filter_table_prefix+filter, id) 
                                          for id in db.GetLinkingColumnsForTable(tablename)])
            where_clause = 'WHERE %s'%(filter_clause)
        return [db.execute('SELECT %s FROM %s %s'%(fields, tables, where_clause))]

    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        
        returns a dictionary mapping setting names to values encoded as strings
        '''
        return {'table' : self.table_choice.GetStringSelection(),
                'x-axis' : self.x_choice.GetStringSelection(),
                'filter' : self.filter_choice.GetStringSelection()
                }
    
    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
        if 'table' in settings:
            self.table_choice.SetStringSelection(settings['table'])
            self.update_column_fields()
        if 'x-axis' in settings:
            self.x_choice.SetStringSelection(settings['x-axis'])
        if 'filter' in settings:
            self.filter_choice.SetStringSelection(settings['filter'])
        self.update_figpanel()
        

class BoxPlotPanel(FigureCanvasWxAgg):
    def __init__(self, parent, points, bins=100, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        
        self.navtoolbar = None
        self.x_labels = ['']
        self.setpoints(points)
        
    def setpoints(self, points):
        ''' Updates the data to be plotted and redraws the plot.
        points - array of samples
        '''
        self.points = [np.array(pts).astype('f')[~ np.isnan(pts)] 
                       for pts in points]        
        points = self.points
        
        x_labels = self.x_labels
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
        # nothing to plot?
        if len(points)==0:
            logging.warn('No data to plot.')
            return
        
        self.subplot.boxplot(points)
        if len(points) > 1:
            self.figure.autofmt_xdate()
        self.subplot.set_xticklabels(x_labels)
        
        self.reset_toolbar()
    
    def set_x_labels(self, labels):
        self.x_labels = labels
        
    def getpointslists(self):
        return self.points
    
    def get_toolbar(self):
        if not self.navtoolbar:
            self.navtoolbar = NavigationToolbar(self.canvas)
            self.navtoolbar.DeleteToolByPos(6)
        return self.navtoolbar

    def reset_toolbar(self):
        # Cheat since there is no way reset
        if self.navtoolbar:
            self.navtoolbar._views.clear()
            self.navtoolbar._positions.clear()
            self.navtoolbar.push_current()


class BoxPlot(wx.Frame, CPATool):
    '''
    A very basic boxplot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='BoxPlot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        points = []
        figpanel = BoxPlotPanel(self, points)
        configpanel = DataSourcePanel(self, figpanel)
        self.SetToolBar(figpanel.get_toolbar())
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
        sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        
        #
        # Forward save and load settings functionality to the configpanel
        #
        self.save_settings = configpanel.save_settings
        self.load_settings = configpanel.load_settings

                    
if __name__ == "__main__":
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            print 'BoxPlot requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    import multiclasssql
    multiclasssql.CreateFilterTables()
    
    boxplot = BoxPlot(None)
    boxplot.Show()
    
    app.MainLoop()
