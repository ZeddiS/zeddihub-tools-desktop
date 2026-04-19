"""
ZeddiHub Tools - Splash / loading screen shown on startup.
Downloads banner from CDN and shows animated intro text.
"""

import tkinter as tk
import threading
import time
import os
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
SPLASH_BG_INNER = "#0a0a0f"
SPLASH_FG       = "#3b82f6"
SPLASH_FG_ALT   = "#8b5cf6"
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
    """Download asset to local cache. Returns True on success."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return True
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception:
        return False


class SplashScreen:
    def __init__(self, on_done_callback):
        self.on_done = on_done_callback
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=SPLASH_BG)
        self.root.attributes("-topmost", True)

        w, h = 700, 380
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui(w, h)
        self._start_sequence()

    def _build_ui(self, w, h):
        self.canvas = tk.Canvas(
            self.root, width=w, height=h,
            bg=SPLASH_BG, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Flat Claude-app splash: no inner card, just the bg
        self.canvas.create_rectangle(0, 0, w, h, fill=SPLASH_BG, outline="")

        self.banner_img_ref = None
        if PIL_OK and BANNER_PATH.exists():
            self._show_banner(w, h)
        else:
            self._show_text_logo(w)

        # Title
        self.canvas.create_text(
            w // 2, h - 114,
            text="ZeddiHub Tools",
            fill=SPLASH_TEXT, font=("Segoe UI", 18, "bold")
        )
        # Small muted version/tagline
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

        # Status text (centered above progress bar)
        self.status_var = tk.StringVar(value="Spouštění...")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var,
            bg=SPLASH_BG, fg=SPLASH_DIM, font=("Segoe UI", 10)
        )
        self.status_label.place(relx=0.5, y=h - 58, anchor="center")

        # Progress bar — very thin Claude-app style track
        bar_left, bar_right = 80, w - 80
        bar_top, bar_bot = h - 38, h - 34
        self.canvas.create_rectangle(bar_left, bar_top, bar_right, bar_bot,
                                     fill=SPLASH_TRACK, outline="")
        self.progress_bar = self.canvas.create_rectangle(
            bar_left, bar_top, bar_left, bar_bot, fill=SPLASH_FG, outline=""
        )
        self._progress_bounds = (bar_left, bar_top, bar_right, bar_bot)
        self._progress_w = bar_right - bar_left

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

    def _set_progress(self, pct: float):
        bar_left, bar_top, _, bar_bot = self._progress_bounds
        x2 = bar_left + int(self._progress_w * pct)
        self.canvas.coords(self.progress_bar, bar_left, bar_top, x2, bar_bot)

    def _start_sequence(self):
        """Download assets then animate loading, then call on_done."""
        def run():
            # Download assets in background
            _download_asset(BANNER_URL, BANNER_PATH)
            _download_asset(LOGO_URL, LOGO_PATH)

            steps = len(INTRO_LINES)
            for i, line in enumerate(INTRO_LINES):
                self.root.after(0, self.status_var.set, line)
                self.root.after(0, self._set_progress, (i + 1) / steps)
                time.sleep(0.35)

            time.sleep(0.4)
            self.root.after(0, self._finish)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.root.mainloop()

    def _finish(self):
        self.root.destroy()
        self.on_done()


def run_splash(on_done_callback):
    """Download banner then show splash, call on_done when done."""
    # Pre-download sync so splash has image ready
    _download_asset(BANNER_URL, BANNER_PATH)
    _download_asset(LOGO_URL, LOGO_PATH)
    SplashScreen(on_done_callback)
