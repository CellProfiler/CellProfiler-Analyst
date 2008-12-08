'''
ImageReader.py
Authors: afraser
'''

import wx
from PIL import Image
import numpy
import urllib
from array import array
from cStringIO import StringIO
from Properties import Properties

p = Properties.getInstance()

class ImageReader(object):
    '''
    ImageReader manages image file formats and transfer protocols (local and http).
    Use this class to read separate image channels in batches and return them to the caller.
    This class could also be used to load batches of images at a time.
    '''
    
    def __init__(self):
        if p.__dict__ != {}:
            if p.image_url_prepend.startswith('http://'):
                self.protocol = 'http'
            elif p.image_url_prepend.startswith('smb:'):
                self.protocol = 'smb'
            else:
                self.protocol = 'local'
                
            assert self.protocol in ['local', 'http'], 'Unsupported image transfer protocol.  Currently only local and http are supported.'
            
        
    def ReadImages(self, filenames):
        '''
        Do not call read images with a large number of filenames or it will likely crash.
        We allow multiple files so image channels can be loaded more quickly together.
        '''
        format = filenames[0].split('.')[-1]
        
        if format.upper() in ['TIF', 'TIFF', 'BMP', 'JPG', 'PNG', 'GIF']:
            return self.ReadBitmaps(filenames)
        elif format.upper() in ['DIB']:
            return self.ReadDIBs(filenames)
        else:
            return []
    
    
    def ReadDIBs(self, filenames):
        ''' Reads Cellomics DIB files and returns a list of numpy arrays '''
        images = []
        bufs = self.GetRawData(filenames)
        for buf in bufs:
            assert numpy.fromstring(buf[0:4], dtype='<u4')[0] == 40, 'Unexpected DIB header size.'
            assert numpy.fromstring(buf[14:16], dtype='<u2')[0] == 16, 'DIB Bit depth is not 16!'
            size = numpy.fromstring(buf[4:12], dtype='<u4')

            imdata = numpy.fromstring(buf[52:], dtype='<u2')   # read data skipping header
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
        for data in self.GetRawData(filenames):
            im = Image.open(StringIO(data))
            
            # Handle 16 and 12 bit images
            if im.mode == 'I;16':
                imdata = numpy.fromstring(im.tostring(), numpy.uint16)
                imdata.shape = im.size[1], im.size[0]
                imdata = imdata.astype(numpy.float32)
                
                sixteenBit = (imdata > 4095).any()
                if sixteenBit:
                    imdata /= 65535.0
                else: # twelve bit
                    imdata /= 4095.0
            else:
                imdata = numpy.asarray(im.convert('L'))
                imdata = imdata / 255.0
                
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
            try:
                if self.protocol.upper() == 'HTTP':
                    print 'Opening image: '+p.image_url_prepend+url
                    streams.append(urllib.urlopen(p.image_url_prepend+url))
                else:  # Default: local file protocol
                    print 'Opening image:',url
                    streams.append(open(url))
            except Exception, e:
                print "Failed to load image data:",e
                
        for stream in streams:
            data.append(stream.read())
            # Ray claims the call below is safer since read() is not guaranteed to
            # return the whole file. However, it does not work for local files. 
            #data.append(stream.read(int(stream.info()['content-length'])))
            stream.close()
            
        return data


####################### FOR TESTING ######################### 
if __name__ == "__main__":
    p = Properties.getInstance()
    p.LoadFile('../properties/2008_07_22_HSC_Alison_Stewart_fixed.properties')
    from ImageViewer import ImageViewer
    app = wx.PySimpleApp()
    
    ir = ImageReader()
    images = ir.ReadImages(['bcb/image09/HCS/StewartAlison/StewartA1137HSC2454a/2008-06-24/9168/StewartA1137HSC2454a_D10_s3_w1412D5337-1BB6-4965-9E54-C635BCD4B71F.tif',
                            'bcb/image09/HCS/StewartAlison/StewartA1137HSC2454a/2008-06-24/9168/StewartA1137HSC2454a_D10_s3_w20A6F4EF9-1200-4EA9-990F-49486F4AF7E4.tif',
                            'imaging/analysis/2008_07_22_HSC_Alison_Stewart/2008_11_05_1137HSC2454a_output/outlines/StewartA1137HSC2454a_D10_s3_w20A6F4EF9-1200-4EA9-990F-49486F4AF7E4.tif_CellsOutlines.png'])
    frame = ImageViewer(imgs=images)
    frame.Show()
    
    
    app.MainLoop()


