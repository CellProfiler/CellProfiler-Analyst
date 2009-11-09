from ColorBarPanel import ColorBarPanel
from DBConnect import DBConnect, UniqueImageClause, image_key_columns
from PlateMapPanel import *
import ImageTools
import Properties
import logging
import numpy as np
import os
import matplotlib.cm
import re
import wx

p = Properties.Properties.getInstance()
# Hack the properties module so it doesn't require the object table.
Properties.optional_vars += ['object_table']
db = DBConnect.getInstance()


class AwesomePMP(PlateMapPanel):
    '''
    PlateMapPanel that does selection and tooltips for data.
    '''
    def __init__(self, parent, data, shape=None, well_labels=None,
                 colormap='jet', wellshape=ROUNDED, row_label_format=None, **kwargs):
        PlateMapPanel.__init__(self, parent, data, shape, well_labels, 
                               colormap, wellshape, row_label_format,  **kwargs)
                
        self.chMap = p.image_channel_colors
        self.plate = None
        self.tip = wx.ToolTip('')
        self.tip.Enable(False)
        self.SetToolTip(self.tip)
        
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRClick)
        
    def SetPlate(self, plate):
        self.plate = plate


    def OnMotion(self, evt):
        well = self.GetWellAtCoord(evt.X, evt.Y)
        wellLabel = self.GetWellLabelAtCoord(evt.X, evt.Y)
        if well is not None:
            self.tip.SetTip('%s: %s'%(wellLabel,self.data[well]))
            self.tip.Enable(True)
        else:
            self.tip.Enable(False)
        
    def OnClick(self, evt):
        if evt.ShiftDown():
            self.ToggleSelected(self.GetWellAtCoord(evt.X, evt.Y))
        else:
            self.SelectWell(self.GetWellAtCoord(evt.X, evt.Y))
            
    def OnDClick(self, evt):
        if self.plate is not None:
            well = self.GetWellLabelAtCoord(evt.X, evt.Y)
            imKeys = db.execute('SELECT %s FROM %s WHERE %s="%s" AND %s="%s"'%
                                (UniqueImageClause(), p.image_table, p.well_id, well, p.plate_id, self.plate))
            for imKey in imKeys:
                ImageTools.ShowImage(imKey, self.chMap, parent=self)

    def OnRClick(self, evt):
        if self.plate is not None:
            well = self.GetWellLabelAtCoord(evt.X, evt.Y)
            imKeys = db.execute('SELECT %s FROM %s WHERE %s="%s" AND %s="%s"'%
                                (UniqueImageClause(), p.image_table, p.well_id, well, p.plate_id, self.plate))
            self.ShowPopupMenu(imKeys, (evt.X,evt.Y))
                
    def ShowPopupMenu(self, items, pos):
        self.popupItemById = {}
        popupMenu = wx.Menu()
        popupMenu.SetTitle('Show Image')
        for item in items:
            id = wx.NewId()
            self.popupItemById[id] = item
            popupMenu.Append(id,str(item))
        popupMenu.Bind(wx.EVT_MENU, self.OnSelectFromPopupMenu)
        self.PopupMenu(popupMenu, pos)

    def OnSelectFromPopupMenu(self, evt):
        """Handles selections from the popup menu."""
        imKey = self.popupItemById[evt.GetId()]
        ImageTools.ShowImage(imKey, self.chMap, parent=self)



ID_EXIT = wx.NewId()

