#!/usr/bin/env python3
"""
CyberCampus CTF - Script de génération de données fictives
Génère 50 utilisateurs avec des soumissions variées et réalistes
Usage: docker exec cybercampus_web python seed_users.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, '/app')

from app import app
from core import db
from core.models import User, Challenge, Flag, Submission, Scoreboard, EmailVerification

# ------------------------------
# DONNÉES FICTIVES
# ------------------------------

PSEUDOS = [
    "shadow_hacker", "n3o_ctf", "zeroc00l", "ph4ntom", "r3dteam",
    "xpl0it3r", "bytebandit", "darkn3t", "cyph3r", "nullbyte",
    "h4x0r_fr", "l33tcode", "r00tkit", "shellstorm", "packetloss",
    "w1reShark", "bl4ckh4t", "pentest_pro", "vuln_hunter", "sec_ninja",
    "m4lware_x", "0x41424344", "cr4ckm3", "rev3rse", "fuzzer99",
    "sqlm4ster", "xss_queen", "bruteking", "cryptowolf", "osint_eye",
    "uploadkid", "steg4no", "h3xdump", "b1n4ry", "assembly_god",
    "netflow_x", "arp_spoof", "mitm_pro", "dnsh4ck", "portscanner",
    "p4yload", "shellcode", "exploit_dev", "ret2libc", "rop_chain",
    "heap_spray", "uaf_hunter", "format_str", "race_cond", "pwn_master"
]

DOMAINES = ["gmail.com", "protonmail.com", "outlook.com", "yahoo.fr", "tutanota.com"]

# Challenges avec leurs points et flags
CHALLENGES = {
    1: {"titre": "SQL Injection", "points": 25, "flag": "CTF{SQL_1nj3ct10n_m4st3r}"},
    2: {"titre": "XSS Reflected", "points": 25, "flag": "CTF{XSS_r3fl3ct3d_pwn3d}"},
    3: {"titre": "Bruteforce", "points": 175, "flag": "CTF{Brut3F0rc3_M4st3r_7394}"},
    4: {"titre": "Cryptographie", "points": 75, "flag": "CTF{r41nb0w_t4bl3s_pwn3d}"},
    5: {"titre": "OSINT", "points": 50, "flag": "CTF{H3m_s3cr3t_c1ty_0s1nt}"},
    6: {"titre": "Upload", "points": 125, "flag": "CTF{Upl04d_PHP_Sh3ll_M4st3r}"},
    7: {"titre": "Stéganographie", "points": 150, "flag": "CTF{C4rt0_st3g4_ROT13_pwn3d}"},
}

FLAGS_INCORRECTS = [
    "CTF{wrong_flag}", "CTF{test}", "CTF{flag}", "CTF{essai}",
    "CTF{hacked}", "CTF{hello}", "flag{wrong}", "CTF{nope}",
    "CTF{tryagain}", "CTF{idk}", "CTF{maybe}", "CTF{lol}",
]

def random_date(start_days_ago=90, end_days_ago=1):
    """Génère une date aléatoire dans les derniers mois"""
    start = datetime.utcnow() - timedelta(days=start_days_ago)
    end = datetime.utcnow() - timedelta(days=end_days_ago)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def get_hint_penalty(nb_hints):
    """Calcule la pénalité selon le nombre d'indices utilisés"""
    penalties = {0: 0, 1: 10, 2: 30, 3: 80}
    return penalties.get(nb_hints, 80)

