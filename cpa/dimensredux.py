#!/usr/bin/env python

# TODO: Add not-classified data functionality, activate url links to 'About'

'''
GUI for visual dimensionality reduction of the data via various methods:

Singular Value Decomposition (Principal Component Analysis)
*A Tutorial on Principal Component Analysis - Jonathon Shlens: 
http://www.snl.salk.edu/~shlens/pca.pdf

t-Distributed Stochastic Neighbor Embedding
* L.J.P. van der Maaten and G.E. Hinton. Visualizing High-Dimensional Data Using t-SNE. 
Journal of Machine Learning Research 9(Nov):2579-2605, 2008. 
http://jmlr.csail.mit.edu/papers/volume9/vandermaaten08a/vandermaaten08a.pdf

By: Juan Escribano Navarro (Intelligent Systems Department, Radboud Universiteit Nijmegen) - 01/05/2010
Modified By: Joris Kraak (Department of Electrical Engineering, Signal Processing Systems Group, Eindhoven University of Technology) - 28-12-2010
'''

import sys
import logging
from operator import itemgetter
import numpy as np
import wx
import wx.aui
from wx.combo import OwnerDrawnComboBox as ComboBox
from matplotlib import cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from imagetools import ShowImage
from dbconnect import DBConnect
from properties import Properties

SVD = 'SVD: Singular Value Decomposition'
TSNE = 't-SNE: t-Distributed Stochastic Neighbor Embedding'
COLORS = ['g', 'r', 'g', 'g', 'g', 'b', 'b', 'b', 'darkorange', 'greenyellow', 'darkorchid', 'aqua', 'deeppink', 'sienna', 'bisque', 'cornflowerblue', 'goldenrod', 'indigo', 'gray', 'olive', 'steelblue']

