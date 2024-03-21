
import re
import wx
import wx.lib.intctrl
import wx.lib.agw.floatspin as FS
from . import normalize as norm
# Grouping options
from .normalize import G_EXPERIMENT, G_PLATE, G_QUADRANT, G_WELL_NEIGHBORS, G_CONSTANT
# Aggregation options
from .normalize import M_MEDIAN, M_MEAN, M_MODE, M_NEGCTRL
# Window options
from .normalize import W_SQUARE, W_MEANDER
import numpy as np
from . import dbconnect
import logging
from . import properties
from itertools import groupby
from .plateviewer import FormatPlateMapData
from . import sqltools as sql
from . import guiutils as ui
from .cpatool import CPATool

GROUP_CHOICES = [G_EXPERIMENT, G_PLATE, G_QUADRANT, G_WELL_NEIGHBORS, G_CONSTANT]
AGG_CHOICES = [M_MEDIAN, M_MEAN, M_MODE, M_NEGCTRL]
WINDOW_CHOICES = [W_MEANDER, W_SQUARE]

p = properties.Properties()
db = dbconnect.DBConnect()

class NormalizationStepPanel(wx.Panel):
    def __init__(self, parent, id=-1, allow_delete=True, **kwargs):
        '''allow_delete - whether or not to show an "X" button to allow the user
        to delete this panel
        '''
        wx.Panel.__init__(self, parent, id, **kwargs)
        
        if not (p.plate_id and p.well_id):
            GROUP_CHOICES.remove(G_PLATE)
            GROUP_CHOICES.remove(G_QUADRANT)
            GROUP_CHOICES.remove(G_WELL_NEIGHBORS)

        if not p.negative_control and M_NEGCTRL in AGG_CHOICES:
            AGG_CHOICES.remove(M_NEGCTRL)
            
        self.window_group = wx.Choice(self, -1, choices=GROUP_CHOICES)
        self.window_group.Select(0)
        self.window_group.SetHelpText("Set the grouping to be used for the normalization.\n"
                                     "Experiment: Perform using all data.\n"
                                     "Plate: Perform on a per-plate basis.\n"
                                     "Plate Quadrant: Perform by grouping wells from each 4 x 4 grid together.\n"
                                     "Well Neighbors: Perform using data aggregated from neighboring spots/wells; corrects for spatial effects.\n"
                                     "Constant: Simple division by a constant value.\n\n"
                                     "If no plate or well information is available, only the Experiment and Constant options are shown.")
        self.agg_type = wx.Choice(self, -1, choices=AGG_CHOICES)
        self.agg_type.Select(0)
        self.agg_type.SetHelpText("Set the aggregation statistic to use.")
        self.constant_float = FS.FloatSpin(self, -1, increment=1, value=1.0)
        self.constant_float.Hide()
        self.constant_float.SetHelpText("Specify the constant to divide by.")
        self.window_type = wx.RadioBox(self, -1, 'Window type', choices=WINDOW_CHOICES)
        self.window_type.Hide()
        self.window_type.SetHelpText("Set the type of spatial averaging to use. "
                                     "This is commonly used for screens in which the cells are plated according to a spatial pattern, or "
                                     "there are spatially-dependent variations to correct for.")
        self.window_size_desc = wx.StaticText(self, -1, 'Window size:')
        self.window_size_desc.Hide()
        self.window_size = wx.lib.intctrl.IntCtrl(self, value=3, min=1, max=999)
        self.window_size.Hide()
        self.window_size.SetHelpText("Sets the number of adjacent spots/wells to be "
                                     "included in the aggregation.\n"
                                     "If 'Linear (meander)' is selected, the size N is used for a 1 x N filter. "
                                     "If 'Square' is selected, the filter size is N x N.")
                
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Divide values by:'))
        sz.AddSpacer(5)
        sz.Add(self.window_group)
        sz.AddSpacer(5)
        sz.Add(self.agg_type)
        sz.Add(self.constant_float)
        if allow_delete:
            self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))
            self.x_btn.SetHelpText("Click this button to remove a normalization step.")
            sz.AddStretchSpacer()
            sz.Add(self.x_btn)
            self.x_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        self.Sizer.Add(sz, 1, wx.EXPAND)
        
        self.Sizer.Add(self.window_type, 0, wx.LEFT, 30)
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(self.window_size_desc, 0)
        sz.Add(self.window_size, 0, wx.LEFT, 5)
        self.Sizer.Add(sz, 1, wx.EXPAND|wx.LEFT, 30)
        
        self.window_group.Bind(wx.EVT_CHOICE, self.on_window_group_selected)

    def on_window_group_selected(self, evt):
        self.update_visible_fields()
        
    def update_visible_fields(self):
        selected_string = self.window_group.GetStringSelection()
        self.window_type.Hide()
        self.window_size.Hide()
        self.window_size_desc.Hide()
        self.agg_type.Show()
        self.constant_float.Hide()
        if selected_string == G_WELL_NEIGHBORS:
            self.window_type.Show()
            self.window_size.Show()
            self.window_size_desc.Show()
        elif selected_string == G_CONSTANT:
            self.agg_type.Hide()
            self.constant_float.Show()
        self.Fit()
        self.Parent.FitInside()
        
    def on_remove(self, evt):
        self.GrandParent.remove_norm_step(self)
        
    def set_from_configuration_dict(self, config):
        '''config - a configuration dictionary as output by get_configuration_dict()
        '''
        self.window_group.SetStringSelection(config[norm.P_GROUPING])
        self.update_visible_fields()
        self.agg_type.SetStringSelection(config[norm.P_AGG_TYPE])
        if config[norm.P_CONSTANT] is not None:
            self.constant_float.SetValue(config[norm.P_CONSTANT])
        if config[norm.P_WIN_TYPE] is not None:
            self.window_type.SetStringSelection(config[norm.P_WIN_TYPE])
        if config[norm.P_WIN_SIZE] is not None:
            self.window_size.SetValue(config[norm.P_WIN_SIZE])
            
    def set_group_choices(self, choices):
        '''since the per-object table can't yet be spatially grouped, this 
        method allows the choices to be narrowed
        '''
        assert all(c in GROUP_CHOICES for c in choices)
        sel = self.window_group.GetStringSelection()
        self.window_group.SetItems(choices)
        if sel in self.window_group.Items:
            self.window_group.SetStringSelection(sel)
        else:
            self.window_group.Select(0)
        self.update_visible_fields()
        
    def get_configuration_dict(self):
        '''returns a dictionary of configuration settings to be used by 
        normalize.do_normalization_step.
        IMPORTANT: these key names must match the parameter names of
            do_normalization_step
        '''
        return {norm.P_GROUPING : self.window_group.GetStringSelection(), 
                norm.P_AGG_TYPE : self.agg_type.GetStringSelection(), 
                norm.P_CONSTANT : self.constant_float.GetValue() if self.window_group.GetStringSelection()==G_CONSTANT else None, 
                norm.P_WIN_TYPE : self.window_type.GetStringSelection() if self.window_group.GetStringSelection()==G_WELL_NEIGHBORS else None, 
                norm.P_WIN_SIZE : int(self.window_size.Value) if self.window_group.GetStringSelection()==G_WELL_NEIGHBORS else None
                }

