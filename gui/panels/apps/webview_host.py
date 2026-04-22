"""
WebView2 host + Edge WebView2 runtime detection/install.

Strategy:
  1. ``open_webview(url, title)`` tries to spawn a ``pywebview`` window with
     Edge Chromium as backend. On Windows this requires the WebView2 runtime
     (installed by default on Win11 / Edge ≥ 90).
  2. If pywebview or the runtime is missing, ``open_webview`` returns
     ``False`` so the caller can fall back to the system browser (open-in-OS).
  3. ``webview2_installed()`` does a registry check for the evergreen
     runtime. ``install_webview2_async()`` downloads Microsoft's official
     ``MicrosoftEdgeWebview2Setup.exe`` bootstrapper and runs it.

Note: pywebview's ``webview.start()`` blocks the calling thread — we launch
it in a daemon thread so the main GUI stays responsive. Because pywebview
windows run their own event loop in that thread, closing the webview window
naturally ends the thread.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from ...version import user_agent

try:  # pragma: no cover - optional
    import webview as _pywebview
    PYWEBVIEW_OK = True
except Exception:
    _pywebview = None
    PYWEBVIEW_OK = False


# Official evergreen bootstrapper — small (~2 MB) installer that downloads
# the real runtime at setup time.
WEBVIEW2_BOOTSTRAPPER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
WEBVIEW2_BOOTSTRAPPER_NAME = "MicrosoftEdgeWebview2Setup.exe"

# Registry keys to probe. Reference:
# https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution
_WEBVIEW2_REG_KEYS = [
    r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    # Per-user install:
    r"Software\Microsoft\EdgeUpdate\ClientState\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
]


def webview2_installed() -> bool:
    """True if the WebView2 evergreen runtime is installed anywhere."""
    if sys.platform != "win32":
        return False
    try:
        import winreg  # type: ignore
    except Exception:
        return False
    for root_name, root in [
        ("HKLM", winreg.HKEY_LOCAL_MACHINE),
        ("HKCU", winreg.HKEY_CURRENT_USER),
    ]:
        for sub in _WEBVIEW2_REG_KEYS:
            try:
                with winreg.OpenKey(root, sub):
                    return True
            except OSError:
                continue
    return False


def install_webview2_async(on_done: Optional[Callable[[bool, str], None]] = None):
    """Download + silently run the WebView2 bootstrapper. Fire-and-forget.

    ``on_done(success: bool, msg: str)`` is called when the setup process
    exits (or on error). Caller must route UI updates via ``self.after``.
    """
    def _worker():
        tmp_dir = Path(tempfile.gettempdir())
        dst = tmp_dir / WEBVIEW2_BOOTSTRAPPER_NAME
        try:
            req = urllib.request.Request(
                WEBVIEW2_BOOTSTRAPPER_URL,
                headers={"User-Agent": user_agent()},
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(dst, "wb") as fh:
                fh.write(resp.read())
        except Exception as e:
            if on_done:
                on_done(False, f"Nepodařilo se stáhnout instalátor: {e}")
            return

        try:
            # Silent install; bootstrapper downloads + installs runtime
            proc = subprocess.Popen(
                [str(dst), "/silent", "/install"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            rc = proc.wait(timeout=600)
            ok = rc == 0 and webview2_installed()
            msg = ("WebView2 runtime nainstalován." if ok
                   else f"Instalátor skončil s kódem {rc}. Zkus restart aplikace.")
            if on_done:
                on_done(ok, msg)
        except subprocess.TimeoutExpired:
            if on_done:
                on_done(False, "Instalace WebView2 trvá příliš dlouho; zkus ji dokončit ručně.")
        except Exception as e:
            if on_done:
                on_done(False, f"Chyba při spuštění instalátoru: {e}")
        finally:
            try:
                dst.unlink()
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True).start()


class WebViewUnavailable(Exception):
    pass


def open_webview(url: str, *, title: str = "ZeddiHub Tools — WebView",
                 width: int = 1280, height: int = 820) -> bool:
    """Open ``url`` in an embedded Edge WebView2 window.

    Returns ``True`` on success (window created and event loop will run until
    closed in a daemon thread), ``False`` if pywebview is missing or WebView2
    runtime unavailable — caller should fall back to ``webbrowser.open``.
    """
    if not PYWEBVIEW_OK:
        return False
    if sys.platform == "win32" and not webview2_installed():
        return False

    def _run():
        try:
            _pywebview.create_window(
                title, url,
                width=width, height=height,
                resizable=True, confirm_close=False,
            )
            # ``gui="edgechromium"`` picks the WebView2 renderer explicitly.
            _pywebview.start(gui="edgechromium")
        except Exception:
            # Fall back silently; caller can't retry at this point.
            pass

    threading.Thread(target=_run, daemon=True).start()
    return True


__all__ = [
    "open_webview",
    "webview2_installed",
    "install_webview2_async",
    "PYWEBVIEW_OK",
    "WEBVIEW2_BOOTSTRAPPER_URL",
]
