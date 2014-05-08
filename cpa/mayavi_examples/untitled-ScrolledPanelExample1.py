import wx
from wx.lib.scrolledpanel import ScrolledPanel

class MyFrame( wx.Frame ):
    def __init__( self, parent, ID, title ):
        wx.Frame.__init__( self, parent, ID, title,
                         wx.DefaultPosition, wx.Size( 600, 400 ) )
        #Controls
        self.tin = wx.TextCtrl( self, 
                                size = wx.Size( 600, 400 ),
                                style=wx.TE_MULTILINE )        
        self.test_panel = ScrolledPanel( self, 
                                         size = wx.Size( 600, 400 ) )
        self.test_panel.SetupScrolling()
        self.tin2 = wx.StaticText( self.test_panel )

        #Layout
        #-- Scrolled Window
        self.panel_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.panel_sizer.Add( self.tin2, 0, wx.EXPAND )
        self.test_panel.SetSizer( self.panel_sizer )
        self.panel_sizer.Fit(self.test_panel)
        #-- Main Frame
        self.inner_sizer = wx.BoxSizer( wx.HORIZONTAL )        
        self.inner_sizer.Add( self.tin, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 50  )
        self.inner_sizer.Add( self.test_panel, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 50  )

        self.sizer = wx.BoxSizer( wx.VERTICAL )
        self.sizer.Add(self.inner_sizer, 1, wx.ALL | wx.EXPAND, 20)        
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.sizer.Layout()

        self.test_panel.SetAutoLayout(1)

        #Bind Events
        self.tin.Bind( wx.EVT_TEXT, self.TextChange )

    def TextChange( self, event ):
        self.tin2.SetLabel(self.tin.GetValue())
        self.test_panel.FitInside()


class MyApp( wx.App ):
    def OnInit( self ):
        self.fr = MyFrame( None, -1, "TitleX" )
        self.fr.Show( True )
        self.SetTopWindow( self.fr )
        return True

app = MyApp( 0 )
app.MainLoop()

def main():

    win = 1

if ( __name__ == "__main__" ):
    main()    