# Instructions : Test Vente Comptabilité sur VPS

**Objectif:** Vérifier que l'intégration comptable fonctionne après les corrections

---

## 🚀 Exécution du Test

### Sur le VPS

```bash
ssh erp-admin@51.254.36.25
cd /opt/erp/app
source venv/bin/activate

# Exécuter le script de test
python3 scripts/test_vente_comptabilite_vps.py
```

---

## 📋 Ce que le Script Fait

1. **Vérifie les prérequis:**
   - Compte Caisse (530) existe et est actif
   - Compte Ventes (701) existe et est actif
   - Journal Ventes (VT) existe et est actif
   - Session de caisse ouverte (crée une session de test si nécessaire)

2. **Affiche l'état avant:**
   - Nombre d'écritures comptables
   - Solde Caisse
   - Solde Ventes

3. **Simule une vente:**
   - Sélectionne un produit fini
   - Crée une écriture comptable via `AccountingIntegrationService.create_sale_entry()`
   - Montant: prix du produit (ou 1000 DA par défaut)

4. **Vérifie l'état après:**
   - Nombre d'écritures comptables (doit augmenter)
   - Solde Caisse (doit augmenter)
   - Solde Ventes (doit augmenter)

5. **Vérifications finales:**
   - ✅ Nouvelle écriture créée
   - ✅ Nouvelles lignes d'écriture créées
   - ✅ Solde caisse correct
   - ✅ Solde ventes correct
   - ✅ Écriture équilibrée

---

## ✅ Résultat Attendu

Si tout fonctionne correctement, vous devriez voir :

```
✅ TEST RÉUSSI - L'intégration comptable fonctionne correctement!
```

Avec :
- ✅ Nouvelle écriture créée
- ✅ Nouvelles lignes d'écriture créées
- ✅ Solde caisse correct
- ✅ Solde ventes correct
- ✅ Écriture équilibrée

---

## ❌ Si le Test Échoue

### Problème : Compte non trouvé

**Erreur:** `Compte Caisse (530) non trouvé ou inactif`

**Solution:**
```bash
# Vérifier que les comptes existent
sudo -u postgres psql -d fee_maison_db -c "SELECT code, name, is_active FROM accounting_accounts WHERE code IN ('530', '701');"

# Si manquants, exécuter le script d'insertion
sudo -u postgres psql -d fee_maison_db -f documentation/INSERT_COMPTABILITE_VPS.sql
```

### Problème : Journal non trouvé

**Erreur:** `Journal Ventes (VT) non trouvé ou inactif`

**Solution:**
```bash
# Vérifier que les journaux existent
sudo -u postgres psql -d fee_maison_db -c "SELECT code, name, is_active FROM accounting_journals WHERE code = 'VT';"

# Si manquant, exécuter le script d'insertion
sudo -u postgres psql -d fee_maison_db -f documentation/INSERT_COMPTABILITE_VPS.sql
```

### Problème : Erreur lors de la création

**Erreur:** `Exception: ...`

**Solution:**
1. Vérifier les logs Flask :
   ```bash
   tail -n 100 /opt/erp/app/logs/app.log | grep -i "erreur\|error\|exception"
   ```

2. Vérifier que l'exercice fiscal existe :
   ```bash
   sudo -u postgres psql -d fee_maison_db -c "SELECT year, is_active FROM accounting_fiscal_years WHERE year = 2025;"
   ```

3. Si manquant :
   ```bash
   sudo -u postgres psql -d fee_maison_db -c "INSERT INTO accounting_fiscal_years (year, start_date, end_date, is_active, is_closed, created_at) VALUES (2025, '2025-01-01', '2025-12-31', true, false, NOW()) ON CONFLICT (year) DO NOTHING;"
   ```

---

## 📊 Vérification Manuelle Après le Test

### Vérifier l'écriture créée

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    je.id,
    je.reference,
    je.description,
    je.entry_date,
    je.is_validated,
    j.code as journal_code
FROM accounting_journal_entries je
JOIN accounting_journals j ON je.journal_id = j.id
WHERE je.description LIKE '%Test vente comptabilité%'
ORDER BY je.created_at DESC
LIMIT 1;
"
```

### Vérifier les lignes d'écriture

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    jel.line_number,
    a.code as compte_code,
    a.name as compte_name,
    jel.debit_amount,
    jel.credit_amount
FROM accounting_journal_entry_lines jel
JOIN accounting_accounts a ON jel.account_id = a.id
JOIN accounting_journal_entries je ON jel.entry_id = je.id
WHERE je.description LIKE '%Test vente comptabilité%'
ORDER BY jel.line_number;
"
```

### Vérifier les soldes

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    a.code,
    a.name,
    SUM(jel.debit_amount) as total_debit,
    SUM(jel.credit_amount) as total_credit,
    CASE 
        WHEN a.account_nature = 'DEBIT' THEN SUM(jel.debit_amount) - SUM(jel.credit_amount)
        ELSE SUM(jel.credit_amount) - SUM(jel.debit_amount)
    END as solde
FROM accounting_accounts a
LEFT JOIN accounting_journal_entry_lines jel ON a.id = jel.account_id
WHERE a.code IN ('530', '701')
GROUP BY a.id, a.code, a.name, a.account_nature;
"
```

---

## 🔍 Analyse des Logs

Si le test échoue, vérifier les logs Flask pour voir les erreurs détaillées :

```bash
# Logs récents
tail -n 200 /opt/erp/app/logs/app.log

# Filtrer les erreurs comptables
tail -n 500 /opt/erp/app/logs/app.log | grep -i "comptable\|accounting\|erreur\|error"
```

Les nouvelles corrections de logging devraient maintenant afficher des erreurs détaillées avec stack traces.

---

## 📝 Notes

- Le script crée une écriture avec `order_id=999` (ID de test)
- La session de caisse est créée automatiquement si elle n'existe pas
- Le script ne modifie pas les données existantes (sauf création de la session de test)
- L'écriture créée peut être supprimée manuellement après le test si nécessaire

---

**Fin des instructions**

