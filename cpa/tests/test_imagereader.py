import os
import unittest
import cpa.imagereader

class ReadBitmapViaPILTestCase(unittest.TestCase):
    def test_unsupported_format(self):
        data = open(os.path.join(os.path.dirname(__file__), '32-bit-grayscale.tif')).read()
        self.assertRaises(Exception, cpa.imagereader.ReadBitmapViaPIL, (data,))
