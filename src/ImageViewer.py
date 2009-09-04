from DBConnect import DBConnect
from DataModel import DataModel
from ImageControlPanel import *
from ImagePanel import ImagePanel
from Properties import Properties
import numpy as np
import ImageTools
import cPickle
import wx

p = Properties.getInstance()
db = DBConnect.getInstance()

CL_NUMBERED = 'numbered'
CL_COLORED = 'colored'

ID_SAVE_IMAGE = wx.NewId()
ID_EXIT = wx.NewId()

class ImageViewerPanel(ImagePanel):
    '''
    ImagePanel subclass that does selection.
    '''
    def __init__(self, imgs, chMap, parent, scale=1.0, brightness=1.0, contrast=None):
        super(ImageViewerPanel, self).__init__(imgs, chMap, parent, scale, brightness, contrast=contrast)
        self.selectedPoints = []
        self.classes        = {}  # {'Positive':[(x,y),..], 'Negative': [(x2,y2),..],..}
        self.classVisible   = {}
        self.class_rep    = CL_COLORED
    
    def OnPaint(self, evt):
        dc = super(ImageViewerPanel, self).OnPaint(evt)
        font = self.GetFont()
        font.SetPixelSize((6,12))
        dc.SetFont(font)
        dc.SetTextForeground('WHITE')

        # Draw class numbers over each object
        if self.classes:
            for (name, cl), clnum, color in zip(self.classes.items(), self.class_nums, self.colors):
                if self.classVisible[name]:
                    dc.BeginDrawing()
                    for (x,y) in cl:
                        if self.class_rep==CL_NUMBERED:
                            x = x * self.scale - 3
                            y = y * self.scale - 6
                            dc.DrawText(clnum, x, y)
                        else:
                            x = x * self.scale - 2
                            y = y * self.scale - 2
                            w = h = 4
                            dc.SetPen(wx.Pen(color,1))
                            dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                            dc.DrawRectangle(x,y,w,h)
                            dc.DrawRectangle(x-1,y-1,6,6)
                    dc.EndDrawing()
                    
        # Draw small white (XOR) boxes at each selected point
        dc.SetLogicalFunction(wx.XOR)
        dc.SetPen(wx.Pen("WHITE",1))
        dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
        for (x,y) in self.selectedPoints:
            x = x * self.scale - 3
            y = y * self.scale - 3
            w = h = 6
            dc.BeginDrawing()
            dc.DrawRectangle(x,y,w,h)
            dc.EndDrawing()
        return dc
    
    def SetSelectedPoints(self, posns):
        self.selectedPoints = posns
        self.Refresh()
                        
    def SelectPoint(self, pos):
        self.selectedPoints += [pos]
        self.Refresh()
        
    def DeselectPoint(self, pos):
        self.selectedPoints.remove(pos)
        self.Refresh()
        
    def TogglePointSelection(self, pos):
        if pos in self.selectedPoints:
            self.DeselectPoint(pos)
        else:
            self.SelectPoint(pos)
        
    def DeselectAll(self):
        self.selectedPoints = []
        self.Refresh()

    def SetClassPoints(self, classes):
        from matplotlib.pyplot import cm
        self.classes = classes
        vals = np.arange(float(len(self.classes))) / len(self.classes)
        if len(vals) > 0:
            vals += (1.0 - vals[-1]) / 2
        self.colors = [np.array(cm.jet(val))*255 for val in vals]
        self.class_nums = [str(i+1) for i,_ in enumerate(classes)]

        self.classVisible = {}
        for className in classes.keys():
            self.classVisible[className] = True 
        self.Refresh()
        
    def ToggleClassRepresentation(self):
        if self.class_rep==CL_NUMBERED:
            self.class_rep = CL_COLORED
        else:
            self.class_rep = CL_NUMBERED
        
    def ToggleClass(self, className, show):
        self.classVisible[className] = show
        self.Refresh()



