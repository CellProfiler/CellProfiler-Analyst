from bench import *
from metadatainput import *
from lineagepanel import *
from experimentsettings import *

class LineageProfiler(wx.App):
    '''The LineageProfiler Application
    This launches the main UI, and keeps track of the session.
    '''
    def OnInit(self):

        settings_frame = wx.Frame(None, title='Experiment Settings', 
                                  size=(600, 400), pos=(-1,-1))
        p = ExperimentSettingsWindow(settings_frame)
        settings_frame.Show()
        
        settings_frame.SetMenuBar(wx.MenuBar())
        fileMenu = wx.Menu()
        saveSettingsMenuItem = fileMenu.Append(-1, 'Save settings\tCtrl+S', help='')
        loadSettingsMenuItem = fileMenu.Append(-1, 'Load settings\tCtrl+O', help='')
        settings_frame.Bind(wx.EVT_MENU, on_save_settings, saveSettingsMenuItem)
        settings_frame.Bind(wx.EVT_MENU, on_load_settings, loadSettingsMenuItem) 
        settings_frame.GetMenuBar().Append(fileMenu, 'File')

        
        bench_frame = Bench(None, size=(600,-1), 
                            pos=(0,settings_frame.Position[1]+410))
        bench_frame.Show()
        
        return True
        


if __name__ == '__main__':
    app = LineageProfiler()
    ExperimentSettings.getInstance().load_from_file('/Users/afraser/Desktop/experiment_settings.txt')
    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import cellprofiler.utilities.jutil as jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
