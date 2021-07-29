# A dimensionality reduction tool put together as a standard CPA module and modernised with sklearn.
# Based on an earlier prototype developed at the Intelligent Systems Dept.,
# Radboud Universiteit Nijmegen as part of the CellProfiler project


import ctypes
import threading
from io import StringIO
from contextlib import redirect_stdout

import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA as skPCA
from sklearn.manifold import TSNE as skTSNE

from cpa.classifier import Classifier
from .cpatool import CPATool
from . import tableviewer
from .dbconnect import DBConnect, image_key_columns, object_key_columns
from . import sqltools as sql
from .properties import Properties
from wx.adv import OwnerDrawnComboBox as ComboBox
from . import guiutils as ui
from .gating import GatingHelper
from . import imagetools
from cpa.icons import get_icon
import logging
import numpy as np
import sys
from time import time
import wx
from matplotlib.widgets import LassoSelector
from matplotlib.pyplot import cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.backend_bases import MouseButton, NavigationToolbar2
from matplotlib.path import Path

p = Properties()
db = DBConnect()

object_filter_cache = {}

PCA = 'PCA: Principal Component Analysis'
SVD = 'SVD: Singular Value Decomposition'
GRP = 'GRP: Gaussian Random Projection'
SRP = 'SRP: Sparse Random Projection'
FA = "FA: Factor Analysis"
FAGG = 'FAgg: Feature Agglomeration'
TSNE = 't-SNE: t-Distributed Stochastic Neighbor Embedding'

STAT_NAMES = {
    PCA: "PC",
    SVD: "PC",
    GRP: "GRP",
    SRP: "SRP",
    FA: "Factor_",
    FAGG: "Cluster_",
    TSNE: "tSNE_",
}

PCA_TABLE = "pca_table"


