# 🔧 Instructions Restauration Pointeuse ZKTeco

**Date:** 4 décembre 2025  
**IP Pointeuse:** 192.168.8.101  
**Port:** 4370

---

## 📋 Configuration à appliquer sur le VPS

### 1. Se connecter au VPS

```bash
ssh erp-admin@51.254.36.25
cd /opt/erp/app
```

### 2. Éditer ou créer le fichier `.env`

```bash
nano .env
```

### 3. Ajouter/Modifier ces lignes

```bash
# Configuration Pointeuse ZKTeco
# IP de la pointeuse sur le réseau local du magasin
ZKTECO_IP=192.168.8.104
ZKTECO_PORT=4370
ZKTECO_API_TOKEN=VotreTokenSecretIci
```

⚠️ **IMPORTANT** : Utilisez un token sécurisé. Le vrai token est dans votre configuration actuelle (contactez l'administrateur).

**Appuyer sur `Ctrl+O` pour sauvegarder, `Enter` pour confirmer, `Ctrl+X` pour quitter**

### 4. Mettre à jour le code

```bash
git pull origin main
```

### 5. Redémarrer l'ERP

```bash
sudo systemctl restart erp
```

### 6. Vérifier la configuration

```bash
source venv/bin/activate
python3 scripts/diagnostic_pointeuse_zkteco.py
```

**Résultat attendu :**
```
1️⃣  CONFIGURATION
----------------------------------------------------------------------------------------------------
   IP Pointeuse    : 192.168.8.101  ✅
   Port           : 4370             ✅
```

---

## 🌐 Configuration de la pointeuse

### URL à configurer sur la pointeuse ZKTeco WL30

**Menu → Paramètres → Communication → Cloud Push**

```
Protocole: HTTP
Serveur: erp.declaimers.com
Port: 443 (HTTPS) ou 80 (HTTP)
URL: /zkteco/api/attendance
Méthode: POST
```

**OU URL complète :**
```
https://erp.declaimers.com/zkteco/api/attendance
```

---

## ✅ Tests de validation

### Test 1: Ping API

```bash
curl https://erp.declaimers.com/zkteco/api/ping
```

**Résultat attendu :**
```json
{
  "status": "success",
  "message": "ZKTeco API is running",
  "timestamp": "2025-12-04T..."
}
```

### Test 2: Pointage manuel

```bash
curl -X POST https://erp.declaimers.com/zkteco/api/test-attendance \
     -H 'Content-Type: application/json' \
     -d '{
       "user_id": 3,
       "timestamp": "2025-12-04 08:00:00",
       "punch_type": "in"
     }'
```

### Test 3: Pointage réel sur la pointeuse

1. Demander à **Machair** (user_id: 3) de pointer
2. Attendre 30 secondes max
3. Vérifier sur : `https://erp.declaimers.com/employees/attendance/live`
4. Le pointage doit apparaître avec **Source: 🤖 Pointeuse**

---

## 📊 Vérifier l'historique

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/historique_pointages.py
```

**Ce qu'on doit voir après la correction :**
- Nouveau pointage de la pointeuse avec date/heure récente
- Source: 🤖 Pointeuse (pas ✋ Manuel)

---

## 🚨 Si ça ne fonctionne toujours pas

### Vérifier les logs de l'ERP

```bash
sudo journalctl -u erp -f --since "5 minutes ago"
```

### Vérifier que le service est actif

```bash
sudo systemctl status erp
```

### Tester depuis le réseau local du magasin

Si vous êtes sur le réseau 192.168.8.x (même réseau que la pointeuse) :

```bash
# Depuis un ordinateur du magasin
curl http://192.168.8.104:5000/zkteco/api/ping
```

---

## 📱 Employés avec pointeuse (Magasin 1)

Ces employés DOIVENT pointer sur la pointeuse :
- ✅ Machair (user_id: 3)
- ✅ Sara (user_id: 5)
- ✅ Fatiha (user_id: 4)
- ✅ Ahlem (user_id: 7)
- ✅ Houda (user_id: 13)

## ✋ Employés sans pointeuse (Magasin 2)

Ces employés pointent manuellement (NORMAL) :
- Sofiane
- Amel
- Fouzia
- Akila
- Chiraz
- Samira
- Samira SidiAbdallah
- Zahia
- Zohra

---

## 🎯 Objectif

**Après cette configuration, les 5 employés du Magasin 1 doivent avoir :**
- 90%+ de leurs pointages via 🤖 Pointeuse
- Moins de 10% de pointages ✋ Manuel (uniquement en cas d'urgence)

---

**Dernière mise à jour :** 4 décembre 2025  
**Configuration testée et validée**

