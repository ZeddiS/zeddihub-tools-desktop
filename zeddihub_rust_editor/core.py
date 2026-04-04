import os
import json
import time
import sys
import shutil
import platform
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ctypes
import re
import textwrap
import threading
import queue
from .langs import L

VERSION = "v3.0.0"
CONSOLE_WIDTH = 110
CONSOLE_HEIGHT = 48

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COMPILER_DIR = os.path.join(SCRIPT_DIR, "compiler_refs")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "editor_config.json")

os.makedirs(SCRIPT_DIR, exist_ok=True)
os.makedirs(COMPILER_DIR, exist_ok=True)

ORANGE, CYAN, GREEN, YELLOW, RED, GRAY, RESET = '\033[38;5;208m', '\033[38;5;51m', '\033[38;5;46m', '\033[38;5;226m', '\033[38;5;196m', '\033[90m', '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
WHITE = '\033[97m'
SPEEDS = [0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.001]

task_queue = []

settings = {
    "ui_lang": "cz", "source_dir": "", "target_dir": "", 
    "backup_dir": os.path.join(SCRIPT_DIR, "backups"),
    "log_dir": os.path.join(SCRIPT_DIR, "logs"), 
    "auto_backup": True, "write_speed": 0.01, "post_action": 0, "run_compiler_after": False, "open_folder_after": False
}

SESSION_LOG_FILE = ""

class ReturnToLauncher(Exception): pass
class ExecuteQueueNow(Exception): pass

def t(key): return L.get(settings.get("ui_lang", "cz"), L["cz"]).get(key, key)

def save_settings():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(settings, f, indent=4)

def load_settings():
    global settings
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if k in settings: settings[k] = v
        except Exception: pass
        return True
    return False

