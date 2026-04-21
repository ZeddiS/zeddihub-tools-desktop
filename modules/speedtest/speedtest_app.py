"""
ZeddiHub SpeedTest — standalone module.

Minimalist speed test with PIL-rendered antialiased gauge and a
collapsible history panel.
"""

import json
import math
import socket
import statistics
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk


# ── Config ────────────────────────────────────────────────────────────────
APP_NAME     = "ZeddiHub SpeedTest"
APP_VERSION  = "1.0.1"
WINDOW_W     = 500
WINDOW_H     = 640

DL_URL       = "https://speed.cloudflare.com/__down?bytes={bytes}"
UL_URL       = "https://speed.cloudflare.com/__up"
META_URL     = "https://speed.cloudflare.com/meta"

PING_HOSTS   = [("cloudflare.com", 443), ("google.com", 443), ("zeddihub.eu", 443)]
GAUGE_MAX_DEFAULT = 500.0

HISTORY_DIR  = Path.home() / "AppData" / "Local" / "ZeddiHub" / "speedtest"
HISTORY_FILE = HISTORY_DIR / "history.json"
HISTORY_MAX  = 200

# Theme — flat, minimalist
BG        = "#0a0a0f"
CARD      = "#13131b"
BORDER    = "#1f1f2a"
TEXT      = "#f5f5f7"
TEXT_DIM  = "#7a7a8a"
ORANGE    = "#f0a500"
ORANGE_HI = "#ffb91f"
GREEN     = "#22c55e"
BLUE      = "#3b82f6"
RED       = "#ef4444"
TRACK     = "#1e1e28"


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


# ── Antialiased gauge (PIL supersampling) ────────────────────────────────
def _hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


