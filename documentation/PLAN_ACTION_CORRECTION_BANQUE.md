# 🚨 PLAN D'ACTION : CORRECTION BANQUE -2 000 000 DA

## 📋 PROBLÈME IDENTIFIÉ

**Symptôme :** La banque affiche un solde de **-2 000 000 DA** après une erreur dans l'unité de conditionnement lors de la saisie d'un bon d'achat.

**Cause probable :** 
1. Un bon d'achat a été **marqué comme payé par banque** avec un montant incorrect (erreur d'unité)
2. Une **écriture comptable** a été créée avec ce montant erroné
3. Le bon d'achat a été **modifié** (correction de l'unité) → le `total_amount` a été recalculé
4. **MAIS** l'écriture comptable n'a **PAS été mise à jour** → incohérence

## 🔍 ANALYSE TECHNIQUE

### Architecture actuelle

#### 1. Marquage comme payé (`mark_as_paid`)
- Crée une écriture comptable avec le montant `purchase.total_amount`
- Si `payment_method == 'bank'` → Crédit sur compte 512 (Banque)
- Référence de l'écriture : `ACH-{purchase.id}`

#### 2. Modification d'un bon (`edit_purchase`)
- ✅ Annule l'impact stock de l'ancien achat
- ✅ Recalcule le stock avec les nouvelles quantités
- ✅ Recalcule `purchase.total_amount` via `calculate_totals()`
- ❌ **NE MET PAS À JOUR l'écriture comptable** si le bon était déjà payé

#### 3. Marquage comme non payé (`mark_unpaid`)
- ✅ Supprime l'écriture comptable

### Problème identifié

**Scénario probable :**
```
1. Bon d'achat créé avec erreur d'unité → total_amount = 2 000 000 DA (incorrect)
2. Bon marqué comme payé par banque → Écriture créée avec 2 000 000 DA
3. Bon modifié (correction unité) → total_amount = 20 000 DA (correct)
4. Écriture comptable reste à 2 000 000 DA → Banque débitée de 2 000 000 DA au lieu de 20 000 DA
```

## 📊 ÉTAPES DE DIAGNOSTIC

### Étape 1 : Exécuter le script de diagnostic

```bash
cd /opt/erp/app
source venv/bin/activate
python3 scripts/diagnostic_banque_bon_achat.py
```

**Ce script va :**
- ✅ Afficher le solde actuel de la banque
- ✅ Lister tous les bons d'achat payés par banque
- ✅ Identifier les incohérences entre montant bon et montant écriture
- ✅ Afficher les détails des bons récents (30 derniers jours)

### Étape 2 : Identifier le bon problématique

Le script va afficher :
```
📋 Bon d'achat : BA2025-XXXXX (ID: XXX)
   Date paiement : 2025-XX-XX
   Montant bon actuel : 20 000,00 DA
   Montant écriture comptable : 2 000 000,00 DA
   ÉCART : -1 980 000,00 DA
```

**Noter :**
- L'ID du bon d'achat
- L'ID de l'écriture comptable
- Le montant correct (actuel)
- Le montant incorrect (écriture)

### Étape 3 : Vérifier l'historique

1. Aller sur l'interface : `/admin/purchases/{id}`
2. Vérifier :
   - Le montant actuel du bon
   - La date de paiement
   - La date de dernière modification
   - Les items et leurs quantités

## 🔧 SOLUTIONS POSSIBLES

### Solution 1 : Correction manuelle de l'écriture comptable (RECOMMANDÉE)

**Avantages :**
- ✅ Correction précise
- ✅ Traçabilité complète
- ✅ Pas de risque de casser autre chose

**Étapes :**

1. **Identifier l'écriture à corriger**
   ```sql
   SELECT * FROM journal_entries WHERE reference = 'ACH-{purchase_id}';
   SELECT * FROM journal_entry_lines WHERE entry_id = {entry_id};
   ```

