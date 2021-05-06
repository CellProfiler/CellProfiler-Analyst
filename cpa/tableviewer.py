# -*- Encoding: utf-8 -*-

#
# TODO: make use of new table linking
# Add link_to_images() function to subclasses of TableData and call it lazily
# when user requests images.
#


import csv
import os
import re
import logging

import numpy as np

import wx
import wx.grid as  gridlib
import cpa.helpmenu
from cpa.guiutils import create_status_bar
from .properties import Properties
from . import dbconnect
from .datamodel import DataModel
from . import imagetools

p = Properties()
db = dbconnect.DBConnect()

ABC = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
ABC += [x+y for x in ABC for y in ABC] + [x+y+z for x in ABC for y in ABC for z in ABC]
ROW_LABEL_SIZE = 30


class TableData(gridlib.GridTableBase):
    '''
    Interface connecting the table grid GUI to the underlying table data.
    '''
    def __init__(self):
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        gridlib.GridTableBase.__init__(self)
    
    def set_sort_col(self, col_index, add=False):
        '''Sort rows by the column indicated indexed by col_index. If add is 
        True, the column will be added to the end of a list of sort-by columns.
        '''
        raise NotImplementedError
    
    def get_image_keys_at_row(self, row):
        '''returns a list of image keys at a given row index or None.
        '''
        raise NotImplementedError
    
    def get_object_keys_at_row(self, row):
        '''returns a list of object keys at a given row index or None.
        '''
        raise NotImplementedError
    
    def set_filter(self, filter):
        '''filter - a per-image filter to apply to the data.
        '''
        #XXX: how does this apply to per-well data?
        self.filter = filter
    
    def set_key_indices(self, key_indices):
        '''key_indices - the indices of the key columns for this table data.
              These columns, taken together, should be UNIQUE for every row.
        '''
        self.key_indices = key_indices
    
    def set_grouping(self, group_name):
        '''group_name - group name that specifies how the data is grouped
              relative to the per image table.
        '''
        self.grouping = group_name

    def set_row_interval(self, rmin, rmax):
        '''rmin, rmax - min and max row indices to display.
              Used for displaying pages.
              Use None to leave the bound open.
        '''
        raise NotImplementedError

    def ResetView(self, grid):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        grid.BeginBatch()
        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), 
             gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED, 
             gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), 
             gridlib.GRIDTABLE_NOTIFY_COLS_DELETED, 
             gridlib.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:
            if new < current:
                msg = gridlib.GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = gridlib.GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)
        grid.EndBatch()
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        # update the column rendering plugins
##        self._updateColAttrs(grid)
        # update the scrollbars and the displayed part of the grid
        grid.AdjustScrollbars()
        grid.ForceRefresh()


    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = gridlib.GridTableMessage(self, gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)


