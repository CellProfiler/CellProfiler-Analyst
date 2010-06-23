# TODO: add hooks to change point size, alpha, numsides etc.
from cpatool import CPATool
from ColorBarPanel import ColorBarPanel
from dbconnect import DBConnect, UniqueImageClause, UniqueObjectClause, image_key_columns
from MulticlassSQL import filter_table_prefix
from properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import ImageList
import imagetools
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
CREATE_NEW_FILTER = '*create new filter*'

ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LINEAR_SCALE = 'linear'

SELECTED_OUTLINE_COLOR = colorConverter.to_rgba('black')
UNSELECTED_OUTLINE_COLOR = colorConverter.to_rgba('black', alpha=0.)

class Datum:
    def __init__(self, (x, y), color):
        self.x = x
        self.y = y
        self.color = color
        
        
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
        wx.EVT_COMBOBOX(self.filter_choice, -1, self.on_filter_selected)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.update_figpanel)   
        
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
        
    def update_column_fields(self):
        tablename = self.table_choice.GetStringSelection()
        fieldnames = db.GetColumnNames(tablename)#self.get_numeric_columns_from_table(tablename)
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
        
    def update_figpanel(self, evt=None):        
        filter = self.filter_choice.GetStringSelection()
        keys_and_points = self.loadpoints(self.table_choice.GetStringSelection(),
                                 self.x_choice.GetStringSelection(),
                                 self.y_choice.GetStringSelection(),
                                 filter)
        col_types = self.get_selected_column_types()
                
        # Convert keys and points into a np array
        kps = np.array(keys_and_points)
        # Strip out keys
        keys = kps[:,:len(image_key_columns())].astype(int)
        # Strip out x coords
        if col_types[0] in [float, int, long]:
            xpoints = kps[:,-2].astype('float32')
        else:
            xpoints = kps[:,-2]
        # Strip out y coords
        if col_types[1] in [float, int, long]:
            ypoints = kps[:,-1].astype('float32')
        else:
            ypoints = kps[:,-1]

        # plot the points
        self.figpanel.set_points(xpoints, ypoints)
        self.figpanel.set_keys(keys)
        self.figpanel.set_x_label(self.x_choice.GetStringSelection())
        self.figpanel.set_y_label(self.y_choice.GetStringSelection())
        self.figpanel.set_x_scale(self.x_scale_choice.GetStringSelection())
        self.figpanel.set_y_scale(self.y_scale_choice.GetStringSelection())
        self.figpanel.redraw()
        self.figpanel.draw()
        
    def removefromchart(self, event):
        selected = self.plotfieldslistbox.GetSelection()
        self.plotfieldslistbox.Delete(selected)
        
    def loadpoints(self, tablename, xcol, ycol, filter=NO_FILTER):
        ''' Returns a list of rows containing:
        (TableNumber), ImageNumber, X measurement, Y measurement
        '''
        fields = UniqueImageClause(tablename)
        fields += ', %s.%s, %s.%s'%(tablename, xcol, tablename, ycol)
        tables = tablename
        where_clause = ''
        if filter != NO_FILTER:
            # If a filter is applied we must compute a WHERE clause and add the 
            # filter table to the FROM clause
            tables += ', %s'%(filter_table_prefix+filter) 
            filter_clause = ' AND '.join(['%s.%s=%s.%s'%(tablename, id, filter_table_prefix+filter, id) 
                                          for id in db.GetLinkingColumnsForTable(tablename)])
            where_clause = 'WHERE %s'%(filter_clause)
            
        return db.execute('SELECT %s FROM %s %s'%(fields, tables, where_clause))
    
    def get_selected_column_types(self):
        ''' Returns a tuple containing the x and y column types. '''
        table = self.table_choice.GetStringSelection()
        xcol = self.x_choice.GetStringSelection()
        ycol = self.y_choice.GetStringSelection()
        return (db.GetColumnType(table, xcol), db.GetColumnType(table, ycol))

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
        if 'y-axis' in settings:
            self.y_choice.SetStringSelection(settings['y-axis'])
        if 'x-scale' in settings:
            self.x_scale_choice.SetStringSelection(settings['x-scale'])
        if 'y-scale' in settings:
            self.y_scale_choice.SetStringSelection(settings['y-scale'])
        if 'filter' in settings:
            self.filter_choice.SetStringSelection(settings['filter'])
        self.update_figpanel()


