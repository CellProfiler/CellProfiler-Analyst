from itertools import islice

from .dbconnect import *
from .singleton import *
from .properties import Properties

p = Properties()
db = DBConnect()

class DataModel(metaclass=Singleton):
    '''
    DataModel is a dictionary of perImageObjectCounts indexed by (TableNumber,ImageNumber)
    '''
    
    def __init__(self):
        self.data = {}           # {imKey:obCount, ... }
        self.groupMaps = {}      # { groupName:{imKey:groupKey, }, ... }
                                 # eg: groupMaps['Wells'][(0,4)]  ==>  (3,'A01')
        self.revGroupMaps = {}   # { groupName:{groupKey:imKey, }, ... }
                                 # eg: groupMaps['Wells'][(3,'A01')]  ==>  [(0,1),(0,2),(0,3),(0,4)]
        self.groupColNames = {}  # {groupName:[col_names,...], ...}
                                 # eg: {'Plate+Well': ['plate','well'], ...}
        self.groupColTypes = {}  # {groupName:[col_types,...], ...}
        self.cumSums = []        # cumSum[i]: sum of objects in images 1..i (inclusive) 
        self.obCount = 0
        self.keylist = []
        self.filterkeys = {}     # sets of image keys keyed by filter name
        self.plate_map = {}      # maps well names to (x,y) plate locations
        self.rev_plate_map = {}  # maps (x,y) plate locations to well names
        
    def __str__(self):
        return str(self.obCount)+" objects in "+ \
               str(len(self.data))+" images"
               
    def PopulateModel(self, delete_model=False):
        if delete_model:
            self.DeleteModel()
        elif not self.IsEmpty():
            # No op if already populated
            return
        
        if db is None:
            logging.error("Error: No database connection!")
            return
        
        if p.check_tables == 'yes':
            db.CheckTables()
        
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
        self.cumSums = np.zeros(len(self.data)+1, dtype='int')
        for i, imKey in enumerate(self.keylist):
            self.cumSums[i+1] = self.cumSums[i]+self.data[imKey]

        self.groupMaps, self.groupColNames = db.GetGroupMaps()
        self.revGroupMaps, _ = db.GetGroupMaps(reverse=True)
        for group in self.groupMaps:
            self.groupColTypes[group] = [type(col) for col in list(self.groupMaps[group].items())[0][1]]

    def DeleteModel(self):
        self.data = {}
        self.groupMaps = {}
        self.cumSums = []
        self.obCount = 0
        
    def _if_empty_populate(self):
        if self.IsEmpty:
            self.PopulateModel()
            
    def get_total_object_count(self):
        self._if_empty_populate()
        return self.obCount
        
    def GetRandomObject(self, N):
        '''
        Returns a random object key
        We expect self.data.keys() to return the keys in the SAME ORDER
        every time since we build cumSums from that same ordering.  This
        need not necessarily be in sorted order.
        '''
        self._if_empty_populate()
        obIdxs = random.sample(list(range(1, self.obCount + 1)), N)
        obKeys = []
        for obIdx in obIdxs:
            imIdx = np.searchsorted(self.cumSums, obIdx, 'left')
            # SUBTLETY: images which have zero objects will appear as repeated
            #    sums in the cumulative array, so we must pick the first index
            #    of any repeated sum, otherwise we are picking an image with no
            #    objects
            while self.cumSums[imIdx] == self.cumSums[imIdx-1]:
                imIdx -= 1
            imKey = list(self.data.keys())[imIdx-1]
            obIdx = obIdx-self.cumSums[imIdx-1]  # object number relative to this image
            obKeys.append(db.GetObjectIDAtIndex(imKey, obIdx))
        return obKeys

    def GetRandomObjects(self, N, imKeys=None, with_replacement=False):
        '''
        Returns N random objects.
        If a list of imKeys is specified, GetRandomObjects will return 
        objects from only these images.
        '''
        self._if_empty_populate()
        if N > self.obCount:
            logging.info(f"{N} is greater than the number of objects. Fetching {self.obCount} objects.")
            N = self.obCount
        if imKeys == None:
            if p.use_legacy_fetcher:
                return self.GetRandomObject(N)
            else:
                return db.GetRandomObjectsSQL(None, N)
        elif imKeys == []:
            return []
        else:
            if p.use_legacy_fetcher:
                sums = np.cumsum([self.data[imKey] for imKey in imKeys])
                if sums[-1] < 1:
                    return []
                obs = []
                if with_replacement:
                    obIdxs = random.choices(list(range(1, sums[-1] + 1)), k=N)
                else:
                    if N > sums[-1]:
                        logging.info(f"Number of available objects is less than {N}. Fetching {sums[-1]} objects.")
                        N = sums[-1]
                    obIdxs = random.sample(list(range(1, sums[-1]+1)), k=N)
                for obIdx in obIdxs:
                    index = np.searchsorted(sums, obIdx, 'left')
                    if index != 0:
                        while sums[index] == sums[index-1]:
                            index -= 1
                        obIdx = obIdx-sums[index-1]
                    obKey = db.GetObjectIDAtIndex(imKeys[index], obIdx)
                    obs.append(obKey)
            else:
                obs = db.GetRandomObjectsSQL(imKeys, N)
                if with_replacement and 0 < len(obs) < N:
                    obs = random.choices(obs, k=N)
            return obs

    def GetAllObjects(self, filter_name=None, gate_name=None, imkeys=[], N=None):
        self._if_empty_populate()
        if imkeys == []:
            imkeys = self.GetAllImageKeys(filter_name=filter_name, gate_name=gate_name)
        if p.use_legacy_fetcher:
            obs = (x for im in imkeys for x in self.GetObjectsFromImage(im))
            if N is None:
                return list(obs)
            else:
                return list(islice(obs, N))
        else:
            return db.GetAllObjectsSQL(imkeys, N)

    def GetObjectsFromImage(self, imKey):
        self._if_empty_populate()
        if p.use_legacy_fetcher:
            obKeys=[]
            for i in range(1,self.GetObjectCountFromImage(imKey)+1):
                obKeys.append(db.GetObjectIDAtIndex(imKey, i))
        else:
            obKeys = db.GetAllObjectsSQL([imKey])
        return obKeys

    def GetAllImageKeys(self, filter_name=None, gate_name=None):
        ''' Returns all object keys. If a filter is passed in, only the image
        keys that fall within the filter will be returned.'''
        self._if_empty_populate()
        if filter_name is not None:
            return db.GetFilteredImages(filter_name)
        elif gate_name is not None:
            return db.GetGatedImages(gate_name)
        else:
            return list(self.data.keys())

    def GetObjectCountFromImage(self, imKey):
        ''' Returns the number of objects in the specified image. '''
        self._if_empty_populate()
        return self.data[imKey]
    
    def GetImageKeysAndObjectCounts(self, filter_name=None):
        ''' Returns pairs of imageKeys and object counts. '''
        self._if_empty_populate()
        if filter_name is None:
            return list(self.data.items())
        else:
            return [(imKey, self.data[imKey]) for imKey in db.GetFilteredImages(filter_name)]
    
    def GetGroupColumnNames(self, group, include_table_name=False):
        ''' Returns the key column names associated with the specified group. '''
        self._if_empty_populate()
        if include_table_name:
            # return a copy of this list so it can't be modified
            return list(self.groupColNames[group])
        else:
            return [col.split('.')[-1] for col in self.groupColNames[group]]

    def GetGroupColumnTypes(self, group):
        ''' Returns the key column types associated with the specified group. '''
        self._if_empty_populate()
        return list(self.groupColTypes[group])   # return a copy of this list so it can't be modified

    def SumToGroup(self, imdata, group):
        '''
        Takes image data of the form:
           imdata = { imKey : np.array(values), ... }
        and sums the data into the specified group to return:
           groupdata = { groupKey : np.array(values), ... }
        '''
        self._if_empty_populate()
        groupData = {}
        nvals = len(list(imdata.values())[0])
        for imKey in list(imdata.keys()):
            # initialize each entry to [0,0,...]
            groupData[self.groupMaps[group][imKey]] = np.zeros(nvals)
            
        for imKey, vals in list(imdata.items()):
            # add values to running sum of this group
            groupData[self.groupMaps[group][imKey]] += vals
        
        return groupData
    
    def GetImagesInGroupWithWildcards(self, group, groupKey, filter_name=None):
        '''
        Returns all imKeys in a particular group. 
        '__ANY__' in the groupKey matches anything.
        '''
        self._if_empty_populate()
        if '__ANY__' in groupKey:
            # if there are wildcards in the groupKey then accumulate
            #   imkeys from all matching groupKeys
            def matches(key1, key2):
                return all([(a==b or b=='__ANY__') for a,b in zip(key1,key2)])
            imkeys = []
            for gkey, ikeys in list(self.revGroupMaps[group].items()):
                if matches(gkey,groupKey):
                    imkeys += ikeys
            return imkeys
        else:
            # if there are no wildcards simply lookup the imkeys
            return self.GetImagesInGroup(group, groupKey, filter_name)
    
    def GetImagesInGroup(self, group, groupKey, filter_name=None):
        ''' Returns all imKeys in a particular group. '''
        self._if_empty_populate()
        try:
            imkeys = self.revGroupMaps[group][groupKey]
        except KeyError:
            return []
            
        # apply filter if supplied
        if filter_name is not None:
            if filter_name not in list(self.filterkeys.keys()):
                self.filterkeys[filter_name] = db.GetFilteredImages(filter_name)
            imkeys = set(imkeys).intersection(self.filterkeys[filter_name])    
        
        return imkeys
    
    def GetGroupKeysInGroup(self, group):
        ''' Returns all groupKeys in specified group '''
        self._if_empty_populate()
        return list(set(self.groupMaps[group].values()))
        
    def IsEmpty(self):
        return self.data == {}
    
    def populate_plate_maps(self):
        '''Computes plate_maps which maps well names to their corresponding
        plate positions, and rev_plate_maps which does the reverse.
        eg: plate_maps['A01'] = (0,0)
            rev_plate_maps[(0,0)] = 'A01'
        '''
        if p.well_format == 'A01':
            well_re = r'^[A-Za-z]\d+$'
        elif p.well_format == '123':
            well_re = r'^\d+$'
        else:
            raise ValueError('Unknown well format: %s' % repr(p.well_format))
        
        pshape = p.plate_shape
        
        res = db.execute('SELECT DISTINCT %s FROM %s '%(p.well_id, p.image_table))
        for r in res:
            well = r[0]
            # Make sure all well entries match the naming format
            if type(well) == str:
                well = well.strip()
                assert re.match(well_re, well), 'Well "%s" did not match well naming format "%s"'%(r[0], p.well_format)
            elif type(well) == int:
                if not p.well_format == '123':
                    '''
                    import wx
                    wx.MessageBox('Well "%s" did not match well naming format "%s".\n'
                                  'If your wells are in numerical format then add\n'
                                  'the line "well_format = 123" to your properties'
                                  'file. Trying well_format = 123.'%(r[0], p.well_format), 'Error')
                    '''
                    p.well_format = '123'
                    try:
                        self.populate_plate_maps()
                    except:
                        import wx
                        wx.MessageBox('Error when trying well_format = 123. Try another well naming format.', 'Error')
                    return

            if p.well_format == 'A01':
                if pshape[0] <= 26:
                    row = 'abcdefghijklmnopqrstuvwxyz'.index(well[0].lower())
                    col = int(well[1:]) - 1
                elif pshape[0] <= 52:
                    row = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'.index(well[0])
                    col = int(well[1:]) - 1
                else:
                    raise ValueError('Plates with over 52 rows cannot have well format "A01" Check your properties file.')
                self.plate_map[well] = (row, col)
                self.rev_plate_map[(row, col)] = well
            elif p.well_format == '123':
                row = (int(well) - 1) // pshape[1]
                col = (int(well) - 1) % pshape[1]
                self.plate_map[well] = (row, col)
                self.rev_plate_map[(row, col)] = well
    
    def get_well_position_from_name(self, well_name):
        '''returns the plate position tuple (row, col) corresponding to 
        the given well_name.
        '''
        try:
            well_name = well_name.strip()
        except:
            pass
        if self.plate_map == {}:
            self.populate_plate_maps()
        if well_name in list(self.plate_map.keys()):
            return self.plate_map[well_name]
        else:
            raise KeyError('Well name "%s" could not be mapped to a plate position.' % well_name)

    def get_well_name_from_position(self, xxx_todo_changeme):
        '''returns the well name (eg: "A01") corresponding to the given 
        plate position tuple.
        '''
        (row, col) = xxx_todo_changeme
        if self.plate_map == {}:
            self.populate_plate_maps()
        if (row, col) in list(self.rev_plate_map.keys()):
            return self.rev_plate_map[(row, col)]
        else:
            raise KeyError('Plate position "%s" could not be mapped to a well key.' % str((row,col)))


if __name__ == "__main__":
    p = Properties()
    p.LoadFile('../properties/2009_02_19_MijungKwon_Centrosomes.properties')
    db = DBConnect()
    db.connect()
    d = DataModel()
    d.PopulateModel()
