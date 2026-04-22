"""
ZeddiHub REST API client (auth).

Talks to `https://zeddihub.eu/api/auth/*` using the contract documented in
`zeddihub-tools-website/api/auth/CONTRACT.md`. This module is intentionally
low-level: it returns plain dicts and raises a typed exception on HTTP/network
errors. Business logic (credential storage, fallback, telemetry) lives in
`gui/auth.py`.

All calls:
  * send `X-App-Secret` (bypasses hCaptcha)
  * send `X-Client-Kind: desktop`
  * send `X-Client-Version: <APP_VERSION>`
  * return `{"ok": true, ...}` on success
  * raise `ApiError(error_key, message, status)` on documented failures
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Optional, Dict, Any

from .version import APP_VERSION

# ---------------------------------------------------------------------------
# Constants — kept here so there is exactly one place that knows the URL +
# shared secret. Rotating the APP_SECRET means editing this file AND the
# server-side `_config.php`.
# ---------------------------------------------------------------------------

API_BASE = "https://zeddihub.eu/api/auth"

# Shared with mobile + server. Also defined in
# `zeddihub-tools-website/api/_config.php::ZH_APP_SECRET`.
APP_SECRET = "696d63c65a8536637183028e4eecb841cd5b679ce7b2d33c6ef2d4054166e438"

CLIENT_KIND = "desktop"

USER_AGENT = f"ZeddiHubTools/{APP_VERSION} ({CLIENT_KIND})"

DEFAULT_TIMEOUT = 10  # seconds


class ApiError(Exception):
    """Raised when the API returns `{ok: false, error: ...}` or HTTP 4xx/5xx."""

    def __init__(self, error: str, message: str = "", status: int = 0):
        super().__init__(message or error)
        self.error = error
        self.message = message
        self.status = status

    def __repr__(self) -> str:
        return f"ApiError({self.error!r}, status={self.status})"


class NetworkError(Exception):
    """Raised on DNS/socket/SSL failures — caller can decide to fall back."""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _ssl_ctx() -> ssl.SSLContext:
    # Use system defaults; the API is served over Let's Encrypt.
    return ssl.create_default_context()


def _request(
    path: str,
    method: str = "POST",
    body: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    url = f"{API_BASE}/{path.lstrip('/')}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "X-App-Secret": APP_SECRET,
        "X-Client-Kind": CLIENT_KIND,
        "X-Client-Version": APP_VERSION,
    }
    data: Optional[bytes] = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx()) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        # Server returned 4xx/5xx — try to parse the JSON body.
        try:
            body_bytes = e.read()
            parsed = json.loads(body_bytes.decode("utf-8"))
            err_key = str(parsed.get("error", "http_error"))
            msg = str(parsed.get("message", "") or e.reason or "")
            raise ApiError(err_key, msg, status=e.code) from e
        except ApiError:
            raise
        except Exception:
            raise ApiError("http_error", str(e.reason or e), status=e.code) from e
    except urllib.error.URLError as e:
        raise NetworkError(str(e.reason or e)) from e
    except TimeoutError as e:
        raise NetworkError(f"timeout: {e}") from e
    except OSError as e:
        raise NetworkError(str(e)) from e

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ApiError("bad_json", f"Invalid JSON: {e}", status=status) from e

    if not isinstance(parsed, dict) or not parsed.get("ok"):
        raise ApiError(
            str(parsed.get("error", "unknown_error")),
            str(parsed.get("message", "")),
            status=status,
        )
    return parsed


# ---------------------------------------------------------------------------
# Public calls — one function per endpoint in CONTRACT.md §2
# ---------------------------------------------------------------------------

def register(username: str, email: str, password: str) -> Dict[str, Any]:
    """POST /register — returns `{user, token, expires_at}` on success."""
    return _request("register", body={
        "username": username,
        "email": email,
        "password": password,
    })


def login(identifier: str, password: str) -> Dict[str, Any]:
    """POST /login — `identifier` may be username or email.

    Returns `{user, token, expires_at}` on success.
    """
    return _request("login", body={
        "identifier": identifier,
        "password": password,
    })


def logout(token: str) -> Dict[str, Any]:
    """POST /logout — revokes *this* token only."""
    return _request("logout", method="POST", token=token)


def me(token: str) -> Dict[str, Any]:
    """GET /me — validates token and slides the expiry forward."""
    return _request("me", method="GET", token=token)


def admin_reset(
    caller_token: str,
    target_username: Optional[str],
    target_email: Optional[str],
    new_password: str,
    revoke_all: bool = False,
) -> Dict[str, Any]:
    """POST /admin_reset — caller must be listed in ZH_ADMIN_USERS."""
    body: Dict[str, Any] = {"new_password": new_password}
    if target_username:
        body["target_username"] = target_username
    if target_email:
        body["target_email"] = target_email
    if revoke_all:
        body["revoke_all"] = True
    return _request("admin_reset", body=body, token=caller_token)
