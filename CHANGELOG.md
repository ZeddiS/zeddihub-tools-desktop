# Changelog

All notable changes to ZeddiHub Tools Desktop are documented in this file.

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
