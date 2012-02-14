import wx
import numpy as np
import urllib2
import urllib
import os.path
import logging
from properties import Properties

p = Properties.getInstance()

class ImageReader(object):
    def __init__(self):
        self.load_using_bioformats = None
        try:
            from bioformats import load_using_bioformats
            logging.debug('ImageReader will use load_using_bioformats from CellProfiler.')
            self.load_using_bioformats = load_using_bioformats
        except ImportError:
            import traceback
            logging.error(traceback.format_exc())
            logging.error('ImageReader failed to import load_using_bioformats from '
                          'CellProfiler, will fall back on PIL and TiffFile.')

    def ReadImages(self, fds):
        '''fds -- list of file descriptors (filenames or urls)
        returns a list of channels as numpy float32 arrays
        '''
        if self.load_using_bioformats is not None:
            return self.read_images_via_cp(fds)
        else:
            return self.read_images_old_way(fds)
        
    def read_images_via_cp(self, fds):
        '''Uses CellProfiler's LoadImagesImageProvider to load images.
        fds -- list of file descriptors (filenames or urls)
        returns a list of channels as numpy float32 arrays
        '''
        assert self.load_using_bioformats is not None
        channels = []
        for i, fd in enumerate(fds):
            if p.image_url_prepend and p.image_url_prepend.lower().startswith('http://'):
                url, ignored_headers = urllib.urlretrieve('http://' + urllib2.quote(p.image_url_prepend[7:]) + urllib2.quote(fd))
            else:
                url = fd
            logging.info('Loading image from "%s"'%(url))
            image = self.load_using_bioformats(url)

            # Got 1 channel, expected more
            if image.ndim == 2 and p.channels_per_image[i] != '1':
                raise Exception('CPA found %d channels in the "%s" image at '
                                '%s, but it was expecting %s as specified '
                                'by properties field channels_per_image. '
                                'Please update the channels_per_image field '
                                'in your properties file, or make sure your '
                                'images are in the right format.'
                                %(1, 
                                  p.image_names[i],
                                  fd,
                                  p.channels_per_image[i]))
            
            # Got fewer channels than expected
            elif image.ndim > 2 and image.shape[2] < int(p.channels_per_image[i]):
                raise Exception('CPA found %d channels in the "%s" image at '
                                '%s, but it was expecting %s as specified '
                                'by properties field channels_per_image. '
                                'Please update the channels_per_image field '
                                'in your properties file, or make sure your '
                                'images are in the right format.'
                                %(image.shape[2], 
                                  p.image_names[i],
                                  fd,
                                  p.channels_per_image[i]))
            
            # Got more channels than expected (load the first ones & warn)
            elif image.ndim > 2 and image.shape[2] > int(p.channels_per_image[i]):
                logging.warn('WARNING: CPA found %d channels in the "%s" image '
                             'at %s, but it will only load the first %s as '
                             'specified by properties field channels_per_image.'
                             %(image.shape[2], 
                               p.image_names[i],
                               fd,
                               p.channels_per_image[i]))
                channels += [image[:,:,i] for i in range(int(p.channels_per_image[i]))]

            # Got as many channels as expected
            else:
                if image.ndim == 2:
                    channels += [image]
                else:
                    channels += [image[:,:,i] for i in range(image.shape[2])]
                
        # Check if any images need to be rescaled, and if they are the same
        # aspect ratio. If so, do the scaling.
        from imagetools import check_image_shape_compatibility
        check_image_shape_compatibility(channels)
        if p.image_rescale:
            from imagetools import rescale
            for i in range(len(channels)):
                if channels[i].shape != p.image_rescale:
                    channels[i] = rescale(channels[i], (p.image_rescale[1], p.image_rescale[0]))

        return channels
    
    def read_images_old_way(self, fds):
        '''fds -- list of file descriptors (filenames or urls)
        returns a list of channels as numpy float32 arrays
        '''
        channels = []
        for i, fd in enumerate(fds):
            format = fd.split('.')[-1]
            if format.upper() in ['TIF', 'TIFF', 'BMP', 'JPG', 'JPEG', 'PNG', 'GIF', 'C01']:
                planes = self.ReadBitmap(fd)
            elif format.upper() in ['DIB']:
                planes = [self.ReadDIB(fd)]
            else:
                logging.error('Image format (%s) not supported. Skipping image "%s".'%(format, fds))
            
            # Got fewer channels than expected
            if len(planes) < int(p.channels_per_image[i]):
                raise Exception('CPA found %d channels in the "%s" image at '
                                '%s, but it was expecting %s as specified '
                                'by properties field channels_per_image. '
                                'Please update the channels_per_image field '
                                'in your properties file, or make sure your '
                                'images are in the right format.'
                                %(len(planes), 
                                  p.image_names[i],
                                  fd,
                                  p.channels_per_image[i]))
            
            # Got more channels than expected (load the first ones & warn)
            elif len(planes) > int(p.channels_per_image[i]):
                logging.warn('WARNING: CPA found %d channels in the "%s" image '
                             'at %s, but it will only load the first %s as '
                             'specified by properties field channels_per_image.'
                             %(len(planes), 
                               p.image_names[i],
                               fd,
                               p.channels_per_image[i]))
                channels += planes[:int(p.channels_per_image[i])]
                
            # Got as many channels as expected
            else:
                channels += planes

        # Check if any images need to be rescaled, and if they are the same
        # aspect ratio. If so, do the scaling.

        from imagetools import check_image_shape_compatibility
        check_image_shape_compatibility(channels)
        if p.image_rescale:
            from imagetools import rescale
            for i in range(len(channels)):
                if channels[i].shape != map(int, p.image_rescale):
                    channels[i] = rescale(channels[i], (int(p.image_rescale[1]), int(p.image_rescale[0])))

        return channels

    def ReadDIB(self, fd):
        ''' Reads a Cellomics DIB and returns the data as a float32 array
        NOTE: this function does not support multiple channels
        '''
        buf = self.GetRawData(fd)
        assert np.fromstring(buf[0:4], dtype='<u4')[0] == 40, 'Unexpected DIB header size.'
        assert np.fromstring(buf[14:16], dtype='<u2')[0] == 16, 'DIB Bit depth is not 16!'
        size = np.fromstring(buf[4:12], dtype='<u4')

        # read data skipping header
        imdata = np.fromstring(buf[52:], dtype='<u2')
        imdata.shape = size[1], size[0]
        imdata = imdata.astype('float32')

        sixteenBit = (imdata > 4095).any()
        if sixteenBit:
            imdata /= 65535.0
        else: # twelve bit
            imdata /= 4095.0

        return imdata

    def ReadBitmap(self, fd):
        '''Reads a bitmap using PIL with a fallback to tifffile.
        Returns a list of images as numpy float32 arrays.
        '''
        data = self.GetRawData(fd)
        try:
            imdata = ReadBitmapViaPIL(data)
        except:
            imdata = ReadBitmapViaTIFFfile(data)

        channels = []
        if type(imdata) == list:
            # multiple channels returned
            channels = imdata
        else:
            # single channel returned
            channels = [imdata]
        return channels

    def GetRawData(self, url):
        '''Opens url as a file-like object and returns the raw data.'''
        if p.image_url_prepend and p.image_url_prepend.lower().startswith('http://'):
            # load file via http
            fullurl = 'http://' + urllib2.quote(p.image_url_prepend[7:]) + urllib2.quote(url)
            logging.info('Opening image: %s'%fullurl)
            try:
                stream = urllib2.urlopen(fullurl)
            except:
                raise Exception('Image not found: "'+fullurl+'"')
            data = ''
            while True:
                chunk = stream.read()
                if len(chunk)==0:
                    break
                data += chunk
        else:
            # load local file
            if p.image_url_prepend:
                fullurl = os.path.join(p.image_url_prepend, url)
            else:
                # if no prepend is provided, compute the path relative to the properties file.
                if os.path.isabs(url):
                    fullurl = url
                else:
                    fullurl = os.path.join(os.path.dirname(p._filename), url)
            logging.info('Opening image: %s'%fullurl)
            try:
                stream = open(fullurl, "rb")
            except:
                raise Exception('Could not open image: "'+fullurl+'"')
            data = stream.read()
            
        stream.close()
        return data

    
