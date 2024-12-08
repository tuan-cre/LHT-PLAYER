# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mavPlayer.py'],
    pathex=[],
    binaries=[('C:/Program Files/VideoLAN/VLC/libvlc.dll', '.'), ('C:/Program Files/VideoLAN/VLC/plugins/*', 'plugins')],
    datas=[('C:/Program Files/VideoLAN/VLC/*.dll', 'vlc_dlls')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='mavPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    name='mavPlayer',
)
