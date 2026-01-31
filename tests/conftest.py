# tests/conftest.py
"""
Configuration pytest pour les tests unitaires
Gestion de la base de données temporaire et des fixtures
"""

import pytest
import tempfile
import os
from app import app as flask_app
from core import db
from core.models import User, Challenge, Flag, Submission, Scoreboard


@pytest.fixture(scope='function')
def app():
    """
    Fixture pour l'application Flask avec base de données temporaire
    Scope 'function' = nouvelle BDD pour chaque test (isolation complète)
    """
    # Créer un fichier de base de données temporaire
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Configuration de test
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,  # Désactiver CSRF pour les tests
        'SECRET_KEY': 'test-secret-key',
        'SERVER_NAME': 'localhost.localdomain'  # Pour url_for dans les tests
    })
    
    # Créer les tables
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        
        # Nettoyage après le test
        db.session.remove()
        db.drop_all()
    
    # Fermer et supprimer le fichier temporaire
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """Client de test Flask"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Runner CLI de test"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def init_database(app):
    """
    Initialise la base de données avec des données de test
    """
    with app.app_context():
        # Créer des utilisateurs de test
        user1 = User(pseudo="testuser1", email="test1@example.com")
        user1.set_password("password123")
        
        user2 = User(pseudo="testuser2", email="test2@example.com")
        user2.set_password("password456")
        
        admin_user = User(pseudo="admin", email="admin@example.com", role="admin")
        admin_user.set_password("adminpass")
        
        db.session.add_all([user1, user2, admin_user])
        db.session.flush()
        
        # Créer des challenges de test
        challenge1 = Challenge(
            titre="Test SQL Injection",
            description="Challenge de test pour SQLi",
            points=100,
            actif=True
        )
        
        challenge2 = Challenge(
            titre="Test XSS",
            description="Challenge de test pour XSS",
            points=150,
            actif=True
        )
        
        challenge3 = Challenge(
            titre="Challenge Inactif",
            description="Challenge désactivé",
            points=200,
            actif=False
        )
        
        db.session.add_all([challenge1, challenge2, challenge3])
        db.session.flush()
        
        # Créer des flags pour les challenges
        flag1 = Flag(challenge_id=challenge1.id)
        flag1.setFlag("CTF{test_flag_1}")
        
        flag2 = Flag(challenge_id=challenge2.id)
        flag2.setFlag("CTF{test_flag_2}")
        
        flag3 = Flag(challenge_id=challenge3.id)
        flag3.setFlag("CTF{test_flag_3}")
        
        db.session.add_all([flag1, flag2, flag3])
        
        # Créer des scoreboards
        scoreboard1 = Scoreboard(user_id=user1.id, points_total=0)
        scoreboard2 = Scoreboard(user_id=user2.id, points_total=0)
        
        db.session.add_all([scoreboard1, scoreboard2])
        
        db.session.commit()
        
        return {
            'user1': user1,
            'user2': user2,
            'admin': admin_user,
            'challenge1': challenge1,
            'challenge2': challenge2,
            'challenge3': challenge3,
            'flag1': flag1,
            'flag2': flag2,
            'flag3': flag3
        }


@pytest.fixture
def authenticated_client(client, init_database):
    """Client authentifié en tant qu'utilisateur normal"""
    client.post('/login', data={
        'email': 'test1@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client, init_database):
    """Client authentifié en tant qu'admin"""
    client.post('/login', data={
        'email': 'admin@example.com',
        'password': 'adminpass'
    }, follow_redirects=True)
    return client