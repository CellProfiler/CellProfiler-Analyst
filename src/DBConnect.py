'''
DBConnect.py
Authors: afraser
'''

import exceptions
import string
import numpy
import MySQLdb
from MySQLdb.cursors import SSCursor
from pysqlite2 import dbapi2 as sqlite
from Singleton import Singleton
from Properties import Properties
from DataProvider import DataProvider
from sys import stderr
p = Properties.getInstance()



class DBException(Exception):
    pass


def GetWhereClauseForObjects(obKeys):
    '''
    Returns a MySQL where-clause specifying the given object keys.
    eg: GetWhereClauseForObjects( [(1,3),(2,4)] ) = "WHERE <imnum>=1 AND <obnum>=3 OR <imnum>=2 AND <obnum>=4"
    '''
    wheres = []
    for obKey in obKeys:
        if p.table_id:
            where = p.table_id+'='+str(obKey[0])+' AND '+p.image_id+'='+str(obKey[1])+' AND '+p.object_id+'='+str(obKey[2])
        else:
            where = p.image_id+'='+str(obKey[0])+' AND '+p.object_id+'='+str(obKey[1])
        wheres.append(where)
    return ' OR '.join(wheres)


def GetWhereClauseForImages(imKeys):
    '''
    Returns a MySQL where-clause specifying the given image keys.
    eg: GetWhereClauseForObjects( [(3,),(4,)] ) = "WHERE <imnum>=3 OR <imnum>=4"
    '''
    wheres = []
    for imKey in imKeys:
        if p.table_id:
            where = p.table_id+'='+str(imKey[0])+' AND '+p.image_id+'='+str(imKey[1])
        else:
            where = p.image_id+'='+str(imKey[0])
        wheres.append(where)
    return ' OR '.join(wheres)


def UniqueObjectClause():
    '''
    Returns a clause for specifying a unique object in MySQL.
    eg: "SELECT <UniqueObjectClause()> FROM <mydb>;" would return all object keys
    '''

    if p.table_id:
        obCl = p.table_id+','+p.image_id+','+p.object_id
    else:
        obCl = p.image_id+','+p.object_id
    return obCl


def UniqueImageClause(table_name=None):
    '''
    Returns a clause for specifying a unique image in MySQL.
    eg: "SELECT <UniqueObjectClause()> FROM <mydb>;" would return all image keys 
    '''

    if table_name:
        table_name = table_name+'.'
    else:
        table_name = ''

    if p.table_id:
        imCl = table_name+p.table_id+','+table_name+p.image_id
    else:
        imCl = table_name+p.image_id
    return imCl




