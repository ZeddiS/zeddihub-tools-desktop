"""
Odpočet — countdown od nastaveného času na nulu.

v1.7.5 featury:
  • Zadání H:M:S stepper inputs + rychlé presety (30s / 1m / 5m / 10m / pomodoro 25m).
  • Milisekundová přesnost, velký display.
  • Zvuk + desktop notifikace při dokončení (nastavitelné).
  • Přiřazená akce po doběhnutí: ZOBRAZIT DIALOG | PŘEHRÁT ZVUK | SYSTEM SHUTDOWN | VLASTNÍ PŘÍKAZ.
  • Pauza / Resume / Reset.
"""

from __future__ import annotations

import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from ... import icons
from ...widgets import make_page_title, make_section_title, make_button, make_card, make_entry


def _fmt_hms(ms: int) -> str:
    if ms < 0:
        ms = 0
    total_cs = ms // 10
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}"


def _beep_async():
    """Non-blocking short beep. Uses winsound on Windows, falls back to bell."""
    try:
        import winsound
        import threading
        def _play():
            try:
                for _ in range(3):
                    winsound.Beep(880, 220)
                    time.sleep(0.08)
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()
    except Exception:
        try:
            import tkinter
            tkinter.Tk().bell()
        except Exception:
            pass


ACTIONS = [
    ("dialog",   "Zobrazit dialog"),
    ("beep",     "Přehrát zvuk"),
    ("both",     "Dialog + zvuk"),
    ("shutdown", "Vypnout počítač"),
    ("custom",   "Spustit vlastní příkaz"),
]


