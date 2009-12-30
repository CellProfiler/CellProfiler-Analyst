from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, image_key_columns
from MulticlassSQL import filter_table_prefix
from PlateMapPanel import *
from PlotPanel import *
from Properties import Properties
from wx.combo import OwnerDrawnComboBox as ComboBox
import ImageTools
import numpy as np
import os
import sys
import re
import wx
import wx.combo
from matplotlib.widgets import Lasso, RectangleSelector
from matplotlib.nxutils import points_inside_poly
from matplotlib.colors import colorConverter
from matplotlib.collections import RegularPolyCollection
from matplotlib.pyplot import figure, show, cm

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


class DataSourcePanel(wx.Panel):
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
        self.Bind(wx.EVT_SIZE, self._onsize)
        
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
        fields = '%s.%s, %s.%s'%(tablename, xpoints, tablename, ypoints)
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
        
    def _onsize(self, evt):
        self.figpanel._SetSize()
        evt.Skip()
        

class ScatterPanel(PlotPanel):
    '''
    ScatterPanel contains the guts for drawing scatter plots to a PlotPanel.
    '''
    def __init__(self, parent, point_lists, clr_list=None, **kwargs):
        PlotPanel.__init__(self, parent, (255,255,255), **kwargs)
        
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.x_label = ''
        self.y_label = ''
        self.sel     = {}
        self.set_point_lists(point_lists, clr_list)
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.show_popup_menu)
        
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
            new_sel = np.nonzero(points_inside_poly(self.xys[c], verts))[0]
            if self.sel_key == None:
                self.sel[c] = new_sel
            elif self.sel_key == 'shift':
                self.sel[c] = set(self.sel.get(c,[])).union(new_sel)
            elif self.sel_key == 'alt':
                self.sel[c] = set(self.sel.get(c,[])).difference(new_sel)
            
            # Color the points
            facecolors = collection.get_facecolors()
            for i in range(len(self.point_lists[c])):
                if i in self.sel[c]:
                    facecolors[i] = SELECTED_COLOR
                else:
                    facecolors[i] = self.colors[c]

        self.canvas.draw_idle()
        
    def on_press(self, evt):
        if evt.button == 1:
            self.sel_key = evt.key
            if self.canvas.widgetlock.locked(): return
            if evt.inaxes is None: return
            
            self.lasso = Lasso(evt.inaxes, (evt.xdata, evt.ydata), self.lasso_callback)
            # acquire a lock on the widget drawing
            self.canvas.widgetlock(self.lasso)
        else:
            self.canvas.Parent.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
        
    def on_release(self, event):
        # Note: lasso_callback is not called on click without drag so we release
        #   the lock here to handle this case as well.
        if self.__dict__.has_key('lasso') and self.lasso:
            self.canvas.draw_idle()
            self.canvas.widgetlock.release(self.lasso)
            del self.lasso
        
    def show_popup_menu(self, (x, y), data):
        pass
#        popup = wx.Menu()
#        test = wx.MenuItem(popup, -1, 'test')
#        popup.AppendItem(test)
#        def test_cb(evt):
#            print data
#        self.PopupMenu(popup, (x,y))
        
    def set_point_lists(self, points, colors=None):
        '''
        points - a list of lists of points
        colors - a list of colors to be applied to each inner list of points
        '''
        if len(points)==0: points = [[]]
        points = [np.array(pl).astype(float) for pl in points]
        self.point_lists = points
        
        # Create and clear the subplot
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
        
        # Label the axes
        self.subplot.set_xlabel(self.x_label)
        self.subplot.set_ylabel(self.y_label)
        
        # Set axis scales
        if self.x_scale == LOG_SCALE:
            self.subplot.set_xscale('log', basex=2.1)
        if self.y_scale == LOG_SCALE:
            self.subplot.set_yscale('log', basey=2.1)
            
        # Choose colors from jet colormap starting with light blue (0.28)
        if colors is None:
            vals = np.arange(0.28, 1.28, 1./len(points)) % 1.
            colors = np.array([colorConverter.to_rgba(cm.jet(val), alpha=0.75) 
                               for val in vals])
        self.colors = colors
        
        # Each point list is converted to a separate point collection
        self.collections = []
        self.xys = []
        for plot_pts, color in zip(points, colors):
            data = [Datum(xy, color) for xy in plot_pts]
            facecolors = [d.color for d in data]
            self.xys.append([(d.x, d.y) for d in data])

            collection = RegularPolyCollection(
                self.figure.get_dpi(), 1, sizes=(25,),
                facecolors = facecolors,
                offsets = self.xys[-1] or None,
                transOffset = self.subplot.transData,
                edgecolor = 'none',
                alpha = 0.75)
    
            self.subplot.add_collection(collection)

        # Stop if there is no data in any of the point lists
        if max(map(len, points))==0:
            return

         # Clip negative values if in log space
        if self.x_scale == LOG_SCALE:
            logging.warn('Discarding points with negative x-values.')
            points = [points[i][c[:,0]>3] for i,c in enumerate(points)]
        if self.y_scale == LOG_SCALE:
            logging.warn('Discarding points with negative y-values.')
            points = [points[i][c[:,1]>3] for i,c in enumerate(points)]
        
        # Add padding around the points in the plot
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
    
    def draw(self):
        self.canvas.draw()
        

class Scatter(wx.Frame):
    '''
    A very basic scatter plot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600)):
        wx.Frame.__init__(self, parent, -1, size=size, title='Scatter Plot')
        self.SetName('Scatter')
        
        points = []
#        points = [[],
#                  [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
#                  [],
#                  [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7)],
#                  [],]
        clrs = [(0., 0.62, 1., 0.75),
                (0.1, 0.2, 0.3, 0.75)]

        
        figpanel = ScatterPanel(self, points)
        configpanel = DataSourcePanel(self, figpanel)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
        sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        



def LoadProperties():
    import os
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])  # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        print 'Scatterplot requires a properties file.  Exiting.'
        sys.exit()

            
if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    logging.basicConfig(level=logging.DEBUG,)
        
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        LoadProperties()

    import MulticlassSQL
    MulticlassSQL.CreateFilterTables()
    
    scatter = Scatter(None)
    scatter.Show()
    
    app.MainLoop()