"""
MacroEngine — plays a Macro's steps in a daemon thread using pynput.

Features:
  • Loop / endif skip logic without needing a compiler pass.
  • Playback speed multiplier (0.25× – 4.0×) applied to every wait.
  • Global stop flag — callers can call :meth:`stop` any time; the engine
    tolerates being stopped mid-wait via a short polling sleep.
  • if_pixel condition via PIL ImageGrab (optional; if PIL missing the step
    is treated as true).
  • on_state/on_error/on_step callbacks for the UI (all fired via .after()
    wrapper supplied by caller — engine itself never touches Tk).
"""

from __future__ import annotations

import random
import threading
import time
import traceback
from typing import Callable, Dict, List, Optional

try:  # pragma: no cover - optional
    from pynput.keyboard import Controller as KeyboardController, Key as _Key
    from pynput.mouse import Controller as MouseController, Button as _Button
    PYNPUT_OK = True
except Exception:
    KeyboardController = None
    MouseController = None
    _Key = None
    _Button = None
    PYNPUT_OK = False

try:  # pragma: no cover
    from PIL import ImageGrab
    PIL_OK = True
except Exception:
    ImageGrab = None
    PIL_OK = False


# ── Key name resolution ───────────────────────────────────────────────────
# Map human-friendly names (as emitted by recorder.py or typed by user) to
# pynput Key members or literal chars.
_SPECIAL_KEYS = {
    "ctrl":        "ctrl_l",
    "control":     "ctrl_l",
    "ctrl_l":      "ctrl_l",
    "ctrl_r":      "ctrl_r",
    "shift":       "shift",
    "shift_l":     "shift_l",
    "shift_r":     "shift_r",
    "alt":         "alt_l",
    "alt_l":       "alt_l",
    "alt_r":       "alt_r",
    "win":         "cmd",
    "super":       "cmd",
    "meta":        "cmd",
    "cmd":         "cmd",
    "esc":         "esc",
    "escape":      "esc",
    "tab":         "tab",
    "space":       "space",
    "enter":       "enter",
    "return":      "enter",
    "backspace":   "backspace",
    "delete":      "delete",
    "del":         "delete",
    "home":        "home",
    "end":         "end",
    "page_up":     "page_up",
    "page_down":   "page_down",
    "pageup":      "page_up",
    "pagedown":    "page_down",
    "up":          "up",
    "down":        "down",
    "left":        "left",
    "right":       "right",
    "insert":      "insert",
    "caps_lock":   "caps_lock",
    "num_lock":    "num_lock",
    "scroll_lock": "scroll_lock",
    "print_screen":"print_screen",
    "menu":        "menu",
}
for _i in range(1, 25):
    _SPECIAL_KEYS[f"f{_i}"] = f"f{_i}"


def _resolve_key(name: str):
    """Convert a key name like ``'ctrl'`` / ``'F6'`` / ``'a'`` into a pynput
    Key enum or the raw character for ``press()``."""
    if not isinstance(name, str):
        return None
    n = name.strip().lower()
    if not n:
        return None
    if n in _SPECIAL_KEYS and _Key is not None:
        key_attr = _SPECIAL_KEYS[n]
        return getattr(_Key, key_attr, n)
    # fall back to literal char
    return name[0] if len(name) >= 1 else None


def _resolve_button(name: str):
    if _Button is None:
        return None
    n = (name or "left").lower()
    if n in ("right", "r"):
        return _Button.right
    if n in ("middle", "m", "center"):
        return _Button.middle
    return _Button.left


