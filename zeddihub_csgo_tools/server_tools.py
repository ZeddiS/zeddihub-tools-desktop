import os
import re
import time
import shutil
import platform
import json
import tkinter as tk
from tkinter import filedialog
from .core import *

def parse_databases_cfg(content):
    databases = {}
    lines = content.splitlines()
    in_db_block = False
    current_db = None
    
    for line in lines:
        line_clean = line.strip()
        if line_clean.startswith("//") or not line_clean:
            continue
        
        if '"Databases"' in line_clean:
            in_db_block = True
            continue
            
        if in_db_block:
            m_key_val = re.findall(r'"([^"]+)"\s*"([^"]*)"', line_clean)
            if m_key_val:
                key, val = m_key_val[0]
                if current_db:
                    databases[current_db][key] = val
                elif key == "driver_default":
                    databases["_driver_default"] = val
                continue
                
            m_key = re.findall(r'^"([^"]+)"$', line_clean)
            if m_key and m_key[0] != "Databases":
                current_db = m_key[0]
                databases[current_db] = {
                    "driver": "default", "host": "", "database": "", "user": "", "pass": "", "port": "3306"
                }
    return databases

def generate_databases_cfg(databases):
    lines = ['"Databases"', '{']
    if "_driver_default" in databases:
        lines.append(f'\t"driver_default"\t\t"{databases["_driver_default"]}"')
        lines.append('')
        
    for db_name, db_data in databases.items():
        if db_name == "_driver_default":
            continue
        lines.append(f'\t"{db_name}"')
        lines.append('\t{')
        
        keys_order = ["driver", "host", "database", "user", "pass", "port"]
        extra_keys = [k for k in db_data.keys() if k not in keys_order]
        
        for k in keys_order + extra_keys:
            if k in db_data:
                v = db_data[k]
                key_str = f'"{k}"'
                lines.append(f'\t\t{key_str.ljust(24)}"{v}"')
                
        lines.append('\t}')
        lines.append('') 
        
    if lines and lines[-1] == '':
        lines.pop()
        
    lines.append('}')
    return "\n".join(lines)

def db_field_editor(databases, db_name):
    c_sel = 0
    while True:
        # Prevent crash if the database was deleted and we somehow return here
        if db_name not in databases:
            return
            
        fields = list(databases[db_name].keys())
        opts_fields = [f"{f.capitalize().ljust(10)}: {databases[db_name][f]}" for f in fields]
        
        is_sqlite = (databases[db_name].get("driver", "").lower() == "sqlite")
        switch_text = "➡️ Přesunout do MySQL seznamu" if is_sqlite else "➡️ Přesunout do SQLite seznamu"
        
        opts_fields.extend(["", switch_text, RED + "🗑️ Smazat tuto databázi" + RESET, GREEN + "🔙 Zpět k seznamu databází" + RESET])
        
        render_menu(f"ÚPRAVA: {db_name} ({'SQLite' if is_sqlite else 'MySQL'})", opts_fields, c_sel, footer="[W/S] Pohyb | [Enter] Upravit pole | [A/Esc] Zpět")
        fk = read_key()
        
        if fk in ['a', 'esc', 'q']:
            break
        elif fk == 'w' and c_sel > 0:
            c_sel -= 1
        elif fk == 's' and c_sel < len(opts_fields)-1:
            c_sel += 1
        elif fk in ['d', 'enter', 'space']:
            if opts_fields[c_sel] == "":
                continue
            elif "Přesunout" in opts_fields[c_sel]:
                databases[db_name]["driver"] = "default" if is_sqlite else "sqlite"
                print_header()
                print("\n"*4 + GREEN + center("✅ Databáze úspěšně přesunuta!") + RESET)
                time.sleep(1)
                break
            elif "Smazat" in opts_fields[c_sel]:
                del databases[db_name]
                break
            elif "Zpět" in opts_fields[c_sel]:
                break
            else:
                field_name = fields[c_sel]
                print_header()
                print("\n"*4 + YELLOW + center(f"ÚPRAVA: {db_name} -> {field_name}") + RESET)
                new_val = safe_input("\n" + center(f"Nová hodnota (nyní '{databases[db_name][field_name]}'): "))
                if new_val is not None:
                    databases[db_name][field_name] = new_val.strip()

