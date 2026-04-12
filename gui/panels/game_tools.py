"""
ZeddiHub Tools - Herní Nástroje panel.
Tabs: Translator | Sensitivity Converter | eDPI Kalkulačka | Ping Tester
"""

import socket
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
import tkinter as tk
import customtkinter as ctk
from pathlib import Path

try:
    from ..locale import t
    from .. import icons
except ImportError:
    def t(k, **kw): return k
    class icons:
        @staticmethod
        def icon(*a, **kw): return None


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
        text_color=color or "#f0f0f0", **kw)


def _card(parent, theme):
    return ctk.CTkFrame(parent, fg_color=theme["card_bg"], corner_radius=8)


# ──────────────────────────────────────────────────────────────────────────────
# Sensitivity multipliers: how many in-game units equal 1 degree of rotation.
# Formula: cm_per_360 = 36000 / (dpi * sens * mult)
# ──────────────────────────────────────────────────────────────────────────────
SENS_GAMES: dict[str, float] = {
    "CS2 / CS:GO":         0.022,
    "Rust":                0.1,
    "Valorant":            0.07,
    "Apex Legends":        0.022,
    "Overwatch 2":         0.0066,
    "Rainbow Six Siege":   0.00572957795,
    "PUBG":                0.00571428571,
    "Fortnite":            0.05555555556,
    "Battlefield 2042":    0.022,
    "Quake / Source":      0.022,
    "Team Fortress 2":     0.022,
    "Left 4 Dead 2":       0.022,
    "Hunt: Showdown":      0.03333333333,
    "Escape From Tarkov":  0.03,
    "DayZ":                0.09090909091,
    "ARMA 3":              0.01,
    "Splitgate":           0.022,
    "Halo Infinite":       0.0182,
    "Destiny 2":           0.0166666667,
    "The Finals":          0.022,
}

# Gaming server endpoints for ping test
PING_SERVERS: list[tuple[str, str, int]] = [
    ("Valve (CS2/TF2)",         "sto.steampowered.com",       443),
    ("Valve (EU Amsterdam)",    "ams.steampowered.com",        27019),
    ("Cloudflare DNS",          "1.1.1.1",                     53),
    ("Google DNS",              "8.8.8.8",                     53),
    ("Riot Games (EU)",         "euw.op.gg",                   443),
    ("Ubisoft (EU)",            "ubisoft.com",                 443),
    ("Epic Games (Fortnite)",   "epicgames.com",               443),
    ("Bungie (Destiny 2)",      "bungie.net",                  443),
    ("Faceit EU",               "www.faceit.com",              443),
    ("PingTest",                "speed.cloudflare.com",        443),
]


class GameToolsPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        th = self.theme
        tab = ctk.CTkTabview(self, fg_color=th["sidebar_bg"])
        tab.pack(fill="both", expand=True, padx=12, pady=12)

        tab.add("🌐 " + t("translator"))
        tab.add("🎯 Sensitivity")
        tab.add("📐 eDPI")
        tab.add("📡 Ping Tester")

        # Lazy-load translator (heavy build, only when tab is opened)
        translator_tab = tab.tab("🌐 " + t("translator"))
        self._translator_frame = ctk.CTkFrame(translator_tab, fg_color="transparent")
        self._translator_frame.pack(fill="both", expand=True)
        self._translator_loaded = False
        tab.configure(command=lambda: self._on_tab_change(tab))

        self._build_sensitivity(tab.tab("🎯 Sensitivity"))
        self._build_edpi(tab.tab("📐 eDPI"))
        self._build_ping(tab.tab("📡 Ping Tester"))

        # Load translator immediately (it's the default tab)
        self.after(50, self._ensure_translator)

    def _on_tab_change(self, tab_widget):
        name = tab_widget.get()
        if ("translator" in name.lower() or "🌐" in name) and not self._translator_loaded:
            self._ensure_translator()

    def _ensure_translator(self):
        if self._translator_loaded:
            return
        try:
            from .translator import TranslatorPanel
            tp = TranslatorPanel(self._translator_frame, theme=self.theme)
            tp.pack(fill="both", expand=True)
            self._translator_loaded = True
        except Exception as e:
            _label(self._translator_frame,
                   f"Chyba při načítání překladače:\n{e}",
                   12, color=self.theme["error"]).pack(pady=40)

    # ── SENSITIVITY CONVERTER ─────────────────────────────────────────────────

    def _build_sensitivity(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "🎯 Sensitivity Converter", 16, bold=True, color=th["primary"],
               image=icons.icon("crosshairs", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 4), anchor="w")
        _label(scroll, "Převede citlivost myši mezi hrami. Zachová stejné fyzické pohyby (cm/360°).",
               11, color=th["text_dim"]
               ).pack(padx=4, pady=(0, 12), anchor="w")

        game_names = list(SENS_GAMES.keys())

        # ── Input card ────────────────────────────────────────────────────────
        inp_card = _card(scroll, th)
        inp_card.pack(fill="x", pady=6)

        _label(inp_card, "Zdrojová hra", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        src_row = ctk.CTkFrame(inp_card, fg_color="transparent")
        src_row.pack(fill="x", padx=14, pady=(0, 8))

        self._src_game_var = ctk.StringVar(value="CS2 / CS:GO")
        ctk.CTkOptionMenu(
            src_row, variable=self._src_game_var,
            values=game_names,
            fg_color=th["secondary"], button_color=th["primary"],
            button_hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 12), height=36, width=200,
            command=lambda _: self._recalc_sens()
        ).pack(side="left", padx=(0, 12))

        _label(src_row, "Sensitivity:", 11, color=th["text_dim"]).pack(side="left", padx=(0, 6))
        self._src_sens_var = ctk.StringVar(value="1.0")
        sens_entry = ctk.CTkEntry(src_row, textvariable=self._src_sens_var,
                                  fg_color=th["secondary"], text_color=th["text"],
                                  font=ctk.CTkFont("Segoe UI", 13), height=36, width=90)
        sens_entry.pack(side="left", padx=(0, 12))
        self._src_sens_var.trace_add("write", lambda *_: self._recalc_sens())

        _label(src_row, "DPI:", 11, color=th["text_dim"]).pack(side="left", padx=(0, 6))
        self._src_dpi_var = ctk.StringVar(value="800")
        ctk.CTkEntry(src_row, textvariable=self._src_dpi_var,
                     fg_color=th["secondary"], text_color=th["text"],
                     font=ctk.CTkFont("Segoe UI", 13), height=36, width=80
                     ).pack(side="left")
        self._src_dpi_var.trace_add("write", lambda *_: self._recalc_sens())

        # cm/360 display
        self._cm360_var = ctk.StringVar(value="")
        _label(inp_card, "", 11, color=th["text_dim"], textvariable=self._cm360_var
               ).pack(padx=14, pady=(0, 12), anchor="w")

        # ── Output card ───────────────────────────────────────────────────────
        out_card = _card(scroll, th)
        out_card.pack(fill="x", pady=6)

        _label(out_card, "Cílová hra", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        dst_row = ctk.CTkFrame(out_card, fg_color="transparent")
        dst_row.pack(fill="x", padx=14, pady=(0, 8))

        self._dst_game_var = ctk.StringVar(value="Valorant")
        ctk.CTkOptionMenu(
            dst_row, variable=self._dst_game_var,
            values=game_names,
            fg_color=th["secondary"], button_color=th["primary"],
            button_hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 12), height=36, width=200,
            command=lambda _: self._recalc_sens()
        ).pack(side="left", padx=(0, 12))

        _label(dst_row, "Target DPI:", 11, color=th["text_dim"]).pack(side="left", padx=(0, 6))
        self._dst_dpi_var = ctk.StringVar(value="800")
        ctk.CTkEntry(dst_row, textvariable=self._dst_dpi_var,
                     fg_color=th["secondary"], text_color=th["text"],
                     font=ctk.CTkFont("Segoe UI", 13), height=36, width=80
                     ).pack(side="left")
        self._dst_dpi_var.trace_add("write", lambda *_: self._recalc_sens())

        # Result
        result_card = _card(scroll, th)
        result_card.pack(fill="x", pady=6)

        self._sens_result_var = ctk.StringVar(value="Vyplňte hodnoty výše")
        _label(result_card, "Výsledek:", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 4), anchor="w")
        result_lbl = _label(result_card, "", 28, bold=True, color=th["success"],
                             textvariable=self._sens_result_var)
        result_lbl.pack(padx=14, pady=(0, 4), anchor="w")

        self._sens_detail_var = ctk.StringVar(value="")
        _label(result_card, "", 10, color=th["text_dim"],
               textvariable=self._sens_detail_var).pack(padx=14, pady=(0, 12), anchor="w")

        # Reference table
        ref_card = _card(scroll, th)
        ref_card.pack(fill="x", pady=6)

        _label(ref_card, "Tabulka cm/360° → pocit", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 4), anchor="w")

        tbl_frame = ctk.CTkFrame(ref_card, fg_color="transparent")
        tbl_frame.pack(padx=14, pady=(0, 12), anchor="w")

        refs = [
            ("< 20 cm", "Velmi rychlá — esport"),
            ("20–30 cm", "Rychlá — FPS standard"),
            ("30–45 cm", "Střední — comfortable"),
            ("45–70 cm", "Pomalá — tactical / sniper"),
            ("> 70 cm", "Velmi pomalá — strategy"),
        ]
        for cm_range, desc in refs:
            row = ctk.CTkFrame(tbl_frame, fg_color="transparent")
            row.pack(anchor="w", pady=1)
            _label(row, cm_range, 10, bold=True, color=th["primary"], width=100
                   ).pack(side="left")
            _label(row, desc, 10, color=th["text_dim"]).pack(side="left", padx=(8, 0))

        self._recalc_sens()

    def _recalc_sens(self):
        try:
            src_game = self._src_game_var.get()
            dst_game = self._dst_game_var.get()
            src_sens = float(self._src_sens_var.get().replace(",", "."))
            src_dpi  = float(self._src_dpi_var.get().replace(",", "."))
            dst_dpi  = float(self._dst_dpi_var.get().replace(",", "."))

            src_mult = SENS_GAMES.get(src_game, 0.022)
            dst_mult = SENS_GAMES.get(dst_game, 0.022)

            cm_per_360 = 36000.0 / (src_dpi * src_sens * src_mult)
            dst_sens   = 36000.0 / (dst_dpi * dst_mult * cm_per_360)

            self._sens_result_var.set(f"{dst_sens:.4f}")
            self._cm360_var.set(f"📏 cm/360°: {cm_per_360:.2f} cm  |  eDPI: {int(src_dpi * src_sens)}")
            self._sens_detail_var.set(
                f"{src_game} {src_sens} @ {int(src_dpi)} DPI  →  "
                f"{dst_game} {dst_sens:.4f} @ {int(dst_dpi)} DPI  |  {cm_per_360:.2f} cm/360°"
            )
        except (ValueError, ZeroDivisionError):
            self._sens_result_var.set("—")
            self._cm360_var.set("")
            self._sens_detail_var.set("")

    # ── eDPI KALKULAČKA ───────────────────────────────────────────────────────

    def _build_edpi(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "📐 eDPI Kalkulačka", 16, bold=True, color=th["primary"],
               image=icons.icon("calculator", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 4), anchor="w")
        _label(scroll, "eDPI (effective DPI) = DPI × in-game sensitivity. "
                       "Umožňuje porovnání citlivosti napříč různými DPI.",
               11, color=th["text_dim"], wraplength=680, justify="left"
               ).pack(padx=4, pady=(0, 12), anchor="w")

        calc_card = _card(scroll, th)
        calc_card.pack(fill="x", pady=6)

        _label(calc_card, "Výpočet eDPI", 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 8), anchor="w")

        # Grid layout
        inp_frame = ctk.CTkFrame(calc_card, fg_color="transparent")
        inp_frame.pack(fill="x", padx=14, pady=(0, 8))

        fields = [
            ("DPI:", "800"),
            ("In-game Sensitivity:", "1.0"),
        ]
        self._edpi_vars = []
        for col, (label, default) in enumerate(fields):
            inner = ctk.CTkFrame(inp_frame, fg_color="transparent")
            inner.pack(side="left", padx=(0, 20))
            _label(inner, label, 11, color=th["text_dim"]).pack(anchor="w", pady=(0, 4))
            var = ctk.StringVar(value=default)
            var.trace_add("write", lambda *_: self._recalc_edpi())
            ctk.CTkEntry(inner, textvariable=var,
                         fg_color=th["secondary"], text_color=th["text"],
                         font=ctk.CTkFont("Segoe UI", 14), height=40, width=130
                         ).pack()
            self._edpi_vars.append(var)

        # Result
        edpi_result_card = _card(scroll, th)
        edpi_result_card.pack(fill="x", pady=6)

        self._edpi_result_var = ctk.StringVar(value="—")
        _label(edpi_result_card, "eDPI:", 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 4), anchor="w")
        _label(edpi_result_card, "", 32, bold=True, color=th["success"],
               textvariable=self._edpi_result_var
               ).pack(padx=14, pady=(0, 4), anchor="w")

        self._edpi_rating_var = ctk.StringVar(value="")
        _label(edpi_result_card, "", 11, color=th["text_dim"],
               textvariable=self._edpi_rating_var
               ).pack(padx=14, pady=(0, 12), anchor="w")

        # Reference tiers
        ref_card = _card(scroll, th)
        ref_card.pack(fill="x", pady=6)

        _label(ref_card, "eDPI Tiers pro FPS hry", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        tiers = [
            ("< 400",       "#f87171", "Velmi nízké — extreme low sens"),
            ("400–800",     "#fb923c", "Nízké — competitive / esport"),
            ("800–1600",    "#4ade80", "Střední — běžný hráč"),
            ("1600–3200",   "#fbbf24", "Vysoké — casual"),
            ("> 3200",      "#a78bfa", "Velmi vysoké — beginners"),
        ]
        tbl = ctk.CTkFrame(ref_card, fg_color="transparent")
        tbl.pack(padx=14, pady=(0, 12))

        for edpi_range, color, desc in tiers:
            row = ctk.CTkFrame(tbl, fg_color="transparent")
            row.pack(anchor="w", pady=2)
            ctk.CTkFrame(row, fg_color=color, corner_radius=3, width=12, height=12
                         ).pack(side="left", padx=(0, 8))
            _label(row, edpi_range, 10, bold=True, color=th["text"], width=80
                   ).pack(side="left")
            _label(row, desc, 10, color=th["text_dim"]).pack(side="left", padx=(8, 0))

        # Pro player reference
        pro_card = _card(scroll, th)
        pro_card.pack(fill="x", pady=6)

        _label(pro_card, "Referenční hodnoty pro-hráčů (CS2)", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        pros = [
            ("s1mple",  400, 3.09,  ""),
            ("ZywOo",   400, 2.0,   ""),
            ("NiKo",    400, 1.35,  ""),
            ("device",  400, 1.6,   ""),
            ("ropz",    400, 1.0,   ""),
            ("sh1ro",   400, 2.5,   ""),
            ("m0NESY",  400, 1.4,   ""),
            ("broky",   400, 1.05,  ""),
        ]
        pro_tbl = ctk.CTkFrame(pro_card, fg_color="transparent")
        pro_tbl.pack(padx=14, pady=(0, 12), fill="x")

        hdr_row = ctk.CTkFrame(pro_tbl, fg_color=th["secondary"], corner_radius=4)
        hdr_row.pack(fill="x", pady=(0, 2))
        for txt, w in [("Hráč", 90), ("DPI", 60), ("Sens", 60), ("eDPI", 70)]:
            _label(hdr_row, txt, 10, bold=True, color=th["text_dim"], width=w
                   ).pack(side="left", padx=8, pady=4)

        for name, dpi, sens, _ in pros:
            edpi = int(dpi * sens)
            row = ctk.CTkFrame(pro_tbl, fg_color="transparent")
            row.pack(fill="x", pady=1)
            for txt, w in [(name, 90), (str(dpi), 60), (str(sens), 60), (str(edpi), 70)]:
                _label(row, txt, 10, color=th["text"], width=w
                       ).pack(side="left", padx=8)

        self._recalc_edpi()

    def _recalc_edpi(self):
        try:
            dpi  = float(self._edpi_vars[0].get().replace(",", "."))
            sens = float(self._edpi_vars[1].get().replace(",", "."))
            edpi = dpi * sens
            self._edpi_result_var.set(f"{edpi:.0f}")

            if edpi < 400:
                rating = "⬇ Velmi nízké eDPI — extreme low sens"
            elif edpi < 800:
                rating = "🎯 Nízké eDPI — competitive / esport tier"
            elif edpi < 1600:
                rating = "✅ Střední eDPI — typický hráč"
            elif edpi < 3200:
                rating = "⬆ Vysoké eDPI — casual hráč"
            else:
                rating = "🔺 Velmi vysoké eDPI — zkus snížit DPI nebo sens"

            self._edpi_rating_var.set(rating)
        except (ValueError, ZeroDivisionError):
            self._edpi_result_var.set("—")
            self._edpi_rating_var.set("")

    # ── PING TESTER ───────────────────────────────────────────────────────────

    def _build_ping(self, tab):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        _label(scroll, "📡 Ping Tester", 16, bold=True, color=th["primary"],
               image=icons.icon("tower-broadcast", 18, th["primary"]), compound="left"
               ).pack(padx=4, pady=(4, 4), anchor="w")
        _label(scroll, "Změří latenci k herním serverům a síťovým endpointům pomocí TCP/socket spojení.",
               11, color=th["text_dim"]).pack(padx=4, pady=(0, 12), anchor="w")

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(0, 8))

        ctk.CTkButton(
            btn_row, text=" Testovat vše",
            image=icons.icon("play", 14, "#cccccc"), compound="left",
            fg_color=th["primary"], hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36,
            command=self._run_all_pings
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text=" Vymazat výsledky",
            image=icons.icon("trash", 13, "#cccccc"), compound="left",
            fg_color=th["secondary"], hover_color="#3a1a1a",
            font=ctk.CTkFont("Segoe UI", 11), height=36,
            command=self._clear_pings
        ).pack(side="left")

        # Server rows
        self._ping_rows: dict[str, dict] = {}
        servers_card = _card(scroll, th)
        servers_card.pack(fill="x", pady=6)

        hdr = ctk.CTkFrame(servers_card, fg_color=th["secondary"], corner_radius=0)
        hdr.pack(fill="x")
        for txt, w in [("Server", 220), ("Host", 200), ("Port", 60), ("Latence", 100), ("Status", 100)]:
            _label(hdr, txt, 10, bold=True, color=th["text_dim"], width=w
                   ).pack(side="left", padx=8, pady=6)

        for (name, host, port) in PING_SERVERS:
            row_frame = ctk.CTkFrame(servers_card, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            _label(row_frame, name, 11, color=th["text"], width=220
                   ).pack(side="left", padx=8)
            _label(row_frame, host[:30], 10, color=th["text_dim"], width=200
                   ).pack(side="left", padx=8)
            _label(row_frame, str(port), 10, color=th["text_dim"], width=60
                   ).pack(side="left", padx=8)

            latency_lbl = _label(row_frame, "—", 11, bold=True, color=th["text_dim"], width=100)
            latency_lbl.pack(side="left", padx=8)

            status_lbl = _label(row_frame, "čeká", 10, color=th["text_dim"], width=100)
            status_lbl.pack(side="left", padx=8)

            self._ping_rows[name] = {"lat": latency_lbl, "st": status_lbl, "host": host, "port": port}

        # Custom server
        custom_card = _card(scroll, th)
        custom_card.pack(fill="x", pady=6)

        _label(custom_card, "Vlastní server", 12, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        cust_row = ctk.CTkFrame(custom_card, fg_color="transparent")
        cust_row.pack(fill="x", padx=14, pady=(0, 14))

        self._custom_host = ctk.CTkEntry(
            cust_row, placeholder_text="hostname nebo IP",
            fg_color=th["secondary"], text_color=th["text"],
            font=ctk.CTkFont("Segoe UI", 12), height=36)
        self._custom_host.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._custom_port = ctk.CTkEntry(
            cust_row, placeholder_text="port",
            fg_color=th["secondary"], text_color=th["text"],
            font=ctk.CTkFont("Segoe UI", 12), height=36, width=80)
        self._custom_port.insert(0, "443")
        self._custom_port.pack(side="left", padx=(0, 8))

        self._custom_result = _label(custom_card, "", 12, color=th["text_dim"])
        self._custom_result.pack(padx=14, pady=(0, 8), anchor="w")

        ctk.CTkButton(
            cust_row, text="Ping",
            fg_color=th["primary"], hover_color=th["primary_hover"],
            font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36, width=80,
            command=self._run_custom_ping
        ).pack(side="left")

    def _tcp_ping_ms(self, host: str, port: int, timeout: float = 3.0) -> float | None:
        """Connect via TCP and return latency in ms, or None on failure."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            t0 = time.perf_counter()
            result = s.connect_ex((host, port))
            ms = (time.perf_counter() - t0) * 1000
            s.close()
            return ms if result == 0 else None
        except Exception:
            return None

    def _run_all_pings(self):
        th = self.theme
        for name, row in self._ping_rows.items():
            row["lat"].configure(text="...", text_color=th["text_dim"])
            row["st"].configure(text="měřím", text_color=th["text_dim"])

        def worker(name, row):
            ms = self._tcp_ping_ms(row["host"], row["port"])
            if ms is None:
                lat_txt = "timeout"
                lat_col = th["error"]
                st_txt  = "❌ offline"
                st_col  = th["error"]
            elif ms < 50:
                lat_txt = f"{ms:.0f} ms"
                lat_col = th["success"]
                st_txt  = "✅ excellent"
                st_col  = th["success"]
            elif ms < 100:
                lat_txt = f"{ms:.0f} ms"
                lat_col = "#4ade80"
                st_txt  = "✅ good"
                st_col  = "#4ade80"
            elif ms < 200:
                lat_txt = f"{ms:.0f} ms"
                lat_col = th["warning"]
                st_txt  = "⚠ fair"
                st_col  = th["warning"]
            else:
                lat_txt = f"{ms:.0f} ms"
                lat_col = th["error"]
                st_txt  = "🔴 high"
                st_col  = th["error"]

            self.after(0, row["lat"].configure,
                       {"text": lat_txt, "text_color": lat_col})
            self.after(0, row["st"].configure,
                       {"text": st_txt, "text_color": st_col})

        for name, row in self._ping_rows.items():
            threading.Thread(target=worker, args=(name, row), daemon=True).start()

    def _clear_pings(self):
        th = self.theme
        for row in self._ping_rows.values():
            row["lat"].configure(text="—", text_color=th["text_dim"])
            row["st"].configure(text="čeká", text_color=th["text_dim"])

    def _run_custom_ping(self):
        host = self._custom_host.get().strip()
        if not host:
            return
        try:
            port = int(self._custom_port.get().strip())
        except ValueError:
            port = 443
        self._custom_result.configure(text=f"Měřím {host}:{port}...",
                                       text_color=self.theme["text_dim"])

        def run():
            ms = self._tcp_ping_ms(host, port)
            if ms is None:
                txt = f"❌ {host}:{port} — nedostupný (timeout)"
                col = self.theme["error"]
            else:
                txt = f"✅ {host}:{port} — {ms:.0f} ms"
                col = self.theme["success"] if ms < 100 else self.theme["warning"]
            self.after(0, self._custom_result.configure, {"text": txt, "text_color": col})

        threading.Thread(target=run, daemon=True).start()
