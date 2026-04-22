"""
Procesy — samostatný panel se seznamem běžících procesů.

Oddělen od pc_tools.py ve v1.7.5 (Utility byla rozbita do 4 podsekcí).

Featury:
  • Tabulka PID / Název / CPU% / RAM MB.
  • Řazení kliknutím na hlavičku (cpu / ram / name / pid).
  • Vyhledávací filter (live, case-insensitive substring přes název).
  • Ruční "Aktualizovat" a volitelné auto-refresh každých 3 s.
  • Tlačítko "Ukončit proces" (psutil.Process.terminate → kill fallback).
"""

from __future__ import annotations

import threading
from tkinter import messagebox
from typing import List, Dict, Optional

import customtkinter as ctk

try:
    import psutil  # type: ignore
    PSUTIL_OK = True
except Exception:
    PSUTIL_OK = False

from .. import icons
from ..widgets import (
    make_page_title,
    make_section_title,
    make_button,
    make_card,
    make_entry,
)


class ProcessesPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme

        self._rows: List[Dict] = []
        self._sort_key = "cpu"
        self._sort_desc = True
        self._filter_var = ctk.StringVar(value="")
        self._auto_var = ctk.BooleanVar(value=False)
        self._status_var = ctk.StringVar(value="—")
        self._auto_job: Optional[str] = None
        self._selected_pid: Optional[int] = None

        self._build()

        if PSUTIL_OK:
            # warm up CPU counters (first call returns 0.0)
            try:
                psutil.cpu_percent(interval=None)
            except Exception:
                pass
            self._refresh()

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=24)

        make_page_title(
            root, "Procesy", th,
            subtitle="Seznam běžících procesů s tříděním, filtrováním a možností ukončení.",
        ).pack(fill="x", anchor="w", pady=(0, 16))

        if not PSUTIL_OK:
            warn = make_card(root, th, padding=18, bordered=True)
            warn.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                warn, image=icons.icon("triangle-exclamation", 24, th.get("warning", "#f59e0b")),
                text="",
            ).pack(padx=18, pady=(16, 4), anchor="w")
            ctk.CTkLabel(
                warn, text="Modul psutil není nainstalován.",
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                text_color=th.get("text_strong", th["text"]),
            ).pack(padx=18, anchor="w")
            ctk.CTkLabel(
                warn,
                text="Spusť v terminálu:  pip install psutil\na restartuj aplikaci.",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=th.get("text_muted", th["text_dim"]),
                justify="left",
            ).pack(padx=18, pady=(4, 18), anchor="w")
            return

        # ── Toolbar ────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(root, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 10))

        search_wrap = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_wrap.pack(side="left", fill="x", expand=True)

        make_entry(
            search_wrap, self._filter_var, th,
            placeholder="Hledat podle názvu (např. chrome.exe)…",
            height=34,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._filter_var.trace_add("write", lambda *_: self._render_rows())

        make_button(
            toolbar, "  Aktualizovat", self._refresh, th,
            variant="primary", accent="primary",
            icon=icons.icon("rotate", 13, "#ffffff"), compound="left",
            height=34, width=130,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkCheckBox(
            toolbar, text="Auto-refresh",
            variable=self._auto_var, command=self._toggle_auto,
            fg_color=th["primary"], hover_color=th["primary_hover"],
            text_color=th.get("text_muted", th["text_dim"]),
            font=ctk.CTkFont("Segoe UI", 11),
            checkbox_width=18, checkbox_height=18, corner_radius=4,
        ).pack(side="left", padx=(0, 8))

        make_button(
            toolbar, "  Ukončit", self._kill_selected, th,
            variant="primary", accent="danger",
            icon=icons.icon("xmark", 13, "#ffffff"), compound="left",
            height=34, width=120,
        ).pack(side="right")

        # ── Table card ────────────────────────────────────────────────
        card = make_card(root, th, padding=0)
        card.pack(fill="both", expand=True)

        # Header row (clickable to sort)
        header = ctk.CTkFrame(card, fg_color=th.get("input_bg", th["secondary"]),
                              corner_radius=10)
        header.pack(fill="x", padx=8, pady=(8, 4))

        header.grid_columnconfigure(0, weight=0, minsize=80)    # PID
        header.grid_columnconfigure(1, weight=1)                # Name
        header.grid_columnconfigure(2, weight=0, minsize=80)    # CPU
        header.grid_columnconfigure(3, weight=0, minsize=100)   # MEM

        self._hdr_buttons = {}
        for col, (key, label) in enumerate([
            ("pid", "PID"),
            ("name", "Název"),
            ("cpu", "CPU %"),
            ("mem", "RAM MB"),
        ]):
            btn = ctk.CTkButton(
                header, text=label,
                command=lambda k=key: self._set_sort(k),
                fg_color="transparent", hover_color=th.get("card_hover", th["secondary"]),
                text_color=th.get("text_muted", th["text_dim"]),
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
                height=28, corner_radius=6, anchor="w",
            )
            btn.grid(row=0, column=col, sticky="ew", padx=2, pady=2)
            self._hdr_buttons[key] = btn

        # Scrollable list
        self._list = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=th["primary"],
            scrollbar_button_hover_color=th["primary_hover"],
        )
        self._list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Status bar
        status = ctk.CTkFrame(root, fg_color="transparent")
        status.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(
            status, textvariable=self._status_var,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(side="left")

        self._update_sort_indicator()

    # ── Data ───────────────────────────────────────────────────────────────
    def _refresh(self):
        if not PSUTIL_OK:
            return
        self._status_var.set("Načítám procesy…")

        def worker():
            rows: List[Dict] = []
            try:
                for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                    try:
                        info = p.info
                        mem = info.get("memory_info")
                        rows.append({
                            "pid": info.get("pid") or 0,
                            "name": info.get("name") or "?",
                            "cpu": float(info.get("cpu_percent") or 0.0),
                            "mem": int(mem.rss // 1024 // 1024) if mem else 0,
                        })
                    except Exception:
                        pass
            except Exception:
                pass
            self.after(0, self._on_loaded, rows)

        threading.Thread(target=worker, daemon=True).start()

    def _on_loaded(self, rows: List[Dict]):
        self._rows = rows
        self._render_rows()
        self._status_var.set(f"Načteno {len(rows)} procesů")

    def _set_sort(self, key: str):
        if self._sort_key == key:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_key = key
            self._sort_desc = key in ("cpu", "mem")
        self._update_sort_indicator()
        self._render_rows()

    def _update_sort_indicator(self):
        arrow_down = " ▼"
        arrow_up = " ▲"
        labels = {"pid": "PID", "name": "Název", "cpu": "CPU %", "mem": "RAM MB"}
        th = self.theme
        for key, btn in self._hdr_buttons.items():
            if key == self._sort_key:
                btn.configure(
                    text=labels[key] + (arrow_down if self._sort_desc else arrow_up),
                    text_color=th.get("text_strong", th["text"]),
                )
            else:
                btn.configure(
                    text=labels[key],
                    text_color=th.get("text_muted", th["text_dim"]),
                )

    # ── Render ─────────────────────────────────────────────────────────────
    def _render_rows(self):
        th = self.theme
        for ch in list(self._list.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass

        needle = (self._filter_var.get() or "").strip().lower()
        rows = list(self._rows)
        if needle:
            rows = [r for r in rows if needle in r["name"].lower() or needle == str(r["pid"])]

        rev = self._sort_desc
        key = self._sort_key
        if key == "name":
            rows.sort(key=lambda r: (r["name"] or "").lower(), reverse=rev)
        else:
            rows.sort(key=lambda r: r.get(key, 0), reverse=rev)

        # Cap to 200 rows for performance
        shown = rows[:200]
        for r in shown:
            is_sel = (r["pid"] == self._selected_pid)
            row = ctk.CTkFrame(
                self._list,
                fg_color=th.get("card_hover", th["secondary"]) if is_sel else "transparent",
                corner_radius=6,
            )
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(0, weight=0, minsize=80)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0, minsize=80)
            row.grid_columnconfigure(3, weight=0, minsize=100)

            pid = r["pid"]
            cells = [
                (str(pid), "w"),
                (r["name"], "w"),
                (f"{r['cpu']:.1f}", "e"),
                (str(r["mem"]), "e"),
            ]
            for col, (text, anchor) in enumerate(cells):
                lbl = ctk.CTkLabel(
                    row, text=text, anchor=anchor,
                    font=ctk.CTkFont("Consolas" if col != 1 else "Segoe UI", 11),
                    text_color=th["text"],
                )
                pad = (6, 6) if col == 0 else ((6, 6) if col == 1 else (6, 10))
                lbl.grid(row=0, column=col, sticky="ew", padx=pad, pady=4)
                lbl.bind("<Button-1>", lambda _e, p=pid: self._select_pid(p))
            row.bind("<Button-1>", lambda _e, p=pid: self._select_pid(p))

        if len(rows) > len(shown):
            ctk.CTkLabel(
                self._list,
                text=f"(zobrazeno prvních {len(shown)} z {len(rows)} — upřesni vyhledávání)",
                font=ctk.CTkFont("Segoe UI", 9, "italic"),
                text_color=th.get("text_muted", th["text_dim"]),
            ).pack(pady=(6, 0))

    def _select_pid(self, pid: int):
        self._selected_pid = pid
        self._render_rows()
        self._status_var.set(f"Vybráno PID {pid}")

    # ── Actions ────────────────────────────────────────────────────────────
    def _kill_selected(self):
        if not PSUTIL_OK:
            return
        if not self._selected_pid:
            messagebox.showinfo("Procesy", "Nejprve klikni na řádek s procesem.")
            return
        pid = self._selected_pid
        row = next((r for r in self._rows if r["pid"] == pid), None)
        name = row["name"] if row else f"PID {pid}"
        if not messagebox.askyesno(
            "Ukončit proces",
            f"Opravdu ukončit proces '{name}' (PID {pid})?\n\n"
            "Neuložená data v tomto procesu budou ztracena.",
        ):
            return
        try:
            p = psutil.Process(pid)
            p.terminate()
            try:
                p.wait(timeout=2.0)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
            self._status_var.set(f"Proces {name} (PID {pid}) ukončen.")
            self._selected_pid = None
            self._refresh()
        except Exception as e:
            messagebox.showerror("Procesy", f"Nelze ukončit proces:\n{e}")

    def _toggle_auto(self):
        if self._auto_var.get():
            self._schedule_auto()
        else:
            if self._auto_job:
                try:
                    self.after_cancel(self._auto_job)
                except Exception:
                    pass
                self._auto_job = None

    def _schedule_auto(self):
        if not self._auto_var.get():
            return
        self._refresh()
        self._auto_job = self.after(3000, self._schedule_auto)

    def destroy(self):
        if self._auto_job:
            try:
                self.after_cancel(self._auto_job)
            except Exception:
                pass
        super().destroy()
