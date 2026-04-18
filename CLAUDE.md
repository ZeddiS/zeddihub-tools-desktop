# CLAUDE.md — ZeddiHub Tools Desktop: Projektová znalostní báze

> **Účel souboru:** Slouží jako externí paměť pro AI asistenta (Claude) i pro členy týmu. Obsahuje kompletní technický popis architektury, logiky komunikace mezi moduly, vývojových konvencí a aktuálního stavu projektu.
> **Aktualizovat při každé větší změně architektury nebo přidání nového panelu/modulu.**

---

## 1. Architektura — Mapování složek a jejich účelu

```
zeddihub_tools/
├── app.py                     # Hlavní vstupní bod GUI aplikace
├── main.py                    # Alternativní vstupní bod (volá app.main())
├── launcher.py                # (zmíněn v .bat skriptu) — spouštěč přes conhost.exe
├── requirements.txt           # Python závislosti (customtkinter, Pillow, cryptography, pystray, psutil, requests)
├── version.json               # Záložní verze (autoritativní zdroj je GitHub Releases API)
├── .gitignore                 # Ignoruje dist/, build/, *.spec, __pycache__, /data/, *.enc atd.
│
├── assets/                    # Statické soubory (ikony, loga, fonty)
│   ├── icon.ico               # Ikona okna a tray ikony (generována z PNG při prvním spuštění)
│   ├── logo.png               # Logo v headeru (36×36 px)
│   ├── logo2.png              # Logo v headeru hlavního okna
│   ├── logo_transparent.png   # Záložní PNG pro generování .ico
│   ├── logo_icon.png          # Ikona (čtvercová verze loga)
│   ├── banner.png             # Banner na domovské stránce (stahuje se z CDN při spuštění)
│   └── fonts/                 # FontAwesome 6 Free TTF soubory (stahují se z CDN automaticky)
│       ├── fa-solid-900.ttf
│       └── fa-brands-400.ttf
│
├── gui/                       # Celý GUI kód aplikace
│   ├── __init__.py
│   ├── app.py                 # ← NEPLETE S KOŘENEM: toto je záložní; hlavní je root app.py
│   ├── auth.py                # Autentizační systém (Fernet šifrování přihlašovacích údajů)
│   ├── config.py              # Konfigurace bootstrapu a datového adresáře
│   ├── icons.py               # FontAwesome 6 Free icon rendering (CTkImage)
│   ├── locale.py              # Lokalizační systém (CZ/EN, JSON soubory)
│   ├── main_window.py         # Hlavní okno aplikace (sidebar, header, content panel)
│   ├── splash.py              # Splash screen při spuštění
│   ├── telemetry.py           # Anonymní telemetrie (fire-and-forget POST)
│   ├── themes.py              # Barevné motivy per-hra (default/cs2/csgo/rust, dark/light)
│   ├── tray.py                # Systémová lišta (pystray integrace)
│   ├── updater.py             # Kontrola aktualizací přes GitHub Releases API
│   └── panels/                # Jednotlivé panely obsahu (každý = jedna "stránka")
│       ├── __init__.py
│       ├── cs2.py             # CS2PlayerPanel, CS2ServerPanel
│       ├── csgo.py            # CSGOPlayerPanel, CSGOServerPanel
│       ├── game_tools.py      # GameToolsPanel (Translator, Sensitivity, eDPI, Ping Tester)
│       ├── home.py            # HomePanel (server status, doporučené nástroje)
│       ├── keybind.py         # KeybindPanel (vizuální klávesnice pro CS2/CS:GO/Rust)
│       ├── links.py           # LinksPanel (rychlé odkazy, DNS správa, File Uploader, Credits)
│       ├── pc_tools.py        # PCToolsPanel (sys info, DNS flush, net tools, utility)
│       ├── rust.py            # RustPlayerPanel, RustServerPanel
│       ├── settings.py        # SettingsPanel (jazyk, appearance, aktualizace, data složka, account)
│       ├── translator.py      # TranslatorPanel (překlad JSON/TXT/LANG souborů)
│       └── watchdog.py        # WatchdogPanel (monitoring serverů na pozadí)
│
├── locale/                    # Lokalizační JSON soubory
│   ├── cs.json                # Česká lokalizace (~90 klíčů)
│   └── en.json                # Anglická lokalizace (~90 klíčů)
│
└── webhosting/                # Serverová část (PHP admin panel + datové soubory)
    ├── index.php              # Veřejná landing page (stahuje verzi z GitHub API)
    ├── telemetry.php          # Telemetrický endpoint (přijímá POST z desktop klienta)
    ├── README.md              # Instrukce pro nasazení na hosting
    └── admin/
    │   ├── index.php          # PHP admin panel (správa klientů, JSON editory, telemetrie)
    │   ├── style.css          # Dark theme CSS pro admin panel
    │   └── .htaccess          # Zakázání výpisu adresáře
    └── data/
        ├── auth.json          # Uživatelé a přístupové kódy (ZMĚNIT HESLO!)
        ├── recommended.json   # Doporučené nástroje na domovské stránce
        ├── tray_tools.json    # Položky v tray menu (konfigurovatelné z admin panelu)
        ├── servers.json       # Herní servery na domovské stránce
        ├── version.json       # Záložní info o verzi
        └── .htaccess          # Zakázání výpisu adresáře
```

