from app import app
from core import db
from core.models import Challenge, Flag

# Liste de configuration de vos challenges
# C'est ici que tu ajoutes ou modifies tes challenges
CHALLENGES_DATA = [
    {
        "titre": "SQL Injection - Login Bypass",
        "description": "Connectez-vous en tant qu'administrateur pour récupérer le flag. L'application utilise une requête SQL vulnérable.",
        "points": 150,
        "actif": True,
        "flag_str": "CTF{SQL_1nj3ct10n_m4st3r}"
    },
    {
        "titre": "XSS Reflected - Livre d'or",
        "description": "Exploitez une faille XSS dans le système de commentaires pour obtenir le flag.",
        "points": 120,
        "actif": True,
        "flag_str": "CTF{XSS_r3fl3ct3d_pwn3d}"
    }
]

with app.app_context():
    print("🔄 Synchronisation des challenges (Conservation des données utilisateurs)...")
    
    try:
        for data in CHALLENGES_DATA:
            # 1. Vérifier si le challenge existe déjà par son titre
            challenge = Challenge.query.filter_by(titre=data["titre"]).first()

            if challenge:
                print(f"🔹 Mise à jour du challenge existant : {data['titre']}")
                # On met à jour les champs (sauf l'ID, pour ne pas casser les submissions)
                challenge.description = data["description"]
                challenge.points = data["points"]
                challenge.actif = data["actif"]
                
                # Gestion du Flag associé
                flag_obj = Flag.query.filter_by(challenge_id=challenge.id).first()
                if flag_obj:
                    flag_obj.setFlag(data["flag_str"]) # Met à jour le hash
                else:
                    # Cas de secours si le challenge existe mais a perdu son flag
                    new_flag = Flag(challenge_id=challenge.id)
                    new_flag.setFlag(data["flag_str"])
                    db.session.add(new_flag)

            else:
                print(f"✨ Création du nouveau challenge : {data['titre']}")
                # Création du challenge
                new_challenge = Challenge(
                    titre=data["titre"],
                    description=data["description"],
                    points=data["points"],
                    actif=data["actif"]
                )
                db.session.add(new_challenge)
                db.session.flush() # Important pour récupérer l'ID généré
                
                # Création du flag
                new_flag = Flag(challenge_id=new_challenge.id)
                new_flag.setFlag(data["flag_str"])
                db.session.add(new_flag)

        db.session.commit()
        print("✅ Synchronisation terminée ! Les progressions utilisateurs sont conservées.")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de la synchronisation : {e}")