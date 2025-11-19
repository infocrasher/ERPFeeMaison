# 🏗️ Architecture d'Impression - Déploiement VPS

## 📋 Vue d'Ensemble

L'ERP utilise une **architecture hybride** pour l'impression :

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS (Cloud - OVH)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ERP Flask Application                               │  │
│  │  - RemotePrinterService (client HTTP)                │  │
│  │  - NO USB access                                     │  │
│  │  - NO pyusb required                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/HTTPS
                          │ (Internet)
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              SmartPOS (Windows - Magasin)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PrinterAgent (Flask HTTP Server)                    │  │
│  │  - Port 8080                                         │  │
│  │  - Token authentication                              │  │
│  │  - PrinterService (USB access)                      │  │
│  │  - pyusb REQUIRED                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          │ USB                               │
│                          ▼                                   │
│              ┌──────────────────────────┐                   │
│              │  Imprimante Thermique    │                   │
│              │  + Tiroir-Caisse        │                   │
│              └──────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Problème Identifié

**Le fichier `printer_service.py` importe `usb.core` au niveau du module**, même si le VPS n'a pas besoin d'USB.

### Solution : Import Conditionnel

Le code doit importer `usb` **uniquement** si :
- `PRINTER_ENABLED=true` ET
- `PRINTER_NETWORK_ENABLED=false` (mode local)

Sinon, l'import doit être **lazy** (dans les méthodes qui l'utilisent).

## 📦 Dépendances Manquantes dans `requirements.txt`

### ✅ Dépendances Identifiées

1. **`num2words`** - Utilisé dans `app/utils/filters.py`
   - Pour convertir les montants en lettres (factures)
   - **Nécessaire pour la production**

2. **`pyusb`** - Utilisé dans `app/services/printer_service.py`
   - **UNIQUEMENT nécessaire sur le SmartPOS (Windows)**
   - **PAS nécessaire sur le VPS** si `PRINTER_NETWORK_ENABLED=true`

### 📝 Recommandation

Créer **deux fichiers requirements** :
- `requirements.txt` - Pour le VPS (sans pyusb)
- `requirements-pos.txt` - Pour le SmartPOS (avec pyusb)

## ⚙️ Configuration `.env` pour le VPS

### Variables Obligatoires

```env
# ========================================
# MODE DÉPLOIEMENT : VPS (Cloud)
# ========================================
FLASK_ENV=production

# ========================================
# IMPRESSION : Mode Réseau (Agent Distant)
# ========================================
# Désactiver l'accès USB direct
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
# AUTRES CONFIGURATIONS
# ========================================
# ... (DB, SECRET_KEY, etc.)
```

### Génération du Token

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🔒 Sécurité

### 1. Firewall SmartPOS

Le SmartPOS doit autoriser les connexions entrantes sur le port 8080 **uniquement depuis l'IP du VPS** :

```bash
# Windows Firewall
netsh advfirewall firewall add rule name="ERP Printer Agent" dir=in action=allow protocol=TCP localport=8080 remoteip=51.254.36.25
```

### 2. Token d'Authentification

- **Ne JAMAIS** commiter le token dans Git
- Utiliser un token différent pour chaque environnement
- Régénérer le token si compromis

### 3. HTTPS (Recommandé)

Pour la production, utiliser HTTPS entre VPS et SmartPOS :
- Certificat SSL auto-signé (pour IP)
- Ou tunnel sécurisé (Cloudflare Tunnel, ngrok)

## 🚀 Déploiement

### Sur le VPS

1. **Installer les dépendances** (sans pyusb) :
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer `.env`** avec les variables ci-dessus

3. **Vérifier la connexion** :
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://SMARTPOS_IP:8080/health
   ```

### Sur le SmartPOS

1. **Installer les dépendances** (avec pyusb) :
   ```bash
   pip install -r requirements-pos.txt
   ```

2. **Configurer `.env`** :
   ```env
   PRINTER_ENABLED=true
   PRINTER_NETWORK_ENABLED=false
   PRINTER_VENDOR_ID=0471
   PRINTER_PRODUCT_ID=0055
   PRINTER_AGENT_HOST=0.0.0.0
   PRINTER_AGENT_PORT=8080
   PRINTER_AGENT_TOKEN=your_secure_token_here_change_me
   ```

3. **Démarrer l'agent** :
   ```bash
   python -m app.services.printer_agent
   ```

## ✅ Checklist Déploiement VPS

- [ ] `PRINTER_ENABLED=false` dans `.env`
- [ ] `PRINTER_NETWORK_ENABLED=true` dans `.env`
- [ ] `PRINTER_AGENT_HOST` configuré (IP ou domaine SmartPOS)
- [ ] `PRINTER_AGENT_TOKEN` généré et configuré
- [ ] `num2words` ajouté à `requirements.txt`
- [ ] `pyusb` **NON installé** sur le VPS
- [ ] Code corrigé pour import conditionnel de `usb`
- [ ] Test de connexion à l'agent SmartPOS réussi