---

## 2. Logika — Jak spolu soubory komunikují

### 2.1 Startovací sekvence

```
main.py / app.py
  └── main()
        ├── _generate_icon()             # Vytvoří icon.ico z PNG pokud neexistuje
        ├── gui/locale.init()            # Načte jazyk z settings.json (nebo default "cs")
        ├── gui/config.is_first_launch() # Zkontroluje bootstrap.json v %LOCALAPPDATA%/ZeddiHub/
        │     ├── TRUE  → _show_first_launch_wizard()   # Výběr jazyka + složky pro data
        │     │             ├── gui/config.set_data_dir()
        │     │             └── gui/locale.set_lang()
        │     └── FALSE → (přeskočit wizard)
        └── gui/splash.run_splash()      # Splash screen (stahuje banner/logo z CDN)
              └── on_done_callback → MainWindow()
```

### 2.2 Datový adresář (bootstrap systém)

- **Bootstrap soubor:** `%LOCALAPPDATA%/ZeddiHub/bootstrap.json`
  - Uchovává pouze `{"data_dir": "C:\\Users\\...\\Documents\\ZeddiHub.Tools.Data"}`
  - Pokud neexistuje → první spuštění → spustí se wizard
- **Datový adresář** (uživatelem zvolitelný, default: `~/Documents/ZeddiHub.Tools.Data`):
  - `settings.json` — jazyk, appearance mode, sidebar stavy
  - `auth.enc` — Fernet-šifrované přihlašovací údaje
  - `.key` — Fernet klíč odvozený z machine ID (SHA-256 UUID+hostname)

### 2.3 Autentizační tok

```
gui/auth.py
  ├── verify_access(username, password, callback)
  │     └── HTTP GET → https://zeddihub.eu/tools/data/auth.json
  │           ├── Porovnává username+password se seznamem users[]
  │           ├── Nebo kontroluje access_codes[]
  │           └── Offline fallback: pokud _auth_verified=True, povolí přístup
  ├── save_credentials(username, password)  # Fernet šifrování → auth.enc
  ├── load_credentials()                    # Fernet dešifrování
  └── Globální stav: _cached_token, _auth_verified (module-level proměnné)
```

### 2.4 Hlavní okno a navigace

`MainWindow` (gui/main_window.py) je centrální třída dědící z `ctk.CTk`:

```
MainWindow
  ├── _build_layout()
  │     ├── Header (logo, game badge, auth status, version, light/dark toggle)
  │     ├── Sidebar (scrollable nav, sekce s accordion chováním)
  │     └── Content container (swapuje panely)
  │
  ├── _navigate(nav_id)
  │     ├── Určí hru z NAV_GAME_MAP dict
  │     ├── Přepne téma přes get_theme()
  │     ├── Aktualizuje game badge v headeru
  │     ├── Zvýrazní aktivní nav button
  │     └── Zavolá _show_panel(nav_id)
  │
  ├── _show_panel(nav_id)
  │     └── Lazy import + instantiace příslušného panelu
  │           Každý panel dědí z ctk.CTkFrame
  │           Destruuje předchozí panel (panel.destroy())
  │
  └── NAV_SECTIONS (list tuples) → definuje strukturu sidebaru
        Format: (sec_id, label, fa_icon, game, children, _)
        children = None → top-level button
        children = list → accordion sekce s podsložkami
```

