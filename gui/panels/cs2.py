"""
ZeddiHub Tools - CS2 Player & Server Tools GUI panels.
"""

import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .. import icons


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    font = ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal")
    return ctk.CTkLabel(parent, text=text, font=font,
                        text_color=color or "#ffffff", **kw)


def _btn(parent, text, cmd, theme, width=180, height=36, **kw):
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        fg_color=theme["primary"], hover_color=theme["primary_hover"],
        text_color=theme["button_fg"],
        font=ctk.CTkFont("Segoe UI", 12, "bold"),
        width=width, height=height, **kw
    )


def _section(parent, title, theme):
    f = ctk.CTkFrame(parent, fg_color=theme["card_bg"], corner_radius=8)
    f.pack(fill="x", padx=0, pady=6)
    _label(f, title, 13, bold=True, color=theme["primary"]).pack(
        padx=14, pady=(10, 6), anchor="w")
    return f


def _entry_row(parent, label_text, default_val, theme, row, hint=""):
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    e = ctk.CTkEntry(parent, textvariable=var, width=160,
                     fg_color=theme["secondary"], text_color=theme["text"],
                     font=ctk.CTkFont("Courier New", 11))
    e.grid(row=row, column=1, padx=4, pady=3, sticky="w")
    if hint:
        ctk.CTkLabel(parent, text=hint, font=ctk.CTkFont("Segoe UI", 9),
                     text_color=theme["text_dim"]
                     ).grid(row=row, column=2, padx=4, pady=3, sticky="w")
    return var


def _bool_row(parent, label_text, default_val, theme, row, hint=""):
    """Dropdown row for boolean (0/1) values."""
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    ctk.CTkOptionMenu(parent, variable=var,
                      values=["0", "1"],
                      fg_color=theme["secondary"], button_color=theme["primary"],
                      button_hover_color=theme["primary_hover"],
                      text_color=theme["text"],
                      font=ctk.CTkFont("Segoe UI", 11), width=80, height=28,
                      ).grid(row=row, column=1, padx=4, pady=3, sticky="w")
    if hint:
        ctk.CTkLabel(parent, text=hint, font=ctk.CTkFont("Segoe UI", 9),
                     text_color=theme["text_dim"]
                     ).grid(row=row, column=2, padx=4, pady=3, sticky="w")
    return var


def _dropdown_row(parent, label_text, options: list, default_val, theme, row, hint=""):
    """Dropdown row for discrete string/numeric values."""
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    ctk.CTkOptionMenu(parent, variable=var,
                      values=[str(o) for o in options],
                      fg_color=theme["secondary"], button_color=theme["primary"],
                      button_hover_color=theme["primary_hover"],
                      text_color=theme["text"],
                      font=ctk.CTkFont("Segoe UI", 11), width=160, height=28,
                      ).grid(row=row, column=1, padx=4, pady=3, sticky="w")
    if hint:
        ctk.CTkLabel(parent, text=hint, font=ctk.CTkFont("Segoe UI", 9),
                     text_color=theme["text_dim"]
                     ).grid(row=row, column=2, padx=4, pady=3, sticky="w")
    return var


def _stepper_row(parent, label_text, default_val, min_val, max_val, step, theme, row, hint=""):
    """Numeric stepper row with – / + buttons."""
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    cell = ctk.CTkFrame(parent, fg_color="transparent")
    cell.grid(row=row, column=1, padx=4, pady=3, sticky="w")

    def _clamp(v):
        try:
            if isinstance(step, float) or isinstance(min_val, float):
                val = round(max(float(min_val), min(float(max_val), float(v))), 4)
                return str(int(val)) if val == int(val) else str(val)
            else:
                return str(max(int(min_val), min(int(max_val), int(float(v)))))
        except (ValueError, TypeError):
            return str(default_val)

    def _dec():
        try:
            cur = float(var.get())
            var.set(_clamp(cur - step))
        except ValueError:
            var.set(str(default_val))

    def _inc():
        try:
            cur = float(var.get())
            var.set(_clamp(cur + step))
        except ValueError:
            var.set(str(default_val))

    ctk.CTkButton(cell, text="−", width=28, height=28,
                  fg_color=theme["secondary"], hover_color=theme["primary"],
                  font=ctk.CTkFont("Segoe UI", 13, "bold"),
                  text_color=theme["text"], command=_dec
                  ).pack(side="left")
    ctk.CTkEntry(cell, textvariable=var, width=70,
                 fg_color=theme["secondary"], text_color=theme["text"],
                 font=ctk.CTkFont("Courier New", 11), justify="center"
                 ).pack(side="left", padx=2)
    ctk.CTkButton(cell, text="+", width=28, height=28,
                  fg_color=theme["secondary"], hover_color=theme["primary"],
                  font=ctk.CTkFont("Segoe UI", 13, "bold"),
                  text_color=theme["text"], command=_inc
                  ).pack(side="left")
    if hint:
        ctk.CTkLabel(parent, text=hint, font=ctk.CTkFont("Segoe UI", 9),
                     text_color=theme["text_dim"]
                     ).grid(row=row, column=2, padx=4, pady=3, sticky="w")
    return var


def _make_scrollable(parent, theme):
    scroll = ctk.CTkScrollableFrame(parent, fg_color=theme["content_bg"])
    scroll.pack(fill="both", expand=True, padx=0, pady=0)
    return scroll


# ─────────────────────────────────────────────
# CS2 PLAYER TOOLS
# ─────────────────────────────────────────────

