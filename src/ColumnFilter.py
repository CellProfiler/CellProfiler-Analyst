import sys
import wx
from Filter import Filter
from Properties import Properties
from DBConnect import DBConnect
from wx.combo import OwnerDrawnComboBox as ComboBox


p = Properties.getInstance()
db = DBConnect.getInstance()

#
# under construction
#

class ColumnFilterPanel(wx.Panel):
    '''
    Experimental.  Creates a UI that allows the user to create WHERE clauses
    by selecting 1) a DB column name, 2) a comparator, and 3) a value
    '''
    def __init__(self, parent, tables, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.fieldSets = []
        self.tables = tables
        self.types = {}
        self.types[p.image_table] = db.GetColumnTypes(p.image_table)
        self.tableChoice = ComboBox(self, choices=self.tables, size=(150,-1))
        self.tableChoice.Select(0)
        self.colChoice = ComboBox(self, choices=db.GetColumnNames(p.image_table), size=(150,-1), style=wx.CB_READONLY)
        self.comparatorChoice = ComboBox(self)
        self.update_comparator_choice()
        self.valueField = wx.ComboBox(self, -1, value='')
        
        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(self.tableChoice, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.colChoice, 1, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.comparatorChoice, 0.5, wx.EXPAND)
        colSizer.AddSpacer((5,-1))
        colSizer.Add(self.valueField, 1, wx.EXPAND)
        
        self.SetSizer(colSizer)
        self.tableChoice.Bind(wx.EVT_COMBOBOX, self.on_select_table)
        self.colChoice.Bind(wx.EVT_COMBOBOX, self.on_select_col)
        
    def on_select_col(self, evt):
        self.update_comparator_choice()
        self.update_value_choice()
        
    def on_select_table(self, evt):
        self.update_col_choice()
        self.update_comparator_choice()
        self.update_value_choice()
        
    def update_col_choice(self):
        table = self.tableChoice.GetStringSelection()
        self.colChoice.SetItems(db.GetColumnNames(table))
        self.colChoice.Select(0)
        
    def update_comparator_choice(self):
        table = self.tableChoice.GetStringSelection()
        colidx = self.colChoice.GetSelection()
        coltype = db.GetColumnTypes(table)[colidx]
        print coltype
        comparators = []
        if coltype in [str, unicode]:
            comparators = ['=', '!=', 'REGEXP']
        if coltype in [int, float, long]:
            comparators = ['=', '!=', '<', '>', '<=', '>=']
        self.comparatorChoice.SetItems(comparators)
        self.comparatorChoice.Select(0)
        
    def update_value_choice(self):
        table = self.tableChoice.GetStringSelection()
        column = self.colChoice.GetStringSelection()
        colidx = self.colChoice.GetSelection()
        coltype = db.GetColumnTypes(table)[colidx]
        vals = []
        if coltype == str:# or coltype == int or coltype == long:
            res = db.execute('SELECT DISTINCT %s FROM %s ORDER BY %s'%(column, table, column))
            vals = [str(row[0]) for row in res]
        self.valueField.SetItems(vals)
    
    def get_filter(self):
        table = self.tableChoice.GetStringSelection()
        column = self.colChoice.GetStringSelection()
        comparator = self.comparatorChoice.GetStringSelection()
        value = self.valueField.GetValue()
        return Filter(table, column, comparator, value)
        
                
class ColumnFilterFrame(wx.Frame):
    def __init__(self, parent, tables, **kwargs):
        wx.Frame.__init__(self, parent, -1, **kwargs)
        self.tables = tables
        self.panels = [ColumnFilterPanel(self, tables)]
        self.addbtn = wx.Button(self, -1, 'Add Column')
        self.ok = wx.Button(self, -1, 'OK')
        self.cancel = wx.Button(self, -1, 'Cancel')
        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(vsizer)
        hsizer.Add(self.ok)
        hsizer.Add(self.cancel)
        vsizer.Add(self.panels[0])
        vsizer.Add(self.addbtn)
        vsizer.Add(hsizer)
        
        self.addbtn.Bind(wx.EVT_BUTTON, self.add_column)
        self.ok.Bind(wx.EVT_BUTTON, lambda(x):self.EndModal(wx.OK))
        self.cancel.Bind(wx.EVT_BUTTON, lambda(x):self.EndModal(wx.CANCEL))
        
    def get_filter(self):
        filter = Filter()
        for panel in self.panels:
            filter += panel.get_filter()
        return filter
    
    def add_column(self, evt):
        self.panels += [ColumnFilterPanel(self, self.tables)]
        self.GetSizer().Insert(len(self.panels)-1, self.panels[-1])
        self.Layout()

    
if __name__ == "__main__":
    
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    app = wx.PySimpleApp()
    
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        p.LoadFile('/Users/afraser/Desktop/cpa_example/example.properties')
        #p.LoadFile('../properties/Gilliland_LeukemiaScreens_Validation.properties')


    cff = ColumnFilterFrame(None, tables=[p.image_table], size=(550,-1))
    if cff.Show(True)==wx.OK:
        print cff.get_filter()
    cff.Destroy()

    app.MainLoop()