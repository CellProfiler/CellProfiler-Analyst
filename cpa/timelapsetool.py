'''
Dependencies:
NetworkX: http://www.lfd.uci.edu/~gohlke/pythonlibs/#networkx
PyGraphviz: http://www.lfd.uci.edu/~gohlke/pythonlibs/#pygraphviz
Graphviz 2.28, from here: http://www.graphviz.org/pub/graphviz/stable/windows/

To get PyGraphViz working with PyGraphviz, needed to do the following:
* Use DOS-paths in Graphviz installation, i.e., C:\Progra~2\ instead of C:\Program Files (x86)\
* No spaces in Graphviz folder, i.e, .\Graphviz\ instead of .\Graphviz 2.28\
* Add Graphviz bin folder to Windows path
otherwise will get error msg "Program dot not found in path."
'''
import wx
from wx.combo import OwnerDrawnComboBox as ComboBox
import networkx as nx
import numpy as np
#import matplotlib
#matplotlib.use('WXAgg')

#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
#from matplotlib import pyplot, rcParams
#rcParams['font.size'] = 10

import logging
import time
import sortbin
from guiutils import get_main_frame_or_none
from dbconnect import DBConnect, image_key_columns, object_key_columns
from properties import Properties
from cpatool import CPATool
import tableviewer

# traits imports
from traits.api import HasTraits, Instance
from traitsui.api import View, Item, HSplit, Group

# mayavi imports
from mayavi import mlab
from mayavi.core.ui.api import MlabSceneModel, SceneEditor
from tvtk.pyface.scene import Scene
from tvtk.api import tvtk

# Modiying sys.path doesn't seem to work for some reason; b/c it's the search path for *modules*?
#import sys
#sys.path.append("C:\\Progra~2\\Graphviz\\bin") 
import os
os.environ["PATH"] = os.environ["PATH"] + ";C:\\Progra~2\\Graphviz\\bin" 

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

props = Properties.getInstance()
# Temp declarations; these will be retrieved from the properties file directly
#props.series_id = ["Image_Group_Number"]
props.series_id = ["Image_Metadata_Plate"]
props.group_id = "Image_Group_Number"
props.timepoint_id = "Image_Group_Index"
props.object_tracking_label = "Nuclei_TrackObjects_Label"

required_fields = ['series_id', 'group_id', 'timepoint_id','object_tracking_label']

db = DBConnect.getInstance()

def retrieve_datasets():
    series_list = ",".join(props.series_id)
    all_datasets = [x[0] for x in db.execute("SELECT %s FROM %s GROUP BY %s"%(series_list,props.image_table,series_list))]
    return all_datasets

def retrieve_trajectories(selected_dataset, selected_feature):
    def parse_dataset_selection(s):
        return [x.strip() for x in s.split(',') if x.strip() is not '']
    
    all_datasets = retrieve_datasets()
    selection_list = parse_dataset_selection(selected_dataset)
    dataset_clause = " AND ".join(["I.%s = '%s'"%(x[0], x[1]) for x in zip(props.series_id, selection_list)])
    all_labels = [x[0] for x in db.execute("SELECT DISTINCT(O.%s) FROM %s as I, %s as O WHERE I.%s = O.%s AND %s"%(
        props.object_tracking_label, props.image_table, props.object_table, props.image_id, props.image_id, dataset_clause))]
    trajectory_info = dict( (x,{"db_key":[],"x":[],"y":[],"t":[],"s":[]}) for x in all_labels ) # Wanted to use fromkeys, but it leads to incorrect behavior since it passes by reference not by value
    locations = db.execute("SELECT O.%s, O.%s, O.%s, O.%s, O.%s, I.%s, O.%s FROM %s AS I, %s as O WHERE I.%s = O.%s AND %s ORDER BY O.%s, I.%s"%(
                props.object_tracking_label, props.image_id, props.object_id, props.cell_x_loc, props.cell_y_loc, props.timepoint_id, selected_feature, props.image_table, props.object_table, props.image_id, props.image_id, dataset_clause, props.object_tracking_label, props.timepoint_id))
    for loc in locations:
        trajectory_info[loc[0]]["db_key"].append((loc[1],loc[2]))
        trajectory_info[loc[0]]["x"].append(loc[3])
        trajectory_info[loc[0]]["y"].append(loc[4])
        trajectory_info[loc[0]]["t"].append(loc[5])
        trajectory_info[loc[0]]["s"].append(loc[6])
    return trajectory_info