class PlotPanel(wx.Panel):
    '''
    Principal Component Analysis (PCA) plot (PCA1 against PCA2) GUI
    '''
    def __init__(self, parent, id= -1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.figure = Figure(dpi=dpi, figsize=(2, 2))
        self.canvas = Canvas(self, -1, self.figure)
        self.figure.set_facecolor((1, 1, 1))
        self.figure.set_edgecolor((1, 1, 1))
        self.canvas.SetBackgroundColour('white')
        self.subplot = self.figure.add_subplot(111)
        self.plot_scores = None
        self.class_masks = None
        self.class_names = None
        self.Loadings = None
        self.object_opacity = None
        self.object_accuracies = None
        self.leg = None
        self.maskedPCA1 = None
        self.maskedPCA2 = None
        self.axes = None

        # If the script is loaded from ClassifierGUI, load the classification weaklearners
        try:
            self.classifier = classifier
            self.classifier_rules = classifier.algorithm.weak_learners
        except: 
            self.classifier_rules = [('None', 0, np.array([0, 0]))]

        self.chMap = p.image_channel_colors
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 6
        self.toolbar.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)

        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(1)
        self.motion_event_active = False
        self.canvas.mpl_connect('motion_notify_event', self.update_status_bar)
        self.canvas.mpl_connect('button_press_event', self.on_open_image)

        self.hide_legend_btn = wx.Button(self, -1, " Hide legend ")
        wx.EVT_BUTTON(self.hide_legend_btn, -1, self.hide_show_legend)
        self.hide_legend = True

        tools_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tools_sizer.Add(self.toolbar, 0, wx.RIGHT | wx.EXPAND)
        tools_sizer.AddSpacer((5, -1))
        tools_sizer.Add(self.hide_legend_btn, 0, wx.LEFT | wx.EXPAND)    
        tools_sizer.AddSpacer((5, -1))
        tools_sizer.Add(self.statusBar, 0, wx.LEFT | wx.EXPAND)    

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(tools_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)    

    def set_plot_type(self, plot_scores):
        '''
        Set the plot type (Scores. Loadings) for each notebook page
        '''
        self.plot_scores = plot_scores

    def set_colormap(self, class_array):
        '''
        Set the colormap based on the number of different classes to plot
        '''
        self.colormap = cm.get_cmap('hsv')
        num_colors = len(class_array)
        class_value = np.array(xrange(1, (num_colors + 2)), dtype='float') / num_colors
        color_set = np.array(self.colormap(class_value))
        return color_set

    def on_open_image(self, event):
        if event.button == 2 and self.plot_scores == "Scores" and event.inaxes:
            self.open_image()

    def open_image(self):
        '''
        Open the image of the selected cell in the Scores plot
        '''
        imViewer = ShowImage(self.actual_key[:-1], self.chMap[:],
                             parent=self.classifier, brightness=1.0,
                             contrast=None)
        imViewer.imagePanel.SelectPoint(db.GetObjectCoords(self.actual_key))

    def hide_show_legend(self, event):
        '''
        Hide or show the legend on the canvas by pressing the button
        '''
        if self.leg is not None:
            if self.hide_legend:
                self.leg.set_visible(False)
                self.figure.canvas.draw()
                self.hide_legend = False
                self.hide_legend_btn.SetLabel(label='Show legend')
            else:
                self.leg.set_visible(True)
                self.figure.canvas.draw()
                self.hide_legend = True
                self.hide_legend_btn.SetLabel(label=' Hide legend ')

    def update_status_bar(self, event):
        '''
        Show the key for the nearest object (measured as the Euclidean distance) to the mouse pointer in the 
        plot (scores pdimensredux.PlotPanel.__init__dimensredux.PlotPanel.__init__lot) or the nearest feature 
        (loadings plot)
        '''
        if event.inaxes and self.motion_event_active:
            x, y = event.xdata, event.ydata
            if self.plot_scores == "Scores":
                dist = np.hypot((x - self.Scores[:, 0]), (y - self.Scores[:, 1]))
                object_dict_key = np.where(dist == np.amin(dist))
                xy_key = int(object_dict_key[0][0])
                if self.object_accuracies:
                    errorData = ', CA = %0.1f%%' % ((1-self.object_opacity[xy_key])*100.0)
                else:
                    errorData = ''
                self.statusBar.SetStatusText(("Object key = " + str(self.data_dic[xy_key]) + errorData), 0)
                self.actual_key = self.data_dic[xy_key]
            elif self.plot_scores == "Loadings":
                dist = np.hypot((x - self.Loadings[0]), (y - self.Loadings[1]))
                feature_dict_key = np.where(dist == np.amin(dist))
                xy_key = int(feature_dict_key[0])
                feat_text = self.features_dic[xy_key].split('_')
                self.statusBar.SetStatusText(('_'.join(feat_text[1:])), 0)

    def plot_pca(self):
        '''
        Plot the Principal Component Analysis scores (cells) and loadings (features)
        along with the percentage of data variance the scores represent
        '''
        self.subplot.clear()
        # Only obtain class data from the database if no data is available yet
        if self.class_masks is None or self.class_names is None:
            self.class_masks, self.class_names = self.create_class_masks()
        self.data = np.nan_to_num(self.data) # Eliminate NaNs

        # Calculate PCA-SVD and mask data with class information
        centered = self.mean_center(self.data)
        U, S, self.Loadings, explained_variance = self.pca_svd(centered, 100, True)
        self.Scores = np.array(U[:, 0:2])
        self.maskedPCA1, self.maskedPCA2 = self.mask_data(len(self.class_names),
                                                          self.class_masks, self.Scores)
        self.axes = explained_variance[0:2]
        self.color_set = self.set_colormap(self.class_names)

        # Plot the first two PCAs' Scores in the Scores canvas
        if self.plot_scores == "Scores":
            handles = []
            labels = []

            # Determine the different opacities for the objects. This is set to 1 if no opacities have been specified.
            if self.object_opacity is None:
                self.object_opacity = np.ones([self.maskedPCA1.shape[0], 1])
                self.object_accuracies = False
            elif self.object_accuracies is None:
                self.object_accuracies = True
            opacities = np.unique(self.object_opacity)
            nOpacity = len(opacities)
            
            # For each class and opacity combination plot the corresponding objects
            for i in xrange(len(self.class_names)):
                cell_count = np.shape(np.nonzero(self.maskedPCA1[:, i]))
                for j in xrange(nOpacity):
                    showObjects = np.where(self.object_opacity == opacities[j])
                    subHandle = self.subplot.scatter(self.maskedPCA1[showObjects[0], i], self.maskedPCA2[showObjects[0], i], 8, c=self.color_set[i, :], linewidth="0.25", alpha=0.25+0.75*opacities[j])

                    # The highest opacity objects are added to the legend
                    if opacities[j] == np.max(opacities):
                        handles.append(subHandle)
                        labels.append(self.class_names[i] + ': ' + str(cell_count[1]))

            # Construct the legend and make up the rest of the plot
            self.leg = self.subplot.legend(handles, labels, loc=4, fancybox=True, handlelength=1)
            self.leg.get_frame().set_alpha(0.25)
            x_var = round(((1 - self.axes[0]) * 100), 2)
            y_var = round(((self.axes[0] - self.axes[1]) * 100), 2)
            x_axe_var = 'Explained variance: ' + str(x_var) + '%'
            y_axe_var = 'Explained variance: ' + str(y_var) + '%'
            self.subplot.set_xlabel(x_axe_var, fontsize=12)
            self.subplot.set_ylabel(y_axe_var, fontsize=12)
            self.subplot.axhline(0, -100000, 100000, c='k', lw=0.1)
            self.subplot.axvline(0, -100000, 100000, c='k', lw=0.1)
            self.figure.canvas.draw()
        elif self.plot_scores == "Loadings":
            # Plot the first two PCAs' Loadings in the Loading canvas
            weaklearners_mask = np.zeros((np.shape(self.Loadings[0])))
            for key in self.features_dic.keys():
                for value in self.classifier_rules:
                    if value[0] == self.features_dic[key]:
                        weaklearners_mask[key] += 1
            scatter_mask = weaklearners_mask + 1
            colors_mask = []
            size_mask = []
            for i in xrange(len(scatter_mask)):
                colors_mask.append(COLORS[int(scatter_mask[i])])
                size_mask.append((int(scatter_mask[i]) ** 2) * 5)

            self.subplot.scatter(self.Loadings[0], self.Loadings[1], c=colors_mask,
                                 s=size_mask, linewidth="0.5", marker='o')
            self.subplot.axhline(0, -100000, 100000, c='k', lw=0.1)
            self.subplot.axvline(0, -100000, 100000, c='k', lw=0.1)
            self.figure.canvas.draw()

        self.motion_event_active = True

    def plot_tsne(self):
        ''' 
        Plot the t-Distributed Stochastic Neighbor Embedding (t-SNE) distribution of the data
        '''
        self.subplot.clear()
        self.data = np.nan_to_num(self.data) # Eliminate NaNs
        centered = self.mean_center(self.data)
        standardized = self.standardization(centered)

        # Calculate t-SNE of the data and mask it (python t-SNE version if Intel IPP is not installed)
        try:
            from calc_tsne import calc_tsne
            U = calc_tsne(standardized, 2, 50, 20.0)
        except:
            logging.warning('''Could not use fast t-SNE. You may need to install the Intel Integrated Performance Libraries. Will use normal t-SNE instead.''')
            try:
                from tsne import tsne
                U = tsne(standardized, 2, 50, 20.0)
            except:
                logging.error('''Both t-SNE versions failed. Your dataset may be too large for t-SNE to handle. Will not plot t-SNE results.''')
                return

        self.Scores = U[:, 0:2]
        if self.class_masks is None or self.class_names is None:
            self.class_masks, self.class_names = self.create_class_masks()
        self.masked_X, self.masked_Y = self.mask_data(len(self.class_names), self.class_masks, self.Scores)

        # Plot the masked t-SNE results in the Scores canvas
        self.color_set = self.set_colormap(self.class_names)
        handles = []
        labels = []

        # Determine the different opacities for the objects. This is set to 1 if no opacities have been specified.
        if self.object_opacity is None:
            self.object_opacity = np.ones([self.masked_X.shape[0], 1])
            self.object_accuracies = False
        elif self.object_accuracies is None:
            self.object_accuracies = True
        opacities = np.unique(self.object_opacity)
        nOpacity = len(opacities)
            
        # For each class and opacity combination plot the corresponding objects
        for i in xrange(len(self.class_names)):
            cell_count = np.shape(np.nonzero(self.masked_X[:, i]))
            for j in xrange(nOpacity):
                showObjects = np.where(self.object_opacity == opacities[j])
                subHandle = self.subplot.scatter(self.masked_X[showObjects, i], self.masked_Y[showObjects, i], 8, c=self.color_set[i, :], linewidth="0.25", alpha=0.25+0.75*opacities[j])
                # The highest opacity objects are added to the legend
                if opacities[j] == np.max(opacities):
                    handles.append(subHandle)
                    labels.append(self.class_names[i] + ': ' + str(cell_count[1]))
        self.leg = self.subplot.legend(handles, labels, loc=4, fancybox=True, handlelength=1)
        self.leg.get_frame().set_alpha(0.25)
        self.subplot.axhline(0, -100000, 100000, c='k', lw=0.1)
        self.subplot.axvline(0, -100000, 100000, c='k', lw=0.1)
        self.figure.canvas.draw()
        self.motion_event_active = True

    def clean_canvas(self):
        self.subplot.clear()

    def standardization(self, centered_data):
        '''
        Standardize data prior to calculation in order to improve 
        the performance over measurements with large differences
        in their value ranges
        '''
        standards = np.std(centered_data, 0)

        for value in standards: 
            if value == 0:
                logging.error('Division by zero, cannot proceed (an object measurements in your dataset has 0 standard deviation, please check your database)')
            standardized_data = centered_data / standards

        return standardized_data

    def mean_center(self, raw_data):
        '''
        Centering the measurements data around the mean is necessary prior to 
        calculation
        '''
        row, col = np.shape(raw_data) 
        centered_data = raw_data
        mean_data = raw_data.mean(axis=0)
        for i in xrange(row):
            centered_data[i] -= mean_data
        centered_data = centered_data[:,np.var(centered_data, axis=0) != 0]
        
        return centered_data

    def pca_svd(self, data, PCs=100, standardize=True):
        '''
        Calculate the eigenvectors of the data array using SVD 
        (Singular Value Decomposition) method
        '''    
        row, col = np.shape(data)
        if PCs > col:
            PCs = col

        if standardize:
            data = self.standardization(data)
        import time
        U, S, V = np.linalg.svd(data, full_matrices=False)

        # Calculate the percentage of data measurements variance each PCA explains
        E = data.copy()
        row, col = np.shape(E)
        explained_variance = np.zeros((PCs)) 
        total_explained_variance = 0 
        init_total_error = np.sum(np.square(E))
        for k in xrange(PCs):
            T = (U[:, k].reshape(row, 1)) * S[k]
            V_t = np.transpose(V)
            P = V_t[:, k].reshape(col, 1)
            E = E - T * (np.transpose(P))
            total_error = np.sum(np.square(E))
            total_object_residual_variance = (total_error / init_total_error) 
            explained_variance[k] = 1 - total_object_residual_variance - total_explained_variance 
            total_explained_variance += explained_variance[k]

        return U, S, V, explained_variance   

    def create_class_masks(self):
        '''
        Create class masks for the data based on the classification data from CPAnalyst.
        This is done in order to print Scoring plots with points in different colors
        for each class
        '''
        class_data = db.execute('SELECT class, class_number FROM %s ' \
                                'ORDER BY %s ASC, %s ASC' % (p.class_table, \
                                                             p.image_id, p.object_id))

        class_name_number = set([result for result in class_data])
        class_name_number = sorted(class_name_number, key=itemgetter(1))
        class_names = [item[0] for item in class_name_number]
        class_number = np.array([result[1] for result in class_data])
        num_classes = len(class_names)

        # In case class numbers are missing in the range (for instance some classes
        # that were available to train objects in have no objects classified in them)
        # the class numbers should be remapped
        class_ids = [item[1] for item in class_name_number]
        max_id = np.max(class_ids)
        if len(class_ids) != max_id:
            logging.info('Found non-consecutive class IDs. Remapping class IDs.')
            missing_ids = np.flipud(np.setdiff1d(np.arange(max_id)+1, class_ids))
            while missing_ids.shape != (0,):
                indices = class_number >= missing_ids[0]
                class_number[indices] -= 1
                missing_ids = np.delete(missing_ids, 0)    

        class_masks = np.zeros((len(class_number), num_classes))
        for i in range(len(class_number)):
            class_col = class_number[i] - 1
            class_masks[i, class_col] = 1

        return class_masks, class_names

    def mask_data(self, num_classes, class_masks, Scores):
        '''
        Mask the Score matrixes using the masks from create_class_mask
        '''
        row = np.size(Scores[:, 0])
        col = num_classes
        masked_data_X = np.zeros((row, col))
        masked_data_Y = np.zeros((row, col))
        for i in xrange(num_classes):
            masked_data_X[:, i] = Scores[:, 0] * class_masks[:, i]
            masked_data_Y[:, i] = Scores[:, 1] * class_masks[:, i]

        return masked_data_X, masked_data_Y

