#!/bin/bash

# ========================================
# SCRIPT DE DÉPLOIEMENT VPS SÉCURISÉ
# ========================================
# Ce script génère automatiquement les fichiers de configuration
# sans exposer de secrets dans le dépôt Git

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement ERP Fée Maison sur VPS"
echo "======================================"

# Variables de configuration (à modifier selon votre VPS)
DB_PASSWORD="$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)"
SECRET_KEY="$(openssl rand -base64 64)"
ZK_PASSWORD="$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-12)"

echo "✅ Génération des mots de passe sécurisés..."

# Créer le fichier .env de production
cat > .env << EOF
# ========================================
# CONFIGURATION PRODUCTION - GÉNÉRÉE AUTOMATIQUEMENT
# ========================================

# CONFIGURATION FLASK
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DEBUG=False

# CONFIGURATION BASE DE DONNÉES POSTGRESQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fee_maison_db
DB_USER=erp_user
POSTGRES_PASSWORD=${DB_PASSWORD}

# CONFIGURATION REDIS (OPTIONNEL)
REDIS_URL=redis://localhost:6379/0

# CONFIGURATION POINTEUSE ZKTECO
ZK_IP=192.168.1.100
ZK_PORT=4370
ZK_PASSWORD=${ZK_PASSWORD}
ZK_API_PASSWORD=admin123

# CONFIGURATION EMAIL (À CONFIGURER MANUELLEMENT)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here

# CONFIGURATION NGINX
NGINX_SERVER_NAME=your_domain.com
NGINX_SSL_CERT_PATH=/path/to/ssl/cert.pem
NGINX_SSL_KEY_PATH=/path/to/ssl/key.pem
EOF

echo "✅ Fichier .env créé avec des secrets sécurisés"

# Créer le script de configuration PostgreSQL
cat > setup_postgresql.sh << EOF
#!/bin/bash
# Configuration PostgreSQL sécurisée

DB_NAME="fee_maison_db"
DB_USER="erp_user"
DB_PASSWORD="${DB_PASSWORD}"

echo "🗄️  Configuration PostgreSQL..."

# Créer la base de données
sudo -u postgres psql -c "CREATE DATABASE \$DB_NAME;" 2>/dev/null || echo "Base de données déjà existante"

# Créer l'utilisateur
sudo -u postgres psql -c "CREATE USER \$DB_USER WITH PASSWORD '\$DB_PASSWORD';" 2>/dev/null || echo "Utilisateur déjà existant"

# Donner les permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \$DB_NAME TO \$DB_USER;"
sudo -u postgres psql -c "ALTER USER \$DB_USER CREATEDB;"

echo "✅ PostgreSQL configuré avec succès"
echo "   Base: \$DB_NAME"
echo "   Utilisateur: \$DB_USER"
echo "   Mot de passe: \$DB_PASSWORD"
EOF

chmod +x setup_postgresql.sh

# Créer le script de configuration Nginx
cat > setup_nginx.sh << EOF
#!/bin/bash
# Configuration Nginx

DOMAIN="your_domain.com"
APP_PORT="8080"

echo "🌐 Configuration Nginx..."

# Créer la configuration Nginx
sudo tee /etc/nginx/sites-available/erp-fee-maison << EOF_NGINX
server {
    listen 80;
    server_name \$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:\$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/erp-fee-maison/app/static;
        expires 30d;
    }
}
EOF_NGINX

# Activer le site
sudo ln -sf /etc/nginx/sites-available/erp-fee-maison /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Nginx configuré pour \$DOMAIN"
EOF

chmod +x setup_nginx.sh

# Créer le service systemd
cat > erp-fee-maison.service << EOF
[Unit]
Description=ERP Fée Maison Flask Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/erp-fee-maison
Environment=PATH=/var/www/erp-fee-maison/venv/bin
Environment=FLASK_APP=wsgi.py
Environment=FLASK_ENV=production
Environment=POSTGRES_USER=erp_user
Environment=POSTGRES_PASSWORD=${DB_PASSWORD}
Environment=POSTGRES_HOST=localhost
Environment=POSTGRES_PORT=5432
Environment=POSTGRES_DB_NAME=fee_maison_db
Environment=SECRET_KEY=${SECRET_KEY}
ExecStart=/var/www/erp-fee-maison/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8080 --timeout 120 --access-logfile /var/log/erp-fee-maison/access.log --error-logfile /var/log/erp-fee-maison/error.log wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Fichiers de configuration créés"
echo ""
echo "📋 PROCHAINES ÉTAPES :"
echo "1. Copier ces fichiers sur le VPS"
echo "2. Exécuter: chmod +x setup_postgresql.sh setup_nginx.sh"
echo "3. Exécuter: ./setup_postgresql.sh"
echo "4. Configurer l'email dans .env"
echo "5. Exécuter: ./setup_nginx.sh"
echo "6. Installer le service: sudo cp erp-fee-maison.service /etc/systemd/system/"
echo "7. Démarrer: sudo systemctl enable erp-fee-maison && sudo systemctl start erp-fee-maison"
echo ""
echo "🔐 SECRETS GÉNÉRÉS :"
echo "   DB_PASSWORD: ${DB_PASSWORD}"
echo "   SECRET_KEY: ${SECRET_KEY:0:20}..."
echo "   ZK_PASSWORD: ${ZK_PASSWORD}"
echo ""
echo "⚠️  IMPORTANT: Notez ces secrets et gardez-les en sécurité !" 