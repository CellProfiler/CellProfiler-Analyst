'''
ImageViewer.py
authors: afraser
'''

import wx
import numpy
import ImageTools
from Properties import Properties

p = Properties.getInstance()



# TODO: broadcast color-mappings to other windows
#   these should probably be in ImageTools (?)
EVT_COLOR_MAP_CHANGED_ID = wx.NewId()

def EVT_COLOR_MAP_CHANGED(win, func):
    win.Connect(-1, -1, EVT_COLOR_MAP_CHANGED_ID, func)
   
class ColorMapChangedEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COLOR_MAP_CHANGED_ID)
        self.data = data
        
        
        
        

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
        
        wx.Frame.__init__(self, parent, wx.NewId(), title, size=imgs[0].shape)

        self.chMap       = chMap
        self.toggleChMap = chMap[:]
        self.images      = imgs      # image channel arrays
        self.bitmap      = ImageTools.MergeToBitmap(imgs, self.chMap)   # displayed wx.Bitmap
        
        self.sw = wx.ScrolledWindow(self)
        self.SetMenuBar(wx.MenuBar())
        self.CreateChannelMenus()
        w,h = self.bitmap.GetSize()
        self.SetClientSize((w,h))
        self.Centre()
        self.sw.SetScrollbars(1,1,w,h)
        wx.StaticBitmap(self.sw, -1, self.bitmap)
        
        self.Bind(wx.EVT_KEY_UP, self.OnKey)



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
        (chIdx,color) = self.chMapById[evt.GetId()]
        self.chMap[chIdx] = color
        if color.lower() != 'none':
            self.toggleChMap[chIdx] = color
        self.MapChannels(self.chMap)

        
    def MapChannels(self, chMap):
        self.chMap = chMap
        
        # TODO: Need to update color menu selections
        # broadcast to all windows open?
#        wx.PostEvent(notify_window, ColorMapChangedEvent(chMap))
        
        self.bitmap = ImageTools.MergeToBitmap(self.images, self.chMap)
        wx.StaticBitmap(self.sw, -1, self.bitmap)
        self.Refresh()
    

    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.Destroy()
            
        if evt.ControlDown():
            chIdx = evt.GetKeyCode()-49
            if len(self.chMap) > chIdx >= 0:   # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
            
            
    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)
            
            
#    def IdentifyObjects(self, posns):
#        self.bitmap = ImageTools.MergeToBitmap




if __name__ == "__main__":
    p.LoadFile('../properties/nirht.properties')
    app = wx.PySimpleApp()
    from DataModel import DataModel
    from DBConnect import DBConnect
    from ImageCollection import ImageCollection
    db = DBConnect.getInstance()
    db.Connect(db_host="imgdb01", db_user="cpadmin", db_passwd="cPus3r", db_name="cells")
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