class PlateMapBrowser(wx.Frame):
    '''
    '''
    def __init__(self, parent, size=(800,-1)):
        wx.Frame.__init__(self, parent, -1, size=size)
        assert (p.well_id is not None and p.plate_id is not None), \
            'Plate Viewer requires the well_id and plate_id columns to be defined in your properties file.'

        self.Center()        
        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.loadCSVMenuItem = self.fileMenu.Append(-1, text='Load CSV\tCtrl+O', help='Load a CSV file storing per-image data')
        self.fileMenu.AppendSeparator()
        self.exitMenuItem = self.fileMenu.Append(id=ID_EXIT, text='Exit\tCtrl+Q',help='Close Plate Viewer')
        self.GetMenuBar().Append(self.fileMenu, 'File')
        
        self.Bind(wx.EVT_MENU, self.OnLoadCSV, self.loadCSVMenuItem)
        wx.EVT_MENU(self, ID_EXIT, lambda(_):self.Close())
        
        self.plateNames = db.GetPlateNames()

        dataSourceSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Source:'), wx.VERTICAL)
        dataSourceSizer.Add(wx.StaticText(self, label='Data source:'))
        src_choices = [p.image_table]
        if p.object_table:
            src_choices += [p.object_table]
        try:
            db.execute('SELECT * FROM __Classifier_output LIMIT 1')
            src_choices += ['__Classifier_output']
        except:
            pass
        self.sourceChoice = wx.Choice(self, choices=src_choices)
        self.sourceChoice.Select(0)
        dataSourceSizer.Add(self.sourceChoice)
                
        dataSourceSizer.AddSpacer((-1,10))
        dataSourceSizer.Add(wx.StaticText(self, label='Measurement:'))
        measurements = self.GetNumericColumnsFromTable(p.image_table)
        self.measurementsChoice = wx.Choice(self, choices=measurements)#, size=(132,-1))
        self.measurementsChoice.Select(0)
        dataSourceSizer.Add(self.measurementsChoice)
        
        groupingSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Data aggregation:'), wx.VERTICAL)
        groupingSizer.Add(wx.StaticText(self, label='Aggregation method:'))
        aggregation = ['mean', 'sum', 'median', 'stdev', 'cv%', 'min', 'max']
        self.aggregationMethodsChoice = wx.Choice(self, choices=aggregation)
        self.aggregationMethodsChoice.Select(0)
        groupingSizer.Add(self.aggregationMethodsChoice)
        
        viewSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='View options:'), wx.VERTICAL)
        viewSizer.Add(wx.StaticText(self, label='Color map:'))
        maps = [m for m in matplotlib.cm.datad.keys() if not m.endswith("_r")]
        maps.sort()
        self.colorMapsChoice = wx.Choice(self, choices=maps)
        self.colorMapsChoice.SetSelection(maps.index('jet'))
        viewSizer.Add(self.colorMapsChoice)
        
        viewSizer.AddSpacer((-1,10))
        viewSizer.Add(wx.StaticText(self, label='Well shape:'))
        self.wellShapeChoice = wx.Choice(self, choices=all_well_shapes)
        self.wellShapeChoice.Select(0)
        viewSizer.Add(self.wellShapeChoice)
        
        viewSizer.AddSpacer((-1,10))
        viewSizer.Add(wx.StaticText(self, label='Number of plates:'))
        self.numberOfPlatesTE = wx.TextCtrl(self, -1, '1', style=wx.TE_PROCESS_ENTER)
        viewSizer.Add(self.numberOfPlatesTE)
        
        controlSizer = wx.BoxSizer(wx.VERTICAL)
        controlSizer.Add(dataSourceSizer, 0, wx.EXPAND)
        controlSizer.AddSpacer((-1,10))
        controlSizer.Add(groupingSizer, 0, wx.EXPAND)
        controlSizer.AddSpacer((-1,10))
        controlSizer.Add(viewSizer, 0, wx.EXPAND)
    
        self.plateMapSizer = wx.GridSizer(1,1,5,5)
        self.plateMaps = []
        self.plateMapChoices = []
        
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightSizer.Add(self.plateMapSizer, 1, wx.EXPAND|wx.BOTTOM, 10)
        self.colorBar = ColorBarPanel(self, 'jet', size=(-1,25))
        self.rightSizer.Add(self.colorBar, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(controlSizer, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 10)
        mainSizer.Add(self.rightSizer, 1, wx.EXPAND|wx.ALL, 10)
        
        self.SetSizer(mainSizer)
        self.SetClientSize((self.Size[0],self.Sizer.CalcMin()[1]))
        
        self.sourceChoice.Bind(wx.EVT_CHOICE, self.OnSelectDataSource)
        self.measurementsChoice.Bind(wx.EVT_CHOICE, self.OnSelectMeasurement)
        self.aggregationMethodsChoice.Bind(wx.EVT_CHOICE, self.OnSelectAggregationMethod)
        self.colorMapsChoice.Bind(wx.EVT_CHOICE, self.OnSelectColorMap)
        self.numberOfPlatesTE.Bind(wx.EVT_TEXT_ENTER, self.OnEnterNumberOfPlates)
        self.wellShapeChoice.Bind(wx.EVT_CHOICE, self.OnSelectWellShape)
        
        global_extents = db.execute('SELECT MIN(%s), MAX(%s) FROM %s'%(self.measurementsChoice.GetStringSelection(), 
                                                                       self.measurementsChoice.GetStringSelection(), 
                                                                       self.sourceChoice.GetStringSelection()))[0]
        self.colorBar.SetGlobalExtents(global_extents)
        self.AddPlateMap()
        self.UpdatePlateMaps()
    
    def OnLoadCSV(self, evt):
        dlg = wx.FileDialog(self, "Select a comma-separated-values file to load...",
                            defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadCSV(filename)
            
    def LoadCSV(self, filename):
        countsTable = os.path.splitext(os.path.split(filename)[1])[0]
        if db.CreateTempTableFromCSV(filename, countsTable):
            self.AddTableChoice(countsTable)
            
    def AddTableChoice(self, table):
        sel = self.sourceChoice.GetSelection()
        self.sourceChoice.SetItems(self.sourceChoice.GetItems()+[table])
        self.sourceChoice.Select(sel)
            
    def AddPlateMap(self, plateIndex=0):
        '''
        Adds a new blank plateMap to the PlateMapSizer.
        '''
        data = np.ones(int(p.plate_type))
        if p.plate_type == '384': shape = (16,24)
        elif p.plate_type == '96': shape = (8,12)
        elif p.plate_type == '5600': shape = (40,140)
        elif p.plate_type == '1536': shape = (32,48)
        
        # Try to get explicit labels for all wells, otherwise the PMP
        # will generate labels automatically which MAY NOT MATCH labels
        # in the database, and therefore, showing images will not work. 
        res = db.execute('SELECT %s FROM %s WHERE %s!="" GROUP BY %s'%
                         (p.well_id, p.image_table, p.well_id, p.well_id))
        well_labels = [x[0] for x in res]
        if len(well_labels) != len(data):
            well_labels = None
            
        self.plateMaps += [AwesomePMP(self, data, shape, well_labels=well_labels,
                                      colormap=self.colorMapsChoice.GetStringSelection(),
                                      wellshape=self.wellShapeChoice.GetStringSelection())]
        self.plateMapChoices += [wx.Choice(self, choices=self.plateNames)]
        self.plateMapChoices[-1].Select(plateIndex)
        self.plateMapChoices[-1].Bind(wx.EVT_CHOICE, self.OnSelectPlate)
        
        plateMapChoiceSizer = wx.BoxSizer(wx.HORIZONTAL)
        plateMapChoiceSizer.Add(wx.StaticText(self, label='Plate:'))
        plateMapChoiceSizer.Add(self.plateMapChoices[-1])
        
        singlePlateMapSizer = wx.BoxSizer(wx.VERTICAL)
        singlePlateMapSizer.Add(plateMapChoiceSizer, 0, wx.ALIGN_CENTER)
        singlePlateMapSizer.Add(self.plateMaps[-1], 1, wx.EXPAND, wx.ALIGN_CENTER)
        
        self.plateMapSizer.Add(singlePlateMapSizer, 1, wx.EXPAND, wx.ALIGN_CENTER)
            
    def UpdatePlateMaps(self):
        measurement = self.measurementsChoice.GetStringSelection()
        table       = self.sourceChoice.GetStringSelection()
        aggMethod   = self.aggregationMethodsChoice.GetStringSelection()
        self.colorBar.ClearNotifyWindows()

        if aggMethod == 'mean':
            expression = "AVG(%s.%s)"%(table, measurement)
        elif aggMethod == 'stdev':
            expression = "STDDEV(%s.%s)"%(table, measurement)
        elif aggMethod == 'cv%':
            expression = "STDDEV(%s.%s)/AVG(%s.%s)*100"%(table, measurement, table, measurement)
        elif aggMethod == 'sum':
            expression = "SUM(%s.%s)"%(table, measurement)
        elif aggMethod == 'min':
            expression = "MIN(%s.%s)"%(table, measurement)
        elif aggMethod == 'max':
            expression = "MAX(%s.%s)"%(table, measurement)
        elif aggMethod == 'median':
            expression = "MEDIAN(%s.%s)"%(table, measurement)
        
        if table == p.image_table:
            group = True
            platesWellsAndVals = db.execute('SELECT %s, %s, %s FROM %s %s'%
                                      (p.plate_id, p.well_id, expression, table,
                                       'GROUP BY %s, %s'%(p.plate_id, p.well_id) if group else ''))
        elif set([p.well_id, p.plate_id]) == set(db.GetLinkingColumnsForTable(table)):
            # For data from tables with well and plate columns, we simply
            # fetch and aggregate
            # XXX: SHOULD we allow aggregation of per-well data since there 
            #      should logically only be one row per well???? 
            group = True
            platesWellsAndVals = db.execute('SELECT %s, %s, %s FROM %s %s'%
                                      (p.plate_id, p.well_id, expression, table,
                                       'GROUP BY %s, %s'%(p.plate_id, p.well_id) if group else ''))
        else:
            # For data from other tables without well and plate columns, we 
            # need to link the table to the per image table via the 
            # ImageNumber column
            group = True
            platesWellsAndVals = db.execute('SELECT %s.%s, %s.%s, %s FROM %s, %s WHERE %s %s'%
                                      (p.image_table, p.plate_id, p.image_table, p.well_id, expression, 
                                       p.image_table, table, 
                                       ' AND '.join(['%s.%s=%s.%s'%(table, id, p.image_table, id) for id in db.GetLinkingColumnsForTable(table)]),
                                       'GROUP BY %s.%s, %s.%s'%(p.image_table, p.plate_id, p.image_table, p.well_id) if group else ''))
        platesWellsAndVals = np.array(platesWellsAndVals, dtype=object)
        # Replace None's with nan
        for row in platesWellsAndVals:
            if row[2] is None:
                row[2] = np.nan
        gmin = np.nanmin([float(val) for _,_,val in platesWellsAndVals])
        gmax = np.nanmax([float(val) for _,_,val in platesWellsAndVals])

        data = []
        dmax = -np.inf
        dmin = np.inf
        for plateChoice, plateMap in zip(self.plateMapChoices, self.plateMaps):
            plate = plateChoice.GetStringSelection()
            plateMap.SetPlate(plate)
            self.colorBar.AddNotifyWindow(plateMap)
            wellsAndVals = [v[1:] for v in platesWellsAndVals if str(v[0])==plate]
            data += [FormatPlateMapData(wellsAndVals)]
            dmin = np.nanmin([float(val) for _,val in wellsAndVals]+[dmin])
            dmax = np.nanmax([float(val) for _,val in wellsAndVals]+[dmax])
        
        if np.isinf(dmin) or np.isinf(dmax):
            dlg = wx.MessageDialog(self, 'No numeric data was found in this column ("%s.%s") for the selected plate ("%s").'%(table,measurement,plate), 'No data!', style=wx.OK)
            dlg.ShowModal()
            gmin = gmax = dmin = dmax = 1.
        
        self.colorBar.SetLocalExtents([dmin,dmax])
        self.colorBar.SetGlobalExtents([gmin,gmax])
        
        for d, plateMap in zip(data, self.plateMaps):
            plateMap.SetData(d, data_range=self.colorBar.GetLocalExtents(), 
                             clip_interval=self.colorBar.GetLocalInterval(), 
                             clip_mode=self.colorBar.GetClipMode())
        
    def GetNumericColumnsFromTable(self, table):
        ''' Fetches names of numeric columns for the given table. '''
        measurements = db.GetColumnNames(table)
        types = db.GetColumnTypes(table)
        return [m for m,t in zip(measurements, types) if t in [float, int, long]]
        
    def OnSelectDataSource(self, evt):
        '''
        Handles the selection of a source table (per-image or per-object) from
        a choice box.  The measurement choice box is populated with the names
        of numeric columns from the selected table.
        '''
        table = self.sourceChoice.GetStringSelection()
        self.measurementsChoice.SetItems(self.GetNumericColumnsFromTable(table))
        self.measurementsChoice.Select(0)
        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()
        
    def OnSelectPlate(self, evt):
        ''' Handles the selection of a plate from the plate choice box. '''
        self.UpdatePlateMaps()
        
    def OnSelectMeasurement(self, evt):
        ''' Handles the selection of a measurement to plot from a choice box. '''
        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()
        
    def OnSelectAggregationMethod(self, evt):
        ''' Handles the selection of an aggregation method from the choice box. '''
        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()
        
    def OnSelectColorMap(self, evt):
        ''' Handles the selection of a color map from a choice box. '''
        map = self.colorMapsChoice.GetStringSelection()
        cm = matplotlib.cm.get_cmap(map)
        
        self.colorBar.SetMap(map)
        for plateMap in self.plateMaps:
            plateMap.SetColorMap(map)
            
    def OnSelectWellShape(self, evt):
        ''' Handles the selection of a well shape from a choice box. '''
        sel = self.wellShapeChoice.GetStringSelection()
        if sel.lower() == 'image':
            dlg = wx.MessageDialog(self, 'This mode will render each well as a shrunken image loaded from that well. This feature is currently VERY SLOW since it requires loading hundreds of full sized images. Are you sure you want to continue?',
                                   'Load all images?', wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            if dlg.ShowModal() != wx.ID_OK:
                self.wellShapeChoice.SetSelection(0)
                return
        for platemap in self.plateMaps:
            platemap.SetWellShape(sel)
            
    def OnEnterNumberOfPlates(self, evt):
        ''' Handles the entry of a plates to view from a choice box. '''
        try:
            nPlates = int(self.numberOfPlatesTE.GetValue())
        except:
            logging.warn('Invalid # of plates! Please enter a number between 1 and 100')
            return
        if nPlates>100:
            logging.warn('Too many plates! Please enter a number between 1 and 100')
            return
        if nPlates<1:
            logging.warn('You must display at least 1 plate.')
            self.numberOfPlatesTE.SetValue('1')
            nPlates = 1
        
        # Record the indices of the plates currently selected.
        # Pad the list with sequential plate indices then crop to the new number of plates.
        currentPlates = [plateChoice.GetSelection() for plateChoice in self.plateMapChoices]
        currentPlates = (currentPlates+[(currentPlates[-1]+1+p)%nPlates for p in range(nPlates)])[:nPlates]
        # Remove all plateMaps
        self.plateMapSizer.Clear(deleteWindows=True)
        self.plateMaps = []
        self.plateMapChoices = []
        # Restructure the plateMapSizer appropriately
        rows = cols = np.ceil(np.sqrt(nPlates))
        self.plateMapSizer.SetRows(rows)
        self.plateMapSizer.SetCols(cols)
        # Add the plate maps
        for plateIndex in currentPlates:
            self.AddPlateMap(plateIndex)
        self.UpdatePlateMaps()
        self.plateMapSizer.Layout()
        

def FormatPlateMapData(wellsAndVals):
    '''
    wellsAndVals: a list of 2-tuples of wells and values
    returns a properly shaped numpy array of the given values with NaNs
            filling empty slots.  
    '''
    #TODO: well naming format (A##/123..) may have to go in props file
    format = 'A01'
    
    # Make an educated guess at the well naming format
    res = db.execute('SELECT DISTINCT %s FROM %s '%(p.well_id, p.image_table))
    a = b = c = 0
    for r in res:
        if re.match('^[A-Za-z]\d\d$', str(r[0])):
            a += 1
        elif re.match('^\d+$', str(r[0])):
            b += 1
        else:
            c += 1
    if a > b and a > c:
        format = 'A01'
    elif b > a and b > c:
        format = '123'
    else:
        logging.warn('Could not determine well naming format from the database. Trying default...')
    
    if p.plate_type == '384': shape = (16,24)
    elif p.plate_type == '96': shape = (8,12)
    elif p.plate_type == '5600':
        shape = (40,140)
        format = '123'
    elif p.plate_type == '1536': shape = (32,48)
    data = np.ones(shape)*np.nan
    for well, val in wellsAndVals:
        if format=='A01':
            if re.match('^[a-zA-Z][0-9]?[0-9]?$', well):
                row = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'.index(well[0])
                col = int(well[1:])-1
                data[row,col] = float(val)
        elif format=='123':
            row = (int(well)-1)/shape[1]
            col = (int(well)-1)%shape[1]
            data[row,col] = float(val)
    return data
    


def LoadProperties():
    import os
    dlg = wx.FileDialog(None, "Select a the file containing your properties.", style=wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        filename = dlg.GetPath()
        os.chdir(os.path.split(filename)[0])      # wx.FD_CHANGE_DIR doesn't seem to work in the FileDialog, so I do it explicitly
        p.LoadFile(filename)
    else:
        print 'Plate Viewer requires a properties file.  Exiting.'
        exit()

            
if __name__ == "__main__":
    app = wx.PySimpleApp()
        
    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        LoadProperties()
#        p.LoadFile('../properties/2009_02_19_MijungKwon_Centrosomes.properties')
#        p.LoadFile('../properties/Gilliland_LeukemiaScreens_Validation.properties')

    pmb = PlateMapBrowser(None)
    pmb.Show()

    app.MainLoop()