class CS2PlayerPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        t = self.theme
        tab = ctk.CTkTabview(self, fg_color=t["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("Crosshair")
        tab.add("🔫 Viewmodel")
        tab.add("📝 Autoexec")
        tab.add("Practice")
        tab.add("🛒 Buy Binds")

        self._build_crosshair(tab.tab("Crosshair"))
        self._build_viewmodel(tab.tab("🔫 Viewmodel"))
        self._build_autoexec(tab.tab("📝 Autoexec"))
        self._build_practice(tab.tab("Practice"))
        self._build_buybinds(tab.tab("🛒 Buy Binds"))

    # ── CROSSHAIR ──────────────────────────────
    def _build_crosshair(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True)

        # Pack right first so left can fill remaining space
        right = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=10, width=260)
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)

        left = ctk.CTkFrame(main, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 0))

        scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        _label(scroll, "CS2 – Crosshair Generátor", 16, bold=True,
               color=t["primary"]).pack(padx=12, pady=(12, 4), anchor="w")
        _label(scroll, "Nastavte parametry a vygenerujte .cfg soubor.",
               11, color=t["text_dim"]).pack(padx=12, pady=(0, 10), anchor="w")

        sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        sec.pack(fill="x", padx=8, pady=4)
        sec.grid_columnconfigure(1, weight=1)

        self._xhair_vars = {}
        row = 0
        # Discrete dropdowns
        self._xhair_vars["cl_crosshairstyle"] = _dropdown_row(
            sec, "Styl", ["0","1","2","3","4","5"], "4", t, row,
            "0=Default,1=Static,2=Classic,3=CS:GO,4=Small,5=Tiny"); row += 1
        self._xhair_vars["cl_crosshaircolor"] = _dropdown_row(
            sec, "Barva", ["0","1","2","3","4","5"], "1", t, row,
            "0=Červená,1=Zelená,2=Žlutá,3=Modrá,4=Cyan,5=Custom"); row += 1
        # Steppers for numeric ranges
        self._xhair_vars["cl_crosshairsize"] = _stepper_row(
            sec, "Velikost", "2", 0, 10, 0.5, t, row, "0–10"); row += 1
        self._xhair_vars["cl_crosshairthickness"] = _stepper_row(
            sec, "Tloušťka", "0.5", 0, 3, 0.5, t, row, "0–3"); row += 1
        self._xhair_vars["cl_crosshairgap"] = _stepper_row(
            sec, "Mezera", "-1", -10, 10, 1, t, row, "záporná = menší"); row += 1
        self._xhair_vars["cl_crosshair_outlinethickness"] = _stepper_row(
            sec, "Tl. obrysu", "1", 0, 3, 0.5, t, row, "0–3"); row += 1
        self._xhair_vars["cl_crosshairalpha"] = _stepper_row(
            sec, "Průhlednost", "255", 0, 255, 10, t, row, "0–255"); row += 1
        # Booleans
        self._xhair_vars["cl_crosshairdot"] = _bool_row(
            sec, "Tečka", "0", t, row, "0=Ne / 1=Ano"); row += 1
        self._xhair_vars["cl_crosshair_drawoutline"] = _bool_row(
            sec, "Obrys", "1", t, row, "0=Ne / 1=Ano"); row += 1
        self._xhair_vars["cl_crosshair_t"] = _bool_row(
            sec, "T-shape", "0", t, row, "0=Ne / 1=Ano"); row += 1

        _btn(scroll, "💾 Uložit crosshair.cfg", self._save_crosshair, t).pack(
            padx=8, pady=10, fill="x")

        ctk.CTkButton(scroll, text=" Kopírovat share kód",
                      image=icons.icon("copy", 14, "#cccccc"), compound="left",
                      command=self._copy_crosshair_code,
                      fg_color=t["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 11), height=32
                      ).pack(padx=8, pady=(0, 10), fill="x")

        # Preview canvas in right panel
        _label(right, "Náhled", 12, bold=True, color=t["text_dim"]).pack(pady=(14, 6))
        self.xhair_canvas = tk.Canvas(right, width=220, height=160,
                                      bg=t["card_bg"], highlightthickness=0)
        self.xhair_canvas.pack(padx=10, pady=4)
        _btn(right, "↻ Aktualizovat", self._update_xhair_preview, t,
             width=140, height=30).pack(pady=8)

        self._update_xhair_preview()
        # Auto-refresh on var change
        for var in self._xhair_vars.values():
            var.trace_add("write", lambda *_: self.after(200, self._update_xhair_preview))

    def _update_xhair_preview(self):
        try:
            c = self.xhair_canvas
            c.delete("all")
            w, h = 220, 160
            cx, cy = w // 2, h // 2

            size = max(0, int(float(self._xhair_vars["cl_crosshairsize"].get())))
            gap = int(float(self._xhair_vars["cl_crosshairgap"].get()))
            thickness = max(1, int(float(self._xhair_vars["cl_crosshairthickness"].get()) * 3))
            dot = int(float(self._xhair_vars["cl_crosshairdot"].get())) == 1
            color_idx = int(self._xhair_vars["cl_crosshaircolor"].get())
            t_shape = int(float(self._xhair_vars["cl_crosshair_t"].get())) == 1
            outline = int(float(self._xhair_vars["cl_crosshair_drawoutline"].get())) == 1

            colors_map = ["#dd3333", "#33dd33", "#dddd33", "#3333ff", "#33dddd", "#ffffff"]
            color = colors_map[color_idx] if 0 <= color_idx < len(colors_map) else "#33dd33"

            scale = 4
            half_t = thickness // 2
            g = max(0, gap * scale)
            s = max(2, size * scale)

            if outline:
                oc = "#000000"
                ow = 2
                if not t_shape:
                    c.create_rectangle(cx - half_t - ow, cy - g - s - ow,
                                       cx + half_t + ow + 1, cy - g + ow, fill=oc, outline="")
                c.create_rectangle(cx - half_t - ow, cy + g - ow,
                                   cx + half_t + ow + 1, cy + g + s + ow, fill=oc, outline="")
                c.create_rectangle(cx - g - s - ow, cy - half_t - ow,
                                   cx - g + ow, cy + half_t + ow + 1, fill=oc, outline="")
                c.create_rectangle(cx + g - ow, cy - half_t - ow,
                                   cx + g + s + ow, cy + half_t + ow + 1, fill=oc, outline="")

            if not t_shape:
                c.create_rectangle(cx - half_t, cy - g - s, cx + half_t + 1, cy - g, fill=color, outline="")
            c.create_rectangle(cx - half_t, cy + g, cx + half_t + 1, cy + g + s, fill=color, outline="")
            c.create_rectangle(cx - g - s, cy - half_t, cx - g, cy + half_t + 1, fill=color, outline="")
            c.create_rectangle(cx + g, cy - half_t, cx + g + s, cy + half_t + 1, fill=color, outline="")

            if dot:
                c.create_oval(cx - 2, cy - 2, cx + 3, cy + 3, fill=color, outline="")
        except Exception:
            pass

    def _save_crosshair(self):
        path = filedialog.asksaveasfilename(
            title="Uložit crosshair.cfg",
            defaultextension=".cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")],
            initialfile="cs2_crosshair.cfg"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS2 Crosshair - Generated by ZeddiHub Tools\n// https://zeddihub.eu\n\n")
            for k, var in self._xhair_vars.items():
                f.write(f'{k} "{var.get()}"\n')
        messagebox.showinfo("Uloženo", f"Crosshair cfg uložen:\n{path}")

    def _copy_crosshair_code(self):
        parts = [f"{k} {var.get()}" for k, var in self._xhair_vars.items()]
        code = "; ".join(parts)
        self.clipboard_clear()
        self.clipboard_append(code)
        messagebox.showinfo("Zkopírováno", "Share kód zkopírován do schránky!\n\nVložte ho do konzole CS2.")

    # ── VIEWMODEL ─────────────────────────────
    def _build_viewmodel(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True)

        right = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=10, width=260)
        right.pack(side="right", fill="y", padx=(8, 0))
        right.pack_propagate(False)

        left = ctk.CTkFrame(main, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        _label(scroll, "CS2 – Viewmodel Generátor", 16, bold=True,
               color=t["primary"]).pack(padx=12, pady=(12, 4), anchor="w")

        sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        sec.pack(fill="x", padx=8, pady=4)
        sec.grid_columnconfigure(1, weight=1)

        self._vm_vars = {}
        vrow = 0
        self._vm_vars["viewmodel_fov"] = _stepper_row(
            sec, "FOV", "68", 54, 68, 1, t, vrow, "54–68"); vrow += 1
        self._vm_vars["viewmodel_offset_x"] = _stepper_row(
            sec, "Offset X", "2.5", -2.5, 2.5, 0.5, t, vrow, "−2.5 – +2.5"); vrow += 1
        self._vm_vars["viewmodel_offset_y"] = _stepper_row(
            sec, "Offset Y", "0", -2.5, 2.5, 0.5, t, vrow, "−2.5 – +2.5"); vrow += 1
        self._vm_vars["viewmodel_offset_z"] = _stepper_row(
            sec, "Offset Z", "-1.5", -2.5, 2.5, 0.5, t, vrow, "−2.5 – +2.5"); vrow += 1
        self._vm_vars["viewmodel_presetpos"] = _dropdown_row(
            sec, "Preset", ["1","2","3"], "3", t, vrow,
            "1=Desktop / 2=Couch / 3=Classic"); vrow += 1
        self._vm_vars["cl_bob_lower_amt"] = _stepper_row(
            sec, "Bob Lower", "5", 5, 30, 1, t, vrow, "5–30"); vrow += 1
        self._vm_vars["cl_bobamt_lat"] = _stepper_row(
            sec, "Bob Lat", "0.1", 0.0, 2.0, 0.1, t, vrow, "0–2"); vrow += 1
        self._vm_vars["cl_bobamt_vert"] = _stepper_row(
            sec, "Bob Vert", "0.1", 0.0, 2.0, 0.1, t, vrow, "0–2"); vrow += 1

        _btn(scroll, "💾 Uložit viewmodel.cfg", self._save_viewmodel, t).pack(
            padx=8, pady=10, fill="x")

        # Presets
        presets_frame = _section(scroll, "Rychlé presety", t)
        presets = [
            ("Competitive (Classic)", {"viewmodel_fov":"68","viewmodel_offset_x":"2.5","viewmodel_offset_y":"0","viewmodel_offset_z":"-1.5","viewmodel_presetpos":"3"}),
            ("Nový preset (Wide FOV)", {"viewmodel_fov":"68","viewmodel_offset_x":"-2","viewmodel_offset_y":"0","viewmodel_offset_z":"-2","viewmodel_presetpos":"1"}),
            ("Pro player style",       {"viewmodel_fov":"68","viewmodel_offset_x":"2.5","viewmodel_offset_y":"0","viewmodel_offset_z":"-1.5","viewmodel_presetpos":"3","cl_bob_lower_amt":"21","cl_bobamt_lat":"0.33","cl_bobamt_vert":"0.14"}),
        ]
        for name, vals in presets:
            ctk.CTkButton(
                presets_frame, text=name, height=30,
                fg_color=t["secondary"], hover_color=t["primary"],
                font=ctk.CTkFont("Segoe UI", 11),
                command=lambda v=vals: self._apply_vm_preset(v)
            ).pack(padx=12, pady=3, fill="x")

        # Preview
        _label(right, "Náhled zbraně", 12, bold=True, color=t["text_dim"]).pack(pady=(14, 4))
        _label(right, "Boční pohled — přibližné umístění", 9, color=t["text_dark"]
               ).pack(pady=(0, 6))
        self.vm_canvas = tk.Canvas(right, width=260, height=200,
                                   bg=t["card_bg"], highlightthickness=0)
        self.vm_canvas.pack(padx=4)
        self._draw_vm_preview()
        for var in self._vm_vars.values():
            var.trace_add("write", lambda *_: self.after(300, self._draw_vm_preview))

    def _apply_vm_preset(self, vals: dict):
        for k, v in vals.items():
            if k in self._vm_vars:
                self._vm_vars[k].set(v)

    def _draw_vm_preview(self):
        """Draw a top-down CS2-style rifle silhouette on the preview canvas."""
        try:
            c = self.vm_canvas
            c.delete("all")
            W, H = 260, 200

            fov = float(self._vm_vars["viewmodel_fov"].get())
            ox  = float(self._vm_vars["viewmodel_offset_x"].get())
            oz  = float(self._vm_vars["viewmodel_offset_z"].get())

            bg   = self.theme.get("card_bg", "#1a1a1a")
            col  = self.theme["primary"]
            dim  = self.theme.get("text_dark", "#444444")
            xhair = "#22dd22"

            c.configure(bg=bg)

            # ── Screen border ──────────────────────────────────────────────
            c.create_rectangle(2, 2, W-2, H-2, outline=dim, width=1)

            # ── Crosshair (screen center) ────────��─────────────────────────
            cx, cy = W // 2, H // 2
            for dx, dy in [(-8,0),(8,0),(0,-8),(0,8)]:
                c.create_line(cx+dx, cy+dy,
                              cx+dx*2, cy+dy*2, fill=xhair, width=2)

            # ── Weapon position on screen ──────────────────────────────────
            # Base position: bottom-right of screen
            # fov=68 → normal; lower fov → weapon appears closer (larger, higher)
            # offset_x: positive = more right; offset_z: negative = lower
            fov_scale = (68 - fov) * 0.8        # higher fov → weapon further away
            gx = int(W * 0.72 - ox * 9 + fov_scale)
            gy = int(H * 0.68 - oz * 9 + fov_scale * 0.3)
            gx = max(60, min(W - 10, gx))
            gy = max(40, min(H - 10, gy))

            # Scale factor based on FOV (lower = bigger weapon)
            scale = 1.0 + (68 - fov) * 0.03
            s = scale

            # ── AK-47 / M4 silhouette (side view, pointing left) ──────────
            # Barrel (long horizontal tube)
            bx, by = gx - int(90*s), gy
            c.create_rectangle(bx,    by-3,  gx-int(30*s), by+3,
                                fill=col, outline="")
            # Muzzle brake
            c.create_rectangle(bx-4, by-5, bx+2, by+5, fill=col, outline="")

            # Upper receiver / body
            rx1, ry1 = gx-int(30*s), by-int(8*s)
            rx2, ry2 = gx+int(18*s), by+int(10*s)
            c.create_rectangle(rx1, ry1, rx2, ry2, fill=col, outline="")

            # Pistol grip
            c.create_polygon(
                gx+int(6*s),  by+int(10*s),
                gx+int(18*s), by+int(10*s),
                gx+int(20*s), by+int(28*s),
                gx+int(8*s),  by+int(30*s),
                fill=col, outline=""
            )

            # Stock
            c.create_polygon(
                gx+int(18*s), by-int(4*s),
                gx+int(18*s), by+int(10*s),
                gx+int(42*s), by+int(10*s),
                gx+int(46*s), by+int(2*s),
                gx+int(42*s), by-int(8*s),
                fill=col, outline=""
            )
            # Stock butt plate
            c.create_rectangle(gx+int(42*s), by-int(8*s),
                                gx+int(48*s), by+int(10*s),
                                fill=col, outline="")

            # Magazine
            mag_x = gx - int(8*s)
            c.create_polygon(
                mag_x-int(8*s),  by+int(10*s),
                mag_x+int(8*s),  by+int(10*s),
                mag_x+int(6*s),  by+int(32*s),
                mag_x-int(6*s),  by+int(32*s),
                fill=col, outline=""
            )

            # Scope / sights
            c.create_rectangle(gx-int(40*s), by-int(12*s),
                                gx-int(20*s), by-int(8*s),
                                fill=col, outline="")

            # ── Info text ─────────���───────────────────────────────────────
            info = f"FOV: {fov:.0f}  X: {ox:+.1f}  Z: {oz:+.1f}"
            c.create_text(W//2, H - 14, text=info,
                          fill=self.theme.get("text_dim","#888888"),
                          font=("Segoe UI", 8))
        except Exception:
            pass

    def _save_viewmodel(self):
        path = filedialog.asksaveasfilename(
            title="Uložit viewmodel.cfg", defaultextension=".cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")],
            initialfile="cs2_viewmodel.cfg"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS2 Viewmodel - Generated by ZeddiHub Tools\n\n")
            for k, var in self._vm_vars.items():
                f.write(f'{k} "{var.get()}"\n')
        messagebox.showinfo("Uloženo", f"Viewmodel cfg uložen:\n{path}")

    # ── AUTOEXEC ──────────────────────────────
    def _build_autoexec(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS2 – Autoexec Config", 16, bold=True,
               color=t["primary"]).pack(padx=4, pady=(4, 2), anchor="w")

        categories = {
            "Síť (sub-tick)": {
                "rate": ("Rate", "786432"),
                "cl_cmdrate": ("Cmdrate", "128"),
                "cl_updaterate": ("Updaterate", "128"),
                "cl_interp_ratio": ("Interp ratio", "1"),
                "cl_interp": ("Interp", "0.015625"),
                "engine_low_latency_sleep_after_client_tick": ("Low latency sleep", "1"),
            },
            "FPS a Grafika": {
                "fps_max": ("FPS max", "0"),
                "fps_max_tools": ("FPS max tools", "120"),
                "r_drawtracers_firstperson": ("Tracery 1st", "0"),
                "cl_forcepreload": ("Force preload", "1"),
            },
            "Zvuk": {
                "snd_voipvolume": ("VOIP hlasitost", "0.5"),
                "snd_musicvolume": ("Hudba", "0"),
                "volume": ("Hlasitost", "0.5"),
            },
            "Myš": {
                "sensitivity": ("Citlivost", "1.0"),
                "zoom_sensitivity_ratio": ("Zoom cit.", "1.0"),
            },
            "Matchmaking": {
                "cl_join_advertise": ("Join advertise", "2"),
                "mm_dedicated_search_maxping": ("Max ping MM", "50"),
            },
            "Utilita": {
                "gameinstructor_enable": ("Game instructor", "0"),
                "cl_autohelp": ("Auto help", "0"),
                "con_enable": ("Console", "1"),
            },
        }

        self._ae_vars = {}
        for cat_name, fields in categories.items():
            # outer uses pack (title label), inner uses grid (entry rows) — never mix in one frame
            outer = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            outer.pack(fill="x", padx=0, pady=6)
            _label(outer, cat_name, 13, bold=True, color=t["primary"]).pack(
                padx=14, pady=(10, 6), anchor="w")
            inner = ctk.CTkFrame(outer, fg_color="transparent")
            inner.pack(fill="x", padx=0, pady=(0, 6))
            inner.grid_columnconfigure(1, weight=1)
            for i, (k, (lbl, default)) in enumerate(fields.items()):
                self._ae_vars[k] = _entry_row(inner, f"{lbl} ({k})", default, t, i)

        # Custom commands
        _label(scroll, "Vlastní příkazy:", 12, bold=True, color=t["text"]).pack(
            padx=4, pady=(8, 2), anchor="w")
        self.ae_custom = ctk.CTkTextbox(scroll, height=80,
                                        fg_color=t["secondary"], text_color=t["text"],
                                        font=ctk.CTkFont("Courier New", 11))
        self.ae_custom.pack(fill="x", padx=4, pady=4)
        self.ae_custom.insert("end", "// Přidejte vlastní příkazy zde\n// Příklad: bind f3 \"toggle cl_righthand\"\n")

        _btn(scroll, "💾 Uložit autoexec.cfg", self._save_autoexec, t).pack(
            padx=4, pady=8, fill="x")

    def _save_autoexec(self):
        path = filedialog.asksaveasfilename(
            title="Uložit autoexec.cfg", defaultextension=".cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")],
            initialfile="cs2_autoexec.cfg"
        )
        if not path:
            return
        custom = self.ae_custom.get("1.0", "end").strip()
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS2 Autoexec - Generated by ZeddiHub Tools\n// https://zeddihub.eu\n\n")
            for k, var in self._ae_vars.items():
                f.write(f'{k} "{var.get()}"\n')
            if custom and not custom.startswith("//"):
                f.write("\n// Vlastní příkazy\n")
                f.write(custom + "\n")
            f.write('\n\necho "ZeddiHub autoexec loaded!"\nhost_writeconfig\n')
        messagebox.showinfo("Uloženo", f"Autoexec uložen:\n{path}")

    # ── PRACTICE ──────────────────────────────
    def _build_practice(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS2 – Practice Config", 16, bold=True,
               color=t["primary"]).pack(padx=4, pady=(4, 2), anchor="w")
        _label(scroll, "Pro trénink granátů, nákupy kdekoliv, nekonečná munice...",
               11, color=t["text_dim"]).pack(padx=4, anchor="w")

        outer_prac = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        outer_prac.pack(fill="x", padx=0, pady=6)
        _label(outer_prac, "Nastavení", 13, bold=True, color=t["primary"]).pack(
            padx=14, pady=(10, 6), anchor="w")
        sec = ctk.CTkFrame(outer_prac, fg_color="transparent")
        sec.pack(fill="x", padx=0, pady=(0, 6))
        sec.grid_columnconfigure(1, weight=1)

        practice_defs = {
            "sv_cheats": ("SV Cheats (nutné)", "1"),
            "sv_infinite_ammo": ("Nekonečná munice", "1"),
            "mp_buy_anywhere": ("Kupovat kdekoliv", "1"),
            "mp_buytime": ("Buy time", "99999"),
            "mp_freezetime": ("Freeze time", "0"),
            "mp_roundtime_defuse": ("Round time (min)", "60"),
            "mp_roundtime": ("Round time alt", "60"),
            "mp_maxmoney": ("Max peníze", "65535"),
            "mp_startmoney": ("Start peníze", "65535"),
            "sv_grenade_trajectory_prac_pipreview": ("Nade trajektorie", "1"),
            "sv_grenade_trajectory_prac_trailtime": ("Nade trail time", "4"),
            "cl_grenadepreview": ("Grenade preview", "1"),
        }
        self._prac_vars = {}
        for i, (k, (lbl, default)) in enumerate(practice_defs.items()):
            self._prac_vars[k] = _entry_row(sec, lbl, default, t, i)

        _btn(scroll, "💾 Uložit practice.cfg", self._save_practice, t).pack(
            padx=4, pady=10, fill="x")

    def _save_practice(self):
        path = filedialog.asksaveasfilename(
            title="Uložit practice.cfg", defaultextension=".cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")],
            initialfile="cs2_practice.cfg"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS2 Practice Mode - Generated by ZeddiHub Tools\n")
            f.write("// Použijte: exec cs2_practice\n\n")
            f.write("mp_warmup_end\nbot_kick\n\n")
            for k, var in self._prac_vars.items():
                f.write(f"{k} {var.get()}\n")
            f.write("\nmp_restartgame 1\necho \"Practice mode activated!\"\n")
        messagebox.showinfo("Uloženo", f"Practice cfg uložen:\n{path}")

    # ── BUY BINDS ─────────────────────────────
    def _build_buybinds(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS2 – Buy Binds Generátor", 16, bold=True,
               color=t["primary"]).pack(padx=4, pady=(4, 8), anchor="w")

        self._bind_vars = {}
        binds_default = {
            "kp_ins":       ("AK-47 / M4A4",               "buy ak47; buy m4a1;"),
            "kp_end":       ("AWP",                         "buy awp;"),
            "kp_downarrow": ("Deagle",                      "buy deagle;"),
            "kp_pgdn":      ("Armor + Defuse",              "buy vesthelm; buy defuser;"),
            "kp_leftarrow": ("Smoke + Flash + Molotov",     "buy smokegrenade; buy flashbang; buy molotov; buy incgrenade;"),
            "kp_5":         ("HE Grenade",                  "buy hegrenade;"),
            "kp_rightarrow":("Decoy",                       "buy decoy;"),
            "kp_home":      ("MP9 / MAC-10",                "buy mp9; buy mac10;"),
            "kp_uparrow":   ("Famas / Galil",               "buy famas; buy galilar;"),
            "kp_pgup":      ("Full Buy",                    "buy ak47; buy m4a1; buy vesthelm; buy defuser; buy smokegrenade; buy flashbang; buy molotov; buy hegrenade;"),
        }

        outer_bb = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        outer_bb.pack(fill="x", padx=0, pady=6)
        _label(outer_bb, "Klávesy a příkazy", 13, bold=True, color=t["primary"]).pack(
            padx=14, pady=(10, 6), anchor="w")
        sec = ctk.CTkFrame(outer_bb, fg_color="transparent")
        sec.pack(fill="x", padx=0, pady=(0, 6))
        sec.grid_columnconfigure(0, minsize=160)
        sec.grid_columnconfigure(1, minsize=160)
        sec.grid_columnconfigure(2, weight=1)

        for i, (key, (label, cmd)) in enumerate(binds_default.items()):
            ctk.CTkLabel(sec, text=f"[{key}]  {label}",
                         font=ctk.CTkFont("Courier New", 11),
                         text_color=t["text"], anchor="w"
                         ).grid(row=i, column=0, padx=(12, 4), pady=3, sticky="w")
            var = ctk.StringVar(value=cmd)
            ctk.CTkEntry(sec, textvariable=var, width=300,
                         fg_color=t["secondary"], text_color=t["text"],
                         font=ctk.CTkFont("Courier New", 10)
                         ).grid(row=i, column=1, columnspan=2, padx=4, pady=3, sticky="ew")
            self._bind_vars[key] = var

        _btn(scroll, "💾 Uložit buybinds.cfg", self._save_buybinds, t).pack(
            padx=4, pady=10, fill="x")

    def _save_buybinds(self):
        path = filedialog.asksaveasfilename(
            title="Uložit buybinds.cfg", defaultextension=".cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")],
            initialfile="cs2_buybinds.cfg"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS2 Buy Binds - Generated by ZeddiHub Tools\n\n")
            for key, var in self._bind_vars.items():
                f.write(f'bind "{key}" "{var.get()}"\n')
            f.write('\necho "ZeddiHub buy binds loaded!"\n')
        messagebox.showinfo("Uloženo", f"Buy binds uloženy:\n{path}")


