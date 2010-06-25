import wx
import wx.grid as  gridlib
import logging
import numpy as np
from cpatool import CPATool
from properties import Properties
import dbconnect
import imagetools
from UserDict import DictMixin

p = Properties.getInstance()
db = dbconnect.DBConnect.getInstance()

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
        self.order_by = [self.cols[0]]
        self.order_direction = 'ASC'
        self.filter = '' #'WHERE Image_Intensity_Actin_Total_intensity > 17000'
        
    def set_sort_col(self, col_index, add=False):
        col = self.cols[col_index]
        if add:
            if col in self.order_by:
                self.order_by.remove(col)
                if self.order_by == []:
                    self.order_by = [self.cols[0]]
            else:
                self.order_by += [col]
        else:
            if col in self.order_by:
                if self.order_direction == 'ASC':
                    self.order_direction = 'DESC'
                else:
                    self.order_direction = 'ASC'
            else:
                self.order_by = [col]
                
        print self.order_by
        print self.order_direction
        self.cache.clear()
        
    def get_image_key_at_row(self, row):
        return db.execute('SELECT %s FROM %s %s ORDER BY %s LIMIT %s,1'
                          %(dbconnect.UniqueImageClause(), self.table, 
                            self.filter, ','.join([c+' '+self.order_direction for c in self.order_by]), row))[0]
        
    def GetNumberRows(self):
        return db.execute('SELECT COUNT(*) FROM %s %s'%(self.table, self.filter))[0][0]
        
    def GetNumberCols(self):
        return len(self.cols)
    
    def GetColLabelValue(self, col_index):
        col = self.cols[col_index]
        if col in self.order_by:
            return col+' [%s%s]'%(len(self.order_by)>1 and self.order_by.index(col) + 1 or '', 
                                 self.order_direction=='ASC' and 'v' or '^') 
        return col

    def GetValue(self, row, col):
        if not row in self.cache:
            print "query", row
            lo = max(row - 25, 0)
            hi = row + 25
            cols = ','.join(self.cols)
            vals = db.execute('SELECT %s FROM %s %s ORDER BY %s LIMIT %s,%s'%
                              (cols, self.table, self.filter, 
                               ','.join([c+' '+self.order_direction for c in self.order_by]),
                               lo, hi-lo), 
                              silent=True)
            self.cache.update((lo+i, v) for i,v in enumerate(vals))
            # if cache exceeds 1000 entries, clip to last 500
            if len(self.cache) > 5000:
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
##        self.SetReadOnly(5, 5, True)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.on_rightclick_grid)
        self.Bind(gridlib.EVT_GRID_CMD_LABEL_LEFT_CLICK, self.on_leftclick_label)
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.on_dclick_grid)
    
    def set_source_table(self, table):
        table_base = HugeTable(table)
        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done. Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table_base, True)
        
    def on_leftclick_label(self, evt):
        if evt.ShiftDown() or evt.ControlDown() or evt.CmdDown():
            self.Table.set_sort_col(evt.Col, add=True)
        else:
            self.Table.set_sort_col(evt.Col)
        for col in range(self.Table.GetNumberCols()):
            print self.Table.GetColLabelValue(col)
            self.SetColLabelValue(col, self.Table.GetColLabelValue(col))
        self.Refresh()
        
    def on_rightclick_grid(self, evt):
        print self.GetSelectedRows()
        
    def on_dclick_grid(self, evt):
        imagetools.ShowImage(self.Table.get_image_key_at_row(evt.Row),
                             p.image_channel_colors)


class DataTable(wx.Frame, CPATool):
    def __init__(self, parent, **kwargs):
        wx.Frame.__init__(self, parent, -1, size=(640,480), **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        
        grid = HugeTableGrid(self, p.image_table)
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
        

if __name__ == '__main__':
    import sys
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)
    if p.show_load_dialog():
        frame = DataTable(None)
        frame.Show(True)
    app.MainLoop()
