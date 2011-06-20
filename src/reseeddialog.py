import wx
import sys
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *
from bench import *


########################################################################        
########       Popup Dialog showing all instances of stock culture   ####
########################################################################            
class ReseedDialog(wx.Dialog):
    def __init__(self, parent, harvest_instance, selected_timepoint):
        wx.Dialog.__init__(self, parent, -1, size=(400,500), title='Transfer', style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        
        self.settings_controls = {}        
        meta = ExperimentSettings.getInstance()
        self.harvest_instance = harvest_instance
        self.selected_timepoint = selected_timepoint
        
        fgs = wx.FlexGridSizer(rows=30, cols=2, hgap=5, vgap=5)
        
        #----------- Microscope Labels and Text Controler-------        
        plateselect_header = wx.StaticText(self, -1, 'Plate')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        plateselect_header.SetFont(font)
        fgs.Add(plateselect_header, 0)
        fgs.Add(wx.StaticText(self, -1, ''), 0)
            
        # Harvested Well number
        hwellTAG = 'CellTransfer|Harvest|Wells|%s|%s'%(self.harvest_instance, self.selected_timepoint)
        harvested_well_number = len(meta.get_field(hwellTAG, ''))

        #--Plate selection--#
        stackNames = []
        for id in meta.get_field_instances('ExptVessel|Plate'):
            #TO DO Check whether the plate has already been seeded with cells and for Flask, Dish, etc.
             # TODO: set to a stack which has not been seeded yet
            stack_name = 'PlateGroup_'+meta.get_field('ExptVessel|Plate|GroupName|%s'%(id))
            stackNames += [stack_name]
            
        stack_selection = wx.Choice(self, -1,  choices=stackNames)
        stack_selection.Bind(wx.EVT_CHOICE, wx.GetApp().get_bench().on_group_selection)
        stack_selection.SetToolTipString('Select the stack to be reseeded')
        fgs.Add(wx.StaticText(self, -1, 'Select Reseeding Plate'), 0)
        fgs.Add(stack_selection, 0, wx.EXPAND) 
    
        reseed_header = wx.StaticText(self, -1, 'Condition')
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        reseed_header.SetFont(font)
        fgs.Add(reseed_header, 0)
        fgs.Add(wx.StaticText(self, -1, ''), 0)
        
        #Seeding Density
        self.densityFIELD = wx.TextCtrl(self, value=meta.get_field('CellTransfer|Harvest|Density|%s'%self.harvest_instance, ''))
        self.densityFIELD.SetToolTipString('Number of cells reseeded from each well or flask')
        fgs.Add(wx.StaticText(self, -1, 'Density'), 0)
        fgs.Add(self.densityFIELD, 0, wx.EXPAND)
        
        # Medium Used
        self.mediumFIELD = wx.Choice(self, -1,  choices=['Typical', 'Atypical'])
        self.mediumFIELD.SetStringSelection(meta.get_field('CellTransfer|Harvest|MediumUsed|%s'%self.harvest_instance, ''))
        self.mediumFIELD.SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self, -1, 'Medium Used'), 0)
        fgs.Add(self.mediumFIELD, 0, wx.EXPAND) 
        
        #  Medium Addatives
        self.mediumaddFIELD = wx.TextCtrl(self, value=meta.get_field('CellTransfer|Harvest|MediumAddatives|%s'%self.harvest_instance, ''))
        self.mediumaddFIELD.SetToolTipString('Any medium addatives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self, -1, 'Medium Additives'), 0)
        fgs.Add(self.mediumaddFIELD, 0, wx.EXPAND)
        
        # Trypsinization
        self.trypsinFIELD = wx.Choice(self, -1,  choices=['Yes', 'No'])
        self.trypsinFIELD.SetStringSelection(meta.get_field('CellTransfer|Harvest|Trypsinizatiton|%s'%self.harvest_instance, ''))
        self.trypsinFIELD.SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self, -1, 'Trypsinization'), 0)
        fgs.Add(self.trypsinFIELD, 0, wx.EXPAND) 
        
        #Buttons    
        reseed_btn = wx.Button(self, wx.ID_OK, 'Proceed Reseeding')
        fgs.Add(wx.StaticText(self, -1, ''), 0)     
        fgs.Add(reseed_btn, 0)
        
        #reseedseq_header = wx.StaticText(self, -1, 'Order')
        #font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        #reseedseq_header.SetFont(font)
        #fgs.Add(reseedseq_header, 0)
        #fgs.Add(wx.StaticText(self, -1, ''), 0)
        
         
        #one_to_one = wx.CheckBox(self, -1, 'Reseed from %s --> %s Wells'%(harvested_well_number, harvested_well_number))
        #one_to_many = wx.CheckBox(self, -1, 'Diverge each of the harvested Well by')
        #many_to_one = wx.CheckBox(self, -1, 'Converge to single Well')
        #divergence_order = wx.Choice(self, -1, choices=['2','3','4','5','6'])
        
        #fgs.Add(one_to_one, 0)
        #fgs.Add(wx.StaticText(self, -1, ''), 0)
        #fgs.Add(one_to_many, 0)
        #fgs.Add(divergence_order, 0)
        #fgs.Add(many_to_one, 0)
        #fgs.Add(wx.StaticText(self, -1, ''), 0)
        
        #---------------Layout with sizers---------------
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(fgs, 1, wx.EXPAND|wx.ALL, 5)
        
        
        #del wx.GetApp().get_bench().selections[:]
        #selected_tag = 'CellTransfer|Reseed|%s'%self.reseed_instance
        #wx.GetApp().get_bench().selections += [selected_tag]
        
        if self.ShowModal() == wx.ID_OK:
            meta = ExperimentSettings.getInstance()
            
            # Reseeding instance number
            reseed_list = meta.get_field_instances('CellTransfer|Reseed|')
            if reseed_list:
                self.reseed_instance  =  int(reseed_list[-1])+1
            else:
                self.reseed_instance = 1
            
            #meta.set_field('CellTransfer|Reseed|HarvestInstance|%s'%self.reseed_instance,  str(self.harvest_instance))
            #meta.set_field('CellTransfer|Reseed|EventTimepoint|%s'%self.reseed_instance,    self.selected_timepoint)
            meta.set_field('CellTransfer|Seed|Density|%s'%self.reseed_instance, self.densityFIELD.GetValue())
            meta.set_field('CellTransfer|Seed|MediumUsed|%s'%self.reseed_instance, self.mediumFIELD.GetStringSelection())
            meta.set_field('CellTransfer|Seed|MediumAddatives|%s'%self.reseed_instance, self.mediumaddFIELD.GetValue())
            meta.set_field('CellTransfer|Seed|Trypsinizatiton|%s'%self.reseed_instance, self.trypsinFIELD.GetStringSelection())
            
            wx.GetApp().get_bench().selections
            
            self.Destroy()
            

            

     
    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
         
        print tag
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
     
        
