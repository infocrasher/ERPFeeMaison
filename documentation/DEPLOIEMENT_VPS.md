# 📋 DOCUMENTATION COMPLÈTE - ERP FÉE MAISON VPS

## 🏗️ ARCHITECTURE GÉNÉRALE DU SYSTÈME

### **Infrastructure VPS**
- **Hébergeur** : OVH
- **Système d'exploitation** : Ubuntu 24.10 (Oracular)
- **Kernel** : 6.11.0-29-generic
- **Adresse IP** : 51.254.36.25
- **Domaine** : erp.declaimers.com
- **Utilisateur admin** : erp-admin

### **Stack Technologique**
```
Client (Navigateur) → Nginx (Port 80) → Gunicorn (Port 5000) → Flask App → PostgreSQL
                    ↓
Intégrations Matérielles (ESC/POS, ZKTeco, Tiroir-caisse)
```

### **Nouvelles Intégrations Version 5**
- **Imprimante ESC/POS** : Tickets de vente automatiques
- **Pointeuse ZKTeco** : Pointage biométrique des employés
- **Tiroir-caisse** : Ouverture automatique lors des ventes
- **Services réseau** : Agent d'impression distant

## 🔧 SERVICES PRINCIPAUX

### **1. Application ERP**
- **Framework** : Flask Python 3.12
- **Serveur WSGI** : Gunicorn 23.0.0
- **Service systemd** : erp-fee-maison.service
- **Répertoire** : /opt/erp/app/
- **Environnement virtuel** : /opt/erp/app/venv/
- **Workers** : 4 processus Gunicorn
- **Port d'écoute** : 127.0.0.1:5000

### **2. Serveur Web**
- **Serveur** : Nginx 1.26.0
- **Configuration** : /etc/nginx/sites-enabled/nginx_erp.conf
- **Proxy reverse** : Redirige vers Flask sur port 5000
- **Ports** : 80 (HTTP)
- **SSL** : Désactivé (configuration HTTP uniquement)

### **3. Base de Données**
- **SGBD** : PostgreSQL
- **Nom de la base** : fee_maison_db
- **Utilisateur** : fee_maison_user
- **Mot de passe** : FeeMaison_ERP_2025_Secure!
- **Host** : localhost
- **Port** : 5432

## 🔐 CONFIGURATION SÉCURITÉ

### **Authentification PostgreSQL**
```env
POSTGRES_USER=fee_maison_user
POSTGRES_PASSWORD=FeeMaison_ERP_2025_Secure!
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB_NAME=fee_maison_db
DATABASE_URL=postgresql://fee_maison_user:FeeMaison_ERP_2025_Secure!@localhost:5432/fee_maison_db
```

### **Authentification ERP**
- **Email administrateur** : admin@feemaison.com
- **Mot de passe** : FeeM@ison2025!Prod#

### **Configuration Email SMTP**
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=erpfeemaison@gmail.com
MAIL_PASSWORD=VJFx93hxYLzMdtJ
```

## 🚀 PROCESSUS D'INSTALLATION

### **Étapes d'Installation Réalisées**

1. **Préparation du VPS**
   - Installation Ubuntu 24.10
   - Création utilisateur erp-admin
   - Configuration SSH

2. **Installation des Dépendances**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv postgresql nginx git
   ```

3. **Configuration PostgreSQL**
   ```sql
   CREATE DATABASE fee_maison_db;
   CREATE USER fee_maison_user WITH PASSWORD 'FeeMaison_ERP_2025_Secure!';
   GRANT ALL PRIVILEGES ON DATABASE fee_maison_db TO fee_maison_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fee_maison_user;
   ```

4. **Déploiement de l'Application**
   ```bash
   sudo mkdir -p /opt/erp/app
   cd /opt/erp/app
   git clone https://github.com/infocrasher/ERPFeeMaison.git .
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configuration Systemd**
   - Création du service : /etc/systemd/system/erp-fee-maison.service
   - Activation : sudo systemctl enable erp-fee-maison

6. **Configuration Nginx**
   - Fichier : /etc/nginx/sites-available/nginx_erp.conf
   - Activation : lien symbolique vers sites-enabled

## 📁 STRUCTURE DES RÉPERTOIRES

```
/opt/erp/app/
├── app/                    # Application Flask principale
│   ├── __init__.py
│   ├── models.py          # Modèles de données
│   ├── auth/              # Module d'authentification
│   ├── sales/             # Module de ventes
│   ├── inventory/         # Module de stock
│   ├── hr/                # Module RH
│   ├── accounting/        # Module comptabilité
│   └── static/            # Fichiers statiques (CSS, JS)
├── venv/                  # Environnement virtuel Python
├── .env                   # Variables d'environnement
├── requirements.txt       # Dépendances Python
├── gunicorn.conf.py      # Configuration Gunicorn
└── run.py                # Point d'entrée de l'application
```

## 🔄 PROCESSUS DE MISE À JOUR

### **Workflow Git Standard**

```bash
# 1. Connexion au VPS
ssh erp-admin@51.254.36.25

# 2. Navigation vers le répertoire de l'application
cd /opt/erp/app/

# 3. Récupération des dernières modifications
git pull origin main

# 4. Mise à jour des dépendances (si nécessaire)
source venv/bin/activate
pip install -r requirements.txt

# 5. Redémarrage du service
sudo systemctl restart erp-fee-maison

# 6. Vérification du statut
sudo systemctl status erp-fee-maison
```

### **Vérifications Post-Déploiement**

```bash
# Vérification des logs
sudo journalctl -u erp-fee-maison -f

# Test de connectivité
curl -I http://51.254.36.25/

