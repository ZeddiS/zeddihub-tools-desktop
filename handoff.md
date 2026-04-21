# ZeddiHub Tools Desktop — Handoff pro další Claude chat

> **Datum handoffu:** 2026-04-20
> **Autor:** Claude (předchozí chat)
> **Repo:** `C:\Users\12voj\Documents\zeddihub_tools_desktop`
> **GitHub:** https://github.com/ZeddiS/zeddihub-tools-desktop
> **Aktuální verze:** v2.0.0 (lokálně commitnuto, ještě ne pushnuto)

Tento soubor obsahuje kompletní přehled všech požadavků zadaných v chatu, co je hotové a co zbývá. Vloz ho do nového Claude chatu, aby navazující Claude měl kontext.

---

## 🎯 Kontext projektu

ZeddiHub Tools Desktop = Python/CustomTkinter GUI aplikace pro Windows (CS2/CS:GO/Rust herní nástroje + PC utility). Build přes PyInstaller jako single `.exe`. Je pro Windows — **NIKDY nepoužívej Linux/WSL/bash pro operace s repem**, používej nativní Windows nástroje (cmd, PowerShell, .bat skripty, Read/Write/Edit file tools).

Dokumentace architektury: `CLAUDE.md` v rootu (teď gitignored, ale existuje lokálně).

---

## ✅ HOTOVO v tomto chatu

### A. Release v2.0.0 — bump verze napříč projektem
- `gui/version.py` → `APP_VERSION = "2.0.0"` (single source of truth)
- `version.json` (root) → 2.0.0
- `webhosting/data/version.json` → 2.0.0 (již ne trackovaný, viz sekce D)
- `webhosting/admin/_lib.php` → `APP_VERSION = '2.0.0'` (už ne trackovaný)
- `webhosting/admin/version.php` → 1.9.0→2.0.0 (už ne trackovaný)
- `webhosting/admin/news.php` seed → v2.0.0 entry (už ne trackovaný)
- `CHANGELOG.md` → přidán `[2.0.0] — 2026-04-19` oddíl (Added/Changed/Fixed/Upgrade notes/Verification)
- `release_notes_v2.0.0.md` → nový bilingvní CZ/EN soubor (Highlights/Added/Changed/Fixed/Upgrade/Verification)
- `CLAUDE.md` → aktualizován v §3.7, §5 tabulka konstant, §footer

### B. F-14: Oprava ikony v .exe buildu
Dřív build balil starou `icon.ico`, protože `app.py._generate_icon()` běžel jen za běhu aplikace, ne při buildu. Fix:
- `zeddihub.bat:build_exe` nyní **před** PyInstallerem volá `copy /Y assets\web_favicon.ico assets\icon.ico >nul`
- Identická regenerace v `:release_wizard` kroku build

### C. zeddihub.bat v2.0.0 — kompletní přepis
- ANSI barvy (bootstrap přes `echo prompt $E | cmd`)
- ASCII banner s `+===+` okraji
- 12-položkové menu rozdělené do sekcí **Release / Build / Git / Maint** s ANSI barevnými badges `[OK]`/`[POZOR]`/`[CHYBA]`/`[INFO]`
- `:preflight` reusable funkce — kontroluje `.env`, `GITHUB_TOKEN`, python, git tree clean, branch ahead/behind, origin reachable
- `:push_preview` reusable funkce — zobrazí commits/files/tags/build stav, vyžaduje explicitní `YES`
- `:release_wizard` — 7 kroků: pre-flight → bump version → CHANGELOG → build → commit → tag → push → GitHub release
- `:cleanup_secret` / `:cleanup_filter_repo` — auto-install `git-filter-repo` + regex nahrazení PAT patternu
- Keybinds rozšířené: `choice /c WSADQ123456789RTV` — T=wizard, V=preview, R=refresh
- CLI args `--wizard`/`/w` launchují wizard přímo

