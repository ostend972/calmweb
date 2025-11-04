# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Répertoire de base
base_dir = Path(r'C:\Users\Alan\Desktop\CalmWeb_Clean')
calmweb_dir = base_dir / 'calmweb'

# Collecte TOUS les fichiers Python de CalmWeb
datas = []

# Ajouter tout le répertoire calmweb comme données
for root, dirs, files in os.walk(str(calmweb_dir)):
    for file in files:
        if file.endswith(('.py', '.json', '.txt', '.cfg')):
            src = os.path.join(root, file)
            # Calculer le chemin de destination
            rel_path = os.path.relpath(src, str(base_dir))
            datas.append((src, os.path.dirname(rel_path)))

# Ajouter le dashboard React compilé
dashboard_dist_dir = base_dir / 'calmweb-dashboard' / 'dist'
if dashboard_dist_dir.exists():
    for root, dirs, files in os.walk(str(dashboard_dist_dir)):
        for file in files:
            src = os.path.join(root, file)
            # Calculer le chemin de destination relatif
            rel_path = os.path.relpath(src, str(base_dir))
            datas.append((src, os.path.dirname(rel_path)))

# Configuration finale d'analyse
a = Analysis(
    [str(base_dir / 'standalone_main.py')],
    pathex=[str(base_dir), str(calmweb_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Imports essentiels
        'socket', 'threading', 'json', 'http.server', 'urllib.request', 'urllib.parse',
        'ssl', 'time', 'os', 'sys', 'signal', 'subprocess', 'collections', 'datetime',
        'pathlib', 'configparser', 'ctypes', 'winreg', 'ipaddress', 'email.utils',
        # Imports Windows
        'win32api', 'win32con', 'win32gui', 'win32ui', 'pywintypes', 'pythoncom',
        # Modules web
        'http', 'http.client', 'http.cookies', 'http.server',
        # Modules réseau
        'socketserver', 'select', 'ssl', 'hashlib', 'base64',
        # Modules system tray
        'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw',
        # Interface utilisateur
        'tkinter', 'tkinter.scrolledtext'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PyQt5', 'PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CalmWeb',
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
    manifest='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.1.0.0"
    processorArchitecture="*"
    name="CalmWeb"
    type="win32"
  />
  <description>CalmWeb Content Filter v1.1.0</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    </application>
  </compatibility>
</assembly>''',
)