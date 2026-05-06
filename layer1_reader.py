# ══════════════════════════════════════════════════════════════════
# layer1_reader.py
# Lit les logs Nginx + Fail2ban pour le dashboard admin
# Utilise fail2ban-client avec socket Unix
# ══════════════════════════════════════════════════════════════════

import subprocess
import re
from pathlib import Path

FAIL2BAN_SOCKET   = "/var/run/fail2ban/fail2ban.sock"
NGINX_BLOCKED_LOG = Path("/var/log/nginx/cybercampus_blocked.log")
FAIL2BAN_LOG      = Path("/var/log/fail2ban/fail2ban.log")


# ── Statut Fail2ban ───────────────────────────────────────────────

def get_fail2ban_status() -> dict:
    result = {
        "available": False,
        "jails": [],
        "total_banned": 0,
        "error": None,
    }

    def run(args):
        return subprocess.run(
            ["fail2ban-client", "--socket", FAIL2BAN_SOCKET] + args,
            capture_output=True, text=True, timeout=5
        )

    try:
        out = run(["status"])
        if out.returncode != 0:
            result["error"] = out.stderr.strip() or "fail2ban-client non disponible"
            return result

        result["available"] = True

        match = re.search(r"Jail list:\s+(.+)", out.stdout)
        if not match:
            return result

        jail_names = [j.strip() for j in match.group(1).split(",") if j.strip()]

        for jail in jail_names:
            jail_out = run(["status", jail])
            if jail_out.returncode != 0:
                continue

            txt = jail_out.stdout

            def extract(pattern, default=0):
                m = re.search(pattern, txt)
                return int(m.group(1)) if m else default

            def extract_ips(pattern):
                m = re.search(pattern, txt)
                if not m:
                    return []
                raw = m.group(1).strip()
                return [ip.strip() for ip in raw.split() if ip.strip()] if raw else []

            currently_banned = extract(r"Currently banned:\s+(\d+)")

            result["jails"].append({
                "name":             jail,
                "currently_banned": currently_banned,
                "total_banned":     extract(r"Total banned:\s+(\d+)"),
                "banned_ips":       extract_ips(r"Banned IP list:\s+(.+)"),
                "currently_failed": extract(r"Currently failed:\s+(\d+)"),
                "total_failed":     extract(r"Total failed:\s+(\d+)"),
            })
            result["total_banned"] += currently_banned

    except FileNotFoundError:
        result["error"] = "fail2ban-client non installé"
    except subprocess.TimeoutExpired:
        result["error"] = "timed out"
    except Exception as e:
        result["error"] = str(e)

    return result


# ── Requêtes bloquées par Nginx ───────────────────────────────────

def get_blocked_requests(limit: int = 50) -> list:
    if not NGINX_BLOCKED_LOG.exists():
        return []

    pattern_json = re.compile(
        r'^\{"time":"(?P<time>[^"]+)","remote_addr":"(?P<ip>[^"]+)","method":"(?P<method>[^"]+)","uri":"(?P<uri>[^"]+)","status":"(?P<status>[^"]+)"'
    )
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