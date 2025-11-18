#!/bin/bash

# Script de mise à jour automatique de la documentation ERP Fée Maison
# Version simple et robuste

echo "🚀 Mise à jour automatique de la documentation ERP Fée Maison"
echo "================================================================"
echo

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "../app/__init__.py" ]; then
    echo "❌ Erreur : Ce script doit être exécuté depuis le dossier scripts/"
    echo "📁 Répertoire actuel : $(pwd)"
    echo "💡 Utilisation : cd scripts && ./update_docs.sh"
    exit 1
fi

# Aller à la racine du projet
cd ..

# Vérifier que le dossier documentation existe
if [ ! -d "documentation" ]; then
    echo "❌ Erreur : Dossier 'documentation' non trouvé"
    exit 1
fi

echo "✅ Vérifications de base OK"
echo

# Créer une sauvegarde de la documentation actuelle
echo "📦 Création d'une sauvegarde..."
backup_dir="documentation_backup_$(date +%Y%m%d_%H%M%S)"
cp -r documentation "$backup_dir"
echo "✅ Sauvegarde créée : $backup_dir"
echo

# Exécuter le script Python de mise à jour
echo "🔧 Exécution du script de mise à jour..."
if python3 scripts/update_urls_documentation.py; then
    echo "✅ Script de mise à jour exécuté avec succès"
else
    echo "❌ Erreur lors de l'exécution du script"
    echo "🔄 Restauration de la sauvegarde..."
    rm -rf documentation
    mv "$backup_dir" documentation
    echo "✅ Documentation restaurée"
    exit 1
fi

echo
echo "📊 Résumé de la mise à jour :"
echo "=============================="

# Afficher les fichiers modifiés
echo "📝 Fichiers mis à jour :"
if [ -f "documentation/ARCHITECTURE_TECHNIQUE.md" ]; then
    echo "  ✅ ARCHITECTURE_TECHNIQUE.md"
fi
if [ -f "documentation/QUESTIONS_TEST_IA.md" ]; then
    echo "  ✅ QUESTIONS_TEST_IA.md"
fi

# Afficher les rapports générés
echo
echo "📋 Rapports générés :"
for report in documentation/RAPPORT_URLS_*.md; do
    if [ -f "$report" ]; then
        echo "  📊 $(basename "$report")"
    fi
done

echo
echo "🎯 Prochaines étapes :"
echo "======================"
echo "1. Vérifier les modifications dans la documentation"
echo "2. Tester avec une IA pour valider la compréhension"
echo "3. Commiter les changements si tout est OK"
echo "4. Supprimer la sauvegarde si plus nécessaire"
echo
echo "💡 Pour supprimer la sauvegarde : rm -rf $backup_dir"
echo
echo "✅ Mise à jour terminée avec succès ! 🚀" 