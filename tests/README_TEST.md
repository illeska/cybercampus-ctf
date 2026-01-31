# 🧪 Tests Unitaires - CyberCampus CTF

Suite complète de tests unitaires avec base de données temporaire (isolation complète).

## 📋 Structure des Tests

```
tests/
├── conftest.py              # Configuration pytest & fixtures
├── test_models.py           # Tests des modèles (User, Challenge, Flag, etc.)
├── test_auth.py             # Tests d'authentification (login, register, logout)
├── test_challenges.py       # Tests des challenges et soumissions
├── test_scoreboard.py       # Tests du classement
├── test_admin.py            # Tests du panel administrateur
├── test_public_pages.py     # Tests des pages publiques
├── requirements-test.txt    # Dépendances de test
└── pytest.ini              # Configuration pytest
```

## 🚀 Installation

1. **Installer les dépendances de test** :
```bash
pip install -r tests/requirements-test.txt
```

2. **Vérifier l'installation** :
```bash
pytest --version
```

## ▶️ Exécution des Tests

### Tous les tests
```bash
pytest
```

### Tests avec couverture détaillée
```bash
pytest --cov=core --cov=app --cov-report=html --cov-report=term
```

### Tests spécifiques
```bash
# Un fichier spécifique
pytest tests/test_models.py

# Une classe spécifique
pytest tests/test_models.py::TestUserModel

# Un test spécifique
pytest tests/test_models.py::TestUserModel::test_user_creation
```

### Tests par catégorie
```bash
# Tests d'authentification
pytest tests/test_auth.py -v

# Tests admin
pytest tests/test_admin.py -v

# Tests des modèles
pytest tests/test_models.py -v
```

### Mode verbeux
```bash
pytest -v
```

### Afficher les prints
```bash
pytest -s
```

### Arrêter au premier échec
```bash
pytest -x
```

### Exécuter seulement les tests qui ont échoué
```bash
pytest --lf
```

## 📊 Rapport de Couverture

Après avoir exécuté les tests avec `--cov`, un rapport HTML est généré :
```bash
# Générer le rapport
pytest --cov=core --cov=app --cov-report=html

# Ouvrir le rapport dans le navigateur
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🔍 Ce qui est Testé

### ✅ Modèles de données (`test_models.py`)
- ✓ Création et validation des utilisateurs
- ✓ Hashing des mots de passe
- ✓ Calcul des scores
- ✓ Gestion des challenges
- ✓ Vérification des flags
- ✓ Enregistrement des soumissions
- ✓ Classement (scoreboard)
- ✓ Relations entre modèles

### ✅ Authentification (`test_auth.py`)
- ✓ Inscription (validation, doublons, etc.)
- ✓ Connexion (succès, échec, erreurs)
- ✓ Déconnexion
- ✓ Protection des routes
- ✓ Dashboard utilisateur
- ✓ Validation des formulaires

### ✅ Challenges (`test_challenges.py`)
- ✓ Liste des challenges actifs
- ✓ Vue détaillée d'un challenge
- ✓ Soumission de flags (correct/incorrect)
- ✓ Système de points
- ✓ Protection contre les points en double
- ✓ Système d'indices avec pénalités
- ✓ Statistiques des tentatives

### ✅ Scoreboard (`test_scoreboard.py`)
- ✓ Affichage du classement
- ✓ Tri par points décroissants
- ✓ Position de l'utilisateur
- ✓ Podium (Top 3)
- ✓ Limite à 100 utilisateurs
- ✓ Gestion des ex-aequo
- ✓ Mise à jour en temps réel

### ✅ Administration (`test_admin.py`)
- ✓ Contrôle d'accès (admin only)
- ✓ Dashboard avec statistiques
- ✓ Gestion des utilisateurs (ban, unban, reset)
- ✓ Gestion des challenges (edit, toggle)
- ✓ Visualisation des soumissions
- ✓ Export CSV
- ✓ Sécurité des routes admin

### ✅ Pages publiques (`test_public_pages.py`)
- ✓ Page d'accueil
- ✓ Bibliothèque de cours
- ✓ Navigation
- ✓ Pages d'erreur (404)
- ✓ Assets statiques (CSS, JS)
- ✓ Accessibilité de base

## 🗄️ Base de Données Temporaire

**Isolation complète** : Chaque test utilise sa propre base de données SQLite temporaire qui est **automatiquement détruite** après le test.

### Avantages
- ✅ **Aucun impact** sur la base de données de production
- ✅ **Tests parallélisables** (chaque test est indépendant)
- ✅ **Reproductibilité** (état initial identique pour chaque test)
- ✅ **Rapidité** (SQLite en mémoire)
- ✅ **Nettoyage automatique** (pas de données résiduelles)

### Comment ça marche
```python
# Chaque test reçoit une nouvelle base de données vierge
def test_example(app, client, init_database):
    # 'app' = Application Flask avec BDD temporaire
    # 'client' = Client de test
    # 'init_database' = Données de test pré-chargées
    
    # Après le test, la BDD est automatiquement supprimée
