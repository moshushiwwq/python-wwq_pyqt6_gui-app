# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['2048.py'],
             pathex=['d:\\Python\\python-wwq_pyqt6_gui-app'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建一个无控制台的exe文件
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='2048_game',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,  # 设置为False以不显示控制台窗口
          icon=None)  # 可以在这里添加一个图标文件

# 创建一个单文件的exe包
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='2048_game')