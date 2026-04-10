import os
import sys
import platform
import time
import traceback
import re
import json
import glob

try:
    import msvcrt
except ImportError:
    pass

if platform.system() == "Windows":
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

VERSION = "v3.0.0"
CONSOLE_WIDTH = 110
CONSOLE_HEIGHT = 48

# === BARVY ===
ORANGE = '\033[38;5;208m'
GOLD = '\033[38;5;220m'
CYAN = '\033[38;5;51m'
GREEN = '\033[38;5;46m'
YELLOW = '\033[38;5;226m'
RED = '\033[38;5;196m'
GRAY = '\033[90m'
DIM = '\033[2m'
BOLD = '\033[1m'
WHITE = '\033[97m'
MAGENTA = '\033[38;5;201m'
RESET = '\033[0m'

def clean_len(text):
    return len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text))

def center(text, width=CONSOLE_WIDTH):
    return " " * max(0, (width - clean_len(text)) // 2) + text

def setup_console():
    if platform.system() == "Windows":
        try:
            import ctypes
            h = ctypes.windll.kernel32.GetStdHandle(-10)
            m = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(m))
            ctypes.windll.kernel32.SetConsoleMode(h, m.value & ~0x0040)
            ctypes.windll.kernel32.SetConsoleTitleW(f"ZeddiHub Tools {VERSION}")
            os.system(f"mode con cols={CONSOLE_WIDTH} lines={CONSOLE_HEIGHT}")

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                user32 = ctypes.windll.user32
                sw = user32.GetSystemMetrics(0)
                sh = user32.GetSystemMetrics(1)
                user32.SetWindowPos(hwnd, 0, (sw - 920) // 2, (sh - 780) // 2, 0, 0, 0x0001)
        except Exception:
            pass

def clear_console():
    sys.stdout.write("\033[2J\033[H")

def print_header():
    clear_console()
    logo_lines = [
        r"  ______         _     _ _ _    _       _      ",
        r" |___  /        | |   | (_) |  | |     | |     ",
        r"    / /  ___  __| | __| |_| |__| |_   _| |__   ",
        r"   / /  / _ \/ _` |/ _` | |  __  | | | | '_ \  ",
        r"  / /__| ___/ (_| | (_| | | |  | | |_| | |_) | ",
        r" /_____|\___|\__,_|\__,_|_|_|  |_|\__,_|_.__/  ",
    ]

    box_w = 60
    left_pad = (CONSOLE_WIDTH - box_w) // 2
    pad = " " * left_pad

    print()
    print(ORANGE + pad + "+" + "=" * (box_w - 2) + "+" + RESET)
    print(ORANGE + pad + "|" + " " * (box_w - 2) + "|" + RESET)
    for line in logo_lines:
        inner = line.center(box_w - 2)
        print(ORANGE + pad + "|" + GOLD + inner + ORANGE + "|" + RESET)
    print(ORANGE + pad + "|" + " " * (box_w - 2) + "|" + RESET)

    tag = f"TOOLS LAUNCHER {VERSION}"
    tag_inner = tag.center(box_w - 2)
    print(ORANGE + pad + "|" + WHITE + BOLD + tag_inner + RESET + ORANGE + "|" + RESET)

    print(ORANGE + pad + "|" + " " * (box_w - 2) + "|" + RESET)
    print(ORANGE + pad + "+" + "=" * (box_w - 2) + "+" + RESET)

    print(CYAN + center("https://zeddihub.eu  |  Made by ZeddiS  |  dsc.gg/zeddihub") + RESET)
    print()

def read_key():
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
        except Exception: return None
    return input().lower()

def draw_separator(char="=", color=GRAY):
    print(color + center(char * (CONSOLE_WIDTH - 10)) + RESET)

def draw_tool_status():
    tools = [
        ("Rust Editor", "zeddihub_rust_editor"),
        ("CS:GO Tools", "zeddihub_csgo_tools"),
        ("CS2 Tools", "zeddihub_cs2_tools"),
        ("Translator", "zeddihub_translator"),
        ("Server Status", "zeddihub_server_status")
    ]
    statuses = []
    for name, folder in tools:
        path = os.path.join(current_dir, folder)
        if os.path.isdir(path):
            statuses.append(f"{GREEN}[OK]{RESET} {name}")
        else:
            statuses.append(f"{RED}[--]{RESET} {name}")
    print(GRAY + center("   ".join(statuses)) + RESET)

def reset_all_settings():
    """Reset all module configs to factory defaults."""
    # When frozen, configs live in <exe_dir>/data/<module>/
    if getattr(sys, 'frozen', False):
        data_root = os.path.join(os.path.dirname(sys.executable), "data")
    else:
        data_root = current_dir
    configs = [
        os.path.join(data_root, "zeddihub_rust_editor", "editor_config.json"),
        os.path.join(data_root, "zeddihub_csgo_tools", "csgo_config.json"),
        os.path.join(data_root, "zeddihub_cs2_tools", "cs2_config.json"),
        os.path.join(data_root, "zeddihub_translator", "config.json"),
        os.path.join(data_root, "zeddihub_server_status", "status_config.json"),
    ]
    count = 0
    for cfg in configs:
        if os.path.exists(cfg):
            os.remove(cfg)
            count += 1
    print_header()
    if count > 0:
        print("\n" * 4 + GREEN + center(f"Smazáno {count} konfiguračních souborů.") + RESET)
        print(WHITE + center("Všechny moduly byly resetovány do továrního nastavení.") + RESET)
    else:
        print("\n" * 4 + YELLOW + center("Žádné konfigurační soubory nebyly nalezeny.") + RESET)
    time.sleep(2)

def credits_menu():
    import webbrowser
    sel = 0
    opts = [
        "🌐 Web (zeddihub.eu)",
        "📖 ZeddiWiki (wiki.zeddihub.eu)",
        "👨‍💻 ZeddiS (zeddis.xyz)",
        "🐙 GitHub (github.com/ZeddiS)",
        "💬 Discord (dsc.gg/zeddihub)",
        f"✨ Verze: {VERSION}"
    ]
    descs = [
        "Oficiální web ZeddiHub komunity.",
        "Wiki s návody a dokumentací.",
        "Portfolio a kontakt na autora.",
        "Repozitáře a open-source projekty.",
        "Komunitní Discord server.",
        ""
    ]
    while True:
        print_header()
        print(YELLOW + center("CREDITS A ODKAZY") + RESET)
        draw_separator("-", CYAN)
        print()
        for i in range(len(opts)):
            if i == sel:
                print(GREEN + center(f"  >>  {opts[i]}  <<  ") + RESET)
                if descs[i]:
                    print(WHITE + center(descs[i]) + RESET)
            else:
                print(CYAN + center(f"      {opts[i]}      ") + RESET)
                if descs[i]:
                    print(DIM + GRAY + center(descs[i]) + RESET)
            print()
        draw_separator()
        print(YELLOW + center("[W/S] Pohyb | [D/Enter] Otevřít | [A/Esc] Zpět") + RESET)
        k = read_key()
        if k in ['esc', 'q', 'a']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: webbrowser.open("https://zeddihub.eu")
            elif sel == 1: webbrowser.open("https://wiki.zeddihub.eu")
            elif sel == 2: webbrowser.open("https://zeddis.xyz")
            elif sel == 3: webbrowser.open("https://github.com/ZeddiS")
            elif sel == 4: webbrowser.open("https://dsc.gg/zeddihub")

def launch_module(name, import_func):
    try:
        mod = import_func()
        mod()
        setup_console()
    except Exception:
        print_header()
        print("\n" * 2 + RED + center(f"CHYBA: Nelze načíst {name}!") + RESET + "\n")
        for line in traceback.format_exc().splitlines():
            print(center(line[:100]))
        print("\n" + YELLOW + center("[Stiskněte libovolnou klávesu pro návrat]") + RESET)
        read_key()

def main():
    setup_console()
    sel = 0
    opts = [
        "🔧 Spustit ZeddiHub Rust Editor",
        "🎯 Spustit ZeddiHub CS:GO Tools",
        "🎮 Spustit ZeddiHub CS2 Tools",
        "🌍 Spustit ZeddiHub Translator",
        "📡 Spustit ZeddiHub Server Status",
        "⚙️ Resetovat všechna nastavení",
        "🌟 Credits a Odkazy"
    ]
    icons = ["RUST", "CSGO", "CS2 ", "LANG", "STAT", "RSET", "INFO"]
    descs = [
        "Nástroje pro opravy, kompilace a úpravy Rust pluginů.",
        "Editor databází a generátory configů pro CS:GO servery.",
        "Crosshair, Viewmodel, Autoexec, Server.cfg pro Counter-Strike 2.",
        "Komplexní nástroj pro hromadný překlad souborů.",
        "Monitoring stavu herních serverů v reálném čase.",
        "Smaže všechny konfigurace a obnoví tovární nastavení.",
        "Odkazy na komunitu, wiki a kontakty."
    ]
    colors = [ORANGE, CYAN, MAGENTA, GREEN, YELLOW, RED, GRAY]

    while True:
        print_header()
        draw_tool_status()
        print()
        draw_separator("-", CYAN)
        print()

        for i in range(len(opts)):
            icon = f"[{icons[i]}]"
            if i == sel:
                c = colors[i]
                print(c + BOLD + center(f"  >>  {icon} {opts[i]}  <<  ") + RESET)
                print(WHITE + center(descs[i]) + RESET)
            else:
                print(GRAY + center(f"      {icon} {opts[i]}      ") + RESET)
                print(DIM + GRAY + center(descs[i]) + RESET)
            print()

        draw_separator()
        print(YELLOW + center("[W/S] Pohyb | [D/Enter] Spustit | [Esc] Ukončit") + RESET)

        k = read_key()
        if k in ['esc', 'q']:
            clear_console()
            print("\n" * 5 + GREEN + center("Děkujeme za použití ZeddiHub Tools!") + RESET)
            print(GRAY + center("https://zeddihub.eu") + RESET)
            time.sleep(1.5)
            sys.exit()
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                def imp():
                    from zeddihub_rust_editor.menus import start_editor
                    return start_editor
                launch_module("Rust Editor", imp)
            elif sel == 1:
                def imp():
                    from zeddihub_csgo_tools.menus import start_editor
                    return start_editor
                launch_module("CS:GO Tools", imp)
            elif sel == 2:
                def imp():
                    from zeddihub_cs2_tools.menus import start_editor
                    return start_editor
                launch_module("CS2 Tools", imp)
            elif sel == 3:
                def imp():
                    from zeddihub_translator.main import start_translator
                    return start_translator
                launch_module("Translator", imp)
            elif sel == 4:
                def imp():
                    from zeddihub_server_status.main import start_server_status
                    return start_server_status
                launch_module("Server Status", imp)
            elif sel == 5:
                reset_all_settings()
            elif sel == 6:
                credits_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        print(f"\nCRITICAL LAUNCHER ERROR: {e}")
        traceback.print_exc()
        input("Stiskněte Enter pro zavření...")
