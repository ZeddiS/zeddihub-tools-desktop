# ZeddiHub Tools Desktop – v1.7.0

**Release date:** 2026-04-18

Velký release přinášející detekci z Windows Registry, autostart, redesignované home se statistikami GitHubu, nový panel "O aplikaci" a celou řadu oprav.

---

## Novinky

### Nové funkce
- **N-12 — Panel "O aplikaci":** nový samostatný panel s verzí, použitými technologiemi, autorem, odkazy a licencí. V záhlaví přibylo tlačítko ⓘ pro rychlý přístup.
- **N-13 — Novinky z GitHub Releases:** Home panel nyní načítá posledních 5 releases přímo z GitHub API a zobrazuje je v přehledné kartě.
- **N-05 — GitHub Checker:** 4 statistické karty (Issues, Stars, Forks, Downloads) s live daty z GitHub API.
- **N-14 — Windows sensitivity detection:** v Sensitivity Converteru tlačítko "Načíst z Windows" čte `HKCU\Control Panel\Mouse\MouseSensitivity` a automaticky vyplní citlivost.
- **N-15 — Spustit při startu Windows:** v Nastavení switch, který zapisuje/maže klíč `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\ZeddiHubTools`.
- **F-07 — Volba chování tlačítka Zavřít:** radio buttony "Minimalizovat do tray" / "Ukončit aplikaci" + tray notifikace při minimalizaci.
- **F-08 — Keybind Generator numpad:** přidána celá numerická klávesnice (Num0–9, /, *, +, -, NumLock, NumEnter, KP_DEL).
- **YouTube Downloader:** on-demand instalace yt-dlp po potvrzení uživatele, progress indikátor.
- **Autoclicker:** globální hotkey (funguje i při minimalizované aplikaci) přes pynput + pyautogui.
- **Sticky Notes:** perzistentní napříč restartem + volitelný self-destruct timer.

### Opravy (Bug fixes)
- **Fix `.pack(width=…)` SyntaxError** na několika místech (AuthDialog, `_show_tray_notice`, sticky notes dialog) — width přesunut do konstruktoru tlačítka.
- **Fix Sticky Notes persistence:** zavření plovoucího okna poznámky již nesmaže poznámku ze storage.
- **Fix `_LogoutDialog`:** doplněna chybějící část (tlačítka potvrdit / zrušit).
- **Fix SyntaxError v settings.py:** pozitional argument po keyword argumentu v `_label()`.

### Technické změny
- `CURRENT_VERSION` sesynchronizována napříč `updater.py`, `telemetry.py`, `version.json`.
- Přidány do `requirements.txt`: `pyautogui>=0.9.54`, `pynput>=1.7.6`.
- Nové locale klíče (cs/en) pro About panel, autostart, close behavior, Windows sensitivity, GitHub checker, news.

---

## Instalace / upgrade
Aplikace má vestavěný auto-updater — po spuštění vás upozorní na novou verzi. Alternativně stáhněte **ZeddiHubTools.exe** níže a přepište starou kopii.

## Checksums
> SHA-256 checksum přidá build pipeline automaticky při nahrání binárky.

---
**Plný changelog:** viz soubor `version.json` v repozitáři.
