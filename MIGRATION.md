# ZeddiHub Tools — Migrace na Tauri 2 + Svelte 5

**Status:** Phase 1 (foundation + reference panels) — in progress
**Cíl:** plná feature-parity s aktuální Python/CTk aplikací (v1.7.12 baseline)
**Stack:** Tauri 2 (Rust backend) + SvelteKit (TypeScript frontend) + Tailwind CSS
**Lokace nového projektu:** `zeddihub_v2/`

Stará Python aplikace zůstává v repu jako `gui/` — zatímco se migruje, obě
mohou koexistovat. Po dokončení migrace se Python verze archivuje
(`gui_legacy/`) a nový build převezme `ZeddiHubTools.exe` název pro
auto-updater přechod.

---

## 🎯 Klíčová architektonická rozhodnutí

### Frontend stack
- **SvelteKit 2 (s adapter-static)** — file-based routing, TypeScript first-class, hot reload, malé bundles. SSR funkce nepoužíváme (desktop app).
- **Svelte 5 syntax (runes)** — `$state`, `$derived`, `$effect` místo starého `let`/reactive statements.
- **TypeScript** všude — IPC contract mezi Rustem a frontendem typovaný přes generované TS bindings.
- **Tailwind CSS 4** — utility-first, super malý production bundle po purge, design tokens v `tailwind.config.js`.
- **lucide-svelte** pro ikony (tree-shakeable, SVG, ne FontAwesome download).

### Backend stack
- **Tauri 2.x** — IPC commands, tray plugin, updater plugin, fs / shell / dialog plugins.
- **Rust 1.95+** — moduly podle domény: `auth`, `http`, `rcon`, `a2s_query`, `watchdog`, `crypto`, `paths`, `telemetry`.
- **`reqwest`** pro HTTP (place `ureq` z PoC, lépe se integruje s tokio).
- **`tokio`** async runtime (Tauri ho už používá).
- **`serde` + `serde_json`** pro JSON serializaci IPC.
- **`thiserror`** + custom Error enum pro error handling.
- **`chacha20poly1305`** nebo **`aes-gcm`** jako Fernet ekvivalent pro local credential storage.
- **`sysinfo`** crate pro PCToolsPanel sysinfo.
- **`directories`** crate pro per-platform data dir (`%LOCALAPPDATA%/ZeddiHub`).

### State management (frontend)
- **Svelte stores** (writable + derived) pro globální state: `auth`, `theme`, `locale`, `currentNav`.
- Per-panel local state přes `$state` runes.
- Persistence: Tauri's `app_data_dir` pro `settings.json`, encrypted store pro credentials.

### IPC contract
- Tauri commands typované — generované TS bindings z Rustu přes `tauri-specta` (volitelně) nebo manuálně.
- Pojmenování commands: `<doména>_<akce>` (e.g. `auth_login`, `http_fetch_json`, `rcon_send`).
- Errors: každý command vrací `Result<T, AppError>`, frontend handluje `try/catch` na `invoke()`.

### Routing
- File-based přes `src/routes/`:
  - `+layout.svelte` — sidebar + header shell
  - `+page.svelte` — Home (default)
  - `settings/+page.svelte`, `cs2/player/+page.svelte`, etc.
- Programmatic nav přes `goto('/cs2/player')`.

---

## 📅 Týdenní plán (10 týdnů, ~40 h/týden = full-time; 4 h/den = 20 týdnů)

### Týden 1 — Foundation (✅ dnes částečně)
- [x] Project scaffold (SvelteKit + Tauri + TS + Tailwind)
- [x] Layout shell (Sidebar + Header + Content router)
- [x] Theme store + persistence (dark/light)
- [x] Locale store + persistence (CZ/EN)
- [x] Tray icon + minimize-to-tray
- [x] HTTP cache module (Rust)
- [ ] Auth REST client (Rust): login, register, me, logout, admin_reset
- [ ] Encrypted credential storage (Rust, `chacha20poly1305`)
- [ ] Auth Svelte store + reactive UI

### Týden 2 — Top panels
- [ ] **HomePanel** (✅ dnes částečně) — cards, GitHub stats, login card, PC Tools home grid, news section
- [ ] **AboutPanel** — kontakt, verze, ikony, links
- [ ] **NewsPanel** — GitHub Releases feed
- [ ] **LinksPanel** — quick links, DNS lookup, port checker, file uploader, credits
- [ ] **AppsPanel** — katalog z `quick_links.json` s WebView2 embed (Tauri má vlastní webview API)

