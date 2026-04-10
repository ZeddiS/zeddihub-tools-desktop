import os
import time
import tkinter as tk
from tkinter import filedialog
from .core import *

def first_run_wizard():
    print_header()
    print("\n"*4 + center(YELLOW + t("wiz_title") + RESET))
    print(center(CYAN + "Welcome! Let's set up the basics." + RESET))
    time.sleep(2)
    
    opts = ["Čeština", "English"]
    sel = 0
    while True:
        render_menu(t("wiz_step1"), opts, sel, footer="[W/S] Move | [Enter] Select")
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            settings["ui_lang"] = "cz" if sel == 0 else "en"
            break
            
    while True:
        print_header()
        print("\n"*4 + center(YELLOW + t("wiz_step2") + RESET))
        print(center(CYAN + t("dlg_src") + RESET))
        time.sleep(1.5)
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        p = filedialog.askdirectory(title=t("dlg_src"))
        root.destroy()
        
        if p:
            print_header()
            print("\n"*4 + center(YELLOW + "Zahrnout pro analýzu i podsložky? (A = Ano / N = Ne)" + RESET))
            inc_sub = (read_key(allow_esc_exit=False) == 'a')
            
            valid, invalid = check_cs_validity(p, inc_sub)
            if invalid:
                print_header()
                print("\n"*2 + RED + center("VAROVÁNÍ: Nalezeny syntax chyby (nesedí složené závorky) u těchto souborů:") + RESET)
                for i in invalid[:15]: print(center(i))
                if len(invalid) > 15: print(center(f"... a dalších {len(invalid)-15}"))
                time.sleep(4)
            settings["source_dir"] = p
            break
        else:
            settings["source_dir"] = os.path.join(SCRIPT_DIR, "source_plugins")
            break

    while True:
        print_header()
        print("\n"*4 + center(YELLOW + t("wiz_step3") + RESET))
        print(center(CYAN + t("dlg_tgt") + RESET))
        time.sleep(1.5)
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        p = filedialog.askdirectory(title=t("dlg_tgt"))
        root.destroy()
        
        if p:
            if os.path.basename(p).lower() != "plugins": p = os.path.join(p, "plugins")
            settings["target_dir"] = p
            break
        else:
            settings["target_dir"] = os.path.join(SCRIPT_DIR, "fixed_plugins", "plugins")
            break

    pa_opts = ["Nic nedělat", "Ukončit aplikaci", "Režim spánku", "Vypnout PC"]; sel = 0
    while True:
        render_menu(t("wiz_step4"), pa_opts, sel, footer="[W/S] Posun | [Enter] Vybrat")
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(pa_opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']: settings["post_action"] = sel; break

    sel = 0; yn = ["ANO (Doporučeno)", "NE"]
    while True:
        render_menu(t("wiz_step5"), yn, sel, ["Po dokončení fronty zkusí Editor automaticky kompilaci nanečisto."] * 2, footer="[W/S] Posun | [Enter] Vybrat")
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter', 'space']: settings["run_compiler_after"] = (sel == 0); break
        
    sel = 0
    while True:
        render_menu(t("wiz_step6"), yn, sel, ["Po dokončení fronty otevře okno průzkumníka s opravenými soubory."] * 2, footer="[W/S] Posun | [Enter] Vybrat")
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter', 'space']: settings["open_folder_after"] = (sel == 0); break

    os.makedirs(settings["source_dir"], exist_ok=True)
    os.makedirs(settings["target_dir"], exist_ok=True)
    os.makedirs(settings["backup_dir"], exist_ok=True)
    os.makedirs(settings["log_dir"], exist_ok=True)
    save_settings()

def pause_menu():
    sel = 0
    while True:
        spd_idx = SPEEDS.index(settings['write_speed'])
        vis_fill = len(SPEEDS) - spd_idx
        bar = "█" * vis_fill + "░" * (len(SPEEDS) - vis_fill)
        spd_txt = f"[{bar}]"
        
        pa_opts = ["Nic", "Ukončit aplikaci", "Režim spánku", "Vypnout PC"]
        opts = ["Pokračovat", f"Rychlost vizualizace: {spd_txt}", f"Po dokončení: {pa_opts[settings.get('post_action', 0)]}", "Zrušit a vrátit se do Menu"]
        render_menu("PROCES POZASTAVEN", opts, sel, footer="[W/S] Pohyb | [Enter] Vybrat | [P/A] Pokračovat")
        k = read_key(allow_esc_exit=False)
        
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: return "resume"
            elif sel == 1: settings["write_speed"] = SPEEDS[(SPEEDS.index(settings["write_speed"])+1)%len(SPEEDS)]
            elif sel == 2: settings["post_action"] = (settings.get("post_action", 0) + 1) % 4
            elif sel == 3: return "abort"
        elif k in ['a', 'p', 'esc', 'q']: return "resume"