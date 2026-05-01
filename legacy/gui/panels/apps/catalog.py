"""
Quick-links catalog — fetches + caches ``quick_links.json`` from the website
and exposes search/filter helpers for the panel.

Schema (see also webhosting side ``tools/data/quick_links.json``):

    {
      "filter_groups": [
        {"id": "category", "label": "Kategorie", "options": [
          {"id": "gaming", "label": "Gaming"},
          {"id": "stats",  "label": "Statistiky"}
        ]}
      ],
      "items": [
        {
          "id":            "csgostats",
          "name":          "CSGOstats.gg",
          "description":   "Statistiky hráčů z CS2/CS:GO.",
          "icon":          "chart-line",
          "url":           "https://csgostats.gg/",
          "screenshot":    null,
          "open_mode":     "webview",   // webview | external | download
          "tags":          ["category:stats", "category:gaming"]
        }
      ]
    }
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...config import get_data_dir
from ...version import user_agent


CATALOG_URL = "https://zeddihub.eu/tools/data/quick_links.json"
CACHE_NAME = "quick_links.cache.json"
CACHE_TTL_SECONDS = 60 * 60 * 6  # 6 hours — admin edits propagate on next launch


def _cache_path() -> Path:
    return get_data_dir() / CACHE_NAME


def _fetch(url: str, timeout: float = 6.0) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent()})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Catalog root must be an object")
    # Normalize
    data.setdefault("filter_groups", [])
    data.setdefault("items", [])
    return data


def _read_cache() -> Optional[Dict[str, Any]]:
    p = _cache_path()
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception:
        return None


def _write_cache(data: Dict[str, Any]):
    p = _cache_path()
    try:
        payload = {"fetched_at": time.time(), "data": data}
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


class CatalogClient:
    """Async-friendly catalog loader with disk cache + manual refresh."""

    def __init__(self, url: str = CATALOG_URL):
        self.url = url
        self._data: Dict[str, Any] = {"filter_groups": [], "items": []}
        self._last_fetch: float = 0.0
        self._last_error: Optional[str] = None
        self._source: str = "empty"  # one of: empty | cache | network
        self._lock = threading.Lock()

    # ── Public props ──────────────────────────────────────────────────────
    @property
    def items(self) -> List[Dict[str, Any]]:
        return list(self._data.get("items") or [])

    @property
    def filter_groups(self) -> List[Dict[str, Any]]:
        return list(self._data.get("filter_groups") or [])

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    @property
    def source(self) -> str:
        return self._source

    # ── Loading ───────────────────────────────────────────────────────────
    def load_cached(self) -> bool:
        """Populate from disk cache if it exists and is not absurdly stale.

        Returns True if something was loaded.
        """
        cached = _read_cache()
        if not cached:
            return False
        with self._lock:
            self._data = cached.get("data", {"filter_groups": [], "items": []})
            self._last_fetch = float(cached.get("fetched_at") or 0.0)
            self._source = "cache"
        return True

    def refresh_async(self, on_done: Optional[Callable[[bool, Optional[str]], None]] = None,
                      force: bool = False):
        """Fetch the catalog in a background thread.

        Callback signature: ``on_done(success: bool, error_msg: str | None)``.
        Always called on the calling thread you route back via ``.after()``
        from the UI — this method does not touch Tk.
        """
        if not force and self.is_fresh():
            if on_done:
                on_done(True, None)
            return

        def _worker():
            success = False
            err: Optional[str] = None
            try:
                data = _fetch(self.url)
                with self._lock:
                    self._data = data
                    self._last_fetch = time.time()
                    self._last_error = None
                    self._source = "network"
                _write_cache(data)
                success = True
            except Exception as e:
                err = str(e)
                with self._lock:
                    self._last_error = err
            if on_done:
                try:
                    on_done(success, err)
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()

    def is_fresh(self) -> bool:
        return self._last_fetch > 0 and (time.time() - self._last_fetch) < CATALOG_TTL()

    # ── Filtering / search ────────────────────────────────────────────────
    def search(self, needle: str, active_filters: Dict[str, str]) -> List[Dict[str, Any]]:
        """Return items whose name/desc/tags match ``needle`` AND every
        ``active_filters`` entry (group_id → option_id).
        """
        needle = (needle or "").strip().lower()

        def _matches_text(item: Dict[str, Any]) -> bool:
            if not needle:
                return True
            hay = " ".join([
                str(item.get("name") or ""),
                str(item.get("description") or ""),
                " ".join(item.get("tags") or []),
            ]).lower()
            return needle in hay

        def _matches_filters(item: Dict[str, Any]) -> bool:
            tags = set(item.get("tags") or [])
            for group_id, option_id in active_filters.items():
                if not option_id:
                    continue
                if f"{group_id}:{option_id}" not in tags:
                    return False
            return True

        return [it for it in self.items if _matches_text(it) and _matches_filters(it)]


def CATALOG_TTL() -> int:
    """Wrapped as function so test code can monkey-patch."""
    return CACHE_TTL_SECONDS


__all__ = ["CatalogClient", "CATALOG_URL"]
