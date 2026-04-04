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
            "🔙 Zpět do Hlavního menu"
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
            for t in task_queue[-5:]:
                q_box.append(f"[{t['type'].upper()}] {t['file']} - {t.get('desc', '')}")
            if queue_count > 5:
                q_box.append(f"... a dalších {queue_count - 5} úkolů čeká ve frontě.")

        render_menu("NÁSTROJE PRO OPRAVU PLUGINŮ (FRONTA)", opts, sel, descs, footer="[W/S] Pohyb | [Enter] Vybrat | [A/Esc] Zpět", queue_box=q_box)
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

def settings_menu():
    sel = 0
    pa_opts = ["Nic", "Ukončit aplikaci", "Režim spánku", "Vypnout PC"]
    while True:
        opts = [
            f"Zdrojová složka: {os.path.basename(settings['source_dir'])}", 
            f"Cílová složka: {os.path.basename(settings['target_dir'])}", 
            f"Zálohování: {'✅ ZAPNUTO' if settings['auto_backup'] else '❌ VYPNUTO'}",
            f"UI Jazyk: {settings['ui_lang'].upper()}",
            f"Po dokončení akce: {pa_opts[settings.get('post_action', 0)]}",
            f"Simulace po dokončení: {'✅ ZAPNUTO' if settings.get('run_compiler_after') else '❌ VYPNUTO'}",
            f"Otevřít složku po dokončení: {'✅ ZAPNUTO' if settings.get('open_folder_after') else '❌ VYPNUTO'}",
            RED + t("reset_def") + RESET
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
        render_menu(t("m_settings"), opts, sel, descs)
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
        opts = ["🌐 Web (zeddihub.eu)", "👨‍💻 ZeddiS (zeddis.xyz)", "💬 Discord (dsc.gg/zeddihub)", f"✨ Verze Aplikace: {VERSION} ✨"]
        render_menu(t("m_credits"), opts, sel, [t("d_credits")]*4)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: webbrowser.open("https://zeddihub.eu")
            elif sel == 1: webbrowser.open("https://zeddis.xyz")
            elif sel == 2: webbrowser.open("https://dsc.gg/zeddihub")

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
            qc = f" (Fronta: {len(task_queue)})" if len(task_queue) > 0 else ""
            opts = [
                f"{t('m_fix_menu')}{qc}",
                f"{t('m_check')}",
                f"{t('m_cmd_ext')}",
                f"{t('m_sim_data')}",
                f"{t('m_compiler')}",
                f"{t('m_folders')}",
                "RCON Klient",
                "Plugin Dependency Checker",
                f"{t('m_settings')}",
                f"{t('m_credits')}",
                f"{t('m_exit')}"
            ]
            descs = [t('d_fix_menu'), t('d_check'), t('d_cmd_ext'), t('d_sim_data'), t('d_compiler'), t('d_folders'),
                     "Pripojte se k Rust serveru pres RCON a posilejte prikazy.",
                     "Analyzuje zavislosti Oxide/uMod pluginu ve zdrojove slozce.",
                     t('d_settings'), t('d_credits'), ""]
            render_menu(t("main_menu"), opts, sel, descs, centered=True)
            k = read_key()

            if k in ['a', 'esc', 'q']: continue
            elif k == 'w' and sel > 0: sel -= 1
            elif k == 's' and sel < len(opts)-1: sel += 1
            elif k in ['d', 'enter', 'space']:
                if sel == 0: tools_menu()
                elif sel == 1: analyzers.run_stability_check()
                elif sel == 2: analyzers.run_command_extractor()
                elif sel == 3: analyzers.run_generated_files_simulator()
                elif sel == 4: compiler.run_compiler_simulator()
                elif sel == 5: folders.interactive_folders()
                elif sel == 6: server_tools.rcon_client()
                elif sel == 7: server_tools.plugin_dependency_checker()
                elif sel == 8: settings_menu()
                elif sel == 9: credits_menu()
                elif sel == 10: raise ReturnToLauncher()
                
        except ReturnToLauncher:
            return