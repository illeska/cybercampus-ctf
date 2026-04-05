"""
Tests unitaires — Sécurité & Rôles
=====================================
Couvre : contrôle d'accès basé sur les rôles (RBAC), isolation des données
         entre utilisateurs, vérification des flags de chaque challenge,
         protection contre les manipulations
"""

import pytest
from core.models import User, Submission, Scoreboard, Challenge, Flag
from core import db


class TestRoleBasedAccess:
    """Tests du contrôle d'accès par rôle."""

    def test_user_cannot_access_admin(self, auth_client):
        """Un utilisateur standard ne peut pas accéder au panel admin."""
        resp = auth_client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 302

    def test_user_cannot_ban(self, auth_client, admin_user):
        """Un utilisateur standard ne peut pas bannir."""
        resp = auth_client.post(f"/admin/users/{admin_user.id}/ban",
                                follow_redirects=False)
        assert resp.status_code == 302

    def test_user_cannot_toggle_challenge(self, auth_client, challenge_sqli):
        """Un utilisateur standard ne peut pas désactiver un challenge."""
        resp = auth_client.post(f"/admin/challenges/{challenge_sqli.id}/toggle",
                                follow_redirects=False)
        assert resp.status_code == 302

    def test_user_cannot_export_csv(self, auth_client):
        """Un utilisateur standard ne peut pas exporter le CSV."""
        resp = auth_client.get("/admin/export", follow_redirects=False)
        assert resp.status_code == 302

    def test_user_cannot_manage_rss(self, auth_client):
        """Un utilisateur standard ne peut pas gérer les flux RSS."""
        resp = auth_client.post("/admin/actualites/add", data={
            "nom": "Hack", "url": "https://evil.com/rss"
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_can_access_all(self, admin_client, challenge_sqli, user):
        """Un admin peut accéder à toutes les sections."""
        for url in ["/admin/", "/admin/users", "/admin/challenges",
                    "/admin/submissions", "/admin/actualites"]:
            resp = admin_client.get(url)
            assert resp.status_code == 200, f"Admin ne peut pas accéder à {url}"

    def test_anonymous_cannot_submit_flag(self, client, challenge_sqli):
        """Un visiteur anonyme ne peut pas soumettre de flag."""
        resp = client.post(f"/challenge/{challenge_sqli.id}/submit",
                           data={"flag": "CTF{test}"}, follow_redirects=False)
        assert resp.status_code == 302

    def test_anonymous_cannot_view_challenge(self, client, challenge_sqli):
        """Un visiteur anonyme ne peut pas voir un challenge."""
        resp = client.get(f"/challenge/{challenge_sqli.id}", follow_redirects=False)
        assert resp.status_code == 302


class TestDataIsolation:
    """Tests d'isolation des données entre utilisateurs."""

    def test_user_scores_independent(self, app, user, admin_user, challenge_sqli):
        """Les scores de deux utilisateurs sont indépendants."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()

            u = User.query.get(user.id)
            a = User.query.get(admin_user.id)
            assert u.score == 25
            assert a.score == 0

    def test_solved_challenges_per_user(self, app, user, admin_user, challenge_sqli):
        """Les challenges résolus sont propres à chaque utilisateur."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()

            u = User.query.get(user.id)
            a = User.query.get(admin_user.id)
            assert len(u.get_solved_challenges()) == 1
            assert len(a.get_solved_challenges()) == 0


class TestAllChallengeFlags:
    """Vérification des flags pour chaque challenge du projet."""

    CHALLENGE_FLAGS = [
        (1, "SQL Injection", "CTF{SQL_1nj3ct10n_m4st3r}", 25),
        (2, "XSS Reflected", "CTF{XSS_r3fl3ct3d_pwn3d}", 25),
        (3, "Bruteforce", "CTF{Brut3F0rc3_M4st3r_7394}", 175),
    ]

    @pytest.mark.parametrize("cid,titre,flag_str,points", CHALLENGE_FLAGS)
    def test_flag_verification(self, app, cid, titre, flag_str, points):
        """Le flag de chaque challenge est vérifié correctement."""
        with app.app_context():
            c = Challenge(id=cid, titre=titre, description="Test", points=points, actif=True)
            db.session.add(c)
            db.session.flush()
            f = Flag(challenge_id=c.id)
            f.setFlag(flag_str)
            db.session.add(f)
            db.session.commit()

            assert f.verifierFlag(flag_str) is True
            assert f.verifierFlag("CTF{wrong}") is False
            assert f.verifierFlag("") is False
            assert f.verifierFlag(flag_str.lower()) is (flag_str == flag_str.lower())

    def test_all_challenge_flags_defined(self):
        """Vérifie qu'on teste bien tous les challenges principaux."""
        assert len(self.CHALLENGE_FLAGS) >= 3


class TestSecurityMiscellaneous:
    """Tests de sécurité divers."""

    def test_password_not_stored_in_plain(self, user):
        """Le mot de passe n'est pas stocké en clair."""
        assert user.password_hash != "password123"
        assert "password123" not in user.password_hash

    def test_flag_stored_as_hash(self, app, challenge_sqli):
        """Le flag est stocké hashé (SHA-256)."""
        with app.app_context():
            flag = Flag.query.filter_by(challenge_id=challenge_sqli.id).first()
            assert flag.flag_hash != "CTF{SQL_1nj3ct10n_m4st3r}"
            assert len(flag.flag_hash) == 64  # SHA-256 = 64 hex chars

    def test_submission_records_flag_soumis(self, app, user, challenge_sqli):
        """La soumission enregistre le flag soumis (pour audit)."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{attempt}")
            sub.enregistrer()
            saved = Submission.query.filter_by(user_id=user.id).first()
            assert saved.flag_soumis == "CTF{attempt}"

    def test_cannot_submit_to_inactive_challenge_via_view(self, auth_client, challenge_inactive):
        """Accéder à un challenge inactif redirige."""
        resp = auth_client.get(f"/challenge/{challenge_inactive.id}",
                               follow_redirects=False)
        assert resp.status_code == 302