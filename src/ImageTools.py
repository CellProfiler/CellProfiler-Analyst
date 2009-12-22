'''
A collection of tools to modify images used in CPA.
'''

import Image
import PILfix
from Properties import Properties
from DBConnect import DBConnect
from ImageReader import ImageReader
import matplotlib.image
import numpy as np
import wx

p = Properties.getInstance()
db = DBConnect.getInstance()

#last_imkey = None
#last_image = None
cache = {}
cachedkeys = []

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
#    global last_image
#    global last_imkey
#    if imKey == last_imkey:
#        return last_image
#    else:
#        last_imkey = imKey
    global cachedkeys
    if imKey in cache.keys():
        return cache[imKey]
    else:
        ir = ImageReader()
        filenames = db.GetFullChannelPathsForImage(imKey)
        cache[imKey] = ir.ReadImages(filenames)
        cachedkeys += [imKey]
        while len(cachedkeys) > int(p.image_buffer_size):
            del cache[cachedkeys.pop(0)]
        return cache[imKey]

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
    chMap - list of colors to map each corresponding channel onto.  
            eg: ['red', 'green', 'blue']
    brightness - value around 1.0 to multiply color values by
    contrast - value around 1.0 to scale contrast by
    scale - value around 1.0 to scale the image by
    masks - not currently used, see MergeChannels
    contrast - contrast mode to use
    blending - list, how to blend this channel with others 'add' or 'subtract'
               eg: ['add','add','add','subtract']
    '''
    if contrast=='Log':
        logims = [log_transform(im) for im in imgs]
        imData = MergeChannels(logims, chMap, masks=masks)
    elif contrast=='Linear':
        newims = [auto_contrast(im) for im in imgs]
        imData = MergeChannels(newims, chMap, masks=masks)
    else:
        imData = MergeChannels(imgs, chMap, masks=masks)
        
    h,w = imgs[0].shape
    
    # Convert from float [0-1] to 8bit
    imData *= 255.0
    imData[imData>255] = 255

    # Write wx.Image
    if p.image_rescale:
        img = wx.EmptyImage(p.image_rescale[1], p.image_rescale[0])
    else:
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
    
    n_channels = sum(map(int, p.channels_per_image))
    blending = p.image_channel_blend_modes or ['add']*n_channels
    h,w = imgs[0].shape
    
    colormap = {'red'      : [1,0,0], 
                'green'    : [0,1,0], 
                'blue'     : [0,0,1], 
                'cyan'     : [0,1,1], 
                'yellow'   : [1,1,0], 
                'magenta'  : [1,0,1], 
                'gray'     : [1,1,1], 
                'none'     : [0,0,0] }
    
    if not p.image_rescale:
        # Check image shape compatibility
        if np.any([imgs[i].shape!=imgs[0].shape for i in xrange(len(imgs))]):
            dims = [im.shape for im in imgs]
            aspect_ratios = [float(dims[i][0])/dims[i][1] for i in xrange(len(dims))]
            def almost_equal(expected, actual, rel_err=1e-7, abs_err=1e-20):
                absolute_error = abs(actual - expected)
                return absolute_error <= max(abs_err, rel_err * abs(expected))
            for i in xrange(len(aspect_ratios)):
                assert (almost_equal(aspect_ratios[0], aspect_ratios[i], abs_err=0.01),
                        'Can\'t merge image channels. Aspect ratios do not match.')
            areas = map(np.product, dims)
            max_idx = areas.index(max(areas))
            min_idx = areas.index(min(areas))
            
            s = [imgs[max_idx].shape, imgs[min_idx].shape]
            dlg = wx.SingleChoiceDialog(None, 'Some of your images were found to have different\n'
                                       'scales. Please choose a size and CPA will\n'
                                       'automatically rescale image channels to fit a\n'
                                       'single image.',
                                       'Inconsistent image channel sizes',
                                       [str(s[0]), str(s[1])])
            if dlg.ShowModal() == wx.ID_OK:
                dims = eval(dlg.GetStringSelection())
                p.image_rescale = dims
            else:
                return None
    
    if p.image_rescale:
        imData = np.zeros((p.image_rescale[0], p.image_rescale[1], 3), dtype='float')
    else:
        imData = np.zeros((h,w,3), dtype='float')
    
    for i, im in enumerate(imgs):
        if blending[i].lower() == 'add':
            if p.image_rescale and im.shape != p.image_rescale:
                im = rescale(im, (p.image_rescale[1], p.image_rescale[0]))
            c = colormap[chMap[i].lower()]
            for chan in range(3):
                imData[:,:,chan] += im * c[chan]
    
    imData[imData>1.0] = 1.0
    imData[imData<0.0] = 0.0
    
    for i, im in enumerate(imgs):
        if blending[i].lower() == 'subtract':
            if p.image_rescale and im.shape != p.image_rescale:
                im = rescale(im, (p.image_rescale[1], p.image_rescale[0]))
            c = colormap[chMap[i].lower()]
            for chan in range(3):
                imData[:,:,chan] -= im * c[chan]
            
    imData[imData>1.0] = 1.0
    imData[imData<0.0] = 0.0
    
    for mask, func in masks:
        imData = func(imData, mask)

    return imData

def rescale(im, scale):
    from scipy.misc import imresize
    return imresize(im, (scale[1], scale[0])) / 255.

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
    if format.lower() in ['jpg', 'jpeg']:
        im.save(filename, format, quality=95)
    else:
        im.save(filename, format)

def ImageToPIL(image):
    '''Convert wx.Image to PIL Image.'''
    pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
    pil.fromstring(image.GetData())
    return pil

def BitmapToPIL(bitmap):
    '''Convert wx.Bitmap to PIL Image.'''
    return ImageToPIL(wx.ImageFromBitmap(bitmap))

def npToPIL(imdata):
    '''Convert np image data to PIL Image'''
    if type(imdata) == list:
        buf = np.dstack(imdata)
    elif len(imdata.shape) == 2:
        buf = np.dstack([imdata, imdata, imdata])
    elif len(imdata.shape) == 3:
        buf = imdata
        assert imdata.shape[2] >=3, 'Cannot convert the given numpy array to PIL'
    if buf.dtype != 'uint8':
        buf = (buf * 255.0).astype('uint8')
    im = Image.fromstring(mode='RGB', size=(buf.shape[1],buf.shape[0]),
                          data=buf.tostring())
    return im


def pil_to_np( pilImage ):
    """
    load a PIL image and return it as a numpy array of uint8.  For
    grayscale images, the return array is MxN.  For RGB images, the
    return value is MxNx3.  For RGBA images the return value is MxNx4
    """
    def toarray(im):
        'return a 1D array of floats'
        x_str = im.tostring('raw', im.mode)
        x = np.fromstring(x_str,np.uint8)
        return x

    
    if pilImage.mode[0] == 'P':
        im = pilImage.convert('RGBA')
        x = toarray(im)
        x = x.reshape(-1, 4)
        if (x[:,0] == x).all():
            im = pilImage.convert('L')
        pilImage = im


    if pilImage.mode[0] in ('1', 'L', 'I', 'F'):
        x = toarray(pilImage)
        x.shape = pilImage.size[1], -1
        return x
    else:
        x = toarray(pilImage.convert('RGBA'))
        x.shape = pilImage.size[1], pilImage.size[0], 4
        # discard alpha if all 1s
        if (x[:,:,4] == 255).all():
            return x[:,:,:3]
        return x
