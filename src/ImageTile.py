'''
A special image panel meant to be dragged and dropped.
'''
from DBConnect import DBConnect
from ImagePanel import ImagePanel
from Properties import Properties
import ImageTools
import cPickle
import wx


p = Properties.getInstance()
db = DBConnect.getInstance()


class ImageTileDropTarget(wx.DropTarget):
    ''' ImageTiles pass drop events to their parent bin. '''
    def __init__(self, tile):
        self.data = wx.CustomDataObject("ObjectKey")
        wx.DropTarget.__init__(self, self.data)
        self.tile = tile
    
    def OnDrop(self, x, y):
        self.GetData()
        key = self.data.GetData()
        self.tile.bin.ReceiveDrop(key)
        return True


class ImageTile(ImagePanel):
    '''
    ImageTiles are thumbnail images that can be dragged and dropped
    between SortBins.
    '''
    def __init__(self, bin, obKey, images, chMap, selected=False, scale=1.0, brightness=1.0):
        ImagePanel.__init__(self, images, chMap, bin, scale=scale, brightness=brightness)
        self.SetDropTarget(ImageTileDropTarget(self))

        self.bin        = bin             # the SortBin this object belongs to
        self.classifier = bin.classifier  # ClassifierGUI needs to capture the mouse on tile selection
        self.obKey      = obKey           # (table, image, object)
        self.selected   = selected        # whether or not this tile is selected
        self.leftPressed = False
        
        self.MapChannels(chMap)
        self.CreatePopupMenu()
                
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)     # Show images on double click
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaving)


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
            self.bin.RemoveSelectedTiles()
            
            
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
        self.leftPressed = True
        self.mouseDownX = evt.GetX()
        self.mouseDownY = evt.GetY()
            
        if not evt.ShiftDown() and not self.selected:
            self.bin.DeselectAll()
            self.Select()
        elif evt.ShiftDown():
            self.ToggleSelect()
            
            
    def OnLeaving(self, evt):
        self.leftPressed = False

            
    def OnMotion(self, evt):
        # Give a 4 pixel radius of leeway before dragging a tile
        # this makes selecting multiple tiles less tedious
        if (not evt.LeftIsDown() or not self.leftPressed or 
            ((evt.GetX()-self.mouseDownX)**2+(evt.GetY()-self.mouseDownY)**2 <= 16)):
            return
        
        self.bin.SetFocusIgnoringChildren()
        
        cursorImg = self.bitmap.ConvertToImage()
        cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, int(self.bitmap.Size[0])/2)
        cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, int(self.bitmap.Size[1])/2)
        cursor = wx.CursorFromImage(cursorImg)
            
        if not evt.ShiftDown() and not self.selected:
            self.bin.DeselectAll()
            self.Select()
        elif evt.ShiftDown():
            self.ToggleSelect()

        source = wx.DropSource(self, copy=cursor, move=cursor)
        # wx crashes unless the data object is assigned to a variable.
        data_object = wx.CustomDataObject("ObjectKey")
        data_object.SetData(cPickle.dumps(self.bin.SelectedKeys()))
        source.SetData(data_object)
        result = source.DoDragDrop(flags=wx.Drag_DefaultMove)
        if result is 0:
            self.bin.RemoveSelectedTiles()
    
    
    def OnSize(self, evt):
        self.SetClientSize(evt.GetSize())
        evt.Skip()


        
