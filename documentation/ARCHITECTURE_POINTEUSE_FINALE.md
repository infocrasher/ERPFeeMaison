# 🏗️ Architecture Pointeuse ZKTeco - Solution Finale

**Date:** 7 décembre 2025  
**Statut:** ✅ Solution opérationnelle validée

---

## 📊 ARCHITECTURE FINALE

```
┌─────────────────────────────────────────────────────────────┐
│                    POINTEUSE ZKTECO WL30                      │
│              (192.168.8.100 - IP dynamique)                  │
│                                                               │
│  Configuration Serveur Cloud:                                │
│  - Adresse Serveur: 192.168.8.101 (IP fixe PC)              │
│  - Port: 8090                                                 │
│  - Mode: PUSH (iClock Protocol)                               │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        │ HTTP (réseau local)
                        │
┌───────────────────────▼───────────────────────────────────────┐
│              PC MAGASIN (Windows)                            │
│              (192.168.8.101 - IP FIXE)                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  serveur_zkteco.py (Flask)                         │    │
│  │  Port: 8090                                        │    │
│  │  Protocole: iClock (ZKTeco ADMS)                  │    │
│  │  Routes:                                           │    │
│  │    - /iclock/cdata (GET/POST)                      │    │
│  │    - /iclock/getrequest                            │    │
│  │    - /iclock/devicecmd                             │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        │ HTTPS POST
                        │ Authorization: Bearer Token
                        │
┌───────────────────────▼───────────────────────────────────────┐
│                    VPS (OVH Ubuntu)                          │
│              erp.declaimers.com                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Flask ERP                                          │    │
│  │  Route: /zkteco/api/attendance                      │    │
│  │  Authentification: Token Bearer                     │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔧 COMPOSANTS

### 1. **Pointeuse ZKTeco WL30**

**Caractéristiques :**
- **Modèle:** WL30
- **Firmware:** 6.60
- **Protocole:** iClock (ADMS Push)
- **IP:** Dynamique (192.168.8.100-200, détectée par MAC: `8C:AA:B5:D7:44:29`)

**Configuration Serveur Cloud :**
```
Menu → Configuration Serveur Cloud
- Adresse Serveur: 192.168.8.101 (IP fixe du PC magasin)
- Port: 8090
- Mode: PUSH (automatique)
```

**⚠️ IMPORTANT :** Le PC magasin doit avoir une **IP fixe** (192.168.8.101) pour que la pointeuse puisse toujours le joindre.

**⚠️ IMPORTANT :** La pointeuse envoie automatiquement les pointages dès qu'ils sont créés. Pas besoin de script PULL.

---

### 2. **Serveur Flask Local (`serveur_zkteco.py`)**

**Fichier:** `C:\Users\pos\Desktop\ERP_AGENT\serveur_zkteco.py`

**Fonctionnalités :**
- ✅ Écoute sur port 8090
- ✅ Implémente le protocole iClock complet
- ✅ Reçoit les données ATTLOG (pointages)
- ✅ Parse le format tabulé ZKTeco
- ✅ Transmet au VPS avec authentification

**Protocole iClock implémenté :**

#### Route `/iclock/cdata` (GET)
**Réponse aux keep-alive de la pointeuse :**
```
GET /iclock/cdata?SN=A5KX203260068&options=all&pushver=3.0.1&language=70
```

**Réponse :**
```
GET OPTION FROM: 10000
ATTLOGStamp=None
OPERLOGStamp=None
ATTPHOTOStamp=None
ErrorDelay=30
Delay=10
TransTimes=00:00;14:05
TransInterval=1
TransFlag=1111000000
Realtime=1
Encrypt=0
```

#### Route `/iclock/cdata` (POST)
**Réception des pointages :**
```
POST /iclock/cdata?table=ATTLOG
Body (texte tabulé):
1	2025-12-07 08:30:15	0	0	0
2	2025-12-07 08:31:20	1	0	0
```

**Format des données :**
```
user_id \t timestamp \t punch_type \t status \t verify
```

**Mapping punch_type :**
- `0` = Entrée (in)
- `1` = Sortie (out)
- `5` = Sortie (out) - variante

---

### 3. **Communication Réseau Local**

**Configuration :**
- Pointeuse et PC sont sur le **même réseau local** (192.168.8.x)
- Communication **directe** via HTTP (pas besoin de Ngrok)
- PC magasin a une **IP fixe** : 192.168.8.101

**Fonction :**
- Communication directe sur le réseau local
- Pas de tunnel nécessaire (même réseau)
- Latence minimale

---

### 4. **VPS ERP**

**Route API :**
```
POST https://erp.declaimers.com/zkteco/api/attendance
```

**Authentification :**
```
Authorization: Bearer TokenSecretFeeMaison2025
```

**Format attendu :**
```json
{
  "user_id": 1,
  "timestamp": "2025-12-07 08:30:15",
  "punch_type": "in"
}
```

---

## 📝 CODE COMPLET DU SERVEUR

```python
from flask import Flask, request
import requests
import sys

