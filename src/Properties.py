'''
Properties.py
Authors: afraser
'''

from Singleton import *

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
        if( not self.__dict__.has_key(id) ):
            return None
        else:
            return self.__dict__[id]
    
    
    def LoadFile(self, filename):
        ''' Loads variables in from a properties file. '''
        self.Clear()
        f = open(filename, 'r')
        
        lines = f.read()
        lines = lines.replace('\r', '\n')                        # replace CRs with LFs
        lines = lines.split('\n')

        # TODO: Copy all lines for saving files with whitespace
#        self.lines = lines

        self.groups = {}
        self.groups_ordered = []
        self.filters = {}
        self.filters_ordered = []

        for line in lines:
            if not line.strip().startswith('#') and line.strip()!='':          # skip commented and empty lines
                (name, val) = line.split('=', 1)                               # split each side of the first eq sign
                name = name.strip()
                val = val.strip()
                                
                if name in ['db_type',
                            'db_port',
                            'db_host',
                            'db_name',
                            'db_user',
                            'db_passwd',
                            'image_table',
                            'object_table',
                            'image_csv_file',
                            'object_csv_file',
                            'table_id',
                            'image_id',
                            'object_id',
                            'cell_x_loc',
                            'cell_y_loc',
                            'image_url_prepend',
                            'image_tile_size',
                            'image_buffer_size',
                            'tile_buffer_size']:
                    self.__dict__[name] = val
                
                elif name in ['image_channel_paths',
                            'image_channel_files',
                            'image_channel_names',
                            'image_channel_colors',
                            'object_name',
                            'classifier_ignore_substrings']:
                    self.__dict__[name] = [v.strip() for v in val.split(',') if v.strip() is not '']
                    
                elif name.startswith('group_SQL_'):
                    group_name = name[10:]
                    if group_name == '':
                        raise Exception, '''Invalid syntax in properties file, "group_SQL_" should be followed by a group name.
Example: "group_SQL_MyGroup = <QUERY>" would define a group named "MyGroup" defined by
a MySQL query "<QUERY>". See the README.'''
                    if group_name in self.groups.keys():
                        raise Exception, 'Group "%s" is defined twice in properties file.'%(group_name)
                    self.groups[group_name] = val
                    self.groups_ordered += [group_name]
                    
                elif name.startswith('filter_SQL_'):
                    filter_name = name[11:]
                    if filter_name == '':
                        raise Exception, '''Invalid syntax in properties file, "filter_SQL_" should be followed by a filter name.
Example: "filter_SQL_MyFilter = <QUERY>" would define a filter named "MyFilter" defined by
a MySQL query "<QUERY>". See the README.'''
                    if filter_name in self.filters.keys():
                        raise Exception, 'Filter "%s" is defined twice in properties file.'%(filter_name)
                    self.filters[filter_name] = val
                    self.filters_ordered += [filter_name]
                
                else:
                    raise Exception, 'Unrecognized field "%s" in properties file'%(name)
                    
        f.close()
        
    
    def SaveFile(self, filename):
        # TODO: Save files WITH previous comments and whitespace.
        f = open(filename, 'w')
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
        
        
if __name__ == "__main__":
    p = Properties.getInstance()
    p = Properties.getInstance()
    p.LoadFile('../Properties/nirht_test.properties')
    print p
