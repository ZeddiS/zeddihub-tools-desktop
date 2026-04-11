"""
ZeddiHub Tools - Visual Keybind Generator
Works for CS2, CS:GO and Rust. Shows a visual keyboard.
User clicks a key, then picks an item or types a custom command.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable

from .. import icons

# ---- CS2 / CS:GO items ----
CS_WEAPONS = [
    "ak47", "m4a1", "m4a1_silencer", "awp", "deagle", "glock", "usp_silencer",
    "p250", "tec9", "fiveseven", "cz75a", "revolver", "sg556", "aug",
    "famas", "galilar", "mp9", "mac10", "mp7", "mp5sd", "ump45", "bizon",
    "p90", "negev", "m249", "nova", "xm1014", "sawedoff", "mag7",
    "vesthelm", "vest", "defuser", "hegrenade", "flashbang", "smokegrenade",
    "molotov", "incgrenade", "decoy", "taser",
]

CS_COMMANDS = [
    "buy {weapon}",
    "toggle cl_righthand 0 1",
    "toggle r_drawviewmodel 0 1",
    "noclip",
    "god",
    "give weapon_{weapon}",
    "sv_cheats 1",
    "bot_add_ct",
    "bot_add_t",
    "bot_kick",
    "mp_restartgame 1",
    "callvote kick",
    "say !swap",
    "say !rr",
    "say !menu",
    "use weapon_knife",
    "use weapon_c4",
    "+jump",
    "slot1",
    "slot2",
    "slot3",
    "drop",
    "inspect",
    "screenshot",
    "clear",
    "disconnect",
]

# ---- Rust items ----
RUST_COMMANDS = [
    "chat.say /kit",
    "chat.say /home",
    "chat.say /tpr",
    "chat.say /tpa",
    "chat.say /sethome",
    "chat.say /trade",
    "chat.say /shop",
    "chat.say /backpack",
    "chat.say /bgrade 2",
    "chat.say /bgrade 3",
    "chat.say /bgrade 4",
    "consoletoggle",
    "kill",
    "respawn",
    "inventory.toggle",
    "map.toggle",
    "voice.voicevolume 0",
    "graphics.quality 3",
    "bind f1 consoletoggle",
]

# ---- Keyboard layout (row, col, key_name, display, width_factor) ----
# width_factor: 1.0 = normal, 1.5 = 1.5x wide, etc.
KEYBOARD_ROWS = [
    # Row 0: Function keys
    [("ESC", "Esc", 1.0), ("F1", "F1", 1.0), ("F2", "F2", 1.0), ("F3", "F3", 1.0),
     ("F4", "F4", 1.0), ("F5", "F5", 1.0), ("F6", "F6", 1.0), ("F7", "F7", 1.0),
     ("F8", "F8", 1.0), ("F9", "F9", 1.0), ("F10", "F10", 1.0), ("F11", "F11", 1.0),
     ("F12", "F12", 1.0)],
    # Row 1: Numbers
    [("TILDE", "`", 1.0), ("1", "1", 1.0), ("2", "2", 1.0), ("3", "3", 1.0),
     ("4", "4", 1.0), ("5", "5", 1.0), ("6", "6", 1.0), ("7", "7", 1.0),
     ("8", "8", 1.0), ("9", "9", 1.0), ("0", "0", 1.0), ("MINUS", "-", 1.0),
     ("EQUALS", "=", 1.0), ("BACKSPACE", "⌫", 2.0)],
    # Row 2: QWERTY
    [("TAB", "Tab", 1.5), ("q", "Q", 1.0), ("w", "W", 1.0), ("e", "E", 1.0),
     ("r", "R", 1.0), ("t", "T", 1.0), ("y", "Y", 1.0), ("u", "U", 1.0),
     ("i", "I", 1.0), ("o", "O", 1.0), ("p", "P", 1.0), ("LBRACKET", "[", 1.0),
     ("RBRACKET", "]", 1.0), ("BACKSLASH", "\\", 1.5)],
    # Row 3: ASDF
    [("CAPSLOCK", "Caps", 1.75), ("a", "A", 1.0), ("s", "S", 1.0), ("d", "D", 1.0),
     ("f", "F", 1.0), ("g", "G", 1.0), ("h", "H", 1.0), ("j", "J", 1.0),
     ("k", "K", 1.0), ("l", "L", 1.0), ("SEMICOLON", ";", 1.0),
     ("APOSTROPHE", "'", 1.0), ("ENTER", "Enter", 2.25)],
    # Row 4: ZXCV
    [("LSHIFT", "Shift", 2.25), ("z", "Z", 1.0), ("x", "X", 1.0), ("c", "C", 1.0),
     ("v", "V", 1.0), ("b", "B", 1.0), ("n", "N", 1.0), ("m", "M", 1.0),
     ("COMMA", ",", 1.0), ("PERIOD", ".", 1.0), ("SLASH", "/", 1.0),
     ("RSHIFT", "Shift", 2.75)],
    # Row 5: Bottom
    [("LCTRL", "Ctrl", 1.5), ("LALT", "Alt", 1.25), ("SPACE", "SPACE", 5.5),
     ("RALT", "Alt", 1.25), ("RCTRL", "Ctrl", 1.5),
     ("LEFT", "◄", 1.0), ("UP", "▲", 1.0), ("DOWN", "▼", 1.0), ("RIGHT", "►", 1.0)],
]

KEY_W = 38
KEY_H = 34
KEY_GAP = 4


class KeybindPanel(ctk.CTkFrame):
    def __init__(self, parent, game: str, theme: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=theme["content_bg"], **kwargs)
        self.game = game
        self._nav_callback = nav_callback
        self.theme = theme
        self.binds: dict[str, str] = {}  # key_name → command string
        self._key_buttons: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self):
        # Title
        th = self.theme
        title = ctk.CTkLabel(
            self, text=f"  Keybind Generátor – {self.game.upper()}",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=th["primary"],
            image=icons.icon("keyboard", 20, th["primary"]),
            compound="left"
        )
        title.pack(pady=(16, 4), padx=20, anchor="w")

        ctk.CTkLabel(
            self,
            text="Klikněte na klávesu pro přiřazení akce. Oranžově = přiřazeno.",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=self.theme["text_dim"]
        ).pack(padx=20, anchor="w")

        # Keyboard frame
        kb_frame = ctk.CTkFrame(self, fg_color=self.theme["card_bg"], corner_radius=10)
        kb_frame.pack(padx=20, pady=12, fill="x")

        # Use tkinter Canvas for keyboard layout
        self.kb_canvas = tk.Canvas(
            kb_frame, bg=self.theme["card_bg"],
            highlightthickness=0,
            height=(KEY_H + KEY_GAP) * 6 + KEY_GAP * 2 + 8
        )
        self.kb_canvas.pack(padx=10, pady=10, fill="x")

        # Draw keyboard after window renders
        self.after(50, self._draw_keyboard)

        # Current binds list
        ctk.CTkLabel(
            self, text="Přiřazené klávesy:",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=self.theme["text"]
        ).pack(padx=20, pady=(4, 2), anchor="w")

        self.binds_text = ctk.CTkTextbox(
            self, height=120, font=ctk.CTkFont("Courier New", 11),
            fg_color=self.theme["secondary"],
            text_color=self.theme["text"]
        )
        self.binds_text.pack(padx=20, fill="x")

        # Buttons row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=20, pady=10, fill="x")

        ctk.CTkButton(
            btn_row, text=" Uložit .cfg soubor",
            fg_color=self.theme["primary"],
            hover_color=self.theme["primary_hover"],
            image=icons.icon("save", 14, "#ffffff"), compound="left",
            command=self._save_cfg,
            font=ctk.CTkFont("Segoe UI", 12, "bold"), height=36, width=200
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text=" Vymazat vše",
            fg_color=self.theme["secondary"],
            hover_color="#3a3a4a",
            image=icons.icon("trash", 14, th["text_dim"]), compound="left",
            command=self._clear_all,
            font=ctk.CTkFont("Segoe UI", 12), height=36, width=140
        ).pack(side="left")

    def _draw_keyboard(self):
        self.kb_canvas.delete("all")
        self._key_rects = {}
        self._key_texts = {}

        canvas_w = self.kb_canvas.winfo_width()
        if canvas_w < 100:
            canvas_w = 900

        y = KEY_GAP + 4
        for row in KEYBOARD_ROWS:
            # Calculate total width of row for auto-scaling
            total_units = sum(w for _, _, w in row)
            scale = (canvas_w - KEY_GAP * (len(row) + 1) - 20) / (total_units * KEY_W)
            scale = min(scale, 1.0)

            x = KEY_GAP + 10
            for key_name, display, width_factor in row:
                kw = int(KEY_W * width_factor * scale)
                assigned = key_name in self.binds
                fill = self.theme["primary"] if assigned else self.theme["secondary"]
                outline = self.theme["accent"] if assigned else self.theme["border"]
                text_color = "#ffffff" if assigned else self.theme["text_dim"]

                rect = self.kb_canvas.create_rectangle(
                    x, y, x + kw, y + KEY_H,
                    fill=fill, outline=outline, width=1 if not assigned else 2
                )
                txt = self.kb_canvas.create_text(
                    x + kw // 2, y + KEY_H // 2,
                    text=display,
                    fill=text_color,
                    font=("Segoe UI", 7 if width_factor >= 2 else 8)
                )
                self._key_rects[key_name] = rect
                self._key_texts[key_name] = txt

                # Bind click
                for item in (rect, txt):
                    self.kb_canvas.tag_bind(
                        item, "<Button-1>",
                        lambda e, k=key_name: self._on_key_click(k)
                    )
                    self.kb_canvas.tag_bind(
                        item, "<Enter>",
                        lambda e, r=rect: self.kb_canvas.itemconfig(r, outline=self.theme["primary"])
                    )
                    self.kb_canvas.tag_bind(
                        item, "<Leave>",
                        lambda e, r=rect, k=key_name: self.kb_canvas.itemconfig(
                            r, outline=self.theme["accent"] if k in self.binds else self.theme["border"]
                        )
                    )

                x += kw + KEY_GAP
            y += KEY_H + KEY_GAP

    def _on_key_click(self, key_name: str):
        """Show dialog to assign bind to key."""
        dialog = _BindDialog(self, key_name, self.game, self.theme,
                              current=self.binds.get(key_name, ""))
        self.wait_window(dialog)
        if dialog.result is None:
            return
        if dialog.result == "":
            # Remove bind
            self.binds.pop(key_name, None)
        else:
            self.binds[key_name] = dialog.result

        self._refresh_keyboard()
        self._refresh_binds_text()

    def _refresh_keyboard(self):
        for key_name, rect in self._key_rects.items():
            assigned = key_name in self.binds
            fill = self.theme["primary"] if assigned else self.theme["secondary"]
            outline = self.theme["accent"] if assigned else self.theme["border"]
            text_color = "#ffffff" if assigned else self.theme["text_dim"]
            self.kb_canvas.itemconfig(rect, fill=fill, outline=outline,
                                      width=2 if assigned else 1)
            if key_name in self._key_texts:
                self.kb_canvas.itemconfig(self._key_texts[key_name], fill=text_color)

    def _refresh_binds_text(self):
        self.binds_text.configure(state="normal")
        self.binds_text.delete("1.0", "end")
        if not self.binds:
            self.binds_text.insert("end", "// Žádné klávesy nejsou přiřazeny.\n")
        else:
            self.binds_text.insert("end", f"// {self.game.upper()} Keybinds - ZeddiHub Tools\n\n")
            for k, cmd in sorted(self.binds.items()):
                self.binds_text.insert("end", f'bind "{k}" "{cmd}"\n')
        self.binds_text.configure(state="disabled")

    def _save_cfg(self):
        if not self.binds:
            _show_msg(self, "Chyba", "Žádné klávesy nejsou přiřazeny!", self.theme)
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Uložit keybinds jako...",
            defaultextension=".cfg",
            filetypes=[("Config files", "*.cfg"), ("All files", "*.*")],
            initialfile=f"{self.game}_keybinds.cfg"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"// {self.game.upper()} Keybinds\n")
            f.write("// Generated by ZeddiHub Tools\n// https://zeddihub.eu\n\n")
            for k, cmd in sorted(self.binds.items()):
                f.write(f'bind "{k}" "{cmd}"\n')
            f.write('\necho "ZeddiHub keybinds loaded!"\n')
        _show_msg(self, "Úspěch", f"Keybinds uloženy do:\n{path}", self.theme)

    def _clear_all(self):
        self.binds.clear()
        self._refresh_keyboard()
        self._refresh_binds_text()


class _BindDialog(ctk.CTkToplevel):
    def __init__(self, parent, key_name: str, game: str, theme: dict, current: str = ""):
        super().__init__(parent)
        self.result = None
        self.game = game
        self.theme = theme
        self.title(f"Přiřadit klávesu: {key_name}")
        self.geometry("500x520")
        self.resizable(False, False)
        self.configure(fg_color=theme["content_bg"])
        self.grab_set()

        self._build(key_name, current)

    def _build(self, key_name: str, current: str):
        ctk.CTkLabel(
            self, text=f"Klávesa:  {key_name}",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=self.theme["primary"]
        ).pack(pady=(16, 4), padx=20, anchor="w")

        # Tabs: Items | Custom command
        tab_frame = ctk.CTkTabview(self, fg_color=self.theme["secondary"])
        tab_frame.pack(fill="both", expand=True, padx=20, pady=8)

        # Items tab
        if self.game in ("cs2", "csgo"):
            items_tab = tab_frame.add("Zbraně / Předměty")
            self._build_items_tab(items_tab, CS_WEAPONS)
        else:
            items_tab = tab_frame.add("Příkazy Rust")
            self._build_items_tab(items_tab, RUST_COMMANDS)

        # Commands tab
        cmd_tab = tab_frame.add("Vlastní příkaz")
        self._build_custom_tab(cmd_tab, current)

        # Predefined commands tab
        if self.game in ("cs2", "csgo"):
            pre_tab = tab_frame.add("Předvolby CS")
            self._build_items_tab(pre_tab, CS_COMMANDS)

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(4, 16))

        if current:
            ctk.CTkButton(
                btn_row, text=" Odebrat bind",
                fg_color="#8b2020", hover_color="#6b1818",
                image=icons.icon("trash", 13, "#ffffff"), compound="left",
                command=self._remove, height=34, width=130
            ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text=" Zrušit",
            fg_color=self.theme["secondary"],
            hover_color="#3a3a4a",
            image=icons.icon("times", 13, self.theme["text_dim"]), compound="left",
            command=self.destroy, height=34, width=100
        ).pack(side="right")

    def _build_items_tab(self, tab, items: list):
        frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        cols = 3
        for i, item in enumerate(items):
            ctk.CTkButton(
                frame, text=item,
                fg_color=self.theme["card_bg"],
                hover_color=self.theme["primary"],
                text_color=self.theme["text"],
                command=lambda cmd=item: self._set_result(cmd),
                font=ctk.CTkFont("Courier New", 10),
                height=28, anchor="w"
            ).grid(row=i // cols, column=i % cols, padx=3, pady=2, sticky="ew")

        for c in range(cols):
            frame.grid_columnconfigure(c, weight=1)

    def _build_custom_tab(self, tab, current: str):
        ctk.CTkLabel(
            tab, text="Zadejte vlastní příkaz nebo bind:",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=self.theme["text_dim"]
        ).pack(padx=10, pady=(10, 4), anchor="w")

        examples = {
            "cs2": 'Příklad: "buy ak47; buy vesthelm"',
            "csgo": 'Příklad: "buy ak47; buy vesthelm"',
            "rust": 'Příklad: "chat.say /kit"',
        }
        ctk.CTkLabel(
            tab, text=examples.get(self.game, ''),
            font=ctk.CTkFont("Courier New", 10),
            text_color=self.theme["text_dim"]
        ).pack(padx=10, anchor="w")

        self.custom_entry = ctk.CTkEntry(
            tab, height=38, placeholder_text="Zadejte příkaz...",
            font=ctk.CTkFont("Courier New", 12),
            fg_color=self.theme["secondary"],
            text_color=self.theme["text"]
        )
        self.custom_entry.pack(padx=10, pady=8, fill="x")
        if current:
            self.custom_entry.insert(0, current)

        ctk.CTkButton(
            tab, text=" Potvrdit příkaz",
            fg_color=self.theme["primary"],
            hover_color=self.theme["primary_hover"],
            image=icons.icon("check", 13, "#ffffff"), compound="left",
            command=self._confirm_custom,
            height=36
        ).pack(padx=10, pady=4, fill="x")

    def _set_result(self, cmd: str):
        # For CS weapons, wrap in buy command
        if self.game in ("cs2", "csgo") and not cmd.startswith("buy ") and " " not in cmd and not cmd.startswith("+"):
            if cmd in CS_WEAPONS:
                cmd = f"buy {cmd}"
        self.result = cmd
        self.destroy()

    def _confirm_custom(self):
        cmd = self.custom_entry.get().strip()
        if cmd:
            self.result = cmd
            self.destroy()

    def _remove(self):
        self.result = ""
        self.destroy()


def _show_msg(parent, title: str, msg: str, theme: dict):
    d = ctk.CTkToplevel(parent)
    d.title(title)
    d.geometry("360x160")
    d.configure(fg_color=theme["content_bg"])
    d.grab_set()
    ctk.CTkLabel(d, text=msg, font=ctk.CTkFont("Segoe UI", 12),
                 text_color=theme["text"], wraplength=320).pack(pady=30, padx=20)
    ctk.CTkButton(d, text="OK", command=d.destroy,
                  fg_color=theme["primary"], hover_color=theme["primary_hover"],
                  height=34, width=100).pack()
