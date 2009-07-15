'''
A collection of tools to modify images used in CPA.
'''

import Image
from Properties import Properties
from DBConnect import DBConnect
from ImageReader import ImageReader
import numpy as np
import wx

p = Properties.getInstance()
db = DBConnect.getInstance()

last_imkey = None
last_image = None

def FetchTile(obKey):
    '''
    returns a list of cropped image data 
        and a list of intensity intervals of the original uncropped images
    '''
    imKey = obKey[:-1]
    pos = db.GetObjectCoords(obKey)
    size = (int(p.image_tile_size),int(p.image_tile_size))
    return [Crop(im,size,pos) for im in FetchImage(imKey)]

def FetchImage(imKey):
    global last_image
    global last_imkey
    if imKey == last_imkey:
        return last_image
    else:
        last_imkey = imKey
    
    ir = ImageReader()
    filenames = db.GetFullChannelPathsForImage(imKey)
    last_image = ir.ReadImages(filenames)
    return last_image

def ShowImage(imKey, chMap, parent=None, brightness=1.0, scale=1.0, contrast=None):
    from ImageViewer import ImageViewer
    imgs = FetchImage(imKey)
    frame = ImageViewer(imgs=imgs, chMap=chMap, img_key=imKey, 
                        parent=parent, title=str(imKey),
                        brightness=brightness, scale=scale,
                        contrast=contrast)
    frame.Show(True)
    return frame

def Crop(imgdata, (w,h), (x,y)):
    '''
    Crops an image to the width (w,h) around the point (x,y).
    Area outside of the image is filled with the color specified.
    '''
    im_width = imgdata.shape[1]
    im_height = imgdata.shape[0]

    x = int(x + 0.5)
    y = int(y + 0.5)

    # find valid cropping region in imgdata
    lox = max(x - w/2, 0)
    loy = max(y - h/2, 0)
    hix = min(x - w/2 + w, im_width)
    hiy = min(y - h/2 + h, im_height)
    
    # find destination
    dest_lox = lox - (x - w/2)
    dest_loy = loy - (y - h/2)
    dest_hix = dest_lox + hix - lox
    dest_hiy = dest_loy + hiy - loy

    crop = np.zeros((h,w), dtype='float32')
    crop[dest_loy:dest_hiy, dest_lox:dest_hix] = imgdata[loy:hiy, lox:hix]
    return crop

def MergeToBitmap(imgs, chMap, brightness=1.0, scale=1.0, masks=[], contrast=None):
    '''
    imgs  - list of np arrays containing pixel data for each channel of an image
    chMap - list of colors to map each corresponding channel onto.  eg: ['red', 'green', 'blue']
    brightness - value around 1.0 to multiply color values by
    contrast - value around 1.0 to scale contrast by
    scale - value around 1.0 to scale the image by
    contrast - contrast mode to use
    '''
    if contrast=='Log':
        logims = [log_transform(im) for im in imgs]
        imData = MergeChannels(logims, chMap, masks=masks)
    elif contrast=='Auto':
        newims = [auto_contrast(im) for im in imgs]
        imData = MergeChannels(newims, chMap, masks=masks)
    else:
        imData = MergeChannels(imgs, chMap, masks=masks)

    h,w = imgs[0].shape
    
    # Convert from float [0-1] to 8bit
    imData *= 255.0
    imData[imData>255] = 255

    # Write wx.Image
    img = wx.EmptyImage(w,h)
    img.SetData(imData.astype('uint8').flatten())
    
    # Apply brightness & scale
    if brightness != 1.0:
        img = img.AdjustChannels(brightness, brightness, brightness)
    if scale != 1.0:
        if w*scale>10 and h*scale>10:
            img.Rescale(w*scale, h*scale)
        else:
            img.Rescale(10,10)
    
    return img.ConvertToBitmap()

def MergeChannels(imgs, chMap, masks=[]):
    '''
    Merges the given image data into the channels listed in chMap.
    Masks are passed in pairs (mask, blendingfunc).
    '''
    nChannels = len(p.image_channel_paths)
    h,w = imgs[0].shape
    imData = np.zeros((h,w,3),dtype='float')
    
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
    
    for mask, func in masks:
        imData = func(imData, mask)
        imData[imData>1.0] = 1.0
        imData[imData<0.0] = 0.0
        
    return imData

def log_transform(im, interval=None):
    '''Takes a single image in the form of a np array and returns it
    log-transformed and scaled to the interval [0,1] '''
    # Check that the image isn't binary 
    # (used to check if it was not all 0's, but this covers both cases)
    # if (im!=0).any()
    (min, max) = interval or (im.min(), im.max())
    if np.any((im>min)&(im<max)):
        im = im.clip(im[im>0].min(), im.max())
        im = np.log(im)
        im -= im.min()
        if im.max() > 0:
            im /= im.max()
    return im

def auto_contrast(im, interval=None):
    '''Takes a single image in the form of a np array and returns it
    scaled to the interval [0,1] '''
    im = im.copy()
    (min, max) = interval or (im.min(), im.max())
    # Check that the image isn't binary 
    if np.any((im>min)&(im<max)):
        im -= im.min()
        if im.max() > 0:
            im /= im.max()
    return im

def SaveBitmap(bitmap, filename, format='PNG'):
    im = BitmapToPIL(bitmap)
    im.save(filename, format)

def ImageToPIL(image):
    '''Convert wx.Image to PIL Image.'''
    pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
    pil.fromstring(image.GetData())
    return pil

def BitmapToPIL(bitmap):
    '''Convert wx.Bitmap to PIL Image.'''
    return ImageToPIL(wx.ImageFromBitmap(bitmap))

def npToPIL(imData):
    '''Convert np image data to PIL Image.'''
    buf = np.dstack(imgData)
    buf = (buf * 255.0).astype('uint8')
    im = Image.fromstring(mode='RGB', size=(imgData[0].shape[1],imgData[0].shape[0]),
                          data=buf.tostring())
    return im

