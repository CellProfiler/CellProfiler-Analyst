#######################
# Notes: Christina 09.16.2011
# The following is an example of properties file data that work with this imageviewer:
#
#image_path_cols =  Image_PathName_OutlinedAxons,Image_PathName_SomaOutlines,Image_PathName_SkelDendrites,Image_PathName_SkelAxons,Image_PathName_ColorImage,Image_PathName_OrigD,Image_PathName_OrigA,Image_PathName_OrigN,Image_PathName_OutlinedDendrites
#image_file_cols = Image_FileName_OutlinedAxons,Image_FileName_SomaOutlines,Image_FileName_SkelDendrites,Image_FileName_SkelAxons,Image_FileName_ColorImage,Image_FileName_OrigD,Image_FileName_OrigA,Image_FileName_OrigN,Image_FileName_OutlinedDendrites
#image_names = OutlinedAxons,SomaOutlines,SkelDendrites,SkelAxons,ColorImage,OrigD,OrigA,OrigN,OutlinedDendrites
#channels_per_image  = 3,3,1,1,3,1,1,1,3
#image_channel_colors = none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, none, 
#########################

import cpa.helpmenu
from .dbconnect import *
from .datamodel import DataModel
from .imagecontrolpanel import *
from .imagepanel import ImagePanel
from .properties import Properties
from . import imagetools
import pickle
import logging
import numpy as np
import wx

p = Properties()
db = DBConnect()

REQUIRED_PROPERTIES = ['channels_per_image','image_channel_colors', 'object_name', 'image_names', 'image_id']

CL_NUMBERED = 'numbered'
CL_COLORED = 'colored'
ID_SELECT_ALL = wx.NewId()
ID_DESELECT_ALL = wx.NewId()

def get_classifier_window():
    from .classifier import ID_CLASSIFIER
    win = wx.FindWindowById(ID_CLASSIFIER)
    if win:
        return win
    wins = [x for x in wx.GetTopLevelWindows() if x.Name=='Classifier']
    if wins:
        return wins[0]
    else:
        return None


def rescale_image_coord_to_display(x, y):
    ''' Rescale coordinate to fit the rescaled image dimensions '''
    if not p.rescale_object_coords:
        return x,y
    x = x * p.image_rescale[0] / p.image_rescale_from[0]
    y = y * p.image_rescale[1] / p.image_rescale_from[1]
    return x,y

def rescale_display_coord_to_image(x, y):
    ''' Rescale coordinate to fit the display image dimensions '''
    if not p.rescale_object_coords:
        return x,y
    x = x * p.image_rescale_from[0] / p.image_rescale[0]
    y = y * p.image_rescale_from[1] / p.image_rescale[1]
    return x,y

