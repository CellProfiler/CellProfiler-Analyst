from cpatool import CPATool
from colorbarpanel import ColorBarPanel
from dbconnect import DBConnect, UniqueImageClause, UniqueWellClause, image_key_columns, GetWhereClauseForWells, well_key_columns
import dbconnect
import platemappanel as pmp
from datamodel import DataModel
from wx.combo import OwnerDrawnComboBox as ComboBox
import imagetools
import properties
import logging
import matplotlib.cm
import numpy as np
import os
import sys
import re
import wx


p = properties.Properties.getInstance()
# Hack the properties module so it doesn't require the object table.
properties.optional_vars += ['object_table']
db = DBConnect.getInstance()

P96   = (8, 12)
P384  = (16, 24)
P1536 = (32, 48)
P5600 = (40, 140)

NO_FILTER = 'No filter'
CREATE_NEW_FILTER = '*create new filter*'

required_fields = ['plate_type', 'plate_id', 'well_id']

ID_EXIT = wx.NewId()

class PlateViewer(wx.Frame, CPATool):
    def __init__(self, parent, size=(800,-1), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Plate Viewer', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)

        # Check for required properties fields.
        fail = False
        for field in required_fields:
            if not p.field_defined(field):
                fail = True
                raise 'Properties field "%s" is required for PlateViewer.'%(field)
        if fail:    
            self.Destroy()
            return

        assert (p.well_id is not None and p.plate_id is not None), \
               'Plate Viewer requires the well_id and plate_id columns to be defined in your properties file.'

        self.chMap = p.image_channel_colors[:]

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.loadCSVMenuItem = self.fileMenu.Append(-1, text='Load CSV\tCtrl+O', help='Load a CSV file storing per-image data')
        self.fileMenu.AppendSeparator()
        self.exitMenuItem = self.fileMenu.Append(id=ID_EXIT, text='Exit\tCtrl+Q',help='Close Plate Viewer')
        self.GetMenuBar().Append(self.fileMenu, 'File')

        self.Bind(wx.EVT_MENU, self.OnLoadCSV, self.loadCSVMenuItem)
        wx.EVT_MENU(self, ID_EXIT, lambda(_):self.Close())

        dataSourceSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Source:'), wx.VERTICAL)
        dataSourceSizer.Add(wx.StaticText(self, label='Data source:'))
        src_choices = [p.image_table]
        if p.object_table:
            src_choices += [p.object_table]
        self.sourceChoice = ComboBox(self, choices=src_choices, style=wx.CB_READONLY)
        try:
            for table in wx.GetApp().user_tables:
                self.AddTableChoice(table)
        except AttributeError:
            # running outside the main UI
            wx.GetApp().user_tables = []
        self.sourceChoice.Select(0)
        dataSourceSizer.Add(self.sourceChoice)
        dataSourceSizer.AddSpacer((-1,10))
        dataSourceSizer.Add(wx.StaticText(self, label='Measurement:'))
        measurements = get_non_blob_types_from_table(p.image_table)
        self.measurementsChoice = ComboBox(self, choices=measurements, style=wx.CB_READONLY)
        self.measurementsChoice.Select(0)
        dataSourceSizer.Add(self.measurementsChoice)
        dataSourceSizer.Add(wx.StaticText(self, label='Filter:'))
        self.filterChoice = ComboBox(self, choices=[NO_FILTER]+p._filters_ordered+[CREATE_NEW_FILTER], style=wx.CB_READONLY)
        self.filterChoice.Select(0)
        dataSourceSizer.Add(self.filterChoice)
        
        groupingSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Data aggregation:'), wx.VERTICAL)
        groupingSizer.Add(wx.StaticText(self, label='Aggregation method:'))
        aggregation = ['mean', 'sum', 'median', 'stdev', 'cv%', 'min', 'max']
        self.aggregationMethodsChoice = ComboBox(self, choices=aggregation, style=wx.CB_READONLY)
        self.aggregationMethodsChoice.Select(0)
        groupingSizer.Add(self.aggregationMethodsChoice)

        viewSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='View options:'), wx.VERTICAL)
        viewSizer.Add(wx.StaticText(self, label='Color map:'))
        maps = [m for m in matplotlib.cm.datad.keys() if not m.endswith("_r")]
        maps.sort()
        self.colorMapsChoice = ComboBox(self, choices=maps, style=wx.CB_READONLY)
        self.colorMapsChoice.SetSelection(maps.index('jet'))
        viewSizer.Add(self.colorMapsChoice)

        viewSizer.AddSpacer((-1,10))
        viewSizer.Add(wx.StaticText(self, label='Well display:'))
        if p.image_thumbnail_cols:
            choices = pmp.all_well_shapes
        else:
            choices = list(pmp.all_well_shapes)
            choices.remove(pmp.THUMBNAIL)
        self.wellDisplayChoice = ComboBox(self, choices=choices, style=wx.CB_READONLY)
        self.wellDisplayChoice.Select(0)
        viewSizer.Add(self.wellDisplayChoice)

        viewSizer.AddSpacer((-1,10))
        viewSizer.Add(wx.StaticText(self, label='Number of plates:'))
        self.numberOfPlatesTE = wx.TextCtrl(self, -1, '1', style=wx.TE_PROCESS_ENTER)
        viewSizer.Add(self.numberOfPlatesTE)

        annotationSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Annotation:'), wx.VERTICAL)
        annotationSizer.Add(wx.StaticText(self, label='Annotation column:'))
        annotationColSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.annotation_cols = dict([(col, db.GetColumnType(p.image_table, col)) 
                                     for col in db.GetUserColumnNames(p.image_table)])
        self.annotationCol = ComboBox(self, choices=self.annotation_cols.keys(), size=(120,-1), style=wx.CB_READONLY)
        if len(self.annotation_cols) > 0:
            self.annotationCol.SetSelection(0)
        annotationColSizer.Add(self.annotationCol)
        annotationColSizer.AddSpacer((10,-1))
        self.addAnnotationColBtn = wx.Button(self, -1, 'Add', size=(44,-1))
        annotationColSizer.Add(self.addAnnotationColBtn)
        annotationSizer.Add(annotationColSizer)
        annotationSizer.AddSpacer((-1,10))
        annotationSizer.Add(wx.StaticText(self, label='Label:'))
        self.annotationLabel = wx.TextCtrl(self, -1, 'Select wells')#, style=wx.TE_PROCESS_ENTER)
        self.annotationLabel.Disable()
        self.annotationLabel.SetForegroundColour(wx.Color(80,80,80))
        self.annotationLabel.SetBackgroundColour(wx.LIGHT_GREY)
        annotationSizer.Add(self.annotationLabel)
        annotationSizer.AddSpacer((-1,10))
        self.outlineMarked = wx.CheckBox(self, -1, label='Outline annotated wells')
        annotationSizer.Add(self.outlineMarked)
        annotationSizer.AddSpacer((-1,10))
        self.annotationShowVals = wx.CheckBox(self, -1, label='Show values on plate')
        annotationSizer.Add(self.annotationShowVals)
        if len(db.GetUserColumnNames(p.image_table)) == 0:
            self.outlineMarked.Disable()
            self.annotationShowVals.Disable()
            
        controlSizer = wx.BoxSizer(wx.VERTICAL)
        controlSizer.Add(dataSourceSizer, 0, wx.EXPAND)
        controlSizer.AddSpacer((-1,10))
        controlSizer.Add(groupingSizer, 0, wx.EXPAND)
        controlSizer.AddSpacer((-1,10))
        controlSizer.Add(viewSizer, 0, wx.EXPAND)
        controlSizer.AddSpacer((-1,10))
        controlSizer.Add(annotationSizer, 0 , wx.EXPAND)

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

        self.sourceChoice.Bind(wx.EVT_COMBOBOX, self.UpdateMeasurementChoice)
        self.measurementsChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectMeasurement)
        self.aggregationMethodsChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectAggregationMethod)
        self.colorMapsChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectColorMap)
        self.numberOfPlatesTE.Bind(wx.EVT_TEXT_ENTER, self.OnEnterNumberOfPlates)
        self.wellDisplayChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectWellDisplay)
        self.annotationCol.Bind(wx.EVT_COMBOBOX, self.OnSelectAnnotationCol)
        self.addAnnotationColBtn.Bind(wx.EVT_BUTTON, self.OnAddAnnotationCol)
        self.annotationLabel.Bind(wx.EVT_KEY_UP, self.OnEnterAnnotation)
        self.outlineMarked.Bind(wx.EVT_CHECKBOX, self.OnOutlineMarked)
        self.annotationShowVals.Bind(wx.EVT_CHECKBOX, self.OnShowAnotationValues)
        self.filterChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectFilter)
        
        global_extents = db.execute('SELECT MIN(%s), MAX(%s) FROM %s'%(
            self.measurementsChoice.Value, 
            self.measurementsChoice.Value, 
            self.sourceChoice.Value))[0]
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
            self.sourceChoice.SetStringSelection(countsTable)
            self.UpdateMeasurementChoice()

    def AddTableChoice(self, table):
        if table in self.sourceChoice.Strings:
            return
        if db.GetLinkingColumnsForTable(table) is None:
            wx.MessageDialog(self, 'Could not add table "%s" to PlateViewer '
                             'since it could not be linked to the per_image '
                             'table.'%(table), "Couldn't load table").ShowModal()
            return
        sel = self.sourceChoice.GetSelection()
        self.sourceChoice.SetItems(self.sourceChoice.GetItems()+[table])
        self.sourceChoice.Select(sel)

    def AddPlateMap(self, plateIndex=0):
        '''
        Adds a new blank plateMap to the PlateMapSizer.
        '''
        data = np.ones(int(p.plate_type))
        if p.plate_type == '384': shape = P384
        elif p.plate_type == '96': shape = P96
        elif p.plate_type == '5600': shape = P5600
        elif p.plate_type == '1536': shape = P1536

        # Try to get explicit labels for all wells.
        res = db.execute('SELECT DISTINCT %s FROM %s WHERE %s != "" and %s IS NOT NULL'%
                         (p.well_id, p.image_table, p.well_id, p.well_id))

        self.plateMapChoices += [ComboBox(self, choices=db.GetPlateNames(), 
                                          style=wx.CB_READONLY, size=(100,-1))]
        self.plateMapChoices[-1].Select(plateIndex)
        self.plateMapChoices[-1].Bind(wx.EVT_COMBOBOX, self.OnSelectPlate)

        plate_col_type = db.GetColumnType(p.image_table, p.plate_id)
        plate_id = plate_col_type(self.plateMapChoices[-1].GetString(plateIndex))
        well_keys = [(plate_id, r[0]) for r in res]

        platemap = pmp.PlateMapPanel(self, data, well_keys, shape,
                                     colormap = self.colorMapsChoice.Value,
                                     well_disp = self.wellDisplayChoice.Value)
        platemap.add_well_selection_handler(self.OnSelectWell)
        self.plateMaps += [platemap]

        plateMapChoiceSizer = wx.BoxSizer(wx.HORIZONTAL)
        plateMapChoiceSizer.Add(wx.StaticText(self, label='Plate:'), 0, wx.EXPAND)
        plateMapChoiceSizer.Add(self.plateMapChoices[-1])

        singlePlateMapSizer = wx.BoxSizer(wx.VERTICAL)
        singlePlateMapSizer.Add(plateMapChoiceSizer, 0, wx.ALIGN_CENTER)
        singlePlateMapSizer.Add(platemap, 1, wx.EXPAND|wx.ALIGN_CENTER)

        self.plateMapSizer.Add(singlePlateMapSizer, 1, wx.EXPAND|wx.ALIGN_CENTER)

    def UpdatePlateMaps(self):
        measurement = self.measurementsChoice.Value
        table       = self.sourceChoice.Value
        aggMethod   = self.aggregationMethodsChoice.Value

        categorical = measurement not in get_numeric_columns_from_table(table)
        fltr        = self.filterChoice.Value
        self.colorBar.ClearNotifyWindows()
        
        assert (db.GetLinkingColumnsForTable(table) is not None, 
            'Table "%s" could not be linked to the per_image table.'%(table))

        if not categorical:
            #
            # NUMERICAL DATA
            #
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
            elif aggMethod == 'none':
                expression = "(%s.%s)"%(table, measurement)

            if table == p.image_table:
                group = True
                if fltr == NO_FILTER:
                    from_clause = table
                else:
                    from_clause = '%s join _filter_%s using (%s)'%(
                        table, fltr, UniqueImageClause())
                platesWellsAndVals = db.execute(
                    'SELECT %s, %s FROM %s GROUP BY %s'%
                    (UniqueWellClause(), expression, from_clause, UniqueWellClause()))
            elif set(well_key_columns()) == set(db.GetLinkingColumnsForTable(table)):
                # For data from tables with well and plate columns, we simply
                # fetch the measurement without aggregating
                group = True
                if fltr == NO_FILTER:
                    from_clause = table
                else:
                    # HACK: splice the well key columns into the filter SELECT
                    f = p._filters[fltr]
                    ins = f.upper().index('FROM')
                    f = '%s, %s %s'%(f[:ins], UniqueWellClause(), f[ins:])
                    from_clause = '%s join (%s) as filter_SQL_%s using (%s)'%(
                        table, f, fltr, UniqueWellClause())
                platesWellsAndVals = db.execute(
                    'SELECT %s, %s FROM %s GROUP BY %s'%
                    (UniqueWellClause(), measurement, from_clause, UniqueWellClause()))
            else:
                # For data from other tables without well and plate columns, we 
                # need to link the table to the per image table via the 
                # ImageNumber column
                group = True
                if fltr == NO_FILTER:
                    from_clause = table
                else:
                    from_clause = '%s join (%s) as filter_SQL_%s using (%s)'%(
                        table, p._filters[fltr], fltr, UniqueImageClause())
                platesWellsAndVals = db.execute(
                    'SELECT %s, %s FROM %s, %s WHERE %s GROUP BY %s'%
                    (UniqueWellClause(p.image_table), expression, 
                     p.image_table, from_clause, 
                     ' AND '.join(['%s.%s=%s.%s'%(table, id, p.image_table, id) 
                                for id in db.GetLinkingColumnsForTable(table)]),
                     UniqueWellClause(p.image_table)))
            platesWellsAndVals = np.array(platesWellsAndVals, dtype=object)

            # Replace None's with nan
            for row in platesWellsAndVals:
                if row[2] is None:
                    row[2] = np.nan

            data = []
            dmax = -np.inf
            dmin = np.inf
            for plateChoice, plateMap in zip(self.plateMapChoices, self.plateMaps):
                plate = plateChoice.Value
                plateMap.SetPlate(plate)
                self.colorBar.AddNotifyWindow(plateMap)
                keys_and_vals = [v for v in platesWellsAndVals if str(v[0])==plate]
                platedata, platelabels = FormatPlateMapData(keys_and_vals)
                data += [platedata]
                dmin = np.nanmin([float(kv[-1]) for kv in keys_and_vals]+[dmin])
                dmax = np.nanmax([float(kv[-1]) for kv in keys_and_vals]+[dmax])

            # Compute the global extents if there is any data whatsoever
            if len(platesWellsAndVals) > 0:
                gmin = np.nanmin([float(val) for _,_,val in platesWellsAndVals])
                gmax = np.nanmax([float(val) for _,_,val in platesWellsAndVals])
                # Warn if there was no data for this plate
                if np.isinf(dmin) or np.isinf(dmax):
                    wx.MessageDialog(self, 'No numeric data was found in this '
                                     'column (%s.%s) for the selected plate (%s)%s'
                                     %(table, measurement, plate, 
                                       '.' if fltr == NO_FILTER else ' using filter "%s".'%(fltr)), 
                                     'No data!', style=wx.OK).ShowModal()
                    gmin = gmax = dmin = dmax = 1.
            else:
                gmin = gmax = 1.
                if fltr == NO_FILTER:
                    wx.MessageDialog(self, 'No numeric data was found in the '
                                     'database for this column (%s.%s).'
                                     %(table, measurement), 
                                     'No data!', style=wx.OK).ShowModal()
                else:
                    wx.MessageDialog(self, 'No numeric data was found in the '
                                     'database for this column (%s.%s) when '
                                     'using filter "%s".'
                                     %(table, measurement, fltr), 
                                     'No data!', style=wx.OK).ShowModal()


            self.colorBar.SetLocalExtents([dmin,dmax])
            self.colorBar.SetGlobalExtents([gmin,gmax])

        else:
            #
            # CATEGORICAL data
            #
            if table == p.image_table:
                if fltr == NO_FILTER:
                    from_clause = table
                else:
                    from_clause = '%s join (%s) as filter_SQL_%s using (%s)'%(table, p._filters[fltr], fltr, UniqueImageClause())
                platesWellsAndVals = db.execute('SELECT %s, %s FROM %s GROUP BY %s'%
                                                (UniqueWellClause(), measurement, 
                                                 from_clause, UniqueWellClause()))
            elif set(well_key_columns()) == set(db.GetLinkingColumnsForTable(table)):
                # For data from tables with well data
                group = True
                if fltr == NO_FILTER:
                    from_clause = table
                else:
                    # HACK: splice the well key columns into the filter SELECT
                    f = p._filters[fltr]
                    ins = f.upper().index('FROM')
                    f = '%s, %s %s'%(f[:ins], UniqueWellClause(), f[ins:])
                    from_clause = '%s join (%s) as filter_SQL_%s using (%s)'%(table, f, fltr, UniqueWellClause())
                platesWellsAndVals = db.execute(
                    'SELECT %s, %s FROM %s GROUP BY %s'%
                    (UniqueWellClause(), measurement, from_clause, UniqueWellClause()))
            else:
                # For data from other tables without well and plate columns, we 
                # need to link the table to the per image table via the 
                # ImageNumber column
                if fltr == NO_FILTER:
                    from_clause = table
                else:
                    from_clause = '%s join (%s) as filter_SQL_%s using (%s)'%(table, p._filters[fltr], fltr, UniqueImageClause())
                platesWellsAndVals = db.execute(
                    'SELECT %s, %s FROM %s, %s WHERE %s GROUP BY %s'%
                    (UniqueWellClause(p.image_table), measurement, 
                     p.image_table, from_clause, 
                     ' AND '.join(['%s.%s=%s.%s'%(table, id, p.image_table, id) for id in db.GetLinkingColumnsForTable(table)]),
                     UniqueWellClause()))

            data = []
            for plateChoice, plateMap in zip(self.plateMapChoices, self.plateMaps):
                plate = plateChoice.Value
                plateMap.SetPlate(plate)
                self.colorBar.AddNotifyWindow(plateMap)
                keys_and_vals = [v for v in platesWellsAndVals if str(v[0])==plate]
                platedata, platelabels = FormatPlateMapData(keys_and_vals, categorical=True)
                data += [platedata]

            self.colorBar.SetLocalExtents([0,1])
            self.colorBar.SetGlobalExtents([0,1])

        for d, plateMap in zip(data, self.plateMaps):
            if categorical:
                plateMap.SetData(np.ones(d.shape) * np.nan)
                plateMap.SetTextData(d)
            else:
                plateMap.SetData(d, data_range=self.colorBar.GetLocalExtents(), 
                                 clip_interval=self.colorBar.GetLocalInterval(), 
                                 clip_mode=self.colorBar.GetClipMode())

    def UpdateMeasurementChoice(self, evt=None):
        '''
        Handles the selection of a source table (per-image or per-object) from
        a choice box.  The measurement choice box is populated with the names
        of numeric columns from the selected table.
        '''
        table = self.sourceChoice.Value
        self.measurementsChoice.SetItems(get_non_blob_types_from_table(table))
        self.measurementsChoice.Select(0)
        if db.GetLinkingColumnsForTable(table) == well_key_columns():
            self.aggregationMethodsChoice.Disable()
            self.aggregationMethodsChoice.SetValue('none')
        else:
            self.aggregationMethodsChoice.Enable()
            self.aggregationMethodsChoice.SetSelection(0)

        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()

    def OnSelectPlate(self, evt):
        ''' Handles the selection of a plate from the plate choice box. '''
        self.UpdatePlateMaps()

    def OnSelectMeasurement(self, evt=None):
        ''' Handles the selection of a measurement to plot from a choice box. '''
        selected_measurement = self.measurementsChoice.Value 
        table = self.sourceChoice.Value
        numeric_measurements = get_numeric_columns_from_table(table)
        if (selected_measurement in numeric_measurements):
            if (set(well_key_columns()) != set(db.GetLinkingColumnsForTable(self.sourceChoice.Value))):
                self.aggregationMethodsChoice.Enable()
            self.colorMapsChoice.Enable()
        else:
            self.aggregationMethodsChoice.Disable()
            self.colorMapsChoice.Disable()
        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()

    def OnSelectAggregationMethod(self, evt=None):
        ''' Handles the selection of an aggregation method from the choice box. '''
        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()

    def OnSelectColorMap(self, evt=None):
        ''' Handles the selection of a color map from a choice box. '''
        map = self.colorMapsChoice.Value
        cm = matplotlib.cm.get_cmap(map)

        self.colorBar.SetMap(map)
        for plateMap in self.plateMaps:
            plateMap.SetColorMap(map)

    def OnSelectWellDisplay(self, evt=None):
        ''' Handles the selection of a well display choice from a choice box. '''
        sel = self.wellDisplayChoice.Value
        if sel.lower() == 'image':
            dlg = wx.MessageDialog(self, 
                'This mode will render each well as a shrunken image loaded '
                'from that well. This feature is currently VERY SLOW since it '
                'requires loading hundreds of full sized images. Are you sure '
                'you want to continue?',
                'Load all images?', wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            if dlg.ShowModal() != wx.ID_OK:
                self.wellDisplayChoice.SetSelection(0)
                return
        for platemap in self.plateMaps:
            platemap.SetWellDisplay(sel)

    def OnEnterNumberOfPlates(self, evt=None):
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
        currentPlates = (currentPlates+[(currentPlates[-1]+1+p) % len(db.GetPlateNames()) for p in range(nPlates)])[:nPlates]
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
        # Update outlines
        self.OnOutlineMarked()
        
    def OnSelectWell(self):
        '''When wells are selected: display their annotation in the annotation
        label control. If multiple annotations are found then make sure the
        user knows.
        '''
        wellkeys = []
        for pm in self.plateMaps:
            wellkeys += pm.get_selected_well_keys()
        if len(wellkeys) > 0 and self.annotationCol.Value != '':
            self.annotationLabel.Enable()
            self.annotationLabel.SetForegroundColour(wx.BLACK)
            self.annotationLabel.SetBackgroundColour(wx.WHITE)
            annotations = db.execute('SELECT %s FROM %s WHERE "%s"'%(
                                self.annotationCol.Value, 
                                p.image_table, 
                                GetWhereClauseForWells(wellkeys)))
            annotations = list(set([a[0] for a in annotations]))
            if len(annotations) == 1:
                if annotations[0] == None:
                    self.annotationLabel.SetValue('')
                else:
                    self.annotationLabel.SetValue(str(annotations[0]))
            else:
                self.annotationLabel.SetValue(','.join([a for a in annotations if a is not None]))
        else:
            self.annotationLabel.Disable()
            self.annotationLabel.SetForegroundColour(wx.Color(80,80,80))
            self.annotationLabel.SetBackgroundColour(wx.LIGHT_GREY)
            self.annotationLabel.SetValue('Select wells')
                
    def OnAddAnnotationCol(self, evt):
        '''Add a new user annotation column to the database.
        '''
        dlg = wx.TextEntryDialog(self, 'New annotation column name: User_','Add Annotation Column')
        if dlg.ShowModal() != wx.ID_OK:
            return
        new_column = 'User_'+dlg.GetValue()
        # user-type ==> (sql-type, python-type)
        coltypes = {'Text'   : ('VARCHAR(255)', str), 
                    'Number' : ('FLOAT', float)}
        dlg = wx.SingleChoiceDialog(self, 
                'What type of annotation column would you like to add?\nThis can not be changed.',
                'Add Annotation Column', coltypes.keys(), wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() != wx.ID_OK:
            return
        usertype = dlg.GetStringSelection()
        db.AppendColumn(p.image_table, new_column, coltypes[usertype][0])
        self.annotation_cols[new_column] = coltypes[usertype][1]
        self.annotationCol.Items += [new_column]
        self.annotationCol.SetSelection(len(self.annotation_cols) - 1)
        self.measurementsChoice.SetItems(self.measurementsChoice.Strings + [new_column])
        if self.annotationShowVals.IsChecked():
            column = self.annotationCol.Value
            self.sourceChoice.SetStringSelection(p.image_table)
            self.measurementsChoice.SetStringSelection(column)
            self.UpdatePlateMaps()
        self.annotationShowVals.Enable()
        self.outlineMarked.Enable()
        self.OnSelectWell()
        
    def OnSelectAnnotationCol(self, evt=None):
        '''Handles selection of an annotation column.
        '''
        col = self.annotationCol.Value
        if col == '':
            return
        coltype = self.annotation_cols[col]
        self.OnSelectWell()
        self.OnOutlineMarked()
        if self.annotationShowVals.IsChecked():
            if coltype != str:
                self.colorMapsChoice.Enable()
            else:
                self.colorMapsChoice.Disable()
            self.measurementsChoice.SetStringSelection(col)
            self.UpdatePlateMaps()
        
    def OnEnterAnnotation(self, evt=None):
        '''Store the annotation value in the annotation column of the db.
        '''
        if evt.KeyCode < 32 or evt.KeyCode > 127:
            return
        column = self.annotationCol.Value
        value = self.annotationLabel.Value
        wellkeys = []
        for pm in self.plateMaps:
            wellkeys += pm.get_selected_well_keys()
        if value == '':
            value = None
        elif self.annotation_cols[column] == float:
            try:
                value = float(value)
                self.annotationLabel.SetForegroundColour(wx.BLACK)
            except:
                self.annotationLabel.SetForegroundColour(wx.Color(255,0,0))
                return
        db.UpdateWells(p.image_table, column, value, wellkeys)
        if self.outlineMarked.IsChecked():
            for pm in self.plateMaps:
                if value is None:
                    pm.UnOutlineWells(wellkeys)
                else:
                    pm.OutlineWells(wellkeys)
        if (self.sourceChoice.Value == p.image_table and 
            self.measurementsChoice.Value == column):
            self.UpdatePlateMaps()

    def OnOutlineMarked(self, evt=None):
        '''Outlines all non-NULL values of the current annotation
        '''
        # Disable filters when outlining marked wells
        if self.outlineMarked.IsChecked():
            self.filterChoice.SetStringSelection(NO_FILTER)
            self.filterChoice.Disable()
        else:
            if not self.annotationShowVals.IsChecked():
                self.filterChoice.Enable()
        # Update outlined wells in PlateMapPanels
        for pm in self.plateMaps:
            if self.outlineMarked.IsChecked():
                column = self.annotationCol.Value
                res = db.execute('SELECT %s, %s FROM %s WHERE %s=%s'%(
                    ','.join(well_key_columns()), column, p.image_table, 
                    p.plate_id, pm.plate))
                keys = [tuple(r[:-1]) for r in res if r[-1] is not None]
                pm.SetOutlinedWells(keys)
            else:
                pm.SetOutlinedWells([])
        self.UpdatePlateMaps()
                
    def OnShowAnotationValues(self, evt=None):
        '''Handler for the show values checkbox.
        '''
        if self.annotationShowVals.IsChecked():
            column = self.annotationCol.Value
            self.sourceChoice.SetStringSelection(p.image_table)
            self.measurementsChoice.SetItems(get_non_blob_types_from_table(p.image_table))            
            self.measurementsChoice.SetStringSelection(column)
            self.filterChoice.SetStringSelection(NO_FILTER)
            self.sourceChoice.Disable()
            self.measurementsChoice.Disable()
            self.filterChoice.Disable()
            self.aggregationMethodsChoice.Disable()
            self.aggregationMethodsChoice.SetValue('none')
        else:
            self.sourceChoice.Enable()
            self.measurementsChoice.Enable()
            if not self.outlineMarked.IsChecked():
                self.filterChoice.Enable()
            if db.GetColumnType(self.sourceChoice.Value, self.measurementsChoice.Value) != str:
                self.aggregationMethodsChoice.Enable()
                self.aggregationMethodsChoice.SetSelection(0)
        self.UpdatePlateMaps()
        
    def OnSelectFilter(self, evt):
        f = self.filterChoice.Value
        if f == CREATE_NEW_FILTER:
            from columnfilter import ColumnFilterDialog
            cff = ColumnFilterDialog(self, tables=[p.image_table], size=(600,150))
            if cff.ShowModal()==wx.OK:
                fltr = str(cff.get_filter())
                fname = str(cff.get_filter_name())
                p._filters_ordered += [fname]
                p._filters[fname] = fltr
                items = self.filterChoice.GetItems()
                self.filterChoice.SetItems(items[:-1]+[fname]+items[-1:])
                self.filterChoice.SetSelection(len(items)-1)
                from multiclasssql import CreateFilterTable
                logging.info('Creating filter table...')
                CreateFilterTable(fname)
                logging.info('Done creating filter.')
            else:
                self.filterChoice.SetStringSelection(NO_FILTER)
            cff.Destroy()
        self.UpdatePlateMaps()
        
    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        
        returns a dictionary mapping setting names to values encoded as strings
        '''
        settings = {'table' : self.sourceChoice.Value,
                    'measurement' : self.measurementsChoice.Value,
                    'aggregation' : self.aggregationMethodsChoice.Value,
                    'colormap' : self.colorMapsChoice.Value,
                    'well display' : self.wellDisplayChoice.Value,
                    'number of plates' : self.numberOfPlatesTE.GetValue(),
                    }
        for i, choice in enumerate(self.plateMapChoices):
            settings['plate %d'%(i+1)] = choice.Value
        return settings
    
    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
        if 'table' in settings:
            self.sourceChoice.SetStringSelection(settings['table'])
            self.UpdateMeasurementChoice()
        if 'measurement' in settings:
            self.measurementsChoice.SetStringSelection(settings['measurement'])
            self.OnSelectMeasurement()
        if 'aggregation' in settings:
            self.aggregationMethodsChoice.SetStringSelection(settings['aggregation'])
            self.OnSelectAggregationMethod()
        if 'colormap' in settings:
            self.colorMapsChoice.SetStringSelection(settings['colormap'])
            self.OnSelectColorMap()
        if 'number of plates' in settings:
            self.numberOfPlatesTE.SetValue(settings['number of plates'])
            self.OnEnterNumberOfPlates()
        for s, v in settings.items():
            if s.startswith('plate '):
                self.plateMapChoices[int(s.strip('plate ')) - 1].SetValue(v)
        # set well display last since each step currently causes a redraw and
        # this could take a long time if they are displaying images
        if 'well display' in settings:
            self.wellDisplayChoice.SetStringSelection(settings['well display'])
            self.OnSelectWellDisplay()

            
def FormatPlateMapData(keys_and_vals, categorical=False):
    '''
    wellsAndVals: a list of lists of plates, wells and values
    returns a 2-tuple containing:
       -an array in the shape of the plate containing the given values with NaNs filling empty slots.  
       -an array in the shape of the plate containing the given keys with (unknownplate, unknownwell) filling empty slots
    '''

    if   p.plate_type == '96':   shape = P96
    elif p.plate_type == '384':  shape = P384
    elif p.plate_type == '1536': shape = P1536
    elif p.plate_type == '5600': 
        shape = P5600
        data = np.array(keys_and_vals)[:,-1]
        well_keys = np.array(keys_and_vals)[:,:-1]
        assert data.ndim == 1
        if len(data) < 5600: raise Exception(
            '''The measurement you chose to plot was missing for some wells. 
            Because CPA doesn't know the well labelling convention used by this
            microarray, we can't be sure how to plot the data. If you are 
            plotting an object measurement, you probably have no objects in 
            some of your wells.''')
        assert len(data) == 5600
        data = np.array(list(meander(data.reshape(shape)))).reshape(shape)
        well_keys = np.array(list(meander(well_keys.reshape(shape + (2,))))).reshape(shape + (2,))
        return data, well_keys

    data = np.ones(shape) * np.nan
    if categorical:
        data = data.astype('object')
    well_keys = np.array([('UnknownPlate', 'UnknownWell')] * np.prod(shape), 
                         dtype=object).reshape(shape + (2,))
    for plate, well, val in keys_and_vals:
        dm = DataModel.getInstance()
        (row, col) = dm.get_well_position_from_name(well)
        data[(row, col)] = val
        well_keys[row, col] = (plate, well)
    return data, well_keys

def meander(a):
    ''' a - 2D array
    returns cells from the array starting at 0,0 and meandering 
    left-to-right on even rows and right-to-left on odd rows'''
    for i, row in enumerate(a):
        if i % 2 ==0:
            for val in row:
                yield val
        else:        
            for val in reversed(row):
                yield val

def get_numeric_columns_from_table(table):
    ''' Fetches names of numeric columns for the given table. '''
    measurements = db.GetColumnNames(table)
    types = db.GetColumnTypes(table)
    return [m for m,t in zip(measurements, types) if t in [float, int, long]]

def get_non_blob_types_from_table(table):
    measurements = db.GetColumnNames(table)
    types = db.GetColumnTypeStrings(table)
    return [m for m,t in zip(measurements, types) if not 'blob' in t.lower()]

if __name__ == "__main__":
    app = wx.PySimpleApp()

    logging.basicConfig(level=logging.DEBUG)

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            print 'Plate Viewer requires a properties file.  Exiting.'
            # necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()

#        p.LoadFile('../properties/2009_02_19_MijungKwon_Centrosomes.properties')
#        p.LoadFile('../properties/Gilliland_LeukemiaScreens_Validation.properties')

    pmb = PlateViewer(None)
    pmb.Show()

    app.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import cellprofiler.utilities.jutil as jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
