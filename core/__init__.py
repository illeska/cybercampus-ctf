# ------------------------------
# CyberCampus CTF - Initialisation du module core
# ------------------------------

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def init_app(app):
    """Initialise les extensions avec l'application Flask"""
    db.init_app(app)
    login_manager.init_app(app)

    # Initialisation de Flask-Mail
    mail.init_app(app)
    
    # Page par défaut si l'utilisateur non connecté tente d'accéder à une page protégée
    login_manager.login_view = "auth.login"
    
