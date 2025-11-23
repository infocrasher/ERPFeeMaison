-- ============================================
-- FIX IMMÉDIAT VPS - Éléments Critiques
-- ============================================
-- À exécuter en PRIORITÉ pour que l'ERP fonctionne
-- ============================================

-- 1. EXERCICE FISCAL 2025 (CRITIQUE - À CRÉER EN PREMIER)
-- ============================================
INSERT INTO accounting_fiscal_years (
    year,
    start_date,
    end_date,
    is_active,
    is_closed,
    created_at
) VALUES (
    2025,
    '2025-01-01',
    '2025-12-31',
    true,
    false,
    NOW()
)
ON CONFLICT (year) DO NOTHING;

-- 2. JOURNAUX COMPTABLES (5 journaux essentiels - CRITIQUE)
-- ============================================
INSERT INTO accounting_journals (code, name, journal_type, is_active, created_at) VALUES
('VT', 'Journal des ventes', 'VENTES'::journaltype, true, NOW()),
('AC', 'Journal des achats', 'ACHATS'::journaltype, true, NOW()),
('CA', 'Journal de caisse', 'CAISSE'::journaltype, true, NOW()),
('BQ', 'Banque', 'BANQUE'::journaltype, true, NOW()),
('OD', 'Opérations diverses', 'OPERATIONS_DIVERSES'::journaltype, true, NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. COMPTE CAISSE (530) - Si manquant
-- ============================================
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at)
VALUES ('530', 'Caisse', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- Vérification
SELECT '✅ Fix immédiat terminé' as status;
SELECT COUNT(*) as total_journaux FROM accounting_journals;
SELECT COUNT(*) as total_exercices FROM accounting_fiscal_years;