**NAV_GAME_MAP** (dict v main_window.py) mapuje nav_id na hru:
```python
{"cs2_player": "cs2", "cs2_server": "cs2", ..., "home": "default", ...}
```

### 2.5 Systém témat

`gui/themes.py` obsahuje `GAME_THEMES` dict se 4 tématy: `default`, `cs2`, `csgo`, `rust`.

Každé téma má klíče: `primary`, `primary_hover`, `bg`, `sidebar_bg`, `header_bg`, `content_bg`, `card_bg`, `secondary`, `border`, `text`, `text_dim`, `text_dark`, `success`, `error`, `warning`, `accent`, `button_fg` + vnořený dict `light` s override hodnotami pro světlý režim.

```python
get_theme(game: str, mode: str = None) -> dict
# mode="light" → sloučí base + light overrides
# mode=None/dark → vrátí base téma (light dict odstraní)
```

### 2.6 Lokalizační systém

```
gui/locale.py
  ├── init()          # Načte jazyk z settings.json
  ├── t(key, **kwargs) # Vrátí přeložený řetězec, podporuje .format(**kwargs)
  ├── set_lang(lang)   # Uloží jazyk do settings.json, načte locale/xx.json
  └── _strings dict   # Module-level cache načtených překladů
```

Lokalizační soubory: `locale/cs.json`, `locale/en.json` (~90 klíčů každý).

### 2.7 FontAwesome ikony

`gui/icons.py` — lazy download FA 6 Free TTF z jsDelivr CDN:
- `preload()` → spustí stahování fontů na pozadí při startu aplikace
- `icon(name, size, color)` → vrátí `ctk.CTkImage` nebo `None`
- Cache: `_img_cache` (key: tuple name+size+color), `_font_cache`
- Brand ikony (github, discord, steam, chrome) používají `fa-brands-400.ttf`
- `CHARS` dict mapuje ~120 ikon na Unicode code-pointy

### 2.8 Panely — přehled komunikace

| Panel | Soubor | Klíčové závislosti |
|---|---|---|
| HomePanel | home.py | Steam A2S UDP query, urllib CDN fetch, A2S_INFO protokol |
| CS2PlayerPanel | cs2.py | tkinter filedialog, messagebox, tkinter Canvas (preview) |
| CS2ServerPanel | cs2.py | socket/struct RCON protokol (Source Engine) |
| CSGOPlayerPanel | csgo.py | Totožná struktura jako CS2, mírně odlišné defaulty |
| CSGOServerPanel | csgo.py | Stejný RCON klient jako CS2 |
| RustPlayerPanel | rust.py | Vlastní sensitivity kalkulátor, regex pro analýzu pluginů |
| RustServerPanel | rust.py | .bat generátor, RCON klient, regex bulk-fix Oxide pluginů |
| KeybindPanel | keybind.py | tkinter Canvas pro vizuální klávesnici |
| GameToolsPanel | game_tools.py | Sensitivity converter (SENS_GAMES dict), TCP ping, lazy-load TranslatorPanel |
| TranslatorPanel | translator.py | Google/MyMemory/LibreTranslate/DeepL API, threading |
| PCToolsPanel | pc_tools.py | subprocess wmic/ipconfig/ping, ctypes kernel32, psutil (volitelný) |
| WatchdogPanel | watchdog.py | UDP A2S + TCP fallback ping, threading loop |
| SettingsPanel | settings.py | Orchestruje locale, auth, config, updater moduly |
| LinksPanel | links.py | DNS lookup přes socket, port checker, webbrowser |

### 2.9 Updater

```
gui/updater.py
  ├── CURRENT_VERSION = "1.8.0"
  ├── check_for_update(callback)
  │     └── GET https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases/latest
  │           Porovná tag_name s CURRENT_VERSION (tuple comparison)
  │           Najde první .exe asset jako download_url
  ├── download_update(url, version, progress_callback, done_callback)
  │     └── Stáhne do tempfile.gettempdir()
  └── apply_update(new_exe_path)
        └── Pro frozen (PyInstaller) build: vytvoří .bat skript v TEMP
              .bat čeká 3s (ping), zkopíruje nové .exe, spustí, smaže sebe
```

