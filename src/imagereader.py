import wx
import Image
import logging
import numpy as np
import urllib2
import os.path
import tifffile
from array import array
from cStringIO import StringIO
from properties import Properties

p = Properties.getInstance()
logr = logging.getLogger('ImageReader')

class ImageReader(object):
    '''
    ImageReader manages image file formats and transfer protocols (local and http).
    Use this class to read separate image channels in batches and return them to the caller.
    This class could also be used to load batches of images at a time.
    '''

    def __init__(self):
        if p.__dict__ != {}:
            if p.image_url_prepend and p.image_url_prepend.startswith('http://'):
                self.protocol = 'http'
            else:
                self.protocol = 'local'

            assert self.protocol in ['local', 'http'], 'Unsupported image transfer protocol.  Currently only local and http are supported.'


    def ReadImages(self, fds):
        '''fds -- list of file descriptors (filenames or urls)
        returns a list of channels as numpy float32 arrays
        '''
        channels = []
        for fd in fds:
            format = fd.split('.')[-1]
            if format.upper() in ['TIF', 'TIFF', 'BMP', 'JPG', 'PNG', 'GIF']:
                channels += self.ReadBitmap(fd)
            elif format.upper() in ['DIB']:
                channels += [self.ReadDIB(fd)]
            else:
                logging.error('Image format (%s) not supported. Skipping image "%s".'%(format, fds))

        from imagetools import check_image_shape_compatibility
        check_image_shape_compatibility(channels)
        if p.image_rescale:
            from imagetools import rescale
            for i in range(len(channels)):
                if channels[i].shape != p.image_rescale:
                    channels[i] = rescale(channels[i], (p.image_rescale[1], p.image_rescale[0]))

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
        #
        # Open the file
        #
        if self.protocol.upper() == 'HTTP':
            fullurl = p.image_url_prepend+urllib2.quote(url)
            logr.info('Opening image: %s'%fullurl)
            try:
                stream = urllib2.urlopen(fullurl)
            except:
                raise Exception('Image not found: "'+fullurl+'"')
        else:
            # Default: local file protocol
            if p.image_url_prepend:
                fullurl = os.path.join(p.image_url_prepend, url)
            else:
                # if no prepend is provided, compute the path relative to the properties file.
                if os.path.isabs(url):
                    fullurl = url
                else:
                    fullurl = os.path.join(os.path.dirname(p._filename), url)
            logr.info('Opening image: %s'%fullurl)
            try:
                stream = open(fullurl, "rb")
            except:
                raise Exception('Could not open image: "'+fullurl+'"')
        #
        # Read from the stream
        #
        if self.protocol.upper() == 'HTTP':
            data = ''
            while True:
                chunk = stream.read()
                if len(chunk)==0:
                    break
                data += chunk
        else:
            data = stream.read()
        stream.close()

        return data


def ReadBitmapViaPIL(data):
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
    from datamodel import DataModel
    from dbconnect import DBConnect
    from imageviewer import ImageViewer 

    logging.basicConfig(level=logging.DEBUG,)
    app = wx.PySimpleApp()

    p = Properties.getInstance()
    p._filename = '../../CPAnalyst_test_data/test_images/'
    p.image_channel_colors = ['red','green','blue','none','none','none']
    p.object_name = ['cell', 'cells']
    p.image_names = ['', '', '']
    p.image_id = 'ImageNumber'

    dm = DataModel.getInstance()
    db = DBConnect.getInstance()
    ir = ImageReader()

#    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('/Users/afraser/cpa_example/example.properties')
#    p.LoadFile('../properties/2009_02_19_MijungKwon_Centrosomes.properties')
#    p.LoadFile('/Users/afraser/Desktop/RuvkunLab_afraser.properties')
#    p.LoadFile('/Users/afraser/Downloads/RuvkunLab_afraser.properties')

##    obkey = dm.GetRandomObject()
##    fds = db.GetFullChannelPathsForImage(obkey[:-1])
##    images = ir.ReadImages(fds)

##    p.channels_per_image = ['3']
##    fds = ['color.tif']
##    images = ir.ReadImages(fds)
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()
##
##    fds = ['30-2A1b.jpg']
##    images = ir.ReadImages(fds)
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()

    p.channels_per_image = ['1','1','1']
    fds = ['01_POS002_D.TIF',
           '01_POS002_F.TIF',
           '01_POS002_R.TIF']
    images = ir.ReadImages(fds)
    for im in images:
        print im.shape
    ImageViewer(images).Show()

##    fds = ['AS_09125_050116030001_D03f00d0.DIB',
##           'AS_09125_050116030001_D03f00d1.DIB',
##           'AS_09125_050116030001_D03f00d2.DIB',]
##    images = ir.ReadImages(fds)
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()
##
##    fds = ['AS_09125_050116030001_D03f00d0.tif',
##           'AS_09125_050116030001_D03f00d1.tif',
##           'AS_09125_050116030001_D03f00d2.tif',]
##    images = ir.ReadImages(fds)
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()
##
##    fds = ['AS_09125_050116000001_A01f00d0.png',
##           'AS_09125_050116000001_A01f00d1.png',
##           'AS_09125_050116000001_A01f00d2.png',]
##    images = ir.ReadImages(fds)
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()
##
##    # READ different image types into same channel set
##    fds = ['AS_09125_050116030001_D03f00d0.DIB',
##           'AS_09125_050116030001_D03f00d1.tif',
##           'AS_09125_050116000001_A01f00d2.png',]
##    images = ir.ReadImages(fds)
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()
##
##    # 
##    fds = ['PANDORA_100324070001_P14f00d0.TIF',
##           'PANDORA_100324070001_P14f00d1.TIF',]
##    images = ir.ReadImages(fds)
##    assert len(images) == 2
##    for im in images:
##        print im.shape
##    ImageViewer(images).Show()

#    images = ir.ReadImages(['bcb/image09/HCS/StewartAlison/StewartA1137HSC2454a/2008-06-24/9168/StewartA1137HSC2454a_D10_s3_w1412D5337-1BB6-4965-9E54-C635BCD4B71F.tif',
#                            'bcb/image09/HCS/StewartAlison/StewartA1137HSC2454a/2008-06-24/9168/StewartA1137HSC2454a_D10_s3_w20A6F4EF9-1200-4EA9-990F-49486F4AF7E4.tif',
#                            'imaging/analysis/2008_07_22_HSC_Alison_Stewart/2008_11_05_1137HSC2454a_output/outlines/StewartA1137HSC2454a_D10_s3_w20A6F4EF9-1200-4EA9-990F-49486F4AF7E4.tif_CellsOutlines.png'])
#    images = ir.ReadImages(['/Users/afraser/Desktop/ims/2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A02f00d0.DIB',
#                            '/Users/afraser/Desktop/ims/2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A02f00d1.DIB',
#                            '/Users/afraser/Desktop/ims/2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A02f00d2.DIB'])

#    images = ir.ReadImages(['/Users/afraser/Desktop/B02.bmp','/Users/afraser/Desktop/B02o.png'])
##    frame = ImageViewer(imgs=images, chMap=p.image_channel_colors, img_key=obkey[:-1])
##    frame.Show()
##    
##    
    app.MainLoop()


