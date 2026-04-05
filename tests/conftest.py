"""
CyberCampus CTF — Fixtures de test centralisées
=================================================
Ce fichier fournit toutes les fixtures réutilisables pour la suite de tests :
- Application Flask configurée pour les tests (SQLite en mémoire)
- Client HTTP de test
- Utilisateurs (normal, admin, banni)
- Challenges avec flags
- Soumissions et scoreboard
"""

import pytest
import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from core import db as _db
from core.models import User, Challenge, Flag, Submission, Scoreboard, RssFeed


# ─────────────────────────────────────────────
# APPLICATION & BASE DE DONNÉES
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """Application Flask configurée pour les tests."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret-key-very-secure",
        "SERVER_NAME": "localhost",
        "LOGIN_DISABLED": False,
    })
    with flask_app.app_context():
        _db.create_all()
    yield flask_app
    with flask_app.app_context():
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Nettoie la base de données entre chaque test."""
    with app.app_context():
        # Supprimer dans l'ordre pour respecter les FK
        Submission.query.delete()
        Scoreboard.query.delete()
        Flag.query.delete()
        Challenge.query.delete()
        RssFeed.query.delete()
        User.query.delete()
        _db.session.commit()
    yield


@pytest.fixture()
def client(app):
    """Client HTTP de test Flask."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Session SQLAlchemy utilisable dans les tests."""
    with app.app_context():
        yield _db.session


# ─────────────────────────────────────────────
# UTILISATEURS
# ─────────────────────────────────────────────

@pytest.fixture()
def user(app):
    """Utilisateur standard."""
    with app.app_context():
        u = User(pseudo="testuser", email="test@example.com", role="user")
        u.set_password("password123")
        _db.session.add(u)
        _db.session.commit()
        _db.session.refresh(u)
        return u


@pytest.fixture()
def admin_user(app):
    """Utilisateur administrateur."""
    with app.app_context():
        u = User(pseudo="adminuser", email="admin@example.com", role="admin")
        u.set_password("adminpass123")
        _db.session.add(u)
        _db.session.commit()
        _db.session.refresh(u)
        return u


@pytest.fixture()
def banned_user(app):
    """Utilisateur banni."""
    with app.app_context():
        u = User(pseudo="banneduser", email="banned@example.com", role="banned")
        u.set_password("bannedpass123")
        _db.session.add(u)
        _db.session.commit()
        _db.session.refresh(u)
        return u


# ─────────────────────────────────────────────
# CHALLENGES & FLAGS
# ─────────────────────────────────────────────

@pytest.fixture()
def challenge_sqli(app):
    """Challenge SQL Injection avec flag."""
    with app.app_context():
        c = Challenge(id=1, titre="SQL Injection", description="Exploitez la faille SQLi",
                      points=25, actif=True)
        _db.session.add(c)
        _db.session.flush()
        f = Flag(challenge_id=c.id)
        f.setFlag("CTF{SQL_1nj3ct10n_m4st3r}")
        _db.session.add(f)
        _db.session.commit()
        _db.session.refresh(c)
        return c


@pytest.fixture()
def challenge_xss(app):
    """Challenge XSS avec flag."""
    with app.app_context():
        c = Challenge(id=2, titre="XSS Reflected", description="Exploitez le XSS",
                      points=25, actif=True)
        _db.session.add(c)
        _db.session.flush()
        f = Flag(challenge_id=c.id)
        f.setFlag("CTF{XSS_r3fl3ct3d_pwn3d}")
        _db.session.add(f)
        _db.session.commit()
        _db.session.refresh(c)
        return c


@pytest.fixture()
def challenge_bruteforce(app):
    """Challenge Bruteforce avec flag."""
    with app.app_context():
        c = Challenge(id=3, titre="Bruteforce", description="Trouvez le code",
                      points=175, actif=True)
        _db.session.add(c)
        _db.session.flush()
        f = Flag(challenge_id=c.id)
        f.setFlag("CTF{Brut3F0rc3_M4st3r_7394}")
        _db.session.add(f)
        _db.session.commit()
        _db.session.refresh(c)
        return c


@pytest.fixture()
def challenge_inactive(app):
    """Challenge désactivé."""
    with app.app_context():
        c = Challenge(id=99, titre="Inactif", description="Pas encore dispo",
                      points=50, actif=False)
        _db.session.add(c)
        _db.session.flush()
        f = Flag(challenge_id=c.id)
        f.setFlag("CTF{inactive}")
        _db.session.add(f)
        _db.session.commit()
        _db.session.refresh(c)
        return c


@pytest.fixture()
def all_challenges(challenge_sqli, challenge_xss, challenge_bruteforce):
    """Les 3 challenges principaux."""
    return [challenge_sqli, challenge_xss, challenge_bruteforce]


# ─────────────────────────────────────────────
# RSS FEEDS
# ─────────────────────────────────────────────

@pytest.fixture()
def rss_feed(app):
    """Flux RSS de test."""
    with app.app_context():
        feed = RssFeed(nom="CERT-FR Test", url="https://example.com/feed/",
                       actif=True, langue="FR")
        _db.session.add(feed)
        _db.session.commit()
        _db.session.refresh(feed)
        return feed


# ─────────────────────────────────────────────
# HELPERS DE CONNEXION
# ─────────────────────────────────────────────

@pytest.fixture()
def auth_client(client, user):
    """Client connecté en tant qu'utilisateur standard."""
    client.post("/login", data={"email": "test@example.com", "password": "password123"},
                follow_redirects=True)
    return client


@pytest.fixture()
def admin_client(client, admin_user):
    """Client connecté en tant qu'administrateur."""
    client.post("/login", data={"email": "admin@example.com", "password": "adminpass123"},
                follow_redirects=True)
    return client