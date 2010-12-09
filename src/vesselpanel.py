import wx
import numpy as np
from experimentsettings import *

# Well Displays
ROUNDED   = 'rounded'
CIRCLE    = 'circle'
SQUARE    = 'square'

all_well_shapes = [SQUARE, ROUNDED, CIRCLE]

class VesselPanel(wx.Panel):    
    def __init__(self, parent, plate_id, well_disp=ROUNDED, **kwargs):
        '''
        parent -- wx parent window
        plate_id -- a plate_id registered in the PlateDesign class
        well_disp -- ROUNDED, CIRCLE, SQUARE, THUMBNAIL or IMAGE
        '''
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.plate_id = plate_id
        self.well_disp = well_disp
        self.selection = set([])           # list of (row,col) tuples 
        self.selection_enabled = True
        self.repaint = False
        self.well_selection_handlers = []  # funcs to call when a well is selected        
        # drawing parameters
        self.PAD = 10.0
        self.GAP = 0.5
        self.WELL_R = 1.0
        
        self.shape = PlateDesign.get_plate_format(self.plate_id)
        self.row_labels = PlateDesign.get_row_labels(self.shape)
        self.col_labels = PlateDesign.get_col_labels(self.shape)
        
        # minimum 5 sq. pixels per cell
        long_edge = max(self.shape)
        self.SetMinSize(((long_edge + 1) * 8.0, 
                         (long_edge + 1) * 8.0))

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_SIZE, self._on_size)
        self.Bind(wx.EVT_IDLE, self._on_idle)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_click)
        
    def get_plate_id(self):
        return self.plate_id

    def set_well_display(self, well_disp):
        '''
        well_disp in PlatMapPanel.ROUNDED,
                     PlatMapPanel.CIRCLE,
                     PlatMapPanel.SQUARE
        '''
        self.well_disp = well_disp
        self.Refresh()

    def enable_selection(self):
        self.selection_enabled = True
        self.Refresh()
        
    def disable_selection(self):
        self.selection_enabled = False
        self.Refresh()
        
    def set_selected_well_ids(self, wellids):
        '''selects the wells corresponding to the specified wellids or 
        platewell_ids
        '''
        self.selection = set([PlateDesign.get_pos_for_wellid(self.shape, wellid)
                              for wellid in wellids])
        self.Refresh()
        
    def select_well_at_pos(self, (wellx, welly)):
        self.selection = set([(wellx, welly)])
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
        if (row > self.shape[0] or row < 0 or
            col > self.shape[1] or col < 0):
            return None
        return (int(row), int(col))

    def get_well_id_at_xy(self, px, py):
        '''returns the well_id at the pixel coord px,py
        '''
        return PlateDesign.get_well_id_at_pos(self.shape, self.get_well_pos_at_xy(px,py))

    def get_platewell_id_at_xy(self, px, py):
        '''returns the platewell_id at the pixel coord px,py
        '''
        return (self.plate_id, self.get_well_id_at_xy(px, py))
    
    def get_selected_well_ids(self):
        return [PlateDesign.get_well_id_at_pos(self.shape, pos) 
                for pos in self.selection]
    
    def _on_paint(self, evt=None):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        PAD = self.PAD
        GAP = self.GAP
        ROWS, COLS = self.shape

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
        for x in range(COLS + 1):
            for y in range(ROWS + 1):
                px = PAD + GAP/2. + (x * R*2)
                py = PAD + GAP/2. + (y * R*2)
                
                if (y-1, x-1) in self.selection:
                    if self.selection_enabled:
                        dc.SetPen(wx.Pen("BLACK",4))
                    else:
                        dc.SetPen(wx.Pen("GRAY",4))
                else:
                    dc.SetPen(wx.Pen((210,210,210),1))

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
        
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    f = wx.Frame(None, size=(900.,800.))
    
    from bench import PlateScroller
    ps = PlateScroller(f)
    
    PlateDesign.add_plate('1', P1536)
    vp = VesselPanel(ps, '1')
    ps.add_vessel_panel(vp, '1')
    
    PlateDesign.add_plate('2', P96)
    vp = VesselPanel(ps, '2')

    ps.add_vessel_panel(vp, '2')
    f.Show()

    app.MainLoop()



