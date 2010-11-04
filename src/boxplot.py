from dbconnect import DBConnect, UniqueImageClause, image_key_columns
from multiclasssql import filter_table_prefix
from properties import Properties
import datamodel
from wx.combo import OwnerDrawnComboBox as ComboBox
import sqltools as sql
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
NO_GROUP = "Whole column"
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

        tables = [p.image_table] #db.GetTableNames()
        if p.object_table:
            tables += [p.object_table]
        self.table_choice = ComboBox(self, -1, choices=tables, style=wx.CB_READONLY)
        if p.image_table in tables:
            self.table_choice.Select(tables.index(p.image_table))
        else:
            logging.error('Could not find your image table "%s" among the database tables found: %s'%(p.image_table, tables))
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.x_multiple = wx.Button(self, -1, 'select multiple')
        self.group_choice = ComboBox(self, -1, choices=[NO_GROUP]+p._groups_ordered, style=wx.CB_READONLY)
        self.group_choice.Select(0)
        self.filter_choice = ComboBox(self, -1, choices=[NO_FILTER]+p._filters_ordered+[CREATE_NEW_FILTER], style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_column_fields()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "table:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.table_choice, 1, wx.EXPAND)
        sz.AddSpacer((3,-1))
        sz.Add(wx.StaticText(self, -1, "measurement:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_multiple, 0, wx.EXPAND|wx.TOP, 2)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,3))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "group x-axis by:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.group_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,3))

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,3))
        
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_BUTTON(self.x_multiple, -1, self.on_select_multiple)
        wx.EVT_COMBOBOX(self.table_choice, -1, self.on_table_selected)
        wx.EVT_COMBOBOX(self.x_choice, -1, self.on_column_selected)
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
            self.group_choice.Disable()
            self.group_choice.SetStringSelection(NO_GROUP)
        
    def on_table_selected(self, evt):
        self.group_choice.Enable()
        self.x_columns = []
        self.update_column_fields()
        
    def on_column_selected(self, evt):
        self.group_choice.Enable()        
    
    def on_filter_selected(self, evt):
        filter = self.filter_choice.Value
        if filter == CREATE_NEW_FILTER:
            from columnfilter import ColumnFilterDialog
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
            else:
                self.filter_choice.SetSelection(0)
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
        table = self.table_choice.Value
        filter = self.filter_choice.Value
        grouping = self.group_choice.Value
        if self.x_choice.Value == SELECT_MULTIPLE:
            points_dict = {}
            for col in self.x_columns:
                pts = self.loadpoints(table, col, filter, NO_GROUP)
                for k in pts.keys(): assert k not in points_dict.keys()
                points_dict.update(pts)
        else:
            col = self.x_choice.Value
            points_dict = self.loadpoints(table, col, filter, grouping)
        
        # Check if the user is creating a plethora of plots by accident
        if 100 >= len(points_dict) > 25:
            res = wx.MessageDialog(self, 'Are you sure you want to show %s box '
                                   'plots on one axis?'%(len(points_dict)), 
                                   'Warning', style=wx.YES_NO|wx.NO_DEFAULT
                                   ).ShowModal()
            if res != wx.ID_YES:
                return
        elif len(points_dict) > 100:
            wx.MessageBox('Sorry, boxplot can not show more than 100 plots on\n'
                          'a single axis. Your current settings would plot %d.\n'
                          'Try using a filter to narrow your query.'
                          %(len(points_dict)), 'Too many groups to plot')
            return

        self.figpanel.setpoints(points_dict)
        if self.group_choice.Value != NO_GROUP:
            self.figpanel.set_x_axis_label(grouping)
            self.figpanel.set_y_axis_label(self.x_choice.Value)
        self.figpanel.draw()
        
    def loadpoints(self, tablename, col, filter=NO_FILTER, grouping=NO_GROUP):
        '''
        Returns a dict mapping x label values to lists of values from col
        '''
        
        q = sql.QueryBuilder()
        columns = [(tablename, col)]
        if grouping != NO_GROUP:
            dm = datamodel.DataModel.getInstance()
            group_cols = dm.GetGroupColumnNames(grouping, include_table_name=True)
            columns += [col.split('.') for col in group_cols]
        q.set_columns(columns)
        if filter != NO_FILTER:
            #
            # This is a bit annoying... We need to parse the filter query and
            # 1) mash the tables into the query builder 
            # 2) plop the where clause at the end of the resultant query
            #
            fq = p._filters[filter]
            from_idx = re.search('\sFROM\s', fq.upper()).start()
            where_idx = re.search('\sWHERE\s', fq.upper()).start()
            f_where = fq[where_idx+7:]
            f_from = fq[from_idx+6 : where_idx]
            f_tables = [t.strip() for t in f_from.split(',')]
            for t in f_tables:
                if ' ' in t:
                    res = wx.MessageBox('Unable to parse properties filter "%s".'%(filter), 'Error')
            q.add_table_dependencies(f_tables)
            if q.get_where_clause():
                q = str(q) + ' AND ' + f_where
            else:
                q = str(q) + ' WHERE ' + f_where        

        res = db.execute(str(q))
        
        points_dict = {}
        if self.group_choice.Value != NO_GROUP:
            for row in res:
                groupkey = row[1:]
                if points_dict.get(groupkey, None) is None:
                    points_dict[groupkey] = [row[0]]
                else:
                    points_dict[groupkey] += [row[0]]
        else:
            points_dict = {col : [r[0] for r in res]}
        return points_dict

    def save_settings(self):
        '''
        Called when saving a workspace to file.
        returns a dictionary mapping setting names to values encoded as strings
        '''
        if self.x_choice.Value == SELECT_MULTIPLE:
            cols = self.x_columns
        else:
            cols = [self.x_choice.GetStringSelection()]
        return {'table'  : self.table_choice.Value,
                'x-axis' : ','.join(cols),
                'filter' : self.filter_choice.Value,
                'x-lim'  : self.figpanel.subplot.get_xlim(),
                'y-lim'  : self.figpanel.subplot.get_ylim(),
##                'grouping': self.group_choice.Value,
##                'version': '1',
                }
    
    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
