"""
ZeddiHub Tools Desktop - Main GUI entry point.
v1.0.0

Usage:
    python app.py
    pyinstaller --onefile --windowed --icon=assets/icon.ico --name "ZeddiHub.Tools" app.py
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
    """Generate a simple icon from logo.png or fallback drawn icon."""
    from pathlib import Path
    icon_path = Path(_root) / "assets" / "icon.ico"
    if icon_path.exists():
        return

    # Try to convert logo_icon.png or logo.png to .ico
    for png_name in ["logo_icon.png", "logo_transparent.png", "logo.png"]:
        png_path = Path(_root) / "assets" / png_name
        if png_path.exists():
            try:
                from PIL import Image
                img = Image.open(png_path)
                img = img.convert("RGBA")
                img.save(str(icon_path), format="ICO",
                         sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
                return
            except Exception:
                pass

    # Fallback: draw simple icon
    try:
        from PIL import Image, ImageDraw
        Path(_root, "assets").mkdir(exist_ok=True)
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill="#f0a500")
        draw.text((18, 18), "ZH", fill="white")
        img.save(str(icon_path), format="ICO")
    except Exception:
        pass


def _show_language_dialog():
    """Show first-launch language selection dialog. Returns chosen lang."""
    import tkinter as tk

    chosen = ["cs"]  # Default

    root = tk.Toplevel()
    root.title("Vyberte jazyk / Choose Language")
    root.geometry("400x220")
    root.configure(bg="#0c0c0c")
    root.resizable(False, False)
    root.grab_set()
    root.overrideredirect(False)

    # Center
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w, h = 400, 220
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # Title
    tk.Label(root, text="Vyberte jazyk / Choose Language",
             bg="#0c0c0c", fg="#f0a500",
             font=("Segoe UI", 14, "bold")).pack(pady=(24, 16))

    btn_frame = tk.Frame(root, bg="#0c0c0c")
    btn_frame.pack()

    def pick(lang):
        chosen[0] = lang
        root.destroy()

    # Czech button
    cs_btn = tk.Button(
        btn_frame, text="🇨🇿  Česky",
        bg="#222222", fg="#f0f0f0",
        activebackground="#f0a500", activeforeground="#ffffff",
        font=("Segoe UI", 13, "bold"),
        width=12, height=2,
        bd=0, relief="flat",
        cursor="hand2",
        command=lambda: pick("cs")
    )
    cs_btn.pack(side="left", padx=12)

    # English button
    en_btn = tk.Button(
        btn_frame, text="🇬🇧  English",
        bg="#222222", fg="#f0f0f0",
        activebackground="#5b9cf6", activeforeground="#ffffff",
        font=("Segoe UI", 13, "bold"),
        width=12, height=2,
        bd=0, relief="flat",
        cursor="hand2",
        command=lambda: pick("en")
    )
    en_btn.pack(side="left", padx=12)

    tk.Label(root, text="Jazyk lze kdykoliv změnit v Nastavení  /  Language can be changed in Settings",
             bg="#0c0c0c", fg="#555555",
             font=("Segoe UI", 8)).pack(pady=(16, 0))

    root.wait_window(root)
    return chosen[0]


def main():
    _generate_icon()

    # Initialize locale module to check if first launch
    from gui.locale import init as locale_init, is_first_launch, set_lang

    is_first = is_first_launch()

    def _launch():
        from gui.main_window import MainWindow
        app = MainWindow()
        app.mainloop()

    def _after_splash():
        if is_first:
            # Show language selection before main window
            # We need a temporary root for the dialog
            tmp_root = ctk.CTk()
            tmp_root.withdraw()  # hide it
            lang = _show_language_dialog()
            set_lang(lang)
            tmp_root.destroy()
        _launch()

    # Show splash screen first, then launch main window
    try:
        from gui.splash import run_splash
        run_splash(on_done_callback=_after_splash)
    except Exception:
        # If splash fails, do first-launch check and launch directly
        if is_first:
            import tkinter as tk
            _tmp = tk.Tk()
            _tmp.withdraw()
            lang = _show_language_dialog()
            set_lang(lang)
            _tmp.destroy()
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
