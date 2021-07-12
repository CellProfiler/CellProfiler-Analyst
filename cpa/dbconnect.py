
import decimal
import random
from .properties import Properties
from .singleton import Singleton
import numpy as np
import sys
import threading
import re
import os.path
import logging
import copy
# This module should be usable on systems without wx.

verbose = True

p = Properties()

class DBException(Exception):
    def __str__(self):
        return 'ERROR: ' + self.args[0] + '\n'
# XXX: sys.traceback is only set when an exception is not handled
#      To test, enter an invalid image_channel_path column name in props file
#        filename, line_number, function_name, text = traceback.extract_tb(sys.last_traceback)[-1]
#        return "ERROR <%s>: "%(function_name) + self.args[0] + '\n'


def DBError():
    '''returns the Error type associated with the db library in use'''
    if p.db_type.lower() == 'mysql':
        import MySQLdb
        return MySQLdb.Error
    elif p.db_type.lower() == 'sqlite':
        import sqlite3
        return sqlite3.Error
    
def DBOperationalError():
    '''returns the Error type associated with the db library in use'''
    if p.db_type.lower() == 'mysql':
        import MySQLdb
        return MySQLdb.OperationalError
    elif p.db_type.lower() == 'sqlite':
        import sqlite3
        return sqlite3.OperationalError


class DBDisconnectedException(Exception):
    """
    Raised when a query or other database operation fails because the
    database is shutting down or the connection has been lost.
    """
    def with_mysql_retry(cls, f):
        """
        Decorator that tries calling its function a second time if a
        DBDisconnectedException occurs the first time.
        """
        def fn(db, *args, **kwargs):
            try:
                return f(db, *args, **kwargs)
            except DBDisconnectedException:
                logging.info('Lost connection to the MySQL database; reconnecting.')
                db.connect()
                return f(db, *args, **kwargs)
        return fn
    with_mysql_retry = classmethod(with_mysql_retry)

def sqltype_to_pythontype(t):
    '''
    t -- a valid sql typestring
    returns a python type that will hold the given sqltype
    '''
    t = t.upper()
    if (t.startswith('INT') or t.startswith('DECIMAL') or t.startswith('BIGINT') or
        t in ['TINYINT', 'SMALLINT', 'MEDIUMINT', 'UNSIGNED BIG INT', 
              'INT2', 'INT8', 'NUMERIC', 'BOOLEAN', 'DATE', 'DATETIME']):
        return int
    elif t in ['REAL', 'DOUBLE', 'DOUBLE PRECISION', 'FLOAT']:
        return float
    elif (t.startswith('CHARACTER') or t.startswith('VARCHAR') or t.startswith('CHAR') or
          t.startswith('VARYING CHARACTER') or t.startswith('NCHAR') or 
          t.startswith('NCHAR') or t.startswith('NATIVE CHARACTER') or
          t.startswith('NVARCHAR') or t in ['TEXT', 'CLOB']):
        return str
    
#TODO: this doesn't belong in this module
def get_data_table_from_csv_reader(reader):
    '''reads a csv table into a 2d list'''
    dtable = []
    try:
        row = next(reader)
    except:
        return []
    while row:
        dtable += [row]
        try:
            row = next(reader)
        except StopIteration: break
    return dtable


def clean_up_colnames(colnames):
    '''takes a list of column names and makes them so they
    don't have to be quoted in sql syntax'''
    colnames = [col.replace(' ','_') for col in colnames]
    colnames = [col.replace('\n','_') for col in colnames]
    colnames = [''.join([c for c in col if re.match('[A-Za-z0-9_]',c)]) for col in colnames]
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
    elif p.well_id:
        return (table_name+p.well_id, )
    else:
        return None

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
    assert p.object_table is not None
    if table_name is None:
        table_name = ''
    if table_name != '':
        table_name += '.'
    object_id = '' if not (p.object_id and p.object_table) else p.object_id
    if p.table_id:
        return (table_name+p.table_id, table_name+p.image_id, table_name+object_id)
    else:
        return (table_name+p.image_id, table_name+object_id)

def object_key_defs():
    return ', '.join(['%s INT'%(id) for id in object_key_columns()])

def GetWhereClauseForObjects(obkeys, table_name=None):
    '''
    Return a SQL WHERE clause that matches any of the given object keys.
    Example: GetWhereClauseForObjects([(1, 3), (2, 4)]) => "ImageNumber=1 
             AND ObjectNumber=3 OR ImageNumber=2 AND ObjectNumber=4"
    '''
    if table_name is None:
        table_name = ''
    # To limit the depth of this expression, we split it into a binary tree.
    # This helps avoid SQLITE_MAX_LIMIT_EXPR_DEPTH
    def split(keys,table_name):
        if len(keys) <= 3:
            return '(' + ' OR '.join([' AND '.join([col + '=' + str(value)
                                                    for col, value in zip(object_key_columns(table_name), obkey)])
                                      for obkey in keys]) + ')'
        else:
            halflen = len(keys) // 2
            return '(' + split(keys[:halflen],table_name) + ' OR ' + split(keys[halflen:],table_name) + ')'

    return split(obkeys,table_name)

