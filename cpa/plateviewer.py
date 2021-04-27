
from .cpatool import CPATool
from .colorbarpanel import ColorBarPanel
from .dbconnect import DBConnect, UniqueImageClause, UniqueWellClause, image_key_columns, GetWhereClauseForWells, well_key_columns
from . import dbconnect
from . import sqltools as sql
from . import platemappanel as pmp
from .datamodel import DataModel
from .guiutils import TableComboBox, FilterComboBox, get_other_table_from_user
from wx.adv import OwnerDrawnComboBox as ComboBox
from . import imagetools
from . import properties
import logging
import matplotlib.cm
import numpy as np
from itertools import groupby
import os
import sys
import re
import wx
import cpa.helpmenu
import csv

p = properties.Properties()
# Hack the properties module so it doesn't require the object table.
properties.optional_vars += ['object_table']
db = DBConnect()

required_fields = ['plate_shape', 'well_id']

fixed_width = (200,-1)

class PlateViewer(wx.Frame, CPATool):
    def __init__(self, parent, size=(800,-1), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Plate Viewer', **kwargs)
        CPATool.__init__(self)
        self.SetName(self.tool_name)
        self.SetBackgroundColour("white") # Fixing the color

        # Check for required properties fields.
        fail = False
        for field in required_fields:
            if not p.field_defined(field):
                fail = True
                raise Exception('Properties field "%s" is required for PlateViewer.'%(field))
        if fail:    
            self.Destroy()
            return

        self.chMap = p.image_channel_colors[:]

        self.menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar)
        self.fileMenu = wx.Menu()
        self.exitMenuItem = self.fileMenu.Append(id=wx.ID_EXIT, item='Exit\tCtrl+Q', helpString='Close Plate Viewer')
        self.GetMenuBar().Append(self.fileMenu, 'File')
        self.menuBar.Append(cpa.helpmenu.make_help_menu(self, manual_url="8_plate_viewer.html"), 'Help')
        save_csv_menu_item = self.fileMenu.Append(-1, 'Save table to CSV\tCtrl+S')
        self.Bind(wx.EVT_MENU, self.on_save_csv, save_csv_menu_item)
        
        self.Bind(wx.EVT_MENU, lambda _:self.Close(), id=wx.ID_EXIT)

        dataSourceSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Source:'), wx.VERTICAL)
        dataSourceSizer.Add(wx.StaticText(self, label='Data source:'))
        self.sourceChoice = TableComboBox(self, -1, size=fixed_width)
        dataSourceSizer.Add(self.sourceChoice)
        dataSourceSizer.Add(-1, 3, 0)
        dataSourceSizer.Add(wx.StaticText(self, label='Measurement:'))
        measurements = get_non_blob_types_from_table(p.image_table)
        self.measurementsChoice = ComboBox(self, choices=measurements, size=fixed_width, style=wx.CB_READONLY)
        self.measurementsChoice.Select(0)
        dataSourceSizer.Add(self.measurementsChoice)
        dataSourceSizer.Add(wx.StaticText(self, label='Filter:'))
        self.filterChoice = FilterComboBox(self, size=fixed_width, style=wx.CB_READONLY)
        dataSourceSizer.Add(self.filterChoice)
        
        groupingSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Data aggregation:'), wx.VERTICAL)
        groupingSizer.Add(wx.StaticText(self, label='Aggregation method:'))
        aggregation = ['mean', 'sum', 'median', 'stdev', 'cv%', 'min', 'max']
        self.aggregationMethodsChoice = ComboBox(self, choices=aggregation, size=fixed_width)
        self.aggregationMethodsChoice.Select(0)
        groupingSizer.Add(self.aggregationMethodsChoice)

        viewSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='View options:'), wx.VERTICAL)
        viewSizer.Add(wx.StaticText(self, label='Color map:'))
        maps = [m for m in list(matplotlib.cm.datad.keys()) if not m.endswith("_r")]
        maps.sort()
        self.colorMapsChoice = ComboBox(self, choices=maps, size=fixed_width)
        self.colorMapsChoice.SetSelection(maps.index('jet'))
        viewSizer.Add(self.colorMapsChoice)

        viewSizer.Add(-1, 3, 0)
        viewSizer.Add(wx.StaticText(self, label='Well display:'))
        if p.image_thumbnail_cols:
            choices = pmp.all_well_shapes
        else:
            choices = list(pmp.all_well_shapes)
            choices.remove(pmp.THUMBNAIL)
        self.wellDisplayChoice = ComboBox(self, choices=choices, size=fixed_width)
        self.wellDisplayChoice.Select(0)
        viewSizer.Add(self.wellDisplayChoice)

        viewSizer.Add(-1, 3, 0)
        viewSizer.Add(wx.StaticText(self, label='Number of plates:'))
        self.numberOfPlatesTE = wx.TextCtrl(self, -1, '1', style=wx.TE_PROCESS_ENTER)
        viewSizer.Add(self.numberOfPlatesTE)
        if not p.plate_id:
            self.numberOfPlatesTE.Disable()

        annotationSizer = wx.StaticBoxSizer(wx.StaticBox(self, label='Annotation:'), wx.VERTICAL)
        annotationSizer.Add(wx.StaticText(self, label='Annotation column:'))
        annotationColSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.annotation_cols = dict([(col, db.GetColumnType(p.image_table, col)) 
                                     for col in db.GetUserColumnNames(p.image_table)])
        self.annotationCol = ComboBox(self, choices=list(self.annotation_cols.keys()), size=(120,-1))
        if len(self.annotation_cols) > 0:
            self.annotationCol.SetSelection(0)
        annotationColSizer.Add(self.annotationCol, flag=wx.ALIGN_CENTER_VERTICAL)
        annotationColSizer.AddSpacer(3)
        self.addAnnotationColBtn = wx.Button(self, -1, 'Add', size=(44,-1))
        annotationColSizer.Add(self.addAnnotationColBtn, flag=wx.ALIGN_CENTER_VERTICAL)
        annotationSizer.Add(annotationColSizer)
        annotationSizer.Add(-1, 3, 0)
        annotationSizer.Add(wx.StaticText(self, label='Label:'))
        self.annotationLabel = wx.TextCtrl(self, -1, 'Select wells')#, style=wx.TE_PROCESS_ENTER)
        self.annotationLabel.Disable()
        self.annotationLabel.SetForegroundColour(wx.Colour(80,80,80))
        self.annotationLabel.SetBackgroundColour(wx.LIGHT_GREY)
        annotationSizer.Add(self.annotationLabel)
        annotationSizer.Add(-1, 3, 0)
        self.outlineMarked = wx.CheckBox(self, -1, label='Outline annotated wells')
        annotationSizer.Add(self.outlineMarked)
        annotationSizer.Add(-1, 3, 0)
        self.annotationShowVals = wx.CheckBox(self, -1, label='Show values on plate')
        annotationSizer.Add(self.annotationShowVals)
        if len(db.GetUserColumnNames(p.image_table)) == 0:
            self.outlineMarked.Disable()
            self.annotationShowVals.Disable()
            
        controlSizer = wx.BoxSizer(wx.VERTICAL)
        controlSizer.Add(dataSourceSizer, 0, wx.EXPAND)
        controlSizer.Add(-1, 3, 0)
        controlSizer.Add(groupingSizer, 0, wx.EXPAND)
        controlSizer.Add(-1, 3, 0)
        controlSizer.Add(viewSizer, 0, wx.EXPAND)
        controlSizer.Add(-1, 3, 0)
        controlSizer.Add(annotationSizer, 0 , wx.EXPAND)

        self.plateMapSizer = wx.GridSizer(1,1,5,5)
        self.plateMaps = []
        self.plateMapChoices = []

        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightSizer.Add(self.plateMapSizer, 1, wx.EXPAND|wx.BOTTOM, 10)
        self.colorBar = ColorBarPanel(self, 'jet', size=(-1,25))
        self.rightSizer.Add(self.colorBar, 0, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(controlSizer, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 10)
        mainSizer.Add(self.rightSizer, 1, wx.EXPAND|wx.ALL, 10)

        self.SetSizer(mainSizer)
        self.SetClientSize((self.Size[0],self.Sizer.CalcMin()[1]))

        self.sourceChoice.Bind(wx.EVT_COMBOBOX, self.UpdateMeasurementChoice)
        self.measurementsChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectMeasurement)
        self.measurementsChoice.Select(0)
        self.aggregationMethodsChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectAggregationMethod)
        self.colorMapsChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectColorMap)
        self.numberOfPlatesTE.Bind(wx.EVT_TEXT_ENTER, self.OnEnterNumberOfPlates)
        self.wellDisplayChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectWellDisplay)
        self.annotationCol.Bind(wx.EVT_COMBOBOX, self.OnSelectAnnotationCol)
        self.addAnnotationColBtn.Bind(wx.EVT_BUTTON, self.OnAddAnnotationCol)
        self.annotationLabel.Bind(wx.EVT_KEY_UP, self.OnEnterAnnotation)
        self.outlineMarked.Bind(wx.EVT_CHECKBOX, self.OnOutlineMarked)
        self.annotationShowVals.Bind(wx.EVT_CHECKBOX, self.OnShowAnnotationValues)
        self.filterChoice.Bind(wx.EVT_COMBOBOX, self.OnSelectFilter)

        self.AddPlateMap()
        self.OnSelectMeasurement()


    def AddPlateMap(self, plateIndex=0):
        '''
        Adds a new blank plateMap to the PlateMapSizer.
        '''
        data = np.ones(p.plate_shape)

        # Try to get explicit labels for all wells.
        res = db.execute('SELECT DISTINCT %s FROM %s WHERE %s != "" and %s IS NOT NULL'%
                         (dbconnect.UniqueWellClause(), p.image_table, p.well_id, p.well_id))

        if p.plate_id:
            self.plateMapChoices += [ComboBox(self, choices=db.GetPlateNames(), size=(400,-1))]
            self.plateMapChoices[-1].Select(plateIndex)
            self.plateMapChoices[-1].Bind(wx.EVT_COMBOBOX, self.OnSelectPlate)
    
            #plate_col_type = db.GetColumnType(p.image_table, p.plate_id)
            #plate_id = plate_col_type(self.plateMapChoices[-1].GetString(plateIndex))
            
            plateMapChoiceSizer = wx.BoxSizer(wx.HORIZONTAL)
            plateMapChoiceSizer.Add(wx.StaticText(self, label='Plate:'), flag=wx.ALIGN_CENTER_VERTICAL)
            plateMapChoiceSizer.Add(self.plateMapChoices[-1], flag=wx.ALIGN_CENTER_VERTICAL)
        well_keys = res

        platemap = pmp.PlateMapPanel(self, data, well_keys, p.plate_shape,
                                     colormap = self.colorMapsChoice.Value,
                                     well_disp = self.wellDisplayChoice.Value)
        platemap.add_well_selection_handler(self.OnSelectWell)
        self.plateMaps += [platemap]

        singlePlateMapSizer = wx.BoxSizer(wx.VERTICAL)
        if p.plate_id:
            singlePlateMapSizer.Add(plateMapChoiceSizer, 0, wx.ALIGN_CENTER)
        singlePlateMapSizer.Add(platemap, 1, wx.EXPAND)

        self.plateMapSizer.Add(singlePlateMapSizer, 1, wx.EXPAND)

    def UpdatePlateMaps(self):
        self.measurement = self.measurementsChoice.Value
        measurement = self.measurement
        table       = self.sourceChoice.Value
        self.aggMethod   = self.aggregationMethodsChoice.Value
        categorical = measurement not in get_numeric_columns_from_table(table)
        fltr        = self.filterChoice.Value
        self.colorBar.ClearNotifyWindows()

        q = sql.QueryBuilder()
        well_key_cols = [sql.Column(p.image_table, col) for col in well_key_columns()]
        select = list(well_key_cols)
        if not categorical:
            if self.aggMethod=='mean':
                select += [sql.Column(table, measurement, 'AVG')]
            elif self.aggMethod=='stdev':
                select += [sql.Column(table, measurement, 'STDDEV')]
            elif self.aggMethod=='cv%':
                # stddev(col) / avg(col) * 100
                select += [sql.Expression(
                              sql.Column(table, measurement, 'STDDEV'), ' / ',
                              sql.Column(table, measurement, 'AVG'), ' * 100')]
            elif self.aggMethod=='sum':
                select += [sql.Column(table, measurement, 'SUM')]
            elif self.aggMethod=='min':
                select += [sql.Column(table, measurement, 'MIN')]
            elif self.aggMethod=='max':
                select += [sql.Column(table, measurement, 'MAX')]
            elif self.aggMethod=='median':
                select += [sql.Column(table, measurement, 'MEDIAN')]
            elif self.aggMethod=='none':
                select += [sql.Column(table, measurement)]
        else:
            select += [sql.Column(table, measurement)]
        
        q.set_select_clause(select)
        q.set_group_columns(well_key_cols)
        if fltr not in (FilterComboBox.NO_FILTER, FilterComboBox.NEW_FILTER, ''):
            if fltr in p._filters:
                q.add_filter(p._filters[fltr])
            elif fltr in p.gates:
                q.add_filter(p.gates[fltr].as_filter())
            else:
                raise Exception('Could not find filter "%s" in gates or filters'%(fltr))
        wellkeys_and_values = db.execute(str(q))
        wellkeys_and_values = np.array(wellkeys_and_values, dtype=object)

        # Replace measurement None's with nan
        for row in wellkeys_and_values:
            if row[-1] is None:
                row[-1] = np.nan

        data = []
        key_lists = []
        dmax = -np.inf
        dmin = np.inf
        if p.plate_id:
            for plateChoice, plateMap in zip(self.plateMapChoices, self.plateMaps):
                plate = plateChoice.Value
                plateMap.SetPlate(plate)
                self.colorBar.AddNotifyWindow(plateMap)
                self.keys_and_vals = [v for v in wellkeys_and_values if str(v[0])==plate]
                platedata, wellkeys, ignore = FormatPlateMapData(self.keys_and_vals, categorical)
                data += [platedata]
                key_lists += [wellkeys]
                if not categorical:
                    dmin = np.nanmin([float(kv[-1]) for kv in self.keys_and_vals]+[dmin])
                    dmax = np.nanmax([float(kv[-1]) for kv in self.keys_and_vals]+[dmax])
        else:
            self.colorBar.AddNotifyWindow(self.plateMaps[0])
            platedata, wellkeys, ignore = FormatPlateMapData(wellkeys_and_values, categorical)
            data += [platedata]
            key_lists += [wellkeys]
            if not categorical:
                dmin = np.nanmin([float(kv[-1]) for kv in wellkeys_and_values])
                dmax = np.nanmax([float(kv[-1]) for kv in wellkeys_and_values])
            
        if not categorical:
            if len(wellkeys_and_values) > 0:
                # Compute the global extents if there is any data whatsoever
                gmin = np.nanmin([float(vals[-1]) for vals in wellkeys_and_values])
                gmax = np.nanmax([float(vals[-1]) for vals in wellkeys_and_values])
                if np.isinf(dmin) or np.isinf(dmax):
                    gmin = gmax = dmin = dmax = 1.
                    # Warn if there was no data for this plate (and no filter was used)
                    if fltr == FilterComboBox.NO_FILTER:
                        wx.MessageBox('No numeric data was found in "%s.%s" for plate "%s"'
                                      %(table, measurement, plate), 'Warning')
            else:
                gmin = gmax = 1.
                if fltr == FilterComboBox.NO_FILTER:
                    wx.MessageBox('No numeric data was found in %s.%s'
                                  %(table, measurement), 'Warning')

        if categorical:
            self.colorBar.Hide()
        else:
            self.colorBar.Show()
            self.colorBar.SetLocalExtents([dmin,dmax])
            self.colorBar.SetGlobalExtents([gmin,gmax])
        self.rightSizer.Layout()

        for keys, d, plateMap in zip(key_lists, data, self.plateMaps):
            plateMap.SetWellKeys(keys)
            if categorical:
                plateMap.SetData(np.ones(d.shape) * np.nan)
                plateMap.SetTextData(d)
            else:
                plateMap.SetData(d, data_range=self.colorBar.GetLocalExtents(), 
                                 clip_interval=self.colorBar.GetLocalInterval(), 
                                 clip_mode=self.colorBar.GetClipMode())

        for keys, d, plateMap in zip(key_lists, data, self.plateMaps):
            plateMap.SetWellKeys(keys)
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
        if table == TableComboBox.OTHER_TABLE:
            t = get_other_table_from_user(self)
            if t is not None:
                self.sourceChoice.Items = self.sourceChoice.Items[:-1] + [t] + self.sourceChoice.Items[-1:]
                self.sourceChoice.Select(self.sourceChoice.Items.index(t))
                table = t
            else:
                self.sourceChoice.Select(0)
                return
        self.measurementsChoice.SetItems(get_non_blob_types_from_table(table))
        self.measurementsChoice.Select(0)
        self.colorBar.ResetInterval()
        self.UpdatePlateMaps()

    def on_save_csv(self, evt):
        defaultFileName = 'my_plate_table.csv'
        saveDialog = wx.FileDialog(self, message="Save as:",
                                   defaultDir=os.getcwd(),
                                   defaultFile=defaultFileName,
                                   wildcard='csv|*',
                                   style=(wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT |
                                          wx.FD_CHANGE_DIR))
        if saveDialog.ShowModal() == wx.ID_OK:
            filename = saveDialog.GetPath()
            self.save_to_csv(filename)
            self.Title = filename
        saveDialog.Destroy()

    def save_to_csv(self, filename):
        with open(filename, 'w', newline="") as f:
            w = csv.writer(f)
            w.writerow(['Plate', 'Well', self.measurement + ' ' + self.aggMethod])
            w.writerows(self.keys_and_vals)

        logging.info('Table saved to %s'%filename)

    def OnSelectPlate(self, evt):
        ''' Handles the selection of a plate from the plate choice box. '''
        self.UpdatePlateMaps()

    def OnSelectMeasurement(self, evt=None):
        ''' Handles the selection of a measurement to plot from a choice box. '''
        selected_measurement = self.measurementsChoice.Value 
        table = self.sourceChoice.Value
        numeric_measurements = get_numeric_columns_from_table(table)
        if (selected_measurement in numeric_measurements):
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
        if sel.lower() in ['image', 'thumbnail']:
            self.colorBar.Hide()
        else:
            self.colorBar.Show()
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
        self.plateMapSizer.Clear(delete_windows=True)
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
            annotations = db.execute('SELECT %s FROM %s WHERE %s'%(
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
                self.annotationLabel.SetValue(','.join([str(a) for a in annotations if a is not None]))
        else:
            self.annotationLabel.Disable()
            self.annotationLabel.SetForegroundColour(wx.Colour(80,80,80))
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
                'Add Annotation Column', list(coltypes.keys()), wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() != wx.ID_OK:
            return
        usertype = dlg.GetStringSelection()
        db.AppendColumn(p.image_table, new_column, coltypes[usertype][0])
        self.annotation_cols[new_column] = coltypes[usertype][1]
        self.annotationCol.Items += [new_column]
        self.annotationCol.SetSelection(len(self.annotation_cols) - 1)
        current_selection = self.measurementsChoice.GetSelection()
        self.measurementsChoice.SetItems(self.measurementsChoice.Strings + [new_column])
        if self.annotationShowVals.IsChecked():
            column = self.annotationCol.Value
            self.sourceChoice.SetStringSelection(p.image_table)
            self.measurementsChoice.SetStringSelection(column)
            self.UpdatePlateMaps()
        else:
            self.measurementsChoice.SetSelection(current_selection)
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
        #if self.outlineMarked.IsChecked():
            #self.filterChoice.SetStringSelection(FilterComboBox.NO_FILTER)
            #self.filterChoice.Disable()
        #else:
            #if not self.annotationShowVals.IsChecked():
                #self.filterChoice.Enable()
        # Update outlined wells in PlateMapPanels
        for pm in self.plateMaps:
            if self.outlineMarked.IsChecked():
                column = self.annotationCol.Value
                if p.plate_id:
                    res = db.execute('SELECT %s, %s FROM %s WHERE %s="%s"'%(
                        dbconnect.UniqueWellClause(), column, p.image_table, 
                        p.plate_id, pm.plate))
                else:
                    # if there's no plate_id, we assume there is only 1 plate
                    # and fetch all the data
                    res = db.execute('SELECT %s, %s FROM %s'%(
                        dbconnect.UniqueWellClause(), column, p.image_table))
                keys = [tuple(r[:-1]) for r in res if r[-1] is not None]
                pm.SetOutlinedWells(keys)
            else:
                pm.SetOutlinedWells([])
        self.UpdatePlateMaps()
                
    def OnShowAnnotationValues(self, evt=None):
        '''Handler for the show values checkbox.
        '''
        if self.annotationShowVals.IsChecked():
            column = self.annotationCol.Value
            self.sourceChoice.SetStringSelection(p.image_table)
            self.measurementsChoice.SetItems(get_non_blob_types_from_table(p.image_table))            
            self.measurementsChoice.SetStringSelection(column)
            self.filterChoice.SetStringSelection(FilterComboBox.NO_FILTER)
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
        self.filterChoice.on_select(evt)
        self.UpdatePlateMaps()
        self.colorBar.ResetInterval()
        
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
        for s, v in list(settings.items()):
            if s.startswith('plate '):
                self.plateMapChoices[int(s.strip('plate ')) - 1].SetValue(v)
        # set well display last since each step currently causes a redraw and
        # this could take a long time if they are displaying images
        if 'well display' in settings:
            self.wellDisplayChoice.SetStringSelection(settings['well display'])
            self.OnSelectWellDisplay()
            
            
def FormatPlateMapData(keys_and_vals, categorical=False):
    '''
    keys_and_vals -- a list of lists of well-keys and values
                     eg: [['p1', 'A01', 0.2], 
                          ['p1', 'A02', 0.9], ...]
    returns a 2-tuple containing:
       -an array in the shape of the plate containing the given values with 
        NaNs filling empty slots. If multiple sites per-well are given, then
        the array will be shaped (rows, cols, sites)
       -an array in the shape of the plate containing the given keys with 
        (UnknownPlate, UnknownWell) filling empty slots
    '''
    from itertools import groupby
    keys_and_vals = np.array(keys_and_vals)
    nkeycols = len(dbconnect.well_key_columns())
    shape = list(p.plate_shape)
    if p.plate_type == '5600': 
        well_keys = keys_and_vals[:,:-1] # first column(s) are keys
        data = keys_and_vals[:,-1]       # last column is data
        assert data.ndim == 1
        if len(data) < 5600: raise Exception(
            '''The measurement you chose to plot was missing for some spots. 
            Because CPA doesn't know the well labelling convention used by this
            microarray, we can't be sure how to plot the data. If you are 
            plotting an object measurement, you may have some spots with 0 
            objects and therefore no entry in the table.''')
        assert len(data) == 5600
        data = np.array(list(meander(data.reshape(shape)))).reshape(shape)
        sort_indices = np.array(list(meander(np.arange(np.prod(shape)).reshape(shape)))).reshape(shape)
        well_keys = np.array(list(meander(well_keys.reshape(shape + [nkeycols] )))).reshape(shape + [nkeycols])
        return data, well_keys, sort_indices

    # compute the number of sites-per-well as the max number of rows with the same well-key
    nsites = max([len(list(grp))
                  for k, grp in groupby(keys_and_vals, 
                                        lambda row: tuple(row[:nkeycols]))
                  ])
    if nsites > 1:
        # add a sites dimension to the array shape if there's >1 site per well
        shape += [nsites]
    data = np.ones(shape) * np.nan
    if categorical:
        data = data.astype('object')
    if p.plate_id:
        dummy_key = ('UnknownPlate', 'UnknownWell')
    else:
        dummy_key = ('UnknownWell',)
    well_keys = np.array([dummy_key] * np.prod(shape), 
                         dtype=object).reshape(shape + [nkeycols])
    sort_indices = np.ones(data.shape)*np.nan
    
    dm = DataModel()
    ind = keys_and_vals.argsort(axis=0)
    for i, (k, well_grp) in enumerate(groupby(keys_and_vals[ind[:,len(dummy_key)-1],:], 
                                              lambda row: tuple(row[:len(dummy_key)]))):
        (row, col) = dm.get_well_position_from_name(k[-1])
        well_data = np.array(list(well_grp))[:,-1]
        if len(well_data) == 1:
            data[row, col] = well_data[0]
            sort_indices[row,col] = ind[:,len(dummy_key)-1][i]
        else:
            data[row, col] = well_data
            sort_indices[row,col] = ind[:,len(dummy_key)-1][i*nsites + np.array(list(range(nsites)))] 
        well_keys[row, col] = k
        
    return data, well_keys, sort_indices


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
    return [m for m,t in zip(measurements, types) if t in (float, int)]

def get_non_blob_types_from_table(table):
    measurements = db.GetColumnNames(table)
    types = db.GetColumnTypeStrings(table)
    return [m for m,t in zip(measurements, types) if not 'blob' in t.lower()]

if __name__ == "__main__":
    app = wx.App()

    logging.basicConfig(level=logging.DEBUG)

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        p.LoadFile(propsFile)
    else:
        if not p.show_load_dialog():
            print('Plate Viewer requires a properties file.  Exiting.')
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
        import javabridge
        javabridge.kill_vm()  # noqa: F821
    except:
        import traceback
        traceback.print_exc()
        print("Caught exception while killing VM")
