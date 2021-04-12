
import logging
import wx
import numpy as np
from .properties import Properties
from .dbconnect import *
from . import imagetools

p = Properties()
db = DBConnect()

class ImageListCtrl(wx.ListCtrl):
    def __init__(self, parent, imkeys):
        wx.ListCtrl.__init__(self, parent, -1, 
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)

        self.set_key_list(imkeys)

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def set_key_list(self, imkeys):
        self.imkeys = imkeys

        if len(self.imkeys) > 0:
            columns_of_interest = well_key_columns(p.image_table)
            if len(columns_of_interest) > 0:
                columns_of_interest = ','+','.join(columns_of_interest)
                self.data = db.execute('SELECT %s%s FROM %s WHERE %s'%(
                            UniqueImageClause(), 
                            columns_of_interest,
                            p.image_table,
                            GetWhereClauseForImages(imkeys)))
                self.cols = image_key_columns() + well_key_columns()
            else:
                self.data = np.array(self.imkeys)
                self.cols = image_key_columns() 
        else:
            self.data = []
            self.cols = []

        self.data.sort()

        for i, col in enumerate(self.cols):
           self.InsertColumn(i, col)
           self.SetColumnWidth(i, 150)
        self.SetItemCount(len(imkeys))

    def OnItemActivated(self, event):
        imkey = self.imkeys[event.m_itemIndex]
        f = imagetools.ShowImage(tuple(imkey), p.image_channel_colors, self.GrandParent or self.Parent)
        f.Raise()

    def OnGetItemText(self, row, col):
        return str(self.data[row][col])


class ImageListFrame(wx.Frame):
    def __init__(self, parent, imkeys, **kwargs):
        wx.Frame.__init__(self, parent, -1, **kwargs)
    
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.imlist = ImageListCtrl(self, imkeys)
        sizer.Add(self.imlist, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
        
        
if __name__ == "__main__":
    app = wx.App()
    logging.basicConfig(level=logging.DEBUG,)
    
    if not p.show_load_dialog():
        print('Props file required')
        sys.exit()
    
    ilf = ImageListFrame(None, db.execute('SELECT %s from %s'%(UniqueImageClause(), p.image_table)))
    ilf.Show()
    
    app.MainLoop()
    