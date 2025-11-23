# 🔍 Commandes de Diagnostic Comptabilité VPS

## 📋 Commandes à exécuter sur le VPS

### 1. Vérifier les COMPTES COMPTABLES

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    COUNT(*) as total_comptes,
    COUNT(CASE WHEN is_active = true THEN 1 END) as comptes_actifs
FROM accounting_accounts;
"
```

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT code, name, account_type::text, account_nature::text, is_active
FROM accounting_accounts
ORDER BY code;
"
```

### 2. Vérifier les JOURNAUX COMPTABLES

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    COUNT(*) as total_journaux,
    COUNT(CASE WHEN is_active = true THEN 1 END) as journaux_actifs
FROM accounting_journals;
"
```

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT code, name, journal_type::text, is_active
FROM accounting_journals
ORDER BY code;
"
```

### 3. Vérifier les EXERCICES FISCAUX

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    COUNT(*) as total_exercices,
    COUNT(CASE WHEN is_active = true THEN 1 END) as exercices_actifs
FROM accounting_fiscal_years;
"
```

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT year, start_date, end_date, is_active, is_closed
FROM accounting_fiscal_years
ORDER BY year DESC;
"
```

### 4. VÉRIFICATION RAPIDE - Éléments Critiques

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    'Compte 512 (Banque)' as element,
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '512') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END as statut
UNION ALL
SELECT 
    'Compte 530 (Caisse)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '530') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Compte 411 (Clients)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '411') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Compte 401 (Fournisseurs)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '401') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Compte 701 (Ventes)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '701') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal VT (Ventes)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'VT') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal AC (Achats)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'AC') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal CA (Caisse)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'CA') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal BQ (Banque)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'BQ') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal OD (Opérations diverses)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'OD') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Exercice 2025',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_fiscal_years WHERE year = 2025) THEN '✅ EXISTE' ELSE '❌ MANQUANT' END;
"
```

### 5. RÉSUMÉ COMPLET (Une seule commande)

```bash
sudo -u postgres psql -d fee_maison_db << 'EOF'
\echo '========================================'
\echo 'DIAGNOSTIC COMPTABILITÉ VPS'
\echo '========================================'
\echo ''
\echo '1. COMPTES COMPTABLES:'
SELECT COUNT(*) as total FROM accounting_accounts;
SELECT code, name FROM accounting_accounts ORDER BY code LIMIT 10;
\echo ''
\echo '2. JOURNAUX COMPTABLES:'
SELECT COUNT(*) as total FROM accounting_journals;
SELECT code, name FROM accounting_journals;
\echo ''
\echo '3. EXERCICES FISCAUX:'
SELECT COUNT(*) as total FROM accounting_fiscal_years;
SELECT year, start_date, end_date, is_active FROM accounting_fiscal_years;
\echo ''
\echo '4. VÉRIFICATION CRITIQUE:'
SELECT 
    'Compte 512' as element,
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '512') THEN '✅' ELSE '❌' END as statut
UNION ALL
SELECT 'Compte 530', CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '530') THEN '✅' ELSE '❌' END
UNION ALL
SELECT 'Journal VT', CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'VT') THEN '✅' ELSE '❌' END
UNION ALL
SELECT 'Journal CA', CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'CA') THEN '✅' ELSE '❌' END
UNION ALL
SELECT 'Journal BQ', CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'BQ') THEN '✅' ELSE '❌' END
UNION ALL
SELECT 'Exercice 2025', CASE WHEN EXISTS (SELECT 1 FROM accounting_fiscal_years WHERE year = 2025) THEN '✅' ELSE '❌' END;
EOF
```

---

## 🎯 Commande Recommandée

**Pour un diagnostic rapide et complet, utilisez cette commande unique :**

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    'COMPTES' as categorie,
    COUNT(*)::text as total,
    string_agg(code, ', ' ORDER BY code) as codes
FROM accounting_accounts
UNION ALL
SELECT 
    'JOURNAUX',
    COUNT(*)::text,
    string_agg(code, ', ' ORDER BY code)
FROM accounting_journals
UNION ALL
SELECT 
    'EXERCICES',
    COUNT(*)::text,
    string_agg(year::text, ', ' ORDER BY year)
FROM accounting_fiscal_years;
"
```

---

## 📝 Notes

- Si le compte `512` existe déjà (créé manuellement), il apparaîtra dans la liste
- Les éléments marqués `❌ MANQUANT` doivent être créés
- L'exercice fiscal 2025 est **CRITIQUE** - sans lui, les écritures ne peuvent pas être enregistrées

