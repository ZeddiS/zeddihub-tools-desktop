"""
ZeddiHub Tools — PC tools sub-panels.

Thin wrappers that reuse PCToolsPanel's _build_* methods so each PC-tools
section renders as its own sidebar entry instead of a single tabview.
"""

import customtkinter as ctk

from .pc_tools import PCToolsPanel


class _PCSubPanelBase(PCToolsPanel):
    """Inherits PCToolsPanel state setup; overrides _build to render a
    single section instead of the full tabview."""

    _build_method: str = ""

    def _build(self):
        if not self._build_method:
            return
        container = ctk.CTkFrame(self, fg_color=self.theme.get("sidebar_bg", "#141420"))
        container.pack(fill="both", expand=True, padx=12, pady=12)
        method = getattr(self, self._build_method, None)
        if method is not None:
            method(container)


class PCSysInfoPanel(_PCSubPanelBase):
    _build_method = "_build_sysinfo"


class PCNetToolsPanel(_PCSubPanelBase):
    _build_method = "_build_nettools"


class PCUtilityPanel(_PCSubPanelBase):
    _build_method = "_build_utility"


class PCGameOptPanel(_PCSubPanelBase):
    _build_method = "_build_game_opt"


class PCAdvancedPanel(_PCSubPanelBase):
    _build_method = "_build_advanced"
