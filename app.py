"""
ZeddiHub Tools Desktop - Main GUI entry point.
v1.2.0

Usage:
    python app.py
    pyinstaller --onefile --windowed --icon=assets/icon.ico --name "ZeddiHub.Tools" app.py
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog

_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

_BG = "#0c0c0c"
_ORANGE = "#f0a500"
_BLUE = "#5b9cf6"
_DIM = "#555555"
_BTN_BG = "#1e1e1e"


def _generate_icon():
    from pathlib import Path
    icon_path = Path(_root) / "assets" / "icon.ico"
    if icon_path.exists():
        return
    for png_name in ["logo_icon.png", "logo_transparent.png", "logo.png"]:
        png_path = Path(_root) / "assets" / png_name
        if png_path.exists():
            try:
                from PIL import Image
                img = Image.open(png_path).convert("RGBA")
                img.save(str(icon_path), format="ICO",
                         sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
                return
            except Exception:
                pass


def _show_first_launch_wizard() -> tuple:
    """
    Two-step wizard shown on first launch.
    Step 1: Language selection
    Step 2: Data folder location
    Returns (lang: str, data_dir: Path)
    """
    from pathlib import Path
    from gui.config import get_default_data_dir

    chosen_lang = ["cs"]
    chosen_dir = [get_default_data_dir()]
    step = [1]

    # ── Build window ──────────────────────────────────────────────────────────
    win = tk.Tk()
    win.withdraw()
    win.title("ZeddiHub Tools – Nastavení / Setup")
    w, h = 480, 320
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    win.configure(bg=_BG)
    win.resizable(False, False)

    # Main container (swap frames to switch steps)
    container = tk.Frame(win, bg=_BG)
    container.pack(fill="both", expand=True, padx=30, pady=24)

    # ── Step 1: Language ──────────────────────────────────────────────────────
    frame1 = tk.Frame(container, bg=_BG)

    tk.Label(frame1, text="Vyberte jazyk / Choose Language",
             bg=_BG, fg=_ORANGE, font=("Segoe UI", 15, "bold")).pack(pady=(0, 6))
    tk.Label(frame1, text="Jazyk lze kdykoliv změnit v Nastavení  ·  Language can be changed in Settings",
             bg=_BG, fg=_DIM, font=("Segoe UI", 9)).pack(pady=(0, 20))

    btn_row1 = tk.Frame(frame1, bg=_BG)
    btn_row1.pack()

    def _pick_lang(lang):
        chosen_lang[0] = lang
        # Highlight selected
        cs_btn.configure(bg=_ORANGE if lang == "cs" else _BTN_BG,
                         fg="#0c0c0c" if lang == "cs" else "#f0f0f0")
        en_btn.configure(bg=_BLUE if lang == "en" else _BTN_BG,
                         fg="#0c0c0c" if lang == "en" else "#f0f0f0")

    cs_btn = tk.Button(btn_row1, text="🇨🇿  Česky",
                       bg=_ORANGE, fg="#0c0c0c",
                       activebackground=_ORANGE, activeforeground="#0c0c0c",
                       font=("Segoe UI", 13, "bold"), width=12, height=2,
                       bd=0, relief="flat", cursor="hand2",
                       command=lambda: _pick_lang("cs"))
    cs_btn.pack(side="left", padx=12)

    en_btn = tk.Button(btn_row1, text="🇬🇧  English",
                       bg=_BTN_BG, fg="#f0f0f0",
                       activebackground=_BLUE, activeforeground="#0c0c0c",
                       font=("Segoe UI", 13, "bold"), width=12, height=2,
                       bd=0, relief="flat", cursor="hand2",
                       command=lambda: _pick_lang("en"))
    en_btn.pack(side="left", padx=12)

    def _next_step():
        frame1.pack_forget()
        frame2.pack(fill="both", expand=True)
        step[0] = 2
        win.deiconify()

    tk.Button(frame1, text="Pokračovat →",
              bg=_ORANGE, fg="#0c0c0c",
              activebackground="#d4900a", activeforeground="#0c0c0c",
              font=("Segoe UI", 12, "bold"), width=18, height=2,
              bd=0, relief="flat", cursor="hand2",
              command=_next_step).pack(pady=(28, 0))

    # ── Step 2: Data folder ────────────────────────────────────────────────────
    frame2 = tk.Frame(container, bg=_BG)

    tk.Label(frame2,
             text="Složka pro data aplikace\nApp data folder",
             bg=_BG, fg=_ORANGE, font=("Segoe UI", 15, "bold"),
             justify="center").pack(pady=(0, 6))
    tk.Label(frame2,
             text="Nastavení, přihlašovací údaje a cache se ukládají do této složky.\n"
                  "Settings, credentials and cache are saved here.",
             bg=_BG, fg=_DIM, font=("Segoe UI", 9), justify="center").pack(pady=(0, 14))

    path_var = tk.StringVar(value=str(chosen_dir[0]))

    path_frame = tk.Frame(frame2, bg="#1a1a1a", padx=8, pady=6)
    path_frame.pack(fill="x", pady=(0, 8))

    path_label = tk.Label(path_frame, textvariable=path_var,
                          bg="#1a1a1a", fg="#cccccc",
                          font=("Segoe UI", 9), wraplength=360, justify="left")
    path_label.pack(fill="x")

    def _browse():
        base = filedialog.askdirectory(
            title="Vyberte složku pro ZeddiHub.Tools.Data",
            initialdir=str(chosen_dir[0].parent),
            parent=win
        )
        if base:
            from pathlib import Path as P
            new_dir = P(base) / "ZeddiHub.Tools.Data"
            chosen_dir[0] = new_dir
            path_var.set(str(new_dir))

    btn_row2 = tk.Frame(frame2, bg=_BG)
    btn_row2.pack(pady=(0, 20))

    tk.Button(btn_row2, text="📂 Změnit / Change",
              bg=_BTN_BG, fg="#cccccc",
              activebackground="#333333", activeforeground="#ffffff",
              font=("Segoe UI", 11), width=18, height=2,
              bd=0, relief="flat", cursor="hand2",
              command=_browse).pack()

    def _finish():
        win.destroy()

    tk.Button(frame2, text="✓ Dokončit / Finish",
              bg=_ORANGE, fg="#0c0c0c",
              activebackground="#d4900a", activeforeground="#0c0c0c",
              font=("Segoe UI", 12, "bold"), width=18, height=2,
              bd=0, relief="flat", cursor="hand2",
              command=_finish).pack()

    # Start with frame1
    frame1.pack(fill="both", expand=True)
    win.deiconify()
    win.wait_window(win)

    return chosen_lang[0], chosen_dir[0]


def main():
    _generate_icon()

    from gui.locale import init as locale_init, set_lang, is_first_launch

    is_first = is_first_launch()

    def _launch():
        from gui.main_window import MainWindow
        app = MainWindow()
        app.mainloop()

    def _after_splash():
        if is_first:
            # First-launch wizard: language + data folder
            tmp = ctk.CTk()
            tmp.withdraw()

            lang, data_dir = _show_first_launch_wizard()

            # Save data dir first (locale will use it for settings)
            from gui.config import set_data_dir, save_bootstrap, get_bootstrap
            set_data_dir(data_dir)

            # Now save language
            set_lang(lang)

            tmp.destroy()

        _launch()

    try:
        from gui.splash import run_splash
        run_splash(on_done_callback=_after_splash)
    except Exception:
        if is_first:
            lang, data_dir = _show_first_launch_wizard()
            from gui.config import set_data_dir
            set_data_dir(data_dir)
            from gui.locale import set_lang
            set_lang(lang)
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