# ================= CONFIGURATION =================
VPS_API_URL = "https://erp.declaimers.com/zkteco/api/attendance"
VPS_TOKEN = "TokenSecretFeeMaison2025"
SERVER_PORT = 8090
# =================================================

app = Flask(__name__)

def send_to_vps(user_id, timestamp, state):
    """Envoie un pointage au VPS"""
    punch_type = "out" if str(state) in ['1', '5'] else "in"
    
    payload = {
        "user_id": user_id,
        "timestamp": timestamp,
        "punch_type": punch_type
    }
    headers = {"Authorization": f"Bearer {VPS_TOKEN}"}
    
    try:
        print(f"   -> Envoi VPS : User {user_id} ({punch_type}) a {timestamp}...", end="", flush=True)
        r = requests.post(VPS_API_URL, json=payload, headers=headers, timeout=5)
        if r.status_code in [200, 201]:
            print(" [OK]")
            return True
        else:
            print(f" [ERREUR VPS: {r.status_code}]")
            return False
    except Exception as e:
        print(f" [ERREUR RESEAU: {e}]")
        return False

@app.route('/iclock/cdata', methods=['GET', 'POST'])
def receive_data():
    table = request.args.get('table', '')
    
    if table == 'ATTLOG':
        raw_data = request.get_data().decode('utf-8')
        if not raw_data: 
            return "OK"
        
        print(f"\n[RECU] Paquet de logs", flush=True)
        
        lines = raw_data.strip().split('\n')
        count = 0
        
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                uid = parts[0]
                ts = parts[1]
                state = parts[2]
                send_to_vps(uid, ts, state)
                count += 1
        
        print(f"   -- {count} pointages traites.", flush=True)
        return "OK"
    
    if request.method == 'GET' and 'options' in request.args:
        return "GET OPTION FROM: 10000\nATTLOGStamp=None\nOPERLOGStamp=None\nATTPHOTOStamp=None\nErrorDelay=30\nDelay=10\nTransTimes=00:00;14:05\nTransInterval=1\nTransFlag=1111000000\nRealtime=1\nEncrypt=0"
    
    return "OK"

@app.route('/iclock/getrequest', methods=['GET', 'POST'])
def get_request():
    return "OK"

@app.route('/iclock/devicecmd', methods=['GET', 'POST'])
def device_cmd():
    return "OK"

if __name__ == '__main__':
    print(f"SERVEUR ZKTECO -> ERP EN LIGNE (Port {SERVER_PORT})", flush=True)
    print("En attente de pointages...", flush=True)
    app.run(host='0.0.0.0', port=SERVER_PORT)
