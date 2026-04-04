import os
import json
import time
import sys
import shutil
import platform
import tkinter as tk
from tkinter import colorchooser
from datetime import datetime
import ctypes
import re
import textwrap
import urllib.request
import urllib.parse
import threading

try:
    import msvcrt
except ImportError:
    pass

try:
    import winsound
except ImportError:
    winsound = None

from .langs import L, SUPPORTED_LANGS

VERSION = "v3.0.0"
CONSOLE_WIDTH = 110
CONSOLE_HEIGHT = 48
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ZH_DIR = SCRIPT_DIR
CONFIG_PATH = os.path.join(ZH_DIR, "config.json")

ORANGE, CYAN, GREEN, YELLOW, RED, PURPLE, GRAY, RESET = '\033[38;5;208m', '\033[38;5;51m', '\033[38;5;46m', '\033[38;5;226m', '\033[38;5;196m', '\033[38;5;201m', '\033[90m', '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
WHITE = '\033[97m'
SPEEDS = [0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.001]

settings = {
    "ui_lang": "cz", "selected_langs": ["cs", "ru", "de", "es"], 
    "source_dir": "", "target_dir": "",
    "source_lang": "en", "file_extension": ".json", 
    "translator_engine": "combined_free", "api_key": "",
    "write_speed": 0.01, "prefix_enabled": False, "prefix_text": "Nevyplněno",
    "prefix_color": "#ff8c00", "prefix_sync_color": False, "prefix_bracket_color": "#ffffff", "prefix_use_brackets": False,
    "prefix_detect_old": True, "smart_cache": True, "auto_backup": True,
    "backup_dir": os.path.join(ZH_DIR, "backups"), "log_dir": os.path.join(ZH_DIR, "logs"),
    "post_action": 0
}

SESSION_LOG_FILE = ""

def t(key): return L.get(settings.get("ui_lang", "en"), L["en"]).get(key, key)

