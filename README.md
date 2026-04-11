<p align="center">
  <img src="assets/logo.png" alt="ZeddiHub Tools" width="420">
</p>

<p align="center">
  <strong>Nástroje pro správce herních serverů CS2, CS:GO a Rust</strong><br>
  <em>Tools for CS2, CS:GO and Rust game server admins</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/verze-v1.2.0-orange?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/jazyk-CZ%20%2F%20EN-green?style=flat-square" alt="Language">
</p>

<p align="center">
  <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest">
    <strong>⬇ Stáhnout nejnovější verzi</strong>
  </a>
</p>

---

## Jak začít

1. Stáhni **`ZeddiHub.Tools.exe`** ze [stránky Releases](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest)
2. Spusť — žádná instalace, žádný Python
3. Při prvním spuštění zvol jazyk a složku pro data aplikace
4. Hotovo

> **Windows může zobrazit upozornění SmartScreen** při prvním spuštění — to je normální u nepodepsaných aplikací. Klikni na "Více informací" → "Přesto spustit".

---

## Co aplikace umí

### Herní nástroje (CS2 / CS:GO / Rust)

- **Crosshair generátor** — živý náhled, export kódu
- **Viewmodel editor** — nastavení zbraní s náhledem
- **Autoexec editor** — config soubor přímo v aplikaci
- **Server.cfg generátor** — vytvoř config pro svůj server
- **RCON klient** — vzdálená správa serveru
- **Keybind generátor** — vizuální klávesnice, přiřaď příkazy klikem
- **Buy Binds** — nákupní zkratky pro CS2/CS:GO
- **Rust Plugin Manager** — hromadná oprava pluginů, analýza závislostí
- **Translator** — překlad JSON/TXT/LANG souborů do 20+ jazyků

### PC Nástroje

- Informace o systému (CPU, GPU, RAM, Disk)
- DNS flush, čištění temp souborů
- Ping tester, IP geolokace
- Shutdown timer

### Domovská stránka

- Live status herních serverů (Steam A2S query — hráči, mapa, ping)
- Rychlé odkazy na Discord a web

### Přístupová kontrola

Serverové nástroje jsou chráněné — přihlášení přes Discord / ZeddiS.xyz.

---

## Aktualizace

Aplikace automaticky zkontroluje novou verzi při každém spuštění.  
Pokud je dostupná, nabídne stažení a instalaci přímo v aplikaci — bez potřeby otevírat prohlížeč.

---

## Systémové požadavky

- Windows 10 nebo 11 (64-bit)
- Připojení k internetu (pro kontrolu serveru, autorizaci a aktualizace)

---

## Přehled verzí

| Verze | Popis |
|-------|-------|
| **v1.2.0** | Auto-update wizard, výběr složky s daty, GitHub API update check, čistší repo |
| v1.1.0 | Redesign UI, PC Nástroje, jazykový systém CZ/EN, reálný server status |
| v1.0.0 | První customtkinter GUI, splash screen, auth systém |
| v0.1.0 | První GUI pokus (tkinter frameless) |

---

<details>
<summary>Pro vývojáře — build ze zdrojových kódů</summary>

### Spuštění ze zdrojáků

```bash
git clone https://github.com/ZeddiS/zeddihub-tools-desktop.git
cd zeddihub-tools-desktop
pip install -r requirements.txt
python app.py
```

### Build .exe

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "ZeddiHub.Tools" --icon assets/icon.ico --add-data "assets;assets" --add-data "gui;gui" --add-data "locale;locale" app.py
```

Vyžaduje Python 3.11+.

### Poznámka k Windows Defender / SmartScreen

Nepodepsaná PyInstaller aplikace bývá při prvním spuštění označena jako neznámá.  
Reputace se buduje s počtem spuštění. Pro produkci doporučuji code-signing certifikát (OV/EV).  
Alternativně lze exe odeslat Microsoftu k analýze: [aka.ms/submitmalware](https://aka.ms/submitmalware).

</details>

---

<p align="center">
  <a href="https://zeddihub.eu">zeddihub.eu</a> ·
  <a href="https://dsc.gg/zeddihub">Discord</a> ·
  <a href="https://zeddis.xyz">zeddis.xyz</a>
</p>

<p align="center">
  <strong>ZeddiS</strong> — ZeddiHub Community
</p>
