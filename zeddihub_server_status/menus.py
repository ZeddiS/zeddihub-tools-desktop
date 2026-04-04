import os
import time
import platform
from datetime import datetime
from .core import *
from . import wizard
from . import monitor


def dashboard():
    """Live server status dashboard with auto-refresh."""
    if not settings["servers"]:
        print_header()
        print("\n" * 4 + YELLOW + center(t("no_servers")) + RESET)
        time.sleep(2)
        return

    last_results = None
    last_refresh_time = None

    while True:
        # Query all servers
        last_results = monitor.query_all_servers(settings["servers"])
        last_refresh_time = datetime.now().strftime("%H:%M:%S")

        # Render dashboard
        print_header()
        print(YELLOW + BOLD + center("[ SERVER DASHBOARD ]") + RESET)
        print()

        # Stats summary
        total = len(settings["servers"])
        online = sum(1 for r in last_results if r["online"])
        total_players = sum(r["players"] for r in last_results if r["online"])

        summary = (f"{GREEN}{online}{RESET}/{WHITE}{total}{RESET} online  |  "
                   f"{CYAN}{total_players}{RESET} "
                   f"{'hráčů celkem' if settings['ui_lang'] == 'cz' else 'total players'}  |  "
                   f"{GRAY}{t('last_refresh')}: {last_refresh_time}{RESET}")
        print(center(summary))
        print()

        # Table header
        print(center(GRAY + "-" * 100 + RESET))
        print(center(monitor.format_dashboard_header()))
        print(center(GRAY + "-" * 100 + RESET))

        # Server rows
        for i, srv in enumerate(settings["servers"]):
            line = monitor.format_status_line(srv, last_results[i])
            print(center(line))

        print(center(GRAY + "-" * 100 + RESET))
        print()

        refresh_text = f"[R] {'Obnovit' if settings['ui_lang'] == 'cz' else 'Refresh'}  |  " \
                       f"[A/Esc] {'Zpět' if settings['ui_lang'] == 'cz' else 'Back'}  |  " \
                       f"{'Auto-refresh za' if settings['ui_lang'] == 'cz' else 'Auto-refresh in'} " \
                       f"{settings['refresh_interval']}s"
        print(YELLOW + center(refresh_text) + RESET)

        # Wait for key or auto-refresh timeout
        start_wait = time.time()
        while True:
            elapsed = time.time() - start_wait
            if elapsed >= settings["refresh_interval"]:
                break

            if platform.system() == "Windows":
                import msvcrt
                if msvcrt.kbhit():
                    k = read_key_internal()
                    if k in ['a', 'esc', 'q']: return
                    elif k == 'r': break
            else:
                break

            time.sleep(0.1)


def add_server_menu():
    """Add a new server to the monitoring list."""
    print_header()
    print("\n" * 3 + YELLOW + BOLD + center(
        "PŘIDAT SERVER" if settings["ui_lang"] == "cz" else "ADD SERVER") + RESET)
    print()

    ip = safe_input(center(t("add_ip")))
    if ip is None or not ip.strip():
        return

    port_str = safe_input(center(t("add_port")))
    port = 27015
    if port_str and port_str.strip():
        try: port = int(port_str.strip())
        except: pass

    label = safe_input(center(t("add_label")))
    label_text = label.strip() if label else ""

    ip_clean = ip.strip()
    # Handle ip:port format
    if ':' in ip_clean and not port_str:
        parts = ip_clean.rsplit(':', 1)
        ip_clean = parts[0]
        try: port = int(parts[1])
        except: pass

    srv = {
        "ip": ip_clean,
        "port": port,
        "label": label_text if label_text else f"{ip_clean}:{port}"
    }

    # Quick test query
    print_header()
    print("\n" * 4 + CYAN + center(t("srv_querying")) + RESET)

    result = monitor.query_server_a2s(ip_clean, port, timeout=5)

    if result["online"]:
        srv["label"] = label_text if label_text else result["name"][:40]
        print_header()
        print("\n" * 3 + GREEN + center("Server nalezen!" if settings["ui_lang"] == "cz"
                                         else "Server found!") + RESET)
        print(WHITE + center(f"{result['name']}") + RESET)
        print(CYAN + center(f"{result['map']} | {result['players']}/{result['max_players']} | "
                            f"{result['game']}") + RESET)
    else:
        print_header()
        print("\n" * 3 + YELLOW + center(
            "Server neodpovídá - bude přidán jako offline." if settings["ui_lang"] == "cz"
            else "Server not responding - will be added as offline.") + RESET)
        print(GRAY + center(f"({result['error']})") + RESET)

    settings["servers"].append(srv)
    save_settings()

    print()
    print(GREEN + center("Server přidán do seznamu!" if settings["ui_lang"] == "cz"
                          else "Server added to list!") + RESET)
    time.sleep(2)


