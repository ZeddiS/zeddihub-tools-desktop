# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ZeddiHub SpeedTest standalone module."""

from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
PROJECT_ROOT = SPEC_DIR.parent.parent  # .../zeddihub_tools_desktop

ICON = str(PROJECT_ROOT / "assets" / "web_favicon.ico")

a = Analysis(
    [str(SPEC_DIR / "speedtest_app.py")],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "customtkinter", "PIL", "PIL.Image", "PIL.ImageTk",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "numpy", "pandas", "scipy", "test", "unittest",
        "pytest", "setuptools", "wheel", "pip",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="speedtest",
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
    icon=ICON,
)
