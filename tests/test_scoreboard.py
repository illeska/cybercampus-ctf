"""
Tests unitaires — Scoreboard & Classement
============================================
Couvre : calcul de score, classement, position utilisateur, cumul multi-challenges
"""

import pytest
from core.models import User, Submission, Scoreboard, Challenge, Flag
from core import db


class TestScoreCalculation:
    """Tests du calcul de score."""

    def test_score_zero_initially(self, user):
        """Score initial = 0."""
        assert user.score == 0

    def test_score_after_one_correct(self, app, user, challenge_sqli):
        """Score = points du challenge après une résolution."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
            u = User.query.get(user.id)
            assert u.score == 25

    def test_score_after_multiple_correct(self, app, user, challenge_sqli, challenge_xss):
        """Score = somme des points après plusieurs résolutions."""
        with app.app_context():
            s1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s1.enregistrer()
            s2 = Submission(user_id=user.id, challenge_id=challenge_xss.id,
                            flag_soumis="CTF{XSS_r3fl3ct3d_pwn3d}")
            s2.enregistrer()
            u = User.query.get(user.id)
            assert u.score == 50

    def test_score_not_affected_by_wrong_submissions(self, app, user, challenge_sqli):
        """Les soumissions incorrectes n'affectent pas le score."""
        with app.app_context():
            for _ in range(5):
                sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                                 flag_soumis="CTF{wrong}")
                sub.enregistrer()
            u = User.query.get(user.id)
            assert u.score == 0

    def test_recalculate_score(self, app, user, challenge_sqli, challenge_xss):
        """calculerScore recalcule correctement le total."""
        with app.app_context():
            s1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s1.enregistrer()
            s2 = Submission(user_id=user.id, challenge_id=challenge_xss.id,
                            flag_soumis="CTF{XSS_r3fl3ct3d_pwn3d}")
            s2.enregistrer()
            total = Scoreboard.calculerScore(user.id)
            assert total == 50


class TestClassement:
    """Tests du classement."""

    def test_classement_order(self, app, user, admin_user, challenge_sqli, challenge_xss,
                              challenge_bruteforce):
        """Le classement est trié par points décroissants."""
        with app.app_context():
            # User: 25 pts (1 challenge)
            s1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s1.enregistrer()

            # Admin: 200 pts (2 challenges = 25 + 175)
            s2 = Submission(user_id=admin_user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s2.enregistrer()
            s3 = Submission(user_id=admin_user.id, challenge_id=challenge_bruteforce.id,
                            flag_soumis="CTF{Brut3F0rc3_M4st3r_7394}")
            s3.enregistrer()

            classement = Scoreboard.afficherClassement(limit=10)
            assert len(classement) == 2
            assert classement[0][0].points_total == 200
            assert classement[1][0].points_total == 25

    def test_classement_limit(self, app, user, admin_user, challenge_sqli):
        """Le classement respecte la limite demandée."""
        with app.app_context():
            s1 = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s1.enregistrer()
            s2 = Submission(user_id=admin_user.id, challenge_id=challenge_sqli.id,
                            flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            s2.enregistrer()

            classement = Scoreboard.afficherClassement(limit=1)
            assert len(classement) == 1

    def test_classement_empty(self, app):
        """Classement vide si personne n'a de score."""
        with app.app_context():
            classement = Scoreboard.afficherClassement()
            assert len(classement) == 0

    def test_user_rank_on_scoreboard_page(self, auth_client, app, user, challenge_sqli):
        """La position de l'utilisateur apparaît sur le scoreboard."""
        with app.app_context():
            sub = Submission(user_id=user.id, challenge_id=challenge_sqli.id,
                             flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
            sub.enregistrer()
        resp = auth_client.get("/scoreboard")
        assert resp.status_code == 200


class TestScoreboardEdgeCases:
    """Tests des cas limites du scoreboard."""

    def test_score_with_zero_point_challenge(self, app, user):
        """Un challenge à 0 points n'affecte pas le score."""
        with app.app_context():
            c = Challenge(titre="Zero pts", description="Test", points=0, actif=True)
            db.session.add(c)
            db.session.flush()
            f = Flag(challenge_id=c.id)
            f.setFlag("CTF{zero}")
            db.session.add(f)
            db.session.commit()

            sub = Submission(user_id=user.id, challenge_id=c.id, flag_soumis="CTF{zero}")
            sub.enregistrer()

            sb = Scoreboard.query.filter_by(user_id=user.id).first()
            assert sb.points_total == 0

    def test_many_users_ranking(self, app, challenge_sqli):
        """Le classement gère correctement 10+ utilisateurs."""
        with app.app_context():
            for i in range(15):
                u = User(pseudo=f"player_{i}", email=f"p{i}@test.com")
                u.set_password("pass123")
                db.session.add(u)
                db.session.commit()

                sub = Submission(user_id=u.id, challenge_id=challenge_sqli.id,
                                 flag_soumis="CTF{SQL_1nj3ct10n_m4st3r}")
                sub.enregistrer()

            classement = Scoreboard.afficherClassement(limit=100)
            assert len(classement) == 15