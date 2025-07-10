#!/bin/bash

# Script de nettoyage du projet ERP Fée Maison
# Supprime les fichiers inutiles pour le déploiement

echo "🧹 Nettoyage du projet ERP Fée Maison"
echo "====================================="

# Compteur de fichiers supprimés
count=0

# Fonction pour supprimer un fichier s'il existe
remove_file() {
    if [ -f "$1" ]; then
        echo "🗑️  Suppression: $1"
        rm -f "$1"
        ((count++))
    fi
}

# Fonction pour supprimer un dossier s'il existe
remove_dir() {
    if [ -d "$1" ]; then
        echo "🗑️  Suppression dossier: $1"
        rm -rf "$1"
        ((count++))
    fi
}

echo "📋 Suppression des fichiers de sauvegarde..."
# Fichiers de sauvegarde SQL (très volumineux)
remove_file "backup_code_source_20250704_033326.tar.gz"
remove_file "backup_erp_complet_20250704_032915.sql"
remove_file "backup_dashboard_comptabilite_20250704_021301.sql"
remove_file "backup_before_deliveryman_workflow_20250703_013346.sql"
remove_file "backup_before_reset_2025-06-26.sql"
remove_file "backup_before_stock_migration.sql"
remove_file "backup_20250615.sql"
remove_file "backup_fee_maison_20250611.sql"
remove_file "app_sqlite.db.backup"

echo "📄 Suppression des fichiers de documentation énormes..."
remove_file "cursor_discussing_project_erp_updates.md"

echo "💾 Suppression des fichiers de sauvegarde HTML..."
remove_file "view_employee_backup.html"
remove_file "employee_analytics_backup.html"

echo "🖼️  Suppression des fichiers d'erreur/debug..."
remove_file "order_creation_error_1751415651.png"
remove_file "order_creation_error_1751415587.png"
remove_file "order_creation_error_1751415505.png"
remove_file "login_error_1751414334.png"

echo "🧪 Suppression des fichiers de test/diagnostic..."
remove_file "test_all_endpoints_and_suggest.py"
remove_file "run_diagnostics.py"
remove_file "diagnostic_url_for.py"
remove_file "test_endpoints.py"

echo "🛠️  Suppression des fichiers de développement..."
remove_file "generate_erp_core_architecture_Version.py"
remove_file "structure.txt"

echo "💻 Suppression des fichiers système..."
remove_file ".DS_Store"
remove_file "fee_maison_db"

echo "🗂️  Suppression des dossiers temporaires..."
remove_dir "__pycache__"
remove_dir ".pytest_cache"

echo ""
echo "✅ Nettoyage terminé !"
echo "📊 $count fichiers/dossiers supprimés"
echo ""
echo "📋 Fichiers conservés (comme demandé) :"
echo "   ✅ ERP_MEMO.md"
echo "   ✅ ERP_CORE_ARCHITECTURE.md"
echo "   ✅ Save_Project.py"
echo ""
echo "🚀 Projet prêt pour le déploiement !" 