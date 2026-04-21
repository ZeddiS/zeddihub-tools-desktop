# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for ZeddiHub Tools Desktop v1.7.0
# Generated for Windows .exe build
# Run: pyinstaller ZeddiHubTools.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('locale', 'locale'),
        ('webhosting/data/admin_apps.json', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'cryptography',
        'cryptography.fernet',
        'pystray',
        'pystray._win32',
        'psutil',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pyautogui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZeddiHubTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/web_favicon.ico',
)
