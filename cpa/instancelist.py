import wx
import sys
import wx.lib.mixins.listctrl as listmix
from experimentsettings import *

########################################################################        
########       Popup Dialog showing all instances of settings       ####
########################################################################            
class InstanceListDialog(wx.Dialog):
    def __init__(self, parent, tag_prefix, selection_mode):
        wx.Dialog.__init__(self, parent, -1, size=(600,500), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.listctrl = InstanceListCtrl(self, tag_prefix, selection_mode)
        
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
 
        
class InstanceListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin, listmix.TextEditMixin):
    def __init__(self, parent, tag_prefix, selection_mode):
        

        '''
        tag_prefix -- the tag whose instances to list in this list control
        '''
        
        if selection_mode is True:
            wx.ListCtrl.__init__(self, parent, -1, size=(-1,400), style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING|wx.LC_HRULES)
        else:
            wx.ListCtrl.__init__(self, parent, -1, size=(-1,400), style=wx.LC_SINGLE_SEL|wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING|wx.LC_HRULES)

        self.tag_prefix = tag_prefix
        self.selected_instances = []
        
        meta = ExperimentSettings.getInstance()
        attributes = meta.get_attribute_list(self.tag_prefix)        
        #check whether there is at least one attributes
        if not attributes:
            dial = wx.MessageDialog(None, 'No Instances exists!!', 'Error', wx.OK | wx.ICON_ERROR)
            dial.ShowModal()  
            return
      
        #get all the instance
        instances = meta.get_field_instances(self.tag_prefix)
        
        self.instances = sorted(map(int, instances))
        attributename = []
        # from all the instances figure out all the attributes that can be used as column header
        for instance in self.instances:
            for attribute in sorted(attributes):
                value = meta.get_field(self.tag_prefix+'|'+attribute+'|'+str(instance))
                if value:
                    attributename += [attribute]
        columnheads = list(set(attributename))
        columnheads.insert(0, 'Instance No')
        self.columnheads = columnheads
          
        # now create the dictonary where key is the instance number and the values are data values for that instance
        attribute_data = {}        
        for row in range(len(self.instances)):
            row_values = ()
            for col in range(len(self.columnheads)):
                tag = self.tag_prefix+'|'+self.columnheads[col]+'|'+str(self.instances[row])
                if col == 0:
                    row_values += (str(self.instances[row]),)
                elif meta.get_field(tag) is not None:
                    row_values += (meta.get_field(tag),)
                else:
                    row_values += ('-',)
          
            attribute_data[self.instances[row]] = row_values
        
        self.attribute_data = attribute_data
        self.instance_index = sorted(attribute_data.keys())  #TO DO: differenciate between 1, 11, 2, 21 etc

        self.PopulateList()
        # if editing of some value is required
        #listmix.TextEditMixin.__init__(self)  
        
        # Now that the list exists we can init the other base class        
        self.itemDataMap = self.attribute_data
        self.itemIndexMap = self.attribute_data.keys()
        #self.SetItemCount(len(attribute_data))
        
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, len(self.columnheads))

    def PopulateList(self):
        
        for columnname in self.columnheads:
            ##Create the list control with the column header
            self.InsertColumn(self.columnheads.index(columnname), columnname)
            
        items = self.attribute_data.items()
    
        for key, data in items:
            index = self.InsertStringItem(sys.maxint, data[0])
            for col in range(len(self.columnheads)):
                self.SetStringItem(index, col, str(data[col]))
            self.SetItemData(index, int(key))
  
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