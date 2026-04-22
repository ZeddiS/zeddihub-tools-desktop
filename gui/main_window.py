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
from .auth import is_authenticated, load_credentials, verify_access, save_credentials, clear_credentials, logout, get_current_user, is_admin, resume_session, register as auth_register
from . import external_tools
from .updater import check_for_update, download_update, apply_update, open_release_page, CURRENT_VERSION
from .locale import t, get_lang, set_lang, init as locale_init, load_settings, save_settings
from . import icons
from . import telemetry
from .widgets import (
    make_button,
    make_entry,
    make_divider,
    make_page_title,
    make_section_title,
    make_card,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo2.png"          # header / sidebar logo
ICON_PATH = ASSETS_DIR / "web_favicon.ico"    # window + tray icon

SIDEBAR_W = 244
HEADER_H = 64

# Section definitions: (section_id, label, fa_icon, game, items)
# items: [(nav_id, label, fa_icon, requires_auth), ...]
NAV_SECTIONS = [
    ("home",     None,    "house",        None,   None, False),
    # v1.7.5: Utility rozděleny do 4 samostatných sekcí podle UX zpětné vazby
    ("sec_system", "nav_system_section", "laptop", None, [
        ("pc_sysinfo",     "nav_pc_sysinfo",     "laptop",               False),
        ("pc_nettools",    "nav_pc_nettools",    "tower-broadcast",      False),
        ("pc_utility",     "nav_pc_utility",     "screwdriver-wrench",   False),
        ("pc_gameopt",     "nav_pc_gameopt",     "gamepad",              False),
        ("pc_advanced",    "nav_pc_advanced",    "shield-halved",        False),
    ], None),
    ("sec_timers", "nav_timers_section", "stopwatch", None, [
        ("timers_stopky",   "nav_stopky",    "stopwatch",   False),
        ("timers_odpocet",  "nav_odpocet",   "hourglass-half", False),
        ("timers_casovac",  "nav_casovac",   "bell",        False),
    ], None),
    ("sec_macros", "nav_macros_section", "wand-magic-sparkles", None, [
        ("macros_soon",   "nav_macros_soon",   "hourglass-half", False),
    ], None),
    ("sec_processes", "nav_processes_section", "list-check", None, [
        ("processes_list",   "nav_processes_list",  "list",  False),
    ], None),
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
    # v2.1.0: Game Tools split into 4 panels
    ("sec_game_tools", "game_tools_section", "gamepad", None, [
        ("translator",      "translator",      "globe",           False),
        ("sensitivity",     "nav_sensitivity", "crosshairs",      False),
        ("edpi",            "nav_edpi",        "gauge",           False),
        ("ping_tester",     "nav_ping_tester", "tower-broadcast", False),
    ], None),
    # v2.1.0: "Ostatní" section removed — server_updater was moved to the
    # downloadable modules catalog (admin-only) per user request.
]

# Map nav_id -> game for theme switching
NAV_GAME_MAP = {
    "cs2_player": "cs2", "cs2_server": "cs2", "cs2_keybind": "cs2",
    "csgo_player": "csgo", "csgo_server": "csgo", "csgo_keybind": "csgo",
    "rust_player": "rust", "rust_server": "rust", "rust_keybind": "rust",
    "home": "default", "pc_tools": "default", "translator": "default",
    "game_tools": "default",
    "sensitivity": "default", "edpi": "default", "ping_tester": "default",
    "links": "default", "settings": "default", "watchdog": "default",
    "uploader": "default", "about": "default",
    "tools_download": "default",
    "news": "default",
    "pc_sysinfo": "default", "pc_nettools": "default",
    "pc_utility": "default", "pc_gameopt": "default", "pc_advanced": "default",
    # v1.7.5
    "timers_stopky": "default", "timers_odpocet": "default", "timers_casovac": "default",
    "macros_soon": "default",
    "processes_list": "default",
    "apps_catalog": "default",
}

# nav_ids that show NO game badge in header
NO_BADGE_IDS = {"home", "pc_tools", "translator", "game_tools", "links",
                "settings", "watchdog", "uploader", "about", "news",
                "sensitivity", "edpi", "ping_tester", "tools_download",
                "pc_sysinfo", "pc_nettools", "pc_utility",
                "pc_gameopt", "pc_advanced",
                # v1.7.5
                "timers_stopky", "timers_odpocet", "timers_casovac",
                "macros_soon", "processes_list", "apps_catalog"}


def _fade_in_toplevel(win, duration_ms: int = 160):
    """Fade a CTkToplevel in from alpha 0 → 1 over ~duration_ms.
    Silently no-ops on platforms where `-alpha` isn't supported."""
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        return
    frames = max(1, duration_ms // 16)
    step = 1.0 / frames

    def _tick(a: float):
        try:
            if not win.winfo_exists():
                return
            win.attributes("-alpha", min(a, 1.0))
        except Exception:
            return
        if a < 1.0:
            win.after(16, lambda: _tick(a + step))

    win.after(10, lambda: _tick(step))


class AuthDialog(ctk.CTkFrame):
    """Centered in-window login overlay for server tools access.

    Renders as a dimmed backdrop + centered card inside the main window
    instead of a separate Toplevel. Dismissed via Esc, × button, or by
    clicking the backdrop outside the card.
    """

    def __init__(self, parent, theme: dict, on_success=None, on_close=None):
        # parent is the main CTk window — we place ourselves over its full area
        super().__init__(parent, fg_color="#000000", corner_radius=0)
        self.theme = theme
        self.result = False
        self._on_success = on_success
        self._on_close = on_close
        self._parent = parent
        self._user_var = ctk.StringVar(value="")
        self._pass_var = ctk.StringVar(value="")

        # Place as full-window backdrop
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Embedded frames can't do real transparency, but we can fake a dim
        # by blending over the current content_bg instead of a solid black —
        # the underlying UI stays visually present under the backdrop.
        try:
            base = theme.get("content_bg", "#111119")
            dim = self._darken(base, 0.55)
            self.configure(fg_color=dim)
        except Exception:
            try:
                self.configure(fg_color="#0f1014")
            except Exception:
                pass

        # Build card
        self._build()

        # Load saved credentials
        saved = load_credentials()
        if saved:
            self._user_var.set(saved[0])
            self._pass_var.set(saved[1])
            self._remember_var.set(True)

        # Click on backdrop (not card) = close
        self.bind("<Button-1>", self._on_backdrop_click)
        # Esc at toplevel closes overlay
        try:
            top = self.winfo_toplevel()
            self._esc_binding = top.bind("<Escape>", lambda _e: self._safe_close(), add="+")
        except Exception:
            self._esc_binding = None

        # Focus into username entry shortly after mount
        self.after(80, self._focus_first_entry)

    @staticmethod
    def _darken(hex_color: str, factor: float) -> str:
        """Multiply RGB by (1-factor). factor in [0..1]."""
        try:
            c = hex_color.lstrip("#")
            r = int(c[0:2], 16); g = int(c[2:4], 16); b = int(c[4:6], 16)
            k = max(0.0, 1.0 - factor)
            r = int(r * k); g = int(g * k); b = int(b * k)
            return "#%02x%02x%02x" % (r, g, b)
        except Exception:
            return "#0f1014"

    def _focus_first_entry(self):
        try:
            self._user_entry.focus_set()
        except Exception:
            pass

    def _on_backdrop_click(self, event):
        # Only dismiss if the click landed on the backdrop itself (not on
        # any child widget of the card).
        if event.widget is self:
            self._safe_close()

    def _safe_close(self):
        # Unbind escape
        try:
            if self._esc_binding is not None:
                self.winfo_toplevel().unbind("<Escape>", self._esc_binding)
        except Exception:
            pass
        cb = self._on_close
        parent = self._parent
        # Hide first so the underlying UI is visible the moment we destroy
        try:
            self.place_forget()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        # Force a repaint of the parent so the content behind shows up
        try:
            parent.update_idletasks()
        except Exception:
            pass
        if cb:
            try:
                cb()
            except Exception:
                pass

    def _build(self):
        th = self.theme

        # Centered card (fixed-ish size, pinned by .place on backdrop)
        card = ctk.CTkFrame(
            self,
            fg_color=th.get("bg", th["content_bg"]),
            border_color=th.get("divider", th.get("border", "#2a2a2a")),
            border_width=1,
            corner_radius=16,
            width=480, height=560,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)
        self._card = card

        # Swallow clicks on the card so backdrop handler doesn't fire
        card.bind("<Button-1>", lambda _e: "break")

        # Top row with close × button
        top_row = ctk.CTkFrame(card, fg_color="transparent", height=32)
        top_row.pack(fill="x", padx=16, pady=(12, 0))
        top_row.pack_propagate(False)
        ctk.CTkButton(
            top_row, text="×", width=28, height=28,
            fg_color="transparent",
            hover_color=th.get("card_hover", th["secondary"]),
            text_color=th.get("text_muted", th["text_dim"]),
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            corner_radius=8,
            command=self._safe_close,
        ).pack(side="right")

        # Root content container with generous padding (Claude-style)
        root = ctk.CTkFrame(card, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=28, pady=(4, 24))

        # Page title
        make_page_title(
            root, t("login_title"), th,
            subtitle=t("login_subtitle"),
        ).pack(fill="x", anchor="w", pady=(0, 16))

        # Tab view: Login / Register (styled via tabview defaults)
        self._tab = ctk.CTkTabview(
            root,
            fg_color="transparent",
            segmented_button_fg_color=th.get("card_bg", th["secondary"]),
            segmented_button_selected_color=th["primary"],
            segmented_button_selected_hover_color=th["primary_hover"],
            segmented_button_unselected_color=th.get("card_bg", th["secondary"]),
            segmented_button_unselected_hover_color=th.get("card_hover", th["secondary"]),
            text_color=th.get("text_strong", th["text"]),
        )
        self._tab.pack(fill="both", expand=True, padx=0, pady=0)
        self._tab.add(t("login_btn"))
        self._tab.add(t("register"))

        self._build_login_tab(self._tab.tab(t("login_btn")), th)
        self._build_register_tab(self._tab.tab(t("register")), th)

    def _build_login_tab(self, tab, th):
        # Username
        ctk.CTkLabel(
            tab, text=t("username") + " / kód",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(fill="x", pady=(12, 4), anchor="w")
        self._user_entry = make_entry(
            tab, self._user_var, th,
            placeholder="username nebo access_code",
            height=40,
        )
        self._user_entry.pack(fill="x", pady=(0, 12))

        # Password
        ctk.CTkLabel(
            tab, text=t("password") + " (prázdné pro kód)",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(fill="x", pady=(0, 4), anchor="w")
        self._pass_entry = make_entry(
            tab, self._pass_var, th,
            placeholder="heslo...",
            height=40, show="*",
        )
        self._pass_entry.pack(fill="x", pady=(0, 8))
        self._pass_entry.bind("<Return>", lambda _: self._login())

        # Remember me
        self._remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            tab, text=t("remember_me"),
            variable=self._remember_var,
            text_color=th.get("text_muted", th["text_dim"]),
            fg_color=th["primary"], hover_color=th["primary_hover"],
            border_width=2, border_color=th.get("divider", th["secondary"]),
            font=ctk.CTkFont("Segoe UI", 11),
            checkbox_height=18, checkbox_width=18,
        ).pack(anchor="w", pady=(4, 12))

        # Divider
        make_divider(tab, th).pack(fill="x", pady=(0, 14))

        # Status
        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            tab, textvariable=self.status_var,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th["warning"], anchor="w",
        ).pack(fill="x", pady=(0, 10))

        # Button row
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 0))

        make_button(
            btn_row, " " + t("login_btn"), self._login, th,
            variant="primary", accent="primary",
            height=42, width=200,
            icon=icons.icon("right-to-bracket", 16, "#ffffff"),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        make_button(
            btn_row, t("cancel"), self._safe_close, th,
            variant="ghost",
            height=42, width=100,
            font=ctk.CTkFont("Segoe UI", 12),
        ).pack(side="left")

    def _build_register_tab(self, tab, th):
        # --- Form vars --------------------------------------------------
        self._reg_user_var = ctk.StringVar(value="")
        self._reg_email_var = ctk.StringVar(value="")
        self._reg_pass_var = ctk.StringVar(value="")
        self._reg_pass2_var = ctk.StringVar(value="")

        muted = th.get("text_muted", th["text_dim"])

        # Username
        ctk.CTkLabel(
            tab, text=t("username"),
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=muted, anchor="w",
        ).pack(fill="x", pady=(12, 4), anchor="w")
        self._reg_user_entry = make_entry(
            tab, self._reg_user_var, th,
            placeholder="3–24 znaků, A–Z 0–9 . _ -",
            height=38,
        )
        self._reg_user_entry.pack(fill="x", pady=(0, 10))

        # Email
        ctk.CTkLabel(
            tab, text="Email",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=muted, anchor="w",
        ).pack(fill="x", pady=(0, 4), anchor="w")
        make_entry(
            tab, self._reg_email_var, th,
            placeholder="tvuj@email.cz",
            height=38,
        ).pack(fill="x", pady=(0, 10))

        # Password
        ctk.CTkLabel(
            tab, text=t("password") + " (min. 8 znaků)",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=muted, anchor="w",
        ).pack(fill="x", pady=(0, 4), anchor="w")
        make_entry(
            tab, self._reg_pass_var, th,
            placeholder="nové heslo",
            height=38, show="*",
        ).pack(fill="x", pady=(0, 10))

        # Password confirm
        ctk.CTkLabel(
            tab, text="Heslo znovu",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=muted, anchor="w",
        ).pack(fill="x", pady=(0, 4), anchor="w")
        pass2 = make_entry(
            tab, self._reg_pass2_var, th,
            placeholder="potvrzení hesla",
            height=38, show="*",
        )
        pass2.pack(fill="x", pady=(0, 8))
        pass2.bind("<Return>", lambda _e: self._register())

        make_divider(tab, th).pack(fill="x", pady=(4, 10))

        # Status line (reuses register-specific var)
        self.reg_status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            tab, textvariable=self.reg_status_var,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th["warning"], anchor="w",
        ).pack(fill="x", pady=(0, 8))

        # Action row
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", pady=(4, 0))

        make_button(
            row, " Vytvořit účet", self._register, th,
            variant="primary", accent="primary",
            height=42, width=200,
            icon=icons.icon("user-plus", 16, "#ffffff"),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        make_button(
            row, t("cancel"), self._safe_close, th,
            variant="ghost",
            height=42, width=100,
            font=ctk.CTkFont("Segoe UI", 12),
        ).pack(side="left")

        # Footer: "Už máš účet? Přihlásit se"
        footer = ctk.CTkFrame(tab, fg_color="transparent")
        footer.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(
            footer, text="Už máš účet?",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=muted,
        ).pack(side="left")
        link = ctk.CTkLabel(
            footer, text=" " + t("login_btn"),
            font=ctk.CTkFont("Segoe UI", 11, "underline"),
            text_color=th["primary"],
            cursor="hand2",
        )
        link.pack(side="left")
        link.bind("<Button-1>", lambda _e: self._tab.set(t("login_btn")))

    def _register(self):
        u = (self._reg_user_var.get() or "").strip()
        em = (self._reg_email_var.get() or "").strip()
        p1 = self._reg_pass_var.get() or ""
        p2 = self._reg_pass2_var.get() or ""

        if not u or not em or not p1:
            self.reg_status_var.set("Vyplňte všechna pole.")
            return
        if p1 != p2:
            self.reg_status_var.set("Hesla se neshodují.")
            return
        if len(p1) < 8:
            self.reg_status_var.set("Heslo musí mít alespoň 8 znaků.")
            return

        self.reg_status_var.set("Vytvářím účet...")

        def on_done(ok: bool, msg: str):
            if ok:
                # Registration also logs the user in — persist session and
                # close the overlay the same way /login does.
                self.result = True
                from . import telemetry as _telem
                _telem.on_login(u)
                parent = self._parent
                cb = self._on_success
                self._safe_close()
                if cb and parent is not None:
                    try:
                        parent.after(0, cb)
                    except Exception:
                        try:
                            cb()
                        except Exception:
                            pass
            else:
                try:
                    self.reg_status_var.set(f"✗ {msg}")
                except Exception:
                    pass

        def _dispatch(s, m):
            try:
                if self.winfo_exists():
                    self.after(0, on_done, s, m)
            except Exception:
                pass

        auth_register(u, em, p1, callback=_dispatch)

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
                # Capture parent + callback BEFORE destroying the overlay —
                # `self.master` / `self.after` are unusable once the widget
                # has been torn down.
                parent = self._parent
                cb = self._on_success
                self._safe_close()
                if cb and parent is not None:
                    try:
                        parent.after(0, cb)
                    except Exception:
                        try:
                            cb()
                        except Exception:
                            pass
            else:
                try:
                    self.status_var.set(f"✗ {msg}")
                except Exception:
                    pass

        # Guard the bounce-back — if the overlay was closed before verify_access
        # finishes, `self.after` would explode on a dead widget.
        def _dispatch(s, m):
            try:
                if self.winfo_exists():
                    self.after(0, on_result, s, m)
            except Exception:
                pass
        verify_access(user, pw, callback=_dispatch)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # CRITICAL: hide window IMMEDIATELY to prevent any paint flash.
        # Must be the first thing after super().__init__() — before any
        # widget is created. Order: alpha=0 first, then withdraw.
        try:
            self.attributes("-alpha", 0.0)
            self.withdraw()
        except Exception:
            pass

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
        # Module-update tracking (filled by background thread)
        self._updatable_slugs: dict[str, str] = {}  # slug -> newest_version
        self._module_update_toast = None

        icons.preload()
        self._setup_window()
        self._setup_icon()
        self._build_layout()
        self._navigate("home")

        # Reveal window with a short fade-in once the layout is painted.
        self.after(10, self._reveal_with_fade)

        # Check for updates in background (callback safely scheduled on main thread)
        check_for_update(callback=lambda r: self.after(0, self._on_update_check, r))

        # Try auto-login from saved session (token → /me; falls back to
        # saved password → /login if token expired; then legacy auth.json).
        resume_session(callback=lambda s, m: self.after(100, self._update_auth_ui) if s else None)

        # Telemetry: launch event (fire after a short delay so UI is ready)
        self.after(2000, lambda: telemetry.on_launch(get_current_user()))

        # Check installed modules for new versions in background
        self.after(1500, self._check_module_updates_bg)

        # System tray
        self._tray = None
        self.after(500, self._start_tray)
        self.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

        # N-03: global keyboard shortcuts
        self._fullscreen = False
        self._bound_shortcuts: list = []
        self._apply_shortcut_bindings()

    def _apply_shortcut_bindings(self):
        """N-03: wire or re-wire global shortcuts based on user preference."""
        # Unbind previous
        for seq in list(getattr(self, "_bound_shortcuts", [])):
            try:
                self.unbind_all(seq)
            except Exception:
                pass
        self._bound_shortcuts = []

        if not load_settings().get("shortcuts_enabled", True):
            return

        bindings = [
            ("<Control-Key-1>", lambda e: self._navigate("home")),
            ("<Control-Key-2>", lambda e: self._navigate("pc_tools")),
            ("<Control-Key-3>", lambda e: self._navigate("settings")),
            ("<Control-Key-4>", lambda e: self._navigate("links")),
            ("<F5>",            lambda e: self._show_panel(self._current_nav_id)),
            ("<Control-q>",     lambda e: self._quit_app()),
            ("<Control-Q>",     lambda e: self._quit_app()),
            ("<Control-m>",     lambda e: self._minimize_to_tray()),
            ("<Control-M>",     lambda e: self._minimize_to_tray()),
            ("<F11>",           lambda e: self._toggle_fullscreen()),
            ("<F1>",            lambda e: self._show_shortcuts_help()),
        ]
        for seq, fn in bindings:
            try:
                self.bind_all(seq, fn)
                self._bound_shortcuts.append(seq)
            except Exception:
                pass

    def _toggle_fullscreen(self):
        try:
            self._fullscreen = not self._fullscreen
            self.attributes("-fullscreen", self._fullscreen)
        except Exception:
            pass

    def _show_shortcuts_help(self):
        """F1: show a small keybindings help popup."""
        th = self._get_current_theme()
        d = ctk.CTkToplevel(self)
        d.title(t("shortcuts_section"))
        d.geometry("420x360")
        d.configure(fg_color=th["content_bg"])
        d.resizable(False, False)
        try:
            d.grab_set()
        except Exception:
            pass

        ctk.CTkLabel(d, text=t("shortcuts_section"),
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=th["primary"]).pack(pady=(16, 4))
        ctk.CTkLabel(d, text=t("shortcuts_hint"),
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=th["text_dim"]).pack(pady=(0, 10))

        rows = [
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
        body = ctk.CTkFrame(d, fg_color=th["card_bg"], corner_radius=6)
        body.pack(fill="x", padx=20, pady=4)
        for key, desc in rows:
            r = ctk.CTkFrame(body, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(r, text=key, width=80,
                         font=ctk.CTkFont("Consolas", 11, "bold"),
                         text_color=th["primary"], anchor="w"
                         ).pack(side="left")
            ctk.CTkLabel(r, text=desc,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=th["text"]).pack(side="left", padx=(10, 0))

        ctk.CTkButton(d, text=t("close"),
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=d.destroy).pack(pady=(14, 16))

    def _reveal_with_fade(self, duration_ms: int = 140):
        """Fade the main window in from alpha 0 → 1. Hides the Win11 black
        flash by forcing a full paint BEFORE the window becomes visible."""
        try:
            # Pre-paint while still at alpha 0 and withdrawn
            self.attributes("-alpha", 0.0)
            self.update_idletasks()
            self.deiconify()
            self.update_idletasks()
            self.lift()
        except Exception:
            pass

        steps = max(5, duration_ms // 16)
        inc = 1.0 / steps

        def _step(alpha: float):
            try:
                eased = 1.0 - (1.0 - alpha) * (1.0 - alpha)
                self.attributes("-alpha", min(eased, 1.0))
            except Exception:
                return
            if alpha < 1.0:
                self.after(16, lambda: _step(min(alpha + inc, 1.0)))

        _step(inc)

    def show_with_fade(self):
        """Public entrypoint used by tray / restore paths."""
        try:
            self.state("normal")
        except Exception:
            pass
        self._reveal_with_fade(duration_ms=140)
        try:
            self.focus_force()
        except Exception:
            pass

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
        for png_path in [LOGO_PATH]:
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

        # Thin separator — subtle Claude-app style divider
        self._header_sep = ctk.CTkFrame(self._main, fg_color=th.get("divider", th["border"]), height=1, corner_radius=0)
        self._header_sep.pack(fill="x")

        # Body
        body = ctk.CTkFrame(self._main, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ctk.CTkFrame(body, fg_color=th["sidebar_bg"], width=SIDEBAR_W, corner_radius=0)
        self._sidebar.pack(fill="y", side="left")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Thin vertical separator — subtle divider
        self._sidebar_sep = ctk.CTkFrame(body, fg_color=th.get("divider", th["border"]), width=1, corner_radius=0)
        self._sidebar_sep.pack(fill="y", side="left")

        # Content
        self._content_container = ctk.CTkFrame(body, fg_color=th["content_bg"], corner_radius=0)
        self._content_container.pack(fill="both", expand=True, side="left")

    def _build_header(self):
        th = self._get_current_theme()
        # Left: logo + title
        left = ctk.CTkFrame(self._header, fg_color="transparent")
        left.pack(side="left", padx=18, fill="y")

        # v2.1.0: brand title lives in the sidebar — header keeps only the
        # small logo + game badge to avoid duplication.
        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((28, 28), Image.LANCZOS)
                self._header_logo = ctk.CTkImage(img, size=(28, 28))
                ctk.CTkLabel(left, image=self._header_logo, text="").pack(side="left", padx=(0, 10))
            except Exception:
                pass

        # Game badge — rounded pill, colored by active game theme
        self._game_badge = ctk.CTkLabel(
            left, text="",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=th["text_dim"],
            fg_color=th["glass"],
            corner_radius=12,
            height=24,
        )
        self._game_badge.pack(side="left", padx=(14, 0), pady=16)

        # Right: auth status + version
        right = ctk.CTkFrame(self._header, fg_color="transparent")
        right.pack(side="right", padx=18, fill="y")

        self._version_label = ctk.CTkLabel(right, text=f"v{CURRENT_VERSION}",
                                            font=ctk.CTkFont("Segoe UI", 9),
                                            text_color=th["text_muted"])
        self._version_label.pack(side="right", padx=(4, 0))

        # v1.7.5: Auth badge in header is now clickable — replaces former
        # sidebar-bottom login pill. Click → opens Login/Register dialog when
        # logged out, or a small logout menu when logged in.
        self._auth_label = ctk.CTkButton(
            right,
            image=icons.icon("lock-open", 13, th["text_dim"]),
            text=" " + t("not_logged_in"),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th["text_dim"],
            fg_color="transparent",
            hover_color=th.get("card_hover", th["secondary"]),
            border_width=0,
            height=30,
            corner_radius=10,
            cursor="hand2",
            command=self._on_header_auth_click,
        )
        self._auth_label.pack(side="right", padx=10)

        # F-13: Update badge — created with a hidden pill shape that becomes
        # visible only once _on_update_check() finds a new release.
        self._update_label = ctk.CTkLabel(
            right, text="",
            image=None,
            compound="left",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=th["primary"],
            fg_color="transparent",
            corner_radius=10,
        )
        self._update_label.pack(side="right", padx=8, pady=10)

        # Dark/light mode toggle — softer, more rounded
        self._mode_btn = ctk.CTkButton(
            right, image=icons.icon("sun", 15, th["text_dim"]), text="",
            width=34, height=30,
            corner_radius=10,
            fg_color="transparent", hover_color=th["card_hover"],
            command=self._toggle_appearance_mode
        )
        self._mode_btn.pack(side="right", padx=4)
        self._update_mode_btn()

        # N-12: "About" / "Info" tlačítko (ⓘ)
        self._about_btn = ctk.CTkButton(
            right, image=icons.icon("circle-info", 15, th["text_dim"]), text="",
            width=34, height=30,
            corner_radius=10,
            fg_color="transparent", hover_color=th["card_hover"],
            command=lambda: self._navigate("about"),
        )
        self._about_btn.pack(side="right", padx=4)

    def _build_sidebar(self):
        th = self._get_current_theme()
        nav_text = th["text"]
        nav_dim = th.get("text_muted", th["text_dim"])
        nav_hover = th.get("nav_hover", th["card_bg"])
        divider = th.get("divider", th["border"])

        # Top logo area — generous breathing room
        logo_area = ctk.CTkFrame(self._sidebar, fg_color=th["sidebar_bg"], height=80, corner_radius=0)
        logo_area.pack(fill="x")
        logo_area.pack_propagate(False)

        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((34, 34), Image.LANCZOS)
                self._sidebar_logo_img = ctk.CTkImage(img, size=(34, 34))
                ctk.CTkLabel(logo_area, image=self._sidebar_logo_img, text="").pack(
                    side="left", padx=(16, 10), pady=22)
            except Exception:
                pass

        ctk.CTkLabel(logo_area, text="ZeddiHub\nTools",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=th.get("text_strong", th["text"]), justify="left"
                     ).pack(side="left", pady=22)

        ctk.CTkFrame(self._sidebar, fg_color=divider, height=1).pack(fill="x")

        # Scrollable nav area
        self._nav_scroll = ctk.CTkScrollableFrame(
            self._sidebar, fg_color="transparent",
            scrollbar_button_color=divider,
            scrollbar_button_hover_color=th["secondary"]
        )
        self._nav_scroll.pack(fill="both", expand=True, padx=0, pady=6)

        self._build_nav_items()

        # Bottom section: settings + language
        ctk.CTkFrame(self._sidebar, fg_color=divider, height=1).pack(fill="x", side="bottom")

        lang = get_lang()
        lang_flag = "🇨🇿" if lang == "cs" else "🇬🇧"
        lang_name = "Česky" if lang == "cs" else "English"
        self._lang_btn = ctk.CTkButton(
            self._sidebar,
            text=f"{lang_flag} {lang_name}",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_dim, anchor="w",
            font=ctk.CTkFont("Segoe UI", 10),
            height=32,
            corner_radius=8,
            border_width=0,
            command=self._toggle_language
        )
        self._lang_btn.pack(fill="x", padx=10, pady=(4, 6), side="bottom")

        # v1.7.5: Auth pill removed from sidebar — moved to header.

        self._settings_btn = ctk.CTkButton(
            self._sidebar,
            image=icons.icon("gear", 15, nav_dim),
            text="  " + t("settings"),
            compound="left",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_text, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36,
            corner_radius=8,
            border_width=0,
            command=lambda: self._navigate("settings")
        )
        self._settings_btn.pack(fill="x", padx=10, pady=1, side="bottom")

        self._links_btn = ctk.CTkButton(
            self._sidebar,
            image=icons.icon("link", 15, nav_dim),
            text="  " + t("links"),
            compound="left",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_text, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36,
            corner_radius=8,
            border_width=0,
            command=lambda: self._navigate("links")
        )
        self._links_btn.pack(fill="x", padx=10, pady=1, side="bottom")

        # v1.7.5: "Aplikace" button above "Odkazy" — catalog of external
        # apps/webs/downloads. Panel arrives in v1.7.7; for now the button
        # navigates to a placeholder that explains the feature is coming.
        self._apps_btn = ctk.CTkButton(
            self._sidebar,
            image=icons.icon("grid", 15, nav_dim),
            text="  " + t("apps_catalog"),
            compound="left",
            fg_color="transparent", hover_color=nav_hover,
            text_color=nav_text, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11),
            height=36,
            corner_radius=8,
            border_width=0,
            command=lambda: self._navigate("apps_catalog")
        )
        self._apps_btn.pack(fill="x", padx=10, pady=1, side="bottom")

    def _rebuild_nav_items(self):
        """Destroy and re-render sidebar nav items — used on auth state change
        so locked/unlocked items can appear/disappear cleanly."""
        try:
            for child in list(self._nav_scroll.winfo_children()):
                child.destroy()
        except Exception:
            pass
        self._nav_buttons = {}
        self._section_btns = {}
        self._section_frames = {}
        self._locked_navs = set()
        # _build_nav_items already calls _build_external_tools_section at its
        # tail — never call it a second time here (that caused duplicate
        # "Ostatní nástroje" sections after login).
        self._build_nav_items()

    def _build_nav_items(self):
        th = self._get_current_theme()
        nav_text = th["text"]
        nav_dim = th.get("text_muted", th["text_dim"])
        nav_dim2 = th["text_dark"]
        nav_hover = th.get("nav_hover", th["card_bg"])
        divider_color = th.get("divider", th.get("border", "#2a2a3a"))

        def _pack_divider(parent=self._nav_scroll):
            tk.Frame(parent, height=1, bg=divider_color,
                     bd=0, highlightthickness=0).pack(
                fill="x", padx=14, pady=(8, 0))

        # Load saved section states
        settings = load_settings()
        saved_states = settings.get("sidebar_sections", {})

        first_rendered = False
        for entry in NAV_SECTIONS:
            if len(entry) == 6:
                sec_id, label, icon, game, children, _ = entry
            else:
                continue

            # Skip section if all children require auth and user isn't authenticated
            if children is not None:
                _visible = [c for c in children
                            if not (len(c) >= 4 and c[3] and not is_authenticated())]
                if not _visible:
                    continue

            if first_rendered:
                _pack_divider()
            first_rendered = True

            if children is None:
                # Top-level nav button (home, pc_tools, watchdog)
                nav_id = sec_id
                display_label = {
                    "home":       t("home"),
                    "pc_tools":   t("pc_tools"),
                    "game_tools": t("game_tools"),
                }.get(nav_id, nav_id)
                btn = ctk.CTkButton(
                    self._nav_scroll,
                    image=icons.icon(icon, 16, nav_dim),
                    text=f"  {display_label}",
                    compound="left",
                    fg_color="transparent",
                    hover_color=nav_hover,
                    text_color=nav_text,
                    border_width=0,
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 12),
                    height=36,
                    corner_radius=8,
                    command=lambda nid=nav_id: self._navigate(nid)
                )
                btn.pack(fill="x", padx=10, pady=1)
                self._nav_buttons[nav_id] = btn
            else:
                # Skip the whole section if every child is locked — v2.0.3:
                # locked tools must not be visible at all to users without access.
                visible_children = [
                    c for c in children
                    if not (len(c) >= 4 and c[3] and not is_authenticated())
                ]
                if not visible_children:
                    continue

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
                # Claude-app style: subtle tracked-caps category label, no background
                spaced_label = "\u2009".join(display_sec_label.upper())
                section_btn = ctk.CTkButton(
                    outer,
                    image=icons.icon(icon, 12, nav_dim),
                    text=f"  {spaced_label}   {arrow}",
                    compound="left",
                    fg_color="transparent",
                    hover_color=nav_hover,
                    text_color=nav_dim,
                    border_width=0,
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 10, "bold"),
                    height=30,
                    corner_radius=8,
                    command=lambda sid=sec_id: self._toggle_section(sid)
                )
                section_btn.pack(fill="x", padx=14, pady=(14, 2))
                self._section_btns[sec_id] = section_btn

                # Children frame lives inside outer — toggling it never reorders siblings
                children_frame = ctk.CTkFrame(outer, fg_color="transparent")
                self._section_frames[sec_id] = children_frame

                if is_expanded:
                    children_frame.pack(fill="x", padx=0, pady=0)

                for nav_id, child_label_key, child_icon, requires_auth in children:
                    # v2.0.3: locked items are hidden entirely, not rendered dimmed.
                    if requires_auth and not is_authenticated():
                        self._locked_navs.add(nav_id)
                        continue
                    # child_label_key is a locale key → translate it
                    child_label = t(child_label_key)
                    child_img = icons.icon(child_icon, 14, nav_text)
                    tc = nav_text
                    fg = "transparent"

                    # Premium/Admin pill for items that were locked and are
                    # now visible because the user authenticated.
                    show_pill = bool(requires_auth) and is_authenticated()
                    if show_pill:
                        # Server tools are premium features (regardless of whether
                        # the current user is admin). Pill is always "PREMIUM".
                        pill_text = "PREMIUM"
                        pill_bg = "#22c55e"
                        _cmd = lambda nid=nav_id, auth=requires_auth: self._on_nav_click(nid, auth)
                        # Row frame — hover state is propagated to the button so
                        # the entire row (including the pill area) feels active.
                        row = ctk.CTkFrame(children_frame, fg_color="transparent")
                        row.pack(fill="x", padx=10, pady=1)
                        btn = ctk.CTkButton(
                            row,
                            image=child_img,
                            text=f"   {child_label}",
                            compound="left",
                            fg_color=fg,
                            hover_color=nav_hover,
                            text_color=tc,
                            border_width=0,
                            anchor="w",
                            font=ctk.CTkFont("Segoe UI", 11),
                            height=34,
                            corner_radius=8,
                            command=_cmd,
                        )
                        btn.pack(side="left", fill="x", expand=True)
                        pill = ctk.CTkLabel(
                            row, text=pill_text,
                            font=ctk.CTkFont("Segoe UI", 8, "bold"),
                            text_color="#0a0a0a",
                            fg_color=pill_bg,
                            corner_radius=10,
                            width=56, height=18,
                            cursor="hand2",
                        )
                        pill.pack(side="right", padx=(0, 6))
                        # The pill is a CTkLabel sibling of the button and would
                        # otherwise create a dead hit-area. Forward clicks to the
                        # button so the whole row row is clickable.
                        def _pill_click(event, fn=_cmd):
                            fn()
                        pill.bind("<Button-1>", _pill_click)
                        # Also forward clicks from the transparent row gap.
                        row.bind("<Button-1>", _pill_click)
                        row.configure(cursor="hand2")
                        self._nav_buttons[nav_id] = btn
                    else:
                        btn = ctk.CTkButton(
                            children_frame,
                            image=child_img,
                            text=f"   {child_label}",
                            compound="left",
                            fg_color=fg,
                            hover_color=nav_hover,
                            text_color=tc,
                            border_width=0,
                            anchor="w",
                            font=ctk.CTkFont("Segoe UI", 11),
                            height=34,
                            corner_radius=8,
                            command=lambda nid=nav_id, auth=requires_auth: self._on_nav_click(nid, auth)
                        )
                        btn.pack(fill="x", padx=10, pady=1)
                        self._nav_buttons[nav_id] = btn

        # Admin-only "Ostatní nástroje" section (external tools)
        if first_rendered:
            _pack_divider()
        self._build_external_tools_section()

    def _build_external_tools_section(self):
        """Sidebar section for downloadable modules — catalog + installed."""
        th = self._get_current_theme()
        nav_text = th["text"]
        nav_dim = th.get("text_muted", th["text_dim"])
        nav_hover = th.get("nav_hover", th["card_bg"])

        sec_id = "sec_external_tools"
        settings = load_settings()
        saved_states = settings.get("sidebar_sections", {})
        is_expanded = saved_states.get(sec_id, False)
        self._section_states[sec_id] = is_expanded

        outer = ctk.CTkFrame(self._nav_scroll, fg_color="transparent")
        outer.pack(fill="x", padx=0, pady=0)
        self._external_section_outer = outer

        arrow = "▼" if is_expanded else "▶"
        label = t("sec_external_tools")
        spaced_label = "\u2009".join(label.upper())
        section_btn = ctk.CTkButton(
            outer,
            image=icons.icon("puzzle-piece", 12, nav_dim),
            text=f"  {spaced_label}   {arrow}",
            compound="left", fg_color="transparent", hover_color=nav_hover,
            text_color=nav_dim, border_width=0, anchor="w",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            height=30, corner_radius=8,
            command=lambda sid=sec_id: self._toggle_section(sid)
        )
        section_btn.pack(fill="x", padx=14, pady=(14, 2))
        self._section_btns[sec_id] = section_btn

        children_frame = ctk.CTkFrame(outer, fg_color="transparent")
        self._section_frames[sec_id] = children_frame
        if is_expanded:
            children_frame.pack(fill="x", padx=0, pady=0)

        # "Download Tools" entry
        btn = ctk.CTkButton(
            children_frame,
            image=icons.icon("download", 14, nav_text),
            text=f"   {t('nav_tools_download')}",
            compound="left", fg_color="transparent",
            hover_color=nav_hover, text_color=nav_text,
            border_width=0, anchor="w",
            font=ctk.CTkFont("Segoe UI", 11), height=34, corner_radius=8,
            command=lambda: self._navigate("tools_download")
        )
        btn.pack(fill="x", padx=10, pady=1)
        self._nav_buttons["tools_download"] = btn

        # Resolved installed-tool order (user-saved order, missing slugs appended)
        installed = external_tools.list_installed()
        saved_order = list(settings.get("external_tools_order", []) or [])
        installed_by_slug = {e.get("slug"): e for e in installed}
        ordered: list = []
        for s in saved_order:
            if s in installed_by_slug:
                ordered.append(installed_by_slug[s])
        for e in installed:
            if e.get("slug") not in {o.get("slug") for o in ordered}:
                ordered.append(e)

        # "Edit order" row — a small compact toggle above the installed list,
        # visible only if there is more than one installed tool.
        reorder_mode = bool(getattr(self, "_reorder_external_tools", False))
        if len(ordered) >= 2:
            edit_row = ctk.CTkFrame(children_frame, fg_color="transparent")
            edit_row.pack(fill="x", padx=10, pady=(4, 2))
            edit_label = "✓ Hotovo" if reorder_mode else "↕ Upravit pořadí"
            edit_color = th.get("primary", "#f0a500") if reorder_mode else nav_dim
            ctk.CTkButton(
                edit_row, text=edit_label,
                fg_color="transparent", hover_color=nav_hover,
                text_color=edit_color, border_width=0, anchor="w",
                font=ctk.CTkFont("Segoe UI", 10),
                height=22, corner_radius=6,
                command=lambda: self._toggle_external_tools_reorder()
            ).pack(fill="x")

        # Installed tools
        for entry in ordered:
            slug = entry.get("slug")
            icon_name = entry.get("icon", "wrench")
            has_update = slug in getattr(self, "_updatable_slugs", {})
            label_text = f"   {entry.get('name', slug)}"
            row = ctk.CTkFrame(children_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=1)

            if reorder_mode:
                # Drag handle + label only — no "open module" action while
                # reordering (clicks are repurposed for drag).
                handle_img = icons.icon("grip-lines", 12, nav_dim) if icons else None
                ebtn = ctk.CTkButton(
                    row,
                    image=handle_img,
                    text=label_text,
                    compound="left",
                    fg_color=th.get("card_bg", "#1a1a26"),
                    hover_color=th.get("card_bg", "#1a1a26"),
                    text_color=nav_text,
                    border_width=1, border_color=th.get("border", "#2a2a36"),
                    anchor="w",
                    font=ctk.CTkFont("Segoe UI", 11), height=34, corner_radius=8,
                )
                ebtn.pack(side="left", fill="x", expand=True)
                try:
                    ebtn.configure(cursor="fleur")
                except Exception:
                    pass
                self._bind_drag_reorder(ebtn, slug, children_frame)
            else:
                ebtn = ctk.CTkButton(
                    row,
                    image=icons.icon(icon_name, 14, nav_text),
                    text=label_text,
                    compound="left", fg_color="transparent",
                    hover_color=nav_hover, text_color=nav_text,
                    border_width=0, anchor="w",
                    font=ctk.CTkFont("Segoe UI", 11), height=34, corner_radius=8,
                    command=lambda s=slug: self._open_installed_module(s)
                )
                ebtn.pack(side="left", fill="x", expand=True)
                if has_update:
                    bell_lbl = ctk.CTkLabel(
                        row,
                        image=icons.icon("bell", 13, "#f0a500"),
                        text="",
                        fg_color="transparent",
                    )
                    bell_lbl.pack(side="right", padx=(0, 8))
                    bell_lbl.bind("<Button-1>", lambda _e: self._navigate("tools_download"))
                    try:
                        bell_lbl.configure(cursor="hand2")
                    except Exception:
                        pass
            self._nav_buttons[f"mod:{slug}"] = ebtn

    def _toggle_external_tools_reorder(self):
        """Flip the reorder mode and rebuild the sidebar."""
        self._reorder_external_tools = not bool(
            getattr(self, "_reorder_external_tools", False)
        )
        # Force the section to stay expanded while reordering
        try:
            settings = load_settings()
            secs = settings.setdefault("sidebar_sections", {})
            secs["sec_external_tools"] = True
            save_settings(settings)
        except Exception:
            pass
        self.refresh_external_tools_sidebar()

    def _bind_drag_reorder(self, widget, slug: str, container):
        """Attach press/motion/release bindings for drag-to-reorder."""
        state = {"start_y": 0, "moved": False}

        def _on_press(event):
            state["start_y"] = event.y_root
            state["moved"] = False
            try:
                widget.configure(border_color=self._get_current_theme().get("primary", "#f0a500"))
            except Exception:
                pass

        def _on_motion(event):
            dy = event.y_root - state["start_y"]
            if abs(dy) < 18:  # half a row
                return
            # Threshold crossed — shift this slug up or down one position
            self._shift_external_tool_order(slug, -1 if dy < 0 else +1)
            state["start_y"] = event.y_root
            state["moved"] = True

        def _on_release(_event):
            try:
                widget.configure(border_color=self._get_current_theme().get("border", "#2a2a36"))
            except Exception:
                pass

        widget.bind("<ButtonPress-1>", _on_press, add="+")
        widget.bind("<B1-Motion>", _on_motion, add="+")
        widget.bind("<ButtonRelease-1>", _on_release, add="+")

    def _shift_external_tool_order(self, slug: str, delta: int):
        """Move slug by `delta` positions in the saved order and rebuild."""
        try:
            settings = load_settings()
            installed = [e.get("slug") for e in external_tools.list_installed()]
            saved = list(settings.get("external_tools_order", []) or [])
            # Build full ordering (saved first, then remaining installed)
            full = [s for s in saved if s in installed]
            for s in installed:
                if s not in full:
                    full.append(s)
            if slug not in full:
                return
            idx = full.index(slug)
            new_idx = max(0, min(len(full) - 1, idx + delta))
            if new_idx == idx:
                return
            full.pop(idx)
            full.insert(new_idx, slug)
            settings["external_tools_order"] = full
            save_settings(settings)
            self.refresh_external_tools_sidebar()
        except Exception:
            pass

    def _open_installed_module(self, slug: str):
        """Navigate to a dynamic panel backed by an installed module."""
        self._navigate(f"mod:{slug}")

    # ── Module update detection ─────────────────────────────────────────────
    @staticmethod
    def _ver_tuple(v: str) -> tuple:
        try:
            return tuple(int(x) for x in str(v).strip().lstrip("v").split(".") if x.isdigit())
        except Exception:
            return (0,)

    def _check_module_updates_bg(self):
        """Fetch catalog in a background thread and flag installed modules
        whose version is older than the catalog version."""
        import threading

        def _worker():
            try:
                catalog = external_tools.fetch_catalog()
            except Exception:
                catalog = []
            installed = {e.get("slug"): e for e in external_tools.list_installed()}
            updatable: dict[str, str] = {}
            for item in catalog:
                slug = item.get("slug")
                if not slug or slug not in installed:
                    continue
                cat_ver = item.get("version", "0.0.0")
                inst_ver = installed[slug].get("version", "0.0.0")
                if self._ver_tuple(cat_ver) > self._ver_tuple(inst_ver):
                    updatable[slug] = cat_ver
            try:
                self.after(0, self._on_module_updates_found, updatable)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _on_module_updates_found(self, updatable: dict):
        self._updatable_slugs = updatable or {}
        if not self._updatable_slugs:
            return
        # Refresh sidebar so bells appear next to installed modules
        try:
            self.refresh_external_tools_sidebar()
        except Exception:
            pass
        # Show a toast in bottom-right corner
        try:
            self._show_module_update_toast()
        except Exception:
            pass

    def _show_module_update_toast(self):
        """Floating card bottom-right — 'N nástrojů má aktualizaci'. Auto-dismiss 8s."""
        if not self._updatable_slugs:
            return
        # Dismiss any previous
        try:
            if self._module_update_toast is not None:
                self._module_update_toast.destroy()
        except Exception:
            pass

        th = self._get_current_theme()
        n = len(self._updatable_slugs)
        first_name = None
        # Try to show first slug's pretty name from installed registry
        for e in external_tools.list_installed():
            if e.get("slug") in self._updatable_slugs:
                first_name = e.get("name", e.get("slug"))
                break

        toast = ctk.CTkFrame(
            self,
            fg_color=th.get("card_bg", "#1a1a1a"),
            border_color="#f0a500",
            border_width=1,
            corner_radius=12,
        )
        self._module_update_toast = toast

        # Header row: bell + title + close
        hdr = ctk.CTkFrame(toast, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 2))
        ctk.CTkLabel(
            hdr, image=icons.icon("bell", 16, "#f0a500"), text="",
            fg_color="transparent",
        ).pack(side="left")
        ctk.CTkLabel(
            hdr,
            text="  Dostupná aktualizace" if n == 1 else f"  Dostupné aktualizace ({n})",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=th.get("text_strong", th["text"]),
            fg_color="transparent",
        ).pack(side="left")
        ctk.CTkButton(
            hdr, text="×", width=24, height=24,
            fg_color="transparent", hover_color=th.get("card_hover", th["secondary"]),
            text_color=th.get("text_muted", th["text_dim"]),
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            corner_radius=8, command=self._dismiss_module_update_toast,
        ).pack(side="right")

        # Body text
        if n == 1 and first_name:
            body_text = f"{first_name} má novější verzi."
        else:
            body_text = f"{n} nainstalovaných nástrojů má novější verzi."
        ctk.CTkLabel(
            toast, text=body_text,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_muted", th["text_dim"]),
            fg_color="transparent", anchor="w", justify="left",
        ).pack(fill="x", padx=14, pady=(0, 8))

        # Action row
        act = ctk.CTkFrame(toast, fg_color="transparent")
        act.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkButton(
            act, text="Zobrazit", width=110, height=30,
            fg_color="#f0a500", hover_color="#d99400",
            text_color="#111111",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            corner_radius=8,
            command=self._open_updates_from_toast,
        ).pack(side="left")
        ctk.CTkButton(
            act, text="Později", width=80, height=30,
            fg_color="transparent",
            hover_color=th.get("card_hover", th["secondary"]),
            text_color=th.get("text_muted", th["text_dim"]),
            font=ctk.CTkFont("Segoe UI", 10),
            corner_radius=8,
            command=self._dismiss_module_update_toast,
        ).pack(side="left", padx=(6, 0))

        toast.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        # Auto-dismiss after 8s
        self.after(8000, self._dismiss_module_update_toast)

    def _open_updates_from_toast(self):
        self._dismiss_module_update_toast()
        self._navigate("tools_download")

    def _dismiss_module_update_toast(self):
        try:
            if self._module_update_toast is not None and self._module_update_toast.winfo_exists():
                self._module_update_toast.destroy()
        except Exception:
            pass
        self._module_update_toast = None

    def refresh_external_tools_sidebar(self):
        """Rebuild only the external tools section (called after install/uninstall)."""
        # Prune stale nav button refs — widgets inside the outer frame are
        # about to be destroyed, and leaving dangling Tcl paths in
        # _nav_buttons crashes every subsequent _navigate() call.
        stale = [nid for nid in self._nav_buttons
                 if nid == "tools_download" or nid.startswith("mod:")]
        for nid in stale:
            self._nav_buttons.pop(nid, None)

        if hasattr(self, "_external_section_outer"):
            try:
                self._external_section_outer.destroy()
            except Exception:
                pass
        self._build_external_tools_section()

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
            def _after_login():
                self._update_auth_ui()
                self._navigate(nav_id)
            AuthDialog(self, get_theme(self._current_game),
                       on_success=lambda: self.after(0, _after_login))
            return

        self._navigate(nav_id)

    def _navigate(self, nav_id: str):
        # v2.1.0: uploader is a web link, not a panel — open browser and return
        if nav_id == "uploader":
            try:
                webbrowser.open("https://zeddihub.eu/tools/uploader/")
            except Exception:
                pass
            return

        self._current_nav_id = nav_id

        # Determine game for this nav_id
        game = NAV_GAME_MAP.get(nav_id, "default")
        if game != self._current_game:
            self._current_game = game
            self._apply_theme()

        # Update header badge — every panel gets a label pill
        t_dict = get_theme(game)
        game_names = {"cs2": "Counter-Strike 2", "csgo": "CS:GO", "rust": "Rust"}
        section_labels = {
            "home": t("home"),
            "pc_tools": t("pc_tools"),
            "pc_sysinfo": t("pc_tools"),
            "pc_nettools": t("pc_tools"),
            "pc_utility": t("pc_tools"),
            "pc_gameopt": t("pc_tools"),
            "pc_advanced": t("pc_tools"),
            "game_tools": t("game_tools_section"),
            "translator": t("game_tools_section"),
            "sensitivity": t("game_tools_section"),
            "edpi": t("game_tools_section"),
            "ping_tester": t("game_tools_section"),
            "links": t("links"),
            "settings": t("settings_title"),
            "about": t("about"),
            "tools_download": t("nav_tools_download"),
            "news": t("news_title"),
            "watchdog": t("nav_watchdog"),
        }
        if nav_id and nav_id.startswith("mod:"):
            slug = nav_id[4:]
            try:
                reg = external_tools.load_registry()
                entry = reg.get("installed", {}).get(slug, {})
                label_text = entry.get("name", slug)
            except Exception:
                label_text = slug
        elif game in game_names:
            label_text = game_names[game]
        else:
            label_text = section_labels.get(nav_id, "")
        if label_text:
            self._game_badge.configure(
                text="  " + label_text + "  ",
                text_color=t_dict["primary"],
                fg_color=t_dict.get("accent_soft", t_dict["glass"]),
            )
        else:
            self._game_badge.configure(text="", fg_color="transparent")

        # Update nav button styles
        mode = ctk.get_appearance_mode().lower()
        for nid, btn in self._nav_buttons.items():
            nid_game = NAV_GAME_MAP.get(nid, "default")
            btn_th = get_theme(nid_game, mode)
            cur_th = get_theme(self._current_game, mode)
            nav_hover = cur_th.get("nav_hover", cur_th["card_bg"])
            if nid == nav_id:
                active_bg = btn_th.get("nav_active_bg", btn_th["primary"])
                active_text = btn_th.get("nav_active_text", "#ffffff")
                btn.configure(fg_color=active_bg, text_color=active_text,
                              hover_color=active_bg)
            else:
                is_locked = nid in self._locked_navs
                tc = cur_th["text_dark"] if is_locked else cur_th["text"]
                fg = cur_th["secondary"] if is_locked else "transparent"
                btn.configure(fg_color=fg, text_color=tc, hover_color=nav_hover)

        # Update settings / links button highlights — pill style
        def_th = get_theme("default", mode)
        nav_hover_def = def_th.get("nav_hover", def_th["card_bg"])
        active_bg_def = def_th.get("nav_active_bg", def_th["primary"])
        active_text_def = def_th.get("nav_active_text", "#ffffff")
        if nav_id == "settings":
            self._settings_btn.configure(fg_color=active_bg_def, text_color=active_text_def,
                                          hover_color=active_bg_def)
        else:
            self._settings_btn.configure(fg_color="transparent",
                                          text_color=def_th["text"],
                                          hover_color=nav_hover_def)

        if hasattr(self, "_links_btn"):
            if nav_id == "links":
                self._links_btn.configure(fg_color=active_bg_def, text_color=active_text_def,
                                           hover_color=active_bg_def)
            else:
                self._links_btn.configure(fg_color="transparent",
                                           text_color=def_th["text"],
                                           hover_color=nav_hover_def)

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
            self._header_sep.configure(fg_color=th.get("divider", th["border"]))
        if hasattr(self, "_sidebar_sep"):
            self._sidebar_sep.configure(fg_color=th.get("divider", th["border"]))

        # Update all nav button hover/inactive colors for new theme
        nav_text = th["text"]
        nav_dim = th["text_dark"]
        nav_hover = th.get("nav_hover", th["card_bg"])
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
            sbtn.configure(text_color=th.get("text_muted", th["text_dim"]), hover_color=nav_hover)

        # Update bottom sidebar buttons
        for attr in ("_settings_btn", "_links_btn", "_apps_btn", "_lang_btn"):
            w = getattr(self, attr, None)
            if w:
                w.configure(hover_color=nav_hover)

        # v1.8.0 "Blur" redesign — keep header widgets in sync with active theme
        try:
            if hasattr(self, "_version_label"):
                self._version_label.configure(text_color=th.get("text_muted", th["text_dim"]))
            if hasattr(self, "_auth_label"):
                self._auth_label.configure(text_color=th["text_dim"])
            if hasattr(self, "_update_label"):
                self._update_label.configure(text_color=th["primary"])
            if hasattr(self, "_game_badge"):
                self._game_badge.configure(
                    text_color=th["text_dim"],
                    fg_color=th.get("glass", th["card_bg"]),
                )
            for btn_attr in ("_mode_btn", "_about_btn"):
                b = getattr(self, btn_attr, None)
                if b:
                    b.configure(hover_color=th.get("card_hover", th["card_bg"]))
        except Exception:
            pass

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
        elif nav_id and nav_id.startswith("pc_"):
            from .panels import pc_subpanels
            _pc_map = {
                "pc_sysinfo":     pc_subpanels.PCSysInfoPanel,
                "pc_nettools":    pc_subpanels.PCNetToolsPanel,
                "pc_utility":     pc_subpanels.PCUtilityPanel,
                "pc_gameopt":     pc_subpanels.PCGameOptPanel,
                "pc_advanced":    pc_subpanels.PCAdvancedPanel,
            }
            cls = _pc_map.get(nav_id)
            if cls is not None:
                panel = cls(container, theme=_th())
        # v1.7.5: new timer panels
        elif nav_id == "timers_stopky":
            from .panels.timers import StopkyPanel
            panel = StopkyPanel(container, theme=_th())
        elif nav_id == "timers_odpocet":
            from .panels.timers import OdpocetPanel
            panel = OdpocetPanel(container, theme=_th())
        elif nav_id == "timers_casovac":
            from .panels.timers import CasovacPanel
            panel = CasovacPanel(container, theme=_th())
        # v1.7.5: processes split from PCToolsPanel
        elif nav_id == "processes_list":
            from .panels.processes import ProcessesPanel
            panel = ProcessesPanel(container, theme=_th())
        # v1.7.5: macros placeholder — real system lands in v1.7.6
        elif nav_id == "macros_soon":
            from .panels.macros_placeholder import MacrosPlaceholderPanel
            panel = MacrosPlaceholderPanel(container, theme=_th())
        # v1.7.5: apps catalog placeholder — real system lands in v1.7.7
        elif nav_id == "apps_catalog":
            from .panels.apps_placeholder import AppsPlaceholderPanel
            panel = AppsPlaceholderPanel(container, theme=_th())
        elif nav_id == "settings":
            from .panels.settings import SettingsPanel
            panel = SettingsPanel(container, theme=_th(),
                                   on_language_change=self._on_language_change,
                                   on_auth_change=self._update_auth_ui)
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
        elif nav_id == "game_tools":
            from .panels.game_tools import GameToolsPanel
            panel = GameToolsPanel(container, theme=_th())
        elif nav_id == "translator":
            from .panels.translator import TranslatorPanel
            panel = TranslatorPanel(container, theme=_th())
        elif nav_id == "sensitivity":
            from .panels.sensitivity import SensitivityPanel
            panel = SensitivityPanel(container, theme=_th())
        elif nav_id == "edpi":
            from .panels.edpi import EDPIPanel
            panel = EDPIPanel(container, theme=_th())
        elif nav_id == "ping_tester":
            from .panels.ping_tester import PingTesterPanel
            panel = PingTesterPanel(container, theme=_th())
        elif nav_id == "links":
            from .panels.links import LinksPanel
            panel = LinksPanel(container, theme=_th())
        elif nav_id == "watchdog":
            from .panels.watchdog import WatchdogPanel
            panel = WatchdogPanel(container, theme=_th())
        elif nav_id == "about":
            # N-12: O aplikaci panel
            from .panels.about import AboutPanel
            panel = AboutPanel(container, theme=_th(), nav_callback=self._navigate)
        elif nav_id == "news":
            # N-13: Novinky z GitHub Releases
            from .panels.news import NewsPanel
            panel = NewsPanel(container, theme=_th(), nav_callback=self._navigate)
        elif nav_id == "tools_download":
            from .panels.tools_download import ToolsDownloadPanel
            panel = ToolsDownloadPanel(
                container, theme=_th(),
                on_refresh_sidebar=self.refresh_external_tools_sidebar,
                on_open_module=self._open_installed_module,
            )
        elif nav_id and nav_id.startswith("mod:"):
            slug = nav_id[4:]
            try:
                cls, _name = external_tools.load_panel_class(slug)
                panel = cls(container, theme=_th(), nav_callback=self._navigate)
            except Exception as e:
                panel = ctk.CTkFrame(container, fg_color=_th().get("content_bg", "#0a0a0f"))
                ctk.CTkLabel(
                    panel,
                    text=f"Chyba načtení modulu '{slug}':\n{e}",
                    font=ctk.CTkFont("Segoe UI", 12),
                    text_color=_th().get("text", "#fff"),
                    justify="left", wraplength=520,
                ).pack(padx=24, pady=24, anchor="w")
        if panel:
            # Force a layout pass BEFORE pack so children resolve their
            # themed colors; then pack as the final atomic render.
            try:
                panel.update_idletasks()
                container.update_idletasks()
            except Exception:
                pass
            panel.pack(fill="both", expand=True)
            self._current_panel = panel
            telemetry.on_panel_open(nav_id, get_current_user())

    def _fade_in_panel(self, panel):
        """Subtle opacity-like fade on panel switch by interpolating the
        panel's fg_color from container bg → target over ~140 ms.
        Uses a tiny color easing via widget update after() calls.
        """
        try:
            target = panel.cget("fg_color")
        except Exception:
            return
        # Skip transparent panels — they'd look jumpy without a base color.
        if not target or target == "transparent":
            return

        bg = self._get_current_theme().get("content_bg", "#111119")

        def _mix(c1: str, c2: str, r: float) -> str:
            try:
                a = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
                b = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
                return "#%02x%02x%02x" % (
                    int(a[0] + (b[0] - a[0]) * r),
                    int(a[1] + (b[1] - a[1]) * r),
                    int(a[2] + (b[2] - a[2]) * r),
                )
            except Exception:
                return c2

        tgt = target if isinstance(target, str) else str(target)
        if not tgt.startswith("#") or len(tgt) != 7:
            return

        def _step(t: float):
            if not panel.winfo_exists():
                return
            try:
                panel.configure(fg_color=_mix(bg, tgt, min(t, 1.0)))
            except Exception:
                return
            if t < 1.0:
                panel.after(16, lambda: _step(t + 0.15))

        _step(0.0)

    def _open_auth_dialog(self, on_success=None):
        """N-11: Public wrapper — opens login/logout dialog with optional success callback.
        Called by HomePanel login card to sync auth state back to the header + panel.
        """
        def _combined_success():
            self.after(0, self._update_auth_ui)
            if on_success:
                self.after(0, on_success)

        if is_authenticated():
            user = get_current_user()
            dialog = _LogoutDialog(self, get_theme(self._current_game), user)
            self.wait_window(dialog)
            if dialog.result == "logout":
                logout()
                self.after(0, self._update_auth_ui)
                if on_success:
                    self.after(50, on_success)
        else:
            # In-window overlay — callback handles success; no wait_window.
            AuthDialog(self, get_theme(self._current_game),
                       on_success=_combined_success)

    def _show_auth_dialog(self):
        """Sidebar auth button.

        - Authenticated → navigate to Settings > Účet (no popup).
        - Not authenticated → open the login overlay.
        """
        if is_authenticated():
            self._navigate("settings")
            # After the panel mounts, force the Account tab to open.
            self.after(50, self._focus_settings_account_tab)
            return
        self._open_auth_dialog()

    def _on_header_auth_click(self):
        """v1.7.5: Header auth pill click handler.

        - Logged out: open Login/Register dialog (same as former sidebar pill).
        - Logged in: navigate to Settings > Account (consistent with sidebar behavior).
        """
        if is_authenticated():
            self._navigate("settings")
            self.after(50, self._focus_settings_account_tab)
            return
        self._open_auth_dialog()

    def _focus_settings_account_tab(self):
        """Flip SettingsPanel to its 'Účet' tab if it exposes a hook."""
        try:
            panel = self._current_panel
            if panel is None:
                return
            # Common hooks: switch_to_tab(name) / _tab.set(name) / set_section().
            if hasattr(panel, "switch_to_tab"):
                panel.switch_to_tab("account")
                return
            if hasattr(panel, "_tab"):
                try:
                    panel._tab.set(t("account"))
                    return
                except Exception:
                    try:
                        panel._tab.set("Účet")
                        return
                    except Exception:
                        pass
        except Exception:
            pass

    def _update_auth_ui(self):
        # v2.0.3: rebuild entire sidebar nav so locked items are hidden/shown
        # cleanly on auth state change (previously they were just re-styled).
        try:
            self._rebuild_nav_items()
        except Exception:
            pass
        # Re-apply current active-nav styling (rebuild cleared button state)
        try:
            if self._current_nav_id and self._current_nav_id in self._nav_buttons:
                th = get_theme(NAV_GAME_MAP.get(self._current_nav_id, "default"))
                self._nav_buttons[self._current_nav_id].configure(
                    fg_color=th.get("nav_active_bg", th["primary"]),
                    text_color=th.get("nav_active_text", "#ffffff"),
                )
        except Exception:
            pass
        if is_authenticated():
            user = get_current_user() or "?"
            self._auth_label.configure(
                image=icons.icon("user", 13, "#4ade80"),
                text=f" {user}", text_color="#4ade80")
        else:
            self._auth_label.configure(
                image=icons.icon("lock-open", 13, "#888888"),
                text=" " + t("not_logged_in"), text_color="#888888")

        # N-11: propagate auth state change to HomePanel login card if it is visible
        try:
            if hasattr(self, "_current_panel") and hasattr(self._current_panel, "_refresh_login_card"):
                self._current_panel._refresh_login_card()
        except Exception:
            pass

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
        """Hide window to tray on first close; show one-time info dialog.
        F-07: respektuje uživatelskou volbu 'close_behavior' (minimize/quit).
        """
        settings = load_settings()
        # F-07: pokud uživatel zvolil 'quit', rovnou ukončit aplikaci
        if settings.get("close_behavior", "minimize") == "quit":
            self._quit_app()
            return
        if self._tray is not None:
            if not settings.get("tray_close_shown", False):
                settings["tray_close_shown"] = True
                save_settings(settings)
                self._show_tray_notice()
                return  # notice has its own close/minimize buttons
            try:
                self.attributes("-alpha", 0.0)
            except Exception:
                pass
            self.withdraw()
            # F-07: volitelná tray notifikace
            try:
                if hasattr(self._tray, "show_notification"):
                    self._tray.show_notification(
                        "ZeddiHub Tools",
                        "Aplikace běží v systémové liště. Pro ukončení klikni pravým na tray ikonu.",
                    )
            except Exception:
                pass
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
        """Full shutdown: stop tray, end mainloop, destroy window, force-exit.

        Background threads (verify_access, updater, module-catalog check…)
        can keep the Python process alive after Tk is torn down, which
        manifests as 'app won't close / must kill task'. We force-exit at
        the end to make sure the process actually goes away.
        """
        try:
            if self._tray is not None:
                self._tray.stop()
        except Exception:
            pass
        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        import os
        try:
            os._exit(0)
        except Exception:
            pass

    def _on_update_check(self, result):
        """F-13: Wire both the header pill AND the sidebar auth-button area
        so the user never misses a new release. Auto-popup is delayed until
        any blocking first-launch Toplevels have closed.
        """
        if not (result and result.get("available")):
            return

        latest = result.get("latest", "?")
        self._last_update_info = result

        # Header pill — now with a soft orange background so it stands out.
        try:
            self._update_label.configure(
                image=icons.icon("arrow-up", 13, "#ffffff"),
                compound="left",
                text=f" v{latest}",
                text_color="#ffffff",
                fg_color="#fb923c",
                cursor="hand2",
            )
            # Re-bind each time (safe) and allow double-click too.
            self._update_label.bind("<Button-1>", lambda _: self._show_update_dialog(result))
        except Exception:
            pass

        # Auto-open the wizard once per launch. Delay up to 3 s so the
        # first-launch tray-notice dialog can be dismissed first without
        # stealing grab_set from a blank background.
        if not getattr(self, "_update_dialog_shown", False):
            self._update_dialog_shown = True
            def _deferred():
                # If another Toplevel (tray notice, auth dialog) is still up,
                # wait another 2 s before trying to steal focus.
                try:
                    for w in self.winfo_children():
                        if isinstance(w, ctk.CTkToplevel) and w.winfo_viewable():
                            self.after(2000, _deferred)
                            return
                except Exception:
                    pass
                self._show_update_dialog(result)
            self.after(2500, _deferred)

    def _show_update_dialog(self, update_info: dict):
        """Update download wizard — Step 1: info, Step 2: downloading, Step 3: done.
        F-13: robust layout — pack root frame first, solid (non-transparent) cards,
        immediate grab_set, and fallback changelog text if GitHub body is empty.
        """
        th = get_theme(self._current_game)
        d = ctk.CTkToplevel(self)
        d.title(t("update_available"))
        d.geometry("560x540")
        # Darker near-black modal bg (Claude-style)
        d.configure(fg_color=th.get("bg", th["content_bg"]))
        d.resizable(False, False)
        d.transient(self)
        # Force the Toplevel to render its decorations & background before
        # children get packed — fixes "empty window" on some Win11 themes.
        d.update_idletasks()
        try:
            d.grab_set()
        except Exception:
            pass

        latest = update_info.get("latest", "?")
        changelog = (update_info.get("changelog") or "").strip()
        download_url = update_info.get("download_url", "")

        # ── Step 1/2/3 stacked frames, generous 32px padding ──────────────────
        frame1 = ctk.CTkFrame(d, fg_color="transparent")
        frame2 = ctk.CTkFrame(d, fg_color="transparent")
        frame3 = ctk.CTkFrame(d, fg_color="transparent")

        def _show(f):
            for ff in (frame1, frame2, frame3):
                try:
                    ff.pack_forget()
                except Exception:
                    pass
            f.pack(fill="both", expand=True, padx=32, pady=32)

        # Pack frame1 FIRST so children render into an already-laid-out parent.
        _show(frame1)

        # Frame 1 — Info
        make_page_title(
            frame1, f"Nová verze: v{latest}", th,
            subtitle=f"Aktuální verze: v{CURRENT_VERSION}",
        ).pack(fill="x", anchor="w", pady=(0, 18))

        make_divider(frame1, th).pack(fill="x", pady=(0, 14))

        # Changelog notes inside a subtle card
        notes_card = make_card(frame1, th, padding=14)
        notes_card.pack(fill="both", expand=False, pady=(0, 18))
        make_section_title(notes_card, "Changelog", th).pack(
            anchor="w", padx=14, pady=(14, 6)
        )
        if not changelog:
            changelog = (
                "Podrobný changelog najdete na GitHub Releases.\n"
                "Detailed changelog is available on GitHub Releases."
            )
        notes_box = ctk.CTkTextbox(
            notes_card, height=140,
            fg_color="transparent",
            text_color=th["text"],
            font=ctk.CTkFont("Segoe UI", 10),
            corner_radius=0, border_width=0,
        )
        notes_box.pack(fill="x", padx=14, pady=(0, 14))
        notes_box.insert("end", changelog[:1200])
        notes_box.configure(state="disabled")

        btn_row1 = ctk.CTkFrame(frame1, fg_color="transparent")
        btn_row1.pack(fill="x")

        make_button(
            btn_row1, " Stáhnout a nainstalovat",
            lambda: _start_download(), th,
            variant="primary", accent="primary",
            height=42, width=200,
            icon=icons.icon("download", 16, "#ffffff"),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        make_button(
            btn_row1, t("later"), d.destroy, th,
            variant="ghost",
            height=42, width=100,
            font=ctk.CTkFont("Segoe UI", 12),
        ).pack(side="left")

        # Frame 2 — Downloading
        make_page_title(
            frame2, "Stahuji aktualizaci...", th,
            subtitle="Stahování se spouští na pozadí.",
        ).pack(fill="x", anchor="w", pady=(0, 18))

        make_divider(frame2, th).pack(fill="x", pady=(0, 18))

        dl_card = make_card(frame2, th, padding=18)
        dl_card.pack(fill="x")

        _dl_status = ctk.CTkLabel(
            dl_card, text="Připravuji stahování...",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        )
        _dl_status.pack(fill="x", padx=18, pady=(18, 10))
        _progress_bar = ctk.CTkProgressBar(
            dl_card, height=10,
            progress_color=th["primary"],
            fg_color=th.get("input_bg", th["secondary"]),
            corner_radius=5,
        )
        _progress_bar.pack(fill="x", padx=18, pady=(0, 4))
        _progress_bar.set(0)
        _pct_label = ctk.CTkLabel(
            dl_card, text="0 %",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_muted", th["text_dim"]),
        )
        _pct_label.pack(anchor="e", padx=18, pady=(0, 18))

        # Frame 3 — Done
        make_page_title(
            frame3, "Aktualizace stažena!", th,
            subtitle=f"Verze v{latest} je připravena k instalaci.",
        ).pack(fill="x", anchor="w", pady=(0, 18))

        make_divider(frame3, th).pack(fill="x", pady=(0, 18))

        done_card = make_card(frame3, th, padding=18)
        done_card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            done_card,
            text="Po kliknutí na 'Restartovat' se aplikace zavře\n"
                 "a automaticky nahradí sebe novou verzí.",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
            justify="left", anchor="w",
        ).pack(fill="x", padx=18, pady=18)

        _new_exe_path = [None]

        def _restart():
            if _new_exe_path[0]:
                apply_update(_new_exe_path[0])
            d.destroy()
            self.destroy()

        make_button(
            frame3, " Restartovat a nainstalovat", _restart, th,
            variant="primary", accent="success",
            height=44,
            icon=icons.icon("arrows-rotate", 16, "#ffffff"),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
        ).pack(fill="x")

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
                        text=f"Chyba stahování: {path_or_error[:120]}",
                        text_color=th.get("error", "#ef4444"))
                    _progress_bar.configure(progress_color=th.get("error", "#ef4444"))

            download_update(
                url,
                version=latest,
                progress_callback=lambda p: d.after(0, _on_progress, p),
                done_callback=lambda s, v: d.after(0, _on_done, s, v),
            )

        # frame1 already packed up-front via _show(frame1) above
        d.lift()
        d.focus_force()


class _LogoutDialog(ctk.CTkToplevel):
    """Potvrzovací dialog pro odhlaseni."""

    def __init__(self, parent, theme: dict, user: str):
        super().__init__(parent)
        self.result = None
        self.title(t("logout") + "?")
        self.geometry("400x240")
        self.resizable(False, False)
        self.configure(fg_color=theme.get("bg", theme["content_bg"]))
        self.grab_set()

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=32)

        make_page_title(
            root, t("logout") + "?", theme,
            subtitle=t("logged_in_as", user=user or "?"),
        ).pack(fill="x", anchor="w", pady=(0, 18))

        make_divider(root, theme).pack(fill="x", pady=(0, 18))

        row = ctk.CTkFrame(root, fg_color="transparent")
        row.pack(fill="x")

        make_button(
            row, " " + t("logout"), self._do_logout, theme,
            variant="primary", accent="danger",
            height=42, width=160,
            icon=icons.icon("right-from-bracket", 16, "#ffffff"),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        make_button(
            row, t("cancel"), self._cancel, theme,
            variant="ghost",
            height=42, width=110,
            font=ctk.CTkFont("Segoe UI", 12),
        ).pack(side="left")

    def _do_logout(self):
        self.result = "logout"
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()
