import distutils
import sys
from distutils.core import setup, Extension
import py2exe
import matplotlib
import os
import os.path
import glob
import numpy
import subprocess
import _winreg

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
AppVerName=CellProfiler 2.0 r%s
OutputBaseFilename=CellProfilerAnalyst_win32_r%s
""" % (cpa_version.VERSION, cpa_version.VERSION))
        fd.close()
        required_files = os.path.join("dist", "cpa.exe")
        compile_command = self.__compile_command()
        compile_command = compile_command.replace("%1", "CellProfilerAnalyst.iss")
        self.make_file(
            required_files,
            os.path.join("Output", "CellProfilerAnalyst_win32_r%s.exe" % cpa_version.VERSION),
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
            raise DistutilsFileError, "Inno Setup does not seem to be installed properly. Specifically, there is no entry in the HKEY_CLASSES_ROOT for InnoSetupScriptFile\\shell\\Compile\\command"

    
CP_HOME = '../../CellProfiler/'
if not os.path.exists(CP_HOME):
    raise Exception('CellProfiler source not found. Edit CP_HOME in setup.py')
    exit(1)
else:
    sys.path.append(CP_HOME)

#
# Write version to cpa_version.py so CPA.exe can determine version.
#
s = os.popen('svnversion')
version = s.read()
f = open('cpa_version.py', 'w')
f.write('VERSION = "%s"\n'%("".join([v for v in version.strip() if v in '0123456789'])))
f.close()
import cpa_version

if not 'py2exe' in sys.argv:
    sys.argv.append('py2exe')

setup(windows=[{'script':'cpa.py',
				'icon_resources':[(1,'.\icons\cpa.ico')]}],
      options={
        'py2exe': {
            'packages' : ['matplotlib', 'pytz', 'MySQLdb', 'icons',
                          'bioformats', 'killjavabridge'],
            'includes' : ['pilfix', "xml.etree.cElementTree", "xml.etree.ElementTree"],
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
      data_files=(
              matplotlib.get_py2exe_datafiles() +
              [('icons', glob.glob('icons\\*.png')),
               ('bioformats', [CP_HOME+'bioformats/loci_tools.jar']),
               ('cellprofiler/icons', [CP_HOME+'cellprofiler/icons/CellProfilerIcon.png']), # needed for cpfigure used by classifier cross validation
              ]
            ),
      cmdclass={"msi":CellProfilerAnalystMSI}
)