class ImageViewerPanel(ImagePanel):
    '''
    ImagePanel with selection and object class labels. 
    '''
    def __init__(self, imgs, chMap, img_key, parent, scale=1.0, brightness=1.0, contrast=None):
        super(ImageViewerPanel, self).__init__(imgs, chMap, parent, scale, brightness, contrast=contrast, display_whole_image=True)
        self.selectedPoints = []
        self.classes        = {}  # {'Positive':[(x,y),..], 'Negative': [(x2,y2),..],..}
        self.classVisible   = {}
        self.class_rep      = CL_COLORED
        self.img_key        = img_key
        self.show_object_numbers = False

    def OnPaint(self, evt):
        dc = super(ImageViewerPanel, self).OnPaint(evt)
        font = self.GetFont()
        font.SetPixelSize((6,12))
        dc.SetFont(font)
        dc.SetTextForeground('WHITE')

        # Draw object numbers
        if self.show_object_numbers and p.object_table:
            dc.SetLogicalFunction(wx.XOR)
            for i, (x,y) in enumerate(self.ob_coords):
                x = x * self.scale - 6*(len('%s'%i)-1)
                y = y * self.scale - 6
                dc.DrawText('%s'%(i + 1), x, y)

        # Draw class numbers over each object
        if self.classes:
            for (name, cl), clnum, color in zip(list(self.classes.items()), self.class_nums, self.colors):
                if self.classVisible[name]:
                    for (x,y) in cl:
                        if self.class_rep==CL_NUMBERED:
                            dc.SetLogicalFunction(wx.XOR)
                            x = x * self.scale - 3
                            y = y * self.scale - 6
                            dc.DrawText(clnum, x, y)
                        else:
                            w = h = 4
                            x = x * self.scale - w/2
                            y = y * self.scale - h/2

                            dc.SetPen(wx.Pen(color,1))
                            dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                            dc.DrawRectangle(x,y,w,h)
                            dc.DrawRectangle(x-1,y-1,6,6)

        # Draw small white (XOR) boxes at each selected point
        dc.SetLogicalFunction(wx.XOR)
        dc.SetPen(wx.Pen("WHITE",1))
        dc.SetBrush(wx.Brush("WHITE", style=wx.TRANSPARENT))
        for (x,y) in self.selectedPoints:
            w = h = 6
            x = x * self.scale - w/2
            y = y * self.scale - h/2

            dc.DrawRectangle(x,y,w,h)
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
        if len(classes) == 0:
            logging.warn('There are no objects to classify in this image.')
            return
        from matplotlib.pyplot import cm
        self.classes = classes
        vals = np.arange(0, 1, 1. / len(classes))
        vals += (1.0 - vals[-1]) / 2
        self.colors = [np.array(cm.jet(val)) * 255 for val in vals]
        self.class_nums = [str(i+1) for i,_ in enumerate(classes)]

        self.classVisible = {}
        for className in classes.keys():
            self.classVisible[className] = True 
        self.Refresh()

    def ToggleObjectNumbers(self):
        self.show_object_numbers = not self.show_object_numbers
        if self.show_object_numbers:
            self.ob_coords = db.GetAllObjectCoordsFromImage(self.img_key)
        self.Refresh()

    def ToggleClassRepresentation(self):
        if self.class_rep==CL_NUMBERED:
            self.class_rep = CL_COLORED
        else:
            self.class_rep = CL_NUMBERED
        self.Refresh()

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
    def __init__(self, imgs=None, chMap=None, img_key=None, parent=None, title='Image Viewer', 
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
        wx.Frame.__init__(self, parent, -1, title)
        self.SetName('ImageViewer')
        self.SetBackgroundColour("white")
        self.img_key     = img_key
        self.classifier  = parent
        self.sw          = wx.ScrolledWindow(self)
        self.selection   = []
        self.maxSize     = tuple([xy-50 for xy in wx.DisplaySize()])
        self.defaultFile = 'MyImage.png'
        self.defaultPath = ''
        self.imagePanel  = None
        self.cp          = None
        self.controls    = None
        self.first_layout = True
        self.inspect_release = True

        if chMap is None:
            try:
                chMap = p.image_channel_colors
            except:
                pass

        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.CreateMenus()
        self.CreatePopupMenu()
        if imgs and chMap:
            self.SetImage(imgs, chMap, brightness, scale, contrast)
        else:
            self.OnOpenImage()
        self.DoLayout()
        self.Center()

        if classCoords is not None:
            self.SetClasses(classCoords)

    def AutoTitle(self):
        if p.plate_id and p.well_id:
            plate, well = db.execute('SELECT %s, %s FROM %s WHERE %s'%(p.plate_id, p.well_id, p.image_table, GetWhereClauseForImages([self.img_key])))[0]
            title = '%s %s, %s %s, image-key %s'%(p.plate_id, plate, p.well_id, well, str(self.img_key))
        else:
            title = 'image-key %s'%(str(self.img_key))
        self.SetTitle(title)

    def CreatePopupMenu(self):
        self.popupMenu = wx.Menu()
        self.sel_all = wx.MenuItem(self.popupMenu, ID_SELECT_ALL, 'Select all\tCtrl+A')
        self.deselect = wx.MenuItem(self.popupMenu, ID_DESELECT_ALL, 'Deselect all\tCtrl+D')
        self.popupMenu.Append(self.sel_all)
        self.popupMenu.Append(self.deselect)
        accelerator_table = wx.AcceleratorTable([(wx.ACCEL_CMD,ord('A'),ID_SELECT_ALL),
                                                 (wx.ACCEL_CMD,ord('D'),ID_DESELECT_ALL),])
        self.SetAcceleratorTable(accelerator_table)

    def SetImage(self, imgs, chMap=None, brightness=1, scale=1, contrast=None):
        self.AutoTitle()
        self.chMap = chMap or p.image_channel_colors
        self.toggleChMap = self.chMap[:]
        if self.imagePanel:
            self.imagePanel.Destroy()
        self.imagePanel = ImageViewerPanel(imgs, self.chMap, self.img_key, 
                                           self.sw, brightness=brightness, 
                                           scale=scale, contrast=contrast)
        self.imagePanel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.imagePanel.Bind(wx.EVT_SIZE, self.OnResizeImagePanel)
        self.imagePanel.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

    def CreateMenus(self):
        self.SetMenuBar(wx.MenuBar())
        # File Menu
        self.fileMenu = wx.Menu()
        self.openImageMenuItem = self.fileMenu.Append(-1, item='Open Image\tCtrl+O')
        self.saveImageMenuItem = self.fileMenu.Append(-1, item='Save Image\tCtrl+S')
        self.fileMenu.AppendSeparator()
        self.exitMenuItem      = self.fileMenu.Append(-1, item='Exit\tCtrl+Q')
        self.GetMenuBar().Append(self.fileMenu, 'File')
        # Classify menu (requires classifier window
        self.classifyMenu = wx.Menu()
        self.classifyMenuItem = self.classifyMenu.Append(-1, item='Classify Image')
        self.GetMenuBar().Append(self.classifyMenu, 'Classify')
        # View Menu
        self.viewMenu = wx.Menu()
        self.objectNumberMenuItem = self.viewMenu.Append(-1, item='Show %s numbers\tCtrl+`'%p.object_name[0])
        self.objectNumberMenuItem.Enable(p.object_table is not None)
        self.classViewMenuItem = self.viewMenu.Append(-1, item='View %s classes as numbers'%p.object_name[0])
        self.classViewMenuItem.Enable(p.object_table is not None)
        self.GetMenuBar().Append(self.viewMenu, 'View')
        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self, manual_url="7_image_viewer.html"), 'Help')


    #######################################
    # CreateChannelMenus 
    #######################################
    def CreateChannelMenus(self):
        ''' Create color-selection menus for each channel. '''

        # Clean up existing channel menus
        try:
            menus = set([items[2].Menu for items in list(self.chMapById.values())])
            for menu in menus:
                for i, mbmenu in enumerate(self.MenuBar.Menus):
                    if mbmenu[0] == menu:
                        self.MenuBar.Remove(i)
            for menu in menus:
                menu.Destroy()
            if 'imagesMenu' in self.__dict__:
                self.MenuBar.Remove(self.MenuBar.FindMenu('Images'))
                self.imagesMenu.Destroy()
        except:
            pass

        # Initialize variables
        self.imagesMenu = wx.Menu()
        chIndex = 0
        imIndex = 0
        self.chMapById = {}
        self.imMapById = {}
        channel_names = []
        startIndex = 0

        # Construct channel names, for RGB images, append a # to the end of
        # each channel. 
        for i, chans in enumerate(p.channels_per_image):
            chans = int(chans)
            name = p.image_names[i]
            if chans == 1:
                channel_names += [name]
            elif chans == 3: #RGB
                channel_names += ['%s [%s]'%(name,x) for x in 'RGB']
            elif chans == 4: #RGBA
                channel_names += ['%s [%s]'%(name,x) for x in 'RGBA']
            else:
                channel_names += ['%s [%s]'%(name,x+1) for x in range(chans)]
        # Zip channel names with channel map
        zippedChNamesChMap = list(zip(channel_names, self.chMap))

        # Loop over all the image names in the properties file
        for i, chans in enumerate(p.image_names):
            channelIds = []
            # Loop over all the channels
            for j in range(0, int(p.channels_per_image[i])):
                (channel, setColor) = zippedChNamesChMap[chIndex]
                channel_menu = wx.Menu()
                for color in ['Red', 'Green', 'Blue', 'Cyan', 'Magenta', 'Yellow', 'Gray', 'None']:
                    id = wx.NewId()
                    # Create a radio item that maps an id and a color. 
                    item = channel_menu.AppendRadioItem(id,color)
                    # Add a new chmapbyId object
                    self.chMapById[id] = (chIndex, color, item, channel_menu)
                    # If lowercase color matches what it was originally set to...
                    if color.lower() == setColor.lower():
                        # Check off the item 
                        item.Check()
                    # Bind
                    self.Bind(wx.EVT_MENU, self.OnMapChannels, item)
                    # Add appropriate Ids to imMapById
                    if ((int(p.channels_per_image[i]) == 1 and color == 'Gray') or 
                        (int(p.channels_per_image[i]) > 1 and j == 0 and color == 'Red') or 
                        (int(p.channels_per_image[i]) > 1 and j == 2 and color == 'Blue') or 
                        (int(p.channels_per_image[i]) > 1 and j == 1 and color == 'Green')): 
                        channelIds = channelIds + [id]
                # Add new menu item  
                self.GetMenuBar().Append(channel_menu, channel)
                chIndex+=1
            # New id for the image as a whole
            id = wx.NewId()
            item = self.imagesMenu.AppendRadioItem(id, p.image_names[i])
            #Effectively this code creates a data structure that stores relevant info with ID as a key
            self.imMapById[id] = (int(p.channels_per_image[i]), item, startIndex, channelIds) 
            # Binds the event menu to OnFetchImage (below) and item 
            self.Bind(wx.EVT_MENU, self.OnFetchImage, item)
            startIndex += int(p.channels_per_image[i])
        # Add the "none" image and check it off. 
        id= wx.NewId()
        item = self.imagesMenu.AppendRadioItem(id, 'None')
        self.Bind(wx.EVT_MENU, self.OnFetchImage, item)
        item.Check()
        # Add new "Images" menu bar item
        self.GetMenuBar().Append(self.imagesMenu, 'Images')
    #######################################
    # /CreateChannelMenus 
    #######################################



    #######################################
    # OnFetchImage
    # 
    # Allows user to display one image at a time.  If image is single channel,
    # displays the image as gray.  If image is multichannel, displays image as
    # RGB.
    # @param self, evt
    #######################################
    def OnFetchImage(self, evt=None):

        # Set every channel to black and set all the toggle options to 'none'
        for ids in list(self.chMapById.keys()):
            (chIndex, color, item, channel_menu) = self.chMapById[ids] 
            if (color.lower() == 'none'):
                item.Check()		
        for ids in list(self.imMapById.keys()):
            (cpi, itm, si, channelIds) = self.imMapById[ids]
            if cpi == 3:
                self.chMap[si] = 'none'
                self.chMap[si+1] = 'none'
                self.chMap[si+2] = 'none'
                self.toggleChMap[si] = 'none'
                self.toggleChMap[si+1] = 'none'
                self.toggleChMap[si+2] = 'none'
            else:
                self.chMap[si] = 'none'
                self.toggleChMap[si] = 'none'

        # Determine what image was selected based on the event.  Set channel to appropriate color(s)
        if evt.GetId() in self.imMapById:

            (chanPerIm, item, startIndex, channelIds) = self.imMapById[evt.GetId()]

            if chanPerIm == 1:
                # Set channel map and toggleChMap values. 
                self.chMap[startIndex] = 'gray'
                self.toggleChMap[startIndex] = 'gray'

                # Toggle the option for the independent channel menu
                (chIndex, color, item, channel_menu) = self.chMapById[channelIds[0]] 
                item.Check()
            else:
                RGB = ['red', 'green', 'blue'] + ['none'] * chanPerIm
                for i in range(chanPerIm):
                    # Set chMap and toggleChMap values
                    self.chMap[startIndex + i] = RGB[i]
                    self.toggleChMap[startIndex + i] = RGB[i]                
                    # Toggle the option in the independent channel menus
                    (chIndex, color, item, channel_menu) = self.chMapById[channelIds[i]] 
                    item.Check()                

        self.MapChannels(self.chMap)
        #######################################
        # /OnFetchImage
        #######################################


    def DoLayout(self):
        if self.imagePanel:
            if not self.cp:
                self.cp = wx.CollapsiblePane(self, label='Show controls', style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
                self.SetBackgroundColour('white') # color for the background of panel
                self.controls  = ImageControlPanel(self.cp.GetPane(), self.imagePanel, 
                                                   brightness=self.imagePanel.brightness,
                                                   scale=self.imagePanel.scale, 
                                                   contrast=self.imagePanel.contrast)
                self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self.cp)
                # self.cp.Collapse(collapse=False) # default open controls
            else:
                self.controls.SetListener(self.imagePanel)
            self.Sizer.Clear()
            self.Sizer.Add(self.sw, proportion=1, flag=wx.EXPAND)
            self.Sizer.Add(self.cp, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 25)
            w, h = self.imagePanel.GetSize()
            if self.first_layout:
                self.SetClientSize( (min(self.maxSize[0], w*self.imagePanel.scale),
                                     min(self.maxSize[1], h*self.imagePanel.scale+55)) )
                self.Center()
                self.first_layout = False
            self.sw.SetScrollbars(1, 1, w*self.imagePanel.scale, h*self.imagePanel.scale)
            #self.sw.SetScrollRate(1, 1)
            self.CreateChannelMenus()

            # Annoying: Need to bind 3 windows to KEY_DOWN in case focus changes.
            self.Bind(wx.EVT_KEY_DOWN, self.HoldKey) 
            self.sw.Bind(wx.EVT_KEY_DOWN, self.HoldKey)
            self.cp.Bind(wx.EVT_KEY_DOWN, self.HoldKey)
            self.imagePanel.Bind(wx.EVT_KEY_DOWN, self.HoldKey)

            # Annoying: Need to bind 3 windows to KEY_UP in case focus changes.
            self.Bind(wx.EVT_KEY_UP, self.OnKey)
            self.sw.Bind(wx.EVT_KEY_UP, self.OnKey)
            self.cp.Bind(wx.EVT_KEY_UP, self.OnKey)
            self.imagePanel.Bind(wx.EVT_KEY_UP, self.OnKey)
            self.Bind(wx.EVT_MENU, lambda e: self.SelectAll(), self.sel_all)
            self.Bind(wx.EVT_MENU, lambda e: self.DeselectAll(), self.deselect)

        self.fileMenu.Bind(wx.EVT_MENU_OPEN, self.OnOpenFileMenu)
        self.classifyMenu.Bind(wx.EVT_MENU_OPEN, self.OnOpenClassifyMenu)
        self.viewMenu.Bind(wx.EVT_MENU_OPEN, self.OnOpenViewMenu)
        self.Bind(wx.EVT_MENU, self.OnOpenImage, self.openImageMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveImage, self.saveImageMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveImage, self.saveImageMenuItem)
        self.Bind(wx.EVT_MENU, self.OnOpenImage, self.openImageMenuItem)
        self.Bind(wx.EVT_MENU, self.OnChangeClassRepresentation, self.classViewMenuItem)
        self.Bind(wx.EVT_MENU, self.OnShowObjectNumbers, self.objectNumberMenuItem)
        self.Bind(wx.EVT_MENU, self.OnClassifyImage, self.classifyMenuItem)
        self.Bind(wx.EVT_MENU, lambda evt:self.Close(), self.exitMenuItem)

    def OnClassifyImage(self, evt=None):
        logging.info('Classifying image with key=%s...'%str(self.img_key))
        classifier = get_classifier_window()
        if classifier is None:
            logging.error('Could not find Classifier!')
            return
        # Score the Image
        classifier.ClassifyImage(self.img_key)
        self.Close()

    def OnPaneChanged(self, evt=None):
        self.Layout()
        if self.cp.IsExpanded():
            self.cp.SetLabel('Hide controls')
        else:
            self.cp.SetLabel('Show controls')

    def OnMapChannels(self, evt):
        if evt.GetId() in self.chMapById:
            (chIdx,color,_,_) = self.chMapById[evt.GetId()]
            self.chMap[chIdx] = color
            if color.lower() != 'none':
                self.toggleChMap[chIdx] = color
            self.MapChannels(self.chMap)

    def MapChannels(self, chMap):
        self.chMap = chMap
        self.imagePanel.MapChannels(chMap)

    def HoldKey(self, evt):
        keycode = evt.GetKeyCode()
        chIdx = keycode-49
        if evt.CmdDown() or evt.ControlDown():
            if keycode == ord('F'): # When holding, make it dark
                # Check if evt before was already released
                if(self.inspect_release):
                    self.imagePanel.tmp_brightness = self.imagePanel.brightness
                    self.inspect_release = False
                self.imagePanel.SetBrightness(0)
        else:
            evt.Skip()

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
                self.imagePanel.SetContrastMode('Linear')
                self.controls.SetContrastMode('Linear')
            elif keycode == ord('L'):
                self.imagePanel.SetContrastMode('Log')
                self.controls.SetContrastMode('Log')
            elif keycode == ord('F'): # Release the darkness :)
                brightness = self.imagePanel.tmp_brightness
                self.imagePanel.SetBrightness(brightness)
                self.inspect_release = True # Tell the panel, F key is not pressed anymore, otherwise it is stuck in key down events.
            elif len(self.chMap) > chIdx >= 0:   
                # ctrl+n where n is the nth channel
                self.ToggleChannel(chIdx)
            else:
                evt.Skip()
        else:
            if keycode == ord(' '):
                self.cp.Collapse(not self.cp.IsCollapsed())
                self.OnPaneChanged()
            else:
                evt.Skip()

    def OnResizeImagePanel(self, evt):
        self.sw.SetVirtualSize(evt.GetSize())

    def ToggleChannel(self, chIdx):
        if self.chMap[chIdx] == 'None':
            for (idx, color, item, menu) in list(self.chMapById.values()):
                if idx == chIdx and color.lower() == self.toggleChMap[chIdx].lower():
                    item.Check()   
            self.chMap[chIdx] = self.toggleChMap[chIdx]
            self.MapChannels(self.chMap)
        else:
            for (idx, color, item, menu) in list(self.chMapById.values()):
                if idx == chIdx and color.lower() == 'none':
                    item.Check()
            self.chMap[chIdx] = 'None'
            self.MapChannels(self.chMap)

    def SelectAll(self):
        if p.object_table:
            coords = db.GetAllObjectCoordsFromImage(self.img_key)
            self.selection = db.GetObjectsFromImage(self.img_key)
            if p.rescale_object_coords:
                coords = [rescale_image_coord_to_display(x, y) for (x, y) in coords]
            self.imagePanel.SetSelectedPoints(coords)

    def DeselectAll(self):
        self.selection = []
        self.imagePanel.DeselectAll()

    def SelectObject(self, obkey):
        coord = db.GetObjectCoords(obkey)
        if p.rescale_object_coords:
            coord = rescale_image_coord_to_display(coord[0], coord[1])
        self.selection += [coord]
        self.imagePanel.SetSelectedPoints([coord])

    def SetClasses(self, classCoords):
        self.classViewMenuItem.Enable()
        self.imagePanel.SetClassPoints(classCoords)
        self.controls.SetClassPoints(classCoords)
        self.Refresh()
        self.Layout()

    def OnLeftDown(self, evt):
        if self.img_key and p.object_table:
            x = evt.GetPosition().x / self.imagePanel.scale
            y = evt.GetPosition().y / self.imagePanel.scale
            if p.rescale_object_coords:
                x, y = rescale_display_coord_to_image(x, y)
            obKey = db.GetObjectNear(self.img_key, x, y)

            if not obKey: return

            # update existing selection
            if not evt.ShiftDown():
                self.selection = [obKey]
                self.imagePanel.DeselectAll()
            else:
                if obKey not in self.selection:
                    self.selection += [obKey]
                else:
                    self.selection.remove(obKey)

            # select the object
            (x,y) = db.GetObjectCoords(obKey)            
            if p.rescale_object_coords:
                x, y = rescale_image_coord_to_display(x, y)
            self.imagePanel.TogglePointSelection((x,y))

            if self.selection:
                # start drag
                source = wx.DropSource(self)
                # wxPython crashes unless the data object is assigned to a variable.
                data_object = wx.CustomDataObject("application.cpa.ObjectKey")
                data_object.SetData(pickle.dumps( (self.GetId(), self.selection) ))
                source.SetData(data_object)
                result = source.DoDragDrop(flags=wx.Drag_DefaultMove)
                if result == 0:
                    pass

    def OnRightDown(self, evt):
        ''' On right click show popup menu. '''
        if p.object_table:
            self.PopupMenu(self.popupMenu, evt.GetPosition())

    def OnOpenImage(self, evt=None):
        # 1) Get the image key
        # Start with the table_id if there is one
        tblNum = None
        if p.table_id:
            dlg = wx.TextEntryDialog(self, p.table_id+':','Enter '+p.table_id)
            dlg.SetValue('0')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    tblNum = int(dlg.GetValue())
                except ValueError:
                    errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(p.table_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                    errdlg.ShowModal()
                    return
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
        # Then get the image_id
        dlg = wx.TextEntryDialog(self, p.image_id+':','Enter '+p.image_id)
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                imgNum = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(p.image_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        # Build the imkey
        if p.table_id:
            imkey = (tblNum,imgNum)
        else:
            imkey = (imgNum,)

        dm = DataModel()
        if imkey not in dm.GetAllImageKeys():
            errdlg = wx.MessageDialog(self, 'There is no image with that key.', "Couldn't find image", wx.OK|wx.ICON_EXCLAMATION)
            errdlg.ShowModal()
            self.Destroy()
        else:            
            # load the image
            self.img_key = imkey
            self.SetImage(imagetools.FetchImage(imkey), p.image_channel_colors)
            self.DoLayout()

    def OnSaveImage(self, evt):
        import os
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=self.defaultPath, defaultFile=self.defaultFile,
                                   wildcard='PNG file (*.png)|*.png|JPG file (*.jpg, *.jpeg)|*.jpg', 
                                   style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
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
            imagetools.SaveBitmap(self.imagePanel.bitmap, filename, format.upper()[1:])


    def OnChangeClassRepresentation(self, evt):
        if self.classViewMenuItem.ItemLabel.endswith('numbers'):
            self.classViewMenuItem.ItemLabel = 'View %s classes as colors'%p.object_name[0]
        else:
            self.classViewMenuItem.ItemLabel = 'View %s classes as numbers'%p.object_name[0]
        self.imagePanel.ToggleClassRepresentation()

    def OnShowObjectNumbers(self, evt):
        if self.objectNumberMenuItem.ItemLabel.startswith('Hide'):
            self.objectNumberMenuItem.ItemLabel = 'Show %s numbers\tCtrl+`'%(p.object_name[0])
        else:
            self.objectNumberMenuItem.ItemLabel = 'Hide %s numbers\tCtrl+`'%(p.object_name[0])
        self.imagePanel.ToggleObjectNumbers()

    def OnOpenFileMenu(self, evt=None):
        if self.imagePanel:
            self.saveImageMenuItem.Enable()
        else:
            self.saveImageMenuItem.Enable(False)

    def OnOpenViewMenu(self, evt=None):
        if self.imagePanel and self.imagePanel.classes:
            self.classViewMenuItem.Enable()
        else:
            self.classViewMenuItem.Enable(False)

    def OnOpenClassifyMenu(self, evt=None):
        classifier = get_classifier_window()
        if classifier and classifier.IsTrained():
            self.classifyMenuItem.Enable()
        else:
            self.classifyMenuItem.Enable(False)



if __name__ == "__main__":
    logging.basicConfig()

#    p.LoadFile('/Users/afraser/Desktop/cpa_example/example.properties')
#    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('../properties/2008_07_29_Giemsa.properties')
    app = wx.App()
    from .imagereader import ImageReader

    p = Properties()
    p.image_channel_colors = ['red','green','blue']
    p.object_name = ['cell', 'cells']
    p.image_names = ['a', 'b', 'c']
    p.image_id = 'ImageNumber'
    p.channels_per_image = [1,1,1]
    images = [np.ones((200,200)),
              np.ones((200,200)) / 2. ,
              np.ones((200,200)) / 4. ,
              np.ones((200,200)) / 8. ,
              np.ones((200,200)),
              np.ones((200,200)) / 2. ,
              np.ones((200,200)) / 4. ,
              np.ones((200,200)) / 8. ,
              ]

    pixels = []
    for channel in p.image_channel_colors:        
        pixels += [imagetools.tile_images(images)]

    f = ImageViewer(pixels)
    f.Show()


##    if not p.show_load_dialog():
##        logging.error('ImageViewer requires a properties file.  Exiting.')
##        wx.GetApp().Exit()
##        raise Exception('ImageViewer requires a properties file.  Exiting.')
##    
##    db = DBConnect()
##    dm = DataModel()
##    ir = ImageReader()
##    
##    obKey = dm.GetRandomObject()
##    imagetools.ShowImage(obKey[:-1], p.image_channel_colors, None)
#    filenames = db.GetFullChannelPathsForImage(obKey[:-1])
#    images = ir.ReadImages(filenames)
#    frame = ImageViewer(imgs=images, chMap=p.image_channel_colors, img_key=obKey[:-1])
#    frame.Show()

#    for i in xrange(1):
#        obKey = dm.GetRandomObject()
#        imgs = imagetools.FetchImage(obKey[:-1])
#        f2 = ImageViewer(imgs=imgs, img_key=obKey[:-1], chMap=p.image_channel_colors, title=str(obKey[:-1]))
#        f2.Show(True)

#    classCoords = {'a':[(100,100),(200,200)],'b':[(200,100),(200,300)] }
#    f2.SetClasses(classCoords)

    #imagetools.SaveBitmap(frame.imagePanel.bitmap, '/Users/afraser/Desktop/TEST.png')

    app.MainLoop()
