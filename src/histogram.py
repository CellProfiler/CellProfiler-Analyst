from dbconnect import DBConnect, UniqueImageClause, image_key_columns
from icons import lasso_tool
import sqltools as sql
from multiclasssql import filter_table_prefix
from properties import Properties
from guiutils import TableComboBox, get_other_table_from_user
from wx.combo import OwnerDrawnComboBox as ComboBox
import imagetools
import logging
import numpy as np
import os
import sys
import re
import wx
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

from cpatool import CPATool

p = Properties.getInstance()
db = DBConnect.getInstance()

NO_FILTER = 'No filter'
CREATE_NEW_FILTER = '*create new filter*'
ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LOG2_SCALE   = 'log2'
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

        self.table_choice = TableComboBox(self, -1, style=wx.CB_READONLY)
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.bins_input = wx.SpinCtrl(self, -1, '100')
        self.bins_input.SetRange(1,400)
        self.x_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE, LOG2_SCALE], style=wx.CB_READONLY)
        self.x_scale_choice.Select(0)
        self.y_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.y_scale_choice.Select(0)
        self.filter_choice = ComboBox(self, -1, choices=[NO_FILTER]+p._filters_ordered+[CREATE_NEW_FILTER], style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_column_fields()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer((2,-1))
        sz.Add(self.table_choice, 1, wx.EXPAND)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-scale:"), 0, wx.TOP, 4)
        sz.AddSpacer((2,-1))
        sz.Add(self.x_scale_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "y-scale:"), 0, wx.TOP, 4)
        sz.AddSpacer((2,-1))
        sz.Add(self.y_scale_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "bins:"), 0, wx.TOP, 4)
        sz.AddSpacer((2,-1))
        sz.Add(self.bins_input)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"), 0, wx.TOP, 4)
        sz.AddSpacer((2,-1))
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
        
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_COMBOBOX(self.table_choice, -1, self.on_table_selected)
        wx.EVT_COMBOBOX(self.filter_choice, -1, self.on_filter_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.update_figpanel)   
        
        self.SetSizer(sizer)
        self.Show(1)

    def on_table_selected(self, evt):
        table = self.table_choice.Value
        if table == TableComboBox.OTHER_TABLE:
            t = get_other_table_from_user(self)
            if t is not None:
                self.table_choice.Items = self.table_choice.Items[:-1] + [t] + self.table_choice.Items[-1:]
                self.table_choice.Select(self.table_choice.Items.index(t))
            else:
                self.table_choice.Select(0)
                return
        self.update_column_fields()
        
    def on_filter_selected(self, evt):
        filter = self.filter_choice.GetStringSelection()
        if filter == CREATE_NEW_FILTER:
            from columnfilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(600,150))
            if cff.ShowModal()==wx.OK:
                fltr = cff.get_filter()
                fname = str(cff.get_filter_name())
                p._filters_ordered += [fname]
                p._filters[fname] = fltr
                items = self.filter_choice.GetItems()
                self.filter_choice.SetItems(items[:-1]+[fname]+items[-1:])
                self.filter_choice.SetSelection(len(items)-1)
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
        filter = self.filter_choice.GetStringSelection()
        points = self.loadpoints(self.table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 filter)
        points = np.array(points[0]).T[0]
        bins = int(self.bins_input.GetValue())
        self.figpanel.set_x_label(self.x_choice.GetStringSelection())
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())
        self.figpanel.setpoints(points, bins)
        self.figpanel.draw()
        
    def loadpoints(self, tablename, xpoints, filter=NO_FILTER):
        ''' Returns a list of rows containing:
        (TableNumber), ImageNumber, X measurement
        '''
        q = sql.QueryBuilder()
        q.set_select_clause([sql.Column(tablename, xpoints)])
        if filter != NO_FILTER:
            q.add_filter(p._filters[filter])
        return [db.execute(str(q))]

    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        
        returns a dictionary mapping setting names to values encoded as strings
        '''
        return {'table' : self.table_choice.GetStringSelection(),
                'x-axis' : self.x_choice.GetStringSelection(),
                'bins' : self.bins_input.GetValue(),
                'x-scale' : self.x_scale_choice.GetStringSelection(),
                'y-scale' : self.y_scale_choice.GetStringSelection(),
                'filter' : self.filter_choice.GetStringSelection(),
                'x-lim': self.figpanel.subplot.get_xlim(),
                'y-lim': self.figpanel.subplot.get_ylim(),
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
        if 'bins' in settings:
            self.bins_input.SetValue(int(settings['bins']))
        if 'x-scale' in settings:
            self.x_scale_choice.SetStringSelection(settings['x-scale'])
        if 'y-scale' in settings:
            self.y_scale_choice.SetStringSelection(settings['y-scale'])
        if 'filter' in settings:
            self.filter_choice.SetStringSelection(settings['filter'])
        self.update_figpanel()
        if 'x-lim' in settings:
            self.figpanel.subplot.set_xlim(eval(settings['x-lim']))
        if 'y-lim' in settings:
            self.figpanel.subplot.set_ylim(eval(settings['y-lim']))
        self.figpanel.draw()
        

class HistogramPanel(FigureCanvasWxAgg):
    def __init__(self, parent, points, bins=100, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        
        self.navtoolbar = NavigationToolbar(self.canvas)
        self.navtoolbar.DeleteToolByPos(6)
        #self.span_tool = self.navtoolbar.InsertSimpleTool(5, -1, lasso_tool.ConvertToBitmap(), 
                                                          #shortHelpString='Draw gate', 
                                                          #isToggle=True)
        self.span = None
        self.navtoolbar.Realize()
        #self.navtoolbar.Bind(wx.EVT_TOOL, self.on_span_tool_clicked, self.span_tool)
            
        self.x_label = ''
        self.log_y = False
        self.x_scale = LINEAR_SCALE
        self.setpoints(points, bins)
        
        #self.canvas.mpl_connect('button_press_event', self.on_press)
        #self.canvas.mpl_connect('button_release_event', self.on_release)
        
    #def on_press(self, evt):
        #if self.span_tool.IsToggled():
            #import matplotlib as mpl

            #mpl.lines.Line2D([evt.x, evt.x], [0, 1], transform=self.figure.transFigure, figure=self.figure)

    #def selection_callback(self, xmin, xmax):
        #print xmin, xmax
        
    def setpoints(self, points, bins):
        ''' Updates the data to be plotted and redraws the plot.
        points - array of samples
        bins - number of bins to aggregate points in
        '''
        self.points = np.array(points).astype('f')
        self.bins = bins
        
        points = self.points
        x_label = self.x_label
        #Draw data.
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
            #self.span = SpanSelector(self.subplot, self.selection_callback, 
                                     #'horizontal', useblit=True,
                                     #rectprops=dict(alpha=0.3, facecolor='red'))

        self.subplot.clear()
        # log xform the data, ignoring non-positives
        # XXX: This will not work for selection since the data is changed
        if self.x_scale in [LOG_SCALE, LOG2_SCALE]:
            if self.x_scale == LOG_SCALE:
                points = np.log(self.points[self.points>0])
                x_label = 'Log(%s)'%(self.x_label)
            elif self.x_scale == LOG2_SCALE:
                points = np.log2(self.points[self.points>0])
                x_label = 'Log2(%s)'%(self.x_label)
            ignored = len(self.points[self.points<=0])
            if ignored>0:
                logging.warn('Histogram ignored %s negative value%s.'%
                             (ignored, (ignored!=1 and's' or '')))

        # hist apparently doesn't like nans, need to preen them out first
        points = points[~ np.isnan(points)]
        
        # nothing to plot?
        if len(points)==0:
            logging.warn('No data to plot.')
            return
        
        self.subplot.hist(points, self.bins, 
                          facecolor=[0.0,0.62,1.0], 
                          edgecolor='none',
                          log=self.log_y,
                          alpha=0.75)
        self.subplot.set_xlabel(x_label)
        #self.span.visible = self.span_tool.IsToggled()

        self.reset_toolbar()
    
    def set_x_label(self, label):
        self.x_label = label
        
    def set_x_scale(self, scale):
        self.x_scale = scale
        
    def set_y_scale(self, scale):
        if scale == LINEAR_SCALE:
            self.log_y = False
        elif scale == LOG_SCALE:
            self.log_y = True
        else:
            raise 'Unsupported y-axis scale.' 

    def getpointslists(self):
        return self.points
    
    def get_toolbar(self):
        return self.navtoolbar

    def reset_toolbar(self):
        # Cheat since there is no way reset
        if self.navtoolbar:
            self.navtoolbar._views.clear()
            self.navtoolbar._positions.clear()
            self.navtoolbar.push_current()
            
    #def on_span_tool_clicked(self, evt):
        #if self.span:
            #self.span.visible = evt.IsChecked()


class Histogram(wx.Frame, CPATool):
    '''
    A very basic histogram plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Histogram', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        points = []
        figpanel = HistogramPanel(self, points)
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
            print 'Histogram requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    histogram = Histogram(None)
    histogram.Show()
    
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
