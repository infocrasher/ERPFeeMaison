-- ============================================================
-- INJECTION DES UNITÉS DE CONDITIONNEMENT SUR LE VPS
-- ============================================================
-- Ce script injecte toutes les unités de conditionnement
-- nécessaires pour créer des bons d'achat
--
-- Date : 2025-11-23
-- ============================================================

-- Supprimer les unités existantes si nécessaire (optionnel)
-- DELETE FROM units;

-- Insérer les unités de conditionnement
-- Utilisation de ON CONFLICT pour éviter les doublons

INSERT INTO units (name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at)
VALUES 
    -- Poids
    ('Sac 25kg', 'g', 25000, 'Poids', 1, true, CURRENT_TIMESTAMP),
    ('Sac 10kg', 'g', 10000, 'Poids', 2, true, CURRENT_TIMESTAMP),
    ('Sac 5kg', 'g', 5000, 'Poids', 3, true, CURRENT_TIMESTAMP),
    ('Sac 2kg', 'g', 2000, 'Poids', 4, true, CURRENT_TIMESTAMP),
    ('Sac 1kg', 'g', 1000, 'Poids', 5, true, CURRENT_TIMESTAMP),
    ('Barre 1,8kg', 'g', 1800, 'Poids', 6, true, CURRENT_TIMESTAMP),
    ('Bidon 3,8kg', 'g', 3800, 'Poids', 7, true, CURRENT_TIMESTAMP),
    ('Boite 500g', 'g', 500, 'Poids', 8, true, CURRENT_TIMESTAMP),
    ('Sachet 500g', 'g', 500, 'Poids', 9, true, CURRENT_TIMESTAMP),
    ('Pot 500g', 'g', 500, 'Poids', 10, true, CURRENT_TIMESTAMP),
    ('Boite 250g', 'g', 250, 'Poids', 11, true, CURRENT_TIMESTAMP),
    ('Sachet 125g', 'g', 125, 'Poids', 12, true, CURRENT_TIMESTAMP),
    ('Sachet 10g', 'g', 10, 'Poids', 13, true, CURRENT_TIMESTAMP),
    
    -- Volume
    ('Bidon 5L', 'ml', 5000, 'Volume', 20, true, CURRENT_TIMESTAMP),
    ('Bouteille 5L', 'ml', 5000, 'Volume', 21, true, CURRENT_TIMESTAMP),
    ('Bouteille 2L', 'ml', 2000, 'Volume', 22, true, CURRENT_TIMESTAMP),
    ('Bouteille 1L', 'ml', 1000, 'Volume', 23, true, CURRENT_TIMESTAMP),
    
    -- Pièces/Unités
    ('Lot de 100 pièces', 'pièce', 100, 'Unitaire', 30, true, CURRENT_TIMESTAMP),
    ('Lot de 50 pièces', 'pièce', 50, 'Unitaire', 31, true, CURRENT_TIMESTAMP),
    ('Plateau de 30 pièces', 'pièce', 30, 'Unitaire', 32, true, CURRENT_TIMESTAMP),
    ('Lot de 12 pièces', 'pièce', 12, 'Unitaire', 33, true, CURRENT_TIMESTAMP),
    ('Lot de 10 pièces', 'pièce', 10, 'Unitaire', 34, true, CURRENT_TIMESTAMP),
    ('Lot de 6 pièces', 'pièce', 6, 'Unitaire', 35, true, CURRENT_TIMESTAMP),
    ('Fardeau de 6 bouteilles', 'pièce', 6, 'Unitaire', 36, true, CURRENT_TIMESTAMP),
    
    -- Unités de Base
    ('Gramme (g)', 'g', 1, 'Poids', 100, true, CURRENT_TIMESTAMP),
    ('Millilitre (ml)', 'ml', 1, 'Volume', 101, true, CURRENT_TIMESTAMP),
    ('Pièce', 'pièce', 1, 'Unitaire', 102, true, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING;

-- Vérification
SELECT 
    COUNT(*) as total_units,
    COUNT(CASE WHEN unit_type = 'Poids' THEN 1 END) as poids,
    COUNT(CASE WHEN unit_type = 'Volume' THEN 1 END) as volume,
    COUNT(CASE WHEN unit_type = 'Unitaire' THEN 1 END) as unitaire
FROM units
WHERE is_active = true;

-- Afficher toutes les unités créées
SELECT id, name, base_unit, conversion_factor, unit_type, display_order
FROM units
WHERE is_active = true
ORDER BY display_order, name;

