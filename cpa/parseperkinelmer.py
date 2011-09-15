import xml.dom.minidom as dom
import os
import numpy as np
from properties import Properties
import dbconnect
import wx

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


#
# REQUIRED
#
results_dir = '/Users/afraser/Desktop/PKI Example Data/Columbus/P010-R ETAR[56]_SinglePlaneTIF'
measurements_index = 'MeasurementIndex.ColumbusIDX.xml'

URL_COLUMN_PREFIX = 'Image_URL_'
PATH_COLUMN_PREFIX = 'Image_Path_'
FILE_COLUMN_PREFIX = 'Image_File_'

DEFAULT_DB_NAME = 'cpa.db'
DEFAULT_PROPERTIES_FILENAME = 'cpa.properties'

p = Properties.getInstance()
db = dbconnect.DBConnect.getInstance()

def load_columbus(filepath):
    '''
    Loads a Columbus dataset by either importing the data into a CPA database 
    and properties file or by loading a pre-existing CPA database.
    
    filepath -- path to the MeasurementIndex.ColumbusIDX.xml file output by Columbus
    '''
##    progress_dlg = wx.ProgressDialog('Creating CPA database.', '0% Complete', 100, None, 
##                            wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
##    def update(frac):
##        cont, skip = progress_dlg.Update(int(frac * 100.), '%d%% Complete'%(frac * 100.))
##        if not cont: # cancel was pressed
##            progress_dlg.Destroy()
##            raise StopCalculating()
    
    global measurements_index
    global results_dir
    measurements_index = filepath
    results_dir = os.path.dirname(filepath)
    # relative image paths are loaded from cwd
    os.chdir(results_dir)
    
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
            return
        else:
            # delete then re-import
            os.remove(os.path.join(results_dir, DEFAULT_DB_NAME))
            os.remove(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))
            
    doc = dom.parse(os.path.join(results_dir, measurements_index))
    image_index = get_image_index_file(doc)
    image_dir = os.path.dirname(image_index)
    
    plates, wells, images = get_plates_wells_and_images(image_index)
    channels = get_channel_names(plates, wells, images)

    print 'Creating properties file at: %s'%(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))
    create_properties_file(image_index, channels)
    db.connect(empty_sqlite_db = True)
    p.load_file(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))

    print 'Creating SQLite database at: %s'%(os.path.join(results_dir, DEFAULT_DB_NAME))
    print 'Creating per_image table...'
    imagenumber_dict = create_per_image_table(image_dir, plates, wells, images, channels)
    print '...done'
    
    print 'Creating per_object table...'
    from time import time
    t = time()
    create_per_object_table(doc, imagenumber_dict)
    print '...done in %.2f seconds'%(time() - t)
    
##    progress_dlg.Destroy()


def create_properties_file(image_index, channels):
    '''
    returns (image_column_names, image_table
    '''
    assert channels != []
    
    plate_shape = get_plate_shape(image_index)
##    dlg = wx.TextEntryDialog(None, 'Enter cell window size',
##                             'What is the approximate maximum diameter of your '
##                             'cells in microns? CPA will use this value to crop '
##                             'cell tiles for Classifier.',
##                             '50', style=wx.CENTER|wx.OK)
##    dlg.ShowModal()
##    cell_diameter = float(dlg.GetValue())
##    image_tile_size = str(int(get_cell_pixel_size(image_index, cell_diameter)))
##    dlg.Destroy()
    
    p.db_type             = 'sqlite'
    p.db_sqlite_file      = os.path.join(results_dir, DEFAULT_DB_NAME)
    p.image_table         = 'per_image'
    p.object_table        = 'per_object'
    p.image_id            = 'ImageNumber'
    p.object_id           = 'ObjectNumber'
    p.plate_id            = 'Plate'
    p.well_id             = 'Well'
    p.cell_x_loc          = 'X'
    p.cell_y_loc          = 'Y'
    p.image_path_cols     = [PATH_COLUMN_PREFIX + c for c in channels]
    p.image_file_cols     = [FILE_COLUMN_PREFIX + c for c in channels]
    p.image_channel_names = channels
    p.plate_type          = convert_plate_dims_to_platetype(*plate_shape)
    p.image_tile_size     = 100 #image_tile_size
    p._filters = {}
    p._groups = {}
    p._textfile = ''
    
    p.save_file(os.path.join(results_dir, DEFAULT_PROPERTIES_FILENAME))