# ─────────────────────────────────────────────
# CS2 SERVER TOOLS
# ─────────────────────────────────────────────

class CS2ServerPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        t = self.theme
        tab = ctk.CTkTabview(self, fg_color=t["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("Server.cfg")
        tab.add("Gamemode Presety")
        tab.add("🗺 Map Group")
        tab.add("RCON Klient")

        self._build_servercfg(tab.tab("Server.cfg"))
        self._build_gamemode(tab.tab("Gamemode Presety"))
        self._build_mapgroup(tab.tab("🗺 Map Group"))
        self._build_rcon(tab.tab("RCON Klient"))

    def _build_servercfg(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS2 – Server.cfg Generátor", 16, bold=True,
               color=t["primary"]).pack(padx=4, pady=(4, 8), anchor="w")

        self._srv_vars = {}

        def _srv_section(title):
            outer = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            outer.pack(fill="x", padx=0, pady=6)
            _label(outer, title, 13, bold=True, color=t["primary"]).pack(
                padx=14, pady=(10, 6), anchor="w")
            inner = ctk.CTkFrame(outer, fg_color="transparent")
            inner.pack(fill="x", padx=0, pady=(0, 6))
            inner.grid_columnconfigure(1, weight=1)
            return inner

        # Základní
        s = _srv_section("Základní")
        self._srv_vars["hostname"]      = _entry_row(s, "Název serveru", "ZeddiHub CS2 Server", t, 0)
        self._srv_vars["sv_password"]   = _entry_row(s, "Heslo serveru", "", t, 1)
        self._srv_vars["rcon_password"] = _entry_row(s, "RCON heslo", "changeme", t, 2)
        self._srv_vars["sv_cheats"]     = _bool_row(s, "SV Cheats", "0", t, 3)
        self._srv_vars["sv_lan"]        = _bool_row(s, "LAN only", "0", t, 4)

        # Gamemode
        s = _srv_section("Gamemode")
        self._srv_vars["game_type"] = _dropdown_row(
            s, "Game type", ["0","1","2"], "0", t, 0, "0=Classic,1=GunGame,2=Training")
        self._srv_vars["game_mode"] = _dropdown_row(
            s, "Game mode", ["0","1","2","3"], "1", t, 1, "0=Casual,1=Comp,2=Wingman,3=DM")

        # Network
        s = _srv_section("Network")
        self._srv_vars["sv_maxrate"]        = _stepper_row(s, "Max rate",        "0",      0, 2000000, 128000, t, 0)
        self._srv_vars["sv_minrate"]        = _stepper_row(s, "Min rate",        "128000", 0, 786432,  64000,  t, 1)
        self._srv_vars["sv_maxcmdrate"]     = _dropdown_row(s, "Max cmdrate",    ["64","100","128"], "128", t, 2)
        self._srv_vars["sv_mincmdrate"]     = _dropdown_row(s, "Min cmdrate",    ["32","64","100","128"], "64", t, 3)
        self._srv_vars["sv_maxupdaterate"]  = _dropdown_row(s, "Max updaterate", ["64","100","128"], "128", t, 4)
        self._srv_vars["sv_minupdaterate"]  = _dropdown_row(s, "Min updaterate", ["32","64","100","128"], "64", t, 5)

        # Gameplay
        s = _srv_section("Gameplay")
        self._srv_vars["mp_autoteambalance"] = _bool_row(s, "Auto team balance", "1", t, 0)
        self._srv_vars["mp_limitteams"]      = _bool_row(s, "Limit teams",       "1", t, 1)
        self._srv_vars["mp_friendlyfire"]    = _bool_row(s, "Friendly fire",     "0", t, 2)
        self._srv_vars["mp_maxrounds"]       = _dropdown_row(s, "Max rounds", ["12","16","24","30"], "24", t, 3)
        self._srv_vars["mp_roundtime"]       = _stepper_row(s, "Round time (min)", "1.92", 0.5, 10.0, 0.5, t, 4)
        self._srv_vars["mp_freezetime"]      = _stepper_row(s, "Freeze time (s)",  "15",   0,   30,   1,   t, 5)
        self._srv_vars["mp_buytime"]         = _stepper_row(s, "Buy time (s)",     "20",   0,   90,   5,   t, 6)

        # Komunikace
        s = _srv_section("Komunikace")
        self._srv_vars["sv_alltalk"]    = _bool_row(s, "All talk",     "0", t, 0)
        self._srv_vars["sv_deadtalk"]   = _bool_row(s, "Dead talk",    "1", t, 1)
        self._srv_vars["sv_allow_votes"]= _bool_row(s, "Allow votes",  "1", t, 2)

        # GOTV
        s = _srv_section("GOTV")
        self._srv_vars["tv_enable"] = _bool_row(s, "GOTV enable", "1", t, 0)
        self._srv_vars["tv_delay"]  = _stepper_row(s, "GOTV delay (s)", "30", 0, 120, 10, t, 1)

        _btn(scroll, "💾 Uložit server.cfg", self._save_servercfg, t).pack(
            padx=4, pady=10, fill="x")

    def _save_servercfg(self):
        path = filedialog.asksaveasfilename(
            title="Uložit server.cfg", defaultextension=".cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")],
            initialfile="server.cfg"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS2 Server Config - Generated by ZeddiHub Tools\n// https://zeddihub.eu\n\n")
            for k, var in self._srv_vars.items():
                v = var.get()
                if k in ("hostname", "sv_password", "rcon_password") and v:
                    f.write(f'{k} "{v}"\n')
                elif v:
                    f.write(f'{k} {v}\n')
            f.write('\necho "[ZeddiHub] Server config loaded!"\n')
        messagebox.showinfo("Uloženo", f"server.cfg uložen:\n{path}")

    def _build_gamemode(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS2 – Gamemode Presety", 16, bold=True,
               color=t["primary"]).pack(padx=4, pady=(4, 8), anchor="w")

        modes = {
            "Competitive 5v5": {"game_mode":"1","game_type":"0","mp_maxrounds":"24","mp_roundtime":"1.92","mp_freezetime":"15","mp_buytime":"20","mp_startmoney":"800"},
            "Competitive MR12 (Premier)": {"game_mode":"1","game_type":"0","mp_maxrounds":"24","mp_roundtime":"1.92","mp_freezetime":"15","mp_buytime":"20","mp_startmoney":"800","mp_overtime_enable":"1","mp_overtime_maxrounds":"6"},
            "Wingman 2v2": {"game_mode":"2","game_type":"0","mp_maxrounds":"16","mp_roundtime":"1.5","mp_freezetime":"10","mp_buytime":"15","mp_startmoney":"800"},
            "Deathmatch": {"game_mode":"2","game_type":"1","mp_roundtime":"10","mp_freezetime":"0","mp_buytime":"0","mp_startmoney":"65535","sv_infinite_ammo":"2","mp_respawn_on_death_ct":"1","mp_respawn_on_death_t":"1"},
            "Casual": {"game_mode":"0","game_type":"0","mp_maxrounds":"15","mp_roundtime":"2.25","mp_freezetime":"10","mp_buytime":"30","mp_startmoney":"1000"},
            "Retake": {"game_mode":"0","game_type":"0","mp_maxrounds":"8","mp_roundtime":"0.92","mp_freezetime":"3","mp_buytime":"0","mp_startmoney":"0","sv_enablebunnyhopping":"1"},
            "1v1 Arena": {"game_mode":"1","game_type":"0","mp_maxrounds":"16","mp_roundtime":"1.5","mp_freezetime":"5","mp_buytime":"0","mp_startmoney":"16000","mp_teammates_are_enemies":"0"},
        }

        for mode_name, cmds in modes.items():
            card = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            card.pack(fill="x", pady=4)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=mode_name, font=ctk.CTkFont("Segoe UI", 13, "bold"),
                         text_color=t["accent"], anchor="w"
                         ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")
            ctk.CTkLabel(card, text="  ".join(f"{k}={v}" for k, v in list(cmds.items())[:4]),
                         font=ctk.CTkFont("Courier New", 9), text_color=t["text_dim"], anchor="w"
                         ).grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")
            ctk.CTkButton(
                card, text="💾 Generovat", height=30, width=120,
                fg_color=t["primary"], hover_color=t["primary_hover"],
                font=ctk.CTkFont("Segoe UI", 11),
                command=lambda n=mode_name, c=cmds: self._save_gamemode(n, c)
            ).grid(row=0, column=1, rowspan=2, padx=12, pady=8)

    def _save_gamemode(self, name: str, cmds: dict):
        safe = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        path = filedialog.asksaveasfilename(
            title=f"Uložit {name}",
            defaultextension=".cfg",
            initialfile=f"cs2_gamemode_{safe}.cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"// CS2 Gamemode: {name}\n// Generated by ZeddiHub Tools\n\n")
            for k, v in cmds.items():
                f.write(f"{k} {v}\n")
            f.write(f'\necho "[ZeddiHub] Gamemode {name} loaded!"\n')
        messagebox.showinfo("Uloženo", f"Gamemode cfg uložen:\n{path}")

    def _build_mapgroup(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        _label(main, "CS2 – Map Group Editor", 16, bold=True,
               color=t["primary"]).pack(padx=4, pady=(4, 8), anchor="w")

        row = ctk.CTkFrame(main, fg_color="transparent")
        row.pack(fill="both", expand=True)

        # Left: pools
        left = ctk.CTkFrame(row, fg_color=t["card_bg"], corner_radius=8, width=240)
        left.pack(side="left", fill="both", padx=(0, 8))
        left.pack_propagate(False)
        _label(left, "Map Pools", 12, bold=True, color=t["text_dim"]).pack(padx=10, pady=8)

        self._map_pools = {
            "Active Duty": ["de_dust2", "de_mirage", "de_inferno", "de_nuke", "de_overpass", "de_ancient", "de_anubis"],
            "Wingman": ["de_inferno", "de_overpass", "de_vertigo", "de_nuke"],
            "Deathmatch": ["de_dust2", "de_mirage", "de_inferno", "de_nuke", "cs_office"],
            "Custom": [],
        }

        self._pool_var = ctk.StringVar(value="Active Duty")
        for pool in self._map_pools:
            ctk.CTkRadioButton(
                left, text=pool, variable=self._pool_var, value=pool,
                text_color=t["text"], fg_color=t["primary"],
                font=ctk.CTkFont("Segoe UI", 11),
                command=self._refresh_map_list
            ).pack(padx=12, pady=4, anchor="w")

        # Right: map list
        right = ctk.CTkFrame(row, fg_color=t["card_bg"], corner_radius=8)
        right.pack(side="left", fill="both", expand=True)
        _label(right, "Mapy v poolu", 12, bold=True, color=t["text_dim"]).pack(padx=10, pady=8)

        self.map_listbox = tk.Listbox(
            right, bg=t["secondary"], fg=t["text"], selectbackground=t["primary"],
            font=("Courier New", 11), relief="flat", borderwidth=0, height=10
        )
        self.map_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        add_row = ctk.CTkFrame(right, fg_color="transparent")
        add_row.pack(fill="x", padx=10, pady=4)

        self.map_entry = ctk.CTkEntry(add_row, placeholder_text="de_mapname nebo workshop/ID",
                                      fg_color=t["secondary"], text_color=t["text"],
                                      font=ctk.CTkFont("Courier New", 11))
        self.map_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(add_row, text="+ Přidat", width=90, height=32,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._add_map).pack(side="left", padx=(0, 4))
        ctk.CTkButton(add_row, text="- Odebrat", width=90, height=32,
                      fg_color="#8b2020", hover_color="#6b1818",
                      command=self._remove_map).pack(side="left")

        _btn(right, "💾 Generovat mapgroup", self._save_mapgroup, t).pack(
            padx=10, pady=8, fill="x")

        self._refresh_map_list()

    def _refresh_map_list(self):
        pool = self._pool_var.get()
        self.map_listbox.delete(0, "end")
        for m in self._map_pools.get(pool, []):
            self.map_listbox.insert("end", m)

    def _add_map(self):
        m = self.map_entry.get().strip()
        if m:
            pool = self._pool_var.get()
            self._map_pools[pool].append(m)
            self._refresh_map_list()
            self.map_entry.delete(0, "end")

    def _remove_map(self):
        sel = self.map_listbox.curselection()
        if sel:
            pool = self._pool_var.get()
            idx = sel[0]
            self._map_pools[pool].pop(idx)
            self._refresh_map_list()

    def _save_mapgroup(self):
        pool = self._pool_var.get()
        maps = self._map_pools[pool]
        if not maps:
            messagebox.showerror("Chyba", "Pool je prázdný!")
            return
        safe = pool.lower().replace(" ", "_")
        path = filedialog.asksaveasfilename(
            title=f"Uložit mapgroup_{safe}.txt",
            defaultextension=".txt",
            initialfile=f"cs2_mapgroup_{safe}.txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"// CS2 Map Group: {pool}\n// Generated by ZeddiHub Tools\n\n")
            f.write(f'"cs2_mapgroup_{safe}"\n{{\n')
            for m in maps:
                f.write(f'\t"{m}"\t""\n')
            f.write("}\n")
        messagebox.showinfo("Uloženo", f"Map group uložen:\n{path}")

    def _build_rcon(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "CS2 – RCON Klient", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Připojení k CS2 serveru přes Source RCON protokol.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 12))

        cfg_row = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        cfg_row.pack(fill="x", pady=4)

        self._rcon_host = ctk.StringVar(value="127.0.0.1")
        self._rcon_port = ctk.StringVar(value="27015")
        self._rcon_pw = ctk.StringVar()

        for i, (lbl, var, mask) in enumerate([
            ("IP adresa", self._rcon_host, False),
            ("Port",      self._rcon_port, False),
            ("RCON heslo", self._rcon_pw, True),
        ]):
            ctk.CTkLabel(cfg_row, text=lbl, font=ctk.CTkFont("Segoe UI", 11),
                         text_color=t["text_dim"], width=110, anchor="w"
                         ).grid(row=i, column=0, padx=(12, 4), pady=4, sticky="w")
            ctk.CTkEntry(cfg_row, textvariable=var, width=200,
                         fg_color=t["secondary"], text_color=t["text"],
                         font=ctk.CTkFont("Courier New", 11),
                         show="*" if mask else ""
                         ).grid(row=i, column=1, padx=4, pady=4, sticky="w")

        _btn(cfg_row, "🔌 Připojit", self._rcon_connect, t, width=130
             ).grid(row=0, column=2, rowspan=3, padx=12)

        # Console output
        _label(main, "Výstup konzole:", 11, bold=True, color=t["text_dim"]).pack(
            anchor="w", pady=(12, 2))

        self.rcon_output = ctk.CTkTextbox(
            main, height=200, font=ctk.CTkFont("Courier New", 11),
            fg_color=t["secondary"], text_color="#44ff44", state="disabled"
        )
        self.rcon_output.pack(fill="both", expand=True, pady=4)

        cmd_row = ctk.CTkFrame(main, fg_color="transparent")
        cmd_row.pack(fill="x", pady=4)

        self.rcon_cmd_entry = ctk.CTkEntry(
            cmd_row, placeholder_text="Zadejte RCON příkaz...",
            fg_color=t["secondary"], text_color=t["text"],
            font=ctk.CTkFont("Courier New", 12)
        )
        self.rcon_cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.rcon_cmd_entry.bind("<Return>", lambda _: self._rcon_send())

        _btn(cmd_row, "Odeslat", self._rcon_send, t, width=100).pack(side="left")

        self._rcon_socket = None

    def _rcon_log(self, msg: str):
        self.rcon_output.configure(state="normal")
        self.rcon_output.insert("end", msg + "\n")
        self.rcon_output.see("end")
        self.rcon_output.configure(state="disabled")

    def _rcon_connect(self):
        import socket, struct, threading

        host = self._rcon_host.get().strip()
        try:
            port = int(self._rcon_port.get().strip())
        except ValueError:
            self._rcon_log("! Neplatný port")
            return
        pw = self._rcon_pw.get().strip()
        if not pw:
            self._rcon_log("! RCON heslo je prázdné")
            return

        def connect():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((host, port))

                def pkt(req_id, ptype, body):
                    enc = body.encode() + b'\x00\x00'
                    return struct.pack('<iii', 4+4+len(enc), req_id, ptype) + enc

                def read_resp(sock):
                    d = sock.recv(4)
                    if len(d) < 4: return None, None
                    size = struct.unpack('<i', d)[0]
                    rest = b''
                    while len(rest) < size:
                        c = sock.recv(size - len(rest))
                        if not c: break
                        rest += c
                    if len(rest) < 8: return None, None
                    rid, rtype = struct.unpack('<ii', rest[:8])
                    return rid, rest[8:].rstrip(b'\x00').decode('utf-8', errors='replace')

                s.sendall(pkt(1, 3, pw))
                r1, _ = read_resp(s)
                r2, _ = read_resp(s)
                if r2 == -1:
                    self.after(0, self._rcon_log, "✗ Autentizace selhala! Špatné heslo.")
                    s.close()
                    return
                self._rcon_socket = s
                self.after(0, self._rcon_log, f"✓ Připojeno k {host}:{port}")
            except Exception as e:
                self.after(0, self._rcon_log, f"✗ Chyba připojení: {e}")

        threading.Thread(target=connect, daemon=True).start()

    def _rcon_send(self):
        import struct, threading
        cmd = self.rcon_cmd_entry.get().strip()
        if not cmd or not self._rcon_socket:
            if not self._rcon_socket:
                self._rcon_log("! Nejste připojeni. Klikněte na Připojit.")
            return
        self.rcon_cmd_entry.delete(0, "end")

        def send():
            try:
                enc = cmd.encode() + b'\x00\x00'
                pkt = struct.pack('<iii', 4+4+len(enc), 2, 2) + enc
                self._rcon_socket.sendall(pkt)
                import time; time.sleep(0.3)
                d = self._rcon_socket.recv(4)
                if len(d) < 4: return
                size = struct.unpack('<i', d)[0]
                rest = b''
                while len(rest) < size:
                    c = self._rcon_socket.recv(size - len(rest))
                    if not c: break
                    rest += c
                body = rest[8:].rstrip(b'\x00').decode('utf-8', errors='replace')
                self.after(0, self._rcon_log, f"> {cmd}")
                if body:
                    for line in body.splitlines():
                        self.after(0, self._rcon_log, f"  {line}")
            except Exception as e:
                self.after(0, self._rcon_log, f"! Chyba: {e}")
                self._rcon_socket = None

        threading.Thread(target=send, daemon=True).start()
