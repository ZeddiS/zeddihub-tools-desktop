import os
import re
import time
import shutil
from .core import *

AVAILABLE_FIXES = [
    {"id": "pool", "name": "Facepunch.Pool (GetList/FreeList)", "desc": "Opravuje staré metody na nové unmanaged z updatu Shipshape.", "rules": [(r"Pool\.GetList<(.+?)>\(\)", r"Pool.Get<List<\1>>()"), (r"Pool\.FreeList\((.+?)\)", r"Pool.FreeUnmanaged(\1)")]},
    {"id": "hooks", "name": "Zastaralé Hooky (Oxide)", "desc": "Aktualizuje OnPlayerInit na OnPlayerConnected.", "rules": [(r"OnPlayerInit\s*\(", r"OnPlayerConnected(")]},
    {"id": "cmd", "name": "Oxide Command API", "desc": "Nahradí zastaralé player.SendConsoleCommand za bezpečné player.Command.", "rules": [(r"(\w+)\.SendConsoleCommand\(", r"\1.Command(")]},
    {"id": "conn", "name": "Bezpečné Player Connection", "desc": "Přepisuje padající player.net.connection na stabilnější player.Connection.", "rules": [(r"(\w+)\.net\.connection", r"\1.Connection")]},
    {"id": "ontick", "name": "Zablokování OnTick()", "desc": "Zakomentuje OnTick, který způsobuje lagy a chyby.", "rules": [(r"(\s*)void\s+OnTick\s*\(", r"\1// void OnTick(")]},
    {"id": "notify", "name": "Rust+ Notification Fix", "desc": "Zakomentuje odesílání notifikací, které hází Internal Server Error.", "rules": [(r"([^/])(SendNotification\s*\()", r"\1// \2")]}
]

def queue_bulk_fix():
    if not os.path.exists(settings["source_dir"]): return
    files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(".cs")]
    if not files: return

    sel_fixes = multi_select_menu("HROMADNÁ OPRAVA - VÝBĚR PRAVIDEL", [f["name"] for f in AVAILABLE_FIXES], [True]*len(AVAILABLE_FIXES), [f["desc"] for f in AVAILABLE_FIXES])
    if not sel_fixes: return
        
    active_rules = []
    for i, active in enumerate(sel_fixes):
        if active: active_rules.extend(AVAILABLE_FIXES[i]["rules"])

    print_header(); print("\n"*4 + YELLOW + center("PROBÍHÁ ANALÝZA SOUBORŮ...") + RESET)
    affected_files, affected_descs, file_ops, file_details = [], [], {}, {}

    for f_name in files:
        filepath = os.path.join(settings["source_dir"], f_name)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f: lines = f.readlines()
        except Exception: continue
        
        matches, details = 0, []
        for pat, rep in active_rules:
            for line_idx, line in enumerate(lines):
                if re.search(pat, line):
                    matches += 1; details.append({"preview": f"Řádek {line_idx + 1}: Nalezen vzor", "full": f"[{line_idx + 1}] {line.strip()}", "filepath": filepath})
                
        if matches > 0:
            affected_files.append(f_name); affected_descs.append(f"Nalezeno {matches}x míst k opravě.")
            file_ops[f_name] = matches; file_details[f_name] = details

    if not affected_files:
        print_header(); print("\n"*4 + GREEN + center("V pluginech nebyly nalezeny žádné chyby k opravě!") + RESET); time.sleep(3); return

    try:
        sel_files = multi_select_menu("PŘEHLED CHYB A VÝBĚR K OPRAVĚ", affected_files, [True]*len(affected_files), affected_descs, file_details, enable_x=True)
        if not sel_files: return
        add_and_exec = False
    except ExecuteQueueNow:
        sel_files = [True]*len(affected_files)
        add_and_exec = True
    
    added_count = 0
    for i, active in enumerate(sel_files):
        if active:
            queue_add("bulk_fix", affected_files[i], rules=active_rules, count=file_ops[affected_files[i]])
            added_count += 1
            
    print_header(); print("\n"*4 + GREEN + center(f"✅ Přidáno {added_count} pluginů k hromadné opravě do Fronty!") + RESET); time.sleep(1.5)
    if add_and_exec: execute_queue()

