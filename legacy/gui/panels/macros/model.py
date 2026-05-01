"""
Macro domain model — dataclasses + JSON (de)serialization.

A ``Macro`` is a named sequence of ``Step`` instances with optional trigger,
metadata and playback settings. Steps are plain dicts with a ``type`` key plus
type-specific fields (see STEP_TYPES below); we keep them as dicts rather than
subclasses so JSON round-trips trivially and the step editor can edit them
generically.

Step types (v1.7.6):
    key_press      {"key": "<name>"}
    key_release    {"key": "<name>"}
    key_tap        {"key": "<name>"}                   # press + release
    key_combo      {"keys": ["ctrl", "c"]}             # press all, release reverse
    key_type       {"text": "...", "interval_ms": 5}   # type literal string
    mouse_move     {"x": int, "y": int, "relative": bool}
    mouse_click    {"button": "left|right|middle",
                    "x": int|None, "y": int|None,
                    "clicks": int, "hold_ms": int}
    mouse_scroll   {"dx": int, "dy": int}
    wait           {"ms": int}
    wait_random    {"min_ms": int, "max_ms": int}
    loop_start     {"count": int}                      # 0 = infinite (stop via hotkey)
    loop_end       {}
    if_pixel       {"x": int, "y": int, "rgb": [r,g,b], "tolerance": int}
    endif          {}
    comment        {"text": "..."}

Triggers:
    {"type": "manual"}                            # play button only
    {"type": "hotkey", "combo": "F6"}             # global hotkey (pynput)
    {"type": "hotkey", "combo": "ctrl+shift+m"}
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, List, Dict, Optional


# List used by the step editor dropdown
STEP_TYPES: List[str] = [
    "key_tap",
    "key_combo",
    "key_press",
    "key_release",
    "key_type",
    "mouse_click",
    "mouse_move",
    "mouse_scroll",
    "wait",
    "wait_random",
    "loop_start",
    "loop_end",
    "if_pixel",
    "endif",
    "comment",
]


STEP_LABELS = {
    "key_tap":     "⌨ Stisknout klávesu",
    "key_combo":   "⌨ Kombinace kláves",
    "key_press":   "⌨ Držet klávesu",
    "key_release": "⌨ Pustit klávesu",
    "key_type":    "⌨ Napsat text",
    "mouse_click": "🖱 Kliknout myší",
    "mouse_move":  "🖱 Posun myši",
    "mouse_scroll":"🖱 Scroll",
    "wait":        "⏱ Čekat",
    "wait_random": "⏱ Čekat (náhodně)",
    "loop_start":  "🔁 Začátek smyčky",
    "loop_end":    "🔁 Konec smyčky",
    "if_pixel":    "🎨 Podmínka: barva pixelu",
    "endif":       "🎨 Konec podmínky",
    "comment":     "💬 Komentář",
}


DEFAULT_STEP: Dict[str, Dict[str, Any]] = {
    "key_tap":     {"key": "a"},
    "key_combo":   {"keys": ["ctrl", "c"]},
    "key_press":   {"key": "a"},
    "key_release": {"key": "a"},
    "key_type":    {"text": "", "interval_ms": 10},
    "mouse_click": {"button": "left", "x": None, "y": None, "clicks": 1, "hold_ms": 0},
    "mouse_move":  {"x": 0, "y": 0, "relative": False},
    "mouse_scroll":{"dx": 0, "dy": 1},
    "wait":        {"ms": 500},
    "wait_random": {"min_ms": 100, "max_ms": 300},
    "loop_start":  {"count": 3},
    "loop_end":    {},
    "if_pixel":    {"x": 0, "y": 0, "rgb": [255, 255, 255], "tolerance": 10},
    "endif":       {},
    "comment":     {"text": ""},
}


def make_step(step_type: str, **overrides) -> Dict[str, Any]:
    base = {"type": step_type}
    base.update(DEFAULT_STEP.get(step_type, {}))
    base.update(overrides)
    return base


def summarize_step(step: Dict[str, Any]) -> str:
    """One-line human-readable summary of a step for the list view."""
    t = step.get("type", "?")
    if t == "key_tap":
        return f"Klávesa   {step.get('key', '?')}"
    if t == "key_combo":
        return f"Kombinace {'+'.join(step.get('keys', []))}"
    if t == "key_press":
        return f"Držet     {step.get('key', '?')}"
    if t == "key_release":
        return f"Pustit    {step.get('key', '?')}"
    if t == "key_type":
        txt = step.get("text", "")
        if len(txt) > 40:
            txt = txt[:37] + "…"
        return f"Napsat    '{txt}'"
    if t == "mouse_click":
        xy = ""
        if step.get("x") is not None and step.get("y") is not None:
            xy = f" @ {step['x']},{step['y']}"
        return f"Klik {step.get('button', 'left')}{xy} × {step.get('clicks', 1)}"
    if t == "mouse_move":
        mode = "rel" if step.get("relative") else "abs"
        return f"Přesun    {step.get('x', 0)},{step.get('y', 0)} ({mode})"
    if t == "mouse_scroll":
        return f"Scroll    dx={step.get('dx', 0)} dy={step.get('dy', 0)}"
    if t == "wait":
        return f"Čekat     {step.get('ms', 0)} ms"
    if t == "wait_random":
        return f"Čekat     {step.get('min_ms', 0)}–{step.get('max_ms', 0)} ms"
    if t == "loop_start":
        c = step.get("count", 0)
        return f"◄ Smyčka × {c if c > 0 else '∞'}"
    if t == "loop_end":
        return "◄ Konec smyčky"
    if t == "if_pixel":
        r, g, b = step.get("rgb", [0, 0, 0])
        return f"IF pixel @ {step.get('x', 0)},{step.get('y', 0)} ≈ RGB({r},{g},{b})"
    if t == "endif":
        return "END IF"
    if t == "comment":
        return f"# {step.get('text', '')}"
    return f"? {t}"


@dataclass
class Macro:
    id: str
    name: str
    description: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    trigger: Dict[str, Any] = field(default_factory=lambda: {"type": "manual"})
    playback_speed: float = 1.0
    created_at: float = 0.0
    updated_at: float = 0.0
    tags: List[str] = field(default_factory=list)

    @classmethod
    def new(cls, name: str) -> "Macro":
        now = time.time()
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            created_at=now,
            updated_at=now,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Macro":
        return cls(
            id=d.get("id") or uuid.uuid4().hex,
            name=d.get("name", "Bez názvu"),
            description=d.get("description", ""),
            steps=list(d.get("steps") or []),
            trigger=dict(d.get("trigger") or {"type": "manual"}),
            playback_speed=float(d.get("playback_speed") or 1.0),
            created_at=float(d.get("created_at") or time.time()),
            updated_at=float(d.get("updated_at") or time.time()),
            tags=list(d.get("tags") or []),
        )

    def touch(self):
        self.updated_at = time.time()

    def hotkey_combo(self) -> Optional[str]:
        tr = self.trigger or {}
        if tr.get("type") == "hotkey":
            combo = tr.get("combo")
            if isinstance(combo, str) and combo.strip():
                return combo.strip().lower()
        return None


__all__ = [
    "Macro",
    "STEP_TYPES",
    "STEP_LABELS",
    "DEFAULT_STEP",
    "make_step",
    "summarize_step",
]
