"""
This attempts to combine the functionality of the wx embedding 
example (http://docs.enthought.com/mayavi/mayavi/auto/example_wx_embedding.html#example-wx-embedding)
and the select red balls example (http://docs.enthought.com/mayavi/mayavi/auto/example_select_red_balls.html#example-select-red-balls).
The two of these together are basically a stripped down version of a UI I am making
which contains wx controls and a mayavi view for visualizing data.
"""
import numpy as np

import wx
from wx.combo import OwnerDrawnComboBox as ComboBox

from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item

from mayavi import mlab
from mayavi.core.ui.api import SceneEditor, MlabSceneModel
from mayavi.core.ui.mayavi_scene import MayaviScene

import networkx as nx

color_dict = {'red':(1,0,0),
              'orange':(1,0.5,0),
              'yellow':(1,1,0),
              'green':(0,1,0),
              'blue':(0,0,1),
              'purple':(1,0,1)}

################################################################################
class MayaviView(HasTraits):

    scene = Instance(MlabSceneModel, ())

    # The layout of the panel created by Traits
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene), 
                     resizable=True,
                    show_label=False),
                    resizable=True)

    def __init__(self, parent):
        HasTraits.__init__(self)
        self.parent = parent
        self.figure = self.scene.mlab.gcf()
        #self.figure = self.scene.mayavi_scene
        mlab.clf(figure = self.scene.mayavi_scene)
        
    @on_trait_change('scene.activated')
    def activate_trajectory_scene(self):
        # Here, we grab the points describing the individual glyph, to figure
        # out how many points are in an individual glyph.
        # Can't get these points until after the scene is activated
        self.glyph_points = self.ball_1_glyphs.glyph.glyph_source.glyph_source.output.points.to_array()         
        
        picker = self.figure.on_mouse_pick(self.picker_callback)

        # Decrease the tolerance, so that we can more easily select a precise point.
        picker.tolerance = 0.01
                
    def picker_callback(self,picker):
        """ Picker callback: this get called when on pick events.
        """
        if picker.actor in self.ball_1_glyphs.actor.actors:
            # Find which data point corresponds to the point picked:
            # we have to account for the fact that each data point is
            # represented by a glyph with several points
            point_id = picker.point_id/self.glyph_points.shape[0]
            # If the no points have been selected, we have '-1'
            if point_id != -1:
                # Retrieve the coordinnates coorresponding to that data point
                x, y, z = self.ball_1_glyphs.mlab_source.points[point_id,:]
                # Move the outline to the data point.
                self.outline.bounds = (x-0.1, x+0.1,
                                  y-0.1, y+0.1,
                                  z-0.1, z+0.1)
    
    def create_points(self):
        x1, y1, z1 = np.random.random((3, 10))
        x2, y2, z2 = np.random.random((3, 10))
        return (x1,y1,z1),(x2,y2,z2)
        
    def cMap(self,glyph,x,y,z):
        pass
        #lut = glyph.module_manager.scalar_lut_manager.lut.table.to_array()

    def initialize_data(self):
        self.scene.disable_render = True
        
        # Creates two set of points using mlab.points3d: red point and white points
        pts1,pts2 = self.create_points()
        
        # From http://docs.enthought.com/mayavi/mayavi/building_applications.html#embedding-mayavi-traits
        #  under "A scene, with mlab embedded"
        # Annoyingly, you can't specifiy an (r,g,b) value to change the color, only a scalar value. So
        #  I have to make one up; see http://stackoverflow.com/questions/18537172/specify-absolute-colour-for-3d-points-in-mayavi/18595299#18595299
        #x,y,z = color_dict[self.parent.control_panel.color_ball_1.GetStringSelection()]
        #s = 0
        self.ball_1_glyphs = mlab.points3d(pts1[0], pts1[1], pts1[2], #[s]*len(pts1[0]),
                                           #colormap = 'jet',
                                           color=(1, 0, 0),
                                           resolution=20,
                                           scale_mode = 'none',
                                           figure=self.scene.mayavi_scene)
        #s = self.cMap(self.ball_1_glyphs,x,y,z)
        
        self.ball_2_glyphs = mlab.points3d(pts2[0], pts2[1], pts2[2], #[s]*len(pts1[0]),
                                           #colormap = 'jet',
                                           color=(0.9, 0.9, 0.9),
                                           resolution=20, 
                                           scale_mode = 'none',
                                           figure=self.scene.mayavi_scene)
        self.update_color()
        
        # Add an outline to show the selected point and center it on the first data point.
        self.outline = mlab.outline(line_width=3, figure = self.scene.mayavi_scene)
        self.outline.outline_mode = 'cornered'
        self.outline.bounds = (pts1[0][0]-0.1, pts1[0][0]+0.1,
                               pts1[1][0]-0.1, pts1[1][0]+0.1,
                               pts1[2][0]-0.1, pts1[2][0]+0.1)
        
        # Every object has been created, we can reenable the rendering.
        self.scene.disable_render = False        
               
        #mlab.show() # Uncommenting this line causes the on_trait_change NOT to fire for some reason; see comment below
        
    def update_data(self):
        pass
    
    def update_color(self):
        pass
        #self.ball_1_glyphs.mlab_source.set(color = self.scalar_data)
        #self.ball_2_glyphs.mlab_source.set(color = self.scalar_data)
        
