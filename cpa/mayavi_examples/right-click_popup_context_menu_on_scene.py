import collections
import copy
import operator
import os
import time

import wx

from enthought.traits.api import HasTraits, Instance, on_trait_change, List, Dict, Int, Array
from enthought.traits.ui.api import View, Item
from enthought.mayavi.sources.api import ArraySource
from enthought.mayavi.modules.api import IsoSurface
from enthought.mayavi.core.ui.api import MlabSceneModel, SceneEditor
from enthought.mayavi import mlab
from enthought.tvtk.api import tvtk

class UniverseViewer(HasTraits):
                    
    scene = Instance(MlabSceneModel, (), {'background' : (0,0,0)})
    
    def __init__(self):
    
        HasTraits.__init__(self)
        
        
    view = View(Item("scene", editor = SceneEditor(), resizable = True, show_label = False), resizable = True)

    
class UniversePanel(wx.Panel):
    
    def __init__(self, parent):
    
        wx.Panel.__init__(self, parent=parent)

        self.parent = parent
        
        sizer = wx.BoxSizer(wx.VERTICAL)
                                
        self.viewer = UniverseViewer()
        
        self.control = self.viewer.edit_traits(parent=self, kind='subpanel').control
        
        sizer.Add(self.control, 1, wx.ALL|wx.EXPAND, 0)
            
        self.SetSizer(sizer)
                                
        self.menu = wx.Menu()
        
        item = self.menu.Append(wx.ID_ANY, "Select all")
        self.menu.Bind(wx.EVT_MENU, self.__select_all, item)

        self.control.Bind(wx.EVT_CONTEXT_MENU, self.__show_menu)
                                    
                        
    def __show_menu(self, event):
                                
        pos = event.GetPosition()
        pos = self.control.ScreenToClient(pos)                                                        
        self.PopupMenu(self.menu, pos)
                        

    def __select_all(self, event=None):

        print "toto"
                
        
def start_application():
    
    app = wx.App(redirect = False)
 
    f = wx.Frame(None)
    c = UniversePanel(f)
    f.Show(True)
    app.MainLoop()
    
    
if __name__ == "__main__":
    start_application()