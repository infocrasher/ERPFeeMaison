# 🖨️ Installation Agent d'Impression sur SmartPOS (Windows)

## 📋 Vue d'ensemble

Le SmartPOS Windows doit exécuter un **agent d'impression** qui :
- Écoute les requêtes du VPS
- Contrôle l'imprimante USB locale
- Ouvre le tiroir-caisse

```
┌─────────────┐         Internet          ┌──────────────┐
│     VPS     │ ────────────────────────> │  SmartPOS    │
│   (OVH)     │    HTTP/HTTPS              │  (Windows)   │
│   (ERP)     │                            │              │
└─────────────┘                            └──────┬───────┘
                                                   │
                                                   │ Agent HTTP
                                                   │ Port 8080
                                                   ▼
                                            ┌──────────────┐
                                            │ Agent Local  │
                                            │ (Python)     │
                                            └──────┬───────┘
                                                   │
                                                   │ USB
                                                   ▼
                                            ┌──────────────┐
                                            │ Imprimante   │
                                            │ + Tiroir     │
                                            └──────────────┘
```

## 🔧 Installation sur SmartPOS (Windows)

### Étape 1 : Installer Python

1. Télécharger Python 3.11+ depuis [python.org](https://www.python.org/downloads/)
2. **IMPORTANT** : Cocher "Add Python to PATH" lors de l'installation
3. Vérifier l'installation :
   ```cmd
   python --version
   pip --version
   ```

### Étape 2 : Cloner/Transférer le Projet

**Option A : Git (si disponible)**
```cmd
cd C:\
git clone https://github.com/votre-repo/fee_maison_gestion_cursor.git
cd fee_maison_gestion_cursor
```

**Option B : Transfert manuel**
- Copier le dossier du projet depuis le MacBook vers `C:\fee_maison_gestion_cursor`

### Étape 3 : Créer l'Environnement Virtuel

```cmd
cd C:\fee_maison_gestion_cursor
python -m venv venv
venv\Scripts\activate
```

### Étape 4 : Installer les Dépendances

```cmd
pip install flask requests pyusb
```

**Note pour pyusb sur Windows** :
- Installer [Zadig](https://zadig.akeo.ie/) pour configurer le driver USB
- Ou utiliser `libusb-win32` ou `libusbK`

### Étape 5 : Configuration

Créer un fichier `.env` dans le dossier du projet :

```env
# Configuration Agent d'Impression SmartPOS
PRINTER_ENABLED=true
PRINTER_VENDOR_ID=0471
PRINTER_PRODUCT_ID=0055
PRINTER_INTERFACE=0
PRINTER_TIMEOUT=5000

# Agent HTTP (écoute sur toutes les interfaces)
PRINTER_AGENT_HOST=0.0.0.0
PRINTER_AGENT_PORT=8080

# Token d'authentification (GÉNÉRER UN TOKEN SÉCURISÉ !)
PRINTER_AGENT_TOKEN=your_secure_token_here_change_me

PRINTER_LOG_LEVEL=INFO
```

**Générer un token sécurisé** :
```cmd
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Étape 6 : Tester l'Agent

```cmd
venv\Scripts\activate
python -m app.services.printer_agent --host 0.0.0.0 --port 8080 --token YOUR_TOKEN
```

Vous devriez voir :
```
🖨️ Démarrage agent imprimante sur 0.0.0.0:8080
 * Running on http://0.0.0.0:8080
```

### Étape 7 : Configurer le Firewall Windows

Autoriser le port 8080 :

```cmd
# Ouvrir PowerShell en Administrateur
netsh advfirewall firewall add rule name="ERP Printer Agent" dir=in action=allow protocol=TCP localport=8080
```

### Étape 8 : Obtenir l'Adresse IP du SmartPOS

```cmd
ipconfig
```

Notez l'adresse IPv4 (ex: `192.168.1.50`).

**Si le SmartPOS est derrière un routeur** :
- Vous devrez configurer le port forwarding sur le routeur
- Ou utiliser un tunnel (voir section "Tunnel Sécurisé" ci-dessous)

## 🔧 Configuration sur le VPS

### Étape 1 : Variables d'Environnement

Ajouter dans `.env` sur le VPS :

```env
# Mode réseau activé
PRINTER_NETWORK_ENABLED=true

# Adresse IP du SmartPOS
# Option 1 : IP publique (si routeur configuré avec port forwarding)
PRINTER_AGENT_HOST=votre-ip-publique-ou-domaine.com

# Option 2 : IP locale si même réseau (peu probable)
# PRINTER_AGENT_HOST=192.168.1.50

# Port de l'agent
PRINTER_AGENT_PORT=8080

# Token (MÊME que sur SmartPOS)
PRINTER_AGENT_TOKEN=your_secure_token_here_change_me
```

### Étape 2 : Redémarrer l'Application

```bash
sudo systemctl restart gunicorn
# ou
sudo systemctl restart fee-maison
```

## 🔒 Solution : Tunnel Sécurisé (Recommandé)

Si le SmartPOS est derrière un NAT/routeur, utiliser un tunnel :

### Option A : Cloudflare Tunnel (Gratuit, Recommandé)

**Sur le SmartPOS** :

1. Installer `cloudflared` :
   ```cmd
   # Télécharger depuis https://github.com/cloudflare/cloudflared/releases
   # Extraire cloudflared.exe dans C:\cloudflared\
   ```

2. Créer un tunnel :
   ```cmd
   cd C:\cloudflared
   cloudflared tunnel create printer-agent
   cloudflared tunnel route dns printer-agent printer-agent.votre-domaine.com
   ```

3. Créer `config.yml` :
   ```yaml
   tunnel: printer-agent
   credentials-file: C:\cloudflared\printer-agent.json
   
   ingress:
     - hostname: printer-agent.votre-domaine.com
       service: http://localhost:8080
     - service: http_status:404
   ```

4. Démarrer le tunnel :
   ```cmd
   cloudflared tunnel run printer-agent
   ```

5. Configurer le VPS :
   ```env
   PRINTER_AGENT_HOST=printer-agent.votre-domaine.com
   PRINTER_AGENT_PORT=443
   ```

### Option B : ngrok (Simple mais moins sécurisé)

**Sur le SmartPOS** :

1. Télécharger ngrok depuis [ngrok.com](https://ngrok.com/)
2. Créer un compte et obtenir un token
3. Configurer :
   ```cmd
   ngrok config add-authtoken YOUR_TOKEN
   ngrok http 8080
   ```
4. Utiliser l'URL fournie (ex: `https://abc123.ngrok.io`) dans le VPS

## 🚀 Démarrage Automatique (Service Windows)

### Créer un Service Windows avec NSSM

1. Télécharger [NSSM](https://nssm.cc/download)
2. Extraire dans `C:\nssm\`
3. Créer le service :

```cmd
cd C:\nssm\win64
nssm install PrinterAgent
```

Configurer :
- **Path** : `C:\fee_maison_gestion_cursor\venv\Scripts\python.exe`
- **Startup directory** : `C:\fee_maison_gestion_cursor`
- **Arguments** : `-m app.services.printer_agent --host 0.0.0.0 --port 8080 --token YOUR_TOKEN`

4. Démarrer le service :
```cmd
nssm start PrinterAgent
```

5. Vérifier :
```cmd
nssm status PrinterAgent
```

## 🧪 Tests

### Test 1 : Agent Local (SmartPOS)

```cmd
curl http://localhost:8080/health
```

### Test 2 : Depuis le VPS

```bash
# Sur le VPS
curl http://IP_SMARTPOS:8080/health
# ou
curl https://printer-agent.votre-domaine.com/health
```

### Test 3 : Avec Token

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://IP_SMARTPOS:8080/status
```

### Test 4 : Test d'Impression

Via l'interface admin de l'ERP sur le VPS :
- Aller à `/admin/printer/`
- Cliquer sur "Test Impression"

## 🐛 Dépannage

### Problème : Agent ne démarre pas

**Vérifications** :
1. Python installé et dans le PATH
2. Dépendances installées : `pip list | findstr flask`
3. Port 8080 libre : `netstat -an | findstr 8080`

### Problème : Imprimante non détectée

**Solutions** :
1. Installer le driver USB avec Zadig
2. Vérifier les permissions administrateur
3. Tester avec : `python -c "import usb.core; print(usb.core.find(idVendor=0x0471))"`

### Problème : VPS ne peut pas accéder à l'agent

**Solutions** :
1. Vérifier le firewall Windows
2. Vérifier le port forwarding sur le routeur
3. Utiliser un tunnel (Cloudflare ou ngrok)
4. Vérifier que l'IP est correcte

### Problème : Token invalide

**Vérifications** :
1. Le token est identique sur SmartPOS et VPS
2. Le header Authorization est correct
3. Pas d'espaces dans le token

## 📊 Monitoring

### Vérifier le Service

```cmd
nssm status PrinterAgent
```

### Logs

Les logs sont dans la console si lancé manuellement, ou configurer NSSM pour rediriger vers un fichier.

### Statut via API

```cmd
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/status
```

## 📝 Checklist de Déploiement

- [ ] Python installé sur SmartPOS
- [ ] Projet copié sur SmartPOS
- [ ] Environnement virtuel créé
- [ ] Dépendances installées
- [ ] Fichier `.env` configuré avec token
- [ ] Agent testé localement
- [ ] Firewall Windows configuré
- [ ] IP du SmartPOS notée
- [ ] Port forwarding configuré (ou tunnel)
- [ ] Variables d'environnement configurées sur VPS
- [ ] Test de connectivité depuis VPS réussi
- [ ] Service Windows créé (optionnel)
- [ ] Test d'impression réussi
- [ ] Test d'ouverture de caisse réussi

## 🆘 Support

En cas de problème :
1. Vérifier les logs de l'agent
2. Vérifier les logs de l'ERP sur le VPS
3. Tester la connectivité réseau
4. Vérifier les permissions USB

