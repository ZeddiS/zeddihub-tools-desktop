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
ICON_PATH   = ASSETS_DIR / "icon.ico"

SPLASH_BG   = "#0d0d1a"
SPLASH_FG   = "#e07b39"
SPLASH_TEXT = "#cccccc"

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

        # Border glow effect
        self.canvas.create_rectangle(1, 1, w-1, h-1, outline="#e07b39", width=2)
        self.canvas.create_rectangle(4, 4, w-4, h-4, outline="#3a2010", width=1)

        self.banner_img_ref = None
        if PIL_OK and BANNER_PATH.exists():
            self._show_banner(w, h)
        else:
            self._show_text_logo(w)

        # Version label
        self.canvas.create_text(
            w // 2, h - 90,
            text="ZeddiHub Tools Desktop",
            fill=SPLASH_FG, font=("Segoe UI", 14, "bold")
        )
        self.canvas.create_text(
            w // 2, h - 68,
            text="by ZeddiS  |  zeddihub.eu",
            fill="#666666", font=("Segoe UI", 9)
        )

        # Status text
        self.status_var = tk.StringVar(value="Spouštění...")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var,
            bg=SPLASH_BG, fg=SPLASH_TEXT, font=("Segoe UI", 9)
        )
        self.status_label.place(x=20, y=h - 40)

        # Progress bar background
        self.canvas.create_rectangle(20, h-22, w-20, h-10, fill="#1a1a2e", outline="#333333")
        self.progress_bar = self.canvas.create_rectangle(
            20, h-22, 20, h-10, fill=SPLASH_FG, outline=""
        )
        self._progress_w = w - 40

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
            w // 2, 100,
            text="ZeddiHub Tools",
            fill=SPLASH_FG, font=("Segoe UI", 32, "bold")
        )

    def _set_progress(self, pct: float):
        x1 = 20
        x2 = x1 + int(self._progress_w * pct)
        self.canvas.coords(self.progress_bar, x1, self.root.winfo_height()-22,
                           x2, self.root.winfo_height()-10)

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
