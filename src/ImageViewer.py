
import wx
import ImageTools
from Properties import Properties
from ImagePanel import ImagePanel
from ImageControlPanel import ImageControlPanel

p = Properties.getInstance()


class ImageViewer(wx.Frame):
    '''
    A frame that takes a list of numpy arrays representing image channels 
    and merges and displays them as a single image.
    Menus are provided to change the RGB mapping of each channel passed in.
    Note: chMap is passed by reference by default, this means that the caller
       of ImageViewer can have it's own chMap (if any) updated by changes
       made in the viewer.  Otherwise pass in chMap[:] for a copy.
    '''
    def __init__(self, imgs, chMap, parent=None, title='Image Viewer'):
        '''
        imgs  : [numpy.array(dtype=float32), ... ]
        chMap : ['color', ...]
        chMap defines the colors that will be mapped to the corresponding
           image channels in imgs
        NOTE: imgs lists must be of the same length.
        '''
        
        h,w = imgs[0].shape

        wx.Frame.__init__(self, parent, wx.NewId(), title, size=(w,h))
        
        self.chMap       = chMap
        self.toggleChMap = chMap[:]
        self.sw = wx.ScrolledWindow(self)
        self.imagePanel  = ImagePanel(imgs, chMap, self.sw)
        
        self.SetMenuBar(wx.MenuBar())
        self.CreateChannelMenus()
        self.CreateMenus()
        self.SetClientSize((w,h))
        self.Centre()
        
        self.sw.SetScrollbars(1,1,w,h)
        
        self.Bind(wx.EVT_CHAR, self.OnKey)
        self.Bind(wx.EVT_MENU, self.OnShowImageControls, self.imageControlsMenuItem)
        self.imagePanel.Bind(wx.EVT_SIZE, self.OnResizeImagePanel)
        

    def CreateMenus(self):
        self.DisplayMenu = wx.Menu()
        self.imageControlsMenuItem = wx.MenuItem(parentMenu=self.DisplayMenu, id=wx.NewId(), text='Image Controls', help='Launches a control panel for adjusting image brightness, size, etc.')
        self.DisplayMenu.AppendItem(self.imageControlsMenuItem)
        self.GetMenuBar().Append(self.DisplayMenu, 'Display')


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
        if keycode == wx.WXK_ESCAPE:
            self.Destroy()
        if evt.ControlDown():
            chIdx = evt.GetKeyCode()-49
            if len(self.chMap) > chIdx >= 0:   # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
                    
                
    def OnShowImageControls(self, evt):
        self.imageControlFrame = wx.Frame(self)
        ImageControlPanel(self.imageControlFrame, self.imagePanel)
        self.imageControlFrame.Show(True)
        
        
    def OnResizeImagePanel(self, evt):
        self.sw.SetVirtualSize(evt.GetSize())
        
            
    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)
            
        
            
        


if __name__ == "__main__":
    p.LoadFile('../properties/nirht_test.properties')
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
        frame = ImageViewer(imgs=imgs, chMap=p.image_channel_colors, title=str(obKey[:-1]) )
        frame.Show(True)
           
    app.MainLoop()
