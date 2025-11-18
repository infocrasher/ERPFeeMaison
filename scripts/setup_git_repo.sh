#!/bin/bash
# ========================================
# SCRIPT D'INITIALISATION GIT
# Pour préparer le projet pour GitHub
# ========================================

set -e

echo "🔧 Configuration Git pour ERP Fée Maison"
echo "=========================================="
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "app/__init__.py" ]; then
    echo "❌ Ce script doit être exécuté depuis la racine du projet"
    exit 1
fi

# Vérifier Git
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé"
    echo "💡 Installez-le avec: xcode-select --install (macOS)"
    exit 1
fi

echo "✅ Git détecté: $(git --version)"
echo ""

# Vérifier si Git est déjà initialisé
if [ -d ".git" ]; then
    echo "ℹ️  Git est déjà initialisé"
    read -p "Voulez-vous continuer quand même ? (o/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        exit 0
    fi
else
    echo "📦 Initialisation de Git..."
    git init
    echo "✅ Git initialisé"
fi

# Créer .gitignore s'il n'existe pas
if [ ! -f ".gitignore" ]; then
    echo "📝 Création du fichier .gitignore..."
    cat > .gitignore << 'EOF'
# Environnement virtuel
venv/
env/
.venv/

# Fichiers Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Fichiers sensibles
.env
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/
*.log.*

# Fichiers système
.DS_Store
Thumbs.db
*.swp
*.swo

# IDE
.vscode/
.idea/
*.code-workspace

# Backups
*.sql
backups/
*.bak

# Fichiers temporaires
*.tmp
*.temp
.cache/

# Données historiques (optionnel - décommenter si trop volumineux)
# donnees_historiques*.csv
# Téléchargements Comptabilité/
EOF
    echo "✅ .gitignore créé"
else
    echo "ℹ️  .gitignore existe déjà"
fi

# Vérifier l'état
echo ""
echo "📊 État actuel du dépôt:"
git status --short | head -20

echo ""
echo "📋 PROCHAINES ÉTAPES :"
echo ""
echo "1. Vérifier les fichiers à ajouter :"
echo "   git status"
echo ""
echo "2. Ajouter tous les fichiers :"
echo "   git add ."
echo ""
echo "3. Faire le premier commit :"
echo "   git commit -m 'Initial commit - ERP Fée Maison'"
echo ""
echo "4. Créer un dépôt sur GitHub (github.com)"
echo ""
echo "5. Connecter le projet à GitHub :"
echo "   git remote add origin https://github.com/VOTRE_USERNAME/fee-maison-erp.git"
echo ""
echo "6. Pousser le code :"
echo "   git push -u origin main"
echo ""
echo "💡 Consultez documentation/GUIDE_DEPLOIEMENT_GIT_ETAPE_PAR_ETAPE.md pour les détails"

