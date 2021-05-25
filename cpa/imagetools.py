'''
A collection of tools to modify images used in CPA.
'''

import PIL.Image as Image
from . import pilfix
from .properties import Properties
from . import dbconnect
from .imagereader import ImageReader
import logging
import scipy.ndimage
import numpy as np
import wx

p = Properties()
db = dbconnect.DBConnect()

cache = {}
cachedkeys = []

cachedparams = None
cachedresult = None

def FetchTile(obKey, display_whole_image=False):
    '''returns a list of image channel arrays cropped around the object
    coordinates
    '''
    imKey = obKey[:-1]
    # Could transform object coords here
    imgs = FetchImage(imKey)
    if imgs is None:
        # Loading failed, return gracefully.
        return
    
    size = (int(p.image_size),int(p.image_size))
    if display_whole_image:
        return imgs

    else:
        size = (int(p.image_tile_size), int(p.image_tile_size))
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
        if p.rescale_object_coords:
            pos[0] *= p.image_rescale[0] / p.image_rescale_from[0]
            pos[1] *= p.image_rescale[1] / p.image_rescale_from[1]
    
        return [Crop(im, size, pos) for im in imgs]

def FetchImage(imKey):
    global cachedkeys
    if imKey in cache:
        return cache[imKey]
    else:
        ir = ImageReader()
        filenames = db.GetFullChannelPathsForImage(imKey)
        try:
            log_io = wx.GetApp().frame.log_io
        except:
            log_io = True
        imgs = ir.ReadImages(filenames, log_io)
        if imgs is None:
            # Loading failed
            return
        cache[imKey] = imgs
        cachedkeys += [imKey]
        while len(cachedkeys) > int(p.image_buffer_size):
            del cache[cachedkeys.pop(0)]
        return cache[imKey]

def ShowImage(imKey, chMap, parent=None, brightness=1.0, scale=1.0, contrast=None):
    from .imageviewer import ImageViewer
    imgs = FetchImage(imKey)
    if imgs is None:
        return
    frame = ImageViewer(imgs=imgs, chMap=chMap, img_key=imKey, 
                        parent=parent, title=str(imKey),
                        brightness=brightness, scale=scale,
                        contrast=contrast)
    frame.Show(True)
    return frame

