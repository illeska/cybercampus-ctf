# tests/test_models.py
"""
Tests unitaires pour les modèles de données
"""

import pytest
from core.models import User, Challenge, Flag, Submission, Scoreboard
from core import db


class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_user_creation(self, app):
        """Test de création d'un utilisateur"""
        with app.app_context():
            user = User(pseudo="newuser", email="new@example.com")
            user.set_password("testpass123")
            
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.pseudo == "newuser"
            assert user.email == "new@example.com"
            assert user.role == "user"  # Rôle par défaut
            assert user.password_hash is not None
            assert user.password_hash != "testpass123"  # Hash != password
    
    def test_password_hashing(self, app):
        """Test du hashing de mot de passe"""
        with app.app_context():
            user = User(pseudo="test", email="test@example.com")
            user.set_password("mypassword")
            
            # Le mot de passe ne doit pas être stocké en clair
            assert user.password_hash != "mypassword"
            
            # check_password doit valider le bon mot de passe
            assert user.check_password("mypassword") is True
            assert user.check_password("wrongpassword") is False
    
    def test_user_score_property(self, app, init_database):
        """Test de la propriété score"""
        with app.app_context():
            data = init_database
            user = User.query.get(data['user1'].id)
            
            # Score initial devrait être 0
            assert user.score == 0
            
            # Ajouter une soumission correcte
            submission = Submission(
                user_id=user.id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
            
            # Le score devrait être mis à jour
            db.session.refresh(user)
            assert user.score == 100
    
    def test_get_solved_challenges(self, app, init_database):
        """Test de récupération des challenges résolus"""
        with app.app_context():
            data = init_database
            user = User.query.get(data['user1'].id)
            
            # Aucun challenge résolu initialement
            assert len(user.get_solved_challenges()) == 0
            
            # Résoudre un challenge
            submission = Submission(
                user_id=user.id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
            
            # Un challenge devrait être résolu
            solved = user.get_solved_challenges()
            assert len(solved) == 1
            assert solved[0].id == data['challenge1'].id


class TestChallengeModel:
    """Tests pour le modèle Challenge"""
    
    def test_challenge_creation(self, app):
        """Test de création d'un challenge"""
        with app.app_context():
            challenge = Challenge(
                titre="Test Challenge",
                description="Description de test",
                points=50,
                actif=True
            )
            
            db.session.add(challenge)
            db.session.commit()
            
            assert challenge.id is not None
            assert challenge.titre == "Test Challenge"
            assert challenge.points == 50
            assert challenge.actif is True
    
    def test_challenge_activation(self, app, init_database):
        """Test d'activation/désactivation d'un challenge"""
        with app.app_context():
            data = init_database
            challenge = Challenge.query.get(data['challenge3'].id)
            
            # Challenge 3 est inactif par défaut
            assert challenge.actif is False
            
            # Activer
            challenge.activer()
            db.session.refresh(challenge)
            assert challenge.actif is True
            
            # Désactiver
            challenge.desactiver()
            db.session.refresh(challenge)
            assert challenge.actif is False


class TestFlagModel:
    """Tests pour le modèle Flag"""
    
    def test_flag_hashing(self, app, init_database):
        """Test du hashing de flag"""
        with app.app_context():
            data = init_database
            challenge = Challenge.query.get(data['challenge1'].id)
            
            flag = Flag(challenge_id=challenge.id)
            flag.setFlag("CTF{secret_flag}")
            
            db.session.add(flag)
            db.session.commit()
            
            # Le flag ne doit pas être stocké en clair
            assert flag.flag_hash != "CTF{secret_flag}"
            
            # Vérification du flag correct
            assert flag.verifierFlag("CTF{secret_flag}") is True
            assert flag.verifierFlag("CTF{wrong_flag}") is False
    
    def test_flag_verification(self, app, init_database):
        """Test de vérification de flag"""
        with app.app_context():
            data = init_database
            flag = Flag.query.get(data['flag1'].id)
            
            # Flag correct
            assert flag.verifierFlag("CTF{test_flag_1}") is True
            
            # Flags incorrects
            assert flag.verifierFlag("CTF{wrong}") is False
            assert flag.verifierFlag("") is False
            assert flag.verifierFlag("random_text") is False


class TestSubmissionModel:
    """Tests pour le modèle Submission"""
    
    def test_submission_creation(self, app, init_database):
        """Test de création d'une soumission"""
        with app.app_context():
            data = init_database
            
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            
            db.session.add(submission)
            db.session.commit()
            
            assert submission.id is not None
            assert submission.user_id == data['user1'].id
            assert submission.challenge_id == data['challenge1'].id
            assert submission.flag_soumis == "CTF{test_flag_1}"
    
    def test_submission_verification_correct(self, app, init_database):
        """Test de vérification d'une soumission correcte"""
        with app.app_context():
            data = init_database
            
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            
            # Vérifier et enregistrer
            result = submission.enregistrer()
            
            assert result is True
            assert submission.correct is True
    
    def test_submission_verification_incorrect(self, app, init_database):
        """Test de vérification d'une soumission incorrecte"""
        with app.app_context():
            data = init_database
            
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{wrong_flag}"
            )
            
            result = submission.enregistrer()
            
            assert result is False
            assert submission.correct is False
    
    def test_submission_updates_scoreboard(self, app, init_database):
        """Test que la soumission met à jour le scoreboard"""
        with app.app_context():
            data = init_database
            user = User.query.get(data['user1'].id)
            
            # Score initial
            initial_score = user.score
            assert initial_score == 0
            
            # Soumettre un flag correct
            submission = Submission(
                user_id=user.id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
            
            # Vérifier que le score a été mis à jour
            db.session.refresh(user)
            assert user.score == initial_score + 100
    
    def test_no_duplicate_points(self, app, init_database):
        """Test qu'on ne peut pas gagner des points plusieurs fois pour le même challenge"""
        with app.app_context():
            data = init_database
            user = User.query.get(data['user1'].id)
            
            # Première soumission correcte
            submission1 = Submission(
                user_id=user.id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            score_after_first = user.score
            
            # Deuxième soumission correcte du même challenge
            submission2 = Submission(
                user_id=user.id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission2.enregistrer()
            
            # Le score ne devrait pas changer
            db.session.refresh(user)
            assert user.score == score_after_first


class TestScoreboardModel:
    """Tests pour le modèle Scoreboard"""
    
    def test_scoreboard_creation(self, app, init_database):
        """Test de création d'un scoreboard"""
        with app.app_context():
            data = init_database
            scoreboard = Scoreboard.query.filter_by(user_id=data['user1'].id).first()
            
            assert scoreboard is not None
            assert scoreboard.user_id == data['user1'].id
            assert scoreboard.points_total == 0
    
    def test_calculer_score(self, app, init_database):
        """Test du calcul de score"""
        with app.app_context():
            data = init_database
            user_id = data['user1'].id
            
            # Ajouter des soumissions correctes
            submission1 = Submission(
                user_id=user_id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            submission2 = Submission(
                user_id=user_id,
                challenge_id=data['challenge2'].id,
                flag_soumis="CTF{test_flag_2}"
            )
            submission2.enregistrer()
            
            # Calculer le score
            total = Scoreboard.calculerScore(user_id)
            
            # 100 + 150 = 250
            assert total == 250
    
    def test_afficher_classement(self, app, init_database):
        """Test de l'affichage du classement"""
        with app.app_context():
            data = init_database
            
            # Donner des points à user1
            submission1 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            # Donner plus de points à user2
            submission2 = Submission(
                user_id=data['user2'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission2.enregistrer()
            
            submission3 = Submission(
                user_id=data['user2'].id,
                challenge_id=data['challenge2'].id,
                flag_soumis="CTF{test_flag_2}"
            )
            submission3.enregistrer()
            
            # Récupérer le classement
            classement = Scoreboard.afficherClassement(limit=10)
            
            # user2 devrait être premier (250 points)
            # user1 devrait être deuxième (100 points)
            assert len(classement) >= 2
            assert classement[0][1].id == data['user2'].id
            assert classement[1][1].id == data['user1'].id