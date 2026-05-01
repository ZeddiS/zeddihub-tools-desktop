"""
ZeddiHub Tools - Sensitivity Converter panel.
Extracted from GameToolsPanel for v2.1.0.
"""

import customtkinter as ctk

from .game_tools import GameToolsPanel, _label, _card, SENS_GAMES  # reuse


class SensitivityPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        # Delegate to GameToolsPanel._build_sensitivity via a bound stub
        # Reuse the implementation by calling the unbound method on a shim
        # that has the required attributes set on `self`.
        GameToolsPanel._build_sensitivity(self, self)

    # Delegate recalc/load helpers used by bound callbacks
    _recalc_sens = GameToolsPanel._recalc_sens
    _load_win_sens = GameToolsPanel._load_win_sens
