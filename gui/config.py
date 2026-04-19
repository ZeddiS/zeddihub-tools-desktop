"""
ZeddiHub Tools - Central configuration: bootstrap and data directory management.

Bootstrap file lives at: %LOCALAPPDATA%/ZeddiHub/bootstrap.json
It stores only the path to the user-chosen data directory.

All app data (settings, credentials) is stored in the data directory,
which defaults to ~/Documents/ZeddiHub.Tools.Data.
"""

import os
import json
from pathlib import Path

BOOTSTRAP_FILE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ZeddiHub" / "bootstrap.json"
DEFAULT_DATA_DIR_NAME = "ZeddiHub.Tools.Data"


def get_bootstrap() -> dict:
    if BOOTSTRAP_FILE.exists():
        try:
            with open(BOOTSTRAP_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_bootstrap(data: dict):
    BOOTSTRAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BOOTSTRAP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_data_dir() -> Path:
    """Return the user-configured data directory. Creates it if needed."""
    bootstrap = get_bootstrap()
    if "data_dir" in bootstrap:
        p = Path(bootstrap["data_dir"])
    else:
        p = Path.home() / "Documents" / DEFAULT_DATA_DIR_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_data_dir(path: "Path | str"):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    bootstrap = get_bootstrap()
    bootstrap["data_dir"] = str(path)
    save_bootstrap(bootstrap)


def is_first_launch() -> bool:
    """True if the bootstrap file does not exist yet (app never configured)."""
    return not BOOTSTRAP_FILE.exists()


def get_default_data_dir() -> Path:
    return Path.home() / "Documents" / DEFAULT_DATA_DIR_NAME


def get_appdata_data_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home()))
    return base / "ZeddiHub" / DEFAULT_DATA_DIR_NAME
