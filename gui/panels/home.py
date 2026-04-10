"""
ZeddiHub Tools - Home Panel with server status display.
Fetches server status from webhosting API.
"""

import json
import time
import threading
import socket
import urllib.request
import urllib.error
import tkinter as tk
import customtkinter as ctk
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

BANNER_PATH = Path(__file__).parent.parent.parent / "assets" / "banner.png"
SERVER_STATUS_URL = "https://files.zeddihub.eu/tools/servers.json"


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#ffffff", **kw)


class HomePanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._server_widgets = []
        self._build()
        self._start_status_refresh()

    def _build(self):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color=t["content_bg"])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Banner
        self._build_banner(scroll)

        # Welcome section
        welcome = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=10)
        welcome.pack(fill="x", padx=20, pady=(8, 8))

        _label(welcome, "Vítejte v ZeddiHub Tools!", 20, bold=True,
               color=t["primary"]).pack(padx=20, pady=(16, 4), anchor="w")
        _label(welcome, "Komplexní sada nástrojů pro správu herních serverů a optimalizaci hráčského nastavení.",
               12, color=t["text_dim"]).pack(padx=20, pady=(0, 6), anchor="w")

        links_row = ctk.CTkFrame(welcome, fg_color="transparent")
        links_row.pack(padx=20, pady=(4, 16), anchor="w")

        quick_links = [
            ("🌐 ZeddiHub Web", "https://zeddihub.eu"),
            ("📖 Wiki",          "https://wiki.zeddihub.eu"),
            ("💬 Discord",       "https://dsc.gg/zeddihub"),
            ("👨‍💻 ZeddiS.xyz",    "https://zeddis.xyz"),
        ]
        for label, url in quick_links:
            ctk.CTkButton(links_row, text=label, height=30, width=140,
                          fg_color=t["secondary"], hover_color=t["primary"],
                          font=ctk.CTkFont("Segoe UI", 11),
                          command=lambda u=url: __import__("webbrowser").open(u)
                          ).pack(side="left", padx=4)

        # Server status
        srv_header = ctk.CTkFrame(scroll, fg_color="transparent")
        srv_header.pack(fill="x", padx=20, pady=(8, 4))

        _label(srv_header, "📡  Status serverů", 16, bold=True,
               color=t["primary"]).pack(side="left", anchor="w")

        self.refresh_btn = ctk.CTkButton(
            srv_header, text="↻ Obnovit", height=28, width=90,
            fg_color=t["secondary"], hover_color=t["primary"],
            font=ctk.CTkFont("Segoe UI", 10),
            command=self._refresh_status
        )
        self.refresh_btn.pack(side="right")

        self.last_update_label = _label(srv_header, "", 9, color=t["text_dim"])
        self.last_update_label.pack(side="right", padx=8)

        # Server cards container
        self.servers_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.servers_frame.pack(fill="x", padx=20, pady=4)

        self.status_label = _label(scroll, "Načítám status serverů...", 11, color=t["text_dim"])
        self.status_label.pack(padx=20, pady=4, anchor="w")

        # Stats / Tools overview
        self._build_tools_overview(scroll)

    def _build_banner(self, parent):
        t = self.theme
        banner_frame = ctk.CTkFrame(parent, fg_color=t["card_bg"], corner_radius=10, height=100)
        banner_frame.pack(fill="x", padx=20, pady=(12, 8))
        banner_frame.pack_propagate(False)

        if PIL_OK and BANNER_PATH.exists():
            try:
                img = Image.open(BANNER_PATH)
                img.thumbnail((600, 80), Image.LANCZOS)
                self._banner_img = ImageTk.PhotoImage(img)
                tk.Label(banner_frame, image=self._banner_img,
                         bg=t["card_bg"]).pack(expand=True)
                return
            except Exception:
                pass

        # Fallback text banner
        _label(banner_frame, "ZeddiHub Tools", 26, bold=True,
               color=t["primary"]).pack(expand=True)

    def _build_tools_overview(self, parent):
        t = self.theme
        _label(parent, "⚡  Dostupné nástroje", 16, bold=True,
               color=t["primary"]).pack(padx=20, pady=(16, 6), anchor="w")

        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.pack(padx=20, fill="x")

        tools = [
            ("🎮 CS2 Nástroje",        "Crosshair, Viewmodel, Autoexec,\nPractice, Server CFG, RCON", "#1a6fbf"),
            ("🎯 CS:GO Nástroje",      "Crosshair, Viewmodel, Autoexec,\nServer CFG, DB Editor, RCON", "#c49b3c"),
            ("🦀 Rust Nástroje",       "Server Config, Plugin Manager,\nAnalyzér závislostí, RCON", "#cd3f1e"),
            ("🌍 Translator",          "Hromadný překlad .json/.txt/.lang\ndo 20+ jazyků najednou", "#4caf50"),
            ("⌨  Keybind Generátor",  "Vizuální klávesnice pro přiřazení\nbindů (CS2, CS:GO, Rust)", "#9c27b0"),
            ("🔗 Odkazy a Klienty",    "Steam, Discord, File Uploader,\nDNS správa, ZeddiHub Web", "#e07b39"),
        ]

        cols = 3
        for i, (name, desc, color) in enumerate(tools):
            card = ctk.CTkFrame(grid_frame, fg_color=t["card_bg"], corner_radius=8)
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")

            ctk.CTkLabel(card, text="●", font=ctk.CTkFont("Segoe UI", 10),
                         text_color=color).pack(padx=(12, 4), pady=(12, 2), anchor="w", side="top")
            _label(card, name, 12, bold=True, color=t["text"]).pack(padx=12, pady=(0, 4), anchor="w")
            _label(card, desc, 10, color=t["text_dim"]).pack(padx=12, pady=(0, 12), anchor="w")

        for c in range(cols):
            grid_frame.grid_columnconfigure(c, weight=1)

    def _start_status_refresh(self):
        self._refresh_status()
        # Auto-refresh every 60 seconds
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
            # Show placeholder / offline message
            self.after(0, self._update_server_cards, [])

    def _update_server_cards(self, servers: list):
        t = self.theme

        # Clear existing cards
        for w in self._server_widgets:
            w.destroy()
        self._server_widgets.clear()

        for w in self.servers_frame.winfo_children():
            w.destroy()

        if not servers:
            self.status_label.configure(
                text="⚠ Nelze načíst status serverů (offline nebo API nedostupné)."
            )
            # Show placeholder
            servers = [
                {"name": "ZeddiHub Rust #1",  "ip": "rust1.zeddihub.eu",  "port": 28015, "game": "rust",  "status": "unknown"},
                {"name": "ZeddiHub CS2 #1",   "ip": "cs2.zeddihub.eu",    "port": 27015, "game": "cs2",   "status": "unknown"},
                {"name": "ZeddiHub CS:GO #1", "ip": "csgo.zeddihub.eu",   "port": 27015, "game": "csgo",  "status": "unknown"},
            ]
        else:
            self.status_label.configure(text="")

        cols = min(len(servers), 3) if servers else 1
        for i, srv in enumerate(servers):
            card = self._make_server_card(self.servers_frame, srv, t)
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")
            self._server_widgets.append(card)

        for c in range(cols):
            self.servers_frame.grid_columnconfigure(c, weight=1)

        now = time.strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Aktualizováno: {now}")
        self.refresh_btn.configure(state="normal", text="↻ Obnovit")

        # Ping servers in background
        for srv in servers:
            threading.Thread(target=self._ping_server, args=(srv,), daemon=True).start()

    def _make_server_card(self, parent, srv: dict, t: dict) -> ctk.CTkFrame:
        status = srv.get("status", "unknown")
        game = srv.get("game", "default")

        status_colors = {"online": "#4caf50", "offline": "#f44336", "unknown": "#888888"}
        status_texts = {"online": "● Online", "offline": "● Offline", "unknown": "● Neznámo"}

        game_colors = {"rust": "#cd3f1e", "cs2": "#1a6fbf", "csgo": "#c49b3c"}
        game_color = game_colors.get(game, t["primary"])

        card = ctk.CTkFrame(parent, fg_color=t["card_bg"], corner_radius=8)

        # Header with game color
        header = ctk.CTkFrame(card, fg_color=game_color, corner_radius=0, height=4)
        header.pack(fill="x")
        header.pack_propagate(False)

        _label(card, srv.get("name", "Server"), 13, bold=True, color=t["text"]
               ).pack(padx=12, pady=(10, 2), anchor="w")

        ip_port = f"{srv.get('ip', '')}:{srv.get('port', '')}"
        _label(card, ip_port, 10, color=t["text_dim"]).pack(padx=12, anchor="w")

        status_lbl = ctk.CTkLabel(
            card, text=status_texts.get(status, "● Neznámo"),
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=status_colors.get(status, "#888888")
        )
        status_lbl.pack(padx=12, pady=(4, 6), anchor="w")

        # Store reference for ping update
        card._status_label = status_lbl
        card._srv_data = srv

        if srv.get("players") is not None:
            _label(card, f"Hráči: {srv.get('players', 0)}/{srv.get('max_players', '?')}",
                   10, color=t["text_dim"]).pack(padx=12, pady=(0, 6), anchor="w")

        # Copy IP button
        ctk.CTkButton(card, text="📋 Kopírovat IP", height=26, width=120,
                      fg_color=t["secondary"], hover_color=t["primary"],
                      font=ctk.CTkFont("Segoe UI", 9),
                      command=lambda ip=ip_port: self._copy_ip(ip)
                      ).pack(padx=12, pady=(0, 10), anchor="w")

        return card

    def _ping_server(self, srv: dict):
        """Try to ping the server and update its status card."""
        ip = srv.get("ip", "")
        port = srv.get("port", 0)
        if not ip or not port:
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            result = s.connect_ex((ip, int(port)))
            s.close()
            status = "online" if result == 0 else "offline"
        except Exception:
            status = "offline"

        # Update the card in UI thread
        def update():
            for w in self._server_widgets:
                if hasattr(w, '_srv_data') and w._srv_data.get("ip") == ip:
                    status_colors = {"online": "#4caf50", "offline": "#f44336"}
                    status_texts = {"online": "● Online", "offline": "● Offline"}
                    if hasattr(w, '_status_label'):
                        w._status_label.configure(
                            text=status_texts.get(status, "● Offline"),
                            text_color=status_colors.get(status, "#f44336")
                        )
        self.after(0, update)

    def _copy_ip(self, ip: str):
        self.clipboard_clear()
        self.clipboard_append(ip)
