import sys
sys.path.append('../../CellProfiler/pyCellProfiler')
from distutils.core import setup, Extension
import py2exe
import matplotlib
import os
import os.path
import glob
import numpy

s = os.popen('svnversion')
version = s.read()
f = open('cpa_version.py', 'w')
f.write('VERSION = "%s"\n'%("".join([v for v in version.strip() if v in '0123456789'])))
f.close()

if not 'py2exe' in sys.argv:
    sys.argv.append('py2exe')

setup(console=['cpa.py'],
      options={
        'py2exe': {
            'packages' : ['matplotlib', 'pytz', 'MySQLdb', 'pysqlite2'],
            'includes' : ['PILfix'],
            "excludes" : ['_gtkagg', '_tkagg',
                          "Tkconstants","Tkinter","tcl"],
            "dll_excludes": ['libgdk-win32-2.0-0.dll',
                             'libgobject-2.0-0.dll', 
                             'libgdk_pixbuf-2.0-0.dll',
                             'tcl84.dll', 'tk84.dll'],
            }
        },
      data_files=(matplotlib.get_py2exe_datafiles()+
              [('icons', glob.glob('icons\\*.png'))]),
)
