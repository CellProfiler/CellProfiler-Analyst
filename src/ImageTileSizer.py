'''
Special sizer for organizing image tiles.
'''

import wx
import math

class ImageTileSizer(wx.PySizer):
    def __init__(self):
        wx.PySizer.__init__(self)
        
    def pitch(self):
        # get sizes of all tiles
        sizes = [c.GetSize() + wx.Size(2*c.GetBorder(), 2*c.GetBorder())
                 for c in self.GetChildren()]
        if sizes == []:
            return None
        else:
            return max(sizes)

    def CalcMin(self):
        n = len(self.GetChildren())
        if n > 0:
            width = self.GetContainingWindow().GetClientSize().GetWidth()
            self.columns = max(1, width/self.pitch().x)
            self.rows = math.ceil(1.0 * n / self.columns)
            pitch = self.pitch()
            return wx.Size(self.columns * pitch.x, self.rows * pitch.y)
        else:
            return wx.Size(0,0)
        
    def RecalcSizes(self):
        self.CalcMin()
        origin = self.GetPosition()
        pitch = self.pitch()
        for k, item in enumerate(self.GetChildren()):
            i = k / self.columns
            j = k % self.columns
            pos = origin + wx.Point(j * pitch.x, i * pitch.y)
            item = self.GetChildren()[i * self.columns + j]
            border = item.GetBorder()
            item.SetDimension(pos+wx.Point(border, border), item.GetSize())