def seed():
    with app.app_context():
        print("=" * 60)
        print("   GÉNÉRATION DE 50 UTILISATEURS FICTIFS")
        print("=" * 60)

        # ------------------------------
        # PROFILS DE JOUEURS
        # ------------------------------

        # 2 joueurs ont fait les 7 challenges (elite)
        elite = [0, 1]

        # 3 joueurs ont fait 6 challenges
        presque_elite = [2, 3, 4]

        # 10 joueurs ont fait 4-5 challenges (bons)
        bons = list(range(5, 15))

        # 15 joueurs ont fait 2-3 challenges (moyens)
        moyens = list(range(15, 30))

        # 20 joueurs ont fait 1-2 challenges (débutants)
        debutants = list(range(30, 50))

        stats_globales = {"users": 0, "submissions": 0, "flags_valides": 0}

        for i, pseudo in enumerate(PSEUDOS):
            email = f"{pseudo}@{random.choice(DOMAINES)}"
            date_inscription = random_date(90, 30)

            # Créer l'utilisateur
            user = User(
                pseudo=pseudo,
                email=email,
                email_verified=True,
                role="user",
                created_at=date_inscription
            )
            user.set_password(f"Pass_{pseudo}_2026!")
            db.session.add(user)
            db.session.flush()

            stats_globales["users"] += 1

            # Déterminer les challenges à faire selon le profil
            if i in elite:
                challenges_a_faire = list(CHALLENGES.keys())  # Tous les 7
                nb_hints_pool = [0, 1, 2]  # Peu d'indices (bons joueurs)
                taux_reussite = 0.95

            elif i in presque_elite:
                tous = list(CHALLENGES.keys())
                challenges_a_faire = random.sample(tous, 6)
                nb_hints_pool = [0, 1, 2]
                taux_reussite = 0.90

            elif i in bons:
                nb_challenges = random.randint(4, 5)
                challenges_a_faire = random.sample(list(CHALLENGES.keys()), nb_challenges)
                nb_hints_pool = [0, 0, 1, 2, 3]
                taux_reussite = 0.80

            elif i in moyens:
                nb_challenges = random.randint(2, 3)
                challenges_a_faire = random.sample(list(CHALLENGES.keys()), nb_challenges)
                nb_hints_pool = [0, 1, 2, 3, 3]
                taux_reussite = 0.65

            else:  # débutants
                nb_challenges = random.randint(1, 2)
                challenges_a_faire = random.sample(list(CHALLENGES.keys()), nb_challenges)
                nb_hints_pool = [1, 2, 3, 3]
                taux_reussite = 0.45

            points_total = 0

            for challenge_id in challenges_a_faire:
                challenge_info = CHALLENGES[challenge_id]
                base_points = challenge_info["points"]
                flag_correct = challenge_info["flag"]

                # Nombre d'indices utilisés
                nb_hints = random.choice(nb_hints_pool)
                penalty_percent = get_hint_penalty(nb_hints)

                # Tentatives incorrectes avant de réussir (ou pas)
                a_reussi = random.random() < taux_reussite
                nb_tentatives_incorrectes = random.randint(0, 5) if a_reussi else random.randint(1, 10)

                date_base = random_date(89, 2)

                # Soumettre les mauvais flags
                for t in range(nb_tentatives_incorrectes):
                    mauvais_flag = random.choice(FLAGS_INCORRECTS)
                    date_tentative = date_base + timedelta(minutes=t * random.randint(2, 30))

                    sub_bad = Submission(
                        user_id=user.id,
                        challenge_id=challenge_id,
                        flag_soumis=mauvais_flag,
                        correct=False,
                        timestamp=date_tentative
                    )
                    db.session.add(sub_bad)
                    stats_globales["submissions"] += 1

                # Soumettre le bon flag si réussi
                if a_reussi:
                    date_succes = date_base + timedelta(
                        minutes=nb_tentatives_incorrectes * random.randint(5, 45) + random.randint(10, 120)
                    )

                    sub_good = Submission(
                        user_id=user.id,
                        challenge_id=challenge_id,
                        flag_soumis=flag_correct,
                        correct=True,
                        timestamp=date_succes
                    )
                    db.session.add(sub_good)
                    stats_globales["submissions"] += 1
                    stats_globales["flags_valides"] += 1

                    # Calculer les points avec pénalité
                    penalty_points = int(base_points * penalty_percent / 100)
                    final_points = base_points - penalty_points
                    points_total += final_points

            # Créer ou mettre à jour le scoreboard
            if points_total > 0:
                sb = Scoreboard(
                    user_id=user.id,
                    points_total=points_total
                )
                db.session.add(sb)

            profil = (
                "ELITE" if i in elite else
                "PRESQUE ELITE" if i in presque_elite else
                "BON" if i in bons else
                "MOYEN" if i in moyens else
                "DÉBUTANT"
            )

            print(f"✅ [{profil}] {pseudo} — {len(challenges_a_faire)} challenges — {points_total} pts")

        # Commit final
        db.session.commit()

        print()
        print("=" * 60)
        print("✅ GÉNÉRATION TERMINÉE")
        print("=" * 60)
        print(f"👥 Utilisateurs créés  : {stats_globales['users']}")
        print(f"📝 Soumissions totales : {stats_globales['submissions']}")
        print(f"🏆 Flags validés       : {stats_globales['flags_valides']}")
        print("=" * 60)

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)