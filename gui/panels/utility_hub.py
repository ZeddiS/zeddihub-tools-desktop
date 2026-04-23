"""
ZeddiHub Tools — Utility Hub panel (v1.7.8).

Single panel that consolidates all Utility-like tools into one place using
a CTkTabview. Replaces the v1.7.5 sidebar split (separate sections for
Systém / Časovače / Makra / Procesy) per user feedback — the desired pattern
is the same as CS2 Player Tools (one sidebar entry, tabs inside).

Top-level tabs:
    • Systém     — nested tabview for 5 PC sub-panels
    • Časovače   — nested tabview for Stopky / Odpočet / Časovač
    • Makra      — embedded MacrosPanel
    • Procesy    — embedded ProcessesPanel
"""

from __future__ import annotations

import customtkinter as ctk


class UtilityHubPanel(ctk.CTkFrame):
    """Consolidated Utility hub — CS2-style tabbed container."""

    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build(self):
        th = self.theme

        tab = ctk.CTkTabview(self, fg_color=th.get("sidebar_bg", "#141420"))
        tab.pack(fill="both", expand=True, padx=16, pady=16)

        tab.add("💻 Systém")
        tab.add("⏱ Časovače")
        tab.add("🪄 Makra")
        tab.add("🧩 Procesy")

        self._build_system_tab(tab.tab("💻 Systém"))
        self._build_timers_tab(tab.tab("⏱ Časovače"))
        self._build_macros_tab(tab.tab("🪄 Makra"))
        self._build_processes_tab(tab.tab("🧩 Procesy"))

    # ── SYSTÉM — nested tabview for 5 PC sub-panels ────────────────────────
    def _build_system_tab(self, parent):
        # Lazy imports so panel load cost is amortised only when tab is opened.
        from .pc_subpanels import (
            PCSysInfoPanel,
            PCNetToolsPanel,
            PCUtilityPanel,
            PCGameOptPanel,
            PCAdvancedPanel,
        )

        th = self.theme
        inner = ctk.CTkTabview(parent, fg_color=th.get("card_bg", "#1a1a28"))
        inner.pack(fill="both", expand=True, padx=0, pady=0)

        inner.add("Info")
        inner.add("Síť")
        inner.add("Utility")
        inner.add("Hry")
        inner.add("Pokročilé")

        PCSysInfoPanel(inner.tab("Info"),    theme=th).pack(fill="both", expand=True)
        PCNetToolsPanel(inner.tab("Síť"),    theme=th).pack(fill="both", expand=True)
        PCUtilityPanel(inner.tab("Utility"), theme=th).pack(fill="both", expand=True)
        PCGameOptPanel(inner.tab("Hry"),     theme=th).pack(fill="both", expand=True)
        PCAdvancedPanel(inner.tab("Pokročilé"), theme=th).pack(fill="both", expand=True)

    # ── ČASOVAČE — nested tabview for 3 timer panels ──────────────────────
    def _build_timers_tab(self, parent):
        from .timers import StopkyPanel, OdpocetPanel, CasovacPanel

        th = self.theme
        inner = ctk.CTkTabview(parent, fg_color=th.get("card_bg", "#1a1a28"))
        inner.pack(fill="both", expand=True, padx=0, pady=0)

        inner.add("Stopky")
        inner.add("Odpočet")
        inner.add("Časovač")

        StopkyPanel(inner.tab("Stopky"),   theme=th).pack(fill="both", expand=True)
        OdpocetPanel(inner.tab("Odpočet"), theme=th).pack(fill="both", expand=True)
        CasovacPanel(inner.tab("Časovač"), theme=th).pack(fill="both", expand=True)

    # ── MAKRA — single embedded panel ─────────────────────────────────────
    def _build_macros_tab(self, parent):
        from .macros import MacrosPanel
        MacrosPanel(parent, theme=self.theme).pack(fill="both", expand=True)

    # ── PROCESY — single embedded panel ───────────────────────────────────
    def _build_processes_tab(self, parent):
        from .processes import ProcessesPanel
        ProcessesPanel(parent, theme=self.theme).pack(fill="both", expand=True)
