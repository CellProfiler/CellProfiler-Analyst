import wx
import sys
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *

########################################################################        
########       Popup Dialog showing all instances of stock culture   ####
########################################################################            
class SeedDialog(wx.Dialog):
    def __init__(self, parent, stock_instance):
        wx.Dialog.__init__(self, parent, -1, size=(250,300), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        
        self.settings_controls = {}        
        meta = ExperimentSettings.getInstance()
        
        cellload_list = meta.get_field_instances('CellTransfer|Seed|')
        self.page_counter = 1
        # update the  number of existing cell loading
        if cellload_list:    
            self.page_counter  =  int(cellload_list[-1])+1
       
        fgs = wx.FlexGridSizer(rows=15, cols=2, hgap=5, vgap=5) 
        
        # Display the some important parameters of Stock Culture
        fgs.Add(wx.StaticText(self, -1, 'Cell Line'), 0)
        fgs.Add(wx.StaticText(self, -1, meta.get_field('StockCulture|Sample|CellLine|%s'%str(stock_instance), default='')), 0)
        fgs.Add(wx.StaticText(self, -1, 'ATCC Reference'), 0)
        fgs.Add(wx.StaticText(self, -1, meta.get_field('StockCulture|Sample|ATCCref|%s'%str(stock_instance), default='')), 0)
        fgs.Add(wx.StaticText(self, -1, 'Passage Number'), 0)
        fgs.Add(wx.StaticText(self, -1, meta.get_field('StockCulture|Sample|PassageNumber|%s'%str(stock_instance), default='')), 0)
        fgs.Add(wx.StaticText(self, -1, 'Stock Flask Cell Density'), 0)
        fgs.Add(wx.StaticText(self, -1, meta.get_field('StockCulture|Sample|Density|%s'%str(stock_instance), default='')), 0)
        
        # Link instance value of stock culture to the current seeding instance
        meta.set_field('CellTransfer|Seed|StockInstance|'+str(self.page_counter), stock_instance)
        
        # Seeding Density
        seedTAG = 'CellTransfer|Seed|SeedingDensity|'+str(self.page_counter)
        self.settings_controls[seedTAG] = wx.TextCtrl(self, value=meta.get_field(seedTAG, default=''))
        self.settings_controls[seedTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[seedTAG].SetToolTipString('Number of cells seeded in each well or flask')
        fgs.Add(wx.StaticText(self, -1, 'Seeding Cell Density'), 0)
        fgs.Add(self.settings_controls[seedTAG], 0, wx.EXPAND)

        # Medium Used
        medmTAG = 'CellTransfer|Seed|MediumUsed|'+str(self.page_counter)
        self.settings_controls[medmTAG] = wx.Choice(self, -1,  choices=['Typical', 'Atypical'])
        if meta.get_field(medmTAG) is not None:
            self.settings_controls[medmTAG].SetStringSelection(meta.get_field(medmTAG))
        self.settings_controls[medmTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[medmTAG].SetToolTipString('Typical/Atypical (Ref in both cases)')
        fgs.Add(wx.StaticText(self, -1, 'Medium Used'), 0)
        fgs.Add(self.settings_controls[medmTAG], 0, wx.EXPAND)

        #  Medium Addatives
        medaddTAG = 'CellTransfer|Seed|MediumAddatives|'+str(self.page_counter)
        self.settings_controls[medaddTAG] = wx.TextCtrl(self, value=meta.get_field(medaddTAG, default=''))
        self.settings_controls[medaddTAG].Bind(wx.EVT_TEXT, self.OnSavingData)
        self.settings_controls[medaddTAG].SetToolTipString('Any medium additives used with concentration, Glutamine')
        fgs.Add(wx.StaticText(self, -1, 'Medium Additives'), 0)
        fgs.Add(self.settings_controls[medaddTAG], 0, wx.EXPAND)

        #Trypsinization
        trypsTAG = 'CellTransfer|Seed|Trypsinizatiton|'+str(self.page_counter)
        self.settings_controls[trypsTAG] = wx.Choice(self, -1,  choices=['Yes', 'No'])
        if meta.get_field(trypsTAG) is not None:
            self.settings_controls[trypsTAG].SetStringSelection(meta.get_field(trypsTAG))
        self.settings_controls[trypsTAG].Bind(wx.EVT_CHOICE, self.OnSavingData)
        self.settings_controls[trypsTAG].SetToolTipString('(Y/N) After cells were loded on the exerimental vessel, i.e. time 0 of the experiment')
        fgs.Add(wx.StaticText(self, -1, 'Trypsinization'), 0)
        fgs.Add(self.settings_controls[trypsTAG], 0, wx.EXPAND)
        
        #Buttons    
        self.selection_btn = wx.Button(self, wx.ID_OK, 'Proceed Seeding')
        self.close_btn = wx.Button(self, wx.ID_CANCEL)
        
        fgs.Add(self.selection_btn, 0, wx.ALL, 5)
        fgs.Add(self.close_btn, 0, wx.ALL, 5)
        #---------------Layout with sizers---------------
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(fgs, 1, wx.EXPAND|wx.ALL, 5)
        
    def OnSavingData(self, event):
        meta = ExperimentSettings.getInstance()

        ctrl = event.GetEventObject()
        tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
        if isinstance(ctrl, wx.Choice):
            meta.set_field(tag, ctrl.GetStringSelection())
        else:
            meta.set_field(tag, ctrl.GetValue())
     
        
