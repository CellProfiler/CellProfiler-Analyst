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
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib import pyplot, rcParams
rcParams['font.size'] = 10

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
from traitsui.api import View, Item, Group

# mayavi imports
from mayavi import mlab
from mayavi.core.ui.api import MlabSceneModel, SceneEditor
from tvtk.pyface.scene import Scene

use_matplotlib = False

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
props.series_id = ["Image_Group_Number"]
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
class DataSourcePanel(wx.Panel):
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
    scene = Instance(MlabSceneModel, ())

    # The layout of the dialog created
    view = View(Item('scene', editor=SceneEditor(scene_class=Scene), resizable=True, show_label=False),
                resizable=True )
    
    def __init__(self):
        HasTraits.__init__(self)
    
################################################################################        
class CanvasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        ''' According to here (http://stackoverflow.com/questions/8644233/networkx-and-matplotlib-axes-error)
        the call needs to be to pyplot.figure() for MPL 1.0+, rather than Figure() '''
        self.figure = pyplot.figure() # Figure()
        self.canvas = FigureCanvas(self, -1, self.figure)        
        self.figure.set_facecolor((1,1,1))
        self.figure.set_edgecolor((1,1,1))
        self.canvas.SetBackgroundColour('white')        
        self.axes = self.figure.add_subplot(111)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

