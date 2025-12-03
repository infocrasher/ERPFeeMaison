-- Script SQL pour analyser le problème de stock de "Rechta PF"
-- À exécuter directement sur le VPS

-- 1. Trouver le produit Rechta PF
SELECT 
    id,
    name,
    stock_comptoir,
    stock_ingredients_local,
    stock_ingredients_magasin,
    stock_consommables,
    total_stock_value,
    cost_price,
    last_stock_update,
    created_at
FROM products
WHERE name ILIKE '%rechta%'
ORDER BY name;

-- 2. Historique des mouvements de stock (stock_comptoir uniquement)
SELECT 
    sm.id,
    sm.reference,
    sm.created_at,
    sm.movement_type,
    sm.quantity,
    sm.stock_before,
    sm.stock_after,
    sm.reason,
    sm.order_id,
    u.username as user_name,
    o.order_type,
    o.status as order_status
FROM stock_movements sm
LEFT JOIN users u ON sm.user_id = u.id
LEFT JOIN orders o ON sm.order_id = o.id
WHERE sm.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
  AND sm.stock_location = 'COMPTOIR'
ORDER BY sm.created_at DESC
LIMIT 50;

-- 3. Commandes contenant Rechta PF
SELECT 
    o.id as order_id,
    o.order_type,
    o.status,
    o.created_at,
    o.due_date,
    oi.quantity,
    oi.unit_price,
    u.username as created_by
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN users u ON o.user_id = u.id
WHERE oi.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
ORDER BY o.created_at DESC
LIMIT 50;

-- 4. Ajustements manuels suspects
SELECT 
    sm.id,
    sm.created_at,
    sm.movement_type,
    sm.quantity,
    sm.stock_before,
    sm.stock_after,
    sm.reason,
    u.username as user_name
FROM stock_movements sm
LEFT JOIN users u ON sm.user_id = u.id
WHERE sm.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
  AND sm.stock_location = 'COMPTOIR'
  AND sm.movement_type IN ('AJUSTEMENT_POSITIF', 'AJUSTEMENT_NEGATIF', 'INVENTAIRE')
ORDER BY sm.created_at DESC;

-- 5. Grandes incrémentations (>100 pièces)
SELECT 
    sm.id,
    sm.created_at,
    sm.movement_type,
    sm.quantity,
    sm.stock_before,
    sm.stock_after,
    sm.reason,
    sm.order_id,
    u.username as user_name
FROM stock_movements sm
LEFT JOIN users u ON sm.user_id = u.id
WHERE sm.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
  AND sm.stock_location = 'COMPTOIR'
  AND sm.quantity > 100
ORDER BY sm.quantity DESC;

-- 6. Ordres de production pour Rechta PF
SELECT 
    o.id,
    o.status,
    o.created_at,
    o.due_date,
    oi.quantity,
    u.username as created_by
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN users u ON o.user_id = u.id
WHERE oi.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
  AND o.order_type = 'counter_production_request'
ORDER BY o.created_at DESC
LIMIT 20;

-- 7. Statistiques par type de mouvement
SELECT 
    sm.movement_type,
    COUNT(*) as nombre_mouvements,
    SUM(sm.quantity) as total_quantite,
    MIN(sm.quantity) as min_quantite,
    MAX(sm.quantity) as max_quantite,
    AVG(sm.quantity) as moyenne_quantite
FROM stock_movements sm
WHERE sm.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
  AND sm.stock_location = 'COMPTOIR'
GROUP BY sm.movement_type
ORDER BY total_quantite DESC;

-- 8. Évolution du stock au fil du temps (approximation basée sur les mouvements)
WITH stock_evolution AS (
    SELECT 
        sm.created_at::date as date,
        SUM(sm.quantity) OVER (ORDER BY sm.created_at) as stock_cumule,
        sm.quantity,
        sm.stock_after,
        sm.movement_type
    FROM stock_movements sm
    WHERE sm.product_id = (SELECT id FROM products WHERE name ILIKE '%rechta%' LIMIT 1)
      AND sm.stock_location = 'COMPTOIR'
    ORDER BY sm.created_at DESC
    LIMIT 100
)
SELECT * FROM stock_evolution
ORDER BY date DESC;

