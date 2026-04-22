"""
MacrosPanel — main entry point for the macro system.

Layout (two columns):
  • LEFT: list of macros (cards) + toolbar (New / Import / Export / Delete).
  • RIGHT: detail view for the selected macro — name + hotkey + speed,
           step list with reorder buttons, Record / Play / Stop controls.

The panel owns a :class:`MacroStore`, :class:`MacroEngine`, :class:`MacroRecorder`
and :class:`HotkeyManager`. Hotkeys are applied on panel construction and
re-applied after every save so edits propagate without a restart.
"""

from __future__ import annotations

import json
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional

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

from .engine import MacroEngine, PYNPUT_OK as ENGINE_OK
from .hotkeys import HotkeyManager, HotkeyConflict, _display as _hk_display
from .model import Macro, make_step, summarize_step
from .recorder import MacroRecorder, PYNPUT_OK as RECORDER_OK
from .step_editor import StepEditorDialog
from .store import MacroStore


class MacrosPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme

        self._store = MacroStore()
        self._engine = MacroEngine(
            on_state=lambda s: self.after(0, self._on_engine_state, s),
            on_error=lambda m: self.after(0, self._on_engine_error, m),
            on_step=lambda c, t: self.after(0, self._on_engine_step, c, t),
        )
        self._recorder = MacroRecorder(
            on_event=lambda ev: self.after(0, self._on_recorder_event, ev),
            stop_key_name="f8",
            capture_mouse_move=False,
        )
        self._hotkeys = HotkeyManager(
            on_error=lambda msg: self.after(0, self._flash_status, msg, "error"),
        )

        # Selection state
        self._selected_id: Optional[str] = None
        self._dirty = False

        # Name + trigger vars
        self._name_var = ctk.StringVar(value="")
        self._desc_var = ctk.StringVar(value="")
        self._hotkey_var = ctk.StringVar(value="")
        self._speed_var = ctk.StringVar(value="1.0")
        self._status_var = ctk.StringVar(value="Připraveno.")

        self._build()
        self._load_and_bind_hotkeys()
        self._refresh_macro_list()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=32, pady=24)

        make_page_title(
            root, "Makra", th,
            subtitle="Záznam, úprava a spouštění klávesnicových a myšových maker.",
        ).pack(fill="x", anchor="w", pady=(0, 14))

        if not (ENGINE_OK and RECORDER_OK):
            warn = make_card(root, th, padding=18, bordered=True)
            warn.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                warn, image=icons.icon("triangle-exclamation", 22,
                                       th.get("warning", "#f59e0b")),
                text="",
            ).pack(padx=18, pady=(14, 4), anchor="w")
            ctk.CTkLabel(
                warn, text="Makra vyžadují modul pynput (globální klávesnice/myš hooky).",
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=th.get("text_strong", th["text"]),
            ).pack(padx=18, anchor="w")
            ctk.CTkLabel(
                warn, text="Spusť v terminálu:  pip install pynput  a restartuj aplikaci.",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=th.get("text_muted", th["text_dim"]),
            ).pack(padx=18, pady=(4, 16), anchor="w")
            return

        # Two-column split
        cols = ctk.CTkFrame(root, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=1, minsize=280)
        cols.grid_columnconfigure(1, weight=3)
        cols.grid_rowconfigure(0, weight=1)

        self._left = self._build_left(cols)
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._right = self._build_right(cols)
        self._right.grid(row=0, column=1, sticky="nsew")

        # Status bar
        status = ctk.CTkFrame(root, fg_color="transparent")
        status.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(
            status, textvariable=self._status_var,
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_muted", th["text_dim"]),
            anchor="w",
        ).pack(side="left")

    def _build_left(self, parent) -> ctk.CTkFrame:
        th = self.theme
        card = make_card(parent, th, padding=0)

        # Toolbar
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.pack(fill="x", padx=12, pady=(12, 6))

        make_button(toolbar, "  Nové", self._on_new, th,
                    variant="primary", accent="primary",
                    icon=icons.icon("plus", 12, "#ffffff"), compound="left",
                    height=30, width=96).pack(side="left")
        make_button(toolbar, "", self._on_import, th,
                    variant="secondary",
                    icon=icons.icon("file-arrow-up", 14,
                                    th.get("text_muted", th["text_dim"])),
                    height=30, width=36).pack(side="left", padx=(6, 0))
        make_button(toolbar, "", self._on_export, th,
                    variant="secondary",
                    icon=icons.icon("download", 14,
                                    th.get("text_muted", th["text_dim"])),
                    height=30, width=36).pack(side="left", padx=(6, 0))
        make_button(toolbar, "", self._on_delete, th,
                    variant="secondary",
                    icon=icons.icon("trash-can", 14,
                                    th.get("error", "#ef4444")),
                    height=30, width=36).pack(side="right")

        # Scrollable list
        self._list_frame = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=th["primary"],
            scrollbar_button_hover_color=th["primary_hover"],
        )
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        return card

    def _build_right(self, parent) -> ctk.CTkFrame:
        th = self.theme
        card = make_card(parent, th, padding=0)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=18)
        self._right_inner = inner

        # Header row
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")

        name_col = ctk.CTkFrame(header, fg_color="transparent")
        name_col.pack(side="left", fill="x", expand=True)
        make_label(name_col, "Název", th, size=10, bold=True,
                   color=th.get("text_muted", th["text_dim"]),
                   anchor="w").pack(fill="x", anchor="w")
        self._name_entry = make_entry(name_col, self._name_var, th, height=36)
        self._name_entry.pack(fill="x", pady=(2, 0))
        self._name_var.trace_add("write", lambda *_: self._mark_dirty())

        hk_col = ctk.CTkFrame(header, fg_color="transparent")
        hk_col.pack(side="right", padx=(12, 0))
        make_label(hk_col, "Hotkey", th, size=10, bold=True,
                   color=th.get("text_muted", th["text_dim"]),
                   anchor="w").pack(fill="x", anchor="w")
        hk_row = ctk.CTkFrame(hk_col, fg_color="transparent")
        hk_row.pack()
        self._hk_entry = make_entry(hk_row, self._hotkey_var, th,
                                     width=140, height=36,
                                     placeholder="F6 / ctrl+shift+m")
        self._hk_entry.pack(side="left")
        self._hotkey_var.trace_add("write", lambda *_: self._mark_dirty())
        make_button(hk_row, "✕", self._clear_hotkey, th,
                    variant="ghost", height=30, width=30).pack(side="left", padx=(4, 0))

        # Meta row (description + speed)
        meta = ctk.CTkFrame(inner, fg_color="transparent")
        meta.pack(fill="x", pady=(10, 0))

        desc_col = ctk.CTkFrame(meta, fg_color="transparent")
        desc_col.pack(side="left", fill="x", expand=True)
        make_label(desc_col, "Popis (volitelný)", th, size=10, bold=True,
                   color=th.get("text_muted", th["text_dim"]),
                   anchor="w").pack(fill="x", anchor="w")
        make_entry(desc_col, self._desc_var, th, height=34).pack(fill="x", pady=(2, 0))
        self._desc_var.trace_add("write", lambda *_: self._mark_dirty())

        speed_col = ctk.CTkFrame(meta, fg_color="transparent")
        speed_col.pack(side="right", padx=(12, 0))
        make_label(speed_col, "Rychlost", th, size=10, bold=True,
                   color=th.get("text_muted", th["text_dim"]),
                   anchor="w").pack(fill="x", anchor="w")
        make_entry(speed_col, self._speed_var, th, width=80, height=34
                    ).pack(pady=(2, 0))
        self._speed_var.trace_add("write", lambda *_: self._mark_dirty())

        # Controls row
        ctrl = ctk.CTkFrame(inner, fg_color="transparent")
        ctrl.pack(fill="x", pady=(14, 6))

        self._btn_record = make_button(
            ctrl, "  Záznam", self._toggle_record, th,
            variant="primary", accent="danger",
            icon=icons.icon("circle-dot", 13, "#ffffff"), compound="left",
            height=36, width=120,
        )
        self._btn_record.pack(side="left", padx=(0, 8))

        self._btn_play = make_button(
            ctrl, "  Spustit", self._toggle_play, th,
            variant="primary", accent="success",
            icon=icons.icon("play", 13, "#ffffff"), compound="left",
            height=36, width=120,
        )
        self._btn_play.pack(side="left", padx=(0, 8))

        make_button(
            ctrl, "  Uložit", self._save_current, th,
            variant="primary", accent="primary",
            icon=icons.icon("floppy-disk", 13, "#ffffff"), compound="left",
            height=36, width=120,
        ).pack(side="right")

        make_button(
            ctrl, "  Přidat krok", self._add_step_dialog, th,
            variant="secondary",
            icon=icons.icon("plus", 13, th.get("text_muted", th["text_dim"])),
            compound="left", height=36, width=130,
        ).pack(side="right", padx=(0, 8))

        make_section_title(inner, "Kroky", th).pack(fill="x", anchor="w", pady=(12, 6))
        self._steps_scroll = ctk.CTkScrollableFrame(
            inner, fg_color=th.get("input_bg", th["secondary"]),
            corner_radius=10,
            scrollbar_button_color=th["primary"],
            scrollbar_button_hover_color=th["primary_hover"],
        )
        self._steps_scroll.pack(fill="both", expand=True)

        return card

    # ── Left list rendering ───────────────────────────────────────────────
    def _refresh_macro_list(self):
        th = self.theme
        for ch in list(self._list_frame.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass

        macros = self._store.all()
        if not macros:
            ctk.CTkLabel(
                self._list_frame,
                text="Zatím žádná makra.\nKlikni na „Nové\".",
                font=ctk.CTkFont("Segoe UI", 10, "italic"),
                text_color=th.get("text_muted", th["text_dim"]),
                justify="center",
            ).pack(pady=20)
            return

        for m in macros:
            is_sel = (m.id == self._selected_id)
            row = ctk.CTkFrame(
                self._list_frame,
                fg_color=th.get("card_hover", th["secondary"]) if is_sel else "transparent",
                corner_radius=8, cursor="hand2",
            )
            row.pack(fill="x", pady=2, padx=2)

            name = ctk.CTkLabel(
                row, text=m.name, font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=th.get("text_strong", th["text"]), anchor="w",
            )
            name.pack(fill="x", padx=10, pady=(8, 0), anchor="w")

            # Subtitle: hotkey + step count
            hk = m.hotkey_combo()
            meta_text = f"{len(m.steps)} kroků"
            if hk:
                meta_text = f"{_hk_display(hk)}  ·  {meta_text}"
            ctk.CTkLabel(
                row, text=meta_text,
                font=ctk.CTkFont("Segoe UI", 10),
                text_color=th.get("text_muted", th["text_dim"]),
                anchor="w",
            ).pack(fill="x", padx=10, pady=(0, 8), anchor="w")

            # Click to select (bind on frame + label for full-row hit test)
            for w in (row, name):
                w.bind("<Button-1>", lambda _e, mid=m.id: self._select(mid))

    def _select(self, macro_id: str):
        if self._dirty and self._selected_id and self._selected_id != macro_id:
            if not messagebox.askyesno(
                "Neuložené změny",
                "Aktuální makro má neuložené změny. Zahodit je a přepnout?",
            ):
                return
        self._selected_id = macro_id
        self._dirty = False
        self._load_selected_into_form()
        self._refresh_macro_list()

    def _load_selected_into_form(self):
        m = self._store.get(self._selected_id) if self._selected_id else None
        if not m:
            self._name_var.set("")
            self._desc_var.set("")
            self._hotkey_var.set("")
            self._speed_var.set("1.0")
            self._render_steps([])
            return
        self._name_var.set(m.name)
        self._desc_var.set(m.description)
        self._hotkey_var.set(m.hotkey_combo() or "")
        self._speed_var.set(str(m.playback_speed))
        self._render_steps(m.steps)
        self._dirty = False

    def _render_steps(self, steps: List[Dict]):
        th = self.theme
        for ch in list(self._steps_scroll.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass

        if not steps:
            ctk.CTkLabel(
                self._steps_scroll,
                text="Zatím žádné kroky.\nKlikni na „Přidat krok\" nebo „Záznam\".",
                font=ctk.CTkFont("Segoe UI", 10, "italic"),
                text_color=th.get("text_muted", th["text_dim"]),
                justify="center",
            ).pack(pady=26)
            return

        for idx, step in enumerate(steps):
            row = ctk.CTkFrame(
                self._steps_scroll,
                fg_color=th.get("card_bg", th["secondary"]),
                corner_radius=6,
            )
            row.pack(fill="x", padx=6, pady=2)

            num = ctk.CTkLabel(
                row, text=f"{idx+1:>3}",
                font=ctk.CTkFont("Consolas", 10),
                text_color=th.get("text_muted", th["text_dim"]),
                width=30,
            )
            num.pack(side="left", padx=(8, 0))

            summary = ctk.CTkLabel(
                row, text=summarize_step(step),
                font=ctk.CTkFont("Consolas", 11),
                text_color=th["text"], anchor="w", justify="left",
            )
            summary.pack(side="left", fill="x", expand=True, padx=(8, 8), pady=6)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right", padx=(0, 8))

            def _mk_btn(icon_name, color, cmd, width=28):
                return ctk.CTkButton(
                    actions, text="",
                    image=icons.icon(icon_name, 12, color),
                    command=cmd, width=width, height=26,
                    corner_radius=6,
                    fg_color="transparent",
                    hover_color=th.get("card_hover", th["secondary"]),
                )

            _mk_btn("arrow-up", th.get("text_muted", th["text_dim"]),
                    lambda i=idx: self._move_step(i, -1)).pack(side="left", padx=2)
            _mk_btn("arrow-down", th.get("text_muted", th["text_dim"]),
                    lambda i=idx: self._move_step(i, +1)).pack(side="left", padx=2)
            _mk_btn("pen", th["primary"],
                    lambda i=idx: self._edit_step(i)).pack(side="left", padx=2)
            _mk_btn("trash-can", th.get("error", "#ef4444"),
                    lambda i=idx: self._delete_step(i)).pack(side="left", padx=2)

    # ── Mutation on the selected macro ────────────────────────────────────
    def _current(self) -> Optional[Macro]:
        return self._store.get(self._selected_id) if self._selected_id else None

    def _mark_dirty(self):
        if self._selected_id:
            self._dirty = True
            self._status_var.set("Neuložené změny — klikni „Uložit\".")

    def _add_step_dialog(self):
        m = self._current()
        if not m:
            messagebox.showinfo("Makra", "Nejprve vyber nebo vytvoř makro.")
            return

        def _on_save(new_step):
            m.steps.append(new_step)
            self._render_steps(m.steps)
            self._mark_dirty()

        StepEditorDialog(self, self.theme, make_step("wait"),
                         on_save=_on_save, title="Nový krok")

    def _edit_step(self, idx: int):
        m = self._current()
        if not m or idx < 0 or idx >= len(m.steps):
            return

        def _on_save(new_step):
            m.steps[idx] = new_step
            self._render_steps(m.steps)
            self._mark_dirty()

        StepEditorDialog(self, self.theme, dict(m.steps[idx]),
                         on_save=_on_save, title=f"Úprava kroku #{idx+1}")

    def _move_step(self, idx: int, delta: int):
        m = self._current()
        if not m:
            return
        new = idx + delta
        if new < 0 or new >= len(m.steps):
            return
        m.steps[idx], m.steps[new] = m.steps[new], m.steps[idx]
        self._render_steps(m.steps)
        self._mark_dirty()

    def _delete_step(self, idx: int):
        m = self._current()
        if not m or idx < 0 or idx >= len(m.steps):
            return
        m.steps.pop(idx)
        self._render_steps(m.steps)
        self._mark_dirty()

    # ── New / Import / Export / Delete ────────────────────────────────────
    def _on_new(self):
        m = Macro.new("Nové makro")
        self._store.save(m)
        self._selected_id = m.id
        self._load_selected_into_form()
        self._refresh_macro_list()
        self._flash_status("Vytvořeno nové makro.")

    def _on_delete(self):
        m = self._current()
        if not m:
            return
        if not messagebox.askyesno(
            "Smazat makro",
            f"Opravdu smazat makro '{m.name}'?\nTato akce je nevratná.",
        ):
            return
        try:
            self._hotkeys.set_binding(m.id, None, lambda: None)
        except Exception:
            pass
        self._store.delete(m.id)
        self._selected_id = None
        self._load_selected_into_form()
        self._refresh_macro_list()
        self._flash_status("Makro smazáno.")

    def _on_import(self):
        path = filedialog.askopenfilename(
            title="Importovat makro",
            filetypes=[("JSON", "*.json"), ("Všechny soubory", "*.*")],
        )
        if not path:
            return
        m = self._store.import_from(Path(path))
        if not m:
            messagebox.showerror("Import", "Soubor se nepodařilo načíst jako makro.")
            return
        self._selected_id = m.id
        self._load_selected_into_form()
        self._refresh_macro_list()
        self._flash_status(f"Importováno: {m.name}")

    def _on_export(self):
        m = self._current()
        if not m:
            return
        dst = filedialog.asksaveasfilename(
            title="Exportovat makro",
            defaultextension=".json",
            initialfile=f"{m.name}.json",
            filetypes=[("JSON", "*.json")],
        )
        if not dst:
            return
        if self._store.export_to(m.id, Path(dst)):
            self._flash_status(f"Exportováno do {dst}")

    # ── Save / hotkeys ────────────────────────────────────────────────────
    def _save_current(self):
        m = self._current()
        if not m:
            return
        m.name = (self._name_var.get() or "Bez názvu").strip()
        m.description = self._desc_var.get().strip()
        try:
            m.playback_speed = max(0.25, min(4.0, float(self._speed_var.get() or "1")))
        except ValueError:
            m.playback_speed = 1.0
        combo = (self._hotkey_var.get() or "").strip()
        if combo:
            m.trigger = {"type": "hotkey", "combo": combo}
        else:
            m.trigger = {"type": "manual"}

        # Try binding hotkey first; if conflict, abort save
        try:
            self._hotkeys.set_binding(
                m.id,
                combo or None,
                lambda mid=m.id: self._play_by_id(mid),
                macro_name=m.name,
            )
        except HotkeyConflict as hc:
            messagebox.showerror("Kolize hotkey", str(hc))
            return

        self._store.save(m)
        self._dirty = False
        self._refresh_macro_list()
        self._flash_status(f"Uloženo: {m.name}")

    def _clear_hotkey(self):
        self._hotkey_var.set("")
        self._mark_dirty()

    def _load_and_bind_hotkeys(self):
        for m in self._store.all():
            combo = m.hotkey_combo()
            if combo:
                try:
                    self._hotkeys.set_binding(
                        m.id, combo,
                        lambda mid=m.id: self._play_by_id(mid),
                        macro_name=m.name,
                    )
                except HotkeyConflict:
                    # Second+ macro claims the same combo — clear its trigger
                    m.trigger = {"type": "manual"}
                    self._store.save(m)

    # ── Record / Play ─────────────────────────────────────────────────────
    def _toggle_record(self):
        if self._recorder.recording:
            self._finish_recording()
            return
        m = self._current()
        if not m:
            messagebox.showinfo("Makra", "Nejprve vyber nebo vytvoř makro.")
            return
        # Warn if macro already has steps
        if m.steps and not messagebox.askyesno(
            "Přepsat kroky",
            "Toto makro už má kroky. Záznam je přepíše. Pokračovat?",
        ):
            return
        self._recorder.start(on_stop=lambda: self.after(0, self._finish_recording))
        self._btn_record.configure(
            text="  Stop záznam (F8)",
            image=icons.icon("stop", 13, "#ffffff"),
        )
        self._flash_status("Záznam běží — F8 pro ukončení.", "warning")

    def _finish_recording(self):
        steps = self._recorder.stop()
        m = self._current()
        if m:
            m.steps = steps
            self._render_steps(m.steps)
            self._mark_dirty()
        self._btn_record.configure(
            text="  Záznam",
            image=icons.icon("circle-dot", 13, "#ffffff"),
        )
        self._flash_status(f"Záznam dokončen — {len(steps)} kroků.")

    def _toggle_play(self):
        if self._engine.running:
            self._engine.stop()
            return
        m = self._current()
        if not m:
            return
        if not m.steps:
            messagebox.showinfo("Makra", "Makro nemá žádné kroky.")
            return
        speed = 1.0
        try:
            speed = max(0.25, min(4.0, float(self._speed_var.get() or "1")))
        except ValueError:
            pass
        self._engine.play(list(m.steps), speed=speed)

    def _play_by_id(self, macro_id: str):
        """Hotkey-driven playback — looks up macro by id and plays it."""
        m = self._store.get(macro_id)
        if not m or not m.steps or self._engine.running:
            return
        self._engine.play(list(m.steps), speed=m.playback_speed or 1.0)

    # ── Engine / Recorder callbacks (main thread) ─────────────────────────
    def _on_engine_state(self, state: str):
        th = self.theme
        if state == "running":
            self._btn_play.configure(
                text="  Zastavit",
                image=icons.icon("stop", 13, "#ffffff"),
                fg_color=th.get("error", "#ef4444"),
                hover_color=th.get("error", "#ef4444"),
            )
            self._flash_status("Makro běží…", "info")
        else:
            self._btn_play.configure(
                text="  Spustit",
                image=icons.icon("play", 13, "#ffffff"),
                fg_color=th.get("success", "#22c55e"),
                hover_color=th.get("success", "#22c55e"),
            )
            self._flash_status("Makro dokončeno.")

    def _on_engine_error(self, msg: str):
        self._flash_status(msg, "error")

    def _on_engine_step(self, cur: int, total: int):
        self._status_var.set(f"Krok {cur}/{total}…")

    def _on_recorder_event(self, ev: str):
        if ev == "stopped" and self._recorder.stop_requested:
            self._finish_recording()

    # ── Status ────────────────────────────────────────────────────────────
    def _flash_status(self, text: str, kind: str = "info"):
        self._status_var.set(text)

    # ── Lifecycle ─────────────────────────────────────────────────────────
    def destroy(self):
        try:
            self._engine.stop()
        except Exception:
            pass
        try:
            if self._recorder.recording:
                self._recorder.stop()
        except Exception:
            pass
        # Keep hotkey bindings alive so global triggers work after panel switch?
        # Better to clear — user expects macros off when panel is gone unless
        # we promote HotkeyManager to app-level. For v1.7.6 we clear on panel
        # destroy; v1.7.6+ can move this to MainWindow.
        try:
            self._hotkeys.clear_all()
        except Exception:
            pass
        super().destroy()


__all__ = ["MacrosPanel"]
