"""
ZeddiHub Tools — Player Database module (admin-only).

Provides a cross-platform, searchable database of players aggregated from
one or more game-server MySQL databases. Source credentials are entered
by the admin in the UI; the local cache is Fernet-encrypted with a
machine-id-derived key (same scheme as auth.enc).

MySQL schema is auto-detected: the module scans candidate tables for
Name-like / IP-like / Connected-like columns and surfaces matches.
"""

import base64
import hashlib
import json
import os
import re
import threading
import time
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

try:
    import pymysql
    PYMYSQL_OK = True
except ImportError:
    pymysql = None
    PYMYSQL_OK = False

try:
    from gui import icons as _app_icons
except Exception:
    _app_icons = None


# ── constants ────────────────────────────────────────────────────────────────
NAME_COLS = {"name", "playername", "player_name", "username", "user_name",
             "displayname", "display_name", "nick", "nickname", "ign"}
IP_COLS = {"ip", "ipaddress", "ip_address", "lastip", "last_ip", "lastknownip"}
CONN_COLS = {"connected", "lastconnected", "last_connected", "lastseen",
             "last_seen", "lastlogin", "last_login", "joindate", "join_date",
             "created", "created_at", "updated_at"}
ID_COLS = {"steamid", "steam_id", "steamid64", "uid", "user_id", "userid",
           "player_id", "playerid", "id"}


# ── module paths ─────────────────────────────────────────────────────────────
def _data_dir() -> Path:
    try:
        from gui.config import get_data_dir
        d = get_data_dir() / "player_db"
    except Exception:
        d = Path.home() / "ZeddiHub.Tools.Data" / "player_db"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key() -> Optional[bytes]:
    if not CRYPTO_OK:
        return None
    try:
        import platform, uuid
        mid = str(uuid.getnode()) + platform.node()
    except Exception:
        mid = "zeddihub-player-db-fallback"
    return base64.urlsafe_b64encode(hashlib.sha256(mid.encode()).digest())


def _enc_write(path: Path, obj: Any):
    raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    k = _key()
    if not k:
        path.write_bytes(raw)
        return
    path.write_bytes(Fernet(k).encrypt(raw))


def _enc_read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    blob = path.read_bytes()
    k = _key()
    if k:
        try:
            blob = Fernet(k).decrypt(blob)
        except InvalidToken:
            pass  # legacy plaintext fallback
    try:
        return json.loads(blob.decode("utf-8"))
    except Exception:
        return default


def _sources_file() -> Path: return _data_dir() / "sources.enc"
def _cache_file() -> Path:   return _data_dir() / "cache.enc"
def _notes_file() -> Path:   return _data_dir() / "notes.enc"


# ── MySQL ingestion ──────────────────────────────────────────────────────────
def _detect_columns(cols: list[str]) -> dict:
    """Return {'name', 'ip', 'connected', 'ids': [...]} — lowercase-matched."""
    lc = {c.lower(): c for c in cols}
    out = {"name": None, "ip": None, "connected": None, "ids": []}
    for low, orig in lc.items():
        if low in NAME_COLS and not out["name"]:
            out["name"] = orig
        if low in IP_COLS and not out["ip"]:
            out["ip"] = orig
        if low in CONN_COLS and not out["connected"]:
            out["connected"] = orig
        if low in ID_COLS:
            out["ids"].append(orig)
    return out


def _ingest_source(source: dict, progress: Callable[[str], None]) -> list[dict]:
    """Connect to MySQL, auto-detect player tables, return list of records."""
    if not PYMYSQL_OK:
        raise RuntimeError("pymysql není nainstalován — modul vyžaduje pymysql.")
    conn = pymysql.connect(
        host=source["host"], port=int(source.get("port", 3306)),
        user=source["user"], password=source["password"],
        database=source["database"], charset="utf8mb4",
        connect_timeout=8, read_timeout=30,
    )
    records = []
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            tables = [r[0] for r in cur.fetchall()]
            for tbl in tables:
                try:
                    cur.execute(f"SHOW COLUMNS FROM `{tbl}`")
                    cols = [r[0] for r in cur.fetchall()]
                except Exception:
                    continue
                det = _detect_columns(cols)
                if not det["name"]:
                    continue
                progress(f"Skenuji {tbl}…")
                select_cols = [det["name"]]
                if det["ip"]: select_cols.append(det["ip"])
                if det["connected"]: select_cols.append(det["connected"])
                select_cols += det["ids"]
                col_sql = ", ".join(f"`{c}`" for c in select_cols)
                try:
                    cur.execute(f"SELECT {col_sql} FROM `{tbl}` LIMIT 50000")
                    rows = cur.fetchall()
                except Exception as e:
                    progress(f"  ! {tbl}: {e}")
                    continue
                for row in rows:
                    rec = {"_source": source["label"], "_table": tbl}
                    rec["name"] = str(row[0]) if row[0] is not None else ""
                    idx = 1
                    if det["ip"]:
                        rec["ip"] = str(row[idx]) if row[idx] is not None else ""
                        idx += 1
                    if det["connected"]:
                        rec["connected"] = str(row[idx]) if row[idx] is not None else ""
                        idx += 1
                    for id_col in det["ids"]:
                        rec[id_col.lower()] = str(row[idx]) if row[idx] is not None else ""
                        idx += 1
                    if rec["name"]:
                        records.append(rec)
    finally:
        try: conn.close()
        except Exception: pass
    return records


