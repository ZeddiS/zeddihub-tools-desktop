"""
Časovač — budík / plánovač akce na konkrétní denní čas.

v1.7.5 featury:
  • Dva režimy:
      – "V čase HH:MM"  (absolutně — vystřelí dnes nebo zítra)
      – "Za H:M"        (relativně — za hodinu, za 2h apod.)
  • Živý náhled cílového data/času a zbývajícího odpočtu.
  • 5 akcí po vystřelení (jako Odpočet): dialog / beep / both / shutdown / custom.
  • Start / Stop toggle, tichý tick 1 Hz (stačí pro minutovou granularitu).
"""

from __future__ import annotations

import subprocess
import sys
import time
import threading
import datetime as _dt
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from ... import icons
from ...widgets import (
    make_page_title,
    make_section_title,
    make_button,
    make_card,
    make_entry,
)


def _beep_async():
    try:
        import winsound
        def _play():
            try:
                for _ in range(3):
                    winsound.Beep(880, 220)
                    time.sleep(0.08)
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()
    except Exception:
        pass


ACTIONS = [
    ("dialog",   "Zobrazit dialog"),
    ("beep",     "Přehrát zvuk"),
    ("both",     "Dialog + zvuk"),
    ("shutdown", "Vypnout počítač"),
    ("custom",   "Spustit vlastní příkaz"),
]

MODE_ABS = "abs"
MODE_REL = "rel"


