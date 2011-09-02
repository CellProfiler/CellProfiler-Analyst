import wx
#from experimentsettings import PlateDesign
from experimentsettings import *

# Well Displays
ROUNDED   = 'rounded'
CIRCLE    = 'circle'
SQUARE    = 'square'

all_well_shapes = [SQUARE, ROUNDED, CIRCLE]
meta = ExperimentSettings.getInstance()

class VesselPanel(wx.Panel):    
    def __init__(self, parent, plate_id, well_disp=ROUNDED, **kwargs):
        '''
        parent -- wx parent window
        plate_id -- a plate_id registered in the PlateDesign class
        well_disp -- ROUNDED, CIRCLE, SQUARE, THUMBNAIL or IMAGE
        '''
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.vessel = PlateDesign.get_vessel(plate_id)
        self.well_disp = well_disp
        self.selection = set()           # list of (row,col) tuples
        self.marked = set()
        self.selection_enabled = True
        self.repaint = False
        self.well_selection_handlers = []  # funcs to call when a well is selected
        # drawing parameters
        self.PAD = 10.0
        self.GAP = 0.5
        self.WELL_R = 1.0
        
        self.row_labels = PlateDesign.get_row_labels(self.vessel.shape)
        self.col_labels = PlateDesign.get_col_labels(self.vessel.shape)
        
        # minimum 5 sq. pixels per cell
        long_edge = max(self.vessel.shape)
        self.SetMinSize(((long_edge + 1) * 8.0, 
                         (long_edge + 1) * 8.0))

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
                
    def get_plate_id(self):
        return self.vessel.vessel_id

    def set_well_display(self, well_disp):
        '''well_disp in PlatMapPanel.ROUNDED,
                        PlatMapPanel.CIRCLE,
                        PlatMapPanel.SQUARE
        '''
        self.well_disp = well_disp
        self.Refresh()

    def enable_selection(self, enabled=True):
        self.selection_enabled = enabled
        self.Refresh()
        
    def disable_selection(self):
        self.selection_enabled = False
        self.Refresh()
        
    def set_selected_well_ids(self, wellids):
        '''selects the wells corresponding to the specified wellids or 
        platewell_ids
        '''
        self.selection = set([PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid)
                              for wellid in wellids])
        self.Refresh()
        
    def set_marked_well_ids(self, wellids):
        '''selects the wells corresponding to the specified wellids or 
        platewell_ids
        '''
        self.marked = set([PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid)
                           for wellid in wellids])
        self.Refresh()

    def select_well_id(self, wellid):
        self.select_well_at_pos(PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid))
        
    def deselect_well_id(self, wellid):
        self.deselect_well_at_pos(PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid))
        
    def select_well_at_pos(self, (wellx, welly)):
        self.selection.add((wellx, welly))
        self.Refresh()

    def deselect_well_at_pos(self, (wellx, welly)):
        self.selection.remove((wellx, welly))
        self.Refresh()

    def toggle_selected(self, (wellx, welly)):
        ''' well: 2-tuple of integers indexing a well position (row,col)'''
        if (wellx, welly) in self.selection:
            self.deselect_well_at_pos((wellx, welly))
            return False
        else:
            self.select_well_at_pos((wellx, welly))
            return True

    def get_well_pos_at_xy(self, px, py):
        '''returns a 2 tuple of integers indexing a well position or None if 
        there is no well at the given position.
        '''
        cell_w = self.WELL_R * 2
        x0 = y0 = self.PAD + cell_w
        row = (py - y0) / cell_w
        col = (px - x0) / cell_w
        if (row > self.vessel.shape[0] or row < 0 or
            col > self.vessel.shape[1] or col < 0):
            return None
        return (int(row), int(col))

    def get_well_id_at_xy(self, px, py):
        '''returns the well_id at the pixel coord px,py
        '''
        return PlateDesign.get_well_id_at_pos(self.vessel.shape, self.get_well_pos_at_xy(px,py))

    def get_platewell_id_at_xy(self, px, py):
        '''returns the platewell_id at the pixel coord px,py
        '''
        return (self.vessel.vessel_id, self.get_well_id_at_xy(px, py))
    
    def get_selected_well_ids(self):
        return [PlateDesign.get_well_id_at_pos(self.vessel.shape, pos) 
                for pos in self.selection]
    
    def get_selected_platewell_ids(self):
        return [(self.vessel.vessel_id, PlateDesign.get_well_id_at_pos(self.vessel.shape, pos)) 
                for pos in self.selection]
    
    def _on_paint(self, evt=None):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        PAD = self.PAD
        GAP = self.GAP
        ROWS, COLS = self.vessel.shape

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        # calculate the well radius
        R = min(((w_win - PAD * 2) - ((COLS) * GAP)) / (COLS + 1),
                ((h_win - PAD * 2) - ((ROWS) * GAP)) / (ROWS + 1)) / 2.0
        self.WELL_R = R
        
        # Set font size to fit
        font = dc.GetFont()
        if R > 40:
            font.SetPixelSize((R-10, (R-10)*2))
        elif R > 6:
            font.SetPixelSize((R-2, (R-2)*2))
        else:
            font.SetPixelSize((3, 6))
        wtext, htext = font.GetPixelSize()[0] * 2, font.GetPixelSize()[1]
        dc.SetFont(font)
        
        self.well_positions = []
        if self.selection_enabled:            
            dc.SetBrush(wx.Brush((255,255,255)))
        else:
            dc.SetBrush(wx.Brush((230,230,230)))
        
        # for each well time independently find out whether it had been affect by any event if so
        # color it dc.SetBrush(wx.Brush((255,255,204)))
        
        for x in range(COLS + 1):
            for y in range(ROWS + 1):
                px = PAD + GAP/2. + (x * R*2)
                py = PAD + GAP/2. + (y * R*2) 
                if self.selection_enabled:
                    if (y-1, x-1) in self.selection:
                        dc.SetPen(wx.Pen("BLACK", 2))
                        dc.SetBrush(wx.Brush("YELLOW"))
                    elif (y-1, x-1) in self.marked:
                        dc.SetPen(wx.Pen("BLACK", 2, style=wx.SHORT_DASH))
                        dc.SetBrush(wx.Brush("#FFFFE0"))
                    else:
                        dc.SetPen(wx.Pen((210,210,210), 1))
                        dc.SetBrush(wx.Brush("WHITE"))
                else:
                    dc.SetPen(wx.Pen("GRAY", 0))
                    dc.SetBrush(wx.Brush("LIGHT GRAY"))

                if y==0 and x!=0:
                    dc.DrawText(self.col_labels[x-1], px, py)
                elif y!=0 and x==0:
                    dc.DrawText(self.row_labels[y-1], px + font.GetPixelSize()[0]/2., py)
                elif y == x == 0:
                    pass
                else:
                    if self.well_disp == ROUNDED:
                        dc.DrawRoundedRectangle(px, py, R*2, R*2, R*0.75)
                    elif self.well_disp == CIRCLE:
                        dc.DrawCircle(px+R, py+R, R)
                    elif self.well_disp == SQUARE:
                        dc.DrawRectangle(px, py, R*2, R*2)
            
        dc.EndDrawing()

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.Refresh()
            self.repaint = False

    def add_well_selection_handler(self, handler):
        '''handler -- a function to call on well selection. 
        The handler must be defined as follows: handler(WellUpdateEventplatewell_id, selected)
        where platewell_id is the clicked well's platewell_id and 
        selected is a boolean for whether the well is now selected.
        '''
        self.well_selection_handlers += [handler]
            
    def _on_click(self, evt):
        if self.selection_enabled == False:
            return
        well = self.get_well_pos_at_xy(evt.X, evt.Y)
        if well is None:
            return        
        selected = self.toggle_selected(well)
        for handler in self.well_selection_handlers:
            handler(self.get_platewell_id_at_xy(evt.X, evt.Y), selected)   
            
            
