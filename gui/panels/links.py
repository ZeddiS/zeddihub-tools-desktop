"""
ZeddiHub Tools - Links, Credits & ZeddiS-Client features panel.
Includes: DNS management, file uploader, social links.
"""

import webbrowser
import tkinter as tk
import customtkinter as ctk

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

from pathlib import Path

from .. import icons

LOGO_PATH = Path(__file__).parent.parent.parent / "assets" / "logo.png"


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#ffffff", **kw)


def _link_btn(parent, text, url, theme, icon="globe", width=240):
    _img = icons.icon(icon, 14, theme["text_dim"]) if icon else None
    return ctk.CTkButton(
        parent, text=f"  {text}",
        **( {"image": _img, "compound": "left"} if _img else {} ),
        command=lambda: webbrowser.open(url),
        fg_color=theme["secondary"], hover_color=theme["primary"],
        text_color=theme["text"], anchor="w",
        font=ctk.CTkFont("Segoe UI", 12),
        width=width, height=40
    )


class LinksPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        t = self.theme
        tab = ctk.CTkTabview(self, fg_color=t["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("Rychlé odkazy")
        tab.add("DNS Správa")
        tab.add("📁 File Uploader")
        tab.add("ℹ Credits")

        self._build_links(tab.tab("Rychlé odkazy"))
        self._build_dns(tab.tab("DNS Správa"))
        self._build_uploader(tab.tab("📁 File Uploader"))
        self._build_credits(tab.tab("ℹ Credits"))

    def _build_links(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        _label(scroll, "Rychlé Odkazy", 18, bold=True, color=t["primary"]).pack(anchor="w", pady=(0, 16))

        sections = {
            ("ZeddiHub Komunita", "house"): [
                ("ZeddiHub Web",          "https://zeddihub.eu",              "globe"),
                ("ZeddiWiki – Návody",    "https://wiki.zeddihub.eu",         "book"),
                ("Discord Server",         "https://dsc.gg/zeddihub",          "discord"),
                ("GitHub Organizace",      "https://github.com/ZeddiS",        "github"),
            ],
            ("ZeddiS – Autor", "user"): [
                ("Portfolio / Web",        "https://zeddis.xyz",               "user"),
                ("Steam Profil",           "https://steamcommunity.com/profiles/76561198085060456", "gamepad"),
                ("GitHub Profil",          "https://github.com/ZeddiS",        "github"),
            ],
            ("Nástroje a Soubory", "tools"): [
                ("File Uploader",          "https://files.zeddihub.eu/uploader/", "upload"),
                ("Files CDN",              "https://files.zeddihub.eu",        "hdd"),
                ("ZeddiHub Tools Releases","https://github.com/ZeddiS/zeddihub-tools-desktop/releases", "box-open"),
            ],
            ("Herní Servery", "gamepad"): [
                ("Rust Server – connect",  "steam://connect/rust1.zeddihub.eu:28015", "puzzle-piece"),
                ("CS2 Server – connect",   "steam://connect/cs2.zeddihub.eu:27015",   "crosshairs"),
            ],
        }

        for (section_name, section_icon), links in sections.items():
            sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            sec.pack(fill="x", pady=6)
            sec_icon_img = icons.icon(section_icon, 15, t["primary"])
            _label(sec, section_name, 13, bold=True, color=t["primary"],
                   **({"image": sec_icon_img, "compound": "left"} if sec_icon_img else {})
                   ).pack(padx=14, pady=(10, 6), anchor="w")

            for label, url, icon in links:
                _link_btn(sec, label, url, t, icon=icon, width=380).pack(
                    padx=14, pady=3, anchor="w")
            ctk.CTkFrame(sec, fg_color="transparent", height=8).pack()

    def _build_dns(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "DNS Správa", 18, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Správa DNS záznamů pro herní servery a webové služby ZeddiHub.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 12))

        # DNS Lookup tool
        lookup_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        lookup_frame.pack(fill="x", pady=6)
        _label(lookup_frame, " DNS Lookup", 13, bold=True, color=t["text_dim"],
               image=icons.icon("search", 15, t["text_dim"]), compound="left").pack(
            padx=12, pady=(10, 6), anchor="w")

        row = ctk.CTkFrame(lookup_frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 8))

        self.dns_entry = ctk.CTkEntry(row, placeholder_text="zeddihub.eu nebo IP adresa...",
                                      fg_color=t["secondary"], text_color=t["text"],
                                      font=ctk.CTkFont("Courier New", 12))
        self.dns_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.dns_entry.bind("<Return>", lambda _: self._dns_lookup())

        ctk.CTkButton(row, text=" Vyhledat", height=36, width=110,
                      image=icons.icon("search", 13, "#ffffff"), compound="left",
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._dns_lookup).pack(side="left")

        self.dns_result = ctk.CTkTextbox(lookup_frame, height=160,
                                         font=ctk.CTkFont("Courier New", 11),
                                         fg_color=t["secondary"], text_color=t["text"],
                                         state="disabled")
        self.dns_result.pack(fill="x", padx=12, pady=(0, 12))

        # Ping tool
        ping_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        ping_frame.pack(fill="x", pady=6)
        _label(ping_frame, " Port Checker / Ping", 13, bold=True, color=t["text_dim"],
               image=icons.icon("satellite-dish", 15, t["text_dim"]), compound="left").pack(
            padx=12, pady=(10, 6), anchor="w")

        ping_row = ctk.CTkFrame(ping_frame, fg_color="transparent")
        ping_row.pack(fill="x", padx=12, pady=(0, 4))

        self.ping_host = ctk.CTkEntry(ping_row, placeholder_text="IP nebo doména",
                                      fg_color=t["secondary"], text_color=t["text"],
                                      font=ctk.CTkFont("Courier New", 11), width=220)
        self.ping_host.pack(side="left", padx=(0, 6))

        self.ping_port = ctk.CTkEntry(ping_row, placeholder_text="Port",
                                      fg_color=t["secondary"], text_color=t["text"],
                                      font=ctk.CTkFont("Courier New", 11), width=80)
        self.ping_port.pack(side="left", padx=(0, 6))

        ctk.CTkButton(ping_row, text="Zkontrolovat", height=34, width=120,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._check_port).pack(side="left")

        self.ping_result = _label(ping_frame, "", 11, color=t["text"])
        self.ping_result.pack(padx=12, pady=(4, 12), anchor="w")

        # Common ZeddiHub DNS
        dns_quick = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        dns_quick.pack(fill="x", pady=6)
        _label(dns_quick, " Rychlé vyhledávání ZeddiHub domén", 12, bold=True, color=t["text_dim"],
               image=icons.icon("bolt", 14, t["text_dim"]), compound="left"
               ).pack(padx=12, pady=(10, 6), anchor="w")

        for domain in ["zeddihub.eu", "wiki.zeddihub.eu", "files.zeddihub.eu", "zeddis.xyz"]:
            ctk.CTkButton(dns_quick, text=domain, height=30, anchor="w",
                          fg_color=t["secondary"], hover_color=t["primary"],
                          font=ctk.CTkFont("Courier New", 11),
                          command=lambda d=domain: self._quick_dns(d)
                          ).pack(padx=12, pady=3, anchor="w", fill="x")
        ctk.CTkFrame(dns_quick, fg_color="transparent", height=8).pack()

    def _dns_lookup(self):
        import socket, threading
        host = self.dns_entry.get().strip()
        if not host:
            return

        def lookup():
            try:
                info = socket.getaddrinfo(host, None)
                ips = list(set(r[4][0] for r in info))
                try:
                    hostname = socket.gethostbyaddr(ips[0])[0]
                except Exception:
                    hostname = "N/A"
                result = f"Host: {host}\n"
                result += f"IP adresy: {', '.join(ips)}\n"
                result += f"Reverse DNS: {hostname}\n"
                self.after(0, self._set_dns_result, result)
            except Exception as e:
                self.after(0, self._set_dns_result, f"Chyba: {e}")

        threading.Thread(target=lookup, daemon=True).start()
        self._set_dns_result(f"Vyhledávám {host}...")

    def _set_dns_result(self, text: str):
        self.dns_result.configure(state="normal")
        self.dns_result.delete("1.0", "end")
        self.dns_result.insert("end", text)
        self.dns_result.configure(state="disabled")

    def _check_port(self):
        import socket, threading
        host = self.ping_host.get().strip()
        try:
            port = int(self.ping_port.get().strip())
        except ValueError:
            self.ping_result.configure(text="! Neplatný port", text_color="#f44336")
            return

        def check():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                import time
                start = time.time()
                result = s.connect_ex((host, port))
                elapsed = int((time.time() - start) * 1000)
                s.close()
                if result == 0:
                    self.after(0, self.ping_result.configure,
                               {"text": f"✓ {host}:{port} je OTEVŘENÝ ({elapsed} ms)",
                                "text_color": "#4caf50"})
                else:
                    self.after(0, self.ping_result.configure,
                               {"text": f"✗ {host}:{port} je ZAVŘENÝ / nedostupný",
                                "text_color": "#f44336"})
            except Exception as e:
                self.after(0, self.ping_result.configure,
                           {"text": f"! Chyba: {e}", "text_color": "#f44336"})

        self.ping_result.configure(text=f"Kontroluji {host}:{port}...", text_color="#888888")
        threading.Thread(target=check, daemon=True).start()

    def _quick_dns(self, domain: str):
        self.dns_entry.delete(0, "end")
        self.dns_entry.insert(0, domain)
        self._dns_lookup()

    def _build_uploader(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "File Uploader", 18, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Nahrávání souborů na ZeddiHub CDN (files.zeddihub.eu).",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 12))

        # Quick open button
        card = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        card.pack(fill="x", pady=6)

        _label(card, " Webový uploader", 14, bold=True, color=t["text"],
               image=icons.icon("globe", 16, t["text"]), compound="left").pack(
            padx=16, pady=(16, 4), anchor="w")
        _label(card, "Otevře se webová stránka nahrávání souborů ve vašem prohlížeči.",
               11, color=t["text_dim"]).pack(padx=16, pady=(0, 8), anchor="w")
        ctk.CTkButton(card, text=" Otevřít File Uploader",
                      image=icons.icon("external-link-alt", 14, "#ffffff"), compound="left",
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"), height=42,
                      command=lambda: webbrowser.open("https://files.zeddihub.eu/uploader/")
                      ).pack(padx=16, pady=(0, 16), fill="x")

        # Info
        info = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        info.pack(fill="x", pady=6)
        _label(info, " Informace o CDN", 13, bold=True, color=t["text_dim"],
               image=icons.icon("info-circle", 15, t["text_dim"]), compound="left").pack(
            padx=12, pady=(10, 6), anchor="w")

        info_items = [
            ("URL CDN",     "https://files.zeddihub.eu"),
            ("Uploader",    "https://files.zeddihub.eu/uploader/"),
            ("Správce",     "ZeddiS"),
        ]
        for key, val in info_items:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            _label(row, f"{key}:", 11, bold=True, color=t["text_dim"]).pack(side="left", padx=(0, 8))
            _label(row, val, 11, color=t["text"]).pack(side="left")
        ctk.CTkFrame(info, fg_color="transparent", height=10).pack()

    def _build_credits(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Logo
        if PIL_OK and LOGO_PATH.exists():
            try:
                img = Image.open(LOGO_PATH)
                img.thumbnail((120, 120), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(scroll, image=self._logo_img,
                         bg=t["content_bg"]).pack(pady=(0, 16))
            except Exception:
                pass

        _label(scroll, "ZeddiHub Tools Desktop", 22, bold=True,
               color=t["primary"]).pack(anchor="center")
        _label(scroll, "v1.0.0  |  Developed by ZeddiS", 12,
               color=t["text_dim"]).pack(pady=(2, 16), anchor="center")

        credits_data = [
            ("Autor",        "ZeddiS – https://zeddis.xyz"),
            ("Komunita",     "ZeddiHub – https://zeddihub.eu"),
            ("Dokumentace",  "https://wiki.zeddihub.eu"),
            ("Discord",      "https://dsc.gg/zeddihub"),
            ("GitHub",       "https://github.com/ZeddiS"),
            ("Framework",    "Python 3 + customtkinter"),
            ("Licence",      "MIT License"),
        ]

        sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        sec.pack(fill="x", pady=8)

        for key, val in credits_data:
            row = ctk.CTkFrame(sec, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            _label(row, key, 11, bold=True, color=t["text_dim"], width=140, anchor="w").pack(side="left")
            _label(row, val, 11, color=t["text"]).pack(side="left")

        ctk.CTkFrame(sec, fg_color="transparent", height=10).pack()

        ctk.CTkButton(scroll, text=" Otevřít zeddihub.eu",
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"), height=42,
                      image=icons.icon("globe", 14, "#cccccc"), compound="left",
                      command=lambda: webbrowser.open("https://zeddihub.eu")
                      ).pack(pady=12, fill="x")
