from singleton import Singleton

class ExperimentSettings(Singleton):
    def __init__(self):
        self.global_settings = {}
        self.timeline = None
        self.subscribers = {}

    def set_field(self, tag, value):
        self.global_settings[tag] = value
        if self.subscribers.get(tag, None) is not None:
            self.subscribers[tag]()

    def get_field(self, tag, default=None):
        return self.global_settings.get(tag, default)

    def remove_field(self, tag):
        if self.get_field(tag) is not None:
            self.global_settings.pop(tag)

    def get_field_instances(self, tag_prefix):
        '''returns a list of unique instance ids for each tag beginning with 
        tag_prefix'''
        ids = set([tag.rsplit('|', 1)[-1] for tag in self.global_settings
                   if tag.startswith(tag_prefix)])
        return list(ids)

    def get_field_tags(self, tag_prefix, instance=''):
        '''returns a list of all tags beginning with tag_prefix. If instance
        is passed in, only tags of the given instance will be returned'''
        return [tag for tag in self.global_settings 
                if tag.startswith(tag_prefix) and tag.endswith(instance)]

    def clear(self):
        self.global_settings = {}
        self.timeline = None        

    def save_to_file(self, file):
        f = open(file, 'w')
        for field, value in self.global_settings.items():
            f.write('%s = %s\n'%(field, repr(value)))
        f.close()

    def load_from_file(self, file):
        self.clear()
        f = open(file, 'r')
        for line in f:
            field, value = line.split('=')
            field = field.strip()
            self.set_field(field, eval(value))
        f.close()
        
    def add_subscriber(self, func, tag_list):
        '''
        '''
        for tag_prefix in tag_list:
            for tag in self.get_field_tags(tag_prefix):
                self.subscribers[tag] = func

        
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
# Plate formats
P6    = (2, 3)
P24   = (4, 6)
P96   = (8, 12)
P384  = (16, 24)
P1536 = (32, 48)
P5600 = (40, 140)

NO_EVENT = 'no event'  # Deprecated


class PlateDesign:
    '''Maps plate_ids to plate formats'''
    plates = {}
    @classmethod
    def add_plate(self, plate_id, plate_format):
        '''Add a new plate with the specified format
        '''
        self.plates[plate_id] = plate_format

    @classmethod
    def get_plate_format(self, plate_id):
        '''returns the plate_format for a given plate_id
        '''
        return self.plates[plate_id]

    @classmethod
    def get_well_ids(self, plate_format):
        '''plate_format - a valid plate format. eg: P96 or (8,12)
        '''
        return ['%s%02d'%(ch, num) 
                for ch in ALPHABET[:plate_format[0]] 
                for num in range(1,plate_format[1]+1)]

    @classmethod
    def get_well_id_from_row_col(self, plate_format, (row, col)):
        '''returns a well_id given a plate format and (x,y) (0-indexed) position 
        on a plate
        '''
        import numpy as np
        assert 0 <= row < plate_format[0], 'invalid row %s'%(row)
        assert 0 <= col < plate_format[1], 'invalid col %s'%(col)
        plate = np.array(self.get_well_ids(plate_format)).reshape(plate_format)
        return plate[row,col]

        