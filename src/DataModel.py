'''
DataModel.py
Authors: afraser
'''

import wx
from random import randint
import numpy
from DBConnect import DBConnect
from Singleton import *
from Properties import Properties

p = Properties.getInstance()

class DataModel(Singleton):
    '''
    DataModel is a dictionary of perImageObjectCounts indexed by (TableNumber,ImageNumber)
    '''
    
    def __init__(self):
        self.data = {}        # {imKey:obCount, ... }
        self.groupMaps = {}   # { groupName:{imKey:groupKey, }, ... }
                              # eg: groupMaps['Wells'][(0,4)]  ==>  (3,'A01')
        self.cumSums = []     # cumSum[i]: sum of objects in images 1..i (inclusive) 
        self.obCount = 0
        
    def __str__(self):
        return str(self.obCount)+" objects in "+ \
               str(len(self.data))+" images"
               
    
    def PopulateModel(self):
        self.DeleteModel()
        db = DBConnect.getInstance()
        if db is None:
            print "Error: No database connection!"
            return
            
        if 'table_id' in p.__dict__:
            imgKey = p.table_id+', '+p.image_id
        else:
            imgKey = p.image_id
            
        db.Execute("SELECT "+imgKey+" FROM "+p.image_table+" GROUP BY "+imgKey)
        res = db.GetResultsAsList()
        for key in res:
            key = tuple([int(k) for k in key])    # convert keys to to int tuples
            self.data[key] = 0
          
        db.Execute("SELECT "+imgKey+", count("+p.object_id+") FROM "+str(p.object_table)+" GROUP BY "+imgKey)
        res = db.GetResultsAsList()  # = [(imKey, obCt), (imKey, obCt)...]
        for r in res:
            key = tuple([int(k) for k in r[:-1]])
            self.data[key] = r[-1]
            self.obCount += r[-1]
            
        # Build a cumulative sum array to use for generating random objects quickly
        self.cumSums = numpy.zeros(len(self.data)+1)
        for i in xrange(1, len(self.data)+1):
            if 'table_id' in p.__dict__:
                imKey = (0,i)
            else:
                imKey = (i,)
            self.cumSums[i] = self.cumSums[i-1]+self.data[imKey]
            
        # Build dictionary mapping group names and image keys to group keys
        if 'groups' in p.__dict__:
            for group in p.groups:
                if 'group_SQL_'+group in p.__dict__:
                    db.Execute( p.__dict__['group_SQL_'+group] )
                    res = db.GetResultsAsList()
                    groupDict = {}
                    for row in res:
                        if 'table_id' in p.__dict__:
                            imKey = row[:2]
                            groupKey = row[2:]
                        else:
                            imKey = row[:1]
                            groupKey = row[1:]
                        groupDict[imKey] = groupKey
                    self.groupMaps[group] = groupDict
        

    def DeleteModel(self):
        self.data = {}
        self.groupMaps = {}
        self.cumSums = []
        self.obCount = 0
        
    
    def GetRandomObject(self):
        ''' Returns a random object key '''
        obNum = randint(1, self.obCount)
        imNum = numpy.searchsorted(self.cumSums, obNum, 'left')
        # SUBTLETY: images which have zero objects will appear as repeated
        #    sums in the cumulative array, so we must pick the first index
        #    of any repeated sum, otherwise we are picking an image with no
        #    objects
        while self.cumSums[imNum] == self.cumSums[imNum-1]:
            imNum -= 1
        obNum = obNum-self.cumSums[imNum-1]  # object number relative to this image  
        if 'table_id' in p.__dict__:
            return (0,imNum,obNum)
        else:
            return (imNum,obNum)


    def GetRandomObjects(self, N, imKeys=None):
        ''' imKeys: if included, GetRandomObjects will return objects from only these images '''
        if not imKeys:
            return [self.GetRandomObject() for i in xrange(N)]
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


    def GetObjectCountFromImage(self, imKey):
        ''' Returns the number of objects in the specified image. '''
        return self.data[imKey]
    
    
    def SumToGroup(self, imdata, group):
        '''
        Takes image data of the form:
           imdata = { imKey : numpy.array(values), ... }
        and sums the data into the specified group to return:
           groupdata = { groupKey : numpy.array(values), ... }
        '''
        # imData = {imKey: numpy.array(), ... }
        groupData = {}
        for imKey, vals in imdata.items():
            groupKey = self.groupMaps[group][imKey]   # get the group of this image
            
            # add vals to running sum of this group
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
    p.LoadFile('../properties/nirht_NO_TABLE.properties')
    db = DBConnect.getInstance()
    db.Connect(db_host="imgdb01", db_user="cpadmin", db_passwd="cPus3r", db_name="cells")
    d = DataModel.getInstance()
    d.PopulateModel()
    
    
    imKeys = d.GetImagesInGroup('Gene', d.groupMaps['Gene'][(1,)])
    print len(imKeys)
    for im in imKeys:
        print im
    
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
