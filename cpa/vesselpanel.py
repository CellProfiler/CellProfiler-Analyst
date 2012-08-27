import wx
import icons
from experimentsettings import *
from wx.lib.masked import NumCtrl

#Icon Size
ICON_SIZE = 22.0
# Well Display
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
        wx.Panel.__init__(self, parent, style=wx.BORDER_SUNKEN, **kwargs)
        
        self.vessel = PlateDesign.get_vessel(plate_id)
        self.well_disp = well_disp
        self.selection = set()           # list of (row,col) tuples
	self.wells_with_status = set()     # list of (row, col) where at least one event occured before the current timepoint
        self.marked = set()
        self.selection_enabled = True
        self.repaint = False
        self.well_selection_handlers = []  # funcs to call when a well is selected
        # drawing parameters
        self.PAD = 10.0
        self.GAP = 0.5
        self.WELL_R = 1.0
	self.vpanel = VesselScroller(self)
        
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
        
        #right click menu for cell transfer
        self.popupmenu = wx.Menu()
        item = self.popupmenu.Append(-1, 'Harvest')
        self.Bind(wx.EVT_MENU, self.OnPopupItemSelected, item)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnShowPopup)
	
        self.rect = None
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)
	self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.on_mouse_capture_lost)
	
    def on_mouse_down(self, event):
        self.rect = (event.GetPosition().x,
                     event.GetPosition().y,
                     event.GetPosition().x,
                     event.GetPosition().y)
	self.CaptureMouse()
    
    def on_mouse_move(self, event):
        if self.rect is None:
            return
        x0, y0 = self.rect[:2]
        x1 = event.GetPosition().x
        y1 = event.GetPosition().y
        self.rect = (x0, y0, x1, y1)
        self.Refresh(eraseBackground=False)
    
    def on_mouse_up(self, event):
	if self.rect is None:
	    return
        x0, y0, x1, y1 = self.rect
	self.on_well_selection(x0, y0, x1, y1)
        # Do something
        self.rect = None
        self.Refresh(eraseBackground=False)
	self.ReleaseMouse()
    
    def on_mouse_capture_lost(self, event):
	self.rect = None
	self.Refresh(eraseBackground=False)
	
    def OnShowPopup(self, event):
        self.rclick_pos = event.GetPosition()
        self.rclick_pos = self.ScreenToClient(self.rclick_pos)
        self.PopupMenu(self.popupmenu, self.rclick_pos)
        
    def OnPopupItemSelected(self, event):
	harvest_from_well = self.get_platewell_id_at_xy(self.rclick_pos.x,self.rclick_pos.y)
        sample_instances = [meta.get_sampleInstance(instance) for instance in meta.get_seeded_sample(harvest_from_well)]
        # TO DO: only take the last seeding cell line instance, however if it is co-culture (with multiple cell line seeded in different time points
        # then we need to think of multiple cell line specific GUI for a given well
	
	# TO DO check the validity of the well - i.e. it has cell lines in it. not harvested before etc.
        sample_inst = str(sample_instances.pop())
        new_harvest_inst = meta.get_new_protocol_id('CellTransfer|Harvest')
        new_seed_inst = meta.get_new_protocol_id('CellTransfer|Seed')
	cell_line = meta.get_field('StockCulture|Sample|CellLine|%s'%meta.get_field('CellTransfer|Seed|StockInstance|%s'%sample_inst))
        #establish connection with the Bench panel
        try:
            bench = wx.GetApp().get_bench()
        except: 
            return         
       
    # get the timepoint this harvest event being occuring
    # pop up the dialog to show the available wells to be transferred, including the own, and highlight/disable origin well    
        dlg = VesselSelectionPopup(self, sample_inst, cell_line)
        if dlg.ShowModal() == wx.ID_OK:           
            destination_wells = dlg.get_selected_platewell_ids()
            assert destination_wells
	    
	    meta.set_field('CellTransfer|Harvest|StockInstance|%s'%new_harvest_inst, sample_inst)
	    meta.set_field('CellTransfer|Harvest|HarvestingDensity|%s'%new_harvest_inst, [dlg.h_cell_density.GetValue(), dlg.h_cell_dunit.GetStringSelection()])
	    meta.set_field('CellTransfer|Harvest|MediumAddatives|%s'%new_harvest_inst, dlg.h_medium.GetValue())
	    meta.set_field('CellTransfer|Harvest|Wells|%s|%s'%(new_harvest_inst, bench.get_selected_timepoint()), [harvest_from_well])
	    
	    meta.set_field('CellTransfer|Seed|HarvestInstance|%s'%new_seed_inst, new_harvest_inst)
	    meta.set_field('CellTransfer|Seed|SeedingDensity|%s'%new_seed_inst, [dlg.s_cell_density.GetValue(), dlg.s_cell_dunit.GetStringSelection()])
	    meta.set_field('CellTransfer|Seed|MediumAddatives|%s'%new_seed_inst,dlg.s_medium.GetValue())	    
            meta.set_field('CellTransfer|Seed|Wells|%s|%s'%
                           (new_seed_inst, bench.get_selected_timepoint() + 1), # For now all reseeding instances are set 1 minute after harvesting
                           destination_wells)
	    #bench.update_well_selections()
        #else:
            #self.vesselscroller.get_vessel(platewell_id[0]).deselect_well_id(platewell_id)
            #return
        
           

        
                
    def get_plate_id(self):
        return self.vessel.vessel_id  

    def set_well_display(self, well_disp):
        '''well_disp in PlatMapPanel.ROUNDED,
                        PlatMapPanel.CIRCLE,
                        PlatMapPanel.SQUARE
        '''
        self.well_disp = well_disp
        self.Refresh(eraseBackground=False)

    def enable_selection(self, enabled=True):
        self.selection_enabled = enabled
	self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))
        self.Refresh(eraseBackground=False)
        
    def disable_selection(self):
        self.selection_enabled = False
	self.SetCursor(wx.StockCursor(wx.CURSOR_BLANK))
        self.Refresh(eraseBackground=False)
        
    def set_selected_well_ids(self, wellids):
        '''selects the wells corresponding to the specified wellids or 
        platewell_ids
        '''
        self.selection = set([PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid)
                              for wellid in wellids])
        self.Refresh(eraseBackground=False)
	
    def set_well_ids_state(self, wellids):
	'''set the well ids (row, col) tuples as the filled with event 
	'''
	self.wells_with_status = set([PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid)
                              for wellid in wellids])
	self.Refresh(eraseBackground=False)	
        
    def set_marked_well_ids(self, wellids):
        '''selects the wells corresponding to the specified wellids or 
        platewell_ids
        '''
        self.marked = set([PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid)
                           for wellid in wellids])
        self.Refresh(eraseBackground=False)

    def select_well_id(self, wellid):
        self.select_well_at_pos(PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid))
        
    def deselect_well_id(self, wellid):
        self.deselect_well_at_pos(PlateDesign.get_pos_for_wellid(self.vessel.shape, wellid))
        
    def select_well_at_pos(self, (wellx, welly)):
        self.selection.add((wellx, welly))
        self.Refresh(eraseBackground=False)

    def deselect_well_at_pos(self, (wellx, welly)):
        self.selection.remove((wellx, welly))
        self.Refresh(eraseBackground=False)

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
    
    def get_current_timepoint(self):
	try:
	    bench = wx.GetApp().get_bench()
	except: return
	return bench.time_slider.GetValue()
    
    def get_platewell_state(self):
	'''state: whether any event e.g sample, perturbation occured to the wells of this plate before the timepoint'''
	all_pw_ids = PlateDesign.get_all_platewell_ids()
	timeline = meta.get_timeline()
	
	return [set(timeline.get_well_ids(utp)) & set(all_pw_ids) for utp in timeline.get_unique_timepoints()
	 if utp <= self.get_current_timepoint()]

    
    def _on_paint(self, evt=None):
        dc = wx.BufferedPaintDC(self)
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
            font.SetPixelSize((R-10, f(R-10)*2))
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
        
        # get the affected plate_well ids upto the current timepoint
	#self.set_selected_well_ids(list(self.get_platewell_state()[0]))	
	
	
        for x in range(COLS + 1):
            for y in range(ROWS + 1):
                px = PAD + GAP/2. + (x * R*2)
                py = PAD + GAP/2. + (y * R*2) 
		
		# instead of selection, we define the well state whether they have cells/sample/at least one event occured before this timepoint 
		# dc.SetBrush(wx.Brush('<Yellow/White>', wx.CROSSDIAG_HATCH))
		#### change here for the defining the well state ###
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
			
		    if (y-1, x-1) in self.wells_with_status:
			dc.SetBrush(wx.Brush('RED', wx.CROSSDIAG_HATCH))
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
            
	if self.rect is not None:
	    x0, y0, x1, y1 = self.rect
	    x = min(x0, x1)
	    y = min(y0, y1)
	    w = max(x0, x1) - x
	    h = max(y0, y1) - y    
	    dc.SetBrush(wx.Brush(wx.Color(0, 0, 0), wx.TRANSPARENT))
	    dc.SetPen(wx.BLACK_PEN)
	    dc.DrawRectangle(x, y, w, h)    
        dc.EndDrawing()

    def _on_size(self, evt):
        self.repaint = True

    def _on_idle(self, evt):
        if self.repaint:
            self.Refresh(eraseBackground=False)
            self.repaint = False

    def add_well_selection_handler(self, handler):
        '''handler -- a function to call on well selection. 
        The handler must be defined as follows: handler(WellUpdateEventplatewell_id, selected)
        where platewell_id is the clicked well's platewell_id and 
        selected is a boolean for whether the well is now selected.
        '''
        self.well_selection_handlers += [handler]
    #----------------------------------------------------------------------
    def on_well_selection(self, x0, y0, x1, y1):
	"""get all plate well ids for the selected region"""
	if self.selection_enabled == False:
		    return	
	
	wells = set([ self.get_well_pos_at_xy(X, Y)
	 for X in range(x0, x1+1)
	    for Y in range(y0, y1+1)
	     if self.get_well_pos_at_xy(X, Y) is not None])
	if not wells:
	    return
	for well in wells:
	    selected = self.toggle_selected(well)
	    for handler in self.well_selection_handlers:
		handler(self.get_selected_platewell_ids(), selected) 	
		

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
        stack_name = PlateDesign.get_plate_group(vessel_id)
        sz.Add(wx.StaticText(self, -1, stack_name+'_'+vessel_id), 0, wx.EXPAND|wx.TOP|wx.LEFT, 10)
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
    #def __init__(self, parent, **kwargs):
	    #wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwargs)    
    def __init__(self, parent, sample_inst, cell_line):
	wx.Dialog.__init__(self, parent, -1, size=(600,500), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
	
	self.sample_inst = sample_inst
	self.cell_line = cell_line
	
	
	#------- Harvesting ---#
	h_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
	
	pic=wx.StaticBitmap(self)
	pic.SetBitmap(icons.harvest.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap())
	text = wx.StaticText(self, -1, 'Harvest')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD)
	text.SetFont(font)
	h_titleSizer = wx.BoxSizer(wx.HORIZONTAL)
	h_titleSizer.Add(pic)
	h_titleSizer.AddSpacer((5,-1))	
	h_titleSizer.Add(text, 0)	
	h_titleSizer.Add((-1,5))
        # Cell Line 
	self.h_cell_line = wx.TextCtrl(self, -1, value=self.cell_line, style=wx.TE_PROCESS_ENTER) 
	self.h_cell_line.Disable()
	h_fgs.Add(wx.StaticText(self, -1, 'Cell Line'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	h_fgs.Add(self.h_cell_line, 0, wx.EXPAND)
	h_fgs.Add(wx.StaticText(self, -1, ''), 0)
	# Density - value
	harvestdensity = meta.get_field('CellTransfer|Seed|SeedingDensity|%s'%self.sample_inst, [])
	self.h_cell_density = wx.lib.masked.NumCtrl(self, size=(20,-1), style=wx.TE_PROCESS_ENTER)
	if len(harvestdensity) > 0:
	    self.h_cell_density.SetValue(harvestdensity[0])		
	unit_choices =['nM2', 'uM2', 'mM2','Other']	
	self.h_cell_dunit = wx.ListBox(self, -1, wx.DefaultPosition, (50,20), unit_choices, wx.LB_SINGLE)
	if len(harvestdensity) > 1:
	    self.h_cell_dunit.SetStringSelection(harvestdensity[1])
	h_fgs.Add(wx.StaticText(self, -1, 'Density'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	h_fgs.Add(self.h_cell_density, 0, wx.EXPAND)	
	h_fgs.Add(self.h_cell_dunit, 0, wx.EXPAND)
	# Medium
	self.h_medium = wx.TextCtrl(self, -1, value=meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%self.sample_inst, default=''), style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE) 
	h_fgs.Add(wx.StaticText(self, -1, 'Medium Additives'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	h_fgs.Add(self.h_medium, 0, wx.EXPAND)
	h_fgs.Add(wx.StaticText(self, -1, ''), 0) 	
	
	hSizer = wx.BoxSizer(wx.VERTICAL)
	hSizer.Add(h_titleSizer)
	hSizer.AddSpacer((-1,10))
	hSizer.Add(h_fgs)
	
	#------- Seeding ---#
	s_fgs = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)
	
	pic=wx.StaticBitmap(self)
	pic.SetBitmap(icons.seed.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap())
	text = wx.StaticText(self, -1, 'Seed')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.BOLD)
	text.SetFont(font)
	s_titleSizer = wx.BoxSizer(wx.HORIZONTAL)
	s_titleSizer.Add(pic)
	s_titleSizer.AddSpacer((5,-1))	
	s_titleSizer.Add(text, 0)	
	s_titleSizer.Add((-1,5))
	# Cell Line 
	self.s_cell_line = wx.TextCtrl(self, -1, value=self.cell_line, style=wx.TE_PROCESS_ENTER) 
	self.s_cell_line.Disable()
	s_fgs.Add(wx.StaticText(self, -1, 'Cell Line'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	s_fgs.Add(self.s_cell_line, 0, wx.EXPAND)
	s_fgs.Add(wx.StaticText(self, -1, ''), 0)
	# Density - value
	seeddensity = meta.get_field('CellTransfer|Seed|SeedingDensity|%s'%self.sample_inst, [])
	self.s_cell_density = wx.lib.masked.NumCtrl(self, size=(20,-1), style=wx.TE_PROCESS_ENTER)
	if len(seeddensity) > 0:
	    self.s_cell_density.SetValue(seeddensity[0])			
	self.s_cell_dunit = wx.ListBox(self, -1, wx.DefaultPosition, (50,20), unit_choices, wx.LB_SINGLE)
	if len(seeddensity) > 1:
	    self.s_cell_dunit.SetStringSelection(seeddensity[1])
	s_fgs.Add(wx.StaticText(self, -1, 'Density'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	s_fgs.Add(self.s_cell_density, 0, wx.EXPAND)	
	s_fgs.Add(self.s_cell_dunit, 0, wx.EXPAND)	
	# Medium
	self.s_medium = wx.TextCtrl(self, -1, value=meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%self.sample_inst, default=''), style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE) 
	s_fgs.Add(wx.StaticText(self, -1, 'Medium Additives'), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
	s_fgs.Add(self.s_medium, 0, wx.EXPAND)
	s_fgs.Add(wx.StaticText(self, -1, ''), 0)   
	
	sSizer = wx.BoxSizer(wx.VERTICAL)
	sSizer.Add(s_titleSizer)
	sSizer.AddSpacer((-1,10))
	sSizer.Add(s_fgs)	
	
	infoSizer = wx.BoxSizer(wx.HORIZONTAL)
	infoSizer.AddSpacer((10,-1))
	infoSizer.Add(hSizer)
	infoSizer.AddSpacer((50,-1))
	infoSizer.Add(sSizer)
               
        
        # VESSEL Panel 
        label = wx.StaticText(self, -1, 'Select Destination Vessel(s)')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        label.SetFont(font)
        self.vpanel = VesselScroller(self)
        for plate_id in PlateDesign.get_plate_ids():
            self.vpanel.add_vessel_panel(
                VesselPanel(self.vpanel, plate_id),
                plate_id)
        self.done = wx.Button(self, wx.ID_OK, 'Transfer')
        self.cancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(self.done)
        button_sizer.AddSpacer((10,-1))
        button_sizer.Add(self.cancel)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(infoSizer, 0, wx.EXPAND|wx.TOP, 10)
	self.Sizer.AddSpacer((5,-1))
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(label, 0, wx.ALL, 20)
        self.Sizer.Add(self.vpanel, 1, wx.EXPAND|wx.ALL, 10)
        self.Sizer.Add(button_sizer, 0, wx.EXPAND|wx.RIGHT|wx.BOTTOM, 10)
                
    def get_selected_platewell_ids(self):
        return self.vpanel.get_selected_platewell_ids()
            
        

        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    f = wx.Frame(None, size=(900.,800.))
    VesselSelectionPopup(None, size=(600,400)).ShowModal()
    app.MainLoop()



