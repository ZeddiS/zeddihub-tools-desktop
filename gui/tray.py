"""
ZeddiHub Tools - System tray icon integration.
Shows icon in the Windows notification area with a right-click context menu.
Dynamic tool shortcuts are loaded from the webhosting JSON.
"""

import threading
import json
import urllib.request
from pathlib import Path
from typing import Optional

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_OK = True
except ImportError:
    TRAY_OK = False

TRAY_TOOLS_URL = "https://files.zeddihub.eu/tools/tray_tools.json"
ASSETS_DIR = Path(__file__).parent.parent / "assets"


def _make_fallback_icon() -> "Image.Image":
    """Create a simple orange circle as fallback icon."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, 30, 30], fill="#f0a500")
    draw.text((9, 8), "ZH", fill="#0c0c0c")
    return img


def _load_icon_image() -> "Image.Image":
    for name in ["icon.ico", "logo_icon.png", "logo_transparent.png", "logo.png"]:
        p = ASSETS_DIR / name
        if p.exists():
            try:
                img = Image.open(p)
                img = img.convert("RGBA")
                img = img.resize((32, 32), Image.LANCZOS)
                return img
            except Exception:
                pass
    return _make_fallback_icon()


class TrayIcon:
    def __init__(self, app):
        """
        app: MainWindow instance.
        Communication back to the GUI must always go through app.after().
        """
        self._app = app
        self._icon: Optional["pystray.Icon"] = None
        self._tray_tools: list = []
        self._running = False

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        """Start tray icon in background thread. Safe to call from main thread."""
        if not TRAY_OK:
            return
        self._running = True
        self._fetch_tools_then_start()

    def stop(self):
        """Stop and remove tray icon."""
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def show_notification(self, title: str, message: str):
        """Show a system tray notification balloon."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fetch_tools_then_start(self):
        def _run():
            try:
                req = urllib.request.Request(
                    TRAY_TOOLS_URL,
                    headers={"User-Agent": "ZeddiHubTools/1.3.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    self._tray_tools = data.get("tools", [])
            except Exception:
                self._tray_tools = []
            self._start_icon()

        threading.Thread(target=_run, daemon=True).start()

    def _start_icon(self):
        if not self._running:
            return
        image = _load_icon_image()
        menu = self._build_menu()
        self._icon = pystray.Icon(
            "ZeddiHub Tools",
            image,
            "ZeddiHub Tools",
            menu,
        )
        # Run blocks until stop() is called
        self._icon.run()

    def _build_menu(self) -> "pystray.Menu":
        items = [
            pystray.MenuItem(
                "ZeddiHub Tools",
                self._on_open,
                default=True,
            ),
            pystray.Menu.SEPARATOR,
        ]

        # Dynamic tools submenu
        if self._tray_tools:
            tool_menu_items = []
            for tool in self._tray_tools:
                label = tool.get("label", "?")
                nav_id = tool.get("nav_id", "home")
                tool_menu_items.append(
                    pystray.MenuItem(
                        label,
                        self._make_nav_action(nav_id),
                    )
                )
            items.append(
                pystray.MenuItem(
                    "Nástroje",
                    pystray.Menu(*tool_menu_items),
                )
            )
            items.append(pystray.Menu.SEPARATOR)

        items += [
            pystray.MenuItem("⚙ Nastavení", self._make_nav_action("settings")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕ Zavřít", self._on_quit),
        ]

        return pystray.Menu(*items)

    def _make_nav_action(self, nav_id: str):
        def _action(icon=None, item=None):
            self._app.after(0, self._show_and_navigate, nav_id)
        return _action

    def _on_open(self, icon=None, item=None):
        self._app.after(0, self._show_window)

    def _on_quit(self, icon=None, item=None):
        self._app.after(0, self._do_quit)

    def _show_window(self):
        """Must be called from main thread via after()."""
        self._app.deiconify()
        self._app.lift()
        self._app.focus_force()
        self._app.state("normal")

    def _show_and_navigate(self, nav_id: str):
        self._show_window()
        self._app.after(50, self._app._navigate, nav_id)

    def _do_quit(self):
        """Full application exit from tray. Must be called from main thread."""
        self.stop()
        if hasattr(self._app, "_quit_app"):
            self._app._quit_app()
        else:
            try:
                self._app.destroy()
            except Exception:
                pass
