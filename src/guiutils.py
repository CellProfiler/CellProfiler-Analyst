import wx
import wx.combo
import re
import icons
import properties
import dbconnect
import sqltools
from wx.combo import OwnerDrawnComboBox as ComboBox

p = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()

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
        self.Sizer.AddSpacer((10,-1))
        self.Sizer.Add(wx.StaticText(self, -1, '<=>'), 0, wx.TOP, 4)
        self.Sizer.AddSpacer((10,-1))
        self.Sizer.Add(wx.StaticText(self, -1, table_b+'.'), 0, wx.TOP, 4)
        self.Sizer.Add(self.bChoice, 1, wx.EXPAND)
        if allow_delete:
            self.Sizer.AddSpacer((10,-1))
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
        self.Sizer.AddSpacer((-1,10))

        self.sw = wx.ScrolledWindow(self)
        if a_cols:
            self.panels = [_ColumnLinkerPanel(self.sw, table_a, table_b, a_cols[0], b_cols[0], allow_delete=False)]
            a_cols = a_cols[1:]
            b_cols = b_cols[1:]
        else:
            self.panels = [_ColumnLinkerPanel(self.sw, table_a, table_b, allow_delete=False)]
        self.sw.EnableScrolling(x_scrolling=False, y_scrolling=True)
        self.sw.Sizer = wx.BoxSizer(wx.VERTICAL)
        (w,h) = self.sw.Sizer.GetSize()
        self.sw.SetScrollbars(20,20,w/20,h/20,0,0)
        self.sw.Sizer.Add(self.panels[0], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.Sizer.Add(self.sw, 1, wx.EXPAND)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddSpacer((10,-1))
        sz.Add(self.addbtn, 0)
        sz.AddStretchSpacer()
        sz.Add(self.ok, 0)
        sz.AddSpacer((10,-1))
        sz.Add(self.cancel, 0)
        sz.AddSpacer((10,-1))

        self.Sizer.AddSpacer((-1,10))
        self.Sizer.Add(sz, 0, wx.EXPAND)
        self.Sizer.AddSpacer((-1,10))

        for cola, colb in zip(a_cols, b_cols):
            self.add_column(cola, colb)

        if 'size' not in kwargs.keys():
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
        from tableviewer import TableViewer
        tableview = TableViewer(wx.GetApp().__dict__.get('frame', None))
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
            wx.MessageDialog('Sorry, CPA does not currently support multiple\n'
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
            wx.MessageDialog('Sorry, CPA does not currently support multiple\n'
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


class FilterComboBox(wx.combo.BitmapComboBox):
    '''A combobox for selecting/creating filters. This box will automatically
    update it's choices as filters and gates are created and deleted.
    '''
    NO_FILTER = 'NO FILTER'
    NEW_FILTER = 'CREATE NEW FILTER'
    def __init__(self, parent, id=-1, **kwargs):
        choices = kwargs.get('choices', self.get_choices())
        wx.combo.BitmapComboBox.__init__(self, parent, id, choices=choices, **kwargs)
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
        self.SetStringSelection(selected_string)
        self.Layout()
        
    def get_filter_or_none(self):
        '''returns a sqltools.Filter object for the selected object or None
        if the selection is NO_FILTER or NEW_FILTER
        '''
        kind = self.get_item_kind(self.Selection)
        if kind == 'filter':
            return p._filters[self.Value]
        elif kind == 'gate':
            return p.gates[self.Value].as_filter()
        else:
            return None
        
    def get_choices(self):
        choices = [FilterComboBox.NO_FILTER] + p._filters_ordered
        choices += [g for g in p.gates_ordered 
                    if all([p.image_table==t for t in p.gates[g].get_tables()])] 
        choices += [FilterComboBox.NEW_FILTER]
        return choices
    
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
            return icons.filter.ConvertToBitmap()
        elif kind == 'gate':
            return icons.gate.ConvertToBitmap()
        elif self.get_choices()[n] == FilterComboBox.NEW_FILTER:
            return icons.filter_new.ConvertToBitmap()
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
            from columnfilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(600,150))
            if cff.ShowModal()==wx.OK:
                fltr = cff.get_filter()
                fname = str(cff.get_filter_name())
                p._filters[fname] = fltr
                self.SetStringSelection(fname)
            else:
                self.Select(0)
            cff.Destroy()
        else:
            evt.Skip()

        
class GateComboBox(wx.combo.BitmapComboBox):
    '''A combobox for selecting/creating gates. This box will automatically 
    update it's choices as gates are created and deleted.
    '''
    NO_GATE = 'NO GATE'
    NEW_GATE = 'CREATE NEW GATE'
    MANAGE_GATES = 'MANAGE GATES'
    def __init__(self, parent, id=-1, **kwargs):
        choices = kwargs.get('choices', self.get_choices())
        wx.combo.BitmapComboBox.__init__(self, parent, id, choices=choices, **kwargs)
        self.Select(0)
        self.reset_bitmaps()
        p.gates.addobserver(self.update_choices)
        self.Bind(wx.EVT_COMBOBOX, self.on_select)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        
    def get_choices(self):
        return [GateComboBox.NO_GATE] + p.gates_ordered + [GateComboBox.NEW_GATE, GateComboBox.MANAGE_GATES]

    def update_choices(self, evt=None):
        selected_string = self.Value
        self.SetItems(self.get_choices())
        self.reset_bitmaps()
        if selected_string in self.Items:
            self.SetStringSelection(selected_string)
        else:
            self.Select(0)
        
    def get_gate_or_none(self):
        if self.Value in (GateComboBox.NO_GATE, GateComboBox.NEW_GATE, GateComboBox.MANAGE_GATES):
            return None
        return self.Value
        
    def get_item_bitmap(self, n):
        '''returns the bitmap corresponding with the nth item'''
        if n != 0 and n < len(self.Items)-2:
            return icons.gate.ConvertToBitmap()
        elif self.get_choices()[n] == GateComboBox.NEW_GATE:
            return icons.gate_new.ConvertToBitmap()
        else:
            return wx.NullBitmap

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
            self.Select(0)
        evt.Skip()
        
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
        if not re.match('^[A-Za-z0-9]\w*$', val):
            return False
        if val in p.gates.keys():
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
            self.txtCtrl.SetForegroundColour('black')
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


def prompt_user_to_create_loadimages_table(parent, select_gates):
    dlg = CreateLoadImagesTableDialog(parent, select_gates)
    if dlg.ShowModal() == wx.ID_OK:
        import tableviewer
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
        gates = [g for g in p.gates_ordered 
                 if all([p.image_table==c.table for c in p.gates[g].get_columns()])]
        self.gate_choices = wx.CheckListBox(self, choices=gates)
        self.gate_choices.SetCheckedStrings(select_gates)
        self.Sizer.Add(self.gate_choices, 1, wx.EXPAND|wx.ALL|wx.CENTER, 10)

        self.gate_columns_check = wx.CheckBox(self, -1, 'Show gates columns?')
        self.Sizer.Add(self.gate_columns_check, 0, wx.BOTTOM|wx.CENTER, 10)
        
        btnsizer = wx.StdDialogButtonSizer()

        helpbtn = wx.Button(self, wx.ID_HELP)
        helpbtn.Bind(wx.EVT_BUTTON, lambda(evt): wx.TipWindow(
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
        kwargs['style'] = kwargs.get('style',wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME)
        wx.Dialog.__init__(self, parent, title="Gate Inspector", **kwargs)
        
        self.gatelist = wx.ListBox(self, choices=p.gates_ordered)
        self.gateinfo = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.deletebtn = wx.Button(self, -1, 'Delete selected gate')
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(wx.StaticText(self, -1, 'Gates:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer((-1,5))
        self.Sizer.Add(self.gatelist, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer((-1,5))
        self.Sizer.Add(self.deletebtn, 0, wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(wx.StaticText(self, -1, 'Gate info:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer((-1,5))
        self.Sizer.Add(self.gateinfo, 2, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(wx.Button(self, wx.ID_OK, 'Close'), 0, wx.ALIGN_RIGHT|wx.ALL, 15 )
        
        self.SetSize((350,350))
        self.SetMinSize((350,350))
        
        self.gatelist.Bind(wx.EVT_LISTBOX, self.on_select)
        self.deletebtn.Bind(wx.EVT_BUTTON, self.on_delete)
        
        p.gates.addobserver(self.update_choices)
        
    def on_select(self, evt):
        self.update_info()
        
    def update_info(self):
        gate = self.gatelist.GetStringSelection()
        self.deletebtn.Enable(gate in p.gates_ordered)
        self.gateinfo.Value = str(p.gates[gate]) if gate else ''
        
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

class CheckListComboBox(wx.combo.ComboCtrl):
    '''A handy concoction for doing selecting multiple items with a ComboBox.
    '''
    def __init__(self, parent, choices, **kwargs):
        wx.combo.ComboCtrl.__init__(self, parent, -1, **kwargs)
        self.checklist = CheckListComboPopup(choices)
        self.SetPopupControl(self.checklist)
        
    def GetValue(self):
        return self.checklist.GetValue()
    Value = property(GetValue)


class CheckListComboPopup(wx.combo.ComboPopup):
    '''A ComboBox that provides a CheckList for multiple selection. Hurray!
    '''
    def __init__(self, choices):
        wx.combo.ComboPopup.__init__(self)
        self.choices = choices

    def on_dclick(self, evt):
        self.Dismiss()

    def GetValue(self):
        return self.list.GetCheckedStrings()

    # Overridden ComboPopup methods

    def Create(self, parent):
        self.list = wx.CheckListBox(parent, -1, choices=self.choices, style=wx.SIMPLE_BORDER)
        self.list.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick)

    def GetControl(self):
        return self.list

    def GetStringValue(self):
        return ', '.join(self.list.GetCheckedStrings())

    def SetStringValue(self, value):
        if type(value)==list:
            self.list.SetCheckedStrings(value)

    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        return wx.Size(minWidth, min(100, maxHeight))
    

if __name__ == "__main__":
    app = wx.PySimpleApp()
    import logging, sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    p.load_file('/Users/afraser/cpa_example/example.properties')

    d = GateManager(None)
    d.ShowModal()
##    print get_other_table_from_user(None)

    #dlg = LinkTablesDialog(None, p.object_table, p.image_table, dbconnect.object_key_columns(), dbconnect.object_key_columns())
    #if (dlg.ShowModal() == wx.ID_OK):
        #print dlg.get_column_pairs()

##   f = wx.Frame(None)
##   f.Sizer = wx.BoxSizer()
##   t = TableComboBox(f)
##   f.Sizer.Add(t, 0)
##   f.Show()

    app.MainLoop()
