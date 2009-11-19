from setuptools import setup, Extension
import sys, os

# fix from
#  http://mail.python.org/pipermail/pythonmac-sig/2008-June/020111.html
import pytz
pytz.zoneinfo = pytz.tzinfo
pytz.zoneinfo.UTC = pytz.UTC

import PILfix

if sys.platform == "darwin":
    os.system("svn info | grep Revision | sed -e 's/Revision:/\"Version/' -e 's/^/VERSION = /' -e 's/$/\"/' > version.py")

APPNAME = 'CPAnalyst'
APP = ['cpa.py']
DATA_FILES = []
OPTIONS = {'argv_emulation': False,
           #'iconfile': "wormprofiler_icons/%s.icns" % APPNAME,
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
                             libraries = ['sqlite3'])]
                             
)

