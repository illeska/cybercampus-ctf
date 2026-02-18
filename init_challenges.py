from app import app
from core import db
from core.models import Challenge, Flag

CHALLENGES_DATA = [
    {
        "id":1,
        "titre": "SQL Injection - Accès Restreint",
        "description": "Une zone d’authentification protège un espace sensible. Trouvez un moyen d’accéder au compte administrateur pour récupérer le flag.",
        "points": 25,
        "actif": True,
        "flag_str": "CTF{SQL_1nj3ct10n_m4st3r}"
    },
    {
        "id":2,
        "titre": "XSS Reflected - Livre d'or",
        "description": "Un livre d’or permet aux visiteurs de laisser un message. Interagissez avec cette fonctionnalité et trouvez comment récupérer le flag.",
        "points": 25,
        "actif": True,
        "flag_str": "CTF{XSS_r3fl3ct3d_pwn3d}"
    },
    {
        "id":3,
        "titre": "Bruteforce - Coffre-fort Digital",
        "description": "Un coffre-fort numérique protège une information confidentielle. Découvrez le bon code pour accéder au flag.",
        "points": 175,
        "actif": True,
        "flag_str": "CTF{Brut3F0rc3_M4st3r_7394}"
    },
    {
        "id":4,
        "titre": "Cryptographie - Données compromises",
        "description": "Plusieurs messages chiffrés ont été interceptés. Analysez les informations fournies et parvenez à retrouver le flag.",
        "points": 75,
        "actif": True,
        "flag_str": "CTF{r41nb0w_t4bl3s_pwn3d}"
    },
    {
        "id":5,
        "titre": "OSINT - Surface d'Exposition",
        "description": "Un site web public semble anodin, mais comme souvent, certaines informations accessibles à tous peuvent révéler davantage qu'il n’y paraît. Explorez intelligemment et retrouvez le flag.",
        "points": 50,
        "actif": True,
        "flag_str": "CTF{H3m_s3cr3t_c1ty_0s1nt}"
    },
    {
        "id":6,
        "titre": "Upload - Point d’Entrée",
        "description": "Un simple formulaire peut sembler anodin, mais certaines fonctionnalités cachent parfois plus qu’il n’y paraît. Analysez attentivement son fonctionnement et trouvez un moyen d’en tirer parti pour récupérer le flag.",
        "points": 125,
        "actif": True,
        "flag_str": "CTF{Upl04d_PHP_Sh3ll_M4st3r}"
    }
    
]

def sync_challenges():
    with app.app_context():
        try:
            for data in CHALLENGES_DATA:
                # On cherche si le challenge existe déjà par son id
                challenge = Challenge.query.filter_by(id=data["id"]).first()
                
                if challenge:
                    print(f"🔄 Mise à jour du challenge : {data['titre']}")
                    challenge.description = data["titre"]
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
                        id=data["id"],
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