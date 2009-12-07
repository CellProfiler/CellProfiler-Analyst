from distutils.core import setup, Extension
import py2exe
import matplotlib
import os
import numpy

s = os.popen('svnversion')
version = s.read()
f = open('cpa_version.py', 'w')
f.write('VERSION = "%s"\n'%(version.strip()))
f.close()



setup(console=['cpa.py'],
      options={
        'py2exe': {
            'packages' : ['matplotlib', 'pytz', 'MySQLdb', 'pysqlite2'],
            'includes' : ['PILfix', 'version'],
            "excludes" : ['_gtkagg', '_tkagg',
                          "Tkconstants","Tkinter","tcl"],
            "dll_excludes": ['libgdk-win32-2.0-0.dll',
                             'libgobject-2.0-0.dll', 
                             'libgdk_pixbuf-2.0-0.dll',
                             'tcl84.dll', 'tk84.dll']
            }
        },
      data_files=matplotlib.get_py2exe_datafiles(),
      ext_modules = [Extension('_classifier',
                               sources = ['_classifier.c'],
                               include_dirs=[numpy.get_include()],
                               libraries = ['sqlite3dll'])]
)



