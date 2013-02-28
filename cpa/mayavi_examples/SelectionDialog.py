import wx

try:
    from tvtk.api import tvtk
except ImportError:
    from enthought.tvtk.api import tvtk

from nMOLDYN.GUI.Events import EVT_CLEAR_SELECTION, EVT_SELECTION
from nMOLDYN.GUI.SelectionPanel import SelectionPanel
from nMOLDYN.GUI.MolecularViewer import MolecularViewer
import nMOLDYN.GUI.Widgets as wid 
from nMOLDYN.GUI.Resources.Icons import FIRST24, LAST24, NEXT24, PREV24
from nMOLDYN.GUI.NumStrCtrl import NumStrCtrl
from nMOLDYN.Core.UserDefinitions import USER_DEFINITIONS

class SelectionFrame(wx.Frame):
    '''
    Build a dialog from which the user can build an atom selection.
    '''
            
    def __init__(self, parent, trajInfo, selection=None, exclusion = None):
        '''
        The constructor.
        
        @param parent: the widget parent. Can be None.
        @type parent: wx widget
        
        @param trajInfo: the trajectory info dictionary.
        @type trajInfo: dict
        
        @param selection: a list of indexes of predefined atoms.
        @type selection: list
        '''

        # The frame constructor.
        wx.Frame.__init__(self,
                          parent,
                          title="Atom selection",
                          style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
                          
        # The arguments are copied to instances variables.
        self.parent = parent
        self.trajInfo = trajInfo
        if selection is None:
            self.selection = set()
        else:
            self.selection = set(selection)
        
        if exclusion is None:
            self.exclusion = set()
        else:
            self.exclusion = set(exclusion)
            
        # if standalone
        if self.parent is None: 
            USER_DEFINITIONS.load(trajInfo['path'])
            
        # The dialog is built.
        self.__build_dialog()            
        

        
    def __build_context_menu(self):
        '''
        Build silently the mayavi viewer context menu.
        '''

        # A menu widget is created.
        self.menu = wx.Menu()
                
        # The 'Select all' item and its associated binding: select all the atoms.
        item = self.menu.Append(wx.ID_ANY, "Select all")
        self.menu.Bind(wx.EVT_MENU, self.on_select_all, item)
        
        # The 'Show selected atoms' item and its associated binding: display only the selected atoms.
        item = self.menu.Append(wx.ID_ANY, "Show selected atoms")
        self.menu.Bind(wx.EVT_MENU, self.on_show_selected_atoms, item)
    
        # The 'Show unselected atoms' item and its associated binding: display only the unselected atoms.
        item = self.menu.Append(wx.ID_ANY, "Show unselected atoms")
        self.menu.Bind(wx.EVT_MENU, self.on_show_unselected_atoms, item)
        
        # The 'Show all atoms' item and its associated binding: display only the unselected atoms.
        item = self.menu.Append(wx.ID_ANY, "Show all atoms")
        self.menu.Bind(wx.EVT_MENU, self.on_show_all_atoms, item)
        
        # The 'Clear selection' item and its associated binding: clear the selection.
        item = self.menu.Append(wx.ID_ANY, "Clear selection")
        self.menu.Bind(wx.EVT_MENU, self.on_clear_selection, item)

        self.menu.AppendSeparator()

        # The 'Clear labels' item and its associated binding: clear the labels.
        item = self.menu.Append(wx.ID_ANY, "Label all molecules")
        self.menu.Bind(wx.EVT_MENU, self.on_label_all_molecules, item)
        
        item = self.menu.Append(wx.ID_ANY, "Clear labels")
        self.menu.Bind(wx.EVT_MENU, self.on_clear_labels, item)    
        
        self.menu.AppendSeparator()
        
        item = self.menu.Append(wx.ID_ANY, "Undo selection")
        self.menu.Bind(wx.EVT_MENU, self.on_undo_selection, item)            

        item = self.menu.Append(wx.ID_ANY, "Undo exclusion")
        self.menu.Bind(wx.EVT_MENU, self.on_undo_exclusion, item) 


        
    def __build_dialog(self):
        '''
        Build the dialog.
        '''
        # The main panel.
        mainPanel = wx.Panel(self, wx.ID_ANY)
        
        # The mainPanelSizer.
        mainPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        leftPanelSizer = wx.BoxSizer(wx.VERTICAL)
        
        # The selection panel.
        self.selectionPanel = SelectionPanel(mainPanel, self.trajInfo)
                           
        # Add the selection panel to the sizer.
        leftPanelSizer.Add(self.selectionPanel, 1, wx.ALL|wx.EXPAND, 2)
        
        # The sizer that will contain the cancel and ok buttons and the selection name entry.
        sb = wx.StaticBox(mainPanel, wx.ID_ANY, label="Actions")       
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        # The cancel button is created.                
        cancelButton  = wx.Button(mainPanel, wx.ID_ANY, label="Cancel")
        # And added to the sizer.        
        actionsSizer.Add(cancelButton, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 2)
        
        # An empty space is added to the sizer so as the cancel button always looks separated from the rest of the widgets.        
        actionsSizer.Add((1,1), 1, wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, 2)

        # The entry for the selection name is created.  
        self.selectionName = wid.ComboPanel(mainPanel, label="Selection name", widgetParams = {"value":"selection"}, widget = wx.TextCtrl)
        self.selectionName.create()   

        actionsSizer.Add(self.selectionName, 4, wx.ALL|wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL, 2)
                
        # The save button is created.
        saveButton = wx.Button(mainPanel, wx.OK, label="Save")
        # And added to the sizer.
        actionsSizer.Add(saveButton, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 2)
        
        # The action sizer is added to the left panel sizer.
        leftPanelSizer.Add(actionsSizer, 0, wx.ALL|wx.EXPAND, 2)        
        
        # The mayavi viewer is created.
#        self.trajInfo['bonds'] = {} # momentary added by bachir until finishing the database 
        self.viewer = MolecularViewer(self.trajInfo, self.selection)
        
        # right panel sizer
        rightPanelSizer = wx.BoxSizer(wx.VERTICAL)
        
        # frame control
        # The next frame button.      
        sb = wx.StaticBox(mainPanel, wx.ID_ANY, label = "Configuration control")
        frameSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        s = wx.GridBagSizer(1,5)
        self.previousConfiguration = wx.BitmapButton(mainPanel, wx.ID_ANY, wx.Bitmap(PREV24))
        self.configurationNumber = NumStrCtrl(parent = mainPanel, NumStrParam = {'value':0, 'type':int, "minValue":0, "maxValue":len(self.trajInfo['traj'])-1, "allowEmpty":False} )
        self.nextConfiguration = wx.BitmapButton(mainPanel, wx.ID_ANY, wx.Bitmap(NEXT24))
        self.firstConfiguration = wx.BitmapButton(mainPanel, wx.ID_ANY, wx.Bitmap(FIRST24))                    
        self.lastConfiguration = wx.BitmapButton(mainPanel, wx.ID_ANY, wx.Bitmap(LAST24))
        # bing label options
        self.Bind(wx.EVT_BUTTON, self.on_previous_configuration, self.previousConfiguration)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_set_configuration_number, self.configurationNumber)
        self.Bind(wx.EVT_BUTTON, self.on_next_configuration, self.nextConfiguration)
        self.Bind(wx.EVT_BUTTON, self.on_first_configuration, self.firstConfiguration)
        self.Bind(wx.EVT_BUTTON, self.on_last_configuration, self.lastConfiguration)
        # build sizer
        s.Add(self.previousConfiguration, pos=(0,0), flag=wx.ALL)
        s.Add(self.configurationNumber, pos=(0,1), flag=wx.ALL|wx.EXPAND)
        s.Add(self.nextConfiguration, pos=(0,2), flag=wx.ALL)
        s.Add(self.firstConfiguration, pos=(0,4), flag=wx.ALL) 
        s.Add(self.lastConfiguration, pos=(0,5), flag=wx.ALL) 
        s.AddGrowableCol(1)
        frameSizer.Add(s, 1, wx.ALL|wx.EXPAND, 5)
        rightPanelSizer.Add(frameSizer,  0, wx.ALL|wx.EXPAND, 2)
        
        # The right panel that will contain the mayavi viewer.
        self.rightPanel = self.viewer.edit_traits(parent=mainPanel, kind='subpanel').control                        
        rightPanelSizer.Add(self.rightPanel, 1, wx.ALL|wx.EXPAND, 2)
        
        # create atom labeling options
        widgetSizerParams = {'flag':wx.ALL|wx.ALIGN_BOTTOM, 'proportion':1, 'border':1}
        sb = wx.StaticBox(mainPanel, wx.ID_ANY, label = "Mouse middle button atom labeling")
        labelSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        s = wx.GridBagSizer(4,3)
        self.moleculeNameLabel = wx.CheckBox(parent = mainPanel, label = 'Molecule name')
        self.moleculeIndexLabel = wx.CheckBox(parent = mainPanel, label = 'Molecule index')
        self.atomNameLabel = wx.CheckBox(parent = mainPanel, label = 'Atom name')
        self.atomIndexLabel = wx.CheckBox(parent = mainPanel, label = 'Atom index')
        self.atomElementLabel = wx.CheckBox(parent = mainPanel, label = 'Atom element')
        self.xPositionLabel = wx.CheckBox(parent = mainPanel, label = 'X position')
        self.yPositionLabel = wx.CheckBox(parent = mainPanel, label = 'Y position')
        self.zPositionLabel = wx.CheckBox(parent = mainPanel, label = 'Z position')
        self.scaleLabel =  wid.ComboPanel(mainPanel, label = 'Scale',  widget = wx.SpinCtrl,   labelParams = {'style':  wx.ALIGN_RIGHT}, widgetParams = {'style' : wx.SP_ARROW_KEYS}, labelSizerParams = {'flag':wx.ALL|wx.ALIGN_CENTER_VERTICAL, 'proportion':0, 'border':1}, widgetSizerParams = widgetSizerParams )
        self.opacityLabel =  wid.ComboPanel(mainPanel, label = 'Opacity',  widget = wx.SpinCtrl,   labelParams = {'style':  wx.ALIGN_RIGHT}, widgetParams = {'style' : wx.SP_ARROW_KEYS}, labelSizerParams = {'flag':wx.ALL|wx.ALIGN_CENTER_VERTICAL, 'proportion':0, 'border':1}, widgetSizerParams = widgetSizerParams )
        self.colourLabel =  wid.ComboPanel(mainPanel, label = 'Colour',  widget = wid.nmoldynColourPickerCtrl,   labelParams = { 'style':  wx.ALIGN_RIGHT}, widgetParams = {'style' : wx.CLRP_USE_TEXTCTRL}, labelSizerParams = {'flag':wx.ALL|wx.ALIGN_CENTER_VERTICAL, 'proportion':0, 'border':1}, widgetSizerParams = widgetSizerParams )        
        # initialize label options 
        self.moleculeNameLabel.SetValue(False)
        self.moleculeIndexLabel.SetValue(False)
        self.atomElementLabel.SetValue(False)
        self.atomIndexLabel.SetValue(True)
        self.atomNameLabel.SetValue(True)
        self.xPositionLabel.SetValue(False)
        self.yPositionLabel.SetValue(False)
        self.zPositionLabel.SetValue(False)
        self.colourLabel.create()
        self.scaleLabel.create()
        self.opacityLabel.create()
        self.scaleLabel.get_widget().SetValue(20)
        self.opacityLabel.get_widget().SetValue(100)
        self.colourLabel.get_widget().SetColour(wx.WHITE)
        # bing label options
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.moleculeNameLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.moleculeIndexLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.atomNameLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.atomElementLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.atomIndexLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.xPositionLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.yPositionLabel)
        self.Bind(wx.EVT_CHECKBOX, self.update_labels, self.zPositionLabel)
        self.Bind(wx.EVT_SPINCTRL, self.update_labels, id = self.scaleLabel.get_widget_id())
        self.Bind(wx.EVT_TEXT_ENTER, self.update_labels, id = self.scaleLabel.get_widget_id())
        self.Bind(wx.EVT_SPINCTRL, self.update_labels, id = self.opacityLabel.get_widget_id())
        self.Bind(wx.EVT_TEXT_ENTER, self.update_labels, id = self.opacityLabel.get_widget_id())
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.update_labels, self.colourLabel.get_widget())
        # build label options sizer
        s.Add(self.moleculeNameLabel, (0,0), flag=wx.ALL)
        s.Add(self.moleculeIndexLabel, (0,1), flag=wx.ALL)
        s.Add(self.atomNameLabel, (1,0), flag=wx.ALL)
        s.Add(self.atomIndexLabel, (1,1), flag=wx.ALL)
        s.Add(self.atomElementLabel, (1,2), flag=wx.ALL)
        s.Add(self.xPositionLabel, (2,0), flag=wx.ALL)
        s.Add(self.yPositionLabel, (2,1), flag=wx.ALL)
        s.Add(self.zPositionLabel, (2,2), flag=wx.ALL)
        s.Add(self.scaleLabel, (3,0), flag=wx.ALL)
        s.Add(self.opacityLabel, (3,1), flag=wx.ALL)
        s.Add(self.colourLabel, (3,2), flag=wx.ALL)
        s.AddGrowableCol(0)
        s.AddGrowableCol(1)
        s.AddGrowableCol(2)
        s.AddGrowableCol(3)
        labelSizer.Add(s, 1, wx.ALL|wx.EXPAND, 5)
        rightPanelSizer.Add(labelSizer,  0, wx.ALL|wx.EXPAND, 2)
        
        # Add the right panel to the sizer.
        mainPanelSizer.Add(leftPanelSizer, 1, wx.ALL|wx.EXPAND, 2)
        mainPanelSizer.Add(rightPanelSizer, 1, wx.ALL|wx.EXPAND, 2)
        
        # Set the sizer.
        mainPanel.SetSizer(mainPanelSizer)

        # Set frame size
        self.SetSizeHints(500,500,2000,2000)
        self.SetSize((950, 700))
        
        self.statusBar = self.CreateStatusBar()
        
        # And showed as a modal dialog.
        self.MakeModal(True)                                        
        self.Show(True)
                
        # Build (but not show) the context menu.
        self.__build_context_menu()

        # The events.        
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_BUTTON, self.on_close, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_validate_selection, saveButton)
                
        # Bind the mayavi viewer with a context menu. 
        self.rightPanel.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
        
        self.Bind(EVT_SELECTION, self.on_show_selection)
        self.Bind(EVT_CLEAR_SELECTION, self.on_clear_selection)

        # An atom picker object is created to trigger an event when an atom is picked.       
        self.atomPicker = self.viewer.scene.mlab.gcf().on_mouse_pick(self.on_pick_one_atom)

        # The tolerance for the atom picker. 
        self.atomPicker.tolerance = 0.01

        # A label picker object is created to trigger an event when an atom is mouse middle-button clicked. 
        self.labelPicker = self.viewer.scene.mlab.gcf().on_mouse_pick(self.on_show_label, button="Middle")
        
        # The tolerance for the label picker. 
        self.labelPicker.tolerance = 0.01

        # An area picker object is created to trigger an event when a selection is drawn.                
        self.viewer.scene.interactor.picker = tvtk.AreaPicker()

        self.viewer.scene.interactor.picker.add_observer('PickEvent', self.on_select_atoms)

        self.viewer.scene.interactor.interactor_style = tvtk.InteractorStyleRubberBandPick()


    def on_set_configuration_number(self, event = None):
        '''
        Event handler: set configuration number.  
        
        @param event: the event binder
        @type event: wx event
        '''
        configurationNumber = int(self.configurationNumber.GetValue())
        self.viewer.set_configuration(configurationNumber)
        
        
    def on_last_configuration(self, event = None):
        '''
        Event handler: set last configuration.  
        
        @param event: the event binder
        @type event: wx event
        '''
        self.configurationNumber.SetValue(len(self.trajInfo['traj'])-1)
        self.on_set_configuration_number()
    
    
    def on_first_configuration(self, event = None):
        '''
        Event handler: set first configuration.  
        
        @param event: the event binder
        @type event: wx event
        '''
        self.configurationNumber.SetValue(0)
        self.on_set_configuration_number()
    
    
    def on_next_configuration(self, event = None):
        '''
        Event handler: set next configuration.  
        
        @param event: the event binder
        @type event: wx event
        '''
        frame = int(self.configurationNumber.GetValue()) + 1
        self.configurationNumber.SetValue(frame)
        self.on_set_configuration_number()
        
    
    def on_previous_configuration(self, event = None):
        '''
        Event handler: set previous configuration.  
        
        @param event: the event binder
        @type event: wx event
        '''
        frame = int(self.configurationNumber.GetValue()) - 1
        self.configurationNumber.SetValue(frame)
        self.on_set_configuration_number()
        
        
    def on_clear_labels(self, event=None):
        '''
        Event handler: clear the labels.  
        
        @param event: the event binder
        @type event: wx event
        '''
        
        self.viewer.clear_labels()

    
    def on_label_all_molecules(self, event=None):
        '''
        Event handler: label all atoms.  
        
        @param event: the event binder
        @type event: wx event
        '''
        indexes = [mol.atomList()[0].index for mol in self.trajInfo['traj'].universe.objectList()]
        self.viewer.update_labels( indexes, 
                                   **self.get_label_kwargs() )
        
        
    def on_undo_selection(self, event = None):
        '''
        Event handler: Undo the last selection.  
        
        @param event: the event binder
        @type event: wx event
        '''
        self.selectionPanel.on_undo_selection()
        
    
    def on_undo_exclusion(self, event = None):
        '''
        Event handler: Undo the last exclusion.  
        
        @param event: the event binder
        @type event: wx event
        '''
        self.selectionPanel.on_undo_exclusion()
        
         
    def on_clear_selection(self, event=None):
        '''
        Event handler: clear the current atom selection.  
        
        @param event: the event binder
        @type event: wx event
        '''
                        
        # If the clear selection is triggered by the context menu then cleanup the selection panel.
        if event.GetEventType() != EVT_CLEAR_SELECTION.typeId:      
            # The selection panel is cleared.
            self.selectionPanel.on_clear_selection()
        else:
            self.selection = set()
            self.update_selection(self.selection)


    def on_close(self, event=None):
        '''
        Event handler: closes the dialog.
        
        @param event: the event binder
        @type event: wx event
        '''

        # Destroy the frame.  
        self.MakeModal(False)      
        self.Destroy()


    def on_pick_one_atom(self, event=None):
        '''
        Event handler: mark the picked atom as selected.
        
        @param event: the event binder.
        @type event: tvtk event
        '''

        # Check that the picked object is actually an atom.            
        if self.atomPicker.actor in self.viewer.pts.actor.actors:
            # Retrieve to which atom corresponds the picked glyph.                   
            res = self.viewer.pts.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]
            id = int(self.atomPicker.point_id/res)
            # Add the selected atom.
            if id != -1:
                if self.selectionPanel.selectionRadioButton.GetValue():
                    self.selectionPanel.update_selection(('atompicked',[id]))
                elif self.selectionPanel.exclusionRadioButton.GetValue():
                    self.selectionPanel.update_exclusion(('atompicked',[id]))
            
                
    def on_select_all(self, event=None):
        '''
        Event handler: select all the atoms.  
        
        @param event: the event binder
        @type event: wx event
        '''
        self.selectionPanel.update_selection(val = ("atomindex", ["*"]))

        
    def on_select_atoms(self, widget, event):
        '''
        Event handler: mark the atoms within the drawn area as selected.
        
        @param widget:
        @type widget:
        
        @param event: the event binder.
        @type event: tvtk event
        '''
        
        e = tvtk.ExtractSelectedFrustum()
        e.set_input(0, self.viewer.pts.mlab_source.dataset)
        e.frustum = self.viewer.scene.interactor.picker.frustum
        e.update()
        o = e.get_output(0)
        
        idxs = [int(v) for v in list(o.point_data.get_array(2))]
        
        if idxs:
            self.selectionPanel.update_selection(('atompicked',idxs))

    
    def get_label_kwargs(self):
        kwargs = {}
        kwargs["molecule_name"] = self.moleculeNameLabel.GetValue()
        kwargs["molecule_index"] = self.moleculeIndexLabel.GetValue()
        kwargs["atom_element"] = self.atomElementLabel.GetValue()
        kwargs["atom_index"] = self.atomIndexLabel.GetValue()
        kwargs["atom_name"] = self.atomNameLabel.GetValue()
        kwargs["x_position"] = self.xPositionLabel.GetValue()
        kwargs["y_position"] = self.yPositionLabel.GetValue()
        kwargs["z_position"] = self.zPositionLabel.GetValue()        
        kwargs["colour"] = self.colourLabel.get_widget().GetValue()
        kwargs["scale"] = self.scaleLabel.get_widget().GetValue()
        kwargs["opacity"] = self.opacityLabel.get_widget().GetValue()
        
        return kwargs
    
    
    def update_labels(self, event):
        self.viewer.update_labels(None, **self.get_label_kwargs()) 
        
        
    def on_show_label(self, picker=None):                
        '''
        Event handler: show the label corresponding to the picked atom.
        
        @param picker: the event binder.
        @type picker: tvtk event
        '''
        if self.labelPicker.actor in self.viewer.pts.actor.actors:                   
            res = self.viewer.pts.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]
            id = int(self.labelPicker.point_id/res)
            if id != -1:
                self.viewer.update_label(id, **self.get_label_kwargs())                                

        
    def on_show_popup_menu(self, event=None):
        '''
        Event handler: show the mayavi viewer context menu.  
        
        @param event: the event binder
        @type event: wx event
        '''
                
        # The event (mouse right-click) position.
        pos = event.GetPosition()
        
        # Converts the position to mayavi internal coordinates.
        pos = self.rightPanel.ScreenToClient(pos)
        
        # Show the context menu.                                                        
        self.rightPanel.PopupMenu(self.menu, pos)


    def on_show_selected_atoms(self, event=None):
        '''
        Event handler: show the selected atoms.  
        
        @param event: the event binder
        @type event: wx event
        '''
        
        self.viewer.hideshow_selection(True)


    def on_show_selection(self, event=None):
        '''
        Event handler: show the current selection.  
        
        @param event: the event binder
        @type event: wx event
        '''
        
        # Get the indexes of the selected atoms.        
        self.selection = self.selectionPanel.get_selection()
        
        self.update_selection(self.selection)        

        self.statusBar.SetStatusText('%d atoms selected.' % len(self.selection))        


    def on_show_unselected_atoms(self, event=None):
        '''
        Event handler: show the unselected atoms.  
        
        @param event: the event binder
        @type event: wx event
        '''
        
        self.viewer.hideshow_selection(False)
        
    
    def on_show_all_atoms(self, event = None):
        '''
        Event handler: show all atoms.  
        
        @param event: the event binder
        @type event: wx event
        '''
        
        # Get the indexes of the selected atoms.        
        indexes = self.selectionPanel.get_selection()
                        
        self.viewer.hideshow_selection(True) 
        self.viewer.select_atoms(indexes) 


    def on_validate_selection(self, event=None):
        '''
        Event handler: validate the selection. 
        
        @param event: the event binder
        @type event: wx event
        '''

        if not self.selection:
            d = wx.MessageDialog(self, message="No atoms selected.", style=wx.OK|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP)
            d.ShowModal()
            return
        
        selName = self.selectionName.GetValue()
       
        path = self.trajInfo['path']

        if USER_DEFINITIONS[path]['selections'].has_key(selName):                
            d = wx.MessageDialog(self,
                                 message="This selection already exists.\nDo you really want to overwrite it ?",
                                 style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION|wx.STAY_ON_TOP)
                                                                
            if d.ShowModal() == wx.ID_NO:
                return
        
        sel = {}
        sel["selection"] = self.selectionPanel.get_selection_string()
        sel["exclusion"] = self.selectionPanel.get_exclusion_string()
        USER_DEFINITIONS.set(path, "selections", selName, sel) 
 
        if hasattr(self.parent, 'refresh_trajectory_tree'):          
            self.parent.refresh_trajectory_tree()
        
    
    def update_selection(self, selection):
        '''
        Update the displayed selection
        
        @param selection: the selection
        @type selection: set
        '''

        # The viewer is updated.
        self.viewer.select_atoms(selection)        

        # The status bar is updated.
        self.statusBar.SetStatusText('%d atoms selected.' % len(selection))        
                                
        