################################################################################
class TimeLapseControlPanel(wx.Panel):
    '''
    A panel with controls for selecting the data for a visual
    '''

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)

        # Get names of data sets
        all_datasets = retrieve_datasets()

        # Get names of fields
        measurements = db.GetColumnNames(props.object_table)
        coltypes = db.GetColumnTypes(props.object_table)
        fields = [m for m,t in zip(measurements, coltypes) if t in [float, int, long]]

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Define widgets
        self.dataset_choice = ComboBox(self, -1, choices=[str(i) for i in all_datasets], size=(200,-1), style=wx.CB_READONLY)
        self.dataset_choice.Select(0)
        self.feature_choice = ComboBox(self, -1, choices=fields, style=wx.CB_READONLY)
        self.feature_choice.Select(0)
        self.colormap_choice = ComboBox(self, -1, choices=all_colormaps, style=wx.CB_READONLY)
        self.colormap_choice.SetStringSelection("jet") 
        self.trajectory_selection_button = wx.Button(self, -1, "Select Tracks to Visualize...")
        self.update_plot_button = wx.Button(self, -1, "Update")

        # Arrange widgets
        # Row #1: Dataset drop-down + track selection button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Data source:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.dataset_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.trajectory_selection_button)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        # Row #2: Feature selection, colormap, update button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Measurement:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.feature_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Colormap:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.colormap_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.update_plot_button)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        self.SetSizer(sizer)
        self.Show(True)

   
################################################################################
class MayaviView(HasTraits):
    """ Create a mayavi scene"""
    lineage_scene = Instance(MlabSceneModel, ())
    trajectory_scene = Instance(MlabSceneModel, ())
    
    # The layout of the dialog created
    view = View(HSplit(Group(Item('trajectory_scene',
                                  editor = SceneEditor(scene_class = Scene),
                                  #width=480, height=480,
                                  resizable=True, show_label=False)),
                       Group(Item('lineage_scene',
                                  editor = SceneEditor(scene_class = Scene),
                                  #width=480, height=480,
                                  resizable=True, show_label=False))),
                resizable=True)

    def __init__(self):
        HasTraits.__init__(self)

