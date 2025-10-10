# ------------------------------
# CyberCampus CTF - Authentification (Blueprint)
# ------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash, request
from core.forms import RegisterForm
from core.models import User
from core import db
from flask_login import login_user, logout_user, login_required, current_user

# Création du blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

# ------------------------------
# Route d'inscription
# ------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Si l'utilisateur est déjà connecté, on le redirige
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    
    if form.validate_on_submit():
        # Vérifier si l'email ou le pseudo existent déjà
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.pseudo == form.pseudo.data)
        ).first()

        if existing_user:
            flash("Ce pseudo ou cet email existe déjà.", "danger")
            return redirect(url_for("auth.register"))

        # Créer un nouvel utilisateur
        new_user = User(
            pseudo=form.pseudo.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)

from core.forms import RegisterForm, LoginForm  # <-- ajoute LoginForm ici

# ------------------------------
# Route de connexion
# ------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        # Rechercher l'utilisateur par email
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f"Bienvenue {user.pseudo} !", "success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html", form=form)

# ------------------------------
# Route de déconnexion
# ------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Déconnecté avec succès.", "info")
    return redirect(url_for("auth.login"))

# ------------------------------
# Route du tableau de bord (après connexion)
# ------------------------------
@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

# Note: Le décorateur @login_required protège cette route pour que seuls les utilisateurs connectés puissent y accéder.
# ------------------------------
# Fin du fichier auth.py
# ------------------------------


