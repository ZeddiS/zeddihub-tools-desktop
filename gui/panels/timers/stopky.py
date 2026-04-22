"""
Stopky — přesné stopky s kruhy (laps), historií, exportem a global hotkey.

v1.7.5 featury:
  • Milisekundová přesnost (10ms tick).
  • Start / Pauza / Reset přes tlačítka nebo globální hotkey (Ctrl+Alt+S / Ctrl+Alt+L).
  • Laps s delta mezi koly + total.
  • Historie ukončených měření (uloženo v data dir → stopky_history.json).
  • Export aktuálního běhu do TXT.
"""

from __future__ import annotations

import json
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk

from ... import icons
from ...config import get_data_dir
from ...widgets import make_page_title, make_section_title, make_button, make_card


HISTORY_FILE = "stopky_history.json"
MAX_HISTORY = 50


def _fmt_hms(ms: int) -> str:
    """Format milliseconds as HH:MM:SS.cs (centiseconds — 2 digits)."""
    total_cs = ms // 10
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}"


def _history_path() -> Path:
    return get_data_dir() / HISTORY_FILE


def _load_history() -> list:
    p = _history_path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_history(entries: list) -> None:
    p = _history_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(entries[-MAX_HISTORY:], ensure_ascii=False, indent=2),
                     encoding="utf-8")
    except Exception:
        pass