# Vérification Nginx
sudo systemctl status nginx
```

## 🖥️ ÉTAT ACTUEL DU SYSTÈME

### **Services Opérationnels**

| Service | Statut | PID | Mémoire | CPU |
|---------|--------|-----|---------|-----|
| erp-fee-maison | active (running) | 140336 | 206.7M | 3.426s |
| nginx | active (running) | 28853 | 4.6M | 13.131s |
| postgresql | active (running) | - | - | - |

### **Configuration Réseau**
```bash
# Ports en écoute
tcp   LISTEN 0.0.0.0:80     # Nginx HTTP
tcp   LISTEN 127.0.0.1:5000 # Gunicorn Flask
tcp   LISTEN 127.0.0.1:5432 # PostgreSQL
```

### **Accès Applicatif**
- **URL principale** : http://51.254.36.25
- **URL alternative** : http://erp.declaimers.com
- **Page de connexion** : /auth/login
- **Interface d'administration** : /admin

## 🛠️ MAINTENANCE ET SURVEILLANCE

### **Commandes de Monitoring**

```bash
# Surveillance des services
sudo systemctl status erp-fee-maison nginx postgresql

# Logs en temps réel
sudo journalctl -u erp-fee-maison -f

# Espace disque
df -h

# Mémoire système
free -h

# Processus Python
ps aux | grep python
```

### **Maintenance Préventive**

#### **Quotidienne**
- Vérification des logs d'erreur
- Surveillance de l'utilisation mémoire
- Test d'accès à l'application

#### **Hebdomadaire**
- Sauvegarde de la base de données
- Mise à jour des dépendances système
- Vérification des performances

#### **Mensuelle**
- Mise à jour de sécurité Ubuntu
- Nettoyage des logs anciens
- Optimisation PostgreSQL

## 🔧 RÉSOLUTION DE PROBLÈMES

### **Problèmes Courants et Solutions**

#### **Service ERP ne démarre pas**
```bash
# Vérification des logs
sudo journalctl -u erp-fee-maison -n 50

# Redémarrage du service
sudo systemctl restart erp-fee-maison

# Test de la configuration
cd /opt/erp/app && source venv/bin/activate && python run.py
```

#### **Erreurs de base de données**
```bash
# Vérification des permissions
sudo -u postgres psql -d fee_maison_db -c "\du"

# Réapplication des permissions
sudo -u postgres psql -d fee_maison_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fee_maison_user;"
```

#### **Problèmes Nginx**
```bash
# Test de configuration
sudo nginx -t

# Rechargement
sudo systemctl reload nginx

# Vérification des logs
sudo tail -f /var/log/nginx/error.log
```

## 📊 MODULES ERP DISPONIBLES

### **Modules Opérationnels**
- **Authentification** : Gestion des utilisateurs et sessions
- **Ventes** : Devis, commandes, facturation
- **Stock** : Gestion des produits et inventaire
- **RH** : Gestion des employés et pointeuse ZKTeco
- **Comptabilité** : Écritures comptables et reporting
- **Production** : Gestion des ordres de fabrication
- **Achats** : Gestion des fournisseurs et commandes
- **Livraisons** : Suivi des expéditions

### **Intégrations**
- **Pointeuse ZKTeco** : IP 192.168.1.101, port 4370
- **Notifications Email** : Via Gmail SMTP
- **Système de fichiers** : Gestion des documents

## 🔒 SÉCURITÉ ET SAUVEGARDE

### **Mesures de Sécurité Appliquées**
- **Firewall UFW** : Inactif (ports gérés par hébergeur)
- **Authentification forte** : Mots de passe complexes
- **Environnement isolé** : Variables d'environnement sécurisées
- **Permissions PostgreSQL** : Accès restreint à l'utilisateur dédié

### **Sauvegarde Recommandée**
```bash
# Sauvegarde base de données
pg_dump -U fee_maison_user -h localhost fee_maison_db > backup_$(date +%Y%m%d).sql

# Sauvegarde application
tar -czf erp_backup_$(date +%Y%m%d).tar.gz /opt/erp/app/

# Sauvegarde configuration
cp /etc/nginx/sites-enabled/nginx_erp.conf backup_nginx_$(date +%Y%m%d).conf
```

## 📈 PERFORMANCE ET OPTIMISATION

### **Métriques Actuelles**
- **Temps de réponse** : 200-500ms pour les pages simples
- **Utilisateurs simultanés** : 10-20 supportés
- **Utilisation mémoire** : 206.7M pour l'application
- **Disponibilité** : 99.9% (service auto-restart)

### **Optimisations Possibles**
- **Cache Redis** : Pour améliorer les performances
- **Load balancing** : Pour la scalabilité
- **CDN** : Pour les fichiers statiques
- **Database indexing** : Pour les requêtes fréquentes

## 🎯 RECOMMANDATIONS FUTURES

### **Améliorations Techniques**
1. **Mise en place SSL** : Certificat Let's Encrypt fonctionnel
2. **Monitoring avancé** : Prometheus + Grafana
3. **Conteneurisation** : Migration vers Docker
4. **CI/CD** : Pipeline automatisé avec GitHub Actions

### **Sécurité Renforcée**
1. **Nettoyage historique Git** : Suppression des secrets exposés
2. **Rotation des mots de passe** : Tous les 90 jours
3. **Audit de sécurité** : Scan des vulnérabilités
4. **Backup automatisé** : Sauvegarde quotidienne

**Dernière mise à jour** : 18 juillet 2025  
**Statut système** : ✅ Opérationnel  
**Version ERP** : Production stable  
**Prochaine maintenance** : Selon planification

---

# 📚 Guide d'installation détaillé (historique)