# Data could be aggregated many ways... need to know which way so image keys and
# object keys can be returned faithfully
# XXX: implement get_object_keys_at_row
# XXX: Consider consuming this functionality into DBTable by automatically 
#      transforming all tables into DB temporary tables.
#      Tables could then be made permanent by saving to CSV or DB.
class PlainTable(TableData):
    '''
    Generic table interface for displaying tabular data, eg, from a csv file.
    If the image key column names exist in the column labels then the values 
    from these columns will be used to link the data to the images
    '''
    def __init__(self, grid, data, col_labels=None, key_indices=None, 
                 grouping=None):
        '''
        Arguments:
        grid -- parent grid
        data -- the table data as a 2D np object array
        col_labels -- text labels for each column
        key_indices -- indices of columns that constitute a unique key for the table
        grouping -- a group name that specifies how the data is grouped relative
                    to the per image table.
        '''
        if col_labels is None:
            col_labels = ABC[:data.shape[1]]

        assert len(col_labels) == data.shape[1], "Number of column labels does not match the number of columns in data."
        self.sortdir       =  1    # sort direction (1=descending, -1=descending)
        self.sortcols      =  []   # column indices being sorted (in order)
        self.grid          =  grid
        self.data          =  data
        self.ordered_data  =  self.data
        self.col_labels    =  np.array(col_labels)
        self.row_labels    =  None
        self.shown_columns =  np.arange(len(self.col_labels))
        self.row_order     =  np.arange(self.data.shape[0])
        self.col_order     =  np.arange(self.data.shape[1])
        self.key_indices   =  key_indices
        self.grouping      =  grouping
        TableData.__init__(self)
        
    def set_shown_columns(self, col_indices):
        '''sets which column should be shown from the db table
        
        col_indices -- the indices of the columns to show (all others will be 
                       hidden)
        '''
        self.shown_columns = self.col_order = col_indices
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
        
    def set_key_col_indices(self, indices):
        '''Sets the indices (starting at 0) of the key columns. These are needed
        to relate tables to each other.
        eg: to relate a unique (Table, Well, Replicate) to a unique image key.
        '''
        for i in indices: 
            assert 0 < i < len(self.sortcols), 'Key column index (%s) was outside the realm of possible indices (0-%d).'%(i, len(self.sortcols)-1)
        self.key_indices = indices
        
    def get_image_keys_at_row(self, row):
        '''Returns a list of image keys at the given row or None if the column 
        names can't be found in col_labels
        '''
        if self.key_indices is None or self.grouping is None:
            return None
        else:
            if self.grouping.lower() == 'image':     
                return [tuple(self.data[self.row_order,:][row, self.key_indices])]
            elif self.grouping.lower() == 'object': 
                return [tuple(self.data[self.row_order,:][row, self.key_indices[:-1]])]
            else:
                dm = DataModel()
                return dm.GetImagesInGroup(self.grouping, self.get_row_key(row))
        
    def get_object_keys_at_row(self, row):
        '''Returns a list of object keys at the given row or None if the column
        names can't be found in col_labels
        '''
        if self.key_indices is None or self.grouping is None:
            return None
        else:
            dm = DataModel()
            # If the key index for the row is an object key, just return that key
            if self.grouping.lower() == 'object': 
                return [tuple(self.data[self.row_order,:][row, self.key_indices])]
            else: # Otherwise, return all object keys in the image
                imkeys = self.get_image_keys_at_row(row) 
                obkeys = []
                for imkey in imkeys:
                    obs = dm.GetObjectCountFromImage(imkey)
                    obkeys += [tuple(list(imkey)+[i]) for i in range(1,obs+1)]
                return obkeys
        
    def get_row_key(self, row):
        '''Returns the key column values at the given row.
        '''
        if self.key_indices is None:
            return None
        else:
            return tuple(self.ordered_data[row, self.key_indices])
        
    def get_key_cols(self):
        '''Returns a list of the key column names or None if none are specified.
        '''
        if self.key_indices is not None:
            return self.col_labels[self.key_indices].tolist()
        else:
            return None
    
    def GetNumberRows(self):
        return self.ordered_data.shape[0]

    def GetNumberCols(self):
        return self.ordered_data.shape[1]

    def GetColLabelValueWithoutDecoration(self, col_index):
        '''returns the column label at a given index (without ^,v decoration)
        Note: this does not return hidden column labels
        '''
        return self.col_labels[self.shown_columns][col_index]
    
    def GetColLabelValue(self, col_index):
        '''returns the column label at a given index (for display)
        '''
        col = self.col_labels[self.shown_columns][col_index]
        if col_index in self.sortcols:
            return col+' [%s%s]'%(len(self.sortcols)>1 and self.sortcols.index(col_index) + 1 or '', 
                                 self.sortdir>0 and 'v' or '^') 
        return col

    def get_all_column_names(self):
        '''returns all (hidden and shown) column names in this table.
        '''
        return self.col_labels.tolist()

    def IsEmptyCell(self, row, col):
        return False

    def GetValue(self, row, col):
        return self.ordered_data[row,col]

    def SetValue(self, row, col, value):
        logging.warn('You can not edit this table.')
        pass
    
    def GetColValues(self, col):
        return self.ordered_data[:,col]
    
    def set_sort_col(self, col_index, add=False):
        '''Set the column to sort this table by. If add is true, this column
        will be added to the end of the existing sort order (or removed from the
        sort order if it is already present.)
        '''
        if not add:
            if len(self.sortcols)>0 and col_index in self.sortcols:
                # If this column is already sorted, flip it
                self.row_order = self.row_order[::-1]
                self.sortdir = -self.sortdir
            else:
                self.sortdir = 1
                self.sortcols = [col_index]
                # If this column hasn't been sorted yet, then sort descending
                self.row_order = np.lexsort(self.data[:,self.col_order][:,self.sortcols[::-1]].T.tolist())
        else:
            if len(self.sortcols)>0 and col_index in self.sortcols:
                self.sortcols.remove(col_index)
            else:
                self.sortcols += [col_index]
            if self.sortcols==[]:
                # if all sort columns have been toggled off, reset row_order
                self.row_order = np.arange(self.data.shape[0])
            else:
                self.row_order = np.lexsort(self.data[:,self.sortcols[::-1]].T.tolist())
        self.ordered_data = self.data[self.row_order,:][:,self.col_order]
         
    def GetRowLabelValue(self, row):
        if self.row_labels is not None:
            return self.row_labels[row]
        else:
            return '*'

