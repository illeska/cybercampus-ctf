#!/usr/bin/env python3
"""
Script pour supprimer un ou plusieurs challenges de CyberCampus CTF

Fonctionnalités :
- Supprimer un challenge par ID
- Supprimer un challenge par titre
- Supprimer TOUS les challenges (--wipe-all)
- Supprimer un conteneur Docker
"""

import sys
import subprocess
import argparse

from app import app
from core import db
from core.models import Challenge, Flag, Submission


# =========================
# Docker
# =========================

def stop_and_remove_container(container_name):
    """Arrête et supprime un conteneur Docker"""
    try:
        print(f"\n🐳 Gestion du conteneur Docker : {container_name}")

        subprocess.run(['docker', 'stop', container_name], capture_output=True)
        subprocess.run(['docker', 'rm', container_name], capture_output=True)

        print("   ✅ Conteneur traité")
        return True

    except FileNotFoundError:
        print("❌ Docker non installé ou absent du PATH")
        return False

    except Exception as e:
        print(f"❌ Erreur Docker : {e}")
        return False


# =========================
# Suppression DB
# =========================

def delete_challenge_from_db(challenge_id=None, titre=None):
    """Supprime un challenge spécifique"""

    with app.app_context():

        if challenge_id:
            challenge = Challenge.query.get(challenge_id)
        elif titre:
            challenge = Challenge.query.filter_by(titre=titre).first()
        else:
            print("❌ ID ou titre requis")
            return False

        if not challenge:
            print("❌ Challenge non trouvé")
            return False

        flag_count = Flag.query.filter_by(challenge_id=challenge.id).count()
        submissions_count = Submission.query.filter_by(challenge_id=challenge.id).count()

        print("\n" + "=" * 60)
        print("   CHALLENGE À SUPPRIMER")
        print("=" * 60)
        print(f"ID          : {challenge.id}")
        print(f"Titre       : {challenge.titre}")
        print(f"Points      : {challenge.points}")
        print(f"Flags       : {flag_count}")
        print(f"Submissions : {submissions_count}")
        print("=" * 60)

        confirm = input("\n👉 Confirmer la suppression ? (o/n) : ").strip().lower()
        if confirm != "o":
            print("❌ Suppression annulée")
            return False

        try:
            db.session.delete(challenge)
            db.session.commit()

            print("✅ Challenge supprimé avec succès")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur DB : {e}")
            return False


def wipe_all_challenges():
    """Supprime TOUS les challenges"""

    with app.app_context():

        challenges = Challenge.query.all()

        if not challenges:
            print("⚠️ Aucun challenge à supprimer.")
            return False

        total_flags = Flag.query.count()
        total_submissions = Submission.query.count()

        print("\n" + "=" * 60)
        print("🚨 SUPPRESSION TOTALE")
        print("=" * 60)
        print(f"Challenges  : {len(challenges)}")
        print(f"Flags       : {total_flags}")
        print(f"Submissions : {total_submissions}")
        print("🚨 CETTE ACTION EST IRRÉVERSIBLE 🚨")
        print("=" * 60)

        confirm = input("\nTapez SUPPRIMER pour confirmer : ").strip()

        if confirm != "SUPPRIMER":
            print("❌ Suppression annulée")
            return False

        try:
            for challenge in challenges:
                db.session.delete(challenge)

            db.session.commit()

            print("✅ Tous les challenges ont été supprimés")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur : {e}")
            return False


# =========================
# Main
# =========================

def main():

    parser = argparse.ArgumentParser(description="Gestion des suppressions CyberCampus CTF")

    parser.add_argument('--id', type=int, help='ID du challenge')
    parser.add_argument('--titre', type=str, help='Titre du challenge')
    parser.add_argument('--container', type=str, help='Nom du conteneur Docker')
    parser.add_argument('--wipe-all', action='store_true', help='Supprimer tous les challenges')
    parser.add_argument('--no-docker', action='store_true', help='Ignorer Docker')

    args = parser.parse_args()

    # 🔴 Suppression totale
    if args.wipe_all:
        wipe_all_challenges()
        return

    # 🔹 Suppression challenge
    if args.id or args.titre:
        success = delete_challenge_from_db(
            challenge_id=args.id,
            titre=args.titre
        )

        if success and args.container and not args.no_docker:
            stop_and_remove_container(args.container)

    # 🔹 Suppression container seul
    elif args.container:
        stop_and_remove_container(args.container)

    else:
        print("❌ Aucun argument fourni.")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Opération annulée.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        sys.exit(1)