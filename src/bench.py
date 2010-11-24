from experimentsettings import *
from vesselpanel import *
import wx
from wx.lib.masked import TimeCtrl
import numpy as np
import icons

class VesselScroller(wx.ScrolledWindow):
    def __init__(self, parent, id=-1, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, id, **kwargs)
        self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        (w,h) = self.Sizer.GetSize()
        self.SetScrollbars(20,20,w/20,h/20,0,0)
        self.plates = []
        
    def add_vessel_panel(self, panel, plate_id):
        if len(self.Sizer.GetChildren()) > 0:
            self.Sizer.AddSpacer((10,-1))
        sz = wx.BoxSizer(wx.VERTICAL)
        sz.Add(wx.StaticText(self, -1, plate_id), 0, wx.EXPAND|wx.TOP|wx.LEFT, 10)
        sz.Add(panel, 1, wx.EXPAND)
        self.Sizer.Add(sz, 1, wx.EXPAND)
        self.plates += [panel]
    
    def get_vessels(self):
        return self.plates
    
    def get_selected_well_ids(self):
        wells = []
        for plate in self.plates:
            wells += plate.get_selected_well_keys()
        return wells
    
    def clear(self):
        self.plates = []
        self.Sizer.Clear(deleteWindows=True)

ID_SEED = wx.NewId()
ID_HARVEST = wx.NewId()
ID_CHEM = wx.NewId()
ID_BIO = wx.NewId()
ID_STAIN = wx.NewId()
ID_SPIN = wx.NewId()
ID_WASH = wx.NewId()
ID_DRY = wx.NewId()
ID_IMAGE = wx.NewId()
ID_FLOW = wx.NewId()