def queue_command_editor():
    if not os.path.exists(settings["source_dir"]): return
    files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(".cs")]
    if not files: return

    print_header(); print("\n"*4 + YELLOW + center("SKENOVÁNÍ PŘÍKAZŮ V PLUGINECH...") + RESET)
    cmd_regex = re.compile(r'\[(ChatCommand|ConsoleCommand)\(\s*["\']([^"\']+)["\']\s*\)\]')
    file_commands = {}
    
    for f_name in files:
        try:
            with open(os.path.join(settings["source_dir"], f_name), "r", encoding="utf-8", errors="ignore") as f:
                matches = cmd_regex.findall(f.read())
                if matches: file_commands[f_name] = matches
        except Exception: continue

    if not file_commands:
        print_header(); print("\n"*4 + GREEN + center("V pluginech nebyly nalezeny žádné upravitelné příkazy.") + RESET); time.sleep(3); return

    plugin_names = list(file_commands.keys()); sel_plugin = 0
    while True:
        render_menu("EDITOR PŘÍKAZŮ - VÝBĚR PLUGINU", plugin_names, sel_plugin)
        k = read_key()
        if k in ['a', 'q', 'esc']: return
        elif k == 'w' and sel_plugin > 0: sel_plugin -= 1
        elif k == 's' and sel_plugin < len(plugin_names) - 1: sel_plugin += 1
        elif k in ['d', 'enter', 'space']:
            chosen_file = plugin_names[sel_plugin]
            cmds = file_commands[chosen_file]
            cmd_sel = 0
            while True:
                display_cmds = [f"[{c[0]}] /{c[1]}" for c in cmds]
                render_menu(f"PŘÍKAZY: {chosen_file}", display_cmds, cmd_sel, footer="[W/S] Pohyb | [Enter] Upravit do Fronty | [X] Spustit Frontu | [A/Esc] Zpět")
                ck = read_key()
                if ck in ['a', 'q', 'esc']: break
                elif ck == 'w' and cmd_sel > 0: cmd_sel -= 1
                elif ck == 's' and cmd_sel < len(cmds) - 1: cmd_sel += 1
                elif ck == 'x': execute_queue(); return
                elif ck in ['d', 'enter', 'space']:
                    curr_type, curr_cmd = cmds[cmd_sel]
                    print_header(); print("\n"*4 + YELLOW + center(f"ÚPRAVA PŘÍKAZU: {curr_cmd}") + RESET)
                    new_cmd = safe_input("\n" + center("Zadejte nový název příkazu (bez lomítka): "))
                    if new_cmd and new_cmd.strip():
                        old_attr = f'[{curr_type}("{curr_cmd}")]'
                        new_attr = f'[{curr_type}("{new_cmd.strip()}")]'
                        queue_add("replace_exact", chosen_file, old=old_attr, new=new_attr, desc=f"Změna příkazu na {new_cmd.strip()}", count=1)
                        cmds[cmd_sel] = (curr_type, new_cmd.strip())
                        print_header(); print("\n"*4 + GREEN + center("✅ Změna příkazu přidána do Fronty!") + RESET); time.sleep(1.5)

