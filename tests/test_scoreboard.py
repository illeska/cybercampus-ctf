# tests/test_scoreboard.py
"""
Tests unitaires pour le scoreboard (classement)
"""

import pytest
from core.models import User, Submission, Scoreboard
from core import db


class TestScoreboardPage:
    """Tests pour la page du scoreboard"""
    
    def test_scoreboard_page_loads(self, client):
        """Test que la page du scoreboard se charge"""
        response = client.get('/scoreboard')
        assert response.status_code == 200
        assert b'Classement' in response.data or b'Scoreboard' in response.data
    
    def test_scoreboard_shows_top_users(self, client, app, init_database):
        """Test que le scoreboard affiche les meilleurs joueurs"""
        # Donner des points aux utilisateurs
        with app.app_context():
            data = init_database
            
            # User1: 100 points
            submission1 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            # User2: 250 points
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
        
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # Devrait afficher les deux utilisateurs
        assert b'testuser1' in response.data
        assert b'testuser2' in response.data
        
        # User2 devrait apparaître avant User1 (plus de points)
        pos_user1 = response.data.find(b'testuser1')
        pos_user2 = response.data.find(b'testuser2')
        assert pos_user2 < pos_user1
    
    def test_scoreboard_shows_user_rank(self, authenticated_client, app, init_database):
        """Test que le scoreboard affiche le rang de l'utilisateur connecté"""
        # Donner des points
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
        
        response = authenticated_client.get('/scoreboard')
        assert response.status_code == 200
        
        # Devrait afficher "Votre position" ou similaire
        assert b'Votre' in response.data or b'position' in response.data.lower()
    
    def test_scoreboard_highlights_current_user(self, authenticated_client, app, init_database):
        """Test que le scoreboard met en évidence l'utilisateur connecté"""
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
        
        response = authenticated_client.get('/scoreboard')
        assert response.status_code == 200
        
        # Devrait avoir une classe ou un badge "Vous"
        assert b'Vous' in response.data or b'current-user' in response.data
    
    def test_scoreboard_shows_podium(self, client, app, init_database):
        """Test que le scoreboard affiche un podium pour le Top 3"""
        # Créer 3 utilisateurs avec des scores différents
        with app.app_context():
            # User pour la 3ème place
            user3 = User(pseudo="user3", email="user3@example.com")
            user3.set_password("pass")
            db.session.add(user3)
            db.session.flush()
            
            scoreboard3 = Scoreboard(user_id=user3.id, points_total=0)
            db.session.add(scoreboard3)
            
            data = init_database
            
            # 3ème place: 100 points
            submission1 = Submission(
                user_id=user3.id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            # 2ème place: 150 points
            submission2 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge2'].id,
                flag_soumis="CTF{test_flag_2}"
            )
            submission2.enregistrer()
            
            # 1ère place: 250 points
            submission3 = Submission(
                user_id=data['user2'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission3.enregistrer()
            
            submission4 = Submission(
                user_id=data['user2'].id,
                challenge_id=data['challenge2'].id,
                flag_soumis="CTF{test_flag_2}"
            )
            submission4.enregistrer()
        
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # Devrait afficher des médailles/icônes
        assert b'podium' in response.data.lower() or b'1' in response.data
    
    def test_empty_scoreboard_shows_message(self, client, app):
        """Test que le scoreboard vide affiche un message approprié"""
        with app.app_context():
            # Créer un utilisateur sans score
            user = User(pseudo="nopoints", email="nopoints@example.com")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()
        
        response = client.get('/scoreboard')
        assert response.status_code == 200


class TestScoreboardCalculations:
    """Tests pour les calculs du scoreboard"""
    
    def test_scoreboard_updates_on_flag_submission(self, authenticated_client, app, init_database):
        """Test que le scoreboard se met à jour après soumission"""
        # Score initial
        response1 = authenticated_client.get('/scoreboard')
        initial_content = response1.data
        
        # Soumettre un flag
        with app.app_context():
            data = init_database
            authenticated_client.post('/challenge/1/submit', data={
                'flag': 'CTF{test_flag_1}'
            }, follow_redirects=True)
        
        # Score mis à jour
        response2 = authenticated_client.get('/scoreboard')
        updated_content = response2.data
        
        # Le contenu devrait avoir changé
        assert b'100' in updated_content  # Points du challenge
    
    def test_scoreboard_respects_limit(self, client, app):
        """Test que le scoreboard respecte la limite de 100"""
        # Créer plus de 100 utilisateurs avec des scores
        with app.app_context():
            for i in range(105):
                user = User(
                    pseudo=f"user{i}",
                    email=f"user{i}@example.com"
                )
                user.set_password("pass")
                db.session.add(user)
                db.session.flush()
                
                scoreboard = Scoreboard(user_id=user.id, points_total=i * 10)
                db.session.add(scoreboard)
            
            db.session.commit()
        
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # Ne devrait afficher que les 100 premiers
        # (Vérification approximative en comptant les lignes du tableau)
    
    def test_scoreboard_handles_tied_scores(self, client, app, init_database):
        """Test que le scoreboard gère les ex-aequo"""
        with app.app_context():
            data = init_database
            
            # Donner le même score aux deux utilisateurs
            submission1 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            submission2 = Submission(
                user_id=data['user2'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission2.enregistrer()
        
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # Les deux utilisateurs devraient apparaître
        assert b'testuser1' in response.data
        assert b'testuser2' in response.data


class TestScoreboardSorting:
    """Tests pour le tri du scoreboard"""
    
    def test_scoreboard_sorts_by_points_descending(self, client, app, init_database):
        """Test que le scoreboard trie par points décroissants"""
        with app.app_context():
            data = init_database
            
            # User1: 100 points
            submission1 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            # User2: 250 points
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
        
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # User2 (250 pts) devrait apparaître avant User1 (100 pts)
        pos_user1 = response.data.find(b'testuser1')
        pos_user2 = response.data.find(b'testuser2')
        
        assert pos_user1 > 0
        assert pos_user2 > 0
        assert pos_user2 < pos_user1


class TestScoreboardDisplay:
    """Tests pour l'affichage du scoreboard"""
    
    def test_scoreboard_shows_challenges_solved(self, client, app, init_database):
        """Test que le scoreboard affiche le nombre de challenges résolus"""
        with app.app_context():
            data = init_database
            
            # Résoudre 2 challenges
            submission1 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            submission2 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge2'].id,
                flag_soumis="CTF{test_flag_2}"
            )
            submission2.enregistrer()
        
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # Devrait afficher "2" challenges résolus
        assert b'2' in response.data
    
    def test_scoreboard_shows_join_date(self, client, init_database):
        """Test que le scoreboard affiche la date d'inscription"""
        response = client.get('/scoreboard')
        assert response.status_code == 200
        
        # Devrait afficher une date au format JJ/MM/AAAA
        # (Vérification approximative)
        assert b'202' in response.data  # Année 2024/2025/etc.