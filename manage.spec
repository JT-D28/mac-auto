# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['manage.py'],
             pathex=[],
             binaries=[],
             datas=[('./homepage','homepage'),('./logs','logs'),('./login','login'),('./manager','manager'),('./ME2','ME2'),('./static','static'),('mymiddleware.py','.')],
             hiddenimports=['daphne','channels','channels.auth','channels.generic.websocket','channels.generic','pyDes','jenkins','channels.apps','corsheaders','corsheaders.apps','mysqlclient','pymysql','mysqldb','xlrd','corsheaders.middleware'],
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
          name='run',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ME2')
