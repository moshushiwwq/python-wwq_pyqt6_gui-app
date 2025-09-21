# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集PyQt6的所有子模块
hidden_imports = collect_submodules('PyQt6')
hidden_imports += ['requests', 'bs4', 'urllib3', 'urllib.parse']

# 添加额外的依赖
hidden_imports.append('pkg_resources')

a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('down.png', '.')],  # 包含需要的资源文件
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='应用程序启动器',  # 使用中文名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件可以添加
)
