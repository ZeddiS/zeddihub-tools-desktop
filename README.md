<p align="center">
  <img src="assets/logo.png" alt="ZeddiHub Tools" width="420">
</p>

<p align="center">
  <strong>Desktopová aplikace pro správu herních serverů a nastavení hráčů</strong><br>
  <em>Desktop application for game server management and player configuration</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/verze-v1.1.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/standalone-.exe-blue?style=flat-square" alt="Standalone">
  <img src="https://img.shields.io/badge/jazyk-CZ%20%2F%20EN-green?style=flat-square" alt="Language">
  <img src="https://img.shields.io/badge/Python-3.11+-yellow?style=flat-square&logo=python" alt="Python">
</p>

<p align="center">
  <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest"><strong>⬇ Stáhnout nejnovější verzi</strong></a>
</p>

---

## O aplikaci

**ZeddiHub Tools** je kompletní sada nástrojů pro správce herních serverů a hráče. Aplikace je postavena na moderním dark GUI frameworku **customtkinter** s čistým minimalistickým designem, per-game barevnými tématy a plnohodnotnými nástroji pro CS2, CS:GO, Rust i správu PC.

Stačí spustit `.exe` — Python ani žádné instalace nejsou potřeba.

---

## Stažení

Ze [stránky Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest) stáhni:

**`ZeddiHub.Tools.exe`** — přenosný single-file build, žádný instalátor (~22 MB)

Dvojklik a spustit.

---

## Funkce

### 🎮 Herní nástroje (CS2 / CS:GO / Rust)

| Modul | Popis |
|-------|-------|
| **Hráčské nástroje** | Crosshair generátor (živý náhled), Viewmodel, Autoexec editor, Practice config, Buy Binds |
| **Serverové nástroje** | Server.cfg generátor, Gamemode presety, RCON klient, Map Group Editor |
| **Rust Plugin Manager** | Hromadná oprava pluginů, analyzér závislostí, překladač zpráv |
| **Keybind Generátor** | Vizuální klávesnice — přiřaď příkazy kliknutím na klávesu |
| **Translator** | Hromadný překlad JSON/TXT/LANG souborů do 20+ jazyků |

### 💻 PC Nástroje

| Funkce | Popis |
|--------|-------|
| Informace o PC | CPU, GPU, RAM, Disk, OS — veškeré systémové informace |
| DNS flush | Vymaže DNS cache jedním klikem |
| Temp cleanup | Skenuje a maže dočasné soubory |
| Ping | Otestuj odezvu libovolného serveru nebo IP |
| IP Info | Geolokace a informace o IP adrese |
| Shutdown Timer | Naplánuj vypnutí PC za X minut |

### 🏠 Hlavní stránka

- **Status serverů** — živé dotazování přes Steam A2S_INFO (hráči, mapa, ping)
- **Doporučené nástroje** — konfigurovatelné přes webhosting
- Rychlé odkazy na Discord, Steam, ZeddiHub web

### 🔐 Přístupová kontrola

- Server Tools jsou uzamčeny pro neautorizované uživatele
- Šifrované ukládání přihlašovacích údajů (Fernet/AES)
- Správa přístupu přes webhosting (auth.json)

### ⚙ Nastavení & Jazyk

- Přepínání jazyků: 🇨🇿 Česky / 🇬🇧 English (dialog při prvním spuštění)
- Nastavení aplikace (jazyk, účet, o aplikaci)
- Auto-update ze souboru version.json na webhosting

---

## Co je nového ve v1.1.0

- **Kompletní redesign UI** — moderní černé téma, per-game accent barvy
- **PC Nástroje** — systémové info, DNS, Temp, Ping, IP Info, Shutdown Timer
- **Nastavení** — jazyk, přihlášení, o aplikaci
- **Jazykový systém** — Čeština / Angličtina, dotaz při prvním spuštění
- **Skutečný server status** — Steam A2S_INFO UDP query (hráči, mapa, ping)
- **Doporučené nástroje** na domovské stránce
- **Skládací sidebar** — sekce CS2 ▼ / CS:GO ▼ / Rust ▼ se rozklikávají
- **Opraveno:** header game badge, status přihlášení, verze v titulku

---

## Buildy z historie

| Verze | Popis |
|-------|-------|
| **v1.1.0** | Redesign, PC Nástroje, jazyk CZ/EN, reálný server status |
| v1.0.0 | První customtkinter GUI, splash screen, auth systém |
| v0.1.0 | První GUI pokus (tkinter frameless) |
| v0.0.1 | Původní terminálové TUI |

---

## Build ze zdrojových kódů

```bash
git clone https://github.com/ZeddiS/zeddihub-tools-desktop.git
cd zeddihub-tools-desktop
pip install -r requirements.txt
python app.py
```

Pro sestavení .exe:
```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "ZeddiHub.Tools" --icon assets/icon.ico --add-data "assets;assets" --add-data "gui;gui" --add-data "locale;locale" app.py
```

---

## Požadavky

- Windows 10/11 (64-bit)
- Při spouštění ze zdrojáků: Python 3.11+

---

<p align="center">
  <a href="https://zeddihub.eu">zeddihub.eu</a> ·
  <a href="https://wiki.zeddihub.eu">ZeddiWiki</a> ·
  <a href="https://zeddis.xyz">zeddis.xyz</a> ·
  <a href="https://dsc.gg/zeddihub">Discord</a>
</p>

<p align="center">
  <strong>ZeddiS</strong> — ZeddiHub Community
</p>
