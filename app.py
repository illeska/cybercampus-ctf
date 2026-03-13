# ------------------------------
# CyberCampus CTF - Application principale avec système de hints
# ------------------------------

from flask import Flask, render_template, url_for, redirect, request, flash, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from core import init_app, db
from core.models import User, Challenge, Submission, Scoreboard
from core.auth import auth_bp
from core.admin import admin_bp

import os


# Création de l'application Flask.
app = Flask(__name__, template_folder="./webapp/templates", static_folder="./webapp/static")

# Chargement de la configuration depuis config.py
app.config.from_object("config.Config")

app.config.update(
    SESSION_COOKIE_SECURE=True,    # Force le cookie à ne passer que par HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Empêche le JavaScript de voler le cookie (sécurité anti-XSS)
    SESSION_COOKIE_SAMESITE='Lax', # Permet de garder la session lors de la navigation interne
    SESSION_COOKIE_NAME='cybercampus_session', # Un nom unique pour ton CTF
    PERMANENT_SESSION_LIFETIME=31536000 # Session d'une année
)

# Initialisation des extensions (SQLAlchemy, LoginManager, etc.)
init_app(app)

print("DB URI =", app.config["SQLALCHEMY_DATABASE_URI"])

# Enregistrement des blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

@app.errorhandler(404)
def page_not_found(e):
    # On renvoie directement le HTML sans passer par render_template
    return """
    <html>
        <head><title>404 - CyberCampus</title></head>
        <body style="font-family:sans-serif; text-align:center; padding-top:50px;">
            <h1>404 - Page non trouvée</h1>
            <p>Désolé, cette page n'existe pas.</p>
            <a href="/home" style="color: #007bff; text-decoration: none;">Retourner à l'accueil</a>
        </body>
    </html>
    """, 404

# ------------------------------
# SYSTÈME DE HINTS EN MÉMOIRE
# ------------------------------
HINTS_DATABASE = {
    1: {  # Challenge SQLi
        "hints": [
            {
                "text": "💡 Les identifiants sont vérifiés avec une requête SQL. Que se passe-t-il si vous entrez des caractères spéciaux dans le champ username ?",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Essayez d'utiliser le caractère guillemet simple (') dans le champ username pour 'casser' la requête SQL. Vous pouvez ajouter des conditions logiques comme OR.",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Utilisez un payload en SQL dans le champ username.",
                "penalty_percent": 50
            }
        ]
    },
    2: {  # Challenge XSS
        "hints": [
            {
                "text": "💡 Les commentaires ne sont pas filtrés. Que se passe-t-il si vous injectez du code HTML dans le champ commentaire ?",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Le filtre |safe désactive l'échappement HTML. Essayez d'insérer une balise <script> dans votre commentaire pour exécuter du JavaScript.",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Tapez exactement ceci dans le champ commentaire : <script>alert('XSS')</script>\n\nVous pouvez aussi essayer avec des attributs comme : <img src=x onerror=alert('XSS')>",
                "penalty_percent": 50
            }
        ]
    },
    3: {  # Challenge Bruteforce
        "hints": [
            {
                "text": "💡 Le code est composé de 4 chiffres (0000 à 9999). Tester manuellement prendrait trop de temps... Pensez à automatiser avec un script !",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Utilisez la bibliothèque requests de Python pour envoyer des requêtes POST automatiquement. Parcourez tous les codes de 0000 à 9999 avec une boucle for.",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Voici un squelette de script Python :\n\nimport requests\nfor code in range(10000):\n    code_str = str(code).zfill(4)\n    response = requests.post('http://localhost:5004', data={'code': code_str})\n    if 'FLAG' in response.text or 'déverrouillé' in response.text:\n        print(f'Code trouvé: {code_str}')\n        break",
                "penalty_percent": 50
            }
        ]
    },
    4: {  # Challenge Crypto
        "hints": [
            {
                "text": "💡 Les mots de passe sont hashés avec MD5 sans sel. Les rainbow tables peuvent être utilisées pour craquer ces hash rapidement.",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Utilisez des outils comme 'hashcat' ou des services en ligne pour rechercher les hash MD5. Vous pouvez aussi écrire un script Python pour automatiser la recherche.",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Par exemple, le hash '5f4dcc3b5aa765d61d8327deb882cf99' correspond au mot de passe 'password'. Essayez de craquer les autres hash de la même manière.",
                "penalty_percent": 50
            }
        ]
    },
    5: {  # Challenge OSINT
        "hints": [
            {
                "text": "💡 Certaines informations ne sont pas visibles à l’écran mais restent accessibles publiquement.",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Tous les onglets ne sont pas forcément visibles dans le menu principal.",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Examinez attentivement le code source de l'une des villes. Certains chemins ou liens peuvent y apparaître sans être affichés à l’écran",
                "penalty_percent": 50
            }
        ]
    },
    6: {  # Challenge Upload
        "hints": [
            {
                "text": "💡 Ce que tu vois côté interface n’est pas toujours représentatif de ce qui se passe côté serveur.",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Intéresse-toi à la manière dont les fichiers sont acceptés et enregistrés.",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Les fichiers uploadés sont accessibles via /uploads/. Réfléchis à ce qui pourrait se passer si un fichier particulier était exécuté au lieu d’être simplement affiché.",
                "penalty_percent": 50
            }
        ]
    },
    7: {  # Challenge Stégano
        "hints": [
            {
                "text": "💡 Les données sont cachées dans des pixels précis. La formule : le i-ème caractère se trouve au pixel (i×37 mod W, i×53 mod H). L'index 0 indique la longueur.",
                "penalty_percent": 15
            },
            {
                "text": "🎯 Chaque pixel cache un caractère dans son canal Rouge (R). char = chr(pixel[x, y][0]). Extrayez le message, mais ne croyez pas encore vos yeux…",
                "penalty_percent": 35
            },
            {
                "text": "🔑 Le message extrait est chiffré ROT13. python3 -c \"import codecs; print(codecs.decode('MESSAGE', 'rot13'))\"",
                "penalty_percent": 50
            }
        ]
    }
    
}
def get_hints_for_challenge(challenge_id):
    """Récupère les hints d'un challenge"""
    return HINTS_DATABASE.get(challenge_id, {"hints": []})

