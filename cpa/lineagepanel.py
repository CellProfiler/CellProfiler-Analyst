import experimentsettings as exp
import wx
import os
import subprocess
import numpy as np
import icons
import timeline
import  wx.lib.dialogs
import math
import bisect
import csv
from wx.lib.combotreebox import ComboTreeBox
from PIL import Image
from time import time
from datalinkList import *
from notepad import NotePad

# x-spacing modes for timeline and lineage panels
SPACE_EVEN = 0
SPACE_TIME = 1
SPACE_TIME_COMPACT = 2

meta = exp.ExperimentSettings.getInstance()

class LineageFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='Visualization Panel', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        
        sw = wx.ScrolledWindow(self)
        self.sw = sw
        timeline_panel = TimelinePanel(sw)
        self.timeline_panel = timeline_panel
        lineage_panel = LineagePanel(sw)
        self.lineage_panel = lineage_panel
        timeline_panel.set_style(padding=20)
        lineage_panel.set_style(padding=20, flask_gap = 40)
        sw.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sw.Sizer.Add(timeline_panel, 0, wx.EXPAND|wx.LEFT, 40)
        sw.Sizer.Add(lineage_panel, 1, wx.EXPAND)
        sw.SetScrollbars(20, 20, self.Size[0]/20, self.Size[1]/20, 0, 0)
        sw.Fit()
        
        #tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        #tb.AddControl(wx.StaticText(tb, -1, 'zoom'))
        #self.zoom = tb.AddControl(wx.Slider(tb, -1, style=wx.SL_AUTOTICKS|wx.VERTICAL)).GetControl()
        #self.zoom.SetRange(1, 30)
        #self.zoom.SetValue(8)
        ##x_spacing = tb.AddControl(wx.CheckBox(tb, -1, 'Time-relative branches'))
        ##x_spacing.GetControl().SetValue(0)
        ##generate = tb.AddControl(wx.Button(tb, -1, '+data'))        
        #tb.Realize()
        
        #from f import TreeCtrlComboPopup
        #cc = wx.combo.ComboCtrl(sw)
        #self.tcp = TreeCtrlComboPopup()
        #cc.SetPopupControl(self.tcp)
        #sw.Sizer.Add(cc)
        #meta.add_subscriber(self.on_metadata_changed, '')
        
        #self.Bind(wx.EVT_SLIDER, self.on_zoom, self.zoom)
        #self.Bind(wx.EVT_CHECKBOX, self.on_change_spacing, x_spacing)
        #self.Bind(wx.EVT_BUTTON, self.generate_random_data, generate)
        
    def on_metadata_changed(self, tag):
        self.tcp.Clear()
        alltags = meta.get_field_tags()
        t0 = set([tag.split('|')[0] for tag in alltags])
        for t in t0:
            item1 = self.tcp.AddItem(t)
            t1 = set([tag.split('|')[1] for tag in meta.get_field_tags(t)])
            for tt in t1:
                item2 = self.tcp.AddItem(tt, item1)
                t2 = set([tag.split('|')[2] for tag in meta.get_field_tags('%s|%s'%(t,tt))])
                for ttt in t2:
                    item3 = self.tcp.AddItem(ttt, item2)

    def on_zoom(self, evt):
        self.lineage_panel.set_style(node_radius=self.zoom.GetValue(),
                                     xgap=self.lineage_panel.NODE_R*2+1,
                                     ygap=self.lineage_panel.NODE_R*2+1)
        self.timeline_panel.set_style(icon_size=self.zoom.GetValue()*2,
                                      xgap=self.timeline_panel.ICON_SIZE+2)
        
    def on_change_spacing(self, evt):
        if evt.Checked():
            self.lineage_panel.set_x_spacing(SPACE_TIME)
            self.timeline_panel.set_x_spacing(SPACE_TIME)
        else:
            self.lineage_panel.set_x_spacing(SPACE_EVEN)
            self.timeline_panel.set_x_spacing(SPACE_EVEN)
    
    def generate_random_data(self, evt=None):
        exp.PlateDesign.add_plate('test', PLATE_TYPE)
        allwells = exp.PlateDesign.get_well_ids(exp.PlateDesign.get_plate_format('test'))
        event_types = ['AddProcess|Stain|Wells|0|',
                       'AddProcess|Wash|Wells|0|',
                       'AddProcess|Dry|Wells|0|',
                       'AddProcess|Spin|Wells|0|',
                       'Perturbation|Chem|Wells|0|',
                       'Perturbation|Bio|Wells|0|',
                       'DataAcquis|TLM|Wells|0|',
                       'DataAcquis|FCS|Wells|0|',
                       'DataAcquis|HCS|Wells|0|',
                       'CellTransfer|Seed|Wells|0|',
                       'CellTransfer|Harvest|Wells|0|']
        # GENERATE RANDOM EVENTS ON RANDOM WELLS
        for t in list(np.random.random_integers(0, MAX_TIMEPOINT, N_TIMEPOINTS)):
            for j in range(np.random.randint(1, N_FURCATIONS)):
                np.random.shuffle(allwells)
                well_ids = [('test', well) for well in allwells[:np.random.randint(1, len(allwells)+1)]]
                #timeline.add_event(t, 'event%d'%(t), well_ids)
                etype = event_types[np.random.randint(0,len(event_types))]
                meta.set_field('%s%s'%(etype, t), well_ids)
		
    def set_hover_timepoint(self, hover_timepoint):
	self.timeline_panel.hover_timepoint = hover_timepoint
	self.lineage_panel.set_timepoint(hover_timepoint)