def queue_hardcoded_translator():
    if not os.path.exists(settings["source_dir"]): return
    files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(".cs")]
    if not files: return
    
    print_header(); print("\n"*4 + YELLOW + center("SKENOVÁNÍ SOUBORŮ PRO PŘEKLAD...") + RESET)
    chat_regex = re.compile(r'(?:SendReply|PrintToChat|ChatMessage|ReplyToPlayer|SendMessage|Chat)\s*\(\s*(?:[^,]+,\s*)?["\']([^"\'\\]*(?:\\.[^"\'\\]*)*)["\']')
    translatable_files = []

    for f_name in files:
        try:
            with open(os.path.join(settings["source_dir"], f_name), "r", encoding="utf-8", errors="ignore") as f:
                if chat_regex.search(f.read()): translatable_files.append(f_name)
        except Exception: continue

    if not translatable_files:
        print_header(); print("\n"*4 + GREEN + center("Nenalezeny žádné pevně kódované zprávy do chatu.") + RESET); time.sleep(2); return

    sel = 0
    while True:
        render_menu("PŘEKLADAČ ZPRÁV V KÓDU", [f"📄 {f}" for f in translatable_files], sel)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(translatable_files)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            f_name = translatable_files[sel]
            try:
                with open(os.path.join(settings["source_dir"], f_name), "r", encoding="utf-8", errors="ignore") as f: lines = f.readlines()
            except Exception: continue
            
            matches_data = [{"line_idx": i, "str_val": m.group(1)} for i, line in enumerate(lines) for m in chat_regex.finditer(line)]

            m_sel = 0
            while True:
                display = [textwrap.shorten(f"L{m['line_idx']+1}: {m['str_val']}", width=80) for m in matches_data]
                render_menu(f"ZPRÁVY V {f_name}", display, m_sel, footer="[W/S] Pohyb | [Enter] Přeložit do Fronty | [X] Spustit Frontu | [A/Esc] Zpět", preview_box=matches_data[m_sel]["str_val"])
                mk = read_key()
                if mk in ['a', 'esc', 'q']: break
                elif mk == 'w' and m_sel > 0: m_sel -= 1
                elif mk == 's' and m_sel < len(display)-1: m_sel += 1
                elif mk == 'x': execute_queue(); return
                elif mk in ['d', 'enter', 'space']:
                    curr_match = matches_data[m_sel]
                    print_header(); print(YELLOW + center("PŘEKLAD ZPRÁVY") + "\n" + CYAN + center(curr_match['str_val']) + RESET)
                    custom_t = safe_input("\n" + center("(ESC pro zrušení) Nový text: "))
                    if custom_t and custom_t.strip():
                        queue_add("replace_line", f_name, old=f'"{curr_match["str_val"]}"', new=f'"{custom_t}"', idx=curr_match["line_idx"], count=1, desc="Překlad zprávy")
                        matches_data[m_sel]["str_val"] = custom_t
                        print_header(); print("\n"*4 + GREEN + center("✅ Překlad přidán do Fronty!") + RESET); time.sleep(1)

