import wx
import os
import numpy as np
import icons
import wx.lib.scrolledpanel as scrolled
import wx.lib.platebtn as platebtn
from experimentsettings import *
from vesselpanel import VesselPanel, VesselScroller
from instancelist import *
from seedparaminput import *
from harvestparaminput import *
from temporaltaglist import *
from harvestedwelllist import *
from utils import *
from wx.lib.embeddedimage import PyEmbeddedImage
from groupselection import *
from wx.lib.masked import TimeCtrl

ID_SEED = 111
ID_HARVEST = 112
ID_CHEM = 121
ID_BIO = 122
ID_STAIN = 131
ID_ANTIBODY = 132
ID_PRIMER = 133
ID_SPIN = 141
ID_WASH = 142
ID_DRY = 143
ID_INCUBATE = 144
ID_TIMELAPSE = 153
ID_IMAGE = 156
ID_FLOW = 159

meta = ExperimentSettings.getInstance()


class Bench(wx.Frame):
    def __init__(self, parent, id=-1, title='Bench', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        
        # some variables settings
        self.is_selected = False
        self.selected_tag_prefix = None        
        self.selected_tag_instance = None
        self.selections = []  
        
         ## --- Timer Panel--- #
        self.tp = wx.Panel(self)
        time_sizer = self.tp.Sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.time_slider = wx.Slider(self.tp, -1)
        self.time_slider.Bind(wx.EVT_SLIDER, self.on_adjust_timepoint)
        self.time_slider.SetRange(0, 1440)
        self.tlabel1 = wx.StaticText(self.tp, -1, "Time:")
        self.time_text_box = wx.TextCtrl(self.tp, -1, '0:00', size=(50, -1))
        self.time_spin = wx.SpinButton(self.tp, -1, style=wx.SP_VERTICAL)
        self.time_spin.Max = 1000000

        self.add24_button = wx.Button(self.tp, -1, "Add 24h")
        self.add24_button.Bind(wx.EVT_BUTTON, lambda(evt):self.set_time_interval(0, self.time_slider.GetMax()+1440))

        time_sizer.AddSpacer((10,-1))
        time_sizer.Add(self.tlabel1,0, wx.EXPAND|wx.ALL, 5)
        time_sizer.AddSpacer((2,-1))
        time_sizer.Add(self.time_slider, 1, wx.EXPAND|wx.ALL, 5)
        time_sizer.AddSpacer((5,-1))
        time_sizer.Add(self.time_text_box, 0, wx.ALL, 5)
        time_sizer.AddSpacer((2,-1))
        time_sizer.Add(self.time_spin, 0, wx.ALL, 5)
        time_sizer.AddSpacer((5,-1))
        time_sizer.Add(self.add24_button, 0, wx.ALL, 5)
        time_sizer.AddSpacer((10,-1))
        
        self.time_spin.Bind(wx.EVT_SPIN_UP, self.on_increment_time)
        self.time_spin.Bind(wx.EVT_SPIN_DOWN, self.on_decrement_time)
        self.time_text_box.Bind(wx.EVT_TEXT, self.on_edit_time_text_box)
                
        ## -- Tag List Panel -- ##
        self.tagpanel = wx.Panel(self)
        tagpanel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.taglistctrl = TemporalTagListCtrl(self.tagpanel)
        ## TO DO: Add search capability
        #self.tagpanel.search_button.Disable()
        
        self.taglistctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onInstanceSelectiton)
        
        meta.add_subscriber(self.checkUpdate, 'CellTransfer.*')
        meta.add_subscriber(self.checkUpdate, 'Perturbation.*')
        meta.add_subscriber(self.checkUpdate, 'Labeling.*')
        meta.add_subscriber(self.checkUpdate, 'AddProcess.*')
        meta.add_subscriber(self.checkUpdate, 'DataAcquis.*')
 
        tagpanel_sizer.AddSpacer((10,-1))
        tagpanel_sizer.Add(self.taglistctrl, 1, wx.EXPAND)
        tagpanel_sizer.AddSpacer((10, -1))
        
        self.tagpanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.tagpanel.Sizer.Add(tagpanel_sizer,1,wx.EXPAND)
        
        ## --- Vessel Panel ---#
        self.vp = wx.Panel(self)
        self.vpg = wx.Panel(self.vp)
        
        fgs = wx.FlexGridSizer(cols=6, hgap=5, vgap=5)
        fgs.Add(wx.StaticText(self.vpg, -1, 'Select Stack'), 0)
        grpslct = GroupSelection(self.vpg)
        grpslct.update_choices(self.vpg)
        grpslct.Bind(wx.EVT_CHOICE, self.on_group_selection)
        fgs.Add(grpslct, 0, wx.EXPAND)
        
        self.seedstockBut = wx.Button(self.vpg, -1, 'Seed from Stock Culture')
        self.seedstockBut.Bind (wx.EVT_BUTTON, self.onShowStockInstance) 
        
        self.seedharvestBut = wx.Button(self.vpg, -1, 'Seed from Harvested Cells')
        #seedharvestBut.Bind (wx.EVT_BUTTON, self.OnShowDialog) 

        self.harvestBut = wx.ToggleButton(self.vpg)
        self.harvestBut.Bind (wx.EVT_TOGGLEBUTTON, self.onShowHarvestDialog)
        self.harvestBut.SetLabel('Harvest')
        
        fgs.Add(self.seedstockBut, 0, wx.EXPAND)
        fgs.Add(self.seedharvestBut, 0, wx.EXPAND)
        fgs.Add(self.harvestBut, 0, wx.EXPAND)
        
        self.vpg.SetSizer(fgs)

        self.vesselscroller = VesselScroller(self.vp)
        self.vesselscroller.SetBackgroundColour('#FFFFFF')
        
        self.vp.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.vp.Sizer.Add(self.vpg, 1,wx.EXPAND|wx.ALL, 5)
        self.vp.Sizer.Add(self.vesselscroller, 6, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.Sizer.Add(self.tp, 0, wx.EXPAND)
        self.Sizer.Add(self.tagpanel, 2, wx.EXPAND)
        self.Sizer.Add(self.vp, 5, wx.EXPAND)
        
        
    
    def onShowStockInstance(self, event):
        self.settings_controls = {}
        # link with the dynamic experiment settings
        meta = ExperimentSettings.getInstance()
        attributes = meta.get_attribute_list('StockCulture|Sample') 
          
        #check whether there is at least one attributes
        if not attributes:
            dial = wx.MessageDialog(None, 'No Instances exists!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        #show the popup table
        stock_dialog = InstanceListDialog(self, 'StockCulture|Sample', selection_mode = False)
        if stock_dialog.ShowModal() == wx.ID_OK:
            if stock_dialog.listctrl.get_selected_instances() != []:
                instance = stock_dialog.listctrl.get_selected_instances()[0]
                stock_dialog.Destroy()
                # create another pop up for this stock culture instance to define the seeding instance
                seed_dialog = SeedDialog(self, instance)
                
                if seed_dialog.ShowModal() == wx.ID_OK:
                    del self.selections[:]
 
                    selected_tag = 'CellTransfer|Seed|'+str(seed_dialog.page_counter)
                    self.selections += [selected_tag]
        
                    for plate in self.vesselscroller.get_vessels():
                            plate.enable_selection()
                    self.is_selected = True
               
                    self.update_well_selections()
                    
    def onShowHarvestDialog(self, event):
        '''This dialog pops up when users select to do Harvest event
        Once 'Harvest' button is clicked in the Bench panel, users must select
        Wells they are Harvesting from.  For now all selected Wells MUST HAVE SAME CELL LINE
        users will be given the choice to change density, medium used etc parameters. 
        '''
        # according to the state of the harvest change the selection mode
        if self.harvestBut.GetValue() == True:
            #disable Selection list and all other buttons in Bench except the Wells
            self.taglistctrl.Disable()
            self.seedstockBut.Disable()
            self.seedharvestBut.Disable()
            
            self.harvested_pw_ids = []
            for plate in self.vesselscroller.get_vessels():
                plate.enable_selection()  
                plate.add_well_selection_handler(self.on_well_selected)
            self.harvestBut.SetLabel('Modify Cell Density')
            
        if self.harvestBut.GetValue() == False:
            #check whether the harvested Wells being Seeded at the first place
            self.taglistctrl.Enable()
            self.seedstockBut.Enable()
            self.seedharvestBut.Enable()
            #change the state of the harvest button
            self.harvestBut.SetLabel('Harvest')
            #get the selected wells and their associated seeding instances
            harvest_dialog = HarvestDialog(self, self.harvested_pw_ids, self.get_selected_timepoint())

            if  harvest_dialog.ShowModal() == wx.ID_OK:
                
                del self.selections[:]
                selected_tag = 'CellTransfer|Harvest|'+str(harvest_dialog.harvest_instance)
                self.selections += [selected_tag]
                
                for plate in self.vesselscroller.get_vessels():
                    plate.enable_selection()
                self.is_selected = True
        
                self.set_timepoint(self.get_selected_timepoint()+5)
                self.taglistctrl.Enable()
                self.update_well_selections()
                for plate in self.vesselscroller.get_vessels():
                    plate.disable_selection()
                

    def onShowHarvestedList(self, event):
        # according to the state of the harvest change the selection mode
        if self.harvestBut.GetValue() == True:
            #clear the previous selections
            del self.selections[:]
            #disable Selection list and all other buttons in Bench except the Wells
            self.taglistctrl.Disable()
            self.seedstockBut.Disable()
            self.seedharvestBut.Disable()
            
            for plate in self.vesselscroller.get_vessels():
                plate.enable_selection()  
                plate.add_well_selection_handler(self.on_well_selected)
            self.harvestBut.SetLabel('Change Cell Density')
            
        if self.harvestBut.GetValue() == False:
            #check whether the harvested Wells being Seeded at the first place
            self.taglistctrl.Enable()
            self.seedstockBut.Enable()
            self.seedharvestBut.Enable()
            #change the state of the harvest button
            self.harvestBut.SetLabel('Harvest')
            #get the selected wells and their associated seeding instances
            harvested_pws_info = self.check_seeding(self.harvested_pw_ids)
            harvest_dialog = HarvestListDialog(self, harvested_pws_info)
            harvest_dialog.ShowModal()
      
        
    def on_well_selected(self, platewell_id, selected):
        if selected == True:
            self.harvested_pw_ids.append(platewell_id)
        if selected == False:
            self.harvested_pw_ids.remove(platewell_id)


    def checkUpdate(self, tag):
        '''Checks for update in Catalogue panel, however if there are updates on
           Wells by selecting Wells by clicking then it will not affect the state of listcrtl'''
        attribute = tag.split('|')[2]
        if attribute == 'Wells' or attribute == 'Images' or attribute == 'EventTimepoint':
            return
        else:
            self.taglistctrl.Disable()
      
    def onPopulateTaglist(self):
        self.taglistctrl.Enable()
        self.taglistctrl.DeleteAllItems()
        tags =  meta.get_temporal_tag_list()
        
        instance_information = self.build_taglist_information(tags)
      
        for key, tag in enumerate(instance_information):
            descriptions = str(instance_information[tag])
            index = self.taglistctrl.InsertStringItem(sys.maxint, tag.split('|')[0])
            self.taglistctrl.SetStringItem(index, 1, tag.split('|')[1])
            self.taglistctrl.SetStringItem(index, 2, tag.split('|')[2])
            self.taglistctrl.SetStringItem(index, 3, descriptions) 
        
    def build_taglist_information(self, tags):
        instance_information = {}
        category_list =[]
        type_list = []
        instance_list = []
        
        for tag in tags:
            category_list += meta.get_eventclass_list(tag)
            type_list += meta.get_eventtype_list(tag)
            instance_list += meta.get_field_instances(tag)
    
        for cat_name in sorted(set(category_list)):
            for type_name in set(type_list):             
                temp_tag_prefix = cat_name+'|'+type_name
                instances = meta.get_field_instances(temp_tag_prefix)
                
                for instance in set(instance_list):
                    isTrue = str(instance) in instances
                    if isTrue is True:
                        instance_information[temp_tag_prefix+'|'+instance] = self.taglistctrl.get_descriptions(temp_tag_prefix, instance)
        
        return instance_information
    
    def show_selected_instances(self, selected_timepoint):
        prev_selected_tags = [] 
        instance_information = {}
        
        for tag in meta.get_temporal_tag_list():
            if tag.split('|')[2] == 'Wells' and int(tag.split('|')[4]) == self.get_selected_timepoint():
                    prev_selected_tags += [tag]
        if prev_selected_tags:
            self.taglistctrl.DeleteAllItems()
            
            for tag in prev_selected_tags:
                temp_tag_prefix = tag.split('|')[0]+'|'+tag.split('|')[1]
                instance = tag.split('|')[3]
                self.selections += [temp_tag_prefix+'|'+instance]
                instance_information[temp_tag_prefix+'|'+instance] = self.taglistctrl.get_descriptions(temp_tag_prefix, instance)
          
            for key, tag in enumerate(instance_information):
                descriptions = str(instance_information[tag])
                index = self.taglistctrl.InsertStringItem(sys.maxint, tag.split('|')[0])
                self.taglistctrl.SetStringItem(index, 1, tag.split('|')[1])
                self.taglistctrl.SetStringItem(index, 2, tag.split('|')[2])
                self.taglistctrl.SetStringItem(index, 3, descriptions) 
            
            
            self.taglistctrl.Disable()
            self.update_well_selections()
            del prev_selected_tags[:]
            
    def onInstanceSelectiton(self, event):         
        if self.taglistctrl.IsEnabled() == False:
            event.Veto()
            dial = wx.MessageDialog(None, 'Please update Shelf by clicking time slider before selection!!', 'Warning', wx.OK | wx.ICON_WARNING)
            dial.ShowModal()  
            return
      
        ctrl = event.GetEventObject()
        i = -1
        del self.selections[:]
        while 1:
            i = ctrl.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if i == -1:
                break
            selected_tag = ctrl.GetItem(i, 0).GetText()+'|'+ctrl.GetItem(i, 1).GetText()+'|'+ctrl.GetItem(i, 2).GetText()
            self.selections += [selected_tag]
        #check whether selecting being made
        if not self.selections:
            dial = wx.MessageDialog(None, 'No Instances selected, please select an instance!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        
        for plate in self.vesselscroller.get_vessels():
                plate.enable_selection()
        self.is_selected = True
   
        self.update_well_selections()
        

            
    def on_group_selection(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        selected_group = ctrl.GetStringSelection()
        group_name = selected_group.split('_')[1]
        
        if selected_group.startswith('PlateGroup'):
            vessel_type = 'Plate'
        if selected_group.startswith('FlaskGroup'):
            vessel_type = 'Flask'
        if selected_group.startswith('DishGroup'):
            vessel_type = 'Dish'
        if selected_group.startswith('CoverslipGroup'):
            vessel_type = 'Coverslip'
        
            
        selected_ves_ids = []   
        for id in meta.get_field_instances('ExptVessel|'+vessel_type):
            stackName = meta.get_field('ExptVessel|'+vessel_type+'|GroupName|%s'%(id))
            if stackName == group_name:
                    selected_ves_ids += [id]
        
        #Draw the vessel in the vesselscroller panel according to the selection            
        self.vesselscroller.clear()        
        
        if selected_group.startswith('PlateGroup'):
            for id in sorted(selected_ves_ids):
                plate_shape = WELL_NAMES[meta.get_field('ExptVessel|Plate|Design|%s'%(id))]
                well_ids = PlateDesign.get_well_ids(plate_shape)
                plate_id = 'plate%s'%(id)
                plate = VesselPanel(self.vesselscroller, plate_id)
                self.vesselscroller.add_vessel_panel(plate, group_name+'_plate %s'%(id))
                plate.add_well_selection_handler(self.on_update_well)
                
        if selected_group.startswith('FlaskGroup'):
            for id in sorted(selected_ves_ids):
                well_ids = PlateDesign.get_well_ids(FLASK)
                plate_id = 'flask%s'%(id)
                plate = VesselPanel(self.vesselscroller, plate_id)
                self.vesselscroller.add_vessel_panel(plate, 'flask %s'%(id))
                plate.add_well_selection_handler(self.on_update_well) 
            
        if selected_group.startswith('DishGroup'):
            for id in sorted(selected_ves_ids):
                well_ids = PlateDesign.get_well_ids(FLASK)
                plate_id = 'dish%s'%(id)
                plate = VesselPanel(self.vesselscroller, plate_id)
                self.vesselscroller.add_vessel_panel(plate, 'dish %s'%(id))
                plate.add_well_selection_handler(self.on_update_well)
        
        if selected_group.startswith('CoverslipGroup'):
            for id in sorted(selected_ves_ids):
                well_ids = PlateDesign.get_well_ids(FLASK)
                plate_id = 'coverslip%s'%(id)
                plate = VesselPanel(self.vesselscroller, plate_id)
                self.vesselscroller.add_vessel_panel(plate, 'coverslip %s'%(id))
                plate.add_well_selection_handler(self.on_update_well) 
        
        self.update_well_selections()
        self.vesselscroller.FitInside()
    
    def onCreatePlates(self, event):
        self.vesselscroller.clear()
        meta = ExperimentSettings.getInstance()
        field_ids = sorted(meta.get_field_instances('ExptVessel|Plate'))
        for id in field_ids:
            stackName = meta.get_field('ExptVessel|Plate|GroupName|%s'%(id))
            plate_shape = WELL_NAMES[meta.get_field('ExptVessel|Plate|Design|%s'%(id))]
            well_ids = PlateDesign.get_well_ids(plate_shape)
            plate_id = 'plate%s'%(id)
            plate = VesselPanel(self.vesselscroller, plate_id)
            self.vesselscroller.add_vessel_panel(plate, stackName+'_plate %s'%(id))
            plate.add_well_selection_handler(self.on_update_well)
        self.update_well_selections()
        self.vesselscroller.FitInside() 
        
    def on_adjust_timepoint(self, evt):
        self.set_timepoint(self.time_slider.Value)
        self.onPopulateTaglist()

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
        self.update_well_selections()

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
    



    def update_well_selections(self):
        
        if self.selections == []:
            for plate in self.vesselscroller.get_vessels():
                plate.disable_selection()
                plate.set_selected_well_ids([])
                plate.set_marked_well_ids([])
            return
   
        else:
            selected_ids = []
            
            for selection in self.selections:
                prefix_instance = selection.rsplit('|',1)
    
                self.selected_tag_prefix = prefix_instance[0]
                self.selected_tag_instance = prefix_instance[1]
                                              
                wells_tag = '%s|Wells|%s|%s'%(self.selected_tag_prefix, 
                                              self.selected_tag_instance, 
                                              self.get_selected_timepoint())
                selected_ids = meta.get_field(wells_tag, [])
                
                
                marked_ids = []
                for inst in meta.get_field_instances(get_tag_stump(wells_tag)):
                    marked_ids += meta.get_field('%s|%s|%s'%(get_tag_stump(wells_tag), inst, self.get_selected_timepoint()), [])
                
                for plate in self.vesselscroller.get_vessels():
                    plate.enable_selection()
                    
                    selected_well_ids = [pw_id for pw_id in selected_ids if pw_id[0]==plate.get_plate_id()]
                    marked_well_ids   = [pw_id for pw_id in marked_ids if pw_id[0]==plate.get_plate_id()]
                    affected_well_ids = selected_well_ids.extend(marked_well_ids)
                    
                    
                    plate.set_selected_well_ids(selected_well_ids)
                    plate.set_marked_well_ids(marked_well_ids)
                    plate.set_affected_well_ids(selected_well_ids)
                    



    def on_update_well(self, platewell_id, selected):
        '''Called when a well is clicked.
        Populate all action tags with the set of wells that were effected.
        eg: AddProcess|Spin|Wells|<instance>|<timepoint> = ['A01',...]
            AddProcess|Spin|EventTimepoint|<instance> = [timepoint, ...]
        '''
        if self.selected_tag_prefix is None:
            return
        
        if self.harvestBut.GetValue() == True:
            return
        
        # Update the wells tags

        wells_tag = '%s|Wells|%s|%s'%(self.selected_tag_prefix, self.selected_tag_instance, self.get_selected_timepoint())
        platewell_ids = set(meta.get_field(wells_tag, []))
    
        if selected:
            platewell_ids.update([platewell_id])
            meta.set_field(wells_tag, list(platewell_ids))
        else:
            platewell_ids.remove(platewell_id)
            if len(platewell_ids) > 0:
                meta.set_field(wells_tag, list(platewell_ids))
            else:
                meta.remove_field(wells_tag)

        # Update the images tags
        if selected and self.selected_tag_prefix.startswith('DataAcquis'):
            
            images_tag = '%s|Images|%s|%s|%s'%(self.selected_tag_prefix, self.selected_tag_instance, self.get_selected_timepoint(), repr(platewell_id))
            
            if self.selected_tag_prefix == 'DataAcquis|HCS':
                dlg = wx.FileDialog(self,message='Select the images for Plate %s, '
                                    'Well %s'%(platewell_id[0], platewell_id[1]),
                                    defaultDir=os.getcwd(), defaultFile='', 
                                    style=wx.OPEN|wx.MULTIPLE)
            elif self.selected_tag_prefix == 'DataAcquis|FCS':
                dlg = wx.FileDialog(self,message='Select the FCS files for flask %s'%(platewell_id[0]),
                                    defaultDir=os.getcwd(), defaultFile='', wildcard = "Adobe PDF files (*.pdf)|*.pdf|",
                                    style=wx.OPEN|wx.MULTIPLE)
            elif self.selected_tag_prefix == 'DataAcquis|TLM':
                dlg = wx.FileDialog(self,message='Select the images for Plate %s, '
                                    'Well %s'%(platewell_id[0], platewell_id[1]),
                                    defaultDir=os.getcwd(), defaultFile='', 
                                    style=wx.OPEN|wx.MULTIPLE)
            else:
                raise 'unrecognized tag prefix'
            
            if dlg.ShowModal() == wx.ID_OK:
                meta.set_field(images_tag, dlg.GetPaths())
                os.chdir(os.path.split(dlg.GetPath())[0])
                dlg.Destroy()
            else:
                dlg.Destroy()
                meta.remove_field(images_tag)
                for vessel in self.vesselscroller.get_vessels():
                    if vessel.get_plate_id() == platewell_id[0]:
                        vessel.deselect_well_at_pos(
                            PlateDesign.get_pos_for_wellid(
                                PlateDesign.get_plate_format(platewell_id[0]), 
                                platewell_id[1]))
                        return
        
        

        # Update the timepoints tag
        #
        # XXX: This tag is redundant with the wells tags
        timepoint_tag = '%s|EventTimepoint|%s'%(self.selected_tag_prefix, self.selected_tag_instance)
        timepoints = set(meta.get_field(timepoint_tag, []))
        if len(platewell_ids) > 0:
            timepoints.update([self.get_selected_timepoint()])
            meta.set_field(timepoint_tag, list(timepoints))
        else:
            meta.remove_field(timepoint_tag)
    


if __name__ == "__main__":
    app = wx.PySimpleApp()

    f = Bench(None, size=(800,500))
    f.Show()

    app.MainLoop()
