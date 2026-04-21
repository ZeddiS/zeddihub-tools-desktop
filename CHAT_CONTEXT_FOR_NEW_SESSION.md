# ZeddiHub Tools Desktop — Kontext pro nový Claude chat

> Tento soubor shrnuje vše, co bylo zadáno v předchozím chatu, co bylo splněno a co zbývá.
> Použij ho jako vstup do nového Claude chatu.

---

## PRAVIDLA PRO CLAUDE (povinné dodržovat vždy)

1. **Komunikuj pouze česky.**
2. **Editace souborů výhradně metodou FIND/REPLACE** — nikdy neposílej celý přepsaný soubor.
3. **Nikdy nemaž ani nezkracuj existující kód** — pouze přidávej nebo upravuj cíleně.
4. **Před každou změnou ověř konvence v CLAUDE.md** (je součástí projektu v `C:\Users\12voj\Documents\zeddihub_tools_desktop\CLAUDE.md`).
5. **Po dokončení každého úkolu napiš krátký report do listu "Backlog"** v Google tabulce ID: `1F-2BaU35QaBCHLInj5AUgTt_p2w1Nd10hpHicEnWgPE`.
6. **Doplňující dotazy** ke každému úkolu jsou zodpovězeny v listu "Dotazy" téže tabulky — přečti je před začátkem práce.

---

## PROJEKT — Základní info

- **Název:** ZeddiHub Tools Desktop
- **Jazyk:** Python 3.10+
- **GUI:** CustomTkinter (CTk)
- **Složka projektu:** `C:\Users\12voj\Documents\zeddihub_tools_desktop\`
- **Dokumentace architektury:** `CLAUDE.md` v kořeni projektu
- **Google Sheets backlog:** `https://docs.google.com/spreadsheets/d/1F-2BaU35QaBCHLInj5AUgTt_p2w1Nd10hpHicEnWgPE/edit`
- **Aktuální verze:** v2.1.0

### Klíčové konvence (shrnutí z CLAUDE.md)
- Panely dědí z `ctk.CTkFrame`, `__init__(self, parent, theme: dict, nav_callback=None, **kwargs)`
- UI aktualizace z vláken vždy přes `self.after(0, callback, args)` — thread safety
- `subprocess` vždy s `creationflags=0x08000000` (CREATE_NO_WINDOW) na Windows
- Lokalizace: `from ..locale import t` → `t("klic")`
- Feature flags: `PSUTIL_OK`, `PYAUTOGUI_OK`, `PYNPUT_OK` — graceful degradation
- Grid a Pack nesmí být míchány v jednom Frame

---

## CO BYLO SPLNĚNO V PŘEDCHOZÍM CHATU

### ✅ N-01 — PC Tools: Autoclicker, Sticky Notes, YouTube Downloader

**Soubor:** `gui/panels/pc_tools.py`

Implementovány 3 nové záložky v `PCToolsPanel` pomocí FIND/REPLACE editací:

#### 🖱 Autoclicker (záložka "🖱 Autoclicker")
- CPS (clicks per second) entry s validací
- Výběr tlačítka myši (Left / Right / Middle)
- Nastavitelný hotkey pro start/stop (default F8)
- Globální pynput listener — funguje i při minimalizaci do tray
- `threading.Event` stop signal pro čisté zastavení
- `pyautogui` pro simulaci klikání (`FAILSAFE=True`)
- Pokud `pyautogui` není nainstalován: tlačítko "Nainstalovat pyautogui" (pip install)
- Feature flag `PYAUTOGUI_OK` + `PYNPUT_OK`

#### ▶ YouTube DL (záložka "▶ YouTube DL")
- URL entry + výběr kvality (best / 1080p / 720p / 480p / 360p / audio only mp3)
- Browse tlačítko pro výběr výstupní složky
- Při prvním použití: messagebox.askyesno dotaz na instalaci yt-dlp
- Po potvrzení: pip install yt-dlp na pozadí, pak spustí stahování
- Progress bar parsovaný z stdout (`%` hodnoty z yt-dlp výstupu)
- Log textbox s výstupem stahování
- Nástroj je neaktivní dokud není yt-dlp nainstalován

#### 📝 Sticky Notes (záložka "📝 Sticky Notes")
- Perzistentní poznámky uložené v JSON (`get_data_dir()/sticky_notes.json`)
- Plovoucí CTkToplevel okna s barevným akcentem
- 6 barev na výběr při vytváření
- Při startu aplikace se automaticky otevřou uložené poznámky (`self.after(600, ...)`)
- Volitelný časovač auto-smazání (0 = nikdy; jinak počet minut)
- Obsah se ukládá okamžitě při psaní (`<KeyRelease>`)
- Ochrana proti duplicitním oknům (`_note_id` atribut)

