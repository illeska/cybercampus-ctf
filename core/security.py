# ------------------------------
# CyberCampus CTF - Module Sécurité (IDS / Pare-feu)
# ------------------------------

from datetime import datetime, timedelta
from collections import defaultdict
import json

from flask import request as flask_request
from core import db


# ── Modèle SecurityEvent ───────────────────────────────────────────────────

class SecurityEvent(db.Model):
    __tablename__ = "security_event"

    id         = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    path       = db.Column(db.String(200), nullable=True)
    extra      = db.Column(db.Text, nullable=True)  # JSON libre
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="security_events", lazy="select")

    # ── Types d'événements ──
    LOGIN_OK       = "login_success"
    LOGIN_FAIL     = "login_fail"
    REGISTER       = "register"
    FLAG_OK        = "flag_submit_ok"
    FLAG_FAIL      = "flag_submit_fail"
    BANNED_ATTEMPT = "banned_user_attempt"
    BRUTE_SUSPECT  = "bruteforce_suspect"
    PORT_SCAN      = "port_scan_suspect"
    RATE_LIMIT     = "rate_limit_hit"

    @staticmethod
    def log(event_type, ip=None, user_id=None, extra=None):
        """Enregistre un événement de sécurité."""
        try:
            ua  = flask_request.headers.get("User-Agent", "")[:300]
            pth = flask_request.path[:200]
            ip  = ip or flask_request.remote_addr
            ev  = SecurityEvent(
                event_type=event_type,
                ip_address=ip,
                user_id=user_id,
                user_agent=ua,
                path=pth,
                extra=json.dumps(extra) if extra else None,
            )
            db.session.add(ev)
            db.session.commit()
            return ev
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def get_extra(event):
        try:
            return json.loads(event.extra) if event.extra else {}
        except Exception:
            return {}

    def __repr__(self):
        return f"<SecurityEvent {self.event_type} {self.ip_address}>"


# ── Helpers analytiques ───────────────────────────────────────────────────

def get_ip_info(ip: str) -> dict:
    """Retourne des infos basiques sur une IP (pays via rDNS simplifié)."""
    # En prod, on pourrait appeler ip-api.com ou ipinfo.io
    # Ici on fait une détection simple des plages privées
    if not ip:
        return {"country": "?", "type": "unknown"}
    if ip in ("127.0.0.1", "::1") or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
        return {"country": "Local", "type": "private"}
    return {"country": "External", "type": "public"}


def detect_bruteforce(ip: str, window_minutes: int = 5, threshold: int = 10) -> bool:
    """Détecte si une IP a fait trop de tentatives de login échouées."""
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    count = SecurityEvent.query.filter(
        SecurityEvent.event_type == SecurityEvent.LOGIN_FAIL,
        SecurityEvent.ip_address == ip,
        SecurityEvent.timestamp >= since,
    ).count()
    return count >= threshold


def detect_flag_spam(ip: str, window_minutes: int = 2, threshold: int = 20) -> bool:
    """Détecte du spam de soumissions de flags."""
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    count = SecurityEvent.query.filter(
        SecurityEvent.event_type.in_([SecurityEvent.FLAG_OK, SecurityEvent.FLAG_FAIL]),
        SecurityEvent.ip_address == ip,
        SecurityEvent.timestamp >= since,
    ).count()
    return count >= threshold