def ReadBitmapViaPIL(data):
    import PIL.Image as Image
    from cStringIO import StringIO
    im = Image.open(StringIO(data))

    # Handle 16 and 12 bit images
    if im.mode == 'I':
        raise "Can't handle 32 bit grayscale yet"

    if im.mode == 'I;16':
        # deal with the endianness explicitly... I'm not sure
        # why PIL doesn't get this right.
        imdata = np.fromstring(im.tostring(), np.uint8)
        imdata.shape = (int(imdata.shape[0] / 2), 2)
        imdata = imdata.astype(np.uint16)
        hi,lo = (0,1) if im.tag.prefix == 'MM' else (1,0)
        imdata = imdata[:,hi] * 256 + imdata[:,lo]
        imsize = list(im.size)
        imsize.reverse()
        new_img = imdata.reshape(imsize)
        # The magic # for maximum sample value is 281
        if im.tag.has_key(281):
            imdata = new_img.astype(float) / im.tag[281][0]
        elif np.max(new_img) < 4096:
            imdata = new_img.astype(float) / 4095.
        else:
            imdata = new_img.astype(float) / 65535.

    elif im.mode == 'L':
        imd = np.fromstring(im.tostring(), np.uint8) / 255.0
        imsize = list(im.size)
        imsize.reverse()
        imdata = imd.reshape(imsize)

    elif im.mode == '1':
        imd = np.fromstring(im.convert('L').tostring(), np.uint8) / 255.0
        imsize = list(im.size)
        imsize.reverse()
        imdata = imd.reshape(imsize)

    elif im.mode in ['RGB', 'RGBA']:
        import imagetools
        imd = np.asarray(im) / 255.0

        if len(imd.shape)==3 and imd.shape[2]>=3:
            # 3-channels in image
            if (np.any(imd[:,:,0] != imd[:,:,1]) and 
                np.any(imd[:,:,0] != imd[:,:,2])):
                if imd.shape[2] == 4:
                    # strip alpha channel if all values are the same
                    assert np.all(imd[:,:,3]==imd[0,0,3]), 'CPA does not yet support alpha channels in images.'
                    logging.warn('Discarding alpha channel in color image.')
                    imd = imd[:,:,:3]
                # Return all (3) channels if not identical
                imdata = [imd[:,:,i] for i in range(imd.shape[2])]
            else:
                # Channels are identical, return only 1
                imdata = imd[:,:,0]
        else:
            # Single-channel image, return that channel
            imdata = imd

    else:
        raise Exception('Image mode not supported.')

    return imdata

