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
import cpa.pilfix
from subprocess import call

import cpa.util.version

APPNAME = 'CellProfiler Analyst'
APP = ['CellProfiler-Analyst.py']
OPTIONS = {'argv_emulation': True,
           'iconfile' : "cpa/icons/cpa.icns",
           'includes' : [ 'scipy.sparse'],
           'packages' : ['numpy', 'cpa', 'javabridge', 'bioformats', 'PIL','sklearn'],
           'excludes' : ['nose', 'wx.tools', 'Cython', 'pylab', 'Tkinter',
                         'scipy.weave', 'imagej','AppKit','CoreFoundation','Foundation','objc'],
           'resources' : []
           # 'plist': {
           #     "LSArchitecturePriority": ["x86_64"]
           #     "LSMinimumSystemVersion": "10.6.8",
           #     "CFBundleName": "CellProfiler Analyst",
           #     "CFBundleIdentifier": "org.cellprofiler.CellProfiler-Analyst",
           #     "CFBundleShortVersionString": cpa.util.version.get_bundle_version(),
            # }
}

setup(
    app=APP,
    version=cpa.util.version.get_normalized_version(),
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name = APPNAME,
)
# if sys.argv[-1] == 'py2app':
#     a = "CellProfiler\\ Analyst" 
#     call('find dist/{a}.app -name tests -type d | xargs rm -rf'.format(a=a), shell=True)
#     call('lipo dist/{a}.app/Contents/MacOS/{a} -thin i386 -output dist/{a}.app/Contents/MacOS/{a}'.format(a=a), shell=True)

