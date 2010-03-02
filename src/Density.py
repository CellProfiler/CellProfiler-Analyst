from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, image_key_columns
from MulticlassSQL import filter_table_prefix
from Properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import ImageTools
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

        tables = db.GetTableNames()
        self.table_choice = ComboBox(self, -1, choices=tables, style=wx.CB_READONLY)
        if p.image_table in tables:
            self.table_choice.Select(tables.index(p.image_table))
        else:
            logging.error('Could not find your image table "%s" among the database tables found: %s'%(p.image_table, tables))
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
        sz.Add(wx.StaticText(self, -1, "x-scale:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.x_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "y-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.y_choice, 1, wx.EXPAND)
        sz.AddSpacer((5,-1))
        sz.Add(wx.StaticText(self, -1, "y-scale:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.y_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,5))
        
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
        
        wx.EVT_COMBOBOX(self.table_choice, -1, self.on_table_selected)
        wx.EVT_COMBOBOX(self.filter_choice, -1, self.on_filter_selected)
        wx.EVT_COMBOBOX(self.colormap_choice, -1, self.on_cmap_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.on_update_pressed)
        
        self.SetSizer(sizer)
        self.Show(1)

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
                from MulticlassSQL import CreateFilterTable
                logging.info('Creating filter table...')
                CreateFilterTable(fname)
                logging.info('Done creating filter.')
            cff.Destroy()
            
    def on_cmap_selected(self, evt):
        self.figpanel.set_colormap(self.colormap_choice.GetStringSelection())
        
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
        filter = self.filter_choice.GetStringSelection()
        points = self.loadpoints(self.table_choice.GetStringSelection(),
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
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xpoints, ypoints, filter=NO_FILTER):
        fields = '%s.%s, %s.%s'%(tablename, xpoints, tablename, ypoints)
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
        self.point_lists = []
        self.gridsize = 50
        self.cb = None
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.color_scale = None
        self.x_label = ''
        self.y_label = ''
        self.cmap ='jet'
    
    def setpointslists(self, points):
        self.point_lists = points
        
        self.figure.clear()
        self.subplot = self.figure.add_subplot(111)
            
        for i, pt_list in enumerate(self.point_lists):
            plot_pts = np.array(pt_list).astype(float)
            
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
            
#            h, xedges, yedges = np.histogram2d(plot_pts[:, 0], plot_pts[:, 1],
#                                               bins=self.gridsize)
#            extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
#            hb = self.subplot.imshow(h, extent=extent, interpolation='nearest')
            
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
        return self.point_lists
    
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
    

class Density(wx.Frame):
    '''
    A very basic density plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600)):
        wx.Frame.__init__(self, parent, -1, size=size, title='Density Plot')
        self.SetName('Density')
        
        figpanel = DensityPanel(self)
        configpanel = DataSourcePanel(self, figpanel)
        self.SetToolBar(figpanel.get_toolbar())
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
        sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)



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

    import MulticlassSQL
    MulticlassSQL.CreateFilterTables()
    
    density = Density(None)
    density.Show()
    
    app.MainLoop()