def save_settings():
    os.makedirs(ZH_DIR, exist_ok=True)
    with open(os.path.join(ZH_DIR, "config.json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def load_settings():
    global settings
    config_path = os.path.join(ZH_DIR, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if k in settings: settings[k] = v
        except: pass
        return True
    return False

def init_session_log():
    global SESSION_LOG_FILE
    os.makedirs(settings["log_dir"], exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    SESSION_LOG_FILE = os.path.join(settings["log_dir"], f"Log_{stamp}.txt")
    write_log(f"=== ZEDDIHUB TRANSLATOR {VERSION} - LOG SESSION START ===")

def write_log(action_text):
    global SESSION_LOG_FILE
    if not SESSION_LOG_FILE: init_session_log()
    try:
        with open(SESSION_LOG_FILE, "a", encoding="utf-8") as f:
            stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{stamp}] {action_text}\n")
    except: pass

def get_backup_name(original_filename):
    return f"{original_filename}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h:02d}h {m:02d}m"
    return f"{m:02d}:{s:02d}"

class ProgressWindow:
    def __init__(self):
        self.root = None
        self.text_widget = None
        self.is_running = False
        self.auto_scroll = None
        self.q = __import__('queue').Queue()

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
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.lower()
        if platform.system() == "Windows":
            try:
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd: ctypes.windll.user32.SetForegroundWindow(hwnd)
            except: pass

        self._process_queue()
        self.root.mainloop()

    def _process_queue(self):
        try:
            while not self.q.empty():
                msg = self.q.get_nowait()
                if msg == "[[CLOSE]]":
                    self._on_close()
                    return
                elif msg == "[[FRONT]]":
                    self.root.attributes('-topmost', True)
                    self.root.attributes('-topmost', False)
                    self.root.lift()
                else:
                    self.text_widget.insert(tk.END, msg + "\n")
                    if self.auto_scroll and self.auto_scroll.get():
                        self.text_widget.see(tk.END)
        except Exception: pass
        if self.is_running:
            self.root.after(50, self._process_queue)

    def _on_close(self):
        self.is_running = False
        try: self.root.destroy()
        except: pass

    def start(self, title):
        t_thread = threading.Thread(target=self._run, args=(title,), daemon=True)
        t_thread.start()
        time.sleep(0.5)

    def log(self, msg):
        self.q.put(msg)

    def bring_to_front(self):
        self.q.put("[[FRONT]]")

    def close(self):
        self.q.put("[[CLOSE]]")

def hex_to_ansi(hex_str):
    try:
        h = hex_str.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return f"\033[38;2;{r};{g};{b}m"
    except: return RESET

def clean_len(text): return len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text))

def center(text, width=CONSOLE_WIDTH):
    return " " * max(0, (width - clean_len(text)) // 2) + text

def box_center(raw_text, colored_text, width=96):
    pad = max(0, width - clean_len(raw_text))
    lp = " " * (pad // 2)
    rp = " " * (pad - len(lp))
    margin = " " * ((CONSOLE_WIDTH - (width + 2)) // 2)
    return margin + f"{CYAN}│{RESET}{lp}{colored_text}{rp}{CYAN}│{RESET}"

def box_left(raw_text, colored_text, width=94):
    pad = max(0, width - clean_len(raw_text))
    margin = " " * ((CONSOLE_WIDTH - (width + 4)) // 2)
    return margin + f"{CYAN}│{RESET} {colored_text}{' '*pad} {CYAN}│{RESET}"

def draw_box_line(ansi_txt, raw_txt, width=94):
    pad = max(0, width - clean_len(raw_txt))
    margin = " " * ((CONSOLE_WIDTH - (width + 2)) // 2)
    print(margin + f"{CYAN}│{RESET} {ansi_txt}{' '*pad} {CYAN}│{RESET}")

def clear_console():
    sys.stdout.write("\033[2J\033[H")

def setup_console():
    if platform.system() == "Windows":
        try:
            h = ctypes.windll.kernel32.GetStdHandle(-10)
            m = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(m))
            ctypes.windll.kernel32.SetConsoleMode(h, m.value & ~0x0040)
            ctypes.windll.kernel32.SetConsoleTitleW(f"★ ZeddiHub Translator {VERSION} ★")
            os.system(f"mode con cols={CONSOLE_WIDTH} lines={CONSOLE_HEIGHT}")
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                u32 = ctypes.windll.user32
                style = u32.GetWindowLongW(hwnd, -16)
                u32.SetWindowLongW(hwnd, -16, style & ~0x00010000 & ~0x00040000)
                sw, sh = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
                u32.SetWindowPos(hwnd, 0, (sw-800)//2, (sh-700)//2, 0, 0, 0x0001)
        except: pass

def do_post_action():
    if settings["post_action"] == 1: exit_app()
    elif settings["post_action"] == 2: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif settings["post_action"] == 3: os.system("shutdown /s /t 5")

def exit_app():
    clear_console()
    print("\n"*5 + center(GREEN + "ZeddiHub Translator se loučí..." + RESET))
    print(center(GRAY + t("quote") + RESET))
    time.sleep(2)
    sys.exit()

def exit_confirm_dialog():
    sel = 1
    opts = [f"{t('yes')}", f"{t('no')}"]
    while True:
        clear_console()
        print("\n"*10 + YELLOW + center(f"--- {t('exit_q_title')} ---") + RESET + "\n\n")
        for i in range(2):
            if i == sel: print(GREEN + center(f" ►►  {opts[i]}  ◄◄ ") + RESET)
            else: print(CYAN + center(f"     {opts[i]}     ") + RESET)
        print("\n" + "═"*CONSOLE_WIDTH)
        print(YELLOW + center("[W/S] Pohyb | [D] Vybrat") + RESET)
        
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: exit_app()
            return
        elif k in ['a', 'q', 'esc']: return

def read_key(allow_esc_exit=True):
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
                if allow_esc_exit:
                    exit_confirm_dialog()
                    return 'refresh'
                return 'esc'
            k = key.decode('utf-8').lower()
            if k in ['\r', '\n']: return 'enter'
            if k == ' ': return 'space'
            if k in ['q', 'a', 'p', 'd', 't']: return k
            return k
        except: return None
    return input().lower()

def safe_input(prompt_text):
    print(prompt_text, end='', flush=True)
    chars = []
    while True:
        if platform.system() != "Windows": return input()
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
                clip = root.clipboard_get()
                root.destroy()
                chars.extend(list(clip))
                sys.stdout.write(clip)
                sys.stdout.flush()
            except: pass
        else:
            chars.append(char)
            sys.stdout.write(char)
            sys.stdout.flush()

def print_header():
    clear_console()
    logo = [
        r"  ______ ______ _____  _____ _____ _    _ _    _ ____  ",
        r" |___  /|  ____|  __ \|  __ \_   _| |  | | |  | |  _ \ ",
        r"    / / | |__  | |  | | |  | || | | |__| | |  | | |_) |",
        r"   / /  |  __| | |  | | |  | || | |  __  | |  | |  _ < ",
        r"  / /__ | |____| |__| | |__| || |_| |  | | |__| | |_) |",
        r" /_____||______|_____/|_____/_____|_|  |_|\____/|____/ "
    ]
    for line in logo: print(ORANGE + center(line) + RESET)
    print(CYAN + center(f"https://zeddihub.eu  |  Made by ZeddiS  |  {VERSION}") + RESET)
    print(GRAY + center("-" * 65) + RESET)

def render_menu(title, options, sel, descs=None, centered=False, footer=None):
    print_header()
    print(YELLOW + BOLD + center(f"[ {title.upper()} ]") + RESET + "\n")
    max_v = 12
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

    print("\n" + GRAY + center("-" * 80) + RESET)
    print(YELLOW + center(footer if footer else t("footer")) + RESET)

def choose_color_custom(current_hex):
    print_header()
    print(YELLOW + center(t("col_sel")) + RESET + "\n"*4)
    print(CYAN + center(t("hex_prompt")) + RESET)
    print(GRAY + center(t("hex_empty")) + RESET + "\n")
    c = safe_input(center(t("inp_esc") + "\n\n" + center(t("your_choice"))))
    if c is None: return current_hex
    c = c.strip()
    if c:
        if not c.startswith("#"): c = "#" + c
        if len(c) == 7: return c
        return current_hex
    else:
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        res = colorchooser.askcolor(initialcolor=current_hex)[1]; root.destroy()
        return res if res else current_hex

def protect_placeholders(text):
    pattern = re.compile(r'(\{[^}]+\})|(<[^>]+>)|(\*[^*]+\*)|(%[^%\s]+%)|(\[[^\]]+\])|(%\w)')
    placeholders = []
    def replacer(m):
        placeholders.append(m.group(0))
        return f" __{len(placeholders)-1}__ "
    protected_text = pattern.sub(replacer, str(text))
    return protected_text, placeholders

def restore_placeholders(text, placeholders):
    for i, p in enumerate(placeholders):
        pattern = re.compile(r'__\s*' + str(i) + r'\s*__')
        text = pattern.sub(p, text)
    return text.replace("  ", " ").strip()

def free_google_translate(text, target_lang):
    if target_lang.lower() in ["en-gb", "en-us"]: target_lang = "en"
    if target_lang.lower() == "pt-br": target_lang = "pt"
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        res = json.loads(response.read().decode('utf-8'))
        return "".join([t[0] for t in res[0] if t[0]])

def free_lingva_translate(text, source_lang, target_lang):
    if source_lang.lower() in ["en-gb", "en-us"]: source_lang = "en"
    if target_lang.lower() in ["en-gb", "en-us"]: target_lang = "en"
    url = f"https://lingva.ml/api/v1/{source_lang}/{target_lang}/{urllib.parse.quote(text)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        res = json.loads(response.read().decode('utf-8'))
        return res.get("translation", text)

def free_mymemory_translate(text, source_lang, target_lang):
    if source_lang.lower() in ["en-gb", "en-us"]: source_lang = "en"
    if target_lang.lower() in ["en-gb", "en-us"]: target_lang = "en"
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={source_lang}|{target_lang}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        res = json.loads(response.read().decode('utf-8'))
        return res["responseData"]["translatedText"]

def free_libre_translate(text, target_lang):
    if target_lang.lower() in ["en-gb", "en-us"]: target_lang = "en"
    url = "https://translate.terraprint.co/translate"
    data = urllib.parse.urlencode({"q": text, "source": "auto", "target": target_lang, "format": "text"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode('utf-8'))["translatedText"]

def combined_free_translate(text, source_lang, target_lang):
    try: return free_google_translate(text, target_lang)
    except: pass
    try: return free_lingva_translate(text, source_lang, target_lang)
    except: pass
    try: return free_libre_translate(text, target_lang)
    except: pass
    try: return free_mymemory_translate(text, source_lang, target_lang)
    except: pass
    raise Exception("API_RATE_LIMIT")

def translate_text_safe(text, target_lang, engine, api_key="", source_lang="en"):
    prot_text, placeholders = protect_placeholders(text)
    if engine == "deepl_api":
        import deepl
        tr = deepl.Translator(api_key)
        dl_lang = target_lang.upper()
        if dl_lang == "EN": dl_lang = "EN-GB"
        if dl_lang == "PT": dl_lang = "PT-BR"
        translated = tr.translate_text(prot_text, target_lang=dl_lang).text
    elif engine == "google_free":
        translated = free_google_translate(prot_text, target_lang)
    elif engine == "libre_free":
        translated = free_libre_translate(prot_text, target_lang)
    else:
        translated = combined_free_translate(prot_text, source_lang, target_lang)
    return restore_placeholders(translated, placeholders)

def apply_prefix(text):
    if not settings["prefix_enabled"]: return text
    if settings["prefix_detect_old"]:
        text = re.sub(r'^(\[.*?\]|<color=.*?>\[.*?\]</color>|<color=.*?>.*?</color>)\s*', '', text).strip()
    if not settings["prefix_text"] or settings["prefix_text"].lower() == "nevyplněno": return text
    p_c = f"<color={settings['prefix_color']}>{settings['prefix_text']}</color>"
    if settings["prefix_use_brackets"]:
        b_c = settings["prefix_color"] if settings.get("prefix_sync_color") else settings["prefix_bracket_color"]
        return f"<color={b_c}>[</color>{p_c}<color={b_c}>]</color> {text}"
    return f"{p_c} {text}"

def parse_file_for_translation(filepath):
    ext = settings["file_extension"]
    with open(filepath, 'r', encoding='utf-8') as f:
        if ext == ".json":
            d = json.load(f)
            keys = [k for k, v in d.items() if isinstance(v, str) and v.strip()]
            return d, keys, "json"
        else:
            lines = f.read().splitlines()
            keys = [i for i, l in enumerate(lines) if l.strip() and any(c.isalpha() for c in l)]
            return lines, keys, "text"

def draw_progress(done_ops, total_ops, lang_done, lang_total, file_done, file_total, elapsed, eta, lang, f_idx, total_f, f_name):
    sys.stdout.write("\033[10;0H\033[J") 
    bar_w = 40
    filled_t = int(bar_w * done_ops // total_ops) if total_ops > 0 else 0
    print(center(CYAN + "┌" + "─"*88 + "┐" + RESET))
    raw_bar_t = f"[{'█'*filled_t}{'░'*(bar_w-filled_t)}] {(done_ops/total_ops)*100:5.1f}%"
    col_bar_t = f"{GRAY}[{RESET}{GREEN}{'█'*filled_t}{RESET}{GRAY}{'░'*(bar_w-filled_t)}{RESET}{GRAY}]{RESET} {(done_ops/total_ops)*100:5.1f}%"
    print(box_center(f"CELKOVÝ PRŮBĚH: {raw_bar_t}", f"{YELLOW}CELKOVÝ PRŮBĚH:{RESET} {col_bar_t}"))
    
    filled_l = int(bar_w * lang_done // lang_total) if lang_total > 0 else 0
    raw_bar_l = f"[{'█'*filled_l}{'░'*(bar_w-filled_l)}] {(lang_done/lang_total)*100:5.1f}%"
    col_bar_l = f"{GRAY}[{RESET}{GREEN}{'█'*filled_l}{RESET}{GRAY}{'░'*(bar_w-filled_l)}{RESET}{GRAY}]{RESET} {(lang_done/lang_total)*100:5.1f}%"
    print(box_center(f"JAZYK ({lang.upper()}): {raw_bar_l}", f"{PURPLE}JAZYK ({lang.upper()}):{RESET} {col_bar_l}"))

    filled_f = int(bar_w * file_done // file_total) if file_total > 0 else 0
    raw_bar_f = f"[{'█'*filled_f}{'░'*(bar_w-filled_f)}] {(file_done/file_total)*100:5.1f}%"
    col_bar_f = f"{GRAY}[{RESET}{GREEN}{'█'*filled_f}{RESET}{GRAY}{'░'*(bar_w-filled_f)}{RESET}{GRAY}]{RESET} {(file_done/file_total)*100:5.1f}%"
    print(box_center(f"SOUBOR ({f_idx}/{total_f}): {raw_bar_f}", f"{CYAN}SOUBOR ({f_idx}/{total_f}):{RESET} {col_bar_f}"))

    raw_time = f"⏱ Čas: {format_time(elapsed)} | ⏳ ETA: {format_time(eta)}"
    col_time = f"⏱ {GRAY}Čas:{RESET} {format_time(elapsed)} | ⏳ {GRAY}ETA:{RESET} {format_time(eta)}"
    print(box_center(raw_time, col_time))
    
    print(center(CYAN + "└" + "─"*88 + "┘" + RESET))
    print(center(YELLOW + "[P/A] PAUZA a Rychlost | [Esc] Zrušit překlad" + RESET))
    sys.stdout.flush()

def pause_menu():
    sel = 0
    while True:
        spd_idx = SPEEDS.index(settings['write_speed'])
        vis_fill = len(SPEEDS) - spd_idx
        bar = "█" * vis_fill + "░" * (len(SPEEDS) - vis_fill)
        spd_txt = f"[{bar}]"
        pa_opts = [t("pa_none"), t("pa_exit"), t("pa_sleep"), t("pa_shutdown")]
        opts = [t("resume"), f"{t('o_speed')}: {spd_txt}", f"{t('post_action')}: {pa_opts[settings.get('post_action', 0)]}", t("m_exit_menu")]
        render_menu(t("pause_title"), opts, sel, footer="[W/S] Pohyb | [D] Vybrat | [P/A] Pokračovat")
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: return "resume"
            elif sel == 1: settings["write_speed"] = SPEEDS[(SPEEDS.index(settings["write_speed"])+1)%len(SPEEDS)]
            elif sel == 2: settings["post_action"] = (settings.get("post_action", 0) + 1) % 4
            elif sel == 3: return "abort"
        elif k in ['a', 'p', 'esc', 'q']: return "resume"

def error_prompt(e, lang, k_j, orig_text):
    sel = 0
    opts = [t("try_again"), t("change_api"), t("skip_key"), t("cancel_trans")]
    while True:
        print_header()
        print("\n" + RED + center(f"❌ {t('err_trans')} ❌") + RESET)
        print(center(str(e)))
        print("\n" + GRAY + center(f"Jazyk: {lang.upper()} | Klíč: {k_j}") + RESET)
        print(CYAN + center(textwrap.shorten(orig_text, width=80)) + RESET + "\n")
        for i, o in enumerate(opts):
            if i == sel: print(GREEN + center(f" ►►  {o}  ◄◄ ") + RESET)
            else: print(CYAN + center(f"     {o}     ") + RESET)
        print("\n" + YELLOW + center("[W/S] Pohyb | [D] Vybrat") + RESET)
        k = read_key(allow_esc_exit=False)
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts)-1: sel += 1
        elif k in ['d', 'enter']:
            if sel == 0: return 'retry'
            if sel == 1: return 'change'
            if sel == 2: return 'skip'
            if sel == 3: return 'abort'