def get_dashboard_stats() -> dict:
    """Calcule toutes les statistiques pour le dashboard sécurité."""
    now   = datetime.utcnow()
    h24   = now - timedelta(hours=24)
    h1    = now - timedelta(hours=1)
    min5  = now - timedelta(minutes=5)

    # ── Compteurs globaux ──────────────────────────────────────────
    total_events = SecurityEvent.query.count()
    events_24h   = SecurityEvent.query.filter(SecurityEvent.timestamp >= h24).count()
    events_1h    = SecurityEvent.query.filter(SecurityEvent.timestamp >= h1).count()

    # ── Connexions ─────────────────────────────────────────────────
    logins_ok_24h   = SecurityEvent.query.filter(
        SecurityEvent.event_type == SecurityEvent.LOGIN_OK,
        SecurityEvent.timestamp >= h24,
    ).count()

    logins_fail_24h = SecurityEvent.query.filter(
        SecurityEvent.event_type == SecurityEvent.LOGIN_FAIL,
        SecurityEvent.timestamp >= h24,
    ).count()

    registers_24h = SecurityEvent.query.filter(
        SecurityEvent.event_type == SecurityEvent.REGISTER,
        SecurityEvent.timestamp >= h24,
    ).count()

    # ── Flags ──────────────────────────────────────────────────────
    flags_ok_24h   = SecurityEvent.query.filter(
        SecurityEvent.event_type == SecurityEvent.FLAG_OK,
        SecurityEvent.timestamp >= h24,
    ).count()

    flags_fail_24h = SecurityEvent.query.filter(
        SecurityEvent.event_type == SecurityEvent.FLAG_FAIL,
        SecurityEvent.timestamp >= h24,
    ).count()

    # ── IPs suspectes (brute-force détecté sur 5 min) ──────────────
    suspicious_ips = (
        db.session.query(
            SecurityEvent.ip_address,
            db.func.count(SecurityEvent.id).label("count"),
        )
        .filter(
            SecurityEvent.event_type == SecurityEvent.LOGIN_FAIL,
            SecurityEvent.timestamp >= min5,
        )
        .group_by(SecurityEvent.ip_address)
        .having(db.func.count(SecurityEvent.id) >= 5)
        .order_by(db.desc("count"))
        .all()
    )

    # ── Top IPs (24h) ──────────────────────────────────────────────
    top_ips = (
        db.session.query(
            SecurityEvent.ip_address,
            db.func.count(SecurityEvent.id).label("count"),
        )
        .filter(SecurityEvent.timestamp >= h24)
        .group_by(SecurityEvent.ip_address)
        .order_by(db.desc("count"))
        .limit(10)
        .all()
    )

    # ── Derniers événements ────────────────────────────────────────
    recent_events = (
        SecurityEvent.query
        .order_by(SecurityEvent.timestamp.desc())
        .limit(50)
        .all()
    )

    # ── Répartition par type (24h) ─────────────────────────────────
    type_counts_raw = (
        db.session.query(
            SecurityEvent.event_type,
            db.func.count(SecurityEvent.id).label("count"),
        )
        .filter(SecurityEvent.timestamp >= h24)
        .group_by(SecurityEvent.event_type)
        .all()
    )
    type_counts = {t: c for t, c in type_counts_raw}

    # ── Activité par heure (24 dernières heures) ───────────────────
    hourly = []
    for i in range(23, -1, -1):
        t_start = now - timedelta(hours=i + 1)
        t_end   = now - timedelta(hours=i)
        cnt = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= t_start,
            SecurityEvent.timestamp < t_end,
        ).count()
        hourly.append({
            "label": (now - timedelta(hours=i)).strftime("%H:00"),
            "count": cnt,
        })

    # ── IPs bannies (tentatives utilisateurs bannis) ───────────────
    banned_attempts = (
        SecurityEvent.query
        .filter(SecurityEvent.event_type == SecurityEvent.BANNED_ATTEMPT)
        .order_by(SecurityEvent.timestamp.desc())
        .limit(20)
        .all()
    )

    return {
        "total_events"    : total_events,
        "events_24h"      : events_24h,
        "events_1h"       : events_1h,
        "logins_ok_24h"   : logins_ok_24h,
        "logins_fail_24h" : logins_fail_24h,
        "registers_24h"   : registers_24h,
        "flags_ok_24h"    : flags_ok_24h,
        "flags_fail_24h"  : flags_fail_24h,
        "suspicious_ips"  : suspicious_ips,
        "top_ips"         : top_ips,
        "recent_events"   : recent_events,
        "type_counts"     : type_counts,
        "hourly"          : hourly,
        "banned_attempts" : banned_attempts,
    }

class BannedIP(db.Model):
    __tablename__ = "banned_ip"
 
    id         = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    reason     = db.Column(db.String(300), nullable=True)
    banned_by  = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    banned_at  = db.Column(db.DateTime, default=datetime.utcnow)
 
    admin = db.relationship("User", foreign_keys=[banned_by])
 
    @staticmethod
    def is_banned(ip: str) -> bool:
        if not ip:
            return False
        return BannedIP.query.filter_by(ip_address=ip).first() is not None
 
    def __repr__(self):
        return f"<BannedIP {self.ip_address}>"
 