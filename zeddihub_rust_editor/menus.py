import os
import sys
import time
import subprocess
from .core import *
from . import wizard
from . import queue_tools
from . import analyzers
from . import compiler
from . import folders
from . import server_tools

def tools_menu():
    sel = 0
    while True:
        queue_count = len(task_queue)
        opts = [
            "🛠️ Hromadná oprava pluginů",
            "💻 Úprava In-game Příkazů",
            "🌍 Překladač Zpráv v Kódu",
            "🏷️ Detektor Prefixů",
            f"▶ SPUSTIT FRONTU OPRAV (Čeká: {queue_count})" if queue_count > 0 else f"⏸ FRONTA JE PRÁZDNÁ",
            "🔙 Zpět"
        ]
        descs = [
            "Aplikuje nejnovější záplaty na staré pluginy.",
            "Najde a umožní přepsat příkazy do chatu a konzole.",
            "Najde hardcoded anglické zprávy do chatu a umožní překlad.",
            "Najde definice prefixů a umožní změnit jejich jméno a barvu.",
            "Kliknutím sem se spustí všechny úpravy najednou a uloží se.",
            ""
        ]

        q_box = None
        if queue_count > 0:
            q_box = []
            for t_item in task_queue[-5:]:
                q_box.append(f"[{t_item['type'].upper()}] {t_item['file']} - {t_item.get('desc', '')}")
            if queue_count > 5:
                q_box.append(f"... a dalších {queue_count - 5} úkolů čeká ve frontě.")

        render_menu("🛠️ NÁSTROJE PRO OPRAVU PLUGINŮ", opts, sel, descs, footer="[W/S] Pohyb | [Enter] Vybrat | [A/Esc] Zpět", queue_box=q_box)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: queue_tools.queue_bulk_fix()
            elif sel == 1: queue_tools.queue_command_editor()
            elif sel == 2: queue_tools.queue_hardcoded_translator()
            elif sel == 3: queue_tools.queue_prefix_detector()
            elif sel == 4: queue_tools.execute_queue()
            elif sel == 5: return

