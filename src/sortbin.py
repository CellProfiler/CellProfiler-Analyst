from dbconnect import DBConnect
import tilecollection
from imagetile import ImageTile
from imagetilesizer import ImageTileSizer
from imagecontrolpanel import ImageControlPanel
from properties import Properties
import imagetools
import cPickle
import wx

p  = Properties.getInstance()
db = DBConnect.getInstance()


# The event type is shared, and there is no information in the event
# about which SortBin it came from.  That's ok because the handler
# will need to check all the SortBins anyway.
EVT_QUANTITY_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)


class CellMontageFrame(wx.Frame):
    '''A frame that allows you to add a bunch of object tiles
    '''
    def __init__(self, parent, **kwargs):
        wx.Frame.__init__(self, parent, **kwargs)
        self.sb = SortBin(self)
        self.cp = wx.CollapsiblePane(self, label='Show controls', style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.icp = ImageControlPanel(self.cp.GetPane(), self)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sb, 1, wx.EXPAND)
        self.Sizer.Add(self.cp, 0, wx.EXPAND)
        
        self.cp.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_control_pane_change)
        
    def _on_control_pane_change(self, evt=None):
        self.Layout()
        if self.cp.IsExpanded():
            self.cp.SetLabel('Hide controls')
        else:
            self.cp.SetLabel('Show controls')
        
    def add_objects(self, obkeys):
        self.sb.AddObjects(obkeys)
        
    #
    # required by ImageControlPanel
    #
    def SetBrightness(self, brightness):
        [t.SetBrightness(brightness) for t in self.sb.tiles]

    def SetScale(self, scale):
        [t.SetScale(scale) for t in self.sb.tiles]
        self.sb.UpdateSizer()

    def SetContrastMode(self, mode):
        [t.SetContrastMode(mode) for t in self.sb.tiles]

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
        self.SetMinSize((50, 50))

        (w,h) = self.sizer.GetSize()
        self.SetScrollbars(20,20,w/20,h/20,0,0)
        self.EnableScrolling(x_scrolling=False, y_scrolling=True)
                
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        # stop focus events from propagating to the evil
        # wx.ScrollWindow class which otherwise causes scroll jumping.
        self.Bind(wx.EVT_SET_FOCUS, (lambda(evt):None))
        tilecollection.EVT_TILE_UPDATED(self, self.OnTileUpdated)
    
        self.CreatePopupMenu()

    def __str__(self):
        return 'Bin %s with %d objects'%(self.label, len(self.sizer.GetChildren()))
        
    def CreatePopupMenu(self):
        popupMenuItems = ['View full images of selected',
                          'Select all\tCtrl+A',
                          'Deselect all\tCtrl+D',
                          'Invert selection\tCtrl+I',
                          'Remove selected\tDelete']
        if self.label != 'unclassified' and self.classifier is not None:
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
                if self.classifier:
                    imViewer = imagetools.ShowImage(key[:-1], self.chMap[:], 
                                    parent=self.classifier, 
                                    brightness=self.classifier.brightness, 
                                    scale=self.classifier.scale,
                                    contrast=self.classifier.contrast)
                else:
                    imViewer = imagetools.ShowImage(key[:-1], self.chMap[:], parent=self)

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
    
    def AddObject(self, obKey, chMap=None, priority=1, pos='first'):
        self.AddObjects([obKey], chMap, priority, pos)
                        
    def AddObjects(self, obKeys, chMap=None, priority=1, pos='first'):
        if chMap is None:
            chMap = p.image_channel_colors
        if self.tile_collection == None:
            self.tile_collection = tilecollection.TileCollection.getInstance()
        imgSet = self.tile_collection.GetTiles(obKeys, (self.classifier or self), priority)
        for i, obKey, imgs in zip(range(len(obKeys)), obKeys, imgSet):
            if self.classifier:
                newTile = ImageTile(self, obKey, imgs, chMap, False,
                                    scale=self.classifier.scale, 
                                    brightness=self.classifier.brightness,
                                    contrast=self.classifier.contrast)
            else:
                newTile = ImageTile(self, obKey, imgs, chMap, False)
                
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
        if self.classifier:
            self.AddObjects(obKeys, self.classifier.chMap)
        else:
            self.AddObjects(obKeys)
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
        ''' Inverts the selection. '''
        for t in self.tiles:
            t.ToggleSelect()
        
    def OnLeftDown(self, evt):
        ''' Deselect all tiles unless shift is held. '''
        self.SetFocusIgnoringChildren() # prevent children from getting focus (want bin to catch key events)
        if not evt.ShiftDown():
            self.DeselectAll()

    def OnTileUpdated(self, evt):
        ''' When the tile loader returns the cropped image update the tile. '''
        self.UpdateTile(evt.data)
            
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
          so we inform Classifier whenever this state changes.
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



if __name__ == '__main__':
    app = wx.PySimpleApp()
 
    p.show_load_dialog()    
    import datamodel
    dm = datamodel.DataModel.getInstance()
    
    f = wx.Frame(None)
    sb = SortBin(f)
    f.Show()
    
    sb.AddObjects([dm.GetRandomObject() for i in range(50)])

    app.MainLoop()