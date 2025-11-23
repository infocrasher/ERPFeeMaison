#!/bin/bash
# Script d'audit complet pour comparer les données VPS vs Local
# Usage: ./audit_vps_complete.sh

set -e

AUDIT_DIR="/tmp/audit_vps_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$AUDIT_DIR"

echo "🔍 Début de l'audit VPS..."
echo "📁 Répertoire d'export: $AUDIT_DIR"

# Fonction pour exécuter une requête SQL
run_query() {
    local query="$1"
    local output_file="$2"
    sudo -u postgres psql -d fee_maison_db -c "$query" > "$output_file" 2>&1
    echo "✅ Exporté: $output_file"
}

# 1. Comptes par table
echo "📊 Export des comptes..."
run_query "
SELECT 
    'units' as table_name, COUNT(*) as count FROM units
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'recipes', COUNT(*) FROM recipes
UNION ALL
SELECT 'accounting_accounts', COUNT(*) FROM accounting_accounts
UNION ALL
SELECT 'accounting_journals', COUNT(*) FROM accounting_journals
UNION ALL
SELECT 'accounting_fiscal_years', COUNT(*) FROM accounting_fiscal_years
UNION ALL
SELECT 'delivery_zones', COUNT(*) FROM delivery_zones
UNION ALL
SELECT 'profiles', COUNT(*) FROM profiles
ORDER BY table_name;
" "$AUDIT_DIR/00_counts.txt"

# 2. Unités de conditionnement
echo "📦 Export des unités..."
run_query "
SELECT id, name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at
FROM units
ORDER BY id;
" "$AUDIT_DIR/01_units.txt"

# 3. Catégories
echo "📁 Export des catégories..."
run_query "
SELECT id, name, description, show_in_pos, created_at
FROM categories
ORDER BY id;
" "$AUDIT_DIR/02_categories.txt"

# 4. Fournisseurs
echo "🏢 Export des fournisseurs..."
run_query "
SELECT id, company_name, contact_person, email, phone, supplier_type, is_active, created_at
FROM suppliers
ORDER BY id;
" "$AUDIT_DIR/03_suppliers.txt"

# 5. Clients
echo "👥 Export des clients..."
run_query "
SELECT id, name, email, phone, address, customer_type, is_active, created_at
FROM customers
ORDER BY id;
" "$AUDIT_DIR/04_customers.txt"

# 6. Produits (résumé)
echo "📦 Export des produits (résumé)..."
run_query "
SELECT id, name, product_type, unit, category_id, sku
FROM products
ORDER BY id;
" "$AUDIT_DIR/05_products_summary.txt"

# 7. Comptes comptables
echo "💰 Export des comptes comptables..."
run_query "
SELECT id, code, name, account_type, account_nature, is_active, is_detail
FROM accounting_accounts
ORDER BY code;
" "$AUDIT_DIR/06_accounting_accounts.txt"

# 8. Journaux comptables
echo "📒 Export des journaux comptables..."
run_query "
SELECT id, code, name, journal_type, is_active
FROM accounting_journals
ORDER BY code;
" "$AUDIT_DIR/07_accounting_journals.txt"

# 9. Exercices comptables
echo "📅 Export des exercices comptables..."
run_query "
SELECT id, year, start_date, end_date, is_closed, is_active, is_current
FROM accounting_fiscal_years
ORDER BY year;
" "$AUDIT_DIR/08_accounting_fiscal_years.txt"

# 10. Zones de livraison
echo "🚚 Export des zones de livraison..."
run_query "
SELECT id, name, description, delivery_cost, is_active
FROM delivery_zones
ORDER BY id;
" "$AUDIT_DIR/09_delivery_zones.txt"

# 11. Profils utilisateurs
echo "👤 Export des profils..."
run_query "
SELECT id, name, description, is_active
FROM profiles
ORDER BY id;
" "$AUDIT_DIR/10_profiles.txt"

# 12. Produits utilisés (empêchent suppression)
echo "🔗 Export des produits utilisés..."
run_query "
SELECT 
    p.id,
    p.name,
    COUNT(DISTINCT oi.id) as order_items_count,
    COUNT(DISTINCT ri.id) as recipe_uses_count,
    CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END as has_recipe_definition
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
LEFT JOIN recipe_ingredients ri ON ri.product_id = p.id
LEFT JOIN recipes r ON r.product_id = p.id
GROUP BY p.id, p.name, r.id
HAVING COUNT(DISTINCT oi.id) > 0 
    OR COUNT(DISTINCT ri.id) > 0 
    OR r.id IS NOT NULL
ORDER BY p.name;
" "$AUDIT_DIR/11_products_used.txt"

# 13. Fournisseurs utilisés (empêchent suppression)
echo "🔗 Export des fournisseurs utilisés..."
run_query "
SELECT 
    s.id,
    s.company_name,
    COUNT(p.id) as purchases_count
FROM suppliers s
LEFT JOIN purchases p ON p.supplier_id = s.id
GROUP BY s.id, s.company_name
HAVING COUNT(p.id) > 0
ORDER BY s.company_name;
" "$AUDIT_DIR/12_suppliers_used.txt"

# 14. Contraintes de clés étrangères
echo "🔑 Export des contraintes de clés étrangères..."
run_query "
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
" "$AUDIT_DIR/13_foreign_keys.txt"

echo ""
echo "✅ Audit terminé !"
echo "📁 Fichiers exportés dans: $AUDIT_DIR"
echo ""
echo "📊 Résumé des comptes:"
cat "$AUDIT_DIR/00_counts.txt"