class DBTable(TableData):
    '''
    Interface connecting the table grid GUI to the database tables.
    '''
    def __init__(self, table_name, rmin=None, rmax=None):
        self.grouping = None
        self.set_table(table_name)
        self.filter = '' #'WHERE Image_Intensity_Actin_Total_intensity > 17000'
        self.set_row_interval(rmin, rmax)
        #XXX: should filter be defined at a higher level? Just UI?
        TableData.__init__(self)
        
    def set_table(self, table_name):
        if table_name == p.image_table:
            self.grouping = 'Image'
        elif table_name == p.object_table:
            self.grouping = 'Object'
        else:
            self.grouping = None
        self.table_name = table_name
        self.cache = {}
        self.col_labels = np.array(db.GetColumnNames(self.table_name))
        self.shown_columns = np.arange(len(self.col_labels))
        self.order_by = [self.col_labels[0]]
        self.order_direction = 'ASC'
        self.key_indices = None
        if self.table_name == p.image_table:
            self.key_indices = [self.col_labels.tolist().index(v) for v in dbconnect.image_key_columns()]
        if self.table_name == p.object_table:
            self.key_indices = [self.col_labels.tolist().index(v) for v in dbconnect.object_key_columns()]
            
    def set_shown_columns(self, col_indices):
        '''sets which column should be shown from the db table
        
        col_indices -- the indices of the columns to show (all others will be 
                       hidden)
        '''
        self.shown_columns = col_indices
        self.cache.clear()
    
    def set_sort_col(self, col_index, add=False):
        col = self.col_labels[col_index]
        if add:
            if col in self.order_by:
                self.order_by.remove(col)
                if self.order_by == []:
                    self.order_by = [self.col_labels[0]]
            else:
                self.order_by += [col]
        else:
            if col in self.order_by:
                if self.order_direction == 'ASC':
                    self.order_direction = 'DESC'
                else:
                    self.order_direction = 'ASC'
            else:
                self.order_by = [col]
        self.cache.clear()
    
    def set_row_interval(self, rmin, rmax):
        self.cache.clear()
        if rmin == None: 
            rmin = 0
        if rmax == None: 
            rmax = self.get_total_number_of_rows()
        try:
            int(rmin)
            int(rmax)
        except:
            raise ValueError('Invalid row interval, values must be positive numbers.')
        self.rmin = rmin
        self.rmax = rmax
        
    def get_row_key(self, row):
        if self.key_indices is None:
            return None
        cols = ','.join(self.col_labels[self.key_indices])
        key = db.execute('SELECT %s FROM %s %s ORDER BY %s LIMIT %s,%s'%
                          (cols, self.table_name, self.filter, 
                           ','.join([c+' '+self.order_direction for c in self.order_by]),
                           row, 1))[0]
        return key
    
    def get_image_keys_at_row(self, row):
        # XXX: needs to be updated to work for per_well data
        if self.table_name == p.image_table:
            key = self.get_row_key(row)
            if key is None:
                return None
            return [key]
#            return [tuple([self.GetValue(row, col) for col in self.key_indices])]
        elif self.table_name == p.object_table:
            key = self.get_row_key(row)
            if key is None:
                return None
            return [key[:-1]]
        else:
            # BAD: assumes that columns with the same name as the image key 
            #    columns ARE image key columns (not true if looking at unrelated 
            #    image table)
            key = []
            for col in dbconnect.image_key_columns():
                if col not in self.col_labels:
                    return None
                else:
                    col_index = self.col_labels.tolist().index(col)
                    key += [self.GetValue(row, col_index)]
            return [tuple(key)]
    
    def get_object_keys_at_row(self, row):
        # XXX: needs to be updated to work for per_well data
        if self.table_name == p.image_table:
            # return all objects in this image
            key = self.get_row_key(row)
            if key is None:
                return None
            dm = DataModel()
            n_objects = dm.GetObjectCountFromImage(key)
            return [tuple(list(key) + [i]) for i in range(n_objects)]
        elif self.table_name == p.object_table:
            key = self.get_row_key(row)
            if key is None:
                return None
            return [key]
        else:
            key = []
            for col in dbconnect.object_key_columns():
                if col not in self.col_labels:
                    return None
                else:
                    col_index = self.col_labels.tolist().index(col)
                    key += [self.GetValue(row, col_index)]
            return [tuple(key)]

    def get_total_number_of_rows(self):
        '''Returns the total number of rows in the database
        '''
        return int(db.execute('SELECT COUNT(*) FROM %s %s' % (self.table_name, self.filter))[0][0])
    
    def GetNumberRows(self):
        '''Returns the number of rows on the current page (between rmin,rmax)
        '''
        total = self.get_total_number_of_rows()
        if self.rmax and self.rmin:
            return min(self.rmax, total) - self.rmin + 1
        else:
            return total
    
    def GetNumberCols(self):
        return len(self.shown_columns)
    
    def GetColLabelValueWithoutDecoration(self, col_index):
        '''returns the column label at a given index (without ^,v decoration)
        Note: this does not return hidden column labels
        '''
        return self.col_labels[self.shown_columns][col_index]
    
    def GetColLabelValue(self, col_index):
        '''returns the column label at a given index (for display)
        '''
        col = self.col_labels[self.shown_columns][col_index]
        if col in self.order_by:
            return col+' [%s%s]'%(len(self.order_by)>1 and self.order_by.index(col) + 1 or '', 
                                 self.order_direction=='ASC' and 'v' or '^') 
        return col
    
    def get_all_column_names(self):
        '''returns all (hidden and shown) column names in this table.
        '''
        return db.GetColumnNames(self.table_name)
    
    def get_key_cols(self):
        '''Returns a list of the key column names or None if none are specified.
        '''
        if self.key_indices is not None:
            return self.col_labels[self.key_indices].tolist()
        else:
            return None

    def GetValue(self, row, col):
        row += self.rmin
        if not row in self.cache:
            lo = max(row - 25, 0)
            hi = row + 25
            cols = ','.join(self.col_labels[self.shown_columns])
            vals = db.execute('SELECT %s FROM %s %s ORDER BY %s LIMIT %s,%s'%
                              (cols, self.table_name, self.filter, 
                               ','.join([c+' '+self.order_direction for c in self.order_by]),
                               lo, hi-lo), 
                              silent=False)
            self.cache.update((lo+i, v) for i,v in enumerate(vals))
            # if cache exceeds 1000 entries, clip to last 500
            if len(self.cache) > 5000:
                for key in list(self.cache.keys())[:-500]:
                    del self.cache[key]
        return self.cache[row][col]

    def SetValue(self, row, col, value):
        print(('SetValue(%d, %d, "%s") ignored.\n' % (row, col, value)))
        
    def GetColValues(self, col):
        colname = self.col_labels[self.shown_columns][col]
        vals = db.execute('SELECT %s FROM %s %s ORDER BY %s'%
                          (colname, self.table_name, self.filter, 
                           ','.join([c+' '+self.order_direction for c in self.order_by])), 
                          silent=False)
        return np.array(vals).flatten()

    def GetRowLabelValue(self, row):
        return '*'


