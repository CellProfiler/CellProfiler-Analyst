'''
A collection of tools to modify images used in CPA.
'''

import PIL.Image as Image
import pilfix
from properties import Properties
import dbconnect
from imagereader import ImageReader
import logging
import matplotlib.image
import numpy as np
import wx

p = Properties.getInstance()
db = dbconnect.DBConnect.getInstance()

cache = {}
cachedkeys = []

def FetchTile(obKey):
    '''returns a list of image channel arrays cropped around the object
    coordinates
    '''
    imKey = obKey[:-1]
    pos = list(db.GetObjectCoords(obKey))
    if None in pos:
        message = ('Failed to load coordinates for object key %s. This may '
                   'indicate a problem with your per-object table.\n'
                   'You can check your per-object table "%s" in TableViewer'
                   %(', '.join(['%s:%s'%(col, val) for col, val in 
                                zip(dbconnect.object_key_columns(), obKey)]), 
                   p.object_table))
        wx.MessageBox(message, 'Error')
        logging.error(message)
        return None
    size = (int(p.image_tile_size), int(p.image_tile_size))
    # Could transform object coords here
    imgs = FetchImage(imKey)
    if p.rescale_object_coords:
        pos[0] *= p.image_rescale[0] / p.image_rescale_from[0]
        pos[1] *= p.image_rescale[1] / p.image_rescale_from[1]
    return [Crop(im, size, pos) for im in imgs]

def FetchImage(imKey):
    global cachedkeys
    if imKey in cache.keys():
        return cache[imKey]
    else:
        ir = ImageReader()
        filenames = db.GetFullChannelPathsForImage(imKey)
        imgs = ir.ReadImages(filenames)                    
        cache[imKey] = imgs
        cachedkeys += [imKey]
        while len(cachedkeys) > int(p.image_buffer_size):
            del cache[cachedkeys.pop(0)]
        return cache[imKey]

def ShowImage(imKey, chMap, parent=None, brightness=1.0, scale=1.0, contrast=None):
    from imageviewer import ImageViewer
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

    # XXX - hack to make scaling work per-image instead of per-tile
    crop[0, 0] = imgdata.min()
    crop[-1, -1] = imgdata.max()

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
    
    imData = np.zeros((h,w,3), dtype='float')
    
    for i, im in enumerate(imgs):
        if blending[i].lower() == 'add':
            c = colormap[chMap[i].lower()]
            for chan in range(3):
                imData[:,:,chan] += im * c[chan]
    
    imData[imData>1.0] = 1.0
    imData[imData<0.0] = 0.0
    
    for i, im in enumerate(imgs):
        if blending[i].lower() == 'subtract':
            c = colormap[chMap[i].lower()]
            for chan in range(3):
                imData[:,:,chan] -= im * c[chan]

    imData[imData>1.0] = 1.0
    imData[imData<0.0] = 0.0
    
    for i, im in enumerate(imgs):
        if blending[i].lower() == 'solid':
            if chMap[i].lower() != 'none':
                c = colormap[chMap[i].lower()]
                for chan in range(3):
                    imData[:,:,chan][im == 1] = c[chan]
            
    imData[imData>1.0] = 1.0
    imData[imData<0.0] = 0.0
    
    for mask, func in masks:
        imData = func(imData, mask)

    return imData

def check_image_shape_compatibility(imgs):
    '''If all of the images are not of the same shape, then prompt the user
    to choose a shape to resize them to.
    '''
    if not p.image_rescale:
        if np.any([imgs[i].shape != imgs[0].shape for i in xrange(len(imgs))]):
            dims = [im.shape for im in imgs]
            aspect_ratios = [float(dims[i][0])/dims[i][1] for i in xrange(len(dims))]
            def almost_equal(expected, actual, rel_err=1e-7, abs_err=1e-20):
                absolute_error = abs(actual - expected)
                return absolute_error <= max(abs_err, rel_err * abs(expected))
            for i in xrange(len(aspect_ratios)):
                if not almost_equal(aspect_ratios[0], aspect_ratios[i], abs_err=0.01):
                    raise Exception('Can\'t merge image channels. Aspect ratios do not match.')
            areas = map(np.product, dims)
            max_idx = areas.index(max(areas))
            min_idx = areas.index(min(areas))
            
            s = [imgs[max_idx].shape, imgs[min_idx].shape]
            
            if p.use_larger_image_scale:
                p.image_rescale = map(float, imgs[max_idx].shape)
                if p.rescale_object_coords:
                    p.image_rescale_from = map(float, imgs[min_idx].shape)
            else:
                p.image_rescale = map(float, imgs[min_idx].shape)
                if p.rescale_object_coords:
                    p.image_rescale_from = map(float, imgs[max_idx].shape)
            
#            dlg = wx.SingleChoiceDialog(None, 
#                     'Some of your images were found to have different\n'
#                     'scales. Please choose a size and CPA will\n'
#                     'automatically rescale image channels to fit a\n'
#                     'single image.',
#                     'Inconsistent image channel sizes',
#                     [str(s[0]), str(s[1])])
#            if dlg.ShowModal() == wx.ID_OK:
#                dims = eval(dlg.GetStringSelection())
#                p.image_rescale = dims
#                dlg = wx.MessageDialog(None,
#                        'Your %s coordinates may need to be rescaled as\n'
#                        ' well in order to crop the images properly for\n'
#                        'Classifier.\n'
#                        'Rescale %s coordinates?'%(p.object_name[1], p.object_name[1]),
#                        'Rescale %s coordinates?'%(p.object_name[1]),
#                        wx.YES_NO|wx.ICON_QUESTION)
#                if dlg.ShowModal() == wx.ID_YES:
#                    p.rescale_object_coords = True
#                    p.image_rescale_from = set(s).difference([dims]).pop()

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

def tile_images(images):
    '''
    images - a list of images (arrays) of the same dimensions
    returns an image that is a composite of the given images tiled in in as
       nearly a square grid as possible
    '''        
    h, w = [int(x) for x in images[0].shape]
    for im in images:
        assert (im.shape == (h,w)), 'Images must be the same size to tile them.'
    cols = int(np.ceil(len(images)**0.5))
    
    composite = np.zeros((h, w * cols))
    i = 0
    for row in range(0, cols * h, h):
        for col in range(0, cols * w, w):
            composite[row : row + h, col : col + w] = images[i]
            i += 1
            if i >= len(images): break
        if i >= len(images): break
        # add another row
        composite = np.vstack((composite, np.zeros((h, w * cols))))
        row += h
    return composite

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
        if np.all(x[:,0] == x):
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
        if (x[:,:,3] == 255).all():
            return x[:,:,:3]
        return x
