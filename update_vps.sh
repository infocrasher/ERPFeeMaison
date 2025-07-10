#!/bin/bash

# ============================================================
# 🔄 SCRIPT DE MISE À JOUR VPS - ERP FÉE MAISON
# ============================================================
# Ce script met à jour le VPS avec les dernières corrections
# et configure le service systemd final

set -e  # Arrêter en cas d'erreur

echo "🔄 MISE À JOUR VPS ERP FÉE MAISON"
echo "=================================="

# Variables
ERP_DIR="/opt/erp"
APP_DIR="$ERP_DIR/app"
SERVICE_NAME="erp-fee-maison"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier que nous sommes sur le VPS
if [ ! -d "$ERP_DIR" ]; then
    log_error "Répertoire ERP non trouvé: $ERP_DIR"
    log_error "Ce script doit être exécuté sur le VPS"
    exit 1
fi

# 1. Sauvegarder la configuration actuelle
log_info "Sauvegarde de la configuration actuelle..."
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$ERP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
    log_success "Configuration sauvegardée"
fi

# 2. Aller dans le répertoire de l'application
cd "$APP_DIR"

# 3. Récupérer les dernières modifications
log_info "Récupération des dernières modifications..."
git fetch origin
git reset --hard origin/main
log_success "Code mis à jour"

# 4. Installer/mettre à jour les dépendances
log_info "Mise à jour des dépendances Python..."
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn==23.0.0
log_success "Dépendances mises à jour"

# 5. Vérifier que les fichiers de correction sont présents
log_info "Vérification des fichiers de correction..."
REQUIRED_FILES=("diagnostic_erp.py" "wsgi.py" "start_erp.sh")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "$file présent"
    else
        log_error "$file manquant"
        exit 1
    fi
done

# 6. Rendre les scripts exécutables
chmod +x diagnostic_erp.py start_erp.sh

# 7. Tester le diagnostic
log_info "Test du script de diagnostic..."
python3 diagnostic_erp.py

# 8. Créer le service systemd corrigé
log_info "Configuration du service systemd..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=ERP Fée Maison Flask Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=erp-admin
Group=erp-admin
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=FLASK_ENV=production
Environment=SECRET_KEY=MPw0QYyvKozThVQERADaDA5DASASDAsxDxar7RuvMsqYiMaY7sJO#P
Environment=POSTGRES_USER=erp_user
Environment=POSTGRES_PASSWORD=erp_secure_password_2024
Environment=POSTGRES_HOST=localhost
Environment=POSTGRES_PORT=5432
Environment=POSTGRES_DB_NAME=fee_maison_db
Environment=REDIS_URL=redis://localhost:6379/0
Environment=MAIL_SERVER=smtp.gmail.com
Environment=MAIL_PORT=587
Environment=MAIL_USE_TLS=true
Environment=MAIL_USERNAME=erpfeemaison@gmail.com
Environment=MAIL_PASSWORD=erp_secure_mail_password_2024
Environment=ZK_DEVICE_IP=192.168.1.100
Environment=ZK_DEVICE_PORT=4370
Environment=ZK_DEVICE_PASSWORD=123456
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8080 --timeout 120 --access-logfile /var/log/erp/access.log --error-logfile /var/log/erp/error.log wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log_success "Service systemd créé"

# 9. Créer les répertoires de logs
sudo mkdir -p /var/log/erp
sudo chown erp-admin:erp-admin /var/log/erp

# 10. Recharger systemd et activer le service
log_info "Configuration de systemd..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
log_success "Service activé"

# 11. Tester le démarrage
log_info "Test du démarrage du service..."
sudo systemctl start $SERVICE_NAME
sleep 3

# 12. Vérifier le statut
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Service démarré avec succès"
    sudo systemctl status $SERVICE_NAME --no-pager -l
else
    log_error "Échec du démarrage du service"
    sudo systemctl status $SERVICE_NAME --no-pager -l
    sudo journalctl -u $SERVICE_NAME -n 20 --no-pager
    exit 1
fi

# 13. Test de l'application
log_info "Test de l'application..."
sleep 2
if curl -s http://localhost:8080 > /dev/null; then
    log_success "Application accessible sur localhost:8080"
else
    log_warning "Application non accessible - vérifiez les logs"
fi

# 14. Test du proxy Nginx
log_info "Test du proxy Nginx..."
if curl -s http://erp.declaimers.com > /dev/null; then
    log_success "Proxy Nginx fonctionnel"
else
    log_warning "Proxy Nginx non accessible - vérifiez la configuration"
fi

echo ""
echo "🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS"
echo "===================================="
echo "📋 Récapitulatif:"
echo "   ✅ Code mis à jour depuis GitHub"
echo "   ✅ Dépendances installées"
echo "   ✅ Service systemd configuré"
echo "   ✅ Application démarrée"
echo ""
echo "🔧 Commandes utiles:"
echo "   sudo systemctl status $SERVICE_NAME"
echo "   sudo systemctl restart $SERVICE_NAME"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo "   python3 diagnostic_erp.py"
echo ""
echo "🌐 Accès:"
echo "   Local: http://localhost:8080"
echo "   Web: http://erp.declaimers.com"
echo "" 