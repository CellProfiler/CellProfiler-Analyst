
import xml.dom.minidom as dom
import os
import re
import numpy as np
from .properties import Properties
from . import dbconnect
import wx
import logging
logging.basicConfig(level=logging.DEBUG)
# PER-IMAGE DATA

# output/<image dir>/ImageIndex.ColumbusIDX.xml
# -- referenced from output/MeasurementIndex.ColumbusIDX.xml
# -- measurement names in: AnalysisResults > ParameterAnnotations > Parameter
# -- measurement values in: AnalysisResults > Results > ResultTable > table

# PER-OBJECT DATA

# output/MeasurementIndex.ColumbusIDX.xml
# -- List of references to well results xml files which contain per-object measurements

# output/2009-02-12T171135Z[57]RMS Receptor Internalization AAS[414].result.E3[354].xml
# -- Example of an Individual results file
# -- measurement names are under AnalysisResults > ParameterAnnotations > Parameter
# -- measurement data are under AnalysisResults > ResultTable > table


results_dir = ''

URL_COLUMN_PREFIX = 'Image_URL_'
PATH_COLUMN_PREFIX = 'Image_Path_'
FILE_COLUMN_PREFIX = 'Image_File_'

DEFAULT_DB_NAME = 'cpa.db'
DEFAULT_PROPERTIES_FILENAME = 'cpa.properties'

p = Properties()
db = dbconnect.DBConnect()


def load_harmony(plate_results):
    '''
    Loads a Harmony dataset by either importing the data into a CPA database 
    and properties file or by loading a pre-existing CPA database.
    
    results_path -- full path to the harmony output directory 
    '''
    global results_dir
    results_dir = os.path.dirname(plate_results)
    
    os.chdir(results_dir) # relative image paths are loaded from cwd
    
    if check_already_imported(results_dir):
        return
    
    eval_dirs = [os.path.abspath(fd) for fd in os.listdir(results_dir) if fd.startswith('Evaluation')]
    image_dir = os.path.join(results_dir, '../Images')
    image_index = os.path.join(image_dir, 'Index.idx.xml')
    
    plates, wells, images = get_plates_wells_and_images(image_index)
    channels = get_channel_names(plates, wells, images)
    object_results_files = get_object_results_files_harmony(results_dir)
    
    print(('Creating properties file at: %s'%(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))))
    create_properties_file(image_index, channels, len(object_results_files)>0)
    db.connect(empty_sqlite_db = True)
    p.load_file(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))
    
    print(('Creating SQLite database at: %s'%(os.path.join(results_dir, DEFAULT_DB_NAME))))
    print('Creating per_image table...')
    imagesets = create_image_set_dict(plates, wells, images)
    create_per_image_table(plates, channels, imagesets, image_dir)
    print('...done')
    
    print('Creating per_well table...')
    create_harmony_per_well_table(plate_results)
    print('...done')
    
    if object_results_files:
        print('Creating per_object table...')
        create_per_object_table(object_results_files)
        print('...done')
    
    

def load_columbus(measurements_index):
    '''
    Loads a Columbus dataset by either importing the data into a CPA database 
    and properties file or by loading a pre-existing CPA database.
    
    measurements_index -- path to the MeasurementIndex.ColumbusIDX.xml file output by Columbus
    '''
    global results_dir
    results_dir = os.path.dirname(measurements_index)
    os.chdir(results_dir) # relative image paths are loaded from cwd
    
    if check_already_imported(results_dir):
        return
            
    doc = dom.parse(measurements_index)
    image_index = get_columbus_image_index_file(doc)
    image_dir = os.path.dirname(image_index)
    
    plates, wells, images = get_plates_wells_and_images(image_index)
    channels = get_channel_names(plates, wells, images)

    print(('Creating properties file at: %s'%(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))))
    create_properties_file(image_index, channels)
    db.connect(empty_sqlite_db = True)
    p.load_file(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))

    print(('Creating SQLite database at: %s'%(os.path.join(results_dir, DEFAULT_DB_NAME))))
    print('Creating per_image table...')
    imagesets = create_image_set_dict(plates, wells, images)
    create_per_image_table(plates, channels, imagesets, image_dir)
    print('...done')
    
    print('Creating per_object table...')
    from time import time
    t = time()
    object_results_files = get_object_results_files_columbus(doc)
    create_per_object_table(object_results_files)
    print(('...done in %.2f seconds'%(time() - t)))
    

