# -*- mode: python ; coding: utf-8 -*-

import os
import os.path

import PyInstaller.compat
import PyInstaller.utils.hooks

binaries = []
binaries += PyInstaller.utils.hooks.collect_dynamic_libs("scipy")

block_cipher = None

datas = []

datas += PyInstaller.utils.hooks.collect_data_files("bioformats")
datas += PyInstaller.utils.hooks.collect_data_files("javabridge")

datas += [
    ("../../cpa/icons/*", "cpa/icons"),
]

hiddenimports = []

hiddenimports += PyInstaller.utils.hooks.collect_submodules('sklearn.utils')
hiddenimports += PyInstaller.utils.hooks.collect_submodules("scipy")
hiddenimports += PyInstaller.utils.hooks.collect_submodules("scipy.special")
hiddenimports += PyInstaller.utils.hooks.collect_submodules('skimage.io._plugins')
hiddenimports += PyInstaller.utils.hooks.collect_submodules("skimage.feature")
hiddenimports += PyInstaller.utils.hooks.collect_submodules("skimage.filters")
hiddenimports += ["cmath", "scipy._lib", "sklearn.utils.sparsetools"]

a = Analysis(['../../CellProfiler-Analyst.py'],
             pathex=['CellProfiler-Analyst'],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='CellProfiler-Analyst',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
		  icon='../../cpa/icons/cpa.ico',
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='CellProfiler-Analyst')
