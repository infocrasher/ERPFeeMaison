#!/bin/bash
# ========================================
# SCRIPT DE MISE À JOUR VPS
# Pour les déploiements futurs
# ========================================

set -e

APP_DIR="/opt/erp/app"
APP_USER="erp-admin"
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
SERVICE_NAME="erp-fee-maison"

echo "🔄 Mise à jour ERP Fée Maison sur VPS"
echo "======================================"
echo ""

# Vérifier les privilèges
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

# Sauvegarder la base de données
echo "💾 Sauvegarde de la base de données..."
BACKUP_FILE="/opt/erp/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /opt/erp/backups
sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE
echo "✅ Sauvegarde créée: $BACKUP_FILE"

# Arrêter le service
echo "⏸️  Arrêt du service..."
systemctl stop $SERVICE_NAME

# Mettre à jour le code
echo "📦 Mise à jour du code..."
cd $APP_DIR

# Option A : Git
if [ -d ".git" ]; then
    sudo -u $APP_USER git pull origin main
else
    echo "⚠️  Dépôt Git non détecté, mise à jour manuelle requise"
    echo "💡 Utilisez rsync ou scp pour copier les nouveaux fichiers"
    read -p "Appuyez sur Entrée une fois le code mis à jour..."
fi

# Mettre à jour les dépendances
echo "📦 Mise à jour des dépendances..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt

# Appliquer les migrations
echo "🗃️  Application des migrations..."
cd $APP_DIR
sudo -u $APP_USER venv/bin/flask db upgrade

# Redémarrer le service
echo "🚀 Redémarrage du service..."
systemctl start $SERVICE_NAME
sleep 2

# Vérifier le statut
systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo "✅ Mise à jour terminée"
echo ""
echo "📋 Vérifications :"
echo "   - Service: systemctl status $SERVICE_NAME"
echo "   - Logs: journalctl -u $SERVICE_NAME -f"
echo "   - Application: curl http://localhost:5000"

