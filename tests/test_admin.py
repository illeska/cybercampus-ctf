# tests/test_admin.py
"""
Tests unitaires pour le panel administrateur
"""

import pytest
from core.models import User, Challenge, Submission
from core import db


class TestAdminAccess:
    """Tests pour l'accès au panel admin"""
    
    def test_admin_dashboard_requires_login(self, client):
        """Test que le dashboard admin nécessite une connexion"""
        response = client.get('/admin/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Connexion' in response.data or b'login' in response.data.lower()
    
    def test_admin_dashboard_requires_admin_role(self, authenticated_client):
        """Test que le dashboard admin nécessite le rôle admin"""
        response = authenticated_client.get('/admin/', follow_redirects=True)
        assert response.status_code == 200
        # Devrait afficher un message d'accès refusé ou rediriger
        assert b'refus' in response.data.lower() or b'admin' in response.data.lower()
    
    def test_admin_dashboard_accessible_to_admin(self, admin_client):
        """Test que le dashboard admin est accessible aux admins"""
        response = admin_client.get('/admin/')
        assert response.status_code == 200
        assert b'Admin' in response.data or b'Panel' in response.data
    
    def test_regular_user_cannot_access_admin_routes(self, authenticated_client):
        """Test qu'un utilisateur normal ne peut pas accéder aux routes admin"""
        routes = [
            '/admin/',
            '/admin/users',
            '/admin/challenges',
            '/admin/submissions'
        ]
        
        for route in routes:
            response = authenticated_client.get(route, follow_redirects=True)
            assert response.status_code == 200
            # Ne devrait pas afficher le contenu admin


class TestAdminDashboard:
    """Tests pour le dashboard administrateur"""
    
    def test_admin_dashboard_shows_statistics(self, admin_client, init_database):
        """Test que le dashboard affiche les statistiques"""
        response = admin_client.get('/admin/')
        assert response.status_code == 200
        
        # Devrait afficher le nombre d'utilisateurs, challenges, etc.
        assert b'Utilisateur' in response.data or b'utilisateur' in response.data
        assert b'Challenge' in response.data or b'challenge' in response.data
    
    def test_admin_dashboard_shows_recent_activity(self, admin_client, app, init_database):
        """Test que le dashboard affiche l'activité récente"""
        # Créer de l'activité
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
        
        response = admin_client.get('/admin/')
        assert response.status_code == 200
        
        # Devrait afficher les dernières soumissions
        assert b'Soumission' in response.data or b'soumission' in response.data


class TestAdminUsers:
    """Tests pour la gestion des utilisateurs"""
    
    def test_admin_can_view_users_list(self, admin_client, init_database):
        """Test que l'admin peut voir la liste des utilisateurs"""
        response = admin_client.get('/admin/users')
        assert response.status_code == 200
        
        assert b'testuser1' in response.data
        assert b'testuser2' in response.data
        assert b'admin' in response.data
    
    def test_admin_can_ban_user(self, admin_client, app, init_database):
        """Test que l'admin peut bannir un utilisateur"""
        with app.app_context():
            data = init_database
            user_id = data['user1'].id
        
        response = admin_client.post(
            f'/admin/users/{user_id}/ban',
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Vérifier que l'utilisateur est banni
        with app.app_context():
            user = User.query.get(user_id)
            assert user.role == "banned"
    
    def test_admin_can_unban_user(self, admin_client, app, init_database):
        """Test que l'admin peut débannir un utilisateur"""
        with app.app_context():
            data = init_database
            user = User.query.get(data['user1'].id)
            user.role = "banned"
            db.session.commit()
            user_id = user.id
        
        response = admin_client.post(
            f'/admin/users/{user_id}/ban',
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Vérifier que l'utilisateur est débanni
        with app.app_context():
            user = User.query.get(user_id)
            assert user.role == "user"
    
    def test_admin_cannot_ban_themselves(self, admin_client, app, init_database):
        """Test que l'admin ne peut pas se bannir lui-même"""
        with app.app_context():
            admin = User.query.filter_by(email='admin@example.com').first()
            admin_id = admin.id
        
        response = admin_client.post(
            f'/admin/users/{admin_id}/ban',
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Devrait afficher un message d'erreur
        assert b'vous-m' in response.data.lower() or b'bannir' in response.data.lower()
        
        # L'admin devrait toujours être admin
        with app.app_context():
            admin = User.query.get(admin_id)
            assert admin.role == "admin"
    
    def test_admin_can_reset_user_score(self, admin_client, app, init_database):
        """Test que l'admin peut réinitialiser le score d'un utilisateur"""
        # Donner des points à l'utilisateur
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
            user_id = data['user1'].id
        
        # Vérifier que l'utilisateur a des points
        with app.app_context():
            user = User.query.get(user_id)
            assert user.score > 0
        
        # Réinitialiser le score
        response = admin_client.post(
            f'/admin/users/{user_id}/reset_score',
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Vérifier que le score est à 0
        with app.app_context():
            user = User.query.get(user_id)
            assert user.score == 0


class TestAdminChallenges:
    """Tests pour la gestion des challenges"""
    
    def test_admin_can_view_challenges_list(self, admin_client, init_database):
        """Test que l'admin peut voir la liste des challenges"""
        response = admin_client.get('/admin/challenges')
        assert response.status_code == 200
        
        assert b'Test SQL Injection' in response.data
        assert b'Test XSS' in response.data
    
    def test_admin_can_toggle_challenge_status(self, admin_client, app, init_database):
        """Test que l'admin peut activer/désactiver un challenge"""
        with app.app_context():
            data = init_database
            challenge = Challenge.query.get(data['challenge1'].id)
            initial_status = challenge.actif
            challenge_id = challenge.id
        
        response = admin_client.post(
            f'/admin/challenges/{challenge_id}/toggle',
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Vérifier que le statut a changé
        with app.app_context():
            challenge = Challenge.query.get(challenge_id)
            assert challenge.actif != initial_status
    
    def test_admin_can_edit_challenge(self, admin_client, app, init_database):
        """Test que l'admin peut modifier un challenge"""
        with app.app_context():
            data = init_database
            challenge_id = data['challenge1'].id
        
        response = admin_client.post(
            f'/admin/challenges/{challenge_id}/edit',
            data={
                'titre': 'Challenge Modifié',
                'description': 'Nouvelle description',
                'points': 200
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Vérifier que le challenge a été modifié
        with app.app_context():
            challenge = Challenge.query.get(challenge_id)
            assert challenge.titre == 'Challenge Modifié'
            assert challenge.points == 200
    
    def test_admin_can_update_flag(self, admin_client, app, init_database):
        """Test que l'admin peut modifier le flag d'un challenge"""
        with app.app_context():
            data = init_database
            challenge_id = data['challenge1'].id
        
        response = admin_client.post(
            f'/admin/challenges/{challenge_id}/edit',
            data={
                'titre': 'Test Challenge',
                'description': 'Description',
                'points': 100,
                'flag': 'CTF{new_flag}'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Vérifier que le flag a été mis à jour
        with app.app_context():
            challenge = Challenge.query.get(challenge_id)
            assert challenge.flag.verifierFlag('CTF{new_flag}')


class TestAdminSubmissions:
    """Tests pour la visualisation des soumissions"""
    
    def test_admin_can_view_submissions(self, admin_client, app, init_database):
        """Test que l'admin peut voir les soumissions"""
        # Créer des soumissions
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
        
        response = admin_client.get('/admin/submissions')
        assert response.status_code == 200
        
        assert b'testuser1' in response.data
        assert b'Test SQL Injection' in response.data
    
    def test_admin_can_filter_submissions(self, admin_client, app, init_database):
        """Test que l'admin peut filtrer les soumissions"""
        # Créer des soumissions correctes et incorrectes
        with app.app_context():
            data = init_database
            
            submission1 = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission1.enregistrer()
            
            submission2 = Submission(
                user_id=data['user2'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{wrong_flag}"
            )
            submission2.enregistrer()
        
        # Filtrer les soumissions correctes
        response = admin_client.get('/admin/submissions?status=correct')
        assert response.status_code == 200
        
        # Devrait afficher uniquement les soumissions correctes


class TestAdminExport:
    """Tests pour l'export de données"""
    
    def test_admin_can_export_scoreboard(self, admin_client, app, init_database):
        """Test que l'admin peut exporter le scoreboard en CSV"""
        # Créer des scores
        with app.app_context():
            data = init_database
            submission = Submission(
                user_id=data['user1'].id,
                challenge_id=data['challenge1'].id,
                flag_soumis="CTF{test_flag_1}"
            )
            submission.enregistrer()
        
        response = admin_client.get('/admin/export')
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        
        # Vérifier que le CSV contient les données
        assert b'testuser1' in response.data
        assert b'100' in response.data  # Score


class TestAdminSecurity:
    """Tests de sécurité pour le panel admin"""
    
    def test_banned_user_cannot_access_admin(self, client, app, init_database):
        """Test qu'un utilisateur banni ne peut pas accéder au panel admin"""
        with app.app_context():
            # Créer un admin banni (cas extrême)
            admin = User(pseudo="bannedadmin", email="banned@example.com", role="banned")
            admin.set_password("pass")
            db.session.add(admin)
            db.session.commit()
        
        # Se connecter
        client.post('/login', data={
            'email': 'banned@example.com',
            'password': 'pass'
        }, follow_redirects=True)
        
        # Essayer d'accéder au panel admin
        response = client.get('/admin/', follow_redirects=True)
        assert response.status_code == 200
        # Ne devrait pas avoir accès
    
    def test_admin_routes_use_post_for_modifications(self, admin_client, init_database):
        """Test que les modifications utilisent POST (pas GET)"""
        with app.app_context():
            data = init_database
            user_id = data['user1'].id
        
        # Essayer de bannir avec GET (devrait échouer)
        response = admin_client.get(f'/admin/users/{user_id}/ban')
        assert response.status_code == 405  # Method Not Allowed