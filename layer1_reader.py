# ══════════════════════════════════════════════════════════════════
# core/layer1_reader.py
# Lit les logs Nginx + Fail2ban pour les afficher dans le dashboard
# Appelé par la route /admin/security
# ══════════════════════════════════════════════════════════════════

import subprocess
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# Chemins des logs (adapter si différent)
NGINX_ACCESS_LOG  = Path("/var/log/nginx/cybercampus_access.log")
NGINX_BLOCKED_LOG = Path("/var/log/nginx/cybercampus_blocked.log")
FAIL2BAN_LOG      = Path("/var/log/fail2ban/fail2ban.log")


# ── Lecture Fail2ban via client ────────────────────────────────────

def get_fail2ban_status() -> dict:
    """
    Lit le statut de tous les jails Fail2ban via fail2ban-client.
    Retourne un dict structuré.
    """
    result = {
        "available": False,
        "jails": [],
        "total_banned": 0,
        "error": None,
    }

    try:
        # Liste des jails
        out = subprocess.run(
            ["fail2ban-client", "status"],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode != 0:
            result["error"] = "fail2ban-client non disponible"
            return result

        result["available"] = True

        # Extraire les noms de jails
        match = re.search(r"Jail list:\s+(.+)", out.stdout)
        if not match:
            return result

        jail_names = [j.strip() for j in match.group(1).split(",") if j.strip()]

        for jail in jail_names:
            jail_out = subprocess.run(
                ["fail2ban-client", "status", jail],
                capture_output=True, text=True, timeout=5
            )
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
            total_banned_all  = extract(r"Total banned:\s+(\d+)")
            banned_ips        = extract_ips(r"Banned IP list:\s+(.+)")

            result["jails"].append({
                "name":            jail,
                "currently_banned": currently_banned,
                "total_banned":    total_banned_all,
                "banned_ips":      banned_ips,
                "currently_failed": extract(r"Currently failed:\s+(\d+)"),
                "total_failed":    extract(r"Total failed:\s+(\d+)"),
            })
            result["total_banned"] += currently_banned

    except FileNotFoundError:
        result["error"] = "fail2ban non installé"
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout fail2ban-client"
    except Exception as e:
        result["error"] = str(e)

    return result


# ── Lecture du log Nginx bloqué ────────────────────────────────────

def get_blocked_requests(limit: int = 100) -> list:
    """
    Lit les dernières entrées du log cybercampus_blocked.log.
    Format : $remote_addr - [$time_local] "$request" $status "$ua"
    """
    if not NGINX_BLOCKED_LOG.exists():
        return []

    pattern = re.compile(
        r'^(?P<ip>[\d\.a-fA-F:]+) - \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" (?P<status>\d+) "(?P<ua>[^"]*)"'
    )

    entries = []
    try:
        # Lire les dernières lignes (tail)
        out = subprocess.run(
            ["tail", "-n", str(limit), str(NGINX_BLOCKED_LOG)],
            capture_output=True, text=True, timeout=5
        )
        for line in reversed(out.stdout.splitlines()):
            m = pattern.match(line.strip())
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


# ── Comptage des scans de ports ────────────────────────────────────

def get_port_scan_stats(minutes: int = 60) -> dict:
    """
    Lit /var/log/syslog ou kern.log pour compter les lignes PORTSCAN.
    Retourne le nombre de scans et les top IPs.
    """
    result = {"total": 0, "top_ips": [], "available": False}

    log_files = [
        Path("/var/log/kern.log"),
        Path("/var/log/syslog"),
    ]

    pattern = re.compile(r"PORTSCAN:.*SRC=([\d\.]+)")
    ip_counts: dict = {}

    for log_file in log_files:
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


# ── Récents bans Fail2ban depuis le log ───────────────────────────

def get_recent_bans(limit: int = 30) -> list:
    """
    Lit /var/log/fail2ban/fail2ban.log pour les bans récents.
    Format : 2026-05-05 17:30:00,123 fail2ban.actions [INFO] [jail] Ban 1.2.3.4
    """
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
            if "Ban" not in line and "Unban" not in line:
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


# ── Fonction principale appelée par le dashboard ──────────────────

def get_layer1_stats() -> dict:
    """Agrège toutes les stats couche 1 pour le dashboard admin."""
    return {
        "fail2ban":      get_fail2ban_status(),
        "blocked":       get_blocked_requests(50),
        "port_scans":    get_port_scan_stats(),
        "recent_bans":   get_recent_bans(20),
    }