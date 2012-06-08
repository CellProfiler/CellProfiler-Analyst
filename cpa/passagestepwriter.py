import wx
import re
import datetime
import experimentsettings as exp
from experimentsettings import ExperimentSettings
from wx.lib.masked import NumCtrl

meta = exp.ExperimentSettings.getInstance()
Default_Protocol ={
    'ADMIN' : ['Your name', '', '', '',''],
    'Step1' : ['Remove medium with a stripette','','', ''],
    'Step2' : ['Add trypsin in the following volumes - 1ml for the 60mm dish or T25 flask OR 2ml for 100mm dish or T75 flask','','', ''],
    'Step3' : ['Gently tip to ensure trypsin reaches all surfaces','','', ''],
    'Step4' : ['Immediately remove trypsin with either a pipette or syringe','','', ''],
    'Step5' : ['Add approx. 0.5ml of trypsin as before, close the flask (if used)','','', ''],
    'Step6' : ['Incubate','5','', 'Beware! A few cell lines need less than this'],
    'Step7' : ['Check under the microscope to see if the cells are detached, Return to incubator for a further few minutes if not detached','','', ''],
    'Step8' : ['Add medium (DMEM) to your dish or flask','','', ''],
    'Step9' : ['Flush off the cells and then pipette your trypsinised cells into the appropriate new container.','','', 'Excess cells should be placed in container and treated appropriately. Waste cells must not be sucked into traps.  The trypsin should not really be >10% of your final volume.  If it does you should spin down your cells (5mins at 1000rpm), draw off most of the supernatant and replace with fresh medium.'],
    }
 