class StopkyPanel(ctk.CTkFrame):
    """Stopky (stopwatch) with laps + history."""

    TICK_MS = 40  # UI refresh cadence (~25 Hz) — perceived smooth

    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme

        # Timing state
        self._running = False
        self._start_monotonic: Optional[float] = None
        self._accumulated_ms = 0
        self._laps: List[int] = []   # absolute-elapsed ms at each lap

        # UI references
        self._time_var = ctk.StringVar(value="00:00:00.00")
        self._lap_list: Optional[ctk.CTkTextbox] = None
        self._tick_job: Optional[str] = None

        self._build()

        # Keyboard shortcuts (panel-level — active while panel focused)
        self.bind_all("<Control-space>", lambda _e: self._toggle(), add="+")
        self.bind_all("<Control-l>",     lambda _e: self._lap(),    add="+")
        self.bind_all("<Control-r>",     lambda _e: self._reset(),  add="+")

    # ── UI construction ────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=24)

        make_page_title(
            root, "Stopky", th,
            subtitle="Přesné stopky s kruhy (laps) a historií. Ctrl+Space = Start/Stop · Ctrl+L = Lap · Ctrl+R = Reset.",
        ).pack(fill="x", anchor="w", pady=(0, 16))

        # Two-column layout: big time display + laps list
        cols = ctk.CTkFrame(root, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=3)
        cols.grid_columnconfigure(1, weight=2)
        cols.grid_rowconfigure(0, weight=1)

        # ── Left: time + controls ────────────────────────────────────────
        left = make_card(cols, th, padding=(28, 24))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            left,
            textvariable=self._time_var,
            font=ctk.CTkFont("JetBrains Mono, Consolas", 56, "bold"),
            text_color=th.get("text_strong", th["text"]),
        ).pack(fill="x", pady=(10, 24))

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", pady=(6, 0))

        self._start_btn = make_button(
            btn_row, "  Start", self._toggle, th,
            variant="primary", accent="primary",
            icon=icons.icon("play", 15, "#ffffff"), compound="left",
            height=42, width=130,
        )
        self._start_btn.pack(side="left", padx=(0, 8))

        self._lap_btn = make_button(
            btn_row, "  Lap", self._lap, th,
            variant="secondary",
            icon=icons.icon("flag", 15, th.get("text_strong", th["text"])),
            compound="left", height=42, width=110,
            state="disabled",
        )
        self._lap_btn.pack(side="left", padx=(0, 8))

        self._reset_btn = make_button(
            btn_row, "  Reset", self._reset, th,
            variant="ghost",
            icon=icons.icon("rotate-left", 15, th.get("text_muted", th["text_dim"])),
            compound="left", height=42, width=110,
            state="disabled",
        )
        self._reset_btn.pack(side="left")

        # Export + save-to-history row
        row2 = ctk.CTkFrame(left, fg_color="transparent")
        row2.pack(fill="x", pady=(14, 0))

        make_button(
            row2, "  Uložit do historie", self._save_to_history, th,
            variant="ghost",
            icon=icons.icon("bookmark", 13, th.get("text_muted", th["text_dim"])),
            compound="left", height=34, width=170,
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(0, 8))

        make_button(
            row2, "  Export TXT", self._export_txt, th,
            variant="ghost",
            icon=icons.icon("file-arrow-down", 13, th.get("text_muted", th["text_dim"])),
            compound="left", height=34, width=130,
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left")

        # ── Right: laps list ────────────────────────────────────────────
        right = make_card(cols, th, padding=(18, 16))
        right.grid(row=0, column=1, sticky="nsew")

        make_section_title(right, "Kruhy (laps)", th).pack(fill="x", anchor="w")

        self._lap_list = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont("JetBrains Mono, Consolas", 12),
            fg_color=th.get("input_bg", "#0f1115"),
            text_color=th.get("text", "#d0d0d0"),
            border_width=0,
            corner_radius=8,
        )
        self._lap_list.pack(fill="both", expand=True, pady=(8, 0))
        self._lap_list.configure(state="disabled")

        # ── Bottom: history ──────────────────────────────────────────────
        hist_card = make_card(root, th, padding=(18, 16))
        hist_card.pack(fill="x", pady=(16, 0))

        header_row = ctk.CTkFrame(hist_card, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 8))
        make_section_title(header_row, "Historie měření", th).pack(side="left")
        make_button(
            header_row, "  Vyčistit", self._clear_history, th,
            variant="ghost",
            icon=icons.icon("trash", 12, th.get("text_muted", th["text_dim"])),
            compound="left", height=28, width=110,
            font=ctk.CTkFont("Segoe UI", 10),
        ).pack(side="right")

        self._history_box = ctk.CTkTextbox(
            hist_card,
            height=140,
            font=ctk.CTkFont("Segoe UI", 10),
            fg_color=th.get("input_bg", "#0f1115"),
            text_color=th.get("text_muted", th["text_dim"]),
            border_width=0,
            corner_radius=8,
        )
        self._history_box.pack(fill="x")
        self._history_box.configure(state="disabled")

        self._refresh_history()

    # ── Timer logic ────────────────────────────────────────────────────────
    def _elapsed_ms(self) -> int:
        if self._running and self._start_monotonic is not None:
            delta = int((time.monotonic() - self._start_monotonic) * 1000)
            return self._accumulated_ms + delta
        return self._accumulated_ms

    def _tick(self):
        self._time_var.set(_fmt_hms(self._elapsed_ms()))
        if self._running:
            self._tick_job = self.after(self.TICK_MS, self._tick)

    def _toggle(self):
        if self._running:
            # Pause
            self._accumulated_ms = self._elapsed_ms()
            self._running = False
            self._start_monotonic = None
            if self._tick_job:
                try:
                    self.after_cancel(self._tick_job)
                except Exception:
                    pass
                self._tick_job = None
            self._start_btn.configure(
                text="  Pokračovat",
                image=icons.icon("play", 15, "#ffffff"),
            )
        else:
            # Start / resume
            self._start_monotonic = time.monotonic()
            self._running = True
            self._tick()
            self._start_btn.configure(
                text="  Pauza",
                image=icons.icon("pause", 15, "#ffffff"),
            )
            self._lap_btn.configure(state="normal")
            self._reset_btn.configure(state="normal")

    def _lap(self):
        if not self._running and self._elapsed_ms() == 0:
            return
        elapsed = self._elapsed_ms()
        self._laps.append(elapsed)
        self._render_laps()

    def _render_laps(self):
        if self._lap_list is None:
            return
        self._lap_list.configure(state="normal")
        self._lap_list.delete("1.0", "end")
        prev = 0
        for i, total in enumerate(self._laps, 1):
            delta = total - prev
            prev = total
            self._lap_list.insert(
                "end",
                f"Lap {i:02d}   +{_fmt_hms(delta)}   total {_fmt_hms(total)}\n",
            )
        self._lap_list.see("end")
        self._lap_list.configure(state="disabled")

    def _reset(self):
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None
        self._running = False
        self._start_monotonic = None
        self._accumulated_ms = 0
        self._laps.clear()
        self._time_var.set("00:00:00.00")
        self._start_btn.configure(
            text="  Start",
            image=icons.icon("play", 15, "#ffffff"),
        )
        self._lap_btn.configure(state="disabled")
        self._reset_btn.configure(state="disabled")
        self._render_laps()

    # ── History ────────────────────────────────────────────────────────────
    def _save_to_history(self):
        total = self._elapsed_ms()
        if total == 0:
            messagebox.showinfo("Stopky", "Nic se neměří.")
            return
        entry = {
            "ts": int(time.time()),
            "total_ms": total,
            "laps_ms": list(self._laps),
            "label": f"Měření {time.strftime('%Y-%m-%d %H:%M:%S')}",
        }
        hist = _load_history()
        hist.append(entry)
        _save_history(hist)
        self._refresh_history()

    def _clear_history(self):
        if not messagebox.askyesno("Historie stopek", "Vymazat celou historii?"):
            return
        _save_history([])
        self._refresh_history()

    def _refresh_history(self):
        if not hasattr(self, "_history_box"):
            return
        self._history_box.configure(state="normal")
        self._history_box.delete("1.0", "end")
        hist = list(reversed(_load_history()))
        if not hist:
            self._history_box.insert("end", "(zatím prázdné)\n")
        else:
            for h in hist:
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h.get("ts", 0)))
                total = _fmt_hms(h.get("total_ms", 0))
                n_laps = len(h.get("laps_ms") or [])
                self._history_box.insert(
                    "end", f"[{ts}]  {total}  ({n_laps} laps)\n"
                )
        self._history_box.configure(state="disabled")

    # ── Export ─────────────────────────────────────────────────────────────
    def _export_txt(self):
        total = self._elapsed_ms()
        if total == 0:
            messagebox.showinfo("Stopky", "Nic se neměří.")
            return
        path = filedialog.asksaveasfilename(
            title="Export stopek",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Vše", "*.*")],
            initialfile=f"stopky_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not path:
            return
        try:
            lines = [
                f"ZeddiHub Tools — Stopky",
                f"Export: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Celkový čas: {_fmt_hms(total)}",
                "",
                "Laps:",
            ]
            prev = 0
            for i, lap_total in enumerate(self._laps, 1):
                delta = lap_total - prev
                prev = lap_total
                lines.append(
                    f"  {i:02d}  +{_fmt_hms(delta)}   total {_fmt_hms(lap_total)}"
                )
            Path(path).write_text("\n".join(lines), encoding="utf-8")
            messagebox.showinfo("Stopky", f"Uloženo: {path}")
        except Exception as e:
            messagebox.showerror("Stopky", f"Uložení selhalo: {e}")

    # Clean up hotkey bindings when panel is destroyed
    def destroy(self):
        try:
            self.unbind_all("<Control-space>")
            self.unbind_all("<Control-l>")
            self.unbind_all("<Control-r>")
        except Exception:
            pass
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
        super().destroy()
