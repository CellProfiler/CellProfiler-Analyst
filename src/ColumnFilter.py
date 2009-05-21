import sys
import wx
from Properties import Properties
from DBConnect import DBConnect


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
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.fieldSets = []
        
        self.cols = db.GetColumnNames(p.image_table)
        self.types = db.GetColumnTypes(p.image_table)
        colChoice = wx.Choice(self, choices=self.cols, size=(150,-1))
        #colChoice.Select(0)
        comparatorChoice = wx.Choice(self, choices=self.GetComparatorsForType(self.types[0]))
        valueField = wx.ComboBox(self, -1, value='', choices=self.GetValueChoicesForColumnIdx(colChoice.GetSelection()))
        
        self.okBtn = wx.Button(self, -1, 'OK')
        self.fieldSets += [[colChoice, comparatorChoice, valueField]]
        
        colSizer = wx.BoxSizer(wx.HORIZONTAL)
        colSizer.Add(colChoice)
        colSizer.AddSpacer((5,20))
        colSizer.Add(comparatorChoice)
        colSizer.AddSpacer((5,20))
        colSizer.Add(valueField)
        
        rowSizer = wx.BoxSizer(wx.VERTICAL)
        rowSizer.Add(colSizer)
        rowSizer.Add(self.okBtn)
        
        self.SetSizer(rowSizer)
        colChoice.Bind(wx.EVT_CHOICE, self.OnSelectColumn)
        
    def GetComparatorsForType(self, colType):
        if colType == str:
            return ['=', '!=', 'REGEXP']
        if colType == int or colType == float or colType == long:
            return ['=', '!=', '<', '>', '<=', '>=']
        return []
    
    def GetValueChoicesForColumnIdx(self, index):
        column = self.cols[index]
        colType = self.types[index]
        res = db.execute('SELECT %s FROM %s GROUP BY %s'%(column, p.image_table, column))
        if colType == str or colType == int or colType == long:
            return [str(row[0]) for row in res]
        if colType == float:
            return []
        
    def OnSelectColumn(self, evt):
        evtObj = evt.GetEventObject()
        for fieldSet in self.fieldSets:
            if fieldSet[0] == evtObj:
                selIdx = fieldSet[0].GetSelection()
                fieldSet[1].SetItems(self.GetComparatorsForType(self.types[selIdx]))
                fieldSet[2].SetItems(self.GetValueChoicesForColumnIdx(fieldSet[0].GetSelection()))
                

class ColumnFilterFrame(wx.Frame):
    def __init__(self, parent, **kwargs):
        wx.Frame.__init__(self, parent, -1, **kwargs)
        self.panel = ColumnFilterPanel(self, **kwargs)
    

    
if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        p.LoadFile('../properties/nirht_test.properties')
        #p.LoadFile('../properties/Gilliland_LeukemiaScreens_Validation.properties')


    cff = ColumnFilterFrame(None)
    cff.Show()

    app.MainLoop()