def _fmt_countdown(secs: int) -> str:
    if secs < 0:
        secs = 0
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class CasovacPanel(ctk.CTkFrame):
    TICK_MS = 500  # 2× za sekundu, aby se sekundový odpočet tvářil plynule

    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme

        self._mode = MODE_ABS
        self._target_ts: Optional[float] = None   # epoch seconds
        self._running = False
        self._tick_job: Optional[str] = None
        self._action = "both"
        self._custom_cmd = ""

        # Absolute HH:MM
        self._abs_h_var = ctk.StringVar(value=_dt.datetime.now().strftime("%H"))
        self._abs_m_var = ctk.StringVar(value="00")
        # Relative H:M
        self._rel_h_var = ctk.StringVar(value="0")
        self._rel_m_var = ctk.StringVar(value="30")

        self._cmd_var = ctk.StringVar(value="")
        self._target_text = ctk.StringVar(value="—")
        self._remain_text = ctk.StringVar(value="--:--")

        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=24)

        make_page_title(
            root, "Časovač", th,
            subtitle="Budík / plánovač akce na konkrétní čas nebo za zadanou dobu.",
        ).pack(fill="x", anchor="w", pady=(0, 16))

        cols = ctk.CTkFrame(root, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=3)
        cols.grid_columnconfigure(1, weight=2)

        # ── Left: live preview + controls ──────────────────────────────
        left = make_card(cols, th, padding=(28, 24))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        inner_l = ctk.CTkFrame(left, fg_color="transparent")
        inner_l.pack(fill="both", expand=True, padx=22, pady=18)

        ctk.CTkLabel(
            inner_l, text="Cílový čas",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(fill="x", anchor="w")

        ctk.CTkLabel(
            inner_l, textvariable=self._target_text,
            font=ctk.CTkFont("JetBrains Mono, Consolas", 36, "bold"),
            text_color=th.get("text_strong", th["text"]),
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(2, 18))

        ctk.CTkLabel(
            inner_l, text="Zbývá",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(fill="x", anchor="w")

        ctk.CTkLabel(
            inner_l, textvariable=self._remain_text,
            font=ctk.CTkFont("JetBrains Mono, Consolas", 28),
            text_color=th["primary"],
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(2, 24))

        btn_row = ctk.CTkFrame(inner_l, fg_color="transparent")
        btn_row.pack(fill="x")

        self._start_btn = make_button(
            btn_row, "  Spustit", self._toggle, th,
            variant="primary", accent="primary",
            icon=icons.icon("play", 15, "#ffffff"), compound="left",
            height=42, width=140,
        )
        self._start_btn.pack(side="left", padx=(0, 8))

        make_button(
            btn_row, "  Reset", self._stop, th,
            variant="ghost",
            icon=icons.icon("rotate-left", 15, th.get("text_muted", th["text_dim"])),
            compound="left", height=42, width=110,
        ).pack(side="left")

        # ── Right: settings ─────────────────────────────────────────────
        right = make_card(cols, th, padding=(22, 20))
        right.grid(row=0, column=1, sticky="nsew")

        inner_r = ctk.CTkFrame(right, fg_color="transparent")
        inner_r.pack(fill="both", expand=True, padx=18, pady=16)

        make_section_title(inner_r, "Režim", th).pack(fill="x", anchor="w", pady=(0, 6))

        # Mode switch (two radio-ish buttons)
        mode_row = ctk.CTkFrame(inner_r, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 12))
        mode_row.grid_columnconfigure(0, weight=1)
        mode_row.grid_columnconfigure(1, weight=1)

        self._mode_abs_btn = make_button(
            mode_row, "V čase HH:MM",
            lambda: self._switch_mode(MODE_ABS), th,
            variant="primary", accent="primary", height=34, width=10,
        )
        self._mode_abs_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self._mode_rel_btn = make_button(
            mode_row, "Za H:M",
            lambda: self._switch_mode(MODE_REL), th,
            variant="secondary", height=34, width=10,
        )
        self._mode_rel_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Absolute inputs
        self._abs_frame = ctk.CTkFrame(inner_r, fg_color="transparent")
        self._abs_frame.pack(fill="x", pady=(0, 10))
        self._build_hm_pair(self._abs_frame, self._abs_h_var, self._abs_m_var,
                            h_max=23, m_max=59)

        # Relative inputs
        self._rel_frame = ctk.CTkFrame(inner_r, fg_color="transparent")
        self._build_hm_pair(self._rel_frame, self._rel_h_var, self._rel_m_var,
                            h_max=99, m_max=59)

        # Action selector
        make_section_title(inner_r, "Akce po vypršení", th).pack(fill="x", anchor="w", pady=(8, 6))

        self._action_menu = ctk.CTkOptionMenu(
            inner_r,
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

        self._cmd_frame = ctk.CTkFrame(inner_r, fg_color="transparent")
        ctk.CTkLabel(
            self._cmd_frame, text="Příkaz (spustí se přes subprocess)",
            font=ctk.CTkFont("Segoe UI", 9),
            text_color=th.get("text_muted", th["text_dim"]),
        ).pack(anchor="w")
        make_entry(self._cmd_frame, self._cmd_var, th,
                   placeholder="např. notepad.exe",
                   height=32).pack(fill="x", pady=(3, 0))

        self._on_action_pick(self._action_menu.get())
        self._update_preview()  # initial

    def _build_hm_pair(self, parent, h_var, m_var, *, h_max: int, m_max: int):
        th = self.theme
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=0)
        parent.grid_columnconfigure(2, weight=1)

        for col, (lbl, var, mx) in enumerate([
            ("Hodiny", h_var, h_max),
            (":",       None, None),
            ("Minuty", m_var, m_max),
        ]):
            if var is None:
                ctk.CTkLabel(
                    parent, text=lbl,
                    font=ctk.CTkFont("Segoe UI", 20, "bold"),
                    text_color=th.get("text_muted", th["text_dim"]),
                ).grid(row=0, column=col, rowspan=2, padx=6)
                continue
            ctk.CTkLabel(
                parent, text=lbl,
                font=ctk.CTkFont("Segoe UI", 9, "bold"),
                text_color=th.get("text_muted", th["text_dim"]),
                anchor="w",
            ).grid(row=0, column=col, sticky="w", pady=(0, 2))
            e = make_entry(parent, var, th, height=36)
            e.grid(row=1, column=col, sticky="ew")
            e.bind("<FocusOut>", lambda _e, v=var, m=mx: self._clamp_int(v, 0, m))
            e.bind("<KeyRelease>", lambda _e: self._update_preview())

    # ── Mode / preview helpers ─────────────────────────────────────────────
    def _switch_mode(self, mode: str):
        if self._running:
            return  # don't allow mid-run switch
        self._mode = mode
        if mode == MODE_ABS:
            self._mode_abs_btn.configure(
                fg_color=self.theme["primary"],
                hover_color=self.theme["primary_hover"],
                text_color=self.theme.get("nav_active_text", "#ffffff"),
            )
            self._mode_rel_btn.configure(
                fg_color="transparent",
                hover_color=self.theme.get("card_hover", self.theme["secondary"]),
                text_color=self.theme.get("text", "#d0d0d0"),
            )
            self._rel_frame.pack_forget()
            self._abs_frame.pack(fill="x", pady=(0, 10))
        else:
            self._mode_rel_btn.configure(
                fg_color=self.theme["primary"],
                hover_color=self.theme["primary_hover"],
                text_color=self.theme.get("nav_active_text", "#ffffff"),
            )
            self._mode_abs_btn.configure(
                fg_color="transparent",
                hover_color=self.theme.get("card_hover", self.theme["secondary"]),
                text_color=self.theme.get("text", "#d0d0d0"),
            )
            self._abs_frame.pack_forget()
            self._rel_frame.pack(fill="x", pady=(0, 10))
        self._update_preview()

    def _clamp_int(self, var: ctk.StringVar, lo: int, hi: int):
        try:
            v = int(var.get() or "0")
        except ValueError:
            v = 0
        v = max(lo, min(hi, v))
        var.set(f"{v:02d}" if hi >= 59 and hi <= 60 else str(v))
        self._update_preview()

    def _compute_target(self) -> Optional[_dt.datetime]:
        now = _dt.datetime.now().replace(microsecond=0)
        try:
            if self._mode == MODE_ABS:
                h = int(self._abs_h_var.get() or "0")
                m = int(self._abs_m_var.get() or "0")
                h = max(0, min(23, h))
                m = max(0, min(59, m))
                target = now.replace(hour=h, minute=m, second=0)
                if target <= now:
                    target = target + _dt.timedelta(days=1)
                return target
            else:
                h = int(self._rel_h_var.get() or "0")
                m = int(self._rel_m_var.get() or "0")
                if h == 0 and m == 0:
                    return None
                return now + _dt.timedelta(hours=h, minutes=m)
        except ValueError:
            return None

    def _update_preview(self):
        if self._running:
            # Running: live target is fixed
            if self._target_ts:
                t = _dt.datetime.fromtimestamp(self._target_ts)
                self._target_text.set(t.strftime("%d.%m.  %H:%M:%S"))
                remain = int(self._target_ts - time.time())
                self._remain_text.set(_fmt_countdown(remain))
            return
        target = self._compute_target()
        if not target:
            self._target_text.set("—")
            self._remain_text.set("--:--")
            return
        self._target_text.set(target.strftime("%d.%m.  %H:%M"))
        remain = int((target - _dt.datetime.now()).total_seconds())
        self._remain_text.set(_fmt_countdown(remain))

    def _on_action_pick(self, label: str):
        self._action = next((k for k, lbl in ACTIONS if lbl == label), self._action)
        if self._action == "custom":
            self._cmd_frame.pack(fill="x", pady=(2, 0))
        else:
            try:
                self._cmd_frame.pack_forget()
            except Exception:
                pass

    # ── Control ───────────────────────────────────────────────────────────
    def _toggle(self):
        if self._running:
            self._stop()
            return
        target = self._compute_target()
        if not target:
            messagebox.showinfo("Časovač", "Nastavte cílový čas.")
            return
        self._target_ts = target.timestamp()
        self._running = True
        self._start_btn.configure(
            text="  Stop",
            image=icons.icon("stop", 15, "#ffffff"),
        )
        self._tick()

    def _tick(self):
        if not self._running or self._target_ts is None:
            return
        remain = int(self._target_ts - time.time())
        if remain <= 0:
            self._remain_text.set("00:00")
            self._fire()
            return
        self._remain_text.set(_fmt_countdown(remain))
        self._tick_job = self.after(self.TICK_MS, self._tick)

    def _stop(self):
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
            self._tick_job = None
        self._running = False
        self._target_ts = None
        self._start_btn.configure(
            text="  Spustit",
            image=icons.icon("play", 15, "#ffffff"),
        )
        self._update_preview()

    def _fire(self):
        self._running = False
        act = self._action
        cmd = (self._cmd_var.get() or "").strip()
        target_ts = self._target_ts
        self._target_ts = None

        if act in ("beep", "both"):
            _beep_async()
        if act in ("dialog", "both"):
            try:
                when = (
                    _dt.datetime.fromtimestamp(target_ts).strftime("%H:%M:%S")
                    if target_ts else "—"
                )
                self.after(50, lambda: messagebox.showinfo(
                    "Časovač vypršel",
                    f"Nastavený čas {when} nastal.",
                ))
            except Exception:
                pass
        if act == "shutdown":
            if messagebox.askyesno(
                "Časovač — vypnout PC",
                "Čas nastal. Vypnout počítač za 30 sekund?",
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
                messagebox.showerror("Časovač — příkaz selhal", str(e))

        self._start_btn.configure(
            text="  Spustit",
            image=icons.icon("play", 15, "#ffffff"),
        )
        self._update_preview()

    def destroy(self):
        if self._tick_job:
            try:
                self.after_cancel(self._tick_job)
            except Exception:
                pass
        super().destroy()
