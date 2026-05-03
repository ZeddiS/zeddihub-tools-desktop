/**
 * Keyboard layout + per-game command catalogs for KeybindPanel.
 * Mirrors legacy/gui/panels/keybind.py.
 */

export type Game = "cs2" | "csgo" | "rust";

export interface Key {
  /** Source-engine bind name (e.g. "f1", "kp_enter", "TAB"). */
  name: string;
  /** Visible label on the key cap. */
  label: string;
  /** Width factor — 1.0 = standard key (38 px), 5.5 = spacebar. */
  w: number;
}

export const KEYBOARD_ROWS: Key[][] = [
  // Function row
  [
    { name: "ESC", label: "Esc", w: 1 },
    { name: "F1", label: "F1", w: 1 }, { name: "F2", label: "F2", w: 1 },
    { name: "F3", label: "F3", w: 1 }, { name: "F4", label: "F4", w: 1 },
    { name: "F5", label: "F5", w: 1 }, { name: "F6", label: "F6", w: 1 },
    { name: "F7", label: "F7", w: 1 }, { name: "F8", label: "F8", w: 1 },
    { name: "F9", label: "F9", w: 1 }, { name: "F10", label: "F10", w: 1 },
    { name: "F11", label: "F11", w: 1 }, { name: "F12", label: "F12", w: 1 },
  ],
  // Number row
  [
    { name: "TILDE", label: "`", w: 1 },
    { name: "1", label: "1", w: 1 }, { name: "2", label: "2", w: 1 },
    { name: "3", label: "3", w: 1 }, { name: "4", label: "4", w: 1 },
    { name: "5", label: "5", w: 1 }, { name: "6", label: "6", w: 1 },
    { name: "7", label: "7", w: 1 }, { name: "8", label: "8", w: 1 },
    { name: "9", label: "9", w: 1 }, { name: "0", label: "0", w: 1 },
    { name: "MINUS", label: "-", w: 1 }, { name: "EQUALS", label: "=", w: 1 },
    { name: "BACKSPACE", label: "⌫", w: 2 },
  ],
  // QWERTY
  [
    { name: "TAB", label: "Tab", w: 1.5 },
    { name: "q", label: "Q", w: 1 }, { name: "w", label: "W", w: 1 },
    { name: "e", label: "E", w: 1 }, { name: "r", label: "R", w: 1 },
    { name: "t", label: "T", w: 1 }, { name: "y", label: "Y", w: 1 },
    { name: "u", label: "U", w: 1 }, { name: "i", label: "I", w: 1 },
    { name: "o", label: "O", w: 1 }, { name: "p", label: "P", w: 1 },
    { name: "LBRACKET", label: "[", w: 1 }, { name: "RBRACKET", label: "]", w: 1 },
    { name: "BACKSLASH", label: "\\", w: 1.5 },
  ],
  // ASDF
  [
    { name: "CAPSLOCK", label: "Caps", w: 1.75 },
    { name: "a", label: "A", w: 1 }, { name: "s", label: "S", w: 1 },
    { name: "d", label: "D", w: 1 }, { name: "f", label: "F", w: 1 },
    { name: "g", label: "G", w: 1 }, { name: "h", label: "H", w: 1 },
    { name: "j", label: "J", w: 1 }, { name: "k", label: "K", w: 1 },
    { name: "l", label: "L", w: 1 },
    { name: "SEMICOLON", label: ";", w: 1 }, { name: "APOSTROPHE", label: "'", w: 1 },
    { name: "ENTER", label: "Enter", w: 2.25 },
  ],
  // ZXCV
  [
    { name: "LSHIFT", label: "Shift", w: 2.25 },
    { name: "z", label: "Z", w: 1 }, { name: "x", label: "X", w: 1 },
    { name: "c", label: "C", w: 1 }, { name: "v", label: "V", w: 1 },
    { name: "b", label: "B", w: 1 }, { name: "n", label: "N", w: 1 },
    { name: "m", label: "M", w: 1 },
    { name: "COMMA", label: ",", w: 1 }, { name: "PERIOD", label: ".", w: 1 },
    { name: "SLASH", label: "/", w: 1 },
    { name: "RSHIFT", label: "Shift", w: 2.75 },
  ],
  // Bottom row + arrows
  [
    { name: "LCTRL", label: "Ctrl", w: 1.5 },
    { name: "LALT", label: "Alt", w: 1.25 },
    { name: "SPACE", label: "SPACE", w: 5.5 },
    { name: "RALT", label: "Alt", w: 1.25 },
    { name: "RCTRL", label: "Ctrl", w: 1.5 },
    { name: "LEFT", label: "◄", w: 1 }, { name: "UP", label: "▲", w: 1 },
    { name: "DOWN", label: "▼", w: 1 }, { name: "RIGHT", label: "►", w: 1 },
  ],
  // Numpad
  [
    { name: "NUMLOCK", label: "NumLk", w: 1 },
    { name: "KP_SLASH", label: "/", w: 1 }, { name: "KP_MULTIPLY", label: "*", w: 1 },
    { name: "KP_MINUS", label: "-", w: 1 },
    { name: "KP_7", label: "7", w: 1 }, { name: "KP_8", label: "8", w: 1 }, { name: "KP_9", label: "9", w: 1 },
    { name: "KP_4", label: "4", w: 1 }, { name: "KP_5", label: "5", w: 1 }, { name: "KP_6", label: "6", w: 1 },
    { name: "KP_PLUS", label: "+", w: 1 },
    { name: "KP_1", label: "1", w: 1 }, { name: "KP_2", label: "2", w: 1 }, { name: "KP_3", label: "3", w: 1 },
    { name: "KP_0", label: "0", w: 1 }, { name: "KP_DEL", label: ".", w: 1 },
    { name: "KP_ENTER", label: "Enter", w: 1.5 },
  ],
];