def create_properties_file(image_index, channels, has_per_object=True):
    '''
    returns (image_column_names, image_table
    '''
    assert channels != []
    
    plate_shape           = get_plate_shape(image_index)
    is_http               = get_url_protocol(image_index) == 'http'
    p.db_type             = 'sqlite'
    p.db_sqlite_file      = os.path.join(results_dir, DEFAULT_DB_NAME)
    p.image_table         = 'per_image'
    p.image_id            = 'ImageNumber'
    p.plate_id            = 'Plate'
    p.well_id             = 'Well'
    p.image_path_cols     = [PATH_COLUMN_PREFIX + c for c in channels]
    p.image_file_cols     = [FILE_COLUMN_PREFIX + c for c in channels]
    p.image_names         = channels
    p.plate_shape         = [int(d) for d in plate_shape]
    p.classifier_ignore_columns = ['ImageNumber']
    p._filters = {}
    p._groups = {'plate': 'SELECT ImageNumber, Plate FROM per_image', 
                 'well': 'SELECT ImageNumber, Plate, Well FROM per_image'}
    p.group_SQL_plate = 'SELECT ImageNumber, Plate FROM per_image'
    p.group_SQL_well = 'SELECT ImageNumber, Plate, Well FROM per_image'
    p._textfile = ''
    
    if has_per_object:
        p.object_table        = 'per_object'
        p.object_id           = 'ObjectNumber'
        p.cell_x_loc          = 'X'
        p.cell_y_loc          = 'Y'
        p.image_tile_size     = 100 #image_tile_size
        p.classifier_ignore_columns = ['ImageNumber', 'ObjectNumber', 'X', 'Y']

    p.save_file(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))


def create_per_object_table(well_result_files):
    '''doc -- measurements_index DOM document object
    '''
    def get_column_names(well_res_file):
        '''parses reported column names out of the given well_results_file'''
        ob_col_dict = {}
        doc = dom.parse(os.path.join(results_dir, well_res_file))
        for ref in doc.getElementsByTagName('ParameterAnnotations'):
            for param in ref.getElementsByTagName('Parameter'):
                ob_col_dict[param.getAttribute('id')] = dict(list(param.attributes.items()))
                
        params_node = doc.getElementsByTagName('ResultTable')[0].getElementsByTagName('Parameters')[0]
        measurement_ids = [p.getAttribute('parID') 
                           for p in params_node.getElementsByTagName('Parameter')]
        
        return [ob_col_dict[id]['name'] for id in measurement_ids]
    
    # Get per-object column names
    default_columns = ['ImageNumber', 'ObjectNumber', 'Well', 'X', 'Y']
    param_columns = get_column_names(well_result_files[0])
    colnames = default_columns + param_columns
    
    coltypes = ['INTEGER', 'INTEGER', 'VARCHAR(3)', 'REAL', 'REAL']
    coltypes += ['REAL'] * len(param_columns)
    
    colnames = dbconnect.clean_up_colnames(colnames)
    db.create_empty_table('per_object', colnames, coltypes)
    db.create_default_indexes_on_table('per_object')

    # create object measurement matrix
    for well_res_file in well_result_files:
        #
        # TODO: Object number should change for every image, not every well
        #
        object_number = 1
        doc = dom.parse(os.path.join(results_dir, well_res_file))
        platename = doc.getElementsByTagName('PlateName')[0].firstChild.data
        r = doc.getElementsByTagName('ResultTable')[0].getAttribute('Row')
        c = doc.getElementsByTagName('ResultTable')[0].getAttribute('Col')
        pid = doc.getElementsByTagName('ResultTable')[0].getAttribute('PlaneID')
        tid = doc.getElementsByTagName('ResultTable')[0].getAttribute('TimepointID')
        wellname = convert_rowcol_to_wellid(r, c)
        rows = []
        for tr in doc.getElementsByTagName('ResultTable')[0].getElementsByTagName('tr'):
            fid = tr.getAttribute('FieldID')
            query = 'SELECT ImageNumber FROM per_image WHERE Plate="%s" AND ' \
                    'Well="%s" AND FieldID="%s" AND PlaneID="%s" AND ' \
                    'TimepointID="%s"'%(platename, wellname, fid, pid, tid)
            image_number = db.execute(query)[0][0]
            row = [image_number, 
                   object_number, 
                   wellname, 
                   float(tr.getAttribute('x')), 
                   float(tr.getAttribute('y'))]
            row += [float(col.firstChild.data) 
                    for col in tr.childNodes if col.firstChild]
            rows += [row]
            object_number += 1
        
        # Insert rows from this well result file
        db.insert_rows_into_table('per_object', colnames, coltypes, rows)
            
    db.Commit()
    
    
