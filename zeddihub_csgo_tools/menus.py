import os
import sys
import time
from .core import *
from . import wizard
from . import server_tools
from . import player_tools

def player_tools_menu():
    sel = 0
    while True:
        opts = [
            "Crosshair Generátor (S náhledem)",
            "Viewmodel Generátor (Live Preview okno)",
            "Autoexec Config Generátor",
            "Practice Config Generátor",
            "Buy Binds Generátor",
            "Editor vlastních Configů (.cfg)"
        ]
        descs = [
            "Vygeneruje tvůj unikátní crosshair pomocí ASCII náhledu v konzoli.",
            "Vytvoříš si viewmodel, který ihned vidíš ve vyskakovacím 2D okně.",
            "Základní generátor tvých ratů, FPS a sítě.",
            "Vygeneruje practice config s granáty a nekonečnou municí.",
            "Vygeneruje buy bindy na numpad pro rychlý nákup.",
            "Najde, upraví a uloží jakýkoliv .cfg soubor na tvém disku."
        ]
        render_menu("HRÁČSKÉ NÁSTROJE", opts, sel, descs)
        k = read_key()

        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                player_tools.crosshair_generator()
            elif sel == 1:
                player_tools.viewmodel_generator()
            elif sel == 2:
                player_tools.config_generator()
            elif sel == 3:
                player_tools.practice_config()
            elif sel == 4:
                player_tools.buy_binds_generator()
            elif sel == 5:
                player_tools.config_editor()

def server_tools_menu():
    sel = 0
    while True:
        opts = [
            "Editor Databases.cfg",
            "Server.cfg Generátor",
            "SourceMod Překladač"
        ]
        descs = [
            "Upraví, naklonuje a zformátuje SQL a SQLite údaje ve tvých databázích.",
            "Vygeneruje kompletní server.cfg s rozumnými výchozími hodnotami.",
            "Vezme SourceMod překlady (např. core.phrases.txt) a přeloží je i pomocí Google API."
        ]
        render_menu("SERVEROVÉ NÁSTROJE", opts, sel, descs)
        k = read_key()

        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                server_tools.run_database_editor()
            elif sel == 1:
                server_tools.server_cfg_generator()
            elif sel == 2:
                server_tools.run_sourcemod_translator()

def settings_menu():
    sel = 0
    while True:
        opts = [
            f"Zdrojová složka: {os.path.basename(settings['source_dir'])}", 
            f"Cílová složka: {os.path.basename(settings['target_dir'])}", 
            f"Zálohování (Před uložením): {'✅ ZAPNUTO' if settings['auto_backup'] else '❌ VYPNUTO'}",
            f"Otevřít složku po dokončení: {'✅ ZAPNUTO' if settings.get('open_folder_after', True) else '❌ VYPNUTO'}",
            f"UI Jazyk: {settings['ui_lang'].upper()}",
            RED + t("reset_def") + RESET
        ]
        descs = [
            "Složka, ze které se načítají originální konfigurace a překlady ke kontrole.", 
            "Složka, kam se budou automaticky ukládat všechny vygenerované a opravené soubory.", 
            "Pokud je ZAPNUTO, původní soubory se automaticky uloží do složky backups.", 
            "Po úspěšném vygenerování souboru (databáze/crosshair atd.) otevře okno Windows Exploreru.",
            "Hlavní jazyk tohoto uživatelského rozhraní (CZ/EN).", 
            "Smaže kompletně konfigurační soubor a provede tvrdý restart celé aplikace do Prvotní instalace."
        ]
        render_menu(t("m_settings"), opts, sel, descs)
        k = read_key()
        save_settings()
        
        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: 
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                p = filedialog.askdirectory(title="Vyberte Zdrojovou složku")
                root.destroy()
                if p:
                    settings['source_dir'] = p
            elif sel == 1:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                p = filedialog.askdirectory(title="Vyberte Cílovou složku")
                root.destroy()
                if p:
                    settings['target_dir'] = p
            elif sel == 2:
                settings["auto_backup"] = not settings["auto_backup"]
            elif sel == 3:
                settings["open_folder_after"] = not settings.get("open_folder_after", True)
            elif sel == 4:
                settings["ui_lang"] = "en" if settings["ui_lang"] == "cz" else "cz"
            elif sel == 5:
                if os.path.exists(CONFIG_PATH):
                    os.remove(CONFIG_PATH)
                print_header()
                print("\n"*4 + RED + center("RESTARTUJI APLIKACI DO TOVÁRNÍHO NASTAVENÍ...") + RESET)
                time.sleep(2)
                raise ReturnToLauncher()

def credits_menu():
    import webbrowser
    sel = 0
    while True:
        opts = ["🌐 Web (zeddihub.eu)", "👨‍💻 ZeddiS (zeddis.xyz)", "💬 Discord (dsc.gg/zeddihub)", f"✨ Verze Aplikace: {VERSION} ✨"]
        render_menu(t("m_credits"), opts, sel)
        k = read_key()
        
        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                webbrowser.open("https://zeddihub.eu")
            elif sel == 1:
                webbrowser.open("https://zeddis.xyz")
            elif sel == 2:
                webbrowser.open("https://dsc.gg/zeddihub")

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
                f"👤 {t('m_player')} 👤", 
                f"🖥️ {t('m_server')} 🖥️", 
                f"⚙️ {t('m_settings')} ⚙️", 
                f"🌟 {t('m_credits')} 🌟"
            ]
            descs = [t('d_player'), t('d_server'), t('d_settings'), t('d_credits')]
            render_menu(t("main_menu"), opts, sel, descs, centered=True)
            k = read_key()
            
            if k in ['a', 'esc', 'q']:
                raise ReturnToLauncher()
            elif k == 'w' and sel > 0:
                sel -= 1
            elif k == 's' and sel < len(opts)-1:
                sel += 1
            elif k in ['d', 'enter', 'space']:
                if sel == 0:
                    player_tools_menu()
                elif sel == 1:
                    server_tools_menu()
                elif sel == 2:
                    settings_menu()
                elif sel == 3:
                    credits_menu()
                
        except ReturnToLauncher:
            return