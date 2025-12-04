# 🕐 Configuration Pointeuse ZKTeco sur le VPS

**Date:** 4 décembre 2025  
**Statut:** Instructions de reconfiguration

---

## 🐛 Problème identifié

La configuration `ZKTECO_IP` et `ZKTECO_PORT` a été perdue dans le fichier `config.py`, empêchant la pointeuse d'envoyer les données à l'ERP.

**Dernier pointage de la pointeuse:** À vérifier avec `python3 scripts/historique_pointages.py`

---

## 🔧 Solution : Reconfiguration complète

### 1️⃣ Ajouter les variables d'environnement sur le VPS

```bash
# Se connecter au VPS
ssh erp-admin@51.254.36.25

# Éditer le fichier .env (ou créer s'il n'existe pas)
cd /opt/erp/app
nano .env
```

Ajouter ces lignes :
```bash
# Configuration Pointeuse ZKTeco
ZKTECO_IP=192.168.1.XXX    # Remplacer par l'IP réelle de votre pointeuse
ZKTECO_PORT=4370
```

**Note :** Vous devez trouver l'IP de la pointeuse sur votre réseau local. Vérifiez :
- Les paramètres de la pointeuse (menu réseau)
- Votre routeur (liste des appareils connectés)
- Ou utilisez : `nmap -sn 192.168.1.0/24` (scanner le réseau)

### 2️⃣ Mettre à jour le code

```bash
cd /opt/erp/app
git pull origin main
sudo systemctl restart erp
```

### 3️⃣ Vérifier la configuration

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/diagnostic_pointeuse_zkteco.py
```

Vous devriez voir :
```
1️⃣  CONFIGURATION
----------------------------------------------------------------------------------------------------
   IP Pointeuse    : 192.168.1.XXX
   Port           : 4370
```

---

## 🔗 Configurer la pointeuse pour envoyer à l'ERP

### A. Trouver l'URL de votre ERP

**Option 1 - Si le VPS et la pointeuse sont sur le même réseau local :**
```
http://IP_VPS_LOCAL:5000/zkteco/api/attendance
```

**Option 2 - Via Internet (domaine) :**
```
https://erp.declaimers.com/zkteco/api/attendance
```

### B. Configurer la pointeuse

1. **Accéder au menu de la pointeuse**
   - Menu → Communication → Cloud
   - Ou Menu → System → Communication

2. **Paramètres à configurer :**
   - **URL Push** : `http://VOTRE_IP:5000/zkteco/api/attendance`
   - **Méthode** : POST
   - **Format** : JSON
   - **Intervalle** : 30 secondes (ou temps réel)

3. **Tester la connexion**
   - Utiliser la fonction "Test" de la pointeuse
   - Faire un pointage test
   - Vérifier dans l'ERP : Menu → Employés & RH → Suivi Temps Réel

---

## 🧪 Tests de validation

### Test 1 : API accessible

```bash
# Depuis le VPS
curl http://localhost:5000/zkteco/api/ping

# Depuis un autre ordinateur sur le réseau
curl http://IP_VPS:5000/zkteco/api/ping
```

Résultat attendu :
```json
{
  "status": "success",
  "message": "ZKTeco API is running",
  "timestamp": "2025-12-04T..."
}
```

### Test 2 : Pointage test manuel

```bash
cd /opt/erp/app
source venv/bin/activate

curl -X POST http://localhost:5000/zkteco/api/test-attendance \
     -H 'Content-Type: application/json' \
     -d '{
       "user_id": 1,
       "timestamp": "2025-12-04 08:00:00",
       "punch_type": "in"
     }'
```

Résultat attendu :
```json
{
  "status": "success",
  "message": "Test de pointage effectué"
}
```

### Test 3 : Vérifier dans l'ERP

1. Aller sur : `https://erp.declaimers.com/employees/attendance/live`
2. Le pointage test devrait apparaître
3. Faire un vrai pointage sur la pointeuse
4. Vérifier qu'il apparaît dans l'ERP en temps réel (max 30s)

---

## 📊 Scripts de diagnostic

### Voir l'historique complet des pointages

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/historique_pointages.py
```

Ce script montre :
- Nombre total de pointages (pointeuse vs manuel)
- Historique jour par jour
- Dernier pointage de la pointeuse
- Détails des 30 derniers pointages

### Diagnostic complet de la pointeuse

```bash
python3 scripts/diagnostic_pointeuse_zkteco.py
```

---

## 🔍 Résolution de problèmes

### Problème 1 : "Configuration manquante"

**Cause :** Variables `ZKTECO_IP` et `ZKTECO_PORT` non définies

**Solution :**
1. Ajouter dans `.env` (voir étape 1)
2. Redémarrer l'ERP : `sudo systemctl restart erp`

### Problème 2 : "Aucun pointage aujourd'hui"

**Causes possibles :**
- Pointeuse non configurée pour envoyer à l'ERP
- Firewall bloque la connexion
- IP incorrecte

**Solutions :**
1. Vérifier la configuration Push de la pointeuse
2. Tester la connexion : `curl http://IP_VPS:5000/zkteco/api/ping`
3. Vérifier le firewall : `sudo ufw status`

### Problème 3 : "Tous les pointages sont manuels"

**Cause :** La pointeuse n'envoie plus les données depuis un certain temps

**Solution :**
1. Exécuter `python3 scripts/historique_pointages.py` pour voir quand ça a arrêté
2. Vérifier la configuration réseau de la pointeuse
3. Reconfigurer l'URL Push

### Problème 4 : "Device User ID: N/A"

**Cause :** Les employés n'ont pas d'ID associé à la pointeuse

**Solution :**
1. Dans l'ERP, éditer chaque employé
2. Ajouter le `Device User ID` (numéro dans la pointeuse)
3. Exemple : Si l'employé est le n°1 dans la pointeuse, mettre 1

---

## 🌐 Configuration Firewall (si nécessaire)

Si la pointeuse ne peut pas accéder à l'ERP :

```bash
# Ouvrir le port 5000 (Flask)
sudo ufw allow 5000/tcp

# Ou si vous utilisez Nginx (port 80/443)
sudo ufw allow 'Nginx Full'

# Vérifier
sudo ufw status
```

---

## 📝 Checklist finale

- [ ] Variables `ZKTECO_IP` et `ZKTECO_PORT` dans `.env`
- [ ] Code à jour (`git pull`)
- [ ] ERP redémarré (`systemctl restart erp`)
- [ ] Diagnostic OK (IP affichée)
- [ ] API ping répond
- [ ] Pointeuse configurée avec bonne URL
- [ ] Test de pointage manuel fonctionne
- [ ] Vrai pointage sur la pointeuse apparaît dans l'ERP

---

## 🆘 Support

Si le problème persiste après toutes ces étapes :

1. **Logs de l'ERP :**
   ```bash
   sudo journalctl -u erp -f
   ```

2. **Logs de la pointeuse :**
   - Menu → System → Logs
   - Vérifier les erreurs de connexion

3. **Tester la connectivité réseau :**
   ```bash
   # Depuis la pointeuse vers le VPS (si SSH disponible)
   ping IP_VPS
   
   # Depuis le VPS
   ping IP_POINTEUSE
   ```

---

**Dernière mise à jour :** 4 décembre 2025

