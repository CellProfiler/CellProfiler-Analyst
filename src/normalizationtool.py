import re
import wx
import wx.lib.intctrl
import wx.lib.agw.floatspin as FS
import normalize as norm
# Grouping options
from normalize import G_EXPERIMENT, G_PLATE, G_QUADRANT, G_WELL_NEIGHBORS, G_CONSTANT
# Aggregation options
from normalize import M_MEDIAN, M_MEAN, M_MODE
# Window options
from normalize import W_SQUARE, W_MEANDER
import numpy as np
import dbconnect
import logging
import properties
from itertools import groupby
from plateviewer import FormatPlateMapData
import sqltools as sql

GROUP_CHOICES = [G_EXPERIMENT, G_PLATE, G_QUADRANT, G_WELL_NEIGHBORS, G_CONSTANT]
AGG_CHOICES = [M_MEDIAN, M_MEAN, M_MODE]
WINDOW_CHOICES = [W_MEANDER, W_SQUARE]

p = properties.Properties.getInstance()
db = dbconnect.DBConnect.getInstance()

class NormalizationStepPanel(wx.Panel):
    def __init__(self, parent, id=-1, allow_delete=True, **kwargs):
        wx.Panel.__init__(self, parent, id, **kwargs)
        
        if not (p.plate_id and p.well_id):
            GROUP_CHOICES.remove(G_PLATE)
            GROUP_CHOICES.remove(G_QUADRANT)
            GROUP_CHOICES.remove(G_WELL_NEIGHBORS)
        self.window_group = wx.Choice(self, -1, choices=GROUP_CHOICES)
        self.window_group.Select(0)
        self.agg_type = wx.Choice(self, -1, choices=AGG_CHOICES)
        self.agg_type.Select(0)
        self.constant_float = FS.FloatSpin(self, -1, increment=1, value=1.0)
        self.constant_float.Hide()
        self.window_type = wx.RadioBox(self, -1, 'Window type', choices=WINDOW_CHOICES)
        self.window_type.Disable()
        self.window_size = wx.lib.intctrl.IntCtrl(self, value=3, min=1, max=999)
        self.window_size.Disable()
        self.window_size.SetHelpText("Window size help text...")
        self.window_size.SetForegroundColour(wx.LIGHT_GREY)
                
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Divide values by:'))
        sz.AddSpacer((5,-1))
        sz.Add(self.window_group)
        sz.AddSpacer((5,-1))
        sz.Add(self.agg_type)
        sz.Add(self.constant_float)
        if allow_delete:
            self.x_btn = wx.Button(self, -1, 'x', size=(30,-1))
            sz.AddStretchSpacer()
            sz.Add(self.x_btn)
            self.x_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        self.Sizer.Add(sz, 1, wx.EXPAND)
        
        self.Sizer.Add(self.window_type, 0, wx.LEFT, 30)
        self.Sizer.AddSpacer((-1,15))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Window size:'), 0)
        sz.AddSpacer((5,-1))
        sz.Add(self.window_size, 0)
        self.Sizer.Add(sz, 1, wx.EXPAND|wx.LEFT, 30)
        
        self.window_group.Bind(wx.EVT_CHOICE, self.on_window_group_selected)
        self.Fit()

    def on_window_group_selected(self, evt):
        selected_string = self.window_group.GetStringSelection()
        self.window_type.Disable()
        self.window_size.Disable()
        self.window_size.SetForegroundColour(wx.LIGHT_GREY)
        self.agg_type.Show()
        self.constant_float.Hide()
        if selected_string == G_WELL_NEIGHBORS:
            self.window_type.Enable()
            self.window_size.Enable()
            self.window_size.SetForegroundColour(wx.BLACK)
        elif selected_string == G_CONSTANT:
            self.agg_type.Hide()
            self.constant_float.Show()
        self.Refresh()
        self.Layout()
        
    def on_remove(self, evt):
        self.GrandParent.remove_norm_step(self)
        
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

