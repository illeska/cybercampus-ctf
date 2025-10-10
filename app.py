# ------------------------------
# CyberCampus CTF - Application principale
# ------------------------------

from flask import Flask, render_template # Importe le framework Flask
from flask_login import login_required,current_user  # Importe le décorateur pour protéger les routes
from core import init_app,db  # Importe la fonction d'initialisation des extensions
from core.models import User  # Importe le modèle User pour la création de la base de données
from core.auth import auth_bp  # Importe le blueprint d'authentification

# Création de l'application Flask
app = Flask(__name__, template_folder="./webapp/templates", static_folder="./webapp/static")

# Chargement de la configuration depuis le fichier config.py
app.config.from_object("config.Config")

# Initialisation des extensions (base de données, gestion des utilisateurs, etc.)
init_app(app)
# Enregistrement du blueprint d'authentification
app.register_blueprint(auth_bp)

# Définition d'une route : la page d'accueil apres connexion

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

# Définition d'une route : la page d'accueil "/"
@app.route('/')
def home():
    return render_template("index.html")

# Point d'entrée du programme
if __name__ == "__main__":
    # Initialisation des extensions avec l'application Flask
    with app.app_context():
        db.create_all()  # Crée les tables de la base de données si elles n'existent pas
    # Lancement du serveur web local
    app.run(debug=True)
