"""
ZeddiHub SpeedTest — integrated module panel.

Exposes SpeedTestPanel (ctk.CTkFrame) which is loaded dynamically by the
main app after installation via tools_download. Rendered inline in the
main window content area.
"""

import json
import math
import os
import socket
import statistics
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Best-effort: reuse the host app's FontAwesome icon renderer so the
# Historie / Rozšířené výsledky pills and other buttons match the
# rest of the app. Falls back to unicode glyphs if the module is
# loaded in a standalone context.
try:
    from gui import icons as _app_icons  # type: ignore
except Exception:
    _app_icons = None


# ── Config ────────────────────────────────────────────────────────────────
MODULE_NAME    = "SpeedTest"
MODULE_VERSION = "1.0.6"

DL_URL   = "https://speed.cloudflare.com/__down?bytes={bytes}"
UL_URL   = "https://speed.cloudflare.com/__up"
META_URL = "https://speed.cloudflare.com/meta"

PING_HOSTS   = [("cloudflare.com", 443), ("google.com", 443), ("zeddihub.eu", 443)]
GAUGE_MAX_DEFAULT = 500.0

HISTORY_DIR  = Path.home() / "AppData" / "Local" / "ZeddiHub" / "speedtest"
HISTORY_FILE = HISTORY_DIR / "history.json"
HISTORY_MAX  = 200

ORANGE    = "#f0a500"
ORANGE_HI = "#ffb91f"
GREEN     = "#22c55e"
BLUE      = "#3b82f6"
RED       = "#ef4444"


# ── Font loader (PyInstaller-safe absolute paths) ────────────────────────
def _win_font(name: str) -> str:
    """Return absolute Windows font path if it exists, else the bare name
    so PIL can try its own lookup; returns None if none works (caller
    falls back to load_default)."""
    candidates = [
        fr"C:\Windows\Fonts\{name}",
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name),
        name,
    ]
    for p in candidates:
        try:
            if os.path.isabs(p) and not os.path.isfile(p):
                continue
            ImageFont.truetype(p, 10)
            return p
        except Exception:
            continue
    return None


def _load_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    """Bundled bitmap ImageFont.load_default() ignores fill color on older
    PILs — always try TTF first so the value number renders in whatever
    color we asked for."""
    names = (["segoeuib.ttf", "arialbd.ttf", "tahomabd.ttf"]
             if bold else
             ["segoeui.ttf", "arial.ttf", "tahoma.ttf"])
    for n in names:
        p = _win_font(n)
        if p:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ── History ───────────────────────────────────────────────────────────────
