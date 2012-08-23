"""Windows setup file
Delete build and dist folder from the cpa folder
Also delete previous version of setup.exe from the output folder
To invoke, from the command-line type change directory to ..\cpa and type the following command:
python windows_setup.py py2exe msi

This script will create three subdirectories
build: contains the collection of files needed during packaging
dist:  the contents that need to be given to the user to run ProtocolNavigator.
output: contains the .msi if you did the msi commmand
"""
from distutils.core import setup
import distutils.core
import distutils.errors
import py2exe
import sys
import glob
import subprocess
import re
import os
import _winreg
import matplotlib
import tempfile
import xml.dom.minidom
import util.version

vcredist = os.path.join("windows", "vcredist_x86.exe")
protocol_navigator_iss = "ProtocolNavigator.iss"
class CellProfilerMSI(distutils.core.Command):
    description = "Make ProtocolNavigator.msi using the ProtocolNavigator.iss InnoSetup compiler"
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        required_files = ["dist\\ProtocolNavigator.exe",protocol_navigator_iss]
        compile_command = self.__compile_command()
        compile_command = compile_command.replace("%1",protocol_navigator_iss)
        self.make_file(required_files,"Output\\"+"ProtocolNavigatorSetup.exe", 
                       subprocess.check_call,([compile_command]),
                       "Compiling %s" % protocol_navigator_iss)
        
    
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
            raise distutils.errors.DistutilsFileError, "Inno Setup does not seem to be installed properly. Specifically, there is no entry in the HKEY_CLASSES_ROOT for InnoSetupScriptFile\\shell\\Compile\\command"

opts = {
    'py2exe': { "includes" : ["PIL","wx"],
                'excludes': ['pylab','Tkinter','Cython'],
                'dll_excludes': ["msvcr90.dll", "msvcm90.dll", "msvcp90.dll"]
              },
    'msi': {}
       }
data_files = [('icons',
               ['icons\\%s'%(x) 
                for x in os.listdir('icons')
                if x.lower().endswith(".png") or x.lower().endswith(".psd")])]

#
# Call setup
#
setup(console=[{'script':'protocolnavigator.py'}],
      name='ProtocolNavigator',
      cmdclass={'msi':CellProfilerMSI
                },
      data_files = data_files,
      options=opts)