### Týden 3 — Settings + Login
- [ ] **SettingsPanel** — tabs: Účet / Vzhled / Jazyk / Datová složka / Backup / Aktualizace
- [ ] **LoginDialog** — overlay s Login + Register tabs, validace, error states, captcha (skip pro desktop kvůli APP_SECRET)
- [ ] First-launch wizard (data dir picker)

### Týden 4 — CS2 Player Tools (kritické pro uživatele)
- [ ] **CS2PlayerPanel** — TabView s 5 sekcemi:
  - Crosshair generator + live Canvas preview (HTML `<canvas>` API)
  - Viewmodel editor + zbraň silhouette preview
  - Autoexec config (kategorizované sekce)
  - Practice config
  - Buy Binds Generator
- [ ] Sdílené `_label`, `_btn`, `_section`, `_entry_row` jako Svelte komponenty v `lib/components/form/`

### Týden 5 — CS2 Server Tools + Keybind
- [ ] **CS2ServerPanel** — Server.cfg, Gamemode presety (7 módů), Map Group, RCON klient (Rust TCP socket)
- [ ] **CS2KeybindPanel** — vizuální klávesnice (HTML + CSS Grid), drag-drop pro bind assignment

### Týden 6 — CSGO + Rust panely (= fork CS2 + úpravy)
- [ ] **CSGOPlayerPanel** + **CSGOServerPanel** + **CSGOKeybindPanel** — sdílí komponenty s CS2
- [ ] **RustPlayerPanel** — sensitivity calc, Client CFG, Bindy, Tipy
- [ ] **RustServerPanel** — Config gen + .bat skript, RCON klient (Rust WebSocket pro Rust facepunch RCON), Plugin Manager (regex Oxide bulk-fix)

### Týden 7 — Game Tools + Watchdog
- [ ] **TranslatorPanel** — Google/MyMemory/LibreTranslate/DeepL API, JSON/TXT/LANG file IO přes Tauri fs plugin
- [ ] **SensitivityPanel** — converter mezi 20 hrami, DPI calc
- [ ] **EDPIPanel** — kalkulačka, pro player tabulka
- [ ] **PingTesterPanel** — TCP socket latence, 10 herních serverů
- [ ] **WatchdogPanel** — periodický monitoring serverů, UDP A2S query v Rustu, alert log

### Týden 8 — PC Tools (5 sub-panelů)
- [ ] **PCSysInfoPanel** — `sysinfo` crate, OS / CPU / RAM / Disk / GPU / Net info
- [ ] **PCNetToolsPanel** — DNS Flush (Tauri shell exec `ipconfig`), DNS Scanner (`nslookup` parsing v Rustu), Speedtest (HTTP download), IP Geolocation, Port Checker
- [ ] **PCUtilityPanel** — Auto Clicker (Rust + `enigo` crate), Stopky/Odpočet/Časovač, Temp Cleaner, Shutdown Timer, Process List (sysinfo)
- [ ] **PCGameOptPanel** — placeholders / future
- [ ] **PCAdvancedPanel** — placeholders / future
- [ ] **UtilityHubPanel** — kontejner s tabs (jako CS2PlayerPanel pattern)

### Týden 9 — System integrace
- [ ] **Auto-updater** přes `tauri-plugin-updater` + GitHub Releases
- [ ] **Telemetrie** — fire-and-forget POST na `https://zeddihub.eu/tools/telemetry.php`
- [ ] **External tools** — downloadable modules (admin only)
- [ ] **Tools download panel**
- [ ] **Sessions management** (admin REST API)

### Týden 10 — Polish + cutover
- [ ] Splash screen
- [ ] First-launch wizard polish
- [ ] Migration tool: konvertuje uživatelský data folder z Python verze (auth.enc, settings.json) do Rust formátu
- [ ] Build pipeline: `npm run tauri build` → release artifacts (NSIS installer + MSI + standalone EXE)
- [ ] Auto-update přechod: starý ZeddiHubTools.exe (Python) detekuje že je dostupná verze 2.0.0+ (Tauri) a stáhne nový installer místo nového Python EXE
- [ ] Code signing (volitelně) — pokud máš Microsoft Authenticode cert
- [ ] Dokumentace: README v zeddihub_v2/, CHANGELOG.md, in-app About panel s migration notes