#
# TODO: Rename _Execute, _Connect, _GetNextResult, etc
#       If users can use non-DB tables then all DB specific functions should be
#       completely abstracted.
class DBConnect(DataProvider, Singleton):
    '''
    DBConnect abstracts calls to MySQLdb.
    '''
    def __init__(self):
        self.classifierColNames = None
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}

    def __str__(self):
        return string.join([ (key + " = " + str(val) + "\n")
                            for (key, val) in self.__dict__.items()])


    def Connect(self, db_host, db_user, db_passwd, db_name, connID='default'):

        if connID in self.connections.keys():
            if self.connectionInfo[connID] == (db_host, db_user, db_passwd, db_name):
                print 'WARNING <DBConnect.Connect>: Already connected to %s as %s@%s (connID = "%s").' % (db_name, db_user, db_host, connID)
            else:
                print 'WARNING <DBConnect.Connect>: connID "%s" is already in use. Close this connection first.' % (connID)
            return True

        # 
        if p.db_type.lower() == 'sqlite':
            self.connections[connID] = sqlite.connect('CPA_DB')
            self.cursors[connID] = self.connections[connID].cursor()
            self.connectionInfo[connID] = ('local', '', '', 'tempDB')
            # If this is the first connection, then we need to create the DB from the files
            if len(self.connections) == 1:
                try:
                    fimg = open(p.image_csv_file)
                    fobj = open(p.object_csv_file)
                except IOError:
                    raise Exception, 'ERROR <DBConnect.Connect>: Failed to open tables ("%s", "%s") from file.'%(p.image_table, p.object_table)
                else:
                    fimg.close()
                    fobj.close()
                    print 'No database info specified. Will attempt to load tables from file.'
                    self.CreateSQLiteDB()
            return True
        elif p.db_type.lower() == 'mysql':
            try:
                conn = MySQLdb.connect(host=db_host, db=db_name, user=db_user, passwd=db_passwd)
                self.connections[connID] = conn
                self.cursors[connID] = SSCursor(conn)
                self.connectionInfo[connID] = (db_host, db_user, db_passwd, db_name)
                print 'Connected to database: %s as %s@%s (connID = "%s").' % (db_name, db_user, db_host, connID)
                return True
            except MySQLdb.Error, e:
                raise DBException, 'ERROR <DBConnect.Connect>: Failed to connect to database: %s as %s@%s (connID = "%s").\n' % (db_name, db_user, db_host, connID)
                return False
        else:
            raise DBException, "ERROR <DBConnect.Connect>: Unknown db_type in properties: '%s'\n"%(p.db_type)


    def Disconnect(self):
        for conn in self.connections.values():
            conn.close()
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}
        self.classifierColNames = None
        
    
    def CloseConnection(self, connID):
        if connID in self.connections.keys():
            self.connections[connID].commit()
            self.connections.pop(connID).close()
            self.cursors.pop(connID)
            (db_host, db_user, db_passwd, db_name) = self.connectionInfo.pop(connID)
            print 'Closed connection: %s as %s@%s (connID = "%s").' % (db_name, db_user, db_host, connID)
        else:
            print 'WARNING <DBConnect.CloseConnection>: No connection ID "%s" found.' %(connID)


    def Execute(self, query, connID='default', silent=False):
        try:
            if not silent: print '['+connID+'] '+query
            self.cursors[connID].execute(query)
        except MySQLdb.Error, e:
            raise DBException, 'ERROR <DBConnect.Execute> Database query failed for connection "%s"\n\t%s\n\t%s\n' %(connID, query, e)
        except KeyError, e:
            raise DBException, 'ERROR <DBConnect.Execute> No such connection: "%s".\n' %(connID)
            
    def Commit(self, connID='default'):
        try:
            print '['+connID+'] - commit'
            self.connections[connID].commit()
        except MySQLdb.Error, e:
            raise DBException, 'ERROR <DBConnect.Commit> Commit failed for connection "%s"\n\t%s\n' %(connID, e)
        except KeyError, e:
            raise DBException, 'ERROR <DBConnect.Execute> No such connection: "%s".\n' %(connID)
            


    def GetNextResult(self, connID='default'):
        try:
            return self.cursors[connID].next()
        except MySQLdb.Error, e:
            raise DBException, 'ERROR <DBConnect.GetNextResult> Error retrieving next result from database.\n'
            return None
        except StopIteration, e:
            return None
        except KeyError, e:
            raise DBException, 'ERROR <DBConnect.GetNextResult> No such connection: "%s".\n' %(connID)
        
        
    def GetResultsAsList(self, connID='default'):
        ''' Returns a list of results retrieved from the last execute query. '''
        r = self.GetNextResult(connID)
        l = []
        while r:
            l.append(r)
            r = self.GetNextResult(connID)
        return l
    
    
    
    
    
    def GetObjectIDAtIndex(self, imKey, index, connID='default'):
        '''
        Returns the true object ID of the nth object in an image.
        Note: This must be used when object IDs in the DB aren't
              contiguous starting at 1.
              (eg: if some objects have been removed)
        '''
        imNum = imKey[-1]
        if p.table_id:
            tblNum = imKey[0]
            self.Execute('SELECT %s FROM %s WHERE %s=%s AND %s=%s LIMIT %s,1'
                       %(p.object_id, p.object_table, p.table_id, tblNum, p.image_id, imNum, index-1))
            obNum = self.GetResultsAsList()
            obNum = obNum[0][0]
        else:
            self.Execute('SELECT %s FROM %s WHERE %s=%s LIMIT %s,1'
                       %(p.object_id, p.object_table, p.image_id, imNum, index-1))
            obNum = self.GetResultsAsList()
            obNum = obNum[0][0]
        return tuple(list(imKey)+[int(obNum)])

    
    
    def GetPerImageObjectCounts(self, connID='default'):
        ''' 
        Returns a list of (imKey, obCount) tuples. 
        '''
        select = "SELECT "+UniqueImageClause()+", COUNT("+p.object_id+") FROM "+str(p.object_table)+" GROUP BY "+UniqueImageClause()
        self.Execute(select, connID)
        return self.GetResultsAsList(connID)
    
    
    def GetAllImageKeys(self, connID='default'):
        ''' 
        Returns a list of all image keys in the image_table. 
        '''
        select = "SELECT "+UniqueImageClause()+" FROM "+p.image_table+" GROUP BY "+UniqueImageClause()
        self.Execute(select, connID)
        return self.GetResultsAsList(connID)
    
    
    def GetColumnNames(self, tableName, connID='default'):
        ''' 
        Returns a list of the column names for the specified table. 
        '''
        q = 'Describe '+tableName
        self.Execute(q, connID)
        #print self.GetResultsAsList(connID)
        return [x[0] for x in self.GetResultsAsList(connID)]
    
        
    # TODO: there should be a better way to get the grouping column names
    def GetResultColumnNames(self, connID='default'):
        ''' Returns the column names of the last query on this connection. '''
        return [x[0] for x in self.cursors[connID].description]
        
    
    def GetObjectCoords(self, obKey, connID='default'):
        ''' 
        Returns the specified object's x, y coordinates in an image. 
        '''
        select = 'SELECT '+p.cell_x_loc+', '+p.cell_y_loc+' FROM '+p.object_table+' WHERE '+GetWhereClauseForObjects([obKey])
        self.Execute(select, connID)
        res = self.GetResultsAsList(connID)
        assert len(res)==1, "ERROR <DBConnect.GetObjectCoords>: Returned %s objects instead of 1.\n" % len(res)
        return res[0]


    def GetObjectNear(self, imkey, x, y, connID='default'):
        ''' 
        Returns obKey of the closest object to x, y in an image.
        '''
        delta_x = p.cell_x_loc+' - %d'%(x)
        delta_y = p.cell_y_loc+' - %d'%(y)
        dist_clause = 'POW(%s, 2) + POW(%s, 2)'%(delta_x, delta_y)
        select = 'SELECT '+UniqueObjectClause()+' FROM '+p.object_table+' WHERE '+GetWhereClauseForImages([imkey])+' ORDER BY ' +dist_clause+' LIMIT 1'
        self.Execute(select, connID)
        res = self.GetResultsAsList(connID)
        if len(res) == 0:
            return None
        else:
            return res[0]
    
    
    def GetFullChannelPathsForImage(self, imKey, connID='default'):
        ''' 
        Returns a list of image channel filenames for a particular image
        including the absolute path.
        '''
        assert len(p.image_channel_paths) == len(p.image_channel_files), "Number of image_channel_paths and image_channel_files do not match!"
        
        nChannels = len(p.image_channel_paths)
        select = 'SELECT '
        for i in xrange(nChannels):
            select += p.image_channel_paths[i]+', '+p.image_channel_files[i]+', '
        select = select[:-2] # chop off the last ', '
        select += ' FROM '+p.image_table+' WHERE '+GetWhereClauseForImages([imKey])
        
        self.Execute(select, connID)
        imPaths = self.GetNextResult(connID)
        assert self.GetNextResult(connID) == None, "Query unexpectedly returned more than one result!\n\t"+select
        
        # parse filenames out of results
        filenames = []
        for i in xrange(0,len(p.image_channel_paths*2),2):
            filenames.append( imPaths[i]+'/'+imPaths[i+1] )
        return filenames
    
    
    def GetFilteredImages(self, filter, connID='default'):
        '''
        Returns a list of imKeys from the given filter.
        '''
        if 'filter_SQL_'+filter not in p.__dict__:
            raise DBException, 'ERROR <DBConnect.GetImagesInGroup>: The filter %s was not found in the properties file!' %(filter)
        
        self.Execute(p.__dict__['filter_SQL_'+filter], connID)
        return self.GetResultsAsList(connID)
    
    
    def GetColnamesForClassifier(self, connID='default'):
        '''
        Returns a list of column names for the object_table excluding 
        those specified in Properties.classifier_ignore_substrings
        '''
        if self.classifierColNames is None:
            self.Execute('DESCRIBE %s' % (p.object_table), connID)
            data = self.GetResultsAsList(connID)
            self.classifierColNames = [i[0] for i in data if not any([sub.lower() in i[0].lower() for sub in p.classifier_ignore_substrings])]
        return self.classifierColNames
    
    
    def GetCellDataForClassifier(self, obKey, connID='default'):
        '''
        Returns a list of measurements for the specified object excluding
        those specified in Properties.classifier_ignore_substrings
        '''
        if (self.classifierColNames == None):
            self.GetColnamesForClassifier()
        query = 'SELECT %s FROM %s WHERE %s' %(','.join(self.classifierColNames), p.object_table, GetWhereClauseForObjects([obKey]))
        self.Execute(query, connID, silent=True)
        data = self.GetResultsAsList(connID)
        if len(data) == 0:
            print 'ERROR <DBConnect.GetCellDataForClassifier>: No data for obKey:',obKey
        return numpy.array(data[0])
    
    
    
    
    def CreateSQLiteDB(self):
        '''
        When the user specifies csv files as tables, we create an SQLite DB
        from those tables and do everything else the same.
        '''
        import csv

        p.image_table = 'per_image'
        p.object_table = 'per_object'

        # CREATE THE IMAGE TABLE
        # All the ugly code is to establish the type of each column in the table
        # so we can form a proper CREATE TABLE statement.
        f = open(p.image_csv_file, 'r')
        r = csv.reader(f)
        columnLabels = r.next()
        columnLabels = [lbl.strip() for lbl in columnLabels]
        row = r.next()
        rowTypes = {}
        maxLen   = {}   # Maximum string length for each column (if VARCHAR)
        for i in xrange(len(columnLabels)):
            rowTypes[i] = ''
            maxLen[i] = 0 
        while row:
            for i, e in enumerate(row):
                if rowTypes[i]!='FLOAT' and not rowTypes[i].startswith('VARCHAR'):
                    try:
                        x = int(e)
                        rowTypes[i] = 'INT'
                        continue
                    except ValueError: pass
                if not rowTypes[i].startswith('VARCHAR'):
                    try:
                        x = float(e)
                        rowTypes[i] = 'FLOAT'
                        continue
                    except ValueError: pass
                try:
                    x = str(e)
                    maxLen[i] = max(len(x), maxLen[i])
                    rowTypes[i] = 'VARCHAR(%d)'%(maxLen[i])
                except ValueError: 
                    raise Exception, '<ERROR>: Value in table could not be converted to string!'
            try:
                row = r.next()
            except StopIteration: break
        
        # Build the CREATE TABLE statement
        statement = 'CREATE TABLE '+p.image_table+' ('
        statement += ',\n'.join([lbl+' '+rowTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
        
        self.Execute('DROP TABLE IF EXISTS test_per_image')
        # Create the image table
        self.Execute(statement)
        
        # CREATE THE OBJECT TABLE
        # For the object table we assume that all values are type FLOAT
        # except for the primary keys
        f = open(p.object_csv_file, 'r')
        r = csv.reader(f)
        columnLabels = r.next()
        columnLabels = [lbl.strip() for lbl in columnLabels]
        row = r.next()
        rowTypes = {}
        for i, lbl in enumerate(columnLabels):
            if lbl in [p.table_id, p.image_id, p.object_id]:
                rowTypes[i] = 'INT'
            else:
                rowTypes[i]='FLOAT'
        statement = 'CREATE TABLE '+p.object_table+' ('
        statement += ',\n'.join([lbl+' '+rowTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
    
        self.Execute('DROP TABLE IF EXISTS test_per_object')
        self.Execute(statement)
        
        # POPULATE THE IMAGE TABLE
        f = open(p.image_csv_file, 'r')
        r = csv.reader(f)
        row = r.next() # skip the headers
        row = r.next()
        while row: 
            self.Execute('INSERT INTO '+p.image_table+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')',
                         silent=True)
            try:
                row = r.next()
            except StopIteration:
                break
        f.close()
        
        # POPULATE THE OBJECT TABLE
        f = open(p.object_csv_file, 'r')
        r = csv.reader(f)
        row = r.next() # skip the headers
        row = r.next()
        while row: 
            self.Execute('INSERT INTO '+p.object_table+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')',
                         silent=True)
            try:
                row = r.next()
            except StopIteration:
                break
        f.close()
        
        self.Commit()

        
        



if __name__ == "__main__":
    p = Properties.getInstance()
    p.LoadFile('../properties/nirht_local.properties')
    db = DBConnect.getInstance()
    db.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
    
#    print db.GetColnamesForClassifier()
    print db.GetPerImageObjectCounts()