class DimensionReduction(wx.Frame, CPATool):
    '''
    A dimension reduction plot with controls for choosing methods and components.
    '''

    def __init__(self, parent, size=(600, 600), loadData=True, **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Dimensionality Reduction Plot', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        self.SetBackgroundColour("white")
        self.hoverlabel = None

        if not p.is_initialized():
            logging.critical('This tool requires a properties file. Exiting.')
            raise Exception('This tool requires a properties file. Exiting.')

        global classifier
        classifier = parent

        figpanel = ReduxPanel(self)
        self.fig = figpanel
        sizer = wx.BoxSizer(wx.VERTICAL)
        # MacOS won't render an MPL navbar set as a frame toolbar for some reason. Let's add it to the panel instead.
        if sys.platform == 'darwin':
            tb = figpanel.get_toolbar()
            tb.hoverlabel.Hide()
            tb.hoverlabel.Show()
            sizer.Add(tb, 0, wx.EXPAND)
        else:
            self.SetToolBar(figpanel.get_toolbar())
        sizer.Add(figpanel, 1, wx.EXPAND)

        configpanel = ReduxControlPanel(self, figpanel)
        figpanel.set_configpanel(configpanel)
        sizer.Add(configpanel, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)
        #
        # Forward save and load settings functionality to the configpanel
        #
        self.save_settings = configpanel.save_settings
        self.load_settings = configpanel.load_settings

    def configure_subplots(self, *args):
        # Fixed MPL subplot window generator
        from matplotlib.backends.backend_wx import _set_frame_icon, FigureManagerWx
        from matplotlib.widgets import SubplotTool

        frame = wx.Frame(None, -1, "Configure subplots")
        _set_frame_icon(frame)

        toolfig = Figure((6, 3))
        canvas = FigureCanvasWxAgg(frame, -1, toolfig)

        # Create a figure manager to manage things
        FigureManagerWx(canvas, 1, frame)

        # Now put all into a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        frame.SetSizer(sizer)
        frame.Fit()
        SubplotTool(self.fig.canvas.figure, toolfig)
        frame.Show()


class ReduxPanel(FigureCanvasWxAgg):
    '''
    Contains the guts for drawing scatter plots.
    '''

    def __init__(self, parent, **kwargs):
        self.figure = Figure()
        FigureCanvasWxAgg.__init__(self, parent, -1, self.figure, **kwargs)

        self.parent = parent
        self.canvas = self.figure.canvas
        self.SetMinSize((100, 100))
        self.figure.set_facecolor((1, 1, 1))
        self.figure.set_edgecolor((1, 1, 1))
        self.canvas.SetBackgroundColour('white')
        self.navtoolbar = None
        self.subplot = self.figure.add_subplot(111)
        self.gate_helper = GatingHelper(self.subplot, self)

        # Track whether we have any results displayed or plots made
        self.calculated = None
        self.displayed = None
        # Whether to try to update the status bar on plot hover
        self.motion_event_active = False
        # List of data columns we want available for plotting. Usually just PCA components.
        self.pc_cols = []
        # Current displayed columns
        self.x_var = None
        self.y_var = None

        # Full data table and ket table from object set
        self.data = None
        self.keys = None

        # PCA results tables from the current analysis
        self.Scores = None
        self.Loadings = None

        # Results data table currently shown on the plots, post-filtering
        self.current_data = None

        # Per-object class data from the classifier module, if found in database
        self.class_table = None

        self.legend = None

        # Lasso drawing vars
        self.selection = set()
        self.lasso = None
        self.patches = []

        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.update_status_bar)
        self.canvas.mpl_connect('draw_event', self.on_draw)

    def update_status_bar(self, event):
        '''
        Show the key for the nearest object (measured as the Euclidean distance) to the mouse pointer in the
        plot (scores pdimensredux.PlotPanel.__init__dimensredux.PlotPanel.__init__lot) or the nearest feature
        (loadings plot)
        '''
        if event.inaxes and self.motion_event_active:
            lab = self.navtoolbar.hoverlabel
            evt_x, evt_y = event.xdata, event.ydata
            dist = np.hypot((evt_x - self.current_data[self.x_var]), (evt_y - self.current_data[self.y_var]))
            min_dist = np.amin(dist)
            scaled_dist = min_dist / np.amax(dist)
            if scaled_dist > 0.015:
                lab.SetLabel("")
                return

            if self.displayed == "Scores":
                object_idx = np.where(dist == min_dist)[0]
                xy_key = tuple(self.current_data.iloc[object_idx][[p.image_id, p.object_id]].values[0])
                lab.SetLabel("Object: " + str(xy_key))
            elif self.displayed == "Loadings":
                feature_idx = np.where(dist == min_dist)[0][0]
                lab.SetLabel("Feature: " + self.Loadings["Feature_Name"].tolist()[feature_idx])

    def calculate(self, mode, dlg):
        '''
        Generates models and stores transformed data.
        mode - text string representing the desired model
        dlg - wx.ProgressDialog instance for displaying progress
        '''
        # Scale data
        dlg.Pulse("Scaling data")
        sc = StandardScaler(with_mean=mode!=SVD)
        standardized = sc.fit_transform(self.data)
        dlg.Pulse("Fitting model")
        if mode == PCA:
            model = skPCA(n_components=10)
        elif mode == SVD:
            model = TruncatedSVD(n_components=10)
        elif mode == GRP:
            from sklearn.random_projection import GaussianRandomProjection
            model = GaussianRandomProjection(n_components=10)
        elif mode == SRP:
            from sklearn.random_projection import SparseRandomProjection
            model = SparseRandomProjection(n_components=10)
        elif mode == FA:
            from sklearn.decomposition import FactorAnalysis
            model = FactorAnalysis(n_components=10)
        elif mode == FAGG:
            from sklearn.cluster import FeatureAgglomeration
            model = FeatureAgglomeration(n_clusters=10)
        elif mode == TSNE:
            model = skTSNE(perplexity=25.0, verbose=9)
        else:
            raise NotImplementedError("Mode", mode, "is not implemented yet")
        if mode == TSNE:
            # t-SNE takes a long time, we want to be able to update the dialog.
            result_container = []
            th = threading.Thread(target=self.calculate_tsne, args=(model, standardized, result_container))

            # Capture and display the progress statements from sklearn, since sklearn can't take a callback function.
            temp_stdout = StringIO()
            with redirect_stdout(temp_stdout):
                th.daemon = True
                th.start()
                last = 0
                while th.is_alive() and not dlg.WasCancelled():
                    if last != temp_stdout.tell():
                        temp_stdout.seek(last)
                        data = temp_stdout.read().replace('\n', '')
                        dlg.Pulse(data)
                        logging.info(data)
                        last = temp_stdout.tell()
                    wx.Yield()
                if dlg.WasCancelled():
                    # Manually trigger an exception on the worker thread
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_long(th.ident),
                        ctypes.py_object(CancelledException))
                th.join()
            if result_container:
                results = result_container[0]
            else:
                logging.error("t-SNE Failed to complete.")
                return
        else:
            results = model.fit_transform(standardized)
        if mode == FAGG:
            self.pc_cols = [f"{STAT_NAMES[mode]}{x + 1}" for x in range(model.n_clusters_)]
        else:
            self.pc_cols = [f"{STAT_NAMES[mode]}{x + 1}" for x in range(model.n_components)]

        dlg.Pulse("Processing model results")

        scores = pd.DataFrame(self.keys, columns=[p.image_id, p.object_id])
        scores[self.pc_cols] = results
        if mode in (PCA, SVD, GRP):
            loadings = pd.DataFrame(self.data.columns.tolist(), columns=["Feature_Name"])
            loadings[self.pc_cols] = model.components_.transpose()
        else:
            loadings = None
        if hasattr(model, "explained_variance_ratio_"):
            self.axes = dict(zip(self.pc_cols, model.explained_variance_ratio_))
        else:
            self.axes = None
        self.Loadings = loadings

        if p.class_table is not None:
            if self.class_table is None and db.table_exists(p.class_table):
                # Get the class table and store it
                self.class_table = self.get_class_table()
            if self.class_table is not None:
                try:
                    scores = scores.merge(self.class_table, on=[p.image_id, p.object_id])
                except:
                    # Class table wasn't valid for some reason (user changed classifier mode?).
                    logging.error("Class table could not be applied")
                    self.class_table = None
        self.Scores = scores

        # Add class PCA table to database
        connID = threading.currentThread().getName()
        if connID not in db.connections:
            db.connect()
        conn = db.connections[connID]
        dlg.Pulse("Writing to database")
        if p.db_type.lower() == "sqlite":
            scores.to_sql(PCA_TABLE, conn, if_exists="replace", index=False)
        else:
            # MySQLClient not supported by pandas to_sql.
            csvbuffer = StringIO()
            scores.to_csv(csvbuffer, index=False)
            csvbuffer.seek(0)
            db.CreateTempTableFromCSV(csvbuffer, PCA_TABLE)
        if not db.get_linking_tables(p.image_table, PCA_TABLE):
            db.do_link_tables(p.image_table, PCA_TABLE, image_key_columns(), image_key_columns())
        if not db.get_linking_tables(p.object_table, PCA_TABLE):
            db.do_link_tables(p.object_table, PCA_TABLE, object_key_columns(), object_key_columns())
        dlg.Pulse("Writing complete")
        self.calculated = mode

    def calculate_tsne(self, model, data, container):
        try:
            container.append(model.fit_transform(data))
        except CancelledException:
            logging.warn("User canceled t-SNE")
        except Exception as e:
            logging.error(f"t-SNE Failed: {e}")
        return container

    def plot_redux(self, type="Scores", x="PC1", y="PC2", legend=False):
        '''
        Plot the Truncated SVD distribution of the data
        '''
        if type == "Scores":
            data = self.Scores
            def_colour = "blue"
            filter = self.configpanel.filter_choice.get_filter_or_none()
            if filter:
                if filter not in object_filter_cache:
                    object_filter_cache[filter] = db.GetFilteredObjects(filter, random=False)
                obs = object_filter_cache[filter]
                data = data.assign(key_col=list(zip(data[p.image_id].values, data[p.object_id].values)))
                data = data[data.key_col.isin(obs)]
        else:
            data = self.Loadings
            def_colour = "red"
        self.current_data = data
        self.subplot.clear()
        self.x_var = x
        self.y_var = y

        if type == "Loadings" or self.class_table is None:
            self.subplot.scatter(data[x], data[y], s=8, color=def_colour,
                                 linewidth=0.25, alpha=0.5)
        else:
            handles = []
            labels = []
            cmap = cm.get_cmap("brg")
            classnames = pd.unique(data["class"])
            for classname in classnames:
                subset = data[data["class"] == classname]
                num = subset["class_number"].values[0]
                coln = num / len(classnames)
                colmap = [coln] * len(subset)
                handle = self.subplot.scatter(subset[x], subset[y], s=8, color=cmap(num / len(classnames)),
                                              linewidth=0.25, alpha=0.5)
                handles.append(handle)
                labels.append(f"{classname}: {len(subset)}")
            if legend:
                self.leg = self.subplot.legend(handles, labels, loc=4, fancybox=True, handlelength=1)
                self.leg.get_frame().set_alpha(0.25)

        # Construct the legend and make up the rest of the plot
        if self.axes is not None:
            x_var = round((self.axes[x] * 100), 2)
            y_var = round((self.axes[y] * 100), 2)
            x = f'{x} - Explained variance: {x_var}%'
            y = f'{y} - Explained variance: {y_var}%'
        self.subplot.set_xlabel(x, fontsize=12)
        self.subplot.set_ylabel(y, fontsize=12)
        self.subplot.axhline(0, -100000, 100000, c='k', lw=0.1)
        self.subplot.axvline(0, -100000, 100000, c='k', lw=0.1)
        self.figure.tight_layout()
        self.figure.canvas.draw()
        self.motion_event_active = True

    def get_class_table(self):
        '''
        Create class masks for the data based on the classification data from CPAnalyst.
        This is done in order to print Scoring plots with points in different colors
        for each class
        '''
        class_data = db.execute(f'SELECT * FROM {p.class_table}')
        return pd.DataFrame(class_data, columns=db.GetResultColumnNames())

    def set_configpanel(self, configpanel):
        '''Allow access of the control panel from the plotting panel'''
        self.configpanel = configpanel

    def selection_is_empty(self):
        return len(self.selection) == 0

    def lasso_callback(self, verts):
        # Note: If the mouse is released outside of the canvas, (None,None) is
        #   returned as the last coordinate pair.
        # Cancel selection if user releases outside the canvas.
        if self.displayed != "Scores": return
        if verts is None or None in verts[-1]: return
        # Build the selection
        if self.current_data is not None:
            points = self.current_data[[self.x_var, self.y_var]].values
            selected = self.current_data.loc[Path(verts).contains_points(points), [p.image_id, p.object_id]].values
            new_sel = set([tuple(key) for key in selected])
        else:
            new_sel = set()
        if wx.GetKeyState(wx.WXK_SHIFT):
            self.selection = self.selection.union(new_sel)
        else:
            # Clear previous lasso
            self.patches.clear()
            self.selection = new_sel
        logging.info('Selected %s points.' % len(self.selection))
        self.patches.append(self.get_lasso_patch(verts))

    def on_lasso_activate(self, evt=None, force_disable=False):
        if self.lasso or force_disable:
            if self.lasso:
                self.canvas.widgetlock.release(self.lasso)
            self.lasso = None
            self.selection = set()
        else:
            self.navtoolbar.untoggle_mpl_tools()
            if self.displayed == "Scores":
                self.lasso = LassoSelector(self.subplot, self.lasso_callback, button=MouseButton(1))
                self.canvas.widgetlock(self.lasso)
            else:
                self.navtoolbar.ToggleTool(self.navtoolbar.lasso_tool.GetId(), False)

    def get_lasso_patch(self, verts):
        '''Returns a matplotlib patch to be drawn on the canvas whose dimensions
        have been computed from the current gate.
        '''
        x_min, x_max = self.subplot.get_xlim()
        x_range = x_max - x_min
        y_min, y_max = self.subplot.get_ylim()
        y_range = y_max - y_min

        from matplotlib.patches import Polygon
        poly = Polygon(verts, animated=True)
        poly.set_fill(False)
        poly.set_linestyle('dashed')
        poly.set_edgecolor('dimgrey')
        return self.subplot.add_patch(poly)

    def on_draw(self, evt):
        for patch in self.patches:
            self.subplot.draw_artist(patch)

    def on_release(self, evt):
        # Note: lasso_callback is not called on click without drag so we release
        #   the lock here to handle this case as well.
        if evt.button == 1:
            if self.lasso:
                self.canvas.draw_idle()

        elif evt.button == 3:  # right click
            self.show_popup_menu((evt.x, self.canvas.GetSize()[1] - evt.y), None)

    def show_objects_from_selection(self, evt=None):
        '''Callback for "Show objects in selection" popup item.'''
        show_keys = self.selection

        if len(show_keys) > 100:
            te = wx.TextEntryDialog(self,
                                    message=f'You have selected {len(show_keys)} {p.object_name[1]}. '
                                            f'How many would you like to show at random?',
                                    caption=f'Choose # of {p.object_name[1]}',
                                    value='100'
                                    )
            te.ShowModal()
            try:
                res = int(te.Value)
                show_keys = list(show_keys)
                np.random.shuffle(show_keys)
                show_keys = show_keys[:res]
            except ValueError:
                wx.MessageDialog(self, 'You have entered an invalid number', 'Error').ShowModal()
                return
        from . import sortbin
        f = sortbin.CellMontageFrame(None)
        f.Show()
        f.add_objects(show_keys)

    def send_selected_objects_to_classifier(self, evt=None):
        '''Callback for "Show objects in selection" popup item.'''
        keys = self.selection
        classifier = next(win for win in wx.GetTopLevelWindows() if isinstance(win, Classifier))
        if not classifier:
            return
        if len(keys) > 100:
            te = wx.TextEntryDialog(self,
                                    message=f'You have selected {len(keys)} {p.object_name[1]}.'
                                            f'How many would you like to send at random?',
                                    caption=f'Choose # of {p.object_name[1]}',
                                    value='100'
                                    )
            te.ShowModal()
            try:
                res = int(te.Value)
                keys = list(keys)
                np.random.shuffle(keys)
                keys = keys[:res]
            except ValueError:
                wx.MessageDialog(self, 'You have entered an invalid number', 'Error').ShowModal()
                return
        classifier.unclassifiedBin.AddObjects(keys, classifier.chMap, pos='last',
                                              display_whole_image=p.classification_type == 'image')

    def show_objects_from_gate(self, evt=None):
        '''Callback for "Show objects in gate" popup item.'''
        gatename = self.configpanel.gate_choice.get_gatename_or_none()
        if gatename:
            ui.show_objects_from_gate(gatename)

    def show_images_from_gate(self, evt=None):
        '''Callback for "Show images in gate" popup item.'''
        gatename = self.configpanel.gate_choice.get_gatename_or_none()
        if gatename:
            ui.show_images_from_gate(gatename)

    def show_images_from_selection(self, evt=None):
        '''Callback for "Show images in selection" popup item.'''
        show_keys = set([(i,) for i, _ in self.selection])
        if len(show_keys) > 10:
            dlg = wx.MessageDialog(self, 'You are about to open %s images. '
                                         'This may take some time depending on your '
                                         'settings. Continue?' % (len(show_keys)),
                                   'Warning', wx.YES_NO | wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response != wx.ID_YES:
                return
        logging.info('Opening %s images.' % (len(show_keys)))
        for key in sorted(show_keys):
            if len(key) == len(image_key_columns()):
                imagetools.ShowImage(key, p.image_channel_colors, parent=self)
            else:
                imview = imagetools.ShowImage(key[:-1], p.image_channel_colors, parent=self)
                imview.SelectObject(key)

    def show_selection_in_table(self, evt=None):
        '''Callback for "Show selection in a table" popup item.'''
        if len(self.selection) == 0:
            logging.info('No points were selected by the lasso tool')
            return
        indexer = list(map(lambda x: x in self.selection, zip(self.keys[p.image_id], self.keys[p.object_id])))
        table = pd.concat((self.keys[indexer], self.data[indexer]), axis=1).sort_values([p.image_id, p.object_id])
        grid = tableviewer.TableViewer(self, title='Objects from lasso selection')
        grid.table_from_array(table.to_numpy(dtype=str), table.columns.tolist())
        grid.set_auto_col_widths()
        grid.Show()

    def show_popup_menu(self, points, data):
        (x, y) = points
        popup = wx.Menu()

        selected_gate = self.configpanel.gate_choice.get_gatename_or_none()
        selected_gates = []
        if selected_gate:
            selected_gates = [selected_gate]

        show_images_in_gate_item = popup.Append(-1, 'Show images in gate')
        show_images_in_gate_item.Enable(selected_gate is not None)
        self.Bind(wx.EVT_MENU, self.show_images_from_gate, show_images_in_gate_item)
        if p.object_table:
            show_objects_in_gate_item = popup.Append(-1, 'Show %s in gate (montage)' % (p.object_name[1]))
            show_objects_in_gate_item.Enable(selected_gate is not None)
            self.Bind(wx.EVT_MENU, self.show_objects_from_gate, show_objects_in_gate_item)

        popup.AppendSeparator()

        show_images_item = popup.Append(-1, 'View images from selection')
        show_images_item.Enable(not self.selection_is_empty())
        self.Bind(wx.EVT_MENU, self.show_images_from_selection, show_images_item)

        if p.object_table:
            show_objects_item = popup.Append(-1, 'Show %s in selection' % (p.object_name[1]))
            if self.selection_is_empty():
                show_objects_item.Enable(False)
            self.Bind(wx.EVT_MENU, self.show_objects_from_selection, show_objects_item)

        if any(isinstance(x, Classifier) for x in wx.GetTopLevelWindows()):
            send_objects_item = popup.Append(-1, 'Send %s to classifier' % (p.object_name[1]))
            if self.selection_is_empty():
                send_objects_item.Enable(False)
            self.Bind(wx.EVT_MENU, self.send_selected_objects_to_classifier, send_objects_item)

        show_imagelist_item = popup.Append(-1, 'Show selection in table')
        if self.selection_is_empty():
            show_imagelist_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.show_selection_in_table, show_imagelist_item)

        self.PopupMenu(popup, (x, y))

    def get_toolbar(self):
        if not self.navtoolbar:
            self.navtoolbar = CustomNavToolbar(self.canvas)
            self.navtoolbar.Realize()
            self.navtoolbar.Bind(wx.EVT_TOOL, self.on_lasso_activate, source=self.navtoolbar.lasso_tool)
        return self.navtoolbar


