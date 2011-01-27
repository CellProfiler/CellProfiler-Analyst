import os
import math
import xml.etree.cElementTree as ET
import sqlite3

__all__ = ['parse_incell']

def parse_incell(filename, properties=None):

    sqlite_out = filename + '.sqlite3'
    assert not os.path.exists(sqlite_out)
    dbconn = sqlite3.connect(sqlite_out)

    context = ET.iterparse(open(filename))

    for action, element in context:
        if element.tag in ['WellData']:
            # we should emit something here
            try:
                if element.items()[0][1] == 'Summary':
                    print element.items()
                else:
                    element.clear()
            except:
                pass
        elif element.tag not in ['Measure', 'Values']:
            print element

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
    
    # image paths and files
    properties.image_path_cols = ['DAPI_Path']
    properties.image_file_cols = ['DAPI_Filename']


    try:
        plate_info = tree.find('.//AutoLeadAcquisitionProtocol/Plate')
        properties.plate_type = '%d'%(int(plate_info.get('rows')) * int(plate_info.get('columns')))
    except:
        print "unable to find plate type"


    # Create image table
    export_image_table(dbconn, tree)

    return tree


def export_image_table(dbconn, tree):
    cursor = dbconn.cursor()
    # create image table
    cursor.execute('CREATE TABLE Images '
                   '(ImageNumber INTEGER PRIMARY KEY,'
                   ' DAPI_Path TEXT,'
                   ' DAPI_Filename TEXT,'
                   ' PlateName TEXT,'
                   ' Well TEXT,'
                   ' Field INTEGER)')

    #
    imagestack = tree.find('ImageStack/Images')
    path = imagestack.get('path')
    path = os.path.normpath(path.replace('\\', os.sep))
    platename = os.path.split(path)[1]

    # Create image table
    imagenumber = 1
    for image in imagestack.findall('Image'):
        if image.find('ExcitationFilter').get('name') != 'D360_40x':
            continue
        row = int(image.find('Well/Row').get('number'))
        col = int(image.find('Well/Column').get('number'))
        well = '%s%02d'%(chr(ord('A') + row - 1), col)
        field = int(image.find('Identifier').get('field_index')) + 1 # WTF, Incell.
        assert field > 0
        cursor.execute('INSERT INTO Images VALUES (?, ?, ?, ?, ?, ?)',
                       (imagenumber,
                        path,
                        image.get('filename'),
                        platename,
                        well,
                        field))
        imagenumber += 1
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