class VesselScroller(wx.ScrolledWindow):
    '''Scrolled window that displays a set of vessel panels with text labels
    '''
    def __init__(self, parent, id=-1, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, id, **kwargs)
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        (w,h) = self.Sizer.GetSize()
        self.SetScrollbars(20,20,w/20,h/20,0,0)
        self.vessels = {}
        # TODO: Update self when vessels are removed from the experiment.

    def add_vessel_panel(self, panel, vessel_id):
        if len(self.Sizer.GetChildren()) > 0:
            self.Sizer.AddSpacer((10,-1))
        sz = wx.BoxSizer(wx.VERTICAL)
        sz.Add(wx.StaticText(self, -1, vessel_id), 0, wx.EXPAND|wx.TOP|wx.LEFT, 10)
        sz.Add(panel, 1, wx.EXPAND|wx.ALIGN_CENTER)
        self.Sizer.Add(sz, 1, wx.EXPAND)
        self.vessels[vessel_id] = panel

    def get_vessels(self):
        return self.vessels.values()
    
    def get_vessel(self, vessel_id):
        '''returns the vessel matching the given vessel_id or None
        vessel_id -- the first part of a platewell_id tuple
        '''
        return self.vessels[vessel_id]

    def get_selected_platewell_ids(self):
        well_ids = []
        for v in self.get_vessels():
            well_ids += v.get_selected_platewell_ids()
        return well_ids

    def clear(self):
        self.vessels = {}
        self.Sizer.Clear(deleteWindows=True)
        
        
class VesselSelectionPopup(wx.Dialog):
    '''Dialog that presents the user with a vesselscroller from which to choose 
    vessels.
    Used for reseeding.
    '''
    def __init__(self, parent, **kwargs):
        wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwargs)
        label = wx.StaticText(self, -1, 'Specify the destination vessel(s) where cells were transfered.')
        font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL)
        label.SetFont(font)
        self.vpanel = VesselScroller(self)
        for plate_id in PlateDesign.get_plate_ids():
            self.vpanel.add_vessel_panel(
                VesselPanel(self.vpanel, plate_id),
                plate_id)
        self.done = wx.Button(self, wx.ID_OK, 'Done')
        self.cancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.done)
        button_sizer.AddSpacer((10,-1))
        button_sizer.Add(self.cancel)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(label, 0, wx.ALL, 20)
        self.Sizer.Add(self.vpanel, 1, wx.EXPAND|wx.ALL, 10)
        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.RIGHT|wx.BOTTOM, 10)
                
    def get_selected_platewell_ids(self):
        return self.vpanel.get_selected_platewell_ids()
            
        

        
if __name__ == "__main__":
    app = wx.PySimpleApp()
        
    f = wx.Frame(None, size=(900.,800.))
    
    from experimentsettings import P12, P96
    ps = VesselScroller(f)
    
    PlateDesign.add_plate('1', P12)
    vp = VesselPanel(ps, '1')
    ps.add_vessel_panel(vp, '1')
    
    PlateDesign.add_plate('2', P96)
    vp = VesselPanel(ps, '2')

    ps.add_vessel_panel(vp, '2')
##    f.Show()

    VesselSelectionPopup(None, size=(600,400)).ShowModal()

    app.MainLoop()



