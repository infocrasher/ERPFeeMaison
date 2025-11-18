# 🖨️ Configuration Hybride Caisse & Imprimante (VPS ↔ SmartPOS)

## 📋 Vue d'ensemble

L'ERP Fée Maison utilise une **architecture hybride** pour gérer la caisse et l'imprimante :

- **Mode Local** : Sur la machine de développement (MacBook), l'ERP accède directement à l'imprimante USB
- **Mode Réseau** : Sur le VPS, l'ERP communique avec un **agent local** qui tourne sur le **SmartPOS Windows**

```
┌─────────────────┐         Internet          ┌──────────────────┐
│   VPS (ERP)     │ ────────────────────────> │  SmartPOS        │
│   (OVH)         │    HTTP/HTTPS              │  (Windows)       │
│                 │                            │  (Navigateur)    │
│ RemotePrinter   │                            └──────┬───────────┘
│ Service         │                                   │
└─────────────────┘                                   │ HTTP API
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

## 📚 Documentation Complète

Pour l'installation sur **SmartPOS Windows**, consultez :
- **`documentation/INSTALLATION_SMARTPOS_WINDOWS.md`** - Guide complet d'installation

## 🔧 Configuration sur le SmartPOS (Windows)

### 1. Installation Automatique (Recommandé)

Utilisez le script d'installation automatique :

```cmd
# Exécuter en tant qu'Administrateur
install_printer_agent_windows.bat
```

Ce script :
- Vérifie Python
- Crée l'environnement virtuel
- Installe les dépendances
- Configure le firewall
- Crée le fichier .env

### 2. Démarrer l'Agent d'Impression

L'agent doit tourner en permanence sur le SmartPOS pour recevoir les requêtes du VPS.

#### Option A : Service Windows (Recommandé)

Utilisez NSSM pour créer un service Windows :

```cmd
# 1. Télécharger NSSM depuis https://nssm.cc/download
# 2. Exécuter le script de création de service
create_windows_service.bat
```

Le service démarrera automatiquement au boot de Windows.

#### Option B : Script de démarrage manuel

```bash
#!/bin/bash
# Démarrer l'agent d'impression sur la machine POS

cd /chemin/vers/fee_maison_gestion_cursor
source venv/bin/activate

# Configuration
export PRINTER_ENABLED=true
export PRINTER_AGENT_HOST=0.0.0.0  # Écouter sur toutes les interfaces
export PRINTER_AGENT_PORT=8080
export PRINTER_AGENT_TOKEN=your_secure_token_here_change_me

# Démarrer l'agent
python -m app.services.printer_agent --host 0.0.0.0 --port 8080 --token $PRINTER_AGENT_TOKEN
```

Rendez-le exécutable :
```bash
chmod +x start_printer_agent.sh
```

#### Option B : Service systemd (Linux) ou LaunchAgent (macOS)

**macOS - LaunchAgent** :

Créez `~/Library/LaunchAgents/com.feemaison.printer-agent.plist` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.feemaison.printer-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>app.services.printer_agent</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8080</string>
        <string>--token</string>
        <string>your_secure_token_here</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/chemin/vers/fee_maison_gestion_cursor</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/printer-agent.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/printer-agent-error.log</string>
</dict>
</plist>
```

Charger le service :
```bash
launchctl load ~/Library/LaunchAgents/com.feemaison.printer-agent.plist
launchctl start com.feemaison.printer-agent
```

### 2. Configuration Firewall

Autoriser le port 8080 sur la machine POS :

**macOS** :
```bash
# Autoriser le port 8080
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/bin/python3
```

**Linux** :
```bash
sudo ufw allow 8080/tcp
```

### 3. Obtenir l'Adresse IP de la Machine POS

```bash
# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Linux
ip addr show | grep "inet " | grep -v 127.0.0.1
```

Notez l'adresse IP (ex: `192.168.1.100`).

### 4. Tester l'Agent Localement

```bash
# Test de santé
curl http://localhost:8080/health

# Test avec token
curl -H "Authorization: Bearer your_secure_token_here" http://localhost:8080/status
```

## 🔧 Configuration sur le VPS

### 1. Variables d'Environnement

Ajoutez dans `.env` sur le VPS :

```bash
# Mode réseau activé
PRINTER_NETWORK_ENABLED=true

# Adresse IP de la machine POS (remplacer par l'IP réelle)
PRINTER_AGENT_HOST=192.168.1.100

# Port de l'agent (doit correspondre à celui de l'agent)
PRINTER_AGENT_PORT=8080

# Token d'authentification (DOIT être identique à celui de l'agent)
PRINTER_AGENT_TOKEN=your_secure_token_here_change_me
```

### 2. Vérifier la Connectivité

Depuis le VPS, testez la connexion à l'agent :

```bash
# Test de santé (sans token)
curl http://192.168.1.100:8080/health

# Test avec token
curl -H "Authorization: Bearer your_secure_token_here" http://192.168.1.100:8080/status
```

