"""
ZeddiHub Tools - About panel.
Statický informační panel: verze, autor, licence, technologie, odkazy.
N-12.
"""

import platform
import sys
import webbrowser
import customtkinter as ctk

from .. import icons

try:
    from ..locale import t
except ImportError:
    def t(key, **kw):
        return key

try:
    from ..updater import CURRENT_VERSION, GITHUB_RELEASES_URL
except ImportError:
    CURRENT_VERSION = "?"
    GITHUB_RELEASES_URL = "https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"


def _label(parent, text, font_size=12, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", font_size, "bold" if bold else "normal"),
                        text_color=color or "#f0f0f0", **kw)


def _card(parent, theme):
    return ctk.CTkFrame(parent, fg_color=theme["card_bg"], corner_radius=8)


class AboutPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._nav_callback = nav_callback
        self._build()

    def _build(self):
        th = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        # ── Header: logo + název aplikace ──────────────────────────────────
        hero = _card(scroll, th)
        hero.pack(fill="x", pady=(0, 10))

        _label(hero, "ZeddiHub Tools", 22, bold=True, color=th["primary"]
               ).pack(padx=20, pady=(18, 4), anchor="w")
        _label(hero, t("about_tagline"), 12, color=th["text_dim"]
               ).pack(padx=20, pady=(0, 14), anchor="w")

        # ── Verze a systém ─────────────────────────────────────────────────
        ver_card = _card(scroll, th)
        ver_card.pack(fill="x", pady=6)
        _label(ver_card, t("about_version_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")

        grid = ctk.CTkFrame(ver_card, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(0, 12))
        grid.grid_columnconfigure(1, weight=1)

        rows = [
            (t("about_app_version"), f"v{CURRENT_VERSION}"),
            (t("about_python_version"), platform.python_version()),
            (t("about_os"), f"{platform.system()} {platform.release()}"),
            (t("about_architecture"), platform.machine()),
        ]
        for i, (k, v) in enumerate(rows):
            _label(grid, k + ":", 11, color=th["text_dim"]
                   ).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=2)
            _label(grid, v, 11, color=th["text"]
                   ).grid(row=i, column=1, sticky="w", pady=2)

        # ── Autor ──────────────────────────────────────────────────────────
        author_card = _card(scroll, th)
        author_card.pack(fill="x", pady=6)
        _label(author_card, t("about_author_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(author_card,
               "ZeddiS  •  © 2024–2026  •  " + t("about_author_note"),
               11, color=th["text"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 12), anchor="w")

        # ── Technologie ────────────────────────────────────────────────────
        tech_card = _card(scroll, th)
        tech_card.pack(fill="x", pady=6)
        _label(tech_card, t("about_tech_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        tech_list = (
            "• Python 3.10+  •  customtkinter  •  Pillow  •  cryptography (Fernet)\n"
            "• pystray  •  psutil  •  pynput  •  pyautogui  •  yt-dlp (on-demand)"
        )
        _label(tech_card, tech_list, 11, color=th["text"], justify="left"
               ).pack(padx=14, pady=(0, 12), anchor="w")

        # ── Odkazy / tlačítka ──────────────────────────────────────────────
        btn_card = _card(scroll, th)
        btn_card.pack(fill="x", pady=6)
        _label(btn_card, t("about_links_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 8), anchor="w")

        btn_row = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkButton(btn_row, text=" GitHub",
                      image=icons.icon("github", 14, "#ffffff"), compound="left",
                      fg_color=th["primary"], hover_color=th["primary_hover"],
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=140,
                      command=lambda: webbrowser.open(GITHUB_RELEASES_URL)
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text=" Web",
                      image=icons.icon("globe", 14, "#ffffff"), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=140,
                      command=lambda: webbrowser.open("https://zeddihub.eu/tools/")
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text=" Discord",
                      image=icons.icon("discord", 14, "#ffffff"), compound="left",
                      fg_color=th["secondary"], hover_color=th["primary"],
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=140,
                      command=lambda: webbrowser.open("https://discord.gg/zeddihub")
                      ).pack(side="left", padx=(0, 8))

        # N-09: Report a bug via GitHub Issues (no token — browser prefill)
        ctk.CTkButton(btn_row, text=" " + (t("report_bug") if t("report_bug") != "report_bug"
                                           else "Nahlásit chybu"),
                      image=icons.icon("bug", 14, "#ffffff"), compound="left",
                      fg_color=th.get("error", "#ef4444"),
                      hover_color=th.get("warning", "#f59e0b"),
                      font=ctk.CTkFont("Segoe UI", 11), height=32, width=160,
                      command=self._open_report_bug
                      ).pack(side="left")

        # ── Licence ────────────────────────────────────────────────────────
        lic_card = _card(scroll, th)
        lic_card.pack(fill="x", pady=6)
        _label(lic_card, t("about_license_section"), 13, bold=True, color=th["primary"]
               ).pack(padx=14, pady=(12, 6), anchor="w")
        _label(lic_card, t("about_license_text"),
               10, color=th["text_dim"], wraplength=700, justify="left"
               ).pack(padx=14, pady=(0, 12), anchor="w")

    # ── N-09: Report a bug dialog ──────────────────────────────────────────
    def _open_report_bug(self):
        th = self.theme
        d = ctk.CTkToplevel(self)
        d.title(t("report_bug_title") if t("report_bug_title") != "report_bug_title"
                else "Nahlásit chybu")
        d.geometry("520x460")
        d.resizable(False, False)
        d.configure(fg_color=th.get("bg", th["content_bg"]))
        d.transient(self.winfo_toplevel())
        d.after(120, lambda: (d.lift(), d.focus_force(), d.grab_set()))

        root = ctk.CTkFrame(d, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=20, pady=20)

        _label(root, t("report_bug_title") if t("report_bug_title") != "report_bug_title"
                     else "Nahlásit chybu",
               16, bold=True, color=th.get("text_strong", th["text"])
               ).pack(anchor="w", pady=(0, 4))
        _label(root, t("report_bug_hint") if t("report_bug_hint") != "report_bug_hint"
                     else "Otevře se GitHub Issue s předvyplněnými údaji. Před odesláním můžeš text upravit.",
               10, color=th.get("text_muted", th["text_dim"])
               ).pack(anchor="w", pady=(0, 12))

        _label(root, t("report_bug_subject") if t("report_bug_subject") != "report_bug_subject"
                     else "Stručný popis", 11, color=th["text"]
               ).pack(anchor="w")
        title_var = ctk.StringVar(value="")
        title_entry = ctk.CTkEntry(
            root, textvariable=title_var, height=34,
            corner_radius=int(th.get("radius_entry", 8)),
            border_width=1, border_color=th.get("input_border", th.get("border", "#3a3a4a")),
            fg_color=th.get("input_bg", th.get("secondary", "#1a1a24")),
            text_color=th["text"],
        )
        title_entry.pack(fill="x", pady=(4, 10))

        _label(root, t("report_bug_body") if t("report_bug_body") != "report_bug_body"
                     else "Podrobnosti (co se stalo, kroky k reprodukci)",
               11, color=th["text"]).pack(anchor="w")
        body_box = ctk.CTkTextbox(
            root, height=180,
            corner_radius=int(th.get("radius_entry", 8)),
            border_width=1, border_color=th.get("input_border", th.get("border", "#3a3a4a")),
            fg_color=th.get("input_bg", th.get("secondary", "#1a1a24")),
            text_color=th["text"],
        )
        body_box.pack(fill="both", expand=False, pady=(4, 14))

        btn_row = ctk.CTkFrame(root, fg_color="transparent")
        btn_row.pack(fill="x")

        def _submit():
            import urllib.parse
            title = title_var.get().strip() or "Bug report"
            body_raw = body_box.get("1.0", "end").strip()
            import platform as _p
            footer = (
                f"\n\n---\n"
                f"ZeddiHub Tools v{CURRENT_VERSION}  •  "
                f"{_p.system()} {_p.release()}  •  Python {_p.python_version()}"
            )
            body = (body_raw or "(bez popisu)") + footer
            q = urllib.parse.urlencode({
                "title": title,
                "body": body,
                "labels": "bug,from-app",
            })
            url = f"https://github.com/ZeddiS/zeddihub-tools-desktop/issues/new?{q}"
            webbrowser.open(url)
            try:
                d.grab_release()
            except Exception:
                pass
            d.destroy()

        ctk.CTkButton(
            btn_row,
            text=t("cancel") if t("cancel") != "cancel" else "Zrušit",
            fg_color="transparent", hover_color=th.get("card_hover", th["secondary"]),
            text_color=th["text"], height=34, width=100,
            corner_radius=int(th.get("radius_button", 10)),
            command=lambda: (d.grab_release(), d.destroy()),
        ).pack(side="left")
        ctk.CTkButton(
            btn_row,
            text=" " + (t("report_bug_submit") if t("report_bug_submit") != "report_bug_submit"
                        else "Otevřít na GitHubu"),
            image=icons.icon("github", 14, "#ffffff"), compound="left",
            fg_color=th["primary"], hover_color=th.get("primary_hover", th["primary"]),
            text_color=th.get("nav_active_text", "#ffffff"),
            height=34,
            corner_radius=int(th.get("radius_button", 10)),
            command=_submit,
        ).pack(side="right")

        title_entry.focus_set()
