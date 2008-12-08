'''
ImageTile.py
Authors: afraser
'''

import wx
import ImageTools
from Properties import Properties
from DropTarget import DropTarget
from DragObject import DragObject


p = Properties.getInstance()
drag = DragObject.getInstance()


class ImageTile(wx.Panel, DropTarget):
    '''
    ImageTiles are thumbnail images that can be dragged and dropped
    between CellBoards.  They contain image data in a key=(table, image, object)
    and manage their state of selection.
    '''
    def __init__(self, board, obKey, images, chMap, selected=False):

        self.size = (int(p.image_tile_size),int(p.image_tile_size))
        wx.Panel.__init__(self, board, size=self.size)
        
        self.board = board
        self.classifier = board.classifier
        self.obKey = obKey         # (table, image, object)
        self.images = images       # the image channels
        self.bitmap = None         # the drawn image
        self.chMap = chMap
        self.selected = selected   # whether or not this tile is selected
            
        self.MapChannels(chMap)
        self.CreatePopupMenu()

        self.SetSizeHintsSz(self.size)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)     # Show images on double click
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        
            
    def CreatePopupMenu(self):
        popupMenuItems = ['View full images of selected',
                          '[ctrl+a] - Select all',
                          '[ctrl+d] - Deselect all',
                          '[Delete] - Remove selected ']
        self.popupItemIndexById = {}
        self.popupMenu = wx.Menu()
        for i, item in enumerate(popupMenuItems):
            id = wx.NewId()
            self.popupItemIndexById[id] = i
            self.popupMenu.Append(id,item)
        self.popupMenu.Bind(wx.EVT_MENU,self.OnSelectFromPopupMenu)
        
        
    def OnRightDown(self, evt):
        ''' On right click show popup menu. '''
        self.PopupMenu(self.popupMenu, evt.GetPosition())
    
    
    def OnSelectFromPopupMenu(self, evt):
        ''' Handles selections from the popup menu. '''
        choice = self.popupItemIndexById[evt.GetId()]
        if choice == 0:
            for obKey in self.board.SelectedKeys():
                ImageTools.ShowImage(obKey[:-1], self.chMap[:], parent=self.classifier)
        elif choice == 1:
            self.board.SelectAll()
        elif choice == 2:
            self.board.DeselectAll()
        elif choice == 3:
            self.board.DestroySelectedTiles()
            
            
    def OnDClick(self, evt):
        ImageTools.ShowImage(self.obKey[:-1], self.chMap[:], parent=self.classifier)
        

    def MapChannels(self, chMap):
        ''' Recalculates the displayed bitmap for this tile. '''
        self.chMap = chMap
        self.bitmap = ImageTools.MergeToBitmap(self.images, self.chMap, self.selected)
        self.Refresh()
        
        
    def Select(self):
        self.selected = True
        self.bitmap = ImageTools.MergeToBitmap(self.images, self.chMap, self.selected)
        self.Refresh()


    def Deselect(self):
        self.selected = False
        self.bitmap = ImageTools.MergeToBitmap(self.images, self.chMap, self.selected)
        self.Refresh()
        
    
    def ToggleSelect(self):
        if self.selected:
            self.Deselect()
        else:
            self.Select()
    
    
    def OnLeftDown(self, evt):
        self.board.SetFocus()
        if drag.IsEmpty():
            self.classifier.CaptureMouse()
            cursorImg = self.bitmap.ConvertToImage()
            cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, int(self.size[0])/2)
            cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, int(self.size[1])/2)
#            wx.SetCursor(wx.CursorFromImage(cursorImg))
#            for tlw in wx.GetTopLevelWindows():
#                tlw.SetCursor(wx.CursorFromImage(cursorImg))
            drag.data = self.board.SelectedKeys()
            drag.source = self.board
            
        if not evt.ShiftDown() and not self.selected:
            self.board.DeselectAll()
            self.ToggleSelect()
            return
        if not evt.ShiftDown():
            self.Select()
        else:
            self.ToggleSelect()

        if evt.AltDown():
            print 'Clearing selected tiles'
            self.board.DestroySelectedTiles()
            return

                
    
    def OnSize(self, evt):
        self.SetSize(evt.GetSize())
        evt.Skip()
    
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0, 0)
        
        
    def ReceiveDrop(self, data):
        if self.board != drag.source:
            self.board.ReceiveDrop(data)
            
        
    
