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
        
    def set_table(self, table):
        print 'set table'
        self.table = table
        self.cache = odict()
        self.cols = db.GetColumnNames(self.table)
        self.Freeze()
        self.ClearAll()
        n_rows = db.execute('SELECT COUNT(*) FROM %s'%(self.table))[0][0]
        self.SetItemCount(n_rows)
        for i, col in enumerate(self.cols):
            self.InsertColumn(i, col)
            self.SetColumnWidth(i, 100)
        self.Thaw()
        self.Refresh()

    #---------------------------------------------------
    # These methods are callbacks for implementing the
    # "virtualness" of the list...  Normally you would
    # determine the text, attributes and/or image based
    # on values from some external data source, but for
    # this demo we'll just calculate them
    def OnGetItemText(self, row, col):
        if not row in self.cache:
            print "query", row
            lo = row - 10
            hi = row + 10
            cols = ','.join(self.cols)
            where = '%s BETWEEN %s AND %s'%(p.image_id, lo, hi)
            vals = db.execute('SELECT %s, %s FROM %s WHERE %s'%(p.image_id, cols, self.table, where))
            self.cache.update((v[0] - 1, v[1:]) for v in vals)
            # if cache exceeds 10000 entries, clip to last 5000
            if len(self.cache) > 10000:
                for key in self.cache.keys()[:-5000]:
                    del self.cache[key]
        return self.cache[row][col]



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

    frame = wx.Frame(None)
    vlp = VirtualListPanel(frame)
    frame.Show()

    # Add menu items for changing the table
    frame.SetMenuBar(wx.MenuBar())
    tableMenu = wx.Menu()
    imtblMenuItem = tableMenu.Append(-1, p.image_table)
    obtblMenuItem = tableMenu.Append(-1, p.object_table)
    frame.GetMenuBar().Append(tableMenu, 'Tables')
    def setimtable(evt):
        vlp.vlist.set_table(p.image_table)
    def setobtable(evt):
        vlp.vlist.set_table(p.object_table)
    frame.Bind(wx.EVT_MENU, setimtable, imtblMenuItem)
    frame.Bind(wx.EVT_MENU, setobtable, obtblMenuItem)
    
    app.MainLoop()
