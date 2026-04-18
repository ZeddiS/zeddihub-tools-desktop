"""
ZeddiHub Tools - About panel.
Statický informační panel: verze, autor, licence, technologie, odkazy.
N-12.
"""

import platform
import sys
import webbrowser
import customtkinter as ctk

from .. import icons

try:
    from ..locale import t
except ImportError:
    def t(key, **kw):
        return key

try:
    from ..updater import CURRENT_VERSION, GITHUB_RELEASES_URL
except ImportError:
    CURRENT_VERSION = "?"
    GITHUB_RELEASES_URL = "https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#f0f0f0", **kw)


def _card(parent, theme):
    return ctk.CTkFrame(parent, fg_color=theme["card_bg"], corner_radius=8)


class AboutPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        # ── Header: logo + název aplikace ──────────────────────────────────
        hero = _card(scroll, th)
        hero.pack(fill="x", pady=(0, 10))

        _label(hero, "ZeddiHub Tools", 22, bold=True, color=th["primary"]
               ).pack(padx=20, pady=(18, 4), anchor="w")
        _label(hero, t("about_tagline"), 12, color=th["text_dim"]
               ).pack(padx=20, pady=(0, 14), anchor="w")

        # ── Verze a systém ─────────────────────────────────────────────────
        ver_card = _card(scroll, th)
        ver_card.pack(fill="x", pady=6)
        _label(ver_card, t("about_version_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        grid = ctk.CTkFrame(ver_card, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(0, 12))
        grid.grid_columnconfigure(1, weight=1)

        rows = [
            (t("about_app_version"), f"v{CURRENT_VERSION}"),
            (t("about_python_version"), platform.python_version()),
            (t("about_os"), f"{platform.system()} {platform.release()}"),
            (t("about_architecture"), platform.machine()),
        ]
        for i, (k, v) in enumerate(rows):
            _label(grid, k + ":", 11, color=th["text_dim"]
                   ).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=2)
            _label(grid, v, 11, color=th["text"]
                   ).grid(row=i, column=1, sticky="w", pady=2)

        # ── Autor ──────────────────────────────────────────────────────────
        author_card = _card(scroll, th)
        author_card.pack(fill="x", pady=6)
        _label(author_card, t("about_author_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(author_card,
               "ZeddiS  •  © 2024–2026  •  " + t("about_author_note"),
               11, color=th["text"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 12), anchor="w")

        # ── Technologie ────────────────────────────────────────────────────
        tech_card = _card(scroll, th)
        tech_card.pack(fill="x", pady=6)
        _label(tech_card, t("about_tech_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        tech_list = (
            "• Python 3.10+  •  customtkinter  •  Pillow  •  cryptography (Fernet)\n"
            "• pystray  •  psutil  •  pynput  •  pyautogui  •  yt-dlp (on-demand)"
        )
        _label(tech_card, tech_list, 11, color=th["text"], justify="left"
               ).pack(padx=14, pady=(0, 12), anchor="w")

        # ── Odkazy / tlačítka ──────────────────────────────────────────────
        btn_card = _card(scroll, th)
        btn_card.pack(fill="x", pady=6)
        _label(btn_card, t("about_links_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 8), anchor="w")

        btn_row = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkButton(btn_row, text=" GitHub",
                      image=icons.icon("github", 14, "#ffffff"), compound="left",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=140,
                      command=lambda: webbrowser.open(GITHUB_RELEASES_URL)
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text=" Web",
                      image=icons.icon("globe", 14, "#ffffff"), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=140,
                      command=lambda: webbrowser.open("https://zeddihub.eu/tools/")
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text=" Discord",
                      image=icons.icon("discord", 14, "#ffffff"), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=140,
                      command=lambda: webbrowser.open("https://discord.gg/zeddihub")
                      ).pack(side="left")

        # ── Licence ────────────────────────────────────────────────────────
        lic_card = _card(scroll, th)
        lic_card.pack(fill="x", pady=6)
        _label(lic_card, t("about_license_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(lic_card, t("about_license_text"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 12), anchor="w")
