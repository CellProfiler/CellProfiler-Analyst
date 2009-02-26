#!/usr/bin/env python

from Singleton import *

string_vars = ['db_type', 'db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',
                'image_table', 'object_table',
                'image_csv_file', 'object_csv_file',
                'table_id', 'image_id', 'object_id',
                'cell_x_loc', 'cell_y_loc',
                'image_url_prepend',
                'image_tile_size', 'image_buffer_size',
                'tile_buffer_size',
                'area_scoring_column',
                'training_set']

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
                    self.groups[group_name] = val
                    self.groups_ordered += [group_name]
                    
                elif name.startswith('filter_SQL_'):
                    filter_name = name[11:]
                    if filter_name == '':
                        raise Exception, 'PROPERTIES ERROR (%s): "filter_SQL_" should be followed by a filter name.\nExample: "filter_SQL_MyFilter = <QUERY>" would define a filter named "MyFilter" defined by\na MySQL query "<QUERY>". See the README.'%(name)
                    if filter_name in self.filters.keys():
                        raise Exception, 'Filter "%s" is defined twice in properties file.'%(filter_name)
                    self.filters[filter_name] = val
                    self.filters_ordered += [filter_name]
                
                elif name in ['groups', 'filters']:
                    print 'PROPERTIES WARNING (%s): This field is no longer necessary in the properties file.\nOnly the group_SQL_XXX and filter_SQL_XXX fields are needed when defining groups and filters.'%(name)
                    
                else:
                    raise Exception, 'Unrecognized field "%s" in properties file'%(name)
                
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
        # Check that all required variables were loaded
        optional_vars = ['db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',
                         'table_id', 'image_url_prepend', 'image_csv_file',
                         'object_csv_file', 'area_scoring_column', 'trainint_set']
        for name in string_vars + list_vars:
            if name not in optional_vars:
                assert name in self.__dict__.keys(), 'PROPERTIES ERROR (%s): Field is missing.'%(name)
        
        # Check values of loaded variables
        for name, val in self.__dict__.items():
            # SINGLE VALUE VARIABLES
            if name == 'db_type':
                assert val.lower() in ['mysql', 'sqlite'], 'PROPERTIES ERROR (%s): Value must be either "mysql" or "sqlite".'%(name)
                if val.lower()=='sqlite':
                    for field in ['image_csv_file','object_csv_file']:
                        assert field in self.__dict__.keys(), 'PROPERTIES ERROR (%s): Field is required with db_type=sqlite.'%(field)
                if val.lower()=='mysql':
                    for field in ['db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',]:
                        assert field in self.__dict__.keys(), 'PROPERTIES ERROR (%s): Field is required with db_type=mysql.'%(field)
                    
            
            elif name =='db_port':
                if self.db_type.lower()=='mysql':
                    assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)
                elif self.db_type.lower()=='sqlite':
                    if val:
                        print 'PROPERTIES WARNING (%s): Field not required with db_type=sqlite.'%(name)
            
            elif name =='db_host':
                if self.db_type.lower()=='mysql':
                    assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)
                elif self.db_type.lower()=='sqlite':
                    if val:
                        print 'PROPERTIES WARNING (%s): Field not required with db_type=sqlite.'%(name)
            
            elif name =='db_name':
                if self.db_type.lower()=='mysql':
                    assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)
                elif self.db_type.lower()=='sqlite':
                    if val:
                        print 'PROPERTIES WARNING (%s): Field not required with db_type=sqlite.'%(name)
                        
            elif name =='db_passwd':
                # Could be left blank. Not optional.
                pass

            elif name =='image_table':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='object_table':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='image_csv_file':
                if self.db_type.lower()=='mysql':
                    if val:
                        print 'PROPERTIES WARNING (%s): Field not required with db_type=mysql.'%(name)
                elif self.db_type.lower()=='sqlite':
                    assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='object_csv_file':
                if self.db_type.lower()=='mysql':
                    if val:
                        print 'PROPERTIES WARNING (%s): Field not required with db_type=mysql.'%(name)
                elif self.db_type.lower()=='sqlite':
                    assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)
                    
            elif name =='table_id':
                # Optional
                pass
                    
            elif name =='image_id':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='object_id':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='cell_x_loc':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='cell_y_loc':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='image_url_prepend':
                # Optional
                pass

            elif name =='image_tile_size':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='image_buffer_size':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='tile_buffer_size':
                assert val, 'PROPERTIES ERROR (%s): No value specified.'%(name)

            elif name =='area_scoring_column':
                #Optional
                print 'PROPERTIES: Area scoring will be used.'
                pass

            elif name=='groups':
                # Groups are validated on load
                pass

            elif name=='filters':
                # Filters are validated on load
                pass

            # LIST VARIABLES
            elif name=='image_channel_paths':
                assert val, 'PROPERTIES ERROR (%s): No value(s) specified.'%(name)

            elif name=='image_channel_files':
                assert val, 'PROPERTIES ERROR (%s): No value(s) specified.'%(name)

            elif name=='image_channel_names':
                assert val, 'PROPERTIES ERROR (%s): No value(s) specified.'%(name)

            elif name=='image_channel_colors':
                assert val, 'PROPERTIES ERROR (%s): No value(s) specified.'%(name)

            elif name=='object_name':
                assert val, 'PROPERTIES ERROR (%s): No values specified.'%(name)

            elif name=='classifier_ignore_substrings':
                if not val:
                    print 'PROPERTIES WARNING (%s): No values specified. Classifier will use ALL per_object columns when training.'%(name)

            elif name =='training_set':
                #Optional
                if val:
                    try:
                        f = open(val)
                        f.close()
                    except:
                        print 'PROPERTIES WARNING (%s): Training set at "%s" could not be found.'%(name,val)                        
                    print 'PROPERTIES: Training set found at "%s"'%(val)


        
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        filename = "../Properties/nirht_test.properties"
    p = Properties.getInstance()
    p.LoadFile(filename)
#    print p
