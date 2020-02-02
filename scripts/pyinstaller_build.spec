# -*- mode: python -*-

block_cipher = None


a = Analysis([r"..\autosub\__main__.py",
             r"..\autosub\__init__.py",
             r"..\autosub\cmdline_utils.py",
             r"..\autosub\constants.py",
             r"..\autosub\core.py",
             r"..\autosub\exceptions.py",
             r"..\autosub\ffmpeg_utils.py",
             r"..\autosub\lang_code_utils.py",
             r"..\autosub\metadata.py",
             r"..\autosub\options.py",
             r"..\autosub\speech_trans_api.py",
             r"..\autosub\sub_utils.py",],
             pathex=[r'C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x64'],
             binaries=[],
             datas=[],
             hiddenimports=["google.cloud.speech"],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          icon=r"..\docs\icon\autosub.ico",
          name="autosub",
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True )
