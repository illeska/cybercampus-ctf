# ------------------------------
# CyberCampus CTF - Application principale
# ------------------------------

from flask import Flask, render_template
from flask_login import login_required, current_user
from core import init_app, db
from core.models import User
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
# Routes
# ------------------------------

@app.route('/')
def home():
    """Page d'accueil du site"""
    return render_template("index.html")

@app.route('/dashboard')
@login_required
def dashboard():
    """Page du tableau de bord (protégée)"""
    return render_template("dashboard.html", user=current_user)


# ------------------------------
# Point d'entrée du programme (mode local)
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
