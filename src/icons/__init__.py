import wx
import os.path
import glob
import sys

for f in glob.glob(os.path.join(__path__[0], "*.png")):
    globals()[os.path.basename(f)[:-4]] = wx.Image(f)

def get_cpa_icon(size=None):
    '''The CellProfiler Analyst icon as a wx.Icon'''
    icon = wx.EmptyIcon()
    if size == None and sys.platform.startswith('win'):
        icon.CopyFromBitmap(wx.BitmapFromImage(cpa_32))
    else:
        icon.CopyFromBitmap(wx.BitmapFromImage(cpa_128))
    return icon