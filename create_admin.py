#!/usr/bin/env python3
"""
Script pour promouvoir un utilisateur existant en admin
Usage: 
  python create_admin.py
  python create_admin.py <email_ou_pseudo>
"""

import sys
from app import app
from core import db
from core.models import User

def promote_to_admin(identifier=None):
    with app.app_context():
        print("=" * 60)
        print("   PROMOUVOIR UN UTILISATEUR EN ADMINISTRATEUR")
        print("=" * 60)
        print()
        
        # Si aucun identifiant n'est fourni, demander
        if not identifier:
            identifier = input("📧 Email ou Pseudo de l'utilisateur : ").strip()
        
        # Chercher l'utilisateur
        user = User.query.filter(
            (User.email == identifier) | (User.pseudo == identifier)
        ).first()
        
        if not user:
            print(f"\n❌ ERREUR : Aucun utilisateur trouvé avec '{identifier}'")
            print("\n💡 Assurez-vous que l'utilisateur existe déjà dans la base.")
            print("   Créez d'abord un compte via l'interface web.")
            return False
        
        # Afficher les infos de l'utilisateur
        print(f"\n👤 UTILISATEUR TROUVÉ")
        print("-" * 60)
        print(f"   ID     : {user.id}")
        print(f"   Pseudo : {user.pseudo}")
        print(f"   Email  : {user.email}")
        print(f"   Rôle   : {user.role}")
        print(f"   Score  : {user.score} points")
        print(f"   Inscrit: {user.created_at.strftime('%d/%m/%Y')}")
        print("-" * 60)
        
        # Vérifier si déjà admin
        if user.role == "admin":
            print("\n✅ Cet utilisateur est déjà administrateur.")
            return True
        
        # Confirmation
        print(f"\n⚠️  Vous êtes sur le point de promouvoir '{user.pseudo}' en admin.")
        print("   Cette action lui donnera accès à toutes les fonctionnalités admin.")
        
        choice = input("\n👉 Confirmer la promotion ? (o/n) : ").strip().lower()
        
        if choice != 'o':
            print("\n❌ Opération annulée.")
            return False
        
        # Promouvoir en admin
        user.role = "admin"
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("✅ PROMOTION RÉUSSIE")
        print("=" * 60)
        print(f"   {user.pseudo} est maintenant administrateur !")
        print(f"   Il peut accéder au panel admin via /admin")
        print("=" * 60)
        return True

def list_all_users():
    """Liste tous les utilisateurs (pour aide)"""
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("\n⚠️  Aucun utilisateur dans la base de données.")
            return
        
        print("\n" + "=" * 60)
        print(f"   LISTE DES UTILISATEURS ({len(users)} total)")
        print("=" * 60)
        
        for user in users:
            role_emoji = "👑" if user.role == "admin" else "👤"
            print(f"{role_emoji} {user.pseudo:<20} | {user.email:<30} | {user.role}")
        
        print("=" * 60)

if __name__ == "__main__":
    try:
        # Si argument fourni en ligne de commande
        if len(sys.argv) > 1:
            if sys.argv[1] == "--list":
                list_all_users()
            else:
                promote_to_admin(sys.argv[1])
        else:
            promote_to_admin()
    
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()