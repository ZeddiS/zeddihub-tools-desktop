import os
import time
from .core import *


def first_run_wizard():
    print_header()
    print("\n" * 4 + center(YELLOW + t("wiz_title") + RESET))
    print(center(CYAN + "Welcome to Server Status setup." + RESET))
    time.sleep(2)

    # Step 1: Language
    opts = ["Čeština", "English"]
    sel = 0
    while True:
        render_menu(t("wiz_step1"), opts, sel, footer="[W/S] Move | [Enter] Select")
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            settings["ui_lang"] = "cz" if sel == 0 else "en"
            break

    # Step 2: Add first server
    print_header()
    print("\n" * 3 + center(YELLOW + t("wiz_step2") + RESET))
    print(center(CYAN + ("Přidejte svůj první server pro monitoring." if settings["ui_lang"] == "cz"
                          else "Add your first server to monitor.") + RESET))
    print()

    ip = safe_input(center(t("add_ip")))
    if ip and ip.strip():
        port = safe_input(center(t("add_port")))
        port_num = 27015
        if port and port.strip():
            try: port_num = int(port.strip())
            except: pass
        label = safe_input(center(t("add_label")))
        label_text = label.strip() if label else ""

        settings["servers"].append({
            "ip": ip.strip(),
            "port": port_num,
            "label": label_text if label_text else f"{ip.strip()}:{port_num}"
        })

    # Step 3: Refresh interval
    sel = 0
    intervals = ["10", "15", "30", "60"]
    interval_descs = [
        "10s - Rychlé obnovování" if settings["ui_lang"] == "cz" else "10s - Fast refresh",
        "15s - Doporučeno" if settings["ui_lang"] == "cz" else "15s - Recommended",
        "30s - Střední" if settings["ui_lang"] == "cz" else "30s - Moderate",
        "60s - Pomalé" if settings["ui_lang"] == "cz" else "60s - Slow"
    ]
    while True:
        render_menu(t("wiz_step3"), intervals, sel, interval_descs,
                     footer="[W/S] Move | [Enter] Select")
        k = read_key(allow_esc_exit=False)
        if k == 'refresh': continue
        if k == 'w' and sel > 0: sel -= 1
        elif k == 's' and sel < len(intervals) - 1: sel += 1
        elif k in ['d', 'enter', 'space']:
            settings["refresh_interval"] = int(intervals[sel])
            break

    save_settings()

    print_header()
    print("\n" * 4 + GREEN + center("Instalace dokončena!" if settings["ui_lang"] == "cz"
                                     else "Setup complete!") + RESET)
    if settings["servers"]:
        print(CYAN + center(f"Server: {settings['servers'][0]['label']}") + RESET)
    print(CYAN + center(f"Interval: {settings['refresh_interval']}s") + RESET)
    time.sleep(2)
