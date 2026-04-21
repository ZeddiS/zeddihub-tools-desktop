"""
ZeddiHub Server Updater — integrated module panel.

Admin-only module. Monitors four classes of server-side updates:
  1) Game builds (Steam Web API)
  2) Oxide / uMod for Rust
  3) MetaMod + SourceMod + CounterStrikeSharp for CS2/CS:GO
  4) Per-plugin GitHub Releases

Configuration lives at <data_dir>/server_updater.json. Checks run in
background threads; UI is notify-first, manual or automatic apply.
"""

import json
import threading
import time
from pathlib import Path
from typing import Optional

import customtkinter as ctk


# ── Host-app integration (best-effort) ────────────────────────────────────
# When loaded by the main app, `from gui ...` works and gives us the real
# icon renderer / data dir / admin check. When loaded standalone (dev), we
# fall back to sensible defaults so the panel still renders.
try:
    from gui import icons  # type: ignore
except Exception:
    icons = None

try:
    from gui.config import get_data_dir  # type: ignore
except Exception:
    def get_data_dir() -> Path:
        return Path.home() / "AppData" / "Local" / "ZeddiHub"

try:
    from gui.auth import is_admin  # type: ignore
except Exception:
    def is_admin() -> bool:
        return True  # standalone dev mode → allow


# ── Update sources (bundled in this module) ──────────────────────────────
try:
    # When loaded via spec_from_file_location, the module's directory is
    # added to sys.path by external_tools.load_module, so this top-level
    # absolute import resolves to modules/server-updater/update_sources/.
    from update_sources import SOURCES, UpdateResult  # type: ignore
except Exception:
    SOURCES = {}
    class UpdateResult:  # minimal stub so _render_rows doesn't crash
        def __init__(self):
            self.update_available = False
            self.latest_version = None
            self.current_version = None
            self.error = None
            self.url = None


# ── Config ────────────────────────────────────────────────────────────────
MODULE_NAME    = "Server Updater"
MODULE_VERSION = "1.0.0"

DEFAULT_CONFIG = {
    "interval_minutes": 30,
    "auto_apply": False,
    "targets": [
        {"source": "game_builds",    "target": "rust",      "current": None},
        {"source": "game_builds",    "target": "cs2",       "current": None},
        {"source": "umod_rust",      "target": "rust",      "current": None},
        {"source": "sourcemod_cs",   "target": "metamod",   "current": None},
        {"source": "sourcemod_cs",   "target": "sourcemod", "current": None},
        {"source": "sourcemod_cs",   "target": "cssharp",   "current": None},
    ],
}


def _config_path() -> Path:
    return get_data_dir() / "server_updater.json"


def load_config() -> dict:
    p = _config_path()
    if not p.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(p, encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ── Panel ─────────────────────────────────────────────────────────────────
class ServerUpdaterPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme.get("content_bg", "#0a0a0f"),
                         **kwargs)
        self.theme = theme
        self._cfg = load_config()
        self._results: dict = {}
        self._polling = False

        if not is_admin():
            self._build_locked()
            return

        self._build()
        self.after(300, self._check_all_async)

    def _build_locked(self):
        th = self.theme
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True)
        ctk.CTkLabel(
            wrap, text="🔒  Server Updater",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=th.get("text", "#fff"),
        ).pack(pady=(80, 8))
        ctk.CTkLabel(
            wrap,
            text="Tento modul je dostupný pouze uživatelům s rolí Admin.",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_dim", "#888"),
        ).pack()

    def _build(self):
        th = self.theme
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(
            header, text="Server Updater",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=th.get("text", "#fff"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Vzdálený monitoring: game builds · Oxide · MetaMod/SourceMod · GitHub pluginy.",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=th.get("text_dim", "#888"),
        ).pack(anchor="w")

        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(anchor="w", pady=(10, 0))
        ctk.CTkButton(
            toolbar, text="Zkontrolovat nyní",
            fg_color=th.get("primary", "#f0a500"),
            hover_color=th.get("primary_hover", "#d4900a"),
            text_color="#000", width=160, height=32,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            command=self._check_all_async,
        ).pack(side="left", padx=(0, 8))
        self._auto_var = ctk.BooleanVar(value=self._cfg.get("auto_apply", False))
        ctk.CTkSwitch(
            toolbar, text="Automaticky aplikovat",
            variable=self._auto_var,
            command=self._toggle_auto,
            fg_color=th.get("secondary", "#333"),
            progress_color=th.get("primary", "#f0a500"),
            font=ctk.CTkFont("Segoe UI", 11),
        ).pack(side="left", padx=(8, 0))

        self._status = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_dim", "#888"),
        )
        self._status.pack(anchor="w", pady=(6, 0))

        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.pack(fill="both", expand=True, padx=24, pady=(4, 20))
        self._render_rows()

    def _toggle_auto(self):
        self._cfg["auto_apply"] = bool(self._auto_var.get())
        save_config(self._cfg)

    def _render_rows(self):
        for child in self._list.winfo_children():
            child.destroy()
        th = self.theme
        for entry in self._cfg.get("targets", []):
            src_id = entry.get("source")
            target = entry.get("target", "")
            key = f"{src_id}:{target}"
            source = SOURCES.get(src_id)
            res: Optional[UpdateResult] = self._results.get(key)

            card = ctk.CTkFrame(self._list, fg_color=th.get("card_bg", "#1a1a26"),
                                corner_radius=14)
            card.pack(fill="x", pady=6)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            label = source.label if source else src_id
            ctk.CTkLabel(
                info, text=f"{label} · {target}",
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                text_color=th.get("text", "#fff"),
            ).pack(anchor="w")

            if res is None:
                status_text, color = "⏳ Čeká na kontrolu...", th.get("text_dim", "#888")
            elif res.error:
                status_text, color = f"! {res.error}", th.get("error", "#ef4444")
            elif res.update_available:
                status_text = f"● Nová verze: {res.latest_version}  (aktuální: {res.current_version or '?'})"
                color = th.get("warning", "#f59e0b")
            else:
                status_text = f"✓ Aktuální: {res.latest_version or '—'}"
                color = th.get("success", "#22c55e")
            ctk.CTkLabel(
                info, text=status_text,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=color,
            ).pack(anchor="w", pady=(2, 0))

            if res and getattr(res, "url", None):
                btn = ctk.CTkButton(
                    row, text="Otevřít", width=80, height=28,
                    fg_color=th.get("secondary", "#333"),
                    hover_color=th.get("primary", "#f0a500"),
                    font=ctk.CTkFont("Segoe UI", 10),
                    command=lambda u=res.url: _open_url(u),
                )
                btn.pack(side="right")

    def _check_all_async(self):
        if self._polling:
            return
        self._polling = True
        self._status.configure(text="⏳ Kontrola...")

        def _run():
            for entry in self._cfg.get("targets", []):
                src_id = entry.get("source")
                target = entry.get("target", "")
                current = entry.get("current")
                source = SOURCES.get(src_id)
                if not source:
                    continue
                try:
                    res = source.check(target, current)
                except Exception as e:
                    try:
                        from update_sources.base import UpdateResult as _R
                        res = _R(src_id, target, None, current, False, error=str(e))
                    except Exception:
                        res = None
                self._results[f"{src_id}:{target}"] = res
                self.after(0, self._render_rows)
            self.after(0, lambda: self._status.configure(
                text=f"✓ Kontrola dokončena: {time.strftime('%H:%M:%S')}"))
            self._polling = False

        threading.Thread(target=_run, daemon=True).start()


def _open_url(url: str):
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass
