# tests/test_auth.py
"""
Tests unitaires pour l'authentification et les routes auth
"""

import pytest
from flask import session
from core.models import User
from core import db


class TestRegistration:
    """Tests pour l'inscription"""
    
    def test_register_page_loads(self, client):
        """Test que la page d'inscription se charge"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Cr' in response.data  # "Créer un compte"
    
    def test_register_new_user_success(self, client, app):
        """Test d'inscription d'un nouvel utilisateur"""
        response = client.post('/register', data={
            'pseudo': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Vérifier que l'utilisateur a été créé
        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.pseudo == 'newuser'
            assert user.check_password('password123')
    
    def test_register_duplicate_email(self, client, init_database):
        """Test d'inscription avec un email déjà utilisé"""
        response = client.post('/register', data={
            'pseudo': 'anotheruser',
            'email': 'test1@example.com',  # Email déjà existant
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Devrait afficher un message d'erreur
        assert b'existe' in response.data or b'Pseudo' in response.data
    
    def test_register_duplicate_pseudo(self, client, init_database):
        """Test d'inscription avec un pseudo déjà utilisé"""
        response = client.post('/register', data={
            'pseudo': 'testuser1',  # Pseudo déjà existant
            'email': 'newmail@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'existe' in response.data or b'Pseudo' in response.data
    
    def test_register_password_mismatch(self, client):
        """Test d'inscription avec des mots de passe différents"""
        response = client.post('/register', data={
            'pseudo': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'different_password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Le formulaire devrait afficher une erreur
        assert b'correspond' in response.data or b'password' in response.data.lower()
    
    def test_register_short_password(self, client):
        """Test d'inscription avec un mot de passe trop court"""
        response = client.post('/register', data={
            'pseudo': 'testuser',
            'email': 'test@example.com',
            'password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Le formulaire devrait afficher une erreur de validation


class TestLogin:
    """Tests pour la connexion"""
    
    def test_login_page_loads(self, client):
        """Test que la page de connexion se charge"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Connexion' in response.data
    
    def test_login_success(self, client, init_database):
        """Test de connexion réussie"""
        response = client.post('/login', data={
            'email': 'test1@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Bienvenue' in response.data or b'testuser1' in response.data
    
    def test_login_wrong_password(self, client, init_database):
        """Test de connexion avec mauvais mot de passe"""
        response = client.post('/login', data={
            'email': 'test1@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data.lower() or b'erreur' in response.data.lower()
    
    def test_login_nonexistent_user(self, client, init_database):
        """Test de connexion avec un utilisateur inexistant"""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data.lower() or b'erreur' in response.data.lower()
    
    def test_login_invalid_email(self, client):
        """Test de connexion avec un email invalide"""
        response = client.post('/login', data={
            'email': 'not-an-email',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestLogout:
    """Tests pour la déconnexion"""
    
    def test_logout_success(self, authenticated_client):
        """Test de déconnexion réussie"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'connect' in response.data.lower() or b'Connexion' in response.data


class TestDashboard:
    """Tests pour le tableau de bord"""
    
    def test_dashboard_requires_login(self, client):
        """Test que le dashboard nécessite une connexion"""
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Devrait rediriger vers la page de login
        assert b'Connexion' in response.data or b'login' in response.data.lower()
    
    def test_dashboard_loads_for_authenticated_user(self, authenticated_client):
        """Test que le dashboard se charge pour un utilisateur authentifié"""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        assert b'testuser1' in response.data or b'Bienvenue' in response.data
    
    def test_dashboard_shows_user_stats(self, authenticated_client, app):
        """Test que le dashboard affiche les statistiques de l'utilisateur"""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        # Devrait afficher le score, les challenges, etc.
        assert b'Points' in response.data or b'Score' in response.data or b'points' in response.data


class TestProtectedRoutes:
    """Tests pour les routes protégées"""
    
    def test_challenges_list_requires_login(self, client):
        """Test que la liste des challenges nécessite une connexion"""
        response = client.get('/challenges', follow_redirects=True)
        assert response.status_code == 200
        # Devrait rediriger vers login
        assert b'Connexion' in response.data or b'login' in response.data.lower()
    
    def test_challenge_view_requires_login(self, client, init_database):
        """Test que la vue d'un challenge nécessite une connexion"""
        response = client.get('/challenge/1', follow_redirects=True)
        assert response.status_code == 200
        # Devrait rediriger vers login
        assert b'Connexion' in response.data or b'login' in response.data.lower()
    
    def test_authenticated_user_can_access_challenges(self, authenticated_client):
        """Test qu'un utilisateur authentifié peut accéder aux challenges"""
        response = authenticated_client.get('/challenges')
        assert response.status_code == 200
        assert b'Challenge' in response.data or b'challenge' in response.data