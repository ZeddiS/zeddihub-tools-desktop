"""
ZeddiHub Tools - Authentication system for Server Tools.

v1.7.4+: REST API primary path (``https://zeddihub.eu/api/auth/*``), legacy
``tools/data/auth.json`` kept as network fallback only. Bearer tokens are the
source of truth for the current session. Credentials (username + password +
token) are stored encrypted with Fernet (AES-128) in ``auth.enc``.

Error-key taxonomy mirrors the REST contract (``invalid_username``, ``taken``,
``bad_credentials`` …). See ``zeddihub-tools-website/api/auth/CONTRACT.md`` §8.
"""

from __future__ import annotations

import os
import json
import hashlib
import base64
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Tuple

try:
    from cryptography.fernet import Fernet
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

import urllib.request
import urllib.error

from . import api_auth
from .api_auth import ApiError, NetworkError

# ---------------------------------------------------------------------------
# Legacy fallback config (read-only JSON on the old ``/tools/data/`` path).
# Used ONLY when the REST API is unreachable AND the user has no cached token.
# ---------------------------------------------------------------------------
LEGACY_AUTH_API_URL = "https://zeddihub.eu/tools/data/auth.json"

# ---------------------------------------------------------------------------
# Session state (module-level; single desktop instance at a time).
# ---------------------------------------------------------------------------
_cached_username: Optional[str] = None
_cached_token: Optional[str] = None  # REST Bearer token when REST auth succeeds
_cached_expires_at: int = 0           # unix seconds
_auth_verified: bool = False
_current_role: str = "user"  # "admin" | "premium" | "user"
_current_user_dict: Dict[str, Any] = {}

# Czech error strings for REST error-keys the user might actually see in the
# login / register overlay. Anything not mapped here falls through to the
# server's own ``message`` field.
_ERROR_CS: Dict[str, str] = {
    "invalid_username":   "Neplatné uživatelské jméno.",
    "invalid_email":      "Neplatný email.",
    "invalid_password":   "Neplatné heslo (min. 8 znaků).",
    "captcha_required":   "Chybí captcha token (interní chyba klienta).",
    "captcha_failed":     "Captcha se nepodařilo ověřit.",
    "taken":              "Uživatelské jméno nebo email už někdo používá.",
    "bad_credentials":    "Nesprávné přihlašovací údaje.",
    "disabled":           "Účet je zablokovaný. Kontaktujte administrátora.",
    "too_fast":           "Moc rychle. Zkuste to znovu za chvíli.",
    "too_many_fails":     "Příliš mnoho neúspěšných pokusů. Zkuste později.",
    "daily_limit":        "Dosáhli jste denního limitu registrací.",
    "auth_required":      "Přihlášení vypršelo, přihlaste se znovu.",
    "auth_invalid":       "Session vypršela, přihlaste se znovu.",
    "forbidden":          "Nemáte oprávnění.",
    "not_found":          "Uživatel nenalezen.",
    "server_error":       "Chyba serveru, zkuste později.",
    "missing_identifier": "Zadejte uživatelské jméno nebo email.",
    "missing_password":   "Zadejte heslo.",
}


def _humanize_api_error(err: ApiError) -> str:
    """Convert an ApiError into a short Czech message for the UI.

    v1.7.8: Pokud server vrátí neznámý error-key, přidáme ho do závorky, aby
    šlo diagnostikovat problém bez otevírání logů (user sám vidí „server_error
    (http_error/502)" atp.)."""
    msg = _ERROR_CS.get(err.error)
    if msg:
        return msg
    if err.message:
        suffix = f" ({err.error}"
        if err.status:
            suffix += f"/{err.status}"
        suffix += ")"
        return err.message + suffix
    if err.status:
        return f"Chyba: {err.error} (HTTP {err.status})"
    return f"Chyba: {err.error}"


# ---------------------------------------------------------------------------
# Local encrypted storage ("auth.enc")
# ---------------------------------------------------------------------------