### 2.10 Tray

`gui/tray.py` — závisí na `pystray` + `Pillow`:
- Načte ikonu z assets/ (přednost: web_favicon.ico → icon.ico → logo_icon.png)
- Dynamicky načte tray_tools z `https://zeddihub.eu/tools/data/tray_tools.json`
- Komunikace s MainWindow **výhradně** přes `app.after(0, ...)` (thread safety)
- Zavření okna → `withdraw()` (hide to tray), ne `destroy()`

### 2.11 Telemetrie

`gui/telemetry.py` — fire-and-forget, nikdy neblokuje UI:
- POST na `https://zeddihub.eu/tools/telemetry.php`
- Payload: `{event, panel, user (SHA-256 prefix 12 znaků), version, os}`
- Události: `launch`, `login`, `panel_open`, `export`
- Lze deaktivovat: `telemetry.set_enabled(False)`

### 2.12 Webhosting — Admin panel (PHP)

`webhosting/admin/index.php`:
- Session-based auth (admin role v auth.json)
- CSRF ochrana (token v SESSION)
- Stránky: dashboard, clients, recommended, tray, servers, version, telemetry
- Dashboard zobrazuje GitHub stats (cache 30 min v `.gh_cache.json`)
- JSON editory s inline validací (JavaScript)
- Bilingvní rozhraní CZ/EN (přepínání přes GET `?lang=`)

---

## 3. Konvence — Pojmenování proměnných, chybové ošetření, struktura kódu

### 3.1 Pojmenování

| Typ | Konvence | Příklad |
|---|---|---|
| Třídy | PascalCase | `CS2PlayerPanel`, `MainWindow`, `AuthDialog` |
| Metody | `_snake_case` s prefixem `_` pro privátní | `_build_crosshair()`, `_save_cfg()` |
| Veřejné metody | `snake_case` bez prefixu | `verify_access()`, `get_theme()` |
| Konstanty | `UPPER_SNAKE_CASE` | `CURRENT_VERSION`, `AUTH_API_URL`, `KEY_W` |
| Module-level state | `_snake_case` s prefixem | `_cached_token`, `_auth_verified`, `_strings` |
| Theme dict přístup | Přes lokální alias `t = self.theme` | `t["primary"]`, `t["card_bg"]` |
| Locale funkce | `t(key)` — jednoznakový alias | `t("login")`, `t("server_status")` |
| Nav ID | `snake_case` stringly-typed | `"cs2_player"`, `"rust_server"`, `"home"` |

### 3.2 Struktura panelů

Každý panel **musí**:
1. Dědit z `ctk.CTkFrame`
2. Mít `__init__(self, parent, theme: dict, nav_callback=None, **kwargs)` signaturu
3. Zavolat `super().__init__(parent, fg_color=theme["content_bg"], **kwargs)`
4. Uložit `self.theme = theme`
5. Zavolat `self._build()` na konci `__init__`

Vnitřní layout builder metody jsou pojmenovány `_build_<sekce>()`, např. `_build_crosshair()`, `_build_rcon()`.

### 3.3 Helper funkce v panelech

Každý panelový soubor opakuje tyto module-level helper funkce (ne metody třídy):

```python
def _label(parent, text, font_size=12, bold=False, color=None, **kw) → ctk.CTkLabel
def _btn(parent, text, cmd, theme, width=180, height=36, **kw) → ctk.CTkButton
def _section(parent, title, theme) → ctk.CTkFrame  # Card s nadpisem
def _entry_row(parent, label_text, default_val, theme, row, hint="") → ctk.StringVar
def _bool_row(...)   # OptionMenu 0/1
def _dropdown_row(...)  # OptionMenu s hodnotami
def _stepper_row(...)   # +/- tlačítka + entry
```

> ⚠️ **Duplikace kódu:** Tyto helper funkce jsou zkopírovány do cs2.py, csgo.py, rust.py — při refactoringu přesunout do `gui/widgets.py` nebo `gui/utils.py`.

### 3.4 Grid vs Pack — KRITICKÁ konvence

V rámci jednoho `ctk.CTkFrame` (nebo `tk.Frame`) **nikdy nemíchat** `.grid()` a `.pack()`.