### D. Bezpečnostní cleanup — git tracked files
Příkaz `git rm --cached` (soubory zůstávají lokálně, jen zmizí z indexu):
- ✅ Celá složka `webhosting/` (37 souborů včetně `auth.json` s plaintext hesly)
- ✅ Složka `ZeddiHub App/` (Google Apps Script, 39 KB)
- ✅ Obsoletní release skripty: `release_1_8_0.bat`, `release_1_8_0.ps1`, `release_1_8_0_manual.cmd`
- ✅ Zastaralé soubory: `RELEASE_NOTES_v1.7.0.md`, `backlog_export_v1.7.0.csv`, `ZeddiHub.Tools.spec` (starý spec)
- ✅ `.gitignore` updated — přidány patterny pro všechno výše + `CLAUDE.md`, `release_notes_v*.md`, `security_cleanup.bat`

### E. Lokální commity (připravené, zatím NE pushnuté)
```
b62f039  Release v2.0.0
22fbdb8  chore(security): move webhosting/ and internal files out of repo
7295d82  Release v1.9.0 (předchozí remote HEAD)
```

GitHub po budoucím push bude mít **51 souborů** (jen desktop app source + `.github/workflows/release.yml`). Seznam:
```
.env.example, .github/assets/*, .github/workflows/release.yml,
.gitignore, CHANGELOG.md, README.md, ZeddiHubTools.spec, app.py,
assets/fonts/*, assets/icon.ico, assets/logo*.png,
gui/* (auth.py, config.py, icons.py, locale.py, main_window.py,
splash.py, telemetry.py, themes.py, tray.py, updater.py, version.py,
widgets.py, panels/{about,cs2,csgo,game_tools,home,keybind,links,
pc_tools,rust,settings,translator,watchdog}.py),
locale/{cs,en}.json, main.py, requirements.txt, version.json,
zeddihub.bat
```

### F. Windows-nativní cleanup skript
`security_cleanup.bat` v rootu repa — 6 kroků:
1. Smaže zbytkové `.git/*.lock*` (po mých neúspěšných pokusech z Linux sandboxu)
2. Smaže `.git-rewrite/` (leftover po filter-branch)
3. `git fsck` integrity check
4. Auto-install `git-filter-repo` + rewrite historie (regex na PAT patterny)
5. Smaže `build/`, `dist/`, `__pycache__/` (uvolní ~84 MB)
6. Načte token z `.env` + force push na GitHub

---

## ❌ NEHOTOVO — zbývá udělat

### 1. 🔴 KRITICKÉ: Revokovat leaknutý PAT token
- **Lokace:** V git historii, commity `c6b9fbb` a `594f0a8` (oba release v1.7.0)
- **V souboru:** `.gitignore` (někdo omylem vložil hodnotu tokenu jako ignore pattern)
- **Token:** `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`
- **Akce:** https://github.com/settings/tokens → Delete → vygenerovat nový → vložit do `.env`

### 2. 🔴 Spustit `security_cleanup.bat`
Po revokaci PATu spustit z Windows CMD v `C:\Users\12voj\Documents\zeddihub_tools_desktop`:
```cmd
security_cleanup.bat
```
Skript se zeptá před každou destruktivní akcí (A/N). Provede:
- Cleanup `.git/*.lock*` a `.git-rewrite/`
- Rewrite historie (PAT → `***REDACTED_PAT***`)
- Smazání `build/`, `dist/`, `__pycache__/`
- Force push na GitHub

### 3. 🟡 Finální release v2.0.0 na GitHub
Po force pushi — vytvořit git tag `v2.0.0` + GitHub release s `ZeddiHubTools.exe`:
- Buď přes `zeddihub.bat` → možnost `[5] Auto Release` nebo `[1] New Release Wizard`
- Nebo manuálně: `git tag v2.0.0`, `git push origin v2.0.0` → GitHub Actions zbuilduje a vypublikuje

### 4. 🟡 Legacy úkoly z předchozích sezení
- **Task #20:** Verify release v1.7.0 na GitHubu vytvořen (check že `.exe` asset je tam)
- **Task #47:** Aktualizovat Google Sheets — 11 položek TODO → COMPLETED

