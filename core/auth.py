# ------------------------------
# CyberCampus CTF - Authentification (Blueprint)
# ------------------------------

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from core.forms import RegisterForm, LoginForm
from core.models import User, EmailVerification
from core import db, mail
from datetime import datetime
import random
import requests as http_requests
from core.security import SecurityEvent, detect_bruteforce

# Création du blueprint d'authentification
auth_bp = Blueprint('auth', __name__)

# ------------------------------
# Fonctions utilitaires
# ------------------------------


#------------------------------
# Recapcha 
# ------------------------------
def verify_recaptcha(response_token):
    secret = current_app.config['RECAPTCHA_PRIVATE_KEY']
    r = http_requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': secret,
        'response': response_token
    })
    return r.json().get('success', False) 

def generate_code():
    """Génère un code aléatoire à 6 chiffres"""
    return str(random.randint(100000, 999999))

def send_verification_code(user_email, code):
    """Envoie le code de vérification par email"""
    msg = Message(
        subject="Votre code de vérification - CyberCampus CTF 🔐",
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
                © 2026 CyberCampus CTF - no-reply@cybercampus-ctf.fr
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
        # RECAPTCHA
        token = request.form.get('g-recaptcha-response')
        if not token or not verify_recaptcha(token):
            flash('Veuillez valider le CAPTCHA.', 'error')
            return render_template('register.html', form=form)
        
        # Vérifier que les CGU ont été acceptées
        if not request.form.get('accept_cgu'):
            flash("Vous devez accepter les CGU et la politique de confidentialité pour vous inscrire.", "danger")
            return redirect(url_for("auth.register"))
        
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

        new_user.ip_address = request.remote_addr
        db.session.commit()
        SecurityEvent.log(
            SecurityEvent.REGISTER,
            ip=request.remote_addr,
            user_id=new_user.id,
            extra={"pseudo": new_user.pseudo}
        )

        # Générer et envoyer le code
        try:
            code = create_verification_code(new_user.id)
            send_verification_code(new_user.email, code)
            # Stocker l'user_id en session pour la page de vérification
            session['verify_user_id'] = new_user.id
            flash("Un code de vérification a été envoyé à votre adresse email.", "success")
        except Exception as e:
            pass

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
        # RECAPTCHA
        token = request.form.get('g-recaptcha-response')
        if not token or not verify_recaptcha(token):
            flash('Veuillez valider le CAPTCHA.', 'error')
            return render_template('login.html', form=form)
        
        # Rechercher l'utilisateur par email
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            
            # Vérifier si l'email est confirmé
            if not user.email_verified:
                session['verify_user_id'] = user.id
                flash("⚠️ Veuillez vérifier votre email avant de vous connecter.", "warning")
                return redirect(url_for("auth.verify_email_page"))

            login_user(user)
            user.last_ip    = request.remote_addr
            user.last_seen  = dt.utcnow()
            user.login_count = (user.login_count or 0) + 1
            db.session.commit()

            SecurityEvent.log(
                SecurityEvent.LOGIN_OK,
                ip=request.remote_addr,
                user_id=user.id,
                extra={"pseudo": user.pseudo}
            )

            flash(f"Bienvenue {user.pseudo} !", "success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
            SecurityEvent.log(
            SecurityEvent.LOGIN_FAIL,
            ip=request.remote_addr,
            extra={"email_tried": form.email.data}
            )
            # Détecter le brute-force
            if detect_bruteforce(request.remote_addr):
                SecurityEvent.log(
                    SecurityEvent.BRUTE_SUSPECT,
                    ip=request.remote_addr,
                    extra={"reason": "Too many failed logins in 5min"}
                )
                return redirect(url_for("auth.login"))
            
        if user and user.role == "banned":
            SecurityEvent.log(
                SecurityEvent.BANNED_ATTEMPT,
                ip=request.remote_addr,
                user_id=user.id,
                extra={"pseudo": user.pseudo}
            )
            flash("Votre compte a été banni.", "danger")
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
# Routes de suppression de compte
# ------------------------------
 
@auth_bp.route("/account/delete/request", methods=["POST"])
@login_required
def request_delete_account():
    """Envoie un email de confirmation de suppression"""
    user = current_user
 
    # Générer un token sécurisé
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps(user.email, salt='delete-account')
 
    confirm_url = url_for('auth.confirm_delete_account', token=token, _external=True)
 
    # Envoyer l'email de confirmation
    try:
        msg = Message(
            subject="Confirmation de suppression de compte - CyberCampus CTF ⚠️",
            recipients=[user.email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
                        background: #050a10; color: #fff; padding: 40px; border-radius: 10px;">
                <h1 style="color: #ef4444; text-align: center;">CyberCampus CTF</h1>
                <h2 style="text-align: center; color: #fff;">Suppression de compte</h2>
 
                <p>Bonjour <strong style="color: #00f5c0;">{user.pseudo}</strong>,</p>
                <p>
                    Nous avons reçu une demande de suppression de votre compte.
                    Si vous n'êtes pas à l'origine de cette demande, ignorez cet email — votre compte restera intact.
                </p>
                <p>Si vous souhaitez confirmer la suppression, cliquez sur le bouton ci-dessous :</p>
 
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{confirm_url}"
                       style="background: #ef4444; color: #fff; padding: 15px 35px;
                              border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.05rem;">
                        🗑️ Confirmer la suppression
                    </a>
                </div>
 
                <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
                            border-radius: 8px; padding: 15px; margin-top: 20px;">
                    <p style="color: #ef4444; margin: 0; font-size: 0.9rem;">
                        ⚠️ Cette action est <strong>irréversible</strong>.
                        Toutes vos données (progression, scores, soumissions) seront définitivement supprimées.
                        Ce lien expire dans <strong>1 heure</strong>.
                    </p>
                </div>
 
                <hr style="border-color: #1e293b; margin: 30px 0;">
                <p style="color: #64748b; font-size: 0.8rem; text-align: center;">
                    © 2026 CyberCampus CTF — no-reply@cybercampus-ctf.fr
                </p>
            </div>
            """
        )
        mail.send(msg)
        flash("📧 Un email de confirmation vous a été envoyé. Vérifiez votre boîte mail.", "info")
    except Exception:
        flash("❌ Erreur d'envoi du mail. Réessayez plus tard.", "danger")
 
    return redirect(url_for('dashboard'))
 


@auth_bp.route("/account/delete/confirm/<token>", methods=["GET", "POST"])
@login_required
def confirm_delete_account(token):
    """Page de confirmation finale avec saisie du mot de passe"""
 
    # Vérifier le token
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='delete-account', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("❌ Le lien de suppression est invalide ou expiré.", "danger")
        return redirect(url_for('dashboard'))
 
    # Vérifier que le token correspond bien à l'utilisateur connecté
    if email != current_user.email:
        flash("❌ Ce lien ne vous appartient pas.", "danger")
        return redirect(url_for('dashboard'))
 
    if request.method == "POST":
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
 
        if not current_user.check_password(password):
            flash("❌ Mot de passe incorrect.", "danger")
            return redirect(url_for('auth.confirm_delete_account', token=token))
 
        if password != confirm:
            flash("❌ Les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for('auth.confirm_delete_account', token=token))
 
        # Supprimer toutes les données de l'utilisateur
        user_id = current_user.id
        user_pseudo = current_user.pseudo
        user_email = current_user.email
 
        # Déconnecter avant suppression
        logout_user()
 
        # Supprimer les données liées
        from core.models import Submission, Scoreboard, EmailVerification
        Submission.query.filter_by(user_id=user_id).delete()
        Scoreboard.query.filter_by(user_id=user_id).delete()
        EmailVerification.query.filter_by(user_id=user_id).delete()
 
        # Supprimer l'utilisateur
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
 
        # Envoyer email de confirmation de suppression
        try:
            msg = Message(
                subject="✅ Votre compte a été supprimé - CyberCampus CTF",
                recipients=[user_email],
                html=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
                            background: #050a10; color: #fff; padding: 40px; border-radius: 10px;">
                    <h1 style="color: #00f5c0; text-align: center;">CyberCampus CTF</h1>
                    <h2 style="text-align: center;">Compte supprimé</h2>
                    <p>Bonjour <strong>{user_pseudo}</strong>,</p>
                    <p>
                        Votre compte et toutes vos données ont été définitivement supprimés de notre plateforme.
                        Nous espérons vous revoir un jour !
                    </p>
                    <hr style="border-color: #1e293b; margin: 30px 0;">
                    <p style="color: #64748b; font-size: 0.8rem; text-align: center;">
                        © 2026 CyberCampus CTF — no-reply@cybercampus-ctf.fr
                    </p>
                </div>
                """
            )
            mail.send(msg)
        except Exception:
            pass
 
        return redirect(url_for('auth.account_deleted'))
 
    return render_template("confirm_delete_account.html", token=token)
 
 
@auth_bp.route("/account/deleted")
def account_deleted():
    """Page affichée après suppression du compte"""
    return render_template("account_deleted.html")
 


# ------------------------------
# Routes de modification de profil
# ------------------------------

from datetime import datetime as dt

@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Page de modification du profil"""

    if request.method == "POST":
        action = request.form.get("action")

        # ------------------------------
        # Action : Infos personnelles
        # ------------------------------
        if action == "personal_info":
            birth_year = request.form.get("birth_year", "").strip()
            country = request.form.get("country", "").strip()
            gender = request.form.get("gender", "").strip()

            # Validation année de naissance
            if birth_year:
                try:
                    birth_year_int = int(birth_year)
                    current_year = dt.utcnow().year
                    age = current_year - birth_year_int
                    if age < 16:
                        flash("❌ Vous devez avoir au moins 16 ans.", "danger")
                        return redirect(url_for("auth.edit_profile"))
                    if birth_year_int < 1900 or birth_year_int > current_year:
                        flash("❌ Année de naissance invalide.", "danger")
                        return redirect(url_for("auth.edit_profile"))
                    current_user.birth_year = birth_year_int
                except ValueError:
                    flash("❌ Année de naissance invalide.", "danger")
                    return redirect(url_for("auth.edit_profile"))
            else:
                current_user.birth_year = None

            current_user.country = country if country else None
            current_user.gender = gender if gender else None
            db.session.commit()
            flash("✅ Informations personnelles mises à jour.", "success")
            return redirect(url_for("auth.edit_profile"))

        # ------------------------------
        # Action : Changer le pseudo
        # ------------------------------
        if action == "change_pseudo":
            new_pseudo = request.form.get("pseudo", "").strip()

            if not new_pseudo:
                flash("❌ Le pseudo ne peut pas être vide.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if len(new_pseudo) < 3 or len(new_pseudo) > 50:
                flash("❌ Le pseudo doit contenir entre 3 et 50 caractères.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if new_pseudo == current_user.pseudo:
                flash("⚠️ C'est déjà votre pseudo actuel.", "warning")
                return redirect(url_for("auth.edit_profile"))

            existing = User.query.filter_by(pseudo=new_pseudo).first()
            if existing:
                flash("❌ Ce pseudo est déjà pris.", "danger")
                return redirect(url_for("auth.edit_profile"))

            current_user.pseudo = new_pseudo
            db.session.commit()
            flash("✅ Pseudo mis à jour avec succès.", "success")
            return redirect(url_for("auth.edit_profile"))

        # ------------------------------
        # Action : Changer l'email
        # ------------------------------
        if action == "change_email":
            new_email = request.form.get("new_email", "").strip().lower()

            if not new_email:
                flash("❌ L'email ne peut pas être vide.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if new_email == current_user.email:
                flash("⚠️ C'est déjà votre email actuel.", "warning")
                return redirect(url_for("auth.edit_profile"))

            existing = User.query.filter_by(email=new_email).first()
            if existing:
                flash("❌ Cet email est déjà utilisé.", "danger")
                return redirect(url_for("auth.edit_profile"))

            # Stocker le nouvel email en attente
            current_user.new_email_pending = new_email
            db.session.commit()

            # Générer le token et envoyer l'email de confirmation
            s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = s.dumps(
                {"user_id": current_user.id, "new_email": new_email},
                salt='change-email'
            )
            confirm_url = url_for('auth.confirm_change_email', token=token, _external=True)

            try:
                msg = Message(
                    subject="✉️ Confirmez votre nouvel email - CyberCampus CTF",
                    recipients=[new_email],
                    html=f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
                                background: #050a10; color: #fff; padding: 40px; border-radius: 10px;">
                        <h1 style="color: #00f5c0; text-align: center;">CyberCampus CTF</h1>
                        <h2 style="text-align: center;">Confirmation de votre nouvel email</h2>
                        <p>Bonjour <strong style="color: #00f5c0;">{current_user.pseudo}</strong>,</p>
                        <p>
                            Vous avez demandé à changer votre adresse email sur CyberCampus CTF.
                            Cliquez sur le bouton ci-dessous pour confirmer votre nouvel email :
                        </p>
                        <div style="text-align: center; margin: 35px 0;">
                            <a href="{confirm_url}"
                               style="background: #00f5c0; color: #050a10; padding: 15px 35px;
                                      border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.05rem;">
                                ✅ Confirmer mon nouvel email
                            </a>
                        </div>
                        <p style="color: #94a3b8; font-size: 0.9rem; text-align: center;">
                            Ce lien expire dans <strong style="color: #fff;">1 heure</strong>.
                            Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
                        </p>
                        <hr style="border-color: #1e293b; margin: 30px 0;">
                        <p style="color: #64748b; font-size: 0.8rem; text-align: center;">
                            © 2026 CyberCampus CTF — no-reply@cybercampus-ctf.fr
                        </p>
                    </div>
                    """
                )
                mail.send(msg)
                flash(f"📧 Un email de confirmation a été envoyé à {new_email}. Vérifiez votre boîte mail.", "info")
            except Exception:
                flash("❌ Erreur d'envoi du mail. Réessayez plus tard.", "danger")

            return redirect(url_for("auth.edit_profile"))

        # ------------------------------
        # Action : Changer le mot de passe
        # ------------------------------
        if action == "change_password":
            old_password = request.form.get("old_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_user.check_password(old_password):
                flash("❌ Mot de passe actuel incorrect.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if len(new_password) < 8:
                flash("❌ Le nouveau mot de passe doit contenir au moins 8 caractères.", "danger")
                return redirect(url_for("auth.edit_profile"))

            import re
            if not re.search(r'\d', new_password):
                flash("❌ Le nouveau mot de passe doit contenir au moins un chiffre.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]', new_password):
                flash("❌ Le nouveau mot de passe doit contenir au moins un caractère spécial.", "danger")
                return redirect(url_for("auth.edit_profile"))

            if new_password != confirm_password:
                flash("❌ Les mots de passe ne correspondent pas.", "danger")
                return redirect(url_for("auth.edit_profile"))

            current_user.set_password(new_password)
            db.session.commit()
            flash("✅ Mot de passe mis à jour avec succès.", "success")
            return redirect(url_for("auth.edit_profile"))

    return render_template("edit_profile.html", user=current_user)


@auth_bp.route("/profile/email/confirm/<token>")
@login_required
def confirm_change_email(token):
    """Confirme le changement d'email via le lien reçu"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='change-email', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("❌ Le lien de confirmation est invalide ou expiré.", "danger")
        return redirect(url_for("auth.edit_profile"))

    user_id = data.get("user_id")
    new_email = data.get("new_email")

    if user_id != current_user.id:
        flash("❌ Ce lien ne vous appartient pas.", "danger")
        return redirect(url_for("auth.edit_profile"))

    # Vérifier que l'email n'est pas déjà pris
    existing = User.query.filter_by(email=new_email).first()
    if existing and existing.id != current_user.id:
        flash("❌ Cet email est déjà utilisé par un autre compte.", "danger")
        return redirect(url_for("auth.edit_profile"))

    # Appliquer le changement
    current_user.email = new_email
    current_user.new_email_pending = None
    db.session.commit()

    flash("✅ Votre email a été mis à jour avec succès.", "success")
    return redirect(url_for("auth.edit_profile"))


# ------------------------------
# Fin du fichier auth.py
# ------------------------------