def run_database_editor():
    source_file = ""
    sel_start = 0
    while True:
        opts_start = [f"📂 Vybraný soubor: {os.path.basename(source_file) if source_file else 'Prázdné (Klikněte pro výběr)'}"]
        if source_file:
            opts_start.append(GREEN + "👉 Pokračovat k úpravě databází" + RESET)
        
        render_menu("ZDROJOVÝ SOUBOR DATABÁZÍ", opts_start, sel_start)
        k = read_key()
        
        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel_start > 0:
            sel_start -= 1
        elif k == 's' and sel_start < len(opts_start)-1:
            sel_start += 1
        elif k in ['d', 'enter', 'space']:
            if sel_start == 0:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                p = filedialog.askopenfilename(title="Vyberte databases.cfg", filetypes=[("Config Files", "*.cfg"), ("All Files", "*.*")])
                root.destroy()
                if p:
                    source_file = p
            elif sel_start == 1:
                break

    with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    databases = parse_databases_cfg(content)
    if not databases:
        print_header()
        print("\n"*4 + RED + center("V souboru se nepodařilo najít strukturu (blok 'Databases').") + RESET)
        time.sleep(2)
        return
        
    sel = 0
    while True:
        db_keys = [k for k in databases.keys() if k != "_driver_default"]
        mysql_keys = [k for k in db_keys if databases[k].get("driver", "").lower() != "sqlite"]
        sqlite_keys = [k for k in db_keys if databases[k].get("driver", "").lower() == "sqlite"]
        
        opts = [
            f"🐬 MySQL Databáze ({len(mysql_keys)})",
            f"🪶 SQLite Databáze ({len(sqlite_keys)})",
            "",
            "➕ Přidat novou databázi",
            "🔄 Přenos nastavení (Klonování Credentials)",
            "💾 Uložit, opravit formátování a otevřít složku"
        ]
        
        render_menu("EDITOR DATABASES.CFG", opts, sel)
        k = read_key()
        
        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if opts[sel] == "":
                continue
            elif "MySQL Databáze" in opts[sel]:
                m_sel = 0
                while True:
                    mysql_keys = [k for k in databases.keys() if k != "_driver_default" and databases[k].get("driver", "").lower() != "sqlite"]
                    if not mysql_keys:
                        break
                    opts_m = [f"🗄️ {k}" for k in mysql_keys]
                    render_menu("MYSQL DATABÁZE", opts_m, m_sel)
                    mk = read_key()
                    if mk in ['a', 'esc', 'q']:
                        break
                    elif mk == 'w' and m_sel > 0:
                        m_sel -= 1
                    elif mk == 's' and m_sel < len(opts_m)-1:
                        m_sel += 1
                    elif mk in ['d', 'enter', 'space']:
                        db_field_editor(databases, mysql_keys[m_sel])
                        # Safe clamp for index after returning
                        current_len = len([k for k in databases.keys() if k != "_driver_default" and databases[k].get("driver", "").lower() != "sqlite"])
                        if m_sel >= current_len: 
                            m_sel = max(0, current_len - 1)
                            
            elif "SQLite Databáze" in opts[sel]:
                s_sel = 0
                while True:
                    sqlite_keys = [k for k in databases.keys() if k != "_driver_default" and databases[k].get("driver", "").lower() == "sqlite"]
                    if not sqlite_keys:
                        break
                    opts_s = [f"🗄️ {k}" for k in sqlite_keys]
                    render_menu("SQLITE DATABÁZE", opts_s, s_sel)
                    sk = read_key()
                    if sk in ['a', 'esc', 'q']:
                        break
                    elif sk == 'w' and s_sel > 0:
                        s_sel -= 1
                    elif sk == 's' and s_sel < len(opts_s)-1:
                        s_sel += 1
                    elif sk in ['d', 'enter', 'space']:
                        db_field_editor(databases, sqlite_keys[s_sel])
                        # Safe clamp for index after returning
                        current_len = len([k for k in databases.keys() if k != "_driver_default" and databases[k].get("driver", "").lower() == "sqlite"])
                        if s_sel >= current_len: 
                            s_sel = max(0, current_len - 1)
                            
            elif "Přidat novou" in opts[sel]:
                print_header()
                print("\n"*4 + YELLOW + center("PŘIDÁNÍ NOVÉ DATABÁZE") + RESET)
                new_name = safe_input("\n" + center("Zadejte unikátní název (např. sourcebans): "))
                if new_name and new_name.strip() and new_name.strip() not in databases:
                    print_header()
                    print("\n"*4 + CYAN + center(f"Typ databáze pro '{new_name.strip()}'?") + RESET)
                    print("\n" + center("[M] MySQL (Běžná)  |  [S] SQLite (Lokální soubor)"))
                    t_k = read_key(allow_esc_exit=False)
                    driver = "sqlite" if t_k == 's' else "default"
                    databases[new_name.strip()] = {"driver": driver, "host": "", "database": "", "user": "", "pass": "", "port": "3306"}
                    
            elif "Přenos nastavení" in opts[sel]:
                if len(db_keys) < 2:
                    print_header()
                    print("\n"*4 + RED + center("Nemáte dostatek databází pro klonování.") + RESET)
                    time.sleep(2)
                    continue
                    
                c_sel = 0
                while True:
                    render_menu("ZVOLTE ZDROJOVOU DATABÁZI (KOPÍROVAT Z)", [f"🗄️ {k}" for k in db_keys], c_sel)
                    ck = read_key()
                    if ck in ['a', 'esc', 'q']:
                        break
                    elif ck == 'w' and c_sel > 0:
                        c_sel -= 1
                    elif ck == 's' and c_sel < len(db_keys)-1:
                        c_sel += 1
                    elif ck in ['d', 'enter', 'space']:
                        src_db_name = db_keys[c_sel]
                        target_keys = [k for k in db_keys if k != src_db_name]
                        t_flags = multi_select_menu(f"ZVOLTE CÍLOVÉ DATABÁZE PRO PŘEPIS Z '{src_db_name}'", target_keys, [False]*len(target_keys))
                        
                        if t_flags:
                            src_data = databases[src_db_name]
                            for idx, flag in enumerate(t_flags):
                                if flag:
                                    tdb = target_keys[idx]
                                    databases[tdb]["host"] = src_data.get("host", "")
                                    databases[tdb]["database"] = src_data.get("database", "")
                                    databases[tdb]["user"] = src_data.get("user", "")
                                    databases[tdb]["pass"] = src_data.get("pass", "")
                                    databases[tdb]["port"] = src_data.get("port", "3306")
                            print_header()
                            print("\n"*4 + GREEN + center("✅ Údaje úspěšně naklonovány!") + RESET)
                            time.sleep(2)
                        break
                        
            elif "Uložit, opravit" in opts[sel]:
                print_header()
                print("\n"*4 + YELLOW + center("Chcete uložit soubor a zafixovat formátování (zarovnání, mezery)?") + RESET)
                print("\n" + center(GREEN + "[Enter] Uložit a Otevřít" + RESET + " | " + RED + "[Esc] Zpět" + RESET))
                
                sk = read_key(allow_esc_exit=False)
                if sk in ['d', 'enter', 'space']:
                    os.makedirs(settings["target_dir"], exist_ok=True)
                    tgt_file = os.path.join(settings["target_dir"], "databases.cfg")
                    
                    if settings["auto_backup"]:
                        os.makedirs(settings["backup_dir"], exist_ok=True)
                        shutil.copy(source_file, os.path.join(settings["backup_dir"], get_backup_name("databases.cfg")))
                        
                    with open(tgt_file, "w", encoding="utf-8") as f:
                        f.write(generate_databases_cfg(databases))
                        
                    print_header()
                    print("\n"*4 + GREEN + center("✅ Soubor databases.cfg perfektně vygenerován a zarovnán!") + RESET)
                    time.sleep(1.5)
                    if settings.get("open_folder_after") and platform.system() == "Windows":
                        try:
                            os.startfile(settings["target_dir"])
                        except Exception:
                            pass
                    return