class TimelinePanel(wx.Panel):
    '''An interactive timeline panel
    '''
    # Drawing parameters
    PAD = 0.0
    ICON_SIZE = 16.0
    MIN_X_GAP = ICON_SIZE + 2
    TIC_SIZE = 10
    FONT_SIZE = (5,10)
    NOTE_ICON_FACTOR = 0.0

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)

        meta.add_subscriber(self.on_timeline_updated, exp.get_matchstring_for_subtag(2, 'Well'))
        self.timepoints = None
        self.events_by_timepoint = None
        self.cursor_pos = None
        self.hover_timepoint = None
        self.time_x = False
        
        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_exit)
        self.Bind(wx.EVT_LEFT_UP, self._on_click)
        
    def set_style(self, padding=None, xgap=None, icon_size=None):
        if padding is not None:
            self.PAD = padding
        if xgap is not None:
            self.MIN_X_GAP = xgap
        if icon_size is not None:
            self.ICON_SIZE = icon_size
        self._recalculate_min_size()
        self.Refresh(eraseBackground=False)
        self.Parent.FitInside()
        
    def set_x_spacing(self, mode):
        if mode == SPACE_TIME:
            self.time_x = True
        elif mode == SPACE_EVEN:
            self.time_x = False
        self._recalculate_min_size()
        self.Refresh(eraseBackground=False)
        self.Parent.FitInside()

    def on_timeline_updated(self, tag):
        timeline = meta.get_timeline()
        self.events_by_timepoint = timeline.get_events_by_timepoint()
        self.timepoints = timeline.get_unique_timepoints()
         #for time compact x-spacing
        if len(self.timepoints) > 1:
            self.min_time_gap = min([y-x for x,y in zip(self.timepoints[:-1], 
                                                        self.timepoints[1:])])
        else:
            self.min_time_gap = 1
        self._recalculate_min_size()
        self.Refresh(eraseBackground=False)
        self.Parent.FitInside()
	
    def on_note_icon_add(self):
	note_num = {}
	for tag in meta.global_settings: 
	    if tag.startswith('Notes'):
		timepoint = exp.get_tag_attribute(tag)
		if not timepoint in note_num:
		    note_num[timepoint] = 1
		else:
		    note_num[timepoint] += 1	
	if note_num:
	    self.NOTE_ICON_FACTOR = (max(note_num.values())+1) * self.ICON_SIZE
	    self._recalculate_min_size()
	    self.Refresh(eraseBackground=False)
	    self.Parent.FitInside()	
	
    def _recalculate_min_size(self):
        if self.timepoints is not None and len(self.timepoints) > 0:
	    min_h = self.NOTE_ICON_FACTOR + self.PAD * 2 + self.FONT_SIZE[1] + self.TIC_SIZE * 2 + 1
            if self.time_x:
                self.SetMinSize((self.PAD * 2 + self.MIN_X_GAP * self.timepoints[-1], min_h))
            else:
                self.SetMinSize((len(self.timepoints) * self.MIN_X_GAP + self.PAD * 2, min_h))

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        if not self.timepoints:
            evt.Skip()
            return

        PAD = self.PAD + self.ICON_SIZE / 2.0
        ICON_SIZE = self.ICON_SIZE
        MIN_X_GAP = self.MIN_X_GAP
        TIC_SIZE = self.TIC_SIZE
        FONT_SIZE = self.FONT_SIZE
        MAX_TIMEPOINT = self.timepoints[-1]
	WIGGEL_NUM = 100
        self.hover_timepoint = None
	self.current_ntag = None
	self.on_note_icon_add()

        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        if self.time_x:
            if MAX_TIMEPOINT == 0:
                px_per_time = 1
            else:
                px_per_time = max((w_win - PAD * 2.0) / MAX_TIMEPOINT,
                                  MIN_X_GAP)
	else:
	    px_per_time = 1
        
        if len(self.timepoints) == 1:
            x_gap = 1
        else:
            x_gap = max(MIN_X_GAP, 
                        (w_win - PAD * 2) / (len(self.timepoints) - 1))

        # y pos of line
        y = h_win - PAD - FONT_SIZE[1] - TIC_SIZE - 1
	
	
	def icon_hover(mouse_pos, icon_pos, icon_size):
	    '''returns whether the mouse is hovering over an icon
	    '''
	    if mouse_pos is None:
		return False
	    MX,MY = mouse_pos
	    X,Y = icon_pos
	    return (X - icon_size/2.0 < MX < X + icon_size/2.0 and 
	            Y - icon_size/2.0 < MY < Y + icon_size/2.0)	

	# draw the timeline
	if self.time_x:	    
	    dc.DrawLine(PAD, y, 
	                px_per_time * MAX_TIMEPOINT + PAD, y)
	else:   
	    dxs = range(WIGGEL_NUM+1)
	    dxs = [float(dx)/WIGGEL_NUM for dx in dxs]

	    x = PAD
	    for i, timepoint in enumerate(self.timepoints):
		if i > 0:
		    n = math.sqrt(((self.timepoints[i]-self.timepoints[i-1])))  #instead of log can use square root
		    ys = [5*(math.sin((math.pi)*dx))*math.sin(2*math.pi*dx*n) for dx in dxs] # 10 is px height fow wiggles can change it
		    for p, dx in enumerate(dxs[:-1]):
			dc.DrawLine(x+x_gap*dxs[p], y+ys[p], x+x_gap*dxs[p+1], y+ys[p+1])
		    x += x_gap

	font = dc.Font
	font.SetPixelSize(FONT_SIZE)
	dc.SetFont(font)
	
	# draw the ticks
        for i, timepoint in enumerate(self.timepoints):
	    # if data acquisition is the only event in this timepoint skip it
	    #evt_categories = list(set([exp.get_tag_stump(ev.get_welltag(), 1) for ev in self.events_by_timepoint[timepoint]]))
	    #if all(evt_categories[0] == cat and cat == 'DataAcquis' for cat in evt_categories):
		#continue
	
            # x position of timepoint on the line
            if self.time_x:
                x = timepoint * px_per_time + PAD
            else:
                x = i * x_gap + PAD
                
            if (self.cursor_pos is not None and 
                x - ICON_SIZE/2 < self.cursor_pos[0] < x + ICON_SIZE/2):
                dc.SetPen(wx.Pen(wx.BLACK, 3))
                self.hover_timepoint = timepoint
            else:
                dc.SetPen(wx.Pen(wx.BLACK, 1))
            # Draw tic marks
            dc.DrawLine(x, y - TIC_SIZE, 
                        x, y + TIC_SIZE)    
	    
	    # Draw the note icon above the tick
	    note_tags = [ tag for tag in meta.global_settings
	                  if tag.startswith('Notes') and exp.get_tag_attribute(tag) == str(timepoint)] 
	    #if note_tags:
		#self.on_note_icon_add()  #update the min_h of the panel
	    for i, ntag in enumerate(note_tags):
		    bmp = icons.note.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap() 		
		    dc.DrawBitmap(bmp, x - ICON_SIZE / 2.0, 
		                    y - ((i+1)*ICON_SIZE) - TIC_SIZE - 1)	
		    
		    if icon_hover(self.cursor_pos, (x - ICON_SIZE / 2.0, 
		                    y - ((i+1)*ICON_SIZE) - TIC_SIZE - 1), ICON_SIZE):
			self.current_ntag = ntag
					#highlight the note icon		    
            		
            # draw the timepoint beneath the line
            time_string = exp.format_time_string(timepoint)
            wtext = FONT_SIZE[0] * len(time_string)
	    htext = FONT_SIZE[1]
            dc.DrawText(time_string, x - wtext/2.0, y + TIC_SIZE + 1)
	    dc.DrawLine(x, y + TIC_SIZE + 1 + htext,  x, h_win)  # extension of tick towards the lineage panel
	    		   
        dc.EndDrawing()

    def _on_mouse_motion(self, evt):
        self.cursor_pos = evt.X, evt.Y
        self.Refresh(eraseBackground=False)

    def _on_mouse_exit(self, evt):
        self.cursor_pos = None
        self.Refresh(eraseBackground=False)
        
    def _on_click(self, evt):
        if self.hover_timepoint is not None:
            try:
                bench = wx.GetApp().get_bench()
            except: return
            bench.set_timepoint(self.hover_timepoint)
            bench.update_well_selections()
	
	if self.current_ntag is not None:
	    note_type = exp.get_tag_event(self.current_ntag)	    
	    timepoint = exp.get_tag_attribute(self.current_ntag)
	    self.page_counter = exp.get_tag_instance(self.current_ntag)
	    
	    
	    note_dia = NotePad(self, note_type, timepoint, self.page_counter)
	    if note_dia.ShowModal() == wx.ID_OK:
		    # Notes|<type>|<timepoint>|<instance> = value
		meta.set_field('Notes|%s|%s|%s' %(note_dia.noteType, timepoint, str(self.page_counter)), note_dia.noteDescrip.GetValue())   	    