Typický pattern v panelech:
- Vnější kontejner sekce → `.pack(fill="x", padx=0, pady=6)`
- Nadpis sekce → `.pack(padx=14, pady=(10,6), anchor="w")`
- Vnitřní `ctk.CTkFrame` pro form rows → `.grid_columnconfigure(1, weight=1)` + child widgety přes `.grid()`

### 3.5 Thread safety

Všechny UI aktualizace z background threadů **musí** používat `self.after(0, callback, args)`:

```python
# SPRÁVNĚ:
self.after(0, self._rcon_log, f"✓ Připojeno k {host}:{port}")

# ŠPATNĚ (způsobí crash tkinter):
self._rcon_log(f"✓ Připojeno")  # volání z non-main threadu
```

### 3.6 Chybové ošetření

- Síťové operace vždy v `try/except` s fallback chováním (ne crash)
- RCON/socket chyby → `_rcon_log(f"! Chyba: {e}")` + `self._rcon_socket = None`
- Chybějící PIL/psutil/pystray → graceful degradation (`PIL_OK`, `PSUTIL_OK`, `TRAY_OK` flags)
- Lokalizace: chybějící klíč → vrátí samotný klíč (`_strings.get(key, key)`)
- Icon rendering: vrátí `None` → CTkButton/Label s `image=None` zobrazí jen text

### 3.7 Verze

Verze aplikace je definována na **dvou místech** (musí být synchronizovány ručně):
1. `gui/updater.py` → `CURRENT_VERSION = "1.8.0"` (autoritativní pro runtime)
2. `gui/telemetry.py` → `_APP_VERSION = "1.8.0"` (synchronizováno)
3. `webhosting/data/version.json` → záložní (přepsán GitHub Releases API)
4. `version.json` (root) → pouze informativní

### 3.8 Import pořadí a relativní importy

V `gui/panels/` souborech:
```python
# Relativní import z nadřazeného balíčku
from ..locale import t
from .. import icons
from ..themes import get_theme
```

V `gui/main_window.py` jsou panely importovány **lazy** (uvnitř `_show_panel()` metody) aby se urychlilo startování:
```python
elif nav_id == "cs2_player":
    from .panels.cs2 import CS2PlayerPanel
    panel = CS2PlayerPanel(container, theme=th)
```

---

## 4. Stav vývoje

### 4.1 Hotové funkce (implementovány a funkční)

#### GUI & Infrastruktura
- [x] Hlavní okno s collapsible sidebar navigací (accordion sekce)
- [x] Per-game barevná témata (CS2/CS:GO/Rust/default × dark/light mode)
- [x] Lokalizace CZ/EN s přepínáním za běhu
- [x] First-launch wizard (jazyk + datová složka)
- [x] Splash screen s CDN stahováním assetů
- [x] FontAwesome 6 Free icon systém (download TTF, PIL rendering)
- [x] Systémová lišta (pystray) s dynamickým menu z webhosting JSON
- [x] Minimize to tray místo zavření okna (one-time info dialog)
- [x] Auto-update systém (GitHub Releases API, download wizard, .bat self-replace)
- [x] Přihlašovací dialog s TabView (Login + Register info)
- [x] Šifrované ukládání přihlašovacích údajů (Fernet AES)
- [x] Offline fallback autentizace

#### CS2 / CS:GO Panely
- [x] Crosshair Generator (stepper+dropdown UI, live Canvas preview)
- [x] Viewmodel Editor (stepper UI, zbraň silhouette Canvas preview, presety)
- [x] Autoexec Config (kategorizované sekce, vlastní příkazy textbox)
- [x] Practice Config
- [x] Buy Binds Generator
- [x] Server.cfg Generator (základní, gamemode, network, gameplay, GOTV sekce)
- [x] Gamemode Presety (7 módů: Competitive 5v5, MR12, Wingman, DM, Casual, Retake, 1v1)
- [x] Map Group Editor (pool selector, listbox, add/remove mapy)
- [x] RCON Klient (Source RCON protokol, background thread, console output)
- [x] CS:GO DB Editor (složkový výběr .ini/.cfg souborů)

