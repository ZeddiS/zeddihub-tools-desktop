<p align="center">
  <img src=".github/assets/banner.png" alt="ZeddiHub Tools" width="500">
</p>

<p align="center">
  <strong>Console TUI toolkit for game server management and configuration</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v3.0.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/standalone-.exe-blue?style=flat-square" alt="Standalone">
  <img src="https://img.shields.io/badge/language-CZ%20%2F%20EN-green?style=flat-square" alt="Language">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square" alt="Dependencies">
</p>

<p align="center">
  <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"><strong>Download latest .exe</strong></a>
</p>

---

## About

ZeddiHub Tools is a modular console toolkit for game server administrators and players. The entire application runs in terminal with a colored TUI interface, keyboard navigation and a first-run setup wizard.

**This is the desktop build** — a single-file `.exe` that runs directly on Windows with **no Python installation required**. All 5 modules, the Roslyn C# compiler, and every dependency are bundled in one portable executable.

## Download

Grab the latest release from the [Releases page](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest):

- **`ZeddiHub Tools.exe`** — single-file portable build, no installer needed

Double-click to run. A `data/` folder is created next to the `.exe` on first launch for your configs.

## Modules

### Player Tools

| Module | Description |
|--------|-------------|
| **CS2 Tools** | Crosshair generator, viewmodel generator with ASCII preview, autoexec with custom commands, practice config, buy binds |
| **CS:GO Tools** | Crosshair generator with preview, viewmodel generator with live 2D window, autoexec, practice config, buy binds, .cfg editor |
| **Rust Editor** | Plugin search, bulk fixer, command editor, message translator, prefix detector, stability analyzer |

### Server Tools

| Module | Description |
|--------|-------------|
| **Server Status** | Real-time game server monitoring via A2S_INFO protocol, live dashboard, quick query, auto-refresh (CS2/CS:GO/Rust/TF2/GMod) |
| **CS2 Server** | Server.cfg generator, gamemode presets, map group editor, RCON client |
| **CS:GO Server** | Database editor, server.cfg generator, SourceMod translator |
| **Rust Server** | RCON client, plugin dependency checker, C# compiler, generated files simulator |
| **Translator** | Batch file translation (JSON/TXT/LANG), prefix manager, translation stats, batch export (TXT/JSON/CSV), Google Translate API |

## Requirements

- **Windows 10/11** (64-bit)
- No Python needed, no external dependencies — everything is bundled

## Controls

| Key | Action |
|-----|--------|
| `W` / `S` | Navigate up / down |
| `D` / `Enter` | Confirm selection |
| `A` / `Esc` | Back / Exit to launcher |

## Building from Source

If you prefer to run or build from source, the Python source lives at [ZeddiS/zeddihub-tools](https://github.com/ZeddiS/zeddihub-tools). To rebuild the .exe yourself:

```bash
git clone https://github.com/ZeddiS/zeddihub-tools-desktop.git
cd zeddihub-tools-desktop
pip install pyinstaller pillow
pyinstaller ZeddiHubTools.spec --clean
```

The resulting `.exe` will be in `dist/`.

## Changelog

See [Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases) for full changelog.

---

<details>
<summary>Cestina / Czech</summary>

## O projektu

ZeddiHub Tools je sada modularnich konzolovych nastroju pro spravce hernich serveru a hrace. Cela aplikace bezi v terminalu s barevnym TUI rozhranim, navigaci pomoci klaves a pruvodcem pri prvnim spusteni.

**Toto je desktopovy build** — jediny `.exe` soubor, ktery bezi primo na Windows **bez nutnosti instalace Pythonu**. Vsech 5 modulu, Roslyn C# kompilator a vsechny zavislosti jsou zabalene v jednom prenosnem souboru.

## Stazeni

Stahnete si posledni verzi ze [stranky Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest):

- **`ZeddiHub Tools.exe`** — jednosouborovy portable build, zadny instalator

Dvojklik pro spusteni. Pri prvnim spusteni se vedle `.exe` vytvori slozka `data/` pro vase konfigurace.

## Ovladani

| Klavesa | Akce |
|---------|------|
| `W` / `S` | Nahoru / dolu |
| `D` / `Enter` | Potvrdit vyber |
| `A` / `Esc` | Zpet / Navrat do launcheru |

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
