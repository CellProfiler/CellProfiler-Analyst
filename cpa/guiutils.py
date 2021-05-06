import logging
import platform
import wx
import wx.adv
import os
import re
from cpa.icons import get_icon
from . import properties
from . import dbconnect
from . import sqltools
import numpy as np
from .utils import Observable
from wx.adv import OwnerDrawnComboBox as ComboBox

p = properties.Properties()
db = dbconnect.DBConnect()

def get_main_frame_or_none():
    return wx.GetApp().__dict__.get('frame', None)

class _ColumnLinkerPanel(wx.Panel):
    def __init__(self, parent, table_a, table_b, col_a=None, col_b=None, allow_delete=True, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.table_a = table_a
        self.table_b = table_b
        self.aChoice = ComboBox(self, choices=db.GetColumnNames(table_a), 
                                size=(100,-1), style=wx.CB_READONLY)
        self.bChoice = ComboBox(self, choices=db.GetColumnNames(table_b), 
                                size=(100,-1), style=wx.CB_READONLY)
        if col_a in self.aChoice.Strings:
            self.aChoice.Select(self.aChoice.Strings.index(col_a))
        if col_b in self.bChoice.Strings:
            self.bChoice.Select(self.bChoice.Strings.index(col_b))

        if allow_delete:
            self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))

        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Sizer.Add(wx.StaticText(self, -1, table_a+'.'), 0, wx.TOP, 4)
        self.Sizer.Add(self.aChoice, 1, wx.EXPAND)
        self.Sizer.AddSpacer(10)
        self.Sizer.Add(wx.StaticText(self, -1, '<=>'), 0, wx.TOP, 4)
        self.Sizer.AddSpacer(10)
        self.Sizer.Add(wx.StaticText(self, -1, table_b+'.'), 0, wx.TOP, 4)
        self.Sizer.Add(self.bChoice, 1, wx.EXPAND)
        if allow_delete:
            self.Sizer.AddSpacer(10)
            self.Sizer.Add(self.x_btn)
            self.x_btn.Bind(wx.EVT_BUTTON, self.GrandParent.on_remove_panel)

    def get_column_pair(self):
        '''returns ((table_a, col_a), (table_b, col_b))
        '''
        return ((self.table_a, self.aChoice.Value), 
                (self.table_b, self.bChoice.Value))



