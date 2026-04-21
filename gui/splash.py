"""
ZeddiHub Tools - Splash / loading screen shown on startup.
Professional launch animation: fade-in, smooth interpolated progress bar,
shimmer highlight, cross-fade status text, fade-out before hand-off.
"""

import tkinter as tk
import threading
import time
import math
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

BANNER_URL = "https://files.zeddihub.eu/logo.png"
LOGO_URL   = "https://files.zeddihub.eu/logo2.png"
ASSETS_DIR = Path(__file__).parent.parent / "assets"
BANNER_PATH = ASSETS_DIR / "banner.png"
LOGO_PATH   = ASSETS_DIR / "logo.png"
ICON_PATH   = ASSETS_DIR / "web_favicon.ico"

SPLASH_BG       = "#0a0a0f"
SPLASH_FG       = "#f0a500"
SPLASH_FG_ALT   = "#ffb91f"
SPLASH_GLOW     = "#ffcf5c"
SPLASH_TEXT     = "#f5f5f7"
SPLASH_DIM      = "#7a7a90"
SPLASH_TRACK    = "#1a1a24"

INTRO_LINES = [
    "Inicializace systému...",
    "Načítání modulů nástrojů...",
    "Připojování k ZeddiHub...",
    "Aplikace je připravena.",
]


def _download_asset(url: str, path: Path) -> bool:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return True
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception:
        return False


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(c))) for c in rgb))