################################################################################
class LineageTool(wx.Frame, CPATool):
    '''
    A Time Visual plot with its controls.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Lineage Tool', **kwargs)
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

        self.configpanel = DataSourcePanel(self)
        self.selected_dataset = self.configpanel.dataset_choice.GetStringSelection()
        self.selected_colormap  = self.configpanel.colormap_choice.GetStringSelection()
        self.plot_updated = False
        self.trajectory_selected = False
        self.selected_node = None
        
        if use_matplotlib:
            self.figpanel = CanvasPanel(self)  
        else:
            self.mayavi_view = MayaviView()
            self.figpanel = self.mayavi_view.edit_traits(
                                                parent=self,
                                                kind='subpanel').control 

        self.generate_graph(True)
        if use_matplotlib:
            self.draw_matplotlib_lineage(True)
        else:
            self.draw_mayavi_lineage(True)
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.figpanel, 1, wx.EXPAND)
        sizer.Add(self.configpanel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        
        self.figpanel.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
        
        # Define events
        wx.EVT_COMBOBOX(self.configpanel.dataset_choice, -1, self.on_dataset_selected)
        wx.EVT_COMBOBOX(self.configpanel.feature_choice, -1, self.on_feature_selected)
        wx.EVT_BUTTON(self.configpanel.trajectory_selection_button, -1, self.update_trajectory_selection)
        wx.EVT_BUTTON(self.configpanel.colormap_choice, -1, self.on_colormap_selected)
        wx.EVT_BUTTON(self.configpanel.update_plot_button, -1, self.update_plot)
        
    def on_show_all_trajectories(self, event = None):
        all_labels = self.trajectory_info.keys()
        self.trajectory_selection = dict.fromkeys(all_labels,1)
        self.update_plot()    
            
    def on_hover_over_node(self, event = None): #http://stackoverflow.com/questions/4453143/point-and-line-tooltips-in-matplotlib
        collisionFound = False
        if event.xdata != None and event.ydata != None: # mouse is inside the axes
            radius = self.default_node_size
            for node, xy in self.node_positions.items():
                if abs(event.xdata - xy[0]) < radius and abs(event.ydata - xy[1]) < radius:
                    self.tooltip.SetTip('%s %d,t=%d: %f' %(props.object_name[0],node[0],node[1], self.directed_graph.node[node]["s"])) 
                    self.tooltip.Enable(True)
                    collisionFound = True
                    break
        if not collisionFound:
            self.tooltip.Enable(False)    

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
        pos = self.figpanel.ScreenToClient(pos)                                                        
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
        if self.selected_dataset == self.configpanel.dataset_choice.GetStringSelection() or self.plot_updated :
            self.configpanel.trajectory_selection_button.Enable()
        else:
            self.configpanel.trajectory_selection_button.Disable()   
            
    def on_feature_selected(self, event = None):
        if self.selected_feature == self.configpanel.feature_choice.GetStringSelection() or self.plot_updated :
            self.configpanel.trajectory_selection_button.Enable()
        else:
            self.configpanel.trajectory_selection_button.Disable()            

    def on_colormap_selected(self, event = None):
        self.selected_colormap = self.configpanel.colormap_choice.GetStringSelection()    
        
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
        if use_matplotlib:
            self.draw_matplotlib_lineage(False)
        else:
            self.draw_mayavi_lineage(False)
        self.configpanel.trajectory_selection_button.Enable()    
            
    def generate_graph(self, init = False):
        # Generate data
        changed_dataset = self.selected_dataset != self.configpanel.dataset_choice.GetStringSelection()
        self.selected_dataset = self.configpanel.dataset_choice.GetStringSelection()
        self.selected_feature = self.configpanel.feature_choice.GetStringSelection()
        self.selected_colormap = self.configpanel.colormap_choice.GetStringSelection()
        
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
        logging.info("Computed layout (%.2f sec)"%(t2-t1))
        
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
        
        self.node_positions = node_positions
        self.node_x_locations = node_x_locs
        
    def on_pick_one_timepoint_matplotlib(self, event=None):
        node_collection = event.artist
        picked_node = sorted([[(xy[0]-event.mouseevent.xdata)**2+(xy[1]-event.mouseevent.ydata)**2,node] for node, xy in self.node_positions.items()])[0][1]
        current_line_width = node_collection.get_linewidths()
        line_widths = len(current_line_width)*[self.default_node_linewidth]
        if picked_node == self.selected_node: # Node was selected already: de-select
            line_widths[event.ind[0]] = self.default_node_linewidth
            self.selected_node = None
        else:
            line_widths[event.ind[0]] = self.selected_node_linewidth 
            self.selected_node = picked_node
        node_collection.set_linewidth(line_widths)                      
        node_collection.figure.canvas.draw()    

    def on_pick_one_timepoint_mayavi(self,picker):
            """ Picker callback: this gets called upon pick events.
            """
            # Retrieving the data from Mayavi pipelines: http://docs.enthought.com/mayavi/mayavi/data.html#retrieving-the-data-from-mayavi-pipelines
            # More helpful example: http://docs.enthought.com/mayavi/mayavi/auto/example_select_red_balls.html
            if picker.actor in self.edge_collection.actor.actors + self.node_collection.actor.actors:
                # TODO: Figure what the difference is between node_collection and edge_collection being clicked on.
                # Retrieve to which point corresponds the picked point. 
                # Here, we grab the points describing the individual glyph, to figure
                # out how many points are in an individual glyph.                
                n_glyph = self.node_collection.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]
                # Find which data point corresponds to the point picked:
                # we have to account for the fact that each data point is
                # represented by a glyph with several points      
                point_id = picker.point_id/n_glyph
                x,y,z = self.node_collection.mlab_source.points[point_id,:]
                picked_node = sorted(self.directed_graph)[point_id]
                if picked_node == self.selected_node:
                    self.selected_node = None 
                else:
                    self.selected_node = picked_node
                    outline = mlab.outline(line_width=3)
                    outline.outline_mode = 'cornered'
                    # Move the outline to the data point
                    s = 5
                    outline.bounds = (x-s, x+s,
                                      y-s, y+s,
                                      0, 0)
            else:
                self.selected_node = None   
    
    def draw_mayavi_lineage(self,init = False):

        # If I want to use mayavi, see here: http://docs.enthought.com/mayavi/mayavi/auto/example_delaunay_graph.html
        # Other possibly relevant pages:
        # https://groups.google.com/forum/?fromgroups=#!topic/networkx-discuss/wdhYIPeuilo
        # http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00727.html        

        # Clear the scene
        logging.info("Drawing lineage graph...")
        self.mayavi_view.scene.mlab.clf()
        t1 = time.clock()
        
        G = nx.convert_node_labels_to_integers(self.directed_graph,ordering="sorted")
        edges = G.edges()
        start_idx, end_idx = np.array(list(edges)).T
        start_idx = start_idx.astype(np.int)
        end_idx   = end_idx.astype(np.int)
        xy = np.array([self.node_positions[i] for i in sorted(self.directed_graph)])
        node_scalars = np.array(G.nodes())
        pts = mlab.points3d(xy[:,0], xy[:,1], np.zeros_like(xy[:,0]),
                            node_scalars,
                            scale_factor = 10.0, # scale_factor = 'auto' results in huge pts: pts.glyph.glpyh.scale_factor = 147
                            line_width = 0.5, 
                            scale_mode = 'none',
                            colormap = self.selected_colormap,
                            resolution = 8) 
        pts.glyph.color_mode = 'color_by_scalar'
        pts.mlab_source.dataset.lines = np.array(edges)
        self.node_collection = pts
        
        tube = mlab.pipeline.tube(pts, tube_radius=2.0) # Default tube_radius results in v. thin lines: tube.filter.radius = 0.05
        self.edge_collection = mlab.pipeline.surface(tube, color=(0.8, 0.8, 0.8))
 
        # Add object label text to the left
        dx = np.diff(self.node_x_locations)[0]
        first_nodes = [i[0] for i in self.connected_nodes]
        x = [self.node_positions[i][0]-0.75*dx for i in first_nodes]
        y = [self.node_positions[i][1] for i in first_nodes]
        z = list(np.array(y)*0)
        s = [str(i[0]) for i in first_nodes]
        self.text_collection = [mlab.text3d(xx, yy, zz, ss,
                                            line_width = 20,
                                            scale = 20,
                                            name = ss,
                                            figure = self.mayavi_view.scene.mayavi_scene) 
                                for xx,yy,zz,ss in zip(x,y,z,s)] 

        # Scale axes according to the data limits
        # TODO: Figure out how scaling relates to elment coordinates for trajectory picking.
        #self.axis_scaling = [1.0/(max(xy[:,0])-min(xy[:,0])), 1.0/(max(xy[:,1])-min(xy[:,1])), 0.0]
        #self.node_collection.actor.actor.scale = self.axis_scaling
        #self.edge_collection.actor.actor.scale = self.axis_scaling
        # Text labels are not the same scale as the other graphical elements, so adjust accordingly
        # TODO: Figure out how to scale the text the same as the graphical elements.
        #current_text_scaling = self.text_collection[0].actor.actor.scale
        #for t in self.text_collection:
            #t.actor.actor.scale = current_text_scaling*self.axis_scaling

        mlab.outline()
        self.mayavi_view.scene.reset_zoom()
        
        # Make the graph clickable
        self.trajectory_picker = self.mayavi_view.scene.mayavi_scene.on_mouse_pick(self.on_pick_one_timepoint_mayavi)
        # Make the graph clickable
        # Doesn't seem to be tooltips avilable
        #self.tooltip = wx.ToolTip('')
        #self.figpanel.canvas.SetToolTip(self.tooltip)
        #self.tooltip.Enable(False)
        #self.tooltip.SetDelay(0)        
        #self.figpanel.canvas.mpl_connect('motion_notify_event', self.on_hover_over_node)        

        # Re-enable the rendering
        self.mayavi_view.scene.disable_render = False
        t2 = time.clock()
        logging.info("Computed layout (%.2f sec)"%(t2-t1))   
           

    def draw_matplotlib_lineage(self, init = False):
        # Clear the scene
        logging.info("Drawing lineage graph...")
        self.figpanel.axes.clear()
    
        # Set some default attributes for the graph
        self.default_node_size = 10
        self.default_node_linewidth = 1.0
        self.default_edge_color = (0,0,0,1) # Black   
        self.selected_node_linewidth = 5*self.default_node_linewidth
        
        all_line_widths = self.directed_graph.number_of_nodes()*[self.default_node_linewidth]
        
        # Set unselected nodes to different graphical attributes
        # (1) node_size = 0.1*default
        self.unselected_node_size = self.default_node_size/10
        all_selected_trajectories = [i for i in self.trajectory_selection.keys() if self.trajectory_selection[i] == 1]
        nodedata = self.directed_graph.nodes(data=True)
        all_selected_nodes = [i for i,data in nodedata if data["l"] in all_selected_trajectories]
        all_node_sizes = [self.default_node_size if data["l"] in all_selected_trajectories else self.unselected_node_size for _,data in self.directed_graph.nodes(data=True)  ]
        
        # (2) edge_color = light gray
        self.unselected_edge_color = (0.85,0.85,0.85,1)
        edgedata = self.directed_graph.edges(nbunch=all_selected_nodes)
        all_edge_colors = [self.default_edge_color if i in edgedata else self.unselected_edge_color for i in self.directed_graph.edges()]
        
        # Draw the graph
        keys, all_node_colors = zip(*nx.get_node_attributes(self.directed_graph,'s').items())
        self.ordered_nodelist, all_node_sizes, all_node_colors = zip(*sorted(zip(keys, all_node_sizes, all_node_colors))) 
        self.node_collection = nx.draw_networkx_nodes(self.directed_graph,
                                                    nodelist = self.ordered_nodelist,
                                                    pos = self.node_positions,
                                                    ax = self.figpanel.axes,
                                                    with_labels = False,  
                                                    node_size  = all_node_sizes,
                                                    node_color  =  all_node_colors,
                                                    node_shape  = 'o',
                                                    alpha = 1.0,
                                                    linewidths = all_line_widths,
                                                    cmap = self.selected_colormap)
        
        self.edge_collection = nx.draw_networkx_edges(self.directed_graph,
                                                    nodelist = self.ordered_nodelist,
                                                    pos = self.node_positions, 
                                                    ax = self.figpanel.axes,
                                                    with_labels = False, 
                                                    arrows = False, 
                                                    edge_color = all_edge_colors,
                                                    linewidths = all_line_widths,
                                                    alpha = 1.0,
                                                    cmap = self.selected_colormap)
        
        # Place object labels as text to the left       
        dx = np.diff(self.node_x_locations)[0]
        first_nodes = [i[0] for i in self.connected_nodes]
        x = [self.node_positions[i][0]-1.5*dx for i in first_nodes]
        y = [self.node_positions[i][1] for i in first_nodes]
        s = [str(i[0]) for i in first_nodes]
        [self.figpanel.axes.text(xx, yy, ss, axes = self.figpanel.axes) for xx,yy,ss in zip(x,y,s)]
        
        #self.figpanel.axes.set_axis_off()
        self.figpanel.axes.axis('tight') 
        
        self.figpanel.figure.canvas.draw()
        
        # Make the graph clickable
        self.node_collection.set_picker(3*self.default_node_size)
        self.figpanel.canvas.mpl_connect('pick_event', self.on_pick_one_timepoint_matplotlib)  
        self.tooltip = wx.ToolTip('')
        self.figpanel.canvas.SetToolTip(self.tooltip)
        self.tooltip.Enable(False)
        self.tooltip.SetDelay(0)        
        self.figpanel.canvas.mpl_connect('motion_notify_event', self.on_hover_over_node)        
        
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

    timevisual = LineageTool(None)
    timevisual.Show()

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
