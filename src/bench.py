from experimentsettings import *
from vesselpanel import VesselPanel, VesselScroller
import wx
import os
from wx.lib.masked import TimeCtrl
import numpy as np
import icons

ID_SEED = wx.NewId()
ID_HARVEST = wx.NewId()
ID_CHEM = wx.NewId()
ID_BIO = wx.NewId()
ID_STAIN = wx.NewId()
ID_SPIN = wx.NewId()
ID_WASH = wx.NewId()
ID_DRY = wx.NewId()
ID_IMAGE = wx.NewId()
ID_TIMELAPSE = wx.NewId()
ID_FLOW = wx.NewId()

meta = ExperimentSettings.getInstance()


class Bench(wx.Frame):
    def __init__(self, parent, id=-1, title='Bench', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)

        meta.add_subscriber(self.update_plate_window, 'ExptVessel.*')
        meta.add_subscriber(self.update_plate_window, get_matchstring_for_subtag(2, 'Well'))

        tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        tb.SetToolBitmapSize((32,32))
        tb.AddRadioLabelTool(ID_SEED, 'Seed', icons.seed.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_HARVEST, 'Harvest', icons.harvest.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_CHEM, 'Chem', icons.treat.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_BIO, 'Bio', icons.treat_bio.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_STAIN, 'Stain', icons.add_stain.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_SPIN, 'Spin', icons.spin.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_WASH, 'Wash', icons.wash.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_DRY, 'Dry', icons.dry.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_IMAGE, 'Image', icons.imaging.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_TIMELAPSE, 'Timelapse', icons.timelapse.ConvertToBitmap(), shortHelp='', longHelp='')
        tb.AddRadioLabelTool(ID_FLOW, 'Flow', icons.flow.ConvertToBitmap(), shortHelp='', longHelp='')        
        tb.Realize()

        self.mode_tag_prefix = []
        self.mode_tag_instance = None

        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.setting_shown = False
        self.vesselscroller = VesselScroller(self)
        self.Sizer.Add(self.vesselscroller, 1, wx.EXPAND)
        self.update_plate_window(None)

        time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.time_slider = wx.Slider(self, -1)
        self.time_slider.Bind(wx.EVT_SLIDER, self.on_adjust_timepoint)
        self.time_slider.SetRange(0, 1440)
        self.tlabel1 = wx.StaticText(self, -1, "Time:")
        self.time_text_box = wx.TextCtrl(self, -1, '0:00', size=(50, -1))
        self.time_spin = wx.SpinButton(self, -1, style=wx.SP_VERTICAL)
        self.time_spin.Max = 1000000

        self.add24_button = wx.Button(self, -1, "Add 24h")
        self.add24_button.Bind(wx.EVT_BUTTON, lambda(evt):self.time_slider.SetRange(0, self.time_slider.GetMax()+1440))

        time_sizer.AddSpacer((10,-1))
        time_sizer.Add(self.tlabel1,0, wx.EXPAND)
        time_sizer.Add(self.time_slider, 1, wx.EXPAND)
        time_sizer.AddSpacer((5,-1))
        time_sizer.Add(self.time_text_box, 0, wx.BOTTOM, 15)
        time_sizer.Add(self.time_spin, 0, wx.BOTTOM, 15)
        time_sizer.AddSpacer((5,-1))
        time_sizer.Add(self.add24_button, 0, wx.EXPAND, wx.TOP|wx.BOTTOM, 5)
        time_sizer.AddSpacer((10,-1))
        self.Sizer.Add(time_sizer, 0, wx.EXPAND)

        self.Bind(wx.EVT_TOOL, self.on_tool_clicked)
        self.time_spin.Bind(wx.EVT_SPIN_UP, self.on_increment_time)
        self.time_spin.Bind(wx.EVT_SPIN_DOWN, self.on_decrement_time)
        self.time_text_box.Bind(wx.EVT_TEXT, self.on_edit_time_text_box)

    def get_selected_timepoint(self):
        return self.time_slider.GetValue()

    def on_adjust_timepoint(self, evt):
        time_string = format_time_string(self.time_slider.GetValue())
        self.time_text_box.SetValue(time_string)
        self.update_well_selections()
        
    def on_increment_time(self, evt):
        self.time_slider.Value += 1
        self.on_adjust_timepoint(None)
        
    def on_decrement_time(self, evt):
        self.time_slider.Value -= 1
        self.on_adjust_timepoint(None)
        
    def on_edit_time_text_box(self, evt):
        time_string = self.time_text_box.GetValue()
        try:
            hours, mins = map(int, time_string.split(':'))
            minutes = hours * 60 + mins
            self.time_text_box.SetForegroundColour(wx.BLACK)
            self.time_slider.SetValue(minutes)
            self.update_well_selections()
        except:
            self.time_text_box.SetForegroundColour(wx.RED)

    def update_well_selections(self):
        meta = ExperimentSettings.getInstance()
        if self.mode_tag_instance is None or self.mode_tag_prefix == []:
            for plate in self.vesselscroller.get_vessels():
                plate.disable_selection()
                plate.set_selected_well_ids([])
                plate.set_marked_well_ids([])
            return
        else:
            wells_tag = '%s|Wells|%s|%s'%(self.mode_tag_prefix, 
                                          self.mode_tag_instance, 
                                          self.get_selected_timepoint())
            selected_ids = meta.get_field(wells_tag, [])
            marked_ids = []
            for inst in meta.get_field_instances(get_tag_stump(wells_tag)):
                marked_ids += meta.get_field('%s|%s|%s'%(get_tag_stump(wells_tag), inst, self.get_selected_timepoint()), [])
            for plate in self.vesselscroller.get_vessels():
                plate.enable_selection()
                plate.set_selected_well_ids([pw_id for pw_id in selected_ids 
                                             if pw_id[0]==plate.get_plate_id()])
                plate.set_marked_well_ids([pw_id for pw_id in marked_ids 
                                           if pw_id[0]==plate.get_plate_id()])


    def update_plate_window(self, tag):
        '''Syncronizes the vessel panels with the vessel metadata.
        '''
        self.vesselscroller.clear()
        meta = ExperimentSettings.getInstance()
        field_ids = meta.get_field_instances('ExptVessel|Plate')
        for id in field_ids:
            plate_shape = WELL_NAMES[meta.get_field('ExptVessel|Plate|Design|%s'%(id))]
            well_ids = PlateDesign.get_well_ids(plate_shape)
            plate_id = 'plate%s'%(id)
            plate = VesselPanel(self.vesselscroller, plate_id)
            self.vesselscroller.add_vessel_panel(plate, 'plate %s'%(id))
            plate.add_well_selection_handler(self.on_update_well)

        field_ids = meta.get_field_instances('ExptVessel|Flask')
        for id in field_ids:
            well_ids = PlateDesign.get_well_ids(FLASK)
            plate_id = 'flask%s'%(id)
            plate = VesselPanel(self.vesselscroller, plate_id)
            self.vesselscroller.add_vessel_panel(plate, 'flask %s'%(id))
            plate.add_well_selection_handler(self.on_update_well)
        self.update_well_selections()
        self.vesselscroller.FitInside()

    def on_update_well(self, platewell_id, selected):
        '''Called when a well is clicked.
        Populate all action tags with the set of wells the were effected.
        eg: ExpNum|AddProcess|Spin|Wells|<instance>|<timepoint> = ['A01',...]
            ExpNum|AddProcess|Spin|EventTimepoint|<instance> = [timepoint, ...]
        '''
        if self.mode_tag_instance is None or self.mode_tag_prefix == []:
            return
        meta = ExperimentSettings.getInstance()

        #
        # Update the images tags
        #
        images_tag = '%s|Images|%s|%s|%s'%(self.mode_tag_prefix, 
                                           self.mode_tag_instance, 
                                           self.get_selected_timepoint(),
                                           repr(platewell_id))
        if selected and self.mode_tag_prefix.startswith('DataAcquis'):
            if self.mode_tag_prefix == 'DataAcquis|HCS':
                dlg = wx.FileDialog(self,message='Select the images for Plate %s, '
                                    'Well %s'%(platewell_id[0], platewell_id[1]),
                                    defaultDir=os.getcwd(), defaultFile='', 
                                    style=wx.OPEN|wx.MULTIPLE)
            elif self.mode_tag_prefix == 'DataAcquis|FCS':
                dlg = wx.FileDialog(self,message='Select the FCS files for flask %s'%(platewell_id[0]),
                                    defaultDir=os.getcwd(), defaultFile='', 
                                    style=wx.OPEN|wx.MULTIPLE)
            elif self.mode_tag_prefix == 'DataAcquis|TLM':
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
        else:
            meta.remove_field(images_tag)
        
        #
        # Update the wells tags
        #
        wells_tag = '%s|Wells|%s|%s'%(self.mode_tag_prefix, 
                                      self.mode_tag_instance, 
                                      self.get_selected_timepoint())
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

        #
        # Update the timepoints tag
        #
        # XXX: This tag is redundant with the wells tags
        timepoint_tag = '%s|EventTimepoint|%s'%(self.mode_tag_prefix, self.mode_tag_instance)
        timepoints = set(meta.get_field(timepoint_tag, []))
        if len(platewell_ids) > 0:
            timepoints.update([self.get_selected_timepoint()])
            meta.set_field(timepoint_tag, list(timepoints))
        else:
            meta.remove_field(timepoint_tag)

    def on_tool_clicked(self, evt):
        meta = ExperimentSettings.getInstance()
        self.mode_tag_instance = None
        if self.setting_shown:
            control = self.Sizer.GetItem(0).GetWindow()
            self.Sizer.Remove(0)
            control.Destroy()

        if evt.Checked():
            def create_setting_panel(label, choices):
                setting = wx.Panel(self)
                setting.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
                if choices != []:
                    setting.Sizer.Add(wx.StaticText(setting, -1, label), 0, wx.ALL, 10)
                    choice_control = wx.Choice(setting, -1, choices=choices)
                    choice_control.Select(0)
                    setting.Sizer.Add(choice_control, 0, wx.TOP, 8)
                    self.mode_tag_instance = choices[0]

                    def choice_handler(evt):
                        self.mode_tag_instance = evt.GetEventObject().GetStringSelection()
                        self.update_well_selections()
                    choice_control.Bind(wx.EVT_CHOICE, choice_handler)
                else:
                    label = 'No configurations available. Please configure presets first.'
                    setting.Sizer.Add(wx.StaticText(setting, -1, label), 0, wx.ALL, 10)
                return setting

            if evt.Id == ID_SEED:
                panel = create_setting_panel('Seeding settings: ', meta.get_field_instances('CellTransfer|Seed'))
                self.mode_tag_prefix = 'CellTransfer|Seed'
            elif evt.Id == ID_HARVEST:
                panel = create_setting_panel('Harvesting settings: ', meta.get_field_instances('CellTransfer|Harvest'))
                self.mode_tag_prefix = 'CellTransfer|Harvest'
            elif evt.Id == ID_CHEM:
                panel = create_setting_panel('Chemical treatment settings: ', meta.get_field_instances('Perturbation|Chem'))
                self.mode_tag_prefix = 'Perturbation|Chem'
            elif evt.Id == ID_BIO:
                panel = create_setting_panel('Biological treatment settings: ', meta.get_field_instances('Perturbation|Bio'))
                self.mode_tag_prefix = 'Perturbation|Bio'
            elif evt.Id == ID_STAIN:
                panel = create_setting_panel('Stain settings: ', meta.get_field_instances('AddProcess|Stain'))
                self.mode_tag_prefix = 'AddProcess|Stain'
            elif evt.Id == ID_SPIN:
                panel = create_setting_panel('Spin settings: ', meta.get_field_instances('AddProcess|Spin'))
                self.mode_tag_prefix = 'AddProcess|Spin'
            elif evt.Id == ID_WASH:
                panel = create_setting_panel('Wash settings: ', meta.get_field_instances('AddProcess|Wash'))
                self.mode_tag_prefix = 'AddProcess|Wash'
            elif evt.Id == ID_DRY:
                panel = create_setting_panel('Dry settings: ', meta.get_field_instances('AddProcess|Dry'))
                self.mode_tag_prefix = 'AddProcess|Dry'
            elif evt.Id == ID_IMAGE:
                panel = create_setting_panel('Image settings: ', meta.get_field_instances('DataAcquis|HCS'))
                self.mode_tag_prefix = 'DataAcquis|HCS'
            elif evt.Id == ID_TIMELAPSE:
                panel = create_setting_panel('Image settings: ', meta.get_field_instances('DataAcquis|TLM'))
                self.mode_tag_prefix = 'DataAcquis|TLM'
            elif evt.Id == ID_FLOW:
                panel = create_setting_panel('Flow settings: ', meta.get_field_instances('DataAcquis|FCS'))
                self.mode_tag_prefix = 'DataAcquis|FCS'
            else:
                raise Exception('Unknown tool clicked.')
            self.Sizer.Insert(0, panel, 0, wx.EXPAND)
            self.setting_shown = True
        else:
            self.mode_tag_prefix = []
            self.setting_shown = False
        self.update_well_selections()
        self.Layout()



if __name__ == "__main__":
    app = wx.PySimpleApp()

    f = Bench(None, size=(800,-1))
    f.Show()

    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import cellprofiler.utilities.jutil as jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"