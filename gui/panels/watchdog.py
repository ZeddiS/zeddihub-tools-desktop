"""
ZeddiHub Tools - Server Watchdog panel.
Monitors game servers in the background and alerts when they go offline/online.
"""

import time
import socket
import struct
import threading
import json
import urllib.request
import tkinter as tk
import customtkinter as ctk
from typing import Optional

try:
    from ..locale import t
except ImportError:
    def t(key, **kw): return key

from .. import icons

A2S_INFO = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"
SERVER_STATUS_URL = "https://zeddihub.eu/tools/data/servers.json"


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#f0f0f0", **kw)


def _ping_server(ip: str, port: int, timeout: float = 3.0) -> tuple[bool, int]:
    """Returns (is_online, ping_ms). Uses A2S for game servers, fallback to TCP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        start = time.time()
        sock.sendto(A2S_INFO, (ip, int(port)))
        data, _ = sock.recvfrom(4096)
        sock.close()
        ping_ms = int((time.time() - start) * 1000)
        return True, ping_ms
    except Exception:
        pass
    # TCP fallback
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, int(port)))
        sock.close()
        ping_ms = int((time.time() - start) * 1000)
        return True, ping_ms
    except Exception:
        return False, 0


class WatchdogPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._monitors: list[dict] = []  # {name, ip, port, game, online, ping, consecutive_failures}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._interval = 30  # seconds
        self._build()
        self._load_servers()

    def _build(self):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color=th["content_bg"])
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        # Header
        header_row = ctk.CTkFrame(scroll, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(16, 8))

        _label(header_row, "Server Watchdog", 20, bold=True,
               color=th["primary"],
               image=icons.icon("bell", 22, th["primary"]), compound="left").pack(side="left")

        self._status_dot = _label(header_row, "⬤ Neaktivní", 11,
                                   color=th["text_dim"])
        self._status_dot.pack(side="right", padx=8)

        # Controls
        ctrl_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
        ctrl_card.pack(fill="x", padx=20, pady=6)

        _label(ctrl_card, "Nastavení", 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        row1 = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(0, 6))

        _label(row1, "Interval kontroly (s):", 11, color=th["text_dim"]).pack(side="left")
        self._interval_var = ctk.StringVar(value=str(self._interval))
        ctk.CTkEntry(row1, textvariable=self._interval_var,
                     fg_color=th["secondary"], text_color=th["text"],
                     font=ctk.CTkFont("Segoe UI", 11), width=60, height=28
                     ).pack(side="left", padx=8)

        btn_row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        btn_row.pack(padx=14, pady=(0, 14), anchor="w")

        self._start_btn = ctk.CTkButton(
            btn_row, text=" Spustit monitoring",
            fg_color=th["primary"], hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36,
            image=icons.icon("play", 14, "#ffffff"), compound="left",
            command=self._start_monitoring
        )
        self._start_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = ctk.CTkButton(
            btn_row, text=" Zastavit",
            fg_color=th["secondary"], hover_color="#6b1818",
            font=ctk.CTkFont("Segoe UI", 12), height=36,
            image=icons.icon("stop", 14, "#f87171"), compound="left",
            state="disabled",
            command=self._stop_monitoring
        )
        self._stop_btn.pack(side="left")

        # Add custom server
        add_card = ctk.CTkFrame(scroll, fg_color=th["card_bg"], corner_radius=8)
        add_card.pack(fill="x", padx=20, pady=6)

        _label(add_card, " Přidat server", 13, bold=True, color=th["primary"],
               image=icons.icon("plus-circle", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")

        add_row = ctk.CTkFrame(add_card, fg_color="transparent")
        add_row.pack(fill="x", padx=14, pady=(0, 14))

        self._add_name = ctk.CTkEntry(add_row, placeholder_text="Název",
                                       fg_color=th["secondary"], text_color=th["text"],
                                       font=ctk.CTkFont("Segoe UI", 11), height=32, width=160)
        self._add_name.pack(side="left", padx=(0, 6))

        self._add_ip = ctk.CTkEntry(add_row, placeholder_text="IP adresa",
                                     fg_color=th["secondary"], text_color=th["text"],
                                     font=ctk.CTkFont("Segoe UI", 11), height=32, width=160)
        self._add_ip.pack(side="left", padx=(0, 6))

        self._add_port = ctk.CTkEntry(add_row, placeholder_text="Port",
                                       fg_color=th["secondary"], text_color=th["text"],
                                       font=ctk.CTkFont("Segoe UI", 11), height=32, width=70)
        self._add_port.pack(side="left", padx=(0, 6))
        self._add_port.insert(0, "27015")

        ctk.CTkButton(add_row, text="",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=32, width=40,
                      image=icons.icon("plus", 14, "#ffffff"), compound="left",
                      command=self._add_server
                      ).pack(side="left")

        # Servers list
        _label(scroll, " Monitorované servery", 15, bold=True,
               color=th["primary"],
               image=icons.icon("satellite-dish", 17, th["primary"]), compound="left"
               ).pack(padx=20, pady=(12, 4), anchor="w")

        self._servers_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._servers_frame.pack(fill="x", padx=20, pady=4)

        # Log
        _label(scroll, "Log", 13, bold=True, color=th["primary"],
               image=icons.icon("clipboard-list", 15, th["primary"]), compound="left"
               ).pack(padx=20, pady=(12, 4), anchor="w")

        self._log_box = ctk.CTkTextbox(scroll, height=150,
                                        fg_color=th["card_bg"], text_color=th["text"],
                                        font=ctk.CTkFont("Courier New", 9), state="disabled")
        self._log_box.pack(fill="x", padx=20, pady=(0, 16))

    def _load_servers(self):
        """Load servers from the web API and populate the list."""
        def _fetch():
            try:
                req = urllib.request.Request(
                    SERVER_STATUS_URL,
                    headers={"User-Agent": "ZeddiHubTools/1.4.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    servers = json.loads(resp.read().decode())
                self.after(0, self._populate_servers, servers)
            except Exception:
                # Add demo server
                self.after(0, self._populate_servers, [
                    {"name": "ZeddiHub Rust #1", "ip": "rust1.zeddihub.eu", "port": 28015, "game": "rust"},
                ])

        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_servers(self, servers: list):
        self._monitors = []
        for srv in servers:
            self._monitors.append({
                "name": srv.get("name", "Server"),
                "ip": srv.get("ip", ""),
                "port": int(srv.get("port", 27015)),
                "game": srv.get("game", "cs2"),
                "online": None,
                "ping": 0,
                "consecutive_failures": 0,
            })
        self._render_server_cards()

    def _add_server(self):
        name = self._add_name.get().strip() or "Custom Server"
        ip = self._add_ip.get().strip()
        port_str = self._add_port.get().strip()
        if not ip:
            return
        try:
            port = int(port_str)
        except ValueError:
            port = 27015
        self._monitors.append({
            "name": name, "ip": ip, "port": port, "game": "cs2",
            "online": None, "ping": 0, "consecutive_failures": 0,
        })
        self._add_name.delete(0, "end")
        self._add_ip.delete(0, "end")
        self._render_server_cards()

    def _render_server_cards(self):
        for w in self._servers_frame.winfo_children():
            w.destroy()

        th = self.theme
        if not self._monitors:
            _label(self._servers_frame, "Žádné servery. Přidejte server výše.",
                   11, color=th["text_dim"]).pack(padx=8, pady=16)
            return

        for i, mon in enumerate(self._monitors):
            card = self._make_server_card(self._servers_frame, mon, i)
            card.pack(fill="x", pady=4)

    def _make_server_card(self, parent, mon: dict, idx: int) -> ctk.CTkFrame:
        th = self.theme
        game_colors = {"rust": "#f97316", "cs2": "#5b9cf6", "csgo": "#fbbf24"}
        game_color = game_colors.get(mon.get("game", ""), th["primary"])

        card = ctk.CTkFrame(parent, fg_color=th["card_bg"], corner_radius=8)

        top_bar = ctk.CTkFrame(card, fg_color=game_color, height=3, corner_radius=0)
        top_bar.pack(fill="x")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)

        online = mon.get("online")
        if online is True:
            dot = "● " ; dot_color = "#4ade80"
        elif online is False:
            dot = "● "; dot_color = "#f87171"
        else:
            dot = "● "; dot_color = "#888888"

        status_lbl = ctk.CTkLabel(row, text=dot,
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   text_color=dot_color, width=20)
        status_lbl.pack(side="left")
        mon["_status_lbl"] = status_lbl

        info_col = ctk.CTkFrame(row, fg_color="transparent")
        info_col.pack(side="left", fill="x", expand=True, padx=(4, 0))

        _label(info_col, mon["name"], 13, bold=True, color=th["text"]).pack(anchor="w")
        ping_text = f"{mon['ip']}:{mon['port']}"
        if online is True and mon["ping"]:
            ping_text += f"  —  {mon['ping']} ms"
        ping_lbl = _label(info_col, ping_text, 10, color=th["text_dim"])
        ping_lbl.pack(anchor="w")
        mon["_ping_lbl"] = ping_lbl

        ctk.CTkButton(row, text="", width=28, height=28,
                      fg_color=th["secondary"], hover_color="#6b1818",
                      font=ctk.CTkFont("Segoe UI", 11), text_color="#888888",
                      image=icons.icon("times", 11, "#888888"), compound="left",
                      command=lambda i=idx: self._remove_server(i)
                      ).pack(side="right")

        return card

    def _remove_server(self, idx: int):
        if 0 <= idx < len(self._monitors):
            self._monitors.pop(idx)
            self._render_server_cards()

    # ── Monitoring loop ───────────────────────────────────────────────────────

    def _start_monitoring(self):
        try:
            self._interval = max(5, int(self._interval_var.get()))
        except ValueError:
            self._interval = 30
        if not self._monitors:
            return
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_dot.configure(text="⬤ Aktivní", text_color="#4ade80")
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self._log("Monitoring spuštěn.")

    def _stop_monitoring(self):
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._status_dot.configure(text="⬤ Neaktivní", text_color=self.theme["text_dim"])
        self._log("Monitoring zastaven.")

    def _monitor_loop(self):
        while self._running:
            for mon in self._monitors:
                if not self._running:
                    break
                was_online = mon.get("online")
                online, ping = _ping_server(mon["ip"], mon["port"])
                mon["online"] = online
                mon["ping"] = ping
                if online:
                    mon["consecutive_failures"] = 0
                else:
                    mon["consecutive_failures"] = mon.get("consecutive_failures", 0) + 1

                # Alert on status change
                if was_online is True and not online:
                    self.after(0, self._alert_offline, mon)
                elif was_online is False and online:
                    self.after(0, self._alert_online, mon)

                self.after(0, self._update_card_status, mon)

            # Sleep in small increments so we can stop cleanly
            for _ in range(self._interval * 2):
                if not self._running:
                    break
                time.sleep(0.5)

    def _update_card_status(self, mon: dict):
        lbl = mon.get("_status_lbl")
        ping_lbl = mon.get("_ping_lbl")
        if lbl:
            color = "#4ade80" if mon["online"] else "#f87171"
            lbl.configure(text_color=color)
        if ping_lbl:
            txt = f"{mon['ip']}:{mon['port']}"
            if mon["online"] and mon["ping"]:
                txt += f"  —  {mon['ping']} ms"
            elif not mon["online"] and mon.get("consecutive_failures", 0) > 1:
                txt += f"  —  offline ({mon['consecutive_failures']}× za sebou)"
            ping_lbl.configure(text=txt)

    def _alert_offline(self, mon: dict):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log(f"[{ts}] ⚠ OFFLINE: {mon['name']} ({mon['ip']}:{mon['port']})")

    def _alert_online(self, mon: dict):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log(f"[{ts}] ✓ ONLINE:  {mon['name']} ({mon['ip']}:{mon['port']}) — {mon['ping']} ms")

    def _log(self, text: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", text + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def destroy(self):
        self._running = False
        super().destroy()
