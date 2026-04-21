"""
ZeddiHub Tools — Stažitelné nástroje panel.

Lists catalog from admin_apps.json with search, filter chips, large FA
icons per card and a progress/pause/cancel UI during installation.
"""

import threading
import tkinter as tk
import customtkinter as ctk

try:
    from .. import external_tools
    from .. import icons
except ImportError:
    external_tools = None
    icons = None


def _fmt_bytes(n: float) -> str:
    if n < 1024: return f"{int(n)} B"
    if n < 1024 ** 2: return f"{n / 1024:.1f} KB"
    if n < 1024 ** 3: return f"{n / (1024 ** 2):.1f} MB"
    return f"{n / (1024 ** 3):.2f} GB"


def _fmt_speed(bps: float) -> str:
    if bps <= 0: return "— KB/s"
    if bps < 1024: return f"{bps:.0f} B/s"
    if bps < 1024 ** 2: return f"{bps / 1024:.1f} KB/s"
    return f"{bps / (1024 ** 2):.2f} MB/s"


def _ver_tuple(v) -> tuple:
    s = str(v or "0").lstrip("vV ")
    parts = []
    for chunk in s.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def _installed_version(slug: str) -> str:
    if not external_tools: return ""
    entry = external_tools.load_registry().get("installed", {}).get(slug)
    return (entry or {}).get("version", "") if entry else ""


class ToolsDownloadPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, on_refresh_sidebar=None,
                 on_open_module=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._on_refresh_sidebar = on_refresh_sidebar
        self._on_open_module = on_open_module
        self._catalog: list = []
        self._query: str = ""
        self._filter: str = "all"    # all | installed | available
        self._install_tasks: dict = {}   # slug -> InstallTask
        self._cards: dict = {}           # slug -> dict of widgets
        self._build()
        self._load_catalog_async()

    # ── tokens ────────────────────────────────────────────────────────────
    def _tk(self, key, fallback):
        return self.theme.get(key, fallback)

    # ── layout ────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        card_bg = th.get("card_bg", "#1a1a26")
        primary = th.get("primary", "#f0a500")

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 6))

        ctk.CTkLabel(header, text="Stažitelné nástroje",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=text).pack(anchor="w")
        ctk.CTkLabel(header,
                     text="Rozšiřující moduly — po instalaci se otevřou přímo v aplikaci.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=text_dim).pack(anchor="w")

        # Search + filter bar
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(12, 2))

        self._search_entry = ctk.CTkEntry(
            bar, placeholder_text="🔍  Hledat modul podle názvu nebo popisu…",
            fg_color=card_bg, border_width=1, border_color=th.get("border", "#2a2a36"),
            text_color=text, height=36, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 11),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(
            bar, text="⟳",
            fg_color=card_bg, hover_color=primary, text_color=text,
            font=ctk.CTkFont("Segoe UI", 14),
            width=36, height=36, corner_radius=10,
            command=self._load_catalog_async,
        ).pack(side="left")

        # Filter chips
        chips = ctk.CTkFrame(self, fg_color="transparent")
        chips.pack(fill="x", padx=24, pady=(6, 0))
        self._chip_btns: dict = {}
        for key, label in [("all", "Vše"), ("installed", "Nainstalované"), ("available", "Dostupné")]:
            btn = ctk.CTkButton(
                chips, text=label,
                fg_color=card_bg, hover_color=primary, text_color=text,
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
                height=28, width=110, corner_radius=14, border_width=0,
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="left", padx=(0, 8))
            self._chip_btns[key] = btn

        # Status strip
        self._status = ctk.CTkLabel(self, text="",
                                    font=ctk.CTkFont("Segoe UI", 10),
                                    text_color=text_dim)
        self._status.pack(anchor="w", padx=24, pady=(6, 0))

        # Scrollable list
        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list_frame.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        self._update_chip_styles()

    # ── filters / search ──────────────────────────────────────────────────
    def _on_search(self, _evt=None):
        self._query = self._search_entry.get().strip().lower()
        self._render_list()
        self._scroll_to_top()

    def _set_filter(self, key: str):
        self._filter = key
        self._update_chip_styles()
        self._render_list()
        self._scroll_to_top()

    def _scroll_to_top(self):
        # CTkScrollableFrame keeps its old yview after re-rendering a shorter
        # list — if the user had scrolled down in "Vše" the filtered result
        # appears empty because the viewport is past the content. Reset it.
        try:
            self._list_frame._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _update_chip_styles(self):
        th = self.theme
        primary = th.get("primary", "#f0a500")
        card_bg = th.get("card_bg", "#1a1a26")
        text = th.get("text", "#fff")
        for key, btn in self._chip_btns.items():
            if key == self._filter:
                btn.configure(fg_color=primary, text_color="#000", hover_color=primary)
            else:
                btn.configure(fg_color=card_bg, text_color=text, hover_color=th.get("primary_hover", primary))

    # ── catalog fetch ─────────────────────────────────────────────────────
    def _set_status(self, text: str):
        try:
            self.after(0, self._status.configure, {"text": text})
        except Exception:
            pass

    def _load_catalog_async(self):
        self._set_status("⏳ Načítání katalogu…")

        def _run():
            try:
                tools = external_tools.fetch_catalog()
                self._catalog = tools
                self.after(0, self._render_list)
                n = len(tools)
                upd = sum(1 for t in tools
                          if self._has_update(t.get("slug", ""), t.get("version")))
                if n and upd:
                    msg = f"✓ {n} nástrojů v katalogu  ·  🔔 {upd} aktualizace"
                elif n:
                    msg = f"✓ {n} nástrojů v katalogu  ·  vše aktuální"
                else:
                    msg = "Katalog je prázdný — momentálně žádné moduly nejsou k dispozici."
                self.after(0, lambda m=msg: self._status.configure(text=m))
            except Exception as e:
                msg = str(e) or e.__class__.__name__
                self._catalog = []
                self.after(0, self._render_list)
                self.after(0, lambda m=msg: self._status.configure(
                    text=f"! Nelze načíst katalog: {m}"))

        threading.Thread(target=_run, daemon=True).start()

    # ── list rendering ────────────────────────────────────────────────────
    def _filtered(self) -> list:
        q = self._query
        # Admin-only entries (require_admin=true in catalog) are hidden from
        # non-admin users entirely.
        try:
            from ..auth import is_admin as _is_admin
            admin = bool(_is_admin())
        except Exception:
            admin = False
        out = []
        for tool in self._catalog:
            slug = tool.get("slug", "")
            if tool.get("require_admin") and not admin:
                continue
            installed = external_tools.is_installed(slug)
            available = bool(tool.get("available", True))
            if self._filter == "installed" and not installed:
                continue
            if self._filter == "available" and (installed or not available):
                continue
            if q:
                blob = f"{tool.get('name', '')} {tool.get('description', '')} {slug}".lower()
                if q not in blob:
                    continue
            out.append(tool)
        return out

    def _render_list(self):
        for child in self._list_frame.winfo_children():
            child.destroy()
        self._cards.clear()

        th = self.theme
        tools = self._filtered()
        if not tools:
            msg = "Žádné nástroje neodpovídají filtru." if self._catalog else "Žádné nástroje v katalogu."
            ctk.CTkLabel(self._list_frame, text=msg,
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=th.get("text_dim", "#888")).pack(pady=30)
            return

        # Split: pending updates first (only in 'all' and 'installed' filters)
        updatable, normal = [], []
        for tool in tools:
            slug = tool.get("slug", "")
            if self._has_update(slug, tool.get("version")):
                updatable.append(tool)
            else:
                normal.append(tool)

        if updatable:
            self._render_section_header(
                f"🔔  Aktualizace dostupné ({len(updatable)})",
                th.get("primary", "#f0a500"),
            )
            for tool in updatable:
                self._render_card(tool)

        if normal:
            if updatable:
                self._render_section_header("Všechny nástroje",
                                            th.get("text_dim", "#888"))
            for tool in normal:
                self._render_card(tool)

    def _render_section_header(self, text: str, color: str):
        lbl = ctk.CTkLabel(
            self._list_frame, text=text,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=color, anchor="w",
        )
        lbl.pack(fill="x", padx=14, pady=(10, 2))

    def _has_update(self, slug: str, catalog_ver: str) -> bool:
        if not external_tools or not external_tools.is_installed(slug):
            return False
        return _ver_tuple(catalog_ver) > _ver_tuple(_installed_version(slug))

    def _render_card(self, tool: dict):
        th = self.theme
        card_bg = th.get("card_bg", "#1a1a26")
        tile_bg = th.get("secondary", "#0f0f18")
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")
        border = th.get("border", "#2a2a36")

        slug = tool.get("slug", "")
        installed = external_tools.is_installed(slug)

        # Single CTkFrame root per card — everything else is tk.Frame to
        # avoid CTk's per-widget canvas redraw during scroll (flicker).
        card = ctk.CTkFrame(self._list_frame, fg_color=card_bg,
                            corner_radius=14, border_width=1, border_color=border,
                            height=124)
        card.pack(fill="x", padx=8, pady=6)
        card.pack_propagate(False)

        row = tk.Frame(card, bg=card_bg, bd=0, highlightthickness=0)
        row.pack(fill="both", expand=True, padx=14, pady=14)

        # Icon tile (tk.Frame with static bg — no CTk redraw)
        tile = tk.Frame(row, bg=tile_bg, width=72, height=72,
                        bd=0, highlightthickness=0)
        tile.pack(side="left")
        tile.pack_propagate(False)
        icon_name = tool.get("icon", "wrench")
        icon_img = icons.icon(icon_name, 36, primary) if icons else None
        lbl = ctk.CTkLabel(tile, text="" if icon_img else "•",
                           image=icon_img, fg_color=tile_bg,
                           font=ctk.CTkFont("Segoe UI", 26, "bold"),
                           text_color=primary)
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        info = tk.Frame(row, bg=card_bg, bd=0, highlightthickness=0)
        info.pack(side="left", fill="both", expand=True, padx=(14, 10))
        ctk.CTkLabel(info, text=tool.get("name", slug),
                     fg_color=card_bg,
                     font=ctk.CTkFont("Segoe UI", 17, "bold"),
                     text_color=text).pack(anchor="w")
        if tool.get("description"):
            ctk.CTkLabel(info, text=tool.get("description"),
                         fg_color=card_bg,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=text_dim,
                         wraplength=500, justify="left").pack(anchor="w", pady=(2, 0))

        meta = tk.Frame(info, bg=card_bg, bd=0, highlightthickness=0)
        meta.pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(meta, text=f"v{tool.get('version', '1.0.0')}",
                     fg_color=card_bg,
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=text_dim).pack(side="left")
        if installed:
            ctk.CTkLabel(meta, text="  •  ", fg_color=card_bg,
                         font=ctk.CTkFont("Segoe UI", 9),
                         text_color=text_dim).pack(side="left")
            ctk.CTkLabel(meta, text="Nainstalováno", fg_color=card_bg,
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=th.get("success", "#22c55e")).pack(side="left")
        # Gold ADMIN pill — only admin accounts see this card at all
        # (non-admins are filtered out in _filtered()).
        if tool.get("require_admin"):
            ctk.CTkLabel(meta, text="  ", fg_color=card_bg,
                         font=ctk.CTkFont("Segoe UI", 9)).pack(side="left")
            ctk.CTkLabel(
                meta, text="ADMIN",
                font=ctk.CTkFont("Segoe UI", 8, "bold"),
                text_color="#0a0a0a", fg_color="#f5a623",
                corner_radius=8, width=52, height=16,
            ).pack(side="left")

        actions = tk.Frame(row, bg=card_bg, width=340,
                           bd=0, highlightthickness=0)
        actions.pack(side="right", fill="y")
        actions.pack_propagate(False)

        self._cards[slug] = {
            "card": card, "actions": actions, "tool": tool, "card_bg": card_bg,
        }
        self._render_card_actions(slug)

        # Clicking anywhere on the card (outside the action buttons) opens a
        # detail overlay. CTkButtons intercept their own clicks, so the
        # Install/Open/Uninstall buttons remain functional.
        def _open_detail(_e=None, t=tool):
            self._show_detail_overlay(t)
        for w in (card, row, tile, info, meta):
            try:
                w.bind("<Button-1>", _open_detail)
                w.configure(cursor="hand2")
            except Exception:
                pass
        # Also catch the rendered text labels inside the info/meta areas.
        for child in list(info.winfo_children()) + list(meta.winfo_children()):
            try:
                child.bind("<Button-1>", _open_detail)
                child.configure(cursor="hand2")
            except Exception:
                pass
        try:
            lbl.bind("<Button-1>", _open_detail)
            lbl.configure(cursor="hand2")
        except Exception:
            pass

    def _render_card_actions(self, slug: str):
        rec = self._cards.get(slug)
        if not rec:
            return
        actions = rec["actions"]
        for w in actions.winfo_children():
            w.destroy()

        tool = rec["tool"]
        th = self.theme
        primary = th.get("primary", "#f0a500")
        hover = th.get("primary_hover", "#d4900a")
        danger = "#8b2020"

        task = self._install_tasks.get(slug)
        installed = external_tools.is_installed(slug)
        available = bool(tool.get("available", True))

        # Persistent error state (card render after _done failure + panel
        # re-render). Survives sidebar/auth refresh inside the same session.
        if rec.get("error_msg") and task is None:
            self._render_error_ui(slug)
            return

        active_states = {
            "preparing", "downloading", "paused", "verifying",
            "extracting", "registering", "removing", "cleaning", "idle",
        }
        if task is not None and task.state in active_states:
            self._build_progress_ui(actions, slug, task)
            return

        if not installed and not available:
            # "Brzy k dispozici" badge
            card_bg = self._cards.get(slug, {}).get("card_bg", th.get("card_bg", "#1a1a26"))
            badge = tk.Frame(actions, bg=card_bg, bd=0, highlightthickness=0)
            badge.pack(side="right", pady=12, padx=4)
            pill = tk.Frame(badge, bg=th.get("secondary", "#2a2a36"),
                            bd=0, highlightthickness=0)
            pill.pack()
            ctk.CTkLabel(
                pill, text="  🕒  Brzy k dispozici  ",
                fg_color=th.get("secondary", "#2a2a36"),
                text_color=th.get("text_dim", "#888"),
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
            ).pack(padx=6, pady=4)
            return

        if installed:
            has_update = self._has_update(slug, tool.get("version"))
            if has_update:
                # Update replaces "Otevřít" as the primary action
                ctk.CTkButton(
                    actions, text=f"Aktualizovat → v{tool.get('version', '?')}",
                    fg_color=primary, hover_color=hover, text_color="#000",
                    width=200, height=34, corner_radius=10,
                    font=ctk.CTkFont("Segoe UI", 11, "bold"),
                    image=(icons.icon("arrows-rotate", 12, "#000") if icons else None),
                    compound="left",
                    command=lambda t=tool: self._install(t),
                ).pack(side="right")
            else:
                ctk.CTkButton(
                    actions, text="Otevřít",
                    fg_color=primary, hover_color=hover, text_color="#000",
                    width=100, height=34, corner_radius=10,
                    font=ctk.CTkFont("Segoe UI", 11, "bold"),
                    command=lambda s=slug: self._open_module(s),
                ).pack(side="right")
            ctk.CTkButton(
                actions, text="Odinstalovat",
                fg_color="transparent", hover_color=danger,
                text_color=th.get("text_dim", "#888"),
                border_width=1, border_color=th.get("border", "#2a2a36"),
                width=110, height=34, corner_radius=10,
                font=ctk.CTkFont("Segoe UI", 10),
                command=lambda s=slug: self._uninstall(s),
            ).pack(side="right", padx=(0, 6))
        else:
            ctk.CTkButton(
                actions, text="Instalovat",
                fg_color=primary, hover_color=hover, text_color="#000",
                width=140, height=38, corner_radius=10,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                image=(icons.icon("download", 14, "#000") if icons else None),
                compound="left",
                command=lambda t=tool: self._install(t),
            ).pack(side="right", pady=10)

    def _build_progress_ui(self, parent, slug: str, task):
        th = self.theme
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")
        card_bg = th.get("card_bg", "#1a1a26")
        # Track bar in a neutral border-ish tone so the orange fill only
        # appears when bytes actually start flowing.
        bar_track = th.get("border", "#2a2a36")
        connecting_color = th.get("text_dim", "#888")

        wrap = tk.Frame(parent, bg=card_bg, bd=0, highlightthickness=0)
        wrap.pack(fill="both", expand=True)

        top_row = tk.Frame(wrap, bg=card_bg, bd=0, highlightthickness=0)
        top_row.pack(fill="x", pady=(4, 0))

        # Start in "connecting" look: gray track, gray fill, zero progress.
        pb = ctk.CTkProgressBar(top_row, height=10, corner_radius=6,
                                progress_color=connecting_color, fg_color=bar_track)
        pb.set(0.0)
        pb.pack(side="left", fill="x", expand=True, padx=(0, 8))

        pause_btn = ctk.CTkButton(
            top_row, text="",
            image=(icons.icon("pause", 12, text) if icons else None),
            fg_color=card_bg, hover_color=primary, text_color=text,
            width=28, height=28, corner_radius=8,
        )
        pause_btn.pack(side="left", padx=(0, 4))

        cancel_btn = ctk.CTkButton(
            top_row, text="",
            image=(icons.icon("xmark", 12, text) if icons else None),
            fg_color=card_bg, hover_color="#8b2020", text_color=text,
            width=28, height=28, corner_radius=8,
            command=lambda s=slug: self._cancel_install(s),
        )
        cancel_btn.pack(side="left")

        pct_lbl = ctk.CTkLabel(wrap, text="0 %", fg_color=card_bg,
                               font=ctk.CTkFont("Segoe UI", 11, "bold"),
                               text_color=text)
        pct_lbl.pack(anchor="w", pady=(6, 0))

        info_lbl = ctk.CTkLabel(wrap, text="Připojování…", fg_color=card_bg,
                                font=ctk.CTkFont("Segoe UI", 9),
                                text_color=text_dim)
        info_lbl.pack(anchor="w")

        rec = self._cards.get(slug, {})
        rec["pb"] = pb
        rec["pct_lbl"] = pct_lbl
        rec["info_lbl"] = info_lbl
        rec["pause_btn"] = pause_btn
        rec["cancel_btn"] = cancel_btn

        def _toggle_pause():
            t = self._install_tasks.get(slug)
            if not t or not hasattr(t, "paused"): return
            if t.paused:
                t.resume()
                pause_btn.configure(image=(icons.icon("pause", 12, text) if icons else None))
            else:
                t.pause()
                pause_btn.configure(image=(icons.icon("play", 12, primary) if icons else None))

        pause_btn.configure(command=_toggle_pause)

        # UninstallTask has no pause/cancel — hide those controls
        if not hasattr(task, "pause"):
            pause_btn.pack_forget()
            cancel_btn.pack_forget()

    # ── actions ───────────────────────────────────────────────────────────
    def _install(self, tool: dict):
        slug = tool.get("slug")
        if not slug or slug in self._install_tasks:
            return

        # Clear any previous error state for this slug
        rec = self._cards.get(slug)
        if rec is not None:
            rec.pop("error_msg", None)
            rec.pop("error_tool", None)

        def _progress(done, total, speed, state):
            self.after(0, self._update_progress_ui, slug, done, total, speed, state)

        def _done(ok, msg):
            def _apply():
                self._install_tasks.pop(slug, None)
                self._status.configure(text=msg)
                if not ok:
                    # Keep an error UI on the card (red bar + retry button)
                    # instead of silently reverting to "Instalovat".
                    r = self._cards.get(slug)
                    if r is not None:
                        r["error_msg"] = str(msg or "Chyba při instalaci")
                        r["error_tool"] = tool
                    self._render_error_ui(slug)
                    return
                if self._on_refresh_sidebar:
                    self._on_refresh_sidebar()
                self._render_card_actions(slug)
            self.after(0, _apply)

        task = external_tools.install_tool(tool, progress_cb=_progress, done_cb=_done)
        self._install_tasks[slug] = task
        self._render_card_actions(slug)

    def _render_error_ui(self, slug: str):
        """Red progress bar + retry button. Shown when install fails."""
        rec = self._cards.get(slug)
        if not rec:
            return
        actions = rec["actions"]
        for w in actions.winfo_children():
            w.destroy()

        th = self.theme
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")
        card_bg = th.get("card_bg", "#1a1a26")
        bar_track = th.get("border", "#2a2a36")
        error_color = "#e24a4a"

        err_msg = rec.get("error_msg", "Chyba při instalaci")
        tool = rec.get("error_tool", rec.get("tool", {}))

        wrap = tk.Frame(actions, bg=card_bg, bd=0, highlightthickness=0)
        wrap.pack(fill="both", expand=True)

        top_row = tk.Frame(wrap, bg=card_bg, bd=0, highlightthickness=0)
        top_row.pack(fill="x", pady=(4, 0))

        pb = ctk.CTkProgressBar(top_row, height=10, corner_radius=6,
                                progress_color=error_color, fg_color=bar_track)
        pb.set(1.0)
        pb.pack(side="left", fill="x", expand=True, padx=(0, 8))

        retry_btn = ctk.CTkButton(
            top_row, text="Opakovat",
            image=(icons.icon("arrows-rotate", 12, "#000") if icons else None),
            compound="left",
            fg_color=primary, hover_color=th.get("primary_hover", "#d4900a"),
            text_color="#000",
            width=110, height=28, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            command=lambda t=tool: self._install(t),
        )
        retry_btn.pack(side="left", padx=(0, 4))

        dismiss_btn = ctk.CTkButton(
            top_row, text="",
            image=(icons.icon("xmark", 12, text) if icons else None),
            fg_color=card_bg, hover_color="#8b2020", text_color=text,
            width=28, height=28, corner_radius=8,
            command=lambda s=slug: self._dismiss_error(s),
        )
        dismiss_btn.pack(side="left")

        err_title = ctk.CTkLabel(wrap, text="Chyba stahování",
                                 fg_color=card_bg,
                                 font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                 text_color=error_color)
        err_title.pack(anchor="w", pady=(6, 0))
        err_body = ctk.CTkLabel(wrap, text=err_msg, fg_color=card_bg,
                                font=ctk.CTkFont("Segoe UI", 9),
                                text_color=text_dim, wraplength=320,
                                justify="left")
        err_body.pack(anchor="w")

    def _dismiss_error(self, slug: str):
        rec = self._cards.get(slug)
        if rec is not None:
            rec.pop("error_msg", None)
            rec.pop("error_tool", None)
        self._render_card_actions(slug)

    def _cancel_install(self, slug: str):
        task = self._install_tasks.get(slug)
        if task:
            task.cancel()

    def _update_progress_ui(self, slug, done, total, speed, state):
        rec = self._cards.get(slug)
        if not rec or "pb" not in rec:
            return
        pb = rec["pb"]
        pct_lbl = rec["pct_lbl"]
        info_lbl = rec["info_lbl"]

        pct = (done / total) if total else 0.0
        pb.set(max(0.0, min(1.0, pct)))
        pct_str = f"{int(pct * 100)} %" if total else "— %"

        th = self.theme
        primary = th.get("primary", "#f0a500")
        text_dim = th.get("text_dim", "#888")
        error_color = "#e24a4a"

        # Track fill color:
        #   gray while connecting/preparing/verifying/registering/cleaning,
        #   orange once bytes actually flow (downloading/extracting/paused),
        #   red on error.
        if state == "error":
            try: pb.configure(progress_color=error_color)
            except Exception: pass
        elif state in ("downloading", "extracting", "paused"):
            try: pb.configure(progress_color=primary)
            except Exception: pass
        else:
            try: pb.configure(progress_color=text_dim)
            except Exception: pass

        if state == "preparing":
            pct_lbl.configure(text=pct_str)
            info_lbl.configure(text="Připojování…")
        elif state == "downloading":
            pct_lbl.configure(text=pct_str)
            size_part = f"{_fmt_bytes(done)} / {_fmt_bytes(total)}" if total else _fmt_bytes(done)
            info_lbl.configure(text=f"{_fmt_speed(speed)} · {size_part}")
        elif state == "paused":
            pct_lbl.configure(text=pct_str)
            info_lbl.configure(text="⏸  Pozastaveno")
        elif state == "verifying":
            pct_lbl.configure(text=pct_str)
            info_lbl.configure(text="Ověřování integrity…")
        elif state == "extracting":
            pb.set(1.0)
            pct_lbl.configure(text="100 %")
            info_lbl.configure(text="Rozbalování souborů…")
        elif state == "registering":
            pct_lbl.configure(text=pct_str)
            info_lbl.configure(text="Registrace modulu…")
        elif state == "removing":
            pct_lbl.configure(text=pct_str)
            info_lbl.configure(text="Odstraňování souborů…")
        elif state == "cleaning":
            pct_lbl.configure(text=pct_str)
            info_lbl.configure(text="Čištění registru…")
        elif state == "cancelled":
            info_lbl.configure(text="Zrušeno")
        elif state == "error":
            info_lbl.configure(text="Chyba")

    def _open_module(self, slug: str):
        if self._on_open_module:
            try:
                self._on_open_module(slug)
                return
            except Exception as e:
                self._status.configure(text=f"! Chyba otevření: {e}")
        else:
            self._status.configure(text="! Otevření modulu není propojeno s hlavním oknem.")

    def _uninstall(self, slug: str):
        if slug in self._install_tasks:
            return

        def _progress(done, total, speed, state):
            self.after(0, self._update_progress_ui, slug, done, total, speed, state)

        def _done(ok, msg):
            def _apply():
                self._install_tasks.pop(slug, None)
                self._status.configure(text=f"✓ {msg}" if ok else f"! {msg}")
                if self._on_refresh_sidebar:
                    self._on_refresh_sidebar()
                self._render_list()
            self.after(0, _apply)

        task = external_tools.uninstall_tool_async(slug, progress_cb=_progress, done_cb=_done)
        self._install_tasks[slug] = task
        self._render_card_actions(slug)

    # ── detail overlay ─────────────────────────────────────────────────────
    def _show_detail_overlay(self, tool: dict):
        """In-window modal that shows the tool name, description, screenshot.
        The panel content remains rendered underneath (backdrop dims it)."""
        # Close any existing overlay first
        self._close_detail_overlay()

        th = self.theme
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        card_bg = th.get("card_bg", "#1a1a26")
        border = th.get("border", "#2a2a36")
        primary = th.get("primary", "#f0a500")
        hover = th.get("primary_hover", "#d4900a")
        danger = "#8b2020"

        # Centered modal placed directly on the panel — NO full backdrop,
        # so the catalog behind remains visible around the modal edges.
        modal = ctk.CTkFrame(self, fg_color=card_bg,
                             corner_radius=16, border_width=1,
                             border_color=border)
        modal.place(relx=0.5, rely=0.5, anchor="center",
                    relwidth=0.72, relheight=0.82)
        try:
            modal.lift()
        except Exception:
            pass

        # Close X
        close_btn = ctk.CTkButton(
            modal, text="",
            image=(icons.icon("xmark", 16, text) if icons else None),
            fg_color="transparent", hover_color=danger, text_color=text,
            width=36, height=36, corner_radius=10,
            command=self._close_detail_overlay,
        )
        close_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # Header row: icon + name/version
        header = ctk.CTkFrame(modal, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(28, 10))

        icon_name = tool.get("icon", "wrench")
        icon_img = icons.icon(icon_name, 44, primary) if icons else None
        ctk.CTkLabel(header, text="", image=icon_img,
                     fg_color="transparent").pack(side="left")

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True, padx=(16, 0))
        ctk.CTkLabel(title_col, text=tool.get("name", tool.get("slug", "")),
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=text, anchor="w").pack(anchor="w")
        ver_line = f"v{tool.get('version', '1.0.0')}"
        if tool.get("author"):
            ver_line += f"  ·  {tool.get('author')}"
        ctk.CTkLabel(title_col, text=ver_line,
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=text_dim, anchor="w").pack(anchor="w", pady=(4, 0))

        # Body — description + screenshot
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(6, 10))

        desc_text = tool.get("long_description") or tool.get("description") or "Bez popisu."
        desc = ctk.CTkLabel(body, text=desc_text,
                            font=ctk.CTkFont("Segoe UI", 12),
                            text_color=text, wraplength=640,
                            justify="left", anchor="nw")
        desc.pack(fill="x", anchor="w")

        # Screenshot placeholder — lazy-fetch from screenshot_url
        shot_url = tool.get("screenshot_url") or tool.get("screenshot")
        shot_wrap = ctk.CTkFrame(body, fg_color=th.get("secondary", "#0f0f18"),
                                 corner_radius=12, border_width=1,
                                 border_color=border, height=300)
        shot_wrap.pack(fill="both", expand=True, pady=(16, 4))
        shot_wrap.pack_propagate(False)

        shot_lbl = ctk.CTkLabel(
            shot_wrap,
            text=("Ukázka se načítá…" if shot_url else "Bez ukázky"),
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=text_dim,
        )
        shot_lbl.pack(expand=True)

        if shot_url:
            self._load_screenshot_async(shot_url, shot_lbl, shot_wrap)

        # Action bar
        actions = ctk.CTkFrame(modal, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(6, 22))

        slug = tool.get("slug")
        installed = external_tools.is_installed(slug) if external_tools else False
        available = bool(tool.get("available", True))

        def _primary_and_close(cmd):
            self._close_detail_overlay()
            cmd()

        if installed:
            has_update = self._has_update(slug, tool.get("version"))
            if has_update:
                ctk.CTkButton(
                    actions, text=f"Aktualizovat → v{tool.get('version', '?')}",
                    fg_color=primary, hover_color=hover, text_color="#000",
                    width=220, height=38, corner_radius=10,
                    font=ctk.CTkFont("Segoe UI", 12, "bold"),
                    image=(icons.icon("arrows-rotate", 14, "#000") if icons else None),
                    compound="left",
                    command=lambda t=tool: _primary_and_close(lambda: self._install(t)),
                ).pack(side="right")
            else:
                ctk.CTkButton(
                    actions, text="Otevřít",
                    fg_color=primary, hover_color=hover, text_color="#000",
                    width=140, height=38, corner_radius=10,
                    font=ctk.CTkFont("Segoe UI", 12, "bold"),
                    command=lambda s=slug: _primary_and_close(lambda: self._open_module(s)),
                ).pack(side="right")
        elif available:
            ctk.CTkButton(
                actions, text="Instalovat",
                fg_color=primary, hover_color=hover, text_color="#000",
                width=160, height=40, corner_radius=10,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                image=(icons.icon("download", 14, "#000") if icons else None),
                compound="left",
                command=lambda t=tool: _primary_and_close(lambda: self._install(t)),
            ).pack(side="right")
        else:
            ctk.CTkLabel(
                actions, text="  🕒  Brzy k dispozici  ",
                fg_color=th.get("secondary", "#2a2a36"),
                text_color=text_dim,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                corner_radius=10, height=32,
            ).pack(side="right")

        # ESC to close
        try:
            self.winfo_toplevel().bind("<Escape>", lambda _e: self._close_detail_overlay(), add="+")
        except Exception:
            pass

        self._detail_overlay = modal

    def _close_detail_overlay(self):
        ov = getattr(self, "_detail_overlay", None)
        if ov is not None:
            try:
                ov.destroy()
            except Exception:
                pass
            self._detail_overlay = None

    def _load_screenshot_async(self, url: str, lbl, wrap):
        """Download a screenshot in a background thread and render it."""
        def _worker():
            import io
            import urllib.request
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "ZeddiHubTools/1.7"}
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = r.read()
            except Exception as e:
                self.after(0, lambda: lbl.configure(text=f"Nelze načíst ukázku: {e}"))
                return
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(data))
                img.load()
            except Exception as e:
                self.after(0, lambda: lbl.configure(text=f"Neplatný obrázek: {e}"))
                return

            def _apply():
                try:
                    # Scale to fit the wrap while keeping aspect
                    wrap.update_idletasks()
                    w = max(420, wrap.winfo_width() - 24)
                    h = max(220, wrap.winfo_height() - 24)
                    iw, ih = img.size
                    scale = min(w / iw, h / ih, 1.0)
                    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                    disp = img.resize((nw, nh), Image.LANCZOS)
                    photo = ctk.CTkImage(
                        light_image=disp, dark_image=disp, size=(nw, nh)
                    )
                    lbl.configure(text="", image=photo)
                    lbl._photo_ref = photo  # keep reference
                except Exception as ex:
                    lbl.configure(text=f"Chyba zobrazení: {ex}")
            self.after(0, _apply)

        threading.Thread(target=_worker, daemon=True).start()