### Týden 11+ — Long-tail (dle priority)
- [ ] **Macros panel** (record + engine + hotkey manager) — Rust + `rdev` nebo `enigo` crates
- [ ] **PCAdvancedPanel** features dle plánu
- [ ] Mobilní aplikace UI sjednocení (jiný projekt, sdílí backend REST API)

---

## 🗺 Mapa Python → Rust/Svelte

| Python modul | Tauri/Svelte ekvivalent | Status |
|---|---|---|
| `gui/main_window.py` (1700 řádků) | `src/routes/+layout.svelte` + `src/lib/components/Sidebar.svelte` + `Header.svelte` | ⏳ Phase 1 |
| `gui/auth.py` + `gui/api_auth.py` | `src-tauri/src/services/auth.rs` + `src/lib/stores/auth.ts` | ⏳ Phase 1 |
| `gui/themes.py` | `src/lib/stores/theme.ts` + `tailwind.config.js` design tokens | ✅ scaffold |
| `gui/locale.py` + `locale/*.json` | `src/lib/stores/locale.ts` + `src/lib/i18n/{cs,en}.ts` | ✅ scaffold |
| `gui/icons.py` (FontAwesome) | `lucide-svelte` (tree-shaken, žádný TTF download) | ✅ |
| `gui/tray.py` | `src-tauri/src/services/tray.rs` + Tauri tray plugin | ✅ Phase 1 |
| `gui/updater.py` | `tauri-plugin-updater` | ⏳ Týden 9 |
| `gui/telemetry.py` | `src-tauri/src/services/telemetry.rs` | ⏳ Týden 9 |
| `gui/http_cache.py` (z v1.7.9) | `src-tauri/src/services/http_cache.rs` | ✅ Phase 1 |
| `gui/widgets.py` (make_button, etc.) | `src/lib/components/ui/{Button,Card,Entry,Tabview}.svelte` | ⏳ Phase 1 |
| `gui/panels/home.py` | `src/routes/+page.svelte` | ⏳ Phase 1 |
| `gui/panels/cs2.py` Player | `src/routes/cs2/player/+page.svelte` | Týden 4 |
| `gui/panels/cs2.py` Server | `src/routes/cs2/server/+page.svelte` | Týden 5 |
| `gui/panels/keybind.py` | `src/routes/cs2/keybind/+page.svelte`, ... | Týden 5–6 |
| RCON klient (`socket` + Source RCON proto) | `src-tauri/src/services/rcon.rs` (`tokio::net::TcpStream`) | Týden 5 |
| A2S query (UDP) | `src-tauri/src/services/a2s.rs` (`tokio::net::UdpSocket`) | Týden 7 |
| `pystray` tray menu | `tauri-plugin-tray` (oficiální) | ✅ scaffold |
| `psutil` (volitelný) | `sysinfo` crate (vždy dostupný) | Týden 8 |
| `pyautogui` / `pynput` (Auto Clicker, Macros) | `enigo` crate (Win/Mac/Linux) | Týden 8 / 11+ |
| `cryptography.fernet` | `chacha20poly1305` crate | ⏳ Phase 1 |

---

## 🔌 IPC contract (Rust ↔ TS)

Konvence pojmenování `<doména>_<akce>`. Všechny commandy vracejí `Result<T, AppError>`.

```rust
// src-tauri/src/commands/auth.rs
#[tauri::command]
async fn auth_login(identifier: String, password: String) -> Result<UserSession, AppError>;
#[tauri::command]
async fn auth_register(username: String, email: String, password: String) -> Result<UserSession, AppError>;
#[tauri::command]
async fn auth_me() -> Result<UserDto, AppError>;
#[tauri::command]
async fn auth_logout() -> Result<(), AppError>;
#[tauri::command]
async fn auth_admin_reset(target: String, new_password: String) -> Result<(), AppError>;
```

```typescript
// src/lib/api/auth.ts
import { invoke } from "@tauri-apps/api/core";

export type UserSession = { user: UserDto; token: string; expiresAt: number };
export type UserDto = { id: number; username: string; email: string; role: string; isAdmin: boolean };

export const authApi = {
  login:  (identifier: string, password: string) => invoke<UserSession>("auth_login", { identifier, password }),
  register: (username: string, email: string, password: string) => invoke<UserSession>("auth_register", { username, email, password }),
  me: () => invoke<UserDto>("auth_me"),
  logout: () => invoke<void>("auth_logout"),
};
```

