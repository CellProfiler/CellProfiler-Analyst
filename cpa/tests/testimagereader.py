import unittest
from cpa.imagereader import ImageReader
from cpa.properties import Properties

p = Properties()

# fake-up some props
p._filename = '../../CPAnalyst_test_data/test_images/'
p.image_channel_colors = ['red','green','blue','none','none','none']
p.object_name = ['cell', 'cells']
p.image_names = ['', '', '']
p.image_id = 'ImageNumber'

ir = ImageReader()

class TestImageReader(unittest.TestCase):

   def test_tif1(self):
      # TIF RGB, 8-bit, PackBits encoding
      fds = ['color.tif']
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)

   def test_tif2(self):
      # 2 RGB TIFS
      fds = ['color.tif','color.tif']
      images = ir.ReadImages(fds)
      assert len(images) == 6
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)

   def test_tif3(self):
      # Buzz buam TIF 8-bit uncompressed
      fds = ['01_POS002_D.TIF',
             '01_POS002_F.TIF',
             '01_POS002_R.TIF']
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (1006, 1000)

   def test_tif4(self):
      # TIF 8-bit PackBits encoding
      fds = ['AS_09125_050116030001_D03f00d0.tif',
             'AS_09125_050116030001_D03f00d1.tif',
             'AS_09125_050116030001_D03f00d2.tif',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)

   def test_tif5(self):
      # TIFs from Neurospheres project
      fds = ['PANDORA_100324070001_P14f00d0.TIF',
             'PANDORA_100324070001_P14f00d1.TIF',]
      images = ir.ReadImages(fds)
      assert len(images) == 2
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)

   def test_jpg1(self):
      # JPG
      fds = ['30-2A1b.jpg']
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (1200, 1600)

   def test_dib(self):
      # Cellomics dibs
      fds = ['AS_09125_050116030001_D03f00d0.DIB',
             'AS_09125_050116030001_D03f00d1.DIB',
             'AS_09125_050116030001_D03f00d2.DIB',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)

   def test_png(self):
      # PNG
      fds = ['AS_09125_050116000001_A01f00d0.png',
             'AS_09125_050116000001_A01f00d1.png',
             'AS_09125_050116000001_A01f00d2.png',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)

   def test_mixed(self):
      # READ different image types into same channel set
      fds = ['AS_09125_050116030001_D03f00d0.DIB',
             'AS_09125_050116030001_D03f00d1.tif',
             'AS_09125_050116000001_A01f00d2.png',]
      images = ir.ReadImages(fds)
      assert len(images) == 3
      for im in images:
         assert 0. <= im.min() <= im.max() <= 1.
         assert im.shape == (512, 512)
         
if __name__ == "__main__":
   unittest.main()