def ReadBitmapViaTIFFfile(data):
    import tifffile
    from cStringIO import StringIO
    im = tifffile.TIFFfile(StringIO(data))
    imdata = im.asarray(squeeze=True)
    if imdata.dtype == np.uint16:
        if np.max(imdata) < 4096:
            imdata = imdata.astype(np.float32) / 4095.
        else:
            imdata = imdata.astype(np.float32) / 65535.
            
        if imdata.ndim == 3:
            # check if channels are identical:
            #   if so return only the first
            #   if not, separate the channels into a list
            if (np.any(imdata[0] != imdata[1]) or
                np.any(imdata[0] != imdata[2])):
                imdata = [imdata[0], imdata[1], imdata[2]]
            else:
                imdata = imdata[0]
    return imdata


####################### FOR TESTING ######################### 
if __name__ == "__main__":
    import wx
    from datamodel import DataModel
    from dbconnect import DBConnect
    from imageviewer import ImageViewer 
    import sys

    app = wx.PySimpleApp()

    p = Properties.getInstance()
    dm = DataModel.getInstance()
    db = DBConnect.getInstance()
    ir = ImageReader()
    
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            wx.GetApp().Exit()

    obkey = dm.GetRandomObject()
    fds = db.GetFullChannelPathsForImage(obkey[:-1])
    images = ir.ReadImages(fds)
    ImageViewer(images, img_key=obkey[:-1]).Show()

    app.MainLoop()


