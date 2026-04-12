"""
ZeddiHub Tools - CS:GO Player & Server Tools GUI panels.
"""

import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .. import icons


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#ffffff", **kw)


def _btn(parent, text, cmd, theme, width=180, height=36, **kw):
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=theme["primary"], hover_color=theme["primary_hover"],
                         text_color=theme["button_fg"],
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         width=width, height=height, **kw)


def _section(parent, title, theme):
    f = ctk.CTkFrame(parent, fg_color=theme["card_bg"], corner_radius=8)
    f.pack(fill="x", padx=0, pady=6)
    _label(f, title, 13, bold=True, color=theme["primary"]).pack(padx=14, pady=(10, 6), anchor="w")
    return f


def _entry_row(parent, label_text, default_val, theme, row, hint=""):
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    ctk.CTkEntry(parent, textvariable=var, width=160,
                 fg_color=theme["secondary"], text_color=theme["text"],
                 font=ctk.CTkFont("Courier New", 11)
                 ).grid(row=row, column=1, padx=4, pady=3, sticky="w")
    if hint:
        ctk.CTkLabel(parent, text=hint, font=ctk.CTkFont("Segoe UI", 9),
                     text_color=theme["text_dim"]
                     ).grid(row=row, column=2, padx=4, pady=3, sticky="w")
    return var


