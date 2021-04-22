import logging
import sys
import wx
import re
from time import time
from . import sqltools as sql
from .properties import Properties
from .dbconnect import DBConnect
from wx.adv import OwnerDrawnComboBox as ComboBox

p = Properties()
db = DBConnect()

class ColumnFilterPanel(wx.Panel):
    '''
    Creates a UI that allows the user to create WHERE clauses by selecting 
    1) a DB column name, 2) a comparator, and 3) a value
    '''
    def __init__(self, parent, tables, allow_delete=True, expression=None, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)

        self.fieldSets = []
        self.tables = tables
        self.types = {}
        self.types[p.image_table] = db.GetColumnTypes(p.image_table)
        self.tableChoice = ComboBox(self, choices=self.tables, size=(150,-1), style=wx.CB_READONLY)
        self.tableChoice.Select(0)
        self.colChoice = ComboBox(self, choices=db.GetColumnNames(p.image_table), size=(150,-1), style=wx.CB_READONLY)
        self.colChoice.Select(0)
        self.comparatorChoice = ComboBox(self, size=(80,-1), style=wx.CB_READONLY)
        self.update_comparator_choice()
        self.valueField = wx.ComboBox(self, -1, value='')
        if allow_delete:
            self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))
            
##        if expression is not None:
##            self.set_expression(expression)

        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(self.tableChoice, 1, wx.EXPAND)
        colSizer.AddSpacer(5)
        colSizer.Add(self.colChoice, 1, wx.EXPAND)
        colSizer.AddSpacer(5)
        colSizer.Add(self.comparatorChoice, 1, wx.EXPAND)
        colSizer.AddSpacer(5)
        colSizer.Add(self.valueField, 1, wx.EXPAND)
        if allow_delete:
            colSizer.AddSpacer(5)
            colSizer.Add(self.x_btn, 0, wx.EXPAND)

        self.SetSizer(colSizer)
        self.tableChoice.Bind(wx.EVT_COMBOBOX, self.on_select_table)
        self.colChoice.Bind(wx.EVT_COMBOBOX, self.on_select_col)
        if allow_delete:
            self.x_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        self.Fit()

    def on_remove(self, evt):
        self.GrandParent.remove(self)

    def on_select_col(self, evt):
        self.update_comparator_choice()
        self.update_value_choice()

    def on_select_table(self, evt):
        self.update_col_choice()
        self.update_comparator_choice()
        self.update_value_choice()

    def update_col_choice(self):
        table = self.tableChoice.Value
        self.colChoice.SetItems(db.GetColumnNames(table))
        self.colChoice.Select(0)
        
    def _get_col_type(self):
        table = self.tableChoice.Value
        colidx = self.colChoice.GetSelection()
        return db.GetColumnTypes(table)[colidx]

    def update_comparator_choice(self):
        coltype = self._get_col_type()
        comparators = []
        if coltype == str:
            comparators = ['=', '!=', 'REGEXP', 'IS', 'IS NOT']
        if coltype in (int, float):
            comparators = ['=', '!=', '<', '>', '<=', '>=', 'IS', 'IS NOT']
        self.comparatorChoice.SetItems(comparators)
        self.comparatorChoice.Select(0)

    def update_value_choice(self):
        table = self.tableChoice.Value
        column = self.colChoice.Value
        colidx = self.colChoice.GetSelection()
        coltype = db.GetColumnTypes(table)[colidx]
        vals = []
        # if coltype == str:# or coltype == int or coltype == long:
        #     res = db.execute('SELECT DISTINCT %s FROM %s ORDER BY %s'%(column, table, column))
        #     vals = [str(row[0]) for row in res]
        self.valueField.SetItems(vals)

    def get_filter(self):
        table = self.tableChoice.Value
        column = self.colChoice.Value
        comparator = self.comparatorChoice.GetValue()
        value = self.valueField.GetValue()
        if self._get_col_type() in (int, float):
            # Don't quote numbers
            return sql.Filter(sql.Column(table, column), comparator, '%s'%(value))
        if comparator.upper() in ['IS', 'IS NOT'] and value.upper() == 'NULL':
            # Don't quote comparisons to NULL
            return sql.Filter(sql.Column(table, column), comparator, '%s'%(value))
        return sql.Filter(sql.Column(table, column), comparator, '"%s"'%(value))
    