################################################################################
class ControlPanel(wx.Panel):
    '''
    A panel with controls for selecting the data for a visual
    Some helpful tips on using sizers for layout: http://zetcode.com/wxpython/layout/
    '''

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Define widgets
        self.number_of_balls = ComboBox(self, -1, choices=['5','10','20'], size=(200,-1), style=wx.CB_READONLY)
        self.number_of_balls.Select(0)
        self.color_ball_1 = ComboBox(self, -1, choices=['red','orange','yellow'], style=wx.CB_READONLY)
        self.color_ball_1.SetStringSelection("red") 
        self.color_ball_2 = ComboBox(self, -1, choices=['blue','green','purple'], style=wx.CB_READONLY)
        self.color_ball_2.SetStringSelection("blue")         
        self.update_button = wx.Button(self, -1, "Update")
                
        # Arrange widgets
        # Row #1: Ball number
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Number of balls Source:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.number_of_balls, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        # Row #2: Color of balls 1 and 2, update button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Color of ball 1:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.color_ball_1, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Color of ball 2:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.color_ball_2, 1, wx.EXPAND)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))
        
        # Row #3: Update button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(self.update_button)        
        sizer.Add(sz, 1, wx.EXPAND) 
        sizer.Layout()
        self.SetSizer(sizer)
        self.Layout()
        self.Show(True)        
        
######################################################
class MainWindow(wx.Frame):

    def __init__(self, parent, id, size=(1000,600)):
        wx.Frame.__init__(self, parent, id, 'Mayavi in Wx',size=size)
        
        self.control_panel = ControlPanel(self)
        
        self.selected_ball_number = self.control_panel.number_of_balls.GetStringSelection()
        self.selected_ball_1_color = self.control_panel.color_ball_1.GetItems()
        self.selected_ball_2_color = self.control_panel.color_ball_2.GetStringSelection()  
        
        # Define events
        wx.EVT_COMBOBOX(self.control_panel.number_of_balls, -1, self.on_number_of_balls_selected)
        wx.EVT_COMBOBOX(self.control_panel.color_ball_1, -1, self.on_ball_1_color_selected)
        wx.EVT_COMBOBOX(self.control_panel.color_ball_2, -1, self.on_ball_2_color_selected)
        wx.EVT_BUTTON(self.control_panel.update_button, -1, self.update)      

        self.mayavi_view = MayaviView(self)
        self.mayavi_view.initialize_data()            
        
        # Use traits to create a panel, and use it as the content of this wx frame.
        # From http://docs.enthought.com/mayavi/mayavi/auto/example_adjust_cropping_extents.html
        #  We need to use 'edit_traits' and not 'configure_traits()' as we do
        #  not want to start the GUI event loop (the call to mlab.show())
        #  at the end of the script will do it.
        self.figure_panel = self.mayavi_view.edit_traits(
                        parent=self,
                        kind='subpanel').control
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.figure_panel, 1, wx.EXPAND)        
        sizer.Add(self.control_panel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)        
        
        self.Show(True)

    def on_number_of_balls_selected(self, event = None):
        pass
    
    def on_ball_1_color_selected(self, event = None):
        self.selected_ball_1_color = self.control_panel.color_ball_1.GetItems()
    
    def on_ball_2_color_selected(self, event = None):
        pass
    
    def update(self, event = None):
        pass    
        
app = wx.PySimpleApp()
frame = MainWindow(None, wx.ID_ANY)
app.MainLoop()

