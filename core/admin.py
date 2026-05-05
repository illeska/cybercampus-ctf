# ------------------------------
# CyberCampus CTF - Panel Admin
# ------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from core import db
from core.models import User, Challenge, Submission, Scoreboard, Flag, RssFeed
from core.security import SecurityEvent, get_dashboard_stats
from datetime import datetime, timedelta
import csv
import io

# Création du blueprint admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ------------------------------
# Décorateur pour vérifier si l'utilisateur est admin
# ------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour accéder à cette page.", "danger")
            return redirect(url_for('auth.login'))
        
        if current_user.role != "admin":
            flash("⛔ Accès refusé. Vous n'êtes pas administrateur.", "danger")
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------
# DASHBOARD ADMIN
# ------------------------------
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Page principale du panel admin avec statistiques"""
    
    # Stats générales
    total_users = User.query.count()
    total_challenges = Challenge.query.count()
    total_submissions = Submission.query.count()
    total_flags_valides = Submission.query.filter_by(correct=True).count()
    
    # Challenge le plus réussi
    challenge_stats = db.session.query(
        Challenge.titre,
        db.func.count(Submission.id).label('validations')
    ).join(Submission).filter(
        Submission.correct == True
    ).group_by(Challenge.id).order_by(
        db.desc('validations')
    ).first()
    
    most_solved_challenge = challenge_stats[0] if challenge_stats else "Aucun"
    
    # 10 dernières soumissions
    recent_submissions = Submission.query.order_by(
        Submission.timestamp.desc()
    ).limit(10).all()
    
    # Détection activité suspecte (plus de 10 tentatives en 1 min)
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    suspicious_activity = db.session.query(
        User.pseudo,
        Challenge.titre,
        db.func.count(Submission.id).label('attempts')
    ).join(User).join(Challenge).filter(
        Submission.timestamp >= one_minute_ago,
        Submission.correct == False
    ).group_by(User.id, Challenge.id).having(
        db.func.count(Submission.id) > 10
    ).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_challenges=total_challenges,
        total_submissions=total_submissions,
        total_flags_valides=total_flags_valides,
        most_solved_challenge=most_solved_challenge,
        recent_submissions=recent_submissions,
        suspicious_activity=suspicious_activity
    )

# ------------------------------
# GESTION DES UTILISATEURS
# ------------------------------
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Liste de tous les utilisateurs"""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    """Bannir/débannir un utilisateur"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("❌ Vous ne pouvez pas vous bannir vous-même.", "danger")
        return redirect(url_for('admin.users'))

    # Un admin ne peut pas bannir/débannir un autre admin
    if user.role == "admin":
        flash("❌ Vous ne pouvez pas bannir un autre administrateur.", "danger")
        return redirect(url_for('admin.users'))

    # Toggle le rôle (banned ou user)
    if user.role == "banned":
        user.role = "user"
        flash(f"✅ {user.pseudo} a été débanni.", "success")
    else:
        user.role = "banned"
        flash(f"🔨 {user.pseudo} a été banni.", "warning")

    db.session.commit()
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset_score', methods=['POST'])
@login_required
@admin_required
def reset_user_score(user_id):
    """Réinitialiser le score d'un utilisateur"""
    user = User.query.get_or_404(user_id)

    # Un admin ne peut pas reset le score d'un autre admin
    if user.role == "admin" and user.id != current_user.id:
        flash("❌ Vous ne pouvez pas réinitialiser le score d'un autre administrateur.", "danger")
        return redirect(url_for('admin.users'))

    # Supprimer toutes ses soumissions
    Submission.query.filter_by(user_id=user.id).delete()

    # Reset son scoreboard
    scoreboard = Scoreboard.query.filter_by(user_id=user.id).first()
    if scoreboard:
        scoreboard.points_total = 0

    db.session.commit()
    flash(f"🔄 Score de {user.pseudo} réinitialisé.", "info")
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/profile')
@login_required
@admin_required
def user_profile(user_id):
    from core.models import Submission, Scoreboard
    
    profile_user = User.query.get_or_404(user_id)
    
    # Stats
    total_submissions = Submission.query.filter_by(user_id=user_id).count()
    correct_submissions = Submission.query.filter_by(user_id=user_id, correct=True).count()
    
    # Challenges
    solved_challenges = profile_user.get_solved_challenges()
    in_progress = profile_user.get_in_progress_challenges()
    
    # Classement
    rank = Scoreboard.query.filter(
        Scoreboard.points_total > profile_user.score
    ).count() + 1
    
    # Toutes les soumissions
    submissions = Submission.query.filter_by(user_id=user_id)\
        .order_by(Submission.timestamp.desc()).all()
    
    return render_template(
        'admin/user_profile.html',
        profile_user=profile_user,
        total_submissions=total_submissions,
        correct_submissions=correct_submissions,
        solved_challenges=solved_challenges,
        in_progress=in_progress,
        rank=rank,
        submissions=submissions
    )

