"""
ZeddiHub Tools Desktop - Main GUI entry point.
v1.0.0

Usage:
    python app.py
    pyinstaller --onefile --windowed --icon=assets/icon.ico --name "ZeddiHub Tools" app.py
"""

import sys
import os

# Add project root to path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def _generate_icon():
    """Generate a simple icon if none exists."""
    from pathlib import Path
    icon_path = Path(_root) / "assets" / "icon.ico"
    if icon_path.exists():
        return

    try:
        from PIL import Image, ImageDraw
        Path(_root, "assets").mkdir(exist_ok=True)
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill="#e07b39")
        draw.text((18, 18), "ZH", fill="white")
        img.save(icon_path, format="ICO")
    except Exception:
        pass


def main():
    _generate_icon()

    def _launch():
        from gui.main_window import MainWindow
        app = MainWindow()
        app.mainloop()

    # Show splash screen first, then launch main window
    try:
        from gui.splash import run_splash
        run_splash(on_done_callback=_launch)
    except Exception:
        # If splash fails, launch directly
        _launch()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        input("Stiskněte Enter pro zavření...")
