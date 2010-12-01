from experimentsettings import *
import wx
import numpy as np
from time import time

class LineageFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='Experiment Lineage', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        
        sw = wx.ScrolledWindow(self)
        timeline_panel = TimelinePanel(sw)
        self.timeline_panel = timeline_panel
        lineage_panel = LineagePanel(sw)
        self.lineage_panel = lineage_panel
        timeline_panel.set_style(padding=30)
        lineage_panel.set_style(padding=30, flask_gap = 40)
        sw.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sw.Sizer.Add(timeline_panel, 0, wx.EXPAND|wx.LEFT, 40)
        sw.Sizer.Add(lineage_panel, 1, wx.EXPAND)
        sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
        sw.Fit()
        
        tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        tb.AddControl(wx.StaticText(tb, -1, 'zoom'))
        self.zoom = tb.AddControl(wx.Slider(tb, -1, style=wx.SL_AUTOTICKS|wx.SL_LABELS)).GetControl()
        self.zoom.SetRange(1, 30)
        self.zoom.SetValue(10)
        x_spacing = tb.AddControl(wx.CheckBox(tb, -1, 'Even x spacing'))
        x_spacing.GetControl().SetValue(1)
        tb.Realize()
        
        self.Bind(wx.EVT_SLIDER, self.on_zoom, self.zoom)
        self.Bind(wx.EVT_CHECKBOX, self.on_change_spacing, x_spacing)
        
    def on_zoom(self, evt):
        self.lineage_panel.set_style(node_radius=self.zoom.GetValue(),
                                     xgap=self.lineage_panel.NODE_R*2+2,
                                     ygap=self.lineage_panel.NODE_R*2+2)
        self.timeline_panel.set_style(box_width=self.zoom.GetValue(),
                                      box_height=self.zoom.GetValue(),
                                      xgap=self.timeline_panel.BOX_W+2)
    def on_change_spacing(self, evt):
        if evt.Checked():
            self.lineage_panel.set_even_x_spacing()
            self.timeline_panel.set_even_x_spacing()
        else:
            self.lineage_panel.set_time_x_spacing()
            self.timeline_panel.set_time_x_spacing()


class TimelinePanel(wx.Panel):
    '''An interactive timeline panel
    '''
    PAD = 30.0
    BOX_W = 10.0
    BOX_H = 10.0
    MIN_X_GAP = BOX_W + 1

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)

        meta = ExperimentSettings.getInstance()
        meta.add_subscriber(self.on_timeline_updated, get_matchstring_for_subtag(2, 'Well'))
        self.timeline = None
        self.timepoints = None
        self.cursor_pos = None
        self.show_time_flag = False
        self.hover_timepoint = None
        self.selection = None
        self.time_x = False
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_exit)
        
    def set_style(self, padding=None, xgap=None, box_width=None, box_height=None):
        if padding is not None:
            self.PAD = padding
        if xgap is not None:
            self.MIN_X_GAP = xgap
        if box_width is not None:
            self.BOX_W = box_width
        if box_height is not None:
            self.BOX_H = box_height
        self.Refresh()
        
    def set_time_x_spacing(self):
        self.time_x = True
        self.Refresh()

    def set_even_x_spacing(self):
        self.time_x = False
        self.Refresh()

    def on_timeline_updated(self, tag):
        meta = ExperimentSettings.getInstance()
        timeline = meta.get_timeline()
        self.timepoints = timeline.get_unique_timepoints()
        if len(self.timepoints) > 0:
            if self.time_x:
                self.SetMinSize((self.PAD * 2 + self.MIN_X_GAP * self.timepoints[-1],
                                 self.PAD * 2 + self.BOX_W * 3))
            else:
                self.SetMinSize((len(self.timepoints) * self.MIN_X_GAP + self.PAD * 2,
                                 self.PAD * 2 + self.BOX_W * 3))            
        self.Refresh()

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        if self.timepoints is None:
            return

        PAD = self.PAD
        BOX_W = self.BOX_W
        BOX_H = self.BOX_H
        MIN_X_GAP = BOX_W + 2
        MAX_TIMEPOINT = self.timepoints[-1]
        
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        px_per_time = max((w_win - PAD * 2) / MAX_TIMEPOINT,
                          MIN_X_GAP)
        
        if len(self.timepoints) == 1:
            x_step = 1
        else:
            x_step = max(MIN_X_GAP, 
                         (w_win - PAD * 2) / (len(self.timepoints) - 1))


        # draw the timeline
        if self.time_x:
            dc.DrawLine(PAD, h_win - PAD, 
                        px_per_time * MAX_TIMEPOINT + PAD, h_win - PAD)
        else:            
            dc.DrawLine(PAD, h_win - PAD, 
                        x_step * (len(self.timepoints) - 1) + PAD, h_win - PAD)
        
        # y pos to draw event boxes at
        y = h_win - PAD - (BOX_H - 1) / 2
        
        # draw flag at cursor pos
        if self.cursor_pos is not None and self.show_time_flag:
            dc.SetBrush(wx.Brush('#FFFFCC'))
            dc.DrawLine(self.cursor_pos, y + (BOX_W - 1) / 2, 
                        self.cursor_pos, y - BOX_W - 2)
            dc.DrawRectangle(self.cursor_pos, y-BOX_W - 2, 
                             BOX_W * 4, BOX_W)

        # draw event boxes
        dc.SetBrush(wx.Brush('#FFFFFF'))
        for i, timepoint in enumerate(self.timepoints):
            if self.time_x:
                x = timepoint * px_per_time + PAD - BOX_W / 2
            else:
                x = i * x_step + PAD - BOX_W / 2
            if self.cursor_pos is not None and x < self.cursor_pos < x + BOX_W:
                dc.SetBrush(wx.Brush('#FFFFCC'))
                dc.SetPen(wx.Pen(wx.BLACK, 2))
                self.hover_timepoint = timepoint
            else:
                dc.SetBrush(wx.Brush('#FFFFFF'))
                dc.SetPen(wx.Pen(wx.BLACK, 1))
                self.hover_timepoint = None
            dc.DrawRectangle(x, y, BOX_W, BOX_H)
        
        dc.EndDrawing()

    def _on_mouse_motion(self, evt):
        self.cursor_pos = evt.X
        self.Refresh()

    def _on_mouse_exit(self, evt):
        self.cursor_pos = None
        self.Refresh()
        
    def _on_click(self, evt):
        meta = ExperimentSettings.getInstance()
        timeline = meta.get_timeline()
        if self.hover_timepoint is not None:
            self.selection = (self.hover_timepoint, 
                              timeline.get_events_at_timepoint())


