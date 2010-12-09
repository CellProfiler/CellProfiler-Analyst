from cpatool import CPATool
from dbconnect import DBConnect, UniqueImageClause, image_key_columns
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
import matplotlib.cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

p = Properties.getInstance()
db = DBConnect.getInstance()

NO_FILTER = 'No filter'
CREATE_NEW_FILTER = '*create new filter*'
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

        self.x_table_choice = TableComboBox(self, -1, style=wx.CB_READONLY)
        self.y_table_choice = TableComboBox(self, -1, style=wx.CB_READONLY)
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
        self.filter_choice = ComboBox(self, -1, choices=[NO_FILTER]+p._filters_ordered+[CREATE_NEW_FILTER], style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_x_choices()
        self.update_y_choices()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_table_choice, 1, wx.EXPAND)
        sz.AddSpacer((3,-1))
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sz.AddSpacer((3,-1))
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
        sz.AddSpacer((3,-1))
        sz.Add(wx.StaticText(self, -1, "scale:"), 0, wx.TOP, 4)
        sz.AddSpacer((3,-1))
        sz.Add(self.y_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)        
        sz.Add(wx.StaticText(self, -1, "grid size:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.gridsize_input, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, label='color map:'))
        sz.AddSpacer((5,-1))
        sz.Add(self.colormap_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, label='color scale:'))
        sz.AddSpacer((5,-1))
        sz.Add(self.color_scale_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_COMBOBOX(self.x_table_choice, -1, self.on_x_table_selected)
        wx.EVT_COMBOBOX(self.y_table_choice, -1, self.on_y_table_selected)
        wx.EVT_COMBOBOX(self.filter_choice, -1, self.on_filter_selected)
        wx.EVT_COMBOBOX(self.colormap_choice, -1, self.on_cmap_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.update_figpanel)
        
        self.SetSizer(sizer)
        self.Show(1)

    def on_x_table_selected(self, evt):
        table = self.x_table_choice.Value
        if table == TableComboBox.OTHER_TABLE:
            t = get_other_table_from_user(self)
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
        if table == TableComboBox.OTHER_TABLE:
            t = get_other_table_from_user(self)
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
        
    def on_filter_selected(self, evt):
        filter = self.filter_choice.GetStringSelection()
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
        
    def update_figpanel(self, evt=None):
        filter = self.filter_choice.GetStringSelection()
        points = self.loadpoints(self.x_table_choice.GetStringSelection(),
                                 self.y_table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 self.y_choice.GetStringSelection(),
                                 filter)
        self.figpanel.setgridsize(int(self.gridsize_input.GetValue()))
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())
        self.figpanel.set_color_scale(self.color_scale_choice.GetStringSelection())
        self.figpanel.set_x_label(self.x_choice.GetStringSelection())
        self.figpanel.set_y_label(self.y_choice.GetStringSelection())
        self.figpanel.set_colormap(self.colormap_choice.GetStringSelection())
        self.figpanel.setpointslists(points)
        self.figpanel.draw()
        
    def loadpoints(self, xtable, ytable, xcol, ycol, filter=NO_FILTER):
        ''' Returns a list of tuples (X measurement, Y measurement)
        '''
        q = sql.QueryBuilder()
        q.set_select_clause([sql.Column(xtable, xcol), 
                             sql.Column(ytable, ycol)])
        if filter != NO_FILTER:
            #
            # This is a bit annoying... We need to parse the filter query and
            # 1) mash the tables into the query builder 
            # 2) plop the where clause at the end of the resultant query
            #
            fq = p._filters[filter]
            f_where = re.search('\sWHERE\s(?P<wc>.*)', fq, re.IGNORECASE).groups()[0]
            f_from = re.search('\sFROM\s(?P<wc>.*)\sWHERE', fq, re.IGNORECASE).groups()[0]
            f_tables = [t.strip() for t in f_from.split(',')]
            for t in f_tables:
                if ' ' in t:
                    wx.MessageBox('Unable to parse properties filter "%s".'%(filter), 'Error')
            q.add_table_dependencies(f_tables)
            if q.get_where_clause():
                q = str(q) + ' AND ' + f_where
            else:
                q = str(q) + ' WHERE ' + f_where
        return db.execute(str(q))
        
    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        
        returns a dictionary mapping setting names to values encoded as strings
        '''
        #TODO: Add axis bounds 
        return {'table' : self.table_choice.GetStringSelection(),
                'x-axis' : self.x_choice.GetStringSelection(),
                'y-axis' : self.y_choice.GetStringSelection(),
                'x-scale' : self.x_scale_choice.GetStringSelection(),
                'y-scale' : self.y_scale_choice.GetStringSelection(),
                'grid size' : self.gridsize_input.GetValue(),
                'colormap' : self.colormap_choice.GetStringSelection(),
                'color scale' : self.color_scale_choice.GetStringSelection(),
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
    
    def setpointslists(self, points):
        self.point_list = points
        
        self.figure.clear()
        self.subplot = self.figure.add_subplot(111)
            
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
            
        #h, xedges, yedges = np.histogram2d(plot_pts[:, 0], plot_pts[:, 1],
                                           #bins=self.gridsize)
        #extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        #hb = self.subplot.imshow(h, extent=extent, interpolation='nearest')
            
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
            self.navtoolbar.DeleteToolByPos(6)
        return self.navtoolbar

    def reset_toolbar(self):
        # Cheat since there is no way reset
        if self.navtoolbar:
            self.navtoolbar._views.clear()
            self.navtoolbar._positions.clear()
            self.navtoolbar.push_current()
    

class Density(wx.Frame, CPATool):
    '''
    A very basic density plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Density Plot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        
        figpanel = DensityPanel(self)
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
            print 'Density plot requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    import multiclasssql
    multiclasssql.CreateFilterTables()
    
    density = Density(None)
    density.Show()
    
    app.MainLoop()
