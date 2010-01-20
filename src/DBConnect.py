import decimal
import types
import random
from MySQLdb.cursors import SSCursor
from Properties import Properties
from Singleton import Singleton
from sys import stderr
import MySQLdb
import exceptions
import numpy as np
import logging
import string
import sys
import threading
import traceback
import re
import os.path
import logging
import copy
# This module should be usable on systems without wx.

verbose = True

p = Properties.getInstance()
logr = logging.getLogger('DBConnect')

class DBException(Exception):
    def __str__(self):
        return 'ERROR: ' + self.args[0] + '\n'
# XXX: sys.traceback is only set when an exception is not handled
#      To test, enter an invalid image_channel_path column name in props file
#        filename, line_number, function_name, text = traceback.extract_tb(sys.last_traceback)[-1]
#        return "ERROR <%s>: "%(function_name) + self.args[0] + '\n'


#TODO: this doesn't belong in this module
def get_data_table_from_csv_reader(reader):
    '''reads a csv table into a 2d list'''
    dtable = []
    try:
        row = reader.next()
    except:
        return []
    while row:
        dtable += [row]
        try:
            row = reader.next()
        except StopIteration: break
    return dtable


def clean_up_colnames(colnames):
    '''takes a list of column names and makes them so they
    don't have to be quoted in sql syntax'''
    colnames = [col.replace(' ','_') for col in colnames]
    colnames = [col.replace('\n','_') for col in colnames]
    colnames = [filter(lambda c: re.match('[A-Za-z0-9_]',c), col) for col in colnames]
    return colnames        


def well_key_columns(table_name=''):
    '''Return, as a tuple, the names of the columns that make up the
    well key.  If table_name is not None, use it to qualify each
    column name.'''
    if table_name is None:
        table_name = ''
    if table_name != '':
        table_name += '.'
    if p.plate_id and p.well_id:
        return (table_name+p.plate_id, table_name+p.well_id)
    else:
        return tuple()

def image_key_columns(table_name=''):
    '''Return, as a tuple, the names of the columns that make up the
    image key.  If table_name is not None, use it to qualify each
    column name.'''
    if table_name is None:
        table_name = ''
    if table_name != '':
        table_name += '.'
    if p.table_id:
        return (table_name+p.table_id, table_name+p.image_id)
    else:
        return (table_name+p.image_id,)

def object_key_columns(table_name=''):
    '''Return, as a tuple, the names of the columns that make up the
    object key.'''
    if table_name is None:
        table_name = ''
    if table_name != '':
        table_name += '.'
    if p.table_id:
        return (table_name+p.table_id, table_name+p.image_id, table_name+p.object_id)
    else:
        return (table_name+p.image_id, table_name+p.object_id)

def object_key_defs():
    return ', '.join(['%s INT'%(id) for id in object_key_columns()])

def GetWhereClauseForObjects(obkeys):
    '''
    Return a SQL WHERE clause that matches any of the given object keys.
    Example: GetWhereClauseForObjects([(1, 3), (2, 4)]) => "ImageNumber=1 
             AND ObjectNumber=3 OR ImageNumber=2 AND ObjectNumber=4"
    '''
    return '(' + ' OR '.join([' AND '.join([col + '=' + str(value)
              for col, value in zip(object_key_columns(), obkey)])
              for obkey in obkeys]) + ')'

def GetWhereClauseForImages(imkeys):
    '''
    Return a SQL WHERE clause that matches any of the give image keys.
    Example: GetWhereClauseForImages([(3,), (4,)]) => 
             "(ImageNumber IN (3, 4))"
    '''
    imkeys.sort()
    if not p.table_id:
        return '%s IN (%s)'%(p.image_id, ','.join([str(k[0]) for k in imkeys]))
    else:
        imkeys = np.array(imkeys)
        count = 0
        tnum = 0
        wheres = []
        while count<len(imkeys):
            imnums = imkeys[(imkeys[:,0]==tnum), 1]
            count += len(imnums)
            if len(imnums)>0:
                wheres += ['(%s=%s AND %s IN (%s))'%(p.table_id, tnum, 
                            p.image_id, ','.join([str(k) for k in imnums]))]
            tnum += 1
        return ' OR '.join(wheres)

def UniqueObjectClause(table_name=None):
    '''
    Returns a clause for specifying a unique object in MySQL.
    Example: "SELECT "+UniqueObjectClause()+" FROM <mydb>;" would return all object keys
    '''
    return ','.join(object_key_columns(table_name))

def UniqueImageClause(table_name=None):
    '''
    Returns a clause for specifying a unique image in MySQL.
    Example: "SELECT <UniqueObjectClause()> FROM <mydb>;" would return all image keys 
    '''
    return ','.join(image_key_columns(table_name))

def get_csv_filenames_from_sql_file():
    '''
    Get the image and object CSVs specified in the .SQL file
    '''
    f = open(p.db_sql_file)
    lines = f.read()
    f.close()
    files = re.findall(r" '\w+\.[Cc][Ss][Vv]' ",lines)
    files = [f[2:-2] for f in files]
    imcsvs = [] 
    obcsvs = []
    for file in files:
        if file.lower().endswith('image.csv'):
            imcsvs += [file]
        elif file.lower().endswith('object.csv'):
            obcsvs += [file]
    return imcsvs, obcsvs


class SqliteClassifier():
    def __init__(self):
        pass

    def setup_classifier(self, thresholds, a, b):
        self.thresholds = thresholds
        self.a = a.T
        self.b = b.T

    def classify(self, *features):
        return 1 + np.where((features > self.thresholds), self.a, self.b).sum(axis=1).argmax()


