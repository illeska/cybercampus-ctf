#!/usr/bin/env python3
"""
Script pour supprimer un challenge de CyberCampus CTF
- Supprime de la base de données (cascade : flag, submissions)
- Arrête et supprime le conteneur Docker
- Optionnel : supprime les fichiers du challenge

Usage:
    python delete_challenge.py
    python delete_challenge.py --id 4
    python delete_challenge.py --titre "Rainbow Tables"
    python delete_challenge.py --container cybercampus_crypto
"""

import sys
import subprocess
from app import app
from core import db
from core.models import Challenge, Flag, Submission

def stop_and_remove_container(container_name):
    """Arrête et supprime un conteneur Docker"""
    try:
        print(f"\n🐳 Arrêt du conteneur Docker : {container_name}")
        
        # Arrêter le conteneur
        result = subprocess.run(
            ['docker', 'stop', container_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   ✅ Conteneur arrêté : {container_name}")
        else:
            print(f"   ⚠️  Conteneur introuvable ou déjà arrêté : {container_name}")
        
        # Supprimer le conteneur
        result = subprocess.run(
            ['docker', 'rm', container_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   ✅ Conteneur supprimé : {container_name}")
        else:
            print(f"   ⚠️  Conteneur déjà supprimé ou inexistant")
        
        return True
    
    except FileNotFoundError:
        print("   ❌ Docker n'est pas installé ou pas dans le PATH")
        return False
    except Exception as e:
        print(f"   ❌ Erreur Docker : {e}")
        return False

def delete_challenge_from_db(challenge_id=None, titre=None):
    """Supprime un challenge de la base de données"""
    with app.app_context():
        # Rechercher le challenge
        if challenge_id:
            challenge = Challenge.query.get(challenge_id)
        elif titre:
            challenge = Challenge.query.filter_by(titre=titre).first()
        else:
            print("❌ Vous devez spécifier un ID ou un titre")
            return False
        
        if not challenge:
            print(f"❌ Challenge non trouvé")
            return False
        
        # Afficher les infos du challenge
        print("\n" + "=" * 60)
        print("   CHALLENGE À SUPPRIMER")
        print("=" * 60)
        print(f"   ID          : {challenge.id}")
        print(f"   Titre       : {challenge.titre}")
        print(f"   Points      : {challenge.points}")
        print(f"   Actif       : {challenge.actif}")
        print(f"   Description : {challenge.description[:80]}...")
        print("=" * 60)
        
        # Compter les éléments liés
        flag_count = Flag.query.filter_by(challenge_id=challenge.id).count()
        submissions_count = Submission.query.filter_by(challenge_id=challenge.id).count()
        
        print(f"\n⚠️  ATTENTION : Cette action va également supprimer :")
        print(f"   • {flag_count} flag(s)")
        print(f"   • {submissions_count} soumission(s) d'utilisateurs")
        
        # Confirmation
        choice = input(f"\n👉 Confirmer la suppression ? (o/n) : ").strip().lower()
        
        if choice != 'o':
            print("\n❌ Suppression annulée.")
            return False
        
        # Suppression en cascade (Flask-SQLAlchemy gère le cascade)
        try:
            db.session.delete(challenge)
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ SUPPRESSION RÉUSSIE")
            print("=" * 60)
            print(f"   Challenge '{challenge.titre}' supprimé de la base de données")
            print(f"   {flag_count} flag(s) supprimé(s)")
            print(f"   {submissions_count} soumission(s) supprimée(s)")
            print("=" * 60)
            
            return True
        
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de la suppression : {e}")
            return False

def list_all_challenges():
    """Liste tous les challenges disponibles"""
    with app.app_context():
        challenges = Challenge.query.all()
        
        if not challenges:
            print("\n⚠️  Aucun challenge dans la base de données.")
            return
        
        print("\n" + "=" * 80)
        print(f"   LISTE DES CHALLENGES ({len(challenges)} total)")
        print("=" * 80)
        print(f"{'ID':<5} {'Titre':<40} {'Points':<8} {'Actif':<8} {'Soumissions'}")
        print("-" * 80)
        
        for c in challenges:
            submissions = Submission.query.filter_by(challenge_id=c.id).count()
            actif = "✅ Oui" if c.actif else "❌ Non"
            print(f"{c.id:<5} {c.titre[:38]:<40} {c.points:<8} {actif:<8} {submissions}")
        
        print("=" * 80)

def list_all_containers():
    """Liste tous les conteneurs Docker en cours d'exécution"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Image}}\t{{.Status}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Erreur lors de la récupération des conteneurs Docker")
            return
        
        containers = result.stdout.strip().split('\n')
        
        if not containers or containers == ['']:
            print("\n⚠️  Aucun conteneur Docker en cours d'exécution.")
            return
        
        print("\n" + "=" * 80)
        print(f"   LISTE DES CONTENEURS DOCKER EN COURS D'EXÉCUTION ({len(containers)} total)")
        print("=" * 80)
        print(f"{'Nom du Conteneur':<30} {'Image':<30} {'Statut'}")
        print("-" * 80)
        
        for line in containers:
            name, image, status = line.split('\t')
            print(f"{name:<30} {image:<30} {status}")
        
        print("=" * 80)
    
    except FileNotFoundError:
        print("❌ Docker n'est pas installé ou pas dans le PATH")
    except Exception as e:
        print(f"❌ Erreur Docker : {e}")


def interactive_mode_challenge():
    """Mode interactif pour choisir le challenge à supprimer"""
    print("\n" + "=" * 60)
    print("   SUPPRESSION DE CHALLENGE - MODE INTERACTIF")
    print("=" * 60)
    
    # Lister les challenges
    list_all_challenges()
    
    
    print("\nOptions :")
    print("  1. Supprimer par ID")
    print("  2. Supprimer par titre")
    print("  3. Annuler")
    
    choice = input("\n👉 Votre choix (1-3) : ").strip()
    
    if choice == '1':
        try:
            challenge_id = int(input("📝 ID du challenge à supprimer : ").strip())
            return delete_challenge_from_db(challenge_id=challenge_id)
        except ValueError:
            print("❌ ID invalide")
            return False
    
    elif choice == '2':
        titre = input("📝 Titre du challenge à supprimer : ").strip()
        return delete_challenge_from_db(titre=titre)
    
    else:
        print("❌ Suppression annulée")
        return False


def interactive_container_delete():
    """Mode interactif pour choisir un conteneur Docker à supprimer"""
    containers = list_all_containers()

    if not containers:
        return False

    try:
        choice = input("\n👉 Numéro du conteneur à supprimer (0 pour annuler) : ").strip()

        if choice == '0':
            print("❌ Suppression annulée")
            return False

        index = int(choice) - 1
        if index < 0 or index >= len(containers):
            print("❌ Choix invalide")
            return False

        container_name = containers[index]["name"]

        confirm = input(
            f"\n⚠️ Confirmer la suppression du conteneur '{container_name}' ? (o/n) : "
        ).strip().lower()

        if confirm != 'o':
            print("❌ Suppression annulée")
            return False

        return stop_and_remove_container(container_name)

    except ValueError:
        print("❌ Entrée invalide")
        return False

def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Supprimer un challenge CyberCampus CTF (DB + Docker)'
    )
    parser.add_argument('--id', type=int, help='ID du challenge à supprimer')
    parser.add_argument('--titre', type=str, help='Titre du challenge à supprimer')
    parser.add_argument('--container', type=str, help='Nom du conteneur Docker à supprimer')
    parser.add_argument('--list', action='store_true', help='Lister tous les challenges')
    parser.add_argument('--no-docker', action='store_true', help='Ne pas supprimer le conteneur Docker')

    args = parser.parse_args()

    # Mode liste uniquement
    if args.list:
        list_all_challenges()
        return

    # Mode interactif si aucun argument
    if not args.id and not args.titre and not args.container:
        print("\n" + "=" * 60)
        print("   MODE INTERACTIF")
        print("=" * 60)
        print("Options :")
        print("  1. Supprimer un challenge")
        print("  2. Supprimer un conteneur Docker")
        print("  3. Annuler")

        choice = input("\n👉 Votre choix (1-3) : ").strip()

        if choice == '1':
            success = interactive_mode_challenge()

            if success and not args.no_docker:
                container_name = input(
                    "\n🐳 Nom du conteneur Docker à supprimer (vide pour ignorer) : "
                ).strip()
                if container_name:
                    stop_and_remove_container(container_name)

        elif choice == '2':
            interactive_container_delete()

        else:
            print("❌ Opération annulée")

        return

    # Mode suppression challenge via arguments
    if args.id or args.titre:
        success = delete_challenge_from_db(
            challenge_id=args.id,
            titre=args.titre
        )

        if success and args.container and not args.no_docker:
            stop_and_remove_container(args.container)

    # Mode suppression container uniquement
    elif args.container:
        stop_and_remove_container(args.container)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)