class PlotControl(wx.Panel): 
    '''
    Control panel for the dimensionality reduction analysis
    '''
    def __init__(self, parent, fig_sco, fig_load, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.fig_sco = fig_sco
        self.fig_load = fig_load
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.method_choice = ComboBox(self, -1, choices=[SVD, TSNE], style=wx.CB_READONLY)
        self.method_choice.Select(0)
        self.update_chart_btn = wx.Button(self, -1, "Show plot")
        self.help_btn = wx.Button(self, -1, "About")

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Method:"))
        sz.AddSpacer((5, -1))
        sz.Add(self.method_choice, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1, 5))

        sz2 = wx.BoxSizer(wx.HORIZONTAL)
        sz2.Add(self.help_btn, wx.LEFT)
        sz2.AddSpacer((400, -1))
        sz2.Add(self.update_chart_btn, wx.RIGHT)

        sizer.Add(sz2, 1, wx.EXPAND)
        sizer.AddSpacer((-1, 5))

        wx.EVT_BUTTON(self.update_chart_btn, -1, self.on_show_pressed)
        wx.EVT_BUTTON(self.help_btn, -1, self.on_show_about)    

        self.SetSizer(sizer)
        self.Show(1)

    def on_show_about(self, evt):
        '''
        Shows a message box with the version number etc.
        '''
        message = ('Dimensionality Reduction Plot was developed at the Intelligent Systems Dept., '
                   'Radboud Universiteit Nijmegen as part of the CellProfiler project and is'
                   ' distributed under the GNU General Public License version 2.\n'
                   '\n'
                   'For more information about the dimensionality reduction algorithms check:\n'
                   '\n'
                   '*Singular Value Decomposition: http://www.snl.salk.edu/~shlens/pca.pdf\n'
                   '\n'
                   '*t-SNE: http://homepage.tudelft.nl/19j49/t-SNE.html\n')
        dlg = wx.MessageDialog(self, message, 'CellProfiler Analyst 2.0', style=wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()

    def on_show_pressed(self, evt): 
        '''
        Show the selected dimensionality reduction plot on the canvas      
        '''
        selected_method = self.method_choice.GetStringSelection()

        if selected_method == SVD:
            self.fig_sco.plot_pca()
            self.fig_load.plot_pca()
        elif selected_method == TSNE:
            self.fig_sco.plot_tsne()
            self.fig_load.clean_canvas()

class PlotNotebook(wx.Panel):
    '''
    A simple wx notebook to create different tabs for Scores and Loadings plot
    '''
    def __init__(self, parent, id= -1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = wx.aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def add(self, name):
        page = PlotPanel(self.nb)
        self.nb.AddPage(page, name)
        return page

class StopCalculating:
    pass

class PlotMain(wx.Frame):
    '''
    Dimensionality reduction GUI main frame
    '''
    def __init__(self, parent, properties = None, show_controls = True, size=(600, 600), loadData = True, **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Dimensionality Reduction Plot', **kwargs)
        self.SetName('Plot main')

        if properties is not None:
            global p
            p = properties

            if not p.is_initialized():
                logging.critical('Classifier requires a properties file. Exiting.')
                raise Exception('Classifier requires a properties file. Exiting.')
            global db
            db = DBConnect.getInstance()

        global classifier
        classifier = parent

        if loadData:
            # Define a progress dialog
            dlg = wx.ProgressDialog('Fetching cell data...', '0% Complete', 100, classifier,
                                    wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME |
                                    wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
            def cb(frac):
                cont, skip = dlg.Update(int(frac * 100.), '%d%% Complete'%(frac * 100.))
                if not cont: # cancel was pressed
                    dlg.Destroy()
                    raise StopCalculating()

            # Load the data for each object
            try:
                self.data, self.data_dic = self.load_obj_measurements(cb)
            except StopCalculating:
                self.PostMessage('User canceled updating training set.')
                return
            dlg.Destroy()
        else:
            self.data, self.data_dic = None, None
            
        self.features_dic = self.load_feature_names()
        self.class_masks = None
        self.class_names = None
        self.object_opacity = None

        figpanel = PlotNotebook(self)
        self.figure_scores = figpanel.add('Scores')
        self.figure_loadings = figpanel.add('Loadings')
        self.update_figures()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(figpanel, 1, wx.EXPAND)
                
        configpanel = PlotControl(self, self.figure_scores, self.figure_loadings)
        sizer.Add(configpanel, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        self.Centre()

    def load_obj_measurements(self, cb = None):
        '''
        Load all cell measurements from the DB into a Numpy array and a dictionary
        The dictionary links each object to its key to show it when the mouse is on
        its dot representation in the plot.
        '''
        self.filter_col_names(p.object_table)
         
        all_keys = map(db.GetObjectsFromImage, db.GetAllImageKeys())

        obj_counts = db.GetPerImageObjectCounts()
        total_obj_count = sum(k[1] for k in obj_counts) 

        for key in all_keys:
            if key:
                measurements = len(db.GetCellDataForClassifier(key[0]))
                break

        data = np.zeros((total_obj_count, measurements))
        data_dic = {}
        key_list = [key for image_keys in all_keys for key in image_keys]
        nKeys = float(len(key_list))
        for index, key in enumerate(key_list):
            cb(index / nKeys)
            data[index, :] = db.GetCellDataForClassifier(key)
            data_dic[index] = key

        return data, data_dic

    def load_feature_names(self):
        '''
        Load feature names for loadings plot.
        '''
        feature_names = db.GetColnamesForClassifier()
        features_dictionary = {}    
        for i, feat in enumerate(feature_names):
            features_dictionary[i] = feat

        return features_dictionary

    def set_data(self, data, data_dic, class_masks, class_names, object_opacity=None):
        '''
        Stores data to be used in the dimensionality reduction process
        '''
        self.data = data
        self.data_dic = data_dic
        self.class_masks = class_masks
        self.class_names = class_names
        self.object_opacity = object_opacity
        self.update_figures();

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

    def update_figures(self):
        self.figure_scores.data, self.figure_scores.data_dic = self.data, self.data_dic
        self.figure_scores.class_masks, self.figure_scores.class_names = self.class_masks, self.class_names
        self.figure_scores.object_opacity = self.object_opacity
        self.figure_scores.set_plot_type("Scores")

        self.figure_loadings.data, self.figure_loadings.data_dic = self.data, self.data_dic
        self.figure_loadings.class_masks, self.figure_loadings.class_names = self.class_masks, self.class_names
        self.figure_loadings.object_opacity = self.object_opacity
        self.figure_loadings.features_dic = self.features_dic
        self.figure_loadings.set_plot_type("Loadings")

if __name__ == "__main__":
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.INFO,)

    global p
    p = Properties.getInstance()
    global db
    db = DBConnect.getInstance()

    try:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    except:
        if not p.show_load_dialog():
            raise Exception("DimensRedux.py needs a CPAnalyst properties file passed as args. Exiting...")     
            sys.exit()

    pca_main = PlotMain(None)
    pca_main.Show()
    app.MainLoop()