if __name__ == "__main__":

    import os
    from nMOLDYN.Core.Platform import Platform
    from nMOLDYN.Utilities.TrajectoryInfo import get_trajectory_info
    
    
    tInfo = get_trajectory_info(os.path.join(Platform().package_directory(), "Data","Trajectories", "mmtk","dmpc_in_periodic_universe.nc"))
#    tInfo = get_trajectory_info('/Users/AOUN/Desktop/Collaboration/Sharma_micelle/analysis/cvff/300k_2ns_1ps_time_step/GMFT_micelle_300k_2ns.nc')
#    tInfo = get_trajectory_info('/Users/AOUN/Desktop/nMOLDYN_files/EMIM_Br_prod.nc')
#    tInfo = get_trajectory_info('/Users/AOUN/Desktop/Collaboration/dmpc_membranes/charmm36/analysis/280K_to_330K/72l_144w//300K/BTCT_dmpc_72l_144w_300K.nc')
#    tInfo = get_trajectory_info( '/Users/AOUN/Desktop/Collaboration/micelles/dtab_C12/analysis/330K/rt_solvatedMicelle_330K_production.nc')
#    tInfo = get_trajectory_info( "/Users/AOUN/Desktop/Collaboration/apoferritin/analysis/180K/gmft_1IER_180K_production.nc")


    app = wx.App(redirect = False)
    
    f = SelectionFrame(None, tInfo)
    
    app.MainLoop()
    