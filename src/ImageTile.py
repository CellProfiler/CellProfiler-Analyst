'''
A special image panel meant to be dragged and dropped.
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


class ImageTile(ImagePanel, DropTarget):
    '''
    ImageTiles are thumbnail images that can be dragged and dropped
    between SortBins.
    '''
    def __init__(self, bin, obKey, images, chMap, selected=False, scale=1.0, brightness=1.0):
        ImagePanel.__init__(self, images, chMap, bin, scale=scale, brightness=brightness)
        
        self.bin        = bin             # the SortBin this object belongs to
        self.classifier = bin.classifier  # ClassifierGUI needs to capture the mouse on tile selection
        self.obKey      = obKey           # (table, image, object)
        self.selected   = selected        # whether or not this tile is selected
        
        self.MapChannels(chMap)
        self.CreatePopupMenu()
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
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
            for obKey in self.bin.SelectedKeys():
                imViewer = ImageTools.ShowImage(obKey[:-1], self.chMap[:], parent=self.classifier,
                                        brightness=self.brightness, scale=self.scale)
                pos = db.GetObjectCoords(obKey)
                imViewer.imagePanel.SelectPoints([pos])
        elif choice == 1:
            self.bin.SelectAll()
        elif choice == 2:
            self.bin.DeselectAll()
        elif choice == 3:
            self.bin.DestroySelectedTiles()
            
            
    def OnDClick(self, evt):
        imViewer = ImageTools.ShowImage(self.obKey[:-1], list(self.chMap), parent=self.classifier,
                                        brightness=self.brightness, scale=self.scale)
        imViewer.imagePanel.SelectPoints([db.GetObjectCoords(self.obKey)])
        
        
    def Select(self):
        if not self.selected:
            self.selected = True
            self.Refresh()


    def Deselect(self):
        if self.selected:
            self.selected = False
            self.Refresh()
        
    
    def ToggleSelect(self):
        if self.selected:
            self.Deselect()
        else:
            self.Select()
    
    
    def OnLeftDown(self, evt):
        self.bin.SetFocusIgnoringChildren()

#            cursorImg = self.bitmap.ConvertToImage()
#            cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, int(self.size[0])/2)
#            cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, int(self.size[1])/2)
#            wx.SetCursor(wx.CursorFromImage(cursorImg))
#            for tlw in wx.GetTopLevelWindows():
#                tlw.SetCursor(wx.CursorFromImage(cursorImg))
            
        if not evt.ShiftDown() and not self.selected:
            self.bin.DeselectAll()
            self.Select()
        elif evt.ShiftDown():
            self.ToggleSelect()

        if self.bin.SelectedKeys():
            self.classifier.CaptureMouse()
            drag.data = self.bin.SelectedKeys()
            drag.source = self.bin

    def OnSize(self, evt):
        self.SetClientSize(evt.GetSize())
        evt.Skip()
        
        
    def ReceiveDrop(self, data):
        if self.bin != drag.source:
            self.bin.ReceiveDrop(data)
            

        