class ReduxControlPanel(wx.Panel):
    '''
    A panel with controls for selecting the source data
    '''

    def __init__(self, parent, figpanel, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)

        # the panel to draw charts on
        self.figpanel = figpanel
        self.SetBackgroundColour('white')  # color for the background of panel

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.method_choice = ComboBox(self, -1, choices=[PCA, SVD, GRP, SRP, FA, FAGG, TSNE], size=(200, -1),
                                      style=wx.CB_READONLY)
        self.method_choice.Select(0)
        self.plot_choice = ComboBox(self, -1, choices=["Scores", "Loadings"], size=(80, -1), style=wx.CB_READONLY)
        self.plot_choice.Select(0)
        self.x_choice = ComboBox(self, -1, choices=[''], size=(100, -1), style=wx.CB_READONLY)
        self.x_choice.Select(0)
        self.y_choice = ComboBox(self, -1, choices=[''], size=(100, -1), style=wx.CB_READONLY)
        self.y_choice.Select(0)
        self.display_legend = wx.CheckBox(self, -1, label="Show Legend", size=(200, -1))
        self.display_legend.SetValue(True)
        self.filter_choice = ui.FilterComboBox(self, style=wx.CB_READONLY)
        self.filter_choice.Select(0)
        self.gate_choice = ui.GateComboBox(self, style=wx.CB_READONLY)
        # self.gate_choice.set_gatable_columns([self.x_column, self.y_column])
        self.update_chart_btn = wx.Button(self, -1, "Update Chart")

        self.update_col_choices(clear=True)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Method:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.method_choice, 2, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(wx.StaticText(self, -1, "Display:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.plot_choice)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 2, 0)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddSpacer(11)
        sz.Add(wx.StaticText(self, -1, "x-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.x_choice, 2, wx.EXPAND)
        sz.AddSpacer(6)
        sz.Add(wx.StaticText(self, -1, "y-axis:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.y_choice, 2, wx.EXPAND)
        sz.AddSpacer(10)
        sz.Add(self.display_legend, 2, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 2, 0)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddSpacer(18)

        sz.Add(wx.StaticText(self, -1, "filter:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.filter_choice, 1, wx.EXPAND)
        sz.AddSpacer(3)
        sz.Add(wx.StaticText(self, -1, "gate:"), 0, wx.TOP, 4)
        sz.AddSpacer(3)
        sz.Add(self.gate_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.Add(-1, 2, 0)

        sizer.Add(self.update_chart_btn)

        self.gate_choice.addobserver(self.on_gate_selected)
        self.method_choice.Bind(wx.EVT_COMBOBOX, self.update_plot_choices)
        self.update_chart_btn.Bind(wx.EVT_BUTTON, self.update_figpanel)

        self.SetSizer(sizer)
        self.Show(1)

    @property
    def x_column(self):
        return sql.Column(PCA_TABLE,
                          self.x_choice.Value)

    @property
    def y_column(self):
        return sql.Column(PCA_TABLE,
                          self.y_choice.Value)

    @property
    def filter(self):
        return self.filter_choice.get_filter_or_none()

    def on_gate_selected(self, gate_name):
        self.update_gate_helper()

    def update_gate_helper(self):
        gate_name = self.gate_choice.get_gatename_or_none()
        if gate_name:
            # Deactivate the lasso tool
            self.figpanel.navtoolbar.ToggleTool(self.figpanel.navtoolbar.lasso_tool.GetId(), False)
            self.figpanel.on_lasso_activate(force_disable=True)
            self.figpanel.gate_helper.set_displayed_gate(p.gates[gate_name], self.x_column, self.y_column)
        else:
            self.figpanel.gate_helper.disable()

    def update_col_choices(self, clear=False):
        fieldnames = self.figpanel.pc_cols
        self.x_choice.Clear()
        self.y_choice.Clear()
        if len(fieldnames) == 0:
            self.x_choice.Enable(False)
            self.y_choice.Enable(False)
            return
        self.x_choice.Enable(True)
        self.y_choice.Enable(True)
        self.x_choice.AppendItems(fieldnames)
        self.y_choice.AppendItems(fieldnames)
        self.x_choice.SetSelection(0)
        self.y_choice.SetSelection(1)

    def _plotting_per_object_data(self):
        return (p.object_table is not None and
                p.object_table in [self.x_column.table, self.y_column.table]
                or (self.x_column.table != p.image_table and db.adjacent(p.object_table, self.x_column.table))
                or (self.y_column.table != p.image_table and db.adjacent(p.object_table, self.y_column.table))
                )

    def load_obj_measurements(self):
        '''
        Load all cell measurements from the DB into a Numpy array and a dictionary
        The dictionary links each object to its key to show it when the mouse is on
        its dot representation in the plot.
        '''
        self.filter_col_names(p.object_table)
        data = db.GetCellDataForRedux()
        data = np.nan_to_num(data.astype(float))
        cols = [p.image_id, p.object_id] + db.GetColnamesForClassifier()
        return pd.DataFrame(data, columns=cols)

    def filter_col_names(self, table):
        '''
        Add DB non-measurement column names to the 'ignore colums' list.
        This is performed to avoid using its data for the calculations
        '''
        col_names = db.GetColumnNames(table)
        filter_cols = [p.cell_x_loc, p.cell_y_loc, p.plate_id, p.well_id, p.image_id]
        if not p.classifier_ignore_columns:
            p.classifier_ignore_columns = []
        [p.classifier_ignore_columns.append(column) for column in filter_cols if column in col_names]

    def update_figpanel(self, evt=None):

        '''
        Show the selected dimensionality reduction plot on the canvas
        '''

        if self.method_choice.Value == TSNE and self.figpanel.calculated != TSNE:
            dlg = wx.MessageDialog(self, 't-SNE is an intensive method. \n\n Calculations '
                                         'may take several minutes, or even longer when '
                                         'running large datasets. Continue?',
                                   'Warning', wx.YES_NO | wx.ICON_QUESTION)
            response = dlg.ShowModal()
            if response != wx.ID_YES:
                return

        # Define a progress dialog
        dlg = wx.ProgressDialog('Generating figure...', 'Fetching data ...', 100, parent=self,
                                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT)
        try:
            # Reset selections
            self.figpanel.patches = []
            self.figpanel.selection = set()

            if self.figpanel.data is None:
                dlg.Pulse('Fetching object data from database')
                try:
                    # Fetch all data from database
                    data = self.load_obj_measurements()
                    keys, values = np.split(data, [2], axis=1)
                    self.figpanel.keys = keys.astype(int)
                    # Remove zero variance features
                    self.figpanel.data = values.loc[:, (values != values.iloc[0]).any()]
                except Exception as e:
                    self.figpanel.data = None
                    self.figpanel.keys = None
                    logging.error(f"Unable to load data: {e}")
                    dlg.Destroy()
                    return

            start = time()

            dlg.Pulse('Generating model and plot')
            selected_method = self.method_choice.GetStringSelection()
            selected_plot = self.plot_choice.GetStringSelection()

            if self.figpanel.calculated != selected_method:
                # Clear gates made with previous methods.
                for gate_name in list(p.gates.keys()):
                    if PCA_TABLE in p.gates[gate_name].get_tables():
                        p.gates.pop(gate_name)
                        logging.warning(f'Reduction method changed, gate "{gate_name}" was removed.')
                self.figpanel.calculate(selected_method, dlg=dlg)
                if self.figpanel.calculated != selected_method:
                    # Calculation failed for whatever reason
                    dlg.Destroy()
                    return
                self.update_col_choices()
            self.figpanel.navtoolbar.update()

            dlg.Pulse("Plotting results")
            self.figpanel.plot_redux(type=selected_plot, x=self.x_choice.Value, y=self.y_choice.Value,
                                     legend=self.display_legend.Value)
            self.figpanel.displayed = selected_plot
        finally:
            dlg.Destroy()

        print(f"Finished {selected_method} in {time() - start}")
        self.update_gate_helper()

    def update_plot_choices(self, evt):
        if self.method_choice.Value in (PCA, SVD, GRP):
            self.plot_choice.SetItems(["Scores", "Loadings"])
        else:
            self.plot_choice.SetItems(["Scores"])
        self.plot_choice.SetSelection(0)
        evt.Skip()

    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        returns a dictionary mapping setting names to values encoded as strings
        '''
        d = {'method': self.method_choice.Value,
             'plot': self.plot_choice.Value,
             'x-axis': self.x_choice.Value,
             'y-axis': self.y_choice.Value,
             'filter': self.filter_choice.Value,
             'x-lim': self.figpanel.subplot.get_xlim(),
             'y-lim': self.figpanel.subplot.get_ylim(),
             'legend': self.display_legend.Value,
             'version': '1',
             }
        if self.gate_choice.get_gatename_or_none():
            gate_choice_id = self.gate_choice.GetSelection()
            d['gate'] = self.gate_choice.GetString(gate_choice_id)
        return d

    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
        if 'version' not in settings:
            if 'table' in settings:
                settings['x-table'] = settings['table']
                settings['y-table'] = settings['table']
            settings['version'] = '1'
        if 'method' in settings:
            self.method_choice.SetStringSelection(settings['method'])
        if 'plot' in settings:
            self.plot_choice.SetStringSelection(settings['plot'])
        if 'x-axis' in settings:
            self.x_choice.SetStringSelection(settings['x-axis'])
        if 'y-axis' in settings:
            self.y_choice.SetStringSelection(settings['y-axis'])
        if 'filter' in settings:
            self.filter_choice.SetStringSelection(settings['filter'])
        if 'legend' in settings:
            self.display_legend.SetValue(settings['legend'] == "True")
        self.update_figpanel()
        if 'x-lim' in settings:
            self.figpanel.subplot.set_xlim(eval(settings['x-lim']))
        if 'y-lim' in settings:
            self.figpanel.subplot.set_ylim(eval(settings['y-lim']))
        self.figpanel.draw()


class CustomNavToolbar(NavigationToolbar2WxAgg):
    '''wx/mpl NavToolbar with an additional tools user interaction.
    This class is necessary because simply adding a new togglable tool to the
    toolbar won't (1) radio-toggle between the new tool and the pan/zoom tools.
    (2) disable the pan/zoom tool modes in the associated subplot(s).
    '''

    def __init__(self, canvas):
        super(CustomNavToolbar, self).__init__(canvas, coordinates=False)
        self.PAN = self.wx_ids['Pan']
        self.ZOOM = self.wx_ids['Zoom']
        self.CONFIG_SUBPLOTS = self.wx_ids["Subplots"]
        self.pan_tool = self.FindById(self.PAN)
        self.zoom_tool = self.FindById(self.ZOOM)
        self.subplots_tool = self.FindById(self.CONFIG_SUBPLOTS)
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.zoom_tool)
        self.Bind(wx.EVT_TOOL, self.on_toggle_pan_zoom, self.pan_tool)

        # self.add_user_tool('lasso', 6, get_icon("lasso_tool").ConvertToBitmap(), True, 'Lasso')
        # self.add_user_tool('gate', 7, get_icon("gate_tool").ConvertToBitmap(), True, 'Gate')

        self.lasso_tool = self.AddCheckTool(wx.ID_ANY, "", get_icon("lasso").ConvertToBitmap(),
                                            shortHelp='Lasso Select', longHelp='Lasso select')
        self.Bind(wx.EVT_TOOL, self.Parent.configure_subplots, id=self.CONFIG_SUBPLOTS)

        pos = self.GetToolsCount()
        self.hoverlabel = wx.StaticText(self, label="")
        self.InsertControl(pos, self.hoverlabel, "")
        self.AddStretchableSpace()
        self.Realize()

    def untoggle_mpl_tools(self):
        '''Less hacky than it once was: We need to turn off any MPL tools
        when activating a custom tool
        This function needs to be called whenever any user-defined tool
        (eg: lasso) is clicked.
        '''
        if self.pan_tool.IsToggled():
            self.ToggleTool(self.PAN, False)
            NavigationToolbar2.pan(self)
        elif self.zoom_tool.IsToggled():
            self.ToggleTool(self.ZOOM, False)
            NavigationToolbar2.zoom(self)

    def on_toggle_pan_zoom(self, evt):
        '''Called when pan or zoom is toggled.
        We need to manually untoggle user-defined tools.
        '''
        if self.lasso_tool.IsToggled():
            self.Parent.fig.on_lasso_activate(force_disable=True)
            self.ToggleTool(self.lasso_tool.GetId(), False)
        evt.Skip()

    def reset_history(self):
        '''Clear/reset the toolbar history.
        '''
        self._nav_stack.clear()


class CancelledException(BaseException):
    pass


if __name__ == "__main__":
    app = wx.App()
    logging.basicConfig(level=logging.DEBUG, )

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            print('Dimensionality Reduction requires a properties file.  Exiting.')
            # necessary in case other modal dialogs are up
            sys.exit()
    redux = DimensionReduction(None)
    redux.Show()

    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import javabridge

        javabridge.kill_vm()
    except:
        import traceback

        traceback.print_exc()
        print("Caught exception while killing VM")
