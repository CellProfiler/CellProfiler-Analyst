import wx
import string
import numpy
from DBConnect import DBConnect
import MySQLdb
from MySQLdb.cursors import SSCursor
import exceptions
import threading



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

db = DBConnect.getInstance()
db.Connect(db_host="imgdb01", db_name="cells", db_user="cpadmin", db_passwd="cPus3r")

EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    win.Connect(-1, -1, EVT_RESULT_ID, func)
   
class ResultEvent(wx.PyEvent):
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class Worker(threading.Thread):
    def __init__(self, notify_window, query, id):
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self.query = query
        self.ID = id
        self.start()

    def run(self):
        db.Execute(self.query)
        res = db.GetResultsAsList()
        wx.PostEvent(self._notify_window, ResultEvent((self.ID, res)))
        
        
class Querifier(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=-1)
        EVT_RESULT(self, self.OnResult)
    
    def go(self):
        workers = []
        for i in xrange(1):
            q = 'SELECT ImageNumber FROM per_image WHERE ImageNumber=%s' %( i+1 ) 
            w = Worker(self, query=q, id=i)
            workers.append( w )
            
    def OnResult(self, evt):
        print 'results:', str(evt.data)

app = wx.PySimpleApp()
qwer = Querifier()
qwer.go()
app.MainLoop()

    
    
    
    