import wx
import  wx.gizmos   as  gizmos


class MyFrame(wx.Frame):
    #""" We simply derive a new class of Frame. """
    def __init__(self, parent, id, title):
	wx.Frame.__init__(self, parent, id, 'Multi Panel', size=(700, 600))
	
	panel = wx.Panel(self, -1)

	##======NoteBook PANEL as a CLASS===========#
        self.nbPanel = NotebookPanel(panel, -1)

	###======TIME LINE PANEL as a CLASS===========#
        self.sldPanel = SliderPanel(panel, -1)
	
	vbox = wx.BoxSizer(wx.VERTICAL)
	vbox.Add(self.nbPanel, 1, wx.EXPAND)
	vbox.Add(self.sldPanel, 1, wx.EXPAND)
	panel.SetSizer(vbox)
	


##---------------------- NOTEBOOK PANEL ----------------------------##
## This panel is a notebook where each page of the notebook represents 
## a temporal event - Perturbation, Staining etc.. where within each 
## page the different Event variables are been listed
class NotebookPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        
        nb = wx.Notebook(self)

        # create the page windows as children of the notebook
	page1 = PerturbPage(nb)
        page2 = CellLoadPage(nb)
        #page2 = PerturbPage(nb)
        page3 = StainPage(nb)

        # add the pages to the notebook with the label to show on the tab
        nb.AddPage(page1, "Cell Loading")
        nb.AddPage(page2, "Perturbation")
        nb.AddPage(page3, "Staining")

        # finally, put the notebook in a sizer for the panel to manage
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
	
class CellLoadPage(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
	self.sw = wx.ScrolledWindow(self)
	
	fgs = wx.FlexGridSizer(rows=10, cols=2, hgap=5, vgap=5)
        
        # Cell Density
        cden = wx.Choice(self.sw, -1, choices= ['Density 10x6', 'Density 10x8'])
        cden.SetToolTipString('Cell Density')
        fgs.Add(wx.StaticText(self.sw, -1, 'Cell Density'), 0)
        fgs.Add(cden, 0, wx.EXPAND)
	
	self.sw.SetSizer(fgs)
        self.sw.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        # Layout with sizers
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.ALL, 5)

class PerturbPage(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
		
        sampleList = ['Drug X conc C1', 'Drug X conc C2', 'Drug X conc C3', 'Drug Y conc C1', 'Drug Y conc C2', 'Drug Set S1 contains 10,000 chemicals',
                      'Drug Set S2 contains 12,000 chemicals']

        #wx.StaticText(self, -1, "This example uses the wxCheckListBox control.", (45, 15))
	
	self.selectedDrugs = {}
        lb = wx.CheckListBox(self, -1, (80, 50), wx.DefaultSize, sampleList)
        self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, lb)
        lb.SetSelection(0)
        self.lb = lb
        
        pos = lb.GetPosition().x + lb.GetSize().width + 25
        self.addBut = wx.Button(self, -1, "Add Perturbation @  hr  min", (pos, 50))
        self.Bind(wx.EVT_BUTTON, self.OnAddPerturbation, self.addBut)


    def EvtCheckListBox(self, event):
        index = event.GetSelection()
        label = self.lb.GetString(index)
        
        if self.lb.IsChecked(index):
            self.selectedDrugs[label] = 'timepoint'
	else:
	    del self.selectedDrugs[label]

    def OnAddPerturbation(self, event):
	myCursor= wx.StockCursor(wx.CURSOR_SPRAYCAN)
	self.SetCursor(myCursor)
	
	#wx.CURSOR_SPRAYCAN
	#for k, v in self.selectedDrugs.iteritems():
	    #print k



class StainPage(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is a PageThree object", (60,60))



class SliderPanel(wx.Panel):
    def __init__(self, parent, id=-1, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        self.SetBackgroundColour("#9999FF")
           
        self.Bind(wx.EVT_PAINT, self.OnPaint) 
        self.timepoints = {}     
        
        # hook some mouse events
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.OnMove)
        
        self.text = wx.TextCtrl(self, -1, "24", (305, 10), (60, -1))
        h = self.text.GetSize().height
        w = self.text.GetSize().width + self.text.GetPosition().x + 2
        self.text.SetId(500)
        self.spin = wx.SpinButton(self, -1, (w, 10), (h*2/3, h), wx.SP_VERTICAL)
        self.spin.SetRange(24, 7200)
        self.spin.SetValue(24)
        self.spin.SetId(501)

        self.Bind(wx.EVT_SPIN, self.OnSpin, self.spin)
        
    def OnSpin(self, event):
        self.text.SetValue(str(event.GetPosition()))
    
    def OnMove(self, event):
        pos = event.GetPosition()
        
        #self.timelmt = self.spin.GetValue()*3600
        
        self.timelmt = self.spin.GetValue()*60
        slc_time = int((pos.x-50)*self.timelmt/(300-50))  #300 & 50 are the x2 and x1 coordinate of the timeline fixed
        hours = slc_time / 60
        slc_time -= 60*hours
        minutes = slc_time 
        self.SetToolTipString("%02d hrs %02d min " % (hours, minutes))
    
    def OnPaint(self, event):
        # establish the painting surface
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen('Black', 3))
        dc.DrawText('0', 40, 10)
        dc.DrawLine(50, 20, 300, 20)
            
    def OnRightDown(self, event):
        """left mouse button is pressed"""
       
        self.popupmenu = wx.Menu()
        for text in "CellLoading Perturbation Staining Spin Wash Harvest ImageAcquistion".split():
            item = self.popupmenu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.OnPopupItemSelected, item)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnShowPopup)
   
    def OnShowPopup(self, event):
        self.pt = event.GetPosition()
        self.pt = self.ScreenToClient(self.pt)
        self.PopupMenu(self.popupmenu, self.pt)
                
    def OnPopupItemSelected(self, event):
        item = self.popupmenu.FindItemById(event.GetId())
        text = item.GetText()
        #wx.MessageBox("You selected item '%s'" % text) 
        #Destroy all the buttons previously created EXCEPT the SpinHr control
        for child in self.GetChildren():
            if child.GetId()!= 500 and child.GetId()!= 501:
                child.Destroy() 
        #Fill the timepoint dictoniary previously created
        slc_time_in_min = int((self.pt.x-50)*self.timelmt/(300-50))
        self.timepoints[slc_time_in_min] = text
        
        #Draw the buttons accroding to timepoints
        for tp, evt in self.timepoints.iteritems():
	    dX = (tp*300/self.timelmt)
	    if evt == 'Perturbation':
		prtbut = wx.Button(self, -1,'',(dX,35), size = (15,15))
		prtbut.SetBackgroundColour('#FF3300')
	    elif evt == 'Staining':
		prtbut = wx.Button(self, -1,'',(dX,35), size = (15,15))
		prtbut.SetBackgroundColour('#66FF33')
	    elif evt == 'CellLoading':
		prtbut = wx.Button(self, -1,'',(dX,35), size = (15,15))
		prtbut.SetBackgroundColour('#FFCC33')
	    elif evt == 'ImageAcquistion':
		prtbut = wx.Button(self, -1,'',(dX,35), size = (15,15))
		prtbut.SetBackgroundColour('#FF66FF')

if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None, -1, '')
    frame.Show()
    app.MainLoop()

