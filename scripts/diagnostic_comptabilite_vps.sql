-- Script SQL de diagnostic comptabilité pour le VPS
-- À exécuter directement dans PostgreSQL

\echo '========================================'
\echo '  DIAGNOSTIC COMPTABILITÉ - VPS'
\echo '========================================'
\echo ''

-- 1. Vérifier les comptes nécessaires
\echo '1. VÉRIFICATION DES COMPTES'
\echo '---------------------------'
SELECT 
    code,
    name,
    CASE 
        WHEN code IN ('530', '512', '701', '601', '411', '401', '758', '658', '641', '421', '300', '101') 
        THEN '✅ Requis'
        ELSE '⚠️  Optionnel'
    END as status,
    is_active,
    account_type,
    account_nature
FROM accounting_accounts
WHERE code IN ('530', '512', '701', '601', '411', '401', '758', '658', '641', '421', '300', '101')
ORDER BY code;

\echo ''
\echo 'Comptes manquants:'
SELECT code, name
FROM (VALUES 
    ('530', 'Caisse'),
    ('512', 'Banque'),
    ('701', 'Ventes de marchandises'),
    ('601', 'Achats de marchandises'),
    ('411', 'Clients'),
    ('401', 'Fournisseurs'),
    ('758', 'Produits divers'),
    ('658', 'Charges diverses'),
    ('641', 'Rémunérations du personnel'),
    ('421', 'Personnel - Rémunérations dues'),
    ('300', 'Stocks de marchandises'),
    ('101', 'Capital')
) AS required(code, name)
WHERE NOT EXISTS (
    SELECT 1 FROM accounting_accounts WHERE accounting_accounts.code = required.code
);

-- 2. Vérifier les journaux nécessaires
\echo ''
\echo '2. VÉRIFICATION DES JOURNAUX'
\echo '----------------------------'
SELECT 
    code,
    name,
    journal_type,
    is_active,
    CASE 
        WHEN code IN ('VT', 'AC', 'CA', 'BQ', 'OD') THEN '✅ Requis'
        ELSE '⚠️  Optionnel'
    END as status
FROM accounting_journals
WHERE code IN ('VT', 'AC', 'CA', 'BQ', 'OD')
ORDER BY code;

\echo ''
\echo 'Journaux manquants:'
SELECT code, name
FROM (VALUES 
    ('VT', 'Ventes'),
    ('AC', 'Achats'),
    ('CA', 'Caisse'),
    ('BQ', 'Banque'),
    ('OD', 'Opérations Diverses')
) AS required(code, name)
WHERE NOT EXISTS (
    SELECT 1 FROM accounting_journals WHERE accounting_journals.code = required.code
);

-- 3. Vérifier les écritures pour le compte banque (512)
\echo ''
\echo '3. ÉCRITURES COMPTE BANQUE (512)'
\echo '---------------------------------'
SELECT 
    COUNT(*) as total_ecritures,
    COALESCE(SUM(jel.debit_amount), 0) as total_debits,
    COALESCE(SUM(jel.credit_amount), 0) as total_credits,
    COALESCE(SUM(jel.debit_amount), 0) - COALESCE(SUM(jel.credit_amount), 0) as solde_banque
FROM accounting_journal_entry_lines jel
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE a.code = '512';

\echo ''
\echo 'Dernières écritures banque:'
SELECT 
    je.entry_date,
    je.entry_number,
    je.reference,
    je.description,
    jel.debit_amount,
    jel.credit_amount
FROM accounting_journal_entry_lines jel
JOIN accounting_journal_entries je ON jel.entry_id = je.id
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE a.code = '512'
ORDER BY je.entry_date DESC, je.id DESC
LIMIT 10;

-- 4. Vérifier les cashouts
\echo ''
\echo '4. CASHOUTS'
\echo '-----------'
SELECT 
    COUNT(*) as total_cashouts,
    COALESCE(SUM(cm.amount), 0) as total_montant
FROM cash_movements cm
WHERE cm.reason LIKE '%Dépôt en banque%' OR cm.reason LIKE '%Cashout%';

\echo ''
\echo 'Cashouts sans écriture comptable:'
SELECT 
    cm.id,
    cm.created_at,
    cm.amount,
    cm.reason
FROM cash_movements cm
WHERE (cm.reason LIKE '%Dépôt en banque%' OR cm.reason LIKE '%Cashout%')
AND NOT EXISTS (
    SELECT 1 
    FROM accounting_journal_entries je 
    WHERE je.reference LIKE 'DEPOSIT-' || cm.id || '%'
)
ORDER BY cm.created_at DESC;

-- 5. Vérifier les écritures de cashout
\echo ''
\echo '5. ÉCRITURES DE CASHOUT'
\echo '-----------------------'
SELECT 
    COUNT(*) as total_ecritures_cashout