class TableViewer(wx.Frame):
    '''
    Frame containing the data grid, and UI tools that operate on it.
    '''
    def __init__(self, parent, **kwargs):
        wx.Frame.__init__(self, parent, -1, size=(640,480), **kwargs)
##        CPATool.__init__(self)
        
        self.selected_cols = set([])
        
        # Toolbar
##        from guiutils import FilterComboBox
##        tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
##        self.filter_choice = FilterComboBox(self)
##        tb.AddControl(self.filter_choice)
##        tb.Realize()
        
        #
        # Create the menubar
        #
        self.SetMenuBar(wx.MenuBar())
        file_menu = wx.Menu()
        self.GetMenuBar().Append(file_menu, 'File')
        new_table_item = file_menu.Append(-1, 'New empty table\tCtrl+N')
        file_menu.AppendSeparator()
        load_csv_menu_item = file_menu.Append(-1, 'Load table from CSV\tCtrl+O')
        load_db_table_menu_item = file_menu.Append(-1, 'Load table from database\tCtrl+Shift+O')
        file_menu.AppendSeparator()
        save_csv_menu_item = file_menu.Append(-1, 'Save table to CSV\tCtrl+S')
        save_temp_table_menu_item = file_menu.Append(-1, 'Save table to database\tCtrl+Shift+S')

##        table_menu = wx.Menu()
##        self.GetMenuBar().Append(table_menu, 'Table')
##        pca_menu_item = table_menu.Append(-1, 'Compute PCA on current table',
##                            help='Performs Principal Component Analysis on '
##                            'the current table and creates a new table with '
##                            'the resulting columns.')
##        tsne_menu_item = table_menu.Append(-1, 'Compute t-SNE on current table',
##                            help='Performs t-Distributed Stochastic Neighbor '
##                            'Embedding on the current table and creates a new '
##                            'table with the resulting columns.')
        
        view_menu = wx.Menu()
        self.GetMenuBar().Append(view_menu, 'View')
        column_width_menu = wx.Menu()
        show_hide_cols_item = view_menu.Append(-1, 'Show/Hide columns')
        view_menu.Append(-1, 'Column widths', column_width_menu)
        fixed_cols_menu_item = column_width_menu.Append(-1, 'Fixed width', kind=wx.ITEM_RADIO)
        fit_cols_menu_item = column_width_menu.Append(-1, 'Fit to table', kind=wx.ITEM_RADIO)
        auto_cols_menu_item = column_width_menu.Append(-1, 'Auto width', kind=wx.ITEM_RADIO)

        self.GetMenuBar().Append(cpa.helpmenu.make_help_menu(self, manual_url="6_table_viewer.html"), 'Help')
        
        self.status_bar = create_status_bar(self)
        
        self.Bind(wx.EVT_MENU, self.on_new_table, new_table_item)
        self.Bind(wx.EVT_MENU, self.on_load_csv, load_csv_menu_item)
        self.Bind(wx.EVT_MENU, self.on_load_db_table, load_db_table_menu_item)
        self.Bind(wx.EVT_MENU, self.on_save_csv, save_csv_menu_item)
        self.Bind(wx.EVT_MENU, self.on_save_table_to_db, save_temp_table_menu_item)
        self.Bind(wx.EVT_MENU, self.on_show_hide_cols, show_hide_cols_item)
        self.Bind(wx.EVT_MENU, self.on_set_fixed_col_widths, fixed_cols_menu_item)
        self.Bind(wx.EVT_MENU, self.on_set_fitted_col_widths, fit_cols_menu_item)
        self.Bind(wx.EVT_MENU, self.on_set_auto_col_widths, auto_cols_menu_item)