def remove_server_menu():
    """Remove a server from the monitoring list."""
    if not settings["servers"]:
        print_header()
        print("\n" * 4 + YELLOW + center(t("no_servers")) + RESET)
        time.sleep(2)
        return

    sel = 0
    while True:
        opts = [f"{srv['label']}  ({srv['ip']}:{srv['port']})" for srv in settings["servers"]]
        render_menu("ODEBRAT SERVER" if settings["ui_lang"] == "cz" else "REMOVE SERVER",
                     opts, sel,
                     footer="[W/S] Pohyb | [Enter] Odebrat | [A/Esc] Zpět" if settings["ui_lang"] == "cz"
                     else "[W/S] Move | [Enter] Remove | [A/Esc] Back")
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            removed = settings["servers"].pop(sel)
            save_settings()
            print_header()
            print("\n" * 4 + GREEN + center(
                f"Server '{removed['label']}' odebrán!" if settings["ui_lang"] == "cz"
                else f"Server '{removed['label']}' removed!") + RESET)
            time.sleep(1.5)
            if not settings["servers"]:
                return
            sel = min(sel, len(settings["servers"]) - 1)


def quick_query_menu():
    """Quick query a server without adding it to the list."""
    print_header()
    print("\n" * 3 + YELLOW + BOLD + center(
        "RYCHLÝ DOTAZ" if settings["ui_lang"] == "cz" else "QUICK QUERY") + RESET)
    print(GRAY + center(
        "Dotaz na server bez přidání do seznamu." if settings["ui_lang"] == "cz"
        else "Query a server without adding it to your list.") + RESET)
    print()

    ip = safe_input(center(t("add_ip")))
    if ip is None or not ip.strip():
        return

    ip_clean = ip.strip()
    port = 27015

    if ':' in ip_clean:
        parts = ip_clean.rsplit(':', 1)
        ip_clean = parts[0]
        try: port = int(parts[1])
        except: pass
    else:
        port_str = safe_input(center(t("add_port")))
        if port_str and port_str.strip():
            try: port = int(port_str.strip())
            except: pass

    print_header()
    print("\n" * 3 + CYAN + center(t("srv_querying")) + RESET)

    result = monitor.query_server_a2s(ip_clean, port, timeout=5)

    print_header()
    print()

    if result["online"]:
        print(GREEN + BOLD + center(f"=== {result['name']} ===") + RESET)
        print()
        info_lines = [
            (t("srv_name"), result["name"]),
            ("IP", f"{ip_clean}:{port}"),
            (t("srv_map"), result["map"]),
            (t("srv_game"), result["game"]),
            (t("srv_players"), f"{result['players']}/{result['max_players']}"),
            (t("srv_ping"), f"{result['ping']}ms"),
            ("Status", f"{GREEN}ONLINE{RESET}")
        ]
        for label, val in info_lines:
            print(center(f"{YELLOW}{label}:{RESET}  {WHITE}{val}{RESET}"))
    else:
        print(RED + BOLD + center(f"=== {ip_clean}:{port} ===") + RESET)
        print()
        print(center(f"{RED}Status: OFFLINE{RESET}"))
        print(center(f"{GRAY}Error: {result['error']}{RESET}"))

    print()
    print(GRAY + center("-" * 60) + RESET)
    print(YELLOW + center("[Libovolná klávesa pro návrat]" if settings["ui_lang"] == "cz"
                           else "[Press any key to return]") + RESET)
    read_key_internal()


