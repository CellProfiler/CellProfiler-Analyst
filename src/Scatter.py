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
from matplotlib.pyplot import figure, show

p = Properties.getInstance()
db = DBConnect.getInstance()

NO_FILTER = 'No filter'

ID_EXIT = wx.NewId()
LOG_SCALE    = 'log'
LINEAR_SCALE = 'linear'


class Datum:
    colorin = colorConverter.to_rgba('red', alpha=0.75)
    colorout = colorConverter.to_rgba((0., 0.61960784, 1.), alpha=0.75)
    def __init__(self, x, y, include=False):
        self.x = x
        self.y = y
        if include: self.color = self.colorin
        else: self.color = self.colorout


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
            tables += ', `%s`'%(filter_table_prefix+filter) 
            filter_clause = ' AND '.join(['%s.%s=`%s`.%s'%(tablename, id, filter_table_prefix+filter, id) 
                                          for id in db.GetLinkingColumnsForTable(tablename)])
            where_clause = 'WHERE %s'%(filter_clause)
        return [db.execute('SELECT %s FROM %s %s'%(fields, tables, where_clause))]
        
    def _onsize(self, evt):
        self.figpanel._SetSize()
        evt.Skip()
        

class ScatterPanel(PlotPanel):
    def __init__(self, parent, point_lists, clr_list, **kwargs):
        PlotPanel.__init__(self, parent, **kwargs)
        self.SetColor((255, 255, 255))
        
        self.clr_list = clr_list
        self.x_scale = LINEAR_SCALE
        self.y_scale = LINEAR_SCALE
        self.x_label = ''
        self.y_label = ''
        self.setpointslists(point_lists)
        
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.show_popup_menu)
        
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)

    def callback(self, verts):
        # Note: If the mouse is released outside of the canvas, (None,None) is
        #   returned as the last coordinate pair.
        # Cancel selection if user releases outside the canvas.
        for v in verts:
            if None in v:
                return
            
        xys = (self.xys - np.min(self.xys)) / np.max(self.xys)
        verts = (verts - np.min(self.xys)) / np.max(self.xys)

        # Build the selection
        new_sel = np.nonzero(points_inside_poly(xys, verts))[0]
        if self.sel_key == None:
            self.sel = new_sel
        elif self.sel_key == 'shift':
            self.sel = set(self.sel).union(new_sel)
        elif self.sel_key == 'alt':
            self.sel = set(self.sel).difference(new_sel)
            
        # Color the points
        facecolors = self.collection.get_facecolors()
        for i in range(self.n_points):
            if i in self.sel:
                facecolors[i] = Datum.colorin
            else:
                facecolors[i] = Datum.colorout

        self.canvas.draw_idle()
        
    def on_press(self, evt):
        if evt.button == 1:
            self.sel_key = evt.key
            if self.canvas.widgetlock.locked(): return
            if evt.inaxes is None: return
            
            self.lasso = Lasso(evt.inaxes, (evt.xdata, evt.ydata), self.callback)
#             acquire a lock on the widget drawing
            self.canvas.widgetlock(self.lasso)
        else:
            self.canvas.Parent.show_popup_menu((evt.x, self.canvas.GetSize()[1]-evt.y), None)
        
    def on_release(self, event):
        # Note: callback is not called on click without drag so we release the
        #   lock here to handle this case as well.
        if self.__dict__.has_key('lasso') and self.lasso:
            self.canvas.draw_idle()
            self.canvas.widgetlock.release(self.lasso)
            del self.lasso
            
    def show_popup_menu(self, (x, y), data):
        popup = wx.Menu()
        test = wx.MenuItem(popup, -1, 'test')
        popup.AppendItem(test)
        def test_cb(evt):
            print data
        self.PopupMenu(popup, (x,y))
        
    def setpointslists(self, points):
        self.point_lists = np.array(points).astype(float)
        plot_pts = self.point_lists[0]
        
        data = [Datum(*xy) for xy in plot_pts]
        self.n_points = len(data)

        facecolors = [d.color for d in data]
        self.xys = [(d.x, d.y) for d in data]

        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
            
        self.collection = RegularPolyCollection(
            self.figure.get_dpi(), 1, sizes=(25,),
            facecolors = facecolors,
            offsets = self.xys,
            transOffset = self.subplot.transData,
            edgecolor = 'none',
            alpha = 0.75)

        self.subplot.add_collection(self.collection)
        
        #Draw data.
        for i, pt_list in enumerate(self.point_lists):
            if len(pt_list)==0:
                logging.error('No points to plot!')
                return
            
            # Label axes
            self.subplot.set_xlabel(self.x_label)
            self.subplot.set_ylabel(self.y_label)
            
            # Set axis scales
            # and clip negative values if in log space
            if self.x_scale == LOG_SCALE:
                pt_list = pt_list[(pt_list[:,0]>0)]
                self.subplot.set_xscale('log', basex=2.1)
            if self.y_scale == LOG_SCALE:
                pt_list = pt_list[(pt_list[:,1]>0)]
                self.subplot.set_yscale('log', basey=2.1)
            
            # Pad all sides
            xmin = np.nanmin(pt_list[:,0])
            xmax = np.nanmax(pt_list[:,0])
            ymin = np.nanmin(pt_list[:,1])
            ymax = np.nanmax(pt_list[:,1])
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
    
    def getpointslists(self):
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
        
        points = [[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]]
        clrs = [[0, 158, 255], [1,2,3]]
        
        figpanel = ScatterPanel(self, points, clrs)
#        figpanel = cpfig.CPFigurePanel(self, -1)
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