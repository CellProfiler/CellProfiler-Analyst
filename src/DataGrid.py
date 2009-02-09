import wx
import wx.grid
import numpy
import ImageTools
from DataModel import DataModel
from sys import stderr
import os
import csv

dm = DataModel.getInstance()


IMAGE_GROUPING = 'Image'

class HugeTable(wx.grid.PyGridTableBase):

    def __init__(self, data, col_labels, row_label_indices):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.col_labels = col_labels
        self.row_label_indices = row_label_indices
    
    def GetNumberRows(self):
        return self.data.shape[0]

    def GetNumberCols(self):
        return self.data.shape[1]

    def GetColLabelValue(self, col):
        return self.col_labels[col]

    def GetRowLabelValue(self, row):
        return " : ".join([str(v) for v in self.data[row, self.row_label_indices]])

    def IsEmptyCell(self, row, col):
        return False

    def GetValue(self, row, col):
        return str(self.data[row, col])

    def SetValue(self, row, col, value):
        # ignore
        pass


class HugeTableGrid(wx.grid.Grid):
    def __init__(self, parent, data, col_labels, row_label_indices):
        wx.grid.Grid.__init__(self, parent, -1)

        table = HugeTable(data, col_labels, row_label_indices)
        self.DisableCellEditControl()
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)

        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done.  Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

    def OnSelectCell(self, evt):
        return # prevent selection


