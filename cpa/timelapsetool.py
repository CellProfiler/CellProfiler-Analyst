'''
Dependencies:
Enthought Tool Suite (for Mayavi2): http://www.lfd.uci.edu/~gohlke/pythonlibs/#ets
VTK (5.10+): http://www.lfd.uci.edu/~gohlke/pythonlibs/#vtk
NetworkX (1.7+): http://www.lfd.uci.edu/~gohlke/pythonlibs/#networkx
NumPy-MKL (1.71+): http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
configobj (required by Enthought): https://pypi.python.org/pypi/configobj
'''
import wx
# Looks like wx.combo becomes wx.adv in wx 2.9+ or Phoenix? http://comments.gmane.org/gmane.comp.python.wxpython.devel/5635
from wx.combo import OwnerDrawnComboBox as ComboBox
from wx.lib.scrolledpanel import ScrolledPanel
import networkx as nx
import numpy as np
from operator import itemgetter
import glayout

import logging
import time
import sortbin
import imagetools
from guiutils import get_main_frame_or_none
from dbconnect import DBConnect, image_key_columns, object_key_columns
from properties import Properties
from cpatool import CPATool
import tableviewer

import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

# traits imports
from traits.api import HasTraits, Int, Instance, on_trait_change
from traitsui.api import View, Item, HSplit, Group

# mayavi imports
from mayavi import mlab
from mayavi.core.ui.api import MlabSceneModel, SceneEditor
from mayavi.core.ui.mayavi_scene import MayaviScene
from tvtk.pyface.scene import Scene
from tvtk.api import tvtk

# Colormap names from an error msg (http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00615.html)
# TODO(?): Find a better way to captures these names
all_colormaps = ['Accent', 'Blues', 'BrBG', 'BuGn', 'BuPu', 'Dark2', 
                 'GnBu', 'Greens', 'Greys', 'OrRd', 'Oranges', 'PRGn', 
                 'Paired', 'Pastel1', 'Pastel2', 'PiYG', 'PuBu', 
                 'PuBuGn', 'PuOr', 'PuRd', 'Purples', 'RdBu', 'RdGy', 
                 'RdPu', 'RdYlBu', 'RdYlGn', 'Reds', 'Set1', 'Set2', 
                 'Set3', 'Spectral', 'YlGn', 'YlGnBu', 'YlOrBr', 
                 'YlOrRd', 'autumn', 'binary', 'black-white', 'blue-red', 
                 'bone', 'cool', 'copper', 'file', 'flag', 'gist_earth', 
                 'gist_gray', 'gist_heat', 'gist_ncar', 'gist_rainbow', 
                 'gist_stern', 'gist_yarg', 'gray', 'hot', 'hsv', 'jet', 
                 'pink', 'prism', 'spectral', 'spring', 'summer','winter']
all_colormaps.sort()

required_fields = ['series_id', 'group_id', 'timepoint_id','object_tracking_label']



db = DBConnect.getInstance()
props = Properties.getInstance()

TRACKING_MODULE_NAME = "TrackObjects"
OTHER_METRICS = "Other derived metrics..."
L_YCOORD = "Y_2"
L_TCOORD = "T_2"
T_XCOORD = "X_3"
T_YCOORD = "Y_3"
T_TCOORD = "T_3"
SCALAR_VAL = "S"
VISIBLE = "VISIBLE"
track_attributes = ["label","x","y","t",SCALAR_VAL,"f"]

SUBGRAPH_ID = "Subgraph"

VISIBLE_SUFFIX = "_VISIBLE"
METRIC_BC = "BetweennessCentrality"
METRIC_BC_VISIBLE = METRIC_BC+VISIBLE_SUFFIX

METRIC_SINGLETONS = "Singletons"
METRIC_SINGLETONS_VISIBLE = METRIC_SINGLETONS+VISIBLE_SUFFIX

METRIC_NODESWITHINDIST = "NodesWithinDistanceCutoff"
METRIC_NODESWITHINDIST_VISIBLE = METRIC_NODESWITHINDIST+VISIBLE_SUFFIX

BRANCH_NODES = "Branch_node"
END_NODES = "End_node"
START_NODES = "Start_node"
TERMINAL_NODES = "Terminal_node"
IS_REMOVED = "Is_removed"

EDITED_TABLE_SUFFIX = "_Edits"
ORIGINAL_TRACK = "Original: No edits"

def add_props_field(props):
    # Temp declarations; these will be retrieved from the properties file directly, eventually
    props.series_id = ["Image_Group_Number"]
    #props.series_id = ["Image_Metadata_Plate"]
    props.group_id = "Image_Group_Number"
    props.timepoint_id = "Image_Group_Index"
    obj = retrieve_object_name() 
    # TODO: Allow for selection of tracking labels, since there may be multiple objects tracked in different ways. Right now, just pick the first one.
    # TODO: Allow for selection of parent image/object fields, since there may be multiple tracked objects. Right now, just pick the first one.
    if props.db_type == 'sqlite':
        query = "PRAGMA table_info(%s)"%(props.object_table)
        all_fields = [item[1] for item in db.execute(query)]
    else:
        query = "SELECT column_name FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(props.db_name, props.object_table)
        all_fields = [item[0] for item in db.execute(query)]
    props.object_tracking_label = [item for item in all_fields if item.find("_".join((obj,TRACKING_MODULE_NAME,'Label'))) != -1][0]
    props.parent_fields = [ [item for item in all_fields if item.find("_".join((obj,TRACKING_MODULE_NAME,'ParentImageNumber'))) != -1][0],
                            [item for item in all_fields if item.find("_".join((obj,TRACKING_MODULE_NAME,'ParentObjectNumber'))) != -1][0] ] 
    table_prefix = props.image_table.split("Per_Image")[0]
    props.relationship_table = table_prefix + "Per_Relationships"
    props.relationshiptypes_table = table_prefix + "Per_RelationshipTypes"
    props.relationships_view = table_prefix + "Per_RelationshipsView"
    return props

def retrieve_datasets():
    series_list = ",".join(props.series_id)
    query = "SELECT %s FROM %s GROUP BY %s"%(series_list,props.image_table,series_list)
    all_datasets = [x[0] for x in db.execute(query)]
    return all_datasets

def retrieve_object_name():
    return props.cell_x_loc.split('_Location_Center')[0]

def is_LAP_tracking_data():
    # If the data is LAP-based, then additional button(s) show up
    LAP_field = "Kalman"
    if props.db_type == 'sqlite':
        query = "PRAGMA table_info(%s)"%(props.object_table)
        return(len([item[1] for item in db.execute(query) if item[1].find(LAP_field) != -1]) > 0)
    else:
        query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP '_Kalman_'"%(props.db_name, props.object_table)
        return(len(db.execute(query)) > 0)
    
def where_stmt_for_tracked_objects(obj, group_id, selected_dataset):
    # We want relationships that are cover the following:
    # - Are parent/child, e.g, exclude neighborhood
    # - Share the same parent/child object, e.g, exclude primary/secondary/tertiary, some cases of neighborhood
    # - Are across-frame, e.g, exclude neighborhood, primary/secondary/tertiary
    # - For the selected dataset        
    stmt = ("LOWER(relationship) = 'parent'", 
            "AND object_name1 = '%s'"%(obj),
            "AND object_name1 = object_name2",
            "AND image_number1 != image_number2",
            "AND i1.%s = %d"%(group_id,selected_dataset)
            )
    return stmt    

def obtain_relationship_index(selected_dataset, selected_dataset_track):
    obj = retrieve_object_name()
    query = ("SELECT %s FROM %s, %s i1 WHERE"%(selected_dataset_track, props.relationships_view, props.image_table),) + \
                 where_stmt_for_tracked_objects(obj,props.group_id,int(selected_dataset))    
    query = " ".join(query)  
    return [_ for _ in db.execute(query)]    
    
def obtain_tracking_data(selected_dataset, selected_dataset_track, selected_measurement, selected_filter):
    def parse_dataset_selection(s):
        return [x.strip() for x in s.split(',') if x.strip() is not '']
    
    selection_list = parse_dataset_selection(selected_dataset)
    dataset_clause = " AND ".join(["%s = '%s'"%(x[0], x[1]) for x in zip([props.image_table+"."+item for item in props.series_id], selection_list)])
    
    columns_to_retrieve = list(object_key_columns(props.object_table))    # Node IDs
    columns_to_retrieve += [props.object_table+"."+item for item in props.parent_fields]    # Parent node IDs
    columns_to_retrieve += [props.object_table+"."+props.object_tracking_label] # Label assigned by TrackObjects
    columns_to_retrieve += [props.object_table+"."+props.cell_x_loc, props.object_table+"."+props.cell_y_loc] # x,y coordinates
    columns_to_retrieve += [props.image_table+"."+props.timepoint_id] # Timepoint/frame
    columns_to_retrieve += [props.object_table+"."+selected_measurement if selected_measurement is not None else 'NULL'] # Measured feature, insert NULL as placeholder if derived
    columns_to_retrieve += [" AND ".join(selected_filter)] if selected_filter is not None else ['1'] # Filter
    query = ["SELECT %s"%(",".join(columns_to_retrieve))]
    query.append("FROM %s, %s"%(props.image_table, props.object_table))
    query.append("WHERE %s = %s AND %s"%(props.image_table+"."+props.image_id, props.object_table+"."+props.image_id, dataset_clause))
    query.append("ORDER BY %s, %s"%(props.object_tracking_label, props.timepoint_id))
    data = db.execute(" ".join(query))
    columns = [props.object_tracking_label, props.image_id, props.object_id, props.cell_x_loc, props.cell_y_loc, props.timepoint_id, "Filter", props.parent_fields]
    
    obj = retrieve_object_name()
    reln_cols = ['image_number1', 'object_number1', 'image_number2', 'object_number2']
    query = ("SELECT %s FROM %s, %s i1 WHERE"%(",".join(reln_cols), props.relationships_view, props.image_table),) + \
             where_stmt_for_tracked_objects(obj,props.group_id,int(selected_dataset)) 
    query = " ".join(query)  
    relationships = [_ for _ in db.execute(query)]    
    return columns, data, relationships

################################################################################
class MeasurementFilter(wx.Panel):
    '''
    Widget for creating lists of filters
    '''    
    def __init__(self, parent, allow_delete=True, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)        
        
        self.measurement_choices = db.GetColumnNames(props.object_table)
        self.colChoice = ComboBox(self, choices=self.measurement_choices, size=(-1,-1), style=wx.CB_READONLY)
        self.colChoice.Select(0)
        self.colChoice.Bind(wx.EVT_COMBOBOX, self.on_select_column)
        
        self.comparatorChoice = ComboBox(self, size=(-1,-1))
        self.update_comparator_choice()
        
        self.valueField = wx.ComboBox(self, -1, value='')
        
        if allow_delete:
            self.minus_button = wx.Button(self, -1, label='-', size=(30,-1))
            self.minus_button.Bind(wx.EVT_BUTTON, lambda event: self.Parent.on_remove_filter(event,self))              
        self.plus_button = wx.Button(self, -1, label='+', size=(30,-1))   
        self.plus_button.Bind(wx.EVT_BUTTON, lambda event: self.Parent.on_add_filter(event,self))     
        
        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(self.colChoice, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.comparatorChoice, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.valueField, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.plus_button, 0, wx.EXPAND) 
        colSizer.AddSpacer((5,-1))        
        colSizer.Add(self.minus_button if allow_delete else wx.StaticText(self,-1,size=(30,-1)), 0, wx.EXPAND)
        self.SetSizerAndFit(colSizer)

    def on_select_column(self, evt):
        self.update_comparator_choice()
        self.update_value_choice()

    def _get_column_type(self):
        return db.GetColumnTypes(props.object_table)[self.colChoice.GetSelection()]

    def update_comparator_choice(self):
        coltype = self._get_column_type()
        comparators = []
        if coltype in [str, unicode]:
            comparators = ['=', '!=', 'REGEXP', 'IS', 'IS NOT', 'IS NULL']
        if coltype in [int, float, long]:
            comparators = ['=', '!=', '<', '>', '<=', '>=', 'IS', 'IS NOT', 'IS NULL']
        self.comparatorChoice.SetItems(comparators)
        self.comparatorChoice.Select(0)
        
    def update_value_choice(self):
        column = self.colChoice.Value
        column_type = db.GetColumnTypes(props.object_table)[self.colChoice.GetSelection()]
        vals = []
        if column_type == str:# or coltype == int or coltype == long:
            res = db.execute('SELECT DISTINCT %s FROM %s ORDER BY %s'%(column, table, column))
            vals = [str(row[0]) for row in res]
        self.valueField.SetItems(vals)         

