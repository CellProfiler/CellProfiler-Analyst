from DBConnect import DBConnect
from DataModel import DataModel
from ImageControlPanel import *
from ImagePanel import ImagePanel
from Properties import Properties
from matplotlib.pyplot import cm
import numpy
import ImageTools
import cPickle
import wx

p = Properties.getInstance()
db = DBConnect.getInstance()
dm = DataModel.getInstance()

class ImageViewerPanel(ImagePanel):
    '''
    Create a ImagePanel subclass that does selection.
    '''
    def __init__(self, imgs, chMap, parent, scale=1.0, brightness=1.0):
        super(ImageViewerPanel, self).__init__(imgs, chMap, parent, scale, brightness)
        self.selectedPoints = []
        self.classes        = {}  # {'Positive':[(x,y),..], 'Negative': [(x2,y2),..],..}
        self.classVisible   = {}
    
    def OnPaint(self, evt):
        dc = super(ImageViewerPanel, self).OnPaint(evt)
        # Draw colored boxes at each classified point
        if self.classes:
            for (name, cl), color in zip(self.classes.items(), self.colors):
                if self.classVisible[name]:
                    dc.BeginDrawing()
                    for (x,y) in cl:
                        x = x * self.scale - 2
                        y = y * self.scale - 2
                        w = h = 4
                        dc.SetPen(wx.Pen(color,1))
                        dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                        dc.DrawRectangle(x,y,w,h)
                        dc.DrawRectangle(x-1,y-1,6,6)
                    dc.EndDrawing()
        # Draw small white boxes at each selected point
        for (x,y) in self.selectedPoints:
            x = x * self.scale - 3
            y = y * self.scale - 3
            w = h = 6
            dc.BeginDrawing()
            dc.SetPen(wx.Pen("WHITE",1))
            dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
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
        self.classes = classes
        vals = numpy.arange(float(len(self.classes))) / len(self.classes)
        if len(vals) > 0:
            vals += (1.0 - vals[-1]) / 2
        self.colors = [numpy.array(cm.jet(val))*255 for val in vals]

        self.classVisible = {}
        for className in classes.keys():
            self.classVisible[className] = True 
        self.Refresh()
        
    def ToggleClass(self, className, show):
        self.classVisible[className] = show
        self.Refresh()



class ImageViewer(wx.Frame):
    '''
    A frame that takes a list of numpy arrays representing image channels 
    and merges and displays them as a single image.
    Menus are provided to change the RGB mapping of each channel passed in.
    Note: chMap is passed by reference by default, this means that the caller
       of ImageViewer can have it's own chMap (if any) updated by changes
       made in the viewer.  Otherwise pass in chMap[:] for a copy.
    '''
    def __init__(self, imgs, chMap, img_key=None, parent=None, title='Image Viewer', classifier=None, brightness=1.0, scale=1.0):
        '''
        imgs  : [numpy.array(dtype=float32), ... ]
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
        self.imagePanel  = ImageViewerPanel(imgs, chMap, self.sw, brightness=brightness, scale=scale)
        self.controls    = ImageControlPanel(self, self.imagePanel, brightness=brightness, scale=scale)
        self.selection   = []
        self.maxSize     = tuple([xy-50 for xy in wx.DisplaySize()])
        self.defaultFile = ''
        self.defaultPath = ''

        self.SetMenuBar(wx.MenuBar())
        fileMenu = wx.Menu()
        saveImageMenuItem = wx.MenuItem(parentMenu=fileMenu,id=wx.NewId(), text='Save Image')
        fileMenu.AppendItem(saveImageMenuItem)
        self.GetMenuBar().Append(fileMenu, 'File')
        self.CreateChannelMenus()
        
        self.SetClientSize( (min(self.maxSize[0], w*scale),
                             min(self.maxSize[1], h*scale+135)) )
        self.Centre()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sw, proportion=1, flag=wx.EXPAND)
        self.controlSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.controlSizer.Add(self.controls, proportion=1, flag=wx.EXPAND)
        sizer.Add(self.controlSizer)
        self.SetSizer(sizer)
        
        self.sw.SetScrollbars(1,1,w*scale,h*scale)
        
        self.Bind(wx.EVT_MENU, self.OnSaveImage, saveImageMenuItem)
        self.imagePanel.Bind(wx.EVT_KEY_UP, self.OnKey)
        self.imagePanel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.imagePanel.Bind(wx.EVT_SIZE, self.OnResizeImagePanel)


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
            if keycode == ord('W'):
                self.Destroy()
            elif keycode == ord('Q'):
                self.Destroy()
            elif keycode == ord('S'):
                self.OnSaveImage(evt)
            elif keycode == ord('A'):
                self.SelectAll()
            elif keycode == ord('D'):
                self.DeselectAll()
            elif len(self.chMap) > chIdx >= 0:   # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
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
        coordList = db.GetAllObjectCoordsFromImage(self.img_key)
        self.selection = dm.GetObjectsFromImage(self.img_key)
        self.imagePanel.SetSelectedPoints(coordList)
        
        
    def DeselectAll(self):
        self.selection = []
        self.imagePanel.DeselectAll()

    
    def SetClasses(self, classCoords):
        self.imagePanel.SetClassPoints(classCoords)
        self.classControls = ImageViewerControlPanel(self, self.imagePanel,
                                                     classCoords, self.imagePanel.colors)
        self.controlSizer.Add(self.classControls, proportion=1, flag=wx.EXPAND)
        self.Refresh()
        self.Layout()
        
        
    def OnLeftDown(self, evt):
        if self.img_key:
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


if __name__ == "__main__":
    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('../properties/2008_07_29_Giemsa.properties')
    app = wx.PySimpleApp()
    from DataModel import DataModel
    import ImageTools
    
    db = DBConnect.getInstance()
    db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
    dm = DataModel.getInstance()
    dm.PopulateModel()
    
    for i in xrange(1):
        obKey = dm.GetRandomObject()
        print obKey
        imgs = ImageTools.FetchImage(obKey[:-1])
        frame = ImageViewer(imgs=imgs, img_key=obKey[:-1], chMap=p.image_channel_colors, title=str(obKey[:-1]) )
        frame.Show(True)
    
    classCoords = {'a':[(10,10),(20,20)],
                   'b':[(100,10),(200,20)] }
    frame.SetClasses(classCoords)
    
    ImageTools.SaveBitmap(frame.imagePanel.bitmap, '/Users/afraser/Desktop/TEST.png')
           
    app.MainLoop()
