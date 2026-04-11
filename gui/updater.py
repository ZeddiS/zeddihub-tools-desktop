"""
ZeddiHub Tools - Auto-update system.
Checks GitHub Releases API for newer versions and provides an in-app download wizard.
"""

import os
import sys
import json
import threading
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

CURRENT_VERSION = "1.5.0"
GITHUB_API_URL = "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases/latest"
GITHUB_RELEASES_URL = "https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"


def parse_version(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except Exception:
        return (0, 0, 0)


def check_for_update(callback=None) -> "dict | None":
    """
    Check GitHub Releases API for a newer version.
    Returns a dict or None. If callback is provided, runs in background thread.
    """
    def _check():
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "User-Agent": f"ZeddiHubTools/{CURRENT_VERSION}",
                    "Accept": "application/vnd.github.v3+json",
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            tag = data.get("tag_name", "0.0.0")
            latest = tag.lstrip("v")

            if parse_version(latest) > parse_version(CURRENT_VERSION):
                # Find the .exe asset URL
                assets = data.get("assets", [])
                download_url = GITHUB_RELEASES_URL
                for asset in assets:
                    name = asset.get("name", "")
                    if name.endswith(".exe"):
                        download_url = asset.get("browser_download_url", GITHUB_RELEASES_URL)
                        break

                result = {
                    "available": True,
                    "current": CURRENT_VERSION,
                    "latest": latest,
                    "changelog": data.get("body", ""),
                    "download_url": download_url,
                    "mandatory": data.get("prerelease", False) is False and False,
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
        return None
    else:
        return _check()


def download_update(url: str, version: str = "",
                    progress_callback=None, done_callback=None):
    """
    Download the new exe to a temp file.
    progress_callback(float 0..1)
    done_callback(success: bool, path_or_error: str)
    """
    def _download():
        try:
            filename = f"ZeddiHub.Tools.v{version}.exe" if version else "ZeddiHub.Tools.update.exe"
            tmp_path = os.path.join(tempfile.gettempdir(), filename)

            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"ZeddiHubTools/{CURRENT_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0

                with open(tmp_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total > 0:
                            progress_callback(downloaded / total)

            if progress_callback:
                progress_callback(1.0)

            if done_callback:
                done_callback(True, tmp_path)

        except Exception as e:
            if done_callback:
                done_callback(False, str(e))

    t = threading.Thread(target=_download, daemon=True)
    t.start()


def apply_update(new_exe_path: str):
    """
    Self-replace the current exe with the downloaded one.
    Creates a bat script that waits for this process to exit, copies the new exe,
    then relaunches it. Works only for frozen (PyInstaller) builds.
    """
    if getattr(sys, "frozen", False):
        current_exe = sys.executable
    else:
        # Running from source — just launch the new exe directly
        subprocess.Popen([new_exe_path])
        return

    bat_path = os.path.join(tempfile.gettempdir(), "zeddihub_updater.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(
            f"@echo off\r\n"
            f"ping -n 3 127.0.0.1 > nul\r\n"
            f"copy /y \"{new_exe_path}\" \"{current_exe}\"\r\n"
            f"start \"\" \"{current_exe}\"\r\n"
            f"del \"{new_exe_path}\"\r\n"
            f"del \"%~f0\"\r\n"
        )

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )


def open_release_page():
    import webbrowser
    webbrowser.open(GITHUB_RELEASES_URL)
