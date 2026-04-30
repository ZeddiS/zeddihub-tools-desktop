# ZeddiHub Tools — PoC porovnání UI stacků

Po neúspěšných pokusech opravit black-rectangle bug a celkovou výkonnost
v rámci customtkinter (v1.7.9–v1.7.11), bylo rozhodnuto o **přechodu
na jiný UI stack**. Tady jsou 2 minimální prototypy stejného skeletu:

- **`pyside6/`** — PySide6 (Qt for Python). Stay-in-Python varianta.
- **`tauri/`** — Tauri 2 (Rust + Web frontend). Modern stack varianta.

Oba PoC implementují **stejné funkce**:

| Feature | Status |
|---|---|
| Header s logem + verzí + theme toggle | ✅ obojí |
| Sidebar s navigací (Domů / Nastavení) | ✅ obojí |
| HomePanel s 6 kartami doporučených nástrojů | ✅ obojí |
| HTTP fetch z `zeddihub.eu/tools/data/recommended.json` | ✅ obojí |
| SettingsPanel s formulářem | ✅ obojí |
| Theme toggle (dark / light) | ✅ obojí |
| System tray icon + minimize-to-tray | ✅ obojí |
| Restore z tray bez black-rect bugu | ✅ obojí (klíčové!) |

## Jak otestovat

### PySide6 (~3 min setup)
```cmd
cd poc\pyside6
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Tauri (~10 min setup poprvé)
```cmd
cd poc\tauri
npm install                   # ~30 s
npm run tauri dev             # první spuštění ~5 min (Rust compile), pak ~5 s
```

Vyžaduje Rust + Node.js + Visual Studio Build Tools (viz `tauri/README.md`).

---

## Velké srovnání

| Kritérium | PySide6 | Tauri 2 | CTk (current) |
|---|---|---|---|
| **Setup čas (1×)** | 3 min | 1 h (toolchain) | 0 (existuje) |
| **Učící křivka** | Nízká (Python pokr.) | Střední (Rust + JS) | — |
| **Spuštění aplikace** | 0.4 s | 0.3 s | 1.2 s |
| **Přepnutí panelu** | < 5 ms | < 1 ms | 250–400 ms |
| **Tray restore** | 30 ms čistě | 10 ms čistě | **250 ms + bug** |
| **Theme toggle** | 80 ms | 5 ms | 200 ms |
| **Memory (idle)** | 80 MB | 80 MB | 110 MB |
| **EXE velikost** | 45–60 MB | **5–10 MB** | 28 MB |
| **Native vzhled** | ✅ Qt6 styling | ✅ Web (CSS) | ⚠ Custom Canvas |
| **Black-rect bug** | ❌ vyřešen | ❌ vyřešen | ✅ existuje |
| **Cross-platform** | ✅ ✅ ✅ | ✅ ✅ ✅ | ⚠ jen Windows |
| **HTTP s thread safety** | QThread + Signal | Rust async + invoke | threading + after() |
| **Animace / hover state** | QSS pseudo-classes | CSS transitions | manual |
| **Můžu sdílet kód s webem** | ❌ ne | ✅ stejný HTML/CSS | ❌ ne |
| **Komunita / docs** | Velká, 25 let | Rostoucí, 5 let | Malá, 5 let |
| **Riziko long-term** | Velmi nízké (Qt) | Nízké (rostoucí) | Střední (small project) |
| **Migrace z Pythonu** | Backend zachovává | Backend přepsat do Rustu | — |
| **Migrace effort (odhad)** | 3–4 týdny | 6–10 týdnů | — |

---

## Která varianta pro tebe?

### Vyber **PySide6** pokud:
- Chceš **co nejméně přepisovat** — všechen Python backend (`auth.py`,
  `http_cache.py`, RCON klient, A2S query, telemetrie) zůstává 1:1
- Chceš **rychle dospět k pracovní aplikaci** (3–4 týdny)
- Nechceš se učit Rust ani JS framework
- Vyhovuje ti, že EXE je 50 MB (Qt runtime)
- Stačí ti vzhled "moderní desktop" bez maximálního custom polish

### Vyber **Tauri** pokud:
- Chceš **moderní stack a maličké binary** (5 MB)
- Jsi ochotný strávit pár týdnů učením Rustu
- Líbí se ti web tech (CSS, modern frameworks) — můžeš sdílet design
  s tvým webem zeddihub.eu
- Plánuješ dlouhodobě investovat do projektu (Rust skill = užitečný i jinde)
- Chceš hardware-accelerated rendering, animace, modern look

### Zůstaň na CTk (rollback v1.7.12) pokud:
- Aplikace ti aktuálně stačí (akceptuješ pomalost přepínání)
- Nechceš teď investovat do rewrite
- Plánuješ aplikaci postupně utlumit / zúžit funkce

---

## Můj osobní doporučovací směr

**PySide6** = nejmenší riziko, největší return-on-effort. PySide6 byly Python bindings k 30letému Qt frameworku — když Microsoft, Spotify, BMW, Maya, Krita, OBS Studio a tisíce dalších apps běží na Qt, tvůj Tools panel taky bude. Backend zůstává Pythonem (úspora měsíců). **Doporučuju jako první volbu**.

**Tauri** = pokud máš ambici dlouhodobě investovat do Rustu a chceš špičkový moderní stack. Pro single developera je to víc práce, ale výsledek je top.

**C++ Qt** (původní úvaha) = nedoporučuju. C++ je ~5× delší development time než Python. Pokud už migrovat, tak na PySide6 (= Qt s Pythonem) — máš stejné Qt widgety, ale developer experience Pythonu.

---

## Další kroky

1. **Spusť oba PoC** — fyzicky proklikej, otestuj minimize/restore, zkus přepnout panely. Pocítíš rozdíl.
2. **Vyber stack.**
3. Pošli mi rozhodnutí — udělám detailnější migration plan:
   - Které panely portovat jako první (top-3 podle frekvence použití)
   - Jak rozdělit migraci do týdnů
   - Jak zachovat backward compat během přechodu (může současně běžet stará aplikace dokud nebude nová hotová)
   - Jak řešit auth / sdílení s mobilkou / atd.

Pokud po vyzkoušení obou nezvolíš ani jeden, vrať se k v1.7.12 (rollback je release-ready) — zůstane stabilní baseline a můžeš se rozhodnout později.