2. **Corriger la ligne de crédit (banque)**
   ```sql
   UPDATE journal_entry_lines 
   SET credit_amount = {montant_correct}
   WHERE entry_id = {entry_id} 
     AND account_id = (SELECT id FROM accounting_accounts WHERE code = '512');
   ```

3. **Corriger la ligne de débit (achats)**
   ```sql
   UPDATE journal_entry_lines 
   SET debit_amount = {montant_correct}
   WHERE entry_id = {entry_id} 
     AND account_id = (SELECT id FROM accounting_accounts WHERE code = '601');
   ```

4. **Vérifier le solde**
   - Aller sur `/admin/accounting/bank-statement`
   - Vérifier que le solde est correct

### Solution 2 : Marquer comme non payé puis re-marquer comme payé

**Avantages :**
- ✅ Utilise l'interface existante
- ✅ Pas de SQL manuel

**Étapes :**

1. Aller sur `/admin/purchases/{id}`
2. Cliquer sur "Marquer comme non payé" → Supprime l'écriture
3. Cliquer sur "Marquer comme payé" → Crée une nouvelle écriture avec le bon montant
4. Vérifier le solde

**⚠️ ATTENTION :** Cette méthode crée une nouvelle écriture au lieu de corriger l'ancienne. L'ancienne écriture sera supprimée.

### Solution 3 : Script de correction automatique

**À créer si plusieurs bons sont concernés**

```python
# Script à créer : scripts/correction_ecriture_bon_achat.py
# Prendre l'ID du bon et corriger automatiquement l'écriture
```

## 🛡️ PRÉVENTION FUTURE

### Problème identifié dans le code

**Fichier :** `app/purchases/routes.py` - Fonction `edit_purchase()`

**Problème :** Quand un bon d'achat est modifié après paiement, l'écriture comptable n'est pas mise à jour.

**Solution à implémenter :**

```python
# Dans edit_purchase(), après purchase.calculate_totals() :

# Si le bon est payé, mettre à jour l'écriture comptable
if purchase.is_paid and purchase.payment_method == 'bank':
    entry = JournalEntry.query.filter_by(reference=f"ACH-{purchase.id}").first()
    if entry:
        # Mettre à jour les lignes d'écriture
        bank_line = JournalEntryLine.query.filter_by(
            entry_id=entry.id,
            account_id=bank_account.id
        ).first()
        if bank_line:
            bank_line.credit_amount = float(purchase.total_amount)
        
        purchase_line = JournalEntryLine.query.filter_by(
            entry_id=entry.id,
            account_id=purchase_account.id
        ).first()
        if purchase_line:
            purchase_line.debit_amount = float(purchase.total_amount)
```

## ✅ CHECKLIST DE CORRECTION

- [ ] Exécuter le script de diagnostic
- [ ] Identifier le bon d'achat problématique
- [ ] Vérifier le montant correct actuel
- [ ] Vérifier le montant de l'écriture comptable
- [ ] Calculer l'écart exact
- [ ] Choisir la solution (1, 2 ou 3)
- [ ] Appliquer la correction
- [ ] Vérifier le solde de la banque après correction
- [ ] Documenter la correction
- [ ] Implémenter la prévention (mise à jour automatique)

## 📝 NOTES IMPORTANTES

1. **Ne pas modifier sans validation** : Toujours vérifier les montants avant correction
2. **Sauvegarde** : Faire une sauvegarde de la base avant toute modification
3. **Traçabilité** : Documenter toutes les corrections effectuées
4. **Test** : Tester sur un environnement de développement si possible

## 🔗 RESSOURCES

- Script de diagnostic : `scripts/diagnostic_banque_bon_achat.py`
- Route comptabilité : `/admin/accounting/bank-statement`
- Route bons d'achat : `/admin/purchases/{id}`
- Code source : `app/purchases/routes.py` (ligne 478+)
- Code comptabilité : `app/accounting/services.py` (ligne 96+)

