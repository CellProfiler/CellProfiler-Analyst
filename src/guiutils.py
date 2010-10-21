import wx
import properties
import dbconnect
from wx.combo import OwnerDrawnComboBox as ComboBox

p = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()

class _ColumnLinkerPanel(wx.Panel):
   def __init__(self, parent, table_a, table_b, allow_delete=True, **kwargs):
      wx.Panel.__init__(self, parent, **kwargs)
      self.table_a = table_a
      self.table_b = table_b
      self.aChoice = ComboBox(self, choices=db.GetColumnNames(table_a), size=(150,-1), style=wx.CB_READONLY)
      self.aChoice.Select(0)
      self.bChoice = ComboBox(self, choices=db.GetColumnNames(table_b), size=(150,-1), style=wx.CB_READONLY)
      self.bChoice.Select(0)
      if allow_delete:
         self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))

      self.Sizer = wx.BoxSizer(wx.HORIZONTAL)
      self.Sizer.Add(wx.StaticText(self, -1, table_a+'.'), 0, wx.TOP, 4)
      self.Sizer.Add(self.aChoice, 1, wx.EXPAND)
      self.Sizer.AddSpacer((10,-1))
      self.Sizer.Add(wx.StaticText(self, -1, '-- MATCHES --'), 0, wx.TOP, 4)
      self.Sizer.AddSpacer((10,-1))
      self.Sizer.Add(wx.StaticText(self, -1, table_b+'.'), 0, wx.TOP, 4)
      self.Sizer.Add(self.bChoice, 1, wx.EXPAND)
      if allow_delete:
         self.Sizer.AddSpacer((10,-1))
         self.Sizer.Add(self.x_btn)
         self.x_btn.Bind(wx.EVT_BUTTON, self.GrandParent.on_remove_panel)
   
   def get_column_pair(self):
      '''
      returns ((table_a, col_a), (table_b, col_b))
      '''
      return ((self.table_a, self.aChoice.Value), 
              (self.table_b, self.bChoice.Value))
         
               
class LinkTablesDialog(wx.Dialog):
   '''
   Prompts the user to specify which columns link the given tables
   '''
   def __init__(self, parent, table_a, table_b, **kwargs):
      wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, **kwargs)

      self.table_a = table_a
      self.table_b = table_b
      self.addbtn = wx.Button(self, -1, 'Add Column')
      self.ok = wx.Button(self, -1, 'OK')
      self.cancel = wx.Button(self, -1, 'Cancel')
      
      self.Sizer = wx.BoxSizer(wx.VERTICAL)
            
      self.Sizer.Add(wx.StaticText(self, -1, 'Select key columns from "%s" and the corresponding columns in "%s"'%(table_a, table_b)), 
                     0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.TOP|wx.CENTER, 10)
      self.Sizer.AddSpacer((-1,10))

      self.sw = wx.ScrolledWindow(self)
      self.panels = [_ColumnLinkerPanel(self.sw, table_a, table_b, False)]
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
      return [p.get_column_pair() for p in self.panels]
      
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
   
   def add_column(self, evt):
      self.panels += [_ColumnLinkerPanel(self.sw, self.table_a, self.table_b)]
      self.sw.Sizer.Add(self.panels[-1], 0, wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, 5)
      self.resize_to_fit()
      
   def resize_to_fit(self):
      w = min(self.sw.Sizer.MinSize[0] + self.Sizer.MinSize[0], 
              wx.GetDisplaySize()[0] - self.Position[0])
      h = min(self.sw.Sizer.MinSize[1] + self.Sizer.MinSize[1],
              wx.GetDisplaySize()[1] - self.Position[1])
      self.SetSize((w,h+7))

        
def get_other_table_from_user(parent):
   '''
   Prompts the user to select a table from a list of tables that they haven't 
   yet accessed in the database.
   '''
   dlg = wx.SingleChoiceDialog(parent, 'Select a table', 'Select a table',
                               db.get_other_table_names(), 
                               wx.CHOICEDLG_STYLE)
   if dlg.ShowModal() == wx.ID_OK:
      table = dlg.GetStringSelection()
      dlg.Destroy()
      return table
   else:
      dlg.Destroy()
      return None
      
class TableComboBox(ComboBox):
   OTHER_TABLE = '*OTHER TABLE*'

   def __init__(self, parent, id=-1, **kwargs):
      if kwargs.get('choices', None) is None:
         choices = [p.image_table]
         if p.object_table: 
            choices += [p.object_table]
         choices += db.table_data.keys()
         choices += [TableComboBox.OTHER_TABLE]
      else:
         choices = kwargs['choices']
      ComboBox.__init__(self, parent, id, choices=choices, **kwargs)
      self.Select(0)

      
      
if __name__ == "__main__":
   app = wx.PySimpleApp()
   
   p.LoadFile('/Users/afraser/cpa_example/example.properties')
      
   dlg = LinkTablesDialog(None, p.object_table, 'class_table')
   if (dlg.ShowModal() == wx.ID_OK):
      print dlg.get_column_pairs()
   
##   f = wx.Frame(None)
##   f.Sizer = wx.BoxSizer()
##   t = TableComboBox(f)
##   f.Sizer.Add(t, 0)
##   f.Show()
   
   app.MainLoop()
   