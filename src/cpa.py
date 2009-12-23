# This must come first for py2app/py2exe
__version__ = ''
try:
    import cpa_version
    __version__ = 'r'+cpa_version.VERSION
except: pass
from ClassifierGUI import *
# ---

import wx
import sys
import logging
import threading
from ImageViewer import ImageViewer
from Scatter import Scatter
from Histogram import Histogram
from Density import Density
from icons import get_cpa_icon, get_cpa_splash, imviewer_icon, datatable_icon, classifier_icon, pv_icon, scatter_icon, histogram_icon, density_icon

# Toolbar icons

ID_CLASSIFIER = wx.NewId()
ID_PLATE_VIEWER = wx.NewId()
ID_DATA_TABLE = wx.NewId()
ID_IMAGE_VIEWER = wx.NewId()
ID_SCATTER = wx.NewId()
ID_HISTOGRAM = wx.NewId()
ID_DENSITY = wx.NewId()

class FuncLog(logging.Handler):
    '''
    A logging handler that sends logs to an update function
    '''
    def __init__(self, update):
        logging.Handler.__init__(self)
        self.update = update
                
    def emit(self, record):
        self.update(self.format(record))


class MainGUI(wx.Frame):
    '''
    GUI for CellProfiler Analyst
    '''
    def __init__(self, properties, parent, id=-1, **kwargs):
        wx.Frame.__init__(self, parent, id=id, title='CellProfiler Analyst 2.0 %s'%(__version__), **kwargs)
        
        self.properties = properties
        self.tbicon = wx.TaskBarIcon()
        self.tbicon.SetIcon(get_cpa_icon(), 'CellProfiler Analyst 2.0')
        self.SetIcon(get_cpa_icon())
        self.SetName('CPA')
        self.Center(wx.HORIZONTAL)
        self.CreateStatusBar()
        
        #
        # Setup toolbar
        #
        tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        tb.SetToolBitmapSize((32,32))
        tb.SetSize((-1,132))
        tb.AddLabelTool(ID_CLASSIFIER, 'Classifier', classifier_icon.get_bitmap(), shortHelp='Classifier', longHelp='Launch Classifier')
        tb.AddLabelTool(ID_PLATE_VIEWER, 'PlateViewer', pv_icon.get_bitmap(), shortHelp='Plate Viewer', longHelp='Launch Plate Viewer')
        tb.AddLabelTool(ID_DATA_TABLE, 'DataTable', datatable_icon.get_bitmap(), shortHelp='Data Table', longHelp='Launch DataTable')
        tb.AddLabelTool(ID_IMAGE_VIEWER, 'ImageViewer', imviewer_icon.get_bitmap(), shortHelp='Image Viewer', longHelp='Launch ImageViewer')
        tb.AddLabelTool(ID_SCATTER, 'ScatterPlot', scatter_icon.get_bitmap(), shortHelp='Scatter Plot', longHelp='Launch Scatter Plot')
        tb.AddLabelTool(ID_HISTOGRAM, 'Histogram', histogram_icon.get_bitmap(), shortHelp='Histogram', longHelp='Launch Histogram')
        tb.AddLabelTool(ID_DENSITY, 'DensityPlot', density_icon.get_bitmap(), shortHelp='Density Plot', longHelp='Launch Density Plot')
        tb.Realize()
        
        #
        # Setup menu items
        #
        self.SetMenuBar(wx.MenuBar())
        fileMenu = wx.Menu()
        saveLogMenuItem = fileMenu.Append(-1, 'Save Log\tCtrl+S', help='Save the contents of the log window.')
        fileMenu.AppendSeparator()
        self.exitMenuItem = fileMenu.Append(ID_EXIT, 'Exit\tCtrl+Q', help='Exit classifier')
        self.GetMenuBar().Append(fileMenu, 'File')

        toolsMenu = wx.Menu()
        classifierMenuItem  = toolsMenu.Append(-1, 'Classifier\tCtrl+Shift+C', help='Launches Classifier.')
        plateMapMenuItem    = toolsMenu.Append(-1, 'Plate Viewer\tCtrl+Shift+P', help='Launches the Plate Viewer tool.')
        dataTableMenuItem   = toolsMenu.Append(-1, 'Data Table\tCtrl+Shift+T', help='Launches the Data Table tool.')
        imageViewerMenuItem = toolsMenu.Append(-1, 'Image Viewer\tCtrl+Shift+I', help='Launches the ImageViewer tool.')
        scatterMenuItem     = toolsMenu.Append(-1, 'Scatter Plot\tCtrl+Shift+A', help='Launches the Scatter Plot tool.')
        histogramMenuItem   = toolsMenu.Append(-1, 'Histogram Plot\tCtrl+Shift+H', help='Launches the Histogram Plot tool.')
        densityMenuItem     = toolsMenu.Append(-1, 'Density Plot\tCtrl+Shift+D', help='Launches the Density Plot tool.')
        self.GetMenuBar().Append(toolsMenu, 'Tools')

        logMenu = wx.Menu()        
        debugMenuItem    = logMenu.AppendRadioItem(-1, 'Debug\tCtrl+1', help='Logging window will display debug-level messages.')
        infoMenuItem     = logMenu.AppendRadioItem(-1, 'Info\tCtrl+2', help='Logging window will display info-level messages.')
        warnMenuItem     = logMenu.AppendRadioItem(-1, 'Warnings\tCtrl+3', help='Logging window will display warning-level messages.')
        errorMenuItem    = logMenu.AppendRadioItem(-1, 'Errors\tCtrl+4', help='Logging window will display error-level messages.')
        criticalMenuItem = logMenu.AppendRadioItem(-1, 'Critical\tCtrl+5', help='Logging window will only display critical messages.')
        infoMenuItem.Check()
        self.GetMenuBar().Append(logMenu, 'Logging')
        
        helpMenu = wx.Menu()
        aboutMenuItem = helpMenu.Append(-1, text='About', help='About CPA 2.0')
        self.GetMenuBar().Append(helpMenu, 'Help')

        
        # console and logging
        self.console = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.console.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.console.SetBackgroundColour('#111111')
        
        self.console.SetForegroundColour('#DDDDDD')
        log_level = logging.INFO
        self.logr = logging.getLogger()
        self.set_log_level(log_level)
        self.log_text = ''
        def update(x):
            self.log_text += x+'\n'
        hdlr = FuncLog(update)
