"""
ZeddiHub Tools — PySide6 PoC.

Minimální skeleton, který replikuje vzhled a chování současné aplikace
v Qt:
  • Header s logo / názvem / theme toggle
  • Levý sidebar s navigací (3 ukázkové sekce)
  • Content area s "panelem" (HomePage = 6 dlaždic doporučených nástrojů
    + HTTP fetch z https://zeddihub.eu/tools/data/recommended.json)
  • Demonstrace: minimize → restore = ŽÁDNÉ černé obdélníky, žádný
    redraw walker, žádný panel pool. Qt to řeší nativně.
  • Tray icon přes QSystemTrayIcon (10 řádků kódu, žádný pystray)

Spuštění:
    cd poc/pyside6
    python -m venv .venv
    .venv\\Scripts\\activate     (Windows)  /  source .venv/bin/activate (Mac/Linux)
    pip install -r requirements.txt
    python main.py

Build standalone EXE (volitelné):
    pip install pyinstaller
    pyinstaller --noconfirm --onefile --windowed --name ZeddiHubPySide6 main.py
"""

from __future__ import annotations

import sys
import json
import urllib.request
from typing import Optional

from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QAction, QIcon, QPalette, QColor, QPixmap, QPainter
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, QLineEdit,
    QStackedWidget, QSystemTrayIcon, QMenu, QSizePolicy, QSpacerItem,
)


# ───────────────────────────── Theme ──────────────────────────────────────
DARK = {
    "bg":          "#0c0c0c",
    "sidebar_bg":  "#141420",
    "header_bg":   "#0f0f1a",
    "content_bg":  "#0a0a14",
    "card_bg":     "#1a1a28",
    "card_hover":  "#22222e",
    "border":      "#2a2a3a",
    "primary":     "#f0a500",
    "primary_hover": "#d99400",
    "text":        "#f0f0f0",
    "text_muted":  "#9a9aa6",
    "accent":      "#5b9cf6",
}

LIGHT = {
    "bg":          "#f5f5f7",
    "sidebar_bg":  "#ffffff",
    "header_bg":   "#ffffff",
    "content_bg":  "#fafafa",
    "card_bg":     "#ffffff",
    "card_hover":  "#f5f5f5",
    "border":      "#e5e5e5",
    "primary":     "#f0a500",
    "primary_hover": "#d99400",
    "text":        "#1a1a1a",
    "text_muted":  "#6b6b6b",
    "accent":      "#0066cc",
}

RECOMMENDED_URL = "https://zeddihub.eu/tools/data/recommended.json"

FALLBACK_RECOMMENDED = [
    {"name": "CS2 Crosshair", "desc": "Vygeneruj svůj crosshair", "color": "#5b9cf6"},
    {"name": "CS2 Server CFG", "desc": "Nastavení herního serveru", "color": "#5b9cf6"},
    {"name": "CS:GO Crosshair", "desc": "CS:GO crosshair generátor", "color": "#fbbf24"},
    {"name": "Rust Server CFG", "desc": "Konfiguruj Rust server", "color": "#f97316"},
    {"name": "Keybind Generator", "desc": "Vizuální keybind editor", "color": "#a78bfa"},
    {"name": "Translator", "desc": "Hromadný překlad .json/.lang", "color": "#4ade80"},
]


