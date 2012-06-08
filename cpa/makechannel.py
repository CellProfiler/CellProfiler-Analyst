#!/usr/bin/python

import wx
import wx.lib.agw.gradientbutton as GB
import icons
from experimentsettings import *
from wx.lib.masked import NumCtrl

class ChannelBuilder(wx.Dialog):  
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(1000,350), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
     
	self.top_panel = wx.Panel(self)
        self.bot_panel = wx.ScrolledWindow(self)
	
	meta = ExperimentSettings.getInstance()

        self.componentList = {}
        self.componentCount = 0
              
        # Header row
        choices =['FSC', 'SSC', 'FL-1', 'FL-2','FL-3','FL-4','FL-5','FL-6','FL-7','FL-8', 'Other']
	self.select_chName= wx.ListBox(self.top_panel, -1, wx.DefaultPosition, (50,30), choices, wx.LB_SINGLE)
	self.select_chName.Bind(wx.EVT_LISTBOX, self.OnChSelection)
        self.select_component = wx.Choice(self.top_panel, -1, choices=['Dichroic Mirror', 'Filter', 'Beam Splitter',  'Dye', 'Detector'])
	self.select_component.Disable()
        self.select_component.Bind(wx.EVT_CHOICE, self.OnAddComponent)	
	
        self.select_btn = wx.Button(self, wx.ID_OK, 'Set Channel')
	self.select_btn.Disable()
	self.close_btn = wx.Button(self, wx.ID_CANCEL)	
	
	# -- Sizers Lay out ---#
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
	self.top_sizer.Add(wx.StaticText(self.top_panel, -1, 'Channel Name'), 0, wx.ALL, 5)
	self.top_sizer.Add(self.select_chName, 0, wx.HORIZONTAL, 5)
	self.top_sizer.Add(wx.StaticText(self.top_panel, -1, 'Component'), 0, wx.ALL, 5)
	self.top_sizer.Add(self.select_component, 0, wx.HORIZONTAL, 5)
	self.top_sizer.Add((500, -1))
	#self.top_sizer.Add(self.select_btn, 1, wx.ALIGN_RIGHT|wx.RIGHT, 5)
	
	self.fgs = wx.FlexGridSizer(cols=30, hgap=10)	

        self.top_panel.SetSizer(self.top_sizer)
	self.bot_panel.SetSizer(self.fgs)
        self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	
	btnSizer = wx.BoxSizer(wx.HORIZONTAL)
	btnSizer.Add(self.select_btn , 0, wx.ALL, 5)
	btnSizer.Add(self.close_btn , 0, wx.ALL, 5)		

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	self.Sizer.Add(btnSizer)
        self.Show()         
    
    def OnChSelection(self, event):
	if self.select_chName.GetStringSelection() == 'Other':
	    other = wx.GetTextFromUser('Insert Other', 'Other')
	    self.select_chName.Append(other)
	    self.select_chName.SetStringSelection(other)		
	self.select_chName.Disable()
	
	self.componentCount +=1	

	staticbox = wx.StaticBox(self.bot_panel, -1, "Excitation Laser")
	staticbox.SetMaxSize((200,300))
	
	self.laser = wx.TextCtrl(self.bot_panel, value='', style= wx.TE_PROCESS_ENTER)
	self.laser.Bind(wx.EVT_TEXT_ENTER, self.setLaserColor)  # increament the component count when users entered the value of Laser beam
	#self.laser = wx.lib.masked.NumCtrl(self.bot_panel, size=(20,-1), style=wx.TE_PROCESS_ENTER)
	#self.laser.Bind(wx.EVT_TEXT, self.setLaserColor)
	laserSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	laserSizer.Add(self.laser, 0) 	    
	self.fgs.Add(laserSizer,  0)	
	
	#Add to sizers-------
	self.bot_panel.SetSizer(self.fgs)
	self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)
	

	
    def OnAddComponent(self, event):
	meta = ExperimentSettings.getInstance()	    
	self.componentCount +=1	
	if self.componentCount != len(self.componentList)+1:
	    dial = wx.MessageDialog(None, 'Please set previous component', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal() 
	    self.componentCount -=1
	    return
		  
	startNM, endNM = meta.getNM(self.componentList[self.componentCount-1][1])
	
        if self.select_component.GetStringSelection() == 'Dichroic Mirror':	    
	    staticbox = wx.StaticBox(self.bot_panel, -1, "Dichroic Mirror")
            self.dmtTsld = wx.Slider(self.bot_panel, -1, startNM, startNM, endNM, wx.DefaultPosition, (100, -1), wx.SL_LABELS)
            self.dmtBsld = wx.Slider(self.bot_panel, -1, endNM, startNM, endNM, wx.DefaultPosition, (100, -1), style = wx.SL_LABELS|wx.SL_TOP)
	    self.mirrspectrum = MirrorSpectrum(self.bot_panel)
            self.enabled = True
            self.mirrStatus = "Reflected"
            self.passrefBut = wx.Button(self.bot_panel, -1, self.mirrStatus)
            self.Bind(wx.EVT_BUTTON, self.OnToggleMirror, self.passrefBut)
            self.dmtTsld.Bind(wx.EVT_SCROLL, self.OnScrollMirror)
            self.dmtBsld.Bind(wx.EVT_SCROLL, self.OnScrollMirror)
            
            #Sizers
	    mirrorSizer = wx.BoxSizer(wx.VERTICAL)
            mirrorSizer.Add(self.dmtTsld,0)
	    mirrorSizer.Add(self.mirrspectrum, 0)
            mirrorSizer.Add(self.dmtBsld,0) 
            dichrosetSizer = wx.StaticBoxSizer(staticbox, wx.HORIZONTAL)
            dichrosetSizer.Add(mirrorSizer, 0)
            dichrosetSizer.Add(self.passrefBut, 0, wx.EXPAND)
            self.fgs.Add(dichrosetSizer, 0)   
	    
	if self.select_component.GetStringSelection() == 'Beam Splitter':     
	    staticbox = wx.StaticBox(self.bot_panel, -1, "Beam Splitter")
	    self.sltTsld = wx.Slider(self.bot_panel, -1, 0, 0, 100, wx.DefaultPosition, (100, -1))
	    self.splitSpectrum = SplitterSpectrum(self.bot_panel)
	    self.sltTsld.Bind(wx.EVT_SCROLL, self.OnScrollSplitter)
	    
	    #Sizers
	    splitterSizer = wx.BoxSizer(wx.VERTICAL)
	    splitterSizer.Add(self.sltTsld,0)
	    splitterSizer.Add(self.splitSpectrum, 0)
	    mainSizer = wx.StaticBoxSizer(staticbox, wx.HORIZONTAL)
	    mainSizer.Add(splitterSizer, 0)
	    self.fgs.Add(mainSizer, 0)   	
        
        if self.select_component.GetStringSelection() == 'Filter':
	    staticbox = wx.StaticBox(self.bot_panel, -1, "Filter")
            self.fltTsld = wx.Slider(self.bot_panel, -1, startNM, startNM, endNM, wx.DefaultPosition, (100, -1), wx.SL_LABELS)
            self.fltBsld = wx.Slider(self.bot_panel, -1, endNM, startNM, endNM, wx.DefaultPosition, (100, -1), style = wx.SL_LABELS|wx.SL_TOP)
            self.fltrspectrum = FilterSpectrum(self.bot_panel)
            self.fltTsld.Bind(wx.EVT_SCROLL, self.OnScrollFilter)
            self.fltBsld.Bind(wx.EVT_SCROLL, self.OnScrollFilter)
	    
            #Sizers
            fltrSizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
            fltrSizer.Add(self.fltTsld,0)
            fltrSizer.Add(self.fltrspectrum, 0)
            fltrSizer.Add(self.fltBsld,0)             
            self.fgs.Add(fltrSizer, 0)           
            
	if self.select_component.GetStringSelection() == 'Dye':
	    staticbox = wx.StaticBox(self.bot_panel, -1, "Dye List")
	    dyeList = meta.setDyeList(startNM, endNM)
	    dyeList.append('Add Dye by double click')  
	    self.dyeListBox = wx.ListBox(self.bot_panel, -1, wx.DefaultPosition, (150, 100), dyeList, wx.LB_SINGLE)
	    self.Bind(wx.EVT_LISTBOX, self.OnDyeSelect, self.dyeListBox)
	    self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnMyDyeSelect, self.dyeListBox)
            
            #Sizers
	    dye_sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
	    dye_sizer.Add(self.dyeListBox, 0)               
	    self.fgs.Add(dye_sizer, 0) 	    
	    
        if self.select_component.GetStringSelection() == 'Detector':
            staticbox = wx.StaticBox(self.bot_panel, -1, "Detector Voltage")
	    self.detector = wx.SpinCtrl(self.bot_panel, -1, "", (30, 50))
	    self.detector.SetRange(1,1000)
	    self.detector.SetValue(500)
	    self.Bind(wx.EVT_SPINCTRL, self.OnDetectorVoltSet, self.detector)	    
            
            #Sizers
            detector_sizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
            detector_sizer.Add(self.detector, 0)
            self.fgs.Add(detector_sizer, 0)
        
        
        #--- Sizers -------
        self.bot_panel.SetSizer(self.fgs)
        self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)

    def setLaserColor(self, event):
	meta = ExperimentSettings.getInstance()	
        ctrl = event.GetEventObject()
	# check the validity of the input
	if ctrl.GetValue().isdigit() is False:
	    dial = wx.MessageDialog(None, 'Laser excitation should be integer value', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal() 
	    return	 
	    
        if meta.belongsTo(int(ctrl.GetValue()), 380, 800) is False:
	    dial = wx.MessageDialog(None, 'Laser excitation should be within 380-800 nm range', 'Error', wx.OK | wx.ICON_ERROR)
	    dial.ShowModal() 
	    return
	# Set the Laser colour    
	ctrl.SetBackgroundColour(meta.nmToRGB(int(ctrl.GetValue())))
	emSpect =[]
	
	for dye in FLUOR_SPECTRUM:
	    extLow, extHgh = meta.getNM(FLUOR_SPECTRUM[dye][0])	    
	    emtLow, emtHgh = meta.getNM(FLUOR_SPECTRUM[dye][1])
	    
	    # according to the inserted excitation laser select the emission range
	    if meta.belongsTo(int(ctrl.GetValue()), extLow, extHgh):
		emSpect.append(emtLow)
		emSpect.append(emtHgh)
		emSpect.append(int(ctrl.GetValue())-15) # Also add the scattered light from the laser
		emSpect.append(int(ctrl.GetValue())+15)		    
	    # adjust the emission range with previous laser emission range
	    for component in self.componentList:
		if  self.componentList[component][0].startswith('LSR'):
		    emSpect.append(int(self.componentList[component][0].split('LSR')[1])-15) # Also add the scattered light from the laser
		    emSpect.append(int(self.componentList[component][0].split('LSR')[1])+15)
		    
		    if meta.belongsTo(int(self.componentList[component][0].split('LSR')[1]),extLow, extHgh):                
			emSpect.append(emtLow)
			emSpect.append(emtHgh)
	    
	self.componentList[self.componentCount] = ['LSR%s'%ctrl.GetValue(), str(min(emSpect))+'-'+str(max(emSpect))]	   
	    
	#Enable users to select the component from the list
	self.select_component.Enable()
	self.select_btn.Enable()
	
	# draw the cell picture
	bmp = icons.cpa_32.Scale(32.0, 32.0, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()	
	cell_image = wx.BitmapButton(self.bot_panel, -1, bmp, (32, 32), style = wx.NO_BORDER)
	
	# sizers
	self.fgs.Add(cell_image, 0)
	self.bot_panel.SetSizer(self.fgs)
	self.bot_panel.SetScrollbars(20, 20, self.Size[0]+20, self.Size[1]+20, 0, 0)
	
	self.Sizer = wx.BoxSizer(wx.VERTICAL)
	self.Sizer.Add(self.top_panel, 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)
	self.Sizer.Add(self.bot_panel, 1, wx.EXPAND|wx.ALL, 10)	
	
    def OnScrollMirror(self, event):    
        # check: there is alwasy 11 nm range for the slider
        if self.dmtTsld.GetValue()+5 >= self.dmtBsld.GetValue():
            dial = wx.MessageDialog(None, 'Upper wavelength must be higher than lower wavelength!!', 'Error', wx.OK | wx.ICON_ERROR)
            self.dmtTsld.SetValue(self.dmtBsld.GetValue()-6)
            dial.ShowModal()  
            return    	
 
        if self.dmtTsld.GetValue() > self.dmtTsld.GetMin() and self.mirrStatus == 'Reflected': 
	    self.dmtBsld.Disable()
            self.componentList[self.componentCount]= ['DMR%sLP'%self.dmtTsld.GetValue(), str(self.dmtTsld.GetMin())+'-'+str(self.dmtTsld.GetValue())]
	if self.dmtTsld.GetValue() > self.dmtTsld.GetMin() and self.mirrStatus == 'Transmitted': 
	    self.dmtBsld.Disable()
	    self.componentList[self.componentCount]= ['DMR%sLP'%self.dmtTsld.GetValue(), str(self.dmtTsld.GetValue())+'-'+str(self.dmtBsld.GetMax())]	
        if self.dmtBsld.GetValue() < self.dmtBsld.GetMax()and self.mirrStatus == 'Reflected':
	    self.dmtTsld.Disable()
	    self.componentList[self.componentCount]= ['DMR%sSP'%self.dmtBsld.GetValue(), str(self.dmtBsld.GetValue())+'-'+str(self.dmtBsld.GetMax())]
	if self.dmtBsld.GetValue() < self.dmtBsld.GetMax()and self.mirrStatus == 'Transmitted':
	    self.dmtTsld.Disable()
	    self.componentList[self.componentCount]= ['DMR%sSP'%self.dmtBsld.GetValue(), str(self.dmtTsld.GetMin())+'-'+str(self.dmtBsld.GetValue())]
            
        self.mirrspectrum.Refresh()
	
    def OnScrollSplitter(self, event):
	
	meta = ExperimentSettings.getInstance()	
	
	self.startNM, self.endNM = meta.getNM(self.componentList[self.componentCount-1][1])
	
	self.componentList[self.componentCount]= ['SLT%s/%s'%(str(100-self.sltTsld.GetValue()), str(self.sltTsld.GetValue())), str(self.startNM)+'-'+str(self.endNM)] 	

	self.splitSpectrum.Refresh()
	 
    def OnScrollFilter(self, event):    
        # check: there is alwasy 11 nm range for the slider
        if self.fltTsld.GetValue()+8 >= self.fltBsld.GetValue():
            dial = wx.MessageDialog(None, 'Upper wavelength must be higher than lower wavelength!!', 'Error', wx.OK | wx.ICON_ERROR)
            self.fltTsld.SetValue(self.fltBsld.GetValue()-9)
            dial.ShowModal()  
            return              
    
	if self.fltTsld.GetValue() > self.fltTsld.GetMin() and self.fltBsld.GetValue() == self.fltBsld.GetMax():
	    self.componentList[self.componentCount] = ['FLT%sLP'%self.fltTsld.GetValue(), str(self.fltTsld.GetValue())+'-'+str(self.fltBsld.GetMax())]
	elif self.fltBsld.GetValue() < self.fltBsld.GetMax() and self.fltTsld.GetValue() == self.fltTsld.GetMin():
	    self.componentList[self.componentCount] = ['FLT%sSP'%self.fltBsld.GetValue(), str(self.fltTsld.GetMin())+'-'+str(self.fltBsld.GetValue())]
	else:  
	    midValue = int((self.fltTsld.GetValue()+self.fltBsld.GetValue())/2)
	    ranges = self.fltBsld.GetValue()-self.fltTsld.GetValue()
	    self.componentList[self.componentCount]= ['FLT'+str(midValue)+'/'+str(ranges)+'BP', str(self.fltTsld.GetValue())+'-'+str(self.fltBsld.GetValue())]
	self.fltrspectrum.Refresh()
    
    def OnToggleMirror(self, event):
        self.mirrStatus =  (self.enabled and "Transmitted" or "Reflected")
        self.passrefBut.SetLabel(self.mirrStatus)
        self.enabled = not self.enabled
        
        if self.dmtTsld.GetValue() > self.dmtTsld.GetMin() and self.mirrStatus == 'Reflected': 
            self.componentList[self.componentCount]= ['DMR%sLP'%self.dmtTsld.GetValue(), str(self.dmtTsld.GetMin())+'-'+str(self.dmtTsld.GetValue())]
	if self.dmtTsld.GetValue() > self.dmtTsld.GetMin() and self.mirrStatus == 'Transmitted': 
	    self.componentList[self.componentCount]= ['DMR%sLP'%self.dmtTsld.GetValue(), str(self.dmtTsld.GetValue())+'-'+str(self.dmtBsld.GetMax())]	
        if self.dmtBsld.GetValue() < self.dmtBsld.GetMax()and self.mirrStatus == 'Reflected':
	    self.componentList[self.componentCount]= ['DMR%sSP'%self.dmtBsld.GetValue(), str(self.dmtBsld.GetValue())+'-'+str(self.dmtBsld.GetMax())]
	if self.dmtBsld.GetValue() < self.dmtBsld.GetMax()and self.mirrStatus == 'Transmitted':
	    self.componentList[self.componentCount]= ['DMR%sSP'%self.dmtBsld.GetValue(), str(self.dmtTsld.GetMin())+'-'+str(self.dmtBsld.GetValue())]	
    
    #def OnToggleSplitter(self, event):
	#self.splitterStatus =  (self.enabled and "Right\nSide" or "Left\nSide")
	#self.splitfBut.SetLabel(self.splitterStatus)
	#self.enabled = not self.enabled
	
	#if self.splitterStatus == "Left\nSide":
	    #self.componentList[self.componentCount]= ['SLT%s/%s'%(str(self.sltTsld.GetValue()), str(100-self.sltTsld.GetValue())), str(self.startNM)+'-'+str(self.currNM)]
	#if self.splitterStatus == "Right\nSide":
	    #self.componentList[self.componentCount]= ['SLT%s/%s'%(str(self.sltTsld.GetValue()), str(100-self.sltTsld.GetValue())), str(self.currNM)+'-'+str(self.endNM)]	
	
			
    #def setDyeList(self, emLow, emHgh):
	
	#meta = ExperimentSettings.getInstance()	
	#dyeList = []
	
	#for dye in FLUOR_SPECTRUM: 
	    #dyeLowNM, dyeHghNM = meta.getNM(FLUOR_SPECTRUM[dye][1])
	    #for wl in range(emLow, emHgh+1):
		#if wl in range(dyeLowNM, dyeHghNM+1):
		    #dyeList.append(dye)
	##self.dyeListBox.Clear()	
	#return sorted(list(set(dyeList)))  
    
    def OnDyeSelect(self, event):
	meta = ExperimentSettings.getInstance()	
	emLow, emHgh = meta.getNM(self.componentList[self.componentCount-1][1])
	self.componentList[self.componentCount]= ['DYE'+'_'+event.GetString(), str(emLow)+'-'+str(emHgh)]  # if multi selection seperate dye name with : 
	
    def OnMyDyeSelect(self, event):
	meta = ExperimentSettings.getInstance()	
	emLow, emHgh = meta.getNM(self.componentList[self.componentCount-1][1])
	dye = wx.GetTextFromUser('Enter Dye name within the emission range '+str(emLow)+' - '+str(emHgh), 'Customized Dye')
        if dye != '':
	    self.dyeListBox.Delete(self.dyeListBox.GetSelection())
            self.dyeListBox.Append(dye)
	    self.componentList[self.componentCount]= ['DYE'+'_'+dye, str(emLow)+'-'+str(emHgh)]
	    self.dyeListBox.Select(event.GetSelection())

    def OnDetectorVoltSet(self, event):
	
	meta = ExperimentSettings.getInstance()
        volt = self.detector.GetValue()
        #self.voltageValue.SetLabel(str(volt)+" Volts")
	emLow, emHgh = meta.getNM(self.componentList[self.componentCount-1][1])
	self.componentList[self.componentCount]= ['DTC%s'%str(volt), str(emLow)+'-'+str(emHgh)] 
    
    def getEmission(self, wl):
	
	meta = ExperimentSettings.getInstance()	
	emSpect = []

	for dye in FLUOR_SPECTRUM:
	    
	    extLow, extHgh = meta.getNM(FLUOR_SPECTRUM[dye][0])
	    emtLow, emtHgh = meta.getNM(FLUOR_SPECTRUM[dye][1])
	    
	    if self.belongsTo(wl,extLow, extHgh):
		emSpect.append(emtLow)
		emSpect.append(emtHgh)
	
	return min(emSpect), max(emSpect)    
	    

class MirrorSpectrum(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,  size=(100, 30), style=wx.SUNKEN_BORDER)

        self.parent = parent
	
	self.meta = ExperimentSettings.getInstance()
	
	self.startNM, self.endNM = self.meta.getNM(self.parent.GetParent().componentList[self.parent.GetParent().componentCount-1][1])
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
	
	# get the component WL of the just previous one
	nmRange =  self.meta.partition(range(self.startNM, self.endNM+1), 5)
	
        sldLowVal = self.parent.GetParent().dmtTsld.GetValue()
	sldLowMinVal = self.parent.GetParent().dmtTsld.GetMin()
        sldHghVal = self.parent.GetParent().dmtBsld.GetValue()
	sldHghMaxVal = self.parent.GetParent().dmtBsld.GetMax()
	
	sldLowMove = (sldLowVal-sldLowMinVal)*100/(sldHghMaxVal-sldLowMinVal)  # 100 pxl is the physical size of the spectra panel
	sldHghMove = (sldHghVal-sldLowMinVal)*100/(sldHghMaxVal-sldLowMinVal)
	        
        # Draw the specturm according to the spectral range
        dc.GradientFillLinear((0, 0, 20, 30),  self.meta.nmToRGB(nmRange[0]), self.meta.nmToRGB(nmRange[1]), wx.EAST)
        dc.GradientFillLinear((20, 0, 20, 30), self.meta.nmToRGB(nmRange[1]), self.meta.nmToRGB(nmRange[2]), wx.EAST)
        dc.GradientFillLinear((40, 0, 20, 30), self.meta.nmToRGB(nmRange[2]), self.meta.nmToRGB(nmRange[3]), wx.EAST)
        dc.GradientFillLinear((60, 0, 20, 30), self.meta.nmToRGB(nmRange[3]), self.meta.nmToRGB(nmRange[4]), wx.EAST)
        dc.GradientFillLinear((80, 0, 20, 30), self.meta.nmToRGB(nmRange[4]), self.meta.nmToRGB(nmRange[5]), wx.EAST)
        
        # Draw the slider on the spectrum to depict the selected range within the specta
	dc = wx.PaintDC(self)
	dc.SetPen(wx.Pen(self.GetBackgroundColour()))
	dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
	dc.DrawRectangle(0, 0, sldLowMove, 30)
	dc.DrawRectangle(sldHghMove, 0, 100, 30) 
	
	#dc.SetPen(wx.Pen('#5C5142'))
	#dc.DrawText(str(sldLowVal), sldLowMove-7, 10)
	#dc.DrawText(str(sldHghVal), sldHghMove-7, 10)
    
    def OnSize(self, event):
	self.Refresh()	
    
class FilterSpectrum(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,  size=(100, 30), style=wx.SUNKEN_BORDER)

        self.parent = parent
	self.meta = ExperimentSettings.getInstance()
	
	self.startNM, self.endNM = self.meta.getNM(self.parent.GetParent().componentList[self.parent.GetParent().componentCount-1][1])
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
	
	# get the component WL of the just previous one
	nmRange =  self.meta.partition(range(self.startNM, self.endNM+1), 5)
	
        fltTsldVal = self.parent.GetParent().fltTsld.GetValue()
	fltTsldMinVal = self.parent.GetParent().fltTsld.GetMin()
        fltBsldVal = self.parent.GetParent().fltBsld.GetValue()
	fltBsldMaxVal = self.parent.GetParent().fltBsld.GetMax()
	
	fltTsldMove = (fltTsldVal-fltTsldMinVal)*100/(fltBsldMaxVal-fltTsldMinVal)  # 100 pxl is the physical size of the spectra panel
	fltBsldMove = (fltBsldVal-fltTsldMinVal)*100/(fltBsldMaxVal-fltTsldMinVal)
	        
        # Draw the specturm according to the spectral range
        dc.GradientFillLinear((0, 0, 20, 30), self.meta.nmToRGB(nmRange[0]), self.meta.nmToRGB(nmRange[1]), wx.EAST)
        dc.GradientFillLinear((20, 0, 20, 30), self.meta.nmToRGB(nmRange[1]), self.meta.nmToRGB(nmRange[2]), wx.EAST)
        dc.GradientFillLinear((40, 0, 20, 30), self.meta.nmToRGB(nmRange[2]), self.meta.nmToRGB(nmRange[3]), wx.EAST)
        dc.GradientFillLinear((60, 0, 20, 30), self.meta.nmToRGB(nmRange[3]), self.meta.nmToRGB(nmRange[4]), wx.EAST)
        dc.GradientFillLinear((80, 0, 20, 30), self.meta.nmToRGB(nmRange[4]), self.meta.nmToRGB(nmRange[5]), wx.EAST)
        
        # Draw the slider on the spectrum to depict the selected range within the specta
	dc = wx.PaintDC(self)
	dc.SetPen(wx.Pen(self.GetBackgroundColour()))
	dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
	dc.DrawRectangle(0, 0, fltTsldMove, 30)
	dc.DrawRectangle(fltBsldMove, 0, 100, 30) 
	
	#dc.SetPen(wx.Pen('#5C5142'))
	#dc.DrawText(str(sldLowVal), sldLowMove-7, 10)
	#dc.DrawText(str(fltBsldVal), fltBsldMove-7, 10)

       
    def OnSize(self, event):
        self.Refresh()

class SplitterSpectrum(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent,  size=(100, 30), style=wx.SUNKEN_BORDER)

        self.parent = parent
	
	self.meta = ExperimentSettings.getInstance()
	
	self.startNM, self.endNM = self.meta.getNM(self.parent.GetParent().componentList[self.parent.GetParent().componentCount-1][1])
	
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
	
	# get the component WL of the just previous one
	nmRange =  self.meta.partition(range(self.startNM, self.endNM+1), 5)
	
        sltTsldVal = self.parent.GetParent().sltTsld.GetValue()

	#currNM = int(((self.endNM - self.startNM)*sltTsldVal)/100)+self.startNM
	
	currNM = sltTsldVal
	        
        # Draw the specturm according to the spectral range
        dc.GradientFillLinear((0, 0, 20, 30), self.meta.nmToRGB(nmRange[0]), self.meta.nmToRGB(nmRange[1]), wx.EAST)
        dc.GradientFillLinear((20, 0, 20, 30), self.meta.nmToRGB(nmRange[1]), self.meta.nmToRGB(nmRange[2]), wx.EAST)
        dc.GradientFillLinear((40, 0, 20, 30), self.meta.nmToRGB(nmRange[2]), self.meta.nmToRGB(nmRange[3]), wx.EAST)
        dc.GradientFillLinear((60, 0, 20, 30), self.meta.nmToRGB(nmRange[3]), self.meta.nmToRGB(nmRange[4]), wx.EAST)
        dc.GradientFillLinear((80, 0, 20, 30), self.meta.nmToRGB(nmRange[4]), self.meta.nmToRGB(nmRange[5]), wx.EAST)
        
        # Draw the slider on the spectrum to depict the selected range within the specta
	dc = wx.PaintDC(self)
	dc.SetBrush(wx.Brush('White'))
	dc.DrawRectangle(sltTsldVal, 0, 5, 30)

	# Draw the ratio value on the spectrum
	dc.SetPen(wx.Pen('#5C5142'))
	dc.DrawText(str(100-sltTsldVal)+'/'+str(sltTsldVal), sltTsldVal-14, 10)
       
    def OnSize(self, event):
        self.Refresh()

class ImgPanel(wx.Panel):
    def __init__(self, parent, image):
        wx.Panel.__init__(self, parent)

        img = wx.Image(image, wx.BITMAP_TYPE_ANY)
        self.sBmp = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))

        sizer = wx.BoxSizer()
        sizer.Add(item=self.sBmp, proportion=0, flag=wx.ALL, border=10)
        self.SetBackgroundColour('green')
        self.SetSizerAndFit(sizer)
	
#class MyFrame(wx.Frame):
    #def __init__(self, parent, id, title):
        #wx.Frame.__init__(self, parent, id, title, size=(350,200))

        #panel = wx.Panel(self, -1)
        #wx.Button(panel, 1, '+ Add Channel', (100,100))
        #self.Bind (wx.EVT_BUTTON, self.OnShowCustomDialog, id=1)

    #def OnShowCustomDialog(self, event):
        #dia = ChannelBuilder(self, -1, 'Channel Builder')
        #dia.ShowModal()
        #dia.Destroy()

#class MyApp(wx.App):
    #def OnInit(self):
        #frame = MyFrame(None, -1, 'Title')
        #frame.Show(True)
        #frame.Centre()
        #return True

#app = MyApp(0)
#app.MainLoop()