from DataModel import *
from DBConnect import DBConnect
from Properties import Properties
import ImageTools
import wx
import numpy as np
import matplotlib.cm

abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# Well Shapes
ROUNDED  = 'rounded'
CIRCLE   = 'circle'
SQUARE   = 'square'
IMAGE    = 'image'

all_well_shapes = [SQUARE, ROUNDED, CIRCLE, IMAGE]

class PlateMapPanel(wx.Panel):
    '''
    A Panel that displays a plate layout with wells that are colored by their
    data (in the range [0,1]).  The panel provides mechanisms for selection,
    color mapping, setting row & column labels, and reshaping the layout.
    '''
    
    def __init__(self, parent, data, shape=None, well_labels=None,
                 colormap='jet', wellshape=ROUNDED, row_label_format=None,
                 data_range=None, **kwargs):
        '''
        ARGUMENTS:
        parent -- wx parent window
        data -- a numpy array of numeric values
        
        KEYWORD ARGUMENTS:
        shape -- a 2-tuple to reshape the data to (must fit the data)
        well_labels -- list of labels for each well (must be same len as data)
        colormap -- a colormap name from matplotlib.cm
        wellshape -- ROUNDED, CIRCLE, or SQUARE
        row_label_format -- 'ABC' or '123'
        data_range -- 2-tuple containing the min and max values that the data 
           should be normalized to. Otherwise the min and max will be taken 
           from the data (ignoring NaNs).
        '''
        
        wx.Panel.__init__(self, parent, **kwargs)
        self.hideLabels = False
        self.selection = set([])
        self.SetColorMap(colormap)
        self.wellshape = wellshape
        self.SetData(data, shape, data_range=data_range)
        if row_label_format is None:
            if self.data.shape[0] <= len(abc):
                self.row_label_format = 'ABC'
            else:
                self.row_label_format = '123'
        else:
            self.row_label_format = row_label_format
        self.SetWellLabels(well_labels)
        
        if self.row_label_format == 'ABC':
            self.row_labels = ['%2s'%c for c in abc[:self.data.shape[0]]]
        elif self.row_label_format == '123':
            self.row_labels = ['%02d'%(i+1) for i in range(self.data.shape[0])]
        self.col_labels = ['%02d'%i for i in range(1,self.data.shape[1]+1)]
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.repaint = False
        self.Bind(wx.EVT_SIZE, self._onsize)
        self.Bind(wx.EVT_IDLE, self._onidle)
       
    def SetData(self, data, shape=None, data_range=None, clip_interval=None, clip_mode='rescale'):
        '''
        data -- An iterable containing numeric values. It's shape will be used
           to layout the plate unless overridden by the shape parameter
        shape -- If passed, this will be used to reshape the data. (rows,cols)
        '''
        self.data = np.array(data).astype('float')
        if shape is not None:
            self.data = self.data.reshape(shape)
            
        self.SetClipInterval(clip_interval, data_range, clip_mode)
        
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
        
    def SetWellLabels(self, labels):
        if labels is None:
            if self.row_label_format=='ABC':
                self.well_labels = np.array(['%s%02d'%(abc[i],j+1)
                                    for i in xrange(self.data.shape[0])
                                    for j in xrange(self.data.shape[1])])
            elif self.row_label_format=='123':
                self.well_labels = np.array(['(row:%d col:%d)'%(i+1,j+1)
                                    for i in xrange(self.data.shape[0])
                                    for j in xrange(self.data.shape[1])])
        else:
            assert len(labels) == self.data.shape[0]*self.data.shape[1]
            self.well_labels = np.array(labels)
        self.well_labels = self.well_labels.reshape(self.data.shape)
        
    def SetWellShape(self, wellshape):
        '''
        wellshape in PlatMapPanel.ROUNDED,
                     PlatMapPanel.CIRCLE,
                     PlatMapPanel.SQUARE
        '''
        self.wellshape = wellshape
        self.Refresh()
        
    def SetColorMap(self, map):
        ''' map: the name of a matplotlib.colors.LinearSegmentedColormap instance '''
        self.colormap = matplotlib.cm.get_cmap(map)
        self.Refresh()
        
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
        if self.well_labels is not None and loc is not None:
            row, col = loc
            return self.well_labels[row,col]
        else:
            return None
        
    def OnPaint(self, evt=None):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        
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

        if self.wellshape == IMAGE:
            bmp = {}
            db = DBConnect.getInstance()
            wells_and_images = db.execute('SELECT %s, %s FROM %s GROUP BY %s'%(p.well_id, p.image_id, p.image_table, p.well_id))
            imgs = {}
            for well, im in wells_and_images:
                imgs[well] = (im, )

        py = self.yo
        i=0
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
                # Draw wells
                elif y>0 and x>0:
                    if (y-1, x-1) in self.selection:
                        dc.SetPen(wx.Pen("BLACK",5))
                    else:
                        dc.SetPen(wx.Pen("BLACK",0.5))
                    color = np.array(self.colormap(self.data_scaled[y-1][x-1])[:3]) * 255
                    # NaNs get no color
                    if np.isnan(self.data[y-1][x-1]):
                        dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                    else:
                        dc.SetBrush(wx.Brush(color))
                    # Draw Well Shape
                    if self.wellshape == ROUNDED:
                        dc.DrawRoundedRectangle(px+1, py+1, r*2, r*2, r*0.75)
                    elif self.wellshape == CIRCLE:
                        dc.DrawCircle(px+r+1, py+r+1, r)
                    elif self.wellshape == SQUARE:
                        dc.DrawRectangle(px+1, py+1, r*2, r*2)
                    elif self.wellshape == IMAGE:
                        p.image_buffer_size = int(p.plate_type)
                        well = self.GetWellLabelAtCoord(px+r, py+r)
                        if imgs.has_key(well):
                            ims = ImageTools.FetchImage(imgs[well])
                            size = ims[0].shape
                            scale = r*2./max(size)
                            bmp[well] = ImageTools.MergeToBitmap(ims, p.image_channel_colors, scale=scale)
                            dc.DrawBitmap(bmp[well], px+1, py+1)
                    # Draw X
                    if np.isnan(self.data[y-1][x-1]):
                        dc.SetPen(wx.Pen("GRAY",1))
                        dc.DrawLine(px+3, py+3, px+r*2-2, py+r*2-2)
                        dc.DrawLine(px+3, py+r*2-2, px+r*2-2, py+3)    
                    i+=1
                px += 2*r+1
            py += 2*r+1
        dc.EndDrawing()
        return dc

    def _onsize(self, evt):
        self.repaint = True
        
    def _onidle(self, evt):
        if self.repaint:
            self.Refresh()
            self.repaint = False


if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    # test plate map panel
    data = np.arange(5600.)
    labels = [str(i) for i in xrange(1,5601)]
#    data = np.ones(384)
    data[100:102] = np.nan
    frame = wx.Frame(None, size=(900.,800.))
    p = PlateMapPanel(frame, data, shape=(40,140), well_labels=labels, wellshape='square', data_range=(400,500))
    frame.Show()
    
    app.MainLoop()
    
    
    
