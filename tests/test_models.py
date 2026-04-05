"""
Tests unitaires — Modèles de données
======================================
Couvre : User, Challenge, Flag, Submission, Scoreboard, RssFeed
"""

import pytest
import hashlib
from core import db
from core.models import User, Challenge, Flag, Submission, Scoreboard, RssFeed


# ═══════════════════════════════════════════════
#  USER MODEL
# ═══════════════════════════════════════════════

class TestUserModel:
    """Tests du modèle User."""

    def test_create_user(self, app, db_session):
        """Création d'un utilisateur avec tous les champs."""
        u = User(pseudo="alice", email="alice@test.com", role="user")
        u.set_password("securepass")
        db_session.add(u)
        db_session.commit()

        found = User.query.filter_by(pseudo="alice").first()
        assert found is not None
        assert found.email == "alice@test.com"
        assert found.role == "user"
        assert found.created_at is not None

    def test_password_hashing(self, user):
        """Le mot de passe est hashé et vérifiable."""
        assert user.password_hash != "password123"
        assert user.check_password("password123") is True
        assert user.check_password("wrongpassword") is False

    def test_password_hash_uniqueness(self, app, db_session):
        """Deux utilisateurs avec le même mot de passe ont des hash différents."""
        u1 = User(pseudo="u1", email="u1@test.com")
        u1.set_password("samepassword")
        u2 = User(pseudo="u2", email="u2@test.com")
        u2.set_password("samepassword")
        # Werkzeug utilise des sels aléatoires, donc les hash doivent différer
        assert u1.password_hash != u2.password_hash

    def test_user_default_role(self, app, db_session):
        """Le rôle par défaut est 'user'."""
        u = User(pseudo="newuser", email="new@test.com")
        u.set_password("pass123")
        db_session.add(u)
        db_session.commit()
        assert u.role == "user"

    def test_user_score_no_submissions(self, user):
        """Score = 0 quand aucune soumission."""
        assert user.score == 0
        assert user.getScore() == 0

    def test_user_score_with_scoreboard(self, app, user):
        """Score lu depuis le scoreboard s'il existe."""
        with app.app_context():
            sb = Scoreboard(user_id=user.id, points_total=150)
            db.session.add(sb)
            db.session.commit()
            refreshed = User.query.get(user.id)
            assert refreshed.score == 150

    def test_get_solved_challenges_empty(self, user):
        """Aucun challenge résolu initialement."""
        assert user.get_solved_challenges() == []

    def test_get_solved_challenges(self, app, user, challenge_sqli):
        """Un challenge apparaît dans solved après un flag correct."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
            u = User.query.get(user.id)
            solved = u.get_solved_challenges()
            assert len(solved) == 1
            assert solved[0].id == challenge_sqli.id

    def test_get_in_progress_challenges(self, app, user, challenge_sqli):
        """Challenge tenté mais non résolu = in progress."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{wrong}")
            sub.enregistrer()
            u = User.query.get(user.id)
            in_progress = u.get_in_progress_challenges()
            assert len(in_progress) == 1

    def test_get_not_started_challenges(self, app, user, all_challenges):
        """Challenges actifs non tentés."""
        with app.app_context():
            u = User.query.get(user.id)
            not_started = u.get_not_started_challenges()
            assert len(not_started) == 3

    def test_pseudo_unique_constraint(self, app, user, db_session):
        """Pseudo dupliqué lève une erreur."""
        u2 = User(pseudo="testuser", email="other@test.com")
        u2.set_password("pass")
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_email_unique_constraint(self, app, user, db_session):
        """Email dupliqué lève une erreur."""
        u2 = User(pseudo="otheruser", email="test@example.com")
        u2.set_password("pass")
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


# ═══════════════════════════════════════════════
#  CHALLENGE MODEL
# ═══════════════════════════════════════════════