def settings_menu():
    sel = 0
    while True:
        interval_txt = f"{settings['refresh_interval']}s"
        auto_txt = ("ZAPNUTO" if settings["auto_refresh"] else "VYPNUTO") if settings["ui_lang"] == "cz" \
            else ("ON" if settings["auto_refresh"] else "OFF")
        lang_txt = settings["ui_lang"].upper()

        opts = [
            f"{'Interval obnovování' if settings['ui_lang'] == 'cz' else 'Refresh interval'}: {interval_txt}",
            f"{'Auto-refresh' if settings['ui_lang'] == 'cz' else 'Auto-refresh'}: {auto_txt}",
            f"{'UI Jazyk' if settings['ui_lang'] == 'cz' else 'UI Language'}: {lang_txt}",
            RED + t("reset_def") + RESET
        ]
        descs = [
            "Jak často se bude dashboard automaticky obnovovat." if settings["ui_lang"] == "cz"
            else "How often the dashboard auto-refreshes.",
            "Automatické obnovování v dashboardu." if settings["ui_lang"] == "cz"
            else "Enable automatic refresh in dashboard.",
            "Jazyk uživatelského rozhraní (CZ/EN)." if settings["ui_lang"] == "cz"
            else "User interface language (CZ/EN).",
            "Smaže config a restartuje aplikaci." if settings["ui_lang"] == "cz"
            else "Delete config and restart application."
        ]
        render_menu(t("m_settings"), opts, sel, descs)
        k = read_key()
        save_settings()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0:
                # Cycle through intervals
                intervals = [5, 10, 15, 30, 60]
                current = settings["refresh_interval"]
                try:
                    idx = intervals.index(current)
                    settings["refresh_interval"] = intervals[(idx + 1) % len(intervals)]
                except ValueError:
                    settings["refresh_interval"] = 15
            elif sel == 1:
                settings["auto_refresh"] = not settings["auto_refresh"]
            elif sel == 2:
                settings["ui_lang"] = "en" if settings["ui_lang"] == "cz" else "cz"
            elif sel == 3:
                if os.path.exists(CONFIG_PATH):
                    os.remove(CONFIG_PATH)
                print_header()
                print("\n" * 4 + RED + center("RESTARTUJI DO TOVÁRNÍHO NASTAVENÍ..."
                                               if settings["ui_lang"] == "cz"
                                               else "RESETTING TO FACTORY DEFAULTS...") + RESET)
                time.sleep(2)
                raise ReturnToLauncher()


def credits_menu():
    import webbrowser
    sel = 0
    while True:
        opts = ["Web (zeddihub.eu)", "ZeddiS (zeddis.xyz)", "Discord (dsc.gg/zeddihub)",
                f"Verze Aplikace: {VERSION}"]
        render_menu(t("m_credits"), opts, sel)
        k = read_key()
        if k in ['a', 'esc', 'q']: return
        elif k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(opts) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            if sel == 0: webbrowser.open("https://zeddihub.eu")
            elif sel == 1: webbrowser.open("https://zeddis.xyz")
            elif sel == 2: webbrowser.open("https://dsc.gg/zeddihub")


def start_editor():
    setup_console()
    if not load_settings():
        wizard.first_run_wizard()

    print_header()
    print("\n" * 4 + center(YELLOW + "* " * 15 + RESET))
    print(center(BLUE + t("welcome") + RESET))
    print(center(GRAY + t("quote") + RESET))
    print(center(YELLOW + "* " * 15 + RESET))
    time.sleep(2)

    sel = 0
    while True:
        try:
            opts = [
                t('m_dashboard'),
                t('m_add'),
                t('m_remove'),
                "Quick Query",
                t('m_settings'),
                t('m_credits')
            ]
            descs = [
                t('d_dashboard'),
                t('d_add'),
                t('d_remove'),
                "Dotaz na server bez přidání." if settings["ui_lang"] == "cz"
                else "Query a server without adding it.",
                t('d_settings'),
                t('d_credits')
            ]
            server_count = len(settings["servers"])
            online_info = f"  [{server_count} {'serverů' if settings['ui_lang'] == 'cz' else 'servers'}]"
            opts[0] = t('m_dashboard') + f"  {GRAY}({server_count}){RESET}"

            render_menu(t("main_menu"), opts, sel, descs, centered=True)
            k = read_key()
            if k in ['a', 'esc', 'q']: raise ReturnToLauncher()
            elif k == 'w' and sel > 0: sel -= 1
            elif k == 's' and sel < len(opts) - 1: sel += 1
            elif k in ['d', 'enter', 'space']:
                if sel == 0: dashboard()
                elif sel == 1: add_server_menu()
                elif sel == 2: remove_server_menu()
                elif sel == 3: quick_query_menu()
                elif sel == 4: settings_menu()
                elif sel == 5: credits_menu()
        except ReturnToLauncher:
            return
