import unittest
from ImageReader import ImageReader
from Properties import Properties

p = Properties.getInstance()

# fake-up some props
p._filename = '../../CPAnalyst_test_data/test_images/'
p.image_channel_colors = ['red','green','blue','none','none','none']
p.object_name = ['cell', 'cells']
p.image_names = ['', '', '']
p.image_id = 'ImageNumber'

ir = ImageReader()

class TestImageReader(unittest.TestCase):

   def test_read_images(self):
      # TIF RGB, 8-bit, PackBits encoding
      fds = ['color.tif']
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (512, 512)

      # 2 RGB TIFS
      fds = ['color.tif','color.tif']
      images = ir.ReadImages(fds)
      assert len(images) == 6
      for im in images:
         assert im.shape == (512, 512)

      # JPG
      fds = ['30-2A1b.jpg']
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (1200, 1600)

      # Buzz buam TIF 8-bit uncompressed
      fds = ['01_POS002_D.TIF',
             '01_POS002_F.TIF',
             '01_POS002_R.TIF']
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (1006, 1000)

      # Cellomics dibs
      fds = ['AS_09125_050116030001_D03f00d0.DIB',
             'AS_09125_050116030001_D03f00d1.DIB',
             'AS_09125_050116030001_D03f00d2.DIB',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (512, 512)

      # TIF 8-bit PackBits encoding
      fds = ['AS_09125_050116030001_D03f00d0.tif',
             'AS_09125_050116030001_D03f00d1.tif',
             'AS_09125_050116030001_D03f00d2.tif',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (512, 512)

      # PNG
      fds = ['AS_09125_050116000001_A01f00d0.png',
             'AS_09125_050116000001_A01f00d1.png',
             'AS_09125_050116000001_A01f00d2.png',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (512, 512)

      # READ different image types into same channel set
      fds = ['AS_09125_050116030001_D03f00d0.DIB',
             'AS_09125_050116030001_D03f00d1.tif',
             'AS_09125_050116000001_A01f00d2.png',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert im.shape == (512, 512)

if __name__ == "__main__":
   unittest.main()