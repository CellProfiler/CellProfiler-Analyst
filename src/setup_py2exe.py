import sys
sys.path.append('../../CellProfiler')
from distutils.core import setup, Extension
import py2exe
import matplotlib
import os
import os.path
import glob
import numpy

#
# Write version to cpa_version.py so CPA.exe can determine version.
#
s = os.popen('svnversion')
version = s.read()
f = open('cpa_version.py', 'w')
f.write('VERSION = "%s"\n'%("".join([v for v in version.strip() if v in '0123456789'])))
f.close()

if not 'py2exe' in sys.argv:
    sys.argv.append('py2exe')

setup(windows=['cpa.py'],
      options={
        'py2exe': {
            'packages' : ['matplotlib', 'pytz', 'MySQLdb'],
            'includes' : ['pilfix'],
            "excludes" : ['_gtkagg', '_tkagg', "nose",
                          "wx.tools", "pylab", "scipy.weave",
                          "Tkconstants","Tkinter","tcl",
                          "Cython", "imagej", 'h5py', 'vigra',
                          'PyQt4'],
            "dll_excludes": ['libgdk-win32-2.0-0.dll',
                             'libgobject-2.0-0.dll', 
                             'libgdk_pixbuf-2.0-0.dll',
                             'tcl84.dll', 'tk84.dll', 'jvm.dll'],
            }
        },
      data_files=(matplotlib.get_py2exe_datafiles()+
              [('icons', glob.glob('icons\\*.png'))]),
)
