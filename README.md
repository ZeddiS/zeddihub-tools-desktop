# ZeddiHub Tools

Sada konzolových TUI nástrojů pro správu herních serverů a konfigurací. Podpora Rust, CS:GO, CS2, hromadného překladu a real-time monitoringu serverů.

**Jazyk rozhraní:** Čeština / English

## Moduly

| Modul | Popis |
|---|---|
| **Rust Editor** | Opravy, kompilace a analýza Oxide/uMod pluginů, editor databází, RCON klient, dependency checker |
| **CS:GO Tools** | Crosshair generátor, viewmodel generátor, autoexec/practice config, buy bindy, server.cfg, editor .cfg |
| **CS2 Tools** | Crosshair generátor, viewmodel s ASCII náhledem, autoexec s vlastními příkazy, server.cfg, RCON klient |
| **Translator** | Hromadný překlad souborů (JSON/TXT/LANG), prefix manager, statistiky, batch export (TXT/JSON/CSV) |
| **Server Status** | Real-time monitoring herních serverů (A2S_INFO protokol), dashboard, quick query, auto-refresh |

## Požadavky

- **Windows 10/11**
- **Python 3.10+** (bez externích závislostí)

## Instalace

```bash
git clone https://github.com/ZeddiS/zeddihub-tools.git
cd zeddihub-tools
```

## Spuštění

Dvojklik na `ZeddiHub Tools Launcher.bat` nebo:

```bash
python launcher.py
```

Při prvním spuštění každého modulu se zobrazí průvodce nastavením.

## Ovládání

- **W/S** - pohyb v menu nahoru/dolů
- **D/Enter** - potvrdit výběr
- **A/Esc** - zpět

## Struktura projektu

```
zeddihub-tools/
├── launcher.py                  # Hlavní launcher
├── ZeddiHub Tools Launcher.bat  # Windows spouštěč
├── zeddihub_rust_editor/        # Rust Editor modul
├── zeddihub_csgo_tools/         # CS:GO Tools modul
├── zeddihub_cs2_tools/          # CS2 Tools modul
├── zeddihub_translator/         # Translator modul
└── zeddihub_server_status/      # Server Status modul
```

Každý modul obsahuje: `core.py` (základ), `langs.py` (překlady), `wizard.py` (průvodce), `menus.py` (menu), `main.py` (vstupní bod).

## Licence

Tento projekt je soukromý. Všechna práva vyhrazena.

## Autor

**ZeddiS** - [zeddihub.eu](https://zeddihub.eu) | [Discord](https://dsc.gg/zeddihub)
