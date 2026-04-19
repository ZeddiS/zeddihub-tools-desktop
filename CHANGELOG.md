# Changelog

All notable changes to ZeddiHub Tools Desktop are documented in this file.

## [2.0.2] — 2026-04-19

### Added
- **Server Updater panel** (`gui/panels/server_updater.py`) — remote monitoring of server-side updates across four layers (see `gui/update_sources/`):
  1. **Game builds** via Steam Web API (`ISteamApps/UpToDateCheck`) for Rust Dedicated, CS2 / CS:GO.
  2. **Oxide / uMod** for Rust via `umod.org/games/rust.json`.
  3. **MetaMod + SourceMod + CounterStrikeSharp** via AlliedModders drop endpoints + CSSharp GitHub Releases.
  4. **Per-plugin GitHub Releases** (`owner/repo` targets).
  Modular architecture: each source implements the same `UpdateSource` interface, so adding a new detector is one file. Status indicators (green OK / orange update-available / red error), configurable per-target current version, async background checks that never block the UI, auto-apply toggle, config persisted to `<data_dir>/server_updater.json`.
- **"Ostatní nástroje" — admin-only external-tools section** — new sidebar category visible only to users with `role=admin` in `auth.json`. Contains a **Stáhnout nástroje** (`gui/panels/tools_download.py`) hub that fetches a catalog from `zeddihub.eu/tools/data/admin_apps.json`, downloads each tool as an app module into `<data_dir>/apps/<slug>/` (auto-detects `.exe` vs `.zip`) and registers it. Installed tools appear as their own sidebar entries under "Ostatní nástroje" with one-click launch / uninstall and live sidebar refresh after install or uninstall.
- **Role-based access** (`gui/auth.py`) — login flow now reads `role` from the webhosting auth JSON and exposes `get_current_role()` / `is_admin()`. Unknown roles fall back to `"user"`. Clears on logout.
- **Windows autostart — second toggle "Spustit minimalizované do tray"** in Settings → Autostart. When enabled the `HKCU\...\Run` entry is rewritten with a `--minimized` flag, and `app.py` parses it on startup to call `withdraw()` right after creating the main window so the app lives in the tray until the user asks for it. The main autostart toggle and this one can be changed independently.
- **First-launch wizard — `%APPDATA%\ZeddiHub` as the recommended default** — the second wizard step now offers a two-button preset (AppData recommended / Documents) plus a "Custom" picker, instead of only the old `Documents` default. New helper `gui/config.get_appdata_data_dir()` resolves the path consistently.

### Changed
- **Google Apps Script integration** (`ZeddiHub App/zeddihub_sheets_github.gs`) — rewritten end-to-end: dropped the stale April-19 seed/update functions, consolidated API calls into a single `apiCall_()` helper, trimmed boilerplate, shipped a fresh `seedTasks_v2_2_0()` that populates Backlog and Bugs with the v2.0.2 roadmap (N-20 Server Updater, N-21 External Tools, N-22 Roles, N-23 Premium; F-14 Wizard default, F-15 Autostart minimized). Paste the new file into Apps Script and run the three setup steps at the top.

### Upgrade notes
- Drop-in upgrade from v2.0.1. Existing settings, credentials and data folder are preserved.
- The admin-only "Ostatní nástroje" section is invisible unless your webhosting `auth.json` user record has `"role": "admin"`. Existing users without the field default to `"user"` and see no change.
- Server Updater ships with a default target list; edit `<data_dir>/server_updater.json` to add your own plugin GitHub repos or adjust current versions.

