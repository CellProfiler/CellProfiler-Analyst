
# TODO: add hooks to change point size, alpha, numsides etc.
from .cpatool import CPATool
from . import tableviewer
from .dbconnect import DBConnect, image_key_columns, object_key_columns
from . import sqltools as sql
from .properties import Properties
from wx.adv import OwnerDrawnComboBox as ComboBox
from . import guiutils as ui
from .gating import GatingHelper
from . import imagetools
from cpa.icons import get_icon
import logging
import numpy as np
from bisect import bisect
import sys
from time import time
import wx
from matplotlib.widgets import Lasso
from matplotlib.colors import colorConverter
from matplotlib.pyplot import cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg

p = Properties()
db = DBConnect()

ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LINEAR_SCALE = 'linear'

SELECTED_OUTLINE_COLOR = colorConverter.to_rgba('black')
UNSELECTED_OUTLINE_COLOR = colorConverter.to_rgba('black', alpha=0.)

class Datum:
    def __init__(self, xxx_todo_changeme, color):
        (x, y) = xxx_todo_changeme
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
                     legend.figure.canvas.mpl_connect('button_press_event', self.on_press),
                     legend.figure.canvas.mpl_connect('button_release_event', self.on_release)]
        
    def on_motion(self, evt):
        if self.dragging:
            dx = evt.x - self.mouse_x
            dy = evt.y - self.mouse_y
            loc_in_canvas = self.legend_x + dx, self.legend_y + dy
            loc_in_norm_axes = self.legend.parent.transAxes.inverted().transform_point(loc_in_canvas)
            self.legend._loc = tuple(loc_in_norm_axes)
            self.legend.figure.canvas.draw()
    
    def on_press(self, evt):
        if evt.button == 1 and self.hit_test(evt):
            bbox = self.legend.get_window_extent()
            self.mouse_x = evt.x
            self.mouse_y = evt.y
            self.legend_x = bbox.xmin
            self.legend_y = bbox.ymin 
            self.dragging = True
            
    def hit_test(self, evt):
        return self.legend.get_window_extent().contains(evt.x, evt.y)
    
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
        self.SetBackgroundColour('white') # color for the background of panel

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.x_table_choice = ui.TableComboBox(self, -1, style=wx.CB_READONLY)
        self.y_table_choice = ui.TableComboBox(self, -1, style=wx.CB_READONLY)
        self.x_choice = ComboBox(self, -1, choices=[''], size=(200,-1), style=wx.CB_READONLY)
        self.x_choice.Select(0)
        self.y_choice = ComboBox(self, -1, choices=[''], size=(200,-1), style=wx.CB_READONLY)
        self.y_choice.Select(0)
        self.x_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], size=(90,-1), style=wx.CB_READONLY)
        self.x_scale_choice.Select(0)
        self.y_scale_choice = ComboBox(self, -1, choices=[LINEAR_SCALE, LOG_SCALE], size=(90,-1), style=wx.CB_READONLY)
        self.y_scale_choice.Select(0)
        self.filter_choice = ui.FilterComboBox(self, style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.gate_choice = ui.GateComboBox(self, style=wx.CB_READONLY)
        self.gate_choice.set_gatable_columns([self.x_column, self.y_column])
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_x_choices()
        self.update_y_choices()
                
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.x_table_choice, 1, wx.EXPAND) 
        sz.AddSpacer(3)
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(wx.StaticText(self, -1, "scale:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.x_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 2, 0)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "y-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.y_table_choice, 1, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(self.y_choice, 2, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(wx.StaticText(self, -1, "scale:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.y_scale_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 2, 0)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(wx.StaticText(self, -1, "gate:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.gate_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 2, 0)
        
        sizer.Add(self.update_chart_btn)

        self.x_table_choice.Bind(wx.EVT_COMBOBOX, self.on_x_table_selected)
        self.y_table_choice.Bind(wx.EVT_COMBOBOX, self.on_y_table_selected)
        self.gate_choice.addobserver(self.on_gate_selected)
        self.update_chart_btn.Bind(wx.EVT_BUTTON, self.update_figpanel)

        self.SetSizer(sizer)
        self.Show(1)
        
    @property
    def x_column(self):
        x_table_choice_id = self.x_table_choice.GetSelection()
        x_choice_id = self.x_choice.GetSelection()
        return sql.Column(self.x_table_choice.GetString(x_table_choice_id), 
                          self.x_choice.GetString(x_choice_id))
    @property
    def y_column(self):
        y_table_choice_id = self.y_table_choice.GetSelection()
        y_choice_id = self.y_choice.GetSelection()
        return sql.Column(self.y_table_choice.GetString(y_table_choice_id), 
                          self.y_choice.GetString(y_choice_id))
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
            # Deactivate the lasso tool
            self.figpanel.get_toolbar().toggle_user_tool('lasso', False)
            self.figpanel.gate_helper.set_displayed_gate(p.gates[gate_name], self.x_column, self.y_column)
        else:
            self.figpanel.gate_helper.disable()        

    def update_x_choices(self):
        tablename = self.x_table_choice.Value
        fieldnames = db.GetColumnNames(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)
            
    def update_y_choices(self):
        tablename = self.y_table_choice.Value
        fieldnames = db.GetColumnNames(tablename)
        self.y_choice.Clear()
        self.y_choice.AppendItems(fieldnames)
        self.y_choice.SetSelection(0)
        
    def _plotting_per_object_data(self):
        return (p.object_table is not None and
                p.object_table in [self.x_column.table, self.y_column.table]
                or (self.x_column.table != p.image_table and db.adjacent(p.object_table, self.x_column.table))
                or (self.y_column.table != p.image_table and db.adjacent(p.object_table, self.y_column.table))
                )
        
    def update_figpanel(self, evt=None):
        self.gate_choice.set_gatable_columns([self.x_column, self.y_column])
        self.gate_choice.update_info()
        keys_and_points = self._load_points()
        col_types = self.get_selected_column_types()
                
        # Convert keys and points into a np array
        # NOTE: We must set dtype "object" on creation or values like 0.34567e-9
        #       may be truncated to 0.34567e (error) or 0.345 (no error) when
        #       the array contains strings.
        kps = np.array(keys_and_points, dtype='object')
        # Strip out keys
        if self._plotting_per_object_data():
            key_indices = list(range(len(object_key_columns())))
        else:
            key_indices = list(range(len(image_key_columns())))

        keys = kps[:,key_indices].astype(int) 
        # Strip out x coords
        if col_types[0] in (float, int):
            xpoints = kps[:,-2].astype('float32')
        else:
            xpoints = kps[:,-2]
        # Strip out y coords
        if col_types[1] in (float, int):
            ypoints = kps[:,-1].astype('float32')
        else:
            ypoints = kps[:,-1]

        # plot the points
        self.figpanel.set_points(xpoints, ypoints)
        self.figpanel.set_keys(keys)
        self.figpanel.set_x_scale(self.x_scale_choice.Value)
        self.figpanel.set_y_scale(self.y_scale_choice.Value)
        self.figpanel.set_x_label(self.x_column.col)
        self.figpanel.set_y_label(self.y_column.col)
        self.update_gate_helper()
        self.figpanel.redraw()
        self.figpanel.draw()
        
    def _load_points(self):
        q = sql.QueryBuilder()
        select = []
        #
        # If there's an object table fetch object keys. Else fetch image keys.
        #
        # TODO: linking per-well data doesn't work if we fetch keys this way
        #
        if self._plotting_per_object_data():
            select += [sql.Column(p.object_table, col) for col in object_key_columns()]
        else:
            select += [sql.Column(p.image_table, col) for col in image_key_columns()]
        select += [self.x_column, self.y_column]
        q.set_select_clause(select)
        if self.filter != None:
            q.add_filter(self.filter)
        q.add_where(sql.Expression(self.x_column, 'IS NOT NULL'))
        q.add_where(sql.Expression(self.y_column, 'IS NOT NULL'))
        return db.execute(str(q))
    
    def get_selected_column_types(self):
        ''' Returns a tuple containing the x and y column types. '''
        return (db.GetColumnType(self.x_table_choice.Value, self.x_choice.Value),
                db.GetColumnType(self.y_table_choice.Value, self.y_choice.Value))

    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        returns a dictionary mapping setting names to values encoded as strings
        '''
        d = {'x-table' : self.x_table_choice.Value,
             'y-table' : self.y_table_choice.Value,
             'x-axis'  : self.x_choice.Value,
             'y-axis'  : self.y_choice.Value,
             'x-scale' : self.x_scale_choice.Value,
             'y-scale' : self.y_scale_choice.Value,
             'filter'  : self.filter_choice.Value,
             'x-lim'   : self.figpanel.subplot.get_xlim(),
             'y-lim'   : self.figpanel.subplot.get_ylim(),
             'version' : '1',
             }
        if self.gate_choice.get_gatename_or_none():
            gate_choice_id = self.gate_choice.GetSelection() 
            d['gate'] = self.gate_choice.GetString(gate_choice_id)
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


class ScatterPanel(FigureCanvasWxAgg):
    '''
    Contains the guts for drawing scatter plots.
    '''
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
        
        self.x_column = None
        self.y_column = None 
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
        self.mouse_mode = 'gate'
        self.legend = None
        self.lasso = None
        self.redraw()
        
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
    
    def set_configpanel(self,configpanel):
        '''Allow access of the control panel from the plotting panel'''
        self.configpanel = configpanel
        
    def get_current_x_measurement_name(self):
        '''Return the x measurement column currently selected in the UI panel'''
        return str(self.configpanel.x_choice.Value)
    
    def get_current_y_measurement_name(self):
        '''Return the x measurement column currently selected in the UI panel'''
        return str(self.configpanel.y_choice.Value)
    
    def is_per_object_data(self):
        '''return whether points in the current plot represent objects'''
        if p.object_table is None:
            return False
        for kl in self.key_lists:
            try:
                if len(kl[0]) == len(object_key_columns()):
                    return True
            except:
                pass
        return False
    
    def is_per_image_data(self):
        '''return whether points in the current plot represent images'''
        # FIXME: still don't support per-well data
        return not self.is_per_object_data()
        
    def selection_is_empty(self):
        return self.selection == {} or all([len(s)==0 for s in list(self.selection.values())])
        
    def lasso_callback(self, verts):
        # Note: If the mouse is released outside of the canvas, (None,None) is
        #   returned as the last coordinate pair.
        # Cancel selection if user releases outside the canvas.
        if None in verts[-1]: return
        
        for c, collection in enumerate(self.subplot.collections):
            # Build the selection
            if len(self.xys[c]) > 0:
                from matplotlib.path import Path
                new_sel = np.nonzero(Path(verts).contains_points(self.xys[c]))[0]
            else:
                new_sel = []
            if self.selection_key == None:
                self.selection[c] = new_sel
            elif self.selection_key == 'shift':
                self.selection[c] = list(set(self.selection.get(c,[])).union(new_sel))
            elif self.selection_key == 'alt':
                self.selection[c] = list(set(self.selection.get(c,[])).difference(new_sel))
            
            # outline the points
            edgecolors = collection.get_edgecolors()
            for i in range(len(self.xys[c])):
                if i in self.selection[c]:
                    edgecolors[i] = SELECTED_OUTLINE_COLOR
                else:
                    edgecolors[i] = UNSELECTED_OUTLINE_COLOR
        logging.info('Selected %s points.'%(np.sum([len(sel) for sel in list(self.selection.values())])))
        self.canvas.draw_idle()
        
    def on_press(self, evt):
        if self.legend and self.legend.hit_test(evt):
            return
        if evt.button == 1:
            self.selection_key = evt.key
            if self.canvas.widgetlock.locked(): return
            if evt.inaxes is None: return
            if self.navtoolbar.get_mode() == 'lasso':
                self.lasso = Lasso(evt.inaxes, (evt.xdata, evt.ydata), self.lasso_callback)
                # acquire a lock on the widget drawing
                self.canvas.widgetlock(self.lasso)
        
    def on_release(self, evt):
        # Note: lasso_callback is not called on click without drag so we release
        #   the lock here to handle this case as well.
        if evt.button == 1:
            if self.lasso:
                self.canvas.draw_idle()
                self.canvas.widgetlock.release(self.lasso)
                self.lasso = None
        elif evt.button == 3:  # right click
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
            
    def show_objects_from_selection(self, evt=None):
        '''Callback for "Show objects in selection" popup item.'''
        show_keys = []
        for i, sel in list(self.selection.items()):
            keys = self.key_lists[i][sel]
            show_keys += list(set([tuple(k) for k in keys]))
        if len(show_keys[0]) == len(image_key_columns()):
            from . import datamodel
            dm = datamodel.DataModel()
            obkeys = []
            for key in show_keys:
                obkeys += dm.GetObjectsFromImage(key)
            show_keys = obkeys

        if len(show_keys) > 100:
            te = wx.TextEntryDialog(self, 'You have selected %s %s. How many '
                            'would you like to show at random?'%(len(show_keys), 
                            p.object_name[1]), 'Choose # of %s'%
                            (p.object_name[1]), defaultValue='100')
            te.ShowModal()
            try:
                res = int(te.Value)
                np.random.shuffle(show_keys)
                show_keys = show_keys[:res]
            except ValueError:
                wx.MessageDialog('You have entered an invalid number', 'Error').ShowModal()
                return
        from . import sortbin
        f = sortbin.CellMontageFrame(None)
        f.Show()
        f.add_objects(show_keys)
        
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

    def show_images_from_selection(self, evt=None):
        '''Callback for "Show images in selection" popup item.'''
        show_keys = set()
        for i, sel in list(self.selection.items()):
            keys = self.key_lists[i][sel]
            show_keys.update([tuple(k) for k in keys])
        if len(show_keys)>10:
            dlg = wx.MessageDialog(self, 'You are about to open %s images. '
                                   'This may take some time depending on your '
                                   'settings. Continue?'%(len(show_keys)),
                                   'Warning', wx.YES_NO|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response != wx.ID_YES:
                return
        logging.info('Opening %s images.'%(len(show_keys)))
        for key in sorted(show_keys):
            if len(key) == len(image_key_columns()):
                imagetools.ShowImage(key, p.image_channel_colors, parent=self)
            else:
                imview = imagetools.ShowImage(key[:-1], p.image_channel_colors, parent=self)
                imview.SelectObject(key)
            
    def show_selection_in_table(self, evt=None):
        '''Callback for "Show selection in a table" popup item.'''
        for i, sel in list(self.selection.items()):
            keys = self.key_lists[i][sel].T.astype('object')
            if len(keys) > 0:
                xpoints = self.x_points[i][sel]
                ypoints = self.y_points[i][sel]
                table_data = np.vstack((keys, xpoints, ypoints)).T
                column_labels = []
                if self.is_per_image_data():
                    column_labels = list(image_key_columns())
                    group = 'Image'
                elif self.is_per_object_data():
                    column_labels = list(object_key_columns())
                    group = 'Object'
                key_col_indices = list(range(len(column_labels)))
                column_labels += [self.get_current_x_measurement_name(), 
                                  self.get_current_y_measurement_name()]
                grid = tableviewer.TableViewer(self, title='Selection from collection %d in scatter'%(i))
                grid.table_from_array(table_data, column_labels, group, key_col_indices)
                grid.set_fitted_col_widths()
                grid.Show()
            else:
                logging.info('No points were selected in collection %d'%(i))
            
    def on_new_collection_from_filter(self, evt):
        '''Callback for "Collection from filter" popup menu options.'''
        assert self.key_lists, 'Can not create a collection from a filter since image keys have not been set for this plot.'
        filter = self.popup_menu_filters[evt.Id]   
        keys = sorted(db.GetFilteredImages(filter))
        key_lists = []
        xpoints = []
        ypoints = []
        sel_keys = []
        sel_xs = []
        sel_ys = []
        for c, col in enumerate(self.subplot.collections):
            sel_indices = []
            unsel_indices = []
            # Find indices of keys that fall in the filter.
            # Improved performance: |N|log(|F|) N = data points, F = filterd points
            # Assumes that the filtered image keys are in order
            if self.is_per_object_data():
                collection_keys = [tuple(k[:-1]) for k in self.key_lists[c]]
            else:
                collection_keys = [tuple(k) for k in self.key_lists[c]]
            for i, key in enumerate(collection_keys):
                idx = bisect(keys, key) - 1
                if keys[idx] == key:
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
            indices = list(range(len(col.get_offsets())))
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
    
    def show_popup_menu(self, xxx_todo_changeme1, data):
        (x,y) = xxx_todo_changeme1
        self.popup_menu_filters = {}
        popup = wx.Menu()

        loadimages_table_item = popup.Append(-1, 'Create gated table for CellProfiler LoadImages')
        selected_gate = self.configpanel.gate_choice.get_gatename_or_none()
        selected_gates = []
        if selected_gate:
            selected_gates = [selected_gate]
        self.Bind(wx.EVT_MENU, 
                  lambda e:ui.prompt_user_to_create_loadimages_table(self, selected_gates), 
                  loadimages_table_item)
        
        show_images_in_gate_item = popup.Append(-1, 'Show images in gate')
        show_images_in_gate_item.Enable(selected_gate is not None)
        self.Bind(wx.EVT_MENU, self.show_images_from_gate, show_images_in_gate_item)
        if p.object_table:
            show_objects_in_gate_item = popup.Append(-1, 'Show %s in gate (montage)'%(p.object_name[1]))
            show_objects_in_gate_item.Enable(selected_gate is not None)
            self.Bind(wx.EVT_MENU, self.show_objects_from_gate, show_objects_in_gate_item)

        popup.AppendSeparator()
        
        show_images_item = popup.Append(-1, 'View images from selection')
        show_images_item.Enable(not self.selection_is_empty())
        self.Bind(wx.EVT_MENU, self.show_images_from_selection, show_images_item)
        
        if p.object_table:
            show_objects_item = popup.Append(-1, 'Show %s in selection'%(p.object_name[1]))
            if self.selection_is_empty():
                show_objects_item.Enable(False)
            self.Bind(wx.EVT_MENU, self.show_objects_from_selection, show_objects_item)
        
        show_imagelist_item = popup.Append(-1, 'Show selection in table')
        if self.selection_is_empty():
            show_imagelist_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.show_selection_in_table, show_imagelist_item)
        
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
        popup.Append(-1, 'Create collection from filter', submenu)
        
        self.PopupMenu(popup, (x,y))
            
    def get_key_lists(self):
        return self.key_lists

    def get_colors(self):
        if self.colors:
            colors = self.colors
        elif max(list(map(len, self.x_points)))==0:
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
            if self.navtoolbar:
                self.navtoolbar.reset_history()
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
            self.subplot.set_xticks(list(range(len(x_categories))))
            self.subplot.set_xticklabels(sorted(x_categories))
            self.figure.autofmt_xdate() # rotates and shifts xtick-labels so they look nice
        if yvalmap:
            self.subplot.set_yticks(list(range(len(y_categories))))
            self.subplot.set_yticklabels(sorted(y_categories))
        
        if len(self.x_points) > 1:
            if self.legend:
                self.legend.disconnect_bindings()
            self.legend = self.subplot.legend(fancybox=True)
            try:
                self.legend.draggable(True)
            except:
                self.legend = DraggableLegend(self.legend)
            
        # Set axis scales
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', base=2.1)
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', base=2.1)
            
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
        
        if self.navtoolbar:
            self.navtoolbar.reset_history()
        
    def get_toolbar(self):
        if not self.navtoolbar:
            self.navtoolbar = CustomNavToolbar(self.canvas)
            self.navtoolbar.Realize()
        return self.navtoolbar
    
    def set_x_scale(self, scale):
        self.x_scale = scale
        # Set log axes and print warning if any values will be masked out
        ignored = 0
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', base=2.1, nonpositive='mask')
            ignored = sum([len(self.x_points[i][xs <= 0]) 
                           for i, xs in enumerate(self.x_points) if len(xs) > 0])
        if ignored > 0:
            logging.warn('Scatter masked out %s points with non-positive X values.'%(ignored))        
            
    def set_y_scale(self, scale):
        self.y_scale = scale
        # Set log axes and print warning if any values will be masked out
        ignored = 0
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', base=2.1, nonpositive='mask')
            ignored += sum([len(self.y_points[i][ys <= 0]) 
                            for i, ys in enumerate(self.y_points) if len(ys) > 0])
        if ignored > 0:
            logging.warn('Scatter masked out %s points with non-positive Y values.'%(ignored))  
    
    def set_x_label(self, label):
        self.x_label = label
        if self.x_scale == LOG_SCALE:
            self.x_label = 'Log(%s)'%(self.x_label)

    
    def set_y_label(self, label):
        self.y_label = label
        if self.y_scale == LOG_SCALE:
            self.y_label = 'Log(%s)'%(self.y_label)
        

class Scatter(wx.Frame, CPATool):
    '''
    A very basic scatter plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Scatter Plot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        self.SetBackgroundColour("white")
        
        figpanel = ScatterPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
                
        configpanel = ScatterControlPanel(self, figpanel)
        figpanel.set_configpanel(configpanel)
        sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetToolBar(figpanel.get_toolbar())            
        self.SetSizer(sizer)
        self.fig = figpanel
        #
        # Forward save and load settings functionality to the configpanel
        #
        self.save_settings = configpanel.save_settings
        self.load_settings = configpanel.load_settings

    # Hack: See http://stackoverflow.com/questions/6124419/matplotlib-navtoolbar-doesnt-realize-in-wx-2-9-mac-os-x
    def SetToolBar(self, toolbar):
        from matplotlib.backends.backend_wx import _load_bitmap
        toolbar.Hide()
        tb = self.CreateToolBar((wx.TB_HORIZONTAL|wx.TB_TEXT))
        toolbar.tb = tb

        _NTB2_HOME = wx.NewId()
        _NTB2_BACK = wx.NewId()
        _NTB2_FORWARD = wx.NewId()
        _NTB2_PAN = wx.NewId()
        _NTB2_ZOOM = wx.NewId()
        _NTB2_SAVE = wx.NewId()
        _NTB2_SUBPLOT = wx.NewId()
        tb.AddTool(_NTB2_HOME, "", _load_bitmap('home.png'), 'Home')
        tb.AddTool(_NTB2_BACK, "", _load_bitmap('back.png'), 'Back')
        tb.AddTool(_NTB2_FORWARD, "", _load_bitmap('forward.png'), 'Forward')

        tb.AddCheckTool(_NTB2_PAN, "", _load_bitmap('move.png'), shortHelp='Pan', longHelp='Pan with left, zoom with right')
        tb.AddCheckTool(_NTB2_ZOOM, "", _load_bitmap('zoom_to_rect.png'), shortHelp='Zoom', longHelp='Zoom to rectangle')

        tb.AddSeparator()
        tb.AddTool(_NTB2_SUBPLOT, "", _load_bitmap('subplots.png'), 'Configure subplots')
        tb.AddTool(_NTB2_SAVE, "", _load_bitmap('filesave.png'), 'Save plot')

        def on_toggle_pan(evt):
            tb.ToggleTool(_NTB2_ZOOM, False)
            evt.Skip()

        def on_toggle_zoom(evt):
            tb.ToggleTool(_NTB2_PAN, False)
            evt.Skip()

        self.Bind(wx.EVT_TOOL, toolbar.home, id=_NTB2_HOME)
        self.Bind(wx.EVT_TOOL, toolbar.forward, id=_NTB2_FORWARD)
        self.Bind(wx.EVT_TOOL, toolbar.back, id=_NTB2_BACK)
        self.Bind(wx.EVT_TOOL, toolbar.zoom, id=_NTB2_ZOOM)
        self.Bind(wx.EVT_TOOL, toolbar.pan, id=_NTB2_PAN)
        self.Bind(wx.EVT_TOOL, self.configure_subplots, id=_NTB2_SUBPLOT)
        self.Bind(wx.EVT_TOOL, toolbar.save_figure, id=_NTB2_SAVE)
        self.Bind(wx.EVT_TOOL, on_toggle_zoom, id=_NTB2_ZOOM)
        self.Bind(wx.EVT_TOOL, on_toggle_pan, id=_NTB2_PAN)

        tb.Realize()
        # Hack end

    def configure_subplots(self, *args):
        # Fixed MPL subplot window generator
        from matplotlib.backends.backend_wx import _set_frame_icon, FigureManagerWx
        from matplotlib.widgets import SubplotTool

        frame = wx.Frame(None, -1, "Configure subplots")
        _set_frame_icon(frame)

        toolfig = Figure((6, 3))
        canvas = FigureCanvasWxAgg(frame, -1, toolfig)

        # Create a figure manager to manage things
        FigureManagerWx(canvas, 1, frame)

        # Now put all into a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        frame.SetSizer(sizer)
        frame.Fit()
        SubplotTool(self.fig.canvas.figure, toolfig)
        frame.Show()


class CustomNavToolbar(NavigationToolbar2WxAgg):
    '''wx/mpl NavToolbar hack with an additional tools user interaction.
    This class is necessary because simply adding a new togglable tool to the
    toolbar won't (1) radio-toggle between the new tool and the pan/zoom tools.
    (2) disable the pan/zoom tool modes in the associated subplot(s).
    '''
    def __init__(self, canvas):
        super(CustomNavToolbar, self).__init__(canvas)
        self.PAN = self.wx_ids['Pan']
        self.ZOOM =  self.wx_ids['Zoom']
        self.pan_tool  = self.FindById(self.PAN)
        self.zoom_tool = self.FindById(self.ZOOM)
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.zoom_tool)
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.pan_tool)

        self.user_tools = {}   # user_tools['tool_mode'] : wx.ToolBarToolBase

        self.InsertSeparator(5)
        self.add_user_tool('lasso', 6, get_icon("lasso_tool").ConvertToBitmap(), True, 'Lasso')
        #self.add_user_tool('gate', 7, get_icon("gate_tool").ConvertToBitmap(), True, 'Gate')
        
    def add_user_tool(self, mode, pos, bmp, istoggle=True, shortHelp=''):
        '''Adds a new user-defined tool to the toolbar.
        mode -- the value that CustomNavToolbar.get_mode() will return if this  
                tool is toggled on
        pos -- the position in the toolbar to add the icon
        bmp -- a wx.Bitmap of the icon to use in the toolbar
        isToggle -- whether or not the new tool toggles on/off with the other 
                    togglable tools
        shortHelp -- the tooltip shown to the user for the new tool
        '''
        tool_id = wx.NewId()
        self.user_tools[mode] = self.InsertTool(pos, tool_id, "", bmp, kind=wx.ITEM_CHECK if istoggle else wx.ITEM_NORMAL, shortHelp=shortHelp)
        self.Bind(wx.EVT_TOOL, self.on_toggle_user_tool, self.user_tools[mode])

    def get_mode(self):
        '''Use this rather than navtoolbar.mode
        '''
        for mode, tool in list(self.user_tools.items()):
            if tool.IsToggled():
                return mode
        return self.mode
        
    def untoggle_mpl_tools(self):
        '''Hack city: Since I can't figure out how to change the way the 
        associated subplot(s) handles mouse events: I generate events to turn
        off whichever tool mode is enabled (if any). 
        This function needs to be called whenever any user-defined tool 
        (eg: lasso) is clicked.
        '''
        if self.pan_tool.IsToggled():
            wx.PostEvent(
                self.GetEventHandler(), 
                wx.CommandEvent(wx.EVT_TOOL.typeId, self.PAN)
            )
            self.ToggleTool(self.PAN, False)
        elif self.zoom_tool.IsToggled():
            wx.PostEvent(
                self.GetEventHandler(),
                wx.CommandEvent(wx.EVT_TOOL.typeId, self.ZOOM)
            )
            self.ToggleTool(self.ZOOM, False)
            
    def toggle_user_tool(self, mode_name, state):
        '''mode_name -- the mode name given to the tool when added with
        add_user_tool
        state -- True or False
        '''
        self.ToggleTool(self.user_tools[mode_name].Id, state)
    
    def on_toggle_user_tool(self, evt):
        '''User tool click handler.
        '''
        if evt.Checked():
            self.untoggle_mpl_tools()
            #untoggle other user tools
            for tool in list(self.user_tools.values()):
                if tool.Id != evt.Id:
                    self.ToggleTool(tool.Id, False)
            
    def on_toggle_pan_zoom(self, evt):
        '''Called when pan or zoom is toggled. 
        We need to manually untoggle user-defined tools.
        '''
        if evt.Checked():
            for tool in list(self.user_tools.values()):
                self.ToggleTool(tool.Id, False)
        # Make sure the regular pan/zoom handlers get the event
        evt.Skip()
        
    def reset_history(self):
        '''Clear/reset the toolbar history.
        '''
        self._nav_stack.clear()
        self.push_current()
    
if __name__ == "__main__":
    app = wx.App()
    logging.basicConfig(level=logging.DEBUG,)
        
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
##        p.load_file('/Users/afraser/cpa_example/example2.properties')
        if not p.show_load_dialog():
            print('Scatterplot requires a properties file.  Exiting.')
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()
    scatter = Scatter(None)
    scatter.Show()
    
    app.MainLoop()
    
    #
    # Kill the Java VM
    #
    try:
        import javabridge
        javabridge.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print("Caught exception while killing VM")
