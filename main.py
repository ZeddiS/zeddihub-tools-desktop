#!/usr/bin/env python3
"""
ZeddiHub Tools Desktop - GUI Entry Point.
v1.0.0

Usage:
    python main.py                     # Launch GUI (default)
    python main.py --tui               # Launch original TUI version
    python app.py                      # Also launches GUI

Build:
    pyinstaller --onefile --windowed --icon=assets/icon.ico --name "ZeddiHub Tools" app.py
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

if "--tui" in sys.argv:
    # Legacy TUI launcher
    from launcher import main
    main()
else:
    # New GUI launcher
    from app import main
    main()

if __name__ == "__main__":
    pass
