# -*- Encoding: utf-8 -*-
import os
import re
import wx
import wx.wizard as wiz
from DBConnect import DBConnect
from Properties import Properties

def makePageTitle(wizPg, title):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(wizPg, -1, title)
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.AddWindow(wx.StaticLine(wizPg, -1), 0, wx.EXPAND|wx.ALL, 5)
        return sizer
     
    
class Page1(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Connect (step 1 of 5)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        directions = wx.StaticText(self, -1, "Load a Properties file that contains the database info below.", style=wx.ALIGN_CENTRE)
        browseBtn = wx.Button(self, wx.NewId(), 'Choose file…')
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, browseBtn)
        label_2 = wx.StaticText(self, -1, "DB Host: ")
        self.lblDBHost = wx.StaticText(self, -1, "")
        label_3 = wx.StaticText(self, -1, "DB Name: ")
        self.lblDBName = wx.StaticText(self, -1, "")
        self.btnTest = wx.Button(self, -1, "Test")
        width, height = self.btnTest.GetSize()
        self.btnTest.SetMinSize((200, height))
        self.btnTest.Disable()
        
        label_2.SetMinSize((59, 16))
        self.lblDBHost.SetMinSize((250, 22))
        label_3.SetMinSize((66, 16))
        self.lblDBName.SetMinSize((250, 22))
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridsizer = wx.GridSizer(5, 2, 5, 5)
        sizer1.Add(directions, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(browseBtn, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        gridsizer.Add(label_2, 0, wx.ALIGN_RIGHT, 0)
        gridsizer.Add(self.lblDBHost, 1, 0, 0)
        gridsizer.Add(label_3, 0, wx.ALIGN_RIGHT, 0)
        gridsizer.Add(self.lblDBName, 1, 0, 0)
        sizer1.Add(gridsizer, 0, 0, 0)
        sizer1.Add(self.btnTest, 0, wx.ALIGN_CENTER)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.btnTest.Bind(wx.EVT_BUTTON, self.OnTest)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

    def OnBrowse(self, evt):
        dlg = wx.FileDialog(self, "Select a property file", defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            p = Properties.getInstance()
            p.LoadFile(dlg.GetPath())
            self.lblDBHost.SetLabel(p.db_host)
            self.lblDBName.SetLabel(p.db_name)
            self.btnTest.SetLabel('Test')
            self.btnTest.Enable()
        
    def OnTest(self, evt):
        p = Properties.getInstance()
        db = DBConnect.getInstance()
        try:
            db.Disconnect()
            db.Connect(db_host=p.db_host, db_name=p.db_name, db_user=p.db_user, db_passwd=p.db_passwd)
            self.btnTest.SetLabel('Connection OK')
            wx.FindWindowById(wx.ID_FORWARD).Enable()
        except:
            self.btnTest.SetLabel('Connection Failed')
        self.btnTest.Disable()
            
    def OnPageChanging(self,evt):
        p = Properties.getInstance()
        db = DBConnect.getInstance()
        try:
            db.Disconnect()
            db.Connect(db_host=p.db_host, db_name=p.db_name, db_user=p.db_user, db_passwd=p.db_passwd)
            self.btnTest.SetLabel('Connection OK')
            wx.FindWindowById(wx.ID_FORWARD).Enable()
            self.Parent.inDB = self.Parent.outDB = p.db_name
        except:
            self.btnTest.SetLabel('Connection Failed')
            evt.Veto()
        self.btnTest.Disable()
        
        
        
class Page2(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Choose Tables (step 2 of 5)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        self.directions = wx.StaticText(self, -1, "Select the tables you wish to include in the master.", style=wx.ALIGN_CENTRE)
        self.listTables = wx.ListBox(self, -1, choices=[], style=wx.LB_EXTENDED)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(self.directions, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.listTables, 1, wx.EXPAND, 0)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.listTables.Bind(wx.EVT_LISTBOX, self.OnSelectItem)
        
    def OnPageLoaded(self, evt):
        self.listTables.Clear()
        db = DBConnect.getInstance()
        db.Execute("SHOW TABLES")
        r = db.GetResultsAsList()
        perObTables = [t[0] for t in r if t[0][-10:].lower() == 'per_object']
        perImTables = [t[0] for t in r if t[0][-9:].lower() == 'per_image']
        for im in perImTables[::-1]:
            for ob in perObTables:
                if ob.startswith(im[:-9]):         # if prefixes match, add these two tables
                    prefix = ob[:-10].rstrip('_')
                    self.listTables.Insert(prefix+' ('+im+' / '+ob+')', 0, (im,ob))

    def OnSelectItem(self,evt):
        self.Parent.perImageTables = [self.listTables.GetClientData(i)[0] for i in self.listTables.GetSelections()]
        self.Parent.perObjectTables = [self.listTables.GetClientData(i)[1] for i in self.listTables.GetSelections()]
        self.directions.SetForegroundColour('#000001')
            
    def OnPageChanging(self,evt):
        if self.listTables.GetSelections() == () and evt.GetDirection() == True:
            evt.Veto()
            self.directions.SetForegroundColour('#FF0000')
        
        
        
class Page3(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Choose Export Database (step 3 of 5)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        label_1 = wx.StaticText(self, -1, "Connect to the database that contains the tables you wish to use in your analysis.", style=wx.ALIGN_CENTRE)
        self.radioDBSelect = wx.RadioBox(self, -1, "", choices=["Current database", "Other (specify below)"], majorDimension=0, style=wx.RA_SPECIFY_ROWS)
        self.otherDB = wx.StaticText(self, -1, 'Enter other name here (if chosen): ')
        self.txtOtherDB = wx.TextCtrl(self, -1, "")
        self.txtOtherDB.Disable()
        self.otherDB.Disable()
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(label_1, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.radioDBSelect, 1, wx.EXPAND, 0)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.otherDB, 0, wx.TOP|wx.BOTTOM|wx.LEFT, 10)
        sizer2.Add(self.txtOtherDB, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 10)
        sizer1.Add(sizer2)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.radioDBSelect.Bind(wx.EVT_RADIOBOX, self.OnRadioSelect)
        self.txtOtherDB.Bind(wx.EVT_TEXT, self.OnText)

    def OnPageLoaded(self, evt):
        self.radioDBSelect.SetItemLabel(0,'Current database: "'+self.Parent.inDB+'"')
        wx.FindWindowById(wx.ID_FORWARD).Enable()
        self.OnRadioSelect(None)
      
    def OnRadioSelect(self, evt):
        if self.radioDBSelect.Selection == 0:
            self.txtOtherDB.Disable()
            self.txtOtherDB.Clear()
            self.otherDB.SetForegroundColour('#CCCCCC')
            self.Parent.outDB = self.Parent.inDB
        else:
            self.txtOtherDB.Enable()
            self.otherDB.SetForegroundColour('#000001')
            
    def OnPageChanging(self,evt):
        if self.radioDBSelect.Selection == 1 and self.txtOtherDB.GetValue() == '' and evt.GetDirection() == True:
            evt.Veto()
            self.otherDB.SetForegroundColour('#FF0000')
            
    def OnText(self, evt):
        #TODO: Validate me, or display a list of DBs to choose from
        self.Parent.outDB = self.txtOtherDB.GetValue()
        
        
class Page4(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Choose Prefix (step 4 of 5)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        label_1 = wx.StaticText(self, -1, 'Enter a prefix name for your CPA master tables.', style=wx.ALIGN_CENTRE)
        self.txtPrefix = wx.TextCtrl(self, -1, 'CPA')
        self.example = wx.StaticText(self, -1, 'Output tables: "CPA_Per_Image", "CPA_Per_Object"')
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(label_1, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.txtPrefix, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.example, 0, wx.ALL|wx.EXPAND, 10)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.txtPrefix.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.OnText(None)
    
    def OnText(self, evt):
        nameRules = re.compile('[a-zA-Z0-9]\w*$')
        if nameRules.match(self.txtPrefix.GetValue()):        
            self.Parent.outPerImage = self.txtPrefix.GetValue()+'_Per_Image'
            self.Parent.outPerObject = self.txtPrefix.GetValue()+'_Per_Object'
            self.example.SetLabel('Output tables: '+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.txtPrefix.GetValue()+'_table_index')
        else:
            self.example.SetLabel('Invalid table prefix.')
            
    def OnPageChanging(self,evt):
        if self.example.GetLabel() == 'Invalid table prefix.' and evt.GetDirection() == True:
            evt.Veto()  
            
            
            
class Page5(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Summary (step 5 of 5)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        label_1 = wx.StaticText(self, -1, 'Confirm that the following information is correct and click "Finish".', style=wx.ALIGN_CENTRE)
        self.outDB = wx.StaticText(self, -1, 'Database to write to: ')
        self.inTables = wx.StaticText(self, -1, 'Tables to merge: ')
        self.outTables = wx.StaticText(self, -1, 'Tables to write: ')
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(label_1, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.outDB, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.inTables, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.outTables, 0, wx.ALL|wx.EXPAND, 10)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnFinish)

    def OnPageLoaded(self, evt):
        import string
        self.outDB.SetLabel('Database to write to: '+self.Parent.outDB)
        self.inTables.SetLabel('Tables to merge: \n'+string.join([str(t[0])+', '+str(t[1]) for t in zip(self.Parent.perImageTables,self.Parent.perObjectTables)],'\n'))
        self.outTables.SetLabel('Tables to write: \n'+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.Parent.outPerImage[:-10]+'_table_index')
        
    def OnFinish(self, evt):
        '''
        DO THE ACTUAL MERGE!
        '''
        
        # TODO: Allow abort from dialog        
        
        if evt.GetDirection() == True:
            nTables = len(self.Parent.perImageTables)
            prefix = self.Parent.outPerImage[:-10]
            dlg = wx.ProgressDialog("Creating Master Tables", "0%", 100, style=wx.PD_CAN_ABORT|wx.PD_SMOOTH)
            dlg.SetSize((400,150))
            dlg.Show()
            
            db = DBConnect.getInstance()
            
            # Create the DB if it doesn't exist already
            db.Execute('CREATE DATABASE IF NOT EXISTS '+self.Parent.outDB)
            db.Execute('USE '+self.Parent.outDB)
            
            # Create a table_index table which will be used to link the "TableNumber" fields to the original table names
            db.Execute('CREATE TABLE IF NOT EXISTS '+prefix+'_table_index (TableNumber INT, PerImageTable varchar(60), PerObjectTable varchar(60), PRIMARY KEY (TableNumber))')
            for i in xrange(nTables):
                db.Execute('INSERT INTO '+prefix+'_table_index (TableNumber, PerImageTable, PerObjectTable) VALUES('+str(i)+', "'+self.Parent.perImageTables[i]+'", "'+self.Parent.perObjectTables[i]+'")')
            
            # Create the per_image tables
            db.Execute('CREATE TABLE IF NOT EXISTS '+self.Parent.outPerImage+' LIKE '+self.Parent.inDB+'.'+self.Parent.perImageTables[0])
            db.Execute('ALTER TABLE '+self.Parent.outPerImage+' DROP PRIMARY KEY')
            db.Execute('ALTER TABLE '+self.Parent.outPerImage+' ADD COLUMN TableNumber INT')
            db.Execute('ALTER TABLE '+self.Parent.outPerImage+' ADD PRIMARY KEY (TableNumber, ImageNumber)')
            
            dlg.Update(0, 'Creating "'+self.Parent.outPerImage+'": 0%')
            for i in xrange(nTables):
                db.Execute('INSERT INTO '+self.Parent.outPerImage+' SELECT *,'+str(i)+' FROM '+self.Parent.inDB+'.'+self.Parent.perImageTables[i])
                percent = 100*i/nTables
                dlg.Update(percent, '"Creating "'+self.Parent.outPerImage+'": '+str(percent)+'%')
            db.Execute('ALTER TABLE '+self.Parent.outPerImage+' MODIFY COLUMN TableNumber INT FIRST')
            
            # Create the per_object tables
            db.Execute('CREATE TABLE IF NOT EXISTS '+self.Parent.outPerObject+' LIKE '+self.Parent.inDB+'.'+self.Parent.perObjectTables[0])
            db.Execute('ALTER TABLE '+self.Parent.outPerObject+' DROP PRIMARY KEY')
            db.Execute('ALTER TABLE '+self.Parent.outPerObject+' ADD COLUMN TableNumber INT')
            db.Execute('ALTER TABLE '+self.Parent.outPerObject+' ADD PRIMARY KEY (TableNumber, ImageNumber, ObjectNumber)')
            
            dlg.Update(0, 'Creating "'+self.Parent.outPerObject+'": 0%')
            for i in xrange(nTables):
                db.Execute('INSERT INTO '+self.Parent.outPerObject+' SELECT *,'+str(i)+' FROM '+self.Parent.inDB+'.'+self.Parent.perObjectTables[i])
                percent = 100*i/nTables
                dlg.Update(percent, 'Creating table "'+self.Parent.outPerObject+'": '+str(percent)+'%')
            db.Execute('ALTER TABLE '+self.Parent.outPerObject+' MODIFY COLUMN TableNumber INT FIRST')
            
            # Log the newly created table names in CPA_Merged_Tables.merged
            db.Execute('INSERT INTO CPA_Merged_Tables.merged (per_image, per_object, table_index) VALUES("'+self.Parent.outDB+'.'+self.Parent.outPerImage+'", "'+self.Parent.outDB+'.'+self.Parent.outPerObject+'", "'+self.Parent.outDB+'.'+prefix+'_table_index")' )
            
            dlg.Destroy()
            
            


app = wx.PySimpleApp()
wizard = wiz.Wizard(None, -1, "Create Master Table")
page1 = Page1(wizard)
page2 = Page2(wizard)
page3 = Page3(wizard)
page4 = Page4(wizard)
page5 = Page5(wizard)
wiz.WizardPageSimple_Chain(page1,page2)
wiz.WizardPageSimple_Chain(page2,page3)
wiz.WizardPageSimple_Chain(page3,page4)
wiz.WizardPageSimple_Chain(page4,page5)
wizard.FitToPage(page1)
wizard.RunWizard(page1)
wizard.Destroy()
app.MainLoop()