class MacroEngine:
    def __init__(
        self,
        *,
        on_state: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_step:  Optional[Callable[[int, int], None]] = None,
    ):
        self._kb = KeyboardController() if PYNPUT_OK else None
        self._mouse = MouseController() if PYNPUT_OK else None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._running = False
        self._on_state = on_state or (lambda s: None)
        self._on_error = on_error or (lambda m: None)
        self._on_step = on_step or (lambda cur, total: None)

    # ── Control ───────────────────────────────────────────────────────────
    @property
    def running(self) -> bool:
        return self._running

    def play(self, steps: List[Dict], *, speed: float = 1.0):
        if not PYNPUT_OK:
            self._on_error("pynput není dostupný — makra nelze spustit.")
            return
        if self._running:
            return
        self._stop.clear()
        self._running = True
        self._on_state("running")
        t = threading.Thread(target=self._run, args=(steps, speed), daemon=True)
        self._thread = t
        t.start()

    def stop(self):
        self._stop.set()

    # ── Playback loop ─────────────────────────────────────────────────────
    def _run(self, steps: List[Dict], speed: float):
        try:
            self._execute(steps, max(0.05, min(10.0, float(speed))))
        except Exception as e:
            self._on_error(f"{e}\n\n{traceback.format_exc()}")
        finally:
            self._running = False
            self._on_state("idle")

    # control-flow bookkeeping
    def _execute(self, steps: List[Dict], speed: float):
        total = len(steps)
        if total == 0:
            return
        # Pre-compute jump tables for matched loop_start/loop_end and if/endif
        loop_match = self._match_pairs(steps, "loop_start", "loop_end")
        if_match = self._match_pairs(steps, "if_pixel", "endif")

        loop_stack: List[Dict] = []   # [{"start": idx, "end": idx, "remaining": int}]
        skip_until: Optional[int] = None

        i = 0
        while i < total and not self._stop.is_set():
            step = steps[i]
            t = step.get("type")

            # skipping inside a false branch
            if skip_until is not None:
                if i == skip_until:
                    skip_until = None
                i += 1
                continue

            self._on_step(i + 1, total)

            if t == "loop_start":
                count = int(step.get("count", 0) or 0)
                end_idx = loop_match.get(i, None)
                if end_idx is None:
                    # unmatched — skip silently
                    pass
                else:
                    loop_stack.append({"start": i, "end": end_idx,
                                       "remaining": count if count > 0 else -1})
            elif t == "loop_end":
                if loop_stack:
                    frame = loop_stack[-1]
                    if frame["remaining"] == -1:
                        # infinite — always loop
                        i = frame["start"]
                        continue
                    frame["remaining"] -= 1
                    if frame["remaining"] > 0:
                        i = frame["start"]
                        continue
                    loop_stack.pop()
            elif t == "if_pixel":
                truthy = self._check_pixel(step)
                if not truthy:
                    skip_until = if_match.get(i, i)
            elif t == "endif":
                pass
            else:
                self._run_single(step, speed)

            i += 1

    # ── Step execution ────────────────────────────────────────────────────
    def _run_single(self, step: Dict, speed: float):
        t = step.get("type")
        try:
            if t == "key_tap":
                k = _resolve_key(step.get("key", ""))
                if k is not None:
                    self._kb.press(k)
                    self._kb.release(k)
            elif t == "key_press":
                k = _resolve_key(step.get("key", ""))
                if k is not None:
                    self._kb.press(k)
            elif t == "key_release":
                k = _resolve_key(step.get("key", ""))
                if k is not None:
                    self._kb.release(k)
            elif t == "key_combo":
                keys = [_resolve_key(k) for k in (step.get("keys") or [])]
                keys = [k for k in keys if k is not None]
                for k in keys:
                    self._kb.press(k)
                for k in reversed(keys):
                    self._kb.release(k)
            elif t == "key_type":
                text = step.get("text", "") or ""
                interval = max(0, int(step.get("interval_ms", 0) or 0)) / 1000.0
                for ch in text:
                    if self._stop.is_set():
                        return
                    try:
                        self._kb.type(ch)
                    except Exception:
                        # fall back to press/release for chars pynput can't type
                        try:
                            self._kb.press(ch)
                            self._kb.release(ch)
                        except Exception:
                            pass
                    if interval:
                        self._interruptible_sleep(interval / speed)
            elif t == "mouse_click":
                btn = _resolve_button(step.get("button", "left"))
                x = step.get("x"); y = step.get("y")
                clicks = max(1, int(step.get("clicks", 1) or 1))
                hold = max(0, int(step.get("hold_ms", 0) or 0)) / 1000.0
                if x is not None and y is not None:
                    self._mouse.position = (int(x), int(y))
                for _ in range(clicks):
                    if self._stop.is_set():
                        return
                    self._mouse.press(btn)
                    if hold > 0:
                        self._interruptible_sleep(hold / speed)
                    self._mouse.release(btn)
            elif t == "mouse_move":
                x = int(step.get("x", 0) or 0); y = int(step.get("y", 0) or 0)
                if step.get("relative"):
                    cx, cy = self._mouse.position
                    self._mouse.position = (cx + x, cy + y)
                else:
                    self._mouse.position = (x, y)
            elif t == "mouse_scroll":
                dx = int(step.get("dx", 0) or 0); dy = int(step.get("dy", 0) or 0)
                self._mouse.scroll(dx, dy)
            elif t == "wait":
                ms = max(0, int(step.get("ms", 0) or 0))
                self._interruptible_sleep((ms / 1000.0) / speed)
            elif t == "wait_random":
                lo = max(0, int(step.get("min_ms", 0) or 0))
                hi = max(lo, int(step.get("max_ms", lo) or lo))
                ms = random.randint(lo, hi)
                self._interruptible_sleep((ms / 1000.0) / speed)
            elif t == "comment":
                pass
            # else: unknown step — ignore
        except Exception as e:
            self._on_error(f"Krok '{t}' selhal: {e}")

    # ── Helpers ───────────────────────────────────────────────────────────
    def _interruptible_sleep(self, seconds: float):
        """Sleep in 30 ms chunks so ``stop()`` feels responsive."""
        if seconds <= 0:
            return
        end = time.monotonic() + seconds
        while not self._stop.is_set():
            remaining = end - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(0.03, remaining))

    @staticmethod
    def _match_pairs(steps: List[Dict], start_type: str, end_type: str) -> Dict[int, int]:
        """Return dict mapping opener index → closer index for matched pairs."""
        stack: List[int] = []
        out: Dict[int, int] = {}
        for i, s in enumerate(steps):
            t = s.get("type")
            if t == start_type:
                stack.append(i)
            elif t == end_type and stack:
                opener = stack.pop()
                out[opener] = i
        return out

    def _check_pixel(self, step: Dict) -> bool:
        if not PIL_OK:
            return True  # lenient fallback
        try:
            x = int(step.get("x", 0) or 0); y = int(step.get("y", 0) or 0)
            want = step.get("rgb") or [0, 0, 0]
            tol = int(step.get("tolerance", 0) or 0)
            img = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
            got = img.getpixel((0, 0))
            if isinstance(got, int):
                got = (got, got, got)
            got = got[:3]
            for a, b in zip(got, want):
                if abs(int(a) - int(b)) > tol:
                    return False
            return True
        except Exception:
            return True


__all__ = ["MacroEngine", "PYNPUT_OK"]
