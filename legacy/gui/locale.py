"""Language/localization system for ZeddiHub Tools."""
import json
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

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
    settings = load_settings()
    settings["language"] = lang
    save_settings(settings)


def _settings_file() -> Path:
    from .config import get_data_dir
    return get_data_dir() / "settings.json"


def load_settings() -> dict:
    f = _settings_file()
    if f.exists():
        try:
            with open(f, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


def save_settings(settings: dict):
    f = _settings_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2, ensure_ascii=False)


def init():
    """Initialize locale from saved settings or default to Czech."""
    settings = load_settings()
    lang = settings.get("language", "cs")
    _load(lang)
    return lang


def is_first_launch() -> bool:
    """Delegate to config bootstrap check."""
    from .config import is_first_launch as _bootstrap_first
    return _bootstrap_first()
