""" A custom editor for a workflow. """


# Major package imports.
import logging
import os
import wx

# Enthought library imports.
from enthought.component.function_binding import FunctionBinding
from enthought.component.function_binding_editor import wxFunctionBindingEditor
from enthought.pyface.list_box import ListBox
from enthought.pyface.list_box_model import ListBoxModel
from enthought.traits.api import Any, Instance, Str
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.wx.basic_editor_factory import BasicEditorFactory
from enthought.util.wx.image import get_bitmap
from enthought.util.wx.lazy_switcher import SwitcherPanel
from enthought.util.wx.sized_panel import SizedPanel


# Setup a logger for this module
logger = logging.getLogger(__name__)


class TraitListBoxModel(ListBoxModel):
    """ A model for a trait list box. """

    obj = Any
    trait_name = Str()
    editor = Instance(Editor)

    def __init__(self, **traits):
        """ Creates a new trait list box model. """

        super(TraitListBoxModel, self).__init__(**traits)

        self.obj.on_trait_change(self._on_list_changed,
                                 self.trait_name)
        self.obj.on_trait_change(self._on_list_changed,
                                 self.trait_name + '_items')

        self._initialize()

        return

    def dispose(self):

        if hasattr(self, '_items') and self._items is not None:
            for item in self._items:
                item.on_trait_change(self._on_item_changed, remove = True)

        self.obj.on_trait_change(self._on_list_changed,
                                 self.trait_name, remove = True)
        self.obj.on_trait_change(self._on_list_changed,
                                 self.trait_name + '_items', remove = True)
        return

    ###########################################################################
    # 'ListModel' interface.
    ###########################################################################

    def get_item_count(self):
        """ Returns the number of items in the list. """

        return len(self.editor.value)

    def get_item_at(self, index):
        """ Returns the item at the specified index. """

        item = self.editor.value[index]

        return str(item), item

    ###########################################################################
    # 'TraitListBoxModel' interface.
    ###########################################################################

    def append(self, item):
        """ Append an item to the list. """

        return self.editor.append(item)

    def insert(self, index, item):
        """ Insert an item into the list. """

        return self.editor.insert(index, item)

    def remove(self, item):
        """ Remove an item from the list. """

        return self.editor.remove(item)

    ###########################################################################
    # Trait event handlers.
    ###########################################################################

    def _on_list_changed(self):
        """ Called when the list has changed. """

        self._initialize()
        self.fire_list_changed()

        return

    def _on_item_changed(self):
        """ Called when an item in the list has changed. """

        self.fire_list_changed()

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _initialize(self):
        """ Initialize the list. """

        if hasattr(self, '_items') and self._items is not None:
            for item in self._items:
                item.on_trait_change(self._on_item_changed, remove = True)

        self._items = items = self.editor.value
        for item in items:
            item.on_trait_change(self._on_item_changed)

        return

class WorkflowListTraitEditor(Editor):

    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        query = self.object.query

        self.control = wxSerialWorkflowEditor(parent, -1, self,
                                              query = query)
        return

    def dispose ( self ):
        """ Disposes of the contents of an editor.
        """
        super(WorkflowListTraitEditor, self).dispose()
        self.control.dispose()

    def update_editor ( self ):
        return self.control.SetValue(self.value)

    def append(self, item):
        """ Append an item to the list. """

        # to make undos work in traits UI we currently have to reproduce
        # the entire list.
        items = self.value
        self.value = items[:] + [item]

        return

    def insert(self, index, item):
        """ Insert an item into the list. """

        # to make undos work in traits UI we currently have to reproduce
        # the entire list.
        items = self.value
        self.value = items[:index] + [item] + items[index:]
        return

    def remove(self, item):
        """ Remove an item from the list. """

        # to make undos work in traits UI we currently have to reproduce
        # the entire list.
        items = self.value
        try:
            index = items.index(item)
        except ValueError, e:
            logger.exception(e)
            return

        self.value = items[:index] + items[index + 1:]

        return

