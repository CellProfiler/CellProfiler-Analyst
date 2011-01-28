import os
import math
import xml.etree.cElementTree as ET
import sqlite3

__all__ = ['parse_incell']

well_field_to_imagenumber = {}

def get_object_data(values):
    names = []
    vals = []
    for measure in values.findall('Measure'):
        try:
            colname = rewrite_feature_name(measure)
            val = float(measure.get('value'))
            names.append(colname)
            if 'cgY' in names:
                val = -val
            vals.append(val)
                
        except Exception, e:
            pass
    return names, vals

def parse_incell(filename, properties=None):
    well_field_to_imagenumber.clear()

    sqlite_out = filename + '.sqlite3'
    assert not os.path.exists(sqlite_out)
    dbconn = sqlite3.connect(sqlite_out)

    context = ET.iterparse(open(filename))

    # create the object table
    cursor = dbconn.cursor()
    cursor.execute('CREATE TABLE Objects '
                   '(ImageNumber INTEGER,'
                   'ObjectNumber INTEGER,'
                   'PRIMARY KEY (ImageNumber, ObjectNumber))')

    object_data_columns = set()

    for action, element in context:
        if element.tag in ['WellData']:
            try:
                row = int(element.get('row'))
                col = int(element.get('col'))
                field = int(element.get('field')) # WTF, incell.  (see below)
                well = '%s%02d'%(chr(ord('A') + row - 1), col)
                imagenumber = well_field_to_imagenumber.setdefault((well, field), len(well_field_to_imagenumber) + 1)
                
                if element.get('cell') == 'Summary':
                    print well, field
                else:
                    # extract features and values
                    objectnumber = int(element.get('cell'))
                    colnames, values = get_object_data(element.find('Values'))
                    missing_features = set(colnames) - object_data_columns
                    for m in missing_features:
                        cursor.execute('ALTER TABLE Objects ADD COLUMN %s REAL'%(m))
                    object_data_columns.update(set(colnames))
                    cursor.execute('INSERT INTO Objects (ImageNumber, ObjectNumber, %s) VALUES (%s)'%(
                            ','.join(colnames), ','.join('?'*(len(colnames) + 2))),
                                   [imagenumber, objectnumber] + list(values))
            except Exception, e:
                print "Failed to load well object data", element, element.attrib, e
                print colnames, values
                pass

            element.clear()
        elif element.tag not in ['Measure', 'Values']:
            print element

    dbconn.commit()
    print "done"

    tree = context.root
    ET.ElementTree(tree).write('lastparsed.xml')

    # create required property elements
    if not properties:
        return

    # image tile size - default 50, otherwise twice nuclear diameter
    try:
        calibration = tree.find('.//ObjectiveCalibration')
        segmentation = tree.find('.//Segmentation/NTHSegmentation')
        diameter = 2 * math.sqrt(float(segmentation.get('size')) / math.pi)
        properties.image_tile_size = 2 * diameter / float(calibration.get('pixel_height'))
    except:
        print "unable to find nucleus size in pixels"
        properties.image_tile_size = 50


    # cell location
    image_height = int(tree.find('.//Camera/Size').get('height'))
    try:
        properties.cell_x_loc = [col for col in object_data_columns if 'cgX' in col][0]
        properties.cell_y_loc = [col for col in object_data_columns if 'cgY' in col][0]
        cursor.execute('UPDATE Objects SET %s = %d - %s'%(properties.cell_y_loc, image_height, properties.cell_y_loc))
        dbconn.commit()
    except:
        print "No location information found"
        pass

    # db_type
    properties.db_type = 'sqlite'
    properties.db_sqlite_file = sqlite_out 

    # plates, images, objects
    properties.plate_id = 'PlateName'
    properties.well_id = 'Well'
    properties.well_format = 'A01'
    properties.image_table = 'Images'
    properties.object_table = 'Objects'
    properties.image_id = 'ImageNumber'
    properties.object_id = 'ObjectNumber'
    
    try:
        plate_info = tree.find('.//AutoLeadAcquisitionProtocol/Plate')
        properties.plate_type = '%d'%(int(plate_info.get('rows')) * int(plate_info.get('columns')))
    except:
        print "unable to find plate type"


    # Create image table
    export_image_table(dbconn, tree, properties)

    return tree

