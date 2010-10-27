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
        #timepoints.append(-1)
        
        # get the time dictonary  where the structure is #d[t] ==> [node,...]    #d[t][i] ==> ith child at timepoint t
##        time_dictoniary = self.timeline.get_nodes_by_timepoint()

        nodeY = {}
        Y = 10
        
        nodes_by_timepoint = self.timeline.get_nodes_by_timepoint()
        for t, nodes in nodes_by_timepoint.items():
            print t
            for n in nodes:
                print n.id
                print '\t', [c.id for c in n.children]
        

        dc.SetPen(wx.Pen("BLACK",1))
        for i, time in enumerate(timepoints): 
            print time,"\t"
            X = timepoints[i]*50
            if i == 0: #ensure that it is the last timepoint
                for node in nodes_by_timepoint[time]:
                    dc.DrawCircle(X, Y, 5)
                    nodeY[node.id] = Y
                    Y += 20
            else:
                for node in nodes_by_timepoint[time]:
                    ycoord = []  #reset to empty list
                    print node.id
                    for child in node.get_children():
                        print child.id, child.get_well_ids()
                        ycoord.append(nodeY[child.id])
                    print "\n"    
                    Y = int((min(ycoord)+max(ycoord))/2)
                    dc.DrawCircle(X, Y, 5)
                    nodeY[node.id] = Y

        #Create the pen for drawing the lineage


        dc.EndDrawing()
        #Drawing the lineage from Right --> Left
        # for the latest time point get all the nodes and draw them with fixed point distance start from Y =10 and then increase by 20 pxl
        # for the previous generation, start from the top node, get the number of childeren it has  if 3 chidren then the topmost nodes of this generation will be (20*3/2)+10
        # if the subsequent

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.repaint = False
            self.Layout()

        #d[t] ==> [node,...]
        #d[t][i] ==> ith child at timepoint t
        #for time in timepoint:
        #for time in reverse(timepoints) + [-1]:         # add the stock time point -1 to the reverse timepoint
            #  print time
        #td[time][0].parent ==



# get the last timepoint and find how many nodes should be there and place them fixed pixel apart
# find the parents of these last timepoint nodes and place their mohter node in the middle Y axis of the children nodes i.e. 3 child nodes (Y1+Y2+Y3)/2
# connect the parent and child nodes with line
# now the parents nodes become the child nodes and recursively find their parent and continue untill the ROOT node is placed and connected
        #r = 5
        #dc.SetPen(wx.Pen("BLACK",1))
        #dc.DrawLine(0, 0, 300, 20)
        #dc.DrawCircle(300, 20, r)





if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = wx.Frame(None, size=(600,400))
    p = LineagePanel(frame)

    t = LP.Timeline('U2OS')

    LP.PlateDesign.add_plate('fred', LP.P6)
    all_wells = LP.PlateDesign.get_well_ids(LP.PlateDesign.get_plate_format('fred'))

    t.add_event(1, 'seed', 'fred', all_wells)

    t.add_event(2, 'treatment1', 'fred', ['A01', 'A02', 'A03', 'B03'])
    t.add_event(2, 'treatment2', 'fred', [ 'A02', 'B02', 'B03'])
    untreated_wells = set(all_wells) - set(t.get_well_ids(2))
    t.add_event(2, LP.NO_EVENT,     'fred', untreated_wells)

    t.add_event(3, 'treat', 'fred', ['A01', 'A03', 'B02'])
    t.add_event(3, 'wash', 'fred', ['B02', 'B03'])
    untreated_wells = set(all_wells) - set(t.get_well_ids(3))
    t.add_event(3, LP.NO_EVENT, 'fred', untreated_wells)

    t.add_event(4, 'spin', 'fred', ['B01', 'A02', 'A03'])
    untreated_wells = set(all_wells) - set(t.get_well_ids(4))
    t.add_event(4, LP.NO_EVENT, 'fred', untreated_wells)

    p.set_timeline(t)
    frame.Show()

    app.MainLoop()



