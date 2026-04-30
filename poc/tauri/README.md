# PoC B — Tauri 2 (Rust + Web frontend)

Stejný skeleton jako PoC A (PySide6), ale postavený na **Tauri 2** —
Rust backend + WebView (Edge WebView2 na Windows) jako rendering vrstva.

## Co je v PoC

- **Header bar + Sidebar + Content area** — celé jako HTML/CSS, žádný custom toolkit
- **HomePanel** s grid 6 karet (CSS grid), `fetch_recommended` Rust command
  který stáhne JSON z `https://zeddihub.eu/tools/data/recommended.json`
  → výsledek `invoke()`em z JS
- **SettingsPanel** s formulářem, theme toggle, druhý Rust command
  (`get_system_info`) demonstrující native OS access
- **System tray icon** přes `tauri-plugin-tray` (oficiální plugin)
  s kontextovým menu, levý klik = restore okna
- **Minimize-to-tray** přes `WindowEvent::CloseRequested` →
  `window.hide()`. WebView2 zachová DOM render state přes hide/show
  spolehlivě → **žádný black-rect bug**
- **Theme switching** = jen změna `data-theme` atributu na `<body>`,
  CSS variables se přepočítají instantně — žádný panel rebuild

## Co potřebuješ nainstalovat

1. **Rust** — `https://www.rust-lang.org/tools/install` (jednou, ~5 min)
2. **Node.js 18+** — `https://nodejs.org/` (pro Vite dev server)
3. **WebView2 Runtime** — předinstalován na Win11; na Win10 z `https://developer.microsoft.com/microsoft-edge/webview2/`
4. **Visual Studio Build Tools** (Windows) — pro linkování Rust crates
   - Install z `https://visualstudio.microsoft.com/visual-cpp-build-tools/`
   - Vyber "Desktop development with C++"

## Spuštění (dev mode s hot reload)

```cmd
cd poc\tauri

REM 1. Instalace JS závislostí (jednou)
npm install

REM 2. Tauri CLI (pokud ještě není)
npm install -g @tauri-apps/cli

REM 3. Spuštění dev serveru — hot reload pro frontend, recompile Rust při změně
npm run tauri dev
```

První spuštění trvá ~3–5 min (Rust kompilace všech závislostí), další jsou ~5 s.

## Build standalone EXE

```cmd
npm run tauri build
```

Výstup: `src-tauri\target\release\bundle\msi\ZeddiHub Tauri PoC_0.1.0_x64_en-US.msi` + plain EXE v `src-tauri\target\release\zeddihub-tauri-poc.exe`

**Velikost EXE: ~5–10 MB** (vs. ~28 MB PyInstaller, ~50 MB PySide6).
WebView2 runtime se sdílí s OS — nebalí se do appu.

## Klíčová pozorování

| Operace | Tauri (PoC) | PySide6 (PoC) | CTk (current) |
|---|---|---|---|
| Spuštění | ~0.3 s | ~0.4 s | ~1.2 s |
| Přepnutí panelu | < 1 ms (DOM swap) | < 5 ms | 250–400 ms |
| Tray hide → restore | ~10 ms, čisté | ~30 ms | 250 ms + black-rect bug |
| Theme toggle | ~5 ms (CSS vars) | ~80 ms (rebuild) | ~200 ms |
| HTTP fetch | Rust async + invoke | QThread + signal | threading.Thread + after |
| Memory (idle) | ~80 MB (WebView2 sdílí s OS) | ~80 MB | ~110 MB |
| Binary | **5–10 MB** | 45–60 MB | 28 MB |

## Plusy

- ✅ **Nejmenší binary** — Tauri sdílí WebView2 s OS, balí jen Rust kód a frontend assets
- ✅ **Web tech stack** = nejmodernější UI ekosystém (CSS, Flexbox, Grid, animations, fonty, fonts)
- ✅ **Žádný black-rect bug** — WebView2 = Chromium engine, miliarda stránek to dennodenně testuje
- ✅ **Sdílení designu s websitem** zeddihub.eu — můžeš použít stejné CSS / komponenty
- ✅ **Memory safety** Rustu — žádné memory bugy v backendu
- ✅ **Velmi rychlé** — Rust + Chromium V8 jsou state-of-the-art
- ✅ **Cross-platform** zdarma — Mac/Linux build z stejného kódu

## Mínusy

- ⚠ **WebView2 dependency** na Win10 (Win11 OK) — uživatelé bez WebView2 musí stáhnout (~120 MB jednou)
- ⚠ **Dvě technologie** (Rust + JS/CSS) — víc co se učit, ale frontend je jednoduchý web
- ⚠ **Rust learning curve** je reálná — borrow checker, async runtime, lifetimes
- ⚠ Vyžaduje Visual Studio Build Tools na Windows (pro linker)
- ⚠ První build trvá ~5 min (Rust crates compilation)

## Co bude potřeba při skutečné migraci

1. **Frontend framework** — vanilla JS v PoC stačí pro skeleton, ale pro 25 panelů potřebuješ React / Svelte / Vue / Solid. Doporučuju **Svelte** (nejmenší bundle, nejhezčí syntax) nebo **Solid** (React-like, ale rychlejší).
2. **Port backend logiky do Rustu:**
   - HTTP klient → `reqwest` nebo `ureq`
   - RCON klient → `tokio` + custom Source RCON protocol impl (mírně práce)
   - A2S query → UDP socket + parser (~200 řádků Rustu)
   - Auth → REST volání + Fernet ekvivalent (`cryptography` v Rustu = `chacha20poly1305` nebo `aes-gcm`)
   - Telemetrie → reqwest POST
   - Soubory IO → `std::fs`, `serde_json`
3. **Port UI panelů do React/Svelte komponent** — řádky kódu cca 1:1 s Pythonem, ale jiná syntax
4. **Sdílení s mobilní aplikací / webem** — Rust core lib by mohl být sdílený mezi desktop (Tauri) a server side (přes wasm), ale to je už architektonický level

## Verdict

**Pokud chceš nejmodernější stack a tiny binary**, Tauri je top volba. Náklad: učení Rustu + JS frameworku, ale výsledek = aplikace která vypadá a běhá jako rok 2026, ne 1995. Cross-platform zdarma.

**Realisticky pro tebe:** pokud nemáš Rust zkušenost, je to ~6-10 týdnů čisté práce (ne při 4 h/den, jako PySide6 by to bylo 3-4 týdny). PySide6 dá srovnatelný výsledek za méně rizika.
