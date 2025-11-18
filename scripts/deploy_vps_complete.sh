#!/bin/bash
# ========================================
# SCRIPT DE DÉPLOIEMENT COMPLET VPS
# ERP Fée Maison - Version Complète
# ========================================

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier les privilèges root
if [ "$EUID" -ne 0 ]; then 
    log_error "Ce script doit être exécuté en tant que root ou avec sudo"
    exit 1
fi

echo "=========================================="
echo "🚀 DÉPLOIEMENT ERP FÉE MAISON SUR VPS"
echo "=========================================="
echo ""

# Variables de configuration
APP_DIR="/opt/erp/app"
APP_USER="erp-admin"
DB_NAME="fee_maison_db"
DB_USER="fee_maison_user"
SERVICE_NAME="erp-fee-maison"
NGINX_SITE="erp-fee-maison"

# Générer les secrets
log_info "Génération des secrets sécurisés..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -base64 64)
ZK_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)

log_success "Secrets générés"

# Demander confirmation
read -p "📋 Voulez-vous continuer avec le déploiement ? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    log_error "Déploiement annulé"
    exit 1
fi

# Étape 1 : Installation des dépendances système
log_info "Étape 1/10 : Installation des dépendances système..."
apt update -qq
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git build-essential libpq-dev python3-dev curl > /dev/null 2>&1
log_success "Dépendances installées"

# Étape 2 : Création de l'utilisateur
log_info "Étape 2/10 : Création de l'utilisateur $APP_USER..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    log_success "Utilisateur $APP_USER créé"
else
    log_info "Utilisateur $APP_USER existe déjà"
fi

# Étape 3 : Configuration PostgreSQL
log_info "Étape 3/10 : Configuration PostgreSQL..."
sudo -u postgres psql << EOF > /dev/null 2>&1
CREATE DATABASE $DB_NAME;
EOF
if [ $? -eq 0 ]; then
    log_success "Base de données $DB_NAME créée"
else
    log_info "Base de données $DB_NAME existe déjà"
fi

sudo -u postgres psql << EOF > /dev/null 2>&1
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
EOF
if [ $? -eq 0 ]; then
    log_success "Utilisateur $DB_USER créé"
else
    log_info "Utilisateur $DB_USER existe déjà, mise à jour du mot de passe..."
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" > /dev/null 2>&1
fi

sudo -u postgres psql << EOF > /dev/null 2>&1
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
EOF
log_success "PostgreSQL configuré"

# Étape 4 : Création des répertoires
log_info "Étape 4/10 : Création des répertoires..."
mkdir -p $APP_DIR
mkdir -p /opt/erp/uploads
mkdir -p /var/log/erp
chown -R $APP_USER:$APP_USER /opt/erp
chown -R $APP_USER:$APP_USER /var/log/erp
log_success "Répertoires créés"

# Étape 5 : Création du fichier .env
log_info "Étape 5/10 : Création du fichier .env..."
cat > $APP_DIR/.env << EOF
# ========================================
# CONFIGURATION PRODUCTION - GÉNÉRÉE AUTOMATIQUEMENT
# ========================================

# Flask
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DEBUG=False

# Base de données PostgreSQL
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB_NAME=${DB_NAME}
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# Email (À CONFIGURER MANUELLEMENT)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here

# Imprimante Réseau (À CONFIGURER APRÈS INSTALLATION SMARTPOS)
PRINTER_NETWORK_ENABLED=false
PRINTER_AGENT_HOST=localhost
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=default_token_change_me

# IA (Optionnel)
# OPENAI_API_KEY=sk-proj-...
# GROQ_API_KEY=gsk_...

# Pointeuse ZKTeco (Optionnel)
ZK_DEVICE_IP=192.168.1.100
ZK_DEVICE_PORT=4370
ZK_DEVICE_PASSWORD=123456
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env
log_success "Fichier .env créé"

