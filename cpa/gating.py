
import wx
import numpy as np
from . import sqltools as sql
from matplotlib.patches import Rectangle
from .properties import Properties
p = Properties()

class GatingHelper(object):
    '''
    Helper class to handle drawing and interactions with gates on 1-D and 2-D 
    plots.
    '''
    BOUNDARY_LEFT   = 'left'
    BOUNDARY_RIGHT  = 'right'
    BOUNDARY_TOP    = 'top'
    BOUNDARY_BOTTOM = 'bottom'
    BOUNDARY_INSIDE = 'inside'
    
    def __init__(self, subplot, parent_window=None):
        '''subplot -- a matplotlib.axes.Axes instance to attach to.
        parent-window -- if the subplot that this GatingHelper is attached to is
           within a wx.Window, you must specify the window here so GatingHelper
           knows when to detach it's observers from the gate objects.
        Note that if the Axes object is deleted or replaced, a new GatingHelper
        will need to be created for that subplot.
        '''
        self.gate = None
        self.dragging = False
        self.patch = None
        self.cids = []
        self.hover = False
        self.subplot = subplot
        self.canvas = subplot.figure.canvas
        self.background = self.canvas.copy_from_bbox(self.subplot.bbox)
        if parent_window:
            parent_window.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        p.gates.addobserver(self.on_gate_list_changed)
        
    def on_destroy(self, evt=None):
        self.destroy()
        evt.Skip()
        
    def destroy(self):
        '''Important: this function must be called when this object is destroyed.
        Note: for some reason calling it in __del__ doesn't work
        '''
        if self.gate:
            self.gate.removeobserver(self.redraw)
        p.gates.removeobserver(self.on_gate_list_changed)
            
    def on_gate_list_changed(self, xxx_todo_changeme):
        (name, gate) = xxx_todo_changeme
        if gate is None:
            # a gate was deleted, check to see if it was this gate.
            if self.gate not in list(p.gates.values()):
                self.disable()
        
    def disable(self):
        '''Hide gates and disable mouse interactions.'''
        self.disconnect_bindings()
        if self.gate:
            self.gate.removeobserver(self.redraw)
        self.gate = None
        self.patch = None
        self.canvas.draw()
                
    def set_displayed_gate(self, gate, x_column, y_column):
        '''Set the gate to be drawn on this plot. Gates are drawn as
        a dashed rectangle marking the min and max values of the gate along the
        currently displayed dimension(s).

        Note: This feature does not yet represent gate dimensions that are not
              displayed on a plot axis. If a gate is passed in whose columns
              are not a subset of (x_column, y_column) then nothing will be
              drawn.
        
        gate - sqltools.Gate object to visualize/edit. If the gate passed in is
               empty then the user may draw a gate in the current axes to 
               populate it.
        x_column - sqltools.Column specifying which column is currently being 
                   plotted on the x axis or None
        y_column - sqltools.Column specifying which column is currently being
                   plotted on the y axis or None
        '''
        assert isinstance(gate, sql.Gate)
        for col in gate.get_columns():
            if col not in (x_column, y_column):
                print('can not display this gate')
                self.disable()
                return
        if self.gate:
            self.gate.removeobserver(self.redraw)
        self.gate = gate
        self.gate.addobserver(self.redraw)
        self.patch = None
        self.x_column = x_column
        self.y_column = y_column
        
        self.disconnect_bindings()
        if self.gate.is_empty():
            # a horse of a different color
            self.cids = [self.canvas.mpl_connect('motion_notify_event', self.on_motion_new_gate),
                         self.canvas.mpl_connect('button_press_event', self.on_press),
                         self.canvas.mpl_connect('button_release_event', self.on_release_new_gate),
                         self.canvas.mpl_connect('draw_event', self.on_draw)]
        else:
            self.cids = [self.canvas.mpl_connect('motion_notify_event', self.on_motion),
                         self.canvas.mpl_connect('button_press_event', self.on_press),
                         self.canvas.mpl_connect('button_release_event', self.on_release),
                         self.canvas.mpl_connect('draw_event', self.on_draw)]
        self.canvas.draw()

    def get_gate_patch(self):
        '''Returns a matplotlib patch to be drawn on the canvas whose dimensions
        have been computed from the current gate.
        '''
        x_min, x_max = self.subplot.get_xlim()
        x_range = x_max - x_min
        y_min, y_max = self.subplot.get_ylim()
        y_range = y_max - y_min
        
        for subgate in self.gate.get_subgates():       
            col = subgate.get_column()
            if col == self.x_column:
                x_min = subgate.get_min()
                x_range = subgate.get_max() - subgate.get_min()
            if col == self.y_column:
                y_min = subgate.get_min()
                y_range = subgate.get_max() - subgate.get_min()

        if self.patch not in self.subplot.patches:
            rect = Rectangle((x_min, y_min), x_range, y_range, animated=True)
            rect.set_fill(False)
            rect.set_linestyle('dashed')
            rect.set_edgecolor('dimgrey')
            self.patch = self.subplot.add_patch(rect)
        else:
            self.patch.set_bounds(x_min, y_min, x_range, y_range)
        return self.patch
        
    def on_draw(self, evt):
        '''Cache the plot background and draw the gate over it.
        Called when the canvas is redrawn. 
        '''
        self.background = self.canvas.copy_from_bbox(self.subplot.bbox)
        if self.gate:
            self.subplot.draw_artist(self.get_gate_patch())
        self.canvas.blit(self.subplot.bbox)
        
    def redraw(self, evt=None):
        '''Redraw the gate on the canvas.
        This is called whenever the visible gate is modified.
        '''
        self.canvas.restore_region(self.background)
        # Recompute and redraw the gate patch
        if self.gate:
            self.subplot.draw_artist(self.get_gate_patch())
        self.canvas.blit(self.subplot.bbox)
        
    def on_motion(self, evt):
        '''Mouse motion handler. Handle cursor changes and gate-boundary 
        dragging.
        '''        
        if self.dragging:
            #
            # A gate is being resized:
            #   Recompute the current gate min/max from the mouse position.
            #
            if self.hover == self.BOUNDARY_LEFT and evt.xdata:
                for subgate in self.gate.get_subgates():
                    if subgate.get_column() == self.x_column:
                        subgate.set_min(min(evt.xdata, subgate.get_max()))
                
            elif self.hover == self.BOUNDARY_RIGHT and evt.xdata:
                for subgate in self.gate.get_subgates():
                    if subgate.get_column() == self.x_column:
                        subgate.set_max(max(evt.xdata, subgate.get_min()))

            elif self.hover == self.BOUNDARY_BOTTOM and evt.ydata:
                for subgate in self.gate.get_subgates():
                    if subgate.get_column() == self.y_column:
                        subgate.set_min(min(evt.ydata, subgate.get_max()))

            elif self.hover == self.BOUNDARY_TOP and evt.ydata:
                for subgate in self.gate.get_subgates():
                    if subgate.get_column() == self.y_column:
                        subgate.set_max(max(evt.ydata, subgate.get_min()))

            elif self.hover == self.BOUNDARY_INSIDE and evt.xdata and evt.ydata:
                for subgate in self.gate.get_subgates():
                    if subgate.get_column() == self.x_column:
                        new_range = self._init_range[subgate.get_column()] - self._mouse_click_xy_data[0] + evt.xdata
                    elif subgate.get_column() == self.y_column:
                        new_range = self._init_range[subgate.get_column()] - self._mouse_click_xy_data[1] + evt.ydata
                    subgate.set_range(*new_range)

            if evt.xdata and evt.ydata:
                self._mouse_xy_data = (evt.xdata, evt.ydata)
            return

        self.hover = None
        if self.patch:
            #
            # If there is a patch, change the mouse according to which part of
            # the patch the mouse is hovering over.
            #
            xmin, ymin = self.subplot.transData.transform(
                             np.array([self.patch.get_xy()]))[0]
            xmax, ymax = self.subplot.transData.transform(
                             np.array([(self.patch.get_x() + self.patch.get_width(),
                                        self.patch.get_y() + self.patch.get_height())]))[0]
            
            if abs(evt.x - xmin) < 2 and (ymin < evt.y < ymax):
                self.hover = self.BOUNDARY_LEFT
                wx.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
                
            elif abs(evt.x - xmax) < 2 and (ymin < evt.y < ymax):
                self.hover = self.BOUNDARY_RIGHT
                wx.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
                
            elif abs(evt.y - ymin) < 2 and (xmin < evt.x < xmax):
                self.hover = self.BOUNDARY_BOTTOM
                wx.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
                
            elif abs(evt.y - ymax) < 2 and (xmin < evt.x < xmax):
                self.hover = self.BOUNDARY_TOP
                wx.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
                
            elif (xmin < evt.x < xmax) and (ymin < evt.y < ymax):
                self.hover = self.BOUNDARY_INSIDE
                wx.SetCursor(wx.Cursor(wx.CURSOR_SIZING))
                
            else:
                wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        else:
            wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            
    def on_motion_new_gate(self, evt):
        '''Mouse motion handler for empty gates that need to be created first.
        Handle cursor changes and gate dragging.
        '''
        if evt.xdata and evt.ydata:
            wx.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
            if self.dragging:
                if self.x_column:
                    xmin = min(self._mouse_xy_data[0], evt.xdata)
                    xmax = max(self._mouse_xy_data[0], evt.xdata)
                    if self.x_column not in [g.get_column() for g in self.gate.get_subgates()]:
                        self.gate.add_subgate(sql.Gate1D(self.x_column.copy(), (xmin, xmax)))
                    else:
                        for subgate in self.gate.get_subgates():
                            if subgate.get_column() == self.x_column:
                                subgate.set_range(xmin, xmax)
                if self.y_column and self.y_column != self.x_column:
                    ymin = min(self._mouse_xy_data[1], evt.ydata)
                    ymax = max(self._mouse_xy_data[1], evt.ydata)
                    if self.y_column not in [g.get_column() for g in self.gate.get_subgates()]:
                        self.gate.add_subgate(sql.Gate1D(self.y_column.copy(), (ymin, ymax)))
                    else:
                        for subgate in self.gate.get_subgates():
                            if subgate.get_column() == self.y_column:
                                subgate.set_range(ymin, ymax)
            return
        else:
            wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
                
    def on_press(self, evt):
        '''Mouse-down handler. Start dragging. Store data coords of xi,yi
        '''
        if self.hover or self.gate.is_empty():
            if evt.button == 1:
                self.dragging = True
                self._mouse_xy_data = (evt.xdata, evt.ydata)
                self._mouse_click_xy_data = (evt.xdata, evt.ydata)
                self._init_range = {}
                for subgate in self.gate.get_subgates():
                    self._init_range[subgate.get_column()] = np.array(subgate.get_range())

            
    def on_release(self, evt):
        '''Mouse-up handler. Stop dragging.
        '''
        self.dragging = False
        
    def on_release_new_gate(self, evt):
        '''Mouse-up handler for creating a new gate. Stop dragging. Switch to 
        gate-editing mode.
        '''
        self.dragging = False
        self.set_displayed_gate(self.gate, self.x_column, self.y_column)
            
    def disconnect_bindings(self):
        '''Disconnect all event handlers.
        '''
        for cid in self.cids:
            self.canvas.mpl_disconnect(cid)