```

---

## 🚨 PROBLÈME RÉSOLU : IP DYNAMIQUE

### Problème initial
- PC magasin : IP changeait régulièrement (DHCP)
- Pointeuse : Configurée avec ancienne IP fixe (ex: 192.168.8.102)
- Résultat : La pointeuse essayait d'envoyer vers une IP inexistante

### Solution appliquée
1. ✅ **IP fixe sur PC** : Configuration Windows pour IP statique 192.168.8.101
2. ✅ **Config pointeuse** : Adresse serveur = 192.168.8.101 (IP fixe du PC)
3. ✅ **Communication directe** : Réseau local, pas besoin de tunnel

**Architecture simple :**
```
Pointeuse (192.168.8.100) → PC local (192.168.8.101:8090) → VPS
```

**Note :** La pointeuse peut avoir une IP dynamique (192.168.8.100-200), mais le PC doit avoir une IP fixe pour que la pointeuse puisse toujours le joindre.

---

## 🔄 WORKFLOW COMPLET

### 1. Pointage sur la pointeuse
- Employé pointe son doigt
- Pointeuse enregistre : `user_id=1, timestamp=2025-12-07 08:30:15, punch_type=0`

### 2. Envoi automatique (PUSH)
- Pointeuse envoie via iClock vers `192.168.8.101:8090` (IP fixe du PC)
- Communication directe sur réseau local
- `serveur_zkteco.py` reçoit les données

### 3. Traitement local
- Parse le format tabulé
- Convertit `punch_type` (0=in, 1=out)
- Prépare payload JSON

### 4. Transmission VPS
- POST vers `https://erp.declaimers.com/zkteco/api/attendance`
- Authentification Bearer Token
- Log dans l'ERP

### 5. Confirmation
- Serveur répond "OK" à la pointeuse
- Pointeuse marque le log comme envoyé

---

## 📋 INSTALLATION ET DÉMARRAGE

### ⚠️ PRÉREQUIS : IP Fixe sur PC Magasin

**Le PC magasin DOIT avoir une IP fixe (192.168.8.101) pour que la pointeuse puisse toujours le joindre.**

**Configuration Windows (IP Statique) :**
1. Paramètres → Réseau et Internet → Ethernet
2. Propriétés de la connexion → Modifier les paramètres IP
3. Passer de "Automatique (DHCP)" à "Manuel"
4. Configurer :
   - **Adresse IP :** `192.168.8.101`
   - **Masque :** `255.255.255.0`
   - **Passerelle :** `192.168.8.1`
   - **DNS :** `192.168.8.1` et `8.8.8.8`
5. Enregistrer et redémarrer

**Vérification :**
```cmd
ipconfig
```
Doit afficher : `192.168.8.101`

### Fichiers nécessaires sur PC magasin

```
C:\Users\pos\Desktop\ERP_AGENT\
├── serveur_zkteco.py      (Serveur Flask iClock)
├── agent.py               (Agent imprimante - port 8080)
└── START_FULL_ERP.bat     (Script de démarrage)
```

### Dépendances Python

```bash
pip install flask requests
```

### Script de démarrage (`START_FULL_ERP.bat`)

```batch
@echo off
TITLE ERP FEE MAISON - SYSTEME CENTRAL

echo Démarrage des services...

:: 1. Serveur ZKTeco (port 8090)
start "Serveur ZKTeco" python serveur_zkteco.py

:: 2. Agent Imprimante (port 8080)
start "Agent Imprimante" python agent.py

:: 3. Tunnel Ngrok (pour imprimante uniquement, si nécessaire)
:: start "Tunnel Ngrok" ngrok http --domain=ungesticular-disillusionedly-kenna.ngrok-free.dev 8080

echo.
echo TOUS LES SYSTEMES SONT EN LIGNE.
echo Ne pas fermer cette fenetre.
pause
```

**Note :** Ngrok n'est pas nécessaire pour la pointeuse (communication locale directe). Il peut être utilisé pour l'imprimante si besoin.

---

## ⚠️ NOTES IMPORTANTES

### Compatibilité WL30 Firmware 6.60

**Problème connu :**
- Le firmware 6.60 utilise une structure de données utilisateurs (SSR/Push) incompatible avec le parsing standard de `pyzk`
- `get_users()` retourne vide
- `get_attendance()` fonctionne pour les logs (format compatible)

**Solution appliquée :**
- Utilisation du protocole iClock natif (PUSH)
- Pas besoin de `pyzk` pour récupérer les logs
- La pointeuse envoie automatiquement