---

## 🔐 Bezpečnost

- **APP_SECRET** (pro hCaptcha bypass) — v Rustu jako `const`, nikoli v JS — nebudou mít webové stránky šanci ho přečíst.
- **Token storage** — encrypted at rest přes `chacha20poly1305` s klíčem odvozeným z machine ID (Win: `MachineGuid`).
- **Tauri capabilities** — minimum needed permissions v `default.json`.
- **CSP** — strict, žádný `unsafe-eval`.
- **HTTPS only** pro REST API.

---

## 🚢 Distribuce

### Build
```bash
cd zeddihub_v2
npm install
npm run tauri build
```

Výstup:
- `src-tauri/target/release/zeddihub-tools.exe` — standalone (~13–18 MB)
- `src-tauri/target/release/bundle/nsis/ZeddiHub Tools_2.0.0_x64-setup.exe` — installer (~3–5 MB)
- `src-tauri/target/release/bundle/msi/ZeddiHub Tools_2.0.0_x64_en-US.msi` — MSI

### Auto-update přechod z Python verze
1. Python v1.7.x s GitHub Releases polling detekuje tag `v2.0.0` (semver newer)
2. Stará v1.x updater stahuje `ZeddiHubTools.exe` asset → ten ale obsahuje **migraci**:
   - Bootstrap mode: zjistí stará data folder
   - Migruje `auth.enc` (Fernet → chacha20poly1305) jednorázově
   - Spustí nový Tauri install z bundled installer
   - Smaže staré `.exe` po prvním úspěšném spuštění nového
3. Pro čisté instalace: GitHub Releases má primární asset jen NSIS installer

### Code signing
- Volitelné, ale doporučené (předpokládám že nemáš zatím Authenticode cert)
- Bez signingu Win SmartScreen ukáže warning při prvním spuštění
- DigiCert / SignPath / GlobalSign cert ~$200/rok
- Lze implementovat později, není blocker

---

## 📂 Struktura projektu zeddihub_v2/

```
zeddihub_v2/
├── package.json                    # SvelteKit + Tauri + Tailwind deps
├── svelte.config.js                # adapter-static (no SSR)
├── vite.config.ts                  # port 1420, env prefix
├── tailwind.config.js              # design tokens (theme colors)
├── tsconfig.json                   # strict mode, path aliases
├── tauri.conf.json                 # window, bundle, identifier
│
├── src/
│   ├── app.html                    # root HTML template
│   ├── app.css                     # Tailwind base + custom CSS vars
│   ├── routes/
│   │   ├── +layout.svelte          # Sidebar + Header + Content shell
│   │   ├── +layout.ts              # SSR off, prerender
│   │   ├── +page.svelte            # Home (default)
│   │   ├── settings/+page.svelte
│   │   ├── about/+page.svelte
│   │   ├── news/+page.svelte
│   │   ├── links/+page.svelte
│   │   ├── apps/+page.svelte
│   │   ├── cs2/
│   │   │   ├── player/+page.svelte
│   │   │   ├── server/+page.svelte
│   │   │   └── keybind/+page.svelte
│   │   ├── csgo/...
│   │   ├── rust/...
│   │   ├── tools/{translator,sensitivity,edpi,ping}/+page.svelte
│   │   ├── pc/{sysinfo,nettools,utility,gameopt,advanced}/+page.svelte
│   │   ├── watchdog/+page.svelte
│   │   └── tools-download/+page.svelte
│   │
│   └── lib/
│       ├── api/                    # Tauri IPC wrappers (typed)
│       │   ├── auth.ts
│       │   ├── http.ts
│       │   ├── rcon.ts
│       │   ├── a2s.ts
│       │   └── system.ts
│       ├── stores/                 # Svelte stores
│       │   ├── auth.ts
│       │   ├── theme.ts
│       │   ├── locale.ts
│       │   └── nav.ts
│       ├── components/
│       │   ├── ui/                 # Reusable: Button, Card, Entry, Tabs, Modal
│       │   ├── layout/             # Sidebar, Header, ContentArea
│       │   └── panels/             # Shared panel blocks (LoginCard, ServerCard...)
│       └── i18n/
│           ├── cs.ts
│           └── en.ts
│
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── build.rs
│   ├── icons/                      # 32, 64, 128, 256, 128@2x + ico
│   ├── capabilities/default.json   # IPC permissions
│   └── src/
│       ├── main.rs                 # entry point (just calls lib::run)
│       ├── lib.rs                  # tauri::Builder + register commands
│       ├── error.rs                # AppError enum + From impls
│       ├── commands/               # #[tauri::command] thin wrappers
│       │   ├── mod.rs
│       │   ├── auth.rs
│       │   ├── http.rs
│       │   ├── rcon.rs
│       │   ├── a2s.rs
│       │   ├── system.rs
│       │   └── settings.rs
│       └── services/               # Pure Rust business logic
│           ├── mod.rs
│           ├── auth.rs             # REST client + token mgmt
│           ├── crypto.rs           # chacha20poly1305 encrypt/decrypt
│           ├── http_cache.rs       # in-memory + disk TTL cache
│           ├── rcon.rs             # Source RCON over TCP
│           ├── a2s.rs              # Steam A2S_INFO over UDP
│           ├── paths.rs            # data_dir / config_dir resolver
│           ├── tray.rs             # system tray builder
│           ├── telemetry.rs        # fire-and-forget POST
│           └── settings.rs         # settings.json read/write
│
└── static/                         # static assets (logos, banner)
    ├── logo.png
    └── banner.png
```

