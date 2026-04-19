"""
ZeddiHub Tools - Settings panel.
Language, account management, about info.
"""

import webbrowser
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from typing import Callable, Optional

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from ..locale import t, get_lang, set_lang, load_settings, save_settings
    from ..auth import is_authenticated, get_current_user, logout, clear_credentials
    from ..updater import check_for_update, CURRENT_VERSION
    from ..config import get_data_dir, set_data_dir
    from .. import icons
except ImportError:
    def t(key, **kw): return key
    def get_lang(): return "cs"
    def set_lang(lang): pass
    def load_settings(): return {}
    def save_settings(s): pass
    def is_authenticated(): return False
    def get_current_user(): return None
    def logout(): pass
    def clear_credentials(): pass
    def check_for_update(callback=None): pass
    def get_data_dir(): from pathlib import Path; return Path.home()
    def set_data_dir(p): pass
    CURRENT_VERSION = "1.0.0"
    class icons:  # noqa: E306
        @staticmethod
        def icon(name, size=16, color=None): return None

try:
    from ..widgets import make_page_title, make_card, make_divider
except ImportError:
    def make_page_title(parent, text, theme, subtitle=None, **kw):
        import customtkinter as _ctk
        f = _ctk.CTkFrame(parent, fg_color="transparent")
        _ctk.CTkLabel(f, text=text,
                      font=_ctk.CTkFont("Segoe UI", 22, "bold"),
                      text_color=theme.get("text", "#f0f0f0")).pack(anchor="w")
        if subtitle:
            _ctk.CTkLabel(f, text=subtitle,
                          font=_ctk.CTkFont("Segoe UI", 12),
                          text_color=theme.get("text_dim", "#888")).pack(anchor="w")
        return f
    def make_card(parent, theme, padding=20, **kw):
        import customtkinter as _ctk
        return _ctk.CTkFrame(parent, fg_color=theme.get("card_bg", "#1a1a26"),
                             corner_radius=14, border_width=0)
    def make_divider(parent, theme, **kw):
        import customtkinter as _ctk
        return _ctk.CTkFrame(parent, fg_color=theme.get("border", "#2a2a35"),
                             height=1, corner_radius=0)

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#f0f0f0", **kw)


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, on_language_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._on_language_change = on_language_change
        self._build()

    def _build(self):
        th = self.theme

        # Page title lives OUTSIDE the tabview (Claude-app style header)
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        make_page_title(
            outer, t("settings_title"), th,
            subtitle=t("choose_language") if t("choose_language") != "choose_language" else None,
        ).pack(fill="x", padx=32, pady=(28, 16), anchor="w")

        tab = ctk.CTkTabview(
            outer,
            fg_color=th["content_bg"],
            segmented_button_fg_color=th.get("input_bg", th["secondary"]),
            segmented_button_selected_color=th["primary"],
            segmented_button_selected_hover_color=th.get("primary_hover", th["primary"]),
            segmented_button_unselected_color=th.get("input_bg", th["secondary"]),
            segmented_button_unselected_hover_color=th.get("card_hover", th["secondary"]),
            text_color=th["text"],
        )
        tab.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        tab.add(t("general"))
        tab.add(t("account"))
        tab.add(t("about"))

        self._build_general(tab.tab(t("general")))
        self._build_account(tab.tab(t("account")))
        self._build_about(tab.tab(t("about")))

    # ─── GENERAL ──────────────────────────────────────────────────────────────

    def _build_general(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Language section
        lang_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        lang_card.pack(fill="x", pady=6)

        _label(lang_card, " " + t("settings_language"), 13, bold=True, color=th["primary"],
               image=icons.icon("language", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(lang_card, t("choose_language"),
               10, color=th["text_dim"]).pack(padx=14, pady=(0, 10), anchor="w")

        lang_row = ctk.CTkFrame(lang_card, fg_color="transparent")
        lang_row.pack(padx=14, pady=(0, 14), anchor="w")

        current_lang = get_lang()

        self._cs_btn = ctk.CTkButton(
            lang_row, text="Česky",
            fg_color=th["primary"] if current_lang == "cs" else th["secondary"],
            hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 13, "bold" if current_lang == "cs" else "normal"),
            height=44, width=140,
            command=lambda: self._select_language("cs")
        )
        self._cs_btn.pack(side="left", padx=(0, 10))

        self._en_btn = ctk.CTkButton(
            lang_row, text="English",
            fg_color=th["primary"] if current_lang == "en" else th["secondary"],
            hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 13, "bold" if current_lang == "en" else "normal"),
            height=44, width=140,
            command=lambda: self._select_language("en")
        )
        self._en_btn.pack(side="left")

        self._lang_notice = _label(lang_card, "", 10, color=th["warning"])
        self._lang_notice.pack(padx=14, pady=(0, 8), anchor="w")

        # Appearance mode section
        mode_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        mode_card.pack(fill="x", pady=6)

        _label(mode_card, " Vzhled / Barevný režim", 13, bold=True, color=th["primary"],
               image=icons.icon("moon", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(mode_card, "Volba se použije okamžitě. Tlačítko slunce/měsíc je také v záhlaví.",
               10, color=th["text_dim"]).pack(padx=14, pady=(0, 8), anchor="w")

        import customtkinter as ctk_ref
        current_mode = ctk_ref.get_appearance_mode().lower()
        saved_settings = load_settings()
        saved_mode = saved_settings.get("appearance_mode", "dark")

        mode_row = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_row.pack(padx=14, pady=(0, 14), anchor="w")

        for mode_id, mode_label in [("dark", "Tmavý"), ("light", "Světlý"), ("system", "Systém")]:
            is_active = (saved_mode == mode_id)
            ctk.CTkButton(
                mode_row, text=mode_label, width=110, height=36,
                fg_color=th["primary"] if is_active else th["secondary"],
                hover_color=th["primary_hover"],
                font=ctk.CTkFont("Segoe UI", 12, "bold" if is_active else "normal"),
                command=lambda m=mode_id: self._set_appearance(m)
            ).pack(side="left", padx=(0, 8))

        # Update section
        update_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        update_card.pack(fill="x", pady=6)

        _label(update_card, " Aktualizace", 13, bold=True, color=th["primary"],
               image=icons.icon("sync-alt", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")

        self._update_status = _label(update_card, f"Aktuální verze: v{CURRENT_VERSION}",
                                      10, color=th["text_dim"])
        self._update_status.pack(padx=14, pady=(0, 8), anchor="w")

        ctk.CTkButton(update_card, text=" " + t("check_updates"),
                      image=icons.icon("search", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._check_updates
                      ).pack(padx=14, pady=(0, 14), anchor="w")

        # Autostart section (N-15: run at Windows startup)
        autostart_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        autostart_card.pack(fill="x", pady=6)

        _label(autostart_card, " " + t("autostart_section"), 13, bold=True, color=th["primary"],
               image=icons.icon("power-off", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(autostart_card, t("autostart_hint"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 8), anchor="w")

        self._autostart_var = ctk.BooleanVar(value=self._is_autostart_enabled())
        self._autostart_switch = ctk.CTkSwitch(
            autostart_card, text=t("autostart_enable"),
            variable=self._autostart_var,
            command=self._toggle_autostart,
            fg_color=th["secondary"], progress_color=th["primary"],
            font=ctk.CTkFont("Segoe UI", 11),
        )
        self._autostart_switch.pack(padx=14, pady=(0, 6), anchor="w")

        self._start_minimized_var = ctk.BooleanVar(
            value=bool(load_settings().get("start_minimized", False))
        )
        self._start_minimized_switch = ctk.CTkSwitch(
            autostart_card, text=t("autostart_minimized"),
            variable=self._start_minimized_var,
            command=self._toggle_start_minimized,
            fg_color=th["secondary"], progress_color=th["primary"],
            font=ctk.CTkFont("Segoe UI", 11),
        )
        self._start_minimized_switch.pack(padx=14, pady=(0, 6), anchor="w")

        self._autostart_status = _label(autostart_card, "", 10, color=th["text_dim"])
        self._autostart_status.pack(padx=14, pady=(0, 14), anchor="w")

        # Close behavior section (F-07: minimize to tray vs. quit)
        close_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        close_card.pack(fill="x", pady=6)

        _label(close_card, " " + t("close_behavior_section"), 13, bold=True, color=th["primary"],
               image=icons.icon("window-close", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(close_card, t("close_behavior_hint"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 8), anchor="w")

        current_close = load_settings().get("close_behavior", "minimize")
        self._close_var = ctk.StringVar(value=current_close)

        close_row = ctk.CTkFrame(close_card, fg_color="transparent")
        close_row.pack(padx=14, pady=(0, 14), anchor="w")

        ctk.CTkRadioButton(
            close_row, text=t("close_behavior_minimize"),
            variable=self._close_var, value="minimize",
            command=self._save_close_behavior,
            fg_color=th["primary"], hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(0, 16))

        ctk.CTkRadioButton(
            close_row, text=t("close_behavior_quit"),
            variable=self._close_var, value="quit",
            command=self._save_close_behavior,
            fg_color=th["primary"], hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left")

        # Data folder section
        data_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        data_card.pack(fill="x", pady=6)

        _label(data_card, " Složka s daty / Data folder", 13, bold=True, color=th["primary"],
               image=icons.icon("folder", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(data_card, "Nastavení, přihlašovací údaje a cache aplikace.",
               10, color=th["text_dim"]).pack(padx=14, pady=(0, 6), anchor="w")

        self._data_dir_label = _label(data_card, str(get_data_dir()), 9, color=th["text_dim"])
        self._data_dir_label.pack(padx=14, pady=(0, 8), anchor="w")

        ctk.CTkButton(data_card, text=" Změnit složku",
                      image=icons.icon("folder-open", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._change_data_dir
                      ).pack(padx=14, pady=(0, 14), anchor="w")

        # Factory reset / backup section
        reset_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        reset_card.pack(fill="x", pady=6)

        _label(reset_card, " Záloha a reset", 13, bold=True, color=th["primary"],
               image=icons.icon("lock", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(reset_card, "Záloha uloží nastavení do ZeddiHub.Tools.Data/backup_YYYYMMDD.json.",
               10, color=th["text_dim"]).pack(padx=14, pady=(0, 8), anchor="w")

        self._backup_status = _label(reset_card, "", 10, color=th["text_dim"])
        self._backup_status.pack(padx=14, pady=(0, 6), anchor="w")

        backup_row = ctk.CTkFrame(reset_card, fg_color="transparent")
        backup_row.pack(padx=14, pady=(0, 6), anchor="w")

        ctk.CTkButton(backup_row, text=" Zálohovat nastavení",
                      image=icons.icon("save", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._backup_settings
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(backup_row, text=" Obnovit ze zálohy",
                      image=icons.icon("folder-open", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._restore_settings
                      ).pack(side="left")

        ctk.CTkButton(reset_card, text=" Tovární reset (smazat vše)",
                      image=icons.icon("exclamation-triangle", 13, "#ffffff"), compound="left",
                      fg_color="#8b2020", hover_color="#6b1818",
                      text_color="#ffffff",
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._factory_reset
                      ).pack(padx=14, pady=(6, 14), anchor="w")

        # ─── Shortcuts section (N-03) ─────────────────────────────────────────
        sc_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        sc_card.pack(fill="x", pady=6)

        _label(sc_card, " " + t("shortcuts_section"), 13, bold=True, color=th["primary"],
               image=icons.icon("keyboard", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(sc_card, t("shortcuts_hint"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 8), anchor="w")

        sc_enabled = load_settings().get("shortcuts_enabled", True)
        self._sc_var = ctk.BooleanVar(value=sc_enabled)
        ctk.CTkSwitch(
            sc_card, text=t("shortcuts_enable"),
            variable=self._sc_var,
            command=self._toggle_shortcuts,
            fg_color=th["secondary"], progress_color=th["primary"],
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(padx=14, pady=(0, 8), anchor="w")

        # Shortcut reference table
        sc_table = ctk.CTkFrame(sc_card, fg_color=th["secondary"], corner_radius=6)
        sc_table.pack(fill="x", padx=14, pady=(0, 14))

        shortcuts_ref = [
            ("Ctrl+1", t("shortcuts_home")),
            ("Ctrl+2", t("shortcuts_pc_tools")),
            ("Ctrl+3", t("shortcuts_settings")),
            ("Ctrl+4", t("shortcuts_links")),
            ("F5",     t("shortcuts_refresh")),
            ("Ctrl+Q", t("shortcuts_quit")),
            ("Ctrl+M", t("shortcuts_tray")),
            ("F11",    t("shortcuts_fullscreen")),
            ("F1",     t("shortcuts_help")),
        ]
        for key, desc in shortcuts_ref:
            row = ctk.CTkFrame(sc_table, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)
            key_lbl = ctk.CTkLabel(
                row, text=key, width=80,
                font=ctk.CTkFont("Consolas", 11, "bold"),
                text_color=th["primary"], anchor="w",
            )
            key_lbl.pack(side="left")
            _label(row, desc, 11, color=th["text"]).pack(side="left", padx=(10, 0))

        # ─── Report a bug section (N-09) ──────────────────────────────────────
        bug_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        bug_card.pack(fill="x", pady=6)

        _label(bug_card, " " + t("report_bug_section"), 13, bold=True, color=th["primary"],
               image=icons.icon("bug", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(bug_card, t("report_bug_hint"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 8), anchor="w")

        ctk.CTkButton(bug_card, text=" " + t("report_bug_btn"),
                      image=icons.icon("github", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._open_bug_report,
                      ).pack(padx=14, pady=(0, 14), anchor="w")

    def _toggle_shortcuts(self):
        """N-03: Enable/disable global shortcut bindings."""
        try:
            settings = load_settings()
            settings["shortcuts_enabled"] = bool(self._sc_var.get())
            save_settings(settings)
            # Notify main window to rebind
            parent = self.winfo_toplevel()
            if hasattr(parent, "_apply_shortcut_bindings"):
                parent._apply_shortcut_bindings()
        except Exception:
            pass

    def _open_bug_report(self):
        """N-09: open pre-filled GitHub Issues template."""
        import platform as _pf
        import urllib.parse as _up
        try:
            parent = self.winfo_toplevel()
            active_panel = getattr(parent, "_current_nav_id", "unknown")
        except Exception:
            active_panel = "unknown"

        title = f"[Bug] v{CURRENT_VERSION} — "
        body = (
            "**Popis problému / Describe the bug**\n"
            "<!-- Stručný popis co se stalo -->\n\n"
            "**Kroky k reprodukci / Steps to reproduce**\n"
            "1. …\n2. …\n3. …\n\n"
            "**Očekávané chování / Expected behavior**\n\n\n"
            "**Systémové info / System info**\n"
            f"- App: ZeddiHub Tools v{CURRENT_VERSION}\n"
            f"- OS: {_pf.system()} {_pf.release()} ({_pf.machine()})\n"
            f"- Python: {_pf.python_version()}\n"
            f"- Aktivní panel / Active panel: `{active_panel}`\n\n"
            "**Screenshoty / logs (volitelné)**\n"
        )
        url = (
            "https://github.com/ZeddiS/zeddihub-tools-desktop/issues/new"
            f"?title={_up.quote(title)}&body={_up.quote(body)}&labels=bug"
        )
        webbrowser.open(url)

    def _backup_settings(self):
        import datetime, json as _json
        from tkinter import messagebox as _mb
        try:
            data_dir = get_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            settings = load_settings()
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = data_dir / f"backup_{date_str}.json"
            backup_path.write_text(
                _json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
            self._backup_status.configure(
                text=f"✅ Záloha uložena: {backup_path.name}", text_color=self.theme["success"])
        except Exception as e:
            self._backup_status.configure(
                text=f"✗ Chyba: {e}", text_color=self.theme["error"])

    def _restore_settings(self):
        import json as _json
        from tkinter import filedialog, messagebox as _mb
        data_dir = get_data_dir()
        path = filedialog.askopenfilename(
            title="Vyberte zálohu",
            initialdir=str(data_dir),
            filetypes=[("JSON", "*.json"), ("All", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                restored = _json.load(f)
            save_settings(restored)
            self._backup_status.configure(
                text=f"✅ Nastavení obnoveno. Restartujte aplikaci.",
                text_color=self.theme["success"])
        except Exception as e:
            self._backup_status.configure(
                text=f"✗ Chyba: {e}", text_color=self.theme["error"])

    def _factory_reset(self):
        from tkinter import messagebox as _mb
        if not _mb.askyesno("Tovární reset",
                             "Opravdu smazat VŠECHNA nastavení?\nZáloha nebude vytvořena. Tato akce nelze vrátit."):
            return
        try:
            save_settings({})
            self._backup_status.configure(
                text="✅ Reset dokončen. Restartujte aplikaci.",
                text_color=self.theme["success"])
        except Exception as e:
            self._backup_status.configure(
                text=f"✗ Chyba: {e}", text_color=self.theme["error"])

    def _set_appearance(self, mode: str):
        import customtkinter as ctk_ref
        if mode == "system":
            ctk_ref.set_appearance_mode("system")
        else:
            ctk_ref.set_appearance_mode(mode)
        settings = load_settings()
        settings["appearance_mode"] = mode
        save_settings(settings)
        # Update toggle button in main window if accessible
        parent = self.winfo_toplevel()
        if hasattr(parent, "_update_mode_btn"):
            parent._update_mode_btn()

    def _select_language(self, lang: str):
        th = self.theme
        set_lang(lang)

        # Update button styles
        self._cs_btn.configure(
            fg_color=th["primary"] if lang == "cs" else th["secondary"],
            font=ctk.CTkFont("Segoe UI", 13, "bold" if lang == "cs" else "normal")
        )
        self._en_btn.configure(
            fg_color=th["primary"] if lang == "en" else th["secondary"],
            font=ctk.CTkFont("Segoe UI", 13, "bold" if lang == "en" else "normal")
        )

        self._lang_notice.configure(text=t("language_changed"))

        if self._on_language_change:
            self._on_language_change(lang)

    def _check_updates(self):
        self._update_status.configure(text="Kontroluji aktualizace...", text_color=self.theme["text_dim"])

        def on_result(result):
            if result is None:
                self._update_status.configure(
                    text=t("update_check_failed"), text_color=self.theme["warning"])
            elif result.get("available"):
                latest = result.get("latest", "?")
                self._update_status.configure(
                    text=f"⬆ Dostupná aktualizace: v{latest}  — klikněte pro stažení",
                    text_color="#fb923c")
                self._update_status.bind("<Button-1>", lambda _: self._open_update_wizard(result))
                self._update_status.configure(cursor="hand2")
            else:
                self._update_status.configure(
                    text=t("up_to_date") + f"  (v{CURRENT_VERSION})",
                    text_color=self.theme["success"])

        check_for_update(callback=lambda r: self.after(0, on_result, r))

    def _open_update_wizard(self, result: dict):
        """Trigger the update wizard from the main window."""
        # Walk up to the MainWindow and call its update dialog
        parent = self.winfo_toplevel()
        if hasattr(parent, "_show_update_dialog"):
            parent._show_update_dialog(result)

    def _change_data_dir(self):
        import tkinter as tk
        from tkinter import filedialog
        from pathlib import Path
        current = get_data_dir()
        base = filedialog.askdirectory(
            title="Vyberte složku pro ZeddiHub.Tools.Data",
            initialdir=str(current.parent),
        )
        if base:
            new_dir = Path(base) / "ZeddiHub.Tools.Data"
            set_data_dir(new_dir)
            self._data_dir_label.configure(text=str(new_dir))

    # ─── AUTOSTART (N-15) ─────────────────────────────────────────────────────

    AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    AUTOSTART_VALUE_NAME = "ZeddiHubTools"

    def _get_autostart_target(self) -> str:
        """Vrátí cestu, která se má spouštět při startu Windows."""
        import sys as _sys
        minimized = bool(load_settings().get("start_minimized", False))
        suffix = " --minimized" if minimized else ""
        if getattr(_sys, "frozen", False):
            return f'"{_sys.executable}"{suffix}'
        app_py = Path(__file__).parent.parent.parent / "app.py"
        return f'"{_sys.executable}" "{app_py}"{suffix}'

    def _toggle_start_minimized(self):
        try:
            settings = load_settings()
            settings["start_minimized"] = bool(self._start_minimized_var.get())
            save_settings(settings)
            if self._is_autostart_enabled():
                self._toggle_autostart_rewrite()
        except Exception:
            pass

    def _toggle_autostart_rewrite(self):
        try:
            import winreg
            target = self._get_autostart_target()
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.AUTOSTART_KEY,
                                0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, self.AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, target)
        except Exception:
            pass

    def _is_autostart_enabled(self) -> bool:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.AUTOSTART_KEY) as k:
                val, _ = winreg.QueryValueEx(k, self.AUTOSTART_VALUE_NAME)
                return bool(val)
        except (ImportError, FileNotFoundError, OSError):
            return False

    def _toggle_autostart(self):
        try:
            import winreg
            if self._autostart_var.get():
                target = self._get_autostart_target()
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.AUTOSTART_KEY,
                                    0, winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, self.AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, target)
                self._autostart_status.configure(
                    text=f"✅ Autostart aktivován:\n{target}",
                    text_color=self.theme["success"],
                )
            else:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.AUTOSTART_KEY,
                                        0, winreg.KEY_SET_VALUE) as k:
                        winreg.DeleteValue(k, self.AUTOSTART_VALUE_NAME)
                except FileNotFoundError:
                    pass
                self._autostart_status.configure(
                    text="ℹ Autostart deaktivován.",
                    text_color=self.theme["text_dim"],
                )
        except ImportError:
            self._autostart_status.configure(
                text="! winreg není k dispozici (pouze Windows).",
                text_color=self.theme["warning"],
            )
            self._autostart_var.set(False)
        except Exception as e:
            self._autostart_status.configure(
                text=f"✗ Chyba při zápisu do registru: {e}",
                text_color=self.theme["error"],
            )

    def _save_close_behavior(self):
        """F-07: uloží volbu chování tlačítka zavřít (minimize vs. quit)."""
        try:
            settings = load_settings()
            settings["close_behavior"] = self._close_var.get()
            save_settings(settings)
        except Exception:
            pass

    # ─── ACCOUNT ──────────────────────────────────────────────────────────────

    def _build_account(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # ─── Profile section (N-10) ───────────────────────────────────────────
        prof_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        prof_card.pack(fill="x", pady=6)

        _label(prof_card, " " + t("profile_section"), 13, bold=True, color=th["primary"],
               image=icons.icon("id-card", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(prof_card, t("profile_hint"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 10), anchor="w")

        saved = load_settings()
        prof = saved.get("profile", {}) if isinstance(saved.get("profile", {}), dict) else {}

        prof_form = ctk.CTkFrame(prof_card, fg_color="transparent")
        prof_form.pack(fill="x", padx=14, pady=(0, 6))
        prof_form.grid_columnconfigure(1, weight=1)

        _label(prof_form, t("profile_display_name") + ":", 11, color=th["text_dim"]
               ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        self._prof_name_var = ctk.StringVar(value=prof.get("display_name", get_current_user() or ""))
        ctk.CTkEntry(prof_form, textvariable=self._prof_name_var, height=32,
                     fg_color=th["secondary"], border_color=th["border"],
                     font=ctk.CTkFont("Segoe UI", 11),
                     ).grid(row=0, column=1, sticky="ew", pady=4)

        _label(prof_form, t("profile_email") + ":", 11, color=th["text_dim"]
               ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        self._prof_email_var = ctk.StringVar(value=prof.get("email", ""))
        ctk.CTkEntry(prof_form, textvariable=self._prof_email_var, height=32,
                     fg_color=th["secondary"], border_color=th["border"],
                     font=ctk.CTkFont("Segoe UI", 11),
                     ).grid(row=1, column=1, sticky="ew", pady=4)

        _label(prof_form, t("profile_about") + ":", 11, color=th["text_dim"]
               ).grid(row=2, column=0, sticky="nw", padx=(0, 10), pady=4)
        self._prof_about_txt = ctk.CTkTextbox(
            prof_form, height=72,
            fg_color=th["secondary"], border_color=th["border"],
            font=ctk.CTkFont("Segoe UI", 11),
        )
        self._prof_about_txt.grid(row=2, column=1, sticky="ew", pady=4)
        self._prof_about_txt.insert("1.0", prof.get("about", ""))

        self._prof_status = _label(prof_card, "", 10, color=th["text_dim"])
        self._prof_status.pack(padx=14, pady=(2, 4), anchor="w")

        prof_btn_row = ctk.CTkFrame(prof_card, fg_color="transparent")
        prof_btn_row.pack(padx=14, pady=(0, 14), anchor="w")

        ctk.CTkButton(prof_btn_row, text=" " + t("profile_save"),
                      image=icons.icon("save", 13, th["text"]), compound="left",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 11, "bold"), height=34,
                      command=self._save_profile,
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(prof_btn_row, text=" " + t("profile_change_password"),
                      image=icons.icon("key", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=lambda: webbrowser.open("https://zeddihub.eu/tools/account"),
                      ).pack(side="left")

        auth_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        auth_card.pack(fill="x", pady=6)

        _label(auth_card, t("settings_auth"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        if is_authenticated():
            user = get_current_user() or "?"
            _label(auth_card, f"✅ {t('logged_in_as', user=user)}",
                   12, color=th["success"]).pack(padx=14, pady=(0, 10), anchor="w")

            ctk.CTkButton(auth_card, text=" " + t("logout"),
                          image=icons.icon("lock", 13, "#ffffff"), compound="left",
                          fg_color="#8b2020", hover_color="#6b1818",
                          font=ctk.CTkFont("Segoe UI", 12), height=36,
                          command=self._do_logout
                          ).pack(padx=14, pady=(0, 14), anchor="w")
        else:
            _label(auth_card, " " + t("not_logged_in"), 12,
                   image=icons.icon("unlock", 13, th["text_dim"]), compound="left",
                   color=th["text_dim"]).pack(padx=14, pady=(0, 8), anchor="w")
            _label(auth_card, t("server_tools_locked"),
                   10, color=th["text_dim"]).pack(padx=14, pady=(0, 10), anchor="w")
            ctk.CTkFrame(auth_card, fg_color="transparent", height=6).pack()

        # Saved credentials
        creds_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        creds_card.pack(fill="x", pady=6)

        _label(creds_card, " " + t("remember_me"), 13, bold=True, color=th["primary"],
               image=icons.icon("key", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")

        self._creds_status = _label(creds_card, "", 10, color=th["text_dim"])
        self._creds_status.pack(padx=14, pady=(0, 8), anchor="w")
        self._refresh_cred_status()

        ctk.CTkButton(creds_card, text=" " + t("clear_credentials"),
                      image=icons.icon("trash", 13, th["text"]), compound="left",
                      fg_color=th["secondary"], hover_color="#8b2020",
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._clear_creds
                      ).pack(padx=14, pady=(0, 14), anchor="w")

        # Register info
        reg_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        reg_card.pack(fill="x", pady=6)

        _label(reg_card, " " + t("register"), 13, bold=True, color=th["primary"],
               image=icons.icon("clipboard-list", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(reg_card, t("register_info"),
               10, color=th["text_dim"], wraplength=500, justify="left"
               ).pack(padx=14, pady=(0, 10), anchor="w")

        ctk.CTkButton(reg_card, text=" " + t("open_discord") + " → dsc.gg/zeddihub",
                      image=icons.icon("discord", 13, "#7289da"), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=lambda: webbrowser.open("https://dsc.gg/zeddihub")
                      ).pack(padx=14, pady=(0, 14), anchor="w")

    def _save_profile(self):
        """N-10: save profile info locally to settings.json."""
        try:
            settings = load_settings()
            settings["profile"] = {
                "display_name": self._prof_name_var.get().strip(),
                "email":        self._prof_email_var.get().strip(),
                "about":        self._prof_about_txt.get("1.0", "end").strip(),
            }
            save_settings(settings)
            self._prof_status.configure(
                text="✅ " + t("profile_saved"),
                text_color=self.theme["success"],
            )
        except Exception as e:
            self._prof_status.configure(
                text=f"✗ {e}",
                text_color=self.theme["error"],
            )

    def _do_logout(self):
        logout()
        # Refresh the panel by rebuilding
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _clear_creds(self):
        clear_credentials()
        self._refresh_cred_status()

    def _refresh_cred_status(self):
        from pathlib import Path
        import os
        cred_file = Path(os.environ.get("APPDATA", Path.home())) / "ZeddiHub" / "Tools" / "auth.enc"
        if cred_file.exists():
            self._creds_status.configure(
                text="✅ Přihlašovací údaje jsou uloženy lokálně (šifrovaně).",
                text_color=self.theme["success"])
        else:
            self._creds_status.configure(
                text=t("no_saved_credentials"),
                text_color=self.theme["text_dim"])

    # ─── ABOUT ────────────────────────────────────────────────────────────────

    def _build_about(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # Logo
        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((80, 80), Image.LANCZOS)
                self._about_logo = ctk.CTkImage(img, size=(80, 80))
                ctk.CTkLabel(scroll, image=self._about_logo, text="").pack(pady=(16, 4))
            except Exception:
                pass

        _label(scroll, "ZeddiHub Tools", 22, bold=True, color=th["primary"]
               ).pack(pady=(8, 2))
        _label(scroll, f"v{CURRENT_VERSION}", 13, color=th["text_dim"]
               ).pack(pady=(0, 4))
        _label(scroll, "by ZeddiS  |  zeddihub.eu", 10, color=th["text_dark"]
               ).pack(pady=(0, 16))

        # Info card
        info_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        info_card.pack(fill="x", pady=6, padx=40)

        info_lines = [
            (t("about_version"), f"v{CURRENT_VERSION}"),
            ("Platform", "Windows (customtkinter)"),
            (t("about_github"), "github.com/ZeddiS"),
        ]
        for label_text, value in info_lines:
            row = ctk.CTkFrame(info_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            _label(row, label_text, 11, color=th["text_dim"]).pack(side="left")
            _label(row, value, 11, bold=True, color=th["text"]).pack(side="right")

        # Link buttons
        links_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=14)
        links_card.pack(fill="x", pady=6, padx=40)

        _label(links_card, " Odkazy", 12, bold=True, color=th["primary"],
               image=icons.icon("link", 14, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")

        links = [
            (" GitHub", "https://github.com/ZeddiS/zeddihub-tools-desktop", "github"),
            (" Discord", "https://dsc.gg/zeddihub", "discord"),
            (" ZeddiHub.eu", "https://zeddihub.eu", "globe"),
            (" ZeddiS.xyz", "https://zeddis.xyz", "user"),
        ]
        for lbl, url, icon_name in links:
            ctk.CTkButton(links_card, text=lbl, height=34,
                          fg_color=th["secondary"], hover_color=th["primary"],
                          font=ctk.CTkFont("Segoe UI", 11), anchor="w",
                          image=icons.icon(icon_name, 13, th["text_dim"]), compound="left",
                          command=lambda u=url: webbrowser.open(u)
                          ).pack(fill="x", padx=14, pady=3)

        ctk.CTkFrame(links_card, fg_color="transparent", height=8).pack()

        _label(scroll, "Vytvořeno s ❤ pro herní komunitu ZeddiHub.",
               10, color=th["text_dark"]).pack(pady=16)
