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
            s += k + " = " + str(v) + "\n"
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
            
        for line in lines:
            if not line.strip().startswith('#') and line.strip()!='':          # skip commented and empty lines
                
                (name, val) = line.split('=', 1)                               # split each side of the first eq sign
                name = name.strip()
                val = val.strip()
                
                if val=='': continue                                   # skip empty entries (handled in __getattr___)
                
                # Special SQL cases are not to be parsed into lists
                if name.startswith('filter_SQL_') or name.startswith('group_SQL_'):
                    self.__dict__[name] = val
                    continue
                
                # Comma separated entries are parsed into a list
                # All others are set to the right-hand side of the '='
                if val.find(',') == -1:
                    self.__dict__[name] = val
                else:
                    self.__dict__[name] = [v.strip() for v in val.split(',') if v.strip() is not '']
        f.close()
        
    
    def SaveFile(self, filename):
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
    p.LoadFile('/Users/afraser/Desktop/testLee.txt')#/nirht_test.properties')
    print p
