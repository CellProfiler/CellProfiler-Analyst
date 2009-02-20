from random import randint
import numpy
from DBConnect import *
from Singleton import *
from Properties import Properties

p = Properties.getInstance()
db = DBConnect.getInstance()

class DataModel(Singleton):
    '''
    DataModel is a dictionary of perImageObjectCounts indexed by (TableNumber,ImageNumber)
    '''
    
    def __init__(self):
        self.data = {}           # {imKey:obCount, ... }
        self.groupMaps = {}      # { groupName:{imKey:groupKey, }, ... }
                                 # eg: groupMaps['Wells'][(0,4)]  ==>  (3,'A01')
        self.groupColNames = {}  # {groupName:[group_key_col_names], ...}
                                 # eg: {'Gene': ['gene']}
        self.cumSums = []        # cumSum[i]: sum of objects in images 1..i (inclusive) 
        self.obCount = 0
        self.keylist = []
        
    def __str__(self):
        return str(self.obCount)+" objects in "+ \
               str(len(self.data))+" images"
               
    
    def PopulateModel(self):
        self.DeleteModel()
        if db is None:
            print "Error: No database connection!"
            return
        
        # Initialize per-image object counts to zero
        imKeys = db.GetAllImageKeys()
        for key in imKeys:
            key = tuple([int(k) for k in key])    # convert keys to to int tuples
            self.data[key] = 0
                    
        # Compute per-image object counts
        res = db.GetPerImageObjectCounts()
        for r in res:
            key = tuple([int(k) for k in r[:-1]])
            self.data[key] = r[-1]
            self.obCount += r[-1]
            
        self.keylist = list(self.data.keys())

        # Build a cumulative sum array to use for generating random objects quickly
        self.cumSums = numpy.zeros(len(self.data)+1, dtype='int')
        for i, imKey in enumerate(self.keylist):
            self.cumSums[i+1] = self.cumSums[i]+self.data[imKey]

        self.groupMaps, self.groupColNames = db.GetGroupMaps()

    def DeleteModel(self):
        self.data = {}
        self.groupMaps = {}
        self.cumSums = []
        self.obCount = 0
        
    
    def GetRandomObject(self):
        '''
        Returns a random object key
        We expect self.data.keys() to return the keys in the SAME ORDER
        every time since we build cumSums from that same ordering.  This
        need not necessarily be in sorted order.
        '''
        obIdx = randint(1, self.obCount)
#        print 'rand:',obIdx
        imIdx = numpy.searchsorted(self.cumSums, obIdx, 'left')
        # SUBTLETY: images which have zero objects will appear as repeated
        #    sums in the cumulative array, so we must pick the first index
        #    of any repeated sum, otherwise we are picking an image with no
        #    objects
        while self.cumSums[imIdx] == self.cumSums[imIdx-1]:
            imIdx -= 1
        imKey = self.data.keys()[imIdx-1]
        obIdx = obIdx-self.cumSums[imIdx-1]  # object number relative to this image
                    
        obKey = db.GetObjectIDAtIndex(imKey, obIdx)
        return obKey
        

    def GetRandomObjects(self, N, imKeys=None):
        '''
        Returns N random objects.
        If a list of imKeys is specified, GetRandomObjects will return 
        objects from only these images.
        '''
        if imKeys == None:
            return [self.GetRandomObject() for i in xrange(N)]
        elif imKeys == []:
            return []
        else:
            sums = numpy.cumsum([self.data[imKey] for imKey in imKeys])
            obs = []
            for i in xrange(N):
                obNum = randint(1, sums[-1])
                index = numpy.searchsorted(sums, obNum, 'left')
                while sums[index] == sums[index-1]:
                    index -= 1
                obNum = obNum-sums[index-1]
                obs.append(tuple(list(imKeys[index])+[obNum]))
            return obs
            
    