def get_revealed_hints(challenge_id):
    """Récupère les indices déjà révélés par l'utilisateur pour ce challenge"""
    if 'revealed_hints' not in session:
        session['revealed_hints'] = {}
    
    user_hints = session['revealed_hints']
    key = f"{current_user.id}_{challenge_id}"
    return user_hints.get(key, [])

def reveal_hint(challenge_id, hint_index):
    """Marque un indice comme révélé pour l'utilisateur"""
    if 'revealed_hints' not in session:
        session['revealed_hints'] = {}
    
    key = f"{current_user.id}_{challenge_id}"
    if key not in session['revealed_hints']:
        session['revealed_hints'][key] = []
    
    if hint_index not in session['revealed_hints'][key]:
        session['revealed_hints'][key].append(hint_index)
    
    session.modified = True

def calculate_hint_penalty(challenge_id):
    """Calcule la pénalité totale basée sur les indices révélés"""
    revealed = get_revealed_hints(challenge_id)
    hints_data = get_hints_for_challenge(challenge_id)
    
    total_penalty = 0
    for idx in revealed:
        if idx < len(hints_data["hints"]):
            total_penalty += hints_data["hints"][idx]["penalty_percent"]
    
    return total_penalty

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
# INJECTION GLOBALE
# ------------------------------
@app.context_processor
def inject_globals():
    """Injecte des variables globales dans tous les templates"""
    return {
        'now': datetime.now,
        'Challenge': Challenge,
        'Submission': Submission,
        'User': User
    }

# ------------------------------
# Routes
# ------------------------------

@app.route('/')
def root():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template("index.html")

@app.route('/mentionslegales')
def legale():
    return render_template("mentionlegale.html")

@app.route('/politiqueconfidentialite')
def confidentialite():
    return render_template("politiqueconfidentialite.html")
@app.route('/cgu')
def cgu():
    return render_template("cgu.html")

@app.route('/dashboard')
@login_required
def dashboard():
    """Page du tableau de bord (protégée)"""
    return render_template("dashboard.html", user=current_user)

@app.route('/scoreboard')
def scoreboard():
    """Page du classement général (Top 100)"""
    # Récupérer le classement général (Top 100)
    classement = Scoreboard.afficherClassement(limit=100)
    
    # Si l'utilisateur est connecté, trouver sa position
    user_rank = None
    user_score = None
    if current_user.is_authenticated:
        user_score = current_user.score
        # Compter combien d'utilisateurs ont plus de points
        user_rank = Scoreboard.query.filter(
            Scoreboard.points_total > user_score
        ).count() + 1
    
    return render_template(
        "scoreboard.html",
        classement=classement,
        user_rank=user_rank,
        user_score=user_score
    )

@app.route('/learn')
def learn():
    """Bibliothèque de cours - Page d'index"""
    return render_template("learn/index.html")

@app.route('/learn/sqli')
def learn_sqli():
    """Cours sur les injections SQL"""
    return render_template("learn/sqli.html")