class Gauge(ctk.CTkLabel):
    """Renders a minimalist arc + thin needle via PIL with 2x supersampling
    for smooth antialiasing. Sits directly on BG (no card)."""

    SWEEP_DEG = 240          # total arc sweep
    START_DEG = 150          # 150° from +x axis, going clockwise
    SS        = 2            # supersampling factor

    def __init__(self, parent, size: int = 360):
        self._size = size
        self._max = GAUGE_MAX_DEFAULT
        self._value = 0.0
        self._target = 0.0
        self._unit = "Mbps"
        self._phase_label = ""
        self._color = ORANGE
        self._animating = False
        self._img_ref = None

        super().__init__(parent, text="", fg_color="transparent", width=size, height=size)
        self._render()

    # ── public API ────────────────────────────────────────────────────────
    def set_phase(self, label: str, color: str, unit: str = "Mbps",
                  auto_max: float = GAUGE_MAX_DEFAULT):
        self._phase_label = label
        self._color = color
        self._unit = unit
        self._max = auto_max
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
        self._phase_label = ""
        self._render()

    # ── animation ─────────────────────────────────────────────────────────
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

    # ── render ────────────────────────────────────────────────────────────
    def _render(self):
        S = self._size
        ss = self.SS
        W = S * ss
        img = Image.new("RGBA", (W, W), _hex_rgb(BG) + (255,))
        d = ImageDraw.Draw(img)

        cx, cy = W / 2, W / 2 + 6 * ss
        r_outer = W / 2 - 20 * ss
        track_w = 10 * ss

        # Track arc (outline look) — draw as a thin arc stroke
        bbox = [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer]
        start_a = self.START_DEG
        # PIL's arc uses angles measured clockwise from +x axis in PIL coordinate
        # system where y grows DOWN — so "start" visually at 150° upper-left means
        # start=150, end=150+240=390 (i.e. 30). We'll compute the visual-style
        # sweep manually.

        # Draw full track
        d.arc(bbox, start=start_a, end=start_a + self.SWEEP_DEG,
              fill=_hex_rgb(TRACK) + (255,), width=int(track_w))

        # Draw filled portion
        pct = max(0.0, min(1.0, self._value / self._max)) if self._max > 0 else 0.0
        if pct > 0.005:
            end_a = start_a + self.SWEEP_DEG * pct
            d.arc(bbox, start=start_a, end=end_a,
                  fill=_hex_rgb(self._color) + (255,), width=int(track_w))

        # Tick marks at 11 positions
        for i in range(11):
            t = i / 10
            ang = math.radians(start_a + self.SWEEP_DEG * t)
            r1 = r_outer - track_w - 6 * ss
            r2 = r_outer - track_w - 14 * ss
            x1, y1 = cx + math.cos(ang) * r1, cy + math.sin(ang) * r1
            x2, y2 = cx + math.cos(ang) * r2, cy + math.sin(ang) * r2
            d.line([(x1, y1), (x2, y2)],
                   fill=_hex_rgb(TEXT_DIM) + (255,), width=int(2 * ss))

        # Needle — thin triangle polygon, pointing from center to current value
        ang = math.radians(start_a + self.SWEEP_DEG * pct)
        tip_r = r_outer - track_w - 4 * ss
        tip_x = cx + math.cos(ang) * tip_r
        tip_y = cy + math.sin(ang) * tip_r
        # base of triangle perpendicular at center (thin)
        perp = ang + math.pi / 2
        base_half = 5 * ss
        bx1 = cx + math.cos(perp) * base_half
        by1 = cy + math.sin(perp) * base_half
        bx2 = cx - math.cos(perp) * base_half
        by2 = cy - math.sin(perp) * base_half
        d.polygon([(tip_x, tip_y), (bx1, by1), (bx2, by2)],
                  fill=_hex_rgb(self._color) + (255,))

        # Hub
        hub_r = 9 * ss
        d.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r],
                  fill=_hex_rgb(BG) + (255,),
                  outline=_hex_rgb(self._color) + (255,), width=int(3 * ss))

        # Downscale for antialiasing
        img = img.resize((S, S), Image.LANCZOS)

        # Text is drawn on the downsampled image for crisp native-resolution text
        d2 = ImageDraw.Draw(img)
        self._draw_texts(d2, S)

        try:
            photo = ImageTk.PhotoImage(img)
        except Exception:
            return
        self._img_ref = photo  # prevent GC
        try:
            self.configure(image=photo, text="")
        except Exception:
            pass

    def _draw_texts(self, d: ImageDraw.ImageDraw, S: int):
        # Use default font since PIL's truetype lookup is unreliable in PyInstaller
        cx = S // 2
        cy = S // 2 + 6

        # Value
        val_txt = f"{self._value:.2f}" if self._value < 100 else f"{self._value:.1f}"

        # Try to load a TTF for nicer numbers; fall back to default
        try:
            from PIL import ImageFont
            big = ImageFont.truetype("segoeuib.ttf", 48)
            small = ImageFont.truetype("segoeui.ttf", 12)
            label = ImageFont.truetype("segoeuib.ttf", 11)
        except Exception:
            from PIL import ImageFont
            big = ImageFont.load_default()
            small = ImageFont.load_default()
            label = ImageFont.load_default()

        # Phase label (top)
        if self._phase_label:
            tw = d.textlength(self._phase_label, font=label)
            d.text((cx - tw / 2, cy - 60), self._phase_label,
                   fill=_hex_rgb(self._color) + (255,), font=label)

        # Big value
        tw = d.textlength(val_txt, font=big)
        d.text((cx - tw / 2, cy - 16), val_txt,
               fill=_hex_rgb(TEXT) + (255,), font=big)

        # Unit
        tw = d.textlength(self._unit, font=small)
        d.text((cx - tw / 2, cy + 40), self._unit,
               fill=_hex_rgb(TEXT_DIM) + (255,), font=small)


