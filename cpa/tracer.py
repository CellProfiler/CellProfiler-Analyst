'''
Dependencies:
Enthought Tool Suite (for Mayavi2): http://www.lfd.uci.edu/~gohlke/pythonlibs/#ets
VTK (5.10+): http://www.lfd.uci.edu/~gohlke/pythonlibs/#vtk
NetworkX (1.7+): http://www.lfd.uci.edu/~gohlke/pythonlibs/#networkx
NumPy-MKL (1.71+): http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
configobj (required by Enthought): https://pypi.python.org/pypi/configobj
'''
import wx
from wx.combo import OwnerDrawnComboBox as ComboBox
from wx.lib.scrolledpanel import ScrolledPanel
import networkx as nx
import numpy as np
import hashlib
from operator import itemgetter
import glayout

import logging
import time
import sortbin
import imagetools
from guiutils import get_main_frame_or_none
from dbconnect import DBConnect, image_key_columns, object_key_columns
from properties import Properties
from cpatool import CPATool
import tableviewer
from columnfilter import ColumnFilterDialog

import matplotlib
from matplotlib import gridspec
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from textwrap import wrap

# traits imports
from traits.api import HasTraits, Int, Instance, on_trait_change
from traitsui.api import View, Item, HSplit, Group

# mayavi imports
from mayavi import mlab
from mayavi.core.ui.api import MlabSceneModel, SceneEditor
from mayavi.core import lut_manager
from mayavi.core.ui.mayavi_scene import MayaviScene
from tvtk.pyface.scene import Scene
from tvtk.api import tvtk

#
# Monkey-patch ComboBox.GetStringSelection()
#   self.Selection returns a tuple instead of a single value
#   and things probably go downhill from there.
#
def __GetStringSelection(self):
    sel = self.Selection[0]
    items = self.GetItems()
    if sel >= 0 and sel < len(items):
        return items[sel]
ComboBox.GetStringSelection = __GetStringSelection

required_fields = ['series_id', 'group_id', 'timepoint_id']

db = DBConnect.getInstance()
props = Properties.getInstance()

TRACKING_MODULE_NAME = "TrackObjects"
OTHER_METRICS = "Other derived metrics..."
L_YCOORD = "Y_2"
L_TCOORD = "T_2"
T_XCOORD = "X_3"
T_YCOORD = "Y_3"
T_TCOORD = "T_3"
SCALAR_VAL = "S"
VISIBLE = "VISIBLE"
COMPONENT_ID = "Component_ID"
track_attributes = ["x","y","t",SCALAR_VAL]

SUBGRAPH_ID = "Subgraph"

VISIBLE_SUFFIX = "_VISIBLE"
METRIC_BC = "BetweennessCentrality"
METRIC_BC_VISIBLE = METRIC_BC + VISIBLE_SUFFIX

METRIC_SINGLETONS = "Singletons"
METRIC_SINGLETONS_VISIBLE = METRIC_SINGLETONS + VISIBLE_SUFFIX

METRIC_NODESWITHINDIST = "NodesWithinDistanceCutoff"
METRIC_NODESWITHINDIST_VISIBLE = METRIC_NODESWITHINDIST + VISIBLE_SUFFIX

METRIC_LOOPS = "Loops"
METRIC_LOOPS_VISIBLE = METRIC_LOOPS + VISIBLE_SUFFIX

METRIC_CROSSINGS = 'Crossings'
METRIC_CROSSINGS_VISIBLE = METRIC_CROSSINGS + VISIBLE_SUFFIX

BRANCH_NODES = "Branch_node"
END_NODES = "End_node"
START_NODES = "Start_node"
TERMINAL_NODES = "Terminal_node"
FINISH_NODES = "Finish_node"
IS_REMOVED = "Is_removed"

EDITED_TABLE_SUFFIX = "_Edits"
ORIGINAL_TRACK = "Original"
EDGE_TBL_ID = "edges"
NODE_TBL_ID = "nodes"

def add_props_field(props):
    # Temp declarations; these will be retrieved from the properties file directly, eventually
    props.series_id = ["Image_Group_Number"]
    #props.series_id = ["Image_Metadata_Plate"]
    props.group_id = "Image_Group_Number"
    props.timepoint_id = "Image_Group_Index"
    
    if props.db_type == 'sqlite':
        query = "PRAGMA table_info(%s)"%(props.image_table)
        all_fields = [item[1] for item in db.execute(query)]
    else:
        query = "SELECT column_name FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(props.db_name, props.image_table)
        all_fields = [item[0] for item in db.execute(query)]    

    # Check if the appropriate cols exist in the object table
    defined_tables = {_:False for _ in props.series_id}
    defined_tables[props.group_id] = False
    defined_tables[props.timepoint_id] = False
    success = True
    for key in defined_tables.keys():
        if key not in all_fields:
            success = False
            message = "A '%s' column is required in the image table for Tracer."%(key)
            wx.MessageBox(message,'Required image table column missing')
            logging.error(message)
            break        
    
    obj = get_object_name() 
    # TODO: Allow for selection of tracking labels, since there may be multiple objects tracked in different ways. Right now, just pick the first one.
    # TODO: Allow for selection of parent image/object fields, since there may be multiple tracked objects. Right now, just pick the first one.
    if props.db_type == 'sqlite':
        query = "PRAGMA table_info(%s)"%(props.object_table)
        all_fields = [item[1] for item in db.execute(query)]
    else:
        query = "SELECT column_name FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(props.db_name, props.object_table)
        all_fields = [item[0] for item in db.execute(query)]
    
    table_prefix = props.image_table[:props.image_table.lower().find("per_image")]
    props.relationship_table = table_prefix + "Per_Relationships"
    props.relationshiptypes_table = table_prefix + "Per_RelationshipTypes"
    props.relationships_view = table_prefix + "Per_RelationshipsView"
    
    # Check if the appropriate tables/views exist
    defined_tables = {props.relationship_table:False, props.relationshiptypes_table:False, props.relationships_view:False}
    for key in defined_tables.keys():
        if props.db_type == 'sqlite':
            query = "PRAGMA table_info(%s)"%(key)
            defined_tables[key] = len([item[1] for item in db.execute(query)]) > 0
        else:
            query = "SELECT * FROM information_schema.tables WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(props.db_name,key)
            defined_tables[key] = len([item[0] for item in db.execute(query)]) > 0
    
    success = True
    if not all(defined_tables.values()):
        success = False
        message = " ".join(('The tables/views',
                           '%s'%(", ".join([_[0] for _ in defined_tables.items() if not _[1]])),
                           'are required in the database for Tracer.'))
        wx.MessageBox(message,'Required tables missing')
        logging.error(message)      

    return props, success

def retrieve_datasets():
    #TODO: Decide if this approach or the relationship table should be used
    series_list = ",".join(props.series_id)
    query = "SELECT %s FROM %s GROUP BY %s"%(series_list,props.image_table,series_list)
    available_datasets = [x[0] for x in db.execute(query)]
    return available_datasets

def get_object_name():
    return props.cell_x_loc.split('_Location_Center')[0]

def get_edited_relationship_tablenames():
    return {EDGE_TBL_ID: "_".join(("",EDGE_TBL_ID,props.relationship_table.split('_Per')[0])),
            NODE_TBL_ID: "_".join(("",NODE_TBL_ID,props.relationship_table.split('_Per')[0]))}

def is_LAP_tracking_data():
    # If the data is LAP-based, then additional button(s) show up
    LAP_field = "Kalman"
    if props.db_type == 'sqlite':
        query = "PRAGMA table_info(%s)"%(props.object_table)
        return(len([item[1] for item in db.execute(query) if item[1].find(LAP_field) != -1]) > 0)
    else:
        query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP '_Kalman_'"%(props.db_name, props.object_table)
        return(len(db.execute(query)) > 0)
    
def where_stmt_for_tracked_objects(obj, group_id, selected_dataset):
    # We want relationships that are cover the following:
    # - Are parent/child, e.g, exclude neighborhood
    # - Share the same parent/child object, e.g, exclude primary/secondary/tertiary, some cases of neighborhood
    # - Are across-frame, e.g, exclude neighborhood, primary/secondary/tertiary
    # - For the selected dataset        
    stmt = ("LOWER(relationship) = 'parent'", 
            "AND object_name1 = '%s'"%(obj),
            "AND object_name1 = object_name2",
            "AND image_number1 != image_number2",
            "AND i1.%s = %d"%(group_id,selected_dataset)
            )
    return stmt    

def does_table_exist(table_name):
    if props.db_type == 'sqlite':
        query = "PRAGMA table_info(%s)"%(table_name)
    else:
        query = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(props.db_name, table_name)
    return len(db.execute(query)) > 0    
    
def create_update_relationship_tables():
    
    reln_cols = {EDGE_TBL_ID:['image_number1', 'object_number1', 'image_number2', 'object_number2'],
                 NODE_TBL_ID:['image_number', 'object_number']}    
        
    def create_table_hash():
        query = "SELECT * FROM %s"%(props.relationship_table)
        h = hashlib.sha1()
        h.update(repr(db.execute(query)))
        d = np.frombuffer(h.digest(), np.uint8)
        return "".join(["%02x" % b for b in d])   
    
    def create_adjacency_tables():
        # Trick to copy table structure in SQLite; seems to work in MySQL too
        # From http://stackoverflow.com/questions/12730390/copy-table-structure-to-new-table-in-sqlite3
        
        # Edge table
        query = ("CREATE TABLE %s AS"%(edited_relnship_tables[EDGE_TBL_ID]),
                    "SELECT %s"%(",".join(reln_cols[EDGE_TBL_ID])),
                    "FROM %s"%(props.relationships_view),
                    "WHERE 0")
        query = " ".join(query)            
        db.execute(query)    
        
        # Node table
        orig_cols = [props.image_id, props.object_id]
        query = ("CREATE TABLE %s AS"%(edited_relnship_tables[NODE_TBL_ID]),
                    "SELECT %s"%(",".join(["%s AS %s"%(_) for _ in zip(orig_cols,reln_cols[NODE_TBL_ID])])),
                    "FROM %s"%(props.object_table),
                    "WHERE 0")
        query = " ".join(query)            
        db.execute(query)        
        
    edited_relnship_tables = get_edited_relationship_tablenames()
    tracer_info_table = '_tracer_info'
    # Check if the info table exists
    is_tracer_table = does_table_exist(tracer_info_table)
    no_changes_needed = True
        
    if not is_tracer_table:
        # If the Tracer info table doens't exist, create it
        logging.info("Creating info table for Tracer...")
        query = ("CREATE TABLE IF NOT EXISTS %s ("%tracer_info_table,
                 "schema_hash TEXT,",
                 "edge_table TEXT,",
                 "node_table TEXT"
                 ")")
        query = " ".join(query)
        db.execute(query)  
        
        # Create hash of relationship data
        schema_hash = create_table_hash()      

        query = ("UPDATE %s SET"%tracer_info_table,
                 "edge_table = '%s',"%EDGE_TBL_ID,
                 "node_table = '%s',"%NODE_TBL_ID,
                 "schema_hash = '%s'"%schema_hash)
        query = " ".join(query)        
        db.execute(query) 
        
        # Create edge and node tables
        logging.info("Creating custom relationship tables...")
        create_adjacency_tables()
        db.Commit()
        no_changes_needed = False
    else:
        query = "SELECT schema_hash FROM %s"%tracer_info_table
        saved_schema_hash = db.execute(query)
        current_schema_hash = create_table_hash()
        
        if saved_schema_hash == current_schema_hash:
            logging.info("No change to data since last session: Keeping old info...")
        else:            
            logging.info("Data has changed: Removing old info...")
            # Data has changed: Drop edge and node tables after confirming they exist
            if does_table_exist(edited_relnship_tables[EDGE_TBL_ID]):
                query = "DROP TABLE %s"%(edited_relnship_tables[EDGE_TBL_ID])
                db.execute(query) 
            if does_table_exist(edited_relnship_tables[NODE_TBL_ID]):
                query = "DROP TABLE %s"%(edited_relnship_tables[NODE_TBL_ID])
                db.execute(query) 
                
            # Re-create edge and node tables
            logging.info("Re-creating custom relationship tables...")
            create_adjacency_tables() 
            
            # Save new data hash
            query = "UPDATE %s SET schema_hash = '%s'"%(tracer_info_table, current_schema_hash)
            db.execute(query)
            db.Commit()
            no_changes_needed = False
    
    if not no_changes_needed: # Need to re-populate the adjacency tables
        # Populate the edge table first
        logging.info("Populating custom relationship tables...")
        
        obj = get_object_name()
        
        query = "SELECT DISTINCT(%s) FROM %s"%(props.group_id, props.image_table)
        available_datasets = [_[0] for _ in db.execute(query)]
        for selected_dataset in available_datasets:
            query = ("INSERT INTO %s"%(edited_relnship_tables[EDGE_TBL_ID]),
                     "SELECT %s"%(",".join(reln_cols[EDGE_TBL_ID])),
                     "FROM %s r"%(props.relationships_view),
                     "JOIN %s i1"%(props.image_table),
                     "ON r.image_number1 = i1.%s"%(props.image_id),
                     "WHERE") + \
                where_stmt_for_tracked_objects(obj,props.group_id,int(selected_dataset)) 
            query = " ".join(query)            
            db.execute(query)
        # Create an index to speed things up
        index_name = 'idx'
        if props.db_type == 'sqlite':
            query = "DROP INDEX IF EXISTS %s"%(index_name)
            db.execute(query) 
        else:
            query = "SHOW INDEX FROM %s WHERE KEY_NAME = '%s'"%(edited_relnship_tables[EDGE_TBL_ID], index_name)
            if len([_ for _ in db.execute(query)]) > 0:
                query = "DROP INDEX %s ON %s"%(index_name, edited_relnship_tables[EDGE_TBL_ID])
                db.execute(query)         
        query = "CREATE INDEX %s ON %s(image_number1,object_number1)"%(index_name, edited_relnship_tables[EDGE_TBL_ID])
        db.execute(query)
              
        # Add the grouping ID and default track columns 
        # SQLite doesn't do multiple ADDs in one query, so do with multiple queries
        query = "ALTER TABLE %s ADD COLUMN %s INT"%(edited_relnship_tables[EDGE_TBL_ID], props.group_id)
        db.execute(query)
        query = "ALTER TABLE %s ADD COLUMN %s INT DEFAULT 1"%(edited_relnship_tables[EDGE_TBL_ID], ORIGINAL_TRACK)
        db.execute(query)
            
        if props.db_type == 'sqlite':
            # From http://stackoverflow.com/questions/19270259/update-join-sqlite
            query = ("UPDATE %s"%(edited_relnship_tables[EDGE_TBL_ID]),
                     "SET %s ="%(props.group_id),
                     "(SELECT %s.%s"%(props.image_table,props.group_id),
                     "FROM %s"%(props.image_table),
                     "WHERE %s.image_number1 = %s.%s)"%(edited_relnship_tables[EDGE_TBL_ID],props.image_table,props.image_id))
        else:
            # From http://dba.stackexchange.com/questions/21152/how-to-update-one-table-based-on-another-tables-values-on-the-fly
            query = ("UPDATE %s"%(edited_relnship_tables[EDGE_TBL_ID]),
                        "INNER JOIN %s"%(props.image_table),
                        "ON %s.image_number1 = %s.%s"%(edited_relnship_tables[EDGE_TBL_ID], props.image_table, props.image_id),
                        "SET %s.%s = %s.%s"%(edited_relnship_tables[EDGE_TBL_ID], props.group_id, props.image_table, props.group_id))
        query = " ".join(query)  
        db.execute(query)
        # Spent the better part of a day figuring out that a 'commit' was needed here
        db.Commit()
        
        #-------------------------------
        # Now the node table
        query = "SELECT DISTINCT(%s) FROM %s"%(props.group_id, props.image_table)
        available_datasets = [_[0] for _ in db.execute(query)]
        for selected_dataset in available_datasets:
            query = ("INSERT INTO %s"%(edited_relnship_tables[NODE_TBL_ID]),
                     "SELECT %s"%(",".join(["o.%s"%(_) for _ in [props.image_id, props.object_id]])),
                     "FROM %s o"%(props.object_table),
                     "JOIN %s i"%(props.image_table),
                     "ON o.%s = i.%s"%(props.image_id, props.image_id),
                     "WHERE i.%s = %d"%(props.group_id, int(selected_dataset)) )
            query = " ".join(query)            
            db.execute(query)
        # Create an index to speed things up
        index_name = 'idx'
        if props.db_type == 'sqlite':
            query = "DROP INDEX IF EXISTS %s"%(index_name)
            db.execute(query) 
        else:
            query = "SHOW INDEX FROM %s WHERE KEY_NAME = '%s'"%(edited_relnship_tables[NODE_TBL_ID], index_name)
            if len([_ for _ in db.execute(query)]) > 0:
                query = "DROP INDEX %s ON %s"%(index_name, edited_relnship_tables[NODE_TBL_ID])
                db.execute(query)                  
        query = "CREATE INDEX %s ON %s(image_number,object_number)"%(index_name, edited_relnship_tables[NODE_TBL_ID])
        db.execute(query)  
            
        # Add the grouping ID and default track columns 
        # SQLite doesn't do multiple ADDs in one query, so do with multiple queries
        query = "ALTER TABLE %s ADD COLUMN %s INT"%(edited_relnship_tables[NODE_TBL_ID], props.group_id)
        db.execute(query)
        query = "ALTER TABLE %s ADD COLUMN %s INT DEFAULT 1"%(edited_relnship_tables[NODE_TBL_ID], ORIGINAL_TRACK)
        db.execute(query)            
            
        if props.db_type == 'sqlite':
            # From http://stackoverflow.com/questions/19270259/update-join-sqlite
            query = ("UPDATE %s"%(edited_relnship_tables[NODE_TBL_ID]),
                     "SET %s ="%(props.group_id),
                     "(SELECT %s.%s"%(props.image_table,props.group_id),
                     "FROM %s"%(props.image_table),
                     "WHERE %s.image_number = %s.%s)"%(edited_relnship_tables[NODE_TBL_ID],props.image_table,props.image_id))
        else:
            # From http://dba.stackexchange.com/questions/21152/how-to-update-one-table-based-on-another-tables-values-on-the-fly
            query = ("UPDATE %s"%(edited_relnship_tables[NODE_TBL_ID]),
                        "INNER JOIN %s"%(props.image_table),
                        "ON %s.image_number = %s.%s"%(edited_relnship_tables[NODE_TBL_ID], props.image_table, props.image_id),
                        "SET %s.%s = %s.%s"%(edited_relnship_tables[NODE_TBL_ID], props.group_id, props.image_table, props.group_id))
        query = " ".join(query)  
        db.execute(query) 
        db.Commit()        
        
    # Retrieve column names
    relationship_table_cols = {}  
    relationship_table_data = {}
    for key in edited_relnship_tables.keys():
        if props.db_type == 'sqlite':
            query = "PRAGMA table_info(%s)"%(edited_relnship_tables[key])
            relationship_table_cols[key] = [_[1] for _ in db.execute(query)]
        else:
            query = "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(props.db_name, edited_relnship_tables[key])
            relationship_table_cols[key] = [_[0] for _ in db.execute(query) ]
        
        query = "SELECT * FROM %s"%edited_relnship_tables[key]
        relationship_table_data[key] = [_ for _ in db.execute(query)] 
    
    defined_track_cols = list(set(relationship_table_cols[NODE_TBL_ID]).difference(set(reln_cols[NODE_TBL_ID]+[props.group_id])))
    
    return relationship_table_cols, defined_track_cols, relationship_table_data

