"""
ZeddiHub Tools - PC Tools panel.
System info, DNS flush, network tools, shutdown timer.
"""

import os
import sys
import platform
import subprocess
import threading
import socket
import json
import urllib.request
import urllib.error
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from .. import icons

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

try:
    from ..locale import t
except ImportError:
    def t(key, **kw):
        return key


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#f0f0f0", **kw)


def _card(parent, theme):
    return ctk.CTkFrame(parent, fg_color=theme["card_bg"], corner_radius=8)


class PCToolsPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._shutdown_running = False
        self._build()

    def _build(self):
        t_theme = self.theme
        tab = ctk.CTkTabview(self, fg_color=t_theme["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=12, pady=12)

        tab.add(t("sys_info"))
        tab.add(t("dns_temp"))
        tab.add("📡 " + t("net_tools"))
        tab.add(t("utility"))

        self._build_sysinfo(tab.tab(t("sys_info")))
        self._build_dns_temp(tab.tab(t("dns_temp")))
        self._build_nettools(tab.tab("📡 " + t("net_tools")))
        self._build_utility(tab.tab(t("utility")))

    # ─── SYSTEM INFO ──────────────────────────────────────────────────────────

    def _build_sysinfo(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, t("sys_info"), 16, bold=True, color=th["primary"],
               image=icons.icon("laptop", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 8), anchor="w")

        if not PSUTIL_OK:
            warn = _card(scroll, th)
            warn.pack(fill="x", pady=6)
            _label(warn, "psutil není nainstalován — systémové info nedostupné.",
                   12, color=th["warning"],
                   image=icons.icon("triangle-exclamation", 14, th["warning"]),
                   compound="left").pack(padx=16, pady=(12, 4), anchor="w")
            _label(warn, "Klikni na tlačítko níže pro automatickou instalaci.",
                   11, color=th["text_dim"]).pack(padx=16, pady=(0, 4), anchor="w")
            ctk.CTkButton(warn, text="Nainstalovat psutil",
                          fg_color=th["primary"], hover_color=th["primary_hover"],
                          font=ctk.CTkFont("Segoe UI", 11), height=30,
                          command=self._install_psutil
                          ).pack(padx=16, pady=(0, 12), anchor="w")

        # Refresh button
        ctk.CTkButton(scroll, text="↻ " + t("refresh"),
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=30, width=120,
                      command=lambda: self._load_sysinfo(info_frame)
                      ).pack(anchor="e", padx=4, pady=(0, 6))

        info_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        info_frame.pack(fill="x")

        self._load_sysinfo(info_frame)

    def _install_psutil(self):
        import subprocess as sp
        import sys as _sys
        try:
            sp.check_call([_sys.executable, "-m", "pip", "install", "psutil"],
                          creationflags=0x08000000)  # CREATE_NO_WINDOW on Windows
            from tkinter import messagebox
            messagebox.showinfo("psutil nainstalován",
                                "psutil byl úspěšně nainstalován.\nRestartuj aplikaci pro aktivaci.")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Chyba instalace", f"Nepodařilo se nainstalovat psutil:\n{e}")

    def _load_sysinfo(self, frame: ctk.CTkFrame):
        for w in frame.winfo_children():
            w.destroy()
        th = self.theme

        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="x")

        data = self._gather_sysinfo()
        sections = [
            (t("os"), data["os"], th["primary"]),
            (t("cpu"), data["cpu"], "#5b9cf6"),
            (t("ram"), data["ram"], "#4ade80"),
            (t("disk"), data["disk"], "#fb923c"),
            (t("gpu"), data["gpu"], "#f87171"),
            (t("network"), data["network"], "#a78bfa"),
        ]

        cols = 2
        for i, (name, info_lines, color) in enumerate(sections):
            card = ctk.CTkFrame(grid, fg_color=th["card_bg"], corner_radius=8)
            card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="nsew")

            header = ctk.CTkFrame(card, fg_color=color, corner_radius=0, height=3)
            header.pack(fill="x")

            _label(card, name, 12, bold=True, color=color).pack(
                padx=14, pady=(10, 4), anchor="w")
            for line in info_lines:
                _label(card, line, 10, color=th["text_dim"]).pack(
                    padx=14, pady=1, anchor="w")
            ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1)

    def _gather_sysinfo(self) -> dict:
        data = {
            "os": [],
            "cpu": [],
            "ram": [],
            "disk": [],
            "gpu": [],
            "network": [],
        }

        # OS
        try:
            data["os"] = [
                f"System: {platform.system()} {platform.release()}",
                f"Version: {platform.version()[:60]}",
                f"Arch: {platform.machine()}",
                f"Node: {platform.node()}",
            ]
        except Exception:
            data["os"] = ["N/A"]

        # CPU
        try:
            cpu_info = [
                f"Name: {platform.processor()[:50] or 'N/A'}",
                f"Cores: {psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} logical" if PSUTIL_OK else "N/A",
                f"Usage: {psutil.cpu_percent(interval=0.1):.1f}%" if PSUTIL_OK else "N/A",
            ]
            # Try to get CPU freq
            if PSUTIL_OK:
                try:
                    freq = psutil.cpu_freq()
                    if freq:
                        cpu_info.append(f"Freq: {freq.current:.0f} MHz")
                except Exception:
                    pass
            data["cpu"] = cpu_info
        except Exception:
            data["cpu"] = ["N/A"]

        # RAM
        try:
            if PSUTIL_OK:
                mem = psutil.virtual_memory()
                data["ram"] = [
                    f"Total: {mem.total / 1e9:.2f} GB",
                    f"Used: {mem.used / 1e9:.2f} GB ({mem.percent:.1f}%)",
                    f"Free: {mem.available / 1e9:.2f} GB",
                ]
            else:
                data["ram"] = ["psutil required"]
        except Exception:
            data["ram"] = ["N/A"]

        # Disk (C: on Windows)
        try:
            if PSUTIL_OK:
                drive = "C:\\" if sys.platform == "win32" else "/"
                disk = psutil.disk_usage(drive)
                data["disk"] = [
                    f"Drive: {drive}",
                    f"Total: {disk.total / 1e9:.2f} GB",
                    f"Used: {disk.used / 1e9:.2f} GB ({disk.percent:.1f}%)",
                    f"Free: {disk.free / 1e9:.2f} GB",
                ]
            else:
                data["disk"] = ["psutil required"]
        except Exception as e:
            data["disk"] = [f"Error: {e}"]

        # GPU
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, timeout=5
            )
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and l.strip() != "Name"]
            data["gpu"] = lines[:3] if lines else ["N/A"]
        except Exception:
            data["gpu"] = ["N/A (wmic not available)"]

        # Network
        try:
            if PSUTIL_OK:
                net_lines = []
                addrs = psutil.net_if_addrs()
                for iface, addr_list in list(addrs.items())[:4]:
                    for addr in addr_list:
                        if addr.family == socket.AF_INET:
                            net_lines.append(f"{iface}: {addr.address}")
                counters = psutil.net_io_counters()
                net_lines.append(f"Sent: {counters.bytes_sent / 1e6:.1f} MB")
                net_lines.append(f"Recv: {counters.bytes_recv / 1e6:.1f} MB")
                data["network"] = net_lines[:6] if net_lines else ["N/A"]
            else:
                data["network"] = ["psutil required"]
        except Exception:
            data["network"] = ["N/A"]

        return data

    # ─── DNS & TEMP ───────────────────────────────────────────────────────────

    def _build_dns_temp(self, tab):
        th = self.theme
        self._dns_history: list[dict] = []  # {time, result, success}
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, t("dns_temp"), 16, bold=True, color=th["primary"],
               image=icons.icon("globe", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 10), anchor="w")

        # DNS Flush section
        dns_card = _card(scroll, th)
        dns_card.pack(fill="x", pady=6)

        _label(dns_card, t("dns_flush"), 13, bold=True, color=th["primary"],
               image=icons.icon("arrows-rotate", 15, th["primary"]), compound="left"
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(dns_card, "Vymaže DNS cache systému Windows (ipconfig /flushdns).",
               10, color=th["text_dim"]).pack(padx=14, anchor="w")

        ctk.CTkButton(dns_card, text=t("dns_flush_btn"),
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36,
                      command=self._flush_dns
                      ).pack(padx=14, pady=10, anchor="w")

        self._dns_output = ctk.CTkTextbox(dns_card, height=80,
                                           fg_color=th["secondary"], text_color=th["text"],
                                           font=ctk.CTkFont("Courier New", 10), state="disabled")
        self._dns_output.pack(fill="x", padx=14, pady=(0, 14))

        # DNS history
        hist_card = _card(scroll, th)
        hist_card.pack(fill="x", pady=6)

        hist_header = ctk.CTkFrame(hist_card, fg_color="transparent")
        hist_header.pack(fill="x", padx=14, pady=(12, 6))
        _label(hist_header, "Historie DNS flush", 13, bold=True, color=th["primary"],
               image=icons.icon("clipboard-list", 15, th["primary"]), compound="left"
               ).pack(side="left")
        ctk.CTkButton(hist_header, text=" Vymazat", height=26, width=80,
                      image=icons.icon("trash", 12, "#cccccc"), compound="left",
                      fg_color=th["secondary"], hover_color="#3a1a1a",
                      font=ctk.CTkFont("Segoe UI", 10),
                      command=self._clear_dns_history
                      ).pack(side="right")

        # Search + filter row
        ctrl_row = ctk.CTkFrame(hist_card, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=14, pady=(0, 6))

        self._dns_search_var = ctk.StringVar()
        self._dns_search_var.trace_add("write", lambda *_: self._refresh_dns_history())
        ctk.CTkEntry(ctrl_row, textvariable=self._dns_search_var,
                     placeholder_text="🔍 Hledat...",
                     fg_color=th["secondary"], text_color=th["text"],
                     font=ctk.CTkFont("Segoe UI", 11), height=30
                     ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._dns_filter_var = ctk.StringVar(value="Vše")
        filter_menu = ctk.CTkOptionMenu(
            ctrl_row, variable=self._dns_filter_var,
            values=["Vše", "Úspěch", "Chyba"],
            fg_color=th["secondary"], button_color=th["primary"],
            font=ctk.CTkFont("Segoe UI", 11), height=30, width=100,
            command=lambda _: self._refresh_dns_history()
        )
        filter_menu.pack(side="left")

        self._dns_hist_box = ctk.CTkTextbox(hist_card, height=120,
                                             fg_color=th["secondary"], text_color=th["text"],
                                             font=ctk.CTkFont("Courier New", 9), state="disabled")
        self._dns_hist_box.pack(fill="x", padx=14, pady=(0, 14))

        # Temp files section
        temp_card = _card(scroll, th)
        temp_card.pack(fill="x", pady=6)

        _label(temp_card, "🗑 " + t("temp_files"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(temp_card, "Čistí: %TEMP% (uživatelská) + C:\\Windows\\Temp (systémová)",
               10, color=th["text_dim"]).pack(padx=14, anchor="w")

        self._temp_info_var = ctk.StringVar(value="Klikněte na Skenovat pro analýzu temp složek.")
        _label(temp_card, "", 10, color=th["text_dim"], textvariable=self._temp_info_var
               ).pack(padx=14, anchor="w")

        btn_row = ctk.CTkFrame(temp_card, fg_color="transparent")
        btn_row.pack(padx=14, pady=10, anchor="w")

        ctk.CTkButton(btn_row, text=" " + t("scan_temp"),
                      image=icons.icon("magnifying-glass", 14, "#cccccc"), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._scan_temp
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text=" " + t("delete_temp"),
                      image=icons.icon("trash", 14, "#cccccc"), compound="left",
                      fg_color="#8b2020", hover_color="#6b1818",
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._clean_temp
                      ).pack(side="left")

        self._temp_log = ctk.CTkTextbox(temp_card, height=120,
                                         fg_color=th["secondary"], text_color=th["text"],
                                         font=ctk.CTkFont("Courier New", 9), state="disabled")
        self._temp_log.pack(fill="x", padx=14, pady=(0, 14))

    def _flush_dns(self):
        def run():
            import datetime
            success = False
            try:
                result = subprocess.run(
                    ["ipconfig", "/flushdns"],
                    capture_output=True, text=True,
                    encoding="cp852", errors="replace", timeout=15
                )
                output = result.stdout + result.stderr
                success = result.returncode == 0
            except Exception as e:
                output = f"Chyba: {e}"
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self._dns_history.append({"time": ts, "result": output.strip(), "success": success})
            self.after(0, self._set_textbox, self._dns_output, output)
            self.after(0, self._refresh_dns_history)

        threading.Thread(target=run, daemon=True).start()
        self._set_textbox(self._dns_output, "Spouštím ipconfig /flushdns...")

    def _refresh_dns_history(self):
        search = self._dns_search_var.get().lower()
        filt = self._dns_filter_var.get()
        lines = []
        for entry in reversed(self._dns_history):
            if filt == "Úspěch" and not entry["success"]:
                continue
            if filt == "Chyba" and entry["success"]:
                continue
            summary = entry["result"].replace("\n", " ")[:80]
            if search and search not in summary.lower() and search not in entry["time"]:
                continue
            status = "✓" if entry["success"] else "✗"
            lines.append(f"[{entry['time']}] {status} {summary}")
        text = "\n".join(lines) if lines else "(žádné záznamy)"
        self._set_textbox(self._dns_hist_box, text)

    def _clear_dns_history(self):
        self._dns_history.clear()
        self._refresh_dns_history()

    def _get_temp_dirs(self) -> list:
        dirs = []
        user_temp = Path(os.environ.get("TEMP", os.environ.get("TMP", "")))
        if user_temp and user_temp.exists():
            dirs.append(user_temp)
        win_temp = Path("C:/Windows/Temp")
        if win_temp.exists() and win_temp not in dirs:
            dirs.append(win_temp)
        return dirs

    def _scan_temp(self):
        def run():
            dirs = self._get_temp_dirs()
            total_files = 0
            total_size = 0
            log_lines = []
            for td in dirs:
                try:
                    files = [f for f in td.rglob("*") if f.is_file()]
                    size = sum(f.stat().st_size for f in files)
                    total_files += len(files)
                    total_size += size
                    log_lines.append(f"{td}")
                    log_lines.append(f"  Souborů: {len(files)}  |  Velikost: {size/1e6:.1f} MB")
                except Exception as e:
                    log_lines.append(f"{td}: Chyba — {e}")
            size_mb = total_size / 1e6
            self.after(0, self._temp_info_var.set,
                       f"Celkem: {total_files} souborů | {size_mb:.1f} MB ve {len(dirs)} složkách")
            self.after(0, self._set_textbox, self._temp_log, "\n".join(log_lines))

        threading.Thread(target=run, daemon=True).start()
        self._temp_info_var.set("Skenuji...")

    def _clean_temp(self):
        dirs = self._get_temp_dirs()
        dir_list = "\n".join(f"  • {d}" for d in dirs)
        if not messagebox.askyesno("Smazat Temp soubory",
                                    f"Opravdu smazat soubory v temp složkách?\n{dir_list}\n\nTato akce nelze vrátit."):
            return

        def run():
            import shutil
            deleted = 0
            errors = 0
            log_lines = []
            for temp_dir in dirs:
                log_lines.append(f"Mažu: {temp_dir}")
                try:
                    for item in temp_dir.iterdir():
                        try:
                            if item.is_file():
                                item.unlink()
                                deleted += 1
                            elif item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                                deleted += 1
                        except Exception as e:
                            errors += 1
                            log_lines.append(f"  Skip: {item.name} ({e})")
                except Exception as e:
                    log_lines.append(f"  Chyba: {e}")

            log_lines.append(f"\nSmazáno: {deleted} položek | Chyby: {errors}")
            self.after(0, self._set_textbox, self._temp_log, "\n".join(log_lines))
            self.after(0, self._temp_info_var.set, f"Hotovo. Smazáno: {deleted} | Chyby: {errors}")

        threading.Thread(target=run, daemon=True).start()
        self._set_textbox(self._temp_log, "Mažu temp soubory...")

    # ─── NETWORK TOOLS ────────────────────────────────────────────────────────

    def _build_nettools(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "📡 " + t("net_tools"), 16, bold=True, color=th["primary"]
               ).pack(padx=4, pady=(4, 10), anchor="w")

        # Ping tool
        ping_card = _card(scroll, th)
        ping_card.pack(fill="x", pady=6)

        _label(ping_card, "🏓 " + t("ping_tool"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        ping_row = ctk.CTkFrame(ping_card, fg_color="transparent")
        ping_row.pack(fill="x", padx=14, pady=(0, 6))

        self._ping_entry = ctk.CTkEntry(ping_row,
                                         placeholder_text="hostname nebo IP (např. google.com)",
                                         fg_color=th["secondary"], text_color=th["text"],
                                         font=ctk.CTkFont("Segoe UI", 12), height=36)
        self._ping_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._ping_entry.insert(0, "google.com")

        ctk.CTkButton(ping_row, text=t("ping_btn"),
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36, width=80,
                      command=self._run_ping
                      ).pack(side="left")

        self._ping_output = ctk.CTkTextbox(ping_card, height=120,
                                            fg_color=th["secondary"], text_color=th["text"],
                                            font=ctk.CTkFont("Courier New", 10), state="disabled")
        self._ping_output.pack(fill="x", padx=14, pady=(0, 14))

        # IP Info
        ip_card = _card(scroll, th)
        ip_card.pack(fill="x", pady=6)

        _label(ip_card, "🌍 " + t("ip_info"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        ip_row = ctk.CTkFrame(ip_card, fg_color="transparent")
        ip_row.pack(fill="x", padx=14, pady=(0, 6))

        self._ip_entry = ctk.CTkEntry(ip_row,
                                       placeholder_text="IP adresa (prázdné = vaše IP)",
                                       fg_color=th["secondary"], text_color=th["text"],
                                       font=ctk.CTkFont("Segoe UI", 12), height=36)
        self._ip_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(ip_row, text=t("ip_lookup"),
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36, width=100,
                      command=self._run_ip_lookup
                      ).pack(side="left")

        self._ip_output = ctk.CTkTextbox(ip_card, height=140,
                                          fg_color=th["secondary"], text_color=th["text"],
                                          font=ctk.CTkFont("Courier New", 10), state="disabled")
        self._ip_output.pack(fill="x", padx=14, pady=(0, 14))

        # Port checker
        port_card = _card(scroll, th)
        port_card.pack(fill="x", pady=6)

        _label(port_card, "🔌 " + t("port_checker"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        port_row = ctk.CTkFrame(port_card, fg_color="transparent")
        port_row.pack(fill="x", padx=14, pady=(0, 6))

        self._port_host_entry = ctk.CTkEntry(port_row, placeholder_text="host",
                                              fg_color=th["secondary"], text_color=th["text"],
                                              font=ctk.CTkFont("Segoe UI", 12), height=36, width=200)
        self._port_host_entry.pack(side="left", padx=(0, 8))
        self._port_host_entry.insert(0, "localhost")

        self._port_num_entry = ctk.CTkEntry(port_row, placeholder_text="port",
                                             fg_color=th["secondary"], text_color=th["text"],
                                             font=ctk.CTkFont("Segoe UI", 12), height=36, width=80)
        self._port_num_entry.pack(side="left", padx=(0, 8))
        self._port_num_entry.insert(0, "80")

        self._port_result_label = _label(port_card, "", 11, color=th["text_dim"])
        self._port_result_label.pack(padx=14, pady=(0, 4), anchor="w")

        ctk.CTkButton(port_row, text=t("check_port"),
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36,
                      command=self._check_port
                      ).pack(side="left")

    def _run_ping(self):
        host = self._ping_entry.get().strip()
        if not host:
            return

        def run():
            try:
                result = subprocess.run(
                    ["ping", "-n", "4", host],
                    capture_output=True, text=True,
                    encoding="cp852", errors="replace", timeout=20
                )
                output = result.stdout or result.stderr
            except Exception as e:
                output = f"Chyba: {e}"
            self.after(0, self._set_textbox, self._ping_output, output)

        threading.Thread(target=run, daemon=True).start()
        self._set_textbox(self._ping_output, f"Pinguju {host}...")

    def _run_ip_lookup(self):
        ip = self._ip_entry.get().strip()
        url = f"http://ip-api.com/json/{ip}" if ip else "http://ip-api.com/json/"

        def run():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools/1.0.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode())

                lines = [
                    f"IP:       {data.get('query', 'N/A')}",
                    f"Country:  {data.get('country', 'N/A')} ({data.get('countryCode', '')})",
                    f"Region:   {data.get('regionName', 'N/A')}",
                    f"City:     {data.get('city', 'N/A')}",
                    f"ZIP:      {data.get('zip', 'N/A')}",
                    f"ISP:      {data.get('isp', 'N/A')}",
                    f"AS:       {data.get('as', 'N/A')}",
                    f"Lat/Lon:  {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}",
                    f"Timezone: {data.get('timezone', 'N/A')}",
                ]
                output = "\n".join(lines)
            except Exception as e:
                output = f"Chyba: {e}"
            self.after(0, self._set_textbox, self._ip_output, output)

        threading.Thread(target=run, daemon=True).start()
        self._set_textbox(self._ip_output, f"Vyhledávám {ip or 'vaši IP'}...")

    def _check_port(self):
        host = self._port_host_entry.get().strip()
        try:
            port = int(self._port_num_entry.get().strip())
        except ValueError:
            self._port_result_label.configure(text="Neplatné číslo portu.", text_color=self.theme["error"])
            return

        def run():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                result = s.connect_ex((host, port))
                s.close()
                if result == 0:
                    self.after(0, self._port_result_label.configure,
                               {"text": f"✅ {t('port_open')}: {host}:{port}", "text_color": self.theme["success"]})
                else:
                    self.after(0, self._port_result_label.configure,
                               {"text": f"❌ {t('port_closed')}: {host}:{port}", "text_color": self.theme["error"]})
            except Exception as e:
                self.after(0, self._port_result_label.configure,
                           {"text": f"Chyba: {e}", "text_color": self.theme["warning"]})

        self._port_result_label.configure(text="Kontroluji...", text_color=self.theme["text_dim"])
        threading.Thread(target=run, daemon=True).start()

    # ─── UTILITY ──────────────────────────────────────────────────────────────

    def _build_utility(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, t("utility"), 16, bold=True, color=th["primary"],
               image=icons.icon("wrench", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 10), anchor="w")

        # Shutdown timer
        shutdown_card = _card(scroll, th)
        shutdown_card.pack(fill="x", pady=6)

        _label(shutdown_card, "⏱ " + t("shutdown_timer"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        row = ctk.CTkFrame(shutdown_card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 6))

        _label(row, t("minutes") + ":", 11, color=th["text_dim"]).pack(side="left", padx=(0, 8))

        self._shutdown_minutes = ctk.CTkEntry(row,
                                               fg_color=th["secondary"], text_color=th["text"],
                                               font=ctk.CTkFont("Segoe UI", 12), height=34, width=80)
        self._shutdown_minutes.pack(side="left", padx=(0, 12))
        self._shutdown_minutes.insert(0, "30")

        ctk.CTkButton(row, text=" " + t("run"),
                      image=icons.icon("play", 14, "#cccccc"), compound="left",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 11, "bold"), height=34,
                      command=self._start_shutdown
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(row, text=" " + t("shutdown_cancel"),
                      image=icons.icon("xmark", 14, "#cccccc"), compound="left",
                      fg_color="#8b2020", hover_color="#6b1818",
                      font=ctk.CTkFont("Segoe UI", 11), height=34,
                      command=self._cancel_shutdown
                      ).pack(side="left")

        self._shutdown_status = _label(shutdown_card, "", 10, color=th["text_dim"])
        self._shutdown_status.pack(padx=14, pady=(0, 12), anchor="w")

        # Process list
        proc_card = _card(scroll, th)
        proc_card.pack(fill="x", pady=6)

        _label(proc_card, "📊 " + t("process_list"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        ctk.CTkButton(proc_card, text="↻ " + t("refresh"),
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=30, width=100,
                      command=lambda: self._load_processes(proc_list)
                      ).pack(padx=14, pady=(0, 6), anchor="w")

        proc_list = ctk.CTkTextbox(proc_card, height=200,
                                    fg_color=th["secondary"], text_color=th["text"],
                                    font=ctk.CTkFont("Courier New", 10), state="disabled")
        proc_list.pack(fill="x", padx=14, pady=(0, 14))

        self._load_processes(proc_list)

    def _start_shutdown(self):
        try:
            minutes = int(self._shutdown_minutes.get().strip())
            seconds = minutes * 60
        except ValueError:
            self._shutdown_status.configure(text="Zadejte platný počet minut.", text_color=self.theme["error"])
            return

        try:
            subprocess.run(["shutdown", "/s", "/t", str(seconds)], check=True)
            self._shutdown_status.configure(
                text=f"✅ Vypnutí naplánováno za {minutes} minut.",
                text_color=self.theme["success"])
        except Exception as e:
            self._shutdown_status.configure(text=f"Chyba: {e}", text_color=self.theme["error"])

    def _cancel_shutdown(self):
        try:
            subprocess.run(["shutdown", "/a"], check=True)
            self._shutdown_status.configure(
                text="✅ Vypnutí zrušeno.", text_color=self.theme["success"])
        except Exception as e:
            self._shutdown_status.configure(
                text=f"Chyba: {e}", text_color=self.theme["warning"])

    def _load_processes(self, textbox: ctk.CTkTextbox):
        def run():
            if not PSUTIL_OK:
                self.after(0, self._set_textbox, textbox, "psutil není nainstalován. pip install psutil")
                return
            try:
                procs = []
                for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                    try:
                        procs.append({
                            "pid": p.info["pid"],
                            "name": p.info["name"],
                            "cpu": p.info["cpu_percent"] or 0.0,
                            "mem": (p.info["memory_info"].rss // 1024 // 1024) if p.info["memory_info"] else 0,
                        })
                    except Exception:
                        pass

                procs.sort(key=lambda x: x["cpu"], reverse=True)
                lines = [f"{'PID':>7}  {'CPU%':>6}  {'MEM MB':>7}  {'Name':<30}"]
                lines.append("-" * 55)
                for p in procs[:20]:
                    lines.append(f"{p['pid']:>7}  {p['cpu']:>6.1f}  {p['mem']:>7}  {p['name']:<30}")

                self.after(0, self._set_textbox, textbox, "\n".join(lines))
            except Exception as e:
                self.after(0, self._set_textbox, textbox, f"Chyba: {e}")

        threading.Thread(target=run, daemon=True).start()
        self._set_textbox(textbox, "Načítám procesy...")

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    def _set_textbox(self, textbox: ctk.CTkTextbox, text: str):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")