FROM accounting_journal_entries
WHERE reference LIKE 'DEPOSIT-%';

\echo ''
\echo 'Dernières écritures de cashout:'
SELECT 
    je.entry_date,
    je.entry_number,
    je.reference,
    je.description,
    SUM(jel.debit_amount) as total_debit,
    SUM(jel.credit_amount) as total_credit
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE je.reference LIKE 'DEPOSIT-%' AND a.code = '512'
GROUP BY je.id, je.entry_date, je.entry_number, je.reference, je.description
ORDER BY je.entry_date DESC
LIMIT 10;

-- 6. Vérifier le solde initial banque
\echo ''
\echo '6. SOLDE INITIAL BANQUE'
\echo '----------------------'
SELECT 
    je.entry_date,
    je.reference,
    je.description,
    jel.debit_amount as solde_initial
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE je.reference LIKE 'OUVERTURE-%' AND a.code = '512';

-- 7. Vérifier la double comptabilisation des ventes
\echo ''
\echo '7. DOUBLE COMPTABILISATION VENTES'
\echo '---------------------------------'
SELECT 
    COUNT(*) as ventes_sur_produits_divers
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE a.code = '758' 
AND (je.description LIKE '%Vente%' OR je.description LIKE '%vente%');

\echo ''
\echo 'Écritures "Produits divers" avec "Vente" dans description:'
SELECT 
    je.entry_date,
    je.entry_number,
    je.reference,
    je.description,
    jel.credit_amount
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
JOIN accounting_accounts a ON jel.account_id = a.id
WHERE a.code = '758' 
AND (je.description LIKE '%Vente%' OR je.description LIKE '%vente%')
ORDER BY je.entry_date DESC
LIMIT 10;

-- 8. Vérifier les écritures non équilibrées
\echo ''
\echo '8. ÉCRITURES NON ÉQUILIBRÉES'
\echo '----------------------------'
SELECT 
    je.id,
    je.entry_number,
    je.entry_date,
    SUM(jel.debit_amount) as total_debit,
    SUM(jel.credit_amount) as total_credit,
    ABS(SUM(jel.debit_amount) - SUM(jel.credit_amount)) as difference
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
GROUP BY je.id, je.entry_number, je.entry_date
HAVING ABS(SUM(jel.debit_amount) - SUM(jel.credit_amount)) > 0.01
ORDER BY difference DESC
LIMIT 20;

-- 9. Vérifier les écritures de salaires
\echo ''
\echo '9. ÉCRITURES DE SALAIRES'
\echo '------------------------'
SELECT 
    COUNT(*) as total_ecritures_salaires
FROM accounting_journal_entries
WHERE description LIKE '%Calcul salaire%' OR description LIKE '%Paiement salaire%';

\echo ''
\echo 'Écritures de salaires non équilibrées:'
SELECT 
    je.id,
    je.entry_number,
    je.entry_date,
    je.description,
    SUM(jel.debit_amount) as total_debit,
    SUM(jel.credit_amount) as total_credit,
    ABS(SUM(jel.debit_amount) - SUM(jel.credit_amount)) as difference
FROM accounting_journal_entries je
JOIN accounting_journal_entry_lines jel ON je.id = jel.entry_id
WHERE je.description LIKE '%Calcul salaire%' OR je.description LIKE '%Paiement salaire%'
GROUP BY je.id, je.entry_number, je.entry_date, je.description
HAVING ABS(SUM(jel.debit_amount) - SUM(jel.credit_amount)) > 0.01
ORDER BY je.entry_date DESC;

-- 10. Vérifier les références dupliquées
\echo ''
\echo '10. RÉFÉRENCES DUPLIQUÉES'
\echo '-------------------------'
SELECT 
    entry_number,
    COUNT(*) as count
FROM accounting_journal_entries
GROUP BY entry_number
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- 11. Statistiques générales
\echo ''
\echo '11. STATISTIQUES GÉNÉRALES'
\echo '--------------------------'
SELECT 
    (SELECT COUNT(*) FROM accounting_accounts) as total_comptes,
    (SELECT COUNT(*) FROM accounting_accounts WHERE is_active = true) as comptes_actifs,
    (SELECT COUNT(*) FROM accounting_journals) as total_journaux,
    (SELECT COUNT(*) FROM accounting_journal_entries) as total_ecritures,
    (SELECT COUNT(*) FROM accounting_journal_entries WHERE is_validated = true) as ecritures_validees,
    (SELECT COUNT(*) FROM accounting_journal_entry_lines) as total_lignes;

\echo ''
\echo '========================================'
\echo '  FIN DU DIAGNOSTIC'
\echo '========================================'