@app.route('/learn/xss')
def learn_xss():
    """Cours sur le Cross-Site Scripting"""
    return render_template("learn/xss.html")

@app.route('/learn/bruteforce')
def learn_bruteforce():
    """Cours sur le Bruteforce"""
    return render_template("learn/bruteforce.html")

@app.route('/learn/crypto')
def learn_crypto():
    """Cours sur la Cryptographie"""
    return render_template("learn/crypto.html")

@app.route('/learn/osint')
def learn_osint():
    """Cours sur l'OSINT"""
    return render_template("learn/osint.html")

@app.route('/learn/upload')
def learn_upload():
    """Cours sur l'Upload"""
    return render_template("learn/upload.html")

@app.route('/challenges')
@login_required
def challenges_list():
    """Page listant tous les challenges disponibles"""
    challenges = Challenge.query.filter_by(actif=True).all()
    return render_template("challenges_list.html", challenges=challenges)

@app.route('/challenge/<int:challenge_id>')
@login_required
def challenge_view(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    if not challenge.actif:
        flash("Ce challenge n'est pas encore disponible.", "warning")
        return redirect(url_for('dashboard'))
    
    # Récupérer les hints et ceux déjà révélés
    hints_data = get_hints_for_challenge(challenge_id)
    revealed_indices = get_revealed_hints(challenge_id)
    current_penalty = calculate_hint_penalty(challenge_id)
    
    return render_template(
        "challenge.html", 
        challenge=challenge,
        hints=hints_data["hints"],
        revealed_hints=revealed_indices,
        current_penalty=current_penalty
    )

@app.route('/challenge/<int:challenge_id>/hint/<int:hint_index>', methods=['POST'])
@login_required
def reveal_hint_route(challenge_id, hint_index):
    """Révèle un indice pour l'utilisateur"""
    challenge = Challenge.query.get_or_404(challenge_id)
    hints_data = get_hints_for_challenge(challenge_id)
    
    # Vérifier que l'indice existe
    if hint_index >= len(hints_data["hints"]):
        return jsonify({"error": "Indice invalide"}), 400
    
    # Vérifier que l'indice n'a pas déjà été révélé
    revealed = get_revealed_hints(challenge_id)
    if hint_index in revealed:
        return jsonify({"error": "Indice déjà révélé"}), 400
    
    # Révéler l'indice
    reveal_hint(challenge_id, hint_index)
    
    hint = hints_data["hints"][hint_index]
    new_penalty = calculate_hint_penalty(challenge_id)
    
    return jsonify({
        "success": True,
        "hint_text": hint["text"],
        "penalty": hint["penalty_percent"],
        "total_penalty": new_penalty
    })

@app.route('/challenge/<int:challenge_id>/submit', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    flag_soumis = request.form.get('flag', '').strip()
    
    # Calculer la pénalité AVANT soumission
    penalty_percent = calculate_hint_penalty(challenge_id)
    
    submission = Submission(
        user_id=current_user.id,
        challenge_id=challenge_id,
        flag_soumis=flag_soumis
    )
    
    if submission.enregistrer():
        # Calculer les points avec pénalité
        base_points = challenge.points
        penalty_points = int(base_points * penalty_percent / 100)
        final_points = base_points - penalty_points
        
        # Récupérer ou créer le scoreboard
        sb = Scoreboard.query.filter_by(user_id=current_user.id).first()
        if not sb:
            sb = Scoreboard(user_id=current_user.id, points_total=0)
            db.session.add(sb)
            db.session.flush()
        
        # Vérifier si c'est la première validation de ce challenge
        previous_correct = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id,
            correct=True
        ).count()
        
        # Si c'est la première fois, ajuster avec la pénalité
        if previous_correct == 1:  # === 1 car on vient juste d'enregistrer
            # Retirer les points de base déjà ajoutés par Submission.enregistrer()
            sb.points_total = sb.points_total - base_points + final_points
            db.session.commit()
        
        # Message personnalisé selon la pénalité
        if penalty_percent > 0:
            flash(
                f"✅ Bravo ! Flag correct ! +{final_points} points "
                f"({base_points} - {penalty_points} de pénalité)",
                "success"
            )
        else:
            flash(f"✅ Bravo ! Flag correct ! +{final_points} points", "success")
        
        # Réinitialiser les hints pour ce challenge
        key = f"{current_user.id}_{challenge_id}"
        if 'revealed_hints' in session and key in session['revealed_hints']:
            del session['revealed_hints'][key]
            session.modified = True
    else:
        flash("❌ Flag incorrect. Réessayez !", "danger")
    
    return redirect(url_for('challenge_view', challenge_id=challenge_id))

# ------------------------------
# Point d'entrée du programme (mode local)
# ------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)