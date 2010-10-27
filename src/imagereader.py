import numpy as np
import urllib2
from properties import Properties
from cellprofiler.modules.loadimages import LoadImagesImageProvider

p = Properties.getInstance()

class ImageReader(object):

    def ReadImages(self, fds):
        '''fds -- list of file descriptors (filenames or urls)
        returns a list of channels as numpy float32 arrays
        '''
        channels = []
        for i, fd in enumerate(fds):
            if p.image_url_prepend and p.image_url_prepend.lower().startswith('http://'):
                url = 'http://' + urllib2.quote(p.image_url_prepend[7:]) + urllib2.quote(fd)
            else:
                url = fd
            print 'loading image from ', url
            lip = LoadImagesImageProvider("dummy", "", url, True)
            image = lip.provide_image(None).pixel_data
            
            if p.channels_per_image[i] == '1':
                if image.ndim == 2:
                    channels += [image]
                else:
                    channels += [image[:,:,0]]
            elif p.channels_per_image[i] == '3':
                channels += [image[:,:,i] for i in range(3)]
            elif p.channels_per_image[i] >= '4':
                if image.shape[2] != p.channels_per_image[i]:
                    raise ('Your properties file specifies %s channels for '
                           'image #%s but %s channels were found. Make sure '
                           '"channels_per_image" is set correctly in your '
                           'properties file.'%(p.channels_per_image[i], i+1, 
                                               image.shape[2]))
                channels += [image[:,:,i] for i in range(image.shape[2])]
            else:
                raise ('Invalid number of channels (%s) specified for image #%s.'
                       ' Make sure "channels_per_image" is set correctly in your'
                       'properties file.'%(p.channels_per_image[0] ,i+1))
        
        from imagetools import check_image_shape_compatibility
        check_image_shape_compatibility(channels)
        if p.image_rescale:
            from imagetools import rescale
            for i in range(len(channels)):
                if channels[i].shape != p.image_rescale:
                    channels[i] = rescale(channels[i], (p.image_rescale[1], p.image_rescale[0]))

        return channels

    
####################### FOR TESTING ######################### 
if __name__ == "__main__":
    import wx
    from datamodel import DataModel
    from dbconnect import DBConnect
    from imageviewer import ImageViewer 

    app = wx.PySimpleApp()

    p = Properties.getInstance()
    dm = DataModel.getInstance()
    db = DBConnect.getInstance()
    ir = ImageReader()
    
    p.LoadFile('/Users/afraser/Desktop/2010_03_04_OilRedO_RuvkunLab.properties')

    obkey = dm.GetRandomObject()
    fds = db.GetFullChannelPathsForImage(obkey[:-1])
    images = ir.ReadImages(fds)
    ImageViewer(images, img_key=obkey[:-1]).Show()

    app.MainLoop()


