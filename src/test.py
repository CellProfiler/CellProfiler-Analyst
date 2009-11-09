
import wx
import wx.combo

app = wx.PySimpleApp()
frame = wx.Frame(None, -1, "..", size = (400, 300))
p = wx.Panel(frame, -1)
bcb = wx.combo.OwnerDrawnComboBox(p, -1, choices= ['aASDfasdf_asdf_asdfasasdfasd_asdfasdfasdf_asdfasdfasdfasd_asdfasdfasdf','b','asdf'], pos=(25,25), size=(130,-1))
frame.Show(True)
app.MainLoop()
