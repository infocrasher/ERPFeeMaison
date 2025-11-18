# 🚀 Guide de Déploiement Complet - ERP Fée Maison sur VPS

## 📋 Vue d'ensemble

Ce guide couvre le déploiement complet de l'ERP Fée Maison sur un VPS OVH, incluant :
- Application Flask avec Gunicorn
- Base de données PostgreSQL
- Serveur web Nginx
- Configuration de l'imprimante réseau (SmartPOS)
- Migrations de base de données
- Variables d'environnement

## 🏗️ Architecture

```
Internet → Nginx (Port 80) → Gunicorn (Port 5000) → Flask App → PostgreSQL
                                                              ↓
                                                    SmartPOS (Agent HTTP)
```

## ✅ Prérequis

- VPS Ubuntu 20.04+ (OVH)
- Accès SSH avec privilèges root/sudo
- Domaine configuré (optionnel)
- Python 3.10+ installé
- PostgreSQL installé
- Nginx installé

## 🔧 Étape 1 : Préparation du VPS

### 1.1 Mise à jour du système

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Installation des dépendances système

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    build-essential \
    libpq-dev \
    python3-dev \
    curl
```

### 1.3 Création de l'utilisateur applicatif

```bash
sudo useradd -m -s /bin/bash erp-admin
sudo usermod -aG sudo erp-admin
```

## 🗄️ Étape 2 : Configuration PostgreSQL

### 2.1 Créer la base de données et l'utilisateur

```bash
sudo -u postgres psql << EOF
CREATE DATABASE fee_maison_db;
CREATE USER fee_maison_user WITH PASSWORD 'FeeMaison_ERP_2025_Secure!';
GRANT ALL PRIVILEGES ON DATABASE fee_maison_db TO fee_maison_user;
ALTER USER fee_maison_user CREATEDB;
\q
EOF
```

### 2.2 Vérifier la connexion

```bash
psql -U fee_maison_user -d fee_maison_db -h localhost -c "SELECT version();"
```

## 📦 Étape 3 : Déploiement de l'Application

### 3.1 Cloner le projet

```bash
sudo mkdir -p /opt/erp
sudo chown erp-admin:erp-admin /opt/erp
cd /opt/erp

# Option A : Depuis Git
sudo -u erp-admin git clone https://github.com/votre-repo/fee_maison_gestion_cursor.git app

# Option B : Transfert depuis MacBook
# Utiliser scp ou rsync pour copier le projet
```

### 3.2 Créer l'environnement virtuel

```bash
cd /opt/erp/app
sudo -u erp-admin python3 -m venv venv
sudo -u erp-admin venv/bin/pip install --upgrade pip
```

### 3.3 Installer les dépendances

```bash
sudo -u erp-admin venv/bin/pip install -r requirements.txt
```

**Note** : Si `prophet` pose problème, installer les dépendances système :
```bash
sudo apt install -y libpython3-dev python3-numpy-dev
```

## ⚙️ Étape 4 : Configuration

### 4.1 Créer le fichier .env

```bash
cd /opt/erp/app
sudo -u erp-admin nano .env
```

Contenu du fichier `.env` :

```env
# ========================================
# CONFIGURATION PRODUCTION
# ========================================

# Flask
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=GÉNÉRER_UN_SECRET_KEY_SÉCURISÉ_ICI
DEBUG=False

# Base de données PostgreSQL
POSTGRES_USER=fee_maison_user
POSTGRES_PASSWORD=FeeMaison_ERP_2025_Secure!
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB_NAME=fee_maison_db
DATABASE_URL=postgresql://fee_maison_user:FeeMaison_ERP_2025_Secure!@localhost:5432/fee_maison_db

# Email (optionnel)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# Imprimante Réseau (SmartPOS)
PRINTER_NETWORK_ENABLED=true
PRINTER_AGENT_HOST=IP_OU_DOMAINE_SMARTPOS
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=TOKEN_IDENTIQUE_AU_SMARTPOS

# IA (optionnel)
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...

