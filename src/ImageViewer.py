from DBConnect import DBConnect
from ImageControlPanel import ImageControlPanel
from ImagePanel import ImagePanel
from Properties import Properties
import SortBin
import ImageTools
import cPickle
import wx

p = Properties.getInstance()
db = DBConnect.getInstance()

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
        self.imagePanel  = ImagePanel(imgs, chMap, self.sw, brightness=brightness, scale=scale)
        self.controls    = ImageControlPanel(self, self.imagePanel, brightness=brightness, scale=scale)
        self.selection   = []
        self.maxSize     = tuple([xy-50 for xy in wx.DisplaySize()])

        self.SetMenuBar(wx.MenuBar())
        self.CreateChannelMenus()
        self.SetClientSize( (min(self.maxSize[0], w*scale),
                             min(self.maxSize[1], h*scale+135)) )
        self.Centre()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sw, proportion=1, flag=wx.EXPAND)
        sizer.Add(self.controls, proportion=0, flag=wx.EXPAND)
        self.SetSizer(sizer)
        
        self.sw.SetScrollbars(1,1,w*scale,h*scale)
        
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
            elif len(self.chMap) > chIdx >= 0:   # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
        
            
    def OnResizeImagePanel(self, evt):
        self.sw.SetVirtualSize(evt.GetSize())
        
            
    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)
    
        
    def OnLeftDown(self, evt):
        if self.img_key:
            x = evt.GetPosition().x / self.imagePanel.scale
            y = evt.GetPosition().y / self.imagePanel.scale
            obkey = db.GetObjectNear(self.img_key, x, y)

            # update selection
            if not evt.ShiftDown():
                self.selection = set([obkey])
            else:
                if obkey in self.selection:
                    self.selection.remove(obkey)
                else:
                    self.selection.add(obkey)

            # update drawing
            if self.selection:
                self.imagePanel.SelectPoints([db.GetObjectCoords(k) for k in self.selection])
                # start drag
                source = wx.DropSource(self)
                # wxPython crashes unless the data object is assigned to a variable.
                data_object = wx.CustomDataObject("ObjectKey")
                data_object.SetData(cPickle.dumps(self.selection))
                source.SetData(data_object)
                result = source.DoDragDrop(flags=wx.Drag_DefaultMove)
                if result is 0:
                    pass

    
            


if __name__ == "__main__":
    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('../properties/2008_07_29_Giemsa.properties')
    app = wx.PySimpleApp()
    from DataModel import DataModel
    from DBConnect import DBConnect
    from ImageCollection import ImageCollection
    db = DBConnect.getInstance()
    db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
    dm = DataModel.getInstance()
    dm.PopulateModel()
    IC = ImageCollection.getInstance(p)
    
    for i in xrange(1):
        obKey = dm.GetRandomObject()
        print obKey
        imgs = IC.FetchImage(obKey[:-1])
        frame = ImageViewer(imgs=imgs, img_key=obKey[:-1], chMap=p.image_channel_colors, title=str(obKey[:-1]) )
        frame.Show(True)
           
    app.MainLoop()
