'''
DBConnect.py
Authors: afraser
'''

import string
import numpy
import MySQLdb
from MySQLdb.cursors import SSCursor
import exceptions
from Singleton import Singleton
from Properties import Properties
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



class DBConnect(Singleton):
    ''' Wrapper for MySQLdb functions. '''
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


    def Disconnect(self):
        for conn in self.connections.values():
            conn.close()
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}
        self.classifierColNames = None
        
    
    def CloseConnection(self, connID):
        if connID in self.connections.keys():
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
    
    
    def GetResultColumnNames(self, connID='default'):
        ''' Returns the column names of the last query on this connection. '''
        return [x[0] for x in self.cursors[connID].description]
        
    
    def GetObjectCoords(self, obKey, connID='default'):
        ''' Queries the database for the specified object's coordinates. '''
        select = 'SELECT '+p.cell_x_loc+', '+p.cell_y_loc+' FROM '+p.object_table+' WHERE '+GetWhereClauseForObjects([obKey])
        self.Execute(select, connID)
        res = self.GetResultsAsList(connID)
        assert len(res)==1, "ERROR <DBConnect.GetObjectCoords>: Returned %s objects instead of 1.\n" % len(res)
        return res[0]

    def GetObjectNear(self, imkey, x, y, connID='default'):
        '''finds the closest object to x, y in an image'''
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
        ''' Queries the database for the image channel paths and filenames
        for a particular image. '''
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
        ''' Returns a list of imKeys from the given filter. '''
        
#        assert 'group_where_'+group in p.__dict__ and 'group_tables_'+group in p.__dict__, \
#                    'ERROR <DBConnect.GetImagesInGroup>: The group '+group+' was not found in the properties file!'            
#        where = p.__dict__['group_where_'+group]
#        tables = p.__dict__['group_tables_'+group]
#        query = "SELECT %s FROM %s WHERE %s" % (UniqueImageClause(), ','.join(tables), where)

        if 'filter_SQL_'+filter not in p.__dict__:
            raise DBException, 'ERROR <DBConnect.GetImagesInGroup>: The filter %s was not found in the properties file!' %(filter)
        
        self.Execute(p.__dict__['filter_SQL_'+filter], connID)
        return self.GetResultsAsList(connID)
    
    
    def GetColnamesForClassifier(self, connID='default'):
        if self.classifierColNames is None:
            self.Execute('DESCRIBE %s' % (p.object_table), connID)
            data = self.GetResultsAsList(connID)
            self.classifierColNames = [i[0] for i in data if not any([sub.lower() in i[0].lower() for sub in p.classifier_ignore_substrings])]
        return self.classifierColNames
    
    
    def GetCellDataForClassifier(self, obKey, connID='default'):
        if (self.classifierColNames == None):
            self.GetColnamesForClassifier()
        query = 'SELECT %s FROM %s WHERE %s' %(','.join(self.classifierColNames), p.object_table, GetWhereClauseForObjects([obKey]))
        self.Execute(query, connID, silent=True)
        data = self.GetResultsAsList(connID)
        if len(data) == 0:
            print 'ERROR <DBConnect.GetCellDataForClassifier>: No data for obKey:',obKey
        return numpy.array(data[0])
        


if __name__ == "__main__":
    ''' This allows us to use: python DBConnect.py -v
    to test all modules with a doctest string. '''
    p = Properties.getInstance()
    p.LoadFile('../properties/nirht.properties')
    db = DBConnect.getInstance()
#    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPur")
    
    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r")
    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r")
    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r", connID='test')
#    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r", connID='test')
#    db.CloseConnection('test')
#    db.CloseConnection('test')
#    db.CloseConnection('default')
#    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r", connID='test')
#    
#    db.Execute('SELECT ImageNumber FROM CPA_per_image LIMIT 10', 'test')
#    print db.GetResultsAsList()
#    print db.GetResultsAsList('test')
#    print db.GetResultsAsList('test')
#    
#    db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r")
#    
#    db.Execute('SELECT ImageNumber FROM CPA_per_image LIMIT 10', 'test')
#    db.Execute('SELECT ImageNumber FROM CPA_per_image LIMIT 10')
#    print db.GetResultsAsList()
#    print db.GetResultsAsList('test')    
    
    print db.GetObjectCoords((0,1,1))
    print db.GetResultColumnNames()
    print db.GetObjectCoords((0,1,1), 'test')
    print db.GetResultColumnNames()
    print db.GetObjectCoords((0,1,1))
    print db.GetResultColumnNames()

#    print GetWhereClauseForImages([key for key in db.GetImagesInGroup('EMPTY')[:5]])
#    print GetWhereClauseForObjects([list(key)+[0] for key in db.GetImagesInGroup('EMPTY')[:5]])
#    print db.GetImagesInGroup('EMPTY')[:10]
#    print db.GetImagesInGroup('CDKs')[:10]
#    print db.GetImagesInGroup('Accuracy75')[:10]
    
    
