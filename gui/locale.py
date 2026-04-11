"""Language/localization system for ZeddiHub Tools."""
import json
import os
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"
SETTINGS_FILE = Path(os.environ.get("APPDATA", Path.home())) / "ZeddiHub" / "Tools" / "settings.json"

_current_lang = "cs"
_strings = {}


def _load(lang: str):
    global _strings, _current_lang
    f = LOCALE_DIR / f"{lang}.json"
    if f.exists():
        with open(f, encoding="utf-8") as fh:
            _strings = json.load(fh)
        _current_lang = lang
    else:
        _strings = {}


def t(key: str, **kwargs) -> str:
    """Get translated string."""
    val = _strings.get(key, key)
    if kwargs:
        try:
            val = val.format(**kwargs)
        except Exception:
            pass
    return val


def get_lang() -> str:
    return _current_lang


def set_lang(lang: str):
    _load(lang)
    # Save to settings
    settings = load_settings()
    settings["language"] = lang
    save_settings(settings)


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_settings(settings: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def init():
    """Initialize locale from saved settings or default to Czech."""
    settings = load_settings()
    lang = settings.get("language", "cs")
    _load(lang)
    return lang


def is_first_launch() -> bool:
    return not SETTINGS_FILE.exists()
