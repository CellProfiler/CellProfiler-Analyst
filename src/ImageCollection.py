'''
ImageCollection.py
Authors: afraser
'''

import wx
import ImageTools
from Singleton import Singleton
from DBConnect import DBConnect
from Properties import Properties
from ImageReader import ImageReader

db = DBConnect.getInstance()


class ImageCollection(Singleton):
    '''
    This class abstracts the database access required for image retrieval.
    It acts as an image cache allowing for retrieval of images and tiles.
    '''
    def __init__(self, properties):
        self.p = properties
        db.Connect(self.p.db_host, self.p.db_user, self.p.db_passwd, self.p.db_name, connID='ImageCollectionConn')

        self.tileCache  = {}    # (tblNum,imNum,obNum): cropped image channel data
        self.imageCache = {}    # (tblNum,imNum): image channel data

        self.maxTiles  = int(self.p.tile_buffer_size)    # max number of cropped image-sets to store at a time
        self.maxImages = int(self.p.image_buffer_size)   # max number of image-sets to store at a time
        
        self.tileKeyQueue  = [] # queues determine the order in which cache entries are removed
        self.imageKeyQueue = [] # queues determine the order in which cache entries are removed
        
        
    def FetchImage(self, imKey):
        '''
        Returns image channel data.
        '''
        if imKey not in self.imageCache.keys():
            self.UpdateCache(imKey)
        return self.imageCache[imKey]

    
    def FetchTile(self, obKey):
        '''
        Returns image channel data cropped around the specified object.
        '''
        if obKey not in self.tileCache.keys():
            self.UpdateTileCache(obKey)
        return self.tileCache[obKey]
    
    
    def UpdateTileCache(self, obKey):
        '''
        Updates the tile cache by cropping images fetched through FetchImages.
        '''
        imKey = obKey[:-1]
        
        # Remove the oldest element in the cache if it's full
        self.tileKeyQueue.insert(0,obKey)
        if len(self.tileCache) >= self.maxTiles:
            self.tileCache.pop(self.tileKeyQueue[-1])
            self.tileKeyQueue = self.tileKeyQueue[:self.maxTiles]
        
        pos = db.GetObjectCoords(obKey, 'ImageCollectionConn')
        
        size = (int(self.p.image_tile_size),int(self.p.image_tile_size))
        # add this image data to the tileCache
        self.tileCache[obKey] = [ImageTools.Crop(imData,size,pos) for imData in self.FetchImage(imKey)]
        
    
    def UpdateCache(self, imKey):
        '''
        Queries the DB for channel path information then
        reads the images associated with the key or keys specified.
        Each key and image set is added to the cache.
        '''
        # get the image paths
        filenames = db.GetFullChannelPathsForImage(imKey, 'ImageCollectionConn')
        # get the image data
        ir = ImageReader()
        images = ir.ReadImages(filenames)
        
        # remove the oldest element in the cache if it's full
        self.imageKeyQueue.insert(0,imKey)
        if len(self.imageCache) >= self.maxImages:
            self.imageCache.pop(self.imageKeyQueue[-1])
            self.imageKeyQueue = self.imageKeyQueue[:self.maxImages]

        # update the cache
        self.imageCache[imKey] = images





################# FOR TESTING ##########################
if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    from DataModel import DataModel
    from ImageViewer import ImageViewer
    import time
    p = Properties.getInstance()
    p.LoadFile('../properties/nirht_test.properties')
    db = DBConnect.getInstance()
    db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
    dm = DataModel.getInstance()
    dm.PopulateModel()
    
    test = ImageCollection.getInstance(p)
    
    t1 = time.time()    
    for i in xrange(1):
        obKey = dm.GetRandomObject()
        print obKey
        imgs = test.FetchImage(obKey[:-1])
        frame = ImageViewer(imgs=imgs, chMap=p.image_channel_colors)
        frame.Show(True)
        imgs = test.FetchTile(obKey)
        frame = ImageViewer(imgs=imgs, chMap=p.image_channel_colors)
        frame.Show(True)
    t2 = time.time()
    print t2-t1,'seconds' 
    
#    t1 = time.time()     
#    for i in xrange(20):
#        imgs = test.FetchTile(dm.GetRandomCell())
#        frame = ImageViewer(imgs=imgs)
#        frame.Show(True)
#    t2 = time.time()
#    print t2-t1,'seconds'
    
    app.MainLoop()
    


