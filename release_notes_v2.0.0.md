# ZeddiHub Tools Desktop v2.0.0 — Release Manager 2.0 + Win11 Dark Gaming

**Vydáno / Released: 19. dubna 2026 / April 19, 2026**

> CZ: Major release. Skok z 1.9.0 na 2.0.0 značí kompletní přepis release nástroje, sjednocení vizuálního stylu Win11 a nový admin panel. Žádné breaking changes pro uživatele aplikace — všechna nastavení, data, přihlášení a bindy se zachovají.
>
> EN: Major release. The jump from 1.9.0 to 2.0.0 marks the full rewrite of the release tooling, the unified Win11 visual style and the new admin panel. No breaking changes for end users — all settings, data, credentials and bindings are preserved.

---

## ✨ Highlights

- **Release Manager 2.0** (`zeddihub.bat`) — barevný ASCII banner, pre-flight kontroly, **wizard mód** pro nový release a **push preview** před každou destruktivní akcí. / Colorized ASCII banner, pre-flight checks, a guided **release wizard** and a **push preview** before every destructive action.
- **Build .exe ikona opravena (F-14)** — `web_favicon.ico` se kopíruje do `icon.ico` *před* PyInstallerem, takže build nese vždy aktuální ikonu. / Build always carries the latest favicon.
- **Win11 Dark Gaming theme** — paleta s Windows 11 modrou (`#0078D4`) a herní fialovou (`#6B46C1`), hlubší pozadí (`#0a0a0f`), per-game akcenty zachovány. / Win11 blue + gaming purple, deeper backgrounds, per-game accents preserved.
- **Admin panel kompletně přepracován** — multi-page architektura, Win11 sidebar, KPI dashboard s Chart.js grafy, šest nových stránek. / Multi-page architecture, KPI dashboard with Chart.js, six brand-new pages.
- **Updater opraven** — prázdný dialog je pryč, nová verze v hlavičce svítí oranžovou pilulkou. / Empty dialog fixed; new version pulses as an orange pill in the header.
- **`gui/version.py`** — single source of truth. Bumpování verze je úprava jednoho souboru. / Version bump is now a one-file change.
- **Sdílený favicon** — desktop aplikace a web mají vždy identickou ikonu. / Desktop app and website always share the same favicon.
- **Sjednocený formát release notes** — bilingvní CZ/EN, konzistentní sekce, snadné porovnání mezi verzemi. / Bilingual CZ/EN, consistent sections, easy diffing across releases.

---

## 🆕 Added

- **Release Wizard v zeddihub.bat** — krokový průvodce: bump version → CHANGELOG → build → commit → tag → push → release v jednom flow s potvrzením v každém kroku. / Step-by-step wizard from version bump to GitHub release with confirmations.
- **Pre-flight checks** — `.env` načteno, `GITHUB_TOKEN` validní, čistý git tree, branch ahead/behind status, lokální vs. remote tag. Spouští se automaticky před každou release/push akcí. / Auto-runs before every release/push action.
- **Push Preview** — souhrn commits, změněných souborů, tagů a build stavu PŘED pushem; vyžaduje explicitní `YES`. / Summary of commits, files, tags, build state before push; requires explicit `YES`.
- **ANSI barvy a ASCII banner v menu** — `[OK]` zelené, `[POZOR]` žluté, `[CHYBA]` červené, `[INFO]` cyan; barevný banner při startu. / Color-coded badges and a colored ASCII banner.
- **Build icon regeneration (F-14)** — `:build_exe` před PyInstallerem volá `copy /Y assets\web_favicon.ico assets\icon.ico` aby `.spec` zabalil aktuální ikonu. / Build copies fresh favicon into icon.ico before PyInstaller.
- **E-05 Win11 Dark Gaming theme** — `gui/themes.py` paleta s `accent_soft`, `outline`, `text_muted`, `glass`, `card_hover`, light mode aktualizován paralelně.
- **E-05 `gui/widgets.py`** — sdílené helpery (`make_label`, `make_button`, `make_card`, `make_entry`, `make_stepper`, `make_dropdown`, `make_tabview`, `make_section_title`, `apply_sidebar_active_style`, `apply_animated_hover`).
- **E-04 Admin panel split** — `webhosting/admin/index.php` rozdělen na `_layout.php` + `_lib.php` + per-page soubory; sklápěcí sidebar (220 px / 64 px ikony-only) s persistencí přes cookie.
- **E-04 KPI dashboard** — 4 karty (active users, total downloads, app version, open issues) + 3 Chart.js grafy (events over time, top panels, OS distribution).
- **E-04 Nové admin stránky** — `users.php`, `news.php`, `fileshare.php`, `audit.php`, `export.php`, `maintenance.php`.
- **E-04 Audit log + atomické zápisy** — všechny změny přes `json_write()` (temp + rename), každá akce do `webhosting/data/audit.log`.
- **F-10 Dynamická verze na webu** — `get_latest_release_cached()`, cache 30 minut, fallback chain: cache → `version.json` → konstanta → `—`.
- **F-09 `gui/version.py`** — `APP_VERSION`, `APP_NAME`, `GITHUB_OWNER`, `GITHUB_REPO`, `user_agent()`. `updater.py`, `telemetry.py`, `links.py` importují odsud.
- **F-12 Shared favicon** — `app.py._generate_icon()` při startu kopíruje `assets/web_favicon.ico` → `assets/icon.ico`.

