'''
ImageCollection.py
Authors: afraser

A collection of tools to modify images used in CPA.
'''

import numpy
import wx
from Properties import Properties

p = Properties.getInstance()


def ShowImage(imKey, chMap, parent=None):
    from ImageViewer import ImageViewer
    from ImageCollection import ImageCollection
    IC = ImageCollection.getInstance()
    imgs = IC.FetchImage(imKey)
    frame = ImageViewer(imgs=imgs, chMap=chMap, parent=parent, title=str(imKey) )
    frame.Show(True)
    

def Crop(imgdata, (w,h), (x,y)):
    '''
    Crops an image to the width (w,h) around the point (x,y).
    Area outside of the image is filled with the color specified.
    '''
    imWidth = imgdata.shape[1]
    imHeight = imgdata.shape[0]
    crop = numpy.zeros((h,w), dtype='float32')
    for px in xrange(w):
        for py in xrange(h):
            xx = px+x-w/2
            yy = py+y-h/2
            if 0<=xx<imWidth and 0<=yy<imHeight:
                crop[py,px] = imgdata[yy,xx]
            else:
                crop[py,px] = 0
    return crop


def MergeToBitmap(imgs, chMap, selected=0):
    '''
    imgs  - list of numpy arrays containing pixel data for each channel of an image
    chMap - list of colors to map each corresponding channel onto.  eg: ['red', 'green', 'blue']
    selected - 0/1, whether to draw a white outline around the image 
    '''
    
    imData = MergeChannels(imgs, chMap)
    h,w = imgs[0].shape
    
    # Outline in white if selected
    if selected: 
        imData[0:h,0,:]  = 1.0 # left
        imData[0,0:w,:]  = 1.0 # top
        imData[0:h,-1,:]  = 1.0 # right
        imData[-1,0:w,:]  = 1.0 # bottom   
    
    # Convert from float [0-1] to 8bit
    imData *= 255.0
    imData[imData>255] = 255

    # Write to bitmap
    img = wx.EmptyImage(w,h)
    img.SetData( imData.astype('uint8').flatten() )
    return img.ConvertToBitmap()


def MergeChannels(imgs, chMap):
    ''' Merges the given image data into the channels listed in chMap. '''
    nChannels = len(p.image_channel_paths)
    h,w = imgs[0].shape
    imData = numpy.zeros((h,w,3),dtype='float')
    
    colormap = {'red'      : [1,0,0], 
                'green'    : [0,1,0], 
                'blue'     : [0,0,1], 
                'cyan'     : [0,1,1], 
                'yellow'   : [1,1,0], 
                'magenta'  : [1,0,1],
                'gray'     : [1,1,1],
                'none'     : [0,0,0] }
    
    for i, im in enumerate(imgs):
        c = colormap[chMap[i].lower()]
        for chan in range(3):
            imData[:,:,chan] += im * c[chan]
        
    return imData




def HighlightCellsInClass(cl):
    obKeysToTry = dm.GetAllObjectsFromImage(100,imKeysInGroup)
    stump_query, score_query, find_max_query, class_query, count_query = MulticlassSQL.translate(self.weaklearners, self.trainingSet.colnames, p.object_table)
    obKeys += MulticlassSQL.FilterObjectsFromClassN(obClass, obKeysToTry, stump_query, score_query, find_max_query)


def AdjustBrightness():
    pass


def AdjustContrast():
    pass