# Afficher les secrets générés
echo ""
echo "=========================================="
echo "🔐 SECRETS GÉNÉRÉS - NOTEZ-LES !"
echo "=========================================="
echo "DB_PASSWORD: ${DB_PASSWORD}"
echo "SECRET_KEY: ${SECRET_KEY:0:30}..."
echo "ZK_PASSWORD: ${ZK_PASSWORD}"
echo ""
echo "⚠️  IMPORTANT: Ces secrets sont sauvegardés dans $APP_DIR/.env"
echo ""

# Étape 6 : Instructions pour le déploiement du code
log_info "Étape 6/10 : Instructions pour le déploiement du code..."
echo ""
echo "📦 PROCHAINES ÉTAPES MANUELLES :"
echo ""
echo "1. Copier le projet dans $APP_DIR :"
echo "   Option A (Git):"
echo "   sudo -u $APP_USER git clone https://github.com/votre-repo/fee_maison_gestion_cursor.git $APP_DIR"
echo ""
echo "   Option B (SCP depuis MacBook):"
echo "   scp -r /chemin/vers/projet $APP_USER@VPS_IP:$APP_DIR"
echo ""
echo "2. Créer l'environnement virtuel :"
echo "   cd $APP_DIR"
echo "   sudo -u $APP_USER python3 -m venv venv"
echo ""
echo "3. Installer les dépendances :"
echo "   sudo -u $APP_USER venv/bin/pip install --upgrade pip"
echo "   sudo -u $APP_USER venv/bin/pip install -r requirements.txt"
echo ""
echo "4. Appliquer les migrations :"
echo "   cd $APP_DIR"
echo "   sudo -u $APP_USER venv/bin/flask db upgrade"
echo ""

read -p "Appuyez sur Entrée une fois le code déployé et les dépendances installées..."

# Étape 7 : Création du service systemd
log_info "Étape 7/10 : Création du service systemd..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=ERP Fée Maison Flask Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/erp/access.log \
    --error-logfile /var/log/erp/error.log \
    --log-level info \
    wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
log_success "Service systemd créé et activé"

# Étape 8 : Configuration Nginx
log_info "Étape 8/10 : Configuration Nginx..."
read -p "🌐 Entrez le nom de domaine (ou IP) : " DOMAIN

cat > /etc/nginx/sites-available/${NGINX_SITE} << EOF
server {
    listen 80;
    server_name ${DOMAIN};
    
    access_log /var/log/nginx/erp_access.log;
    error_log /var/log/nginx/erp_error.log;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    location /static/ {
        alias ${APP_DIR}/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads/ {
        alias /opt/erp/uploads/;
        client_max_body_size 10M;
    }
}
EOF

ln -sf /etc/nginx/sites-available/${NGINX_SITE} /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
log_success "Nginx configuré pour ${DOMAIN}"

# Étape 9 : Configuration Firewall
log_info "Étape 9/10 : Configuration Firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    log_success "Règles firewall ajoutées"
else
    log_info "UFW non installé, configurez le firewall manuellement"
fi

# Étape 10 : Démarrage du service
log_info "Étape 10/10 : Démarrage du service..."
systemctl start ${SERVICE_NAME}
sleep 2
systemctl status ${SERVICE_NAME} --no-pager -l

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=========================================="
echo ""
echo "📋 RÉSUMÉ :"
echo "   Application: ${APP_DIR}"
echo "   Utilisateur: ${APP_USER}"
echo "   Base de données: ${DB_NAME}"
echo "   Service: ${SERVICE_NAME}"
echo "   Domaine: ${DOMAIN}"
echo ""
echo "🔗 URLs :"
echo "   http://${DOMAIN}"
echo "   http://localhost:5000 (direct)"
echo ""
echo "📝 COMMANDES UTILES :"
echo "   Status: sudo systemctl status ${SERVICE_NAME}"
echo "   Logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "   Redémarrer: sudo systemctl restart ${SERVICE_NAME}"
echo ""
echo "⚠️  N'OUBLIEZ PAS :"
echo "   1. Configurer l'email dans ${APP_DIR}/.env"
echo "   2. Configurer l'imprimante réseau (SmartPOS)"
echo "   3. Créer un utilisateur admin: cd ${APP_DIR} && venv/bin/flask create-admin"
echo "   4. Tester l'application: curl http://${DOMAIN}"
echo ""

