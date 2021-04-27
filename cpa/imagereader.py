import urllib.request, urllib.error, urllib.parse
import urllib.parse
import imageio
import os.path
import logging
import bioformats
import javabridge
from .properties import Properties
from .errors import ClearException

p = Properties()
IMAGEIO_FORMATS = (".tif", ".tiff", ".bmp", ".gif", ".png", ".jpeg")

class ThrowingURLopener(urllib.request.URLopener):
    def http_error_default(*args, **kwargs):
        return urllib.request.URLopener.http_error_default(*args, **kwargs)

class ImageReader(object):

    def ReadImages(self, fds, log_io=True):
        '''fds -- list of file descriptors (filenames or urls)
        returns a list of channels as numpy float32 arrays
        '''
        channels = []
        for i, filename_or_url in enumerate(fds):
            image = self._read_image(filename_or_url, log_io=log_io)
            if image is None:
                return
            channels += self._extract_channels(filename_or_url, image,
                                               p.image_names[i],
                                               int(p.channels_per_image[i]))

        # Check if any images need to be rescaled, and if they are the same
        # aspect ratio. If so, do the scaling.
        from .imagetools import check_image_shape_compatibility
        check_image_shape_compatibility(channels)
        if p.image_rescale:
            from .imagetools import rescale
            for i in range(len(channels)):
                if channels[i].shape != p.image_rescale:
                    channels[i] = rescale(channels[i], (p.image_rescale[1], p.image_rescale[0]))

        return channels

    def _read_image(self, filename_or_url, log_io=True):
        if p.image_url_prepend:
            parsed = urllib.parse.urlparse(p.image_url_prepend + filename_or_url)
            if parsed.scheme:
                try:
                    filename_or_url, ignored_headers = urllib.request.urlretrieve(parsed.geturl())
                except IOError as e:
                    if e.args[0] == 'http error':
                        status_code, message = e.args[1:3]
                        raise ClearException(
                            'Failed to load image from %s' % parsed.geturl(),
                            '%d %s' % (status_code, message))
                    else:
                        raise
        if not p.force_bioformats and os.path.splitext(filename_or_url)[-1].lower() in IMAGEIO_FORMATS:
            if log_io:
                logging.info('ImageIO: Loading image from "%s"' % filename_or_url)
            try:
                return imageio.imread(filename_or_url)
            except FileNotFoundError:
                logging.error(f"File not found: {filename_or_url}")
                return
            except:
                logging.info('Loading with ImageIO failed, falling back to BioFormats')
        if javabridge.get_env() is None:
            logging.debug("Starting javabridge")
            javabridge.start_vm(class_path=bioformats.JARS, run_headless=True)
            javabridge.attach()
        if log_io:
            logging.info('BioFormats: Loading image from "%s"' % filename_or_url)
        try:
            return bioformats.load_image(filename_or_url, rescale=False)
        except FileNotFoundError:
            logging.error(f"File not found: {filename_or_url}")
        except:
            logging.error('Loading with BioFormats failed, file may be corrupted or unavailable')

    def _extract_channels(self, filename_or_url, image, image_name, channels_per_image):
        if image.ndim == 2 and channels_per_image != 1:
            # Got 1 channel, expected more
            raise Exception('CPA found %d channels in the "%s" image at '
                            '%s, but it was expecting %s as specified '
                            'by properties field channels_per_image. '
                            'Please update the channels_per_image field '
                            'in your properties file, or make sure your '
                            'images are in the right format.'
                            %(1,
                              image_name,
                              filename_or_url,
                              channels_per_image))
        if image.ndim > 2 and image.shape[2] < channels_per_image:
            # Got fewer channels than expected
            raise Exception('CPA found %d channels in the "%s" image at '
                            '%s, but it was expecting %s as specified '
                            'by properties field channels_per_image. '
                            'Please update the channels_per_image field '
                            'in your properties file, or make sure your '
                            'images are in the right format.'
                            %(image.shape[2],
                              image_name,
                              filename_or_url,
                              channels_per_image))
        if image.ndim > 2 and image.shape[2] > channels_per_image:
            # Got more channels than expected (load the first ones & warn)
            logging.warn('WARNING: CPA found %d channels in the "%s" image '
                         'at %s, but it will only load the first %s as '
                         'specified by properties field channels_per_image.'
                         %(image.shape[2],
                           image_name,
                           filename_or_url,
                           channels_per_image))
            return [image[:, :, j]
                    for j in range(int(channels_per_image))]
        else:
            # Got as many channels as expected
            if image.ndim == 2:
                return [image]
            else:
                return [image[:, :, j]
                        for j in range(image.shape[2])]


####################### FOR TESTING #########################
if __name__ == "__main__":
    import wx
    from .datamodel import DataModel
    from .dbconnect import DBConnect
    from .imageviewer import ImageViewer
    import sys

    app = wx.App()

    p = Properties()
    dm = DataModel()
    db = DBConnect()
    ir = ImageReader()

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            wx.GetApp().Exit()

    obkey = dm.GetRandomObject(1)[0]
    fds = db.GetFullChannelPathsForImage(obkey[:-1])
    images = ir.ReadImages(fds)
    ImageViewer(images, img_key=obkey[:-1]).Show()

    app.MainLoop()