################################################################################
class FilterPanel(ScrolledPanel):
    '''
    Panel for measurement filtering.
    '''
    def __init__(self, parent, **kwargs):
        ScrolledPanel.__init__(self, parent, **kwargs)
        
        self.panel_sizer = wx.BoxSizer( wx.VERTICAL )
        self.filters = []
        filt = MeasurementFilter(self, False)
        self.panel_sizer.Add(filt, 0, wx.EXPAND)
        self.filters.append(filt)

        self.SetSizer(self.panel_sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling(False,True)
        self.Disable()
        
    def on_add_filter(self,event,selected_filter):
        self.filters.append(MeasurementFilter(self, True))
        self.panel_sizer.Add(self.filters[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.SetupScrolling(False,True)
        self.panel_sizer.SetMinSize(self.panel_sizer.GetMinSize())
        self.SetSizerAndFit(self.panel_sizer)        
        self.SetAutoLayout(1)
        self.Refresh()
        self.Layout() 
        
    def on_remove_filter(self,event,selected_filter):
        i = self.filters.index(selected_filter)
        self.filters.remove(selected_filter)
        self.panel_sizer.Remove(selected_filter)
        selected_filter.Destroy()
        self.SetupScrolling(False,len(self.filters) < 3 )  
        self.Refresh()
        self.Layout()          

################################################################################
class TimeLapseControlPanel(wx.Panel):
    '''
    A panel with controls for selecting the data for a visual
    Some helpful tips on using sizers for layout: http://zetcode.com/wxpython/layout/
    '''

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)

        # Get names of data sets
        all_datasets = retrieve_datasets()

        # Capture if LAP data is being used
        self.isLAP = is_LAP_tracking_data()
        
        # Get names of fields
        measurements = db.GetColumnNames(props.object_table)
        coltypes = db.GetColumnTypes(props.object_table)
        fields = [m for m,t in zip(measurements, coltypes) if t in [float, int, long]]
        self.dataset_measurement_choices = fields
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Define widgets
        self.dataset_choice = ComboBox(self, -1, choices=[str(item) for item in all_datasets], size=(200,-1), style=wx.CB_READONLY)
        self.dataset_choice.Select(0)
        self.dataset_choice.SetHelpText("Select the time-lapse data set to visualize.")
        
        self.dataset_relationship_index = ComboBox(self, -1, choices=[ORIGINAL_TRACK], size=(200,-1), style=wx.CB_READONLY)
        self.dataset_relationship_index.Select(0)
        self.dataset_relationship_index.SetHelpText("Select the identifier specifying the tracked object relationships in the current data set.")  
        self.dataset_relationship_index.Disable()

        self.dataset_measurement_choice = ComboBox(self, -1, choices=self.dataset_measurement_choices, style=wx.CB_READONLY)
        self.dataset_measurement_choice.Select(0)
        self.dataset_measurement_choice.SetHelpText("Select the per-%s measurement to visualize the data with. The lineages and (xyt) trajectories will be color-coded by this measurement."%props.object_name[0])
        
        self.colormap_choice = ComboBox(self, -1, choices=all_colormaps, style=wx.CB_READONLY)
        self.colormap_choice.SetStringSelection("jet") 
        self.colormap_choice.SetHelpText("Select the colormap to use for color-coding the data.")
        
        self.trajectory_selection_button = wx.Button(self, -1, "Select Tracks to Visualize...")
        self.trajectory_selection_button.SetHelpText("Select the trajectories to show or hide in both panels.")
        if self.isLAP:
            self.trajectory_diagnosis_toggle = wx.ToggleButton(self, -1, "Show LAP Diagnostic Graphs")
            self.trajectory_diagnosis_toggle.SetHelpText("If you have tracking data generated by the LAP method, a new box will open with diagnostic graphs indicating goodness of your settings.")
        
        self.update_plot_color_button = wx.Button(self, -1, "Update Color")
        self.update_plot_color_button.SetHelpText("Press this button after making selections to update the panels.")
        
        self.help_button = wx.ContextHelpButton(self)
        
        self.derived_measurement_choice = ComboBox(self, -1, style=wx.CB_READONLY)
        self.derived_measurement_choice.SetHelpText("Select the derived measurement to visualize the data with.")     
        self.derived_measurement_choice.Disable()
        
        self.distance_cutoff_value = wx.SpinCtrl(self, -1, value = "4", style=wx.SP_ARROW_KEYS, min=0, initial=4)
        self.distance_cutoff_value.SetHelpText("Enter the number of nodes from a branch that a terminus must be found in order to be selected as a candidate for pruning.")   
        self.distance_cutoff_value.Disable()
        
        self.bc_branch_ratio_value = wx.TextCtrl(self, -1, value = "0.5", style=wx.TE_PROCESS_ENTER)
        self.bc_branch_ratio_value.SetHelpText("Enter the betweeness centrality fraction that a branch node must be in order be selected as a candidate for pruning.")   
        self.bc_branch_ratio_value.Disable()        

        self.preview_prune_button = wx.ToggleButton(self, -1, "Preview Pruned Branches")
        self.preview_prune_button.SetHelpText("Redraws the graph with the pruned nodes removed.")
        self.preview_prune_button.Disable()  
        
        self.add_pruning_to_edits_button = wx.Button(self, -1, "Add Pruning to Edits")
        self.add_pruning_to_edits_button.SetHelpText("Adds the pruned graph to the list of edits.")
        self.add_pruning_to_edits_button.Disable()          
        
        self.save_edited_tracks = wx.Button(self, -1, "Save Edited Tracks...")
        self.save_edited_tracks.SetHelpText("Saves the edited graph as a new index into the relationship table.")
        self.save_edited_tracks.Disable()         

        self.all_derived_measurements_widgets = [self.derived_measurement_choice, 
                                                 self.distance_cutoff_value, 
                                                 self.bc_branch_ratio_value, 
                                                 self.preview_prune_button, 
                                                 self.add_pruning_to_edits_button,
                                                 self.save_edited_tracks]
        
        # Arrange widgets
        # Row #1: Dataset drop-down + track selection button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Data Source:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.dataset_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Data Tracks:"), 0, wx.TOP, 4)
        sz.Add(self.dataset_relationship_index, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.trajectory_selection_button)
        if self.isLAP:
            sz.AddSpacer((4,-1))
            sz.Add(self.trajectory_diagnosis_toggle)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        # Row #2: Data measurement color selection, colormap, update button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Data Measurements:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.dataset_measurement_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Colormap:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.colormap_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.update_plot_color_button)
        sz.AddSpacer((4,-1))
        sz.Add(self.help_button)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        # Row #3: Derived measurement color selection
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Derived Metrics:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))  
        sz.Add(self.derived_measurement_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Distance cutoff:"), 0, wx.TOP, 4)
        sz.Add(self.distance_cutoff_value, 1, wx.EXPAND)
        sz.Add(wx.StaticText(self, -1, "Betweeness centrality cutoff:"), 0, wx.TOP, 4)
        sz.Add(self.bc_branch_ratio_value, 1, wx.EXPAND) 
        sz.AddSpacer((4,-1))
        sz.Add(self.preview_prune_button, 1, wx.EXPAND) 
        sz.AddSpacer((4,-1))
        sz.Add(self.add_pruning_to_edits_button, 1, wx.EXPAND) 
        sz.AddSpacer((4,-1))
        sz.Add(self.save_edited_tracks, 1, wx.EXPAND) 
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))        

        # Row #4: Measurement filter selection
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.enable_filtering_checkbox = wx.CheckBox(self, -1, label="Enable filtering")
        self.enable_filtering_checkbox.SetValue(0)
        sz.Add(self.enable_filtering_checkbox, 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        self.filter_panel = FilterPanel(self)
        sz.Add(self.filter_panel,1, wx.TOP, 4)
        sz.Layout()
        sizer.Add(sz, 1, wx.EXPAND) 
        sizer.AddSpacer((-1,2))
        sizer.Layout()
        self.SetSizer(sizer)
        self.Layout()
        self.Show(True)
        
################################################################################
class MayaviView(HasTraits):
    """ Create a mayavi scene"""
    lineage_scene = Instance(MlabSceneModel, ())
    trajectory_scene = Instance(MlabSceneModel, ())
    dataset = Int(0)
    
    # The layout of the dialog created
    view = View(HSplit(Group(Item('trajectory_scene',
                                  #editor = SceneEditor(scene_class = Scene),
                                  editor = SceneEditor(scene_class=MayaviScene),
                                  resizable=True, show_label=False)),
                       Group(Item('lineage_scene',
                                  editor = SceneEditor(scene_class = Scene),
                                  #editor = SceneEditor(scene_class=MayaviScene),
                                  resizable=True, show_label=False))),
                resizable=True)
    
    def __init__(self, parent):
        HasTraits.__init__(self)
        self.parent = parent
        self.axes_opacity = 0.25
        self.lineage_figure = self.lineage_scene.mlab.gcf()
        self.trajectory_figure = self.trajectory_scene.mlab.gcf()

    # Apparently, I cannot use mlab.clf to clear the figure without disconnecting the picker
    # So remove the children to get the same effect.
    # See: http://stackoverflow.com/questions/23435986/mayavi-help-in-resetting-mouse-picker-and-connecting-wx-event-to-on-trait-chan
    # Note that the respondent says I will still need to reattach the picker, but that doesn't seem to be the case here...
    def clear_figures(self, scene):
        for child in scene.mayavi_scene.children:
            child.remove()  
            
    @on_trait_change('lineage_scene.activated')
    def activate_lineage_scene(self):
        # An trajectory picker object is created to trigger an event when a trajectory is picked. 
        # Can press 'p' to get UI on current pick 
        #
        # Helpful pages re: pickers
        # https://gist.github.com/syamajala/8804396
        # http://sourceforge.net/p/mayavi/mailman/message/27239432/  (not identical problem)    
        picker = self.lineage_scene.mayavi_scene.on_mouse_pick(self.on_pick_lineage)
        picker.tolerance = 0.01
        
        # Why is this here? Well, apparently the axes need to be oriented to a camera, which needs the view to be opened first.
        # See http://en.it-usenet.org/thread/15952/8170/
        mlab.axes(self.lineage_node_collection, 
                          xlabel='T', ylabel='',
                          extent = self.lineage_extent,
                          opacity = self.axes_opacity,
                          x_axis_visibility=True, y_axis_visibility=False, z_axis_visibility=False) 
        
        # Constrain view to 2D
        self.lineage_scene.interactor.interactor_style = tvtk.InteractorStyleImage()        
        self.lineage_scene.reset_zoom()
        
        # Add object label text to the left
        # Why is this here? The text module needs to have a scene opened to work
        # http://enthought-dev.117412.n3.nabble.com/How-to-clear-AttributeError-NoneType-object-has-no-attribute-active-camera-td2181947.html
        text_scale_factor = self.lineage_node_scale_factor/1.0 
        t = nx.get_node_attributes(self.directed_graph,L_TCOORD)
        y = nx.get_node_attributes(self.directed_graph,L_YCOORD)
        start_nodes = {}
        for key,subgraph in self.connected_nodes.items():
            start_nodes[key] = [_[0] for _ in nx.get_node_attributes(subgraph,START_NODES).items() if _[1]]
        self.lineage_label_collection = dict(zip(self.connected_nodes.keys(),
                                                 [mlab.text3d(t[start_nodes[key][0]]-0.75*self.lineage_temporal_scaling,
                                                              y[start_nodes[key][0]],
                                                              0,
                                                              str(key),
                                                              scale = text_scale_factor,
                                                              figure = self.lineage_scene.mayavi_scene)
                                                  for key,subgraph in self.connected_nodes.items()]))       
        #self.dataset = int(self.parent.selected_dataset)        
    
    @on_trait_change('trajectory_scene.activated')
    def activate_trajectory_scene(self):
        picker = self.trajectory_scene.mayavi_scene.on_mouse_pick(self.on_pick_trajectory)
        picker.tolerance = 0.01
        
        # TODO: Incorporate image dimensions into axes viz
        # Get image dimensions
        if props.db_type == 'sqlite':
            query = "PRAGMA table_info(%s)"%(props.image_table)
            w_col = [_[1] for _ in db.execute(query) if _[1].find('Image_Width') >= 0][0]
            h_col = [_[1] for _ in db.execute(query) if _[1].find('Image_Height') >= 0][0]  
        else:
            query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP 'Image_Width' LIMIT 1"%(props.db_name, props.image_table)
            w_col = db.execute(query)[0][0]
            query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP 'Image_Height' LIMIT 1"%(props.db_name, props.image_table)
            h_col = db.execute(query)[0][0]          

        query = "SELECT %s FROM %s LIMIT 1"%(w_col, props.image_table)
        self.parent.image_x_dims = db.execute(query)[0][0]
        query = "SELECT %s FROM %s LIMIT 1"%(h_col, props.image_table)
        self.parent.image_y_dims = db.execute(query)[0][0]        
        
        ax = mlab.axes(self.trajectory_line_source, 
                      xlabel='X', ylabel='Y',zlabel='T',
                      #extent = (1,self.parent.image_x_dims,1,self.parent.image_y_dims,self.parent.start_frame,self.parent.end_frame),
                      opacity = self.axes_opacity,
                      x_axis_visibility=True, y_axis_visibility=True, z_axis_visibility=True)
        
        # Set axes to MATLAB's default 3d view
        mlab.view(azimuth = 322.5,elevation = 30.0,
                  figure = self.trajectory_scene.mayavi_scene)     
        
        # Add object label text at end of trajectory
        text_scale_factor = self.trajectory_node_scale_factor*5 
        end_nodes = {}
        for (key,subgraph) in self.connected_nodes.items():
            end_nodes[key] = [_[0] for _ in nx.get_node_attributes(subgraph,END_NODES).items() if _[1]][0]
        self.trajectory_label_collection = dict(zip(self.connected_nodes.keys(),
                                                    [mlab.text3d(subgraph.node[end_nodes[key]]["x"],
                                                                 subgraph.node[end_nodes[key]]["y"],
                                                                 subgraph.node[end_nodes[key]]["t"]*self.trajectory_temporal_scaling,
                                                                 str(key),
                                                                 scale = text_scale_factor,
                                                                 name = str(key),
                                                                 figure = self.trajectory_scene.mayavi_scene) 
                                                     for (key,subgraph) in self.connected_nodes.items()]))       
        #self.dataset = int(self.parent.selected_dataset)
        self.trajectory_scene.reset_zoom()        
        
    def on_pick_lineage(self, picker):
        """ Lineage picker callback: this gets called upon pick events.
        """
        picked_graph_node = None
        picked_lineage_coords = None
        picked_trajectory_coords = None
        if picker.actor in self.lineage_node_collection.actor.actors + self.lineage_edge_collection.actor.actors:
            # TODO: Figure what the difference is between node_collection and edge_collection being clicked on.
            # Retrieve to which point corresponds the picked point. 
            # Here, we grab the points describing the individual glyph, to figure
            # out how many points are in an individual glyph.                
            n_glyph = self.lineage_node_collection.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]
            # Find which data point corresponds to the point picked:
            # we have to account for the fact that each data point is
            # represented by a glyph with several points      
            point_id = picker.point_id/n_glyph
            picked_lineage_coords = self.lineage_node_collection.mlab_source.points[point_id,:]
            picked_trajectory_coords = self.trajectory_node_collection.mlab_source.points[point_id,:]
            picked_graph_node = sorted(self.directed_graph)[point_id]
        self.on_pick(picked_graph_node, picked_lineage_coords, picked_trajectory_coords)
    
    def on_select_point(self):
        # Used if a coordinate is picked via somethign other than a mouse pick
        point_id = sorted(self.directed_graph).index(self.parent.selected_node)
        picked_trajectory_coords = self.trajectory_node_collection.mlab_source.points[point_id,:]
        picked_lineage_coords = self.lineage_node_collection.mlab_source.points[point_id,:]
        #self.parent.selected_node = None # Disable temporailty since it gets set back in on_pick
        self.on_pick(self.parent.selected_node, picked_lineage_coords, picked_trajectory_coords, True)  
    
    def on_pick_trajectory(self,picker):
        """ Trajectory picker callback: this gets called upon pick events.
        """
        picked_graph_node = None
        picked_lineage_coords = None
        picked_trajectory_coords = None
        if picker.actor in self.trajectory_node_collection.actor.actors:
            n_glyph = self.trajectory_node_collection.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]  
            point_id = picker.point_id/n_glyph            
            picked_trajectory_coords = self.trajectory_node_collection.mlab_source.points[point_id,:]
            picked_lineage_coords = self.lineage_node_collection.mlab_source.points[point_id,:]
            picked_graph_node = sorted(self.directed_graph)[point_id]        
        else:
            picked_graph_node = None
        self.on_pick(picked_graph_node, picked_lineage_coords, picked_trajectory_coords)
                
    def on_pick(self,picked_graph_node, picked_lineage_coords = None, picked_trajectory_coords = None, no_mouse = False):
        if picked_graph_node != None:
            # If the picked node is not one of the selected trajectories, then don't select it 
            if not no_mouse and picked_graph_node == self.parent.selected_node:
                self.parent.selected_node = None
                self.parent.selected_trajectory = None      
                self.lineage_selection_outline.actor.actor.visibility = 0
                self.trajectory_selection_outline.actor.actor.visibility = 0
            else:
                self.parent.selected_node = picked_graph_node
                self.parent.selected_trajectory = [self.parent.directed_graph[self.parent.selected_dataset_track].node[picked_graph_node][SUBGRAPH_ID]]
                
                # Move the outline to the data point
                dx = np.diff(self.lineage_selection_outline.bounds[:2])[0]/2
                dy = np.diff(self.lineage_selection_outline.bounds[2:4])[0]/2           
                self.lineage_selection_outline.bounds = (picked_lineage_coords[0]-dx, picked_lineage_coords[0]+dx,
                                                         picked_lineage_coords[1]-dy, picked_lineage_coords[1]+dy,
                                                         0, 0)
                self.lineage_selection_outline.actor.actor.visibility = 1
                
                dx = np.diff(self.trajectory_selection_outline.bounds[:2])[0]/2
                dy = np.diff(self.trajectory_selection_outline.bounds[2:4])[0]/2
                dt = np.diff(self.trajectory_selection_outline.bounds[4:6])[0]/2
                self.trajectory_selection_outline.bounds = (picked_trajectory_coords[0]-dx, picked_trajectory_coords[0]+dx,
                                                            picked_trajectory_coords[1]-dy, picked_trajectory_coords[1]+dy,
                                                            picked_trajectory_coords[2]-dt, picked_trajectory_coords[2]+dt)
                self.trajectory_selection_outline.actor.actor.visibility = 1        

    def draw_lineage(self, do_plots_need_updating, directed_graph=None, connected_nodes=None, selected_colormap=None, scalar_data = None):
        # Rendering temporarily disabled
        self.lineage_scene.disable_render = True 

        # Helpful pages on using NetworkX and Mayavi:
        #  http://docs.enthought.com/mayavi/mayavi/auto/example_delaunay_graph.html
        #  https://groups.google.com/forum/?fromgroups=#!topic/networkx-discuss/wdhYIPeuilo
        #  http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00727.html        

        # Draw the lineage tree if the dataset has been updated
        if do_plots_need_updating["dataset"]:
            self.connected_nodes = connected_nodes
            self.directed_graph = directed_graph
            
            # Clear the scene
            logging.info("Drawing lineage graph...")
            if self.parent.plot_initialized:
                self.clear_figures(self.lineage_scene)
             
            #mlab.title("Lineage tree",size=2.0,figure=self.lineage_scene.mayavi_scene)   
            
            t1 = time.clock()
            
            G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
            xys = np.array([[directed_graph.node[node][L_TCOORD],directed_graph.node[node][L_YCOORD],directed_graph.node[node][SCALAR_VAL]] for node in sorted(directed_graph.nodes()) ])
            #if len(xys) == 0:
                #xys = np.array(3*[np.NaN],ndmin=2)
            dt = np.median(np.diff(np.unique(nx.get_node_attributes(directed_graph,"t").values())))
            # The scale factor defaults to the typical interpoint distance, which may not be appropriate. 
            # So I set it explicitly here to a fraction of delta_t
            # To inspect the value, see pts.glyph.glpyh.scale_factor
            node_scale_factor = 0.5*dt
            self.lineage_node_collection = mlab.points3d(xys[:,0], xys[:,1], np.zeros_like(xys[:,0]), xys[:,2],
                                scale_factor = node_scale_factor, 
                                scale_mode = 'none',
                                colormap = selected_colormap,
                                resolution = 8,
                                figure = self.lineage_scene.mayavi_scene) 
            self.lineage_node_collection.glyph.color_mode = 'color_by_scalar'
            
            #tube_radius = node_scale_factor/10.0
            #tube = mlab.pipeline.tube(self.lineage_node_collection, 
            #                          tube_radius = tube_radius, # Default tube_radius results in v. thin lines: tube.filter.radius = 0.05
            #                          figure = self.lineage_scene.mayavi_scene)
            #self.lineage_tube = tube
            self.lineage_edge_collection = mlab.pipeline.surface(self.lineage_node_collection, 
                                                                 color=(0.8, 0.8, 0.8),
                                                                 figure = self.lineage_scene.mayavi_scene)
            self.lineage_edge_collection.mlab_source.dataset.lines = np.array(G.edges())
            self.lineage_edge_collection.mlab_source.update()
            
            # Add outline to be used later when selecting points
            self.lineage_selection_outline = mlab.outline(line_width=3,
                                                          figure = self.lineage_scene.mayavi_scene)
            self.lineage_selection_outline.outline_mode = 'cornered'
            self.lineage_selection_outline.actor.actor.visibility = 0
            self.lineage_selection_outline.bounds = (-node_scale_factor,node_scale_factor,
                                                     -node_scale_factor,node_scale_factor,
                                                     -node_scale_factor,node_scale_factor)            
            # Add 2 more outlines to be used later when selecting points
            self.lineage_point_selection_outline = []
            for i in range(2):
                ol = mlab.points3d(0,0,0,
                                   extent = list(2*np.array([-node_scale_factor,node_scale_factor,
                                             -node_scale_factor,node_scale_factor,
                                             -node_scale_factor,node_scale_factor])),
                                   color = (1,0,1),
                                   mode = 'sphere',
                                   scale_factor = 2*node_scale_factor, 
                                   scale_mode = 'none',                                   
                                   figure = self.lineage_scene.mayavi_scene)
                ol.actor.actor.visibility = 0    
                self.lineage_point_selection_outline.append(ol)            

            self.lineage_node_scale_factor = node_scale_factor
            
            # Add axes outlines
            self.lineage_extent = (0,np.max(nx.get_node_attributes(directed_graph,L_TCOORD).values()),
                                   0,np.max(nx.get_node_attributes(directed_graph,L_YCOORD).values()),
                                   0,0)
            self.lineage_outline = mlab.pipeline.outline(self.lineage_node_collection,
                                  extent = self.lineage_extent,
                                  opacity = self.axes_opacity,
                                  figure = self.lineage_scene.mayavi_scene) 
            
            t2 = time.clock()
            logging.info("Computed layout (%.2f sec)"%(t2-t1))   
        else:
            logging.info("Re-drawing lineage tree...")
            
            if do_plots_need_updating["trajectories"]:
                G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
                edges = np.array([e for e in G.edges() if G.node[e[0]][VISIBLE] and G.node[e[1]][VISIBLE]])
                self.lineage_edge_collection.mlab_source.dataset.lines = edges
                self.lineage_edge_collection.mlab_source.update()
                
                for key in connected_nodes.keys():
                    self.lineage_label_collection[key].actor.actor.visibility = self.parent.trajectory_selection[key]

            if do_plots_need_updating["measurement"]:
                self.lineage_node_collection.mlab_source.set(scalars = scalar_data)
            
            if do_plots_need_updating["colormap"]:
                # http://docs.enthought.com/mayavi/mayavi/auto/example_custom_colormap.html
                self.lineage_node_collection.module_manager.scalar_lut_manager.lut_mode = selected_colormap
                
        # Re-enable the rendering
        self.lineage_scene.disable_render = False        

    def draw_trajectories(self, do_plots_need_updating, directed_graph = None, connected_nodes = None, selected_colormap=None, scalar_data = None):
        # Rendering temporarily disabled
        self.trajectory_scene.disable_render = True  
        
        # Draw the lineage tree if either (1) all the controls indicate that updating is needed (e.g., initial condition) or
        # (2) if the dataset has been updated        
        if do_plots_need_updating["dataset"]:
            self.directed_graph = directed_graph
            self.connected_nodes = connected_nodes

            logging.info("Drawing trajectories...")
            # Clear the scene
            if self.parent.plot_initialized:
                self.clear_figures(self.trajectory_scene)
    
            #mlab.title("Trajectory plot",size=2.0,figure=self.trajectory_scene.mayavi_scene)   
    
            t1 = time.clock()
            
            G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
    
            xyts = np.array([(directed_graph.node[key]["x"],
                               directed_graph.node[key]["y"],
                               directed_graph.node[key]["t"],
                               directed_graph.node[key][SCALAR_VAL],
                               directed_graph.node[key][VISIBLE]) for key in sorted(directed_graph)])
            
            visible = xyts[:, -1]
            # Compute reasonable scaling factor according to the data limits.
            # We want the plot to be roughly square, to avoid nasty Mayavi axis scaling issues later.
            # Unfortunately, adjusting the surface.actor.actor.scale seems to lead to more problems than solutions.
            # See: http://stackoverflow.com/questions/13015097/how-do-i-scale-the-x-and-y-axes-in-mayavi2
            t_scaling = np.mean( [(max(xyts[:,0])-min(xyts[:,0])), (max(xyts[:,1])-min(xyts[:,1]))] ) / (max(xyts[:,2])-min(xyts[:,2]))
            xyts[:,2] *= t_scaling
            self.trajectory_temporal_scaling = t_scaling
    
            # Taken from http://docs.enthought.com/mayavi/mayavi/auto/example_plotting_many_lines.html
            # Create the lines
            self.trajectory_line_source = mlab.pipeline.scalar_scatter(xyts[:,0], xyts[:,1], xyts[:,2], xyts[:,3], \
                                                                       figure = self.trajectory_scene.mayavi_scene)
            # Connect them using the graph edge matrix
            self.trajectory_line_source.mlab_source.dataset.lines = np.array(G.edges())     
            
            # Finally, display the set of lines by using the surface module. Using a wireframe
            # representation allows to control the line-width.
            self.trajectory_line_collection = mlab.pipeline.surface(mlab.pipeline.stripper(self.trajectory_line_source), # The stripper filter cleans up connected lines; it regularizes surfaces by creating triangle strips
                                                                    line_width=1, 
                                                                    colormap=selected_colormap,
                                                                    figure = self.trajectory_scene.mayavi_scene)         
    
            # Generate the corresponding set of nodes
            dt = np.median(np.diff(np.unique(nx.get_node_attributes(directed_graph,"t").values())))
            self.lineage_temporal_scaling = dt
            
            # Try to scale the nodes in a reasonable way
            # To inspect, see pts.glyph.glpyh.scale_factor 
            node_scale_factor = 0.5*dt
            pts = mlab.points3d(xyts[:,0], xyts[:,1], xyts[:,2], xyts[:,3],
                                scale_factor = 0.0,
                                scale_mode = 'none',
                                colormap = selected_colormap,
                                figure = self.trajectory_scene.mayavi_scene) 
            pts.glyph.color_mode = 'color_by_scalar'
            pts.mlab_source.dataset.lines = np.array(G.edges())
            self.trajectory_node_collection = pts    
    
            # Add outline to be used later when selecting points
            self.trajectory_selection_outline = mlab.outline(line_width = 3,
                                                             figure = self.trajectory_scene.mayavi_scene)
            self.trajectory_selection_outline.outline_mode = 'cornered'
            self.trajectory_selection_outline.bounds = (-node_scale_factor,node_scale_factor,
                                                        -node_scale_factor,node_scale_factor,
                                                        -node_scale_factor,node_scale_factor)
            self.trajectory_selection_outline.actor.actor.visibility = 0
            
            # Add 2 more points to be used later when selecting points
            self.trajectory_point_selection_outline = []
            for i in range(2):
                ol = mlab.points3d(0,0,0,
                                   extent = [-node_scale_factor,node_scale_factor,
                                             -node_scale_factor,node_scale_factor,
                                             -node_scale_factor,node_scale_factor],
                                   color = (1,0,1),
                                   figure = self.trajectory_scene.mayavi_scene)
                ol.actor.actor.visibility = 0    
                self.trajectory_point_selection_outline.append(ol)
            
            self.trajectory_node_scale_factor = node_scale_factor
            
            # Using axes doesn't work until the scene is avilable: 
            # http://docs.enthought.com/mayavi/mayavi/building_applications.html#making-the-visualization-live
            mlab.pipeline.outline(self.trajectory_line_source,
                                  opacity = self.axes_opacity,
                                  figure = self.trajectory_scene.mayavi_scene) 
            
            # Figure decorations
            # Orientation axes
            #mlab.orientation_axes(zlabel = "T", 
                                  #line_width = 5,
                                  #figure = self.mayavi_view.trajectory_scene.mayavi_scene )
            # Colormap
            # TODO: Figure out how to scale colorbar to smaller size
            #c = mlab.colorbar(orientation = "horizontal", 
                              #title = self.selected_measurement,
                              #figure = self.mayavi_view.trajectory_scene.mayavi_scene)
            #c.scalar_bar_representation.position2[1] = 0.05
            #c.scalar_bar.height = 0.05
            
            t2 = time.clock()
            logging.info("Computed trajectory layout (%.2f sec)"%(t2-t1))              
        else:
            logging.info("Re-drawing trajectories...")
            
            if do_plots_need_updating["trajectories"]:
                G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
                edges = [e for e in G.edges() if G.node[e[0]][VISIBLE] and G.node[e[1]][VISIBLE]]
                self.trajectory_line_collection.mlab_source.dataset.lines = self.trajectory_line_source.mlab_source.dataset.lines = \
                    np.array(edges)
                self.trajectory_line_collection.mlab_source.update()
                self.trajectory_line_source.mlab_source.update()                
                
                for key in connected_nodes.keys():
                    self.trajectory_label_collection[key].actor.actor.visibility = self.parent.trajectory_selection[key] != 0  

            if do_plots_need_updating["measurement"]:
                self.trajectory_line_collection.mlab_source.set(scalars = scalar_data)
                self.trajectory_node_collection.mlab_source.set(scalars = scalar_data)
            
            if do_plots_need_updating["colormap"]:
                self.trajectory_line_collection.module_manager.scalar_lut_manager.lut_mode = selected_colormap
                self.trajectory_node_collection.module_manager.scalar_lut_manager.lut_mode = selected_colormap
                
        # Re-enable the rendering
        self.trajectory_scene.disable_render = False  
            
