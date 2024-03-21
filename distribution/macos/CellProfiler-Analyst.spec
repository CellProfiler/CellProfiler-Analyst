# -*- mode: python ; coding: utf-8 -*-

import os
import os.path

import PyInstaller.compat
import PyInstaller.utils.hooks

binaries = []

block_cipher = None

datas = []

datas += PyInstaller.utils.hooks.collect_data_files("bioformats")
datas += PyInstaller.utils.hooks.collect_data_files("javabridge")

datas += [
    ("../../cpa/icons/*", "cpa/icons"),
]

for subdir, dirs, files in os.walk(os.environ["JAVA_HOME"]):
    if 'Contents/' in subdir:
        if len(subdir.split('Contents/')) >1:
            _, subdir_split = subdir.split('Contents/')
            for file in files:
                datas += [(os.path.join(subdir, file), subdir_split)]

hiddenimports = []

hiddenimports += PyInstaller.utils.hooks.collect_submodules('sklearn.utils')
hiddenimports += ['cmath']

excludes = []

excludes += [
    "PyQt5.QtGui",
    "PyQt5.QtCore",
    "PyQt4.QtGui",
    "PyQt4.QtCore",
    "PySide.QtGui",
    "PySide.QtCore",
    "PyQt5",
    "PyQt4",
    "PySide",
    "PySide2",
    "FixTk",
    "tcl",
    "tk",
    "_tkinter",
    "tkinter",
    "Tkinter"
]


a = Analysis(['../../CellProfiler-Analyst.py'],
             pathex=['CellProfiler-Analyst'],
             binaries=binaries,
             datas=datas,
             excludes=excludes,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

libpng_pathname = PyInstaller.utils.hooks.get_homebrew_path("libpng")
libpng_pathname = os.path.join(libpng_pathname, "lib", "libpng16.16.dylib")

java_pathname = os.path.join(os.environ["JAVA_HOME"], "lib/libjava.dylib")
a.binaries += [
    ("libpng16.16.dylib", libpng_pathname, "BINARY"),
    ("libjava.dylib", java_pathname, "BINARY")
]

exclude_binaries = [
    ('libpng16.16.dylib', '/usr/local/lib/python3.8/site-packages/matplotlib/.dylibs/libpng16.16.dylib', 'BINARY'),
]

a.binaries = [binary for binary in a.binaries if binary not in exclude_binaries]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="cpanalyst",
    debug=True,
    strip=False,
    upx=True,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    icon="../../cpa/icons/cpa.icns",
    name="CellProfiler-Analyst.app"
)

app = BUNDLE(
    coll,
    name="CellProfiler-Analyst.app",
    icon="../../cpa/icons/cpa.icns",
    bundle_identifier=None
)