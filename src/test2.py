import wx
import numpy
from ImageFrame import ImageFrame


def Crop(im, (w,h), (x,y) ):
    ''' Crops an image. '''
    d = numpy.fromstring(im.GetData(), 'uint8')
    crop = wx.EmptyImage(w,h)
    for px in xrange(w):
        for py in xrange(h):
            xx = px+x-w/2
            yy = py+y-h/2
            if 0<=xx<im.GetWidth() and 0<=yy<im.GetHeight():
                 crop.SetRGB(px, py,
                             im.GetRed(xx,yy),
                             im.GetGreen(xx,yy),
                             im.GetBlue(xx,yy))
            else:
                crop.SetRGB(px,py, 0,0,0)
    return crop
    
    
    
ims =[0,0,0]
ims[0] = wx.Image('/Users/afraser/Desktop/swinger_r.jpg')
ims[1] = wx.Image('/Users/afraser/Desktop/swinger_g.jpg')
ims[2] = wx.Image('/Users/afraser/Desktop/swinger_b.jpg')

width = ims[0].GetWidth()
height = ims[0].GetHeight()

dn = [numpy.fromstring(im.GetData(), 'uint8')[::3] for im in ims]
for d in dn:
    d.shape=(height,width)

img = wx.EmptyImage(width,height)
img.SetData(numpy.dstack([d for d in dn]).flatten())

app = wx.PySimpleApp()
img.SetRGB(50,50, 255,255,255)
img.SetRGB(350,0, 255,255,255)
img.SetRGB(0,233, 255,255,255)
img.SetRGB(432,603, 255,255,255)
img.SetRGB(432/2,603/2, 255,255,255)

frame = ImageFrame(image=img)
frame.Show(True)

imgCrop = Crop(img, (100,100), (0,0))
frame = ImageFrame(image=imgCrop)
frame.Show(True)

imgCrop = Crop(img, (100,100), (50,50))
frame = ImageFrame(image=imgCrop)
frame.Show(True)

imgCrop = Crop(img, (100,100), (350,0))
frame = ImageFrame(image=imgCrop)
frame.Show(True)

imgCrop = Crop(img, (100,100), (0,233))
frame = ImageFrame(image=imgCrop)
frame.Show(True)

imgCrop = Crop(img, (100,100), (432,603))
frame = ImageFrame(image=imgCrop)
frame.Show(True)

imgCrop = Crop(img, (500,700), (432/2,603/2))
frame = ImageFrame(image=imgCrop)
frame.Show(True)

app.MainLoop()



# TODO: write me!!!

