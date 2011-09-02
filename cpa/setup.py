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
    

##import bioformats.tests.test_formatreader
##CP_EXAMPLE_IMAGES = '/Users/afraser/trunk/ExampleImages'
##os.environ['CP_EXAMPLEIMAGES'] = os.path.abspath(CP_EXAMPLE_IMAGES)
##retval = os.system(''' nosetests %s/bioformats/tests/test_formatreader.py --with-kill-vm '''%(CP_HOME))
##if retval != 0:
##    print 'nosetests failed. Aborting setup.py'
##    exit(1)

#
# Store version in cpa_version.py
# The CPA app will use this to determine version rather than svn
#
if sys.platform == "darwin":
    os.system(''' svnversion | sed -e's/^/VERSION = \"/' -e 's/[0-9]*://' -e 's/M//' -e 's/$/\"/' > cpa_version.py ''')
    
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