class Bench(wx.Frame):
    def __init__(self, parent, id=-1, title='Bench', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)

        meta = ExperimentSettings.getInstance()
        
        meta.add_subscriber(self.update_plate_window, ['ExptVessel'])
        
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
        tb.AddRadioLabelTool(ID_FLOW, 'Flow', icons.flow.ConvertToBitmap(), shortHelp='', longHelp='')        
        tb.Realize()
        
        self.mode_tag_prefixes = []
        self.mode_tag_instance = None
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.setting_shown = False
        self.vesselscroller = VesselScroller(self)
        self.Sizer.Add(self.vesselscroller, 1, wx.EXPAND)
        self.update_plate_window()
        
        time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.time_slider = wx.Slider(self, -1, style = wx.SL_LABELS|wx.SL_AUTOTICKS)
        self.time_slider.Bind(wx.EVT_SLIDER, self.on_adjust_timepoint)
        self.time_slider.SetRange(0, 24)
        #clock = TimeCtrl(self, -1, display_seconds=False)
        self.add24_button = wx.Button(self, -1, "Add 24h")
        self.add24_button.Bind(wx.EVT_BUTTON, lambda(evt):self.time_slider.SetRange(0, self.time_slider.GetMax()+24))
        time_sizer.Add(self.time_slider, 1, wx.EXPAND)
        time_sizer.Add(self.add24_button, 0, wx.EXPAND)
        self.Sizer.Add(time_sizer, 0, wx.EXPAND)
        
        self.Bind(wx.EVT_TOOL, self.on_tool_clicked)
        
    def on_adjust_timepoint(self, evt):
        self.update_well_selections()
        
    def update_well_selections(self):
        if self.mode_tag_instance is None or self.mode_tag_prefixes == []:
            for plate in self.vesselscroller.get_vessels():
                plate.disable_selection()
                plate.set_selected_well_ids([])
            return
        else:
            for plate in self.vesselscroller.get_vessels():
                plate.enable_selection()
                #plate.set_selected_well_ids([])
        
        
    def update_plate_window(self):
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
            ExpNum|AddProcess|Spin|EventTimepoint|<instance> = timepoint
        '''
        if self.mode_tag_instance is None or self.mode_tag_prefixes == []:
            return

        meta = ExperimentSettings.getInstance()
        for prefix in self.mode_tag_prefixes:
            wells_tag = '%s|Wells|%s|%s'%(prefix, self.mode_tag_instance, self.time_slider.GetSelStart())
            platewell_ids = set(meta.get_field(wells_tag, []))
            if selected:
                platewell_ids.update([platewell_id])
            else:
                platewell_ids.remove(platewell_id)
            meta.set_field(wells_tag, list(platewell_ids))
            print platewell_ids
            
            timepoint_tag = '%s|EventTimepoint|%s'%(prefix, self.mode_tag_instance)
            meta.set_field(timepoint_tag, self.time_slider.GetSelStart())
            
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
                setting.Sizer.Add(wx.StaticText(setting, -1, label), 0, wx.ALL, 10)
                choice_control = wx.Choice(setting, -1, choices=choices)
                choice_control.Select(0)
                if choices != []:
                    self.mode_tag_instance = choices[0]
                else:
                    self.mode_tag_instance = None
                setting.Sizer.Add(choice_control, 0, wx.TOP, 8)
                
                def choice_handler(evt):
                    self.mode_tag_instance = evt.GetEventObject().GetStringSelection()
                    self.update_well_selections()
                choice_control.Bind(wx.EVT_CHOICE, choice_handler)
                return setting
    
            if evt.Id == ID_SEED:
                panel = create_setting_panel('Seeding settings: ', meta.get_field_instances('CellTransfer|Seed'))
                self.mode_tag_prefixes = ['CellTransfer|Seed']
            elif evt.Id == ID_HARVEST:
                panel = create_setting_panel('Harvesting settings: ', meta.get_field_instances('CellTransfer|Harvest'))
                self.mode_tag_prefixes = ['CellTransfer|Harvest']
            elif evt.Id == ID_CHEM:
                panel = create_setting_panel('Chemical treatment settings: ', meta.get_field_instances('Perturbation|Chem'))
                self.mode_tag_prefixes = ['Perturbation|Chem']
            elif evt.Id == ID_BIO:
                panel = create_setting_panel('Biological treatment settings: ', meta.get_field_instances('Perturbation|Bio'))
                self.mode_tag_prefixes = ['Perturbation|Bio']
            elif evt.Id == ID_STAIN:
                panel = create_setting_panel('Stain settings: ', meta.get_field_instances('AddProcess|Stain'))
                self.mode_tag_prefixes = ['AddProcess|Stain']
            elif evt.Id == ID_SPIN:
                panel = create_setting_panel('Spin settings: ', meta.get_field_instances('AddProcess|Spin'))
                self.mode_tag_prefixes = ['AddProcess|Spin']
            elif evt.Id == ID_WASH:
                panel = create_setting_panel('Wash settings: ', meta.get_field_instances('AddProcess|Wash'))
                self.mode_tag_prefixes = ['AddProcess|Wash']
            elif evt.Id == ID_DRY:
                panel = create_setting_panel('Dry settings: ', meta.get_field_instances('AddProcess|Dry'))
                self.mode_tag_prefixes = ['AddProcess|Dry']
            elif evt.Id == ID_IMAGE:
                choices = meta.get_field_instances('DataAcquis|TLM') + meta.get_field_instances('DataAcquis|HCS')
                panel = create_setting_panel('Image settings: ', choices)
                self.mode_tag_prefixes = ['DataAcquis|TLM', 'DataAcquis|HCS']
            elif evt.Id == ID_FLOW:
                panel = create_setting_panel('Flow settings: ', meta.get_field_instances('DataAcquis|FCS'))
                self.mode_tag_prefixes = ['DataAcquis|FCS']
            else:
                raise Exception('Unknown tool clicked.')
            self.Sizer.Insert(0, panel, 0, wx.EXPAND)
            self.setting_shown = True
        else:
            self.mode_tag_prefixes = []
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