**Přidané feature flagy do souboru:**
```python
try:
    import pyautogui
    PYAUTOGUI_OK = True
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.0
except ImportError:
    PYAUTOGUI_OK = False

try:
    from pynput import keyboard as _pynput_keyboard
    PYNPUT_OK = True
except ImportError:
    PYNPUT_OK = False
    _pynput_keyboard = None
```

**Nové metody přidané do PCToolsPanel:**
- `_build_autoclicker(tab)`
- `_install_pyautogui()`
- `_ac_setup_hotkey()`
- `_toggle_autoclicker()`
- `_start_autoclicker()`
- `_stop_autoclicker()`
- `_build_ytdl(tab)`
- `_ytdl_browse()`
- `_ytdl_check_installed()`
- `_ytdl_start()`
- `_ytdl_run(url)`
- `_get_notes_file()`
- `_load_notes_from_file()`
- `_open_persistent_notes()`
- `_save_notes()`
- `_build_stickynotes(tab)`
- `_refresh_notes_list()`
- `_delete_note(note)`
- `_new_note()`
- `_open_note_window(note)`

**Stav v Google Sheets:** Stále evidován jako TODO — report do Backlogu nebyl zapsán (kontext chatu se přerušil).

---

## CO NEBYLO SPLNĚNO (zbývající úkoly z Backlogu)

### Nové funkce (NEW)

