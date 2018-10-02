# =============================================================================
#
#   Main file for CellProfiler-Analyst
#
#   Run python setup.py py2app to build a dmg
#
# =============================================================================

#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import sys
import os
import os.path
import logging
import re
import javabridge
import bioformats
from cpa import __version__
import cpa.helpmenu
from cpa.properties import Properties
from cpa.dbconnect import DBConnect


class FuncLog(logging.Handler):
    '''A logging handler that sends logs to an update function.
    '''
    def __init__(self, update):
        logging.Handler.__init__(self)
        self.update = update

    def emit(self, record):
        self.update(self.format(record))


def setup_frozen_logging():
    # py2exe has a version of this in boot_common.py, but it causes an
    # error window to appear if any messages are actually written.
    class Stderr(object):
        softspace = 0 # python uses this for printing
        _file = None
        _error = None
        def write(self, text, fname=sys.executable + '.log'):
            if self._file is None and self._error is None:
                try:
                    self._file = open(fname, 'w')
                except Exception as details:
                    self._error = details
            if self._file is not None:
                self._file.write(text)
                self._file.flush()
        def flush(self):
            if self._file is not None:
                self._file.flush()
    # send everything to logfile
    sys.stderr = Stderr()
    sys.stdout = sys.stderr

if hasattr(sys, 'frozen') and sys.platform.startswith('win'):
    # on windows, log to a file (Mac goes to console)
    setup_frozen_logging()
logging.basicConfig(level=logging.DEBUG)

# Handles args to MacOS "Apps"
if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
    del sys.argv[1]