def command_search():
    """Search for commands, hooks, and permissions across all .cs plugins."""
    import re as regex
    source = settings.get("source_dir", "")
    if not source or not os.path.isdir(source):
        print_header()
        print("\n" * 4 + RED + center("Zdrojová složka není nastavena nebo neexistuje!") + RESET)
        time.sleep(2)
        return

    cs_files = [f for f in os.listdir(source) if f.endswith('.cs')]
    if not cs_files:
        print_header()
        print("\n" * 4 + RED + center("Ve zdrojové složce nebyly nalezeny žádné .cs soubory!") + RESET)
        time.sleep(2)
        return

    print_header()
    print("\n" * 3 + YELLOW + BOLD + center("🔍 VYHLEDÁVÁNÍ V PLUGINECH") + RESET)
    print(GRAY + center("Zadejte hledaný výraz (název příkazu, hooku, permisse...)") + RESET)
    query = safe_input("\n" + center("Hledat: "))
    if not query or not query.strip():
        return
    query = query.strip().lower()

    results = []
    patterns = {
        "chat_cmd": regex.compile(r'\[ChatCommand\s*\(\s*"([^"]+)"', regex.MULTILINE),
        "console_cmd": regex.compile(r'\[ConsoleCommand\s*\(\s*"([^"]+)"', regex.MULTILINE),
        "hook": regex.compile(r'(?:void|object|bool|string)\s+(On\w+|Can\w+)\s*\(', regex.MULTILINE),
        "permission": regex.compile(r'permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"', regex.MULTILINE),
        "plugin_ref": regex.compile(r'\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)', regex.MULTILINE),
    }

    for fname in cs_files:
        fpath = os.path.join(source, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        for label, pattern in patterns.items():
            for m in pattern.finditer(content):
                value = m.group(1)
                if query in value.lower() or query in fname.lower():
                    line_num = content[:m.start()].count('\n') + 1
                    results.append({"file": fname, "type": label, "value": value, "line": line_num})

        if query in content.lower():
            for i, line in enumerate(content.splitlines(), 1):
                if query in line.lower() and not any(r["file"] == fname and r["line"] == i for r in results):
                    snippet = line.strip()[:60]
                    results.append({"file": fname, "type": "text", "value": snippet, "line": i})

    sel = 0
    type_labels = {"chat_cmd": "💬 Chat CMD", "console_cmd": "🖥️ Console CMD", "hook": "🪝 Hook", "permission": "🔑 Permission", "plugin_ref": "🔗 Plugin Ref", "text": "📄 Text"}

    while True:
        opts = []
        descs = []
        for r in results[:30]:
            label = type_labels.get(r["type"], r["type"])
            opts.append(f"{label}  {r['value']}")
            descs.append(f"{r['file']}:{r['line']}")

        if not opts:
            opts = ["Žádné výsledky"]
            descs = [f"Výraz '{query}' nebyl nalezen v žádném pluginu."]

        title = f"🔍 VÝSLEDKY: '{query}' ({len(results)} nalezeno)"
        render_menu(title, opts, sel, descs, footer="[W/S] Pohyb | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1

def player_tools_menu():
    sel = 0
    while True:
        opts = [
            "🔍 Vyhledávání v Pluginech",
            "🛠️ Nástroje pro Opravu Pluginů",
            "🔬 Kontrola Stability Pluginů",
            "📋 Extrakce Příkazů",
        ]
        descs = [
            "Hledejte příkazy, hooky a permisse napříč všemi pluginy.",
            "Hromadná oprava, překlad zpráv, úprava příkazů a prefixů.",
            "Zkontroluje kód pluginů na běžné chyby a problémy.",
            "Extrahuje seznam všech příkazů ze zdrojových souborů.",
        ]
        render_menu("👤 HRÁČSKÉ NÁSTROJE", opts, sel, descs)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: command_search()
            elif sel == 1: tools_menu()
            elif sel == 2: analyzers.run_stability_check()
            elif sel == 3: analyzers.run_command_extractor()

def server_tools_menu():
    sel = 0
    while True:
        opts = [
            "🖥️ RCON Klient",
            "🔗 Plugin Dependency Checker",
            "📊 Simulátor Generovaných Dat",
            "⚙️ C# Kompilátor",
            "📁 Správa Složek",
        ]
        descs = [
            "Připojte se k Rust serveru přes RCON a posílejte příkazy vzdáleně.",
            "Analyzuje závislosti Oxide/uMod pluginů ve zdrojové složce.",
            "Simuluje data, která pluginy generují do datových souborů.",
            "Zkompiluje .cs pluginy s referencemi Oxide/Rust.",
            "Interaktivní správa zdrojových a cílových složek.",
        ]
        render_menu("🖥️ SERVEROVÉ NÁSTROJE", opts, sel, descs)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: server_tools.rcon_client()
            elif sel == 1: server_tools.plugin_dependency_checker()
            elif sel == 2: analyzers.run_generated_files_simulator()
            elif sel == 3: compiler.run_compiler_simulator()
            elif sel == 4: folders.interactive_folders()

def settings_menu():
    sel = 0
    pa_opts = ["Nic", "Ukončit aplikaci", "Režim spánku", "Vypnout PC"]
    while True:
        opts = [
            f"📂 Zdrojová složka: {os.path.basename(settings['source_dir'])}",
            f"📁 Cílová složka: {os.path.basename(settings['target_dir'])}",
            f"💾 Zálohování: {'✅ ZAPNUTO' if settings['auto_backup'] else '❌ VYPNUTO'}",
            f"🌐 UI Jazyk: {settings['ui_lang'].upper()}",
            f"⏭️ Po dokončení akce: {pa_opts[settings.get('post_action', 0)]}",
            f"🔨 Simulace po dokončení: {'✅ ZAPNUTO' if settings.get('run_compiler_after') else '❌ VYPNUTO'}",
            f"📂 Otevřít složku po dokončení: {'✅ ZAPNUTO' if settings.get('open_folder_after') else '❌ VYPNUTO'}",
            RED + "🔄 " + t("reset_def") + RESET
        ]
        descs = [
            "Složka, ze které se načítají originální rozbité pluginy ke kontrole.",
            "Složka, kam se budou automaticky ukládat všechny opravené soubory.",
            "Pokud je ZAPNUTO, původní .cs soubory se automaticky uloží do složky backups.",
            "Hlavní jazyk tohoto uživatelského rozhraní (CZ/EN).",
            "Vybere akci, která se stane ihned po dokončení překladů nebo fronty oprav.",
            "Po úspěšné úpravě z fronty Editor automaticky provede tichou kompilaci a vypíše C# chyby.",
            "Po úspěšném zpracování fronty otevře okno Windows Exploreru s opravenými soubory.",
            "Smaže kompletně konfigurační soubor a provede tvrdý restart celé aplikace."
        ]
        render_menu("⚙️ " + t("m_settings"), opts, sel, descs)
        k = read_key()
        save_settings()

        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                p = filedialog.askdirectory(title="Vyberte Zdrojovou složku"); root.destroy()
                if p: settings['source_dir'] = p
            elif sel == 1:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
                p = filedialog.askdirectory(title="Vyberte Cílovou složku"); root.destroy()
                if p: settings['target_dir'] = p
            elif sel == 2: settings["auto_backup"] = not settings["auto_backup"]
            elif sel == 3: settings["ui_lang"] = "en" if settings["ui_lang"] == "cz" else "cz"
            elif sel == 4: settings["post_action"] = (settings.get("post_action", 0) + 1) % 4
            elif sel == 5: settings["run_compiler_after"] = not settings.get("run_compiler_after", False)
            elif sel == 6: settings["open_folder_after"] = not settings.get("open_folder_after", False)
            elif sel == 7:
                if os.path.exists(CONFIG_PATH): os.remove(CONFIG_PATH)
                print_header(); print("\n"*4 + RED + center("RESTARTUJI APLIKACI DO TOVÁRNÍHO NASTAVENÍ...") + RESET); time.sleep(2)
                raise ReturnToLauncher()

def credits_menu():
    import webbrowser
    sel = 0
    while True:
        opts = [
            "🌐 Web (zeddihub.eu)",
            "📖 ZeddiWiki (wiki.zeddihub.eu)",
            "👨‍💻 ZeddiS (zeddis.xyz)",
            "🐙 GitHub (github.com/ZeddiS)",
            "💬 Discord (dsc.gg/zeddihub)",
            f"✨ Verze: {VERSION}"
        ]
        render_menu("🌟 " + t("m_credits"), opts, sel, [t("d_credits")]*6)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: webbrowser.open("https://zeddihub.eu")
            elif sel == 1: webbrowser.open("https://wiki.zeddihub.eu")
            elif sel == 2: webbrowser.open("https://zeddis.xyz")
            elif sel == 3: webbrowser.open("https://github.com/ZeddiS")
            elif sel == 4: webbrowser.open("https://dsc.gg/zeddihub")

def start_editor():
    setup_console()
    if not load_settings():
        wizard.first_run_wizard()

    print_header()
    print("\n"*4 + center(YELLOW + "★ " * 15 + RESET))
    print(center(ORANGE + t("welcome") + RESET))
    print(center(GRAY + t("quote") + RESET))
    print(center(YELLOW + "★ " * 15 + RESET))
    time.sleep(2)

    sel = 0
    while True:
        try:
            opts = [
                f"👤 {t('m_player')}",
                f"🖥️ {t('m_server')}",
                f"⚙️ {t('m_settings')}",
                f"🌟 {t('m_credits')}"
            ]
            descs = [t('d_player'), t('d_server'), t('d_settings'), t('d_credits')]
            render_menu(t("main_menu"), opts, sel, descs, centered=True)
            k = read_key()

            if k in ['a', 'esc', 'q']: raise ReturnToLauncher()
            elif k == 'w' and sel > 0: sel -= 1
            elif k == 's' and sel < len(opts)-1: sel += 1
            elif k in ['d', 'enter', 'space']:
                if sel == 0: player_tools_menu()
                elif sel == 1: server_tools_menu()
                elif sel == 2: settings_menu()
                elif sel == 3: credits_menu()

        except ReturnToLauncher:
            return