#def obtain_tracking_data(selected_dataset, selected_measurement, selected_filter):
def obtain_tracking_data(selected_dataset, selected_measurement):
    #def parse_dataset_selection(s):
        #return [x.strip() for x in s.split(',') if x.strip() is not '']
    
    #selection_list = parse_dataset_selection(selected_dataset)
    #dataset_clause = " AND ".join(["%s = '%s'"%(x[0], x[1]) for x in zip([props.image_table+"."+_ for _ in props.series_id], selection_list)])
    dataset_clause = " AND ".join(["%s = '%s'"%(x[0], x[1]) for x in zip([props.image_table+"."+_ for _ in props.series_id], [selected_dataset])])
    
    columns_to_retrieve = list(object_key_columns(props.object_table))    # Node IDs
    columns_to_retrieve += [props.object_table+"."+props.cell_x_loc, props.object_table+"."+props.cell_y_loc] # x,y coordinates
    columns_to_retrieve += [props.image_table+"."+props.timepoint_id] # Timepoint/frame
    columns_to_retrieve += [props.object_table+"."+selected_measurement if selected_measurement is not None else 'NULL'] # Measured feature, insert NULL as placeholder if derived
    #columns_to_retrieve += [" AND ".join(selected_filter)] if selected_filter is not None else ['1'] # Filter
    query = ["SELECT %s"%(",".join(columns_to_retrieve))]
    query.append("FROM %s, %s"%(props.image_table, props.object_table))
    query.append("WHERE %s = %s AND %s"%(props.image_table+"."+props.image_id, props.object_table+"."+props.image_id, dataset_clause))
    #query.append("ORDER BY %s, %s"%(props.object_tracking_label, props.timepoint_id))
    query.append("ORDER BY %s"%(props.timepoint_id))
    data = db.execute(" ".join(query))
    #columns = [props.object_tracking_label, props.image_id, props.object_id, props.cell_x_loc, props.cell_y_loc, props.timepoint_id, "Filter", props.parent_fields]
    columns = [props.image_id, props.object_id, props.cell_x_loc, props.cell_y_loc, props.timepoint_id, selected_measurement]
    
    return columns, data

################################################################################
class TracerControlPanel(wx.Panel):
    '''
    A panel with controls for selecting the data for a visual
    Some helpful tips on using sizers for layout: http://zetcode.com/wxpython/layout/
    '''

    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.parent = parent
        
        # Get names of data sets
        # TODO: Decide if this should be self.available_datasets for use elsewhere
        available_datasets = retrieve_datasets()

        # Capture if LAP data is being used
        self.isLAP = is_LAP_tracking_data()
        
        # Get names of fields
        measurements = db.GetColumnNames(props.object_table)
        coltypes = db.GetColumnTypes(props.object_table)
        fields = [m for m,t in zip(measurements, coltypes) if t in [float, int, long]]
        self.dataset_measurement_choices = fields
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Define widgets
        self.dataset_choice = ComboBox(self, -1, choices=[str(_) for _ in available_datasets], size=(200,-1), style=wx.CB_READONLY)
        self.dataset_choice.Select(0)
        self.dataset_choice.SetHelpText("Select the time-lapse data set to visualize.")
        
        self.track_collection = ComboBox(self, -1, choices=[ORIGINAL_TRACK], size=(200,-1), style=wx.CB_READONLY)
        self.track_collection.Select(0)
        self.track_collection.SetHelpText("Select the identifier specifying the tracked object relationships in the current data set.")  
        self.track_collection.Disable()

        self.dataset_measurement_choice = ComboBox(self, -1, choices=self.dataset_measurement_choices, style=wx.CB_READONLY)
        self.dataset_measurement_choice.Select(0)
        self.dataset_measurement_choice.SetHelpText("Select the per-%s measurement to visualize the data with. The lineages and (xyt) trajectories will be color-coded by this measurement."%props.object_name[0])
        
        cmaps = sorted(lut_manager.lut_mode_list())
        self.colormap_choice = ComboBox(self, -1, choices=cmaps, style=wx.CB_READONLY)
        self.colormap_choice.SetStringSelection("jet") 
        self.colormap_choice.SetHelpText("Select the colormap to use for color-coding the data.")
        
        self.trajectory_selection_button = wx.Button(self, -1, "Select Tracks to Visualize...")
        self.trajectory_selection_button.SetHelpText("Select the trajectories to show or hide in both panels.")
        if self.isLAP:
            self.trajectory_diagnosis_toggle = wx.ToggleButton(self, -1, "Show LAP Diagnostic Graphs")
            self.trajectory_diagnosis_toggle.SetHelpText("If you have tracking data generated by the LAP method, a new box will open with diagnostic graphs indicating goodness of your settings.")
        
        self.update_plot_color_button = wx.Button(self, -1, "Update Display")
        self.update_plot_color_button.SetHelpText("Press this button after making selections to update the panels.")
        
        self.help_button = wx.ContextHelpButton(self)
        
        self.derived_measurement_choice = ComboBox(self, -1, style=wx.CB_READONLY)
        self.derived_measurement_choice.SetHelpText("Select the derived measurement to visualize the data with.")     
        self.derived_measurement_choice.Disable()
        
        self.singleton_length_cutoff_text = wx.StaticText(self, -1, "Singleton length cutoff:")
        self.singleton_length_cutoff_text.Hide() 
        self.singleton_length_value = wx.SpinCtrl(self, -1, value = "1", style=wx.SP_ARROW_KEYS, min=0, initial=4)
        self.singleton_length_value.SetHelpText("Enter the number of nodes a lone track segment can have to be a candidate for pruning.")   
        self.singleton_length_value.Disable()
        self.singleton_length_value.Hide()        

        self.singleton_length_plot_button = wx.Button(self, -1, "Length Histogram")
        self.singleton_length_plot_button.SetHelpText("Plot of segment lengths")
        self.singleton_length_plot_button.Disable() 
        self.singleton_length_plot_button.Hide()  
        
        self.distance_cutoff_value_text = wx.StaticText(self, -1, "Distance cutoff:")
        self.distance_cutoff_value_text.Hide() 
        
        self.distance_cutoff_value = wx.SpinCtrl(self, -1, value = "4", style=wx.SP_ARROW_KEYS, min=0, initial=4)
        self.distance_cutoff_value.SetHelpText("Enter the number of nodes from a branch that a terminus must be found in order to be selected as a candidate for pruning.")   
        self.distance_cutoff_value.Disable()
        self.distance_cutoff_value.Hide()
        
        self.distance_cutoff_plot_button = wx.Button(self, -1, "Distance Histogram")
        self.distance_cutoff_plot_button.SetHelpText("Plot of branchpoint distances")
        self.distance_cutoff_plot_button.Disable()
        self.distance_cutoff_plot_button.Hide()
        
        self.bc_branch_ratio_value_text = wx.StaticText(self, -1, "Betweeness centrality cutoff:")
        self.bc_branch_ratio_value_text.Hide()
        self.bc_branch_ratio_value = wx.TextCtrl(self, -1, value = "0.5", style=wx.TE_PROCESS_ENTER)
        self.bc_branch_ratio_value.SetHelpText("Enter the betweeness centrality fraction that a branch node must be in order be selected as a candidate for pruning.")   
        self.bc_branch_ratio_value.Disable()        
        self.bc_branch_ratio_value.Hide()
        
        self.bc_branch_plot_button = wx.Button(self, -1, "Betweeness Centrality Histogram")
        self.bc_branch_plot_button.SetHelpText("Plot of between centrality branchpoint values.")   
        self.bc_branch_plot_button.Disable()        
        self.bc_branch_plot_button.Hide()

        self.preview_prune_button = wx.ToggleButton(self, -1, "Preview Pruned Branches")
        self.preview_prune_button.SetHelpText("Redraws the graph with the pruned nodes removed.")
        self.preview_prune_button.Disable()  
        
        self.add_pruning_to_edits_button = wx.Button(self, -1, "Add Pruning to Edits")
        self.add_pruning_to_edits_button.SetHelpText("Adds the pruned graph to the list of edits.")
        self.add_pruning_to_edits_button.Disable()          
        
        self.save_edited_tracks_button = wx.Button(self, -1, "Save Edited Tracks...")
        self.save_edited_tracks_button.SetHelpText("Saves the edited graph as a new index into the relationship table.")
        self.save_edited_tracks_button.Disable()         
        
        # TODO: Fix filtering functionality, then enable
        #self.create_filter_button = wx.Button(self, -1, "Create New Data Measurement Filter")
        #self.create_filter_button.SetHelpText("Creates a new measurement filter.")
        #self.create_filter_button.Disable()  
        #self.filter_choices = ComboBox(self, -1, style=wx.CB_READONLY)
        #self.filter_choices.SetHelpText("Selects a previously defined measurement filter.")
        #self.filter_choices.Disable() 
        
        # Arrange widgets
        # Row #1: Dataset drop-down + track selection button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Data Source:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.dataset_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Data Tracks:"), 0, wx.TOP, 4)
        sz.Add(self.track_collection, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.trajectory_selection_button)
        if self.isLAP:
            sz.AddSpacer((4,-1))
            sz.Add(self.trajectory_diagnosis_toggle)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        # Row #2: Data measurement color selection, colormap, update button
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Data Measurements:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.dataset_measurement_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(wx.StaticText(self, -1, "Colormap:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))
        sz.Add(self.colormap_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.update_plot_color_button)
        sz.AddSpacer((4,-1))
        sz.Add(self.help_button)
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))

        # Row #3: Derived measurement color selection
        sz = wx.BoxSizer(wx.HORIZONTAL)
        sz.Add(wx.StaticText(self, -1, "Derived Metrics:"), 0, wx.TOP, 4)
        sz.AddSpacer((4,-1))  
        sz.Add(self.derived_measurement_choice, 1, wx.EXPAND)
        sz.AddSpacer((4,-1))
        sz.Add(self.singleton_length_cutoff_text, 0, wx.TOP, 4)
        sz.Add(self.singleton_length_value, 1, wx.EXPAND)
        sz.Add(self.singleton_length_plot_button, 1, wx.EXPAND)        
        sz.Add(self.distance_cutoff_value_text, 0, wx.TOP, 4)
        sz.Add(self.distance_cutoff_value, 1, wx.EXPAND)
        sz.Add(self.distance_cutoff_plot_button, 1, wx.EXPAND)
        sz.Add(self.bc_branch_ratio_value_text, 0, wx.TOP, 4)
        sz.Add(self.bc_branch_ratio_value, 1, wx.EXPAND) 
        sz.Add(self.bc_branch_plot_button, 1, wx.EXPAND) 
        #sz.AddSpacer((4,-1))
        #sz.Add(wx.StaticLine(self,-1,style=wx.LI_VERTICAL), 0) 
        sz.AddSpacer((4,-1))
        sz.Add(self.preview_prune_button, 1, wx.EXPAND) 
        sz.AddSpacer((4,-1))
        sz.Add(self.add_pruning_to_edits_button, 1, wx.EXPAND) 
        sz.AddSpacer((4,-1))
        sz.Add(self.save_edited_tracks_button, 1, wx.EXPAND) 
        self.derived_measurement_sizer = sz # Save sizer for later reference
        sizer.Add(sz, 1, wx.EXPAND)
        sizer.AddSpacer((-1,2))       
        
        # TODO: Fix filtering functionality, then enable
        ### Row #4: Measurement filter selection
        #sz = wx.BoxSizer(wx.HORIZONTAL)
        #self.enable_filtering_checkbox = wx.CheckBox(self, -1, label="Enable Filtering by Data Measurements")
        #self.enable_filtering_checkbox.SetValue(0)
        #sz.Add(self.enable_filtering_checkbox, 0, wx.TOP, 4)
        #sz.AddSpacer((4,-1))
        #sz.Add(self.create_filter_button, 1, wx.TOP, 4)
        #sz.AddSpacer((4,-1))
        #sz.Add(self.filter_choices, 1, wx.TOP, 4)
        #sz.Layout()
        #sizer.Add(sz, 1, wx.EXPAND) 
        #sizer.AddSpacer((-1,2))
        
        sizer.Layout()
        self.SetSizer(sizer)
        self.Layout()
        self.Show(True)
        
        self.derived_metric_to_widget_mapping = {   METRIC_SINGLETONS: [self.singleton_length_cutoff_text, self.singleton_length_value, self.singleton_length_plot_button, self.add_pruning_to_edits_button, self.save_edited_tracks_button], 
                                                    METRIC_BC: [self.bc_branch_ratio_value_text, self.bc_branch_ratio_value, self.bc_branch_plot_button],
                                                    METRIC_NODESWITHINDIST: [self.distance_cutoff_value_text, self.distance_cutoff_value, self.distance_cutoff_plot_button],
                                                    METRIC_LOOPS: None,
                                                    METRIC_CROSSINGS: None}
        
        # Define events
        wx.EVT_COMBOBOX(self.dataset_choice, -1, self.on_dataset_selected)
        wx.EVT_COMBOBOX(self.track_collection, -1, self.on_track_collection_selected)
        wx.EVT_COMBOBOX(self.dataset_measurement_choice, -1, self.on_dataset_measurement_selected)
        wx.EVT_COMBOBOX(self.derived_measurement_choice, -1, self.on_derived_measurement_selected)
        wx.EVT_BUTTON(self.trajectory_selection_button, -1, self.on_update_trajectory_selection)
        if self.isLAP:
            wx.EVT_TOGGLEBUTTON(self.trajectory_diagnosis_toggle, -1, self.on_calculate_and_display_lap_stats)
        wx.EVT_COMBOBOX(self.colormap_choice, -1, self.on_colormap_selected)
        wx.EVT_BUTTON(self.update_plot_color_button, -1, self.on_update_plot)
        wx.EVT_BUTTON(self.singleton_length_plot_button,-1,self.on_singleton_length_plot)   
        wx.EVT_SPINCTRL(self.distance_cutoff_value,-1,self.on_derived_measurement_selected)      
        wx.EVT_BUTTON(self.distance_cutoff_plot_button,-1,self.on_diistance_plot)  
        wx.EVT_BUTTON(self.bc_branch_plot_button,-1,self.on_bc_branch_plot)
        wx.EVT_TOGGLEBUTTON(self.preview_prune_button,-1, self.on_toggle_preview_pruned_graph)
        wx.EVT_BUTTON(self.add_pruning_to_edits_button,-1,self.on_add_pruning_to_edits)
        wx.EVT_BUTTON(self.save_edited_tracks_button,-1, self.on_save_edited_tracks)      
        #wx.EVT_CHECKBOX(self.enable_filtering_checkbox, -1, self.on_enable_filtering)
        #wx.EVT_BUTTON(self.create_filter_button,-1, self.on_filter_button) 
        #wx.EVT_COMBOBOX(self.filter_choices,-1, self.on_filter_selection)   
        
    def on_dataset_selected(self, event=None):
        self.parent.dataset_selected(self.dataset_choice.GetStringSelection(), self.track_collection.GetStringSelection())
        
    def on_track_collection_selected(self, event=None):
        self.parent.track_collection_selected(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection())  
        
    def on_dataset_measurement_selected(self, event=None):
        self.parent.dataset_measurement_selected(self.dataset_measurement_choice.GetStringSelection(), 
                                                 self.derived_measurement_choice.GetStringSelection())  
        
    def on_derived_measurement_selected(self, event=None):
        self.parent.derived_measurement_selected(self.derived_measurement_choice.GetStringSelection())  
        
    def on_update_trajectory_selection(self, event=None):
        self.parent.update_trajectory_selection(self.dataset_choice.GetValue(),self.track_collection.GetStringSelection())  
        
    def on_calculate_and_display_lap_stats(self, event=None):
        # TODO: Figure out why the appearance of the toggle doesn't change when pressed
        self.trajectory_diagnosis_toggle.SetValue(True)
        self.parent.calculate_and_display_lap_stats()
        self.trajectory_diagnosis_toggle.SetValue(False)
        
    def on_colormap_selected(self, event=None):
        self.parent.colormap_selected(self.colormap_choice.GetStringSelection())  
        
    def on_update_plot(self, event=None):
        self.parent.update_plot(self.dataset_choice.GetValue(),self.track_collection.GetStringSelection())  
        
    def on_singleton_length_plot(self, event=None):
        self.parent.singleton_length_plot(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection(), int(self.singleton_length_value.GetValue()))
    
    def on_diistance_plot(self, event=None):
        self.parent.distance_plot(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection())
        
    def on_bc_branch_plot(self, event=None):
        self.parent.bc_branch_plot(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection())
    
    def on_toggle_preview_pruned_graph(self, event=None):
        self.parent.toggle_preview_pruned_graph(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection())  
        
    def on_add_pruning_to_edits(self, event=None):
        self.parent.add_pruning_to_edits(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection())  
        
    def on_save_edited_tracks(self, event=None):     
        self.parent.save_edited_tracks(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection())  
        
    def on_enable_filtering(self, event=None):
        is_enabled = self.enable_filtering_checkbox.GetValue()
        self.create_filter_button.Enable(is_enabled)
        self.filter_choices.Enable(is_enabled)            

    def on_filter_button(self, event=None):
        self.parent.create_new_filter()
    
    def on_filter_selection(self, event=None):
        self.parent.filter_selected(self.dataset_choice.GetValue(), self.track_collection.GetStringSelection(), self.filter_choices.GetStringSelection()) 
    
