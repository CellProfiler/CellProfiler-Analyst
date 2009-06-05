from MySQLdb.cursors import SSCursor
from Properties import Properties
from Singleton import Singleton
from sys import stderr
import MySQLdb
import exceptions
import numpy
import string
import sys
import threading
import traceback
import re

verbose = True

p = Properties.getInstance()

class DBException(Exception):
    def __str__(self):
        return 'ERROR: ' + self.args[0] + '\n'
# XXX: sys.traceback is only set when an exception is not handled
#      To test, enter an invalid image_channel_path column name in props file
#        filename, line_number, function_name, text = traceback.extract_tb(sys.last_traceback)[-1]
#        return "ERROR <%s>: "%(function_name) + self.args[0] + '\n'


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
        return (p.table_id, p.image_id, p.object_id)
    else:
        return (p.image_id, p.object_id)


def GetWhereClauseForObjects(obKeys):
    '''
    Return a SQL WHERE clause that matches any of the given object keys.
    Example: GetWhereClauseForObjects([(1, 3), (2, 4)]) => 'WHERE 
    ImageNumber=1 AND ObjectNumber=3 OR ImageNumber=2 AND ObjectNumber=4'
    '''
    return '(' + ' OR '.join([' AND '.join([col + '=' + str(value)
                                      for col, value in zip(object_key_columns(), obKey)])
                        for obKey in obKeys]) + ')'