##        self.Bind(wx.EVT_MENU, self.on_compute_tsne, tsne_menu_item)
        
        #
        # Create the grid
        #
        self.grid = gridlib.Grid(self)
        self.grid.SetRowLabelSize(ROW_LABEL_SIZE)
        self.grid.DisableCellEditControl()
        self.grid.EnableEditing(False)
        self.grid.SetCellHighlightPenWidth(0)
        # Help prevent spurious horizontal scrollbar
        self.grid.SetMargins(0-wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X),
                             0-wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y))
        self.grid.SetRowLabelSize(ROW_LABEL_SIZE)

        self.grid.Bind(gridlib.EVT_GRID_CMD_LABEL_LEFT_CLICK, self.on_leftclick_label)
        self.grid.Bind(gridlib.EVT_GRID_LABEL_LEFT_DCLICK, self.on_dclick_label)
        self.grid.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.on_rightclick_label)
        self.grid.Bind(gridlib.EVT_GRID_SELECT_CELL, self.on_select_cell)
        self.grid.Bind(gridlib.EVT_GRID_RANGE_SELECT, self.on_select_range)

##    def on_select_filter(self, evt):
##        #
##        #  CONSTRUCTION (add filters to dbtable), ignore for plaintable
##        #
##        self.grid.set_filter( self.filter_choice.GetStringSelection() )
        
    def on_select_cell(self, evt):
        evt.Skip()
    
    def on_select_range(self, evt):
        cols = set(range(evt.GetLeftCol(), evt.GetRightCol() + 1))
        # update the selection
        if evt.Selecting():
            self.selected_cols.update(cols)
        else:
            self.selected_cols.difference_update(cols)
        try:
            # try to summarize selected columns
            n, m = self.grid.Table.GetNumberRows(), len(self.selected_cols)
            block = np.empty((n, m))
            for k, j in enumerate(self.selected_cols):
                block[:,k] = self.grid.Table.GetColValues(j)
                self.SetStatusText("Sum: %f — Mean: %f — Std: %f" %
                                               (block.sum(), block.mean(), block.std()))
        except:
            self.SetStatusText("Cannot summarize columns.")

    def on_show_hide_cols(self, evt):
        column_names = self.grid.Table.get_all_column_names()
        dlg = wx.MultiChoiceDialog(self, 
                                   'Select the columns you would like to show',
                                   'Show/Hide Columns', column_names)
        dlg.SetSelections(self.grid.Table.shown_columns)
        if (dlg.ShowModal() == wx.ID_OK):
            selections = dlg.GetSelections()
            self.grid.Table.set_shown_columns(selections)
            self.grid.Table.ResetView(self.grid)
        
    def on_set_fixed_col_widths(self, evt):
        self.set_fixed_col_widths()
    def set_fixed_col_widths(self):
        self.Disconnect(-1, -1, wx.wxEVT_SIZE)
        print(('default ', gridlib.GRID_DEFAULT_COL_WIDTH))
        self.grid.SetDefaultColSize(gridlib.GRID_DEFAULT_COL_WIDTH, True)
        self.Refresh()

    def on_set_auto_col_widths(self, evt):
        self.set_auto_col_widths()
    def set_auto_col_widths(self):
        self.Disconnect(-1, -1, wx.wxEVT_SIZE)
        self.grid.AutoSize()
        self.Refresh()

    def on_set_fitted_col_widths(self, evt):
        self.set_fitted_col_widths()
    def set_fitted_col_widths(self):
        # Note: I disconnect EVT_SIZE before binding in case it's already bound.
        # Otherwise it will get bound twice and set_fixed_col_widths won't work 
        # unless called twice.
        self.Disconnect(-1, -1, wx.wxEVT_SIZE)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.RescaleGrid()
        
    # TODO:
    def on_compute_tsne(self, evt):
        '''Performs t-distributed stochastic neighbor embedding on the numeric
        columns of the current table and saves the resulting columns to a new 
        table.
        '''
        import calc_tsne
        data = [[self.grid.Table.GetValue(row, col) 
                for col in range(self.grid.Table.GetNumberCols())]
                for row in range(self.grid.Table.GetNumberRows())]
        data = np.array(data)
        if self.grid.Table.get_key_cols is None:
            wx.MessageDialog(self, 'The current table does not have key columns defined',
                                 'key columns required', wx.OK|wx.ICON_INFORMATION).ShowModal()
            return
        res = calc_tsne.calc_tsne(data)
        #XXX: add key cols to results
        db.CreateTableFromData(res, 
                               self.grid.Table.get_key_cols()+['a','b'], 
                               'tSNE', 
                               temporary=True)