### 3. Redémarrer l'Application

```bash
# Redémarrer Gunicorn
sudo systemctl restart gunicorn

# Ou si vous utilisez un autre serveur
sudo systemctl restart fee-maison
```

## 🔒 Sécurité

### 1. Token d'Authentification

**IMPORTANT** : Utilisez un token fort et unique :

```bash
# Générer un token sécurisé
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Utilisez le même token sur :
- La machine POS (dans le script de démarrage de l'agent)
- Le VPS (dans `.env`)

### 2. Réseau Privé

Assurez-vous que :
- La machine POS et le VPS sont sur le même réseau privé (VPN, LAN)
- Le port 8080 n'est pas exposé publiquement
- Utilisez un VPN si la machine POS est distante

### 3. Firewall

Sur le VPS, ne pas ouvrir le port 8080 publiquement. Seule la communication interne est nécessaire.

## 🧪 Tests

### Test 1 : Vérifier l'Agent sur la Machine POS

```bash
# Sur la machine POS
curl http://localhost:8080/health
# Devrait retourner : {"status": "healthy", ...}
```

### Test 2 : Vérifier depuis le VPS

```bash
# Sur le VPS
curl http://192.168.1.100:8080/health
# Devrait retourner : {"status": "healthy", ...}
```

### Test 3 : Test d'Impression depuis le VPS

Via l'interface admin de l'ERP sur le VPS :
- Aller à `/admin/printer/`
- Cliquer sur "Test Impression"
- L'imprimante sur la machine POS devrait imprimer

### Test 4 : Test d'Ouverture de Caisse

Via l'interface admin :
- Cliquer sur "Ouvrir Tiroir-Caisse"
- Le tiroir sur la machine POS devrait s'ouvrir

## 🐛 Dépannage

### Problème : Agent non accessible depuis le VPS

**Vérifications** :
1. L'agent tourne-t-il sur la machine POS ?
   ```bash
   # Sur la machine POS
   ps aux | grep printer_agent
   ```

2. Le port 8080 est-il ouvert ?
   ```bash
   # Sur la machine POS
   lsof -i :8080
   ```

3. Le firewall bloque-t-il le port ?
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps
   ```

4. L'IP est-elle correcte ?
   ```bash
   # Sur la machine POS
   ifconfig | grep "inet "
   ```

### Problème : Token invalide

**Vérifications** :
1. Le token est-il identique sur les deux machines ?
2. Le header Authorization est-il correct ?
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" http://192.168.1.100:8080/status
   ```

### Problème : Imprimante non détectée

**Vérifications** :
1. L'imprimante est-elle connectée en USB sur la machine POS ?
2. Les permissions USB sont-elles correctes ?
   ```bash
   # macOS : Vérifier dans Préférences Système > Sécurité
   # Linux : Ajouter l'utilisateur au groupe dialout
   sudo usermod -a -G dialout $USER
   ```

### Problème : Timeout des requêtes

**Solutions** :
1. Augmenter le timeout dans `printer_service.py`
2. Vérifier la latence réseau entre VPS et POS
3. Vérifier que le port n'est pas bloqué par un proxy

## 📊 Monitoring

### Logs de l'Agent

Sur la machine POS, les logs sont dans :
- `/tmp/printer-agent.log` (si configuré avec LaunchAgent)
- Sortie console (si lancé manuellement)

### Statut via API

```bash
# Statut détaillé
curl -H "Authorization: Bearer YOUR_TOKEN" http://192.168.1.100:8080/status
```

Retourne :
```json
{
  "agent": {
    "host": "0.0.0.0",
    "port": 8080,
    "uptime": "2:30:15",
    "stats": {
      "requests_received": 42,
      "print_jobs": 35,
      "drawer_jobs": 7,
      "errors": 0
    }
  },
  "printer": {
    "enabled": true,
    "running": true,
    "connected": true,
    "queue_size": 0
  }
}
```

## 🔄 Mise à Jour

### Mettre à jour l'Agent

1. Arrêter l'agent sur la machine POS
2. Mettre à jour le code
3. Redémarrer l'agent

### Mettre à jour le VPS

1. Mettre à jour le code
2. Redémarrer Gunicorn

## 📝 Checklist de Déploiement

- [ ] Agent démarré sur la machine POS
- [ ] Port 8080 ouvert sur la machine POS
- [ ] IP de la machine POS notée
- [ ] Token sécurisé généré et configuré
- [ ] Variables d'environnement configurées sur le VPS
- [ ] Test de connectivité réussi depuis le VPS
- [ ] Test d'impression réussi
- [ ] Test d'ouverture de caisse réussi
- [ ] Service configuré pour démarrage automatique (optionnel)

## 🆘 Support

En cas de problème :
1. Vérifier les logs de l'agent
2. Vérifier les logs de l'ERP sur le VPS
3. Tester la connectivité réseau
4. Vérifier les permissions USB