#### Rust Panely
- [x] Sensitivity Kalkulátor (5 her, cm/360° přepočet)
- [x] Client CFG Generator
- [x] Bind Generátor (kategorie: Základní, Pohyb, Chat)
- [x] Tipy & Info (konzolové příkazy, optimalizace)
- [x] Server Config Generator + .bat start skript
- [x] Plugin Manager (Oxide bulk fix s regex patchy, edit příkazů, prefix detekce, závislosti)
- [x] RCON Klient s quick commands toolbarem

#### Herní Nástroje (GameToolsPanel)
- [x] Translator (Google/MyMemory/LibreTranslate/DeepL, 20 jazyků, JSON/TXT/LANG)
- [x] Sensitivity Converter (20 her, DPI kalkulace)
- [x] eDPI Kalkulačka (tiers, pro player reference tabulka)
- [x] Ping Tester (10 herních serverů, TCP socket latence, vlastní server)

#### PC Tools
- [x] Systémové info (OS, CPU přes wmic, RAM přes ctypes/psutil, Disk, GPU přes wmic, Network)
- [x] DNS Flush (ipconfig /flushdns, history s search+filter)
- [x] DNS Scanner (nslookup pro A/AAAA/MX/NS/TXT/CNAME/SOA záznamy)
- [x] Temp Cleaner (uživatelský + systémový TEMP, scan + delete, dual cleanup)
- [x] Ping Tool (Windows ping příkaz)
- [x] IP Geolocation (ip-api.com)
- [x] Port Checker (TCP socket)
- [x] Speedtest (HTTP download test z Cloudflare CDN, progress bar)
- [x] Shutdown Timer (subprocess shutdown /s /t)
- [x] Countdown Timer (popup okno s +1min/+5min, zvuk při dokončení)
- [x] Process List (psutil nebo fallback)

#### Server Watchdog
- [x] Přidávání serverů (manuálně + load z webhosting API)
- [x] Periodický monitoring (UDP A2S + TCP fallback, konfigurovatelný interval)
- [x] Alert na offline/online přechod s timestampem v logu

#### Settings & Links
- [x] Výběr jazyka, appearance mode (dark/light/system)
- [x] Kontrola aktualizací z Settings panelu
- [x] Změna datové složky za běhu
- [x] Backup/restore settings (JSON soubor), Factory reset
- [x] Account management (logout, smazání credentials)
- [x] Rychlé odkazy (4 sekce: komunita, autor, soubory, servery)
- [x] DNS Lookup + Port Checker v Links panelu
- [x] File Uploader odkaz (webový)
- [x] Credits stránka

#### Webhosting
- [x] PHP Admin panel (clients CRUD, JSON editory, telemetrie dashboard)
- [x] GitHub stats v dashboardu (stars, forks, watchers, downloads)
- [x] Telemetrický endpoint (telemetry.php, agregovaná JSON statistika)
- [x] Veřejná landing page (CZ/EN, scroll reveal animace, GitHub verze)
- [x] Bilingvní admin rozhraní

### 4.2 Identifikované problémy / technický dluh

| ID | Problém | Soubor | Závažnost |
|---|---|---|---|
| TD-001 | ~~Verze nesynchronizována~~ — opraveno ve v1.8.0: všechny tři zdroje drží `1.8.0`. | gui/updater.py, gui/telemetry.py, version.json | ✅ Vyřešeno |
| TD-002 | Helper funkce (`_label`, `_btn`, `_entry_row`, `_stepper_row` atd.) jsou zkopírovány do cs2.py, csgo.py, rust.py — duplicita kódu | gui/panels/ | Nízká (technický dluh) |
| TD-003 | `main_window.py` importuje `from . import telemetry` ale také `from . import telemetry as _telem` v AuthDialog._login() — nesjednocený import | gui/main_window.py | Nízká |
| TD-004 | `gui/config.py` obsahuje `is_first_launch()` funkci a `gui/locale.py` ji deleguje — zbytečná delegace | gui/locale.py | Nízká |
| TD-005 | `webhosting/data/auth.json` obsahuje plaintext hesla (včetně výchozího `"ZMENTE_HESLO"`) — nutno změnit před nasazením | webhosting/data/auth.json | KRITICKÁ (security) |
| TD-006 | `RustPlayerPanel._build_plugin_info()` a `_build_plugin_analyzer()` jsou definovány ale nikdy neregistrovány v tabview v `_build()` — mrtvý kód | gui/panels/rust.py | Nízká |
| TD-007 | `gui/main_window.py` v `NAV_SECTIONS`: game_tools nav_id je v sekci bez children, ale `_show_panel()` ho routuje do `GameToolsPanel` spolu s "translator" — duplicitní routing | gui/main_window.py | Nízká |
| TD-008 | csgo.py je do velké míry kopií cs2.py s minimálními rozdíly — refactoring na sdílenou base třídu | gui/panels/cs2.py, csgo.py | Střední |

