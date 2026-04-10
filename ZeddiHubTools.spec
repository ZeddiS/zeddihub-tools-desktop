# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ZeddiHub Tools v3.0.0
Build: pyinstaller ZeddiHubTools.spec --clean
"""

import os

block_cipher = None

# Collect all data files (compiler DLL refs + assets)
datas = [
    ('.github/assets/icon.png', '.github/assets'),
    ('.github/assets/banner.png', '.github/assets'),
    ('.github/assets/logo.png', '.github/assets'),
    ('.github/assets/icon.ico', '.github/assets'),
]

# Include Roslyn compiler references recursively
compiler_refs_src = 'zeddihub_rust_editor/compiler_refs'
if os.path.isdir(compiler_refs_src):
    for root, dirs, files in os.walk(compiler_refs_src):
        for f in files:
            src = os.path.join(root, f)
            dst = os.path.dirname(os.path.relpath(src, '.'))
            datas.append((src, dst))

# Hidden imports - force include all submodules
hiddenimports = [
    # Launcher
    'launcher',
    # Rust Editor
    'zeddihub_rust_editor',
    'zeddihub_rust_editor.core',
    'zeddihub_rust_editor.langs',
    'zeddihub_rust_editor.wizard',
    'zeddihub_rust_editor.menus',
    'zeddihub_rust_editor.main',
    'zeddihub_rust_editor.analyzers',
    'zeddihub_rust_editor.compiler',
    'zeddihub_rust_editor.folders',
    'zeddihub_rust_editor.queue_tools',
    'zeddihub_rust_editor.server_tools',
    # CS:GO Tools
    'zeddihub_csgo_tools',
    'zeddihub_csgo_tools.core',
    'zeddihub_csgo_tools.langs',
    'zeddihub_csgo_tools.wizard',
    'zeddihub_csgo_tools.menus',
    'zeddihub_csgo_tools.main',
    'zeddihub_csgo_tools.player_tools',
    'zeddihub_csgo_tools.server_tools',
    # CS2 Tools
    'zeddihub_cs2_tools',
    'zeddihub_cs2_tools.core',
    'zeddihub_cs2_tools.langs',
    'zeddihub_cs2_tools.wizard',
    'zeddihub_cs2_tools.menus',
    'zeddihub_cs2_tools.main',
    'zeddihub_cs2_tools.player_tools',
    'zeddihub_cs2_tools.server_tools',
    # Translator
    'zeddihub_translator',
    'zeddihub_translator.core',
    'zeddihub_translator.langs',
    'zeddihub_translator.main',
    'zeddihub_translator.modules',
    # Server Status
    'zeddihub_server_status',
    'zeddihub_server_status.core',
    'zeddihub_server_status.langs',
    'zeddihub_server_status.main',
    'zeddihub_server_status.menus',
    'zeddihub_server_status.monitor',
    'zeddihub_server_status.wizard',
    # Standard library modules that might be lazy-loaded
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'urllib.request',
    'urllib.parse',
    'urllib.error',
    'socket',
    'struct',
    'threading',
    'webbrowser',
    'json',
    'shutil',
    'subprocess',
    'platform',
    'ctypes',
    'msvcrt',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'scipy', 'pandas', 'matplotlib',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'pytest', 'IPython', 'jupyter', 'notebook',
        'test', 'tests', 'distutils', 'setuptools',
        'email', 'html', 'http', 'xml', 'xmlrpc',
        'sqlite3', 'multiprocessing',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ZeddiHub Tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='.github/assets/icon.ico',
    version=None,
    contents_directory='.',
)