## 🔄 Changed

- **`zeddihub.bat` menu** — položky uspořádány do sekcí (Release / Build / Git / Maintenance) s named labels a stavovými badges. / Menu organized into sections with status badges.
- **Version bump je teď wizard** — průvodce automaticky aktualizuje `gui/version.py`, oba `version.json`, `_lib.php`, `CHANGELOG.md` a vytvoří nový `release_notes_vX.Y.Z.md`.
- **F-11 Web "Co aplikace umí" 20 → 12 karet** — přehlednější grid; staré "NEW v1.x" tagy nahrazeny CSS třídami (`tag-cs2`, `tag-csgo`, `tag-rust`, `tag-gaming`, `tag-pctool`, `tag-server`).
- **F-13 Update dialog rebuild** — root frame packován předem, `card_bg` místo `transparent`, dialog 540×460, changelog s viditelným pozadím, bilingvní fallback text pro prázdný changelog.
- **F-13 Header update pill** — oranžová pilulka (`#fb923c`) se šipkou a kurzorem, auto-otevření odloženo dokud se nezavřou first-launch Toplevels (tray notice).
- **Admin CSS** — Win11 dark gaming paleta v `webhosting/admin/style.css`, nové komponenty (KPI grid, mini-stats, bar rows, modal overlay, collapsible sidebar).

## 🐛 Fixed

- **F-14 Build .exe nesl starou ikonu** — `app.py._generate_icon()` běžel jen za běhu aplikace, takže PyInstaller balil `icon.ico` ze starého buildu. Build pipeline teď ikonu regeneruje sama. / Build now regenerates the icon up-front.
- **F-13 Empty update dialog** — při kliknutí na "Aktualizovat" se dialog už neobjeví prázdný.
- **F-13 Missing update notification** — pilulka v hlavičce se restyluje při každém `_on_update_check()`.
- **TD-002 (částečně)** — duplicitní helper funkce v panelech mají teď sdílenou alternativu v `gui/widgets.py`.

---

## ⬆️ Upgrade notes

- **CZ:** Drop-in upgrade z v1.9.0 nebo libovolné starší verze v1.x. Při prvním spuštění se favicon re-syncuje a verze v cache se obnoví proti GitHub API. Žádná migrace dat.
- **EN:** Drop-in upgrade from v1.9.0 or any earlier v1.x version. On first launch the favicon is re-synced and the cached version label refreshes against the GitHub API. No data migration.
- Pokud máš vlastní skripty volající `zeddihub.bat /5` pro starou auto-release pozici, přepni na nový wizard (`/W` nebo menu položka **[1] New Release Wizard**) — menu indexy se posunuly. / If you had scripts calling `zeddihub.bat /5`, switch to the new wizard.

## ✅ Verification

```cmd
python -c "import gui.version, gui.updater, gui.telemetry; print(gui.version.APP_VERSION)"
:: → 2.0.0

findstr /S /M "1\.9\.0" *.py *.json *.php *.bat
:: → only files in dist\, build\, release_notes_v1.9.0.md, [1.9.0] heading in CHANGELOG.md
```

Build via `[2] Build .exe lokalne` and verify `dist\ZeddiHubTools.exe` carries the new favicon (right-click → Properties).

---

## 📦 Instalace / Installation

**CZ:** Stáhnout `ZeddiHub.Tools.exe` (asset níže) a spustit. Aplikace si při prvním spuštění vyžádá jazyk a složku pro data.

**EN:** Download `ZeddiHub.Tools.exe` (asset below) and run. On first launch the app prompts for language and data folder.

Pro existující uživatele / For existing users: stačí kliknout na oranžové **v2.0.0** v top baru aplikace, dialog se postará o zbytek. / Just click the orange **v2.0.0** pill in the app top bar.

## 🔗 Odkazy / Links

- 🌐 Web: https://zeddihub.eu/tools
- 📚 Návody / Guides: https://zeddihub.eu/tools/guides.php
- 💬 Discord: https://dsc.gg/zeddihub
- 🐛 Bug report: https://github.com/ZeddiS/zeddihub-tools-desktop/issues/new

---

**Plný changelog / Full changelog:** [CHANGELOG.md](https://github.com/ZeddiS/zeddihub-tools-desktop/blob/master/CHANGELOG.md)

**Předchozí verze / Previous release:** [v1.9.0](https://github.com/ZeddiS/zeddihub-tools-desktop/releases/tag/v1.9.0)
