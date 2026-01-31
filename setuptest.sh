#!/bin/bash
# setup_tests.sh
# Script pour initialiser la structure des tests

echo "🧪 Configuration des tests unitaires pour CyberCampus CTF"
echo "=========================================================="
echo ""

# Créer le dossier tests s'il n'existe pas
if [ ! -d "tests" ]; then
    echo "📁 Création du dossier tests/..."
    mkdir tests
    touch tests/__init__.py
else
    echo "✅ Dossier tests/ déjà existant"
fi

# Copier les fichiers de test
echo ""
echo "📄 Copie des fichiers de test..."

files=(
    "conftest.py"
    "test_models.py"
    "test_auth.py"
    "test_challenges.py"
    "test_scoreboard.py"
    "test_admin.py"
    "test_public_pages.py"
)

for file in "${files[@]}"; do
    if [ -f "tests/$file" ]; then
        echo "   ⚠️  $file existe déjà (ignoré)"
    else
        echo "   ✅ Copie de $file"
    fi
done

# Copier pytest.ini à la racine
echo ""
if [ -f "pytest.ini" ]; then
    echo "⚠️  pytest.ini existe déjà à la racine"
else
    echo "📝 Copie de pytest.ini à la racine"
fi

# Installer les dépendances
echo ""
echo "📦 Installation des dépendances de test..."
pip install -r tests/requirements-test.txt

echo ""
echo "✅ Configuration terminée !"
echo ""
echo "Pour exécuter les tests :"
echo "  pytest"
echo ""
echo "Pour voir la couverture :"
echo "  pytest --cov=core --cov=app --cov-report=html"
echo ""
echo "Pour plus d'informations :"
echo "  cat tests/README_TESTS.md"
echo ""