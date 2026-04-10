import os
import json
import time
import sys
import shutil
import textwrap
import traceback
import tkinter as tk
from tkinter import filedialog
from .core import *

def prefix_adv_sub():
    sel = 0
    while True:
        txt_ano = "ANO" if settings["ui_lang"] == "cz" else "YES"
        txt_ne = "NE" if settings["ui_lang"] == "cz" else "NO"
        opts = [
            f"{t('pm_a1')}: {'✅ ' + txt_ano if settings['prefix_use_brackets'] else '❌ ' + txt_ne}",
            f"{t('pm_a2')}: {'✅ ' + txt_ano if settings.get('prefix_sync_color') else '❌ ' + txt_ne}",
            f"{t('pm_a3')}: {settings['prefix_bracket_color']}",
            f"{t('pm_a4')}: {'✅ ' + txt_ano if settings['prefix_detect_old'] else '❌ ' + txt_ne}"
        ]
        render_menu("ROZŠÍŘENÉ NASTAVENÍ PREFIXU" if settings["ui_lang"] == "cz" else "ADVANCED PREFIX SETTINGS", opts, sel)
        k = read_key()
        save_settings()
        if k in ['a', 'esc']: return
        elif k == 'q': return 'q'
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: settings["prefix_use_brackets"] = not settings["prefix_use_brackets"]
            elif sel == 1: settings["prefix_sync_color"] = not settings.get("prefix_sync_color", False)
            elif sel == 2: settings["prefix_bracket_color"] = choose_color_custom(settings["prefix_bracket_color"])
            elif sel == 3: settings["prefix_detect_old"] = not settings["prefix_detect_old"]

def check_json_validity(path):
    valid, invalid = 0, []
    for f in os.listdir(path):
        if f.endswith('.json'):
            try:
                with open(os.path.join(path, f), 'r', encoding='utf-8') as file:
                    json.load(file); valid += 1
            except: invalid.append(f)
    return valid, invalid

def ask_fallback(title_key):
    sel = 0; opts = [t("use_def"), t("retry")]
    while True:
        render_menu(t(title_key), opts, sel)
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k in ['a', 'q', 'esc']: return 'q'
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter']: return sel

def flow_select_source():
    while True:
        print_header(); print("\n"*4 + center(YELLOW + t("wiz_step2") + RESET))
        print(center(CYAN + t("dlg_src") + RESET)); time.sleep(1.5)
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        p = filedialog.askdirectory(title=t("dlg_src")); root.destroy()
        if p:
            if settings["file_extension"] == ".json":
                v, inv = check_json_validity(p)
                if v == 0 and not inv:
                    print_header(); print("\n"*4 + RED + center(t("warn_nojson")) + RESET); time.sleep(2)
                elif inv:
                    print_header(); print("\n"*2 + RED + center(t("warn_badjson")) + RESET)
                    for i in inv: print(center(i))
                    time.sleep(3)
            settings["source_dir"] = p
            break
        else:
            fb = ask_fallback("wiz_step2")
            if fb == 0:
                settings["source_dir"] = os.path.join(ZH_DIR, "source")
                os.makedirs(settings["source_dir"], exist_ok=True); break
            elif fb == 'q': return 'q'

    l_codes = ["en", "cs", "de", "ru", "es", "fr", "it", "nl", "pl", "pt", "tr", "zh", "ja", "ko", "uk", "ro"]; l_s = 0
    while True:
        l_opts = [SUPPORTED_LANGS[x] for x in l_codes]
        render_menu(t("wiz_step2b"), l_opts, l_s)
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k in ['a', 'q', 'esc']: return 'q'
        elif k == 'w' and l_s > 0: l_s -= 1
        elif k == 's' and l_s < len(l_opts)-1: l_s += 1
        elif k in ['d', 'enter']: settings["source_lang"] = l_codes[l_s]; break

def flow_select_target():
    while True:
        print_header(); print("\n"*4 + center(YELLOW + t("wiz_step3") + RESET))
        print(center(CYAN + t("dlg_tgt") + RESET)); time.sleep(1.5)
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        p = filedialog.askdirectory(title=t("dlg_tgt")); root.destroy()
        if p:
            if os.path.basename(p).lower() != "lang": p = os.path.join(p, "lang")
            settings["target_dir"] = p; break
        else:
            fb = ask_fallback("wiz_step3")
            if fb == 0:
                settings["target_dir"] = os.path.join(ZH_DIR, "lang")
                os.makedirs(settings["target_dir"], exist_ok=True); break
            elif fb == 'q': return 'q'