def GetWhereClauseForImages(imkeys):
    '''
    Return a SQL WHERE clause that matches any of the given image keys.
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
        while count < len(imkeys):
            imnums = imkeys[(imkeys[:,0]==tnum), 1]
            count += len(imnums)
            if len(imnums)>0:
                wheres += ['(%s=%s AND %s IN (%s))'%(p.table_id, tnum, 
                            p.image_id, ','.join([str(k) for k in imnums]))]
            tnum += 1
        return ' OR '.join(wheres)

def GetWhereClauseForWells(keys, table_name=None):
    '''
    Return a SQL WHERE clause that matches any of the given well keys.
    Example: GetWhereClauseForImages([('plate1', 'A01'), ('plate1', 'A02')]) => 
             "(plate="plate1" AND well="A01" OR plate="plate1" AND "A02"))"
    '''
    if table_name is None:
        table_name = ''
    else:
        table_name += '.'
    keys.sort()
    if not p.plate_id:
        return '%s%s IN (%s)'%(table_name, p.well_id, ','.join(['"%s"'%(k[0]) for k in keys]))
    else:
        wheres = ['%s%s="%s" AND %s%s="%s"'%(table_name, p.plate_id, plate, table_name, p.well_id, well) for plate, well in keys]
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

def UniqueWellClause(table_name=None):
    '''
    Returns a clause for specifying a unique image in MySQL.
    Example: "SELECT <UniqueObjectClause()> FROM <mydb>;" would return all image keys 
    '''
    return ','.join(well_key_columns(table_name))

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
        features = [0 if f is None else f for f in features]
        class_num = 1 + np.where((features > self.thresholds), self.a, self.b).sum(axis=1).argmax()
        # CRUCIAL: must make sure class_num is an int or it won't compare
        #          properly with the class being looked for and nothing will
        #          be found. This only appears to be a problem on Windows 64bit
        return int(class_num)


def _check_colname_user(properties, table, colname):
    if table in [properties.image_table, properties.object_table] and not colname.lower().startswith('user_'):
        raise ValueError('User-defined columns in the image and object tables must have names beginning with "User_".')

    
class DBConnect(metaclass=Singleton):
    '''
    DBConnect abstracts calls to MySQLdb/SQLite. It's a singleton that maintains
    unique connections for each thread that uses it.  These connections are 
    automatically created on "execute", and results are automatically returned
    as a list.
    '''
    def __init__(self):
        self.classifierColNames = None
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}
        #self.link_cols = {}  # link_cols['table'] = columns that link 'table' to the per-image table
        self.sqlite_classifier = SqliteClassifier()
        self.gui_parent = None

    def __str__(self):
        return ''.join([ (key + " = " + str(val) + "\n")
                            for (key, val) in list(self.__dict__.items())])
            
    def connect(self, empty_sqlite_db=False):
        '''
        Attempts to create a new connection to the specified database using
          the current thread name as a connection ID.
        If properties.db_type is 'sqlite', it will create a sqlite db in a
          temporary directory from the csv files specified by
          properties.image_csv_file and properties.object_csv_file
        '''
        connID = threading.currentThread().getName()
        
        logging.info('[%s] Connecting to the database...'%(connID))
        # If this connection ID already exists print a warning
        if connID in self.connections:
            if self.connectionInfo[connID] == (p.db_host, p.db_user, 
                                               (p.db_passwd or None), p.db_name):
                logging.warn('A connection already exists for this thread. %s as %s@%s (connID = "%s").'%(p.db_name, p.db_user, p.db_host, connID))
            else:
                raise DBException('A connection already exists for this thread (%s). Close this connection first.'%(connID,))

        # MySQL database: connect normally
        if p.db_type.lower() == 'mysql':
            import MySQLdb
            from MySQLdb.cursors import SSCursor
            try:
                conn = MySQLdb.connect(host=p.db_host, db=p.db_name, 
                                       user=p.db_user, passwd=(p.db_passwd or None))
                self.connections[connID] = conn
                self.cursors[connID] = SSCursor(conn)
                self.connectionInfo[connID] = (p.db_host, p.db_user, 
                                               (p.db_passwd or None), p.db_name)
                logging.debug('[%s] Connected to database: %s as %s@%s'%(connID, p.db_name, p.db_user, p.db_host))
                if connID == 'MainThread':
                    if p.classification_type == 'image':
                        self.CreateObjectImageTable()
                    if p.check_tables == 'yes':
                        self.CreateObjectCheckedTable()
            except DBError() as e:
                raise DBException('Failed to connect to database: %s as %s@%s (connID = "%s").\n  %s'%(p.db_name, p.db_user, p.db_host, connID, e))
            
        # SQLite database: create database from CSVs
        elif p.db_type.lower() == 'sqlite':
            import sqlite3 as sqlite
            
            if not p.db_sqlite_file:
                # Compute a UNIQUE database name for these files
                import hashlib
                dbpath = os.getenv('USERPROFILE') or os.getenv('HOMEPATH') or \
                    os.path.expanduser('~')
                dbpath = os.path.join(dbpath,'CPA')
                try:
                    os.listdir(dbpath)
                except OSError:
                    os.mkdir(dbpath)
                if p.db_sql_file:
                    csv_dir = os.path.split(p.db_sql_file)[0] or '.'
                    imcsvs, obcsvs = get_csv_filenames_from_sql_file()
                    files = imcsvs + obcsvs + [os.path.split(p.db_sql_file)[1]]
                    hash = hashlib.new('md5')
                    for fname in files:
                        t = os.stat(csv_dir + os.path.sep + fname).st_mtime
                        hash_me = f"{fname}{t}".encode()
                        hash.update(hash_me)
                    dbname = 'CPA_DB_%s.db'%(hash.hexdigest())
                else:
                    imtime = os.stat(p.image_csv_file).st_mtime
                    obtime = os.stat(p.object_csv_file).st_mtime
                    l = '%s%s%s%s'%(p.image_csv_file,p.object_csv_file,imtime,obtime)
                    dbname = 'CPA_DB_%s.db'%(hashlib.md5(l.encode()).hexdigest())
                    
                p.db_sqlite_file = os.path.join(dbpath, dbname)
            logging.info('[%s] SQLite file: %s'%(connID, p.db_sqlite_file))
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
                    if val is not None:
                        if not np.isnan(float(val)):
                            self.values.append(float(val))
                def finalize(self):
                    n = len(self.values)
                    if n == 0:
                        return None
                    self.values.sort()
                    if n%2 == 1:
                        return self.values[n//2]
                    else:
                        return (self.values[n//2-1] + self.values[n//2]) / 2
            self.connections[connID].create_aggregate('median', 1, median)
            # Create STDDEV function
            class stddev:
                def __init__(self):
                    self.reset()
                def reset(self):
                    self.values = []
                def step(self, val):
                    if val is not None:
                        if not np.isnan(float(val)):
                            self.values.append(float(val))
                def finalize(self):
                    if len(self.values) == 0:
                        return None
                    avg = np.mean(self.values)
                    b = np.sum([(x-avg)**2 for x in self.values])
                    std = np.sqrt(b/len(self.values))
                    return std
            self.connections[connID].create_aggregate('stddev', 1, stddev)
            # Create REGEXP function
            def regexp(expr, item):
                reg = re.compile(expr)
                return reg.match(item) is not None
            self.connections[connID].create_function("REGEXP", 2, regexp)
            # Create classifier function
            self.connections[connID].create_function('classifier', -1, self.sqlite_classifier.classify)
            
            try:
                # Try the connection
                if empty_sqlite_db:
                    self.execute('select 1')
                else:
                    self.GetAllImageKeys()
            except Exception:
                # If this is the first connection, then we need to create the DB from the csv files
                if len(self.connections) == 1:
                    if p.db_sql_file:
                        # TODO: prompt user "create db, y/n"
                        logging.info('[%s] Creating SQLite database at: %s.'%(connID, p.db_sqlite_file))
                        try:
                            self.CreateSQLiteDBFromCSVs()
                        except Exception as e:
                            try:
                                if os.path.isfile(p.db_sqlite_file):
                                    os.remove(p.db_sqlite_file)
                            except:
                                pass
                            raise e
                    elif p.image_csv_file and p.object_csv_file:
                        # TODO: prompt user "create db, y/n"
                        logging.info('[%s] Creating SQLite database at: %s.'%(connID, p.db_sqlite_file))
                        self.CreateSQLiteDB()
                    else:
                        raise DBException('Database at %s appears to be missing specified tables.'%(p.db_sqlite_file))
            # If we're not on the main thread these tables should already have been made.
            if p.classification_type == 'image' and connID == "MainThread":
                self.CreateObjectImageTable()
            if p.check_tables == 'yes' and connID == "MainThread":
                self.CreateObjectCheckedTable()
            logging.debug('[%s] Connected to database: %s'%(connID, p.db_sqlite_file))

        # Unknown database type (this should never happen)
        else:
            raise DBException("Unknown db_type in properties: '%s'\n"%(p.db_type))

    def setup_sqlite_classifier(self, thresh, a, b):
        self.sqlite_classifier.setup_classifier(thresh, a, b)

    def Disconnect(self):
        for connID in list(self.connections.keys()):
            self.CloseConnection(connID)
        self.connections = {}
        self.cursors = {}
        self.connectionInfo = {}
        self.classifierColNames = None
    
    def CloseConnection(self, connID=None):
        if not connID:
            connID = threading.currentThread().getName()
        if connID in self.connections:
            try:
                self.connections[connID].commit()
            except: pass
            self.cursors.pop(connID)
            self.connections.pop(connID).close()
            (db_host, db_user, db_passwd, db_name) = self.connectionInfo.pop(connID)
            logging.info('Closed connection: %s as %s@%s (connID="%s").' % (db_name, db_user, db_host, connID))
        else:
            logging.warn('No database connection ID "%s" found!' %(connID))

    @DBDisconnectedException.with_mysql_retry
    def execute(self, query, args=None, silent=False, return_result=True):
        '''
        Executes the given query using the connection associated with
        the current thread.  Returns the results as a list of rows
        unless return_result is false.
        '''
        if p.db_type.lower() == 'sqlite':
            if args:
                raise TypeError('Can\'t pass args to sqlite execute!')

        # Grab a new connection if this is a new thread
        connID = threading.currentThread().getName()
        if not connID in self.connections:
            self.connect()

        try:
            cursor = self.cursors[connID]
        except KeyError as e:
            raise DBException('No such connection: "%s".\n' %(connID))
        
        # Finally make the query
        try:
            if verbose and not silent: 
                logging.debug('[%s] %s'%(connID, query))
            if p.db_type.lower() == 'sqlite':
                assert args is None
                cursor.execute(query)
            else:
                cursor.execute(query, args=args)
            if return_result:
                return self._get_results_as_list()
        except Exception as e:
            try:
                if isinstance(e, DBOperationalError()) and e.args[0] in [2006, 2013, 1053]:
                    raise DBDisconnectedException()
                else:
                    raise DBException('Database query failed for connection "%s"'
                                     '\nQuery was: "%s"'
                                     '\nException was: %s'%(connID, query, e))
            except Exception as e2:
                raise DBException('Database query failed for connection "%s" and failed to reconnect'
                                  '\nQuery was: "%s"'
                                  '\nFirst exception was: %s'
                                  '\nSecond exception was: %s'%(connID, query, e, e2))
            
    def Commit(self):
        connID = threading.currentThread().getName()
        try:
            logging.debug('[%s] Commit'%(connID))
            self.connections[connID].commit()
        except DBError() as e:
            raise DBException('Commit failed for connection "%s"\n\t%s\n' %(connID, e))
        except KeyError as e:
            raise DBException('No such connection: "%s".\n' %(connID))

    def GetNextResult(self):
        connID = threading.currentThread().getName()
        try:
            return next(self.cursors[connID])
        except DBError() as e:
            raise DBException('Error retrieving next result from database: %s'%(e,))
            return None
        except StopIteration as e:
            return None
        except KeyError as e:
            raise DBException('No such connection: "%s".\n' %(connID))

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
            if fun2 in [decimal.Decimal, float]:
                dtype = 'f8'
            elif fun2 == int:
                dtype = 'i4'
            elif fun2 == bytes:
                dtype = '|S%d'%(internal_size,)
            descr.append((name, dtype))
        return descr

    def get_results_as_structured_array(self, n=None):
        #XXX: this doesn't work for SQLite
        col_names = self.GetResultColumnNames()
        connID = threading.currentThread().getName()
        records = []
        while True:
            r = self.cursors[connID].fetchmany(n)
            if len(r) == 0:
                break
            records.extend(list(r))
        return np.array(records, dtype=self.result_dtype())
    
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

    def GetRandomObjectsSQL(self, imKeys, N):
        '''
        Returns a random sampling of object keys from the database.
        Sampling occurs without replacement.
        imKeys: a list of image keys to sample objects from.
        N: number of keys to sample
        '''
        rand = "RANDOM()" if p.db_type.lower() == 'sqlite' else "RAND()"
        if not imKeys:
            statement = f"SELECT {p.image_id}, {p.object_id} FROM {p.object_table} ORDER BY {rand} LIMIT {N}"

        else:
            where_clause = GetWhereClauseForImages(imKeys)
            statement = f"SELECT {p.image_id}, {p.object_id} FROM {p.object_table} WHERE  {where_clause} ORDER BY {rand} LIMIT {N}"
        object_numbers = self.execute(statement)
        return object_numbers

    def GetAllObjectsSQL(self, imKeys, N=None):
        '''
        Returns objects from a list of keys in order.
        imkeys: a list of image keys
        N: integer representing the number of objects to fetch.
        '''
        if N is None:
            limit_clause = ""
        else:
            limit_clause = f" LIMIT {N}"
        if not imKeys:
            statement = f"SELECT {p.image_id}, {p.object_id} FROM {p.object_table} ORDER BY {p.image_id}{limit_clause}"
        else:
            where_clause = GetWhereClauseForImages(imKeys)
            statement = f"SELECT {p.image_id}, {p.object_id} FROM {p.object_table} WHERE {where_clause} ORDER BY {p.image_id}{limit_clause}"
        object_numbers = self.execute(statement)
        return object_numbers

    def GetPerImageObjectCounts(self):
        '''
        Returns a list of (imKey, obCount) tuples. 
        The counts returned correspond to images that are present in BOTH the 
        per_image and per_object table.
        '''
        if p.object_table is None or p.object_id is None:
            return []

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
        '''Returns the specified object's x, y coordinates in an image.
        '''
        res = self.execute('SELECT %s, %s FROM %s WHERE %s'%(
                        p.cell_x_loc, p.cell_y_loc, p.object_table, 
                        GetWhereClauseForObjects([obKey])), silent=silent)
        if len(res) == 0 or res[0][0] is None or res[0][1] is None:
            message = ('Failed to load coordinates for object key %s. This may '
                       'indicate a problem with your per-object table.\n'
                       'You can check your per-object table "%s" in TableViewer'
                       %(', '.join(['%s:%s'%(col, val) for col, val in 
                                    zip(object_key_columns(), obKey)]), 
                       p.object_table))
            raise Exception(message)
        else:
            return res[0]

    def GetObjectsCoords(self, obKeys, none_ok=False, silent=False):
        '''Returns the specified objects' x, y coordinates in an image.
        '''
        res = self.execute('SELECT %s, %s, %s, %s FROM %s WHERE %s'%(
                        p.image_id, p.object_id, p.cell_x_loc, p.cell_y_loc, p.object_table,
                        GetWhereClauseForObjects(obKeys)), silent=silent)
        if len(res) == 0 or res[0][0] is None or res[0][1] is None:
            message = ('Failed to load coordinates for object key %s. This may '
                       'indicate a problem with your per-object table.\n'
                       'You can check your per-object table "%s" in TableViewer'
                       %(', '.join(['%s:%s'%(col, val) for col, val in
                                    zip(object_key_columns(), obKeys)]),
                       p.object_table))
            raise Exception(message)
        else:
            # Now we need to match the returned lines to the requested keys
            res_dict = {}
            buffer = []
            for tup in res:
                res_dict[(tup[0], tup[1])] = (tup[2], tup[3])
            for key in obKeys:
                buffer.append(res_dict[key])
            return buffer
    
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
        assert len(p.image_path_cols) == len(p.image_file_cols), "Number of image_path_cols and image_file_cols do not match!"
        
        nChannels = len(p.image_path_cols)
        select = 'SELECT '
        for i in range(nChannels):
            select += p.image_path_cols[i]+', '+p.image_file_cols[i]+', '
        select = select[:-2] # chop off the last ', '
        select += ' FROM '+p.image_table+' WHERE '+GetWhereClauseForImages([imKey])
        imPaths = self.execute(select)[0]
        # parse filenames out of results
        filenames = []
        for i in range(0,len(p.image_path_cols*2),2):
            if p.image_url_prepend:
                filenames.append( imPaths[i]+'/'+imPaths[i+1] )
            else:
                filenames.append( os.path.join(imPaths[i],imPaths[i+1]) )
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

    def group_map(self, group, reverse=False, filter=None):
        """
        Return a tuple of (1) a dictionary mapping image keys to
        group keys and (2) a list of column names for the group
        keys. 

        If reverse is set to true, the dictionary will map
        group keys to image keys instead.

        """
        key_size = p.table_id and 2 or 1
        query = p._groups[group]
        from_idx = re.search('\sFROM\s', query.upper()).start()
        try:
            where_idx = re.search('\sWHERE\s', query.upper()).start()
        except AttributeError:
            where_idx = len(query)

        if filter:
            join_clause = ' JOIN (%s) as f USING (%s)' % (self.filter_sql(filter),
                                                          ','.join(image_key_columns()))
            query = query[:where_idx] + join_clause + query[where_idx:]
        try:
            res = self.execute(query)
        except DBException as e:
            raise DBException('Group query failed for group "%s". Check the SQL'
                              ' syntax in your properties file.\n'
                              'Error was: "%s"'%(group, e))
        
        col_names = self.GetResultColumnNames()[key_size:]
        from_clause = query[from_idx+6 : where_idx].strip()
        if ',' not in from_clause and ' ' not in from_clause:
            col_names = ['%s.%s'%(from_clause, col) for col in col_names]
        else:
            for table in from_clause.split(','):
                if re.search('\sAS\s', table.upper()) or ' ' in table.strip():
                    raise Exception('Unable to parse group query for group named "%s". '
                                    'This could be because you are using table aliases '
                                    'in your FROM clause. Please try rewriting your '
                                    'query without aliases and try again.'%(group))
            col_names = [col.strip() for col in query[7 : from_idx].split(',')][len(image_key_columns()):]

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
    
    def filter_sql(self, filter_name):
        f = p._filters[filter_name]
        from . import sqltools
        if isinstance(f, sqltools.Filter):
            unique_tables = np.unique(f.get_tables())
            if len(unique_tables) > 1:
                if p.image_table in unique_tables:
                    select_name = UniqueImageClause(p.image_table)
                else:
                    select_name = UniqueImageClause(unique_tables[0])
                    logging.warn("Mixing multiple object tables in a filter is experimental, use with caution")
            else:
                select_name = UniqueImageClause()
            return 'SELECT %s FROM %s WHERE %s' % (select_name,
                                                   ','.join(unique_tables), 
                                                   str(f))
        elif isinstance(f, sqltools.OldFilter):
            return str(f)
        else:
            raise Exception('Invalid filter type in p._filters')

    def GetFilteredImages(self, filter_name):
        ''' Returns a list of imKeys from the given filter. '''
        try:
            f = p._filters[filter_name]
            # New filters can be based on object parameters. We need to remove duplicates.
            # Using dict instead of set preserves key order without additional time cost.
            imKeys = self.execute(self.filter_sql(filter_name))
            return list(dict.fromkeys(imKeys))
        except Exception as e:
            logging.error('Filter query failed for filter "%s". Check the SQL syntax in your properties file.'%(filter_name))
            logging.error(e)
            raise Exception('Filter query failed for filter "%s". Check the SQL syntax in your properties file.'%(filter_name))

    def GetFilteredObjects(self, filter_obj, N=None, random=True):
        # Get filtered object keys using a passed in filter sql object
        from . import sqltools
        q = sqltools.QueryBuilder()
        q.select(sqltools.object_cols())
        q.where([filter_obj])
        q.group_by(sqltools.object_cols())
        if random:
            if p.db_type.lower() == 'sqlite':
                query = f"{str(q)} ORDER BY RANDOM()"
            else:
                query = f"{str(q)} ORDER BY RAND()"
        else:
            query = f"{str(q)} ORDER BY {p.object_table}.{p.image_id}"
        if N is not None:
            query += f" LIMIT {N}"
        keys = self.execute(query)
        return keys


    def GetGatedImages(self, gate_name):
        ''' Returns a list of imKeys from the given filter. '''
        try:
            g = p.gates[gate_name]
            from . import sqltools
            if isinstance(g, sqltools.Gate):
                unique_tables = np.unique(g.get_tables())
                if len(unique_tables) > 1:
                    if p.image_table in unique_tables:
                        select_name = UniqueImageClause(p.image_table)
                    else:
                        select_name = UniqueImageClause(unique_tables[0])
                        logging.warn("Mixing multiple object tables in a filter is experimental, use with caution")
                else:
                    select_name = UniqueImageClause()
                imKeys = self.execute(f"SELECT {select_name} FROM {','.join(unique_tables)} WHERE {str(g)}")
                return list(dict.fromkeys(imKeys))
            else:
                raise Exception('Invalid gate type in p.gate')

        except Exception as e:
            logging.error('Filter query failed for filter "%s". Check the MySQL syntax in your properties file.'%(gate_name))
            logging.error(e)
            raise Exception('Filter query failed for filter "%s". Check the MySQL syntax in your properties file.'%(gate_name))

    def GetGatedObjects(self, gate_name, N=None, random=True):
        from . import sqltools
        q = sqltools.QueryBuilder()
        q.select(sqltools.object_cols())
        q.where([p.gates[gate_name]])
        q.group_by(sqltools.object_cols())
        if random:
            if p.db_type.lower() == 'sqlite':
                query = f"{str(q)} ORDER BY RANDOM()"
            else:
                query = f"{str(q)} ORDER BY RAND()"
        else:
            query = f"{str(q)} ORDER BY {p.object_table}.{p.image_id}"
        if N is not None:
            query += f" LIMIT {N}"
        keys = self.execute(query)
        return keys

    def GetTableNames(self):
        '''
        returns all table names in the database
        '''
        if p.db_type.lower()=='mysql':
            res = self.execute('SHOW TABLES')
            return [t[0] for t in res] 
        elif p.db_type.lower()=='sqlite':
            res = self.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
            return [t[0] for t in res] 

    def get_other_table_names(self):
        '''
        returns a list of table names in the database that CPA hasn't accessed.
        '''
        tables = list(set(self.GetTableNames()) - 
                      set([p.image_table, p.object_table]))
        return sorted(tables)
        
    def GetColumnNames(self, table):
        '''Returns a list of the column names for the specified table. '''
        # NOTE: SQLite doesn't like DESCRIBE or SHOW statements so we do it this way.
        self.execute('SELECT * FROM %s LIMIT 1'%(table))
        return self.GetResultColumnNames()   # return the column names
    

    
    
    #
    # Methods used for linking database tables
    #
    #
    #           link_tables_table
    # +-------------------------------------+
    # | src     | dest     | link   | ord   |
    # +-------------------------------------+
    # | obj     | treat    | img    | 0     |
    # | obj     | treat    | well   | 1     |
    # | obj     | treat    | treat  | 2     |
    #
    #          link_columns_table
    # +-----------------------------------+
    # | table1 | table2   | col1  | col2  |
    # +-----------------------------------+
    # | per_im | per_well | plate | plate |
    # | per_im | per_well | well  | well  |
    # 
    
    def _add_link_tables_row(self, src, dest, link, order):
        '''adds src, dest, link, order to link_tables_table.
        '''
        self.execute('INSERT INTO %s (src, dest, link, ord) '
                     'VALUES ("%s", "%s", "%s", "%d")'
                     %(p.link_tables_table, src, dest, link, order))
        
    def _add_link_columns_row(self, src, dest, col1, col2):
        '''adds src, dest, col1, col2 to link_columns_table
        '''
        self.execute('INSERT INTO %s (table1, table2, col1, '
                     'col2) VALUES ("%s", "%s", "%s", "%s")'
                     %(p.link_columns_table, src, dest, col1, col2))

    def connected_tables(self, table):
        '''return tables connected (directly or indirectly) to the given table
        '''
        return [r[0] for r in self.execute('SELECT DISTINCT dest FROM %s '
                                           'WHERE src="%s"'
                                           %(p.link_tables_table, table))]
        
    def adjacent_tables(self, table):
        '''return tables directly connected to the given table
        '''
        return [r[0] for r in self.execute('SELECT DISTINCT link FROM %s '
                                           'WHERE src="%s" AND ord=0'
                                           %(p.link_tables_table, table))]
        
    def adjacent(self, table1, table2):
        '''return whether the given tables are adjacent
        '''
        return table1 in self.adjacent_tables(table2)
        
    def do_link_tables(self, src, dest, src_cols, dest_cols):
        '''Inserts table linking information into the database so src can 
        be linked to dest through the columns specified.
        src - table to be linked in
        dest - table to link src to
        src_cols - foreign key column names in src
        dest_cols - foreign key column names in dest
        '''
        assert len(src_cols) == len(dest_cols), 'Column lists were not the same length.'
        
        # create the tables if they don't exist
        if p.link_tables_table.lower() not in [x.lower() for x in self.GetTableNames()]:
            self.execute('CREATE TABLE %s (src VARCHAR(100), '
                         'dest VARCHAR(100), link VARCHAR(100), ord INTEGER)'
                         %(p.link_tables_table))
        if p.link_columns_table.lower() not in [x.lower() for x in self.GetTableNames()]:
            self.execute('CREATE TABLE %s (table1 VARCHAR(100), '
                    'table2 VARCHAR(100), col1 VARCHAR(200), col2 VARCHAR(200))'
                    %(p.link_columns_table))
            
        if self.get_linking_tables(src, dest) is not None:
            raise Exception('Tables are already linked. Call '
                'DBConnect.get_linking_tables to check if tables are linked '
                'before do_link_tables.')
        
        # Connect src directly to dest
        self._add_link_tables_row(src, dest, dest, 0)
        for col1, col2 in zip(src_cols, dest_cols):
            self._add_link_columns_row(src, dest, col1, col2)

        # Connect src to everything dest is connected to through dest
        for t in self.connected_tables(dest):
            self._add_link_tables_row(src, t, dest, 0)
            res = self.execute('SELECT * FROM %s WHERE src="%s" AND dest="%s"'
                               %(p.link_tables_table, dest, t))
            for row in res:
                link = row[2]
                order = int(row[3]) + 1
                self._add_link_tables_row(src, t, link, order)
        
        # Connect dest back to src
        self._add_link_tables_row(dest, src, src, 0)
        for col1, col2 in zip(src_cols, dest_cols):
            self._add_link_columns_row(dest, src, col2, col1)

        self.Commit()
        
    #
    # TODO: ensure this table wasn't linking others together.
    #
    def do_unlink_table(self, table):
        '''remove all linkage entries pertaining to the given table
        '''
        self.execute('DELETE FROM %s WHERE src=%s OR dest=%s OR link=%s'
                     %(p.link_tables_table, table, table, table))
        self.execute('DELETE FROM %s WHERE table1=%s OR table2=%s'
                     %(p.link_columns_table, table, table))
        self.Commit()
            
    def get_linking_expressions(self, tables):
        '''returns: A list of Expressions linking the tables given. These 
        expressions may link through some intermediate table if a path exists.
        
        Use when constructing a where clause for a multi-table query.
                 
        An exception is raised if a path linking the tables doesn't exist. Call
        DBConnect.get_linking_tables first to check that all tables are linked.
                 
        usage: 
        get_linking_expressions(['per_well', 'per_image', 'per_object'])
        [Expression(('per_well', 'Plate'), '=', ('per_image', 'Plate')),
         Expression(('per_well', 'Well'),  '=', ('per_image', 'Well')),
         Expression(('per_image', 'ImageNumber'),  '=', ('per_object', 'ImageNumber'))]
        '''
        from . import sqltools as sql
        for t in tables[1:]:
            if self.get_linking_table_pairs(tables[0], t) is None:
                raise Exception('Tables "%s" and "%s" are not linked.'%(tables[0], t))
            
        def get_linking_clauses(table1, table2):
            #helper function returns expressions that link 2 tables
            return [sql.Expression(sql.Column(ta, cola), '=', sql.Column(tb, colb))
                    for ta, tb in self.get_linking_table_pairs(table1, table2)
                    for cola, colb in self.get_linking_columns(ta, tb)]
        
        expressions = set()
        for table in tables[1:]:
            expressions.update(get_linking_clauses(tables[0], table))
        return expressions
    
    def get_linking_tables(self, table_from, table_to):
        '''returns: an ordered list of tables that must be used to join
        table_from to table_to. If the tables aren't linked in link_tables_table
        then None is returned.
        
        usage:
        get_linking_tables(per_well, per_object)
        [per_image, per_object]
        '''
        if p.link_tables_table not in self.GetTableNames():
            return None
        res = self.execute('SELECT link FROM %s '
                          'WHERE src="%s" AND dest="%s" ORDER BY ord'
                          %(p.link_tables_table, table_from, table_to))

        return [row[0] for row in res] or None 
    
    def get_linking_table_pairs(self, table_from, table_to):
        '''returns: an ordered list of table pairs that must be used to join 
        table_from to table_to. If the tables aren't linked in link_tables_table
        then None is returned.
        
        usage:
        get_linking_table_pairs(per_well, per_object)
        [(per_well, per_image), (per_image, per_object)]        
        '''
        ltables = self.get_linking_tables(table_from, table_to)
        if ltables is None:
            return None
        from_tables = [table_from] + [t for t in ltables[:-1]]
        to_tables = ltables
        return [(tfrom, tto) for tfrom, tto in zip(from_tables, to_tables)]
    
    def get_linking_columns(self, table_from, table_to):
        '''returns: a list of column pairs that can be used to join table_from 
                 to table_to. An exception is raised if table_from is not 
                 DIRECTLY linked to table_to in link_tables_table or if the
                 link_columns_table is not found.

        usage: >>> get_linking_columns(per_well, per_image)
               [(plateid, plate), (wellid, well)]
        '''
        if p.link_columns_table not in self.GetTableNames():
            raise Exception('Could not find link_columns table "%s".'%(p.link_columns_table))
        col_pairs = self.execute('SELECT col1, col2 FROM %s WHERE table1="%s" '
                                 'AND table2="%s"'%(p.link_columns_table, table_from, table_to))
        if len(col_pairs[0]) == 0:
            raise Exception('Tables "%s" and "%s" are not directly linked in '
                            'the database'%(table_from, table_to))
        return col_pairs
        
    def get_linkable_tables(self):
        '''returns the list of tables that CPA can link together.
        '''
        tables = []
        if p.link_tables_table in self.GetTableNames():
            tables = [row[0] for row in 
                      self.execute('SELECT DISTINCT src FROM %s'
                                   %(p.link_tables_table))]
        if len(tables) == 0:
            if p.object_table:
                self.do_link_tables(p.image_table, p.object_table, 
                                    image_key_columns(), image_key_columns())
                return [p.image_table, p.object_table]
            else:
                return [p.image_table]
        return tables

    def GetUserColumnNames(self, table):
        '''Returns a list of the column names that start with "User_" for the 
        specified table. '''
        return [col for col in self.GetColumnNames(table) if col.lower().startswith('user')]

    def GetColumnTypes(self, table):
        '''Returns python types for each column of the given table. '''
        sqltypes = self.GetColumnTypeStrings(table)
        return [sqltype_to_pythontype(t) for t in sqltypes]
    
    def GetColumnType(self, table, colname):
        '''Returns the python type for a given table column. '''
        for col, coltype in zip(self.GetColumnNames(table), self.GetColumnTypes(table)):
            if col == colname:
                return coltype
            
    def GetColumnTypeStrings(self, table):
        '''Returns the SQL type string for each column of the given table.'''
        if p.db_type.lower() == 'sqlite':
            res = self.execute('PRAGMA table_info(%s)'%(table))
            return [r[2] for r in res]
        elif p.db_type.lower() == 'mysql':
            res = self.execute('SHOW COLUMNS FROM %s'%(table))
            return [r[1] for r in res]
        
    def GetColumnTypeString(self, table, colname):
        '''Returns the SQL type string for a given table column. '''
        for col, coltype in zip(self.GetColumnNames(table), self.GetColumnTypeStrings(table)):
            if col == colname:
                return coltype

    def GetColnamesForClassifier(self, exclude_features_with_no_variance=False,
                                 force=False):
        '''
        Returns a list of column names for the object_table excluding 
        those specified in Properties.classifier_ignore_columns
        and excluding those with zero variance (unless 
        exclude_features_with_no_variance is set to False)
        '''
        if (self.classifierColNames is None) or force:
            col_names = self.GetColumnNames(p.object_table)
            col_types = self.GetColumnTypes(p.object_table)
            # automatically ignore all string-type columns
            # ColumnTypes will return None for unknown formats, rather than a proper type.
            self.classifierColNames = [col for col, coltype in zip(col_names, col_types) if coltype not in (str, None)]
            # automatically ignore ID columns
            if p.table_id in self.classifierColNames:
                self.classifierColNames.remove(p.table_id)
            self.classifierColNames.remove(p.image_id)
            self.classifierColNames.remove(p.object_id)
            if len(self.classifierColNames) == 0:
                import wx
                wx.MessageBox('No columns were found to use for classification '
                              'Please check your per-object table, it may be '
                              'empty or not contain any numeric columns.', 'Error')
                self.classifierColNames = None
                return None
            # treat each classifier_ignore_substring as a regular expression
            # for column names to ignore
            if p.classifier_ignore_columns:
                self.classifierColNames = [col for col in self.classifierColNames
                                           if not any([re.match('^'+user_exp+'$',col)
                                                       for user_exp in p.classifier_ignore_columns])]
            logging.info('Ignoring columns: %s'%([x for x in col_names if x not in self.classifierColNames]))

            if exclude_features_with_no_variance:
                # ignore columns which have no variance
                cq = ', '.join(['MAX(%s)-MIN(%s)'%(col,col) for col in col_names])
                res = np.array(self.execute('SELECT %s FROM %s'%(cq, p.object_table))[0])
                ignore_cols = np.array(col_names)[np.where(res==0)[0]]                
                for colname in ignore_cols:
                    self.classifierColNames.remove(colname)            
                    logging.warning('Ignoring column "%s" because it has zero variance'%(colname))
            
            if len(self.classifierColNames) == 0 and p.classifier_ignore_columns:
                import wx
                wx.MessageBox('No columns were found to use for classification '
                              'after filtering columns that matched your '
                              'classifier_ignore_columns properties setting. '
                              'Please check your properties and your per-object'
                              ' table.', 'Error')
                self.classifierColNames = None
                return None
        return self.classifierColNames
    
    def GetResultColumnNames(self):
        ''' Returns the column names of the last query on this connection. '''
        connID = threading.currentThread().getName()
        return [x[0] for x in self.cursors[connID].description]

    def GetCellDataForRedux(self):
        '''
        Returns a list of measurements for the specified object excluding
        those specified in Properties.classifier_ignore_columns
        '''
        if (self.classifierColNames == None):
            self.GetColnamesForClassifier()
        query = 'SELECT %s FROM %s' %(', '.join([p.image_id, p.object_id] + self.classifierColNames), p.object_table)

        data = self.execute(query, silent=False)
        if len(data) == 0:
            logging.error('No data in table')
            return None
        # This should be the case
        valid_types = (int, float, type(None))
        if not all([type(x) in valid_types for x in data[0]]):
            raise ValueError("Invalid column types were found in the data. "
                             "Only numerical columns can be present in the object table")
        return np.array(data, dtype=np.float)

    def GetCellData(self, obKey):
        '''
        Returns a list of measurements for the specified object.
        '''
        query = 'SELECT * FROM %s WHERE %s' %(p.object_table, GetWhereClauseForObjects([obKey]))
        data = self.execute(query, silent=True)
        if len(data) == 0:
            logging.error('No data for obKey: %s'%str(obKey))
            return None
        # fetch out only numeric data
        values = [x if type(x) in (int, float) else 0.0 for x in data[0]]
        return np.array(values)

    def GetCellsData(self, obKeys):
        '''
        Returns a list of measurements for multiple objects.
        '''
        if p.db_type.lower() == 'mysql':
            query = f'SELECT {p.image_id}, {p.object_id}, {p.object_table}.* FROM {p.object_table} WHERE {GetWhereClauseForObjects(obKeys)}'
        else:
            query = f'SELECT {p.image_id}, {p.object_id}, * FROM {p.object_table} WHERE {GetWhereClauseForObjects(obKeys)}'
        data = self.execute(query, silent=True)
        if len(data) == 0:
            logging.error('No data for obKeys: %s'%str(obKeys))
            return None
        # fetch out only numeric data
        buffer = []
        for line in data:
            buffer.append(((line[0], line[1]), np.array([x if type(x) in (int, float) else 0.0 for x in line[2:]])))
        return buffer

    def GetPlateNames(self):
        '''
        Returns the names of each plate in the per-image table.
        '''
        res = self.execute('SELECT DISTINCT %s FROM %s ORDER BY %s'%(p.plate_id, p.image_table, p.plate_id))
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
        colTypes = ['' for i in range(nCols)]
        # Maximum string length for each column (if VARCHAR)
        maxLen   = [0 for i in range(nCols)] 
        try:
            tabledata[0][0]
        except: 
            raise Exception('Cannot infer column types from an empty table.')
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
                    raise Exception('Value in table could not be converted to string!')
        return colTypes
    
    def AppendColumn(self, table, colname, coltype):
        '''
        Appends a new column to the specified table.
        The column name must begin with "User_" and contain only A-Za-z0-9_
        '''
        _check_colname_user(p, table, colname)
        if not re.match('^[A-Za-z]\w*$', colname):
            raise ValueError('Column name may contain only alphanumeric characters and underscore, and must begin with a letter.')
        self.execute('ALTER TABLE %s ADD %s %s'%(table, colname, coltype))
        
    def UpdateWells(self, table, colname, value, wellkeys):
        '''
        Sets the value of the specified column in the database for each row
        associated with wellkeys. Pass value=None to store NULL
        '''
        # TODO: handle other tables
        assert table == p.image_table
        _check_colname_user(p, table, colname)
        if type(value) == str:
            if re.search(r'["\'`]', value):
                raise ValueError('No quotes are allowed in values written to the database.')
            value = '"'+value+'"'
        if value is None:
            value = 'NULL'
        self.execute('UPDATE %s SET %s=%s WHERE %s'%(table, colname, value,
                                                GetWhereClauseForWells(wellkeys)))
        # for some reason non string columns need to be committed or they will not be saved
        self.Commit()
    
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
        columnLabels = next(r)
        columnLabels = [lbl.strip() for lbl in columnLabels]

        dtable = get_data_table_from_csv_reader(r)
        colTypes = self.InferColTypesFromData(dtable, len(columnLabels))
        
        # Build the CREATE TABLE statement
        statement = 'CREATE TABLE '+p.image_table+' ('
        statement += ',\n'.join([lbl+' '+colTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
        
        logging.info('Creating table: %s'%(p.image_table))
        self.execute('DROP TABLE IF EXISTS %s'%(p.image_table))
        self.execute(statement)

        if not p.classification_type == 'image':
            # CREATE THE OBJECT TABLE
            # For the object table we assume that all values are type FLOAT
            # except for the primary keys
            f = open(p.object_csv_file, 'U')
            r = csv.reader(f)
            columnLabels = next(r)
            columnLabels = [lbl.strip() for lbl in columnLabels]
            dtable = get_data_table_from_csv_reader(r)
            colTypes = self.InferColTypesFromData(dtable, len(columnLabels))
            statement = 'CREATE TABLE '+p.object_table+' ('
            statement += ',\n'.join([lbl+' '+colTypes[i] for i, lbl in enumerate(columnLabels)])
            keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
            statement += ',\nPRIMARY KEY (' + keys + ') )'
            f.close()

            logging.info('Creating table: %s'%(p.object_table))
            self.execute('DROP TABLE IF EXISTS '+p.object_table)
            self.execute(statement)
        
        # POPULATE THE IMAGE TABLE
        f = open(p.image_csv_file, 'U')
        r = csv.reader(f)
        row = next(r) # skip the headers
        row = next(r)
        while row:
            self.execute('INSERT INTO '+p.image_table+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')',
                         silent=True)
            try:
                row = next(r)
            except StopIteration:
                break
        f.close()
        
        # POPULATE THE OBJECT TABLE
        if not p.classification_type == 'image':
            f = open(p.object_csv_file, 'U')
            r = csv.reader(f)
            row = next(r) # skip the headers
            row = next(r)
            while row:
                self.execute('INSERT INTO '+p.object_table+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')',
                             silent=True)
                try:
                    row = next(r)
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
        csv_dir = os.path.split(p.db_sql_file)[0] or '.'
        dir_files = os.listdir(csv_dir)
        for file in imcsvs + obcsvs:
            assert file in dir_files, ('File "%s" was specified in %s but was '
                                      'not found in %s.'%(file, os.path.split(p.db_sql_file)[1], csv_dir))

        assert len(imcsvs)>0, ('Failed to parse image csv filenames from %s. '
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
        
        import wx
        if self.gui_parent is not None and issubclass(self.gui_parent.__class__, wx.Window):
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
            logging.info('Populating image table with data from %s'%file)
            f = open(os.path.join(csv_dir, file), 'U')
            r = csv.reader(f)
            row1 = next(r)
            command = 'INSERT INTO '+p.image_table+' VALUES ('+','.join(['?' for i in row1])+')'
            self.cursors[connID].execute(command, row1)
            self.cursors[connID].executemany(command, [l for l in r if len(l)>0])
            f.close()
            base_bytes += os.path.getsize(os.path.join(csv_dir, file))
            pct = min(int(100 * base_bytes / total_bytes), 100)
            if dlg:
                c, s = dlg.Update(pct, '%d%% Complete'%(pct))
                if not c:
                    try:
                        os.remove(p.db_sqlite_file)
                    except OSError:
                        wx.MessageBox('Could not remove incomplete database'
                                      ' at "%s". This file must be removed '
                                      'manually or CPAnalyst will load it '
                                      'the next time use use the current '
                                      'database settings.', 'Error')
                    raise Exception('cancelled load')
            logging.info("... loaded %d%% of CSV data"%(pct))

        line_count = 0
        if not p.classification_type == 'image':
            assert len(obcsvs)>0, ('Failed to parse object csv filenames from %s. '
                              'Make sure db_sql_file in your properties file is'
                              ' set to the .SQL file output by CellProfiler\'s '
                              'ExportToDatabase module.'%(os.path.split(p.db_sql_file)[1]))

            for file in obcsvs:
                logging.info('Populating object table with data from %s'%file)
                f = open(csv_dir+os.path.sep+file, 'U')
                r = csv.reader(f)
                row1 = next(r)
                if p.check_tables:
                    object_table = p.object_table
                    object_table = object_table.split('_checked')[0]
                    command = 'INSERT INTO '+object_table+' VALUES ('+','.join(['?' for i in row1])+')'
                else:
                    command = 'INSERT INTO '+p.object_table+' VALUES ('+','.join(['?' for i in row1])+')'
                # guess at a good number of lines, about 250 megabytes, assuming floats)
                nlines = (250*1024*1024) // (len(row1) * 64)
                self.cursors[connID].execute(command, row1)
                lnum = 1
                while True:
                    lnum += 1
                    # fetch a certain number of lines efficiently
                    args = [l for idx, l in zip(list(range(nlines)), r) if len(l) > 0]
                    if args == []:
                        break
                    self.cursors[connID].executemany(command, args)
                    line_count += len(args)
                    prog = line_count
                    # pct = min(int(100 * (f.tell() + base_bytes) / total_bytes), 100)
                    if dlg:
                        c, s = dlg.Update(prog, '%d lines loaded'%(prog))
                        if not c:
                            try:
                                os.remove(p.db_sqlite_file)
                            except OSError:
                                wx.MessageBox('Could not remove incomplete database'
                                              ' at "%s". This file must be removed '
                                              'manually or CPAnalyst will load it '
                                              'the next time use use the current '
                                              'database settings.', 'Error')
                            raise Exception('cancelled load')
                    logging.info("... loaded %d lines of CSV data"%(prog))
                f.close()
                logging.info("Finished loading CSV data")
                base_bytes += os.path.getsize(os.path.join(csv_dir, file))

        # Commit only at very end. No use in committing if the db is incomplete.
        self.Commit()
        if dlg:
            dlg.Destroy()

    def GetImageWidthHeight(self,list_of_cols):
        # Get image width and height
        try:
            width_col = next(name for name in list_of_cols if 'width' in name.lower())
            height_col = next(name for name in list_of_cols if 'height' in name.lower())
            width_query = 'SELECT %s FROM %s LIMIT 1'%(width_col, p.image_table)
            height_query = 'SELECT %s FROM %s LIMIT 1'%(height_col, p.image_table)
            width = self.execute(width_query)
            height = self.execute(height_query)
            width = int(width[0][0])
            height = int(height[0][0])
        except:
            if p.image_width and p.image_height:
                width = int(p.image_width)
                height = int(p.image_height)
            else:
                raise Exception('Input image_width and image_height fields in properties file')
        return width, height

    def CreateObjectCheckedTable(self):
        # Create object (checked) table where there are no rows with missing/null values
        DB_NAME = p.db_name
        DB_TYPE = p.db_type.lower()

        object_table = p.object_table
        object_table = object_table.split('_checked')[0]

        # Try to get a quick count of how many table rows we started with.
        try:
            query = f"SELECT COUNT(*) FROM {object_table}"
            initial_count = self.execute(query)[0][0]
        except:
            logging.error("Unable to count table rows")
            initial_count = 0

        all_cols = [str(x) for x in self.GetColumnNames(object_table)]

        # We don't want to obliterate the table if there's an entirely empty column. Let's exclude those.
        # Checking entire columns is expensive, let's restrict our search.
        # First we sample 1 row and identify columns with missing values.
        query = f"SELECT * FROM {object_table} LIMIT 1"
        res = self.execute(query)[0]
        maybe_empty_cols = [col for col, val in zip(all_cols, res) if val is None]
        if len(maybe_empty_cols) > 0:
            # Now let's check whether those missing columns are entirely empty (count will be 0).
            query = f"SELECT {', '.join([f'count({col})' for col in maybe_empty_cols])} from {object_table}"
            res = self.execute(query)[0]
            empty_cols = set([col for col, count in zip(maybe_empty_cols, res) if count == 0])
            # Now we rebuild our table column list without the empty columns
            all_cols = [col for col in all_cols if col not in empty_cols]
            logging.info(f"Table checking dropped {len(empty_cols)} blank columns")

        AreaShape_Area = [x for x in all_cols if 'AreaShape_Area' in x]
        if DB_TYPE == 'mysql':
            if len(AreaShape_Area) > 0:
                query = f"""CREATE OR REPLACE VIEW {p.object_table} AS SELECT {', '.join(all_cols)} FROM {object_table} 
                WHERE {" IS NOT NULL AND ".join(all_cols)} IS NOT NULL AND {" > 0 AND ".join(AreaShape_Area)} > 0"""
            else:
                query = f"""CREATE OR REPLACE VIEW {p.object_table} AS SELECT {', '.join(all_cols)} FROM {object_table} 
                WHERE {" IS NOT NULL AND ".join(all_cols)} IS NOT NULL"""
            self.execute(query)
        elif DB_TYPE == 'sqlite':
            # SQL can only handle 1000 comparisons in a query. If we have too many columns we'll need to break it up.
            col_buffer = [all_cols[i:i + 400] for i in range(0, len(all_cols), 400)]
            # Do the largest chunk first, it'll reduce work later on.
            to_test = col_buffer.pop(0)

            query = f"PRAGMA table_info({object_table})"
            self.execute(query)
            query = f'DROP TABLE IF EXISTS {p.object_table}'
            self.execute(query)
            if len(AreaShape_Area) > 0:
                query = f"""CREATE TABLE {p.object_table} AS SELECT {', '.join(all_cols)} FROM {object_table} WHERE {
                " IS NOT NULL AND ".join(to_test)} IS NOT NULL AND {" != '' AND ".join(to_test)}  != '' AND {
                " > 0 AND ".join(AreaShape_Area)} > 0"""
            else:
                query = f"""CREATE TABLE {p.object_table} AS SELECT {', '.join(all_cols)} FROM {object_table} WHERE {
                " IS NOT NULL AND ".join(to_test)} IS NOT NULL AND {" != '' AND ".join(to_test)}  != ''"""
            self.execute(query)
            for chunk in col_buffer:
                query = f"""DELETE FROM {p.object_table} WHERE {
                " IS NOT NULL AND ".join(chunk)} IS NOT NULL AND {" != '' AND ".join(chunk)}  != ''"""
                self.execute(query)
        self.Commit()
        # Inform user of what we did. Also check whether we nuked the table.
        try:
            query = f"SELECT COUNT(*) FROM {p.object_table}"
            res = self.execute(query)[0][0]
            if res == 0:
                logging.error("Table checking removed all rows, you may have an empty column in your database. "
                              "Disable check_tables in your properties file if this is expected.")
            else:
                logging.info(f"Table checking removed {initial_count - res} rows with missing values")
            if res < initial_count // 2:
                import wx
                dlg = wx.MessageDialog(None, 'The check_tables option was enabled in your propreties file, but this '
                                             f'would exclude {initial_count - res} of {initial_count} rows from your '
                                             'data set (which had values missing). If using a combined object '
                                             'table you might want to disable table checking. Should the rows be '
                                             'excluded for this session?',
                                       'Table checking', wx.YES_NO | wx.ICON_WARNING)
                result = dlg.ShowModal()
                if result == wx.ID_NO:
                    # Use the non-checked table instead
                    logging.info(f"Discarded table checking results, using original object table")
                    p.object_table = object_table
        except:
            logging.error("Unable to validate checked object table")

        try:
            if not self.get_linking_tables(p.image_table, p.object_table):
                # Link image table to the checked object table.
                self.do_link_tables(p.image_table, p.object_table, image_key_columns(), image_key_columns())
        except:
            logging.error("Unable to link checked tables upon creation. Some SQL filters may not work correctly.")

    def CreateObjectImageTable(self):
        # Create object table for image classification
        DB_NAME = p.db_name
        DB_TYPE = p.db_type.lower()
        if DB_TYPE == 'mysql':
            query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '%s' AND TABLE_NAME = '%s'"%(DB_NAME, p.image_table)
            self.execute(query)
            list_of_cols = []
            cols = [x for x in self.GetColumnNames(p.image_table)]
            list_of_cols.extend([str(x) for x in cols])
            width, height = self.GetImageWidthHeight(list_of_cols)

            query = "CREATE OR REPLACE VIEW %s AS SELECT 1 AS %s, %d AS %s, %d AS %s, %s.* FROM %s"%(p.object_table, p.object_id, width/2, p.cell_x_loc, height/2, p.cell_y_loc, p.image_table,p.image_table)
            self.execute(query)

        elif DB_TYPE == 'sqlite':
            # Copy image table and add more columns
            query = "PRAGMA table_info(%s)"%p.image_table
            self.execute(query)
            list_of_cols = [str(x) for x in self.GetColumnNames(p.image_table)]
            list_of_colTypes = [str(x) for x in self.GetColumnTypeStrings(p.image_table)]
            all_cols = list(list_of_cols)
            all_colTypes = list(list_of_colTypes)
            pid_index = all_cols.index(p.image_id)
            all_cols.remove(p.image_id)
            all_colTypes.remove(list_of_colTypes[pid_index])
            all_cols = [p.image_id, p.object_id, p.cell_x_loc, p.cell_y_loc] + all_cols
            list_of_colTypes = [list_of_colTypes[pid_index], list_of_colTypes[pid_index], 'float', 'float'] + all_colTypes
            object_table = p.object_table
            if object_table.endswith('_checked'):
                object_table = object_table[:-8]
            query = 'DROP TABLE IF EXISTS %s'%(object_table)
            self.execute(query)
            query = 'CREATE TABLE %s (%s)'%(object_table, ",".join([all_cols[i]+' '+list_of_colTypes[i] for i in range(len(all_cols))]))
            self.execute(query)
            query = 'INSERT INTO %s (%s) SELECT %s FROM %s'%(object_table, ",".join(list_of_cols), ",".join(list_of_cols), p.image_table)
            self.execute(query)

            #Get info on image width and height (assuming they are fields in the image table) to get image center
            width, height = self.GetImageWidthHeight(list_of_cols)

            query = "UPDATE %s SET %s=1, %s=%s, %s=%s"%(object_table, p.object_id,
                                                              p.cell_x_loc, width/2,
                                                              p.cell_y_loc, height/2)
            self.execute(query)
            self.Commit()
        if self.get_linking_tables(object_table, p.image_table) is None:
            # Link the temporary table if needed
            self.do_link_tables(object_table, p.image_table, image_key_columns(), image_key_columns())
        logging.info('%s table added to database'%object_table)


    def table_exists(self, name):
        res = []
        if p.db_type.lower() == 'mysql':
            res = self.execute("SELECT table_name FROM information_schema.tables WHERE table_name='%s' AND table_schema='%s'"%(name, p.db_name))
        else:
            res = self.execute("SELECT name FROM sqlite_master WHERE type='table' and name='%s'"%(name))
            res += self.execute("SELECT name FROM sqlite_temp_master WHERE type='table' and name='%s'"%(name))            
        return len(res) > 0
    
    def CreateTempTableFromCSV(self, filename, tablename):
        '''
        Reads a csv file into a temporary table in the database.
        Column names are taken from the first row.
        Column types are inferred from the data.
        '''
        import csv
        if hasattr(filename, 'read'):
            f = filename
        else:
            f = open(filename, 'U')
        r = csv.reader(f)
        self.execute('DROP TABLE IF EXISTS %s'%(tablename))
        colnames = next(r)
        dtable = np.array(get_data_table_from_csv_reader(r))
        typed_table = []
        for i in range(dtable.shape[1]):
            try:
                col = np.array(dtable[:,i], dtype=str)
                col = np.array(dtable[:,i], dtype=float)
                col = np.array(dtable[:,i], dtype=int) 
            except:
                pass
            typed_table += [col]
        typed_table = np.array(typed_table, dtype=object).T
        return self.CreateTempTableFromData(typed_table, colnames, tablename)
    
    def create_empty_table(self, tablename, colnames, coltypes, temporary=False):
        '''Creates an empty table with the given tablename and columns.
        Note: column names will automatically be cleaned up.
        '''
        self.execute('DROP TABLE IF EXISTS %s'%(tablename))
        # Clean up column names
        colnames = clean_up_colnames(colnames)
        coldefs = ', '.join(['`%s` %s'%(lbl, coltypes[i]) for i, lbl in enumerate(colnames)])
        if not temporary:
            self.execute('CREATE TABLE %s (%s)'%(tablename, coldefs))
        else:
            self.execute('CREATE TEMPORARY TABLE %s (%s)'%(tablename, coldefs))

    def create_default_indexes_on_table(self, tablename):
        '''automatically adds indexes to all the image, object, and well key 
        columns in the specified table
        '''
        for key in list(well_key_columns() or []) + list(object_key_columns()):
            if key in self.GetColumnNames(tablename):
                self.execute('CREATE INDEX %s ON %s (%s)'%('%s_%s'%(tablename,key), tablename, key))

    def insert_rows_into_table(self, tablename, colnames, coltypes, rows):
        '''Inserts the given rows into the table
        '''
        for row in rows:
            vals = []
            for i, val in enumerate(row):
                if (coltypes[i]=='FLOAT' and (np.isinf(val) or np.isnan(val))
                    or val is None):
                    vals += ['NULL']
                else:
                    vals += ['"%s"'%val]
            vals = ', '.join(vals)
            self.execute('INSERT INTO %s (%s) VALUES (%s)'%(
                          tablename, ', '.join(colnames), vals), silent=True)
    
    def CreateTempTableFromData(self, dtable, colnames, tablename, temporary=True):
        '''Creates and populates a temporary table in the database.
        '''
        return self.CreateTableFromData(dtable, colnames, tablename, temporary=temporary)
    
    def CreateTableFromData(self, dtable, colnames, tablename, temporary=False, coltypes=None):
        '''Creates and populates a table in the database.
        dtable -- array of the data to populate the table with (SQL data types 
                  are inferred from the array data)
        colnames -- the column names to use (note: these will be cleaned up if 
                    invalid characters are used)
        tablename -- the name of the table
        temporary -- whether the table should be created as temporary
        '''
        colnames = clean_up_colnames(colnames)
        if coltypes is None:
            coltypes = self.InferColTypesFromData(dtable, len(colnames))
        self.create_empty_table(tablename, colnames, coltypes, temporary)
        self.create_default_indexes_on_table(tablename)
        logging.info('Populating %stable %s...'%((temporary and 'temporary ' or ''), tablename))
        self.insert_rows_into_table(tablename, colnames, coltypes, dtable)
        self.Commit()
        return True
    
    def is_view(self, table):
        if p.db_type == 'sqlite':
            return False
        self.execute('SHOW CREATE TABLE %s'%(table))
        res = self.GetResultColumnNames()
        return res[0].lower() == 'view'
    
    def CheckTables(self):
        '''
        Queries the DB to check that the per_image and per_object
        tables agree on image numbers.
        '''
        if p.db_type=='sqlite':
            logging.warn('Skipping table checking step for sqlite')
            return

        logging.info('Checking database tables...')
        if not self.is_view(p.image_table):
            # For now, don't check indices on views.
            # Check for index on image_table
            res = self.execute('SHOW INDEX FROM %s'%(p.image_table))
            idx_cols = [r[4] for r in res]
            for col in image_key_columns():
                if col not in idx_cols:
                    import wx
                    wx.MessageDialog(self.gui_parent, 'Column "%s" is not indexed in table '
                        '"%s" Without column indices, dabase performance will be '
                        'severly slowed.\n'
                        'To avoid this warning, set check_tables = false in your '
                        'properties file.'%(col, p.object_table),
                        'Missing column index', 
                        style=wx.OK|wx.ICON_EXCLAMATION).ShowModal()
        else:
            logging.warn('%s is a view. CheckTables will skip the index check on this table'%(p.image_table))

        # Explicitly check for TableNumber in case it was not specified in props file
        if not p.object_table and 'TableNumber' in self.GetColumnNames(p.image_table):
            raise ValueError('Indexed column "TableNumber" was found in the database but not in your properties file.')
        
        # STOP here if there is no object table
        if not p.object_table:
            return
        
        if not self.is_view(p.object_table):
            # Check for index on object_table
            res = self.execute('SHOW INDEX FROM %s'%(p.object_table))
            idx_cols = [r[4] for r in res]
            for col in object_key_columns():
                if col not in idx_cols:
                    import wx
                    wx.MessageDialog(self.gui_parent, 'Column "%s" is not indexed in table '
                        '"%s" Without column indices, dabase performance will be '
                        'severly slowed.\n'
                        'To avoid this warning, set check_tables = false in your '
                        'properties file.'%(col, p.object_table),
                        'Missing column index', 
                        style=wx.OK|wx.ICON_EXCLAMATION).ShowModal()
        else:
            logging.warn('%s is a view. CheckTables will skip the index check on this table'%(p.object_table))
        
        # Explicitly check for TableNumber in case it was not specified in props file
        if ('TableNumber' not in object_key_columns()) and ('TableNumber' in self.GetColumnNames(p.object_table)):
            raise ValueError('Indexed column "TableNumber" was found in the database but not in your properties file.')
        elif ('TableNumber' in self.GetColumnNames(p.object_table)):
            logging.warn('TableNumber column was found indexed in your image table but not your object table.')
        elif ('TableNumber' not in object_key_columns()):
            logging.warn('TableNumber column was found indexed in your object table but not your image table.')
        
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
                logging.warn('WARNING: Images were found in "%s" that had a NULL or empty "%s" column value'%(p.image_table, p.well_id))
        
        # Check for unlabeled plates
        if p.plate_id:
            res = self.execute('SELECT %s FROM %s WHERE %s IS NULL OR %s=""'%(UniqueImageClause(), p.image_table, p.plate_id, p.plate_id))
            if any(res):
                logging.warn('WARNING: Images were found in "%s" that had a NULL or empty "%s" column value'%(p.image_table, p.plate_id))
        logging.info('Done checking database tables.')

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
            table_clause = "(%s) as foo"%(table_or_query,)
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

        def __next__(self):
            try:
                r = self.db.GetNextResult()
                if r:
                    return r
                else:
                    raise StopIteration
            except GeneratorExit:
                print("GeneratorExit")
                connID = threading.currentThread().getName()
                self.db.cursors[connID].fetchall()

    def __init__(self):
        self._where = []
        self.filters = []
        self._offset = None
        self._limit = None
        self._ordering = None
        self._columns = None
        self.group_columns = []

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

    def group_by(self, group_columns):
        new = copy.deepcopy(self)
        if type(group_columns) == str:
            new.group_columns += [group_columns]
        elif type(group_columns) in [list, tuple]:
            new.group_columns += group_columns
        else:
            raise
        return new

    def where(self, predicate):
        new = copy.deepcopy(self)
        new._where.append(predicate)
        return new

    def _get_where_clause(self):
        return "" if self._where == [] else "WHERE " + \
            " AND ".join(self._where)
    where_clause = property(_get_where_clause)

    def _get_group_by_clause(self):
        if self.group_columns == []:
            return ''
        else:
            return "GROUP BY " + ",".join(self.group_columns)
    group_by_clause = property(_get_group_by_clause)
    
    def count(self):
        c = DBConnect().execute(self.all_query(columns=["COUNT(*)"]))[0][0]
        c = max(0, c - (self._offset or 0))
        c = max(c, self._limit or 0)
        return c

    def all(self):
        return self.dbiter(self, DBConnect())

    def all_query(self, columns=None):
        return "SELECT %s FROM %s %s %s %s %s" % (
            ",".join(columns or self.columns()),
            self.from_clause,
            self.where_clause,
            self.group_by_clause,
            self.ordering_clause,
            self.offset_limit_clause)

    def _get_ordering_clause(self):
        if self._ordering is None:
            return ""
        else:
            return "ORDER BY " + ", ".join(self._ordering)
    ordering_clause = property(_get_ordering_clause)

    def _get_offset_limit_clause(self):
        return " ".join((self._limit and ["LIMIT %d" % self._limit] or []) +
                        (self._offset and ["OFFSET %d" % self._offset] or []))
    offset_limit_clause = property(_get_offset_limit_clause)

    def ordering(self, ordering):
        new = copy.deepcopy(self)
        new._ordering = ordering
        return new

    def project(self, columns):
        new = copy.deepcopy(self)
        new._columns = columns
        return new
    
    
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
    > cpa.dbconnect.Images().filter(compound_name).where("cast(Image_LoadedText_Platemap as decimal) = 10").objects()
    '''

    def __init__(self):
        super(Images, self).__init__()

    def _get_from_clause(self):
        t = set([col[:col.index('.')] for col in self.columns() if '.' in col])
        t = t - set(Properties().image_table)
        from_clause = [Properties().image_table] + list(t)
        for filter in self.filters:
            from_clause.append("JOIN (%s) AS %s USING (%s)" %
                               (Properties()._filters[filter],
                                'filter_SQL_' + filter,
                                ", ".join(image_key_columns())))
        return " ".join(from_clause)
    from_clause = property(_get_from_clause)

    def objects(self):
        if self._offset is not None or self._limit is not None:
            raise ValueError("Cannot join with objects after applying "
                "offset/limit.")
        return Objects(images=self)

    def columns(self):
        return self._columns or DBConnect().GetColumnNames(Properties().image_table)

    
