# 🔴 URGENT : Fix Cashout Comptabilité VPS

**Problème:** Erreur lors du cashout : `'cash_movement_id' is an invalid keyword argument for JournalEntry`

**Cause:** Le modèle `JournalEntry` n'a pas de champ `cash_movement_id`. Ce champ n'existe pas dans la base de données.

**Solution:** Mettre à jour le code sur le VPS avec la dernière correction.

---

## 🚀 Solution Immédiate

### Étape 1 : Résoudre l'erreur Git (si pas encore fait)

```bash
ssh erp-admin@51.254.36.25
cd /opt/erp/app

# Sauvegarder les fichiers qui bloquent
mv scripts/diagnostic_comptabilite_vps.py scripts/diagnostic_comptabilite_vps.py.backup
mv scripts/diagnostic_comptabilite_vps.sql scripts/diagnostic_comptabilite_vps.sql.backup

# Faire le pull
git pull origin main
```

### Étape 2 : Vérifier que le code est corrigé

```bash
# Vérifier que cash_movement_id n'est plus dans JournalEntry
grep -n "cash_movement_id" app/accounting/services.py | grep "JournalEntry"

# Si cette commande retourne quelque chose, le code n'est pas à jour
# Si elle ne retourne rien, le code est à jour ✅
```

**Résultat attendu:** Aucune ligne retournée (le code est corrigé)

### Étape 3 : Redémarrer l'application

```bash
sudo systemctl restart erp-fee-maison
sudo systemctl status erp-fee-maison
```

### Étape 4 : Vérifier les logs

```bash
# Vérifier qu'il n'y a pas d'erreurs au démarrage
sudo journalctl -u erp-fee-maison -n 50 --no-pager
```

---

## ✅ Vérification Après Correction

### Test 1 : Vérifier le code

```bash
# Le code doit être comme ça (SANS cash_movement_id dans JournalEntry):
grep -A 8 "create_bank_deposit_entry" app/accounting/services.py | grep -A 5 "JournalEntry"
```

**Doit afficher:**
```python
entry = JournalEntry(
    journal_id=bank_journal.id,
    entry_date=date.today(),
    description=description,
    reference=f"DEPOSIT-{cash_movement_id}",
    created_by_id=current_user.id if current_user else 1
)
```

**Ne doit PAS contenir:** `cash_movement_id=cash_movement_id,`

### Test 2 : Tester un cashout

1. Aller sur la page de caisse
2. Faire un cashout (même petit montant pour tester)
3. Vérifier qu'il n'y a pas d'erreur
4. Vérifier que l'écriture comptable est créée :

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    je.id,
    je.reference,
    je.description,
    je.entry_date,
    a.code as compte_code,
    jel.debit_amount,
    jel.credit_amount
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE je.description LIKE '%Dépôt caisse vers banque%'
ORDER BY je.created_at DESC
LIMIT 5;
"
```

---

## 📋 Commit de Correction

**Commit:** `b56189e` - "Fix: Retirer order_id, purchase_id, cash_movement_id de JournalEntry (champs n'existent pas)"

**Fichier modifié:** `app/accounting/services.py`

**Changements:**
- Retiré `order_id` de `create_sale_entry()`
- Retiré `purchase_id` de `create_purchase_entry()`
- Retiré `cash_movement_id` de `create_cash_movement_entry()`
- Retiré `cash_movement_id` de `create_bank_deposit_entry()`

---

## ⚠️ Important

**Le cashout fonctionne toujours** (le mouvement de caisse est créé), mais **l'écriture comptable n'est pas créée** à cause de cette erreur.

Après la correction, les cashouts futurs créeront automatiquement les écritures comptables.

---

**Fin du document**