class TestChallengeModel:
    """Tests du modèle Challenge."""

    def test_create_challenge(self, app, db_session):
        """Création d'un challenge."""
        c = Challenge(titre="Test Challenge", description="Desc", points=50, actif=True)
        db_session.add(c)
        db_session.commit()
        assert c.id is not None
        assert c.actif is True

    def test_activer_desactiver(self, challenge_sqli, app):
        """Activation et désactivation d'un challenge."""
        with app.app_context():
            c = Challenge.query.get(challenge_sqli.id)
            c.desactiver()
            assert Challenge.query.get(c.id).actif is False
            c.activer()
            assert Challenge.query.get(c.id).actif is True

    def test_challenge_cascade_delete(self, app, challenge_sqli, user):
        """Supprimer un challenge supprime ses soumissions et flags (cascade)."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id, flag_soumis="test")
            db.session.add(sub)
            db.session.commit()

            assert Submission.query.filter_by(challenge_id=challenge_sqli.id).count() == 1
            assert Flag.query.filter_by(challenge_id=challenge_sqli.id).count() == 1

            db.session.delete(Challenge.query.get(challenge_sqli.id))
            db.session.commit()

            assert Submission.query.filter_by(challenge_id=challenge_sqli.id).count() == 0
            assert Flag.query.filter_by(challenge_id=challenge_sqli.id).count() == 0


# ═══════════════════════════════════════════════
#  FLAG MODEL
# ═══════════════════════════════════════════════

class TestFlagModel:
    """Tests du modèle Flag."""

    def test_flag_hash_sha256(self):
        """Le hash utilise SHA-256."""
        plain = "CTF{test_flag}"
        expected = hashlib.sha256(plain.encode("utf-8")).hexdigest()
        assert Flag._hash(plain) == expected

    def test_set_and_verify_flag(self, challenge_sqli, app):
        """setFlag + verifierFlag fonctionnent ensemble."""
        with app.app_context():
            flag = Flag.query.filter_by(challenge_id=challenge_sqli.id).first()
            assert flag.verifierFlag("CTF{SQL_1nj3ct10n_m4st3r}") is True
            assert flag.verifierFlag("CTF{wrong}") is False

    def test_flag_case_sensitive(self, challenge_sqli, app):
        """Les flags sont sensibles à la casse."""
        with app.app_context():
            flag = Flag.query.filter_by(challenge_id=challenge_sqli.id).first()
            assert flag.verifierFlag("ctf{sql_1nj3ct10n_m4st3r}") is False

    def test_update_flag(self, challenge_sqli, app):
        """Mise à jour d'un flag existant."""
        with app.app_context():
            flag = Flag.query.filter_by(challenge_id=challenge_sqli.id).first()
            flag.setFlag("CTF{new_flag}")
            db.session.commit()
            assert flag.verifierFlag("CTF{new_flag}") is True
            assert flag.verifierFlag("CTF{SQL_1nj3ct10n_m4st3r}") is False


# ═══════════════════════════════════════════════
#  SUBMISSION MODEL
# ═══════════════════════════════════════════════

