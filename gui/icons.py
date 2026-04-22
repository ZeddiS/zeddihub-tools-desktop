"""
ZeddiHub Tools - FontAwesome 6 Free icon rendering.
Downloads FA fonts on first run and renders icons as CTkImage
for use with image= and compound="left" in CTkButton / CTkLabel.
"""

import threading
import urllib.request
from pathlib import Path
from typing import Optional

import customtkinter as ctk

try:
    from PIL import Image, ImageFont
    PIL_OK = True
except ImportError:
    PIL_OK = False

ASSETS_DIR = Path(__file__).parent.parent / "assets"
FONTS_DIR  = ASSETS_DIR / "fonts"
FA_SOLID   = FONTS_DIR / "fa-solid-900.ttf"
FA_BRANDS  = FONTS_DIR / "fa-brands-400.ttf"

_CDN_SOLID  = "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/webfonts/fa-solid-900.ttf"
_CDN_BRANDS = "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/webfonts/fa-brands-400.ttf"

_img_cache:  dict = {}
_font_cache: dict = {}
_dl_started: bool = False

# ── FA 6 Free unicode code-points ─────────────────────────────────────────────
CHARS: dict[str, str] = {
    # Navigation / layout
    "house":                "\uf015",
    "home":                 "\uf015",
    "laptop":               "\uf109",
    "bell":                 "\uf0f3",
    "bell-slash":           "\uf1f6",
    "gear":                 "\uf013",
    "gears":                "\uf085",
    "link":                 "\uf0c1",
    "bars":                 "\uf0c9",
    "angle-right":          "\uf105",
    "angle-down":           "\uf107",
    "chevron-right":        "\uf054",
    "chevron-down":         "\uf078",
    "moon":                 "\uf186",
    "sun":                  "\uf185",
    "circle-half-stroke":   "\uf042",
    "sliders":              "\uf1de",
    # User / Auth
    "user":                 "\uf007",
    "users":                "\uf0c0",
    "user-plus":            "\uf234",
    "user-gear":            "\uf4fe",
    "lock":                 "\uf023",
    "lock-open":            "\uf3c1",
    "key":                  "\uf084",
    "shield":               "\uf132",
    "shield-halved":        "\uf3ed",
    "id-badge":             "\uf2c1",
    "right-from-bracket":   "\uf2f5",
    "right-to-bracket":     "\uf2f6",
    "address-card":         "\uf2bb",
    # Server / Network
    "server":               "\uf233",
    "display":              "\uf390",
    "desktop":              "\uf108",
    "satellite-dish":       "\uf7c0",
    "tower-broadcast":      "\ue4d9",
    "wifi":                 "\uf1eb",
    "network-wired":        "\uf6ff",
    "globe":                "\uf0ac",
    "map-marker":           "\uf041",
    "location-dot":         "\uf3c5",
    "signal":               "\uf012",
    "ethernet":             "\uf796",
    "plug":                 "\uf1e6",
    # Game tools
    "crosshairs":           "\uf05b",
    "gun":                  "\ue19b",
    "file-pen":             "\uf31c",
    "gamepad":              "\uf11b",
    "cart-shopping":        "\uf07a",
    "puzzle-piece":         "\uf12e",
    "keyboard":             "\uf11c",
    "table-tennis":         "\ue3db",
    "gamepad-alt":          "\uf11b",
    # Actions
    "arrows-rotate":        "\uf021",
    "rotate":               "\uf021",
    "play":                 "\uf04b",
    "stop":                 "\uf04d",
    "pause":                "\uf04c",
    "plus":                 "\uf067",
    "minus":                "\uf068",
    "xmark":                "\uf00d",
    "check":                "\uf00c",
    "trash":                "\uf1f8",
    "trash-can":            "\uf2ed",
    "pen":                  "\uf304",
    "pen-to-square":        "\uf044",
    "copy":                 "\uf0c5",
    "download":             "\uf019",
    "upload":               "\uf093",
    "floppy-disk":          "\uf0c7",
    "save":                 "\uf0c7",
    "expand":               "\uf065",
    "compress":             "\uf066",
    "magnifying-glass":     "\uf002",
    "search":               "\uf002",
    "filter":               "\uf0b0",
    "sort":                 "\uf0dc",
    "share":                "\uf064",
    "external-link":        "\uf08e",
    "arrow-right":          "\uf061",
    "arrow-left":           "\uf060",
    "arrow-up":             "\uf062",
    "arrow-down":           "\uf063",
    # Files / Data
    "folder":               "\uf07b",
    "folder-open":          "\uf07c",
    "clipboard":            "\uf328",
    "clipboard-list":       "\uf46d",
    "list":                 "\uf03a",
    "list-ul":              "\uf0ca",
    "file":                 "\uf15b",
    "file-code":            "\uf1c9",
    "file-lines":           "\uf15c",
    "hard-drive":           "\uf0a0",
    "database":             "\uf1c0",
    "box-archive":          "\uf187",
    # Info / Status
    "circle-info":          "\uf05a",
    "info":                 "\uf129",
    "triangle-exclamation": "\uf071",
    "circle-exclamation":   "\uf06a",
    "star":                 "\uf005",
    "thumbtack":            "\uf08d",
    "circle":               "\uf111",
    "circle-dot":           "\uf192",
    "circle-check":         "\uf058",
    "circle-xmark":         "\uf057",
    "square-check":         "\uf14a",
    # System / PC
    "microchip":            "\uf2db",
    "memory":               "\uf538",
    "power-off":            "\uf011",
    "chart-line":           "\uf201",
    "chart-bar":            "\uf080",
    "clock":                "\uf017",
    "terminal":             "\uf120",
    "wrench":               "\uf0ad",
    "screwdriver-wrench":   "\uf7d9",
    "temperature-half":     "\uf2c9",
    "gauge":                "\uf624",
    "gauge-high":           "\uf625",
    "gauge-simple":         "\uf629",
    "clock-rotate-left":    "\uf1da",
    "chart-simple":         "\ue473",
    "bolt":                 "\uf0e7",
    # Communication
    "comment":              "\uf075",
    "comments":             "\uf086",
    "paper-plane":          "\uf1d8",
    "envelope":             "\uf0e0",
    "at":                   "\uf1fa",
    # Brands (need fa-brands-400.ttf)
    "github":               "\uf09b",
    "discord":              "\uf392",
    "steam":                "\uf1b6",
    "chrome":               "\uf268",
}