def first_run_wizard():
    print_header(); print("\n"*4 + center(YELLOW + t("wiz_title") + RESET))
    print(center(CYAN + "Welcome! Let's set up the basics." + RESET)); time.sleep(2)
    
    opts = ["Čeština", "English"]; sel = 0
    while True:
        render_menu(t("wiz_step1"), opts, sel, footer="[W/S] Move | [Enter] Select")
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter']: settings["ui_lang"] = "cz" if sel == 0 else "en"; break

    if flow_select_source() == 'q': pass
    if flow_select_target() == 'q': pass
    
    e_keys = ["combined_free", "google_free", "libre_free", "deepl_api"]
    e_names = ["Doporučená volba (Kombinace Free)", "Google Translate (ZDARMA)", "LibreTranslate (ZDARMA)", "DeepL PRO (API)"]
    sel = 0
    while True:
        render_menu(t("wiz_step4"), e_names, sel)
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(e_names)-1: sel += 1
        elif k in ['d', 'enter']:
            settings["translator_engine"] = e_keys[sel]
            if e_keys[sel] == "deepl_api":
                print_header(); print("\n"*4 + center(YELLOW + t("api_req") + RESET))
                api = safe_input(center(t("inp_esc") + "\n\n" + center("")))
                if api: settings["api_key"] = api.strip()
            break

    exts = [".json", ".txt", ".lang", "Vlastní/Custom"]; sel = 0
    while True:
        render_menu(t("wiz_step5"), exts, sel)
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(exts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 3:
                print_header(); print("\n"*4 + center(YELLOW + t("type_ext") + RESET))
                ex = safe_input(center(t("inp_esc") + "\n\n" + center("")))
                if ex: settings["file_extension"] = ex.strip() if ex.strip().startswith(".") else "." + ex.strip()
            else: settings["file_extension"] = exts[sel]
            break

    opts = [f"{t('yes')} (Vlastní složky/Custom)", f"{t('no')} (Základní složky)"]; sel = 0
    while True:
        render_menu(t("wiz_step6"), opts, sel)
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0:
                print_header(); print("\n"*4 + center(CYAN + t("dlg_log") + RESET)); time.sleep(1)
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); p1 = filedialog.askdirectory(title=t("dlg_log")); root.destroy()
                if p1: settings["log_dir"] = p1
                
                print_header(); print("\n"*4 + center(CYAN + t("dlg_bak") + RESET)); time.sleep(1)
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); p2 = filedialog.askdirectory(title=t("dlg_bak")); root.destroy()
                if p2: settings["backup_dir"] = p2
            break
    save_settings()

def engine_select_sub():
    from .main import settings_menu # Avoid circular if possible, but safe here
    sel = 0
    engines = {"combined_free": "Doporučená (Kombinace všech Free)", "google_free": "Google Translate (ZDARMA)", "libre_free": "LibreTranslate (ZDARMA)", "deepl_api": "DeepL PRO (API)"}
    while True:
        opts = [f"Motor: {engines[settings['translator_engine']]}", f"API Klíč: {settings['api_key'][:5] + '...' if len(settings['api_key'])>5 else 'NENASTAVENO'}"]
        render_menu("PŘEKLADAČ A API", opts, sel)
        k = read_key()
        save_settings()
        if k in ['a', 'esc']: return
        elif k == 'q': return 'q'
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0:
                e_keys = list(engines.keys()); e_s = 0
                while True:
                    e_opts = [f"{'✅' if e == settings['translator_engine'] else '☐'} {engines[e]}" for e in e_keys]
                    render_menu("VÝBĚR MOTORU", e_opts, e_s)
                    ek = read_key()
                    if ek in ['a', 'esc']: break
                    elif ek == 'q': return 'q'
                    elif ek == 'w' and e_s > 0: e_s -= 1
                    elif ek == 's' and e_s < len(e_opts)-1: e_s += 1
                    elif ek in ['d', 'enter']: settings["translator_engine"] = e_keys[e_s]; break
            elif sel == 1:
                print_header(); print("\n"*4 + center(t("api_req")))
                api = safe_input(center(t("inp_esc") + "\n\n" + center("")))
                if api is not None and api.strip(): settings["api_key"] = api.strip()