class ImageViewer(wx.Frame):
    '''
    A frame that takes a list of np arrays representing image channels 
    and merges and displays them as a single image.
    Menus are provided to change the RGB mapping of each channel passed in.
    Note: chMap is passed by reference by default, this means that the caller
       of ImageViewer can have it's own chMap (if any) updated by changes
       made in the viewer.  Otherwise pass in a copy.
    '''
    def __init__(self, imgs, chMap, img_key=None, parent=None, title='Image Viewer', 
                 classifier=None, brightness=1.0, scale=1.0, contrast=None, 
                 classCoords=None):
        '''
        imgs  : [np.array(dtype=float32), ... ]
        chMap : ['color', ...]
            defines the colors that will be mapped to the corresponding
            image channels in imgs
        img_key : key for this image in the database, to allow selection of cells
        NOTE: imgs lists must be of the same length.
        '''
        
        h,w = imgs[0].shape
        
        wx.Frame.__init__(self, parent, wx.NewId(), title)
                
        self.chMap       = chMap
        self.toggleChMap = chMap[:]
        self.img_key     = img_key
        self.classifier  = parent
        self.sw          = wx.ScrolledWindow(self)
        self.imagePanel  = ImageViewerPanel(imgs, chMap, self.sw, brightness=brightness, scale=scale, contrast=contrast)
        self.cp = cp     = wx.CollapsiblePane(self, label='Show controls', style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.controls    = ImageControlPanel(cp.GetPane(), self.imagePanel, brightness=brightness, scale=scale, contrast=contrast)
        self.selection   = []
        self.maxSize     = tuple([xy-50 for xy in wx.DisplaySize()])
        self.defaultFile = ''
        self.defaultPath = ''

        self.SetMenuBar(wx.MenuBar())
        # File Menu
        fileMenu = wx.Menu()
        saveImageMenuItem = wx.MenuItem(parentMenu=fileMenu, id=ID_SAVE_IMAGE, text='Save Image\tCtrl+S')
        exitMenuItem = wx.MenuItem(parentMenu=fileMenu, id=ID_EXIT, text='Exit\tCtrl+Q')
        fileMenu.AppendItem(saveImageMenuItem)
        fileMenu.AppendSeparator()
        fileMenu.AppendItem(exitMenuItem)
        self.GetMenuBar().Append(fileMenu, 'File')
        # View Menu
        viewMenu = wx.Menu()
        self.classViewMenuItem = wx.MenuItem(parentMenu=viewMenu, id=wx.NewId(), text='View phenotypes as numbers')
        viewMenu.AppendItem(self.classViewMenuItem)
        self.GetMenuBar().Append(viewMenu, 'View')
        self.CreateChannelMenus()
        
        self.SetClientSize( (min(self.maxSize[0], w*scale),
                             min(self.maxSize[1], h*scale+55)) )
        self.Centre()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sw, proportion=1, flag=wx.EXPAND)
        sizer.Add(cp, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
        self.SetSizer(sizer)
        
        self.sw.SetScrollbars(1,1,w*scale,h*scale)
        
        if classCoords is not None:
            self.SetClasses(classCoords)
        
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, cp)
        self.Bind(wx.EVT_MENU, self.OnSaveImage, saveImageMenuItem)
        self.Bind(wx.EVT_MENU, self.OnChangeClassRepresentation, self.classViewMenuItem)
        wx.EVT_MENU(self, ID_EXIT, lambda evt:self.Close())
        self.imagePanel.Bind(wx.EVT_KEY_UP, self.OnKey)
        self.imagePanel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.imagePanel.Bind(wx.EVT_SIZE, self.OnResizeImagePanel)


    def OnPaneChanged(self, evt=None):
        self.Layout()
        if self.cp.IsExpanded():
            self.cp.SetLabel('Hide controls')
        else:
            self.cp.SetLabel('Show controls')
            

    def CreateChannelMenus(self):
        ''' Create color-selection menus for each channel. '''
        chIndex=0
        self.chMapById = {}
        for channel, setColor in zip(p.image_channel_names, self.chMap):
            channel_menu = wx.Menu()
            for color in ['Red', 'Green', 'Blue', 'Cyan', 'Magenta', 'Yellow', 'Gray', 'None']:
                id = wx.NewId()
                self.chMapById[id] = (chIndex,color)
                if color.lower() == setColor.lower():
                    item = channel_menu.AppendRadioItem(id,color).Check()
                else:
                    item = channel_menu.AppendRadioItem(id,color)
                self.Bind(wx.EVT_MENU, self.OnMapChannels, item)
            channel_menu.InsertSeparator(3)
            channel_menu.InsertSeparator(8)
            self.GetMenuBar().Append(channel_menu, channel)
            chIndex+=1


    def OnMapChannels(self, evt):
        if evt.GetId() in self.chMapById.keys():
            (chIdx,color) = self.chMapById[evt.GetId()]
            self.chMap[chIdx] = color
            if color.lower() != 'none':
                self.toggleChMap[chIdx] = color
            self.MapChannels(self.chMap)


    def MapChannels(self, chMap):
        self.chMap = chMap
        self.imagePanel.MapChannels(chMap)


    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        keycode = evt.GetKeyCode()
        chIdx = keycode-49
        if evt.CmdDown() or evt.ControlDown():
            if keycode == ord('A'):
                self.SelectAll()
            elif keycode == ord('D'):
                self.DeselectAll()
            elif keycode == ord('J'):
                self.imagePanel.SetContrastMode('None')
                self.controls.SetContrastMode('None')
            elif keycode == ord('K'):
                self.imagePanel.SetContrastMode('Auto')
                self.controls.SetContrastMode('Auto')
            elif keycode == ord('L'):
                self.imagePanel.SetContrastMode('Log')
                self.controls.SetContrastMode('Log')
            elif len(self.chMap) > chIdx >= 0:   # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
            else:
                evt.Skip()
        else:
            evt.Skip()
        
            
    def OnResizeImagePanel(self, evt):
        self.sw.SetVirtualSize(evt.GetSize())
        
            
    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)
            
            
    def SelectAll(self):
        if p.object_table:
            coordList = db.GetAllObjectCoordsFromImage(self.img_key)
            self.selection = db.GetObjectsFromImage(self.img_key)
            self.imagePanel.SetSelectedPoints(coordList)
        
        
    def DeselectAll(self):
        self.selection = []
        self.imagePanel.DeselectAll()

    
    def SetClasses(self, classCoords):
        self.imagePanel.SetClassPoints(classCoords)
        self.controls.SetClassPoints(classCoords)
        self.Refresh()
        self.Layout()
        
        
    def OnLeftDown(self, evt):
        if self.img_key and p.object_table:
            x = evt.GetPosition().x / self.imagePanel.scale
            y = evt.GetPosition().y / self.imagePanel.scale
            obKey = db.GetObjectNear(self.img_key, x, y)

            if not obKey: return
            
            # update selection
            if not evt.ShiftDown():
                self.selection = [obKey]
                self.imagePanel.DeselectAll()
                self.imagePanel.TogglePointSelection(db.GetObjectCoords(obKey))
            else:
                if obKey not in self.selection:
                    self.selection += [obKey]
                else:
                    self.selection.remove(obKey)
                self.imagePanel.TogglePointSelection(db.GetObjectCoords(obKey))

            if self.selection:
                # start drag
                source = wx.DropSource(self)
                # wxPython crashes unless the data object is assigned to a variable.
                data_object = wx.CustomDataObject("ObjectKey")
                data_object.SetData(cPickle.dumps( (self.GetId(), self.selection) ))
                source.SetData(data_object)
                result = source.DoDragDrop(flags=wx.Drag_DefaultMove)
                if result is 0:
                    pass


    def OnSaveImage(self, evt):
        import os
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=self.defaultPath, defaultFile=self.defaultFile,
                                   wildcard='PNG file (*.png)|*.png|JPG file (*.jpg, *.jpeg)|*.jpg', 
                                   style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)
        if saveDialog.ShowModal()==wx.ID_OK:
            filename = str(saveDialog.GetPath())
            self.defaultPath, self.defaultFile = os.path.split(filename)
            format = os.path.splitext(filename)[-1]
            saveDialog.Destroy()
            if not format.upper() in ['.PNG','.JPG','.JPEG']:
                errdlg = wx.MessageDialog(self, 'Invalid file extension (%s)! File extension must be .PNG or .JPG.'%(format),
                                          "Invalid file extension", wx.OK|wx.ICON_EXCLAMATION)
                if errdlg.ShowModal() == wx.ID_OK:
                    return self.OnSaveImage(evt)
            if format.upper()=='.JPG':
                format = '.JPEG'
            ImageTools.SaveBitmap(self.imagePanel.bitmap, filename, format.upper()[1:])


    def OnChangeClassRepresentation(self, evt):
        self.classViewMenuItem.Text = 'View phenotypes as colors'
        self.imagePanel.ToggleClassRepresentation()

if __name__ == "__main__":
    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('../properties/2008_07_29_Giemsa.properties')
    app = wx.PySimpleApp()
    from DataModel import DataModel
    import ImageTools
    
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()
    dm.PopulateModel()
    
    for i in xrange(1):
        obKey = dm.GetRandomObject()
        imgs = ImageTools.FetchImage(obKey[:-1])
                    
        #imgs = [ImageTools.log_transform(im) for im in imgs]
#        imgs = [ImageTools.auto_contrast(im) for im in imgs]
        
#        f1 = ImageViewer(imgs=imgs, img_key=obKey[:-1], chMap=p.image_channel_colors, title=str(obKey[:-1]) )
#        f1.Show(True)
        f2 = ImageViewer(imgs=imgs, img_key=obKey[:-1], chMap=p.image_channel_colors, title=str(obKey[:-1]))
        f2.Show(True)
    
    classCoords = {'a':[(100,100),(200,200)],'b':[(200,100),(200,300)] }
    f2.SetClasses(classCoords)
    
    #ImageTools.SaveBitmap(frame.imagePanel.bitmap, '/Users/afraser/Desktop/TEST.png')
           
    app.MainLoop()
