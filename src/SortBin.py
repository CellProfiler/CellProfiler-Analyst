import wx
from Properties import Properties
from ImageCollection import ImageCollection
from ImageTileSizer import ImageTileSizer
from ImageTile import ImageTile
from DragObject import DragObject
from DropTarget import DropTarget
from DBConnect import DBConnect
import ImageTools

p  = Properties.getInstance()
db = DBConnect.getInstance()

class SortBin(wx.ScrolledWindow, DropTarget):
    '''
    SortBins contain collections of objects as small image tiles
    that can be dragged to other SortBins for classification.
    '''
    def __init__(self, parent, chMap=None, label='', classifier=None):
        wx.ScrolledWindow.__init__(self, parent)
        
        self.label = label
        self.tiles = []
        if chMap:
            self.chMap = chMap
        else:
            self.chMap = p.image_channel_colors
        self.classifier = classifier
        self.IC = None
        
        self.SetBackgroundColour('#000000')
        self.sizer = ImageTileSizer()
        self.SetSizer(self.sizer)

        (w,h) = self.sizer.GetSize()
        self.SetScrollbars(20,20,w/20,h/20,0,0)
        self.EnableScrolling(x_scrolling=False, y_scrolling=True)
                
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        
        self.CreatePopupMenu()
        
    
    def __str__(self):
        return 'Bin %s with %d objects'%(self.label, len(self.sizer.GetChildren()))
    
        
    def CreatePopupMenu(self):
        popupMenuItems = ['View full images of selected',
                          'Select all - [ctrl+a]',
                          'Deselect all - [ctrl+d]',
                          'Remove selected - [Delete]',
                          'Rename class',
                          'Delete bin']
        self.popupItemIndexById = {}
        self.popupMenu = wx.Menu()
        for i, item in enumerate(popupMenuItems):
            id = wx.NewId()
            self.popupItemIndexById[id] = i
            self.popupMenu.Append(id,item)
        self.popupMenu.Bind(wx.EVT_MENU,self.OnSelectFromPopupMenu)
            
        
    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        if evt.GetKeyCode() in [wx.WXK_DELETE, wx.WXK_BACK]:        # delete
            self.DestroySelectedTiles()
            self.Layout()
            self.Refresh()
        elif evt.ControlDown() or evt.CmdDown():
            if evt.GetKeyCode() == ord('A'):
                self.SelectAll()
            elif evt.GetKeyCode() == ord('D'):
                self.DeselectAll()
            elif evt.GetKeyCode() == ord('I'):
                [t.ToggleSelect() for t in self.tiles]
#            elif evt.GetKeyCode() == ord('R'):
#                self.classifier.RenameClass(self.label)
            else:
                evt.Skip()
        else:
            evt.Skip()
            
    def OnRightDown(self, evt):
        ''' On right click show popup menu. '''
        self.PopupMenu(self.popupMenu, evt.GetPosition())
        
    
    def OnSelectFromPopupMenu(self, evt):
        ''' Handles selections from the popup menu. '''
        choice = self.popupItemIndexById[evt.GetId()]
        if choice == 0:
            for key in self.SelectedKeys():
                imViewer = ImageTools.ShowImage((key[0],key[1]), self.chMap[:], parent=self.classifier,
                                        brightness=self.classifier.brightness, scale=self.classifier.scale)
                pos = db.GetObjectCoords(key)
                imViewer.imagePanel.SelectPoints([pos])
        elif choice == 1:
            self.SelectAll()
        elif choice == 2:
            self.DeselectAll()
        elif choice == 3:
            self.DestroySelectedTiles()
        elif choice == 4:
            self.classifier.RenameClass(self.label)
        elif choice == 5:
            self.classifier.RemoveSortClass(self.label)
    
    
    def AddObject(self, obKey, chMap, refresh=True):
        ''' Creates a new tile and adds it. '''
        if self.IC == None:
            self.IC = ImageCollection.getInstance(p)
        imgs = self.IC.FetchTile(obKey)
        newTile = ImageTile(self, obKey, imgs, chMap, False, scale=self.classifier.scale, brightness=self.classifier.brightness)
        self.tiles.append(newTile)
        self.sizer.Add(newTile, 0, wx.ALL|wx.EXPAND, 1)
        if refresh:
            self.Refresh()
            self.Layout()
        self.SetVirtualSize(self.sizer.CalcMin())
                
    
    def AddTile(self, tile, refresh=True, pos='first'):
        ''' Adds the given tile. 
        Set refresh to false for faster performance, and refresh manually.'''
        tile.bin = self
        self.tiles.append(tile)
        if pos == 'first':
            self.sizer.Insert(0, tile, 0, wx.ALL|wx.EXPAND, 1 )
        else:
            self.sizer.Add(tile, 0, wx.ALL|wx.EXPAND, 1)
        tile.Reparent(self)
        self.SetVirtualSize(self.sizer.CalcMin())
