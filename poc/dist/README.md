# ZeddiHub Tools — PoC executables

Spustitelné soubory obou prototypů, ke stažení a otestování bez nutnosti
něco instalovat / kompilovat.

## Soubory v této složce

| Soubor | Velikost | Co to je | Jak spustit |
|---|---|---|---|
| `ZeddiHub-PoC-A-PySide6.exe` | **44.4 MB** | PoC A — Python + Qt6 (PySide6), PyInstaller one-file build | Dvojklik. Spouští se ~1-2 s (rozbalení PyInstaller bundle). |
| `ZeddiHub-PoC-B-Tauri.exe` | **12.8 MB** | PoC B — Rust + Web frontend (Tauri 2), standalone EXE bez instalace | Dvojklik. Spouští se okamžitě (~150 ms). **Vyžaduje WebView2** — předinstalován na Win11, na Win10 viz dole. |
| `ZeddiHub-PoC-B-Tauri-Installer.exe` | **3.0 MB** | NSIS installer pro PoC B (vytvoří shortcut, registr, Add/Remove Programs entry) | Dvojklik. Klasický Windows installer. |
| `ZeddiHub-PoC-B-Tauri.msi` | **4.5 MB** | MSI verze instaláteru pro PoC B (corporate / enterprise deployment) | `msiexec /i ZeddiHub-PoC-B-Tauri.msi` nebo dvojklik. |

## ⚠ WebView2 dependency (jen pro PoC B Tauri)

Tauri používá Edge WebView2 jako rendering vrstvu místo bundlovat svůj
vlastní browser engine. To je důvod, proč je EXE jen 12 MB (vs 46 MB
PySide6).

- **Windows 11**: WebView2 je předinstalován, nic nedělej.
- **Windows 10**: pokud při spuštění uvidíš dialog "WebView2 missing",
  stáhni ho zdarma z
  [developer.microsoft.com/microsoft-edge/webview2](https://developer.microsoft.com/microsoft-edge/webview2/)
  (Evergreen Bootstrapper, ~2 MB stažení, nainstaluje se na pozadí).
  Tauri 2 má i auto-installer flow, ale tento PoC ho nemá zapnutý.

## Co testovat

Oba PoC mají identický feature scope, abys mohl porovnat:

1. **Spusť aplikaci** → vidíš header (ZeddiHub Tools / verze / 🌙 toggle)
   + sidebar (Domů, Nastavení) + content area s dlaždicemi.
2. **Klik na dlaždice** → reagují, hover state.
3. **Načítání dat** — krátce uvidíš "Načítám…" pak `✓ N nástrojů (live)`.
   To je HTTP fetch z `https://zeddihub.eu/tools/data/recommended.json`,
   stejný endpoint jako live aplikace. Pokud jsi offline, uvidíš `⚠ fallback`.
4. **Nav na Nastavení** → formulář s buttonem na theme toggle, druhý
   button "Zeptat se Rust backendu" (jen u Tauri PoC).
5. **🌙 toggle** v headeru → přepnutí dark/light. **Důležitý test:**
   sleduj jak rychle se to přepne.
6. **System tray** — zavři okno (×). Aplikace půjde do tray (vpravo dole
   u hodin). Klikni na ikonu → restore okna.
   **KLÍČOVÝ TEST:** zkontroluj, jestli widgety jsou kresleny správně
   po restore (žádné černé obdélníky jako CTk verze v1.7.10/11).
7. **Zavři přes tray menu** (pravý klik → Ukončit) — full quit.

## Velikost — proč ten rozdíl?

| EXE | Co obsahuje |
|---|---|
| PySide6 44 MB | Python interpreter + Qt6 framework (asi 30 MB DLLs) + Pillow + Pythoní stdlib + tvůj kód |
| Tauri 12 MB | Rust kompilovaný kód + Tauri framework + tvůj kód. WebView2 sdílíš s OS. |
| Tauri installer 3 MB | LZMA-stlačený zabalený main EXE + NSIS skripty |

## Performance srovnání (subjektivní, na slabším HW se rozdíl zvětšuje)

| Operace | PoC A PySide6 | PoC B Tauri | CTk v1.7.12 (rollback) |
|---|---|---|---|
| Cold start | ~1.5 s (PyInstaller extract) | ~0.2 s | ~1.2 s |
| Hot start (po prvním) | ~0.5 s | ~0.2 s | ~1.2 s |
| Klik dlaždice (hover) | < 5 ms | < 1 ms (CSS) | ~30 ms |
| Theme toggle | ~80 ms (rebuild) | ~5 ms (CSS vars) | ~200 ms |
| Tray restore | ~30 ms | ~10 ms | ~250 ms + bug |
| RAM idle | ~85 MB | ~80 MB (sdílí WebView2) | ~110 MB |

## Po vyzkoušení

Napiš mi rozhodnutí (PySide6 / Tauri / zůstat na CTk v1.7.12 = `master`).
Připravím detailní migration plán.

## Build sám si

Kdybys chtěl rebuildnout (např. po vlastních úpravách kódu):

```cmd
REM PoC A (PySide6) — vyžaduje Python 3.11+ + pip
cd poc\pyside6
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ZeddiHubPySide6 main.py

REM PoC B (Tauri) — vyžaduje Rust + Node.js + VS Build Tools
cd poc\tauri
npm install
npm run tauri build
```

Build časy: PySide6 ~2 min, Tauri ~5–8 min (první build kompiluje všechny Rust crates; další jsou inkrementální).
