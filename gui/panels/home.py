"""
ZeddiHub Tools - Home Panel with server status (Steam A2S_INFO UDP) and recommended tools.
"""

import json
import time
import struct
import socket
import threading
import webbrowser
import urllib.request
import urllib.error
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from ..locale import t
except ImportError:
    def t(key, **kw): return key

try:
    from ..auth import is_authenticated, get_current_user
except ImportError:
    def is_authenticated(): return False
    def get_current_user(): return None

from .. import icons
from ..widgets import make_page_title, make_card, make_divider

BANNER_PATH = Path(__file__).parent.parent.parent / "assets" / "banner.png"
SERVER_STATUS_URL = "https://zeddihub.eu/tools/data/servers.json"
RECOMMENDED_URL   = "https://zeddihub.eu/tools/data/recommended.json"

A2S_INFO = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"

FALLBACK_RECOMMENDED = [
    {"name": "CS2 Crosshair", "desc": "Vygeneruj svůj crosshair", "nav_id": "cs2_player", "color": "#5b9cf6"},
    {"name": "CS2 Server CFG", "desc": "Nastavení herního serveru", "nav_id": "cs2_server", "color": "#5b9cf6"},
    {"name": "CS:GO Crosshair", "desc": "CS:GO crosshair generátor", "nav_id": "csgo_player", "color": "#fbbf24"},
    {"name": "Rust Server CFG", "desc": "Konfiguruj Rust server", "nav_id": "rust_server", "color": "#f97316"},
    {"name": "Keybind Generator", "desc": "Vizuální keybind editor", "nav_id": "cs2_keybind", "color": "#a78bfa"},
    {"name": "Translator", "desc": "Hromadný překlad .json/.lang", "nav_id": "translator", "color": "#4ade80"},
]


