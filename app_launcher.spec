# -*- mode: python ; coding: utf-8 -*-

# 优化app_launcher.spec以加快exe启动速度
# 1. 添加pathex以帮助PyInstaller快速找到依赖项
# 2. 添加hiddenimports以确保所有PyQt6组件都被正确包含
# 3. 设置noarchive=True以提高启动速度
# 4. 添加exclude以排除不必要的模块

import sys
from os import path

sys.setrecursionlimit(5000)

base_path = 'D:/Python/python-wwq_pyqt6_gui-app'

a = Analysis(
    [path.join(base_path, 'app_launcher.py')],
    pathex=[base_path],
    binaries=[],
    datas=[
        # 添加必要的资源文件
        ('down.png', '.'),
        ('infor/', 'infor/')
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'logging',
        'sys',
        'os',
        'threading',
        'pickle'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'test',
        'doctest',
        'unittest',
        'pkg_resources',
        'setuptools'
    ],
    noarchive=True,  # 设置为True可以显著提高启动速度
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    exclude_binaries=True,
    name='app_launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # 禁用strip工具，避免Windows系统找不到strip工具的错误
    upx=True,  # 使用UPX压缩可执行文件
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app_launcher',
)
