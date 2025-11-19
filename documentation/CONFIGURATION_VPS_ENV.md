# ⚙️ Configuration `.env` pour VPS (Production)

## 📋 Variables Obligatoires

Copiez ce fichier vers `.env` sur le VPS et remplissez les valeurs :

```env
# ========================================
# ENVIRONNEMENT
# ========================================
FLASK_ENV=production
FLASK_APP=app
DEBUG=False

# ========================================
# SÉCURITÉ
# ========================================
# Générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_super_secret_key_here_change_this

# ========================================
# BASE DE DONNÉES POSTGRESQL
# ========================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fee_maison_db
DB_USER=erp_user
POSTGRES_PASSWORD=your_secure_password_here

# ========================================
# IMPRESSION : Mode Réseau (Agent Distant)
# ========================================
# Désactiver l'accès USB direct (VPS n'a pas d'USB)
PRINTER_ENABLED=false

# Activer le mode réseau (communication avec SmartPOS)
PRINTER_NETWORK_ENABLED=true

# Adresse IP publique ou domaine du SmartPOS
# Option 1 : IP publique (si SmartPOS a IP fixe)
PRINTER_AGENT_HOST=xxx.xxx.xxx.xxx

# Option 2 : Domaine (si SmartPOS accessible via domaine)
# PRINTER_AGENT_HOST=smartpos.feemaison.dz

# Port de l'agent (par défaut 8080)
PRINTER_AGENT_PORT=8080

# Token d'authentification (GÉNÉRER UN TOKEN SÉCURISÉ !)
# Générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
PRINTER_AGENT_TOKEN=your_secure_token_here_change_me

# ========================================
# POINTEUSE ZKTECO (Optionnel)
# ========================================
# Si la pointeuse est accessible depuis le VPS
ZK_ENABLED=false
ZK_IP=
ZK_PORT=4370
ZK_PASSWORD=
ZK_API_PASSWORD=

# ========================================
# CONFIGURATION IA (OpenAI/Groq)
# ========================================
# ⚠️  ATTENTION: Ne jamais commiter de vraies clés API !
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# ========================================
# REDIS (Optionnel - pour cache/sessions)
# ========================================
REDIS_URL=redis://localhost:6379/0

# ========================================
# EMAIL (Optionnel)
# ========================================
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here

# ========================================
# NGINX (Optionnel - si reverse proxy)
# ========================================
NGINX_SERVER_NAME=your_domain.com
```

## 🔑 Génération des Secrets

### SECRET_KEY
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### PRINTER_AGENT_TOKEN
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## ✅ Vérification

Après configuration, vérifier :

```bash
# Vérifier que les variables sont chargées
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('PRINTER_ENABLED:', os.getenv('PRINTER_ENABLED')); print('PRINTER_NETWORK_ENABLED:', os.getenv('PRINTER_NETWORK_ENABLED'))"

# Tester la connexion à l'agent SmartPOS
curl -H "Authorization: Bearer YOUR_TOKEN" http://SMARTPOS_IP:8080/health
```

## ⚠️ Sécurité

- **NE JAMAIS** commiter le fichier `.env` dans Git
- Utiliser des tokens différents pour chaque environnement
- Changer les mots de passe par défaut
- Restreindre l'accès au fichier `.env` :
  ```bash
  chmod 600 .env
  ```

