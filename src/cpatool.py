'''
'''
import wx

class CPATool(object):
    '''Any tool or visualization whose state may be saved and recalled from a 
    series of settings and corresponding values.'''
    def __init__(self):
        # Set the name of the tool based on the class name.  A subclass can 
        # override this by declaring a tool_name attribute in the class
        # definition
        if 'tool_name' not in self.__dict__:
            self.tool_name = self.__class__.__name__

    def save_settings(self):
        '''Override this method when defining a new tool or visualization.

        save_settings is called when saving a workspace to file.
        
        returns a dictionary mapping setting names to values encoded as strings
        '''
        raise NotImplementedError
    
    def load_settings(self, settings):
        '''Override this method when defining a new tool or visualization.
        
        load_settings is called when loading a workspace from file.
        
        settings - a dictionary mapping setting names to values encoded as
                   strings.
        '''
        raise NotImplementedError