##    def set_expression(self, expression):
##        '''Populate inputs with expression values'''
##        assert len(expression.get_token_list()) == 3
##        col, comp, val = expression.get_token_list()
##        
##        self.tableChoice.SetStringSelection(col.table)
##        self.update_col_choice()
##        self.colChoice.SetStringSelection(col.col)
##        self.update_comparator_choice()
##        self.comparatorChoice.SetStringSelection(comp)
##        self.update_value_choice()
##        self.valueField.SetValue(val)


class ColumnFilterDialog(wx.Dialog):
    '''
    Dialog for building Filters on the fly.
    '''
    def __init__(self, parent, tables, **kwargs):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwargs)

        self.tables = tables
        self.conjunctions = []
        self.filter_name = wx.TextCtrl(self, -1, '')
##        self.filter_name = ComboBox(self, choices=p._filters_ordered)
##        self.filter_name.SetStringSelection('My_Filter')
        self.addbtn = wx.Button(self, -1, 'Add Column')
        self.testbtn = wx.Button(self, -1, 'Test Filter')
        self.testlabel = wx.StaticText(self, label='')
        self.ok = wx.Button(self, -1, 'OK')
        self.cancel = wx.Button(self, -1, 'Cancel')

        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Name your filter: '), 0, wx.CENTER)
        sz.Add(self.filter_name, 1, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(-1, 5, 0)

        self.Sizer.Add(wx.StaticText(self, -1, 'Choose constraints for your filter: '), 0, wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.Sizer.Add(-1, 10, 0)

        self.sw = wx.ScrolledWindow(self)
        self.panels = [ColumnFilterPanel(self.sw, tables, False)]
        self.sw.Sizer = wx.BoxSizer(wx.VERTICAL)
        (w,h) = self.sw.Sizer.GetSize()
        self.sw.SetScrollbars(20,20,w//20,h//20,0,0)
        self.sw.Sizer.Add(self.panels[0], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.Sizer.Add(self.sw, 1, wx.EXPAND)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddSpacer(10)
        sz.Add(self.addbtn, 0)
        sz.AddSpacer(3)
        sz.Add(self.testbtn, 0)
        sz.AddSpacer(3)
        sz.Add(self.testlabel, 0, wx.ALIGN_CENTER_VERTICAL)

        sz.AddStretchSpacer()
        sz.Add(self.ok, 0)
        sz.AddSpacer(10)
        sz.Add(self.cancel, 0)
        sz.AddSpacer(10)

        self.Sizer.Add(0,10)
        self.Sizer.Add(sz, 0, wx.EXPAND)
        self.Sizer.Add(-1,10)

        self.validate_filter_name()

        self.addbtn.Bind(wx.EVT_BUTTON, self.on_add_column)
        self.testbtn.Bind(wx.EVT_BUTTON, self.on_test)
        self.ok.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.filter_name.Bind(wx.EVT_TEXT, self.validate_filter_name)
##        self.filter_name.Bind(wx.EVT_COMBOBOX, self.on_select_existing_filter)
        if sys.platform == 'win32':
            self.size_mod = 30
        else:
            self.size_mod = 7
        self.resize_to_fit()

    def reset(self):
        for panel in self.panels[1:]:
            self.remove(panel)
        self.Refresh()
        
    def on_ok(self, evt):
        self.EndModal(wx.OK)

    def on_cancel(self, evt):
        self.EndModal(wx.CANCEL)

    def validate_filter_name(self, evt=None):
        name = self.get_filter_name()
        self.ok.Enable()
        self.filter_name.SetForegroundColour('black')
        if (name in p._filters
            or name in p.gates
            or not re.match('^[A-Za-z]\w*$',name)):
            self.ok.Disable() 
            self.filter_name.SetForegroundColour('red')

    def get_filter(self):
        fltr = self.panels[0].get_filter()
        for i, conj in enumerate(self.conjunctions):
            fltr.append_expression(conj.GetStringSelection(), 
                                   *self.panels[i+1].get_filter().get_token_list())
        return fltr

    def get_filter_name(self):
        return str(self.filter_name.Value) # do NOT return unicode

    def remove(self, panel):
        i = self.panels.index(panel)
        if 0 < i <= len(self.conjunctions):
            self.conjunctions.pop(i-1).Destroy()
        self.panels.remove(panel)
        panel.Destroy()
        self.sw.FitInside()
        self.resize_to_fit()

    def on_add_column(self, evt):
        self.add_column()

    def add_column(self, conjunction='AND', expression=None):
        '''expression -- sqltools.Expression instance
        '''
        self.panels += [ColumnFilterPanel(self.sw, self.tables, expression=expression)]
        self.conjunctions += [wx.Choice(self.sw, -1, choices=['AND', 'OR'])]
        self.conjunctions[-1].SetStringSelection(conjunction)
        self.sw.Sizer.Add(self.conjunctions[-1], 0, wx.CENTER|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.sw.Sizer.Add(self.panels[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
        self.sw.FitInside()
        self.resize_to_fit()

    def on_test(self, evt):
        fltr = self.get_filter()
        logging.info(f"Testing filter: {fltr}")
        self.testlabel.SetLabelText(f"Testing filter...")
        try:
            t0 = time()
            data = db.GetFilteredObjects(fltr, random=False)
            t1 = time()
            num_ims = len(set([x for x, _ in data]))
            logging.info(f"Filter found {len(data)} {p.object_name[1]} from {num_ims} images in {(t1 - t0):.2f}s")
            self.testlabel.SetLabelText(f"[OK] Found {len(data)} {p.object_name[1]} from {num_ims} images in {(t1 - t0):.2f}s")
        except Exception as exc:
            logging.error(f"Filter Failed: {exc}")
            last_err = list(filter(None, str(exc).split('\n')))[-1]
            self.testlabel.SetLabelText(f"[ERROR] {last_err}")

    def resize_to_fit(self):
        w = min(self.sw.Sizer.MinSize[0] + self.Sizer.MinSize[0], 
                wx.GetDisplaySize()[0] - self.Position[0])
        h = min(self.sw.Sizer.MinSize[1] + self.Sizer.MinSize[1],
                wx.GetDisplaySize()[1] - self.Position[1])
        self.SetSize((w, h + self.size_mod))
##    def on_select_existing_filter(self, evt):
##        self.load_existing_filter(self.filter_name.GetStringSelection())
        
##    def load_existing_filter(self, filter_name):
##        # TODO: make this work so filters can be modified.
##        fltr = p._filters[filter_name]
##        if isinstance(fltr, sql.Filter):
##            self.reset()
##            self.panels[0].set_expression(fltr.get_sub_expressions()[0])
##            for conj, exp in zip(fltr.get_conjunctions(), fltr.get_sub_expressions()[1:]):
##                self.add_column(conj, exp)
##        else:
##            self.reset()
##            logging.error('Can not load old filter')
##        self.Refresh()



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = wx.App()
    
    # Load a properties file if passed in args
    if p.show_load_dialog():
        p._filters['test'] = sql.Filter(('per_image', 'gene'), 'REGEXP', 'MAP*',
                                    'OR', sql.Column('per_image', 'gene'), 'IS', 'NULL')
        p._filters_ordered += ['test']

        p._filters['test2'] = sql.Filter(('per_image', 'well'), '!=', 'A01')
        p._filters_ordered += ['test2']

        cff = ColumnFilterDialog(None, tables=[p.image_table])
        if cff.ShowModal()==wx.OK:
            print((cff.get_filter()))

        cff.Destroy()
        app.MainLoop()