def GetWhereClauseForImages(imKeys):
    '''
    Return a SQL WHERE clause that matches any of the give image keys.
    Example: GetWhereClauseForImages([(3,), (4,)]) => 'WHERE
    ImageNumber=3 OR ImageNumber=4'
    '''
    return '(' + ' OR '.join([' AND '.join([col + '=' + str(value)
                                      for col, value in zip(image_key_columns(), imKey)])
                        for imKey in imKeys]) + ')'


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
        self.sqliteDBFile = None

    def __str__(self):
        return string.join([ (key + " = " + str(val) + "\n")
                            for (key, val) in self.__dict__.items()])


    def Connect(self, db_host, db_user, db_passwd, db_name):
        '''
        Attempts to create a new connection to the specified database using
          the current thread name as a connection ID.
        If properties.db_type is 'sqlite', it will create a sqlite db in a
          temporary directory from the csv files specified by
          properties.image_csv_file and properties.object_csv_file
        '''
        connID = threading.currentThread().getName()
        
        # If this connection ID already exists print a warning
        if connID in self.connections.keys():
            if self.connectionInfo[connID] == (db_host, db_user, db_passwd, db_name):
                print 'WARNING <DBConnect.Connect>: A connection already exists for this thread. %s as %s@%s (connID = "%s").'%(db_name, db_user, db_host, connID)
            else:
                raise DBException, 'A connection already exists for this thread (%s). Close this connection first.'%(connID)

        # MySQL database: connect normally
        if p.db_type.lower() == 'mysql':
            try:
                conn = MySQLdb.connect(host=db_host, db=db_name, user=db_user, passwd=db_passwd)
                self.connections[connID] = conn
                self.cursors[connID] = SSCursor(conn)
                self.connectionInfo[connID] = (db_host, db_user, db_passwd, db_name)
                if verbose:
                    print 'Connected to database: %s as %s@%s (connID = "%s").'%(db_name, db_user, db_host, connID)
            except MySQLdb.Error, e:
                raise DBException, 'Failed to connect to database: %s as %s@%s (connID = "%s").\n  %s'%(db_name, db_user, db_host, connID, e)
            
        # SQLite database: create database from file
        elif p.db_type.lower() == 'sqlite':
            from pysqlite2 import dbapi2 as sqlite
            
            if self.sqliteDBFile is None:
                # compute a database name unique to this data  
                from tempfile import gettempdir
                from md5 import md5
                f_im = open(p.image_csv_file, 'U')
                f_ob = open(p.object_csv_file, 'U')
                l = str(f_im.readlines() + f_ob.readlines())
                f_im.close()
                f_ob.close()
                dbname = 'CPA_DB_'+md5(l).hexdigest()+'.db'
                dbpath = gettempdir()
                self.sqliteDBFile = dbpath+'/'+dbname

            # Use existing database file
            self.connections[connID] = sqlite.connect(self.sqliteDBFile)
            self.cursors[connID] = self.connections[connID].cursor()
            self.connectionInfo[connID] = ('sqlite', 'cpa_user', '', 'CPA_DB')
            self.connections[connID].create_function('greatest', -1, max)
            self.connections[connID].create_function('median', -1, numpy.median)

            def classifier(num_stumps, *args):
                args = numpy.array(args)
                stumps = args[:num_stumps]  > args[num_stumps:2*num_stumps]
                num_classes = (len(args) / num_stumps) - 2
                best = -numpy.inf
                data = args[2*num_stumps:]
                for cl in range(num_classes):
                    score = (data[:num_stumps] * stumps).sum()
                    if score > best:
                        bestcl = cl
                        best = score
                    data = data[num_stumps:]
                return bestcl

            self.connections[connID].create_function('classifier', -1, classifier)
            
            try:
                # Try the connection
                self.GetAllImageKeys()
            except Exception:
                # If this is the first connection, then we need to create the DB from the csv files
                if len(self.connections) == 1:
                    print 'DBConnect: Creating SQLite database at: %s.'%(self.sqliteDBFile)
                    self.CreateSQLiteDB()
                    
        # Unknown database type (this should never happen)
        else:
            raise DBException, "Unknown db_type in properties: '%s'\n"%(p.db_type)


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
            print 'Closed connection: %s as %s@%s (connID="%s").' % (db_name, db_user, db_host, connID)
        else:
            print 'WARNING <DBConnect.CloseConnection>: No connection ID "%s" found.' %(connID)


    def execute(self, query, args=None, silent=False):
        '''
        Executes the given query using the connection associated with the 
        current thread, then returns the results as a list of rows.
        '''
        # Grab a new connection if this is a new thread
        connID = threading.currentThread().getName()
        if not connID in self.connections.keys():
            self.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
        
        # Test for lost connection
        try:
            self.connections[connID].ping()
        except MySQLdb.OperationalError, e:
            print 'Lost connection to database. Attempting to reconnect...'
            self.CloseConnection(connID)
            self.Connect(db_host=p.db_host, db_user=p.db_user, db_passwd=p.db_passwd, db_name=p.db_name)
        except AttributeError:
            pass # SQLite doesn't know ping.
        
        # Finally make the query
        try:
            if verbose and not silent: print '[%s] %s'%(connID, query)
            if p.db_type=='sqlite':
                if args:
                    raise 'Can\'t pass args to sqlite execute!'
                self.cursors[connID].execute(query)
            else:
                self.cursors[connID].execute(query, args=args)
            return self._get_results_as_list()
        except MySQLdb.Error, e:
            raise DBException, 'Database query failed for connection "%s"\n\t%s\n\t%s\n' %(connID, query, e)
        except KeyError, e:
            raise DBException, 'No such connection: "%s".\n' %(connID)
            
            
    def Commit(self):
        connID = threading.currentThread().getName()
        try:
            print '[%s] Commit'%(connID)
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
            raise DBException, 'Error retrieving next result from database.\n'
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
        r = self.GetNextResult()
        l = []
        while r:
            l.append(r)
            r = self.GetNextResult()
        return l
    
    
    
    
    
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
        select = 'SELECT '+UniqueImageClause(p.object_table)+', COUNT('+p.object_table+'.'+p.object_id
        select += ') FROM '+p.object_table+', '+p.image_table
        select += ' WHERE '+p.object_table+'.'+p.image_id+' = '+p.image_table+'.'+p.image_id
        if p.table_id:
            select += ' AND '+p.object_table+'.'+p.table_id+' = '+p.image_table+'.'+p.table_id
        select += ' GROUP BY '+UniqueImageClause(p.object_table)
        return self.execute(select)
    
    
    def GetAllImageKeys(self):
        ''' Returns a list of all image keys in the image_table. '''
        select = "SELECT "+UniqueImageClause()+" FROM "+p.image_table+" GROUP BY "+UniqueImageClause()
        return self.execute(select)
    
    
    def GetObjectCoords(self, obKey):
        ''' Returns the specified object's x, y coordinates in an image. '''
        select = 'SELECT '+p.cell_x_loc+', '+p.cell_y_loc+' FROM '+p.object_table+' WHERE '+GetWhereClauseForObjects([obKey])
        res = self.execute(select)
        assert len(res)>0, "Couldn't find object coordinates for object key %s." %(obKey,) 
        assert len(res)==1, "Database unexpectedly returned %s sets of object coordinates instead of 1." % len(res)
        return res[0]
    
    
    def GetAllObjectCoordsFromImage(self, imKey):
        ''' Returns a list of lists x, y coordinates for all objects in the given image. '''
        select = 'SELECT '+p.cell_x_loc+', '+p.cell_y_loc+' FROM '+p.object_table+' WHERE '+GetWhereClauseForImages([imKey])
        return self.execute(select)


    def GetObjectNear(self, imkey, x, y):
        ''' Returns obKey of the closest object to x, y in an image. '''
        delta_x = '(%s - %d)'%(p.cell_x_loc, x)
        delta_y = '(%s - %d)'%(p.cell_y_loc, y)
        dist_clause = '%s*%s + %s*%s'%(delta_x, delta_x, delta_y, delta_y)
        select = 'SELECT '+UniqueObjectClause()+' FROM '+p.object_table+' WHERE '+GetWhereClauseForImages([imkey])+' ORDER BY ' +dist_clause+' LIMIT 1'
        res = self.execute(select)
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
            filenames.append( imPaths[i]+'/'+imPaths[i+1] )
        return filenames


    def GetGroupMaps(self):
        ''' Build dictionary mapping group names and image keys to group keys. '''
        groupColNames = {}
        groupMaps = {}
        key_size = p.table_id and 2 or 1
        for group, query in p._groups.items():
            res = []
            try:
                res = self.execute(query)
            except Exception:
                raise Exception, 'Group query failed for group "%s". Check the MySQL syntax in your properties file.'%(group)
                continue
            groupColNames[group] = self.GetResultColumnNames()[key_size:]
            d = {}
            for row in res:
                d[row[:key_size]] = row[key_size:]
            groupMaps[group] = d
        return groupMaps, groupColNames
        
    
    def GetFilteredImages(self, filter):
        ''' Returns a list of imKeys from the given filter. '''
        try:
            return self.execute(p._filters[filter])
        except Exception, e:
            print e
            raise Exception, 'Filter query failed for filter "%s". Check the MySQL syntax in your properties file.'%(filter)
    
    
    def GetColumnNames(self, table):
        '''  Returns a list of the column names for the specified table. '''
        # NOTE: SQLite doesn't like DESCRIBE statements so we do it this way.
        self.execute('SELECT * FROM %s LIMIT 1'%(table))
        return self.GetResultColumnNames()   # return the column names
            

    def GetColumnTypes(self, table):
        ''' Returns the column types for the given table. '''
        res = self.execute('SELECT * from %s LIMIT 1'%(table), silent=True)
        return [type(x) for x in res[0]]


    def GetColnamesForClassifier(self):
        '''
        Returns a list of column names for the object_table excluding 
        those specified in Properties.classifier_ignore_substrings
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
            if p.classifier_ignore_substrings:
                self.classifierColNames = [col for col in self.classifierColNames
                                                if not any([re.match('^'+user_exp+'$',col)
                                                       for user_exp in p.classifier_ignore_substrings])]
            print 'Ignoring columns:',[x for x in col_names if x not in self.classifierColNames]
        return self.classifierColNames
    
    
    def GetResultColumnNames(self):
        ''' Returns the column names of the last query on this connection. '''
        connID = threading.currentThread().getName()
        return [x[0] for x in self.cursors[connID].description]
    
    
    def GetCellDataForClassifier(self, obKey):
        '''
        Returns a list of measurements for the specified object excluding
        those specified in Properties.classifier_ignore_substrings
        '''
        if (self.classifierColNames == None):
            self.GetColnamesForClassifier()
        query = 'SELECT %s FROM %s WHERE %s' %(','.join(self.classifierColNames), p.object_table, GetWhereClauseForObjects([obKey]))
        data = self.execute(query, silent=True)
        if len(data) == 0:
            print 'No data for obKey:',obKey
        return numpy.array(data[0])
    
    
    def GetPlateNames(self):
        '''
        Returns the names of each plate in the per-image table.
        '''
        res = self.execute('SELECT %s FROM %s GROUP BY %s'%(p.plate_id, p.image_table, p.plate_id))
        return [str(l[0]) for l in res]
    
    
    def InferColTypesFromData(self, reader, nCols):
        '''
        For converting csv data to DB data.
        Returns a list of column types (INT, FLOAT, or VARCHAR(#)) that each column can safely be converted to
        reader: csv reader
        nCols: # of columns  
        '''
        colTypes = []
        maxLen   = []   # Maximum string length for each column (if VARCHAR)
        for i in xrange(nCols):
            colTypes += ['']
            maxLen += [0]
        row = reader.next()
        while row:
            for i, e in enumerate(row):
                if colTypes[i]!='FLOAT' and not colTypes[i].startswith('VARCHAR'):
                    try:
                        x = int(e)
                        colTypes[i] = 'INT'
                        continue
                    except ValueError: pass
                if not colTypes[i].startswith('VARCHAR'):
                    try:
                        x = float(e)
                        colTypes[i] = 'FLOAT'
                        continue
                    except ValueError: pass
                try:
                    x = str(e)
                    maxLen[i] = max(len(x), maxLen[i])
                    colTypes[i] = 'VARCHAR(%d)'%(maxLen[i])
                except ValueError: 
                    raise Exception, '<ERROR>: Value in table could not be converted to string!'
            try:
                row = reader.next()
            except StopIteration: break
        return colTypes
            
    
    def CreateSQLiteDB(self):
        '''
        When the user specifies csv files as tables, we create an SQLite DB
        from those tables and do everything else the same.
        '''
        import csv
        # CREATE THE IMAGE TABLE
        # All the ugly code is to establish the type of each column in the table
        # so we can form a proper CREATE TABLE statement.
        f = open(p.image_csv_file, 'U')
        r = csv.reader(f)
        columnLabels = r.next()
        columnLabels = [lbl.strip() for lbl in columnLabels]
        colTypes = self.InferColTypesFromData(r, len(columnLabels))
        
        # Build the CREATE TABLE statement
        statement = 'CREATE TABLE '+p.image_table+' ('
        statement += ',\n'.join([lbl+' '+colTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
        
        print 'Creating table:', p.image_table
        self.execute('DROP TABLE IF EXISTS %s'%(p.image_table))
        self.execute(statement)
        
        # CREATE THE OBJECT TABLE
        # For the object table we assume that all values are type FLOAT
        # except for the primary keys
        f = open(p.object_csv_file, 'U')
        r = csv.reader(f)
        columnLabels = r.next()
        columnLabels = [lbl.strip() for lbl in columnLabels]
        colTypes = self.InferColTypesFromData(r, len(columnLabels))
        statement = 'CREATE TABLE '+p.object_table+' ('
        statement += ',\n'.join([lbl+' '+colTypes[i] for i, lbl in enumerate(columnLabels)])
        keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
        statement += ',\nPRIMARY KEY (' + keys + ') )'
        f.close()
    
        print 'Creating table:', p.object_table
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
        reader = csv.reader(f)#, quoting=csv.QUOTE_NONE)
        self.execute('DROP TABLE IF EXISTS %s'%(tablename))
        colnames = reader.next()
        colTypes = self.InferColTypesFromData(reader, len(colnames))
        coldefs = ', '.join([lbl+' '+colTypes[i] for i, lbl in enumerate(colnames)])
        self.execute('CREATE TEMPORARY TABLE %s (%s)'%(tablename, coldefs))
        f = open(filename, 'U')
        reader = csv.reader(f)#, quoting=csv.QUOTE_NONE)
        print 'Populating table %s...'%(tablename)
        row = reader.next() # skip col headers
        row = reader.next()
        while row:
            vals = ', '.join(['"'+val+'"' for val in row])
            self.execute('INSERT INTO %s (%s) VALUES (%s)'%(
                          tablename, ', '.join(colnames), vals), silent=True)
            try:
                row = reader.next()
            except StopIteration: break
        print 'Done.'
        self.Commit()
        f.close()
        return True
    
    
    def CheckTables(self):
        '''
        Queries the DB to check that the per_image and per_object
        tables agree on image numbers.
        '''
        # Check for index on image_table
        res = self.execute('SHOW INDEX FROM %s'%(p.image_table))
        idx_cols = [r[4] for r in res]
        for col in image_key_columns():
            assert col in idx_cols, 'Column "%s" is not indexed in table "%s"'%(col, p.image_table)
                
        # Check for index on object_table
        res = self.execute('SHOW INDEX FROM %s'%(p.object_table))
        idx_cols = [r[4] for r in res]
        for col in object_key_columns():
            assert col in idx_cols, 'Column "%s" is not indexed in table "%s"'%(col, p.object_table)
                
        # Explicitly check for TableNumber in case it was not specified in props file
        if ('TableNumber' not in object_key_columns()) and ('TableNumber' in idx_cols):
            raise 'Indexed column "TableNumber" was found in the database but not in your properties file.'
        
        # Check for orphaned objects
        res = self.execute('SELECT %s FROM %s LEFT JOIN %s USING (%s) WHERE %s.%s IS NULL'%
                           (UniqueImageClause(p.object_table), p.object_table, p.image_table, p.image_id, p.image_table, p.image_id))
        assert not any(res), 'Objects were found in "%s" that had no corresponding image key in "%s"'%(p.object_table, p.image_table)
            
        # Check for unlabeled wells
        if p.well_id:
            res = self.execute('SELECT %s FROM %s WHERE %s IS NULL OR %s=""'%
                               (UniqueImageClause(), p.image_table, p.well_id, p.well_id))        
            assert not any(res), 'Images were found in "%s" that had a NULL or empty "%s" column value'%(p.image_table, p.well_id)
        
        # Check for unlabeled plates
        if p.plate_id:
            res = self.execute('SELECT %s FROM %s WHERE %s IS NULL OR %s=""'%
                               (UniqueImageClause(), p.image_table, p.plate_id, p.plate_id))        
            assert not any(res), 'Images were found in "%s" that had a NULL or empty "%s" column value'%(p.image_table, p.plate_id)
    

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
        h = numpy.zeros(nbins)
        res = self.execute("select %s as bin, count(*) from %s "
                           "where %s <= %d "
                           "group by %s order by bin" % (clause, table_clause,
                                                         clause, nbins, clause))
        for bin, count in res:
            if bin == nbins:
                bin -= 1
            h[bin] = count
        return h, numpy.linspace(min, max, nbins + 1)


if __name__ == "__main__":

    from TrainingSet import TrainingSet
    import FastGentleBoostingMulticlass
    import MulticlassSQL
    from cStringIO import StringIO
    from DataModel import DataModel
    
    p = Properties.getInstance()
    db = DBConnect.getInstance()
    dm = DataModel.getInstance()

    p.LoadFile('../properties/nirht_test.properties')
    dm.PopulateModel()
    
    # TEST CreateTempTableFromCSV
    table = '_blah'
    db.CreateTempTableFromCSV('../test_data/test_per_image.txt', table)
    print db.execute('SELECT * from %s LIMIT 10'%(table))

    measurements = db.GetColumnNames(table)
    types = db.GetColumnTypes(table)
    print [m for m,t in zip(measurements, types) if t in[float, int, long]]

    print db.GetColumnNames(table)
    print db.GetColumnTypes(table)


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