def translate_single_key(filepath, f_type, data, target_key, orig_text):
    sel_o = 0; opts_o = [t("f_config"), t("f_new")]
    while True:
        render_menu(t("folder_q"), opts_o, sel_o)
        k = read_key(allow_esc_exit=False)
        if k in ['a', 'esc', 'q']: return 'cancel'
        elif k == 'w' and sel_o > 0: sel_o -= 1
        elif k == 's' and sel_o < 1: sel_o += 1
        elif k in ['d', 'enter']:
            if sel_o == 0: t_dir = settings["target_dir"]
            else:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); p = filedialog.askdirectory(title=t("dlg_tgt")); root.destroy()
                if not p: return 'cancel'
                t_dir = p
            break
            
    sel_a = 0; action_opts = [t("act1"), t("act2"), t("act3"), t("act4")]
    while True:
        print_header(); print(YELLOW + center(t("choose_act")) + RESET + "\n")
        print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
        print(center(CYAN + "│" + RESET + center("KLÍČ: " + str(target_key), 90) + CYAN + "│" + RESET))
        print(center(CYAN + "├" + "─"*90 + "┤" + RESET))
        wrapped = textwrap.wrap(orig_text, width=86)
        for line in wrapped: print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
        print(center(CYAN + "└" + "─"*90 + "┘" + RESET) + "\n")
        for i, opt in enumerate(action_opts):
            if i == sel_a: print(GREEN + center(f" ►►  {opt}  ◄◄ ") + RESET)
            else: print(CYAN + center(f"     {opt}     ") + RESET)
        print("\n" + "═"*CONSOLE_WIDTH + "\n" + YELLOW + center(t("footer")) + RESET)
        
        ak = read_key()
        if ak in ['a', 'esc', 'q']: return 'cancel'
        elif ak == 'w' and sel_a > 0: sel_a -= 1
        elif ak == 's' and sel_a < len(action_opts)-1: sel_a += 1
        elif ak in ['d', 'enter']:
            langs_to_process = settings["selected_langs"].copy()
            if sel_a == 1 or sel_a == 3:
                l_opts = [SUPPORTED_LANGS[x] for x in settings["selected_langs"]]
                if not l_opts: break
                ls_idx = 0
                while True:
                    render_menu(t("sel_lang"), l_opts, ls_idx)
                    lk = read_key()
                    if lk in ['a', 'esc', 'q']: break
                    elif lk == 'w' and ls_idx > 0: ls_idx -= 1
                    elif lk == 's' and ls_idx < len(l_opts)-1: ls_idx += 1
                    elif lk in ['d', 'enter']: langs_to_process = [settings["selected_langs"][ls_idx]]; break
                if lk in ['a', 'esc']: continue

            for lang in langs_to_process:
                curr_t_dir = os.path.join(t_dir, lang); os.makedirs(curr_t_dir, exist_ok=True)
                target_file = os.path.join(curr_t_dir, os.path.basename(filepath))
                if os.path.exists(target_file):
                    try: t_data, _, _ = parse_file_for_translation(target_file)
                    except: t_data = data.copy() if f_type == "json" else list(data)
                else: t_data = data.copy() if f_type == "json" else list(data)

                if sel_a == 0 or sel_a == 1: 
                    try: translated = translate_text_safe(orig_text, lang, settings["translator_engine"], settings["api_key"], settings["source_lang"])
                    except Exception as e: print_header(); print("\n"*4 + RED + center(f"{t('err_trans')}: {e}") + RESET); time.sleep(3); continue
                    final_res = apply_prefix(translated)
                    print_header(); print("\n" + center(YELLOW + f"{t('auto_res')} ({lang.upper()})" + RESET) + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                    for line in textwrap.wrap(final_res, width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                    print(center(CYAN + "└" + "─"*90 + "┘" + RESET)); print("\n" + center(GREEN + t("cfm_save") + RESET + " | " + RED + t("cfm_discard") + RESET))
                    cfm = read_key(allow_esc_exit=False)
                    if cfm not in ['d', 'enter', 'space']: continue
                    if f_type == "json": t_data[target_key] = final_res
                    else: t_data[target_key] = final_res
                    
                elif sel_a == 2 or sel_a == 3: 
                    print_header(); print("\n" + center(YELLOW + f"VLASTNÍ PŘEKLAD PRO: {lang.upper()}" + RESET) + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                    print(center(CYAN + "│" + RESET + center(t("orig_t"), 90) + CYAN + "│" + RESET)); print(center(CYAN + "├" + "─"*90 + "┤" + RESET))
                    for line in textwrap.wrap(orig_text, width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                    print(center(CYAN + "└" + "─"*90 + "┘" + RESET))
                    custom_t = safe_input("\n" + center(t("inp_esc") + "\n\n" + center(t("new_t") + " ")))
                    if custom_t is None: continue
                    final_res = apply_prefix(custom_t.strip() if custom_t.strip() else orig_text)
                    print_header(); print("\n" + center(YELLOW + f"{t('auto_res')} ({lang.upper()})" + RESET) + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                    for line in textwrap.wrap(final_res, width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                    print(center(CYAN + "└" + "─"*90 + "┘" + RESET)); print("\n" + center(GREEN + t("cfm_save") + RESET + " | " + RED + t("cfm_discard") + RESET))
                    cfm = read_key(allow_esc_exit=False)
                    if cfm not in ['d', 'enter', 'space']: continue
                    if f_type == "json": t_data[target_key] = final_res
                    else: t_data[target_key] = final_res

                if settings["auto_backup"] and os.path.exists(target_file):
                    os.makedirs(settings["backup_dir"], exist_ok=True); shutil.copy(target_file, os.path.join(settings["backup_dir"], get_backup_name(os.path.basename(filepath))))
                with open(target_file, 'w', encoding='utf-8') as f:
                    if f_type == "json": json.dump(t_data, f, indent=2, ensure_ascii=False)
                    else: f.write('\n'.join(t_data))
            
            write_log(f"Detailní překlad - Klíč: {target_key} do {langs_to_process}")
            print_header(); print("\n"*4 + GREEN + center(t("done")) + RESET); time.sleep(2); return 'done'

def view_file_contents(filepath):
    sel = 0
    while True:
        try: data, keys, f_type = parse_file_for_translation(filepath)
        except: return
        items = [f"🔑 {k}: {data[k]}" if f_type == "json" else f"L{k}: {data[k]}" for k in keys]
        if not items: items = [t("empty_file")]
        
        display_opts = [textwrap.shorten(item, width=80) for item in items]
        render_menu(f"SOUBOR: {os.path.basename(filepath)}", display_opts, sel, footer=t("v_close"))
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(display_opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if items[0] == t("empty_file"): continue
            print_header(); print(YELLOW + center(f"{t('detail')} {keys[sel] if f_type=='json' else sel}") + RESET + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
            full_text = str(data[keys[sel]] if f_type=='json' else data[sel])
            for line in textwrap.wrap(full_text, width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
            print(center(CYAN + "└" + "─"*90 + "┘" + RESET)); print("\n" + center(t("v_close")))
            while True:
                rk = read_key()
                if rk in ['a', 'esc', 'd', 'enter', 'q']: break
                if rk == 't': translate_single_key(filepath, f_type, data, keys[sel] if f_type=='json' else sel, full_text); break
        elif k == 't':
            if items[0] == t("empty_file"): continue
            full_text = str(data[keys[sel]] if f_type=='json' else data[sel])
            translate_single_key(filepath, f_type, data, keys[sel] if f_type=='json' else sel, full_text)

def interactive_folders():
    sel = 0
    while True:
        t_dir = settings["target_dir"]
        if not os.path.exists(t_dir) or not os.listdir(t_dir):
            print_header(); print("\n"*4 + YELLOW + center(t("no_folders")) + RESET); time.sleep(2); return
        folders = sorted([d for d in os.listdir(t_dir) if os.path.isdir(os.path.join(t_dir, d))])
        if not folders: print_header(); print("\n"*4 + YELLOW + center(t("no_folders")) + RESET); time.sleep(2); return
        render_menu(t("m_folders"), [f"📁 {f}" for f in folders], sel)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(folders)-1: sel += 1
        elif k in ['d', 'enter']:
            f_sel = 0; selected_f = folders[sel]; f_path = os.path.join(t_dir, selected_f)
            while True:
                files = sorted([fi for fi in os.listdir(f_path) if os.path.isfile(os.path.join(f_path, fi))])
                f_opts = [f"📄 {fi}" for fi in files] if files else [t("empty_file")]
                render_menu(f"SLOŽKA: {selected_f.upper()}", f_opts, f_sel)
                fk = read_key()
                if fk in ['a', 'esc']: break
                elif fk == 'q': return 'q'
                elif fk == 'w' and f_sel > 0: f_sel -= 1
                elif fk == 's' and f_sel < len(f_opts)-1: f_sel += 1
                elif fk in ['d', 'enter'] and files: view_file_contents(os.path.join(f_path, files[f_sel]))

def selective_translation():
    sel_o = 0; opts_o = [t("sel_src_def"), t("sel_src_new")]
    while True:
        render_menu(t("sel_src_q"), opts_o, sel_o)
        k = read_key(allow_esc_exit=False)
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel_o > 0: sel_o -= 1
        elif k == 's' and sel_o < 1: sel_o += 1
        elif k in ['d', 'enter']:
            if sel_o == 0: s_dir, s_lang = settings["source_dir"], settings["source_lang"]
            else:
                root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True); p = filedialog.askdirectory(title=t("dlg_src")); root.destroy()
                if not p: return
                s_dir = p
                l_codes = ["en", "cs", "de", "ru", "es", "fr", "it", "nl", "pl", "pt", "tr", "zh", "ja", "ko", "uk", "ro"]; l_s = 0
                while True:
                    l_opts = [SUPPORTED_LANGS[x] for x in l_codes]
                    render_menu(t("tgt_lang_q"), l_opts, l_s)
                    lk = read_key(allow_esc_exit=False)
                    if lk in ['a', 'q', 'esc']: return
                    elif lk == 'w' and l_s > 0: l_s -= 1
                    elif lk == 's' and l_s < len(l_opts)-1: l_s += 1
                    elif lk in ['d', 'enter']: s_lang = l_codes[l_s]; break
            break

    if not os.path.exists(s_dir): print_header(); print("\n"*4 + RED + center(t("src_not_exist")) + RESET); time.sleep(2); return
    files = [f for f in os.listdir(s_dir) if f.endswith(settings["file_extension"])]
    if not files: print_header(); print("\n"*4 + RED + center(t("no_files")) + RESET); time.sleep(2); return
    
    print_header(); print("\n"*4 + center(YELLOW + "🎯 SELEKTIVNÍ PŘEKLÁDÁNÍ 🎯" + RESET)); print(center(CYAN + t("search_phrase") + RESET))
    phrase = safe_input("\n" + center(t("inp_esc") + "\n\n" + center("")))
    if not phrase: return
    phrase = phrase.strip().lower()

    flat_matches = []
    for f_name in files:
        try:
            data, keys, f_type = parse_file_for_translation(os.path.join(s_dir, f_name))
            for k in keys:
                val = str(data[k])
                if phrase in re.sub(r'<[^>]+>', '', val).lower(): flat_matches.append({"file": f_name, "key": k, "text": val, "f_type": f_type, "data": data})
        except: pass

    if not flat_matches: print_header(); print("\n"*4 + RED + center(t("no_phrase")) + RESET); time.sleep(2); return

    sel = 0
    while True:
        opts = []
        for m in flat_matches:
            wrapped_str = "\n".join([f"    {GRAY}{l}{RESET}" for l in textwrap.wrap(str(m['text']), width=70)])
            opts.append(f"📄 {m['file']} | 🔑 {str(m['key'])}\n{wrapped_str}\n")
        
        print_header(); print(YELLOW + center(t("search_res")) + RESET + "\n")
        max_v = 4; start = max(0, sel - max_v // 2); end = min(len(opts), start + max_v)
        if end - start < max_v: start = max(0, end - max_v)
        for i in range(start, end):
            if i == sel: print(GREEN + center(f" ►► {opts[i].split(chr(10))[0]} ◄◄ ") + RESET + "\n" + "\n".join(opts[i].split(chr(10))[1:]))
            else: print(CYAN + center(f"    {opts[i].split(chr(10))[0]}    ") + RESET + "\n" + "\n".join(opts[i].split(chr(10))[1:]))
        print("═"*CONSOLE_WIDTH + "\n" + YELLOW + center(t("footer")) + RESET)

        k = read_key()
        if k in ['a', 'esc']: return
        elif k == 'q': return 'q'
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            selected = flat_matches[sel]
            sel_a = 0; action_opts = [t("act1"), t("act2"), t("act3"), t("act4")]
            while True:
                print_header(); print(YELLOW + center(t("choose_act")) + RESET + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                print(center(CYAN + "│" + RESET + center("KLÍČ: " + str(selected["key"]), 90) + CYAN + "│" + RESET)); print(center(CYAN + "├" + "─"*90 + "┤" + RESET))
                for line in textwrap.wrap(str(selected["text"]), width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                print(center(CYAN + "└" + "─"*90 + "┘" + RESET) + "\n")
                for i, opt in enumerate(action_opts):
                    if i == sel_a: print(GREEN + center(f" ►►  {opt}  ◄◄ ") + RESET)
                    else: print(CYAN + center(f"     {opt}     ") + RESET)
                print("\n" + "═"*CONSOLE_WIDTH + "\n" + YELLOW + center(t("footer")) + RESET)
                ak = read_key()
                if ak in ['a', 'esc']: break
                if ak == 'q': return 'q'
                elif ak == 'w' and sel_a > 0: sel_a -= 1
                elif ak == 's' and sel_a < len(action_opts)-1: sel_a += 1
                elif ak in ['d', 'enter']:
                    langs_to_process = settings["selected_langs"].copy()
                    if sel_a == 1 or sel_a == 3:
                        l_opts = [SUPPORTED_LANGS[x] for x in settings["selected_langs"]]
                        if not l_opts: break
                        ls_idx = 0
                        while True:
                            render_menu(t("sel_lang"), l_opts, ls_idx)
                            lk = read_key()
                            if lk in ['a', 'esc', 'q']: break
                            elif lk == 'w' and ls_idx > 0: ls_idx -= 1
                            elif lk == 's' and ls_idx < len(l_opts)-1: ls_idx += 1
                            elif lk in ['d', 'enter']: langs_to_process = [settings["selected_langs"][ls_idx]]; break
                        if lk in ['a', 'esc']: continue

                    for lang in langs_to_process:
                        t_dir = os.path.join(settings["target_dir"], lang); os.makedirs(t_dir, exist_ok=True)
                        target_file = os.path.join(t_dir, selected["file"])
                        if os.path.exists(target_file):
                            try: t_data, _, _ = parse_file_for_translation(target_file)
                            except: t_data = selected["data"].copy() if selected["f_type"] == "json" else list(selected["data"])
                        else: t_data = selected["data"].copy() if selected["f_type"] == "json" else list(selected["data"])

                        if sel_a == 0 or sel_a == 1: 
                            try: translated = translate_text_safe(str(selected["text"]), lang, settings["translator_engine"], settings["api_key"], s_lang)
                            except Exception as e: print_header(); print("\n"*4 + RED + center(f"{t('err_trans')}: {e}") + RESET); time.sleep(3); continue
                            final_res = apply_prefix(translated)
                            print_header(); print("\n" + center(YELLOW + f"{t('auto_res')} ({lang.upper()})" + RESET) + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                            for line in textwrap.wrap(final_res, width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                            print(center(CYAN + "└" + "─"*90 + "┘" + RESET)); print("\n" + center(GREEN + t("cfm_save") + RESET + " | " + RED + t("cfm_discard") + RESET))
                            cfm = read_key(allow_esc_exit=False)
                            if cfm not in ['d', 'enter', 'space']: continue
                            if selected["f_type"] == "json": t_data[selected["key"]] = final_res
                            else: t_data[selected["key"]] = final_res
                        elif sel_a == 2 or sel_a == 3: 
                            print_header(); print("\n" + center(YELLOW + f"VLASTNÍ PŘEKLAD PRO: {lang.upper()}" + RESET) + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                            print(center(CYAN + "│" + RESET + center(t("orig_t"), 90) + CYAN + "│" + RESET)); print(center(CYAN + "├" + "─"*90 + "┤" + RESET))
                            for line in textwrap.wrap(str(selected["text"]), width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                            print(center(CYAN + "└" + "─"*90 + "┘" + RESET))
                            custom_t = safe_input("\n" + center(t("inp_esc") + "\n\n" + center(t("new_t") + " ")))
                            if custom_t is None: continue
                            final_res = apply_prefix(custom_t.strip() if custom_t.strip() else str(selected["text"]))
                            print_header(); print("\n" + center(YELLOW + f"{t('auto_res')} ({lang.upper()})" + RESET) + "\n"); print(center(CYAN + "┌" + "─"*90 + "┐" + RESET))
                            for line in textwrap.wrap(final_res, width=86): print(center(f"{CYAN}│{RESET}  {line.ljust(86)}  {CYAN}│{RESET}"))
                            print(center(CYAN + "└" + "─"*90 + "┘" + RESET)); print("\n" + center(GREEN + t("cfm_save") + RESET + " | " + RED + t("cfm_discard") + RESET))
                            cfm = read_key(allow_esc_exit=False)
                            if cfm not in ['d', 'enter', 'space']: continue
                            if selected["f_type"] == "json": t_data[selected["key"]] = final_res
                            else: t_data[selected["key"]] = final_res

                        if settings["auto_backup"] and os.path.exists(target_file):
                            os.makedirs(settings["backup_dir"], exist_ok=True); shutil.copy(target_file, os.path.join(settings["backup_dir"], get_backup_name(selected["file"])))
                        with open(target_file, 'w', encoding='utf-8') as f:
                            if selected["f_type"] == "json": json.dump(t_data, f, indent=2, ensure_ascii=False)
                            else: f.write('\n'.join(t_data))
                    write_log(f"Selektivní překlad - Klíč: {selected['key']} do {langs_to_process}")
                    print_header(); print("\n"*4 + GREEN + center(t("done")) + RESET); time.sleep(2); return 'q'

def run_translation():
    try:
        if not os.path.exists(settings["source_dir"]): print_header(); print("\n"*4 + RED + center(t("src_not_exist")) + RESET); time.sleep(2); return
        ext = settings["file_extension"]; files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(ext)]
        if not files: print_header(); print("\n"*4 + RED + center(t("no_files")) + RESET); time.sleep(2); return

        total_keys = 0; file_data = {}
        for f_name in files:
            try: data, keys, f_type = parse_file_for_translation(os.path.join(settings["source_dir"], f_name)); file_data[f_name] = (data, keys, f_type); total_keys += len(keys)
            except: pass
        
        total_ops = total_keys * len(settings["selected_langs"])
        engine_map = {"combined_free": "Doporučená (Kombinace)", "google_free": "Google (ZDARMA)", "libre_free": "LibreTranslate (ZDARMA)", "deepl_api": "DeepL PRO"}
        langs_str = ", ".join(settings['selected_langs']); wrapped_langs = textwrap.wrap(langs_str, width=65)
        est_time = format_time(total_ops * settings["write_speed"] + (total_ops * 0.1))
        
        print_header(); print(YELLOW + center(t("confirm")) + RESET); print(center(CYAN + f"┌{'─'*88}┐" + RESET))
        print(box_left(f"CÍLOVÉ JAZYKY: {wrapped_langs[0]}", f"{PURPLE}CÍLOVÉ JAZYKY:{RESET} {GREEN}{wrapped_langs[0]}{RESET}", 88))
        for line in wrapped_langs[1:]: print(box_left(f"               {line}", f"               {GREEN}{line}{RESET}", 88))
        draw_box_line(f"{PURPLE}ODHAD ČASU:{RESET} ~{est_time} | {PURPLE}SOUBORY:{RESET} {len(files)} ({ext}) | {PURPLE}KLÍČE:{RESET} {total_ops}", f"ODHAD ČASU: ~{est_time} | SOUBORY: {len(files)} ({ext}) | KLÍČE: {total_ops}", 88)
        draw_box_line(f"{PURPLE}NASTAVENÍ:{RESET} Prefix: {'ZAP' if settings['prefix_enabled'] else 'VYP'}, Cache: {'ZAP' if settings['smart_cache'] else 'VYP'}, Zálohy: {'ZAP' if settings['auto_backup'] else 'VYP'}", f"NASTAVENÍ: Prefix: {'ZAP' if settings['prefix_enabled'] else 'VYP'}, Cache: {'ZAP' if settings['smart_cache'] else 'VYP'}, Zálohy: {'ZAP' if settings['auto_backup'] else 'VYP'}", 88)
        draw_box_line(f"{PURPLE}PŘEKLADAČ:{RESET} {GREEN}{engine_map[settings['translator_engine']]}{RESET}", f"PŘEKLADAČ: {engine_map[settings['translator_engine']]}", 88)
        print(center(CYAN + f"└{'─'*88}┘" + RESET) + "\n"); print(center(GREEN + "➤ [D/Enter] Potvrdit a spustit" + RESET + " | " + RED + "➤ [A/Esc] Zrušit" + RESET))
        
        k = read_key()
        if k not in ['d', 'enter']: return

        if settings["translator_engine"] == "deepl_api" and not settings["api_key"]:
            print_header(); print("\n"*4 + RED + center("CHYBA: Není nastaven DeepL API klíč v Nastavení!") + RESET); time.sleep(3); return

        write_log(f"--- HROMADNÝ PŘEKLAD --- Zdroj: {settings['source_dir']} | Jazyky: {settings['selected_langs']} | Engine: {settings['translator_engine']}")
        prog_win = ProgressWindow()
        prog_win.start("ZeddiHub Translator - Translation Progress")
        
        done_ops = 0; start_t = time.time(); paused_t = 0; print_header() 
        
        for lang in settings["selected_langs"]:
            t_dir = os.path.join(settings["target_dir"], lang); os.makedirs(t_dir, exist_ok=True)
            prog_win.log(f"\n{'='*60}\n🌍 STARTING LANGUAGE: {lang.upper()}\n{'='*60}")
            lang_done = 0
            for f_idx, f_name in enumerate(files):
                if f_name not in file_data: continue
                data, keys, f_type = file_data[f_name]
                if not keys: continue
                new_data = data.copy() if f_type == "json" else list(data); file_done = 0
                for k_j in keys:
                    original_text = str(data[k_j]) if f_type == "json" else str(data[k_j])
                    translated = original_text
                    if not (lang.lower() == settings["source_lang"].lower() and os.path.abspath(settings["source_dir"]) == os.path.abspath(settings["target_dir"])):
                        while True:
                            try:
                                translated = translate_text_safe(original_text, lang, settings["translator_engine"], settings["api_key"], settings["source_lang"])
                                write_log(f"[{f_name} | {lang}] {k_j}: {original_text} -> {translated}"); break 
                            except Exception as trans_e:
                                if "Quota" in str(trans_e): print_header(); print("\n"*4 + RED + center("❌ API KVÓTA DEEPL VYČERPÁNA! ❌") + RESET); time.sleep(4); prog_win.close(); return
                                if "API_RATE_LIMIT" in str(trans_e) or "Google API Error" in str(trans_e) or "Network" in str(trans_e):
                                    print_header(); print("\n"*4 + RED + center(t("conn_lost")) + RESET); time.sleep(5); print_header(); continue
                                write_log(f"CHYBA PŘEKLADU ({lang} / {k_j}): {trans_e}")
                                act = error_prompt(trans_e, lang, k_j, original_text)
                                if act == 'retry': continue
                                elif act == 'change': 
                                    if engine_select_sub() == 'q': prog_win.close(); return
                                    continue
                                elif act == 'skip': translated = ""; break
                                elif act == 'abort': write_log("Překlad přerušen po chybě."); prog_win.close(); return

                    final_txt = apply_prefix(translated)
                    if f_type == "json": new_data[k_j] = final_txt
                    else: new_data[k_j] = final_txt
                    
                    done_ops += 1; lang_done += 1; file_done += 1
                    prog_win.log(f"[{lang.upper()}] {str(k_j)[:15]} -> {translated}")
                    
                    elapsed = time.time() - start_t - paused_t
                    eta = (elapsed / done_ops) * (total_ops - done_ops) if done_ops > 0 else 0
                    draw_progress(done_ops, total_ops, lang_done, total_keys, file_done, len(keys), elapsed, eta, lang, f_idx+1, len(files), f_name)
                    time.sleep(settings["write_speed"])
                    
                    if msvcrt.kbhit():
                        key_bytes = msvcrt.getch()
                        if key_bytes == b'\x1b':
                            print_header(); print("\n"*5 + center(RED + t("abort") + RESET)); time.sleep(2); prog_win.close(); return
                        elif key_bytes in [b'a', b'A', b'p', b'P']:
                            ps_start = time.time()
                            if pause_menu() == "abort": prog_win.close(); return
                            paused_t += (time.time() - ps_start); print_header()

                target_file = os.path.join(t_dir, f_name)
                if settings["auto_backup"] and os.path.exists(target_file): os.makedirs(settings["backup_dir"], exist_ok=True); shutil.copy(target_file, os.path.join(settings["backup_dir"], get_backup_name(f_name)))
                with open(target_file, 'w', encoding='utf-8') as f:
                    if f_type == "json": json.dump(new_data, f, indent=2, ensure_ascii=False)
                    else: f.write('\n'.join(new_data))
                prog_win.log(f"✅ ULOŽENO: {f_name}")

        write_log("--- PŘEKLAD ÚSPĚŠNĚ DOKONČEN ---")
        if winsound: winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        prog_win.log("\n" + "="*60 + "\n✅ PROCES DOKONČEN! Log zůstane otevřený.\n" + "="*60)
        prog_win.bring_to_front()
        do_post_action()
        print_header(); print("\n"*4 + center(GREEN + t("done") + RESET)); print(center(GREEN + "[Enter / D] Návrat do Menu" + RESET))
        while read_key(allow_esc_exit=False) not in ['d', 'enter', 'space', 'esc', 'a', 'q']: pass

    except Exception as e:
        try: prog_win.close()
        except: pass
        handle_crash(e)

def translation_stats():
    """Show statistics about source and translated files."""
    source = settings.get("source_dir", "")
    target = settings.get("target_dir", "")
    ext = settings.get("file_extension", ".json")

    if not source or not os.path.isdir(source):
        print_header()
        print("\n" * 4 + RED + center("Zdrojová složka není nastavena!") + RESET)
        time.sleep(2)
        return

    # Count source files and keys
    src_files = [f for f in os.listdir(source) if f.endswith(ext)]
    total_src_keys = 0
    for fname in src_files:
        try:
            with open(os.path.join(source, fname), "r", encoding="utf-8") as f:
                if ext == ".json":
                    data = json.load(f)
                    total_src_keys += len(data) if isinstance(data, dict) else 0
                else:
                    total_src_keys += sum(1 for line in f if line.strip() and not line.strip().startswith("//"))
        except Exception:
            pass

    # Count translated files per language
    lang_stats = {}
    if os.path.isdir(target):
        for lang_dir in os.listdir(target):
            lang_path = os.path.join(target, lang_dir)
            if os.path.isdir(lang_path) and lang_dir in SUPPORTED_LANGS:
                files = [f for f in os.listdir(lang_path) if f.endswith(ext)]
                keys = 0
                for fname in files:
                    try:
                        with open(os.path.join(lang_path, fname), "r", encoding="utf-8") as f:
                            if ext == ".json":
                                data = json.load(f)
                                keys += len(data) if isinstance(data, dict) else 0
                            else:
                                keys += sum(1 for line in f if line.strip() and not line.strip().startswith("//"))
                    except Exception:
                        pass
                lang_stats[lang_dir] = {"files": len(files), "keys": keys}

    # Count backups
    backup_count = 0
    backup_dir = settings.get("backup_dir", "")
    if os.path.isdir(backup_dir):
        backup_count = len([f for f in os.listdir(backup_dir) if f.endswith('.bak')])

    # Display
    while True:
        opts = [
            f"Zdrojové soubory: {len(src_files)}",
            f"Zdrojové klíče: {total_src_keys}",
            f"Přeložených jazyků: {len(lang_stats)}",
            ""
        ]
        descs = [
            f"Formát: {ext}",
            f"Složka: {os.path.basename(source)}",
            f"Složka: {os.path.basename(target)}" if target else "---",
            ""
        ]

        for lang_code, stats in sorted(lang_stats.items()):
            lang_name = SUPPORTED_LANGS.get(lang_code, lang_code)
            pct = int((stats["keys"] / total_src_keys * 100)) if total_src_keys > 0 else 0
            bar_len = 20
            filled = int(bar_len * pct / 100)
            bar = GREEN + "█" * filled + GRAY + "░" * (bar_len - filled) + RESET
            opts.append(f"{lang_name:<20} {bar} {pct}%  ({stats['keys']}/{total_src_keys})")
            descs.append(f"{stats['files']} souborů")

        opts.append("")
        opts.append(f"Zálohy: {backup_count} souborů")

        render_menu("STATISTIKY PŘEKLADU" if settings["ui_lang"] == "cz" else "TRANSLATION STATS",
                     opts, 0, descs,
                     footer="[A/Esc] Zpět" if settings["ui_lang"] == "cz" else "[A/Esc] Back")
        k = read_key()
        if k in ['a', 'esc', 'q']: return


def batch_export():
    """Export all translations into a single combined file for review."""
    target = settings.get("target_dir", "")
    ext = settings.get("file_extension", ".json")

    if not target or not os.path.isdir(target):
        print_header()
        print("\n" * 4 + RED + center("Cílová složka není nastavena!") + RESET)
        time.sleep(2)
        return

    # Find all language directories
    lang_dirs = []
    for d in os.listdir(target):
        dp = os.path.join(target, d)
        if os.path.isdir(dp) and d in SUPPORTED_LANGS:
            lang_dirs.append(d)

    if not lang_dirs:
        print_header()
        print("\n" * 4 + RED + center("Nebyly nalezeny žádné přeložené složky!") + RESET)
        time.sleep(2)
        return

    # Choose export format
    sel = 0
    formats = ["TXT (čitelný přehled)", "JSON (strukturovaný export)", "CSV (tabulkový export)"]
    while True:
        render_menu("FORMÁT EXPORTU" if settings["ui_lang"] == "cz" else "EXPORT FORMAT",
                     formats, sel,
                     footer="[W/S] Pohyb | [Enter] Exportovat | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(formats) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            break

    print_header()
    print("\n" * 4 + CYAN + center("Exportuji překlady...") + RESET)

    export_data = {}
    for lang_code in sorted(lang_dirs):
        lang_path = os.path.join(target, lang_code)
        export_data[lang_code] = {}
        for fname in os.listdir(lang_path):
            if fname.endswith(ext):
                fpath = os.path.join(lang_path, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        if ext == ".json":
                            data = json.load(f)
                            if isinstance(data, dict):
                                export_data[lang_code][fname] = data
                        else:
                            export_data[lang_code][fname] = f.read()
                except Exception:
                    pass

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    if sel == 0:
        # TXT export
        export_path = os.path.join(target, f"export_all_{timestamp}.txt")
        with open(export_path, "w", encoding="utf-8") as f:
            f.write("ZeddiHub Translation Export\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            for lang_code, files in export_data.items():
                lang_name = SUPPORTED_LANGS.get(lang_code, lang_code)
                f.write(f"\n{'=' * 60}\n")
                f.write(f"LANGUAGE: {lang_name} ({lang_code})\n")
                f.write(f"{'=' * 60}\n\n")
                for fname, data in files.items():
                    f.write(f"--- {fname} ---\n")
                    if isinstance(data, dict):
                        for k, v in data.items():
                            f.write(f"  {k}: {v}\n")
                    else:
                        f.write(data + "\n")
                    f.write("\n")

    elif sel == 1:
        # JSON export
        export_path = os.path.join(target, f"export_all_{timestamp}.json")
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    elif sel == 2:
        # CSV export
        export_path = os.path.join(target, f"export_all_{timestamp}.csv")
        with open(export_path, "w", encoding="utf-8") as f:
            f.write("language,file,key,value\n")
            for lang_code, files in export_data.items():
                for fname, data in files.items():
                    if isinstance(data, dict):
                        for k, v in data.items():
                            v_clean = str(v).replace('"', '""')
                            f.write(f'{lang_code},{fname},"{k}","{v_clean}"\n')

    print_header()
    print("\n" * 4 + GREEN + center("Export úspěšně dokončen!") + RESET)
    print(WHITE + center(os.path.basename(export_path)) + RESET)
    time.sleep(2)
    if settings.get("open_folder_after", True) and platform.system() == "Windows":
        try: os.startfile(target)
        except Exception: pass


def handle_crash(e):
    write_log(f"CRASH: {e}")
    opts = [t("err_m"), t("err_e"), t("err_r")]; sel = 0
    while True:
        print_header()
        print("\n"*2 + RED + center(t("err_title")) + RESET)
        print(center(str(e)))
        print("\n" + GRAY)
        for line in traceback.format_exc().splitlines(): print(center(line[:90]))
        print(RESET + "\n")
        for i, opt in enumerate(opts):
            if i == sel: print(GREEN + center(f" ►►  {opt}  ◄◄ ") + RESET)
            else: print(CYAN + center(f"     {opt}     ") + RESET)
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: return "menu"
            elif sel == 1: return "exit"
            elif sel == 2: return "reset"