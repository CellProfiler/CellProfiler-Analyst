import wx
import sys
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *

meta = ExperimentSettings.getInstance()
        
class TemporalTagListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        '''
        tag_prefix -- the tag whose instances to list in this list control
        '''
        
        wx.ListCtrl.__init__(self, parent, -1, size=(200,100), style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING|wx.LC_HRULES)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        self.InsertColumn(0, "Category")
        self.InsertColumn(1, "Type")
        self.InsertColumn(2, "Instance No")
        self.InsertColumn(3, "Description")
        
    def get_descriptions(self, tag_prefix, instance):
        attributes = meta.get_attribute_list(tag_prefix)
        
        values = []
        for attribute in attributes:
            if attribute.startswith('Wells') or attribute.startswith('Images') or attribute.startswith('EventTimepoint'):
                pass
            else:
                tag = tag_prefix+'|'+attribute+'|'+instance
                values.append(meta.get_field(tag, default=''))   
        return ';  '.join(values)
            
    
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