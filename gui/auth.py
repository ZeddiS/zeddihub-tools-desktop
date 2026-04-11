"""
ZeddiHub Tools - Authentication system for Server Tools.
Credentials are stored encrypted using Fernet (AES-128).
Access list is fetched from webhosting API.
"""

import os
import json
import hashlib
import base64
import threading
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

import urllib.request
import urllib.error

# --- Config ---
AUTH_API_URL = "https://files.zeddihub.eu/tools/auth.json"

_cached_token: str | None = None
_auth_verified: bool = False


def _get_data_dir() -> Path:
    from .config import get_data_dir
    return get_data_dir()


def _cred_file() -> Path:
    return _get_data_dir() / "auth.enc"


def _key_file() -> Path:
    return _get_data_dir() / ".key"


def _ensure_dir():
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


def save_credentials(username: str, password: str, remember: bool = True):
    """Encrypt and save credentials locally."""
    if not CRYPTO_OK or not remember:
        return
    _ensure_dir()
    try:
        key = _get_or_create_key()
        f = Fernet(key)
        data = json.dumps({"username": username, "password": password}).encode()
        encrypted = f.encrypt(data)
        _cred_file().write_bytes(encrypted)
    except Exception:
        pass


def load_credentials():
    """Load and decrypt saved credentials. Returns (username, password) or None."""
    cf = _cred_file()
    if not CRYPTO_OK or not cf.exists():
        return None
    try:
        key = _get_or_create_key()
        f = Fernet(key)
        data = f.decrypt(cf.read_bytes())
        creds = json.loads(data.decode())
        return creds.get("username", ""), creds.get("password", "")
    except Exception:
        return None


def clear_credentials():
    """Remove saved credentials."""
    cf = _cred_file()
    if cf.exists():
        cf.unlink()
    global _cached_token, _auth_verified
    _cached_token = None
    _auth_verified = False


def verify_access(username: str, password: str, callback=None) -> bool:
    """
    Verify user has access by checking against the webhosting auth API.
    callback(success: bool, message: str) if provided.
    Runs in background thread if callback given, otherwise blocks.
    """
    def _check():
        global _cached_token, _auth_verified
        try:
            req = urllib.request.Request(
                AUTH_API_URL,
                headers={"User-Agent": "ZeddiHubTools/1.5.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            users = data.get("users", [])
            for u in users:
                if (u.get("username", "").lower() == username.lower()
                        and u.get("password") == password):
                    _cached_token = username
                    _auth_verified = True
                    if callback:
                        callback(True, "Přihlášení úspěšné!")
                    return True

            # Try access code
            codes = data.get("access_codes", [])
            if username in codes or password in codes:
                _cached_token = username or password
                _auth_verified = True
                if callback:
                    callback(True, "Přístupový kód přijat!")
                return True

            if callback:
                callback(False, "Nesprávné přihlašovací údaje nebo přístupový kód.")
            return False

        except urllib.error.URLError:
            # Allow offline fallback if credentials were previously verified
            if _auth_verified:
                if callback:
                    callback(True, "Offline režim - použita cached autentizace.")
                return True
            if callback:
                callback(False, "Nelze se připojit k autorizačnímu serveru.")
            return False
        except Exception as e:
            if callback:
                callback(False, f"Chyba: {e}")
            return False

    if callback:
        t = threading.Thread(target=_check, daemon=True)
        t.start()
    else:
        return _check()


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return _auth_verified


def get_current_user() -> str | None:
    """Get current logged-in username/code."""
    return _cached_token


def logout():
    """Log out current user (does not remove saved credentials)."""
    global _cached_token, _auth_verified
    _cached_token = None
    _auth_verified = False
