#!/bin/bash
# ========================================
# VÉRIFICATION RAPIDE PRÉ-DÉPLOIEMENT
# Vérifie que tout est prêt pour le déploiement
# ========================================

echo "🔍 Vérification Pré-Déploiement"
echo "================================"
echo ""

ERRORS=0

# Vérifier les fichiers essentiels
echo "📁 Vérification des fichiers..."
FILES=("wsgi.py" "requirements.txt" "config.py" "run.py")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file manquant"
        ERRORS=$((ERRORS + 1))
    fi
done

# Vérifier les dépendances critiques
echo ""
echo "📦 Vérification des dépendances..."
if grep -q "gunicorn" requirements.txt; then
    echo "  ✅ gunicorn"
else
    echo "  ❌ gunicorn manquant"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "psycopg2" requirements.txt; then
    echo "  ✅ psycopg2-binary"
else
    echo "  ❌ psycopg2-binary manquant"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "requests" requirements.txt; then
    echo "  ✅ requests"
else
    echo "  ❌ requests manquant"
    ERRORS=$((ERRORS + 1))
fi

# Vérifier les migrations
echo ""
echo "🗃️  Vérification des migrations..."
if [ -d "migrations" ]; then
    MIGRATION_COUNT=$(find migrations/versions -name "*.py" 2>/dev/null | wc -l)
    echo "  ✅ Dossier migrations trouvé ($MIGRATION_COUNT migrations)"
else
    echo "  ⚠️  Dossier migrations non trouvé (normal si première installation)"
fi

# Vérifier wsgi.py
echo ""
echo "🔧 Vérification wsgi.py..."
if grep -q "create_app" wsgi.py && grep -q "application" wsgi.py; then
    echo "  ✅ wsgi.py configuré correctement"
else
    echo "  ❌ wsgi.py mal configuré"
    ERRORS=$((ERRORS + 1))
fi

# Résumé
echo ""
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ Tout est prêt pour le déploiement !"
    exit 0
else
    echo "❌ $ERRORS erreur(s) détectée(s)"
    echo "💡 Corrigez les erreurs avant de déployer"
    exit 1
fi

