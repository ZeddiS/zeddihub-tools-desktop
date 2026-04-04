import os
import sys
import time
import subprocess
import shutil
from .core import *
from . import modules

def prefix_manager_menu():
    sel = 0
    while True:
        p_c, b_c = hex_to_ansi(settings["prefix_color"]), hex_to_ansi(settings["prefix_color"] if settings.get("prefix_sync_color") else settings["prefix_bracket_color"])
        preview = f"{b_c}[{RESET}{p_c}{settings['prefix_text']}{RESET}{b_c}]{RESET}" if settings["prefix_use_brackets"] else f"{p_c}{settings['prefix_text']}{RESET}"
        if not settings["prefix_text"] or settings["prefix_text"] == "Nevyplněno": preview = f"{GRAY}Nevyplněno{RESET}"
        
        opts = [f"Stav: {'✅ ZAP' if settings['prefix_enabled'] else '❌ VYP'}", f"Náhled: {preview}", f"Barva textu: {p_c}{settings['prefix_color']}{RESET}", "Rozšířené nastavení"]
        render_menu(t("m_prefix"), opts, sel, [t("pm_d1"), t("pm_d2"), t("pm_d3"), t("pm_d4")])
        k = read_key()
        save_settings()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: settings["prefix_enabled"] = not settings["prefix_enabled"]
            elif sel == 1:
                print_header(); print("\n"*4 + center(t("new_pref")))
                nt = safe_input(center(t("inp_esc") + "\n\n" + center("")))
                if nt is not None: settings["prefix_text"] = nt.strip() if nt.strip() else "Nevyplněno"
            elif sel == 2: settings["prefix_color"] = choose_color_custom(settings["prefix_color"])
            elif sel == 3: 
                if modules.prefix_adv_sub() == 'q': return 'q'

def settings_menu():
    sel = 0
    while True:
        opts = [f"Zdroj: {os.path.basename(settings['source_dir'])} ({settings['source_lang']})", f"Cíl: {os.path.basename(settings['target_dir'])}", "Cílové jazyky", f"Formát: {settings['file_extension']}", "Překladač a API", "Cesty a Systém", f"UI Jazyk: {settings['ui_lang'].upper()}", RED + t("reset_def") + RESET]
        descs = [t("d_src"), t("d_tgt"), t("d_langs"), t("d_fmt"), t("d_api"), t("d_sys"), t("d_ui"), t("d_reset")]
        render_menu(t("m_settings"), opts, sel, descs)
        k = read_key()
        save_settings()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: 
                if modules.flow_select_source() == 'q': return 'q'
            elif sel == 1: 
                if modules.flow_select_target() == 'q': return 'q'
            elif sel == 2: 
                if lang_select_sub() == 'q': return 'q'
            elif sel == 3:
                exts = [".json", ".txt", ".lang", "Vlastní"]; e_s = 0
                while True:
                    render_menu("FORMÁT SOUBORŮ", exts, e_s)
                    ek = read_key()
                    if ek in ['a', 'esc', 'q']: break
                    elif ek == 'w' and e_s > 0: e_s -= 1
                    elif ek == 's' and e_s < len(exts)-1: e_s += 1
                    elif ek in ['d', 'enter']:
                        if e_s == 3:
                            print_header(); print("\n"*4 + center(t("type_ext")))
                            ex = safe_input(center(t("inp_esc") + "\n\n" + center("")))
                            if ex is not None and ex.strip(): settings["file_extension"] = ex.strip() if ex.strip().startswith(".") else "." + ex.strip()
                        else: settings["file_extension"] = exts[e_s]
                        break
            elif sel == 4: 
                if modules.engine_select_sub() == 'q': return 'q'
            elif sel == 5: 
                if path_select_sub() == 'q': return 'q'
            elif sel == 6: settings["ui_lang"] = "en" if settings["ui_lang"] == "cz" else "cz"
            elif sel == 7:
                if os.path.exists(CONFIG_PATH): os.remove(CONFIG_PATH)
                print_header(); print("\n"*4 + RED + center("RESTARTUJI APLIKACI DO TOVÁRNÍHO NASTAVENÍ...") + RESET); time.sleep(2)
                launcher_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "launcher.py")
                subprocess.Popen([sys.executable, launcher_path]); sys.exit()

def lang_select_sub():
    l_keys = list(SUPPORTED_LANGS.keys()); sel = 0
    while True:
        opts = [f"{'✅' if l in settings['selected_langs'] else '☐'} {SUPPORTED_LANGS[l]}" for l in l_keys]
        render_menu("CÍLOVÉ JAZYKY", opts, sel, footer="[H] Hlavní | [V] Vše | [N] Nic | [W/S] Pohyb | [Enter] Zvolit | [A/Esc] Zpět")
        k = read_key()
        save_settings()
        if k in ['a', 'esc', 'q']: return
        elif k == 'h': settings["selected_langs"] = ["en", "cs", "ru", "de", "es", "fr"]
        elif k == 'v': settings["selected_langs"] = list(SUPPORTED_LANGS.keys())
        elif k == 'n': settings["selected_langs"] = []
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            l = l_keys[sel]
            if l in settings["selected_langs"]: settings["selected_langs"].remove(l)
            else: settings["selected_langs"].append(l)

