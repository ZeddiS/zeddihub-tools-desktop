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
from .updater import check_for_update, CURRENT_VERSION
from .locale import t, get_lang, set_lang, init as locale_init, load_settings, save_settings

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
ICON_PATH = ASSETS_DIR / "icon.ico"
LOGO_ICON_PATH = ASSETS_DIR / "logo_icon.png"

SIDEBAR_W = 240
HEADER_H = 54

# Section definitions: (section_id, label, icon, game, items)
# items: [(nav_id, label, icon, requires_auth), ...]
NAV_SECTIONS = [
    ("home",     None,    "🏠", None,   None, False),   # top-level item, no section
    ("pc_tools", None,    "💻", None,   None, False),   # top-level item
    ("sec_cs2",  "CS2",   "🎯", "cs2",  [
        ("cs2_player",  "Hráčské nástroje",  "👤", False),
        ("cs2_server",  "Serverové nástroje", "🖥", True),
        ("cs2_keybind", "Keybind Generátor",  "⌨", False),
    ], None),
    ("sec_csgo", "CS:GO", "🎮", "csgo", [
        ("csgo_player",  "Hráčské nástroje",  "👤", False),
        ("csgo_server",  "Serverové nástroje", "🖥", True),
        ("csgo_keybind", "Keybind Generátor",  "⌨", False),
    ], None),
    ("sec_rust", "Rust",  "🦀", "rust", [
        ("rust_player",  "Hráčské nástroje",  "👤", False),
        ("rust_server",  "Serverové nástroje", "🖥", True),
        ("rust_keybind", "Keybind Generátor",  "⌨", False),
    ], None),
    ("sec_translator", "Translator", "🌍", None, [
        ("translator", "Translator", "🌍", False),
    ], None),
    ("sec_tools", "Nástroje", "🔗", None, [
        ("links", "Odkazy a Klienti", "🔗", False),
    ], None),
]

# Map nav_id -> game for theme switching
NAV_GAME_MAP = {
    "cs2_player": "cs2", "cs2_server": "cs2", "cs2_keybind": "cs2",
    "csgo_player": "csgo", "csgo_server": "csgo", "csgo_keybind": "csgo",
    "rust_player": "rust", "rust_server": "rust", "rust_keybind": "rust",
    "home": "default", "pc_tools": "default", "translator": "default",
    "links": "default", "settings": "default",
}

