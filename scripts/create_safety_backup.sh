#!/bin/bash
# ========================================
# SCRIPT DE BACKUP DE SÉCURITÉ COMPLET
# Crée un backup complet avant restauration
# ========================================

set -e

# Configuration
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
BACKUP_DIR="/opt/erp/backups"
APP_DIR="/opt/erp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="safety_backup_${TIMESTAMP}"

echo "💾 CRÉATION D'UN BACKUP DE SÉCURITÉ COMPLET"
echo "============================================"
echo "📅 Date : $(date '+%d/%m/%Y %H:%M:%S')"
echo ""

# Vérifier les privilèges
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

# Créer le répertoire de backup s'il n'existe pas
mkdir -p "$BACKUP_DIR"
echo "📁 Répertoire de backup : $BACKUP_DIR"
echo ""

# 1. Backup de la base de données
echo "🗄️  1/3 - Sauvegarde de la base de données..."
DB_BACKUP="${BACKUP_DIR}/${BACKUP_PREFIX}_database.sql"
sudo -u postgres pg_dump $DB_NAME > "$DB_BACKUP"
DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1)
echo "   ✅ Base de données sauvegardée : $DB_BACKUP ($DB_SIZE)"
echo ""

# 2. Backup des images produits
echo "🖼️  2/3 - Sauvegarde des images produits..."
IMAGES_DIR="${APP_DIR}/app/static/img/products"
IMAGES_BACKUP="${BACKUP_DIR}/${BACKUP_PREFIX}_images_produits.tar.gz"

if [ -d "$IMAGES_DIR" ]; then
    cd "$APP_DIR"
    tar -czf "$IMAGES_BACKUP" -C app/static/img products/
    IMAGES_SIZE=$(du -h "$IMAGES_BACKUP" | cut -f1)
    IMAGES_COUNT=$(find "$IMAGES_DIR" -type f | wc -l)
    echo "   ✅ Images sauvegardées : $IMAGES_BACKUP ($IMAGES_SIZE)"
    echo "   📊 Nombre d'images : $IMAGES_COUNT"
else
    echo "   ⚠️  Répertoire images non trouvé : $IMAGES_DIR"
fi
echo ""

# 3. Backup des autres fichiers statiques importants
echo "📦 3/3 - Sauvegarde des autres fichiers statiques..."
STATIC_BACKUP="${BACKUP_DIR}/${BACKUP_PREFIX}_static_files.tar.gz"
cd "$APP_DIR"
tar -czf "$STATIC_BACKUP" \
    app/static/img/logo-feemaison.png \
    app/static/img/cachet-feemaison.png \
    app/static/img/feemaison-logo-noir.png \
    app/static/contact.vcf \
    2>/dev/null || echo "   ⚠️  Certains fichiers statiques non trouvés"
STATIC_SIZE=$(du -h "$STATIC_BACKUP" 2>/dev/null | cut -f1 || echo "0")
echo "   ✅ Fichiers statiques sauvegardés : $STATIC_BACKUP ($STATIC_SIZE)"
echo ""

# Statistiques de la base avant backup
echo "📊 Statistiques de la base de données :"
PRODUCTS_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM products;" | tr -d ' ')
RECIPES_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM recipes;" | tr -d ' ')
ORDERS_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM orders;" | tr -d ' ')
echo "   📦 Produits : $PRODUCTS_COUNT"
echo "   📝 Recettes : $RECIPES_COUNT"
echo "   🛒 Commandes : $ORDERS_COUNT"
echo ""

# Résumé final
echo "✅ BACKUP DE SÉCURITÉ TERMINÉ"
echo "=============================="
echo ""
echo "📁 Fichiers créés :"
echo "   1. Base de données : $DB_BACKUP"
echo "   2. Images produits : $IMAGES_BACKUP"
echo "   3. Fichiers statiques : $STATIC_BACKUP"
echo ""
echo "💡 Pour restaurer ce backup plus tard :"
echo "   sudo -u postgres psql fee_maison_db < $DB_BACKUP"
echo "   tar -xzvf $IMAGES_BACKUP -C /"
echo "   tar -xzvf $STATIC_BACKUP -C /"
echo ""
echo "🔒 Backup sécurisé ! Tu peux maintenant restaurer le backup du 26/11 en toute sécurité."

