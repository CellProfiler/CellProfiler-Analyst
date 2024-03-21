
from .dbconnect import DBConnect
from .properties import Properties
from . import datamodel
from . import guiutils as ui 
from wx.adv import OwnerDrawnComboBox as ComboBox
from . import sqltools as sql
import logging
import numpy as np
import sys
import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

from .cpatool import CPATool

p = Properties()
db = DBConnect()

NO_GROUP = "Whole column"
ID_EXIT = wx.NewId()
SELECT_MULTIPLE = '<MULTIPLE SELECTED>'

class DataSourcePanel(wx.Panel):
    '''
    A panel with controls for selecting the source data for a boxplot 
    '''
    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        # the panel to draw charts on
        self.SetBackgroundColour('white') # color for the background of panel
        self.figpanel = figpanel
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.x_columns = [] # column names to plot if selecting multiple columns

        self.table_choice = ui.TableComboBox(self, -1, style=wx.CB_READONLY)
        self.x_choice = ComboBox(self, -1, size=(200,-1), style=wx.CB_READONLY)
        self.x_multiple = wx.Button(self, -1, 'select multiple')
        self.group_choice = ComboBox(self, -1, choices=[NO_GROUP]+p._groups_ordered, style=wx.CB_READONLY)
        self.group_choice.Select(0)
        self.filter_choice = ui.FilterComboBox(self, style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_column_fields()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "table:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.table_choice, 1, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(wx.StaticText(self, -1, "measurement:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(self.x_multiple, 0, wx.EXPAND|wx.TOP, 2)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 3, 0)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "group x-axis by:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.group_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 3, 0)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "filter:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 3, 0)
        
        sizer.Add(self.update_chart_btn)    

        self.x_multiple.Bind(wx.EVT_BUTTON, self.on_select_multiple)
        self.table_choice.Bind(wx.EVT_COMBOBOX, self.on_table_selected)
        self.x_choice.Bind(wx.EVT_COMBOBOX, self.on_column_selected)
        self.update_chart_btn.Bind(wx.EVT_BUTTON, self.update_figpanel)

        self.SetSizer(sizer)
        self.Show(1)

    def on_select_multiple(self, evt):
        tablename = self.table_choice.GetString(self.table_choice.GetSelection())
        column_names = self.get_numeric_columns_from_table(tablename)
        dlg = wx.MultiChoiceDialog(self, 
                                   'Select the columns you would like to plot',
                                   'Select Columns', column_names)
        dlg.SetSelections([column_names.index(v) for v in self.x_columns])
        if (dlg.ShowModal() == wx.ID_OK):
            self.x_choice.SetValue(SELECT_MULTIPLE)
            self.x_columns = [column_names[i] for i in dlg.GetSelections()]
            self.group_choice.Disable()
            self.group_choice.SetStringSelection(NO_GROUP)
        
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
        self.group_choice.Enable()
        self.x_columns = []
        self.update_column_fields()
        
    def on_column_selected(self, evt):
        self.group_choice.Enable()        
    
    def update_column_fields(self):
        tablename = self.table_choice.GetString(self.table_choice.GetSelection())
        fieldnames = self.get_numeric_columns_from_table(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.Append(SELECT_MULTIPLE)
        self.x_choice.SetSelection(0)

    def get_numeric_columns_from_table(self, table):
        ''' Fetches names of numeric columns for the given table. '''
        measurements = db.GetColumnNames(table)
        types = db.GetColumnTypes(table)
        return [m for m,t in zip(measurements, types) if t in (float, int)]
        
    def update_figpanel(self, evt=None):
        table = self.table_choice.Value
        fltr = self.filter_choice.get_filter_or_none()
        grouping = self.group_choice.Value
        if self.x_choice.Value == SELECT_MULTIPLE:
            points_dict = {}
            for col in self.x_columns:
                pts = self.loadpoints(table, col, fltr, NO_GROUP)
                for k in list(pts.keys()): assert k not in points_dict
                points_dict.update(pts)
        else:
            col = self.x_choice.Value
            points_dict = self.loadpoints(table, col, fltr, grouping)
        
        # Check if the user is creating a plethora of plots by accident
        if 100 >= len(points_dict) > 25:
            res = wx.MessageDialog(self, 'Are you sure you want to show %s box '
                                   'plots on one axis?'%(len(points_dict)), 
                                   'Warning', style=wx.YES_NO|wx.NO_DEFAULT
                                   ).ShowModal()
            if res != wx.ID_YES:
                return
        elif len(points_dict) > 100:
            wx.MessageBox('Sorry, boxplot can not show more than 100 plots on\n'
                          'a single axis. Your current settings would plot %d.\n'
                          'Try using a filter to narrow your query.'
                          %(len(points_dict)), 'Too many groups to plot')
            return

        self.figpanel.setpoints(points_dict)
        if self.group_choice.Value != NO_GROUP:
            self.figpanel.set_x_axis_label(grouping)
            self.figpanel.set_y_axis_label(self.x_choice.Value)
        self.figpanel.draw()
        
    def loadpoints(self, tablename, col, fltr=None, grouping=NO_GROUP):
        '''
        Returns a dict mapping x label values to lists of values from col
        '''
        q = sql.QueryBuilder()
        select = [sql.Column(tablename, col)]
        if grouping != NO_GROUP:
            dm = datamodel.DataModel()
            group_cols = dm.GetGroupColumnNames(grouping, include_table_name=True)
            select += [sql.Column(*col.split('.')) for col in group_cols]
        q.set_select_clause(select)
        if fltr is not None:
            q.add_filter(fltr)

        res = db.execute(str(q))
        res = np.array(res, dtype=object)
        # replaces Nones with NaNs
        for row in res:
            if row[0] is None:
                row[0] = np.nan
        
        points_dict = {}
        if self.group_choice.Value != NO_GROUP:
            for row in res:
                groupkey = tuple(row[1:])
                points_dict[groupkey] = points_dict.get(groupkey, []) + [row[0]]
        else:
            points_dict = {col : [r[0] for r in res]}
        return points_dict

    def save_settings(self):
        '''
        Called when saving a workspace to file.
        returns a dictionary mapping setting names to values encoded as strings
        '''
        if self.x_choice.Value == SELECT_MULTIPLE:
            cols = self.x_columns
        else:
            cols = [self.x_choice.GetString(self.x_choice.GetSelection())]
        return {'table'  : self.table_choice.Value,
                'x-axis' : ','.join(cols),
                'filter' : self.filter_choice.Value,
                'x-lim'  : self.figpanel.subplot.get_xlim(),
                'y-lim'  : self.figpanel.subplot.get_ylim(),
##                'grouping': self.group_choice.Value,
##                'version': '1',
                }
    
    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
##        if 'version' not in settings:
##            settings['grouping'] = NO_GROUP
##            settings['version'] = '1'
        if 'table' in settings:
            self.table_choice.SetStringSelection(settings['table'])
            self.update_column_fields()
        if 'x-axis' in settings:
            cols = list(map(str.strip, settings['x-axis'].split(',')))
            if len(cols) == 1:
                self.x_choice.SetStringSelection(cols[0])
            else:
                self.x_choice.SetValue(SELECT_MULTIPLE)
                self.x_columns = cols
        if 'filter' in settings:
            self.filter_choice.SetStringSelection(settings['filter'])
        self.update_figpanel()
        if 'x-lim' in settings:
            self.figpanel.subplot.set_xlim(eval(settings['x-lim']))
        if 'y-lim' in settings:
            self.figpanel.subplot.set_ylim(eval(settings['y-lim']))
        self.figpanel.draw()


class BoxPlotPanel(FigureCanvasWxAgg):
    def __init__(self, parent, points, **kwargs):
        '''
        points -- a dictionary mapping x axis values to lists of values to plot
        '''
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)
        self.canvas = self.figure.canvas
        self.SetMinSize((100,100))
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')
        
        self.navtoolbar = None
        self.setpoints(points)
        
    def setpoints(self, points):
        '''
        Updates the data to be plotted and redraws the plot.
        points - list of array samples, where each sample will be plotted as a 
                 separate box plot against the same y axis
        '''
        self.xlabels = []
        self.points = []
        ignored = 0
        for label, values in sorted(points.items()):
            if type(label) in [tuple, list]:
                self.xlabels += [','.join([str(l) for l in label])]
            else:
                self.xlabels += [label]
            self.points += [np.array(values).astype('f')[~ np.isnan(values)]]
            ignored += len(np.array(values)[np.isnan(values)])
        
        if not hasattr(self, 'subplot'):
            self.subplot = self.figure.add_subplot(111)
        self.subplot.clear()
        # nothing to plot?
        if len(self.points)==0:
            logging.warn('No data to plot.')
            return
        self.subplot.boxplot(self.points, sym='k.')
        if len(self.points) > 1:
            self.figure.autofmt_xdate()
        self.subplot.set_xticklabels(self.xlabels)
        self.reset_toolbar()
        if ignored == 0:
            logging.info('Boxplot: Plotted %s points.'%(sum(map(len, self.points))))
        else:
            logging.warn('Boxplot: Plotted %s points. Ignored %s NaNs.'
                          %(sum(map(len, self.points)), ignored))
        
    def set_x_axis_label(self, label):
        self.subplot.set_xlabel(label)
    
    def set_y_axis_label(self, label):
        self.subplot.set_ylabel(label)
    
    def get_point_lists(self):
        return self.points
    
    def get_xlabels(self):
        return self.xlabels
    
    def get_toolbar(self):
        if not self.navtoolbar:
            self.navtoolbar = NavigationToolbar(self.canvas)
            self.navtoolbar.DeleteToolByPos(6)
        return self.navtoolbar

    def reset_toolbar(self):
        # Cheat since there is no way reset
        if self.navtoolbar:
            self.navtoolbar._nav_stack.clear()
            self.navtoolbar.push_current()


class BoxPlot(wx.Frame, CPATool):
    '''
    A very basic boxplot with controls for setting it's data source.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='BoxPlot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        self.SetBackgroundColour("white")
        points = {}
        figpanel = BoxPlotPanel(self, points)
        configpanel = DataSourcePanel(self, figpanel)
        self.SetToolBar(figpanel.get_toolbar())
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
        sizer.Add(configpanel, 0, wx.EXPAND|wx.ALL, 5)
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

                    
if __name__ == "__main__":
    app = wx.App()
    logging.basicConfig(level=logging.DEBUG,)

    if len(sys.argv) > 1:
        # Load a properties file if passed in args
        p = Properties()
        p.LoadFile(sys.argv[1])
    elif not p.show_load_dialog():
        print('BoxPlot requires a properties file.  Exiting.')
        # necessary in case other modal dialogs are up
        wx.GetApp().Exit()
        sys.exit()

    boxplot = BoxPlot(None)
    boxplot.Show()
    
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
