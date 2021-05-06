# =============================================================================
#
#   Main file for CellProfiler-Analyst
#
# =============================================================================



import sys
import os
import os.path
import logging

from cpa.dimensionreduction import DimensionReduction
from cpa.guiutils import create_status_bar
from cpa.util.version import display_version
from cpa.properties import Properties
from cpa.dbconnect import DBConnect
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


class FuncLog(logging.Handler):
    '''A logging handler that sends logs to an update function.
    '''
    def __init__(self, update):
        logging.Handler.__init__(self)
        self.update = update

    def emit(self, record):
        self.update(self.format(record))

logging.basicConfig(level=logging.DEBUG)

# Handles args to MacOS "Apps"
if len(sys.argv) > 1 and sys.argv[1].startswith('-psn'):
    del sys.argv[1]

if len(sys.argv) > 1:
    # Load a properties file if passed in args
    p = Properties()
    if sys.argv[1] == '--incell':
        # GE Incell xml wrapper
        # LOOP
        p.LoadIncellFiles(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        p.LoadFile(sys.argv[1])


from cpa.cpatool import CPATool
import inspect

import cpa.multiclasssql
# ---
import wx

ID_CLASSIFIER = wx.NewIdRef()
ID_IMAGE_GALLERY = wx.NewIdRef()
ID_PLATE_VIEWER = wx.NewIdRef()
ID_TABLE_VIEWER = wx.NewIdRef()
ID_IMAGE_VIEWER = wx.NewIdRef()
ID_SCATTER = wx.NewIdRef()
ID_HISTOGRAM = wx.NewIdRef()
ID_DENSITY = wx.NewIdRef()
ID_BOXPLOT = wx.NewIdRef()
ID_DIMENSREDUX = wx.NewIdRef()
ID_NORMALIZE = wx.NewIdRef()

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

        from cpa.icons import get_icon, get_cpa_icon

        wx.Frame.__init__(self, parent, id=id, title='CellProfiler Analyst %s'%(display_version), **kwargs)
        self.properties = properties
        self.SetIcon(get_cpa_icon())
        self.tbicon = None
        self.SetName('CPA')
        self.Center(wx.HORIZONTAL)
        self.status_bar = create_status_bar(self)
        self.log_io = True

        #
        # Setup toolbar
        #
        tb = self.CreateToolBar(wx.TB_HORZ_TEXT|wx.TB_FLAT)
        tb.SetToolBitmapSize((32,32))
        tb.SetSize((-1,132))
        tb.AddTool(ID_IMAGE_GALLERY.GetId(), 'Image Gallery', get_icon("image_gallery").ConvertToBitmap(), shortHelp='Image Gallery')
        tb.AddTool(ID_CLASSIFIER.GetId(), 'Classifier', get_icon("classifier").ConvertToBitmap(), shortHelp='Classifier')
        # tb.AddLabelTool(ID_CLASSIFIER, 'PixelClassifier', get_icon("pixelclassifier").ConvertToBitmap(), shortHelp='Pixel-based Classifier', longHelp='Launch pixel-based Classifier')
        tb.AddTool(ID_PLATE_VIEWER.GetId(), 'Plate Viewer', get_icon("platemapbrowser").ConvertToBitmap(), shortHelp='Plate Viewer')
        # tb.AddLabelTool(ID_IMAGE_VIEWER, 'ImageViewer', get_icon("image_viewer").ConvertToBitmap(), shortHelp='Image Viewer', longHelp='Launch ImageViewer')
        tb.AddTool(ID_SCATTER.GetId(), 'Scatter Plot', get_icon("scatter").ConvertToBitmap(), shortHelp='Scatter Plot')
        tb.AddTool(ID_HISTOGRAM.GetId(), 'Histogram', get_icon("histogram").ConvertToBitmap(), shortHelp='Histogram')
        tb.AddTool(ID_DENSITY.GetId(), 'Density Plot', get_icon("density").ConvertToBitmap(), shortHelp='Density Plot')
        tb.AddTool(ID_BOXPLOT.GetId(), 'Box Plot', get_icon("boxplot").ConvertToBitmap(), shortHelp='Box Plot')
        tb.AddTool(ID_DIMENSREDUX.GetId(), 'Reduction', get_icon("dimensionality").ConvertToBitmap(), shortHelp='Dimensionality Reduction')
        tb.AddTool(ID_TABLE_VIEWER.GetId(), 'Table Viewer', get_icon("data_grid").ConvertToBitmap(), shortHelp='Table Viewer')
        # tb.AddLabelTool(ID_NORMALIZE, 'Normalize', get_icon("normalize").ConvertToBitmap(), shortHelp='Normalization Tool', longHelp='Launch Feature Normalization Tool')
        tb.Realize()

        #
        # Setup menu items
        #
        self.SetMenuBar(wx.MenuBar())
        fileMenu = wx.Menu()
        loadPropertiesMenuItem = fileMenu.Append(-1, 'Load properties file', helpString='Load a properties file.')
        savePropertiesMenuItem = fileMenu.Append(-1, 'Save properties\tCtrl+S', helpString='Save the properties.')
##        loadWorkspaceMenuItem = fileMenu.Append(-1, 'Load properties\tCtrl+O', helpString='Open another properties file.')
        fileMenu.AppendSeparator()
        saveWorkspaceMenuItem = fileMenu.Append(-1, 'Save workspace\tCtrl+Shift+S', helpString='Save the currently open plots and settings.')
        loadWorkspaceMenuItem = fileMenu.Append(-1, 'Load workspace\tCtrl+Shift+O', helpString='Open plots saved in a previous workspace.')
        fileMenu.AppendSeparator()
        saveLogMenuItem = fileMenu.Append(-1, 'Save log', helpString='Save the contents of the log window.')
        fileMenu.AppendSeparator()
        self.exitMenuItem = fileMenu.Append(wx.ID_EXIT, 'Exit\tCtrl+Q', helpString='Exit classifier')
        self.GetMenuBar().Append(fileMenu, 'File')

        toolsMenu = wx.Menu()
        imageGalleryMenuItem = toolsMenu.Append(ID_IMAGE_GALLERY, 'Image Gallery Viewer\tCtrl+Shift+I', helpString='Launches the Image Gallery')
        classifierMenuItem  = toolsMenu.Append(ID_CLASSIFIER, 'Classifier\tCtrl+Shift+C', helpString='Launches Classifier.')
        plateMapMenuItem    = toolsMenu.Append(ID_PLATE_VIEWER, 'Plate Viewer\tCtrl+Shift+P', helpString='Launches the Plate Viewer tool.')
        #imageViewerMenuItem = toolsMenu.Append(ID_IMAGE_VIEWER, 'Image Viewer\tCtrl+Shift+I', helpString='Launches the ImageViewer tool.')
        scatterMenuItem     = toolsMenu.Append(ID_SCATTER, 'Scatter Plot\tCtrl+Shift+A', helpString='Launches the Scatter Plot tool.')
        histogramMenuItem   = toolsMenu.Append(ID_HISTOGRAM, 'Histogram Plot\tCtrl+Shift+H', helpString='Launches the Histogram Plot tool.')
        densityMenuItem     = toolsMenu.Append(ID_DENSITY, 'Density Plot\tCtrl+Shift+D', helpString='Launches the Density Plot tool.')
        boxplotMenuItem     = toolsMenu.Append(ID_BOXPLOT, 'Box Plot\tCtrl+Shift+B', helpString='Launches the Box Plot tool.')
        dimensionMenuItem   = toolsMenu.Append(ID_DIMENSREDUX, 'Dimensionality Reduction', helpString='Launches the Dimensionality Reduction tool.')
        dataTableMenuItem   = toolsMenu.Append(ID_TABLE_VIEWER, 'Table Viewer\tCtrl+Shift+T', helpString='Launches the Table Viewer tool.')
        normalizeMenuItem   = toolsMenu.Append(ID_NORMALIZE, 'Normalization Tool\tCtrl+Shift+T', helpString='Launches a tool for generating normalized values for measurement columns in your tables.')
        self.GetMenuBar().Append(toolsMenu, 'Tools')

        logMenu = wx.Menu()
        debugMenuItem    = logMenu.AppendRadioItem(-1, 'Debug\tCtrl+1', help='Logging window will display debug-level messages.')
        infoMenuItem     = logMenu.AppendRadioItem(-1, 'Info\tCtrl+2', help='Logging window will display info-level messages.')
        warnMenuItem     = logMenu.AppendRadioItem(-1, 'Warnings\tCtrl+3', help='Logging window will display warning-level messages.')
        errorMenuItem    = logMenu.AppendRadioItem(-1, 'Errors\tCtrl+4', help='Logging window will display error-level messages.')
        criticalMenuItem = logMenu.AppendRadioItem(-1, 'Critical\tCtrl+5', help='Logging window will only display critical messages.')
        logioItem = logMenu.AppendCheckItem(-1, item='Log image loading', help='Log image loader events')
        infoMenuItem.Check()
        logioItem.Check()
        self.GetMenuBar().Append(logMenu, 'Logging')

        advancedMenu = wx.Menu()
        #normalizeMenuItem = advancedMenu.Append(-1, 'Launch feature normalization tool', helpString='Launches a tool for generating normalized values for measurement columns in your tables.')
        queryMenuItem = advancedMenu.Append(-1, 'Launch SQL query tool', helpString='Opens a tool for making SQL queries to the CPA database. Advanced users only.')
        clearTableLinksMenuItem = advancedMenu.Append(-1, 'Clear table linking information', helpString='Removes the tables from your database that tell CPA how to link your tables.')
        self.GetMenuBar().Append(advancedMenu, 'Advanced')
        import cpa.helpmenu
        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self, main=True), 'Help')

        # console and logging
        self.console = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
        self.console.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Black background and white font
        self.console.SetDefaultStyle(wx.TextAttr(wx.WHITE,wx.BLACK))
        self.console.SetBackgroundColour('#000000')

        log_level = logging.INFO # INFO is the default log level
        self.logr = logging.getLogger()
        self.set_log_level(log_level)
        self.log_text = ""
        def update(x):
            self.log_text += x+'\n'
        hdlr = FuncLog(update)