### 5. 🟡 Nedokončené technické dluhy (nepovinné)
- **TD-002:** Existující panely (`cs2.py`, `csgo.py`, `rust.py`) stále duplikují helper funkce. `gui/widgets.py` existuje, ale panely ještě nemigrovány. Refactoring zatím odložen.
- **TD-003:** `gui/main_window.py` — nesjednocený import `from . import telemetry as _telem`
- **TD-006:** `RustPlayerPanel._build_plugin_info/analyzer` jsou mrtvý kód
- **TD-007:** `game_tools` / `translator` nav_id duplicitní routing v `_show_panel()`
- **TD-008:** `csgo.py` je kopie `cs2.py` — refactoring na společnou base třídu

---

## ⚠️ Důležité varování pro dalšího Claude

### Nikdy nepoužívej Linux/bash pro git operace na tomto repu
Repo je na Windows disku. Bash sandbox má jen **read-only** práva — každá git operace, která modifikuje `.git/` (commit, filter-branch, atd.) selže na permission errors a nechá tam `.lock` soubory. Tím jsem rozbil `.git/` v minulém sezení a musel jsem vytvořit `security_cleanup.bat` na opravu. Vždy:
- **Čti soubory:** `Read` tool (funguje s Windows cestami)
- **Modifikuj soubory:** `Write` / `Edit` tool (funguje s Windows cestami)
- **Git operace:** Napsat `.bat` skript → uživatel spustí z Windows CMD
- **Příkazy na disku:** Napsat `.bat` skript → uživatel spustí

### Git je zatím v nečistém stavu po mých pokusech
`.git/` obsahuje zbytky po failed filter-branch z Linux sandboxu:
- `.git/index.broken`, `.git/index.lock.old*`, `.git/HEAD.lock.old`
- `.git-rewrite/` složka
- `.git/objects/**/tmp_obj_*`

**`security_cleanup.bat` krok [1] a [2] tohle všechno uklidí.** Dokud to uživatel nespustí, pracuj opatrně — některé git příkazy mohou selhat kvůli lock souborům.

### User preferences zjištěné v chatu
- Jazyk: CZ (čeština), s občasnými bilingvními prvky (CZ/EN v release notes)
- Rozumí technickým věcem, umí spustit `.bat`, má GitHub PAT
- Chce jen app source na GitHubu (ŽÁDNÝ webhosting, ŽÁDNÉ interní docs)
- Používá Windows 11, CustomTkinter aplikaci běžně buildí přes `zeddihub.bat`

---

## 📁 Soubory vytvořené v tomto chatu

| Soubor | Účel | Stav |
|---|---|---|
| `zeddihub.bat` (přepsán) | v2.0.0 Release Manager s ANSI + wizard | ✅ commitnuto v `b62f039` |
| `release_notes_v2.0.0.md` | Bilingvní release notes | ✅ commitnuto v `b62f039` |
| `CHANGELOG.md` (edit) | Přidán `[2.0.0]` oddíl | ✅ commitnuto v `b62f039` |
| `.gitignore` (edit) | Webhosting, interní soubory | ✅ commitnuto v `22fbdb8` |
| `security_cleanup.bat` | Windows-native security fix | ✅ v rootu, ne-trackovaný (gitignore) |
| `handoff.md` (tento soubor) | Shrnutí pro další Claude chat | ✅ v rootu, ne-trackovaný |

---

## 🔑 Klíčové konstanty a URL

- `APP_VERSION` v `gui/version.py` = `"2.0.0"` (single source)
- `GITHUB_OWNER` = `ZeddiS`
- `GITHUB_REPO` = `zeddihub-tools-desktop`
- Remote: `https://github.com/ZeddiS/zeddihub-tools-desktop.git`
- Branch: `master`
- Leaked PAT (REVOKOVAT!): `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`

---

**Konec handoffu.** Dalšímu Claude: přečti `CLAUDE.md` pro hlubší technický kontext projektu, pak `handoff.md` (tento soubor) pro aktuální stav.
