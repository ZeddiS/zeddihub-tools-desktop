# CLAUDE.md — ZeddiHub Tools Desktop (Migration Spec)

> **Účel souboru:** Rozsáhlá referenční dokumentace VŠECH funkcí a vizuálního designu
> původní Python/customtkinter aplikace (v1.7.12). Slouží jako spec pro migraci na
> Tauri 2 + SvelteKit + Rust. **Každý panel, každé tlačítko, každý form field musí
> být v nové verzi 1:1 zachován.**
>
> Aktualizovat při každém migrovaném panelu (přidat „✅ ported in week N").
> Týdenní plán v `MIGRATION.md`.

---

## Část 1 — Globální architektura

### 1.1 Stack

**Stávající (v1.7.12, "Python verze", v `legacy/`):**
- Python 3.11+ + customtkinter (Tk wrapper)
- PyInstaller one-file build (28 MB EXE)
- pystray + Pillow + cryptography (Fernet) + psutil + requests
- FontAwesome 6 Free TTF (download z CDN)

**Cílová (v2.0.0, "Tauri verze", v root):**
- Tauri 2 + Rust 1.95 (backend)
- SvelteKit 2 + Svelte 5 runes + TypeScript (frontend)
- Tailwind CSS 3 (utility-first) + CSS variables (design tokens)
- lucide-svelte (tree-shakeable SVG ikony)
- reqwest (HTTP) + tokio (async) + chacha20poly1305 (crypto) + sysinfo + enigo
- WebView2 (Edge engine, sdílí s OS = malé EXE 13–17 MB)

### 1.2 Projektová struktura (po reorganizaci)

```
zeddihub_tools_desktop/                # repo root
├── package.json                        # ← Svelte/Tauri root (dříve v zeddihub_v2/)
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── postcss.config.js
├── src/                                # frontend (SvelteKit)
│   ├── app.html
│   ├── app.css
│   ├── routes/                         # file-based routing
│   │   ├── +layout.svelte              # Header + Sidebar shell
│   │   ├── +layout.ts
│   │   ├── +page.svelte                # Home
│   │   └── ... (24 panel routes)
│   └── lib/
│       ├── api/                        # typed Tauri IPC wrappers
│       ├── stores/                     # Svelte stores (theme/locale/auth/nav)
│       ├── components/{ui,layout,panels}
│       └── i18n/{cs,en}.ts
├── src-tauri/                          # backend (Rust)
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── icons/
│   ├── capabilities/
│   └── src/
│       ├── main.rs
│       ├── lib.rs                      # tauri::Builder
│       ├── error.rs                    # AppError enum
│       ├── commands/                   # #[tauri::command] handlers
│       └── services/                   # business logic
├── legacy/                             # ← původní Python verze (archiv, build-able)
│   ├── gui/                            # všechny .py soubory
│   ├── app.py
│   ├── main.py
│   ├── version.json
│   ├── zeddibuild.json
│   ├── _build_clean.bat
│   └── requirements.txt
├── assets/                             # sdílené (logo, banner, fonts)
├── poc/                                # PoC artefakty (nedotýkat)
├── CLAUDE.md                           # tento soubor
├── MIGRATION.md                        # týdenní plán migrace
└── README.md
```

### 1.3 Identifikátory aplikace

| Klíč | Hodnota |
|---|---|
| Bundle ID | `eu.zeddihub.tools` |
| Product Name | `ZeddiHub Tools` |
| EXE filename | `zeddihub-tools.exe` (přejmenovat na `ZeddiHubTools.exe` před prod release) |
| Auto-update GitHub repo | `ZeddiS/zeddihub-tools-desktop` |
| Data dir Windows | `%LOCALAPPDATA%\ZeddiHub\Tools\` |
| Data dir macOS | `~/Library/Application Support/eu.zeddihub.tools/` |
| Data dir Linux | `~/.local/share/zeddihub-tools/` |

### 1.4 Externí URL (zachovat v migraci)

| Konstanta | URL | Použití |
|---|---|---|
| `AUTH_API_BASE` | `https://zeddihub.eu/api/auth/` | Login/Register/Me/Logout |
| `LEGACY_AUTH_API_URL` | `https://zeddihub.eu/tools/data/auth.json` | Offline fallback |
| `SERVER_STATUS_URL` | `https://zeddihub.eu/tools/data/servers.json` | Watchdog seed |
| `RECOMMENDED_URL` | `https://zeddihub.eu/tools/data/recommended.json` | HomePanel cards |
| `TRAY_TOOLS_URL` | `https://zeddihub.eu/tools/data/tray_tools.json` | Tray menu items |
| `QUICK_LINKS_URL` | `https://zeddihub.eu/tools/data/quick_links.json` | AppsPanel katalog |
| `TELEMETRY_URL` | `https://zeddihub.eu/tools/telemetry.php` | Anonymní eventy |
| `GITHUB_REPO_API` | `https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop` | Stats |
| `GITHUB_RELEASES_API` | `https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases` | News + updater |
| `COBALT_PROXY` | `https://zeddihub.eu/api/tools/cobalt_proxy.php` | YouTube DL |

### 1.5 APP_SECRET

```
696d63c65a8536637183028e4eecb841cd5b679ce7b2d33c6ef2d4054166e438
```

Sdílí se mezi desktop + mobile + server (`api/_config.php::ZH_APP_SECRET`).
Bypassuje hCaptcha. **V Rustu jako `const &str` — nikoli v JS bundle**, aby
ho nebylo vidět v dev tools.

---

## Část 2 — Visual Design System

### 2.1 Per-game theming

Aplikace má **4 témata** podle aktivní hry. Theme se přepíná automaticky při
navigaci na panel té hry. Každé téma má **dark + light** variantu.

| Téma | Trigger | Primary | Accent |
|---|---|---|---|
| `default` | home, settings, links, atd. | `#f0a500` | `#ff6a00` |
| `cs2` | cs2/* nav | `#f5b623` (zlatá CS2) | `#ff6a00` |
| `csgo` | csgo/* nav | `#fdbf2c` (CS:GO oranžová) | `#ff8a1f` |
| `rust` | rust/* nav | `#cd2616` (Rust červená) | `#ff5c33` |

**Theme tokens** (RGB triplety v CSS variables, viz `src/app.css`):

```
bg              — base background
sidebar-bg      — sidebar fill
header-bg       — header fill
content-bg      — content area fill
card-bg         — card surface
card-hover      — card hover state
border          — input borders, dividers (hard)
divider         — UI separators (subtle, prefer over `border`)
primary         — accent color, active nav, primary buttons
primary-hover   — hover/glow variant
text            — primary text
text-strong     — page titles (one shade brighter)
text-muted      — captions, placeholders
text-dim        — disabled, secondary
text-dark       — text on primary fill (= near-black on amber)
accent          — secondary accent (orange-ish)
success         — green (#22c55e dark / #16a34a light)
warning         — amber (#f59e0b)
error           — red (#ef4444)
```

**Radius tokens:** `radius_card=14px`, `radius_button=10px`, `radius_entry=8px`.

### 2.2 Typography

- **Sans-serif stack:** `"Segoe UI", system-ui, -apple-system, sans-serif`
- **Page title** (h1): 24px / bold / `text-strong`
- **Section title** (h2/h3): 14px / bold / `text-strong` nebo `text`
- **Body**: 13px / normal / `text`
- **Caption**: 11px / normal / `text-muted`
- **Small label**: 10px / uppercase / `text-muted` / tracking-wide

### 2.3 Sidebar layout (přesný popis)

```
[ZeddiHub logo + verze]               <- Header (h: 56px, padding 0 20px)
[lang toggle] [theme toggle]              

┌──────────────┬──────────────────────────────────┐
│ Home         │                                   │
│ Aplikace     │                                   │
│ ─────────    │                                   │
│ ▶ PC NÁSTROJE│         CONTENT AREA              │
│ ▼ CS2        │       (currently mounted          │
│   Player     │           panel)                  │
│   Server 🟢  │  ← PREMIUM pill u auth-locked     │
│   Keybind    │                                   │
│ ▶ CS:GO      │                                   │
│ ▶ Rust       │                                   │
│ ▶ HERNÍ NÁSTR│                                   │
│              │                                   │
│ ─────────    │                                   │
│ Watchdog     │                                   │
│ Novinky      │                                   │
│ Odkazy       │                                   │
│ Stáhnout    🟢│                                   │
│ Nastavení    │                                   │
│ O aplikaci   │                                   │
└──────────────┴──────────────────────────────────┘
  width 240px       width: flex-1
```

**Sidebar pravidla:**
- **Top items** (Home, Aplikace) — vždy viditelné, nemají sekci
- **5 collapsible sekcí** s ▶/▼ chevron — každá má 3 položky (Player/Server/Keybind, případně 5 pro PC nástroje, 4 pro Game Tools)
- **Bottom items** (Watchdog, Novinky, Odkazy, Tools-Download, Nastavení, O aplikaci)
- **Locked items** (`requires_auth=True`) — viditelné jen když přihlášen, a navíc dostávají žluto-zelený `PREMIUM` pill v pravém okraji
- **Active item** — `bg-primary text-text-dark font-semibold`
- **Collapse state** — perzistuje v `settings.json::sidebar_sections`

### 2.4 Header layout (přesný popis)

```
[Logo + ZeddiHub Tools]   [Game badge: "Counter-Strike 2"]   [auth pill]  [lang]  [theme]
└─ 16px bold primary ─┘   └────── orange tint pill ──────┘   └ icon + name ┘
   │                                                                       │
   ├────── padding 0 20px, height 56px, bg-header-bg ─────────────────────┘
```

- **Logo**: text "ZeddiHub Tools" + verze (`v2.0.0 alpha`) ve stejném řádku, gap 12px
- **Game badge**: středový pill se jménem hry (CS2/CS:GO/Rust), barva = primary/15% bg s primary text. Skrývá se pro `default` panely.
- **Auth pill**: ikona + username (zelená pokud přihlášen) nebo "Nepřihlášen" (šedá). Klik = goto `/settings`.
- **Lang toggle**: emoji vlajka + kód (🇨🇿 CS / 🇬🇧 EN). Klik = toggle.
- **Theme toggle**: 🌙 / ☀ ikona, klik = toggle.

---

## Část 3 — Panel-by-panel inventory

> Pro každý panel: **co dělá**, **vizuál**, **technické závislosti**, **migrační target**.

### 3.1 HomePanel (`/`) ✅ Phase 1 hotov

**Co dělá:**
- Vítací stránka s doporučenými nástroji + GitHub stats + login card + news feed.

**Vizuální layout:**
```
H1: Vítej zpět
P:  ZeddiHub Tools — všechno potřebné na jednom místě.

[Quick links strip: ZeddiHub.eu | Wiki | Discord | ZeddiS.xyz]

┌─ Login card (1/3) ─┐ ┌─ GitHub stats (2/3) ───────────────┐
│ Username + role    │ │ Issues 🐛 | Stars ⭐ | Forks ⑂ | DL ⬇ │
│ [Logout] / [Login] │ │ (4 tile grid)                       │
└────────────────────┘ └─────────────────────────────────────┘

H2: Doporučené nástroje                   ✓ N nástrojů (live)
[Card grid 3xN: name + desc + color strip]

H2: Novinky z GitHub Releases
[Release card list: tag, title, body excerpt, "Open on GitHub" btn]
```

**Funkce:**
- Fetch `recommended.json` (TTL 30 min) → 6 dlaždic; fallback hardcoded list
- Fetch `github.com/repos/ZeddiS/.../releases` (TTL 1 h) → posledních 5
- Fetch `/repos/ZeddiS/...` → stars/forks/issues
- Sum `download_count` přes všechny assety = celkové DL count
- Login card: rozdíl podle `$auth.user`. Klik na "Login" = goto `/settings`.
- Quick link buttons → `tauri-plugin-shell::open(url)`

**Migrační target:** ✅ `src/routes/+page.svelte` (hotov v Phase 1)

### 3.2 SettingsPanel (`/settings`) 🟡 Phase 1 částečně

**Co dělá:**
- Konfigurace aplikace + login form + account info.

**Vizuální layout (5 tabs):** Účet | Vzhled | Jazyk | Datová složka | Aktualizace

**Tab 1 — Účet (when not authenticated):**
- Title "Přihlásit"
- Error banner pokud `$auth.error`
- Username/email field (placeholder "zeddi…")
- Password field (type=password)
- "Pamatovat si mě" checkbox (default: true)
- Primary button "Přihlásit"
- Footer link "Nemáš účet? Registrace na zeddihub.eu/tools/user/"

**Tab 1 — Účet (when authenticated):**
- Avatar (1. písmeno username, success bg, font-bold)
- Username + email + role
- "Odhlásit" button (secondary)
- "Smazat uložené credentials" button (warning)
- Sekce "Aktivní zařízení" — list zh_auth_tokens řádků (jen pro vlastní sessions)

**Tab 2 — Vzhled:**
- "Aktuální motiv" + "Tmavý nebo světlý" + theme toggle button
- Auto-toggle dle systému (volitelné)

**Tab 3 — Jazyk:**
- 🇨🇿 Čeština / 🇬🇧 English buttons (active stav vyplněný)

**Tab 4 — Datová složka:**
- Aktuální cesta (read-only field + Open button)
- "Změnit složku..." button → file dialog
- "Backup nastavení" → uloží `settings.json` jako .zip
- "Obnovit ze zálohy" → file dialog → unzip
- "Factory reset" — destruktivní, červené

**Tab 5 — Aktualizace:**
- Aktuální verze
- "Zkontrolovat aktualizace" button
- Auto-update checkbox (default: zapnuto)
- Telemetrie checkbox
- "Otevřít release stránku" link

**Migrační target:** 🟡 scaffold v `src/routes/settings/+page.svelte` (Phase 1 alpha). Plný funkcionální obsah doplnit v týdnu 3.

### 3.3 AppsPanel (`/apps`) ⏳ Týden 2

**Co dělá:**
- Katalog užitečných webů a nástrojů s search/filter, načítaný z `quick_links.json`.
- Embedded WebView2 nebo external browser open.

**Schema `quick_links.json`:**
```json
{
  "filter_groups": [
    {"id": "category", "label": "Kategorie", "options": [{"id": "gaming", "label": "Gaming"}]}
  ],
  "items": [
    {
      "id": "csgostats",
      "name": "CSGOstats.gg",
      "description": "Statistiky hráčů z CS2/CS:GO.",
      "icon": "chart-line",
      "url": "https://csgostats.gg/",
      "screenshot": null,
      "open_mode": "webview",
      "tags": ["category:stats", "category:gaming"]
    }
  ]
}
```

**Funkce:**
- 6h disk cache `quick_links.cache.json` v data_dir
- Search (debounce 250 ms)
- Multi-filter: AND mezi groupy, OR uvnitř groupy
- Klik na kartu:
  - `open_mode=webview` → otevři v Tauri webview
  - `open_mode=external` → `shell::open(url)`
  - `open_mode=download` → download manager

**Migrační target:** `src/routes/apps/+page.svelte`. WebView2 detection v Rustu.

### 3.4 AboutPanel (`/about`) ⏳ Týden 2

**Vizuál:**
- Logo (centered, 96x96)
- Verze + build date + git hash
- "Vytvořeno: ZeddiHub (ZeddiS)"
- Links: GitHub repo / Discord / Web / Email
- Sekce "Použité knihovny"
- Tlačítka: "Zkontrolovat aktualizace", "Otevřít changelog", "Reportovat bug"

**Migrační target:** `src/routes/about/+page.svelte`.

### 3.5 NewsPanel (`/news`) ⏳ Týden 2

- List release karet — Tag, jméno, datum, markdown body, assets, "Otevřít na GitHubu"
- Fetch top 20 releases (TTL 30 min)
- "Načíst další" button
- Filter prerelease toggle

**Migrační target:** `src/routes/news/+page.svelte`. Markdown přes `marked`.

### 3.6 LinksPanel (`/links`) ⏳ Týden 2

**Vnitřní záložky (6):**
1. **Novinky** — duplikát NewsPanel
2. **Moduly** — list nainstalovaných external modulů
3. **Odkazy** — kategorizovaný seznam (Komunita / Autor / Soubory / Servery)
4. **DNS** — DNS lookup + Port checker (TCP)
5. **Uploader** — file picker → upload na zeddihub.eu/tools/uploader/
6. **Credits** — autoři, ikony, fonty, knihovny

**Migrační target:** `src/routes/links/+page.svelte` s vnitřním tab navigatorem.

### 3.7 WatchdogPanel (`/watchdog`) ⏳ Týden 7

**Funkce:**
- Add/Edit/Delete server
- Load serverů z `servers.json`
- Periodický UDP A2S_INFO query (default 60 s)
- Fallback: TCP ping
- State machine: unknown → online → offline (alert)
- Tray notification on alert
- Log scrollable, max 500 řádků FIFO

**Migrační target:** `src/routes/watchdog/+page.svelte` + `src-tauri/src/services/{a2s,watchdog}.rs`.

### 3.8 ToolsDownloadPanel (`/tools-download`) 🔒 Auth required ⏳ Týden 9

- Admin-only katalog z `https://zeddihub.eu/api/tools/modules.json`
- Karty: ikona, název, popis, version, "Stáhnout" / "Aktualizovat" / "Odebrat"
- Progress bar během downloadu (3 fáze)
- Po instalaci: emit event do sidebaru

### 3.9 CS2 Player Tools (`/cs2/player`) ⏳ Týden 4

**Vnitřní layout: TabView se 5 záložkami.**

#### 3.9.1 Tab "Crosshair"

**Form fields:** style (0-5), color (RGB), size (0-10), thickness (0-5), gap (-10..10), outline (0/1 + thickness), dot (0/1), t-style (0/1), drawoutline (0/1), alpha (0-255), use_alpha (0/1), sniper_width.

**Right panel:** Canvas 320x320 — render crosshair v real time (background: dust2 zoomed nebo plain gray).

**Bottom:** Generated CFG output (textarea, monospace 8-12 řádků), [Copy] [Save] [Load] buttons. Presets row: pro players (Stewie2K, ZyWoO, NiKo) + Default + "Save preset...".

#### 3.9.2 Tab "🔫 Viewmodel"

- Fields: viewmodel_offset_{x,y,z}, viewmodel_fov, viewmodel_presetpos, cl_bob_*, cl_viewmodel_shift_*
- Right preview: SVG/Canvas zbraň silhouette s offsetem
- Same buttons (Copy/Save/Load/Reset/Pro presets)

#### 3.9.3 Tab "📝 Autoexec"

- Kategorizované collapsible sekce: Network, Mouse, HUD, Audio, Misc
- Custom commands textarea
- Generate `autoexec.cfg`

#### 3.9.4 Tab "Practice"

- Predefined scenarios (smoke nades, deathmatch, retake)
- Form: bot_difficulty, mp_*, sv_cheats
- Generate practice.cfg

#### 3.9.5 Tab "🛒 Buy Binds"

- Visual key picker
- Default presety
- Output `buybinds.cfg`

**Migrační target:** `src/routes/cs2/player/+page.svelte` s vnitřním Tabs komponentou + `<canvas>` pro crosshair preview + `<CrosshairPreview>` Svelte komponenta.

### 3.10 CS2 Server Tools (`/cs2/server`) 🔒 Auth required ⏳ Týden 5

**Vnitřní layout: TabView se 4 záložkami.**

#### 3.10.1 Tab "Server.cfg"
Sekce: Hostname / RCON / Network / Sourcetv / Logs / Voting / Bot. Output `server.cfg`.

#### 3.10.2 Tab "Gamemode Presety"
7 módů: Competitive 5v5, MR12, Wingman, DM, Casual, Retake, 1v1. Klik na preset → naplní form.

#### 3.10.3 Tab "🗺 Map Group"
Map pool selector, Listbox s vybranými mapami, Add/Remove buttons. Save jako `mapgroup.cfg`.

#### 3.10.4 Tab "RCON Klient" 🔥 Kritický feature

```
[Connection: IP : Port : Password] [Connect] [Disconnect]   🔴 Disconnected
[Quick commands: status / users / say / changelevel / restart]
[Console output — read-only, monospace, scrollback 1000 řádků]
[Command input ___________ ] [Send]
```

**Funkce:**
- Source RCON protokol nad TCP (Valve packet format)
- Auth → keep-alive → command/response
- Background tokio task udržuje connection
- Frontend: tauri::event listener pro real-time output
- Disconnect na change page
- History: ↑/↓ arrow keys

**Migrační target:** `src-tauri/src/services/rcon.rs` + `src/routes/cs2/server/+page.svelte` s tabs.

### 3.11 CS2 Keybind (`/cs2/keybind`) ⏳ Týden 5

**Vizuální:** Visual keyboard layout (full QWERTY + mouse buttons). Click on key → modal s kategorizovanými commands (Movement, Buy, Teamcomm, Misc, Voice) + custom command input.

**Funkce:**
- 3 hry varianty (CS2/CS:GO/Rust) — různé command listy
- Cfg output: `bind "<key>" "<cmd>"` per řádek

**Migrační target:** `src/routes/cs2/keybind/+page.svelte` + `<VirtualKeyboard>` komponenta v `lib/components/keyboards/`.

### 3.12 CS:GO Panels (`/csgo/{player,server,keybind}`) ⏳ Týden 6
Identická struktura s CS2, jen jiné defaulty + některé commands.

### 3.13 Rust Player Tools (`/rust/player`) ⏳ Týden 6

**Vnitřní záložky (6):**
1. **Sensitivity** — Rust sens calculator (5 her: CS2, Valorant, Apex, Overwatch, Fortnite)
2. **Bindy** — kategorizované Rust commandy, `keys.cfg`
3. **Tipy & Info** — read-only HTML s konzolovými příkazy + FPS boost
4. **Settings** — Client CFG generator
5. **Plugin Info** — info pro server admins
6. **Plugin Analyzer** — paste plugin source → regex detection

### 3.14 Rust Server Tools (`/rust/server`) 🔒 Auth required ⏳ Týden 6

**Vnitřní záložky (3):**
1. **Server Config** — Form + `server.cfg` + `start.bat` generator
2. **Plugin Manager** — Importuje Oxide pluginy, detekce závislostí, bulk-fix, edit commands
3. **RCON Klient** — WebSocket Facepunch RCON

**Migrační target:** `src-tauri/src/services/{rust_rcon,oxide_plugins}.rs` + UI komponenty.

### 3.15 Rust Keybind (`/rust/keybind`) ⏳ Týden 6
Stejně jako CS2 Keybind, jen Rust commandy.

### 3.16 Game Tools — Translator (`/tools/translator`) ⏳ Týden 7

**Funkce:**
- 20 jazyků
- 4 engines: Google, MyMemory, LibreTranslate, DeepL (API key)
- Source/output file picker (.json/.txt/.lang)
- Concurrent requests (5 parallel) s rate limit
- Re-translate single key
- Progress přes Tauri events
- Save: zachová custom překlad pokud existuje

**Migrační target:** `src/routes/tools/translator/+page.svelte` + `src-tauri/src/services/translator.rs`.

### 3.17–3.19 Sensitivity / eDPI / Ping Tester (`/tools/{sensitivity,edpi,ping}`) ⏳ Týden 7

- **Sensitivity:** 20 her source/target, DPI, FOV → target sens + cm/360 + odchylka bar chart + pro player table
- **eDPI:** DPI × sens calculator + tier breakdown (low/medium/high) + pro players reference
- **Ping Tester:** 10 herních serverů (TCP socket ping) + ping graph (last 10) + custom server input

**Migrační target:** `src-tauri/src/services/ping.rs` (TCP connect_timeout).

### 3.20 PC Sysinfo (`/pc/sysinfo`) ⏳ Týden 8

**Cards 2x3 grid:** System | CPU (live %) | Memory | Disks | GPU | Network adapters

**Migrační target:** `src/routes/pc/sysinfo/+page.svelte` + `src-tauri/src/services/sysinfo_ext.rs` (extends `sysinfo` crate o GPU + network adapters).

### 3.21 PC Net Tools (`/pc/nettools`) ⏳ Týden 8

**Vnitřní záložky:**
- DNS Flush (`ipconfig /flushdns` shell exec) + history
- DNS Scanner (A/AAAA/MX/NS/TXT/CNAME/SOA)
- IP Geolocation (ip-api.com)
- Port Checker (TCP connect)
- Speedtest (Cloudflare CDN, 10 / 100 MB chunks)
- Ping Tool (`ping -n 4` shell exec)

**Migrační target:** `src-tauri/src/services/net_tools.rs`.

### 3.22 PC Utility (`/pc/utility`) ⏳ Týden 8

**Vnitřní záložky:**
- **Auto Clicker** — fixed XY s F8 capture, single/double/triple click, CPS slider, jitter, click-count limit, pre-start countdown, sep. Start/Stop hotkeys, JSON presety
- **Stopky** — count-up + laps + history
- **Odpočet** — 5 post-expiry actions (dialog/beep/shutdown/custom/both)
- **Časovač** — absolute HH:MM nebo relative
- **Temp Cleaner** — user + system TEMP, dual cleanup
- **Shutdown Timer** — `shutdown /s /t N`
- **Process List** — sortable, kill selected, optional 3 s auto-refresh
- **YouTube Downloader** — yt-dlp wrapper, ve frozen build stáhne `yt-dlp.exe` standalone
- **Sticky Notes** — multi-tab note manager

**Migrační target:** `src/routes/pc/utility/+page.svelte` + Rust services pro auto-clicker (`enigo`).

### 3.23 PC Game Optimization (`/pc/gameopt`) ⏳ Týden 8
Aktuálně placeholders — i v migraci.

### 3.24 PC Advanced (`/pc/advanced`) ⏳ Týden 8
Aktuálně placeholders.

### 3.25 Macros (panel — currently in v1.7.6) ⏳ Týden 11+

**Komponenty:**
- Recorder (záznam přes globální hooky)
- Engine: 15 step types (key tap, key combo, type, mouse click, move, scroll, wait, random_wait, loop_start, loop_end, if_pixel, endif, comment)
- Hotkey Manager (globální hotkeys)
- Step Editor (GUI pro úpravu kroků)
- Storage: per-macro JSON v `<data_dir>/macros/`

**Migrační target:** `src/routes/macros/+page.svelte` + `src-tauri/src/services/macros/{recorder,engine,hotkeys}.rs` přes `enigo` + `windows-rs`. ⏳ Komplexní, odložit na týden 11+.

---

## Část 4 — Cross-cutting features

### 4.1 Authentication

**Flow:**
1. App startuje → `auth.resume()` v `+layout.svelte::onMount`
2. Resume volá `invoke("auth_me")` → backend čte `auth.enc`, dešifruje, čte token
3. Backend volá `GET /api/auth/me` s `Authorization: Bearer <token>`
4. Pokud OK → fill `auth` store; pokud expired → fallback `POST /api/auth/login` se saved password
5. Pokud nic neuspělo, `auth.user = null` (nepřihlášen)

**REST endpoints:**
- `POST /api/auth/login` — body `{identifier, password}` → `{ok, user, token, expires_at}` nebo `{ok:false, error, message}`
- `POST /api/auth/register` — body `{username, email, password}` → stejné
- `GET /api/auth/me` — header `Authorization: Bearer <token>` → `{ok, user, expires_at}`
- `POST /api/auth/logout` — `{ok}`
- `POST /api/auth/admin_reset` — admin-only

**Headers (každý request):**
- `User-Agent: ZeddiHubTools/<version> (desktop)`
- `Accept: application/json`
- `X-App-Secret: <APP_SECRET>` (bypass hCaptcha)
- `X-Client-Kind: desktop`
- `X-Client-Version: <APP_VERSION>`
- `Authorization: Bearer <token>` (jen me/logout)

**Error keys** (Czech messages):
- `invalid_username`, `invalid_email`, `invalid_password`
- `captcha_required`, `captcha_failed`, `taken`
- `bad_credentials`, `disabled`, `auth_required`, `auth_invalid`
- `forbidden`, `not_found`
- `too_fast`, `too_many_fails`, `daily_limit`
- `server_error`, `missing_identifier`, `missing_password`

**Token storage:**
- Soubor: `<data_dir>/auth.enc`
- Šifrování: ChaCha20Poly1305 (Fernet ekvivalent)
- Klíč: SHA-256 z `"zeddihub|<hostname>|<username>"`
- Layout: 12-byte nonce || ciphertext
- Plain JSON: `{username, token, expires_at, password?, user?}`

### 4.2 Theme system (per-game)

- Svelte store `currentGame` (default → cs2 → csgo → rust)
- `<html>` dostává `data-game="cs2"` → CSS vars overrides v `app.css`
- Light/dark parallel: `html.dark[data-game="cs2"]`, `html.light[data-game="cs2"]`

### 4.3 Localization (i18n)

- Languages: cs, en
- `src/lib/i18n/{cs,en}.ts` — flat dict
- Persistence: `localStorage::zh.lang`
- Použití: `import { t } from "$stores/locale"; ... {$t("nav_home")}`

### 4.4 System Tray

**Menu items:**
1. ZeddiHub Tools (default, dvojklik) — restore window
2. ─────
3. Nástroje (submenu, dynamic z `tray_tools.json`)
4. ─────
5. ⚙ Nastavení → nav `settings`
6. ─────
7. ✕ Ukončit → app exit

**Behavior:**
- Levý klik = restore okna
- Pravý klik = menu
- Tray notifikace přes `tauri-plugin-notification` (Watchdog alerts, update available)

### 4.5 Auto-Updater

- `tauri-plugin-updater` (oficiální plugin)
- `tauri.conf.json::plugins.updater.endpoints` = `["https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest/download/latest.json"]`
- Server-side `latest.json` s `signature`, `url`, `pub_date`, `notes`
- Code signing přes `tauri signer generate-key`
- Migration přechod ze staré Python verze viz Část 9.2

### 4.6 Telemetry

**Endpoint:** `POST https://zeddihub.eu/tools/telemetry.php`

**Payload:**
```json
{
  "event": "launch" | "login" | "panel_open" | "export",
  "panel": "<nav_id>",
  "user": "<sha256(username)[:12]>",
  "version": "2.0.0",
  "os": "Windows 11"
}
```

- Fire-and-forget (background task)
- Lze deaktivovat: `Settings > Aktualizace > Telemetrie ☐`

### 4.7 Splash Screen
Tauri 2 splash window — secondary window bez decorations, fade-out po `setup()`.

### 4.8 First-launch wizard
- Detekce: pokud `<data_dir>/settings.json` neexistuje
- Krok 1: výběr jazyka
- Krok 2: výběr datové složky
- Po dokončení redirect na `/`

### 4.9 HTTP Cache ✅ hotové
- `src-tauri/src/services/http_cache.rs`
- In-memory `HashMap<String, (timestamp, value)>`
- TTL per-fetch
- Stale-on-failure fallback

---

## Část 5 — Backend services (Rust)

| Modul | Popis | Status |
|---|---|---|
| `services/auth.rs` | REST klient `/api/auth/*` + encrypted session | ✅ |
| `services/http_cache.rs` | In-memory TTL cache | ✅ |
| `services/crypto.rs` | ChaCha20Poly1305 encrypt/decrypt | ✅ |
| `services/paths.rs` | Per-platform data dir resolver | ✅ |
| `services/tray.rs` | System tray (chybí dynamic submenu) | 🟡 |
| `services/rcon.rs` | Source RCON (CS2/CS:GO) přes TCP | ⏳ Týden 5 |
| `services/rust_rcon.rs` | Facepunch RCON přes WebSocket | ⏳ Týden 6 |
| `services/a2s.rs` | Steam A2S_INFO over UDP | ⏳ Týden 7 |
| `services/watchdog.rs` | Periodic monitoring loop | ⏳ Týden 7 |
| `services/ping.rs` | TCP socket ping | ⏳ Týden 7 |
| `services/translator.rs` | Multi-engine translation | ⏳ Týden 7 |
| `services/oxide_plugins.rs` | Regex bulk patcher | ⏳ Týden 6 |
| `services/macros/recorder.rs` | Globální hook recording | ⏳ Týden 11+ |
| `services/macros/engine.rs` | Step playback | ⏳ Týden 11+ |
| `services/macros/hotkeys.rs` | Global hotkey manager | ⏳ Týden 11+ |
| `services/sysinfo_ext.rs` | GPU + network adapters | ⏳ Týden 8 |
| `services/net_tools.rs` | DNS, port, speedtest, IP geo | ⏳ Týden 8 |
| `services/auto_clicker.rs` | Auto Clicker (`enigo`) | ⏳ Týden 8 |
| `services/timers.rs` | Stopky / Odpočet / Časovač | ⏳ Týden 8 |
| `services/sticky_notes.rs` | Multi-tab note storage | ⏳ Týden 8 |
| `services/external_tools.rs` | Module download/install | ⏳ Týden 9 |
| `services/updater.rs` | Tauri updater integration | ⏳ Týden 9 |
| `services/telemetry.rs` | Fire-and-forget POST | ⏳ Týden 9 |
| `services/migration.rs` | Bridge from Python verze | ⏳ Týden 10 |

---

## Část 6 — Frontend komponenty (Svelte)

### 6.1 lib/components/ui/

| Komponenta | Popis | Status |
|---|---|---|
| `Button.svelte` | variants: primary / secondary / ghost | ✅ |
| `Card.svelte` | padding, strip color, bordered | ✅ |
| `Input.svelte` | label, placeholder, type, error | ⏳ |
| `Tabs.svelte` | controlled tabs s `bind:active` | ⏳ |
| `Modal.svelte` | backdrop, focus trap, esc close | ⏳ |
| `Stepper.svelte` | numeric +/- input min/max | ⏳ |
| `Dropdown.svelte` | select with options | ⏳ |
| `Toggle.svelte` | checkbox styled as switch | ⏳ |
| `DataTable.svelte` | sortable, filterable, virtualized | ⏳ |
| `ProgressBar.svelte` | determinate / indeterminate | ⏳ |
| `Toast.svelte` | notification system | ⏳ |
| `KbdKey.svelte` | single key in virtual keyboard | ⏳ |

### 6.2 lib/components/layout/
`Header.svelte` ✅ | `Sidebar.svelte` ✅ | `PanelStub.svelte` ✅ | `GameBadge.svelte` ⏳

### 6.3 lib/components/panels/

Reusable bloky používané víc panely:
- `LoginCard.svelte` — Home + Settings
- `ServerCard.svelte` — Watchdog + Home
- `RconConsole.svelte` — CS2/CS:GO/Rust server
- `CrosshairPreview.svelte` — Canvas-based, CS2 + CS:GO
- `VirtualKeyboard.svelte` — Keybind panely
- `BindDialog.svelte` — modal s items + custom command

### 6.4 lib/api/ (Tauri IPC wrappers)
`auth.ts` ✅ | `http.ts` ✅ | `system.ts` ✅ | `rcon.ts` ⏳ | `a2s.ts` ⏳ | `watchdog.ts` ⏳ | `nettools.ts` ⏳ | `macros.ts` ⏳ | `external_tools.ts` ⏳ | `updater.ts` ⏳

### 6.5 lib/stores/
`theme.ts` ✅ | `locale.ts` ✅ | `auth.ts` ✅ | `nav.ts` ⏳ | `settings.ts` ⏳ | `notifications.ts` ⏳

---

## Část 7 — IPC contract (kompletní seznam command)

| Command | Args | Returns | Status |
|---|---|---|---|
| `auth_login` | `identifier, password` | `UserSession` | ✅ |
| `auth_register` | `username, email, password` | `UserSession` | ✅ |
| `auth_me` | `()` | `UserDto` | ✅ |
| `auth_logout` | `()` | `()` | ✅ |
| `http_fetch_json` | `url, ttl_seconds, force_refresh` | `Value` | ✅ |
| `http_cache_age` | `url` | `Option<u64>` | ✅ |
| `http_invalidate` | `url` | `()` | ✅ |
| `system_info` | `()` | `SystemInfo` | ✅ |
| `rcon_connect` | `host, port, password, kind` | `RconHandle` | ⏳ |
| `rcon_send` | `handle, command` | `String` | ⏳ |
| `rcon_disconnect` | `handle` | `()` | ⏳ |
| `a2s_query` | `host, port` | `A2SInfo` | ⏳ |
| `watchdog_add` | `server` | `()` | ⏳ |
| `watchdog_remove` | `id` | `()` | ⏳ |
| `watchdog_start` | `interval` | `()` | ⏳ |
| `watchdog_stop` | `()` | `()` | ⏳ |
| `watchdog_status` | `()` | `Vec<ServerStatus>` | ⏳ |
| `dns_lookup` | `domain, record_type` | `Vec<String>` | ⏳ |
| `dns_flush` | `()` | `()` | ⏳ |
| `port_check` | `host, port, timeout_ms` | `bool` | ⏳ |
| `ip_geolocation` | `ip` | `IpGeoInfo` | ⏳ |
| `speedtest_start` | `()` | `Stream<f64>` (event) | ⏳ |
| `ping_host` | `host, count` | `Vec<f64>` | ⏳ |
| `temp_clean` | `scope` (user/system) | `CleanResult` | ⏳ |
| `process_list` | `()` | `Vec<ProcessInfo>` | ⏳ |
| `process_kill` | `pid` | `()` | ⏳ |
| `shutdown_timer` | `seconds` | `()` | ⏳ |
| `auto_clicker_start` | `config` | `()` | ⏳ |
| `auto_clicker_stop` | `()` | `ClickStats` | ⏳ |
| `ytdl_download` | `url, format` | `Stream<f64>` | ⏳ |
| `translate_batch` | `texts, src, target, engine` | `Vec<String>` | ⏳ |
| `oxide_scan` | `dir_path` | `Vec<PluginInfo>` | ⏳ |
| `oxide_bulk_fix` | `plugin_paths` | `FixReport` | ⏳ |
| `external_modules_list` | `()` | `Vec<ModuleInfo>` | ⏳ |
| `external_modules_install` | `slug` | `()` | ⏳ |
| `external_modules_uninstall` | `slug` | `()` | ⏳ |
| `macros_record_start` | `()` | `()` | ⏳ |
| `macros_record_stop` | `()` | `MacroData` | ⏳ |
| `macros_play` | `data, speed` | `()` | ⏳ |
| `macros_register_hotkey` | `key, macro_id` | `()` | ⏳ |
| `settings_load` | `()` | `Settings` | ⏳ |
| `settings_save` | `settings` | `()` | ⏳ |
| `settings_reset` | `()` | `()` | ⏳ |
| `settings_data_dir` | `()` | `String` | ⏳ |
| `settings_change_data_dir` | `path` | `()` | ⏳ |
| `settings_backup` | `dest_path` | `()` | ⏳ |
| `settings_restore` | `src_path` | `()` | ⏳ |
| `updater_check` | `()` | `Option<ReleaseInfo>` | ⏳ |
| `updater_download` | `release` | `Stream<f64>` | ⏳ |
| `updater_install` | `()` | `()` | ⏳ |
| `telemetry_send` | `event, panel?` | `()` | ⏳ |

**Events (Rust → Frontend):**
- `zh:navigate` — request to goto path
- `zh:auth_changed` — auth state updated externally
- `zh:watchdog_alert` — server online/offline transition
- `zh:rcon_output` — async RCON response
- `zh:speedtest_progress` — speedtest progress
- `zh:download_progress` — generic download
- `zh:update_available` — auto-updater detection
- `zh:notification` — show toast

---

## Část 8 — Otevřené architektonické otázky

1. **External modules (`mod:slug`)** — v Pythonu = importovaný panel.
   V Tauri možnosti:
   a) WASM moduly (komplexní)
   b) Jen REST endpointy s frontend komponentou v hlavním bundle (omezené)
   c) Tauri plugin systém (Rust plugins loaded at runtime — neexistuje out-of-the-box)
   d) **Doporučení:** v2.0 vypustit external modules, v2.1+ zvážit (a) nebo (b)

2. **WebView2 fallback na Win10** — Tauri 2 má auto-installer flow přes `WebViewInstall` Rust crate. Ověřit.

3. **Code signing** — bez Authenticode certu Win SmartScreen ukazuje warning. ~$200/rok. Lze řešit po cutover.

4. **Cross-platform support** — primárně Win, Linux best-effort, Mac mimo scope.

5. **Migration data folder** — Python: `~/Documents/ZeddiHub.Tools.Data` (default). Tauri: `%LOCALAPPDATA%/ZeddiHub/Tools`. Bridge migrator musí přesunout.

6. **Translator API keys** — DeepL/LibreTranslate keys v Pythonu plain JSON. V Tauri encrypted store.

---

## Část 9 — Distribuce + cutover plán

### 9.1 Build pipeline

```
zeddihub_tools_desktop/  (root po reorganizaci)
└── npm run tauri build
    ├── (1) npm run build           # SvelteKit static → /build/
    ├── (2) cargo build --release   # Rust → src-tauri/target/release/zeddihub-tools.exe
    └── (3) tauri bundle
        ├── NSIS installer  → src-tauri/target/release/bundle/nsis/*.exe
        └── MSI             → src-tauri/target/release/bundle/msi/*.msi
```

### 9.2 Auto-update přechod (kritický!)

**Phase A** (před cutover, aktuální):
- `legacy/` Python — buildí se přes `_build_clean.bat` jako `dist/ZeddiHubTools.exe` (28 MB) — *jen pro reference*
- root Tauri — buildí se přes `npm run tauri build` jako `zeddihub-tools.exe` (17 MB) — *aktivně vyvíjené*
- GitHub Releases nadále publikují Python EXE jako `ZeddiHubTools.exe` až do v2.0.0

**Phase B** (cutover, v2.0.0 release):
- GitHub release `v2.0.0` má 2 assety:
  - `ZeddiHubTools.exe` (Tauri build, přejmenovaný pro auto-updater detection)
  - `ZeddiHub-Tools-Setup.exe` (Tauri NSIS installer pro nové instalace)
- Stará v1.7.x detekuje `v2.0.0+` v GH releases → stahuje `ZeddiHubTools.exe` → spustí ho s `--first-run-after-migration`
- Bridge migrator:
  1. Detekuje stará Python data dir
  2. Migruje `auth.enc` (Fernet → ChaCha20Poly1305)
  3. Spustí Tauri MSI installer
  4. Smaže starý EXE po prvním úspěšném startu nového

**Phase C** (po cutover):
- Auto-update čistě Tauri-native (`tauri-plugin-updater`)
- `latest.json` na GH Releases určuje verzi
- Code-signed updates (po pořízení Authenticode certu)

### 9.3 Migration bridge (Rust binary)

Speciální mode v Tauri main.rs:
```rust
fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--first-run-after-migration") {
        if let Err(e) = migration::run_bridge() {
            // show error dialog, fallback to normal start
        }
    }
    zeddihub_tools_lib::run();
}
```

`migration::run_bridge()`:
1. Detekuje stará Python data dir (`%LOCALAPPDATA%/ZeddiHub/bootstrap.json` → contains `data_dir`)
2. Pokud existuje `<old_data_dir>/auth.enc` (Fernet), dekryptuje ho s known machine_id pattern
3. Re-encryptuje s ChaCha20Poly1305 a uloží do `%LOCALAPPDATA%/ZeddiHub/Tools/auth.enc`
4. Migruje `settings.json`, sticky notes, macros, presety
5. Zapíše marker `<new_data_dir>/migrated_from_v1.txt`
6. Volitelně smaže staré data (after user confirmation)

---

## Část 10 — Migrace progress (live tracking)

Update tuto tabulku po dokončení každého panelu.

| Panel | Status | Verze | Týden |
|---|---|---|---|
| Foundation (theme/locale/auth/layout) | ✅ ported | 2.0.0-1 | 1 |
| HomePanel | ✅ ported | 2.0.0-1 | 1 |
| SettingsPanel — basic | 🟡 scaffold | 2.0.0-1 | 1 |
| SettingsPanel — full features | ⏳ planned | | 3 |
| AppsPanel | ✅ ported | 2.0.0-2 | 2 |
| AboutPanel | ✅ ported | 2.0.0-2 | 2 |
| NewsPanel | ✅ ported | 2.0.0-2 | 2 |
| LinksPanel | ✅ ported | 2.0.0-2 | 2 |
| LoginDialog (overlay) | ⏳ planned | | 3 |
| First-launch wizard | ⏳ planned | | 10 |
| CS2 PlayerPanel | ⏳ planned | | 4 |
| CS2 ServerPanel | ⏳ planned | | 5 |
| CS2 KeybindPanel | ⏳ planned | | 5 |
| CS:GO PlayerPanel | ⏳ planned | | 6 |
| CS:GO ServerPanel | ⏳ planned | | 6 |
| CS:GO KeybindPanel | ⏳ planned | | 6 |
| Rust PlayerPanel | ⏳ planned | | 6 |
| Rust ServerPanel + Plugin Manager | ⏳ planned | | 6 |
| Rust KeybindPanel | ⏳ planned | | 6 |
| TranslatorPanel | ⏳ planned | | 7 |
| SensitivityPanel | ⏳ planned | | 7 |
| EDPIPanel | ⏳ planned | | 7 |
| PingTesterPanel | ⏳ planned | | 7 |
| WatchdogPanel | ⏳ planned | | 7 |
| PCSysInfoPanel | ⏳ planned | | 8 |
| PCNetToolsPanel | ⏳ planned | | 8 |
| PCUtilityPanel | ⏳ planned | | 8 |
| PCGameOptPanel | ⏳ planned | | 8 |
| PCAdvancedPanel | ⏳ planned | | 8 |
| ToolsDownloadPanel | ⏳ planned | | 9 |
| Auto-updater | ⏳ planned | | 9–10 |
| Telemetry | ⏳ planned | | 9 |
| Splash Screen | ⏳ planned | | 10 |
| Migration bridge | ⏳ planned | | 10 |
| MacrosPanel | ⏳ planned | | 11+ |

---

## Část 11 — Code conventions

### 11.1 Frontend (Svelte 5 + TS)

- **Runes:** `$state`, `$derived`, `$effect`, `$props`, `$bindable`
- **No `let` for reactive state** — vždy `$state(initial)`
- **Stores** přes `writable<T>(initial)` z `svelte/store`
- **Subscribe v komponentách** přes `$store` syntax
- **TypeScript strict** — žádný `any` bez důvodu (`unknown` lepší)
- **Naming:** `camelCase` proměnné, `PascalCase` komponenty + types, `UPPER_SNAKE` konstanty
- **Tailwind utilities** primárně, custom CSS jen pro design tokens (`app.css`)
- **CSS classes pojmenovaní:** používej Tailwind, custom třída jen kde nezbytné s prefix `zh-`

### 11.2 Backend (Rust)

- **Modules:** `services/` = doménová logika (čistý Rust, nebavi se Tauri), `commands/` = thin wrappers s `#[tauri::command]`
- **Errors:** vše vrací `Result<T, AppError>`
- **Async:** `async fn` defaultně, `tokio::task::spawn_blocking` pro CPU-bound
- **State:** sdílené přes `tauri::State<'_, T>` parametry
- **Dependencies:** `serde`, `tokio`, `reqwest`, `thiserror`, `directories`, `sysinfo`
- **Naming:** `snake_case` všude, `PascalCase` typy, `SCREAMING_SNAKE_CASE` konstanty
- **No `unwrap()` v produkční cestě** — `expect("…")` s rozumnou message OK pro init/setup

### 11.3 Git

- **Commit style:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`)
- **Co-authored:** `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` na konci message
- **Tags:** semver `vMAJOR.MINOR.PATCH` (např `v2.0.0`)
- **Pre-release:** `vMAJOR.MINOR.PATCH-N` (numeric, NSIS/MSI compat)

---

## Část 12 — Closed feedback od uživatele (history)

- **2026-04-30**: User chce migrovat z customtkinter na Tauri. Důvod: nestability + výkon + black-rect bug po withdraw/deiconify, který se nepodařilo opravit ani v 3 patch verzích (v1.7.9–v1.7.11).
- **2026-04-30**: Po porovnání PoC PySide6 vs Tauri uživatel zvolil Tauri.
- **2026-05-01**: Po Phase 1 buildu (Home + Settings + foundation) je uživatel spokojený. Žádá:
  - Použít stejnou složku (`zeddihub_tools_desktop`, ne podsložku `zeddihub_v2/`)
  - Plnou feature parity s Pythonem
  - Detailní CLAUDE.md jako reference (TENTO SOUBOR)

---

*Aktualizováno: 2026-05-01 · Po každém migrovaném panelu doplnit do Části 10 a relevantní podsekce v Části 3. Při nové funkci přidat do Části 3 a Části 7 (IPC).*
