# ZeddiHub Tools Desktop v1.9.0 — Win11 Dark Gaming + Admin Redesign

Vydáno: 19. dubna 2026

Tato verze přináší kompletně přepracovaný admin panel na webu, sjednocený grafický styl podle Windows 11, opravy aktualizačního dialogu, a centralizaci verze aplikace na jedno místo.

---

## ✨ Highlights

- **Win11 Dark Gaming theme** — nová paleta s Windows 11 modrou (`#0078D4`) a herní fialovou (`#6B46C1`), hlubší pozadí (`#0a0a0f`), zachovány per-game akcenty (CS2 zlatá, CS:GO modrá, Rust hlína).
- **Admin panel kompletně přepracován** — multi-page architektura, sklápěcí Win11 sidebar, KPI karty, Chart.js grafy, šest nových stránek (Uživatelé, Novinky, File share, Audit log, Export, Údržba).
- **Updater opraven** — prázdný dialog při kliknutí na "Aktualizovat" je pryč; nová verze se v hlavičce zobrazuje výraznou oranžovou pilulkou s šipkou.
- **Dynamická verze na webu** — landing page si verzi a download URL tahá přímo z GitHub Releases API (s 30min cache a fallbackem). Tlačítka pro stažení už nemůžou ukázat zastaralý odkaz.
- **`gui/version.py`** — single source of truth. Bumpování verze je teď úprava jednoho souboru.
- **Sdílený favicon** — `app.py` při startu kopíruje `web_favicon.ico` do `icon.ico`, takže ikona desktop aplikace a webu jsou vždy identické.

---

## 🆕 Added

- **E-05 Win11 Dark Gaming theme** — nová paleta v `gui/themes.py`. Per-game primaries zůstávají (`#f5b623`, `#3399ff`, `#cd5a3a`), přibyly `accent_soft`, `outline`, `text_muted`, `glass`, `card_hover`. Light mode aktualizován paralelně.
- **E-05 `gui/widgets.py`** — sdílené widget helpery (`make_label`, `make_button`, `make_card`, `make_entry`, `make_stepper`, `make_dropdown`, `make_tabview`, `make_section_title`, `apply_sidebar_active_style`, `apply_animated_hover`). Začátek migrace pryč od duplicitních helperů ve `cs2.py` / `csgo.py` / `rust.py`.
- **E-04 Admin panel split** — `webhosting/admin/index.php` rozdělen na `_layout.php` + `_lib.php` + per-page soubory. Sklápěcí sidebar (220 px / 64 px ikony-only) s persistencí přes cookie.
- **E-04 KPI dashboard** — 4 karty (active users, total downloads, app version, open issues) + 3 Chart.js grafy (events over time, top panels, OS distribution).
- **E-04 Nové admin stránky** — `users.php` (CRUD uživatelů s warning o plain heslech), `news.php` (CRUD novinek pro landing page), `fileshare.php` (read-only listing souborů z File Share), `audit.php` (tail audit logu), `export.php` (one-click ZIP všech JSON souborů), `maintenance.php` (toggle maintenance mode + clear cache).
- **E-04 Audit log + atomické zápisy** — všechny změny přes `json_write()` (temp + rename), každá akce zapsána do `webhosting/data/audit.log`.
- **F-10 Dynamická verze na webu** — `get_latest_release_cached()` v `index.php`, cache 30 minut v `.version_cache.json`, fallback chain: cache → `version.json` → konstanta → `—`.
- **F-09 `gui/version.py`** — jeden zdroj pravdy pro `APP_VERSION`, `APP_NAME`, `GITHUB_OWNER`, `GITHUB_REPO`, `user_agent()`. `updater.py` a `telemetry.py` importují odsud.
- **F-12 Shared favicon** — `app.py._generate_icon()` při startu kopíruje `assets/web_favicon.ico` → `assets/icon.ico`.

## 🔄 Changed

- **F-11 Web "Co aplikace umí" 20 → 12 karet** — přehlednější grid. Staré "NEW v1.x" tagy nahrazeny CSS třídami `tag-cs2`, `tag-csgo`, `tag-rust`, `tag-gaming`, `tag-pctool`, `tag-server` v odpovídajících barvách.
- **F-13 Update dialog rebuild** — root frame se packuje předem, místo `transparent` se používá `card_bg` (vyhne se race s CustomTkinter repaint), dialog větší (540×460), changelog má viditelné pozadí, fallback text pro prázdný changelog (CZ + EN).
- **F-13 Header update pill** — nová verze v top baru je oranžová pilulka (`#fb923c`) se šipkou a kurzorem, místo nenápadného textu. Auto-otevření dialogu je odloženo, dokud se nezavřou first-launch Toplevels (tray notice).
- **Admin CSS** — `webhosting/admin/style.css` aktualizován na Win11 dark gaming paletu, přidány komponenty (KPI grid, mini-stats, bar rows, modal overlay, collapsible sidebar, top-bar user menu).

## 🐛 Fixed

- **F-13** Prázdný update dialog při kliknutí na "Aktualizovat" — opraveno přebalením root frame předem.
- **F-13** Notifikace o nové verzi se občas nezobrazila — pilulka se teď restyluje při každém `_on_update_check()`.
- **TD-002** Duplicitní helper funkce v panelech — částečně vyřešeno přes nový `gui/widgets.py`.

---

## 📦 Instalace

Stáhnout `ZeddiHub.Tools.exe` (asset níže), spustit. Aplikace si při prvním spuštění vyžádá jazyk a složku pro data.

Pro existující uživatele: stačí kliknout na oranžové **v1.9.0** v top baru aplikace, dialog se postará o zbytek.

## 🔗 Odkazy

- 🌐 Web: https://zeddihub.eu/tools
- 📚 Návody: https://zeddihub.eu/tools/guides.php
- 💬 Discord: https://dsc.gg/zeddihub
- 🐛 Nahlášení bugu: https://github.com/ZeddiS/zeddihub-tools-desktop/issues/new

---

**Plný changelog:** [CHANGELOG.md](https://github.com/ZeddiS/zeddihub-tools-desktop/blob/master/CHANGELOG.md)
