# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['standalone_main.py'],
    pathex=[],
    binaries=[],
    datas=[('calmweb', 'calmweb'), ('calmweb-dashboard/dist', 'calmweb-dashboard-dist')],
    hiddenimports=['urllib3', 'certifi', 'charset_normalizer', 'idna'],
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
    name='CalmWeb_Fr_Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['icon.ico'],
    version='version_info.txt',
)
