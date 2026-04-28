"""
ZeddiHub Tools — Lightweight HTTP cache with TTL (v1.7.9).

Process-wide singleton sloužící jako tenký wrapper okolo `urllib.request` —
ukládá poslední odpovědi do paměti (a volitelně na disk) s TTL, aby se
panely při znovuotevření (po minimalizaci do tray, přepnutí kategorie, …)
nedotazovaly serveru znovu, pokud data ještě nezestárla.

Použití:
    from gui.http_cache import fetch_json
    data = fetch_json(URL, ttl=3600)  # 60 min cache
    # → vrátí dict (nebo None při chybě)

Cache klíč = (URL, accept-flavor). Není thread-safe pro paralelní zápis
do DISKU, ale paměťová část používá ``threading.Lock`` — bezpečné z více
vláken.
"""

from __future__ import annotations

import json
import time
import threading
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple

# Memory cache: key -> (timestamp, payload)
_cache: Dict[Tuple[str, str], Tuple[float, Any]] = {}
_lock = threading.Lock()

DEFAULT_TIMEOUT = 6  # seconds
DEFAULT_TTL = 1800   # 30 min


def _now() -> float:
    return time.time()


def get_cached(url: str, flavor: str = "json") -> Optional[Any]:
    """Vrátí cached payload bez ohledu na stáří, nebo None."""
    with _lock:
        entry = _cache.get((url, flavor))
    if entry is None:
        return None
    return entry[1]


def is_fresh(url: str, ttl: int, flavor: str = "json") -> bool:
    with _lock:
        entry = _cache.get((url, flavor))
    if entry is None:
        return False
    return (_now() - entry[0]) < ttl


def store(url: str, payload: Any, flavor: str = "json") -> None:
    with _lock:
        _cache[(url, flavor)] = (_now(), payload)


def invalidate(url: str, flavor: str = "json") -> None:
    with _lock:
        _cache.pop((url, flavor), None)


def fetch_json(
    url: str,
    *,
    ttl: int = DEFAULT_TTL,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
    force_refresh: bool = False,
) -> Optional[Any]:
    """
    Stáhne JSON z URL s TTL cache. Pokud cache ještě nezestárla, vrátí
    okamžitě cached. Při chybě sítě a existující cache vrátí cached payload
    i přes propadlé TTL (lepší starý obsah než prázdná obrazovka).

    Vrátí ``None`` pouze pokud nikdy nebyla data získána a aktuální dotaz
    selhal.
    """
    if not force_refresh and is_fresh(url, ttl):
        return get_cached(url)

    req_headers = {
        "User-Agent": "ZeddiHubTools/cache",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        parsed = json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError, ValueError):
        # Síť/parsing selhal — vrať starší cached pokud existuje.
        return get_cached(url)

    store(url, parsed)
    return parsed


def fetch_text(
    url: str,
    *,
    ttl: int = DEFAULT_TTL,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
    force_refresh: bool = False,
) -> Optional[str]:
    """Stáhne text/HTML s TTL cache (např. odpovědi z GitHub api)."""
    if not force_refresh and is_fresh(url, ttl, flavor="text"):
        return get_cached(url, "text")

    req_headers = {
        "User-Agent": "ZeddiHubTools/cache",
    }
    if headers:
        req_headers.update(headers)

    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return get_cached(url, "text")

    store(url, txt, flavor="text")
    return txt


def stats() -> Dict[str, Any]:
    """Diagnostika — vrátí počet záznamů a věk každého."""
    with _lock:
        items = []
        now = _now()
        for (url, flavor), (ts, _v) in _cache.items():
            items.append({"url": url, "flavor": flavor, "age_s": int(now - ts)})
    return {"count": len(items), "items": items}