def path_select_sub():
    sel = 0
    pa_opts = [t("pa_none"), t("pa_exit"), t("pa_sleep"), t("pa_shutdown")]
    while True:
        spd_idx = SPEEDS.index(settings['write_speed'])
        vis_fill = len(SPEEDS) - spd_idx
        bar = "█" * vis_fill + "░" * (len(SPEEDS) - vis_fill)
        
        txt_ano = "ANO" if settings["ui_lang"] == "cz" else "YES"
        txt_ne = "NE" if settings["ui_lang"] == "cz" else "NO"
        opts = [f"Zálohy (.bak): {'✅ ' + txt_ano if settings['auto_backup'] else '❌ ' + txt_ne}", f"Smart Cache: {'✅ ' + txt_ano if settings['smart_cache'] else '❌ ' + txt_ne}", f"Zálohy: {os.path.basename(settings['backup_dir'])}", f"Logy: {os.path.basename(settings['log_dir'])}", f"{t('o_speed')}: [{bar}]", f"{t('post_action')}: {pa_opts[settings.get('post_action', 0)]}"]
        render_menu("CESTY A SYSTÉM", opts, sel)
        k = read_key()
        save_settings()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: settings["auto_backup"] = not settings["auto_backup"]
            elif sel == 1: settings["smart_cache"] = not settings["smart_cache"]
            elif sel == 2:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); p = filedialog.askdirectory(title=t("dlg_bak")); root.destroy()
                if p: settings["backup_dir"] = p
            elif sel == 3:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); p = filedialog.askdirectory(title=t("dlg_log")); root.destroy()
                if p: settings["log_dir"] = p
            elif sel == 4: settings["write_speed"] = SPEEDS[(SPEEDS.index(settings["write_speed"])+1)%len(SPEEDS)]
            elif sel == 5: settings["post_action"] = (settings.get("post_action", 0) + 1) % 4

def credits_menu():
    import webbrowser
    sel = 0
    while True:
        opts = [f"🌐 Web (zeddihub.eu)", f"🔨 Banlist (banlist.zeddihub.eu)", f"💬 Discord (dsc.gg/zeddihub)", f"✨ Verze Aplikace: {VERSION} ✨"]
        render_menu(t("m_credits"), opts, sel, [t("d_credits")]*4)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: webbrowser.open("https://zeddihub.eu")
            elif sel == 1: webbrowser.open("https://banlist.zeddihub.eu")
            elif sel == 2: webbrowser.open("https://dsc.gg/zeddihub")

def start_translator():
    setup_console()
    if not load_settings():
        modules.first_run_wizard()
        
    print_header()
    print("\n"*4 + center(YELLOW + "★ " * 15 + RESET))
    print(center(ORANGE + t("welcome") + RESET))
    print(center(GRAY + t("quote") + RESET))
    print(center(YELLOW + "★ " * 15 + RESET)); time.sleep(2)
    
    sel = 0
    while True:
        try:
            opts = [
                f"{t('m_run')}",
                f"{t('m_sel')}",
                f"{t('m_prefix')}",
                "Statistiky překladu" if settings["ui_lang"] == "cz" else "Translation Stats",
                "Batch Export",
                f"{t('m_settings')}",
                f"{t('m_folders')}",
                f"{t('m_cleanup')}",
                f"{t('m_credits')}",
                f"{t('m_exit')}"
            ]
            descs = [
                t('d_run'), t('d_sel'), t('d_prefix'),
                "Přehled stavu překladu pro všechny jazyky." if settings["ui_lang"] == "cz" else "Overview of translation progress for all languages.",
                "Export všech překladů do jednoho souboru (TXT/JSON/CSV)." if settings["ui_lang"] == "cz" else "Export all translations to a single file (TXT/JSON/CSV).",
                t('d_settings'), t('d_folders'), t('d_cleanup'), t('d_credits'), ""
            ]
            render_menu(t('main_menu'), opts, sel, descs, centered=True)
            k = read_key()
            if k in ['a', 'esc', 'q']: continue
            elif k == 'w' and sel > 0: sel -= 1
            elif k == 's' and sel < len(opts)-1: sel += 1
            elif k in ['d', 'enter']:
                if sel == 0: modules.run_translation()
                elif sel == 1: modules.selective_translation()
                elif sel == 2: prefix_manager_menu()
                elif sel == 3: modules.translation_stats()
                elif sel == 4: modules.batch_export()
                elif sel == 5: settings_menu()
                elif sel == 6: modules.interactive_folders()
                elif sel == 7:
                    print_header(); print("\n"*4 + RED + center("ČIŠTĚNÍ SLOŽEK") + RESET + "\n")
                    t_dir = settings["target_dir"]; has_clean = False
                    if os.path.exists(t_dir):
                        for d in os.listdir(t_dir):
                            p = os.path.join(t_dir, d)
                            if os.path.abspath(p) == os.path.abspath(settings["source_dir"]): continue
                            if os.path.isdir(p) and d in SUPPORTED_LANGS:
                                shutil.rmtree(p); print(center(f"Odstraněno: {d}")); has_clean = True
                    if not has_clean: print(GRAY + center(t("clean_empty")) + RESET)
                    time.sleep(2)
                elif sel == 8: credits_menu()
                elif sel == 9: return
        except Exception as e:
            action = modules.handle_crash(e)
            if action == "menu": continue
            elif action == "exit": sys.exit()
            elif action == "reset":
                if os.path.exists(CONFIG_PATH): os.remove(CONFIG_PATH)
                launcher_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "launcher.py")
                subprocess.Popen([sys.executable, launcher_path]); sys.exit()

if __name__ == "__main__":
    start_translator()