################################################################################
class MayaviView(HasTraits):
    """ Create a mayavi scene"""
    lineage_scene = Instance(MlabSceneModel, ())
    trajectory_scene = Instance(MlabSceneModel, ())
    dataset = Int(0)
    
    # The layout of the dialog created
    view = View(HSplit(Group(Item('trajectory_scene',
                                  #editor = SceneEditor(scene_class = Scene),
                                  editor = SceneEditor(scene_class=MayaviScene),
                                  resizable=True, show_label=False)),
                       Group(Item('lineage_scene',
                                  editor = SceneEditor(scene_class = Scene),
                                  #editor = SceneEditor(scene_class=MayaviScene),
                                  resizable=True, show_label=False))),
                resizable=True)
    
    def __init__(self, parent):
        HasTraits.__init__(self)
        self.parent = parent
        self.axes_opacity = 0.25
        self.lineage_figure = self.lineage_scene.mlab.gcf()
        self.trajectory_figure = self.trajectory_scene.mlab.gcf()

    # Apparently, I cannot use mlab.clf to clear the figure without disconnecting the picker
    # So remove the children to get the same effect.
    # See: http://stackoverflow.com/questions/23435986/mayavi-help-in-resetting-mouse-picker-and-connecting-wx-event-to-on-trait-chan
    # Note that the respondent says I will still need to reattach the picker, but that doesn't seem to be the case here...
    def clear_figures(self, scene):
        for child in scene.mayavi_scene.children:
            child.remove()  
            
    @on_trait_change('lineage_scene.activated')
    def activate_lineage_scene(self):
        # An trajectory picker object is created to trigger an event when a trajectory is picked. 
        # Can press 'p' to get UI on current pick 
        #
        # Helpful pages re: pickers
        # https://gist.github.com/syamajala/8804396
        # http://sourceforge.net/p/mayavi/mailman/message/27239432/  (not identical problem)    
        picker = self.lineage_scene.mayavi_scene.on_mouse_pick(self.on_pick_lineage)
        picker.tolerance = 0.01
        
        # Why is this here? Well, apparently the axes need to be oriented to a camera, which needs the view to be opened first.
        # See http://en.it-usenet.org/thread/15952/8170/
        mlab.axes(self.lineage_node_collection, 
                          xlabel='T', ylabel='',
                          extent = self.lineage_extent,
                          opacity = self.axes_opacity,
                          x_axis_visibility=True, y_axis_visibility=False, z_axis_visibility=False) 
        
        # Constrain view to 2D
        self.lineage_scene.interactor.interactor_style = tvtk.InteractorStyleImage()        
        self.lineage_scene.reset_zoom()
        
        # Add object label text to the left
        # Why is this here? The text module needs to have a scene opened to work
        # http://enthought-dev.117412.n3.nabble.com/How-to-clear-AttributeError-NoneType-object-has-no-attribute-active-camera-td2181947.html
        text_scale_factor = self.lineage_node_scale_factor/1.0 
        t = nx.get_node_attributes(self.directed_graph,L_TCOORD)
        y = nx.get_node_attributes(self.directed_graph,L_YCOORD)
        start_nodes = {}
        for key,subgraph in self.connected_nodes.items():
            start_nodes[key] = [_[0] for _ in nx.get_node_attributes(subgraph,START_NODES).items() if _[1]]
        self.lineage_label_collection = dict(zip(self.connected_nodes.keys(),
                                                 [mlab.text3d(t[start_nodes[key][0]]-0.75*self.lineage_temporal_scaling,
                                                              y[start_nodes[key][0]],
                                                              0,
                                                              str(key),
                                                              scale = text_scale_factor,
                                                              figure = self.lineage_scene.mayavi_scene)
                                                  for key,subgraph in self.connected_nodes.items()]))            
    
    @on_trait_change('trajectory_scene.activated')
    def activate_trajectory_scene(self):
        picker = self.trajectory_scene.mayavi_scene.on_mouse_pick(self.on_pick_trajectory)
        picker.tolerance = 0.01
        
        # TODO: Incorporate image dimensions into axes viz
        # Get image dimensions
        if props.db_type == 'sqlite':
            query = "PRAGMA table_info(%s)"%(props.image_table)
            w_col = [_[1] for _ in db.execute(query) if _[1].find('Image_Width') >= 0][0]
            h_col = [_[1] for _ in db.execute(query) if _[1].find('Image_Height') >= 0][0]  
        else:
            query = "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP 'Image_Width' LIMIT 1"%(props.db_name, props.image_table)
            w_col = db.execute(query)[0][0]
            query = "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP 'Image_Height' LIMIT 1"%(props.db_name, props.image_table)
            h_col = db.execute(query)[0][0]          

        query = "SELECT %s FROM %s LIMIT 1"%(w_col, props.image_table)
        self.parent.image_x_dims = db.execute(query)[0][0]
        query = "SELECT %s FROM %s LIMIT 1"%(h_col, props.image_table)
        self.parent.image_y_dims = db.execute(query)[0][0]        
        
        ax = mlab.axes(self.trajectory_line_source, 
                      xlabel='X', ylabel='Y',zlabel='T',
                      #extent = (1,self.parent.image_x_dims,1,self.parent.image_y_dims,self.parent.start_frame,self.parent.end_frame),
                      opacity = self.axes_opacity,
                      x_axis_visibility=True, y_axis_visibility=True, z_axis_visibility=True)
        
        # Set axes to MATLAB's default 3d view
        mlab.view(azimuth = 322.5,elevation = 30.0,
                  figure = self.trajectory_scene.mayavi_scene)     
        
        # Add object label text at end of trajectory
        text_scale_factor = self.trajectory_node_scale_factor*5 
        end_nodes = {}
        for (key,subgraph) in self.connected_nodes.items():
            end_nodes[key] = [_[0] for _ in nx.get_node_attributes(subgraph,END_NODES).items() if _[1]][0]
        self.trajectory_label_collection = dict(zip(self.connected_nodes.keys(),
                                                    [mlab.text3d(subgraph.node[end_nodes[key]]["x"],
                                                                 subgraph.node[end_nodes[key]]["y"],
                                                                 subgraph.node[end_nodes[key]]["t"]*self.trajectory_temporal_scaling,
                                                                 str(key),
                                                                 scale = text_scale_factor,
                                                                 name = str(key),
                                                                 figure = self.trajectory_scene.mayavi_scene) 
                                                     for (key,subgraph) in self.connected_nodes.items()]))       
        self.trajectory_scene.reset_zoom()        
        
    def on_pick_lineage(self, picker):
        """ Lineage picker callback: this gets called upon pick events.
        """
        picked_graph_node = None
        picked_lineage_coords = None
        picked_trajectory_coords = None
        if picker.actor in self.lineage_node_collection.actor.actors + self.lineage_edge_collection.actor.actors:
            # TODO: Figure what the difference is between node_collection and edge_collection being clicked on.
            # Retrieve to which point corresponds the picked point. 
            # Here, we grab the points describing the individual glyph, to figure
            # out how many points are in an individual glyph.                
            n_glyph = self.lineage_node_collection.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]
            # Find which data point corresponds to the point picked:
            # we have to account for the fact that each data point is
            # represented by a glyph with several points      
            point_id = picker.point_id/n_glyph
            picked_lineage_coords = self.lineage_node_collection.mlab_source.points[point_id,:]
            picked_trajectory_coords = self.trajectory_node_collection.mlab_source.points[point_id,:]
            picked_graph_node = sorted(self.directed_graph)[point_id]
        self.on_pick(picked_graph_node, picked_lineage_coords, picked_trajectory_coords)
    
    def on_select_point(self):
        # Used if a coordinate is picked via somethign other than a mouse pick
        point_id = sorted(self.directed_graph).index(self.parent.selected_node)
        picked_trajectory_coords = self.trajectory_node_collection.mlab_source.points[point_id,:]
        picked_lineage_coords = self.lineage_node_collection.mlab_source.points[point_id,:]
        #self.parent.selected_node = None # Disable temporailty since it gets set back in on_pick
        self.on_pick(self.parent.selected_node, picked_lineage_coords, picked_trajectory_coords, True)  
    
    def on_pick_trajectory(self,picker):
        """ Trajectory picker callback: this gets called upon pick events.
        """
        picked_graph_node = None
        picked_lineage_coords = None
        picked_trajectory_coords = None
        if picker.actor in self.trajectory_node_collection.actor.actors:
            n_glyph = self.trajectory_node_collection.glyph.glyph_source.glyph_source.output.points.to_array().shape[0]  
            point_id = picker.point_id/n_glyph            
            picked_trajectory_coords = self.trajectory_node_collection.mlab_source.points[point_id,:]
            picked_lineage_coords = self.lineage_node_collection.mlab_source.points[point_id,:]
            picked_graph_node = sorted(self.directed_graph)[point_id]        
        else:
            picked_graph_node = None
        self.on_pick(picked_graph_node, picked_lineage_coords, picked_trajectory_coords)
                
    def on_pick(self,picked_graph_node, picked_lineage_coords = None, picked_trajectory_coords = None, no_mouse = False):
        if picked_graph_node != None:
            # If the picked node is not one of the selected trajectories, then don't select it 
            if not no_mouse and picked_graph_node == self.parent.selected_node:
                self.parent.selected_node = None
                self.parent.selected_trajectory = None      
                self.lineage_selection_outline.actor.actor.visibility = 0
                self.trajectory_selection_outline.actor.actor.visibility = 0
            else:
                self.parent.selected_node = picked_graph_node
                self.parent.selected_trajectory = [self.parent.directed_graph[self.parent.selected_dataset][self.parent.selected_dataset_track].node[picked_graph_node][SUBGRAPH_ID]]
                
                # Move the outline to the data point
                dx = np.diff(self.lineage_selection_outline.bounds[:2])[0]/2
                dy = np.diff(self.lineage_selection_outline.bounds[2:4])[0]/2           
                self.lineage_selection_outline.bounds = (picked_lineage_coords[0]-dx, picked_lineage_coords[0]+dx,
                                                         picked_lineage_coords[1]-dy, picked_lineage_coords[1]+dy,
                                                         0, 0)
                self.lineage_selection_outline.actor.actor.visibility = 1
                
                dx = np.diff(self.trajectory_selection_outline.bounds[:2])[0]/2
                dy = np.diff(self.trajectory_selection_outline.bounds[2:4])[0]/2
                dt = np.diff(self.trajectory_selection_outline.bounds[4:6])[0]/2
                self.trajectory_selection_outline.bounds = (picked_trajectory_coords[0]-dx, picked_trajectory_coords[0]+dx,
                                                            picked_trajectory_coords[1]-dy, picked_trajectory_coords[1]+dy,
                                                            picked_trajectory_coords[2]-dt, picked_trajectory_coords[2]+dt)
                self.trajectory_selection_outline.actor.actor.visibility = 1        

    def draw_lineage(self, do_plots_need_updating, directed_graph=None, connected_nodes=None, selected_colormap=None, scalar_data = None):
        # Rendering temporarily disabled
        self.lineage_scene.disable_render = True 

        # Helpful pages on using NetworkX and Mayavi:
        #  http://docs.enthought.com/mayavi/mayavi/auto/example_delaunay_graph.html
        #  https://groups.google.com/forum/?fromgroups=#!topic/networkx-discuss/wdhYIPeuilo
        #  http://www.mail-archive.com/mayavi-users@lists.sourceforge.net/msg00727.html        

        # Draw the lineage tree if the dataset has been updated
        if do_plots_need_updating["dataset"]:
            self.connected_nodes = connected_nodes
            self.directed_graph = directed_graph
            
            # Clear the scene
            logging.info("Drawing lineage graph...")
            if self.parent.plot_initialized:
                self.clear_figures(self.lineage_scene)
             
            #mlab.title("Lineage tree",size=2.0,figure=self.lineage_scene.mayavi_scene)   
            
            t1 = time.clock()
            
            G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
            xys = np.array([[directed_graph.node[node][L_TCOORD],directed_graph.node[node][L_YCOORD],directed_graph.node[node][SCALAR_VAL]] for node in sorted(directed_graph.nodes()) ])
            #if len(xys) == 0:
                #xys = np.array(3*[np.NaN],ndmin=2)
            dt = np.median(np.diff(np.unique(nx.get_node_attributes(directed_graph,"t").values())))
            # The scale factor defaults to the typical interpoint distance, which may not be appropriate. 
            # So I set it explicitly here to a fraction of delta_t
            # To inspect the value, see pts.glyph.glpyh.scale_factor
            node_scale_factor = 0.5*dt
            self.lineage_node_collection = mlab.points3d(xys[:,0], xys[:,1], np.zeros_like(xys[:,0]), xys[:,2],
                                                            scale_factor = node_scale_factor, 
                                                            scale_mode = 'none',
                                                            colormap = selected_colormap,
                                                            resolution = 8,
                                                            figure = self.lineage_scene.mayavi_scene) 
            self.lineage_node_collection.glyph.color_mode = 'color_by_scalar'
            
            #tube_radius = node_scale_factor/10.0
            #tube = mlab.pipeline.tube(self.lineage_node_collection, 
            #                          tube_radius = tube_radius, # Default tube_radius results in v. thin lines: tube.filter.radius = 0.05
            #                          figure = self.lineage_scene.mayavi_scene)
            #self.lineage_tube = tube
            self.lineage_edge_collection = mlab.pipeline.surface(self.lineage_node_collection, 
                                                                 color=(0.8, 0.8, 0.8),
                                                                 figure = self.lineage_scene.mayavi_scene)
            self.lineage_edge_collection.mlab_source.dataset.lines = np.array(G.edges())
            self.lineage_edge_collection.mlab_source.update()
            
            # Add outline to be used later when selecting points
            self.lineage_selection_outline = mlab.outline(line_width=3,
                                                          figure = self.lineage_scene.mayavi_scene)
            self.lineage_selection_outline.outline_mode = 'cornered'
            self.lineage_selection_outline.actor.actor.visibility = 0
            self.lineage_selection_outline.bounds = (-node_scale_factor,node_scale_factor,
                                                     -node_scale_factor,node_scale_factor,
                                                     -node_scale_factor,node_scale_factor)            
            # Add 2 more outlines to be used later when selecting points
            #self.lineage_point_selection_outline = []
            #for i in range(2):
                #ol = mlab.points3d(0,0,0,
                                   #extent = list(2*np.array([-node_scale_factor,node_scale_factor,
                                             #-node_scale_factor,node_scale_factor,
                                             #-node_scale_factor,node_scale_factor])),
                                   #color = (1,0,1),
                                   #mode = 'sphere',
                                   #scale_factor = 2*node_scale_factor, 
                                   #scale_mode = 'none',                                   
                                   #figure = self.lineage_scene.mayavi_scene)
                #ol.actor.actor.visibility = 0    
                #self.lineage_point_selection_outline.append(ol)            

            self.lineage_node_scale_factor = node_scale_factor
            
            # Add axes outlines
            self.lineage_extent = (0,np.max(nx.get_node_attributes(directed_graph,L_TCOORD).values()),
                                   0,np.max(nx.get_node_attributes(directed_graph,L_YCOORD).values()),
                                   0,0)
            self.lineage_outline = mlab.pipeline.outline(self.lineage_node_collection,
                                  extent = self.lineage_extent,
                                  opacity = self.axes_opacity,
                                  figure = self.lineage_scene.mayavi_scene) 
            
            t2 = time.clock()
            logging.info("Computed layout (%.2f sec)"%(t2-t1))   
        else:
            logging.info("Re-drawing lineage tree...")
            
            if do_plots_need_updating["trajectories"]:
                G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
                edges = np.array([e for e in G.edges() if G.node[e[0]][VISIBLE] and G.node[e[1]][VISIBLE]])
                self.lineage_edge_collection.mlab_source.dataset.lines = edges
                self.lineage_edge_collection.mlab_source.update()
                
                for key in connected_nodes.keys():
                    self.lineage_label_collection[key].actor.actor.visibility = self.parent.trajectory_selection[key]

            if do_plots_need_updating["measurement"]:
                self.lineage_node_collection.mlab_source.set(scalars = scalar_data)
            
            if do_plots_need_updating["colormap"]:
                # http://docs.enthought.com/mayavi/mayavi/auto/example_custom_colormap.html
                self.lineage_node_collection.module_manager.scalar_lut_manager.lut_mode = selected_colormap
                
        # Re-enable the rendering
        self.lineage_scene.disable_render = False        

    def draw_trajectories(self, do_plots_need_updating, directed_graph = None, connected_nodes = None, selected_colormap=None, scalar_data = None):
        # Rendering temporarily disabled
        self.trajectory_scene.disable_render = True  
        
        # Draw the lineage tree if either (1) all the controls indicate that updating is needed (e.g., initial condition) or
        # (2) if the dataset has been updated        
        if do_plots_need_updating["dataset"]:
            self.directed_graph = directed_graph
            self.connected_nodes = connected_nodes

            logging.info("Drawing trajectories...")
            # Clear the scene
            if self.parent.plot_initialized:
                self.clear_figures(self.trajectory_scene)
    
            #mlab.title("Trajectory plot",size=2.0,figure=self.trajectory_scene.mayavi_scene)   
    
            t1 = time.clock()
            
            G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
    
            xyts = np.array([(directed_graph.node[key]["x"],
                               directed_graph.node[key]["y"],
                               directed_graph.node[key]["t"],
                               directed_graph.node[key][SCALAR_VAL],
                               directed_graph.node[key][VISIBLE]) 
                             for key in sorted(directed_graph)])
            
            visible = xyts[:, -1]
            # Compute reasonable scaling factor according to the data limits.
            # We want the plot to be roughly square, to avoid nasty Mayavi axis scaling issues later.
            # Unfortunately, adjusting the surface.actor.actor.scale seems to lead to more problems than solutions.
            # See: http://stackoverflow.com/questions/13015097/how-do-i-scale-the-x-and-y-axes-in-mayavi2
            t_scaling = np.mean( [(max(xyts[:,0])-min(xyts[:,0])), (max(xyts[:,1])-min(xyts[:,1]))] ) / (max(xyts[:,2])-min(xyts[:,2]))
            xyts[:,2] *= t_scaling
            self.trajectory_temporal_scaling = t_scaling
    
            # Taken from http://docs.enthought.com/mayavi/mayavi/auto/example_plotting_many_lines.html
            # Create the lines
            self.trajectory_line_source = mlab.pipeline.scalar_scatter(xyts[:,0], xyts[:,1], xyts[:,2], xyts[:,3], \
                                                                       figure = self.trajectory_scene.mayavi_scene)
            # Connect them using the graph edge matrix
            self.trajectory_line_source.mlab_source.dataset.lines = np.array(G.edges())     
            
            # Finally, display the set of lines by using the surface module. Using a wireframe
            # representation allows to control the line-width.
            self.trajectory_line_collection = mlab.pipeline.surface(mlab.pipeline.stripper(self.trajectory_line_source), # The stripper filter cleans up connected lines; it regularizes surfaces by creating triangle strips
                                                                    line_width=1, 
                                                                    colormap=selected_colormap,
                                                                    figure = self.trajectory_scene.mayavi_scene)         
    
            # Generate the corresponding set of nodes
            dt = np.median(np.diff(np.unique(nx.get_node_attributes(directed_graph,"t").values())))
            self.lineage_temporal_scaling = dt
            
            # Try to scale the nodes in a reasonable way
            # To inspect, see pts.glyph.glpyh.scale_factor 
            node_scale_factor = 0.5*dt
            pts = mlab.points3d(xyts[:,0], xyts[:,1], xyts[:,2], xyts[:,3],
                                scale_factor = 0.0,
                                scale_mode = 'none',
                                colormap = selected_colormap,
                                figure = self.trajectory_scene.mayavi_scene) 
            pts.glyph.color_mode = 'color_by_scalar'
            pts.mlab_source.dataset.lines = np.array(G.edges())
            self.trajectory_node_collection = pts    
    
            # Add outline to be used later when selecting points
            self.trajectory_selection_outline = mlab.outline(line_width = 3,
                                                             figure = self.trajectory_scene.mayavi_scene)
            self.trajectory_selection_outline.outline_mode = 'cornered'
            self.trajectory_selection_outline.bounds = (-node_scale_factor,node_scale_factor,
                                                        -node_scale_factor,node_scale_factor,
                                                        -node_scale_factor,node_scale_factor)
            self.trajectory_selection_outline.actor.actor.visibility = 0
            
            # Add 2 more points to be used later when selecting points
            #self.trajectory_point_selection_outline = []
            #for i in range(2):
                #ol = mlab.points3d(0,0,0,
                                   #extent = [-node_scale_factor,node_scale_factor,
                                             #-node_scale_factor,node_scale_factor,
                                             #-node_scale_factor,node_scale_factor],
                                   #color = (1,0,1),
                                   #figure = self.trajectory_scene.mayavi_scene)
                #ol.actor.actor.visibility = 0    
                #self.trajectory_point_selection_outline.append(ol)
            
            self.trajectory_node_scale_factor = node_scale_factor
            
            # Using axes doesn't work until the scene is avilable: 
            # http://docs.enthought.com/mayavi/mayavi/building_applications.html#making-the-visualization-live
            mlab.pipeline.outline(self.trajectory_line_source,
                                  opacity = self.axes_opacity,
                                  figure = self.trajectory_scene.mayavi_scene) 
            
            # Figure decorations
            # Orientation axes
            #mlab.orientation_axes(zlabel = "T", 
                                  #line_width = 5,
                                  #figure = self.mayavi_view.trajectory_scene.mayavi_scene )
            # Colormap
            # TODO: Figure out how to scale colorbar to smaller size
            #c = mlab.colorbar(orientation = "horizontal", 
                              #title = self.selected_measurement,
                              #figure = self.mayavi_view.trajectory_scene.mayavi_scene)
            #c.scalar_bar_representation.position2[1] = 0.05
            #c.scalar_bar.height = 0.05
            
            t2 = time.clock()
            logging.info("Computed trajectory layout (%.2f sec)"%(t2-t1))              
        else:
            logging.info("Re-drawing trajectories...")
            
            if do_plots_need_updating["trajectories"]:
                G = nx.convert_node_labels_to_integers(directed_graph,ordering="sorted")
                edges = [e for e in G.edges() if G.node[e[0]][VISIBLE] and G.node[e[1]][VISIBLE]]
                self.trajectory_line_collection.mlab_source.dataset.lines = self.trajectory_line_source.mlab_source.dataset.lines = \
                    np.array(edges)
                self.trajectory_line_collection.mlab_source.update()
                self.trajectory_line_source.mlab_source.update()                
                
                for key in connected_nodes.keys():
                    self.trajectory_label_collection[key].actor.actor.visibility = self.parent.trajectory_selection[key] != 0  

            if do_plots_need_updating["measurement"]:
                self.trajectory_line_collection.mlab_source.set(scalars = scalar_data)
                self.trajectory_node_collection.mlab_source.set(scalars = scalar_data)
            
            if do_plots_need_updating["colormap"]:
                self.trajectory_line_collection.module_manager.scalar_lut_manager.lut_mode = selected_colormap
                self.trajectory_node_collection.module_manager.scalar_lut_manager.lut_mode = selected_colormap
                
        # Re-enable the rendering
        self.trajectory_scene.disable_render = False  
            
