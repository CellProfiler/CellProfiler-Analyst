import wx
import os.path
import sys

# Old code used to scan the icons directory and report everything into global variables on startup.
# As of wx4 this is no longer valid, since the app has to launch first.
# So now we'll call icons when needed and cache them in a dictionary.
# We could convert to wx.Bitmap before storage, but there must be some reason the original
# stored everything as wx.Image, right?

icon_cache = {}

def get_icon(name):
    if name in icon_cache:
        return icon_cache[name]
    else:
        dir = __path__[0]
        icon_cache[name] = wx.Image(os.path.join(dir, name + ".png"))
        return icon_cache[name]

def get_cpa_icon(size=None):
    '''The CellProfiler Analyst icon as a wx.Icon'''
    icon = wx.Icon()
    if size == None and sys.platform.startswith('win'):
        icon.CopyFromBitmap(wx.Bitmap(get_icon("cpa_32")))
    else:
        icon.CopyFromBitmap(wx.Bitmap(get_icon("cpa_128")))
    return icon
