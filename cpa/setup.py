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
from subprocess import call

import util.version
f = open("util/frozen_version.py", "w")
f.write("# MACHINE_GENERATED\nversion_string = '%s'" % util.version.version_string)
f.close()

APPNAME = 'CellProfiler Analyst'
APP = ['cpa.py']
OPTIONS = {'argv_emulation': True,
           'iconfile' : "icons/cpa.icns",
           'includes' : [ 'scipy.sparse'],
           'packages' : ['numpy', 'icons', ],
           'excludes' : ['nose', 'wx.tools', 'Cython', 'pylab', 'Tkinter',
                         'scipy.weave', 'imagej'],
           'resources' : [],
          }

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name = APPNAME,
)
if sys.argv[-1] == 'py2app':
    a = "CellProfiler\\ Analyst" 
    call('find dist/{a}.app -name tests -type d | xargs rm -rf'.format(a=a), shell=True)
    call('lipo dist/{a}.app/Contents/MacOS/{a} -thin i386 -output dist/{a}.app/Contents/MacOS/{a}'.format(a=a), shell=True)