class NormalizationUI(wx.Frame, CPATool):
    '''
    '''
    def __init__(self, parent, id=-1, title='Normalization Settings', **kwargs):
        kwargs['size'] = kwargs.get('size', (500,500))
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        CPATool.__init__(self)
        wx.HelpProvider.Set(wx.SimpleHelpProvider())

        self.n_steps = 1

        self.SetBackgroundColour("white")

        
        #
        # Define the controls
        #
        tables = ([p.image_table] or []) + ([p.object_table] if p.object_table else [])
        self.table_choice = wx.Choice(self, -1, choices=tables)
        select_all_btn = wx.Button(self, -1, 'Select all columns')
        select_all_btn.SetHelpText("Click this button to check all columns.")

        self.table_choice.Select(0)
        self.table_choice.SetHelpText("Select the table containing the measurement columns to normalize.")
        self.col_choices = wx.CheckListBox(self, -1, choices=[], size=(-1, 100))
        self.col_choices.SetHelpText("Select the measurement columns to normalize. More than one column may be selected. "
                                     "The normalization steps below will be performed on all columns.")
        add_norm_step_btn = wx.Button(self, -1, 'Add normalization step')
        add_norm_step_btn.SetHelpText("Click this button to add another normalization to perform. "
                                      "The normalizations are performed from top to bottom, with the "
                                      "results from one step being used as input into the following step.")
        self.norm_meas_checkbox = wx.CheckBox(self, -1, 'Normalized measurements')
        self.norm_meas_checkbox.Set3StateValue(True)
        self.norm_meas_checkbox.SetHelpText("Write a column of normalized measurements to the output table. "
                                            "This column ihas the same name as the input, with the suffix '_NmV'")
        self.norm_factor_checkbox = wx.CheckBox(self, -1, 'Normalization factors')
        self.norm_factor_checkbox.SetHelpText("Write a column of normalization factors to the output table. "
                                            "This column ihas the same name as the input, with the suffix '_NmF' added.")
        self.output_table = wx.TextCtrl(self, -1, 'normalized_measurements', size=(200,-1))
        self.output_table.SetHelpText("Enter the name of the output table which will contain "
                                      "your normalized measurements and/or the normalization factors.\n "
                                      "The text will appear orange if the table already exists "
                                      "in the database. The output table will be linked to the existing "
                                      "tables so it is usable immediately.")
        self.help_btn = wx.ContextHelpButton(self)
        self.do_norm_btn = wx.Button(self, wx.ID_OK, 'Perform Normalization')
        self.do_norm_btn.SetHelpText("Once you have adjusted the settings, click this button to start normalization "
                                     "and write the results to the output table. A progress bar will inform you "
                                     "of the normalization status.")
                
        self.boxes = [ ]
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Select a table:'), 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.table_choice, 0)
        sz.Add(select_all_btn, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.col_choices_desc = wx.StaticText(self, -1, 'Select measurements to normalize:')
        self.Sizer.Add(self.col_choices_desc, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.Add(-1, 5, 0)
        self.Sizer.Add(self.col_choices, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        
        #
        # Lay out the first normalization step inside a scrolled window
        # and a static box sizer.
        #
        self.Sizer.Add(wx.StaticText(self, -1, 'Specify the normalization steps you want to perform:'), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.sw = wx.ScrolledWindow(self)
        sbs = wx.StaticBoxSizer(wx.StaticBox(self.sw, label=''), wx.VERTICAL)
        nsp = NormalizationStepPanel(self.sw, allow_delete=False)
        self.norm_steps = [ nsp ]
        self.boxes = [ sbs ]
        sbs.Add(nsp, 0, wx.EXPAND)
        self.sw.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.sw.Sizer.Add(sbs, 0, wx.EXPAND)
        (w,h) = self.sw.Sizer.GetSize()
        self.sw.SetScrollbars(20,20,w//20,h//20,0,0)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddStretchSpacer()
        sz.Add(add_norm_step_btn, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.output_table_desc = wx.StaticText(self, -1, 'Name your output table:')
        sz.Add(self.output_table_desc, 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.output_table, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.output_format_desc = wx.StaticText(self, -1, 'Output columns:')
        sz.Add(self.output_format_desc, 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.norm_meas_checkbox, 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.norm_factor_checkbox, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(self.help_btn)
        sz.AddStretchSpacer()
        sz.Add(self.do_norm_btn)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.ALL, 15)
        
        self.table_choice.Bind(wx.EVT_CHOICE, self.on_select_table)
        select_all_btn.Bind(wx.EVT_BUTTON, self.on_select_all_columns)
        add_norm_step_btn.Bind(wx.EVT_BUTTON, self.on_add_norm_step)
        self.col_choices.Bind(wx.EVT_CHECKLISTBOX, lambda e: self.validate())
        self.norm_meas_checkbox.Bind(wx.EVT_CHECKBOX, lambda e: self.validate())
        self.norm_factor_checkbox.Bind(wx.EVT_CHECKBOX, lambda e: self.validate())
        self.output_table.Bind(wx.EVT_TEXT, lambda e: self.validate())
        self.do_norm_btn.Bind(wx.EVT_BUTTON, self.on_do_normalization)
        
        self.update_measurement_choices()
        self.validate()

    def on_select_table(self, evt):
        self.update_measurement_choices()
        self.update_steps()
        
    def update_measurement_choices(self):
        measurements = db.GetColumnNames(self.table_choice.GetStringSelection())
        types = db.GetColumnTypes(self.table_choice.GetStringSelection())
        numeric_columns = [m for m,t in zip(measurements, types) if t in (float, int)]
        self.col_choices.SetItems(numeric_columns)
        self.validate()
        
    def update_steps(self):
        table = self.table_choice.GetStringSelection()
        if table != p.image_table:
            for panel in self.norm_steps:
                panel.set_group_choices([G_EXPERIMENT, G_PLATE, G_CONSTANT])
        else:
            for panel in self.norm_steps:
                panel.set_group_choices(GROUP_CHOICES)

    def on_select_all_columns(self, evt):
        self.select_all_columns()

    def select_all_columns(self):
        self.col_choices.SetCheckedStrings(self.col_choices.GetItems())

    def on_add_norm_step(self, evt):
        self.add_norm_step()

    def validate(self):
        is_valid = True

        if not self.col_choices.GetCheckedItems():
            is_valid = False
            self.col_choices_desc.SetForegroundColour((255,0,0))
        else:
            self.col_choices_desc.SetForegroundColour((0,0,0))

        tablename = self.output_table.Value
        if not re.match('^[A-Za-z]\w*$', tablename) or tablename in (p.image_table, p.object_table):
            is_valid = False
            self.output_table.SetForegroundColour((255,0,0))
            self.output_table_desc.SetForegroundColour((255,0,0))
        elif db.table_exists(tablename):
            self.output_table.SetForegroundColour((255,165,0))
            self.output_table_desc.SetForegroundColour((255,165,0))
        else:
            self.output_table.SetForegroundColour((0,0,0))
            self.output_table_desc.SetForegroundColour((0,0,0))

        if not (self.norm_meas_checkbox.IsChecked() or self.norm_factor_checkbox.IsChecked()):
            is_valid = False
            self.output_format_desc.SetForegroundColour((255,0,0))
        else:
            self.output_format_desc.SetForegroundColour((0,0,0))
        
        self.do_norm_btn.Enable(is_valid)
        return is_valid
        
    def add_norm_step(self):
        sz = wx.StaticBoxSizer(wx.StaticBox(self.sw, label=''), wx.VERTICAL)
        self.norm_steps += [NormalizationStepPanel(self.sw)]
        self.boxes += [sz]
        sz.Add(self.norm_steps[-1], 0, wx.EXPAND)
        self.sw.Sizer.Insert(len(self.norm_steps)-1, sz, 0, wx.EXPAND|wx.TOP, 15)
        self.sw.FitInside()
        self.Layout()
        self.update_steps()
        
    def remove_norm_step(self, panel):
        idx = self.norm_steps.index(panel)
        self.norm_steps.remove(panel)
        panel.Destroy()
        # remove the statix box that was holding the panel
        sbox = self.boxes.pop(idx)
        self.sw.Sizer.Remove(sbox)
        self.sw.FitInside()
        self.Layout()
        
    def get_selected_measurement_columns(self):
        return self.col_choices.GetCheckedStrings()

    def on_do_normalization(self, evt):
        self.do_normalization()
        
    def do_normalization(self):
        if not self.validate():
            # Should be unreachable
            wx.MessageBox('Your normalization settings are invalid. Can\'t perform normalization.')
            
        long_cols = [col for col in self.col_choices.GetCheckedStrings() 
                     if len(col) + 4 > 64]
        if long_cols:
            dlg = wx.MessageDialog(self, 'The following columns contain more '
                    'than 64 characters when a normalization suffix (4 '
                    'characters) is appended. This may cause a problem when '
                    'writing to the database.\n %s'%('\n'.join(long_cols)), 
                    'Warning', wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            dlg.Destroy()

        imkey_cols = dbconnect.image_key_columns()
        obkey_cols = dbconnect.object_key_columns()
        wellkey_cols = dbconnect.well_key_columns()
        im_clause = dbconnect.UniqueImageClause
        well_clause = dbconnect.UniqueWellClause
        input_table = self.table_choice.GetStringSelection()
        meas_cols = self.col_choices.GetCheckedStrings()
        wants_norm_meas = self.norm_meas_checkbox.IsChecked()
        wants_norm_factor = self.norm_factor_checkbox.IsChecked()
        output_table = self.output_table.Value
        FIRST_MEAS_INDEX = len(imkey_cols + (wellkey_cols or tuple()))
        if p.db_type == 'mysql':
            BATCH_SIZE = 100
        else:
            BATCH_SIZE = 1
        if input_table == p.object_table: 
            FIRST_MEAS_INDEX += 1 # Original
        if wellkey_cols:
            if input_table == p.image_table:
                WELL_KEY_INDEX = len(imkey_cols)
            else:
                WELL_KEY_INDEX = len(imkey_cols) + 1
                
        if db.table_exists(output_table):
            dlg = wx.MessageDialog(self, 'Are you sure you want to overwrite the table "%s"?'%(output_table), 
                                   "Overwrite table?", wx.YES_NO|wx.NO_DEFAULT|wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
                return 
            dlg.Destroy()

        #
        # First Get the data from the db.
        #
        if input_table == p.image_table:
            if wellkey_cols:
                # If there are well columns, fetch them.
                query = "SELECT %s, %s, %s FROM %s"%(
                            im_clause(), well_clause(), ', '.join(meas_cols), 
                            input_table)
            else:
                query = "SELECT %s, %s FROM %s"%(
                            im_clause(), ', '.join(meas_cols),
                            input_table)
        elif input_table == p.object_table:
            if p.image_table and wellkey_cols:

                # If we have x and y from cells, we can use that for classifier
                if p.cell_x_loc and p.cell_y_loc:
                    FIRST_MEAS_INDEX += 2 # Cell X and Y Location are fixed to for classifier
                    # If there are well columns, fetch them from the per-image table.
                    query = "SELECT %s, %s, %s, %s, %s FROM %s, %s WHERE %s"%(
                                dbconnect.UniqueObjectClause(p.object_table),
                                well_clause(p.image_table),
                                p.cell_x_loc,
                                p.cell_y_loc,
                                ', '.join(['%s.%s'%(p.object_table, col) for col in meas_cols]),
                                p.image_table, p.object_table,
                                ' AND '.join(['%s.%s=%s.%s'%(p.image_table, c, p.object_table, c) 
                                              for c in imkey_cols]) )

                else:
                    # If there are well columns, fetch them from the per-image table.
                    query = "SELECT %s, %s, %s FROM %s, %s WHERE %s"%(
                                dbconnect.UniqueObjectClause(p.object_table),
                                well_clause(p.image_table), 
                                ', '.join(['%s.%s'%(p.object_table, col) for col in meas_cols]),
                                p.image_table, p.object_table,
                                ' AND '.join(['%s.%s=%s.%s'%(p.image_table, c, p.object_table, c) 
                                              for c in imkey_cols]) )

            else:

                if p.cell_x_loc and p.cell_y_loc:
                    FIRST_MEAS_INDEX += 2 # Cell X and Y Location are fixed to for classifier
                    
                    query = "SELECT %s, %s, %s, %s FROM %s"%(
                            im_clause(), p.cell_x_loc, p.cell_y_loc, ', '.join(meas_cols),
                            input_table)

                else:
                    query = "SELECT %s, %s FROM %s"%(
                            im_clause(), ', '.join(meas_cols),
                            input_table)

        if p.negative_control: # if the user defined negative control, we can use that to fetch the wellkeys
                    neg_query = query + ' AND ' + p.negative_control # fetch all the negative control elements

        if wellkey_cols:
            query += " ORDER BY %s"%(well_clause(p.image_table))
            
            
        dlg = wx.ProgressDialog('Computing normalized values',
                                'Querying database for raw data.',
                                parent=self,
                                style = wx.PD_CAN_ABORT|wx.PD_APP_MODAL)
        dlg.Pulse()
        #
        # MAKE THE QUERY
        # 

        input_data = np.array(db.execute(query), dtype=object)  
        if p.negative_control:
            import pandas as pd
            negative_control = pd.DataFrame(db.execute(neg_query), dtype=float)
            logging.info("# of objects in negative control: " + str(negative_control.shape[0]))
            logging.info("# of objects queried: " + str(input_data.shape[0]))
            neg_mean_plate = negative_control.groupby([WELL_KEY_INDEX]).mean()
            neg_std_plate = negative_control.groupby([WELL_KEY_INDEX]).std()

        output_columns = np.ones(input_data[:,FIRST_MEAS_INDEX:].shape) * np.nan
        output_factors = np.ones(input_data[:,FIRST_MEAS_INDEX:].shape) * np.nan
        for colnum, col in enumerate(input_data[:,FIRST_MEAS_INDEX:].T):
            keep_going, skip = dlg.Pulse("Normalizing column %d of %d"%(colnum+1, len(meas_cols))) 
            if not keep_going:
                dlg.Destroy()
                return
            norm_data = col.copy()
            for step_num, step_panel in enumerate(self.norm_steps):
                d = step_panel.get_configuration_dict()
                if d[norm.P_GROUPING] in (norm.G_QUADRANT, norm.G_WELL_NEIGHBORS):
                    # Reshape data if normalization step is plate sensitive.
                    assert p.plate_id and p.well_id
                    well_keys = input_data[:, list(range(WELL_KEY_INDEX, FIRST_MEAS_INDEX - 2)) ] 
                    wellkeys_and_vals = np.hstack((well_keys, np.array([norm_data]).T))
                    new_norm_data    = []
                    for plate, plate_grp in groupby(wellkeys_and_vals, lambda row: row[0]):
                        keys_and_vals = np.array(list(plate_grp))
                        plate_data, wks, ind = FormatPlateMapData(keys_and_vals)
                        pnorm_data = norm.do_normalization_step(plate_data, **d)
                        new_norm_data += pnorm_data.flatten()[ind.flatten().tolist()].tolist()
                    norm_data = new_norm_data
                elif d[norm.P_GROUPING] == norm.G_PLATE:
                    assert p.plate_id and p.well_id

                    if d[norm.P_AGG_TYPE] == norm.M_NEGCTRL:
                        mean_plate_col = neg_mean_plate[colnum + FIRST_MEAS_INDEX]
                        std_plate_col = neg_std_plate[colnum + FIRST_MEAS_INDEX]  
                        print(mean_plate_col)
                        print(std_plate_col)            

                    well_keys = input_data[:, list(range(WELL_KEY_INDEX, FIRST_MEAS_INDEX - 2))]
                    wellkeys_and_vals = np.hstack((well_keys, np.array([norm_data]).T))
                    new_norm_data    = []
                    # print wellkeys_and_vals
                    for plate, plate_grp in groupby(wellkeys_and_vals, lambda row: row[0]):
                        plate_data = np.array(list(plate_grp))[:,-1].flatten()
                        pnorm_data = norm.do_normalization_step(plate_data, **d)

                        if d[norm.P_AGG_TYPE] == norm.M_NEGCTRL:
                            try:
                                plate_mean = mean_plate_col[plate]
                                plate_std = std_plate_col[plate]
                            except:
                                plate_mean = mean_plate_col[int(plate)]
                                plate_std = std_plate_col[int(plate)]

                            try:
                                pnorm_data = (pnorm_data - plate_mean) / plate_std
                                print(pnorm_data)
                            except:
                                logging.error("Plate std is zero, division by zero!")

                        new_norm_data += pnorm_data.tolist()
                    norm_data = new_norm_data
                else:
                    norm_data = norm.do_normalization_step(norm_data, **d)
                    
            output_columns[:,colnum] = np.array(norm_data)
            output_factors[:,colnum] = col.astype(float) / np.array(norm_data,dtype=float)

        dlg.Destroy()

        norm_table_cols = []
        # Write new table
        db.execute('DROP TABLE IF EXISTS %s'%(output_table))
        if input_table == p.image_table:
            norm_table_cols += dbconnect.image_key_columns()
            col_defs = ', '.join(['%s %s'%(col, db.GetColumnTypeString(p.image_table, col))
                              for col in dbconnect.image_key_columns()])
        elif input_table == p.object_table:
            norm_table_cols += obkey_cols
            col_defs = ', '.join(['%s %s'%(col, db.GetColumnTypeString(p.object_table, col))
                              for col in obkey_cols])
        if wellkey_cols:
            norm_table_cols += wellkey_cols
            col_defs +=  ', '+ ', '.join(['%s %s'%(col, db.GetColumnTypeString(p.image_table, col))
                                        for col in wellkey_cols])

        if input_table == p.object_table:
            if p.cell_x_loc and p.cell_y_loc:
                norm_table_cols += [p.cell_x_loc, p.cell_y_loc]
                col_defs += ', %s %s'%(p.cell_x_loc, db.GetColumnTypeString(p.object_table, p.cell_x_loc)) + ', ' + '%s %s'%(p.cell_y_loc, db.GetColumnTypeString(p.object_table, p.cell_y_loc))

        if wants_norm_meas:
            col_defs += ', '+ ', '.join(['%s_NmM %s'%(col, db.GetColumnTypeString(input_table, col))
                                         for col in meas_cols]) 
        if wants_norm_factor:
            col_defs += ', '+ ', '.join(['%s_NmF %s'%(col, db.GetColumnTypeString(input_table, col))
                                         for col in meas_cols]) 

        for col in meas_cols:
            if wants_norm_meas:
                norm_table_cols += ['%s_NmM'%(col)]
            if wants_norm_factor:
                norm_table_cols += ['%s_NmF'%(col)]
        db.execute('CREATE TABLE %s (%s)'%(output_table, col_defs))
        
        dlg = wx.ProgressDialog('Writing to "%s"'%(output_table),
                               "Writing normalized values to database",
                               maximum = output_columns.shape[0],
                               parent=self,
                               style = wx.PD_CAN_ABORT|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME|wx.PD_ESTIMATED_TIME|wx.PD_REMAINING_TIME)
            
        cmd = 'INSERT INTO %s VALUES '%(output_table)
        cmdi = cmd
        for i, (val, factor) in enumerate(zip(output_columns, output_factors)):
            cmdi += '(' + ','.join(['"%s"']*len(norm_table_cols)) + ')'
            if wants_norm_meas and wants_norm_factor:
                cmdi = cmdi%tuple(list(input_data[i, :FIRST_MEAS_INDEX]) + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in val] + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in factor])
            elif wants_norm_meas:
                cmdi = cmdi%tuple(list(input_data[i, :FIRST_MEAS_INDEX]) + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in val])
            elif wants_norm_factor:
                cmdi = cmdi%tuple(list(input_data[i, :FIRST_MEAS_INDEX]) + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in factor])
            if (i+1) % BATCH_SIZE == 0 or i==len(output_columns)-1:
                db.execute(str(cmdi))
                cmdi = cmd
                # update status dialog
                (keep_going, skip) = dlg.Update(i)
                if not keep_going:
                    break
            else:
                cmdi += ',\n'
        dlg.Destroy()
        db.Commit()
        
        #
        # Update table linkage
        #
        if db.get_linking_tables(input_table, output_table) is not None:
            db.do_unlink_table(output_table)
            
        if input_table == p.image_table:
            db.do_link_tables(output_table, input_table, imkey_cols, imkey_cols)
        elif input_table == p.object_table:
            db.do_link_tables(output_table, input_table, obkey_cols, obkey_cols)            
        
        #
        # Show the resultant table        
        #
        from . import tableviewer
        tv = tableviewer.TableViewer(ui.get_main_frame_or_none())
        tv.Show()
        tv.load_db_table(output_table)
        
    def save_settings(self):
        '''returns a dictionary mapping setting names to values encoded as strings'''
        return {
            'table' : self.table_choice.GetStringSelection(),
            'columns' : ','.join(self.col_choices.GetCheckedStrings()),
            'steps' : repr([s.get_configuration_dict() for s in self.norm_steps]),
            'wants_meas' : str(int(self.norm_meas_checkbox.IsChecked())),
            'wants_factor' : str(int(self.norm_factor_checkbox.IsChecked())),
            'output_table' : self.output_table.Value,
            'version' : '1',
        }
    
    def load_settings(self, settings):
        '''settings - a dictionary mapping setting names to values encoded as strings.'''
        if 'table' in settings:
            self.table_choice.SetStringSelection(settings['table'])
            self.update_measurement_choices()
        if 'columns' in settings:
            cols = list(map(str.strip, settings['columns'].split(',')))
            self.col_choices.SetCheckedStrings(cols)
        if 'steps' in settings:
            steps = eval(settings['steps'])
            for panel in self.norm_steps[1:]:
                self.remove_norm_step(panel)
            self.norm_steps[0].set_from_configuration_dict(steps[0])
            for config in steps[1:]:
                self.add_norm_step()
                self.norm_steps[-1].set_from_configuration_dict(config)
        if 'wants_meas' in settings:
            self.norm_meas_checkbox.SetValue(int(settings['wants_meas']))
        if 'wants_factor' in settings:
            self.norm_factor_checkbox.SetValue(int(settings['wants_factor']))
        if 'output_table' in settings:
            self.output_table.SetValue(settings['output_table'])

            
if __name__ == "__main__":
    app = wx.App()
    logging.basicConfig(level=logging.DEBUG)
    
    if p.show_load_dialog():
        f = NormalizationUI(None)
        f.Show()
        f.Center()
    
    app.MainLoop()
