# 🚀 Guide de Préparation VPS - ERP Fée Maison

## 📋 **Informations VPS**
- **IP** : 51.254.36.25
- **OS** : Ubuntu 24.10
- **Utilisateur** : root (à changer)
- **Objectif** : Déployer ERP Flask

---

## 🔐 **PHASE 1 : Sécurité et Préparation Initiale**

### ✅ **Étape 1.1 : Vérification système**
```bash
# Vérifier que les mises à jour sont terminées
sudo apt update && sudo apt upgrade -y

# Vérifier l'IP du serveur
hostname -I

# Vérifier l'espace disque
df -h
```

### ✅ **Étape 1.2 : Création utilisateur sécurisé**
```bash
# Créer un utilisateur dédié pour l'ERP
adduser erp-admin

# Donner les droits sudo
usermod -aG sudo erp-admin

# Passer à ce nouvel utilisateur
su - erp-admin

# Vérifier les droits
sudo whoami
```

---

## 🛠️ **PHASE 2 : Installation Stack Technique**

### ✅ **Étape 2.1 : Outils de base**
```bash
# Installation Python et outils
sudo apt install python3-pip python3-venv git curl wget unzip

# Vérifier les versions
python3 --version
pip3 --version
git --version
```

### ✅ **Étape 2.2 : Base de données PostgreSQL**
```bash
# Installation PostgreSQL
sudo apt install postgresql postgresql-contrib

# Vérifier le statut
sudo systemctl status postgresql

# Activer le démarrage automatique
sudo systemctl enable postgresql
```

### ✅ **Étape 2.3 : Serveur web Nginx**
```bash
# Installation Nginx
sudo apt install nginx

# Vérifier le statut
sudo systemctl status nginx

# Activer le démarrage automatique
sudo systemctl enable nginx
```

### ✅ **Étape 2.4 : Outils de monitoring**
```bash
# Installation htop pour monitoring
sudo apt install htop

# Test du monitoring
htop
```

---

## 📁 **PHASE 3 : Structure du Projet**

### ✅ **Étape 3.1 : Création des répertoires**
```bash
# Créer la structure du projet
sudo mkdir -p /opt/erp
sudo mkdir -p /opt/erp/app
sudo mkdir -p /opt/erp/logs
sudo mkdir -p /opt/erp/backups
sudo mkdir -p /opt/erp/uploads

# Changer le propriétaire
sudo chown -R erp-admin:erp-admin /opt/erp

# Vérifier la structure
ls -la /opt/erp/
```

### ✅ **Étape 3.2 : Configuration PostgreSQL**
```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Dans PostgreSQL, créer la base et l'utilisateur
CREATE DATABASE fee_maison_db;
CREATE USER erp_user WITH PASSWORD 'erp_password_2025';
GRANT ALL PRIVILEGES ON DATABASE fee_maison_db TO erp_user;
\q
```

---

## 🔧 **PHASE 4 : Configuration Nginx**

### ✅ **Étape 4.1 : Configuration de base**
```bash
# Sauvegarder la config par défaut
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Éditer la configuration
sudo nano /etc/nginx/sites-available/default
```

### ✅ **Étape 4.2 : Contenu de la configuration Nginx**
```nginx
server {
    listen 80;
    server_name 51.254.36.25 erp.declaimers.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/erp/app/app/static/;
        expires 30d;
    }
}
```

### ✅ **Étape 4.3 : Activer la configuration**
```bash
# Tester la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx

# Vérifier le statut
sudo systemctl status nginx
```

---

## 📊 **PHASE 5 : Commandes de Monitoring**

### ✅ **Étape 5.1 : Vérifications quotidiennes**
```bash
# Vérifier l'état des services
sudo systemctl status nginx
sudo systemctl status postgresql

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les ports ouverts
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :5432
```

### ✅ **Étape 5.2 : Logs et diagnostic**
```bash
# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Logs système
journalctl -f
```

---

## 🎯 **COMMANDES "KIT DE SURVIE"**

### **Top 10 des commandes essentielles :**

1. **`ls -la`** - Voir le contenu d'un dossier
2. **`cd /opt/erp`** - Aller dans le dossier de l'ERP
3. **`sudo systemctl status nginx`** - Vérifier Nginx
4. **`sudo systemctl restart nginx`** - Redémarrer Nginx
5. **`htop`** - Monitoring des ressources
6. **`df -h`** - Espace disque
7. **`sudo nano /etc/nginx/sites-available/default`** - Éditer config Nginx
8. **`sudo nginx -t`** - Tester config Nginx
9. **`sudo tail -f /var/log/nginx/error.log`** - Logs d'erreur
10. **`sudo netstat -tulpn`** - Ports ouverts

---

## ✅ **CHECKLIST DE PRÉPARATION**

- [ ] Mises à jour système terminées
- [ ] Utilisateur erp-admin créé avec sudo
- [ ] Python3, pip3, git installés
- [ ] PostgreSQL installé et configuré
- [ ] Nginx installé et configuré
- [ ] Structure /opt/erp créée
- [ ] Base de données fee_maison_db créée
- [ ] Configuration Nginx testée
- [ ] Services démarrés et activés
- [ ] Monitoring configuré

---

## 🚀 **PROCHAINES ÉTAPES**

Une fois cette préparation terminée :
1. **Transférer le code** depuis votre MacBook
2. **Configurer l'environnement Python**
3. **Déployer l'application Flask**
4. **Configurer SSL avec Let's Encrypt**
5. **Tester l'ERP en production**

---

*Guide créé pour ERP Fée Maison - VPS 51.254.36.25* 