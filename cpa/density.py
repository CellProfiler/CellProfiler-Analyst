from cpatool import CPATool
from dbconnect import DBConnect, UniqueImageClause, image_key_columns, object_key_columns
import sqltools as sql
from multiclasssql import filter_table_prefix
from properties import Properties
import guiutils as ui 
from gating import GatingHelper
from wx.combo import OwnerDrawnComboBox as ComboBox
import imagetools
import logging
import numpy as np
import os
import sys
import re
import wx
import matplotlib.cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

p = Properties.getInstance()
db = DBConnect.getInstance()

ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LINEAR_SCALE = 'linear'


class DataSourcePanel(wx.Panel):
    '''
    A panel with controls for selecting the source data for a densityplot 
    '''
    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        # the panel to draw charts on
        self.figpanel = figpanel
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.x_table_choice = ui.TableComboBox(self, -1, style=wx.CB_READONLY)
        self.y_table_choice = ui.TableComboBox(self, -1, style=wx.CB_READONLY)
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.y_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.gridsize_input = wx.TextCtrl(self, -1, '50')
        maps = [m for m in matplotlib.cm.datad.keys() if not m.endswith("_r")]
        maps.sort()
        self.colormap_choice = ComboBox(self, -1, choices=maps, style=wx.CB_READONLY)
        self.colormap_choice.SetSelection(maps.index('jet'))
        self.color_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.color_scale_choice.Select(0)
        self.x_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.x_scale_choice.Select(0)
        self.y_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.y_scale_choice.Select(0)
        self.filter_choice = ui.FilterComboBox(self, style=wx.CB_READONLY)
        self.gate_choice = ui.GateComboBox(self, style=wx.CB_READONLY)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_x_choices()
        self.update_y_choices()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_table_choice, 1, wx.EXPAND)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "scale:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "y-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.y_table_choice, 1, wx.EXPAND)
        sz.AddSpacer((3,-1))
        sz.Add(self.y_choice, 2, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "scale:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.y_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)        
        sz.Add(wx.StaticText(self, -1, "grid size:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.gridsize_input, 1, wx.TOP, 3)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, label='color map:'), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.colormap_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, label='color scale:'), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.color_scale_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "gate:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.gate_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_COMBOBOX(self.x_table_choice, -1, self.on_x_table_selected)
        wx.EVT_COMBOBOX(self.y_table_choice, -1, self.on_y_table_selected)
        self.gate_choice.addobserver(self.on_gate_selected)
        wx.EVT_COMBOBOX(self.colormap_choice, -1, self.on_cmap_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.update_figpanel)
        
        self.SetSizer(sizer)
        self.Show(1)

    @property
    def x_column(self):
        return sql.Column(self.x_table_choice.GetStringSelection(), 
                          self.x_choice.GetStringSelection())
    @property
    def y_column(self):
        return sql.Column(self.y_table_choice.GetStringSelection(), 
                          self.y_choice.GetStringSelection())
    @property
    def filter(self):
        return self.filter_choice.get_filter_or_none()
        
    def on_x_table_selected(self, evt):
        table = self.x_table_choice.Value
        if table == ui.TableComboBox.OTHER_TABLE:
            t = ui.get_other_table_from_user(self)
            if t is not None:
                self.x_table_choice.Items = self.x_table_choice.Items[:-1] + [t] + self.x_table_choice.Items[-1:]
                self.x_table_choice.Select(self.x_table_choice.Items.index(t))
                sel = self.y_table_choice.GetSelection()
                self.y_table_choice.Items = self.y_table_choice.Items[:-1] + [t] + self.y_table_choice.Items[-1:]
                self.y_table_choice.SetSelection(sel)
            else:
                self.x_table_choice.Select(0)
                return
        self.update_x_choices()
        
    def on_y_table_selected(self, evt):
        table = self.y_table_choice.Value
        if table == ui.TableComboBox.OTHER_TABLE:
            t = ui.get_other_table_from_user(self)
            if t is not None:
                self.y_table_choice.Items = self.y_table_choice.Items[:-1] + [t] + self.y_table_choice.Items[-1:]
                self.y_table_choice.Select(self.y_table_choice.Items.index(t))
                sel = self.x_table_choice.GetSelection()
                self.x_table_choice.Items = self.x_table_choice.Items[:-1] + [t] + self.x_table_choice.Items[-1:]
                self.x_table_choice.SetSelection(sel)
            else:
                self.y_table_choice.Select(0)
                return
        self.update_y_choices()
            
    def on_gate_selected(self, gate_name):
        self.update_gate_helper()
        
    def update_gate_helper(self):
        gate_name = self.gate_choice.get_gatename_or_none()
        if gate_name:
            self.figpanel.gate_helper.set_displayed_gate(p.gates[gate_name], self.x_column, self.y_column)
        else:
            self.figpanel.gate_helper.disable()

    def on_cmap_selected(self, evt):
        self.figpanel.set_colormap(self.colormap_choice.GetStringSelection())
        
    def update_x_choices(self):
        tablename = self.x_table_choice.Value
        fieldnames = db.GetColumnNames(tablename)#get_numeric_columns_from_table(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)
            
    def update_y_choices(self):
        tablename = self.y_table_choice.Value
        fieldnames = db.GetColumnNames(tablename)#get_numeric_columns_from_table(tablename)
        self.y_choice.Clear()
        self.y_choice.AppendItems(fieldnames)
        self.y_choice.SetSelection(0)

    def get_numeric_columns_from_table(self, table):
        ''' Fetches names of numeric columns for the given table. '''
        measurements = db.GetColumnNames(table)
        types = db.GetColumnTypes(table)
        return [m for m,t in zip(measurements, types) if t in [float, int, long]]
        
    def _plotting_per_object_data(self):
        return (p.object_table and
                p.object_table in [self.x_column.table, self.y_column.table]
                or (self.x_column.table != p.image_table and db.adjacent(p.object_table, self.x_column.table))
                or (self.y_column.table != p.image_table and db.adjacent(p.object_table, self.y_column.table))
                )
        
    def update_figpanel(self, evt=None):
        self.gate_choice.set_gatable_columns([self.x_column, self.y_column])
        points = self._load_points()
        self.figpanel.setgridsize(int(self.gridsize_input.GetValue()))
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())
        self.figpanel.set_color_scale(self.color_scale_choice.GetStringSelection())
        self.figpanel.set_x_label(self.x_column.col)
        self.figpanel.set_y_label(self.y_column.col)
        self.figpanel.set_colormap(self.colormap_choice.GetStringSelection())
        self.figpanel.setpointslists(points)
        self.figpanel.draw()
        self.update_gate_helper()
        
    def _load_points(self):
        q = sql.QueryBuilder()
        select = [self.x_column, self.y_column]
        q.set_select_clause(select)
        if self.filter != None:
            q.add_filter(self.filter)
            
        return db.execute(str(q))
        
    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        returns a dictionary mapping setting names to values encoded as strings
        '''
        d = {'x-table'     : self.x_table_choice.GetStringSelection(),
             'y-table'     : self.y_table_choice.GetStringSelection(),
             'x-axis'      : self.x_choice.GetStringSelection(),
             'y-axis'      : self.y_choice.GetStringSelection(),
             'x-scale'     : self.x_scale_choice.GetStringSelection(),
             'y-scale'     : self.y_scale_choice.GetStringSelection(),
             'grid size'   : self.gridsize_input.GetValue(),
             'colormap'    : self.colormap_choice.GetStringSelection(),
             'color scale' : self.color_scale_choice.GetStringSelection(),
             'filter'      : self.filter_choice.GetStringSelection(),
             'x-lim'       : self.figpanel.subplot.get_xlim(),
             'y-lim'       : self.figpanel.subplot.get_ylim(),
             'version'     : '1',
             }
        if self.gate_choice.get_gatename_or_none():
            d['gate'] = self.gate_choice.GetStringSelection()
        return d
    
    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
        if 'version' not in settings:
            if 'table' in settings:
                settings['x-table'] = settings['table']
                settings['y-table'] = settings['table']
            settings['version'] = '1'
        if 'x-table' in settings:
            self.x_table_choice.SetStringSelection(settings['x-table'])
            self.update_x_choices()
        if 'y-table' in settings:
            self.y_table_choice.SetStringSelection(settings['y-table'])
            self.update_y_choices()
        if 'x-axis' in settings:
            self.x_choice.SetStringSelection(settings['x-axis'])
        if 'y-axis' in settings:
            self.y_choice.SetStringSelection(settings['y-axis'])
        if 'x-scale' in settings:
            self.x_scale_choice.SetStringSelection(settings['x-scale'])
        if 'y-scale' in settings:
            self.y_scale_choice.SetStringSelection(settings['y-scale'])
        if 'grid size' in settings:
            self.gridsize_input.SetValue(settings['grid size'])
        if 'colormap' in settings:
            self.colormap_choice.SetStringSelection(settings['colormap'])
        if 'color scale' in settings:
            self.color_scale_choice.SetStringSelection(settings['color scale'])
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
                p.gates[settings['gate']], self.x_column, self.y_column)
        self.figpanel.draw()

        
class DensityPanel(FigureCanvasWxAgg):
    def __init__(self, parent, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        self.subplot = self.figure.add_subplot(111)
        self.gate_helper = GatingHelper(self.subplot, self)

        self.navtoolbar = None
        self.point_list = []
        self.gridsize = 50
        self.cb = None
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.color_scale = None
        self.x_label = ''
        self.y_label = ''
        self.cmap ='jet'
        
        self.canvas.mpl_connect('button_release_event', self.on_release)
    
    def setpointslists(self, points):
        self.subplot.clear()
        self.point_list = points        
        plot_pts = np.array(points).astype(float)
        
        if self.x_scale == LOG_SCALE:
            plot_pts = plot_pts[(plot_pts[:,0]>0)]
        if self.y_scale == LOG_SCALE:
            plot_pts = plot_pts[(plot_pts[:,1]>0)]
        
        hb = self.subplot.hexbin(plot_pts[:, 0], plot_pts[:, 1], 
                                 gridsize=self.gridsize,
                                 xscale=self.x_scale,
                                 yscale=self.y_scale,
                                 bins=self.color_scale,
                                 cmap=matplotlib.cm.get_cmap(self.cmap))
        
        if self.cb:
            # Remove the existing colorbar and reclaim the space so when we add
            # a colorbar to the new hexbin subplot, it doesn't get indented.
            self.figure.delaxes(self.figure.axes[1])
            self.figure.subplots_adjust(right=0.90)
        self.cb = self.figure.colorbar(hb)
        if self.color_scale==LOG_SCALE:
            self.cb.set_label('log10(N)')
        
        self.subplot.set_xlabel(self.x_label)
        self.subplot.set_ylabel(self.y_label)
        
        xmin = np.nanmin(plot_pts[:,0])
        xmax = np.nanmax(plot_pts[:,0])
        ymin = np.nanmin(plot_pts[:,1])
        ymax = np.nanmax(plot_pts[:,1])

        # Pad all sides
        if self.x_scale==LOG_SCALE:
            xmin = xmin/1.5
            xmax = xmax*1.5
        else:
            xmin = xmin-(xmax-xmin)/20.
            xmax = xmax+(xmax-xmin)/20.
            
        if self.y_scale==LOG_SCALE:
            ymin = ymin/1.5
            ymax = ymax*1.5
        else:
            ymin = ymin-(ymax-ymin)/20.
            ymax = ymax+(ymax-ymin)/20.

        self.subplot.axis([xmin, xmax, ymin, ymax])
    
        self.reset_toolbar()
    
    def getpointslists(self):
        return self.point_list
    
    def setgridsize(self, gridsize):
        self.gridsize = gridsize

    def set_x_scale(self, scale):
        self.x_scale = scale
    
    def set_y_scale(self, scale):
        self.y_scale = scale
        
    def set_color_scale(self, scale):
        if scale==LINEAR_SCALE:
            scale = None
        self.color_scale = scale

    def set_x_label(self, label):
        self.x_label = label
    
    def set_y_label(self, label):
        self.y_label = label
        
    def set_colormap(self, cmap):
        self.cmap = cmap
        self.draw()

    def get_toolbar(self):
        if not self.navtoolbar:
            self.navtoolbar = NavigationToolbar(self.canvas)
        return self.navtoolbar

    def reset_toolbar(self):
        # Cheat since there is no way reset
        if self.navtoolbar:
            self.navtoolbar._views.clear()
            self.navtoolbar._positions.clear()
            self.navtoolbar.push_current()
    
    def set_configpanel(self,configpanel):
        '''Allow access of the control panel from the plotting panel'''
        self.configpanel = configpanel
        
    def on_release(self, evt):
        if evt.button == 3: # right click
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
            
    def show_popup_menu(self, (x,y), data):
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

class Density(wx.Frame, CPATool):
    '''
    A very basic density plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Density Plot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        self.SetBackgroundColour(wx.NullColor)
        figpanel = DensityPanel(self)
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


if __name__ == "__main__":
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            print 'Density plot requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    density = Density(None)
    density.Show()
    
    app.MainLoop()