class TestSubmissionModel:
    """Tests du modèle Submission."""

    def test_correct_submission(self, app, user, challenge_sqli):
        """Soumission correcte : correct=True, scoreboard mis à jour."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            result = sub.enregistrer()
            assert result is True
            assert sub.correct is True

            sb = Scoreboard.query.filter_by(user_id=user.id).first()
            assert sb is not None
            assert sb.points_total == 25

    def test_incorrect_submission(self, app, user, challenge_sqli):
        """Soumission incorrecte : correct=False, pas de points."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{wrong}")
            result = sub.enregistrer()
            assert result is False
            assert sub.correct is False

            sb = Scoreboard.query.filter_by(user_id=user.id).first()
            assert sb is None

    def test_duplicate_correct_no_double_points(self, app, user, challenge_sqli):
        """Un flag correct soumis deux fois ne donne les points qu'une seule fois."""
        with app.app_context():
            sub1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                              flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub1.enregistrer()

            sub2 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                              flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub2.enregistrer()

            sb = Scoreboard.query.filter_by(user_id=user.id).first()
            assert sb.points_total == 25  # Pas 50

    def test_multiple_challenges_score(self, app, user, challenge_sqli, challenge_xss):
        """Résoudre 2 challenges cumule les points."""
        with app.app_context():
            sub1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                              flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub1.enregistrer()

            sub2 = Submission(user_id=user.id, challenge_id=challenge_xss.id,
                              flag_soumis="CTF{XSS_r3fl3ct3d_pwn3d}")
            sub2.enregistrer()

            sb = Scoreboard.query.filter_by(user_id=user.id).first()
            assert sb.points_total == 50  # 25 + 25

    def test_submission_timestamp(self, app, user, challenge_sqli):
        """Chaque soumission a un timestamp."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id, flag_soumis="test")
            sub.enregistrer()
            assert sub.timestamp is not None

    def test_verifier_without_flag(self, app, user):
        """Soumission sur un challenge sans flag = False."""
        with app.app_context():
            c = Challenge(titre="No Flag", description="Test", points=10, actif=True)
            db.session.add(c)
            db.session.commit()
            sub = Submission(user_id=user.id, challenge_id=c.id, flag_soumis="anything")
            assert sub.verifier() is False


# ═══════════════════════════════════════════════
#  SCOREBOARD MODEL
# ═══════════════════════════════════════════════

class TestScoreboardModel:
    """Tests du modèle Scoreboard."""

    def test_calculer_score(self, app, user, challenge_sqli):
        """calculerScore recalcule le total depuis les soumissions."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
            total = Scoreboard.calculerScore(user.id)
            assert total == 25

    def test_afficher_classement(self, app, user, admin_user, challenge_sqli, challenge_xss):
        """Le classement est trié par points décroissants."""
        with app.app_context():
            # User résout 1 challenge (25 pts)
            s1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s1.enregistrer()

            # Admin résout 2 challenges (50 pts)
            s2 = Submission(user_id=admin_user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s2.enregistrer()
            s3 = Submission(user_id=admin_user.id, challenge_id=challenge_xss.id,
                            flag_soumis="CTF{XSS_r3fl3ct3d_pwn3d}")
            s3.enregistrer()

            classement = Scoreboard.afficherClassement(limit=10)
            assert len(classement) == 2
            assert classement[0][1].pseudo == "adminuser"  # 50 pts en premier
            assert classement[1][1].pseudo == "testuser"    # 25 pts en second

    def test_empty_classement(self, app):
        """Classement vide quand aucun score."""
        with app.app_context():
            classement = Scoreboard.afficherClassement()
            assert len(classement) == 0


# ═══════════════════════════════════════════════
#  RSS FEED MODEL
# ═══════════════════════════════════════════════

class TestRssFeedModel:
    """Tests du modèle RssFeed."""

    def test_create_feed(self, app, db_session):
        """Création d'un flux RSS."""
        feed = RssFeed(nom="Test Feed", url="https://test.com/rss", actif=False, langue="EN")
        db_session.add(feed)
        db_session.commit()
        assert feed.id is not None
        assert feed.actif is False

    def test_feed_url_unique(self, rss_feed, app, db_session):
        """URL de flux dupliquée lève une erreur."""
        feed2 = RssFeed(nom="Duplicate", url=rss_feed.url, actif=False)
        db_session.add(feed2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_feed_repr(self, rss_feed):
        """Représentation string du flux."""
        assert "CERT-FR Test" in repr(rss_feed)

    def test_feed_default_inactive(self, app, db_session):
        """Un flux est inactif par défaut."""
        feed = RssFeed(nom="New", url="https://new.com/rss")
        db_session.add(feed)
        db_session.commit()
        assert feed.actif is False