def create_image_set_dict(plates, wells, images):
    '''
    returns a dict d[plateid, well, fieldid, planeid, timepointid] = [ImageInfo, ...]
    '''
    imagesets = {}
    for pid, pinfo in list(plates.items()):
        for wid in pinfo.well_ids:
            winfo = wells[wid]
            well = convert_rowcol_to_wellid(winfo.Row, winfo.Col)
            # merge channels into single rows (ie: imagesets)
            for iid in winfo.image_ids:
                im = images[iid]
                plate = pinfo.PlateID
                fid = im.FieldID
                pid = im.PlaneID
                tid = im.TimepointID
                imagesets[plate, well, fid, pid, tid] = imagesets.get((plate, well, fid, pid, tid), []) + [im]
    return imagesets    

def create_per_image_table(plates, channels, imagesets, image_dir):
    # Default columns assumed to be in ImageIndex and MeasurementIndex
    col_defs = [('ImageNumber', 'INTEGER'),
                ('Plate', 'TEXT'),
                ('Well', 'VARCHAR(3)'),
                ('FieldID', 'INTEGER'),
                ('PlaneID', 'INTEGER'),
                ('TimepointID', 'INTEGER'),
                ]
    # Metadata columns stored in the Plate tags of the ImageIndex
    col_defs += [(col, 'TEXT')
                 for col in list(list(plates.values())[0].__dict__.keys()) 
                 if col not in ['PlateID', 'well_ids'] ]
    # Image file and path columns from the Image tags
    col_defs += [(FILE_COLUMN_PREFIX + cname, 'TEXT')
                 for cname in channels]
    col_defs += [(PATH_COLUMN_PREFIX + cname, 'TEXT')
                  for cname in channels]

    # Create the table definition
    db.execute('CREATE TABLE per_image (%s)'
               %(', '.join(col+' '+typ for col, typ in col_defs)))

    # Populate the table
    imagenumber = 1
    colnames = [col for col, typ in col_defs]
    for (plate, well, fid, pid, tid), imageset in list(imagesets.items()):
        row = [ imagenumber, plate, well, fid, pid, tid ]
        row += [v for col, v in list(plates[plate].__dict__.items()) 
                if col not in ['PlateID', 'well_ids']]
        row += [None] * (len(colnames) - len(row))
        for iinfo in imageset:
            row[colnames.index(FILE_COLUMN_PREFIX + iinfo.ChannelName)] = iinfo.URL
            row[colnames.index(PATH_COLUMN_PREFIX + iinfo.ChannelName)] = image_dir

        db.execute('INSERT INTO per_image VALUES (%s)'%(','.join('"%s"'%r for r in row)))
            
        imagenumber += 1
        
    db.Commit()

