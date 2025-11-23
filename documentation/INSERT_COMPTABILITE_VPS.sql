-- ============================================
-- REQUÊTES SQL INSERT - COMPTABILITÉ VPS
-- ============================================
-- Ce fichier contient toutes les requêtes INSERT
-- pour créer les éléments essentiels de comptabilité
-- ============================================
-- IMPORTANT: Exécuter ces requêtes dans l'ordre
-- ============================================

-- ============================================
-- 1. EXERCICE FISCAL 2025 (CRITIQUE - À CRÉER EN PREMIER)
-- ============================================
-- L'exercice fiscal est nécessaire pour toutes les écritures

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

-- ============================================
-- 2. JOURNAUX COMPTABLES (5 journaux essentiels)
-- ============================================

-- Journal des Ventes (VT)
INSERT INTO accounting_journals (
    code,
    name,
    journal_type,
    is_active,
    created_at
) VALUES (
    'VT',
    'Journal des ventes',
    'VENTES'::journaltype,
    true,
    NOW()
)
ON CONFLICT (code) DO NOTHING;

-- Journal des Achats (AC)
INSERT INTO accounting_journals (
    code,
    name,
    journal_type,
    is_active,
    created_at
) VALUES (
    'AC',
    'Journal des achats',
    'ACHATS'::journaltype,
    true,
    NOW()
)
ON CONFLICT (code) DO NOTHING;

-- Journal de Caisse (CA)
INSERT INTO accounting_journals (
    code,
    name,
    journal_type,
    is_active,
    created_at
) VALUES (
    'CA',
    'Journal de caisse',
    'CAISSE'::journaltype,
    true,
    NOW()
)
ON CONFLICT (code) DO NOTHING;

-- Journal de Banque (BQ)
INSERT INTO accounting_journals (
    code,
    name,
    journal_type,
    is_active,
    created_at
) VALUES (
    'BQ',
    'Banque',
    'BANQUE'::journaltype,
    true,
    NOW()
)
ON CONFLICT (code) DO NOTHING;

-- Journal Opérations Diverses (OD)
INSERT INTO accounting_journals (
    code,
    name,
    journal_type,
    is_active,
    created_at
) VALUES (
    'OD',
    'Opérations diverses',
    'OPERATIONS_DIVERSES'::journaltype,
    true,
    NOW()
)
ON CONFLICT (code) DO NOTHING;

-- ============================================
-- 3. COMPTES COMPTABLES - Plan Comptable Complet
-- ============================================

-- Classe 1 - Capitaux
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('10', 'Capital et réserves', 'CLASSE_1'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('101', 'Capital social', 'CLASSE_1'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- Classe 2 - Immobilisations
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('20', 'Immobilisations', 'CLASSE_2'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('215', 'Installations techniques', 'CLASSE_2'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('2154', 'Matériel de boulangerie', 'CLASSE_2'::accounttype, 'DEBIT'::accountnature, true, true, 3, NOW()),
('218', 'Autres immobilisations', 'CLASSE_2'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- Classe 3 - Stocks
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('30', 'Stocks', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('300', 'Stocks de marchandises', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('301', 'Matières premières', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('3011', 'Farines', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 3, NOW()),
('3012', 'Semoules', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 3, NOW()),
('3013', 'Levures et améliorants', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 3, NOW()),
('302', 'Emballages', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('355', 'Produits finis', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('3551', 'Pain et viennoiseries', 'CLASSE_3'::accounttype, 'DEBIT'::accountnature, true, true, 3, NOW())
ON CONFLICT (code) DO NOTHING;

-- Classe 4 - Tiers
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('40', 'Fournisseurs et comptes rattachés', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('401', 'Fournisseurs', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW()),
('41', 'Clients et comptes rattachés', 'CLASSE_4'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('411', 'Clients', 'CLASSE_4'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('42', 'Personnel et comptes rattachés', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('421', 'Personnel - Rémunérations dues', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW()),
('43', 'Sécurité sociale et autres organismes', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('431', 'Sécurité sociale', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW()),
('44', 'État et collectivités publiques', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('445', 'TVA à décaisser', 'CLASSE_4'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- Classe 5 - Financiers (CRITIQUE pour caisse et banque)
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('50', 'Valeurs mobilières de placement', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('51', 'Banques', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('512', 'Banques', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('53', 'Caisse', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('530', 'Caisse', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('531', 'Caisse', 'CLASSE_5'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- Classe 6 - Charges
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('60', 'Achats', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('601', 'Achats de matières premières', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('602', 'Achats d''emballages', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('606', 'Achats de fournitures', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('607', 'Achats de marchandises', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('61', 'Services extérieurs', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('613', 'Locations', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('615', 'Entretien et réparations', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('616', 'Primes d''assurance', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('62', 'Autres services extérieurs', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('621', 'Personnel extérieur', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('625', 'Déplacements', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('626', 'Frais postaux', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('627', 'Services bancaires', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('628', 'Divers', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('64', 'Charges de personnel', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('641', 'Rémunérations du personnel', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('645', 'Charges de sécurité sociale', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('658', 'Charges diverses de gestion courante', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('66', 'Charges financières', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('661', 'Charges d''intérêts', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW()),
('68', 'Dotations aux amortissements', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, false, 1, NOW()),
('681', 'Dotations aux amortissements', 'CLASSE_6'::accounttype, 'DEBIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- Classe 7 - Produits
INSERT INTO accounting_accounts (code, name, account_type, account_nature, is_active, is_detail, level, created_at) VALUES
('70', 'Ventes', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('701', 'Ventes de produits finis', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW()),
('7011', 'Ventes pain', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, true, 3, NOW()),
('7012', 'Ventes viennoiseries', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, true, 3, NOW()),
('707', 'Ventes de marchandises', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW()),
('758', 'Produits divers de gestion courante', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW()),
('76', 'Produits financiers', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, false, 1, NOW()),
('761', 'Produits de participations', 'CLASSE_7'::accounttype, 'CREDIT'::accountnature, true, true, 2, NOW())
ON CONFLICT (code) DO NOTHING;

-- ============================================
-- VÉRIFICATION FINALE
-- ============================================

SELECT '✅ INSERT terminé' as status;
SELECT COUNT(*) as total_comptes FROM accounting_accounts;
SELECT COUNT(*) as total_journaux FROM accounting_journals;
SELECT COUNT(*) as total_exercices FROM accounting_fiscal_years;

