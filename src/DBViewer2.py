import  wx
import  wx.grid as  gridlib
import logging
import numpy as np
from properties import Properties
from dbconnect import DBConnect
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


class HugeTable(gridlib.PyGridTableBase):
    def __init__(self, table):
        gridlib.PyGridTableBase.__init__(self)
        self.table = table
        self.cache = odict()
        self.cols = db.GetColumnNames(self.table)
        
    def GetNumberRows(self):
        return db.execute('SELECT COUNT(*) FROM %s'%(self.table))[0][0]
        
    def GetNumberCols(self):
        return len(self.cols)
    
    def GetColLabelValue(self, col):
        return self.cols[col]

    def GetValue(self, row, col):
        if not row in self.cache:
            print "query", row
            lo = row
            hi = row + 20
            cols = ','.join(self.cols)
            vals = db.execute('SELECT %s FROM %s ORDER BY %s LIMIT %s,%s'%(cols, self.table, self.cols[0], lo, hi-lo))
            self.cache.update((lo+i, v) for i,v in enumerate(vals))
            # if cache exceeds 1000 entries, clip to last 500
            if len(self.cache) > 1000:
                for key in self.cache.keys()[:-500]:
                    del self.cache[key]
        return self.cache[row][col]

    def SetValue(self, row, col, value):
        print 'SetValue(%d, %d, "%s") ignored.\n' % (row, col, value)


class HugeTableGrid(gridlib.Grid):
    def __init__(self, parent, table):
        gridlib.Grid.__init__(self, parent, -1)
        self.SetRowLabelSize(0)
        self.set_source_table(table)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightDown)
    
    def set_source_table(self, table):
        table_base = HugeTable(table)
        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done.  Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table_base, True)
        

    def OnRightDown(self, event):
        print "hello"
        print self.GetSelectedRows()



class TestFrame(wx.Frame):
    def __init__(self, parent, log):
        wx.Frame.__init__(self, parent, -1, "Huge (virtual) Table Demo", size=(640,480))
        grid = HugeTableGrid(self, p.image_table)
        grid.SetReadOnly(5,5, True)
        self.SetMenuBar(wx.MenuBar())
        tableMenu = wx.Menu()
        imtblMenuItem = tableMenu.Append(-1, p.image_table)
        obtblMenuItem = tableMenu.Append(-1, p.object_table)
        self.GetMenuBar().Append(tableMenu, 'Tables')
        def setimtable(evt):
            grid.set_source_table(p.image_table)
        def setobtable(evt):
            grid.set_source_table(p.object_table)
        self.Bind(wx.EVT_MENU, setimtable, imtblMenuItem)
        self.Bind(wx.EVT_MENU, setobtable, obtblMenuItem)


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
        

if __name__ == '__main__':
    import sys
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)
    LoadProperties()
    frame = TestFrame(None, sys.stdout)
    frame.Show(True)
    app.MainLoop()


#---------------------------------------------------------------------------