def _mix(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


class SplashScreen:
    def __init__(self, on_done_callback):
        self.on_done = on_done_callback
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=SPLASH_BG)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", 0.0)
        except Exception:
            pass

        w, h = 700, 380
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self._w, self._h = w, h
        self._target_pct = 0.0
        self._current_pct = 0.0
        self._shimmer_phase = 0.0
        self._status_alpha = 1.0
        self._pending_status = None
        self._closing = False

        self._build_ui(w, h)
        self.root.update_idletasks()
        self.root.update()

        self._fade_in()
        self._tick()
        self._start_sequence()

    def _build_ui(self, w, h):
        self.canvas = tk.Canvas(
            self.root, width=w, height=h,
            bg=SPLASH_BG, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_rectangle(0, 0, w, h, fill=SPLASH_BG, outline="")

        self.banner_img_ref = None
        if PIL_OK and BANNER_PATH.exists():
            self._show_banner(w, h)
        else:
            self._show_text_logo(w)

        self.canvas.create_text(
            w // 2, h - 114,
            text="ZeddiHub Tools",
            fill=SPLASH_TEXT, font=("Segoe UI", 18, "bold")
        )
        try:
            from .version import APP_VERSION as _v
            _ver = f"v{_v}"
        except Exception:
            _ver = ""
        self.canvas.create_text(
            w // 2, h - 90,
            text=f"{_ver}  \u2009\u00b7\u2009  by ZeddiS  \u2009\u00b7\u2009  zeddihub.eu" if _ver
                 else "by ZeddiS  \u2009\u00b7\u2009  zeddihub.eu",
            fill=SPLASH_DIM, font=("Segoe UI", 11)
        )

        # Status text as canvas text so we can fade it via color
        self._status_text = "Spouštění..."
        self._status_text_id = self.canvas.create_text(
            w // 2, h - 58,
            text=self._status_text,
            fill=SPLASH_DIM, font=("Segoe UI", 10)
        )

        # Thin track
        bar_left, bar_right = 80, w - 80
        bar_top, bar_bot = h - 38, h - 36
        self.canvas.create_rectangle(bar_left, bar_top, bar_right, bar_bot,
                                     fill=SPLASH_TRACK, outline="")
        self.progress_bar = self.canvas.create_rectangle(
            bar_left, bar_top, bar_left, bar_bot, fill=SPLASH_FG, outline=""
        )
        # Shimmer highlight (a slightly brighter moving gradient cap)
        self.shimmer = self.canvas.create_rectangle(
            bar_left, bar_top, bar_left, bar_bot, fill=SPLASH_GLOW, outline=""
        )
        self._bar_bounds = (bar_left, bar_top, bar_right, bar_bot)
        self._bar_w = bar_right - bar_left

    def _show_banner(self, w, h):
        try:
            img = Image.open(BANNER_PATH)
            img.thumbnail((500, 160), Image.LANCZOS)
            self.banner_img_ref = ImageTk.PhotoImage(img)
            self.canvas.create_image(w // 2, 120, image=self.banner_img_ref, anchor="center")
        except Exception:
            self._show_text_logo(w)

    def _show_text_logo(self, w):
        self.canvas.create_text(
            w // 2, 140,
            text="ZeddiHub Tools",
            fill=SPLASH_FG, font=("Segoe UI", 34, "bold")
        )

    def _fade_in(self, duration_ms: int = 160):
        steps = max(8, duration_ms // 16)
        inc = 1.0 / steps

        def step(a: float):
            try:
                eased = 1.0 - (1.0 - a) * (1.0 - a)
                self.root.attributes("-alpha", min(eased, 1.0))
            except Exception:
                return
            if a < 1.0 and not self._closing:
                self.root.after(16, lambda: step(min(a + inc, 1.0)))

        step(inc)

    def _fade_out_and_finish(self, duration_ms: int = 140):
        self._closing = True
        steps = max(6, duration_ms // 16)
        dec = 1.0 / steps

        def step(a: float):
            try:
                eased = a * a
                self.root.attributes("-alpha", max(eased, 0.0))
            except Exception:
                self._finish()
                return
            if a > 0.0:
                self.root.after(16, lambda: step(max(a - dec, 0.0)))
            else:
                self._finish()

        step(1.0)

    def _tick(self):
        """60fps animation loop: smooth progress interpolation + shimmer."""
        if self._closing:
            return

        # Ease the visible progress toward the target
        gap = self._target_pct - self._current_pct
        if abs(gap) > 0.0005:
            self._current_pct += gap * 0.18  # critically-damped feel
        else:
            self._current_pct = self._target_pct

        bar_left, bar_top, bar_right, bar_bot = self._bar_bounds
        x2 = bar_left + int(self._bar_w * self._current_pct)
        self.canvas.coords(self.progress_bar, bar_left, bar_top, x2, bar_bot)

        # Shimmer: a small glow cap at the leading edge, pulsing
        self._shimmer_phase += 0.08
        glow_w = 80
        # glow rides along the bar head but also oscillates when idle
        head = x2
        osc = int(30 * (0.5 + 0.5 * math.sin(self._shimmer_phase)))
        sh_right = min(bar_right, head + osc - 10)
        sh_left = max(bar_left, sh_right - glow_w)
        if self._current_pct > 0.01:
            self.canvas.coords(self.shimmer, sh_left, bar_top, sh_right, bar_bot)
            # pulse alpha via color mixing
            pulse = 0.5 + 0.5 * math.sin(self._shimmer_phase * 1.2)
            col = _mix(SPLASH_FG, SPLASH_GLOW, pulse)
            self.canvas.itemconfigure(self.shimmer, fill=col)
        else:
            self.canvas.coords(self.shimmer, bar_left, bar_top, bar_left, bar_bot)

        # Cross-fade status text if pending change
        if self._pending_status is not None:
            self._status_alpha -= 0.12
            if self._status_alpha <= 0.0:
                self._status_text = self._pending_status
                self._pending_status = None
                self.canvas.itemconfigure(self._status_text_id, text=self._status_text)
                self._status_alpha = 0.0
        elif self._status_alpha < 1.0:
            self._status_alpha = min(1.0, self._status_alpha + 0.12)

        # Apply status fade via color mix (bg ↔ text color)
        col = _mix(SPLASH_BG, SPLASH_TEXT, max(0.0, self._status_alpha))
        self.canvas.itemconfigure(self._status_text_id, fill=col)

        self.root.after(16, self._tick)

    def _set_status(self, text: str):
        """Queue a cross-fade text change."""
        if text == self._status_text:
            return
        self._pending_status = text

    def _set_target(self, pct: float):
        self._target_pct = max(0.0, min(1.0, pct))

    def _start_sequence(self):
        def run():
            _download_asset(BANNER_URL, BANNER_PATH)
            _download_asset(LOGO_URL, LOGO_PATH)

            steps = len(INTRO_LINES)
            for i, line in enumerate(INTRO_LINES):
                self.root.after(0, self._set_status, line)
                self.root.after(0, self._set_target, (i + 1) / steps)
                time.sleep(0.22)

            time.sleep(0.15)
            self.root.after(0, self._fade_out_and_finish)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.root.mainloop()

    def _finish(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        self.on_done()


def run_splash(on_done_callback):
    """Pre-download banner then show splash, call on_done when done."""
    _download_asset(BANNER_URL, BANNER_PATH)
    _download_asset(LOGO_URL, LOGO_PATH)
    SplashScreen(on_done_callback)