---

## 🧪 Testovací matice

| Co testovat | PoC ✅ | v2 cíl |
|---|---|---|
| Spuštění a startup time | ~200 ms | < 300 ms |
| Theme toggle (perceptual) | < 5 ms | < 50 ms |
| Tray hide → restore (ŽÁDNÝ black-rect) | ✅ | ✅ povinné |
| Cold panel switch | ~1 ms (DOM swap) | < 10 ms |
| HTTP cache hit | n/a | < 1 ms (in-memory) |
| HTTP cache miss | ~600ms (real fetch) | < 700 ms |
| RCON connect + send + recv | n/a | < 200 ms LAN |
| A2S query (UDP) | n/a | < 100 ms |
| Login (REST API call) | n/a | < 800 ms |
| Bundle size (NSIS) | 3 MB | < 10 MB |
| Standalone EXE | 13 MB | < 20 MB |
| RAM idle | ~80 MB | < 120 MB |

---

## ❓ Open decisions (rozhodneme později)

1. **CSS framework:** Tailwind 4 vs vanilla CSS s variables. Defaultně Tailwind — produktivita.
2. **Form library:** Felte vs vlastní Svelte action helpers. Defaultně vlastní — méně závislostí.
3. **Tabulky** (PCSysInfoPanel, processes, history): vlastní Svelte komponenta vs `@tanstack/svelte-table`. Defaultně vlastní — naše tabulky jsou jednoduché.
4. **Crosshair preview canvas:** HTML `<canvas>` API přímo, nebo Konva.js / Pixi.js? Defaultně vanilla canvas — naše kresba je jednoduchá.
5. **Macros recording:** Rust `rdev` vs `enigo` vs vlastní WinAPI hook. Defaultně `enigo` (cross-platform) + WinAPI low-level fallback pro recording.
6. **WebView2 fallback** (Win10 bez něj): Tauri 2 má bootstrapper flow přes `tauri-plugin-updater`? Nutno ověřit.

---

## 🚦 Status checkpoint

| Phase | Status | Demo build |
|---|---|---|
| Phase 0 — PoC | ✅ done | [poc-builds release](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/tag/poc-builds) |
| Phase 1 — Foundation + Home | 🟡 in progress | TBD |
| Phase 2 — Top panels | ⏳ planned | TBD |
| Phase 3 — CS2 Player | ⏳ planned | TBD |
| Phase 4 — CS2 Server + Keybind | ⏳ planned | TBD |
| Phase 5 — CSGO + Rust | ⏳ planned | TBD |
| Phase 6 — Game Tools + Watchdog | ⏳ planned | TBD |
| Phase 7 — PC Tools | ⏳ planned | TBD |
| Phase 8 — System integrace | ⏳ planned | TBD |
| Phase 9 — Polish + cutover | ⏳ planned | TBD |