class LinkTablesDialog(wx.Dialog):
    '''Prompts the user to specify which columns link the given tables
    '''
    def __init__(self, parent, table_a, table_b, a_cols=[], b_cols=[], **kwargs):
        '''parent - parent window
        table_a, table_b - the tables to link
        a_cols, b_cols - default column values to set for the user
        '''
        assert len(a_cols) == len(b_cols)
        kwargs['size'] = kwargs.get('size', None) or (600,-1)
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwargs)
        self.table_a = table_a
        self.table_b = table_b
        self.addbtn = wx.Button(self, -1, 'Add Column')
        self.ok = wx.Button(self, -1, 'OK')
        self.cancel = wx.Button(self, -1, 'Cancel')

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.Sizer.Add(wx.StaticText(self, -1, 
                                     'Select the column or columns from "%s" and the corresponding\n'
                                     'columns in "%s" that will be used to join the two tables.'
                                     %(table_a, table_b)), 
                       0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.TOP|wx.CENTER, 10)
        self.Sizer.Add(-1, 10, 0)

        self.sw = wx.ScrolledWindow(self)
        if a_cols:
            self.panels = [_ColumnLinkerPanel(self.sw, table_a, table_b, a_cols[0], b_cols[0], allow_delete=False)]
            a_cols = a_cols[1:]
            b_cols = b_cols[1:]
        else:
            self.panels = [_ColumnLinkerPanel(self.sw, table_a, table_b, allow_delete=False)]
        self.sw.EnableScrolling(xScrolling=False, yScrolling=True)
        self.sw.Sizer = wx.BoxSizer(wx.VERTICAL)
        (w,h) = self.sw.Sizer.GetSize()
        self.sw.SetScrollbars(20,20,w/20,h/20,0,0)
        self.sw.Sizer.Add(self.panels[0], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.Sizer.Add(self.sw, 1, wx.EXPAND)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddSpacer(10)
        sz.Add(self.addbtn, 0)
        sz.AddStretchSpacer()
        sz.Add(self.ok, 0)
        sz.AddSpacer(10)
        sz.Add(self.cancel, 0)
        sz.AddSpacer(10)

        self.Sizer.Add(-1, 10, 0)
        self.Sizer.Add(sz, 0, wx.EXPAND)
        self.Sizer.Add(-1, 10, 0)

        for cola, colb in zip(a_cols, b_cols):
            self.add_column(cola, colb)

        if 'size' not in list(kwargs.keys()):
            self.resize_to_fit()

        self.addbtn.Bind(wx.EVT_BUTTON, self.add_column)
        self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel.Bind(wx.EVT_BUTTON, self.on_cancel)

    def get_column_pairs(self):
        '''
        returns a list of column pairs.
        eg: [((table_a, col_a1), (table_b, col_b1)),
             ((table_a, col_a2), (table_b, col_b2)), ...]
        '''
        return [panel.get_column_pair() for panel in self.panels]

    def on_ok(self, evt):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, evt):
        self.EndModal(wx.ID_CANCEL)

    def on_remove_panel(self, evt):
        panel = evt.EventObject.Parent
        i = self.panels.index(panel)
        self.panels.remove(panel)
        self.Sizer.Remove(panel)
        panel.Destroy()
        self.resize_to_fit()

    def on_add_column(self, evt):
        self.add_column()

    def add_column(self, col_a=None, col_b=None):
        self.panels += [_ColumnLinkerPanel(self.sw, self.table_a, self.table_b, col_a, col_b)]
        self.sw.Sizer.Add(self.panels[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.resize_to_fit()

    def resize_to_fit(self):
        #w = min(self.sw.Sizer.MinSize[0] + self.Sizer.MinSize[0], 
                    #wx.GetDisplaySize()[0] - self.Position[0])
        h = min(self.sw.Sizer.MinSize[1] + self.Sizer.MinSize[1],
                wx.GetDisplaySize()[1] - self.Position[1])
        self.SetSize((-1,h+7))



def get_other_table_from_user(parent):
    '''Prompts the user to select a table from a list of tables that they haven't 
    yet accessed in the database.
    returns the table name or None if the user cancels
    '''
    other_tables = db.get_other_table_names()
    if len(other_tables) == 0:
        wx.MessageDialog(parent, 'No other tables were found in the current database.').ShowModal()
        return None
    dlg = wx.SingleChoiceDialog(parent, 'Select a table', 'Select a table',
                                other_tables, wx.CHOICEDLG_STYLE)
    if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        return None
    table = dlg.GetStringSelection()
    dlg.Destroy()
    return prompt_user_to_link_table(parent, table)
    


def prompt_user_to_link_table(parent, table):
    '''Prompts the user for information about the given table so it may be
    linked into the tables that CPA already accesses.
    returns the given table name or None if the user cancels
    '''
    dlg = wx.SingleChoiceDialog(parent, 'What kind of data is in this table (%s)?'%(table),
                                'Select table type', ['per-well', 'per-image', 'per-object', 'other'], 
                                wx.CHOICEDLG_STYLE)
    show_table_button = wx.Button(dlg, -1, 'Show table')
    dlg.Sizer.Children[2].GetSizer().Insert(0, show_table_button, 0, wx.ALL, 10)
    dlg.Sizer.Children[2].GetSizer().InsertStretchSpacer(1, 1)
    def on_show_table(evt):
        from .tableviewer import TableViewer
        tableview = TableViewer(get_main_frame_or_none())
        tableview.Show()
        tableview.load_db_table(table)
    show_table_button.Bind(wx.EVT_BUTTON, on_show_table)
    if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        return None
    new_table_type = dlg.GetStringSelection()

    if new_table_type == 'per-well':
        link_table_to_try = p.image_table
        link_cols_to_try = dbconnect.well_key_columns()
    elif new_table_type == 'per-image':
        dlg = wx.MessageDialog(parent, 'Does this per-image table represent a '
                               'new set of images in your experiment?', 
                               'New per-image table', wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            wx.MessageDialog(parent,'Sorry, CPA does not currently support multiple\n'
                             'per-image tables unless they are referring to the\n'
                             'same images.\n\n'
                             'Please see the manual for more information',
                             'Multiple per-image tables not supported')
            dlg.Destroy()
            return None
        link_table_to_try = p.image_table
        link_cols_to_try = dbconnect.image_key_columns()
    elif new_table_type == 'per-object':
        dlg = wx.MessageDialog(parent, 'Does this per-object table represent a '
                               'new set of objects in your experiment?', 
                               'New per-object table', wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            wx.MessageDialog(parent,'Sorry, CPA does not currently support multiple\n'
                             'per-object tables unless they are referring to the\n'
                             'same objects.\n\n'
                             'Please see the manual for more information',
                             'Multiple per-object tables not supported')
        if p.object_table:
            if table == p.object_table:
                raise
            link_table_to_try = p.object_table
            link_cols_to_try = dbconnect.object_key_columns()
        else:
            # There should never be an object table without another object 
            # table existing first. Connecting this table to the image_table is
            # asking for trouble.
            return None

    else:
        dlg = wx.SingleChoiceDialog(parent, 'Which of your tables is "%s" linked '
                                    'to?'%(table), 'Select linking table', 
                                    db.get_linkable_tables(), wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return None
        link_table_to_try = dlg.GetStringSelection()
        link_cols_to_try = []

    dlg = LinkTablesDialog(parent, table, link_table_to_try, 
                           link_cols_to_try, link_cols_to_try)
    if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        return None
    col_pairs = dlg.get_column_pairs()
    
    src_cols = [col_pair[0][1] for col_pair in col_pairs]
    dest_cols = [col_pair[1][1] for col_pair in col_pairs]

    db.do_link_tables(table, link_table_to_try, src_cols, dest_cols)
    # return the newly linked table
    return table



# TODO: make this combobox update as tables are created and deleted.
class TableComboBox(ComboBox):
    '''A combobox for selecting a database table.
    '''
    OTHER_TABLE = '*OTHER TABLE*'
    def __init__(self, parent, id=-1, **kwargs):
        if kwargs.get('choices', None) is None:
            choices = db.get_linkable_tables()
            choices += [TableComboBox.OTHER_TABLE]
        else:
            choices = kwargs['choices']
        ComboBox.__init__(self, parent, id, choices=choices, **kwargs)
        if p.image_table:
            self.SetStringSelection(p.image_table)
        else:
            self.Select(0)


class FilterComboBox(wx.adv.BitmapComboBox):
    '''A combobox for selecting/creating filters. This box will automatically
    update it's choices as filters and gates are created and deleted.
    '''
    NO_FILTER = 'NO FILTER'
    NEW_FILTER = 'CREATE NEW FILTER'
    def __init__(self, parent, id=-1, **kwargs):
        choices = kwargs.get('choices', self.get_choices())
        wx.adv.BitmapComboBox.__init__(self, parent, id, choices=choices, **kwargs)
        self.Select(0)
        self.reset_bitmaps()
        p._filters.addobserver(self.update_choices)
        p.gates.addobserver(self.update_choices)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_COMBOBOX, self.on_select)

    def update_choices(self, evt=None):
        selected_string = self.Value
        self.SetItems(self.get_choices())
        self.reset_bitmaps()
        if selected_string in self.Items:
            self.SetStringSelection(selected_string)
        else:
            self.Select(0)
        self.Layout()
        
    def get_filter_or_none(self):
        '''returns a Filter (or OldFilter) for the selected object or None
        if the selection is NO_FILTER or NEW_FILTER
        '''
        kind = self.get_item_kind(self.GetSelection()) # Fix selection issue
        if kind == 'filter':
            return p._filters[self.Value]
        elif kind == 'gate':
            return p.gates[self.Value].as_filter()
        else:
            return None
        
    def get_choices(self):
        return [FilterComboBox.NO_FILTER] + p._filters_ordered \
               + p.gates_ordered + [FilterComboBox.NEW_FILTER]
    
    def get_item_kind(self, n):
        '''returns the kind of item at index n.
        "gate", "filter" or None if the item is NO_FILTER or NEW_FILTER
        '''
        if n == 0 or n == len(self.Items)-1:
            return None
        elif 0 < n <= len(p._filters_ordered):
            return 'filter'
        else:
            return 'gate'
        
    def get_item_bitmap(self, n):
        '''returns the bitmap corresponding with the nth item'''
        kind = self.get_item_kind(n)
        if kind == 'filter':
            return get_icon("filter").ConvertToBitmap()
        elif kind == 'gate':
            return get_icon("gate").ConvertToBitmap()
        elif self.get_choices()[n] == FilterComboBox.NEW_FILTER:
            return get_icon("filter_new").ConvertToBitmap()
        else:
            return wx.NullBitmap

    def reset_bitmaps(self):
        '''resets the bitmaps associated with each choice. Should be called 
        after updating choices with get_choices() 
        '''
        for i in range(len(self.Items)):
            self.SetItemBitmap(i, self.get_item_bitmap(i))
        
    def on_destroy(self, evt):
        p._filters.removeobserver(self.update_choices)
        p.gates.removeobserver(self.update_choices)
        evt.Skip()
        
    def on_select(self, evt):
        '''Show the ColumnFilterDialog if user wants to make a new filter.'''
        ftr = self.Value
        if ftr == FilterComboBox.NEW_FILTER:
            from .columnfilter import ColumnFilterDialog
            tables = []
            for t in [p.image_table, p.object_table, p.class_table]:
                if isinstance(t, str):
                    tables.append(t)
            cff = ColumnFilterDialog(self, tables=tables, size=(600,150))
            if cff.ShowModal()==wx.OK:
                fltr = cff.get_filter()
                fname = str(cff.get_filter_name())
                p._filters[fname] = fltr
                self.SetStringSelection(fname)
                print((fname, p._filters[fname]))
            else:
                self.Select(0)
            cff.Destroy()
        else:
            evt.Skip()


class GateComboBox(wx.adv.BitmapComboBox, Observable):
    '''A combobox for selecting/creating gates. This box will automatically 
    update its choices as gates are created and deleted.
    '''
    NO_GATE = 'NO GATE'
    NEW_GATE = 'CREATE NEW GATE'
    MANAGE_GATES = 'MANAGE GATES'
    def __init__(self, parent, id=-1, **kwargs):
        self.gatable_columns = None
        wx.adv.BitmapComboBox.__init__(self, parent, id, choices=self.get_choices(), **kwargs)
        self.Select(0)
        self.reset_bitmaps()
        p.gates.addobserver(self.update_choices)
        self.Bind(wx.EVT_COMBOBOX, self.on_select)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        # self.update_info()

    def get_choices(self):
        choices = [GateComboBox.NO_GATE]
        if self.gatable_columns == None:
            choices += p.gates_ordered
        else:
            choices += [g for g in p.gates_ordered 
                        if set(p.gates[g].get_columns()).issubset(self.gatable_columns)]
        choices += [GateComboBox.NEW_GATE, GateComboBox.MANAGE_GATES]
        return choices

    def update_choices(self, evt=None):
        selected_string = self.Value
        self.SetItems(self.get_choices())
        self.reset_bitmaps()
        if selected_string in self.Items:
            self.SetStringSelection(selected_string)
        else:
            self.Select(0)

    def update_info(self):
        # Disabled for now
        return
    #     gate = self.get_gatename_or_none()
    #     if gate:
    #         p._filters[gate] = sqltools.Filter(p.gates[gate].as_filter())

    def get_gatename_or_none(self):
        selection = self.GetSelection() # Fix to replace self.GetStringSelection()
        if self.GetString(selection) in (GateComboBox.NO_GATE, 
                                         GateComboBox.NEW_GATE, 
                                         GateComboBox.MANAGE_GATES):
            return None
        return self.GetString(selection) 
        
    def get_item_bitmap(self, n):
        '''returns the bitmap corresponding with the nth item'''
        if n != 0 and n < len(self.Items)-2:
            return get_icon("gate").ConvertToBitmap()
        elif self.get_choices()[n] == GateComboBox.NEW_GATE:
            return get_icon("gate_new").ConvertToBitmap()
        else:
            return wx.NullBitmap

    def set_gatable_columns(self, columns):
        '''Show only gates that operate on a subset of the specified columns.
        columns -- a list of Columns or None to show all gates
        '''
        assert all([isinstance(c, sqltools.Column) for c in columns])
        self.gatable_columns = columns
        self.update_choices()

    def reset_bitmaps(self):
        '''resets the bitmaps associated with each choice. Should be called 
        after updating choices with get_choices() 
        '''
        for i in range(len(self.Items)):
            self.SetItemBitmap(i, self.get_item_bitmap(i))
            
    def on_select(self, evt):
        if self.Value == GateComboBox.MANAGE_GATES:
            dlg = GateManager(self.Parent)
            dlg.ShowModal()
            dlg.Destroy()
            self.Select(0)
        elif self.Value == GateComboBox.NEW_GATE:
            dlg = GateDialog(self.Parent)
            if dlg.ShowModal() == wx.ID_OK:
                self.Items = self.Items[:-1] + [dlg.Value] + self.Items[-1:]
                self.SetStringSelection(dlg.Value)
                p.gates[dlg.Value] = sqltools.Gate()

                # p._filters[dlg.Value] = sqltools.Filter()

            else:
                self.Select(0)
            dlg.Destroy()
        self.notify(self.get_gatename_or_none())
   
    def on_destroy(self, evt):
        p.gates.removeobserver(self.update_choices)
        evt.Skip()
        

class GateDialog(wx.TextEntryDialog):
    '''A Dialog that asks the user to choose a gate name. This dialog prevents
    the user from specifying gate names that are invalid or already taken.
    '''
    def __init__(self, parent, **kwargs):
        msg = kwargs.pop('message', 'Please name this gate:')
        cap = kwargs.pop('caption', 'New Gate')
        wx.TextEntryDialog.__init__(self, parent, msg, cap, **kwargs)
        self.txtCtrl = self.FindWindowById(3000)
        self.okbtn = self.FindWindowById(5100)
        self.txtCtrl.Bind(wx.EVT_TEXT, self.on_text_input)
        self.okbtn.Bind(wx.EVT_BUTTON, self.on_ok)

    def validate(self):
        val = self.txtCtrl.Value
        if not re.match('^[A-Za-z]\w*$', val):
            return False
        if val in p.gates:
            return False
        if val in p._filters:
            return False
        if val in [GateComboBox.NO_GATE, GateComboBox.NEW_GATE, GateComboBox.MANAGE_GATES]:
            return False
        return True

    def on_ok(self, evt):
        # Even though we disable the OK button we still need to catch this in
        # case ENTER was pressed inside the text box.
        if self.validate():
            evt.Skip()
            
    def on_text_input(self, evt):
        valid = self.validate()
        if not valid:
            self.txtCtrl.SetForegroundColour('red')
        else:
            self.txtCtrl.SetForegroundColour('black') # Text color
        self.okbtn.Enable(valid)
        evt.Skip()
                
        
class TableSelectionDialog(wx.SingleChoiceDialog):
    '''This dialog prompts the user to select a table from a list of all tables
    in the database. More relevant tables are shown at the top.
    '''
    def __init__(self, parent):
        try:
            user_tables = wx.GetApp().user_tables
        except AttributeError:
            # running outside of main UI
            wx.GetApp().user_tables = []
            user_tables = []
            
        primary_tables = [p.image_table]
        if p.object_table:
            primary_tables += [p.object_table]
        primary_tables += user_tables
        other_tables = list(set(db.GetTableNames()) - set(primary_tables))
        wx.SingleChoiceDialog.__init__(self, parent,
                'Select a table to load from the database',
                'Select table from database',
                primary_tables + other_tables,
                wx.CHOICEDLG_STYLE)        


def prompt_user_to_create_loadimages_table(parent, select_gates=[]):
    dlg = CreateLoadImagesTableDialog(parent, select_gates)
    if dlg.ShowModal() == wx.ID_OK:
        from . import tableviewer
        return tableviewer.show_loaddata_table(dlg.get_selected_gates(), dlg.get_gates_as_columns())
    else:
        return None
    
    

class CreateLoadImagesTableDialog(wx.Dialog):
    '''This dialog presents the user with a list of per_image gates which they
    can apply to their per_image data to generate a filtered list of images for
    input to CellProfiler LoadImages.
    '''
    def __init__(self, parent, select_gates=[], **kwargs):
        wx.Dialog.__init__(self, parent, title='Create LoadImages Table', size=(300,200), **kwargs)
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, -1, 'Select gates to apply:')
        self.Sizer.Add(text, 0, wx.TOP|wx.CENTER, 10)
        for g in select_gates:
            for c in p.gates[g].get_columns():
                assert p.image_table==c.table, 'Can only create LoadImages table from per-image gates.'
        gates = [g for g in p.gates_ordered 
                 if all([p.image_table==c.table for c in p.gates[g].get_columns()])]
        self.gate_choices = wx.CheckListBox(self, choices=gates)
        self.gate_choices.SetCheckedStrings(select_gates)
        self.Sizer.Add(self.gate_choices, 1, wx.EXPAND|wx.ALL|wx.CENTER, 10)

        self.gate_columns_check = wx.CheckBox(self, -1, 'Show gates columns?')
        self.Sizer.Add(self.gate_columns_check, 0, wx.BOTTOM|wx.CENTER, 10)
        
        btnsizer = wx.StdDialogButtonSizer()

        helpbtn = wx.Button(self, wx.ID_HELP)
        helpbtn.Bind(wx.EVT_BUTTON, lambda evt: wx.TipWindow(
            self, 'This dialog a list of per_image gates which you may apply'
            'to your per_image data to generate a filtered list of images for'
            'input to CellProfiler LoadImages.\n\n'
            'Select "Show gates as columns" if you would like to output all'
            'image rows with a gate column added for each selected gate. Rows '
            'within the gate will be set to 1 and all others will be 0.\n\n'
            'Leave "Show gates as columns" unchecked if you only want to output'
            'the image rows that are contained by the selected gates.'))
        btnsizer.AddButton(helpbtn)
        
        btn = wx.Button(self, wx.ID_OK, 'Show Table')
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)

        btnsizer.Realize()        
        self.Sizer.Add(btnsizer, 0, wx.EXPAND|wx.BOTTOM, 10)
                
    def get_selected_gates(self):
        return self.gate_choices.GetCheckedStrings()
    
    def get_gates_as_columns(self):
        return self.gate_columns_check.IsChecked()
        
    
    
class GateManager(wx.Dialog):
    def __init__(self, parent, **kwargs):
        kwargs['style'] = kwargs.get('style',wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        wx.Dialog.__init__(self, parent, title="Gate Inspector", **kwargs)
        
        self.gatelist = wx.ListBox(self, choices=p.gates_ordered)
        self.gateinfo = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.deletebtn = wx.Button(self, -1, 'Delete selected gate')
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(wx.StaticText(self, -1, 'Gates:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(-1, 5, 0)
        self.Sizer.Add(self.gatelist, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(-1, 5, 0)
        self.Sizer.Add(self.deletebtn, 0, wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(wx.StaticText(self, -1, 'Gate info:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(-1, 5, 0)
        self.Sizer.Add(self.gateinfo, 2, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(wx.Button(self, wx.ID_OK, 'Close'), 0, wx.ALIGN_RIGHT|wx.ALL, 15 )
        
        self.SetSize((350,350))
        self.SetMinSize((350,350))
        
        self.gatelist.Bind(wx.EVT_LISTBOX, self.on_select)
        self.deletebtn.Bind(wx.EVT_BUTTON, self.on_delete)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        
        p.gates.addobserver(self.update_choices)
        
    def on_destroy(self, evt):
        p.gates.removeobserver(self.update_choices)
        evt.Skip()
        
    def on_select(self, evt):
        self.update_info()
        
    def update_info(self):
        gate = self.gatelist.GetStringSelection()
        self.deletebtn.Enable(gate in p.gates)
        if gate:
            self.gateinfo.Value = str(p.gates[gate])
            # p._filters[gate] = sqltools.Filter(p.gates[gate].as_filter())
        else:
            self.gateinfo.Value = ''

    def update_choices(self, evt):
        sel = self.gatelist.GetStringSelection()
        self.gatelist.SetItems(p.gates_ordered)
        if sel in self.gatelist.Items:
            self.gatelist.Select(sel)
        elif len(self.gatelist.Items) > 0:
            self.gatelist.Select(0)
        self.update_info()
        
    def on_delete(self, evt):
        if self.gatelist.Selection == -1:
            return
        gate = self.gatelist.GetStringSelection()
        dlg = wx.MessageDialog(self, 'Really delete gate "%s"?'%(gate), 
                               'Confirm delete', style=wx.YES_NO|wx.NO_DEFAULT)
        if dlg.ShowModal() == wx.ID_YES:
            p.gates.pop(gate)

            
class CheckListComboBox(wx.ComboCtrl):
    '''A handy concoction for doing selecting multiple items with a ComboBox.
    '''
    def __init__(self, parent, choices=[], **kwargs):
        wx.ComboCtrl.__init__(self, parent, -1, **kwargs)
        self.popup = CheckListComboPopup(choices)
        self.SetPopupControl(self.popup)
        
    def GetCheckList(self):
        return self.popup.checklist
        
    def GetItems(self):
        return self.GetCheckList().GetItems()
    
    def SetItems(self, items):
        self.GetCheckList().SetItems(items)
        
    def GetCheckedStrings(self):
        return self.GetCheckList().GetCheckedStrings()

    def SetCheckedStrings(self, strings):
        self.GetCheckList().SetCheckedStrings(strings)
        self.Value = self.popup.GetStringValue()

        
class CheckListComboPopup(wx.ComboPopup):
    '''A ComboBox that provides a CheckList for multiple selection. Hurray!
    '''
    def __init__(self, choices=[]):
        wx.ComboPopup.__init__(self)
        self.choices = choices

    def on_dclick(self, evt):
        self.Dismiss()

    def GetValue(self):
        return self.checklist.GetCheckedStrings()
    
    # Overridden ComboPopup methods

    def Create(self, parent):
        self.checklist = wx.CheckListBox(parent, -1, choices=self.choices, style=wx.SIMPLE_BORDER)
        self.checklist.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick)

    def GetControl(self):
        return self.checklist

    def GetStringValue(self):
        return ', '.join(self.checklist.GetCheckedStrings())

    def SetStringValue(self, value):
        if type(value)==list:
            self.checklist.SetCheckedStrings(value)

    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        return wx.Size(minWidth, min(100, maxHeight))
    

    
class BitmapPopup(wx.MiniFrame):
    def __init__(self, parent, bitmap, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, **kwargs)
        
        self.bmp = bitmap
        self.SetPosition(kwargs.get('pos', (-1,-1)))
        self.SetSize(bitmap.Size)

        self.Bind(wx.EVT_LEFT_DOWN, lambda e: self.Destroy())
        self.Bind(wx.EVT_PAINT, self._on_paint)

    def _on_paint(self, evt):
        dc = wx.BufferedPaintDC(self)
        dc.DrawBitmap(self.bmp, 0, 0)

        
        
def show_objects_from_gate(gatename, warn=100):
    '''Launch a CellMontageFrame with the objects in the specified gate.
    gatename -- name of the gate to apply
    warn -- specify a number of objects that is considered too many to show at
      once without warning the user and prompting to input how many they want.
      set to None if you don't want to warn for any amount.'''
    q = sqltools.QueryBuilder()
    q.select(sqltools.object_cols())
    q.where([p.gates[gatename]])
    q.group_by(sqltools.object_cols())
    keys = db.execute(str(q))
    keys = [tuple(row) for row in keys]
    if warn and len(keys) > warn:
        te = wx.TextEntryDialog(get_main_frame_or_none(), 'You have selected %s %s. '
                    'How many would you like to show at random?'%(len(keys), 
                    p.object_name[1]), 'Choose # of %s'%
                    (p.object_name[1]), value='100')
        te.ShowModal()
        try:
            numobs = int(te.Value)
            np.random.shuffle(keys)
            keys = keys[:numobs]
        except ValueError:
            wx.MessageDialog(get_main_frame_or_none(), 'You have entered an invalid number', 'Error').ShowModal()
            return
    from . import sortbin
    f = sortbin.CellMontageFrame(get_main_frame_or_none())
    f.Show()
    f.add_objects(keys)
    
def show_images_from_gate(gatename, warn=10):
    '''Callback for "Show images in gate" popup item.
    gatename -- name of the gate to apply
    warn -- specify a number of objects that is considered too many to show at
      once without warning the user and prompting to input how many they want.
      set to None if you don't want to warn for any amount.'''
    q = sqltools.QueryBuilder()
    q.select(sqltools.image_cols())
    q.where([p.gates[gatename]])
    q.group_by(sqltools.image_cols())
    res = db.execute(str(q))
    if warn and len(res) > warn:
        dlg = wx.MessageDialog(get_main_frame_or_none(), 'You are about to open %s '
                'images. This may take some time depending on your settings. '
                'Continue?'%(len(res)),
                'Warning', wx.YES_NO|wx.ICON_QUESTION)
        response = dlg.ShowModal()
        if response != wx.ID_YES:
            return
    logging.info('Opening %s images.'%(len(res)))
    from . import imagetools
    for row in res:
        imagetools.ShowImage(tuple(row), p.image_channel_colors, parent=get_main_frame_or_none())
        
def show_load_dialog():
    '''
    prompt the user to choose a CPA properties file
    or Columbus MeasurementIndex file
    or Harmony PlateResults file.
    '''
    if not wx.GetApp():
        raise Exception("Can't display load dialog without a wx App.")
    dlg = wx.FileDialog(None, 'Select the file containing your properties.', '', '', 
                    'Properties file (*.properties, *.txt)|*.properties;*.txt|'
                    'Columbus MeasurementIndex file (*.ColumbusIDX.xml)|*.ColumbusIDX.xml|'
                    'Harmony PlateResults file (*.xml)|*.xml',
                    style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
    response = dlg.ShowModal()
    
    if response == wx.ID_OK:
        filename = dlg.GetPath()
        path, fname = os.path.split(filename)
        os.chdir(path)  # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        logging.info(f"[Properties]: Loading {fname}")
        if filename.endswith('ColumbusIDX.xml'):
            from .parseperkinelmer import load_columbus
            load_columbus(filename)
        elif filename.endswith('.xml'):
            from .parseperkinelmer import load_harmony
            load_harmony(filename)            
        else:
            p.load_file(filename)

        wx.CallAfter(dlg.Destroy) # Force it to destroy
        return True
    else:
        wx.CallAfter(dlg.Destroy)
        return False

def create_status_bar(parent, force=False):
    if platform.system() == "Darwin" and platform.mac_ver()[0].startswith('11'):
        # wx 4.1.0 crashes on Big Sur if you try to make a status bar.
        # Redirect messages to the log instead.
        # Provide a toolbar if we need to place buttons in the status bar.
        def log_status(text):
            logging.info(text)
        parent.SetStatusText = log_status
        if force:
            tb = wx.ToolBar(parent, style=wx.TB_BOTTOM)
            parent.SetToolBar(tb)
            return tb
        else:
            return None
    else:
        return parent.CreateStatusBar()