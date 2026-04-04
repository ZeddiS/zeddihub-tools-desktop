import os
import time
import platform
from .core import *

def interactive_folders():
    sel_dir = 0
    opts_dir = [
        f"Zdrojová složka (Původní): {os.path.basename(settings['source_dir'])}",
        f"Cílová složka (Opravené): {os.path.basename(settings['target_dir'])}"
    ]
    
    while True:
        render_menu("PŘEHLED SLOŽEK - VÝBĚR", opts_dir, sel_dir, footer="[W/S] Pohyb | [Enter] Vybrat | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel_dir > 0: sel_dir -= 1
        elif k == 's' and sel_dir < len(opts_dir)-1: sel_dir += 1
        elif k in ['d', 'enter', 'space']:
            t_dir = settings["source_dir"] if sel_dir == 0 else settings["target_dir"]
            break

    if not os.path.exists(t_dir):
        print_header(); print("\n"*4 + YELLOW + center("Tato složka zatím neexistuje.") + RESET); time.sleep(2); return

    sel = 0
    while True:
        files = sorted([fi for fi in os.listdir(t_dir) if fi.endswith(".cs")])
        if not files:
            print_header(); print("\n"*4 + YELLOW + center("Tato složka je prázdná.") + RESET); time.sleep(2); return

        f_opts = [f"📄 {fi}" for fi in files]
        render_menu(f"PŘEHLED: {os.path.basename(t_dir)}", f_opts, sel, footer="[W/S] Pohyb | [Enter] Číst | [O] Otevřít ve Windows | [A/Esc] Zpět")
        k = read_key()
        if k == 'refresh': continue
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(f_opts)-1: sel += 1
        elif k == 'o':
            if platform.system() == "Windows":
                try: os.startfile(t_dir)
                except Exception: pass
        elif k in ['d', 'enter', 'space']:
            filepath = os.path.join(t_dir, files[sel])
            try:
                with open(filepath, 'r', encoding='utf-8') as f: lines = f.read().splitlines()
                detail_view(f"ČTENÍ SOUBORU: {files[sel]}", [{"preview": f"{i+1}: {l.strip()}", "full": l, "filepath": filepath} for i, l in enumerate(lines) if l.strip()])
            except Exception: pass