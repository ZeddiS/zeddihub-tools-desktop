import os
import time
import platform
import threading
import queue
import tkinter as tk
from tkinter import filedialog
import re
from .core import *

def draw_crosshair_ascii(size, gap, thickness, color_idx):
    try:
        s = int(float(size))
        g = int(float(gap))
        t = max(1, int(float(thickness) * 2))
    except Exception:
        s, g, t = 2, 0, 1

    colors = [RED, GREEN, YELLOW, "\033[38;5;21m", CYAN, RESET]
    try:
        c_color = colors[int(color_idx)] if 0 <= int(color_idx) <= 5 else GREEN
    except Exception:
        c_color = GREEN

    art = []
    art.append(GRAY + "┌" + "─"*30 + "┐" + RESET)
    
    center_y = 7
    center_x = 15
    for y in range(15):
        row = ""
        for x in range(30):
            if center_x - (t//2) <= x <= center_x + (t//2) and (center_y - g - s <= y < center_y - g):
                row += c_color + "█" + RESET
            elif center_x - (t//2) <= x <= center_x + (t//2) and (center_y + g < y <= center_y + g + s):
                row += c_color + "█" + RESET
            elif center_y - (t//2) <= y <= center_y + (t//2) and (center_x - g - s*2 <= x < center_x - g):
                row += c_color + "█" + RESET
            elif center_y - (t//2) <= y <= center_y + (t//2) and (center_x + g < x <= center_x + g + s*2):
                row += c_color + "█" + RESET
            else:
                row += " "
        art.append(GRAY + "│" + RESET + row + GRAY + "│" + RESET)
        
    art.append(GRAY + "└" + "─"*30 + "┘" + RESET)
    return art

def crosshair_generator():
    settings_xhair = {
        "cl_crosshairstyle": "4",
        "cl_crosshairsize": "2",
        "cl_crosshairthickness": "0.5",
        "cl_crosshairgap": "-1",
        "cl_crosshairdot": "0",
        "cl_crosshaircolor": "1",
        "cl_crosshair_drawoutline": "0"
    }
    sel = 0
    while True:
        keys = list(settings_xhair.keys())
        opts = [f"{k.ljust(25)}: {settings_xhair[k]}" for k in keys]
        opts.append(GREEN + "💾 Uložit do crosshair.cfg" + RESET)
        
        art = draw_crosshair_ascii(settings_xhair["cl_crosshairsize"], settings_xhair["cl_crosshairgap"], settings_xhair["cl_crosshairthickness"], settings_xhair["cl_crosshaircolor"])
        
        render_menu("CROSSHAIR GENERATOR (ŽIVÝ NÁHLED)", opts, sel, footer="[W/S] Pohyb | [Enter] Upravit hodnotu | [A/Esc] Zpět", extra_art=art)
        k = read_key()
        
        if k in ['a', 'esc', 'q']:
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == len(keys):
                os.makedirs(settings["target_dir"], exist_ok=True)
                path = os.path.join(settings["target_dir"], "crosshair.cfg")
                with open(path, "w", encoding="utf-8") as f:
                    for k_name, v_val in settings_xhair.items():
                        f.write(f'{k_name} "{v_val}"\n')
                print_header()
                print("\n"*4 + GREEN + center("✅ Soubor crosshair.cfg úspěšně vygenerován!") + RESET)
                time.sleep(2)
                if settings.get("open_folder_after") and platform.system() == "Windows":
                    try:
                        os.startfile(settings["target_dir"])
                    except Exception:
                        pass
                return
            else:
                c_key = keys[sel]
                print_header()
                print("\n"*4 + YELLOW + center(f"ÚPRAVA HODNOTY: {c_key}") + RESET)
                if c_key == "cl_crosshaircolor":
                    print(center("(0=Červená, 1=Zelená, 2=Žlutá, 3=Modrá, 4=Světle modrá)"))
                new_val = safe_input("\n" + center(f"Nová hodnota (nyní '{settings_xhair[c_key]}'): "))
                if new_val is not None and new_val.strip() != "":
                    settings_xhair[c_key] = new_val.strip()

class ViewmodelPreviewWindow:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.q = queue.Queue()
        self.is_running = False

    def _run(self):
        self.root = tk.Tk()
        self.root.title("CS:GO Viewmodel Live Preview")
        self.root.geometry("800x600")
        self.root.configure(bg="#222")
        
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="#111", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.create_rectangle(50, 50, 750, 550, outline="#444", width=5)
        self.canvas.create_text(400, 30, text="Náhled zbraně hráče", fill="#888", font=("Consolas", 14))
        
        self.gun_poly = self.canvas.create_polygon(0,0, 0,0, 0,0, fill="#555", outline="#777", width=2)
        
        self.is_running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.process_queue()
        self.root.mainloop()

    def process_queue(self):
        try:
            while not self.q.empty():
                msg = self.q.get_nowait()
                if msg == "[[CLOSE]]":
                    self.on_close()
                    return
                elif isinstance(msg, dict):
                    fov = float(msg.get("fov", 68))
                    x = float(msg.get("x", 2.5))
                    y = float(msg.get("y", 0))
                    z = float(msg.get("z", -1.5))
                    
                    base_x = 600 + (x * 30) - (fov * 1.5)
                    base_y = 600 - (z * 30) + (y * 10)
                    
                    points = [
                        base_x, base_y,
                        base_x + 100, base_y,
                        base_x + 150, base_y - 200,
                        base_x + 50, base_y - 220,
                        base_x - 20, base_y - 100
                    ]
                    self.canvas.coords(self.gun_poly, *points)
        except Exception:
            pass
            
        if self.is_running:
            self.root.after(50, self.process_queue)

    def on_close(self):
        self.is_running = False
        self.root.destroy()

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        time.sleep(0.5)

    def update_view(self, fov, x, y, z):
        self.q.put({"fov": fov, "x": x, "y": y, "z": z})
        
    def close(self):
        self.q.put("[[CLOSE]]")

def viewmodel_generator():
    settings_vm = {
        "viewmodel_fov": "68",
        "viewmodel_offset_x": "2.5",
        "viewmodel_offset_y": "0",
        "viewmodel_offset_z": "-1.5",
        "viewmodel_presetpos": "3",
        "cl_bob_lower_amt": "5",
        "cl_bobamt_lat": "0.1"
    }
    
    vw = ViewmodelPreviewWindow()
    vw.start()
    vw.update_view(settings_vm["viewmodel_fov"], settings_vm["viewmodel_offset_x"], settings_vm["viewmodel_offset_y"], settings_vm["viewmodel_offset_z"])
    
    sel = 0
    while True:
        keys = list(settings_vm.keys())
        opts = [f"{k.ljust(25)}: {settings_vm[k]}" for k in keys]
        opts.append(GREEN + "💾 Uložit do viewmodel.cfg" + RESET)
        
        render_menu("VIEWMODEL GENERATOR (ŽIVÉ OKNO)", opts, sel, footer="[W/S] Pohyb | [Enter] Upravit | [A/Esc] Zpět")
        k = read_key()
        
        if k in ['a', 'esc', 'q']: 
            vw.close()
            return
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(opts)-1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == len(keys):
                vw.close()
                os.makedirs(settings["target_dir"], exist_ok=True)
                path = os.path.join(settings["target_dir"], "viewmodel.cfg")
                with open(path, "w", encoding="utf-8") as f:
                    for k_name, v_val in settings_vm.items():
                        f.write(f'{k_name} "{v_val}"\n')
                print_header()
                print("\n"*4 + GREEN + center("✅ Soubor viewmodel.cfg úspěšně vygenerován!") + RESET)
                time.sleep(2)
                if settings.get("open_folder_after") and platform.system() == "Windows":
                    try:
                        os.startfile(settings["target_dir"])
                    except Exception:
                        pass
                return
            else:
                c_key = keys[sel]
                print_header()
                print("\n"*4 + YELLOW + center(f"ÚPRAVA HODNOTY: {c_key}") + RESET)
                new_val = safe_input("\n" + center(f"Nová hodnota (nyní '{settings_vm[c_key]}'): "))
                if new_val is not None and new_val.strip() != "":
                    settings_vm[c_key] = new_val.strip()
                    vw.update_view(settings_vm["viewmodel_fov"], settings_vm["viewmodel_offset_x"], settings_vm["viewmodel_offset_y"], settings_vm["viewmodel_offset_z"])

def config_generator():
    autoexec = {
        "rate": "786432",
        "cl_cmdrate": "128",
        "cl_updaterate": "128",
        "cl_interp_ratio": "1",
        "cl_interp": "0",
        "fps_max": "0",
        "fps_max_menu": "120",
        "r_drawtracers_firstperson": "0",
        "mat_queue_mode": "2",
        "cl_forcepreload": "1",
        "snd_mixahead": "0.05",
        "snd_musicvolume": "0",
        "cl_downloadfilter": "nosounds",
        "cl_disablehtmlmotd": "1",
        "gameinstructor_enable": "0",
        "cl_autohelp": "0",
        "cl_showhelp": "0",
        "con_enable": "1"
    }

    categories = {
        "Network (rate, interp)": ["rate", "cl_cmdrate", "cl_updaterate", "cl_interp_ratio", "cl_interp"],
        "FPS a Grafika": ["fps_max", "fps_max_menu", "r_drawtracers_firstperson", "mat_queue_mode", "cl_forcepreload"],
        "Zvuk": ["snd_mixahead", "snd_musicvolume"],
        "Utility": ["cl_downloadfilter", "cl_disablehtmlmotd", "gameinstructor_enable", "cl_autohelp", "cl_showhelp", "con_enable"]
    }

    sel = 0
    keys = list(autoexec.keys())
    while True:
        opts = [f"{k.ljust(28)}: {autoexec[k]}" for k in keys]
        opts.append("")
        opts.append(GREEN + "Uložit do autoexec.cfg" + RESET)

        cat_descs = []
        for k in keys:
            for cat_name, cat_keys in categories.items():
                if k in cat_keys:
                    cat_descs.append(cat_name)
                    break
            else:
                cat_descs.append("")
        cat_descs.append("")
        cat_descs.append("Vygeneruje optimalizovany autoexec.cfg do cilove slozky.")

        render_menu("AUTOEXEC CONFIG GENERATOR", opts, sel, cat_descs, footer="[W/S] Pohyb | [Enter] Upravit | [A/Esc] Zpět")
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
            if "Ulozit" in opts[sel]:
                os.makedirs(settings["target_dir"], exist_ok=True)
                path = os.path.join(settings["target_dir"], "autoexec.cfg")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("// Generated by ZeddiHub CS:GO Tools\n")
                    f.write("// https://zeddihub.eu\n\n")
                    for cat_name, cat_keys in categories.items():
                        f.write(f"// === {cat_name} ===\n")
                        for ck in cat_keys:
                            f.write(f'{ck} "{autoexec[ck]}"\n')
                        f.write("\n")
                    f.write('echo "ZeddiHub autoexec loaded!"\nhost_writeconfig\n')
                print_header()
                print("\n"*4 + GREEN + center("Soubor autoexec.cfg úspěšně vygenerován!") + RESET)
                time.sleep(2)
                if settings.get("open_folder_after") and platform.system() == "Windows":
                    try:
                        os.startfile(settings["target_dir"])
                    except Exception:
                        pass
                return
            else:
                c_key = keys[sel]
                print_header()
                print("\n"*4 + YELLOW + center(f"ÚPRAVA HODNOTY: {c_key}") + RESET)
                new_val = safe_input("\n" + center(f"Nová hodnota (nyní '{autoexec[c_key]}'): "))
                if new_val is not None and new_val.strip() != "":
                    autoexec[c_key] = new_val.strip()

def practice_config():
    cfg = {
        "sv_cheats": "1",
        "sv_infinite_ammo": "1",
        "ammo_grenade_limit_total": "5",
        "sv_grenade_trajectory": "1",
        "sv_grenade_trajectory_time": "10",
        "sv_showimpacts": "1",
        "sv_showimpacts_time": "5",
        "mp_warmup_end": "1",
        "mp_freezetime": "0",
        "mp_roundtime_defuse": "60",
        "mp_roundtime": "60",
        "mp_buytime": "9999",
        "mp_buy_anywhere": "1",
        "mp_startmoney": "65535",
        "mp_maxmoney": "65535",
        "mp_restartgame": "1",
        "bot_kick": "1",
        "mp_autoteambalance": "0",
        "mp_limitteams": "0",
        "god": "1"
    }
    sel = 0
    keys = list(cfg.keys())
    while True:
        opts = [f"{k.ljust(28)}: {cfg[k]}" for k in keys]
        opts.append("")
        opts.append(GREEN + "Uložit do practice.cfg" + RESET)
        render_menu("CS:GO PRACTICE CONFIG", opts, sel,
                     footer="[W/S] Pohyb | [Enter] Upravit | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if opts[sel] == "": continue
            if "Ulozit" in opts[sel]:
                os.makedirs(settings["target_dir"], exist_ok=True)
                path = os.path.join(settings["target_dir"], "practice.cfg")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("// CS:GO Practice Config - Generated by ZeddiHub CS:GO Tools\n")
                    f.write("// https://zeddihub.eu\n\n")
                    for ck, cv in cfg.items():
                        f.write(f"{ck} {cv}\n")
                    f.write('\necho "[ZeddiHub] Practice mode loaded!"\n')
                print_header()
                print("\n" * 4 + GREEN + center("Soubor practice.cfg úspěšně vygenerován!") + RESET)
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


def buy_binds_generator():
    binds = {
        "KP_INS": ("Vesta + Helma", "buy vesthelm;"),
        "KP_END": ("AK-47 / M4A4", "buy ak47; buy m4a1;"),
        "KP_DOWNARROW": ("AWP", "buy awp;"),
        "KP_PGDN": ("Deagle", "buy deagle;"),
        "KP_LEFT": ("Smoke", "buy smokegrenade;"),
        "KP_5": ("Flash", "buy flashbang;"),
        "KP_RIGHT": ("Molotov / Incendiary", "buy molotov; buy incgrenade;"),
        "KP_HOME": ("HE Granat", "buy hegrenade;"),
        "KP_UPARROW": ("Defuse Kit", "buy defuser;"),
        "KP_PGUP": ("Full Buy (Rifle+Vest+Nades)", "buy vesthelm; buy ak47; buy m4a1; buy smokegrenade; buy flashbang; buy hegrenade; buy molotov; buy incgrenade; buy defuser;"),
    }

    sel = 0
    bind_keys = list(binds.keys())
    while True:
        opts = [f"[{k}] {binds[k][0]}" for k in bind_keys]
        opts.append("")
        opts.append(GREEN + "Uložit do buybinds.cfg" + RESET)
        descs = [binds[k][1] for k in bind_keys]
        descs.append("")
        descs.append("Uloží všechny buy bindy do .cfg souboru.")
        render_menu("CS:GO BUY BINDS GENERATOR", opts, sel, descs,
                     footer="[W/S] Pohyb | [Enter] Upravit příkaz | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if opts[sel] == "": continue
            if "Ulozit" in opts[sel]:
                os.makedirs(settings["target_dir"], exist_ok=True)
                path = os.path.join(settings["target_dir"], "buybinds.cfg")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("// CS:GO Buy Binds - Generated by ZeddiHub CS:GO Tools\n")
                    f.write("// https://zeddihub.eu\n\n")
                    for bk, (desc, cmd) in binds.items():
                        f.write(f'bind "{bk}" "{cmd}"  // {desc}\n')
                    f.write('\necho "[ZeddiHub] Buy binds loaded!"\n')
                print_header()
                print("\n" * 4 + GREEN + center("Soubor buybinds.cfg úspěšně vygenerován!") + RESET)
                time.sleep(2)
                if settings.get("open_folder_after") and platform.system() == "Windows":
                    try: os.startfile(settings["target_dir"])
                    except Exception: pass
                return
            else:
                bkey = bind_keys[sel]
                print_header()
                print("\n" * 4 + YELLOW + center(f"ÚPRAVA PŘÍKAZU PRO [{bkey}]") + RESET)
                print(center(f"Popis: {binds[bkey][0]}"))
                new_cmd = safe_input("\n" + center(f"Nový příkaz (nyní '{binds[bkey][1]}'): "))
                if new_cmd is not None and new_cmd.strip():
                    binds[bkey] = (binds[bkey][0], new_cmd.strip())


def config_editor():
    print_header()
    print("\n"*4 + YELLOW + center("VÝBĚR CONFIGU") + RESET)
    print(center("Vyberte libovolný .cfg soubor z disku..."))
    time.sleep(1)
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    p = filedialog.askopenfilename(title="Vyberte config", filetypes=[("Config", "*.cfg"), ("Vše", "*.*")])
    root.destroy()
    
    if not p or not os.path.exists(p):
        return
    
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return

    parsed_lines = []
    for line in lines:
        clean = line.strip()
        if clean.startswith("//") or not clean:
            parsed_lines.append({"type": "raw", "content": line})
            continue
        
        m = re.match(r'^"?([a-zA-Z0-9_]+)"?\s+"?([^"]*)"?$', clean)
        if m:
            parsed_lines.append({"type": "kv", "key": m.group(1), "val": m.group(2), "orig": line})
        else:
            parsed_lines.append({"type": "raw", "content": line})
            
    kv_indices = [i for i, x in enumerate(parsed_lines) if x["type"] == "kv"]
    if not kv_indices:
        print_header()
        print("\n"*4 + RED + center("V souboru nebyly nalezeny žádné upravitelné proměnné.") + RESET)
        time.sleep(2)
        return
        
    sel = 0
    while True:
        opts = []
        for idx in kv_indices:
            item = parsed_lines[idx]
            opts.append(f"{item['key'].ljust(30)} {item['val']}")
        opts.append("")
        opts.append(GREEN + "💾 ULOŽIT NOVÝ CONFIG A OTEVŘÍT SLOŽKU" + RESET)
        
        render_menu(f"EDITOR CONFIGU: {os.path.basename(p)}", opts, sel, footer="[W/S] Pohyb | [Enter] Upravit | [A/Esc] Zrušit a Zpět")
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
            if "ULOŽIT" in opts[sel]:
                os.makedirs(settings["target_dir"], exist_ok=True)
                target = os.path.join(settings["target_dir"], os.path.basename(p))
                with open(target, "w", encoding="utf-8") as f:
                    for line in parsed_lines:
                        if line["type"] == "raw":
                            f.write(line["content"])
                        else:
                            f.write(f'{line["key"]} "{line["val"]}"\n')
                print_header()
                print("\n"*4 + GREEN + center("✅ Config úspěšně uložen do cílové složky!") + RESET)
                time.sleep(2)
                if settings.get("open_folder_after") and platform.system() == "Windows":
                    try:
                        os.startfile(settings["target_dir"])
                    except Exception:
                        pass
                return
            else:
                p_idx = kv_indices[sel]
                item = parsed_lines[p_idx]
                print_header()
                print("\n"*4 + YELLOW + center(f"ÚPRAVA HODNOTY: {item['key']}") + RESET)
                new_val = safe_input("\n" + center(f"Nová hodnota (nyní '{item['val']}'): "))
                if new_val is not None and new_val.strip() != "":
                    parsed_lines[p_idx]["val"] = new_val.strip()