def create_harmony_per_well_table(plate_results_file):    
    # First parse parameter information from the PlateResults
    col_dict = get_param_map_from_plate_results(plate_results_file)
    par_ids = get_resultgroup_param_ids_from_plate_results(plate_results_file)
    plate_res_param_names = [col_dict[p]['name'] for p in par_ids]

    # Default columns assumed to be in ImageIndex and MeasurementIndex
    col_defs = [('Plate', 'TEXT'),
                ('Well', 'VARCHAR(3)'),
                ]
    # Parameters from the PlateResults
    col_defs += [(param, 'FLOAT') for param in plate_res_param_names]
    
    # Convert to db-friendly column names
    col_defs = [(convert_to_friendly_column_name(col), typ) for col, typ in col_defs]

    # Create the table definition
    db.execute('CREATE TABLE per_well (%s)'
               %(', '.join('%s %s'%(col, typ) for col, typ in col_defs)))
    
    # Populate the table
    colnames = [col for col, typ in col_defs]

    par_id_set = set(par_ids) # for fast inclusion testing
    doc = dom.parse(plate_results_file)
    
    platename = doc.getElementsByTagName('PlateName')[0].firstChild.data
    
    for ref in doc.getElementsByTagName('Results'):
        if not ref.attributes: continue
        results = {}
        wellname = convert_rowcol_to_wellid(ref.attributes.get('Row').value, ref.attributes.get('Col').value)
        for res in ref.childNodes:
            if not res.childNodes or res.tagName != 'Result':
                continue
            for val in res.getElementsByTagName('value'):
                for att, attval in list(val.attributes.items()):
                    if att == 'parID' and attval in par_id_set:
                        results[attval] = val.firstChild.data
                        
        set_clause = '"%s", "%s", '%(platename, wellname)
        set_clause += ', '.join(['"%s"'%(results[par_id]) for par_id  in par_ids])
        db.execute('INSERT INTO per_well VALUES (%s)'%(set_clause))
    db.Commit()
    
    db.do_link_tables('per_well', 'per_image', ('Plate', 'Well'), ('Plate', 'Well'))

        
##########################################################################
##
##  Helper Classes
##
##########################################################################

class PlateInfo:
    def __init__(self, plate_node):
        '''plate_node -- Plate DOM node from the ImageIndex file.
        
        Parses and stores child entries of a Plate node.
        '''
        self.PlateID              = plate_node.getElementsByTagName('PlateID')[0].firstChild.data
        self.MeasurementID        = plate_node.getElementsByTagName('MeasurementID')[0].firstChild.data
        self.MeasurementStartTime = plate_node.getElementsByTagName('MeasurementStartTime')[0].firstChild.data
        self.Name                 = plate_node.getElementsByTagName('Name')[0].firstChild.data
        self.PlateTypeName        = plate_node.getElementsByTagName('PlateTypeName')[0].firstChild.data
        self.PlateRows            = plate_node.getElementsByTagName('PlateRows')[0].firstChild.data
        self.PlateColumns         = plate_node.getElementsByTagName('PlateColumns')[0].firstChild.data
        
        self.well_ids = [well_node.getAttribute('id') 
                         for well_node in plate_node.getElementsByTagName('Well')]
        
class WellInfo:
    def __init__(self, well_node):
        '''well_node -- Well DOM node from the ImageIndex file.

        Parses and stores id, Row, Col, and all ImageID entries of a Well node.
        '''
        self.id  = well_node.getElementsByTagName('id')[0].firstChild.data
        self.Row = well_node.getElementsByTagName('Row')[0].firstChild.data
        self.Col = well_node.getElementsByTagName('Col')[0].firstChild.data
        
        self.image_ids = [im_node.getAttribute('id') 
                          for im_node in well_node.getElementsByTagName('Image')]
        
class ImageInfo:
    def __init__(self, image_node):
        '''image_node -- Image DOM node from the ImageIndex file.
        
        Parses all Image child-node values and attributes out into object fields
        eg: <URL BufferNo="0">005003-1-001001001.tif</URL>
            ...is parsed into...
            self.URL          = "005003-1-001001001.tif"
            self.URL_BufferNo = "0"
        '''
        for ch in image_node.childNodes:
            if ch.localName is None:
                continue
            if ch.firstChild is None:
                self.__dict__[ch.localName] = None
            else:
                self.__dict__[ch.localName] = ch.firstChild.data
            for att_name, att_val in list(dict(ch.attributes).items()):
                self.__dict__[ch.localName + '_' + att_name] = att_val.firstChild.data


