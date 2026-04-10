"""
ZeddiHub Tools - Main application window with sidebar navigation.
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
from .panels.home import HomePanel
from .panels.cs2 import CS2PlayerPanel, CS2ServerPanel
from .panels.csgo import CSGOPlayerPanel, CSGOServerPanel
from .panels.rust import RustPlayerPanel, RustServerPanel
from .panels.keybind import KeybindPanel
from .panels.translator import TranslatorPanel
from .panels.links import LinksPanel

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
ICON_PATH = ASSETS_DIR / "icon.ico"

SIDEBAR_W = 230
HEADER_H = 50

# Nav item: (id, label, icon, section, game, requires_auth)
NAV_ITEMS = [
    ("home",         "Domovská stránka",  "🏠", None,   None,    False),
    ("sep_cs2",      "── CS2 ──",         "",    None,   None,    False),
    ("cs2_player",   "Hráčské nástroje",  "👤", "CS2",  "cs2",   False),
    ("cs2_server",   "Serverové nástroje","🖥", "CS2",  "cs2",   True),
    ("cs2_keybind",  "Keybind Generátor", "⌨", "CS2",  "cs2",   False),
    ("sep_csgo",     "── CS:GO ──",       "",    None,   None,    False),
    ("csgo_player",  "Hráčské nástroje",  "👤", "CS:GO","csgo",  False),
    ("csgo_server",  "Serverové nástroje","🖥", "CS:GO","csgo",  True),
    ("csgo_keybind", "Keybind Generátor", "⌨", "CS:GO","csgo",  False),
    ("sep_rust",     "── Rust ──",        "",    None,   None,    False),
    ("rust_player",  "Hráčské nástroje",  "👤", "Rust", "rust",  False),
    ("rust_server",  "Serverové nástroje","🖥", "Rust", "rust",  True),
    ("rust_keybind", "Keybind Generátor", "⌨", "Rust", "rust",  False),
    ("sep_tools",    "── Nástroje ──",    "",    None,   None,    False),
    ("translator",   "Translator",        "🌍", None,   None,    False),
    ("links",        "Odkazy a Klienti",  "🔗", None,   None,    False),
]


class AuthDialog(ctk.CTkToplevel):
    """Login dialog for server tools access."""

    def __init__(self, parent, theme: dict):
        super().__init__(parent)
        self.theme = theme
        self.result = False
        self.title("Přihlášení – Server Tools")
        self.geometry("440x380")
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
        t = self.theme

        ctk.CTkLabel(self, text="🔒  Přihlášení k Server Tools",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=t["primary"]).pack(pady=(20, 4), padx=24, anchor="w")
        ctk.CTkLabel(self, text="Zadejte přihlašovací údaje nebo přístupový kód.",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=t["text_dim"]
                     ).pack(padx=24, anchor="w")

        form = ctk.CTkFrame(self, fg_color=t["card_bg"], corner_radius=8)
        form.pack(fill="x", padx=24, pady=12)

        ctk.CTkLabel(form, text="Uživatelské jméno / kód:",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=t["text_dim"], anchor="w"
                     ).pack(padx=16, pady=(14, 2), anchor="w")
        self._user_entry = ctk.CTkEntry(form, placeholder_text="username nebo access_code",
                                        fg_color=t["secondary"], text_color=t["text"],
                                        font=ctk.CTkFont("Segoe UI", 12), height=38)
        self._user_entry.pack(padx=16, fill="x")

        ctk.CTkLabel(form, text="Heslo (prázdné pro kód):",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=t["text_dim"], anchor="w"
                     ).pack(padx=16, pady=(10, 2), anchor="w")
        self._pass_entry = ctk.CTkEntry(form, placeholder_text="heslo...",
                                        fg_color=t["secondary"], text_color=t["text"],
                                        font=ctk.CTkFont("Segoe UI", 12), height=38, show="*")
        self._pass_entry.pack(padx=16, pady=(0, 4), fill="x")
        self._pass_entry.bind("<Return>", lambda _: self._login())

        self._remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Zapamatovat přihlášení (šifrováno)",
                        variable=self._remember_var,
                        text_color=t["text_dim"], fg_color=t["primary"],
                        font=ctk.CTkFont("Segoe UI", 10)
                        ).pack(padx=16, pady=(4, 14), anchor="w")

        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(self, textvariable=self.status_var,
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=t["warning"]).pack(padx=24, anchor="w")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=12)

        ctk.CTkButton(btn_row, text="🔓 Přihlásit se",
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"), height=40,
                      command=self._login).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_row, text="Zrušit",
                      fg_color=t["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 12), height=40,
                      command=self.destroy).pack(side="left", width=100)

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
                self.destroy()
            else:
                self.status_var.set(f"✗ {msg}")

        verify_access(user, pw, callback=lambda s, m: self.after(0, on_result, s, m))


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self._current_panel: Optional[ctk.CTkFrame] = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
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
            verify_access(saved[0], saved[1])

    def _setup_window(self):
        self.title(f"ZeddiHub Tools  v{CURRENT_VERSION}")
        w, h = 1280, 820
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(960, 640)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#0d0d1a")

    def _setup_icon(self):
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
                return
            except Exception:
                pass
        # Try PNG logo as icon
        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((32, 32), Image.LANCZOS)
                self._icon_img = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon_img)
            except Exception:
                pass

    def _build_layout(self):
        # Main container
        self._main = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=0)
        self._main.pack(fill="both", expand=True)

        # Header bar
        self._header = ctk.CTkFrame(self._main, fg_color="#0a0a16", height=HEADER_H, corner_radius=0)
        self._header.pack(fill="x", side="top")
        self._header.pack_propagate(False)
        self._build_header()

        # Body (sidebar + content)
        body = ctk.CTkFrame(self._main, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ctk.CTkFrame(body, fg_color="#1a1a2e", width=SIDEBAR_W, corner_radius=0)
        self._sidebar.pack(fill="y", side="left")
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self._content_container = ctk.CTkFrame(body, fg_color="#16213e", corner_radius=0)
        self._content_container.pack(fill="both", expand=True, side="left")

    def _build_header(self):
        t = get_theme(self._current_game)

        # Logo / title
        title_frame = ctk.CTkFrame(self._header, fg_color="transparent")
        title_frame.pack(side="left", padx=16, fill="y")

        self._header_title = ctk.CTkLabel(
            title_frame, text="ZeddiHub Tools",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color="#e07b39"
        )
        self._header_title.pack(side="left", padx=(0, 8))

        self._game_badge = ctk.CTkLabel(
            title_frame, text="",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color="#666666"
        )
        self._game_badge.pack(side="left")

        # Right: auth status, version
        right = ctk.CTkFrame(self._header, fg_color="transparent")
        right.pack(side="right", padx=16, fill="y")

        self._auth_label = ctk.CTkLabel(right, text="🔓 Nepřihlášen",
                                         font=ctk.CTkFont("Segoe UI", 10),
                                         text_color="#666666")
        self._auth_label.pack(side="right", padx=8)

        self._update_label = ctk.CTkLabel(right, text=f"v{CURRENT_VERSION}",
                                           font=ctk.CTkFont("Segoe UI", 10),
                                           text_color="#444444")
        self._update_label.pack(side="right", padx=8)

    def _build_sidebar(self):
        t = get_theme("default")

        # Logo at top of sidebar
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="#0d0d1a", height=70, corner_radius=0)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)

        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH).resize((40, 40), Image.LANCZOS)
                self._sidebar_logo = ImageTk.PhotoImage(img)
                tk.Label(logo_frame, image=self._sidebar_logo, bg="#0d0d1a").pack(
                    side="left", padx=10, pady=14)
            except Exception:
                pass

        ctk.CTkLabel(logo_frame, text="ZeddiHub\nTools",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color="#e07b39", justify="left"
                     ).pack(side="left", pady=14)

        ctk.CTkFrame(self._sidebar, fg_color="#2a2a3e", height=1).pack(fill="x")

        # Scrollable nav
        nav_scroll = ctk.CTkScrollableFrame(self._sidebar, fg_color="transparent",
                                             scrollbar_button_color="#2a2a3e")
        nav_scroll.pack(fill="both", expand=True, padx=0, pady=4)

        self._nav_scroll = nav_scroll
        self._build_nav_items()

        # Bottom: auth button
        ctk.CTkFrame(self._sidebar, fg_color="#2a2a3e", height=1).pack(fill="x", side="bottom")
        self._auth_btn = ctk.CTkButton(
            self._sidebar, text="🔐 Přihlásit (Server Tools)",
            fg_color="#0d0d1a", hover_color="#2a2a3e",
            text_color="#888888", anchor="w",
            font=ctk.CTkFont("Segoe UI", 10),
            height=36, command=self._show_auth_dialog
        )
        self._auth_btn.pack(fill="x", padx=0, pady=4, side="bottom")

    def _build_nav_items(self):
        for nav_id, label, icon, section, game, requires_auth in NAV_ITEMS:
            if nav_id.startswith("sep_"):
                # Separator label
                sep = ctk.CTkLabel(
                    self._nav_scroll,
                    text=label,
                    font=ctk.CTkFont("Segoe UI", 9),
                    text_color="#444466"
                )
                sep.pack(fill="x", padx=8, pady=(8, 2))
                continue

            lock = " 🔒" if requires_auth else ""
            display = f"  {icon}  {label}{lock}" if icon else f"  {label}{lock}"

            btn = ctk.CTkButton(
                self._nav_scroll,
                text=display,
                fg_color="transparent",
                hover_color="#2d2d4a",
                text_color="#cccccc",
                anchor="w",
                font=ctk.CTkFont("Segoe UI", 12),
                height=38,
                corner_radius=6,
                command=lambda nid=nav_id, auth=requires_auth: self._on_nav_click(nid, auth)
            )
            btn.pack(fill="x", padx=6, pady=1)
            self._nav_buttons[nav_id] = btn

    def _on_nav_click(self, nav_id: str, requires_auth: bool):
        if requires_auth and not is_authenticated():
            dialog = AuthDialog(self, get_theme(self._current_game))
            self.wait_window(dialog)
            if not dialog.result:
                return
            self._update_auth_ui()

        self._navigate(nav_id)

    def _navigate(self, nav_id: str):
        self._current_nav_id = nav_id

        # Update nav button styles
        for nid, btn in self._nav_buttons.items():
            game = self._get_game_for_nav(nid)
            t = get_theme(game or self._current_game)
            if nid == nav_id:
                btn.configure(fg_color=t["primary"], text_color="#ffffff",
                              hover_color=t["primary_hover"])
            else:
                btn.configure(fg_color="transparent", text_color="#cccccc",
                              hover_color="#2d2d4a")

        # Determine game theme
        game = self._get_game_for_nav(nav_id)
        if game and game != self._current_game:
            self._current_game = game
            self._apply_theme()

        # Show panel
        self._show_panel(nav_id)

    def _get_game_for_nav(self, nav_id: str) -> Optional[str]:
        for nid, _, _, _, game, _ in NAV_ITEMS:
            if nid == nav_id:
                return game
        return None

    def _apply_theme(self):
        t = get_theme(self._current_game)
        self._content_container.configure(fg_color=t["content_bg"])
        self._sidebar.configure(fg_color=t["sidebar_bg"])

        # Update game badge
        game_names = {"cs2": "Counter-Strike 2", "csgo": "CS:GO", "rust": "Rust", "default": ""}
        self._game_badge.configure(
            text=game_names.get(self._current_game, ""),
            text_color=t["primary"]
        )

    def _show_panel(self, nav_id: str):
        """Destroy current panel and create new one."""
        if self._current_panel:
            self._current_panel.destroy()
            self._current_panel = None

        t = get_theme(self._current_game)
        container = self._content_container

        panel = None
        if nav_id == "home":
            panel = HomePanel(container, theme=get_theme("default"))
        elif nav_id == "cs2_player":
            panel = CS2PlayerPanel(container, theme=t)
        elif nav_id == "cs2_server":
            panel = CS2ServerPanel(container, theme=t)
        elif nav_id == "cs2_keybind":
            panel = KeybindPanel(container, game="cs2", theme=t)
        elif nav_id == "csgo_player":
            panel = CSGOPlayerPanel(container, theme=t)
        elif nav_id == "csgo_server":
            panel = CSGOServerPanel(container, theme=t)
        elif nav_id == "csgo_keybind":
            panel = KeybindPanel(container, game="csgo", theme=t)
        elif nav_id == "rust_player":
            panel = RustPlayerPanel(container, theme=t)
        elif nav_id == "rust_server":
            panel = RustServerPanel(container, theme=t)
        elif nav_id == "rust_keybind":
            panel = KeybindPanel(container, game="rust", theme=t)
        elif nav_id == "translator":
            panel = TranslatorPanel(container, theme=get_theme("default"))
        elif nav_id == "links":
            panel = LinksPanel(container, theme=get_theme("default"))

        if panel:
            panel.pack(fill="both", expand=True)
            self._current_panel = panel

    def _show_auth_dialog(self):
        if is_authenticated():
            # Show logout option
            user = get_current_user()
            dialog = _LogoutDialog(self, get_theme(self._current_game), user)
            self.wait_window(dialog)
            if dialog.result == "logout":
                logout()
                self._update_auth_ui()
        else:
            dialog = AuthDialog(self, get_theme(self._current_game))
            self.wait_window(dialog)
            if dialog.result:
                self._update_auth_ui()

    def _update_auth_ui(self):
        if is_authenticated():
            user = get_current_user() or "?"
            self._auth_label.configure(text=f"🔓 {user}", text_color="#4caf50")
            self._auth_btn.configure(text=f"✓ Přihlášen: {user}", text_color="#4caf50")

            # Update lock icons in nav
            for nav_id, _, _, _, _, requires_auth in NAV_ITEMS:
                if requires_auth and nav_id in self._nav_buttons:
                    btn = self._nav_buttons[nav_id]
                    current_text = btn.cget("text").replace(" 🔒", " ✓")
                    btn.configure(text=current_text, text_color="#cccccc")
        else:
            self._auth_label.configure(text="🔓 Nepřihlášen", text_color="#666666")
            self._auth_btn.configure(text="🔐 Přihlásit (Server Tools)", text_color="#888888")

    def _on_update_check(self, result):
        if result and result.get("available"):
            latest = result.get("latest", "?")
            self._update_label.configure(
                text=f"⬆ v{CURRENT_VERSION} → v{latest}",
                text_color="#ff9800",
                cursor="hand2"
            )
            self._update_label.bind("<Button-1>", lambda _: self._show_update_dialog(result))

    def _show_update_dialog(self, update_info: dict):
        t = get_theme(self._current_game)
        d = ctk.CTkToplevel(self)
        d.title("Dostupná aktualizace")
        d.geometry("460x300")
        d.configure(fg_color=t["content_bg"])
        d.grab_set()

        ctk.CTkLabel(d, text=f"⬆ Nová verze: v{update_info['latest']}",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color="#ff9800").pack(pady=(20, 4), padx=24, anchor="w")
        ctk.CTkLabel(d, text=f"Aktuální verze: v{CURRENT_VERSION}",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=t["text_dim"]
                     ).pack(padx=24, anchor="w")

        if update_info.get("changelog"):
            ctk.CTkTextbox(d, height=100, fg_color=t["secondary"], text_color=t["text"],
                           font=ctk.CTkFont("Segoe UI", 10), state="normal"
                           ).pack(fill="x", padx=24, pady=12)

        btn_row = ctk.CTkFrame(d, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=12)

        ctk.CTkButton(btn_row, text="📥 Stáhnout / GitHub",
                      fg_color="#ff9800", hover_color="#e08000",
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=40,
                      command=lambda: (webbrowser.open(
                          "https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"),
                          d.destroy())
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(btn_row, text="Později",
                      fg_color=t["secondary"], height=40,
                      command=d.destroy).pack(side="left", width=100)


class _LogoutDialog(ctk.CTkToplevel):
    def __init__(self, parent, theme: dict, user: str):
        super().__init__(parent)
        self.result = None
        self.title("Odhlásit se?")
        self.geometry("360x180")
        self.configure(fg_color=theme["content_bg"])
        self.grab_set()

        ctk.CTkLabel(self, text=f"Přihlášen jako: {user}",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=theme["text"]).pack(pady=(24, 8), padx=20, anchor="w")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=16)

        ctk.CTkButton(row, text="🔒 Odhlásit se",
                      fg_color="#8b2020", hover_color="#6b1818",
                      height=40, command=self._logout
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(row, text="Zrušit",
                      fg_color=theme["secondary"], height=40,
                      command=self.destroy).pack(side="left", width=100)

    def _logout(self):
        self.result = "logout"
        self.destroy()
