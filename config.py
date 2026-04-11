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

    MAIL_SERVER = 'ssl0.ovh.net'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')

    # Configuration de reCAPTCHA
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')

    # Configuration de Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")