"""
Macro persistence — JSON file per macro in <data_dir>/macros/.

One file per macro keeps diffs small and makes import/export trivial (users
can e-mail a single ``.json``). An in-memory cache is refreshed via
:meth:`MacroStore.reload` which is called lazily on first access.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from ...config import get_data_dir
from .model import Macro


_NAME_SAFE = re.compile(r"[^A-Za-z0-9_.\- ]+")


def _sanitize_filename(name: str) -> str:
    s = _NAME_SAFE.sub("_", name).strip().strip(".")
    return s[:80] or "macro"


class MacroStore:
    def __init__(self, directory: Optional[Path] = None):
        self.dir: Path = directory or (get_data_dir() / "macros")
        self.dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Macro] = {}
        self._loaded = False

    # ── Loading ────────────────────────────────────────────────────────────
    def reload(self) -> List[Macro]:
        self._cache.clear()
        for p in sorted(self.dir.glob("*.json")):
            try:
                with open(p, encoding="utf-8") as fh:
                    data = json.load(fh)
                m = Macro.from_dict(data)
                # Remember filesystem path for later saves/renames
                setattr(m, "_file", p)
                self._cache[m.id] = m
            except Exception:
                # Skip unreadable files but keep going
                continue
        self._loaded = True
        return self.all()

    def _ensure_loaded(self):
        if not self._loaded:
            self.reload()

    # ── Access ─────────────────────────────────────────────────────────────
    def all(self) -> List[Macro]:
        self._ensure_loaded()
        return sorted(self._cache.values(), key=lambda m: m.name.lower())

    def get(self, macro_id: str) -> Optional[Macro]:
        self._ensure_loaded()
        return self._cache.get(macro_id)

    # ── Mutation ───────────────────────────────────────────────────────────
    def save(self, macro: Macro) -> Path:
        self._ensure_loaded()
        macro.touch()
        path = getattr(macro, "_file", None)
        desired = self.dir / f"{_sanitize_filename(macro.name)}_{macro.id[:8]}.json"
        if path is None or Path(path).name != desired.name:
            # first save OR rename: drop old file if present
            old_path: Optional[Path] = path if isinstance(path, Path) else None
            path = desired
            setattr(macro, "_file", path)
            if old_path and old_path.exists() and old_path != path:
                try:
                    old_path.unlink()
                except Exception:
                    pass
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(macro.to_json())
        self._cache[macro.id] = macro
        return path

    def delete(self, macro_id: str) -> bool:
        self._ensure_loaded()
        m = self._cache.pop(macro_id, None)
        if not m:
            return False
        path = getattr(m, "_file", None)
        if path and Path(path).exists():
            try:
                Path(path).unlink()
            except Exception:
                return False
        return True

    def duplicate(self, macro_id: str) -> Optional[Macro]:
        m = self.get(macro_id)
        if not m:
            return None
        clone = Macro.from_dict(json.loads(m.to_json()))
        import uuid as _uuid
        clone.id = _uuid.uuid4().hex
        clone.name = f"{m.name} (kopie)"
        # hotkey musí být unikátní — na kopii zrušíme
        clone.trigger = {"type": "manual"}
        self.save(clone)
        return clone

    # ── Import / Export ────────────────────────────────────────────────────
    def export_to(self, macro_id: str, dst: Path) -> Optional[Path]:
        m = self.get(macro_id)
        if not m:
            return None
        dst = Path(dst)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(m.to_json())
        return dst

    def import_from(self, src: Path) -> Optional[Macro]:
        src = Path(src)
        try:
            with open(src, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return None
        m = Macro.from_dict(data)
        import uuid as _uuid
        # Always re-mint ID on import to avoid collisions
        m.id = _uuid.uuid4().hex
        # clear trigger to avoid immediate hotkey collision
        m.trigger = {"type": "manual"}
        self.save(m)
        return m


__all__ = ["MacroStore"]
