"""
ZeddiHub Tools - Rust Player & Server Tools GUI panels.
"""

import os
import re
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
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
                 text_color=theme["text_dim"], anchor="w", width=220
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


# ─────────────────────────────────────────────
# RUST PLAYER TOOLS
# ─────────────────────────────────────────────

class RustPlayerPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        t = self.theme
        tab = ctk.CTkTabview(self, fg_color=t["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("⚙ Herní nastavení")
        tab.add("📦 Plugin Info")
        tab.add("🔍 Analýza pluginů")

        self._build_settings(tab.tab("⚙ Herní nastavení"))
        self._build_plugin_info(tab.tab("📦 Plugin Info"))
        self._build_plugin_analyzer(tab.tab("🔍 Analýza pluginů"))

    def _build_settings(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "Rust – Herní Nastavení & CFG", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 4), anchor="w")
        _label(scroll, "Vygenerujte client.cfg soubor pro optimální herní nastavení.",
               11, color=t["text_dim"]).pack(padx=4, pady=(0, 8), anchor="w")

        categories = {
            "Grafika": {
                "graphics.quality": ("Kvalita grafiky", "3", "0=nejnižší, 5=nejvyšší"),
                "grass.on":         ("Tráva",           "true", "true/false"),
                "terrain.quality":  ("Terén",           "100", "0-200"),
                "water.quality":    ("Voda",            "10", "0-100"),
                "shadowmode":       ("Stíny",           "1", "0=žádné, 1=nízké, 2=vysoké"),
                "lodrange":         ("LOD vzdálenost",  "200", "100-2000"),
            },
            "Zvuk": {
                "audio.master":  ("Master hlasitost", "1.0", "0.0-1.0"),
                "audio.music":   ("Hudba",            "0.0", ""),
                "audio.game":    ("Hra",              "1.0", ""),
                "audio.voice":   ("Hlas",             "1.0", ""),
            },
            "Výkon": {
                "fps.limit":     ("FPS limit",        "0", "0=neomezeno"),
                "pool.mode":     ("Pool mode",        "0", ""),
            },
        }

        self._cfg_vars = {}
        for cat_name, fields in categories.items():
            outer = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            outer.pack(fill="x", padx=0, pady=6)
            _label(outer, cat_name, 13, bold=True, color=t["primary"]).pack(
                padx=14, pady=(10, 6), anchor="w")
            sec = ctk.CTkFrame(outer, fg_color="transparent")
            sec.pack(fill="x", padx=0, pady=(0, 6))
            sec.grid_columnconfigure(1, weight=1)
            for i, (k, vals) in enumerate(fields.items()):
                lbl, default, hint = vals
                self._cfg_vars[k] = _entry_row(sec, lbl, default, t, i, hint)

        _btn(scroll, "💾 Uložit client.cfg", self._save_client_cfg, t).pack(padx=4, pady=10, fill="x")

    def _save_client_cfg(self):
        path = filedialog.asksaveasfilename(
            title="Uložit client.cfg", defaultextension=".cfg",
            initialfile="rust_client.cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// Rust Client Config - Generated by ZeddiHub Tools\n\n")
            for k, var in self._cfg_vars.items():
                f.write(f"{k} {var.get()}\n")
        messagebox.showinfo("Uloženo", f"client.cfg uložen:\n{path}")

    def _build_plugin_info(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "Rust – Informace o pluginech", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Zvolte .cs plugin soubor a zobrazte jeho detaily.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 10))

        row = ctk.CTkFrame(main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        self.plugin_path_var = ctk.StringVar(value="Nezvolený soubor...")
        ctk.CTkLabel(row, textvariable=self.plugin_path_var,
                     font=ctk.CTkFont("Segoe UI", 10), text_color=t["text_dim"]
                     ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="📂 Zvolit .cs plugin", height=32, width=160,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._pick_plugin).pack(side="left", padx=(8, 0))

        self.plugin_info_text = ctk.CTkTextbox(main, height=300,
                                               font=ctk.CTkFont("Courier New", 11),
                                               fg_color=t["secondary"], text_color=t["text"],
                                               state="disabled")
        self.plugin_info_text.pack(fill="both", expand=True, pady=8)

    def _pick_plugin(self):
        path = filedialog.askopenfilename(
            title="Zvolit .cs plugin",
            filetypes=[("C# Soubory", "*.cs"), ("All", "*.*")]
        )
        if not path:
            return
        self.plugin_path_var.set(os.path.basename(path))
        self._analyze_plugin_file(path)

    def _analyze_plugin_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            patterns = {
                "Závislosti (PluginReference)": re.compile(r'\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)', re.MULTILINE),
                "Requires":                     re.compile(r'\[Requires\("([^"]+)"\)\]', re.MULTILINE),
                "Chat příkazy":                 re.compile(r'\[ChatCommand\s*\(\s*"([^"]+)"', re.MULTILINE),
                "Console příkazy":              re.compile(r'\[ConsoleCommand\s*\(\s*"([^"]+)"', re.MULTILINE),
                "Hooks":                        re.compile(r'(?:void|object|bool|string)\s+(On\w+|Can\w+)\s*\(', re.MULTILINE),
                "Oprávnění":                    re.compile(r'permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"', re.MULTILINE),
            }

            lines = [f"=== Analýza: {os.path.basename(path)} ===\n"]
            for name, pat in patterns.items():
                matches = list(set(m.group(1) for m in pat.finditer(content)))
                if matches:
                    lines.append(f"\n{name} ({len(matches)}):")
                    for m in sorted(matches):
                        lines.append(f"  • {m}")

            feat = []
            if "LoadConfig" in content or "SaveConfig" in content:
                feat.append("Config")
            if "lang.Register" in content or "lang.GetMessage" in content:
                feat.append("Lang")
            if "DataFileSystem" in content:
                feat.append("DataFile")
            lines.append(f"\nFunkce: {', '.join(feat) if feat else 'Žádné'}")

            self.plugin_info_text.configure(state="normal")
            self.plugin_info_text.delete("1.0", "end")
            self.plugin_info_text.insert("end", "\n".join(lines))
            self.plugin_info_text.configure(state="disabled")
        except Exception as e:
            self.plugin_info_text.configure(state="normal")
            self.plugin_info_text.delete("1.0", "end")
            self.plugin_info_text.insert("end", f"Chyba při analýze: {e}")
            self.plugin_info_text.configure(state="disabled")

    def _build_plugin_analyzer(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "Rust – Hromadná Analýza Pluginů", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Zvolte složku se .cs pluginy a zobrazte souhrnné informace o závislostech.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 10))

        row = ctk.CTkFrame(main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        self.analyzer_path_var = ctk.StringVar(value="Nezvolená složka...")
        ctk.CTkLabel(row, textvariable=self.analyzer_path_var,
                     font=ctk.CTkFont("Segoe UI", 10), text_color=t["text_dim"]
                     ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="📂 Zvolit složku", height=32, width=140,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._pick_plugin_folder).pack(side="left", padx=(8, 0))

        self.analyzer_text = ctk.CTkTextbox(main, font=ctk.CTkFont("Courier New", 10),
                                            fg_color=t["secondary"], text_color=t["text"],
                                            state="disabled")
        self.analyzer_text.pack(fill="both", expand=True, pady=8)

        _btn(main, "📄 Exportovat report .txt", self._export_report, t, width=220).pack(anchor="w")
        self._analysis_results = []

    def _pick_plugin_folder(self):
        path = filedialog.askdirectory(title="Zvolit složku s pluginy")
        if not path:
            return
        self.analyzer_path_var.set(path)
        cs_files = [f for f in os.listdir(path) if f.endswith('.cs')]
        if not cs_files:
            self.analyzer_text.configure(state="normal")
            self.analyzer_text.delete("1.0", "end")
            self.analyzer_text.insert("end", "Žádné .cs soubory nenalezeny v této složce.")
            self.analyzer_text.configure(state="disabled")
            return

        patterns = {
            "deps": re.compile(r'\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)', re.MULTILINE),
            "chat": re.compile(r'\[ChatCommand\s*\(\s*"([^"]+)"', re.MULTILINE),
            "console": re.compile(r'\[ConsoleCommand\s*\(\s*"([^"]+)"', re.MULTILINE),
            "hooks": re.compile(r'(?:void|object|bool|string)\s+(On\w+|Can\w+)\s*\(', re.MULTILINE),
            "perms": re.compile(r'permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"', re.MULTILINE),
        }

        results = []
        for fname in cs_files:
            try:
                with open(os.path.join(path, fname), "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                info = {"file": fname}
                for k, pat in patterns.items():
                    info[k] = list(set(m.group(1) for m in pat.finditer(content)))
                feat = []
                if "LoadConfig" in content: feat.append("Config")
                if "lang.Register" in content: feat.append("Lang")
                if "DataFileSystem" in content: feat.append("Data")
                info["features"] = feat
                results.append(info)
            except Exception:
                pass

        self._analysis_results = results
        lines = [f"=== Analýza {len(results)} pluginů ===\n"]
        for r in results:
            lines.append(f"\n{r['file']}")
            lines.append(f"  Deps: {', '.join(r['deps']) or 'žádné'}")
            lines.append(f"  Hooks: {len(r['hooks'])}  Chat cmds: {len(r['chat'])}  Console cmds: {len(r['console'])}")
            lines.append(f"  Funkce: {', '.join(r['features']) or 'žádné'}")

        self.analyzer_text.configure(state="normal")
        self.analyzer_text.delete("1.0", "end")
        self.analyzer_text.insert("end", "\n".join(lines))
        self.analyzer_text.configure(state="disabled")

    def _export_report(self):
        if not self._analysis_results:
            messagebox.showwarning("Chyba", "Nejprve zvolte složku s pluginy.")
            return
        path = filedialog.asksaveasfilename(
            title="Uložit report", defaultextension=".txt",
            initialfile="plugin_report.txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("ZeddiHub Plugin Dependency Report\n" + "="*60 + "\n\n")
            for r in self._analysis_results:
                f.write(f"Plugin: {r['file']}\n")
                f.write(f"  Dependencies: {', '.join(r['deps']) or 'None'}\n")
                f.write(f"  Hooks ({len(r['hooks'])}): {', '.join(r['hooks'][:10])}\n")
                f.write(f"  Commands: {', '.join(r['chat'] + r['console']) or 'None'}\n")
                f.write(f"  Features: {', '.join(r['features']) or 'None'}\n\n")
        messagebox.showinfo("Uloženo", f"Report uložen:\n{path}")


# ─────────────────────────────────────────────
# RUST SERVER TOOLS
# ─────────────────────────────────────────────

class RustServerPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        t = self.theme
        tab = ctk.CTkTabview(self, fg_color=t["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("🖥 Server Config")
        tab.add("🔧 Plugin Manager")
        tab.add("🌐 RCON Klient")

        self._build_server_config(tab.tab("🖥 Server Config"))
        self._build_plugin_manager(tab.tab("🔧 Plugin Manager"))
        self._build_rcon(tab.tab("🌐 RCON Klient"))

    def _build_server_config(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "Rust – Server Config Generátor", 16, bold=True, color=t["primary"]
               ).pack(padx=4, pady=(4, 8), anchor="w")

        server_defs = {
            "Základní nastavení": {
                "server.hostname":     ("Název serveru",      "ZeddiHub Rust Server"),
                "server.description":  ("Popis serveru",      "ZeddiHub Rust Community"),
                "server.url":          ("URL webu",           "https://zeddihub.eu"),
                "server.headerimage":  ("Header obrázek URL", ""),
                "server.port":         ("Port",               "28015"),
                "server.level":        ("Mapa",               "Procedural Map"),
                "server.seed":         ("Seed",               "12345"),
                "server.worldsize":    ("Velikost světa",     "4000"),
                "server.maxplayers":   ("Max hráčů",          "100"),
            },
            "Výkon": {
                "server.tickrate":     ("Tick rate",          "30"),
                "server.gc_mb":        ("GC paměť (MB)",      "256"),
                "server.netcache":     ("Net cache",          "4"),
                "fps.limit":           ("FPS limit",          "30"),
            },
            "Herní pravidla": {
                "server.pve":          ("PvE mód",            "false"),
                "decay.scale":         ("Decay rychlost",     "1.0"),
                "server.radiation":    ("Radiace",            "true"),
                "server.airdropfrequency": ("Airdrop frekvence", "0"),
            },
            "Oxide / uMod": {
                "oxide.reload":        ("Reload příkaz",      "oxide.reload *"),
                "oxide.unload":        ("Unload příkaz",      "oxide.unload *"),
            },
        }

        self._srv_vars = {}
        for sec_name, fields in server_defs.items():
            outer = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=8)
            outer.pack(fill="x", padx=0, pady=6)
            _label(outer, sec_name, 13, bold=True, color=t["primary"]).pack(
                padx=14, pady=(10, 6), anchor="w")
            sec = ctk.CTkFrame(outer, fg_color="transparent")
            sec.pack(fill="x", padx=0, pady=(0, 6))
            sec.grid_columnconfigure(1, weight=1)
            for i, (k, vals) in enumerate(fields.items()):
                lbl, default = vals
                self._srv_vars[k] = _entry_row(sec, lbl, default, t, i)

        _btn(scroll, "💾 Generovat server start.bat", self._save_server_bat, t).pack(
            padx=4, pady=6, fill="x")
        ctk.CTkButton(scroll, text="📄 Generovat server.cfg",
                      fg_color=t["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 12), height=36,
                      command=self._save_server_cfg
                      ).pack(padx=4, pady=(0, 10), fill="x")

    def _save_server_bat(self):
        path = filedialog.asksaveasfilename(
            title="Uložit server start script",
            defaultextension=".bat",
            initialfile="start_rust_server.bat",
            filetypes=[("Batch", "*.bat"), ("Shell", "*.sh"), ("All", "*.*")]
        )
        if not path:
            return
        hn = self._srv_vars.get("server.hostname", ctk.StringVar(value="RustServer")).get()
        port = self._srv_vars.get("server.port", ctk.StringVar(value="28015")).get()
        seed = self._srv_vars.get("server.seed", ctk.StringVar(value="12345")).get()
        size = self._srv_vars.get("server.worldsize", ctk.StringVar(value="4000")).get()
        maxp = self._srv_vars.get("server.maxplayers", ctk.StringVar(value="100")).get()

        with open(path, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("REM Rust Server Start Script - Generated by ZeddiHub Tools\n")
            f.write(f'RustDedicated.exe -batchmode ^^\n')
            f.write(f'  +server.port {port} ^^\n')
            f.write(f'  +server.hostname "{hn}" ^^\n')
            f.write(f'  +server.worldsize {size} ^^\n')
            f.write(f'  +server.seed {seed} ^^\n')
            f.write(f'  +server.maxplayers {maxp} ^^\n')
            f.write(f'  +server.saveinterval 600 ^^\n')
            f.write(f'  +rcon.port 28016 ^^\n')
            f.write(f'  +rcon.password changeme ^^\n')
            f.write(f'  -logfile "%DATE:~-4%-%DATE:~4,2%-%DATE:~7,2%.log"\n')
        messagebox.showinfo("Uloženo", f"Start script uložen:\n{path}")

    def _save_server_cfg(self):
        path = filedialog.asksaveasfilename(
            title="Uložit server.cfg", defaultextension=".cfg",
            initialfile="rust_server.cfg",
            filetypes=[("Config", "*.cfg"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("// Rust Server Config - Generated by ZeddiHub Tools\n\n")
            for k, var in self._srv_vars.items():
                if var.get():
                    f.write(f"{k} \"{var.get()}\"\n")
        messagebox.showinfo("Uloženo", f"server.cfg uložen:\n{path}")

    def _build_plugin_manager(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "Rust – Plugin Manager (Oxide/uMod)", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Správa, opravy a překlad Oxide pluginů ze zdrojových souborů.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 10))

        # Source folder selection
        row = ctk.CTkFrame(main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        self.pm_path_var = ctk.StringVar(value="Nezvolená složka se soubory .cs...")
        ctk.CTkLabel(row, textvariable=self.pm_path_var,
                     font=ctk.CTkFont("Segoe UI", 10), text_color=t["text_dim"]
                     ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="📂 Zvolit složku", height=32, width=140,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._pick_plugin_source).pack(side="left", padx=(8, 0))

        # Operations grid
        ops_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        ops_frame.pack(fill="x", pady=8)
        _label(ops_frame, "Dostupné operace", 12, bold=True, color=t["text_dim"]).pack(
            padx=14, pady=(10, 6), anchor="w")

        ops = [
            ("🛠 Hromadná oprava (záplaty)", self._bulk_fix),
            ("💻 Úprava příkazů v kódu",     self._edit_commands),
            ("🌍 Přeložit zprávy v kódu",    self._translate_messages),
            ("🏷 Detekce prefixů",           self._detect_prefixes),
            ("📊 Analýza závislostí",        self._analyze_deps),
        ]
        ops_grid = ctk.CTkFrame(ops_frame, fg_color="transparent")
        ops_grid.pack(padx=12, pady=(0, 12), fill="x")

        for i, (name, cmd) in enumerate(ops):
            ctk.CTkButton(
                ops_grid, text=name, height=34,
                fg_color=t["secondary"], hover_color=t["primary"],
                font=ctk.CTkFont("Segoe UI", 11),
                command=cmd
            ).grid(row=i // 2, column=i % 2, padx=4, pady=3, sticky="ew")
        ops_grid.grid_columnconfigure(0, weight=1)
        ops_grid.grid_columnconfigure(1, weight=1)

        # Output
        self.pm_output = ctk.CTkTextbox(main, font=ctk.CTkFont("Courier New", 10),
                                        fg_color=t["secondary"], text_color=t["text"],
                                        state="disabled")
        self.pm_output.pack(fill="both", expand=True, pady=8)

        self._pm_source_dir = ""

    def _pm_log(self, msg: str):
        self.pm_output.configure(state="normal")
        self.pm_output.insert("end", msg + "\n")
        self.pm_output.see("end")
        self.pm_output.configure(state="disabled")

    def _pick_plugin_source(self):
        path = filedialog.askdirectory(title="Zvolit složku s .cs pluginy")
        if not path:
            return
        self._pm_source_dir = path
        self.pm_path_var.set(path)
        cs_count = len([f for f in os.listdir(path) if f.endswith('.cs')])
        self._pm_log(f"✓ Složka zvolena: {path}")
        self._pm_log(f"  Nalezeno {cs_count} .cs souborů")

    _BULK_FIX_RULES = [
        (r"Pool\.GetList<(.+?)>\(\)",       r"Pool.Get<List<\1>>()"),
        (r"Pool\.FreeList\((.+?)\)",        r"Pool.FreeUnmanaged(\1)"),
        (r"OnPlayerInit\s*\(",              r"OnPlayerConnected("),
        (r"(\w+)\.SendConsoleCommand\(",    r"\1.Command("),
        (r"(\w+)\.net\.connection",         r"\1.Connection"),
        (r"(\s*)void\s+OnTick\s*\(",        r"\1// void OnTick("),
        (r"([^/])(SendNotification\s*\()",  r"\1// \2"),
    ]

    def _bulk_fix(self):
        if not self._pm_source_dir:
            self._pm_log("! Nejprve zvolte složku se soubory .cs"); return
        self._pm_log("→ Hromadná oprava - kontrola pluginů...")

        def _run():
            cs_files = [f for f in os.listdir(self._pm_source_dir) if f.endswith('.cs')]
            self._pm_log(f"  Nalezeno {len(cs_files)} pluginů...")
            fixed = 0
            for fname in cs_files:
                fpath = os.path.join(self._pm_source_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    new_content = content
                    changes = 0
                    for pat, rep in self._BULK_FIX_RULES:
                        new_content, n = re.subn(pat, rep, new_content)
                        changes += n
                    if changes > 0:
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        self._pm_log(f"  [OPRAVENO {changes}x] {fname}")
                        fixed += 1
                    else:
                        self._pm_log(f"  [OK] {fname}")
                except Exception as e:
                    self._pm_log(f"  [CHYBA] {fname}: {e}")
            self._pm_log(f"✓ Oprava dokončena. Upraveno {fixed}/{len(cs_files)} souborů.")

        threading.Thread(target=_run, daemon=True).start()

    def _edit_commands(self):
        if not self._pm_source_dir:
            self._pm_log("! Nejprve zvolte složku"); return
        self._pm_log("→ Hledám příkazy v pluginech...")
        cs_files = [f for f in os.listdir(self._pm_source_dir) if f.endswith('.cs')]
        found = 0
        for fname in cs_files:
            try:
                with open(os.path.join(self._pm_source_dir, fname), encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                cmds = re.findall(r'\[(?:Chat|Console)Command\s*\(\s*"([^"]+)"', content)
                if cmds:
                    self._pm_log(f"  {fname}: {', '.join(cmds)}")
                    found += len(cmds)
            except Exception:
                pass
        self._pm_log(f"✓ Nalezeno {found} příkazů celkem.")

    def _translate_messages(self):
        self._pm_log("→ Funkce překladu zpráv - použijte Translator modul pro plnou funkcionalitu.")

    def _detect_prefixes(self):
        if not self._pm_source_dir:
            self._pm_log("! Nejprve zvolte složku"); return
        self._pm_log("→ Detekce prefixů v pluginech...")
        cs_files = [f for f in os.listdir(self._pm_source_dir) if f.endswith('.cs')]
        pat = re.compile(r'"(\[[\w\s]+\])"')
        for fname in cs_files:
            try:
                with open(os.path.join(self._pm_source_dir, fname), encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                prefixes = list(set(pat.findall(content)))
                if prefixes:
                    self._pm_log(f"  {fname}: {', '.join(prefixes[:5])}")
            except Exception:
                pass
        self._pm_log("✓ Detekce dokončena.")

    def _analyze_deps(self):
        if not self._pm_source_dir:
            self._pm_log("! Nejprve zvolte složku"); return
        self._pm_log("→ Analýza závislostí pluginů...")
        pat = re.compile(r'\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)', re.MULTILINE)
        cs_files = [f for f in os.listdir(self._pm_source_dir) if f.endswith('.cs')]
        all_deps = {}
        for fname in cs_files:
            try:
                with open(os.path.join(self._pm_source_dir, fname), encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                deps = list(set(pat.findall(content)))
                if deps:
                    all_deps[fname] = deps
                    self._pm_log(f"  {fname}: vyžaduje {', '.join(deps)}")
            except Exception:
                pass
        if not all_deps:
            self._pm_log("  Žádné závislosti nenalezeny.")
        self._pm_log(f"✓ Analýza dokončena. {len(all_deps)} pluginů má závislosti.")

    def _build_rcon(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "Rust – RCON Klient", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Připojení k Rust serveru přes Source RCON (port obvykle game_port + 1).",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 10))

        cfg_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        cfg_frame.pack(fill="x", pady=4)

        self._rcon_host = ctk.StringVar(value="127.0.0.1")
        self._rcon_port = ctk.StringVar(value="28016")
        self._rcon_pw = ctk.StringVar()

        for i, (lbl, var, mask) in enumerate([
            ("IP adresa", self._rcon_host, False),
            ("Port",      self._rcon_port, False),
            ("RCON heslo", self._rcon_pw, True),
        ]):
            ctk.CTkLabel(cfg_frame, text=lbl, font=ctk.CTkFont("Segoe UI", 11),
                         text_color=t["text_dim"], width=110, anchor="w"
                         ).grid(row=i, column=0, padx=(12, 4), pady=4, sticky="w")
            ctk.CTkEntry(cfg_frame, textvariable=var, width=200,
                         fg_color=t["secondary"], text_color=t["text"],
                         font=ctk.CTkFont("Courier New", 11),
                         show="*" if mask else ""
                         ).grid(row=i, column=1, padx=4, pady=4, sticky="w")

        _btn(cfg_frame, "🔌 Připojit", self._rcon_connect, t, width=120
             ).grid(row=0, column=2, rowspan=3, padx=12)

        quick_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=8)
        quick_frame.pack(fill="x", pady=8)
        _label(quick_frame, "Rychlé příkazy:", 11, bold=True, color=t["text_dim"]).pack(
            padx=12, pady=(8, 4), anchor="w")

        quick_cmds = ["status", "playerlist", "oxide.reload *", "oxide.unload *",
                      "save", "quit", "env.time 12", "weather.clouds 0"]
        qrow = ctk.CTkFrame(quick_frame, fg_color="transparent")
        qrow.pack(padx=12, pady=(0, 10), fill="x")
        for i, cmd in enumerate(quick_cmds):
            ctk.CTkButton(qrow, text=cmd, height=28, width=130,
                          fg_color=t["secondary"], hover_color=t["primary"],
                          font=ctk.CTkFont("Courier New", 10),
                          command=lambda c=cmd: self._rcon_quick(c)
                          ).grid(row=i // 4, column=i % 4, padx=3, pady=2)

        self.rcon_output = ctk.CTkTextbox(main, font=ctk.CTkFont("Courier New", 10),
                                          fg_color=t["secondary"], text_color="#44ff44",
                                          state="disabled")
        self.rcon_output.pack(fill="both", expand=True, pady=8)

        cmd_row = ctk.CTkFrame(main, fg_color="transparent")
        cmd_row.pack(fill="x")
        self.rcon_cmd = ctk.CTkEntry(cmd_row, placeholder_text="RCON příkaz (Rust)...",
                                     fg_color=t["secondary"], text_color=t["text"],
                                     font=ctk.CTkFont("Courier New", 12))
        self.rcon_cmd.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.rcon_cmd.bind("<Return>", lambda _: self._rcon_send())
        _btn(cmd_row, "Odeslat", self._rcon_send, t, width=100).pack(side="left")

        self._rcon_socket = None

    def _rcon_log(self, msg: str):
        self.rcon_output.configure(state="normal")
        self.rcon_output.insert("end", msg + "\n")
        self.rcon_output.see("end")
        self.rcon_output.configure(state="disabled")

    def _rcon_quick(self, cmd: str):
        if not self._rcon_socket:
            self._rcon_log("! Nejste připojeni")
            return
        old = self.rcon_cmd.get()
        self.rcon_cmd.delete(0, "end")
        self.rcon_cmd.insert(0, cmd)
        self._rcon_send()

    def _rcon_connect(self):
        import socket, struct
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
                r2 = struct.unpack('<i', rest[:4])[0] if len(rest) >= 4 else -1
                if r2 == -1:
                    self.after(0, self._rcon_log, "✗ Špatné heslo"); s.close(); return
                self._rcon_socket = s
                self.after(0, self._rcon_log, f"✓ Připojeno k Rust serveru {host}:{port}")
                self.after(0, self._rcon_log, "  Užitečné: status, playerlist, oxide.reload *, kick <jméno>")
            except Exception as e:
                self.after(0, self._rcon_log, f"✗ Chyba připojení: {e}")

        threading.Thread(target=connect, daemon=True).start()

    def _rcon_send(self):
        import struct
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
                data = self._rcon_socket.recv(4096)
                body = data[12:].rstrip(b'\x00').decode('utf-8', errors='replace')
                self.after(0, self._rcon_log, f"> {cmd}")
                for line in body.splitlines():
                    self.after(0, self._rcon_log, f"  {line}")
            except Exception as e:
                self.after(0, self._rcon_log, f"! Chyba: {e}")

        threading.Thread(target=send, daemon=True).start()
