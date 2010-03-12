from setuptools import setup, Extension
import sys
import os
import os.path
import numpy
import glob

# fix from
#  http://mail.python.org/pipermail/pythonmac-sig/2008-June/020111.html
import pytz
pytz.zoneinfo = pytz.tzinfo
pytz.zoneinfo.UTC = pytz.UTC

import PILfix

if sys.platform == "darwin":
    os.system(''' svnversion | sed -e's/^/VERSION = \"/' -e 's/[0-9]*://' -e 's/M//' -e 's/$/\"/' > cpa_version.py ''')

APPNAME = 'CellProfiler Analyst'
APP = ['cpa.py']
DATA_FILES = []
OPTIONS = {'argv_emulation': True,
           'iconfile': "icons/cpa.icns",
           'packages': ['numpy', './icons'],
           'excludes': ['nose', 'wx.tools'],
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name = "CellProfiler Analyst",
)

