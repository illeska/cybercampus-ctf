"""
Tests unitaires — Pages Publiques
====================================
Couvre : accueil, scoreboard, mentions légales, CGU, politique de confidentialité,
         pages de cours (learn), actualités, redirections
"""

import pytest


class TestHomePage:
    """Tests de la page d'accueil."""

    def test_root_redirects_to_home(self, client):
        """/ redirige vers /home."""
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/home" in resp.headers.get("Location", "")

    def test_home_page_accessible(self, client):
        """La page d'accueil est accessible sans connexion."""
        resp = client.get("/home")
        assert resp.status_code == 200

    def test_home_page_authenticated(self, auth_client):
        """La page d'accueil est accessible avec connexion."""
        resp = auth_client.get("/home")
        assert resp.status_code == 200


class TestLegalPages:
    """Tests des pages légales."""

    def test_mentions_legales(self, client):
        """Mentions légales accessibles."""
        resp = client.get("/mentionslegales")
        assert resp.status_code == 200

    def test_politique_confidentialite(self, client):
        """Politique de confidentialité accessible."""
        resp = client.get("/politiqueconfidentialite")
        assert resp.status_code == 200

    def test_cgu(self, client):
        """CGU accessibles."""
        resp = client.get("/cgu")
        assert resp.status_code == 200


class TestScoreboardPage:
    """Tests de la page de classement."""

    def test_scoreboard_accessible_anonymous(self, client):
        """Le scoreboard est accessible sans connexion."""
        resp = client.get("/scoreboard")
        assert resp.status_code == 200

    def test_scoreboard_accessible_authenticated(self, auth_client):
        """Le scoreboard est accessible avec connexion."""
        resp = auth_client.get("/scoreboard")
        assert resp.status_code == 200

    def test_scoreboard_with_data(self, auth_client, app, user, challenge_sqli):
        """Le scoreboard affiche les données après une soumission correcte."""
        from core.models import Submission
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
        resp = auth_client.get("/scoreboard")
        assert resp.status_code == 200


class TestActualitesPage:
    """Tests de la page d'actualités."""

    def test_actualites_accessible(self, client):
        """La page d'actualités est accessible."""
        resp = client.get("/actualites")
        assert resp.status_code == 200

    def test_actualites_with_active_feed(self, client, rss_feed):
        """La page d'actualités charge avec un flux actif."""
        resp = client.get("/actualites")
        assert resp.status_code == 200


class TestLearnPages:
    """Tests des pages de cours."""

    def test_learn_index(self, client):
        """La bibliothèque de cours est accessible."""
        resp = client.get("/learn")
        assert resp.status_code == 200

    @pytest.mark.parametrize("path,expected_status", [
        ("/learn/sqli", 200),
        ("/learn/xss", 200),
        ("/learn/bruteforce", 200),
        ("/learn/crypto", 200),
        ("/learn/osint", 200),
        ("/learn/upload", 200),
        ("/learn/stegano", 200),
    ])
    def test_learn_course_pages(self, client, path, expected_status):
        """Chaque page de cours est accessible sans connexion."""
        resp = client.get(path)
        assert resp.status_code == expected_status

    def test_learn_pages_accessible_authenticated(self, auth_client):
        """Les pages de cours sont accessibles avec connexion."""
        for path in ["/learn", "/learn/sqli", "/learn/xss", "/learn/bruteforce",
                     "/learn/crypto", "/learn/osint", "/learn/upload", "/learn/stegano"]:
            resp = auth_client.get(path)
            assert resp.status_code == 200, f"Page {path} inaccessible"


class TestNonExistentRoutes:
    """Tests des routes inexistantes."""

    def test_404_on_unknown_route(self, client):
        """Une route inexistante retourne 404."""
        resp = client.get("/this-page-does-not-exist")
        assert resp.status_code == 404

    def test_404_on_unknown_learn_page(self, client):
        """Un cours inexistant retourne 404."""
        resp = client.get("/learn/nonexistent")
        assert resp.status_code == 404