// ─── Per-game commands ─────────────────────────────────

export const CS_WEAPONS = [
  "ak47", "m4a1", "m4a1_silencer", "awp", "deagle", "glock", "usp_silencer",
  "p250", "tec9", "fiveseven", "cz75a", "revolver", "sg556", "aug",
  "famas", "galilar", "mp9", "mac10", "mp7", "mp5sd", "ump45", "bizon",
  "p90", "negev", "m249", "nova", "xm1014", "sawedoff", "mag7",
  "vesthelm", "vest", "defuser", "hegrenade", "flashbang", "smokegrenade",
  "molotov", "incgrenade", "decoy", "taser",
];

export const CS_COMMANDS = [
  "buy {weapon}",
  "toggle cl_righthand 0 1",
  "toggle r_drawviewmodel 0 1",
  "noclip",
  "god",
  "give weapon_{weapon}",
  "sv_cheats 1",
  "bot_add_ct", "bot_add_t", "bot_kick",
  "mp_restartgame 1",
  "callvote kick",
  "say !swap", "say !rr", "say !menu",
  "use weapon_knife", "use weapon_c4",
  "+jump",
  "slot1", "slot2", "slot3",
  "drop", "inspect", "screenshot", "clear", "disconnect",
];

export const RUST_COMMANDS = [
  "chat.say /kit", "chat.say /home", "chat.say /tpr", "chat.say /tpa",
  "chat.say /sethome", "chat.say /trade", "chat.say /shop", "chat.say /backpack",
  "chat.say /bgrade 2", "chat.say /bgrade 3", "chat.say /bgrade 4",
  "consoletoggle", "kill", "respawn",
  "inventory.toggle", "map.toggle",
  "voice.voicevolume 0", "graphics.quality 3",
  "bind f1 consoletoggle",
];

export interface CommandCategory {
  title: string;
  items: string[];
}

export function getCommandCatalog(game: Game): CommandCategory[] {
  if (game === "rust") {
    return [{ title: "Rust příkazy", items: RUST_COMMANDS }];
  }
  // CS2 / CS:GO share catalog
  return [
    { title: "Příkazy", items: CS_COMMANDS },
    {
      title: "Buy zbraní",
      items: CS_WEAPONS.map((w) => `buy ${w}`),
    },
    {
      title: "Give zbraní (cheats)",
      items: CS_WEAPONS.map((w) => `give weapon_${w}`),
    },
  ];
}
