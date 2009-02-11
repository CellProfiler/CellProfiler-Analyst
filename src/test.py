import wx
import string
import numpy
from DBConnect import DBConnect
import MySQLdb
from MySQLdb.cursors import SSCursor
import exceptions
import threading
import re
from Properties import Properties
from pysqlite2 import dbapi2 as sqlite
import csv
import os

p = Properties.getInstance()
p.LoadFile('../properties/nirht_local.properties')


def CreateSQLiteTables():
    
    # CREATE THE IMAGE TABLE
    f = open(p.image_csv_file, 'r')
    r = csv.reader(f)
    # Establish the type of each column in the table
    columnLabels = r.next()
    columnLabels = [lbl.strip() for lbl in columnLabels]
    row = r.next()
    rowTypes = {}
    for i in xrange(len(columnLabels)):
        rowTypes[i]=''
    maxLen = 1      # Maximum string length
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
                maxLen = max(len(x), maxLen)
                rowTypes[i] = 'VARCHAR(%d)'%(maxLen)
            except ValueError: 
                raise Exception, '<ERROR>: Value in table could not be converted to string!'
        try:
            row = r.next()
        except StopIteration: break
    statement = 'CREATE TABLE '+os.path.splitext(os.path.split(p.image_table)[1])[0]+' ('
    statement += ',\n'.join([lbl+' '+rowTypes[i] for i, lbl in enumerate(columnLabels)])
    keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
    statement += ',\nPRIMARY KEY (' + keys + ') )'
    f.close()
    
    cursor.execute('DROP TABLE IF EXISTS %s'%p.image_table)
    cursor.execute(statement)
    
    # CREATE THE OBJECT TABLE
    # for the object table we assume that all values are FLOAT
    # except for the keys
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
    statement = 'CREATE TABLE '+os.path.splitext(os.path.split(p.object_table)[1])[0]+' ('
    statement += ',\n'.join([lbl+' '+rowTypes[i] for i, lbl in enumerate(columnLabels)])
    keys = ','.join([x for x in [p.table_id, p.image_id, p.object_id] if x in columnLabels])
    statement += ',\nPRIMARY KEY (' + keys + ') )'
    f.close()

#    cursor.execute('DROP TABLE IF EXISTS %s'%p.object_table)
#    cursor.execute(statement)






# Create the SQLite DB
conn = sqlite.connect('test.db')
#conn = sqlite.connect(':memory:')
cursor = conn.cursor()

# Create the tables
CreateSQLiteTables()

# Insert values from the file into the table
f = open(p.image_csv_file, 'r')
r = csv.reader(f)
row = r.next() # skip the headers
row = r.next()
while row: 
    cursor.execute('INSERT INTO '+os.path.splitext(os.path.split(p.image_table)[1])[0]+' VALUES ('+','.join(["'%s'"%(i) for i in row])+')')
    try:
        row = r.next()
    except StopIteration:
        break
f.close()

# QUERY THE DB
cursor.execute('SELECT * FROM %s LIMIT 1'%(os.path.splitext(os.path.split(p.image_table)[1])[0]))
print cursor.fetchall()

cursor.execute('CREATE TEMPORARY TABLE temp.db (column1 INTEGER)')
cursor.execute('INSERT INTO temp.db ("column1") VALUES (1234)')
cursor.execute('SELECT * FROM temp.db')
print cursor.fetchall()




#
# Q? What happens when Execute is called again before results are read?
# A: Results from the second query overwrite the results from the first query.
#
#db = DBConnect.getInstance()
#
#db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r")
#
#q = 'SELECT ImageNumber FROM per_image LIMIT 10'
#q2 = 'SELECT well FROM per_image LIMIT 10'
#
#db.Execute(q)
#db.Execute(q2)
#
#print db.GetResultsAsList()
#print db.GetResultsAsList()





#
# Q? What if many cursors are used?
# A: "Commands out of sync; you can't run this command now"

#connection = MySQLdb.connect(host='imgdb01', db='cells', user='cpadmin', passwd='cPus3r')
#
#cursor  = SSCursor(connection)
#cursor2 = SSCursor(connection)
#
#cursor.execute('SELECT ImageNumber FROM per_image LIMIT 10')
#cursor2.execute('SELECT well FROM per_image LIMIT 10')
#
#l  = []
#l2 = []
#
#while r:
#    try:
#        r = cursor.next()
#        r2 = cursor2.next()
#    except MySQLdb.Error, e:
#        print "Error retrieving next result from database."
#        r = None
#    except StopIteration, e:
#        r = None
#    if r:
#       l.append(r)
#       l2.append(r2)
#print l





#
# What if we bombard the DB with calls from many threads?
#
# Try this with normal DBConnect, then modify DBConnect.Execute to recurse if it fails.

#db = DBConnect.getInstance()
#db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r")
#
#EVT_RESULT_ID = wx.NewId()
#
#def EVT_RESULT(win, func):
#    win.Connect(-1, -1, EVT_RESULT_ID, func)
#   
#class ResultEvent(wx.PyEvent):
#    def __init__(self, data):
#        wx.PyEvent.__init__(self)
#        self.SetEventType(EVT_RESULT_ID)
#        self.data = data
#
#class Worker(threading.Thread):
#    def __init__(self, notify_window, query, id):
#        threading.Thread.__init__(self)
#        self._notify_window = notify_window
#        self.query = query
#        self.ID = id
#        self.start()
#
#    def run(self):
#        db.Execute(self.query)
#        res = db.GetResultsAsList()
#        wx.PostEvent(self._notify_window, ResultEvent((self.ID, res)))
#        
#        
#class Querifier(wx.Frame):
#    def __init__(self):
#        wx.Frame.__init__(self, parent=None, id=-1)
#        EVT_RESULT(self, self.OnResult)
#    
#    def go(self):
#        workers = []
#        for i in xrange(1):
#            q = 'SELECT ImageNumber FROM per_image WHERE ImageNumber=%s' %( i+1 ) 
#            w = Worker(self, query=q, id=i)
#            workers.append( w )
#            
#    def OnResult(self, evt):
#        print 'results:', str(evt.data)
#
#app = wx.PySimpleApp()
#qwer = Querifier()
#qwer.go()
#app.MainLoop()
#
#    
    
    
    