class OdpocetPanel(ctk.CTkFrame):
    TICK_MS = 40

    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme

        self._duration_ms = 5 * 60 * 1000  # default 5 min
        self._remaining_ms = self._duration_ms
        self._running = False
        self._end_monotonic: Optional[float] = None
        self._tick_job: Optional[str] = None
        self._action = "both"
        self._custom_cmd = ""

        self._time_var = ctk.StringVar(value=_fmt_hms(self._duration_ms))
        self._h_var = ctk.StringVar(value="0")
        self._m_var = ctk.StringVar(value="5")
        self._s_var = ctk.StringVar(value="0")
        self._cmd_var = ctk.StringVar(value="")

        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=24)

        make_page_title(
            root, "Odpočet", th,
            subtitle="Countdown timer s volitelnou akcí po doběhnutí.",
        ).pack(fill="x", anchor="w", pady=(0, 16))

        # Two columns: big display + settings
        cols = ctk.CTkFrame(root, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=3)
        cols.grid_columnconfigure(1, weight=2)

        # ── Left: display + controls ────────────────────────────────────
        left = make_card(cols, th, padding=(28, 24))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._display = ctk.CTkLabel(
            left, textvariable=self._time_var,
            font=ctk.CTkFont("JetBrains Mono, Consolas", 56, "bold"),
            text_color=th.get("text_strong", th["text"]),
        )
        self._display.pack(fill="x", pady=(10, 20))

        # Progress bar
        self._progress = ctk.CTkProgressBar(
            left, height=8,
            fg_color=th.get("input_bg", "#0f1115"),
            progress_color=th["primary"],
        )
        self._progress.set(0)
        self._progress.pack(fill="x", pady=(0, 20))

        # Buttons
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x")

        self._start_btn = make_button(
            btn_row, "  Start", self._toggle, th,
            variant="primary", accent="primary",
            icon=icons.icon("play", 15, "#ffffff"), compound="left",
            height=42, width=130,
        )
        self._start_btn.pack(side="left", padx=(0, 8))

        self._reset_btn = make_button(
            btn_row, "  Reset", self._reset, th,
            variant="ghost",
            icon=icons.icon("rotate-left", 15, th.get("text_muted", th["text_dim"])),
            compound="left", height=42, width=110,
        )
        self._reset_btn.pack(side="left")

        # ── Right: setup ────────────────────────────────────────────────
        right = make_card(cols, th, padding=(22, 20))
        right.grid(row=0, column=1, sticky="nsew")

        make_section_title(right, "Nastavení času", th).pack(fill="x", anchor="w", pady=(0, 10))

        # HMS input row
        hms = ctk.CTkFrame(right, fg_color="transparent")
        hms.pack(fill="x", pady=(0, 12))
        for label, var, max_val, col in [
            ("H", self._h_var, 99, 0),
            ("M", self._m_var, 59, 1),
            ("S", self._s_var, 59, 2),
        ]:
            box = ctk.CTkFrame(hms, fg_color="transparent")
            box.grid(row=0, column=col, padx=(0, 8), sticky="ew")
            hms.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(
                box, text=label,
                font=ctk.CTkFont("Segoe UI", 9, "bold"),
                text_color=th.get("text_muted", th["text_dim"]),
            ).pack(anchor="w", pady=(0, 3))
            e = make_entry(box, var, th, height=36)
            e.pack(fill="x")
            e.bind("<FocusOut>", lambda _e, v=var, mx=max_val: self._clamp_int(v, 0, mx))

        # Presets
        make_section_title(right, "Rychlé presety", th).pack(fill="x", anchor="w", pady=(8, 6))
        preset_row = ctk.CTkFrame(right, fg_color="transparent")
        preset_row.pack(fill="x", pady=(0, 14))
        presets = [("30s", 0, 0, 30), ("1m", 0, 1, 0), ("5m", 0, 5, 0),
                   ("10m", 0, 10, 0), ("25m", 0, 25, 0), ("1h", 1, 0, 0)]
        for i, (lbl, h, m, s) in enumerate(presets):
            make_button(
                preset_row, lbl,
                lambda hh=h, mm=m, ss=s: self._apply_preset(hh, mm, ss), th,
                variant="ghost", height=30, width=58,
                font=ctk.CTkFont("Segoe UI", 10),
            ).grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky="ew")
            preset_row.grid_columnconfigure(i % 3, weight=1)

        # Action selector
        make_section_title(right, "Akce po doběhnutí", th).pack(fill="x", anchor="w", pady=(4, 6))

        self._action_menu = ctk.CTkOptionMenu(
            right,
            values=[label for _, label in ACTIONS],
            command=self._on_action_pick,
            fg_color=th.get("input_bg", "#0f1115"),
            button_color=th["primary"],
            button_hover_color=th["primary_hover"],
            text_color=th.get("text", "#d0d0d0"),
            dropdown_fg_color=th.get("card_bg", th["secondary"]),
        )
        self._action_menu.pack(fill="x", pady=(0, 8))
        self._action_menu.set(dict(ACTIONS).get(self._action, ACTIONS[0][1]))

        # Custom command entry (visible only for 'custom')
        self._cmd_frame = ctk.CTkFrame(right, fg_color="transparent")
        ctk.CTkLabel(
            self._cmd_frame, text="Příkaz (spustí se přes subprocess)",
            font=ctk.CTkFont("Segoe UI", 9),
            text_color=th.get("text_muted", th["text_dim"]),
        ).pack(anchor="w")
        make_entry(self._cmd_frame, self._cmd_var, th,
                   placeholder="např. notepad.exe",
                   height=32).pack(fill="x", pady=(3, 0))
        # Hidden by default
        self._on_action_pick(self._action_menu.get())

    # ── Helpers ────────────────────────────────────────────────────────────
    def _clamp_int(self, var: ctk.StringVar, lo: int, hi: int):
        try:
            v = int(var.get() or "0")
        except ValueError:
            v = 0
        v = max(lo, min(hi, v))
        var.set(str(v))
        self._update_display_from_input()

    def _parse_hms(self) -> int:
        try:
            h = int(self._h_var.get() or "0")
            m = int(self._m_var.get() or "0")
            s = int(self._s_var.get() or "0")
        except ValueError:
            return 0
        return (h * 3600 + m * 60 + s) * 1000

    def _update_display_from_input(self):
        if self._running:
            return
        self._duration_ms = self._parse_hms()
        self._remaining_ms = self._duration_ms
        self._time_var.set(_fmt_hms(self._duration_ms))
        self._progress.set(0 if self._duration_ms == 0 else 0.0)

    def _apply_preset(self, h: int, m: int, s: int):
        self._h_var.set(str(h))
        self._m_var.set(str(m))
        self._s_var.set(str(s))
        self._update_display_from_input()

    def _on_action_pick(self, label: str):
        self._action = next((k for k, lbl in ACTIONS if lbl == label), self._action)
        if self._action == "custom":
            self._cmd_frame.pack(fill="x", pady=(2, 0))
        else:
            try:
                self._cmd_frame.pack_forget()
            except Exception:
                pass

    # ── Timer logic ────────────────────────────────────────────────────────
    def _toggle(self):
        if self._running:
            # Pause
            self._remaining_ms = max(0, int((self._end_monotonic - time.monotonic()) * 1000))
            self._running = False
            self._end_monotonic = None
            if self._tick_job:
                try:
                    self.after_cancel(self._tick_job)
                except Exception:
                    pass
                self._tick_job = None
            self._start_btn.configure(text="  Pokračovat",
                                      image=icons.icon("play", 15, "#ffffff"))
        else:
            if self._remaining_ms == self._duration_ms:
                # fresh start — pick up latest inputs
                self._update_display_from_input()
                if self._duration_ms == 0:
                    messagebox.showinfo("Odpočet", "Nastavte čas.")
                    return
                self._remaining_ms = self._duration_ms
            self._end_monotonic = time.monotonic() + self._remaining_ms / 1000
            self._running = True
            self._start_btn.configure(text="  Pauza",
                                      image=icons.icon("pause", 15, "#ffffff"))
            self._tick()

    def _tick(self):
        if not self._running or self._end_monotonic is None:
            return
        remaining_ms = int((self._end_monotonic - time.monotonic()) * 1000)
        if remaining_ms <= 0:
            self._time_var.set("00:00:00.00")
            self._progress.set(1.0)
            self._finish()
            return
        self._time_var.set(_fmt_hms(remaining_ms))
        done_frac = 1.0 - (remaining_ms / max(1, self._duration_ms))
        self._progress.set(max(0.0, min(1.0, done_frac)))
        self._tick_job = self.after(self.TICK_MS, self._tick)

    def _reset(self):
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None
        self._running = False
        self._end_monotonic = None
        self._duration_ms = self._parse_hms()
        self._remaining_ms = self._duration_ms
        self._time_var.set(_fmt_hms(self._duration_ms))
        self._progress.set(0)
        self._start_btn.configure(text="  Start",
                                  image=icons.icon("play", 15, "#ffffff"))

    def _finish(self):
        self._running = False
        self._end_monotonic = None
        act = self._action
        cmd = (self._cmd_var.get() or "").strip()

        if act in ("beep", "both"):
            _beep_async()
        if act in ("dialog", "both"):
            try:
                self.after(50, lambda: messagebox.showinfo(
                    "Odpočet doběhl",
                    f"Čas {_fmt_hms(self._duration_ms)} vypršel.",
                ))
            except Exception:
                pass
        if act == "shutdown":
            if messagebox.askyesno(
                "Odpočet — vypnout PC",
                "Odpočet doběhl. Vypnout počítač za 30 sekund?\n(Storno = Ano nic)",
            ):
                try:
                    if sys.platform == "win32":
                        subprocess.Popen(["shutdown", "/s", "/t", "30"])
                except Exception:
                    pass
        if act == "custom" and cmd:
            try:
                subprocess.Popen(cmd, shell=True)
            except Exception as e:
                messagebox.showerror("Odpočet — příkaz selhal", str(e))

        # Reset UI to allow re-run
        self._reset()

    def destroy(self):
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
        super().destroy()
