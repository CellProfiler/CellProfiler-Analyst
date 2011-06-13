import experimentsettings as exp
import wx
import os
import numpy as np
from time import time
import icons
from wx.lib.combotreebox import ComboTreeBox
from PIL import Image

# x-spacing modes for timeline and lineage panels
SPACE_EVEN = 0
SPACE_TIME = 1
SPACE_TIME_COMPACT = 2

meta = exp.ExperimentSettings.getInstance()

class LineageFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='Experiment Lineage', **kwargs):
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
        
        tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        tb.AddControl(wx.StaticText(tb, -1, 'zoom'))
        self.zoom = tb.AddControl(wx.Slider(tb, -1, style=wx.SL_AUTOTICKS)).GetControl()
        self.zoom.SetRange(1, 30)
        self.zoom.SetValue(8)
        #x_spacing = tb.AddControl(wx.CheckBox(tb, -1, 'Time-relative branches'))
        #x_spacing.GetControl().SetValue(0)
        #generate = tb.AddControl(wx.Button(tb, -1, '+data'))        
        tb.Realize()
        
        #from f import TreeCtrlComboPopup
        #cc = wx.combo.ComboCtrl(sw)
        #self.tcp = TreeCtrlComboPopup()
        #cc.SetPopupControl(self.tcp)
        #sw.Sizer.Add(cc)
        #meta.add_subscriber(self.on_metadata_changed, '')
        
        self.Bind(wx.EVT_SLIDER, self.on_zoom, self.zoom)
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


