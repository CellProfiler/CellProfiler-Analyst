import wx
import sys
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *

########################################################################        
########       Popup Dialog showing all instances of settings       ####
########################################################################            
class HarvestListDialog(wx.Dialog):
    def __init__(self, parent, harvested_pws_info):
        wx.Dialog.__init__(self, parent, -1, size=(600,500), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.listctrl = HarvestListCtrl(self, harvested_pws_info)
        
        self.selection_btn = wx.Button(self, wx.ID_OK, 'Selection complete')
        self.close_btn = wx.Button(self, wx.ID_CANCEL)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.Add(self.listctrl, 1, wx.EXPAND)
        hbox2.Add(self.selection_btn, 1)
        hbox2.Add(self.close_btn, 1)
        vbox.Add(hbox1, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 5)
        vbox.Add(hbox2, 1, wx.ALIGN_RIGHT, 5)
        self.SetSizer(vbox)
        self.Center()
 
 
        
class HarvestListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin, listmix.TextEditMixin):
    def __init__(self, parent, harvested_pws_info):
        wx.ListCtrl.__init__(self, parent, -1, size=(200,100), style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING|wx.LC_HRULES)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)  

        self.InsertColumn(0, "Plate")
        self.InsertColumn(1, "Well Location")
        self.InsertColumn(2, "Cell Line")
        self.InsertColumn(3, "ATCC Reference")
        self.InsertColumn(4, "Organism")
        self.InsertColumn(5, "Seeding Density")
        self.InsertColumn(6, "Medium Used")
        self.InsertColumn(7, "Medium Additives")
        self.InsertColumn(8, "Trypsinizatiton")
        
        self.harvested_pws_info = harvested_pws_info
        
        self.PopulateList()
       

    def PopulateList(self):
        
        items = self.harvested_pws_info.items()
        
        row = 1
    
        for key, data in items:
            index = self.InsertStringItem(sys.maxint, data[0])
            for col in range(0,9):
                self.SetStringItem(index, col, data[col])
            self.SetItemData(index, row)
            row += 1
  
    def get_selected_instances(self):
        i = -1
        selections = []
        while 1:
            i = self.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if i == -1:
                break
            selections += [self.GetItem(i).GetText()]
        #check whether selecting being made
        if not selections:
            dial = wx.MessageDialog(None, 'No Instances selected, please select an instance!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
        return selections
            
    
    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()
    def GetListCtrl(self):
        return self
    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s
    def SortItems(self,sorter=cmp):
        items = list(self.itemDataMap.keys())
        items.sort(sorter)
        self.itemIndexMap = items
        self.Refresh()