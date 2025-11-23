-- ============================================
-- DIAGNOSTIC COMPTABILITÉ VPS
-- ============================================
-- Ce script permet de vérifier ce qui existe et ce qui manque
-- dans les tables de comptabilité sur le VPS
-- ============================================

-- 1. COMPTES COMPTABLES (accounting_accounts)
-- ============================================
\echo '========================================'
\echo '1. COMPTES COMPTABLES'
\echo '========================================'

-- Compter le nombre total de comptes
SELECT 
    COUNT(*) as total_comptes,
    COUNT(CASE WHEN is_active = true THEN 1 END) as comptes_actifs,
    COUNT(CASE WHEN is_detail = true THEN 1 END) as comptes_detail
FROM accounting_accounts;

-- Lister tous les comptes existants
SELECT 
    code,
    name,
    account_type::text as type,
    account_nature::text as nature,
    is_active,
    is_detail
FROM accounting_accounts
ORDER BY code;

-- Vérifier les comptes essentiels (ceux qui doivent exister)
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '512') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as compte_512_banque,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '530') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as compte_530_caisse,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '411') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as compte_411_clients,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '401') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as compte_401_fournisseurs,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '701') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as compte_701_ventes;

-- ============================================
-- 2. JOURNAUX COMPTABLES (accounting_journals)
-- ============================================
\echo ''
\echo '========================================'
\echo '2. JOURNAUX COMPTABLES'
\echo '========================================'

-- Compter le nombre total de journaux
SELECT 
    COUNT(*) as total_journaux,
    COUNT(CASE WHEN is_active = true THEN 1 END) as journaux_actifs
FROM accounting_journals;

-- Lister tous les journaux existants
SELECT 
    code,
    name,
    journal_type::text as type,
    is_active
FROM accounting_journals
ORDER BY code;

-- Vérifier les journaux essentiels (ceux qui doivent exister)
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'VT') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as journal_VT_ventes,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'AC') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as journal_AC_achats,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'CA') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as journal_CA_caisse,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'BQ') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as journal_BQ_banque,
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'OD') THEN '✅ EXISTE'
        ELSE '❌ MANQUANT'
    END as journal_OD_operations_diverses;

-- ============================================
-- 3. EXERCICES FISCAUX (accounting_fiscal_years)
-- ============================================
\echo ''
\echo '========================================'
\echo '3. EXERCICES FISCAUX'
\echo '========================================'

-- Compter le nombre total d'exercices
SELECT 
    COUNT(*) as total_exercices,
    COUNT(CASE WHEN is_active = true THEN 1 END) as exercices_actifs,
    COUNT(CASE WHEN is_closed = false THEN 1 END) as exercices_ouverts
FROM accounting_fiscal_years;

-- Lister tous les exercices existants
SELECT 
    year,
    start_date,
    end_date,
    is_active,
    is_closed,
    created_at
FROM accounting_fiscal_years
ORDER BY year DESC;

-- Vérifier si l'exercice 2025 existe
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM accounting_fiscal_years WHERE year = 2025) THEN '✅ EXISTE'
        ELSE '❌ MANQUANT - CRITIQUE'
    END as exercice_2025;

-- ============================================
-- 4. RÉSUMÉ GLOBAL
-- ============================================
\echo ''
\echo '========================================'
\echo '4. RÉSUMÉ GLOBAL'
\echo '========================================'

SELECT 
    'Comptes comptables' as table_name,
    COUNT(*) as total,
    COUNT(CASE WHEN is_active = true THEN 1 END) as actifs
FROM accounting_accounts
UNION ALL
SELECT 
    'Journaux comptables',
    COUNT(*),
    COUNT(CASE WHEN is_active = true THEN 1 END)
FROM accounting_journals
UNION ALL
SELECT 
    'Exercices fiscaux',
    COUNT(*),
    COUNT(CASE WHEN is_active = true THEN 1 END)
FROM accounting_fiscal_years
UNION ALL
SELECT 
    'Écritures comptables',
    COUNT(*),
    NULL
FROM accounting_journal_entries;

-- ============================================
-- 5. VÉRIFICATION DES DONNÉES CRITIQUES
-- ============================================
\echo ''
\echo '========================================'
\echo '5. VÉRIFICATION DONNÉES CRITIQUES'
\echo '========================================'

SELECT 
    'Compte 512 (Banque)' as element,
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '512') THEN '✅' ELSE '❌ MANQUANT' END as statut
UNION ALL
SELECT 
    'Compte 530 (Caisse)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '530') THEN '✅' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal VT (Ventes)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'VT') THEN '✅' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal CA (Caisse)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'CA') THEN '✅' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal BQ (Banque)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'BQ') THEN '✅' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Exercice 2025',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_fiscal_years WHERE year = 2025) THEN '✅' ELSE '❌ MANQUANT' END;

