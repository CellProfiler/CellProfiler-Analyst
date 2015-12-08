import wx
import cpa
import cpa.icons

def _on_manual(self):
    import webbrowser
    webbrowser.open("http://cellprofiler.org/linked_files/Documentation/cpa2_manual.pdf")

def _on_about(self):
    ''' Shows a message box with the version number etc.'''
    message = ('CellProfiler Analyst was developed at The Broad Institute\n'
               'Imaging Platform and is distributed under the GNU General\n'
               'Public License version 2.')
    info = wx.AboutDialogInfo()
    info.SetIcon(cpa.icons.get_cpa_icon())
    info.SetName('CellProfiler Analyst 2.0 (%s)'%('r'+str(cpa.__version__) or 'unknown revision'))
    info.SetDescription(message)
    info.AddDeveloper('David Dao')
    info.AddDeveloper('Adam Fraser')
    info.AddDeveloper('Thouis (Ray) Jones')
    info.AddDeveloper('Vebjorn Ljosa')
    info.SetWebSite('www.CellProfiler.org')
    wx.AboutBox(info)

def make_help_menu(frame):
    helpMenu = wx.Menu()
    frame.Bind(wx.EVT_MENU, _on_manual, 
               helpMenu.Append(-1, text='Online manual'))
    frame.Bind(wx.EVT_MENU, _on_about, 
               helpMenu.Append(-1, text='About', help='About CellProfiler Analyst'))
    return helpMenu

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = wx.Frame(None, title='Test help menu')
    menu_bar = wx.MenuBar()
    menu_bar.Append(make_help_menu(frame), 'Help')
    frame.SetMenuBar(menu_bar)
    app.MainLoop()

