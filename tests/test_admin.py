"""
Tests unitaires — Panel Administrateur
=========================================
Couvre : accès admin, dashboard, gestion utilisateurs (ban/unban/reset),
         gestion challenges (toggle/edit), soumissions, flux RSS (CRUD),
         export CSV, protection des routes admin
"""

import pytest
from core.models import User, Challenge, Flag, Submission, Scoreboard, RssFeed
from core import db


# ═══════════════════════════════════════════════
#  ACCÈS ET PROTECTION ADMIN
# ═══════════════════════════════════════════════

class TestAdminAccess:
    """Tests de protection des routes admin."""

    def test_admin_dashboard_accessible_for_admin(self, admin_client):
        """Le dashboard admin est accessible pour un admin."""
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200

    def test_admin_dashboard_forbidden_for_user(self, auth_client):
        """Le dashboard admin est interdit pour un utilisateur normal."""
        resp = auth_client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302  # Redirigé

    def test_admin_dashboard_forbidden_for_anonymous(self, client):
        """Le dashboard admin est interdit pour un visiteur anonyme."""
        resp = client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302

    @pytest.mark.parametrize("url", [
        "/admin/users",
        "/admin/challenges",
        "/admin/submissions",
        "/admin/actualites",
        "/admin/export",
    ])
    def test_admin_routes_forbidden_for_user(self, auth_client, url):
        """Toutes les routes admin sont interdites pour un user normal."""
        resp = auth_client.get(url, follow_redirects=False)
        assert resp.status_code == 302

    @pytest.mark.parametrize("url", [
        "/admin/",
        "/admin/users",
        "/admin/challenges",
        "/admin/submissions",
        "/admin/actualites",
    ])
    def test_admin_routes_accessible_for_admin(self, admin_client, url):
        """Toutes les routes admin sont accessibles pour un admin."""
        resp = admin_client.get(url)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════
#  DASHBOARD ADMIN
# ═══════════════════════════════════════════════

class TestAdminDashboard:
    """Tests du dashboard admin."""

    def test_dashboard_shows_stats(self, admin_client, user, challenge_sqli):
        """Le dashboard affiche les statistiques."""
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════
#  GESTION DES UTILISATEURS
# ═══════════════════════════════════════════════