if len(sys.argv) > 1:
    # Load a properties file if passed in args
    p = Properties.getInstance()
    if sys.argv[1] == '--incell':
        # GE Incell xml wrapper
        # LOOP
        p.LoadIncellFiles(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        p.LoadFile(sys.argv[1])

import threading
from cpa.classifier import Classifier
from cpa.tableviewer import TableViewer
from cpa.plateviewer import PlateViewer
from cpa.imageviewer import ImageViewer
from cpa.imagegallery import ImageGallery
from cpa.boxplot import BoxPlot
from cpa.scatter import Scatter
from cpa.histogram import Histogram
from cpa.density import Density
from cpa.querymaker import QueryMaker
from cpa.normalizationtool import NormalizationUI
import cpa.icons
import cpa.cpaprefs
from cpa.cpatool import CPATool
import inspect

from cpa.icons import get_cpa_icon
import cpa.multiclasssql
# ---
import wx

ID_CLASSIFIER = wx.NewId()
ID_IMAGE_GALLERY = wx.NewId()
ID_PLATE_VIEWER = wx.NewId()
ID_TABLE_VIEWER = wx.NewId()
ID_IMAGE_VIEWER = wx.NewId()
ID_SCATTER = wx.NewId()
ID_HISTOGRAM = wx.NewId()
ID_DENSITY = wx.NewId()
ID_BOXPLOT = wx.NewId()
ID_NORMALIZE = wx.NewId()

def get_cpatool_subclasses():
    '''returns a list of CPATool subclasses.
    '''
    class_objs = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    return [klass for name, klass in class_objs
            if issubclass(klass, CPATool) and klass!=CPATool]

class MainGUI(wx.Frame):
    '''Main GUI frame for CellProfiler Analyst
    '''
    def __init__(self, properties, parent, id=-1, **kwargs):
        #wx.Frame.__init__(self, parent, id=id, title='CellProfiler Analyst 2.1.0 (r%s)'%(__version__), **kwargs)
        wx.Frame.__init__(self, parent, id=id, title='CellProfiler Analyst %s'%(__version__), **kwargs)
        self.properties = properties
        self.SetIcon(get_cpa_icon())
        self.tbicon = None
        self.SetName('CPA')
        self.Center(wx.HORIZONTAL)
        self.CreateStatusBar()

        #
        # Setup toolbar
        #
        tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        tb.SetToolBitmapSize((32,32))
        tb.SetSize((-1,132))
        tb.AddLabelTool(ID_IMAGE_GALLERY, 'Image Gallery', cpa.icons.image_gallery.ConvertToBitmap(), shortHelp='Image Gallery', longHelp='Launch Image Gallery Viewer')
        tb.AddLabelTool(ID_CLASSIFIER, 'Classifier', cpa.icons.classifier.ConvertToBitmap(), shortHelp='Classifier', longHelp='Launch Classifier')
        # tb.AddLabelTool(ID_CLASSIFIER, 'PixelClassifier', cpa.icons.pixelclassifier.ConvertToBitmap(), shortHelp='Pixel-based Classifier', longHelp='Launch pixel-based Classifier')
        tb.AddLabelTool(ID_PLATE_VIEWER, 'Plate Viewer', cpa.icons.platemapbrowser.ConvertToBitmap(), shortHelp='Plate Viewer', longHelp='Launch Plate Viewer')
        # tb.AddLabelTool(ID_IMAGE_VIEWER, 'ImageViewer', cpa.icons.image_viewer.ConvertToBitmap(), shortHelp='Image Viewer', longHelp='Launch ImageViewer')
        tb.AddLabelTool(ID_SCATTER, 'Scatter Plot', cpa.icons.scatter.ConvertToBitmap(), shortHelp='Scatter Plot', longHelp='Launch Scatter Plot')
        tb.AddLabelTool(ID_HISTOGRAM, 'Histogram', cpa.icons.histogram.ConvertToBitmap(), shortHelp='Histogram', longHelp='Launch Histogram')
        tb.AddLabelTool(ID_DENSITY, 'Density Plot', cpa.icons.density.ConvertToBitmap(), shortHelp='Density Plot', longHelp='Launch Density Plot')
        tb.AddLabelTool(ID_BOXPLOT, 'Box Plot', cpa.icons.boxplot.ConvertToBitmap(), shortHelp='Box Plot', longHelp='Launch Box Plot')
        tb.AddLabelTool(ID_TABLE_VIEWER, 'Table Viewer', cpa.icons.data_grid.ConvertToBitmap(), shortHelp='Table Viewer', longHelp='Launch Table Viewer')
        # tb.AddLabelTool(ID_NORMALIZE, 'Normalize', cpa.icons.normalize.ConvertToBitmap(), shortHelp='Normalization Tool', longHelp='Launch Feature Normalization Tool')
        tb.Realize()
        # TODO: IMG-1071 - The following was meant to resize based on the toolbar size but GetEffectiveMinSize breaks on Macs 
        # Not the Case anymore with wx.Python 3
        # self.SetDimensions(-1, -1, tb.GetEffectiveMinSize().width, -1, wx.SIZE_USE_EXISTING)


        #
        # Setup menu items
        #
        self.SetMenuBar(wx.MenuBar())
        fileMenu = wx.Menu()
        savePropertiesMenuItem = fileMenu.Append(-1, 'Save properties\tCtrl+S', help='Save the properties.')
##        loadWorkspaceMenuItem = fileMenu.Append(-1, 'Load properties\tCtrl+O', help='Open another properties file.')
        fileMenu.AppendSeparator()
        saveWorkspaceMenuItem = fileMenu.Append(-1, 'Save workspace\tCtrl+Shift+S', help='Save the currently open plots and settings.')
        loadWorkspaceMenuItem = fileMenu.Append(-1, 'Load workspace\tCtrl+Shift+O', help='Open plots saved in a previous workspace.')
        fileMenu.AppendSeparator()
        saveLogMenuItem = fileMenu.Append(-1, 'Save log', help='Save the contents of the log window.')
        fileMenu.AppendSeparator()
        self.exitMenuItem = fileMenu.Append(wx.ID_EXIT, 'Exit\tCtrl+Q', help='Exit classifier')
        self.GetMenuBar().Append(fileMenu, 'File')

        toolsMenu = wx.Menu()
        imageGalleryMenuItem = toolsMenu.Append(ID_IMAGE_GALLERY, 'Image Gallery Viewer\tCtrl+Shift+I', help='Launches the Image Gallery')
        classifierMenuItem  = toolsMenu.Append(ID_CLASSIFIER, 'Classifier\tCtrl+Shift+C', help='Launches Classifier.')
        plateMapMenuItem    = toolsMenu.Append(ID_PLATE_VIEWER, 'Plate Viewer\tCtrl+Shift+P', help='Launches the Plate Viewer tool.')
        #imageViewerMenuItem = toolsMenu.Append(ID_IMAGE_VIEWER, 'Image Viewer\tCtrl+Shift+I', help='Launches the ImageViewer tool.')
        scatterMenuItem     = toolsMenu.Append(ID_SCATTER, 'Scatter Plot\tCtrl+Shift+A', help='Launches the Scatter Plot tool.')
        histogramMenuItem   = toolsMenu.Append(ID_HISTOGRAM, 'Histogram Plot\tCtrl+Shift+H', help='Launches the Histogram Plot tool.')
        densityMenuItem     = toolsMenu.Append(ID_DENSITY, 'Density Plot\tCtrl+Shift+D', help='Launches the Density Plot tool.')
        boxplotMenuItem     = toolsMenu.Append(ID_BOXPLOT, 'Box Plot\tCtrl+Shift+B', help='Launches the Box Plot tool.')
        dataTableMenuItem   = toolsMenu.Append(ID_TABLE_VIEWER, 'Table Viewer\tCtrl+Shift+T', help='Launches the Table Viewer tool.')
        normalizeMenuItem   = toolsMenu.Append(ID_NORMALIZE, 'Normalization Tool\tCtrl+Shift+T', help='Launches a tool for generating normalized values for measurement columns in your tables.')
        self.GetMenuBar().Append(toolsMenu, 'Tools')

        logMenu = wx.Menu()
        debugMenuItem    = logMenu.AppendRadioItem(-1, 'Debug\tCtrl+1', help='Logging window will display debug-level messages.')
        infoMenuItem     = logMenu.AppendRadioItem(-1, 'Info\tCtrl+2', help='Logging window will display info-level messages.')
        warnMenuItem     = logMenu.AppendRadioItem(-1, 'Warnings\tCtrl+3', help='Logging window will display warning-level messages.')
        errorMenuItem    = logMenu.AppendRadioItem(-1, 'Errors\tCtrl+4', help='Logging window will display error-level messages.')
        criticalMenuItem = logMenu.AppendRadioItem(-1, 'Critical\tCtrl+5', help='Logging window will only display critical messages.')
        infoMenuItem.Check()
        self.GetMenuBar().Append(logMenu, 'Logging')

        advancedMenu = wx.Menu()
        #normalizeMenuItem = advancedMenu.Append(-1, 'Launch feature normalization tool', help='Launches a tool for generating normalized values for measurement columns in your tables.')
        queryMenuItem = advancedMenu.Append(-1, 'Launch SQL query tool', help='Opens a tool for making SQL queries to the CPA database. Advanced users only.')
        clearTableLinksMenuItem = advancedMenu.Append(-1, 'Clear table linking information', help='Removes the tables from your database that tell CPA how to link your tables.')
        self.GetMenuBar().Append(advancedMenu, 'Advanced')

        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self), 'Help')

        # console and logging
        self.console = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
        self.console.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Black background and white font
        self.console.SetDefaultStyle(wx.TextAttr(wx.WHITE,wx.BLACK))
        self.console.SetBackgroundColour('#000000')  

        log_level = logging.INFO # INFO is the default log level
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

        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.DEBUG), debugMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.INFO), infoMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.WARN), warnMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.ERROR), errorMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.CRITICAL), criticalMenuItem)
        self.Bind(wx.EVT_MENU, self.on_save_properties, savePropertiesMenuItem)
        self.Bind(wx.EVT_MENU, self.on_save_workspace, saveWorkspaceMenuItem)
        self.Bind(wx.EVT_MENU, self.on_load_workspace, loadWorkspaceMenuItem)
        self.Bind(wx.EVT_MENU, self.save_log, saveLogMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_normalization_tool, normalizeMenuItem)
        self.Bind(wx.EVT_MENU, self.clear_link_tables, clearTableLinksMenuItem)
        self.Bind(wx.EVT_MENU, self.launch_query_maker, queryMenuItem)
        self.Bind(wx.EVT_TOOL, self.launch_classifier, id=ID_CLASSIFIER)
        self.Bind(wx.EVT_TOOL, self.launch_plate_map_browser, id=ID_PLATE_VIEWER)
        self.Bind(wx.EVT_TOOL, self.launch_table_viewer, id=ID_TABLE_VIEWER)
        self.Bind(wx.EVT_TOOL, self.launch_image_viewer, id=ID_IMAGE_VIEWER)
        self.Bind(wx.EVT_TOOL, self.launch_image_gallery, id=ID_IMAGE_GALLERY)
        self.Bind(wx.EVT_TOOL, self.launch_scatter_plot, id=ID_SCATTER)
        self.Bind(wx.EVT_TOOL, self.launch_histogram_plot, id=ID_HISTOGRAM)
        self.Bind(wx.EVT_TOOL, self.launch_density_plot, id=ID_DENSITY)
        self.Bind(wx.EVT_TOOL, self.launch_box_plot, id=ID_BOXPLOT)
        self.Bind(wx.EVT_TOOL, self.launch_normalization_tool, id=ID_NORMALIZE)
        self.Bind(wx.EVT_MENU, self.on_close, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_IDLE, self.on_idle)

    def launch_classifier(self, evt=None):
        # Brave new world! Allowing multiple classifiers
        # classifier = wx.FindWindowById(ID_CLASSIFIER) or wx.FindWindowByName('Classifier')
        # if classifier:
        #     classifier.Show()
        #     classifier.SetFocus()
        #     logging.warn('You may only run one instance of Classifier at a time.')
        #     return
        classifier = Classifier(parent=self, properties=self.properties)
        classifier.Show(True)

    def launch_plate_map_browser(self, evt=None):
        self.pv = PlateViewer(parent=self)
        self.pv.Show(True)

    def launch_table_viewer(self, evt=None):
        table = TableViewer(parent=self)
        table.new_blank_table(100,10)
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

    def launch_image_gallery(self, evt=None):
        colViewer = ImageGallery(parent=self, properties=self.properties)
        colViewer.Show(True)

    def launch_box_plot(self, evt=None):
        boxplot = BoxPlot(parent=self)
        boxplot.Show(True)

    def launch_query_maker(self, evt=None):
        querymaker = QueryMaker(parent=self)
        querymaker.Show(True)

    def launch_normalization_tool(self, evt=None):
        normtool = NormalizationUI(parent=self)
        normtool.Show(True)

    def on_save_properties(self, evt):
        p = Properties.getInstance()
        dirname, filename = os.path.split(p._filename)
        ext = os.path.splitext(p._filename)[-1]
        dlg = wx.FileDialog(self, message="Save properties as...", defaultDir=dirname,
                            defaultFile=filename, wildcard=ext,
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            p.save_file(dlg.GetPath())

    def on_save_workspace(self, evt):
        p = Properties.getInstance()
        dlg = wx.FileDialog(self, message="Save workspace as...", defaultDir=os.getcwd(),
                            defaultFile='%s_%s.workspace'%(os.path.splitext(os.path.split(p._filename)[1])[0], p.image_table),
                            style=wx.SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            wx.GetApp().save_workspace(dlg.GetPath())

    def on_load_workspace(self, evt):
        dlg = wx.FileDialog(self, "Select the file containing your CPAnalyst workspace...", wildcard="Workspace file (*.workspace)|*.workspace",
                            defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            wx.GetApp().load_workspace(dlg.GetPath())

    def save_log(self, evt=None):
        dlg = wx.FileDialog(self, message="Save log as...", defaultDir=os.getcwd(),
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

    def clear_link_tables(self, evt=None):
        p = Properties.getInstance()
        dlg = wx.MessageDialog(self, 'This will delete the tables '
                    '"%s" and "%s" from your database. '
                    'CPA will automatically recreate these tables as it '
                    'discovers how your database is linked. Are you sure you '
                    'want to proceed?'
                    %(p.link_tables_table, p.link_columns_table),
                    'Clear table linking information?',
                    wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        response = dlg.ShowModal()
        if response != wx.ID_YES:
            return
        db = DBConnect.getInstance()
        db.execute('DROP TABLE IF EXISTS %s'%(p.link_tables_table))
        db.execute('DROP TABLE IF EXISTS %s'%(p.link_columns_table))
        db.Commit()

    def on_close(self, evt=None):
        # Classifier needs to be told to close so it can clean up it's threads
        classifier = wx.FindWindowById(ID_CLASSIFIER) or wx.FindWindowByName('Classifier')
        if classifier and classifier.Close() == False:
            return
            
        if any(wx.GetApp().get_plots()):
            dlg = wx.MessageDialog(self, 'Some tools are open, are you sure you want to quit CPA?', 'Quit CellProfiler Analyst?', wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response != wx.ID_YES:
                return

        try:
            logging.debug("Shutting of Java VM")
            import javabridge
            javabridge.kill_vm()
        except:
            logging.debug("Failed to kill the Java VM")

        # Blow up EVVVVERYTHIIINGGG!!! Muahahahahhahahah!
        for win in wx.GetTopLevelWindows():
            logging.debug('Destroying: %s'%(win))
            win.Destroy()
        if self.tbicon is not None:
            self.tbicon.Destroy()
        
        self.Destroy()

    def on_idle(self, evt=None):
        if self.log_text != '':
            self.console.AppendText(self.log_text)
            self.log_text = ''

# new version check
def new_version_cb(new_version, new_version_info):
    # called from a child thread, so use CallAfter to bump it to the gui thread
    def cb2():
        def set_check_pref(val):
            cpa.cpaprefs.set_check_new_versions(val)

        def skip_this_version():
            cpa.cpaprefs.set_skip_version(new_version)

        # showing a modal dialog while the splashscreen is up causes a hang
        try: wx.GetApp().splash.Destroy()
        except: pass

        import cpa.gui.newversiondialog as nvd
        dlg = nvd.NewVersionDialog(None, "CellProfiler Analyst update available (version %d)"%(new_version),
                                   new_version_info, 'http://cellprofiler.org/releases#CPA',
                                   cpa.cpaprefs.get_check_new_versions(), set_check_pref, skip_this_version)
        dlg.Show()

    wx.CallAfter(cb2)

class CPAnalyst(wx.App):
    '''The CPAnalyst application.
    This launches the main UI, and keeps track of the session.
    '''
    def Start(self):
        '''Initialize CPA
        '''

        '''List of tables created by the user during this session'''
        self.user_tables = []

        # splashscreen
        splashimage = cpa.icons.cpa_splash.ConvertToBitmap()
        # If the splash image has alpha, it shows up transparently on
        # windows, so we blend it into a white background.
        splashbitmap = wx.EmptyBitmapRGBA(splashimage.GetWidth(),
                                          splashimage.GetHeight(),
                                          255, 255, 255, 255)
        dc = wx.MemoryDC()
        dc.SelectObject(splashbitmap)
        dc.DrawBitmap(splashimage, 0, 0)
        dc.Destroy() # necessary to avoid a crash in splashscreen
        splash = wx.SplashScreen(splashbitmap, wx.SPLASH_CENTRE_ON_SCREEN |
                                wx.SPLASH_TIMEOUT, 2000, None, -1)
        self.splash = splash

        p = Properties.getInstance()
        if not p.is_initialized():
            from cpa.guiutils import show_load_dialog
            splash.Destroy()
            if not show_load_dialog():
                splash.Destroy()
                example_link_address = 'cellprofiler.org'
                dlg = wx.MessageDialog(None, 'CellProfiler Analyst requires a properties file. Download an example at %s' % (
                                           example_link_address), 'Properties file required', wx.OK)
                response = dlg.ShowModal()
                logging.error('CellProfiler Analyst requires a properties file. Exiting.')
                return False

        self.frame = MainGUI(p, None, size=(1000,-1))

        db = DBConnect.getInstance()
        # Black magic: Bus errors occur on Mac OS X if we wait until
        # the JVM or the wx event look has started to connect. But it
        # has to be done after we have read the properties file. So we
        # do it here.
        db.connect()
        db.register_gui_parent(self.frame)

        # The JVM has to be started after db.connect(), otherwise bus errors
        # occur on Mac OS X.
        javabridge.start_vm(class_path=bioformats.JARS, run_headless=True)

        # removes the log4j warnings
        javabridge.attach()

        # TODO: check for updates
        try:
            if __version__ != -1:
                import cpa.util.check_for_updates as cfu
                cfu.check_for_updates('http://cellprofiler.org/updates/CPA.html',
                                      max(__version__, cpa.cpaprefs.get_skip_version()),
                                      new_version_cb,
                                      user_agent='CPAnalyst/%s'%(__version__))
        except ImportError:
            logging.warn("CPA was unable to check for updates. Could not import cpa.util.check_for_updates.")

        self.frame.Show() # Show frame
        return True

    def get_plots(self):
        '''return a list of all plots'''
        return [win for win in self.frame.Children if issubclass(type(win), CPATool)]

    def get_plot(self, name):
        '''return the plot with the given name'''
        return wx.FindWindowByName(name)

    def load_workspace(self, filepath, close_open_plots=False):
        '''Loads a CPA workspace file and uses it to restore all plots, gates,
        and filters that were saved.
        '''
        logging.info('loading workspace...')
        f = open(filepath, 'U')
        lines = f.read()
        lines = lines.split('\n')
        lines = lines [4:] # first 4 lines are header information
        settings = {}
        pos = 20
        for i in range(len(lines)):
            for cpatool in get_cpatool_subclasses():
                if lines[i] == cpatool.__name__:
                    logging.info('opening plot "%s"'%(lines[i]))
                    while lines[i+1].startswith('\t'):
                        i += 1
                        setting, value = map(str.strip, lines[i].split(':', 1))
                        settings[setting] = value
                    pos += 15
                    plot = cpatool(parent=self.frame, pos=(pos,pos))
                    plot.Show(True)
                    plot.load_settings(settings)
        logging.info('...done loading workspace')

    def save_workspace(self, filepath):
        '''Saves the current CPA workspace. This includes the current settings
        of all open tools along with any gates and filters that have been created.
        '''
        f = open(filepath, 'w')
        f.write('CellProfiler Analyst workflow\n')
        f.write('version: 1\n')
        f.write('CPA version: %s\n'%(__version__))
        f.write('\n')
        for plot in self.get_plots():
            f.write('%s\n'%(plot.tool_name))
            for setting, value in plot.save_settings().items():
                assert ':' not in setting
                f.write('\t%s : %s\n'%(setting, str(value)))
            f.write('\n')
        f.close()

    def make_unique_plot_name(self, prefix):
        '''This function must be called to generate a unique name for each plot.
        eg: plot.SetName(wx.GetApp().make_unique_plot_name('Histogram'))
        '''
        plot_num = max([int(plot.Name[len(prefix):])
                        for plot in self.plots if plot.Name.startswith(prefix)])
        return '%s %d'%(prefix, plot_num)


if __name__ == "__main__":    
    # Initialize the app early because the fancy exception handler
    # depends on it in order to show a 
    app = CPAnalyst(redirect=False)
    app.Start()
    # Install our own pretty exception handler unless one has already
    # been installed (e.g., a debugger)
    if sys.excepthook == sys.__excepthook__:
       from cpa.errors import show_exception_as_dialog
       sys.excepthook = show_exception_as_dialog

    app.MainLoop()
    os._exit(0) # Enforces Exit, see issue #102
