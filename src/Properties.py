#!/usr/bin/env python

from Singleton import *

string_vars = ['db_type', 'db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',
                'image_table', 'object_table',
                'image_csv_file', 'object_csv_file',
                'table_id', 'image_id', 'object_id', 'plate_id', 'well_id',
                'cell_x_loc', 'cell_y_loc',
                'image_url_prepend',
                'image_tile_size', 'image_buffer_size',
                'tile_buffer_size',
                'area_scoring_column',
                'training_set',
                'plate_type']

list_vars = ['image_channel_paths', 'image_channel_files', 'image_channel_names', 'image_channel_colors',
            'object_name',
            'classifier_ignore_substrings']


class Properties(Singleton):
    '''
    Loads and stores properties files.
    '''
    def __init__(self):
        super(Properties, self).__init__()        
    
    def __str__(self):
        s=''
        for k, v in self.__dict__.items():
            s += k+" = "+str(v)+"\n"
        return s
        
    
    def __getattr__(self, id):
        # The name may not be loaded for optional fields.
        if( not self.__dict__.has_key(id) ):
            return None
        else:
            return self.__dict__[id]
    
    
    def LoadFile(self, filename):
        ''' Loads variables in from a properties file. '''
        self.Clear()
        self.filename = filename
        f = open(filename, 'r')
        
        lines = f.read()
        lines = lines.replace('\r', '\n')                        # replace CRs with LFs
        lines = lines.split('\n')

        self.groups = {}
        self.groups_ordered = []
        self.filters = {}
        self.filters_ordered = []

        for line in lines:
            if not line.strip().startswith('#') and line.strip()!='':          # skip commented and empty lines
                (name, val) = line.split('=', 1)                               # split each side of the first eq sign
                name = name.strip()
                val = val.strip()
                                
                if name in string_vars:
                    self.__dict__[name] = val
                
                elif name in list_vars:
                    self.__dict__[name] = [v.strip() for v in val.split(',') if v.strip() is not '']
                    
                elif name.startswith('group_SQL_'):
                    group_name = name[10:]
                    if group_name == '':
                        raise Exception, 'PROPERTIES ERROR (%s): "group_SQL_" should be followed by a group name.\nExample: "group_SQL_MyGroup = <QUERY>" would define a group named "MyGroup" defined by\na MySQL query "<QUERY>". See the README.'%(name)
                    if group_name in self.groups.keys():
                        raise Exception, 'Group "%s" is defined twice in properties file.'%(group_name)
                    if group_name in self.filters.keys():
                        raise Exception, 'Name "%s" is already taken for a filter.'%(group_name)
                    if not val:
                        print 'PROPERTIES WARNING (%s): Undefined group'%(name)
                        continue
                    # TODO: test query
                    self.groups[group_name] = val
                    self.groups_ordered += [group_name]
                    
                elif name.startswith('filter_SQL_'):
                    filter_name = name[11:]
                    if filter_name == '':
                        raise Exception, 'PROPERTIES ERROR (%s): "filter_SQL_" should be followed by a filter name.\nExample: "filter_SQL_MyFilter = <QUERY>" would define a filter named "MyFilter" defined by\na MySQL query "<QUERY>". See the README.'%(name)
                    if filter_name in self.filters.keys():
                        raise Exception, 'Filter "%s" is defined twice in properties file.'%(filter_name)
                    if filter_name in self.groups.keys():
                        raise Exception, 'Name "%s" is already taken for a group.'%(filter_name)
                    if not val:
                        print 'PROPERTIES WARNING (%s): Undefined filter'%(name)
                        continue
                    # TODO: test query
                    self.filters[filter_name] = val
                    self.filters_ordered += [filter_name]
                
                elif name in ['groups', 'filters']:
                    print 'PROPERTIES WARNING (%s): This field is no longer necessary in the properties file.\nOnly the group_SQL_XXX and filter_SQL_XXX fields are needed when defining groups and filters.'%(name)
                    
                else:
                    print 'PROPERTIES WARNING: Unrecognized field "%s" in properties file'%(name)
                
        f.close()
        self.Validate()
        
    
    def SaveFile(self, filename):
        # TODO: Save files WITH previous comments and whitespace.
        f = open(filename, 'w')
        self.filename = filename
        for var, val in self.__dict__.items():
            if type(val)==list:
                f.write(var+' = '+str(val)[1:-1]+'\n')
            else:
                f.write(var+' = '+val+'\n')
        f.close()
        
    
    def Clear(self):
        self.__dict__ = {}
        
        
    def IsEmpty(self):
        return self.__dict__ == {}


    def Validate(self):
        
        def field_defined(name):
            # field name exists and has a non-empty value.
            return name in self.__dict__.keys() and self.__dict__[name]!=''

        # Check that all required variables were loaded
        optional_vars = ['db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',
                         'table_id', 'image_url_prepend', 'image_csv_file',
                         'image_channel_names', 'image_channel_colors',
                         'object_csv_file', 'area_scoring_column', 'training_set',
                         'image_buffer_size', 'tile_buffer_size',
                         'plate_id', 'well_id', 'plate_type']
        
        # check that all required fields are defined
        for name in string_vars + list_vars:
            if name not in optional_vars:
                assert field_defined(name), 'PROPERTIES ERROR (%s): Field is missing or empty.'%(name)        
        
        assert self.db_type.lower() in ['mysql', 'sqlite'], 'PROPERTIES ERROR (db_type): Value must be either "mysql" or "sqlite".'
        
        # BELOW: Check sometimes-optional fields, and print warnings etc
        if self.db_type.lower()=='sqlite':
            for field in ['db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',]:
                if field_defined(field):
                    print 'PROPERTIES WARNING (%s): Field not required with db_type=sqlite.'%(field)
            for field in ['image_csv_file','object_csv_file']:
                assert field_defined(field), 'PROPERTIES ERROR (%s): Field is required with db_type=sqlite.'%(field)            

        if self.db_type.lower()=='mysql':
            for field in ['db_port', 'db_host', 'db_name', 'db_user',]:
                assert field_defined(field), 'PROPERTIES ERROR (%s): Field is required with db_type=mysql.'%(field)
            for field in ['image_csv_file','object_csv_file']:
                if field_defined(field):
                    print 'PROPERTIES WARNING (%s): Field not required with db_type=mysql.'%(field)
        
        if field_defined('area_scoring_column'):
            print 'PROPERTIES: Area scoring will be used.'
        
        if not field_defined('image_channel_names'):
            print 'PROPERTIES WARNING (image_channel_names): No value(s) specified. Classifier will use generic channel names.'
            self.image_channel_names = ['channel-%d'%(i) for i in range(103)] [:len(self.image_channel_files)]

        if not field_defined('image_channel_colors'):
            print 'PROPERTIES WARNING (image_channel_colors): No value(s) specified. Classifier will use a generic channel-color mapping.'
            self.image_channel_colors = ['red', 'green', 'blue']+['none' for x in range(100)] [:len(self.image_channel_files)]

        if not field_defined('classifier_ignore_substrings'):
            print 'PROPERTIES WARNING (classifier_ignore_substrings): No value(s) specified. Classifier will use ALL NUMERIC per_object columns when training.'

        if field_defined('training_set'):
            try:
                f = open(self.training_set)
                f.close()
            except:
                print 'PROPERTIES WARNING (training_set): Training set at "%s" could not be found.'%(self.training_set)                        
            print 'PROPERTIES: Training set found at "%s"'%(self.training_set)
            

        
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        filename = "../Properties/nirht_test.properties"
    
    p = Properties.getInstance()
    p.LoadFile(filename)
#    print p

