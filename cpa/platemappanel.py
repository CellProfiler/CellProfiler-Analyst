from .datamodel import *
from . import dbconnect
from .properties import Properties
from . import imagetools
import wx
import numpy as np
import matplotlib.cm
from base64 import b64decode
from .guiutils import BitmapPopup
import imageio

abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# Well Displays
ROUNDED   = 'rounded'
CIRCLE    = 'circle'
SQUARE    = 'square'
IMAGE     = 'image'
THUMBNAIL = 'thumbnail'

all_well_shapes = [SQUARE, ROUNDED, CIRCLE, THUMBNAIL, IMAGE]

class PlateMapPanel(wx.Panel):
    '''
    A Panel that displays a plate layout with wells that are colored by their
    data (in the range [0,1]).  The panel provides mechanisms for selection,
    color mapping, setting row & column labels, and reshaping the layout.
    '''

    def __init__(self, parent, data, well_keys, shape=None,
                 colormap='jet', well_disp=ROUNDED, data_range=None, 
                 toggle_selection_mode=False, **kwargs):
        '''
        ARGUMENTS:
        parent -- wx parent window
        data -- a numpy array of numeric values

        KEYWORD ARGUMENTS:
        shape -- a 2-tuple to reshape the data to (must fit the data)
        well_keys -- list of keys for each well eg: (plate, well)
        colormap -- a colormap name from matplotlib.cm
        well_disp -- ROUNDED, CIRCLE, SQUARE, THUMBNAIL or IMAGE
        data_range -- 2-tuple containing the min and max values that the data 
           should be normalized to. Otherwise the min and max will be taken 
           from the data (ignoring NaNs).
        '''

        wx.Panel.__init__(self, parent, **kwargs)
        
        self.chMap = p.image_channel_colors
        self.plate = None
        self.tip = wx.ToolTip('')
        self.tip.Enable(False)
        self.SetToolTip(self.tip)
        self.hideLabels = False
        self.selection = set([])
        self.outlined = []
        self.repaint = False
        self.outline_style = wx.SHORT_DASH
        self.well_selection_handlers = []   # funcs to call when a well is selected        
        self.SetColorMap(colormap)
        self.well_disp = well_disp
        self.toggle_selection_mode = toggle_selection_mode
        self.SetData(data, shape, data_range=data_range)
        
        self.well_keys = np.ones(np.prod(self.data.shape), dtype=np.object)
        for i in range(len(self.well_keys)):
            self.well_keys[i] = ('Unknown Plate','Unknown Well')
        self.well_keys = self.well_keys.reshape(self.data.shape)
        for key in well_keys:
            self.well_keys[DataModel().get_well_position_from_name(key[-1])] = key