##        if 'version' not in settings:
##            settings['grouping'] = NO_GROUP
##            settings['version'] = '1'
        if 'table' in settings:
            self.table_choice.SetStringSelection(settings['table'])
            self.update_column_fields()
        if 'x-axis' in settings:
            cols = map(str.strip, settings['x-axis'].split(','))
            if len(cols) == 1:
                self.x_choice.SetStringSelection(cols[0])
            else:
                self.x_choice.SetValue(SELECT_MULTIPLE)
                self.x_columns = cols
        if 'filter' in settings:
            self.filter_choice.SetStringSelection(settings['filter'])
        self.update_figpanel()
        if 'x-lim' in settings:
            self.figpanel.subplot.set_xlim(eval(settings['x-lim']))
        if 'y-lim' in settings:
            self.figpanel.subplot.set_ylim(eval(settings['y-lim']))
        self.figpanel.draw()


class BoxPlotPanel(FigureCanvasWxAgg):
    def __init__(self, parent, points, **kwargs):
        '''
        points -- a dictionary mapping x axis values to lists of values to plot
        '''
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        
        self.navtoolbar = None
        self.setpoints(points)
        
    def setpoints(self, points):
        '''
        Updates the data to be plotted and redraws the plot.
        points - list of array samples, where each sample will be plotted as a 
                 separate box plot against the same y axis
        '''
        self.xlabels = []
        self.points = []
        for label, values in sorted(points.items()):
            self.xlabels += [label]
            self.points += [np.array(values).astype('f')[~ np.isnan(values)]]
        
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
        # nothing to plot?
        if len(self.points)==0:
            logging.warn('No data to plot.')
            return
        self.subplot.boxplot(self.points)
        if len(self.points) > 1:
            self.figure.autofmt_xdate()
        self.subplot.set_xticklabels(self.xlabels)
        self.reset_toolbar()
        
    def set_x_axis_label(self, label):
        self.subplot.set_xlabel(label)
    
    def set_y_axis_label(self, label):
        self.subplot.set_ylabel(label)
    
    def get_point_lists(self):
        return self.points
    
    def get_xlabels(self):
        return self.xlabels
    
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
        points = {}
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

    if not p.show_load_dialog():
        print 'BoxPlot requires a properties file.  Exiting.'
        # necessary in case other modal dialogs are up
        wx.GetApp().Exit()
        sys.exit()
        afraser
    boxplot = BoxPlot(None)
    boxplot.Show()
    
    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import cellprofiler.utilities.jutil as jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
