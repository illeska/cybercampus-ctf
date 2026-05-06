# ══════════════════════════════════════════════════════════════════
# layer1_reader.py
# Lit les logs Nginx + Fail2ban pour le dashboard admin
# Utilise le socket Unix Fail2ban directement (pas de fail2ban-client)
# ══════════════════════════════════════════════════════════════════

import socket
import struct
import json
import re
import subprocess
from pathlib import Path

FAIL2BAN_SOCKET   = "/var/run/fail2ban/fail2ban.sock"
NGINX_BLOCKED_LOG = Path("/var/log/nginx/cybercampus_blocked.log")
FAIL2BAN_LOG      = Path("/var/log/fail2ban/fail2ban.log")


# ── Communication socket Unix Fail2ban ────────────────────────────

def _f2b_send(command: list) -> str:
    """
    Envoie une commande au socket Unix Fail2ban et retourne la réponse texte.
    Protocole : pickle-like maison de Fail2ban (longueur 4 octets + données JSON-ish).
    On utilise la sérialisation native fail2ban (pickle python).
    """
    import pickle

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(FAIL2BAN_SOCKET)

    # Fail2ban attend un pickle de la commande
    data = pickle.dumps(command, protocol=2)
    # Header : longueur sur 4 octets big-endian
    sock.sendall(struct.pack(">i", len(data)) + data)

    # Lecture réponse
    raw_len = b""
    while len(raw_len) < 4:
        chunk = sock.recv(4 - len(raw_len))
        if not chunk:
            break
        raw_len += chunk

    if len(raw_len) < 4:
        sock.close()
        return ""

    length = struct.unpack(">i", raw_len)[0]
    raw_data = b""
    while len(raw_data) < length:
        chunk = sock.recv(length - len(raw_data))
        if not chunk:
            break
        raw_data += chunk

    sock.close()
    response = pickle.loads(raw_data)
    return response


# ── Statut Fail2ban ───────────────────────────────────────────────

def get_fail2ban_status() -> dict:
    result = {
        "available": False,
        "jails": [],
        "total_banned": 0,
        "error": None,
    }

    try:
        # Récupère la liste des jails
        response = _f2b_send(["status"])
        if not isinstance(response, (list, tuple)) or len(response) < 2:
            result["error"] = "Réponse inattendue du socket"
            return result

        # response[1] est un tuple de tuples : (('Number of jail', N), ('Jail list', [...]))
        jail_data = dict(response[1])
        jail_list = jail_data.get("Jail list", [])

        if isinstance(jail_list, str):
            jail_names = [j.strip() for j in jail_list.split(",") if j.strip()]
        else:
            jail_names = list(jail_list)

        result["available"] = True

        for jail in jail_names:
            try:
                jail_resp = _f2b_send(["status", jail])
                if not isinstance(jail_resp, (list, tuple)) or len(jail_resp) < 2:
                    continue

                jail_info = dict(jail_resp[1])

                # Filter stats
                filter_stats = dict(jail_info.get("Filter", []))
                # Action stats
                action_stats = dict(jail_info.get("Actions", []))

                currently_failed = filter_stats.get("Currently failed", 0)
                total_failed     = filter_stats.get("Total failed", 0)
                currently_banned = action_stats.get("Currently banned", 0)
                total_banned     = action_stats.get("Total banned", 0)
                banned_ips_raw   = action_stats.get("Banned IP list", [])

                if isinstance(banned_ips_raw, str):
                    banned_ips = [ip.strip() for ip in banned_ips_raw.split() if ip.strip()]
                else:
                    banned_ips = list(banned_ips_raw)

                result["jails"].append({
                    "name":             jail,
                    "currently_banned": int(currently_banned),
                    "total_banned":     int(total_banned),
                    "banned_ips":       banned_ips,
                    "currently_failed": int(currently_failed),
                    "total_failed":     int(total_failed),
                })
                result["total_banned"] += int(currently_banned)

            except Exception as e:
                result["jails"].append({
                    "name":             jail,
                    "currently_banned": 0,
                    "total_banned":     0,
                    "banned_ips":       [],
                    "currently_failed": 0,
                    "total_failed":     0,
                })

    except FileNotFoundError:
        result["error"] = "Socket Fail2ban introuvable"
    except ConnectionRefusedError:
        result["error"] = "Fail2ban non démarré"
    except PermissionError:
        result["error"] = "Permission refusée sur le socket Fail2ban"
    except Exception as e:
        result["error"] = str(e)

    return result


