"""
AppsPanel — catalog of web apps and direct links with search, dynamic
admin-managed filter groups, and optional embedded WebView2 browsing.

Replaces the v1.7.5/v1.7.6 placeholder.
"""

from __future__ import annotations

import webbrowser
from tkinter import messagebox
from typing import Any, Dict, List, Optional

import customtkinter as ctk

from ... import icons
from ...widgets import (
    make_button,
    make_card,
    make_entry,
    make_label,
    make_page_title,
    make_section_title,
)
from .catalog import CatalogClient
from .webview_host import (
    PYWEBVIEW_OK,
    install_webview2_async,
    open_webview,
    webview2_installed,
)


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class AppsPanel(ctk.CTkFrame):
    #: Number of cards per row in the catalog grid.
    GRID_COLS = 3

    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme

        self._client = CatalogClient()
        self._active_filters: Dict[str, str] = {}  # group_id → option_id ("" = Všechny)
        self._search_var = ctk.StringVar(value="")
        self._status_var = ctk.StringVar(value="")
        # v1.7.9: debounce timer ID pro vyhledávací pole — při psaní se grid
        # rebuilduje až 250 ms po posledním stisku, ne na každý znak.
        self._search_after_id: Optional[str] = None

        self._build()

        # Seed from cache (instant render), then refresh from network
        if self._client.load_cached():
            self._render_filter_groups()
            self._render_grid()
            self._status_var.set("Zobrazeno z cache — obnovuji ze serveru…")
        self._client.refresh_async(
            on_done=lambda ok, err: self.after(0, self._on_refresh_done, ok, err)
        )

    # ── UI ────────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=24)

        make_page_title(
            root, "Aplikace", th,
            subtitle="Katalog užitečných webů, aplikací a přímých odkazů s vyhledáváním a filtry.",
        ).pack(fill="x", anchor="w", pady=(0, 14))

        # Toolbar: search + refresh
        toolbar = ctk.CTkFrame(root, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 12))

        search_entry = make_entry(
            toolbar, self._search_var, th,
            placeholder="Hledat (název, popis, tagy)…",
            height=36,
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        # v1.7.9: debounce — bez něj se grid (50+ karet) rebuilduje na každý
        # stisknutý znak, což je viditelně pomalé při delším query.
        self._search_var.trace_add("write", lambda *_: self._schedule_search_render())

        make_button(
            toolbar, "  Obnovit", self._on_refresh_click, th,
            variant="primary", accent="primary",
            icon=icons.icon("rotate", 13, "#ffffff"), compound="left",
            height=36, width=120,
        ).pack(side="left")

        # Filter row (dynamic — populated by _render_filter_groups)
        self._filters_row = ctk.CTkFrame(root, fg_color="transparent")
        self._filters_row.pack(fill="x", pady=(0, 10))

        # WebView2 status banner (visible only when runtime missing)
        self._webview_banner = ctk.CTkFrame(root, fg_color="transparent")
        self._webview_banner.pack(fill="x", pady=(0, 8))
        self._render_webview_banner()

        # Catalog grid (scrollable)
        self._grid_wrap = ctk.CTkScrollableFrame(
            root, fg_color="transparent",
            scrollbar_button_color=th["primary"],
            scrollbar_button_hover_color=th["primary_hover"],
        )
        self._grid_wrap.pack(fill="both", expand=True)

        # Status bar
        status = ctk.CTkFrame(root, fg_color="transparent")
        status.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(
            status, textvariable=self._status_var,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(side="left")

    # ── WebView2 banner ───────────────────────────────────────────────────
    def _render_webview_banner(self):
        th = self.theme
        for ch in list(self._webview_banner.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass
        if webview2_installed() and PYWEBVIEW_OK:
            return  # all good, no banner

        if not PYWEBVIEW_OK:
            msg = ("Modul pywebview není v tomto buildu nainstalován — odkazy s režimem "
                   "„webview\" se otevřou v systémovém prohlížeči.")
            btn_text = None
            btn_cmd = None
        else:
            msg = ("Edge WebView2 runtime není nainstalován — odkazy s režimem "
                   "„webview\" se otevřou v systémovém prohlížeči. Nainstalovat?")
            btn_text = "Nainstalovat WebView2"
            btn_cmd = self._install_webview2

        warn = make_card(self._webview_banner, th, padding=14, bordered=True)
        warn.pack(fill="x")

        inner = ctk.CTkFrame(warn, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            inner, image=icons.icon("circle-info", 16, th.get("warning", "#f59e0b")),
            text="",
        ).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            inner, text=msg,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w", wraplength=780, justify="left",
        ).pack(side="left", fill="x", expand=True)

        if btn_text and btn_cmd:
            make_button(
                inner, btn_text, btn_cmd, th,
                variant="primary", accent="primary",
                height=32, width=180,
            ).pack(side="right", padx=(10, 0))

    def _install_webview2(self):
        self._status_var.set("Stahuji instalátor WebView2…")
        install_webview2_async(
            on_done=lambda ok, msg: self.after(0, self._on_wv2_done, ok, msg)
        )

    def _on_wv2_done(self, ok: bool, msg: str):
        self._status_var.set(msg)
        self._render_webview_banner()

    # ── Filter groups ─────────────────────────────────────────────────────
    def _render_filter_groups(self):
        th = self.theme
        for ch in list(self._filters_row.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass

        groups = self._client.filter_groups
        if not groups:
            return

        for group in groups:
            gid = group.get("id")
            glabel = group.get("label", gid)
            options = group.get("options") or []
            if not gid or not options:
                continue

            box = ctk.CTkFrame(self._filters_row, fg_color="transparent")
            box.pack(side="left", padx=(0, 14))

            make_label(
                box, glabel, th, size=9, bold=True,
                color=th.get("text_muted", th["text_dim"]),
                anchor="w",
            ).pack(fill="x", anchor="w")

            values = ["Vše"] + [o.get("label", o.get("id", "?")) for o in options]
            id_by_label = {"Vše": ""}
            for o in options:
                id_by_label[o.get("label", o.get("id", "?"))] = o.get("id", "")

            var = ctk.StringVar(value="Vše")
            var.trace_add("write", lambda *_, g=gid, v=var, m=id_by_label:
                          self._on_filter_change(g, m.get(v.get(), "")))
            ctk.CTkOptionMenu(
                box, variable=var, values=values,
                fg_color=th.get("input_bg", th["secondary"]),
                button_color=th["primary"],
                button_hover_color=th["primary_hover"],
                dropdown_fg_color=th.get("card_bg", th["secondary"]),
                text_color=th.get("text", "#d0d0d0"),
                width=160,
            ).pack(pady=(2, 0))

    def _on_filter_change(self, group_id: str, option_id: str):
        if option_id:
            self._active_filters[group_id] = option_id
        else:
            self._active_filters.pop(group_id, None)
        self._render_grid()

    # ── Search debounce ───────────────────────────────────────────────────
    def _schedule_search_render(self) -> None:
        """Posuneme rebuild gridu o 250 ms pokaždé, když se mění query —
        při rychlém psaní se vyrenderuje jen jednou na konci, ne 8× za vteřinu.
        """
        try:
            if self._search_after_id is not None:
                self.after_cancel(self._search_after_id)
        except Exception:
            pass
        try:
            self._search_after_id = self.after(250, self._render_grid)
        except Exception:
            # Widget už neexistuje (eviction). Bezpečně ignorovat.
            self._search_after_id = None

    # ── Grid ──────────────────────────────────────────────────────────────
    def _render_grid(self):
        th = self.theme
        for ch in list(self._grid_wrap.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass

        results = self._client.search(self._search_var.get(), self._active_filters)

        # Update status + empty state
        total = len(self._client.items)
        shown = len(results)
        if total == 0:
            self._render_empty("Katalog je prázdný nebo jej zatím nelze načíst.")
            self._status_var.set("Bez položek.")
            return
        if shown == 0:
            self._render_empty("Nic nenalezeno. Zkus jiná klíčová slova nebo vypnout filtry.")
            self._status_var.set(f"0 / {total} položek odpovídá.")
            return

        self._status_var.set(f"{shown} / {total} položek")

        # Grid
        grid = ctk.CTkFrame(self._grid_wrap, fg_color="transparent")
        grid.pack(fill="x")
        for col in range(self.GRID_COLS):
            grid.grid_columnconfigure(col, weight=1, uniform="apps")

        for row_idx, row in enumerate(_chunks(results, self.GRID_COLS)):
            for col_idx, item in enumerate(row):
                tile = self._make_tile(grid, item)
                tile.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")

    def _render_empty(self, text: str):
        th = self.theme
        ctk.CTkLabel(
            self._grid_wrap, text=text,
            font=ctk.CTkFont("Segoe UI", 12, "italic"),
            text_color=th.get("text_muted", th["text_dim"]),
            justify="center",
        ).pack(pady=40)

    def _make_tile(self, parent, item: Dict[str, Any]) -> ctk.CTkFrame:
        th = self.theme
        card = ctk.CTkFrame(
            parent,
            fg_color=th.get("card_bg", th["secondary"]),
            corner_radius=th.get("radius_card", 14),
            border_width=0,
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Header row: icon + title
        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x", anchor="w")

        icon_name = item.get("icon") or "globe"
        ctk.CTkLabel(
            head, image=icons.icon(icon_name, 22, th["primary"]),
            text="",
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            head, text=item.get("name", "—"),
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=th.get("text_strong", th["text"]),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Description
        desc = item.get("description") or ""
        if desc:
            ctk.CTkLabel(
                inner, text=desc,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=th.get("text_muted", th["text_dim"]),
                anchor="w", justify="left",
                wraplength=280,
            ).pack(fill="x", anchor="w", pady=(6, 8))

        # Tags row
        tags = item.get("tags") or []
        if tags:
            tag_row = ctk.CTkFrame(inner, fg_color="transparent")
            tag_row.pack(fill="x", anchor="w", pady=(0, 8))
            for tag in tags[:4]:
                # show only the option part of "group:option" for compactness
                label = tag.split(":", 1)[-1] if ":" in tag else tag
                ctk.CTkLabel(
                    tag_row, text=f"#{label}",
                    font=ctk.CTkFont("Segoe UI", 9),
                    text_color=th["primary"],
                    fg_color=th.get("input_bg", th["secondary"]),
                    corner_radius=4,
                    padx=6, pady=2,
                ).pack(side="left", padx=(0, 4))

        # Action row
        mode = (item.get("open_mode") or "external").lower()
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(fill="x")

        if mode == "download":
            make_button(
                actions, "  Stáhnout",
                lambda it=item: self._open_item(it), th,
                variant="primary", accent="primary",
                icon=icons.icon("download", 12, "#ffffff"), compound="left",
                height=32, width=120,
            ).pack(side="left")
            make_button(
                actions, "", lambda it=item: self._copy_url(it), th,
                variant="secondary",
                icon=icons.icon("copy", 12, th.get("text_muted", th["text_dim"])),
                height=32, width=36,
            ).pack(side="right")
        else:
            primary_label = "  Otevřít"
            primary_icon = icons.icon(
                "globe" if mode == "webview" else "external-link", 12, "#ffffff"
            )
            make_button(
                actions, primary_label,
                lambda it=item: self._open_item(it), th,
                variant="primary", accent="primary",
                icon=primary_icon, compound="left",
                height=32, width=110,
            ).pack(side="left")
            make_button(
                actions, "", lambda it=item: self._open_external(it), th,
                variant="secondary",
                icon=icons.icon("external-link", 12, th.get("text_muted", th["text_dim"])),
                height=32, width=36,
            ).pack(side="right")
            make_button(
                actions, "", lambda it=item: self._copy_url(it), th,
                variant="secondary",
                icon=icons.icon("copy", 12, th.get("text_muted", th["text_dim"])),
                height=32, width=36,
            ).pack(side="right", padx=(0, 4))

        return card

    # ── Actions ───────────────────────────────────────────────────────────
    def _open_item(self, item: Dict[str, Any]):
        url = (item.get("url") or "").strip()
        if not url:
            messagebox.showinfo("Aplikace", "Tato položka nemá URL.")
            return
        mode = (item.get("open_mode") or "external").lower()
        title = f"ZeddiHub · {item.get('name', 'Web')}"
        if mode == "webview":
            if open_webview(url, title=title):
                self._status_var.set(f"Otevřeno v WebView: {item.get('name', url)}")
                return
            # fallthrough to external if webview unavailable
        if mode == "download":
            try:
                webbrowser.open(url, new=2)
                self._status_var.set(f"Stahování spuštěno: {url}")
                return
            except Exception as e:
                messagebox.showerror("Aplikace", f"Nelze otevřít odkaz: {e}")
                return
        self._open_external(item)

    def _open_external(self, item: Dict[str, Any]):
        url = (item.get("url") or "").strip()
        if not url:
            return
        try:
            webbrowser.open(url, new=2)
            self._status_var.set(f"Otevřeno v prohlížeči: {item.get('name', url)}")
        except Exception as e:
            messagebox.showerror("Aplikace", f"Nelze otevřít odkaz: {e}")

    def _copy_url(self, item: Dict[str, Any]):
        url = (item.get("url") or "").strip()
        if not url:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.update()  # keep clipboard after panel destroy
            self._status_var.set(f"Zkopírováno: {url}")
        except Exception:
            pass

    # ── Refresh flow ──────────────────────────────────────────────────────
    def _on_refresh_click(self):
        self._status_var.set("Načítám katalog…")
        self._client.refresh_async(
            on_done=lambda ok, err: self.after(0, self._on_refresh_done, ok, err),
            force=True,
        )

    def _on_refresh_done(self, ok: bool, err: Optional[str]):
        if ok:
            self._render_filter_groups()
            self._render_grid()
            self._status_var.set(f"{len(self._client.items)} položek · zdroj: {self._client.source}")
        else:
            if not self._client.items:
                # first load failed and no cache — show error state
                self._render_empty(
                    "Katalog se nepodařilo načíst. Zkontroluj připojení a klikni na „Obnovit\"."
                )
            self._status_var.set(f"Chyba: {err or 'neznámá'}")


__all__ = ["AppsPanel"]
