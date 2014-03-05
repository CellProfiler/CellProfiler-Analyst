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


CP_HOME = os.getenv('CP_HOME') or '../../CellProfiler/'
if not os.path.exists(CP_HOME):
    raise Exception('CellProfiler source not found. Edit CP_HOME in setup.py or set the CP_HOME environment variable')
else:
    sys.path.append(CP_HOME)
    

##import bioformats.tests.test_formatreader
##CP_EXAMPLE_IMAGES = '/Users/afraser/trunk/ExampleImages'
##os.environ['CP_EXAMPLEIMAGES'] = os.path.abspath(CP_EXAMPLE_IMAGES)
##retval = os.system(''' nosetests %s/bioformats/tests/test_formatreader.py --with-kill-vm '''%(CP_HOME))
##if retval != 0:
##    print 'nosetests failed. Aborting setup.py'
##    exit(1)

import util.version
f = open("util/frozen_version.py", "w")
f.write("# MACHINE_GENERATED\nversion_string = '%s'" % util.version.version_string)
f.close()

APPNAME = 'CPAnalyst'
APP = ['cpa.py']
DATA_FILES = [# needed for cpfigure used by classifier cross validation
              ('cellprofiler/icons', 
               [os.path.join(CP_HOME, 'cellprofiler/icons/CellProfilerIcon.png')]), 
             ]
for dest, paths in DATA_FILES:
    for path in paths:
        assert os.path.isfile(path), "%s does not exist" % path
OPTIONS = {'argv_emulation': True,
           'iconfile' : "icons/cpa.icns",
           'includes' : [ 'scipy.sparse'],
           'packages' : ['numpy', './icons', 'killjavabridge', ],
           'excludes' : ['nose', 'wx.tools', 'Cython', 'pylab', 'Tkinter',
                         'scipy.weave', 'imagej'],
           'resources' : [],
          }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name = APPNAME,
)
if sys.argv[-1] == 'py2app':
    call('find dist/%(APPNAME)s.app -name tests -type d | xargs rm -rf'%globals(), shell=True)
    call('lipo dist/%(APPNAME)s.app/Contents/MacOS/%(APPNAME)s -thin i386 -output dist/%(APPNAME)s.app/Contents/MacOS/%(APPNAME)s' % globals(), shell=True)

