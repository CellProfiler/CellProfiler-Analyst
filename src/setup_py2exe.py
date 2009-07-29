from distutils.core import setup
import py2exe
import matplotlib

setup(console=['ClassifierGUI.py'],
      options={
        'py2exe': {
            'packages' : ['matplotlib', 'pytz', 'MySQLdb', 'pysqlite2'],
            "excludes": ['_gtkagg', '_tkagg', 
                         "Tkconstants","Tkinter","tcl"],
            "dll_excludes": ['libgdk-win32-2.0-0.dll',
                             'libgobject-2.0-0.dll', 
                             'libgdk_pixbuf-2.0-0.dll',
                             'tcl84.dll', 'tk84.dll']
            }
        },
      data_files=matplotlib.get_py2exe_datafiles(),
)



