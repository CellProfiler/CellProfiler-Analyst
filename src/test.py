
import sys
from properties import Properties
import dbconnect
from pysqlite2 import dbapi2 as sqlite


# Load the properties file

p = Properties.getInstance()
sys.stdout.write('Properties file >>> ')
#fname = sys.stdin.readline().strip()
p.LoadFile('/Users/afraser/Desktop/cpa_example/example.properties')#fname)


# Connect to the DB

db = dbconnect.DBConnect.getInstance()
db.connect()
print p.db_sqlite_file


# Merge in data from E2DB or other SQLite DB?

print '''Where are the tables you would like to merge into this database:
    (1) CSV files from CellProfiler's ExportToDatabase module
    (2) Another SQLite database
>>> '''
ans = sys.stdin.readline().strip()
if ans==1:
    prompt_for_sql_file()
elif ans==2:
    prompt_for_sqlite_file()
else:
    raise 'Invalid selection!'


#
def find_image_and_object_table(tables):
    '''Attempts to pick out the image and object table from a list of tables.'''
    per_image = None
    per_object = None
    for t in tables:
        if 'image' in t.lower():
            if per_image:
                raise 'Too many tables with "image" in their name.'
                return
            per_image = t
        if 'object' in t.lower():
            if per_object:
                raise 'Too many tables with "object" in their name.'
                return
            per_object = t
    if not per_image:
        raise 'No tables with "image" in their name.'
    if not per_object:
        raise 'No tables with "object" in their name.'
    return per_image, per_object
        

def merge_sqlite_files(files, outfile):
    out_conn = sqlite.connect(outfile)
    out_cur  = out_conn.cursor()
    conns    = [sqlite.connect(f) for f in files]
    cursors  = [c.cursor() for c in conns]

    tables = [t[0] for t in out_cur.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')]
    out_per_image, out_per_object = find_image_and_object_table(tables)
    
    for cur in cursors:
        tables = [t[0] for t in cur.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')]
        per_image, per_object = find_image_and_object_table(tables)
        cur.execute('INSERT INTO '+out_per_image+' SELECT *,'+str(i)+' FROM '+per_image)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        