#        hdlr.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
#        hdlr.setFormatter(logging.Formatter('%(levelname)s | %(name)s | %(message)s [@ %(asctime)s in %(filename)s:%(lineno)d]'))
        self.logr.addHandler(hdlr)
        # log_levels are 10,20,30,40,50
        logMenu.GetMenuItems()[(log_level/10)-1].Check()
        
        self.Bind(wx.EVT_MENU, lambda(_):self.set_log_level(logging.DEBUG), debugMenuItem)
        self.Bind(wx.EVT_MENU, lambda(_):self.set_log_level(logging.INFO), infoMenuItem)
        self.Bind(wx.EVT_MENU, lambda(_):self.set_log_level(logging.WARN), warnMenuItem)
        self.Bind(wx.EVT_MENU, lambda(_):self.set_log_level(logging.ERROR), errorMenuItem)
        self.Bind(wx.EVT_MENU, lambda(_):self.set_log_level(logging.CRITICAL), criticalMenuItem)
        self.Bind(wx.EVT_MENU, self.save_log, saveLogMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_classifier, classifierMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_plate_map_browser, plateMapMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_data_table, dataTableMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_image_viewer, imageViewerMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_scatter_plot, scatterMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_histogram_plot, histogramMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_density_plot, densityMenuItem)
        self.Bind(wx.EVT_MENU, self.on_show_about, aboutMenuItem)
        self.Bind(wx.EVT_TOOL, self.launch_classifier, id=ID_CLASSIFIER)
        self.Bind(wx.EVT_TOOL, self.launch_plate_map_browser, id=ID_PLATE_VIEWER)
        self.Bind(wx.EVT_TOOL, self.launch_data_table, id=ID_DATA_TABLE)
        self.Bind(wx.EVT_TOOL, self.launch_image_viewer, id=ID_IMAGE_VIEWER)        
        self.Bind(wx.EVT_TOOL, self.launch_scatter_plot, id=ID_SCATTER)
        self.Bind(wx.EVT_TOOL, self.launch_histogram_plot, id=ID_HISTOGRAM)
        self.Bind(wx.EVT_TOOL, self.launch_density_plot, id=ID_DENSITY)
        self.Bind(wx.EVT_MENU, self.on_close, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_IDLE, self.on_idle)

        
    def launch_classifier(self, evt=None):
        classifier = wx.FindWindowById(ID_CLASSIFIER) or wx.FindWindowByName('Classifier')
        if classifier:
            classifier.Show()
            classifier.SetFocus()
            logging.warn('You may only run one instance of Classifier at a time.')
            return
        classifier = ClassifierGUI(parent=self, properties=self.properties)
        classifier.Show(True)
        
    def launch_plate_map_browser(self, evt=None):
        self.pv = PlateMapBrowser(parent=self)
        self.pv.Show(True)
    
    def launch_data_table(self, evt=None):
        table = DataGrid(parent=self)
        table.Show(True)
        
    def launch_scatter_plot(self, evt=None):
        scatter = Scatter(parent=self)
        scatter.Show(True)

    def launch_histogram_plot(self, evt=None):
        hist = Histogram(parent=self)
        hist.Show(True)

    def launch_density_plot(self, evt=None):
        density = Density(parent=self)
        density.Show(True)

    def launch_image_viewer(self, evt=None):
        imviewer = ImageViewer(parent=self)
        imviewer.Show(True)
        
    def save_log(self, evt=None):
        dlg = wx.FileDialog(self, message="Save as:", defaultDir=os.getcwd(), 
                            defaultFile='CPA_log.txt', wildcard='txt', 
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        f = open(filename, 'w')
        f.write(self.console.Value)
        logging.info('Log saved to "%s"'%filename)
        
    def set_log_level(self, level):
        self.logr.setLevel(level)
        # cheat the logger so these always get displayed
        self.console.AppendText('Logging level: %s\n'%(logging.getLevelName(level)))

    def on_show_about(self, evt):
        ''' Shows a message box with the version number etc.'''
        message = ('CellProfiler Analyst was developed at The Broad Institute '
                   'Imaging Platform and is distributed under the GNU General '
                   'Public License version 2.')
        dlg = wx.MessageDialog(self, message, 'CellProfiler Analyst 2.0 %s'%(__version__ or 'unknown revision'), style=wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()

    def on_close(self, evt=None):
        # Classifier needs to be told to close so it can clean up it's threads
        classifier = wx.FindWindowById(ID_CLASSIFIER) or wx.FindWindowByName('Classifier')
        if classifier and classifier.Close() == False:
            return
        if any([wx.FindWindowByName(n) for n in 
                ['ImageViewer', 'Density', 'Scatter', 'Histogram', 'DataTable', 'PlateViewer']
                ]):
            dlg = wx.MessageDialog(self, 'Some tools are open, are you sure you want to quit CPA?', 'Quit CellProfiler Analyst?', wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response != wx.ID_YES:
                return            
        self.Destroy()
        
    def on_idle(self, evt=None):
        if self.log_text != '':
            self.console.AppendText(self.log_text)
            self.log_text = ''
        




def load_properties():
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])      # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        print 'CellProfiler Analyst requires a properties file.  Exiting.'
        sys.exit()




if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    
    global defaultDir
    defaultDir = os.getcwd()
    
    # Handles args to MacOS "Apps"
    if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
        del sys.argv[1]

    # Initialize the app early because the fancy exception handler
    # depends on it in order to show a dialog.
    app = wx.PySimpleApp()
    
    # Install our own pretty exception handler unless one has already
    # been installed (e.g., a debugger)
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = show_exception_as_dialog

    p = Properties.getInstance()

    # splashscreen
    # splash
    splashimage = get_cpa_splash()
    # If the splash image has alpha, it shows up transparently on
    # windows, so we blend it into a white background.
    splashbitmap = wx.EmptyBitmapRGBA(splashimage.GetWidth(), splashimage.GetHeight(), 255, 255, 255, 255)
    dc = wx.MemoryDC()
    dc.SelectObject(splashbitmap)
    dc.DrawBitmap(splashimage, 0, 0)
    dc.Destroy() # necessary to avoid a crash in splashscreen
    splash = wx.SplashScreen(splashbitmap, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 2000, None, -1)

    cpa = MainGUI(p, None, size=(760,-1))
    cpa.Show(True)
    db = DBConnect.DBConnect.getInstance()
    db.register_gui_parent(cpa)
    dm = DataModel.getInstance()

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        load_properties()
        
    dm.PopulateModel()
    MulticlassSQL.CreateFilterTables()

    app.MainLoop()
    
    
    
    
