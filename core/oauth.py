from flask import redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user
from core.models import User
from core import db
import os
import random
import string

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_url="/auth/google/authorized"
)

def generate_unique_pseudo(base_pseudo):
    """
    Génère un pseudo unique à partir d'un pseudo de base.
    Essaie d'abord le pseudo tel quel, puis ajoute des suffixes si nécessaire.
    """
    # Nettoyer le pseudo (enlever espaces, caractères spéciaux)
    import re
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', base_pseudo.replace(' ', '_'))
    
    # Limiter à 50 caractères max (contrainte du modèle)
    clean = clean[:45]
    
    # Si le pseudo nettoyé est trop court, utiliser un fallback
    if len(clean) < 3:
        clean = "hacker"
    
    # Vérifier si le pseudo est déjà pris
    if not User.query.filter_by(pseudo=clean).first():
        return clean
    
    # Essayer avec des suffixes numériques : pseudo_42, pseudo_137, etc.
    for _ in range(10):
        suffix = random.randint(10, 9999)
        candidate = f"{clean}_{suffix}"
        if not User.query.filter_by(pseudo=candidate).first():
            return candidate
    
    # En dernier recours, suffixe aléatoire en lettres
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
    return f"{clean}_{random_suffix}"


def handle_google_callback():
    if not google.authorized:
        flash("Connexion Google échouée.", "danger")
        return redirect(url_for("auth.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Impossible de récupérer les informations Google.", "danger")
        return redirect(url_for("auth.login"))

    info = resp.json()
    email = info.get("email")
    google_name = info.get("name", "")
    
    # Base du pseudo : nom Google ou partie avant le @ de l'email
    base_pseudo = google_name if google_name else email.split("@")[0]

    # Chercher si l'utilisateur existe déjà (par email)
    user = User.query.filter_by(email=email).first()

    if not user:
        # Générer un pseudo unique
        pseudo = generate_unique_pseudo(base_pseudo)
        
        # Mot de passe aléatoire sécurisé (l'utilisateur se connectera via Google)
        fake_password = ''.join(random.choices(
            string.ascii_letters + string.digits + string.punctuation, k=32
        ))
        
        user = User(
            pseudo=pseudo,
            email=email,
            email_verified=True,
            role="user"
        )
        user.set_password(fake_password)
        db.session.add(user)
        db.session.commit()
        
        flash(f"Compte créé via Google ! Votre pseudo est : {pseudo} 👾", "success")
    else:
        flash(f"Bienvenue {user.pseudo} !", "success")

    login_user(user)
    return redirect(url_for("dashboard"))