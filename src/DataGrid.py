import wx
import wx.grid
import numpy
import ImageTools
from DataModel import DataModel
from Properties import Properties
from sys import stderr
import os
import csv

p = Properties.getInstance()
dm = DataModel.getInstance()


IMAGE_GROUPING = 'Image'


class DataGrid(wx.Frame):
    '''
    A frame with a grid inside of it.
    This grid is specifically designed to hold per-image or grouped per-image data
       in each row.
    Double-clicking a row label will launch an image viewer for that image or images.
    Right-clicking a row label will display a popup menu of images to select for viewing.
    Clicking on a column label will sort that column in ascending then descending order.
    '''
    def __init__(self, data, labels, grouping=IMAGE_GROUPING, chMap=None, parent=None, title='Data Grid'):
        wx.Frame.__init__(self, parent, id=-1, title=title)
        
        self.grid = wx.grid.Grid(parent=self)      # the grid
        self.data = data                           # numpy array of rows x cols
        self.order = numpy.arange(data.shape[0])   # defines the order of the rows displayed
        self.labels = labels                       # text labels for each column
        self.grouping = grouping                   # group name string to match a group in the DataModel.  eg: 'Wells'
        self.chMap = chMap                         # channel-to-color map can be passed in so when an ImageViewer is launched
                                                   #    from the table, the user gets their most recent channel-color map 
        self.sortcol = 0                           # index of the current column being sorted-by
        self.sortdir = 1                           # direction of sorting +1 = ascending, -1 = descending
        
        assert len(labels) == data.shape[1], 'DataGrid.__init__: Number of column labels does not match number of columns in data.'
        
        self.filemenu = wx.Menu()
        self.saveCSVMenuItem = wx.MenuItem(parentMenu=self.filemenu, id=wx.NewId(), text='Save data to CSV', help='Saves data as comma separated values.')
        self.filemenu.AppendItem(self.saveCSVMenuItem)
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.menuBar.Append(self.filemenu, 'File')

        if self.chMap == None:
            self.chMap = p.image_channel_colors
        self.grid.CreateGrid(self.data.shape[0], self.data.shape[1] )
        self.SetColumnLabels(self.labels)
        self.SetGridData(self.data)
#        self.grid.AutoSize()                        # Doesn't work for large grids 
        self.SetSize((800,500))
        self.SetSize((self.grid.Size[0], min(self.grid.Size[1], 500)+22))
        
        self.Bind(wx.EVT_MENU, self.OnSaveCSV, self.saveCSVMenuItem)
        self.grid.Bind(wx.EVT_KEY_UP, self.OnKey)
        wx.grid.EVT_GRID_LABEL_LEFT_CLICK(self.grid, self.OnLabelClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(self.grid, self.OnLabelRightClick)
        wx.grid.EVT_GRID_LABEL_LEFT_DCLICK(self.grid, self.OnLabelDClick)
        
        
    def OnKey(self, evt):
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            #TODO: confirm save
            self.Close()
        evt.Skip()
        

    def OnSaveCSV(self, evt):
        defaultFileName = 'My_Enrichment_Data.csv'
        saveDialog = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(), defaultFile=defaultFileName, wildcard='csv', style=wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
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
        if evt.Row >= 0:
            if self.grouping == IMAGE_GROUPING:
                imKey = self.data[self.order][evt.Row,0]
                ImageTools.ShowImage(imKey, self.chMap, parent=self)
            else:
                groupKey = self.data[self.order][evt.Row,0]
                imKeys = dm.GetImagesInGroup(self.grouping, tuple(groupKey))
                for imKey in imKeys:
                    ImageTools.ShowImage(imKey, self.chMap, parent=self)
            
            
    def OnLabelRightClick(self, evt):
        if evt.Row >= 0:
            if self.grouping == IMAGE_GROUPING:
                imKey = self.data[self.order][evt.Row,0]
                self.ShowPopupMenu([imKey], evt.GetPosition())
            else:
                groupKey = self.data[self.order][evt.Row,0]
                imKeys = dm.GetImagesInGroup(self.grouping, tuple(groupKey))
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
        ''' Handles selections from the popup menu. '''
        imKey = self.popupItemById[evt.GetId()]
        ImageTools.ShowImage(imKey, self.chMap, parent=self)

 
    def SortGridByCol(self, colIndex):
        # If this column is already sorted, flip it
        if self.sortcol == colIndex:
            self.order = self.order[::-1]
            if self.sortdir == 1:
                self.sortdir = -1
            else:
                self.sortdir = 1
        # If this column hasn't been sorted yet, then sort descending
        else:
            self.order = self.data[:,colIndex].argsort()[::-1]
            self.sortdir = -1
            
        self.sortcol = colIndex
        self.SetGridData( self.data[self.order] )

    
    def SetColumnLabels(self, labels):
        for i, label in enumerate(labels):
            self.grid.SetColLabelValue(i, label)

    
    def SetGridData(self, data):
        assert data.shape == (self.grid.NumberRows,self.grid.NumberCols), 'ScoreGrid.SetGridData: Data shape does not match grid shape.'
        for i in xrange(data.shape[0]):      # rows
            self.grid.SetRowLabelValue(i, str(data[i][0]))
            for j in xrange(data.shape[1]):  # cols
                if ( type(data[i][j])==float or
                     type(data[i][j])==numpy.float64 or
                     type(data[i][j])==numpy.float32 ):
                    self.grid.SetCellValue(i,j,'% .4f' % data[i][j])   # format floats to 4 decimal places   
                else:
                    self.grid.SetCellValue(i,j,str(data[i][j]))
                self.grid.SetReadOnly(i,j)                            # set cell read only
    
    






if __name__ == "__main__":
    p = Properties.getInstance()
    p.LoadFile('../properties/nirht_test.properties')
    
    classes = ['a', 'b']
    hits = numpy.array([['key 0000000',10,20,-30,40.123456789],['key 1',11,21,31,41.1],['key 2',0,-22,32,42.2],['key 3',13,-3,33,43.3],['key 4',14,24,4,44.4],['key 5',5,5,5,5.12345]], dtype=object)
    order = numpy.array([4,3,1,2,0])
    labels = ['key', 'count A' , 'count McLongtitle #1\n B' , 'P a' , 'P b' ]
        
    app = wx.PySimpleApp()
    grid = DataGrid( hits, labels )
    grid.Show()
    app.MainLoop()

