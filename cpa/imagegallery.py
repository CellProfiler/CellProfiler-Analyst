# Encoding: utf-8



import matplotlib

from cpa.guiutils import create_status_bar

matplotlib.use('WXAgg')

import sys
import logging
from .datamodel import DataModel
from .imagecontrolpanel import ImageControlPanel
from .properties import Properties
from . import tilecollection
from . import icons
from . import dbconnect
from . import imagetools
from . import sortbin
import os
import wx
import cpa.helpmenu

# number of cells to classify before prompting the user for whether to continue
MAX_ATTEMPTS = 10000

ID_IMAGE_GALLERY = wx.NewIdRef()
CREATE_NEW_FILTER = '*create new filter*'

class ImageGallery(wx.Frame):
    """
    GUI Interface and functionality for Image Gallery.
    """

    def __init__(self, properties=None, parent=None, id=ID_IMAGE_GALLERY, **kwargs):

        if properties is not None:
            global p
            p = properties
            global db
            db = dbconnect.DBConnect()

        wx.Frame.__init__(self, parent, id=id, title='CPA/ImageGallery - %s' % \
                                                     (os.path.basename(p._filename)), size=(800, 600), **kwargs)
        if parent is None and not sys.platform.startswith('win'):
            from wx.adv import TaskBarIcon
            self.tbicon = TaskBarIcon()
            self.tbicon.SetIcon(icons.get_cpa_icon(), 'CPA/ImageGallery')
        else:
            self.SetIcon(icons.get_cpa_icon())
        self.SetName('ImageGallery')

        db.register_gui_parent(self)

        global dm
        dm = DataModel()

        if not p.is_initialized():
            logging.critical('ImageGallery requires a properties file. Exiting.')
            raise Exception('ImageGallery requires a properties file. Exiting.')

        self.pmb = None
        self.worker = None
        self.trainingSet = None
        self.classBins = []
        self.binsCreated = 0
        self.chMap = p.image_channel_colors[:]
        self.toggleChMap = p.image_channel_colors[
                           :]  # used to store previous color mappings when toggling colors on/off with ctrl+1,2,3...
        self.brightness = 1.0
        self.scale = 1.0 
        
        self.contrast = 'Linear'
        self.defaultTSFileName = None
        self.defaultModelFileName = None
        self.lastScoringFilter = None

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.CreateMenus()

        self.status_bar = create_status_bar(self)

        #### Create GUI elements
        # Top level - three split windows
        self.splitter = wx.SplitterWindow(self, style=wx.NO_BORDER | wx.SP_3DSASH)
        self.bins_splitter = wx.SplitterWindow(self.splitter, style=wx.NO_BORDER | wx.SP_3DSASH)

        # fetch & rules
        self.fetch_panel = wx.Panel(self.splitter)

        # sorting bins
        self.gallery_panel = wx.Panel(self.bins_splitter)
        o_label = p.object_name[0] if p.classification_type == 'image' else '' + ' image gallery'
        self.gallery_box = wx.StaticBox(self.gallery_panel, label=o_label)
        self.gallery_sizer = wx.StaticBoxSizer(self.gallery_box, wx.VERTICAL)
        self.galleryBin = sortbin.SortBin(parent=self.gallery_panel,
                                               classifier=self,
                                               label='image gallery',
                                               parentSizer=self.gallery_sizer)
        self.gallery_sizer.Add(self.galleryBin, proportion=1, flag=wx.EXPAND)
        self.gallery_panel.SetSizer(self.gallery_sizer)
        self.objects_bin_panel = wx.Panel(self.bins_splitter)

        # fetch objects interface
        self.startId = wx.TextCtrl(self.fetch_panel, id=-1, value='1', size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.endId = wx.TextCtrl(self.fetch_panel, id=-1, value='100', size=(60, -1), style=wx.TE_PROCESS_ENTER)
        self.fetchChoice = wx.Choice(self.fetch_panel, id=-1, choices=['range','all','individual'])
        self.fetchChoice.SetSelection(0)
        self.filterChoice = wx.Choice(self.fetch_panel, id=-1,
                                      choices=['experiment'] + p._filters_ordered + p._groups_ordered + [
                                          CREATE_NEW_FILTER])
        self.fetchFromGroupSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fetchBtn = wx.Button(self.fetch_panel, -1, 'Fetch!')

        #### Create Sizers
        self.fetchSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.classified_bins_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #### Add elements to sizers and splitters
        # fetch panel
        self.fetchSizer.AddStretchSpacer()
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'Fetch '), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchSizer.Add(self.fetchChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchTxt = wx.StaticText(self.fetch_panel, -1, label='of image IDs:')
        self.fetchSizer.Add(self.fetchTxt, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchSizer.Add(self.startId, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchTxt2 = wx.StaticText(self.fetch_panel, -1, label='to')
        self.fetchSizer.Add(self.fetchTxt2, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchSizer.Add(self.endId, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        #self.fetchSizer.Add(self.obClassChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        #self.fetchSizer.Add(5, 20, 0)
        self.fetchTxt3 = wx.StaticText(self.fetch_panel, -1, label='images')
        self.fetchSizer.Add(self.fetchTxt3, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchSizer.Add(wx.StaticText(self.fetch_panel, -1, 'from'), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchSizer.Add(self.filterChoice, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(10, 20, 0)
        self.fetchSizer.Add(self.fetchFromGroupSizer, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.Add(5, 20, 0)
        self.fetchSizer.Add(self.fetchBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fetchSizer.AddStretchSpacer()
        self.fetch_panel.SetSizerAndFit(self.fetchSizer)

        # classified bins panel
        self.objects_bin_panel.SetSizer(self.classified_bins_sizer)

        # splitter windows
        self.splitter.SplitHorizontally(self.fetch_panel, self.bins_splitter,
                                        self.fetch_panel.GetMinSize()[1])
        self.bins_splitter.SplitHorizontally(self.gallery_panel, self.objects_bin_panel)

        self.splitter.SetSashGravity(0.0)
        self.bins_splitter.SetSashGravity(0.5)

        self.splitter.SetMinimumPaneSize(max(50, self.fetch_panel.GetMinHeight()))
        self.bins_splitter.SetMinimumPaneSize(50)
        self.SetMinSize((self.fetch_panel.GetMinWidth(), 4 * 50 + self.fetch_panel.GetMinHeight()))

        # Set initial state
        self.filterChoice.SetSelection(0)

        # JEN - Start Add
        # self.openDimensReduxBtn.Disable()
        # JEN - End Add
        self.fetchSizer.Hide(self.fetchFromGroupSizer)

        #####################
        #### GUI Section ####
        #####################

        # add the default classes
        #for class in range(1, num_classes+1):
        self.AddSortClass('objects of selected image')
        #self.AddSortClass('negative')

        self.Layout()

        self.Center()
        self.MapChannels(p.image_channel_colors[:])
        self.BindMouseOverHelpText()

        #self.Bind(wx.EVT_BUTTON, self.OnInspect, self.inspectBtn)
        # JEN - Start Add
        # self.Bind(wx.EVT_BUTTON, self.OpenDimensRedux, self.openDimensReduxBtn)
        # JEN - End Add

        self.Bind(wx.EVT_BUTTON, self.OnFetch, self.fetchBtn)
        self.startId.Bind(wx.EVT_TEXT, self.ValidateIntegerField)
        self.startId.Bind(wx.EVT_TEXT_ENTER, self.OnFetch)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHAR, self.OnKey)  # Doesn't work for windows
        tilecollection.EVT_TILE_UPDATED(self, self.OnTileUpdated)
        self.Bind(sortbin.EVT_QUANTITY_CHANGED, self.QuantityChanged)

        self.Bind(wx.EVT_CHOICE, self.OnSelectFetchChoice, self.fetchChoice)
        self.Bind(wx.EVT_CHOICE, self.OnSelectFilter, self.filterChoice)


    # JK - End Add

    def BindMouseOverHelpText(self):
        self.startId.SetToolTip(wx.ToolTip('The number of %s to fetch.' % (p.object_name[1])))
        #self.obClassChoice.SetToolTip(wx.ToolTip('The phenotype of the %s.' % (p.object_name[1])))
        #self.obClassChoice.GetToolTip().SetDelay(3000)
        self.filterChoice.SetToolTip(wx.ToolTip(
            'Filters fetched %s to be from a subset of your images. (See groups and filters in the properties file)' % (
            p.object_name[1])))
        self.filterChoice.GetToolTip().SetDelay(3000)
        self.fetchBtn.SetToolTip(wx.ToolTip('Fetches images of %s to be sorted.' % (p.object_name[1])))
        self.galleryBin.SetToolTip(
            wx.ToolTip('%s gallery of our dataset' % (p.object_name[1].capitalize())))

    def OnKey(self, evt):
        ''' Keyboard shortcuts '''
        keycode = evt.GetKeyCode()
        chIdx = keycode - 49
        if evt.ControlDown() or evt.CmdDown():
            # ctrl+N toggles channel #N on/off
            if len(self.chMap) > chIdx >= 0:
                self.ToggleChannel(chIdx)
            else:
                evt.Skip()
        else:
            evt.Skip()

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

    def CreateMenus(self):
        ''' Create file menu and menu items '''
        # View Menu

        viewMenu = wx.Menu()

        self.fileMenu = wx.Menu()
        loadMenuItem = self.fileMenu.Append(-1, item='Load Image Set\tCtrl+O',
                                                   helpString='Loads images specfied in a csv file.')
        # JEN - End Add
        exitMenuItem = self.fileMenu.Append(id=wx.ID_EXIT, item='Exit\tCtrl+Q', helpString='Exit Image Gallery')
        self.GetMenuBar().Append(self.fileMenu, 'File')

        imageControlsMenuItem = viewMenu.Append(-1, item='Image Controls\tCtrl+Shift+I',
                                                helpString='Launches a control panel for adjusting image brightness, size, etc.')
        self.GetMenuBar().Append(viewMenu, 'View')

        # Rules menu
        # rulesMenu = wx.Menu()
        # rulesEditMenuItem = rulesMenu.Append(-1, text=u'Edit…', help='Lets you edit the rules')
        # self.GetMenuBar().Append(rulesMenu, 'Rules')

        # Channel Menus
        self.CreateChannelMenus()

        # Advanced menu
        advancedMenu = wx.Menu()
        fetchObjMenuItem = advancedMenu.Append(-1, item='Fetch all objects from displayed images', helpString='Fetch all objects from displayed images')
        fetchAllObjMenuItem = advancedMenu.Append(-1, item='Fetch all objects', helpString='Fetch all objects')
        saveImgMenuItem = advancedMenu.Append(-1, item='Save image thumbnails as PNG', helpString='Save image thumbnails as PNG')
        saveObjMenuItem = advancedMenu.Append(-1, item='Save object thumbnails as PNG', helpString='Save object thumbnails as PNG')
        self.GetMenuBar().Append(advancedMenu, 'Advanced')

        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self, manual_url="14_image_gallery.html"), 'Help')

        self.Bind(wx.EVT_MENU, self.OnShowImageControls, imageControlsMenuItem)
        self.Bind(wx.EVT_MENU, self.OnFetchObjThumbnails ,fetchObjMenuItem)
        self.Bind(wx.EVT_MENU, self.OnFetchAllObjThumbnails ,fetchAllObjMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveImgThumbnails ,saveImgMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSaveObjThumbnails ,saveObjMenuItem)
        self.Bind(wx.EVT_MENU, self.OnClose, exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_MENU, self.OnLoadImageSet, loadMenuItem)




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
        self.chMapById = {}
        self.imMapById = {}
        channel_names = []
        startIndex = 0
        channelIds = []

        for i, chans in enumerate(p.channels_per_image):
            chans = int(chans)
            # Construct channel names, for RGB images, append a # to the end of
            # each channel.
            name = p.image_names[i]
            if chans == 1:
                channel_names += [name]
            elif chans == 3:  # RGB
                channel_names += ['%s [%s]' % (name, x) for x in 'RGB']
            elif chans == 4:  # RGBA
                channel_names += ['%s [%s]' % (name, x) for x in 'RGBA']
            else:
                channel_names += ['%s [%s]' % (name, x + 1) for x in range(chans)]

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
                    item = channel_menu.AppendRadioItem(id, color)
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
                chIndex += 1
            # New id for the image as a whole
            id = wx.NewId()
            item = self.imagesMenu.AppendRadioItem(id, p.image_names[i])
            # Effectively this code creates a data structure that stores relevant info with ID as a key
            self.imMapById[id] = (int(p.channels_per_image[i]), item, startIndex, channelIds)
            # Binds the event menu to OnFetchImage (below) and item
            self.Bind(wx.EVT_MENU, self.OnFetchImage, item)
            startIndex += int(p.channels_per_image[i])
        # Add the "none" image and check it off.
        id = wx.NewId()
        item = self.imagesMenu.AppendRadioItem(id, 'None')
        self.Bind(wx.EVT_MENU, self.OnFetchImage, item)
        item.Check()  # Add new "Images" menu bar item
        self.GetMenuBar().Append(self.imagesMenu, 'Images')

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
                self.chMap[si + 1] = 'none'
                self.chMap[si + 2] = 'none'
                self.toggleChMap[si] = 'none'
                self.toggleChMap[si + 1] = 'none'
                self.toggleChMap[si + 2] = 'none'
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

    def OnLoadImageSet(self, evt):
        '''
        Present user with file select dialog, then load selected training set.
        '''
        dlg = wx.FileDialog(self, "Select the file containing your classifier training set.",
                            defaultDir=os.getcwd(),
                            wildcard='CSV files (*.csv)|*.csv',
                            style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            name, file_extension = os.path.splitext(filename)
            if '.csv' == file_extension:
                self.LoadImageSet(filename)
            else:
                logging.error("Couldn't load the file! Make sure it is .csv")

    # Loads a CSV file with ImageNumber column and fetches all images with this number
    def LoadImageSet(self, filename):
        '''
        Loads the selected file, parses out object keys, and fetches the tiles for CSV
        '''
        # pause tile loading
        with tilecollection.load_lock():
            self.PostMessage('Loading image set from %s' % filename)
            import pandas as pd
            df = pd.read_csv(filename)
            def cb():
                keys = [tuple([k,-1]) for k in df['ImageNumber']]    
                self.galleryBin.AddObjects(keys, self.chMap, pos='last', display_whole_image=True)
                self.PostMessage('Image set loaded')
            if df.shape[0] > 100:
                dlg = wx.MessageDialog(self,
                                       'The whole collection consists of %s images. Downloading could be slow. Do you still want to continue?' % (
                                       df.shape[0]),
                                       'Load whole image set?', wx.YES_NO | wx.ICON_QUESTION)
                response = dlg.ShowModal()
                # Call fetch filter with all keys
                if response == wx.ID_YES:
                    self.galleryBin.SelectAll()
                    self.galleryBin.RemoveSelectedTiles()
                    # Need to run this after removing all tiles!
                    wx.CallAfter(cb)
            else:
                self.galleryBin.SelectAll()
                self.galleryBin.RemoveSelectedTiles()
                # Need to run this after removing all tiles!
                wx.CallAfter(cb)

    def OnFetch(self, evt):
        start = int(self.startId.Value)
        end = int(self.endId.Value)
        fltr_sel = self.filterChoice.GetStringSelection()
        fetch_sel = self.fetchChoice.GetStringSelection()
        statusMsg = 'Fetched images %d - %d ' % (start, end)

        # Need to flatten it due to the fact that img key can look like this:
        # (image_id,) or this (table_id, image_id)
        def flatten(*args):
            for x in args:
                if hasattr(x, '__iter__'):
                    for y in flatten(*x):
                        yield y
                else:
                    yield x

        # Fetching all images with filter
        if fetch_sel == 'all':
            # Easy just fetch all images
            if fltr_sel == 'experiment':
                self.FetchAll()
                return
            # Fetch all images with self defined filter
            elif fltr_sel in p._filters_ordered:
                imKeys = db.GetFilteredImages(fltr_sel)
                if imKeys == []:
                    self.PostMessage('No images were found in filter "%s"' % (fltr_sel))
                    return

                # Are you sure?
                if len(imKeys) > 100:
                    dlg = wx.MessageDialog(self,
                                       'The whole collection consists of %s images. Downloading could be slow. Do you still want to continue?' % (
                                       len(imKeys)),
                                       'Load whole image set?', wx.YES_NO | wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    # Call fetch filter with all keys
                    if response == wx.ID_YES:
                        self.galleryBin.SelectAll()
                        self.galleryBin.RemoveSelectedTiles()
                        # Need to run this after removing all tiles!
                        def cb():
                            filteredImKeys = db.GetFilteredImages(fltr_sel)
                            imKeys = [tuple(list(flatten(x,-1))) for x in filteredImKeys]
                            self.galleryBin.AddObjects(imKeys, self.chMap, pos='last', display_whole_image=True)
                        wx.CallAfter(cb)
                        statusMsg += ' from filter "%s"' % (fltr_sel)

                # data set is small, lets go for it!
                else:
                    self.galleryBin.SelectAll()
                    self.galleryBin.RemoveSelectedTiles()
                    # Need to run this after removing all tiles!
                    def cb():
                        filteredImKeys = db.GetFilteredImages(fltr_sel)
                        imKeys = [tuple(list(flatten(x,-1))) for x in filteredImKeys]

                        self.galleryBin.AddObjects(imKeys, self.chMap, pos='last', display_whole_image=True)
                    wx.CallAfter(cb)
                    statusMsg += ' from filter "%s"' % (fltr_sel)

            # fetching all images for predefined filter
            elif fltr_sel in p._groups_ordered:

                
                groupName = fltr_sel
                groupKey = self.GetGroupKeyFromGroupSizer(groupName)
                imKeys = dm.GetImagesInGroupWithWildcards(groupName, groupKey)
                colNames = dm.GetGroupColumnNames(groupName)

                if imKeys == []:
                    self.PostMessage('No images were found in group %s: %s' % (groupName,
                                                                               ', '.join(['%s=%s' % (n, v) for n, v in
                                                                                          zip(colNames, groupKey)])))
                    return

                # Are you sure?
                if len(imKeys) > 100:
                    dlg = wx.MessageDialog(self,
                                       'The whole collection consists of %s images. Downloading could be slow. Do you still want to continue?' % (
                                       len(imKeys)),
                                       'Load whole image set?', wx.YES_NO | wx.ICON_QUESTION)
                    response = dlg.ShowModal()
                    # Yes, I am sure!
                    if response == wx.ID_YES:
                        self.galleryBin.SelectAll()
                        self.galleryBin.RemoveSelectedTiles()
                        groupName = fltr_sel
                        groupKey = self.GetGroupKeyFromGroupSizer(groupName)
                        filteredImKeys = dm.GetImagesInGroupWithWildcards(groupName, groupKey)
                        colNames = dm.GetGroupColumnNames(groupName)
                        def cb():
                            imKeys = [tuple(list(flatten(x,-1))) for x in filteredImKeys]
                            self.galleryBin.AddObjects(imKeys, self.chMap, pos='last', display_whole_image=True)
                        
                        statusMsg += ' from group %s: %s' % (groupName,
                                                             ', '.join(['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))
                        wx.CallAfter(cb)

                # dataset is small, lets go for it!
                else:
                    self.galleryBin.SelectAll()
                    self.galleryBin.RemoveSelectedTiles()
                    groupName = fltr_sel
                    groupKey = self.GetGroupKeyFromGroupSizer(groupName)
                    filteredImKeys = dm.GetImagesInGroupWithWildcards(groupName, groupKey)
                    colNames = dm.GetGroupColumnNames(groupName)
                    def cb():
                        imKeys = [tuple(list(flatten(x,-1))) for x in filteredImKeys]
                        self.galleryBin.AddObjects(imKeys, self.chMap, pos='last', display_whole_image=True)
                    
                    statusMsg += ' from group %s: %s' % (groupName,
                                                         ', '.join(['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))
                    wx.CallAfter(cb)

        # Fetching individual images
        elif fetch_sel == 'individual':

            if p.table_id:
                imgKey = [(start,end,-1)]
            else:
                imgKey = [(end,-1)]

            self.galleryBin.AddObjects(imgKey, self.chMap, pos='last', display_whole_image=True)
            return

        # Fetching images with range
        elif fltr_sel == 'experiment':
            self.galleryBin.SelectAll()
            self.galleryBin.RemoveSelectedTiles()
            # Need to run this after removing all tiles!
            def cb():
                imKeys = db.GetAllImageKeys()
                imKeys = [tuple(list(flatten(x,-1))) for x in imKeys]
                self.galleryBin.AddObjects(imKeys[(start - 1):end], self.chMap, pos='last', display_whole_image=True)
            wx.CallAfter(cb)
            statusMsg += ' from whole experiment'
        elif fltr_sel in p._filters_ordered:
            self.galleryBin.SelectAll()
            self.galleryBin.RemoveSelectedTiles()
            # Need to run this after removing all tiles!
            def cb():
                filteredImKeys = db.GetFilteredImages(fltr_sel)
                if filteredImKeys == []:
                    self.PostMessage('No images were found in filter "%s"' % (fltr_sel))
                    return
                imKeys = [tuple(list(flatten(x,-1))) for x in filteredImKeys]
                self.galleryBin.AddObjects(imKeys[(start - 1):end], self.chMap, pos='last', display_whole_image=True)
            wx.CallAfter(cb)
            statusMsg += ' from filter "%s"' % (fltr_sel)
        elif fltr_sel in p._groups_ordered:
            # if the filter name is a group then it's actually a group
            self.galleryBin.SelectAll()
            self.galleryBin.RemoveSelectedTiles()
            groupName = fltr_sel
            groupKey = self.GetGroupKeyFromGroupSizer(groupName)
            filteredImKeys = dm.GetImagesInGroupWithWildcards(groupName, groupKey)
            colNames = dm.GetGroupColumnNames(groupName)
            def cb():
                if filteredImKeys == []:
                    self.PostMessage('No images were found in group %s: %s' % (groupName,
                                                                               ', '.join(['%s=%s' % (n, v) for n, v in
                                                                                          zip(colNames, groupKey)])))
                    return
                
                imKeys = [tuple(list(flatten(x,-1))) for x in filteredImKeys]
                self.galleryBin.AddObjects(imKeys[(start - 1):end], self.chMap, pos='last', display_whole_image=True)
            
            statusMsg += ' from group %s: %s' % (groupName,
                                                 ', '.join(['%s=%s' % (n, v) for n, v in zip(colNames, groupKey)]))

            wx.CallAfter(cb)
           

        self.PostMessage(statusMsg)


    def FetchAll(self):

        def flatten(*args):
            for x in args:
                if hasattr(x, '__iter__'):
                    for y in flatten(*x):
                        yield y
                else:
                    yield x

        imKeys = db.GetAllImageKeys()
        # A lot of images
        if len(imKeys) > 200:
            # double check
            dlg = wx.MessageDialog(self,
                                   'The whole collection consists of %s images. Downloading could be slow. Do you still want to continue?' % (
                                   len(imKeys)),
                                   'Load whole image set?', wx.YES_NO | wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.galleryBin.SelectAll()
                self.galleryBin.RemoveSelectedTiles()
                # Need to run this after removing all tiles!
                def cb():
                    imKeys = db.GetAllImageKeys()
                    imKeys = [tuple(list(flatten(x,-1))) for x in imKeys]
                    self.galleryBin.AddObjects(imKeys, self.chMap, pos='last', display_whole_image=True)
                    self.PostMessage("Loaded all images")
                wx.CallAfter(cb)
        else: 
            self.galleryBin.SelectAll()
            self.galleryBin.RemoveSelectedTiles()
            # Need to run this after removing all tiles!
            def cb():
                imKeys = db.GetAllImageKeys()
                imKeys = [tuple(list(flatten(x,-1))) for x in imKeys]
                self.galleryBin.AddObjects(imKeys, self.chMap, pos='last', display_whole_image=True)
                self.PostMessage("Loaded all images")
            wx.CallAfter(cb)


    def AddSortClass(self, label):
        ''' Create a new SortBin in a new StaticBoxSizer with the given label.
        This sizer is then added to the classified_bins_sizer. '''
        bin = sortbin.SortBin(parent=self.objects_bin_panel, label=label,
                              classifier=self)

        box = wx.StaticBox(self.objects_bin_panel, label=label)
        # NOTE: bin must be created after sizer or drop events will occur on the sizer
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        bin.parentSizer = sizer

        sizer.Add(bin, proportion=1, flag=wx.EXPAND)
        self.classified_bins_sizer.Add(sizer, proportion=1, flag=wx.EXPAND)
        self.classBins.append(bin)
        self.objects_bin_panel.Layout()
        self.binsCreated += 1
        self.QuantityChanged()
        # IMPORTANT: required for drag and drop to work on Linux
        # see: http://trac.wxwidgets.org/ticket/2763
        box.Lower()
 
    def RemoveSortClass(self, label, clearModel=True):
        pass

    def all_sort_bins(self):
        return [self.galleryBin] + self.classBins

    def QuantityChanged(self, evt=None):
        pass

    def OnTileUpdated(self, evt):
        '''
        When the tile loader returns the tile image update the tile.
        '''
        self.galleryBin.UpdateTile(evt.data)
        for bin in self.classBins:
            bin.UpdateTile(evt.data)

    def OnMapChannels(self, evt):
        ''' Responds to selection from the color mapping menus. '''
        (chIdx, color, item, menu) = self.chMapById[evt.GetId()]
        item.Check()
        self.chMap[chIdx] = color.lower()
        if color.lower() != 'none':
            self.toggleChMap[chIdx] = color.lower()
        self.MapChannels(self.chMap)

    def MapChannels(self, chMap):
        ''' Tell all bins to apply a new channel-color mapping to their tiles. '''
        # TODO: Need to update color menu selections
        self.chMap = chMap
        for bin in self.all_sort_bins():
            bin.MapChannels(chMap)

    def OnSelectFetchChoice(self, evt):
        ''' Handler for fetch filter selection. '''
        fetchChoice = self.fetchChoice.GetStringSelection()
        # Select from a specific image
        if fetchChoice == 'range':
            self.fetchTxt.SetLabel('of image IDs:')
            self.fetchTxt2.SetLabel('to')
            self.fetchTxt2.Show()
            self.fetchTxt3.SetLabel('images')
            self.fetchTxt3.Show()
            self.startId.Show()
            self.endId.Show()
            self.filterChoice.Enable()
            self.fetch_panel.Layout()

        elif fetchChoice == 'all':
            self.fetchTxt.SetLabel('')
            self.fetchTxt2.Hide()
            self.fetchTxt3.SetLabel('images')
            self.fetchTxt3.Show()
            self.startId.Hide()
            self.endId.Hide()
            self.filterChoice.Enable()
            self.fetch_panel.Layout()

        elif fetchChoice == 'individual':

            self.fetchTxt.SetLabel('image ID:')
            if p.table_id:
                self.startId.Show()
            else:
                self.startId.Hide()
            self.endId.Show()
            self.fetchTxt2.Hide()
            self.fetchTxt3.Hide()
            self.filterChoice.Disable()
            self.fetch_panel.Layout()


    def OnSelectFilter(self, evt):
        ''' Handler for fetch filter selection. '''
        filter = self.filterChoice.GetStringSelection()
        # Select from a specific image
        if filter == 'experiment' or filter in p._filters_ordered:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
        elif filter == 'image' or filter in p._groups_ordered:
            self.SetupFetchFromGroupSizer(filter)
            self.fetchSizer.Show(self.fetchFromGroupSizer, True)
        elif filter == CREATE_NEW_FILTER:
            self.fetchSizer.Hide(self.fetchFromGroupSizer, True)
            from .columnfilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(600, 300))
            if cff.ShowModal() == wx.OK:
                fltr = cff.get_filter()
                fname = cff.get_filter_name()
                p._filters[fname] = fltr
                items = self.filterChoice.GetItems()
                self.filterChoice.SetItems(items[:-1] + [fname] + items[-1:])
                self.filterChoice.Select(len(items) - 1)
            else:
                self.filterChoice.Select(0)
            cff.Destroy()
        self.fetch_panel.Layout()
        self.fetch_panel.Refresh() 

    def SetupFetchFromGroupSizer(self, group):
        '''
        This sizer displays input fields for inputting each element of a
        particular group's key. A group with 2 columns: Gene, and Well,
        would be represented by two combo boxes.
        '''
        if group == 'image':
            fieldNames = ['table', 'image'] if p.table_id else ['image']
            fieldTypes = [int, int]
            validKeys = dm.GetAllImageKeys()
        else:
            fieldNames = dm.GetGroupColumnNames(group)
            fieldTypes = dm.GetGroupColumnTypes(group)
            validKeys = dm.GetGroupKeysInGroup(group)

        self.groupInputs = []
        self.groupFieldValidators = []
        self.fetchFromGroupSizer.Clear(True)
        for i, field in enumerate(fieldNames):
            label = wx.StaticText(self.fetch_panel, wx.NewId(), field + ':')
            # Values to be sorted BEFORE being converted to str
            validVals = list(set([col[i] for col in validKeys]))
            validVals.sort()
            validVals = [str(col) for col in validVals]
            if group == 'image' or fieldTypes[i] == int or fieldTypes[i] == int:
                fieldInp = wx.TextCtrl(self.fetch_panel, -1, value=validVals[0], size=(80, -1))
            else:
                fieldInp = wx.Choice(self.fetch_panel, -1, size=(80, -1),
                                       choices=['__ANY__'] + validVals)
            validVals = ['__ANY__'] + validVals
            fieldInp.SetSelection(0)
            # Create and bind to a text Validator
            def ValidateGroupField(evt, validVals=validVals):
                ctrl = evt.GetEventObject()
                if ctrl.GetValue() in validVals:
                    ctrl.SetForegroundColour('#000001')
                else:
                    ctrl.SetForegroundColour('#FF0000')

            self.groupFieldValidators += [ValidateGroupField]
            fieldInp.Bind(wx.EVT_TEXT, self.groupFieldValidators[-1])
            self.groupInputs += [fieldInp]
            self.fetchFromGroupSizer.Add(label)
            self.fetchFromGroupSizer.Add(fieldInp)
            self.fetchFromGroupSizer.Add(10, 20, 0)

    def ValidateIntegerField(self, evt):
        ''' Validates an integer-only TextCtrl '''
        txtCtrl = evt.GetEventObject()
        # NOTE: textCtrl.SetBackgroundColor doesn't work on Mac
        #   and foreground color only works when not setting to black.
        try:
            int(txtCtrl.GetValue())
            txtCtrl.SetForegroundColour('#000001')
        except(Exception):
            txtCtrl.SetForegroundColour('#FF0000')

    def GetGroupKeyFromGroupSizer(self, group=None):
        ''' Returns the text in the group text inputs as a group key. '''
        if group is not None:
            fieldTypes = dm.GetGroupColumnTypes(group)
        else:
            fieldTypes = [int for input in self.groupInputs]
        groupKey = []
        for input, ftype in zip(self.groupInputs, fieldTypes):
            # GetValue returns unicode from ComboBox, but we need a string
            val = str(input.GetStringSelection())
            # if the value is blank, don't bother typing it, it is a wildcard
            if val != '__ANY__':
                val = ftype(val)
            groupKey += [val]
        return tuple(groupKey)

    def OnShowImageControls(self, evt):
        ''' Shows the image adjustment control panel in a new frame. '''
        self.imageControlFrame = wx.Frame(self, size=(470, 155))
        ImageControlPanel(self.imageControlFrame, self, brightness=self.brightness, scale=self.scale,
                          contrast=self.contrast)
        self.imageControlFrame.Show(True)


    # Saving image thumbnails
    def OnSaveImgThumbnails(self, evt):

        saveDialog = wx.DirDialog(self, "Choose input directory", 
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal() == wx.ID_OK:
            directory = saveDialog.GetPath()

            if not os.path.exists(directory + '/image_gallery'):
                os.makedirs(directory + '/image_gallery')

            for tile in self.galleryBin.tiles:
                imagetools.SaveBitmap(tile.bitmap, directory + '/image_gallery/' + str(tile.obKey) + '.png')

    # Fetch all object thumbnails from displayed images
    def OnFetchObjThumbnails(self, evt):

        self.classBins[0].SelectAll()
        self.classBins[0].RemoveSelectedTiles()
        # Need to run this after removing all tiles!
        def cb():
            for tile in self.galleryBin.tiles:
                pseudo_obKeys = tile.obKey
                imKey = pseudo_obKeys[:-1] # Get image key
                obKeys = db.GetObjectsFromImage(imKey)
                self.classBins[0].AddObjects(obKeys, self.chMap, pos='last', display_whole_image=False)
            
        wx.CallAfter(cb)

    # Fetch all object thumbnails from displayed images
    def OnFetchAllObjThumbnails(self, evt):

        self.classBins[0].SelectAll()
        self.classBins[0].RemoveSelectedTiles()
        # Need to run this after removing all tiles!
        def flatten(*args):
            for x in args:
                if hasattr(x, '__iter__'):
                    for y in flatten(*x):
                        yield y
                else:
                    yield x


        def cb():
            imKeys = db.GetAllImageKeys()
            imKeys = [tuple(list(flatten(x,-1))) for x in imKeys]

            for imKey in imKeys:
                pseudo_obKeys = imKey
                imKey = pseudo_obKeys[:-1] # Get image key
                obKeys = db.GetObjectsFromImage(imKey)
                self.classBins[0].AddObjects(obKeys, self.chMap, pos='last', display_whole_image=False)
            
        wx.CallAfter(cb)



    # Saving image thumbnails
    def OnSaveObjThumbnails(self, evt):

        saveDialog = wx.DirDialog(self, "Choose input directory", 
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if saveDialog.ShowModal() == wx.ID_OK:
            directory = saveDialog.GetPath()

            if not os.path.exists(directory + '/object_gallery'):
                os.makedirs(directory + '/object_gallery')

            for tile in self.classBins[0].tiles:
                imagetools.SaveBitmap(tile.bitmap, directory + '/object_gallery/' + str(tile.obKey) + '.png')


    def SetBrightness(self, brightness):
        ''' Updates the global image brightness across all tiles. '''
        self.brightness = brightness
        [t.SetBrightness(brightness) for bin in self.all_sort_bins() for t in bin.tiles]

    def SetScale(self, scale):
        ''' Updates the global image scaling across all tiles. '''
        self.scale = scale
        [t.SetScale(scale) for bin in self.all_sort_bins() for t in bin.tiles]
        [bin.UpdateSizer() for bin in self.all_sort_bins()]

    def SetContrastMode(self, mode):
        self.contrast = mode
        [t.SetContrastMode(mode) for bin in self.all_sort_bins() for t in bin.tiles]

    def PostMessage(self, message):
        ''' Updates the status bar text and logs to info. '''
        self.SetStatusText(message)
        logging.info(message)

    def OnClose(self, evt):
        ''' Prompt to save training set before closing. '''
        self.Destroy()

    def Destroy(self):
        ''' Kill off all threads before combusting. '''
        super(ImageGallery, self).Destroy()
        import threading
        t = tilecollection.TileCollection()
        if self in t.loader.notify_window:
            t.loader.notify_window.remove(self)
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

    
class StopCalculating(Exception):
    pass


# ----------------- Run -------------------

if __name__ == "__main__":
    from .errors import show_exception_as_dialog

    logging.basicConfig(level=logging.DEBUG, )

    global defaultDir
    defaultDir = os.getcwd()

    # Handles args to MacOS "Apps"
    if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
        del sys.argv[1]

    # Initialize the app early because the fancy exception handler
    # depends on it in order to show a dialog.
    app = wx.App()

    # Install our own pretty exception handler unless one has already
    # been installed (e.g., a debugger)
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = show_exception_as_dialog

    p = Properties()
    db = dbconnect.DBConnect()
    dm = DataModel()

    # Load a properties file if passed as the first argument
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            logging.error('Classifier requires a properties file.  Exiting.')
            wx.GetApp().Exit()

    gallery = ImageGallery(p)
    gallery.Show(True)

    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import javabridge

        javabridge.kill_vm()
    except:
        import traceback

        traceback.print_exc()
        print("Caught exception while killing VM")