class PassageStepBuilder(wx.Dialog):
    def __init__(self, parent, protocol, currpassageNo):
        wx.Dialog.__init__(self, parent, -1, size=(700,500), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, title = 'Passage %s' %str(currpassageNo))

	self.protocol = protocol
	self.currpassageNo = currpassageNo
	
	self.top_panel = wx.Panel(self)
	self.bot_panel = wx.ScrolledWindow(self)	
	
	self.settings_controls = {}
	self.curr_protocol = {}
	self.admin_info = {}        
        
	self.tag_stump = exp.get_tag_stump(self.protocol, 2)
	self.instance = exp.get_tag_attribute(self.protocol)
	
	if meta.get_field(self.tag_stump+'|Passage%s|%s' %(str(self.currpassageNo-1), self.instance)) is None:
	    self.curr_protocol = Default_Protocol
	else:
	    #self.curr_protocol = meta.get_field(self.tag_stump+'|Passage%s|%s' %(str(self.currpassageNo-1), self.instance))
	    d =  meta.get_field(self.tag_stump+'|Passage%s|%s' %(str(self.currpassageNo-1), self.instance))
	    for k, v in d:
		self.curr_protocol[k] = v
	
	today = datetime.date.today()
	self.myDate = '%02d/%02d/%4d'%(today.day, today.month, today.year)
	
	self.curr_protocol['ADMIN'][1] = self.myDate   # set todays date as current
	
	self.settings_controls['Admin|0'] = wx.TextCtrl(self.top_panel, size=(70,-1), value=self.curr_protocol['ADMIN'][0])
	self.settings_controls['Admin|1'] = wx.DatePickerCtrl(self.top_panel, style = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)	
	self.settings_controls['Admin|2'] = wx.TextCtrl(self.top_panel, size=(20,-1), value=self.curr_protocol['ADMIN'][2])
	#self.settings_controls['Admin|3'] = wx.TextCtrl(self.top_panel, size=(20,-1), value=self.curr_protocol['ADMIN'][3])
	self.settings_controls['Admin|3'] = wx.lib.masked.NumCtrl(self.top_panel, size=(20,-1), style=wx.TE_PROCESS_ENTER)
	if isinstance(self.curr_protocol['ADMIN'][3], int): #it had value
	    self.settings_controls['Admin|3'].SetValue(self.curr_protocol['ADMIN'][3])
	unit_choices =['nM2', 'uM2', 'mM2','Other']
	self.settings_controls['Admin|4'] = wx.ListBox(self.top_panel, -1, wx.DefaultPosition, (50,20), unit_choices, wx.LB_SINGLE)
	if self.curr_protocol['ADMIN'][4] is not None:
	    self.settings_controls['Admin|4'].Append(self.curr_protocol['ADMIN'][4])
	    self.settings_controls['Admin|4'].SetStringSelection(self.curr_protocol['ADMIN'][4])
	
	self.settings_controls['Admin|0'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls['Admin|1'].Bind(wx.EVT_DATE_CHANGED, self.OnSavingData)
	self.settings_controls['Admin|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls['Admin|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	self.settings_controls['Admin|4'].Bind(wx.EVT_LISTBOX, self.OnSavingData)  
	
        self.selection_btn = wx.Button(self, wx.ID_OK, 'Record Passage')
        self.close_btn = wx.Button(self, wx.ID_CANCEL)
        
	# Sizers and layout
	top_fgs = wx.FlexGridSizer(cols=10, vgap=5)
	
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Operator Name'),0, wx.RIGHT, 5)
	top_fgs.Add(self.settings_controls['Admin|0'] , 0, wx.EXPAND)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Date'),0, wx.RIGHT|wx.LEFT, 5)
	top_fgs.Add(self.settings_controls['Admin|1'], 0, wx.EXPAND)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Split 1:'),0, wx.LEFT, 5)
	top_fgs.Add(self.settings_controls['Admin|2'], 0, wx.EXPAND)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, 'Cell Count'),0, wx.RIGHT|wx.LEFT, 5)
	top_fgs.Add(self.settings_controls['Admin|3'], 0, wx.EXPAND)
	top_fgs.Add(wx.StaticText(self.top_panel, -1, ' cells/'),0)
	top_fgs.Add(self.settings_controls['Admin|4'], 0, wx.EXPAND)
		
	self.fgs = wx.FlexGridSizer(cols=7, hgap=5, vgap=5)	
	self.showSteps()
	
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	btnSizer.Add(self.selection_btn  , 0, wx.ALL, 5)
	btnSizer.Add(self.close_btn , 0, wx.ALL, 5)	

        self.top_panel.SetSizer(top_fgs)
	self.bot_panel.SetSizer(self.fgs)
        self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Sizer.Add(btnSizer)
        self.Show()         
          
    def showSteps(self):
	# get the sorted steps in passaging
	steps = sorted([step for step in self.curr_protocol.keys()
		 if not step.startswith('ADMIN')] , key = meta.stringSplitByNumbers)
		
	#-- Header --#		
	desp_header = wx.StaticText(self.bot_panel, -1, 'Description')
	dur_header = wx.StaticText(self.bot_panel, -1, 'Duration\n(min)')
	temp_header = wx.StaticText(self.bot_panel, -1, 'Temp\n(C)')
	tips_header = wx.StaticText(self.bot_panel, -1, 'Tips')
	
	font = wx.Font(6, wx.SWISS, wx.NORMAL, wx.BOLD)
	desp_header.SetFont(font)
	dur_header.SetFont(font)
	temp_header.SetFont(font)
	tips_header.SetFont(font)
	
	self.fgs.Add(wx.StaticText(self.bot_panel, -1, ''))
	self.fgs.Add(desp_header, 0, wx.ALIGN_CENTRE)
	self.fgs.Add(dur_header, 0, wx.ALIGN_CENTRE)
	self.fgs.Add(temp_header, 0, wx.ALIGN_CENTRE)
	self.fgs.Add(tips_header, 0, wx.ALIGN_CENTER)
	self.fgs.Add(wx.StaticText(self.bot_panel, -1, ''))
	self.fgs.Add(wx.StaticText(self.bot_panel, -1, ''))

	for step in steps:    
	    stepNo = int(step.split('Step')[1])
	    step_info =  self.curr_protocol[step]
	   
	    if not step_info:  # if this is newly added empty step
		step_info = ['','','','']

	    #-- Widgets ---#
	    self.settings_controls[step+'|0'] = wx.TextCtrl(self.bot_panel, size=(200,-1), value=step_info[0], style=wx.TE_PROCESS_ENTER)
	    self.settings_controls[step+'|1'] = wx.TextCtrl(self.bot_panel, size=(30,-1), value=step_info[1], style=wx.TE_PROCESS_ENTER)
	    self.settings_controls[step+'|2'] = wx.TextCtrl(self.bot_panel, size=(30,-1), value=step_info[2], style=wx.TE_PROCESS_ENTER)	
	    self.settings_controls[step+'|3'] = wx.TextCtrl(self.bot_panel, size=(100,-1), value=step_info[3], style=wx.TE_PROCESS_ENTER)
	    if step_info[3]:
		self.settings_controls[step+'|3'].SetForegroundColour(wx.RED) 
	    self.del_btn = wx.Button(self.bot_panel, id=stepNo, label='Del -') 
	    self.add_btn = wx.Button(self.bot_panel, id=stepNo, label='Add +')
	    #--- Tooltips --#
	    self.settings_controls[step+'|0'].SetToolTipString(step_info[0])
	    self.settings_controls[step+'|3'].SetToolTipString(step_info[3])
	    #-- Binding ---#
	    self.settings_controls[step+'|0'].Bind(wx.EVT_TEXT, self.OnSavingData)
	    self.settings_controls[step+'|1'].Bind(wx.EVT_TEXT, self.OnSavingData)
	    self.settings_controls[step+'|2'].Bind(wx.EVT_TEXT, self.OnSavingData)
	    self.settings_controls[step+'|3'].Bind(wx.EVT_TEXT, self.OnSavingData)
	    self.del_btn.step_to_delete = step
	    self.del_btn.Bind(wx.EVT_BUTTON, self.OnDelStep) 	    
	    self.add_btn.Bind(wx.EVT_BUTTON, self.OnAddStep) 	    
	    #--- Layout ---#
	    self.fgs.Add(wx.StaticText(self.bot_panel, -1, 'Step%s'%str(stepNo)), 0, wx.ALIGN_CENTRE) 
	    self.fgs.Add(self.settings_controls[step+'|0'], 1, wx.EXPAND|wx.ALL, 5) 
	    self.fgs.Add(self.settings_controls[step+'|1'], 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.settings_controls[step+'|2'], 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.settings_controls[step+'|3'], 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.add_btn, 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.del_btn, 0, wx.ALIGN_CENTRE)
	    
	    if stepNo == 1:
		self.del_btn.Hide()
	    
	    # Sizers update
	    self.bot_panel.SetSizer(self.fgs)
	    self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	    
	    self.Sizer = wx.BoxSizer(wx.VERTICAL)
	    self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	    self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
	    self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)	                   
		
	
    def OnAddStep(self, event):
	meta = ExperimentSettings.getInstance()
	
	steps = sorted([step for step in self.curr_protocol.keys()
	 if not step.startswith('ADMIN')] , key = meta.stringSplitByNumbers)
	
	for step in steps:
	    if not self.curr_protocol[step]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return

	ctrl = event.GetEventObject()
	
	 #Rearrange the steps numbers in the experimental settings
	temp_steps = {}
	
	for step in steps:
	    stepNo = int(step.split('Step')[1])
	    step_info =  self.curr_protocol[step]	
	    	    
	    if stepNo > ctrl.GetId() and temp_steps[stepNo] is not []:
		temp_steps[stepNo+1] =self.curr_protocol[step]
		del self.curr_protocol[step]
	    else:
		temp_steps[stepNo] = self.curr_protocol[step]
		temp_steps[stepNo+1] = []
		del self.curr_protocol[step]
	
	for stepNo in sorted(temp_steps.iterkeys()):
	    self.curr_protocol['Step%s'%str(stepNo)] = temp_steps[stepNo]	
	
	self.fgs.Clear(deleteWindows=True)
	
	self.showSteps()
	   

    def OnDelStep(self, event):
	
	self.del_btn = event.GetEventObject()
	
	#delete the step from the experimental settings 
	del self.curr_protocol[self.del_btn.step_to_delete]
	
	# Rearrange the steps numbers in the experimental settings
	steps = sorted([step for step in self.curr_protocol.keys()
		 if not step.startswith('ADMIN')] , key = meta.stringSplitByNumbers)
	
	temp_steps = {}
	for stepNo in range(len(steps)):
	    temp_steps[stepNo+1] = self.curr_protocol[steps[stepNo]]
	    del self.curr_protocol[steps[stepNo]]
	    
	for stepNo in sorted(temp_steps.iterkeys()):
	    self.curr_protocol['Step%s'%str(stepNo)] = temp_steps[stepNo]
	
	#clear the bottom panel
	self.fgs.Clear(deleteWindows=True)
	#redraw the panel
	self.showSteps()
    


    def OnSavingData(self, event):
	#TO DO: make this method coherent with other instances of this method
	ctrl = event.GetEventObject()
	tag = [t for t, c in self.settings_controls.items() if c==ctrl][0]
	
	if tag.startswith('Admin'): # if this is an Admin 
	    myDate = ''
	    if isinstance(ctrl, wx.DatePickerCtrl):
		date = ctrl.GetValue()
		self.myDate = '%02d/%02d/%4d'%(date.Day, date.Month+1, date.Year)
	    if isinstance(ctrl, wx.ListBox) and ctrl.GetStringSelection() == 'Other':
		other = wx.GetTextFromUser('Insert Other', 'Other')
		ctrl.Append(other)
		ctrl.SetStringSelection(other)	    
			
	    self.curr_protocol['ADMIN'] = [self.settings_controls['Admin|0'].GetValue(), 
	                                   self.myDate, 
	                                   self.settings_controls['Admin|2'].GetValue(),
	                                   self.settings_controls['Admin|3'].GetValue(),
	                                   self.settings_controls['Admin|4'].GetStringSelection()]
	    
	else:   # if this is a step 
	    step = tag.split('|')[0]
	    # get the sibling controls like description, duration, temp controls for this step
	    info = []
	    for tg in [t for t, c in self.settings_controls.items()]:
		if exp.get_tag_stump(tag, 1) == exp.get_tag_stump(tg, 1) and tg.startswith('Step'):
		    c_num = int(tg.split('|')[1])
		    if isinstance(self.settings_controls[tg], wx.Choice):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())
		    elif isinstance(self.settings_controls[tg], wx.ListBox):
			info.insert(c_num, self.settings_controls[tg].GetStringSelection())		    
		    else:
			user_input = self.settings_controls[tg].GetValue()
			user_input.rstrip('\n')
			user_input.rstrip('\t')
			info.insert(c_num, user_input)
		    
	    self.curr_protocol[step] = info
	