def queue_prefix_detector():
    if not os.path.exists(settings["source_dir"]): return
    files = [f for f in os.listdir(settings["source_dir"]) if f.endswith(".cs")]
    if not files: return
    
    print_header(); print("\n"*4 + YELLOW + center("SKENOVÁNÍ PREFIXŮ V KÓDU...") + RESET)
    prefix_regex = re.compile(r'(?:public|private|internal|readonly|const|\s)*string\s+[a-zA-Z0-9_]*(?:[pP]refix|[pP]re)[a-zA-Z0-9_]*\s*=\s*["\']([^"\']+)["\']')
    prefix_files = []

    for f_name in files:
        try:
            with open(os.path.join(settings["source_dir"], f_name), "r", encoding="utf-8", errors="ignore") as f:
                if prefix_regex.search(f.read()): prefix_files.append(f_name)
        except Exception: continue

    if not prefix_files:
        print_header(); print("\n"*4 + GREEN + center("V pluginech nebyly nalezeny žádné pevně definované prefixy.") + RESET); time.sleep(2); return

    sel = 0
    while True:
        render_menu("DETEKTOR PREFIXŮ", [f"📄 {f}" for f in prefix_files], sel)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(prefix_files)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            f_name = prefix_files[sel]
            try:
                with open(os.path.join(settings["source_dir"], f_name), "r", encoding="utf-8", errors="ignore") as f: lines = f.readlines()
            except Exception: continue
            
            matches_data = [{"line_idx": i, "str_val": m.group(1)} for i, line in enumerate(lines) for m in prefix_regex.finditer(line)]

            m_sel = 0
            while True:
                display = [textwrap.shorten(f"L{m['line_idx']+1}: {m['str_val']}", width=80) for m in matches_data]
                render_menu(f"PREFIXY V {f_name}", display, m_sel, footer="[W/S] Pohyb | [Enter] Upravit do Fronty | [X] Spustit Frontu | [A/Esc] Zpět", preview_box=matches_data[m_sel]["str_val"])
                mk = read_key()
                if mk in ['a', 'esc', 'q']: break
                elif mk == 'w' and m_sel > 0: m_sel -= 1
                elif mk == 's' and m_sel < len(display)-1: m_sel += 1
                elif mk == 'x': execute_queue(); return
                elif mk in ['d', 'enter', 'space']:
                    curr_match = matches_data[m_sel]
                    copts = ["white","red","green","blue","yellow","orange","cyan","magenta"]
                    bopts = ["[]","{}","<>","()","Nic"]
                    cIdx, bIdx, bcIdx, ptxt, bSel = 1, 0, 0, "Server", 0
                    
                    while True:
                        bo, bc = ("", "") if bopts[bIdx] == "Nic" else (bopts[bIdx][0], bopts[bIdx][1])
                        boc = f"<color={copts[bcIdx]}>{bo}</color>" if bo and copts[bcIdx] != "white" else bo
                        bcc = f"<color={copts[bcIdx]}>{bc}</color>" if bc and copts[bcIdx] != "white" else bc
                        prev = f'{boc}<color={copts[cIdx]}>{ptxt}</color>{bcc}'
                        
                        opts = [f"Text Prefixu: {ptxt}", f"Barva textu: {copts[cIdx]}", f"Typ závorek: {bopts[bIdx]}", f"Barva závorek: {copts[bcIdx]}", "👉 POTVRDIT A PŘIDAT DO FRONTY"]
                        render_menu("TVORBA NOVÉHO PREFIXU", opts, bSel, preview_box=prev)
                        bk = read_key()
                        if bk in ['a','esc','q']: break
                        elif bk == 'w' and bSel > 0: bSel -= 1
                        elif bk == 's' and bSel < len(opts)-1: bSel += 1
                        elif bk in ['d','enter','space']:
                            if bSel == 0:
                                t = safe_input("\n" + center("Nový text: "))
                                if t: ptxt = t
                            elif bSel == 1: cIdx = (cIdx + 1) % len(copts)
                            elif bSel == 2: bIdx = (bIdx + 1) % len(bopts)
                            elif bSel == 3: bcIdx = (bcIdx + 1) % len(copts)
                            elif bSel == 4:
                                queue_add("replace_line", f_name, old=f'"{curr_match["str_val"]}"', new=f'"{prev}"', idx=curr_match["line_idx"], count=1, desc="Změna prefixu")
                                matches_data[m_sel]["str_val"] = prev
                                print_header(); print("\n"*4 + GREEN + center("✅ Prefix přidán do Fronty!") + RESET); time.sleep(1.5)
                                break

