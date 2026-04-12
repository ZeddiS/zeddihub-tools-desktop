"""
ZeddiHub Tools - Main application window with collapsible sidebar navigation.
"""

import os
import sys
import json
import webbrowser
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

from .themes import get_theme, GAME_THEMES
from .auth import is_authenticated, load_credentials, verify_access, save_credentials, clear_credentials, logout, get_current_user
from .updater import check_for_update, download_update, apply_update, open_release_page, CURRENT_VERSION
from .locale import t, get_lang, set_lang, init as locale_init, load_settings, save_settings
from . import icons
from . import telemetry

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo2.png"          # header / sidebar logo
ICON_PATH = ASSETS_DIR / "web_favicon.ico"    # window + tray icon
LOGO_ICON_PATH = ASSETS_DIR / "logo_icon.png" # fallback

SIDEBAR_W = 240
HEADER_H = 54

# Section definitions: (section_id, label, fa_icon, game, items)
# items: [(nav_id, label, fa_icon, requires_auth), ...]
NAV_SECTIONS = [
    ("home",     None,    "house",        None,   None, False),
    ("pc_tools", None,    "laptop",       None,   None, False),
    ("watchdog", None,    "bell",         None,   None, False),
    ("sec_cs2",  "CS2",   "crosshairs",   "cs2",  [
        ("cs2_player",  "player_tools",  "user",     False),
        ("cs2_server",  "server_tools",  "server",   True),
        ("cs2_keybind", "keybind",       "keyboard", False),
    ], None),
    ("sec_csgo", "CS:GO", "gamepad",      "csgo", [
        ("csgo_player",  "player_tools",  "user",     False),
        ("csgo_server",  "server_tools",  "server",   True),
        ("csgo_keybind", "keybind",       "keyboard", False),
    ], None),
    ("sec_rust", "Rust",  "puzzle-piece", "rust", [
        ("rust_player",  "player_tools",  "user",     False),
        ("rust_server",  "server_tools",  "server",   True),
        ("rust_keybind", "keybind",       "keyboard", False),
    ], None),
    ("game_tools", None, "gamepad", None, None, False),
]

# Map nav_id -> game for theme switching
NAV_GAME_MAP = {
    "cs2_player": "cs2", "cs2_server": "cs2", "cs2_keybind": "cs2",
    "csgo_player": "csgo", "csgo_server": "csgo", "csgo_keybind": "csgo",
    "rust_player": "rust", "rust_server": "rust", "rust_keybind": "rust",
    "home": "default", "pc_tools": "default", "translator": "default",
    "game_tools": "default",
    "links": "default", "settings": "default", "watchdog": "default",
}

# nav_ids that show NO game badge in header
NO_BADGE_IDS = {"home", "pc_tools", "translator", "game_tools", "links", "settings", "watchdog"}


