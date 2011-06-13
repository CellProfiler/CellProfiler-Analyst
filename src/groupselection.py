import wx
import sys
from experimentsettings import ExperimentSettings

########################################################################
meta = ExperimentSettings.getInstance()

class GroupSelection(wx.Choice):
    """This class creates a choice menu when called and updates the items by listing to the 
    subscriber """

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Choice.__init__(self, parent, -1)

        meta.add_subscriber(self.update_choices, 'ExptVessel.*')
        
    def update_choices(self, tag):
        # find all the group names for the all vessel types
        plate_stack_names = []
        for id in meta.get_field_instances('ExptVessel|Plate'): 
            plate_stack_names.append('PlateGroup_'+meta.get_field('ExptVessel|Plate|GroupName|%s'%(id)))        
        plt_stackName =  list(set(plate_stack_names))
        
        flask_stack_names = []
        for id in meta.get_field_instances('ExptVessel|Flask'): 
            flask_stack_names.append('FlaskGroup_'+meta.get_field('ExptVessel|Flask|GroupName|%s'%(id)))        
        flk_stackName =  list(set(flask_stack_names))
        
        dish_stack_names = []
        for id in meta.get_field_instances('ExptVessel|Dish'): 
            dish_stack_names.append('DishGroup_'+meta.get_field('ExptVessel|Dish|GroupName|%s'%(id)))        
        dsh_stackName =  list(set(dish_stack_names))
        
        coverslip_stack_names = []
        for id in meta.get_field_instances('ExptVessel|Coverslip'): 
            coverslip_stack_names.append('CoverslipGroup_'+meta.get_field('ExptVessel|Coverslip|GroupName|%s'%(id)))        
        csp_stackName =  list(set(coverslip_stack_names))
        
        stackNames =[]
        stackNames.extend(plt_stackName)
        stackNames.extend(flk_stackName)
        stackNames.extend(dsh_stackName)
        stackNames.extend(csp_stackName)
    
        
        s = self.GetStringSelection()
        self.SetItems(stackNames)
        
        if s in (stackNames):
            self.SetStringSelection(s)
        else:
            self.Select(0)
        
        
    
    