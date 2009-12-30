import wx
import os.path
import glob
import sys

# py2exe puts this module into its library.zip, and I'm not sure how
# to stop it from doing so.  However, I can force it to include the
# icons in a directory at the top level.
if 'library.zip' in __path__[0]:
    search_path = 'icons'
else:
    search_path = __path__[0]

for f in glob.glob(os.path.join(search_path, "*.png")):
    globals()[os.path.basename(f)[:-4]] = wx.Image(f)

def get_cpa_icon(size=None):
    '''The CellProfiler Analyst icon as a wx.Icon'''
    icon = wx.EmptyIcon()
    if size == None and sys.platform.startswith('win'):
        icon.CopyFromBitmap(wx.BitmapFromImage(cpa_32))
    else:
        icon.CopyFromBitmap(wx.BitmapFromImage(cpa_128))
    return icon
