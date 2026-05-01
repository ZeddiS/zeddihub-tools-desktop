"""
MacroRecorder — captures keyboard + mouse events via pynput listeners into a
list of :mod:`model` step dicts.

Design:
  • Start / stop is explicit (called from UI).
  • While recording, every event is timestamped; on each event the gap since
    the previous one is emitted as a ``wait`` step (minimum 10 ms so you don't
    get hundreds of zero-length waits).
  • A configurable "stop hotkey" (default F8) ends recording without the user
    having to click back into the panel.
  • The returned list of steps is in chronological order and directly
    compatible with :class:`MacroEngine`.

Recorded step types:
    key_press   / key_release   for every key down / up
    mouse_click                 (press + release collapse into one click step
                                 with button + coords)
    mouse_move                  (sampled at max ~20 Hz to avoid log spam)
    wait                         (gap between events)
"""

from __future__ import annotations

import time
import threading
from typing import Callable, Dict, List, Optional

try:
    from pynput import keyboard as _kb, mouse as _ms
    from pynput.keyboard import Key as _Key
    PYNPUT_OK = True
except Exception:
    _kb = None
    _ms = None
    _Key = None
    PYNPUT_OK = False


# Reverse-ish key name map (from pynput Key.xxx back to the string our model uses)
_KEY_NAME_OVERRIDES = {
    "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "shift_l": "shift", "shift_r": "shift",
    "alt_l": "alt", "alt_r": "alt_gr",
    "cmd": "win", "cmd_l": "win", "cmd_r": "win",
}


def _key_to_name(key) -> str:
    if _Key is None:
        return ""
    if isinstance(key, _Key):
        name = getattr(key, "name", None) or str(key).replace("Key.", "")
        return _KEY_NAME_OVERRIDES.get(name, name)
    # KeyCode
    try:
        c = getattr(key, "char", None)
        if c:
            return c
    except Exception:
        pass
    try:
        vk = getattr(key, "vk", None)
        if vk is not None:
            return f"vk_{vk}"
    except Exception:
        pass
    return str(key)


class MacroRecorder:
    #: Minimum gap between two events to be recorded as its own ``wait`` step.
    MIN_WAIT_MS = 10
    #: Throttle for mouse_move sampling (don't emit faster than ~20 Hz).
    MOVE_SAMPLE_MS = 50

    def __init__(
        self,
        *,
        on_event: Optional[Callable[[str], None]] = None,
        stop_key_name: str = "f8",
        capture_mouse_move: bool = False,
    ):
        self._on_event = on_event or (lambda s: None)
        self._stop_key_name = stop_key_name.lower()
        self._capture_mouse_move = capture_mouse_move

        self._steps: List[Dict] = []
        self._kb_listener = None
        self._ms_listener = None
        self._last_ts: Optional[float] = None
        self._last_move_ts: float = 0.0
        self._recording = False
        self._lock = threading.Lock()
        #: Set once when the stop hotkey fires so the UI can react.
        self._stop_requested = threading.Event()
        self._on_stop: Optional[Callable[[], None]] = None

    @property
    def steps(self) -> List[Dict]:
        return list(self._steps)

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested.is_set()

    # ── Start / stop ───────────────────────────────────────────────────────
    def start(self, *, on_stop: Optional[Callable[[], None]] = None):
        if not PYNPUT_OK or self._recording:
            return
        self._steps.clear()
        self._last_ts = None
        self._last_move_ts = 0.0
        self._stop_requested.clear()
        self._on_stop = on_stop
        self._recording = True
        self._kb_listener = _kb.Listener(on_press=self._on_press,
                                          on_release=self._on_release)
        self._kb_listener.start()
        if self._capture_mouse_move:
            self._ms_listener = _ms.Listener(on_click=self._on_click,
                                              on_move=self._on_move,
                                              on_scroll=self._on_scroll)
        else:
            self._ms_listener = _ms.Listener(on_click=self._on_click,
                                              on_scroll=self._on_scroll)
        self._ms_listener.start()
        self._on_event("recording")

    def stop(self) -> List[Dict]:
        if not self._recording:
            return self._steps
        self._recording = False
        try:
            if self._kb_listener is not None:
                self._kb_listener.stop()
        except Exception:
            pass
        try:
            if self._ms_listener is not None:
                self._ms_listener.stop()
        except Exception:
            pass
        self._kb_listener = None
        self._ms_listener = None
        self._on_event("stopped")
        return self._steps

    # ── Event handlers ─────────────────────────────────────────────────────
    def _gap_ms(self) -> int:
        now = time.monotonic()
        if self._last_ts is None:
            self._last_ts = now
            return 0
        dt = int((now - self._last_ts) * 1000)
        self._last_ts = now
        return dt

    def _emit_wait(self):
        gap = self._gap_ms()
        if gap >= self.MIN_WAIT_MS:
            with self._lock:
                self._steps.append({"type": "wait", "ms": gap})

    def _on_press(self, key):
        if not self._recording:
            return
        name = _key_to_name(key).lower()
        # stop hotkey handling
        if name == self._stop_key_name:
            self._stop_requested.set()
            if self._on_stop:
                try:
                    self._on_stop()
                except Exception:
                    pass
            # stop listeners from this thread is fine; do NOT append the stop key
            return False  # pynput: stop listener
        self._emit_wait()
        with self._lock:
            self._steps.append({"type": "key_press", "key": name})

    def _on_release(self, key):
        if not self._recording:
            return
        name = _key_to_name(key).lower()
        if name == self._stop_key_name:
            return False
        self._emit_wait()
        with self._lock:
            self._steps.append({"type": "key_release", "key": name})

    def _on_click(self, x, y, button, pressed):
        if not self._recording:
            return
        if not pressed:
            # We collapse press+release into a single mouse_click step on press
            # so we ignore the release event.
            return
        btn = getattr(button, "name", "left")
        self._emit_wait()
        with self._lock:
            self._steps.append({
                "type": "mouse_click",
                "button": btn,
                "x": int(x), "y": int(y),
                "clicks": 1,
                "hold_ms": 0,
            })

    def _on_move(self, x, y):
        if not self._recording or not self._capture_mouse_move:
            return
        now = time.monotonic() * 1000
        if now - self._last_move_ts < self.MOVE_SAMPLE_MS:
            return
        self._last_move_ts = now
        self._emit_wait()
        with self._lock:
            self._steps.append({
                "type": "mouse_move",
                "x": int(x), "y": int(y), "relative": False,
            })

    def _on_scroll(self, x, y, dx, dy):
        if not self._recording:
            return
        self._emit_wait()
        with self._lock:
            self._steps.append({
                "type": "mouse_scroll",
                "dx": int(dx), "dy": int(dy),
            })


__all__ = ["MacroRecorder", "PYNPUT_OK"]