################################################################################
class FigureFrame(wx.Frame, CPATool):
    """A wx.Frame with a figure inside"""
    def __init__(self, parent=None, id=-1, title="", 
                     pos=wx.DefaultPosition, size=wx.DefaultSize,
                     style=wx.DEFAULT_FRAME_STYLE, name=wx.FrameNameStr, 
                     subplots=None, on_close = None):
        """Initialize the frame:
            
            parent   - parent window to this one
            id       - window ID
            title    - title in title bar
            pos      - 2-tuple position on screen in pixels
            size     - 2-tuple size of frame in pixels
            style    - window style
            name     - searchable window name
            subplots - 2-tuple indicating the layout of subplots inside the window
            on_close - a function to run when the window closes
            """       
        super(FigureFrame,self).__init__(parent, id, title, pos, size, style, name)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer) 
        matplotlib.rcdefaults()
        self.figure = figure = matplotlib.figure.Figure()
        figure.set_facecolor((1,1,1))
        figure.set_edgecolor((1,1,1))        
        self.panel = FigureCanvasWxAgg(self, -1, self.figure)
        sizer.Add(self.panel, 1, wx.EXPAND)
        #wx.EVT_CLOSE(self, self.on_close)
        if subplots:
            self.subplots = np.zeros(subplots,dtype=object)  
        self.Fit()
        self.Show()
        
    def on_close(self, event):
        if self.close_fn is not None:
            self.close_fn(event)
        self.clf() # Free memory allocated by imshow
        self.Destroy()        
        