def Crop(imgdata, xxx_todo_changeme, xxx_todo_changeme1):
    '''
    Crops an image to the width (w,h) around the point (x,y).
    Area outside of the image is filled with the color specified.
    '''
    (w,h) = xxx_todo_changeme
    (x,y) = xxx_todo_changeme1
    im_width = imgdata.shape[1]
    im_height = imgdata.shape[0]

    x = int(x + 0.5)
    y = int(y + 0.5)

    # find valid cropping region in imgdata
    lox = max(x - w//2, 0)
    loy = max(y - h//2, 0)
    hix = min(x - w//2 + w, im_width)
    hiy = min(y - h//2 + h, im_height)
    
    # find destination
    dest_lox = lox - (x - w//2)
    dest_loy = loy - (y - h//2)
    dest_hix = dest_lox + hix - lox
    dest_hiy = dest_loy + hiy - loy

    crop = np.zeros((h,w), dtype='float32')
    crop[dest_loy:dest_hiy, dest_lox:dest_hix] = imgdata[loy:hiy, lox:hix]

    # XXX - hack to make scaling work per-image instead of per-tile
    crop[0, 0] = imgdata.min()
    crop[-1, -1] = imgdata.max()

    return crop

def MergeToBitmap(imgs, chMap, brightness=1.0, scale=1.0, masks=[], contrast=None, display_whole_image=False):
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
    # The imageio tile loader is fast enough that it can replace temporary tile data before bitmap merging completes.
    # So let's make a copy of the original image data stack while we work.
    imgs = imgs.copy()

    '''
    This is a bit hacky, but right now the tileloader needs to see and merge several channels when making temporary tiles.
    The merging process is pretty slow and makes loading data sets painful. We can't easily avoid tile generation, but we can
    try to figure out if we're using a temporary tile. Temp tiles will always be identical, so we can cache and send back the
    completed temporary tile.
    '''
    global cachedparams
    global cachedresult
    # Laziest "hash" ever, but it'll do.
    imghash = [id(im) for im in imgs]
    # In temporary tiles, [0,0] is always set to 0 to aid contrasting.
    if cachedparams is not None and imgs[0][0][0] == 0:
        if cachedparams == [imghash, chMap, brightness, scale, masks, contrast, display_whole_image]:
            return cachedresult
    cachedparams = [imghash, chMap, brightness, scale, masks, contrast, display_whole_image]

    # Before any resizing, record the genuine full intensity range of each image.
    limits = [(im.min(), im.max()) for im in imgs]
    if not display_whole_image:
        # Rescaling 2k x 2k images to make a 25 x 25 tile is slow and silly.
        # Here we check whether the input image is more than 10x the final tile size.
        # If it is, we'll do a quick and dirty rescale to give a more managable starting point.
        tgt_h = int(p.image_size) * 4
        tgt_w = int(p.image_size) * 4
        h, w = imgs[0].shape
        if tgt_h < h and tgt_w < w:
            rescale_factor = max(tgt_h / h, tgt_w / w)
            # imgs = [scipy.ndimage.zoom(im, (rescale_factor, rescale_factor), order=1, prefilter=False,
            #                            mode="grid-constant", grid_mode=True) for im in imgs]
            tgtsize = (int(w * rescale_factor), int(h * rescale_factor))
            imgs = [np.array(Image.fromarray(im).resize(tgtsize, resample=Image.NEAREST)) for im in imgs]
    if contrast=='Log':
        logims = [log_transform(im, interval=limits[idx]) for idx, im in enumerate(imgs)]
        imData = MergeChannels(logims, chMap, masks=masks)
    elif contrast=='Linear':
        newims = [auto_contrast(im, interval=limits[idx]) for idx, im in enumerate(imgs)]
        imData = MergeChannels(newims, chMap, masks=masks)
    else:
        # Ensure we're in float 0-1 range, scale based on bit depth.
        for i in range(len(imgs)):
            maxval = imgs[i].max()
            if maxval > 255:
                imgs[i] = imgs[i] * (1 / 65535)
            elif maxval > 1:
                imgs[i] = imgs[i] * (1 / 255)
        imData = MergeChannels(imgs, chMap, masks=masks)
        
    h,w = imgs[0].shape

    # Convert from float [0-1] to 8bit
    imData *= 255.0

    imData[imData>255] = 255

    # Write wx.Image
    img = wx.Image(w,h)
    img.SetData(imData.astype('uint8').flatten())

    tmp_h = int(p.image_size)
    tmp_w = int(p.image_size)

    # Here we do a more careful rescale to the target tile size.
    if not display_whole_image and h != tmp_h and h!= tmp_w:
        h = tmp_h
        w = tmp_w
        img.Rescale(h,w)

    # Apply brightness & scale
    if brightness != 1.0:
        img = img.AdjustChannels(brightness, brightness, brightness)
    if scale != 1.0:
        if w*scale>10 and h*scale>10:
            img.Rescale(w*scale, h*scale)
        else:
            img.Rescale(10,10)

    cachedresult = img.ConvertToBitmap()
    return cachedresult

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
        if np.any([imgs[i].shape != imgs[0].shape for i in range(len(imgs))]):
            dims = [im.shape for im in imgs]
            aspect_ratios = [float(dims[i][0])/dims[i][1] for i in range(len(dims))]
            def almost_equal(expected, actual, rel_err=1e-7, abs_err=1e-20):
                absolute_error = abs(actual - expected)
                return absolute_error <= max(abs_err, rel_err * abs(expected))
            for i in range(len(aspect_ratios)):
                if not almost_equal(aspect_ratios[0], aspect_ratios[i], abs_err=0.01):
                    raise Exception('Can\'t merge image channels. Aspect ratios do not match.')
            areas = list(map(np.product, dims))
            max_idx = areas.index(max(areas))
            min_idx = areas.index(min(areas))
            
            s = [imgs[max_idx].shape, imgs[min_idx].shape]
            
            if p.use_larger_image_scale:
                p.image_rescale = list(map(float, imgs[max_idx].shape))
                if p.rescale_object_coords:
                    p.image_rescale_from = list(map(float, imgs[min_idx].shape))
            else:
                p.image_rescale = list(map(float, imgs[min_idx].shape))
                if p.rescale_object_coords:
                    p.image_rescale_from = list(map(float, imgs[max_idx].shape))
            
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

def rescale(im, target):
    import scipy.ndimage
    return scipy.ndimage.zoom(im, (target[0] / im.shape[0], target[1] / im.shape[1])) / 255.

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
    (min, max) = interval or (im.min(), im.max())
    # Check that the image isn't binary
    if np.any((im>min)&(im<max)):
        im -= min
        im[im < 0] = 0
        if max > 0:
            im = im / max
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
    if format.lower() in ['jpg', 'jpeg']:
        bitmap.SaveFile(filename, type=wx.BITMAP_TYPE_JPEG)
    elif format == "PNG":
        bitmap.SaveFile(filename, type=wx.BITMAP_TYPE_PNG)
    else:
        raise ValueError(f"Unable to save. Invalid image format '{format}' for {filename}")

def ImageToPIL(image):
    '''Convert wx.Image to PIL Image.'''
    pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
    pil.frombytes(image.GetData())
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
    im = Image.frombytes(mode='RGB', size=(buf.shape[1],buf.shape[0]),
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
        x = np.frombytes(x_str,np.uint8)
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
