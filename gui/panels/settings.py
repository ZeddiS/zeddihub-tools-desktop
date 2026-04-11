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
        tab = ctk.CTkTabview(self, fg_color=th["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=12, pady=12)

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

        _label(scroll, " " + t("settings_title"), 16, bold=True, color=th["primary"],
               image=icons.icon("cog", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 12), anchor="w")

        # Language section
        lang_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
        mode_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
        update_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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

        # Data folder section
        data_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
        reset_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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

    # ─── ACCOUNT ──────────────────────────────────────────────────────────────

    def _build_account(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, " " + t("account"), 16, bold=True, color=th["primary"],
               image=icons.icon("user", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 12), anchor="w")

        auth_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
            _label(auth_card, " " + t("not_logged_in"),
                   image=icons.icon("unlock", 13, th["text_dim"]), compound="left",
                   12, color=th["text_dim"]).pack(padx=14, pady=(0, 8), anchor="w")
            _label(auth_card, t("server_tools_locked"),
                   10, color=th["text_dim"]).pack(padx=14, pady=(0, 10), anchor="w")
            ctk.CTkFrame(auth_card, fg_color="transparent", height=6).pack()

        # Saved credentials
        creds_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
        reg_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
        info_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
        links_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
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