class TestAdminUsers:
    """Tests de la gestion des utilisateurs par l'admin."""

    def test_users_list(self, admin_client, user):
        """La liste des utilisateurs s'affiche."""
        resp = admin_client.get("/admin/users")
        assert resp.status_code == 200

    def test_ban_user(self, admin_client, app, user):
        """Bannir un utilisateur change son rôle."""
        resp = admin_client.post(f"/admin/users/{user.id}/ban", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            u = User.query.get(user.id)
            assert u.role == "banned"

    def test_unban_user(self, admin_client, app, banned_user):
        """Débannir un utilisateur restaure son rôle."""
        resp = admin_client.post(f"/admin/users/{banned_user.id}/ban",
                                 follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            u = User.query.get(banned_user.id)
            assert u.role == "user"

    def test_admin_cannot_ban_self(self, admin_client, app, admin_user):
        """Un admin ne peut pas se bannir lui-même."""
        resp = admin_client.post(f"/admin/users/{admin_user.id}/ban",
                                 follow_redirects=True)
        with app.app_context():
            u = User.query.get(admin_user.id)
            assert u.role == "admin"

    def test_ban_nonexistent_user(self, admin_client):
        """Bannir un utilisateur inexistant = 404."""
        resp = admin_client.post("/admin/users/99999/ban")
        assert resp.status_code == 404

    def test_reset_user_score(self, admin_client, app, user, challenge_sqli):
        """Réinitialiser le score d'un utilisateur."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
            assert Scoreboard.query.filter_by(user_id=user.id).first().points_total == 25

        resp = admin_client.post(f"/admin/users/{user.id}/reset_score",
                                 follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            sb = Scoreboard.query.filter_by(user_id=user.id).first()
            assert sb.points_total == 0
            assert Submission.query.filter_by(user_id=user.id).count() == 0

    def test_reset_nonexistent_user(self, admin_client):
        """Reset d'un utilisateur inexistant = 404."""
        resp = admin_client.post("/admin/users/99999/reset_score")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════
#  GESTION DES CHALLENGES
# ═══════════════════════════════════════════════

class TestAdminChallenges:
    """Tests de la gestion des challenges par l'admin."""

    def test_challenges_list(self, admin_client, challenge_sqli):
        """La liste des challenges admin s'affiche."""
        resp = admin_client.get("/admin/challenges")
        assert resp.status_code == 200

    def test_toggle_challenge_deactivate(self, admin_client, app, challenge_sqli):
        """Désactiver un challenge actif."""
        resp = admin_client.post(f"/admin/challenges/{challenge_sqli.id}/toggle",
                                 follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            c = Challenge.query.get(challenge_sqli.id)
            assert c.actif is False

    def test_toggle_challenge_activate(self, admin_client, app, challenge_inactive):
        """Activer un challenge inactif."""
        resp = admin_client.post(f"/admin/challenges/{challenge_inactive.id}/toggle",
                                 follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            c = Challenge.query.get(challenge_inactive.id)
            assert c.actif is True

    def test_toggle_nonexistent_challenge(self, admin_client):
        """Toggle d'un challenge inexistant = 404."""
        resp = admin_client.post("/admin/challenges/99999/toggle")
        assert resp.status_code == 404

    def test_edit_challenge_get(self, admin_client, challenge_sqli):
        """La page d'édition d'un challenge est accessible."""
        resp = admin_client.get(f"/admin/challenges/{challenge_sqli.id}/edit")
        assert resp.status_code == 200

    def test_edit_challenge_post(self, admin_client, app, challenge_sqli):
        """Modifier un challenge met à jour les données."""
        resp = admin_client.post(f"/admin/challenges/{challenge_sqli.id}/edit", data={
            "titre": "SQLi Modifié",
            "description": "Nouvelle description",
            "points": "50",
            "flag": "",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            c = Challenge.query.get(challenge_sqli.id)
            assert c.titre == "SQLi Modifié"
            assert c.points == 50

    def test_edit_challenge_with_new_flag(self, admin_client, app, challenge_sqli):
        """Modifier le flag d'un challenge."""
        resp = admin_client.post(f"/admin/challenges/{challenge_sqli.id}/edit", data={
            "titre": "SQL Injection",
            "description": "Exploitez la faille SQLi",
            "points": "25",
            "flag": "CTF{new_flag_value}",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            c = Challenge.query.get(challenge_sqli.id)
            assert c.flag.verifierFlag("CTF{new_flag_value}") is True
            assert c.flag.verifierFlag("CTF{SQL_1nj3ct10n_m4st3r}") is False


# ═══════════════════════════════════════════════
#  SOUMISSIONS ADMIN
# ═══════════════════════════════════════════════

class TestAdminSubmissions:
    """Tests de l'historique des soumissions côté admin."""

    def test_submissions_page(self, admin_client):
        """La page des soumissions est accessible."""
        resp = admin_client.get("/admin/submissions")
        assert resp.status_code == 200

    def test_submissions_filter_correct(self, admin_client, app, user, challenge_sqli):
        """Filtrer les soumissions correctes."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
        resp = admin_client.get("/admin/submissions?status=correct")
        assert resp.status_code == 200

    def test_submissions_filter_incorrect(self, admin_client, app, user, challenge_sqli):
        """Filtrer les soumissions incorrectes."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{wrong}")
            sub.enregistrer()
        resp = admin_client.get("/admin/submissions?status=incorrect")
        assert resp.status_code == 200

    def test_submissions_pagination(self, admin_client):
        """La pagination fonctionne."""
        resp = admin_client.get("/admin/submissions?page=1")
        assert resp.status_code == 200
        resp = admin_client.get("/admin/submissions?page=999")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════
#  GESTION RSS
# ═══════════════════════════════════════════════

class TestAdminRss:
    """Tests de la gestion des flux RSS par l'admin."""

    def test_rss_feeds_page(self, admin_client):
        """La page de gestion RSS est accessible."""
        resp = admin_client.get("/admin/actualites")
        assert resp.status_code == 200

    def test_add_rss_feed(self, admin_client, app):
        """Ajouter un flux RSS."""
        resp = admin_client.post("/admin/actualites/add", data={
            "nom": "Test Feed",
            "url": "https://example.com/rss",
            "langue": "EN",
        }, follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            feed = RssFeed.query.filter_by(nom="Test Feed").first()
            assert feed is not None
            assert feed.actif is False

    def test_add_rss_feed_missing_fields(self, admin_client):
        """Ajout échoue avec champs manquants."""
        resp = admin_client.post("/admin/actualites/add", data={
            "nom": "",
            "url": "",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_add_rss_feed_invalid_url(self, admin_client):
        """Ajout échoue avec URL invalide."""
        resp = admin_client.post("/admin/actualites/add", data={
            "nom": "Bad",
            "url": "not-a-url",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_add_duplicate_rss_feed(self, admin_client, rss_feed):
        """Ajout échoue si l'URL existe déjà."""
        resp = admin_client.post("/admin/actualites/add", data={
            "nom": "Duplicate",
            "url": rss_feed.url,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_toggle_rss_feed(self, admin_client, app, rss_feed):
        """Activer/désactiver un flux RSS."""
        # Le flux est actif, on le désactive
        resp = admin_client.post(f"/admin/actualites/{rss_feed.id}/toggle",
                                 follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            feed = RssFeed.query.get(rss_feed.id)
            assert feed.actif is False

    def test_delete_rss_feed(self, admin_client, app, rss_feed):
        """Supprimer un flux RSS."""
        resp = admin_client.post(f"/admin/actualites/{rss_feed.id}/delete",
                                 follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert RssFeed.query.get(rss_feed.id) is None

    def test_toggle_nonexistent_feed(self, admin_client):
        """Toggle d'un flux inexistant = 404."""
        resp = admin_client.post("/admin/actualites/99999/toggle")
        assert resp.status_code == 404

    def test_delete_nonexistent_feed(self, admin_client):
        """Suppression d'un flux inexistant = 404."""
        resp = admin_client.post("/admin/actualites/99999/delete")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════
#  EXPORT CSV
# ═══════════════════════════════════════════════

class TestAdminExport:
    """Tests de l'export CSV du scoreboard."""

    def test_export_csv_empty(self, admin_client):
        """Export CSV vide (aucun score)."""
        resp = admin_client.get("/admin/export")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"
        content = resp.data.decode("utf-8")
        assert "Rang" in content
        assert "Pseudo" in content

    def test_export_csv_with_data(self, admin_client, app, user, challenge_sqli):
        """Export CSV avec des données."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
        resp = admin_client.get("/admin/export")
        assert resp.status_code == 200
        content = resp.data.decode("utf-8")
        assert "testuser" in content
        assert "25" in content

    def test_export_csv_forbidden_for_user(self, auth_client):
        """L'export CSV est interdit pour un user normal."""
        resp = auth_client.get("/admin/export", follow_redirects=False)
        assert resp.status_code == 302