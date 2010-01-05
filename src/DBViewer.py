#
# Does not yet work for object table
#

import logging
import  wx
import numpy as np
from Properties import Properties
from DBConnect import DBConnect
from UserDict import DictMixin

p = Properties.getInstance()
db = DBConnect.getInstance()

class odict(DictMixin):
    ''' Ordered dictionary '''
    def __init__(self):
        self._keys = []
        self._data = {}
        
    def __setitem__(self, key, value):
        if key not in self._data:
            self._keys.append(key)
        self._data[key] = value
        
    def __getitem__(self, key):
        return self._data[key]
    
    def __delitem__(self, key):
        del self._data[key]
        self._keys.remove(key)
        
    def keys(self):
        return list(self._keys)
    
    def copy(self):
        copyDict = odict()
        copyDict._data = self._data.copy()
        copyDict._keys = self._keys[:]
        return copyDict


class VirtualList(wx.ListCtrl):
    def __init__(self, parent, table=None):
        wx.ListCtrl.__init__(self, parent, -1, 
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)

        if table is None:
            table = p.image_table
        self.set_table(table)

#        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
#        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
#        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def set_table(self, table):
        self.table = table
        self.cache = odict()
        self.cols = db.GetColumnNames(self.table)[:100]
        for i, col in enumerate(self.cols):
            self.InsertColumn(i, col)
            self.SetColumnWidth(i, 150)
        n_rows = db.execute('SELECT COUNT(*) FROM %s'%(self.table))[0][0]
        self.SetItemCount(n_rows)
        
#    def OnItemSelected(self, event):
#        self.currentItem = event.m_itemIndex
#        print 'OnItemSelected: "%s", "%s", "%s", "%s"\n' % (self.currentItem,
#                self.GetItemText(self.currentItem),
#                self.getColumnText(self.currentItem, 1),
#                self.getColumnText(self.currentItem, 2))
#
#    def OnItemActivated(self, event):
#        self.currentItem = event.m_itemIndex
#        print "OnItemActivated: %s\nTopItem: %s\n" %(self.GetItemText(self.currentItem), self.GetTopItem())
#
#    def getColumnText(self, index, col):
#        item = self.GetItem(index, col)
#        return item.GetText()
#
#    def OnItemDeselected(self, evt):
#        print "OnItemDeselected: %s" % evt.m_itemIndex


    #---------------------------------------------------
    # These methods are callbacks for implementing the
    # "virtualness" of the list...  Normally you would
    # determine the text, attributes and/or image based
    # on values from some external data source, but for
    # this demo we'll just calculate them
    def OnGetItemText(self, row, col):
        if not '%s,%s'%(row,col) in self.cache.keys():
            cols = ','.join(self.cols)
            where = '%s>=%s AND %s<=%s'%(p.image_id, row+1, p.image_id, row+11)
            vals = np.array(db.execute('SELECT %s FROM %s WHERE %s'%(cols, self.table, where)))
            for i in range(10):
                for j in range(len(self.cols)):
                    self.cache['%s,%s'%(row+i,col+j)] = vals[i][j]
            # if cache exceeds 10000 entries, clip to last 5000
            if len(self.cache) > 10000:
                for key in self.cache.keys()[:-5000]:
                    self.cache.pop(key)
        return self.cache['%s,%s'%(row,col)]

# XXX: If uncommented, the second column is rendered empty.  Why?
#    def OnGetItemImage(self, item):
#        pass
#    
#    def OnGetItemAttr(self, item):
#        # eg: li = ListItemAttr()
#        #     li.SetBackgroundColor('blue')
#        pass


class VirtualListPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
    
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.vlist = VirtualList(self)
        sizer.Add(self.vlist, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        


def LoadProperties():
    import os
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])  # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        print 'Scatterplot requires a properties file.  Exiting.'
        sys.exit()

if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    logging.basicConfig(level=logging.DEBUG,)
    
    LoadProperties()

    f = wx.Frame(None)
    vlp = VirtualListPanel(f)
    f.Show()

    # Add menu items for changing the table
    f.SetMenuBar(wx.MenuBar())
    tableMenu = wx.Menu()
    imtblMenuItem = tableMenu.Append(-1, p.image_table)
    obtblMenuItem = tableMenu.Append(-1, p.object_table)
    f.GetMenuBar().Append(tableMenu, 'Tables')
    def setimtable(evt):
        vlp.vlist.set_table(p.image_table)
    def setobtable(evt):
        vlp.vlist.set_table(p.object_table)    
    f.Bind(wx.EVT_MENU, setimtable, imtblMenuItem)
    f.Bind(wx.EVT_MENU, setobtable, obtblMenuItem)
    
    app.MainLoop()