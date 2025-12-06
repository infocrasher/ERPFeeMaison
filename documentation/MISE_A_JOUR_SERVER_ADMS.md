# 🔄 Mise à Jour de `server_adms.py`

**Date:** 6 décembre 2025  
**Objectif:** Remplacer l'ancien script par la version avec détection automatique d'IP

---

## 🎯 PROBLÈME RÉSOLU

### ❌ Avant (Version ancienne)
```python
ZK_IP = "192.168.8.104"  # IP en dur
```
**Problème:** Si l'IP de la pointeuse change (DHCP), le script ne fonctionne plus.

### ✅ Après (Version améliorée)
```python
POINTEUSE_MAC = "8C:AA:B5:D7:44:29"  # Détection par MAC
ZK_IP = detect_pointeuse_ip()  # Détection automatique
```
**Avantage:** Le script trouve automatiquement la pointeuse, même si son IP change !

---

## 📋 CE QUI A CHANGÉ

### 1. Ajout de la fonction `detect_pointeuse_ip()`
- Scanne le réseau local (192.168.8.x)
- Cherche la MAC `8C:AA:B5:D7:44:29`
- Retourne l'IP actuelle de la pointeuse
- Fallback sur `192.168.8.104` si détection échoue

### 2. Amélioration des messages d'erreur
- Messages plus clairs en cas de problème
- Instructions de dépannage affichées

### 3. Headers ajoutés
- Bannière au démarrage
- Meilleure traçabilité

---

## 🚀 INSTALLATION SUR LE PC DU MAGASIN

### Étape 1 : Sauvegarder l'ancien script

Sur le PC du magasin (192.168.8.101) :

```cmd
cd C:\erp\fee_maison_gestion_cursor
copy server_adms.py server_adms_OLD.py
```

### Étape 2 : Récupérer la nouvelle version

**Option A : Via Git (Recommandé)**

```cmd
cd C:\erp\fee_maison_gestion_cursor
git pull origin main
```

**Option B : Copie manuelle**

1. Ouvrir le nouveau fichier sur GitHub ou depuis votre Mac
2. Copier tout le contenu
3. Sur le PC magasin, ouvrir `server_adms.py` dans un éditeur
4. Remplacer tout le contenu
5. Enregistrer

### Étape 3 : Tester la nouvelle version

```cmd
cd C:\erp\fee_maison_gestion_cursor
venv\Scripts\activate
python server_adms.py
```

**Résultat attendu :**

```
============================================================
🚀 SYNCHRONISATION POINTEUSE → ERP
   Version avec détection automatique d'IP
============================================================

🔍 Recherche de la pointeuse (MAC: 8C:AA:B5:D7:44:29)...
✅ Pointeuse détectée à l'IP: 192.168.8.100
🔌 Connexion au WL30 (192.168.8.100)...
✅ Connecté à la pointeuse !
📥 Lecture des pointages...
📊 15 pointages trouvés en mémoire.
📤 Envoi vers l'ERP...
...............
✅ Terminé : 15 envoyés sur 15.
👤 Vérification des utilisateurs...
   -> 5 utilisateurs détectés (Scan partiel).
🏁 Synchronisation finie avec succès.
🔌 Déconnecté.

⏳ Fermeture dans 5 secondes...
```

### Étape 4 : Vérifier dans l'ERP

1. Aller sur `https://erp.declaimers.com/employees/attendance/live`
2. Les pointages doivent apparaître
3. Source: 🤖 Pointeuse

---

## 🔧 SI VOUS AVEZ UNE TÂCHE PLANIFIÉE

Si `server_adms.py` tourne automatiquement (Task Scheduler Windows), rien à changer ! Le nouveau script fonctionne exactement de la même manière, juste avec détection automatique d'IP.

**Vérifier la tâche planifiée :**

1. Ouvrir **Planificateur de tâches** (Task Scheduler)
2. Chercher une tâche nommée "Pointeuse" ou "ZKTeco" ou "server_adms"
3. Vérifier qu'elle pointe vers le bon fichier :
   ```
   C:\erp\fee_maison_gestion_cursor\server_adms.py
   ```
4. Pas besoin de modification !

---

## 🧪 TESTS À FAIRE

### Test 1 : Détection avec IP actuelle

```cmd
python server_adms.py
```
Doit détecter et se connecter.

### Test 2 : Détection après changement d'IP

1. Redémarrer la pointeuse (elle aura une nouvelle IP)
2. Attendre 30 secondes
3. Relancer `python server_adms.py`
4. Le script doit **détecter la nouvelle IP automatiquement** !

### Test 3 : Fallback si détection échoue

1. Éteindre la pointeuse
2. Lancer `python server_adms.py`
3. Doit afficher :
   ```
   ⚠️  Pointeuse non trouvée, utilisation IP par défaut: 192.168.8.104
   ```
4. Puis échouer à se connecter (normal, pointeuse éteinte)

---

## 📊 COMPARAISON

| Fonctionnalité | Version Ancienne | Version Améliorée |
|----------------|------------------|-------------------|
| **IP fixe** | ❌ Oui (codée en dur) | ✅ Non (détection auto) |
| **Résistance changement IP** | ❌ Non | ✅ Oui |
| **Dépendance réseau** | ❌ Élevée | ✅ Faible |
| **Diagnostic erreurs** | ⚠️ Basique | ✅ Complet |
| **Compatibilité** | ✅ 100% | ✅ 100% |

---

## ⚠️ POINTS IMPORTANTS

### 1. La MAC ne change jamais
✅ La MAC de la pointeuse est **fixe** : `8C:AA:B5:D7:44:29`  
✅ Pas besoin de la modifier dans le script

### 2. IP par défaut comme fallback
✅ Si la détection échoue, le script utilise `192.168.8.104`  
✅ Donc même logique qu'avant en cas de problème

### 3. Aucun impact sur la tâche planifiée
✅ Pas besoin de reconfigurer quoi que ce soit  
✅ Remplacement transparent

---

## 🆘 DÉPANNAGE

### Erreur : "Pointeuse non trouvée"

**Vérifications :**

1. La pointeuse est allumée ?
2. Câble réseau branché ?
3. Même réseau que le PC (192.168.8.x) ?

**Test manuel :**

```cmd
arp -a | findstr "8c-aa-b5-d7-44-29"
```

Doit afficher une ligne avec l'IP de la pointeuse.

### Erreur : "Erreur connexion"

**Vérifications :**

1. Le port 4370 est-il ouvert ?
2. Firewall Windows bloque-t-il ?
3. Test ping :
   ```cmd
   ping [IP_DETECTÉE]
   ```

### En cas de problème persistant

**Restaurer l'ancienne version :**

```cmd
cd C:\erp\fee_maison_gestion_cursor
copy server_adms_OLD.py server_adms.py
```

---

## ✅ VALIDATION FINALE

Une fois le script mis à jour et testé :

1. ✅ Détection automatique fonctionne
2. ✅ Connexion à la pointeuse OK
3. ✅ Pointages envoyés au VPS OK
4. ✅ Visible dans l'ERP OK
5. ✅ Tâche planifiée fonctionne OK

**Vous êtes prêt ! La pointeuse fonctionnera désormais quelle que soit son IP.** 🎉

---

**Dernière mise à jour :** 6 décembre 2025  
**Auteur :** Équipe Technique Fée Maison

