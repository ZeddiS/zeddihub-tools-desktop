import os
import re
import time
import socket
import platform
from .core import *


def rcon_client():
    """Rust RCON client - connects to Rust server via WebSocket RCON or Source RCON."""
    host = "127.0.0.1"
    port = 28016
    password = ""

    print_header()
    print("\n" * 3 + YELLOW + BOLD + center("RUST RCON KLIENT") + RESET)
    print(GRAY + center("Připojte se k Rust serveru a posílejte příkazy vzdáleně.") + RESET)
    print(GRAY + center("(Používá Source RCON protokol - port je obvykle +1 od game portu)") + RESET)

    h = safe_input("\n" + center("IP adresa serveru (výchozí 127.0.0.1): "))
    if h and h.strip(): host = h.strip()

    p = safe_input(center("RCON Port (výchozí 28016): "))
    if p and p.strip():
        try: port = int(p.strip())
        except: pass

    pw = safe_input(center("RCON heslo (server.rconpassword): "))
    if pw is None: return
    password = pw.strip()
    if not password:
        print_header()
        print("\n" * 4 + RED + center("RCON heslo nesmí být prázdné!") + RESET)
        time.sleep(2)
        return

    def build_rcon_packet(req_id, ptype, body):
        import struct
        body_encoded = body.encode('utf-8') + b'\x00\x00'
        size = 4 + 4 + len(body_encoded)
        return struct.pack('<iii', size, req_id, ptype) + body_encoded

    def read_rcon_response(sock):
        import struct
        data = sock.recv(4)
        if len(data) < 4: return None, None
        size = struct.unpack('<i', data)[0]
        rest = b''
        while len(rest) < size:
            chunk = sock.recv(size - len(rest))
            if not chunk: break
            rest += chunk
        if len(rest) < 8: return None, None
        req_id, resp_type = struct.unpack('<ii', rest[:8])
        body = rest[8:].rstrip(b'\x00')
        return req_id, body.decode('utf-8', errors='replace')

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        auth_pkt = build_rcon_packet(1, 3, password)
        sock.sendall(auth_pkt)
        req_id, body = read_rcon_response(sock)
        req_id2, body2 = read_rcon_response(sock)

        if req_id2 == -1:
            print_header()
            print("\n" * 4 + RED + center("Autentizace selhala! Špatné RCON heslo.") + RESET)
            time.sleep(3)
            sock.close()
            return

        print_header()
        print("\n" + GREEN + center(f"Připojeno k {host}:{port}") + RESET)
        print(GRAY + center("Zadejte příkazy. Napsáním 'exit' se odpojíte.") + RESET)
        print(GRAY + center("Užitečné: status, playerlist, oxide.reload *, kick <name>") + RESET)
        print(GRAY + center("-" * 60) + RESET + "\n")

        while True:
            cmd = safe_input(f"{CYAN}rcon>{RESET} ")
            if cmd is None or cmd.strip().lower() == "exit":
                break
            if not cmd.strip():
                continue
            cmd_pkt = build_rcon_packet(2, 2, cmd.strip())
            sock.sendall(cmd_pkt)
            time.sleep(0.3)
            req_id, response = read_rcon_response(sock)
            if response:
                for line in response.splitlines():
                    print(f"  {WHITE}{line}{RESET}")
            else:
                print(f"  {GRAY}(žádná odpověď){RESET}")

        sock.close()
        print_header()
        print("\n" * 4 + GREEN + center("RCON relace ukončena.") + RESET)
        time.sleep(1.5)

    except socket.timeout:
        print_header()
        print("\n" * 4 + RED + center(f"Časový limit připojení k {host}:{port} vypršel!") + RESET)
        time.sleep(3)
    except ConnectionRefusedError:
        print_header()
        print("\n" * 4 + RED + center(f"Server {host}:{port} odmítl připojení!") + RESET)
        time.sleep(3)
    except Exception as e:
        print_header()
        print("\n" * 4 + RED + center(f"Chyba RCON: {e}") + RESET)
        time.sleep(3)


