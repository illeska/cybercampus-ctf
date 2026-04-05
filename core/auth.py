# ------------------------------
# CyberCampus CTF - Authentification (Blueprint)
# ------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from core.forms import RegisterForm, LoginForm
from core.models import User, EmailVerification
from core import db, mail
from datetime import datetime
import random

# Création du blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

# ------------------------------
# Fonctions utilitaires
# ------------------------------

def generate_code():
    """Génère un code aléatoire à 6 chiffres"""
    return str(random.randint(100000, 999999))

def send_verification_code(user_email, code):
    """Envoie le code de vérification par email"""
    msg = Message(
        subject="🔐 Votre code de vérification - CyberCampus CTF",
        recipients=[user_email],
        html=f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; 
                    background: #050a10; color: #fff; padding: 40px; border-radius: 10px;">
            <h1 style="color: #00f5c0; text-align: center;">CyberCampus CTF</h1>
            <h2 style="text-align: center;">Vérification de votre email</h2>
            <p>Merci de vous être inscrit sur CyberCampus CTF !</p>
            <p>Voici votre code de vérification :</p>
            <div style="text-align: center; margin: 30px 0;">
                <div style="background: #1e293b; color: #00f5c0; padding: 20px 40px; 
                            border-radius: 10px; font-size: 2.5rem; font-weight: bold; 
                            letter-spacing: 10px; display: inline-block; 
                            border: 2px solid #00f5c0;">
                    {code}
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 0.9rem; text-align: center;">
                Ce code expire dans <strong style="color: #fff;">15 minutes</strong>.
            </p>
            <p style="color: #94a3b8; font-size: 0.9rem; text-align: center;">
                Si vous n'avez pas créé de compte, ignorez cet email.
            </p>
            <hr style="border-color: #1e293b; margin: 30px 0;">
            <p style="color: #64748b; font-size: 0.8rem; text-align: center;">
                © 2026 CyberCampus CTF — no-reply@cybercampus-ctf.fr
            </p>
        </div>
        """
    )
    mail.send(msg)

def create_verification_code(user_id):
    """Crée un nouveau code de vérification en BDD (supprime les anciens)"""
    # Supprimer les anciens codes
    EmailVerification.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    # Créer le nouveau code
    code = generate_code()
    verification = EmailVerification(
        user_id=user_id,
        code=code
    )
    db.session.add(verification)
    db.session.commit()
    return code

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

        # Générer et envoyer le code
        try:
            code = create_verification_code(new_user.id)
            send_verification_code(new_user.email, code)
            # Stocker l'user_id en session pour la page de vérification
            session['verify_user_id'] = new_user.id
            flash("Un code de vérification a été envoyé à votre adresse email.", "success")
        except Exception as e:
            flash("Compte créé mais erreur d'envoi du mail. Contactez un admin.", "warning")

        return redirect(url_for("auth.verify_email_page"))

    return render_template("register.html", form=form)

# ------------------------------
# Route de vérification email (page)
# ------------------------------
@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email_page():
    """Page de vérification du code reçu par email"""

    # Récupérer l'user_id depuis la session
    user_id = session.get('verify_user_id')

    if not user_id:
        flash("Session expirée. Veuillez vous reconnecter.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)

    if not user:
        flash("Utilisateur introuvable.", "danger")
        return redirect(url_for("auth.login"))

    # Si déjà vérifié, rediriger vers l'accueil
    if user.email_verified:
        session.pop('verify_user_id', None)
        return redirect(url_for("home"))

    # Récupérer le dernier code
    verification = EmailVerification.query.filter_by(
        user_id=user_id, used=False
    ).order_by(EmailVerification.created_at.desc()).first()

    # Calculer le temps restant avant de pouvoir renvoyer
    can_resend = True
    resend_countdown = 0
    if verification:
        elapsed = (datetime.utcnow() - verification.created_at).total_seconds()
        if elapsed < 30:
            can_resend = False
            resend_countdown = int(30 - elapsed)

    if request.method == "POST":
        action = request.form.get("action")

        # Renvoyer un nouveau code
        if action == "resend":
            if not can_resend:
                flash(f"Attendez encore {resend_countdown} secondes avant de renvoyer.", "warning")
            else:
                try:
                    code = create_verification_code(user_id)
                    send_verification_code(user.email, code)
                    flash("Un nouveau code a été envoyé !", "success")
                except Exception:
                    flash("Erreur d'envoi du mail.", "danger")
            return redirect(url_for("auth.verify_email_page"))

        # Vérifier le code
        if action == "verify":
            code_saisi = request.form.get("code", "").strip()

            if not verification:
                flash("Aucun code actif. Demandez un nouveau code.", "danger")
                return redirect(url_for("auth.verify_email_page"))

            if verification.is_expired():
                flash("Code expiré. Demandez un nouveau code.", "danger")
                EmailVerification.query.filter_by(user_id=user_id).delete()
                db.session.commit()
                return redirect(url_for("auth.verify_email_page"))

            if verification.code == code_saisi:
                # Code correct → activer le compte
                verification.used = True
                user.email_verified = True
                db.session.commit()

                # Nettoyer la session
                session.pop('verify_user_id', None)

                flash("✅ Email vérifié avec succès ! Vous pouvez vous connecter.", "success")
                return redirect(url_for("auth.login"))
            else:
                flash("❌ Code incorrect. Réessayez.", "danger")
                return redirect(url_for("auth.verify_email_page"))

    return render_template(
        "verify_email.html",
        user=user,
        can_resend=can_resend,
        resend_countdown=resend_countdown
    )

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
                session['verify_user_id'] = user.id
                flash("⚠️ Veuillez vérifier votre email avant de vous connecter.", "warning")
                return redirect(url_for("auth.verify_email_page"))

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