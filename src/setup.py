from setuptools import setup, Extension
import sys, os
import numpy

# fix from
#  http://mail.python.org/pipermail/pythonmac-sig/2008-June/020111.html
import pytz
pytz.zoneinfo = pytz.tzinfo
pytz.zoneinfo.UTC = pytz.UTC

import PILfix

if sys.platform == "darwin":
    os.system(''' svnversion | sed -e's/^/VERSION = \"/' -e 's/[0-9]*://' -e 's/M//' -e 's/$/\"/' > cpa_version.py ''')

APPNAME = 'CPAnalyst'
APP = ['cpa.py']
DATA_FILES = []
OPTIONS = {'argv_emulation': False,
           'iconfile': "../resources/cpa.icns",
           'packages': ['numpy'],
           'excludes': ['pylab', 'nose', 'wx.tools'],
           'resources': ['FastGentleBoostingWorkerMulticlass.py'],
#           'resources':['wormprofiler_icons/WormProfiler_icon_32.png', 'change_malloc_zone.dylib']
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name = "CPAnalyst",
    ext_modules = [Extension('_classifier',
                             sources = ['_classifier.c'],
                             include_dirs=[numpy.get_include()],
                             libraries = ['sqlite3'])]
                             
)

