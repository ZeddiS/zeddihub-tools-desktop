# ZeddiHub Tools — v2 (Tauri + SvelteKit)

> **Status:** Phase 1 (foundation + Home + Settings) — work in progress.
> Plný roadmap viz [`/MIGRATION.md`](../MIGRATION.md) v root repu.

## Stack

| Vrstva | Technologie |
|---|---|
| Backend | Rust 1.95 + Tokio async runtime |
| App framework | Tauri 2 |
| Frontend | SvelteKit 2 (Svelte 5 runes) + TypeScript |
| Styling | Tailwind CSS 4 + CSS variables (theme tokens) |
| Ikony | lucide-svelte (tree-shakeable, žádný TTF download) |
| HTTP klient | reqwest (rustls-tls, async) |
| Crypto | chacha20poly1305 (Fernet ekvivalent pro auth.enc) |
| Sys info | sysinfo crate |

## Adresář (zkráceně)

```
zeddihub_v2/
├── src/                         # Frontend (SvelteKit + TS)
│   ├── routes/                  # File-based routing
│   │   ├── +layout.svelte       # Header + Sidebar shell
│   │   ├── +page.svelte         # Home
│   │   ├── settings/+page.svelte
│   │   └── ... (24 stub pages)
│   └── lib/
│       ├── api/                 # Tauri IPC wrappers (typed)
│       ├── stores/              # Svelte stores (theme/locale/auth)
│       ├── components/{ui,layout}
│       └── i18n/{cs,en}.ts
└── src-tauri/                   # Rust backend
    ├── Cargo.toml
    ├── tauri.conf.json
    ├── icons/
    └── src/
        ├── main.rs              # entry → lib::run()
        ├── lib.rs               # Tauri Builder
        ├── error.rs             # AppError + serde
        ├── commands/            # #[tauri::command] handlers
        └── services/            # Business logic (auth, http_cache, crypto, tray)
```

## Setup

### Závislosti
- Rust 1.70+: <https://www.rust-lang.org/tools/install>
- Node.js 18+: <https://nodejs.org/>
- Visual Studio Build Tools (Windows, jen pro Rust linker)
- WebView2 (Win11 OK; Win10 viz <https://developer.microsoft.com/microsoft-edge/webview2/>)

### Spuštění (dev mode, hot reload)

```cmd
cd zeddihub_v2
npm install
npm run tauri:dev
```

První spuštění ~5 min (kompilace Rust crates), další iterace ~5 s.

### Build production EXE

```cmd
npm run tauri:build
```

Výstup:
- `src-tauri/target/release/zeddihub-tools.exe` — standalone (~13–18 MB)
- `src-tauri/target/release/bundle/nsis/ZeddiHub Tools_2.0.0-alpha.1_x64-setup.exe`
- `src-tauri/target/release/bundle/msi/ZeddiHub Tools_2.0.0-alpha.1_x64_en-US.msi`

## Co je hotovo (Phase 1)

- ✅ Project scaffold (Tauri 2 + SvelteKit + TS + Tailwind)
- ✅ Layout shell (Header / Sidebar / Content router)
- ✅ Theme store + persistence (dark/light) via localStorage
- ✅ Locale store + i18n (cs/en) přes Svelte derived store
- ✅ Tray icon + minimize-to-tray (Tauri native, žádný black-rect bug)
- ✅ HTTP cache modul (Rust, in-memory TTL, stale-on-failure fallback)
- ✅ Auth REST klient (Rust, talks to `https://zeddihub.eu/api/auth/*`, encrypted token storage)
- ✅ HomePanel (cards + GitHub stats + login card + recommended grid + news section)
- ✅ SettingsPanel (account / appearance / language / data / updates tabs)
- ✅ 24 stub stránek pro ostatní panely (každá s plánovaným týdnem migrace)

## Co bude dál

Viz `MIGRATION.md` — týdenní plán pro panely 1-25 + system features
(updater, telemetrie, RCON, A2S, plugin manager).

## Konvence kódu

### Frontend (Svelte 5)
- **Runes**: `$state(value)` místo `let`, `$derived(expr)` místo reactive `$:`, `$effect(() => {})` místo `onMount` pro side effects
- **Stores** pro globální state, `$store` syntax pro subscribe
- **Tailwind utilities** primárně, custom CSS jen pro design tokens (`app.css`)
- **TypeScript strict mode** — všechny props typované

### Backend (Rust)
- **Doménově orientované moduly** v `services/` (čistý Rust)
- **`commands/`** = thin wrapper kolem služeb, pouze `#[tauri::command]` handlers
- **`AppError`** unified error enum, serializovatelný do JSON pro frontend
- **`State<'_, T>`** pro shared services (HttpCache, AuthState)
- **`async fn`** kdekoliv jde, blocking jen pro CPU-bound věci v `tokio::task::spawn_blocking`

## IPC contract

Pojmenování: `<doména>_<akce>` (`auth_login`, `http_fetch_json`, …).

Errors: každý command vrací `Result<T, AppError>`; frontend handluje
přes `try { await invoke(...) } catch (e) { ... }`. `AppError` se
serializuje do `{ key, message, status? }` pro snadné parsování v JS.

## Vztah ke staré aplikaci

Stará Python verze žije dál v `gui/` na master branch (v1.7.12 je její
poslední tag). Obě verze se nyní paralelně buildují:
- Python EXE: `dist/ZeddiHubTools.exe` (28 MB)
- Tauri EXE: `zeddihub_v2/src-tauri/target/release/zeddihub-tools.exe` (~13 MB)

Po dokončení migrace:
1. `gui/` se přejmenuje na `gui_legacy/` (pro reference)
2. Tauri verze převezme `ZeddiHubTools.exe` název pro auto-updater přechod
3. Last v1.7.x release detekuje v2.0.0 v GH Releases a stáhne installer
   místo nového Python EXE — uživatel projde transparentní upgrade
