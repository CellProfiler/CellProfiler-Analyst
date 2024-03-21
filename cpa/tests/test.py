import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.backends.backend_wx import _load_bitmap
import matplotlib as mpl


app = wx.App()
f = wx.Frame(None)
fig = mpl.figure.Figure()
p = FigureCanvasWxAgg(f, -1, fig)

toolbar = NavigationToolbar2WxAgg(p)
toolbar.Hide()

#toolbar constants
TBFLAGS = (wx.TB_HORIZONTAL|wx.TB_TEXT)      
tsize = (24,24)
tb = f.CreateToolBar(TBFLAGS)

_NTB2_HOME = wx.NewId()
_NTB2_BACK = wx.NewId()
_NTB2_FORWARD = wx.NewId()
_NTB2_PAN = wx.NewId()
_NTB2_ZOOM = wx.NewId()
_NTB2_SAVE = wx.NewId()
_NTB2_SUBPLOT = wx.NewId()

tb.AddSimpleTool(_NTB2_HOME, _load_bitmap('home.png'), 'Home', 'Reset original view')
tb.AddSimpleTool(_NTB2_BACK, _load_bitmap('back.png'), 'Back', 'Back navigation view')
tb.AddSimpleTool(_NTB2_FORWARD, _load_bitmap('forward.png'), 'Forward', 'Forward navigation view')

tb.AddCheckTool(_NTB2_PAN, "", _load_bitmap('move.png'), shortHelp='Pan')
tb.AddCheckTool(_NTB2_ZOOM, "", _load_bitmap('zoom_to_rect.png'), shortHelp='Zoom')

tb.AddSeparator()
tb.AddSimpleTool(_NTB2_SUBPLOT, _load_bitmap('subplots.png'), 'Configure subplots', 'Configure subplot parameters')
tb.AddSimpleTool(_NTB2_SAVE, _load_bitmap('filesave.png'), 'Save', 'Save plot contents to file')

f.Bind(wx.EVT_TOOL, toolbar.home, id=_NTB2_HOME)
f.Bind(wx.EVT_TOOL, toolbar.forward, id=_NTB2_FORWARD)
f.Bind(wx.EVT_TOOL, toolbar.back, id=_NTB2_BACK)
f.Bind(wx.EVT_TOOL, toolbar.zoom, id=_NTB2_ZOOM)
f.Bind(wx.EVT_TOOL, toolbar.pan, id=_NTB2_PAN)
f.Bind(wx.EVT_TOOL, toolbar.configure_subplots, id=_NTB2_SUBPLOT)
f.Bind(wx.EVT_TOOL, toolbar.save_figure, id=_NTB2_SAVE)

tb.Realize()
f.Show()
f.Close()
app.MainLoop()