################################################################################
class TimeLapseTool(wx.Frame, CPATool):
    '''
    A time-lapse visual plot with its controls.
    '''
    def __init__(self, parent, size=(1000,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Time-Lapse Tool', **kwargs)
        CPATool.__init__(self)
        wx.HelpProvider_Set(wx.SimpleHelpProvider())
        self.SetName(self.tool_name)
        
        # Check for required properties fields.
        #fail = False
        #missing_fields = [field for field in required_fields if not props.field_defined(field)]
        #if missing_fields:
            #fail = True
            #message = 'The following missing fields are required for LineageTool: %s.'%(",".join(missing_fields))
            #wx.MessageBox(message,'Required field(s) missing')
            #logging.error(message)
        #if fail:    
            #self.Destroy()
            #return   
        props = Properties.getInstance()
        props = add_props_field(props)

        self.directed_graph = {}
        self.connected_nodes = {}
        self.control_panel = TimeLapseControlPanel(self)
        self.selected_dataset = self.control_panel.dataset_choice.GetStringSelection()
        self.selected_dataset_track = ORIGINAL_TRACK
        self.dataset_measurement_choices = self.control_panel.dataset_measurement_choice.GetItems()
        self.selected_measurement = self.control_panel.dataset_measurement_choice.GetStringSelection()
        self.selected_metric = self.control_panel.derived_measurement_choice.GetStringSelection()
        self.selected_colormap  = self.control_panel.colormap_choice.GetStringSelection()
        self.selected_filter = None
        self.plot_updated = False
        self.plot_initialized = False
        self.trajectory_selected = False
        self.selected_node = None
        self.selected_endpoints = [None,None]
        self.image_x_dims = None
        self.image_y_dims = None
        self.do_plots_need_updating = {"dataset":True,
                                       "tracks":True,
                                       "colormap":True,
                                       "measurement":True, 
                                       "trajectories":True,
                                       "filter":None}
        
        self.mayavi_view = MayaviView(self)
        self.update_plot() 
        self.plot_initialized = True
        self.figure_panel = self.mayavi_view.edit_traits(
                                            parent=self,
                                            kind='subpanel').control
        self.mayavi_view.dataset = int(self.selected_dataset)
        
        navigation_help_text = ("Tips on navigating the plots:\n"
                                "Rotating the 3-D visualization: Place the mouse pointer over the visualization"
                                "window. Then left-click and drag the mouse pointer in the direction you want to rotate"
                                "the scene, much like rotating an actual object.\n\n"
                                "Zooming in and out: Place the mouse pointer over the visualization"
                                "window. To zoom into the scene, keep the right mouse button pressed and"
                                "drags the mouse upwards. To zoom out of the scene,  keep the right mouse button pressed"
                                "and drags the mouse downwards.\n\n"
                                "Panning: This can be done in one in two ways:\n"
                                "1. Keep the left mouse button pressed and simultaneously holding down the Shift key"
                                "and dragging the mouse in the appropriate direction.\n"
                                "2. Keep the middle mouse button pressed and dragging the mouse in the appropriate"
                                "direction\n\n"
                                "Please note that while the lineage panel can be rotated, zoomed and panned, it is a 2-D"
                                "plot so the top-down view is fixed.")
        self.figure_panel.SetHelpText(" ".join(navigation_help_text))
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.figure_panel, 1, wx.EXPAND)
        sizer.Add(self.control_panel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        
        self.figure_panel.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
        
        # Define events
        wx.EVT_COMBOBOX(self.control_panel.dataset_choice, -1, self.on_dataset_selected)
        wx.EVT_COMBOBOX(self.control_panel.dataset_measurement_choice, -1, self.on_dataset_measurement_selected)
        wx.EVT_COMBOBOX(self.control_panel.derived_measurement_choice, -1, self.on_derived_measurement_selected)
        wx.EVT_BUTTON(self.control_panel.trajectory_selection_button, -1, self.update_trajectory_selection)
        if self.control_panel.isLAP:
            wx.EVT_TOGGLEBUTTON(self.control_panel.trajectory_diagnosis_toggle, -1, self.calculate_and_display_lap_stats)
        wx.EVT_COMBOBOX(self.control_panel.colormap_choice, -1, self.on_colormap_selected)
        wx.EVT_BUTTON(self.control_panel.update_plot_color_button, -1, self.update_plot)
        wx.EVT_CHECKBOX(self.control_panel.enable_filtering_checkbox, -1, self.enable_filtering)
        wx.EVT_SPINCTRL(self.control_panel.distance_cutoff_value,-1,self.on_derived_measurement_selected)        
        wx.EVT_TEXT(self.control_panel.distance_cutoff_value,-1,self.on_derived_measurement_selected)  
        wx.EVT_TOGGLEBUTTON(self.control_panel.preview_prune_button,-1, self.on_toggle_preview_pruned_graph)
        wx.EVT_BUTTON(self.control_panel.add_pruning_to_edits_button,-1,self.on_add_pruning_to_edits)
        wx.EVT_BUTTON(self.control_panel.save_edited_tracks,-1, self.on_saved_edited_tracks)
            
    def on_show_all_trajectories(self, event = None):
        self.trajectory_selection = dict.fromkeys(self.connected_nodes[self.selected_dataset_track].keys(),1)
        self.do_plots_need_updating["trajectories"] = True
        self.update_plot()    

    def on_select_cell_by_index(self,event = None):
        # First, get the image key
        # Start with the table_id if there is one
        tblNum = None
        if props.table_id:
            dlg = wx.TextEntryDialog(self, props.table_id+':','Enter '+props.table_id)
            dlg.SetValue('0')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    tblNum = int(dlg.GetValue())
                except ValueError:
                    errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(props.table_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                    errdlg.ShowModal()
                    return
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
            
        # Then get the image_id
        dlg = wx.TextEntryDialog(self, props.image_id+':','Enter '+props.image_id)
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                imgNum = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(props.image_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
    
        # Then get the object_id
        dlg = wx.TextEntryDialog(self, props.object_id+':','Enter '+props.object_id)
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                objNum = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(props.object_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return        
        
        # Build the imkey
        if props.table_id:
            objectkey = (tblNum,imgNum,objNum)
        else:
            objectkey = (imgNum,objNum)
        
        self.selected_node = objectkey
        self.mayavi_view.on_select_point()
    
    def on_show_popup_menu(self, event = None):   
        '''
        Event handler: show the viewer context menu.  
        
        @param event: the event binder
        @type event: wx event
        '''
        class TrajectoryPopupMenu(wx.Menu):
            '''
            Build the context menu that appears when you right-click on a trajectory
            '''
            def __init__(self, parent):
                super(TrajectoryPopupMenu, self).__init__()
                
                self.parent = parent
                
                # Context menu entries
                # - Select cell using (ImageNumber,ObjectNumber)...
                # - Show selected cell (I,J) as
                #   - Image tile
                #   - Full image
                #   - Data table from selected trajectory                
                # - Define trajectory segment with cell (I,J) as
                #   - Endpoint #1
                #   - Endpoint #2
                #   - N frames before/after...
                #   - Entire trajectory
                # - Display defined trajectory segment as
                #   - Image montage
                #   - Plot of current measurement
                # - Show all trajectories
            
                # The 'Show data in table' item and its associated binding
                item = wx.MenuItem(self, wx.NewId(), "Select cell using object ID...")
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.parent.on_select_cell_by_index, item)
                
                if self.parent.selected_node is not None:
                    item = wx.Menu()
                    ID_SHOW_IMAGE_TILE = wx.NewId()
                    ID_SHOW_FULL_IMAGE = wx.NewId()
                    ID_DATA_TABLE = wx.NewId()
                    item.Append(ID_SHOW_IMAGE_TILE,"Image tile")
                    item.Append(ID_SHOW_FULL_IMAGE,"Full image")
                    item.Append(ID_DATA_TABLE,"Data table from selected trajectory")
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_tile,id=ID_SHOW_IMAGE_TILE)
                    self.Bind(wx.EVT_MENU, self.parent.show_full_image,id=ID_SHOW_FULL_IMAGE)    
                    self.Bind(wx.EVT_MENU, self.parent.show_selection_in_table,id=ID_DATA_TABLE)  
                    self.AppendSubMenu(item,"Show selected %s %s as"%(props.object_name[0],str(self.parent.selected_node)))    
                    
                    #if self.parent.selected_endpoints[0] != None:
                        #item = wx.MenuItem(self, wx.NewId(), "Make point furthest downstream of %s %s as endpoint"%(props.object_name[0],str(self.parent.selected_endpoints[0])))
                        #self.AppendItem(item)
                        #self.Bind(wx.EVT_MENU, self.parent.select_furthest_downstream_point, item)
                    
                    item = wx.Menu()
                    ID_SELECT_ENDPOINT1 = wx.NewId()
                    ID_SELECT_ENDPOINT2 = wx.NewId()
                    ID_SELECT_N_FRAMES = wx.NewId()
                    ID_SELECT_TRAJECTORY = wx.NewId()
                    item.Append(ID_SELECT_ENDPOINT1,"Endpoint #1")
                    item.Append(ID_SELECT_ENDPOINT2,"Endpoint #2")
                    item.Append(ID_SELECT_N_FRAMES,"N frames before/after...")
                    #item.Append(ID_SELECT_TRAJECTORY,"Entire trajectory")                 
                    self.Bind(wx.EVT_MENU, self.parent.select_endpoint1,id=ID_SELECT_ENDPOINT1)
                    self.Bind(wx.EVT_MENU, self.parent.select_endpoint2,id=ID_SELECT_ENDPOINT2)
                    self.Bind(wx.EVT_MENU, self.parent.select_n_frames,id=ID_SELECT_N_FRAMES)
                    self.Bind(wx.EVT_MENU, self.parent.select_entire_trajectory,id=ID_SELECT_TRAJECTORY)                    
                    self.AppendSubMenu(item,"Define trajectory segment with %s %s as"%(props.object_name[0],str(self.parent.selected_node)))
                    
                    item = wx.Menu()
                    are_endpoints_selected = all([_ != None for _ in self.parent.selected_endpoints])
                    ID_DISPLAY_MONTAGE = wx.NewId()
                    subItem = item.Append(ID_DISPLAY_MONTAGE,"Image montage")
                    # Apparently, there's no easy way to enable/disable a wx.Menu
                    # See: http://stackoverflow.com/questions/11576522/wxpython-disable-a-whole-menu
                    subItem.Enable(are_endpoints_selected)
                    ID_DISPLAY_GRAPH = wx.NewId()
                    subItem = item.Append(ID_DISPLAY_GRAPH,"Plot of currently selected measurement")
                    subItem.Enable(are_endpoints_selected)
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_montage,id=ID_DISPLAY_MONTAGE) 
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_measurement_plot,id=ID_DISPLAY_GRAPH)   
                    self.AppendSubMenu(item,"Display defined trajectory segment as")
                    
                # The 'Show all trajectories' item and its associated binding
                item = wx.MenuItem(self, wx.NewId(), "Show all trajectories")
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.parent.on_show_all_trajectories, item)

        # The event (mouse right-click) position.
        pos = event.GetPosition()
        # Converts the position to mayavi internal coordinates.
        pos = self.figure_panel.ScreenToClient(pos)                                                        
        # Show the context menu.      
        self.PopupMenu(TrajectoryPopupMenu(self), pos)    

    def show_selection_in_table(self, event = None):
        '''Callback for "Show selection in a table" popup item.'''
        keys = [self.connected_nodes[self.selected_dataset_track][item].nodes() for item in self.selected_trajectory]
        keys = [item for sublist in keys for item in sublist]
        tracking_label,timepoint,data = zip(*np.array([(self.directed_graph[self.selected_dataset_track].node[node]["label"],
                                                        self.directed_graph[self.selected_dataset_track].node[node]["t"],
                                                        self.directed_graph[self.selected_dataset_track].node[node][SCALAR_VAL]) for node in keys]))
        table_data = np.hstack((np.array(keys), np.array((tracking_label,timepoint,data)).T))
        column_labels = list(object_key_columns())
        key_col_indices = list(xrange(len(column_labels)))
        column_labels += ['Tracking Label','Timepoint ID',self.selected_measurement]
        group = 'Object'
        grid = tableviewer.TableViewer(self, title='Data table from trajectory %d containing %s %s'%(self.selected_trajectory[0],props.object_name[0],self.selected_node))
        grid.table_from_array(table_data, column_labels, group, key_col_indices)
        # Sort by label first, then by timepoint
        grid.grid.Table.set_sort_col(len(key_col_indices)+1)
        grid.grid.Table.set_sort_col(len(key_col_indices)+2,add=True) 
        # Hide the object key columns
        grid.grid.Table.set_shown_columns(list(xrange(len(key_col_indices),len(column_labels))))
        grid.grid.Table.ResetView(grid.grid)
        grid.set_fitted_col_widths()
        grid.Show()
        
    def select_endpoint1(self,event=None):
        self.selected_endpoints[0] = self.selected_node
        self.highlight_selected_endpoint(1)        
        
    def select_endpoint2(self,event=None):
        self.selected_endpoints[1] = self.selected_node
        self.highlight_selected_endpoint(2)
    
    def highlight_selected_endpoint(self, num):
        idx = num-1
        self.mayavi_view.trajectory_point_selection_outline[idx].mlab_source.dataset.points[0] = (np.mean(self.mayavi_view.trajectory_selection_outline.bounds[:2]),
                                                                                                  np.mean(self.mayavi_view.trajectory_selection_outline.bounds[2:4]),
                                                                                                  np.mean(self.mayavi_view.trajectory_selection_outline.bounds[4:]))
        self.mayavi_view.trajectory_point_selection_outline[idx].actor.actor.visibility = 1
        
        self.mayavi_view.lineage_point_selection_outline[idx].mlab_source.dataset.points[0] = (np.mean(self.mayavi_view.lineage_selection_outline.bounds[:2]),
                                                                                               np.mean(self.mayavi_view.lineage_selection_outline.bounds[2:4]),
                                                                                               0)
        self.mayavi_view.lineage_point_selection_outline[idx].actor.actor.visibility = 1  
    
    def select_n_frames(self, event = None):
        dlg = wx.TextEntryDialog(self, "Enter the number of frames before and after")
        dlg.SetValue('0')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                n_frames = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value', "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        if n_frames < 0:
            errdlg = wx.MessageDialog(self, 'Only positive values allowed', "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
            errdlg.ShowModal()
            return            
        
        trajectory_to_use = self.pick_trajectory_to_use()
        subgraph = self.connected_nodes[self.selected_dataset_track][trajectory_to_use]
        # Find all nodes within N frames. This includes nodes that occur after a branch so extra work is needed to figure out which path to follow
        nodes_within_n_frames = {n:length for n, length in nx.single_source_shortest_path_length(subgraph.to_undirected(),self.selected_node).items() if length <= n_frames}
        # Find the candidate terminal nodes @ N frames away (before/after)        
        sorted_nodes = sorted([(key,val,nodes_within_n_frames[key]) for key,val in nx.get_node_attributes(subgraph,'t').items() if key in nodes_within_n_frames.keys()],key=itemgetter(1))
        idx = sorted_nodes.index((self.selected_node,self.selected_node[0],0))
        # A node is at the start/end of the selection if: (1) it's N frames away, or (2) it's at the start/end of the trajectory branch
        start_nodes = [_ for _ in sorted_nodes if (_[2] == n_frames or subgraph.in_degree(_[0])  == 0) and _[1] <= sorted_nodes[idx][1] ]
        end_nodes =   [_ for _ in sorted_nodes if (_[2] == n_frames or subgraph.out_degree(_[0]) == 0) and _[1] >= sorted_nodes[idx][1] ]
        # If we have multiple candidates on either side, try to intelligently pick the right one
        if len(start_nodes) > 1 or len(end_nodes) > 1:
            bc = nx.get_node_attributes(subgraph,METRIC_BC)
            if len(start_nodes) > 1:
                # First, try to pick the furthest one away
                bounding_frame = sorted(start_nodes,key=itemgetter(2),reverse=True)[0][2]
                start_nodes = [_ for _ in start_nodes if _[2] == bounding_frame]
                if len(start_nodes) > 1: 
                    # If we still have multiple candidates, pick the one with the higher betweenness centrality score
                    temp = [bc[_[0]] for _ in start_nodes]
                    idx = temp.index(max(temp))  # If the betweenness centrality scores are equal, this picks the first one
                    start_nodes = start_nodes[idx][0] 
                else:
                    start_nodes = start_nodes[0][0]   
            else:
                start_nodes = start_nodes[0][0]
            if len(end_nodes) > 1:
                sorted_end_nodes = sorted(end_nodes,key=itemgetter(2),reverse=False)
                bounding_frame = sorted_end_nodes[-1][2]
                end_nodes = [_ for _ in end_nodes if _[2] == bounding_frame]
                if len(end_nodes) > 1:
                    temp = [bc[_[0]] for _ in end_nodes]
                    idx = temp.index(max(temp))
                    end_nodes = end_nodes[idx][0] 
                else:
                    end_nodes = end_nodes[0][0]
            else:
                end_nodes = end_nodes[0][0]
        
        self.selected_endpoints = [start_nodes, end_nodes]     
        self.highlight_selected_endpoint(1)
        self.highlight_selected_endpoint(2)        
         
    def select_entire_trajectory(self, event = None):
        trajectory_to_use = self.pick_trajectory_to_use()
        # TODO: Decide on proper behavior if selected node contains multiple end nodes. Use all end nodes? Use terminal nodes?
        self.selected_endpoints = [self.start_nodes[trajectory_to_use], self.end_nodes[trajectory_to_use]]
        self.highlight_selected_endpoint(1)
        self.highlight_selected_endpoint(2)
    
    def pick_trajectory_to_use(self, event = None):
        # Pick out the trajectory containing the selected node
        trajectory_to_use = [key for key, subgraph in self.connected_nodes[self.selected_dataset_track].items() if self.selected_node in subgraph]
        if len(trajectory_to_use) > 1:
            print "Should have only one trajectory selected"
            return [],[]
        else:
            trajectory_to_use = trajectory_to_use[0]    
        return trajectory_to_use
        
    def validate_node_ordering(self):
        trajectory_to_use = self.pick_trajectory_to_use()
            
        # Check the node ordering
        selected_endpoints = self.selected_endpoints if nx.has_path(self.directed_graph[self.selected_dataset_track], self.selected_endpoints[0],self.selected_endpoints[1]) else self.selected_endpoints[::-1]        
        return selected_endpoints, trajectory_to_use
    
    def show_cell_montage(self, event = None):
        # Check the node ordering
        selected_endpoints, trajectory_to_use = self.validate_node_ordering()

        current_trajectory_keys = nx.shortest_path(self.connected_nodes[self.selected_dataset_track][trajectory_to_use], selected_endpoints[0],selected_endpoints[1])
        montage_frame = sortbin.CellMontageFrame(get_main_frame_or_none(),"Image montage from trajectory %d containing %s %s and %s"%(trajectory_to_use, props.object_name[0],selected_endpoints[0],selected_endpoints[1] ))
        montage_frame.Show()
        montage_frame.add_objects(current_trajectory_keys)
        [tile.Select() for tile in montage_frame.sb.tiles if tile.obKey in selected_endpoints]
    
    def show_cell_measurement_plot(self, event = None):
        # Check the node ordering
        selected_endpoints, trajectory_to_use = self.validate_node_ordering()
        
        # Create new figure
        new_title = "Trajectory %d, %s %s and %s"%(trajectory_to_use, props.object_name[0],selected_endpoints[0],selected_endpoints[1])
        window = self.create_or_find(self, -1, new_title, subplots=(1,1), name=new_title)
        
        # Plot the selected measurement
        current_trajectory_keys = nx.shortest_path(self.connected_nodes[self.selected_dataset_track][trajectory_to_use], selected_endpoints[0],selected_endpoints[1])
        timepoint,data = zip(*np.array([(self.directed_graph[self.selected_dataset_track].node[node]["t"],
                                         self.directed_graph[self.selected_dataset_track].node[node][SCALAR_VAL]) 
                                        for node in current_trajectory_keys]))
        axes = window.figure.add_subplot(1,1,1)   
        
        axes.plot(timepoint, data)
        axes.set_xlabel("Timepoint")
        axes.set_ylabel(self.selected_measurement)                
    
    def show_cell_tile(self, event = None):
        montage_frame = sortbin.CellMontageFrame(get_main_frame_or_none(),"Image tile of %s %s"%(props.object_name[0],self.selected_node))
        montage_frame.Show()
        montage_frame.add_objects([self.selected_node])   
    
    def show_full_image(self, event = None):
        imViewer = imagetools.ShowImage(self.selected_node, props.image_channel_colors, parent=self)
        imViewer.imagePanel.SelectPoint(db.GetObjectCoords(self.selected_node))
    
    def on_dataset_selected(self, event = None):
        # Disable trajectory selection button until plot updated or the currently plotted dataset is selected
        self.do_plots_need_updating["dataset"] = False
        if self.selected_dataset == self.control_panel.dataset_choice.GetStringSelection():
            self.control_panel.trajectory_selection_button.Enable()
        else:
            self.control_panel.trajectory_selection_button.Disable()
            self.selected_dataset = self.control_panel.dataset_choice.GetStringSelection()
            self.do_plots_need_updating["dataset"] = True
            
    def on_dataset_measurement_selected(self, event = None):
        self.do_plots_need_updating["measurement"] = False
        if self.control_panel.dataset_measurement_choice.GetStringSelection() == OTHER_METRICS:
            [_.Enable() for _ in self.control_panel.all_derived_measurements_widgets]            
            self.on_derived_measurement_selected()
        else:
            [_.Disable() for _ in self.control_panel.all_derived_measurements_widgets]
        if self.selected_measurement == self.control_panel.dataset_measurement_choice.GetStringSelection():
            self.control_panel.trajectory_selection_button.Enable()
        else:
            self.selected_measurement = self.control_panel.dataset_measurement_choice.GetStringSelection()            
            self.control_panel.trajectory_selection_button.Disable()  
            self.do_plots_need_updating["measurement"] = True

    def on_derived_measurement_selected(self, event = None):
        self.selected_metric = self.control_panel.derived_measurement_choice.GetStringSelection() 
        # A couple more specific ones, until I get the hide/show thing working
        self.control_panel.distance_cutoff_value.Enable(self.selected_metric == METRIC_NODESWITHINDIST)
        self.control_panel.bc_branch_ratio_value.Enable(self.selected_metric == METRIC_BC) 
        self.do_plots_need_updating["measurement"] = True        
    
    def on_toggle_preview_pruned_graph(self, event=None):
        # Set the visibility of the nodes
        attr = nx.get_node_attributes(self.directed_graph[self.selected_dataset_track], VISIBLE)
        if self.control_panel.preview_prune_button.GetValue():
            # Set visibility based on the selected metric and trajectory selection
            for key,subgraph in self.connected_nodes[self.selected_dataset_track].items():
                is_currently_visible = self.trajectory_selection[key]              
                subattr = nx.get_node_attributes(subgraph, self.selected_metric+VISIBLE_SUFFIX)
                for _ in subattr.items():
                    attr[_[0]] = _[1] & is_currently_visible
        else:
            # Set visibility based on trajectory selection only
            for key,subgraph in self.connected_nodes[self.selected_dataset_track].items():
                is_currently_visible = self.trajectory_selection[key] 
                for _ in subgraph.nodes():
                    attr[_] = is_currently_visible      
        nx.set_node_attributes(self.directed_graph[self.selected_dataset_track], VISIBLE, attr)
        
        self.do_plots_need_updating["trajectories"] = True
        self.update_plot()
        
    def on_add_pruning_to_edits(self, event=None):
        attr = nx.get_node_attributes(self.directed_graph[self.selected_dataset_track], IS_REMOVED)
        for key,subgraph in self.connected_nodes[self.selected_dataset_track].items():
            subattr = nx.get_node_attributes(subgraph, self.selected_metric+VISIBLE_SUFFIX)
            for _ in subattr.items():
                attr[_[0]] = (not _[1]) or attr[_[0]]  # A node is removed if it's pruned (i.e, not visible) or it's already removed
        nx.set_node_attributes(self.directed_graph[self.selected_dataset_track], IS_REMOVED, attr)   
        dlg = wx.MessageDialog(self, "The selected pruning has been added to the list of trajectory edits. You can save the edits to the database by selecting the 'Save Edited Tracks' button", "Edits Added", wx.OK)
        dlg.ShowModal()
    
    def on_saved_edited_tracks(self, event = None):
        dlg = wx.TextEntryDialog(self, 'Specify a name for your edited tracks','Enter track identifier')
        dlg.SetValue('MyEditedTracks')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                # TODO: Validate text entry
                trackID = dlg.GetValue()
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value!', "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        # Create new table
        # TODO: Insert table creation here
        table_name = props.relationship_table+EDITED_TABLE_SUFFIX
        logging.info('Populating table %s...'%table_name)
        
        # Retrieve original relationship table
        obj = retrieve_object_name()
        colnames = ['image_number1', 'object_number1', 'image_number2', 'object_number2']
        query = ("SELECT %s FROM %s, %s i1 WHERE"%(",".join(colnames), props.relationships_view, props.image_table),) + \
                 where_stmt_for_tracked_objects(obj,props.group_id,int(self.selected_dataset)) 
        query = " ".join(query)  
        tableData = [_ for _ in db.execute(query)]
        # Create new column containing 1 if edge is kept, 0 if not
        newcol = len(tableData)*[1]
        attr = nx.get_node_attributes(self.directed_graph[self.selected_dataset_track], IS_REMOVED)
        for _ in attr.items():
            if _[1]:
                for successor in self.directed_graph[self.selected_dataset_track].successors_iter(_[0]):
                    newcol[tableData.index(_[0]+successor)] = 0
            
        tableData = np.hstack((np.array(tableData),np.array(newcol)[np.newaxis].T))
        colnames += [trackID]

        success = db.CreateTableFromData(tableData, colnames, table_name, temporary=False)
        
        # Update drop-down listing
        track_choices = self.control_panel.dataset_relationship_index.GetItems() + [trackID]
        self.control_panel.dataset_relationship_index.SetItems(track_choices)
        self.control_panel.dataset_relationship_index.SetSelection(track_choices.index(trackID))   
        self.control_panel.dataset_relationship_index.Enable()  
        
    def on_colormap_selected(self, event = None):
        self.do_plots_need_updating["colormap"] = False
        if self.selected_colormap != self.control_panel.colormap_choice.GetStringSelection():
            self.selected_colormap = self.control_panel.colormap_choice.GetStringSelection()    
            self.do_plots_need_updating["colormap"] = True
    
    #def on_filter_selected(self, event = None):
        #self.do_plots_need_updating["filter"] = []
        #for current_filter in self.control_panel.filter_panel.filters:
            #self.do_plots_need_updating["filter"].append(" ".join((current_filter.colChoice.GetStringSelection(), 
                                                                   #current_filter.comparatorChoice.GetStringSelection(),
                                                                   #current_filter.valueField.GetStringSelection())))
            
    def calculate_and_display_lap_stats(self, event = None):
        self.show_LAP_metrics()
    
    def update_trajectory_selection(self, event = None):
        
        class TrajectoryMultiChoiceDialog (wx.Dialog):
            '''
            Build the dialog box that appears when you click on the trajectory selection
            '''
            def __init__(self, parent, message="", caption="", choices=[]):
                wx.Dialog.__init__(self, parent, -1)
                self.SetTitle(caption)
                sizer1 = wx.BoxSizer(wx.VERTICAL)
                self.message = wx.StaticText(self, -1, message)
                self.clb = wx.CheckListBox(self, -1, choices = choices)
                self.selectallbtn = wx.Button(self,-1,"Select all")
                self.deselectallbtn = wx.Button(self,-1,"Deselect all")
                sizer2 = wx.BoxSizer(wx.HORIZONTAL)
                sizer2.Add(self.selectallbtn,0, wx.ALL | wx.EXPAND, 5)
                sizer2.Add(self.deselectallbtn,0, wx.ALL | wx.EXPAND, 5)
                self.dlgbtns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
                self.Bind(wx.EVT_BUTTON, self.SelectAll, self.selectallbtn)
                self.Bind(wx.EVT_BUTTON, self.DeselectAll, self.deselectallbtn)
                
                sizer1.Add(self.message, 0, wx.ALL | wx.EXPAND, 5)
                sizer1.Add(self.clb, 1, wx.ALL | wx.EXPAND, 5)
                sizer1.Add(sizer2, 0, wx.EXPAND)
                sizer1.Add(self.dlgbtns, 0, wx.ALL | wx.EXPAND, 5)
                self.SetSizer(sizer1)
                self.Fit()
                
            def GetSelections(self):
                return self.clb.GetChecked()
            
            def SetSelections(self, indexes):
                return self.clb.SetChecked(indexes)

            def SelectAll(self, event):
                for i in range(self.clb.GetCount()):
                    self.clb.Check(i, True)
                    
            def DeselectAll(self, event):
                for i in range(self.clb.GetCount()):
                    self.clb.Check(i, False)
        
        trajectory_selection_dlg = TrajectoryMultiChoiceDialog(self, 
                                                    message = 'Select the objects you would like to show',
                                                    caption = 'Select trajectories to visualize', 
                                                    choices = [str(x) for x in self.connected_nodes[self.selected_dataset_track].keys()])
                
        current_selection = np.nonzero(self.trajectory_selection.values())[0]
        trajectory_selection_dlg.SetSelections(current_selection)
        
        if (trajectory_selection_dlg.ShowModal() == wx.ID_OK):
            current_selection = trajectory_selection_dlg.GetSelections()
            all_labels = self.connected_nodes[self.selected_dataset_track].keys()
            self.trajectory_selection = dict.fromkeys(all_labels,0)
            for x in current_selection:
                self.trajectory_selection[all_labels[x]] = 1
            self.do_plots_need_updating["trajectories"] = True
            
            for key, value in self.trajectory_selection.items():
                for node_key in self.connected_nodes[self.selected_dataset_track][key]:
                    self.directed_graph[self.selected_dataset_track].node[node_key][VISIBLE] = (value != 0)
            # Alter lines between the points that we have previously created by directly modifying the VTK dataset.                
            nodes_to_remove = [self.connected_nodes[self.selected_dataset_track][key] for (key,value)in self.trajectory_selection.items() if value == 0]
            nodes_to_remove = [item for sublist in nodes_to_remove for item in sublist]
            
            mapping = dict(zip(sorted(self.directed_graph[self.selected_dataset_track]),
                               range(0,self.directed_graph[self.selected_dataset_track].number_of_nodes()+1)))
            nodes_to_remove = [mapping[item] for item in nodes_to_remove]
            self.altered_directed_graph = nx.relabel_nodes(self.directed_graph[self.selected_dataset_track], mapping, copy=True)
            self.altered_directed_graph.remove_nodes_from(nodes_to_remove)
            self.update_plot()                    
    
    def enable_filtering(self, event=None):
        if self.control_panel.enable_filtering_checkbox.GetValue():
            self.control_panel.filter_panel.Enable()
        else:
            self.control_panel.filter_panel.Disable()
    
    def update_plot(self, event=None):
        self.do_plots_need_updating["filter"] = self.control_panel.enable_filtering_checkbox.IsChecked()   
        self.generate_graph()
        self.mayavi_view.draw_trajectories(self.do_plots_need_updating, 
                                           self.directed_graph[self.selected_dataset_track], 
                                           self.connected_nodes[self.selected_dataset_track], 
                                           self.selected_colormap, 
                                           self.scalar_data)
        self.mayavi_view.draw_lineage(self.do_plots_need_updating, 
                                      self.directed_graph[self.selected_dataset_track], 
                                      self.connected_nodes[self.selected_dataset_track], 
                                      self.selected_colormap, 
                                      self.scalar_data )
        
        self.control_panel.trajectory_selection_button.Enable()
        
        self.do_plots_need_updating["dataset"] = False
        self.do_plots_need_updating["tracks"] = False
        self.do_plots_need_updating["colormap"] = False
        self.do_plots_need_updating["measurement"] = False
        self.do_plots_need_updating["trajectories"] = False
        
    def generate_graph(self):
        # Generate the graph relationship if the dataset has been updated
        
        if not self.do_plots_need_updating["filter"]:
            self.selected_filter = None
        else:
            self.selected_filter = []
            for current_filter in self.control_panel.filter_panel.filters:
                self.selected_filter.append(" ".join((props.object_table + "." + current_filter.colChoice.GetStringSelection(), 
                                                      current_filter.comparatorChoice.GetStringSelection(),
                                                      current_filter.valueField.GetValue())))
                
        column_names,trajectory_info,relationships = obtain_tracking_data(self.selected_dataset,
                                                            self.selected_dataset_track,
                                                            self.selected_measurement if self.selected_measurement in self.dataset_measurement_choices else None, 
                                                            self.selected_filter)
        
        if self.do_plots_need_updating["tracks"]: 
            if self.selected_dataset_track == ORIGINAL_TRACK:
                reln_index = len(relationships)*[1]
            else:
                reln_index = obtain_relationship_index(self.selected_dataset, self.selected_dataset_track)
        
        if len(trajectory_info) == 0:
            logging.info("No object data found")
            wx.MessageBox('The table %s referenced in the properties file contains no object information.'%props.object_table,
                          caption = "No data found",
                            parent = self.control_panel,
                            style = wx.OK | wx.ICON_ERROR)            
            return
        
        if self.do_plots_need_updating["dataset"]:           
            logging.info("Retrieved %d %s from dataset %s (%s)"%(len(trajectory_info),
                                                                 props.object_name[1],
                                                                 self.selected_dataset, 
                                                                 self.selected_dataset_track))
            
            self.directed_graph[self.selected_dataset_track] = nx.DiGraph()
            key_length = len(object_key_columns())
            indices = range(0,key_length)
            node_ids = map(itemgetter(*indices),trajectory_info)
            indices = range(key_length,key_length+2)
            parent_node_ids = map(itemgetter(*indices),trajectory_info) 
            indices = range(key_length+2,len(trajectory_info[0]))
            attr = [dict(zip(track_attributes,item)) for item in map(itemgetter(*indices),trajectory_info)]
            for _ in attr:
                _[VISIBLE] = True
                _[IS_REMOVED] = False
            
            # Add nodes
            self.directed_graph[self.selected_dataset_track].add_nodes_from(zip(node_ids,attr))
            # Add edges as list of tuples (exclude those that have no parent, i.e, (0,0))
            null_node_id = (0,0)
            # TODO: Check if this is faster
            # z = np.array(zip(parent_node_ids,node_ids))
            # index = np.all(z[:,0] != np.array(null_node_id),axis=1)
            # z = z[index,:]
            # self.directed_graph[self.selected_dataset_track].add_edges_from(zip([tuple(x) for x in z[:,0]],[tuple(x) for x in z[:,1]]))
            self.directed_graph[self.selected_dataset_track].add_edges_from([(parent,node) for (node,parent) in zip(node_ids,parent_node_ids) if parent != null_node_id])
            
            logging.info("Constructed graph consisting of %d nodes and %d edges"%(self.directed_graph[self.selected_dataset_track].number_of_nodes(),
                                                                                  self.directed_graph[self.selected_dataset_track].number_of_edges()))
            
            t1 = time.clock()
            G = nx.convert_node_labels_to_integers(self.directed_graph[self.selected_dataset_track],
                                                   first_label=0,
                                                   ordering="default")
            mapping = dict(zip(G.nodes(),self.directed_graph[self.selected_dataset_track].nodes()))
            glayout.layer_layout(G, level_attribute = "t")
            nx.relabel_nodes(G, mapping,copy=False) # Map back to original graph labels
            node_positions = dict(zip(G.nodes(),[[G.node[key]["t"],G.node[key]["y"]] for key in G.nodes()]))
            self.end_frame = end_frame = max(np.array(node_positions.values())[:,0])
            self.start_frame = start_frame = min(np.array(node_positions.values())[:,0])
            
            # Adjust the y-spacing between trajectories so it the plot is roughly square, to avoid nasty Mayavi axis scaling issues later
            # See: http://stackoverflow.com/questions/13015097/how-do-i-scale-the-x-and-y-axes-in-mayavi2
            xy = np.array([node_positions[key] for key in G.nodes()])
            scaling_y = 1.0/float(max(xy[:,1]) - min(xy[:,1]))*float(max(xy[:,0]) - min(xy[:,0]))
            for key in G.nodes(): node_positions[key][1] *= scaling_y
            
            self.lineage_node_positions = node_positions  
            nx.set_node_attributes(self.directed_graph[self.selected_dataset_track],L_TCOORD,dict(zip(node_positions.keys(), [item[0] for item in node_positions.values()])))
            nx.set_node_attributes(self.directed_graph[self.selected_dataset_track],L_YCOORD,dict(zip(node_positions.keys(), [item[1] for item in node_positions.values()])))         
            
            t2 = time.clock()
            logging.info("Computed lineage layout (%.2f sec)"%(t2-t1))
            
            # Each track gets its own indexed subgraph. Later operations to the graphs are referenced to this key.
            # According to http://stackoverflow.com/questions/18643789/how-to-find-subgraphs-in-a-directed-graph-without-converting-to-undirected-graph,
            #  weakly_connected_component_subgraphs maintains directionality
            #connected_nodes = nx.connected_component_subgraphs(self.directed_graph[self.selected_dataset_track].to_undirected())
            connected_nodes = tuple(nx.weakly_connected_component_subgraphs(self.directed_graph[self.selected_dataset_track]))
            self.connected_nodes[self.selected_dataset_track] = dict(zip(range(1,len(connected_nodes)+1),connected_nodes))
            
            # Set graph attributes
            for key,subgraph in self.connected_nodes[self.selected_dataset_track].items():
                # Set connect component ID in ful graph                
                nodes = subgraph.nodes()
                nx.set_node_attributes(self.directed_graph[self.selected_dataset_track], SUBGRAPH_ID, dict(zip(nodes,[key]*len(nodes))))
                
                # Find start/end nodes by checking for nodes with no outgoing/ingoing edges
                # Set end nodes
                out_degrees = subgraph.out_degree()
                # HT to http://stackoverflow.com/questions/9106065/python-list-slicing-with-arbitrary-indices
                #  for using itemgetter to slice a list using a list of indices
                idx = np.nonzero(np.array(out_degrees.values()) == 0)[0]
                # If 1 node is returned, it's a naked tuple instead of a tuple of tuples, so we have to extract the innermost element in this case
                end_nodes = itemgetter(*idx)(out_degrees.keys())
                end_nodes = list(end_nodes) if isinstance(end_nodes[0],tuple) else list((end_nodes,))
                attr = {_: False for _ in subgraph.nodes()}
                for _ in end_nodes:
                    attr[_] = True
                nx.set_node_attributes(subgraph, END_NODES, attr)
                
                # Set start nodes
                in_degrees = subgraph.in_degree()
                # Since it's a directed graph, I know that the in_degree result will have the starting node at index 0.
                #  So even if there are multiple nodes with in-degree 0, this approach will get the first one.
                #  HT to http://stackoverflow.com/a/13149770/2116023 for the index approach
                start_nodes = [in_degrees.keys()[in_degrees.values().index(0)]]   
                attr = {_: False for _ in subgraph.nodes()}
                for _ in start_nodes:
                    attr[_] = True   
                nx.set_node_attributes(subgraph, START_NODES, attr)
                
                # Set branchpoints
                idx = np.nonzero(np.array(out_degrees.values()) > 1)[0]
                branch_nodes = itemgetter(*idx)(out_degrees.keys()) if len(idx) > 0 else []
                if branch_nodes != []:
                    branch_nodes = list(branch_nodes) if isinstance(branch_nodes[0],tuple) else list((branch_nodes,))                
                attr = {_: False for _ in subgraph.nodes()}
                for _ in branch_nodes:
                    attr[_] = True                   
                nx.set_node_attributes(subgraph, BRANCH_NODES, attr)
                
                # Set terminal nodes
                idx = np.nonzero(np.array(subgraph.nodes())[:,0] == end_frame)[0]
                terminal_nodes = itemgetter(*idx)(subgraph.nodes()) if len(idx) > 0 else []  
                if terminal_nodes != []:
                    terminal_nodes = list(terminal_nodes) if isinstance(terminal_nodes[0],tuple) else list((terminal_nodes,))                 
                attr = {_: False for _ in subgraph.nodes()}
                for _ in terminal_nodes:
                    attr[_] = True    
                nx.set_node_attributes(subgraph, TERMINAL_NODES, attr)      

            # Calculate measurements created from existing measurments
            self.derived_measurements = self.add_derived_measurements()
            
            # Insert ref to derived measurements and update current selection
            measurement_choices = self.control_panel.dataset_measurement_choices + [OTHER_METRICS]
            current_measurement_choice = self.control_panel.dataset_measurement_choice.GetSelection() 
            self.control_panel.dataset_measurement_choice.SetItems(measurement_choices)
            self.control_panel.dataset_measurement_choice.SetSelection(current_measurement_choice)
            
            self.control_panel.derived_measurement_choice.SetItems(self.derived_measurements.keys())
            self.control_panel.derived_measurement_choice.SetSelection(0)
            
            # When visualizing a new dataset, select all trajectories by default
            self.trajectory_selection = dict.fromkeys(self.connected_nodes[self.selected_dataset_track].keys(),1)    
                
        else:
            key_length = len(object_key_columns())
            indices = range(0,key_length)
            if self.selected_measurement in self.dataset_measurement_choices:
                node_ids = map(itemgetter(*indices),trajectory_info)
                getitem = itemgetter(len(trajectory_info[0])-2) # Measurement values                
                attr = dict(zip(node_ids,[item for item in map(getitem,trajectory_info)]))        
            else:
                node_ids = sorted(self.directed_graph[self.selected_dataset_track])
                if self.selected_metric == METRIC_NODESWITHINDIST:
                    self.derived_measurements[self.selected_metric] = self.calc_n_nodes_from_branchpoint()
                attr = dict(zip(node_ids,self.derived_measurements[self.selected_metric]))
            nx.set_node_attributes(self.directed_graph[self.selected_dataset_track],SCALAR_VAL,attr)
            getitem = itemgetter(len(trajectory_info[0])-1) # Filter values
            attr = dict(zip(node_ids,[item for item in map(getitem,trajectory_info)])) 
            nx.set_node_attributes(self.directed_graph[self.selected_dataset_track],"f",attr)
            
        self.scalar_data = np.array([self.directed_graph[self.selected_dataset_track].node[key][SCALAR_VAL] for key in sorted(self.directed_graph[self.selected_dataset_track])]).astype(float)

    def calc_n_nodes_from_branchpoint(self):
        cutoff_dist_from_branch = self.control_panel.distance_cutoff_value.GetValue()
        end_nodes_for_pruning = {_: set() for _ in self.connected_nodes[self.selected_dataset_track].keys()}
        
        for (key,subgraph) in self.connected_nodes[self.selected_dataset_track].items():
            branch_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,BRANCH_NODES).items() if _[1]]
            terminal_nodes = [_[0] for _ in nx.get_node_attributes(subgraph, TERMINAL_NODES).items() if _[1]]
            if branch_nodes != []:
                for source_node in branch_nodes:
                    # Find out-degrees for all nodes within N nodes of branchpoint
                    out_degrees = subgraph.out_degree(nx.single_source_shortest_path_length(subgraph,
                                                                                            source_node,
                                                                                            cutoff_dist_from_branch).keys())
                    # Find all nodes for which the out-degree is 0 (i.e, all terminal nodes (leaves)) and not a terminal node (i.e, at end of movie)
                    branch_to_leaf_endpoints = [(source_node,path_node) for (path_node,degree) in out_degrees.items() if degree == 0 and path_node not in terminal_nodes]
                    if len(branch_to_leaf_endpoints) > 0:
                        for current_branch in branch_to_leaf_endpoints:
                            shortest_path = nx.shortest_path(subgraph,current_branch[0],current_branch[1]) 
                            shortest_path.remove(source_node) # Remove the intital branchpoint
                            # Skip this path if another branchpoint exists, since it will get caught later
                            if all(np.array(subgraph.out_degree(shortest_path).values()) <= 1): 
                                # Add nodes on the path from the branchpoint to the leaf
                                end_nodes_for_pruning[key].update(shortest_path)     
            
            # Set identity attributes
            attr = {_: False for _ in subgraph.nodes()}
            for _ in list(end_nodes_for_pruning[key]):
                attr[_] = True
            nx.set_node_attributes(subgraph,METRIC_NODESWITHINDIST,attr)
            # Set visibility attributes
            attr = {_: True for _ in subgraph.nodes()}
            for _ in list(end_nodes_for_pruning[key]):
                attr[_] = False
            nx.set_node_attributes(subgraph,METRIC_NODESWITHINDIST_VISIBLE,attr)            
    
        sorted_nodes = sorted(self.directed_graph[self.selected_dataset_track])

        temp_full_graph_dict =  {_: 0.0 for _ in self.directed_graph[self.selected_dataset_track].nodes()}
        for key, nodes in end_nodes_for_pruning.items():
            l = list(end_nodes_for_pruning[key])
            for ii in l:
                temp_full_graph_dict[ii] = 1.0
        
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes]).astype(float)
        
    def calc_singletons(self):
        sorted_nodes = sorted(self.directed_graph[self.selected_dataset_track])
        temp_full_graph_dict = {_: 0.0 for _ in self.directed_graph[self.selected_dataset_track].nodes()}
        for (key,subgraph) in self.connected_nodes[self.selected_dataset_track].items():
            start_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,START_NODES).items() if _[1]]
            end_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,END_NODES).items() if _[1]]
            singletons = list(set(start_nodes).intersection(set(end_nodes)))
            
            # Set identity attributes
            attr = {_: False for _ in subgraph.nodes()}
            for _ in singletons:
                attr[_] = True
            nx.set_node_attributes(subgraph,METRIC_SINGLETONS,attr)  
            # Set visibility attribute 
            attr = {_: True for _ in subgraph.nodes()}
            for _ in singletons:
                attr[_] = False            
            nx.set_node_attributes(subgraph,METRIC_SINGLETONS_VISIBLE,attr)
            
            if len(singletons) == 1:
                temp_full_graph_dict[list(singletons)[0]] = 1.0
                
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes]).astype(float)     
                
    def calc_betweenness_centrality(self):
        # Suggested by http://stackoverflow.com/questions/18381187/functions-for-pruning-a-networkx-graph/23601809?iemail=1&noredirect=1#23601809
        # nx.betweenness_centrality: http://networkx.lanl.gov/reference/generated/networkx.algorithms.centrality.betweenness_centrality.html
        # Betweenness centrality of a node v is the sum of the fraction of all-pairs shortest paths that pass through v:
        
        sorted_nodes = sorted(self.directed_graph[self.selected_dataset_track])
        temp_full_graph_dict = {_: 0.0 for _ in self.directed_graph[self.selected_dataset_track].nodes()}
        for key,subgraph in self.connected_nodes[self.selected_dataset_track].items():
            attr = {_: 0.0 for _ in subgraph.nodes()}
            betweenness_centrality = nx.betweenness_centrality(subgraph, normalized=True)
            for (node,value) in betweenness_centrality.items():
                temp_full_graph_dict[node] = value
                attr[node] = value
            # Set identity attributes
            nx.set_node_attributes(subgraph, METRIC_BC, attr)
            # Set visibility attribute 
            # TODO: Come up with a heuristic to determine which branch to prune based on this value 
            attr = {_: True for _ in subgraph.nodes()}
            branch_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,BRANCH_NODES).items() if _[1]]
            for bn in branch_nodes:
                successors = subgraph.successors(bn)
                bc_vals = [betweenness_centrality[_] for _ in successors]
                cutoff = 1.0/len(bc_vals)/2.0 # Set to ????
                idx = np.argwhere(np.array(bc_vals)/sum(bc_vals) < cutoff)
                # Find all downstream nodes for branches that failed the cutoff
                for i in idx:
                    nodes = nx.single_source_shortest_path(subgraph,successors[i]).keys()
                    for _ in nodes:
                        attr[_] = False
            nx.set_node_attributes(subgraph, METRIC_BC_VISIBLE, attr)
        
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes ]).astype(float)      
                
    def add_derived_measurements(self):
        logging.info("Calculating derived measurements")
                    
        t1 = time.clock()   
        # TODO: Allow for user choice to add derived measurements
        # TODO: Figure out where to best store this information: as a graph attrubute, subgraph attribute, or a separate matrix
        # Create dict for QC measurements derived from graph properities
        derived_measurements = {}      
                    
        # Find branchpoints and nodes with a distance threshold from them (for later pruning if desired)
        derived_measurements[METRIC_NODESWITHINDIST] = self.calc_n_nodes_from_branchpoint()
        
        # Singletons: Subgraphs for which the start node = end node
        derived_measurements[METRIC_SINGLETONS] = self.calc_singletons()

        # Betweeness centrality:  measure of a node's centrality in a network
        derived_measurements[METRIC_BC] = self.calc_betweenness_centrality()
        
        t2 = time.clock()
        logging.info("Computed derived measurements (%.2f sec)"%(t2-t1))    
        
        return derived_measurements
        
    def find_fig(self, parent=None, title="", name=wx.FrameNameStr, subplots=None):
        """Find a figure frame window. Returns the window or None"""
        if parent:
            window = parent.FindWindowByName(name)
            if window:
                if len(title) and title != window.Title:
                    window.Title = title
                window.figure.clf()
            return window    

    def create_or_find(self, parent=None, id=-1, title="", 
                       pos=wx.DefaultPosition, size=wx.DefaultSize,
                       style=wx.DEFAULT_FRAME_STYLE, name=wx.FrameNameStr,
                       subplots=None,
                       on_close=None):
        """Create or find a figure frame window"""
        win = self.find_fig(parent, title, name, subplots)
        return win or FigureFrame(parent, id, title, pos, size, style, name, 
                                    subplots, on_close)    
    def show_LAP_metrics(self):
        # See http://cshprotocols.cshlp.org/content/2009/12/pdb.top65.full, esp. Figure 5
        # Create new figure
        new_title = "LAP diagnostic metrics"
        window = self.create_or_find(self, -1, new_title, subplots=(2,1), name=new_title)
        
        # Plot the frame-to-frame linking distances
        dists = self.calculate_frame_to_frame_linking_distances() 
        title = "Frame-to-frame linking distances"
        axes = window.figure.add_subplot(2,2,1)   
        
        axes = window.figure.add_subplot(2,2,1) 
        axes.set_axis_off()
        axes.text(0.0,0.0,
                  "Frame-to-frame linking distances\n"
                  "are the distances between the\n"
                  "predicted position of an object\n"
                  "and the observed position. This\n"
                  "data is displayed as a histogram\n"
                  "and should decay to zero.\n\n"
                  "The arrow indicates the pixel\n"
                  "distance at which 95%% of the\n"
                  "maximum number of links were\n"
                  "made. You should confirm that\n"
                  "this value is less than the\n"
                  "maximum search radius in the\n"
                  "%s module."%TRACKING_MODULE_NAME)
        axes = window.figure.add_subplot(2,2,2)        
        if dists.shape[0] == 0:
            plot = axes.text(0.0, 1.0, "No valid values to plot.")
            axes.set_axis_off()  
        else:
            bins = np.arange(0, np.max(dists))
            n, _, _ = axes.hist(dists, bins,
                          edgecolor='none',
                          alpha=0.75)
            max_search_radius = bins[n < 0.05*np.max(n)][0]
            axes.annotate('95%% of max count: %d pixels'%(max_search_radius),
                          xy=(max_search_radius,n[n < 0.05*np.max(n)][0]), 
                          xytext=(max_search_radius,axes.get_ylim()[1]/2), 
                          arrowprops=dict(facecolor='red', shrink=0.05))
            axes.set_xlabel('Frame-to-frame linking distances (pixels)')
            #axes.set_xlim((0,np.mean(dists) + 2*np.std(dists)))
            axes.set_ylabel('Counts')        
        
        # Plot the gap lengths
        axes = window.figure.add_subplot(2,2,3) 
        axes.set_axis_off()
        axes.text(0.0,0.0,
                  "Gap lengths are displayed as\n"
                  "a histogram. A plateau in the\n"
                  "tail of the histogram \n"
                  "indicates that the time window\n"
                  "used for gap closing is too \n"
                  "large, resulting in falsely \n"
                  "closed gaps.\n\n"
                  "If all the gap lengths are 1,\n"
                  "no data is shown since gap\n"
                  "closing was not necessary.")        
        values = np.array(self.calculate_gap_lengths()).flatten()
        values = values[np.isfinite(values)] # Just in case
        title = "Gap lengths"
        axes = window.figure.add_subplot(2,2,4)        
        if values.shape[0] == 0:
            plot = axes.text(0.1, 0.5, "No valid values to plot.")
            axes.set_axis_off()  
        elif np.max(values) == 1:
            plot = axes.text(0.1, 0.5, "No gap lengths > 1")
            axes.set_axis_off()              
        else:
            bins = np.arange(1, np.max(values)+1)
            axes.hist(values, bins,
                      facecolor=(0.0, 0.62, 1.0),
                      edgecolor='none',
                      alpha=0.75)
            axes.set_xlabel('Gap length (frames)')
            axes.set_ylabel('Counts')
        
        # Draw the figure
        window.figure.canvas.draw()
    
    def calculate_gap_lengths(self):
        obj = retrieve_object_name()
        
        query = ("SELECT",
                 "ABS(i2.%s - i1.%s)"%(props.timepoint_id, props.timepoint_id),
                 "FROM %s r"%(props.relationships_view),  
                 "JOIN %s i1"%(props.image_table),
                 "ON r.image_number1 = i1.%s"%(props.image_id),
                 "JOIN %s i2"%(props.image_table),
                 "ON r.image_number2 = i2.%s"%(props.image_id),
                 "WHERE") + \
                 where_stmt_for_tracked_objects(obj,props.group_id,int(self.selected_dataset)) 
        query = " ".join(query)
        return(np.array([_ for _ in db.execute(query)]))
    
    def calculate_frame_to_frame_linking_distances(self):
        #What's recorded in the database for each object are the values necessary to predict the 
        # location of the object in the next frame. There are two models applicable in TrackObjects: Random (NoVel) and Velocity (Vel)
        # For the Velocity model, you have to add Kalman_State_Vel_X and Kalman_State_Vel_VX and similarly for Y to get the 
        # predicted (X,Y) position. 
        # For NoVel, it's Kalman_State_NoVel_X and Kalman_State_NoVel_Y that gives the predicted (X,Y) position.
        # The error in distance between the observed location and the predicted location is calculated depending on which 
        # the user picked in TrackObjects (usually both) and the appropriate model is picked on a per-object basis as the
        # minimum of the two.
        obj = retrieve_object_name()
        prefix = "_".join((obj,TRACKING_MODULE_NAME))
        if props.db_type == 'sqlite':
            query = "PRAGMA table_info(%s)"%(props.object_table)
            used_velocity_model = len([item[1] for item in db.execute(query) if item[1].find('_Kalman_Vel_') > 0]) > 0    
            used_novelocity_model = len([item[1] for item in db.execute(query) if item[1].find('_Kalman_NoVel_') > 0]) > 0  
        else:
            query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP '_Kalman_Vel_'"%(props.db_name, props.object_table)
            used_velocity_model = db.execute(query)[0][0] > 0
            query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP '_Kalman_NoVel_'"%(props.db_name, props.object_table)
            used_novelocity_model = db.execute(query)[0][0] > 0
        # SQL courtesy of Lee. 
        query = ("SELECT",
                 "pred.pred_vel_x, pred.pred_vel_y, pred.pred_novel_x, pred.pred_novel_y, obs.%s_Location_Center_X, obs.%s_Location_Center_Y"%(obj,obj),
                 "FROM %s r"%(props.relationships_view),
                 "JOIN",
                 "(SELECT %s AS ImageNumber, %s AS ObjectNumber,"%(props.image_id, props.object_id),
                 "(%s_Kalman_Vel_State_X + %s_Kalman_Vel_State_VX)"%(prefix,prefix) if used_velocity_model else "NULL","AS pred_vel_x,",
                 "(%s_Kalman_Vel_State_Y + %s_Kalman_Vel_State_VY)"%(prefix,prefix) if used_velocity_model else "NULL","AS pred_vel_y,",
                 "%s_Kalman_NoVel_State_X AS pred_novel_x, %s_Kalman_NoVel_State_Y"%(prefix,prefix) if used_novelocity_model else "NULL","AS pred_novel_y",
                 "FROM %s) AS pred ON r.image_number1 = pred.ImageNumber AND r.object_number1 = pred.ObjectNumber"%(props.object_table),
                 "JOIN %s AS obs ON r.image_number2 = obs.%s AND r.object_number2 = obs.%s"%(props.object_table, props.image_id, props.object_id),
                 "JOIN %s AS i1 ON r.image_number1 = i1.%s"%(props.image_table, props.image_id),
                 "JOIN %s AS i2 ON r.image_number2 = i2.%s"%(props.image_table, props.image_id),
                 "WHERE i1.%s + 1 = i2.%s"%(props.timepoint_id,props.timepoint_id),
                 "AND i1.%s = i2.%s"%(props.group_id,props.group_id),
                 "AND") + \
            where_stmt_for_tracked_objects(obj,props.group_id,int(self.selected_dataset)) 
        query = " ".join(query)
        values = np.array(db.execute(query))
        # I would love to do this arithmetic in the query, but SQLite doesn't handle SQRT or POW
        dist_error_novel = np.sqrt((values[:,2]-values[:,4])**2 + (values[:,3]-values[:,5])**2)
        dist_error_vel = np.sqrt((values[:,0]-values[:,4])**2 + (values[:,1]-values[:,5])**2)
        # Return the minimum of the two models for each object/timepoint
        return(np.min(np.vstack((dist_error_novel,dist_error_vel)),axis=0))
        
    
################################################################################
if __name__ == "__main__":
        
    import sys
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)
    
    props = Properties.getInstance()

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        props.LoadFile(propsFile)
        props = add_props_field(props)
    else:
        if not props.show_load_dialog():
            print 'Time Visualizer requires a properties file.  Exiting.'
            # Necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()
        else:
            props = add_props_field(props)
            
    timelapsevisual = TimeLapseTool(None)
    timelapsevisual.Show()

    app.MainLoop()
    
    #
    # Kill the Java VM
    #
    try:
        from bioformats import jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
