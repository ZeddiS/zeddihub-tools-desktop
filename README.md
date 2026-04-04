<p align="center">
  <img src=".github/assets/banner.png" alt="ZeddiHub Tools" width="500">
</p>

<p align="center">
  <strong>Console TUI toolkit for game server management and configuration</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v3.0.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/language-CZ%20%2F%20EN-green?style=flat-square" alt="Language">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square" alt="Dependencies">
</p>

---

## About

ZeddiHub Tools is a modular console toolkit for game server administrators and players. The entire application runs in terminal with a colored TUI interface, keyboard navigation and a first-run setup wizard. No external dependencies required.

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

## Installation

```bash
git clone https://github.com/ZeddiS/zeddihub-tools.git
cd zeddihub-tools
```

### Requirements

- **Windows 10/11**
- **Python 3.10+**
- No external dependencies

## Usage

Double-click **`ZeddiHub Tools Launcher.bat`** or run:

```bash
python launcher.py
```

A setup wizard will appear on first launch of each module.

## Controls

| Key | Action |
|-----|--------|
| `W` / `S` | Navigate up / down |
| `D` / `Enter` | Confirm selection |
| `A` / `Esc` | Back / Exit to launcher |

## Project Structure

```
zeddihub-tools/
├── launcher.py                  # Main launcher with module selection
├── main.py                      # Entry point for .exe builds
├── ZeddiHub Tools Launcher.bat  # Windows shortcut
├── requirements.txt             # Dependencies (stdlib only)
├── .github/assets/              # Branding (logo, banner, icon)
├── zeddihub_rust_editor/        # Rust Editor module
├── zeddihub_csgo_tools/         # CS:GO Tools module
├── zeddihub_cs2_tools/          # CS2 Tools module
├── zeddihub_translator/         # Translator module
└── zeddihub_server_status/      # Server Status module
```

## Changelog

See [Releases](https://github.com/ZeddiS/zeddihub-tools/releases) for full changelog.

---

<details>
<summary>Cestina / Czech</summary>

## O projektu

ZeddiHub Tools je sada modularnich konzolovych nastroju pro spravce hernich serveru a hrace. Cela aplikace bezi v terminalu s barevnym TUI rozhranim, navigaci pomoci klaves a pruvodcem pri prvnim spusteni. Nepotrebuje zadne externi zavislosti.

## Moduly

### Hracske nastroje

| Modul | Popis |
|-------|-------|
| **CS2 Tools** | Crosshair generator, viewmodel generator s ASCII nahledem, autoexec s vlastnimi prikazy, practice config, buy bindy |
| **CS:GO Tools** | Crosshair generator s nahledem, viewmodel generator s live 2D oknem, autoexec, practice config, buy bindy, .cfg editor |
| **Rust Editor** | Vyhledavani v pluginech, hromadne opravy, editor prikazu, prekladac zprav, detektor prefixu, analyzator stability |

### Serverove nastroje

| Modul | Popis |
|-------|-------|
| **Server Status** | Real-time monitoring hernich serveru pres A2S_INFO protokol, live dashboard, quick query, auto-refresh |
| **CS2 Server** | Server.cfg generator, gamemode presety, map group editor, RCON klient |
| **CS:GO Server** | Editor databazi, server.cfg generator, SourceMod prekladac |
| **Rust Server** | RCON klient, plugin dependency checker, C# kompilator, simulator generovanych dat |
| **Translator** | Hromadny preklad souboru (JSON/TXT/LANG), prefix manager, statistiky prekladu, batch export |

## Instalace

```bash
git clone https://github.com/ZeddiS/zeddihub-tools.git
cd zeddihub-tools
python launcher.py
```

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