class Objects(Entity):
    '''
    Easy access to objects.

    > feature = "Cells_NumberNeighbors_SecondClosestDistance"
    > y = [row[0] for row in Objects().ordering([feature]).project([feature]).all()]
    '''

    def __init__(self, images=None):
        super(Objects, self).__init__()
        if images is None:
            self._images = None
        else:
            self._images = images
            self._where = images._where
            self.filters = images.filters

    def _get_from_clause(self):
        from_clause = [Properties().object_table]
        if self._images is not None:
            from_clause.append("JOIN %s USING (%s)"%
                               (Properties().image_table,
                                ", ".join(image_key_columns())))
        for filter in self.filters:
            from_clause.append("JOIN (%s) AS %s USING (%s)" %
                               (Properties()._filters[filter],
                                'filter_SQL_' + filter,
                                ", ".join(image_key_columns())))
        return " ".join(from_clause)
    from_clause = property(_get_from_clause)

    def columns(self):
        return self._columns or list(object_key_columns()) + \
            DBConnect().GetColnamesForClassifier()

    def standard_deviations(self):
        """Returns a list of the standard deviations of the non-key columns.
        Offsets and limits are ignored here, not sure if they should be."""
        db = DBConnect()
        return db.execute("SELECT %s FROM %s %s"%(
                ",".join(["STD(%s)" % c 
                          for c in db.GetColnamesForClassifier()]),
                self.from_clause, self.where_clause))[0]

    def __add__(self, other):
        return Union(self, other)


if __name__ == "__main__":
    ''' For debugging only... '''
    import wx
    app = wx.App()
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    p.show_load_dialog()

    app.MainLoop()