def export_image_table(dbconn, tree, properties):
    # Find the list of images
    def channel_colname_name(im):
        channel_idx = int(im.find('Identifier').get('wave_index')) + 1
        excitation = im.find('ExcitationFilter').get('name') 
        emission = im.find('EmissionFilter').get('name') 
        if excitation != emission:
            return 'Channel%d'%(channel_idx), '%s_%s'%(excitation, emission)
        return 'Chan%d'%(channel_idx), excitation

    # extract channel names
    imagestack = tree.find('ImageStack/Images')
    channels_info = set([channel_colname_name(im) for im in imagestack.findall('Image')])
    channel_colnames = [s[0] for s in channels_info]
    channel_realnames = [s[1] for s in channels_info]
    num_wavelengths = len(channels_info)
                         
    # image paths and filenames
    properties.image_path_cols = ['%s_Path'%(s) for s in channel_colnames]
    properties.image_file_cols = ['%s_Filename'%(s) for s in channel_colnames]
    properties.image_names = [s for s in channel_realnames]

    # create image table
    im_paths_create = ",".join(['%s_Path TEXT'%(s) for s in channel_colnames])
    im_filenames_create = ",".join(['%s_Filename TEXT'%(s) for s in channel_colnames])
    cursor = dbconn.cursor()
    cursor.execute('CREATE TABLE Images '
                   '(ImageNumber INTEGER PRIMARY KEY,'
                   + im_paths_create + ',' + im_filenames_create + ',' +
                   ' PlateName TEXT,'
                   ' Well TEXT,'
                   ' Field INTEGER)')

    #
    path = imagestack.get('path')
    path = os.path.normpath(path.replace('\\', os.sep))
    path = path.replace('//Gemini/', '/Volumes/') # Curie specific
    platename = os.path.split(path)[1]

    # Fill the image table.  Separate wavelengths at the same location
    # are separate images within the imagestack, so we have to be
    # careful not to add a row twice
    images_inserted = {}
    for image in imagestack.findall('Image'):
        row = int(image.find('Well/Row').get('number'))
        col = int(image.find('Well/Column').get('number'))
        well = '%s%02d'%(chr(ord('A') + row - 1), col)
        field = int(image.find('Identifier').get('field_index')) + 1 # WTF, Incell.
        assert field > 0

        if (well, field) not in images_inserted:
            imagenumber = well_field_to_imagenumber.setdefault((well, field), len(well_field_to_imagenumber) + 1)
            data = [imagenumber] + ([path] * num_wavelengths) + ([''] * num_wavelengths) + [platename, well, field]
            cursor.execute('INSERT INTO Images VALUES (%s)'%(','.join('?'*(4 + 2 * num_wavelengths))), data)
            images_inserted[well, field] = imagenumber
            imagenumber += 1

        chan = channel_colname_name(image)[0]
        cursor.execute('UPDATE Images SET %s_Filename=? WHERE well=? and field=?'%(chan), (image.get('filename'), well, field))

    dbconn.commit()

    imported_features = set()
    # Insert summary data into image table
    for welldata in tree.findall('Wells/WellData'):
        for val in welldata:
            row = int(welldata.get('row'))
            col = int(welldata.get('col'))
            well = '%s%02d'%(chr(ord('A') + row - 1), col)
            field = int(welldata.get('field'))
            assert field > 0
            names, values = zip(*sorted([(rewrite_feature_name(measure), float(measure.get('value'))) for measure in val.findall('Measure')]))
            print names
            missing_features = set(names) - imported_features
            for mf in missing_features:
                cursor.execute('ALTER TABLE Images ADD COLUMN %s REAL'%(mf))
            imported_features.update(set(names))
            for name, val in zip(names, values):
                cursor.execute('UPDATE Images SET %s=? WHERE well=? AND field=?'%(name), (val, well, field))
    dbconn.commit()
               

def rewrite_feature_name(measure):
    name = '%s_%s_%s'%(measure.get('name'), measure.get('key'), measure.get('source'))
    name = name.replace('/', 'div')
    name = name.replace('%', 'pcnt')
    name = name.replace(' ', '')
    name = name.replace('(', '')
    name = name.replace(')', '')
    name = name.replace(':', '')
    name = name.replace('-', '_')
    name = name.replace('+', '_')
    if name[0] in '0123456789':
        name = 'x' + name
    return name

if __name__ == '__main__':
    import sys
    tree = parse_incell(sys.argv[1])