#    def GetRandomObjectFromImage(self, imKey):
#        obNum = randint(1, self.data[imKey])
#        obKey = list(imKey)
#        obKey.append(obNum)
#        return tuple(obKey)


    def GetObjectsFromImage(self, imKey):
        obKeys=[]
        for i in xrange(self.data[imKey]):
            obKey = list(imKey)
            obKey.append(i+1)
            obKeys.append(tuple(obKey))
        return obKeys


    def GetObjectCountFromImage(self, imKey):
        ''' Returns the number of objects in the specified image. '''
        return self.data[imKey]
    
    
    def GetImageKeysAndObjectCounts(self, filter=None):
        ''' Returns pairs of imageKeys and object counts. '''
        if not filter:
            return self.data.items()
        else:
            return [(imKey, self.data[imKey]) for imKey in db.GetFilteredImages(filter)]
    
    
    def GetGroupColumnNames(self, group):
        ''' Returns the key column names associated with the specified group. '''
        return list(self.groupColNames[group])   # return a copy of this list so it can't be modified
    
    
    def SumToGroup(self, imdata, group):
        '''
        Takes image data of the form:
           imdata = { imKey : numpy.array(values), ... }
        and sums the data into the specified group to return:
           groupdata = { groupKey : numpy.array(values), ... }
        '''
        groupData = {}
        for imKey, vals in imdata.items():
            # get the group of this image
            groupKey = self.groupMaps[group][imKey]            
            # add values to running sum of this group
            if groupKey in groupData.keys():
                groupData[groupKey] += vals
            else:
                groupData[groupKey] = vals
        return groupData
    
    
    def GetImagesInGroup(self, group, groupKey):
        ''' Returns all imKeys in a particular group. '''
        return [imKey for imKey,gKey in self.groupMaps[group].items() if gKey==groupKey]
        
    
    def IsEmpty(self):
        return self.data is {}



if __name__ == "__main__":
    p = Properties.getInstance()
    p.LoadFile('../properties/nirht_test.properties')
#    p.LoadFile('../properties/2007_10_19_Gilliland_LeukemiaScreens02_12_Jan_09_Combo.properties')
    db = DBConnect.getInstance()
    db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
    d = DataModel.getInstance()
    d.PopulateModel()
    
    for i in range(100):
        print d.GetRandomObject()
#    imKeys = d.GetImagesInGroup('Gene', d.groupMaps['Gene'][(1,)])
#    print len(imKeys)
#    for im in imKeys:
#        print im
    
#    imKeysInGroup = db.GetImagesInGroup('Accuracy75')
#    a = d.GetRandomObjects(1000, imKeysInGroup)
#    for obKey in a:
#        assert d.GetObjectCountFromImage(obKey[:-1]) != 0, 'image contains no objects'
#    print a

#    a = [d.GetRandomObject() for i in xrange(2000)]
#    for obKey in a:
#        assert d.GetObjectCountFromImage(obKey[:-1]) != 0, 'image contains no objects'

    # Test random for whole dataset
#    for j in xrange(1,10000):
#        obKey = d.GetRandomObjectFromImageList(db.GetImagesInGroup('CDKs'))
#        if obKey[-1] > d.GetObjectCountFromImage(obKey[:-1]) and obKey[-1]>0:
#            print "ERROR:",str(obKey),">",d.GetObjectCountFromImage(t,i)

    # Test random for image lists
    # NOTE: obKey[:-1] is always imKey
#    a=b=0
#    for j in xrange(1,10000):
#        imKeys = [(2,1536),(2,1496)]
#        obKey = d.GetRandomObjectFromImageList(imKeys)
#        if obKey[:-1] == (2,1536):
#            a+=1
#        elif obKey[:-1] == (2,1496):
#            b+=1
#        else:
#            print "ERROR"
#    print a,"should be about half of",b
#    
#    # Get random objects from group 'good_control'
#    for j in xrange(10):
#        print d.GetRandomObjectFromImageList(db.GetImagesInGroup('good_control'))
