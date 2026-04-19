"""
ZeddiHub Tools — Tools download panel (admin only).

Lists available external tools from webhosting admin_apps.json,
offers install/uninstall/launch. Installed tools are registered via
gui.external_tools and shown in sidebar under "Ostatní nástroje".
"""

import threading
import customtkinter as ctk

try:
    from .. import external_tools
    from .. import icons
except ImportError:
    external_tools = None
    icons = None


class ToolsDownloadPanel(ctk.CTkFrame):
    def __init__(self, parent, theme: dict, on_refresh_sidebar=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.theme = theme
        self._on_refresh_sidebar = on_refresh_sidebar
        self._catalog = []
        self._build()
        self._load_catalog_async()

    def _build(self):
        th = self.theme
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(header, text="Stáhnout nástroje",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=th.get("text", "#fff")).pack(anchor="w")
        ctk.CTkLabel(header,
                     text="Admin moduly — po instalaci se přidají do sekce Ostatní nástroje.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=th.get("text_dim", "#888")).pack(anchor="w")

        row = ctk.CTkFrame(header, fg_color="transparent")
        row.pack(anchor="w", pady=(10, 0))
        ctk.CTkButton(row, text="Obnovit katalog",
                      fg_color=th.get("secondary", "#333"),
                      hover_color=th.get("primary", "#f0a500"),
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._load_catalog_async, height=32, width=140).pack(side="left")

        self._status = ctk.CTkLabel(header, text="", font=ctk.CTkFont("Segoe UI", 10),
                                    text_color=th.get("text_dim", "#888"))
        self._status.pack(anchor="w", pady=(6, 0))

        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list_frame.pack(fill="both", expand=True, padx=24, pady=(4, 20))

    def _set_status(self, text: str):
        try:
            self.after(0, self._status.configure, {"text": text})
        except Exception:
            pass

    def _load_catalog_async(self):
        self._set_status("⏳ Načítání katalogu...")

        def _run():
            try:
                tools = external_tools.fetch_catalog()
                self._catalog = tools
                self.after(0, self._render_list)
                self.after(0, lambda: self._status.configure(
                    text=f"✓ {len(tools)} nástrojů v katalogu"))
            except Exception as e:
                self.after(0, lambda: self._status.configure(
                    text=f"! Nelze načíst katalog: {e}"))

        threading.Thread(target=_run, daemon=True).start()

    def _render_list(self):
        for child in self._list_frame.winfo_children():
            child.destroy()

        th = self.theme
        if not self._catalog:
            ctk.CTkLabel(self._list_frame, text="Žádné nástroje v katalogu.",
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=th.get("text_dim", "#888")).pack(pady=30)
            return

        for tool in self._catalog:
            self._render_card(tool)

    def _render_card(self, tool: dict):
        th = self.theme
        card = ctk.CTkFrame(self._list_frame,
                            fg_color=th.get("card_bg", "#1a1a26"),
                            corner_radius=14)
        card.pack(fill="x", pady=6)

        slug = tool.get("slug", "")
        installed = external_tools.is_installed(slug)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info, text=tool.get("name", slug),
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=th.get("text", "#fff")).pack(anchor="w")
        if tool.get("description"):
            ctk.CTkLabel(info, text=tool.get("description"),
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=th.get("text_dim", "#888"),
                         wraplength=600, justify="left").pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(info, text=f"v{tool.get('version', '1.0.0')}",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=th.get("text_dim", "#888")).pack(anchor="w", pady=(2, 0))

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right")

        if installed:
            ctk.CTkButton(actions, text="Spustit",
                          fg_color=th.get("primary", "#f0a500"),
                          hover_color=th.get("primary_hover", "#d4900a"),
                          text_color="#000", width=90, height=30,
                          font=ctk.CTkFont("Segoe UI", 11, "bold"),
                          command=lambda s=slug: external_tools.launch_tool(s)
                          ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(actions, text="Odinstalovat",
                          fg_color="#8b2020", hover_color="#6b1818",
                          text_color="#fff", width=110, height=30,
                          font=ctk.CTkFont("Segoe UI", 11),
                          command=lambda s=slug: self._uninstall(s)
                          ).pack(side="left")
        else:
            btn = ctk.CTkButton(actions, text="Instalovat",
                                fg_color=th.get("primary", "#f0a500"),
                                hover_color=th.get("primary_hover", "#d4900a"),
                                text_color="#000", width=110, height=30,
                                font=ctk.CTkFont("Segoe UI", 11, "bold"))
            btn.configure(command=lambda t=tool, b=btn: self._install(t, b))
            btn.pack(side="left")

    def _install(self, tool: dict, btn):
        btn.configure(state="disabled", text="⏳ 0%")

        def _progress(done, total):
            pct = int(done * 100 / total) if total else 0
            try:
                self.after(0, btn.configure, {"text": f"⏳ {pct}%"})
            except Exception:
                pass

        def _done(ok, msg):
            self.after(0, lambda: self._status.configure(text=msg))
            self.after(0, self._render_list)
            if ok and self._on_refresh_sidebar:
                self.after(0, self._on_refresh_sidebar)

        external_tools.install_tool(tool, progress_cb=_progress, done_cb=_done)

    def _uninstall(self, slug: str):
        if external_tools.uninstall_tool(slug):
            self._status.configure(text=f"✓ Odinstalováno: {slug}")
            self._render_list()
            if self._on_refresh_sidebar:
                self._on_refresh_sidebar()
