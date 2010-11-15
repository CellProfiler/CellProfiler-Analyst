import lineageprofiler as LP
import wx
import numpy as np
try:
    from agw import supertooltip as STT
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.supertooltip as STT

class LineagePanel(wx.Panel):
    '''
    A Panel that displays...
    '''
##
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        scroll=wx.ScrolledWindow(self,-1)

        self.timeline = None
        self.tree = None

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)

    def set_timeline(self, timeline):
        '''
        '''
        self.timeline = timeline
        self.tree = timeline.get_lineage_tree()
        self.Refresh()


    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        if self.timeline is None or self.tree is None:
            return
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))


        # get the unique timpoints from the Lineageprofiller file for this drawing X axis represents the timepoints
        timepoints = self.timeline.get_unique_timepoints()
        timepoints.reverse()
        timepoints.append(-1)

        nodeY = {}
        Y = 10
        
        nodes_by_timepoint = self.timeline.get_nodes_by_timepoint()
        #for t, nodes in nodes_by_timepoint.items():
 
            #for n in nodes:
                #print n.id
                #print '\t', [c.id for c in n.children]
        

        dc.SetPen(wx.Pen("BLACK",1))
        for i, time in enumerate(timepoints): 
            if timepoints[i] == -1: #for the stock culture time point 
                X = 10
            else:
                X = timepoints[i]*50
            
            
            if i == 0: #ensure that it is the last timepoint
                for node in nodes_by_timepoint[time]:
                    dc.DrawCircle(X, Y, 5)
                    nodeY[node.id] = Y
                    Y += 20
            else:
                for node in nodes_by_timepoint[time]:
                    ycoord = []  #reset to empty list
                    
                    for child in node.get_children():
                        ycoord.append(nodeY[child.id])
                       
                    Y = int((min(ycoord)+max(ycoord))/2)
                    dc.DrawCircle(X, Y, 5)
                    for child in node.get_children():
                        dc.DrawLine(X,Y,timepoints[i-1]*50 ,nodeY[child.id])
                    
                    nodeY[node.id] = Y

        #Create the pen for drawing the lineage


        dc.EndDrawing()

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.repaint = False
            self.Layout()




if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = wx.Frame(None, size=(600,400))
    p = LineagePanel(frame)

    t = LP.Timeline('U2OS')

    LP.PlateDesign.add_plate('fred', LP.P6)
    all_wells = LP.PlateDesign.get_well_ids(LP.PlateDesign.get_plate_format('fred'))
    
    #========= ONE SET OF EVENTS ==============#
    #t.add_event(1, 'seed1', 'fred', ['A01', 'A02', 'A03', 'B03'])
    #t.add_event(1, 'seed2', 'fred', [ 'A02', 'B02', 'B03'])

    #t.add_event(2, 'treatment1', 'fred', ['A01', 'A03', 'B02'])
    #t.add_event(2, 'treatment2', 'fred', ['B02', 'B03'])
    
    #t.add_event(3, 'spin', 'fred', ['A02', 'A03', 'B01'])

    #t.add_event(4, 'image', 'fred', all_wells)
    
    #========= ANOTHER SET OF EVENTS ==============#
    t.add_event(2, 'treatment1', 'fred', ['A01', 'A02', 'A03', 'B03'])
    t.add_event(2, 'treatment2', 'fred', [ 'A02', 'B02', 'B03'])

    t.add_event(3, 'treat', 'fred', ['A01', 'A03', 'B02'])
    t.add_event(3, 'wash', 'fred', ['B02', 'B03'])

    t.add_event(4, 'spin', 'fred', ['B01', 'A02', 'A03'])

    p.set_timeline(t)
    frame.Show()

    app.MainLoop()



