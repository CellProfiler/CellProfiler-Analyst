import wx
import os
import numpy as np
import guiutils
import icons
import metadatainput as assay
import re
from experimentsettings import *
from vesselpanel import VesselPanel, VesselScroller, VesselSelectionPopup
from lineagepanel import TimelinePanel
from temporaltaglist import TemporalTagListCtrl
from notepad import NotePad
from wx.lib.embeddedimage import PyEmbeddedImage
from wx.lib.masked import TimeCtrl

meta = ExperimentSettings.getInstance()

class Bench(wx.Frame):
    def __init__(self, protocol_navigator, id=-1, title='Bench', **kwargs):
        wx.Frame.__init__(self, None, id, title=title, **kwargs)
        self.protocol_navigator = protocol_navigator

        # --- FRAME IS SPLIT INTO 2 PARTS (top, bottom) ---
        
        self.splitter = wx.SplitterWindow(self, style=wx.NO_BORDER|wx.SP_3DSASH)
        self.top_panel = wx.Panel(self.splitter)
        self.bot_panel = wx.Panel(self.splitter)
        self.splitter.SplitHorizontally(self.top_panel, self.bot_panel)
        
        # --- CREATE WIDGETS ---
        # TOP
        self.tlabel1 = wx.StaticText(self.top_panel, -1, "Time:")
        self.time_text_box = wx.TextCtrl(self.top_panel, -1, '0:00', size=(50, -1))
        self.time_spin = wx.SpinButton(self.top_panel, -1, style=wx.SP_VERTICAL)
        self.time_spin.Max = 1000000
        self.time_slider = wx.Slider(self.top_panel, -1)        
        self.time_slider.SetRange(0, 1440)
        self.add24_button = wx.Button(self.top_panel, -1, "Add 24h")
        self.taglistctrl = TemporalTagListCtrl(self.top_panel)
        # BOTTOM
	undo_bmp = icons.undo.Scale(24.0, 24.0, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap() 
        self.del_evt_button = wx.BitmapButton(self.bot_panel, -1, undo_bmp, style=0)
	note_bmp = icons.note.Scale(24.0, 24.0, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap() 
	self.add_note_button = wx.BitmapButton(self.bot_panel, -1, note_bmp, style=0)
        self.group_checklist = VesselGroupSelector(self.bot_panel)
        self.group_checklist.update_choices(self.bot_panel)
        self.vesselscroller = VesselScroller(self.bot_panel)
        self.vesselscroller.SetBackgroundColour('WHITE')
        
        # --- BIND CONTROL EVENTS ---
        
        self.time_slider.Bind(wx.EVT_SLIDER, self.on_adjust_timepoint)
        self.time_spin.Bind(wx.EVT_SPIN_UP, self.on_increment_time)
        self.time_spin.Bind(wx.EVT_SPIN_DOWN, self.on_decrement_time)
        self.time_text_box.Bind(wx.EVT_TEXT, self.on_edit_time_text_box)
        self.add24_button.Bind(wx.EVT_BUTTON, lambda(evt):self.set_time_interval(0, self.time_slider.GetMax()+1440))
        self.taglistctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_instance_selected)
        self.taglistctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_instance_selected)
        self.del_evt_button.Bind(wx.EVT_BUTTON, self.on_del_event)
	self.del_evt_button.Disable()
	self.add_note_button.Bind(wx.EVT_BUTTON, self.on_add_note)
        self.group_checklist.GetCheckList().Bind(wx.EVT_CHECKLISTBOX, self.update_plate_groups)

        # --- LAY OUT THE FRAME ---
                
        time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        time_sizer.Add(self.tlabel1,0, wx.EXPAND|wx.ALL, 5)
        time_sizer.Add(self.time_slider, 1, wx.EXPAND|wx.ALL, 5)
        time_sizer.Add(self.time_text_box, 0, wx.ALL, 5)
        time_sizer.Add(self.time_spin, 0, wx.ALL, 5)
        time_sizer.Add(self.add24_button, 0, wx.ALL, 5)
	
	#menu_sizer = wx.BoxSizer(wx.HORIZONTAL)
	edit_staticbox = wx.StaticBox(self.bot_panel, -1, "Edit")
	edit_flex = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
	edit_flex.Add(wx.StaticText(self.bot_panel, -1, 'Undo Event'), 0, wx.CENTER)
	edit_flex.Add(self.del_evt_button, 0)
	edit_flex.Add(wx.StaticText(self.bot_panel, -1, 'Add Note'), 0, wx.CENTER)
	edit_flex.Add(self.add_note_button, 0)
	
	editSizer = wx.StaticBoxSizer(edit_staticbox, wx.VERTICAL)
	editSizer.Add(edit_flex,  1, wx.EXPAND|wx.ALL, 2)

        stack_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stack_sizer.Add(wx.StaticText(self.bot_panel, -1, 'Select Vessel Stack(s)'), 0, wx.LEFT|wx.CENTER, 3)
        stack_sizer.Add(self.group_checklist, 1, wx.LEFT|wx.CENTER, 5)
	stack_sizer.AddSpacer((10,-1))
	stack_sizer.Add(editSizer, 0, wx.RIGHT|wx.CENTER)
                
        self.top_panel.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_panel.Sizer.Add(time_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        self.top_panel.Sizer.Add(self.taglistctrl, 1, wx.EXPAND)
        
        self.bot_panel.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.bot_panel.Sizer.Add(stack_sizer, 0, wx.EXPAND|wx.ALL, 10)
        self.bot_panel.Sizer.Add(self.vesselscroller, 1, wx.EXPAND)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.splitter, 1, wx.EXPAND)
            
    def on_instance_selected(self, event):
        '''when a protocol is selected from the taglistctrl
        '''
        for plate in self.vesselscroller.get_vessels():
            plate.enable_selection(self.taglistctrl.get_selected_protocols() != [])
        self.update_well_selections()
            
    def update_plate_groups(self, event=None):
        '''called when a vessel group is selected.
        '''
        meta = ExperimentSettings.getInstance()

        selected_groups = self.group_checklist.GetCheckedStrings()        
        self.vesselscroller.clear()

        group_tags = meta.get_matching_tags('ExptVessel|*|StackName|*')
        for tag in sorted(group_tags, key=meta.stringSplitByNumbers):
            if meta.get_field(tag) in selected_groups:
                stack_name = meta.get_field(tag)
                prefix = get_tag_stump(tag, 2)
                vessel_type = tag.split('|')[1]
                inst = get_tag_instance(tag)
                plate_id = PlateDesign.get_plate_id(vessel_type, inst)
                plate_shape = PlateDesign.get_plate_format(plate_id)
                well_ids = PlateDesign.get_well_ids(plate_shape)
                plate = VesselPanel(self.vesselscroller, plate_id)
                self.vesselscroller.add_vessel_panel(plate, plate_id)
                plate.add_well_selection_handler(self.on_update_well)
                
        self.update_well_selections()
        self.vesselscroller.FitInside()
        
    def on_adjust_timepoint(self, evt):
        self.set_timepoint(self.time_slider.Value)

    def get_selected_timepoint(self):
        return self.time_slider.GetValue()
    
    def set_time_interval(self, tmin, tmax):
        '''Sets the time slider interval.
        tmin, tmax -- min and max timepoint values
        '''
        self.time_slider.SetRange(tmin, tmax)
    
    def set_timepoint(self, timepoint):
        '''Sets the slider timepoint and updates the plate display.
        If a timepoint is set that is greater than time_slider's max, then the
        time_slider interval is increased to include the timepoint.
        '''
        if timepoint > self.time_slider.Max:
            self.time_slider.SetRange(0, timepoint)
        self.time_slider.Value = timepoint
        self.time_text_box.Value = format_time_string(timepoint)
        self.protocol_navigator.get_lineage().set_hover_timepoint(timepoint)
        self.update_well_selections()
	self.update_well_state_status()

    def on_increment_time(self, evt):
        self.set_timepoint(self.time_slider.Value + 1)
        
    def on_decrement_time(self, evt):
        self.set_timepoint(self.time_slider.Value - 1)

    def on_edit_time_text_box(self, evt):
        time_string = self.time_text_box.GetValue()
        if not re.match('^\d*:\d\d$', time_string):
            self.time_text_box.SetForegroundColour(wx.RED)
            return
        try:
            hours, mins = map(int, time_string.split(':'))
            minutes = hours * 60 + mins
            self.set_timepoint(minutes)
            self.time_text_box.SetForegroundColour(wx.BLACK)
        except:
            self.time_text_box.SetForegroundColour(wx.RED)
    
    def on_add_note(self, evt):
	# check whether any event occured at this timepoint
	timeline = meta.get_timeline()
	self.events_by_timepoint = timeline.get_events_by_timepoint()	
	prefixes = set([get_tag_stump(ev.get_welltag(), 2) for ev in self.events_by_timepoint[self.get_selected_timepoint()]])	    
		
	if not prefixes:
	    dial = wx.MessageDialog(None, 'Notes need to be associated with events!!', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()              
	    return
	
	try:
	    lineage_panel = wx.GetApp().get_lineage()
	except: 
	    return	
		
	self.page_counter = meta.get_new_protocol_id('Notes')	
	if int(self.page_counter) > 1:
	    lineage_panel.timeline_panel.on_note_icon_add()

	note_dia = NotePad(self, None, None, None) # timepoint and instance number as none because users might click Cancel
	if note_dia.ShowModal() == wx.ID_OK:
	    # Notes|<type>|<timepoint>|<instance> = value
	    meta.set_field('Notes|%s|%s|%s' %(note_dia.noteType, str(self.get_selected_timepoint()), str(self.page_counter)), note_dia.noteDescrip.GetValue())   	    
	    lineage_panel.timeline_panel.on_note_icon_add()

    
    def on_del_event(self, evt):
        protocols = self.taglistctrl.get_selected_protocols()
        if protocols == []:
	    dial = wx.MessageDialog(None, 'No event was found for deletion\nor\nCan not undo cell transfer event', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal()              
            return
        
        protocol = protocols[0]
        prefix, instance = protocol.rsplit('|',1)   
	
        wells_tag = '%s|Wells|%s|%s'%(prefix, instance, self.get_selected_timepoint())
        meta.remove_field(wells_tag)
        self.update_well_selections()
	self.del_evt_button.Disable()
        

    def update_well_selections(self):
        '''Updates the selected vessels based on the currently selected 
        timepoint and protocols in the Bench.
        Disables vessel selection if no protocol is selected.
        '''
        protocols = self.taglistctrl.get_selected_protocols()
        if protocols == []:
            for plate in self.vesselscroller.get_vessels():
                plate.disable_selection()
                plate.set_selected_well_ids([])
            return

        for protocol in protocols:
            prefix, instance = protocol.rsplit('|', 1)
            wells_tag = '%s|Wells|%s|%s'%(prefix, instance, self.get_selected_timepoint())
            selected_ids = meta.get_field(wells_tag, [])
                            
            for plate in self.vesselscroller.get_vessels():
                plate.enable_selection()
                selected_well_ids = [pw_id for pw_id in selected_ids if pw_id[0]==plate.get_plate_id()]
                plate.set_selected_well_ids(selected_well_ids)
    
    def update_well_state_status(self):
	timeline = meta.get_timeline()	
	selected_ids = [timeline.get_well_ids(utp) for utp in timeline.get_unique_timepoints() if utp <= self.get_selected_timepoint()]

	for plate in self.vesselscroller.get_vessels():
	    plate.enable_selection()
	    selected_well_ids = [pw_id for pw_ids in selected_ids for pw_id in pw_ids if pw_id[0]==plate.get_plate_id()]
	    plate.set_well_ids_state(selected_well_ids)

    def on_update_well(self, platewell_id, selected):
        '''Called when a well is clicked.
        Populate all action tags with the set of wells that were effected.
        eg: AddProcess|Spin|Wells|<instance>|<timepoint> = ['A01',...]
        '''
        protocols = self.taglistctrl.get_selected_protocols()
        if protocols == []:
            return
        
        protocol = protocols[0]
        prefix, instance = protocol.rsplit('|',1)
        
        wells_tag = '%s|Wells|%s|%s'%(prefix, instance, self.get_selected_timepoint())
        #platewell_ids = set(meta.get_field(wells_tag, [])) 
        
        
        # SPECIAL CASE: For harvesting, we prompt the user to specify the 
        # destination well(s) for each harvested well.
        if prefix == 'CellTransfer|Harvest':
            if selected:
                #
                # TODO:
                #
##                dlg = TimepointSelectionPopup(self)
##                if dlg.ShowModal() != wx.ID_OK:
##                    self.vesselscroller.get_vessel(platewell_id[0]).deselect_well_id(platewell_id)
##                    return
##                new_timepoint = dlg.get_timepoint()
                dlg = VesselSelectionPopup(self)
                if dlg.ShowModal() == wx.ID_OK:
                    destination_wells = dlg.get_selected_platewell_ids()
                    assert destination_wells
                    new_id = meta.get_new_protocol_id('CellTransfer|Seed')
                    meta.set_field('CellTransfer|Seed|Wells|%s|%s'%
                                   (new_id, self.get_selected_timepoint() + 1), # For now all reseeding instances are set 1 minute after harvesting
                                   destination_wells)
                    meta.set_field('CellTransfer|Seed|HarvestInstance|%s'%(new_id), instance)
                    h_density = meta.get_field('CellTransfer|Harvest|HarvestingDensity|%s'%instance, [])
                    s_density = [0,'']
                    if len(h_density) > 0:
                        s_density[0]= h_density[0]
                    if len(h_density) > 1:
                        s_density[1]= h_density[1]
                    meta.set_field('CellTransfer|Seed|SeedingDensity|%s'%(new_id), s_density)
                    if meta.get_field('CellTransfer|Harvest|MediumAddatives|%s'%instance) is not None:
                        meta.set_field('CellTransfer|Seed|MediumAddatives|%s'%(new_id), meta.get_field('CellTransfer|Harvest|MediumAddatives|%s'%instance))  
                    
                    
                else:
                    self.vesselscroller.get_vessel(platewell_id[0]).deselect_well_id(platewell_id)
                    return
                    
            else:
                # Harvesting event removed.
                # Remove all Seeding events that were linked to it.
                seed_harvest_tags = meta.get_field_tags('CellTransfer|Seed|HarvestInstance')
                for t in seed_harvest_tags:
                    if meta.get_field(t) == instance:
                        # if this seed harvest instance is the same as the 
                        # harvest instance that is being removed, then remove 
                        # all seed tags of this instance
                        seed_tags = meta.get_field_tags('CellTransfer|Seed', get_tag_instance(t))
                        for seed_tag in seed_tags:
                            meta.remove_field(seed_tag)
                
        
        # GENERIC CASE: Associate or dissociate event with selected wells
        wells_tag = '%s|Wells|%s|%s'%(prefix, instance, self.get_selected_timepoint())
        platewell_ids = set(meta.get_field(wells_tag, []))
        
        if selected:
            platewell_ids.update(platewell_id)
            meta.set_field(wells_tag, list(platewell_ids))
        #else:
            #platewell_ids.discard(platewell_id)  
            #if len(platewell_ids) > 0:
                #meta.set_field(wells_tag, list(platewell_ids))
            #else:
                #meta.remove_field(wells_tag)

        # Update the Images tags
        if selected and prefix.startswith('DataAcquis'):
            
            images_tag = '%s|Images|%s|%s|%s'%(prefix, instance, self.get_selected_timepoint(), repr(platewell_id))
            
            if prefix == 'DataAcquis|HCS':
                dlg = wx.FileDialog(self,message='Select the images files',
                                    defaultDir=os.getcwd(), defaultFile='', style=wx.OPEN|wx.MULTIPLE)
            elif prefix == 'DataAcquis|FCS':
                #dlg = wx.FileDialog(self,message='Select the FCS files for flask %s'%(platewell_id[0].strip('[]')),
                dlg = wx.FileDialog(self,message='Select the FCS (pdf) files for flask',
                                    defaultDir=os.getcwd(), defaultFile='', wildcard = "Adobe PDF files (*.pdf)|*.pdf|", style=wx.OPEN|wx.MULTIPLE)
            elif prefix == 'DataAcquis|TLM':
                dlg = wx.FileDialog(self,message='Select the images files',
                                    defaultDir=os.getcwd(), defaultFile='', style=wx.OPEN|wx.MULTIPLE)
            else:
                raise Exception('unrecognized tag prefix')
            
            if dlg.ShowModal() == wx.ID_OK:
                meta.set_field(images_tag, dlg.GetPaths())
                os.chdir(os.path.split(dlg.GetPath())[0])
                dlg.Destroy()
            else:
                dlg.Destroy()
                meta.remove_field(wells_tag)
                vessel = self.vesselscroller.get_vessel(platewell_id[0])
                if vessel:
                    vessel.deselect_well_at_pos(
                        PlateDesign.get_pos_for_wellid(
                            PlateDesign.get_plate_format(platewell_id[0]), 
                            platewell_id[1]))
                else:
                    raise Exception('Could not find vessel: %s'%(platewell_id[0]))
                
                
        # NOTE: None of the code needs to use the EventTimepoint tag,
        #       it's redundant with the timepoints encoded in the tags
        #       so we don't set it anymore.

        
class VesselGroupSelector(guiutils.CheckListComboBox):
    '''A ComboBox-style control that presents a checklist of plate groups for
    selection. This class automatically updates itself as vessels are added and
    removed.
    '''
    def __init__(self, parent):
        guiutils.CheckListComboBox.__init__(self, parent)
        meta.add_subscriber(self.update_choices, 'ExptVessel.*')
        
    def update_choices(self, tag):
        group_tags = meta.get_matching_tags('ExptVessel|*|StackName|*')
        stack_names = sorted(set([meta.get_field(tag) for tag in group_tags]))
        selected_strings = self.GetCheckedStrings()
        self.SetItems(stack_names)
        selected_strings = [g for g in selected_strings if g in self.GetItems()] 
        self.SetCheckedStrings(selected_strings)
        self.SetValue(self.popup.GetStringValue())
        
        
if __name__ == "__main__":
    app = wx.PySimpleApp()

    f = Bench(None, size=(800,500))
    f.Show()

    app.MainLoop()
