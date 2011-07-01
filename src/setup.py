from setuptools import setup, Extension
import sys
import os
import os.path
import numpy
# fix from
#  http://mail.python.org/pipermail/pythonmac-sig/2008-June/020111.html
import pytz
pytz.zoneinfo = pytz.tzinfo
pytz.zoneinfo.UTC = pytz.UTC
import pilfix


CP_HOME = '../../CellProfiler/'
if not os.path.exists(CP_HOME):
    raise Exception('CellProfiler source not found. Edit CP_HOME in setup.py')
else:
    sys.path.append(CP_HOME)

APPNAME = 'CPAnalyst'
APP = ['cpa.py']
DATA_FILES = [('bioformats', [CP_HOME+'bioformats/loci_tools.jar']),
              ('cellprofiler/icons', [CP_HOME+'cellprofiler/icons/CellProfilerIcon.png']), # needed for cpfigure used by classifier cross validation
             ]
OPTIONS = {'argv_emulation': True,
           'iconfile' : "icons/cpa.icns",
           'includes' : [ ],
           'packages' : ['numpy', './icons', 'bioformats', 'killjavabridge', ],
           'excludes' : ['nose', 'wx.tools', 'Cython', 'pylab', 'Tkinter',
                         'scipy.weave', 'imagej'],
           'resources' : [],
          }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name = "CPAnalyst",
)

