from singleton import Singleton
import re
from timeline import Timeline
#
# TODO: Updating PlateDesign could be done entirely within 
#       set_field and remove_field.
#

def get_matchstring_for_subtag(pos, subtag):
    '''matches a subtag at a specific position.
    '''
    return '([^\|]+\|){%s}%s.*'%(pos, subtag)

def get_tag_stump(tag):
    return '|'.join(tag.split('|')[:3])

def get_tag_instance(tag):
    return tag.split('|')[3]

def get_tag_timepoint(tag):
    return int(tag.split('|')[4])

class ExperimentSettings(Singleton):
    
    global_settings = {}
    timeline        = Timeline('TEST_STOCK')
    subscribers     = {}
    
    def __init__(self):
        pass
    
    def set_field(self, tag, value):
        self.global_settings[tag] = value
        if re.match(get_matchstring_for_subtag(2, 'Well'), tag):
            self.update_timeline(tag)
        self.notify_subscribers(tag)
        
    def get_field(self, tag, default=None):
        return self.global_settings.get(tag, default)

    def remove_field(self, tag):
        if self.get_field(tag) is not None:
            self.global_settings.pop(tag)
            if re.match(get_matchstring_for_subtag(2, 'Well'), tag):
                self.update_timeline(tag)
            self.notify_subscribers(tag)

    def get_field_instances(self, tag_prefix):
        '''returns a list of unique instance ids for each tag beginning with 
        tag_prefix'''
        ids = set([tag.split('|')[3] for tag in self.global_settings
                   if tag.startswith(tag_prefix)])
        return list(ids)

    def get_field_tags(self, tag_prefix, instance=''):
        '''returns a list of all tags beginning with tag_prefix. If instance
        is passed in, only tags of the given instance will be returned'''
        return [tag for tag in self.global_settings 
                if tag.startswith(tag_prefix) and get_tag_instance(tag) == instance]
    
    def clear(self):
        self.global_settings = {}
        #
        # TODO:
        #
        self.timeline = Timeline('TEST_STOCK')

        
    def get_timeline(self):
        return self.timeline

    def update_timeline(self, welltag):
        '''Updates the experiment metadata timeline event associated with the
        action and wells in welltag (eg: 'ExpNum|AddProcess|Spin|Wells|1|1')
        '''
        action = (get_tag_stump(welltag), get_tag_instance(welltag))
        timepoint = get_tag_timepoint(welltag)
        platewell_ids = self.get_field(welltag, [])
        if platewell_ids == []:
            self.timeline.delete_event(timepoint, action)
        else:
            event = self.timeline.get_event(action, timepoint)
            if event is not None:
                event.set_well_ids(platewell_ids)
            else:
                self.timeline.add_event(timepoint, action, platewell_ids)

    def save_to_file(self, file):
        f = open(file, 'w')
        for field, value in self.global_settings.items():
            f.write('%s = %s\n'%(field, repr(value)))
        f.close()

    def load_from_file(self, file):
        self.clear()
        PlateDesign.clear()
        f = open(file, 'r')
        for line in f:
            tag, value = line.split('=')
            tag = tag.strip()
            if tag.startswith('ExptVessel|Plate|Design'):
                plate_id = 'plate%s'%(get_tag_instance(tag))
                PlateDesign.add_plate(plate_id, WELL_NAMES[eval(value)])
            elif tag.startswith('ExptVessel|Flask|Size'):
                # add 1x1 plate for each flask instance
                plate_id = 'flask%s'%(get_tag_instance(tag))
                PlateDesign.add_plate(plate_id, FLASK)
            self.set_field(tag, eval(value))
        f.close()
        
    def add_subscriber(self, callback, match_string):
        '''callback -- the function to be called
        match_string -- a regular expression string matching the tags you want 
                        to be notified of changes to
        '''
        self.subscribers[match_string] = self.subscribers.get(match_string, []) + [callback]
            
    def notify_subscribers(self, tag):
        for matchstring, callbacks in self.subscribers.items():
            if re.match(matchstring, tag):
                for callback in callbacks:
                    callback(tag)


ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# Plate formats
FLASK = (1, 1)
P6    = (2, 3)
P24   = (4, 6)
P96   = (8, 12)
P384  = (16, 24)
P1536 = (32, 48)
P5600 = (40, 140)

WELL_NAMES = {'6-Well-(2x3)'       : P6, 
              '24-Well-(4x6)'      : P24, 
              '96-Well-(8x12)'     : P96, 
              '384-Well-(16x24)'   : P384, 
              '1536-Well-(32x48)'  : P1536, 
              '5600-Well-(40x140)' : P5600,
              }

WELL_NAMES_ORDERED = ['6-Well-(2x3)',
                      '24-Well-(4x6)',
                      '96-Well-(8x12)',
                      '384-Well-(16x24)',
                      '1536-Well-(32x48)',
                      '5600-Well-(40x140)']

NO_EVENT = 'no event'  # Deprecated


class PlateDesign:
    '''Maps plate_ids to plate formats.
    Provides methods for getting well information for different plate formats.
    '''
    plates = {}
    @classmethod
    def clear(self):
        self.plates = {}
        
    @classmethod
    def add_plate(self, plate_id, plate_format):
        '''Add a new plate with the specified format
        '''
        self.plates[plate_id] = plate_format
        
    @classmethod
    def set_plate_format(self, plate_id, plate_format):
        self.plates[plate_id] = plate_format        
        
    @classmethod
    def get_plate_ids(self):
        return self.plates.keys()

    @classmethod
    def get_plate_format(self, plate_id):
        '''returns the plate_format for a given plate_id
        '''
        return self.plates[plate_id]
    
    @classmethod
    def get_all_platewell_ids(self):
        '''returns a list of every platewell_id across all plates
        '''
        return [(plate_id, well_id) 
                for plate_id in self.plates 
                for well_id in self.get_well_ids(self.get_plate_format(plate_id))
                ]

    @classmethod
    def get_well_ids(self, plate_format):
        '''plate_format - a valid plate format. eg: P96 or (8,12)
        '''
        return ['%s%02d'%(ch, num) 
                for ch in ALPHABET[:plate_format[0]] 
                for num in range(1,plate_format[1]+1)]
    
    @classmethod
    def get_col_labels(self, plate_format):
        return ['%02d'%(num) for num in range(1,plate_format[1]+1)]

    @classmethod
    def get_row_labels(self, plate_format):
        return list(ALPHABET[:plate_format[0]])
    
    @classmethod
    def get_well_id_at_pos(self, plate_format, (row, col)):
        assert 0 <= row < plate_format[0], 'invalid row %s'%(row)
        assert 0 <= col < plate_format[1], 'invalid col %s'%(col)
        cols = plate_format[1]
        return PlateDesign.get_well_ids(plate_format)[cols*row + col]

    @classmethod
    def get_pos_for_wellid(self, plate_format, wellid):
        '''returns the x,y position of the given well
        eg: get_pos_for_wellid(P96, 'A02') --> (0,1)
        '''
        if type(wellid) is tuple:
            wellid = wellid[-1]
        row = ALPHABET.index(wellid[0])
        col = int(wellid[1:]) - 1
        assert row < plate_format[0] and col < plate_format[1], 'Invalid wellid (%s) for plate format (%s)'%(wellid, plate_format)
        return (row, col)