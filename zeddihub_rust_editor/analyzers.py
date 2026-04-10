import os
import re
import time
import tempfile
import platform
from .core import *
from .queue_tools import queue_add

def run_command_extractor():
    if not os.path.exists(settings["source_dir"]): return
    files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(".cs")]
    if not files: return
    
    sel_files = multi_select_menu("EXTRAKTOR PŘÍKAZŮ - VÝBĚR", files, [True]*len(files), ["Vyberte pluginy pro nalezení příkazů."]*len(files))
    if not sel_files: return
    
    files_to_check = [files[i] for i in range(len(files)) if sel_files[i]]
    if not files_to_check: return

    chat_reg = re.compile(r'\[ChatCommand\(\s*["\']([^"\']+)["\']\s*\)\]')
    cons_reg = re.compile(r'\[ConsoleCommand\(\s*["\']([^"\']+)["\']\s*\)\]')
    
    print_header(); print("\n"*4 + YELLOW + center("SKENOVÁNÍ PŘÍKAZŮ V PLUGINECH...") + RESET); time.sleep(1)

    all_results = []
    for f_name in files_to_check:
        filepath = os.path.join(settings["source_dir"], f_name)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
        except Exception: continue
        
        chat_cmds = chat_reg.findall(content)
        cons_cmds = cons_reg.findall(content)
        
        if chat_cmds or cons_cmds:
            all_results.append({"preview": f"--- PLUGIN: {f_name} ---", "full": f"Nalezené příkazy pro plugin {f_name}", "filepath": filepath})
            for c in chat_cmds: all_results.append({"preview": f" 💬 CHAT: /{c}", "full": f"Chatový příkaz: /{c}", "filepath": filepath})
            for c in cons_cmds: all_results.append({"preview": f" 💻 KONZOLE: {c}", "full": f"Konzolový příkaz: {c}", "filepath": filepath})
                
    if all_results:
        c_sel = 0
        while True:
            render_menu("EXTRAKCE DOKONČENA", ["Zobrazit v konzoli", "Exportovat do TXT a otevřít", "Zpět"], c_sel)
            k = read_key()
            if k in ['a','q','esc']: break
            elif k == 'w' and c_sel > 0: c_sel -= 1
            elif k == 's' and c_sel < 2: c_sel += 1
            elif k in ['d','enter','space']:
                if c_sel == 0:
                    detail_view("VŠECHNY NALEZENÉ PŘÍKAZY", all_results)
                elif c_sel == 1:
                    txt_path = os.path.join(tempfile.gettempdir(), "ExtractedCommands.txt")
                    try:
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write("=== ZEDDIHUB COMMAND EXTRACTOR ===\n\n")
                            for r in all_results: f.write(r["full"] + "\n")
                        if platform.system() == "Windows": os.startfile(txt_path)
                    except: pass
                elif c_sel == 2: break
    else:
        print_header(); print("\n"*4 + GREEN + center("V pluginech nebyly nalezeny žádné příkazy.") + RESET); time.sleep(3)

