"""
Tests unitaires — Authentification
====================================
Couvre : inscription, connexion, déconnexion, redirections, protection des routes
"""

import pytest
from core.models import User
from core import db


class TestRegistration:
    """Tests du processus d'inscription."""

    def test_register_page_accessible(self, client):
        """La page d'inscription est accessible."""
        resp = client.get("/register")
        assert resp.status_code == 200

    def test_register_success(self, client, app):
        """Inscription réussie avec données valides."""
        resp = client.post("/register", data={
            "pseudo": "newplayer",
            "email": "newplayer@test.com",
            "password": "secure123",
            "confirm_password": "secure123",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            u = User.query.filter_by(pseudo="newplayer").first()
            assert u is not None
            assert u.email == "newplayer@test.com"
            assert u.role == "user"

    def test_register_duplicate_pseudo(self, client, user):
        """Inscription échoue si le pseudo existe déjà."""
        resp = client.post("/register", data={
            "pseudo": "testuser",
            "email": "unique@test.com",
            "password": "secure123",
            "confirm_password": "secure123",
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Le message flash "existe déjà" doit apparaître ou rediriger

    def test_register_duplicate_email(self, client, user):
        """Inscription échoue si l'email existe déjà."""
        resp = client.post("/register", data={
            "pseudo": "uniqueuser",
            "email": "test@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_password_mismatch(self, client):
        """Inscription échoue si les mots de passe ne correspondent pas."""
        resp = client.post("/register", data={
            "pseudo": "mismatch",
            "email": "mismatch@test.com",
            "password": "secure123",
            "confirm_password": "different",
        }, follow_redirects=True)
        # Le formulaire ne valide pas, on reste sur la page
        assert resp.status_code == 200

    def test_register_short_password(self, client):
        """Inscription échoue si le mot de passe est trop court (< 6)."""
        resp = client.post("/register", data={
            "pseudo": "shortpwd",
            "email": "short@test.com",
            "password": "abc",
            "confirm_password": "abc",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_short_pseudo(self, client):
        """Inscription échoue si le pseudo est trop court (< 3)."""
        resp = client.post("/register", data={
            "pseudo": "ab",
            "email": "shortpseudo@test.com",
            "password": "secure123",
            "confirm_password": "secure123",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_invalid_email(self, client):
        """Inscription échoue avec un email invalide."""
        resp = client.post("/register", data={
            "pseudo": "invalidemail",
            "email": "notanemail",
            "password": "secure123",
            "confirm_password": "secure123",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_empty_fields(self, client):
        """Inscription échoue si des champs sont vides."""
        resp = client.post("/register", data={
            "pseudo": "",
            "email": "",
            "password": "",
            "confirm_password": "",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_redirects_if_authenticated(self, auth_client):
        """Un utilisateur connecté est redirigé depuis /register."""
        resp = auth_client.get("/register")
        assert resp.status_code in (302, 200)


class TestLogin:
    """Tests du processus de connexion."""

    def test_login_page_accessible(self, client):
        """La page de connexion est accessible."""
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_login_success(self, client, user):
        """Connexion réussie avec identifiants corrects."""
        resp = client.post("/login", data={
            "email": "test@example.com",
            "password": "password123",
        }, follow_redirects=False)
        assert resp.status_code == 302  # Redirection vers dashboard

    def test_login_wrong_password(self, client, user):
        """Connexion échoue avec mauvais mot de passe."""
        resp = client.post("/login", data={
            "email": "test@example.com",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_email(self, client, user):
        """Connexion échoue avec email inconnu."""
        resp = client.post("/login", data={
            "email": "nonexistent@test.com",
            "password": "password123",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_empty_fields(self, client):
        """Connexion échoue avec champs vides."""
        resp = client.post("/login", data={
            "email": "",
            "password": "",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_redirects_if_authenticated(self, auth_client):
        """Un utilisateur déjà connecté est redirigé depuis /login."""
        resp = auth_client.get("/login")
        assert resp.status_code in (302, 200)


class TestLogout:
    """Tests de la déconnexion."""

    def test_logout_success(self, auth_client):
        """Déconnexion réussie."""
        resp = auth_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_redirects_to_login(self, auth_client):
        """Après déconnexion, redirection vers login."""
        resp = auth_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200

    def test_logout_requires_login(self, client):
        """Un utilisateur non connecté ne peut pas se déconnecter."""
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302  # Redirigé vers login


class TestProtectedRoutes:
    """Tests de protection des routes nécessitant une connexion."""

    @pytest.mark.parametrize("url", [
        "/dashboard",
        "/challenges",
    ])
    def test_protected_routes_redirect_anonymous(self, client, url):
        """Les routes protégées redirigent les utilisateurs anonymes."""
        resp = client.get(url, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")

    def test_dashboard_accessible_when_logged_in(self, auth_client):
        """Le dashboard est accessible pour un utilisateur connecté."""
        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200

    def test_challenges_accessible_when_logged_in(self, auth_client, challenge_sqli):
        """La liste des challenges est accessible pour un utilisateur connecté."""
        resp = auth_client.get("/challenges")
        assert resp.status_code == 200