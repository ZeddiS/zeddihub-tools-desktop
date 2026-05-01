# ZeddiHub Tools (v2)

Desktop nástroje pro adminy CS2 / CS:GO / Rust serverů.

> **Status:** Migrační větev — Tauri 2 + SvelteKit + Rust. Aktuální verze
> 2.0.0-alpha (Phase 1 hotová: Home + Settings + foundation). Plná
> feature-parity s předchozí Python/customtkinter verzí (v1.7.12)
> v plánu pro v2.0.0 final. Detail: [`MIGRATION.md`](MIGRATION.md) +
> [`CLAUDE.md`](CLAUDE.md).
>
> Předchozí Python verze žije v [`legacy/`](legacy/) — buildable, ale
> není aktivně vyvíjená.

## Stack

| Vrstva | Technologie |
|---|---|
| Backend | Rust 1.95 + Tokio async runtime |
| App framework | Tauri 2 |
| Frontend | SvelteKit 2 (Svelte 5 runes) + TypeScript |
| Styling | Tailwind CSS 3 + CSS variables (theme tokens) |
| Ikony | lucide-svelte (tree-shakeable, žádný TTF download) |
| HTTP klient | reqwest (rustls-tls, async) |
| Crypto | chacha20poly1305 (Fernet ekvivalent pro auth.enc) |
| Sys info | sysinfo crate |

## Adresářová struktura

```
zeddihub_tools_desktop/
├── package.json                   # SvelteKit + Tauri deps
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── postcss.config.js
│
├── src/                           # Frontend (SvelteKit + TS)
│   ├── app.html, app.css
│   ├── routes/                    # File-based routing
│   │   ├── +layout.svelte         # Header + Sidebar shell
│   │   ├── +page.svelte           # Home
│   │   ├── settings/+page.svelte
│   │   └── ... (24 panel routes)
│   └── lib/
│       ├── api/                   # Tauri IPC wrappers (typed)
│       ├── stores/                # Svelte stores (theme/locale/auth)
│       ├── components/{ui,layout,panels}
│       └── i18n/{cs,en}.ts
│
├── src-tauri/                     # Backend (Rust)
│   ├── Cargo.toml, tauri.conf.json
│   ├── icons/, capabilities/
│   └── src/
│       ├── main.rs, lib.rs
│       ├── error.rs               # AppError enum
│       ├── commands/              # #[tauri::command] handlers
│       └── services/              # Business logic
│
├── legacy/                        # Python verze (v1.7.12) — archiv
│   ├── gui/                       # všechny .py panely
│   ├── app.py, main.py
│   └── _build_clean.bat, requirements.txt, ...
│
├── assets/                        # Sdílené (logo, banner, fonts)
├── poc/                           # PoC artefakty (PySide6 vs Tauri)
├── CLAUDE.md                      # Migrační referenční dokument
├── MIGRATION.md                   # Týdenní migration plán
└── README.md
```

## Setup

### Závislosti
- **Rust 1.70+**: <https://www.rust-lang.org/tools/install>
- **Node.js 18+**: <https://nodejs.org/>
- **Visual Studio Build Tools** (Windows, jen pro Rust linker)
- **WebView2** runtime (Win11 OK; Win10: <https://developer.microsoft.com/microsoft-edge/webview2/>)

### Spuštění (dev mode, hot reload)

```cmd
npm install
npm run tauri:dev
```

První spuštění ~5 min (kompilace Rust crates), další iterace ~5 s.

### Build production

```cmd
npm run tauri:build
```

Výstupy:
- `src-tauri/target/release/zeddihub-tools.exe` — standalone (~17 MB)
- `src-tauri/target/release/bundle/nsis/ZeddiHub Tools_*-setup.exe` — NSIS installer (~4 MB)
- `src-tauri/target/release/bundle/msi/ZeddiHub Tools_*.msi` — MSI (~6 MB)

## Build legacy Python verze

Python verze (v1.7.12) zůstává buildable v podsložce `legacy/`:

```cmd
cd legacy
pip install -r requirements.txt
.\_build_clean.bat
```

Výstup: `legacy/dist/ZeddiHubTools.exe` (28 MB).

## Co je hotovo (Phase 1)

- ✅ Project scaffold (Tauri 2 + SvelteKit + TS + Tailwind)
- ✅ Layout shell (Header / Sidebar / Content router)
- ✅ Theme store + persistence (dark/light) přes localStorage
- ✅ Locale store + i18n (cs/en) přes Svelte derived store
- ✅ Tray icon + minimize-to-tray (Tauri native, **žádný black-rect bug**)
- ✅ HTTP cache modul (Rust, in-memory TTL, stale-on-failure fallback)
- ✅ Auth REST klient (Rust, talks to `https://zeddihub.eu/api/auth/*`, encrypted token storage)
- ✅ HomePanel (cards + GitHub stats + login card + recommended grid + news section)
- ✅ SettingsPanel skeleton (account / appearance / language / data / updates tabs)
- ✅ 24 stub stránek pro ostatní panely

## Co bude dál

Viz [`MIGRATION.md`](MIGRATION.md) — týdenní plán pro 24 zbývajících panelů + system features (updater, telemetrie, RCON, A2S, plugin manager).

## IPC contract

Pojmenování: `<doména>_<akce>` (`auth_login`, `http_fetch_json`, …).

Errors: každý command vrací `Result<T, AppError>`; frontend handluje přes
`try { await invoke(...) } catch (e) { ... }`. `AppError` se serializuje
do `{ key, message, status? }` pro snadné parsování v JS.

Plný IPC seznam viz [`CLAUDE.md` Část 7](CLAUDE.md).

## Auto-update přechod z Python verze

Stará v1.7.x detekuje `v2.0.0` tag v GitHub Releases a transparentně
nainstaluje novou Tauri verzi. Bridge migrator přesune existující data
(auth.enc, settings.json, sticky notes, presety) do nového formátu
(`%LOCALAPPDATA%\ZeddiHub\Tools\`). Detail viz CLAUDE.md Část 9.

## Licence

Proprietární. © ZeddiHub (ZeddiS), 2026.