# ── Requêtes bloquées par Nginx ───────────────────────────────────

def get_blocked_requests(limit: int = 50) -> list:
    """Lit cybercampus_blocked.log — format JSON ou classique."""
    if not NGINX_BLOCKED_LOG.exists():
        return []

    # Pattern JSON (format actuel)
    pattern_json = re.compile(
        r'^\{"time":"(?P<time>[^"]+)","remote_addr":"(?P<ip>[^"]+)","method":"(?P<method>[^"]+)","uri":"(?P<uri>[^"]+)","status":"(?P<status>[^"]+)"'
    )
    # Pattern classique fallback
    pattern_classic = re.compile(
        r'^(?P<ip>[\d\.a-fA-F:]+) - \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" (?P<status>\d+) "(?P<ua>[^"]*)"'
    )

    entries = []
    try:
        out = subprocess.run(
            ["tail", "-n", str(limit), str(NGINX_BLOCKED_LOG)],
            capture_output=True, text=True, timeout=5
        )
        for line in reversed(out.stdout.splitlines()):
            line = line.strip()
            m = pattern_json.match(line)
            if m:
                entries.append({
                    "ip":      m.group("ip"),
                    "time":    m.group("time"),
                    "request": f"{m.group('method')} {m.group('uri')}",
                    "status":  m.group("status"),
                    "ua":      "",
                })
                continue
            m = pattern_classic.match(line)
            if m:
                entries.append({
                    "ip":      m.group("ip"),
                    "time":    m.group("time"),
                    "request": m.group("request"),
                    "status":  m.group("status"),
                    "ua":      m.group("ua")[:80],
                })
    except Exception:
        pass

    return entries


# ── Scans de ports ────────────────────────────────────────────────

def get_port_scan_stats() -> dict:
    result = {"total": 0, "top_ips": [], "available": False}
    pattern = re.compile(r"PORTSCAN:.*SRC=([\d\.]+)")
    ip_counts: dict = {}

    for log_file in [Path("/var/log/kern.log"), Path("/var/log/syslog")]:
        if not log_file.exists():
            continue
        try:
            out = subprocess.run(
                ["grep", "-a", "PORTSCAN", str(log_file)],
                capture_output=True, text=True, timeout=10
            )
            for line in out.stdout.splitlines():
                m = pattern.search(line)
                if m:
                    ip = m.group(1)
                    ip_counts[ip] = ip_counts.get(ip, 0) + 1
                    result["available"] = True
        except Exception:
            pass

    result["total"] = sum(ip_counts.values())
    result["top_ips"] = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return result


# ── Historique bans Fail2ban ──────────────────────────────────────

def get_recent_bans(limit: int = 20) -> list:
    if not FAIL2BAN_LOG.exists():
        return []

    pattern = re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[(?P<jail>[^\]]+)\]\s+(?P<action>Ban|Unban)\s+(?P<ip>[\d\.a-fA-F:]+)"
    )
    entries = []
    try:
        out = subprocess.run(
            ["tail", "-n", "500", str(FAIL2BAN_LOG)],
            capture_output=True, text=True, timeout=5
        )
        for line in reversed(out.stdout.splitlines()):
            if "Ban" not in line:
                continue
            m = pattern.search(line)
            if m:
                entries.append({
                    "ts":     m.group("ts"),
                    "jail":   m.group("jail"),
                    "action": m.group("action"),
                    "ip":     m.group("ip"),
                })
                if len(entries) >= limit:
                    break
    except Exception:
        pass
    return entries


# ── Fonction principale ───────────────────────────────────────────

def get_layer1_stats() -> dict:
    return {
        "fail2ban":    get_fail2ban_status(),
        "blocked":     get_blocked_requests(50),
        "port_scans":  get_port_scan_stats(),
        "recent_bans": get_recent_bans(20),
    }