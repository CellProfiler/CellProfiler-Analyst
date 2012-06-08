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
        protocol_info =  self.decode_event_description('Overview|Project|1') #this 1 is psedo to make it coherent with other instance based tabs
    
        self.printfile.write('<html><head><title>Experiment Protocol</title></head>'
                 '<br/><body><h1>'+protocol_info[0]+'</h1>'
                 '<h3>1. Experiment Overview</h3>'                
                )
        for element in protocol_info[1]:
            self.printfile.write('<dfn>'+element[0]+': </dfn><code>'+element[1]+'</code><br />')
        #---- Stock Culture ----#
	stockcultures = meta.get_field_instances('StockCulture|Sample')
	self.printfile.write('<h3>2. Stock Culture</h3>')	
	if stockcultures:
	    for instance in stockcultures:
		protocol_info = self.decode_event_description('StockCulture|Sample|%s'%instance)
		self.printfile.write('<i>'+protocol_info[0]+' </i><br />')
		for element in protocol_info[1]:
		    self.printfile.write('<dfn>'+element[0]+': </dfn><code>'+element[1]+'</code><br />')
		#self.printfile.write('<code>'+protocol_info[2]+' </code><br />')
		self.printfile.write('<br />')
		self.printfile.write('<dfn>'+protocol_info[2][0]+'</dfn><br />'
	else:
	    self.printfile.write('<code>No stock culture was used for this experiment</code>')
          	
        #---- Instrument Secion ---#
        self.printfile.write('<h3>3. Instrument Settings</h3>')
	
	microscopes = meta.get_field_instances('Instrument|Microscope')
	flowcytometers = meta.get_field_instances('Instrument|Flowcytometer')
	
	if microscopes:
	    for instance in microscopes:
		protocol_info = self.decode_event_description('Instrument|Microscope|%s'%instance)
		self.printfile.write('<i>Channel Name: '+protocol_info[0]+' (microscope instance %s)'%instance+'</i><br />')
		for component in protocol_info[1]:
		    if component[0] == 'Component':
			self.printfile.write('<strong>'+component[1]+'</strong><br />')
		    else:			
			self.printfile.write('<code><b>'+component[0]+': </b>'+component[1]+'</code><br />')
		self.printfile.write('<p></p>')
			
	if flowcytometers:
	    for instance in flowcytometers:
		protocol_info = self.decode_event_description('Instrument|Flowcytometer|%s'%instance)
		self.printfile.write('<i>'+protocol_info[0]+' </i><br />')

		for element in protocol_info[1]:  # channels
		    self.printfile.write('<ul><li><code><b>'+element[0]+': </b>') # channel name
		    for i, component in enumerate(element[1]):  # config of each component of this channel
			if i == len(element[1])-1:
			    self.printfile.write(meta.decode_ch_component(component[0]))
			else:
			    self.printfile.write(meta.decode_ch_component(component[0])+' >> ')
		    self.printfile.write('</code></li></ul>')
		self.printfile.write('<p></p>')
	 
	
        #---- Material and Method Secion ---#
        self.printfile.write('<h3>4. Materials and Methods</h3>')
                                 
        for i, timepoint in enumerate(timepoints):
            for protocol in set([exp.get_tag_protocol(ev.get_welltag()) for ev in self.events_by_timepoint[timepoint]]):
		
		instance = exp.get_tag_attribute(protocol)
		# protocol info includes the description of the attributes for each of the protocol e.g. Perturbation|Chem|1 is passed
		protocol_info = self.decode_event_description(protocol)
		# spatial info includes plate well inforamtion for this event well tag e.g. Perturbation|Bio|Wells|1|793
		####spatial_info = self.decode_event_location(ev.get_welltag())  ##THIS THING DOES NOT WORK WHEN SAME EVENT AT SAME TIME POINT HAPPENS
		welltag = exp.get_tag_stump(protocol, 2)+'|Wells|%s|%s'%(instance, str(timepoint)) 
		spatial_info = self.decode_event_location(welltag)
		# -- write the description and location of the event --#
                if (exp.get_tag_event(protocol) == 'Seed') and (meta.get_field('CellTransfer|Seed|StockInstance|%s'%instance) is not None):  
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Seeding</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
                    self.printfile.write('<code>'+protocol_info[0]+'</code><br />')
		    self.printlocation(spatial_info)
		    
		    # if harvest precede seeding
		    #if meta.get_field('CellTransfer|Seed|HarvestInstance|%s'%instance) is not None:
			## origin(harvesting instance), destination(seeding instance), timepoint
			#self.printCellTransfer(meta.get_field('CellTransfer|Seed|HarvestInstance|%s'%instance), 
			                       #instance, timepoint)
			
                if exp.get_tag_event(protocol) == 'Harvest': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Harvest-Seed (Cell Transfer)</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    self.printCellTransfer(instance, timepoint)
		    
                if exp.get_tag_event(protocol) == 'Chem':  #TO DO
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Chemical Perturbation</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
                    self.printfile.write('<code>'+protocol_info[0]+'</code><br />') 		    
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Bio':  
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Biological Perturbation</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    self.printfile.write('<code>'+protocol_info[0]+'</code><br />') 
                    for element in protocol_info[1]:
                        self.printfile.write('<code><i>'+element[0]+': </i>'+element[1]+'</code><br />')
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Dye': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Staining with chemical dye</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[1]:  # step description
			description = element[0]
			duration = element[1]
			temp = element[2]
			if len(duration) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]			    
			if len(temp) > 0: # duration is mentioned
			    temp = ' at %s C.'%element[2]
			self.printfile.write('<ul><li><code>'+description+duration+temp+'</code></li></ul>')		    
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Immuno': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Staining with immunofluorescence</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[2]: #footer part goes here
			self.printfile.write('<code>'+element+'</code><br />') #footer part 
		    for element in protocol_info[1]:  # step description
			description = element[0]
			duration = element[1]
			temp = element[2]
			if len(duration) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]			    
			if len(temp) > 0: # duration is mentioned
			    temp = ' at %s C.'%element[2]
			self.printfile.write('<ul><li><code>'+description+duration+temp+'</code></li></ul>')			    
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Genetic': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Staining with genetic materials</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[2]: #footer part goes here
			self.printfile.write('<code><i>'+element[0]+': </i>'+element[1]+'</code><br />')#footer part 
		    for element in protocol_info[1]:  # step description
			description = element[0]
			duration = element[1]
			temp = element[2]
			if len(duration) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]			    
			if len(temp) > 0: # duration is mentioned
			    temp = ' at %s C.'%element[2]
			self.printfile.write('<ul><li><code>'+description+duration+temp+'</code></li></ul>')			    
		    self.printlocation(spatial_info)
		    
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
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[1]:  # step description
			description = element[0]
			if len(element[1]) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]
			else:
			    duration = ''	
			self.printfile.write('<ul><li><code>'+description+duration+'</code></li></ul>')
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Dry': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Drying</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[1]:  # step description
			description = element[0]
			if len(element[1]) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]
			else:
			    duration = ''	
			self.printfile.write('<ul><li><code>'+description+duration+'</code></li></ul>')
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Medium': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Addition of medium</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')  
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[2]: #footer part goes here
			self.printfile.write('<code>'+element+'</code><br />') #footer part 
		    for element in protocol_info[1]:  # step description
			description = element[0]
			if len(element[1]) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]
			else:
			    duration = ''	
			self.printfile.write('<ul><li><code>'+description+duration+'</code></li></ul>')
		    self.printlocation(spatial_info) 
		    
                if exp.get_tag_event(protocol) == 'Incubator': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Incubation</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />')  
		    self.printfile.write('<i>'+protocol_info[0]+'</i><br />') # header part
		    for element in protocol_info[2]: #footer part goes here
			self.printfile.write('<code><i>'+element[0]+': </i>'+element[1]+'</code><br />') #footer part 
		    for element in protocol_info[1]:  # step description
			description = element[0]
			if len(element[1]) > 0: # duration is mentioned
			    duration = ' for %s minutes'%element[1]
			else:
			    duration = ''	
			self.printfile.write('<ul><li><code>'+description+duration+'</code></li></ul>')
		    self.printlocation(spatial_info)
                
                if exp.get_tag_event(protocol) == 'TLM': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b>Timelapse image acquisition</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    self.printfile.write('<code>'+protocol_info[0]+'</code><br />') # header part wrtie wich setting instance being used
		    for element in protocol_info[1]:
			self.printfile.write('<code><i>'+element[0]+': </i>'+element[1]+'</code><br />')		    
		    self.printlocation(spatial_info)
		    # write the image urls
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
		    self.printfile.write('<code>'+protocol_info[0]+'</code><br />') # header part wrtie wich setting instance being used
		    for element in protocol_info[1]:
			self.printfile.write('<code><i>'+element[0]+': </i>'+element[1]+'</code><br />')		    
		    self.printlocation(spatial_info)
		    # write the image urls
		    self.printfile.write('<table border="0">')
		    for plate, wells in spatial_info.iteritems():
			for well in wells:
			    pw = plate, well
			    self.printfile.write('<code><b>Well '+well+'</b></code><br />')
			    for url in meta.get_field('DataAcquis|HCS|Images|%s|%s|%s'%(instance,timepoint, pw), []):
				self.printfile.write('<small>'+url+'</small><br />')
			    #self.printfile.write('<tr><code><td>'+well+':</td><td>'+('<br />'.join(meta.get_field('DataAcquis|FCS|Images|%s|%s|%s'%(instance,timepoint, pw), [])))+'</td></code></tr>')
			self.printfile.write('</table><br />')		    
               
                if exp.get_tag_event(protocol) == 'FCS': 
                    self.printfile.write('Step '+str(i+1)+':  <em><b> FCS file acquisition</b></em>         at '+exp.format_time_string(timepoint)+' hrs<br />') 
		    self.printfile.write('<code>'+protocol_info[0]+'</code><br />') # header part wrtie wich setting instance being used	
		    for element in protocol_info[1]:
			self.printfile.write('<code><i>'+element[0]+': </i>'+element[1]+'</code><br />')		    
		    self.printlocation(spatial_info)
		    # write the image urls
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
                    self.printfile.write('<font size="2" color="red">Critical point: '+meta.get_field('Notes|CriticalPoint|Description|%s'%instance)+'</font></em><br />')                
		
		if exp.get_tag_event(protocol) == 'Hint': 
		    self.printfile.write('<font size="2" color="blue">Hint: '+meta.get_field('Notes|Hint|Description|%s'%instance)+'</font></em><br />')                		
		
		if exp.get_tag_event(protocol) == 'Rest': 
		    self.printfile.write('<font size="2" color="green">Rest: '+meta.get_field('Notes|Rest|Description|%s'%instance)+'</font></em><br />') 
		
		if exp.get_tag_event(protocol) == 'URL': 
		    self.printfile.write('<code>To find out more information please visit '+meta.get_field('Notes|URL|Description|%s'%instance)+'</code><br />')
		    
		if exp.get_tag_event(protocol) == 'Video': 
		    self.printfile.write('<code>For more information please watch the media file: '+meta.get_field('Notes|Video|Description|%s'%instance)+'</code><br />')
		
            self.printfile.write('<br />')   
               
        
        #---- Protocol Map ---#             
        self.printfile.write('<br />'.join(['<h3>5. Methodology Map</h3>',                                 
                             '<br/><br/>',                     
                             '<center><img src=myImage.png width=500 height=600></center>',
                             '</body></html>']))
                                                     
        self.printfile.close()  

    #----------------------------------------------------------------------
    def sendToPrinter(self):
        """"""
        self.printer.GetPrintData().SetPaperId(wx.PAPER_LETTER)
        self.printer.PrintFile(self.html.GetOpenedPage())    
    
    def decode_event_description(self, protocol):
	meta = ExperimentSettings.getInstance()
	instance = exp.get_tag_attribute(protocol)
	header = ''
	footer = []
	info = []
	
        if exp.get_tag_type(protocol) == 'Overview':
            header += meta.get_field('Overview|Project|Title', default='Not specified')
            info.append(('Aims', meta.get_field('Overview|Project|Aims', default='Not specified')))
	    info.append(('Funding Code', meta.get_field('Overview|Project|Fund', default='Not specified')))
            info.append(('Keywords', meta.get_field('Overview|Project|Keywords', default='Not specified')))
	    info.append(('Experiment Number', meta.get_field('Overview|Project|ExptNum', default='Not specified')))
            info.append(('Experiment date', meta.get_field('Overview|Project|ExptDate', default='Not specified')))
            info.append(('Relevant publications', meta.get_field('Overview|Project|Publications', default='Not specified')))
	    info.append(('Experimenter', meta.get_field('Overview|Project|Experimenter', default='Not specified')))
            info.append(('Institution', meta.get_field('Overview|Project|Institution', default='Not specified')))
	    info.append(('Department', meta.get_field('Overview|Project|Department', default='Not specified')))
            info.append(('Address', meta.get_field('Overview|Project|Address', default='Not specified')))
	    info.append(('Experiment Status', meta.get_field('Overview|Project|Status', default='Not specified')))
	    
            return (header, info)
	
	if exp.get_tag_type(protocol) == 'StockCulture':
	    header += '%s cell line (Authority %s, Ref: %s) was used. This will be referred as Stock Instance %s' %(meta.get_field('StockCulture|Sample|CellLine|%s'%instance, default='Not specified'),
	                                                meta.get_field('StockCulture|Sample|Authority|%s'%instance, default='Not specified'),
	                                                                                                         str(instance),	                                                
	                                                 meta.get_field('StockCulture|Sample|CatalogueNo|%s'%instance, default='Not specified'),
	                                                 str(instance))
	    info.append(('Depositors', meta.get_field('StockCulture|Sample|Depositors|%s'%instance, default='Not specified')))
	    info.append(('Biosafety Level', meta.get_field('StockCulture|Sample|Biosafety|%s'%instance, default='Not specified')))
	    info.append(('Shipment', meta.get_field('StockCulture|Sample|Shipment|%s'%instance, default='Not specified')))
	    info.append(('Permit', meta.get_field('StockCulture|Sample|Permit|%s'%instance, default='Not specified')))
	    info.append(('Growth Property', meta.get_field('StockCulture|Sample|GrowthProperty|%s'%instance, default='Not specified')))
	    info.append(('Organism', meta.get_field('StockCulture|Sample|Organism|%s'%instance, default='Not specified')))
	    info.append(('Morphology', meta.get_field('StockCulture|Sample|Morphology|%s'%instance, default='Not specified')))
	    info.append(('Organ', meta.get_field('StockCulture|Sample|Organ|%s'%instance, default='Not specified')))    
	    info.append(('Disease', meta.get_field('StockCulture|Sample|Disease|%s'%instance, default='Not specified')))
	    info.append(('Products', meta.get_field('StockCulture|Sample|Products|%s'%instance, default='Not specified')))
	    info.append(('Applications', meta.get_field('StockCulture|Sample|Applications|%s'%instance, default='Not specified')))
	    info.append(('Receptors', meta.get_field('StockCulture|Sample|Receptors|%s'%instance, default='Not specified')))
	    info.append(('Antigen', meta.get_field('StockCulture|Sample|Antigen|%s'%instance, default='Not specified')))
	    info.append(('DNA', meta.get_field('StockCulture|Sample|DNA|%s'%instance, default='Not specified')))
	    info.append(('Cytogenetic', meta.get_field('StockCulture|Sample|Cytogenetic|%s'%instance, default='Not specified')))
	    info.append(('Isoenzymes', meta.get_field('StockCulture|Sample|Isoenzymes|%s'%instance, default='Not specified')))
	    info.append(('Age of Organism (days)', meta.get_field('StockCulture|Sample|Age|%s'%instance, default='Not specified')))
	    info.append(('Gender', meta.get_field('StockCulture|Sample|Gender|%s'%instance, default='Not specified')))
	    info.append(('Ethnicity', meta.get_field('StockCulture|Sample|Ethnicity|%s'%instance, default='Not specified')))
	    info.append(('Comments', meta.get_field('StockCulture|Sample|Comments|%s'%instance, default='Not specified')))
	    info.append(('Publications', meta.get_field('StockCulture|Sample|Publications|%s'%instance, default='Not specified')))
	    info.append(('Related Products', meta.get_field('StockCulture|Sample|RelProduct|%s'%instance, default='Not specified')))
	    info.append(('Original Passage Number', meta.get_field('StockCulture|Sample|OrgPassageNo|%s'%instance, default='Not specified')))
	    info.append(('Preservation', meta.get_field('StockCulture|Sample|Preservation|%s'%instance, default='Not specified')))
	    info.append(('GrowthMedium', meta.get_field('StockCulture|Sample|GrowthMedium|%s'%instance, default='Not specified')))
	    
	    passages = [attr for attr in meta.get_attribute_list_by_instance('StockCulture|Sample', instance)
			                        if attr.startswith('Passage')]
	    
	    if passages:
		footer += '%s passages were carried out according to the specifications' %str(len(passages))
		
	    return (header, info, footer)	    
	
	if exp.get_tag_event(protocol) == 'Microscope':	    
	    header += '%s settings' %meta.get_field('Instrument|Microscope|ChannelName|%s'%instance, default = 'Not specified')
	    
	    if meta.get_field('Instrument|Microscope|Stand|%s'%instance) is not None:
		info.append(('Component', 'Stand'))
		info.append(('Type', meta.get_field('Instrument|Microscope|Stand|%s'%instance)[0]))
		info.append(('Make', meta.get_field('Instrument|Microscope|Stand|%s'%instance)[1]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Stand|%s'%instance)[2]))
		info.append(('Orientation', meta.get_field('Instrument|Microscope|Stand|%s'%instance)[3]))
		info.append(('Number of Lampss', str(meta.get_field('Instrument|Microscope|Stand|%s'%instance)[4])))
		info.append(('Number of Detectors', str(meta.get_field('Instrument|Microscope|Stand|%s'%instance)[5])))
	    if meta.get_field('Instrument|Microscope|Condensor|%s'%instance) is not None:
		info.append(('Component', 'Condensor'))
		info.append(('Type', meta.get_field('Instrument|Microscope|Condensor|%s'%instance)[0]))
		info.append(('Make', meta.get_field('Instrument|Microscope|Condensor|%s'%instance)[1]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Condensor|%s'%instance)[2]))
	    if meta.get_field('Instrument|Microscope|Stage|%s'%instance) is not None:
		info.append(('Component', 'Stage'))
		info.append(('Type', meta.get_field('Instrument|Microscope|Stage|%s'%instance)[0]))
		info.append(('Make', meta.get_field('Instrument|Microscope|Stage|%s'%instance)[1]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Stage|%s'%instance)[2]))
		info.append(('Stage Holder', meta.get_field('Instrument|Microscope|Stage|%s'%instance)[3]))
		info.append(('Holder Code', meta.get_field('Instrument|Microscope|Stage|%s'%instance)[4]))
	    if meta.get_field('Instrument|Microscope|Incubator|%s'%instance) is not None:
		info.append(('Component', 'Incubator'))
		info.append(('Make', meta.get_field('Instrument|Microscope|Incubator|%s'%instance)[0]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Incubator|%s'%instance)[1]))
		info.append(('Temperature(C)', meta.get_field('Instrument|Microscope|Incubator|%s'%instance)[2]))
		info.append(('CO2%', meta.get_field('Instrument|Microscope|Incubator|%s'%instance)[3]))
		info.append(('Humidity', meta.get_field('Instrument|Microscope|Incubator|%s'%instance)[4]))
		info.append(('Pressure', meta.get_field('Instrument|Microscope|Incubator|%s'%instance)[5]))
	    if meta.get_field('Instrument|Microscope|LightSource|%s'%instance) is not None:
		info.append(('Component', 'Light Source'))
		info.append(('Type', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[0]))
		info.append(('Source', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[1]))
		info.append(('Make', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[2]))
		info.append(('Model', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[3]))
		info.append(('Measured Power (User)', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[4]))
		info.append(('Measured Power (Instrument)', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[5]))
		info.append(('Shutter Used', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[6]))
		info.append(('Shutter Type', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[7]))
		info.append(('Shutter Make', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[8]))
		info.append(('Shutter Model', meta.get_field('Instrument|Microscope|LightSource|%s'%instance)[9]))
	    if meta.get_field('Instrument|Microscope|ExtFilter|%s'%instance) is not None:
		info.append(('Component', 'Excitation Filter'))
		info.append(('Wavelength Range (nm)', str(meta.get_field('Instrument|Microscope|ExtFilter|%s'%instance)[0])+' - '+str(meta.get_field('Instrument|Microscope|ExtFilter|%s'%instance)[1])))
		info.append(('Make', meta.get_field('Instrument|Microscope|ExtFilter|%s'%instance)[2]))
		info.append(('Model', meta.get_field('Instrument|Microscope|ExtFilter|%s'%instance)[3]))
	    if meta.get_field('Instrument|Microscope|Mirror|%s'%instance) is not None:	    
		info.append(('Component', 'Dichroic Mirror'))
		info.append(('Wavelength Range (nm)', str(meta.get_field('Instrument|Microscope|Mirror|%s'%instance)[0])+' - '+str(meta.get_field('Instrument|Microscope|Mirror|%s'%instance)[1])))
		info.append(('Mode', meta.get_field('Instrument|Microscope|Mirror|%s'%instance)[2]))
		info.append(('Make', meta.get_field('Instrument|Microscope|Mirror|%s'%instance)[3]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Mirror|%s'%instance)[4]))
		info.append(('Modification', meta.get_field('Instrument|Microscope|Mirror|%s'%instance)[5]))
	    if meta.get_field('Instrument|Microscope|EmsFilter|%s'%instance) is not None:
		info.append(('Component', 'Emission Filter'))
		info.append(('Wavelength Range (nm)', str(meta.get_field('Instrument|Microscope|EmsFilter|%s'%instance)[0])+' - '+str(meta.get_field('Instrument|Microscope|EmsFilter|%s'%instance)[1])))
		info.append(('Make', meta.get_field('Instrument|Microscope|EmsFilter|%s'%instance)[2]))
		info.append(('Model', meta.get_field('Instrument|Microscope|EmsFilter|%s'%instance)[3]))
	    if meta.get_field('Instrument|Microscope|Lens|%s'%instance) is not None:
		info.append(('Component', 'Lens'))
		info.append(('Make', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[0]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[1]))
		info.append(('Objective Magnification', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[2]))
		info.append(('Objective NA', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[3]))
		info.append(('Calibrated Magnification', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[4]))
		info.append(('Immersion', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[5]))
		info.append(('Correction Collar', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[6]))
		info.append(('Correction Value', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[7]))
		info.append(('Correction Type', meta.get_field('Instrument|Microscope|Lens|%s'%instance)[8]))
	    if meta.get_field('Instrument|Microscope|Lens|%s'%instance) is not None:
		info.append(('Component', 'Detector'))
		info.append(('Type', meta.get_field('Instrument|Microscope|Detector|%s'%instance)[0]))
		info.append(('Make', meta.get_field('Instrument|Microscope|Detector|%s'%instance)[1]))
		info.append(('Model', meta.get_field('Instrument|Microscope|Detector|%s'%instance)[2]))
		info.append(('Binning', str(meta.get_field('Instrument|Microscope|Detector|%s'%instance)[3])))
		info.append(('Exposure Time', meta.get_field('Instrument|Microscope|Detector|%s'%instance)[4]+' '+meta.get_field('Instrument|Microscope|Detector|%s'%instance)[5]))
		info.append(('Gain', meta.get_field('Instrument|Microscope|Detector|%s'%instance)[6]+' '+meta.get_field('Instrument|Microscope|Detector|%s'%instance)[7]))
		info.append(('Offset', meta.get_field('Instrument|Microscope|Detector|%s'%instance)[8]+' '+meta.get_field('Instrument|Microscope|Detector|%s'%instance)[9]))
		
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'Flowcytometer':
	    header += meta.get_field('Instrument|Flowcytometer|Manufacter|%s'%instance, default='')
	    if meta.get_field('Instrument|Flowcytometer|Model|%s'%instance) is not None:
		header += '(model: %s)' %meta.get_field('Instrument|Flowcytometer|Model|%s'%instance, default = 'not specified')
	    header += ' was used. '
		
	    for attribute, description in sorted(meta.get_attribute_dict('Instrument|Flowcytometer|%s'%instance).iteritems()):
		if attribute.startswith('Manufacter')  or attribute.startswith('Model'):
		    continue
		else:
		    info.append((attribute, description))  # attribute is Ch# and description is the component list	

	    return(header, info)
	    
	
	if exp.get_tag_event(protocol) == 'Seed':
	    if meta.get_field('CellTransfer|Seed|StockInstance|%s'%instance) is not None:
		header += meta.get_field('StockCulture|Sample|CellLine|%s'%meta.get_field('CellTransfer|Seed|StockInstance|%s'%instance)) 
	    header += ' cells were seeded with a density of %s from the stock flask (Instance %s). ' %(meta.get_field('CellTransfer|Seed|SeedingDensity|%s'%instance, default = ''), meta.get_field('CellTransfer|Seed|StockInstance|%s'%instance))
	    #if meta.get_field('CellTransfer|Seed|HarvestInstance|%s'%instance) is not None:
		#header += meta.get_field('StockCulture|Sample|CellLine|%s'%meta.get_field('CellTransfer|Seed|HarvestInstance|%s'%instance)) 
		#header += ' cells were seeded with a density of %s from the Wells depicted bellow. ' %meta.get_field('CellTransfer|Seed|SeedingDensity|%s'%instance, default = '')	    
	    if meta.get_field('CellTransfer|Seed|MediumUsed|%s'%instance) is not None:
		header += meta.get_field('CellTransfer|Seed|MediumUsed|%s'%instance)+' medium was used '
	    if meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%instance) is not None:
		header += 'with following medium additives: %s. ' %meta.get_field('CellTransfer|Seed|MediumAddatives|%s'%instance)
	    if meta.get_field('CellTransfer|Seed|Trypsinizatiton|%s'%instance) is 'Yes':   
		header += 'Also trypsinisation was performed'
	    
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'Chem':
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
		
	    return (header, info) 		    

        if exp.get_tag_event(protocol) == 'Bio':
	    header += 'Biological perturbation was done with following agent'
	    
            info.append(('RNAi Sequence', meta.get_field('Perturbation|Bio|SeqName|%s'%instance, default = 'Not specified')))
            info.append(('Acession Number', meta.get_field('Perturbation|Bio|AccessNumber|%s'%instance, default = 'Not specified')))
            info.append(('Target Gene Accession Number', meta.get_field('Perturbation|Bio|TargetGeneAccessNum|%s'%instance, default = 'Not specified')))
            info.append(('Concentration', meta.get_field('Perturbation|Bio|Conc|%s'%instance, default = 'Not specified')+' '+meta.get_field('Perturbation|Bio|Unit|%s'%instance, default = '')))
            info.append(('Additives', meta.get_field('Perturbation|Bio|Additives|%s'%instance, default = 'Not specified')))
            info.append(('Other Information', meta.get_field('Perturbation|Bio|Other|%s'%instance, default = 'Not specified')))     
            
            return (header, info)
	
	if exp.get_tag_event(protocol) == 'Dye':
	    header += meta.get_field('Staining|Dye|ProtocolName|%s'%instance)
	    steps = sorted(meta.get_attribute_list_by_instance('Staining|Dye|Step', str(instance)), key = meta.stringSplitByNumbers)
	    for step in steps:
		info.append(meta.get_field('Staining|Dye|%s|%s'%(step,instance)))
		
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'Immuno':
	    header += meta.get_field('Staining|Immuno|ProtocolName|%s'%instance)
	    if meta.get_field('Staining|Immuno|Target|%s'%instance) is not None:
		footer.append('Target antibody %s was used.'%meta.get_field('Staining|Immuno|Target|%s'%instance))
	    if meta.get_field('Staining|Immuno|Clonality|%s'%instance) is not None:
		footer.append('Clonality was %s.'%meta.get_field('Staining|Immuno|Clonality|%s'%instance))
	    if meta.get_field('Staining|Immuno|Primary|%s'%instance) is not None:
		token =''
		token += 'Primary antibody %s was used'%meta.get_field('Staining|Immuno|Primary|%s'%instance)[0]
		if len(meta.get_field('Staining|Immuno|Primary|%s'%instance)[1])>0:
		    token += ' with %s'%meta.get_field('Staining|Immuno|Primary|%s'%instance)[1]
		footer.append(token)
	    if meta.get_field('Staining|Immuno|Secondary|%s'%instance) is not None:
		token =''
		token += 'Secondary antibody %s was used'%meta.get_field('Staining|Immuno|Secondary|%s'%instance)[0]
		if len(meta.get_field('Staining|Immuno|Secondary|%s'%instance)[1])>0:
		    token += ' with %s'%meta.get_field('Staining|Immuno|Secondary|%s'%instance)[1]	
		footer.append(token)
	    if meta.get_field('Staining|Immuno|Tertiary|%s'%instance) is not None:
		token =''
		token += 'Tertiary antibody %s was used'%meta.get_field('Staining|Immuno|Tertiary|%s'%instance)[0]
		if len(meta.get_field('Staining|Immuno|Tertiary|%s'%instance)[1])>0:
		    token += ' with %s'%meta.get_field('Staining|Immuno|Tertiary|%s'%instance)[1]	
		footer.append(token)
	    steps = sorted(meta.get_attribute_list_by_instance('Staining|Immuno|Step', str(instance)), key = meta.stringSplitByNumbers)
	    for step in steps:
		info.append(meta.get_field('Staining|Immuno|%s|%s'%(step,instance)))	    
		
	    return (header, info, footer)  
	
	if exp.get_tag_event(protocol) == 'Genetic':
	    header += meta.get_field('Staining|Genetic|ProtocolName|%s'%instance)
	    footer.append(('Target Sequence', meta.get_field('Staining|Genetic|Target|%s'%instance, default = 'Not specified')))
	    footer.append(('Primer Sequence', meta.get_field('Staining|Genetic|Primer|%s'%instance, default = 'Not specified')))
	    footer.append(('Temperature', meta.get_field('Staining|Genetic|Temp|%s'%instance, default = 'Not specified')))
	    footer.append(('Temperature', meta.get_field('Staining|Genetic|GC|%s'%instance, default = 'Not specified')))	    
	    steps = sorted(meta.get_attribute_list_by_instance('Staining|Genetic|Step', str(instance)), key = meta.stringSplitByNumbers)
	    for step in steps:
		info.append(meta.get_field('Staining|Genetic|%s|%s'%(step,instance)))
		
	    return (header, info, footer)	
        
        if exp.get_tag_event(protocol) == 'Spin':
            header += meta.get_field('AddProcess|Spin|ProtocolName|%s'%instance)
	    steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Spin|Step', str(instance)), key = meta.stringSplitByNumbers)	    
	    for step in steps:
		info.append(meta.get_field('AddProcess|Spin|%s|%s'%(step,instance)))
		
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'Wash':
	    header += meta.get_field('AddProcess|Wash|ProtocolName|%s'%instance)
	    steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Wash|Step', str(instance)), key = meta.stringSplitByNumbers)	    
	    for step in steps:
		info.append(meta.get_field('AddProcess|Wash|%s|%s'%(step,instance)))
			
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'Dry':
	    header += meta.get_field('AddProcess|Dry|ProtocolName|%s'%instance)	    
	    steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Dry|Step', str(instance)), key = meta.stringSplitByNumbers)
	    for step in steps:
		info.append(meta.get_field('AddProcess|Dry|%s|%s'%(step,instance)))
			
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'Medium':
	    header += meta.get_field('AddProcess|Medium|ProtocolName|%s'%instance)
	    if meta.get_field('AddProcess|Medium|MediumAdditives|%s'%instance) is not None:
		footer.append('Medium additives used: %s'%meta.get_field('AddProcess|Medium|MediumAdditives|%s'%instance))
	    steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Medium|Step', str(instance)), key = meta.stringSplitByNumbers) 
	    for step in steps:
		info.append(meta.get_field('AddProcess|Medium|%s|%s'%(step,instance)))
			
	    return (header, info, footer)
	
	if exp.get_tag_event(protocol) == 'Incubator':
	    header += meta.get_field('AddProcess|Incubator|ProtocolName|%s'%instance)
	    footer.append(('Incubator settings', ''))
	    footer.append(('Manufacturer', meta.get_field('AddProcess|Incubator|Manufacter|%s'%instance, default = 'Not specified')))
	    footer.append(('Model', meta.get_field('AddProcess|Incubator|Model|%s'%instance, default = 'Not specified')))
	    footer.append(('Temperature', meta.get_field('AddProcess|Incubator|Temp|%s'%instance, default = 'Not specified')))
	    footer.append(('CO2%', meta.get_field('AddProcess|Incubator|CO2|%s'%instance, default = 'Not specified')))
	    footer.append(('Humidity', meta.get_field('AddProcess|Incubator|Humidity|%s'%instance, default = 'Not specified')))
	    footer.append(('Pressure', meta.get_field('AddProcess|Incubator|Pressure|%s'%instance, default = 'Not specified')))	    
	    steps = sorted(meta.get_attribute_list_by_instance('AddProcess|Medium|Step', str(instance)), key = meta.stringSplitByNumbers) 
	    for step in steps:
		info.append(meta.get_field('AddProcess|Medium|%s|%s'%(step,instance)))			
	    return (header, info, footer)	
	
	if exp.get_tag_event(protocol) == 'TLM':	    
	    if meta.get_field('DataAcquis|TLM|MicroscopeInstance|%s'%instance) is not None:
		ch_name = meta.get_field('DataAcquis|TLM|MicroscopeInstance|%s'%instance)
		cytometer_instance=meta.get_instance_by_field_value('Instrument|Microscope|ChannelName|', ch_name) 
		header += ch_name+' channel was used (see microscope instance %s for details)'%cytometer_instance		
	    info.append(('Image Format', meta.get_field('DataAcquis|TLM|Format|%s'%instance, default = 'Not specified')))
	    info.append(('Time Interval (min)', meta.get_field('DataAcquis|TLM|TimeInterval|%s'%instance, default = 'Not specified')))
	    info.append(('Total Frame/Pane Number', meta.get_field('DataAcquis|TLM|FrameNumber|%s'%instance, default = 'Not specified')))
	    info.append(('Stacking Order', meta.get_field('DataAcquis|TLM|StackProcess|%s'%instance, default = 'Not specified')))
	    info.append(('Pixel Size', meta.get_field('DataAcquis|TLM|PixelSize|%s'%instance, default = 'Not specified')))
	    info.append(('Pixel Conversion', meta.get_field('DataAcquis|TLM|PixelConvert|%s'%instance, default = 'Not specified')))
	    info.append(('Software', meta.get_field('DataAcquis|TLM|Software|%s'%instance, default = 'Not specified')))
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'HCS':	    
	    if meta.get_field('DataAcquis|HCS|MicroscopeInstance|%s'%instance) is not None:
		ch_name = meta.get_field('DataAcquis|HCS|MicroscopeInstance|%s'%instance)
		cytometer_instance=meta.get_instance_by_field_value('Instrument|Microscope|ChannelName|', ch_name) 
		header += ch_name+' channel was used (see microscope instance %s for details)'%cytometer_instance	
	    info.append(('Image Format', meta.get_field('DataAcquis|HCS|Format|%s'%instance, default = 'Not specified')))
	    info.append(('Pixel Size', meta.get_field('DataAcquis|HCS|PixelSize|%s'%instance, default = 'Not specified')))
	    info.append(('Pixel Conversion', meta.get_field('DataAcquis|HCS|PixelConvert|%s'%instance, default = 'Not specified')))
	    info.append(('Software', meta.get_field('DataAcquis|HCS|Software|%s'%instance, default = 'Not specified')))
	    return (header, info)
	
	if exp.get_tag_event(protocol) == 'FCS':	    
	    if meta.get_field('DataAcquis|FCS|FlowcytInstance|%s'%instance) is not None:
		cytometer_instance = meta.get_field('DataAcquis|FCS|FlowcytInstance|%s'%instance)
		header += meta.get_field('Instrument|Flowcytometer|Manufacter|%s'%cytometer_instance, default='')+' flowcytometer '
		if meta.get_field('Instrument|Flowcytometer|Model|%s'%cytometer_instance) is not None:
		    header += '(model: %s)' %meta.get_field('Instrument|Flowcytometer|Model|%s'%cytometer_instance, default = 'not specified')
		header += ' was used (see flowcytometer instance %s for details).'%cytometer_instance
	    if meta.get_field('DataAcquis|FCS|Software|%s'%instance) is not None:
		info.append(meta.get_field('DataAcquis|FCS|Software|%s'%instance)+' software was used for data acquisition. ')		
	    if meta.get_field('DataAcquis|FCS|Format|%s'%instance) is not None:
		info.append('FCS files in %s'%meta.get_field('DataAcquis|FCS|Format|%s'%instance)+' format were saved in following location\n')
		
	    return (header, info)
	
	          
			    
	    
                

            
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
	for plate, wells in spatial_info.iteritems():
	    self.printfile.write('<br /><cite>'+plate+'</cite><br />')
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
	    
    def printCellTransfer(self, harvest_inst, timepoint):
	seed_instances = meta.get_protocol_instances('CellTransfer|Seed|HarvestInstance|')
	for seed_inst in seed_instances:
	    if (meta.get_field('CellTransfer|Seed|Wells|%s|%s'%(seed_inst, str(timepoint+1))) is not None) and (meta.get_field('CellTransfer|Seed|HarvestInstance|%s'%seed_inst) == harvest_inst):
		harvest_spatial_info = self.decode_event_location('CellTransfer|Harvest|Wells|%s|%s'%(harvest_inst, str(timepoint)))
		seed_spatial_info = self.decode_event_location('CellTransfer|Seed|Wells|%s|%s'%(seed_inst, str(timepoint+1)))
	
	self.printfile.write('<table border="0">')
	self.printfile.write('<tr><td>')
	
	for plate, wells in harvest_spatial_info.iteritems():
	    self.printfile.write('<br /><cite>'+plate+'</cite><br />')
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
	    self.printfile.write('</table>')
	
	self.printfile.write('</td><td> -- Transferred to --> </td><td>')

	for plate, wells in seed_spatial_info.iteritems():
	    self.printfile.write('<br /><cite>'+plate+'</cite><br />')
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
	    self.printfile.write('</table>')
	self.printfile.write('</td></tr>')	
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