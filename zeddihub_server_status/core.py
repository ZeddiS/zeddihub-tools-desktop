import os
import json
import time
import sys
import platform
import re
import tkinter as tk
from .langs import L

try:
    import msvcrt
except ImportError:
    pass

VERSION = "v3.0.0"
CONSOLE_WIDTH = 110
CONSOLE_HEIGHT = 48

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "status_config.json")

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
MAGENTA = '\033[38;5;201m'
BLUE = '\033[38;5;33m'

settings = {
    "ui_lang": "cz",
    "servers": [],
    "refresh_interval": 15,
    "auto_refresh": True
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
            ctypes.windll.kernel32.SetConsoleTitleW(f"ZeddiHub Server Status {VERSION}")
            os.system(f"mode con cols={CONSOLE_WIDTH} lines={CONSOLE_HEIGHT}")
        except Exception:
            pass


def exit_confirm_dialog():
    sel = 1
    opts = [t('yes'), t('no')]
    while True:
        clear_console()
        print("\n" * 10 + YELLOW + center(f"--- {t('exit_q_title')} ---") + RESET + "\n\n")
        for i in range(2):
            if i == sel:
                print(GREEN + BOLD + center(f"  >>  {opts[i]}  <<  ") + RESET)
            else:
                print(CYAN + center(f"      {opts[i]}      ") + RESET)
        print("\n" + GRAY + center("-" * 80) + RESET)
        print(YELLOW + center(t("footer")) + RESET)
        k = read_key_internal()
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                clear_console()
                print("\n" * 5 + center(GREEN + "Navrat do Launcheru..." + RESET))
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
            if key == b'\x1b': return 'esc'
            if key in [b'\r', b'\n']: return 'enter'
            if key == b' ': return 'space'
            k = key.decode('utf-8', errors='ignore').lower()
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
        if char == '\x1b': return None
        elif char in ('\r', '\n'):
            print()
            return ''.join(chars)
        elif char == '\x08':
            if chars:
                chars.pop()
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        elif char == '\x16':
            try:
                root = tk.Tk(); root.withdraw()
                clip_text = root.clipboard_get(); root.destroy()
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
        r"   ___                          ___ _        _           ",
        r"  / __| ___ _ ___ _____ _ _    / __| |_ __ _| |_ _  _ ___",
        r"  \__ \/ -_) '_\ V / -_) '_|   \__ \  _/ _` |  _| || (_-<",
        r"  |___/\___|_|  \_/\___|_|     |___/\__\__,_|\__|\_,_/__/"
    ]
    for line in logo:
        print(BLUE + center(line) + RESET)
    print(CYAN + center(f"https://zeddihub.eu  |  Made by ZeddiS  |  {VERSION}") + RESET)
    print(GRAY + center("-" * 70) + RESET)


def render_menu(title, options, sel, descs=None, centered=False, footer=None):
    if footer is None:
        footer = t("footer")
    print_header()
    print(YELLOW + BOLD + center(f"[ {title.upper()} ]") + RESET + "\n")
    max_v = 14
    start = max(0, sel - max_v // 2)
    end = min(len(options), start + max_v)
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
    print("\n" + GRAY + center("-" * 90) + RESET)
    print(YELLOW + center(footer) + RESET)