class DBConnect(Singleton):
    '''
    DBConnect abstracts calls to MySQLdb. It is a singleton that maintains 
    unique connections for each thread that uses it.  These connections are 
    automatically created on "execute", and results are automatically returned
    as a list.
    '''
    def __init__(self):
        self.classifierColNames = None
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}
        # link_cols['table'] = columns that link 'table' to the per-image table
        self.link_cols = {}
        self.sqlite_classifier = SqliteClassifier()
        self.gui_parent = None

    def __str__(self):
        return string.join([ (key + " = " + str(val) + "\n")
                            for (key, val) in self.__dict__.items()])


    def connect(self):
        '''
        Attempts to create a new connection to the specified database using
          the current thread name as a connection ID.
        If properties.db_type is 'sqlite', it will create a sqlite db in a
          temporary directory from the csv files specified by
          properties.image_csv_file and properties.object_csv_file
        '''
        connID = threading.currentThread().getName()
        
        logr.info('[%s] Connecting to the database...'%(connID))
        # If this connection ID already exists print a warning
        if connID in self.connections.keys():
            if self.connectionInfo[connID] == (p.db_host, p.db_user, 
                                               p.db_passwd, p.db_name):
                logr.warn('A connection already exists for this thread. %s as %s@%s (connID = "%s").'%(p.db_name, p.db_user, p.db_host, connID))
            else:
                raise DBException, 'A connection already exists for this thread (%s). Close this connection first.'%(connID,)

        # MySQL database: connect normally
        if p.db_type.lower() == 'mysql':
            try:
                conn = MySQLdb.connect(host=p.db_host, db=p.db_name, 
                                       user=p.db_user, passwd=p.db_passwd)
                self.connections[connID] = conn
                self.cursors[connID] = SSCursor(conn)
                self.connectionInfo[connID] = (p.db_host, p.db_user, 
                                               p.db_passwd, p.db_name)
                logr.debug('[%s] Connected to database: %s as %s@%s'%(connID, p.db_name, p.db_user, p.db_host))
            except MySQLdb.Error, e:
                raise DBException, 'Failed to connect to database: %s as %s@%s (connID = "%s").\n  %s'%(p.db_name, p.db_user, p.db_host, connID, e)
            
        # SQLite database: create database from CSVs
        elif p.db_type.lower() == 'sqlite':
            from pysqlite2 import dbapi2 as sqlite
            
            if not p.db_sqlite_file:
                # Compute a UNIQUE database name for these files
                import md5
                dbpath = os.getenv('USERPROFILE') or os.getenv('HOMEPATH') or \
                    os.path.expanduser('~')
                dbpath = os.path.join(dbpath,'CPA')
                try:
                    os.listdir(dbpath)
                except OSError:
                    os.mkdir(dbpath)
                if p.db_sql_file:
                    csv_dir = os.path.split(p.db_sql_file)[0]
                    imcsvs, obcsvs = get_csv_filenames_from_sql_file()
                    files = imcsvs + obcsvs + [os.path.split(p.db_sql_file)[1]]
                    hash = md5.new()
                    for fname in files:
                        t = os.stat(csv_dir + os.path.sep + fname).st_mtime
                        hash.update('%s%s'%(fname,t))
                    dbname = 'CPA_DB_%s.db'%(hash.hexdigest())
                else:
                    imtime = os.stat(p.image_csv_file).st_mtime
                    obtime = os.stat(p.object_csv_file).st_mtime
                    l = '%s%s%s%s'%(p.image_csv_file,p.object_csv_file,imtime,obtime)
                    dbname = 'CPA_DB_%s.db'%(md5.md5(l).hexdigest())
                    
                p.db_sqlite_file = os.path.join(dbpath, dbname)
            logr.info('[%s] SQLite file: %s'%(connID, p.db_sqlite_file))
            self.connections[connID] = sqlite.connect(p.db_sqlite_file)
            self.connections[connID].text_factory = str
            self.cursors[connID] = self.connections[connID].cursor()
            self.connectionInfo[connID] = ('sqlite', 'cpa_user', '', 'CPA_DB')
            self.connections[connID].create_function('greatest', -1, max)
            # Create MEDIAN function
            class median:
                def __init__(self):
                    self.reset()
                def reset(self):
                    self.values = []
                def step(self, val):
                    if not np.isnan(float(val)):
                        self.values.append(float(val))
                def finalize(self):
                    self.values.sort()
                    n = len(self.values)
                    if n%2 == 1:
                        return self.values[n//2]
                    else:
                        return (self.values[n//2-1] + self.values[n//2])/2
            self.connections[connID].create_aggregate('median', 1, median)
            # Create STDDEV function
            class stddev:
                def __init__(self):
                    self.reset()
                def reset(self):
                    self.values = []
                def step(self, val):
                    if not np.isnan(float(val)):
                        self.values.append(float(val))
                def finalize(self):
                    avg = np.mean(self.values)
                    b = np.sum([(x-avg)**2 for x in self.values])
                    std = np.sqrt(b/len(self.values))
                    return std
            self.connections[connID].create_aggregate('stddev', 1, stddev)
            self.connections[connID].create_function('classifier', -1, self.sqlite_classifier.classify)
            
            try:
                # Try the connection
                self.GetAllImageKeys()
            except Exception:
                # If this is the first connection, then we need to create the DB from the csv files
                if len(self.connections) == 1:
                    if p.db_sql_file:
                        # TODO: prompt user "create db, y/n"
                        logr.info('[%s] Creating SQLite database at: %s.'%(connID, p.db_sqlite_file))
                        try:
                            self.CreateSQLiteDBFromCSVs()
                        except Exception, e:
                            try:
                                if os.path.isfile(p.db_sqlite_file):
                                    os.remove(p.db_sqlite_file)
                            except:
                                pass
                            raise e
                    elif p.image_csv_file and p.object_csv_file:
                        # TODO: prompt user "create db, y/n"
                        logr.info('[%s] Creating SQLite database at: %s.'%(connID, p.db_sqlite_file))
                        self.CreateSQLiteDB()
                    else:
                        raise DBException, 'Database at %s appears to be empty.'%(p.db_sqlite_file)
            logr.debug('[%s] Connected to database: %s'%(connID, p.db_sqlite_file))
        # Unknown database type (this should never happen)
        else:
            raise DBException, "Unknown db_type in properties: '%s'\n"%(p.db_type)

    def setup_sqlite_classifier(self, thresh, a, b):
        self.sqlite_classifier.setup_classifier(thresh, a, b)

    def Disconnect(self):
        for connID in self.connections.keys():
            self.CloseConnection(connID)
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}
        self.classifierColNames = None
        
    
    def CloseConnection(self, connID=None):
        if not connID:
            connID = threading.currentThread().getName()
        if connID in self.connections.keys():
            try:
                self.connections[connID].commit()
            except: pass
            self.cursors.pop(connID)
            self.connections.pop(connID).close()
            (db_host, db_user, db_passwd, db_name) = self.connectionInfo.pop(connID)
            logr.info('Closed connection: %s as %s@%s (connID="%s").' % (db_name, db_user, db_host, connID))
        else:
            logr.warn('WARNING <DBConnect.CloseConnection>: No connection ID "%s" found!' %(connID))


    def execute(self, query, args=None, silent=False, return_result=True):
        '''
        Executes the given query using the connection associated with
        the current thread.  Returns the results as a list of rows
        unless return_result is false.
        '''
        # Grab a new connection if this is a new thread
        connID = threading.currentThread().getName()
        if not connID in self.connections.keys():
            self.connect()
        
        # Test for lost connection
        try:
            self.connections[connID].ping()
        except MySQLdb.OperationalError, e:
            logr.error('Lost connection to database. Attempting to reconnect...')
            self.CloseConnection(connID)
            self.connect()
        except AttributeError:
            pass # SQLite doesn't know ping.
        
        # Finally make the query
        try:
            if verbose and not silent: 
                logr.debug('[%s] %s'%(connID, query))
            if p.db_type.lower()=='sqlite':
                if args:
                    raise 'Can\'t pass args to sqlite execute!'
                self.cursors[connID].execute(query)
            else:
                self.cursors[connID].execute(query, args=args)
            if return_result:
                return self._get_results_as_list()
        except MySQLdb.Error, e:
            raise DBException, 'Database query failed for connection "%s"\n\t%s\n\t%s\n' %(connID, query, e)
        except KeyError, e:
            raise DBException, 'No such connection: "%s".\n' %(connID)
            
            
    def Commit(self):
        connID = threading.currentThread().getName()
        try:
            logr.debug('[%s] Commit'%(connID))
            self.connections[connID].commit()
        except MySQLdb.Error, e:
            raise DBException, 'Commit failed for connection "%s"\n\t%s\n' %(connID, e)
        except KeyError, e:
            raise DBException, 'No such connection: "%s".\n' %(connID)
            

    def GetNextResult(self):
        connID = threading.currentThread().getName()
        try:
            return self.cursors[connID].next()
        except MySQLdb.Error, e:
            raise DBException, \
                'Error retrieving next result from database: %s'%(e,)
            return None
        except StopIteration, e:
            return None
        except KeyError, e:
            raise DBException, 'No such connection: "%s".\n' %(connID)

    def _get_results_as_list(self):
        '''
        Returns a list of results retrieved from the last execute query.
        NOTE: this function automatically called by execute.
        '''
        connID = threading.currentThread().getName()
        return list(self.cursors[connID].fetchall())

    def result_dtype(self):
        """
        Return an appropriate descriptor for a numpy array in which the
        result can be stored.
        """
        #XXX: This doesn't work for SQLite... no cursor.description_flags
        cursor = self.cursors[threading.currentThread().getName()]
        descr = []
        for (name, type_code, display_size, internal_size, precision, 
             scale, null_ok), flags in zip(cursor.description, 
                                           cursor.description_flags):
            conversion = cursor.connection.converter[type_code]
            if isinstance(conversion, list):
                fun2 = None
                for mask, fun in conversion:
                    fun2 = fun
                    if mask & flags:
                        break
            else:
                fun2 = conversion
            if fun2 in [decimal.Decimal, types.FloatType]:
                dtype = 'f8'
            elif fun2 in [types.IntType, types.LongType]:
                dtype = 'i4'
            elif fun2 in [types.StringType]:
                dtype = '|S%d'%(internal_size,)
            descr.append((name, dtype))
        return descr

    def get_results_as_structured_array(self, n=None):
        #XXX: this doesn't work for SQLite
        col_names = self.GetResultColumnNames()
        connID = threading.currentThread().getName()
        if n is None:
            records = self.cursors[connID].fetchall()
        else:
            records = self.cursors[connID].fetchmany(n)
            if len(records) == 0:
                return None
        return np.array(list(records), dtype=self.result_dtype())
    
    def GetObjectIDAtIndex(self, imKey, index):
        '''
        Returns the true object ID of the nth object in an image.
        Note: This must be used when object IDs in the DB aren't
              contiguous starting at 1.
              (eg: if some objects have been removed)
        index: a POSITIVE integer (1,2,3...)
        '''
        where_clause = " AND ".join(['%s=%s'%(col, val) for col, val in zip(image_key_columns(), imKey)])
        object_number = self.execute('SELECT %s FROM %s WHERE %s LIMIT %s,1'
                                     %(p.object_id, p.object_table, where_clause, index - 1))
        object_number = object_number[0][0]
        return tuple(list(imKey)+[int(object_number)])
    
    
    def GetPerImageObjectCounts(self):
        '''
        Returns a list of (imKey, obCount) tuples. 
        The counts returned correspond to images that are present in BOTH the 
        per_image and per_object table.
        '''
        select = 'SELECT '+UniqueImageClause(p.object_table)+', COUNT('+p.object_table+'.'+p.object_id + ') FROM '+p.object_table + ' GROUP BY '+UniqueImageClause(p.object_table)
        result1 = self.execute(select)
        select = 'SELECT '+UniqueImageClause(p.image_table)+' FROM '+p.image_table
        result2 = self.execute(select)

        counts = {}
        for r in result1:
            counts[r[:-1]] = r[-1]
        return [r+(counts[r],) for r in result2 if r in counts]
    
    
    def GetAllImageKeys(self):
        ''' Returns a list of all image keys in the image_table. '''
        select = "SELECT "+UniqueImageClause()+" FROM "+p.image_table+" GROUP BY "+UniqueImageClause()
        return self.execute(select)
    
    
    def GetObjectsFromImage(self, imKey):
        return self.execute('SELECT %s FROM %s WHERE %s'%(UniqueObjectClause(), p.object_table, GetWhereClauseForImages([imKey])))
    
    
    def GetObjectCoords(self, obKey, none_ok=False, silent=False):
        ''' Returns the specified object's x, y coordinates in an image. '''
        select = 'SELECT '+p.cell_x_loc+', '+p.cell_y_loc+' FROM '+p.object_table+' WHERE '+GetWhereClauseForObjects([obKey])
        res = self.execute(select, silent=silent)
        if none_ok and len(res) == 0:
            return None
        assert len(res)>0, "Couldn't find object coordinates for object key %s." %(obKey,) 
        assert len(res)==1, "Database unexpectedly returned %s sets of object coordinates instead of 1." % len(res)
        return res[0]
    
    
    def GetAllObjectCoordsFromImage(self, imKey):
        ''' Returns a list of lists x, y coordinates for all objects in the given image. '''
        select = 'SELECT '+p.cell_x_loc+', '+p.cell_y_loc+' FROM '+p.object_table+' WHERE '+GetWhereClauseForImages([imKey])+' ORDER BY '+p.object_id
        return self.execute(select)


    def GetObjectNear(self, imkey, x, y, silent=False):
        ''' Returns obKey of the closest object to x, y in an image. '''
        delta_x = '(%s - %d)'%(p.cell_x_loc, x)
        delta_y = '(%s - %d)'%(p.cell_y_loc, y)
        dist_clause = '%s*%s + %s*%s'%(delta_x, delta_x, delta_y, delta_y)
        select = 'SELECT '+UniqueObjectClause()+' FROM '+p.object_table+' WHERE '+GetWhereClauseForImages([imkey])+' ORDER BY ' +dist_clause+' LIMIT 1'
        res = self.execute(select, silent=silent)
        if len(res) == 0:
            return None
        else:
            return res[0]
    
    
    def GetFullChannelPathsForImage(self, imKey):
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
        imPaths = self.execute(select)[0]
        # parse filenames out of results
        filenames = []
        for i in xrange(0,len(p.image_channel_paths*2),2):
            if p.image_url_prepend:
                filenames.append( imPaths[i]+'/'+imPaths[i+1] )
            else:
                filenames.append( imPaths[i]+os.path.sep+imPaths[i+1] )
        return filenames


    def GetGroupMaps(self, reverse=False):
        '''Return a tuple of two dictionaries: one that maps group
        names to group maps and one that maps group names to lists of
        column names. If reverse is set to true, the group maps will
        map group keys to image keys instead of vice-versa.'''
        groupColNames = {}
        groupMaps = {}
        for group in p._groups:
            groupMaps[group], groupColNames[group] = self.group_map(group, reverse=reverse)
        return groupMaps, groupColNames

    def group_map(self, group, reverse=False):
        """Return a tuple of (1) a dictionary mapping image keys to
        group keys and (2) a list of column names for the group
        keys. If reverse is set to true, the dictionary will map
        group keys to image keys instead."""
        key_size = p.table_id and 2 or 1
        query = p._groups[group]
        try:
            res = self.execute(query)
        except Exception, e:
            raise Exception, 'Group query failed for group "%s". Check the MySQL syntax in your properties file.\nError was: "%s"'%(group, e)
        col_names = self.GetResultColumnNames()[key_size:]
        d = {}
        for row in res:
            if reverse:
                d[row[key_size:]] = []
        for row in res:
            if reverse:
                d[row[key_size:]] += [row[:key_size]]
            else:
                d[row[:key_size]] = row[key_size:]
        return d, col_names
    
    
    def GetFilteredImages(self, filter):
        ''' Returns a list of imKeys from the given filter. '''
        try:
            return self.execute(p._filters[filter])
        except Exception, e:
            logr.error('Filter query failed for filter "%s". Check the MySQL syntax in your properties file.'%(filter))
            logr.error(e)
            raise Exception, 'Filter query failed for filter "%s". Check the MySQL syntax in your properties file.'%(filter)
    
    
    def GetTableNames(self):
        if p.db_type.lower()=='mysql':
            res = self.execute('SHOW TABLES')
            return [t[0] for t in res]
        elif p.db_type.lower()=='sqlite':
            res = self.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
            return [t[0] for t in res]

    
    def GetColumnNames(self, table):
        ''' Returns a list of the column names for the specified table. '''
        # NOTE: SQLite doesn't like DESCRIBE or SHOW statements so we do it this way.
        self.execute('SELECT * FROM %s LIMIT 1'%(table))
        return self.GetResultColumnNames()   # return the column names
            

    def GetColumnTypes(self, table):
        ''' Returns the column types for the given table. '''
        res = self.execute('SELECT * FROM %s LIMIT 1'%(table), silent=True)
        return [type(x) for x in res[0]]


    def GetColnamesForClassifier(self):
        '''
        Returns a list of column names for the object_table excluding 
        those specified in Properties.classifier_ignore_columns
        '''
        if self.classifierColNames is None:
            col_names = self.GetColumnNames(p.object_table)
            col_types = self.GetColumnTypes(p.object_table)
            # automatically ignore all string-type columns
            self.classifierColNames = [col for col, type in zip(col_names, col_types) if type!=str]
            # automatically ignore ID columns
            if p.table_id:
                self.classifierColNames.remove(p.table_id)
            self.classifierColNames.remove(p.image_id)
            self.classifierColNames.remove(p.object_id)
            # treat each classifier_ignore_substring as a regular expression
            # for column names to ignore
            if p.classifier_ignore_columns:
                self.classifierColNames = [col for col in self.classifierColNames
                                                if not any([re.match('^'+user_exp+'$',col)
                                                       for user_exp in p.classifier_ignore_columns])]
            logr.info('Ignoring columns: %s'%([x for x in col_names if x not in self.classifierColNames]))
        return self.classifierColNames
    
    
    def GetResultColumnNames(self):
        ''' Returns the column names of the last query on this connection. '''
        connID = threading.currentThread().getName()
        return [x[0] for x in self.cursors[connID].description]
    
    
    def GetCellDataForClassifier(self, obKey):
        '''
        Returns a list of measurements for the specified object excluding
        those specified in Properties.classifier_ignore_columns
        '''
        if (self.classifierColNames == None):
            self.GetColnamesForClassifier()
        query = 'SELECT %s FROM %s WHERE %s' %(','.join(self.classifierColNames), p.object_table, GetWhereClauseForObjects([obKey]))
        data = self.execute(query, silent=True)
        if len(data) == 0:
            logr.error('No data for obKey: %s'%str(obKey))
            return None
        return np.array(data[0])
    
    
    def GetCellData(self, obKey):
        '''
        Returns a list of measurements for the specified object.
        '''
        query = 'SELECT * FROM %s WHERE %s' %(p.object_table, GetWhereClauseForObjects([obKey]))
        data = self.execute(query, silent=True)
        if len(data) == 0:
            logr.error('No data for obKey: %s'%str(obKey))
            return None
        return np.array(data[0])

    
    def GetPlateNames(self):
        '''
        Returns the names of each plate in the per-image table.
        '''
        res = self.execute('SELECT %s FROM %s GROUP BY %s'%(p.plate_id, p.image_table, p.plate_id))
        return [str(l[0]) for l in res]


    def GetPlatesAndWellsPerImage(self):
        '''
        Returns rows containing image key, plate, and well
        '''
        if p.plate_id and p.well_id:
            return self.execute('SELECT %s, %s FROM %s'%(UniqueImageClause(), ','.join(well_key_columns()), p.image_table))
        else:
            logging.error('Both plate_id and well_id must be defined in properties!')
    
    def get_platewell_for_object(self, key):
        if p.plate_id and p.well_id:
            return self.execute('SELECT %s FROM %s WHERE %s'%(','.join(well_key_columns()), p.image_table, GetWhereClauseForImages([key[:-1]])))[0]
        else:
            return key[:-1]
    
    def InferColTypesFromData(self, tabledata, nCols):
        '''
        For converting csv data to DB data.
        Returns a list of column types (INT, FLOAT, or VARCHAR(#)) that each column can safely be converted to
        tabledata: 2d iterable of strings
        nCols: # of columns  
        '''
        colTypes = ['' for i in xrange(nCols)]
        # Maximum string length for each column (if VARCHAR)
        maxLen   = [0 for i in xrange(nCols)] 
        try:
            tabledata[0][0]
        except: 
            raise Exception('asdf ERROR: Cannot infer column types from an empty table.')
        for row in tabledata:
            for i, e in enumerate(row):
                if colTypes[i]!='FLOAT' and not colTypes[i].startswith('VARCHAR'):
                    try:
                        x = int(str(e))
                        colTypes[i] = 'INT'
                        continue
                    except ValueError: pass
                if not colTypes[i].startswith('VARCHAR'):
                    try:
                        x = float(str(e))
                        colTypes[i] = 'FLOAT'
                        continue
                    except ValueError: pass
                try:
                    x = str(e)
                    maxLen[i] = max(len(x), maxLen[i])
                    colTypes[i] = 'VARCHAR(%d)'%(maxLen[i])
                except ValueError: 
                    raise Exception, '<ERROR>: Value in table could not be converted to string!'
        return colTypes
    
     
    def GetLinkingColumnsForTable(self, table):
        ''' Returns the column(s) that link the given table to the per_image table. '''
        if table not in self.link_cols.keys():
            cols = self.GetColumnNames(table)
            imkey = image_key_columns()
            if all([kcol in cols for kcol in imkey]):
                self.link_cols[table] = imkey
            elif p.well_id in cols and p.plate_id in cols:
                self.link_cols[table] = (p.well_id, p.plate_id)
            else:
                raise Exception('Table %s could not be linked to %s'%(table, p.image_table))
        return self.link_cols[table]       
    
    
    def CreateSQLiteDB(self):
        '''
        Creates an SQLite database from files specified in properties
        image_csv_file and object_csv_file.
        '''
        import csv
        # CREATE THE IMAGE TABLE
        # All the ugly code is to establish the type of each column in the table
        # so we can form a proper CREATE TABLE statement.
        f = open(p.image_csv_file, 'U')
        r = csv.reader(f)
        columnLabels = r.next()
        columnLabels = [lbl.strip() for lbl in columnLabels]
        dtable = get_data_table_from_csv_reader(r)
        colTypes = self.InferColTypesFromData(dtable, len(columnLabels))
        
        # Build the CREATE TABLE statement
        statement = 'CREATE TABLE '+p.image_table+' ('
        statement += ',\n'.join([lbl+' '+colTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
        
        logr.info('Creating table: %s'%(p.image_table))
        self.execute('DROP TABLE IF EXISTS %s'%(p.image_table))
        self.execute(statement)
        
        # CREATE THE OBJECT TABLE
        # For the object table we assume that all values are type FLOAT
        # except for the primary keys
        f = open(p.object_csv_file, 'U')
        r = csv.reader(f)
        columnLabels = r.next()
        columnLabels = [lbl.strip() for lbl in columnLabels]
        dtable = get_data_table_from_csv_reader(r)
        colTypes = self.InferColTypesFromData(dtable, len(columnLabels))
        statement = 'CREATE TABLE '+p.object_table+' ('
        statement += ',\n'.join([lbl+' '+colTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
    
        logr.info('Creating table: %s'%(p.object_table))
        self.execute('DROP TABLE IF EXISTS '+p.object_table)
        self.execute(statement)
        
        # POPULATE THE IMAGE TABLE
        f = open(p.image_csv_file, 'U')
        r = csv.reader(f)
        row = r.next() # skip the headers
        row = r.next()
        while row: 
            self.execute('INSERT INTO '+p.image_table+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')',
                         silent=True)
            try:
                row = r.next()
            except StopIteration:
                break
        f.close()
        
        # POPULATE THE OBJECT TABLE
        f = open(p.object_csv_file, 'U')
        r = csv.reader(f)
        row = r.next() # skip the headers
        row = r.next()
        while row: 
            self.execute('INSERT INTO '+p.object_table+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')',
                         silent=True)
            try:
                row = r.next()
            except StopIteration: break
        f.close()
        
        self.Commit()
        
        
    def CreateSQLiteDBFromCSVs(self):
        '''
        Creates an SQLite database from files generated by CellProfiler's
        ExportToDatabase module.
        '''
        import csv
        
        imcsvs, obcsvs = get_csv_filenames_from_sql_file()
                
        # Verify that the CSVs exist
        csv_dir = os.path.split(p.db_sql_file)[0]
        dir_files = os.listdir(csv_dir)
        print dir_files
        for file in imcsvs + obcsvs:
            print file
            assert file in dir_files, ('File "%s" was specified in %s but was '
                                      'not found in %s.'%(file, os.path.split(p.db_sql_file)[1], csv_dir))
        assert len(imcsvs)>0, ('Failed to parse image csv filenames from %s. '
                              'Make sure db_sql_file in your properties file is'
                              ' set to the .SQL file output by CellProfiler\'s '
                              'ExportToDatabase module.'%(os.path.split(p.db_sql_file)[1]))
        assert len(obcsvs)>0, ('Failed to parse object csv filenames from %s. '
                              'Make sure db_sql_file in your properties file is'
                              ' set to the .SQL file output by CellProfiler\'s '
                              'ExportToDatabase module.'%(os.path.split(p.db_sql_file)[1]))
        
        # parse out create table statements and execute them
        f = open(p.db_sql_file)
        lines = f.readlines()
        create_stmts = []
        i=0
        in_create_stmt = False
        for l in lines:
            if l.upper().startswith('CREATE TABLE') or in_create_stmt:
                if in_create_stmt:
                    create_stmts[i] += l
                else:
                    create_stmts.append(l)
                if l.strip().endswith(';'):
                    in_create_stmt = False
                    i+=1
                else:
                    in_create_stmt = True
        f.close()
        
        for q in create_stmts:
            self.execute(q)
        
        if self.gui_parent is not None and issubclass(gui_parent.__class__, wx.Window):
            import wx
            dlg = wx.ProgressDialog('Creating sqlite DB...', '0% Complete', 100, self.gui_parent, wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT)
        else:
            dlg = None

        # find the number of bytes we're going to read
        total_bytes = 0
        for file in imcsvs + obcsvs:
            total_bytes += os.path.getsize(os.path.join(csv_dir, file))
        total_bytes = float(total_bytes)

        base_bytes = 0
        connID = threading.currentThread().getName()
        # populate tables with contents of csv files
        for file in imcsvs:
            logr.info('Populating image table with data from %s'%file)
            f = open(os.path.join(csv_dir, file), 'U')
            r = csv.reader(f)
            row1 = r.next()
            command = 'INSERT INTO '+p.image_table+' VALUES ('+','.join(['?' for i in row1])+')'
            self.cursors[connID].execute(command, row1)
            self.cursors[connID].executemany(command, [l for l in r if len(l)>0])
            self.Commit()
            f.close()
            base_bytes += os.path.getsize(os.path.join(csv_dir, file))
            pct = min(int(100 * base_bytes / total_bytes), 100)
            if dlg:
                c, s = dlg.Update(pct, '%d%% Complete'%(pct))
                if not c:
                    raise Exception('cancelled load')
            logr.info("... loaded %d%% of CSV data"%(pct))

        line_count = 0
        for file in obcsvs:
            logr.info('Populating object table with data from %s'%file)
            f = open(csv_dir+os.path.sep+file, 'U')
            r = csv.reader(f)
            row1 = r.next()
            command = 'INSERT INTO '+p.object_table+' VALUES ('+','.join(['?' for i in row1])+')'
            # guess at a good number of lines, about 250 megabytes, assuming floats)
            nlines = (250*1024*1024) / (len(row1) * 64)
            self.cursors[connID].execute(command, row1)
            while True:
                # fetch a certain number of lines efficiently
                args = [l for idx, l in zip(range(nlines), r) if len(l) > 0]
                if args == []:
                    break
                self.cursors[connID].executemany(command, args)
                self.Commit()
                line_count += len(args)

                pct = min(int(100 * (f.tell() + base_bytes) / total_bytes), 100)
                if dlg:
                    c, s = dlg.Update(pct, '%d%% Complete'%(pct))
                    if not c:
                        raise Exception('cancelled load')
                logr.info("... loaded %d%% of CSV data"%(pct))
            f.close()
            base_bytes += os.path.getsize(os.path.join(csv_dir, file))

        if dlg:
            dlg.Destroy()

    def table_exists(self, name):
        res = []
        if p.db_type.lower() == 'mysql':
            res = self.execute("SELECT table_name FROM information_schema.tables WHERE table_name='%s' AND table_schema='%s'"%(name, p.db_name))
        else:
            res = self.execute("SELECT name FROM sqlite_master WHERE type='table' and name='%s'"%(name))
        return len(res) > 0


    def CreateTempTableFromCSV(self, filename, tablename):
        '''
        Reads a csv file into a temporary table in the database.
        Column names are taken from the first row.
        Column types are inferred from the data.
        '''
        import csv
        f = open(filename, 'U')
        r = csv.reader(f)
        self.execute('DROP TABLE IF EXISTS %s'%(tablename))
        colnames = r.next()
        dtable = np.array(get_data_table_from_csv_reader(r))
        typed_table = []
        for i in xrange(dtable.shape[1]):
            try:
                col = np.array(dtable[:,i], dtype=str)
                col = np.array(dtable[:,i], dtype=float)
                col = np.array(dtable[:,i], dtype=int) 
            except:
                pass
            typed_table += [col]
        typed_table = np.array(typed_table, dtype=object).T
        return self.CreateTempTableFromData(typed_table, colnames, tablename)
    
    
    def CreateTempTableFromData(self, dtable, colnames, tablename):
        '''
        Creates and populates a temporary table in the database.
        Column names are taken from the first row.
        Column types are inferred from the data.
        '''
        self.execute('DROP TABLE IF EXISTS %s'%(tablename))
        # Clean up column names
        colnames = clean_up_colnames(colnames)
        # Infer column types
        coltypes = self.InferColTypesFromData(dtable, len(colnames))
        coldefs = ', '.join([lbl+' '+coltypes[i] for i, lbl in enumerate(colnames)])
        self.execute('CREATE TEMPORARY TABLE %s (%s)'%(tablename, coldefs))
        for key in list(well_key_columns()) + list(image_key_columns()):
            if key in colnames:
                self.execute('CREATE INDEX %s ON %s (%s)'%('%s_%s'%(tablename,key), tablename, key))
        logr.info('Populating temporary table %s...'%(tablename))
        for row in dtable:
            vals = []
            for i, val in enumerate(row):
                if coltypes[i]=='FLOAT' and (np.isinf(val) or np.isnan(val)):
                    vals += ['NULL']
                else:
                    vals += ['"%s"'%val]
            vals = ', '.join(vals)
            self.execute('INSERT INTO %s (%s) VALUES (%s)'%(
                          tablename, ', '.join(colnames), vals), silent=True)
        self.Commit()
        return True
    
    
    def CheckTables(self):
        '''
        Queries the DB to check that the per_image and per_object
        tables agree on image numbers.
        '''
        if p.db_type=='sqlite':
            logr.warn('Skipping table checking step for sqlite')
            return

        logr.info('Checking database tables...')
        # Check for index on image_table
        res = self.execute('SHOW INDEX FROM %s'%(p.image_table))
        idx_cols = [r[4] for r in res]
        for col in image_key_columns():
            assert col in idx_cols, 'Column "%s" is not indexed in table "%s"'%(col, p.image_table)

        # Explicitly check for TableNumber in case it was not specified in props file
        if not p.object_table and 'TableNumber' in idx_cols:
            raise 'Indexed column "TableNumber" was found in the database but not in your properties file.'
        
        # STOP here if there is no object table
        if not p.object_table:
            return
        
        # Check for index on object_table
        res = self.execute('SHOW INDEX FROM %s'%(p.object_table))
        idx_cols = [r[4] for r in res]
        for col in object_key_columns():
            assert col in idx_cols, 'Column "%s" is not indexed in table "%s"'%(col, p.object_table)
        
        # Explicitly check for TableNumber in case it was not specified in props file
        if ('TableNumber' not in object_key_columns()) and ('TableNumber' in idx_cols):
            raise 'Indexed column "TableNumber" was found in the database but not in your properties file.'
        elif ('TableNumber' in idx_cols):
            logr.warn('TableNumber column was found indexed in your image table but not your object table.')
        elif ('TableNumber' not in object_key_columns()):
            logr.warn('TableNumber column was found indexed in your object table but not your image table.')
        
        # Removed because it doesn't work (ignores TableNumber), and is slow.
        #
        # # Check for orphaned objects
        # obims = [(c[0]) for c in self.execute('SELECT %s, COUNT(*)  FROM %s GROUP BY %s'%(p.image_id, p.object_table, p.image_id))]
        # imims = self.execute('SELECT %s FROM %s'%(p.image_id, p.image_table))
        # orphans = set(obims) - set(imims)
        # assert not orphans, 'Objects were found in "%s" that had no corresponding image key in "%s"'%(p.object_table, p.image_table)
        
        # Check for unlabeled wells
        if p.well_id:
            res = self.execute('SELECT %s FROM %s WHERE %s IS NULL OR %s=""'%(UniqueImageClause(), p.image_table, p.well_id, p.well_id))
            if any(res):
                logr.warn('WARNING: Images were found in "%s" that had a NULL or empty "%s" column value'%(p.image_table, p.well_id))
        
        # Check for unlabeled plates
        if p.plate_id:
            res = self.execute('SELECT %s FROM %s WHERE %s IS NULL OR %s=""'%(UniqueImageClause(), p.image_table, p.plate_id, p.plate_id))
            if any(res):
                logr.warn('WARNING: Images were found in "%s" that had a NULL or empty "%s" column value'%(p.image_table, p.plate_id))
        logr.info('Done checking database tables.')

    def histogram(self, column, table_or_query, nbins, range=None):
        """
        Compute a 1-D histogram entirely in the database.
        column          -- a single column name, as a string
        table_or_query  -- either a table name or a subquery, as a string
        nbins           -- the number of desired bins in the histogram
        range           -- the lower and upper range of the bins

        Returns (hist, bin_edges), where hist is a numpy array of size
        nbins and bin_edges is a numpy array of size nbins + 1.
        """
        if ' ' in table_or_query:
            table_clause = "(%s) as foo"%(query,)
        else:
            table_clause = table_or_query

        if range is None:
            data = self.execute("select min(%s), max(%s) from %s" %
                                (column, column, table_clause))
            min = data[0][0]
            max = data[0][1]
        else:
            min, max = range
            
        clause = ("round(%d * (%s - (%f)) / (%f - (%f)))" % 
                  (nbins, column, min, max, min))
        h = np.zeros(nbins)
        res = self.execute("select %s as bin, count(*) from %s "
                           "where %s <= %d "
                           "group by %s order by bin" % (clause, table_clause,
                                                         clause, nbins, clause))
        for bin, count in res:
            if bin == nbins:
                bin -= 1
            h[bin] = count
        return h, np.linspace(min, max, nbins + 1)

    def get_objects_modify_date(self):
        if p.db_type.lower() == 'mysql':
            return self.execute("select UPDATE_TIME from INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='%s' and TABLE_SCHEMA='%s'"%(p.object_table, p.db_name))[0][0]
        else:
            return os.path.getmtime(p.db_sqlite_file)

    def verify_objects_modify_date_earlier(self, later):
        cur = self.get_objects_modify_date()
        return self.get_objects_modify_date() <= later

    def register_gui_parent(self, parent):
        self.gui_parent = parent

class Entity(object):
    """Abstract class containing code that is common to Images and
    Objects.  Do not instantiate directly."""

    class dbiter(object):

        def __init__(self, objects, db):
            self.length = objects.count()
            self.db = db
            self.db.execute(objects.all_query(), return_result=False)
            self.columns = self.db.GetResultColumnNames()

        def __iter__(self):
            return self

        def __len__(self):
            return self.length

        def structured_array(self):
            return self.db.get_results_as_structured_array()

        def sample(self, n):
            """
            Arguments:
            n -- a non-negative integer or None

            If n is None or n >= length, return all results.
            """
            list = self.db._get_results_as_list()
            n = min(n, len(self))
            return random.sample(list, n)

        def next(self):
            try:
                r = self.db.GetNextResult()
                if r:
                    return r
                else:
                    raise StopIteration
            except GeneratorExit:
                print "GeneratorExit"
                self.db.cursors[connID].fetchall()
                

    def __init__(self):
        self._where = []
        self.filters = []
        self._offset = None
        self._limit = None

    def offset(self, offset):
        new = copy.deepcopy(self)
        new._offset = (0 if new._offset is None else new._offset) + offset
        return new

    def limit(self, limit):
        new = copy.deepcopy(self)
        new._limit = limit
        return new

    def filter(self, name):
        """Add a filter (as defined in the properties file) by name."""
        new = copy.deepcopy(self)
        new.filters.append(name)
        return new

    def where(self, predicate):
        new = copy.deepcopy(self)
        new._where.append(predicate)
        return new

    def _get_where_clause(self):
        return "" if self._where == [] else "where " + \
            " and ".join(self._where)
    where_clause = property(_get_where_clause)

    def count(self):
        c = DBConnect.getInstance().execute(self.all_query(columns=["count(*)"]))[0][0]
        c = max(0, c - (self._offset or 0))
        c = max(c, self._limit or 0)
        return c

    def all(self):
        return self.dbiter(self, DBConnect.getInstance())

    def all_query(self, columns=None):
        return "select %s from %s %s %s %s" % (
            ",".join(columns or self.columns()),
            self.from_clause,
            self.where_clause,
            self.ordering_clause,
            self.offset_limit_clause)


class Union(Entity):
    def __init__(self, *args):
        super(Union, self).__init__()
        self.operands = args

    def all_query(self, *args, **kwargs):
        return " UNION ".join([e.all_query(*args, **kwargs) 
                               for e in self.operands])


class Images(Entity):
    '''
    Easy access to images and their objects.

    # Get all objects treated with 10 uM nocodazole
    >>> cpa.DBConnect.Images().filter(compound_name).where("cast(Image_LoadedText_Platemap as decimal) = 10").objects()
    '''

    def __init__(self):
        super(Images, self).__init__()

    def _get_from_clause(self):
        from_clause = [Properties.getInstance().image_table]
        for filter in self.filters:
            from_clause.append("join (%s) as %s using (%s)" %
                               (Properties.getInstance()._filters[filter],
                                'filter_SQL_' + filter,
                                ", ".join(image_key_columns())))
        return " ".join(from_clause)
    from_clause = property(_get_from_clause)

    def objects(self):
        if self._offset is not None or self._limit is not None:
            raise ValueError, "Cannot join with objects after applying "\
                "offset/limit."
        return Objects(images=self)


class Objects(Entity):
    '''
    Easy access to objects.

    >>> feature = "Cells_NumberNeighbors_SecondClosestDistance"
    >>> y = [row[0] for row in Objects().ordering([feature]).project([feature]).all()]
    '''

    def __init__(self, images=None):
        super(Objects, self).__init__()
        self._columns = None
        self._ordering = None
        if images is None:
            self._images = None
        else:
            self._images = images
            self._where = images._where
            self.filters = images.filters

    def ordering(self, ordering):
        new = copy.deepcopy(self)
        new._ordering = ordering
        return new

    def project(self, columns):
        new = copy.deepcopy(self)
        new._columns = columns
        return new

    def _get_from_clause(self):
        from_clause = [Properties.getInstance().object_table]
        if self._images is not None:
            from_clause.append("join %s using (%s)"%
                               (Properties.getInstance().image_table,
                                ", ".join(image_key_columns())))
        for filter in self.filters:
            from_clause.append("join (%s) as %s using (%s)" %
                               (Properties.getInstance()._filters[filter],
                                'filter_SQL_' + filter,
                                ", ".join(image_key_columns())))
        return " ".join(from_clause)
    from_clause = property(_get_from_clause)

    def _get_offset_limit_clause(self):
        return " ".join((self._limit and ["limit %d" % self._limit] or []) +
                        (self._offset and ["offset %d" % self._offset] or []))
    offset_limit_clause = property(_get_offset_limit_clause)

    def _get_ordering_clause(self):
        if self._ordering is None:
            return ""
        else:
            return "order by " + ", ".join(self._ordering)
    ordering_clause = property(_get_ordering_clause)

    def columns(self):
        return self._columns or list(object_key_columns()) + \
            DBConnect.getInstance().GetColnamesForClassifier()

    def standard_deviations(self):
        """Returns a list of the standard deviations of the non-key columns.
        Offsets and limits are ignored here, not sure if they should be."""
        db = DBConnect.getInstance()
        return db.execute("select %s from %s %s"%(
                ",".join(["std(%s)" % c 
                          for c in db.GetColnamesForClassifier()]),
                self.from_clause, self.where_clause))[0]

    def __add__(self, other):
        return Union(self, other)


if __name__ == "__main__":

    from TrainingSet import TrainingSet
    import FastGentleBoostingMulticlass
    import MulticlassSQL
    from cStringIO import StringIO
    from DataModel import DataModel
    
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    
    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()

#    p.LoadFile('../properties/Gilliland_LeukemiaScreens_Validation.properties')
#    p.LoadFile('../properties/nirht_test.properties')
    p.LoadFile('../test_data/export_to_db_test.properties')
#    p.LoadFile('../test_data/nirht_local.properties')
    
    dm.PopulateModel()

    print '%s images'%len(db.GetAllImageKeys())
    
    # TEST CreateTempTableFromCSV
#    table = '_blah'
#    db.CreateTempTableFromCSV('../test_data/test_per_image.txt', table)
#    print db.execute('SELECT * from %s LIMIT 10'%(table))
#
#    measurements = db.GetColumnNames(table)
#    types = db.GetColumnTypes(table)
#    print [m for m,t in zip(measurements, types) if t in[float, int, long]]
#
#    print db.GetColumnNames(table)
#    print db.GetColumnTypes(table)


    # TEST reconnect
#    import time
#    print db.GetColnamesForClassifier()
#    while(1):
#        print '#'
#        if sys.stdin.readline().strip() == 'q':
#            break
#        try:
#            print db.GetColumnTypes(p.object_table)
#        except:
#            print 'ERROR: query failed.  Try again'
        
    
#    p.LoadFile('../properties/nirht_local.properties')
#    dm.PopulateModel()
#    
#    print 'group maps:',db.GetGroupMaps()
#    print 'filter "firstten":',db.GetFilteredImages('FirstTen')
#    
#    # Train the classifier
#    imKey = (0,1)
#    nRules = 5
#    trainingSet = TrainingSet(p)
#    # make a training set
#    positives = [(0,1,56), (0,1,72), (0,1,92), (0,1,90), (0,1,88), (0,1,49), (0,1,11)]
#    negatives = [(0,1,i) for i in range(1,95) if i not in [56,72,92,90,88,49,11]]
#    trainingSet.Create(['pos','neg'],[positives, negatives])
#    output = StringIO()
#    print 'Training classifier with '+str(nRules)+' rules...'
#    weaklearners = FastGentleBoostingMulticlass.train(trainingSet.colnames, nRules,
#                                                      trainingSet.label_matrix, 
#                                                      trainingSet.values, output)
#
#    obKeys = dm.GetObjectsFromImage(imKey)
##    imKeysInFilter = db.GetFilteredImages('FirstHundred')
##    obKeys = dm.GetRandomObjects(100,imKeysInFilter)
#    hits = []
#    if obKeys:
#        clNum = 1
#        hits = MulticlassSQL.FilterObjectsFromClassN(clNum, weaklearners, [imKey])
#        
#    print hits