##        db.execute('DROP TABLE IF EXISTS tSNE')
##        db.execute('CREATE TABLE tSNE(ImageNumber int, a FLOAT, b FLOAT)')
##        i = 1
##        for a,b in res:
##            db.execute('INSERT INTO tSNE (ImageNumber, a, b) VALUES(%s, %s, %s)'%(i,a,b))
##            i += 1
        wx.GetApp().user_tables = ['tSNE']

    def table_from_array(self, data, col_labels=None, grouping=None, key_indices=None):
        '''Populates the grid with the given data.
        data -- 2d array of data
        col_labels -- labels for each column
        grouping -- group name for linking to images
        key_indices -- indices of the key columns
        '''
        table_base = PlainTable(self, data, col_labels, key_indices, grouping)
        self.grid.SetTable(table_base, True)
        self.grid.SetSelectionMode(self.grid.GridSelectColumns)

    def on_new_table(self, evt=None):
        '''Prompts user to for table dimensions and creates the table.
        '''
        user_is_stupid = True
        while user_is_stupid:
            dlg = wx.TextEntryDialog(
                self, 'How many columns?', 'How many columns?', '10')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    cols = int(dlg.GetValue())
                    if 1 <= cols <= 1000: user_is_stupid = False
                    else: 
                        raise ValueError('You must enter a value between 1 and 1000')
                except:
                    raise ValueError('You must enter a value between 1 and 1000')
            else:
                return
        user_is_stupid = True
        while user_is_stupid:
            dlg = wx.TextEntryDialog(
                self, 'How many rows?', 'How many rows?', '1000')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    rows = int(dlg.GetValue())
                    if 1 <= rows <= 100000: user_is_stupid = False
                    else: raise ValueError('You must enter a value between 1 and 100000')
                except:
                    raise ValueError('You must enter a value between 1 and 100000')
            else:
                return
        pos = (self.Position[0]+10, self.Position[1]+10)
        frame = TableViewer(self.Parent, pos=pos)
        frame.Show(True)
        frame.new_blank_table(rows, cols)
        frame.SetTitle('New_Table')
        if self.GetTitle() == "":
            self.Destroy()
        self.grid.SetSelectionMode(self.grid.GridSelectColumns)
        
    def new_blank_table(self, rows, cols):
        '''Sort of pointless since the table can't be edited... yet.
        '''
        data = np.array([''] * (rows * cols)).reshape((rows, cols))
        table_base = PlainTable(self, data)
        self.grid.SetTable(table_base, True)
        self.RescaleGrid()
        self.grid.SetSelectionMode(self.grid.GridSelectColumns)
        
    def on_load_db_table(self, evt=None):
        from .guiutils import TableSelectionDialog
        dlg = TableSelectionDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            table_name = dlg.GetStringSelection()
            pos = (self.Position[0]+10, self.Position[1]+10)
            frame = TableViewer(self.Parent, pos=pos)
            frame.Show(True)
            frame.load_db_table(table_name)
            if self.GetTitle() == "":
                self.Destroy()


    def load_db_table(self, tablename):
        '''Populates the grid with the data found in a given table.
        '''
        table_base = DBTable(tablename)
        self.grid.SetTable(table_base, True)
        self.SetTitle(tablename)
        self.RescaleGrid()
        self.grid.SetSelectionMode(self.grid.GridSelectColumns)

    def on_load_csv(self, evt=None):
        '''Prompts the user for a csv file and loads it.
        '''
        dlg = wx.FileDialog(self, message='Choose a CSV file to load',
                            defaultDir=os.getcwd(),
                            wildcard='CSV files (*.csv)|*.csv',
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            pos = (self.Position[0]+10, self.Position[1]+10)
            frame = TableViewer(self.Parent, pos=pos)
            frame.Show(True)
            frame.load_csv(filename)
            if self.GetTitle() == "":
                self.Destroy()
            
    def load_csv(self, filename):
        '''Populates the grid with the the data in a CSV file.
        filename -- the path to a CSV file to load
        '''
        #
        # XXX: try using linecache so we don't need to load the whole file.
        #
        
        # infer types
        r = csv.reader(open(filename))
        dtable = dbconnect.get_data_table_from_csv_reader(r)
        first_row_types = db.InferColTypesFromData([dtable[0]], len(dtable[0]))
        coltypes = db.InferColTypesFromData(dtable[1:], len(dtable[0]))
        has_header_row = False
        if (not all([a == b for a, b in zip(first_row_types, coltypes)]) and 
            all([a.startswith('VARCHAR') for a in first_row_types]) and
            not all([b.startswith('VARCHAR') for b in coltypes])):
            has_header_row = True
        for i in range(len(coltypes)):
            if coltypes[i] == 'INT': coltypes[i] = int
            elif coltypes[i] == 'FLOAT': coltypes[i] = np.float32
            else: coltypes[i] = str
        # read data
        r = csv.reader(open(filename))
        if has_header_row:
            labels = next(r)
        else:
            labels = None
        data = []
        for row in r:
            data += [[coltypes[i](v) for i,v in enumerate(row)]]
        data = np.array(data, dtype=object)
        
        table_base = PlainTable(self, data, labels)
        self.grid.SetTable(table_base, True)
        self.grid.Refresh()
        self.SetTitle(filename)
        self.RescaleGrid()
        self.grid.SetSelectionMode(self.grid.GridSelectColumns)

    def on_leftclick_label(self, evt):
        if evt.Col >= 0:
            self.grid.Table.set_sort_col(evt.Col, add=evt.ShiftDown())
            self.grid.Refresh()
##        elif evt.Row >= 0:
##            self.grid.SetSelectionMode(self.grid.wxGridSelectRows)
##            self.grid.SelectRow(evt.Row)
##            self.on_rightclick_label(evt)

    def on_rightclick_label(self, evt):
        if evt.Row >= 0:
            keys = self.grid.Table.get_image_keys_at_row(evt.Row)
            if keys:
                self.show_popup_menu(keys, evt.GetPosition())
            #XXX: Need to prompt user intelligently about linking their table
            #     Could check for known cols (imkey or wellkey) and go from there
##            elif keys is None:
##                dlg = wx.MultiChoiceDialog(self, 
##                    'Can not display images from this table because it has not '
##                    'been linked to your per-image table. Select the ',
##                    'Select Key Columns', column_names)
##                if dlg.ShowModal() == wx.ID_OK:


    def show_popup_menu(self, items, pos):
        self.popupItemById = {}
        menu = wx.Menu()
        menu.SetTitle('Show Image:')
        for item in items:
            id = wx.NewId()
            self.popupItemById[id] = item
            menu.Append(id,str(item))
        menu.Bind(wx.EVT_MENU, self.on_select_image_from_popup)
        self.PopupMenu(menu, pos)

    def on_select_image_from_popup(self, evt):
        '''Handle selections from the popup menu.
        '''
        imkey = self.popupItemById[evt.GetId()]
        imagetools.ShowImage(imkey, p.image_channel_colors, parent=self)

    def on_dclick_label(self, evt):
        '''Handle display of images and objects'''
        if evt.Row >= 0:
            obkeys = self.grid.Table.get_object_keys_at_row(evt.Row)
            if self.grid.Table.grouping is None:
                # We need to know how the table is grouped to know what to do
                logging.warn('CPA does not know how to link this table to your images. Can\'t launch ImageViewer.')
                return
            elif self.grid.Table.grouping.lower() == 'object':
                # For per-object grouping, show the objects in the image
                imview = imagetools.ShowImage(obkeys[0][:-1], 
                                                  p.image_channel_colors,
                                                  parent=self.Parent)
                if obkeys is not None:
                    for obkey in obkeys:
                        imview.SelectObject(obkey)
            elif self.grid.Table.grouping.lower() == 'image':
                # For per-image grouping just show the images.
                # If there is only one object, then highlight it
                if obkeys is not None and len(obkeys) == 1:
                    imview = imagetools.ShowImage(obkeys[0][:-1], 
                                                  p.image_channel_colors,
                                                  parent=self.Parent)
                    imview.SelectObject(obkeys[0])
                else:
                    imkeys = self.grid.Table.get_image_keys_at_row(evt.Row)
                    if imkeys:
                        #XXX: warn if there are a lot
                        for imkey in imkeys:
                            imagetools.ShowImage(imkey, p.image_channel_colors,
                                                 parent=self.Parent)
            else:
                key_cols = self.grid.Table.get_row_key(evt.Row)
                if key_cols:
                    dm = DataModel()
                    imkeys = dm.GetImagesInGroup(self.grid.Table.grouping, key_cols)
                    for imkey in imkeys:
                        imagetools.ShowImage(imkey, p.image_channel_colors,
                                             parent=self.Parent)

    def on_save_csv(self, evt):
        defaultFileName = 'my_table.csv'
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
        f = open(filename, 'w', newline="")
        w = csv.writer(f)
        w.writerow([self.grid.Table.GetColLabelValueWithoutDecoration(col) 
                    for col in range(self.grid.Table.GetNumberCols())])
        for row in range(self.grid.Table.GetNumberRows()):
            w.writerow([self.grid.Table.GetValue(row, col) 
                        for col in range(self.grid.Table.GetNumberCols())])
        f.close()
        logging.info('Table saved to %s'%filename)

    def on_save_table_to_db(self, evt):
        valid = False
        while not valid:
            dlg = wx.TextEntryDialog(self, 'What do you want to name your table?', 
                            'Save table to database', self.Title)
            if dlg.ShowModal() != wx.ID_OK:
                return
            tablename = dlg.GetValue()
            if not re.match('^[A-Za-z]\w*$', tablename):
                wx.MessageDialog(self, 'Table name must begin with a letter and may'
                                 'only contain letters, digits and "_"',
                                 'Invalid table name', wx.OK|wx.ICON_INFORMATION).ShowModal()
            elif db.table_exists(tablename):
                dlg = wx.MessageDialog(self, 
                    'The table "%s" already exists in the database. Overwrite it?'%(tablename),
                    'Table already exists', wx.YES_NO|wx.NO_DEFAULT|wx.ICON_WARNING)
                if dlg.ShowModal() == wx.ID_YES:
                    valid = True
            else:
                valid = True
                
        dlg = wx.SingleChoiceDialog(self, 'Do you want to be able to access\n'
                'this table after you close CPA?', 'Save table to database',
                ['Store for this session only.', 'Store permanently.'], 
                wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() != wx.ID_OK:
            return
        temporary = (dlg.GetSelection() == 0)
        
        colnames = [self.grid.Table.GetColLabelValueWithoutDecoration(col) 
                    for col in range(self.grid.Table.GetNumberCols())]
        data = [[self.grid.Table.GetValue(row, col) 
                for col in range(self.grid.Table.GetNumberCols())]
                for row in range(self.grid.Table.GetNumberRows())]
        db.CreateTableFromData(data, colnames,
                               tablename, temporary=temporary)
        self.Title = tablename
        try:
            wx.GetApp().user_tables += [tablename]
            for plot in wx.GetApp().get_plots():
                if plot.tool_name == 'PlateViewer':
                    plot.AddTableChoice(tablename)
        except AttributeError:
            # running without main UI
            user_tables = wx.GetApp().user_tables = []
            
    def get_table_data(self):
        data = [[self.grid.Table.GetValue(row, col) 
                 for col in range(self.grid.Table.GetNumberCols())]
                for row in range(self.grid.Table.GetNumberRows())]
        return data

    def on_size(self, evt):
        if not self.grid:
            return
        # HACK CITY: Trying to fix spurious horizontal scrollbar
        adjustment = ROW_LABEL_SIZE
        if self.grid.GetScrollRange(wx.VERTICAL) > 0:
            adjustment = wx.SYS_VSCROLL_ARROW_X #+ 12
        cw = (evt.Size[0] - adjustment) / self.grid.Table.GetNumberCols()
        self.grid.SetDefaultColSize(cw, True)
        evt.Skip()
        
    def RescaleGrid(self):
        # Hack: resize window so the grid resizes to fit
        self.Size = self.Size+(1,1)
        self.Size = self.Size-(1,1)
        
    def save_settings(self):
        '''save_settings is called when saving a workspace to file.
        
        returns a dictionary mapping setting names to values encoded as strings
        '''
        pass
##        return {'table' : self.grid.Table.get_table(),
##                'sort_cols' : self.grid.Table.get_sort_cols(),
##                'row_interval' : self.grid.Table.get_row_interval(),
##                }
        
    def load_settings(self, settings):
        '''load_settings is called when loading a workspace from file.
        
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
        pass
    
    
def show_loaddata_table(gate_names, as_columns=True):
    '''Utility function to create a table that can be read by CP LoadData.
    gate_names -- list of gate names to apply
    as_columns -- use True to output each gate as a column with 0's and 1's
                  use False to output only the rows that fall within all gates.
    '''
    for g in gate_names:
        for t in p.gates[g].get_tables():
            assert t == p.image_table, 'this function only takes per-image gates'
    wellkeys = dbconnect.well_key_columns()
    if wellkeys is None:
        wellkeys = ()
    columns = list(dbconnect.image_key_columns() + wellkeys) + p.image_file_cols + p.image_path_cols
    if as_columns:
        query_columns = columns + ['(%s) AS %s'%(str(p.gates[g]), g) for g in gate_names]
        columns += gate_names
        data = db.execute('SELECT %s FROM %s'
                          %(','.join(query_columns), p.image_table))
    else:
        # display only values within the given gates
        where_clause = ' AND '.join([str(p.gates[g]) for g in gate_names])
        data = db.execute('SELECT %s FROM %s WHERE %s'
                          %(','.join(columns), p.image_table, where_clause))
    if data == []:
        wx.MessageBox('Sorry, no data points fall within the combined selected gates.', 'No data to show')
        return None
    grid = TableViewer(None, title="Gated Data")
    grid.table_from_array(np.array(data, dtype='object'), columns, grouping='image', 
                          key_indices=list(range(len(dbconnect.image_key_columns()))))
    grid.Show()
    return grid


if __name__ == '__main__':
    app = wx.App()
    logging.basicConfig(level=logging.DEBUG,)
    if p.show_load_dialog():
        frame = TableViewer(None)
        frame.Show(True)
        frame.load_db_table(p.image_table)
##        show_loaddata_table(p.gates.keys(), True)
##        show_loaddata_table(p.gates.keys(), False)
        
    app.MainLoop()
