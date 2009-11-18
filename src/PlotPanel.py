#!/usr/bin/env python

import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
import numpy as np
import wx
from matplotlib.figure import Figure
from DBConnect import DBConnect
from Properties import Properties
#matplotlib.interactive(True)
#matplotlib.use('WXAgg')

db = DBConnect.getInstance()
p = Properties.getInstance()

class CPFigurePanel(FigureCanvasWxAgg):
    
    def __init__(self, parent, id, subplots=None):
        '''Initialize the panel:
        
        parent   - parent window to this one, typically a CPFigureFrame
        id       - window ID
        subplots - 2-tuple indicating the layout of subplots inside the window
        '''
        self.figure = matplotlib.figure.Figure()
        super(FigureCanvasWxAgg,self).__init__(parent, id, figure=self.figure)
        
        if subplots:
            self.subplots = np.zeros(subplots, dtype=object)
            self.zoom_rects = np.zeros(subplots, dtype=object)
        
        wx.EVT_PAINT(self, self.on_paint)
#        self._resizeflag = False
#        self.Bind(wx.EVT_IDLE, self._onIdle)
#        self.Bind(wx.EVT_SIZE, self._onSize)
#        
#    def _onSize(self, event):
#        self._resizeflag = True
#
#    def _onIdle(self, evt):
#        if self._resizeflag:
#            self._resizeflag = False
#            self._SetSize()
#
#    def _SetSize(self):
#        self.refresh_canvas()

    def clf(self):
        '''Clear the figure window, resetting the display'''
        self.figure.clf()
        self.subplots[:,:] = None
        self.zoom_rects[:,:] = None

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.draw(dc)
        event.Skip()
        del dc
        
    def subplot(self,x,y):
        """Return the indexed subplot
        
        x - column
        y - row
        """
        if not self.subplots[x,y]:
            rows, cols = self.subplots.shape
            plot = self.figure.add_subplot(cols,rows,x+y*rows+1)
            self.subplots[x,y] = plot
        return self.subplots[x,y]

    def set_subplot_title(self,title,x,y):
        """Set a subplot's title in the standard format
        
        title - title for subplot
        x - subplot's column
        y - subplot's row
        """
        self.subplot(x,y).set_title(title,
                                   fontname=cpprefs.get_title_font_name(),
                                   fontsize=cpprefs.get_title_font_size())
        
    def clear_subplot(self, x, y):
        """Clear a subplot of its gui junk

        x - subplot's column
        y - subplot's row
        """
        axes = self.subplot(x,y)
        axes.clear()
        
    def subplot_imshow(self, x, y, image, title=None, clear=True,
                       colormap=None, colorbar=False, vmin=None, vmax=None):
        '''Show an image in a subplot
        
        x,y   - show image in this subplot
        image - image to show
        title - add this title to the subplot
        clear - clear the subplot axes before display if true
        colormap - for a grayscale or labels image, use this colormap
                   to assign colors to the image
        colorbar - display a colorbar if true
        ''' 
        if clear:
            self.clear_subplot(x, y)
        subplot = self.subplot(x,y)
        if colormap == None:
            result = subplot.imshow(image)
        else:
            result = subplot.imshow(image, colormap, vmin=vmin, vmax=vmax)
        if title != None:
            self.set_subplot_title(title, x, y)
        if colorbar:
            if self.colorbar.has_key(subplot):
                axc =self.colorbar[subplot]
            else:
                axc, kw = matplotlib.colorbar.make_axes(subplot)
                self.colorbar[subplot] = axc
            cb = matplotlib.colorbar.Colorbar(axc, result)
            result.colorbar = cb
        return result
    
    def subplot_imshow_color(self, x, y, image, title=None, clear=True, 
                             normalize=True):
        if clear:
            self.clear_subplot(x, y)
        if normalize:
            image = image.astype(np.float32)
            for i in range(3):
                im_min = np.min(image[:,:,i])
                im_max = np.max(image[:,:,i])
                if im_min != im_max:
                    image[:,:,i] -= im_min
                    image[:,:,i] /= (im_max - im_min)
        elif image.dtype.type == np.float64:
            image = image.astype(np.float32)
        subplot = self.subplot(x,y)
        result = subplot.imshow(image)
        if title != None:
            self.set_subplot_title(title, x, y)
        return result
    
    def subplot_imshow_labels(self, x,y,labels, title=None, clear=True):
        labels = renumber_labels_for_display(labels)
        cm = matplotlib.cm.get_cmap(cpprefs.get_default_colormap())
        return self.subplot_imshow(x,y,labels,title,clear,cm)
    
    def subplot_imshow_grayscale(self, x,y,image, title=None, clear=True,
                                 vmin=None, vmax=None):
        if image.dtype.type == np.float64:
            image = image.astype(np.float32)
        return self.subplot_imshow(x, y, image, title, clear, 
                                   matplotlib.cm.Greys_r,
                                   vmin, vmax)
    
    def subplot_imshow_bw(self, x,y,image, title=None, clear=True):
        return self.subplot_imshow(x, y, image, title, clear, 
                                   matplotlib.cm.binary_r)
    
    def subplot_table(self, x, y, statistics, 
                      ratio = (.6, .4),
                      loc = 'center',
                      cellLoc = 'left',
                      clear = True):
        """Put a table into a subplot
        
        x,y - subplot's column and row
        statistics - a sequence of sequences that form the values to
                     go into the table
        ratio - the ratio of column widths
        loc   - placement of the table within the axes
        cellLoc - alignment of text within cells
        """
        if clear:
            self.clear_subplot(x, y)
            
        table_axes = self.subplot(x, y)
        table = table_axes.table(cellText=statistics,
                                 colWidths=ratio,
                                 loc=loc,
                                 cellLoc=cellLoc)
        table_axes.set_frame_on(False)
        table_axes.set_axis_off()
        table.auto_set_font_size(False)
        table.set_fontsize(cpprefs.get_table_font_size())
        # table.set_fontfamily(cpprefs.get_table_font_name())

    def subplot_scatter(self, x, y, points, clear=True):
        """Put a scatterplot into a subplot
        
        x,y - subplot's column and row
        """
        self.figure.set_facecolor([1,1,1])
        self.figure.set_edgecolor([1,1,1])
        points = np.array(points)
        if clear:
            self.clear_subplot(x, y)
        
        axes = self.subplot(x, y)
        axes.xlabel = 'adsf'
        plot = axes.scatter(points[:,0], points[:,1], 
                            facecolor=[0.93, 0.27, 0.58], 
                            edgecolor='none',
                            alpha=0.75)
        
    def subplot_histogram(self, x, y, points, bins=10, clear=True):
        """Put a histogram into a subplot
        
        x,y - subplot's column and row
        """
        self.figure.set_facecolor([1,1,1])
        self.figure.set_edgecolor([1,1,1])
        points = np.array(points)
        if clear:
            self.clear_subplot(x, y)
        axes = self.subplot(x, y)
        axes.xlabel = 'adsf'
        plot = axes.hist(points, bins=bins, 
                         facecolor=[0.93, 0.27, 0.58],
                         edgecolor='none',
                         alpha=0.75)
        
    def refresh_canvas(self):
        self.figure.canvas.draw()



