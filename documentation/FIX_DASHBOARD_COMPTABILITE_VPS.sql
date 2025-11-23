-- ============================================================
-- FIX IMMÉDIAT : Dashboard Comptabilité VPS
-- ============================================================
-- Ce script corrige les erreurs qui empêchent l'affichage
-- du dashboard comptabilité sur le VPS
--
-- Date : 2025-11-23
-- ============================================================

-- 1. Ajouter la colonne is_validated à accounting_journal_entries
-- ============================================================
ALTER TABLE accounting_journal_entries 
ADD COLUMN IF NOT EXISTS is_validated BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE accounting_journal_entries 
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP NULL;

ALTER TABLE accounting_journal_entries 
ADD COLUMN IF NOT EXISTS validated_by_id INTEGER NULL 
REFERENCES users(id);

-- Index pour améliorer les performances des requêtes
CREATE INDEX IF NOT EXISTS idx_journal_entries_validated 
ON accounting_journal_entries(is_validated);

-- 2. Créer la table business_config (singleton)
-- ============================================================
CREATE TABLE IF NOT EXISTS business_config (
    id SERIAL PRIMARY KEY,
    monthly_objective NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    daily_objective NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    yearly_objective NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    stock_rotation_days INTEGER NOT NULL DEFAULT 30,
    quality_target_percent NUMERIC(5, 2) NOT NULL DEFAULT 95.0,
    standard_work_hours_per_day NUMERIC(4, 2) NOT NULL DEFAULT 8.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NULL REFERENCES users(id)
);

-- Insérer une configuration par défaut si elle n'existe pas
INSERT INTO business_config (
    monthly_objective,
    daily_objective,
    yearly_objective,
    stock_rotation_days,
    quality_target_percent,
    standard_work_hours_per_day
)
SELECT 
    0.0,
    0.0,
    0.0,
    30,
    95.0,
    8.0
WHERE NOT EXISTS (SELECT 1 FROM business_config);

-- 3. Ajouter la colonne is_current à accounting_fiscal_years
-- ============================================================
ALTER TABLE accounting_fiscal_years 
ADD COLUMN IF NOT EXISTS is_current BOOLEAN DEFAULT FALSE NOT NULL;

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_fiscal_years_current 
ON accounting_fiscal_years(is_current);

-- ============================================================
-- VÉRIFICATIONS
-- ============================================================
-- Vérifier que les colonnes existent
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'accounting_journal_entries'
AND column_name IN ('is_validated', 'validated_at', 'validated_by_id')
ORDER BY column_name;

-- Vérifier que la table business_config existe
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'business_config'
ORDER BY ordinal_position;

-- Vérifier le contenu de business_config
SELECT * FROM business_config;

