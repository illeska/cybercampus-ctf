# ------------------------------
# CyberCampus CTF - Panel Admin
# ------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from core import db
from core.models import User, Challenge, Submission, Scoreboard, Flag
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
    
    # Supprimer toutes ses soumissions
    Submission.query.filter_by(user_id=user.id).delete()
    
    # Reset son scoreboard
    scoreboard = Scoreboard.query.filter_by(user_id=user.id).first()
    if scoreboard:
        scoreboard.points_total = 0
    
    db.session.commit()
    flash(f"🔄 Score de {user.pseudo} réinitialisé.", "info")
    return redirect(url_for('admin.users'))

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