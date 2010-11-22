from timeline import  *
from experimentsettings import *
import wx
import numpy as np
from time import time

class TimelinePanel(wx.Panel):
    '''An interactive timeline panel
    '''
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        scroll=wx.ScrolledWindow(self,-1)

        self.timeline = None
        self.repaint = False
        self.max_time = 24

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)
        
    def set_timeline(self, timeline):
        self.timeline = timeline
        self.repaint = True

    def set_max_time(self, max_time):
        self.max_time = max_time
        self.repaint = True

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        t0 = time()
        PADDING = 30
        EVT_BOX_W = 5
        MIN_X_GAP = EVT_BOX_W * 2 + 2

        if self.timeline is None:
            return
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        px_per_time = w_win - PADDING * 2 / self.max_time 

        dc.DrawLine(PADDING, h_win-PADDING, w_win-PADDING, h_win-PADDING)
        y = h_win - PADDING
        for timepoint in self.timeline.get_unique_timepoints():
            x = timepoint * px_per_time
            dc.DrawCircle(x, y, EVT_BOX_W)

        dc.EndDrawing()
        print 'rendered in %.2f seconds'%(time() - t0)

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.repaint = False
            self.Layout()


class LineagePanel(wx.Panel):
    '''A Panel that displays a lineage tree.
    '''

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        scroll=wx.ScrolledWindow(self,-1)

        self.timeline = None
        self.tree = None
        self.nodes_by_pos = {} # map node coords (in 0-1 space) to node data
        self.repaint = False
        self.nodes_by_timepoint = {}

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)

    def set_timeline(self, timeline):
        self.nodes_by_pos = {}
        self.timeline = timeline
        t0 = time()
        self.nodes_by_timepoint = self.timeline.get_nodes_by_timepoint()
        n = sum(map(len, self.nodes_by_timepoint.values()))
        print 'Built tree with %s nodes in %.2f seconds'%(n, time()-t0)
        self.tree = timeline.get_lineage_tree()
        self.repaint = True

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        t0 = time()
        PADDING = 30
        NODE_R = 5
        MIN_X_GAP = NODE_R*2 + 2
        MIN_Y_GAP = NODE_R*2 + 2

        if self.timeline is None or self.tree is None:
            return
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))

        # get the unique timpoints from the timeline
        timepoints = self.timeline.get_unique_timepoints()
        timepoints.reverse()
        timepoints.append(-1)
        
        
        self.SetMinSize((len(self.nodes_by_timepoint) * MIN_X_GAP + PADDING * 2,
                         len(self.nodes_by_timepoint[timepoints[0]]) * MIN_Y_GAP + PADDING * 2))

        width = float(self.Size[0])
        height = float(self.Size[1])
        # calculate the number of pixels to separate each generation timepoint
        x_step = max(MIN_X_GAP, (width - PADDING * 2) / (len(self.nodes_by_timepoint) - 1))
        # calcuate the minimum number of pixels to separate nodes on the y axis
        y_gap = max(MIN_Y_GAP, (height - PADDING * 2) / (len(self.nodes_by_timepoint[timepoints[0]]) - 1))
        
        # Store y coords of children so we can calculate where to draw the parents
        nodeY = {}
        Y = PADDING
        X = width - PADDING
        dc.SetPen(wx.Pen("BLACK",1))
        # Iterate from leaf nodes up to the root, and draw R->L, Top->Bottom
        for i, t in enumerate(timepoints): 
            if i == 0:
                # Last timepoint (leaf nodes)
                for node in self.nodes_by_timepoint[t]:
                    dc.DrawCircle(X, Y, NODE_R)
                    if self.nodes_by_pos == {}:
                        self.nodes_by_pos[(X,Y)] = node
                    nodeY[node.id] = Y
                    Y += y_gap
            else:
                # Not the last timepoint
                for node in self.nodes_by_timepoint[t]:
                    ycoord = []
                    for child in node.get_children():
                        ycoord.append(nodeY[child.id])
                    Y = int((min(ycoord) + max(ycoord))/2)
                    dc.DrawCircle(X, Y, NODE_R)
                    if self.nodes_by_pos == {}:
                        self.nodes_by_pos[(X,Y)] = node
                    for child in node.get_children():
                        dc.DrawLine(X + NODE_R, Y, 
                                    X + x_step - NODE_R ,nodeY[child.id])
                    nodeY[node.id] = Y
            X -= x_step
        dc.EndDrawing()
        print 'rendered in %.2f seconds'%(time() - t0)

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.repaint = False
            self.Layout()



if __name__ == "__main__":        
    app = wx.PySimpleApp()

    t = Timeline('U2OS')
    PlateDesign.add_plate('fred', P24)
    allwells = PlateDesign.get_well_ids(PlateDesign.get_plate_format('fred'))
    for i in range(1,8):
        for j in range(np.random.randint(1,12)):
            np.random.shuffle(allwells)
            well_ids = [('fred', well) for well in allwells[:np.random.randint(0, len(allwells))]]
            t.add_event(i, 'spin%d'%(i), well_ids)

    #frame = wx.Frame(None, size=(600,400))
    #sw = wx.ScrolledWindow(frame)
    #p = LineagePanel(sw)
    #sw.Sizer = wx.BoxSizer()
    #sw.Sizer.Add(p, 1 ,wx.EXPAND)
    #p.set_timeline(t)
    #sw.SetScrollbars(20, 20, frame.Size[0]+20, frame.Size[1]+20, 0, 0)
    #sw.Fit()
    #frame.Show()
    
    f = wx.Frame(None)
    sw = wx.ScrolledWindow(f)
    p = TimelinePanel(sw)
    p.set_timeline(t)
    sw.Sizer = wx.BoxSizer()
    sw.Sizer.Add(p, 1 ,wx.EXPAND)
    sw.SetScrollbars(20, 20, f.Size[0]+20, f.Size[1]+20, 0, 0)
    sw.Fit()
    f.Show()
    
    app.MainLoop()