class AuthDialog(ctk.CTkToplevel):
    """Login dialog for server tools access with registration info."""

    def __init__(self, parent, theme: dict, on_success=None):
        super().__init__(parent)
        self.theme = theme
        self.result = False
        self._on_success = on_success
        self.title(t("login_title") + " – Server Tools")
        self.geometry("460x420")
        self.resizable(False, False)
        self.configure(fg_color=theme["content_bg"])
        self.grab_set()
        self._build()

        # Try to load saved credentials
        saved = load_credentials()
        if saved:
            self._user_entry.insert(0, saved[0])
            self._pass_entry.insert(0, saved[1])
            self._remember_var.set(True)

    def _build(self):
        th = self.theme

        # Tab view: Login / Register
        self._tab = ctk.CTkTabview(self, fg_color=th["content_bg"])
        self._tab.pack(fill="both", expand=True, padx=0, pady=0)
        self._tab.add(t("login_btn"))
        self._tab.add(t("register"))

        self._build_login_tab(self._tab.tab(t("login_btn")), th)
        self._build_register_tab(self._tab.tab(t("register")), th)

    def _build_login_tab(self, tab, th):
        ctk.CTkLabel(tab,
                     image=icons.icon("lock", 18, th["primary"]),
                     text="  " + t("login_title"),
                     compound="left",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=th["primary"]).pack(pady=(16, 4), padx=20, anchor="w")
        ctk.CTkLabel(tab, text=t("login_subtitle"),
                     font=ctk.CTkFont("Segoe UI", 11), text_color=th["text_dim"]
                     ).pack(padx=20, anchor="w")

        form = ctk.CTkFrame(tab, fg_color=th["card_bg"], corner_radius=8)
        form.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(form, text=t("username") + " / kód:",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=th["text_dim"], anchor="w"
                     ).pack(padx=16, pady=(12, 2), anchor="w")
        self._user_entry = ctk.CTkEntry(form, placeholder_text="username nebo access_code",
                                        fg_color=th["secondary"], text_color=th["text"],
                                        font=ctk.CTkFont("Segoe UI", 12), height=36)
        self._user_entry.pack(padx=16, fill="x")

        ctk.CTkLabel(form, text=t("password") + " (prázdné pro kód):",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=th["text_dim"], anchor="w"
                     ).pack(padx=16, pady=(8, 2), anchor="w")
        self._pass_entry = ctk.CTkEntry(form, placeholder_text="heslo...",
                                        fg_color=th["secondary"], text_color=th["text"],
                                        font=ctk.CTkFont("Segoe UI", 12), height=36, show="*")
        self._pass_entry.pack(padx=16, pady=(0, 4), fill="x")
        self._pass_entry.bind("<Return>", lambda _: self._login())

        self._remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text=t("remember_me"),
                        variable=self._remember_var,
                        text_color=th["text_dim"], fg_color=th["primary"],
                        font=ctk.CTkFont("Segoe UI", 10)
                        ).pack(padx=16, pady=(4, 12), anchor="w")

        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(tab, textvariable=self.status_var,
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=th["warning"]).pack(padx=20, anchor="w")

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_row,
                      image=icons.icon("right-to-bracket", 16, "#ffffff"),
                      text=" " + t("login_btn"),
                      compound="left",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"), height=38,
                      command=self._login).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_row, text=t("cancel"),
                      fg_color=th["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 12), height=38,
                      command=self.destroy).pack(side="left", width=100)

    def _build_register_tab(self, tab, th):
        ctk.CTkLabel(tab,
                     image=icons.icon("address-card", 18, th["primary"]),
                     text="  " + t("register"),
                     compound="left",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=th["primary"]).pack(pady=(20, 8), padx=20, anchor="w")

        info_frame = ctk.CTkFrame(tab, fg_color=th["card_bg"], corner_radius=8)
        info_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(info_frame,
                     text="Registrace není momentálně dostupná.\n\nPro přístup kontaktujte administrátora\nna Discordu nebo webu ZeddiS.xyz.",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=th["text_dim"],
                     justify="left").pack(padx=16, pady=16, anchor="w")

        ctk.CTkButton(info_frame,
                      image=icons.icon("discord", 16, "#7289da"),
                      text=" Otevřít Discord → dsc.gg/zeddihub",
                      compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 12), height=36,
                      command=lambda: webbrowser.open("https://dsc.gg/zeddihub")
                      ).pack(padx=16, pady=(0, 8), fill="x")

        ctk.CTkButton(info_frame,
                      image=icons.icon("globe", 16, "#cccccc"),
                      text=" ZeddiS.xyz",
                      compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 12), height=36,
                      command=lambda: webbrowser.open("https://zeddis.xyz")
                      ).pack(padx=16, pady=(0, 12), fill="x")

    def _login(self):
        user = self._user_entry.get().strip()
        pw = self._pass_entry.get().strip()
        if not user:
            self.status_var.set("Zadejte uživatelské jméno nebo přístupový kód.")
            return

        self.status_var.set("Ověřuji...")
        remember = self._remember_var.get()

        def on_result(success: bool, msg: str):
            if success:
                if remember:
                    save_credentials(user, pw, True)
                else:
                    clear_credentials()
                self.result = True
                from . import telemetry as _telem
                _telem.on_login(user)
                if self._on_success:
                    self._on_success()
                self.destroy()
            else:
                self.status_var.set(f"✗ {msg}")

        verify_access(user, pw, callback=lambda s, m: self.after(0, on_result, s, m))


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize locale
        locale_init()

        self._current_panel: Optional[ctk.CTkFrame] = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._section_states: dict[str, bool] = {}   # True = expanded
        self._section_frames: dict[str, ctk.CTkFrame] = {}  # children container
        self._section_btns: dict[str, ctk.CTkButton] = {}
        self._current_game: str = "default"
        self._current_nav_id: str = "home"
        self._locked_navs: set = set()

        icons.preload()
        self._setup_window()
        self._setup_icon()
        self._build_layout()
        self._navigate("home")

        # Check for updates in background (callback safely scheduled on main thread)
        check_for_update(callback=lambda r: self.after(0, self._on_update_check, r))

        # Try auto-login from saved credentials
        saved = load_credentials()
        if saved:
            verify_access(saved[0], saved[1],
                          callback=lambda s, m: self.after(100, self._update_auth_ui) if s else None)

        # Telemetry: launch event (fire after a short delay so UI is ready)
        self.after(2000, lambda: telemetry.on_launch(get_current_user()))

        # System tray
        self._tray = None
        self.after(500, self._start_tray)
        self.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

    def _setup_window(self):
        self.title("ZeddiHub Tools")
        w, h = 1280, 820
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(960, 640)

        # Load appearance mode from settings
        settings = load_settings()
        mode = settings.get("appearance_mode", "dark")
        if mode == "system":
            mode = "dark"  # CTK handles system internally
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#0c0c0c")

    def _setup_icon(self):
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
                return
            except Exception:
                pass
        for png_path in [LOGO_ICON_PATH, LOGO_PATH]:
            if PIL_OK and png_path.exists():
                try:
                    img = Image.open(png_path).resize((32, 32), Image.LANCZOS)
                    self._icon_img = ImageTk.PhotoImage(img)
                    self.iconphoto(True, self._icon_img)
                    return
                except Exception:
                    pass

    def _build_layout(self):
        th = self._get_current_theme()
        self._main = ctk.CTkFrame(self, fg_color=th["bg"], corner_radius=0)
        self._main.pack(fill="both", expand=True)

        # Header
        self._header = ctk.CTkFrame(self._main, fg_color=th["header_bg"], height=HEADER_H, corner_radius=0)
        self._header.pack(fill="x", side="top")
        self._header.pack_propagate(False)
        self._build_header()

        # Thin separator
        self._header_sep = ctk.CTkFrame(self._main, fg_color=th["border"], height=1, corner_radius=0)
        self._header_sep.pack(fill="x")

        # Body
        body = ctk.CTkFrame(self._main, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ctk.CTkFrame(body, fg_color=th["sidebar_bg"], width=SIDEBAR_W, corner_radius=0)
        self._sidebar.pack(fill="y", side="left")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Thin vertical separator
        self._sidebar_sep = ctk.CTkFrame(body, fg_color=th["border"], width=1, corner_radius=0)
        self._sidebar_sep.pack(fill="y", side="left")

        # Content
        self._content_container = ctk.CTkFrame(body, fg_color=th["content_bg"], corner_radius=0)
        self._content_container.pack(fill="both", expand=True, side="left")

    def _build_header(self):
        # Left: logo + title
        left = ctk.CTkFrame(self._header, fg_color="transparent")
        left.pack(side="left", padx=16, fill="y")

        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((32, 32), Image.LANCZOS)
                self._header_logo = ctk.CTkImage(img, size=(32, 32))
                ctk.CTkLabel(left, image=self._header_logo, text="").pack(side="left", padx=(0, 8))
            except Exception:
                pass

        ctk.CTkLabel(left, text="ZeddiHub Tools",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color="#f0a500").pack(side="left")

        self._game_badge = ctk.CTkLabel(left, text="",
                                         font=ctk.CTkFont("Segoe UI", 11),
                                         text_color="#666666")
        self._game_badge.pack(side="left", padx=(10, 0))

        # Right: auth status + version
        right = ctk.CTkFrame(self._header, fg_color="transparent")
        right.pack(side="right", padx=16, fill="y")

        self._version_label = ctk.CTkLabel(right, text=f"v{CURRENT_VERSION}",
                                            font=ctk.CTkFont("Segoe UI", 9),
                                            text_color="#444444")
        self._version_label.pack(side="right", padx=(4, 0))

        self._auth_label = ctk.CTkLabel(right,
                                         image=icons.icon("lock-open", 13, "#666666"),
                                         text=" " + t("not_logged_in"),
                                         compound="left",
                                         font=ctk.CTkFont("Segoe UI", 10),
                                         text_color="#666666")
        self._auth_label.pack(side="right", padx=8)

        self._update_label = ctk.CTkLabel(right, text="",
                                           font=ctk.CTkFont("Segoe UI", 10),
                                           text_color="#f0a500")
        self._update_label.pack(side="right", padx=8)

        # Dark/light mode toggle
        self._mode_btn = ctk.CTkButton(
            right, image=icons.icon("sun", 15, "#666666"), text="",
            width=34, height=28,
            fg_color="transparent", hover_color="#2a2a2a",
            command=self._toggle_appearance_mode
        )
        self._mode_btn.pack(side="right", padx=4)
        self._update_mode_btn()

    def _build_sidebar(self):
        th = self._get_current_theme()
        nav_text = th["text"]
        nav_dim = th["text_dim"]
        nav_hover = th["card_bg"]

        # Top logo area
        logo_area = ctk.CTkFrame(self._sidebar, fg_color=th["bg"], height=60, corner_radius=0)
        logo_area.pack(fill="x")
        logo_area.pack_propagate(False)

        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((36, 36), Image.LANCZOS)
                self._sidebar_logo_img = ctk.CTkImage(img, size=(36, 36))
                ctk.CTkLabel(logo_area, image=self._sidebar_logo_img, text="").pack(
                    side="left", padx=12, pady=12)
            except Exception:
                pass

        ctk.CTkLabel(logo_area, text="ZeddiHub\nTools",
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=th["primary"], justify="left"
                     ).pack(side="left", pady=12)

        ctk.CTkFrame(self._sidebar, fg_color=th["border"], height=1).pack(fill="x")

        # Scrollable nav area
        self._nav_scroll = ctk.CTkScrollableFrame(
            self._sidebar, fg_color="transparent",
            scrollbar_button_color=th["border"],
            scrollbar_button_hover_color=th["secondary"]
        )
        self._nav_scroll.pack(fill="both", expand=True, padx=0, pady=4)

        self._build_nav_items()

        # Bottom section: settings + language
        ctk.CTkFrame(self._sidebar, fg_color=th["border"], height=1).pack(fill="x", side="bottom")

        lang = get_lang()
        lang_flag = "🇨🇿" if lang == "cs" else "🇬🇧"
        lang_name = "Česky" if lang == "cs" else "English"
        self._lang_btn = ctk.CTkButton(
            self._sidebar,
            text=f"{lang_flag} {lang_name}",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_dim, anchor="w",
            font=ctk.CTkFont("Segoe UI", 10),
            height=30,
            command=self._toggle_language
        )
        self._lang_btn.pack(fill="x", padx=4, pady=(2, 2), side="bottom")

        self._auth_btn = ctk.CTkButton(
            self._sidebar,
            image=icons.icon("right-to-bracket", 15, nav_text),
            text=" " + t("login"),
            compound="left",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_text, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36, command=self._show_auth_dialog
        )
        self._auth_btn.pack(fill="x", padx=4, pady=2, side="bottom")

        self._settings_btn = ctk.CTkButton(
            self._sidebar,
            image=icons.icon("gear", 15, nav_text),
            text="  " + t("settings"),
            compound="left",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_text, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36, command=lambda: self._navigate("settings")
        )
        self._settings_btn.pack(fill="x", padx=4, pady=2, side="bottom")

        self._links_btn = ctk.CTkButton(
            self._sidebar,
            image=icons.icon("link", 15, nav_text),
            text="  " + t("links"),
            compound="left",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_text, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36, command=lambda: self._navigate("links")
        )
        self._links_btn.pack(fill="x", padx=4, pady=2, side="bottom")

    def _build_nav_items(self):
        th = self._get_current_theme()
        nav_text = th["text"]
        nav_dim = th["text_dim"]
        nav_dim2 = th["text_dark"]
        nav_hover = th["card_bg"]

        # Load saved section states
        settings = load_settings()
        saved_states = settings.get("sidebar_sections", {})

        for entry in NAV_SECTIONS:
            if len(entry) == 6:
                sec_id, label, icon, game, children, _ = entry
            else:
                continue

            if children is None:
                # Top-level nav button (home, pc_tools, watchdog)
                nav_id = sec_id
                display_label = {
                    "home":       t("home"),
                    "pc_tools":   t("pc_tools"),
                    "watchdog":   "Watchdog",
                    "game_tools": t("game_tools"),
                }.get(nav_id, nav_id)
                btn = ctk.CTkButton(
                    self._nav_scroll,
                    image=icons.icon(icon, 16, nav_text),
                    text=f"  {display_label}",
                    compound="left",
                    fg_color="transparent",
                    hover_color=nav_hover,
                    text_color=nav_text,
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 12),
                    height=38,
                    corner_radius=6,
                    command=lambda nid=nav_id: self._navigate(nid)
                )
                btn.pack(fill="x", padx=6, pady=1)
                self._nav_buttons[nav_id] = btn
            else:
                # Wrapper keeps section header + children together so
                # pack_forget/pack on children_frame never changes order.
                outer = ctk.CTkFrame(self._nav_scroll, fg_color="transparent")
                outer.pack(fill="x", padx=0, pady=0)

                default_expanded = (sec_id == "sec_cs2")
                is_expanded = saved_states.get(sec_id, default_expanded)
                self._section_states[sec_id] = is_expanded

                arrow = "▼" if is_expanded else "▶"
                # Translate label if it's a locale key (contains underscore), else use as-is
                display_sec_label = t(label) if label and "_" in label else (label or "")
                section_btn = ctk.CTkButton(
                    outer,
                    image=icons.icon(icon, 14, nav_dim),
                    text=f"  {display_sec_label}  {arrow}",
                    compound="left",
                    fg_color="transparent",
                    hover_color=nav_hover,
                    text_color=nav_dim,
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 11, "bold"),
                    height=34,
                    corner_radius=4,
                    command=lambda sid=sec_id: self._toggle_section(sid)
                )
                section_btn.pack(fill="x", padx=4, pady=(6, 1))
                self._section_btns[sec_id] = section_btn

                # Children frame lives inside outer — toggling it never reorders siblings
                children_frame = ctk.CTkFrame(outer, fg_color="transparent")
                self._section_frames[sec_id] = children_frame

                if is_expanded:
                    children_frame.pack(fill="x", padx=0, pady=0)

                for nav_id, child_label_key, child_icon, requires_auth in children:
                    # child_label_key is a locale key → translate it
                    child_label = t(child_label_key)
                    locked = requires_auth and not is_authenticated()
                    if locked:
                        self._locked_navs.add(nav_id)
                    child_img = icons.icon("lock", 14, nav_dim2) if locked else icons.icon(child_icon, 14, nav_text)
                    tc = nav_dim2 if locked else nav_text
                    fg = th["secondary"] if locked else "transparent"

                    btn = ctk.CTkButton(
                        children_frame,
                        image=child_img,
                        text=f"   {child_label}",
                        compound="left",
                        fg_color=fg,
                        hover_color=nav_hover,
                        text_color=tc,
                        anchor="w",
                        font=ctk.CTkFont("Segoe UI", 11),
                        height=36,
                        corner_radius=6,
                        command=lambda nid=nav_id, auth=requires_auth: self._on_nav_click(nid, auth)
                    )
                    btn.pack(fill="x", padx=6, pady=1)
                    self._nav_buttons[nav_id] = btn

    def _toggle_section(self, sec_id: str):
        is_expanded = self._section_states.get(sec_id, False)
        new_state = not is_expanded

        # ── Accordion: opening a section closes all others ────────────────────
        if new_state:
            for other_id in list(self._section_states.keys()):
                if other_id != sec_id and self._section_states.get(other_id, False):
                    self._section_states[other_id] = False
                    other_btn = self._section_btns.get(other_id)
                    if other_btn:
                        t = other_btn.cget("text")
                        other_btn.configure(text=t.replace("▼", "▶"))
                    other_frame = self._section_frames.get(other_id)
                    if other_frame:
                        other_frame.pack_forget()

        self._section_states[sec_id] = new_state

        btn = self._section_btns.get(sec_id)
        if btn:
            text = btn.cget("text")
            text = text.replace("▶", "▼") if new_state else text.replace("▼", "▶")
            btn.configure(text=text)

        frame = self._section_frames.get(sec_id)
        if frame:
            if new_state:
                frame.pack(fill="x", padx=0, pady=0)
            else:
                frame.pack_forget()

        # Persist all section states
        settings = load_settings()
        if "sidebar_sections" not in settings:
            settings["sidebar_sections"] = {}
        for sid, state in self._section_states.items():
            settings["sidebar_sections"][sid] = state
        save_settings(settings)

    def _on_nav_click(self, nav_id: str, requires_auth: bool):
        if requires_auth and not is_authenticated():
            dialog = AuthDialog(self, get_theme(self._current_game),
                                on_success=lambda: self.after(0, self._update_auth_ui))
            self.wait_window(dialog)
            if not dialog.result:
                return
            self._update_auth_ui()

        self._navigate(nav_id)

    def _navigate(self, nav_id: str):
        self._current_nav_id = nav_id

        # Determine game for this nav_id
        game = NAV_GAME_MAP.get(nav_id, "default")
        if game != self._current_game:
            self._current_game = game
            self._apply_theme()

        # Update header game badge
        if nav_id in NO_BADGE_IDS:
            self._game_badge.configure(text="")
        else:
            t_dict = get_theme(game)
            game_names = {"cs2": "Counter-Strike 2", "csgo": "CS:GO", "rust": "Rust"}
            self._game_badge.configure(
                text=game_names.get(game, ""),
                text_color=t_dict["primary"]
            )

        # Update nav button styles
        mode = ctk.get_appearance_mode().lower()
        for nid, btn in self._nav_buttons.items():
            nid_game = NAV_GAME_MAP.get(nid, "default")
            btn_th = get_theme(nid_game, mode)
            cur_th = get_theme(self._current_game, mode)
            if nid == nav_id:
                btn.configure(fg_color=btn_th["primary"], text_color="#ffffff",
                              hover_color=btn_th["primary_hover"])
            else:
                is_locked = nid in self._locked_navs
                tc = cur_th["text_dark"] if is_locked else cur_th["text"]
                fg = cur_th["secondary"] if is_locked else "transparent"
                btn.configure(fg_color=fg, text_color=tc, hover_color=cur_th["card_bg"])

        # Update settings / links button highlights
        if nav_id == "settings":
            self._settings_btn.configure(fg_color=get_theme("default")["primary"], text_color="#ffffff")
        else:
            self._settings_btn.configure(fg_color="transparent", text_color="#aaaaaa")

        if hasattr(self, "_links_btn"):
            if nav_id == "links":
                self._links_btn.configure(fg_color=get_theme("default")["primary"], text_color="#ffffff")
            else:
                self._links_btn.configure(fg_color="transparent", text_color="#aaaaaa")

        self._show_panel(nav_id)

    def _get_current_theme(self) -> dict:
        mode = ctk.get_appearance_mode().lower()
        return get_theme(self._current_game if hasattr(self, "_current_game") else "default", mode)

    def _apply_theme(self):
        th = self._get_current_theme()
        self._content_container.configure(fg_color=th["content_bg"])
        self._sidebar.configure(fg_color=th["sidebar_bg"])
        self._header.configure(fg_color=th["header_bg"])
        if hasattr(self, "_main"):
            self._main.configure(fg_color=th["bg"])
        if hasattr(self, "_header_sep"):
            self._header_sep.configure(fg_color=th["border"])
        if hasattr(self, "_sidebar_sep"):
            self._sidebar_sep.configure(fg_color=th["border"])

        # Update all nav button hover/inactive colors for new theme
        nav_text = th["text"]
        nav_dim = th["text_dark"]
        nav_hover = th["card_bg"]
        for nid, btn in self._nav_buttons.items():
            if nid == self._current_nav_id:
                continue  # keep active highlight
            is_locked = nid in self._locked_navs
            btn.configure(
                text_color=nav_dim if is_locked else nav_text,
                fg_color=th["secondary"] if is_locked else "transparent",
                hover_color=nav_hover,
            )

        # Update section header buttons
        for sid, sbtn in self._section_btns.items():
            sbtn.configure(text_color=th["text_dim"], hover_color=nav_hover)

        # Update bottom sidebar buttons
        for attr in ("_settings_btn", "_links_btn", "_auth_btn", "_lang_btn"):
            w = getattr(self, attr, None)
            if w:
                w.configure(hover_color=nav_hover)

    def _show_panel(self, nav_id: str):
        if self._current_panel:
            self._current_panel.destroy()
            self._current_panel = None

        mode = ctk.get_appearance_mode().lower()
        th   = get_theme(self._current_game, mode)
        container = self._content_container

        def _th(game="default"):
            return get_theme(game, mode)

        # Lazy imports to avoid circular deps
        panel = None
        if nav_id == "home":
            from .panels.home import HomePanel
            panel = HomePanel(container, theme=_th(), nav_callback=self._navigate)
        elif nav_id == "pc_tools":
            from .panels.pc_tools import PCToolsPanel
            panel = PCToolsPanel(container, theme=_th())
        elif nav_id == "settings":
            from .panels.settings import SettingsPanel
            panel = SettingsPanel(container, theme=_th(),
                                   on_language_change=self._on_language_change)
        elif nav_id == "cs2_player":
            from .panels.cs2 import CS2PlayerPanel
            panel = CS2PlayerPanel(container, theme=th)
        elif nav_id == "cs2_server":
            from .panels.cs2 import CS2ServerPanel
            panel = CS2ServerPanel(container, theme=th)
        elif nav_id == "cs2_keybind":
            from .panels.keybind import KeybindPanel
            panel = KeybindPanel(container, game="cs2", theme=th)
        elif nav_id == "csgo_player":
            from .panels.csgo import CSGOPlayerPanel
            panel = CSGOPlayerPanel(container, theme=th)
        elif nav_id == "csgo_server":
            from .panels.csgo import CSGOServerPanel
            panel = CSGOServerPanel(container, theme=th)
        elif nav_id == "csgo_keybind":
            from .panels.keybind import KeybindPanel
            panel = KeybindPanel(container, game="csgo", theme=th)
        elif nav_id == "rust_player":
            from .panels.rust import RustPlayerPanel
            panel = RustPlayerPanel(container, theme=th)
        elif nav_id == "rust_server":
            from .panels.rust import RustServerPanel
            panel = RustServerPanel(container, theme=th)
        elif nav_id == "rust_keybind":
            from .panels.keybind import KeybindPanel
            panel = KeybindPanel(container, game="rust", theme=th)
        elif nav_id in ("translator", "game_tools"):
            from .panels.game_tools import GameToolsPanel
            panel = GameToolsPanel(container, theme=_th())
        elif nav_id == "links":
            from .panels.links import LinksPanel
            panel = LinksPanel(container, theme=_th())
        elif nav_id == "watchdog":
            from .panels.watchdog import WatchdogPanel
            panel = WatchdogPanel(container, theme=_th())

        if panel:
            panel.pack(fill="both", expand=True)
            self._current_panel = panel
            telemetry.on_panel_open(nav_id, get_current_user())

    def _show_auth_dialog(self):
        if is_authenticated():
            user = get_current_user()
            dialog = _LogoutDialog(self, get_theme(self._current_game), user)
            self.wait_window(dialog)
            if dialog.result == "logout":
                logout()
                self._update_auth_ui()
        else:
            dialog = AuthDialog(self, get_theme(self._current_game),
                                on_success=lambda: self.after(0, self._update_auth_ui))
            self.wait_window(dialog)
            if dialog.result:
                self._update_auth_ui()

    def _update_auth_ui(self):
        if is_authenticated():
            user = get_current_user() or "?"
            self._auth_label.configure(
                image=icons.icon("user", 13, "#4ade80"),
                text=f" {user}", text_color="#4ade80")
            self._auth_btn.configure(
                image=icons.icon("check", 15, "#4ade80"),
                text=f"  {t('logged_in_as', user=user)}", text_color="#4ade80")

            # Unlock locked nav items
            for entry in NAV_SECTIONS:
                if len(entry) < 6:
                    continue
                sec_id, label, icon, game, children, _ = entry
                if children is None:
                    continue
                for nav_id, child_label_key, child_icon, requires_auth in children:
                    child_label = t(child_label_key)
                    if requires_auth and nav_id in self._nav_buttons:
                        self._locked_navs.discard(nav_id)
                        btn = self._nav_buttons[nav_id]
                        if nav_id == self._current_nav_id:
                            th = get_theme(NAV_GAME_MAP.get(nav_id, "default"))
                            btn.configure(
                                image=icons.icon(child_icon, 14, "#ffffff"),
                                text=f"   {child_label}",
                                fg_color=th["primary"], text_color="#ffffff")
                        else:
                            cur_th = self._get_current_theme()
                            btn.configure(
                                image=icons.icon(child_icon, 14, cur_th["text"]),
                                text=f"   {child_label}",
                                fg_color="transparent", text_color=cur_th["text"])
        else:
            self._auth_label.configure(
                image=icons.icon("lock-open", 13, "#666666"),
                text=" " + t("not_logged_in"), text_color="#666666")
            self._auth_btn.configure(
                image=icons.icon("right-to-bracket", 15, "#888888"),
                text=" " + t("login"), text_color="#888888")

            # Re-lock nav items
            th = self._get_current_theme()
            for entry in NAV_SECTIONS:
                if len(entry) < 6:
                    continue
                sec_id, label, icon, game, children, _ = entry
                if children is None:
                    continue
                for nav_id, child_label_key, child_icon, requires_auth in children:
                    child_label = t(child_label_key)
                    if requires_auth and nav_id in self._nav_buttons:
                        self._locked_navs.add(nav_id)
                        btn = self._nav_buttons[nav_id]
                        btn.configure(
                            image=icons.icon("lock", 14, th["text_dark"]),
                            text=f"   {child_label}",
                            fg_color=th["secondary"], text_color=th["text_dark"]
                        )

    def _toggle_appearance_mode(self):
        current = ctk.get_appearance_mode().lower()
        new_mode = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        settings = load_settings()
        settings["appearance_mode"] = new_mode
        save_settings(settings)
        self._update_mode_btn()
        # Slight delay lets CTK finish its own recolor, then re-apply our theme
        # and reload the current panel so it picks up the new colors
        self.after(80, self._apply_theme)
        self.after(120, lambda: self._show_panel(self._current_nav_id))

    def _update_mode_btn(self):
        mode = ctk.get_appearance_mode().lower()
        ic = icons.icon("moon", 15, "#666666") if mode == "dark" else icons.icon("sun", 15, "#666666")
        self._mode_btn.configure(image=ic, text="")

    def _toggle_language(self):
        current = get_lang()
        new_lang = "en" if current == "cs" else "cs"
        set_lang(new_lang)

        flag = "🇬🇧" if new_lang == "en" else "🇨🇿"
        name = "English" if new_lang == "en" else "Česky"
        self._lang_btn.configure(text=f"{flag} {name}")

        # Show notice
        notice = ctk.CTkToplevel(self)
        notice.title(t("restart_required"))
        notice.geometry("380x140")
        notice.configure(fg_color="#1a1a1a")
        notice.grab_set()
        ctk.CTkLabel(notice, text=t("language_changed"),
                     font=ctk.CTkFont("Segoe UI", 12), text_color="#f0f0f0",
                     wraplength=340).pack(pady=24, padx=20)
        ctk.CTkButton(notice, text=t("close"), command=notice.destroy,
                      fg_color="#f0a500", hover_color="#d99400").pack(pady=8)

    def _on_language_change(self, lang: str):
        set_lang(lang)
        flag = "🇬🇧" if lang == "en" else "🇨🇿"
        name = "English" if lang == "en" else "Česky"
        self._lang_btn.configure(text=f"{flag} {name}")

    def _start_tray(self):
        try:
            from .tray import TrayIcon
            self._tray = TrayIcon(self)
            self._tray.start()
        except Exception:
            pass

    def _minimize_to_tray(self):
        """Hide window to tray on first close; show one-time info dialog."""
        settings = load_settings()
        if self._tray is not None:
            if not settings.get("tray_close_shown", False):
                settings["tray_close_shown"] = True
                save_settings(settings)
                self._show_tray_notice()
                return  # notice has its own close/minimize buttons
            self.withdraw()
        else:
            self._quit_app()

    def _show_tray_notice(self):
        """One-time dialog explaining app minimizes to tray."""
        th = self._get_current_theme()
        d = ctk.CTkToplevel(self)
        d.title("Minimalizace do tray")
        d.geometry("400x200")
        d.configure(fg_color=th["content_bg"])
        d.resizable(False, False)
        d.grab_set()
        d.protocol("WM_DELETE_WINDOW", lambda: (self.withdraw(), d.destroy()))

        ctk.CTkLabel(d,
                     image=icons.icon("circle-info", 22, th["primary"]),
                     text="  Aplikace běží na pozadí",
                     compound="left",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=th["text"]).pack(pady=(20, 6), padx=20, anchor="w")
        ctk.CTkLabel(d,
                     text="Zavřením okna se aplikace minimalizuje do\nsystémové lišty. Pravým klikem na ikonu\nv trayi otevřeš menu pro úplné ukončení.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=th["text_dim"],
                     justify="left").pack(padx=20, pady=(0, 16), anchor="w")

        row = ctk.CTkFrame(d, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=4)
        ctk.CTkButton(row, text="Minimalizovat do tray",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 12), height=36,
                      command=lambda: (self.withdraw(), d.destroy())
                      ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="Ukončit",
                      fg_color=th["secondary"], hover_color=th["error"],
                      font=ctk.CTkFont("Segoe UI", 12), height=36,
                      command=lambda: (d.destroy(), self._quit_app())
                      ).pack(side="left", width=90)

    def _quit_app(self):
        """Full shutdown: stop tray then destroy window."""
        if self._tray is not None:
            self._tray.stop()
        try:
            self.destroy()
        except Exception:
            pass

    def _on_update_check(self, result):
        if result and result.get("available"):
            latest = result.get("latest", "?")
            self._update_label.configure(
                image=icons.icon("arrow-up", 12, "#fb923c"),
                compound="left",
                text=f" v{latest}",
                text_color="#fb923c",
                cursor="hand2"
            )
            self._update_label.bind("<Button-1>", lambda _: self._show_update_dialog(result))
            # Auto-show popup once — delay ensures main window is fully rendered
            if not getattr(self, "_update_dialog_shown", False):
                self._update_dialog_shown = True
                self.after(1500, lambda: self._show_update_dialog(result))

    def _show_update_dialog(self, update_info: dict):
        """Update download wizard — Step 1: info, Step 2: downloading, Step 3: done."""
        th = get_theme(self._current_game)
        d = ctk.CTkToplevel(self)
        d.title(t("update_available"))
        d.geometry("480x380")
        d.configure(fg_color=th["content_bg"])
        d.resizable(False, False)
        # Delay grab_set so the window has time to fully render before grabbing input
        d.after(200, d.grab_set)

        latest = update_info.get("latest", "?")
        changelog = update_info.get("changelog", "")
        download_url = update_info.get("download_url", "")

        # ── Step 1: info ──────────────────────────────────────────────────────
        frame1 = ctk.CTkFrame(d, fg_color="transparent")
        frame2 = ctk.CTkFrame(d, fg_color="transparent")
        frame3 = ctk.CTkFrame(d, fg_color="transparent")

        def _show(f):
            for ff in (frame1, frame2, frame3):
                ff.pack_forget()
            f.pack(fill="both", expand=True, padx=24, pady=16)

        # Frame 1 — Info
        ctk.CTkLabel(frame1,
                     image=icons.icon("arrow-up", 20, "#fb923c"),
                     text=f"  Nová verze: v{latest}",
                     compound="left",
                     font=ctk.CTkFont("Segoe UI", 17, "bold"),
                     text_color="#fb923c").pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(frame1, text=f"Aktuální verze: v{CURRENT_VERSION}",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=th["text_dim"]).pack(anchor="w", pady=(0, 12))

        if changelog:
            notes_box = ctk.CTkTextbox(frame1, height=110, fg_color=th["card_bg"],
                                       text_color=th["text_dim"],
                                       font=ctk.CTkFont("Segoe UI", 10))
            notes_box.pack(fill="x", pady=(0, 14))
            notes_box.insert("end", changelog[:800])
            notes_box.configure(state="disabled")

        btn_row1 = ctk.CTkFrame(frame1, fg_color="transparent")
        btn_row1.pack(fill="x")

        ctk.CTkButton(btn_row1,
                      image=icons.icon("download", 16, "#ffffff"),
                      text=" Stáhnout a nainstalovat",
                      compound="left",
                      fg_color="#fb923c", hover_color="#e07b20",
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=40,
                      command=lambda: _start_download()
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_row1, text=t("later"),
                      fg_color=th["secondary"], height=40,
                      command=d.destroy).pack(side="left", width=100)

        # Frame 2 — Downloading
        ctk.CTkLabel(frame2,
                     image=icons.icon("download", 18, "#fb923c"),
                     text="  Stahuji aktualizaci...",
                     compound="left",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="#fb923c").pack(anchor="w", pady=(0, 8))
        _dl_status = ctk.CTkLabel(frame2, text="Připravuji stahování...",
                                   font=ctk.CTkFont("Segoe UI", 10),
                                   text_color=th["text_dim"])
        _dl_status.pack(anchor="w", pady=(0, 12))
        _progress_bar = ctk.CTkProgressBar(frame2, height=14,
                                            progress_color="#fb923c")
        _progress_bar.pack(fill="x", pady=(0, 4))
        _progress_bar.set(0)
        _pct_label = ctk.CTkLabel(frame2, text="0 %",
                                   font=ctk.CTkFont("Segoe UI", 10),
                                   text_color=th["text_dim"])
        _pct_label.pack(anchor="e")

        # Frame 3 — Done
        ctk.CTkLabel(frame3,
                     image=icons.icon("circle-check", 20, "#22c55e"),
                     text="  Aktualizace stažena!",
                     compound="left",
                     font=ctk.CTkFont("Segoe UI", 17, "bold"),
                     text_color="#22c55e").pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(frame3,
                     text=f"Verze v{latest} je připravena.\n"
                          "Po kliknutí na 'Restartovat' se aplikace zavře\n"
                          "a automaticky nahradí sebe novou verzí.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=th["text_dim"], justify="left").pack(anchor="w", pady=(0, 20))

        _new_exe_path = [None]

        def _restart():
            if _new_exe_path[0]:
                apply_update(_new_exe_path[0])
            d.destroy()
            self.destroy()

        ctk.CTkButton(frame3,
                      image=icons.icon("arrows-rotate", 16, "#ffffff"),
                      text=" Restartovat a nainstalovat",
                      compound="left",
                      fg_color="#22c55e", hover_color="#16a34a",
                      font=ctk.CTkFont("Segoe UI", 13, "bold"), height=44,
                      command=_restart).pack(fill="x")

        # ── Download logic ────────────────────────────────────────────────────
        def _start_download():
            # Only attempt direct download if URL points to a .exe file
            url = download_url.strip() if download_url else ""
            if not url or not url.lower().endswith(".exe"):
                # Fallback: open GitHub releases page in browser
                open_release_page()
                d.destroy()
                return
            _show(frame2)

            def _on_progress(pct: float):
                # Called on main thread via d.after() — update UI directly
                _progress_bar.set(pct)
                _pct_label.configure(text=f"{int(pct * 100)} %")
                _dl_status.configure(text=f"Stahování: {int(pct * 100)} %")

            def _on_done(success: bool, path_or_error: str):
                if success:
                    _new_exe_path[0] = path_or_error
                    _show(frame3)
                else:
                    _dl_status.configure(
                        text=f"Chyba stahování: {path_or_error[:120]}")
                    _progress_bar.configure(progress_color="#ef4444")

            download_update(
                url,
                version=latest,
                progress_callback=lambda p: d.after(0, _on_progress, p),
                done_callback=lambda s, v: d.after(0, _on_done, s, v),
            )

        _show(frame1)


class _LogoutDialog(ctk.CTkToplevel):
    def __init__(self, parent, theme: dict, user: str):
        super().__init__(parent)
        self.result = None
        self.title(t("logout") + "?")
        self.geometry("360x180")
        self.configure(fg_color=theme["content_bg"])
        self.grab_set()

        ctk.CTkLabel(self, text=f"{t('logged_in_as', user=user or '?')}",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=theme["text"]).pack(pady=(24, 8), padx=20, anchor="w")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=16)

        ctk.CTkButton(row,
                      image=icons.icon("right-from-bracket", 16, "#ffffff"),
                      text=" " + t("logout"),
                      compound="left",
                      fg_color="#8b2020", hover_color="#6b1818",
                      height=40, command=self._logout
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(row, text=t("cancel"),
                      fg_color=theme["secondary"], height=40,
                      command=self.destroy).pack(side="left", width=100)

    def _logout(self):
        self.result = "logout"
        self.destroy()