##        for i, key in enumerate(well_keys):
##            if i % self.data.shape[1] == 0:
##                self.well_keys += [[]]	
##            self.well_keys[-1] += [key]

        if self.data.shape[0] <= len(abc):
            self.row_labels = ['%2s'%c for c in abc[:self.data.shape[0]]]
        else:
            self.row_labels = ['%02d'%(i+1) for i in range(self.data.shape[0])]
        self.col_labels = ['%02d'%i for i in range(1,self.data.shape[1]+1)]
        
        # minimum 5 sq. pixels per cell
        self.SetMinSize((self.data.shape[1] * 10.0, self.data.shape[0] * 10.0))

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLClick)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRClick)        

    def SetData(self, data, shape=None, data_range=None, clip_interval=None, clip_mode='rescale'):
        '''
        data -- An iterable containing numeric values. It's shape will be used
           to layout the plate unless overridden by the shape parameter
        shape -- If passed, this will be used to reshape the data. (rows,cols)
        '''
        self.text_data = None
        self.data = np.array(data).astype('float32')
        if shape is not None:
            self.data = self.data.reshape(shape)

        self.SetClipInterval(clip_interval, data_range, clip_mode)

    def SetTextData(self, data):
        '''data -- An iterable containing values to be printed on top of each 
              well. The length of this must match the size of the platemap.
        '''
        self.text_data = np.array(data)
        assert self.data.size == self.text_data.size
        self.text_data = self.text_data.reshape(self.data.shape)

    def SetClipInterval(self, clip_interval, data_range=None, clip_mode='rescale'):
        '''
        Rescales/clips the colormap to fit a new range.
        clip_interval -- iterable pair of values to clip/rescale colors to
        data_range -- 2-tuple containing the extents that the data should be
            normalized to. Otherwise the extents will be taken from the data.
        clip_mode -- whether to rescale the colormap to fit the interval,
            or to simply clip the values.
        '''
        if data_range is None:
            data_range = (np.nanmin(self.data), np.nanmax(self.data))
        self.data_range = data_range
        if clip_interval is None:
            clip_interval = data_range

        if clip_interval[0] == clip_interval[1] or data_range[0] == data_range[1]:
            self.data_scaled = self.data - data_range[0] + 0.5
        else:
            # TODO: Set max, min values to inf, -inf and draw these differently on paint
            if clip_mode == 'rescale':
                self.data_scaled = (self.data - clip_interval[0]) / (clip_interval[1] - clip_interval[0])
            elif clip_mode == 'clip':
                self.data_scaled = (self.data - data_range[0]) / (data_range[1] - data_range[0])
                scaled_interval = (clip_interval - data_range[0]) / (data_range[1] - data_range[0])
                self.data_scaled[self.data_scaled < scaled_interval[0]] = 0.
                self.data_scaled[self.data_scaled > scaled_interval[1]] = 1.
        self.Refresh()

    def SetColLabels(self, labels):
        assert len(labels) >= self.data.shape[1]
        self.col_labels = ['%2s'%c for c in labels]
        self.Refresh()

    def SetRowLabels(self, labels):
        assert len(labels) >= self.data.shape[0]
        self.row_labels = ['%2s'%c for c in labels]
        self.Refresh()

    def SetWellDisplay(self, well_disp):
        '''
        well_disp in PlatMapPanel.ROUNDED,
                     PlatMapPanel.CIRCLE,
                     PlatMapPanel.SQUARE
        '''
        self.well_disp = well_disp
        self.Refresh()

    def SetColorMap(self, map):
        ''' map: the name of a matplotlib.colors.LinearSegmentedColormap instance '''
        self.colormap = matplotlib.cm.get_cmap(map)
        self.Refresh()
        
    def SetWellKeys(self, keys):
        ''' keys - a 2D array of keys uniquely identifying each well in the plate.'''
        self.well_keys = keys
        
    def SetOutlinedWells(self, well_keys):
        '''well_keys: list of the well keys to flag'''
        self.outlined = list(set(well_keys))
        self.repaint = True
        
    def OutlineWells(self, well_keys):
        self.outlined = list(set(self.outlined + well_keys))
        self.repaint = True
        
    def UnOutlineWells(self, well_keys):
        self.outlined = list(set(self.outlined) - set(well_keys))
        self.repaint = True

    def SelectWell(self, well):
        ''' well: 2-tuple of integers indexing a well position (row,col)'''
        self.selection = set([well])
        self.Refresh()

    def ToggleSelected(self, well):
        ''' well: 2-tuple of integers indexing a well position (row,col)'''
        if well in self.selection:
            self.selection.remove(well)
        else:
            self.selection.add(well)
        self.Refresh()

    def GetWellAtCoord(self, x, y):
        '''
        returns a 2 tuple of integers indexing a well position 
                or None if there is no well at the given position.
        '''
        if not hasattr(self, 'xo'):
            return None
        r = min(self.Size[0]/(self.data.shape[1]+1.)/2.,
                self.Size[1]/(self.data.shape[0]+1.)/2.) - 0.5
        i = int((x-2-self.xo)/(r*2+1))
        j = int((y-2-self.yo)/(r*2+1))
        if 0<i<=self.data.shape[1] and 0<j<=self.data.shape[0]:
            return (j-1,i-1)
        else:
            return None

    def GetWellLabelAtCoord(self, x, y):
        '''
        returns the well label at the given x,y position 
        '''
        loc = self.GetWellAtCoord(x,y) 
        if self.well_keys is not None and loc is not None:
            row, col = loc
            return str(self.well_keys[row][col][-1])
        else:
            return None

    def GetWellKeyAtCoord(self, x, y):
        '''
        returns the well key at the given x,y position 
        '''
        loc = self.GetWellAtCoord(x,y) 
        if self.well_keys is not None and loc is not None:
            row, col = loc
            return self.well_keys[row][col]
        else:
            return None
        
    def GetWellKeys(self):
        return [tuple(wk) for wk in self.well_keys]
    
    def get_selected_well_keys(self):
        return [tuple(self.well_keys[row][col]) for row, col in self.selection]

    def OnPaint(self, evt=None):
        dc = wx.PaintDC(self)
        dc.Clear()

        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        cols_data, rows_data = (self.data.shape[1], self.data.shape[0])

        # calculate the well radius
        r = min(w_win/(cols_data+1.)/2.,
                h_win/(rows_data+1.)/2.) - 0.5

        # calculate start position to draw at so image is centered.
        w_data, h_data = ((cols_data+1)*2.*(r+0.5), (rows_data+1)*2.*(r+0.5))
        self.xo, self.yo = (0., 0.)
        if w_win/h_win < w_data/h_data:
            self.yo = (h_win-h_data)/2
        else:
            self.xo = (w_win-w_data)/2

        # Set font size to fit
        font = dc.GetFont()
        if r>14:
            font.SetPixelSize((12,24))
        elif r>6:
            font.SetPixelSize((r-2,(r-2)*2))
        else:
            font.SetPixelSize((3,6))
        wtext, htext = font.GetPixelSize()[0]*2, font.GetPixelSize()[1]
        dc.SetFont(font)

        db = dbconnect.DBConnect()
        bmp = {}
        imgs = {}
        if self.well_disp == IMAGE:
            if p.plate_id:
                wells_and_images = db.execute('SELECT %s, %s FROM %s WHERE %s="%s" GROUP BY %s'%(
                    p.well_id, p.image_id, p.image_table, p.plate_id, self.plate, 
                    p.well_id))
            else:
                wells_and_images = db.execute('SELECT %s, %s FROM %s GROUP BY %s'%(
                    p.well_id, p.image_id, p.image_table, p.well_id))
                
            for well, im in wells_and_images:
                imgs[well] = (im, )
        elif self.well_disp == THUMBNAIL:
            assert p.image_thumbnail_cols, 'No thumbnail columns are defined in the database. Platemap cannot be drawn.'
            if p.plate_id:
                wells_and_images = db.execute('SELECT %s, %s FROM %s WHERE %s="%s" GROUP BY %s'%(
                    p.well_id, ','.join(p.image_thumbnail_cols), p.image_table, 
                    p.plate_id, self.plate, p.well_id))
            else:
                wells_and_images = db.execute('SELECT %s, %s FROM %s GROUP BY %s'%(
                    p.well_id, ','.join(p.image_thumbnail_cols), p.image_table, p.well_id))

            for wims in wells_and_images:
                try:
                    ims = [imageio.imread(b64decode(im)).astype('float32') / 255 for im in wims[1:]]
                except Exception as e:
                    ims = [imageio.imread(im.encode()).astype('float32') / 255 for im in wims[1:]]
                imgs[wims[0]] =  ims

        py = self.yo
        for y in range(rows_data+1):
            texty = py+(2.*r - htext)/2.
            px = self.xo
            for x in range(cols_data+1):
                textx = px+(2.*r - wtext)/2.
                # Draw column headers
                if y==0 and x!=0:
                    dc.DrawText(self.col_labels[x-1], textx, texty)
                # Draw row headers
                elif y!=0 and x==0:
                    dc.DrawText(self.row_labels[y-1], textx, texty)
                px += 2*r+1
            py += 2*r+1

        py = self.yo
        font.SetPixelSize((4,8))
        dc.SetFont(font)
        for y in range(rows_data+1):
            texty = py+(2.*r - htext)/2.
            px = self.xo
            for x in range(cols_data+1):
                textx = px+(2.*r - wtext)/2.
                # Draw wells
                if y>0 and x>0:
                    if (y-1, x-1) in self.selection:
                        # thick black outline for selected wells
                        dc.SetPen(wx.Pen("BLACK",5))
                    elif tuple(self.well_keys[y-1][x-1]) in self.outlined:
                        # thick gray outline for selected wells
                        dc.SetPen(wx.Pen("BLACK",2, style=self.outline_style))
                    else:
                        # normal outline
                        dc.SetPen(wx.Pen("GRAY",0.5))
                    color = np.array(self.colormap(self.data_scaled[y-1][x-1])[:3]) * 255
                    # NaNs get no color
                    if np.isnan(self.data[y-1][x-1]):
                        dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                    else:
                        dc.SetBrush(wx.Brush(color))
                    # Draw Well Display
                    if self.well_disp == ROUNDED:
                        dc.DrawRoundedRectangle(px+1, py+1, r*2, r*2, r*0.75)
                    elif self.well_disp == CIRCLE:
                        dc.DrawCircle(px+r+1, py+r+1, r)
                    elif self.well_disp == SQUARE:
                        dc.DrawRectangle(px+1, py+1, r*2, r*2)
                    elif self.well_disp == THUMBNAIL:
                        wellkey = self.GetWellKeyAtCoord(px+r, py+r)
                        well = wellkey[-1]
                        if well in imgs:
                            size = imgs[well][0].shape
                            scale = r*2./max(size)
                            bmp[well] = imagetools.MergeToBitmap(imgs[well], p.image_channel_colors, scale=scale,
                                                                 display_whole_image=True)
                            dc.DrawBitmap(bmp[well], px+1, py+1)
                    elif self.well_disp == IMAGE:
                        p.image_buffer_size = p.plate_shape[0] * p.plate_shape[1]
                        wellkey = self.GetWellKeyAtCoord(px+r, py+r)
                        well = wellkey[-1]
                        if well in imgs:
                            ims = imagetools.FetchImage(imgs[well])
                            # Hacky rescale for now
                            # Todo: Write proper rescale function
                            for i in range(len(ims)):
                                if ims[i].max() > 1:
                                    ims[i] = ims[i] * (1 / np.iinfo(ims[i].dtype).max)
                            size = ims[0].shape
                            scale = r*2./max(size)
                            bmp[well] = imagetools.MergeToBitmap(ims, p.image_channel_colors, scale=scale,
                                                                 display_whole_image=True)
                            dc.DrawBitmap(bmp[well], px+1, py+1)
                    # Draw text data
                    if self.text_data is not None:
                        if type(self.text_data[y-1][x-1]) == str:
                            dc.DrawText(str(self.text_data[y-1][x-1]), px+3, py+r)
                        else:
                            dc.SetPen(wx.Pen("GRAY",1))
                            dc.DrawLine(px+3, py+3, px+r*2-2, py+r*2-2)
                            dc.DrawLine(px+3, py+r*2-2, px+r*2-2, py+3)                            
                    # Draw X
                    elif np.isnan(self.data[y-1][x-1]):
                        dc.SetPen(wx.Pen("GRAY",1))
                        dc.DrawLine(px+3, py+3, px+r*2-2, py+r*2-2)
                        dc.DrawLine(px+3, py+r*2-2, px+r*2-2, py+3)
                px += 2*r+1
            py += 2*r+1
        return dc

    def OnSize(self, evt):
        self.repaint = True

    def OnIdle(self, evt):
        if self.repaint:
            self.Refresh()
            self.repaint = False

    def add_well_selection_handler(self, handler):
        '''handler -- a function to call on well selection. The handler must
              take a single well_key parameter.
        '''
        self.well_selection_handlers += [handler]
            
    def GetX(self, evt):
        if wx.VERSION[0] >= 2 and wx.VERSION[1] > 8:
            return evt.GetX() 
        else:
            return evt.X
        
    def GetY(self, evt):
        if wx.VERSION[0] >= 2 and wx.VERSION[1] > 8:
            return evt.GetY() 
        else:
            return evt.Y
        
    def OnLClick(self, evt):
        well = self.GetWellAtCoord(self.GetX(evt), self.GetY(evt))
        
        if well is None:
            return        
        
        if evt.ShiftDown() or self.toggle_selection_mode:
            self.ToggleSelected(well)
        else:
            self.SelectWell(well)
            
        for handler in self.well_selection_handlers:
            handler()
                
        evt.Skip()

    def SetPlate(self, plate):
        self.plate = plate

    def OnMotion(self, evt):
        well = self.GetWellAtCoord(self.GetX(evt), self.GetY(evt))
        wellLabel = self.GetWellLabelAtCoord(self.GetX(evt), self.GetY(evt))
        if well is not None and wellLabel is not None:
            self.tip.SetTip('%s: %s'%(wellLabel,self.data[well]))
            self.tip.Enable(True)
        else:
            self.tip.Enable(False)
            
    def OnDClick(self, evt):
        if self.plate is not None:
            well = self.GetWellLabelAtCoord(self.GetX(evt), self.GetY(evt))
            imKeys = db.execute('SELECT %s FROM %s WHERE %s="%s" AND %s="%s"'%
                                (UniqueImageClause(), p.image_table, p.well_id, well, p.plate_id, self.plate), silent=False)
            for imKey in imKeys:
                imagetools.ShowImage(imKey, self.chMap, parent=self)

    def OnRClick(self, evt):
        well_label = self.GetWellLabelAtCoord(self.GetX(evt), self.GetY(evt))
        wellkey = self.GetWellKeyAtCoord(self.GetX(evt), self.GetY(evt))
        if wellkey is None:
            return 
        imkeys = db.execute('SELECT %s FROM %s WHERE %s ORDER BY %s'%
                            (UniqueImageClause(), p.image_table, 
                             dbconnect.GetWhereClauseForWells([wellkey]),
                             p.image_id))

        popupMenu = wx.Menu()
        popupMenu.SetTitle('well: %s'%(well_label))
        if p.image_thumbnail_cols:
            item = popupMenu.Append(-1, 'Show thumbnail montage')
            show_montage = lambda e: self.show_thumbnail_montage(wellkey, (self.GetX(evt), self.GetY(evt)))
            popupMenu.Bind(wx.EVT_MENU, show_montage, item)
        for key in imkeys:
            item = popupMenu.Append(-1, ','.join([str(k) for k in key]))
            def handler(evt, key=key):
                imagetools.ShowImage(key, self.chMap, parent=self)
            popupMenu.Bind(wx.EVT_MENU, handler, item)
        self.PopupMenu(popupMenu, (self.GetX(evt), self.GetY(evt)))
        
    def show_thumbnail_montage(self, wellkey, pos):
        images = db.execute('SELECT %s FROM %s WHERE %s ORDER BY %s'%
                            (','.join(p.image_thumbnail_cols), p.image_table,
                             dbconnect.GetWhereClauseForWells([wellkey]),
                             p.image_id))
        if images == []:
            return
        imsets = []
        for channels in images:
            try:
                imsets += [[imageio.imread(b64decode(im)).astype('float32') / 255 for im in channels]]
            except Exception as e:
                imsets += [[imageio.imread(im.encode()).astype('float32') / 255 for im in channels]]

        n_channels = len(imsets[0])
        composite = []
        for i in range(n_channels):
            # composite each channel separately
            composite += [imagetools.tile_images([imset[i] for imset in imsets])]
        bmp = imagetools.MergeToBitmap(composite, p.image_channel_colors, display_whole_image=True)
        
        popup = BitmapPopup(self, bmp, pos=pos)
        popup.Show()

        
if __name__ == "__main__":
    app = wx.App()

    data = np.arange(5600.)
    a = np.zeros((40,140))
    i = 0
    for r, row in enumerate(a):
        if r % 2 == 0:
            a[r] = data[i:i+140]
        else:
            a[r]= np.array(list(reversed(data[i:i+140])))
        i += 140
#    labels = [str(i) for i in xrange(1,5601)]
##    data = np.arange(384).reshape(16,24)
##    data[100:102] = np.nan
    frame = wx.Frame(None, size=(900.,800.))
    pmp = PlateMapPanel(frame, a, well_keys=[], well_disp='square')
##    p.SetTextData(data)
    frame.Show()

    app.MainLoop()