def _bool_row(parent, label_text, default_val, theme, row, hint=""):
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    ctk.CTkOptionMenu(parent, variable=var, values=["0", "1"],
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


def _dropdown_row(parent, label_text, options, default_val, theme, row, hint=""):
    ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont("Segoe UI", 11),
                 text_color=theme["text_dim"], anchor="w", width=240
                 ).grid(row=row, column=0, padx=(12, 4), pady=3, sticky="w")
    var = ctk.StringVar(value=str(default_val))
    ctk.CTkOptionMenu(parent, variable=var, values=[str(o) for o in options],
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
        try: var.set(_clamp(float(var.get()) - step))
        except ValueError: var.set(str(default_val))

    def _inc():
        try: var.set(_clamp(float(var.get()) + step))
        except ValueError: var.set(str(default_val))

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


class CSGOPlayerPanel(ctk.CTkFrame):
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

    def _build_crosshair(self, tab):
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

        _label(scroll, "CS:GO – Crosshair Generátor", 16, bold=True, color=t["primary"]
               ).pack(padx=12, pady=(12, 8), anchor="w")

        sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        sec.pack(fill="x", padx=8, pady=4)
        sec.grid_columnconfigure(1, weight=1)

        self._xhair_vars = {}
        row = 0
        self._xhair_vars["cl_crosshairstyle"] = _dropdown_row(
            sec, "Styl", ["0","1","2","3","4","5"], "4", t, row,
            "0=Default,1=Static,2=Classic,3=CS:GO,4=Small,5=Tiny"); row += 1
        self._xhair_vars["cl_crosshaircolor"] = _dropdown_row(
            sec, "Barva", ["0","1","2","3","4","5"], "1", t, row,
            "0=Červená,1=Zelená,2=Žlutá,3=Modrá,4=Cyan,5=Custom"); row += 1
        self._xhair_vars["cl_crosshairsize"] = _stepper_row(
            sec, "Velikost", "2", 0, 10, 0.5, t, row, "0–10"); row += 1
        self._xhair_vars["cl_crosshairthickness"] = _stepper_row(
            sec, "Tloušťka", "0.5", 0, 3, 0.5, t, row, "0–3"); row += 1
        self._xhair_vars["cl_crosshairgap"] = _stepper_row(
            sec, "Mezera", "-1", -10, 10, 1, t, row, "záporná = menší"); row += 1
        self._xhair_vars["cl_crosshair_outlinethickness"] = _stepper_row(
            sec, "Tl. obrysu", "1", 0, 3, 0.5, t, row); row += 1
        self._xhair_vars["cl_crosshairalpha"] = _stepper_row(
            sec, "Průhlednost", "255", 0, 255, 10, t, row, "0–255"); row += 1
        self._xhair_vars["cl_crosshairdot"] = _bool_row(
            sec, "Tečka", "0", t, row); row += 1
        self._xhair_vars["cl_crosshair_drawoutline"] = _bool_row(
            sec, "Obrys", "1", t, row); row += 1

        _btn(scroll, "💾 Uložit crosshair.cfg", self._save_crosshair, t).pack(padx=8, pady=10, fill="x")
        ctk.CTkButton(scroll, text=" Kopírovat share kód",
                      image=icons.icon("copy", 14, "#cccccc"), compound="left",
                      command=self._copy_code, fg_color=t["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 11), height=32
                      ).pack(padx=8, pady=(0, 10), fill="x")

        _label(right, "Náhled", 12, bold=True, color=t["text_dim"]).pack(pady=(14, 6))
        self.xhair_canvas = tk.Canvas(right, width=220, height=160,
                                      bg=t["card_bg"], highlightthickness=0)
        self.xhair_canvas.pack(padx=10)
        _btn(right, "↻ Aktualizovat", self._update_preview, t, width=140, height=30).pack(pady=8)

        for var in self._xhair_vars.values():
            var.trace_add("write", lambda *_: self.after(200, self._update_preview))
        self._update_preview()

    def _update_preview(self):
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
            outline = int(float(self._xhair_vars["cl_crosshair_drawoutline"].get())) == 1

            colors_map = ["#dd3333", "#33dd33", "#dddd33", "#3333ff", "#33dddd", "#ffffff"]
            color = colors_map[color_idx] if 0 <= color_idx < len(colors_map) else "#c49b3c"
            scale = 4
            half_t = thickness // 2
            g = max(0, gap * scale)
            s = max(2, size * scale)

            if outline:
                for rr in [(cx-half_t-2, cy-g-s-2, cx+half_t+3, cy-g+2),
                           (cx-half_t-2, cy+g-2, cx+half_t+3, cy+g+s+2),
                           (cx-g-s*2-2, cy-half_t-2, cx-g+2, cy+half_t+3),
                           (cx+g-2, cy-half_t-2, cx+g+s*2+2, cy+half_t+3)]:
                    c.create_rectangle(*rr, fill="#000000", outline="")

            c.create_rectangle(cx-half_t, cy-g-s, cx+half_t+1, cy-g, fill=color, outline="")
            c.create_rectangle(cx-half_t, cy+g, cx+half_t+1, cy+g+s, fill=color, outline="")
            c.create_rectangle(cx-g-s*2, cy-half_t, cx-g, cy+half_t+1, fill=color, outline="")
            c.create_rectangle(cx+g, cy-half_t, cx+g+s*2, cy+half_t+1, fill=color, outline="")
            if dot:
                c.create_oval(cx-2, cy-2, cx+3, cy+3, fill=color, outline="")
        except Exception:
            pass

    def _save_crosshair(self):
        path = filedialog.asksaveasfilename(title="Uložit crosshair.cfg",
                                            defaultextension=".cfg",
                                            initialfile="csgo_crosshair.cfg",
                                            filetypes=[("Config", "*.cfg"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS:GO Crosshair - Generated by ZeddiHub Tools\n\n")
            for k, var in self._xhair_vars.items():
                f.write(f'{k} "{var.get()}"\n')
        messagebox.showinfo("Uloženo", f"Crosshair cfg uložen:\n{path}")

    def _copy_code(self):
        code = "; ".join(f"{k} {v.get()}" for k, v in self._xhair_vars.items())
        self.clipboard_clear()
        self.clipboard_append(code)
        messagebox.showinfo("Zkopírováno", "Share kód zkopírován do schránky!")

    def _build_viewmodel(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS:GO – Viewmodel Generátor", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 8), anchor="w")

        sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        sec.pack(fill="x", padx=8, pady=4)
        sec.grid_columnconfigure(1, weight=1)

        self._vm_vars = {}
        vrow = 0
        self._vm_vars["viewmodel_fov"] = _stepper_row(
            sec, "FOV", "60", 54, 68, 1, t, vrow, "54–68"); vrow += 1
        self._vm_vars["viewmodel_offset_x"] = _stepper_row(
            sec, "Offset X", "2.5", -2.5, 2.5, 0.5, t, vrow); vrow += 1
        self._vm_vars["viewmodel_offset_y"] = _stepper_row(
            sec, "Offset Y", "0", -2.5, 2.5, 0.5, t, vrow); vrow += 1
        self._vm_vars["viewmodel_offset_z"] = _stepper_row(
            sec, "Offset Z", "-1.5", -2.5, 2.5, 0.5, t, vrow); vrow += 1
        self._vm_vars["viewmodel_presetpos"] = _dropdown_row(
            sec, "Preset", ["1","2","3"], "3", t, vrow,
            "1=Desktop / 2=Couch / 3=Classic"); vrow += 1
        self._vm_vars["cl_bob_lower_amt"] = _stepper_row(
            sec, "Bob Lower", "5", 5, 30, 1, t, vrow); vrow += 1
        self._vm_vars["cl_bobamt_lat"] = _stepper_row(
            sec, "Bob Lat", "0.33", 0.0, 2.0, 0.1, t, vrow); vrow += 1
        self._vm_vars["cl_bobamt_vert"] = _stepper_row(
            sec, "Bob Vert", "0.14", 0.0, 2.0, 0.1, t, vrow); vrow += 1

        _btn(scroll, "💾 Uložit viewmodel.cfg", self._save_viewmodel, t).pack(padx=8, pady=10, fill="x")

    def _save_viewmodel(self):
        path = filedialog.asksaveasfilename(title="Uložit viewmodel.cfg",
                                            defaultextension=".cfg",
                                            initialfile="csgo_viewmodel.cfg",
                                            filetypes=[("Config", "*.cfg"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS:GO Viewmodel - Generated by ZeddiHub Tools\n\n")
            for k, var in self._vm_vars.items():
                f.write(f'{k} "{var.get()}"\n')
        messagebox.showinfo("Uloženo", f"Viewmodel cfg uložen:\n{path}")

    def _build_autoexec(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS:GO – Autoexec Config", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 8), anchor="w")

        defs = {
            "rate": ("Rate", "786432"),
            "cl_cmdrate": ("Cmdrate", "128"),
            "cl_updaterate": ("Updaterate", "128"),
            "cl_interp_ratio": ("Interp ratio", "1"),
            "cl_interp": ("Interp", "0.015625"),
            "fps_max": ("FPS max", "300"),
            "sensitivity": ("Citlivost", "1.0"),
            "zoom_sensitivity_ratio_mouse": ("Zoom cit.", "1.0"),
            "con_enable": ("Konzole", "1"),
            "snd_musicvolume": ("Hudba", "0"),
            "volume": ("Hlasitost", "0.5"),
            "gameinstructor_enable": ("Instructor", "0"),
            "cl_autohelp": ("Auto help", "0"),
            "mm_dedicated_search_maxping": ("Max ping", "50"),
        }

        outer_ae = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        outer_ae.pack(fill="x", padx=0, pady=6)
        _label(outer_ae, "Herní nastavení", 13, bold=True, color=t["primary"]).pack(
            padx=14, pady=(10, 6), anchor="w")
        sec = ctk.CTkFrame(outer_ae, fg_color="transparent")
        sec.pack(fill="x", padx=0, pady=(0, 6))
        sec.grid_columnconfigure(1, weight=1)
        self._ae_vars = {}
        for i, (k, (lbl, default)) in enumerate(defs.items()):
            self._ae_vars[k] = _entry_row(sec, f"{lbl}", default, t, i)

        _label(scroll, "Vlastní příkazy:", 12, bold=True, color=t["text"]).pack(padx=4, pady=(8, 2), anchor="w")
        self.ae_custom = ctk.CTkTextbox(scroll, height=80, fg_color=t["secondary"],
                                        text_color=t["text"], font=ctk.CTkFont("Courier New", 11))
        self.ae_custom.pack(fill="x", padx=4, pady=4)
        self.ae_custom.insert("end", "// Vlastní příkazy\n")

        _btn(scroll, "💾 Uložit autoexec.cfg", self._save_autoexec, t).pack(padx=4, pady=8, fill="x")

    def _save_autoexec(self):
        path = filedialog.asksaveasfilename(title="Uložit autoexec.cfg",
                                            defaultextension=".cfg",
                                            initialfile="csgo_autoexec.cfg",
                                            filetypes=[("Config", "*.cfg"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS:GO Autoexec - Generated by ZeddiHub Tools\n\n")
            for k, var in self._ae_vars.items():
                f.write(f'{k} "{var.get()}"\n')
            custom = self.ae_custom.get("1.0", "end").strip()
            if custom and not custom.startswith("//"):
                f.write("\n" + custom + "\n")
            f.write('\necho "ZeddiHub autoexec loaded!"\n')
        messagebox.showinfo("Uloženo", f"Autoexec uložen:\n{path}")

    def _build_practice(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS:GO – Practice Config", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 8), anchor="w")

        defs = {
            "sv_cheats":           ("SV Cheats",         "1"),
            "sv_infinite_ammo":    ("Nekonečná munice",  "1"),
            "mp_buy_anywhere":     ("Kupovat kdekoliv",  "1"),
            "mp_buytime":          ("Buy time",          "99999"),
            "mp_freezetime":       ("Freeze time",       "0"),
            "mp_roundtime":        ("Round time",        "60"),
            "mp_maxmoney":         ("Max peníze",        "65535"),
            "mp_startmoney":       ("Start peníze",      "65535"),
            "sv_grenade_trajectory_prac_pipreview": ("Nade preview", "1"),
            "sv_grenade_trajectory_prac_trailtime": ("Nade trail",   "4"),
            "cl_grenadepreview":   ("Grenade preview",   "1"),
        }
        outer_pr = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        outer_pr.pack(fill="x", padx=0, pady=6)
        _label(outer_pr, "Nastavení", 13, bold=True, color=t["primary"]).pack(
            padx=14, pady=(10, 6), anchor="w")
        sec = ctk.CTkFrame(outer_pr, fg_color="transparent")
        sec.pack(fill="x", padx=0, pady=(0, 6))
        sec.grid_columnconfigure(1, weight=1)
        self._prac_vars = {}
        for i, (k, (lbl, default)) in enumerate(defs.items()):
            self._prac_vars[k] = _entry_row(sec, lbl, default, t, i)

        _btn(scroll, "💾 Uložit practice.cfg", self._save_practice, t).pack(padx=4, pady=10, fill="x")

    def _save_practice(self):
        path = filedialog.asksaveasfilename(title="Uložit practice.cfg",
                                            defaultextension=".cfg",
                                            initialfile="csgo_practice.cfg",
                                            filetypes=[("Config", "*.cfg"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS:GO Practice - Generated by ZeddiHub Tools\n")
            f.write("// exec csgo_practice\n\n")
            f.write("mp_warmup_end\nbot_kick\n\n")
            for k, var in self._prac_vars.items():
                f.write(f"{k} {var.get()}\n")
            f.write("\nmp_restartgame 1\necho \"Practice mode activated!\"\n")
        messagebox.showinfo("Uloženo", f"Practice cfg uložen:\n{path}")

    def _build_buybinds(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS:GO – Buy Binds Generátor", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 8), anchor="w")

        binds_default = {
            "kp_ins":        ("AK-47 / M4A4",           "buy ak47; buy m4a1;"),
            "kp_end":        ("AWP",                     "buy awp;"),
            "kp_downarrow":  ("Deagle",                  "buy deagle;"),
            "kp_pgdn":       ("Armor + Defuse",          "buy vesthelm; buy defuser;"),
            "kp_leftarrow":  ("Smoke + Flash + Molotov", "buy smokegrenade; buy flashbang; buy molotov; buy incgrenade;"),
            "kp_5":          ("HE Grenade",              "buy hegrenade;"),
            "kp_rightarrow": ("Decoy",                   "buy decoy;"),
            "kp_home":       ("MP9 / MAC-10",            "buy mp9; buy mac10;"),
            "kp_uparrow":    ("Famas / Galil",           "buy famas; buy galilar;"),
            "kp_pgup":       ("Full Buy",                "buy ak47; buy m4a1; buy vesthelm; buy defuser; buy smokegrenade; buy flashbang; buy molotov; buy hegrenade;"),
        }

        self._bind_vars = {}
        outer_bb = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
        outer_bb.pack(fill="x", padx=0, pady=6)
        _label(outer_bb, "Klávesy a příkazy", 13, bold=True, color=t["primary"]).pack(
            padx=14, pady=(10, 6), anchor="w")
        sec = ctk.CTkFrame(outer_bb, fg_color="transparent")
        sec.pack(fill="x", padx=0, pady=(0, 6))
        sec.grid_columnconfigure(2, weight=1)

        for i, (key, (label, cmd)) in enumerate(binds_default.items()):
            ctk.CTkLabel(sec, text=f"[{key}]", font=ctk.CTkFont("Courier New", 11),
                         text_color=t["accent"], width=110, anchor="w"
                         ).grid(row=i, column=0, padx=(12, 4), pady=3, sticky="w")
            ctk.CTkLabel(sec, text=label, font=ctk.CTkFont("Segoe UI", 10),
                         text_color=t["text_dim"], width=150, anchor="w"
                         ).grid(row=i, column=1, padx=4, pady=3, sticky="w")
            var = ctk.StringVar(value=cmd)
            ctk.CTkEntry(sec, textvariable=var, width=280,
                         fg_color=t["secondary"], text_color=t["text"],
                         font=ctk.CTkFont("Courier New", 10)
                         ).grid(row=i, column=2, padx=4, pady=3, sticky="ew")
            self._bind_vars[key] = var

        _btn(scroll, "💾 Uložit buybinds.cfg", self._save_buybinds, t).pack(padx=4, pady=10, fill="x")

    def _save_buybinds(self):
        path = filedialog.asksaveasfilename(title="Uložit buybinds.cfg",
                                            defaultextension=".cfg",
                                            initialfile="csgo_buybinds.cfg",
                                            filetypes=[("Config", "*.cfg"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS:GO Buy Binds - Generated by ZeddiHub Tools\n\n")
            for key, var in self._bind_vars.items():
                f.write(f'bind "{key}" "{var.get()}"\n')
            f.write('\necho "ZeddiHub buy binds loaded!"\n')
        messagebox.showinfo("Uloženo", f"Buy binds uloženy:\n{path}")


class CSGOServerPanel(ctk.CTkFrame):
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
        tab.add("🗄 DB Editor")
        tab.add("RCON Klient")

        self._build_servercfg(tab.tab("Server.cfg"))
        self._build_db_editor(tab.tab("🗄 DB Editor"))
        self._build_rcon(tab.tab("RCON Klient"))

    def _build_servercfg(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "CS:GO – Server.cfg Generátor", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 8), anchor="w")

        self._srv_vars = {}

        def _s(title):
            outer = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            outer.pack(fill="x", padx=0, pady=6)
            _label(outer, title, 13, bold=True, color=t["primary"]).pack(
                padx=14, pady=(10, 6), anchor="w")
            inner = ctk.CTkFrame(outer, fg_color="transparent")
            inner.pack(fill="x", padx=0, pady=(0, 6))
            inner.grid_columnconfigure(1, weight=1)
            return inner

        s = _s("Základní")
        self._srv_vars["hostname"]      = _entry_row(s, "Název serveru", "ZeddiHub CS:GO Server", t, 0)
        self._srv_vars["sv_password"]   = _entry_row(s, "Heslo serveru", "", t, 1)
        self._srv_vars["rcon_password"] = _entry_row(s, "RCON heslo", "changeme", t, 2)
        self._srv_vars["sv_cheats"]     = _bool_row(s, "SV Cheats", "0", t, 3)
        self._srv_vars["sv_lan"]        = _bool_row(s, "LAN only", "0", t, 4)

        s = _s("Gamemode")
        self._srv_vars["game_type"] = _dropdown_row(s, "Game type", ["0","1","2"], "0", t, 0, "0=Classic,1=GunGame,2=Training")
        self._srv_vars["game_mode"] = _dropdown_row(s, "Game mode", ["0","1","2"], "1", t, 1, "0=Casual,1=Comp,2=Wingman")

        s = _s("Network")
        self._srv_vars["sv_maxrate"] = _stepper_row(s, "Max rate", "786432", 0, 786432, 128000, t, 0)

        s = _s("Gameplay")
        self._srv_vars["mp_autoteambalance"] = _bool_row(s, "Auto balance",    "1", t, 0)
        self._srv_vars["mp_limitteams"]      = _bool_row(s, "Limit teams",     "1", t, 1)
        self._srv_vars["mp_friendlyfire"]    = _bool_row(s, "Friendly fire",   "0", t, 2)
        self._srv_vars["mp_maxrounds"]       = _dropdown_row(s, "Max rounds", ["12","16","24","30"], "30", t, 3)
        self._srv_vars["mp_roundtime"]       = _stepper_row(s, "Round time (min)", "1.92", 0.5, 10, 0.5, t, 4)
        self._srv_vars["mp_freezetime"]      = _stepper_row(s, "Freeze time (s)",  "15",   0,   30,  1,  t, 5)
        self._srv_vars["mp_buytime"]         = _stepper_row(s, "Buy time (s)",     "20",   0,   90,  5,  t, 6)

        s = _s("Komunikace")
        self._srv_vars["sv_alltalk"]  = _bool_row(s, "All talk",  "0", t, 0)
        self._srv_vars["sv_deadtalk"] = _bool_row(s, "Dead talk", "1", t, 1)

        s = _s("GOTV")
        self._srv_vars["tv_enable"] = _bool_row(s, "TV enable", "1", t, 0)
        self._srv_vars["tv_delay"]  = _stepper_row(s, "TV delay (s)", "30", 0, 120, 10, t, 1)

        _btn(scroll, "💾 Uložit server.cfg", self._save_servercfg, t).pack(padx=4, pady=10, fill="x")

    def _save_servercfg(self):
        path = filedialog.asksaveasfilename(title="Uložit server.cfg",
                                            defaultextension=".cfg",
                                            initialfile="server.cfg",
                                            filetypes=[("Config", "*.cfg"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// CS:GO Server Config - Generated by ZeddiHub Tools\n\n")
            for k, var in self._srv_vars.items():
                v = var.get()
                if k in ("hostname", "sv_password", "rcon_password") and v:
                    f.write(f'{k} "{v}"\n')
                elif v:
                    f.write(f'{k} {v}\n')
            f.write('\necho "[ZeddiHub] Server config loaded!"\n')
        messagebox.showinfo("Uloženo", f"server.cfg uložen:\n{path}")

    def _build_db_editor(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "CS:GO – Database / Admini Editor", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Správa adminů, skupin a sourcebans databáze.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 12))

        info = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        info.pack(fill="x", pady=4)

        ctk.CTkLabel(info, text="📁  Zvolte složku s CS:GO databázovými soubory (.ini, .cfg)",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=t["text"]
                     ).pack(padx=16, pady=(12, 4), anchor="w")

        row = ctk.CTkFrame(info, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)

        self.db_path_var = ctk.StringVar(value="Nezvolena složka...")
        ctk.CTkLabel(row, textvariable=self.db_path_var, font=ctk.CTkFont("Segoe UI", 10),
                     text_color=t["text_dim"]).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="📂 Zvolit složku", height=32, width=140,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._pick_db_folder).pack(side="left", padx=(8, 0))

        self.db_file_list = ctk.CTkScrollableFrame(main, fg_color=t["card_bg"], corner_radius=8, height=180)
        self.db_file_list.pack(fill="x", pady=8)
        _label(self.db_file_list, "Soubory se zobrazí po výběru složky.",
               11, color=t["text_dim"]).pack(padx=12, pady=8, anchor="w")

    def _pick_db_folder(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Zvolit složku s DB soubory")
        if not path:
            return
        self.db_path_var.set(path)
        for w in self.db_file_list.winfo_children():
            w.destroy()
        t = self.theme
        files = [f for f in os.listdir(path) if f.endswith(('.ini', '.cfg', '.db', '.sql'))]
        if not files:
            _label(self.db_file_list, "Žádné databázové soubory nenalezeny.", 11, color=t["text_dim"]
                   ).pack(padx=12, pady=8, anchor="w")
            return
        for fname in files:
            row = ctk.CTkFrame(self.db_file_list, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(row, text=fname, font=ctk.CTkFont("Courier New", 11),
                         text_color=t["text"], anchor="w").pack(side="left")

    def _build_rcon(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "CS:GO – RCON Klient", 16, bold=True, color=t["primary"]).pack(anchor="w")

        cfg_row = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        cfg_row.pack(fill="x", pady=8)

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
        _btn(cfg_row, "🔌 Připojit", self._rcon_connect, t, width=120
             ).grid(row=0, column=2, rowspan=3, padx=12)

        self.rcon_output = ctk.CTkTextbox(main, height=220,
                                          font=ctk.CTkFont("Courier New", 11),
                                          fg_color=t["secondary"],
                                          text_color="#44ff44", state="disabled")
        self.rcon_output.pack(fill="both", expand=True, pady=8)

        cmd_row = ctk.CTkFrame(main, fg_color="transparent")
        cmd_row.pack(fill="x")

        self.rcon_cmd = ctk.CTkEntry(cmd_row, placeholder_text="RCON příkaz...",
                                     fg_color=t["secondary"], text_color=t["text"],
                                     font=ctk.CTkFont("Courier New", 12))
        self.rcon_cmd.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.rcon_cmd.bind("<Return>", lambda _: self._rcon_send())
        _btn(cmd_row, "Odeslat", self._rcon_send, t, width=100).pack(side="left")

        self._rcon_socket = None

    def _rcon_log(self, msg):
        self.rcon_output.configure(state="normal")
        self.rcon_output.insert("end", msg + "\n")
        self.rcon_output.see("end")
        self.rcon_output.configure(state="disabled")

    def _rcon_connect(self):
        import socket, struct, threading
        host = self._rcon_host.get().strip()
        try:
            port = int(self._rcon_port.get())
        except ValueError:
            self._rcon_log("! Neplatný port"); return
        pw = self._rcon_pw.get().strip()
        if not pw:
            self._rcon_log("! Prázdné heslo"); return

        def connect():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((host, port))
                enc = pw.encode() + b'\x00\x00'
                s.sendall(struct.pack('<iii', 4+4+len(enc), 1, 3) + enc)
                d = s.recv(4)
                size = struct.unpack('<i', d)[0]
                rest = s.recv(size)
                r2, _ = struct.unpack('<ii', rest[:8])
                if r2 == -1:
                    self.after(0, self._rcon_log, "✗ Špatné heslo"); s.close(); return
                self._rcon_socket = s
                self.after(0, self._rcon_log, f"✓ Připojeno k {host}:{port}")
            except Exception as e:
                self.after(0, self._rcon_log, f"✗ Chyba: {e}")

        threading.Thread(target=connect, daemon=True).start()

    def _rcon_send(self):
        import struct, threading
        cmd = self.rcon_cmd.get().strip()
        if not cmd or not self._rcon_socket:
            if not self._rcon_socket:
                self._rcon_log("! Nejste připojeni")
            return
        self.rcon_cmd.delete(0, "end")

        def send():
            try:
                import time
                enc = cmd.encode() + b'\x00\x00'
                self._rcon_socket.sendall(struct.pack('<iii', 4+4+len(enc), 2, 2) + enc)
                time.sleep(0.3)
                d = self._rcon_socket.recv(4096)
                body = d[12:].rstrip(b'\x00').decode('utf-8', errors='replace')
                self.after(0, self._rcon_log, f"> {cmd}")
                for line in body.splitlines():
                    self.after(0, self._rcon_log, f"  {line}")
            except Exception as e:
                self.after(0, self._rcon_log, f"! Chyba: {e}")

        threading.Thread(target=send, daemon=True).start()