def _load_history() -> list:
    try:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_history(items: list) -> None:
    try:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(items[-HISTORY_MAX:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── Network helpers ───────────────────────────────────────────────────────
def _tcp_ping(host: str, port: int, timeout: float = 2.0):
    try:
        start = time.perf_counter()
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return (time.perf_counter() - start) * 1000.0
    except Exception:
        return None


def _fetch_meta() -> dict:
    meta = {"ip": "-", "isp": "-", "server": "-", "city": "-"}
    try:
        with urllib.request.urlopen(META_URL, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        meta["ip"]     = data.get("clientIp", "-")
        meta["isp"]    = data.get("asOrganization", "-")
        meta["server"] = f"Cloudflare · {data.get('colo', '-')}"
        meta["city"]   = data.get("city", "-") or data.get("country", "-")
    except Exception:
        pass
    return meta


_NAMED_COLORS = {
    "transparent": (10, 10, 15),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}


def _hex_rgb(h):
    if h is None:
        return (10, 10, 15)
    if isinstance(h, (tuple, list)):
        h = h[0] if h else "#0a0a0f"
    if not isinstance(h, str):
        return (10, 10, 15)
    s = h.strip().lstrip("#")
    low = s.lower()
    if low in _NAMED_COLORS:
        return _NAMED_COLORS[low]
    if len(s) == 3 and all(c in "0123456789abcdefABCDEF" for c in s):
        return tuple(int(c * 2, 16) for c in s)
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
    return (10, 10, 15)


def _rgb_hex(r, g, b) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _brightness(hex_color) -> float:
    r, g, b = _hex_rgb(hex_color)
    return (r * 299 + g * 587 + b * 114) / 1000.0


def _blend(a, b, t: float) -> str:
    ar, ag, ab = _hex_rgb(a)
    br, bg, bb = _hex_rgb(b)
    return _rgb_hex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t)


# ── Antialiased gauge ────────────────────────────────────────────────────
class _Gauge(ctk.CTkLabel):
    SWEEP_DEG = 240
    START_DEG = 150
    SS = 2

    def __init__(self, parent, size: int = 340, bg: str = "#0a0a0f",
                 track: str = "#1e1e28", text: str = None,
                 text_dim: str = "#7a7a8a"):
        self._size = size
        self._max = GAUGE_MAX_DEFAULT
        self._value = 0.0
        self._target = 0.0
        self._unit = "Mbps"
        self._show_mbps_conv = False
        self._color = ORANGE
        self._animating = False
        self._img_ref = None
        self._bg = bg
        self._track = track
        # Honor explicit theme text color; otherwise compute from bg
        # brightness. Either way the gauge number stays high-contrast.
        if text:
            self._text = text
        else:
            self._text = "#ffffff" if _brightness(bg) < 140 else "#0a0a0f"
        self._text_dim = text_dim

        super().__init__(parent, text="", fg_color="transparent",
                         width=size, height=size)
        self._render()

    def set_phase(self, color: str, unit: str = "Mbps",
                  auto_max: float = GAUGE_MAX_DEFAULT,
                  show_mbps_conv: bool = False):
        self._color = color
        self._unit = unit
        self._max = auto_max
        self._show_mbps_conv = show_mbps_conv
        self._value = 0.0
        self._target = 0.0
        self._render()

    def set_value(self, v: float):
        self._target = max(0.0, v)
        if self._target > self._max:
            self._max = max(self._max, math.ceil(self._target / 50) * 50)
        if not self._animating:
            self._animating = True
            self._tick()

    def set_final(self, v: float):
        self._target = max(0.0, v)
        self._value = self._target
        if self._target > self._max:
            self._max = max(self._max, math.ceil(self._target / 50) * 50)
        self._render()

    def reset(self):
        self._value = 0.0
        self._target = 0.0
        self._max = GAUGE_MAX_DEFAULT
        self._render()

    def _tick(self):
        gap = self._target - self._value
        if abs(gap) < 0.05:
            self._value = self._target
            self._animating = False
            self._render()
            return
        self._value += gap * 0.22
        self._render()
        self.after(16, self._tick)

    def _render(self):
        S = self._size
        ss = self.SS
        W = S * ss
        img = Image.new("RGBA", (W, W), _hex_rgb(self._bg) + (255,))
        d = ImageDraw.Draw(img)

        cx, cy = W / 2, W / 2 + 6 * ss
        r_outer = W / 2 - 20 * ss
        track_w = 10 * ss
        bbox = [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer]
        start_a = self.START_DEG

        d.arc(bbox, start=start_a, end=start_a + self.SWEEP_DEG,
              fill=_hex_rgb(self._track) + (255,), width=int(track_w))

        pct = max(0.0, min(1.0, self._value / self._max)) if self._max > 0 else 0.0
        if pct > 0.005:
            end_a = start_a + self.SWEEP_DEG * pct
            d.arc(bbox, start=start_a, end=end_a,
                  fill=_hex_rgb(self._color) + (255,), width=int(track_w))

        for i in range(11):
            t = i / 10
            ang = math.radians(start_a + self.SWEEP_DEG * t)
            r1 = r_outer - track_w - 6 * ss
            r2 = r_outer - track_w - 14 * ss
            x1, y1 = cx + math.cos(ang) * r1, cy + math.sin(ang) * r1
            x2, y2 = cx + math.cos(ang) * r2, cy + math.sin(ang) * r2
            d.line([(x1, y1), (x2, y2)],
                   fill=_hex_rgb(self._text_dim) + (255,), width=int(2 * ss))

        ang = math.radians(start_a + self.SWEEP_DEG * pct)
        tip_r = r_outer - track_w - 4 * ss
        tip_x = cx + math.cos(ang) * tip_r
        tip_y = cy + math.sin(ang) * tip_r
        perp = ang + math.pi / 2
        base_half = 5 * ss
        bx1 = cx + math.cos(perp) * base_half
        by1 = cy + math.sin(perp) * base_half
        bx2 = cx - math.cos(perp) * base_half
        by2 = cy - math.sin(perp) * base_half
        d.polygon([(tip_x, tip_y), (bx1, by1), (bx2, by2)],
                  fill=_hex_rgb(self._color) + (255,))

        hub_r = 9 * ss
        d.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r],
                  fill=_hex_rgb(self._bg) + (255,),
                  outline=_hex_rgb(self._color) + (255,), width=int(3 * ss))

        img = img.resize((S, S), Image.LANCZOS)
        d2 = ImageDraw.Draw(img)
        self._draw_texts(d2, S)

        try:
            photo = ImageTk.PhotoImage(img)
        except Exception:
            return
        self._img_ref = photo
        try:
            self.configure(image=photo, text="")
        except Exception:
            pass

    def _draw_texts(self, d, S):
        cx = S // 2
        cy = S // 2 + 6
        val_txt = f"{self._value:.2f}" if self._value < 100 else f"{self._value:.1f}"

        big   = _load_font(bold=True,  size=42)
        small = _load_font(bold=False, size=13)
        tiny  = _load_font(bold=False, size=10)

        # Bottom sector (30°–150° the needle never sweeps) — stable zone
        # for legible text.
        try:
            tw = d.textlength(val_txt, font=big)
        except Exception:
            tw = len(val_txt) * 20
        d.text((cx - tw / 2, cy + 32), val_txt,
               fill=_hex_rgb(self._text) + (255,), font=big)

        try:
            tw = d.textlength(self._unit, font=small)
        except Exception:
            tw = len(self._unit) * 8
        d.text((cx - tw / 2, cy + 86), self._unit,
               fill=_hex_rgb(self._text_dim) + (255,), font=small)

        if self._show_mbps_conv and self._unit.lower() == "mbps":
            mbps_val = self._value / 8.0
            mb_txt = f"≈ {mbps_val:.2f} MB/s"
            try:
                tw = d.textlength(mb_txt, font=tiny)
            except Exception:
                tw = len(mb_txt) * 6
            d.text((cx - tw / 2, cy + 104), mb_txt,
                   fill=_hex_rgb(self._text_dim) + (255,), font=tiny)