def create_per_object_table(doc, imagenumber_dict):
    '''doc -- measurements_index DOM document object
    imagenumber_dict -- a dict mapping (well, fieldID, planeID, timepointID) to 
        an ImageNumber value. This is generated by create_per_image_table
    '''
    def get_column_names(well_res_file):
        '''parses reported column names out of the given well_results_file'''
        ob_col_dict = {}
        doc = dom.parse(os.path.join(results_dir, well_res_file))
        for ref in doc.getElementsByTagName('ParameterAnnotations'):
            for param in ref.getElementsByTagName('Parameter'):
                ob_col_dict[param.getAttribute('id')] = dict(param.attributes.items())
                
        params_node = doc.getElementsByTagName('ResultTable')[0].getElementsByTagName('Parameters')[0]
        measurement_ids = [p.getAttribute('parID') 
                           for p in params_node.getElementsByTagName('Parameter')]
        
        return [ob_col_dict[id]['name'] for id in measurement_ids]

    
    well_result_files = get_well_results_files(doc)
    
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
    object_number = 1
    for well_res_file in well_result_files:
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
            image_number = imagenumber_dict[platename, wellname, fid, pid, tid]
            row = [image_number, 
                   object_number, 
                   wellname, 
                   float(tr.getAttribute('x')), 
                   float(tr.getAttribute('y'))]
            row += [float(col.firstChild.data) 
                    for col in tr.childNodes]
            rows += [row]
            object_number += 1
        
        # Insert rows from this well result file
        db.insert_rows_into_table('per_object', colnames, coltypes, rows)
            
    db.Commit()


def create_per_image_table(image_dir, plates, wells, images, channels):
    '''
    Creates the per_image table 
    '''
    default_colnames = ['ImageNumber', 'Plate', 'Well']
    plate_colnames = [col for col in plates.values()[0].__dict__.keys() if col not in ['PlateID', 'well_ids'] ]
    
    image_loc_colnames = [FILE_COLUMN_PREFIX + cname for cname in channels]
    image_loc_colnames += [PATH_COLUMN_PREFIX + cname for cname in channels]
        
    colnames = default_colnames + plate_colnames + image_loc_colnames
    
    coltypes = ['INTEGER', 'TEXT', 'VARCHAR(3)']
    coltypes += ['TEXT'] * len(plate_colnames)
    coltypes += ['TEXT'] * len(image_loc_colnames)
    
    table = []
    imagenumber = 1
    imagenumber_dict = {}
    for pid, pinfo in plates.items():
        for wid in pinfo.well_ids:
            winfo = wells[wid]
            wellname = convert_rowcol_to_wellid(winfo.Row, winfo.Col)
            # merge channels into single rows (ie: imagesets)
            imagesets = {}
            for iid in winfo.image_ids:
                im = images[iid]
                imagesets[(im.FieldID, im.PlaneID, im.TimepointID)] = imagesets.get((im.FieldID, im.PlaneID, im.TimepointID), []) + [im]
            for (fid, pid, tid), imageset in imagesets.items():
                imagenumber_dict[pinfo.PlateID, wellname, fid, pid, tid] = imagenumber
                row = [
                    imagenumber,
                    pinfo.PlateID,
                    wellname
                ]
                row += [pinfo.__dict__[c] for c in plate_colnames]
                row += [None] * len(image_loc_colnames)
                for iinfo in imageset:
                    row[colnames.index(FILE_COLUMN_PREFIX + iinfo.ChannelName)] = iinfo.URL
                    row[colnames.index(PATH_COLUMN_PREFIX + iinfo.ChannelName)] = image_dir
                
                imagenumber += 1
                table += [row]

    db.CreateTableFromData(table, colnames, 'per_image')
                
    return imagenumber_dict


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
            if ch.firstChild is None:
                self.__dict__[ch.localName] = None
            else:
                self.__dict__[ch.localName] = ch.firstChild.data
            for att_name, att_val in dict(ch.attributes).items():
                self.__dict__[ch.localName + '_' + att_name] = att_val.firstChild.data


##########################################################################
##
##  Helper Functions
##
##########################################################################

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
                     for im_id in wells[plates.values()[0].well_ids[0]].image_ids]))


def get_image_index_file(doc):
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

def get_well_results_files(doc):
    well_result_files = []
    for ref in doc.getElementsByTagName('Reference'):
        if ref.getAttribute('Class') == 'WELLRESULT':
            assert ref.firstChild.nodeType == ref.TEXT_NODE
            well_result_files += [ref.firstChild.data]
    return well_result_files

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

    
#
# try it out
#

if __name__ == "__main__":
    app = wx.PySimpleApp()
    load_columbus(results_dir+'/'+measurements_index)
    app.MainLoop()
    import cpa
    cpa.CPAnalyst
