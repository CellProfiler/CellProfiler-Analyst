import wx
import re
import experimentsettings as exp
from experimentsettings import ExperimentSettings
from wx.lib.masked import NumCtrl

meta = exp.ExperimentSettings.getInstance()
 

class StepBuilder(wx.ScrolledWindow):
    '''Scrolled window that displays a set of steps used for a given process
    '''
    def __init__(self, parent, protocol, **kwargs):
	
        wx.ScrolledWindow.__init__(self, parent, **kwargs)
	self.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	
	self.tag_stump = exp.get_tag_stump(protocol, 2)
	self.instance = exp.get_tag_attribute(protocol)
	

	# Attach a flexi sizer for the text controler and labels
	self.fgs = wx.FlexGridSizer(rows=15000, cols=6, hgap=5, vgap=5)	
	
	#Create the first step as empty
	if not meta.get_field(self.tag_stump+'|Step1|%s'%self.instance):
	    meta.set_field(self.tag_stump+'|Step1|%s'%self.instance,  ['','',''])     	
	
	self.showSteps()

	  
    def showSteps(self):
	
	steps = sorted(meta.get_attribute_list_by_instance(self.tag_stump+'|Step', self.instance), key = meta.stringSplitByNumbers)
	
	#-- Header --#		
	desp_header = wx.StaticText(self, -1, 'Description')
	dur_header = wx.StaticText(self, -1, 'Duration\n(min)')
	temp_header = wx.StaticText(self, -1, 'Temp\n(C)')
	
	font = wx.Font(6, wx.SWISS, wx.NORMAL, wx.BOLD)
	desp_header.SetFont(font)
	dur_header.SetFont(font)
	temp_header.SetFont(font)
	
	self.fgs.Add(wx.StaticText(self, -1, ''))
	self.fgs.Add(desp_header, 0, wx.ALIGN_CENTRE)
	self.fgs.Add(dur_header, 0, wx.ALIGN_CENTRE)
	self.fgs.Add(temp_header, 0, wx.ALIGN_CENTRE)
	self.fgs.Add(wx.StaticText(self, -1, ''))
	self.fgs.Add(wx.StaticText(self, -1, ''))

	for step in steps:
	    stepNo = int(step.split('Step')[1])
	    stepTAG = self.tag_stump+'|%s|%s' %(step, self.instance)
			
	    if not meta.get_field(stepTAG):
		meta.set_field(self.tag_stump+'|%s|%s' %(step, self.instance),  ['','','']) 
		    
	    step_info =  meta.get_field(stepTAG)	
	  
	    #-- Widgets ---#
	    self.Parent.settings_controls[stepTAG+'|0'] = wx.TextCtrl(self, size=(200,-1), value=step_info[0], style=wx.TE_PROCESS_ENTER)
	    self.Parent.settings_controls[stepTAG+'|1'] = wx.TextCtrl(self, size=(30,-1), value=step_info[1], style=wx.TE_PROCESS_ENTER)
	    # Discuss about numerical input only here but the problem is 0 degree Temp means somethin??
	    #self.Parent.settings_controls[stepTAG+'|1'] = wx.lib.masked.NumCtrl(self, size=(10,-1), style=wx.TE_PROCESS_ENTER)	
	    #if isinstance(step_info[1], int): #it had value
		#self.Parent.settings_controls[stepTAG+'|1'].SetValue(step_info[1])
	    self.Parent.settings_controls[stepTAG+'|2'] = wx.TextCtrl(self, size=(30,-1), value=step_info[2], style=wx.TE_PROCESS_ENTER)	    
	    self.del_btn = wx.Button(self, id=stepNo, label='Del -')
	    self.add_btn = wx.Button(self, id=stepNo, label='Add +')
	    #--- Tooltips --#
	    self.Parent.settings_controls[stepTAG+'|0'].SetToolTipString(step_info[0])    
	    #-- Binding ---#
	    self.Parent.settings_controls[stepTAG+'|0'].Bind(wx.EVT_TEXT, self.Parent.OnSavingData)
	    self.Parent.settings_controls[stepTAG+'|1'].Bind(wx.EVT_TEXT, self.Parent.OnSavingData)
	    self.Parent.settings_controls[stepTAG+'|2'].Bind(wx.EVT_TEXT, self.Parent.OnSavingData)
	    self.del_btn.step_to_delete = step
	    self.del_btn.Bind(wx.EVT_BUTTON, self.OnDelStep) 	    
	    self.add_btn.Bind(wx.EVT_BUTTON, self.OnAddStep) 	    
	    #--- Layout ---#
	    self.fgs.Add(wx.StaticText(self, -1, 'Step%s'%str(stepNo)), 0, wx.ALIGN_CENTRE) 
	    self.fgs.Add(self.Parent.settings_controls[stepTAG+'|0'], 1, wx.EXPAND|wx.ALL, 5) 
	    self.fgs.Add(self.Parent.settings_controls[stepTAG+'|1'], 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.Parent.settings_controls[stepTAG+'|2'], 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.add_btn, 0, wx.ALIGN_CENTRE)
	    self.fgs.Add(self.del_btn, 0, wx.ALIGN_CENTRE)
	    
	    if stepNo == 1:
		self.del_btn.Hide()
	    
	    self.SetSizer(self.fgs)
	    self.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	                   
		
	
    def OnAddStep(self, event):
	meta = ExperimentSettings.getInstance()
	
	#if meta.get_field(self.tag_stump+'|ProtocolName|'+self.instance) is None:
	    #dial = wx.MessageDialog(None, 'Please fill the Title/Name filed!!', 'Error', wx.OK | wx.ICON_ERROR)
	    #dial.ShowModal()  
	    #return
	# also check whether the description field has been filled by users
	steps = sorted(meta.get_attribute_list_by_instance(self.tag_stump+'|Step', self.instance), key = meta.stringSplitByNumbers)
	
	for step in steps:
	    step_info = meta.get_field(self.tag_stump+'|%s|%s' %(step, self.instance))
	    if not step_info[0]:
		dial = wx.MessageDialog(None, 'Please fill the description in %s !!' %step, 'Error', wx.OK | wx.ICON_ERROR)
		dial.ShowModal()  
		return
	    
	ctrl = event.GetEventObject()
	
	## Rearrange the steps numbers in the experimental settings
	temp_steps = {}
	
	for step in steps:
	    stepNo = int(step.split('Step')[1])
	    
	    if stepNo > ctrl.GetId() and temp_steps[stepNo] is not []:
		temp_steps[stepNo+1] = meta.get_field(self.tag_stump+'|%s|%s' %(step, self.instance))
		meta.remove_field(self.tag_stump+'|%s|%s' %(step, self.instance))
	    else:
		temp_steps[stepNo] = meta.get_field(self.tag_stump+'|%s|%s' %(step, self.instance))
		temp_steps[stepNo+1] = []
		meta.remove_field(self.tag_stump+'|%s|%s' %(step, self.instance))		
	
	for stepNo in sorted(temp_steps.iterkeys()):
	    meta.set_field(self.tag_stump+'|%s|%s' %('Step%s'%str(stepNo),  self.instance),  temp_steps[stepNo])	
	
	#clear the bottom panel
	self.fgs.Clear(deleteWindows=True)
	
	#redraw the panel
	self.showSteps()
	   

    def OnDelStep(self, event):
	
	self.del_btn = event.GetEventObject()
	
	#delete the step from the experimental settings 
	meta.remove_field(self.tag_stump+'|%s|%s' %(self.del_btn.step_to_delete,  self.instance))
	
	# Rearrange the steps numbers in the experimental settings
	steps = sorted(meta.get_attribute_list_by_instance(self.tag_stump+'|Step', self.instance), key = meta.stringSplitByNumbers)
	temp_steps = {}
	for stepNo in range(len(steps)):
	    temp_steps[stepNo+1] = meta.get_field(self.tag_stump+'|%s|%s' %(steps[stepNo],  self.instance))
	    meta.remove_field(self.tag_stump+'|%s|%s' %(steps[stepNo],  self.instance), notify_subscribers =False)
	
	for stepNo in sorted(temp_steps.iterkeys()):
	    meta.set_field(self.tag_stump+'|%s|%s' %('Step%s'%str(stepNo),  self.instance),  temp_steps[stepNo])
	
	#clear the bottom panel
	self.fgs.Clear(deleteWindows=True)
	#redraw the panel
	self.showSteps()