BRAND_ICONS: frozenset = frozenset({"github", "discord", "steam", "chrome"})


# ── Font management ────────────────────────────────────────────────────────────

def _download_fonts():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for url, path in [(_CDN_SOLID, FA_SOLID), (_CDN_BRANDS, FA_BRANDS)]:
        if path.exists():
            continue
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "ZeddiHubTools/1.5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                path.write_bytes(resp.read())
        except Exception:
            pass


def preload():
    """Download FA fonts in background at app startup."""
    global _dl_started
    if _dl_started:
        return
    _dl_started = True
    threading.Thread(target=_download_fonts, daemon=True).start()


def _get_font(size: int, brand: bool = False):
    if not PIL_OK:
        return None
    key = (size, brand)
    if key in _font_cache:
        return _font_cache[key]
    font_path = FA_BRANDS if brand else FA_SOLID
    if not font_path.exists():
        _download_fonts()
    if not font_path.exists():
        return None
    try:
        fnt = ImageFont.truetype(str(font_path), size)
        _font_cache[key] = fnt
        return fnt
    except Exception:
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def icon(name: str, size: int = 16, color: str = "#e8e8e8") -> Optional["ctk.CTkImage"]:
    """
    Return a CTkImage for the named FA icon, or None on failure.

    Usage in CTkButton / CTkLabel:
        btn = ctk.CTkButton(parent,
                            image=icon("gear", 14, "#ffffff"),
                            text=" Settings",
                            compound="left")
    """
    if not PIL_OK:
        return None
    key = (name, size, color)
    if key in _img_cache:
        return _img_cache[key]

    char = CHARS.get(name)
    if not char:
        return None

    fnt = _get_font(size, name in BRAND_ICONS)
    if not fnt:
        return None

    try:
        from PIL import Image, ImageDraw
        pad = max(2, size // 6)
        dim = size + pad * 2
        img = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            bbox = fnt.getbbox(char)
        except AttributeError:
            # Pillow < 9.2
            w, h = fnt.getsize(char)
            bbox = (0, 0, w, h)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (dim - w) // 2 - bbox[0]
        y = (dim - h) // 2 - bbox[1]
        r, g, b = _hex_rgb(color)
        draw.text((x, y), char, font=fnt, fill=(r, g, b, 255))
        ct = ctk.CTkImage(img, size=(size, size))
        _img_cache[key] = ct
        return ct
    except Exception:
        return None


def _hex_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