```

## 📈 Fixtures Disponibles

### `app`
Application Flask configurée pour les tests avec BDD temporaire

### `client`
Client HTTP de test Flask

### `runner`
Runner CLI de test

### `init_database`
Base de données pré-peuplée avec :
- 3 utilisateurs (user1, user2, admin)
- 3 challenges (2 actifs, 1 inactif)
- 3 flags correspondants
- Scoreboards initialisés

### `authenticated_client`
Client déjà authentifié en tant qu'utilisateur normal

### `admin_client`
Client déjà authentifié en tant qu'administrateur

## 🎯 Commandes Utiles

### Exécuter les tests en continu (watch mode)
```bash
pytest-watch
```

### Tests avec temps d'exécution
```bash
pytest --durations=10
```

### Tests avec parallélisation (plus rapide)
```bash
pip install pytest-xdist
pytest -n auto
```

### Nettoyer les caches
```bash
pytest --cache-clear
```

## 📝 Écrire de Nouveaux Tests

### Template de base
```python
# tests/test_example.py
import pytest
from core.models import User

class TestFeature:
    """Tests pour une fonctionnalité"""
    
    def test_something(self, app, client, init_database):
        """Test que quelque chose fonctionne"""
        # Arrange (préparer)
        with app.app_context():
            data = init_database
            user = User.query.get(data['user1'].id)
        
        # Act (agir)
        response = client.post('/some-route', data={
            'field': 'value'
        })
        
        # Assert (vérifier)
        assert response.status_code == 200
        assert b'expected content' in response.data
```

## ⚠️ Notes Importantes

1. **CSRF désactivé** : Les tests désactivent automatiquement la protection CSRF
2. **Mode TEST** : L'application est en mode `TESTING=True`
3. **Isolation** : Chaque test est complètement isolé des autres
4. **Nettoyage** : Les bases de données temporaires sont automatiquement supprimées
5. **Pas de side effects** : Les tests ne modifient jamais la BDD de production

## 🐛 Dépannage

### "No module named 'app'"
```bash
# S'assurer d'être à la racine du projet
cd /path/to/cybercampus-ctf
pytest
```

### "Database is locked"
```bash
# Supprimer les fichiers de cache
rm -rf .pytest_cache
rm -rf __pycache__
```

### Tests qui échouent de manière aléatoire
```bash
# Exécuter les tests séquentiellement
pytest --maxfail=1
```

## 📊 Couverture de Code Attendue

| Module | Couverture | Statut |
|--------|-----------|--------|
| `core/models.py` | > 90% | ✅ |
| `core/auth.py` | > 85% | ✅ |
| `core/admin.py` | > 80% | ✅ |
| `app.py` | > 75% | ✅ |

## 🚦 CI/CD

Pour intégrer dans un pipeline CI/CD :

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install -r tests/requirements-test.txt
      - run: pytest --cov --cov-report=xml
```

## 📚 Ressources

- [Documentation Pytest](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Pytest-Flask](https://pytest-flask.readthedocs.io/)

---

**Bon test ! 🧪**