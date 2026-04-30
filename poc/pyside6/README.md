# PoC A — PySide6 (Qt for Python)

Minimální skeleton ukazující, jak by ZeddiHub Tools vypadal v Qt.

## Co je v PoC

- **Header bar** s logo / verze
- **Sidebar** s 2 nav buttonami (Domů / Nastavení)
- **HomePanel** s grid 6 karet, načítaných **přes HTTP** ze stejného endpointu jako live aplikace (`https://zeddihub.eu/tools/data/recommended.json`) přes `QThread` background worker → žádný UI freeze
- **SettingsPanel** s formulářem (sekce + button + entry input) + **theme toggle** (dark/light)
- **System tray icon** (`QSystemTrayIcon`) s kontextovým menu — minimize-to-tray + restore
- Klíčové ověření: **minimize → tray → restore = žádné černé obdélníky**, žádný panel pool, žádný custom redraw walker. Qt nativně re-rendruje widgety po `hide()` + `show()`.

## Spuštění

```cmd
cd poc\pyside6

REM Vytvoření virtuálního prostředí (jednou)
python -m venv .venv
.venv\Scripts\activate

REM Instalace závislostí
pip install -r requirements.txt

REM Spuštění
python main.py
```

Mac/Linux:
```bash
cd poc/pyside6
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Build standalone EXE

```cmd
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ZeddiHubPySide6 main.py
```

Výsledný `dist\ZeddiHubPySide6.exe` má cca **45–60 MB** (Qt6 runtime).

## Klíčová pozorování při testu

| Operace | PySide6 (PoC) | CTk (current v1.7.8 baseline) |
|---|---|---|
| Spuštění | ~0.4 s do plné UI | ~1.2 s (splash + fade) |
| Přepnutí panelu | < 5 ms (QStackedWidget) | ~250–400 ms (destroy + rebuild) |
| Tray hide → restore | ~30 ms, čisté | ~250 ms + občas black-rect bug |
| Theme toggle | ~80 ms (rebuild central widget) | ~200 ms |
| HTTP fetch (background) | QThread + Signal | threading.Thread + after(0,…) hack |
| Memory | ~80 MB (Qt runtime) | ~110 MB (CTk + PIL) |

## Co se NEliší od současné aplikace

- **Backend logika beze změny** — RCON klient, A2S query, auth.py, telemetrie, soubory IO. Migrace je jen GUI vrstva.
- Stejné HTTP endpointy (zeddihub.eu/tools/data/*).
- Stejné funkce, jen jinak vykreslené.

## Co bude potřeba při skutečné migraci

1. Port všech ~25 panelů (~3-4 týdny při 4 h/den)
2. Náhrada `tkinter` widgets:
   - `CTkFrame` → `QFrame` / `QWidget`
   - `CTkButton` → `QPushButton`
   - `CTkLabel` → `QLabel`
   - `CTkEntry` → `QLineEdit`
   - `CTkScrollableFrame` → `QScrollArea` + inner `QWidget`
   - `CTkTabview` → `QTabWidget`
   - `CTkOptionMenu` → `QComboBox`
3. Náhrada `tkinter.after(ms, fn)` → `QTimer.singleShot(ms, fn)`
4. Náhrada `pystray` → `QSystemTrayIcon` (už ukázáno v PoC)
5. Theme = QSS stylesheet (CSS-like, zachovává všechny barvy)
6. Lokalizace přes Qt translation files (`.ts`/`.qm`) nebo zachovat current dict-based locale.py

## Plusy oproti CTk

- ✅ **Žádný black-rect bug** — Qt drží native render state napříč hide/show
- ✅ **Native widgety** = native vzhled na Windows (Windows 11 styling out-of-the-box)
- ✅ **Reálná multithreading** přes QThread + signals (thread-safe slot dispatch zabudovaný)
- ✅ **Mnohem víc widgetů** v Qt než v CTk — QTableView pro velká data, QSplitter, QDockWidget…
- ✅ **GPU-accelerované rendering** přes Qt Quick (volitelně)
- ✅ **Qt Designer** pro klikací GUI builder
- ✅ **Velká community** + 25 let vývoje, vše dokumentované

## Mínusy

- ⚠ Větší binary (~45-60 MB vs ~28 MB)
- ⚠ Qt licence je LGPL — pro distribuci EXE musíš dynamicky linkovat (PyInstaller `--onefile` to dělá → OK)
- ⚠ Trochu jiná idiomatika (signals/slots místo lambda callbacků) — pro Pythonistu rychle pochytitelné

## Verdict

**Pokud chceš zůstat v Pythonu**, PySide6 je jasná volba. Backend zůstává, GUI vrstva se přepíše panel po panelu, můžeš migrovat hybridně (necháš starou aplikaci v Tk a přidáváš panely v Qt zatím). Black-rect bug zmizí.
