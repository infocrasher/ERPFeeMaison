# 🔧 Configuration IP Statique pour Pointeuse ZKTeco

**Date:** 6 décembre 2025  
**Objectif:** Fixer l'adresse IP de la pointeuse et du PC magasin pour éviter les changements d'IP

---

## 🎯 Objectifs

- **Pointeuse ZKTeco:** `192.168.8.104` (IP fixe)
- **PC Magasin:** `192.168.8.102` (IP fixe)
- **Routeur Huawei:** `192.168.8.1`

**Pourquoi ?** Les adresses IP dynamiques (DHCP) changent régulièrement, ce qui casse la configuration de la pointeuse.

---

## 📋 MÉTHODE 1 : Configuration via Interface Web Routeur (RECOMMANDÉ)

### Étape 1 : Identifier les adresses MAC

#### A. Adresse MAC de la pointeuse ZKTeco

1. Sur la pointeuse, aller dans le menu
2. **Menu → Communication → Ethernet → Network Settings**
3. Noter l'adresse MAC (format: `AA:BB:CC:DD:EE:FF`)

#### B. Adresse MAC du PC magasin

**Sur Windows:**
```cmd
ipconfig /all
```
Chercher "Adresse physique" ou "Physical Address"

**Sur Mac:**
```bash
ifconfig en0 | grep ether
```

**Sur Linux:**
```bash
ip link show
```

### Étape 2 : Se connecter au routeur Huawei

1. Ouvrir un navigateur sur le PC magasin
2. Aller à : `http://192.168.8.1`
3. Se connecter avec les identifiants admin

### Étape 3 : Configurer les IP statiques

**Le chemin exact dépend du modèle de routeur, mais généralement :**

1. **DHCP → Static IP Address** ou **IP Reservation**
2. **Ajouter une nouvelle réservation:**
   - **Device Name:** Pointeuse ZKTeco
   - **MAC Address:** (celle notée à l'étape 1)
   - **IP Address:** `192.168.8.104`
   - **Status:** Enabled
3. **Enregistrer**
4. **Ajouter une deuxième réservation:**
   - **Device Name:** PC Magasin
   - **MAC Address:** (celle notée à l'étape 1)
   - **IP Address:** `192.168.8.102`
   - **Status:** Enabled
5. **Enregistrer**
6. **Redémarrer le routeur** (optionnel mais recommandé)

### Étape 4 : Redémarrer les appareils

1. Éteindre et rallumer la pointeuse ZKTeco
2. Redémarrer le PC magasin (ou `ipconfig /renew` sur Windows)

### Étape 5 : Vérifier

**Sur le PC magasin:**
```cmd
ipconfig
```
Devrait afficher `192.168.8.102`

**Sur la pointeuse:**
Menu → Communication → Ethernet → Devrait afficher `192.168.8.104`

---

## 📋 MÉTHODE 2 : Configuration via API Huawei (Si disponible)

### Prérequis

```bash
cd "/Users/sofiane/Documents/Save FM/fee_maison_gestion_cursor"
source venv/bin/activate
pip install huawei-lte-api
```

### Script 1 : Explorer les capacités du routeur

```bash
python3 scripts/test_routeur_huawei.py
```

Ce script va :
- Se connecter au routeur
- Lister les méthodes DHCP disponibles
- Afficher la configuration actuelle

### Script 2 : Identifier les appareils connectés

```bash
python3 scripts/identifier_appareils_reseau.py
```

Ce script va tenter de lister tous les appareils connectés.

### Script 3 : Configurer les IP statiques (si l'API le permet)

⚠️ **À créer uniquement si les scripts 1 et 2 montrent que c'est possible**

---

## 📋 MÉTHODE 3 : Configuration sur la pointeuse elle-même (Alternative)

Si le routeur ne permet pas de fixer l'IP via DHCP, on peut configurer une IP statique directement sur la pointeuse.

### Sur la pointeuse ZKTeco WL30 :

1. **Menu → Communication → Ethernet**
2. **IP Mode:** Changer de DHCP à **Static**
3. **IP Address:** `192.168.8.104`
4. **Subnet Mask:** `255.255.255.0`
5. **Gateway:** `192.168.8.1`
6. **DNS1:** `192.168.8.1` (ou `8.8.8.8`)
7. **DNS2:** `8.8.4.4` (optionnel)
8. **Enregistrer et Redémarrer**

### Avantages
- ✅ IP garantie fixe
- ✅ Pas de dépendance au routeur

### Inconvénients
- ⚠️ Risque de conflit si le routeur DHCP attribue la même IP à un autre appareil
- ⚠️ Si vous changez de routeur, il faudra reconfigurer

---

## 🧪 Tests de validation

### Test 1 : Vérifier l'IP de la pointeuse

**Depuis le PC magasin:**
```bash
ping 192.168.8.104
```
**Résultat attendu:** Réponses de la pointeuse

### Test 2 : Vérifier que l'ERP peut joindre la pointeuse

**Sur le VPS:**
```bash
curl http://192.168.8.104:80
```
⚠️ Cela ne fonctionnera que si le VPS est sur le même réseau local (peu probable)

**L'ERP doit être accessible DEPUIS la pointeuse, pas l'inverse !**

### Test 3 : Vérifier la configuration dans l'ERP

**Éditer le `.env` sur le VPS:**
```bash
ZKTECO_IP=192.168.8.104
ZKTECO_PORT=4370
```

**Redémarrer l'ERP:**
```bash
sudo systemctl restart erp
```

**Vérifier les logs:**
```bash
sudo journalctl -u erp -f
```

### Test 4 : Pointage test

Demander à un employé de pointer sur la pointeuse et vérifier que ça apparaît dans l'ERP :
```
https://erp.declaimers.com/employees/attendance/live
```

---

## 📝 RECOMMANDATION FINALE

**Meilleure solution :**

1. ✅ **Configurer IP statique sur la pointeuse elle-même** (Méthode 3)
   - Fiable
   - Indépendant du routeur
   - Pas de configuration complexe

2. ✅ **Configurer IP statique sur le PC** via les paramètres réseau Windows/Mac/Linux
   - Plus simple que de passer par le routeur

3. ✅ **Mettre à jour la configuration ERP** avec la bonne IP

---

## ⚠️ IMPORTANT

Une fois les IP fixées, **mettre à jour immédiatement :**

### Sur le VPS (`.env`)
```bash
ZKTECO_IP=192.168.8.104
ZKTECO_PORT=4370
```

### Dans la documentation
```bash
documentation/INSTRUCTIONS_RESTAURATION_POINTEUSE.md
env_production.example.txt
```

### Redémarrer l'ERP
```bash
sudo systemctl restart erp
```

---

**Dernière mise à jour:** 6 décembre 2025  
**Auteur:** Équipe Technique Fée Maison