# ── Runner ────────────────────────────────────────────────────────────────
class _Runner:
    def __init__(self, on_phase, on_sample, on_meta, on_done, on_status):
        self.on_phase = on_phase
        self.on_sample = on_sample
        self.on_meta = on_meta
        self.on_done = on_done
        self.on_status = on_status
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        t_start = time.monotonic()
        result = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "ping_ms": None, "jitter_ms": None, "loss_pct": None,
            "download_mbps": 0.0, "upload_mbps": 0.0,
            "ip": "-", "isp": "-", "server": "-", "city": "-",
            "duration_s": 0.0,
        }

        self.on_status("Zjišťuji připojení…")
        meta = _fetch_meta()
        result.update(meta)
        self.on_meta(meta)
        if self._stop.is_set(): return

        self.on_phase("ping", "ms", 80)
        pings = []
        self.on_status("Měřím odezvu…")
        for i in range(12):
            if self._stop.is_set(): return
            rtt = None
            for host, port in PING_HOSTS:
                rtt = _tcp_ping(host, port, 2.0)
                if rtt is not None: break
            if rtt is not None:
                pings.append(rtt)
                self.on_sample(rtt)
            time.sleep(0.08)

        if pings:
            result["ping_ms"] = round(statistics.median(pings), 1)
            result["jitter_ms"] = round(statistics.pstdev(pings), 1) if len(pings) > 1 else 0.0
            result["loss_pct"] = round(100.0 * (12 - len(pings)) / 12, 1)
        else:
            result["loss_pct"] = 100.0
        if self._stop.is_set(): return

        self.on_phase("download", "Mbps", GAUGE_MAX_DEFAULT)
        self.on_status("Měřím stahování…")
        dl = self._measure_download(25 * 1024 * 1024, 10.0)
        result["download_mbps"] = round(dl, 2)
        if self._stop.is_set(): return

        self.on_phase("upload", "Mbps", max(100.0, dl * 0.9))
        self.on_status("Měřím odesílání…")
        ul = self._measure_upload(10 * 1024 * 1024, 10.0)
        result["upload_mbps"] = round(ul, 2)

        result["duration_s"] = round(time.monotonic() - t_start, 1)
        self.on_status("✓ Test dokončen")
        self.on_done(result)

    def _measure_download(self, bytes_, cap_s):
        url = DL_URL.format(bytes=bytes_)
        req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubSpeedTest/1.0"})
        total, samples = 0, []
        start = time.perf_counter()
        last, last_bytes = start, 0
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                while True:
                    if self._stop.is_set(): break
                    chunk = resp.read(64 * 1024)
                    if not chunk: break
                    total += len(chunk)
                    now = time.perf_counter()
                    if now - last >= 0.15:
                        inst = ((total - last_bytes) * 8) / (now - last) / 1_000_000
                        samples.append(inst)
                        self.on_sample(inst)
                        last, last_bytes = now, total
                    if now - start > cap_s: break
        except Exception as e:
            self.on_status(f"Chyba stahování: {e.__class__.__name__}")
            return 0.0
        dur = max(0.1, time.perf_counter() - start)
        avg = (total * 8) / dur / 1_000_000
        if samples:
            samples.sort()
            p90 = samples[int(len(samples) * 0.9)] if len(samples) >= 10 else samples[-1]
            return (avg * p90) ** 0.5 if avg > 0 else p90
        return avg

    def _measure_upload(self, bytes_, cap_s):
        import http.client, ssl
        payload = b"x" * (64 * 1024)
        total, samples = 0, []
        start = time.perf_counter()
        last, last_bytes = start, 0
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection("speed.cloudflare.com", 443, timeout=15, context=ctx)
            conn.putrequest("POST", "/__up")
            conn.putheader("Content-Length", str(bytes_))
            conn.putheader("User-Agent", "ZeddiHubSpeedTest/1.0")
            conn.putheader("Content-Type", "application/octet-stream")
            conn.endheaders()
            while total < bytes_ and not self._stop.is_set():
                rem = bytes_ - total
                chunk = payload if rem >= len(payload) else payload[:rem]
                conn.send(chunk)
                total += len(chunk)
                now = time.perf_counter()
                if now - last >= 0.15:
                    inst = ((total - last_bytes) * 8) / (now - last) / 1_000_000
                    samples.append(inst)
                    self.on_sample(inst)
                    last, last_bytes = now, total
                if now - start > cap_s: break
            try:
                resp = conn.getresponse(); resp.read()
            except Exception:
                pass
            conn.close()
        except Exception as e:
            self.on_status(f"Chyba odesílání: {e.__class__.__name__}")
            return 0.0
        dur = max(0.1, time.perf_counter() - start)
        avg = (total * 8) / dur / 1_000_000
        if samples:
            samples.sort()
            p90 = samples[int(len(samples) * 0.9)] if len(samples) >= 10 else samples[-1]
            return (avg * p90) ** 0.5 if avg > 0 else p90
        return avg


