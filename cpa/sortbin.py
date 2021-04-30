from .dbconnect import DBConnect
from . import tilecollection
from .imagetile import ImageTile
from .imagetilesizer import ImageTileSizer
from .imagecontrolpanel import ImageControlPanel
from .properties import Properties
from . import imagetools
import pickle
import wx
import logging


p  = Properties()
db = DBConnect()


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

    def Destroy(self):
        ''' Kill off all threads before combusting. '''
        super(CellMontageFrame, self).Destroy()
        import threading
        t = tilecollection.TileCollection()
        if self.sb in t.loader.notify_window:
            t.loader.notify_window.remove(self.sb)
        # If no other windows are attached to the loader we shut it down and delete the tilecollection.
        if len(t.loader.notify_window) == 0:
            for thread in threading.enumerate():
                if thread != threading.currentThread() and thread.getName().lower().startswith('tileloader'):
                    logging.debug('Aborting thread %s' % thread.getName())
                    try:
                        thread.abort()
                    except:
                        pass
            tilecollection.TileCollection.forget()
        return True

class SortBinDropTarget(wx.DropTarget):
    def __init__(self, bin):
        wx.DropTarget.__init__(self)
        self.data = wx.CustomDataObject("application.cpa.ObjectKey")
        self.SetDataObject(self.data)
        self.bin = bin
        
    def OnData(self, x, y, dragres):
        if not self.GetData():
            return wx.DragNone
        draginfo = self.data.GetData()
        srcID, obKeys = pickle.loads(draginfo)
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
        if label != "image gallery":
            self.SetDropTarget(SortBinDropTarget(self))

        self.label           = label
        self.parentSizer     = parentSizer
        self.tiles           = []
        self.classifier      = classifier
        self.trained         = False
        self.empty           = True
        self.tile_collection = None          # tile collection
        self.dragging = False
        self.anchor = None
        self.selecting = set()
        self.selectbox = None
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
        self.EnableScrolling(xScrolling=False, yScrolling=True)

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        # stop focus events from propagating to the evil
        # wx.ScrollWindow class which otherwise causes scroll jumping.
        self.Bind(wx.EVT_SET_FOCUS, (lambda evt: None))
        self.Bind(wx.EVT_PAINT, self.OnPaint)

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
        # Spaces in the bin label are only possible in the Image Gallery
        if " " not in self.label and self.classifier is not None:
            popupMenuItems += ['Remove duplicates']
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
        elif evt.ControlDown() or evt.CmdDown():
            if evt.GetKeyCode() == ord('A'):
                self.SelectAll()
            elif evt.GetKeyCode() == ord('D'):
                self.DeselectAll()
            elif evt.GetKeyCode() == ord('I'):
                self.InvertSelection()
        elif self.classifier:
            self.classifier.OnKey(evt)
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
            self.RemoveDuplicateTiles()
        elif choice == 6:
            self.classifier.RenameClass(self.label)
        elif choice == 7:
            self.classifier.RemoveSortClass(self.label)

    def AddObject(self, obKey, chMap=None, priority=1, pos='first'):
        self.AddObjects([obKey], chMap, priority, pos)

    def AddObjects(self, obKeys, chMap=None, priority=1, pos='first', display_whole_image=False, srcID=None,
                   deselect=False):
        if chMap is None:
            chMap = p.image_channel_colors
        if self.tile_collection == None:
            self.tile_collection = tilecollection.TileCollection()
        if srcID is not None and isinstance(wx.FindWindowById(srcID), SortBin):
            source = wx.FindWindowById(srcID)
            for tile in source.tiles[::-1]:
                if tile.obKey in obKeys and tile.selected:
                    source.tiles.remove(tile)
                    source.sizer.Detach(tile)
                    tile.Reparent(self)
                    tile.bin = self
                    if pos == 'first':
                        self.tiles.insert(0, tile)
                        self.sizer.Insert(0, tile, 0, wx.ALL | wx.EXPAND, 1)
                    else:
                        self.tiles.append(tile)
                        self.sizer.Add(tile, 0, wx.ALL | wx.EXPAND, 1)
                    if deselect:
                        tile.Deselect()
            source.UpdateSizer()
            source.UpdateQuantity()
        else:
            imgSet = self.tile_collection.GetTiles(obKeys, (self.classifier or self), priority,
                                                   display_whole_image=display_whole_image)
            for i, obKey, imgs in zip(list(range(len(obKeys))), obKeys, imgSet):
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
                wx.CallAfter(t.Destroy) # Call After?
        wx.CallAfter(self.UpdateSizer)
        self.UpdateQuantity()

    def RemoveSelectedTiles(self):
        for tile in self.Selection():
            self.tiles.remove(tile)
            # Destroying removes from sizer automatically
            wx.CallAfter(tile.Destroy)
        wx.CallAfter(self.UpdateSizer)
        self.UpdateQuantity()

    def RemoveDuplicateTiles(self):
        seen = set()
        count = 0
        for tile in self.tiles[::-1]:
            if tile.obKey in seen:
                self.tiles.remove(tile)
                wx.CallAfter(tile.Destroy)
                count += 1
            else:
                seen.add(tile.obKey)
        logging.info(f"Removed {count} duplicates from {self.label}")
        wx.CallAfter(self.UpdateSizer)
        self.UpdateQuantity()

    def Clear(self):
        self.RemoveKeys(self.GetObjectKeys())

    def find_selected_tile_for_key(self, obkey):
        for t in self.tiles:
            if t.obKey == obkey and t.selected:
                return t

    def ReceiveDrop(self, srcID, obKeys):
        # Generate a closure to fix the issue, that images dragged into the own bin are deleted
        # Add back the deleted images after deletion
        def hack(obKeys):
            def closure():
                if self.classifier:
                    self.AddObjects(obKeys, self.classifier.chMap, srcID=srcID)
                else:
                    self.AddObjects(obKeys)
            return closure

        closure = hack(obKeys)
        if srcID == self.GetId() or self.label == "image gallery":
            # wx.CallAfter(closure)
            return wx.DragNone
        self.DeselectAll()
        closure()
        [tile.Select() for tile in self.tiles if tile.obKey in obKeys]
        self.SetFocusIgnoringChildren() # prevent children from getting focus (want bin to catch key events)
        #self.classifier.UpdateTrainingSet() # Update TrainingSet after each drop (very slow)
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
        if not evt.ShiftDown():
            self.anchor = (evt.x, evt.y)
            self.SetFocusIgnoringChildren() # prevent children from getting focus (want bin to catch key events)

    def OnMotion(self, evt):
        if evt.ShiftDown() or not self.anchor:
            return
        if not evt.LeftIsDown():
            self.anchor = None
            self.dragging = False
            self.selecting.clear()
            return
        if not self.dragging and evt.Position != self.anchor:
            self.dragging = True
        self.SetFocusIgnoringChildren()
        self.selectbox = wx.Rect(self.anchor, evt.Position)
        for tile in self.tiles:
            tilebox = tile.GetRect()
            if tile in self.selecting:
                if not self.selectbox.Intersects(tilebox):
                    tile.Deselect()
                    self.selecting.remove(tile)
            else:
                if not tile.selected and self.selectbox.Intersects(tilebox):
                    tile.Select()
                    self.selecting.add(tile)
        self.Refresh()

    def OnPaint(self, evt):
        # self.SetClientSize((self.sizer.GetSize()))
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen("WHITE", 1, style=wx.PENSTYLE_SHORT_DASH))
        dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
        if self.selectbox:
            dc.DrawRectangle(self.selectbox)

    def OnLeftUp(self, evt):
        ''' Deselect all tiles unless shift is held. '''
        self.anchor = None
        self.selecting.clear()
        self.selectbox = None
        self.Refresh()
        if not self.dragging:
            self.SetFocusIgnoringChildren() # prevent children from getting focus (want bin to catch key events)
            if not evt.ShiftDown():
                self.DeselectAll()
        self.dragging = False

    def OnTileUpdated(self, evt):
        ''' When the tile loader returns the cropped image update the tile. '''
        self.UpdateTile(evt.data)
            
    def UpdateTile(self, obKey):
        ''' Called when image data is available for a specific tile. '''
        for t in self.tiles:
            if t.obKey == obKey:
                t.UpdateBitmap()
        if p.classification_type == 'image':
            self.sizer.RecalcSizes()
            self.UpdateSizer()

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
            logging.info("Error: Could not update Quantity!")



if __name__ == '__main__':
    app = wx.App()
 
    p.show_load_dialog()    
    from . import datamodel
    dm = datamodel.DataModel()
    
    f = wx.Frame(None)
    sb = SortBin(f)
    f.Show()
    sb.AddObjects(dm.GetRandomObject(50))

    app.MainLoop()