# Pointeuse ZKTeco (optionnel)
ZK_DEVICE_IP=192.168.1.100
ZK_DEVICE_PORT=4370
ZK_DEVICE_PASSWORD=123456
```

**Générer SECRET_KEY** :
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 4.2 Créer les répertoires nécessaires

```bash
sudo mkdir -p /opt/erp/uploads
sudo mkdir -p /var/log/erp
sudo chown -R erp-admin:erp-admin /opt/erp
sudo chown -R erp-admin:erp-admin /var/log/erp
```

## 🗃️ Étape 5 : Migrations de Base de Données

### 5.1 Initialiser Alembic (si première installation)

```bash
cd /opt/erp/app
sudo -u erp-admin venv/bin/flask db init
```

### 5.2 Appliquer les migrations

```bash
cd /opt/erp/app
sudo -u erp-admin venv/bin/flask db upgrade
```

### 5.3 Vérifier les tables

```bash
psql -U fee_maison_user -d fee_maison_db -h localhost -c "\dt"
```

## 🔧 Étape 6 : Configuration Gunicorn

### 6.1 Créer le service systemd

```bash
sudo nano /etc/systemd/system/erp-fee-maison.service
```

Contenu :

```ini
[Unit]
Description=ERP Fée Maison Flask Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=erp-admin
Group=erp-admin
WorkingDirectory=/opt/erp/app
Environment=PATH=/opt/erp/app/venv/bin
EnvironmentFile=/opt/erp/app/.env
ExecStart=/opt/erp/app/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/erp/access.log \
    --error-logfile /var/log/erp/error.log \
    --log-level info \
    wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.2 Activer et démarrer le service

```bash
sudo systemctl daemon-reload
sudo systemctl enable erp-fee-maison
sudo systemctl start erp-fee-maison
sudo systemctl status erp-fee-maison
```

## 🌐 Étape 7 : Configuration Nginx

### 7.1 Créer la configuration Nginx

```bash
sudo nano /etc/nginx/sites-available/erp-fee-maison
```

Contenu (utiliser `nginx_erp.conf` comme référence) :

```nginx
server {
    listen 80;
    server_name erp.declaimers.com 51.254.36.25;
    
    access_log /var/log/nginx/erp_access.log;
    error_log /var/log/nginx/erp_error.log;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    location /static/ {
        alias /opt/erp/app/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads/ {
        alias /opt/erp/uploads/;
        client_max_body_size 10M;
    }
}
```

### 7.2 Activer le site

```bash
sudo ln -sf /etc/nginx/sites-available/erp-fee-maison /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Étape 8 : Configuration Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (si SSL configuré)
sudo ufw enable
```

## ✅ Étape 9 : Vérifications

### 9.1 Vérifier le service

```bash
sudo systemctl status erp-fee-maison
sudo journalctl -u erp-fee-maison -f
```

### 9.2 Vérifier Nginx

```bash
sudo systemctl status nginx
sudo nginx -t
```

### 9.3 Tester l'application

```bash
curl http://localhost:5000
curl http://erp.declaimers.com
```

### 9.4 Vérifier les logs

```bash
tail -f /var/log/erp/access.log
tail -f /var/log/erp/error.log
tail -f /var/log/nginx/erp_error.log
```

## 🔄 Étape 10 : Mise à Jour (Déploiements Futurs)

### Script de mise à jour

```bash
#!/bin/bash
cd /opt/erp/app

# Sauvegarder la base de données
pg_dump -U fee_maison_user fee_maison_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Mettre à jour le code
git pull origin main
# ou
# rsync depuis MacBook

# Mettre à jour les dépendances
venv/bin/pip install -r requirements.txt

# Appliquer les migrations
venv/bin/flask db upgrade

# Redémarrer le service
sudo systemctl restart erp-fee-maison
```

## 🐛 Dépannage

### Problème : Service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u erp-fee-maison -n 50

# Vérifier les permissions
ls -la /opt/erp/app
sudo chown -R erp-admin:erp-admin /opt/erp/app
```

### Problème : Erreur de connexion PostgreSQL

```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"

# Vérifier les permissions
sudo -u postgres psql -c "\du"
```

### Problème : Erreur 502 Bad Gateway

```bash
# Vérifier que Gunicorn écoute
sudo netstat -tlnp | grep 5000

# Vérifier les logs Nginx
sudo tail -f /var/log/nginx/erp_error.log
```

## 📝 Checklist de Déploiement

- [ ] VPS préparé (Ubuntu, dépendances installées)
- [ ] PostgreSQL configuré (base + utilisateur)
- [ ] Projet cloné/copié sur le VPS
- [ ] Environnement virtuel créé
- [ ] Dépendances installées
- [ ] Fichier `.env` configuré avec tous les secrets
- [ ] Migrations appliquées
- [ ] Service systemd créé et activé
- [ ] Nginx configuré et actif
- [ ] Firewall configuré
- [ ] Tests de connectivité réussis
- [ ] Logs vérifiés
- [ ] Accès depuis Internet testé

## 🆘 Support

En cas de problème :
1. Vérifier les logs : `sudo journalctl -u erp-fee-maison -f`
2. Vérifier Nginx : `sudo nginx -t && sudo tail -f /var/log/nginx/erp_error.log`
3. Vérifier PostgreSQL : `sudo systemctl status postgresql`
4. Tester manuellement : `cd /opt/erp/app && venv/bin/python wsgi.py`

