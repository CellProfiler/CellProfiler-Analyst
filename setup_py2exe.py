# =============================================================================
#
#   Mac OS build file for CellProfiler-Analyst
#
#   Run python setup_py2exe.py to build a dist file containing Windows binaries
#
# =============================================================================

import distutils
import sys
import setuptools
import py2exe
import matplotlib
import os
import os.path
import glob
import numpy
import subprocess
import _winreg
import javabridge
import bioformats
from shutil import rmtree


import cpa.util.version

# Recipe needed to get real distutils if virtualenv.
# Error message is "ImportError: cannot import name dist"
# when running app.
# See http://sourceforge.net/p/py2exe/mailman/attachment/47C45804.9030206@free.fr/1/
#
if hasattr(sys, 'real_prefix'):
    # Running from a virtualenv
    assert hasattr(distutils, 'distutils_path'), \
        "Can't get real distutils path"
    libdir = os.path.dirname(distutils.distutils_path)
    sys.path.insert(0, libdir)
    #
    # Get the system "site" package, not the virtualenv one. This prevents
    # site.virtual_install_main_packages from being called, resulting in
    # "IOError: [Errno 2] No such file or directory: 'orig-prefix.txt'
    #
    del sys.modules["site"]
    import site

    assert not hasattr(site, "virtual_install_main_packages")


#
# These imports help distutils discover modules
#
import scipy.sparse.csgraph._validation
import scipy.linalg

class CellProfilerAnalystMSI(distutils.core.Command):
    description = "Make CellProfilerAnalyst.msi using InnoSetup"
    user_options = []
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        fd = open("version.iss", "w")
        fd.write("""
AppVerName=CellProfiler %d
OutputBaseFilename=CellProfilerAnalyst_win32_%d
""" % (cpa.util.version._semantic_version, cpa.util.version._semantic_version))
        fd.close()
        required_files = os.path.join("dist", "cpa.exe")
        compile_command = self.__compile_command()
        compile_command = compile_command.replace("%1", "CellProfilerAnalyst.iss")
        self.make_file(
            required_files,
            os.path.join("Output", "CellProfilerAnalyst_win32_r%d.exe" % 
                         cpa.util.version._semantic_version),
            subprocess.check_call, ([compile_command]))
        
    def __compile_command(self):
        """Return the command to use to compile an .iss file
        """
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, 
                                   "InnoSetupScriptFile\\shell\\Compile\\command")
            result = _winreg.QueryValueEx(key,None)[0]
            key.Close()
            return result
        except WindowsError:
            if key:
                key.Close()
            raise distutils.errors.DistutilsFileError("Inno Setup does not seem to be installed properly. "
                                                      "Specifically, there is no entry in the HKEY_CLASSES_ROOT "
                                                      "for InnoSetupScriptFile\\shell\\Compile\\command")

# if os.path.exists('build'):
#    raise Exception("Please delete the build directory before running setup.")
if os.path.exists('dist'):
    rmtree('./dist')

if os.path.exists('build'):
    rmtree('./build')
  #raise Exception("Please delete the dist directory before running setup.")
#
# Write the frozen version
#
f = open("cpa/util/frozen_version.py", "w")
f.write("# MACHINE_GENERATED\nversion_string = '%s'" % cpa.util.version._semantic_version)
f.close()

setuptools.setup(
    name="cellprofiler-analyst",
    windows=[{'script':'CellProfiler-Analyst.py',
                'icon_resources':[(1,'.\cpa\icons\cpa.ico')]}],
    options={
        'py2exe': {
            'skip_archive' : 1,
            'includes' : [
                'scipy.linalg.*',
                'scipy.special',
                'scipy.special.*',
                'scipy.sparse.csgraph._validation',
                'skimage.draw',
                'skimage._shared.geometry',
                'sklearn.*',
                'sklearn.neighbors.*',
                'sklearn.tree.*',
                'sklearn.utils.*',
                'sklearn.utils.sparsetools.*',
                'cpa.pilfix', 
                "xml.etree.cElementTree", 
                "xml.etree.ElementTree"
                ],
            "excludes" : ['_gtkagg', '_tkagg', "nose",
                          "wx.tools", "pylab", "scipy.weave",
                          "Tkconstants","Tkinter", "tcl",
                          "Cython", 'h5py',
                          'PyQt4', 'zmq','AppKit','CoreFoundation','objc',
                          'matplotlib.tests',
                          'matplotlib.backends.backend_tk*'],
            "dll_excludes": [
                'libgdk-win32-2.0-0.dll',
                'libgobject-2.0-0.dll', 
                'libgdk_pixbuf-2.0-0.dll',
                'tcl84.dll', 
                'tk84.dll', 
                'jvm.dll', 
                'MSVCP90.dll',
                'crypt32.dll',
                'iphlpapi.dll',
                'kernelbase.dll',
                'mpr.dll',
                'msasn1.dll',
                'msvcr90.dll',
                'msvcm90.dll',
                'msvcp90.dll',
                'nsi.dll',
                'uxtheme.dll',
                'winnsi.dll'],
            }
        },
      install_requires=[
          "javabridge", "matplotlib", "MySQL-python", "numpy",
          "python-bioformats", "scipy"],
      include_package_data=True,
      packages = setuptools.find_packages(
          exclude = [
              "*.tests",
              "*.tests.*",
              "tests.*",
              "tests"]
          ) + ["cpa.icons"],
      data_files=(
              matplotlib.get_py2exe_datafiles() +
              [('cpa\\icons', glob.glob('cpa\\icons\\*.png')),
              ('javabridge\\jars',javabridge.JARS),
              ('bioformats\\jars',bioformats.JARS)
              ]
            ),
      cmdclass={"msi":CellProfilerAnalystMSI}
)