# ── Speedtest runner ──────────────────────────────────────────────────────
class SpeedTestRunner:
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
        result = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "ping_ms": None, "jitter_ms": None, "loss_pct": None,
            "download_mbps": 0.0, "upload_mbps": 0.0,
            "ip": "-", "isp": "-", "server": "-", "city": "-",
        }

        self.on_status("Zjišťuji připojení…")
        meta = _fetch_meta()
        result.update(meta)
        self.on_meta(meta)
        if self._stop.is_set(): return

        # PING
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

        # DOWNLOAD
        self.on_phase("download", "Mbps", GAUGE_MAX_DEFAULT)
        self.on_status("Měřím stahování…")
        dl = self._measure_download(25 * 1024 * 1024, 10.0)
        result["download_mbps"] = round(dl, 2)
        if self._stop.is_set(): return

        # UPLOAD
        self.on_phase("upload", "Mbps", max(100.0, dl * 0.9))
        self.on_status("Měřím odesílání…")
        ul = self._measure_upload(10 * 1024 * 1024, 10.0)
        result["upload_mbps"] = round(ul, 2)

        self.on_status("✓ Test dokončen")
        self.on_done(result)

    def _measure_download(self, bytes_: int, cap_s: float) -> float:
        url = DL_URL.format(bytes=bytes_)
        req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubSpeedTest/1.0"})
        total = 0
        samples = []
        start = time.perf_counter()
        last = start
        last_bytes = 0
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
                        last = now
                        last_bytes = total
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

    def _measure_upload(self, bytes_: int, cap_s: float) -> float:
        import http.client, ssl
        payload = b"x" * (64 * 1024)
        total = 0
        samples = []
        start = time.perf_counter()
        last = start
        last_bytes = 0
        try:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection("speed.cloudflare.com", 443,
                                               timeout=15, context=ctx)
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
                    last = now
                    last_bytes = total
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


