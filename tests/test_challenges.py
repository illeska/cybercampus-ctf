# tests/test_challenges.py
"""
Tests unitaires pour les challenges et la soumission de flags
"""

import pytest
from flask import session
from core.models import Challenge, Submission, Scoreboard, User
from core import db


class TestChallengesList:
    """Tests pour la liste des challenges"""
    
    def test_challenges_list_shows_active_challenges(self, authenticated_client, init_database):
        """Test que la liste affiche uniquement les challenges actifs"""
        response = authenticated_client.get('/challenges')
        assert response.status_code == 200
        
        # Devrait afficher les challenges actifs
        assert b'Test SQL Injection' in response.data
        assert b'Test XSS' in response.data
        
        # Ne devrait PAS afficher le challenge inactif
        assert b'Challenge Inactif' not in response.data
    
    def test_challenges_list_shows_solved_status(self, authenticated_client, app, init_database):
        """Test que la liste affiche le statut résolu"""
        # Résoudre un challenge
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
        
        response = authenticated_client.get('/challenges')
        assert response.status_code == 200
        # Devrait afficher un indicateur de challenge résolu
        # (badge, checkmark, etc.)


class TestChallengeView:
    """Tests pour la vue détaillée d'un challenge"""
    
    def test_challenge_view_loads(self, authenticated_client, init_database):
        """Test que la vue d'un challenge se charge"""
        response = authenticated_client.get('/challenge/1')
        assert response.status_code == 200
        assert b'Test SQL Injection' in response.data
        assert b'Challenge de test pour SQLi' in response.data
    
    def test_challenge_view_shows_points(self, authenticated_client, init_database):
        """Test que la vue affiche les points"""
        response = authenticated_client.get('/challenge/1')
        assert response.status_code == 200
        assert b'100' in response.data  # Points du challenge
    
    def test_inactive_challenge_redirects(self, authenticated_client, init_database):
        """Test qu'un challenge inactif redirige"""
        response = authenticated_client.get('/challenge/3', follow_redirects=True)
        assert response.status_code == 200
        # Devrait afficher un message d'avertissement
        assert b'disponible' in response.data or b'actif' in response.data.lower()
    
    def test_nonexistent_challenge_returns_404(self, authenticated_client):
        """Test qu'un challenge inexistant retourne 404"""
        response = authenticated_client.get('/challenge/999')
        assert response.status_code == 404


class TestFlagSubmission:
    """Tests pour la soumission de flags"""
    
    def test_submit_correct_flag(self, authenticated_client, app, init_database):
        """Test de soumission d'un flag correct"""
        response = authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Bravo' in response.data or b'correct' in response.data.lower()
        
        # Vérifier que le score a été mis à jour
        with app.app_context():
            user = User.query.filter_by(email='test1@example.com').first()
            assert user.score == 100
    
    def test_submit_incorrect_flag(self, authenticated_client, app, init_database):
        """Test de soumission d'un flag incorrect"""
        response = authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{wrong_flag}'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'incorrect' in response.data.lower() or b'essayez' in response.data.lower()
        
        # Le score ne devrait pas changer
        with app.app_context():
            user = User.query.filter_by(email='test1@example.com').first()
            assert user.score == 0
    
    def test_submit_empty_flag(self, authenticated_client, init_database):
        """Test de soumission d'un flag vide"""
        response = authenticated_client.post('/challenge/1/submit', data={
            'flag': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Devrait afficher une erreur
    
    def test_cannot_get_double_points(self, authenticated_client, app, init_database):
        """Test qu'on ne peut pas gagner des points deux fois pour le même challenge"""
        # Première soumission
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        with app.app_context():
            user = User.query.filter_by(email='test1@example.com').first()
            score_after_first = user.score
        
        # Deuxième soumission du même flag
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        with app.app_context():
            user = User.query.filter_by(email='test1@example.com').first()
            # Le score ne devrait pas avoir changé
            assert user.score == score_after_first
    
    def test_submit_flag_creates_submission_record(self, authenticated_client, app, init_database):
        """Test que la soumission crée un enregistrement"""
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        with app.app_context():
            data = init_database
            submissions = Submission.query.filter_by(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id
            ).all()
            
            assert len(submissions) >= 1
            assert submissions[-1].flag_soumis == 'CTF{test_flag_1}'
            assert submissions[-1].correct is True
    
    def test_submit_flag_requires_authentication(self, client, init_database):
        """Test que la soumission nécessite une authentification"""
        response = client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Devrait rediriger vers login
        assert b'Connexion' in response.data or b'login' in response.data.lower()


class TestHintsSystem:
    """Tests pour le système d'indices"""
    
    def test_reveal_hint_reduces_points(self, authenticated_client, app, init_database):
        """Test que révéler un indice réduit les points"""
        # Révéler un indice
        response = authenticated_client.post('/challenge/1/hint/0')
        assert response.status_code == 200
        
        # Soumettre le flag correct après avoir révélé l'indice
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        with app.app_context():
            user = User.query.filter_by(email='test1@example.com').first()
            # Le score devrait être réduit (100 - 10% = 90)
            assert user.score == 90
    
    def test_cannot_reveal_same_hint_twice(self, authenticated_client, init_database):
        """Test qu'on ne peut pas révéler le même indice deux fois"""
        # Première révélation
        response1 = authenticated_client.post('/challenge/1/hint/0')
        assert response1.status_code == 200
        
        # Deuxième tentative
        response2 = authenticated_client.post('/challenge/1/hint/0')
        data = response2.get_json()
        
        assert 'error' in data or response2.status_code == 400
    
    def test_hints_are_sequential(self, authenticated_client, init_database):
        """Test que les indices sont séquentiels"""
        # Essayer de révéler l'indice 2 sans avoir révélé l'indice 1
        # (si applicable selon la logique)
        response = authenticated_client.post('/challenge/1/hint/2')
        
        # Le comportement dépend de votre implémentation
        # Ajustez selon vos règles métier


class TestChallengeStatistics:
    """Tests pour les statistiques des challenges"""
    
    def test_challenge_tracks_attempts(self, authenticated_client, app, init_database):
        """Test que les tentatives sont enregistrées"""
        # Plusieurs tentatives
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{wrong1}'
        }, follow_redirects=True)
        
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{wrong2}'
        }, follow_redirects=True)
        
        authenticated_client.post('/challenge/1/submit', data={
            'flag': 'CTF{test_flag_1}'
        }, follow_redirects=True)
        
        with app.app_context():
            data = init_database
            attempts = Submission.query.filter_by(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id
            ).count()
            
            assert attempts == 3