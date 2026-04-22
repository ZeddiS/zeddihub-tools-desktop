"""
Placeholder panel for the Macros feature.

Real macro system (recorder + step builder + engine + hotkey manager + gallery)
lands in v1.7.6 per the roadmap locked in the v1.7.5 session. This placeholder
keeps the "Makra" sidebar section navigable so users can see what's coming.
"""

import customtkinter as ctk

from .. import icons
from ..widgets import make_page_title


class MacrosPlaceholderPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._build()

    def _build(self):
        th = self.theme
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=40, pady=40)

        make_page_title(
            root,
            "Makra — brzy přijde",
            th,
            subtitle="Profesionální systém maker pro CS2 / CS:GO / Rust i obecné použití.",
        ).pack(fill="x", anchor="w", pady=(0, 18))

        card = ctk.CTkFrame(
            root,
            fg_color=th.get("card_bg", th["secondary"]),
            corner_radius=th.get("radius_card", 14),
            border_width=1,
            border_color=th.get("divider", th.get("border", "#2a2a2a")),
        )
        card.pack(fill="x", pady=(0, 14))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=22)

        ctk.CTkLabel(
            inner,
            image=icons.icon("wand-magic-sparkles", 32, th["primary"]),
            text="",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Co bude obsahovat (v1.7.6):",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=th.get("text_strong", th["text"]),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        features = [
            ("circle-dot",  "Recorder — záznam klávesnice + myši přes globální hook"),
            ("list-check",  "Step Builder — vizuální skládání kroků v GUI"),
            ("keyboard",    "Hotkey manager — globální klávesové zkratky + detekce konfliktů"),
            ("code",        "Řídicí struktury — smyčky, podmínky, wait-for-pixel / wait-for-window"),
            ("clipboard",   "Text & schránka — type string, paste, šablony"),
            ("cloud-arrow-down", "Galerie — stažení doporučených maker od komunity"),
            ("file-arrow-up",    "Import / Export — sdílení maker jako JSON soubory"),
        ]
        for icon_name, desc in features:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row,
                image=icons.icon(icon_name, 14, th["primary"]),
                text="",
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=th.get("text", "#d0d0d0"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

        footer = ctk.CTkFrame(root, fg_color="transparent")
        footer.pack(fill="x")
        ctk.CTkLabel(
            footer,
            text="⚠ Makra v competitive hrách (CS2/CS:GO) mohou vést k VAC banu. Používej jen tam, kde je to bezpečné.",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=th.get("warning", "#f0a500"),
            anchor="w",
            wraplength=700,
            justify="left",
        ).pack(fill="x")
