from DataModel import *
from DBConnect import DBConnect, UniqueImageClause, image_key_columns
from Properties import Properties
from PlateMapPanel import *
from ColorBarPanel import ColorBarPanel
import wx
import numpy as np
import pylab
import ImageTools
import re
import os

p = Properties.getInstance()
db = DBConnect.getInstance()
dm = DataModel.getInstance()

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
                ImageTools.ShowImage(imKey, p.image_channel_colors, parent=self)

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
        ImageTools.ShowImage(imKey, p.image_channel_colors, parent=self)



class PlateMapBrowser(wx.Frame):
    '''
    '''
    def __init__(self, parent, size=(800,-1)):
        wx.Frame.__init__(self, parent, -1, size=size)

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.loadCSVMenuItem = wx.MenuItem(parentMenu=self.fileMenu, id=wx.NewId(), text='L&oad CSV',
                                           help='Load a CSV file storing per-image data')
        self.fileMenu.AppendItem(self.loadCSVMenuItem)
        self.GetMenuBar().Append(self.fileMenu, '&File')
        
        
        self.plateNames = db.GetPlateNames()

        dataSourceSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Source:'), wx.VERTICAL)
        dataSourceSizer.Add(wx.StaticText(self, label='Data source:'))
        self.sourceChoice = wx.Choice(self, choices=[p.image_table, p.object_table])
        self.sourceChoice.Select(0)
        dataSourceSizer.Add(self.sourceChoice)
                
        dataSourceSizer.AddSpacer((-1,10))
        dataSourceSizer.Add(wx.StaticText(self, label='Measurements:'))
        measurements = self.GetNumericColumnsFromTable(p.image_table)
        self.measurementsChoice = wx.Choice(self, choices=measurements, size=(132,-1))
        self.measurementsChoice.Select(0)
        dataSourceSizer.Add(self.measurementsChoice)
        
        groupingSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Data Aggregation:'), wx.VERTICAL)
        groupingSizer.Add(wx.StaticText(self, label='Aggregation method:'))
        aggregation = ['average', 'sum', 'median', 'stdev', 'cv%', 'min', 'max']
        self.aggregationMethodsChoice = wx.Choice(self, choices=aggregation)
        self.aggregationMethodsChoice.Select(0)
        groupingSizer.Add(self.aggregationMethodsChoice)
        
        viewSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='View Options:'), wx.VERTICAL)
        viewSizer.Add(wx.StaticText(self, label='Color Map:'))
        maps = [m for m in pylab.cm.datad.keys() if not m.endswith("_r")]
        maps.sort()
        self.colorMapsChoice = wx.Choice(self, choices=maps)
        self.colorMapsChoice.SetSelection(maps.index('jet'))
        viewSizer.Add(self.colorMapsChoice)
        
        viewSizer.AddSpacer((-1,10))
        viewSizer.Add(wx.StaticText(self, label='Well Shape:'))
        self.wellShapeChoice = wx.Choice(self, choices=all_well_shapes)
        self.wellShapeChoice.Select(0)
        viewSizer.Add(self.wellShapeChoice)
        
        viewSizer.AddSpacer((-1,10))
        viewSizer.Add(wx.StaticText(self, label='Number of Plates:'))
        self.numberOfPlatesChoice = wx.Choice(self, choices=['1','2','4','9','16'])
        self.numberOfPlatesChoice.Select(0)
        viewSizer.Add(self.numberOfPlatesChoice)
        
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
        self.colorBar = ColorBarPanel(self, 'jet', (0,1), size=(-1,25))
        self.rightSizer.Add(self.colorBar, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(controlSizer, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 10)
        mainSizer.Add(self.rightSizer, 1, wx.EXPAND|wx.ALL, 10)
        
        self.SetSizer(mainSizer)
        self.SetClientSize((self.Size[0],self.Sizer.CalcMin()[1]))
        
        self.Bind(wx.EVT_MENU, self.OnLoadCSV, self.loadCSVMenuItem)
        self.sourceChoice.Bind(wx.EVT_CHOICE, self.OnSelectDataSource)
        self.measurementsChoice.Bind(wx.EVT_CHOICE, self.OnSelectMeasurement)
        self.aggregationMethodsChoice.Bind(wx.EVT_CHOICE, self.OnSelectAggregationMethod)
        self.colorMapsChoice.Bind(wx.EVT_CHOICE, self.OnSelectColorMap)
        self.numberOfPlatesChoice.Bind(wx.EVT_CHOICE, self.OnSelectNumberOfPlates)
        self.wellShapeChoice.Bind(wx.EVT_CHOICE, lambda(evt): [plateMap.SetWellShape(self.wellShapeChoice.GetStringSelection()) for plateMap in self.plateMaps])
        
        self.AddPlateMap()
        

    def OnLoadCSV(self, evt):
        dlg = wx.FileDialog(self, "Select a the file containing your classifier training set.",
                            defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.LoadCSV(filename)
    
            
    def LoadCSV(self, filename):
        countsTable = os.path.splitext(os.path.split(filename)[1])[0]
        if db.CreateTempTableFromCSV(filename, countsTable):
            sel = self.sourceChoice.GetSelection()
            self.sourceChoice.SetItems(self.sourceChoice.GetItems()+[countsTable])
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
        self.UpdatePlateMaps()
            
    
    def UpdatePlateMaps(self):
        measurement = self.measurementsChoice.GetStringSelection()
        table       = self.sourceChoice.GetStringSelection()
        aggMethod   = self.aggregationMethodsChoice.GetStringSelection()
        
        def computeMedians(wellsAndVals):
            ''' 
            Median is calculated from sorted values in X as:
            |X| ODD :  X[(n+1)/2]
            |X| EVEN : (X[n/2] + X[n/2+1]) / 2
            '''
            d = {}
            for well, val in wellsAndVals:
                if well not in d.keys():
                    d[well] = [val]
                else:
                    d[well] += [val]
            wellsAndMedians = []
            for well, vals in d.items():
                N = len(d[well])
                sortedVals = sorted(d[well])
                if N%2 != 0:
                    wellsAndMedians += [(well, sortedVals[(N+1)/2])]
                else:
                    wellsAndMedians += [(well, (sortedVals[(N/2)]+sortedVals[(N/2+1)])/2)]
            return wellsAndMedians
        
        data = []
        dmax = -np.inf
        dmin = np.inf
        for plateChoice, plateMap in zip(self.plateMapChoices, self.plateMaps):
            plate = plateChoice.GetStringSelection()
            plateMap.SetPlate(plate)
            wellsAndVals = []
            if table == p.image_table:
                group = True
                if aggMethod == 'average':
                    expression = "AVG(%s)"%(measurement)
                elif aggMethod == 'stdev':
                    expression = "STDDEV(%s)"%(measurement)
                elif aggMethod == 'cv%':
                    expression = "STDDEV(%s)/AVG(%s)*100"%(measurement, measurement)
                elif aggMethod == 'sum':
                    expression = "SUM(%s)"%(measurement)
                elif aggMethod == 'min':
                    expression = "MIN(%s)"%(measurement)
                elif aggMethod == 'max':
                    expression = "MAX(%s)"%(measurement)
                elif aggMethod == 'median':
                    expression = measurement
                    group = False

                wellsAndVals = db.Execute('SELECT %s, %s FROM %s WHERE %s="%s" %s'%
                                          (p.well_id, expression, table, 
                                           p.plate_id, plate,
                                           "GROUP BY %s"%(p.well_id) if group else ""))                   

                if aggMethod == 'median':
                    wellsAndVals = computeMedians(wellsAndVals)

                data += [FormatPlateMapData(wellsAndVals)]
                dmin = np.nanmin([float(val) for w,val in wellsAndVals]+[dmin])
                dmax = np.nanmax([float(val) for w,val in wellsAndVals]+[dmax])
            else:
                # For per-object data, we need to link the object table to the per image table
                # Here's an example query for sums:
                #  SELECT per_image.well, SUM(per_object.measurement) FROM per_image per_object
                #  WHERE per_image.ImageNumber=per_object.ImageNumber AND per_image.plate=plate
                #  GROUP BY Batch1_Per_Image.Image_Metadata_Well;
                
                join_clause = " AND ".join(["%s.%s=%s.%s"%(table, id, p.image_table, id) for id in image_key_columns()])
                where = join_clause + ' AND %s.%s="%s"'%(p.image_table, p.plate_id, plate)

                group = True
                if aggMethod == 'average':
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
                    expression = "%s.%s"%(table, measurement)
                    group = False

                wellsAndVals = db.Execute('SELECT %s FROM %s, %s WHERE %s %s'%
                                          (expression, 
                                           p.image_table, table, 
                                           where,
                                           'GROUP BY %s.%s'%(p.image_table, p.well_id) if group else ''))

                if aggMethod == 'median':
                    wellsAndVals = computeMedians(wellsAndVals)

                data += [FormatPlateMapData(wellsAndVals)]
                dmin = np.nanmin([float(val) for w,val in wellsAndVals]+[dmin])
                dmax = np.nanmax([float(val) for w,val in wellsAndVals]+[dmax])
                
        self.colorBar.SetExtents((dmin,dmax))
        
        for d, plateMap in zip(data, self.plateMaps):
            plateMap.SetData(d, range=(dmin,dmax))
        
        
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
        self.UpdatePlateMaps()
        
        
    def OnSelectPlate(self, evt):
        ''' Handles the selection of a plate from the plate choice box. '''
        self.UpdatePlateMaps()
        
        
    def OnSelectMeasurement(self, evt):
        ''' Handles the selection of a new measurement to plot from a choice box. '''
        self.UpdatePlateMaps()
        
        
    def OnSelectAggregationMethod(self, evt):
        ''' Handles the selection of an aggregation method from the choice box. '''
        self.UpdatePlateMaps()
        
        
    def OnSelectColorMap(self, evt):
        ''' Handles the selection of a new color map from a choice box. '''
        map = self.colorMapsChoice.GetStringSelection()
        cm = pylab.cm.get_cmap(map)
        
        self.colorBar.SetMap(map)
        for plateMap in self.plateMaps:
            plateMap.SetColorMap(map)
            
            
    def OnSelectNumberOfPlates(self, evt):
        ''' Handles the selection of predefined # of plates to view from a choice box. '''
        nPlates = int(self.numberOfPlatesChoice.GetStringSelection())
        # Record the indices of the plates currently selected.
        # Pad the list with 0's then crop to the new number of plates.
        currentPlates = [plateChoice.GetSelection() for plateChoice in self.plateMapChoices]
        currentPlates = (currentPlates+[0 for p in range(nPlates)])[:nPlates]
        # Remove all plateMaps
        self.plateMapSizer.Clear(deleteWindows=True)
        self.plateMaps = []
        self.plateMapChoices = []
        # Restructure the plateMapSizer appropriately
        if nPlates == 1:
            self.plateMapSizer.SetRows(1)
            self.plateMapSizer.SetCols(1)
        elif nPlates == 2:
            self.plateMapSizer.SetRows(2)
            self.plateMapSizer.SetCols(1)
        elif nPlates == 4:
            self.plateMapSizer.SetRows(2)
            self.plateMapSizer.SetCols(2)
        elif nPlates == 9:
            self.plateMapSizer.SetRows(3)
            self.plateMapSizer.SetCols(3)
        elif nPlates == 16:
            self.plateMapSizer.SetRows(4)
            self.plateMapSizer.SetCols(4)
        
        for plateIndex in currentPlates:
            self.AddPlateMap(plateIndex)
            
        self.plateMapSizer.Layout()



def FormatPlateMapData(wellsAndVals):
    '''
    wellsAndVals: a list of 2-tuples of wells and values
    returns a properly shaped numpy array of the given values with NaNs
            filling empty slots.  
    '''
    #TODO: well naming format may have to go in props file
    format = 'A01'
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
        print 'PlateMapBrowser requires a properties file.  Exiting.'
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

    dm.PopulateModel()

    pmb = PlateMapBrowser(None)
    pmb.Show()

    app.MainLoop()
