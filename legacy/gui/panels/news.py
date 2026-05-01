"""
ZeddiHub Tools - News panel (N-13).

Zobrazuje posledních N release z GitHub Releases API jako feed karet.
Fetch běží v threadu, UI aktualizace přes after(0, ...).
"""

from __future__ import annotations

import json
import threading
import urllib.request
import webbrowser
from typing import Optional

import customtkinter as ctk

from .. import icons

try:
    from ..locale import t
except ImportError:
    def t(key, **kw):
        return key


GITHUB_RELEASES_API = (
    "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases"
)
GITHUB_RELEASES_WEB = (
    "https://github.com/ZeddiS/zeddihub-tools-desktop/releases"
)


def _fetch_releases(limit: int = 8) -> list[dict]:
    req = urllib.request.Request(
        f"{GITHUB_RELEASES_API}?per_page={limit}",
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "ZeddiHub-Tools"},
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data if isinstance(data, list) else []


class NewsPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()
        self.after(200, self._load_async)

    def _build(self):
        th = self.theme

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 12))
        ctk.CTkLabel(
            header,
            text=t("news_title") if t("news_title") != "news_title" else "Novinky",
            image=icons.icon("newspaper", 22, th.get("primary", "#f0a500")),
            compound="left",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=th.get("text_strong", th["text"]),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text=" GitHub",
            image=icons.icon("github", 14, "#ffffff"),
            compound="left",
            fg_color=th["primary"],
            hover_color=th.get("primary_hover", th["primary"]),
            text_color=th.get("nav_active_text", "#ffffff"),
            height=32,
            width=120,
            corner_radius=int(th.get("radius_button", 10)),
            command=lambda: webbrowser.open(GITHUB_RELEASES_WEB),
        ).pack(side="right")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self._status = ctk.CTkLabel(
            self._scroll,
            text=t("news_loading") if t("news_loading") != "news_loading"
                 else "Načítám poslední release…",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
        )
        self._status.pack(pady=24)

    def _load_async(self):
        t_ = threading.Thread(target=self._fetch_and_render, daemon=True)
        t_.start()

    def _fetch_and_render(self):
        try:
            releases = _fetch_releases(limit=10)
        except Exception as e:
            self.after(0, self._render_error, str(e))
            return
        self.after(0, self._render, releases)

    def _render_error(self, msg: str):
        th = self.theme
        try:
            self._status.configure(
                text=(t("news_error") if t("news_error") != "news_error"
                      else "Nepodařilo se načíst release") + f"\n{msg}",
                text_color=th.get("error", "#ef4444"),
            )
        except Exception:
            pass

    def _render(self, releases: list[dict]):
        th = self.theme
        try:
            self._status.destroy()
        except Exception:
            pass

        if not releases:
            ctk.CTkLabel(
                self._scroll,
                text="Žádné releasy nenalezeny.",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=th.get("text_muted", th["text_dim"]),
            ).pack(pady=24)
            return

        for rel in releases:
            self._build_card(rel)

    def _build_card(self, rel: dict):
        th = self.theme
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=th.get("card_bg", "#15151e"),
            corner_radius=int(th.get("radius_card", 14)),
            border_width=0,
        )
        card.pack(fill="x", pady=6)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(14, 4))

        tag = rel.get("tag_name") or "?"
        name = rel.get("name") or tag
        published = (rel.get("published_at") or "")[:10]
        url = rel.get("html_url") or GITHUB_RELEASES_WEB

        ctk.CTkLabel(
            header,
            text=tag,
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=th.get("primary", "#f0a500"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"  •  {published}",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text=t("news_open") if t("news_open") != "news_open" else "Otevřít",
            width=90,
            height=26,
            corner_radius=int(th.get("radius_button", 10)),
            fg_color="transparent",
            hover_color=th.get("card_hover", th.get("secondary", "#1f1f2c")),
            text_color=th["text"],
            font=ctk.CTkFont("Segoe UI", 10),
            command=lambda u=url: webbrowser.open(u),
        ).pack(side="right")

        if name and name != tag:
            ctk.CTkLabel(
                card,
                text=name,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=th["text"],
                anchor="w",
                wraplength=820,
                justify="left",
            ).pack(fill="x", padx=18, pady=(0, 4))

        body = (rel.get("body") or "").strip()
        if body:
            if len(body) > 700:
                body = body[:700].rsplit("\n", 1)[0] + "\n…"
            ctk.CTkLabel(
                card,
                text=body,
                font=ctk.CTkFont("Segoe UI", 10),
                text_color=th.get("text_dim", th["text"]),
                anchor="w",
                justify="left",
                wraplength=820,
            ).pack(fill="x", padx=18, pady=(0, 14))
        else:
            ctk.CTkFrame(card, height=8, fg_color="transparent").pack()
