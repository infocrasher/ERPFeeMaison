# ✅ Checklist Variables d'Environnement VPS

## 🔐 Variables OBLIGATOIRES (à configurer absolument)

Ces variables **DOIVENT** être dans le fichier `.env` sur le VPS (`/opt/erp/app/.env`).

### 1. Sécurité Flask
```env
SECRET_KEY=your_super_secret_key_here_change_this
```
**⚠️ CRITIQUE** : Générer avec :
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Base de Données PostgreSQL
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fee_maison_db
DB_USER=erp_user
POSTGRES_PASSWORD=your_secure_password_here
```
**⚠️ CRITIQUE** : Le mot de passe PostgreSQL que tu as créé lors de l'installation.

### 3. Clés API IA (si tu utilises les fonctionnalités IA)
```env
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```
**⚠️ IMPORTANT** : Ces clés doivent être dans le `.env` du VPS.  
**Note** : Les vraies clés sont disponibles dans le fichier `.env` local (non commité).

### 4. Impression (Mode Réseau)
```env
PRINTER_ENABLED=false
PRINTER_NETWORK_ENABLED=true
PRINTER_AGENT_HOST=xxx.xxx.xxx.xxx  # IP du SmartPOS
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=your_secure_token_here
```
**⚠️ CRITIQUE** : `PRINTER_AGENT_TOKEN` doit être généré :
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📋 Variables OPTIONNELLES (selon besoins)

### Pointeuse ZKTeco (si accessible depuis VPS)
```env
ZK_ENABLED=false  # ou true si pointeuse accessible
ZK_IP=192.168.1.100
ZK_PORT=4370
ZK_PASSWORD=your_zk_password
ZK_API_PASSWORD=your_zk_api_password
```

### Email (si tu veux envoyer des emails)
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

### Redis (si tu utilises le cache)
```env
REDIS_URL=redis://localhost:6379/0
```

---

## 🔍 Comment Vérifier sur le VPS

### 1. Vérifier que le fichier `.env` existe
```bash
cd /opt/erp/app
ls -la .env
```

### 2. Vérifier les variables chargées
```bash
cd /opt/erp/app
./venv/bin/python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('SECRET_KEY:', '✅' if os.getenv('SECRET_KEY') else '❌ MANQUANT')
print('DB_NAME:', os.getenv('DB_NAME', '❌ MANQUANT'))
print('POSTGRES_PASSWORD:', '✅' if os.getenv('POSTGRES_PASSWORD') else '❌ MANQUANT')
print('PRINTER_NETWORK_ENABLED:', os.getenv('PRINTER_NETWORK_ENABLED', '❌ MANQUANT'))
print('OPENAI_API_KEY:', '✅' if os.getenv('OPENAI_API_KEY') else '❌ MANQUANT')
print('GROQ_API_KEY:', '✅' if os.getenv('GROQ_API_KEY') else '❌ MANQUANT')
"
```

### 3. Vérifier les permissions du fichier `.env`
```bash
ls -l /opt/erp/app/.env
# Doit afficher : -rw------- (600) pour la sécurité
```

Si les permissions ne sont pas bonnes :
```bash
chmod 600 /opt/erp/app/.env
```

---

## 📝 Template Complet `.env` pour VPS

```env
# ========================================
# ENVIRONNEMENT
# ========================================
FLASK_ENV=production
FLASK_APP=app
DEBUG=False

# ========================================
# SÉCURITÉ (OBLIGATOIRE)
# ========================================
SECRET_KEY=GÉNÉRER_AVEC_SECRETS_TOKEN_URLSAFE_32

# ========================================
# BASE DE DONNÉES (OBLIGATOIRE)
# ========================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fee_maison_db
DB_USER=erp_user
POSTGRES_PASSWORD=TON_MOT_DE_PASSE_POSTGRES

# ========================================
# IMPRESSION (OBLIGATOIRE pour mode réseau)
# ========================================
PRINTER_ENABLED=false
PRINTER_NETWORK_ENABLED=true
PRINTER_AGENT_HOST=IP_DU_SMARTPOS
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=GÉNÉRER_AVEC_SECRETS_TOKEN_URLSAFE_32

# ========================================
# IA (OBLIGATOIRE si tu utilises les analyses IA)
# ========================================
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# ========================================
# POINTEUSE (Optionnel)
# ========================================
ZK_ENABLED=false

# ========================================
# EMAIL (Optionnel)
# ========================================
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your_email@gmail.com
# MAIL_PASSWORD=your_app_password

# ========================================
# REDIS (Optionnel)
# ========================================
# REDIS_URL=redis://localhost:6379/0
```

---

## ⚠️ Points Critiques

1. **SECRET_KEY** : **OBLIGATOIRE** - Sans ça, les sessions Flask ne fonctionnent pas
2. **POSTGRES_PASSWORD** : **OBLIGATOIRE** - Sans ça, pas de connexion DB
3. **PRINTER_AGENT_TOKEN** : **OBLIGATOIRE** si tu utilises l'impression réseau
4. **Clés API IA** : **OBLIGATOIRE** si tu utilises les analyses IA (dashboard, rapports)

---

## 🚨 Si une Variable Manque

Si une variable obligatoire manque, l'application peut :
- ❌ Ne pas démarrer
- ❌ Avoir des erreurs de connexion DB
- ❌ Avoir des erreurs de sessions (SECRET_KEY)
- ❌ Ne pas pouvoir utiliser l'IA (clés API manquantes)

**Solution** : Ajouter la variable dans `/opt/erp/app/.env` puis redémarrer :
```bash
sudo systemctl restart erp-fee-maison
```