class DataGrid(wx.Frame):

    """
    A frame with a grid inside of it.
    
    This grid is specifically designed to hold per-image or grouped
    per-image data in each row.  Double-clicking a row label will
    launch an image viewer for that image or images.  Right-clicking a
    row label will display a popup menu of images to select for
    viewing.  Clicking on a column label will sort that column in
    ascending then descending order.

    """
    
    def __init__(self, data, labels, grouping=IMAGE_GROUPING,
                 groupIDIndices=[0], chMap=None, parent=None,
                 title='Data Grid'):
        """
        Initialize the datagrid.

        Arguments:
        data -- the grid as a numpy array
        labels -- text labels for each column

        Keyword arguments:
        grouping -- group name string, e.g., "Wells"
        groupIDIndices -- column indexes for group IDs
        chMap -- channel-to-color map for ImageViewer, or None to disable
        parent -- wx parent window
        title -- 
        
        # is launched.  If None, no images will be displayed.

        """
        wx.Frame.__init__(self, parent, id=-1, title=title)
        
        self.data = data
        self.grid = HugeTableGrid(self, data, labels, groupIDIndices)
        # The order of the rows displayed.
        self.order = numpy.arange(data.shape[0])
        self.labels = labels
        self.grouping = grouping
        self.groupIDIndices = groupIDIndices
        self.chMap = chMap
        # Index of the current column being sorted by.
        self.sortcol = -1
        
        assert len(labels) == data.shape[1], \
               "DataGrid.__init__: Number of column labels does not match " \
               "the number of columns in data."
        
        self.filemenu = wx.Menu()
        self.saveCSVMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=wx.NewId(),
                        text='Save data to CSV',
                        help='Saves data as comma separated values.')
        self.filemenu.AppendItem(self.saveCSVMenuItem)
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.menuBar.Append(self.filemenu, 'File')

        self.SetColumnLabels(self.labels)
        self.SetSize((800,500))
        self.SetSize((self.grid.Size[0], min(self.grid.Size[1], 500)+22))
        
        self.Bind(wx.EVT_MENU, self.OnSaveCSV, self.saveCSVMenuItem)
        self.grid.Bind(wx.EVT_KEY_UP, self.OnKey)
        wx.grid.EVT_GRID_LABEL_LEFT_CLICK(self.grid, self.OnLabelClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(self.grid, self.OnLabelRightClick)
        wx.grid.EVT_GRID_LABEL_LEFT_DCLICK(self.grid, self.OnLabelDClick)
        
        self.grid.EnableEditing(False)
        self.grid.SetCellHighlightPenWidth(0)


        
    def OnKey(self, evt):
        keycode = evt.GetKeyCode()
        if evt.ControlDown() or evt.CmdDown():
            if evt.GetKeyCode() == ord('W'):
                self.Close()
        evt.Skip()
        

    def OnSaveCSV(self, evt):
        defaultFileName = 'My_Enrichment_Data.csv'
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=os.getcwd(),
                                   defaultFile=defaultFileName,
                                   wildcard='csv',
                                   style=(wx.SAVE | wx.FD_OVERWRITE_PROMPT |
                                          wx.FD_CHANGE_DIR))
        if saveDialog.ShowModal()==wx.ID_OK:
            self.SaveCSV(saveDialog.GetPath())
        
    def SaveCSV(self, filename):
        f = open(filename, 'w')
        w = csv.writer(f)
        w.writerow(self.labels)
        for row in self.data:
            w.writerow(row)
        f.close()
        print 'Table saved to',filename
    
    
    def OnLabelClick(self, evt):
        if evt.Col >= 0:
            self.SortGridByCol(evt.Col)
        evt.Skip()
        
    
    def OnLabelDClick(self, evt):
        if self.chMap:
            key = tuple([self.data[evt.Row,idx]
                         for idx in self.groupIDIndices])
            if evt.Row >= 0:
                if self.grouping == IMAGE_GROUPING:
                    ImageTools.ShowImage(key, self.chMap, parent=self)
                else:
                    imKeys = dm.GetImagesInGroup(self.grouping, tuple(key))
                    for imKey in imKeys:
                        ImageTools.ShowImage(imKey, self.chMap, parent=self)
            else:
                self.OnLabelClick(evt)
            
            
    def OnLabelRightClick(self, evt):
        if evt.Row >= 0:
            key = tuple([self.data[evt.Row,idx]
                         for idx in self.groupIDIndices])
            if self.grouping == IMAGE_GROUPING:   
                self.ShowPopupMenu([key], evt.GetPosition())
            else:
                imKeys = dm.GetImagesInGroup(self.grouping, tuple(key))
                self.ShowPopupMenu(imKeys, evt.GetPosition())
            
            
    def ShowPopupMenu(self, items, pos):
        self.popupItemById = {}
        popupMenu = wx.Menu()
        popupMenu.SetTitle('Show Image')
        for item in items:
            id = wx.NewId()
            self.popupItemById[id] = item
            popupMenu.Append(id,str(item))
        popupMenu.Bind(wx.EVT_MENU, self.OnSelectFromPopupMenu)
        self.PopupMenu(popupMenu, pos)
            
    
    def OnSelectFromPopupMenu(self, evt):
        """Handles selections from the popup menu."""
        if self.chMap:
            imKey = self.popupItemById[evt.GetId()]
            ImageTools.ShowImage(imKey, self.chMap, parent=self)

 
    def SortGridByCol(self, colIndex):
        # If this column is already sorted, flip it
        if self.sortcol == colIndex:
            self.order = numpy.arange(self.data.shape[0])[::-1]
        # If this column hasn't been sorted yet, then sort descending
        else:
            self.order = self.data[:,colIndex].argsort()
            
        self.sortcol = colIndex
        self.data[:] = self.data[self.order].copy()
        self.Refresh()
    
    def SetColumnLabels(self, labels):
        for i, label in enumerate(labels):
            self.grid.SetColLabelValue(i, label)


if __name__ == "__main__":
    classes = ['a', 'b']
    hits = numpy.array([['key 0000000',10,20,-30,40.123456789],['key 1',11,21,31,41.1],['key 2',0,-22,32,42.2],['key 3',13,-3,33,43.3],['key 4',14,24,4,44.4],['key 5',5,5,5,5.12345]], dtype=object)
    order = numpy.array([4,3,1,2,0])
    labels = ['key', 'count A' , 'count McLongtitle #1\n B' , 'P a' , 'P b' ]
        
    app = wx.PySimpleApp()
    grid = DataGrid( hits, labels, groupIDIndices=[0,1] )
    grid.Show()

    app.MainLoop()

