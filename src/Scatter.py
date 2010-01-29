# TODO: add hooks to change point size, alpha, numsides etc.
from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, UniqueObjectClause, image_key_columns
from MulticlassSQL import filter_table_prefix
from Properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import ImageList
#from icons import lasso_tool
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
    def __init__(self, (x, y), color, edgecolor='none', include=False):
        self.x = x
        self.y = y
        if include: self.color = SELECTED_COLOR
        else: self.color = color
        self.edgecolor = edgecolor
        
        
class DraggableLegend:
    '''
    Attaches interaction to a subplot legend to allow dragging.
    usage: DraggableLegend(subplot.legend())
    '''
    def __init__(self, legend):
        self.legend = legend
        self.dragging = False
        self.cids = [legend.figure.canvas.mpl_connect('motion_notify_event', self.on_motion),
                     legend.figure.canvas.mpl_connect('pick_event', self.on_pick),
                     legend.figure.canvas.mpl_connect('button_release_event', self.on_release)]
        legend.set_picker(self.legend_picker)
        
    def on_motion(self, evt):
        if self.dragging:
            dx = evt.x - self.mouse_x
            dy = evt.y - self.mouse_y
            loc_in_canvas = self.legend_x + dx, self.legend_y + dy
            loc_in_norm_axes = self.legend.parent.transAxes.inverted().transform_point(loc_in_canvas)
            self.legend._loc = tuple(loc_in_norm_axes)
            self.legend.figure.canvas.draw()
    
    def legend_picker(self, legend, evt): 
        return legend.legendPatch.contains(evt)

    def on_pick(self, evt):
        if evt.artist == self.legend:
            bbox = self.legend.get_window_extent()
            self.mouse_x = evt.mouseevent.x
            self.mouse_y = evt.mouseevent.y
            self.legend_x = bbox.xmin
            self.legend_y = bbox.ymin 
            self.dragging = 1
            
    def on_release(self, evt):
        self.dragging = False
            
    def disconnect_bindings(self):
        for cid in self.cids:
            self.legend.figure.canvas.mpl_disconnect(cid)
            
            
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
        if p.image_table in tables:
            self.table_choice.Select(tables.index(p.image_table))
        else:
            logging.error('Could not find your image table "%s" among the database tables found: %s'%(p.image_table, tables))
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
    Contains the guts for drawing scatter plots.
    '''
    def __init__(self, parent, point_lists, clr_list=None, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        
        self.subplot = self.figure.add_subplot(111)
        self.navtoolbar = None
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.x_label = ''
        self.y_label = ''
        self.selection = {}
        self.mouse_mode = 'lasso'
        self.legend = None
        self.set_point_lists(point_lists, clr_list)
        
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
    
    def selection_is_empty(self):
        return self.selection == {} or all([len(s)==0 for s in self.selection.values()])
        
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
            edgecolors = collection.get_edgecolors()
            for i in range(len(self.point_lists[c])):
                if i in self.selection[c]:
                    edgecolors[i] = colorConverter.to_rgba('black')
                else:
                    edgecolors[i] = colorConverter.to_rgba('none')

        self.canvas.draw_idle()
        
    def on_press(self, evt):
        if self.legend and self.legend.dragging:
            return
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

    def show_image_list_from_selection(self, evt=None):
        '''Callback for "Show images from selection" popup item.'''
        for i, sel in self.selection.items():
            keys = self.key_lists[i][sel]
            keys = list(set([tuple(k) for k in keys]))
            ilf = ImageList.ImageListFrame(self, keys, title='Selection from collection %d in scatter'%(i+1))
            ilf.Show(True)
            
    def on_new_collection_from_filter(self, evt):
        '''Callback for "Collection from filter" popup menu options.'''
        filter = self.popup_menu_filters[evt.Id]   
        filter_keys = db.GetFilteredImages(filter)
        self.create_collection_from_keys(filter_keys)
        
    def on_collection_from_selection(self, evt):
        keys = []
        for c, collection in enumerate(self.subplot.collections):
            keys = [tuple(self.key_lists[c][id]) for id in self.selection[c]]
        self.create_collection_from_keys(keys)
        
    def create_collection_from_keys(self, keys):
        '''Finds the given keys in self.point_lists, and pulls them into a new
        list which will be colored differently from the rest.'''
        kls = self.key_lists
        pls = self.point_lists
        newkp = []
        coll = []
        for i in xrange(len(kls)):
            newkp += [[]]
            for j in xrange(len(kls[i])):
                entry = list(kls[i][j])+list(pls[i][j])
                if kls[i][j] in keys:
                    coll += [entry]
                else:
                    newkp[i] += [entry]
        newkp += [coll]
        self.set_point_lists(newkp)
        if self.legend:
            self.legend.disconnect_bindings()
        self.legend = DraggableLegend(self.subplot.legend(fancybox=True))
        self.figure.canvas.draw()
    
    def show_popup_menu(self, (x,y), data):
        self.popup_menu_filters = {}
        popup = wx.Menu()
        show_images_item = popup.Append(-1, 'Show images from selection')
        if self.selection_is_empty():
            show_images_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.show_image_list_from_selection, show_images_item)
        
        collection_from_selection_item = popup.Append(-1, 'Collection from selection')
        if self.selection_is_empty():
            collection_from_selection_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.on_collection_from_selection, collection_from_selection_item)
            
        # Color points by filter submenu
        submenu = wx.Menu()
        for f in p._filters_ordered:
            id = wx.NewId()
            item = submenu.Append(id, f)
            self.popup_menu_filters[id] = f
            self.Bind(wx.EVT_MENU, self.on_new_collection_from_filter, item)
        popup.AppendMenu(-1, 'Collection from filter', submenu)
        
        self.PopupMenu(popup, (x,y))
        
    def set_point_lists(self, keys_and_points, colors=None):
        '''
        points - a list of lists of keys and points
        colors - a list of colors to be applied to each inner list of points
                 if not supplied colors will be chosen from the Jet color map
        '''
        t0 = time()
        if len(keys_and_points)==0: keys_and_points = [[]]
        self.selection = {}
        # Convert each list of keys and points into a np float array
        points = [np.array(pl).astype('f') for pl in keys_and_points]
        # Strip out keys and points 
        self.point_lists = []
        self.key_lists = []
        for pl in points:
            # Note, empty point lists are simply discarded
            if len(pl)>0:
                self.point_lists += [pl[:,-2:]]
                self.key_lists += [pl[:,:len(image_key_columns())].astype(int)]
        
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
        
        # Each point list is converted to a separate point collection by 
        # subplot.scatter
        self.xys = []
        for pts, color in zip(points, colors):
            data = [Datum(xy, color) for xy in pts]
            facecolors = [d.color for d in data]
            edgecolors = [d.edgecolor for d in data]
            self.xys.append([(d.x, d.y) for d in data])
            if len(pts) > 0:
                self.subplot.scatter(pts[:,0], pts[:,1],
                    s=30,
                    facecolors = facecolors,
                    edgecolors = edgecolors,
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
    
    def toggle_lasso_tool(self):
        print ':',self.navtoolbar.mode
    
    def get_toolbar(self):
        if not self.navtoolbar:
            self.navtoolbar = NavigationToolbar(self.canvas)
            self.navtoolbar.DeleteToolByPos(6)
#            ID_LASSO_TOOL = wx.NewId()
#            lasso = self.navtoolbar.InsertSimpleTool(5, ID_LASSO_TOOL, lasso_tool.ConvertToBitmap(), '', '', isToggle=True)
#            self.navtoolbar.Realize()
#            self.Bind(wx.EVT_TOOL, self.toggle_lasso_tool, id=ID_LASSO_TOOL)
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
              [],
              np.random.normal(2, 3, size=(500,2))]

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