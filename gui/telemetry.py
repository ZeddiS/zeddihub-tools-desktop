"""
ZeddiHub Tools - Telemetry client.
Sends anonymous usage events to the webhosting endpoint.
No personal data is collected — only event type, panel, app version, OS.
Username is one-way hashed (SHA-256 prefix) if logged in.
"""

import json
import platform
import threading
import urllib.request
import urllib.error
import hashlib

TELEMETRY_URL = "https://zeddihub.eu/tools/telemetry.php"

try:
    from .version import APP_VERSION as _APP_VERSION
except Exception:
    _APP_VERSION = "1.9.0"

_enabled = True  # can be disabled via settings


def set_enabled(enabled: bool):
    global _enabled
    _enabled = enabled


def _send(event: str, panel: str = "", user: str = None):
    """Fire-and-forget POST to telemetry endpoint. Never blocks the UI."""
    if not _enabled:
        return

    def _post():
        try:
            os_name = platform.system()
            payload = json.dumps({
                "event":   event,
                "panel":   panel,
                "user":    _hash_user(user) if user else None,
                "version": _APP_VERSION,
                "os":      os_name,
            }).encode("utf-8")
            req = urllib.request.Request(
                TELEMETRY_URL,
                data=payload,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent":   f"ZeddiHubTools/{_APP_VERSION}",
                }
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # telemetry failures are always silent

    threading.Thread(target=_post, daemon=True).start()


def _hash_user(username: str) -> str:
    return hashlib.sha256(username.lower().encode()).hexdigest()[:12]


# ─── Public API ───────────────────────────────────────────────────────────────

def on_launch(user: str = None):
    _send("launch", user=user)


def on_login(user: str):
    _send("login", user=user)


def on_panel_open(panel_id: str, user: str = None):
    _send("panel_open", panel=panel_id, user=user)


def on_export(panel_id: str, user: str = None):
    _send("export", panel=panel_id, user=user)