class LineagePanel(wx.Panel):
    '''A Panel that displays a lineage tree.
    '''
    # Drawing parameters
    PAD = 30
    NODE_R = 8
    SM_NODE_R = 3
    MIN_X_GAP = NODE_R*2 + 2
    MIN_Y_GAP = NODE_R*2 + 2
    FLASK_GAP = MIN_X_GAP
    #X_SPACING = 'EVEN'

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.SetBackgroundColour('#FAF9F7')

        self.nodes_by_timepoint = {}
        self.time_x = False
        self.cursor_pos = None
        self.current_node = None
	self.timepoint_cursor = None
        
        meta.add_subscriber(self.on_timeline_updated, 
                            exp.get_matchstring_for_subtag(2, 'Well'))

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_exit)
        self.Bind(wx.EVT_LEFT_UP, self._on_mouse_click)
        
    def set_timepoint(self, timepoint):
	self.timepoint_cursor = timepoint
	self.Refresh(eraseBackground=False)
	
    def set_x_spacing(self, mode):
        if mode == SPACE_TIME:
            self.time_x = True
        elif mode == SPACE_EVEN:
            self.time_x = False
        self._recalculate_min_size()
        self.Refresh(eraseBackground=False)
        self.Parent.FitInside()
        
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
        self._recalculate_min_size()
        self.Refresh(eraseBackground=False)
        self.Parent.FitInside()
     
    def on_timeline_updated(self, tag):
        '''called to add events to the timeline and update the lineage
        '''
        timeline = meta.get_timeline()
        t0 = time()
        self.nodes_by_timepoint = timeline.get_nodes_by_timepoint()
      
        #print 'built tree in %s seconds'%(time() - t0)
        # get the unique timpoints from the timeline
        self.timepoints = meta.get_timeline().get_unique_timepoints()
        
        # For time-compact x-spacing
        #if len(self.timepoints) > 1:
            #self.min_time_gap = min([y-x for x,y in zip(self.timepoints[:-1], 
                                                        #self.timepoints[1:])])
        #else:
            #self.min_time_gap = 1
        self.timepoints.reverse()
        self.timepoints.append(-1)

        self._recalculate_min_size()
        self.Refresh(eraseBackground=False)
        self.Parent.FitInside()
        
    def _recalculate_min_size(self):
        timepoints = meta.get_timeline().get_unique_timepoints()
        if len(timepoints) > 0:
            n_leaves = len(self.nodes_by_timepoint.get(timepoints[-1], []))
            if self.time_x:
                self.SetMinSize((self.PAD * 2 + self.MIN_X_GAP * timepoints[-1] + self.FLASK_GAP,
                                 n_leaves * self.MIN_Y_GAP + self.PAD * 2))
            else:
                self.SetMinSize((len(self.nodes_by_timepoint) * self.MIN_X_GAP + self.PAD * 2,
                                 n_leaves * self.MIN_Y_GAP + self.PAD * 2))

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        if self.nodes_by_timepoint == {}:
            evt.Skip()
            return	

        t0 = time()
        PAD = self.PAD + self.NODE_R
        NODE_R = self.NODE_R
	SM_NODE_R = self.SM_NODE_R 
        MIN_X_GAP = self.MIN_X_GAP
        MIN_Y_GAP = self.MIN_Y_GAP
        FLASK_GAP = self.FLASK_GAP
        MAX_TIMEPOINT = self.timepoints[0]
        timepoints = self.timepoints
        nodes_by_tp = self.nodes_by_timepoint
        self.current_node = None           # Node with the mouse over it
        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
	
        if self.time_x:
            if timepoints[0] == 0:
                px_per_time = 1
            else:
                px_per_time = max((w_win - PAD * 2 - FLASK_GAP) / MAX_TIMEPOINT,
                                  MIN_X_GAP)
	else:
	    px_per_time = 1
                
        if len(nodes_by_tp) == 2:
            x_gap = 1
        else:
            # calculate the number of pixels to separate each generation timepoint
            x_gap = max(MIN_X_GAP, 
                         (w_win - PAD * 2 - FLASK_GAP) / (len(nodes_by_tp) - 2))
            
        if len(nodes_by_tp[timepoints[0]]) == 1:
            y_gap = MIN_Y_GAP
        else:
            # calcuate the minimum number of pixels to separate nodes on the y axis
            y_gap = max(MIN_Y_GAP, 
                        (h_win - PAD * 2) / (len(nodes_by_tp[MAX_TIMEPOINT]) - 1))
                        
        nodeY = {}  # Store y coords of children so we can calculate where to draw the parents
        Y = PAD
        X = w_win - PAD
        
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        #dc.SetPen(wx.Pen("BLACK",1))
        
        def hover(mouse_pos, node_pos, node_r):
            '''returns whether the mouse is hovering over a node
            mouse_pos - the mouse position
            node_pos - the node position
            node_r - the node radius
            '''
            if mouse_pos is None:
                return False
            MX,MY = mouse_pos
            X,Y = node_pos
            return (X - node_r < MX < X + node_r and 
                    Y - node_r < MY < Y + node_r)	
	

        # Iterate from leaf nodes up to the root, and draw R->L, Top->Bottom
        for i, t in enumerate(timepoints):
            if t == -1:  # for the root node which is not shown
                X = PAD
            elif self.time_x:
                X = PAD + FLASK_GAP + t * px_per_time
                x_gap = PAD + FLASK_GAP + timepoints[i-1] * px_per_time - X
            else:
                X = PAD + FLASK_GAP + (len(timepoints) - i - 2) * x_gap
		
	    # Draw longitudinal time lines
	    if t != -1:
		dc.SetPen(wx.Pen('#E1E2ED', 1, wx.DOT))
		dc.DrawLine(X, 0, X, h_win)	    
            
            # LEAF NODES
            if i == 0:
                for node in sorted(nodes_by_tp[t], key=self.order_nodes):
		    ancestor_tags = self.get_ancestral_tags(node)	
		    node_tags = node.get_tags()
		    stateRGB = meta.getStateRGB([tags for tags in reversed(ancestor_tags)]+node_tags)# reverse the ancestal line so that it become progeny + curr node			    
		    if node_tags:
			eventRGB = meta.getEventRGB(node_tags[0]) #get all event tags for the passed node and returns the colour associated with the last event** Need to change
		    else:
			eventRGB = (255, 255, 255, 100)
		   
                    empty_path = False # whether this path follows a harvesting
		    event_status = False # whether any event occured to this node		    
		    
                    if len(node.get_tags()) > 0:
                        # Event occurred
			dc.SetBrush(wx.Brush(eventRGB))
			dc.SetPen(wx.Pen(stateRGB, 3))
			event_status = True
			
                    else:
                        # No event
			if eventRGB == (255,255,255,100) and stateRGB == (255,255,255,100):
			    dc.SetBrush(wx.Brush(wx.WHITE))
			    dc.SetPen(wx.Pen(wx.WHITE))	
                        if 'CellTransfer|Harvest' in self.get_ancestral_tags(node):
                            empty_path = True

                    if hover(self.cursor_pos, (X,Y), self.NODE_R):
                        # MouseOver
			if event_status:
			    dc.SetPen(wx.Pen(stateRGB, 1))
			    self.current_node = node
                    else:
                        # No MouseOver
			if event_status:
			    dc.SetPen(wx.Pen(stateRGB, 3))
                    
                    if not empty_path and event_status:
			#dc.DrawCircle(X, Y, NODE_R)
			#evt_categories = list(set([exp.get_tag_stump(tag, 1) for tag in node.get_tags()]))
			#if all(evt_categories[0] == cat and cat == 'DataAcquis' for cat in evt_categories):
			if 'CellTransfer|Seed|StockInstance' in node_tags:
			    event = 'Stock'
			else:
			    event = exp.get_tag_event(node_tags[0])
			
			dc.DrawBitmap(meta.getEventIcon(16.0, event), X - 16.0 / 2.0, Y - 16.0 / 2.0)