def execute_queue():
    from .wizard import pause_menu
    if not task_queue:
        print_header(); print("\n"*4 + YELLOW + center("Fronta je prázdná! Přidejte úkoly z Nástrojů.") + RESET); time.sleep(2); return

    tasks_by_file = {}
    total_ops = 0
    for t in task_queue:
        tasks_by_file.setdefault(t['file'], []).append(t)
        total_ops += t.get('count', 1)

    init_session_log("QueueExecutionLog")
    os.makedirs(settings["target_dir"], exist_ok=True)
    
    prog_win = ProgressWindow()
    prog_win.start("ZeddiHub Editor - Queue Execution")
    
    done_ops = 0; files_changed = 0; start_t = time.time(); paused_t = 0
    
    for f_idx, (f_name, tasks) in enumerate(tasks_by_file.items()):
        src_path = os.path.join(settings["source_dir"], f_name)
        tgt_path = os.path.join(settings["target_dir"], f_name)
        
        try:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines(); content = "".join(lines)
        except Exception: continue
            
        files_changed += 1
        prog_win.log(f"\n{'='*60}\n⚙️ ZPRACOVÁVÁM SOUBOR: {f_name}\n{'='*60}")
        file_ops_count = 0
        
        for t in tasks:
            if t["type"] == "bulk_fix":
                for pat, rep in t["rules"]:
                    c_matches = len(re.findall(pat, content))
                    if c_matches > 0:
                        content = re.sub(pat, rep, content)
                        prog_win.log(f"[+] Hromadná oprava: Nahrazeno {c_matches}x ({pat})")
                lines = content.splitlines(True); file_ops_count += t["count"]
            elif t["type"] == "replace_exact":
                content = content.replace(t["old"], t["new"]); lines = content.splitlines(True)
                prog_win.log(f"[+] {t['desc']}"); file_ops_count += t["count"]
            elif t["type"] == "replace_line":
                idx = t["idx"]
                if idx < len(lines):
                    lines[idx] = lines[idx].replace(t["old"], t["new"])
                    content = "".join(lines)
                    prog_win.log(f"[+] {t['desc']}"); file_ops_count += t["count"]

        if "Fixed by ZeddiHub" not in content:
            content = re.sub(r'(\[Description\([^\]]*?)("\)\])', r'\1 - Fixed by ZeddiHub\2', content, count=1)
            prog_win.log(f"[+] Přidán podpis do Description.")

        write_log(f"SOUBOR UPRAVEN Z FRONTY: {f_name} | Úkolů: {len(tasks)}")
        
        if settings["auto_backup"]:
            os.makedirs(settings["backup_dir"], exist_ok=True)
            shutil.copy(src_path, os.path.join(settings["backup_dir"], get_backup_name(f_name)))
            
        with open(tgt_path, "w", encoding="utf-8") as f: f.write(content)
        prog_win.log(f"✅ ULOŽENO: {f_name}")
        
        for _ in range(file_ops_count):
            time.sleep(settings["write_speed"]); done_ops += 1
            
            try:
                import msvcrt
                if msvcrt.kbhit():
                    kb = msvcrt.getch()
                    if kb == b'\x1b':
                        print_header(); print("\n"*5 + center(RED + "AKCE ZRUŠENA" + RESET)); time.sleep(2)
                        prog_win.log("[[CLOSE]]"); return
                    elif kb in [b'a', b'A', b'p', b'P']:
                        ps_start = time.time()
                        action = pause_menu()
                        if action == "abort":
                            prog_win.log("[[CLOSE]]"); return
                        paused_t += (time.time() - ps_start)
                        print_header()
            except Exception: pass
            
            eta = ((time.time() - start_t - paused_t) / done_ops) * (total_ops - done_ops) if done_ops > 0 else 0
            draw_progress(done_ops, total_ops, time.time() - start_t - paused_t, eta, f_idx+1, len(tasks_by_file), f_name)

    write_log(f"FRONTA DOKONČENA! Upravených souborů: {files_changed} | Celkem úkonů: {total_ops}")
    try:
        import winsound
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except: pass
        
    prog_win.log("\n" + "="*60 + "\n✅ FRONTA DOKONČENA! Log zůstane otevřený dokud ho nezavřete křížkem.\n" + "="*60)
    prog_win.bring_to_front()
    task_queue.clear()
    
    if settings.get("run_compiler_after"):
        from .compiler import run_compiler_simulator
        run_compiler_simulator(auto_mode=True)
        
    do_post_action()