# ── Panel ─────────────────────────────────────────────────────────────────
class SpeedTestPanel(ctk.CTkFrame):
    """Main-app-embedded SpeedTest panel."""

    PHASE_LABELS = {"ping": "ODEZVA", "download": "STAHOVÁNÍ",
                    "upload": "ODESÍLÁNÍ", "result": "VÝSLEDEK"}
    PHASE_COLORS = {"ping": GREEN, "download": ORANGE,
                    "upload": ORANGE_HI, "result": ORANGE}

    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        self.theme = theme or {}
        bg = self.theme.get("content_bg", "#0a0a0f")
        super().__init__(parent, fg_color=bg, **kwargs)
        self._runner = None
        self._history = _load_history()
        self._last_result = None

        self._history_visible = False
        self._advanced_visible = False
        self._history_overlay = None
        self._history_backdrop = None

        self._phase_lbl_current = None
        self._phase_anim_job = None

        self._build()

    # ── theme tokens ──────────────────────────────────────────────────────
    def _c(self, key, fallback):
        return self.theme.get(key, fallback)

    def _build(self):
        bg = self._c("content_bg", "#0a0a0f")
        card = self._c("card_bg", "#13131b")
        border = self._c("border", "#1f1f2a")
        text = self._c("text", "#f5f5f7")
        text_dim = self._c("text_dim", "#7a7a8a")
        track = "#1e1e28"

        self._bg = bg
        self._card = card
        self._border = border
        self._text = text
        self._text_dim = text_dim

        # Full-panel scroll so Rozšířené výsledky / tall stacks never clip
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=bg,
                                              corner_radius=0)
        self._scroll.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(self._scroll, fg_color="transparent")
        inner.pack(fill="both", expand=True)
        self._inner = inner

        # ── top bar (bigger module title + pill Historie button) ──────────
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(16, 6))

        ctk.CTkLabel(top, text="SpeedTest",
                     font=ctk.CTkFont("Segoe UI", 26, "bold"),
                     text_color=text).pack(side="left")

        self._history_btn = self._pill_button(
            top, text="Historie", icon_char="⟳",
            icon_name="clock-rotate-left",
            command=self._toggle_history,
        )
        self._history_btn.pack(side="right")

        # ── gauge ─────────────────────────────────────────────────────────
        gauge_wrap = ctk.CTkFrame(inner, fg_color="transparent", height=360)
        gauge_wrap.pack(fill="x", pady=(0, 0))
        gauge_wrap.pack_propagate(False)

        self._gauge = _Gauge(gauge_wrap, size=340,
                             bg=bg, track=track,
                             text=text, text_dim=text_dim)
        self._gauge.place(relx=0.5, rely=0.5, anchor="center")

        # ── phase label (below gauge, NOT on the needle) ──────────────────
        self._phase_bar = ctk.CTkFrame(inner, fg_color="transparent",
                                       height=36)
        self._phase_bar.pack(fill="x", pady=(6, 0))
        self._phase_bar.pack_propagate(False)

        # ── status line ───────────────────────────────────────────────────
        self._status_label = ctk.CTkLabel(
            inner, text="Klikni START pro zahájení testu",
            font=ctk.CTkFont("Segoe UI", 11), text_color=text_dim,
        )
        self._status_label.pack(pady=(2, 0))

        # ── metrics row (Ping · Download · Upload · Jitter on one line) ──
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(pady=(10, 0))

        self._m_ping   = self._metric(row, "PING",     GREEN,     mbps=False)
        self._m_ping.pack(side="left", padx=(0, 8))
        self._metric_sep(row)
        self._m_dl     = self._metric(row, "DOWNLOAD", ORANGE,    mbps=True)
        self._m_dl.pack(side="left", padx=8)
        self._metric_sep(row)
        self._m_ul     = self._metric(row, "UPLOAD",   ORANGE_HI, mbps=True)
        self._m_ul.pack(side="left", padx=8)
        self._metric_sep(row)
        self._m_jitter = self._metric(row, "JITTER",   BLUE,      mbps=False)
        self._m_jitter.pack(side="left", padx=(8, 0))

        # connection meta (ip · isp · server) under metrics
        self._info_label = ctk.CTkLabel(
            inner, text="", font=ctk.CTkFont("Segoe UI", 10),
            text_color=text_dim,
        )
        self._info_label.pack(pady=(10, 0))

        # ── START / NOVÝ TEST button ──────────────────────────────────────
        primary = self._c("primary", ORANGE)
        primary_hover = self._c("primary_hover", ORANGE_HI)
        self._start_btn = ctk.CTkButton(
            inner, text="START",
            fg_color=primary, hover_color=primary_hover, text_color="#0a0a0f",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            width=180, height=48, corner_radius=24,
            command=self._start_test,
        )
        self._start_btn.pack(pady=(14, 10))

        # ── Rozšířené výsledky pill button ─────────────────────────────────
        self._adv_btn = self._pill_button(
            inner, text="Rozšířené výsledky", icon_char="▸",
            icon_name="chart-simple",
            command=self._toggle_advanced, width=220,
        )
        self._adv_btn.pack(pady=(4, 4))

        self._adv_body = ctk.CTkFrame(
            inner, fg_color=card, corner_radius=12,
            border_width=1, border_color=border,
        )

        # Pre-populate with placeholders + trigger async Cloudflare meta
        # fetch so IP / ISP / server / city are filled before the first
        # test run.
        self._render_advanced({})
        threading.Thread(target=self._prefetch_meta, daemon=True).start()

    # ── pill button factory ──────────────────────────────────────────────
    def _pill_button(self, parent, text: str, icon_char: str,
                     command, width: int = 120, icon_name: str = None):
        card = self._c("card_bg", "#13131b")
        primary = self._c("primary", ORANGE)
        text_col = self._c("text", "#f5f5f7")

        image = None
        if icon_name and _app_icons is not None:
            try:
                image = _app_icons.icon(icon_name, size=14, color=text_col)
            except Exception:
                image = None

        btn = ctk.CTkButton(
            parent,
            text=text if image is not None else f"  {icon_char}   {text}",
            image=image,
            compound="left",
            fg_color=card, hover_color=primary,
            text_color=text_col,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            width=width, height=34, corner_radius=17,
            border_width=1, border_color=self._c("border", "#2a2a36"),
            command=command,
        )
        # Track icon state so _toggle_* handlers can refresh without
        # losing the FA image.
        btn._icon_name = icon_name
        btn._icon_char = icon_char
        btn._label_text = text
        return btn

    def _pill_set_state(self, btn, text: str, icon_name: str,
                        icon_char: str):
        """Re-render a pill button's label + icon atomically."""
        text_col = self._c("text", "#f5f5f7")
        image = None
        if icon_name and _app_icons is not None:
            try:
                image = _app_icons.icon(icon_name, size=14, color=text_col)
            except Exception:
                image = None
        try:
            btn.configure(
                text=text if image is not None else f"  {icon_char}   {text}",
                image=image,
            )
        except Exception:
            try:
                btn.configure(text=f"  {icon_char}   {text}")
            except Exception:
                pass
        btn._icon_name = icon_name
        btn._icon_char = icon_char
        btn._label_text = text

    def _metric(self, parent, label: str, color: str, mbps: bool):
        """Inline metric: LABEL · value · unit all on one row."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(
            frame, text=label,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=self._c("text_dim", "#7a7a8a"),
        ).pack(side="left", padx=(0, 6))
        val = ctk.CTkLabel(
            frame, text="—",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=color,
        )
        val.pack(side="left")
        unit = ctk.CTkLabel(
            frame, text=(" Mbps" if mbps else " ms"),
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=self._c("text_dim", "#7a7a8a"),
        )
        unit.pack(side="left")
        mbps_lbl = None
        if mbps:
            mbps_lbl = ctk.CTkLabel(
                frame, text="",
                font=ctk.CTkFont("Segoe UI", 9),
                text_color=self._c("text_dim", "#7a7a8a"),
            )
            mbps_lbl.pack(side="left", padx=(6, 0))
        frame._val = val
        frame._unit = unit
        frame._mbps_lbl = mbps_lbl
        frame._color = color
        return frame

    def _metric_sep(self, parent):
        ctk.CTkLabel(
            parent, text="·",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=self._c("border", "#2a2a36"),
        ).pack(side="left")

    def _set_metric(self, frame, value, *, mbps_value: float = None):
        if value is None:
            frame._val.configure(text="—")
            if frame._mbps_lbl is not None:
                frame._mbps_lbl.configure(text="")
        else:
            frame._val.configure(text=str(value))
            if frame._mbps_lbl is not None and mbps_value is not None:
                frame._mbps_lbl.configure(text=f"≈ {mbps_value:.2f} MB/s")

    # ── test actions ──────────────────────────────────────────────────────
    def _start_test(self):
        if self._runner is not None:
            return
        self._start_btn.configure(text="Probíhá…", state="disabled")
        self._set_metric(self._m_ping, None)
        self._set_metric(self._m_dl, None)
        self._set_metric(self._m_ul, None)
        self._set_metric(self._m_jitter, None)
        self._info_label.configure(text="")

        # Collapse advanced on new test (but keep the button visible)
        if self._advanced_visible:
            self._toggle_advanced()

        self._runner = _Runner(
            on_phase=lambda n, u, g: self.after(0, self._on_phase, n, u, g),
            on_sample=lambda v: self.after(0, self._gauge.set_value, v),
            on_meta=lambda m: self.after(0, self._on_meta, m),
            on_done=lambda r: self.after(0, self._on_done, r),
            on_status=lambda s: self.after(0, self._status_label.configure, {"text": s}),
        )
        self._runner.run()

    def _on_phase(self, name, unit, gmax):
        color = self.PHASE_COLORS.get(name, ORANGE)
        label = self.PHASE_LABELS.get(name, name.upper())
        show_mbps = (unit == "Mbps")
        self._gauge.set_phase(color, unit=unit, auto_max=gmax,
                              show_mbps_conv=show_mbps)
        self._animate_phase_label(label, color)

    def _animate_phase_label(self, new_text: str, color: str):
        """Slide-up + glow: new label enters from below, color pulses
        toward white mid-anim, old label slides up and fades to bg."""
        if self._phase_anim_job is not None:
            try:
                self.after_cancel(self._phase_anim_job)
            except Exception:
                pass
            self._phase_anim_job = None

        old = self._phase_lbl_current
        new = ctk.CTkLabel(
            self._phase_bar, text=new_text, text_color=color,
            font=ctk.CTkFont("Segoe UI Black", 15, "bold"),
        )
        new.place(relx=0.5, rely=0.5, anchor="center", y=28)
        self._phase_lbl_current = new

        bg_hex = self._bg
        start_t = time.monotonic()

        def _step():
            elapsed = time.monotonic() - start_t
            t = min(1.0, elapsed / 0.55)
            eased = 1.0 - (1.0 - t) ** 3

            new_y = int(28 * (1.0 - eased))
            try:
                new.place_configure(y=new_y)
            except Exception:
                return
            pulse = math.sin(t * math.pi) * 0.55
            glow_color = _blend(color, "#ffffff", pulse)
            try:
                new.configure(text_color=glow_color)
            except Exception:
                pass

            if old is not None and old.winfo_exists():
                try:
                    old.place_configure(y=int(-28 * eased))
                    old.configure(text_color=_blend(color, bg_hex, eased))
                except Exception:
                    pass

            if t >= 1.0:
                try:
                    new.configure(text_color=color)
                except Exception:
                    pass
                if old is not None:
                    try:
                        old.destroy()
                    except Exception:
                        pass
                self._phase_anim_job = None
                return
            self._phase_anim_job = self.after(16, _step)

        _step()

    def _prefetch_meta(self):
        """Background Cloudflare meta fetch so Rozšířené výsledky shows
        IP/ISP/server/city before a test is ever run."""
        try:
            meta = _fetch_meta()
        except Exception:
            return
        def _apply():
            if not self.winfo_exists():
                return
            self._on_meta(meta)
            merged = {
                "ip": meta.get("ip", "-"),
                "isp": meta.get("isp", "-"),
                "server": meta.get("server", "-"),
                "city": meta.get("city", "-"),
            }
            if self._last_result:
                merged.update(self._last_result)
            self._render_advanced(merged)
        try:
            self.after(0, _apply)
        except Exception:
            pass

    def _on_meta(self, meta):
        parts = []
        if meta.get("ip", "-") != "-":  parts.append(meta["ip"])
        if meta.get("isp", "-") != "-": parts.append(meta["isp"])
        if meta.get("server", "-") != "-": parts.append(meta["server"])
        self._info_label.configure(text="  ·  ".join(parts))

    def _on_done(self, result):
        self._runner = None
        self._last_result = result
        self._start_btn.configure(text="NOVÝ TEST", state="normal")

        dl = float(result.get("download_mbps") or 0)
        ul = float(result.get("upload_mbps") or 0)
        ping = result.get("ping_ms")
        jit = result.get("jitter_ms")

        self._set_metric(self._m_ping, ping if ping is not None else None)
        self._set_metric(self._m_dl, f"{dl:.1f}", mbps_value=dl / 8.0)
        self._set_metric(self._m_ul, f"{ul:.1f}", mbps_value=ul / 8.0)
        self._set_metric(self._m_jitter, jit if jit is not None else None)

        self._gauge.set_phase(ORANGE, unit="Mbps",
                              auto_max=max(100.0, dl * 1.15),
                              show_mbps_conv=True)
        self._animate_phase_label("VÝSLEDEK", ORANGE)
        self._gauge.set_final(dl)

        self._history.append(result)
        _save_history(self._history)

        # Advanced expander is already visible — just refresh contents
        self._render_advanced(result)

        if self._history_visible:
            self._render_history()

    # ── advanced (expander) ───────────────────────────────────────────────
    def _toggle_advanced(self):
        self._advanced_visible = not self._advanced_visible
        if self._advanced_visible:
            self._pill_set_state(self._adv_btn,
                                 "Rozšířené výsledky",
                                 "chart-simple", "▾")
            self._adv_body.pack(fill="x", padx=24, pady=(2, 20))
        else:
            self._pill_set_state(self._adv_btn,
                                 "Rozšířené výsledky",
                                 "chart-simple", "▸")
            self._adv_body.pack_forget()

    def _render_advanced(self, r: dict):
        for w in self._adv_body.winfo_children():
            w.destroy()

        text = self._text
        text_dim = self._text_dim

        def _fmt(key, unit, default="—"):
            v = r.get(key)
            if v is None or v == "-" or v == "":
                return default
            return f"{v} {unit}".strip()

        def _meta(key):
            v = r.get(key)
            if v is None or v == "-" or v == "":
                return "—"
            return str(v)

        dl = r.get("download_mbps")
        ul = r.get("upload_mbps")
        dl_s = f"{float(dl):.2f} Mbps   ≈ {float(dl)/8:.2f} MB/s" if dl else "—"
        ul_s = f"{float(ul):.2f} Mbps   ≈ {float(ul)/8:.2f} MB/s" if ul else "—"

        rows = [
            ("Veřejná IP",        _meta("ip")),
            ("Poskytovatel",      _meta("isp")),
            ("Testovací server",  _meta("server")),
            ("Lokalita",          _meta("city")),
            ("Ping",              _fmt("ping_ms", "ms")),
            ("Jitter",            _fmt("jitter_ms", "ms")),
            ("Ztrátovost",        _fmt("loss_pct", "%")),
            ("Doba testu",        _fmt("duration_s", "s")),
            ("Download",          dl_s),
            ("Upload",            ul_s),
        ]

        grid = ctk.CTkFrame(self._adv_body, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=14)
        grid.grid_columnconfigure(1, weight=1)

        for i, (k, v) in enumerate(rows):
            ctk.CTkLabel(grid, text=k,
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=text_dim, anchor="w",
                         ).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 20))
            ctk.CTkLabel(grid, text=str(v),
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=text, anchor="w",
                         ).grid(row=i, column=1, sticky="ew", pady=4)

    # ── History: floating overlay ────────────────────────────────────────
    def _toggle_history(self):
        if self._history_visible:
            self._close_history_overlay()
        else:
            self._open_history_overlay()

    def _open_history_overlay(self):
        self._history_visible = True
        self._pill_set_state(self._history_btn, "Historie",
                             "clock-rotate-left", "▾")

        # Dim backdrop (50% — darkened bg so content stays readable) —
        # click outside closes. Tk can't do real alpha, so we blend bg
        # halfway toward #000 as an "opacity 50%" approximation.
        dim = _blend(self._bg, "#000000", 0.5)
        backdrop = ctk.CTkFrame(self, fg_color=dim, corner_radius=0)
        backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        backdrop.bind("<Button-1>", lambda e: self._close_history_overlay())
        self._history_backdrop = backdrop

        # Floating panel — starts off-screen to the right, slides in
        panel = ctk.CTkFrame(self, fg_color=self._card,
                             corner_radius=14, border_width=1,
                             border_color=self._border, width=360)
        # Start position: relx=1.0, anchor=nw → completely off to the right
        panel.place(relx=1.0, rely=0.02, anchor="nw", x=0, relheight=0.96)
        self._history_overlay = panel
        self._animate_history_in(panel)

        # Header inside panel
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(header, text="Historie měření",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=self._text).pack(side="left")
        ctk.CTkButton(
            header, text="✕",
            fg_color="transparent", hover_color=RED,
            text_color=self._text_dim, width=28, height=28,
            corner_radius=14, font=ctk.CTkFont("Segoe UI", 12, "bold"),
            command=self._close_history_overlay,
        ).pack(side="right")

        count_bar = ctk.CTkFrame(panel, fg_color="transparent")
        count_bar.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(count_bar, text=f"{len(self._history)} záznamů",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=self._text_dim).pack(side="left")

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkButton(
            actions, text="Vymazat",
            fg_color=self._bg, hover_color=RED, text_color=self._text,
            font=ctk.CTkFont("Segoe UI", 10),
            height=28, width=80, corner_radius=6,
            command=self._clear_history,
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Export JSON",
            fg_color=self._bg, hover_color=ORANGE, text_color=self._text,
            font=ctk.CTkFont("Segoe UI", 10),
            height=28, width=110, corner_radius=6,
            command=self._export_history,
        ).pack(side="left", padx=(6, 0))

        self._history_scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", width=320,
        )
        self._history_scroll.pack(fill="both", expand=True, padx=10, pady=(4, 12))

        # Esc handler on the toplevel so the overlay closes cleanly
        try:
            self._esc_binding = self.winfo_toplevel().bind(
                "<Escape>", lambda e: self._close_history_overlay(), add="+"
            )
        except Exception:
            self._esc_binding = None

        self._render_history()

    def _animate_history_in(self, panel):
        """Slide the history panel from the right edge into its final
        parking spot (anchored ne, 18px from right) over ~200ms,
        ease-out cubic."""
        try:
            self.update_idletasks()
            host_w = max(self.winfo_width(), 1)
        except Exception:
            host_w = 1000
        panel_w = 360
        final_x = host_w - panel_w - 18
        start_x = host_w
        start_t = time.monotonic()
        duration = 0.20

        def _step():
            elapsed = time.monotonic() - start_t
            t = min(1.0, elapsed / duration)
            eased = 1.0 - (1.0 - t) ** 3
            x = int(start_x + (final_x - start_x) * eased)
            try:
                panel.place_configure(relx=0, x=x)
            except Exception:
                return
            if t < 1.0:
                self.after(16, _step)

        _step()

    def _close_history_overlay(self):
        self._history_visible = False
        self._pill_set_state(self._history_btn, "Historie",
                             "clock-rotate-left", "⟳")
        try:
            if self._history_overlay is not None:
                self._history_overlay.destroy()
        except Exception:
            pass
        try:
            if self._history_backdrop is not None:
                self._history_backdrop.destroy()
        except Exception:
            pass
        self._history_overlay = None
        self._history_backdrop = None
        esc = getattr(self, "_esc_binding", None)
        if esc:
            try:
                self.winfo_toplevel().unbind("<Escape>", esc)
            except Exception:
                pass
            self._esc_binding = None

    def _render_history(self):
        if not hasattr(self, "_history_scroll") or not self._history_scroll.winfo_exists():
            return
        for w in self._history_scroll.winfo_children():
            w.destroy()

        if not self._history:
            ctk.CTkLabel(self._history_scroll, text="Zatím žádné měření",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=self._text_dim).pack(pady=20)
            return

        for item in reversed(self._history[-HISTORY_MAX:]):
            self._render_history_card(item)

    def _render_history_card(self, item: dict):
        card_bg = self._bg

        card = ctk.CTkFrame(self._history_scroll, fg_color=card_bg,
                            corner_radius=8, border_width=1,
                            border_color=self._border)
        card.pack(fill="x", padx=4, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 2))
        ts = (item.get("ts") or "")[:16].replace("T", " ")
        ctk.CTkLabel(top, text=ts,
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=self._text).pack(side="left")
        isp = (item.get("isp") or "—")
        if len(isp) > 20: isp = isp[:18] + "…"
        ctk.CTkLabel(top, text=isp,
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self._text_dim).pack(side="right")

        mid = ctk.CTkFrame(card, fg_color="transparent")
        mid.pack(fill="x", padx=12, pady=(2, 2))
        for label, val, color in [
            ("Ping", f"{item.get('ping_ms', '—')} ms" if item.get('ping_ms') is not None else "— ms", GREEN),
            ("DL",   f"{item.get('download_mbps', 0):.1f}", ORANGE),
            ("UL",   f"{item.get('upload_mbps', 0):.1f}",   ORANGE_HI),
        ]:
            col = ctk.CTkFrame(mid, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(col, text=label,
                         font=ctk.CTkFont("Segoe UI", 8),
                         text_color=self._text_dim).pack(anchor="w")
            ctk.CTkLabel(col, text=val,
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=color).pack(anchor="w")

        details_txt = (
            f"Jitter {item.get('jitter_ms', 0)} ms  ·  "
            f"Ztráta {item.get('loss_pct', 0)} %  ·  "
            f"{item.get('duration_s', 0)} s"
        )
        ctk.CTkLabel(card, text=details_txt,
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=self._text_dim, anchor="w",
                     ).pack(fill="x", padx=12, pady=(0, 2))

        srv_line = []
        if item.get("server", "-") != "-": srv_line.append(str(item["server"]))
        if item.get("city", "-") != "-":   srv_line.append(str(item["city"]))
        if item.get("ip", "-") != "-":     srv_line.append(str(item["ip"]))
        if srv_line:
            ctk.CTkLabel(card, text="  ·  ".join(srv_line),
                         font=ctk.CTkFont("Segoe UI", 9),
                         text_color=self._text_dim, anchor="w", wraplength=290,
                         justify="left",
                         ).pack(fill="x", padx=12, pady=(0, 10))

    def _clear_history(self):
        self._history = []
        _save_history(self._history)
        self._render_history()

    def _export_history(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"zeddihub_speedtest_{datetime.now():%Y%m%d}.json",
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._history, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