##                      dc.DrawText(str(node.get_tags()), X, Y+NODE_R)
                    nodeY[node.id] = Y
                    Y += y_gap
                    
            # INTERNAL NODES
            else:
                for node in sorted(nodes_by_tp[t], key=self.order_nodes):
		    ancestor_tags = self.get_ancestral_tags(node)
		    children_tags = self.get_children_tags(node)
		    node_tags = node.get_tags()
		    stateRGB = meta.getStateRGB([tags for tags in reversed(ancestor_tags)]+node_tags)# reverse the ancestal line so that it become progeny + curr node			    
		    if node_tags:
			eventRGB = meta.getEventRGB(node_tags[0]) #get all event tags for the passed node and returns the colour associated with the last event** Need to change
		    else:
			eventRGB = (255, 255, 255, 100)
		
                    empty_path = False # whether this path follows a harvesting
		    event_status = False # whether this node has event
		    children_status = False # whether the children nodes have any events associated
		    
		    if children_tags:
			children_status = True
		    
                    ys = []
                    for child in node.get_children():
                        ys.append(nodeY[child.id])
                    Y = (min(ys) + max(ys)) / 2
		    
                    if len(node.get_tags()) > 0:
			#Event occurred
                        dc.SetBrush(wx.Brush(eventRGB))
			dc.SetPen(wx.Pen(stateRGB, 3))
			event_status = True			
                    else:
			#No event
			if eventRGB == (255,255,255,100) and stateRGB == (255,255,255,100):
			    dc.SetBrush(wx.Brush(wx.WHITE))
			    dc.SetPen(wx.Pen(wx.WHITE))
			else:
			    if children_status:
				#dc.SetBrush(wx.Brush(wx.BLACK))
				#dc.SetPen(wx.Pen(wx.BLACK))
				dc.SetBrush(wx.Brush('#D1CDCF'))
				dc.SetPen(wx.Pen('#D1CDCF'))
			    else:
				dc.SetBrush(wx.Brush(wx.WHITE))
				dc.SetPen(wx.Pen(wx.WHITE))			    
			    
			if 'CellTransfer|Harvest' in self.get_ancestral_tags(node):
			    empty_path = True
		
                    if hover(self.cursor_pos, (X,Y), self.NODE_R):
                        # MouseOver
			if event_status:
			    dc.SetPen(wx.Pen(stateRGB, 1))
			    self.current_node = node                        
			    self.SetToolTipString(self.ShowTooltipsInfo())
                    else:
                        # No MouseOver
			if event_status:
			    dc.SetPen(wx.Pen(stateRGB, 3))
                    
                    #if t == -1:
                        #dc.DrawRectangle(X-NODE_R, Y-NODE_R, NODE_R*2, NODE_R*2)
                    #else:
		    if not empty_path:
			if event_status:
			    if (node_tags[0].startswith('CellTransfer|Seed') and 
				        meta.get_field('CellTransfer|Seed|StockInstance|'+exp.get_tag_instance(node_tags[0])) is not None):
				event = 'Stock'
			    else:
				event = exp.get_tag_event(node_tags[0])
			    #dc.DrawCircle(X, Y, NODE_R)
			    #dc.SetPen(wx.Pen('BLACK'))
			    #dc.DrawCircle(X, Y, NODE_R-3/2)
			    dc.DrawBitmap(meta.getEventIcon(16.0, event), X - 16.0 / 2.0, Y - 16.0 / 2.0)
				
			else:
			    #dc.DrawCircle(X-NODE_R,Y, SM_NODE_R) # draws the node slightly left hand side on the furcation point
			    #dc.SetBrush(wx.Brush(stateRGB))
			    dc.DrawCircle(X,Y, SM_NODE_R)
			#dc.DrawText(str(node.get_tags()), X, Y+NODE_R)
                        
                    # DRAW LINES CONNECTING THIS NODE TO ITS CHILDREN
                    dc.SetBrush(wx.Brush('#FAF9F7'))
                    #dc.SetPen(wx.Pen(wx.BLACK, 1))
		    dc.SetPen(wx.Pen('#D1CDCF'))
		    #dc.SetPen(wx.Pen(stateRGB))
                    harvest_tag = False
                    for tag in node.get_tags():
                        if tag.startswith('CellTransfer|Harvest'):
                            harvest_tag = tag
		    # for children of this node check whether furhter event had occured to them if not do not draw the line 
                    for child in node.get_children():
			if harvest_tag:
			    # TODO: improve performance by caching reseed 
			    #       events from the previous timepoint
			    for nn in nodes_by_tp[timepoints[i-1]]:
				for tag in nn.get_tags():
				    if (tag.startswith('CellTransfer|Seed') and 
				        meta.get_field('CellTransfer|Seed|HarvestInstance|'+exp.get_tag_instance(tag)) == exp.get_tag_instance(harvest_tag)):
					dc.SetPen(wx.Pen('#948BB3', 1, wx.SHORT_DASH))
					dc.DrawLine(X + NODE_R, Y, 
				                    X + x_gap - NODE_R ,nodeY[nn.id])
			else:
			    if not empty_path:
				if event_status:
				    if children_status:
					dc.DrawLine(X + NODE_R, Y, 
					            X + x_gap - NODE_R, nodeY[child.id])	
				else:
				    if children_status and stateRGB != (255,255,255,100):
					    dc.SetPen(wx.Pen('#D1CDCF'))
					    #dc.SetPen(wx.Pen(stateRGB))
					    dc.DrawLine(X, Y,
						        X + x_gap, nodeY[child.id])
			
                    nodeY[node.id] = Y
		    
		    
	#if self.timepoint_cursor is not None:  # BUG: New addition of 24hr will not work, i.e. the timeline cant hover over no event time zone****
	    #timepoints = meta.get_timeline().get_unique_timepoints()	
	    #ti = bisect.bisect_left(timepoints, self.timepoint_cursor)
	    #time_interval =  timepoints[ti]-timepoints[ti-1]
	    ##according to the time interval calculate the px per time.
	    ##px_per_time = max((w_win - PAD * 2 - FLASK_GAP) / MAX_TIMEPOINT,
			                      ##MIN_X_GAP)	
	    #px_per_ti = (w_win - PAD * 2 - FLASK_GAP) /(len(timepoints)-1)
	    #adjusted_factor = px_per_ti/time_interval
	   
	    #X = PAD + FLASK_GAP +px_per_ti*(ti-1)+(self.timepoint_cursor - timepoints[ti-1])* adjusted_factor
	   
	    #dc.SetPen(wx.Pen(wx.BLACK, 3))
	    #dc.DrawLine(X, 0, X, h_win)
	  
        dc.EndDrawing()
        #print 'rendered lineage in %.2f seconds'%(time() - t0)
        
    def _on_mouse_motion(self, evt):
        self.cursor_pos = (evt.X, evt.Y)
        self.Refresh(eraseBackground=False)

    def _on_mouse_exit(self, evt):
        self.cursor_pos = None
        self.Refresh(eraseBackground=False)

    def _on_mouse_click(self, evt):
        if self.current_node is None:
            return
        
        # --- Update the Bench view ---
        try:
            bench = wx.GetApp().get_bench()
        except: 
            return
	
        bench.set_timepoint(self.current_node.get_timepoint())
        bench.taglistctrl.set_selected_protocols(
            [exp.get_tag_protocol(tag) for tag in self.current_node.get_tags()])
        bench.group_checklist.SetCheckedStrings(
            [exp.PlateDesign.get_plate_group(well[0]) 
             for well in self.current_node.get_well_ids()])
        bench.update_plate_groups()
        bench.update_well_selections()
	bench.del_evt_button.Enable()
	
        # -- Update the expt setting/metadata view --#
        try:
            exptsettings = wx.GetApp().get_exptsettings()
        except:
            return
	
        exptsettings.OnLeafSelect()
        if self.current_node.get_tags():
            exptsettings.ShowInstance(self.current_node.get_tags()[0])
            
        ancestors = [exp.get_tag_stump(ptag, 2)
                     for pnode in timeline.reverse_iter_tree(self.current_node) if pnode
                     for ptag in pnode.tags]   
	
	# -- show the data url list --- #
        data_acquis = False

        for tag in self.current_node.get_tags():
	    if tag.startswith('DataAcquis'):
		data_acquis = True
		break
	    
	if data_acquis:
	    dia = DataLinkListDialog(self, self.current_node.get_well_ids())
	    if dia.ShowModal() == wx.ID_OK:
		if dia.output_options.GetSelection() == 0:
		    file_dlg = wx.FileDialog(None, message='Exporting Data URL...', 
		                             defaultDir=os.getcwd(), defaultFile='data urls', 
		                             wildcard='.csv', 
		                             style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
		    if file_dlg.ShowModal() == wx.ID_OK:
			os.chdir(os.path.split(file_dlg.GetPath())[0])
			myfile = open(file_dlg.GetPath(), 'wb')
			wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
			for row in dia.listctrl.get_selected_urls():
			    wr.writerow(row)
			myfile.close()	
			file_dlg.Destroy()
		if dia.output_options.GetSelection() == 1:
		    file_dlg = wx.FileDialog(None, message='Exporting Data URL...', 
		                            defaultDir=os.getcwd(), defaultFile='data urls', 
		                            wildcard='.csv', 
		                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
		    if file_dlg.ShowModal() == wx.ID_OK:
			os.chdir(os.path.split(file_dlg.GetPath())[0])
			myfile = open(file_dlg.GetPath(), 'wb')
			wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
			for row in dia.listctrl.get_all_urls():
			    wr.writerow(row)
			myfile.close()	
			file_dlg.Destroy()
		
		if dia.output_options.GetSelection() == 2:
		    image_urls = []
		    for row in dia.listctrl.get_selected_urls():
			image_urls.append(row[2])
		    if os.path.isfile('C:\Program Files\ImageJ\ImageJ.exe') is False:
			#err_dlg = wx.lib.dialogs.ScrolledMessageDialog(self, str("\n".join(urls)), "ERROR!! ImageJ was not found in C\Program Files directory to show following images")
			err_dlg = wx.MessageDialog(None, 'ImageJ was not found in C\Program Files directory to show images!!', 'Error', wx.OK | wx.ICON_ERROR)
			err_dlg.ShowModal()			 
			return 			
		    else:
			#TO DO: check the image format to be shown in ImageJ    
			ImageJPath = 'C:\Program Files\ImageJ\ImageJ.exe'
			subprocess.Popen("%s %s" % (ImageJPath, ' '.join(image_urls)))		    
			
	    dia.Destroy()	
	    
      
    def ShowTooltipsInfo(self):
        info_string = ''
        for tag in self.current_node.get_tags():
            info_string += str(meta.get_attribute_dict(exp.get_tag_protocol(tag)))
        return info_string  
    
    def get_description(self, protocol):
        return '\n'.join(['%s=%s'%(k, v) for k, v in meta.get_attribute_dict(exp.get_tag_protocol(protocol))])  
    
    #----------------------------------------------------------------------
    def get_children_tags(self, node):
	"""returns the children node tags"""
	
	    
	return [exp.get_tag_stump(ctag, 2)
	        for cnodes in timeline.get_progeny(node) if cnodes
	        for ctag in cnodes.tags]	
	
    
    def get_ancestral_tags(self, node):
	#ancestral_tags = []
	#for pnode in timeline.reverse_iter_tree(node):
	    #if pnode:
		#if 'CellTransfer|Seed' in node.tags:
		    #for tag in node.tags:
			##if (tag.startswith('CellTransfer|Seed') and 
			    ##meta.get_field('CellTransfer|Seed|HarvestInstance|'+exp.get_tag_instance(tag)) is not None):
			    #h_instance = meta.get_field('CellTransfer|Seed|HarvestInstance|'+exp.get_tag_instance(tag))
			    #for tpnode in self.nodes_by_timepoint[node.get_timepoint()-1]:
				#if tpnode:
				    #for tptag in tpnode.tags:	       
					#if exp.get_tag_protocol(tptag) == 'CellTransfer|Harvest|'+h_instance:
					    #for npnode in timeline.reverse_iter_tree(tpnode):
						#if npnode:
						    #for nptag in npnode.tags:
							#ancestral_tags.append(exp.get_tag_stump(nptag, 2))
		#else:
		    #for ptag in pnode.tags:
			#ancestral_tags.append(exp.get_tag_stump(ptag, 2))
	
	#return ancestral_tags

	return [exp.get_tag_stump(ptag, 2)
	        for pnode in timeline.reverse_iter_tree(node) if pnode
	        for ptag in pnode.tags]
    
    #----------------------------------------------------------------------
    def order_nodes(self, node):
	"""Sort the node according to the Plate_Well ids"""
	x = node.get_well_ids()
	return tuple(sorted([("PTFCD".find(item[0][0]), item[0], item[1]) for item in x]))	

        
if __name__ == "__main__":
    
    N_FURCATIONS = 2
    N_TIMEPOINTS = 1
    MAX_TIMEPOINT = 100
    PLATE_TYPE = exp.P24
    
    app = wx.PySimpleApp()
    
    f = LineageFrame(None, size=(600, 300))
    f.Show()
    #f.generate_random_data()

    exp.PlateDesign.add_plate('Plate', '1', PLATE_TYPE, 'groupA')
    allwells = exp.PlateDesign.get_well_ids(exp.PlateDesign.get_plate_format('Plate1'))
    f.lineage_panel.on_timeline_updated('')
    ## GENERATE RANDOM EVENTS ON RANDOM WELLS
    #for t in [0] + list(np.random.random_integers(1, MAX_TIMEPOINT, N_TIMEPOINTS)):
        #for j in range(np.random.randint(1, N_FURCATIONS)):
            #np.random.shuffle(allwells)
            #well_ids = [('test', well) for well in allwells[:np.random.randint(0, len(allwells))]]
            ##timeline.add_event(t, 'event%d'%(t), well_ids)
            #meta.set_field('AddProcess|Stain|Wells|0|%s'%(t), well_ids)
    
    app.MainLoop()