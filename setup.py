import sys
if sys.platform == "darwin":
    from setuptools import setup, Extension
elif sys.platform == "win32":
    from distutils.core import setup
    import py2exe
    #
    # Perform a monkey-patch here to always do --skip-archive
    #
    import py2exe.build_exe
    old_initialize_options = py2exe.build_exe.py2exe.initialize_options
    def initialize_options(self, *args, **kwargs):
        old_initialize_options(self, *args, **kwargs)
        self.skip_archive = 1
    py2exe.build_exe.py2exe.initialize_options = initialize_options
import os
import os.path
import numpy
import verlib
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
OPTIONS = {'includes' : [ 
    'scipy.sparse.*', 'scipy.sparse.csgraph.*', 'scipy.integrate', 
    'scipy.special.*', 'scipy.linalg', 
    'verlib', 'traits', 'traitsui', 'traitsui.*', 'traitsui.wx', 'traitsui.wx.*',
    'pyface.*', 'pyface.wx.*', 'pyface.ui.wx', 'pyface.ui.wx.*',
    'pyface.ui.wx.grid.*', 'pyface.ui.wx.action.*', 'pyface.ui.wx.timer.*',
    'pyface.ui.wx.wizard.*', 'pyface.ui.wx.workbench.*',
    'tvtk.*', 'tvtk.pyface.*', 'tvtk.pyface.ui.*','tvtk.pyface.ui.wx.*',
    'tvtk.view.*',
    'enable.*', 'enable.wx.*'],
           'packages' : ['cpa', 'javabridge', 'bioformats'],
           'excludes' : ['nose', 'wx.tools', 'Cython', 'pylab', 'Tkinter',
                         'scipy.weave', 'imagej']
}
if sys.platform == "darwin":
    OPTIONS['packages'].append('numpy')
    OPTIONS['argv_emulation'] = True
    OPTIONS['plist'] = {
               "LSArchitecturePriority": ["i386"],
               "LSMinimumSystemVersion": "10.6.8",
               "CFBundleName": "CellProfiler Analyst",
               "CFBundleIdentifier": "org.cellprofiler.CellProfiler-Analyst",
               "CFBundleShortVersionString": cpa.util.version.get_bundle_version(),
            }
    OPTIONS['iconfile'] = "cpa/icons/cpa.icns"
    OPTIONS['resources'] = []
    packager = 'py2app'
    setup(
        app=APP,
        version=cpa.util.version.get_normalized_version(),
        options={packager: OPTIONS},
        setup_requires=[packager],
        name = APPNAME,
    )
elif sys.platform == "win32":
    import matplotlib
    import cpa.icons
    import mayavi.preferences
    import tvtk.plugins.scene
    
    packager = 'py2exe'
    OPTIONS['dll_excludes']=["MSVCP90.dll", "jvm.dll"]
    data_files = matplotlib.get_py2exe_datafiles()
    icon_path = os.path.dirname(cpa.icons.__file__)
    data_files.append(('cpa/icons', [
        os.path.join(icon_path, f) for f in os.listdir(icon_path) 
        if f.endswith(".png")]))
    #
    # VTK and Mayavi default preferences file
    #
    pref = 'preferences.ini'
    for pkg in mayavi.preferences, tvtk.plugins.scene:
        src_path = os.path.join(os.path.dirname(pkg.__file__), pref)
        dest_dir = pkg.__name__.replace(".", os.path.sep)
        data_files.append((dest_dir, [src_path]))
    import tvtk
    src_path = tvtk.tvtk_class_dir + ".zip"
    data_files.append(("tvtk", [src_path]))
    #
    # Mayavi color palettes
    #
    import mayavi.core.lut
    src_dir = os.path.dirname(mayavi.core.lut.__file__)
    dest_dir = "mayavi\\core\\lut"
    data_files.append((dest_dir, [
        os.path.join(src_dir, filename) for filename in os.listdir(src_dir)
        if any([filename.endswith(ext) for ext in ".gif", ".pkl", ".txt"])]))
    #
    # Mayavi images
    #
    import mayavi.core
    import mayavi.core.ui
    for package in mayavi.core, mayavi.core.ui:
        src_dir = os.path.join(os.path.dirname(package.__file__), "images")
        dest_dir = os.path.join(
            *(list(package.__name__.split(".")) + ["images"]))
        data_files.append((dest_dir, [
            os.path.join(src_dir, filename) for filename in os.listdir(src_dir)]))
    #
    # traitsui image libraries and traitsui.wx images
    #
    import traitsui.image
    src_dir = os.path.join(os.path.dirname(traitsui.image.__file__), "library")
    dest_dir = "traitsui\\image\\library"
    data_files.append((dest_dir, [
        os.path.join(src_dir, filename) for filename in os.listdir(src_dir)
        if filename.endswith(".zip")]))
    import traitsui.wx
    src_dir = os.path.join(os.path.dirname(traitsui.wx.__file__), "images")
    dest_dir = "traitsui\\wx\\images"
    data_files.append((dest_dir, [
        os.path.join(src_dir, filename) for filename in os.listdir(src_dir)]))
    #
    # pyface images
    #
    import pyface
    src_dir = os.path.join(os.path.dirname(pyface.__file__), "images")
    dest_dir = "pyface\\images"
    data_files.append((dest_dir, [
        os.path.join(src_dir, filename) for filename in os.listdir(src_dir)]))
    #
    # tvtk pyface images
    #
    import tvtk.pyface
    src_dir = os.path.join(os.path.dirname(tvtk.pyface.__file__), "images")
    dest_dir = "tvtk\\pyface\\images"
    for dirname in os.listdir(src_dir):
        src_subdir = os.path.join(src_dir, dirname)
        if os.path.isdir(src_subdir):
            data_files.append((os.path.join(dest_dir, dirname), [
                os.path.join(src_subdir, filename) 
                for filename in os.listdir(src_subdir)]))
    #
    # Javabridge and bioformats jars
    #
    import javabridge
    import bioformats
    for package in javabridge, bioformats:
        src_dir = os.path.join(os.path.dirname(package.__file__), "jars")
        dest_dir = os.path.join(package.__name__, "jars")
        data_files.append(
            (dest_dir, [os.path.join(src_dir, filename)
                        for filename in os.listdir(src_dir)
                        if filename.endswith(".jar")]))
                           
    
                                                   
    dist = setup(
        console=APP,
        version=cpa.util.version.get_normalized_version(),
        options={packager: OPTIONS},
        name = APPNAME,
        data_files=data_files
    )

if sys.argv[-1] == 'py2app':
    a = "CellProfiler\\ Analyst" 
    call('find dist/{a}.app -name tests -type d | xargs rm -rf'.format(a=a), shell=True)
    call('lipo dist/{a}.app/Contents/MacOS/{a} -thin i386 -output dist/{a}.app/Contents/MacOS/{a}'.format(a=a), shell=True)

