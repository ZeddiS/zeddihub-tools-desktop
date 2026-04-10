<p align="center">
  <img src=".github/assets/banner.png" alt="ZeddiHub Tools" width="500">
</p>

<p align="center">
  <strong>Modern desktop GUI for game server management and configuration</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v4.0.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/standalone-.exe-blue?style=flat-square" alt="Standalone">
  <img src="https://img.shields.io/badge/UI-frameless%20dark-9146ff?style=flat-square" alt="UI">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square" alt="Dependencies">
</p>

<p align="center">
  <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"><strong>Download latest .exe</strong></a>
</p>

---

## About

ZeddiHub Tools is a modular desktop suite for game server administrators and players. **v4.0.0** is a complete UI overhaul: the legacy console TUI has been replaced by a **luxury frameless windowed GUI** built on pure tkinter with custom canvas-drawn widgets, dark theme, smooth hover transitions, live previews and toast notifications.

**This is the desktop build** — a single-file `.exe` that runs directly on Windows with **no Python installation required**. All 5 modules, the Roslyn C# compiler, and every dependency are bundled in one portable executable.

## Download

Grab the latest release from the [Releases page](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest):

- **`zeddihub-tools-desktop.exe`** — single-file portable build, no installer needed (~30 MB)

Double-click to run. A `data/` folder is created next to the `.exe` on first launch to hold your configs, backups, and logs.

## What's New in v4.0.0

- **Frameless windowed GUI** with custom title bar, drag-to-move, Windows 11 rounded corners (DWM)
- **Sidebar navigation** with 5 modules — no more keyboard menus
- **Canvas-drawn luxury widgets** — rounded buttons, animated hover transitions, dark cards with shadows
- **Live previews** for crosshair and viewmodel — instant visual feedback as you tweak parameters
- **Toast notifications** — slide-in success/error popups
- **Threaded background work** — A2S queries, RCON, C# compilation and batch translation never block the UI
- **DPI awareness** — sharp on 4K displays
- **Single-file portable .exe** renamed to `zeddihub-tools-desktop.exe` to match the repo

## Modules

### Player Tools

| Module | Description |
|--------|-------------|
| **CS2 Tools** | Crosshair generator with live canvas preview, viewmodel generator with first-person preview, autoexec editor (25+ cvars across 7 categories) |
| **CS:GO Tools** | Crosshair generator, viewmodel with bob/lateral controls, autoexec editor (18+ cvars) |
| **Rust Editor** | Plugin browser, bulk fixer (Pool/Hooks/Connection patches), command extractor, bundled Roslyn C# compiler with per-file diagnostics |

### Server Tools

| Module | Description |
|--------|-------------|
| **Server Status** | Real-time A2S_INFO dashboard with auto-refresh, color-coded rows (CS2/CS:GO/Rust/TF2/GMod), add/remove servers |
| **Translator** | Batch file translation (JSON/TXT/LANG), prefix manager with hex color, batch export TXT/JSON/CSV, free Google/Libre/MyMemory engines |
| **RCON Client** | Source RCON shell built into CS2/Rust frames — connect, send commands, see live response |

## Requirements

- **Windows 10/11** (64-bit)
- No Python needed, no external dependencies — everything is bundled

## Navigation

| Action | How |
|--------|-----|
| Switch module | Click sidebar item |
| Drag window | Drag the title bar |
| Maximize / restore | Double-click title bar or click `□` |
| Close | `X` in the title bar |

## Building from Source

If you prefer to run or build from source, the Python source lives at [ZeddiS/zeddihub-tools](https://github.com/ZeddiS/zeddihub-tools). To rebuild the .exe yourself:

```bash
git clone https://github.com/ZeddiS/zeddihub-tools-desktop.git
cd zeddihub-tools-desktop
pip install pyinstaller pillow
pyinstaller ZeddiHubTools.spec --clean
```

The resulting `zeddihub-tools-desktop.exe` will be in `dist/`.

## Changelog

See [Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases) for full changelog.

---

<details>
<summary>Cestina / Czech</summary>

## O projektu

ZeddiHub Tools je modularni desktopova sada nastroju pro spravce hernich serveru a hrace. **v4.0.0** prinasi kompletni prepracovani UI: stare konzolove TUI bylo nahrazeno **luxusnim bezramovym okennim GUI** postavenym na ciste tkinter knihovne s vlastnimi canvas widgety, tmavym tematem, plynulymi hover efekty, zivymi nahledy a toast notifikacemi.

**Toto je desktopovy build** — jediny `.exe` soubor, ktery bezi primo na Windows **bez nutnosti instalace Pythonu**. Vsech 5 modulu, Roslyn C# kompilator a vsechny zavislosti jsou zabalene v jednom prenosnem souboru.

## Stazeni

Stahnete si posledni verzi ze [stranky Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest):

- **`zeddihub-tools-desktop.exe`** — jednosouborovy portable build, zadny instalator (~30 MB)

Dvojklik pro spusteni. Pri prvnim spusteni se vedle `.exe` vytvori slozka `data/` pro vase konfigurace.

## Co je noveho ve v4.0.0

- **Bezramove okenni GUI** s vlastnim titulkem, presunem mysi, zaoblenymi rohy ve Windows 11
- **Sidebar navigace** s 5 moduly — zadne klavesove menu
- **Canvas widgety** — zaoblene tlacitka, animovane hover prechody, tmave karty
- **Zive nahledy** crosshairu a viewmodelu — okamzita vizualni odezva
- **Toast notifikace** — vyjizdici upozorneni
- **Vlaknova prace na pozadi** — A2S, RCON, kompilace a preklad neblokuji UI
- **Podpora 4K** — ostrost diky DPI awareness
- **Single-file `.exe`** prejmenovan na `zeddihub-tools-desktop.exe`

## Pozadavky

- **Windows 10/11** (64-bit)
- Zadny Python, zadne externi zavislosti — vse je v .exe

</details>

---

<p align="center">
  <img src=".github/assets/icon.png" alt="ZeddiHub" width="48">
</p>

<p align="center">
  <strong>ZeddiS</strong><br>
  <a href="https://zeddihub.eu">zeddihub.eu</a> ·
  <a href="https://wiki.zeddihub.eu">ZeddiWiki</a> ·
  <a href="https://zeddis.xyz">zeddis.xyz</a> ·
  <a href="https://dsc.gg/zeddihub">Discord</a>
</p>