def plugin_dependency_checker():
    """Scans .cs plugin files for Oxide/uMod dependencies and references."""
    print_header()
    print("\n" * 3 + YELLOW + BOLD + center("PLUGIN DEPENDENCY CHECKER") + RESET)
    print(GRAY + center("Analyzuje závislosti Oxide/uMod pluginů ve zdrojové složce.") + RESET)
    time.sleep(1)

    source = settings.get("source_dir", "")
    if not source or not os.path.isdir(source):
        print_header()
        print("\n" * 4 + RED + center("Zdrojová složka není nastavena nebo neexistuje!") + RESET)
        time.sleep(2)
        return

    cs_files = [f for f in os.listdir(source) if f.endswith('.cs')]
    if not cs_files:
        print_header()
        print("\n" * 4 + RED + center("Ve zdrojové složce nebyly nalezeny žádné .cs soubory!") + RESET)
        time.sleep(2)
        return

    # Patterns to detect
    patterns = {
        "oxide_refs": re.compile(r'\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)', re.MULTILINE),
        "requires": re.compile(r'\[Requires\("([^"]+)"\)\]', re.MULTILINE),
        "using_oxide": re.compile(r'using\s+Oxide\.[\w.]+', re.MULTILINE),
        "permissions": re.compile(r'permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"', re.MULTILINE),
        "commands_chat": re.compile(r'\[ChatCommand\s*\(\s*"([^"]+)"', re.MULTILINE),
        "commands_console": re.compile(r'\[ConsoleCommand\s*\(\s*"([^"]+)"', re.MULTILINE),
        "hooks": re.compile(r'(?:void|object|bool|string)\s+(On\w+|Can\w+)\s*\(', re.MULTILINE),
        "config_exists": re.compile(r'(?:LoadConfig|SaveConfig|Config\[|LoadDefaultConfig)', re.MULTILINE),
        "lang_exists": re.compile(r'(?:lang\.Register|lang\.GetMessage)', re.MULTILINE),
        "data_exists": re.compile(r'(?:Interface\.Oxide\.DataFileSystem|ProtoStorage)', re.MULTILINE),
    }

    results = []
    for fname in cs_files:
        fpath = os.path.join(source, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        info = {"file": fname, "deps": [], "hooks": [], "commands": [], "perms": [], "features": []}

        # Plugin references
        for m in patterns["oxide_refs"].finditer(content):
            info["deps"].append(m.group(1))
        for m in patterns["requires"].finditer(content):
            info["deps"].append(m.group(1))

        # Remove duplicates
        info["deps"] = list(set(info["deps"]))

        # Hooks
        for m in patterns["hooks"].finditer(content):
            info["hooks"].append(m.group(1))
        info["hooks"] = list(set(info["hooks"]))

        # Commands
        for m in patterns["commands_chat"].finditer(content):
            info["commands"].append(f"/{m.group(1)}")
        for m in patterns["commands_console"].finditer(content):
            info["commands"].append(m.group(1))

        # Permissions
        for m in patterns["permissions"].finditer(content):
            info["perms"].append(m.group(1))

        # Features
        if patterns["config_exists"].search(content):
            info["features"].append("Config")
        if patterns["lang_exists"].search(content):
            info["features"].append("Lang")
        if patterns["data_exists"].search(content):
            info["features"].append("DataFile")

        results.append(info)

    # Display results
    sel = 0
    while True:
        opts = []
        descs = []
        for r in results:
            dep_count = len(r["deps"])
            hook_count = len(r["hooks"])
            cmd_count = len(r["commands"])
            status = f"Deps:{dep_count} Hooks:{hook_count} Cmds:{cmd_count}"
            opts.append(f"{r['file']:<35} {status}")
            features = ", ".join(r["features"]) if r["features"] else "---"
            descs.append(f"Features: {features}")

        render_menu(f"DEPENDENCY CHECK ({len(cs_files)} pluginů)", opts, sel, descs,
                     footer="[W/S] Pohyb | [Enter] Detail | [E] Export | [A/Esc] Zpět")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k == 'e':
            # Export to text file
            os.makedirs(settings["target_dir"], exist_ok=True)
            path = os.path.join(settings["target_dir"], "plugin_dependencies.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("ZeddiHub Plugin Dependency Report\n")
                f.write("=" * 60 + "\n\n")
                for r in results:
                    f.write(f"Plugin: {r['file']}\n")
                    f.write(f"  Dependencies: {', '.join(r['deps']) if r['deps'] else 'None'}\n")
                    f.write(f"  Hooks ({len(r['hooks'])}): {', '.join(r['hooks'][:10])}\n")
                    f.write(f"  Commands: {', '.join(r['commands']) if r['commands'] else 'None'}\n")
                    f.write(f"  Permissions: {', '.join(r['perms']) if r['perms'] else 'None'}\n")
                    f.write(f"  Features: {', '.join(r['features']) if r['features'] else 'None'}\n")
                    f.write("\n")
            print_header()
            print("\n" * 4 + GREEN + center(f"Export uložen: {path}") + RESET)
            time.sleep(2)
            if settings.get("open_folder_after") and platform.system() == "Windows":
                try: os.startfile(settings["target_dir"])
                except Exception: pass

        elif k in ['d', 'enter', 'space']:
            r = results[sel]
            while True:
                detail_opts = [f"Soubor: {r['file']}"]
                detail_opts.append(f"Závislosti: {', '.join(r['deps']) if r['deps'] else 'Žádné'}")
                detail_opts.append(f"Hooks ({len(r['hooks'])}): {', '.join(r['hooks'][:8])}")
                if len(r['hooks']) > 8:
                    detail_opts[-1] += f" ...+{len(r['hooks']) - 8}"
                detail_opts.append(f"Příkazy: {', '.join(r['commands']) if r['commands'] else 'Žádné'}")
                detail_opts.append(f"Oprávnění: {', '.join(r['perms']) if r['perms'] else 'Žádné'}")
                detail_opts.append(f"Features: {', '.join(r['features']) if r['features'] else 'Žádné'}")

                render_menu(f"DETAIL: {r['file']}", detail_opts, 0,
                             footer="[A/Esc] Zpět")
                dk = read_key()
                if dk in ['a', 'esc', 'q']: break
