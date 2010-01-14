# TODO: add hooks to change point size, alpha, numsides etc.
#

from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, UniqueObjectClause, image_key_columns
from MulticlassSQL import filter_table_prefix
from Properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import ImageList
import logging
import numpy as np
import os
import sys
import re
from time import time
import wx
import wx.combo
from matplotlib.widgets import Lasso, RectangleSelector
from matplotlib.nxutils import points_inside_poly
from matplotlib.colors import colorConverter
from matplotlib.collections import RegularPolyCollection
from matplotlib.pyplot import cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

p = Properties.getInstance()
db = DBConnect.getInstance()

NO_FILTER = 'No filter'

ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LINEAR_SCALE = 'linear'

SELECTED_COLOR = colorConverter.to_rgba('red', alpha=0.75)

class Datum:
    def __init__(self, (x, y), color, include=False):
        self.x = x
        self.y = y
        if include: self.color = SELECTED_COLOR
        else: self.color = color


class ScatterControlPanel(wx.Panel):
    '''
    A panel with controls for selecting the source data for a scatterplot 
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
        self.y_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.x_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.x_scale_choice.Select(0)
        self.y_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], style=wx.CB_READONLY)
        self.y_scale_choice.Select(0)
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
        sz.Add(self.y_scale_choice,)
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
        # plot the points
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())
        self.figpanel.set_x_label(self.x_choice.GetStringSelection())
        self.figpanel.set_y_label(self.y_choice.GetStringSelection())
        self.figpanel.set_point_lists(points)
        self.figpanel.draw()
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xpoints, ypoints, filter=NO_FILTER):
        if tablename == p.image_table:
            fields = UniqueImageClause(tablename)
        elif tablename == p.object_table:
            fields = UniqueObjectClause(tablename)
        else:
            raise UnimplementedError
        fields += ', %s.%s, %s.%s'%(tablename, xpoints, tablename, ypoints)
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


class ScatterPanel(FigureCanvasWxAgg):
    '''
    ScatterPanel contains the guts for drawing scatter plots to a PlotPanel.
    '''
    def __init__(self, parent, point_lists, clr_list=None, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        
        self.subplot = self.figure.add_subplot(111)
        self.navtoolbar = None
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.x_label = ''
        self.y_label = ''
        self.selection     = {}
        self.mouse_mode = 'lasso'
        self.set_point_lists(point_lists, clr_list)
        
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        
    def lasso_callback(self, verts):
        # Note: If the mouse is released outside of the canvas, (None,None) is
        #   returned as the last coordinate pair.
        # Cancel selection if user releases outside the canvas.
        for v in verts:
            if None in v: return
        
        for c, collection in enumerate(self.subplot.collections):
            # Build the selection
            if len(self.xys[c]) > 0:
                new_sel = np.nonzero(points_inside_poly(self.xys[c], verts))[0]
            else:
                new_sel = []
            if self.selection_key == None:
                self.selection[c] = new_sel
            elif self.selection_key == 'shift':
                self.selection[c] = list(set(self.selection.get(c,[])).union(new_sel))
            elif self.selection_key == 'alt':
                self.selection[c] = list(set(self.selection.get(c,[])).difference(new_sel))
            
            # Color the points
            facecolors = collection.get_facecolors()
            for i in range(len(self.point_lists[c])):
                if i in self.selection[c]:
                    facecolors[i] = SELECTED_COLOR
                else:
                    facecolors[i] = self.colors[c]

        self.canvas.draw_idle()
        
    def on_press(self, evt):
        if evt.button == 1:
            self.selection_key = evt.key
            if self.canvas.widgetlock.locked(): return
            if evt.inaxes is None: return
            
            if self.mouse_mode == 'lasso':
                self.lasso = Lasso(evt.inaxes, (evt.xdata, evt.ydata), self.lasso_callback)
                # acquire a lock on the widget drawing
                self.canvas.widgetlock(self.lasso)
                
            if self.mouse_mode == 'marquee':
                pass
        
    def on_release(self, evt):
        # Note: lasso_callback is not called on click without drag so we release
        #   the lock here to handle this case as well.
        if evt.button == 1:
            if self.__dict__.has_key('lasso') and self.lasso:
                self.canvas.draw_idle()
                self.canvas.widgetlock.release(self.lasso)
                del self.lasso
        else:
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
        
                    
    def show_popup_menu(self, (x, y), data):
        popup = wx.Menu()
        show_images_item = wx.MenuItem(popup, -1, 'Show images from selection')
        
        popup.AppendItem(show_images_item)
        
        def show_images(evt):
            for i, sel in self.selection.items():
                keys = self.key_lists[i][sel]
                keys = list(set([tuple(k) for k in keys]))
                ilf = ImageList.ImageListFrame(self, keys, title='Selection from collection %d in scatter'%(i+1))
                ilf.Show(True)
            
        self.Bind(wx.EVT_MENU, show_images, show_images_item)
        
        self.PopupMenu(popup, (x,y))
        
    def set_point_lists(self, keys_and_points, colors=None):
        '''
        points - a list of lists of keys and points
        colors - a list of colors to be applied to each inner list of points
                 if not supplied colors will be chosen from the Jet color map
        '''
        t0 = time()
        if len(keys_and_points)==0: keys_and_points = [[]]
        # Convert each list of keys and points into a np float array
        points = [np.array(pl).astype('f') for pl in keys_and_points]
        # Strip out keys and points 
        self.point_lists = []
        self.key_lists = []
        for pl in points:
            if len(pl)>0:
                self.point_lists += [pl[:,-2:]]
                self.key_lists += [pl[:,:len(image_key_columns())].astype(int)]
            else:
                self.point_lists += [np.array([]).astype('f')]
                self.key_lists += [np.array([]).astype(int)]
        
        # Choose colors from jet colormap starting with light blue (0.28)
        if max(map(len, self.point_lists))==0:
            colors = []
        elif colors is None:
            vals = np.arange(0.28, 1.28, 1./len(self.point_lists)) % 1.
            colors = [colorConverter.to_rgba(cm.jet(val), alpha=0.75) 
                      for val in vals]
        else:
            assert len(self.point_lists)==len(colors), 'points and colors must be of equal length'
        self.colors = colors

        self.subplot.clear()
        self.subplot.set_xlabel(self.x_label)
        self.subplot.set_ylabel(self.y_label)
        points = self.point_lists
        
        # Set log axes and print warning if any values will be masked out
        ignored = 0
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', basex=2.1, nonposx='mask')
            ignored = sum([len(points[i][c[:,0]<=0]) for i,c in enumerate(points) if len(c)>0])
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', basey=2.1, nonposy='mask')
            ignored += sum([len(points[i][c[:,1]<=0]) for i,c in enumerate(points) if len(c)>0])
        if ignored > 0:
            logging.warn('Scatter masked out %s points with negative values.'%(ignored))
        
        # Stop if there is no data in any of the point lists
        if max(map(len, points))==0:
            logging.warn('No data to plot.')
            self.reset_toolbar()
            return
        
        # Each point list is converted to a separate point collection
        self.collections = []
        self.xys = []
        for plot_pts, color in zip(points, colors):
            data = [Datum(xy, color) for xy in plot_pts]
            facecolors = [d.color for d in data]
            self.xys.append([(d.x, d.y) for d in data])
            
            self.subplot.scatter(plot_pts[:,0], plot_pts[:,1],
                                 s=30,
                                 facecolors = facecolors,
                                 edgecolor = 'none',
                                 alpha = 0.75)
            
        # Set axis scales & clip negative values if in log space
        # must be done after scatter
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', basex=2.1)
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', basey=2.1)
            
        # Set axis bounds
        xmin = min([np.nanmin(pts[:,0]) for pts in points if len(pts)>0])
        xmax = max([np.nanmax(pts[:,0]) for pts in points if len(pts)>0])
        ymin = min([np.nanmin(pts[:,1]) for pts in points if len(pts)>0])
        ymax = max([np.nanmax(pts[:,1]) for pts in points if len(pts)>0])
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

        logging.debug('Scatter: Plotted %s points in %.3f seconds.'%(sum(map(len, self.point_lists)), time()-t0))
        self.reset_toolbar()
    
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
    
    def get_point_lists(self):
        return self.point_lists
    
    def set_x_scale(self, scale):
        self.x_scale = scale
    
    def set_y_scale(self, scale):
        self.y_scale = scale
    
    def set_x_label(self, label):
        self.x_label = label
    
    def set_y_label(self, label):
        self.y_label = label
    
        

class Scatter(wx.Frame):
    '''
    A very basic scatter plot with controls for setting it's data source.
    '''
    def __init__(self, parent, point_lists=[], clr_lists=None,
                 show_controls=True,
                 size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Scatter Plot', **kwargs)
        self.SetName('Scatter')
        
        figpanel = ScatterPanel(self, point_lists, clr_lists)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
                
        if show_controls:
            configpanel = ScatterControlPanel(self, figpanel)
            sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
            
        self.SetToolBar(figpanel.get_toolbar())
            
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
            print 'Scatterplot requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    import MulticlassSQL
    MulticlassSQL.CreateFilterTables()
    
    points = []
    clrs = None
#    points = [[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
#              [],
#              [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7)],
#              [],]

    points = [np.random.normal(0, 1.5, size=(500,2)),
              np.random.normal(3, 2, size=(500,2)),
              np.random.normal(2, 3, size=(500,2)),]

#    clrs = [(0., 0.62, 1., 0.75),
#            (0.1, 0.2, 0.3, 0.75),
#            (0,0,0,1),
#            (1,0,1,1),
#            ]

    scatter = Scatter(None, points, clrs)
    scatter.Show()
#    scatter.figpanel.set_x_label('test')
#    scatter.figpanel.set_y_label('test')
    
    app.MainLoop()