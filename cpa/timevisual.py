import wx
from wx.combo import OwnerDrawnComboBox as ComboBox
import numpy as np
import time

# traits imports
from traits.api import HasTraits, Instance
from traitsui.api import View, Item, Group

# mayavi imports
from mayavi import mlab
from mayavi.core.ui.api import MlabSceneModel, SceneEditor
from tvtk.pyface.scene import Scene

import logging
from dbconnect import DBConnect
from properties import Properties
from cpatool import CPATool

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
#props.series_id = ["Image_Metadata_Plate"]
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
    trajectory_info = dict( (x,{"x":[],"y":[],"t":[],"s":[]}) for x in all_labels ) # Wanted to use fromkeys, but it leads to incorrect behavior since it passes by reference not by value
    locations = db.execute("SELECT O.%s, O.%s, O.%s, I.%s, O.%s FROM %s AS I, %s as O WHERE I.%s = O.%s AND %s ORDER BY O.%s, I.%s"%(
                props.object_tracking_label, props.cell_x_loc, props.cell_y_loc, props.timepoint_id, selected_feature, props.image_table, props.object_table, props.image_id, props.image_id, dataset_clause, props.object_tracking_label, props.timepoint_id))
    for loc in locations:
        trajectory_info[loc[0]]["x"].append(loc[1])
        trajectory_info[loc[0]]["y"].append(loc[2])
        trajectory_info[loc[0]]["t"].append(loc[3])
        trajectory_info[loc[0]]["s"].append(loc[4])
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

        # Row #2: Divisions, feature selection, colormap, update button
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
class TimeVisual(wx.Frame, CPATool):
    '''
    A Time Visual plot with its controls.
    '''
    def __init__(self, parent, size=(600,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Time Visual', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)

        # Check for required properties fields.
        #fail = False
        #missing_fields = [field for field in required_fields if not props.field_defined(field)]
        #if missing_fields:
            #fail = True
            #message = 'The following missing fields are required for TimeVisual: %s.'%(",".join(missing_fields))
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
        self.mayavi_view = MayaviView()
        
        self.trajectory_info = None
        self.selected_trajectories = None
        
        self.figpanel = self.mayavi_view.edit_traits(
                            parent=self,
                            kind='subpanel').control
        
           
        self.plot_trajectories(True)
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
    
    def on_isolate_trajectory(self, event = None):
        all_labels = self.trajectory_info.keys()
        self.trajectory_selection = dict.fromkeys(all_labels,0)
        self.trajectory_selection[self.selected_trajectories] = 1
        self.update_plot()
    
    def on_show_all_trajectories(self, event = None):
        all_labels = self.trajectory_info.keys()
        self.trajectory_selection = dict.fromkeys(all_labels,1)
        self.update_plot()
        
    def on_show_popup_menu(self, event = None):   
        '''
        Event handler: show the mayavi viewer context menu.  
        
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
            
                # The 'Isolate trajectory' item and its associated binding: display only the selected trajectory
                if self.parent.selected_trajectories is not None:
                    item = wx.MenuItem(self, wx.NewId(), "Isolate trajectory %d"%self.parent.selected_trajectories)
                    self.AppendItem(item)
                    self.Bind(wx.EVT_MENU, self.parent.on_isolate_trajectory, item)
                # The 'Show all trajectories' item and its associated binding: display all trajectories.
                item = wx.MenuItem(self, wx.NewId(), "Show all trajectories")
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.parent.on_show_all_trajectories, item)

        # The event (mouse right-click) position.
        pos = event.GetPosition()
        # Converts the position to mayavi internal coordinates.
        pos = self.figpanel.ScreenToClient(pos)                                                        
        # Show the context menu.      
        self.PopupMenu(TrajectoryPopupMenu(self), pos)
        
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
        self.plot_trajectories(False)
        self.configpanel.trajectory_selection_button.Enable()
    
    def on_pick_one_trajectory(self,picker):
        """ Picker callback: this gets called upon pick events.
        """
        # Retrieving the data from Mayavi pipelines: http://docs.enthought.com/mayavi/mayavi/data.html#id3
        if picker.actor in self.surface.actor.actors:
            # Retrieve to which point corresponds the picked point.                   
            x,y,z = self.surface.mlab_source.points[picker.point_id,:]
            l = self.trajectory_labels[picker.point_id]
            self.selected_trajectories = l
            print x,y,z, l
            outline = mlab.outline(line_width=3)
            outline.outline_mode = 'cornered'
            # Move the outline to the data point.
            outline.bounds = (x-0.1, x+0.1,
                              y-0.1, y+0.1,
                              z-0.1, z+0.1)
        else:
            self.selected_trajectories = None
                
    def plot_trajectories(self, init = False):
        # Rendering disabled
        self.mayavi_view.scene.disable_render = True
        
        # TODO(?): Update the plot according to what was changed: dataset, feature, colormap. 
        # TODO(?): Change only the plot elements required rather than updating the whole thing.
        #  e.g., only the "connections" variable needs to be changed if that's the only UI element the user needed.
        #  See here: http://docs.enthought.com/mayavi/mayavi/mlab_animating.html
        
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
                self.trajectory_selection = dict.fromkeys(self.trajectory_info.keys(),1)
            
        # Taken from http://docs.enthought.com/mayavi/mayavi/auto/example_plotting_many_lines.html
        x = list()
        y = list()
        t = list()
        s = list()
        l = list()
        connections = list()
        index = 0
    
        for current_object in self.trajectory_info.keys():
            x.append(self.trajectory_info[current_object]["x"])
            y.append(self.trajectory_info[current_object]["y"])
            t.append(self.trajectory_info[current_object]["t"])
            s.append(self.trajectory_info[current_object]["s"])
    
            # This is the tricky part: in a line, each point is connected
            # to the one following it. We have to express this with the indices
            # of the final set of points once all lines have been combined
            # together; this is why we need to keep track of the total number of
            # points already created (index)
            N = len(self.trajectory_info[current_object]["x"])
            l.append([current_object]*N)
            if self.trajectory_selection[current_object]:
                connections.append(np.vstack([np.arange(index,   index + N - 1.5),
                                              np.arange(index+1, index + N - .5)]).T)
            index += N
    
        # Now collapse all positions, scalars and connections in big arrays
        x = np.hstack(x)
        y = np.hstack(y)
        t = np.hstack(t)
        s = np.hstack(s)
        l = np.hstack(l)
        if len(connections) > 0:
            connections = np.vstack(connections)
        
        # Clear the scene
        self.mayavi_view.scene.mlab.clf()
        t1 = time.clock()
        
        # Create the lines
        self.source = mlab.pipeline.scalar_scatter(x, y, t, s, figure = self.mayavi_view.scene.mayavi_scene)
        dataset = self.source.mlab_source.dataset
        #dataset.point_data.update()
        self.dataset = dataset
        self.trajectory_labels = l
        
        # Connect them
        self.dataset.lines = connections
        
        # The stripper filter cleans up connected lines
        lines = mlab.pipeline.stripper(self.source) # Regularizes surfaces by creating triangle strips
    
        # Finally, display the set of lines
        self.surface = mlab.pipeline.surface(lines, line_width=1, colormap=self.selected_colormap) 
        
        # Scale axes according to the data limits
        self.surface.actor.actor.scale = [1.0/(max(x)-min(x)), 1.0/(max(y)-min(y)), 1.0/(max(t)-min(t))]
        
        # Add object label text
        # TODO: Figure out how to add text while retaining surface object
        #for i,current_object in enumerate(self.trajectory_info.keys()):
            #t = mlab.text3d(self.trajectory_info[current_object]["x"][-1],
                        #self.trajectory_info[current_object]["y"][-1],
                        #self.trajectory_info[current_object]["t"][-1],
                        #str(current_object),
                        #line_width = 10,
                        #figure = self.mayavi_view.scene.mayavi_scene)
        
        mlab.outline()
        # Using axes doesn't work until the scene is avilable: 
        # http://docs.enthought.com/mayavi/mayavi/building_applications.html#making-the-visualization-live
        #mlab.axes()
        self.mayavi_view.scene.reset_zoom()
        
        # An trajectory picker object is created to trigger an event when a trajectory is picked.       
        # TODO: Figure out how to re-activate picker on scene refresh
        #  E.g., (not identical problem) http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00583.html
        self.trajectory_picker = self.mayavi_view.scene.mayavi_scene.on_mouse_pick(self.on_pick_one_trajectory)
        
        # Figure decorations
        # Orientation axes
        mlab.orientation_axes(zlabel = "t", figure = self.mayavi_view.scene.mayavi_scene, line_width = 5)
        # Colormap
        # TODO: Figure out how to scale colorbar to smaller size
        #c = mlab.colorbar(orientation = "horizontal", title = self.selected_feature)
        #c.scalar_bar_representation.position2[1] = 0.05
        #c.scalar_bar.height = 0.05
        
        # Re-enable the rendering
        self.mayavi_view.scene.disable_render = False
        t2 = time.clock()
        logging.info("Computed layout (%.2f sec)"%(t2-t1))        

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

    timevisual = TimeVisual(None)
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
    