class TimelinePanel(wx.Panel):
    '''An interactive timeline panel
    '''
    # Drawing parameters
    PAD = 0.0
    ICON_SIZE = 16.0
    MIN_X_GAP = ICON_SIZE + 2
    TIC_SIZE = 2
    FONT_SIZE = (5,10)

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
        self.Refresh()
        self.Parent.FitInside()
        
    def set_x_spacing(self, mode):
        if mode == SPACE_TIME:
            self.time_x = True
        elif mode == SPACE_EVEN:
            self.time_x = False
        self._recalculate_min_size()
        self.Refresh()
        self.Parent.FitInside()

    def on_timeline_updated(self, tag):
        timeline = meta.get_timeline()
        self.events_by_timepoint = timeline.get_events_by_timepoint()
        self.timepoints = timeline.get_unique_timepoints()
        # for time compact x-spacing
        #if len(self.timepoints) > 1:
            #self.min_time_gap = min([y-x for x,y in zip(self.timepoints[:-1], 
                                                        #self.timepoints[1:])])
        #else:
            #self.min_time_gap = 1
        self._recalculate_min_size()
        self.Refresh()
        self.Parent.FitInside()
        
    def _recalculate_min_size(self):
        if self.timepoints is not None and len(self.timepoints) > 0:
            timeline = exp.ExperimentSettings.getInstance().get_timeline()
            max_event_types_per_timepoint = \
                    max([len(set([exp.get_tag_stump(evt.get_welltag()) for evt in evts]))
                         for t, evts in self.events_by_timepoint.items()])
            min_h = (max_event_types_per_timepoint+1) * self.ICON_SIZE + self.PAD * 2 + self.FONT_SIZE[1] + self.TIC_SIZE * 2 + 1
            if self.time_x:
                self.SetMinSize((self.PAD * 2 + self.MIN_X_GAP * self.timepoints[-1],
                                 min_h))
            else:
                self.SetMinSize((len(self.timepoints) * self.MIN_X_GAP + self.PAD * 2,
                                 min_h))

    def _on_paint(self, evt=None):
        '''Handler for paint events.
        '''
        if self.timepoints is None:
            evt.Skip()
            return

        PAD = self.PAD + self.ICON_SIZE / 2.0
        ICON_SIZE = self.ICON_SIZE
        MIN_X_GAP = self.MIN_X_GAP
        TIC_SIZE = self.TIC_SIZE
        FONT_SIZE = self.FONT_SIZE
        MAX_TIMEPOINT = self.timepoints[-1]
        self.hover_timepoint = None

        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        if self.time_x:
            if MAX_TIMEPOINT == 0:
                px_per_time = 1
            else:
                px_per_time = max((w_win - PAD * 2.0) / MAX_TIMEPOINT,
                                  MIN_X_GAP)
        
        if len(self.timepoints) == 1:
            x_gap = 1
        else:
            x_gap = max(MIN_X_GAP, 
                        (w_win - PAD * 2) / (len(self.timepoints) - 1))

        # y pos of line
        y = h_win - PAD - FONT_SIZE[1] - TIC_SIZE - 1

        # draw the timeline
        if self.time_x:
            dc.DrawLine(PAD, y, 
                        px_per_time * MAX_TIMEPOINT + PAD, y)
        else:            
            dc.DrawLine(PAD, y, 
                        x_gap * (len(self.timepoints) - 1) + PAD, y)

        font = dc.Font
        font.SetPixelSize(FONT_SIZE)
        dc.SetFont(font)

        # draw event icons
        for i, timepoint in enumerate(self.timepoints):
            # x position of timepoint on the line
            if self.time_x:
                x = timepoint * px_per_time + PAD
            else:
                x = i * x_gap + PAD
                
            if (self.cursor_pos is not None and 
                x - ICON_SIZE/2 < self.cursor_pos < x + ICON_SIZE/2):
                dc.SetPen(wx.Pen(wx.BLACK, 3))
                self.hover_timepoint = timepoint
            else:
                dc.SetPen(wx.Pen(wx.BLACK, 1))
            # Draw tic marks
            dc.DrawLine(x, y - TIC_SIZE, 
                        x, y + TIC_SIZE)
            #dc.DrawRectangle(x, y, ICON_SIZE, ICON_SIZE)
            bmps = []
            process_types = set([])
            for i, ev in enumerate(self.events_by_timepoint[timepoint]):
                stump = exp.get_tag_stump(ev.get_welltag())
                if stump.startswith('CellTransfer|Seed') and stump not in process_types:
                    bmps += [icons.seed.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('CellTransfer|Harvest') and stump not in process_types:
                    bmps += [icons.harvest.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('Perturbation|Chem') and stump not in process_types:
                    bmps += [icons.treat.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('Perturbation|Bio') and stump not in process_types:
                    bmps += [icons.dna.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('Labeling|Stain') and stump not in process_types:
                    bmps += [icons.stain.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('Labeling|Antibody') and stump not in process_types:
                    bmps += [icons.antibody.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('Labeling|Primer') and stump not in process_types:
                    bmps += [icons.primer.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('AddProcess|Spin') and stump not in process_types:
                    bmps += [icons.spin.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('AddProcess|Wash') and stump not in process_types:
                    bmps += [icons.wash.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('AddProcess|Dry') and stump not in process_types:
                    bmps += [icons.keepdry.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('AddProcess|Medium') and stump not in process_types:
                    bmps += [icons.medium.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('AddProcess|Incubator') and stump not in process_types:
                    bmps += [icons.incubator.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('DataAcquis|HCS') and stump not in process_types:
                    bmps += [icons.staticimage.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('DataAcquis|FCS') and stump not in process_types:
                    bmps += [icons.fcs.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                elif stump.startswith('DataAcquis|TLM') and stump not in process_types:
                    bmps += [icons.tlm.Scale(ICON_SIZE, ICON_SIZE, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()]
                process_types.add(stump)
                
            for i, bmp in enumerate(bmps):
                dc.DrawBitmap(bmp, x - ICON_SIZE / 2.0, 
                              y - ((i+1)*ICON_SIZE) - TIC_SIZE - 1)
                
            # draw the timepoint beneath the line
            time_string = exp.format_time_string(timepoint)
            wtext = FONT_SIZE[0] * len(time_string)
            dc.DrawText(time_string, x - wtext/2.0, y + TIC_SIZE + 1)
        
        dc.EndDrawing()

    def _on_mouse_motion(self, evt):
        self.cursor_pos = evt.X
        self.Refresh()

    def _on_mouse_exit(self, evt):
        self.cursor_pos = None
        self.Refresh()
        
    def _on_click(self, evt):
        if self.hover_timepoint is not None:
            try:
                bench = wx.GetApp().get_bench()
            except: return
            bench.set_timepoint(self.hover_timepoint)
            bench.show_selected_instances(self.hover_timepoint)


class LineagePanel(wx.Panel):
    '''A Panel that displays a lineage tree.
    '''
    # Drawing parameters
    PAD = 30
    NODE_R = 8
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
        
        meta.add_subscriber(self.on_timeline_updated, 
                            exp.get_matchstring_for_subtag(2, 'Well'))

        self.Bind(wx.EVT_PAINT, self._on_paint)
        self.Bind(wx.EVT_MOTION, self._on_mouse_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_mouse_exit)
        self.Bind(wx.EVT_LEFT_UP, self._on_mouse_click)
        
    def set_x_spacing(self, mode):
        if mode == SPACE_TIME:
            self.time_x = True
        elif mode == SPACE_EVEN:
            self.time_x = False
        self._recalculate_min_size()
        self.Refresh()
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
        self.Refresh()
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
        self.Refresh()
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
        
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        #dc.SetPen(wx.Pen("BLACK",1))

        # Iterate from leaf nodes up to the root, and draw R->L, Top->Bottom
        for i, t in enumerate(timepoints):
            if t == -1:
                X = PAD
            elif self.time_x:
                X = PAD + FLASK_GAP + t * px_per_time
                x_gap = PAD + FLASK_GAP + timepoints[i-1] * px_per_time - X
            else:
                X = PAD + FLASK_GAP + (len(timepoints) - i - 2) * x_gap
            
            if len(nodes_by_tp) == 1:
                X = w_win / 2
                Y = h_win / 2
                if (self.cursor_pos is not None and 
                    X-NODE_R < self.cursor_pos[0] < X + NODE_R and
                    Y-NODE_R < self.cursor_pos[1] < Y + NODE_R):
                    dc.SetBrush(wx.Brush('#FFFFAA'))
                    dc.SetPen(wx.Pen(wx.RED, 3))
                    self.current_node = nodes_by_tp.values()[t][0]
                else:
                    dc.SetBrush(wx.Brush('#FAF9F7'))
                    #dc.SetPen(wx.Pen(wx.BLACK, 1))
                    self.current_node = None
                    
                dc.DrawRectangle(X-NODE_R, Y-NODE_R, NODE_R*2, NODE_R*2)
                #dc.DrawText(str(nodes_by_tp[t][0].get_timepoint()), X, Y+NODE_R)
            elif i == 0:
                # Leaf nodes
                for node in nodes_by_tp[t]:
                    if (self.cursor_pos is not None and 
                        X-NODE_R < self.cursor_pos[0] < X + NODE_R and
                        Y-NODE_R < self.cursor_pos[1] < Y + NODE_R):
                        dc.SetBrush(wx.Brush('#FFFFAA'))
                        dc.SetPen(wx.Pen('#000000', 3))
                        self.current_node = node
                    else:
                        if len(node.get_tags()) > 0:
                            # If an event occurred
                            dc.SetBrush(wx.Brush('#333333'))
                        else:
                            # no event
                            dc.SetBrush(wx.Brush('#FAF9F7'))
                        dc.SetPen(wx.Pen('#000000', 1))
                    
                    dc.DrawCircle(X, Y, NODE_R)
                    #dc.DrawText(str(node.get_timepoint()), X, Y+NODE_R)
                    nodeY[node.id] = Y
                    Y += y_gap
            else:
                # Internal nodes
                for node in nodes_by_tp[t]:
                    ys = []
                    for child in node.get_children():
                        ys.append(nodeY[child.id])
                    Y = (min(ys) + max(ys)) / 2

                    if (self.cursor_pos is not None and 
                        X-NODE_R < self.cursor_pos[0] < X + NODE_R and
                        Y-NODE_R < self.cursor_pos[1] < Y + NODE_R):
                        dc.SetBrush(wx.Brush('#FFFFAA'))
                        self.current_node = node
                    else:
                        if len(node.get_tags()) > 0:
                            # If an event occurred
                            dc.SetBrush(wx.Brush('#333333'))
                        else:
                            # no event
                            dc.SetBrush(wx.Brush('#FFFFFF'))
                        dc.SetPen(wx.Pen(wx.BLACK, 1))
                    
                    if t == -1:
                        dc.DrawRectangle(X-NODE_R, Y-NODE_R, NODE_R*2, NODE_R*2)
                    else:
                        dc.DrawCircle(X, Y, NODE_R)
                    #dc.DrawText(str(node.get_timepoint()), X, Y+NODE_R)
                        
                    dc.SetBrush(wx.Brush('#FAF9F7'))
                    dc.SetPen(wx.Pen(wx.BLACK, 1))

                    for child in node.get_children():
                        if t == -1:
                            if self.time_x:
                                dc.DrawLine(X + NODE_R, Y, 
                                            X + FLASK_GAP + px_per_time * timepoints[i-1] - NODE_R ,nodeY[child.id])
                            else:
                                dc.DrawLine(X + NODE_R, Y, 
                                            X + FLASK_GAP - NODE_R ,nodeY[child.id])
                        else:
                            dc.DrawLine(X + NODE_R, Y, 
                                        X + x_gap - NODE_R ,nodeY[child.id])
                    nodeY[node.id] = Y
        dc.EndDrawing()
        #print 'rendered lineage in %.2f seconds'%(time() - t0)
        
    def _on_mouse_motion(self, evt):
        self.cursor_pos = (evt.X, evt.Y)
        self.Refresh()

    def _on_mouse_exit(self, evt):
        self.cursor_pos = None
        self.Refresh()

    def _on_mouse_click(self, evt):
        if self.current_node is None:
            return
        for tag in self.current_node.get_tags():
            if (tag.startswith('DataAcquis|TLM') or 
                tag.startswith('DataAcquis|HCS')):
                for well in self.current_node.get_well_ids():
                    image_tag = '%s|Images|%s|%s|%s'%(exp.get_tag_stump(tag, 2),
                                                      exp.get_tag_instance(tag),
                                                      exp.get_tag_timepoint(tag),
                                                      well)
                    urls = meta.get_field(image_tag, [])
                    for url in urls:
                        im = Image.open(url)
                        im.show()
            elif tag.startswith('DataAcquis|FCS'):
                for well in self.current_node.get_well_ids():
                    image_tag = '%s|Images|%s|%s|%s'%(exp.get_tag_stump(tag, 2),
                                                  exp.get_tag_instance(tag),
                                                  exp.get_tag_timepoint(tag),
                                                  well)
                    urls = meta.get_field(image_tag, [])
                    for url in urls:
                        os.startfile(url)
        
        message = ''
        for well in sorted(self.current_node.get_well_ids()):
            message += ', '.join(well)
            message += '\n'
        msg = wx.MessageDialog(self, message, caption='Info', style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP, pos=(200,200))
        msg.ShowModal()
        msg.Destroy()


        #print self.current_node.get_tags()                                     


        
if __name__ == "__main__":
    
    N_FURCATIONS = 2
    N_TIMEPOINTS = 1
    MAX_TIMEPOINT = 100
    PLATE_TYPE = exp.P24
    
    app = wx.PySimpleApp()
    
    f = LineageFrame(None, size=(600, 300))
    f.Show()
    #f.generate_random_data()

    exp.PlateDesign.add_plate('test', PLATE_TYPE)
    allwells = exp.PlateDesign.get_well_ids(exp.PlateDesign.get_plate_format('test'))
    f.lineage_panel.on_timeline_updated('')
    ## GENERATE RANDOM EVENTS ON RANDOM WELLS
    #for t in [0] + list(np.random.random_integers(1, MAX_TIMEPOINT, N_TIMEPOINTS)):
        #for j in range(np.random.randint(1, N_FURCATIONS)):
            #np.random.shuffle(allwells)
            #well_ids = [('test', well) for well in allwells[:np.random.randint(0, len(allwells))]]
            ##timeline.add_event(t, 'event%d'%(t), well_ids)
            #meta.set_field('AddProcess|Stain|Wells|0|%s'%(t), well_ids)
    
    app.MainLoop()