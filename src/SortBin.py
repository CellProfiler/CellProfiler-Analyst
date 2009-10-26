from __future__ import with_statement
from DBConnect import DBConnect
from TileCollection import TileCollection
from ImageTile import ImageTile
from ImageTileSizer import ImageTileSizer
from Properties import Properties
import ImageTools
import cPickle
import wx

p  = Properties.getInstance()
db = DBConnect.getInstance()


# The event type is shared, and there is no information in the event
# about which SortBin it came from.  That's ok because the handler
# will need to check all the SortBins anyway.
EVT_QUANTITY_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)


class SortBinDropTarget(wx.DropTarget):
    def __init__(self, bin):
        wx.DropTarget.__init__(self)
        self.data = wx.CustomDataObject("ObjectKey")
        self.SetDataObject(self.data)
        self.bin = bin
        
    def OnData(self, x, y, dragres):
        if not self.GetData():
            return wx.DragNone
        draginfo = self.data.GetData()
        srcID, obKeys = cPickle.loads(draginfo)
        if not obKeys:
            return wx.DragNone
        return self.bin.ReceiveDrop(srcID, obKeys)


class SortBin(wx.ScrolledWindow):
    '''
    SortBins contain collections of objects as small image tiles
    that can be dragged to other SortBins for classification.
    '''
    def __init__(self, parent, chMap=None, label='', classifier=None, parentSizer=None):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetDropTarget(SortBinDropTarget(self))
        
        self.label           = label
        self.parentSizer     = parentSizer
        self.tiles           = []
        self.classifier      = classifier
        self.trained         = False
        self.empty           = True
        self.tile_collection = None          # tile collection
        if chMap:
            self.chMap = chMap
        else:
            self.chMap = p.image_channel_colors
        
        self.SetBackgroundColour('#000000')
        self.sizer = ImageTileSizer()
        self.SetSizer(self.sizer)
        self.SetMinSize((int(p.image_tile_size), int(p.image_tile_size)))

        (w,h) = self.sizer.GetSize()
        self.SetScrollbars(20,20,w/20,h/20,0,0)
        self.EnableScrolling(x_scrolling=False, y_scrolling=True)
                
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        # stop focus events from propagating to the evil
        # wx.ScrollWindow class which otherwise causes scroll jumping.
        self.Bind(wx.EVT_SET_FOCUS, (lambda(evt):None))
    
        self.CreatePopupMenu()

    def __str__(self):
        return 'Bin %s with %d objects'%(self.label, len(self.sizer.GetChildren()))
    
        
    def CreatePopupMenu(self):
        popupMenuItems = ['View full images of selected',
                          'Select all\tCtrl+A',
                          'Deselect all\tCtrl+D',
                          'Invert selection\tCtrl+I',
                          'Remove selected\tDelete']
        if self.label != 'unclassified':
            popupMenuItems += ['Rename class', 'Delete bin']
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
            self.RemoveSelectedTiles()
            self.UpdateSizer()
        elif evt.ControlDown() or evt.CmdDown():
            if evt.GetKeyCode() == ord('A'):
                self.SelectAll()
            elif evt.GetKeyCode() == ord('D'):
                self.DeselectAll()
            elif evt.GetKeyCode() == ord('I'):
                self.InvertSelection()
        evt.Skip()
        
            
    def OnRightDown(self, evt):
        ''' On right click show popup menu. '''
        self.PopupMenu(self.popupMenu, evt.GetPosition())
        
    
    def OnSelectFromPopupMenu(self, evt):
        ''' Handles selections from the popup menu. '''
        choice = self.popupItemIndexById[evt.GetId()]
        if choice == 0:
            for key in self.SelectedKeys():
                imViewer = ImageTools.ShowImage(key[:-1], self.chMap[:], parent=self.classifier,
                                        brightness=self.classifier.brightness, scale=self.classifier.scale,
                                        contrast=self.classifier.contrast)
                imViewer.imagePanel.SelectPoint(db.GetObjectCoords(key))
        elif choice == 1:
            self.SelectAll()
        elif choice == 2:
            self.DeselectAll()
        elif choice == 3:
            self.InvertSelection()
        elif choice == 4:
            self.RemoveSelectedTiles()
        elif choice == 5:
            self.classifier.RenameClass(self.label)
        elif choice == 6:
            self.classifier.RemoveSortClass(self.label)
    
    
    def AddObject(self, obKey, chMap, priority=1, pos='first'):
        self.AddObjects([obKey], chMap, priority, pos)
                 
                        
    def AddObjects(self, obKeys, chMap, priority=1, pos='first'):
        if self.tile_collection == None:
            self.tile_collection = TileCollection.getInstance()
        imgSet = self.tile_collection.GetTiles(obKeys, self.classifier, priority)
        with self.tile_collection.load_lock:
            for i, obKey, imgs in zip(range(len(obKeys)), obKeys, imgSet):
                newTile = ImageTile(self, obKey, imgs, chMap, False,
                                    scale=self.classifier.scale, 
                                    brightness=self.classifier.brightness,
                                    contrast=self.classifier.contrast)
                if pos == 'first':
                    self.tiles.insert(i, newTile)
                    self.sizer.Insert(i, newTile, 0, wx.ALL|wx.EXPAND, 1 )
                else:
                    self.tiles.append(newTile)
                    self.sizer.Add(newTile, 0, wx.ALL|wx.EXPAND, 1)
        self.UpdateSizer()
        self.UpdateQuantity()

    
    def RemoveKey(self, obKey):
        ''' Removes the specified tile. '''
        self.RemoveKeys([obKey])
        
        
    def RemoveKeys(self, obKeys):
        ''' Removes the specified tile. '''
        for t in self.tiles:
            if t.obKey in obKeys:
                self.tiles.remove(t)
                self.sizer.Remove(t)
                t.Destroy()
        self.UpdateSizer()
        self.UpdateQuantity()


    def RemoveSelectedTiles(self):
        for tile in self.Selection():
            self.tiles.remove(tile)
            self.sizer.Remove(tile)
            tile.Destroy()
        self.UpdateSizer()
        self.UpdateQuantity()
    
    
    def Clear(self):
        self.RemoveKeys(self.GetObjectKeys())
        

    def find_selected_tile_for_key(self, obkey):
        for t in self.tiles:
            if t.obKey == obkey and t.selected:
                return t
            
        
    def ReceiveDrop(self, srcID, obKeys):
        # TODO: stop drops from happening on the same board they originated on 
        if srcID == self.GetId():
            return
        self.DeselectAll()
        self.AddObjects(obKeys, self.classifier.chMap)
        [tile.Select() for tile in self.tiles if tile.obKey in obKeys]
        self.SetFocusIgnoringChildren() # prevent children from getting focus (want bin to catch key events)
        return wx.DragMove
        
        
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
            
    def InvertSelection(self):
        [t.ToggleSelect() for t in self.tiles]
        

    def OnLeftDown(self, evt):
        ''' Deselect all tiles unless shift is held. '''
        self.SetFocusIgnoringChildren() # prevent children from getting focus (want bin to catch key events)
        if not evt.ShiftDown():
            self.DeselectAll()


    def UpdateTile(self, obKey):
        ''' Called when image data is available for a specific tile. '''
        for t in self.tiles:
            if t.obKey == obKey:
                t.UpdateBitmap()
                
    def UpdateSizer(self):
        return self.SetVirtualSize(self.sizer.CalcMin())        


    def UpdateQuantity(self):
        '''
        If a bin contains no objects then it can't be used for training,
          so we inform ClassifierGUI whenever this state changes.
        If the bin is in a StaticBoxSizer (all of them are) we update the
          StaticBox label to contain the current object count.
        '''
        empty = len(self.tiles) == 0
        if (empty and not self.empty) or (not empty and self.empty): 
            self.empty = empty
            event = wx.PyCommandEvent(EVT_QUANTITY_CHANGED.typeId, self.GetId())
            self.GetEventHandler().ProcessEvent(event)
        try:
            self.parentSizer.GetStaticBox().SetLabel('%s (%d)'%(self.label,len(self.tiles)))
        except:
            pass
