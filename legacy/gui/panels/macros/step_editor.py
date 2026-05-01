"""
StepEditorDialog — modal window for editing a single step's fields.

The editor is generic: it looks up ``DEFAULT_STEP`` for the selected step
type to decide which widgets to render. Changing the dropdown swaps out the
field widgets in-place so the user can change e.g. ``wait`` → ``key_tap``
without opening a new dialog.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import customtkinter as ctk

from ...widgets import make_button, make_entry, make_label, make_section_title
from .model import DEFAULT_STEP, STEP_LABELS, STEP_TYPES, make_step


class StepEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, theme: dict, step: Dict[str, Any],
                 *, on_save: Callable[[Dict[str, Any]], None],
                 title: str = "Úprava kroku"):
        super().__init__(parent)
        self.theme = theme
        self._on_save = on_save
        self._original = dict(step)
        self._current_type = step.get("type", "wait")
        self._widgets: Dict[str, ctk.CTkBaseClass] = {}
        self._vars: Dict[str, ctk.Variable] = {}

        self.title(title)
        self.configure(fg_color=theme["content_bg"])
        self.geometry("460x520")
        self.resizable(False, False)
        self.transient(parent)
        self.after(100, self._lift_and_grab)

        self._build()
        self._render_fields(self._current_type)

    def _lift_and_grab(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def _build(self):
        th = self.theme
        pad = ctk.CTkFrame(self, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=22, pady=18)

        make_section_title(pad, "Typ kroku", th).pack(fill="x", anchor="w", pady=(0, 6))

        type_values = [f"{STEP_LABELS.get(t, t)}" for t in STEP_TYPES]
        type_to_label = {t: STEP_LABELS.get(t, t) for t in STEP_TYPES}
        label_to_type = {v: k for k, v in type_to_label.items()}

        self._type_menu = ctk.CTkOptionMenu(
            pad, values=type_values,
            command=lambda label: self._on_type_change(label_to_type.get(label, "wait")),
            fg_color=th.get("input_bg", th["secondary"]),
            button_color=th["primary"],
            button_hover_color=th["primary_hover"],
            text_color=th.get("text", "#d0d0d0"),
            dropdown_fg_color=th.get("card_bg", th["secondary"]),
        )
        self._type_menu.pack(fill="x", pady=(0, 14))
        self._type_menu.set(type_to_label.get(self._current_type, type_values[0]))

        # Field frame (swappable)
        self._fields_frame = ctk.CTkFrame(pad, fg_color="transparent")
        self._fields_frame.pack(fill="both", expand=True)

        # Footer with save/cancel
        footer = ctk.CTkFrame(pad, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 0))

        make_button(footer, "Zrušit", self._cancel, th,
                    variant="secondary", height=36, width=110).pack(side="left")
        make_button(footer, "Uložit", self._save, th,
                    variant="primary", accent="primary", height=36, width=120
                    ).pack(side="right")

    # ── Field rendering per step type ──────────────────────────────────────
    def _on_type_change(self, new_type: str):
        if new_type == self._current_type:
            return
        self._current_type = new_type
        self._render_fields(new_type)

    def _render_fields(self, step_type: str):
        # Clear existing field widgets
        for ch in list(self._fields_frame.winfo_children()):
            try:
                ch.destroy()
            except Exception:
                pass
        self._widgets.clear()
        self._vars.clear()

        th = self.theme
        defaults = DEFAULT_STEP.get(step_type, {})
        # If editor opened with same type, seed from original; otherwise defaults
        src = self._original if self._original.get("type") == step_type else {
            "type": step_type, **defaults,
        }

        row = 0
        for key, default_val in defaults.items():
            container = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            container.pack(fill="x", pady=(0, 8))

            make_label(container, self._label_for(step_type, key), th,
                       size=10, bold=True,
                       color=th.get("text_muted", th["text_dim"]),
                       anchor="w").pack(fill="x", anchor="w")

            cur_val = src.get(key, default_val)
            if isinstance(default_val, bool):
                var = ctk.BooleanVar(value=bool(cur_val))
                cb = ctk.CTkCheckBox(
                    container, text="", variable=var,
                    fg_color=th["primary"], hover_color=th["primary_hover"],
                    checkbox_width=18, checkbox_height=18, corner_radius=4,
                )
                cb.pack(anchor="w", pady=(2, 0))
                self._vars[key] = var
                self._widgets[key] = cb
            elif key == "button":
                var = ctk.StringVar(value=str(cur_val))
                om = ctk.CTkOptionMenu(
                    container, values=["left", "right", "middle"], variable=var,
                    fg_color=th.get("input_bg", th["secondary"]),
                    button_color=th["primary"], button_hover_color=th["primary_hover"],
                )
                om.pack(fill="x", pady=(2, 0))
                self._vars[key] = var
                self._widgets[key] = om
            elif key == "keys":
                # list of strings
                var = ctk.StringVar(value="+".join(cur_val or []))
                e = make_entry(container, var, th, height=32,
                               placeholder="např. ctrl+shift+c")
                e.pack(fill="x", pady=(2, 0))
                self._vars[key] = var
                self._widgets[key] = e
            elif key == "rgb":
                vals = list(cur_val or [0, 0, 0])
                while len(vals) < 3:
                    vals.append(0)
                var = ctk.StringVar(value=",".join(str(int(v)) for v in vals[:3]))
                e = make_entry(container, var, th, height=32,
                               placeholder="R,G,B (0-255)")
                e.pack(fill="x", pady=(2, 0))
                self._vars[key] = var
                self._widgets[key] = e
            else:
                # int, float, str, or None → text entry
                display_val = "" if cur_val is None else str(cur_val)
                var = ctk.StringVar(value=display_val)
                e = make_entry(container, var, th, height=32)
                e.pack(fill="x", pady=(2, 0))
                self._vars[key] = var
                self._widgets[key] = e
            row += 1

        if not defaults:
            make_label(self._fields_frame,
                       "Tento krok nemá žádná nastavení.",
                       th, size=11,
                       color=th.get("text_muted", th["text_dim"])).pack(pady=20)

    @staticmethod
    def _label_for(step_type: str, key: str) -> str:
        human = {
            "key": "Klávesa (např. a, f6, space)",
            "keys": "Kombinace (např. ctrl+shift+c)",
            "text": "Text",
            "interval_ms": "Rozestup mezi znaky (ms)",
            "button": "Tlačítko myši",
            "x": "X souřadnice",
            "y": "Y souřadnice",
            "clicks": "Počet kliknutí",
            "hold_ms": "Držet tlačítko (ms)",
            "relative": "Relativně k aktuální pozici",
            "dx": "Horizontální scroll",
            "dy": "Vertikální scroll (kladné = nahoru)",
            "ms": "Pauza (ms)",
            "min_ms": "Pauza min (ms)",
            "max_ms": "Pauza max (ms)",
            "count": "Počet opakování (0 = nekonečno)",
            "rgb": "Očekávaná barva R,G,B",
            "tolerance": "Tolerance (±)",
        }
        return human.get(key, key)

    # ── Save / cancel ─────────────────────────────────────────────────────
    def _collect(self) -> Optional[Dict[str, Any]]:
        defaults = DEFAULT_STEP.get(self._current_type, {})
        new_step: Dict[str, Any] = {"type": self._current_type}
        for key, default_val in defaults.items():
            var = self._vars.get(key)
            if var is None:
                new_step[key] = default_val
                continue
            raw = var.get()
            if isinstance(default_val, bool):
                new_step[key] = bool(raw)
            elif key == "keys":
                parts = [p.strip().lower() for p in str(raw).split("+") if p.strip()]
                if not parts:
                    parts = list(default_val)
                new_step[key] = parts
            elif key == "rgb":
                try:
                    parts = [int(p.strip()) for p in str(raw).split(",")[:3]]
                    while len(parts) < 3:
                        parts.append(0)
                    new_step[key] = [max(0, min(255, v)) for v in parts]
                except Exception:
                    new_step[key] = list(default_val)
            elif isinstance(default_val, int) or default_val is None and key in ("x", "y"):
                s = str(raw).strip()
                if s == "":
                    new_step[key] = None if default_val is None else default_val
                else:
                    try:
                        new_step[key] = int(float(s))
                    except ValueError:
                        new_step[key] = default_val if default_val is not None else 0
            elif isinstance(default_val, float):
                try:
                    new_step[key] = float(str(raw))
                except ValueError:
                    new_step[key] = default_val
            else:
                new_step[key] = str(raw)
        return new_step

    def _save(self):
        new_step = self._collect()
        if new_step is None:
            return
        try:
            self._on_save(new_step)
        finally:
            self.destroy()

    def _cancel(self):
        self.destroy()