class NormalizationUI(wx.Frame):
    '''
    '''
    def __init__(self, parent=None, id=-1, title='Normalization Settings', **kwargs):
        wx.Frame.__init__(self, parent, id, title=title, **kwargs)
        wx.HelpProvider_Set(wx.SimpleHelpProvider())

        self.n_steps = 1
        
        #
        # Define the controls
        #
        tables = ([p.image_table] or []) + ([p.object_table] or [])
        self.table_choice = wx.Choice(self, -1, choices=tables)
        self.table_choice.Select(0)
        self.col_choices = wx.CheckListBox(self, -1, choices=[], size=(-1, 100))
        self.update_measurement_choices()
        add_norm_step_btn = wx.Button(self, -1, 'Add normalization step')
        self.norm_meas_checkbox = wx.CheckBox(self, -1, 'Normalized measurement')
        self.norm_meas_checkbox.Set3StateValue(True)
        self.norm_factor_checkbox = wx.CheckBox(self, -1, 'Normalization value')
        self.output_table = wx.TextCtrl(self, -1, 'normalized_measurements', size=(200,-1))
        self.output_table.SetHelpText("TODO: help text...")
        self.help_btn = wx.ContextHelpButton(self)
        self.do_norm_btn = wx.Button(self, wx.ID_OK, 'Perform Normalization')
                
        self.boxes = [ ]
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, 'Select a table:'), 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.table_choice, 0)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.col_choices_desc = wx.StaticText(self, -1, 'Select measurements to normalize:')
        self.Sizer.Add(self.col_choices_desc, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)
        self.Sizer.AddSpacer((-1,5))
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
        self.sw.SetScrollbars(20,20,w/20,h/20,0,0)
        self.Sizer.Add(self.sw, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.AddStretchSpacer()
        sz.Add(add_norm_step_btn, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.RIGHT, 15)
        
        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.output_format_desc = wx.StaticText(self, -1, 'Output format:')
        sz.Add(self.output_format_desc, 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.norm_meas_checkbox, 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.norm_factor_checkbox, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        self.output_table_desc = wx.StaticText(self, -1, 'Name your output table:')
        sz.Add(self.output_table_desc, 0, wx.EXPAND|wx.RIGHT, 5)
        sz.Add(self.output_table, 0, wx.EXPAND)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 15)

        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(self.help_btn)
        sz.AddStretchSpacer()
        sz.Add(self.do_norm_btn)
        self.Sizer.Add(sz, 0, wx.EXPAND|wx.ALL, 15)
        
        self.table_choice.Bind(wx.EVT_CHOICE, self.on_select_table)
        add_norm_step_btn.Bind(wx.EVT_BUTTON, self.on_add_norm_step)
        self.col_choices.Bind(wx.EVT_CHECKLISTBOX, lambda(e):self.validate())
        self.norm_meas_checkbox.Bind(wx.EVT_CHECKBOX, lambda(e):self.validate())
        self.norm_factor_checkbox.Bind(wx.EVT_CHECKBOX, lambda(e):self.validate())
        self.output_table.Bind(wx.EVT_TEXT, lambda(e):self.validate())
        self.do_norm_btn.Bind(wx.EVT_BUTTON, self.on_do_normalization)
        
        self.validate()

    def on_select_table(self, evt):
        self.update_measurement_choices()
    def update_measurement_choices(self):
        measurements = db.GetColumnNames(self.table_choice.GetStringSelection())
        types = db.GetColumnTypes(p.image_table)
        numeric_columns = [m for m,t in zip(measurements, types) if t in [float, int, long]]
        self.col_choices.SetItems(numeric_columns)
        
    def on_add_norm_step(self, evt):
        self.add_norm_step()

    def validate(self):
        is_valid = True

        if not self.col_choices.GetChecked():
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
        # TODO: Add new boxes at bottom, rather than at top
        sz.Add(self.norm_steps[-1], 0, wx.EXPAND)
        self.sw.Sizer.InsertSizer(len(self.norm_steps)-1, sz, 0, wx.EXPAND|wx.TOP, 15)
        self.sw.FitInside()
        self.Layout()
        
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
        imkey_cols = dbconnect.image_key_columns()
        wellkey_cols = dbconnect.well_key_columns()
        im_clause = dbconnect.UniqueImageClause
        well_clause = dbconnect.UniqueWellClause
        input_table = self.table_choice.GetStringSelection()
        meas_cols = self.col_choices.GetCheckedStrings()
        wants_norm_meas = self.norm_meas_checkbox.IsChecked()
        wants_norm_factor = self.norm_factor_checkbox.IsChecked()
        output_table = self.output_table.Value
        FIRST_MEAS_INDEX = len(imkey_cols + (wellkey_cols or tuple()))
        if input_table == p.object_table: 
            FIRST_MEAS_INDEX += 1
        if wellkey_cols:
            WELL_KEY_INDEX = len(imkey_cols)
            
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
                # If there are well columns, fetch them from the per-image table.
                query = "SELECT %s, %s, %s FROM %s, %s WHERE %s"%(
                            dbconnect.UniqueObjectClause(p.object_table),
                            well_clause(p.image_table), 
                            ', '.join(['%s.%s'%(p.object_table, col) for col in meas_cols]),
                            p.image_table, p.object_table,
                            ' AND '.join(['%s.%s=%s.%s'%(p.image_table, c, p.object_table, c) 
                                          for c in imkey_cols]) )
            else:
                query = "SELECT %s, %s FROM %s"%(
                            im_clause(), ', '.join(meas_cols),
                            input_table)
        if wellkey_cols:
            query += " ORDER BY %s"%(well_clause(p.image_table))
            
            
        dlg = wx.ProgressDialog('Computing normalized values',
                               "Querying database for raw data.",
                               parent=self,
                               style = wx.PD_CAN_ABORT|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        #
        # MAKE THE QUERY
        #
        input_data = np.array(db.execute(query), dtype=object)
                
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
                if d[norm.P_GROUPING] in (norm.G_PLATE, norm.G_QUADRANT, norm.G_WELL_NEIGHBORS):
                    # Reshape data if normalization step is plate sensitive.
                    assert p.plate_id and p.well_id
                    well_keys = input_data[:, range(WELL_KEY_INDEX, FIRST_MEAS_INDEX)]
                    wellkeys_and_vals = np.hstack((well_keys, np.array([norm_data]).T))
                    new_norm_data    = []
                    for k, plate_grp in groupby(wellkeys_and_vals, lambda(row): tuple(row[0])):
                        keys_and_vals = list(plate_grp)
                        plate_data, wks, ind = FormatPlateMapData(keys_and_vals)
                        pnorm_data = norm.do_normalization_step(plate_data, **d)
                        new_norm_data += pnorm_data.flatten()[ind.flatten().tolist()].tolist()
                    norm_data = new_norm_data
                else:
                    norm_data = norm.do_normalization_step(norm_data, **d)
                    
            output_columns[:,colnum] = np.array(norm_data)
            output_factors[:,colnum] = col.astype(float)/np.array(norm_data,dtype=float)

        dlg.Destroy()
                
        # Write new table
        db.execute('DROP TABLE IF EXISTS %s'%(output_table))
        if input_table == p.image_table:
            col_defs = ', '.join(['%s %s'%(col, db.GetColumnTypeString(p.image_table, col))
                              for col in dbconnect.image_key_columns()])
        elif input_table == p.object_table:
            #new_cols = dbconnect.object_key_columns()
            col_defs = ', '.join(['%s %s'%(col, db.GetColumnTypeString(p.object_table, col))
                              for col in dbconnect.object_key_columns()])
        if wellkey_cols:
            col_defs +=  ', '+ ', '.join(['%s %s'%(col, db.GetColumnTypeString(p.image_table, col))
                                        for col in wellkey_cols])
        if wants_norm_meas:
            col_defs += ', '+ ', '.join(['%s_NmV %s'%(col, db.GetColumnTypeString(input_table, col))
                                         for col in meas_cols]) 
        if wants_norm_factor:
            col_defs += ', '+ ', '.join(['%s_NmF %s'%(col, db.GetColumnTypeString(input_table, col))
                                         for col in meas_cols]) 
        db.execute('CREATE TABLE %s (%s)'%(output_table, col_defs))
        
        dlg = wx.ProgressDialog('Writing to "%s"'%(output_table),
                               "Writing normalized values to database",
                               maximum = output_columns.shape[0],
                               parent=self,
                               style = wx.PD_CAN_ABORT|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME|wx.PD_ESTIMATED_TIME|wx.PD_REMAINING_TIME)
        
        cmd = 'INSERT INTO %s values ('
        if input_table == p.image_table:
            cmd += '%d,'*len(imkey_cols)
        elif input_table == p.object_table:
            cmd += '%d,'*len(dbconnect.object_key_columns())
        if wellkey_cols:
            cmd += '"%s",'*len(wellkey_cols)
        for i, (val, factor) in enumerate(zip(output_columns, output_factors)):
            if wants_norm_meas and wants_norm_factor:
                stmt = cmd + ",".join(["%s" if (np.isnan(x) or np.isinf(x)) else "%f" for x in val]) \
                     + "," + ",".join(["%s" if (np.isnan(x) or np.isinf(x)) else "%f" for x in factor]) \
                     + ")"
                stmt = stmt%tuple([output_table] + 
                                  list(input_data[i, :FIRST_MEAS_INDEX]) + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in val] + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in factor])
            elif wants_norm_meas:
                stmt = cmd + ",".join(["%s" if (np.isnan(x) or np.isinf(x)) else "%f" for x in val]) + ")"
                stmt = stmt%tuple([output_table] + 
                                  list(input_data[i, :FIRST_MEAS_INDEX]) + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in val])
            elif wants_norm_factor:
                stmt += ",".join(["%s" if (np.isnan(x) or np.isinf(x)) else "%f" for x in factor]) + ")"
                stmt = stmt%tuple([output_table] + 
                                  list(input_data[i, :FIRST_MEAS_INDEX]) + 
                                  ['NULL' if (np.isnan(x) or np.isinf(x)) else x for x in factor])
            db.execute(stmt)
            # update status dialog
            (keep_going, skip) = dlg.Update(i)
            if not keep_going:
                break
        dlg.Destroy()
        db.Commit()

            
if __name__ == "__main__":
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG)
    
    if p.show_load_dialog():
        f = NormalizationUI(size=(500,550))
        f.Show()
        f.Center()
    
    app.MainLoop()