def _get_data_dir() -> Path:
    from .config import get_data_dir
    return get_data_dir()


def _cred_file() -> Path:
    return _get_data_dir() / "auth.enc"


def _key_file() -> Path:
    return _get_data_dir() / ".key"


def _ensure_dir() -> None:
    _get_data_dir().mkdir(parents=True, exist_ok=True)


def _get_or_create_key() -> bytes:
    """Get or create machine-specific encryption key."""
    _ensure_dir()
    kf = _key_file()
    if kf.exists():
        return kf.read_bytes()
    machine_id = _get_machine_id()
    key = base64.urlsafe_b64encode(hashlib.sha256(machine_id.encode()).digest())
    kf.write_bytes(key)
    try:
        kf.chmod(0o600)
    except Exception:
        pass
    return key


def _get_machine_id() -> str:
    """Get unique machine identifier."""
    try:
        import platform
        import uuid
        return str(uuid.getnode()) + platform.node()
    except Exception:
        return "zeddihub-fallback-key-2024"


def _write_enc(payload: Dict[str, Any]) -> None:
    if not CRYPTO_OK:
        return
    _ensure_dir()
    try:
        key = _get_or_create_key()
        f = Fernet(key)
        _cred_file().write_bytes(f.encrypt(json.dumps(payload).encode("utf-8")))
    except Exception:
        pass


def _read_enc() -> Optional[Dict[str, Any]]:
    cf = _cred_file()
    if not CRYPTO_OK or not cf.exists():
        return None
    try:
        key = _get_or_create_key()
        f = Fernet(key)
        data = f.decrypt(cf.read_bytes())
        parsed = json.loads(data.decode("utf-8"))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return None


# --- Public credential-storage API (backwards-compatible) -------------------

def save_credentials(username: str, password: str, remember: bool = True) -> None:
    """Encrypt and save username+password locally (legacy signature).

    v1.7.4: also persists the currently-cached REST Bearer token and expiry
    if we have one, so next launch can resume the session without hitting the
    login endpoint.
    """
    if not remember:
        return
    payload: Dict[str, Any] = {"username": username, "password": password}
    if _cached_token:
        payload["token"] = _cached_token
        payload["expires_at"] = _cached_expires_at
    _write_enc(payload)


def save_session(
    username: str,
    token: str,
    expires_at: int,
    password: Optional[str] = None,
) -> None:
    """Persist a full REST session. Optional password supports auto-relogin
    when the token expires and only /login can recover.
    """
    payload: Dict[str, Any] = {
        "username": username,
        "token": token,
        "expires_at": int(expires_at or 0),
    }
    if password:
        payload["password"] = password
    _write_enc(payload)


def load_credentials() -> Optional[Tuple[str, str]]:
    """Return saved (username, password) or None (legacy helper)."""
    parsed = _read_enc()
    if not parsed:
        return None
    u = parsed.get("username") or ""
    p = parsed.get("password") or ""
    if not u:
        return None
    return u, p


def load_session() -> Optional[Dict[str, Any]]:
    """Return the full decrypted payload (may contain token + expires_at)."""
    return _read_enc()


def clear_credentials() -> None:
    """Remove saved credentials FILE only. Does NOT affect current login session.
    Use ``logout()`` to end the current session."""
    cf = _cred_file()
    if cf.exists():
        try:
            cf.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Session-state accessors
# ---------------------------------------------------------------------------

def is_authenticated() -> bool:
    return _auth_verified


def get_current_user() -> Optional[str]:
    return _cached_username


def get_current_token() -> Optional[str]:
    return _cached_token


def get_current_role() -> str:
    if not _auth_verified:
        return "user"
    return _current_role or "user"


def is_admin() -> bool:
    return get_current_role() == "admin"


