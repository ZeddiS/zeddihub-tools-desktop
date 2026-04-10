"""
ZeddiHub Tools - Auto-update system.
Checks version.json on webhosting and downloads update if available.
"""

import os
import sys
import json
import threading
import subprocess
import tempfile
import shutil
import urllib.request
import urllib.error
from pathlib import Path

CURRENT_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://files.zeddihub.eu/tools/version.json"
UPDATE_DOWNLOAD_URL = "https://files.zeddihub.eu/tools/ZeddiHubTools_latest.exe"
GITHUB_RELEASES_URL = "https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"


def parse_version(v: str) -> tuple:
    """Parse version string to tuple for comparison."""
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def check_for_update(callback=None) -> dict | None:
    """
    Check if a newer version is available.
    Returns dict with version info or None if up-to-date / unreachable.
    callback(result: dict | None) if provided (runs in background).
    """
    def _check():
        try:
            req = urllib.request.Request(
                UPDATE_CHECK_URL,
                headers={"User-Agent": "ZeddiHubTools/" + CURRENT_VERSION}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            latest = data.get("version", "0.0.0")
            if parse_version(latest) > parse_version(CURRENT_VERSION):
                result = {
                    "available": True,
                    "current": CURRENT_VERSION,
                    "latest": latest,
                    "changelog": data.get("changelog", ""),
                    "download_url": data.get("download_url", UPDATE_DOWNLOAD_URL),
                    "mandatory": data.get("mandatory", False),
                }
            else:
                result = {"available": False, "current": CURRENT_VERSION, "latest": latest}

            if callback:
                callback(result)
            return result
        except Exception:
            if callback:
                callback(None)
            return None

    if callback:
        t = threading.Thread(target=_check, daemon=True)
        t.start()
    else:
        return _check()


def download_and_install(url: str, progress_callback=None, done_callback=None):
    """Download update and launch installer. Runs in background."""
    def _download():
        try:
            tmp = tempfile.mktemp(suffix=".exe", prefix="zeddihub_update_")
            req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools/" + CURRENT_VERSION})

            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192

                with open(tmp, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total > 0:
                            progress_callback(downloaded / total)

            # Launch installer
            subprocess.Popen([tmp], shell=True)
            if done_callback:
                done_callback(True, tmp)
        except Exception as e:
            if done_callback:
                done_callback(False, str(e))

    t = threading.Thread(target=_download, daemon=True)
    t.start()


def open_release_page():
    """Open GitHub releases page in browser."""
    import webbrowser
    webbrowser.open(GITHUB_RELEASES_URL)