| ID | Název | Složitost | Poznámky |
|---|---|---|---|
| **N-02** | Game Optimization: Game Mode, Windows funkce | Střední | Nový soubor `game_optimization.py` + úprava `main_window.py`. Registry přes `winreg`. |
| **N-03** | Klávesové zkratky: Nastavení | Střední | pynput/keyboard lib, globální hotkeys i v tray. Soubor: `settings.py`. |
| **N-04** | Web Aktualizace (Novinky) | Nízká | Nová sekce na `webhosting/index.php`. Pouze webové soubory. |
| **N-05** | GitHub Checker | Nízká | `home.py` nebo nový panel. Kontroluje Issues, PR, Downloads, shodu README s verzemi, synchronizace novinek z Releases. |
| **N-06** | Guides: na webu | Nízká | Nový soubor `webhosting/guides.php`. |
| **N-07** | File Share | TBD | Upload přes web zeddihub.eu přímo z aplikace, stahování z webu. |
| **N-08** | Advanced PC Tools (Auth Required) | Střední | Registry tweaky pro Windows optimalizaci. UAC elevace pouze při spuštění konkrétní funkce (subprocess runas). Dotaz 6: Claude má vyhledat vhodné tweaky. |
| **N-09** | Report a bug: GitHub Issue z aplikace | Střední | GitHub Issues API, sdílený token (hardcoded — security risk akceptován). |
| **N-10** | Úprava profilu (foto, email, heslo, O mně) | Vysoká | Nový PHP endpoint `profile_api.php`. Foto na server, standardní formát/velikost. Přístup k webu existuje. |
| **N-11** | Login na Hlavní Panel: sync stavu přihlášení | Střední | Login UI na HomePanel, synchronizace s headerem + SettingsPanel. |
| **N-12** | O aplikaci: panel + tlačítko "i" | Nízká | Nový soubor `gui/panels/about.py` + úprava `main_window.py`. |
| **N-13** | Novinky: GitHub Releases v aplikaci | Nízká | `home.py` nebo nový panel. GitHub Releases API. |
| **N-14** | Windows sensitivity detection | Nízká | `game_tools.py`. winreg čtení z `HKCU\Control Panel\Mouse\MouseSensitivity`. |
| **N-15** | Spustit při startu počítače | Nízká | `settings.py`. winreg zápis do `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. |

### Editace (EDIT)

| ID | Název | Složitost | Poznámky |
|---|---|---|---|
| **E-01** | PC Tools: Hlavní panel | Střední | Chce aby na hlavní záložce PC Tools byl přehled PC nástrojů, ne server/hráčské nástroje. |
| **E-02** | Grafický redesign (Blur-AutoClicker styl) | Vysoká | Kompletně vlastní rámeček a styl aplikace (zaoblené rohy, průhledné okraje, acrylic efekt). Zasahuje `themes.py` + všechny panely. |
| **E-03** | Vlastní rámeček okna | Vysoká | Kompletně vlastní titlebar (overrideredirect), spolu s E-02. |

### Bugy (FIX)

| ID | Název | Závažnost | Poznámky |
|---|---|---|---|
| **F-03** | Web vlajky | Nízká | Problém s vlajkami na `webhosting/index.php`. |
| **F-04** | Web "Hotovo za 3 kroky" (ale jsou 4) | Nízká | Text říká 3 kroky, ale kroků je 5. `webhosting/index.php`. |
| **F-05** | Web stažení: chybí název souboru | Nízká | `webhosting/index.php`. |
| **F-06** | Web "Co aplikace umí": nový obsah | Střední | Aktualizace obsahu sekce. `webhosting/index.php`. |
| **F-07** | Zpráva o minimalizování aplikace | Nízká | Windows upozornění se nezobrazuje. Přidat možnost vypnout aplikaci zavřením do nastavení. `tray.py` nebo `main_window.py`. |
| **F-08** | Keybind Generator: chybí numpad + klávesy | Střední | Chybí numpad v Canvas layoutu. `gui/panels/keybind.py`. |

---

## ZODPOVĚZENÉ DOTAZY (z listu "Dotazy")

| Úkol | Dotaz | Odpověď |
|---|---|---|
| N-01 | yt-dlp bundlovat nebo stáhnout za běhu? | Stáhnout externě po dotázání uživatele; nástroj neaktivní do té doby |
| N-01 | Autoclicker globálně nebo jen v popředí? | Vždy (globálně, i při minimalizaci) |
| N-01 | Sticky Notes persistentní + časovač? | Ano, přežijí restart + volitelný časovač auto-smazání |
| E-02 + E-03 | Jen titlebar nebo celý vlastní tvar okna? | Kompletně vlastní okraj (zaoblené, průhledné, acrylic efekt) |
| E-01 | Co přesně změnit na PC Tools hlavním panelu? | Chce tam PC nástroje, ne server/hráčské |
| N-08 | Co jsou "Advanced regedit improvements"? | Claude má vyhledat vhodné Windows tweaky |
| N-08 | UAC elevace při startu nebo per-funkce? | Pouze při spuštění dané funkce (subprocess runas) |
| N-10 | Přístup k PHP backendu? | Ano, má přístup k webu a může nahrát soubory |
| N-10 | Profilový obrázek — server nebo lokálně? | Na server, standardní formát/velikost dle normy |
| N-09 | GitHub token — sdílený nebo OAuth? | Sdílený token |
| N-05 | Co má GitHub Checker kontrolovat? | Issues, PR, Downloads + shoda README s verzemi + sync novinek z Releases |
| N-07 | File Share — odkaz nebo nová funkce? | Upload přes web zeddihub.eu přímo z aplikace |
| F-07 | Co je špatně se zprávou o minimalizaci? | Nezobrazuje se; přidat možnost vypnout app zavřením (v nastavení) |

---

## NEDOKONČENÉ AKCE Z PŘEDCHOZÍHO CHATU

- [ ] Zapsat report o dokončení N-01 do listu "Backlog" v Google tabulce
- [ ] Aktualizovat stav N-01 v Backlogu z TODO na COMPLETED

---

## DOPORUČENÉ POŘADÍ DALŠÍCH ÚKOLŮ

Dle závislostí a komplexity navrhuju:

1. **F-07** — Zpráva o minimalizaci (jednoduchý fix, `tray.py`/`main_window.py`)
2. **N-15** — Spustit při startu (jednoduchý, `settings.py` + winreg)
3. **N-14** — Windows sensitivity detection (jednoduchý, `game_tools.py` + winreg)
4. **N-12** — O aplikaci panel (statický, nový soubor)
5. **N-13** — Novinky z GitHub Releases (rozšíření existující logiky)
6. **N-03** — Klávesové zkratky v nastavení
7. **N-02** — Game Optimization
8. **N-08** — Advanced PC Tools (registry tweaky)
9. **N-11** — Login na Home panelu
10. **N-05** — GitHub Checker
11. **N-09** — Report a bug
12. **N-04, N-06** — Webové aktualizace
13. **N-10** — Úprava profilu (nejvíce komplexní)
14. **N-07** — File Share
15. **E-01** — PC Tools panel redesign
16. **E-02 + E-03** — Kompletní grafický redesign (nejvyšší komplexita)
