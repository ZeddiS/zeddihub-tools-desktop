import os
import json
import time
import sys
import shutil
import platform
import tkinter as tk
from datetime import datetime
import re
import textwrap
from .langs import L

try:
    import msvcrt
except ImportError:
    pass

VERSION = "v3.2.0 CS:GO Ultimate"
CONSOLE_WIDTH = 100
CONSOLE_HEIGHT = 45 

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "csgo_config.json")
os.makedirs(SCRIPT_DIR, exist_ok=True)

ORANGE = '\033[38;5;208m'
CYAN = '\033[38;5;51m'
GREEN = '\033[38;5;46m'
YELLOW = '\033[38;5;226m'
RED = '\033[38;5;196m'
GRAY = '\033[90m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
WHITE = '\033[97m'

settings = {
    "ui_lang": "cz", 
    "source_dir": "", 
    "target_dir": "", 
    "backup_dir": os.path.join(SCRIPT_DIR, "backups"),
    "auto_backup": True,
    "open_folder_after": True
}

class ReturnToLauncher(Exception): 
    pass

def t(key): 
    return L.get(settings.get("ui_lang", "cz"), L["cz"]).get(key, key)

def save_settings():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def load_settings():
    global settings
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if k in settings:
                        settings[k] = v
        except Exception: 
            pass
        return True
    return False

def clean_len(text): 
    return len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text))

def center(text, width=CONSOLE_WIDTH): 
    return " " * max(0, (width - clean_len(text)) // 2) + text

def clear_console(): 
    sys.stdout.write("\033[2J\033[H")

def setup_console():
    if platform.system() == "Windows":
        try:
            import ctypes
            h = ctypes.windll.kernel32.GetStdHandle(-10)
            m = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(m))
            ctypes.windll.kernel32.SetConsoleMode(h, m.value & ~0x0040)
            ctypes.windll.kernel32.SetConsoleTitleW(f"★ ZeddiHub CS:GO Tools {VERSION} ★")
            os.system(f"mode con cols={CONSOLE_WIDTH} lines={CONSOLE_HEIGHT}")
        except Exception: 
            pass

def get_backup_name(original_filename):
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{original_filename}_backup_{stamp}.bak"

def exit_confirm_dialog():
    sel = 1
    opts = [f"{t('yes')}", f"{t('no')}"]
    while True:
        clear_console()
        print("\n"*10 + YELLOW + center(f"--- {t('exit_q_title')} ---") + RESET + "\n\n")
        for i in range(2):
            if i == sel:
                print(GREEN + center(f" ►►  {opts[i]}  ◄◄ ") + RESET)
            else:
                print(CYAN + center(f"     {opts[i]}     ") + RESET)
                
        print("\n" + "═"*CONSOLE_WIDTH + "\n" + YELLOW + center(t("footer")) + RESET)
        
        k = read_key_internal()
        if k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < 1:
            sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                clear_console()
                print("\n"*5 + center(GREEN + "Návrat do Launcheru..." + RESET))
                time.sleep(1)
                raise ReturnToLauncher()
            return
        elif k in ['a', 'q', 'esc']:
            return

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
            if key == b'\x1b':
                return 'esc'
            if key in [b'\r', b'\n']:
                return 'enter'
            if key == b' ':
                return 'space'
            k = key.decode('utf-8', errors='ignore').lower()
            if k in ['q', 'a', 'p', 'd', 'h', 'n', 't', 'i', 'w', 's', 'o', 'x', 'e']:
                return k
            return k
        except Exception:
            return None
    return input().lower()

def read_key(allow_esc_exit=True):
    k = read_key_internal()
    if k == 'esc' and allow_esc_exit:
        exit_confirm_dialog()
        return 'refresh'
    return k

def safe_input(prompt_text):
    print(prompt_text, end='', flush=True)
    chars = []
    while True:
        if platform.system() != "Windows": 
            return input()
            
        char = msvcrt.getwch()
        if char == '\x1b': 
            return None
        elif char in ('\r', '\n'):
            print()
            return ''.join(chars)
        elif char == '\x08':
            if chars:
                chars.pop()
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        elif char == '\x16': # Podpora pro Ctrl+V
            try:
                root = tk.Tk()
                root.withdraw()
                clip_text = root.clipboard_get()
                root.destroy()
                for c in clip_text:
                    if c not in ('\r', '\n'):
                        chars.append(c)
                        sys.stdout.write(c)
                sys.stdout.flush()
            except Exception: 
                pass
        else:
            chars.append(char)
            sys.stdout.write(char)
            sys.stdout.flush()

def print_header():
    clear_console()
    logo = [
        r"   _____  _____    _____  ____    _______ ____   ____  _       _____ ",
        r"  / ____|/ ____|  / ____|/ __ \  |__   __/ __ \ / __ \| |     / ____|",
        r" | |    | (___   | |  __| |  | |    | | | |  | | |  | | |    | (___  ",
        r" | |     \___ \  | | |_ | |  | |    | | | |  | | |  | | |     \___ \ ",
        r" | |____ ____) | | |__| | |__| |    | | | |__| | |__| | |____ ____) |",
        r"  \_____|_____/   \_____|\____/     |_|  \____/ \____/|______|_____/ "
    ]
    for line in logo:
        print(ORANGE + center(line) + RESET)
    print(CYAN + center(f"https://zeddihub.eu  |  Made by ZeddiS  |  {VERSION}") + RESET)
    print(GRAY + center("-" * 70) + RESET)

def render_menu(title, options, sel, descs=None, centered=False, footer=None, extra_art=None):
    if footer is None:
        footer = t("footer")

    print_header()
    print(YELLOW + BOLD + center(f"[ {title.upper()} ]") + RESET + "\n")

    max_v = 12
    start = max(0, sel - max_v // 2)
    end = min(len(options), start + max_v)
    if end - start < max_v:
        start = max(0, end - max_v)

    if centered:
        print("\n" * max(0, (14 - (end - start)) // 2))

    for i in range(start, end):
        if i == sel:
            print(GREEN + BOLD + center(f"  >>  {options[i]}  <<  ") + RESET)
        else:
            print(CYAN + center(f"      {options[i]}      ") + RESET)

        if descs and i < len(descs) and descs[i]:
            color = WHITE if i == sel else GRAY
            print(color + center(f"  {descs[i]}") + RESET)

    if extra_art:
        print()
        for line in extra_art:
            print(center(line))

    print("\n" + GRAY + center("-" * 80) + RESET)
    print(YELLOW + center(footer) + RESET)

def multi_select_menu(title, options, selected_flags, descs=None):
    sel = 0
    while True:
        display_opts = [f"{'✅' if selected_flags[i] else '☐'} {options[i]}" for i in range(len(options))]
        render_menu(title, display_opts, sel, descs, footer="[W/S] Pohyb | [Space/D] Označit | [H] Vše | [N] Nic | [Enter] Potvrdit")
        k = read_key()
        
        if k in ['a', 'q', 'esc']:
            return None
        elif k == 'w' and sel > 0:
            sel -= 1
        elif k == 's' and sel < len(options) - 1:
            sel += 1
        elif k in ['d', 'space']:
            selected_flags[sel] = not selected_flags[sel]
        elif k == 'h':
            selected_flags = [True] * len(options)
        elif k == 'n':
            selected_flags = [False] * len(options)
        elif k == 'enter':
            return selected_flags