################################################################################
class TimeLapseTool(wx.Frame, CPATool):
    '''
    A time-lapse visual plot with its controls.
    '''
    def __init__(self, parent, size=(1000,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Time-Lapse Tool', **kwargs)
        CPATool.__init__(self)
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

        self.control_panel = TimeLapseControlPanel(self)
        self.selected_dataset = self.control_panel.dataset_choice.GetStringSelection()
        self.selected_colormap  = self.control_panel.colormap_choice.GetStringSelection()
        self.plot_updated = False
        self.trajectory_selected = False
        self.selected_node = None
        
        self.mayavi_view = MayaviView()
        self.figure_panel = self.mayavi_view.edit_traits(
                                            parent=self,
                                            kind='subpanel').control 
        self.generate_graph(True)
        self.draw_lineage(True)
        self.draw_trajectories(True)
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.figure_panel, 1, wx.EXPAND)
        sizer.Add(self.control_panel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        
        self.figure_panel.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
        
        # Define events
        wx.EVT_COMBOBOX(self.control_panel.dataset_choice, -1, self.on_dataset_selected)
        wx.EVT_COMBOBOX(self.control_panel.feature_choice, -1, self.on_feature_selected)
        wx.EVT_BUTTON(self.control_panel.trajectory_selection_button, -1, self.update_trajectory_selection)
        wx.EVT_BUTTON(self.control_panel.colormap_choice, -1, self.on_colormap_selected)
        wx.EVT_BUTTON(self.control_panel.update_plot_button, -1, self.update_plot)
        
    def on_show_all_trajectories(self, event = None):
        all_labels = self.trajectory_info.keys()
        self.trajectory_selection = dict.fromkeys(all_labels,1)
        self.update_plot()    

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
            
                # The 'Show data in table' item and its associated binding
                if self.parent.selected_node is not None:
                    item = wx.MenuItem(self, wx.NewId(), "Show data containing %s %s in table"%(props.object_name[0],str(self.parent.selected_node)))
                    self.AppendItem(item)
                    self.Bind(wx.EVT_MENU, self.parent.show_selection_in_table, item)
                    item = wx.MenuItem(self, wx.NewId(), "Show image montage containing %s %s"%(props.object_name[0],str(self.parent.selected_node)))
                    self.AppendItem(item)
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_montage, item)                    
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
        containing_trajectory = [i for i in self.connected_nodes if self.selected_node in i][0]
        keys, ypoints, xpoints, data = zip(*[[self.directed_graph.node[i]["db_key"],i[0],i[1],self.directed_graph.node[i]["s"]] for i in containing_trajectory])
        table_data = np.hstack((np.array(keys), np.array((xpoints,ypoints,data)).T))
        column_labels = list(object_key_columns())
        key_col_indices = list(xrange(len(column_labels)))
        column_labels += [props.object_tracking_label,props.timepoint_id,self.selected_feature]
        group = 'Object'
        grid = tableviewer.TableViewer(self, title='Trajectory data containing %s %d'%(props.object_name[0],self.selected_node[0]))
        grid.table_from_array(table_data, column_labels, group, key_col_indices)
        # TODO: Confirm that hiding the key columns is actually neccesary. Also, an error gets thrown when the user tries to scrool horizontally.
        grid.grid.Table.set_shown_columns(list(xrange(len(key_col_indices),len(column_labels))))
        grid.set_fitted_col_widths()
        grid.Show()
        
    def show_cell_montage(self, event = None):
        containing_trajectory = [i for i in self.connected_nodes if self.selected_node in i][0]
        keys = [self.directed_graph.node[i]["db_key"] for i in containing_trajectory]
        montage_frame = sortbin.CellMontageFrame(get_main_frame_or_none(),"Image montage containing %s %d"%(props.object_name[0],self.selected_node[0]))
        montage_frame.Show()
        montage_frame.add_objects(keys)
        [tile.Select() for tile in montage_frame.sb.tiles if tile.obKey == self.directed_graph.node[self.selected_node]["db_key"]]
    
    def on_dataset_selected(self, event = None):
        # Disable trajectory selection button until plot updated or the currently plotted dataset is selected
        if self.selected_dataset == self.control_panel.dataset_choice.GetStringSelection() or self.plot_updated :
            self.control_panel.trajectory_selection_button.Enable()
        else:
            self.control_panel.trajectory_selection_button.Disable()   
            
    def on_feature_selected(self, event = None):
        if self.selected_feature == self.control_panel.feature_choice.GetStringSelection() or self.plot_updated :
            self.control_panel.trajectory_selection_button.Enable()
        else:
            self.control_panel.trajectory_selection_button.Disable()            

    def on_colormap_selected(self, event = None):
        self.selected_colormap = self.control_panel.colormap_choice.GetStringSelection()    
        
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
                                                    choices = [str(x) for x in self.trajectory_info.keys()])
                
        current_selection = np.nonzero(self.trajectory_selection.values())[0]
        trajectory_selection_dlg.SetSelections(current_selection)
        
        if (trajectory_selection_dlg.ShowModal() == wx.ID_OK):
            current_selection = trajectory_selection_dlg.GetSelections()
            all_labels = self.trajectory_info.keys()
            self.trajectory_selection = dict.fromkeys(all_labels,0)
            for x in current_selection:
                self.trajectory_selection[all_labels[x]] = 1
            self.update_plot()                    
    
    def update_plot(self, event = None):
        self.generate_graph(False)
        self.draw_lineage(False)
        self.draw_trajectories(False)
        self.control_panel.trajectory_selection_button.Enable()    
            
    def generate_graph(self, init = False):
        # Generate data
        changed_dataset = self.selected_dataset != self.control_panel.dataset_choice.GetStringSelection()
        self.selected_dataset = self.control_panel.dataset_choice.GetStringSelection()
        self.selected_feature = self.control_panel.feature_choice.GetStringSelection()
        self.selected_colormap = self.control_panel.colormap_choice.GetStringSelection()
        
        if init:
            self.trajectory_info = retrieve_trajectories(self.selected_dataset,self.selected_feature) # switch to dict() later
            self.trajectory_selection = dict.fromkeys(self.trajectory_info.keys(),1)
        else:
            self.trajectory_info = retrieve_trajectories(self.selected_dataset,self.selected_feature)
            if changed_dataset:
                self.trajectory_selection = dict.fromkeys(self.trajectory_info.keys(),1)    # Taken from http://docs.enthought.com/mayavi/mayavi/auto/example_plotting_many_lines.html
    
        logging.info("Retrieved %d %s from dataset %s"%(len(self.trajectory_info.keys()),props.object_name[1],self.selected_dataset))
        
        self.directed_graph = nx.DiGraph()
        # Same approach as for Mayavi viz
        # TODO(?): Integrate this approach into graph construction to streamline things
        for current_object in self.trajectory_info.keys():
            
            x = self.trajectory_info[current_object]["x"]
            y = self.trajectory_info[current_object]["y"]
            t = self.trajectory_info[current_object]["t"]
            s = self.trajectory_info[current_object]["s"]
            k = self.trajectory_info[current_object]["db_key"]
            
            ## Trying to streamline graph creation: Add nodes all at once
            #node_ids = zip(len(t)*[current_object],t)
            #node_dict = [{"x":attr[0],"y":attr[1],"t":attr[2],"l":current_object,"s":attr[3],"db_key":attr[4]} for attr in zip(x,y,t,s,k)]
            #self.directed_graph.add_nodes_from(zip(node_ids,node_dict))
            ## TODO: Trying to streamline graph creation: Add edges all at once
            #if len(node_ids) > 1:
                #self.directed_graph.add_edges_from(zip(node_ids[:-2],node_ids[1:]))
    
            x0,y0,t0,s0,k0 = x[0],y[0],t[0],s[0],k[0]
            prev_node_id = (current_object,t0)
            self.directed_graph.add_node(prev_node_id, x=x0, y=y0, t=t0, s=s0, l=current_object,db_key=k0)
            for x0,y0,t0,s0,k0 in zip(x[1:],y[1:],t[1:],s[1:],k[1:]):
                curr_node_id = (current_object,t0)
                self.directed_graph.add_node(curr_node_id, x=x0, y=y0, t=t0, s=s0, l=current_object, db_key=k0)
                self.directed_graph.add_edge(prev_node_id, curr_node_id)
                prev_node_id = curr_node_id
            
        # Find start/end nodes by checking for nodes with no outgoing edges
        start_nodes = [n for (n,d) in self.directed_graph.in_degree_iter() if (d == 0)]
        end_nodes = [n for (n,d) in self.directed_graph.out_degree_iter() if (d == 0)]
        #self.simplified_directed_graph = self.directed_graph.copy()
        #self.simplified_directed_graph = self.simplified_directed_graph.remove_nodes_from(set(self.directed_graph.nodes()).difference(start_nodes+end_nodes))
        logging.info("Constructed lineage graph consisting of %d nodes and %d edges"%(self.directed_graph.number_of_nodes(),self.directed_graph.number_of_edges()))
        
        # Hierarchical graph creation: http://stackoverflow.com/questions/11479624/is-there-a-way-to-guarantee-hierarchical-output-from-networkx        
        # Call graphviz to generate the node positional information
        t1 = time.clock()
        node_positions = nx.graphviz_layout(self.directed_graph, prog='dot') 
        t2 = time.clock()
        logging.info("Computed lineage layout (%.2f sec)"%(t2-t1))
        
        # TODO(?): Check into whether I can use arguments into dot to do these spatial flips
        # List of  available graphviz attributes: http://www.graphviz.org/content/attrs        
        p = np.array(node_positions.values())
        p = np.fliplr(p) # Rotate layout from vertical to horizontal
        p[:,0] = np.max(p[:,0])-p[:,0] + np.min(p[:,0])# Flip layout left/right
        for i,key in enumerate(node_positions.keys()):
            node_positions[key] = (p[i,0],p[i,1]) 
        
        # Problem: Since the graph is a dict, the order the nodes are added is not preserved. This is not
        # a problem until the graph is drawn; graphviz orders the root nodes by the node order in the graph object.
        # We want the graph to be ordered by object number.
        # Using G.add_nodes_from or G.subgraph using an ordered dict doesn't solve this.
        # There are a couple of webpages on this issue, which doesn't seem like it will be addressed anytime soon:
        #  https://networkx.lanl.gov/trac/ticket/445
        #  https://networkx.lanl.gov/trac/ticket/711
        
        # So we need to reorder y-locations by the label name.
        # Also, graphviz places the root node at t = 0 for all trajectories. We need to offset the x-locations by the actual timepoint.
        y_min = dict.fromkeys(self.trajectory_info.keys(), np.inf)
        y_max = dict.fromkeys(self.trajectory_info.keys(), -np.inf)
        for n in self.directed_graph.nodes():
            y_min[n[0]] = min(y_min[n[0]],node_positions[n][1])
            y_max[n[0]] = max(y_max[n[0]],node_positions[n][1])
        
        self.connected_nodes = [sorted(i) for i in sorted(nx.connected_components(self.directed_graph.to_undirected()))]

        # Assuming that the x-location on the graph for a given timepoint is unique, collect and sort them so they can be mapped into later
        node_x_locs = sorted(np.unique([i[0] for i in node_positions.values()]))
        
        # Adjust the y-spacing between trajectories so it the plot is roughly square, to avoid nasty Mayavi axis scaling issues later
        # See: http://stackoverflow.com/questions/13015097/how-do-i-scale-the-x-and-y-axes-in-mayavi2
        origin_y = 0 
        spacing_y = round( (max(node_x_locs) - min(node_x_locs))/len(self.connected_nodes) )
        offset_y = 0
        for trajectory in self.connected_nodes:
            dy = y_max[trajectory[0][0]] - y_min[trajectory[0][0]]
            for node in trajectory:
                node_positions[node] = (node_x_locs[node[1]-1], origin_y + offset_y) # (pos[frame][0], origin + offset)
            offset_y += dy + spacing_y
        
        self.lineage_node_positions = node_positions
        self.lineage_node_x_locations = node_x_locs

    def on_pick_one_timepoint(self,picker):
        """ Picker callback: this gets called upon pick events.
        """
        # Retrieving the data from Mayavi pipelines: http://docs.enthought.com/mayavi/mayavi/data.html#retrieving-the-data-from-mayavi-pipelines
        # More helpful example: http://docs.enthought.com/mayavi/mayavi/auto/example_select_red_balls.html
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
            x_lineage,y_lineage,_ = self.lineage_node_collection.mlab_source.points[point_id,:]
            picked_node = sorted(self.directed_graph)[point_id]
            x_traj,y_traj,t_traj = self.trajectory_node_collection.mlab_source.points[point_id,:]
            if picked_node == self.selected_node:
                self.selected_node = None 
            else:
                self.selected_node = picked_node
                
        elif picker.actor in self.trajectory_node_collection.actor.actors:
            # Retrieve to which point corresponds the picked point. 
            # Here, we grab the points describing the individual glyph, to figure
            # out how many points are in an individual glyph.                
            n_glyph = self.trajectory_node_collection.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]  
            # Find which data point corresponds to the point picked:
            # we have to account for the fact that each data point is
            # represented by a glyph with several points      
            point_id = picker.point_id/n_glyph            
            x_traj,y_traj,t_traj = self.trajectory_node_collection.mlab_source.points[point_id,:]
            l = self.trajectory_labels[point_id]
            self.selected_trajectories = l
            picked_node = sorted(self.directed_graph)[point_id]
            x_lineage,y_lineage,_ = self.lineage_node_collection.mlab_source.points[point_id,:]
            if picked_node == self.selected_node:
                self.selected_node = None
                self.selected_trajectories = None
            else:
                self.selected_node = picked_node  
                
        else:
            self.selected_node = None  
            self.selected_trajectories = None

        if self.selected_node:
            # Move the outline to the data point
            s = 5
            self.lineage_selection_outline.bounds = (x_lineage-s, x_lineage+s,
                                                     y_lineage-s, y_lineage+s,
                                                     0, 0)  
            self.trajectory_selection_outline.bounds = (x_traj-s, x_traj+s,
                                                        y_traj-s, y_traj+s,
                                                        t_traj-s, t_traj+s)            
    
    def draw_lineage(self,init = False):
        # Rendering temporarily disabled
        self.mayavi_view.lineage_scene.disable_render = True 

        # If I want to use mayavi, see here: http://docs.enthought.com/mayavi/mayavi/auto/example_delaunay_graph.html
        # Other possibly relevant pages:
        # https://groups.google.com/forum/?fromgroups=#!topic/networkx-discuss/wdhYIPeuilo
        # http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00727.html        

        # Clear the scene
        logging.info("Drawing lineage graph...")
        self.mayavi_view.lineage_scene.mlab.clf(figure = self.mayavi_view.lineage_scene.mayavi_scene)
        t1 = time.clock()
        
        G = nx.convert_node_labels_to_integers(self.directed_graph,ordering="sorted")
        xy = np.array([self.lineage_node_positions[i] for i in sorted(self.directed_graph)])
        node_scalars = np.array(G.nodes())
        pts = mlab.points3d(xy[:,0], xy[:,1], np.zeros_like(xy[:,0]),
                            node_scalars,
                            scale_factor = 10.0, # scale_factor = 'auto' results in huge pts: pts.glyph.glpyh.scale_factor = 147
                            line_width = 0.5, 
                            scale_mode = 'none',
                            colormap = self.selected_colormap,
                            resolution = 8,
                            figure = self.mayavi_view.lineage_scene.mayavi_scene) 
        pts.glyph.color_mode = 'color_by_scalar'
        pts.mlab_source.dataset.lines = np.array(G.edges())
        self.lineage_node_collection = pts
        
        tube = mlab.pipeline.tube(pts, 
                                  tube_radius=2.0, # Default tube_radius results in v. thin lines: tube.filter.radius = 0.05
                                  figure = self.mayavi_view.lineage_scene.mayavi_scene)
        self.lineage_edge_collection = mlab.pipeline.surface(tube, 
                                                             color=(0.8, 0.8, 0.8),
                                                             figure = self.mayavi_view.lineage_scene.mayavi_scene)
        
        # Add object label text to the left
        dx = np.diff(self.lineage_node_x_locations)[0]
        first_nodes = [i[0] for i in self.connected_nodes]
        x = [self.lineage_node_positions[i][0]-0.75*dx for i in first_nodes]
        y = [self.lineage_node_positions[i][1] for i in first_nodes]
        z = list(np.array(y)*0)
        s = [str(i[0]) for i in first_nodes]
        self.lineage_label_collection = [mlab.text3d(*xyzs,
                                                     line_width = 20,
                                                     scale = 20,
                                                     figure = self.mayavi_view.lineage_scene.mayavi_scene) 
                                for xyzs in zip(x,y,z,s)] 
        
        
        # Add outline to be used later when selecting points
        self.lineage_selection_outline = mlab.outline(line_width=3,
                                                      figure = self.mayavi_view.lineage_scene.mayavi_scene)
        self.lineage_selection_outline.outline_mode = 'cornered'        
        
        self.mayavi_view.lineage_scene.reset_zoom()
        
        # Constrain view to 2D
        self.mayavi_view.lineage_scene.interactor.interactor_style = tvtk.InteractorStyleImage()
        
        # Make the graph clickable
        self.mayavi_view.lineage_scene.mayavi_scene.on_mouse_pick(self.on_pick_one_timepoint)

        # Re-enable the rendering
        self.mayavi_view.lineage_scene.disable_render = False
        t2 = time.clock()
        logging.info("Computed layout (%.2f sec)"%(t2-t1))   

    def draw_trajectories(self,init = False):
        # Rendering temporarily disabled
        self.mayavi_view.trajectory_scene.disable_render = True  
        
        # Clear the scene
        logging.info("Drawing trajectories...")
        self.mayavi_view.trajectory_scene.mlab.clf(figure = self.mayavi_view.trajectory_scene.mayavi_scene)
        t1 = time.clock()
        
        G = nx.convert_node_labels_to_integers(self.directed_graph,ordering="sorted")

        xyts = np.array([(self.directed_graph.node[i]["x"],
                          self.directed_graph.node[i]["y"],
                          self.directed_graph.node[i]["t"],
                          self.directed_graph.node[i]["s"]) for i in sorted(self.directed_graph)])
        
        # Compute reasonable scaling factor according to the data limits.
        # We want the plot to be roughly square, to avoid nasty Mayavi axis scaling issues later.
        # Unfortunately, adjusting the surface.actor.actor.scale seems to lead to more problems than solutions.
        # See: http://stackoverflow.com/questions/13015097/how-do-i-scale-the-x-and-y-axes-in-mayavi2
        t_scaling = np.mean( [(max(xyts[:,0])-min(xyts[:,0])), (max(xyts[:,1])-min(xyts[:,1]))] ) / (max(xyts[:,2])-min(xyts[:,2]))
        xyts[:,2] *= t_scaling

        ## Create the lines
        self.source = mlab.pipeline.scalar_scatter(xyts[:,0], xyts[:,1], xyts[:,2], xyts[:,3], 
                                                   figure = self.mayavi_view.trajectory_scene.mayavi_scene)
        # Connect them
        self.source.mlab_source.dataset.lines = np.array(G.edges())     
        
        # Finally, display the set of lines
        self.trajectory_line_collection = mlab.pipeline.surface(mlab.pipeline.stripper(self.source), # The stripper filter cleans up connected lines; it regularizes surfaces by creating triangle strips
                                                                line_width=1, 
                                                                colormap=self.selected_colormap,
                                                                figure = self.mayavi_view.trajectory_scene.mayavi_scene)         

        self.trajectory_labels = np.array([self.directed_graph.node[i]["l"] for i in sorted(self.directed_graph)])
        
        # Generate the corresponding set of nodes
        pts = mlab.points3d(xyts[:,0], xyts[:,1], xyts[:,2], xyts[:,3],
                            scale_factor = 0.0, # scale_factor = 'auto' results in huge pts: pts.glyph.glpyh.scale_factor = 147
                            scale_mode = 'none',
                            colormap = self.selected_colormap,
                            figure = self.mayavi_view.trajectory_scene.mayavi_scene) 
        pts.glyph.color_mode = 'color_by_scalar'
        pts.mlab_source.dataset.lines = np.array(G.edges())
        self.trajectory_node_collection = pts    

        # Add object label text
        self.trajectory_label_collection = [mlab.text3d(self.directed_graph.node[i[-1]]["x"],
                                                        self.directed_graph.node[i[-1]]["y"],
                                                        self.directed_graph.node[i[-1]]["t"]*t_scaling,
                                                        str(i[-1][0]),
                                                        line_width = 20,
                                                        scale = 10,
                                                        name = str(i[-1][0]),
                                                        figure = self.mayavi_view.trajectory_scene.mayavi_scene) 
                                for i in self.connected_nodes]
        
        # Add outline to be used later when selecting points
        self.trajectory_selection_outline = mlab.outline(line_width=3,
                                                         figure = self.mayavi_view.trajectory_scene.mayavi_scene)
        self.trajectory_selection_outline.outline_mode = 'cornered'
        
        # Using axes doesn't work until the scene is avilable: 
        # http://docs.enthought.com/mayavi/mayavi/building_applications.html#making-the-visualization-live
        #mlab.axes()
        self.mayavi_view.trajectory_scene.reset_zoom()
        
        # An trajectory picker object is created to trigger an event when a trajectory is picked.       
        # TODO: Figure out how to re-activate picker on scene refresh
        #  E.g., (not identical problem) http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00583.html
        self.mayavi_view.trajectory_scene.mayavi_scene.on_mouse_pick(self.on_pick_one_timepoint)
        
        # Figure decorations
        # Orientation axes
        mlab.orientation_axes(zlabel = "t", 
                              line_width = 5,
                              figure = self.mayavi_view.trajectory_scene.mayavi_scene )
        # Colormap
        # TODO: Figure out how to scale colorbar to smaller size
        #c = mlab.colorbar(orientation = "horizontal", 
                          #title = self.selected_feature,
                          #figure = self.mayavi_view.trajectory_scene.mayavi_scene)
        #c.scalar_bar_representation.position2[1] = 0.05
        #c.scalar_bar.height = 0.05
        
        # Re-enable the rendering
        self.mayavi_view.trajectory_scene.disable_render = False
        t2 = time.clock()
        logging.info("Computed trajectory layout (%.2f sec)"%(t2-t1))    

################################################################################
if __name__ == "__main__":
        
    import sys
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        props.LoadFile(propsFile)
    else:
        if not props.show_load_dialog():
            print 'Time Visualizer requires a properties file.  Exiting.'
            # Necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

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
