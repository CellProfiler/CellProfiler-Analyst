import wx
import properties
import dbconnect
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


class TableComboBox(ComboBox):
    OTHER_TABLE = '*OTHER TABLE*'
    def __init__(self, parent, id=-1, **kwargs):
        if kwargs.get('choices', None) is None:
            #choices = [p.image_table]
            #if p.object_table: 
                #choices += [p.object_table]
            choices = db.get_linkable_tables()
            choices += [TableComboBox.OTHER_TABLE]
        else:
            choices = kwargs['choices']
        ComboBox.__init__(self, parent, id, choices=choices, **kwargs)
        if p.image_table:
            self.SetStringSelection(p.image_table)
        else:
            self.Select(0)


if __name__ == "__main__":
    app = wx.PySimpleApp()
    import logging, sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    p.LoadFile('/Users/afraser/cpa_example/example.properties')

    print get_other_table_from_user(None)

    #dlg = LinkTablesDialog(None, p.object_table, p.image_table, dbconnect.object_key_columns(), dbconnect.object_key_columns())
    #if (dlg.ShowModal() == wx.ID_OK):
        #print dlg.get_column_pairs()

##   f = wx.Frame(None)
##   f.Sizer = wx.BoxSizer()
##   t = TableComboBox(f)
##   f.Sizer.Add(t, 0)
##   f.Show()

    app.MainLoop()
