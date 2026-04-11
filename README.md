<p align="center">
  <img src="assets/logo_transparent.png" alt="ZeddiHub Tools" width="380">
</p>

<p align="center">
  <strong>Desktop tools for CS2, CS:GO and Rust server administrators</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.5.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-blue?style=flat-square&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/language-EN%20%2F%20CZ-green?style=flat-square" alt="Language">
  <img src="https://img.shields.io/badge/license-private-lightgrey?style=flat-square" alt="License">
</p>

<p align="center">
  <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest">
    <img src="https://img.shields.io/github/downloads/ZeddiS/zeddihub-tools-desktop/total?style=flat-square&color=orange&label=downloads" alt="Downloads">
  </a>
</p>

<p align="center">
  <a href="https://zeddihub.eu/tools/" style="font-size:18px">
    <strong>🌐 zeddihub.eu/tools/</strong>
  </a>
</p>

<p align="center">
  <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest">
    <strong>⬇ Download latest release</strong>
  </a>
  &nbsp;&middot;&nbsp;
  <a href="https://zeddihub.eu">zeddihub.eu</a>
  &nbsp;&middot;&nbsp;
  <a href="https://dsc.gg/zeddihub">Discord</a>
</p>

---

## Getting Started

1. Download **`ZeddiHub.Tools.exe`** from the [Releases page](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest)
2. Run it — no installation, no Python required
3. On first launch, choose your language and data folder location
4. Done

---

## Features

### Game Tools — CS2 / CS:GO / Rust

| Tool | Description |
|------|-------------|
| Crosshair Generator | Live preview, export code |
| Viewmodel Editor | Weapon settings with preview |
| Autoexec Editor | Edit your config directly in the app |
| Server CFG Generator | Create a server config file |
| RCON Client | Remote server management |
| Keybind Generator | Visual keyboard — assign commands by clicking |
| Buy Binds | Purchase shortcuts for CS2 / CS:GO |
| Rust Plugin Manager | Batch plugin repair, dependency analysis |
| Translator | Translate JSON / TXT / LANG files into 20+ languages |
| Server Watchdog | Background monitor that alerts when servers go offline/online |

### PC Tools

- System information (CPU, GPU, RAM, Disk)
- DNS flush, temp file cleanup
- Ping tester, IP geolocation
- Shutdown timer

### Home Dashboard

- Live server status via Steam A2S query (players, map, ping)
- **Steam connect button** — opens `steam://connect/IP:PORT` directly
- Quick links to Discord and website

### System Tray

The app minimizes to the system tray instead of closing.  
Right-click the tray icon for quick access to tools, settings, or to exit.  
The tray menu is configurable via the web admin panel.

---

## Auto-Update

The app checks for new versions on every launch via GitHub Releases.  
If an update is available, it downloads and installs automatically — no browser needed.

---

## Requirements

- Windows 10 or 11 (64-bit)
- Internet connection (for server status, authorization and updates)

---

## Changelog

| Version | Highlights |
|---------|------------|
| **v1.5.0** | FontAwesome icon system — all emoji replaced with FA 6 Free vector icons throughout the UI |
| v1.4.0 | Navbar collapse fix, Steam connect button, dark/light mode, Server Watchdog, factory reset, DNS history, dual temp cleanup, landing page |
| v1.3.1 | Hotfix: web admin panel .htaccess compatibility with FastCGI |
| v1.3.0 | System tray icon, PHP web admin panel, configurable tray shortcuts |
| v1.2.0 | Auto-update wizard, data folder selection on first launch |
| v1.1.0 | UI redesign, PC Tools, CZ/EN language system, live server status |
| v1.0.0 | Initial customtkinter GUI, splash screen, auth system |

---

<details>
<summary>For developers — build from source</summary>

### Run from source

```bash
git clone https://github.com/ZeddiS/zeddihub-tools-desktop.git
cd zeddihub-tools-desktop
pip install -r requirements.txt
python app.py
```

Requires Python 3.11+.

### Build .exe

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "ZeddiHub.Tools" ^
  --icon assets/icon.ico ^
  --add-data "assets;assets" ^
  --add-data "gui;gui" ^
  --add-data "locale;locale" ^
  app.py
```

</details>

---

<details>
<summary>Webhosting / Admin panel setup</summary>

Upload the contents of `webhosting/` to your hosting:

- `admin/` → your domain (e.g. `zeddihub.eu/admin/`)
- `data/` → where the app reads JSON files (e.g. `files.zeddihub.eu/tools/`)

Edit `DATA_DIR` in `admin/index.php` to match your server path.  
**Change the admin password** in `data/auth.json` before going live.

Requires PHP 7.4+ and write permissions on the `data/` directory.

</details>

---

## Česky

### Rychlý začátek

1. Stáhni **`ZeddiHub.Tools.exe`** ze [stránky Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest)
2. Spusť — žádná instalace, žádný Python
3. Při prvním spuštění zvol jazyk a složku pro data aplikace
4. Hotovo

### Funkce

- **Herní nástroje** — crosshair, viewmodel, autoexec, server CFG, RCON, keybindy, buy bindy pro CS2/CS:GO/Rust
- **PC nástroje** — info o systému, DNS flush, čištění temp, ping tester
- **Domovská stránka** — live status serverů, rychlé odkazy
- **Systémová lišta** — aplikace běží na pozadí, přístup přes pravý klik na ikonu
- **Automatické aktualizace** — stažení a instalace přímo v aplikaci

### Systémové požadavky

- Windows 10 nebo 11 (64-bit)
- Připojení k internetu

---

<p align="center">
  <a href="https://zeddihub.eu">zeddihub.eu</a>
  &nbsp;&middot;&nbsp;
  <a href="https://dsc.gg/zeddihub">Discord</a>
  &nbsp;&middot;&nbsp;
  <a href="https://zeddis.xyz">zeddis.xyz</a>
  <br><br>
  Made by <strong>ZeddiS</strong>
</p>