################################################################################
class FigureFrame(wx.Frame, CPATool):
    """A wx.Frame with a figure inside"""
    def __init__(self, parent=None, id=-1, title="", 
                     pos=wx.DefaultPosition, size=wx.DefaultSize,
                     style=wx.DEFAULT_FRAME_STYLE, name=wx.FrameNameStr, 
                     subplots=None, on_close = None):
        """Initialize the frame:
            
            parent   - parent window to this one
            id       - window ID
            title    - title in title bar
            pos      - 2-tuple position on screen in pixels
            size     - 2-tuple size of frame in pixels
            style    - window style
            name     - searchable window name
            subplots - 2-tuple indicating the layout of subplots inside the window
            on_close - a function to run when the window closes
            """       
        super(FigureFrame,self).__init__(parent, id, title, pos, size, style, name)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer) 
        matplotlib.rcdefaults()
        self.figure = figure = matplotlib.figure.Figure()
        figure.set_facecolor((1,1,1))
        figure.set_edgecolor((1,1,1))        
        self.panel = FigureCanvasWxAgg(self, -1, self.figure)
        sizer.Add(self.panel, 1, wx.EXPAND)
        #wx.EVT_CLOSE(self, self.on_close)
        if subplots:
            self.subplots = np.zeros(subplots,dtype=object)  
        self.Fit()
        self.Show()
        
    def on_close(self, event):
        if self.close_fn is not None:
            self.close_fn(event)
        self.clf() # Free memory allocated by imshow
        self.Destroy()        
        