# ── web sync (bearer-token REST) ─────────────────────────────────────────────
def _push_to_web(api_url: str, token: str, records: list[dict],
                 progress: Callable[[str], None]) -> int:
    req = urllib.request.Request(
        api_url, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ZeddiHubTools-PlayerDB/1.0",
        },
        data=json.dumps({"records": records}).encode("utf-8"),
    )
    progress(f"Odesílám {len(records)} záznamů…")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return int(body.get("ingested", 0))


# ── panel ────────────────────────────────────────────────────────────────────
class PlayerDBPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme.get("content_bg", "#0b0b12"), **kwargs)
        self.theme = theme
        self._sources = _enc_read(_sources_file(), default=[]) or []
        self._cache = _enc_read(_cache_file(), default={"records": [], "at": 0}) or {"records": [], "at": 0}
        self._notes = _enc_read(_notes_file(), default={}) or {}  # key → {nickname, note}
        self._web = _enc_read(_data_dir() / "web.enc", default={}) or {}
        self._search_var = ctk.StringVar()
        self._busy = False
        self._build()
        self._render_list()

    # ── layout ────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme
        primary = th.get("primary", "#f0a500")
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        card_bg = th.get("card_bg", "#1a1a26")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            header, text="Player Database",
            font=ctk.CTkFont("Segoe UI", 22, "bold"), text_color=text,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Admin-only — MySQL ingesce, šifrovaná cache, cross-platform přístup.",
            font=ctk.CTkFont("Segoe UI", 11), text_color=text_dim,
        ).pack(anchor="w")

        tabs = ctk.CTkTabview(
            self, fg_color=th.get("content_bg", "#0b0b12"),
            segmented_button_fg_color=card_bg,
            segmented_button_selected_color=primary,
            segmented_button_selected_hover_color=th.get("primary_hover", primary),
            segmented_button_unselected_color=card_bg,
            text_color=text,
        )
        tabs.pack(fill="both", expand=True, padx=16, pady=(10, 16))

        self._tab_search = tabs.add("Hledat")
        self._tab_sources = tabs.add("Zdroje")
        self._tab_sync = tabs.add("Sync")
        self._tab_about = tabs.add("O modulu")

        self._build_search_tab(self._tab_search)
        self._build_sources_tab(self._tab_sources)
        self._build_sync_tab(self._tab_sync)
        self._build_about_tab(self._tab_about)

    # ── search tab ────────────────────────────────────────────────────────
    def _build_search_tab(self, tab):
        th = self.theme
        card_bg = th.get("card_bg", "#1a1a26")
        text = th.get("text", "#fff")
        primary = th.get("primary", "#f0a500")

        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=(10, 6))
        entry = ctk.CTkEntry(
            bar, textvariable=self._search_var,
            placeholder_text="🔍  Hledat jméno, IP, SteamID…",
            fg_color=card_bg, border_width=1,
            border_color=th.get("border", "#2a2a36"),
            text_color=text, height=36, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 11),
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        entry.bind("<KeyRelease>", lambda _e: self._render_list())

        self._status_lbl = ctk.CTkLabel(
            tab, text="", font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("text_dim", "#888"),
        )
        self._status_lbl.pack(anchor="w", padx=12, pady=(0, 6))

        self._list_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 10))

    def _render_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        q = (self._search_var.get() or "").strip().lower()
        records = self._cache.get("records", [])
        if q:
            records = [r for r in records if self._match(r, q)]
        records = records[:500]

        at = self._cache.get("at", 0)
        ts = time.strftime("%d.%m.%Y %H:%M", time.localtime(at)) if at else "—"
        self._status_lbl.configure(
            text=f"Cache: {len(self._cache.get('records', []))} záznamů  ·  poslední sync: {ts}"
        )

        if not records:
            ctk.CTkLabel(
                self._list_frame,
                text="Žádné záznamy. Přidejte MySQL zdroj v záložce 'Zdroje'.",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=self.theme.get("text_dim", "#888"),
            ).pack(pady=40)
            return

        # Aggregate by name
        by_name: dict[str, list[dict]] = {}
        for r in records:
            by_name.setdefault(r.get("name", ""), []).append(r)

        for name, hits in sorted(by_name.items(), key=lambda kv: kv[0].lower()):
            self._render_profile_card(name, hits)

    def _match(self, rec: dict, q: str) -> bool:
        for v in rec.values():
            if isinstance(v, str) and q in v.lower():
                return True
        return False

    def _render_profile_card(self, name: str, hits: list[dict]):
        th = self.theme
        card_bg = th.get("card_bg", "#1a1a26")
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")
        border = th.get("border", "#2a2a36")

        notes = self._notes.get(name.lower(), {})
        card = ctk.CTkFrame(
            self._list_frame, fg_color=card_bg, corner_radius=12,
            border_width=1, border_color=border,
        )
        card.pack(fill="x", padx=8, pady=4)

        row = tk.Frame(card, bg=card_bg, bd=0, highlightthickness=0)
        row.pack(fill="x", padx=12, pady=10)

        left = tk.Frame(row, bg=card_bg, bd=0, highlightthickness=0)
        left.pack(side="left", fill="both", expand=True)

        title = name + (f"  ({notes.get('nickname')})" if notes.get("nickname") else "")
        ctk.CTkLabel(
            left, text=title, fg_color=card_bg,
            font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=text,
        ).pack(anchor="w")

        ips = sorted({h.get("ip", "") for h in hits if h.get("ip")})
        sids = sorted({v for h in hits for k, v in h.items()
                       if k.startswith("steam") and v})
        sources = sorted({h.get("_source", "") for h in hits})
        meta = f"{len(hits)} záznamů  ·  {len(sources)} zdrojů"
        if ips: meta += f"  ·  IP: {', '.join(ips[:2])}"
        if sids: meta += f"  ·  SteamID: {sids[0]}"
        ctk.CTkLabel(
            left, text=meta, fg_color=card_bg,
            font=ctk.CTkFont("Segoe UI", 10), text_color=text_dim,
        ).pack(anchor="w", pady=(2, 0))
        if notes.get("note"):
            ctk.CTkLabel(
                left, text=f"📝  {notes['note']}", fg_color=card_bg,
                font=ctk.CTkFont("Segoe UI", 10), text_color=primary,
                wraplength=600, justify="left",
            ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            row, text="Detail",
            fg_color=primary, hover_color=th.get("primary_hover", primary),
            text_color="#000", width=90, height=30, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            command=lambda n=name, h=hits: self._open_profile(n, h),
        ).pack(side="right")

    def _open_profile(self, name: str, hits: list[dict]):
        top = ctk.CTkToplevel(self)
        top.title(f"Profil: {name}")
        top.geometry("720x560")
        top.configure(fg_color=self.theme.get("content_bg", "#0b0b12"))

        th = self.theme
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")
        card_bg = th.get("card_bg", "#1a1a26")

        head = ctk.CTkFrame(top, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            head, text=name, text_color=text,
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        # Admin notes/nickname
        notes = dict(self._notes.get(name.lower(), {}))
        nick_var = ctk.StringVar(value=notes.get("nickname", ""))
        note_var = ctk.StringVar(value=notes.get("note", ""))

        form = ctk.CTkFrame(top, fg_color=card_bg, corner_radius=10)
        form.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(form, text="Přezdívka (admin):", text_color=text_dim,
                     font=ctk.CTkFont("Segoe UI", 10)).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkEntry(form, textvariable=nick_var, fg_color=th.get("input_bg", "#0f0f18"),
                     border_width=1, text_color=text, height=30,
                     ).pack(fill="x", padx=10, pady=(2, 6))
        ctk.CTkLabel(form, text="Poznámka admina:", text_color=text_dim,
                     font=ctk.CTkFont("Segoe UI", 10)).pack(anchor="w", padx=10)
        ctk.CTkEntry(form, textvariable=note_var, fg_color=th.get("input_bg", "#0f0f18"),
                     border_width=1, text_color=text, height=30,
                     ).pack(fill="x", padx=10, pady=(2, 6))

        def _save():
            self._notes[name.lower()] = {
                "nickname": nick_var.get().strip(),
                "note": note_var.get().strip(),
            }
            _enc_write(_notes_file(), self._notes)
            self._render_list()
            top.destroy()

        ctk.CTkButton(form, text="Uložit poznámku", fg_color=primary,
                      text_color="#000", command=_save, height=30,
                      ).pack(anchor="e", padx=10, pady=(0, 8))

        # All records table
        ctk.CTkLabel(top, text=f"Všechny záznamy ({len(hits)})",
                     text_color=text_dim,
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     ).pack(anchor="w", padx=16, pady=(8, 4))
        tbl = ctk.CTkScrollableFrame(top, fg_color="transparent")
        tbl.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for h in hits:
            row = ctk.CTkFrame(tbl, fg_color=card_bg, corner_radius=8)
            row.pack(fill="x", padx=4, pady=3)
            line = f"{h.get('_source', '?')} / {h.get('_table', '?')}"
            if h.get("ip"): line += f"  ·  {h['ip']}"
            if h.get("connected"): line += f"  ·  {h['connected']}"
            ids = [f"{k}={v}" for k, v in h.items()
                   if k.startswith(("steam", "player_id", "user_id", "uid")) and v]
            if ids: line += "  ·  " + ", ".join(ids[:3])
            ctk.CTkLabel(row, text=line, text_color=text,
                         font=ctk.CTkFont("Consolas", 10),
                         ).pack(anchor="w", padx=10, pady=6)

    # ── sources tab ───────────────────────────────────────────────────────
    def _build_sources_tab(self, tab):
        th = self.theme
        card_bg = th.get("card_bg", "#1a1a26")
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")

        if not PYMYSQL_OK:
            ctk.CTkLabel(
                tab,
                text="⚠  Balíček pymysql není nainstalován. Modul vyžaduje pymysql\n"
                     "    (pip install pymysql) nebo bude fungovat jen offline cache.",
                text_color=th.get("warning", "#f5a623"),
                font=ctk.CTkFont("Segoe UI", 11),
                justify="left",
            ).pack(pady=10, padx=12, anchor="w")

        ctk.CTkLabel(
            tab, text="Zdroje MySQL databází",
            text_color=text, font=ctk.CTkFont("Segoe UI", 14, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            tab, text="Přidejte přístupové údaje k herním databázím. Sloupce Name / IP /\n"
                     "Connected se detekují automaticky.",
            text_color=text_dim, font=ctk.CTkFont("Segoe UI", 10), justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        self._src_list = ctk.CTkFrame(tab, fg_color="transparent")
        self._src_list.pack(fill="x", padx=8, pady=4)
        self._render_sources()

        ctk.CTkButton(
            tab, text="+  Přidat zdroj",
            fg_color=primary, text_color="#000",
            hover_color=th.get("primary_hover", primary),
            height=34, corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            command=lambda: self._edit_source(None),
        ).pack(anchor="w", padx=12, pady=(8, 0))

    def _render_sources(self):
        for w in self._src_list.winfo_children():
            w.destroy()
        th = self.theme
        card_bg = th.get("card_bg", "#1a1a26")
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")

        if not self._sources:
            ctk.CTkLabel(
                self._src_list, text="Žádné zdroje.",
                text_color=text_dim, font=ctk.CTkFont("Segoe UI", 10),
            ).pack(pady=10)
            return

        for i, s in enumerate(self._sources):
            row = ctk.CTkFrame(self._src_list, fg_color=card_bg, corner_radius=10)
            row.pack(fill="x", padx=4, pady=3)
            info = f"{s.get('label', '?')}  ·  {s.get('host', '')}:{s.get('port', 3306)}/{s.get('database', '')}"
            ctk.CTkLabel(row, text=info, text_color=text,
                         font=ctk.CTkFont("Segoe UI", 11),
                         ).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(row, text="Upravit", width=70, height=26, corner_radius=6,
                          fg_color="transparent", border_width=1,
                          border_color=th.get("border", "#2a2a36"),
                          text_color=text_dim,
                          command=lambda idx=i: self._edit_source(idx),
                          ).pack(side="right", padx=4, pady=6)
            ctk.CTkButton(row, text="Smazat", width=70, height=26, corner_radius=6,
                          fg_color="transparent", border_width=1,
                          border_color=th.get("border", "#2a2a36"),
                          text_color="#e57373", hover_color="#8b2020",
                          command=lambda idx=i: self._delete_source(idx),
                          ).pack(side="right", padx=4, pady=6)

    def _edit_source(self, idx: Optional[int]):
        src = dict(self._sources[idx]) if idx is not None else {}
        dlg = ctk.CTkToplevel(self)
        dlg.title("MySQL zdroj")
        dlg.geometry("480x460")
        dlg.configure(fg_color=self.theme.get("content_bg", "#0b0b12"))
        dlg.transient(self.winfo_toplevel())

        vars_ = {
            "label":    ctk.StringVar(value=src.get("label", "")),
            "host":     ctk.StringVar(value=src.get("host", "")),
            "port":     ctk.StringVar(value=str(src.get("port", 3306))),
            "user":     ctk.StringVar(value=src.get("user", "")),
            "password": ctk.StringVar(value=src.get("password", "")),
            "database": ctk.StringVar(value=src.get("database", "")),
        }
        for key, label in [
            ("label", "Název (např. CS2 Servery)"),
            ("host", "Host"),
            ("port", "Port"),
            ("user", "Uživatel"),
            ("password", "Heslo"),
            ("database", "Databáze"),
        ]:
            ctk.CTkLabel(dlg, text=label, text_color=self.theme.get("text_dim", "#888"),
                         font=ctk.CTkFont("Segoe UI", 10),
                         ).pack(anchor="w", padx=16, pady=(8, 0))
            ctk.CTkEntry(dlg, textvariable=vars_[key],
                         show="*" if key == "password" else "",
                         height=32,
                         ).pack(fill="x", padx=16, pady=(2, 0))

        def _save():
            new = {k: v.get().strip() for k, v in vars_.items()}
            try:
                new["port"] = int(new["port"] or "3306")
            except ValueError:
                new["port"] = 3306
            if not new["label"] or not new["host"] or not new["database"]:
                return
            if idx is None:
                self._sources.append(new)
            else:
                self._sources[idx] = new
            _enc_write(_sources_file(), self._sources)
            self._render_sources()
            dlg.destroy()

        ctk.CTkButton(
            dlg, text="Uložit",
            fg_color=self.theme.get("primary", "#f0a500"), text_color="#000",
            height=34, corner_radius=10, command=_save,
        ).pack(pady=16)

    def _delete_source(self, idx: int):
        if 0 <= idx < len(self._sources):
            self._sources.pop(idx)
            _enc_write(_sources_file(), self._sources)
            self._render_sources()

    # ── sync tab ──────────────────────────────────────────────────────────
    def _build_sync_tab(self, tab):
        th = self.theme
        card_bg = th.get("card_bg", "#1a1a26")
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        primary = th.get("primary", "#f0a500")

        ctk.CTkLabel(tab, text="Stáhnout ze zdrojů",
                     text_color=text, font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     ).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(tab,
                     text="Načte záznamy ze všech MySQL zdrojů a uloží je do lokální šifrované cache.",
                     text_color=text_dim, font=ctk.CTkFont("Segoe UI", 10), justify="left",
                     ).pack(anchor="w", padx=12, pady=(0, 8))
        ctk.CTkButton(
            tab, text="⤓  Stáhnout z MySQL",
            fg_color=primary, text_color="#000", height=34,
            hover_color=th.get("primary_hover", primary), corner_radius=10,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            command=self._do_ingest,
        ).pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkLabel(tab, text="Cloud sync (bearer token)",
                     text_color=text, font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     ).pack(anchor="w", padx=12, pady=(14, 4))

        web = self._web
        self._api_var = ctk.StringVar(value=web.get("api",
            "https://zeddihub.eu/tools/admin/api/player_db.php"))
        self._token_var = ctk.StringVar(value=web.get("token", ""))
        for label, var, show in [
            ("API URL", self._api_var, ""),
            ("Bearer token", self._token_var, "*"),
        ]:
            ctk.CTkLabel(tab, text=label, text_color=text_dim,
                         font=ctk.CTkFont("Segoe UI", 10),
                         ).pack(anchor="w", padx=12, pady=(4, 0))
            ctk.CTkEntry(tab, textvariable=var, height=30, show=show,
                         ).pack(fill="x", padx=12, pady=(2, 4))

        btns = ctk.CTkFrame(tab, fg_color="transparent")
        btns.pack(fill="x", padx=12, pady=(6, 10))
        ctk.CTkButton(btns, text="Uložit nastavení", fg_color=card_bg,
                      text_color=text, border_width=1,
                      border_color=th.get("border", "#2a2a36"),
                      height=30, corner_radius=8,
                      command=self._save_web_cfg,
                      ).pack(side="left")
        ctk.CTkButton(btns, text="⤒  Nahrát cache do cloudu",
                      fg_color=primary, text_color="#000", height=30, corner_radius=8,
                      command=self._do_push_web,
                      ).pack(side="left", padx=(6, 0))

        self._sync_log = ctk.CTkTextbox(
            tab, fg_color=card_bg, text_color=text,
            font=ctk.CTkFont("Consolas", 10), height=120, corner_radius=8,
        )
        self._sync_log.pack(fill="both", expand=True, padx=12, pady=(6, 12))
        self._log("Připraveno.")

    def _log(self, msg: str):
        try:
            self._sync_log.insert("end", f"{time.strftime('%H:%M:%S')}  {msg}\n")
            self._sync_log.see("end")
        except Exception:
            pass

    def _save_web_cfg(self):
        self._web = {"api": self._api_var.get().strip(),
                     "token": self._token_var.get().strip()}
        _enc_write(_data_dir() / "web.enc", self._web)
        self._log("✓ Nastavení cloudu uloženo.")

    def _do_ingest(self):
        if self._busy or not PYMYSQL_OK:
            return
        if not self._sources:
            self._log("! Žádné zdroje. Přidejte je v záložce Zdroje.")
            return
        self._busy = True

        def _worker():
            all_records = []
            def _p(m): self.after(0, self._log, m)
            for src in self._sources:
                _p(f"→ {src['label']} ({src['host']})")
                try:
                    recs = _ingest_source(src, _p)
                    _p(f"  ✓ {len(recs)} záznamů")
                    all_records.extend(recs)
                except Exception as e:
                    _p(f"  ! {e}")
            self._cache = {"records": all_records, "at": int(time.time())}
            _enc_write(_cache_file(), self._cache)
            self.after(0, self._render_list)
            self.after(0, self._log, f"✓ Sync hotový: {len(all_records)} celkem.")
            self._busy = False

        threading.Thread(target=_worker, daemon=True).start()

    def _do_push_web(self):
        if self._busy:
            return
        api = self._api_var.get().strip()
        token = self._token_var.get().strip()
        if not api or not token:
            self._log("! Vyplňte API URL a bearer token.")
            return
        records = self._cache.get("records", [])
        if not records:
            self._log("! Cache je prázdná. Nejdřív stáhněte z MySQL.")
            return
        self._busy = True

        def _worker():
            def _p(m): self.after(0, self._log, m)
            try:
                n = _push_to_web(api, token, records, _p)
                _p(f"✓ Cloud přijal {n} záznamů.")
            except urllib.error.HTTPError as e:
                _p(f"! HTTP {e.code}: {e.reason}")
            except Exception as e:
                _p(f"! {e}")
            self._busy = False

        threading.Thread(target=_worker, daemon=True).start()

    # ── about tab ─────────────────────────────────────────────────────────
    def _build_about_tab(self, tab):
        th = self.theme
        text = th.get("text", "#fff")
        text_dim = th.get("text_dim", "#888")
        ctk.CTkLabel(tab, text="Player Database v1.0.0",
                     text_color=text, font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     ).pack(anchor="w", padx=12, pady=(12, 4))
        about = (
            "Admin-only modul pro agregaci záznamů hráčů z více herních MySQL\n"
            "databází.\n\n"
            "• Auto-detekce sloupců Name / IP / Connected / SteamID / ID.\n"
            "• Lokální Fernet-šifrovaná cache (machine-id klíč).\n"
            "• Cloud sync přes REST API s bearer tokenem → sdílení\n"
            "  mezi desktopem, webem a mobilem.\n"
            "• Admin poznámky a přezdívky k jednotlivým hráčům.\n"
            "• Propojení účtů (budoucí verze).\n"
        )
        ctk.CTkLabel(tab, text=about, text_color=text_dim,
                     font=ctk.CTkFont("Segoe UI", 10), justify="left",
                     ).pack(anchor="w", padx=12, pady=(0, 10))
