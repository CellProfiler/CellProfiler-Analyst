# -*- Encoding: utf-8 -*-

from cpa import dbconnect
from cpa.dbconnect import DBConnect
from cpa.guiutils import create_status_bar
from .datamodel import DataModel
from .properties import Properties
from tempfile import gettempdir
from time import ctime
from . import imagetools
import csv
import logging
import numpy as np
import os
import weakref
import wx
import wx.grid

dm = DataModel()
db = DBConnect()
p = Properties()

ID_LOAD_CSV = wx.NewId()
ID_SAVE_CSV = wx.NewId()
ID_EXIT = wx.NewId()

DO_NOT_LINK_TO_IMAGES = 'Do not link to images'
ROW_LABEL_SIZE = 30

# Icon to be used for row headers (difficult to implement) 
#img_icon = PyEmbeddedImage('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')

class HugeTable(wx.grid.GridTableBase):
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
        wx.grid.GridTableBase.__init__(self)
        
        assert len(col_labels) == data.shape[1], "DataGrid.__init__: Number of column labels does not match the number of columns in data."
        self.sortdir      =  1    # sort direction (1=descending, -1=descending)
        self.sortcols     =  []   # column indices being sorted (in order)
        self.grid         =  grid
        self.data         =  data
        self.ordered_data =  self.data
        self.col_labels   =  np.array(col_labels)
        self.row_order    =  np.arange(self.data.shape[0])
        self.col_order    =  np.arange(self.data.shape[1])
        self.key_col_indices  =  key_col_indices
    
    def GetNumberRows(self):
        return self.ordered_data.shape[0]

    def GetNumberCols(self):
        return self.ordered_data.shape[1]

    def GetColLabelValue(self, col):
        col_label = self.col_labels[self.col_order][col]
        if len(self.sortcols) > 1:
            try:
                col_label += ' ['+str(self.sortcols.index(col)+1)
                if self.sortdir > 0:
                    col_label += 'v]'
                else:
                    col_label += '^]'
            except: pass
        return col_label
    
    def GetOrderedColLabels(self):
        return self.col_labels[self.col_order]

    def GetRowLabelValue(self, row):
        return '*'
#        return ", ".join([str(v) for v in self.GetKeyForRow(row)])
    
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
        if len(self.sortcols)>0 and colIndex in self.sortcols:
            # If this column is already sorted, flip it
            self.row_order = self.row_order[::-1]
            self.sortdir = -self.sortdir
        else:
            self.sortdir = 1
            self.sortcols = [colIndex]
            # If this column hasn't been sorted yet, then sort descending
            self.row_order = np.lexsort(self.data[:,self.col_order][:,self.sortcols[::-1]].T.tolist())
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
        self.grid.Refresh()
        
    def AddSortCol(self, colIndex):
        if len(self.sortcols)>0 and colIndex in self.sortcols:
            self.sortcols.remove(colIndex)
        else:
            self.sortcols += [colIndex]
        if self.sortcols==[]:
            # if all sort columns have been toggled off, reset row_order
            self.row_order = np.arange(self.data.shape[0])
        else:
            self.row_order = np.lexsort(self.data[:,self.sortcols[::-1]].T.tolist())
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
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
    '''
    Grid is specifically designed to hold per-image or grouped
    per-image data in each row.  Double-clicking a row label will
    launch an image viewer for that image or images.  Right-clicking a
    row label will display a popup menu of images to select for
    viewing.  Clicking on a column label will sort that column in
    ascending then descending order.
    '''
    
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
        self.SetSelectionMode(self.GridSelectColumns)
        self.SetColumnLabels(self.GetTable().col_labels)
        # Help prevent spurious horizontal scrollbar
        self.SetMargins(0-wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X),
                        0-wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y))
        self.SetRowLabelSize(ROW_LABEL_SIZE)
        
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
            self.GetParent().SetStatusText("Sum: %f — Mean: %f — Std: %f" %
                                           (block.sum(), block.mean(), block.std()))
        except:
            self.GetParent().SetStatusText("Cannot summarize columns.")
            
    def OnLabelClick(self, evt):
        if evt.AltDown():
            column = self.Table.col_order[evt.Col]
            # Alt+Click: hide this column
            self.Table.HideCol(column)
            self.Parent.colmenu.GetMenuItems()[column].Check(False)
            self.Parent.RescaleGrid()
            return
        if evt.Col >= 0:
            if evt.ShiftDown() or evt.ControlDown() or evt.CmdDown():
                # Shift+Click: Add this column to list of sort-columns
                self.GetTable().AddSortCol(evt.Col)
            else:
                # Click: Sort by this column
                self.GetTable().SortByCol(evt.Col)
        evt.Skip()
    
    def OnLabelDClick(self, evt):
        if evt.Row >= 0:
            key = self.GetTable().GetKeyForRow(evt.Row)
            if self.grouping=='Image':
                imagetools.ShowImage(key, self.chMap, parent=self)
            else:
                imKeys = dm.GetImagesInGroup(self.grouping, tuple(key))
                for imKey in imKeys:
                    imagetools.ShowImage(imKey, self.chMap, parent=self)
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
            imagetools.ShowImage(imKey, self.chMap, parent=self)
    
    def SetColumnLabels(self, labels):
        for i, label in enumerate(labels):
            self.SetColLabelValue(i, label)