class LineagePanel(wx.Panel):
    '''A Panel that displays a lineage tree.
    '''
    PAD = 30
    NODE_R = 10
    MIN_X_GAP = NODE_R*2 + 2
    MIN_Y_GAP = NODE_R*2 + 2
    FLASK_GAP = MIN_X_GAP

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.tree = None
        self.nodes_by_timepoint = {}
        self.time_x = False
        
        meta = ExperimentSettings.getInstance()
        meta.add_subscriber(self.on_timeline_updated, 
                            get_matchstring_for_subtag(2, 'Well'))

        self.Bind(wx.EVT_PAINT, self._on_paint)
        
    def set_time_x_spacing(self):
        self.time_x = True
        self.Refresh()

    def set_even_x_spacing(self):
        self.time_x = False
        self.Refresh()
        
    def set_style(self, padding=None, xgap=None, ygap=None, node_radius=None,
                  flask_gap=None):
        if padding is not None:
            self.PAD = padding
        if xgap is not None:
            self.MIN_X_GAP = xgap
        if ygap is not None:
            self.MIN_Y_GAP = ygap
        if node_radius is not None:
            self.NODE_R = node_radius
        if flask_gap is not None:
            self.FLASK_GAP = flask_gap
        self.Refresh()
     
    def on_timeline_updated(self, tag):
        '''called to add events to the timeline and update the lineage
        '''
        meta = ExperimentSettings.getInstance()
        timeline = meta.get_timeline()
        self.nodes_by_timepoint = timeline.get_nodes_by_timepoint()
        self.tree = timeline.get_lineage_tree()
        self.Refresh()

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        if self.tree is None:
            return

        t0 = time()
        PAD = self.PAD
        NODE_R = self.NODE_R
        MIN_X_GAP = self.MIN_X_GAP
        MIN_Y_GAP = self.MIN_Y_GAP
        FLASK_GAP = self.FLASK_GAP

        meta = ExperimentSettings.getInstance()

        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))

        # get the unique timpoints from the timeline
        timepoints = meta.get_timeline().get_unique_timepoints()
        timepoints.reverse()
        timepoints.append(-1)
        
        if self.time_x:
            self.SetMinSize((self.PAD * 2 + self.MIN_X_GAP * timepoints[0] + FLASK_GAP,
                             len(self.nodes_by_timepoint[timepoints[0]]) * MIN_Y_GAP + PAD * 2))
        else:
            self.SetMinSize((len(self.nodes_by_timepoint) * MIN_X_GAP + PAD * 2,
                             len(self.nodes_by_timepoint[timepoints[0]]) * MIN_Y_GAP + PAD * 2))

        
        width = float(self.Size[0])
        height = float(self.Size[1])
        if len(self.nodes_by_timepoint) == 1:
            x_step = 1
        else:
            # calculate the number of pixels to separate each generation timepoint
            x_step = max(MIN_X_GAP, 
                         (width - PAD * 2 - FLASK_GAP) / (len(self.nodes_by_timepoint) - 2))
            
        if len(self.nodes_by_timepoint[timepoints[0]]) == 1:
            y_gap = MIN_Y_GAP
        else:
            # calcuate the minimum number of pixels to separate nodes on the y axis
            y_gap = max(MIN_Y_GAP, (height - PAD * 2) / (len(self.nodes_by_timepoint[timepoints[0]]) - 1))
            
        px_per_time = max((w_win - PAD * 2 - FLASK_GAP) / timepoints[0],
                          MIN_X_GAP)
                
        
        # Store y coords of children so we can calculate where to draw the parents
        nodeY = {}
        Y = PAD
        X = width - PAD
        dc.SetPen(wx.Pen("BLACK",1))

        # Iterate from leaf nodes up to the root, and draw R->L, Top->Bottom
        for i, t in enumerate(timepoints):
            if t == -1:
                X = PAD
            elif self.time_x:
                X = PAD + FLASK_GAP + t * px_per_time
                x_step = PAD + FLASK_GAP + timepoints[i-1] * px_per_time - X
            else:
                X = PAD + FLASK_GAP + (len(timepoints) - i - 2) * x_step
            
            if len(self.nodes_by_timepoint) == 1:
                X = width / 2
                Y = height / 2
                dc.DrawCircle(X, Y, NODE_R)
                #dc.DrawText(str(self.nodes_by_timepoint[t][0].get_timepoint()), X, Y+NODE_R)
            elif i == 0:
                # Leaf nodes
                for node in self.nodes_by_timepoint[t]:
                    dc.DrawCircle(X, Y, NODE_R)
                    #dc.DrawText(str(node.get_timepoint()), X, Y+NODE_R)
                    #if self.nodes_by_pos == {}:
                        #self.nodes_by_pos[(X,Y)] = node
                    nodeY[node.id] = Y
                    Y += y_gap
            else:
                # Internal nodes
                for node in self.nodes_by_timepoint[t]:
                    ycoord = []
                    for child in node.get_children():
                        ycoord.append(nodeY[child.id])
                    Y = int((min(ycoord) + max(ycoord))/2)
                    if t == -1:
                        dc.DrawRectangle(X-NODE_R, Y-NODE_R, NODE_R*2, NODE_R*2)
                    else:
                        dc.DrawCircle(X, Y, NODE_R)
                    #dc.DrawText(str(node.get_timepoint()), X, Y+NODE_R)
                    #if self.nodes_by_pos == {}:
                        #self.nodes_by_pos[(X,Y)] = node
                    for child in node.get_children():
                        if t == -1:
                            dc.DrawLine(X + NODE_R, Y, 
                                        X + FLASK_GAP - NODE_R ,nodeY[child.id])
                        else:
                            dc.DrawLine(X + NODE_R, Y, 
                                        X + x_step - NODE_R ,nodeY[child.id])
                    nodeY[node.id] = Y
        dc.EndDrawing()
        print 'rendered in %.2f seconds'%(time() - t0)        
        
        
if __name__ == "__main__":
    
    N_FURCATIONS = 3
    N_TIMEPOINTS = 5
    MAX_TIMEPOINT = 10
    PLATE_TYPE = P24
    
    app = wx.PySimpleApp()
    
    f = LineageFrame(None, size=(600, 400))
    f.Show()

    meta = ExperimentSettings.getInstance()
    PlateDesign.add_plate('test', PLATE_TYPE)
    allwells = PlateDesign.get_well_ids(PlateDesign.get_plate_format('test'))
    # GENERATE RANDOM EVENTS ON RANDOM WELLS
    for t in [0] + list(np.random.random_integers(1, MAX_TIMEPOINT, N_TIMEPOINTS)):
        for j in range(np.random.randint(1, N_FURCATIONS)):
            np.random.shuffle(allwells)
            well_ids = [('test', well) for well in allwells[:np.random.randint(0, len(allwells))]]
            #timeline.add_event(t, 'event%d'%(t), well_ids)
            meta.set_field('AddProcess|Stain|Wells|0|%s'%(t), well_ids)
    
    app.MainLoop()

