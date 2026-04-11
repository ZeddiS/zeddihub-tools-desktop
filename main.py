#!/usr/bin/env python3
"""
ZeddiHub Tools Desktop
v1.2.0
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app import main
main()
