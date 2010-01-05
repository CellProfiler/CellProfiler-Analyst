import logging
import wx
import numpy as np
from Properties import Properties
from DBConnect import *
from UserDict import DictMixin
import ImageTools

p = Properties.getInstance()
db = DBConnect.getInstance()

class ImageListCtrl(wx.ListCtrl):
    def __init__(self, parent, imkeys):
        wx.ListCtrl.__init__(self, parent, -1, 
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)

        self.set_key_list(imkeys)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def set_key_list(self, imkeys):
        self.imkeys = imkeys
        self.cols = (p.table_id or []) + [p.image_id, p.plate_id, p.well_id]

        if len(self.imkeys) > 0:
            self.data = np.array(db.execute('SELECT %s, %s, %s FROM %s WHERE %s'%(
                                    UniqueImageClause(), 
                                    p.plate_id, p.well_id,
                                    p.image_table,
                                    GetWhereClauseForImages(imkeys))))
        else:
            self.data = []

        for i, col in enumerate(self.cols):
           self.InsertColumn(i, col)
           self.SetColumnWidth(i, 150)
        self.SetItemCount(len(imkeys))

    def OnItemActivated(self, event):
        imkey = self.imkeys[event.m_itemIndex]
        f = ImageTools.ShowImage(tuple(imkey), p.image_channel_colors, self.GrandParent or self.Parent)
        f.Raise()

    def OnGetItemText(self, row, col):
        return self.data[row][col]


class ImageListFrame(wx.Frame):
    def __init__(self, parent, imkeys, **kwargs):
        wx.Frame.__init__(self, parent, -1, **kwargs)
    
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.imlist = ImageListCtrl(self, imkeys)
        sizer.Add(self.imlist, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
        
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)
    
    if not p.show_load_dialog():
        print 'Props file required'
        sys.exit()
    
    ilf = ImageListFrame(None, db.execute('SELECT %s from %s'%(UniqueImageClause(), p.image_table)))
    ilf.Show()
    
    app.MainLoop()
    