def run_stability_check():
    sel_dir = 0
    opts_dir = [
        f"Zdrojová složka (Původní): {os.path.basename(settings['source_dir'])}",
        f"Cílová složka (Opravené): {os.path.basename(settings['target_dir'])}"
    ]
    while True:
        render_menu("ANALYZÁTOR STABILITY - VÝBĚR SLOŽKY", opts_dir, sel_dir, footer="[W/S] Pohyb | [Enter] Vybrat | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel_dir > 0: sel_dir -= 1
        elif k == 's' and sel_dir < len(opts_dir)-1: sel_dir += 1
        elif k in ['d', 'enter', 'space']:
            work_dir = settings["source_dir"] if sel_dir == 0 else settings["target_dir"]
            break
            
    if not os.path.exists(work_dir): return
    files = [f for f in os.listdir(work_dir) if f.endswith(".cs")]
    if not files: return

    sel_files = multi_select_menu("ANALYZÁTOR STABILITY - VÝBĚR SOUBORŮ", files, [True]*len(files), ["Vyberte pluginy pro analýzu."]*len(files))
    if not sel_files: return
    
    files_to_check = [files[i] for i in range(len(files)) if sel_files[i]]
    if not files_to_check: return

    init_session_log("StabilityCheckLog")
    checks = {
        "FindObjectsOfType": {"regex": r"FindObjectsOfType", "level": "CRITICAL", "msg": "Extrémně náročné na výkon!"},
        "OnTick": {"regex": r"void\s+OnTick\s*\(", "level": "WARN", "msg": "Hook OnTick drasticky snižuje FPS serveru."},
        "Update": {"regex": r"void\s+Update\s*\(", "level": "WARN", "msg": "Unity Update() metoda silně zatěžuje hlavní vlákno."},
        "rust.RunServerCommand": {"regex": r"rust\.RunServerCommand", "level": "INFO", "msg": "Zastaralá metoda. Použijte raději 'Server.Command'."},
        "OnPlayerInit": {"regex": r"OnPlayerInit\s*\(", "level": "INFO", "msg": "Zastaralý hook. Použijte OnPlayerConnected."}
    }
    
    prog_win = ProgressWindow()
    prog_win.start("ZeddiHub Editor - Stability Analyzer")
    total_issues = 0; start_t = time.time(); paused_t = 0
    f_with_issues = []; full_list = []

    for f_idx, f_name in enumerate(files_to_check):
        filepath = os.path.join(work_dir, f_name)
        try:
            with open(filepath, "r", encoding="utf-8") as f: lines = f.readlines()
        except Exception: continue
        
        issues = []
        for l_idx, line in enumerate(lines):
            for chk_name, chk_data in checks.items():
                if re.search(chk_data["regex"], line):
                    issues.append({"preview": f"{chk_data['level']}: {chk_name} (L{l_idx+1})", "full": f"[{chk_data['level']}] '{chk_name}' na řádku {l_idx+1}:\n{line.strip()}\nInfo: {chk_data['msg']}", "filepath": filepath})

        if issues:
            f_with_issues.append(f_name)
            full_list.append({"preview": f"--- PLUGIN: {f_name} ---", "full": f"Výpis pro plugin {f_name}", "filepath": filepath})
            full_list.extend(issues)
            total_issues += len(issues)
            prog_win.log(f"\n⚠️ {f_name}: Nalezeno {len(issues)} potenciálních problémů")
            time.sleep(settings["write_speed"] * 5)
            
        draw_progress(0, 1, time.time() - start_t - paused_t, 0, f_idx+1, len(files_to_check), f_name)

    write_log(f"DOKONČENO! Nalezeno {total_issues} potenciálních problémů.")
    try:
        import winsound
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except: pass
    
    if total_issues == 0:
        prog_win.log("\n✅ NENALEZENY ŽÁDNÉ ZNÁMÉ CHYBY STABILITY!")
        prog_win.bring_to_front()
        return

    prog_win.log("\n" + "="*60 + "\n✅ ANALÝZA DOKONČENA! Zavírám okno, pokračujte v hlavní konzoli...\n" + "="*60)
    prog_win.bring_to_front()
    time.sleep(2)
    prog_win.q.put("[[CLOSE]]")
    time.sleep(0.5)
    
    c_sel = 0
    while True:
        render_menu("VÝSLEDEK ANALÝZY", ["Zobrazit detailní výsledky (Doporučeno)", "Opravit chyby automaticky (Přidat do fronty)", "Pokračovat dál"], c_sel)
        k = read_key()
        if k in ['a','q','esc']: break
        elif k == 'w' and c_sel > 0: c_sel -= 1
        elif k == 's' and c_sel < 2: c_sel += 1
        elif k in ['d','enter','space']:
            if c_sel == 0: detail_view("VÝSLEDKY ANALÝZY STABILITY", full_list)
            elif c_sel == 1:
                fix_sel = 0
                while True:
                    render_menu("OPRAVA CHYB DO FRONTY", ["Opravit VŠECHNY zasažené soubory", "Vybrat jednotlivé soubory k opravě", "Zpět"], fix_sel)
                    fk = read_key()
                    if fk in ['a','q','esc']: break
                    elif fk == 'w' and fix_sel > 0: fix_sel -= 1
                    elif fk == 's' and fix_sel < 2: fix_sel += 1
                    elif fk in ['d','enter','space']:
                        to_fix = []
                        if fix_sel == 0: to_fix = f_with_issues
                        elif fix_sel == 1:
                            try:
                                tf_flags = multi_select_menu("VYBERTE SOUBORY K OPRAVĚ", f_with_issues, [True]*len(f_with_issues), enable_x=True)
                                if not tf_flags: continue
                                to_fix = [f_with_issues[i] for i in range(len(f_with_issues)) if tf_flags[i]]
                            except ExecuteQueueNow:
                                to_fix = f_with_issues
                        else: break
                            
                        for f in to_fix:
                            rules = [(r"UnityEngine\.Object\.FindObjectsOfType<([^>]+)>\(\)", r"BaseNetworkable.serverEntities.OfType<\1>()"), (r"rust\.RunServerCommand\(", r"Server.Command("), (r"OnPlayerInit\(", r"OnPlayerConnected(")]
                            queue_add("bulk_fix", f, rules=rules, count=1, desc="Auto oprava stability")
                            
                        print_header(); print("\n"*4 + GREEN + center("✅ Opravy úspěšně přidány do Fronty!") + RESET); time.sleep(1.5)
                        if 'tf_flags' not in locals() or fix_sel == 0:
                            try:
                                print_header()
                                print("\n"*4 + YELLOW + center("Chcete frontu oprav spustit HNED TEĎ? [Enter = ANO / Esc = NE]") + RESET)
                                if read_key(allow_esc_exit=False) in ['d','enter','space']:
                                    from .queue_tools import execute_queue
                                    execute_queue()
                            except Exception: pass
                        break
            elif c_sel == 2: break

def run_generated_files_simulator():
    if not os.path.exists(settings["source_dir"]): return
    files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(".cs")]
    if not files: return
    
    sel_files = multi_select_menu("SIMULÁTOR DAT A KONFIGŮ - VÝBĚR", files, [True]*len(files), ["Vybere pluginy ke skenování dat."] * len(files))
    if not sel_files: return
    
    files_to_check = [files[i] for i in range(len(files)) if sel_files[i]]
    if not files_to_check: return

    cfg_regex = re.compile(r'(?:Config|Configuration)\.(?:WriteObject|Save)\s*\(')
    data_regex = re.compile(r'(?:DataFileSystem|Interface\.Oxide\.DataFileSystem)\.(?:WriteObject|ReadObject|GetFile)(?:<[^>]+>)?\s*\(\s*"([^"]+)"')
    
    print_header(); print("\n"*4 + YELLOW + center("SKENOVÁNÍ VYGENEROVANÝCH SOUBORŮ...") + RESET); time.sleep(1)

    all_results = []
    for f_name in files_to_check:
        filepath = os.path.join(settings["source_dir"], f_name)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
        except Exception: continue
        
        configs, datas = [], []
        if "SaveConfig()" in content or cfg_regex.search(content) or "LoadDefaultConfig" in content:
            configs.append(f"oxide/config/{f_name.replace('.cs', '')}.json")
            
        for m in data_regex.finditer(content): datas.append(f"oxide/data/{m.group(1)}.json")
        datas = list(set(datas))
        
        if configs or datas:
            all_results.append({"preview": f"--- PLUGIN: {f_name} ---", "full": f"Vygenerované soubory pro plugin {f_name}", "filepath": filepath})
            for c in configs: all_results.append({"preview": f" ⚙️ CONFIG: {c}", "full": f"Konfigurační soubor bude vytvořen v: {c}", "filepath": filepath})
            for d in datas: all_results.append({"preview": f" 💾 DATA: {d}", "full": f"Datový soubor bude vytvořen v: {d}", "filepath": filepath})
                
    if all_results: detail_view("VŠECHNY VYGENEROVANÉ SOUBORY", all_results)
    else: print_header(); print("\n"*4 + GREEN + center("Vybrané pluginy negenerují žádná data ani configy.") + RESET); time.sleep(3)