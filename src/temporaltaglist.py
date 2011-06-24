import wx
import sys
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *

meta = ExperimentSettings.getInstance()

## TODO: Add search capability
class TemporalTagListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):#, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        '''
        tag_prefix -- the tag whose instances to list in this list control
        '''
        wx.ListCtrl.__init__(self, parent, -1, size=(200,100), style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING|wx.LC_HRULES|wx.LC_SINGLE_SEL)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
##        listmix.ColumnSorterMixin.__init__(self, 4)

        self.protocols = []
        
        meta.add_subscriber(self.update, 'CellTransfer.*')
        meta.add_subscriber(self.update, 'Perturbation.*')
        meta.add_subscriber(self.update, 'Labeling.*')
        meta.add_subscriber(self.update, 'AddProcess.*')
        meta.add_subscriber(self.update, 'DataAcquis.*')
        
        self.InsertColumn(0, "Category")
        self.InsertColumn(1, "Action")
        self.InsertColumn(2, "Instance No")
        self.InsertColumn(3, "Description")
        
    def get_description(self, protocol):
        return '; '.join(['%s=%s'%(k, v) for k, v in meta.get_attribute_dict(protocol).items()])
    
    def update(self, changed_tag):
        '''called when experiment metadata changes to update the protocol list
        '''
        new_protocols = set([get_tag_protocol(tag) 
                             for tag in meta.get_action_tags()])
        if set(self.protocols) != new_protocols:
            self.protocols = sorted(new_protocols)
            sel = self.get_selected_protocols()
            self.DeleteAllItems()
            for prot in self.protocols:
                cat, action, inst = prot.split('|')
                i = self.InsertStringItem(sys.maxint, cat)
                self.SetStringItem(i, 1, action)
                self.SetStringItem(i, 2, inst)
                self.SetStringItem(i, 3, self.get_description(prot))
            self.set_selected_protocols(sel)
        else:
            for i, prot in enumerate(self.protocols):
                self.SetStringItem(i, 3, self.get_description(prot))
            
            
    def set_selected_protocols(self, protocol_list):
        for i, protocol in enumerate(self.protocols):
            if protocol in protocol_list:
                self.Select(i)
            else:
                self.Select(i, False)
            
    def get_selected_protocols(self):
        sel = []
        i = -1
        while 1:
            i = self.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if i == -1:
                break
            sel += [self.protocols[i]]
        return sel
            
    def getColumnText(self, index, col):
        return self.GetItem(index, col).GetText()
    
    def GetListCtrl(self):
        return self
    
    #
    # TODO: make sortable
    #
    
##    def OnGetItemText(self, item, col):
##        index=self.itemIndexMap[item]
##        s = self.itemDataMap[index][col]
##        return s
    
##    def SortItems(self,sorter=cmp):
##        items = list(self.itemDataMap.keys())
##        items.sort(sorter)
##        self.itemIndexMap = items
##        self.Refresh()