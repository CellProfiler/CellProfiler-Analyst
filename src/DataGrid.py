# -*- Encoding: utf-8 -*-
import wx
import wx.grid
import numpy as np
import ImageTools
from DataModel import DataModel
from DBConnect import DBConnect
from Properties import Properties
from sys import stderr
from tempfile import gettempdir
from time import ctime, time
import os
import csv
import weakref

dm = DataModel.getInstance()
db = DBConnect.getInstance()
p = Properties.getInstance()

class HugeTable(wx.grid.PyGridTableBase):
    '''
    This class abstracts the underlying data and labels used in the DataGrid.
    The data is stored as a 2d numpy array. The data itself never changes but
    may be reordered or subsetted by modifying col_order and row_order.
    Example: col_order==[4,3,1,0] indicates that the columns will be displayed
        in reverse order and that column 2 will not be displayed.
        Similarly, row_order==[0,2,4,6,8,..,N] would show only even rows.
    '''

    def __init__(self, grid, data, col_labels, key_col_indices):
        '''
        Arguments:
        grid -- parent grid
        data -- the grid as a np object array
        col_labels -- text labels for each column
        key_col_indices -- column indexes for group IDs
        '''
        wx.grid.PyGridTableBase.__init__(self)
        
        assert len(col_labels) == data.shape[1], "DataGrid.__init__: Number of column labels does not match the number of columns in data."
        self.sortcol      =  -1   # column index being sorted
        self.grid         =  grid
        self.data         =  data
        self.ordered_data = self.data
        self.col_labels   =  np.array(col_labels)
        self.row_order    =  np.arange(self.data.shape[0])
        self.col_order    =  np.arange(self.data.shape[1])
        self.key_col_indices  =  key_col_indices
    
    def GetNumberRows(self):
        return self.ordered_data.shape[0]

    def GetNumberCols(self):
        return self.ordered_data.shape[1]

    def GetColLabelValue(self, col):
        return self.col_labels[self.col_order][col]

    def GetRowLabelValue(self, row):
        return ", ".join([str(v) for v in self.GetKeyForRow(row)])
    
    def GetKeyForRow(self, row):
        return tuple([v for v in self.data[self.row_order[row],self.key_col_indices]])
        
    def IsEmptyCell(self, row, col):
        return False

    def GetValue(self, row, col):
        return self.ordered_data[row,col]

    def SetValue(self, row, col, value):
        # ignore
        pass
    
    def GetColValues(self, col):
        return self.ordered_data[:,col]
    
    def GetRowValues(self, row):
        return self.ordered_data[row,:]
    
    def HideCol(self, index):
        ''' index -- the raw data index of the column to show '''
        cols = set(self.col_order)
        cols.remove(index)
        self.col_order = np.array(list(cols))
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
        self.ResetView()
        
    def ShowCol(self, index):
        ''' index -- the raw data index of the column to show '''
        cols = self.col_order.tolist()
        cols += [index]
        cols.sort()
        self.col_order = np.array(cols)
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
        self.ResetView()
    
    def SortByCol(self, colIndex):
        if self.sortcol == colIndex:
            # If this column is already sorted, flip it
            self.row_order = self.row_order[::-1]
        else:
            # If this column hasn't been sorted yet, then sort descending
            self.row_order = self.data[:,self.col_order][:,colIndex].argsort()
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
        self.sortcol = colIndex
        self.grid.Refresh()
    
    def ResetView(self):
        """ Trim/extend the control's rows and update all values """
        self.grid.BeginBatch()
        for current, new, delmsg, addmsg in [
                (self.grid.GetNumberRows(), self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
                (self.grid.GetNumberCols(), self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),]:
            if new < current:
                msg = wx.grid.GridTableMessage(self, delmsg, new, current-new)
                self.grid.ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(self, addmsg, new-current)
                self.grid.ProcessTableMessage(msg)
        self.UpdateValues()
        self.grid.EndBatch()

        # The scroll bars aren't resized (at least on windows)
        # Jiggling the size of the window rescales the scrollbars
        h,w = self.grid.GetSize()
        self.grid.SetSize((h+1, w))
        self.grid.SetSize((h, w))
        self.grid.Refresh()

    def UpdateValues( self ):
        """Update all displayed values"""
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.grid.ProcessTableMessage(msg)



class HugeTableGrid(wx.grid.Grid):
    
    def __init__(self, parent, data, col_labels, key_col_indices, grouping="Image", chMap=None):
        wx.grid.Grid.__init__(self, parent, -1)

        table = HugeTable(self, data, col_labels, key_col_indices)
        
        self.selectedColumns = set()
        # Index of the current column being sorted by.
        self.grouping = grouping
        self.chMap = chMap or p.image_channel_colors

        self.DisableCellEditControl()
        self.EnableEditing(False)
        self.SetCellHighlightPenWidth(0)

        # The second parameter means that the grid is to take
        # ownership of the table and will destroy it when done.
        # Otherwise you would need to keep a reference to it and call
        # it's Destroy method later.
        self.SetTable(table, True)
        # Avoid self.AutoSize() because it hangs on large tables.
        self.SetSelectionMode(self.wxGridSelectColumns)
        self.SetColumnLabels(self.GetTable().col_labels)
        
        wx.grid.EVT_GRID_SELECT_CELL(self, self.OnSelectCell)
        wx.grid.EVT_GRID_LABEL_LEFT_CLICK(self, self.OnLabelClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(self, self.OnLabelRightClick)
        wx.grid.EVT_GRID_LABEL_LEFT_DCLICK(self, self.OnLabelDClick)
        wx.grid.EVT_GRID_RANGE_SELECT(self, self.OnSelectedRange)

    def OnSelectCell(self, evt):
        # Prevent selection.
        evt.Skip()
    
    def SetTable( self, object, *attributes ):
            self.tableRef = weakref.ref( object )
            return wx.grid.Grid.SetTable( self, object, *attributes )
    
    def GetTable(self):
            return self.tableRef()

    def OnSelectedRange(self, evt):
        cols = set(range(evt.GetLeftCol(), evt.GetRightCol() + 1))
        # update the selection
        if evt.Selecting():
            self.selectedColumns.update(cols)
        else:
            self.selectedColumns.difference_update(cols)
        try:
            # try to summarize selected columns
            n, m = self.GetTable().GetNumberRows(), len(self.selectedColumns)
            block = np.empty((n, m))
            for k, j in enumerate(self.selectedColumns):
                block[:,k] = self.GetTable().GetColValues(j)
            self.GetParent().SetStatusText(u"Sum: %f — Mean: %f — Std: %f" %
                                           (block.sum(), block.mean(), block.std()))
        except:
            self.GetParent().SetStatusText("Cannot summarize columns.")
            
    def OnLabelClick(self, evt):
        if evt.Col >= 0:
            self.GetTable().SortByCol(evt.Col)
        evt.Skip()
    
    def OnLabelDClick(self, evt):
        if evt.Row >= 0:
            key = self.GetTable().GetKeyForRow(evt.Row)
            if self.grouping=='Image':
                ImageTools.ShowImage(key, self.chMap, parent=self)
            else:
                imKeys = dm.GetImagesInGroup(self.grouping, tuple(key))
                for imKey in imKeys:
                    ImageTools.ShowImage(imKey, self.chMap, parent=self)
        else:
            self.OnLabelClick(evt)
            
    def OnLabelRightClick(self, evt):
        if evt.Row >= 0:
            key = self.GetTable().GetKeyForRow(evt.Row)
            if self.grouping=='Image':
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
    
    def SetColumnLabels(self, labels):
        for i, label in enumerate(labels):
            self.SetColLabelValue(i, label)


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
    
    def __init__(self, data, labels, grouping='Image',
                 key_col_indices=[0], chMap=None, parent=None,
                 title='Data Grid'):
        """
        Initialize the datagrid.

        Arguments:
        data -- the grid as a np object array
        labels -- text labels for each column

        Keyword arguments:
        grouping -- group name string, e.g., "Wells"
        key_col_indices -- column indexes for group IDs
        chMap -- channel-to-color map for ImageViewer, or None to disable
        parent -- wx parent window
        title -- 
        
        # is launched.  If None, no images will be displayed.

        """
        wx.Frame.__init__(self, parent, id=-1, title=title)
        
        self.grid = HugeTableGrid(self, data, labels, key_col_indices, grouping, chMap)
        
        # Autosave enrichments to temp dir just in case.
        print 'Auto saving data...'
        filename = gettempdir()+os.sep+'CPA_enrichments_'+ctime().replace(' ','_').replace(':','-')+'.csv'
        self.SaveCSV(filename, self.grid.GetTable().data, self.grid.GetTable().col_labels)
                
        self.filemenu = wx.Menu()
        self.saveCSVMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=wx.NewId(),
                        text='Save data to CSV',
                        help='Saves data as comma separated values.')
        self.savePerImageCountsToCSVMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=wx.NewId(),
                        text='Save per-image counts to CSV',
                        help='Saves per-image phenotype counts as comma separated values.')
        self.filemenu.AppendItem(self.saveCSVMenuItem)
        self.filemenu.AppendItem(self.savePerImageCountsToCSVMenuItem)
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)
        self.GetMenuBar().Append(self.filemenu, 'File')
        self.CreateColumnMenu()
        self.CreateStatusBar()

        self.SetSize((800,500))
        self.SetSize((self.grid.Size[0], min(self.grid.Size[1], 500)+22))
        
        self.Bind(wx.EVT_MENU, self.OnSaveCSV, self.saveCSVMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSavePerImageCountsToCSV, self.savePerImageCountsToCSVMenuItem)
        wx.EVT_SIZE(self, self.OnSize)

    def CreateColumnMenu(self):
        ''' Create color-selection menus for each channel. '''
        self.colmenu = wx.Menu()
        self.cols_by_id = {}
        for i, column in enumerate(self.grid.GetTable().col_labels):
            id = wx.NewId()
            self.cols_by_id[id] = i
            item = self.colmenu.AppendCheckItem(id, column)
            item.Check()
            self.Bind(wx.EVT_MENU, self.OnToggleCol, item)
        self.GetMenuBar().Append(self.colmenu, "Columns") 

    def OnSize(self, evt):
        # Hack: subtract 25 in order to avoid spurious scrollbar.
        cw = (evt.GetSize()[0]-25) / (self.grid.GetTable().GetNumberCols()+1)
        self.grid.SetDefaultColSize(cw, True)
        self.grid.SetRowLabelSize(cw)
        evt.Skip()
    
    def OnToggleCol(self, evt):
        colIdx = self.cols_by_id[evt.GetId()]
        if evt.Checked():
            self.grid.GetTable().ShowCol(colIdx)
        else:
            self.grid.GetTable().HideCol(colIdx)

    def OnSaveCSV(self, evt):
        defaultFileName = 'My_Enrichment_Data.csv'
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=os.getcwd(),
                                   defaultFile=defaultFileName,
                                   wildcard='csv|*',
                                   style=(wx.SAVE | wx.FD_OVERWRITE_PROMPT |
                                          wx.FD_CHANGE_DIR))
        if saveDialog.ShowModal()==wx.ID_OK:
            self.SaveCSV(saveDialog.GetPath(), self.grid.GetTable().ordered_data, self.grid.GetTable().col_labels)
        saveDialog.Destroy()
    
    def OnSavePerImageCountsToCSV(self, evt):        
        defaultFileName = 'Per_Image_Counts.csv'
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=os.getcwd(),
                                   defaultFile=defaultFileName,
                                   wildcard='csv|*',
                                   style=(wx.SAVE | wx.FD_OVERWRITE_PROMPT |
                                          wx.FD_CHANGE_DIR))
        if saveDialog.ShowModal()==wx.ID_OK:
            colHeaders = []
            pos = 1
            if p.table_id:
                colHeaders += [p.table_id]
                pos = 2
            colHeaders += [p.image_id, p.well_id, p.plate_id]
            colHeaders += ['count_'+bin.label for bin in self.GetParent().classBins]
            data = list(self.GetParent().keysAndCounts)
            for row in data:
                if p.table_id:
                    where = '%s=%s AND %s=%s'%(p.table_id, row[0], p.image_id, row[1])
                else:
                    where = '%s=%s'%(p.image_id, row[0])
                db.Execute('SELECT %s, %s FROM %s WHERE %s'%(p.well_id, p.plate_id, p.image_table, where), silent=True)
                well, plate = db.GetResultsAsList()[0]
                row.insert(pos, well)
                row.insert(pos+1, plate)
            self.SaveCSV(saveDialog.GetPath(), data, colHeaders)
        saveDialog.Destroy()

    def SaveCSV(self, filename, data, colLabels):
        f = open(filename, 'wb')
        w = csv.writer(f)
        w.writerow(colLabels)
        for row in data:
            w.writerow(row)
        f.close()
        print 'Table saved to',filename



if __name__ == "__main__":
    classes = ['a', 'b']
    hits = np.array([['key 0',10,20,-30,40.123456789],['key 1',11,21,31,41.1],['key 2',0,-22,32,42.2],['key 3',13,-3,33,43.3],['key 4',14,24,4,44.4],['key 5',5,5,5,5.12345]]*10, dtype=object)
    labels = ['key', 'count-A' , 'count McLongtitle #1\n B' , 'P(a)' , 'P(b)' ]
    
    app = wx.PySimpleApp()
    grid = DataGrid(hits, labels, key_col_indices=[0,1])
    grid.Show()

    app.MainLoop()