class DataGrid(wx.Frame):
    '''
    A frame with a grid inside of it for displaying grouped .
    '''
    
    def __init__(self, data=None, labels=None, grouping='Image',
                 key_col_indices=[0], chMap=None, parent=None,
                 title='Data Table', autosave=True):
        '''
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
        '''
        
        wx.Frame.__init__(self, parent, id=-1, title=title)
        self.SetName('DataTable')
        
        self.grid = None
        self.file = None
        if not (data is None or labels is None):
            self.grid = HugeTableGrid(self, data, labels, key_col_indices, grouping, chMap)
        
        if autosave and self.grid:
            # Autosave enrichments to temp dir
            logging.info('Auto saving data...')
            filename = gettempdir()+os.sep+'CPA_enrichments_'+ctime().replace(' ','_').replace(':','-')+'.csv'
            self.SaveCSV(filename, self.grid.GetTable().data, self.grid.GetTable().col_labels)
                
        self.filemenu = wx.Menu()
        self.loadCSVMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=ID_LOAD_CSV,
                        text='Load data from CSV\tCtrl+O',
                        helpString='Load data from CSV.')
        self.saveCSVMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=ID_SAVE_CSV,
                        text='Save data to CSV\tCtrl+S',
                        helpString='Saves data as comma separated values.')
        self.savePerImageCountsToCSVMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=-1,
                        text='Save per-image counts to CSV',
                        helpString='Saves per-image phenotype counts as comma separated values.')
        self.exitMenuItem = \
            wx.MenuItem(parentMenu=self.filemenu, id=ID_EXIT,
                        text='Exit\tCtrl+Q',
                        helpString='Close the Data Table')
        self.filemenu.Append(self.loadCSVMenuItem)
        self.filemenu.Append(self.saveCSVMenuItem)
        self.filemenu.Append(self.savePerImageCountsToCSVMenuItem)
        self.filemenu.AppendSeparator()
        self.filemenu.Append(self.exitMenuItem)
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)
        self.GetMenuBar().Append(self.filemenu, 'File')
        self.dbmenu = wx.Menu()
        self.writeToTempTableMenuItem = \
            wx.MenuItem(parentMenu=self.dbmenu, id=-1,
                        text='Write temporary table for Plate Viewer',
                        helpString='Writes this table to a temporary table in your database so Plate Viewer can access it.')
        self.dbmenu.Append(self.writeToTempTableMenuItem)
        self.GetMenuBar().Append(self.dbmenu, 'Database')
        if self.grid:
            self.CreateColumnMenu()
        self.status_bar = create_status_bar(self)

        self.SetSize((800,500))
        if self.grid:
            self.grid.SetSize(self.Size)
        
        self.Bind(wx.EVT_MENU, self.OnSaveCSV, self.saveCSVMenuItem)
        self.Bind(wx.EVT_MENU, self.OnLoadCSV, self.loadCSVMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSavePerImageCountsToCSV, self.savePerImageCountsToCSVMenuItem)
        self.Bind(wx.EVT_MENU, self.OnWriteTempTableToDB, self.writeToTempTableMenuItem)
        self.Bind(wx.EVT_MENU, self.OnExit, self.exitMenuItem)
        self.Bind(wx.EVT_SIZE, self.OnSize, self)
        
        accelerator_table = wx.AcceleratorTable([(wx.ACCEL_CTRL,ord('O'),ID_LOAD_CSV),
                                                 (wx.ACCEL_CTRL,ord('S'),ID_SAVE_CSV),
                                                 (wx.ACCEL_CTRL,ord('Q'),ID_EXIT),])
        self.SetAcceleratorTable(accelerator_table)

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
        
    def OnExit(self, evt):
        if self.file is None:
            dlg = wx.MessageDialog(self, 'Do you want to save this table before quitting?', 'Data Not Saved', wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                if self.PromptToSaveCSV()==wx.ID_CANCEL:
                    return
            elif response == wx.ID_CANCEL:
                return
        self.Destroy()

    def OnSize(self, evt):
        if not self.grid:
            return
        # HACK CITY: Trying to fix spurious horizontal scrollbar
        adjustment = ROW_LABEL_SIZE
        if self.grid.GetScrollRange(wx.VERTICAL)>0:
            adjustment = wx.SYS_VSCROLL_ARROW_X + 12
        cw = (evt.GetSize()[0] - adjustment) // self.grid.GetTable().GetNumberCols()
        self.grid.SetDefaultColSize(cw, True)
        evt.Skip()
        
    def RescaleGrid(self):
        # Hack: resize window so the grid resizes to fit
        self.Size = self.Size+(1,1)
        self.Size = self.Size-(1,1)
    
    def OnToggleCol(self, evt):
        colIdx = self.cols_by_id[evt.GetId()]
        if evt.Checked():
            self.grid.GetTable().ShowCol(colIdx)
        else:
            self.grid.GetTable().HideCol(colIdx)
        self.RescaleGrid()

    def OnLoadCSV(self, evt):
        dlg = wx.FileDialog(self, message='Choose a CSV file to load',
                            defaultDir=os.getcwd(),
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            return
        filename = dlg.GetPath()
        dlg = wx.SingleChoiceDialog(self,
                                    'In order to link the rows of your file back to your images,\n'
                                    'you need to specify how your data was grouped. If this file\n'
                                    'does not contain data linked to your images, then select\n'
                                    '"%s".'%(DO_NOT_LINK_TO_IMAGES),
                                    'Specify Grouping', ['Image']+p._groups_ordered+[DO_NOT_LINK_TO_IMAGES])
        if dlg.ShowModal()!=wx.ID_OK:
            return
        group = dlg.GetStringSelection()
        self.LoadCSV(filename, group)
            
    def LoadCSV(self, csvfile, group='Image'):
        try:
            self.grid.Destroy()
        except: pass
        try:
            # Remove the previous column show/hide menu (should be the third menu)
            self.GetMenuBar().Remove(2)
            self.colmenu.Destroy()
        except: pass
        r = csv.reader(open(csvfile))
        labels = next(r)
        dtable = dbconnect.get_data_table_from_csv_reader(r)
        coltypes = db.InferColTypesFromData(dtable, len(labels))
        for i in range(len(coltypes)):
            if coltypes[i] == 'INT': coltypes[i] = int
            elif coltypes[i] == 'FLOAT': coltypes[i] = float
            else: coltypes[i] = str
        r = csv.reader(open(csvfile))
        next(r) # skip col-headers
        data = []
        for row in r:
            data += [[coltypes[i](v) for i,v in enumerate(row)]]
        data = np.array(data, dtype=object)
        
        if group == DO_NOT_LINK_TO_IMAGES:
            keycols = []
        elif group == 'Image':
            keycols = list(range(len(dbconnect.image_key_columns())))
        else:
            keycols = list(range(len(dm.GetGroupColumnNames(group))))
        
        self.grid = HugeTableGrid(self, data, labels, key_col_indices=keycols, grouping=group, chMap=p.image_channel_colors)
        self.Title = '%s (%s)'%(csvfile, group)
        self.file = csvfile
        self.CreateColumnMenu()
        self.RescaleGrid()
        
    def OnSaveCSV(self, evt):
        self.PromptToSaveCSV()
    
    def PromptToSaveCSV(self):
        defaultFileName = 'My_Enrichment_Data.csv'
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=os.getcwd(),
                                   defaultFile=defaultFileName,
                                   wildcard='csv|*',
                                   style=(wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT |
                                          wx.FD_CHANGE_DIR))
        res = saveDialog.ShowModal()
        if res==wx.ID_OK:
            self.SaveCSV(saveDialog.GetPath(), self.grid.GetTable().ordered_data, self.grid.GetTable().GetOrderedColLabels())
        saveDialog.Destroy()
        return res
    
    def OnSavePerImageCountsToCSV(self, evt):        
        defaultFileName = 'Per_Image_Counts.csv'
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=os.getcwd(),
                                   defaultFile=defaultFileName,
                                   wildcard='csv|*',
                                   style=(wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT |
                                          wx.FD_CHANGE_DIR))
        if saveDialog.ShowModal()==wx.ID_OK:
            colHeaders = list(dbconnect.image_key_columns())
            pos = len(colHeaders)
            if p.plate_id:
                colHeaders += [p.plate_id]
            if p.well_id:
                colHeaders += [p.well_id]
            colHeaders += ['total_count']
            colHeaders += ['count_'+bin.label for bin in self.GetParent().classBins]
            data = list(self.GetParent().keysAndCounts)
            for row in data:
                if p.table_id:
                    where = '%s=%s AND %s=%s'%(p.table_id, row[0], p.image_id, row[1])
                    total = sum(row[2:])
                else:
                    where = '%s=%s'%(p.image_id, row[0])
                    total = sum(row[1:])
                row.insert(pos, total)
                # Plate and Well are written separately IF they are found in the props file
                # TODO: ANY column could be reported by this mechanism
                if p.well_id:
                    res = db.execute('SELECT %s FROM %s WHERE %s'%(p.well_id, p.image_table, where), silent=True)
                    well = res[0][0]
                    row.insert(pos, well)
                if p.plate_id:
                    res = db.execute('SELECT %s FROM %s WHERE %s'%(p.plate_id, p.image_table, where), silent=True)
                    plate = res[0][0]
                    row.insert(pos, plate)
            self.SaveCSV(saveDialog.GetPath(), data, colHeaders)
        saveDialog.Destroy()

    def SaveCSV(self, filename, data, colLabels):
        f = open(filename, 'wb')
        w = csv.writer(f)
        w.writerow(colLabels)
        for row in data:
            w.writerow(row)
        f.close()
        logging.info('Table saved to %s'%filename)
        self.Title = '%s (%s)'%(filename, self.grid.grouping)
        self.file = filename
        
    def OnWriteTempTableToDB(self, evt):
        db.CreateTempTableFromData(self.grid.GetTable().data,
                           dbconnect.clean_up_colnames(self.grid.GetTable().col_labels), 
                           '__Classifier_output')
        try:
            if self.GetParent().pmb:
                self.GetParent().pmb.AddTableChoice('__Classifier_output')
        except:
            pass

        
    def GetData(self):
        if self.grid:
            return self.grid.GetTable().data
        else:
            return []

    def GetOrderedData(self):
        if self.grid:
            return self.grid.GetTable().ordered_data
        else:
            return []