#        if refresh:
#            self.Refresh()
#            self.Layout()
        
    
#    def RemoveTile(self, tile, refresh=True):
#        ''' Removes the given tile.
#        Set refresh to false for faster performance, and refresh manually.'''
#        for t in self.tiles:
#            if t == tile:
#                self.tiles.remove(tile)
#                self.sizer.Remove(tile)
#                break
#        if refresh:
#            self.Refresh()
#            self.Layout()

                
#    def RemoveTiles(self, tiles):
#        for tile in tiles:
#            self.tiles.remove(tile)
#            self.sizer.Remove(tile)
#        self.Refresh()
#        self.Layout()
        
    
    def DestroyTile(self, tile, refresh=True):
        ''' Destroys the given tile.
        Set refresh to false for faster performance, and refresh manually.'''
        for t in self.tiles:
            if t == tile:
                self.tiles.remove(tile)
                self.sizer.Remove(tile)
                tile.Destroy()
                break
        if refresh:
            self.Refresh()
            self.Layout()


    def DestroySelectedTiles(self):
        for tile in self.Selection():
            self.tiles.remove(tile)
            self.sizer.Remove(tile)
            tile.Destroy()
        self.Refresh()
        self.Layout()
        self.classifier.UpdateBinLabels()
    
    
    def Clear(self):
        self.SelectAll()
        self.DestroySelectedTiles()         
        self.Refresh()
        self.Layout()

    def find_selected_tile_for_key(self, obkey):
        for t in self.tiles:
            if t.obKey == obkey and t.selected:
                return t
        
    def ReceiveDrop(self, drag):
        drag = DragObject.getInstance()
        self.DeselectAll()
        if type(drag.source) == SortBin:
            for obkey in drag.data:
                # we don't want to refetch image data
                tile = drag.source.find_selected_tile_for_key(obkey)
                drag.source.sizer.Remove(tile)
                drag.source.tiles.remove(tile)
                tile.Reparent(self)
                tile.bin = self
                self.sizer.Insert(0, tile, 0, wx.ALL|wx.EXPAND, 1)
                self.tiles.append(tile)
            drag.source.SetVirtualSize(drag.source.sizer.CalcMin())
        else:
            print self
            for obkey in drag.data:
                print "adding", obkey
                self.AddObject(obkey, self.chMap)
                
                
        self.SetVirtualSize(self.sizer.CalcMin())
        self.Scroll(-1, 0)
        self.SetFocusIgnoringChildren()

        
    def MapChannels(self, chMap):
        ''' Recalculates the displayed bitmap for all tiles in this bin. '''
        self.chMap = chMap
        for tile in self.tiles:
            tile.MapChannels(self.chMap)
            
    
    def SelectedKeys(self):
        ''' Returns the keys of currently selected tiles on this bin. '''
        return [tile.obKey for tile in self.tiles if tile.selected]
    
    def Selection(self):
        ''' Returns the currently selected tiles on this bin. '''
        tiles = []
        for tile in self.tiles:
            if tile.selected:
                tiles.append(tile)
        return tiles
    
    
    def GetObjectKeys(self):
        return [tile.obKey for tile in self.tiles]
        
    
    def GetNumberOfTiles(self):
        return len(self.tiles)
    
    
    def GetNumberOfSelectedTiles(self):
        return len(self.SelectedKeys())
        
    
    def SelectAll(self):
        ''' Selects all tiles on this bin. '''
        for tile in self.tiles:
            tile.Select()
        
    
    def DeselectAll(self):
        ''' Deselects all tiles on this bin. '''
        for tile in self.tiles:
            tile.Deselect()

    def OnFocus(self, evt):
        # stop focus events from propagating to the evil
        # wx.ScrollWindow class which otherwise causes scroll jumping.
        pass

    def OnLeftDown(self, evt):
        self.SetFocusIgnoringChildren()
        if not evt.ShiftDown():
            self.DeselectAll()
#        if evt.AltDown():
#            self.classifier.RemoveSortClass(self.label)