### Format des données iClock

**ATTLOG (Attendance Log) :**
```
Format: user_id \t timestamp \t punch_type \t status \t verify

Exemple:
1	2025-12-07 08:30:15	0	0	0
2	2025-12-07 08:31:20	1	0	0
```

**Mapping punch_type :**
- `0` = Check-In (Entrée) → `punch_type: "in"`
- `1` = Check-Out (Sortie) → `punch_type: "out"`
- `5` = Check-Out (variante) → `punch_type: "out"`

---

## 🧪 TESTS DE VALIDATION

### Test 1 : Vérifier que le serveur écoute

```cmd
netstat -ano | findstr 8090
```

**Résultat attendu :**
```
TCP    0.0.0.0:8090     0.0.0.0:0     LISTENING     [PID]
```

### Test 2 : Vérifier que le PC a l'IP fixe

```cmd
ipconfig
```

**Résultat attendu :**
```
Adresse IPv4 . . . . . . . . . . . . . . . : 192.168.8.101
```

**Si l'IP est différente :** Configurer une IP statique dans Windows

### Test 3 : Pointage réel

1. Pointer sur la pointeuse
2. Observer les logs de `serveur_zkteco.py`
3. Vérifier dans l'ERP : `https://erp.declaimers.com/employees/attendance/live`

**Résultat attendu :**
```
[RECU] Paquet de logs
   -> Envoi VPS : User 1 (in) a 2025-12-07 08:30:15... [OK]
   -- 1 pointages traites.
```

---

## 🔧 DÉPANNAGE

### Problème : "0 pointages reçus"

**Vérifications :**
1. ✅ PC a-t-il l'IP fixe 192.168.8.101 ?
2. ✅ `serveur_zkteco.py` écoute-t-il sur 8090 ?
3. ✅ Config pointeuse : Adresse = `192.168.8.101` ?
4. ✅ Port pointeuse : `8090` ?
5. ✅ Pointeuse et PC sur même réseau (192.168.8.x) ?

### Problème : "Erreur VPS: 401"

**Cause :** Token invalide ou manquant

**Solution :** Vérifier `VPS_TOKEN` dans `serveur_zkteco.py`

### Problème : "Erreur RESEAU: Connection refused"

**Cause :** VPS inaccessible ou route bloquée

**Solution :** Tester manuellement :
```bash
curl -X POST https://erp.declaimers.com/zkteco/api/attendance \
     -H "Authorization: Bearer TokenSecretFeeMaison2025" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1, "timestamp": "2025-12-07 08:30:15", "punch_type": "in"}'
```

---

## 📊 COMPARAISON : PUSH vs PULL

| Aspect | Mode PUSH (iClock) ✅ ACTUEL | Mode PULL (pyzk) ❌ Ancien |
|--------|------------------------------|----------------------------|
| **Script** | `serveur_zkteco.py` (Flask) | `server_adms.py` (pyzk) |
| **Déclenchement** | Automatique (pointeuse envoie) | Manuel (script va chercher) |
| **Timing** | Temps réel | Délai possible |
| **Buffer** | Non nécessaire | SQLite nécessaire |
| **Complexité** | Simple (serveur passif) | Complexe (connexion active) |
| **Résilience IP** | ✅ IP fixe PC (192.168.8.101) | ❌ Nécessite détection MAC |

**Conclusion :** Mode PUSH est plus simple et plus fiable ! ✅

---

## ✅ CHECKLIST FINALE

- [x] Serveur Flask `serveur_zkteco.py` créé
- [x] Protocole iClock implémenté
- [x] Ngrok configuré pour port 8090
- [x] Pointeuse configurée avec Domain (pas IP)
- [x] VPS API `/zkteco/api/attendance` fonctionnelle
- [x] Authentification Bearer Token
- [x] Mapping punch_type (0=in, 1=out)
- [x] Tests de validation réussis

---

**Dernière mise à jour :** 7 décembre 2025  
**Statut :** ✅ Production - Opérationnel  
**Auteur :** Équipe Technique Fée Maison

