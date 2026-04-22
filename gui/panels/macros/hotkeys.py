"""
HotkeyManager — binds global hotkeys (F-keys or Ctrl/Shift/Alt combos) to
callbacks using ``pynput.keyboard.GlobalHotKeys``. Survives tray minimize.

Features:
  • Conflict detection: registering a combo already bound by another macro
    raises ``HotkeyConflict`` which the UI can surface to the user.
  • Live re-binding: :meth:`apply` replaces the whole listener atomically so
    edits to one macro can't lose bindings of another.
  • Accepts a liberal spelling: ``F6``, ``f6``, ``Ctrl+Shift+M``, ``ctrl+shift+m``.
"""

from __future__ import annotations

import threading
from typing import Callable, Dict, List, Optional, Tuple

try:
    from pynput import keyboard as _kb
    PYNPUT_OK = True
except Exception:
    _kb = None
    PYNPUT_OK = False


class HotkeyConflict(Exception):
    def __init__(self, combo: str, owner: str):
        super().__init__(f"Hotkey {combo} už používá makro „{owner}\"")
        self.combo = combo
        self.owner = owner


def _normalize(combo: str) -> str:
    """Normalize ``'Ctrl + Shift + m'`` → ``'<ctrl>+<shift>+m'`` (pynput syntax)."""
    if not combo:
        return ""
    parts = [p.strip().lower() for p in combo.replace("-", "+").split("+") if p.strip()]
    out: List[str] = []
    for p in parts:
        # pynput wants <ctrl> / <shift> / <alt> / <cmd> with angle brackets for modifiers,
        # and single chars or function keys as-is (<f6>)
        if p in ("ctrl", "control", "shift", "alt", "alt_gr", "cmd", "win", "super"):
            mapped = {
                "control": "ctrl",
                "win": "cmd", "super": "cmd",
            }.get(p, p)
            out.append(f"<{mapped}>")
        elif p.startswith("f") and p[1:].isdigit() and 1 <= int(p[1:]) <= 24:
            out.append(f"<{p}>")
        elif p in ("esc", "escape", "tab", "space", "enter", "return", "backspace",
                   "delete", "home", "end", "page_up", "page_down",
                   "up", "down", "left", "right", "insert"):
            out.append(f"<{'enter' if p in ('enter','return') else p}>")
        elif len(p) == 1:
            out.append(p)
        else:
            out.append(p)
    return "+".join(out)


def _display(combo: str) -> str:
    """Pretty-print a normalized or raw combo for UI."""
    parts = [p.strip().strip("<>") for p in (combo or "").replace("-", "+").split("+")]
    return "+".join(p.upper() if len(p) <= 3 else p.capitalize() for p in parts if p)


class HotkeyManager:
    def __init__(self, *, on_error: Optional[Callable[[str], None]] = None):
        self._bindings: Dict[str, Tuple[str, Callable]] = {}
        #: ``combo_norm → (macro_id, callback)``
        self._owner_by_combo: Dict[str, str] = {}
        self._listener = None
        self._on_error = on_error or (lambda msg: None)
        self._lock = threading.Lock()

    # ── Registration ──────────────────────────────────────────────────────
    def set_binding(self, macro_id: str, combo: Optional[str],
                    callback: Callable, *, macro_name: str = ""):
        """Assign ``combo`` to ``macro_id``. Pass ``None`` / empty to unbind.

        Raises :class:`HotkeyConflict` when another macro owns ``combo``.
        """
        with self._lock:
            # Always clear the previous binding for this macro first
            self._unbind_macro(macro_id)
            if not combo:
                self._rebuild_unlocked()
                return
            norm = _normalize(combo)
            if not norm:
                self._rebuild_unlocked()
                return
            owner = self._owner_by_combo.get(norm)
            if owner and owner != macro_id:
                raise HotkeyConflict(combo, owner)
            self._bindings[macro_id] = (norm, callback)
            self._owner_by_combo[norm] = macro_id
            self._rebuild_unlocked()

    def clear_all(self):
        with self._lock:
            self._bindings.clear()
            self._owner_by_combo.clear()
            self._rebuild_unlocked()

    def list_bindings(self) -> List[Tuple[str, str]]:
        """Return ``[(macro_id, combo_display), ...]`` for UI inspection."""
        return [(mid, _display(combo)) for mid, (combo, _cb) in self._bindings.items()]

    # ── Internal ──────────────────────────────────────────────────────────
    def _unbind_macro(self, macro_id: str):
        cur = self._bindings.pop(macro_id, None)
        if cur:
            combo_norm, _cb = cur
            if self._owner_by_combo.get(combo_norm) == macro_id:
                self._owner_by_combo.pop(combo_norm, None)

    def _rebuild_unlocked(self):
        # Stop existing listener (if any)
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

        if not PYNPUT_OK or not self._bindings:
            return

        bound = {}
        for macro_id, (combo_norm, cb) in self._bindings.items():
            # Wrap to run the callback in a daemon thread so pynput's hotkey
            # thread doesn't block the next press.
            def _make(c=cb):
                def _wrap():
                    import threading as _th
                    _th.Thread(target=c, daemon=True).start()
                return _wrap
            bound[combo_norm] = _make()

        try:
            self._listener = _kb.GlobalHotKeys(bound)
            self._listener.start()
        except Exception as e:
            self._on_error(f"Nelze aktivovat hotkeys: {e}")


__all__ = ["HotkeyManager", "HotkeyConflict", "PYNPUT_OK", "_display", "_normalize"]