##########################################################################
##
##  Helper Functions
##
##########################################################################

def check_already_imported(results_dir):
    '''Checks whether the data is already imported into a db and props file
    '''
    if (os.path.exists(os.path.join(results_dir, DEFAULT_DB_NAME)) and
        os.path.exists(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))):
        res = wx.MessageDialog(None, 
            'A CPA database and properties already exists for these results. '
            'Do you wish to delete them and reimport?\n\nTo avoid seeing this '
            'message, load "%s" instead of your MeasurementIndex file.'
            %(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME)), 
            'Re-import results?', style=wx.YES_NO|wx.ICON_EXCLAMATION
            ).ShowModal()
        if res == wx.ID_NO:
            # load from existing properties
            p.load_file(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))
            return True
        else:
            # delete then re-import
            os.remove(os.path.join(results_dir, DEFAULT_DB_NAME))
            os.remove(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))
    return False

def get_plates_wells_and_images(image_index):
    '''returns plates, wells and images dictionaries mapping their respective 
    object ids to helper classes with the stored node info.
    '''
    doc = dom.parse(os.path.join(results_dir, image_index))
    
    plates = {}
    for node in doc.getElementsByTagName('Plates')[0].getElementsByTagName('Plate'):
        pi = PlateInfo(node)
        plates[pi.PlateID] = pi
    
    wells = {}
    for node in doc.getElementsByTagName('Wells')[0].getElementsByTagName('Well'):
        wi = WellInfo(node)
        wells[wi.id] = wi

    images = {}
    for node in doc.getElementsByTagName('Images')[0].getElementsByTagName('Image'):
        ii = ImageInfo(node)
        images[ii.id] = ii
        
    return plates, wells, images

def get_channel_names(plates, wells, images):
    '''
    Returns the ChannelName entries from the first plate well since all image 
    sets in the experiment are assumed to have the same channels.
    '''
    return list(set([images[im_id].ChannelName 
                     for im_id in wells[list(plates.values())[0].well_ids[0]].image_ids]))

def get_columbus_image_index_file(doc):
    '''
    Parse the ImageIndex filename from measurement index doc:
    doc -- xml.dom.minidom.Document instance
    eg: <Reference ItemID="" Class="IMAGEINDEX" Format="Native XML">2009-02-12T171135Z[57]/ImageIndex.ColumbusIDX.xml</Reference>
     '''
    for ref in doc.getElementsByTagName('Reference'):
        if (ref.getAttribute('Class') == 'IMAGEINDEX' and 
            ref.getAttribute('Format') == 'Native XML'):
            assert ref.firstChild.nodeType == ref.TEXT_NODE
            return ref.firstChild.data

def get_object_results_files_columbus(doc):
    '''doc -- MeasurementIndex xml object'''
    well_result_files = []
    for ref in doc.getElementsByTagName('Reference'):
        if ref.getAttribute('Class') == 'WELLRESULT':
            assert ref.firstChild.nodeType == ref.TEXT_NODE
            well_result_files += [ref.firstChild.data]
    return well_result_files

def get_object_results_files_harmony(results_dir):
    return [f for f in os.listdir(results_dir) if f.startswith('ObjectList')]

def convert_rowcol_to_wellid(row, col):
    ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return '%s%02d'%(ALPHABET[int(row)-1], int(col))

def convert_plate_dims_to_platetype(rows, cols):
    return int(rows) * int(cols)
    
def get_plate_shape(image_index):
    doc = dom.parse(os.path.join(results_dir, image_index))
    plate_node = doc.getElementsByTagName('Plates')[0].getElementsByTagName('Plate')[0]
    rows = plate_node.getElementsByTagName('PlateRows')[0].firstChild.data
    cols = plate_node.getElementsByTagName('PlateColumns')[0].firstChild.data
    return (rows, cols)

