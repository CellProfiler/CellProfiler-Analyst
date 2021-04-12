# Unused module? Mar 2021

# -*- Encoding: utf-8 -*-
import os
import re
import wx
import wx.adv as wiz
from wx.lib.dialogs import ScrolledMessageDialog
from .dbconnect import DBConnect
from .properties import Properties
import logging
logging.basicConfig()

db = DBConnect()
p = Properties()

def makePageTitle(wizPg, title):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(wizPg, -1, title)
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(wx.StaticLine(wizPg, -1), 0, wx.EXPAND|wx.ALL, 5)
        return sizer
     
    
class Page1(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Connect (step 1 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
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
        sizer1.Add(gridsizer, 0, wx.EXPAND, 10)
        sizer1.Add(self.btnTest, 0, wx.ALIGN_CENTER)
        
        self.sizer.Add(sizer1, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.btnTest.Bind(wx.EVT_BUTTON, self.OnTest)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

    def OnBrowse(self, evt):
        dlg = wx.FileDialog(self, "Select a properties file", defaultDir=os.getcwd(), style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            p = Properties()
            p.LoadFile(dlg.GetPath())
            self.lblDBHost.SetLabel(p.db_host)
            self.lblDBName.SetLabel(p.db_name)
            self.btnTest.SetLabel('Test')
            self.btnTest.Enable()
        
    def OnTest(self, evt):
        try:
            db.Disconnect()
            db.connect()
            self.btnTest.SetLabel('Connection OK')
            wx.FindWindowById(wx.ID_FORWARD).Enable()
        except:
            self.btnTest.SetLabel('Connection Failed')
        self.btnTest.Disable()
            
    def OnPageChanging(self,evt):
        if p.db_type.lower()!='mysql':
            wx.MessageBox('This wizard only knows how to merge MySQL databases.', 
                          'Error', wx.OK | wx.ICON_ERROR)
            self.btnTest.SetLabel('Error')
            evt.Veto()
        else:
            try:
                db.Disconnect()
                db.connect()
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
        title = wx.StaticText(self, -1, 'Choose Tables (step 2 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        self.directions = wx.StaticText(self, -1, "Select the tables you wish to include in the master.", style=wx.ALIGN_CENTRE)
        self.listTables = wx.ListBox(self, -1, choices=[], style=wx.LB_HSCROLL|wx.LB_EXTENDED)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.directions, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.listTables, 1, wx.EXPAND, 0)
        
        self.sizer.Add(sizer1, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.listTables.Bind(wx.EVT_LISTBOX, self.OnSelectItem)
        
    def OnPageLoaded(self, evt):
        self.listTables.Clear()
        perImTables = []
        perObTables = []
        for t in db.GetTableNames():
            # Get tables that are NOT masters (do not have a TableNumber index) 
            indices = [r[4] for r in db.execute('SHOW INDEX FROM %s'%(t))]
            if 'TableNumber' not in indices:
                if t.lower().endswith('per_image'):
                    perImTables += [t]
                elif t.lower().endswith('per_object') or t.lower().endswith('per_cells') or t.lower().endswith('per_nuclei') or t.lower().endswith('per_cytoplasm'):
                    perObTables += [t]
        for im in perImTables[::-1]:
            for ob in perObTables:
                if ob.lower().split('per')[0] == im.lower().split('per')[0]: # if prefixes match, add these two tables
                    prefix = ob.lower().split('per')[0].rstrip('_')
                    self.listTables.Insert(prefix+' ('+im+' / '+ob+')', 0, (im,ob))

    def OnSelectItem(self,evt):
        self.Parent.perImageTables = [self.listTables.GetClientData(i)[0] for i in self.listTables.GetSelections()]
        self.Parent.perObjectTables = [self.listTables.GetClientData(i)[1] for i in self.listTables.GetSelections()]
        self.directions.SetForegroundColour('#000001')
            
    def OnPageChanging(self,evt):
        if evt.GetDirection() == True:
            if self.listTables.GetSelections() == ():
                evt.Veto()
                self.directions.SetForegroundColour('#FF0000')
            
            if len(self.Parent.perImageTables) > 1:
                colnames = set(db.GetColumnNames(self.Parent.perImageTables[0]))
                for t in self.Parent.perImageTables:
                    colnames2 = set(db.GetColumnNames(t))
                    if colnames != colnames2:
                        errdlg = ScrolledMessageDialog(self, 'The column names in tables "%s" and "%s" do not match.\n\n'
                                     'Mismatched columns were:\n%s'%(self.Parent.perImageTables[0], 
                                         t, ', '.join(colnames.symmetric_difference(colnames2))), 
                                     'Table column names do not match.',
                                     style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
                        errdlg.ShowModal()
                        evt.Veto()

            if len(self.Parent.perObjectTables) > 1:
                colnames = set(db.GetColumnNames(self.Parent.perObjectTables[0]))
                for t in self.Parent.perObjectTables:
                    colnames2 = set(db.GetColumnNames(t))
                    if colnames != colnames2:
                        errdlg = ScrolledMessageDialog(self, 'The column names in tables "%s" and "%s" do not match.\n\n'
                                     'Mismatched columns were:\n%s'%(self.Parent.perObjectTables[0], 
                                         t, ', '.join(colnames.symmetric_difference(colnames2))), 
                                     'Table column names do not match.',
                                     style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
                        errdlg.ShowModal()
                        evt.Veto()

def find_master_tables():
    tables = db.GetTableNames()
    masters = {}
    for t in tables:
        res = db.execute('SHOW INDEX FROM %s'%(t))
        if t.lower().endswith('per_image'):
            if 'TableNumber' in [r[4] for r in res]:
                if t[:-10] not in masters:
                    masters[t[:-10]] = t
                else:
                    masters[t[:-10]] = t + ',' + masters[t[:-10]] 
        if t.lower().endswith('per_object'):
            if 'TableNumber' in [r[4] for r in res]:
                if t[:-11] not in masters:
                    masters[t[:-11]] = t
                else:
                    masters[t[:-11]] += ',' + t
    return list(masters.values())

        
class Page3(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Choose Master (step 3 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        self.txtPrefix = wx.TextCtrl(self, -1, 'CPA')
        self.example = wx.StaticText(self, -1, 'Output tables: "CPA_Per_Image", "CPA_Per_Object"')
        self.listTables = wx.ListBox(self, -1, choices=[], style=wx.LB_HSCROLL)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(wx.StaticText(self, -1, 'To create a new master, enter a prefix to use:', style=wx.ALIGN_CENTRE), 0, wx.ALL|wx.EXPAND, 5)
        sizer1.Add(self.txtPrefix, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.example, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        sizer1.Add(wx.StaticText(self, -1, '- OR -', style=wx.ALIGN_CENTER), 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(wx.StaticText(self, -1, 'Select an existing master to append to:', style=wx.ALIGN_CENTER), 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.listTables, 1, wx.EXPAND, 0)
        
        self.sizer.Add(sizer1, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.txtPrefix.Bind(wx.EVT_TEXT, self.OnText)
        self.listTables.Bind(wx.EVT_LEFT_DOWN, self.OnClickTableList)
        self.txtPrefix.Bind(wx.EVT_LEFT_DOWN, self.OnClickPrefix)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

    def OnClickTableList(self, evt):
        self.txtPrefix.SetValue('')
        evt.Skip()

    def OnClickPrefix(self, evt):
        self.listTables.DeselectAll()
        evt.Skip()

    def OnPageLoaded(self, evt):
        self.listTables.SetItems(find_master_tables())
        self.OnText(None)
        
    def OnText(self, evt):
        nameRules = re.compile('[a-zA-Z0-9]\w*$')
        if nameRules.match(self.txtPrefix.GetValue()):
            perImage  = self.txtPrefix.GetValue()+'_Per_Image'
            perObject = self.txtPrefix.GetValue()+'_Per_Object'
            if not hasattr(self, 'existingTables'):
                self.existingTables = db.GetTableNames()
            if (perImage not in self.existingTables and 
                perObject not in self.existingTables):
                self.Parent.outPerImage = perImage
                self.Parent.outPerObject = perObject
                self.Parent.masterExists = False
                self.example.SetLabel('Output tables: '+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.txtPrefix.GetValue()+'_table_index')
            else:
                self.example.SetLabel('Table already exists.')
        else:
            self.example.SetLabel('Invalid table prefix.')
            
    def OnPageChanging(self,evt):
        if evt.GetDirection() == True:
            if (self.example.GetLabel() == 'Invalid table prefix.' and 
                self.listTables.GetSelection() == wx.NOT_FOUND):
                evt.Veto()  
            elif self.listTables.GetSelection() != wx.NOT_FOUND:
                self.Parent.outPerImage, self.Parent.outPerObject = self.listTables.GetStringSelection().split(',')
                self.Parent.masterExists = True
            
                if len(self.Parent.perImageTables) > 0:
                    colnames = set(db.GetColumnNames(self.Parent.outPerImage)) - set(['TableNumber'])
                    for t in self.Parent.perImageTables:
                        colnames2 = set(db.GetColumnNames(t))
                        if colnames != colnames2:
                            errdlg = ScrolledMessageDialog(self, 'The column names in tables "%s" and "%s" do not match.\n\n'
                                        'Mismatched columns were:\n%s'%(self.Parent.outPerObject, 
                                            t, ', '.join(colnames.symmetric_difference(colnames2))), 
                                        'Table column names do not match.',
                                     style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
                            errdlg.ShowModal()
                            evt.Veto()
                            
                if len(self.Parent.perObjectTables) > 0:
                    colnames = set(db.GetColumnNames(self.Parent.outPerObject)) - set(['TableNumber'])
                    for t in self.Parent.perObjectTables:
                        colnames2 = set(db.GetColumnNames(t))
                        if colnames != colnames2:
                            errdlg = ScrolledMessageDialog(self, 'The column names in tables "%s" and "%s" do not match.\n\n'
                                        'Mismatched columns were:\n%s'%(self.Parent.outPerObject, 
                                            t, ', '.join(colnames.symmetric_difference(colnames2))), 
                                        'Table column names do not match.',
                                     style=wx.OK|wx.ICON_EXCLAMATION|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
                            errdlg.ShowModal()
                            evt.Veto()
            
class Page4(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Summary (step 4 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        label_1 = wx.StaticText(self, -1, 'Confirm that the following information is correct and click "Finish".', style=wx.ALIGN_CENTRE)
        self.report = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(label_1, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.report, 1, wx.ALL|wx.EXPAND, 10)
        
        self.sizer.Add(sizer1, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnFinish)

    def OnPageLoaded(self, evt):
        rep = 'SELECTED DATABASE: "'+self.Parent.outDB+'"\n\n'
        tables = [str(t[0])+', '+str(t[1]) for t in zip(self.Parent.perImageTables,self.Parent.perObjectTables)]
        tables.sort()
        rep += 'TABLES TO JOIN: \n'+'\n'.join(tables)+'\n\n'
        if self.Parent.masterExists:
            rep += 'APPENDING TO EXISTING MASTER: \n'+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.Parent.outPerImage[:-10]+'_table_index'
        else:
            rep += 'CREATING NEW MASTER: \n'+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.Parent.outPerImage[:-10]+'_table_index'
        self.report.SetValue(rep)
        
    def OnFinish(self, evt):
        ''' DO THE MERGE! '''
        if evt.GetDirection() == True:
            nTables = len(self.Parent.perImageTables)
            prefix = self.Parent.outPerImage[:-10]
            
            if not self.Parent.masterExists:
                ___ing = 'Creating'
            else:
                ___ing = 'Updating'
            dlg = wx.ProgressDialog(___ing+" Master Tables", "0%", 100, style=wx.PD_ELAPSED_TIME|wx.PD_SMOOTH)
            dlg.SetSize((400,150))
            dlg.Show()
            
            # Find which TableNumber to start at
            if self.Parent.masterExists:
                t0 = int(db.execute('SELECT MAX(TableNumber) FROM %s'%(self.Parent.outPerImage))[0][0]) + 1
            else:
                t0 = 0

            # Build a list of columns to select so their order in the db doesn't matter
            # Important: Step 3 guarantees that an existing master table has the
            #            same columns as the table(s) to merge (plus TableNumber)
            im_cols = ','.join(db.GetColumnNames(self.Parent.perImageTables[0]))
            ob_cols = ','.join(db.GetColumnNames(self.Parent.perObjectTables[0]))

            #
            # CREATE/APPEND TO THE MASTER PER_IMAGE TABLE
            #
            
            # TableNumber is moved to the last column
            if self.Parent.masterExists:
                lastcol = db.GetColumnNames(self.Parent.outPerImage)[-1]
                if lastcol != 'TableNumber':
                    db.execute('ALTER TABLE '+self.Parent.outPerImage+' MODIFY COLUMN TableNumber INT AFTER '+lastcol)
            else:
                db.execute('CREATE TABLE IF NOT EXISTS '+self.Parent.outPerImage+' LIKE '+self.Parent.inDB+'.'+self.Parent.perImageTables[0])
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' DROP PRIMARY KEY')
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' ADD COLUMN TableNumber INT')
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' ADD PRIMARY KEY (TableNumber, ImageNumber)')
            
            # Insert values from each table into the master
            dlg.Update(0, ___ing+' "'+self.Parent.outPerImage+'": 0%')
            for i in range(nTables):
                db.execute('INSERT INTO '+self.Parent.outPerImage+' SELECT '+im_cols+','+str(t0+i)+' FROM '+self.Parent.inDB+'.'+self.Parent.perImageTables[i])
                percent = 100*i/nTables
                dlg.Update(percent, ___ing+' "'+self.Parent.outPerImage+'": '+str(percent)+'%')
            db.execute('ALTER TABLE '+self.Parent.outPerImage+' MODIFY COLUMN TableNumber INT FIRST')
            
            #
            # CREATE/APPEND TO THE MASTER PER_OBJECT TABLE
            #
            
            # Tablenumber is moved to the last column
            if self.Parent.masterExists:
                lastcol = db.GetColumnNames(self.Parent.outPerObject)[-1]
                if lastcol != 'TableNumber':
                    db.execute('ALTER TABLE '+self.Parent.outPerObject+' MODIFY COLUMN TableNumber INT AFTER '+lastcol)
            else:
                db.execute('CREATE TABLE IF NOT EXISTS '+self.Parent.outPerObject+' LIKE '+self.Parent.inDB+'.'+self.Parent.perObjectTables[0])
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' DROP PRIMARY KEY')
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' ADD COLUMN TableNumber INT')
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' ADD PRIMARY KEY (TableNumber, ImageNumber, ObjectNumber)')
            
            # Insert values from each table into the master
            dlg.Update(0, ___ing+' "'+self.Parent.outPerObject+'": 0%')
            for i in range(nTables):
                db.execute('INSERT INTO '+self.Parent.outPerObject+' SELECT '+ob_cols+','+str(t0+i)+' FROM '+self.Parent.inDB+'.'+self.Parent.perObjectTables[i])
                percent = 100*i/nTables
                dlg.Update(percent, ___ing+' "'+self.Parent.outPerObject+'": '+str(percent)+'%')
            db.execute('ALTER TABLE '+self.Parent.outPerObject+' MODIFY COLUMN TableNumber INT FIRST')
            
            #
            # CREATE/UPDATE THE TABLE_INDEX table
            #   Used to link the TableNumber cols to the original table names
            #
            
            db.execute('CREATE TABLE IF NOT EXISTS '+prefix+'_table_index (TableNumber INT, PerImageTable varchar(60), PerObjectTable varchar(60), PRIMARY KEY (TableNumber))')
            for i in range(nTables):
                db.execute('INSERT INTO '+prefix+'_table_index (TableNumber, PerImageTable, PerObjectTable) VALUES('+str(t0+i)+', "'+self.Parent.perImageTables[i]+'", "'+self.Parent.perObjectTables[i]+'")')
            
            # Log the newly created table names in CPA_Merged_Tables.merged
            try:
                db.execute('INSERT INTO CPA_Merged_Tables.merged (per_image, per_object, table_index) VALUES("'+self.Parent.outDB+'.'+self.Parent.outPerImage+'", "'+self.Parent.outDB+'.'+self.Parent.outPerObject+'", "'+self.Parent.outDB+'.'+prefix+'_table_index")' )
            except:
                print('Logging merge to CPA_Merged_Tables.merged failed.')
            
            dlg.Destroy()
            
            dlg = wx.MessageDialog(self, 'Tables merged successfully!', 'Success!', wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            


app = wx.App()
wizard = wiz.Wizard(None, -1, "Create Master Table", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
page1 = Page1(wizard)
page2 = Page2(wizard)
page3 = Page3(wizard)
page4 = Page4(wizard)
wiz.WizardPageSimple.Chain(page1,page2)
wiz.WizardPageSimple.Chain(page2,page3)
wiz.WizardPageSimple.Chain(page3,page4)
wizard.FitToPage(page1)
wizard.RunWizard(page1)
wizard.Destroy()
app.MainLoop()