################################################################################
class Tracer(wx.Frame, CPATool):
    '''
    A time-lapse visual plot with its controls.
    '''
    def __init__(self, parent, size=(1000,600), **kwargs):
        wx.Frame.__init__(self, parent, -1, size=size, title='Tracer Time-Lapse Visualization Tool', **kwargs)
        CPATool.__init__(self)
        wx.HelpProvider_Set(wx.SimpleHelpProvider())
        self.SetName(self.tool_name)
        
        self.SetMenuBar(wx.MenuBar())
        fileMenu = wx.Menu()
        self.exitMenuItem = fileMenu.Append(wx.ID_EXIT, 'Exit\tCtrl+Q', help='Exit this tool')
        self.GetMenuBar().Append(fileMenu, 'File')  
        
        # TODO: Add this option back when I feel more confident re: track pruning
        #toolsMenu = wx.Menu()
        #pruneMenuItem         = toolsMenu.Append(-1, 'Save pruned tracks', help='Save pruned tracks.')
        #self.GetMenuBar().Append(toolsMenu, 'Tools')        
        
        helpMenu = wx.Menu()
        self.helpMenuItem         = helpMenu.Append(-1, 'Tracer webpage', help='Go to Tracer webpage.')
        self.GetMenuBar().Append(helpMenu, 'Help')         

        props = Properties.getInstance()
        props, success = add_props_field(props)
        # If a required column or table/view is missing, terminate
        if not success:
            self.Destroy()
            return        

        self.control_panel = TracerControlPanel(self)
        self.selected_dataset = self.control_panel.dataset_choice.GetStringSelection()
        self.selected_dataset_track = ORIGINAL_TRACK
        self.dataset_measurement_choices = self.control_panel.dataset_measurement_choice.GetItems()
        self.selected_measurement = self.control_panel.dataset_measurement_choice.GetStringSelection()
        self.selected_metric = self.control_panel.derived_measurement_choice.GetStringSelection()
        self.selected_colormap  = self.control_panel.colormap_choice.GetStringSelection()
        self.available_filters = None
        self.selected_filter = None
        self.plot_updated = False
        self.plot_initialized = False
        self.trajectory_selected = False
        self.selected_node = None
        self.selected_endpoints = [None,None]
        self.image_x_dims = None
        self.image_y_dims = None
        self.do_plots_need_updating = {"dataset":True,
                                       "tracks":True,
                                       "colormap":True,
                                       "measurement":True, 
                                       "trajectories":True,
                                       "filter":False}
        
        self.mayavi_view = MayaviView(self)
        
        self.relationship_cols, self.defined_track_cols, self.relationship_data = create_update_relationship_tables()
        available_tracks = [ORIGINAL_TRACK]+list(set(self.defined_track_cols).difference([ORIGINAL_TRACK]))
        available_datasets = list(set(map(itemgetter(self.relationship_cols[NODE_TBL_ID].index(props.group_id)),self.relationship_data[NODE_TBL_ID])))
        available_datasets = [str(_) for _ in available_datasets]
        self.directed_graph = {_:{} for _ in available_datasets }
        self.connected_nodes = {_:{} for _ in available_datasets }
        self.derived_measurements = {_:{} for _ in available_datasets }
        for dataset in available_datasets:
            for track in available_tracks:
                self.directed_graph[dataset][track] = None
                self.connected_nodes[dataset][track] = None
                self.derived_measurements[dataset][track] = None
            
        self.control_panel.track_collection.SetItems(available_tracks)
        self.control_panel.track_collection.SetSelection(available_tracks.index(ORIGINAL_TRACK))
        self.control_panel.track_collection.Enable(len(available_tracks) > 1)
        self.generate_graph()
        self.update_plot(self.selected_dataset, self.selected_dataset_track) 
        self.plot_initialized = True
        self.figure_panel = self.mayavi_view.edit_traits(
                                            parent=self,
                                            kind='subpanel').control
        self.mayavi_view.dataset = int(self.selected_dataset)
        
        navigation_help_text = ("Tips on navigating the plots:\n"
                                "Rotating the 3-D visualization: Place the mouse pointer over the visualization"
                                "window. Then left-click and drag the mouse pointer in the direction you want to rotate"
                                "the scene, much like rotating an actual object.\n\n"
                                "Zooming in and out: Place the mouse pointer over the visualization"
                                "window. To zoom into the scene, keep the right mouse button pressed and"
                                "drags the mouse upwards. To zoom out of the scene,  keep the right mouse button pressed"
                                "and drags the mouse downwards.\n\n"
                                "Panning: This can be done in one in two ways:\n"
                                "1. Keep the left mouse button pressed and simultaneously holding down the Shift key"
                                "and dragging the mouse in the appropriate direction.\n"
                                "2. Keep the middle mouse button pressed and dragging the mouse in the appropriate"
                                "direction\n\n"
                                "Please note that while the lineage panel can be rotated, zoomed and panned, it is a 2-D"
                                "plot so the top-down view is fixed.")
        self.figure_panel.SetHelpText(" ".join(navigation_help_text))
            
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.figure_panel, 1, wx.EXPAND)
        sizer.Add(self.control_panel, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)
        
        self.figure_panel.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
        
        self.Bind(wx.EVT_MENU, self.on_close, self.exitMenuItem)
        self.Bind(wx.EVT_MENU, self.on_tracer_webpage, self.helpMenuItem)
    
    def on_close(self, event=None):
        try:
            from cellprofiler.utilities.jutil import kill_vm
            kill_vm()
        except:
            print "Failed to kill the Java VM"
        for win in wx.GetTopLevelWindows():
            logging.debug('Destroying: %s'%(win))
            win.Destroy()
        self.Destroy() 
    
    def on_tracer_webpage(self, event=None):
        import webbrowser
        webbrowser.open("http://www.cellprofiler.org/tracer")        
            
    def on_show_all_trajectories(self, event = None):
        self.trajectory_selection = dict.fromkeys(self.connected_nodes[self.selected_dataset][self.selected_dataset_track].keys(),1)
        self.do_plots_need_updating["trajectories"] = True
        self.update_plot(self.selected_dataset, self.selected_dataset_track)    

    def on_display_measurement_heatmap(self, event = None):
        measurement_selection_dlg = self.MultiChoiceDialog(self, 
                                                    message = 'Select the measurements you would like to show.\nNote that each measurement will be shown normalized from 0 to 1',
                                                    caption = 'Select measurements to visualize', 
                                                    choices = [str(x) for x in self.dataset_measurement_choices])
        measurement_selection_dlg.SetSelections(range(0,len(self.dataset_measurement_choices)))   
        if (measurement_selection_dlg.ShowModal() == wx.ID_OK):
            current_selections = measurement_selection_dlg.GetSelections()  
            if len(current_selections) == 0:
                wx.MessageBox("No measurements were selected", caption = "No selection made", parent = self, style = wx.OK | wx.ICON_ERROR)                  
                return
            selected_measurments = itemgetter(*current_selections)(self.dataset_measurement_choices)
            selected_measurments = [selected_measurments] if isinstance(selected_measurments,(str,unicode)) else selected_measurments
            dataset_index = map(itemgetter(self.relationship_cols[NODE_TBL_ID].index(props.group_id)),self.relationship_data[NODE_TBL_ID])
            dataset_image_ids = map(itemgetter(self.relationship_cols[NODE_TBL_ID].index("image_number")),self.relationship_data[NODE_TBL_ID])
            all_image_ids = [_[0]  for _ in zip(dataset_image_ids, dataset_index) if _[1] == int(self.selected_dataset) ] 
            all_image_ids = list(set(all_image_ids))
            heatmap = np.NaN*np.ones((len(selected_measurments),len(all_image_ids)))
            for idx, image_num in enumerate(all_image_ids):
                query = ("SELECT %s"%(",".join(selected_measurments)),
                         "FROM %s"%props.object_table,
                         "WHERE %s = %d"%(props.image_id, image_num))
                query = " ".join(query)
                data = np.array([_ for _ in db.execute(query)]).astype(float)
                heatmap[:,idx] = np.nanmean(data,axis=0)
            
            # Normalize to [0,1] for visualization
            heatmap = heatmap - np.tile(np.nanmin(heatmap,axis=1,keepdims=True),(1,heatmap.shape[1]))
            heatmap = heatmap/np.tile(np.nanmax(heatmap,axis=1,keepdims=True),(1,heatmap.shape[1]))
            
            # Create new figure
            new_title = "Heatmap"
            window = self.create_or_find_plain_figure_window(self, -1, new_title, subplots=(1,1), name=new_title)
            
            # Plot the selected measurement: http://stackoverflow.com/questions/14391959/heatmap-in-matplotlib-with-pcolor
            axes = window.figure.add_subplot(1,1,1)   
            shown_row_labels = list(np.floor(np.linspace(all_image_ids[0],all_image_ids[-1],5)).astype(int)) 
            row_labels = [str(_) if _ in shown_row_labels else '' for _ in all_image_ids ]
            column_labels = selected_measurments
            pcm = axes.pcolormesh(heatmap, cmap=self.selected_colormap,vmin=0.0, vmax=1.0)
            axes.set_xticks(np.arange(heatmap.shape[1])+0.5, minor=False)   
            axes.set_yticks(np.arange(heatmap.shape[0])+0.5, minor=False)
            axes.set_xticklabels(row_labels, minor=False)
            axes.set_yticklabels(column_labels, minor=False)   
            axes.invert_yaxis()
            axes.xaxis.tick_top()
            axes.grid(False)
            axes.set_xlim((0, heatmap.shape[1]))
            axes.set_ylim((0, heatmap.shape[0]))
            from mpl_toolkits.axes_grid1 import make_axes_locatable # From http://matplotlib.org/users/tight_layout_guide.html
            divider = make_axes_locatable(axes)
            cax = divider.append_axes(position="bottom", size="2%", pad="3%")
            cbar = window.figure.colorbar(pcm, orientation='horizontal', cax=cax, ticks=[0, 0.5, 1])
            cbar.ax.tick_params(labelsize=8) 
            axes.tick_params(axis='both',labelsize=8)              
            window.figure.tight_layout()         
        
    def on_select_cell_by_index(self,event = None):
        # First, get the image key
        # Start with the table_id if there is one
        tblNum = None
        if props.table_id:
            dlg = wx.TextEntryDialog(self, props.table_id+':','Enter '+props.table_id)
            dlg.SetValue('0')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    tblNum = int(dlg.GetValue())
                except ValueError:
                    errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(props.table_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                    errdlg.ShowModal()
                    return
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
            
        # Then get the image_id
        dlg = wx.TextEntryDialog(self, props.image_id+':','Enter '+props.image_id)
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                imgNum = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(props.image_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
    
        # Then get the object_id
        dlg = wx.TextEntryDialog(self, props.object_id+':','Enter '+props.object_id)
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                objNum = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value for %s!'%(props.object_id), "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return        
        
        # Build the imkey
        if props.table_id:
            objectkey = (tblNum,imgNum,objNum)
        else:
            objectkey = (imgNum,objNum)
        
        self.selected_node = objectkey
        self.mayavi_view.on_select_point()
    
    def on_show_popup_menu(self, event = None):   
        '''
        Event handler: show the viewer context menu.  
        
        @param event: the event binder
        @type event: wx event
        '''
        class TrajectoryPopupMenu(wx.Menu):
            '''
            Build the context menu that appears when you right-click on a trajectory
            '''
            def __init__(self, parent):
                super(TrajectoryPopupMenu, self).__init__()
                
                self.parent = parent
                
                # Context menu entries
                # - Select cell using (ImageNumber,ObjectNumber)...
                # - Show selected cell (I,J) as
                #   - Image tile
                #   - Full image
                #   - Data table from selected trajectory                
                # - Define trajectory segment with cell (I,J) as
                #   - Endpoint #1
                #   - Endpoint #2
                #   - N frames before/after...
                #   - Entire trajectory
                # - Display defined trajectory segment as
                #   - Image montage
                #   - Plot of current measurement
                # - Show all trajectories
            
                # The 'Show data in table' item and its associated binding
                item = wx.MenuItem(self, wx.NewId(), "Select cell using object ID...")
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.parent.on_select_cell_by_index, item)
                
                if self.parent.selected_node is not None:
                    self.SetTitle("Selected: Trajectory %d, %s %s"%(self.parent.selected_trajectory[0],props.object_name[0],str(self.parent.selected_node)))
                    item = wx.Menu()
                    ID_SHOW_IMAGE_TILE = wx.NewId()
                    ID_SHOW_FULL_IMAGE = wx.NewId()
                    ID_DATA_TABLE = wx.NewId()
                    item.Append(ID_SHOW_IMAGE_TILE,"Image tile")
                    item.Append(ID_SHOW_FULL_IMAGE,"Full image")
                    item.Append(ID_DATA_TABLE,"Data table from selected trajectory")
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_tile,id=ID_SHOW_IMAGE_TILE)
                    self.Bind(wx.EVT_MENU, self.parent.show_full_image,id=ID_SHOW_FULL_IMAGE)    
                    self.Bind(wx.EVT_MENU, self.parent.show_selection_in_table,id=ID_DATA_TABLE)  
                    self.AppendSubMenu(item,"Show selected %s as"%(props.object_name[0]))    
                    
                    #if self.parent.selected_endpoints[0] != None:
                        #item = wx.MenuItem(self, wx.NewId(), "Make point furthest downstream of %s %s as endpoint"%(props.object_name[0],str(self.parent.selected_endpoints[0])))
                        #self.AppendItem(item)
                        #self.Bind(wx.EVT_MENU, self.parent.select_furthest_downstream_point, item)
                    
                    item = wx.Menu()
                    ID_SELECT_ENDPOINT1 = wx.NewId()
                    ID_SELECT_ENDPOINT2 = wx.NewId()
                    ID_SELECT_N_FRAMES = wx.NewId()
                    ID_SELECT_TRAJECTORY = wx.NewId()
                    item.Append(ID_SELECT_ENDPOINT1,"Endpoint #1")
                    item.Append(ID_SELECT_ENDPOINT2,"Endpoint #2")
                    item.Append(ID_SELECT_N_FRAMES,"N frames before/after...")
                    #item.Append(ID_SELECT_TRAJECTORY,"Entire trajectory")                 
                    self.Bind(wx.EVT_MENU, self.parent.select_endpoint1,id=ID_SELECT_ENDPOINT1)
                    self.Bind(wx.EVT_MENU, self.parent.select_endpoint2,id=ID_SELECT_ENDPOINT2)
                    self.Bind(wx.EVT_MENU, self.parent.select_n_frames,id=ID_SELECT_N_FRAMES)
                    self.Bind(wx.EVT_MENU, self.parent.select_entire_trajectory,id=ID_SELECT_TRAJECTORY)                    
                    self.AppendSubMenu(item,"Define trajectory segment with %s as"%(props.object_name[0]))
                    
                    item = wx.Menu()
                    are_endpoints_selected = all([_ != None for _ in self.parent.selected_endpoints])
                    ID_DISPLAY_MONTAGE = wx.NewId()
                    subItem = item.Append(ID_DISPLAY_MONTAGE,"Synchrogram (Image montage)")
                    # Apparently, there's no easy way to enable/disable a wx.Menu
                    # See: http://stackoverflow.com/questions/11576522/wxpython-disable-a-whole-menu
                    subItem.Enable(are_endpoints_selected)
                    ID_DISPLAY_GRAPH = wx.NewId()
                    subItem = item.Append(ID_DISPLAY_GRAPH,"Plot of currently selected measurement")
                    subItem.Enable(are_endpoints_selected)
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_montage,id=ID_DISPLAY_MONTAGE) 
                    self.Bind(wx.EVT_MENU, self.parent.show_cell_measurement_plot,id=ID_DISPLAY_GRAPH)   
                    self.AppendSubMenu(item,"Display defined trajectory segment as")
                    
                # The 'Make all trajectories visble' item and its associated binding
                item = wx.MenuItem(self, wx.NewId(), "Make all trajectories visible")
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.parent.on_show_all_trajectories, item)
                
                # The 'Display measurement heatmap' item and its associated binding
                item = wx.MenuItem(self, wx.NewId(), "Display measurement heatmap...")                
                self.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.parent.on_display_measurement_heatmap, item)                

        # The event (mouse right-click) position.
        pos = event.GetPosition()
        # Converts the position to mayavi internal coordinates.
        pos = self.figure_panel.ScreenToClient(pos)                                                        
        # Show the context menu.      
        self.PopupMenu(TrajectoryPopupMenu(self), pos)    

    def show_selection_in_table(self, event = None):
        '''Callback for "Show selection in a table" popup item.'''
        keys = [self.connected_nodes[self.selected_dataset][self.selected_dataset_track][item].nodes() for item in self.selected_trajectory]
        keys = [item for sublist in keys for item in sublist]
        tracking_label,timepoint,data = zip(*np.array([(self.directed_graph[self.selected_dataset][self.selected_dataset_track].node[node]["label"],
                                                        self.directed_graph[self.selected_dataset][self.selected_dataset_track].node[node]["t"],
                                                        self.directed_graph[self.selected_dataset][self.selected_dataset_track].node[node][SCALAR_VAL]) for node in keys]))
        table_data = np.hstack((np.array(keys), np.array((tracking_label,timepoint,data)).T))
        column_labels = list(object_key_columns())
        key_col_indices = list(xrange(len(column_labels)))
        column_labels += ['Tracking Label','Timepoint ID',self.selected_measurement]
        group = 'Object'
        grid = tableviewer.TableViewer(self, title='Data table from trajectory %d containing %s %s'%(self.selected_trajectory[0],props.object_name[0],self.selected_node))
        grid.table_from_array(table_data, column_labels, group, key_col_indices)
        # Sort by label first, then by timepoint
        grid.grid.Table.set_sort_col(len(key_col_indices)+1)
        grid.grid.Table.set_sort_col(len(key_col_indices)+2,add=True) 
        # Hide the object key columns
        grid.grid.Table.set_shown_columns(list(xrange(len(key_col_indices),len(column_labels))))
        grid.grid.Table.ResetView(grid.grid)
        grid.set_fitted_col_widths()
        grid.Show()
        
    def select_endpoint1(self,event=None):
        self.selected_endpoints[0] = self.selected_node
        #self.highlight_selected_endpoint(1)        
        
    def select_endpoint2(self,event=None):
        self.selected_endpoints[1] = self.selected_node
        #self.highlight_selected_endpoint(2)
    
    def highlight_selected_endpoint(self, num):
        idx = num-1
        self.mayavi_view.trajectory_point_selection_outline[idx].mlab_source.dataset.points[0] = (np.mean(self.mayavi_view.trajectory_selection_outline.bounds[:2]),
                                                                                                  np.mean(self.mayavi_view.trajectory_selection_outline.bounds[2:4]),
                                                                                                  np.mean(self.mayavi_view.trajectory_selection_outline.bounds[4:]))
        self.mayavi_view.trajectory_point_selection_outline[idx].actor.actor.visibility = 1
        
        self.mayavi_view.lineage_point_selection_outline[idx].mlab_source.dataset.points[0] = (np.mean(self.mayavi_view.lineage_selection_outline.bounds[:2]),
                                                                                               np.mean(self.mayavi_view.lineage_selection_outline.bounds[2:4]),
                                                                                               0)
        self.mayavi_view.lineage_point_selection_outline[idx].actor.actor.visibility = 1  
    
    def select_n_frames(self, event = None):
        dlg = wx.TextEntryDialog(self, "Enter the number of frames before and after")
        n_frames = 0
        #dlg.SetValue(str(n_frames))
        if dlg.ShowModal() == wx.ID_OK:
            try:
                n_frames = int(dlg.GetValue())
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value', "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        if n_frames < 0:
            errdlg = wx.MessageDialog(self, 'Only positive values allowed', "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
            errdlg.ShowModal()
            return            
        
        trajectory_to_use = self.pick_trajectory_to_use()
        subgraph = self.connected_nodes[self.selected_dataset][self.selected_dataset_track][trajectory_to_use]
        # Find all nodes within N frames. This includes nodes that occur after a branch so extra work is needed to figure out which path to follow
        # For a directed graph, nx.single_source_shortest_path_length returns only the upstream nodes, so converted to undirected
        nodes_within_n_frames = nx.single_source_shortest_path_length(subgraph.to_undirected(),self.selected_node,n_frames)
        # Unfortunately, if there branches upstream of the selected node, nodes_within_n_frames can contain upstream nodes from a different branch. So we examine further.
        downstream_nodes_within_n_frames = nx.single_source_shortest_path_length(subgraph,self.selected_node,n_frames) 
        upstream_nodes_within_n_frames = {_[0]: _[1] for _ in nodes_within_n_frames.items() if _[0] not in downstream_nodes_within_n_frames.keys()}
        # Obtain the final node set by checking whether a path exists for upstream nodes to the target via the *directed* graph
        [nodes_within_n_frames.pop(_) for _ in upstream_nodes_within_n_frames.keys() if not nx.has_path(subgraph,_,self.selected_node)]
        # Find the candidate terminal nodes @ N frames away (before/after)  
        node_attributes = nx.get_node_attributes(subgraph,'t')
        sorted_nodes = sorted([(key,val,nodes_within_n_frames[key]) for key,val in node_attributes.items() if key in nodes_within_n_frames.keys()],key=itemgetter(1))
        idx = sorted_nodes.index((self.selected_node,node_attributes[self.selected_node],0))
        # A node is at the start/end of the selection if: (1) it's N frames away, or (2) it's at the start/end of the trajectory branch, even if < N frames away
        start_nodes = [_ for _ in sorted_nodes if (_[2] == n_frames or subgraph.in_degree(_[0])  == 0) and _[1] <= sorted_nodes[idx][1] ]
        end_nodes =   [_ for _ in sorted_nodes if (_[2] == n_frames or subgraph.out_degree(_[0]) == 0) and _[1] >= sorted_nodes[idx][1] ]
        
        # If we have multiple candidates on either side, try to intelligently pick the right one
        def pick_furthest_node(node_set):
            bc = nx.get_node_attributes(subgraph,METRIC_BC)
            if len(node_set) > 1:
                # First, try to pick the furthest one away
                bounding_frame = sorted(node_set,key=itemgetter(2))[-1][2]
                node_set = [_ for _ in node_set if _[2] == bounding_frame]
                if len(node_set) > 1: 
                    # If we still have multiple candidates, pick the one with the higher betweenness centrality score, i.e, longer track
                    temp = [bc[_[0]] for _ in node_set]
                    # If the betweenness centrality scores are equal, this picks the first one
                    # HOWEVER, I found that this can lead to the wrong track being followed, see (19,1) in dataset 1 for example
                    # TODO: It's probably better to either check <object>_TrackObjects_Area and pick the closest one to the selected object,
                    # or if I really want to be slick, compute the Kalman predicted location and match from that (LAP only) 
                    idx = temp.index(max(temp))                    
                    node_set = node_set[idx][0] 
                else:
                    node_set = node_set[0][0]   
            else:
                node_set = node_set[0][0]
            return node_set
                
        bc = nx.get_node_attributes(subgraph,METRIC_BC)
        start_nodes = pick_furthest_node(start_nodes)
        end_nodes = pick_furthest_node(end_nodes)
        
        self.selected_endpoints = [start_nodes, end_nodes]     
        #self.highlight_selected_endpoint(1)
        #self.highlight_selected_endpoint(2)        
         
    def select_entire_trajectory(self, event = None):
        trajectory_to_use = self.pick_trajectory_to_use()
        # TODO: Decide on proper behavior if selected node contains multiple end nodes. Use all end nodes? Use terminal nodes?
        self.selected_endpoints = [self.start_nodes[trajectory_to_use], self.end_nodes[trajectory_to_use]]
        #self.highlight_selected_endpoint(1)
        #self.highlight_selected_endpoint(2)
    
    def pick_trajectory_to_use(self, event = None):
        # Pick out the trajectory containing the selected node
        trajectory_to_use = [key for key, subgraph in self.connected_nodes[self.selected_dataset][self.selected_dataset_track].items() if self.selected_node in subgraph]
        if len(trajectory_to_use) > 1:
            print "Should have only one trajectory selected"
            return [],[]
        else:
            trajectory_to_use = trajectory_to_use[0]    
        return trajectory_to_use
        
    def validate_node_ordering(self):
        trajectory_to_use = self.pick_trajectory_to_use()
            
        # Check the node ordering
        selected_endpoints = self.selected_endpoints if nx.has_path(self.directed_graph[self.selected_dataset][self.selected_dataset_track], self.selected_endpoints[0],self.selected_endpoints[1]) else self.selected_endpoints[::-1]        
        return selected_endpoints, trajectory_to_use
    
    def show_cell_montage(self, event = None):
        # Check the node ordering
        connected_nodes = self.connected_nodes[self.selected_dataset][self.selected_dataset_track]
        selected_endpoints, trajectory_to_use = self.validate_node_ordering()

        # Do piecemeal to prevent wrong path being picked if selected node is on a loop
        current_trajectory_keys = nx.shortest_path(connected_nodes[trajectory_to_use], selected_endpoints[0],self.selected_node) + \
                                    nx.shortest_path(connected_nodes[trajectory_to_use], self.selected_node, selected_endpoints[1])[1:]
        montage_frame = sortbin.CellMontageFrame(get_main_frame_or_none(),"Image montage from trajectory %d containing %s %s"%(trajectory_to_use, props.object_name[0], self.selected_node))
        montage_frame.Show()
        montage_frame.add_objects(current_trajectory_keys)
        [tile.Select() for tile in montage_frame.sb.tiles if tile.obKey == self.selected_node]
    
    def show_cell_measurement_plot(self, event = None):
        connected_nodes = self.connected_nodes[self.selected_dataset][self.selected_dataset_track]
        directed_graph = self.directed_graph[self.selected_dataset][self.selected_dataset_track]
        # Check the node ordering
        selected_endpoints, trajectory_to_use = self.validate_node_ordering()
        
        # Create new figure
        new_title = "Trajectory %d, %s %s and %s"%(trajectory_to_use, props.object_name[0],selected_endpoints[0],selected_endpoints[1])
        window = self.create_or_find_plain_figure_window(self, -1, new_title, subplots=(1,1), name=new_title)
        
        # Plot the selected measurement
        current_trajectory_keys = nx.shortest_path(connected_nodes[trajectory_to_use], selected_endpoints[0],self.selected_node) + \
                                    nx.shortest_path(connected_nodes[trajectory_to_use], self.selected_node, selected_endpoints[1])[1:]
        timepoint,data = zip(*np.array([(directed_graph.node[node]["t"],
                                         directed_graph.node[node][SCALAR_VAL]) 
                                        for node in current_trajectory_keys]))
        axes = window.figure.add_subplot(1,1,1)   
        
        axes.plot(timepoint, data, color='blue', markerfacecolor='white', linestyle='-', marker='o', markeredgecolor='blue')
        axes.set_xlabel("Timepoint")
        axes.set_ylabel(self.selected_measurement)                
    
    def show_cell_tile(self, event = None):
        trajectory_to_use = self.pick_trajectory_to_use()
        montage_frame = sortbin.CellMontageFrame(get_main_frame_or_none(),"Image tile of %s %s in trajectory %d"%(props.object_name[0],self.selected_node,trajectory_to_use))
        montage_frame.Show()
        montage_frame.add_objects([self.selected_node])   
    
    def show_full_image(self, event = None):
        imViewer = imagetools.ShowImage(self.selected_node, props.image_channel_colors, parent=self)
        imViewer.imagePanel.SelectPoint(db.GetObjectCoords(self.selected_node))
    
    def dataset_selected(self, selected_dataset=None, selected_dataset_track=None):
        # Disable trajectory selection button until plot updated or the currently plotted dataset is selected
        self.do_plots_need_updating["dataset"] = False
        if self.selected_dataset == selected_dataset:
            self.control_panel.trajectory_selection_button.Enable()
        else:
            self.control_panel.trajectory_selection_button.Disable()
            self.selected_dataset = selected_dataset
            self.do_plots_need_updating["dataset"] = True
            
    def track_collection_selected(self, selected_dataset=None, selected_dataset_track=None):
        self.selected_dataset_track = selected_dataset_track
        self.do_plots_need_updating["tracks"] = True
        self.update_plot(selected_dataset, selected_dataset_track)
    
    def dataset_measurement_selected(self, selected_measurement=None, selected_metric=None):
        self.do_plots_need_updating["measurement"] = False
        if selected_measurement == OTHER_METRICS:
            # http://stackoverflow.com/questions/14366594/wxpython-how-do-you-access-the-objects-which-youve-placed-inside-of-a-wx-sizer
            [_.Window.Enable() for _ in self.control_panel.derived_measurement_sizer.Children if _.IsWindow()]
            self.derived_measurement_selected(selected_metric)
        else:
            [_.Window.Disable() for _ in self.control_panel.derived_measurement_sizer.Children if _.IsWindow()]
        if self.selected_measurement == selected_measurement:
            self.control_panel.trajectory_selection_button.Enable()
        else:
            self.selected_measurement = selected_measurement            
            self.control_panel.trajectory_selection_button.Disable()  
            self.do_plots_need_updating["measurement"] = True

    def derived_measurement_selected(self, selected_metric=None):
        self.selected_metric = selected_metric
        widget_dict = self.control_panel.derived_metric_to_widget_mapping
        for _ in widget_dict.items():
            if _[1] is None:
                pass
            else:
                [item.Show(_[0] == selected_metric) for item in _[1]]
        self.control_panel.preview_prune_button.Show(True)
        
        # http://stackoverflow.com/questions/2562063/why-does-hideing-and-showing-panels-in-wxpython-result-in-the-sizer-changi
        self.control_panel.derived_measurement_sizer.Layout()
           
        self.do_plots_need_updating["measurement"] = True        
    
    def toggle_preview_pruned_graph(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
                                
        # Set the visibility of the nodes
        attr = nx.get_node_attributes(directed_graph, VISIBLE)
        if self.control_panel.preview_prune_button.GetValue():
            # Set visibility based on the selected metric and trajectory selection
            for key,subgraph in connected_nodes.items():
                is_currently_visible = self.trajectory_selection[key]              
                subattr = nx.get_node_attributes(subgraph, self.selected_metric+VISIBLE_SUFFIX)
                for _ in subattr.items():
                    attr[_[0]] = _[1] & is_currently_visible
        else:
            # Set visibility based on trajectory selection only
            for key,subgraph in connected_nodes.items():
                is_currently_visible = self.trajectory_selection[key] 
                for _ in subgraph.nodes():
                    attr[_] = is_currently_visible      
        nx.set_node_attributes(directed_graph, VISIBLE, attr)
        
        self.do_plots_need_updating["trajectories"] = True
        self.update_plot(selected_dataset,selected_dataset_track)
        
    def add_pruning_to_edits(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
                                        
        attr = nx.get_node_attributes(directed_graph, IS_REMOVED)
        for key,subgraph in connected_nodes.items():
            subattr = nx.get_node_attributes(subgraph, self.selected_metric+VISIBLE_SUFFIX)
            for _ in subattr.items():
                attr[_[0]] = (not _[1]) or attr[_[0]]  # A node is removed if it's pruned (i.e, not visible) or it's already removed
        nx.set_node_attributes(directed_graph, IS_REMOVED, attr) 
        
        attr = nx.get_edge_attributes(directed_graph, IS_REMOVED)
        for key,subgraph in connected_nodes.items():
            subattr = nx.get_edge_attributes(subgraph, self.selected_metric+VISIBLE_SUFFIX)
            for _ in subattr.items():
                attr[_[0]] = (not _[1]) or attr[_[0]]  # An edge is removed if it's pruned (i.e, not visible) or it's already removed
        nx.set_edge_attributes(directed_graph, IS_REMOVED, attr) 
        
        dlg = wx.MessageDialog(self, 
                               "The selected pruning has been added to the list of trajectory edits."
                               "You can save the edits to the database by selecting the 'Save Edited "
                               "Tracks' button", 
                               "Edits Added", wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
    
    def save_edited_tracks(self, selected_dataset=None, selected_dataset_track=None):
        dlg = wx.TextEntryDialog(self, 'Specify a name for your edited tracks','Enter track identifier')
        dlg.SetValue('MyEditedTracks')
        if dlg.ShowModal() == wx.ID_OK:
            try:
                # TODO: Validate text entry
                trackID = dlg.GetValue()
            except ValueError:
                errdlg = wx.MessageDialog(self, 'Invalid value!', "Invalid value", wx.OK|wx.ICON_EXCLAMATION)
                errdlg.ShowModal()
                return
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        # Create/update the table
        table_name = get_edited_relationship_tablenames()
        for key in [EDGE_TBL_ID, NODE_TBL_ID]:
            logging.info('Populating table %s...'%table_name[key])
            
            # Create new column containing 1 if edge is kept, 0 if not
            newcol = len(self.relationship_data[key])*[1]
            attr = nx.get_node_attributes(self.directed_graph[selected_dataset][selected_dataset_track], IS_REMOVED)
            all_edges = map(itemgetter(0,1,2,3), self.relationship_data[key])
            for _ in attr.items():
                if _[1]:
                    for successor in self.directed_graph[selected_dataset][selected_dataset_track].successors_iter(_[0]):
                        newcol[all_edges.index(_[0]+successor)] = 0
                
            if self.relationship_cols[key].count(trackID) == 0:
                colnames = self.relationship_cols[key] + [trackID]
                tableData = np.hstack((np.array(self.relationship_data[key]),np.array(newcol)[np.newaxis].T))
            else:
                dlg = wx.MessageDialog(self, 
                                       'This track already exists. Do you want to overwrite it?', 
                                       "Overwrite track?", wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION|wx.STAY_ON_TOP)
                if dlg.ShowModal() == wx.ID_NO:
                    dlg.Destroy()
                    return
                else:
                    colnames = self.relationship_cols[key] 
                    tableData = np.array(self.relationship_data[key])
                    tableData[:,colnames.index(trackID)] = np.array(newcol)
                    dlg.Destroy()
    
            success = db.CreateTableFromData(tableData, colnames, table_name[key], temporary=False)
        
        # Update drop-down listings
        track_choices = self.control_panel.track_collection.GetItems() + [trackID]
        self.control_panel.track_collection.SetItems(track_choices)
        self.control_panel.track_collection.SetSelection(track_choices.index(trackID))   
        self.control_panel.track_collection.Enable()  
        self.selected_dataset_track = trackID
        self.selected_measurement = props.image_id
        self.control_panel.dataset_measurement_choice.SetSelection(self.control_panel.dataset_measurement_choices.index(self.selected_measurement))
        self.dataset_measurement_selected()
        
        # Update bookkeepinng and display
        self.do_plots_need_updating["dataset"] = True
        self.directed_graph[selected_dataset][trackID] = {}
        self.connected_nodes[selected_dataset][trackID] = {}
        self.derived_measurements[selected_dataset][trackID] = {}        
        self.track_collection_selected()
        
    def colormap_selected(self, selected_colormap = None):
        self.do_plots_need_updating["colormap"] = False
        if self.selected_colormap != selected_colormap:
            self.selected_colormap = selected_colormap    
            self.do_plots_need_updating["colormap"] = True
                                                                   
    def create_new_filter(self):
        cff = ColumnFilterDialog(self, tables=[props.object_table],size=(600,300))
        if cff.ShowModal() == wx.OK:
            fltr = cff.get_filter()
            filter_name = cff.get_filter_name()
            # I *don't* think I want to register the filter name here. TODO: Check into this
            props._filters[filter_name] = fltr
            items = self.control_panel.filter_choices.GetItems()
            self.control_panel.filter_choices.SetItems(items[:-1]+[filter_name]+items[-1:])
            self.control_panel.filter_choices.Select(len(items)-1)
            if self.available_filters is None:
                self.available_filters = {filter_name: fltr} 
            else:
                self.available_filters[filter_name] = fltr
        else:
            self.control_panel.filter_choices.Select(0)
        cff.Destroy()  
        
    def filter_selected(self, selected_dataset=None, selected_dataset_track=None, selected_filter=None):
        if self.selected_filter == selected_filter:
            return
        else:
            self.selected_filter == selected_filter
            fltr = self.available_filters[self.selected_filter]
            
            import sqltools
            from dbconnect import UniqueObjectClause
            query = 'SELECT %s FROM %s WHERE %s' % (UniqueObjectClause(props.object_table), ','.join(fltr.get_tables()), str(fltr))
            node_list = db.execute(query)
            attr = {_: False for _ in self.directed_graph[selected_dataset][selected_dataset_track].nodes()} 
            for _ in node_list:
                if _ in attr:
                    attr[_] = True
            nx.set_node_attributes(self.directed_graph[selected_dataset][selected_dataset_track],"f",attr)   
            
            #for key,subgraph in self.connected_nodes.items():
                #for node_key in self.connected_nodes[key]:
                    #directed_graph.node[node_key][VISIBLE] = (value != 0)
            #self.update_plot(selected_dataset, selected_dataset_track)                
                                                                    
    class MultiChoiceDialog (wx.Dialog):
        '''
        Build the dialog box
        '''
        def __init__(self, parent, message="", caption="", choices=[]):
            wx.Dialog.__init__(self, parent, -1)
            self.SetTitle(caption)
            sizer1 = wx.BoxSizer(wx.VERTICAL)
            self.message = wx.StaticText(self, -1, message)
            self.clb = wx.CheckListBox(self, -1, choices = choices)
            self.selectallbtn = wx.Button(self,-1,"Select all")
            self.deselectallbtn = wx.Button(self,-1,"Deselect all")
            sizer2 = wx.BoxSizer(wx.HORIZONTAL)
            sizer2.Add(self.selectallbtn,0, wx.ALL | wx.EXPAND, 5)
            sizer2.Add(self.deselectallbtn,0, wx.ALL | wx.EXPAND, 5)
            self.dlgbtns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
            self.Bind(wx.EVT_BUTTON, self.SelectAll, self.selectallbtn)
            self.Bind(wx.EVT_BUTTON, self.DeselectAll, self.deselectallbtn)
            
            sizer1.Add(self.message, 0, wx.ALL | wx.EXPAND, 5)
            sizer1.Add(self.clb, 1, wx.ALL | wx.EXPAND, 5)
            sizer1.Add(sizer2, 0, wx.EXPAND)
            sizer1.Add(self.dlgbtns, 0, wx.ALL | wx.EXPAND, 5)
            self.SetSizer(sizer1)
            self.Fit()
            
        def GetSelections(self):
            return self.clb.GetChecked()
        
        def SetSelections(self, indexes):
            return self.clb.SetChecked(indexes)

        def SelectAll(self, event):
            for i in range(self.clb.GetCount()):
                self.clb.Check(i, True)
                
        def DeselectAll(self, event):
            for i in range(self.clb.GetCount()):
                self.clb.Check(i, False)    

    def update_trajectory_selection(self, selected_dataset=None, selected_dataset_track=None):
        
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
                                                            
        trajectory_selection_dlg = self.MultiChoiceDialog(self, 
                                                          message = 'Select the objects you would like to show.',
                                                          caption = 'Select trajectories to visualize', 
                                                          choices = [str(x) for x in connected_nodes.keys()])
                
        current_selection = np.nonzero(self.trajectory_selection.values())[0]
        trajectory_selection_dlg.SetSelections(current_selection)
        
        if (trajectory_selection_dlg.ShowModal() == wx.ID_OK):
            current_selection = trajectory_selection_dlg.GetSelections()
            all_labels = connected_nodes.keys()
            self.trajectory_selection = dict.fromkeys(all_labels,0)
            for x in current_selection:
                self.trajectory_selection[all_labels[x]] = 1
            self.do_plots_need_updating["trajectories"] = True
            
            for key, value in self.trajectory_selection.items():
                for node_key in connected_nodes[key]:
                    directed_graph.node[node_key][VISIBLE] = (value != 0)
            self.update_plot(selected_dataset,selected_dataset_track)                    
    
    def update_plot(self, selected_dataset=None, selected_dataset_track=None):
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        
        #self.do_plots_need_updating["filter"] = self.control_panel.enable_filtering_checkbox.IsChecked()   
        
        self.set_scalar_values(selected_dataset, selected_dataset_track)
        self.mayavi_view.draw_trajectories(self.do_plots_need_updating, 
                                           directed_graph, 
                                           connected_nodes, 
                                           self.selected_colormap, 
                                           self.scalar_data)
        self.mayavi_view.draw_lineage(self.do_plots_need_updating, 
                                      directed_graph, 
                                      connected_nodes, 
                                      self.selected_colormap, 
                                      self.scalar_data )
        
        self.control_panel.trajectory_selection_button.Enable()
        if self.do_plots_need_updating["dataset"]:
            self.trajectory_selection = dict.fromkeys(connected_nodes.keys(),1)
        
        self.do_plots_need_updating["dataset"] = False
        self.do_plots_need_updating["tracks"] = False
        self.do_plots_need_updating["colormap"] = False
        self.do_plots_need_updating["measurement"] = False
        self.do_plots_need_updating["trajectories"] = False
        
    def generate_graph(self, selected_dataset=None, selected_track=None):
        # Generate the graph relationship if the dataset has been updated
        
        #if not self.do_plots_need_updating["filter"]:
            #self.selected_filter = None
        #else:
            #self.selected_filter = []
            #for current_filter in self.control_panel.filter_panel.filters:
                #self.selected_filter.append(" ".join((props.object_table + "." + current_filter.colChoice.GetStringSelection(), 
                                                      #current_filter.comparatorChoice.GetStringSelection(),
                                                      #current_filter.valueField.GetValue())))
       
        if selected_dataset == None and selected_track == None:
            # No data sources or tracks specified: Initialize all graphs from scratch
            available_datasets = list(set(map(itemgetter(self.relationship_cols[NODE_TBL_ID].index(props.group_id)),self.relationship_data[NODE_TBL_ID])))
            available_datasets = [str(_) for _ in available_datasets]            
            available_tracks = self.defined_track_cols
        else:
            # Data source and/or track specified: Add a new graph
            available_datasets = [selected_dataset]
            available_tracks = [selected_track]
            
        for dataset_id in available_datasets:
            column_names,trajectory_info = obtain_tracking_data(dataset_id,
                                                                self.selected_measurement if self.selected_measurement in self.dataset_measurement_choices else None, 
                                                                #self.selected_filter
                                                                )              
            for track_id in available_tracks:     
                if len(trajectory_info) == 0:
                    logging.info("No object data found")
                    wx.MessageBox('The table %s referenced in the properties file contains no object information.'%props.object_table,
                                  caption = "No data found",
                                    parent = self.control_panel,
                                    style = wx.OK | wx.ICON_ERROR)            
                    return                

                logging.info("Retrieved %d %s from dataset %s (%s)"%(len(trajectory_info),
                                                                     props.object_name[1],
                                                                     dataset_id, 
                                                                     track_id))
                
                relationship_index = {}
                for key in [NODE_TBL_ID, EDGE_TBL_ID]:
                    relationship_index[key] = map(itemgetter(self.relationship_cols[key].index(track_id)),self.relationship_data[key])
                    dataset_index = map(itemgetter(self.relationship_cols[key].index(props.group_id)),self.relationship_data[key])
                    # Index is 1 if (a) the row was flagged in the saved track and (b) the dataset is currently active 
                    relationship_index[key] = [_[0] == 1 and _[1] == int(dataset_id) for _ in zip(relationship_index[key], dataset_index)] # Convert to boolean            

                self.directed_graph[dataset_id][track_id] = nx.DiGraph()
                key_length = len(object_key_columns())
                indices = range(0,key_length)
                node_ids = map(itemgetter(*indices),trajectory_info)
                indices = range(key_length,len(trajectory_info[0]))
                attr = [dict(zip(track_attributes,_)) for _ in map(itemgetter(*indices),trajectory_info)]
                for _ in attr:
                    _[VISIBLE] = True
                    _[IS_REMOVED] = False
            
                # Add nodes
                selected_relationships = [_[0] for _ in zip(self.relationship_data[NODE_TBL_ID],relationship_index[NODE_TBL_ID]) if _[1]]
                selected_node_ids = map(itemgetter(0,1),selected_relationships)
                temp = dict(zip(node_ids,attr))
                self.directed_graph[dataset_id][track_id].add_nodes_from(zip(selected_node_ids,
                                                                             [temp[_] for _ in selected_node_ids]))
            
                # Add edges
                selected_relationships = [_[0] for _ in zip(self.relationship_data[EDGE_TBL_ID],relationship_index[EDGE_TBL_ID]) if _[1]]
                selected_node_ids = map(itemgetter(2,3),selected_relationships)
                selected_parent_node_ids = map(itemgetter(0,1),selected_relationships)       
                attr = [{VISIBLE: True, IS_REMOVED: False} for _ in selected_parent_node_ids]
                self.directed_graph[dataset_id][track_id].add_edges_from(zip(selected_parent_node_ids,
                                                                             selected_node_ids, 
                                                                             attr))
                
                logging.info("Constructed graph consisting of %d nodes and %d edges"%(self.directed_graph[dataset_id][track_id].number_of_nodes(),
                                                                                      self.directed_graph[dataset_id][track_id].number_of_edges()))
            
                t1 = time.clock()
                G = nx.convert_node_labels_to_integers(self.directed_graph[dataset_id][track_id],
                                                       first_label=0,
                                                       ordering="default")
                mapping = dict(zip(G.nodes(),self.directed_graph[dataset_id][track_id].nodes()))
                glayout.layer_layout(G, level_attribute = "t")
                nx.relabel_nodes(G, mapping,copy=False) # Map back to original graph labels
                node_positions = dict(zip(G.nodes(),[[G.node[key]["t"],G.node[key]["y"]] for key in G.nodes()]))
                self.end_frame = end_frame = max(np.array(node_positions.values())[:,0])
                self.start_frame = start_frame = min(np.array(node_positions.values())[:,0])
            
                # Adjust the y-spacing between trajectories so it the plot is roughly square, to avoid nasty Mayavi axis scaling issues later
                # See: http://stackoverflow.com/questions/13015097/how-do-i-scale-the-x-and-y-axes-in-mayavi2
                xy = np.array([node_positions[key] for key in G.nodes()])
                ys = float(max(xy[:,1]) - min(xy[:,1]))
                if ys == 0.0: 
                    scaling_y = 1.0
                else:
                    scaling_y = 1.0/ys*float(max(xy[:,0]) - min(xy[:,0]))
                for key in G.nodes(): node_positions[key][1] *= scaling_y
            
                self.lineage_node_positions = node_positions  
                nx.set_node_attributes(self.directed_graph[dataset_id][track_id],
                                       L_TCOORD,
                                       dict(zip(node_positions.keys(), [item[0] for item in node_positions.values()])))
                nx.set_node_attributes(self.directed_graph[dataset_id][track_id],
                                       L_YCOORD,
                                       dict(zip(node_positions.keys(), [item[1] for item in node_positions.values()])))         
                
                t2 = time.clock()
                logging.info("Computed lineage layout: %s (%s): %.2f sec"%(dataset_id, track_id, t2-t1))
            
                # Each track gets its own indexed subgraph. Later operations to the graphs are referenced to this key.
                # According to http://stackoverflow.com/questions/18643789/how-to-find-subgraphs-in-a-directed-graph-without-converting-to-undirected-graph,
                #  weakly_connected_component_subgraphs maintains directionality
                connected_nodes = tuple(nx.weakly_connected_component_subgraphs(self.directed_graph[dataset_id][track_id]))
                self.connected_nodes[dataset_id][track_id] = dict(zip(range(1,len(connected_nodes)+1),connected_nodes))
                for key, subgraph in self.connected_nodes[dataset_id][track_id].items():
                    nx.set_node_attributes(subgraph, COMPONENT_ID, {_:key for _ in subgraph.nodes()})
            
                # Set graph attributes
                for key,subgraph in self.connected_nodes[dataset_id][track_id].items():
                    # Set connect component ID in ful graph                
                    nodes = subgraph.nodes()
                    nx.set_node_attributes(self.directed_graph[dataset_id][track_id], SUBGRAPH_ID, dict(zip(nodes,[key]*len(nodes))))
                    
                    # Find start/end nodes by checking for nodes with no outgoing/ingoing edges
                    # Set end nodes
                    out_degrees = subgraph.out_degree()
                    # HT to http://stackoverflow.com/questions/9106065/python-list-slicing-with-arbitrary-indices
                    #  for using itemgetter to slice a list using a list of indices
                    idx = np.nonzero(np.array(out_degrees.values()) == 0)[0]
                    # If 1 node is returned, it's a naked tuple instead of a tuple of tuples, so we have to extract the innermost element in this case
                    end_nodes = itemgetter(*idx)(out_degrees.keys())
                    end_nodes = list(end_nodes) if isinstance(end_nodes[0],tuple) else list((end_nodes,))
                    attr = dict.fromkeys(subgraph.nodes(), False)
                    for _ in end_nodes:
                        attr[_] = True
                    nx.set_node_attributes(subgraph, END_NODES, attr)
                    
                    # Set start nodes: nodes at the beginning of the track
                    in_degrees = subgraph.in_degree()
                    # Since it's a directed graph, I know that the in_degree result will have the starting node at index 0.
                    #  So even if there are multiple nodes with in-degree 0, this approach will get the first one.
                    #  HT to http://stackoverflow.com/a/13149770/2116023 for the index approach
                    start_nodes = [in_degrees.keys()[in_degrees.values().index(0)]]   
                    attr = dict.fromkeys(subgraph.nodes(), False)
                    for _ in start_nodes:
                        attr[_] = True   
                    nx.set_node_attributes(subgraph, START_NODES, attr)
                    
                    # Set branchpoints: nodes with two or more children
                    idx = np.nonzero(np.array(out_degrees.values()) > 1)[0]
                    branch_nodes = itemgetter(*idx)(out_degrees.keys()) if len(idx) > 0 else []
                    if branch_nodes != []:
                        branch_nodes = list(branch_nodes) if isinstance(branch_nodes[0],tuple) else list((branch_nodes,))                
                    attr = dict.fromkeys(subgraph.nodes(), False)
                    for _ in branch_nodes:
                        attr[_] = True                   
                    nx.set_node_attributes(subgraph, BRANCH_NODES, attr)
                    
                    # Set terminal nodes: nodes at the end of the track; subset of end nodes
                    # Pick terminal nodes based on distance from start node
                    terminal_nodes = {}
                    max_dist = 0
                    for _ in end_nodes:
                        try:
                            dist = nx.shortest_path_length(subgraph,source=start_nodes[0],target=_)
                            terminal_nodes[_] = dist
                            max_dist = max([max_dist, dist])
                        except:
                            pass
                    terminal_nodes = [_[0] for _ in terminal_nodes.items() if _[1] == max_dist]
                    attr = dict.fromkeys(subgraph.nodes(), False)
                    for _ in terminal_nodes:
                        attr[_] = True    
                    nx.set_node_attributes(subgraph, TERMINAL_NODES, attr)                     
                                        
                    # Set finishing nodes: nodes at the end of the movie; subset of terminal nodes
                    idx = np.nonzero(np.array(subgraph.nodes())[:,0] == end_frame)[0]
                    finishing_nodes = itemgetter(*idx)(subgraph.nodes()) if len(idx) > 0 else []  
                    if finishing_nodes != []:
                        finishing_nodes = list(finishing_nodes) if isinstance(finishing_nodes[0],tuple) else list((finishing_nodes,))                 
                    attr = dict.fromkeys(subgraph.nodes(), False)
                    for _ in finishing_nodes:
                        attr[_] = True    
                    nx.set_node_attributes(subgraph, FINISH_NODES, attr)      

                # Calculate measurements created from existing measurments
                self.derived_measurements[dataset_id][track_id] = self.add_derived_measurements(dataset_id, track_id)
                
        if selected_dataset == None and selected_track == None:
            dataset_id = available_datasets[0]
            track_id = ORIGINAL_TRACK
        else:
            dataset_id = selected_dataset
            track_id = selected_track 
            
        # Insert ref to derived measurements and update current selection
        measurement_choices = self.control_panel.dataset_measurement_choices + [OTHER_METRICS]
        current_measurement_choice = self.control_panel.dataset_measurement_choice.GetSelection() 
        self.control_panel.dataset_measurement_choice.SetItems(measurement_choices)
        self.control_panel.dataset_measurement_choice.SetSelection(current_measurement_choice)
        
        self.control_panel.derived_measurement_choice.SetItems(self.derived_measurements[dataset_id][track_id].keys())
        self.control_panel.derived_measurement_choice.SetSelection(0)
        
        # When visualizing a new dataset, select all trajectories by default
        self.trajectory_selection = dict.fromkeys(self.connected_nodes[dataset_id][track_id].keys(),1)  
                
    def set_scalar_values(self, selected_dataset=None, selected_track=None):
        
        #if not self.do_plots_need_updating["filter"]:
            #self.selected_filter = None
        #else:
            #self.selected_filter = []
            #for current_filter in self.control_panel.filter_panel.filters:
                #self.selected_filter.append(" ".join((props.object_table + "." + current_filter.colChoice.GetStringSelection(), 
                                                      #current_filter.comparatorChoice.GetStringSelection(),
                                                      #current_filter.valueField.GetValue())))        
        if selected_dataset == None and selected_track == None:
            # No data sources or tracks specified: Initialize graph scalar attributes from scratch
            available_datasets = list(set(map(itemgetter(self.relationship_cols[NODE_TBL_ID].index(props.group_id)),self.relationship_data[NODE_TBL_ID])))
            available_datasets = [str(_) for _ in available_datasets]                 
            selected_dataset = available_datasets[0]
            available_tracks = self.defined_track_cols
            selected_track = ORIGINAL_TRACK
        else:
            # Data source and/or track specified: Add a new graph
            available_datasets = [selected_dataset]
            available_tracks = [selected_track]
            
        for dataset_id in available_datasets:
            column_names,trajectory_info = obtain_tracking_data(dataset_id,
                                                                self.selected_measurement if self.selected_measurement in self.dataset_measurement_choices else None, 
                                                                #self.selected_filter
                                                                )             
            for track_id in available_tracks:     
                
                selected_node_ids = self.directed_graph[dataset_id][track_id].nodes()
 
                if self.selected_measurement in self.dataset_measurement_choices:
                    key_length = len(object_key_columns())
                    indices = range(0,key_length)
                    node_ids = map(itemgetter(*indices),trajectory_info)
                    getitem = itemgetter(len(trajectory_info[0])-1) # Last value is the measurement value               
                    attr = dict(zip(node_ids,[item for item in map(getitem,trajectory_info)]))  
                    attr = {_:attr[_] for _ in selected_node_ids}
                else:
                    node_ids = sorted(self.directed_graph[dataset_id][track_id]) # Needs to be sorted, for now, due to output from derivied meas calc
                    if self.selected_metric == METRIC_NODESWITHINDIST:
                        self.derived_measurements[dataset_id][track_id][self.selected_metric] = self.calc_n_nodes_from_branchpoint(dataset_id, track_id)
                    elif self.selected_metric == METRIC_SINGLETONS:
                        self.derived_measurements[dataset_id][track_id][self.selected_metric] = self.calc_singletons(dataset_id, track_id)
                    attr = dict(zip(node_ids,self.derived_measurements[dataset_id][track_id][self.selected_metric]))
                nx.set_node_attributes(self.directed_graph[dataset_id][track_id],SCALAR_VAL,attr)
                
                ## Filter values
                #getitem = itemgetter(len(trajectory_info[0])-1)
                #attr = dict(zip(node_ids,[item for item in map(getitem,trajectory_info)])) 
                #attr = {_:attr[_] for _ in selected_node_ids}
                #nx.set_node_attributes(self.directed_graph[dataset_id][track_id],"f",attr)
            
        self.scalar_data = np.array([self.directed_graph[selected_dataset][selected_track].node[key][SCALAR_VAL] 
                                     for key in sorted(self.directed_graph[selected_dataset][selected_track])]).astype(float)

    def distance_plot(self, selected_dataset=None, selected_dataset_track=None):
        pass

    def calc_n_nodes_from_branchpoint(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
        cutoff_dist_from_branch = self.control_panel.distance_cutoff_value.GetValue()
        end_nodes_for_pruning = {_:set() for _ in connected_nodes.keys()} 
        
        for (key,subgraph) in connected_nodes.items():
            branch_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,BRANCH_NODES).items() if _[1]]
            finishing_nodes = [_[0] for _ in nx.get_node_attributes(subgraph, FINISH_NODES).items() if _[1]]
            if branch_nodes != []:
                for source_node in branch_nodes:
                    # Find out-degrees for all nodes within N nodes of branchpoint
                    out_degrees = subgraph.out_degree(nx.single_source_shortest_path_length(subgraph,
                                                                                            source_node,
                                                                                            cutoff_dist_from_branch).keys())
                    # Find all nodes for which the out-degree is 0 (i.e, all terminal nodes (leaves)) and not a terminal node (i.e, at end of movie)
                    branch_to_leaf_endpoints = [(source_node,path_node) for (path_node,degree) in out_degrees.items() if degree == 0 and path_node not in finishing_nodes]
                    if len(branch_to_leaf_endpoints) > 0:
                        for current_branch in branch_to_leaf_endpoints:
                            shortest_path = nx.shortest_path(subgraph,current_branch[0],current_branch[1]) 
                            shortest_path.remove(source_node) # Remove the intital branchpoint
                            # Skip this path if another branchpoint exists, since it will get caught later
                            if all(np.array(subgraph.out_degree(shortest_path).values()) <= 1): 
                                # Add nodes on the path from the branchpoint to the leaf
                                end_nodes_for_pruning[key].update(shortest_path)     
            
            end_nodes_for_pruning[key] = list(end_nodes_for_pruning[key])
                
            # Set identity attributes
            attr = dict.fromkeys(subgraph.nodes(),False)
            for _ in end_nodes_for_pruning[key]:
                attr[_] = True
            nx.set_node_attributes(subgraph,METRIC_NODESWITHINDIST,attr)
            attr = dict.fromkeys(subgraph.edges(),False)
            for _ in end_nodes_for_pruning[key]:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:
                    attr[e] = True
            nx.set_edge_attributes(subgraph,METRIC_NODESWITHINDIST,attr)                
            
            # Set visibility attributes
            attr = dict.fromkeys(subgraph.nodes(),True) 
            for _ in end_nodes_for_pruning[key]:
                attr[_] = False
            nx.set_node_attributes(subgraph,METRIC_NODESWITHINDIST_VISIBLE,attr)            
            attr = dict.fromkeys(subgraph.edges(),True)
            for _ in end_nodes_for_pruning[key]:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:
                    attr[e] = False
            nx.set_edge_attributes(subgraph,METRIC_NODESWITHINDIST_VISIBLE,attr)       

        sorted_nodes = sorted(directed_graph)

        temp_full_graph_dict =  dict.fromkeys(directed_graph.nodes(),0.0)
        for key, nodes in end_nodes_for_pruning.items():
            l = end_nodes_for_pruning[key]
            for ii in l:
                temp_full_graph_dict[ii] = 1.0
        
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes]).astype(float)
        
    def calc_singletons(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
        cutoff_dist = self.control_panel.singleton_length_value.GetValue()
        sorted_nodes = sorted(directed_graph)
        temp_full_graph_dict = dict.fromkeys(directed_graph.nodes(),0.0)
        
        for (key,subgraph) in connected_nodes.items():
            start_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,START_NODES).items() if _[1]]
            terminal_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,TERMINAL_NODES).items() if _[1]]
            singleton_nodes = set()
            for _ in terminal_nodes:
                dist = nx.shortest_path_length(subgraph, source=start_nodes[0], target=_)
                if dist <= cutoff_dist:
                    # If there are multiple terminal nodes, then the distance for them is the same but a different path, so add the new nodes to the list
                    singleton_nodes.union(set(nx.shortest_path(subgraph, source=start_nodes[0], target=_)))
            singleton_nodes = list(singleton_nodes)
            
            # Set identity attributes
            attr = dict.fromkeys(subgraph.nodes(), False)
            for _ in singleton_nodes:
                attr[_] = True
            nx.set_node_attributes(subgraph,METRIC_SINGLETONS,attr)  
            attr = dict.fromkeys(subgraph.edges(),False)
            for _ in singleton_nodes:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:
                    attr[e] = True
            nx.set_edge_attributes(subgraph,METRIC_SINGLETONS,attr)            

            # Set visibility attribute 
            attr = dict.fromkeys(subgraph.nodes(), True)
            for _ in singleton_nodes:
                attr[_] = False            
            nx.set_node_attributes(subgraph,METRIC_SINGLETONS_VISIBLE,attr)
            attr = dict.fromkeys(subgraph.edges(), True)
            for _ in singleton_nodes:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:
                    attr[e] = False            
            nx.set_edge_attributes(subgraph,METRIC_SINGLETONS_VISIBLE,attr)            
            
            for _ in singleton_nodes:
                temp_full_graph_dict[_] = 1.0
                
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes]).astype(float)     
                
    def bc_branch_plot(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        values = []
        ratios = []
        for key,subgraph in connected_nodes.items():
            branch_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,BRANCH_NODES).items() if _[1]]
            for bn in branch_nodes:
                bcs = [subgraph.node[_][METRIC_BC] for _ in subgraph.successors(bn)]
                values += bcs
                ratios += list(bcs/np.sum(bcs))
        
        values = np.array(values)
        ratios = np.array(ratios)
                        
        new_title = "Betweeness centrality branchpoint values"
        window = self.create_or_find_plain_figure_window(self, -1, new_title, subplots=(2,1), name=new_title)
                        
        # Plot the betweeness centrality values
        title = "Betweeness centrality branchpoint values"
        # Nice tutorial on GridSpec: http://matplotlib.org/users/gridspec.html
        gs = gridspec.GridSpec(3, 1, height_ratios=[1, 3, 3])
        axes = window.figure.add_subplot(gs[0]) 
        axes.set_axis_off()
        help_text = ("This plot shows the histogram of the betweenness centrality values for all branchpoints",
                     "in the current data source. The length of a track corresponds to the lifetime of the object.\n\n"
                     "Branches that last for one or just a few frames are likely to be false positives and are"
                     "candidates for removal.")
        help_text = " ".join(help_text)
        help_text = '\n'.join(wrap(help_text,80))
        
        axes.text(0.0,0.0,help_text)
        axes = window.figure.add_subplot(gs[1])        
        if values.shape[0] == 0:
            plot = axes.text(0.0, 1.0, "No valid values to plot.")
            axes.set_axis_off()  
        else:
            bins = np.linspace(0, np.max(values))
            n, _, _ = axes.hist(values, bins,
                          edgecolor='none',
                          alpha=0.75)
            axes.set_xlabel('Betweeness centrality values')
            axes.set_ylabel('Counts')
            
        # Plot the betweeness centrality ratios
        axes = window.figure.add_subplot(gs[2])        
        if ratios.shape[0] == 0:
            plot = axes.text(0.0, 1.0, "No valid ratios to plot.")
            axes.set_axis_off()  
        else:
            bins = np.linspace(0, 0.5)
            n, _, _ = axes.hist(ratios, bins,
                          edgecolor='none',
                          alpha=0.75)
            axes.set_xlabel('Betweeness centrality ratios')
            axes.set_ylabel('Counts')          
                        
        # Draw the figure
        window.figure.tight_layout()
        window.figure.canvas.draw()        
            
    def calc_betweenness_centrality(self, selected_dataset=None, selected_dataset_track=None):
        # Suggested by http://stackoverflow.com/questions/18381187/functions-for-pruning-a-networkx-graph/23601809?iemail=1&noredirect=1#23601809
        # nx.betweenness_centrality: http://networkx.lanl.gov/reference/generated/networkx.algorithms.centrality.betweenness_centrality.html
        # Betweenness centrality of a node v is the sum of the fraction of all-pairs shortest paths that pass through v:
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
        
        nodes_to_prune = {_:set() for _ in connected_nodes.keys()}         
        sorted_nodes = sorted(directed_graph)
        temp_full_graph_dict = dict.fromkeys(directed_graph.nodes(),0.0)
        for key,subgraph in connected_nodes.items():
            attr = dict.fromkeys(subgraph.nodes(), 0.0)
            betweenness_centrality = nx.betweenness_centrality(subgraph, normalized=True)
            for (node,value) in betweenness_centrality.items():
                temp_full_graph_dict[node] = value
                attr[node] = value
            # Set identity attributes
            nx.set_node_attributes(subgraph, METRIC_BC, attr)
            # Set visibility attribute 
            # TODO: Come up with a heuristic to determine which branch to prune based on this value 
            branch_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,BRANCH_NODES).items() if _[1]]
            for bn in branch_nodes:
                successors = subgraph.successors(bn)
                bc_vals = [betweenness_centrality[_] for _ in successors]
                cutoff = 1.0/len(bc_vals)/2.0 # Set to ????
                idx = np.argwhere(np.array(bc_vals)/sum(bc_vals) < cutoff)
                # Find all downstream nodes for branches that failed the cutoff
                for i in idx:
                    nodes = nx.single_source_shortest_path(subgraph,successors[i]).keys()
                    nodes_to_prune[key].update(nodes)
            
            attr = dict.fromkeys(subgraph.nodes(), True)
            for _ in nodes_to_prune[key]:
                attr[_] = False                        
            nx.set_node_attributes(subgraph, METRIC_BC_VISIBLE, attr)
            attr = dict.fromkeys(subgraph.edges(), True)
            for _ in nodes_to_prune[key]:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:
                    attr[e] = False 
            nx.set_edge_attributes(subgraph, METRIC_BC_VISIBLE, attr)
        
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes ]).astype(float)      
    
    def singleton_length_plot(self, selected_dataset=None, selected_dataset_track=None, length_cutoff=1):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        
        dists = []
        num_tracks = len(connected_nodes.keys())
        for key,subgraph in connected_nodes.items():
            start_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,START_NODES).items() if _[1]]
            terminal_nodes = [_[0] for _ in nx.get_node_attributes(subgraph,TERMINAL_NODES).items() if _[1]]
            # If there are multiple terminal nodes, then the distance for them is the same, but with a different path
            for _ in terminal_nodes:
                dists += [nx.shortest_path_length(subgraph, source=start_nodes[0], target=_)+1]
        dists = np.array(dists)
        num_singletons = len(np.argwhere(dists <= length_cutoff))
        
        new_title = "Track lengths"
        window = self.create_or_find_plain_figure_window(self, -1, new_title, subplots=(2,1), name=new_title)
                        
        # Plot the track lengths
        title = "Track lengths"
        gs = gridspec.GridSpec(3, 2)
        axes = window.figure.add_subplot(gs[0,:]) 
        axes.set_axis_off()
        help_text = ("This plot shows the histogram of the track lengths for all trajectories in the current",
                     "data source. The length of a track corresponds to the lifetime of the object.\n\n",
                     "Cells that last for one or just a few frames are likely to be false positives and are",
                     "candidates for removal.")
        help_text = " ".join(help_text)
        help_text = '\n'.join(wrap(help_text,80))        
        axes.text(0.0,0.0,help_text)
        
        axes = window.figure.add_subplot(gs[1:,0])        
        if dists.shape[0] == 0:
            plot = axes.text(0.0, 1.0, "No valid values to plot.")
            axes.set_axis_off()  
        else:
            bins = np.arange(1, np.max(dists)+1)
            n, _, _ = axes.hist(dists, bins,
                          edgecolor='none',
                          alpha=0.75)
            axes.set_xlabel('Track lengths (frames)')
            axes.set_ylabel('Counts')
            
        axes = window.figure.add_subplot(gs[1:,1])
        stats = np.array([["Total number of tracks","%d"%num_tracks],
                          ["Number of singletons","%d"%num_singletons],
                          ["10th percentile length","%d"%np.percentile(dists,10)],
                          ["Median length","%d"%np.percentile(dists,50)],
                          ["90th percentile length","%d"%np.percentile(dists,90)]])
        # TODO: Use cpfiure subplot_table code below (maybe)
        table = axes.table(rowLabels=None, colLabels=None, colWidths=[0.75, 0.25], cellText= stats, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.0, 2.0)
        axes.set_axis_off()        
        
        # Draw the figure
        window.figure.tight_layout()
        window.figure.canvas.draw()        
    
    def calc_crossings(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
                
        sorted_nodes = sorted(directed_graph)    
        temp_full_graph_dict = dict.fromkeys(directed_graph.nodes(),0.0)
        for key,subgraph in connected_nodes.items():
            # Just picking out the simple crossings for now
            #  1   4
            #   \ /
            #    3      
            #   / \
            #  2   5
            # TODO: Generalize for crossings of longer duration 
            out_degrees = subgraph.out_degree(subgraph.nodes())
            in_degrees = subgraph.in_degree(subgraph.nodes())
            crossings = [_ for _ in subgraph.nodes() if (out_degrees[_] > 1 & in_degrees[_] > 1) ]
            
            # Set identity attributes
            attr = dict.fromkeys(subgraph.nodes(), False)
            for _ in crossings:
                attr[_] = True
            nx.set_node_attributes(subgraph,METRIC_CROSSINGS,attr)
            attr = dict.fromkeys(subgraph.edges(), False)
            for _ in crossings:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:
                    attr[e] = True 
            nx.set_edge_attributes(subgraph,METRIC_CROSSINGS,attr)  
            
            # Set visibility attribute 
            attr = dict.fromkeys(subgraph.nodes(), True)
            for _ in crossings:
                attr[_] = False            
            nx.set_node_attributes(subgraph,METRIC_CROSSINGS_VISIBLE,attr)  
            attr = dict.fromkeys(subgraph.edges(), True)
            for _ in crossings:
                ebunch = nx.edges(subgraph,_)
                for e in ebunch:                
                    attr[e] = False            
            nx.set_edge_attributes(subgraph,METRIC_CROSSINGS_VISIBLE,attr)              
            
            for _ in crossings:
                temp_full_graph_dict[_] = 1.0            
        
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes ]).astype(float) 

    def calc_loops(self, selected_dataset=None, selected_dataset_track=None):
        connected_nodes = self.connected_nodes[selected_dataset][selected_dataset_track]
        directed_graph = self.directed_graph[selected_dataset][selected_dataset_track]
                        
        sorted_nodes = sorted(directed_graph)
        temp_full_graph_dict = dict.fromkeys(directed_graph.nodes(),0.0)
        for key,subgraph in connected_nodes.items():
            cycles = nx.cycle_basis(subgraph.to_undirected())
            # Just picking out the simple cycles for now
            #     2
            #   /   \
            #  1     4   -->   4 nodes total
            #   \  /
            #     3
            # TODO: Generalize for loops of longer duration
            cycles = [_ for _ in cycles if len(_) <= 4] 
            # Set identity attributes
            attr = dict.fromkeys(subgraph.nodes(), False)
            for _ in cycles:
                for item in _:
                    attr[item] = True
            nx.set_node_attributes(subgraph,METRIC_LOOPS,attr)  
            # Set visibility attribute 
            attr = dict.fromkeys(subgraph.nodes(), True)
            for _ in cycles:
                for item in _:
                    attr[item] = False            
            nx.set_node_attributes(subgraph,METRIC_LOOPS_VISIBLE,attr)
            attr = dict.fromkeys(subgraph.edges(), True)
            for _ in cycles:
                for item in _:
                    ebunch = nx.edges(subgraph,item)
                    for e in ebunch:
                        attr[e] = False           
            nx.set_edge_attributes(subgraph,METRIC_LOOPS_VISIBLE,attr)            
            
            for _ in cycles:
                t = [subgraph.node[item]["t"] for item in _]
                # Omit interior nodes within the cycle
                # I'm searching by time, rather than in/out-degree b/c further splits could occur within the cycle
                nodes = [item for item in _ if subgraph.node[item]["t"] not in [min(t),max(t)]]
                for item in nodes:
                    temp_full_graph_dict[item] = 1.0            
        
        return np.array([temp_full_graph_dict[node] for node in sorted_nodes ]).astype(float)  
        
    def add_derived_measurements(self, selected_dataset=None, selected_dataset_track=None):
        logging.info("Calculating derived measurements")
                    
        t1 = time.clock()   
        # TODO: Allow for user choice to add derived measurements
        # TODO: Figure out where to best store this information: as a graph attrubute, subgraph attribute, or a separate matrix
        # Create dict for QC measurements derived from graph properities
        derived_measurements = {}      
                    
        # Find branchpoints and nodes with a distance threshold from them (for later pruning if desired)
        derived_measurements[METRIC_NODESWITHINDIST] = self.calc_n_nodes_from_branchpoint(selected_dataset, selected_dataset_track)
        
        # Singletons: Subgraphs for which the start node = end node
        derived_measurements[METRIC_SINGLETONS] = self.calc_singletons(selected_dataset, selected_dataset_track)

        # Betweeness centrality: Measure of a node's centrality in a network
        derived_measurements[METRIC_BC] = self.calc_betweenness_centrality(selected_dataset, selected_dataset_track)
        
        # Loops: Transient split, followed by merge (i.e., cycles in a network)
        derived_measurements[METRIC_LOOPS] = self.calc_loops(selected_dataset, selected_dataset_track)        
        
        # Crossings: Transient merges, followed by split
        derived_measurements[METRIC_CROSSINGS] = self.calc_crossings(selected_dataset, selected_dataset_track)          

        t2 = time.clock()
        logging.info("Computed derived measurements (%.2f sec)"%(t2-t1))    
        
        return derived_measurements
        
    def find_fig(self, parent=None, title="", name=wx.FrameNameStr, subplots=None):
        """Find a figure frame window. Returns the window or None"""
        if parent:
            window = parent.FindWindowByName(name)
            if window:
                if len(title) and title != window.Title:
                    window.Title = title
                window.figure.clf()
            return window    

    def create_or_find_plain_figure_window(self, parent=None, id=-1, title="", 
                                            pos=wx.DefaultPosition, size=wx.DefaultSize,
                                            style=wx.DEFAULT_FRAME_STYLE, name=wx.FrameNameStr,
                                            subplots=None,
                                            on_close=None):
        """Create or find a figure frame window"""
        win = self.find_fig(parent, title, name, subplots)
        return win or FigureFrame(parent, id, title, pos, size, style, name, 
                                    subplots, on_close)    
    
    def subplot_table(self, x, y, statistics, 
                          col_labels=None, 
                          row_labels = None, 
                          n_cols = 1,
                          n_rows = 1):
            """Put a table into a subplot
            
            x,y - subplot's column and row
            statistics - a sequence of sequences that form the values to
                         go into the table
            col_labels - labels for the column header
            
            row_labels - labels for the row header
            
            **kwargs - for backwards compatibility, old argument values
            """
            
            nx, ny = self.subplots.shape
            xstart = float(x) / float(nx)
            ystart = float(y) / float(ny)
            width = float(n_cols) / float(nx)
            height = float(n_rows) / float(ny)
            cw, ch = self.figure.canvas.GetSizeTuple()
            ctrl = wx.grid.Grid(self.figure.canvas)
            self.widgets.append(
                (xstart, ystart, width, height, 
                 wx.ALIGN_CENTER, wx.ALIGN_CENTER, ctrl))
            nrows = len(statistics)
            ncols = 0 if nrows == 0 else len(statistics[0])
            ctrl.CreateGrid(nrows, ncols)
            if col_labels is not None:
                for i, value in enumerate(col_labels):
                    ctrl.SetColLabelValue(i, unicode(value))
            else:
                ctrl.SetColLabelSize(0)
            if row_labels is not None:
                ctrl.GridRowLabelWindow.Font = ctrl.GetLabelFont()
                ctrl.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTER)
                max_width = 0
                for i, value in enumerate(row_labels):
                    value = unicode(value)
                    ctrl.SetRowLabelValue(i, value)
                    max_width = max(
                        max_width, 
                        ctrl.GridRowLabelWindow.GetTextExtent(value+"M")[0])
                ctrl.SetRowLabelSize(max_width)
            else:
                ctrl.SetRowLabelSize(0)
                
            for i, row in enumerate(statistics):
                for j, value in enumerate(row):
                    ctrl.SetCellValue(i, j, unicode(value))
                    ctrl.SetReadOnly(i, j, True)
            ctrl.AutoSize()
            ctrl.Show()
            self.align_widget(ctrl, xstart, ystart, width, height,
                              wx.ALIGN_CENTER, wx.ALIGN_CENTER, cw, ch)
            self.table = []
            if col_labels is not None:
                if row_labels is not None:
                    # Need a blank corner header if both col and row labels
                    col_labels = [""] + list(col_labels)
                self.table.append(col_labels)
            if row_labels is not None:
                self.table += [[a] + list(b) for a, b in zip(row_labels, statistics)]
            else:
                self.table += statistics    
    
    def calculate_and_display_lap_stats(self):
        # See http://cshprotocols.cshlp.org/content/2009/12/pdb.top65.full, esp. Figure 5
        # Create new figure
        new_title = "LAP diagnostic metrics"
        window = self.create_or_find_plain_figure_window(self, -1, new_title, subplots=(2,1), name=new_title)
        
        # Plot the frame-to-frame linking distances
        dists = self.calculate_frame_to_frame_linking_distances() 
        title = "Frame-to-frame linking distances"       
        axes = window.figure.add_subplot(2,2,1) 
        axes.set_axis_off()
        help_text = ("Frame-to-frame linking distances",
                     "are the distances between the",
                     "predicted position of an object",
                     "and the observed position. This",
                     "data is displayed as a histogram",
                     "and should decay to zero.\n\n",
                     "The arrow indicates the pixel",
                     "distance at which 95%% of all",
                     "links were made. You should",
                     "confirm that this value is less",
                     "than the maximum search radius",
                     "in the %s module."%TRACKING_MODULE_NAME)
        help_text = " ".join(help_text)
        help_text = '\n'.join(wrap(help_text,30))    
        axes.text(0.0,0.0,help_text)
        axes = window.figure.add_subplot(2,2,2)        
        if dists.shape[0] == 0:
            plot = axes.text(0.0, 1.0, "No valid values to plot.")
            axes.set_axis_off()  
        else:
            bins = np.arange(0, int(0.95*np.max(dists)))
            if len(bins) > 0:
                n, _, _ = axes.hist(dists, bins,
                              edgecolor='none',
                              alpha=0.75)
                max_search_radius = bins[np.cumsum(n) < 0.95*np.max(np.cumsum(n))][-1]
                axes.annotate('95% of all links: %d pixels'%(max_search_radius),
                              xy=(max_search_radius,n[n < 0.05*np.max(n)][0]), 
                              xytext=(max_search_radius,axes.get_ylim()[1]/2), 
                              arrowprops=dict(facecolor='red', shrink=0.05))
            else:
                n, _, _ = axes.hist(dists, np.array([0,1]),
                                edgecolor='none',
                                alpha=0.75)   
            axes.set_xlabel('Frame-to-frame linking distances (pixels)')
            #axes.set_xlim((0,np.mean(dists) + 2*np.std(dists)))
            axes.set_ylabel('Counts')                    
        
        # Plot the gap lengths
        axes = window.figure.add_subplot(2,2,3) 
        axes.set_axis_off()
        help_text = ("Gap lengths are displayed as",
                     "a histogram. A plateau in the",
                     "tail of the histogram",
                     "indicates that the time window",
                     "used for gap closing is too",
                     "large, resulting in falsely",
                     "closed gaps.\n\n",
                     "If all the gap lengths are 1,",
                     "no data is shown since gap",
                     "closing was not necessary.")
        help_text = " ".join(help_text)
        help_text = '\n'.join(wrap(help_text,30))    
        axes.text(0.0,0.0,help_text)        
        values = np.array(self.calculate_gap_lengths()).flatten()
        values = values[np.isfinite(values)] # Just in case
        title = "Gap lengths"
        axes = window.figure.add_subplot(2,2,4)        
        if values.shape[0] == 0:
            plot = axes.text(0.1, 0.5, "No valid values to plot.")
            axes.set_axis_off()  
        elif np.max(values) == 1:
            plot = axes.text(0.1, 0.5, "No gap lengths > 1")
            axes.set_axis_off()              
        else:
            bins = np.arange(0, np.max(values))
            axes.hist(values, bins,
                      facecolor=(0.0, 0.62, 1.0),
                      edgecolor='none',
                      alpha=0.75)
            axes.set_xlabel('Gap length (frames)')
            axes.set_ylabel('Counts')
        
        # Draw the figure
        #window.figure.tight_layout()
        window.figure.canvas.draw()
    
    def calculate_gap_lengths(self):
        obj = get_object_name()
        
        query = ("SELECT",
                 "ABS(i2.%s - i1.%s)"%(props.timepoint_id, props.timepoint_id),
                 "FROM %s r"%(props.relationships_view),  
                 "JOIN %s i1"%(props.image_table),
                 "ON r.image_number1 = i1.%s"%(props.image_id),
                 "JOIN %s i2"%(props.image_table),
                 "ON r.image_number2 = i2.%s"%(props.image_id),
                 "WHERE") + \
                 where_stmt_for_tracked_objects(obj,props.group_id,int(self.selected_dataset)) 
        query = " ".join(query)
        return(np.array([_ for _ in db.execute(query)]))
    
    def calculate_frame_to_frame_linking_distances(self):
        #What's recorded in the database for each object are the values necessary to predict the 
        # location of the object in the next frame. There are two models applicable in TrackObjects: Random (NoVel) and Velocity (Vel)
        # For the Velocity model, you have to add Kalman_State_Vel_X and Kalman_State_Vel_VX and similarly for Y to get the 
        # predicted (X,Y) position. 
        # For NoVel, it's Kalman_State_NoVel_X and Kalman_State_NoVel_Y that gives the predicted (X,Y) position.
        # The error in distance between the observed location and the predicted location is calculated depending on which 
        # the user picked in TrackObjects (usually both) and the appropriate model is picked on a per-object basis as the
        # minimum of the two.
        obj = get_object_name()
        prefix = "_".join((obj,TRACKING_MODULE_NAME))
        if props.db_type == 'sqlite':
            query = "PRAGMA table_info(%s)"%(props.object_table)
            used_velocity_model = len([item[1] for item in db.execute(query) if item[1].find('_Kalman_Vel_') > 0]) > 0    
            used_novelocity_model = len([item[1] for item in db.execute(query) if item[1].find('_Kalman_NoVel_') > 0]) > 0  
        else:
            query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP '_Kalman_Vel_'"%(props.db_name, props.object_table)
            used_velocity_model = db.execute(query)[0][0] > 0
            query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s' AND COLUMN_NAME REGEXP '_Kalman_NoVel_'"%(props.db_name, props.object_table)
            used_novelocity_model = db.execute(query)[0][0] > 0
        # SQL courtesy of Lee. 
        query = ("SELECT",
                 "pred.pred_vel_x, pred.pred_vel_y, pred.pred_novel_x, pred.pred_novel_y, obs.%s_Location_Center_X, obs.%s_Location_Center_Y"%(obj,obj),
                 "FROM %s r"%(props.relationships_view),
                 "JOIN",
                 "(SELECT %s AS ImageNumber, %s AS ObjectNumber,"%(props.image_id, props.object_id),
                 "(%s_Kalman_Vel_State_X + %s_Kalman_Vel_State_VX)"%(prefix,prefix) if used_velocity_model else "NULL","AS pred_vel_x,",
                 "(%s_Kalman_Vel_State_Y + %s_Kalman_Vel_State_VY)"%(prefix,prefix) if used_velocity_model else "NULL","AS pred_vel_y,",
                 "%s_Kalman_NoVel_State_X AS pred_novel_x, %s_Kalman_NoVel_State_Y"%(prefix,prefix) if used_novelocity_model else "NULL","AS pred_novel_y",
                 "FROM %s) AS pred ON r.image_number1 = pred.ImageNumber AND r.object_number1 = pred.ObjectNumber"%(props.object_table),
                 "JOIN %s AS obs ON r.image_number2 = obs.%s AND r.object_number2 = obs.%s"%(props.object_table, props.image_id, props.object_id),
                 "JOIN %s AS i1 ON r.image_number1 = i1.%s"%(props.image_table, props.image_id),
                 "JOIN %s AS i2 ON r.image_number2 = i2.%s"%(props.image_table, props.image_id),
                 "WHERE i1.%s + 1 = i2.%s"%(props.timepoint_id,props.timepoint_id),
                 "AND i1.%s = i2.%s"%(props.group_id,props.group_id),
                 "AND") + \
            where_stmt_for_tracked_objects(obj,props.group_id,int(self.selected_dataset)) 
        query = " ".join(query)
        values = np.array(db.execute(query))
        # I would love to do this arithmetic in the query, but SQLite doesn't handle SQRT or POW
        dist_error_novel = np.sqrt((values[:,2]-values[:,4])**2 + (values[:,3]-values[:,5])**2)
        dist_error_vel = np.sqrt((values[:,0]-values[:,4])**2 + (values[:,1]-values[:,5])**2)
        # Return the minimum of the two models for each object/timepoint
        return(np.min(np.vstack((dist_error_novel,dist_error_vel)),axis=0))
        
    
################################################################################
if __name__ == "__main__":
        
    import sys
    app = wx.PySimpleApp()
    logging.basicConfig(level=logging.DEBUG,)
    
    props = Properties.getInstance()

    # Load a properties file if passed in args
    if len(sys.argv) > 1:
        propsFile = sys.argv[1]
        props.LoadFile(propsFile)
        props, success = add_props_field(props)
    else:
        if not props.show_load_dialog():
            print 'Time Visualizer requires a properties file.  Exiting.'
            # Necessary in case other modal dialogs are up
            wx.GetApp().Exit()
            sys.exit()
        else:
            props, success = add_props_field(props)
            
    tracer = Tracer(None)
    tracer.Show()

    app.MainLoop()
    
    #
    # Kill the Java VM
    #
    try:
        import javabridge
        javabridge.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