class wxSerialWorkflowEditor(wx.Panel):
    """ A custom editor for a workflow. """


    def __init__(self, parent, wxid, editor, handler=None, query=None, **kw):
        """ Create a new editor. """

        # Base-class constructor.
        wx.Panel.__init__(self, parent, wxid, **kw)

        # The trait editor
        self._editor = editor

        # The query used to select function components (if no query is
        # specified, ALL function components will be returned).
        self.query = query

        # Create the widget.
        self._create_widget(editor.object, handler)

        return

    def GetValue(self):
        return self._editor.value

    def SetValue(self, new_value):
        self._editor.value = new_value
        return

    ###########################################################################
    # Trait event handlers.
    ###########################################################################

    def on_selected_changed(self, obj, trait_name, old, new):
        """ Called when the item selected in the list box is changed. """

        if new is not None:
            self.switcher._show_page(new)

        # determine what the current selection is
        index = self.listbox.selection
        if index == -1:
            # there is no current selection
            item = None
        else:
            label, item = self.listbox.model.get_item_at(index)

        # gray out delete button?
        if item == None:
            self._remove_button.Enable(False)
        else:
            self._remove_button.Enable(True)

        # if we are are either end of the list we disable the button ...
        if item == None or new == 0:
            self._up_button.Enable(False)
        else:
            self._up_button.Enable(True)

        if item == None or new == self.listbox.model.get_item_count() - 1:
            self._down_button.Enable(False)
        else:
            self._down_button.Enable(True)

        # gray out either the enable or disable button

        if item == None:
            self._enable_button.Enable(False)
            self._disable_button.Enable(False)
        elif item.enabled:
            self._enable_button.Enable(False)
            self._disable_button.Enable(True)
        else:
            self._enable_button.Enable(True)
            self._disable_button.Enable(False)

        return

    ###########################################################################
    # wx event handlers.
    ###########################################################################

    def _on_add(self, event):
        """ Called when the 'Add' button is pressed. """

        from enthought.component.function_browser_dialog import FunctionBrowserDialog
        from enthought.envisage.ui.ui_plugin import UIPlugin
        window = UIPlugin.instance.active_window

        parent = window.control
        try:
            dialog = FunctionBrowserDialog(parent, -1, query=self.query)
            dialog.SetSize((750, 750))
            dialog.Center()

            x, y =  dialog.GetPosition()
            dialog.Move((x+200, y))

            result = dialog.ShowModal()
            if result == wx.ID_OK:
                fb = FunctionBinding(function = dialog.get_function())
                model = self.listbox.model
                model.append(fb)

                self.listbox.selection = len(model._items) - 1

        finally:
            dialog.Destroy()

        return

    def _on_remove(self, event):
        """ Called when the 'Remove' button is pressed. """

        index = self.listbox.selection
        if index != -1:
            model = self.listbox.model

            label, item = model.get_item_at(index)
            model.remove(item)

            if model.get_item_count() == 0:
                self.listbox.selection = -1

            else:
                # The first item in the list was deleted.
                if index == 0:
                    self.listbox.selection = -1
                    self.listbox.selection = 0

                # The last item in the list was deleted.
                elif index == model.get_item_count():
                    self.listbox.selection = -1
                    self.listbox.selection = index - 1

                # An item in the middle of the list was deleted.
                else:
                    self.listbox.selection = -1
                    self.listbox.selection = index

        return


    def _on_down(self, event):
        """ Move the currently selected operation down one step."""
        src = self.listbox.selection
        dst = src + 1
        if src < self.listbox.model.get_item_count() - 1:
            self._move_item(src, dst)

        return


    def _on_up(self, event):
        """ Move the currently selected operation up one step."""
        src = self.listbox.selection
        dst = src - 1
        if src > 0:
            self._move_item(src, dst)

        return

    def _move_item(self, src, dst):
        """
        Moves operation one step from src to dst.
        Presumes that the indexes provided are valid.
        """
        model = self.listbox.model
        label, item = model.get_item_at(src)
        model.remove(item)
        model.insert(dst, item)
        self.listbox.selection = dst

        return


    def _on_enable(self, event):
        src = self.listbox.selection
        label, item = self.listbox.model.get_item_at(src)
        item.enabled = True

        self._enable_button.Enable(False)
        self._disable_button.Enable(True)

        # The ListBox loses the selection because the names changes
        self.listbox.selection = -1
        self.listbox.selection = src

        return


    def _on_disable(self, event):
        src = self.listbox.selection
        label, item = self.listbox.model.get_item_at(src)
        item.enabled = False

        self._enable_button.Enable(True)
        self._disable_button.Enable(False)

        # The ListBox loses the selection because the names changes
        self.listbox.selection = -1
        self.listbox.selection = src

        return


    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_widget(self, workflow, handler):
        """ Create the widget! """

        self.sizer = sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        # The operation list and the operation details.
        sizer.Add(self._main(self, workflow, handler), 1, wx.EXPAND)

        # The Add/Remove/Up/Down buttons
        sizer.Add(self._create_buttons(self, handler), 0, wx.EXPAND | wx.TOP, 5)

        # If the workflow contains at least one operation then select the
        # first one.
        if len(workflow.operations) > 0:
            self.listbox.selection = 0

        # Resize the panel to match the sizer's minimal size.
        sizer.Fit(self)

        return

    def _main(self, parent, workflow, handler):
        """ The operation list and the operation details. """

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # The list of operations in the workflow.
        self.listbox = self._operation_list(parent, workflow, handler)
        sizer.Add(self.listbox.control, 1, wx.EXPAND)

        # The details of the selected operation.
        switcher = self._switcher(parent, workflow)
        sizer.Add(switcher, 1, wx.EXPAND)

        return sizer

    def _operation_list(self, parent, workflow, handler):
        """ The list of operations in the workflow. """

        model = TraitListBoxModel(obj = workflow,
                                  trait_name = 'operations',
                                  editor = self._editor)
        listbox = ListBox(parent, model = model)
        listbox.on_trait_change(self.on_selected_changed, 'selection')

        return listbox

    def _create_buttons(self, parent, handler):
        """ The buttons. """

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add.
        bmp = get_bitmap(self, 'image/add.png')
        add_button = wx.BitmapButton(parent, -1, bmp)
        add_button.SetToolTipString('Add a new component')
        sizer.Add(add_button, 0, wx.EXPAND)

        wx.EVT_BUTTON(parent, add_button.GetId(), self._on_add)

        # Remove.
        bmp = get_bitmap(self, 'image/delete.png')
        self._remove_button = wx.BitmapButton(parent, -1, bmp)
        self._remove_button.SetToolTipString('Remove selected component')
        sizer.Add(self._remove_button, 0, wx.EXPAND | wx.LEFT, 10)

        wx.EVT_BUTTON(parent, self._remove_button.GetId(), self._on_remove)

        # Up.
        bmp = get_bitmap(self, 'image/move_up.png')
        self._up_button = wx.BitmapButton(parent, -1, bmp)
        self._up_button.SetToolTipString('Move selected component up')
        sizer.Add(self._up_button, 0, wx.EXPAND | wx.LEFT, 10)

        wx.EVT_BUTTON(parent, self._up_button.GetId(), self._on_up)

        # Down
        bmp = get_bitmap(self, 'image/move_down.png')
        self._down_button = wx.BitmapButton(parent, -1, bmp)
        self._down_button.SetToolTipString('Move selected component down')
        sizer.Add(self._down_button, 0, wx.EXPAND | wx.LEFT, 10)

        wx.EVT_BUTTON(parent, self._down_button.GetId(), self._on_down)

        # Enable
        bmp = get_bitmap(self, 'image/enable.png')
        self._enable_button = wx.BitmapButton(parent, -1, bmp)
        self._enable_button.SetToolTipString('Enable selected component')
        sizer.Add(self._enable_button, 0, wx.EXPAND | wx.LEFT, 10)

        wx.EVT_BUTTON(parent, self._enable_button.GetId(), self._on_enable)
        self._enable_button.Enable(False)

        # Disable
        bmp = get_bitmap(self, 'image/disable.png')
        self._disable_button = wx.BitmapButton(parent, -1, bmp)
        self._disable_button.SetToolTipString('Disable selected component')
        sizer.Add(self._disable_button, 0, wx.EXPAND | wx.LEFT, 10)

        wx.EVT_BUTTON(parent, self._disable_button.GetId(), self._on_disable)
        self._disable_button.Enable(False)

        return sizer


    def _switcher(self, parent, operation_list):
        """ Create the switcher panel. """

        self.switcher = switcher = SwitcherPanel(parent, -1, self, cache=False)

        if len(operation_list.operations) > 0:
            page = switcher._show_page(0)

        return switcher

    def create_page(self, parent, index):
        """ Create a page for the switcher panel. """

        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = SizedPanel(parent, -1, sizer)

        if index != -1:
            operation = self._editor.value[index]

            # clean up any editors we've already created
            if hasattr(self, '_fb_editor') and self._fb_editor is not None:
                self._fb_editor.dispose()

            self._fb_editor = editor = wxFunctionBindingEditor(panel,
                                                               operation,
                                                               self._editor)
            sizer.Add(editor, 1, wx.EXPAND)

        panel.Fit()

        return panel

    def dispose(self):

        if hasattr(self, '_fb_editor') and self._fb_editor is not None:
            self._fb_editor.dispose()

            del self._fb_editor

        if hasattr(self, 'listbox'):
            self.listbox.dispose()
            self.listbox.on_trait_change(self.on_selected_changed, 'selection',
                                         remove = True)

        return

class WorkflowListEditor ( BasicEditorFactory ):

    klass = WorkflowListTraitEditor

#### EOF ######################################################################
