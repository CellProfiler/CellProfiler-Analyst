import os
import wx
import sys
import re
import icons
import experimentsettings as exp
from timeline import Timeline
from wx.html import HtmlEasyPrinting, HtmlWindow
from experimentsettings import ExperimentSettings

meta = exp.ExperimentSettings.getInstance()
 

      
class PrintProtocol(wx.Frame):
 
    ##----------------------------------------------------------------------
    def __init__(self, screen, **kwargs):
        wx.Frame.__init__(self, None, size=(700,800))
        
        self.screen =  screen
 
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.printer = HtmlEasyPrinting(name='Printing', parentWindow=None)
 
        self.html = HtmlWindow(self.panel)
        self.html.SetRelatedFrame(self, self.GetTitle())
 
        #if not os.path.exists('screenshot.htm'):
        self.formatProtocolInfo()
        self.html.LoadPage('screenshot.htm')
        
        # adjust widths for Linux (figured out by John Torres 
        # http://article.gmane.org/gmane.comp.python.wxpython/67327)
        if sys.platform == 'linux2':
            client_x, client_y = self.ClientToScreen((0, 0))
            border_width = client_x - self.screen.x
            title_bar_height = client_y - self.screen.y
            self.screen.width += (border_width * 2)
            self.screen.height += title_bar_height + border_width
 
        #Create a DC for the whole screen area
        dcScreen = wx.ScreenDC()
 
        #Create a Bitmap that will hold the screenshot image later on
        bmp = wx.EmptyBitmap(self.screen.width, self.screen.height)
 
        #Create a memory DC that will be used for actually taking the screenshot
        memDC = wx.MemoryDC()
 
        #Tell the memory DC to use our Bitmap
        memDC.SelectObject(bmp)
 
        #Blit (in this case copy) the actual screen on the memory DC and thus the Bitmap
        memDC.Blit( 0, #Copy to this X coordinate
                    0, #Copy to this Y coordinate
                    self.screen.width, #Copy this width
                    self.screen.height, #Copy this height
                    dcScreen, #From where do we copy?
                    self.screen.x, #What's the X offset in the original DC?
                    self.screen.y  #What's the Y offset in the original DC?
                    )
 
        #Select the Bitmap out of the memory DC by selecting a new uninitialized Bitmap
        memDC.SelectObject(wx.NullBitmap)
 
        img = bmp.ConvertToImage()
        fileName = "myImage.png"
        img.SaveFile(fileName, wx.BITMAP_TYPE_PNG)
        print '...saving as png!'

  
        self.sendToPrinter()
        
        
    def formatProtocolInfo(self):
        ''' this method format the information of the annoted protocols 
        ready for printing'''
        meta = exp.ExperimentSettings.getInstance()
        
        self.printfile = file('screenshot.htm', 'w')
      
        timepoints = meta.get_timeline().get_unique_timepoints()
        timeline = meta.get_timeline()
        self.events_by_timepoint = timeline.get_events_by_timepoint()
        
        
        
        #---- Overview Secion ---#
        protocol_info =  self.decode_event_description('Overview|Project')
    
        self.printfile.write('<html><head><title>Experiment Protocol</title></head>'
                 '<br/><body><h1>'+protocol_info.pop(0)[1]+'</h1>'
                 '<h3>1. Experiment Overview</h3>'                
                )
        for element in protocol_info:
            self.printfile.write('<dfn>'+element[0]+': </dfn><code>'+element[1]+'</code><br />')
          
          
        # - node by node printing --#    
	#self.nodes_by_timepoint = timeline.get_nodes_by_timepoint()
	#for t, nodes in self.nodes_by_timepoint.iteritems():
	    #for node in nodes:
		#print t, node, node.get_parent()
	
        ##---- Instrument Secion ---#
        #self.printfile.write('<h2>2. Instrument Settings</h2>')
        #for instrument in meta.get_eventtype_list('Instrument'):
            #for instance in meta.get_field_instances('Instrument|%s'%instrument):
                #self.printfile.write('<p><b><big>Configuration of '+instance+' instance of '+instrument+'</b></big></p><br />')
                
                #instrument_info = self.decode_event_description('Instrument|%s|%s'%(instrument, instance))
                
                #for element in instrument_info:
                    #if isinstance(element[1], list) is False:
                        #self.printfile.write('<dfn>'+element[0]+': </dfn><code>'+element[1]+'</code><br />')  # elements that are not channel specific like make, model, type...etc.
                    #else:
                        #self.printfile.write('<dfn>'+element[0]+': </dfn>') 
                        #for component in element[1]:  #diff components of a given channel
                            #self.printfile.write('<tt>'+meta.decode_ch_component(component[0])+' >> </tt>')
                        #self.printfile.write('<br />')
                 
        #---- Method Secion ---#
        self.printfile.write('<h2>2. Materials and Methods</h2>')
                                 
        for i, timepoint in enumerate(timepoints):
            for protocol in set([exp.get_tag_protocol(ev.get_welltag()) for ev in self.events_by_timepoint[timepoint]]):
	
		# protocol info includes the description of the attributes for each of the protocol e.g. Perturbation|Chem|1 is passed
		protocol_info = self.decode_event_description(protocol)
		# spatial info includes plate well inforamtion for this event well tag e.g. Perturbation|Bio|Wells|1|793
		####spatial_info = self.decode_event_location(ev.get_welltag())  ##THIS THING DOES NOT WORK WHEN SAME EVENT AT SAME TIME POINT HAPPENS
		welltag = exp.get_tag_stump(protocol, 2)+'|Wells|%s|%s'%(exp.get_tag_attribute(protocol), str(timepoint)) 
		spatial_info = self.decode_event_location(welltag)
		# -- write the description and location of the event --#
                if exp.get_tag_event(protocol) == 'Seed':  
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Seeding</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
                    self.printfile.write('<tt>'+protocol_info[0]+'</tt><br />')
		    self.printlocation(spatial_info) #prints the plate well design as table and highlights the affected wells
		    
                if exp.get_tag_event(protocol) == 'Harvest': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Harvesting</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    
                if exp.get_tag_event(protocol) == 'Chem':  
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Chemical Perturbation</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
                    self.printfile.write('<tt>'+protocol_info[0]+'</tt><br />') 		    
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Bio':  
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Biological Perturbation</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    self.printfile.write('<tt>'+protocol_info[0]+'</tt><br />') 
                    for element in protocol_info[1]:
                        self.printfile.write('<tt><b>'+element[0]+': </b>'+element[1]+'</tt><br />')
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Stain': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Staining with chemical dye</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    
                if exp.get_tag_event(protocol) == 'Antibody': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Staining with immunofluorescence</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    
                if exp.get_tag_event(protocol) == 'Primer': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Staining with genetic materials</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    
                if exp.get_tag_event(protocol) == 'Spin':
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Spinning</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[1]:  # step description
			description = element[0]
			if len(element[1]) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]
			else:
			    duration = ''	
			self.printfile.write('<ul><li><code>'+description+duration+'</code></li></ul>')
		    self.printlocation(spatial_info) 
			
                if exp.get_tag_event(protocol) == 'Wash': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Washing</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
                if exp.get_tag_event(protocol) == 'Dry': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Drying</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
                if exp.get_tag_event(protocol) == 'Medium': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Addition of medium</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')  
                if exp.get_tag_event(protocol) == 'Incubator': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Incubation</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')  
                
                if exp.get_tag_event(protocol) == 'TLM': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Timelapse image acquisition</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    self.printlocation(spatial_info)
		    
		    # write the image urls
		    instance = exp.get_tag_attribute(protocol)
		    self.printfile.write('<table border="0">')
		    for plate, wells in spatial_info.iteritems():
			for well in wells:
			    pw = plate, well
			    self.printfile.write('<code><b>Well '+well+'</b></code><br />')
			    for url in meta.get_field('DataAcquis|TLM|Images|%s|%s|%s'%(instance,timepoint, pw), []):
				self.printfile.write('<small>'+url+'</small><br />')
			    #self.printfile.write('<tr><code><td>'+well+':</td><td>'+('<br />'.join(meta.get_field('DataAcquis|FCS|Images|%s|%s|%s'%(instance,timepoint, pw), [])))+'</td></code></tr>')
			self.printfile.write('</table><br />')		    
		    
                if exp.get_tag_event(protocol) == 'HCS': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Static image acquisition</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
               
                if exp.get_tag_event(protocol) == 'FCS': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b> FCS file acquisition</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    
		    self.printfile.write('<code>'+protocol_info[0]+'</code><br />') # header part	
		    self.printfile.write('<code><i><u> Channel description </u></i></code><br />') # header part
		    
		    for element in protocol_info[1]:  # step description
			self.printfile.write('<ul><li><code><b>'+element[0]+': </b>') # channel name
			for i, component in enumerate(element[1]):  # config of each component of this channel
			    if i == len(element[1])-1:
				self.printfile.write(meta.decode_ch_component(component[0]))
			    else:
				self.printfile.write(meta.decode_ch_component(component[0])+' >> ')
			self.printfile.write('</code></li></ul>')	
		    self.printfile.write('<code>'+protocol_info[2]+'</code><br />') # footer part
		    # for the affected wells the image location
		    
		    self.printlocation(spatial_info) #prints the plate well design as table and highlights the affected wells
		    
		    # write the image urls
		    instance = exp.get_tag_attribute(protocol)
		    self.printfile.write('<table border="0">')
		    for plate, wells in spatial_info.iteritems():
			for well in wells:
			    pw = plate, well
			    self.printfile.write('<code><b>'+plate+'['+well+']'+'</b></code><br />')
			    for url in meta.get_field('DataAcquis|FCS|Images|%s|%s|%s'%(instance,timepoint, pw), []):
				self.printfile.write('<small>'+url+'</small><br />')
			    #self.printfile.write('<tr><code><td>'+well+':</td><td>'+('<br />'.join(meta.get_field('DataAcquis|FCS|Images|%s|%s|%s'%(instance,timepoint, pw), [])))+'</td></code></tr>')
			self.printfile.write('</table><br />')
				
			
                if exp.get_tag_event(protocol) == 'CriticalPoint': # to implement if there are events at the same timepoint write those event first then the critical point
                    self.printfile.write('<font size="2" color="red">Critical point: '+meta.get_field('Notes|CriticalPoint|Description|%s'%exp.get_tag_attribute(protocol))+'</font></em><br />')                
            self.printfile.write('<br />')   
               
        
        #---- Protocol Map ---#             
        self.printfile.write('<br />'.join(['<h2>3. Methodology Map</h2>',                                 
                             '<br/><br/>',                     
                             '<center><img src=myImage.png width=500 height=600></center>',
                             '</body></html>']))
                                                     
        self.printfile.close()  

    #----------------------------------------------------------------------
    def sendToPrinter(self):
        """"""
        self.printer.GetPrintData().SetPaperId(wx.PAPER_LETTER)
        self.printer.PrintFile(self.html.GetOpenedPage())
    
    def stringSplitByNumbers(self, x):
	r = re.compile('(\d+)')
	l = r.split(x)
	return [int(y) if y.isdigit() else y for y in l]     
    
    def decode_event_description(self, protocol):
        
        if exp.get_tag_type(protocol) == 'Overview':
            info = []
            info.append(('Title', meta.get_field('Overview|Project|Title', default='Not specified')))
            info.append(('Aims', meta.get_field('Overview|Project|Aims', default='Not specified')))
            info.append(('Keywords', meta.get_field('Overview|Project|Keywords', default='Not specified')))
            info.append(('Experiment date', meta.get_field('Overview|Project|ExptDate', default='Not specified')))
            info.append(('Relevant publications', meta.get_field('Overview|Project|Publications', default='Not specified')))
            info.append(('Institution', meta.get_field('Overview|Project|Institution', default='Not specified')))
            info.append(('Address', meta.get_field('Overview|Project|Address', default='Not specified')))
            return info
	
	if exp.get_tag_event(protocol) == 'Seed':
	    instance = exp.get_tag_attribute(protocol)
	    header = ''
	    footer = ''
	    info = []	
	    
	    if meta.get_field('CellTransfer|Seed|StockInstance|%s'%instance) is not None:
		header += meta.get_field('StockCulture|Sample|CellLine|%s'%meta.get_field('CellTransfer|Seed|StockInstance|%s'%instance)) 
	    header += ' cells were seeded with a density of %s. ' %meta.get_field('CellTransfer|Seed|SeedingDensity|%s'%instance, default = '')
	    if meta.get_field('CellTransfer|Seed|MediumUsed|%s'%instance) is not None:
		header += meta.get_field('CellTransfer|Seed|MediumUsed|%s'%instance)+' medium was used '
	    if meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%instance) is not None:
		header += 'with following medium additives: %s. ' %meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%instance)
	    if meta.get_field('CellTransfer|Seed|Trypsinizatiton|%s'%instance) is 'Yes':   
		header += 'Also trypsinisation was performed'
	    
	    return (header, info, footer)
	
	if exp.get_tag_event(protocol) == 'Chem':
		    instance = exp.get_tag_attribute(protocol)
		    header = ''
		    footer = ''
		    info = []	
		    
		    if meta.get_field('Perturbation|Chem|ChemName|%s'%instance) is not None:                    
			header += meta.get_field('Perturbation|Chem|ChemName|%s'%instance)
			subtext = '%s,%s' %(meta.get_field('Perturbation|Chem|Manufacturer|%s'%instance, default=''), meta.get_field('Perturbation|Chem|CatNum|%s'%instance, default=''))
			if re.search('\w+', subtext): #if the mfg and or cat number of the chemical is mentioned
			    header += '[%s]'%subtext
			header += ' was added'
		    if meta.get_field('Perturbation|Chem|Conc|%s'%instance) is not None: 
			header += ' with a concentration of %s %s' %(meta.get_field('Perturbation|Chem|Conc|%s'%instance), meta.get_field('Perturbation|Chem|Unit|%s'%instance, default='')) 
		    if meta.get_field('Perturbation|Chem|Additives|%s'%instance) is not None:    
			header += '.  Following additives were included: %s' %meta.get_field('Perturbation|Chem|Additives|%s'%instance)
		    if meta.get_field('Perturbation|Chem|Other|%s'%instance) is not None: 
			header += '.  Other information: %s'%meta.get_field('Perturbation|Chem|Other|%s'%instance) 
			
		    return (header, info, footer) 		    

        if exp.get_tag_event(protocol) == 'Bio':
            instance = exp.get_tag_attribute(protocol)
	    header = ''
	    footer = ''
	    info = []
	    
	    header += 'Biological perturbation was done with following agent'
	    
            info.append(('RNAi Sequence', meta.get_field('Perturbation|Bio|SeqName|%s'%instance, default = 'Not specified')))
            info.append(('Acession Number', meta.get_field('Perturbation|Bio|AccessNumber|%s'%instance, default = 'Not specified')))
            info.append(('Target Gene Accession Number', meta.get_field('Perturbation|Bio|TargetGeneAccessNum|%s'%instance, default = 'Not specified')))
            info.append(('Concentration', meta.get_field('Perturbation|Bio|Conc|%s'%instance, default = 'Not specified')+' '+meta.get_field('Perturbation|Bio|Unit|%s'%instance, default = '')))
            info.append(('Additives', meta.get_field('Perturbation|Bio|Additives|%s'%instance, default = 'Not specified')))
            info.append(('Other Information', meta.get_field('Perturbation|Bio|Other|%s'%instance, default = 'Not specified')))     
            
            return (header, info, footer)
        
        if exp.get_tag_event(protocol) == 'Spin':
            instance = exp.get_tag_attribute(protocol)
	    header = ''
	    footer = ''
	    info = []
	
            steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Spin|Step', str(instance)), key = self.stringSplitByNumbers)
	    
	    header += meta.get_field('AddProcess|Spin|SpinPrtocolTag|%s'%instance)
	    
	    for step in steps:
		info.append(meta.get_field('AddProcess|Spin|%s|%s'%(step,instance)))
		
	    return (header, info, footer)
	
	if exp.get_tag_event(protocol) == 'FCS':
	    instance = exp.get_tag_attribute(protocol)
	    header = ''
	    footer = ''
	    info = []
	    
	    if meta.get_field('DataAcquis|FCS|FlowcytInstance|%s'%instance) is not None:
		cytometer_instance = meta.get_field('DataAcquis|FCS|FlowcytInstance|%s'%instance)
		header += meta.get_field('Instrument|Flowcytometer|Manufacter|%s'%cytometer_instance, default='')+' flowcytometer '
		if meta.get_field('Instrument|Flowcytometer|Model|%s'%cytometer_instance) is not None:
		    header += '(model: %s)' %meta.get_field('Instrument|Flowcytometer|Model|%s'%cytometer_instance, default = 'not specified')
		header += ' was used. '
		
	    for attribute, description in sorted(meta.get_attribute_dict('Instrument|Flowcytometer|%s'%cytometer_instance).iteritems()):
		if attribute.startswith('Manufacter')  or attribute.startswith('Model'):
		    continue
		else:
		    info.append((attribute, description))  # attribute is Ch# and description is the component list
	    
	    if meta.get_field('DataAcquis|FCS|Software|%s'%instance) is not None:
		footer += meta.get_field('DataAcquis|FCS|Software|%s'%instance)+' software was used for data acquisition. '
		
	    if meta.get_field('DataAcquis|FCS|Format|%s'%instance) is not None:
		footer += 'FCS files in %s'%meta.get_field('DataAcquis|FCS|Format|%s'%instance)+' format were saved in following location\n'
		
	    return (header, info, footer)
	
	          
			    
	    
                

            
            #if event == 'Harvest':
                    ##if meta.get_field('CellTransfer|Harvest|StockInstance|%s'%instance) is not None:
                        ##text += meta.get_field('StockCulture|Sample|CellLine|%s'%meta.get_field('CellTransfer|Harvest|StockInstance|%s'%instance))
                    #if meta.get_field('CellTransfer|Seed|Trypsinizatiton|%s'%instance) is 'Yes':   
                        #text += ' cells were harvested by trypsinisation '
                    #text += 'cell density was %s. ' %meta.get_field('CellTransfer|Seed|SeedingDensity|%s'%instance, default = '')
                    #if meta.get_field('CellTransfer|Seed|MediumUsed|%s'%instance) is not None:
                        #text += meta.get_field('CellTransfer|Seed|MediumUsed|%s'%instance)+' medium was used '
                    #if meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%instance) is not None:
                        #text += 'with following medium additives: %s. ' %meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%instance)
              
         


    def decode_event_location(self, plate_well_info):
	d = {}
	for pw in meta.get_field(plate_well_info):
	    plate = pw[0]
	    well = pw[1]
	    
	    if d.get(plate, None) is None:
		d[plate] = [well]
	    else:
		d[plate] += [well]
		
	return d  
    
    def printlocation(self, spatial_info):
	self.printfile.write('<code><i><u> Location information</u></i></code>') # get the wells and url for the data files
	for plate, wells in spatial_info.iteritems():
	    self.printfile.write('<br /><dfn>'+plate+'</dfn><br />')
	    self.printfile.write('<table border="1">')
	    for row in exp.PlateDesign.get_row_labels(exp.PlateDesign.get_plate_format(plate)):
		self.printfile.write('<tr>')
		for col in exp.PlateDesign.get_col_labels(exp.PlateDesign.get_plate_format(plate)):
		    well = row+col
		    if well in wells:
			self.printfile.write('<td BGCOLOR=yellow>'+well+'</td>')
		    else:
			self.printfile.write('<td><code>'+well+'</code></td>')
		self.printfile.write('</tr>')
	    self.printfile.write('</table><br />')	
	    
 
    
class wxHTML(HtmlWindow):
    #----------------------------------------------------------------------
    def __init__(self, parent, id):
        html.HtmlWindow.__init__(self, parent, id, style=wx.NO_FULL_REPAINT_ON_RESIZE)
 
 
if __name__ == '__main__':
    app = wx.App(False)
    frame = PrintProtocol()
    #frame.Show()
    app.MainLoop()