def _apply_rest_session(payload: Dict[str, Any]) -> None:
    """Copy a successful REST `{user, token, expires_at}` response into module state."""
    global _cached_username, _cached_token, _cached_expires_at
    global _auth_verified, _current_role, _current_user_dict
    user = payload.get("user") or {}
    _cached_username = str(user.get("username") or "")
    _cached_token = str(payload.get("token") or "")
    _cached_expires_at = int(payload.get("expires_at") or 0)
    if user.get("is_admin") or str(user.get("role", "")).lower() == "admin":
        _current_role = "admin"
    else:
        _current_role = str(user.get("role") or "user").lower()
    _current_user_dict = user
    _auth_verified = True


def _clear_session_state() -> None:
    global _cached_username, _cached_token, _cached_expires_at
    global _auth_verified, _current_role, _current_user_dict
    _cached_username = None
    _cached_token = None
    _cached_expires_at = 0
    _auth_verified = False
    _current_role = "user"
    _current_user_dict = {}


# ---------------------------------------------------------------------------
# Legacy auth.json fallback (network-unavailable-for-REST path only)
# ---------------------------------------------------------------------------

def _verify_legacy_json(username: str, password: str) -> Tuple[bool, str]:
    """Try the old static JSON auth. Returns (ok, msg)."""
    global _cached_username, _cached_token, _auth_verified, _current_role
    try:
        req = urllib.request.Request(
            LEGACY_AUTH_API_URL,
            headers={"User-Agent": api_auth.USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return False, "Nelze se připojit k autorizačnímu serveru."

    for u in data.get("users", []):
        if (str(u.get("username", "")).lower() == username.lower()
                and u.get("password") == password):
            _cached_username = u.get("username", username)
            _cached_token = None  # no REST token in fallback
            _auth_verified = True
            _current_role = str(u.get("role", "user")).lower()
            return True, "Přihlášení úspěšné (legacy)."

    codes = data.get("access_codes", [])
    if username in codes or password in codes:
        _cached_username = username or password
        _cached_token = None
        _auth_verified = True
        _current_role = "user"
        return True, "Přístupový kód přijat."

    return False, "Nesprávné přihlašovací údaje."


# ---------------------------------------------------------------------------
# Public verify/register/logout — all support a (success:bool, msg:str) callback
# ---------------------------------------------------------------------------

def _dispatch(
    work: Callable[[], Tuple[bool, str]],
    callback: Optional[Callable[[bool, str], None]],
) -> bool:
    """Run ``work`` on a bg thread if a callback is given, else inline."""
    def _run():
        try:
            ok, msg = work()
        except Exception as e:
            ok, msg = False, f"Chyba: {e}"
        if callback:
            try:
                callback(ok, msg)
            except Exception:
                pass

    if callback:
        threading.Thread(target=_run, daemon=True).start()
        return False  # result comes via callback
    ok, _msg = work()
    return ok


def verify_access(
    username: str,
    password: str,
    callback: Optional[Callable[[bool, str], None]] = None,
) -> bool:
    """Verify identity via REST first, fall back to legacy auth.json on network error.

    On success the module-level session state is populated and any positional
    callback is invoked on the worker thread (UI code is expected to bounce
    back onto the main thread via ``after(0, ...)``).
    """
    def _work() -> Tuple[bool, str]:
        # 1) REST path
        try:
            resp = api_auth.login(identifier=username, password=password)
            _apply_rest_session(resp)
            return True, "Přihlášení úspěšné."
        except ApiError as e:
            # Real credential error — do NOT fall back, user needs to fix input.
            return False, _humanize_api_error(e)
        except NetworkError as ne:
            # 2) Legacy fallback only when the REST endpoint is unreachable.
            ok, msg = _verify_legacy_json(username, password)
            if ok:
                return True, msg + " (offline fallback)"
            if _auth_verified:
                return True, "Offline režim – použita cached autentizace."
            # v1.7.8: ukázat konkrétní síťovou chybu, ne jen generické "Nelze se
            # připojit k serveru" — uživatel ví, co je potřeba opravit (DNS,
            # SSL, firewall, VPN).
            detail = str(ne) or "neznámý důvod"
            return False, f"Nelze se připojit k serveru ({detail}) a údaje nejsou v cache."

    return _dispatch(_work, callback)


def register(
    username: str,
    email: str,
    password: str,
    callback: Optional[Callable[[bool, str], None]] = None,
) -> bool:
    """POST /register. On success, the caller is also logged in.

    Callback receives (ok, human_message). On ok=True the session is already
    populated — you don't need to call ``verify_access`` afterwards.
    """
    def _work() -> Tuple[bool, str]:
        try:
            resp = api_auth.register(username=username, email=email, password=password)
            _apply_rest_session(resp)
            # Persist session for next launch — also keep password so that we
            # can /login again once the token expires after 180 days.
            save_session(
                username=_cached_username or username,
                token=_cached_token or "",
                expires_at=_cached_expires_at,
                password=password,
            )
            return True, "Účet vytvořen a přihlášeno."
        except ApiError as e:
            return False, _humanize_api_error(e)
        except NetworkError as e:
            return False, f"Nelze se připojit k serveru: {e}"

    return _dispatch(_work, callback)


def resume_session(
    callback: Optional[Callable[[bool, str], None]] = None,
) -> bool:
    """Re-validate a saved Bearer token via GET /me.

    Called on startup after loading ``auth.enc``. On success, session state is
    populated and the server slides the token's expiry forward.
    """
    saved = load_session()
    if not saved:
        if callback:
            callback(False, "Žádná uložená session.")
        return False

    token = saved.get("token") or ""
    username = saved.get("username") or ""
    password = saved.get("password") or ""

    if not token:
        # Old auth.enc with just username+password — fall through to /login.
        if username and password:
            return verify_access(username, password, callback=callback)
        if callback:
            callback(False, "Žádná uložená session.")
        return False

    def _work() -> Tuple[bool, str]:
        try:
            resp = api_auth.me(token=token)
            # /me does not return a new token but it does return user + expires_at
            global _cached_token, _cached_expires_at
            _apply_rest_session({
                "user": resp.get("user"),
                "token": token,
                "expires_at": resp.get("expires_at") or 0,
            })
            # Persist refreshed expiry (password kept from previous save).
            save_session(
                username=_cached_username or username,
                token=token,
                expires_at=_cached_expires_at,
                password=password or None,
            )
            return True, "Session obnovena."
        except ApiError as e:
            # Token dead — try /login with saved password.
            if e.error in ("auth_invalid", "auth_required") and username and password:
                try:
                    resp = api_auth.login(identifier=username, password=password)
                    _apply_rest_session(resp)
                    save_session(
                        username=_cached_username or username,
                        token=_cached_token or "",
                        expires_at=_cached_expires_at,
                        password=password,
                    )
                    return True, "Přihlášení obnoveno."
                except ApiError as e2:
                    return False, _humanize_api_error(e2)
                except NetworkError:
                    return False, "Offline, nelze obnovit přihlášení."
            return False, _humanize_api_error(e)
        except NetworkError:
            # Offline — trust the cached token until the user reconnects.
            if time.time() < (_cached_expires_at or 0):
                _apply_rest_session({
                    "user": saved.get("user") or {"username": username, "role": "user"},
                    "token": token,
                    "expires_at": saved.get("expires_at") or 0,
                })
                return True, "Offline režim – použit cached token."
            return False, "Offline a cached session vypršela."

    return _dispatch(_work, callback)


def logout(
    callback: Optional[Callable[[bool, str], None]] = None,
) -> bool:
    """Revoke current Bearer token on server + clear local session state.

    Does NOT delete saved credentials file — call ``clear_credentials()`` for
    that. Always reports success (logout is idempotent).
    """
    token = _cached_token

    def _work() -> Tuple[bool, str]:
        if token:
            try:
                api_auth.logout(token=token)
            except (ApiError, NetworkError):
                # Best-effort — kill local state either way.
                pass
        _clear_session_state()
        return True, "Odhlášeno."

    return _dispatch(_work, callback)
