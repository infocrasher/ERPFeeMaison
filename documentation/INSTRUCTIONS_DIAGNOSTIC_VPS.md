# Instructions - Diagnostic Comptabilité VPS

**Date:** 2025-01-XX  
**Objectif:** Vérifier si les problèmes identifiés dans l'analyse existent sur le VPS

---

## 📋 Méthodes de Diagnostic

### Méthode 1 : Script Python (Recommandé)

**Avantages:**
- Analyse complète et détaillée
- Détection automatique de tous les problèmes
- Rapport formaté avec codes couleur

**Commandes:**

```bash
# Se connecter au VPS
ssh erp-admin@51.254.36.25

# Aller dans le répertoire de l'application
cd /opt/erp/app

# Activer l'environnement virtuel
source venv/bin/activate

# Exécuter le script de diagnostic
python3 scripts/diagnostic_comptabilite_vps.py
```

**Résultat attendu:**
- Liste des problèmes détectés
- Statistiques détaillées
- Résumé final avec nombre de problèmes

---

### Méthode 2 : Script SQL Direct

**Avantages:**
- Plus rapide
- Peut être exécuté directement dans psql
- Pas besoin de Flask

**Commandes:**

```bash
# Se connecter au VPS
ssh erp-admin@51.254.36.25

# Se connecter à PostgreSQL
sudo -u postgres psql fee

# Exécuter le script SQL
\i /opt/erp/app/scripts/diagnostic_comptabilite_vps.sql
```

**Ou copier-coller le contenu du script directement dans psql**

---

## 🔍 Ce que le Diagnostic Vérifie

### 1. Comptes et Journaux
- ✅ Existence des comptes nécessaires (530, 512, 701, etc.)
- ✅ Existence des journaux nécessaires (VT, AC, CA, BQ, OD)
- ✅ Statut actif/inactif

### 2. Écritures Banque
- ✅ Nombre d'écritures pour le compte 512
- ✅ Solde calculé (débits - crédits)
- ✅ Écritures de cashout trouvées
- ✅ Solde initial défini

### 3. Cashouts
- ✅ Cashouts dans `cash_movements`
- ✅ Écritures comptables correspondantes
- ✅ Cashouts sans écriture comptable

### 4. Double Comptabilisation
- ✅ Écritures de ventes sur compte 701
- ✅ Écritures de ventes sur compte 758 (Produits divers)
- ✅ Détection des doubles comptabilisations

### 5. Écritures de Salaires
- ✅ Nombre d'écritures de salaires
- ✅ Écritures non équilibrées (brut vs net)

### 6. Équilibre des Écritures
- ✅ Toutes les écritures équilibrées ?
- ✅ Liste des écritures non équilibrées

### 7. Performance
- ✅ Comptes avec beaucoup d'écritures (> 100)
- ✅ Impact sur la propriété `balance`

### 8. Références Dupliquées
- ✅ Détection des `entry_number` dupliqués

---

## 📊 Interprétation des Résultats

### ✅ Aucun Problème
Si le script affiche "Aucun problème critique détecté", alors :
- Les problèmes identifiés dans l'analyse n'existent PAS sur le VPS
- Ou ils ont déjà été corrigés

### ❌ Problèmes Détectés

**Si des problèmes sont détectés:**

1. **Comptes/Journaux manquants:**
   - Solution: Exécuter `INSERT_COMPTABILITE_VPS.sql` ou créer manuellement

2. **Aucune écriture banque:**
   - Vérifier si des cashouts ont été effectués
   - Vérifier les logs d'erreur pour voir si `create_bank_deposit_entry()` échoue

3. **Cashouts sans écriture:**
   - Confirme le bug identifié (exception silencieuse)
   - Vérifier les logs Flask pour voir les erreurs

4. **Double comptabilisation:**
   - Confirme le bug identifié
   - Les ventes sont comptabilisées deux fois

5. **Écritures non équilibrées:**
   - Vérifier les écritures de salaires
   - Vérifier les autres écritures manuelles

---

## 🔧 Actions Après Diagnostic

### Si Problèmes Détectés:

1. **Sauvegarder les résultats:**
   ```bash
   python3 scripts/diagnostic_comptabilite_vps.py > diagnostic_comptabilite_$(date +%Y%m%d).log
   ```

2. **Vérifier les logs Flask:**
   ```bash
   tail -n 100 /opt/erp/app/logs/app.log | grep -i "erreur\|error\|exception"
   ```

3. **Vérifier les cashouts effectués:**
   ```sql
   SELECT * FROM cash_movements 
   WHERE reason LIKE '%Dépôt en banque%' 
   ORDER BY created_at DESC;
   ```

4. **Vérifier les écritures créées:**
   ```sql
   SELECT * FROM accounting_journal_entries 
   WHERE reference LIKE 'DEPOSIT-%' 
   ORDER BY entry_date DESC;
   ```

---

## 📝 Exemple de Sortie Attendue

```
================================================================================
  DIAGNOSTIC COMPLET DE LA COMPTABILITÉ - VPS
================================================================================

Date: 2025-01-XX 10:30:00
Base de données: postgresql://...

================================================================================
  1. VÉRIFICATION DES COMPTES ET JOURNAUX
================================================================================

✅ Compte 530 (Caisse) existe et est actif
✅ Compte 512 (Banque) existe et est actif
❌ PROBLÈME Compte 701: Compte 701 (Ventes de marchandises) n'existe pas
...

================================================================================
  2. VÉRIFICATION DES ÉCRITURES BANQUE (512)
================================================================================

📊 Nombre total d'écritures pour le compte 512: 0
❌ PROBLÈME Banque: Aucune écriture comptable pour le compte 512
   → Cela explique pourquoi l'état de banque affiche 0

💰 Solde banque calculé: 0.00 DA
...

================================================================================
  RÉSUMÉ FINAL
================================================================================

⚠️  3 problème(s) détecté(s):
   ❌ 2 compte(s) manquant(s)
   ❌ 0 cashout(s) sans écriture comptable
   ❌ 5 écriture(s) non équilibrée(s)
```

---

## 🚀 Commandes Rapides

### Diagnostic Complet
```bash
ssh erp-admin@51.254.36.25 "cd /opt/erp/app && source venv/bin/activate && python3 scripts/diagnostic_comptabilite_vps.py"
```

### Diagnostic SQL Seul
```bash
ssh erp-admin@51.254.36.25 "sudo -u postgres psql fee -f /opt/erp/app/scripts/diagnostic_comptabilite_vps.sql"
```

### Vérification Rapide Cashouts
```bash
ssh erp-admin@51.254.36.25 "sudo -u postgres psql fee -c \"SELECT COUNT(*) FROM cash_movements WHERE reason LIKE '%Dépôt en banque%';\""
```

---

**Fin des instructions**

