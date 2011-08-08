from dbconnect import DBConnect, UniqueImageClause, image_key_columns, object_key_columns
from icons import lasso_tool
import sqltools as sql
from multiclasssql import filter_table_prefix
from properties import Properties
import guiutils as ui
from wx.combo import OwnerDrawnComboBox as ComboBox
import imagetools
import logging
import numpy as np
import os
import sys
import re
import wx
from gating import GatingHelper
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from cpatool import CPATool

p = Properties.getInstance()
db = DBConnect.getInstance()

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

        self.table_choice = ui.TableComboBox(self, -1, style=wx.CB_READONLY)
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.bins_input = wx.SpinCtrl(self, -1, '100')
        self.bins_input.SetRange(1,400)
        self.x_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE, LOG2_SCALE], style=wx.CB_READONLY)
        self.x_scale_choice.Select(0)
        self.y_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.y_scale_choice.Select(0)
        self.filter_choice = ui.FilterComboBox(self, style=wx.CB_READONLY)
        self.gate_choice = ui.GateComboBox(self, style=wx.CB_READONLY)
        self.gate_choice.set_gatable_columns([self.x_column])
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
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "gate:"), 0, wx.TOP, 4)
        sz.AddSpacer((2,-1))
        sz.Add(self.gate_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
                
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_COMBOBOX(self.table_choice, -1, self.on_table_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.update_figpanel)
        self.gate_choice.addobserver(self.on_gate_selected)
        
        self.SetSizer(sizer)
        self.Show(1)
        
    @property
    def x_column(self):
        return sql.Column(self.table_choice.GetStringSelection(), 
                          self.x_choice.GetStringSelection())
    @property
    def filter(self):
        return self.filter_choice.get_filter_or_none()

    def on_table_selected(self, evt):
        table = self.table_choice.Value
        if table == ui.TableComboBox.OTHER_TABLE:
            t = ui.get_other_table_from_user(self)
            if t is not None:
                self.table_choice.Items = self.table_choice.Items[:-1] + [t] + self.table_choice.Items[-1:]
                self.table_choice.Select(self.table_choice.Items.index(t))
            else:
                self.table_choice.Select(0)
                return
        self.update_column_fields()

    def on_gate_selected(self, gate_name):
        self.update_gate_helper()
            
    def update_gate_helper(self):
        gate_name = self.gate_choice.get_gatename_or_none()
        if gate_name:
            self.figpanel.gate_helper.set_displayed_gate(p.gates[gate_name], self.x_column, None)
        else:
            self.figpanel.gate_helper.disable()        

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
        
    def _plotting_per_object_data(self):
        return (p.object_table and
                p.object_table in [self.x_column.table, self.x_column.table]
                or (self.x_column.table != p.image_table and db.adjacent(p.object_table, self.x_column.table))
                )
        
    def update_figpanel(self, evt=None):
        self.gate_choice.set_gatable_columns([self.x_column])
        points = self._load_points()
        bins = int(self.bins_input.GetValue())
        self.figpanel.set_x_label(self.x_column.col)
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())
        self.figpanel.setpoints(points, bins)
        self.update_gate_helper()
        self.figpanel.draw()
        
    def _load_points(self):
        q = sql.QueryBuilder()
        select = [self.x_column]
        q.set_select_clause(select)
        if self.filter is not None:
            q.add_filter(self.filter)
            
        return np.array(db.execute(str(q))).T[0]

    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        returns a dictionary mapping setting names to values encoded as strings
        '''
        d = {'table'   : self.table_choice.GetStringSelection(),
             'x-axis'  : self.x_choice.GetStringSelection(),
             'bins'    : self.bins_input.GetValue(),
             'x-scale' : self.x_scale_choice.GetStringSelection(),
             'y-scale' : self.y_scale_choice.GetStringSelection(),
             'filter'  : self.filter_choice.GetStringSelection(),
             'x-lim'   : self.figpanel.subplot.get_xlim(),
             'y-lim'   : self.figpanel.subplot.get_ylim(),
             }
        if self.gate_choice.get_gatename_or_none():
            d['gate'] = self.gate_choice.GetStringSelection()
        return d
    
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
        if 'gate' in settings:
            self.gate_choice.SetStringSelection(settings['gate'])
            self.figpanel.gate_helper.set_displayed_gate(
                p.gates[settings['gate']], self.x_column, None)
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
        self.subplot = self.figure.add_subplot(111)
        self.gate_helper = GatingHelper(self.subplot, self)
        
        self.navtoolbar = NavigationToolbar(self.canvas)
        self.navtoolbar.Realize()
            
        self.x_label = ''
        self.log_y = False
        self.x_scale = LINEAR_SCALE
        self.setpoints(points, bins)
        
        self.canvas.mpl_connect('button_release_event', self.on_release)
                
    def setpoints(self, points, bins):
        ''' Updates the data to be plotted and redraws the plot.
        points - array of samples
        bins - number of bins to aggregate points in
        '''
        points = np.array(points).astype('f')
        self.bins = bins
        x_label = self.x_label

        self.subplot.clear()
        # log xform the data, ignoring non-positives
        # XXX: This will not work for selection since the data is changed
        if self.x_scale in [LOG_SCALE, LOG2_SCALE]:
            if self.x_scale == LOG_SCALE:
                points = np.log(points[points>0])
                x_label = 'Log(%s)'%(self.x_label)
            elif self.x_scale == LOG2_SCALE:
                points = np.log2(points[points>0])
                x_label = 'Log2(%s)'%(self.x_label)
            ignored = len(points[points<=0])
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
        self.reset_toolbar()
    
    def set_x_label(self, label):
        self.x_label = label
        
    def set_x_scale(self, scale):
        '''scale -- LINEAR_SCALE, LOG_SCALE, or LOG2_SCALE'''
        self.x_scale = scale
        
    def set_y_scale(self, scale):
        '''scale -- LINEAR_SCALE or LOG_SCALE'''
        if scale == LINEAR_SCALE:
            self.log_y = False
        elif scale == LOG_SCALE:
            self.log_y = True
        else:
            raise 'Unsupported y-axis scale.' 
    
    def get_toolbar(self):
        return self.navtoolbar

    def reset_toolbar(self):
        '''Clears the navigation toolbar history. Called after setpoints.'''
        # Cheat since there is no way reset
        if self.navtoolbar:
            self.navtoolbar._views.clear()
            self.navtoolbar._positions.clear()
            self.navtoolbar.push_current()
            
    def set_configpanel(self,configpanel):
        '''Allow access of the control panel from the plotting panel'''
        self.configpanel = configpanel
        
    def on_release(self, evt):
        '''click handler'''
        if evt.button == 3: # right click
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
            
    def show_popup_menu(self, (x,y), data):
        '''Show context sensitive popup menu.'''
        self.popup_menu_filters = {}
        popup = wx.Menu()
        loadimages_table_item = popup.Append(-1, 'Create gated table for CellProfiler LoadImages')
        selected_gate = self.configpanel.gate_choice.get_gatename_or_none()
        selected_gates = []
        if selected_gate:
            selected_gates = [selected_gate]
        self.Bind(wx.EVT_MENU, 
                  lambda(e):ui.prompt_user_to_create_loadimages_table(self, selected_gates), 
                  loadimages_table_item)
        
        show_images_in_gate_item = popup.Append(-1, 'Show images in gate')
        show_images_in_gate_item.Enable(selected_gate is not None)
        self.Bind(wx.EVT_MENU, self.show_images_from_gate, show_images_in_gate_item)
        if p.object_table:
            show_objects_in_gate_item = popup.Append(-1, 'Show %s in gate'%(p.object_name[1]))
            show_objects_in_gate_item.Enable(selected_gate is not None)
            self.Bind(wx.EVT_MENU, self.show_objects_from_gate, show_objects_in_gate_item)

        self.PopupMenu(popup, (x,y))
        
    def show_objects_from_gate(self, evt=None):
        '''Callback for "Show objects in gate" popup item.'''
        gatename = self.configpanel.gate_choice.get_gatename_or_none()
        if gatename:
            ui.show_objects_from_gate(gatename)
        
    def show_images_from_gate(self, evt=None):
        '''Callback for "Show images in gate" popup item.'''
        gatename = self.configpanel.gate_choice.get_gatename_or_none()
        if gatename:
            ui.show_images_from_gate(gatename)




class Histogram(wx.Frame, CPATool):
    '''
    A very basic histogram plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Histogram', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        self.SetBackgroundColour(wx.NullColor)
        points = []
        figpanel = HistogramPanel(self, points)
        configpanel = DataSourcePanel(self, figpanel)
        figpanel.set_configpanel(configpanel)
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
        self.fig = figpanel
        
        
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

    # Kill the Java VM
    try:
        from bioformats import jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
