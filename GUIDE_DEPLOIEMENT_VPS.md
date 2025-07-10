# 🚀 Guide de Déploiement VPS - ERP Fée Maison

## 📋 Prérequis

- VPS Ubuntu 24.10 ou plus récent
- Accès SSH root ou sudo
- Domaine configuré (optionnel mais recommandé)

## 🔧 Installation des Dependencies

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des packages nécessaires
sudo apt install -y python3.13 python3.13-venv python3.13-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx redis-server
sudo apt install -y git curl wget unzip
sudo apt install -y build-essential libpq-dev
```

## 📥 Récupération du Code

```bash
# Cloner le dépôt
cd /var/www
sudo git clone https://github.com/infocrasher/ERPFeeMaison.git erp-fee-maison
sudo chown -R www-data:www-data erp-fee-maison
cd erp-fee-maison

# Créer l'environnement virtuel
sudo -u www-data python3.13 -m venv venv
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo -u www-data venv/bin/pip install gunicorn
```

## 🔐 Configuration Sécurisée

### 1. Générer les fichiers de configuration

```bash
# Exécuter le script de déploiement
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### 2. Configurer manuellement les paramètres sensibles

Éditer le fichier `.env` généré :

```bash
sudo nano .env
```

**Paramètres à modifier :**
- `ZK_IP` : IP de votre pointeuse ZKTeco
- `MAIL_USERNAME` : Votre email Gmail
- `MAIL_PASSWORD` : Mot de passe d'application Gmail
- `NGINX_SERVER_NAME` : Votre nom de domaine

### 3. Configuration PostgreSQL

```bash
# Exécuter le script de configuration PostgreSQL
chmod +x setup_postgresql.sh
./setup_postgresql.sh
```

### 4. Configuration Nginx

```bash
# Modifier le domaine dans setup_nginx.sh
sudo nano setup_nginx.sh

# Exécuter le script de configuration Nginx
chmod +x setup_nginx.sh
./setup_nginx.sh
```

## 🗄️ Configuration de la Base de Données

```bash
# Appliquer les migrations
sudo -u www-data venv/bin/flask db upgrade

# Créer un utilisateur admin
sudo -u www-data venv/bin/python seed.py
```

## 🚀 Démarrage du Service

```bash
# Installer le service systemd
sudo cp erp-fee-maison.service /etc/systemd/system/

# Démarrer et activer le service
sudo systemctl daemon-reload
sudo systemctl enable erp-fee-maison
sudo systemctl start erp-fee-maison

# Vérifier le statut
sudo systemctl status erp-fee-maison
```

## 🔍 Vérification

```bash
# Vérifier que l'application répond
curl http://localhost:8080

# Vérifier les logs
sudo journalctl -u erp-fee-maison -f

# Vérifier Nginx
sudo nginx -t
sudo systemctl status nginx
```

## 🔒 Sécurité

### Firewall
```bash
# Configurer UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### SSL/HTTPS (avec Certbot)
```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d votre-domaine.com
```

## 📊 Monitoring

### Logs
```bash
# Logs de l'application
sudo journalctl -u erp-fee-maison -f

# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Surveillance des ressources
```bash
# Installer htop pour surveiller les ressources
sudo apt install htop
htop
```

## 🔄 Mise à Jour

```bash
# Arrêter le service
sudo systemctl stop erp-fee-maison

# Sauvegarder la base de données
sudo -u postgres pg_dump fee_maison_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Mettre à jour le code
cd /var/www/erp-fee-maison
sudo git pull origin main

# Mettre à jour les dépendances
sudo -u www-data venv/bin/pip install -r requirements.txt

# Appliquer les migrations
sudo -u www-data venv/bin/flask db upgrade

# Redémarrer le service
sudo systemctl start erp-fee-maison
```

## 🆘 Dépannage

### Problèmes courants

1. **Service ne démarre pas**
   ```bash
   sudo systemctl status erp-fee-maison
   sudo journalctl -u erp-fee-maison -n 50
   ```

2. **Erreur de base de données**
   ```bash
   sudo -u postgres psql -d fee_maison_db -c "SELECT version();"
   ```

3. **Problème de permissions**
   ```bash
   sudo chown -R www-data:www-data /var/www/erp-fee-maison
   sudo chmod -R 755 /var/www/erp-fee-maison
   ```

4. **Port déjà utilisé**
   ```bash
   sudo netstat -tlnp | grep :8080
   sudo lsof -i :8080
   ```

## 📞 Support

En cas de problème :
1. Vérifier les logs : `sudo journalctl -u erp-fee-maison -f`
2. Vérifier la configuration : `sudo nginx -t`
3. Tester la base de données : `sudo -u postgres psql -d fee_maison_db`
4. Vérifier les permissions : `ls -la /var/www/erp-fee-maison`

---

**⚠️ Important :** Gardez toujours une copie de sauvegarde de votre base de données et de vos fichiers de configuration ! 