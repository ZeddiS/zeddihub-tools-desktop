"""
ZeddiHub Tools - eDPI Calculator panel.
Extracted from GameToolsPanel for v2.1.0.
"""

import customtkinter as ctk

from .game_tools import GameToolsPanel


class EDPIPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        GameToolsPanel._build_edpi(self, self)

    _recalc_edpi = GameToolsPanel._recalc_edpi
