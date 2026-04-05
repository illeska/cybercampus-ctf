# ------------------------------
# CyberCampus CTF - Authentification (Blueprint)
# ------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from core.forms import RegisterForm, LoginForm
from core.models import User
from core import db, mail

# Création du blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

# ------------------------------
# Fonctions utilitaires pour la vérification email
# ------------------------------

def generate_token(email):
    """Génère un token sécurisé pour la vérification email"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
    """Vérifie et décode le token (expire après 1h)"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-confirm', max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None
    return email

def send_verification_email(user_email):
    """Envoie l'email de vérification à l'utilisateur"""
    token = generate_token(user_email)
    confirm_url = url_for('auth.verify_email', token=token, _external=True)

    msg = Message(
        subject="🔐 Vérifiez votre adresse email - CyberCampus CTF",
        recipients=[user_email],
        html=f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #050a10; color: #fff; padding: 40px; border-radius: 10px;">
            <h1 style="color: #00f5c0; text-align: center;">CyberCampus CTF</h1>
            <h2 style="text-align: center;">Vérification de votre email</h2>
            <p>Merci de vous être inscrit sur CyberCampus CTF !</p>
            <p>Cliquez sur le bouton ci-dessous pour activer votre compte :</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{confirm_url}" 
                   style="background: #00f5c0; color: #050a10; padding: 15px 30px; 
                          border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1rem;">
                    ✅ Vérifier mon email
                </a>
            </div>
            <p style="color: #94a3b8; font-size: 0.9rem;">Ce lien expire dans <strong>1 heure</strong>.</p>
            <p style="color: #94a3b8; font-size: 0.9rem;">Si vous n'avez pas créé de compte, ignorez cet email.</p>
            <hr style="border-color: #1e293b; margin: 30px 0;">
            <p style="color: #64748b; font-size: 0.8rem; text-align: center;">
                © 2026 CyberCampus CTF — no-reply@cybercampus-ctf.fr
            </p>
        </div>
        """
    )
    mail.send(msg)

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

        # Créer un nouvel utilisateur (non vérifié par défaut)
        new_user = User(
            pseudo=form.pseudo.data,
            email=form.email.data,
            email_verified=False
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        # Envoyer l'email de vérification
        try:
            send_verification_email(new_user.email)
            flash("Compte créé ! Vérifiez votre boîte mail pour activer votre compte.", "success")
        except Exception as e:
            flash("Compte créé mais erreur d'envoi du mail. Contactez un admin.", "warning")

        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)

# ------------------------------
# Route de vérification email
# ------------------------------
@auth_bp.route("/verify/<token>")
def verify_email(token):
    """Vérifie le token reçu par email et active le compte"""
    email = confirm_token(token)

    if not email:
        flash("Le lien de vérification est invalide ou expiré.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("auth.login"))

    if user.email_verified:
        flash("Votre email est déjà vérifié. Connectez-vous !", "info")
        return redirect(url_for("auth.login"))

    # Activer le compte
    user.email_verified = True
    db.session.commit()
    flash("✅ Email vérifié avec succès ! Vous pouvez vous connecter.", "success")
    return redirect(url_for("auth.login"))

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
            # Vérifier si l'email est confirmé
            if not user.email_verified:
                flash("⚠️ Veuillez vérifier votre email avant de vous connecter.", "warning")
                return redirect(url_for("auth.login"))

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