class ScatterPanel(FigureCanvasWxAgg):
    '''
    Contains the guts for drawing scatter plots.
    '''
    def __init__(self, parent, xpoints=[], ypoints=[], keys=None, clr_list=None, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        
        self.subplot = self.figure.add_subplot(111)
        self.navtoolbar = None
        self.x_points = []
        self.y_points = []
        self.key_lists = None
        self.colors = []
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.x_label = ''
        self.y_label = ''
        self.selection = {}
        self.mouse_mode = 'lasso'
        self.legend = None
        self.set_points(xpoints, ypoints)
        if keys is not None:
            self.set_keys(keys)
        if clr_list is not None:
            self.set_colors(clr_list)
        self.redraw()
        
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
            for i in range(len(self.xys[c])):
                if i in self.selection[c]:
                    edgecolors[i] = SELECTED_OUTLINE_COLOR
                else:
                    edgecolors[i] = UNSELECTED_OUTLINE_COLOR
        logging.info('Selected %s points.'%(np.sum([len(sel) for sel in self.selection.values()])))
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

    def show_images_from_selection(self, evt=None):
        '''Callback for "Show images from selection" popup item.'''
        show_keys = []
        for i, sel in self.selection.items():
            keys = self.key_lists[i][sel]
            show_keys += list(set([tuple(k) for k in keys]))
        if len(show_keys)>10:
            dlg = wx.MessageDialog(self, 'You are about to open %s images. This may take some time depending on your settings.'%(len(show_keys)),
                                   'Warning', wx.YES_NO|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response != wx.ID_YES:
                return
        logging.info('Opening %s images.'%(len(show_keys)))
        for key in show_keys:
            imagetools.ShowImage(key, p.image_channel_colors, parent=self)
            
    def show_image_list_from_selection(self, evt=None):
        '''Callback for "Show image list from selection" popup item.'''
        for i, sel in self.selection.items():
            keys = self.key_lists[i][sel]
            keys = list(set([tuple(k) for k in keys]))
            if len(keys)>0:
                ilf = ImageList.ImageListFrame(self, keys, title='Selection from collection %d in scatter'%(i))
                ilf.Show(True)
            else:
                logging.info('No points were selected in collection %d'%(i))
            
    def on_new_collection_from_filter(self, evt):
        '''Callback for "Collection from filter" popup menu options.'''
        assert self.key_lists, 'Can not create a collection from a filter since image keys have not been set for this plot.'
        filter = self.popup_menu_filters[evt.Id]   
        keys = db.GetFilteredImages(filter)
        key_lists = []
        xpoints = []
        ypoints = []
        sel_keys = []
        sel_xs = []
        sel_ys = []
        for c, col in enumerate(self.subplot.collections):
            # Find indices of keys that fall in the filter.
            # Horribly inefficient (n^2), needs improvement
            # (maybe sort keys and use searchsorted)
            sel_indices = []
            unsel_indices = []
            for i in xrange(len(self.key_lists[c])):
                if self.key_lists[c][i] in keys:
                    sel_indices += [i]
                else:
                    unsel_indices += [i]
            # Build the new collections
            if len(sel_indices) > 0:
                if self.key_lists:
                    sel_keys += list(self.key_lists[c][sel_indices])
                    sel_xs += list(self.x_points[c][sel_indices])
                    sel_ys += list(self.y_points[c][sel_indices])
            if len(unsel_indices) > 0:
                if self.key_lists:
                    key_lists += [self.key_lists[c][unsel_indices]]
                xpoints += [np.array(self.x_points[c][unsel_indices])]
                ypoints += [np.array(self.y_points[c][unsel_indices])]
        xpoints += [np.array(sel_xs)]
        ypoints += [np.array(sel_ys)]
        if self.key_lists:
            key_lists += [np.array(sel_keys)]
        
        self.set_points(xpoints, ypoints)
        if self.key_lists:
            self.set_keys(key_lists)
        # reset scale (this is so the user is warned of masked non-positive values)
        self.set_x_scale(self.x_scale)
        self.set_y_scale(self.y_scale)
        self.redraw()
        self.figure.canvas.draw_idle()
        
    def on_collection_from_selection(self, evt):
        '''Callback for "Collection from selection" popup menu option.'''
        key_lists = []
        xpoints = []
        ypoints = []
        sel_keys = []
        sel_xs = []
        sel_ys = []
        for c, col in enumerate(self.subplot.collections):
            indices = xrange(len(col.get_offsets()))
            sel_indices = self.selection[c]
            unsel_indices = list(set(indices).difference(sel_indices))
            if len(sel_indices) > 0:
                if self.key_lists:
                    sel_keys += list(self.key_lists[c][sel_indices])
                    sel_xs += list(self.x_points[c][sel_indices])
                    sel_ys += list(self.y_points[c][sel_indices])
            if len(unsel_indices) > 0:
                if self.key_lists:
                    key_lists += [self.key_lists[c][unsel_indices]]
                xpoints += [np.array(self.x_points[c][unsel_indices])]
                ypoints += [np.array(self.y_points[c][unsel_indices])]

        xpoints += [np.array(sel_xs)]
        ypoints += [np.array(sel_ys)]
        if self.key_lists:
            key_lists += [np.array(sel_keys)]
        
        self.set_points(xpoints, ypoints)
        if self.key_lists:
            self.set_keys(key_lists)
        # reset scale (this is so the user is warned of masked non-positive values)
        self.set_x_scale(self.x_scale)
        self.set_y_scale(self.y_scale)
        self.redraw()
        self.figure.canvas.draw_idle()
        
    def on_scatter_from_selection(self, evt):
        ''' Creates a new scatter plot from the current selection. '''
        sel_keys = []
        sel_xs = []
        sel_ys = []
        for c, collection in enumerate(self.subplot.collections):
            indices = xrange(len(collection.get_offsets()))
            sel_indices = self.selection[c]
            if len(sel_indices) > 0:
                if self.key_lists:
                    sel_keys += [self.key_lists[c][sel_indices]]
                sel_xs += [self.x_points[c][sel_indices]]
                sel_ys += [self.y_points[c][sel_indices]]
            
        scatter = Scatter(self.Parent, sel_xs, sel_ys, (sel_keys or None))
        scatter.Show()
    
    def show_popup_menu(self, (x,y), data):
        self.popup_menu_filters = {}
        popup = wx.Menu()
        
        show_images_item = popup.Append(-1, 'Show images from selection')
        if self.selection_is_empty():
            show_images_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.show_images_from_selection, show_images_item)
        
        show_imagelist_item = popup.Append(-1, 'Show image list from selection')
        if self.selection_is_empty():
            show_imagelist_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.show_image_list_from_selection, show_imagelist_item)
        
        scatter_from_sel_item = popup.Append(-1, 'Open selected points in new plot')
        if self.selection_is_empty():
            scatter_from_sel_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.on_scatter_from_selection, scatter_from_sel_item)
        
        collection_from_selection_item = popup.Append(-1, 'Create collection from selection')
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
        popup.AppendMenu(-1, 'Create collection from filter', submenu)
        
        self.PopupMenu(popup, (x,y))
            
    def get_key_lists(self):
        return self.key_lists
                                
    def set_colors(self):
        assert len(self.point_lists)==len(colors), 'points and colors must be of equal length'
        self.colors = colors

    def get_colors(self):
        if self.colors:
            colors = self.colors
        elif max(map(len, self.x_points))==0:
            colors = []
        else:
            # Choose colors from jet colormap starting with light blue (0.28)
            vals = np.arange(0.28, 1.28, 1. / len(self.x_points)) % 1.
            colors = [colorConverter.to_rgba(cm.jet(val), alpha=0.75) 
                      for val in vals]
        return colors

    def set_keys(self, keys):
        if len(keys) == 0:
            self.key_lists = None
        if type(keys) != list:
            assert len(keys) == len(self.x_points[0])
            assert len(self.x_points) == 1
            self.key_lists = [keys]
        else:
            assert len(keys) == len(self.x_points)
            for ks, xs in zip(keys, self.x_points):
                assert len(ks) == len(xs)
            self.key_lists = keys

        
    def set_points(self, xpoints, ypoints):
        ''' 
        xpoints - an array or a list of arrays containing points
        ypoints - an array or a list of arrays containing points
        xpoints and ypoints must be of equal size and shape
        each array will be interpreted as a separate collection
        '''
        assert len(xpoints) == len(ypoints)
        if len(xpoints) == 0:
            self.x_points = []
            self.y_points = []
        elif type(xpoints[0]) != np.ndarray:
            self.x_points = [xpoints]
            self.y_points = [ypoints]
        else:
            self.x_points = xpoints
            self.y_points = ypoints
        
    def get_x_points(self):
        return self.x_points

    def get_y_points(self):
        return self.y_points

    def redraw(self):
        t0 = time()
        # XXX: maybe attempt to maintain selection based on keys
        self.selection = {}
        self.subplot.clear()
        
        # XXX: move to setters?
        self.subplot.set_xlabel(self.x_label)
        self.subplot.set_ylabel(self.y_label)
        
        xpoints = self.get_x_points()
        ypoints = self.get_y_points()
        
        # Stop if there is no data in any of the point lists
        if len(xpoints) == 0:
            logging.warn('No data to plot.')
            self.reset_toolbar()
            return

        # Gather all categorical data to be plotted so we can populate
        # the axis the same regardless of which collections the categories
        # fall in.
        xvalmap = {}
        yvalmap = {}
        if not issubclass(self.x_points[0].dtype.type, np.number):
            x_categories = sorted(set(np.hstack(self.x_points)))
            # Map all categorical values to integer values from 0..N
            for i, category in enumerate(x_categories):
                xvalmap[category] = i
        if not issubclass(self.y_points[0].dtype.type, np.number):
            y_categories = sorted(set(np.hstack(self.y_points)))
            # Map all categorical values to integer values from 0..N
            for i, category in enumerate(y_categories):
                yvalmap[category] = i        
            
        # Each point list is converted to a separate point collection by 
        # subplot.scatter
        self.xys = []
        xx = []
        yy = []
        for c, (xs, ys, color) in enumerate(zip(self.x_points, self.y_points, self.get_colors())):
            if len(xs) > 0:
                xx = xs
                yy = ys
                # Map categorical values to integers 0..N
                if xvalmap:
                    xx = [xvalmap[l] for l in xx]
                # Map categorical values to integers 0..N
                if yvalmap:
                    yy = [yvalmap[l] for l in yy]

                data = [Datum(xy, color) for xy in zip(xx, yy)]
                facecolors = [d.color for d in data]
                self.xys.append(np.array([(d.x, d.y) for d in data]))
                
                self.subplot.scatter(xx, yy,
                    s = 30,
                    facecolors = facecolors,
                    edgecolors = ['none' for f in facecolors],
                    alpha = 0.75)
        
        # Set ticks and ticklabels if data is categorical
        if xvalmap:
            self.subplot.set_xticks(range(len(x_categories)))
            self.subplot.set_xticklabels(sorted(x_categories))
            self.figure.autofmt_xdate() # rotates and shifts xtick-labels so they look nice
        if yvalmap:
            self.subplot.set_yticks(range(len(y_categories)))
            self.subplot.set_yticklabels(sorted(y_categories))
        
        if len(self.x_points) > 1:
            if self.legend:
                self.legend.disconnect_bindings()
            self.legend = DraggableLegend(self.subplot.legend(fancybox=True))
            
        # Set axis scales
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', basex=2.1)
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', basey=2.1)
            
        # Set axis bounds. Clip non-positive values if in log space
        # Must be done after scatter.
        xmin = min([np.nanmin(pts[:,0]) for pts in self.xys if len(pts)>0])
        xmax = max([np.nanmax(pts[:,0]) for pts in self.xys if len(pts)>0])
        ymin = min([np.nanmin(pts[:,1]) for pts in self.xys if len(pts)>0])
        ymax = max([np.nanmax(pts[:,1]) for pts in self.xys if len(pts)>0])
        if self.x_scale == LOG_SCALE:
            xmin = min([np.nanmin(pts[:,0][pts[:,0].flatten() > 0]) 
                        for pts in self.xys if len(pts)>0])
            xmin = xmin / 1.5
            xmax = xmax * 1.5
        else:
            xmin = xmin - (xmax - xmin) / 20.
            xmax = xmax + (xmax - xmin) / 20.
        if self.y_scale == LOG_SCALE:
            ymin = min([np.nanmin(pts[:,1][pts[:,1].flatten() > 0]) 
                        for pts in self.xys if len(pts)>0])
            ymin = ymin / 1.5
            ymax = ymax * 1.5
        else:
            ymin = ymin - (ymax - ymin) / 20.
            ymax = ymax + (ymax - ymin) / 20.
        self.subplot.axis([xmin, xmax, ymin, ymax])

        logging.debug('Scatter: Plotted %s points in %.3f seconds.'
                      %(sum(map(len, self.x_points)), time() - t0))
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
    
    def set_x_scale(self, scale):
        self.x_scale = scale
        # Set log axes and print warning if any values will be masked out
        ignored = 0
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', basex=2.1, nonposx='mask')
            ignored = sum([len(self.x_points[i][xs <= 0]) 
                           for i, xs in enumerate(self.x_points) if len(xs) > 0])
        if ignored > 0:
            logging.warn('Scatter masked out %s points with non-positive X values.'%(ignored))        
            
    def set_y_scale(self, scale):
        self.y_scale = scale
        # Set log axes and print warning if any values will be masked out
        ignored = 0
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', basey=2.1, nonposy='mask')
            ignored += sum([len(self.y_points[i][ys <= 0]) 
                            for i, ys in enumerate(self.y_points) if len(ys) > 0])
        if ignored > 0:
            logging.warn('Scatter masked out %s points with non-positive Y values.'%(ignored))  
    
    def set_x_label(self, label):
        self.x_label = label
    
    def set_y_label(self, label):
        self.y_label = label
    
        

class Scatter(wx.Frame, CPATool):
    '''
    A very basic scatter plot with controls for setting it's data source.
    '''
    def __init__(self, parent, xpoints=[], ypoints=[], keys=None, clr_lists=None,
                 show_controls=True,
                 size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Scatter Plot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        
        figpanel = ScatterPanel(self, xpoints, ypoints, keys, clr_lists)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
                
        if show_controls:
            configpanel = ScatterControlPanel(self, figpanel)
            sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetToolBar(figpanel.get_toolbar())            
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
            print 'Scatterplot requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

    import MulticlassSQL
    MulticlassSQL.CreateFilterTables()
    
    xpoints = []
    ypoints = []
    clrs = None

#    clrs = [(0., 0.62, 1., 0.75),
#            (0.1, 0.2, 0.3, 0.75),
#            (0,0,0,1),
#            (1,0,1,1),
#            ]

    scatter = Scatter(None, xpoints, ypoints, clrs)
    scatter.Show()
#    scatter.figpanel.set_x_label('test')
#    scatter.figpanel.set_y_label('test')
    
    app.MainLoop()