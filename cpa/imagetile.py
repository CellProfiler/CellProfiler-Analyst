'''
A special image panel meant to be dragged and dropped.
'''
from dbconnect import DBConnect
from imagepanel import ImagePanel
from properties import Properties
import imagetools
import cPickle
import wx

from trainingset import CellCache

p = Properties.getInstance()
db = DBConnect.getInstance()


class ImageTileDropTarget(wx.DropTarget):
    ''' ImageTiles pass drop events to their parent bin. '''
    def __init__(self, tile):
        self.data = wx.CustomDataObject("ObjectKey")
        wx.DropTarget.__init__(self, self.data)
        self.tile = tile
    
    def OnData(self, x, y, dragres):
        if not self.GetData():
            return wx.DragNone
        draginfo = self.data.GetData()
        srcID, obKeys = cPickle.loads(draginfo)
        if not obKeys:
            return wx.DragNone
        return self.tile.bin.ReceiveDrop(srcID, obKeys) 


class ImageTile(ImagePanel):
    '''
    ImageTiles are thumbnail images that can be dragged and dropped
    between SortBins.
    '''
    def __init__(self, bin, obKey, images, chMap, selected=False, 
                 scale=1.0, brightness=1.0, contrast=None):
        ImagePanel.__init__(self, images, chMap, bin, scale=scale, 
                            brightness=brightness, contrast=contrast)
        self.SetDropTarget(ImageTileDropTarget(self))

        self.bin         = bin             # the SortBin this object belongs to
        self.classifier  = bin.classifier  # Classifier needs to capture the mouse on tile selection
        self.obKey       = obKey           # (table, image, object)
        self.selected    = selected        # whether or not this tile is selected
        self.leftPressed = False
        self.showCenter  = False
        self.popupMenu   = None

        self.cache = CellCache.getInstance()

        
        self.MapChannels(chMap)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)     # Show images on double click
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseOver)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseOut)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        dc = ImagePanel.OnPaint(self, evt)
        if self.showCenter:
            dc.BeginDrawing()
            dc.SetLogicalFunction(wx.XOR)
            dc.SetPen(wx.Pen("WHITE",1))
            dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
            dc.DrawRectangle(self.bitmap.Width/2.-1, self.bitmap.Height/2.-1, 3, 3)
            dc.EndDrawing()
        return dc

    def CreatePopupMenu(self):
        if self.popupMenu is not None:
            return
        popupMenuItems = ['View full images of selected',
                          'View predicted probability scores',
                          'Select all\tCtrl+A',
                          'Deselect all\tCtrl+D',
                          'Invert selection\tCtrl+I',
                          'Remove selected\tDelete']
        self.popupItemIndexById = {}
        self.popupMenu = wx.Menu()
        for i, item in enumerate(popupMenuItems):
            # need to minimize the use of wx.NewId here
            id = wx.NewId()
            self.popupItemIndexById[id] = i
            self.popupMenu.Append(id,item)
        self.popupMenu.Bind(wx.EVT_MENU,self.OnSelectFromPopupMenu)
        
    def OnRightDown(self, evt):
        ''' On right click show popup menu. '''
        self.CreatePopupMenu()
        self.PopupMenu(self.popupMenu, evt.GetPosition())
    
    def OnSelectFromPopupMenu(self, evt):
        ''' Handles selections from the popup menu. '''
        choice = self.popupItemIndexById[evt.GetId()]
        if choice == 0:
            for obKey in self.bin.SelectedKeys():
                imViewer = imagetools.ShowImage(obKey[:-1], self.chMap[:], parent=self.classifier,
                                        brightness=self.brightness, contrast=self.contrast,
                                        scale=self.scale)
                imViewer.imagePanel.SelectPoint(db.GetObjectCoords(obKey))
        elif choice == 1:
            self.DisplayProbs()
        elif choice == 2:
            self.bin.SelectAll()
        elif choice == 3:
            self.bin.DeselectAll()
        elif choice == 4:
            self.bin.InvertSelection()
        elif choice == 5:
            self.bin.RemoveSelectedTiles()

    def DisplayProbs(self):
        try:
            # Get the scikit learn classifier model
            clf = self.classifier.algorithm
            if clf.trained:
                    # Get the probability scores and visualise them in a histogramm
                    #for k in self.bin.SelectedKeys():
                    k = self.obKey
                    def get_data(k):
                        d = self.cache.get_object_data(k)
                        return d

                    values = [get_data(k)]
                    y_score = []
                    y_score = clf.PredictProba(values)        

                    y_score = y_score[0] # Flatten array
                    self.classifier.PlotProbs(y_score)
            else:
                dlg = wx.MessageDialog(self,'Please train your classifier first', 'No probability scores available', style=wx.OK)
                dlg.ShowModal()
        except:
            dlg = wx.MessageDialog(self,'Sorry. The selected classifier does not provide this functionality', 'No probability scores available', style=wx.OK)
            dlg.ShowModal()
        
    def OnDClick(self, evt):
        imViewer = imagetools.ShowImage(self.obKey[:-1], list(self.chMap), parent=self.classifier,
                                        brightness=self.brightness, contrast=self.contrast,
                                        scale=self.scale)
        imViewer.imagePanel.SelectPoint(db.GetObjectCoords(self.obKey))
        
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
        if not evt.ShiftDown() and not self.selected:
            self.bin.DeselectAll()
            self.Select()
        elif evt.ShiftDown():
            self.ToggleSelect()

    def OnLeftUp(self, evt):
        inMotion = False
            
    def OnMouseOver(self, evt):
        self.showCenter = True
        self.Refresh()
        
    def OnMouseOut(self, evt):
        self.showCenter = False
        self.leftPressed = False
        self.Refresh()
            
    def OnMotion(self, evt):
        if not evt.LeftIsDown() or not self.leftPressed:
            return
        self.bin.SetFocusIgnoringChildren()
        # Removed for Linux compatibility
        #cursorImg = self.bitmap.ConvertToImage()
        #cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, int(self.bitmap.Size[0])/2)
        #cursorImg.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, int(self.bitmap.Size[1])/2)
        #cursor = wx.CursorFromImage(cursorImg)
        
        # wx crashes unless the data object is assigned to a variable.
        data_object = wx.CustomDataObject("ObjectKey")
        data_object.SetData(cPickle.dumps( (self.bin.GetId(), self.bin.SelectedKeys()) ))
        source = wx.DropSource(self)#, copy=cursor, move=cursor)
        source.SetData(data_object)
        result = source.DoDragDrop(wx.Drag_DefaultMove)
        # def cb():
        #     self.bin.RemoveKeys(self.bin.SelectedKeys()) # Hack to fix drag move
        # wx.CallAfter(cb)
        #if result is wx.DragMove:
        self.bin.RemoveSelectedTiles() # Removes images which stays during drag and drop
        self.bin.UpdateSizer()
        self.bin.UpdateQuantity()
    
    def OnSize(self, evt):
        self.SetClientSize(evt.GetSize())
        evt.Skip()

