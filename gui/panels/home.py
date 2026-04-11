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

BANNER_PATH = Path(__file__).parent.parent.parent / "assets" / "banner.png"
SERVER_STATUS_URL = "https://files.zeddihub.eu/tools/servers.json"
RECOMMENDED_URL   = "https://files.zeddihub.eu/tools/recommended.json"

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

        # Banner / hero area
        self._build_banner(scroll)

        # Welcome
        welcome = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=10)
        welcome.pack(fill="x", padx=20, pady=(8, 8))

        _label(welcome, t("welcome"), 20, bold=True, color=th["primary"]
               ).pack(padx=20, pady=(16, 4), anchor="w")
        _label(welcome, t("welcome_desc"), 12, color=th["text_dim"]
               ).pack(padx=20, pady=(0, 6), anchor="w")

        links_row = ctk.CTkFrame(welcome, fg_color="transparent")
        links_row.pack(padx=20, pady=(4, 16), anchor="w")

        quick_links = [
            ("🌐 ZeddiHub.eu", "https://zeddihub.eu"),
            ("📖 Wiki", "https://wiki.zeddihub.eu"),
            ("💬 Discord", "https://dsc.gg/zeddihub"),
            ("👨‍💻 ZeddiS.xyz", "https://zeddis.xyz"),
        ]
        for label_text, url in quick_links:
            ctk.CTkButton(links_row, text=label_text, height=30, width=140,
                          fg_color=th["secondary"], hover_color=th["primary"],
                          font=ctk.CTkFont("Segoe UI", 11),
                          command=lambda u=url: __import__("webbrowser").open(u)
                          ).pack(side="left", padx=4)

        # Server status section
        srv_header = ctk.CTkFrame(scroll, fg_color="transparent")
        srv_header.pack(fill="x", padx=20, pady=(12, 4))

        _label(srv_header, "📡 " + t("server_status"), 16, bold=True,
               color=th["primary"]).pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            srv_header, text="↻ " + t("refresh"), height=28, width=90,
            fg_color=th["secondary"], hover_color=th["primary"],
            font=ctk.CTkFont("Segoe UI", 10),
            command=self._refresh_status
        )
        self.refresh_btn.pack(side="right")

        self.last_update_label = _label(srv_header, "", 9, color=th["text_dim"])
        self.last_update_label.pack(side="right", padx=8)

        self.servers_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.servers_frame.pack(fill="x", padx=20, pady=4)

        self.status_label = _label(scroll, t("loading") + "...", 11, color=th["text_dim"])
        self.status_label.pack(padx=20, pady=4, anchor="w")

        # Recommended tools section
        rec_header = ctk.CTkFrame(scroll, fg_color="transparent")
        rec_header.pack(fill="x", padx=20, pady=(16, 4))
        _label(rec_header, "⚡ " + t("recommended_tools"), 16, bold=True,
               color=th["primary"]).pack(side="left")

        self._rec_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._rec_frame.pack(fill="x", padx=20, pady=4)


    def _build_banner(self, parent):
        th = self.theme
        banner_frame = ctk.CTkFrame(parent, fg_color=th["card_bg"], corner_radius=10, height=100)
        banner_frame.pack(fill="x", padx=20, pady=(12, 8))
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

        _label(banner_frame, "ZeddiHub Tools", 26, bold=True,
               color=th["primary"]).pack(expand=True)

    def _build_tools_overview(self, parent):
        th = self.theme
        _label(parent, "🛠 " + t("tools_overview"), 16, bold=True,
               color=th["primary"]).pack(padx=20, pady=(16, 6), anchor="w")

        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.pack(padx=20, fill="x", pady=(0, 16))

        tools = [
            ("🎯 CS2 Nástroje",       "Crosshair, Viewmodel, Autoexec,\nPractice, Server CFG", "#5b9cf6"),
            ("🎮 CS:GO Nástroje",     "Crosshair, Viewmodel, Autoexec,\nServer CFG, RCON",     "#fbbf24"),
            ("🦀 Rust Nástroje",      "Server Config, Plugin Manager,\nAnalyzér závislostí",   "#f97316"),
            ("🌍 Translator",         "Hromadný překlad .json/.txt/.lang\ndo 20+ jazyků",       "#4ade80"),
            ("⌨ Keybind Generátor",  "Vizuální klávesnice pro bind\nCS2, CS:GO, Rust",          "#a78bfa"),
            ("💻 PC Nástroje",        "Systémové info, DNS flush,\nNetwork tools, Utility",     "#fb923c"),
        ]

        cols = 3
        for i, (name, desc, color) in enumerate(tools):
            card = ctk.CTkFrame(grid_frame, fg_color=th["card_bg"], corner_radius=8)
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

        cols = min(len(servers), 3) if servers else 1
        for i, srv in enumerate(servers):
            card = self._make_server_card(self.servers_frame, srv, th)
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")
            self._server_widgets.append(card)

        for c in range(cols):
            self.servers_frame.grid_columnconfigure(c, weight=1)

        now = time.strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Aktualizováno: {now}")
        self.refresh_btn.configure(state="normal", text="↻ " + t("refresh"))

        # Query servers via A2S in background
        for srv in servers:
            threading.Thread(target=self._a2s_query_server, args=(srv,), daemon=True).start()

    def _make_server_card(self, parent, srv: dict, th: dict) -> ctk.CTkFrame:
        game = srv.get("game", "default")
        game_colors = {"rust": "#f97316", "cs2": "#5b9cf6", "csgo": "#fbbf24"}
        game_color = game_colors.get(game, th["primary"])

        card = ctk.CTkFrame(parent, fg_color=th["card_bg"], corner_radius=8)

        header = ctk.CTkFrame(card, fg_color=game_color, corner_radius=0, height=3)
        header.pack(fill="x")
        header.pack_propagate(False)

        _label(card, srv.get("name", "Server"), 13, bold=True, color=th["text"]
               ).pack(padx=12, pady=(10, 2), anchor="w")

        ip_port = f"{srv.get('ip', '')}:{srv.get('port', '')}"
        _label(card, ip_port, 10, color=th["text_dim"]).pack(padx=12, anchor="w")

        status_lbl = ctk.CTkLabel(
            card, text="● " + t("unknown"),
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color="#888888"
        )
        status_lbl.pack(padx=12, pady=(4, 2), anchor="w")
        card._status_label = status_lbl

        self._players_lbl = ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th["text_dim"]
        )
        self._players_lbl.pack(padx=12, pady=(0, 2), anchor="w")
        card._players_label = self._players_lbl

        self._map_lbl = ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th["text_dim"]
        )
        self._map_lbl.pack(padx=12, pady=(0, 2), anchor="w")
        card._map_label = self._map_lbl

        self._ping_lbl = ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th["text_dim"]
        )
        self._ping_lbl.pack(padx=12, pady=(0, 4), anchor="w")
        card._ping_label = self._ping_lbl

        card._srv_data = srv

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(padx=12, pady=(2, 10), anchor="w")

        ctk.CTkButton(btn_row, text="📋 " + t("copy_ip"), height=26, width=100,
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 9),
                      command=lambda ip=ip_port: self._copy_ip(ip)
                      ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(btn_row, text="▶ Steam", height=26, width=80,
                      fg_color="#1a3a1a", hover_color="#4ade80",
                      text_color="#4ade80",
                      font=ctk.CTkFont("Segoe UI", 9, "bold"),
                      command=lambda ip=ip_port: self._steam_connect(ip)
                      ).pack(side="left")

        return card

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
                    if hasattr(w, '_status_label'):
                        w._status_label.configure(text="● " + t("online"), text_color="#4ade80")
                    if hasattr(w, '_players_label'):
                        w._players_label.configure(
                            text=t("players", current=result.get("players", 0),
                                   max=result.get("max_players", 0)))
                    if hasattr(w, '_map_label'):
                        w._map_label.configure(text=t("map", map=result.get("map", "?")))
                    if hasattr(w, '_ping_label'):
                        w._ping_label.configure(text=f"Ping: {ping_ms} ms")
                    # Update name from response
                    children = w.winfo_children()
                    for child in children:
                        if (isinstance(child, ctk.CTkLabel) and
                                child.cget("font") and
                                "bold" in str(child.cget("font"))):
                            try:
                                child.configure(text=result.get("name", srv.get("name", "Server")))
                            except Exception:
                                pass
                            break
                else:
                    if hasattr(w, '_status_label'):
                        w._status_label.configure(text="● " + t("offline"), text_color="#f87171")
                    if hasattr(w, '_ping_label'):
                        w._ping_label.configure(text="")

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
        for w in self._rec_frame.winfo_children():
            w.destroy()

        cols = 3
        for i, item in enumerate(items[:6]):
            color = item.get("color", th["primary"])
            nav_id = item.get("nav_id")

            card = ctk.CTkFrame(self._rec_frame, fg_color=th["card_bg"],
                                corner_radius=8, cursor="hand2" if nav_id else "arrow")
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")

            top = ctk.CTkFrame(card, fg_color=color, height=3, corner_radius=0)
            top.pack(fill="x")

            _label(card, item.get("name", ""), 12, bold=True, color=th["text"]
                   ).pack(padx=12, pady=(10, 2), anchor="w")
            _label(card, item.get("desc", ""), 10, color=th["text_dim"]
                   ).pack(padx=12, pady=(0, 10), anchor="w")

            if nav_id and self._nav_callback:
                for widget in [card, top]:
                    widget.bind("<Button-1>", lambda e, n=nav_id: self._nav_callback(n))

        for c in range(cols):
            self._rec_frame.grid_columnconfigure(c, weight=1)
