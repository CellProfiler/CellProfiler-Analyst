'''
DataProvider.py
This class is meant to provide an interface to be overridden by classes
that provide access to per-image and per-object table data. 
'''

class DataProvider(object):
    def __init__(self):
        pass 
    

    def GetObjectIDAtIndex(self, imKey, index, connID='default'):
        ''' Returns the true object ID of the nth object in an image.
        Note: This should be used when object IDs aren't contiguous
              starting at 1.
        '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.'
    
    
    def GetPerImageObjectCounts(self, connID='default'):
        ''' Returns a list of (imKey, obCount) tuples. '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.'
    
    
    def GetAllImageKeys(self, connID='default'):
        ''' Returns a list of all image keys in the image_table. '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.'
    
    
    def GetColumnNames(self, tableName, connID='default'):
        ''' Returns a list of the column names for the specified table. '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
        
    
    def GetObjectCoords(self, obKey, connID='default'):
        ''' Returns the specified object's x, y coordinates in an image. '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
    
    
    def GetObjectNear(self, imkey, x, y, connID='default'):
        ''' Returns obKey of the closest object to x, y in an image. '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
    
    
    def GetFullChannelPathsForImage(self, imKey, connID='default'):
        ''' Returns a list of image channel filenames for a particular image
        including the absolute path.
        '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
    
    
    def GetFilteredImages(self, filter, connID='default'):
        ''' Returns a list of imKeys from the given filter. '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
    
    
    def GetColnamesForClassifier(self, connID='default'):
        ''' Returns a list of column names for the object_table excluding 
        those specified in Properties.classifier_ignore_substrings
        '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
    
    
    def GetCellDataForClassifier(self, obKey, connID='default'):
        ''' Returns a list of measurements for the specified object excluding
        those specified in Properties.classifier_ignore_substrings
        '''
        raise Exception, 'ERROR <DataProvider>: Method unimplemented! This method should be overridden by all DataProvider subclasses.' 
    
    
if __name__ == "__main__":
    class Test(DataProvider):
        pass
    
    t = Test()
    t.GetCellDataForClassifier(None)
    