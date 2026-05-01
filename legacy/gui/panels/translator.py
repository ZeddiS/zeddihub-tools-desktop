"""
ZeddiHub Tools - Translator GUI panel.
Calls the existing translator logic in a background thread.
"""

import os
import sys
import json
import time
import threading
import subprocess
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#ffffff", **kw)


def _btn(parent, text, cmd, theme, width=180, height=36, **kw):
    kw.setdefault("corner_radius", int(theme.get("radius_button", 10)))
    kw.setdefault("border_width", 0)
    return ctk.CTkButton(parent, text=text, command=cmd,
                         fg_color=theme["primary"], hover_color=theme["primary_hover"],
                         text_color=theme["button_fg"],
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         width=width, height=height, **kw)


SUPPORTED_LANGS = {
    "cs": "Čeština", "en": "Angličtina", "de": "Němčina",
    "ru": "Ruština", "es": "Španělština", "fr": "Francouzština",
    "it": "Italština", "nl": "Nizozemština", "pl": "Polština",
    "pt": "Portugalština", "tr": "Turečtina", "zh": "Čínština",
    "ja": "Japonština", "ko": "Korejština", "uk": "Ukrajinština",
    "ro": "Rumunština", "hu": "Maďarština", "sk": "Slovenština",
    "bg": "Bulharština", "sv": "Švédština",
}

CONFIG_FILE = Path(os.environ.get("APPDATA", Path.home())) / "ZeddiHub" / "Tools" / "translator_gui.json"

ENGINES = {
    "Google Translate (Gratis)":    "google",
    "LibreTranslate (Offline/API)": "libretranslate",
    "DeepL API (klíč)":            "deepl",
    "MyMemory (gratis)":            "mymemory",
}


class TranslatorPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._running = False
        self._lang_vars: dict[str, ctk.BooleanVar] = {}
        self._config = self._load_config()
        self._build()

    def _load_config(self) -> dict:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {
            "source_dir": "",
            "target_dir": "",
            "source_lang": "en",
            "selected_langs": ["cs", "de", "ru"],
            "engine": "google",
            "file_extension": ".json",
            "api_key": "",
            "prefix_text": "",
            "prefix_enabled": False,
        }

    def _save_config(self):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(self._config, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        except Exception:
            pass

    def _build(self):
        t = self.theme
        tab = ctk.CTkTabview(self, fg_color=t["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("▶ Překlad")
        tab.add("⚙ Nastavení")
        tab.add("🏷 Prefix")
        tab.add("📂 Složky")

        self._build_run_tab(tab.tab("▶ Překlad"))
        self._build_settings_tab(tab.tab("⚙ Nastavení"))
        self._build_prefix_tab(tab.tab("🏷 Prefix"))
        self._build_folders_tab(tab.tab("📂 Složky"))

    # ─── PŘEKLAD ───────────────────────────────
    def _build_run_tab(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "ZeddiHub Translator", 18, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Hromadný překlad herních souborů (.json, .txt, .lang) do více jazyků najednou.",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 12))

        # Status row
        status_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        status_frame.pack(fill="x", pady=4)

        info_grid = ctk.CTkFrame(status_frame, fg_color="transparent")
        info_grid.pack(fill="x", padx=16, pady=12)

        self._src_label = _label(info_grid, "📁 Zdroj: Nezvoleno", 11, color=t["text_dim"])
        self._src_label.grid(row=0, column=0, sticky="w", pady=2)

        self._tgt_label = _label(info_grid, "📁 Cíl: Nezvoleno", 11, color=t["text_dim"])
        self._tgt_label.grid(row=1, column=0, sticky="w", pady=2)

        self._engine_label = _label(info_grid, f"🌐 Překladač: {self._config['engine']}", 11, color=t["text_dim"])
        self._engine_label.grid(row=2, column=0, sticky="w", pady=2)

        self._update_status_labels()

        # Language selection
        langs_frame = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        langs_frame.pack(fill="x", pady=8)
        _label(langs_frame, "Cílové jazyky:", 12, bold=True, color=t["text_dim"]).pack(
            padx=12, pady=(10, 6), anchor="w")

        langs_grid = ctk.CTkFrame(langs_frame, fg_color="transparent")
        langs_grid.pack(padx=12, pady=(0, 12), fill="x")

        all_langs = list(SUPPORTED_LANGS.items())
        cols = 4
        for i, (code, name) in enumerate(all_langs):
            var = ctk.BooleanVar(value=code in self._config["selected_langs"])
            self._lang_vars[code] = var
            ctk.CTkCheckBox(langs_grid, text=f"{name} ({code})", variable=var,
                            text_color=t["text"], fg_color=t["primary"],
                            hover_color=t["primary_hover"],
                            font=ctk.CTkFont("Segoe UI", 10),
                            command=self._update_selected_langs
                            ).grid(row=i // cols, column=i % cols, padx=4, pady=2, sticky="w")
        for c in range(cols):
            langs_grid.grid_columnconfigure(c, weight=1)

        # Quick lang buttons
        qrow = ctk.CTkFrame(langs_frame, fg_color="transparent")
        qrow.pack(padx=12, pady=(0, 10))
        for label, codes in [("Hlavní", ["en","cs","de","ru","es","fr"]),
                              ("Všechny", list(SUPPORTED_LANGS.keys())),
                              ("Žádné", [])]:
            ctk.CTkButton(qrow, text=label, height=28, width=90,
                          fg_color=t["secondary"], hover_color=t["primary"],
                          font=ctk.CTkFont("Segoe UI", 10),
                          command=lambda c=codes: self._set_langs(c)
                          ).pack(side="left", padx=4)

        # Progress + output
        self.progress = ctk.CTkProgressBar(main, mode="determinate",
                                           fg_color=t["secondary"], progress_color=t["primary"])
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(8, 4))

        self.status_var = ctk.StringVar(value="Připraven.")
        ctk.CTkLabel(main, textvariable=self.status_var, font=ctk.CTkFont("Segoe UI", 10),
                     text_color=t["text_dim"]).pack(anchor="w", pady=(0, 4))

        self.output_text = ctk.CTkTextbox(main, height=160,
                                          font=ctk.CTkFont("Courier New", 10),
                                          fg_color=t["secondary"], text_color=t["text"],
                                          state="disabled")
        self.output_text.pack(fill="both", expand=True, pady=4)

        # Buttons
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x", pady=6)

        self.run_btn = _btn(btn_row, "▶ Spustit překlad", self._run_translation, t, width=200)
        self.run_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="⏹ Zastavit", command=self._stop_translation,
                      fg_color="#8b2020", hover_color="#6b1818",
                      font=ctk.CTkFont("Segoe UI", 12), height=36, width=120
                      ).pack(side="left")

        ctk.CTkButton(btn_row, text="📂 Otevřít cílovou složku",
                      fg_color=t["secondary"], hover_color="#3a3a4a",
                      font=ctk.CTkFont("Segoe UI", 11), height=36,
                      command=self._open_target_folder
                      ).pack(side="right")

    def _update_status_labels(self):
        src = self._config.get("source_dir", "") or "Nezvoleno"
        tgt = self._config.get("target_dir", "") or "Nezvoleno"
        eng = self._config.get("engine", "google")
        self._src_label.configure(text=f"📁 Zdroj: {os.path.basename(src) if src != 'Nezvoleno' else src} ({self._config.get('source_lang','en')})")
        self._tgt_label.configure(text=f"📁 Cíl: {os.path.basename(tgt) if tgt != 'Nezvoleno' else tgt}")
        self._engine_label.configure(text=f"🌐 Překladač: {eng}")

    def _update_selected_langs(self):
        self._config["selected_langs"] = [c for c, v in self._lang_vars.items() if v.get()]
        self._save_config()

    def _set_langs(self, codes: list):
        for code, var in self._lang_vars.items():
            var.set(code in codes)
        self._update_selected_langs()

    def _log(self, msg: str):
        self.output_text.configure(state="normal")
        self.output_text.insert("end", msg + "\n")
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def _run_translation(self):
        if self._running:
            return
        src = self._config.get("source_dir", "")
        tgt = self._config.get("target_dir", "")
        if not src or not os.path.isdir(src):
            messagebox.showerror("Chyba", "Nejprve nastavte zdrojovou složku v záložce Nastavení!")
            return
        if not tgt:
            messagebox.showerror("Chyba", "Nejprve nastavte cílovou složku v záložce Nastavení!")
            return

        selected = [c for c, v in self._lang_vars.items() if v.get()]
        if not selected:
            messagebox.showerror("Chyba", "Vyberte alespoň jeden cílový jazyk!")
            return

        self._running = True
        self.status_var.set("Překlad probíhá...")
        self.progress.set(0)
        self.run_btn.configure(state="disabled")

        def translate():
            try:
                ext = self._config.get("file_extension", ".json")
                files = [f for f in os.listdir(src) if f.endswith(ext)]
                if not files:
                    self.after(0, self._log, f"Žádné {ext} soubory nenalezeny ve zdrojové složce!")
                    self.after(0, self._finish_translation)
                    return

                engine = self._config.get("engine", "google")
                self.after(0, self._log, f"Spouštím překlad {len(files)} soubor(ů)...")
                self.after(0, self._log, f"Motor: {engine} | Jazyky: {', '.join(selected)}")
                self.after(0, self._log, "")

                total = len(files) * len(selected)
                done = 0

                for fname in files:
                    if not self._running:
                        break
                    src_path = os.path.join(src, fname)
                    try:
                        with open(src_path, "r", encoding="utf-8") as f:
                            if ext == ".json":
                                data = json.load(f)
                            else:
                                data = {"text": f.read()}

                        for lang in selected:
                            if not self._running:
                                break
                            self.after(0, self._log, f"→ Překládám {fname} → {lang}...")

                            translated_data = self._translate_data(data, lang, engine)

                            lang_dir = os.path.join(tgt, lang)
                            os.makedirs(lang_dir, exist_ok=True)
                            out_path = os.path.join(lang_dir, fname)

                            with open(out_path, "w", encoding="utf-8") as f:
                                if ext == ".json":
                                    json.dump(translated_data, f, ensure_ascii=False, indent=2)
                                else:
                                    f.write(translated_data.get("text", ""))

                            done += 1
                            pct = done / total
                            self.after(0, self.progress.set, pct)
                            self.after(0, self.status_var.set,
                                       f"Přeloženo: {done}/{total} ({lang.upper()})")

                    except Exception as e:
                        self.after(0, self._log, f"  ! Chyba u {fname}: {e}")

                if self._running:
                    self.after(0, self._log, "")
                    self.after(0, self._log, f"✓ Překlad dokončen! {done}/{total} jazykových verzí.")
                    self.after(0, self.progress.set, 1.0)

            except Exception as e:
                self.after(0, self._log, f"! Kritická chyba: {e}")
            finally:
                self.after(0, self._finish_translation)

        threading.Thread(target=translate, daemon=True).start()

    def _translate_data(self, data: dict, target_lang: str, engine: str) -> dict:
        """Translate dict values to target language."""
        result = {}
        src_lang = self._config.get("source_lang", "en")

        for key, value in data.items():
            if not isinstance(value, str) or not value.strip():
                result[key] = value
                continue
            try:
                translated = self._translate_text(value, src_lang, target_lang, engine)
                if self._config.get("prefix_enabled") and self._config.get("prefix_text"):
                    prefix = self._config["prefix_text"]
                    if not translated.startswith(prefix):
                        translated = f"{prefix} {translated}"
                result[key] = translated
            except Exception:
                result[key] = value  # fallback to original
        return result

    def _translate_text(self, text: str, src: str, tgt: str, engine: str) -> str:
        """Translate a single text string."""
        import urllib.request
        import urllib.parse

        if src == tgt:
            return text

        if engine == "google":
            # Free Google Translate API (unofficial)
            url = (f"https://translate.googleapis.com/translate_a/single"
                   f"?client=gtx&sl={src}&tl={tgt}&dt=t&q={urllib.parse.quote(text)}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
            return "".join(part[0] for part in result[0] if part[0])

        elif engine == "mymemory":
            url = (f"https://api.mymemory.translated.net/get"
                   f"?q={urllib.parse.quote(text)}&langpair={src}|{tgt}")
            req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            return data["responseData"]["translatedText"]

        elif engine == "libretranslate":
            api_url = self._config.get("libretranslate_url", "https://libretranslate.com/translate")
            payload = json.dumps({
                "q": text, "source": src, "target": tgt,
                "api_key": self._config.get("api_key", "")
            }).encode()
            req = urllib.request.Request(api_url, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())["translatedText"]

        elif engine == "deepl":
            import urllib.parse
            api_key = self._config.get("api_key", "")
            if not api_key:
                raise ValueError("DeepL API klíč není nastaven!")
            data = urllib.parse.urlencode({
                "auth_key": api_key, "text": text,
                "source_lang": src.upper(), "target_lang": tgt.upper()
            }).encode()
            req = urllib.request.Request(
                "https://api-free.deepl.com/v2/translate", data=data)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())["translations"][0]["text"]

        return text  # fallback

    def _stop_translation(self):
        self._running = False
        self.status_var.set("Překlad zastaven.")
        self._log("⏹ Překlad zastaven uživatelem.")

    def _finish_translation(self):
        self._running = False
        self.run_btn.configure(state="normal")
        self.status_var.set("Připraven.")

    def _open_target_folder(self):
        tgt = self._config.get("target_dir", "")
        if tgt and os.path.isdir(tgt):
            os.startfile(tgt)
        else:
            messagebox.showwarning("Chyba", "Cílová složka není nastavena nebo neexistuje.")

    # ─── NASTAVENÍ ──────────────────────────────
    def _build_settings_tab(self, tab):
        t = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        _label(scroll, "Nastavení překladače", 16, bold=True, color=t["primary"]).pack(anchor="w", pady=(0, 12))

        # Source folder
        sec = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        sec.pack(fill="x", pady=6)
        _label(sec, "📁 Zdrojová složka (vstupní soubory)", 12, bold=True, color=t["text_dim"]).pack(
            padx=12, pady=(10, 4), anchor="w")

        src_row = ctk.CTkFrame(sec, fg_color="transparent")
        src_row.pack(fill="x", padx=12, pady=(0, 8))
        self._src_entry = ctk.CTkEntry(src_row, placeholder_text="Cesta ke zdrojové složce...",
                                       fg_color=t["secondary"], text_color=t["text"],
                                       font=ctk.CTkFont("Segoe UI", 10))
        self._src_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        if self._config.get("source_dir"):
            self._src_entry.insert(0, self._config["source_dir"])

        ctk.CTkButton(src_row, text="📂 Procházet", height=32, width=110,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._pick_source).pack(side="left")

        # Source language
        _label(sec, "Jazyk zdrojových souborů:", 11, color=t["text_dim"]).pack(
            padx=12, pady=(0, 4), anchor="w")
        self._src_lang_var = ctk.StringVar(value=self._config.get("source_lang", "en"))
        src_lang_frame = ctk.CTkFrame(sec, fg_color="transparent")
        src_lang_frame.pack(padx=12, pady=(0, 10), fill="x")
        common_langs = [("en", "Angličtina"), ("cs", "Čeština"), ("de", "Němčina"),
                        ("ru", "Ruština"), ("fr", "Francouzština"), ("es", "Španělština")]
        for code, name in common_langs:
            ctk.CTkRadioButton(src_lang_frame, text=f"{name} ({code})",
                               variable=self._src_lang_var, value=code,
                               text_color=t["text"], fg_color=t["primary"],
                               font=ctk.CTkFont("Segoe UI", 10),
                               command=self._save_settings
                               ).pack(side="left", padx=6)

        # Target folder
        sec2 = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        sec2.pack(fill="x", pady=6)
        _label(sec2, "📁 Cílová složka (výstupní soubory)", 12, bold=True, color=t["text_dim"]).pack(
            padx=12, pady=(10, 4), anchor="w")

        tgt_row = ctk.CTkFrame(sec2, fg_color="transparent")
        tgt_row.pack(fill="x", padx=12, pady=(0, 8))
        self._tgt_entry = ctk.CTkEntry(tgt_row, placeholder_text="Cesta k cílové složce...",
                                       fg_color=t["secondary"], text_color=t["text"],
                                       font=ctk.CTkFont("Segoe UI", 10))
        self._tgt_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        if self._config.get("target_dir"):
            self._tgt_entry.insert(0, self._config["target_dir"])

        ctk.CTkButton(tgt_row, text="📂 Procházet", height=32, width=110,
                      fg_color=t["primary"], hover_color=t["primary_hover"],
                      command=self._pick_target).pack(side="left")

        # File extension
        sec3 = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        sec3.pack(fill="x", pady=6)
        _label(sec3, "Formát souborů:", 12, bold=True, color=t["text_dim"]).pack(
            padx=12, pady=(10, 4), anchor="w")
        self._ext_var = ctk.StringVar(value=self._config.get("file_extension", ".json"))
        ext_row = ctk.CTkFrame(sec3, fg_color="transparent")
        ext_row.pack(padx=12, pady=(0, 10))
        for ext in [".json", ".txt", ".lang"]:
            ctk.CTkRadioButton(ext_row, text=ext, variable=self._ext_var, value=ext,
                               text_color=t["text"], fg_color=t["primary"],
                               font=ctk.CTkFont("Segoe UI", 11),
                               command=self._save_settings).pack(side="left", padx=8)

        # Engine
        sec4 = ctk.CTkFrame(scroll, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        sec4.pack(fill="x", pady=6)
        _label(sec4, "Překladový motor:", 12, bold=True, color=t["text_dim"]).pack(
            padx=12, pady=(10, 4), anchor="w")
        self._engine_var = ctk.StringVar(value=self._config.get("engine", "google"))
        engine_frame = ctk.CTkFrame(sec4, fg_color="transparent")
        engine_frame.pack(padx=12, fill="x")
        for i, (name, code) in enumerate(ENGINES.items()):
            ctk.CTkRadioButton(engine_frame, text=name, variable=self._engine_var, value=code,
                               text_color=t["text"], fg_color=t["primary"],
                               font=ctk.CTkFont("Segoe UI", 10),
                               command=self._save_settings
                               ).grid(row=i // 2, column=i % 2, padx=6, pady=3, sticky="w")
        engine_frame.grid_columnconfigure(0, weight=1)
        engine_frame.grid_columnconfigure(1, weight=1)

        _label(sec4, "API klíč (pro DeepL / LibreTranslate):", 11, color=t["text_dim"]).pack(
            padx=12, pady=(8, 2), anchor="w")
        self._api_key_entry = ctk.CTkEntry(sec4, placeholder_text="Váš API klíč...",
                                           fg_color=t["secondary"], text_color=t["text"],
                                           font=ctk.CTkFont("Courier New", 11), show="*")
        self._api_key_entry.pack(padx=12, pady=(0, 12), fill="x")
        if self._config.get("api_key"):
            self._api_key_entry.insert(0, self._config["api_key"])

        _btn(scroll, "💾 Uložit nastavení", self._save_settings, t).pack(pady=8, fill="x")

    def _pick_source(self):
        path = filedialog.askdirectory(title="Zvolit zdrojovou složku")
        if not path:
            return
        self._src_entry.delete(0, "end")
        self._src_entry.insert(0, path)
        self._save_settings()

    def _pick_target(self):
        path = filedialog.askdirectory(title="Zvolit cílovou složku")
        if not path:
            return
        self._tgt_entry.delete(0, "end")
        self._tgt_entry.insert(0, path)
        self._save_settings()

    def _save_settings(self):
        self._config["source_dir"] = self._src_entry.get().strip()
        self._config["target_dir"] = self._tgt_entry.get().strip()
        self._config["source_lang"] = self._src_lang_var.get()
        self._config["file_extension"] = self._ext_var.get()
        self._config["engine"] = self._engine_var.get()
        self._config["api_key"] = self._api_key_entry.get().strip()
        self._save_config()
        self._update_status_labels()

    # ─── PREFIX ─────────────────────────────────
    def _build_prefix_tab(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "Prefix Manager", 16, bold=True, color=t["primary"]).pack(anchor="w")
        _label(main, "Přidejte prefix k přeloženým zprávám (např. název pluginu nebo serveru).",
               11, color=t["text_dim"]).pack(anchor="w", pady=(0, 12))

        sec = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
        sec.pack(fill="x", pady=6)

        self._prefix_enabled_var = ctk.BooleanVar(value=self._config.get("prefix_enabled", False))
        ctk.CTkCheckBox(sec, text="Povolit prefix", variable=self._prefix_enabled_var,
                        text_color=t["text"], fg_color=t["primary"],
                        font=ctk.CTkFont("Segoe UI", 12),
                        command=self._save_prefix).pack(padx=12, pady=(12, 6), anchor="w")

        _label(sec, "Text prefixu:", 11, color=t["text_dim"]).pack(padx=12, anchor="w")
        self._prefix_entry = ctk.CTkEntry(sec, placeholder_text="[ZeddiHub]",
                                          fg_color=t["secondary"], text_color=t["text"],
                                          font=ctk.CTkFont("Courier New", 12))
        self._prefix_entry.pack(padx=12, pady=4, fill="x")
        if self._config.get("prefix_text"):
            self._prefix_entry.insert(0, self._config["prefix_text"])

        _label(sec, "Náhled:", 11, color=t["text_dim"]).pack(padx=12, pady=(8, 2), anchor="w")
        self._prefix_preview = _label(sec, f"[ZeddiHub] Přeložená zpráva...", 11,
                                      color=t["accent"])
        self._prefix_preview.pack(padx=12, pady=(0, 12), anchor="w")

        self._prefix_entry.bind("<KeyRelease>", self._update_prefix_preview)
        _btn(sec, "💾 Uložit prefix", self._save_prefix, t).pack(padx=12, pady=(0, 12), fill="x")

    def _update_prefix_preview(self, _=None):
        prefix = self._prefix_entry.get().strip()
        if prefix and self._prefix_enabled_var.get():
            self._prefix_preview.configure(text=f"{prefix} Přeložená zpráva...")
        else:
            self._prefix_preview.configure(text="Přeložená zpráva... (bez prefixu)")

    def _save_prefix(self):
        self._config["prefix_text"] = self._prefix_entry.get().strip()
        self._config["prefix_enabled"] = self._prefix_enabled_var.get()
        self._save_config()
        self._update_prefix_preview()

    # ─── SLOŽKY ─────────────────────────────────
    def _build_folders_tab(self, tab):
        t = self.theme
        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        _label(main, "Správa složek", 16, bold=True, color=t["primary"]).pack(anchor="w")

        for label, key, btn_label in [
            ("Zdrojová složka:", "source_dir", "📂 Otevřít"),
            ("Cílová složka:", "target_dir", "📂 Otevřít"),
        ]:
            card = ctk.CTkFrame(main, fg_color=t["card_bg"], corner_radius=int(t.get("radius_card", 14)))
            card.pack(fill="x", pady=6)
            _label(card, label, 12, bold=True, color=t["text_dim"]).pack(padx=12, pady=(10, 2), anchor="w")
            path = self._config.get(key, "Nezvoleno")
            _label(card, path or "Nezvoleno", 10, color=t["text"]).pack(padx=12, pady=(0, 6), anchor="w")
            ctk.CTkButton(card, text=btn_label, height=30, width=120,
                          fg_color=t["primary"], hover_color=t["primary_hover"],
                          command=lambda p=path: os.startfile(p) if p and os.path.isdir(p) else None
                          ).pack(padx=12, pady=(0, 10), anchor="w")

        _label(main, "Backup a čištění:", 12, bold=True, color=t["text"]).pack(anchor="w", pady=(16, 4))
        ctk.CTkButton(main, text="🗑 Vymazat cílové složky (přeložené soubory)",
                      fg_color="#8b2020", hover_color="#6b1818",
                      font=ctk.CTkFont("Segoe UI", 11), height=36,
                      command=self._clean_output).pack(fill="x")

    def _clean_output(self):
        tgt = self._config.get("target_dir", "")
        if not tgt or not os.path.isdir(tgt):
            messagebox.showwarning("Chyba", "Cílová složka není nastavena.")
            return
        if not messagebox.askyesno("Potvrdit", f"Vymazat obsah složky:\n{tgt}\n\nPokračovat?"):
            return
        count = 0
        for d in os.listdir(tgt):
            path = os.path.join(tgt, d)
            if os.path.isdir(path) and d in SUPPORTED_LANGS:
                import shutil
                shutil.rmtree(path)
                count += 1
        messagebox.showinfo("Hotovo", f"Odstraněno {count} jazykových složek.")
