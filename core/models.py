# ------------------------------
# CyberCampus CTF - Modèles de la base de données
# ------------------------------

from core import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Modèle utilisateur (issu du diagramme UML)
class User(UserMixin, db.Model):
    __tablename__ = "User"  # Nom de la table

    id = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Méthode pour définir un mot de passe haché
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Méthode pour vérifier un mot de passe
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Fonction de rappel pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la BDD à partir de son ID"""
    return User.query.get(int(user_id))