def init_session_log(prefix="Log"):
    global SESSION_LOG_FILE
    os.makedirs(settings["log_dir"], exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    SESSION_LOG_FILE = os.path.join(settings["log_dir"], f"{prefix}_{stamp}.txt")
    write_log(f"=== ZEDDIHUB RUST EDITOR {VERSION} - SESSION START ===")

def write_log(action_text):
    global SESSION_LOG_FILE
    if not SESSION_LOG_FILE: init_session_log()
    try:
        with open(SESSION_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action_text}\n")
    except Exception: pass

def get_backup_name(original_filename):
    return f"{original_filename}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"

def format_time(seconds):
    m, s = divmod(int(max(0, seconds)), 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h:02d}h {m:02d}m"
    return f"{m:02d}:{s:02d}"

try: import msvcrt
except ImportError: pass

class ProgressWindow:
    def __init__(self):
        self.root = None; self.text_widget = None; self.is_running = False; self.auto_scroll = None; self.q = queue.Queue()
    def _run(self, title):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("850x650")
        self.root.configure(bg="#0c0c0c")
        top_frame = tk.Frame(self.root, bg="#0c0c0c")
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        self.auto_scroll = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(top_frame, text="Auto-Scroll", variable=self.auto_scroll, bg="#0c0c0c", fg="#fff", selectcolor="#222", font=("Consolas", 10))
        chk.pack(side=tk.LEFT)
        self.text_widget = tk.Text(self.root, bg="#0c0c0c", fg="#00ff00", font=("Consolas", 10), wrap=tk.WORD)
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
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
                elif msg == "[[FRONT]]":
                    self.root.attributes('-topmost', True)
                    self.root.attributes('-topmost', False)
                    self.root.lift()
                else:
                    self.text_widget.insert(tk.END, msg + "\n")
                    if self.auto_scroll.get():
                        self.text_widget.see(tk.END)
        except Exception: pass
        if self.is_running:
            self.root.after(50, self.process_queue)

    def on_close(self):
        self.is_running = False
        self.root.destroy()

    def start(self, title):
        thread = threading.Thread(target=self._run, args=(title,), daemon=True)
        thread.start()
        time.sleep(0.5)

    def log(self, msg): self.q.put(msg)
    def bring_to_front(self): self.q.put("[[FRONT]]")

def clean_len(text): return len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text))
def center(text, width=CONSOLE_WIDTH): return " " * max(0, (width - clean_len(text)) // 2) + text
def box_center(raw_text, colored_text, width=96):
    pad = max(0, width - clean_len(raw_text)); margin = " " * ((CONSOLE_WIDTH - (width + 2)) // 2)
    left_pad = " " * (pad // 2); right_pad = " " * (pad - (pad // 2))
    return f"{margin}{CYAN}│{RESET}{left_pad}{colored_text}{right_pad}{CYAN}│{RESET}"

def clear_console(): sys.stdout.write("\033[2J\033[H")
def setup_console():
    if platform.system() == "Windows":
        try:
            import ctypes
            h = ctypes.windll.kernel32.GetStdHandle(-10); m = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(m)); ctypes.windll.kernel32.SetConsoleMode(h, m.value & ~0x0040)
            ctypes.windll.kernel32.SetConsoleTitleW(f"★ ZeddiHub Rust Editor {VERSION} ★")
            os.system(f"mode con cols={CONSOLE_WIDTH} lines={CONSOLE_HEIGHT}")
        except Exception: pass

def do_post_action():
    if settings.get("open_folder_after"):
        try: os.startfile(settings["target_dir"])
        except Exception: pass
        
    pa = settings.get("post_action", 0)
    if pa == 1:
        clear_console(); print("\n"*5 + center(GREEN + "ZeddiHub Editor se loučí..." + RESET)); time.sleep(1.5); sys.exit()
    elif pa == 2: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif pa == 3: os.system("shutdown /s /t 5")

def exit_confirm_dialog():
    sel = 1
    opts = [f"{t('yes')}", f"{t('no')}"]
    while True:
        clear_console(); print("\n"*10 + YELLOW + center(f"--- {t('exit_q_title')} ---") + RESET + "\n\n")
        for i in range(2):
            if i == sel: print(GREEN + center(f" ►►  {opts[i]}  ◄◄ ") + RESET)
            else: print(CYAN + center(f"     {opts[i]}     ") + RESET)
        print("\n" + "═"*CONSOLE_WIDTH + "\n" + YELLOW + center(t("footer")) + RESET)
        k = read_key_internal()
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                clear_console(); print("\n"*5 + center(GREEN + "Návrat do Launcheru..." + RESET)); time.sleep(1); raise ReturnToLauncher()
            return
        elif k in ['a', 'q', 'esc']: return

def read_key_internal():
    if platform.system() == "Windows":
        try:
            key = msvcrt.getch()
            if key in [b'\x00', b'\xe0']:
                a = msvcrt.getch()
                if a == b'H': return 'w'
                if a == b'P': return 's'
                if a == b'K': return 'a'
                if a == b'M': return 'd'
                return None
            if key == b'\x1b': return 'esc'
            if key in [b'\r', b'\n']: return 'enter'
            if key == b' ': return 'space'
            k = key.decode('utf-8', errors='ignore').lower()
            if k in ['q', 'a', 'p', 'd', 'h', 'n', 't', 'i', 'w', 's', 'o', 'x', 'e']: return k
            return k
        except Exception: return None
    return input().lower()

def read_key(allow_esc_exit=True):
    k = read_key_internal()
    if k == 'esc' and allow_esc_exit:
        exit_confirm_dialog()
        return 'refresh'
    return k

def safe_input(prompt_text):
    print(prompt_text, end='', flush=True); chars = []
    while True:
        if platform.system() != "Windows": return input()
        char = msvcrt.getwch()
        if char == '\x1b': return None
        elif char in ('\r', '\n'): print(); return ''.join(chars)
        elif char == '\x08':
            if chars: chars.pop(); sys.stdout.write('\b \b'); sys.stdout.flush()
        else: chars.append(char); sys.stdout.write(char); sys.stdout.flush()

def print_header():
    clear_console()
    logo = [
        r"  _____  _    _  _____ _______   ______ _____ _____ _______ ____  _____  ",
        r" |  __ \| |  | |/ ____|__   __| |  ____|  __ \_   _|__   __/ __ \|  __ \ ",
        r" | |__) | |  | | (___    | |    | |__  | |  | || |    | | | |  | | |__) |",
        r" |  _  /| |  | |\___ \   | |    |  __| | |  | || |    | | | |  | |  _  / ",
        r" | | \ \| |__| |____) |  | |    | |____| |__| || |_   | | | |__| | | \ \ ",
        r" |_|  \_\\____/|_____/   |_|    |______|_____/_____|  |_|  \____/|_|  \_\\"
    ]
    for line in logo: print(ORANGE + center(line) + RESET)
    print(CYAN + center(f"https://zeddihub.eu  |  Made by ZeddiS  |  {VERSION}") + RESET)
    print(GRAY + center("-" * 70) + RESET)

def render_menu(title, options, sel, descs=None, centered=False, footer=None, preview_box=None, queue_box=None):
    if footer is None: footer = t("footer")
    print_header()
    print(YELLOW + BOLD + center(f"[ {title.upper()} ]") + RESET + "\n")
    max_v = 12; start = max(0, sel - max_v // 2); end = min(len(options), start + max_v)
    if end - start < max_v: start = max(0, end - max_v)
    if centered: print("\n" * max(0, (14 - (end - start)) // 2))

    for i in range(start, end):
        if i == sel:
            print(GREEN + BOLD + center(f"  >>  {options[i]}  <<  ") + RESET)
        else:
            print(CYAN + center(f"      {options[i]}      ") + RESET)
        if descs and i < len(descs) and descs[i]:
            color = WHITE if i == sel else GRAY
            print(color + center(f"  {descs[i]}") + RESET)

    if preview_box:
        print()
        margin = " " * max(0, (CONSOLE_WIDTH - 96) // 2)
        print(margin + CYAN + "+" + "-"*94 + "+" + RESET)
        wrapped = textwrap.wrap(preview_box, width=92)
        for w in wrapped: print(margin + CYAN + "|" + RESET + f" {w.ljust(92)} " + CYAN + "|" + RESET)
        print(margin + CYAN + "+" + "-"*94 + "+" + RESET)

    if queue_box:
        print()
        margin = " " * max(0, (CONSOLE_WIDTH - 96) // 2)
        print(margin + ORANGE + "+" + "-"*94 + "+" + RESET)
        header_txt = "AKTIVNI FRONTA UKOLU"
        hpad = (92 - len(header_txt)) // 2
        print(margin + ORANGE + "|" + RESET + " " * hpad + YELLOW + header_txt + RESET + " " * (92 - hpad - len(header_txt)) + ORANGE + "|" + RESET)
        print(margin + ORANGE + "+" + "-"*94 + "+" + RESET)
        for q_line in queue_box:
            w = textwrap.shorten(q_line, width=90)
            print(margin + ORANGE + "|" + RESET + f" {w.ljust(92)} " + ORANGE + "|" + RESET)
        print(margin + ORANGE + "+" + "-"*94 + "+" + RESET)

    print("\n" + GRAY + center("-" * 80) + RESET)
    print(YELLOW + center(footer) + RESET)

def multi_select_menu(title, options, selected_flags, descs=None, file_details=None, enable_x=False):
    sel = 0
    while True:
        display_opts = [f"{'✅' if selected_flags[i] else '☐'} {options[i]}" for i in range(len(options))]
        footer = "[W/S] Pohyb | [Space/D] Označit | [H] Vše | [N] Nic | [I] Detaily"
        if enable_x: footer += " | [X] Spustit Frontu"
        footer += " | [Enter] Potvrdit"
        
        render_menu(title, display_opts, sel, descs, footer=footer)
        k = read_key()
        
        if k in ['a', 'q', 'esc']: return None
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(options) - 1: sel += 1
        elif k in ['d', 'space']: selected_flags[sel] = not selected_flags[sel]
        elif k == 'h': selected_flags = [True] * len(options)
        elif k == 'n': selected_flags = [False] * len(options)
        elif k == 'x' and enable_x: raise ExecuteQueueNow()
        elif k == 'i' and file_details:
            details_list = file_details.get(options[sel], [{"preview": "Žádné detaily.", "full": "Žádné detaily.", "filepath": None}])
            detail_view(f"DETAILY CHYB: {options[sel]}", details_list)
        elif k == 'enter': return selected_flags

def detail_view(title, lines_data):
    sel = 0
    if not lines_data: return
    while True:
        display = [textwrap.shorten(item["preview"], width=80) for item in lines_data]
        preview_text = lines_data[sel]["full"] if lines_data else ""
        fp = lines_data[sel].get("filepath") if lines_data and isinstance(lines_data[sel], dict) else None
        
        footer = "[W/S] Posun | [Enter] Celý řádek detailně"
        if fp: footer += " | [O] Otevřít soubor"
        footer += " | [A/Esc] Zpět"
        
        render_menu(title, display, sel, footer=footer, preview_box=preview_text)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(display) - 1: sel += 1
        elif k == 'o' and fp:
            if platform.system() == "Windows":
                try: os.startfile(fp)
                except Exception: pass
        elif k in ['d', 'enter', 'space']:
            clear_console(); print(YELLOW + center(f"--- DETAIL ZDROJOVÉHO KÓDU (Řádek {sel+1}) ---") + RESET + "\n")
            wrapped_full = textwrap.wrap(lines_data[sel]["full"], width=96)
            for line in wrapped_full: print(CYAN + line + RESET)
            print("\n" + YELLOW + center("[Enter / Esc] Zpět do seznamu") + RESET)
            while read_key_internal() not in ['enter', 'esc', 'space', 'a', 'd', 'q']: pass

def draw_progress(done_ops, total_ops, elapsed, eta, f_idx, total_f, f_name):
    sys.stdout.write("\033[10;0H\033[J") 
    bar_w = 40; filled_t = int(bar_w * done_ops / total_ops) if total_ops > 0 else bar_w; pct_t = (done_ops / total_ops) * 100 if total_ops > 0 else 100.0
    print(center(CYAN + "┌" + "─" * 88 + "┐" + RESET))
    print(" " * ((CONSOLE_WIDTH - 98) // 2) + f"{CYAN}│{RESET} {YELLOW}CELKOVÝ PRŮBĚH:{RESET} {GRAY}[{RESET}{GREEN}{'█'*filled_t}{RESET}{GRAY}{'░'*(bar_w-filled_t)}{RESET}{GRAY}]{RESET} {pct_t:5.1f}%".ljust(96) + f"{CYAN}│{RESET}")
    filled_f = int(bar_w * f_idx / total_f) if total_f > 0 else bar_w; pct_f = (f_idx / total_f) * 100 if total_f > 0 else 100.0
    print(" " * ((CONSOLE_WIDTH - 98) // 2) + f"{CYAN}│{RESET} {CYAN}SOUBOR ({f_idx}/{total_f}):{RESET} {GRAY}[{RESET}{GREEN}{'█'*filled_f}{RESET}{GRAY}{'░'*(bar_w-filled_f)}{RESET}{GRAY}]{RESET} {pct_f:5.1f}%".ljust(96) + f"{CYAN}│{RESET}")
    print(" " * ((CONSOLE_WIDTH - 98) // 2) + f"{CYAN}│{RESET} ⏱ {GRAY}Čas:{RESET} {format_time(elapsed)} | ⏳ {GRAY}ETA:{RESET} {format_time(eta)}".ljust(96) + f"{CYAN}│{RESET}")
    print(center(CYAN + "└" + "─" * 88 + "┘" + RESET) + "\n" + center(YELLOW + "[P/A] PAUZA a Rychlost | [Esc] Zrušit úkol" + RESET))
    sys.stdout.flush()

def check_cs_validity(path, include_subdirs=False):
    valid, invalid = 0, []
    for root_dir, _, files in os.walk(path):
        for f in files:
            if f.endswith('.cs'):
                try:
                    with open(os.path.join(root_dir, f), 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        if content.count('{') != content.count('}'): invalid.append(f)
                        else: valid += 1
                except Exception: invalid.append(f)
        if not include_subdirs: break
    return valid, invalid

def queue_add(task_type, f_name, **kwargs):
    kwargs.update({"type": task_type, "file": f_name})
    task_queue.append(kwargs)