# nav_ids that show NO game badge in header
NO_BADGE_IDS = {"home", "pc_tools", "translator", "links", "settings"}


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
        ctk.CTkLabel(tab, text="🔒  " + t("login_title"),
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

        ctk.CTkButton(btn_row, text="🔓 " + t("login_btn"),
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"), height=38,
                      command=self._login).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_row, text=t("cancel"),
                      fg_color=th["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 12), height=38,
                      command=self.destroy).pack(side="left", width=100)

    def _build_register_tab(self, tab, th):
        ctk.CTkLabel(tab, text="📋  " + t("register"),
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=th["primary"]).pack(pady=(20, 8), padx=20, anchor="w")

        info_frame = ctk.CTkFrame(tab, fg_color=th["card_bg"], corner_radius=8)
        info_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(info_frame,
                     text="Registrace není momentálně dostupná.\n\nPro přístup kontaktujte administrátora\nna Discordu nebo webu ZeddiS.xyz.",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=th["text_dim"],
                     justify="left").pack(padx=16, pady=16, anchor="w")

        ctk.CTkButton(info_frame, text="💬 Otevřít Discord → dsc.gg/zeddihub",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 12), height=36,
                      command=lambda: webbrowser.open("https://dsc.gg/zeddihub")
                      ).pack(padx=16, pady=(0, 8), fill="x")

        ctk.CTkButton(info_frame, text="🌐 ZeddiS.xyz",
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
                if self._on_success:
                    self.after(0, self._on_success)
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

        self._setup_window()
        self._setup_icon()
        self._build_layout()
        self._navigate("home")

        # Check for updates in background
        check_for_update(callback=self._on_update_check)

        # Try auto-login from saved credentials
        saved = load_credentials()
        if saved:
            verify_access(saved[0], saved[1],
                          callback=lambda s, m: self.after(100, self._update_auth_ui) if s else None)

    def _setup_window(self):
        self.title("ZeddiHub Tools")
        w, h = 1280, 820
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(960, 640)
        ctk.set_appearance_mode("dark")
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
        self._main = ctk.CTkFrame(self, fg_color="#0c0c0c", corner_radius=0)
        self._main.pack(fill="both", expand=True)

        # Header
        self._header = ctk.CTkFrame(self._main, fg_color="#0e0e0e", height=HEADER_H, corner_radius=0)
        self._header.pack(fill="x", side="top")
        self._header.pack_propagate(False)
        self._build_header()

        # Thin separator
        ctk.CTkFrame(self._main, fg_color="#1a1a1a", height=1, corner_radius=0).pack(fill="x")

        # Body
        body = ctk.CTkFrame(self._main, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ctk.CTkFrame(body, fg_color="#111111", width=SIDEBAR_W, corner_radius=0)
        self._sidebar.pack(fill="y", side="left")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Thin vertical separator
        ctk.CTkFrame(body, fg_color="#1a1a1a", width=1, corner_radius=0).pack(fill="y", side="left")

        # Content
        self._content_container = ctk.CTkFrame(body, fg_color="#0f0f0f", corner_radius=0)
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

        self._auth_label = ctk.CTkLabel(right, text="🔓 " + t("not_logged_in"),
                                         font=ctk.CTkFont("Segoe UI", 10),
                                         text_color="#666666")
        self._auth_label.pack(side="right", padx=8)

        self._update_label = ctk.CTkLabel(right, text="",
                                           font=ctk.CTkFont("Segoe UI", 10),
                                           text_color="#f0a500")
        self._update_label.pack(side="right", padx=8)

    def _build_sidebar(self):
        # Top logo area
        logo_area = ctk.CTkFrame(self._sidebar, fg_color="#0c0c0c", height=60, corner_radius=0)
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
                     text_color="#f0a500", justify="left"
                     ).pack(side="left", pady=12)

        ctk.CTkFrame(self._sidebar, fg_color="#222222", height=1).pack(fill="x")

        # Scrollable nav area
        self._nav_scroll = ctk.CTkScrollableFrame(
            self._sidebar, fg_color="transparent",
            scrollbar_button_color="#2a2a2a",
            scrollbar_button_hover_color="#333333"
        )
        self._nav_scroll.pack(fill="both", expand=True, padx=0, pady=4)

        self._build_nav_items()

        # Bottom section: settings + language
        ctk.CTkFrame(self._sidebar, fg_color="#222222", height=1).pack(fill="x", side="bottom")

        lang = get_lang()
        lang_flag = "🇨🇿" if lang == "cs" else "🇬🇧"
        lang_name = "Česky" if lang == "cs" else "English"
        self._lang_btn = ctk.CTkButton(
            self._sidebar,
            text=f"{lang_flag} {lang_name}",
            fg_color="transparent", hover_color="#1a1a1a",
            text_color="#555555", anchor="w",
            font=ctk.CTkFont("Segoe UI", 10),
            height=30,
            command=self._toggle_language
        )
        self._lang_btn.pack(fill="x", padx=4, pady=(2, 2), side="bottom")

        self._auth_btn = ctk.CTkButton(
            self._sidebar, text="🔐 " + t("login"),
            fg_color="transparent", hover_color="#1a1a1a",
            text_color="#888888", anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36, command=self._show_auth_dialog
        )
        self._auth_btn.pack(fill="x", padx=4, pady=2, side="bottom")

        self._settings_btn = ctk.CTkButton(
            self._sidebar, text="⚙  " + t("settings"),
            fg_color="transparent", hover_color="#1a1a1a",
            text_color="#aaaaaa", anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36, command=lambda: self._navigate("settings")
        )
        self._settings_btn.pack(fill="x", padx=4, pady=2, side="bottom")

    def _build_nav_items(self):
        # Load saved section states
        settings = load_settings()
        saved_states = settings.get("sidebar_sections", {})

        for entry in NAV_SECTIONS:
            if len(entry) == 6:
                sec_id, label, icon, game, children, _ = entry
            else:
                continue

            if children is None:
                # Top-level nav button (home, pc_tools)
                nav_id = sec_id
                display_label = {"home": t("home"), "pc_tools": t("pc_tools")}.get(nav_id, nav_id)
                btn = ctk.CTkButton(
                    self._nav_scroll,
                    text=f"  {icon}  {display_label}",
                    fg_color="transparent",
                    hover_color="#1a1a1a",
                    text_color="#cccccc",
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 12),
                    height=38,
                    corner_radius=6,
                    command=lambda nid=nav_id: self._navigate(nid)
                )
                btn.pack(fill="x", padx=6, pady=1)
                self._nav_buttons[nav_id] = btn
            else:
                # Section with children
                # Default: cs2 expanded, others collapsed
                default_expanded = (sec_id == "sec_cs2")
                is_expanded = saved_states.get(sec_id, default_expanded)
                self._section_states[sec_id] = is_expanded

                arrow = "▼" if is_expanded else "▶"
                section_btn = ctk.CTkButton(
                    self._nav_scroll,
                    text=f"  {icon}  {label}  {arrow}",
                    fg_color="transparent",
                    hover_color="#1a1a1a",
                    text_color="#888888",
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 11, "bold"),
                    height=34,
                    corner_radius=4,
                    command=lambda sid=sec_id: self._toggle_section(sid)
                )
                section_btn.pack(fill="x", padx=4, pady=(6, 1))
                self._section_btns[sec_id] = section_btn

                # Children frame
                children_frame = ctk.CTkFrame(self._nav_scroll, fg_color="transparent")
                self._section_frames[sec_id] = children_frame

                if is_expanded:
                    children_frame.pack(fill="x", padx=0, pady=0)
                # else: don't pack (hidden)

                for nav_id, child_label, child_icon, requires_auth in children:
                    locked = requires_auth and not is_authenticated()
                    lock_suffix = " 🔒" if locked else ""
                    tc = "#555555" if locked else "#cccccc"
                    fg = "#161616" if locked else "transparent"

                    btn = ctk.CTkButton(
                        children_frame,
                        text=f"    {child_icon}  {child_label}{lock_suffix}",
                        fg_color=fg,
                        hover_color="#1a1a1a",
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
        self._section_states[sec_id] = new_state

        # Update arrow on button
        btn = self._section_btns.get(sec_id)
        if btn:
            text = btn.cget("text")
            if new_state:
                text = text.replace("▶", "▼")
            else:
                text = text.replace("▼", "▶")
            btn.configure(text=text)

        frame = self._section_frames.get(sec_id)
        if frame:
            if new_state:
                frame.pack(fill="x", padx=0, pady=0)
            else:
                frame.pack_forget()

        # Save state
        settings = load_settings()
        if "sidebar_sections" not in settings:
            settings["sidebar_sections"] = {}
        settings["sidebar_sections"][sec_id] = new_state
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
        for nid, btn in self._nav_buttons.items():
            nid_game = NAV_GAME_MAP.get(nid, "default")
            th = get_theme(nid_game)
            if nid == nav_id:
                btn.configure(fg_color=th["primary"], text_color="#ffffff",
                              hover_color=th["primary_hover"])
            else:
                # Preserve lock styling
                locked_text = "🔒" in btn.cget("text")
                tc = "#555555" if locked_text else "#cccccc"
                fg = "#161616" if locked_text else "transparent"
                btn.configure(fg_color=fg, text_color=tc, hover_color="#1a1a1a")

        # Update settings button highlight
        if nav_id == "settings":
            self._settings_btn.configure(fg_color=get_theme("default")["primary"],
                                          text_color="#ffffff")
        else:
            self._settings_btn.configure(fg_color="transparent", text_color="#aaaaaa")

        self._show_panel(nav_id)

    def _apply_theme(self):
        th = get_theme(self._current_game)
        self._content_container.configure(fg_color=th["content_bg"])
        self._sidebar.configure(fg_color=th["sidebar_bg"])
        self._header.configure(fg_color=th.get("header_bg", "#0e0e0e"))

    def _show_panel(self, nav_id: str):
        if self._current_panel:
            self._current_panel.destroy()
            self._current_panel = None

        th = get_theme(self._current_game)
        container = self._content_container

        # Lazy imports to avoid circular deps
        panel = None
        if nav_id == "home":
            from .panels.home import HomePanel
            panel = HomePanel(container, theme=get_theme("default"), nav_callback=self._navigate)
        elif nav_id == "pc_tools":
            from .panels.pc_tools import PCToolsPanel
            panel = PCToolsPanel(container, theme=get_theme("default"))
        elif nav_id == "settings":
            from .panels.settings import SettingsPanel
            panel = SettingsPanel(container, theme=get_theme("default"),
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
        elif nav_id == "translator":
            from .panels.translator import TranslatorPanel
            panel = TranslatorPanel(container, theme=get_theme("default"))
        elif nav_id == "links":
            from .panels.links import LinksPanel
            panel = LinksPanel(container, theme=get_theme("default"))

        if panel:
            panel.pack(fill="both", expand=True)
            self._current_panel = panel

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
                text=f"🔓 {user}", text_color="#4ade80")
            self._auth_btn.configure(
                text=f"✓ {t('logged_in_as', user=user)}", text_color="#4ade80")

            # Unlock locked nav items
            for entry in NAV_SECTIONS:
                if len(entry) < 6:
                    continue
                sec_id, label, icon, game, children, _ = entry
                if children is None:
                    continue
                for nav_id, child_label, child_icon, requires_auth in children:
                    if requires_auth and nav_id in self._nav_buttons:
                        btn = self._nav_buttons[nav_id]
                        # Remove lock icon, restore normal styling
                        new_text = f"    {child_icon}  {child_label}"
                        # If currently selected, keep primary color; else normal
                        if nav_id == self._current_nav_id:
                            th = get_theme(NAV_GAME_MAP.get(nav_id, "default"))
                            btn.configure(text=new_text, fg_color=th["primary"],
                                         text_color="#ffffff")
                        else:
                            btn.configure(text=new_text, fg_color="transparent",
                                         text_color="#cccccc")
        else:
            self._auth_label.configure(text="🔓 " + t("not_logged_in"), text_color="#666666")
            self._auth_btn.configure(text="🔐 " + t("login"), text_color="#888888")

            # Re-lock nav items
            for entry in NAV_SECTIONS:
                if len(entry) < 6:
                    continue
                sec_id, label, icon, game, children, _ = entry
                if children is None:
                    continue
                for nav_id, child_label, child_icon, requires_auth in children:
                    if requires_auth and nav_id in self._nav_buttons:
                        btn = self._nav_buttons[nav_id]
                        btn.configure(
                            text=f"    {child_icon}  {child_label} 🔒",
                            fg_color="#161616",
                            text_color="#555555"
                        )

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

    def _on_update_check(self, result):
        if result and result.get("available"):
            latest = result.get("latest", "?")
            self._update_label.configure(
                text=f"⬆ v{latest}",
                text_color="#fb923c",
                cursor="hand2"
            )
            self._update_label.bind("<Button-1>", lambda _: self._show_update_dialog(result))

    def _show_update_dialog(self, update_info: dict):
        th = get_theme(self._current_game)
        d = ctk.CTkToplevel(self)
        d.title(t("update_available"))
        d.geometry("460x280")
        d.configure(fg_color=th["content_bg"])
        d.grab_set()

        ctk.CTkLabel(d, text=f"⬆ {t('update_available')}: v{update_info['latest']}",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color="#fb923c").pack(pady=(20, 4), padx=24, anchor="w")
        ctk.CTkLabel(d, text=f"Aktuální verze: v{CURRENT_VERSION}",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=th["text_dim"]
                     ).pack(padx=24, anchor="w")

        btn_row = ctk.CTkFrame(d, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=20)

        ctk.CTkButton(btn_row, text="📥 " + t("download") + " / GitHub",
                      fg_color="#fb923c", hover_color="#e07b20",
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=40,
                      command=lambda: (webbrowser.open(
                          "https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"),
                          d.destroy())
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_row, text=t("later"),
                      fg_color=th["secondary"], height=40,
                      command=d.destroy).pack(side="left", width=100)


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

        ctk.CTkButton(row, text="🔒 " + t("logout"),
                      fg_color="#8b2020", hover_color="#6b1818",
                      height=40, command=self._logout
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(row, text=t("cancel"),
                      fg_color=theme["secondary"], height=40,
                      command=self.destroy).pack(side="left", width=100)

    def _logout(self):
        self.result = "logout"
        self.destroy()
