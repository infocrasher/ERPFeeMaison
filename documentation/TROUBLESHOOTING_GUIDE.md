# 🔍 Diagnostic Complet ERP Flask - Solutions et Corrections

## 📋 Résumé du Problème

**Problème principal :** Le service systemd `erp-fee-maison.service` échoue avec le statut `1/FAILURE`.

**Cause identifiée :** Configuration incorrecte du point d'entrée WSGI et variables d'environnement manquantes.

## 🆕 Nouveaux Problèmes Version 5

### **Problèmes d'Inventaires**
- **Erreur TypeError** : `float * decimal.Decimal` lors de la saisie des quantités
- **Solution** : Conversion explicite des types dans `calculate_variance()`

### **Problèmes de Consommables**
- **Erreur SQLAlchemy** : Relations incorrectes avec `Product.category`
- **Solution** : Utilisation de `.has(name='...')` pour les relations

### **Problèmes d'Autocomplétion**
- **Listes vides** : Catégories incorrectes dans les requêtes
- **Solution** : Correction des noms de catégories ('Boite Consomable', 'Gateaux ')

---

## ✅ Solutions Appliquées

### 1. **Création du fichier WSGI (`wsgi.py`)**

**Problème :** Gunicorn cherchait `app:app` mais le point d'entrée était incorrect.

**Solution :** Création d'un fichier WSGI dédié :
```python
#!/usr/bin/env python3
import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV') or 'production')
application = app  # Pour compatibilité
```

### 2. **Correction du service systemd**

**Problème :** Variables d'environnement manquantes et configuration incorrecte.

**Solution :** Mise à jour du service avec toutes les variables nécessaires :
```ini
[Service]
Environment=FLASK_APP=wsgi.py
Environment=FLASK_ENV=production
Environment=POSTGRES_USER=erp_user
Environment=POSTGRES_PASSWORD=${DB_PASSWORD}
Environment=POSTGRES_HOST=localhost
Environment=POSTGRES_PORT=5432
Environment=POSTGRES_DB_NAME=fee_maison_db
Environment=SECRET_KEY=${SECRET_KEY}
ExecStart=/var/www/erp-fee-maison/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8080 --timeout 120 --access-logfile /var/log/erp-fee-maison/access.log --error-logfile /var/log/erp-fee-maison/error.log wsgi:app
```

### 3. **Amélioration de la configuration PostgreSQL**

**Problème :** Variables d'environnement non standardisées.

**Solution :** Configuration flexible qui accepte plusieurs formats :
```python
class ProductionConfig(Config):
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or os.environ.get('DB_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or os.environ.get('DB_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or os.environ.get('DB_PORT', '5432')
    POSTGRES_DB_NAME = os.environ.get('POSTGRES_DB_NAME') or os.environ.get('DB_NAME')
```

### 4. **Ajout de Gunicorn aux dépendances**

**Problème :** Gunicorn manquant dans `requirements.txt`.

**Solution :** Ajout de `gunicorn==23.0.0` aux dépendances.

---

## 🛠️ Outils de Diagnostic Créés

### 1. **Script de diagnostic complet (`diagnostic_erp.py`)**

Tests automatisés pour :
- ✅ Version Python
- ✅ Structure des fichiers
- ✅ Dépendances Python
- ✅ Variables d'environnement
- ✅ Permissions
- ✅ Application Flask
- ✅ Fichier WSGI
- ✅ Gunicorn
- ✅ Connexion base de données

### 2. **Script de démarrage alternatif (`start_erp.sh`)**

Démarrage manuel avec :
- 🔧 Configuration automatique
- 📋 Chargement des variables d'environnement
- 🔍 Diagnostic préalable
- 📝 Logs détaillés

---

## 📋 Instructions de Déploiement VPS

### **Étape 1 : Préparation**
```bash
cd /opt/erp/app
git clone https://github.com/infocrasher/ERPFeeMaison.git .
chmod +x deploy_vps.sh
./deploy_vps.sh
```

