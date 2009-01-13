'''
ImageTile.py
Authors: afraser
'''

import wx
import ImageTools
from Properties import Properties
from DropTarget import DropTarget
from DragObject import DragObject
from ImagePanel import ImagePanel
from DBConnect import DBConnect

p = Properties.getInstance()
db = DBConnect.getInstance()
drag = DragObject.getInstance()


class ImageTile(wx.Window, DropTarget):
    '''
    ImageTiles are thumbnail images that can be dragged and dropped
    between CellBoards.  They contain image data in a key=(table, image, object)
    and manage their state of selection.
    '''
    def __init__(self, board, obKey, images, chMap, selected=False, scale=1.0, brightness=1.0):
        wx.Window.__init__(self, board)
        
        self.imagePanel = ImagePanel(images, chMap, self, scale=scale, brightness=brightness)
        
        self.SetSize(self.imagePanel.GetSize())
        
        self.board      = board
        self.classifier = board.classifier
        self.obKey      = obKey       # (table, image, object)
        self.images     = images      # the image channels
        self.selected   = selected    # whether or not this tile is selected
        
        self.MapChannels(chMap)
        self.CreatePopupMenu()
        
        self.imagePanel.Bind(wx.EVT_SIZE, self.OnSize)
        self.imagePanel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.imagePanel.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)     # Show images on double click
        self.imagePanel.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        
            
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
                imViewer = ImageTools.ShowImage(obKey[:-1], self.chMap[:], parent=self.classifier)
                pos = db.GetObjectCoords(obKey)
                imViewer.imagePanel.SelectPoints([pos])
        elif choice == 1:
            self.board.SelectAll()
        elif choice == 2:
            self.board.DeselectAll()
        elif choice == 3:
            self.board.DestroySelectedTiles()
            
            
    def OnDClick(self, evt):
        imViewer = ImageTools.ShowImage(self.obKey[:-1], self.chMap[:], parent=self.classifier)
        pos = db.GetObjectCoords(self.obKey)
        imViewer.imagePanel.SelectPoints([pos])
        

    def MapChannels(self, chMap):
        ''' Recalculates the displayed bitmap for this tile. '''
        self.imagePanel.MapChannels(chMap)
        self.chMap = chMap
        
        
    def Select(self):
        if not self.selected:
            self.selected = True
            self.imagePanel.selected = True
            self.Refresh()


    def Deselect(self):
        if self.selected:
            self.selected = False
            self.imagePanel.selected = False
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
#            cursorImg = self.bitmap.ConvertToImage()
#            cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, int(self.size[0])/2)
#            cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, int(self.size[1])/2)
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

    
    def OnSize(self, evt):
        self.SetClientSize(evt.GetSize())
        evt.Skip()
        
        
    def ReceiveDrop(self, data):
        if self.board != drag.source:
            self.board.ReceiveDrop(data)
            

        
