import socket
import struct
import time
import threading
from .core import *


def query_server_a2s(ip, port, timeout=3):
    """Query a Source engine server using A2S_INFO protocol (UDP).
    Works with CS2, CS:GO, Rust, TF2, Garry's Mod, and other Source engine games.
    """
    result = {
        "online": False,
        "name": "",
        "map": "",
        "game": "",
        "players": 0,
        "max_players": 0,
        "ping": 0,
        "error": ""
    }

    # A2S_INFO request packet
    # Header: 0xFFFFFFFF + 'T' + "Source Engine Query\0"
    a2s_info = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00'

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        start_time = time.time()
        sock.sendto(a2s_info, (ip, port))

        data, addr = sock.recvfrom(4096)
        ping_ms = int((time.time() - start_time) * 1000)

        sock.close()

        if len(data) < 6:
            result["error"] = "Short response"
            return result

        header = struct.unpack_from('<i', data, 0)[0]

        # Check for challenge response (0x41 = 'A')
        if len(data) >= 9 and data[4] == 0x41:
            challenge = data[5:9]
            # Resend A2S_INFO with challenge token appended
            a2s_challenge = b'\xFF\xFF\xFF\xFF\x54Source Engine Query\x00' + challenge

            sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock2.settimeout(timeout)

            start_time = time.time()
            sock2.sendto(a2s_challenge, (ip, port))
            data, addr = sock2.recvfrom(4096)
            ping_ms = int((time.time() - start_time) * 1000)
            sock2.close()

            if len(data) < 6:
                result["error"] = "Short challenge response"
                return result

        # Some servers (Rust) may return split packets starting with 0xFFFFFFFE
        if len(data) >= 4 and data[0:4] == b'\xFE\xFF\xFF\xFF':
            # Simplified split packet - try to use payload after header
            data = b'\xFF\xFF\xFF\xFF' + data[12:]

        # Parse A2S_INFO response (type 0x49 = 'I' for Source, 0x6D = 'm' for GoldSrc)
        if data[4] == 0x49:
            # Source Engine response
            offset = 5
            # Protocol
            protocol = data[offset]
            offset += 1

            # Server name (null-terminated string)
            name_end = data.index(b'\x00', offset)
            result["name"] = data[offset:name_end].decode('utf-8', errors='replace')
            offset = name_end + 1

            # Map
            map_end = data.index(b'\x00', offset)
            result["map"] = data[offset:map_end].decode('utf-8', errors='replace')
            offset = map_end + 1

            # Folder
            folder_end = data.index(b'\x00', offset)
            offset = folder_end + 1

            # Game description
            game_end = data.index(b'\x00', offset)
            result["game"] = data[offset:game_end].decode('utf-8', errors='replace')
            offset = game_end + 1

            # Steam App ID (2 bytes)
            if offset + 2 <= len(data):
                offset += 2

            # Players, Max players
            if offset + 2 <= len(data):
                result["players"] = data[offset]
                result["max_players"] = data[offset + 1]

            result["online"] = True
            result["ping"] = ping_ms

        elif data[4] == 0x6D:
            # GoldSrc response (older games)
            offset = 5
            # Address
            addr_end = data.index(b'\x00', offset)
            offset = addr_end + 1

            # Name
            name_end = data.index(b'\x00', offset)
            result["name"] = data[offset:name_end].decode('utf-8', errors='replace')
            offset = name_end + 1

            # Map
            map_end = data.index(b'\x00', offset)
            result["map"] = data[offset:map_end].decode('utf-8', errors='replace')
            offset = map_end + 1

            # Folder
            folder_end = data.index(b'\x00', offset)
            offset = folder_end + 1

            # Game
            game_end = data.index(b'\x00', offset)
            result["game"] = data[offset:game_end].decode('utf-8', errors='replace')
            offset = game_end + 1

            # Players, Max
            if offset + 2 <= len(data):
                result["players"] = data[offset]
                result["max_players"] = data[offset + 1]

            result["online"] = True
            result["ping"] = ping_ms
        else:
            result["error"] = f"Unknown response type: 0x{data[4]:02x}"

    except socket.timeout:
        result["error"] = "timeout"
    except ConnectionResetError:
        result["error"] = "refused"
    except OSError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)

    return result


def query_all_servers(servers, timeout=3):
    """Query all servers in parallel using threads. Returns list of results."""
    results = [None] * len(servers)

    def worker(index, srv):
        results[index] = query_server_a2s(srv["ip"], srv["port"], timeout)

    threads = []
    for i, srv in enumerate(servers):
        t = threading.Thread(target=worker, args=(i, srv), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout + 1)

    # Fill in any that didn't complete
    for i in range(len(results)):
        if results[i] is None:
            results[i] = {
                "online": False, "name": "", "map": "", "game": "",
                "players": 0, "max_players": 0, "ping": 0, "error": "thread timeout"
            }

    return results


def format_status_line(srv, result, width=100):
    """Format a single server status line for the dashboard."""
    label = srv.get("label", f"{srv['ip']}:{srv['port']}")
    if len(label) > 25:
        label = label[:22] + "..."

    if result["online"]:
        status = f"{GREEN}ONLINE{RESET}"
        name = result["name"][:30] if result["name"] else "---"
        map_name = result["map"][:18] if result["map"] else "---"
        players = f"{result['players']}/{result['max_players']}"
        ping = f"{result['ping']}ms"

        # Color ping
        if result["ping"] < 50:
            ping_col = GREEN
        elif result["ping"] < 100:
            ping_col = YELLOW
        else:
            ping_col = RED

        # Color players
        if result["max_players"] > 0 and result["players"] >= result["max_players"]:
            player_col = RED
        elif result["max_players"] > 0 and result["players"] > result["max_players"] * 0.7:
            player_col = YELLOW
        else:
            player_col = GREEN

        line = (f" {WHITE}{label:<25}{RESET} "
                f"{status}  "
                f"{CYAN}{name:<30}{RESET} "
                f"{WHITE}{map_name:<18}{RESET} "
                f"{player_col}{players:<8}{RESET} "
                f"{ping_col}{ping}{RESET}")
    else:
        err = result.get("error", "unknown")
        if err == "timeout":
            status = f"{YELLOW}TIMEOUT{RESET}"
        elif err == "refused":
            status = f"{RED}REFUSED{RESET}"
        else:
            status = f"{RED}OFFLINE{RESET}"

        line = (f" {WHITE}{label:<25}{RESET} "
                f"{status}  "
                f"{GRAY}{'---':<30} {'---':<18} {'---':<8} ---{RESET}")

    return line


def format_dashboard_header():
    """Return the column header line for the dashboard."""
    return (f" {BOLD}{YELLOW}{'SERVER':<25} {'STATUS':<10} "
            f"{'NÁZEV':<30} {'MAPA':<18} {'HRÁČI':<8} PING{RESET}")
