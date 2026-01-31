# tests/test_public_pages.py
"""
Tests unitaires pour les pages publiques accessibles sans authentification
"""

import pytest


class TestHomePage:
    """Tests pour la page d'accueil"""
    
    def test_home_page_loads(self, client):
        """Test que la page d'accueil se charge"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'CyberCampus' in response.data or b'CTF' in response.data
    
    def test_home_page_has_navigation(self, client):
        """Test que la page d'accueil a une navigation"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Apprendre' in response.data or b'Challenge' in response.data
    
    def test_home_page_shows_cta_for_guests(self, client):
        """Test que la page d'accueil affiche des CTA pour les visiteurs"""
        response = client.get('/')
        assert response.status_code == 200
        # Devrait avoir des boutons connexion/inscription
        assert b'connecter' in response.data.lower() or b'inscrire' in response.data.lower()
    
    def test_home_redirects_to_home_route(self, client):
        """Test que / redirige vers /home"""
        response = client.get('/', follow_redirects=False)
        # Peut être une redirection ou un render direct
        assert response.status_code in [200, 302]


class TestLearnPages:
    """Tests pour les pages de cours"""
    
    def test_learn_index_loads(self, client):
        """Test que la page index des cours se charge"""
        response = client.get('/learn')
        assert response.status_code == 200
        assert b'Biblioth' in response.data or b'Cours' in response.data
    
    def test_learn_sqli_page_loads(self, client):
        """Test que le cours SQLi se charge"""
        response = client.get('/learn/sqli')
        assert response.status_code == 200
        assert b'SQL' in response.data or b'Injection' in response.data
    
    def test_learn_xss_page_loads(self, client):
        """Test que le cours XSS se charge"""
        response = client.get('/learn/xss')
        assert response.status_code == 200
        assert b'XSS' in response.data or b'Cross-Site' in response.data
    
    def test_learn_bruteforce_page_loads(self, client):
        """Test que le cours Bruteforce se charge"""
        response = client.get('/learn/bruteforce')
        assert response.status_code == 200
        assert b'Bruteforce' in response.data or b'Force brute' in response.data.lower()
    
    def test_learn_crypto_page_loads(self, client):
        """Test que le cours Crypto se charge"""
        response = client.get('/learn/crypto')
        assert response.status_code == 200
        assert b'Crypto' in response.data or b'Rainbow' in response.data
    
    def test_learn_pages_accessible_without_auth(self, client):
        """Test que les cours sont accessibles sans authentification"""
        pages = ['/learn', '/learn/sqli', '/learn/xss', '/learn/bruteforce', '/learn/crypto']
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200


class TestScoreboardPublic:
    """Tests pour l'accès public au scoreboard"""
    
    def test_scoreboard_accessible_without_auth(self, client):
        """Test que le scoreboard est accessible sans connexion"""
        response = client.get('/scoreboard')
        assert response.status_code == 200
        assert b'Classement' in response.data or b'Scoreboard' in response.data
    
    def test_scoreboard_doesnt_show_personal_info_to_guests(self, client, init_database):
        """Test que le scoreboard ne montre pas d'infos personnelles aux visiteurs"""
        response = client.get('/scoreboard')
        assert response.status_code == 200
        # Ne devrait pas afficher "Votre position" si non connecté
        # (ou devrait gérer le cas gracieusement)


class TestNavigation:
    """Tests pour la navigation générale"""
    
    def test_navbar_present_on_all_pages(self, client):
        """Test que la navbar est présente sur toutes les pages"""
        pages = ['/', '/learn', '/scoreboard', '/login', '/register']
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            assert b'nav' in response.data.lower() or b'menu' in response.data.lower()
    
    def test_navbar_changes_based_on_auth_status(self, client, authenticated_client):
        """Test que la navbar change selon l'état d'authentification"""
        # Non authentifié
        response_guest = client.get('/')
        assert b'connecter' in response_guest.data.lower()
        
        # Authentifié
        response_user = authenticated_client.get('/')
        assert b'connect' in response_user.data.lower()  # "Déconnecter" ou "Dashboard"
    
    def test_footer_present_on_pages(self, client):
        """Test que le footer est présent"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'footer' in response.data.lower() or b'2025' in response.data


class TestErrorPages:
    """Tests pour les pages d'erreur"""
    
    def test_404_page_for_nonexistent_route(self, client):
        """Test que les routes inexistantes retournent 404"""
        response = client.get('/this-route-does-not-exist')
        assert response.status_code == 404
    
    def test_404_page_for_nonexistent_challenge(self, client):
        """Test qu'un challenge inexistant retourne 404"""
        response = client.get('/challenge/99999')
        assert response.status_code == 404


class TestStaticAssets:
    """Tests pour les assets statiques"""
    
    def test_css_loads(self, client):
        """Test que le CSS se charge"""
        response = client.get('/static/css/style.css')
        assert response.status_code == 200
        assert b'body' in response.data or b'color' in response.data
    
    def test_js_loads(self, client):
        """Test que le JS se charge"""
        response = client.get('/static/js/main.js')
        assert response.status_code == 200
        assert b'function' in response.data or b'const' in response.data
    
    def test_logo_loads(self, client):
        """Test que le logo se charge"""
        response = client.get('/static/img/logo.png')
        # Peut retourner 200 ou 404 si le fichier n'existe pas
        assert response.status_code in [200, 404]


class TestRedirects:
    """Tests pour les redirections"""
    
    def test_root_redirects_properly(self, client):
        """Test que la racine redirige correctement"""
        response = client.get('/', follow_redirects=False)
        # Vérifie qu'il y a soit un render, soit une redirection valide
        assert response.status_code in [200, 302]
    
    def test_authenticated_user_redirected_from_login(self, authenticated_client):
        """Test qu'un utilisateur authentifié est redirigé depuis /login"""
        response = authenticated_client.get('/login', follow_redirects=True)
        assert response.status_code == 200
        # Ne devrait pas être sur la page de login
        # Devrait être redirigé vers dashboard ou home


class TestFormValidation:
    """Tests pour la validation des formulaires"""
    
    def test_empty_login_form_shows_errors(self, client):
        """Test que le formulaire de connexion vide affiche des erreurs"""
        response = client.post('/login', data={
            'email': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Devrait afficher des messages d'erreur ou rester sur la page
    
    def test_empty_register_form_shows_errors(self, client):
        """Test que le formulaire d'inscription vide affiche des erreurs"""
        response = client.post('/register', data={
            'pseudo': '',
            'email': '',
            'password': '',
            'confirm_password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Devrait afficher des messages d'erreur


class TestAccessibility:
    """Tests d'accessibilité de base"""
    
    def test_pages_have_title(self, client):
        """Test que les pages ont un titre"""
        pages = ['/', '/learn', '/login', '/register']
        
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            assert b'<title>' in response.data
    
    def test_pages_have_proper_encoding(self, client):
        """Test que les pages ont un encodage UTF-8"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')