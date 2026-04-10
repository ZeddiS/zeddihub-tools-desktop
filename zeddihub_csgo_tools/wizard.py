import os
import time
import tkinter as tk
from tkinter import filedialog
from .core import *

def first_run_wizard():
    print_header()
    print("\n"*4 + center(YELLOW + t("wiz_title") + RESET))
    print(center(CYAN + "Welcome to CS:GO Tools setup." + RESET))
    time.sleep(2)
    
    opts = ["Čeština", "English"]
    sel = 0
    while True:
        render_menu(t("wiz_step1"), opts, sel, footer="[W/S] Move | [Enter] Select")
        k = read_key(allow_esc_exit=False)
        if k == 'refresh':
            continue
        if k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < 1:
            sel += 1
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
            settings["source_dir"] = p
            break
        else:
            settings["source_dir"] = os.path.join(SCRIPT_DIR, "source_configs")
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
            settings["target_dir"] = p
            break
        else:
            settings["target_dir"] = os.path.join(SCRIPT_DIR, "fixed_configs")
            break

    os.makedirs(settings["source_dir"], exist_ok=True)
    os.makedirs(settings["target_dir"], exist_ok=True)
    os.makedirs(settings["backup_dir"], exist_ok=True)
    save_settings()