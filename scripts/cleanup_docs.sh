#!/bin/bash

# Script de nettoyage pour les fichiers temporaires de documentation ERP Fée Maison

echo "🧹 Nettoyage des fichiers temporaires de documentation"
echo "======================================================"
echo

# Fonction pour demander confirmation
confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Fonction pour afficher les statistiques
show_stats() {
    local dir="$1"
    local pattern="$2"
    local count=$(find "$dir" -name "$pattern" 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        echo "  📊 $count fichier(s) trouvé(s)"
        find "$dir" -name "$pattern" 2>/dev/null | head -5 | sed 's/^/    - /'
        if [ $count -gt 5 ]; then
            echo "    ... et $((count - 5)) autres"
        fi
    else
        echo "  ✅ Aucun fichier trouvé"
    fi
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "../app/__init__.py" ]; then
    echo "❌ Erreur : Ce script doit être exécuté depuis le dossier scripts/"
    echo "📁 Répertoire actuel : $(pwd)"
    echo "💡 Utilisation : cd scripts && ./cleanup_docs.sh"
    exit 1
fi

# Aller à la racine du projet
cd ..

echo "📁 Répertoire actuel : $(pwd)"
echo

# 1. Nettoyage des sauvegardes de documentation
echo "1️⃣ Sauvegardes de documentation"
echo "-------------------------------"
show_stats "." "documentation_backup_*"

if confirm "Supprimer les sauvegardes de documentation ?"; then
    rm -rf documentation_backup_*
    echo "✅ Sauvegardes supprimées"
else
    echo "⏭️ Sauvegardes conservées"
fi
echo

# 2. Nettoyage des fichiers .backup dans documentation/
echo "2️⃣ Fichiers .backup dans documentation/"
echo "----------------------------------------"
show_stats "documentation" "*.backup"

if confirm "Supprimer les fichiers .backup ?"; then
    find documentation/ -name "*.backup" -delete 2>/dev/null
    echo "✅ Fichiers .backup supprimés"
else
    echo "⏭️ Fichiers .backup conservés"
fi
echo

# 3. Nettoyage des rapports anciens
echo "3️⃣ Rapports de mise à jour"
echo "---------------------------"
show_stats "documentation" "RAPPORT_URLS_*.md"

if confirm "Supprimer les rapports de mise à jour ?"; then
    rm -f documentation/RAPPORT_URLS_*.md
    echo "✅ Rapports supprimés"
else
    echo "⏭️ Rapports conservés"
fi
echo

# 4. Nettoyage des logs
echo "4️⃣ Fichiers de logs"
echo "-------------------"
show_stats "." "docs_update.log*"

if confirm "Supprimer les fichiers de logs ?"; then
    rm -f docs_update.log*
    echo "✅ Logs supprimés"
else
    echo "⏭️ Logs conservés"
fi
echo

# 5. Nettoyage des fichiers temporaires Python
echo "5️⃣ Fichiers temporaires Python"
echo "-------------------------------"
show_stats "." "*.pyc"
show_stats "." "__pycache__"

if confirm "Supprimer les fichiers temporaires Python ?"; then
    find . -name "*.pyc" -delete 2>/dev/null
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    echo "✅ Fichiers temporaires Python supprimés"
else
    echo "⏭️ Fichiers temporaires Python conservés"
fi
echo

# 6. Nettoyage des fichiers de test
echo "6️⃣ Fichiers de test temporaires"
echo "-------------------------------"
show_stats "." "test_*.py"
show_stats "." "*_test.py"

if confirm "Supprimer les fichiers de test temporaires ?"; then
    rm -f test_*.py *_test.py 2>/dev/null
    echo "✅ Fichiers de test supprimés"
else
    echo "⏭️ Fichiers de test conservés"
fi
echo

# Résumé final
echo "📊 Résumé du nettoyage"
echo "======================"

# Compter l'espace libéré (approximatif)
echo "📁 Espace disque :"
du -sh . 2>/dev/null | head -1

echo
echo "🎯 Prochaines étapes :"
echo "======================"
echo "1. Vérifier que la documentation est toujours fonctionnelle"
echo "2. Tester avec une IA pour valider"
echo "3. Commiter les changements si nécessaire"
echo "4. Exécuter scripts/update_docs.sh pour une nouvelle mise à jour"
echo

# Option pour exécuter la mise à jour
if confirm "Exécuter la mise à jour de la documentation maintenant ?"; then
    echo
    cd scripts && ./update_docs.sh
else
    echo "💡 Pour mettre à jour : cd scripts && ./update_docs.sh"
fi

echo
echo "✅ Nettoyage terminé ! 🧹" 