### Verification
- `python -c "import gui.version; print(gui.version.APP_VERSION)"` → must print `2.0.2`.
- Open Settings → Autostart: toggling "Spustit minimalizované" must flip `HKCU\...\Run\ZeddiHubTools` between `"<exe>"` and `"<exe>" --minimized` (`reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- Delete `%LOCALAPPDATA%\ZeddiHub\bootstrap.json` and relaunch: wizard step 2 must preselect AppData and show three buttons (AppData / Documents / Custom).
- Log in as an admin user, open the sidebar: the "Ostatní nástroje" section must appear with "Stáhnout nástroje" inside. Non-admin users must not see the section.

## [2.0.1] — 2026-04-19

### Added
- **Single-instance lock** — application can now run only once per PC. A second launch detects the running instance (localhost socket on port 52719) and shows a warning instead of starting a duplicate.
- **YouTube Downloader standalone mode** — in frozen (.exe) builds yt-dlp is now downloaded as a standalone binary from the official GitHub releases into `%LOCALAPPDATA%\ZeddiHub\bin\yt-dlp.exe`, with a real progress indicator. Fixes the previous hang where `pip install yt-dlp` re-launched the app itself because `sys.executable` pointed to the frozen .exe.
- **Auto Clicker overhaul** — full redesign with click-position modes (cursor / fixed XY with capture hotkey), click-type selector (single / double / triple), CPS slider + entry, random jitter, click-count limit, duration limit, pre-start countdown, live click counter, separate Start/Stop hotkeys, and JSON presets. Modern card layout with a live status indicator.
- **App-wide design refresh** — deeper near-black backgrounds, richer card elevation, crisper borders, new radius tokens (`radius_card`, `radius_button`, `radius_entry`). Consistent look across home, settings, splash and the shared widget helpers.
- **Web Uploader module** (`webhosting/uploader/`) — 100 MB limit, MIME+extension whitelist, four visibility levels (public / private / shared / premium) and tiered quotas (free 100 MB / premium 5 GB / admin unlimited). Reuses admin-panel CSRF, bcrypt auth and audit log.
- **Admin panel bcrypt migration** — `password_verify_any()` transparently accepts `$2y$/$2a$/$2b$` hashes and plaintext legacy passwords, and upgrades plaintext to bcrypt on successful login. Removes the last plaintext-password surface inside `auth.json`.

### Changed
- **`assets/icon.ico` and `assets/logo_icon.png` removed** — every runtime reference now uses `assets/web_favicon.ico` directly. Build pipeline, tray, splash, main window fallback chain, PyInstaller spec and README updated; `app._generate_icon()` is now a no-op.
- **Browser login badge** (`webhosting/admin/login.php`) now uses `assets/logo2.png` instead of a text badge.
- **Admin navigation** — `users.php` consolidated into `clients.php`; flash info icon fixed from stray `i` to the correct `&#9432;`.

### Fixed
- **YouTube Downloader frozen-build bug** — root cause: `sys.executable -m pip install yt-dlp` spawned a new copy of the app because in PyInstaller `--onefile` builds `sys.executable` is the .exe itself. Fix detects `sys.frozen` and downloads the standalone binary instead.
- **Duplicate startup when clicking the exe twice** — resolved by the single-instance lock.

### Upgrade notes
- Drop-in upgrade from v2.0.0. Existing settings, credentials, bindings and datové složka are preserved.
- If you previously installed yt-dlp via pip inside a frozen build, the app will prefer the newly downloaded `%LOCALAPPDATA%\ZeddiHub\bin\yt-dlp.exe` — older pip installs remain usable when running from source.
- The second launch of the .exe will now refuse to start and point you to the system tray.

### Verification
- Double-click `dist\ZeddiHubTools.exe` twice — the second launch must show "ZeddiHub Tools je již spuštěn".
- Open PC Tools → YouTube Downloader on a machine without yt-dlp, paste a URL, click Stáhnout — a real progress indicator must advance and the file `%LOCALAPPDATA%\ZeddiHub\bin\yt-dlp.exe` must appear.
- Open PC Tools → Autoclicker — sliders, live counter and countdown must render and work.

## [2.0.0] — 2026-04-19

> **Major release.** Bumped from 1.9.0 to 2.0.0 to mark the substantial overhaul of the release tooling, the Win11 Dark Gaming desktop palette and the rebuilt admin dashboard. No breaking API changes for end users — all existing settings, data folders, credentials and bindings are preserved on upgrade.

### Added
- **Release Manager redesign (`zeddihub.bat` v2.0.0)** — completely rebuilt the release helper: ANSI-colored ASCII banner, smart pre-flight checks before each action (.env loaded, GitHub token valid, git tree clean, branch ahead/behind), a guided **Release Wizard** that walks through bump → build → commit → tag → push → release in one flow, and a **Push Preview** that summarizes commits, files and tags before any destructive action and requires an explicit `YES` to continue.
- **Build icon regeneration (F-14)** — `:build_exe` now force-copies `assets/web_favicon.ico` to `assets/icon.ico` immediately before invoking PyInstaller, so the bundled `.exe` always carries the same icon as the website. Fixes the long-standing complaint that builds shipped with the previous icon revision.
- **Unified release notes format** — every release tag from v2.0.0 onwards uses the same bilingual CZ/EN section layout (`Highlights`, `Added`, `Changed`, `Fixed`, `Upgrade notes`, `Verification`) so users can scan releases at a glance.

### Changed
- **`zeddihub.bat` menu** is now driven by named submenus (Release / Build / Git / Maintenance) instead of a 12-item flat list, with status badges colored by ANSI escape codes (`[OK]` green, `[POZOR]` yellow, `[CHYBA]` red, `[INFO]` cyan).
- **Version bump is now a wizard** — option `[1] New Release Wizard` walks the user through every required artifact (`gui/version.py`, `version.json` × 2, `webhosting/admin/_lib.php`, `CHANGELOG.md`, release notes file) with confirmation at each step.
- **`webhosting/data/version.json` and `version.json`** rewritten to advertise v2.0.0 with a Major-release-flavored changelog string.

### Fixed
- **F-14 Build .exe carrying stale icon** — root cause was that `app.py._generate_icon()` only ran at app launch, so PyInstaller bundled whatever `icon.ico` existed at build time. The build pipeline in `zeddihub.bat` now regenerates the icon up-front.
- **TD-005 (security)** — release wizard reminds the operator before every push that `webhosting/data/auth.json` and `.env` are auto-unstaged so production secrets cannot leak even on a fresh clone.

### Upgrade notes
- Drop-in upgrade from v1.9.0 (or any earlier version on the v1.x line). On first launch the favicon is re-synced and the cached version label is refreshed against the GitHub API.
- Existing release scripts that called `zeddihub.bat /5` for the old auto-release menu position should switch to the new wizard (`/W`) or rely on the menu, since menu indexes have shifted.

### Verification
- `python -c "import gui.version, gui.updater, gui.telemetry; print(gui.version.APP_VERSION)"` → must print `2.0.0`.
- `findstr /S /M "1\.9\.0" *.py *.json *.php *.bat` (run from repo root) — must list only files in `dist\`, `build\`, archived release notes (`release_notes_v1.9.0.md`) and the `[1.9.0]` heading inside this changelog.
- Build via `[2] Build .exe lokalne` and verify the resulting `dist\ZeddiHubTools.exe` carries the new favicon (right-click → Properties → file icon).

## [1.9.0] — 2026-04-19

### Added
- **E-05 Win11 Dark Gaming theme** — new default palette built around Windows 11 accent blue (`#0078D4`) and a gaming purple accent (`#6B46C1`) on a deeper background (`#0a0a0f`). Per-game primaries are preserved (CS2 gold, CS:GO blue, Rust clay), plus new `accent_soft` keys so chrome can tint towards each game subtly. Light-mode mirror palette updated as well.
- **E-05 `gui/widgets.py`** — shared widget helpers (`make_label`, `make_button`, `make_card`, `make_entry`, `make_stepper`, `make_dropdown`, `make_tabview`, `make_section_title`, `apply_sidebar_active_style`, `apply_animated_hover`). Eliminates the duplicated `_label` / `_btn` / `_entry_row` helpers that were copy-pasted across `cs2.py`, `csgo.py` and `rust.py` (TD-002).
- **E-04 Admin dashboard redesign** — `webhosting/admin/` split from one monolithic file into a proper multi-page panel: shared `_layout.php` + `_lib.php`, collapsible Win11-style sidebar, 4 KPI cards, 3 Chart.js graphs (events over time, top panels, OS distribution), and six brand-new pages (`users.php`, `news.php`, `fileshare.php`, `audit.php`, `export.php`, `maintenance.php`). Existing clients/recommended/tray/servers/version/telemetry pages moved to their own files.
- **E-04 Audit log + atomic JSON writes** — all admin writes now go through an atomic `json_write()` helper (temp file + rename), and every mutating action is appended to `webhosting/data/audit.log` via `audit_log()`. `.htaccess` denies direct access to shared `_*.php` includes.
- **E-04 Maintenance mode** — toggle `.maintenance` flag with message and a one-click cache clear for `.gh_cache.json` / `.version_cache.json`.
- **E-04 Export** — one-click ZIP of all JSON data files from `webhosting/data/`.
- **F-10 Dynamic web version** — `webhosting/index.php` now pulls the latest release tag + download URL from the GitHub API via `get_latest_release_cached()` (30-minute disk cache `.version_cache.json`) with a chain of fallbacks: cache → `webhosting/data/version.json` → static fallback constant → `—`. All download buttons and "latest version" labels share the same source.
- **F-09 Single source of truth for the app version** — new `gui/version.py` exports `APP_VERSION`, `APP_NAME`, `GITHUB_OWNER`, `GITHUB_REPO` and a `user_agent()` helper. `gui/updater.py` and `gui/telemetry.py` now import from it (with a safe fallback if the import fails). Bumping the version is finally a one-file change.
- **F-12 Shared favicon** — `app.py` now copies `assets/web_favicon.ico` to `assets/icon.ico` on every launch when present, so the desktop app and the website use the exact same icon. PNG-to-ICO generation remains as a fallback for installs that don't ship `web_favicon.ico`.

### Changed
- **F-11 "Co aplikace umí" reduced from 20 → 12 cards** — the features grid on the landing page is tighter and easier to scan. The old "NEW v1.x" ribbons are replaced by semantic CSS tag classes (`tag-cs2`, `tag-csgo`, `tag-rust`, `tag-gaming`, `tag-pctool`, `tag-server`) in orange / blue / red / green / purple / yellow respectively. Bilingual CZ/EN is preserved via `data-cs` / `data-en` attributes.
- **Updater dialog rebuilt for reliability (F-13)** — the "Update available" wizard now packs its root frame up-front and uses solid (`card_bg`) cards instead of transparent ones, which fixes a CustomTkinter bug where a race between `grab_set()` and the repaint would leave the dialog looking empty on some Windows 11 configurations. The window is slightly larger (540×460), the changelog area has a visible background, and there is a bilingual fallback message if the GitHub release body is empty.
- **Header update pill (F-13)** — when a new release is available, the version badge in the top bar is now rendered as a bright orange pill (`#fb923c`) with an up-arrow icon and an obvious pointer cursor, instead of a subtle coloured label that was easy to miss. Auto-opening of the update dialog is deferred until any first-launch Toplevels have closed so the dialog no longer appears behind the tray-notice popup.
- **Admin CSS palette** — `webhosting/admin/style.css` swapped to the same Win11 dark gaming palette as the desktop app and extended with new components (KPI grid, mini-stats, bar rows, modal overlay, collapsible sidebar rules, top-bar user menu, alert banners, code blocks).

### Fixed
- **F-13 Empty update dialog** — dialog no longer renders blank when CustomTkinter hasn't finished painting the Toplevel before widgets are added.
- **F-13 Missing update notification** — the header badge is now created with an explicit pill background and is re-styled on every `_on_update_check()` call, eliminating the case where the image failed to swap in after construction.
- **TD-002 partially retired** — panels can now call into `gui/widgets.py` instead of copy-pasting helpers (existing panels are unchanged, new code should use the shared helpers).

## [1.8.0] — 2026-04-18

### Added
- **N-02 Game Optimization** — new tab in PC Tools that toggles Windows Game Mode, Hardware-accelerated GPU Scheduling (HAGS), Game Bar, Fullscreen Optimizations, Visual Effects and the Ultimate Performance power plan in one click. Revert button restores defaults.
- **N-03 Global keyboard shortcuts** — `Ctrl+1/2/3/4` to navigate, `F5` reload panel, `Ctrl+Q` quit, `Ctrl+M` minimize to tray, `F11` fullscreen toggle, `F1` shortcuts help. Toggle + reference table in Settings → General.
- **N-06 Guides page on the website** — `webhosting/guides.php` with sticky sidebar TOC, 15 bilingual (CZ/EN) guides covering installation, CS2/CS:GO tools, Rust tools, PC tools and other features.
- **N-07 File Share** — new section in Links panel for uploading local files to `https://files.zeddihub.eu` via multipart POST; copy-share URL on success.
- **N-08 Advanced PC Tools** — auth-gated tab with registry backup (export `HKCU\Software` to a `.reg`), startup manager enumeration, running services listing, network reset helper (winsock/ip reset), and BSOD minidump history.
- **N-09 Report a bug** — Settings button that opens a pre-filled GitHub Issue with app version, OS details, active panel and reproduction template.
- **N-10 Profile editor** — display name, email and bio fields stored in `settings.profile` (Settings → Account tab).
- **N-11 Login status card** — Home panel now shows signed-in user / not signed in with inline login/logout/profile buttons, synced with the sidebar.
- **E-01 PC Tools on Home** — 3×2 quick-access grid (sys info, DNS flush, ping, speed test, temp cleaner, processes) directly from Home.
- **E-02 Blur graphical redesign** — new color palette with deeper backgrounds, `glass` card surfaces, `accent_soft`/`outline`/`text_muted` keys, softer 10 px corner radii on the header toggle buttons and all sidebar nav entries. Header child widgets now re-theme on game switch.
- **N-04 Website news carousel** — `index.php` pulls the 5 most-recent GitHub Releases (30-min server-side cache) and renders them on the landing page.

### Changed
- Primary default accent slightly richer (`#f5b623`) for stronger contrast on dark backgrounds.
- Sidebar / header separators, version label and auth label now pull colors from the theme instead of hard-coded `#666`/`#444`.
- Dark-mode card hovers use the new `card_hover` key; light mode has parallel overrides.
- `_apply_theme()` refreshes the header's version/auth/update/game-badge/toggle colors on theme change.

### Fixed
- Hard-coded `"#2a2a2a"` hover colors in the header mode-toggle and about buttons no longer override the active theme.
- Header game-badge now uses `glass` background pill instead of plain label.

## [1.7.0] — 2026-04-17
See release notes on GitHub: https://github.com/ZeddiS/zeddihub-tools-desktop/releases/tag/v1.7.0

## [1.6.x]
Older entries are kept in the GitHub Releases archive.
