# 🌉 Installation du Service Pont Pointeuse → VPS

**Objectif:** Installer un service sur le PC du magasin qui :
1. Détecte automatiquement l'IP de la pointeuse (même si elle change)
2. Récupère les pointages en temps réel
3. Les envoie au VPS automatiquement

---

## 📋 PRÉREQUIS

### Sur le PC du magasin (Windows)

1. **Python 3.8+** installé
2. **Accès administrateur** sur le PC
3. **Connexion Internet** stable
4. **Même réseau que la pointeuse** (192.168.8.x)

---

## 🚀 INSTALLATION

### Étape 1 : Fixer l'IP du PC

**Important :** Le PC doit avoir une IP statique (même si la pointeuse ne peut pas).

**Sur Windows 10/11 :**

1. **Paramètres → Réseau et Internet → Ethernet**
2. **Propriétés de la connexion**
3. **Modifier les paramètres IP**
4. Passer de **Automatique (DHCP)** à **Manuel**
5. Configurer :
   - **Adresse IP :** `192.168.8.101`
   - **Masque :** `255.255.255.0`
   - **Passerelle :** `192.168.8.1`
   - **DNS :** `192.168.8.1` et `8.8.8.8`
6. **Enregistrer**
7. **Redémarrer le PC**

### Étape 2 : Installer les dépendances Python

Ouvrir **PowerShell en Administrateur** :

```powershell
# Aller dans le dossier du projet
cd C:\erp\fee_maison_gestion_cursor

# Activer l'environnement virtuel
venv\Scripts\activate

# Installer les bibliothèques nécessaires
pip install pyzk requests python-dotenv

# ou
pip install -r requirements_bridge.txt
```

### Étape 3 : Configurer le service

Créer un fichier `.env` dans `C:\erp\fee_maison_gestion_cursor\` :

```bash
# Configuration du pont pointeuse
POINTEUSE_MAC=8C:AA:B5:D7:44:29
POINTEUSE_PORT=4370
VPS_URL=https://erp.declaimers.com/zkteco/api/attendance
VPS_TOKEN=TokenSecretFeeMaison2025
CHECK_INTERVAL=30
```

### Étape 4 : Tester le service manuellement

```powershell
cd C:\erp\fee_maison_gestion_cursor
venv\Scripts\activate
python scripts\pointeuse_bridge_service.py
```

**Résultat attendu :**
```
🚀 DÉMARRAGE DU SERVICE PONT POINTEUSE → VPS
Pointeuse MAC: 8C:AA:B5:D7:44:29
VPS: https://erp.declaimers.com/zkteco/api/attendance

🔄 IP de la pointeuse détectée: 192.168.8.100
✅ Connecté à la pointeuse 192.168.8.100
```

### Étape 5 : Installer comme service Windows

#### Option A : Utiliser NSSM (Non-Sucking Service Manager)

**Télécharger NSSM :**
```powershell
# Télécharger depuis https://nssm.cc/download
# Extraire dans C:\nssm
```

**Installer le service :**
```powershell
# En Administrateur
cd C:\nssm\win64

.\nssm install FeeMaisonPointeuseBridge "C:\erp\fee_maison_gestion_cursor\venv\Scripts\python.exe" "C:\erp\fee_maison_gestion_cursor\scripts\pointeuse_bridge_service.py"

.\nssm set FeeMaisonPointeuseBridge AppDirectory "C:\erp\fee_maison_gestion_cursor"
.\nssm set FeeMaisonPointeuseBridge DisplayName "Fée Maison - Pont Pointeuse"
.\nssm set FeeMaisonPointeuseBridge Description "Service de pont entre la pointeuse ZKTeco et le VPS ERP"
.\nssm set FeeMaisonPointeuseBridge Start SERVICE_AUTO_START

# Démarrer le service
.\nssm start FeeMaisonPointeuseBridge
```

#### Option B : Créer un service Windows manuellement

Créer `C:\erp\fee_maison_gestion_cursor\scripts\pointeuse_service_wrapper.py` :

```python
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os

class PointeuseBridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FeeMaisonPointeuseBridge"
    _svc_display_name_ = "Fée Maison - Pont Pointeuse"
    _svc_description_ = "Service de pont entre la pointeuse ZKTeco et le VPS ERP"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Importer et lancer le service
        sys.path.insert(0, r'C:\erp\fee_maison_gestion_cursor')
        os.chdir(r'C:\erp\fee_maison_gestion_cursor')
        
        from scripts.pointeuse_bridge_service import run_bridge_service
        run_bridge_service()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PointeuseBridgeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PointeuseBridgeService)
```

**Installer :**
```powershell
pip install pywin32
python pointeuse_service_wrapper.py install
python pointeuse_service_wrapper.py start
```

### Étape 6 : Vérifier que ça fonctionne

**Vérifier le service :**
```powershell
# Voir le statut
sc query FeeMaisonPointeuseBridge

# Voir les logs
type C:\erp\fee_maison_gestion_cursor\pointeuse_bridge.log
```

**Tester un pointage :**
1. Demander à un employé de pointer sur la pointeuse
2. Attendre 30 secondes max
3. Vérifier sur `https://erp.declaimers.com/employees/attendance/live`
4. Le pointage doit apparaître !

---

## 🔧 MAINTENANCE

### Redémarrer le service

```powershell
# Arrêter
nssm stop FeeMaisonPointeuseBridge
# ou
net stop FeeMaisonPointeuseBridge

# Démarrer
nssm start FeeMaisonPointeuseBridge
# ou
net start FeeMaisonPointeuseBridge
```

### Voir les logs

```powershell
type C:\erp\fee_maison_gestion_cursor\pointeuse_bridge.log
```

### Désinstaller le service

```powershell
nssm remove FeeMaisonPointeuseBridge confirm
# ou
python pointeuse_service_wrapper.py remove
```

---

## 🎯 AVANTAGES DE CETTE SOLUTION

✅ **Indépendant de l'IP de la pointeuse** : Détection automatique par MAC  
✅ **Robuste** : Reconnexion automatique si l'IP change  
✅ **Temps réel** : Vérification toutes les 30 secondes  
✅ **Logs complets** : Traçabilité de tous les événements  
✅ **Démarrage automatique** : Service Windows qui démarre au boot  
✅ **Pas de modification de la pointeuse ou du routeur**  

---

## 📊 ARCHITECTURE FINALE

```
┌─────────────────┐
│   Pointeuse     │
│ IP: Variable    │
│ MAC: 8C:AA:...  │
└────────┬────────┘
         │ Réseau local
         │ 192.168.8.x
┌────────▼────────┐
│  PC Magasin     │
│ IP: 192.168.8.101│ (Fixe)
│ Service Bridge  │
└────────┬────────┘
         │ Internet
         │ HTTPS
┌────────▼────────┐
│      VPS        │
│ erp.declaimers  │
└─────────────────┘
```

---

**Dernière mise à jour :** 6 décembre 2025  
**Solution testée et validée**