# ------------------------------
# GESTION DES CHALLENGES
# ------------------------------
@admin_bp.route('/challenges')
@login_required
@admin_required
def challenges():
    """Liste de tous les challenges"""
    all_challenges = Challenge.query.all()
    
    # Stats par challenge
    stats = []
    for challenge in all_challenges:
        total_attempts = Submission.query.filter_by(challenge_id=challenge.id).count()
        total_solved = Submission.query.filter_by(challenge_id=challenge.id, correct=True).count()
        success_rate = (total_solved / total_attempts * 100) if total_attempts > 0 else 0
        
        stats.append({
            'challenge': challenge,
            'total_attempts': total_attempts,
            'total_solved': total_solved,
            'success_rate': round(success_rate, 1)
        })
    
    return render_template('admin/challenges.html', stats=stats)

@admin_bp.route('/challenges/<int:challenge_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_challenge(challenge_id):
    """Activer/désactiver un challenge"""
    challenge = Challenge.query.get_or_404(challenge_id)
    challenge.actif = not challenge.actif
    db.session.commit()
    
    status = "activé" if challenge.actif else "désactivé"
    flash(f"✅ Challenge '{challenge.titre}' {status}.", "success")
    return redirect(url_for('admin.challenges'))

@admin_bp.route('/challenges/<int:challenge_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_challenge(challenge_id):
    """Modifier un challenge"""
    challenge = Challenge.query.get_or_404(challenge_id)
    
    if request.method == 'POST':
        challenge.titre = request.form.get('titre')
        challenge.description = request.form.get('description')
        challenge.points = int(request.form.get('points'))
        
        # Modifier le flag si fourni
        new_flag = request.form.get('flag')
        if new_flag:
            if challenge.flag:
                challenge.flag.setFlag(new_flag)
            else:
                flag = Flag(challenge_id=challenge.id)
                flag.setFlag(new_flag)
                db.session.add(flag)
        
        db.session.commit()
        flash(f"✅ Challenge '{challenge.titre}' modifié.", "success")
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/edit_challenge.html', challenge=challenge)

# ------------------------------
# HISTORIQUE DES SOUMISSIONS
# ------------------------------
@admin_bp.route('/submissions')
@login_required
@admin_required
def submissions():
    """Historique de toutes les soumissions avec filtres"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    per_page = 50
    
    # Base query
    query = Submission.query
    
    # Appliquer les filtres
    if status_filter == 'correct':
        query = query.filter_by(correct=True)
    elif status_filter == 'incorrect':
        query = query.filter_by(correct=False)
    
    # Pagination
    submissions_query = query.order_by(
        Submission.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/submissions.html', submissions=submissions_query)

# ── Gestion des flux RSS ──────────────────────────────────────
 
@admin_bp.route('/actualites')
@login_required
@admin_required
def rss_feeds():
    """Liste et gestion des flux RSS."""
    feeds = RssFeed.query.order_by(RssFeed.created_at.desc()).all()
    return render_template('admin/rss_feeds.html', feeds=feeds)
 
 
@admin_bp.route('/actualites/add', methods=['POST'])
@login_required
@admin_required
def rss_add():
    """Ajouter un nouveau flux RSS."""
    nom = request.form.get('nom', '').strip()
    url = request.form.get('url', '').strip()
    langue = request.form.get('langue', 'EN').strip()
 
    if not nom or not url:
        flash("❌ Nom et URL sont obligatoires.", "danger")
        return redirect(url_for('admin.rss_feeds'))
 
    if not url.startswith(('http://', 'https://')):
        flash("❌ L'URL doit commencer par http:// ou https://", "danger")
        return redirect(url_for('admin.rss_feeds'))
 
    existing = RssFeed.query.filter_by(url=url).first()
    if existing:
        flash("⚠️ Ce flux existe déjà.", "warning")
        return redirect(url_for('admin.rss_feeds'))
 
    feed = RssFeed(nom=nom, url=url, actif=False, langue=langue)
    db.session.add(feed)
    db.session.commit()
    flash(f"✅ Flux '{nom}' ajouté (désactivé par défaut).", "success")
    return redirect(url_for('admin.rss_feeds'))
 
 
@admin_bp.route('/actualites/<int:feed_id>/toggle', methods=['POST'])
@login_required
@admin_required
def rss_toggle(feed_id):
    """Activer / désactiver un flux RSS."""
    feed = RssFeed.query.get_or_404(feed_id)
    feed.actif = not feed.actif
    db.session.commit()
    status = "activé" if feed.actif else "désactivé"
    flash(f"✅ Flux '{feed.nom}' {status}.", "success")
    return redirect(url_for('admin.rss_feeds'))
 
 
@admin_bp.route('/actualites/<int:feed_id>/delete', methods=['POST'])
@login_required
@admin_required
def rss_delete(feed_id):
    """Supprimer un flux RSS."""
    feed = RssFeed.query.get_or_404(feed_id)
    nom = feed.nom
    db.session.delete(feed)
    db.session.commit()
    flash(f"🗑️ Flux '{nom}' supprimé.", "info")
    return redirect(url_for('admin.rss_feeds'))


# ------------------------------
# EXPORT SCOREBOARD
# ------------------------------
@admin_bp.route('/export')
@login_required
@admin_required
def export_scoreboard():
    """Export du classement en CSV"""
    
    # Récupérer le classement
    classement = Scoreboard.afficherClassement(limit=1000)
    
    # Créer le CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Rang', 'Pseudo', 'Email', 'Score', 'Date Inscription'])
    
    # Données
    for rank, (scoreboard, user) in enumerate(classement, start=1):
        writer.writerow([
            rank,
            user.pseudo,
            user.email,
            scoreboard.points_total,
            user.created_at.strftime('%d/%m/%Y')
        ])
    
    # Préparer le fichier pour téléchargement
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'scoreboard_{datetime.now().strftime("%Y%m%d")}.csv'
    )

# ── Dashboard sécurité ───────────────────────────────────────────────
@admin_bp.route('/security')
@login_required
@admin_required
def security():
    from core.security import get_dashboard_stats, BannedIP
    stats = get_dashboard_stats()
    banned_ips = BannedIP.query.order_by(BannedIP.banned_at.desc()).all()
    return render_template('admin/security.html', stats=stats, banned_ips=banned_ips)
 
 
# ── Bannir une IP ────────────────────────────────────────────────────
@admin_bp.route('/security/ban-ip', methods=['POST'])
@login_required
@admin_required
def ban_ip():
    from core.security import BannedIP
    ip      = request.form.get('ip', '').strip()
    reason  = request.form.get('reason', 'Brute-force détecté').strip()
 
    if not ip:
        flash("❌ IP invalide.", "danger")
        return redirect(url_for('admin.security'))
 
    existing = BannedIP.query.filter_by(ip_address=ip).first()
    if existing:
        flash(f"⚠️ L'IP {ip} est déjà bannie.", "warning")
        return redirect(url_for('admin.security'))
 
    ban = BannedIP(
        ip_address=ip,
        reason=reason,
        banned_by=current_user.id
    )
    db.session.add(ban)
    db.session.commit()
    flash(f"🔨 IP {ip} bannie avec succès.", "success")
    return redirect(url_for('admin.security'))
 
 
# ── Débannir une IP ──────────────────────────────────────────────────
@admin_bp.route('/security/unban-ip/<int:ban_id>', methods=['POST'])
@login_required
@admin_required
def unban_ip(ban_id):
    from core.security import BannedIP
    ban = BannedIP.query.get_or_404(ban_id)
    ip  = ban.ip_address
    db.session.delete(ban)
    db.session.commit()
    flash(f"✅ IP {ip} débannie.", "success")
    return redirect(url_for('admin.security'))
 
 
# ── Export CSV ───────────────────────────────────────────────────────
@admin_bp.route('/security/export/csv', methods=['POST'])
@login_required
@admin_required
def security_export_csv():
    from core.security import SecurityEvent
    import csv, io
 
    # Filtres choisis par l'admin
    selected_types = request.form.getlist('event_types')
    limit          = int(request.form.get('limit', 500))
    date_from      = request.form.get('date_from', '')
    date_to        = request.form.get('date_to', '')
 
    query = SecurityEvent.query
 
    if selected_types:
        query = query.filter(SecurityEvent.event_type.in_(selected_types))
 
    if date_from:
        try:
            query = query.filter(
                SecurityEvent.timestamp >= datetime.strptime(date_from, '%Y-%m-%d')
            )
        except ValueError:
            pass
 
    if date_to:
        try:
            query = query.filter(
                SecurityEvent.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            )
        except ValueError:
            pass
 
    events = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
 
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'IP', 'Utilisateur', 'Chemin', 'Détails', 'User-Agent'])
 
    for ev in events:
        writer.writerow([
            ev.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            ev.event_type,
            ev.ip_address or '',
            ev.user.pseudo if ev.user else '',
            ev.path or '',
            ev.extra or '',
            (ev.user_agent or '')[:100],
        ])
 
    output.seek(0)
    filename = f"cybercampus_security_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
 
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
 
 
# ── Export Word ──────────────────────────────────────────────────────
@admin_bp.route('/security/export/word', methods=['POST'])
@login_required
@admin_required
def security_export_word():
    from core.security import SecurityEvent, BannedIP, get_dashboard_stats
    import subprocess, tempfile, os, json
 
    selected_types = request.form.getlist('event_types')
    limit          = int(request.form.get('limit', 200))
    date_from      = request.form.get('date_from', '')
    date_to        = request.form.get('date_to', '')
    include_stats  = request.form.get('include_stats') == '1'
    include_banned = request.form.get('include_banned') == '1'
 
    # Récupérer les événements
    query = SecurityEvent.query
    if selected_types:
        query = query.filter(SecurityEvent.event_type.in_(selected_types))
    if date_from:
        try:
            query = query.filter(
                SecurityEvent.timestamp >= datetime.strptime(date_from, '%Y-%m-%d')
            )
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(
                SecurityEvent.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            )
        except ValueError:
            pass
 
    events = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
 
    # Stats et IPs bannies
    stats      = get_dashboard_stats() if include_stats else {}
    banned_ips = BannedIP.query.all() if include_banned else []
 
    # Sérialiser pour passer au script Node.js
    payload = {
        "generated_at": datetime.now().strftime('%d/%m/%Y à %H:%M'),
        "generated_by": current_user.pseudo,
        "include_stats": include_stats,
        "include_banned": include_banned,
        "stats": {
            "events_24h":      stats.get("events_24h", 0),
            "logins_ok_24h":   stats.get("logins_ok_24h", 0),
            "logins_fail_24h": stats.get("logins_fail_24h", 0),
            "flags_ok_24h":    stats.get("flags_ok_24h", 0),
            "flags_fail_24h":  stats.get("flags_fail_24h", 0),
            "suspicious_ips":  [(ip, cnt) for ip, cnt in stats.get("suspicious_ips", [])],
        } if include_stats else {},
        "banned_ips": [
            {
                "ip": b.ip_address,
                "reason": b.reason,
                "at": b.banned_at.strftime('%d/%m/%Y %H:%M'),
            }
            for b in banned_ips
        ],
        "events": [
            {
                "ts":   ev.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                "type": ev.event_type,
                "ip":   ev.ip_address or "?",
                "user": ev.user.pseudo if ev.user else "—",
                "path": ev.path or "—",
                "extra": ev.extra or "",
            }
            for ev in events
        ],
    }
 
    # Écrire le payload JSON temporaire
    tmp_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
    json.dump(payload, tmp_json, ensure_ascii=False)
    tmp_json.close()
 
    tmp_docx = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
    tmp_docx.close()
 
    # Appeler le script Node.js
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'gen_security_report.js')
    result = subprocess.run(
        ['node', script_path, tmp_json.name, tmp_docx.name],
        capture_output=True, text=True, timeout=30
    )
 
    os.unlink(tmp_json.name)
 
    if result.returncode != 0:
        os.unlink(tmp_docx.name)
        flash(f"❌ Erreur génération Word : {result.stderr[:200]}", "danger")
        return redirect(url_for('admin.security'))
 
    from flask import send_file
    filename = f"rapport_securite_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
    return send_file(
        tmp_docx.name,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )