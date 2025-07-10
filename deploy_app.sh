#!/bin/bash

# Script de déploiement de l'application ERP Fée Maison
# À exécuter après deploy_setup.sh

echo "🚀 Déploiement application ERP Fée Maison"
echo "========================================="

# Variables
APP_DIR="/opt/erp/app"
BACKUP_DIR="/opt/erp/backups"
LOG_DIR="/var/log/erp"

# Création des répertoires manquants
echo "📁 Création répertoires..."
sudo mkdir -p $APP_DIR
sudo mkdir -p $BACKUP_DIR
sudo mkdir -p $LOG_DIR
sudo mkdir -p /opt/erp/uploads

# Changement de propriétaire
sudo chown -R erp:erp /opt/erp
sudo chown -R erp:erp $LOG_DIR

# Copie des fichiers (à adapter selon votre méthode de transfert)
echo "📋 Copie des fichiers..."
# Exemple avec rsync depuis votre Mac :
# rsync -avz --exclude='venv' --exclude='__pycache__' /Users/sofiane/Documents/Save\ FM/fee_maison_gestion_cursor/ root@51.254.36.25:/opt/erp/app/

# Changement vers l'utilisateur erp
sudo -u erp bash << 'EOF'
cd /opt/erp/app

# Création environnement virtuel Python
echo "🐍 Création environnement virtuel..."
python3.13 -m venv venv

# Activation environnement virtuel
source venv/bin/activate

# Mise à jour pip
pip install --upgrade pip

# Installation des dépendances
echo "📦 Installation dépendances Python..."
pip install -r requirements.txt

# Installation Gunicorn pour production
pip install gunicorn psycopg2-binary

# Configuration de la base de données
echo "🐘 Configuration base de données..."
export FLASK_APP=app
export FLASK_ENV=production
export DATABASE_URL="postgresql://erp_user:erp_password_2025@localhost/fee_maison_db"

# Initialisation de la base de données
flask db upgrade || echo "Migration non disponible, création manuelle..."

# Test de l'application
echo "🧪 Test de l'application..."
python -c "from app import create_app; app = create_app(); print('✅ Application créée avec succès')"

EOF

# Configuration Gunicorn
echo "🦄 Configuration Gunicorn..."
sudo tee /etc/systemd/system/erp-gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn instance to serve ERP Fée Maison
After=network.target

[Service]
User=erp
Group=erp
WorkingDirectory=/opt/erp/app
Environment="PATH=/opt/erp/app/venv/bin"
Environment="FLASK_ENV=production"
Environment="DATABASE_URL=postgresql://erp_user:erp_password_2025@localhost/fee_maison_db"
ExecStart=/opt/erp/app/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 -m 007 run:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configuration Nginx
echo "🌐 Configuration Nginx..."
sudo cp nginx_erp.conf /etc/nginx/sites-available/erp
sudo ln -sf /etc/nginx/sites-available/erp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration Nginx
sudo nginx -t

# Démarrage des services
echo "🚀 Démarrage des services..."
sudo systemctl daemon-reload
sudo systemctl enable erp-gunicorn
sudo systemctl start erp-gunicorn
sudo systemctl restart nginx

# Vérification statut
echo "📊 Vérification statut des services..."
sudo systemctl status erp-gunicorn --no-pager -l
sudo systemctl status nginx --no-pager -l

# Test de connectivité
echo "🧪 Test de connectivité..."
curl -I http://localhost || echo "⚠️ Service non accessible"

echo ""
echo "✅ Déploiement terminé !"
echo "======================="
echo "🌐 Application accessible sur :"
echo "   - http://51.254.36.25"
echo "   - http://erp.declaimers.com (si DNS configuré)"
echo ""
echo "📋 Commandes utiles :"
echo "   - Logs app : sudo journalctl -u erp-gunicorn -f"
echo "   - Logs nginx : sudo tail -f /var/log/nginx/erp_*.log"
echo "   - Redémarrer : sudo systemctl restart erp-gunicorn"
echo ""
echo "🔒 Prochaine étape : Configuration SSL avec Let's Encrypt"
echo "   sudo certbot --nginx -d erp.declaimers.com" 