class ScatterController(object):
    '''
    Interface between ScatterControlPanel and figpanel
    '''
    def attach(self, figure, control_panel):
        self.figure = figure
        self.control_panel = control_panel
        
    def get_table_names(self):
        return db.GetTableNames()
    
    def get_column_names(self, table):
        ''' returns names of numeric columns '''
        cols = db.GetColumnNames(table)
        types = db.GetColumnTypes(table)
        return [c for c,t in zip(cols, types) if t in [float, int, long]]
    
    def update_figure(self):
        points = self.loadpoints(self.control_panel.get_table(),
                                 self.control_panel.get_x_column(),
                                 self.control_panel.get_y_column())
        self.figure.subplot_scatter(0, 0, points)

    def loadpoints(self, tablename, xpoints, ypoints):
        n_points = 100000
        points = db.execute('SELECT %s, %s FROM %s LIMIT %s'%(xpoints, ypoints, tablename, n_points)) 
        return points
    
#    def plotpoints(self, points):
#        self.figpanel.setpointslists(points)
#        self.figpanel.draw()


class ScatterFrame(wx.Frame):
    def __init__(self, parent, **kwargs):
        wx.Frame.__init__(self, parent, **kwargs)
        self.controller = ScatterController()
        self.figure = CPFigurePanel(self, -1, (1,1))
        self.controls = ScatterControlPanel(self, self.controller)
        self.controller.attach(self.figure, self.controls)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.Sizer.Add(self.figure, 1, wx.EXPAND)
        self.Sizer.Add(self.controls)


