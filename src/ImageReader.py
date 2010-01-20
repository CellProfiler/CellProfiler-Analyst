import wx
import Image
import logging
import numpy as np
import urllib2
import os.path
import tifffile
from array import array
from cStringIO import StringIO
from Properties import Properties

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
            
        
    def ReadImages(self, filenames):
        '''
        Do not call read images with a large number of filenames, or it
        will likely crash.  We allow multiple files so image channels
        can be loaded more quickly together.
        '''
        format = filenames[0].split('.')[-1]
        
        if format.upper() in ['TIF', 'TIFF', 'BMP', 'JPG', 'PNG', 'GIF']:
            return self.ReadBitmaps(filenames)
        elif format.upper() in ['DIB']:
            return self.ReadDIBs(filenames)
        else:
            return []
    
    
    def ReadDIBs(self, filenames):
        ''' Reads Cellomics DIB files and returns a list of np arrays '''
        images = []
        bufs = self.GetRawData(filenames)

        for buf in bufs:
            assert np.fromstring(buf[0:4], dtype='<u4')[0] == 40, 'Unexpected DIB header size.'
            assert np.fromstring(buf[14:16], dtype='<u2')[0] == 16, 'DIB Bit depth is not 16!'
            size = np.fromstring(buf[4:12], dtype='<u4')

            imdata = np.fromstring(buf[52:], dtype='<u2')   # read data skipping header
            imdata.shape = size[1], size[0]
            imdata = imdata.astype('float32')
            
            sixteenBit = (imdata > 4095).any()
            if sixteenBit:
                imdata /= 65535.0
            else: # twelve bit
                imdata /= 4095.0
            
            images.append( imdata )
        return images


    def ReadBitmaps(self, filenames):
        images = []
        for data, f in zip(self.GetRawData(filenames), filenames):
#            try:
            imdata = ReadBitmapViaPIL(data)
#            except:
#                imdata = ReadBitmapViaTIFFfile(data)
            if type(imdata) == list:
                # multiple channels returned
                images += imdata
            else:
                # single channel returned
                images.append(imdata)
        return images
    

    def GetRawData(self, urls):
        '''
        Simultaneously opens each url as a file-like object and
        reads their raw data in a list.
        NOTE: This function should not be used for reading large
              numbers of images.
        '''
        data = []
        streams = []
        for url in urls:
            if self.protocol.upper() == 'HTTP':
                fullurl = p.image_url_prepend+urllib2.quote(url)
                logr.info('Opening image: %s'%fullurl)
                try:
                    streams.append(urllib2.urlopen(fullurl))
                except:
                    raise Exception('Image not found: "'+fullurl+'"')
            else:  # Default: local file protocol
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
                    streams.append(open(fullurl, "rb"))
                except:
                    raise Exception('Image not found: "'+fullurl+'"')
                
        for stream in streams:
            if self.protocol.upper() == 'HTTP':
                data.append(stream.read(int(stream.info()['content-length'])))
            else:
                data.append(stream.read())
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
        imdata = np.fromstring(im.tostring(),np.uint8)
        imdata.shape=(int(imdata.shape[0]/2),2)
        imdata = imdata.astype(np.uint16)
        hi,lo = (0,1) if im.tag.prefix == 'MM' else (1,0)
        imdata = imdata[:,hi]*256 + imdata[:,lo]
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
    else:
        import ImageTools
        imd = ImageTools.pil_to_np(im)
        imd = imd / 255.0
        
        if len(imd.shape)==3 and imd.shape[2]>=3:
        	# 3-channels in image
            if (np.any(imd[:,:,0]!=imd[:,:,1]) and 
                np.any(imd[:,:,0]!=imd[:,:,2])):
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
            imdata = np.asarray(im.convert('L')) / 255.0
            
    return imdata

def ReadBitmapViaTIFFfile(data):
    im = tifffile.TIFFfile(StringIO(data))
    imdata = im.asarray(squeeze=True)
    if imdata.dtype == np.uint16:
        # for now, assume this is a Buzz Baum file (i.e., 12 bits in a 16 bit format with the high bit high)
        imdata = (imdata.astype(np.float) - 2**15) / 2**12
    return imdata
    
    

####################### FOR TESTING ######################### 
if __name__ == "__main__":
    from DataModel import DataModel
    from DBConnect import DBConnect
    from ImageViewer import ImageViewer 
    
    logging.basicConfig(level=logging.DEBUG,)
    
    p = Properties.getInstance()
    dm = DataModel.getInstance()
    db = DBConnect.getInstance()
    
#    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('../properties/2009_02_19_MijungKwon_Centrosomes.properties')
#    p.LoadFile('/Users/afraser/Desktop/RuvkunLab_afraser.properties')
    p.LoadFile('/Users/afraser/Downloads/RuvkunLab_afraser.properties')

    app = wx.PySimpleApp()

    ir = ImageReader()
    obkey = dm.GetRandomObject()
#    obkey = (0,1,1)
    filenames = db.GetFullChannelPathsForImage(obkey[:-1])
    images = ir.ReadImages(filenames)
    
#    images = ir.ReadImages(['bcb/image09/HCS/StewartAlison/StewartA1137HSC2454a/2008-06-24/9168/StewartA1137HSC2454a_D10_s3_w1412D5337-1BB6-4965-9E54-C635BCD4B71F.tif',
#                            'bcb/image09/HCS/StewartAlison/StewartA1137HSC2454a/2008-06-24/9168/StewartA1137HSC2454a_D10_s3_w20A6F4EF9-1200-4EA9-990F-49486F4AF7E4.tif',
#                            'imaging/analysis/2008_07_22_HSC_Alison_Stewart/2008_11_05_1137HSC2454a_output/outlines/StewartA1137HSC2454a_D10_s3_w20A6F4EF9-1200-4EA9-990F-49486F4AF7E4.tif_CellsOutlines.png'])
#    images = ir.ReadImages(['/Users/afraser/Desktop/ims/2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A02f00d0.DIB',
#                            '/Users/afraser/Desktop/ims/2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A02f00d1.DIB',
#                            '/Users/afraser/Desktop/ims/2006_02_15_NIRHT/trcHT29Images/NIRHTa+001/AS_09125_050116000001_A02f00d2.DIB'])
    
#    images = ir.ReadImages(['/Users/afraser/Desktop/B02.bmp','/Users/afraser/Desktop/B02o.png'])
    frame = ImageViewer(imgs=images, chMap=p.image_channel_colors, img_key=obkey[:-1])
    frame.Show()
    
    
    app.MainLoop()


