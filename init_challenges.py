from app import app
from core import db
from core.models import Challenge, Flag

CHALLENGES_DATA = [
    {
        "titre": "SQL Injection - Login Bypass",
        "description": "Connectez-vous en tant qu'administrateur pour récupérer le flag. L'application utilise une requête SQL vulnérable.",
        "points": 25,
        "actif": True,
        "flag_str": "CTF{SQL_1nj3ct10n_m4st3r}"
    },
    {
        "titre": "XSS Reflected - Livre d'or",
        "description": "Exploitez une faille XSS dans le système de commentaires pour obtenir le flag.",
        "points": 50,
        "actif": True,
        "flag_str": "CTF{XSS_r3fl3ct3d_pwn3d}"
    },
    {
        "titre": "Bruteforce - Coffre-fort Digital",
        "description": "Trouvez le code secret à 4 chiffres pour déverrouiller le coffre-fort.",
        "points": 100,
        "actif": True,
        "flag_str": "CTF{Brut3F0rc3_M4st3r_7394}"
    },
    {
        "titre": "Cryptographie - Rainbow Tables & Hash Cracking",
        "description": "Déchiffrez le message pour obtenir le flag.",
        "points": 75,
        "actif": True,
        "flag_str": "CTF{H4sh_Cr4ck1ng_1s_Fun}"
    }
]

def sync_challenges():
    with app.app_context():
        try:
            for data in CHALLENGES_DATA:
                # On cherche si le challenge existe déjà par son titre
                challenge = Challenge.query.filter_by(titre=data["titre"]).first()
                
                if challenge:
                    print(f"🔄 Mise à jour du challenge : {data['titre']}")
                    challenge.description = data["description"]
                    challenge.points = data["points"]
                    challenge.actif = data["actif"]
                    
                    # Gestion du Flag associé
                    flag_obj = Flag.query.filter_by(challenge_id=challenge.id).first()
                    if flag_obj:
                        flag_obj.setFlag(data["flag_str"])
                else:
                    print(f"✨ Création du nouveau challenge : {data['titre']}")
                    new_challenge = Challenge(
                        titre=data["titre"],
                        description=data["description"],
                        points=data["points"],
                        actif=data["actif"]
                    )
                    db.session.add(new_challenge)
                    db.session.flush()
                    
                    new_flag = Flag(challenge_id=new_challenge.id)
                    new_flag.setFlag(data["flag_str"])
                    db.session.add(new_flag)

            db.session.commit()
            print("✅ Synchronisation terminée !")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la synchronisation : {e}")

if __name__ == "__main__":
    sync_challenges()