def server_cfg_generator():
    cfg = {
        "hostname": "ZeddiHub CS:GO Server",
        "sv_password": "",
        "rcon_password": "changeme",
        "sv_cheats": "0",
        "sv_lan": "0",
        "game_mode": "1",
        "game_type": "0",
        "sv_maxrate": "0",
        "sv_minrate": "128000",
        "sv_mincmdrate": "64",
        "sv_maxcmdrate": "128",
        "sv_minupdaterate": "64",
        "sv_maxupdaterate": "128",
        "mp_autoteambalance": "1",
        "mp_limitteams": "1",
        "mp_friendlyfire": "0",
        "mp_roundtime": "1.92",
        "mp_freezetime": "15",
        "mp_buytime": "20",
        "mp_maxrounds": "30",
        "sv_alltalk": "0",
        "sv_deadtalk": "1",
        "sv_allow_votes": "1",
        "tv_enable": "1",
        "tv_delay": "30"
    }
    categories = {
        "Zakladni": ["hostname", "sv_password", "rcon_password", "sv_cheats", "sv_lan"],
        "Gamemode": ["game_mode", "game_type"],
        "Network": ["sv_maxrate", "sv_minrate", "sv_mincmdrate", "sv_maxcmdrate", "sv_minupdaterate", "sv_maxupdaterate"],
        "Gameplay": ["mp_autoteambalance", "mp_limitteams", "mp_friendlyfire", "mp_roundtime", "mp_freezetime", "mp_buytime", "mp_maxrounds"],
        "Komunikace": ["sv_alltalk", "sv_deadtalk", "sv_allow_votes"],
        "GOTV": ["tv_enable", "tv_delay"]
    }

    sel = 0
    keys = list(cfg.keys())
    while True:
        opts = [f"{k.ljust(28)}: {cfg[k] if cfg[k] else '(prázdné)'}" for k in keys]
        opts.append("")
        opts.append(GREEN + "Uložit do server.cfg" + RESET)
        render_menu("CS:GO SERVER.CFG GENERÁTOR", opts, sel,
                     footer="[W/S] Pohyb | [Enter] Upravit | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if opts[sel] == "": continue
            if "Ulozit" in opts[sel]:
                os.makedirs(settings["target_dir"], exist_ok=True)
                path = os.path.join(settings["target_dir"], "server.cfg")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("// CS:GO Server Config - Generated by ZeddiHub CS:GO Tools\n")
                    f.write("// https://zeddihub.eu\n\n")
                    for cat_name, cat_keys in categories.items():
                        f.write(f"// === {cat_name} ===\n")
                        for ck in cat_keys:
                            if cfg[ck]:
                                if ck in ["hostname", "sv_password", "rcon_password"]:
                                    f.write(f'{ck} "{cfg[ck]}"\n')
                                else:
                                    f.write(f"{ck} {cfg[ck]}\n")
                        f.write("\n")
                    f.write('echo "[ZeddiHub] Server config loaded!"\n')
                print_header()
                print("\n" * 4 + GREEN + center("Soubor server.cfg úspěšně vygenerován!") + RESET)
                time.sleep(2)
                if settings.get("open_folder_after") and platform.system() == "Windows":
                    try: os.startfile(settings["target_dir"])
                    except Exception: pass
                return
            else:
                c_key = keys[sel]
                print_header()
                print("\n" * 4 + YELLOW + center(f"ÚPRAVA: {c_key}") + RESET)
                new_val = safe_input("\n" + center(f"Nová hodnota (nyní '{cfg[c_key]}'): "))
                if new_val is not None:
                    cfg[c_key] = new_val.strip()


def auto_translate_text(text, target_lang="cs"):
    try:
        import urllib.request
        import urllib.parse
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return "".join([t[0] for t in res[0] if t[0]])
    except Exception:
        return None

def run_sourcemod_translator():
    print_header()
    print("\n"*4 + YELLOW + center("SOURCEMOD PŘEKLADAČ FRÁZÍ") + RESET)
    print(center("Vyberte překladový .txt soubor (např. core.phrases.txt)..."))
    time.sleep(1)
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    p = filedialog.askopenfilename(title="Vyberte SourceMod .txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    root.destroy()
    
    if not p:
        return

    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return

    lines = content.splitlines()
    phrases = []
    
    for i, line in enumerate(lines):
        m = re.search(r'^(\s*)"en"\s+"([^"]+)"', line)
        if m:
            phrases.append({
                "line_idx": i, 
                "indent": m.group(1), 
                "text": m.group(2)
            })

    if not phrases:
        print_header()
        print("\n"*4 + RED + center("Nenalezeny žádné 'en' fráze k překladu v tomto formátu.") + RESET)
        time.sleep(2)
        return

    sel = 0
    while True:
        opts = [textwrap.shorten(f"EN: {p['text']}", width=80) for p in phrases]
        render_menu(f"PŘEKLAD: {os.path.basename(p)}", opts, sel, footer="[W/S] Pohyb | [Enter] Přeložit (Vloží 'cz' pod 'en') | [A/Esc] Zpět")
        k = read_key()
        
        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            curr_match = phrases[sel]
            
            t_sel = 0
            while True:
                render_menu("ZVOLTE METODU PŘEKLADU", ["Vlastní překlad (Napsat manuálně)", "Automatický překlad (Google API)", "Zpět"], t_sel)
                tk_key = read_key()
                if tk_key in ['a', 'esc', 'q']: break
                elif tk_key == 'w' and t_sel > 0: t_sel -= 1
                elif tk_key == 's' and t_sel < 2: t_sel += 1
                elif tk_key in ['d', 'enter', 'space']:
                    if t_sel == 0:
                        print_header()
                        print("\n"*4 + YELLOW + center("PŘEKLAD FRÁZE") + RESET)
                        print(center(CYAN + curr_match['text'] + RESET))
                        new_val = safe_input("\n" + center("Zadejte český překlad: "))
                    elif t_sel == 1:
                        print_header()
                        print("\n"*4 + YELLOW + center("KOMUNIKUJI S GOOGLE API...") + RESET)
                        new_val = auto_translate_text(curr_match['text'])
                        if not new_val:
                            print_header()
                            print("\n"*4 + RED + center("Chyba API nebo ztráta připojení.") + RESET)
                            time.sleep(2)
                            break
                    else:
                        break
                        
                    if new_val is not None and new_val.strip() != "":
                        cz_line = f'{curr_match["indent"]}"cz"\t\t\t"{new_val.strip()}"'
                        
                        if curr_match["line_idx"] + 1 < len(lines) and '"cz"' in lines[curr_match["line_idx"] + 1]:
                            lines[curr_match["line_idx"] + 1] = cz_line
                        else:
                            lines.insert(curr_match["line_idx"] + 1, cz_line)
                            for p_update in phrases[sel+1:]:
                                p_update["line_idx"] += 1

                        os.makedirs(settings["target_dir"], exist_ok=True)
                        target = os.path.join(settings["target_dir"], os.path.basename(p))
                        with open(target, "w", encoding="utf-8") as f:
                            f.write("\n".join(lines))
                            
                        print_header()
                        print("\n"*4 + GREEN + center("✅ Přeloženo a uloženo do cílové složky!") + RESET)
                        time.sleep(1)
                    break