### **Étape 2 : Configuration**
```bash
# Configurer PostgreSQL
chmod +x setup_postgresql.sh
./setup_postgresql.sh

# Configurer l'email dans .env
nano .env
```

### **Étape 3 : Test de diagnostic**
```bash
chmod +x diagnostic_erp.py
python3 diagnostic_erp.py
```

### **Étape 4 : Démarrage**
```bash
# Option A : Service systemd
sudo cp erp-fee-maison.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable erp-fee-maison
sudo systemctl start erp-fee-maison

# Option B : Démarrage manuel
chmod +x start_erp.sh
./start_erp.sh
```

---

## 🔍 Commandes de Diagnostic

### **Vérification du service**
```bash
sudo systemctl status erp-fee-maison
sudo journalctl -u erp-fee-maison -f
```

### **Test de l'application**
```bash
# Test complet
python3 diagnostic_erp.py

# Test manuel
curl http://localhost:8080
```

### **Vérification de la base de données**
```bash
sudo -u postgres psql -d fee_maison_db -c "SELECT 1;"
```

---

## 🚨 Problèmes Courants et Solutions

### **1. Service échoue immédiatement**
```bash
# Vérifier les logs
sudo journalctl -u erp-fee-maison -n 50

# Vérifier la configuration
sudo systemctl cat erp-fee-maison

# Tester manuellement
./start_erp.sh
```

### **2. Erreur de connexion à la base**
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Vérifier les variables
sudo -u www-data env | grep POSTGRES

# Tester la connexion
sudo -u www-data venv/bin/python -c "
from app import create_app
from extensions import db
app = create_app('production')
with app.app_context():
    db.engine.execute('SELECT 1')
    print('OK')
"
```

### **3. Erreur de permissions**
```bash
sudo chown -R www-data:www-data /var/www/erp-fee-maison
sudo chmod -R 755 /var/www/erp-fee-maison
sudo chmod 644 /var/www/erp-fee-maison/.env
```

### **4. Port déjà utilisé**
```bash
sudo netstat -tulpn | grep :8080
sudo pkill -f gunicorn
```

---

## 📊 Structure Finale du Projet

```
erp-fee-maison/
├── wsgi.py                    # ✅ NOUVEAU - Point d'entrée WSGI
├── diagnostic_erp.py          # ✅ NOUVEAU - Script de diagnostic
├── start_erp.sh              # ✅ NOUVEAU - Démarrage alternatif
├── deploy_vps.sh             # ✅ CORRIGÉ - Service systemd
├── app/
│   └── __init__.py           # ✅ Application factory
├── config.py                 # ✅ CORRIGÉ - Configuration flexible
├── requirements.txt          # ✅ CORRIGÉ - Gunicorn ajouté
├── models.py                 # ✅ Modèles SQLAlchemy
├── extensions.py             # ✅ Extensions Flask
└── .env                      # ✅ Variables d'environnement
```

---

## 🎯 Points Clés de la Solution

1. **Point d'entrée WSGI correct** : `wsgi:app` au lieu de `app:app`
2. **Variables d'environnement complètes** : Toutes les variables PostgreSQL définies
3. **Configuration flexible** : Support de plusieurs formats de variables
4. **Outils de diagnostic** : Tests automatisés pour identifier les problèmes
5. **Démarrage alternatif** : Option manuelle pour les tests et débogage
6. **Logs détaillés** : Fichiers de logs séparés pour access et error

---

## ✅ Validation de la Solution

Pour valider que tout fonctionne :

1. **Exécuter le diagnostic** : `python3 diagnostic_erp.py`
2. **Tester le démarrage** : `./start_erp.sh`
3. **Vérifier l'application** : `curl http://localhost:8080`
4. **Contrôler les logs** : `tail -f logs/access.log`

Si tous ces tests passent, l'ERP est prêt pour la production ! 🚀 