# ── Main app ──────────────────────────────────────────────────────────────
class SpeedTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            self.attributes("-alpha", 0.0)
            self.withdraw()
        except Exception:
            pass
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}+220+120")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        ctk.set_appearance_mode("dark")

        self._history = _load_history()
        self._runner = None
        self._history_visible = False
        self._history_win = None

        self._build()
        self.after(20, self._reveal)
        # Pre-fetch connection metadata so Public IP / ISP / City populate
        # before the user runs their first test.
        threading.Thread(target=self._bg_prefetch_meta, daemon=True).start()

    def _bg_prefetch_meta(self):
        meta = _fetch_meta()
        try:
            self.after(0, self._on_meta, meta)
        except Exception:
            pass

    def _reveal(self):
        try:
            self.update_idletasks()
            self.deiconify()
            self.update_idletasks()
            self.lift()
        except Exception:
            pass

        def step(a: float):
            try:
                self.attributes("-alpha", min(1.0, 1.0 - (1.0 - a) ** 2))
            except Exception:
                return
            if a < 1.0:
                self.after(16, lambda: step(min(1.0, a + 0.14)))

        step(0.12)

    def _build(self):
        # Top bar — title left, history button right
        top = ctk.CTkFrame(self, fg_color=BG, height=56)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="SpeedTest",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=TEXT).pack(side="left", padx=24, pady=16)

        ctk.CTkButton(
            top, text="Historie",
            fg_color="transparent", hover_color=CARD,
            text_color=TEXT_DIM,
            font=ctk.CTkFont("Segoe UI", 11),
            width=90, height=32, corner_radius=8,
            command=self._toggle_history,
        ).pack(side="right", padx=16, pady=12)

        # Gauge on plain BG (no card)
        gauge_wrap = ctk.CTkFrame(self, fg_color=BG)
        gauge_wrap.pack(fill="both", expand=True)

        self._gauge = Gauge(gauge_wrap, size=360)
        self._gauge.pack(pady=(8, 0))

        self._status_label = ctk.CTkLabel(
            gauge_wrap, text="Klikni START pro zahájení testu",
            font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT_DIM
        )
        self._status_label.pack(pady=(8, 4))

        # Metrics row — flat, minimal
        row = ctk.CTkFrame(gauge_wrap, fg_color=BG)
        row.pack(pady=(8, 8))

        self._m_ping   = self._metric(row, "PING",     "—", "ms",   GREEN)
        self._m_jitter = self._metric(row, "JITTER",   "—", "ms",   BLUE)
        self._m_dl     = self._metric(row, "DOWNLOAD", "—", "Mbps", ORANGE)
        self._m_ul     = self._metric(row, "UPLOAD",   "—", "Mbps", ORANGE_HI)

        for m in (self._m_ping, self._m_jitter, self._m_dl, self._m_ul):
            m.pack(side="left", padx=12)

        # Extended results card — Public IP, ISP, Server, Location
        info_card = ctk.CTkFrame(gauge_wrap, fg_color=CARD,
                                  corner_radius=10, border_width=1,
                                  border_color=BORDER)
        info_card.pack(fill="x", padx=40, pady=(4, 6))
        info_card.grid_columnconfigure(1, weight=1)
        self._info_fields = {}
        for r, (key, lbl) in enumerate([
            ("ip",     "Veřejná IP"),
            ("isp",    "Poskytovatel"),
            ("server", "Testovací server"),
            ("city",   "Lokalita"),
        ]):
            ctk.CTkLabel(info_card, text=lbl,
                         font=ctk.CTkFont("Segoe UI", 9),
                         text_color=TEXT_DIM, anchor="w").grid(
                row=r, column=0, sticky="w", padx=(12, 10), pady=(6 if r == 0 else 2, 6 if r == 3 else 2))
            val = ctk.CTkLabel(info_card, text="—",
                               font=ctk.CTkFont("Segoe UI", 10, "bold"),
                               text_color=TEXT, anchor="e")
            val.grid(row=r, column=1, sticky="e",
                     padx=(0, 12), pady=(6 if r == 0 else 2, 6 if r == 3 else 2))
            self._info_fields[key] = val

        # Start button
        self._start_btn = ctk.CTkButton(
            gauge_wrap, text="START",
            fg_color=ORANGE, hover_color=ORANGE_HI, text_color="#0a0a0f",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            width=160, height=44, corner_radius=22,
            command=self._start_test,
        )
        self._start_btn.pack(pady=(4, 20))

    def _metric(self, parent, label, value, unit, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        # Small top label keeps the metric color (PING=green, DL=orange, …)
        ctk.CTkLabel(frame, text=label,
                     font=ctk.CTkFont("Segoe UI", 8, "bold"),
                     text_color=color).pack()
        # Numeric value is always white for legibility on the dark BG.
        val = ctk.CTkLabel(
            frame, text=f"{value} {unit}",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=TEXT,
        )
        val.pack()
        frame._val = val
        frame._unit = unit
        frame._color = color
        return frame

    def _set_metric(self, frame, value):
        if value is None:
            frame._val.configure(text=f"— {frame._unit}")
        else:
            frame._val.configure(text=f"{value} {frame._unit}")

    # ── actions ───────────────────────────────────────────────────────────
    def _start_test(self):
        if self._runner is not None:
            return
        self._start_btn.configure(text="Probíhá…", state="disabled")
        for m in (self._m_ping, self._m_jitter, self._m_dl, self._m_ul):
            self._set_metric(m, None)
        for v in self._info_fields.values():
            v.configure(text="—")

        self._runner = SpeedTestRunner(
            on_phase=lambda n, u, g: self.after(0, self._on_phase, n, u, g),
            on_sample=lambda v: self.after(0, self._gauge.set_value, v),
            on_meta=lambda m: self.after(0, self._on_meta, m),
            on_done=lambda r: self.after(0, self._on_done, r),
            on_status=lambda s: self.after(0, self._status_label.configure, {"text": s}),
        )
        self._runner.run()

    def _on_phase(self, name, unit, gmax):
        colors = {"ping": GREEN, "download": ORANGE, "upload": ORANGE_HI}
        labels = {"ping": "ODEZVA", "download": "STAHOVÁNÍ", "upload": "ODESÍLÁNÍ"}
        self._gauge.set_phase(labels.get(name, name.upper()),
                              colors.get(name, ORANGE),
                              unit=unit, auto_max=gmax)

    def _on_meta(self, meta: dict):
        for key, lbl in self._info_fields.items():
            v = meta.get(key, "-") or "-"
            lbl.configure(text=v if v != "-" else "—")

    def _on_done(self, result: dict):
        self._runner = None
        self._start_btn.configure(text="NOVÝ TEST", state="normal")

        self._set_metric(self._m_ping,   result.get("ping_ms"))
        self._set_metric(self._m_jitter, result.get("jitter_ms"))
        self._m_dl._val.configure(text=f"{result['download_mbps']:.1f} Mbps")
        self._m_ul._val.configure(text=f"{result['upload_mbps']:.1f} Mbps")

        self._gauge.set_phase("VÝSLEDEK", ORANGE, unit="Mbps",
                              auto_max=max(100.0, result["download_mbps"] * 1.15))
        self._gauge.set_final(result["download_mbps"])

        self._history.append(result)
        _save_history(self._history)
        if self._history_win is not None and self._history_win.winfo_exists():
            self._render_history()

    # ── History drawer (in-window, right side overlay) ────────────────────
    def _toggle_history(self):
        # If drawer exists → hide it (speedtest stays visible, unchanged)
        if self._history_win is not None and self._history_win.winfo_exists():
            try:
                self._history_win.place_forget()
                self._history_win.destroy()
            except Exception:
                pass
            self._history_win = None
            return

        # Build drawer as a child of self (CTk root) so it overlays the
        # gauge area. Use .place() for true overlay on top of siblings.
        drawer = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0,
                              border_width=0)
        # Right 60 % of window (≈ 300 px on a 500 px window) slides in.
        drawer.place(relx=0.40, rely=0.0, relwidth=0.60, relheight=1.0)
        # Left separator (1-px "border")
        ctk.CTkFrame(drawer, fg_color=BORDER, width=1).place(
            relx=0, rely=0, relheight=1.0)

        header = ctk.CTkFrame(drawer, fg_color=CARD)
        header.pack(fill="x", padx=14, pady=(14, 4))
        ctk.CTkLabel(header, text="Historie měření",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT).pack(side="left")
        # Close X in the corner
        ctk.CTkButton(
            header, text="✕",
            fg_color="transparent", hover_color=BG, text_color=TEXT_DIM,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            width=28, height=28, corner_radius=6,
            command=self._toggle_history,
        ).pack(side="right")

        meta = ctk.CTkFrame(drawer, fg_color=CARD)
        meta.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(meta, text=f"{len(self._history)} testů",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=TEXT_DIM).pack(side="left")

        actions = ctk.CTkFrame(drawer, fg_color=CARD)
        actions.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkButton(
            actions, text="Vymazat",
            fg_color=BG, hover_color=RED, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 10),
            height=28, width=80, corner_radius=6,
            command=self._clear_history,
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Export JSON",
            fg_color=BG, hover_color=ORANGE, text_color=TEXT,
            font=ctk.CTkFont("Segoe UI", 10),
            height=28, width=110, corner_radius=6,
            command=self._export_history,
        ).pack(side="left", padx=(6, 0))

        self._history_scroll = ctk.CTkScrollableFrame(drawer, fg_color=CARD)
        self._history_scroll.pack(fill="both", expand=True, padx=8, pady=(4, 12))

        # Always on top of siblings inside this window
        drawer.lift()

        self._history_win = drawer
        self._render_history()

    def _render_history(self):
        if self._history_win is None or not self._history_win.winfo_exists():
            return
        for w in self._history_scroll.winfo_children():
            w.destroy()

        if not self._history:
            ctk.CTkLabel(self._history_scroll, text="Zatím žádné měření",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=TEXT_DIM).pack(pady=20)
            return

        for item in reversed(self._history[-HISTORY_MAX:]):
            self._render_history_card(item)

    def _render_history_card(self, item: dict):
        card = ctk.CTkFrame(self._history_scroll, fg_color=CARD,
                            corner_radius=8, border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=4, pady=3)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 2))
        ts = item.get("ts", "")[:16].replace("T", " ")
        ctk.CTkLabel(top, text=ts,
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=TEXT).pack(side="left")
        isp = (item.get("isp") or "—")
        if len(isp) > 22: isp = isp[:20] + "…"
        ctk.CTkLabel(top, text=isp,
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=TEXT_DIM).pack(side="right")

        mid = ctk.CTkFrame(card, fg_color="transparent")
        mid.pack(fill="x", padx=12, pady=(0, 10))
        for label, val, color in [
            ("Ping", f"{item.get('ping_ms', '—')} ms" if item.get('ping_ms') is not None else "— ms", GREEN),
            ("DL",   f"{item.get('download_mbps', 0):.1f}", ORANGE),
            ("UL",   f"{item.get('upload_mbps', 0):.1f}",   ORANGE_HI),
        ]:
            col = ctk.CTkFrame(mid, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(col, text=label,
                         font=ctk.CTkFont("Segoe UI", 8),
                         text_color=TEXT_DIM).pack(anchor="w")
            ctk.CTkLabel(col, text=val,
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=color).pack(anchor="w")

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


def main():
    try:
        app = SpeedTestApp()
        app.mainloop()
    except Exception as e:
        import traceback
        from tkinter import messagebox
        try:
            messagebox.showerror("ZeddiHub SpeedTest",
                                 f"{e}\n\n{traceback.format_exc()}")
        except Exception:
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
