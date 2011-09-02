import wx
import sys
from experimentsettings import *

########################################################################
class StackDropdown(wx.Choice):
    """This class creates a choice menu when called and updates the items by listing to the 
    subscriber """

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Choice.__init__(self, parent, -1)
        
        meta = ExperimentSettings.getInstance()
        meta.add_subscriber(self.update_choices, 'ExptVessel.*')
        
    def update_choices(self, tag):
        print 'I am at update choices'
        #s = self.GetStringSelection()
        #self.SetItems(stackName)
        
        #if s in (stackName):
            #self.SetStringSelection(s)
        #else:
            #self.Select(0)
    
    