usage = '''
Usage:
  python datatable.py csvfile propsfile grouping

Parameters:
  csvfile -- The csv file you wish to display. It's first row must contain column labels
  propsfile -- The corresponding properties file
  grouping -- Specify what group (in the properties file) was used to aggregate the rows.
              Omit this parameter if rows are per-image. 
'''


if __name__ == "__main__":
    import sys
    app = wx.App()

    if len(sys.argv) == 1:
        # ---- testing ----
        
        p.show_load_dialog()

        print('TESTING DATA GRID') 
        classes = ['a', 'b']
        data = np.array([['key 0',10,20,-30,40.123456789],
                         ['key 1',11,21,31,41.1],
                         ['key 1',10,21,31,41.1],
                         ['key 1',13,21,31,41.1],
                         ['key 1',31,21,31,41.1],
                         ['key 1',-1,21,31,41.1],
                         ['key 2',0,-22,32,42.2],
                         ['key 3',13,-3,33,43.3],
                         ['key 4',14,24,4,44.4],
                         ['key 5',5,5,-np.inf,np.inf]], dtype=object)
        labels = ['key', 'count-A' , 'count McLongtitle #1\n B' , 'P(a)' , 'P(b)' ]
#        grid = DataGrid()
        grid = DataGrid(data, labels, key_col_indices=[0,1], title='TEST', autosave=False)
        grid.Show()
        print((grid.GetData()))
        app.MainLoop()
        # -------------------
      
    if not (3 <= len(sys.argv) <= 4):
        print(usage)
        sys.exit()
    csvfile = sys.argv[1]
    propsfile = sys.argv[2]
    
    p = Properties()
    db = DBConnect()
    dm = DataModel()

    p.LoadFile(propsfile)
    r = csv.reader(open(csvfile))
    labels = next(r)
    dtable = dbconnect.get_data_table_from_csv_reader(r)
    coltypes = db.InferColTypesFromData(dtable, len(labels))
    for i in range(len(coltypes)):
        if coltypes[i] == 'INT': coltypes[i] = int
        elif coltypes[i] == 'FLOAT': coltypes[i] = float
        else: coltypes[i] = str
    r = csv.reader(open(csvfile))
    next(r) # skip col-headers
    data = []
    for row in r:
        data += [[coltypes[i](v) for i,v in enumerate(row)]]
    data = np.array(data, dtype=object)
    
    group = 'Image'
    if len(sys.argv)==4:
        group = sys.argv[3]
    
    if group == 'Image':
        keycols = list(range(len(dbconnect.image_key_columns())))
    else:
        keycols = list(range(len(dm.GetGroupColumnNames(group))))
    
    grid = DataGrid(data, labels, grouping=group, 
                    key_col_indices=keycols,
                    chMap=p.image_channel_colors, 
                    title=csvfile, autosave=False)
       
    grid.Show()
    
    app.MainLoop()
