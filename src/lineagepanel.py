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

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)
        
    def set_tree(self, tree):
        '''tree -- a LineageNode object representing the tree to be drawn
        '''
        # do stuff then refresh
        self.Refresh()
        
 
    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))

        r = 20

        dc.SetPen(wx.Pen("BLACK",5))
        dc.DrawCircle(100, 100, r)
        dc.DrawLine(100+20, 100, 300, 100)
        dc.EndDrawing()

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.Refresh()
            self.repaint = False

        
if __name__ == "__main__":
    app = wx.PySimpleApp()

    frame = wx.Frame(None, size=(500,300))
    p = LineagePanel(frame)
    
    t = LP.Timeline('U2OS')

    LP.PlateDesign.add_plate('fred', LP.P6)
    all_wells = LP.PlateDesign.get_well_ids(LP.PlateDesign.get_plate_format('fred'))
    
    t.add_event(1, 'seed', 'fred', all_wells)
    
    t.add_event(2, 'treatment1', 'fred', ['A01', 'A02', 'A03', 
                                                        'B03'])
    t.add_event(2, 'treatment2', 'fred', [       'A02', 
                                                 'B02', 'B03'])
    untreated_wells = set(all_wells) - set(t.get_well_ids(2))
    t.add_event(2, LP.NO_EVENT,     'fred', untreated_wells)
 
    t.add_event(3, 'treat', 'fred', ['A02'])
    t.add_event(3, 'wash', 'fred', ['A01'])
    untreated_wells = set(all_wells) - set(t.get_well_ids(3))
    t.add_event(3, LP.NO_EVENT, 'fred', untreated_wells)
    t.add_event(4, 'imaging', 'fred', LP.PlateDesign.get_well_ids(LP.P6))
 
    tree = t.get_lineage_tree()
   
    p.set_tree(tree)
    frame.Show()

    app.MainLoop()



