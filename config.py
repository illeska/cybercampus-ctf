# ------------------------------
# CyberCampus CTF - Configuration principale
# ------------------------------

import os
from dotenv import load_dotenv

# Chargement du fichier .env
load_dotenv()

class Config:
    """
    Classe principale de configuration Flask.
    Elle centralise tous les paramètres du projet.
    """
    # Clé secrète pour sécuriser les sessions et formulaires
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key_change_me")

    # URL de connexion à la base de données
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///cybercampus.db")

    # Désactivation du suivi des modifications (optimisation)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mode debug : activé par défaut pour le développement
    DEBUG = True
