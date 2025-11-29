# ------------------------------
# CyberCampus CTF - Application principale
# ------------------------------

from flask import Flask, render_template, url_for, redirect, request, flash  
from flask_login import login_required, current_user
from datetime import datetime # Import direct ici

from core import init_app, db
from core.models import User, Challenge, Submission  
from core.auth import auth_bp


# Création de l'application Flask
app = Flask(__name__, template_folder="./webapp/templates", static_folder="./webapp/static")

# Chargement de la configuration depuis config.py
app.config.from_object("config.Config")

# Initialisation des extensions (SQLAlchemy, LoginManager, etc.)
init_app(app)

# Enregistrement des blueprints
app.register_blueprint(auth_bp)

# ------------------------------
# Création automatique de la base de données
# ------------------------------
with app.app_context():
    try:
        db.create_all()
        print("✅ Base de données initialisée avec succès.")
    except Exception as e:
        print("⚠️ Erreur lors de la création des tables :", e)

# ------------------------------
# INJECTION GLOBALE (Règle vos erreurs 'undefined')
# ------------------------------
@app.context_processor
def inject_globals():
    """
    Injecte 'now', 'Challenge' et 'Submission' dans tous les templates.
    Cela corrige l'erreur même si la route vient de core/auth.py
    """
    return {
        'now': datetime.now,       # Pour calculer les jours depuis l'inscription
        'Challenge': Challenge,    # Pour compter le total des challenges
        'Submission': Submission   # Pour d'autres logiques si besoin
    }

# ------------------------------
# Routes
# ------------------------------

@app.route('/')
def root():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template("index.html")

# Note : Si vous avez déjà une route /dashboard dans auth_bp, celle-ci peut être ignorée par Flask.
# Mais grâce au context_processor ci-dessus, le template fonctionnera dans les deux cas.
@app.route('/dashboard')
@login_required
def dashboard():
    """Page du tableau de bord (protégée)"""
    return render_template("dashboard.html", user=current_user)

@app.route('/challenges')
@login_required
def challenges_list():
    """Page listant tous les challenges disponibles"""
    challenges = Challenge.query.filter_by(actif=True).all()
    return render_template("challenges_list.html", challenges=challenges)

@app.route('/challenge/<int:challenge_id>')
@login_required
def challenge_view(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    if not challenge.actif:
        flash("Ce challenge n'est pas encore disponible.", "warning")
        return redirect(url_for('dashboard'))
    
    return render_template("challenge.html", challenge=challenge)

@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    flag_soumis = request.form.get('flag', '').strip()
    
    submission = Submission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        flag_soumis=flag_soumis
    )
    
    if submission.enregistrer():
        flash(f"✅ Bravo ! Flag correct ! +{challenge.points} points", "success")
    else:
        flash("❌ Flag incorrect. Réessayez !", "danger")
    
    return redirect(url_for('challenge_view', challenge_id=challenge_id))

# ------------------------------
# Point d'entrée du programme (mode local)
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)