### 4.3 Otevřené oblasti pro rozvoj

Níže jsou oblasti, které nejsou implementovány nebo jsou částečně hotové:

- **Rust Keybind Panel** — existuje `KeybindPanel` s podporou `game="rust"`, ale Rust nemá `rust_keybind` slot registrován v sidebar items (NAV_SECTIONS v main_window.py ho uvádí jako "Keybind generator" s `rust_keybind` nav_id, ale panel funguje).
- **Server Watchdog notifikace** — `tray.py` má `show_notification()` metodu, ale Watchdog ji nevolá; alertuje pouze do textového logu v panelu.
- **Rust RCON** — implementuje Source RCON protokol, ale Rust nativně používá WebSocket RCON (Facepunch RCON) — kompatibilita není zaručena pro všechny verze Rust serveru.
- **CS:GO DB Editor** — zobrazuje soubory v složce, ale neumožňuje jejich editaci (placeholder UI).
- **psutil auto-install** — `pc_tools.py` má `_install_psutil()` metodu s tlačítkem, ale tlačítko není viditelné v aktuálním buildu (metoda existuje, ale není volána z UI).

---

## 5. Klíčové URL a konstanty

| Konstanta | Hodnota | Soubor |
|---|---|---|
| `AUTH_API_URL` | `https://zeddihub.eu/tools/data/auth.json` | gui/auth.py |
| `SERVER_STATUS_URL` | `https://zeddihub.eu/tools/data/servers.json` | gui/panels/home.py, watchdog.py |
| `RECOMMENDED_URL` | `https://zeddihub.eu/tools/data/recommended.json` | gui/panels/home.py |
| `TRAY_TOOLS_URL` | `https://zeddihub.eu/tools/data/tray_tools.json` | gui/tray.py |
| `TELEMETRY_URL` | `https://zeddihub.eu/tools/telemetry.php` | gui/telemetry.py |
| `GITHUB_API_URL` | `https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases/latest` | gui/updater.py |
| `GITHUB_RELEASES_URL` | `https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest` | gui/updater.py |
| `BOOTSTRAP_FILE` | `%LOCALAPPDATA%/ZeddiHub/bootstrap.json` | gui/config.py |
| `DEFAULT_DATA_DIR_NAME` | `ZeddiHub.Tools.Data` | gui/config.py |
| `FA_CDN_SOLID` | `https://cdn.jsdelivr.net/.../fa-solid-900.ttf` | gui/icons.py |
| `CURRENT_VERSION` | `"1.8.0"` | gui/updater.py |

---

## 6. Závislosti (requirements.txt)

| Balíček | Verze | Použití |
|---|---|---|
| `customtkinter` | ≥5.2.0 | Celé GUI (CTkFrame, CTkButton, CTkLabel, CTkTabview atd.) |
| `Pillow` | ≥10.0.0 | Image loading, FA font rendering (PIL_OK flag) |
| `cryptography` | ≥41.0.0 | Fernet šifrování přihlašovacích údajů (CRYPTO_OK flag) |
| `pystray` | ≥0.19.4 | Systémová lišta (TRAY_OK flag) |
| `psutil` | ≥5.9.0 | Rozšířené sys info (PSUTIL_OK flag — volitelný, graceful fallback) |
| `requests` | ≥2.31.0 | (v requirements, ale kód používá `urllib.request` — requests není aktivně využit!) |

Stdlib: `tkinter`, `json`, `os`, `sys`, `socket`, `struct`, `re`, `time`, `shutil`, `threading`, `urllib`, `platform`, `subprocess`, `ctypes`, `hashlib`, `base64`, `pathlib`, `tempfile`

---

*Soubor aktualizován: 2026-04-18 | Autor: Claude (Anthropic) | Na základě analýzy zdrojového kódu ZeddiHub Tools Desktop v1.8.0*
