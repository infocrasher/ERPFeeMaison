#!/bin/bash
# ========================================
# SCRIPT DE RESTAURATION DEPUIS BACKUP
# Restaure la base et les images depuis un backup
# ========================================

set -e

# Configuration
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
SERVICE_NAME="erp-fee-maison"
BACKUP_DIR="/opt/erp/backups"

echo "🔄 RESTAURATION DEPUIS BACKUP"
echo "=============================="
echo ""

# Vérifier les privilèges
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

# Lister les backups disponibles
echo "📋 Backups disponibles dans $BACKUP_DIR :"
echo ""
ls -lh $BACKUP_DIR/*.sql 2>/dev/null | tail -10 || echo "Aucun backup .sql trouvé"
echo ""

read -p "📁 Entrez le nom du fichier de backup SQL (ex: backup_20251126_011209.sql) : " BACKUP_FILE

# Chercher le fichier dans plusieurs emplacements possibles
BACKUP_PATH=""
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"
elif [ -f "/opt/erp/app/$BACKUP_FILE" ]; then
    BACKUP_PATH="/opt/erp/app/$BACKUP_FILE"
elif [ -f "$BACKUP_FILE" ]; then
    BACKUP_PATH="$BACKUP_FILE"
elif [ -f "$(pwd)/$BACKUP_FILE" ]; then
    BACKUP_PATH="$(pwd)/$BACKUP_FILE"
fi

if [ -z "$BACKUP_PATH" ] || [ ! -f "$BACKUP_PATH" ]; then
    echo "❌ Le fichier $BACKUP_FILE n'a pas été trouvé dans :"
    echo "   - $BACKUP_DIR/"
    echo "   - /opt/erp/app/"
    echo "   - Répertoire courant"
    echo ""
    echo "💡 Vérifiez le nom du fichier ou entrez le chemin complet"
    exit 1
fi

echo "✅ Fichier trouvé : $BACKUP_PATH"

# Demander pour les images
read -p "🖼️  Restaurer aussi les images ? (o/N) : " RESTORE_IMAGES
RESTORE_IMAGES=${RESTORE_IMAGES:-N}

if [ "$RESTORE_IMAGES" = "o" ] || [ "$RESTORE_IMAGES" = "O" ]; then
    echo ""
    echo "📋 Archives d'images disponibles :"
    ls -lh $BACKUP_DIR/*images*.tar.gz 2>/dev/null | tail -5 || echo "Aucune archive d'images trouvée"
    echo ""
    read -p "📁 Entrez le nom de l'archive d'images (ou Entrée pour ignorer) : " IMAGES_FILE
    if [ -n "$IMAGES_FILE" ]; then
        IMAGES_PATH="$BACKUP_DIR/$IMAGES_FILE"
        if [ ! -f "$IMAGES_PATH" ]; then
            echo "⚠️  Le fichier $IMAGES_PATH n'existe pas, on continue sans images"
            IMAGES_PATH=""
        fi
    else
        IMAGES_PATH=""
    fi
else
    IMAGES_PATH=""
fi

echo ""
echo "⚠️  ATTENTION : Cette opération va REMPLACER la base de données actuelle !"
echo "📅 Backup à restaurer : $BACKUP_FILE"
if [ -n "$IMAGES_PATH" ]; then
    echo "🖼️  Images à restaurer : $IMAGES_FILE"
fi
echo ""
read -p "Êtes-vous sûr de vouloir continuer ? (tapez 'OUI' pour confirmer) : " CONFIRM

if [ "$CONFIRM" != "OUI" ]; then
    echo "❌ Restauration annulée"
    exit 1
fi

# Créer un backup de sécurité AVANT la restauration
echo ""
echo "💾 Création d'un backup de sécurité de la base actuelle..."
SAFETY_BACKUP="$BACKUP_DIR/safety_backup_before_restore_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump $DB_NAME > "$SAFETY_BACKUP"
echo "✅ Backup de sécurité créé : $SAFETY_BACKUP"

# Arrêter le service
echo ""
echo "⏸️  Arrêt du service ERP..."
systemctl stop $SERVICE_NAME || echo "⚠️  Service déjà arrêté"

# Supprimer la base actuelle et la recréer
echo ""
echo "🗑️  Suppression de la base de données actuelle..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};" || true
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# Restaurer depuis le backup
echo ""
echo "📥 Restauration de la base de données..."
sudo -u postgres psql -d $DB_NAME < "$BACKUP_PATH" || {
    echo "❌ Erreur lors de la restauration"
    echo "💡 Tentative de restauration depuis le backup de sécurité..."
    sudo -u postgres psql -d $DB_NAME < "$SAFETY_BACKUP"
    systemctl start $SERVICE_NAME
    exit 1
}

# Restaurer les images si demandé
if [ -n "$IMAGES_PATH" ]; then
    echo ""
    echo "🖼️  Restauration des images..."
    tar -xzvf "$IMAGES_PATH" -C / || {
        echo "⚠️  Erreur lors de la restauration des images"
    }
    echo "✅ Images restaurées"
fi

# Vérifier que la restauration a réussi
echo ""
echo "🔍 Vérification de la restauration..."
TABLE_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
PRODUCTS_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM products;" | tr -d ' ')
RECIPES_COUNT=$(sudo -u postgres psql -d $DB_NAME -t -c "SELECT COUNT(*) FROM recipes;" | tr -d ' ')
echo "✅ Nombre de tables : $TABLE_COUNT"
echo "✅ Nombre de produits : $PRODUCTS_COUNT"
echo "✅ Nombre de recettes : $RECIPES_COUNT"

# Redémarrer le service
echo ""
echo "🚀 Redémarrage du service ERP..."
systemctl start $SERVICE_NAME
sleep 3

# Vérifier le statut
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service démarré avec succès"
else
    echo "⚠️  Le service n'a pas démarré correctement"
    echo "💡 Vérifiez les logs : journalctl -u $SERVICE_NAME -n 50"
fi

echo ""
echo "✅ RESTAURATION TERMINÉE"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. Vérifier l'application : https://erp.declaimers.com"
echo "   2. Vérifier les produits et recettes"
echo "   3. Si problème, restaurer depuis : $SAFETY_BACKUP"
echo ""
echo "📁 Backup de sécurité conservé : $SAFETY_BACKUP"