class ScatterControlPanel(wx.Panel):
    '''
    UI Controls for Scatter Plot
    '''
    def __init__(self, parent, controller, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        # the controller for the figure
        self.controller = controller
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.table_choice = wx.Choice(self, -1, choices=db.GetTableNames())
        self.table_choice.Select(0)
        self.x_choice = wx.Choice(self, -1)
        self.y_choice = wx.Choice(self, -1)
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")
        
        self.update_column_fields()
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "table:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.table_choice, 1, wx.EXPAND)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "x-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.x_choice)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "y-axis:"))
        sz.AddSpacer((5,-1))
        sz.Add(self.y_choice)
        sizer.Add(sz)
        sizer.AddSpacer((-1,5))
        sizer.Add(self.update_chart_btn)    
        
        wx.EVT_CHOICE(self.table_choice, -1, self.update_column_fields)
        wx.EVT_BUTTON(self.update_chart_btn, -1, self.on_update_pressed)   
        
        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        sizer.Fit(self)
        self.Show(1)

    def get_table(self):
        return self.table_choice.GetStringSelection()
        
    def get_x_column(self):
        return self.x_choice.GetStringSelection()
        
    def get_y_column(self):
        return self.y_choice.GetStringSelection()

    def update_column_fields(self, evt=None):
        tablename = self.get_table()
        fieldnames = self.controller.get_column_names(tablename)
        self.x_choice.Clear()
        self.x_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)
        self.y_choice.Clear()
        self.y_choice.AppendItems(fieldnames)
        self.y_choice.SetSelection(0)
        
    def on_update_pressed(self, evt):
        self.controller.update_figure()



class PlotPanel (wx.Panel):
    '''
    The PlotPanel has a Figure and a Canvas. OnSize events simply set a 
    flag, and the actual resizing of the figure is triggered by an Idle event.
    '''
    def __init__(self, parent, color=None, dpi=None, **kwargs):
        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__(self, parent, **kwargs)

        self.dpi = dpi
        self.color = color
        
        self.figure = Figure(None, self.dpi)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.SetColor(self.color)
        self.draw()

        self._resizeflag = False

        self.Bind(wx.EVT_IDLE, self._onIdle)
        self.Bind(wx.EVT_SIZE, self._onSize)

    def clear_figure(self):
        self.figure.clear()
        self.SetColor(self.color)
        self._resizeflag = True
        
    def SetColor(self, rgbtuple=None):
        """Set figure and canvas colours to be the same."""
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get()
        clr = [c / 255. for c in rgbtuple]
        self.figure.set_facecolor(clr)
        self.figure.set_edgecolor(clr)
        self.canvas.SetBackgroundColour(wx.Colour(*rgbtuple))

    def _onSize(self, event):
        self._resizeflag = True

    def _onIdle(self, evt):
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()

    def _SetSize(self):
        pixels = self.GetClientSize()
        if 0 in pixels:
            return
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(float(pixels[0]) / self.figure.get_dpi(),
                                     float(pixels[1]) / self.figure.get_dpi())

    def draw(self):
        # abstract, to be overridden by child classes 
        pass 





# Use CP
#    def launch_scatter(self, evt):
#        figure = cpfig.create_or_find(self, -1, 'scatter', subplots=(1,1), name='scatter')
#        table = np.random.randn(5000,2)
#        figure.panel.subplot_scatter(0, 0, table)



if __name__ == '__main__':
    p.LoadFile('/Users/afraser/Desktop/cpa_example/example.properties')
    app = wx.PySimpleApp()
    f = ScatterFrame(None)
    f.Show()
    app.MainLoop()
