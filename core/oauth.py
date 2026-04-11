from flask import redirect, url_for, flash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_login import login_user
from core.models import User
from core import db
import os
import random
import string
import re

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
)

def generate_unique_pseudo(base_pseudo):
    clean = re.sub(r'[^a-zA-Z0-9_-]', '', base_pseudo.replace(' ', '_'))
    clean = clean[:45]
    if len(clean) < 3:
        clean = "hacker"
    if not User.query.filter_by(pseudo=clean).first():
        return clean
    for _ in range(10):
        suffix = random.randint(10, 9999)
        candidate = f"{clean}_{suffix}"
        if not User.query.filter_by(pseudo=candidate).first():
            return candidate
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
    return f"{clean}_{random_suffix}"


@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Connexion Google échouée.", "danger")
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Impossible de récupérer les informations Google.", "danger")
        return False

    info = resp.json()
    email = info.get("email")
    google_name = info.get("name", "")

    base_pseudo = google_name if google_name else email.split("@")[0]

    user = User.query.filter_by(email=email).first()

    if not user:
        pseudo = generate_unique_pseudo(base_pseudo)
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

    # Retourner False empêche Flask-Dance de stocker le token en DB
    return False