#        hdlr.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
#        hdlr.setFormatter(logging.Formatter('%(levelname)s | %(name)s | %(message)s [@ %(asctime)s in %(filename)s:%(lineno)d]'))
        self.logr.addHandler(hdlr)
        # log_levels are 10,20,30,40,50
        logMenu.GetMenuItems()[(log_level//10)-1].Check()

        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.DEBUG), debugMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.INFO), infoMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.WARN), warnMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.ERROR), errorMenuItem)
        self.Bind(wx.EVT_MENU, lambda _:self.set_log_level(logging.CRITICAL), criticalMenuItem)
        self.Bind(wx.EVT_MENU, self.on_toggle_iologging, logioItem)
        self.Bind(wx.EVT_MENU, self.on_load_properties, loadPropertiesMenuItem)
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
        self.Bind(wx.EVT_TOOL, self.launch_dimens_redux, id=ID_DIMENSREDUX)
        self.Bind(wx.EVT_TOOL, self.launch_normalization_tool, id=ID_NORMALIZE)
        self.Bind(wx.EVT_MENU, self.on_close, self.exitMenuItem)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_IDLE, self.on_idle)

    def confirm_properties(self):
        if self.properties.is_initialized():
            return True
        else:
            dlg = wx.MessageDialog(self, 'A valid properties file must be loaded to use this functionality',
                                   'Properties file needed', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            return False

    def launch_classifier(self, evt=None):
        if self.confirm_properties():
            classifier = Classifier(parent=self, properties=self.properties)
            classifier.Show(True)

    def launch_plate_map_browser(self, evt=None):
        if self.confirm_properties():
            self.pv = PlateViewer(parent=self)
            self.pv.Show(True)

    def launch_table_viewer(self, evt=None):
        if self.confirm_properties():
            table = TableViewer(parent=self)
            table.new_blank_table(100,10)
            table.Show(True)

    def launch_scatter_plot(self, evt=None):
        if self.confirm_properties():
            scatter = Scatter(parent=self)
            scatter.Show(True)

    def launch_histogram_plot(self, evt=None):
        if self.confirm_properties():
            hist = Histogram(parent=self)
            hist.Show(True)

    def launch_density_plot(self, evt=None):
        if self.confirm_properties():
            density = Density(parent=self)
            density.Show(True)

    def launch_image_viewer(self, evt=None):
        if self.confirm_properties():
            imviewer = ImageViewer(parent=self)
            imviewer.Show(True)

    def launch_image_gallery(self, evt=None):
        if self.confirm_properties():
            colViewer = ImageGallery(parent=self, properties=self.properties)
            colViewer.Show(True)

    def launch_box_plot(self, evt=None):
        if self.confirm_properties():
            boxplot = BoxPlot(parent=self)
            boxplot.Show(True)

    def launch_dimens_redux(self, evt=None):
        if self.confirm_properties():
            dimens = DimensionReduction(parent=self)
            dimens.Show(True)

    def launch_query_maker(self, evt=None):
        if self.confirm_properties():
            querymaker = QueryMaker(parent=self)
            querymaker.Show(True)

    def launch_normalization_tool(self, evt=None):
        if self.confirm_properties():
            normtool = NormalizationUI(parent=self)
            normtool.Show(True)

    def on_toggle_iologging(self, evt):
        if evt.IsChecked():
            self.log_io = True
        else:
            self.log_io = False

    def on_load_properties(self, evt):
        # Show confirmation dialog.
        if self.properties.is_initialized():
            dlg = wx.MessageDialog(None, "Loading a new file will close all windows and clear unsaved data. Proceed?", 'Load properties file', wx.OK|wx.CANCEL)
            response = dlg.ShowModal()
            if response != wx.ID_OK:
                return

        # Close all subwindows
        for window in self.GetChildren():
            if isinstance(window, wx.Frame):
                window.Destroy()

        # Shut down existing connections and wipe properties.
        db = DBConnect()
        db.Disconnect()
        p = Properties()
        p.clear()
        from cpa.datamodel import DataModel
        DataModel.forget()
        from cpa.trainingset import CellCache
        CellCache.forget()
        self.console.Clear()

        if not p.is_initialized():
            from cpa.guiutils import show_load_dialog
            if not show_load_dialog():
                example_link_address = 'cellprofileranalyst.org'
                dlg = wx.MessageDialog(None, 'CellProfiler Analyst requires a properties file. Download an example at %s' % (
                                           example_link_address), 'Properties file required', wx.OK)
                response = dlg.ShowModal()
                logging.error('CellProfiler Analyst requires a properties file.')
            else:
                db.connect()
                db.register_gui_parent(self)

    def on_save_properties(self, evt):
        if not self.confirm_properties():
            return
        p = Properties()
        dirname, filename = os.path.split(p._filename)
        ext = os.path.splitext(p._filename)[-1]
        dlg = wx.FileDialog(self, message="Save properties as...", defaultDir=dirname,
                            defaultFile=filename, wildcard=ext,
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            p.save_file(dlg.GetPath())

    def on_save_workspace(self, evt):
        if not self.confirm_properties():
            return
        p = Properties()
        dlg = wx.FileDialog(self, message="Save workspace as...", defaultDir=os.getcwd(),
                            defaultFile='%s_%s.workspace'%(os.path.splitext(os.path.split(p._filename)[1])[0], p.image_table),
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            wx.GetApp().save_workspace(dlg.GetPath())

    def on_load_workspace(self, evt):
        if not self.confirm_properties():
            return
        dlg = wx.FileDialog(self, "Select the file containing your CPAnalyst workspace...", wildcard="Workspace file (*.workspace)|*.workspace",
                            defaultDir=os.getcwd(), style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            wx.GetApp().load_workspace(dlg.GetPath())

    def save_log(self, evt=None):
        dlg = wx.FileDialog(self, message="Save log as...", defaultDir=os.getcwd(),
                            defaultFile='CPA_log.txt', wildcard='txt',
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT|wx.FD_CHANGE_DIR)
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
        if not self.confirm_properties():
            return
        p = Properties()
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
        db = DBConnect()
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
            if javabridge.get_env() is not None:
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


class CPAnalyst(wx.App):
    '''The CPAnalyst application.
    This launches the main UI, and keeps track of the session.
    '''
    def Start(self):
        '''Initialize CPA
        '''
        if hasattr(sys, "frozen") and sys.platform == "darwin":
            # Some versions of Macos like to put CPA in a sandbox. If we're frozen Java should be packed in,
            # so let's just figure out the directory on run time.
            os.environ["CP_JAVA_HOME"] = os.path.abspath(os.path.join(sys.prefix, "..",  "Resources/Home"))
        elif sys.platform == "win32":
            # Windows gets very upset if system locale and wxpython locale don't match exactly.
            import locale
            # Need to startup wx in English, otherwise C++ can't load images.
            self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
            # Ensure Python uses the same locale as wx
            try:
                locale.setlocale(locale.LC_ALL, self.locale.GetName())
            except:
                logging.info(f"Python rejected the system locale detected by WX ('{self.locale.GetName()}').\n"
                      "This shouldn't cause problems, but please let us know if you encounter errors.")

        p = Properties()
        self.frame = MainGUI(p, None, size=(1000,-1))
        self.frame.Show() # Show frame
        if not p.is_initialized():
            from cpa.guiutils import show_load_dialog
            try:
                if not show_load_dialog():
                    example_link_address = 'cellprofileranalyst.org'
                    dlg = wx.MessageDialog(None, 'CellProfiler Analyst requires a properties file. Download an example at %s' % (
                                               example_link_address), 'Properties file required', wx.OK)
                    response = dlg.ShowModal()
                    logging.error('CellProfiler Analyst requires a properties file.')
                    return False
                else:
                    db = DBConnect()
                    db.connect()
                    db.register_gui_parent(self.frame)
            except Exception as e:
                p._initialized = False
                # Fully raising the exception during this startup sequence will crash CPA.
                # So we'll display it manually.
                show_exception_as_dialog(type(e), e, e.__traceback__, raisefurther=False)
                logging.critical(e)

        try:
            from cpa.updatechecker import check_update
            check_update(self.frame, event=False)
        except:
            logging.warn("CPA was unable to check for updates.")
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
                        setting, value = list(map(str.strip, lines[i].split(':', 1)))
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
        f.write('CPA version: %s\n'%(display_version))
        f.write('\n')
        for plot in self.get_plots():
            f.write('%s\n'%(plot.tool_name))
            for setting, value in list(plot.save_settings().items()):
                assert ':' not in setting
                f.write('\t%s : %s\n'%(setting, str(value)))
            f.write('\n')
        f.close()


if __name__ == "__main__":    
    # Initialize the app early because the fancy exception handler
    # depends on it in order to show a 
    app = CPAnalyst(redirect=False)
    # Install our own pretty exception handler unless one has already
    # been installed (e.g., a debugger)
    if sys.excepthook == sys.__excepthook__:
       from cpa.errors import show_exception_as_dialog
       sys.excepthook = show_exception_as_dialog
    app.Start()
    app.MainLoop()
    os._exit(0) # Enforces Exit, see issue #102
