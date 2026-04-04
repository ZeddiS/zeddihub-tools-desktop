#!/usr/bin/env python3
"""
ZeddiHub Tools - Entry point for .exe builds (PyInstaller / cx_Freeze).

Usage:
    python main.py
    pyinstaller --onefile --name "ZeddiHub Tools" --icon .github/assets/icon.ico main.py
"""

import sys
import os

# Ensure the script directory is in path for module imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from launcher import main

if __name__ == "__main__":
    main()