def get_url_protocol(image_index):
    doc = dom.parse(os.path.join(results_dir, image_index))
    images_node = doc.getElementsByTagName('Images')[0]
    image_node = images_node.getElementsByTagName('Image')[0]
    url = image_node.getElementsByTagName('URL')[0].firstChild.data
    assert type(url) == str
    if url.lower().startswith('http://'):
        return 'http'
    else:
        return 'local'
        
def get_cell_pixel_size(image_index, size_in_microns):
    '''
    Returns cell pixel size computed from the image resolution and it's diameter
    in microns.
    '''
    doc = dom.parse(os.path.join(results_dir, image_index))
    image_node = doc.getElementsByTagName('Images')[0].getElementsByTagName('Image')[0]
    xres = float(image_node.getElementsByTagName('ImageResolutionX')[0].firstChild.data)
    yres = float(image_node.getElementsByTagName('ImageResolutionY')[0].firstChild.data)
    # resolution currently assumed to be in meters (per-pixel)
    xunits = image_node.getElementsByTagName('ImageResolutionY')[0].getAttribute('Unit')
    yunits = image_node.getElementsByTagName('ImageResolutionY')[0].getAttribute('Unit')
    assert xunits == yunits == 'm', 'CPA expects image resolution to be in meters per-pixel.'
    # convert res to microns per-pixel
    xres *= 1000000
    yres *= 1000000
    return size_in_microns / min(xres, yres)

def get_param_map_from_plate_results(plate_results_file):
    '''Parses the ParameterAnnotations tag in the PlateResults file.
    returns a dict mapping parameter ids to dictionaries of items.
    eg: {"par0" : {"id"          : "par0",
                   "name"        : "Total Number of Cells", 
                   "description" : "Number of Objects, population All Nuclei", 
                   "population"  : "All Nuclei",
                   "kind"        : "count"},
         "par1" : ...
        }
    '''
    col_dict = {}
    doc = dom.parse(plate_results_file)
    for ref in doc.getElementsByTagName('ParameterAnnotations'):
        for param in ref.getElementsByTagName('Parameter'):
            col_dict[param.getAttribute('id')] = dict(list(param.attributes.items()))
    return col_dict

def convert_to_friendly_column_name(param_name):
    '''mangles param name into something database friendly'''
    #TODO: avoid name collisions (unlikely)
    #TODO: shorten long names
    return re.sub("[^0-9a-zA-Z_$]", "_", param_name) 

def get_resultgroup_param_ids_from_plate_results(plate_results_file):
    '''returns the reported parameter ids from of the ResultGroup tag of the
    PlateResults file'''
    doc = dom.parse(plate_results_file)
    params_node = doc.getElementsByTagName('ResultGroup')[0].getElementsByTagName('Parameters')[0]
    measurement_ids = [p.getAttribute('parID') for p in params_node.getElementsByTagName('Parameter')]
    return measurement_ids

#
# try it out
#

if __name__ == "__main__":
    app = wx.App()
##    load_columbus('/Users/afraser/Desktop/PKI Example Data/Columbus/P010-R ETAR[56]_SinglePlaneTIF/MeasurementIndex.ColumbusIDX.xml')
##    load_harmony('/Users/afraser/Desktop/PKI Example Data/Harmony/P010-R ETAR__2009-02-12T17_11_35-Measurement1/Evaluation1/PlateResults.xml')
    load_harmony('/Users/afraser/Desktop/PKI Example Data/Harmony/P018-Colony Formation__2010-09-17T11_57_24-Measurement1/Evaluation1/PlateResults.xml')
    app.MainLoop()
    app.ExitMainLoop()
    
    import cpa
    cpaapp = cpa.CPAnalyst(redirect=False)
    cpaapp.MainLoop()

    #
    # Kill the Java VM
    #
    try:
        import javabridge
        javabridge.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print("Caught exception while killing VM")