# ───────────────────────────── Networking ─────────────────────────────────
class FetchWorker(QObject):
    """Background HTTP fetch — emit `done` signal s JSON listem nebo None."""

    done = Signal(object)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            req = urllib.request.Request(self.url, headers={"User-Agent": "ZeddiHubPoC/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode())
            if not isinstance(data, list):
                data = None
        except Exception:
            data = None
        self.done.emit(data)


# ───────────────────────────── Widgets ────────────────────────────────────
def make_card(parent: QWidget, theme: dict, *, padding: int = 16) -> QFrame:
    card = QFrame(parent)
    card.setStyleSheet(
        f"""
        QFrame {{
            background-color: {theme['card_bg']};
            border-radius: 12px;
        }}
        QFrame:hover {{
            background-color: {theme['card_hover']};
        }}
        """
    )
    card.setContentsMargins(padding, padding, padding, padding)
    return card


def make_button(text: str, *, theme: dict, primary: bool = False) -> QPushButton:
    btn = QPushButton(text)
    if primary:
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {theme['primary']};
                color: #0a0a0a;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {theme['primary_hover']}; }}
            """
        )
    else:
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {theme['text']};
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                text-align: left;
            }}
            QPushButton:hover {{ background-color: {theme['card_hover']}; }}
            """
        )
    btn.setCursor(Qt.PointingHandCursor)
    return btn


# ───────────────────────────── Panels ─────────────────────────────────────
class HomePanel(QWidget):
    """Reprezentativní panel: scroll area + grid karet + HTTP fetch.

    Demonstruje:
      • Žádný custom Canvas redraw — Qt rendruje native
      • Background QThread pro HTTP fetch — žádný tkinter `after()` hack
      • Hover state přes :hover pseudo-class v stylesheet
    """

    def __init__(self, theme: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = theme
        self._build()
        self._fetch_data()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Vítej zpět")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Doporučené nástroje pro rychlý přístup.")
        subtitle.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 13px;")
        layout.addWidget(subtitle)

        # Status label (replaced when data loads)
        self._status = QLabel("Načítám doporučené nástroje…")
        self._status.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 11px;")
        layout.addWidget(self._status)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {self.theme['content_bg']};")

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setSpacing(12)
        self._grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._grid_host)
        layout.addWidget(scroll, stretch=1)

        # Render with fallback first (instant), then refresh from network
        self._render_grid(FALLBACK_RECOMMENDED)

    def _fetch_data(self):
        self._thread = QThread()
        self._worker = FetchWorker(RECOMMENDED_URL)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_data)
        self._worker.done.connect(self._thread.quit)
        self._thread.start()

    def _on_data(self, data: Optional[list]):
        if data:
            self._status.setText(f"✓ {len(data)} nástrojů (live ze zeddihub.eu)")
            self._render_grid(data[:6])
        else:
            self._status.setText("⚠ Offline — zobrazen fallback")

    def _render_grid(self, items: list):
        # Wipe existing
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        cols = 3
        for i, item in enumerate(items):
            card = make_card(self._grid_host, self.theme, padding=18)
            card.setMinimumHeight(120)
            box = QVBoxLayout(card)
            box.setContentsMargins(18, 18, 18, 18)
            box.setSpacing(8)

            # Color strip
            strip = QFrame(card)
            strip.setFixedHeight(2)
            strip.setStyleSheet(f"background-color: {item.get('color', self.theme['primary'])}; border-radius: 1px;")
            box.addWidget(strip)

            name = QLabel(item.get("name", ""))
            name.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px; font-weight: bold;")
            box.addWidget(name)

            desc = QLabel(item.get("desc", ""))
            desc.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 11px;")
            desc.setWordWrap(True)
            box.addWidget(desc)
            box.addStretch(1)

            self._grid.addWidget(card, i // cols, i % cols)


class SettingsPanel(QWidget):
    """Druhý reprezentativní panel — formulář s entry / button / status."""

    def __init__(self, theme: dict, on_theme_toggle, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = theme
        self._on_theme_toggle = on_theme_toggle
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        title = QLabel("Nastavení")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Card with form
        card = make_card(self, self.theme, padding=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        section = QLabel("Vzhled")
        section.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px; font-weight: bold;")
        card_layout.addWidget(section)

        toggle_btn = make_button("Přepnout dark / light", theme=self.theme, primary=True)
        toggle_btn.clicked.connect(self._on_theme_toggle)
        card_layout.addWidget(toggle_btn)

        section2 = QLabel("Účet")
        section2.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px; font-weight: bold; margin-top: 12px;")
        card_layout.addWidget(section2)

        username_row = QHBoxLayout()
        username_row.addWidget(QLabel("Uživatelské jméno:"))
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("zeddi…")
        self._username_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {self.theme['card_hover']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 8px;
                border-radius: 6px;
            }}
            """
        )
        username_row.addWidget(self._username_input)
        card_layout.addLayout(username_row)

        layout.addWidget(card)
        layout.addStretch(1)


# ───────────────────────────── Main Window ────────────────────────────────
class MainWindow(QMainWindow):
    SIDEBAR_W = 240
    HEADER_H = 56

    def __init__(self):
        super().__init__()
        self.theme_name = "dark"
        self.theme = DARK

        self.setWindowTitle("ZeddiHub Tools — PySide6 PoC")
        self.resize(1200, 760)

        self._build_layout()
        self._setup_tray()
        self._navigate("home")

    def _build_layout(self):
        self.setStyleSheet(f"QMainWindow {{ background-color: {self.theme['bg']}; }}")

        central = QWidget()
        central.setStyleSheet(f"background-color: {self.theme['bg']};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        self._header = QFrame()
        self._header.setFixedHeight(self.HEADER_H)
        self._header.setStyleSheet(f"background-color: {self.theme['header_bg']};")
        h = QHBoxLayout(self._header)
        h.setContentsMargins(20, 8, 20, 8)

        logo_lbl = QLabel("ZeddiHub Tools")
        logo_lbl.setStyleSheet(f"color: {self.theme['primary']}; font-size: 16px; font-weight: bold;")
        h.addWidget(logo_lbl)
        h.addStretch(1)

        version = QLabel("v0.1.0 (PoC)")
        version.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 11px;")
        h.addWidget(version)

        root.addWidget(self._header)

        # ── Body (sidebar + content) ──
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Sidebar
        self._sidebar = QFrame()
        self._sidebar.setFixedWidth(self.SIDEBAR_W)
        self._sidebar.setStyleSheet(f"background-color: {self.theme['sidebar_bg']};")
        sb = QVBoxLayout(self._sidebar)
        sb.setContentsMargins(12, 16, 12, 16)
        sb.setSpacing(2)

        for label, nav_id in [("🏠  Domů", "home"), ("⚙  Nastavení", "settings")]:
            btn = make_button(label, theme=self.theme)
            btn.clicked.connect(lambda _, n=nav_id: self._navigate(n))
            sb.addWidget(btn)
        sb.addStretch(1)

        info = QLabel("PoC — PySide6 + Qt6")
        info.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 10px;")
        sb.addWidget(info)

        body.addWidget(self._sidebar)

        # Content
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background-color: {self.theme['content_bg']};")

        self._panels = {
            "home": HomePanel(self.theme),
            "settings": SettingsPanel(self.theme, on_theme_toggle=self._toggle_theme),
        }
        for nav_id, panel in self._panels.items():
            self._stack.addWidget(panel)

        body.addWidget(self._stack, stretch=1)

        body_widget = QWidget()
        body_widget.setLayout(body)
        root.addWidget(body_widget, stretch=1)

    def _navigate(self, nav_id: str):
        # QStackedWidget = panel switching is essentially free.
        # No destroy/rebuild, no Canvas redraw walker, no black rectangles.
        if nav_id in self._panels:
            self._stack.setCurrentWidget(self._panels[nav_id])

    def _setup_tray(self):
        # Generate a tiny orange logo pixmap on the fly
        pix = QPixmap(32, 32)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setBrush(QColor(self.theme["primary"]))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, 28, 28)
        p.end()
        self.setWindowIcon(QIcon(pix))

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(QIcon(pix), self)
        menu = QMenu()
        menu.addAction("Otevřít", self._restore_from_tray)
        menu.addSeparator()
        menu.addAction("Domů", lambda: (self._restore_from_tray(), self._navigate("home")))
        menu.addAction("Nastavení", lambda: (self._restore_from_tray(), self._navigate("settings")))
        menu.addSeparator()
        menu.addAction("Ukončit", QApplication.quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(
            lambda reason: self._restore_from_tray() if reason == QSystemTrayIcon.Trigger else None
        )
        self._tray.show()

    def _restore_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        # Minimize to tray on close (like the Tk app).
        # Qt natively re-renders widgets after hide()+show() — žádný black-rect bug.
        if hasattr(self, "_tray") and self._tray.isVisible():
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "ZeddiHub Tools",
                "Aplikace běží v systémové liště.",
                QSystemTrayIcon.Information, 2000,
            )
        else:
            event.accept()

    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = LIGHT if self.theme_name == "light" else DARK
        # Rebuild stack with new theme — panel state mostly stateless here.
        # In real app, panels would receive theme via signal and restyle in place.
        self.centralWidget().deleteLater()
        self._build_layout()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # tray keeps app running
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