def query_server(ip: str, port: int, timeout: float = 3.0) -> Optional[dict]:
    """Query game server using Steam A2S_INFO protocol."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(A2S_INFO, (ip, int(port)))
        data, _ = sock.recvfrom(4096)
        sock.close()

        # Handle challenge response (0x41)
        if len(data) >= 5 and data[4:5] == b'\x41':
            challenge = data[5:9]
            req = A2S_INFO + challenge
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock2.settimeout(timeout)
            sock2.sendto(req, (ip, int(port)))
            data, _ = sock2.recvfrom(4096)
            sock2.close()

        if len(data) < 6 or data[4:5] != b'\x49':
            return None

        pos = 6  # Skip 4-byte header + type byte + protocol byte

        def read_str(d, p):
            end = d.index(b'\x00', p)
            return d[p:end].decode('utf-8', errors='replace'), end + 1

        name, pos = read_str(data, pos)
        map_name, pos = read_str(data, pos)
        folder, pos = read_str(data, pos)
        game_name, pos = read_str(data, pos)

        if pos + 6 > len(data):
            return {"online": True, "name": name, "map": map_name, "players": 0, "max_players": 0}

        app_id = struct.unpack_from('<H', data, pos)[0]
        pos += 2
        players = data[pos]
        pos += 1
        max_players = data[pos]
        pos += 1

        return {
            "online": True,
            "name": name,
            "map": map_name,
            "players": players,
            "max_players": max_players,
        }
    except Exception:
        return None


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#f0f0f0", **kw)


class HomePanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._server_widgets = []
        self._build()
        self._start_status_refresh()
        self._load_recommended()

    def _build(self):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color=th["content_bg"])
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        # Page title — Claude-app style: prominent heading + muted subtitle
        make_page_title(
            scroll, t("welcome"), th,
            subtitle=t("welcome_desc"),
        ).pack(fill="x", padx=32, pady=(28, 20), anchor="w")

        # Banner / hero area
        self._build_banner(scroll)

        # Quick links — transparent strip, no surrounding card
        welcome = ctk.CTkFrame(scroll, fg_color="transparent")
        welcome.pack(fill="x", padx=32, pady=(0, 8))

        links_row = ctk.CTkFrame(welcome, fg_color="transparent")
        links_row.pack(pady=(4, 12), anchor="w")

        quick_links = [
            (" ZeddiHub.eu", "https://zeddihub.eu",    "globe",   14, th.get("text_muted", "#cccccc")),
            (" Wiki",        "https://wiki.zeddihub.eu", "book",  14, th.get("text_muted", "#cccccc")),
            (" Discord",     "https://dsc.gg/zeddihub", "discord", 14, "#7289da"),
            (" ZeddiS.xyz",  "https://zeddis.xyz",      "globe",   14, th.get("text_muted", "#cccccc")),
        ]
        nav_hover = th.get("card_hover", th["secondary"])
        for label_text, url, icon_name, icon_size, icon_color in quick_links:
            btn_kw = {}
            if icon_name:
                btn_kw["image"] = icons.icon(icon_name, icon_size, icon_color)
                btn_kw["compound"] = "left"
            ctk.CTkButton(links_row, text=label_text, height=32, width=140,
                          fg_color="transparent", hover_color=nav_hover,
                          text_color=th["text"],
                          border_width=0,
                          corner_radius=8,
                          font=ctk.CTkFont("Segoe UI", 11),
                          command=lambda u=url: __import__("webbrowser").open(u),
                          **btn_kw
                          ).pack(side="left", padx=(0, 6))

        # ── Login card (N-11) + PC Tools quick grid (E-01) side by side ──
        two_col = ctk.CTkFrame(scroll, fg_color="transparent")
        two_col.pack(fill="x", padx=32, pady=(12, 12))
        two_col.grid_columnconfigure(0, weight=1)
        two_col.grid_columnconfigure(1, weight=2)

        self._login_card = make_card(two_col, th, padding=20)
        self._login_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._build_login_card(self._login_card)

        self._pc_home_card = make_card(two_col, th, padding=20)
        self._pc_home_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._build_pc_tools_home(self._pc_home_card)

        # Server status section — flat list, no chunky cards
        srv_header = ctk.CTkFrame(scroll, fg_color="transparent")
        srv_header.pack(fill="x", padx=32, pady=(20, 8))

        _label(srv_header, t("server_status"), 14, bold=True,
               color=th.get("text_strong", th["text"])
               ).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            srv_header, text="↻ " + t("refresh"), height=28, width=90,
            fg_color="transparent", hover_color=th.get("card_hover", th["secondary"]),
            text_color=th.get("text_muted", th["text_dim"]),
            border_width=0, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 10),
            command=self._refresh_status
        )
        self.refresh_btn.pack(side="right")

        self.last_update_label = _label(srv_header, "", 10,
                                        color=th.get("text_muted", th["text_dim"]))
        self.last_update_label.pack(side="right", padx=10)

        # Servers list card (holds flat rows with dividers)
        self.servers_frame = make_card(scroll, th, padding=0)
        self.servers_frame.pack(fill="x", padx=32, pady=4)

        self.status_label = _label(scroll, t("loading") + "...", 11,
                                   color=th.get("text_muted", th["text_dim"]))
        self.status_label.pack(padx=32, pady=4, anchor="w")

        # Recommended tools section
        rec_header = ctk.CTkFrame(scroll, fg_color="transparent")
        rec_header.pack(fill="x", padx=32, pady=(24, 8))
        _label(rec_header, t("recommended_tools"), 14, bold=True,
               color=th.get("text_strong", th["text"])
               ).pack(side="left")

        self._rec_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._rec_frame.pack(fill="x", padx=32, pady=4)

        # ── GitHub Checker (N-05) + Novinky z Releases (N-13) ────────────
        self._build_github_section(scroll)


    # ─── Login Card (N-11) ───────────────────────────────────────────────────

    def _build_login_card(self, parent):
        th = self.theme
        _label(parent, t("login_card_title"), 14, bold=True,
               color=th.get("text_strong", th["text"]),
               ).pack(padx=20, pady=(20, 4), anchor="w")

        self._login_status = _label(parent, "", 11,
                                    color=th.get("text_muted", th["text_dim"]))
        self._login_status.pack(padx=20, pady=(0, 12), anchor="w")

        self._login_btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        self._login_btn_row.pack(fill="x", padx=20, pady=(0, 20))

        self._refresh_login_card()

    def _refresh_login_card(self):
        """Re-render login card (called on auth state changes / periodic)."""
        th = self.theme
        for w in self._login_btn_row.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        if is_authenticated():
            user = get_current_user() or "?"
            self._login_status.configure(
                text=f"✅ {t('login_card_signed_in')}: {user}",
                text_color=th["success"],
            )
            ctk.CTkButton(
                self._login_btn_row, text=" " + t("login_card_profile_btn"),
                image=icons.icon("id-card", 13, th["text"]), compound="left",
                fg_color=th["secondary"], hover_color=th["primary"],
                font=ctk.CTkFont("Segoe UI", 11), height=32,
                command=lambda: self._nav_callback("settings") if self._nav_callback else None,
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                self._login_btn_row, text=" " + t("login_card_logout_btn"),
                image=icons.icon("sign-out-alt", 13, "#ffffff"), compound="left",
                fg_color="#8b2020", hover_color="#6b1818",
                text_color="#ffffff",
                font=ctk.CTkFont("Segoe UI", 11), height=32,
                command=self._handle_logout,
            ).pack(side="left")
        else:
            self._login_status.configure(
                text="🔒 " + t("login_card_anon"),
                text_color=th["text_dim"],
            )
            ctk.CTkButton(
                self._login_btn_row, text=" " + t("login_card_login_btn"),
                image=icons.icon("sign-in-alt", 13, "#ffffff"), compound="left",
                fg_color=th["primary"], hover_color=th["primary_hover"],
                font=ctk.CTkFont("Segoe UI", 11, "bold"), height=32,
                command=self._handle_login,
            ).pack(side="left")

    def _handle_login(self):
        parent = self.winfo_toplevel()
        if hasattr(parent, "_open_auth_dialog"):
            parent._open_auth_dialog(on_success=self._refresh_login_card)
        elif hasattr(parent, "_show_auth_dialog"):
            parent._show_auth_dialog()
            self.after(500, self._refresh_login_card)

    def _handle_logout(self):
        try:
            from ..auth import logout as _logout
            _logout()
        except Exception:
            pass
        self._refresh_login_card()
        parent = self.winfo_toplevel()
        if hasattr(parent, "_update_auth_ui"):
            try:
                parent._update_auth_ui()
            except Exception:
                pass

    # ─── PC Tools Home Quick Grid (E-01) ─────────────────────────────────────

    def _build_pc_tools_home(self, parent):
        th = self.theme
        text_muted = th.get("text_muted", th["text_dim"])
        nav_hover = th.get("card_hover", th["secondary"])

        header_row = ctk.CTkFrame(parent, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(20, 4))
        _label(header_row, t("pc_tools_home"), 14, bold=True,
               color=th.get("text_strong", th["text"])
               ).pack(side="left")
        ctk.CTkButton(
            header_row, text=t("pc_tools_open_full"),
            fg_color="transparent", hover_color=nav_hover,
            text_color=th["primary"],
            border_width=0, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 10), height=26,
            command=lambda: self._nav_callback("pc_tools") if self._nav_callback else None,
        ).pack(side="right")

        _label(parent, t("pc_tools_home_hint"),
               11, color=text_muted).pack(padx=20, pady=(0, 12), anchor="w")

        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 20))
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)

        actions = [
            (t("dns_flush_btn"),  "eraser",       self._pc_dns_flush),
            (t("temp_clean"),     "trash",        lambda: self._jump_pc_tab("dns_temp")),
            (t("ping_tool"),      "wifi",         lambda: self._jump_pc_tab("net_tools")),
            (t("ip_info"),        "globe",        lambda: self._jump_pc_tab("net_tools")),
            (t("sys_info"),       "microchip",    lambda: self._jump_pc_tab("sys_info")),
            (t("process_list"),   "list-check",   lambda: self._jump_pc_tab("utility")),
        ]

        for i, (label, icon_name, cmd) in enumerate(actions):
            b = ctk.CTkButton(
                grid, text=" " + label,
                image=icons.icon(icon_name, 14, text_muted),
                compound="left", anchor="w",
                fg_color="transparent", hover_color=nav_hover,
                text_color=th["text"],
                border_width=0, corner_radius=8,
                font=ctk.CTkFont("Segoe UI", 11),
                height=36,
                command=cmd,
            )
            b.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="ew")

    def _pc_dns_flush(self):
        """Inline DNS flush from the home panel."""
        import subprocess, tkinter.messagebox as _mb
        try:
            subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True, text=True, timeout=8,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            _mb.showinfo("DNS", "✅ DNS cache flushed.")
        except Exception as e:
            _mb.showerror("DNS", f"✗ {e}")

    def _jump_pc_tab(self, tab_name: str):
        """Navigate to pc_tools and hint which tab to open (best-effort)."""
        if self._nav_callback:
            self._nav_callback("pc_tools")

    def _build_banner(self, parent):
        th = self.theme
        banner_frame = make_card(parent, th, padding=16)
        banner_frame.configure(height=100)
        banner_frame.pack(fill="x", padx=32, pady=(4, 12))
        banner_frame.pack_propagate(False)

        if PIL_OK and BANNER_PATH.exists():
            try:
                img = Image.open(BANNER_PATH)
                img.thumbnail((600, 80), Image.LANCZOS)
                self._banner_img = ImageTk.PhotoImage(img)
                tk.Label(banner_frame, image=self._banner_img,
                         bg=th["card_bg"]).pack(expand=True)
                return
            except Exception:
                pass

        _label(banner_frame, "ZeddiHub Tools", 24, bold=True,
               color=th.get("text_strong", th["text"])).pack(expand=True)

    def _build_tools_overview(self, parent):
        th = self.theme
        _label(parent, " " + t("tools_overview"), 16, bold=True,
               color=th["primary"],
               image=icons.icon("tools", 18, th["primary"]), compound="left"
               ).pack(padx=20, pady=(16, 6), anchor="w")

        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.pack(padx=20, fill="x", pady=(0, 16))

        tools = [
            ("CS2 Nástroje",       "Crosshair, Viewmodel, Autoexec,\nPractice, Server CFG", "#5b9cf6"),
            ("CS:GO Nástroje",     "Crosshair, Viewmodel, Autoexec,\nServer CFG, RCON",     "#fbbf24"),
            ("Rust Nástroje",      "Server Config, Plugin Manager,\nAnalyzér závislostí",   "#f97316"),
            ("Translator",         "Hromadný překlad .json/.txt/.lang\ndo 20+ jazyků",       "#4ade80"),
            ("Keybind Generátor",  "Vizuální klávesnice pro bind\nCS2, CS:GO, Rust",          "#a78bfa"),
            ("PC Nástroje",        "Systémové info, DNS flush,\nNetwork tools, Utility",     "#fb923c"),
        ]

        cols = 3
        for i, (name, desc, color) in enumerate(tools):
            card = ctk.CTkFrame(grid_frame, fg_color=th["card_bg"], corner_radius=14)
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")

            indicator = ctk.CTkFrame(card, fg_color=color, height=3, corner_radius=0)
            indicator.pack(fill="x")

            _label(card, name, 12, bold=True, color=th["text"]
                   ).pack(padx=12, pady=(10, 4), anchor="w")
            _label(card, desc, 10, color=th["text_dim"]
                   ).pack(padx=12, pady=(0, 12), anchor="w")

        for c in range(cols):
            grid_frame.grid_columnconfigure(c, weight=1)

    # ─── SERVER STATUS ────────────────────────────────────────────────────────

    def _start_status_refresh(self):
        self._refresh_status()
        self.after(60000, self._start_status_refresh)

    def _refresh_status(self):
        self.refresh_btn.configure(state="disabled", text="...")
        threading.Thread(target=self._fetch_status, daemon=True).start()

    def _fetch_status(self):
        try:
            req = urllib.request.Request(
                SERVER_STATUS_URL,
                headers={"User-Agent": "ZeddiHubTools/1.0.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                servers = json.loads(resp.read().decode())
            self.after(0, self._update_server_cards, servers)
        except Exception:
            self.after(0, self._update_server_cards, [])

    def _update_server_cards(self, servers: list):
        th = self.theme

        for w in self._server_widgets:
            w.destroy()
        self._server_widgets.clear()

        for w in self.servers_frame.winfo_children():
            w.destroy()

        if not servers:
            self.status_label.configure(
                text="⚠ Nelze načíst status serverů (offline nebo API nedostupné).")
            servers = [
                {"name": "ZeddiHub Rust #1",  "ip": "rust1.zeddihub.eu",  "port": 28015, "game": "rust"},
                {"name": "ZeddiHub CS2 #1",   "ip": "cs2.zeddihub.eu",    "port": 27015, "game": "cs2"},
                {"name": "ZeddiHub CS:GO #1", "ip": "csgo.zeddihub.eu",   "port": 27015, "game": "csgo"},
            ]
        else:
            self.status_label.configure(text="")

        # Flat rows with subtle dividers between them
        for i, srv in enumerate(servers):
            if i > 0:
                make_divider(self.servers_frame, th).pack(fill="x", padx=16)
            row = self._make_server_row(self.servers_frame, srv, th)
            row.pack(fill="x")
            self._server_widgets.append(row)

        now = time.strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Aktualizováno: {now}")
        self.refresh_btn.configure(state="normal", text="↻ " + t("refresh"))

        # Query servers via A2S in background
        for srv in servers:
            threading.Thread(target=self._a2s_query_server, args=(srv,), daemon=True).start()

    def _make_server_row(self, parent, srv: dict, th: dict) -> ctk.CTkFrame:
        """Flat row: colored status dot | name + ip | map + players/ping | buttons."""
        game = srv.get("game", "default")
        game_colors = {"rust": "#f97316", "cs2": "#5b9cf6", "csgo": "#fbbf24"}
        game_color = game_colors.get(game, th["primary"])
        text_muted = th.get("text_muted", th["text_dim"])

        row = ctk.CTkFrame(parent, fg_color="transparent")

        # Status dot (small accent block on the left)
        dot = ctk.CTkLabel(
            row, text="●",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=text_muted,
        )
        dot.pack(side="left", padx=(16, 10), pady=12)
        row._status_dot = dot
        row._game_color = game_color

        # Left info stack
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="y", pady=10)

        name_lbl = _label(info, srv.get("name", "Server"), 12, bold=True,
                          color=th.get("text_strong", th["text"]))
        name_lbl.pack(anchor="w")
        row._name_label = name_lbl

        ip_port = f"{srv.get('ip', '')}:{srv.get('port', '')}"
        _label(info, ip_port, 10, color=text_muted).pack(anchor="w")

        # Right: status text + action buttons
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", padx=16, pady=10)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(side="right")

        nav_hover = th.get("card_hover", th["secondary"])
        ctk.CTkButton(btn_row, text=" " + t("copy_ip"), height=28, width=90,
                      fg_color="transparent", hover_color=nav_hover,
                      text_color=th["text"],
                      border_width=0, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 10),
                      image=icons.icon("copy", 13, text_muted), compound="left",
                      command=lambda ip=ip_port: self._copy_ip(ip)
                      ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(btn_row, text=" Steam", height=28, width=80,
                      fg_color="transparent", hover_color=nav_hover,
                      text_color="#4ade80",
                      border_width=0, corner_radius=8,
                      font=ctk.CTkFont("Segoe UI", 10, "bold"),
                      image=icons.icon("steam", 13, "#4ade80"), compound="left",
                      command=lambda ip=ip_port: self._steam_connect(ip)
                      ).pack(side="left")

        # Meta line (map / players / ping) — above the buttons
        meta = ctk.CTkFrame(right, fg_color="transparent")
        meta.pack(side="right", padx=(0, 16))

        status_lbl = ctk.CTkLabel(
            meta, text=t("unknown"),
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=text_muted,
        )
        status_lbl.pack(anchor="e")
        row._status_label = status_lbl

        meta_lbl = ctk.CTkLabel(
            meta, text="",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=text_muted,
        )
        meta_lbl.pack(anchor="e")
        row._meta_label = meta_lbl
        # Back-compat attributes used by _a2s_query_server
        row._players_label = meta_lbl
        row._map_label = meta_lbl
        row._ping_label = meta_lbl

        row._srv_data = srv
        return row

    def _a2s_query_server(self, srv: dict):
        ip = srv.get("ip", "")
        port = srv.get("port", 0)
        if not ip or not port:
            return

        start = time.time()
        result = query_server(ip, port)
        ping_ms = int((time.time() - start) * 1000)

        def update():
            for w in self._server_widgets:
                if not hasattr(w, '_srv_data') or w._srv_data.get("ip") != ip:
                    continue
                if result and result.get("online"):
                    if hasattr(w, '_status_dot'):
                        w._status_dot.configure(text_color="#4ade80")
                    if hasattr(w, '_status_label'):
                        w._status_label.configure(text=t("online"), text_color="#4ade80")
                    if hasattr(w, '_meta_label'):
                        map_name = result.get("map", "?")
                        players = result.get("players", 0)
                        maxp = result.get("max_players", 0)
                        meta_text = f"{map_name}  ·  {players}/{maxp}  ·  {ping_ms} ms"
                        w._meta_label.configure(text=meta_text)
                    # Update name from response (first CTkLabel inside info stack)
                    if hasattr(w, '_name_label'):
                        try:
                            w._name_label.configure(
                                text=result.get("name", srv.get("name", "Server")))
                        except Exception:
                            pass
                else:
                    if hasattr(w, '_status_dot'):
                        w._status_dot.configure(text_color="#f87171")
                    if hasattr(w, '_status_label'):
                        w._status_label.configure(text=t("offline"), text_color="#f87171")
                    if hasattr(w, '_meta_label'):
                        w._meta_label.configure(text="")

        self.after(0, update)

    def _copy_ip(self, ip: str):
        self.clipboard_clear()
        self.clipboard_append(ip)

    def _steam_connect(self, ip_port: str):
        webbrowser.open(f"steam://connect/{ip_port}")

    # ─── RECOMMENDED TOOLS ────────────────────────────────────────────────────

    def _load_recommended(self):
        threading.Thread(target=self._fetch_recommended, daemon=True).start()

    def _fetch_recommended(self):
        try:
            req = urllib.request.Request(
                RECOMMENDED_URL,
                headers={"User-Agent": "ZeddiHubTools/1.0.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                items = json.loads(resp.read().decode())
            if not items or not isinstance(items, list):
                items = FALLBACK_RECOMMENDED
        except Exception:
            items = FALLBACK_RECOMMENDED

        self.after(0, self._render_recommended, items)

    def _render_recommended(self, items: list):
        th = self.theme
        text_muted = th.get("text_muted", th["text_dim"])
        for w in self._rec_frame.winfo_children():
            w.destroy()

        cols = 3
        for i, item in enumerate(items[:6]):
            color = item.get("color", th["primary"])
            nav_id = item.get("nav_id")

            card = ctk.CTkFrame(self._rec_frame, fg_color=th["card_bg"],
                                corner_radius=14, border_width=0,
                                cursor="hand2" if nav_id else "arrow")
            card.grid(row=i // cols, column=i % cols, padx=8, pady=8, sticky="nsew")

            top = ctk.CTkFrame(card, fg_color=color, height=2, corner_radius=0)
            top.pack(fill="x")

            _label(card, item.get("name", ""), 13, bold=True,
                   color=th.get("text_strong", th["text"])
                   ).pack(padx=16, pady=(14, 4), anchor="w")
            _label(card, item.get("desc", ""), 11, color=text_muted
                   ).pack(padx=16, pady=(0, 14), anchor="w")

            if nav_id and self._nav_callback:
                for widget in [card, top]:
                    widget.bind("<Button-1>", lambda e, n=nav_id: self._nav_callback(n))

        for c in range(cols):
            self._rec_frame.grid_columnconfigure(c, weight=1)

    # ─── GitHub Checker (N-05) + Novinky z Releases (N-13) ────────────────
    GITHUB_REPO_API   = "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop"
    GITHUB_ISSUES_API = "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/issues?state=open&per_page=1"
    GITHUB_RELS_API   = "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases?per_page=5"

    def _build_github_section(self, parent):
        th = self.theme
        text_muted = th.get("text_muted", th["text_dim"])

        # Hlavička GitHub Checker
        gh_header = ctk.CTkFrame(parent, fg_color="transparent")
        gh_header.pack(fill="x", padx=32, pady=(24, 8))
        _label(gh_header, t("github_checker_section"), 14, bold=True,
               color=th.get("text_strong", th["text"])
               ).pack(side="left")

        # Čtyři statistické karty (Issues, Stars, Forks, Downloads)
        stats = ctk.CTkFrame(parent, fg_color="transparent")
        stats.pack(fill="x", padx=32, pady=(0, 6))
        for c in range(4):
            stats.grid_columnconfigure(c, weight=1)

        self._gh_stat_labels: dict = {}
        stat_defs = [
            ("issues",    t("github_issues"),    "#f87171"),
            ("stars",     t("github_stars"),     "#fbbf24"),
            ("forks",     t("github_forks"),     "#5b9cf6"),
            ("downloads", t("github_downloads"), "#4ade80"),
        ]
        for i, (key, label, color) in enumerate(stat_defs):
            card = ctk.CTkFrame(stats, fg_color=th["card_bg"], corner_radius=14, border_width=0)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            val_lbl = _label(card, "…", 22, bold=True, color=color)
            val_lbl.pack(padx=18, pady=(16, 0), anchor="w")
            _label(card, label, 11, color=text_muted).pack(padx=18, pady=(2, 16), anchor="w")
            self._gh_stat_labels[key] = val_lbl

        # Novinky (Releases)
        news_header = ctk.CTkFrame(parent, fg_color="transparent")
        news_header.pack(fill="x", padx=32, pady=(20, 8))
        _label(news_header, t("news_section"), 14, bold=True,
               color=th.get("text_strong", th["text"])
               ).pack(side="left")

        self._news_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._news_frame.pack(fill="x", padx=32, pady=(0, 24))
        self._news_loading_lbl = _label(self._news_frame, t("news_loading"),
                                         11, color=th["text_dim"])
        self._news_loading_lbl.pack(padx=4, pady=8, anchor="w")

        # Fetch na pozadí
        threading.Thread(target=self._gh_fetch_worker, daemon=True).start()

    def _gh_fetch_worker(self):
        """Načte GitHub statistiky + Releases v pozadí. Fire-and-forget s fallbackem."""
        headers = {"Accept": "application/vnd.github.v3+json",
                   "User-Agent": "ZeddiHub-Tools"}
        stats = {"issues": "?", "stars": "?", "forks": "?", "downloads": "?"}
        releases: list = []
        try:
            # Repo info
            req = urllib.request.Request(self.GITHUB_REPO_API, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                info = json.loads(resp.read().decode("utf-8", errors="replace"))
                stats["stars"] = str(info.get("stargazers_count", 0))
                stats["forks"] = str(info.get("forks_count", 0))
                stats["issues"] = str(info.get("open_issues_count", 0))
        except Exception:
            pass

        try:
            # Releases — downloads = suma asset.download_count
            req = urllib.request.Request(self.GITHUB_RELS_API, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                rels = json.loads(resp.read().decode("utf-8", errors="replace"))
                total_dl = 0
                for r in rels:
                    for a in r.get("assets", []):
                        total_dl += int(a.get("download_count", 0) or 0)
                stats["downloads"] = str(total_dl)
                releases = rels[:5]
        except Exception:
            pass

        # UI update na main threadu (thread safety dle CLAUDE.md §3.5)
        try:
            self.after(0, self._gh_apply_stats, stats)
            self.after(0, self._gh_apply_news, releases)
        except Exception:
            pass

    def _gh_apply_stats(self, stats: dict):
        for key, val in stats.items():
            lbl = self._gh_stat_labels.get(key)
            if lbl is not None:
                try:
                    lbl.configure(text=val)
                except Exception:
                    pass

    def _gh_apply_news(self, releases: list):
        th = self.theme
        try:
            self._news_loading_lbl.destroy()
        except Exception:
            pass
        for w in list(self._news_frame.winfo_children()):
            try:
                w.destroy()
            except Exception:
                pass

        if not releases:
            _label(self._news_frame, t("news_no_items"), 11, color=th["text_dim"]
                   ).pack(padx=4, pady=8, anchor="w")
            return

        text_muted = th.get("text_muted", th["text_dim"])
        for rel in releases:
            tag = rel.get("tag_name", "?")
            name = rel.get("name") or tag
            body = (rel.get("body") or "").strip()
            published = (rel.get("published_at") or "")[:10]
            html_url = rel.get("html_url", "")

            card = ctk.CTkFrame(self._news_frame, fg_color=th["card_bg"],
                                corner_radius=14, border_width=0)
            card.pack(fill="x", pady=6)
            head_row = ctk.CTkFrame(card, fg_color="transparent")
            head_row.pack(fill="x", padx=20, pady=(16, 0))
            _label(head_row, f"{name}  ({tag})", 13, bold=True,
                   color=th.get("text_strong", th["text"])
                   ).pack(side="left")
            if published:
                _label(head_row, published, 10, color=text_muted
                       ).pack(side="right")
            # Body — první 3 řádky
            body_short = "\n".join(body.splitlines()[:3]).strip()
            if body_short:
                _label(card, body_short, 11, color=text_muted,
                       wraplength=700, justify="left"
                       ).pack(padx=20, pady=(6, 4), anchor="w")
            if html_url:
                nav_hover = th.get("card_hover", th["secondary"])
                ctk.CTkButton(card, text=t("open_github"), height=28, width=120,
                              fg_color="transparent", hover_color=nav_hover,
                              text_color=th["text"],
                              border_width=0, corner_radius=8,
                              font=ctk.CTkFont("Segoe UI", 10),
                              command=lambda u=html_url: webbrowser.open(u)
                              ).pack(padx=16, pady=(4, 16), anchor="w")
