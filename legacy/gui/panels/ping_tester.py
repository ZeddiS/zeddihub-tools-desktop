"""
ZeddiHub Tools - Ping Tester panel.
Extracted from GameToolsPanel for v2.1.0.
"""

import customtkinter as ctk

from .game_tools import GameToolsPanel


class PingTesterPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        GameToolsPanel._build_ping(self, self)

    _tcp_ping_ms = GameToolsPanel._tcp_ping_ms
    _run_all_pings = GameToolsPanel._run_all_pings
    _clear_pings = GameToolsPanel._clear_pings
    _run_custom_ping = GameToolsPanel._run_custom_ping
